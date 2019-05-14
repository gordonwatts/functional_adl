# The representation, in C++ code, of a particular variable.
# This is an abstract class. Almost everyone is going to have to
# implement one.
#
import xAODlib.statement as statement
from cpplib.cpp_vars import unique_name
import ast

class cpp_rep_base:
    r'''
    Represents a term or collection in C++ code. Queried to perform certian actions on the C++ term or collection.

    This is an abstract class for the most part. Do not override things that aren't needed - that way the system will
    know when the user tries to do something that they shouldn't have.
    '''
    def __init__(self, scope, is_pointer = False):
        # Set to true when we represent an item in an interable type.
        self.is_iterable = False
        self._ast = None
        self._scope = scope
        self._is_pointer = is_pointer

    def is_pointer(self):
        return self._is_pointer

    def as_cpp(self):
        'Return the C++ code to represent whatever we are holding'
        raise BaseException("Subclasses need to implement in for as_cpp")

    def as_ast(self):
        'Return a python AST for this representation'
        if not self._ast:
            self.make_ast()
        return self._ast
    
    def make_ast(self):
        'Create and fill the _ast variable with the ast for this rep'
        raise BaseException("Subclasses need to implement this in as_ast")

    def scope(self):
        'Return the scope at which this representation was defined'
        return self._scope

    def set_scope(self, s):
        'Change the scope of this variable to something new.'
        self._scope = s

class cpp_variable(cpp_rep_base):
    r'''
    The representation for a simple variable.
    '''

    def __init__(self, name, scope, is_pointer=False, cpp_type = None, initial_value = None):
        '''
        Craete a new variable

        name - C++ name of the variable
        scope - Scope at which this variable is being defined
        is_pointer - True if we need to use -> to dereference it
        cpp_type - tye type of the variable, or implied (somehow)
        inital_value - if set, then it will be used to declare the variable and initially set it.
        '''
        cpp_rep_base.__init__(self, scope, is_pointer=is_pointer)
        self._cpp_name = name
        self._cpp_type = cpp_type
        self._ast = None
        self._initial_value = initial_value

    def name(self):
        return self._cpp_name

    def initial_value(self):
        return self._initial_value

    def as_cpp(self):
        return self._cpp_name

    def cpp_type(self):
        return self._cpp_type

    def make_ast(self):
        self._ast = ast.Name(self.as_cpp(), ast.Load())
        self._ast.rep = self

class cpp_tuple(cpp_rep_base):
    r'''
    Sometimes we need to carry around a tuple. Unfortunately, we can't "add" items onto a regular
    python tuple (like is_iterable, etc.). So we have to have this special wrapper.
    '''
    def __init__ (self, t, scope):
        cpp_rep_base.__init__(self, scope)
        self._tuple = t
    
    def tup(self):
        return self._tuple

class cpp_expression(cpp_rep_base):
    r'''
    Represents a small bit of C++ code that is an expression. For example "a+b". It does not hold full
    statements.
    '''
    def __init__(self, expr, scope, cpp_type=None, is_pointer = False):
        cpp_rep_base.__init__(self, scope, is_pointer=False)
        self._expr = expr
        self._cpp_type = cpp_type

    def as_cpp(self):
        return self._expr

class cpp_collection(cpp_variable):
    r'''
    The representation for a collection. Something that can be iterated over using
    the standard for loop code.
    '''

    def __init__(self, name, scope, is_pointer=False, cpp_type=None):
        r'''Remember the C++ name of this variable

        name - The name of the variable we are going to save here
        is_pointer - do we need to de-ref it to access it?
        '''
        cpp_variable.__init__(self, name, scope, is_pointer=is_pointer, cpp_type=cpp_type)

    def loop_over_collection(self, gc):
        r'''
        Generate a loop over the collection

        gc - generated_code object to store code in

        returns:

        obj - term containing the object that is the loop variable
        '''

        # Create the var we are going to iterate over, and figure out how to reference
        # What we are doing.
        v = cpp_variable(unique_name("i_obj"), scope = None, is_pointer=True)
        v.is_iterable = True
        c_ref = ("*" + self.name()) if self.is_pointer() else self.name()

        # Finally, the actual loop statement.
        gc.add_statement(statement.loop(c_ref, v.name()))
        v.set_scope(gc.current_scope())

        # and that iterating variable is the rep
        return v
