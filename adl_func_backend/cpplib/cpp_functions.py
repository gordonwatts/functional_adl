# Infrastructure to replace simple functions (like "abs") in python with their
# equivalent in C++.
import ast
from collections import namedtuple

class FunctionAST(ast.AST):
    '''
    An AST node that represents a function that can be a drop-in replacement for
    a python function
    '''
    def __init__ (self, cpp_name, include_files, cpp_return_type):
        ''' Initialize an AST node that represents a C++ drop-in function call

        cpp_name: The C++ name that we will use to do the call
        include_files: List of include files to be put at the start of the emitted source.
        '''
        self.cpp_name = cpp_name
        self.include_files = include_files
        self.cpp_return_type = cpp_return_type
        self.fields = []

class find_known_functions(ast.NodeTransformer):
    def visit_Call(self, node):
        'Look for a call to a Name function that is in our list'
        # First go one level down.
        self.generic_visit(node)

        # See if we are candidate for replacement
        # Get a fully qualified name as possible.
        if type(node.func) is not ast.Name:
            return node

        try:
            fnc = eval(node.func.id)
            fnc_name = '{0}.{1}'.format(fnc.__module__, node.func.id)
        except NameError:
            fnc_name = node.func.id
    
        if fnc_name not in functions_to_replace:
            return node

        # Build the replacement.        
        info = functions_to_replace[fnc_name]
        node.func = FunctionAST(info.cpp_name, info.include_files, info.cpp_return_type)
        
        return node        

def add_function_mapping (python_name, cpp_name, include_files, return_type):
    '''Add a re-mapping from a python function to an actual function.

    python_name: fully qualified name of the python function
    cpp_name: fully qualified name of the C++ function
    include_files: any include files that should be included in the C++ source. Can also be a single string.
    return_type: C++ return type
    '''
    global functions_to_replace
    functions_to_replace[python_name] = cpp_function(cpp_name, include_files if type(include_files) is list else [include_files,], return_type)

# The list of functions to do the replacement
functions_to_replace = {}

# The named tuple that stores the replacement info.
cpp_function = namedtuple('cpp_function', ['cpp_name', 'include_files', 'cpp_return_type'])

# A few simple functions:
add_function_mapping('builtins.abs', 'std::abs', 'cmath', 'double')
add_function_mapping('sin', 'std::sin', 'cmath', 'double')
