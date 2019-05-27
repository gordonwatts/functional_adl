# Statements
from __future__ import annotations
import adl_func_backend.cpplib.cpp_representation as crep
from typing import Any, Optional

class BlockException (BaseException):
    def __init__ (self, message):
        BaseException.__init__(self, message)

class block:
    'This is a bock of statements surrounded by a scoping (like open close bracket, for loop, etc.)'

    def __init__(self):
        self._statements = []
        self._variables = []
        self._rep_dict = {}

    def add_statement(self, s):
        'Add statement s to the list of statements'
        self._statements += [s]

    def declare_variable(self, n):
        'Declare a variable n, which is of type cpp_variable'
        self._variables += [n]

    def emit(self, e):
        'Render the block of code'
        e.add_line("{")
        for v in self._variables:
            init_value = "" if not isinstance(v,crep.cpp_variable) or not v.initial_value() else " ({0})".format(v.initial_value().as_cpp())
            e.add_line("{0} {1}{2};".format(v.cpp_type(), v.as_cpp(), init_value))
        for s in self._statements:
            s.emit(e)
        e.add_line("}")

    def get_rep(self, name: Any) -> Any:
        '''Return the representation for some object. If we do not know its value
        then ask our parent for the value. Return None if we can't find it.

        Args:
            name:           Key for lookup

        Returns:
            None if there is nothing defined with that key in the hierarchy, or
            an actual value if there is.
        '''
        if name in self._rep_dict:
            return self._rep_dict[name]
        return None

    def set_rep(self, name: Any, value: Any):
        '''Defines the `value` for a lookup of `name` at any time in this block and
        below.

        Args:
            name:       The lookup key
            value       The value to be cached
        '''
        if name in self._rep_dict:
            raise BlockException(f'Internal Error: Representation for {str(name)} already exists. Cannot set twice')
        self._rep_dict[name] = value

class loop(block):
    'A for loop'

    def __init__(self, loop_var_rep: crep.cpp_value, collection_rep: crep.cpp_collection):
        '''
        Create a new implicit for loop statement. A new var is created, and the scope is set to
        be the one down from here.
        '''
        block.__init__(self)
        self._collection = collection_rep
        self._loop_variable = loop_var_rep

    def emit(self, e):
        'Emit a for loop enclosed by a block of code'
        e.add_line("for (auto {0} : {1})".format(
            self._loop_variable.as_cpp(), self._collection.as_cpp()))
        block.emit(self, e)

class iftest(block):
    'An if statement'
    def __init__ (self, if_expr):
        block.__init__(self)
        self._expr = if_expr

    def emit(self, e):
        e.add_line('if ({0})'.format(self._expr.as_cpp()))
        block.emit(self, e)

class elsephrase(block):
    'An else statement. Must come after you pop and if statement off'
    def __init__(self):
        block.__init__(self)

    def emit(self, e):
        'Emit an else statement'
        e.add_line('else')
        block.emit(self, e)

class book_ttree:
    'Book a TTree for writing out. Meant to be in the Book method'

    def __init__(self, tree_name, leaves):
        self._tree_name = tree_name
        self._leaves = leaves

    def emit(self, e):
        'Emit the book statement for a tree'
        e.add_line('ANA_CHECK (book (TTree ("{0}", "My analysis ntuple")));'.format(
            self._tree_name))
        e.add_line('auto myTree = tree ("{0}");'.format(self._tree_name))
        for var_pair in self._leaves:
            e.add_line('myTree->Branch("{0}", &{1});'.format(var_pair[0], var_pair[1].as_cpp()))


class ttree_fill:
    'Fill a TTree'

    def __init__(self, tree_name):
        self._tree_name = tree_name

    def emit(self, e):
        e.add_line('tree("{0}")->Fill();'.format(self._tree_name))


class xaod_get_collection:
    def __init__(self, collection_name, var_name):
        self._collection_name = collection_name
        self._var_name = var_name

    def emit(self, e):
        e.add_line("const xAOD::JetContainer* {0} = 0;".format(self._var_name))
        e.add_line('ANA_CHECK (evtStore()->retrieve( {0}, "{1}"));'.format(
            self._var_name, self._collection_name))


class set_var:
    'Set a variable to a value'

    def __init__(self, target_var, value_var):
        r'''
        target_var, value_var: representations we will use
        '''
        self._target = target_var
        self._value = value_var

    def emit(self, e):
        e.add_line('{0} = {1};'.format(self._target.as_cpp(), self._value.as_cpp()))

class push_back:
    'push a variable onto a vector'

    def __init__(self, target_collection, value_var):
        r'''
        target_col, value_var: representations we will use
        '''
        self._target = target_collection
        self._value = value_var

    def emit(self, e):
        e.add_line('{0}.push_back({1});'.format(self._target.as_cpp(), self._value.as_cpp()))

class container_clear:
    'push a variable onto a vector'

    def __init__(self, collection):
        r'''
        target_col, value_var: representations we will use
        '''
        self._collection = collection

    def emit(self, e):
        e.add_line('{0}.clear();'.format(self._collection.as_cpp()))

class arbitrary_statement:
    'An arbitrary line of C++ code. Avoid if possible, as it makes analysis impossible'
    def __init__(self, line):
        self._line = line

    def emit(self, e):
        l = self._line
        if not l.endswith(';'):
            l += ';'
        e.add_line(l)