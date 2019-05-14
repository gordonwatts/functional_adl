# Use this node in the ast when you want to add some custom C++
#
# This is one mechanism to allow for a leaky abstraction.
import ast
from cpplib.cpp_vars import unique_name
from cpplib.cpp_representation import cpp_expression
import xAODlib.statement as statements

# The list of methods and the re-write functions for them. Each rewrite function
# is called with the Call node, which includes arguments, names, etc. It should return
# None or a cpp_ast.
method_names = {}

class CPPCodeValue (ast.AST):
    r'''
    Represents a C++ bit of code that returns a value. Like a function call or a member call.
    Use the be-fore the wire visit phase of processing to look for a pattern that needs
    to generate AST code, like a method call. Then place this AST in place of the function.
    The back-end will then do the rendering useing the information included below.
    '''

    def __init__(self):
        # Files that need to be included at the top of the generated C++ file
        self.include_files = []

        # Code that is run once at the start of each "event"
        self.initialization_code = []

        # Code that is run when the particular bit of code needs to be invoked (e.g. in the middle of a hot loop).
        # This is invoked in its own scope (between "{" and "}") so there are no variable collisions.
        self.running_code = []

        # The arguments to the function. These are "correctly" mapped into the argument values
        # that are passed to the function and then a text replacement is done in the code.
        self.args = []

        # Special replacement if this is a method call. A tuple. THe first item is the string to be replaced in the
        # code. The second is the name against which we should be making the call (e.g. if j is the current jet variable,
        # the tuple might be ("obj", "j")).
        self.replacement_instance_obj = None

        # A string representing the result value. This must be a simple variable. It will get replaced
        # in all the code lines above.
        self.result = None

        # Representation to use for the resulting variable. Includes C++ type information.
        self.result_rep = None

        # We have no further fields for the ast machinery to explore, so this is empty for now.
        self.fields=[]

class cpp_ast_finder(ast.NodeTransformer):
    r'''
    Look through the complete ast and replace method calls that are to a C++ plug in with a c++ ast
    node.
    '''

    def try_call (self, name, node):
        'Try to use name to do the call. Returns (ok, result) monad'
        if name in method_names:
            cpp_call_ast = method_names[name](node)
            return (cpp_call_ast is not None, cpp_call_ast)
        return (False, None)

    def visit_Call(self, node):
        r'''
        Looking for a member call of a particular name. We rewrite that as
        another name.
        WARNING: currently the namespace is global, so the parent type doesn't matter!
        '''

        # Make sure all parts of this AST are visited properly before we attempt to
        # understand the call.
        self.generic_visit(node)

        # Examine the func to see if this is a member call.
        func = node.func
        if (type(func) is ast.Attribute) and (type(func.value) is ast.Name):
            ok, new_node = self.try_call(func.attr, node)
            if ok:
                return new_node
        elif type(func) is ast.Name:
            ok, new_node = self.try_call(func.id, node)
            if ok:
                return new_node

        return node

def process_ast_node(visitor, gc, current_loop_value, call_node):
    r'''Inject the proper code into the output stream to deal with this C++ code.
    
    We expect this to be run on the back-end of the system.

    visitor - The node visitor that is converting the code into C++
    gc - the generated code object that we fill with actual code
    current_loop_variable - the thing we are currently iterating over
    call_node - a Call ast node, with func being a CPPCodeValue.

    Result:
    representation - A value that represents the output
    '''

    # We write everything into a new scope to prevent conflicts. So we have to declare the result ahead of time.
    cpp_ast_node = call_node.func
    result_rep = cpp_ast_node.result_rep
    result_rep.set_scope(gc.current_scope())
    gc.declare_variable(result_rep)

    # Include files
    for i in cpp_ast_node.include_files:
        gc.add_include(i)

    # Build the dictionary for replacement for the object we are calling
    # against, if any.
    repl_list = []
    if cpp_ast_node.replacement_instance_obj is not None:
        repl_list += [(cpp_ast_node.replacement_instance_obj[0], visitor.resolve_id(cpp_ast_node.replacement_instance_obj[1]).rep.name())]

    # Process the arguments that are getting passed to the function
    for arg,dest in zip(cpp_ast_node.args, call_node.args):
        rep = visitor.get_rep(dest)
        repl_list += [(arg, rep.as_cpp())]

    # Emit the statements.
    blk = statements.block()
    visitor._gc.add_statement(blk)

    for s in cpp_ast_node.running_code:
        l = s
        for src,dest in repl_list:
            l = l.replace(src, dest)            
        blk.add_statement(statements.arbitrary_statement(l))

    # Set the result and close the scope
    blk.add_statement(statements.set_var(result_rep, cpp_expression(cpp_ast_node.result, gc.current_scope())))
    gc.pop_scope()

    return result_rep
