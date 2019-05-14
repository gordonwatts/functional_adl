# Executor and code for the ATLAS xAOD input files
from xAODlib.generated_code import generated_code, scope_is_deeper
import xAODlib.statement as statement
from clientlib.ast_util import lambda_assure, lambda_body, lambda_unwrap
import xAODlib.AtlasEventStream
from cpplib.cpp_vars import unique_name
import cpplib.cpp_ast as cpp_ast
from cpplib.cpp_representation import cpp_variable, cpp_collection, cpp_expression, cpp_tuple
import xAODlib.result_handlers as rh
import clientlib.query_result_asts as query_result_asts

from clientlib.tuple_simplifier import remove_tuple_subscripts
from clientlib.function_simplifier import simplify_chained_calls
from clientlib.aggregate_shortcuts import aggregate_node_transformer
from cpplib.cpp_functions import find_known_functions, function_ast

import ast
import tempfile
from shutil import copyfile
import os
import sys
from urllib.parse import urlparse
import jinja2
from copy import copy

# Convert between Python comparisons and C++.
# TODO: Fill out all possible ones
compare_operations = {
    ast.Lt: '<',
    ast.LtE: '<=',
    ast.Gt: '>',
    ast.GtE: '>=',
    ast.Eq: '==',
    ast.NotEq: '!=',
}

# Result handlers - for each return type representation, add a handler that can process it
result_handlers = {
        rh.cpp_ttree_rep: rh.extract_result_TTree,
        rh.cpp_awkward_rep: rh.extract_awkward_result,
        rh.cpp_pandas_rep: rh.extract_pandas_result,
}

def type_of_rep(rep):
    '''
    Return a float unless it is an iterable. Then it is a vector of float.
    '''
    if rep.is_iterable:
        return "std::vector<float>"
    return "float"

class query_ast_visitor(ast.NodeVisitor):
    r"""
    Drive the conversion to C++ from the top level query
    """

    def __init__(self):
        r'''
        Initialize the visitor.
        '''
        # Tracks the output of the code.
        self._gc = generated_code()
        self._var_dict = {}
        self._result = None

    def include_files(self):
        return self._gc.include_files()

    def emit_query(self, e):
        'Emit the parsed lines'
        self._gc.emit_query_code(e)

    def emit_book(self, e):
        'Emit the parsed lines'
        self._gc.emit_book_code(e)

    def class_declaration_code(self):
        return self._gc.class_declaration_code()

    def visit (self, node):
        '''Visit a node. If the node already has a rep, then it has been visited and we
        do not need to visit it again.

        node - if the node has a rep, just return

        '''
        if hasattr(node, 'rep'):
            self._result = node.rep
            return
        else:
            return ast.NodeVisitor.visit(self, node)

    def generic_visit(self, node):
        '''Visit a generic node. If the node already has a rep, then it has been
        visited once and we do not need to visit it again.

        node - If the node has a rep, do not visit it.
    '''
        if hasattr(node, 'rep'):
            return
        else:
            return ast.NodeVisitor.generic_visit(self, node)

    def get_rep(self, node, use_generic_visit = False, reset_result = None, retain_scope = False):
        r'''Return the rep for the node. If it isn't set yet, then run our visit on it.

        node - The ast node to generate a representation for.
        use_generic_visit - if true do generic_visit rather than visit.
        reset_result - Reset the _result variable to this value if requested.
        retain_scope - If true, then the scope level will remain the same before and after the call.
        '''
        if not hasattr(node, 'rep'):
            s = self._gc.current_scope() if retain_scope else None
            self.generic_visit(node) if use_generic_visit else self.visit(node)
            if retain_scope:
                self._gc.set_scope(s)

        # Reset the result
        if reset_result is not None:
            self._result = reset_result

        return node.rep

    def resolve_id(self, id):
        'Look up the in our local dict'
        return self._var_dict[id] if id in self._var_dict else id

    def visit_Call_Lambda(self, call_node):
        'Call to a lambda function. This is book keeping and we dive in'

        for c_arg, l_arg in zip(call_node.args, call_node.func.args.args):
            self._var_dict[l_arg.arg] = c_arg

        # Next, process the lambda's body.
        self.visit(call_node.func.body)

        # Done processing the lambda. Remove the arguments
        # TODO: the below code should work, but it isn't for some reason.
        #       Probably because when we move functions we aren't moving the argument names
        #       correctly (the nesting). This is going to come back and bite us!
        # for l_arg in call_node.func.args.args:
        #     del self._var_dict[l_arg.arg]

    def assure_in_loop(self, collection):
        r'''
        Make sure that we are currently in a loop. For example, if we are
        looking at e.Jets.Aggregate then e.Jets hasn't started a loop. OTOH,
        looking at e.Jets.Select(j => j.pt).Aggregate, then we are already in
        a loop.

        collection: representation of a C++ collection or transformed iterable.
        '''
        # Before we do anything, make sure we are at the proper place for doing this loop
        self._gc.set_scope(collection.scope()) if collection.scope() is not None else None

        # Now, if the collection is already something are iterating on, then
        # we are done.
        if collection.is_iterable:
            return collection

        # Nope - can we iterate on it (might crash due to user error)
        if not hasattr(collection, "loop_over_collection"):
            raise BaseException('Do not know how to loop over the expression "{0}" (with type info: {1}).'.format(collection.as_cpp(), collection.cpp_type()))
        return collection.loop_over_collection(self._gc)


    def visit_Call_Aggregate(self, node):
        r'''Implement the aggregate algorithm in C++
        
        Our source we loop over, and we count out everything. The final result is whatever it is
        we are counting.

        Possible arguments to the call:

        - (acc lambda): the accumulator is set to the first element, and the lambda is called to
                        update it after that.
        - (const, acc lambda): the accumulator is set to the value, and then the lambda is called to
                        update it on every single element.
        - (start lambda, acc lambda): the accumulator is set to the start lambda call on the first
                        element in the sequence, and then acc is called to update it after that.

        Limitations: only floats for now!
        '''
        # Parse the argument list
        use_first_element_separately = False
        agg_lambda = None
        init_lambda = None
        init_val = None
        if len(node.args) == 1:
            agg_lambda = node.args[0]
            use_first_element_separately = True
        elif len(node.args) == 2:
            agg_lambda = node.args[1]
            if type(node.args[0]) is ast.Lambda:
                use_first_element_separately = True
                init_lambda = node.args[0]
            else:
                init_val = node.args[0]
                use_first_element_separately = False
        else:
            raise BaseException('Aggregate can have only one or two arguments')

        # Declare the thing that will be a result, and make sure everything above knows about it.
        result = cpp_variable(unique_name("aggResult"), self._gc.current_scope(), cpp_type="float")
        self._gc.declare_variable(result)

        # We have to initialized the variable to some value, and it depends on how the user
        # is trying to initialize things - first iteration or with a value.
        if use_first_element_separately:
            is_first_iter = cpp_variable(unique_name("is_first"), self._gc.current_scope(), cpp_type="bool")
            self._gc.declare_variable(is_first_iter)
            self._gc.add_statement(statement.set_var(is_first_iter, cpp_expression("true", self._gc.current_scope())))
        else:
            self._gc.add_statement(statement.set_var(result, self.get_rep(init_val)))

        # Store the scope so we cna pop back to it.
        scope = self._gc.current_scope()

        # Next, get the thing we are going to loop over, and generate the loop.
        # Pull the result out of the main result guy
        collection = self.get_rep(node.func.value)

        # Iterate over it now. Make sure we are looping over this thing.
        rep_iterator = self.assure_in_loop(collection)

        # If we have to use the first lambda to set the first value, then we need that code up front.
        if use_first_element_separately:
            if_first = statement.iftest(cpp_expression(is_first_iter.as_cpp(), self._gc.current_scope()))
            self._gc.add_statement(if_first)
            self._gc.add_statement(statement.set_var(is_first_iter, cpp_expression("false", self._gc.current_scope())))
            first_scope = self._gc.current_scope()

            if init_lambda is not None:
                call = ast.Call(init_lambda, [rep_iterator.as_ast()])
                self._gc.add_statement(statement.set_var(result, self.get_rep(call)))
            else:
                self._gc.add_statement(statement.set_var(result, rep_iterator))

            self._gc.set_scope(first_scope)
            self._gc.pop_scope()
            self._gc.add_statement(statement.elsephrase())

        # Perform the aggregation function. We need to call it with the value and the accumulator.
        call = ast.Call(func=agg_lambda, args=[result.as_ast(), rep_iterator.as_ast()])
        self._gc.add_statement(statement.set_var(result, self.get_rep(call)))

        # Finally, pop the whole thing off.
        self._gc.set_scope(scope)

        # Cache the results in our result incase we are skipping nodes in the AST.
        node.rep = result
        self._result = result

    def visit_Call_Member(self, call_node):
        'Method call on an object'

        # If this is a special type of Function call that we need to work with, split out here
        # before any processing is done.
        if (call_node.func.attr == "Aggregate"):
            return self.visit_Call_Aggregate(call_node)

        # Visit everything down a level.
        self.generic_visit(call_node)

        # figure out what we are calling against, and the
        # method name we are going to be calling against.
        calling_against = self.get_rep(call_node.func.value)
        function_name = call_node.func.attr

        # We support member calls that directly translate only. Here, for example, this is only for
        # obj.pt() or similar. The translation is direct.
        c_stub = calling_against.as_cpp() + ("->" if calling_against.is_pointer() else ".")
        self._result = cpp_expression(c_stub + function_name + "()", calling_against.scope())

    def visit_function_ast(self, call_node):
        'Drop-in replacement for a function'
        # Get the arguments
        cpp_func = call_node.func
        arg_reps = [self.get_rep(a) for a in call_node.args]

        # Code up a call
        r = cpp_expression('{0}({1})'.format(cpp_func.cpp_name, ','.join(a.as_cpp() for a in arg_reps)), self._gc.current_scope(), cpp_type = cpp_func.cpp_return_type)

        # Include files and return the resulting expression
        for i in cpp_func.include_files:
            self._gc.add_include(i)
        call_node.rep = r
        return r

    def visit_Call(self, call_node):
        r'''
        Very limited call forwarding.
        '''
        # What kind of a call is this?
        if type(call_node.func) is ast.Lambda:
            self.visit_Call_Lambda(call_node)
        elif type(call_node.func) is ast.Attribute:
            self.visit_Call_Member(call_node)
        elif type(call_node.func) is cpp_ast.CPPCodeValue:
            self._result = cpp_ast.process_ast_node(self, self._gc, self._result, call_node)
        elif type(call_node.func) is function_ast:
            self._result = self.visit_function_ast(call_node)
        else:
            raise BaseException("Do not know how to call '{0}'".format(ast.dump(call_node.func, annotate_fields=False)))
        call_node.rep = self._result

    def visit_Name(self, name_node):
        'Visiting a name - which should represent something'
        id = self.resolve_id(name_node.id)
        if isinstance(id, ast.AST):
            name_node.rep = self.get_rep(id)

    def visit_Subscript(self, node):
        'Index into an array. Check types, as tuple indexing can be very bad for us'
        v = self.get_rep(node.value)
        if v.cpp_type() != 'std::vector<double>':
            raise BaseException("Do not know how to take the index of type '{0}'".format(v.cpp_type()))
        index = self.get_rep(node.slice)
        # TODO: extract the type from the expression
        node.rep = cpp_expression("{0}.at({1})".format(v.as_cpp(), index.as_cpp()), self._gc.current_scope(), cpp_type="double")
        self._result = node.rep

    def visit_Index(self, node):
        'We can only do single items, we cannot do slices yet'
        v = self.get_rep(node.value)
        node.rep = v
        self._result = node

    def visit_Tuple(self, tuple_node):
        r'''
        Process a tuple. We visit each component of it, and build up a representation from each result.

        See github bug #21 for the special case of dealing with (x1, x2, x3)[0].
        '''
        tuple_node.rep = cpp_tuple(tuple(self.get_rep(e, retain_scope=True) for e in tuple_node.elts), self._gc.current_scope())
        self._result = tuple_node.rep

    def visit_BinOp(self, node):
        'An in-line add'
        left = self.get_rep(node.left)
        right = self.get_rep(node.right)

        if type(node.op) is ast.Add:
            r = cpp_expression("({0}+{1})".format(left.as_cpp(), right.as_cpp()), self._gc.current_scope())
        elif type(node.op) is ast.Div:
            r = cpp_expression("({0}/{1})".format(left.as_cpp(), right.as_cpp()), self._gc.current_scope())
        else:
            raise BaseException("Binary operator {0} is not implemented.".format(type(node.op)))

        # Cache the result to push it back further up.
        node.rep = r
        self._result = r

    def visit_IfExp(self, node):
        r'''
        We'd like to be able to use the "?" operator in C++, but the
        problem is lazy evaluation. It could be when we look at one or the
        other item, a bunch of prep work has to be done - and that will
        show up in separate statements. So we have to use if/then/else with
        a result value.
        '''
        
        # The result we'll store everything in.
        result = cpp_variable(unique_name("if_else_result"), self._gc.current_scope(), cpp_type="float")
        self._gc.declare_variable(result)

        # We always have to evaluate the test.
        current_scope = self._gc.current_scope()
        test_expr = self.get_rep(node.test)
        self._gc.add_statement(statement.iftest(test_expr))
        if_scope = self._gc.current_scope()

        # Next, we do the true and false if statement.
        self._gc.add_statement(statement.set_var(result, self.get_rep(node.body)))
        self._gc.set_scope(if_scope)
        self._gc.pop_scope()
        self._gc.add_statement(statement.elsephrase())
        self._gc.add_statement(statement.set_var(result, self.get_rep(node.orelse)))
        self._gc.set_scope(current_scope)

        # Done, the result is the rep of this node!
        node.rep = result
        self._result = result

    def visit_Compare(self, node):
        'A compare between two things. Python supports more than that, but not implemented yet.'
        if len(node.ops) != 1:
            raise BaseException("Do not support 1 < a < 10 comparisons yet!")
        
        left = self.get_rep(node.left)
        right = self.get_rep(node.comparators[0])

        r = cpp_expression('({0}{1}{2})'.format(left.as_cpp(), compare_operations[type(node.ops[0])], right.as_cpp()), self._gc.current_scope())
        node.rep = r
        self._result = r

    def visit_BoolOp(self, node):
        '''A bool op like And or Or on a set of values
        This is a bit more complex than just "anding" things as we want to make sure to short-circuit the
        evaluation if we need to.
        '''

        # The result of this test
        result = cpp_variable(unique_name('bool_op'), self._gc.current_scope(), cpp_type='bool')
        self._gc.declare_variable (result)

        # How we check and short-circuit depends on if we are doing and or or.
        check_expr = result.as_cpp() if type(node.op) == ast.And else '!{0}'.format(result.as_cpp())
        check = cpp_expression(check_expr, self._gc.current_scope(), cpp_type='bool')

        first = True
        scope = self._gc.current_scope()
        for v in node.values:
            if not first:
                self._gc.add_statement(statement.iftest(check))

            rep_v = self.get_rep(v)
            self._gc.add_statement(statement.set_var(result, rep_v))

            if not first:
                self._gc.set_scope(scope)
            first = False
        
        # Cache result variable so those above us have something to use.
        self._result = result
        node.rep = result


    def visit_Num(self, node):
        node.rep = cpp_expression(node.n, self._gc.current_scope())
        self._result = node.rep

    def visit_Str(self, node):
        node.rep = cpp_expression('"{0}"'.format(node.s), self._gc.current_scope())
        self._result = node.rep

    def visit_resultTTree(self, node):
        '''This AST means we are taking an iterable and converting it to a ROOT file.
        '''
        # Get the representations for each variable.
        self.generic_visit(node)
        v_rep_not_norm = self.get_rep(node.source)
        v_rep = v_rep_not_norm.tup() if type(v_rep_not_norm) is cpp_tuple else (v_rep_not_norm,)
        if len(v_rep) != len(node.column_names):
            raise BaseException("Number of columns ({0}) is not the same as labels ({1}) in TTree creation".format(len(v_rep), len(node.column_names)))

        # Next, look at each on in turn to decide if it is a vector or a simple variable.
        var_names = [(name, cpp_variable(unique_name(name, is_class_var=True), self._gc.current_scope(), cpp_type=type_of_rep(rep))) 
                    for name, rep in zip(node.column_names, v_rep)]

        # For each incoming variable, we need to declare something we are going to write.
        for cv in var_names:
            self._gc.declare_class_variable(cv[1])

        # Next, emit the booking code
        tree_name = unique_name("analysis_tree")
        self._gc.add_book_statement(statement.book_ttree(tree_name, var_names))

        # Note that the output file and tree are what we are going to return.
        node.rep = rh.cpp_ttree_rep("data.root", tree_name, self._gc.current_scope())

        # For each varable we need to save, cache it or push it back, depending.
        # Make sure that it happens at the proper scope, where what we are after is defined!
        s_orig = self._gc.current_scope()
        for e in zip(v_rep, var_names):
            # Set the scope. Normally we want to do it where the variable was calculated
            # (think of cases when you have to calculate something with a `push_back`),
            # but if the variable was already calculated, we want to make sure we are at least
            # in the same scope as the tree fill.
            if scope_is_deeper(e[0].scope(), v_rep_not_norm.scope()):
                self._gc.set_scope(v_rep_not_norm.scope())
            else:
                self._gc.set_scope(e[0].scope())

            # If the variable is something we are iterating over, then fill it, otherwise,
            # just set it.
            if e[0].is_iterable:
                self._gc.add_statement(statement.push_back(e[1][1], e[0]))
            else:
                self._gc.add_statement(statement.set_var(e[1][1], e[0]))

        # The fill statement. This should happen at the scope where the tuple was defined.
        self._gc.set_scope(v_rep_not_norm.scope())
        self._gc.add_statement(statement.ttree_fill(tree_name))
        for e in zip(v_rep, var_names):
            if e[0].is_iterable:
                self._gc.add_statement(statement.container_clear(e[1][1]))

        # And we are a terminal, so pop off the block.
        self._gc.set_scope(s_orig)
        self._gc.pop_scope()

    def visit_resultAwkwardArray(self, node):
        '''
        The result of this guy is an awkward array. We generate a token here, and invoke the resultTTree in order to get the
        actual ROOT file written. Later on, when dealing with the result stuff, we extract it into an awkward array.
        '''
        ttree = query_result_asts.resultTTree(node.source, node.column_names)
        r = self.get_rep(ttree)
        node.rep = rh.cpp_awkward_rep(r.filename, r.treename, self._gc.current_scope())
        self._result = node.rep

    def visit_resultPandasDF(self, node):
        '''
        The result of this guy is an pandas dataframe. We generate a token here, and invoke the resultTTree in order to get the
        actual ROOT file written. Later on, when dealing with the result stuff, we extract it into an awkward array.
        '''
        ttree = query_result_asts.resultTTree(node.source, node.column_names)
        r = self.get_rep(ttree)
        node.rep = rh.cpp_pandas_rep(r.filename, r.treename, self._gc.current_scope())
        self._result = node.rep

    def visit_Select(self, select_ast):
        'Transform the iterable from one form to another'

        # Make sure we are in a loop
        s_rep = self.get_rep(select_ast.source)
        loop_var = self.assure_in_loop(s_rep)

        # Simulate this as a "call"
        selection = lambda_unwrap(select_ast.selection)
        c = ast.Call(func=selection, args=[loop_var.as_ast()])
        rep = self.get_rep(c)

        rep.is_iterable = True
        select_ast.rep = rep

    def visit_SelectMany(self, node):
        r'''
        Apply the selection function to the base to generate a collection, and then
        loop over that collection.
        '''
        # We need to "call" the source with the function. So build up a new
        # call, and then visit it.

        c = ast.Call(func=node.selection.body[0].value, args=[node.source])
        rep_collection = self.get_rep(c)

        # Get the collection, and then generate the loop over it.
        # It could be that this comes back from something that is already iterating (like a Select statement),
        # in which case we are already looping.
        rep_iterator = self.assure_in_loop(rep_collection)

        node.rep = rep_iterator

    def visit_Where(self, node):
        'Apply a filtering to the current loop.'

        # Make sure we are in a loop
        s_rep = self.get_rep(node.source)
        loop_var = self.assure_in_loop(s_rep)

        # Simulate the filtering call - we want the resulting value to test.
        filter = lambda_unwrap(node.filter)
        c = ast.Call(func=filter, args=[loop_var.as_ast()])
        rep = self.get_rep(c)

        # Create an if statement
        self._gc.add_statement(statement.iftest(rep))

        # Finally, our result is basically what we had for the source.
        loop_var.set_scope(self._gc.current_scope())
        node.rep = loop_var
        self._result = loop_var

    def visit_First(self, node):
        'We are in a sequence. Take the first element of the sequence and use that for future things.'

        # Make sure we are in a loop.
        s_rep = self.get_rep(node.source)
        loop_var = self.assure_in_loop(s_rep)

        # Next, mark an external scope edge with a variable that will track when we hit first.
        # To do this, we have to go up to the loop we are currently looking at.
        # TODO: Scope needs some methods so we aren't using magic numbers like [0] and [1].
        is_first = cpp_variable(unique_name('is_first'), s_rep.scope(), cpp_type='bool', initial_value='true')
        var_book_statement = s_rep.scope()[0][-1]
        var_book_statement.declare_variable(is_first)

        # Now, as long as is_first is true, we can execute things inside this statement.
        s = statement.iftest(is_first)
        self._gc.add_statement(s)
        self._gc.add_statement(statement.set_var(is_first, cpp_expression('false', self._gc.current_scope(), cpp_type='bool')))

        # Finally, the result of first is the object that we are looping over.
        new_loop_var = copy(loop_var)
        new_loop_var.is_iterable = False
        new_loop_var.set_scope(self._gc.current_scope())

        node.rep = new_loop_var
        self._result = new_loop_var


class cpp_source_emitter:
    r'''
    Helper class to emit C++ code as we go
    '''

    def __init__(self):
        self._lines_of_query_code = []
        self._indent_level = 0

    def add_line(self, l):
        'Add a line of code, automatically deal with the indent'
        if l == '}':
            self._indent_level -= 1

        self._lines_of_query_code += [
            "{0}{1}".format("  " * self._indent_level, l)]

        if l == '{':
            self._indent_level += 1

    def lines_of_query_code(self):
        return self._lines_of_query_code

# The following was copied from: https://www.oreilly.com/library/view/python-cookbook/0596001673/ch04s22.html
def _find(pathname, matchFunc=os.path.isfile):
    for dirname in sys.path:
        candidate = os.path.join(dirname, pathname)
        if matchFunc(candidate):
            return candidate
    raise BaseException("Can't find file %s" % pathname)

def find_file(pathname):
    return _find(pathname)

def find_dir(path):
    return _find(path, matchFunc=os.path.isdir)

class atlas_xaod_executor:
    def __init__(self, dataset):
        self._ds = dataset

    def copy_template_file(self, j2_env, info, template_file, final_dir):
        'Copy a file to a final directory'
        j2_env.get_template(template_file).stream(info).dump(final_dir + '/' + template_file)
    
    def apply_ast_transformations(self, ast):
        r'''
        Run through all the transformations that we have on tap to be run on the client side.
        Return a (possibly) modified ast.
        '''

        # Do tuple resolutions. This might eliminate a whole bunch fo code!
        ast = aggregate_node_transformer().visit(ast)
        ast = simplify_chained_calls().visit(ast)
        ast = remove_tuple_subscripts().visit(ast)
        ast = find_known_functions().visit(ast)

        # Any C++ custom code needs to be threaded into the ast
        ast = cpp_ast.cpp_ast_finder().visit(ast)

        # And return the modified ast
        return ast

    def evaluate(self, ast):
        r"""
        Evaluate the ast over the file that we have been asked to run over
        """

        # Visit the AST to generate the code structure and find out what the
        # result is going to be.
        qv = query_ast_visitor()
        result_rep = qv.get_rep(ast)

        # Emit the C++ code into our dictionaries to be used in template generation below.
        query_code = cpp_source_emitter()
        qv.emit_query(query_code)
        book_code = cpp_source_emitter()
        qv.emit_book(book_code)
        class_dec_code = qv.class_declaration_code()
        includes = qv.include_files()

        # Create a temp directory in which we can run everything.
        with tempfile.TemporaryDirectory() as local_run_dir:
            os.chmod(local_run_dir, 0o777)

            # Parse the dataset. Eventually, this needs to be normalized, but for now.
            (_, netloc, path, _, _, _) = urlparse(self._ds)
            datafile = netloc + path
            datafile_dir = os.path.dirname(datafile)
            datafile_name = os.path.basename(datafile)
            info = {}
            info['data_file_name'] = datafile_name
            info['query_code'] = query_code.lines_of_query_code()
            info['book_code'] = book_code.lines_of_query_code()
            info['class_dec'] = class_dec_code
            info['include_files'] = includes

            # Next, copy over and fill the template files that will control the xAOD running.
            # Assume they are located relative to the python include path.
            template_dir = find_dir("./R21Code")
            j2_env = jinja2.Environment(
                loader=jinja2.FileSystemLoader(template_dir))
            self.copy_template_file(
                j2_env, info, 'ATestRun_eljob.py', local_run_dir)
            self.copy_template_file(
                j2_env, info, 'package_CMakeLists.txt', local_run_dir)
            self.copy_template_file(j2_env, info, 'query.cxx', local_run_dir)
            self.copy_template_file(j2_env, info, 'query.h', local_run_dir)
            self.copy_template_file(j2_env, info, 'runner.sh', local_run_dir)

            os.chmod(os.path.join(local_run_dir, 'runner.sh'), 0o755)

            # Now use docker to run this mess
            docker_cmd = "docker run --rm -v {0}:/scripts -v {0}:/results -v {1}:/data  atlas/analysisbase:21.2.62 /scripts/runner.sh".format(
                local_run_dir, datafile_dir)
            r = os.system(docker_cmd)
            print ("Process result is ", r)
            os.system("type " + os.path.join(local_run_dir, "query.cxx"))

            # Extract the result.
            if type(result_rep) not in result_handlers:
                raise BaseException('Do not know how to process result of type {0}.'.format(type(result_rep).__name__))
            return result_handlers[type(result_rep)](result_rep, local_run_dir)
