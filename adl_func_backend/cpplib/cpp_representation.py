# The representation, in C++ code, of all the data being passed around the system by the C++
# code. Mostly, these are used as "representations" of a particular AST note. Here is an outline
# of how this works:
#
# Things are broken down, generally, into values and sequences.
#
# A value is something like j->pt(), or perhaps even just j. It has a specific value, and it
# also has a particular place where it is valid - the so-called scope. The scope tells you exactly
# where in the code you are allowed to refer to that value. The value is valid at that scope or
# anything deeper.
#
# A collection is a special type of value. The thing about collection is that you can turn it into
# a sequence. This happens implicitly with code that looks like "e.Jets.Select(xxx)" - between the Jets
# and the Select, the collection that is e.Jets gets turned into a sequence.
#
# A tuple is just a special case of a value, and it contains a series of either values or sequences or collections, etc.
#
# Finally, a sequence is something we are iterating over. Select, SelectMany, and Where all return sequences.
# A sequence has the loop iterator - the thing that we are looping over. This iterator is just a value, and has
# all the properties of a value. A sequence also has a "value" associated with it. This value is at first just
# the iterator. But you can have something like a select statement that will do Select(j->pT()). In that case
# the sequence value transforms from j to j->pT(). THe iterator value remains the same at that point.
#
# It is instructive to talk about how various LINQ predicates transform the above things.
#
# seq.Select(f(x)):
#  - if seq is a collection -> sequence with a new iterator value and the sequence value being f(iterator value)
#  - seq can't be a plain value
#  - if seq is a sequence -> new sequence with same iterator value and sequence value being f(old sequence value).
#    Note it is possible for the sequence value to be another sequence!
#
# seq.SelectMany(f(x)):
#  - if seq is a collection -> sequence with a new iterator value and sequence value being f(iterator value).
#    Then go onto next step that applies.
#  - seq can't be a plane value
#
#  next look a the sequence value:
#  - collection -> start a new sequence with the iterator and sequence value being the iterator
#  - value -> not allowedNone, 
#  - sequence -> keep the sequence
#
# seq.First()
#  - seq is a collection -> start a new sequence with the iterator and sequence being the iterator
#  - seq is a value -> not allowed
# then
#  - seq is a sequence -> return the sequence value
#
# Others follow a similar line of reasoning.
#
# TODO: Rename the classes in here to be proper Python names
#
from __future__ import annotations
from adl_func_backend.cpplib.cpp_vars import unique_name
from adl_func_backend.xAODlib.util_scope import gc_scope, gc_scope_top_level
import ast
import copy
from typing import Union

def dereference_var(v):
    '''
    If this is a pointer, return the object with the proper type (and a * to dereference it). Otherwise
    just return the object itself.
    '''
    if not isinstance(v, cpp_value):
        raise BaseException("Internal Error: Makes no sense to dereference anything but a C++ value")

    if not v.cpp_type().is_pointer():
        return v

    # We will go under the covers and "fix" this.
    new_v = copy.copy(v)
    new_v._expression = "*" + new_v._expression
    new_v._cpp_type = new_v._cpp_type.dereference()
    return new_v
class dummy_ast(ast.AST):
    'A dummy ast'
    def __init__(self, rep = None):
        self.rep = rep
        self._fields=tuple()

class cpp_rep_base:
    r'''
    Represents a term or collection in C++ code. Base class for all values, collections, sequences.

    This is an abstract class for the most part. Do not override things that aren't needed - that way the system will
    know when the user tries to do something that they shouldn't have.

    We know only about our type
    '''
    def __init__(self):
        pass

    def as_ast(self):
        'Create an AST rep of this guy'
        return dummy_ast(self)
        
        
class cpp_value(cpp_rep_base):
    r'''
    Represents a value. This has a particular value in C++ code that is valid at some C++ scope, or deeper.
    '''
    def __init__(self, cpp_expression: str, scope: Union[gc_scope, gc_scope_top_level], cpp_type):
        r'''
        Initialize a C++ value

        cpp_expression:         The C++ name that can be emitted to code
        scope:                  The scope at which this value is valid 
        cpp_type:               Type that we can deal with
        '''
        cpp_rep_base.__init__(self)
        self._scope = scope
        self._expression = cpp_expression
        self._cpp_type = cpp_type

    def is_pointer(self):
        'Return true if this type is a pointer'
        if self._cpp_type is None:
            raise BaseException(f"Attempt to get the type of a typeless C++ expression '{self._expression}''.")
        return self._cpp_type.is_pointer()

    def as_cpp(self):
        return self._expression

    def reset_scope(self, scope: gc_scope):
        'If scope has not been set, then we can set it'
        if self._scope is None:
            self._scope = scope
        else:
            raise BaseException("Internal Error: You can't reset the scope to something new")

    def scope(self) -> Union[gc_scope, gc_scope_top_level]:
        'Return the scope at which this variable becomes valid.'
        if self._scope is not None:
            return self._scope
        else:
            raise BaseException("Internal Error: Asking for the undefined scope of a value.")

    def cpp_type(self):
        return self._cpp_type

    def copy_with_new_scope(self, scope):
        'Make a new version, with just the scope changed'
        new_v = copy.copy(self)
        new_v._scope = scope
        return new_v
        
class cpp_variable(cpp_value):
    r'''
    A value that can be declared. Refers to a variable.
    '''
    def __init__(self, cpp_expression: str, scope: Union[gc_scope, gc_scope_top_level], cpp_type, initial_value: cpp_value=None):
        cpp_value.__init__(self, cpp_expression, scope, cpp_type)
        self._initial_value = initial_value

    def initial_value(self):
        return self._initial_value

class cpp_collection(cpp_value):
    r'''
    Represents a special kind of value - a collection (vector<float>).
    '''
    def __init__(self, cpp_expression: str, scope: gc_scope, collection_type):
        r'''
        Initialize a C++ value that can be turned into a sequence if requested.

        cpp_expression:         The expression in C++ to refer to this collection.
        scope:                  The scope at which this collection is valid.
        collection_type:        The type of the collection (see cpp_types). It should be a collection
        '''
        cpp_value.__init__(self, cpp_expression, scope, collection_type)

    def get_element_type(self):
        'Return the type of the element of the sequence'
        return self.cpp_type().element_type()

class cpp_tuple(cpp_rep_base):
    r'''
    Represents a special kind of value - a tuple, which is just a container of other values. This
    isn't a regular cpp_value in the sense it can't be directly put into C++ code. It must be
    specially handled by the interpreter.
    '''
    def __init__(self, list_of_values: tuple, scope: Union[gc_scope, gc_scope_top_level]):
        '''
        A Tuple holds a list of different types

        list_of_values:         Iterator that will give us all the cpp_xxx.
        scope:                  Scope where this is valid
        cpp_type:               An instance of cpp_types.tuple to specify the type. 
        '''
        cpp_rep_base.__init__(self)
        self._values = list_of_values
        self._scope = scope

    def values(self):
        return self._values

    def scope(self):
        return self._scope

class cpp_sequence(cpp_rep_base):
    '''
    Represents a sequence of data. The `sequence_value` points to value of the item in the stream, and
    `iterator_value` points to the iterator itself we are looping over (appears in the for statement).

    A sequence is a stream of values of a particular type. You can think of it like a generator expression,
    or like a vector of some type.
    '''
    def __init__ (self, sequence_value: Union[cpp_value, cpp_sequence], iterator_value: cpp_value):
        '''
        Create a sequence

        sequence_value:         The value of the sequence - of the data items that are in sequence
        iterator_value:         The iterator that is incremented to get the next value in the sequence.
        '''
        cpp_rep_base.__init__(self)
        self._sequence = sequence_value
        self._iterator = iterator_value

    def sequence_value(self):
        return self._sequence

    def iterator_value(self):
        return self._iterator

    def cpp_type(self):
        raise BaseException("Do not know how to get the type of a sequence!")

    def as_cpp(self):
        raise BaseException("Do not know how to get the cpp rep of a sequence!")