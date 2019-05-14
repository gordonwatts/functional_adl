# Helpers for LINQ operators and LINQ expressions in AST form.
# Utility routines to manipulate LINQ expressions.
import adl_func_client.query_ast as query_ast
from adl_func_client.event_dataset import EventDataset
import ast
from typing import Optional

class simplify_chained_calls(ast.NodeTransformer):
    '''
    A python 3 AST tranformer that tries to normalize queries (combine filter operations, etc.).
    This is to normalize the query, make the queries look the same, etc. Most importantly, we do this
    to cleanly evaluate things like tuples (which should not show up at the back end),
    we must move around various functions, evaluate others, etc., where we can. This AST transformer
    does that work.
    '''

    def __init__(self):
        self._arg_dict = {}

    def visit_Select_of_Select(self, parent, selection):
        r'''
        seq.Select(x: f(x)).Select(y: g(y))
        => Select(Select(seq, x: f(x)), y: g(y))
        is turned into
        seq.Select(x: g(f(x)))
        => Select(seq, x: g(f(x)))
        '''
        func_g = selection
        func_f = parent.selection

        # Convolute the two functions
        # TODO: should this be generic of just visit?
        new_selection = self.visit(convolute(func_g, func_f))

        # And return the parent select with the new selection function
        return Select(parent.source, new_selection)

    def visit_Select_of_SelectMany(self, parent, selection):
        r'''
        seq.SelectMany(x: f(x)).Select(y: g(y))
        => Select(SelectMany(seq, x: f(x)), y: g(y))
        is turned into
        seq.SelectMany(x: f(x).Select(y: g(y)))
        => SelectMany(seq, x: Select(f(x), y: g(y)))
        '''
        func_g = selection
        func_f = parent.selection

        return self.visit(SelectMany(parent.source, lambda_body_replace(func_f, Select(lambda_body(func_f), func_g))))

    def visit_Select(self, node):
        r'''
        Transformation #1:
        seq.Select(x: f(x)).Select(y: g(y))
        => Select(Select(seq, x: f(x)), y: g(y))
        is turned into
        seq.Select(x: g(f(x)))
        => Select(seq, x: g(f(x)))

        Transformation #2:
        seq.SelectMany(x: f(x)).Select(y: g(y))
        => Select(SelectMany(seq, x: f(x)), y: g(y))
        is turned into
        seq.SelectMany(x: f(x).Select(y: g(y)))
        => SelectMany(seq, x: Select(f(x), y: g(y)))

        Transformation #3:
        seq.Where(x: f(x)).Select(y: g(y))
        => Select(Where(seq, x: f(x), y: g(y))
        is not altered.
        '''

        parent_select = self.visit(node.source)
        if type(parent_select) is Select:
            return self.visit_Select_of_Select(parent_select, node.selection)
        elif type(parent_select) is SelectMany:
            return self.visit_Select_of_SelectMany(parent_select, node.selection)
        else:
            selection = self.visit(node.selection)
            if lambda_is_identity(selection):
                return parent_select
            else:
                return Select(parent_select, self.visit(node.selection))

    def visit_SelectMany_of_Select(self, parent, selection):
        '''
        seq.Select(x: f(x)).SelectMany(y: g(y))
        => SelectMany(Select(seq, x: f(x)), y:g(y))
        is turned into
        seq.SelectMany(x: g(f(x)))
        => SelectMany(seq, x: g(f(x)))
        '''
        func_g = selection
        func_f = parent.selection
        seq = parent.source

        new_selection = self.generic_visit(convolute(func_g, func_f))
        return self.visit(SelectMany(seq, new_selection))
    
    def visit_SelectMany_of_SelectMany(self, parent, selection):
        '''
        Transformation #1:
        seq.SelectMany(x: f(x)).SelectMany(y: f(y))
        => SelectMany(SelectMany(seq, x: f(x)), y: f(y))
        is turned into:
        seq.SelectMany(x: f(x).SelectMany(y: f(y)))
        => SelectMany(seq, x: SelectMany(f(x), y: f(y)))
        '''
        #TODO: Get to the point we can actually test that this works correctly
        raise BaseException('untested')
        func_g = selection
        func_f = parent.selection

        return self.visit(SelectMany(parent.source, lambda_body_replace(func_f, SelectMany(lambda_body(func_f), func_g))))

    def visit_SelectMany(self, node):
        r'''
        Transformation #1:
        seq.SelectMany(x: f(x)).SelectMany(y: f(y))
        => SelectMany(SelectMany(seq, x: f(x)), y: f(y))
        is turned into:
        seq.SelectMany(x: f(x).SelectMany(y: f(y)))
        => SelectMany(seq, x: SelectMany(f(x), y: f(y)))

        Transformation #2:
        seq.Select(x: f(x)).SelectMany(y: g(y))
        => SelectMany(Select(seq, x: f(x)), y:g(y))
        is turned into
        seq.SelectMany(x: g(f(x)))
        => SelectMany(seq, x: g(f(x)))

        Transformation #3:
        seq.Where(x: f(x)).SelectMany(y: g(y))
        '''
        parent_select = self.visit(node.source)
        if type(parent_select) is SelectMany:
            return self.visit_SelectMany_of_SelectMany(parent_select, node.selection)
        elif type(parent_select) is Select:
            return self.visit_SelectMany_of_Select(parent_select, node.selection)
        else:
            return SelectMany(parent_select, self.visit(node.selection))

    def visit_Where_of_Where(self, parent, filter):
        '''
        seq.Where(x: f(x)).Where(x: g(x))
        => Where(Where(seq, x: f(x)), y: g(y))
        is turned into
        seq.Where(x: f(x) and g(y))
        => Where(seq, x: f(x) and g(y))
        '''
        func_f = parent.filter
        func_g = filter

        arg = arg_name()
        return self.visit(Where(parent.source, lambda_build(arg, ast.BoolOp(ast.And(), [lambda_call(arg, func_f), lambda_call(arg, func_g)]))))

    def visit_Where_of_Select(self, parent, filter):
        '''
        seq.Select(x: f(x)).Where(y: g(y))
        => Where(Select(seq, x: f(x)), y: g(y))
        Is turned into:
        seq.Where(x: g(f(x))).Select(x: f(x))
        => Select(Where(seq, x: g(f(x)), f(x))
        '''
        func_f = parent.selection
        func_g = filter
        seq = parent.source

        w = Where(seq, self.visit(convolute(func_g, func_f)))
        s = Select(w, func_f)

        # Recursively visit this mess to see if the Where needs to move further up.
        return self.visit(s)

    def visit_Where_of_SelectMany(self, parent, filter):
        '''
        seq.SelectMany(x: f(x)).Where(y: g(y))
        => Where(SelectMany(seq, x: f(x)), y: g(y))
        Is turned into:
        seq.SelectMany(x: f(x).Where(y: g(y)))
        => SelectMany(seq, x: Where(f(x), g(y)))
        '''
        func_f = parent.selection
        func_g = filter
        seq = parent.source

        return self.visit(SelectMany(seq, lambda_body_replace(func_f, Where(lambda_body(func_f), func_g))))

    def visit_Where(self, node):
        r'''
        Transformation #1:
        seq.Where(x: f(x)).Where(x: g(x))
        => Where(Where(seq, x: f(x)), y: g(y))
        is turned into
        seq.Where(x: f(x) and g(y))
        => Where(seq, x: f(x) and g(y))

        Transformation #2:
        seq.Select(x: f(x)).Where(y: g(y))
        => Where(Select(seq, x: f(x)), y: g(y))
        Is turned into:
        seq.Where(x: g(f(x))).Select(x: f(x))
        => Select(Where(seq, x: g(f(x)), f(x))
        
        Transformation #3:
        seq.SelectMany(x: f(x)).Where(y: g(y))
        => Where(SelectMany(seq, x: f(x)), y: g(y))
        Is turned into:
        seq.SelectMany(x: f(x).Where(y: g(y)))
        => SelectMany(seq, x: Where(f(x), g(y)))
        '''
        parent_where = self.visit(node.source)
        if type(parent_where) is Where:
            return self.visit_Where_of_Where(parent_where, node.filter)
        elif type(parent_where) is Select:
            return self.visit_Where_of_Select(parent_where, node.filter)
        elif type(parent_where) is SelectMany:
            return self.visit_Where_of_SelectMany(parent_where, node.filter)
        else:
            f = self.visit(node.filter)
            if lambda_is_true(f):
                return parent_where
            else:
                return Where(parent_where, f)
    
    def visit_Call(self, call_node):
        '''We are looking for cases where an argument is another function or expression.
        In that case, we want to try to get an evaluation of the argument, and replace it in the
        AST of this function. This only works of the function we are calling is a lambda.
        '''
        if type(call_node.func) is ast.Lambda:
            arg_asts = [self.visit(a) for a in call_node.args]
            for a_name, arg in zip(call_node.func.args.args, arg_asts):
                # TODO: These have to be removed correctly (deal with common arg names!)
                self._arg_dict[a_name.arg] = arg
            # Now, evaluate the expression, and then lift it.
            return self.visit(call_node.func.body)
        else:
            return self.generic_visit(call_node)

    def visit_Subscript_Tuple(self, v, s):
        '''
        (t1, t2, t3...)[1] => t2

        Only works if index is a number
        '''
        if type(s.value) is not ast.Num:
            return ast.Subscript(v, s, ast.Load())
        n = s.value.n
        if n >= len(v.elts):
            raise BaseException("Attempt to access the {0}th element of a tuple only {1} values long.".format(n, len(v.value.elts)))

        return v.elts[n]

    def visit_Subscript_Of_First(self, first, s):
        '''
        Convert a seq.First()[0]
        ==>
        seq.Select(l: l[0]).First()

        Other work will do the conversion as needed.
        '''
        source = first.source

        # Build the select that starts from the source and does the slice.
        a = arg_name()
        select = Select(source, lambda_build(a, ast.Subscript(ast.Name(a, ast.Load()), s, ast.Load())))

        return self.visit(First(select))

    def visit_Subscript(self, node):
        r'''
        Simple Reduction
        (t1, t2, t3...)[1] => t2

        Move [] past a First()
        seq.First()[0] => seq.Select(j: j[0]).First()
        '''
        v = self.visit(node.value)
        s = self.visit(node.slice)
        if type(v) is ast.Tuple:
            return self.visit_Subscript_Tuple(v, s)

        if type(v) is First:
            return self.visit_Subscript_Of_First(v, s)

        # Nothing interesting, so do the normal thing several levels down.
        return ast.Subscript(v, s, ctx=ast.Load())

    def visit_Name(self, name_node):
        'Do lookup and see if we should translate or not.'
        if name_node.id in self._arg_dict:
            return self._arg_dict[name_node.id]
        return name_node

    def visit_Attribute(self, node):
        'Make sure to make a new version of the Attribute so it does not get reused'
        return ast.Attribute(value=self.visit(node.value), attr=node.attr, ctx=ast.Load())

def find_dataset(a: ast.AST) -> EventDataset:
    r'''
    Given an input query ast, find the EventDataSet and return it.

    Args:
        a:      An AST that represents a query

    Returns:
        The `EventDataSet` at the root of this query. It will not be None.

    Exceptions:
        If there is more than one `EventDataSet` found in the query or if there
        is no `EventDataSet` at the root of the query, then an exception is thrown.
    '''

    class ds_finder(ast.NodeVisitor):
        def __init__(self):
            self.ds: Optional[EventDataset] = None
        
        def visit_EventDataset(self, node):
            if self.ds is not None:
                raise BaseException("AST Query has more than one EventDataSet in it!")
            self.ds = node

        def generic_visit(self, node):
            ast.NodeVisitor.generic_visit(self, node)
    
    ds_f = ds_finder()
    ds_f.visit(a)

    if ds_f.ds is None:
        raise BaseException("AST Query has no root EventDataSet")

    return ds_f.ds
