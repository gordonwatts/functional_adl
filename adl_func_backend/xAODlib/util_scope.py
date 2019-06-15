# Scope related utilities
# see https://stackoverflow.com/questions/33533148/how-do-i-specify-that-the-return-type-of-a-method-is-the-same-as-the-class-itsel
# for info on this next line. Already looking forward to python 4...
import copy
from typing import Union

def top_level_scope():
    '''
    Returns a top level scope. Basically, the class level.
    '''
    return gc_scope_top_level()

class gc_scope:
    'Internal class to track the scope of a statement.'
    def __init__(self, scope_stack):
        self._scope_stack = copy.copy(scope_stack)

    def __getitem__(self, key: int):
        '''
        Return a new scope, some number "up" from where we are now. This uses standard
        array slicing in python. If you do 0 you'll get back the top level. If you do -1
        you will get back everything but the last thing. -2 last two thigns, etc.
        '''
        if type(key) is not int:
            raise BaseException("Key must be an integer")

        if len(self._scope_stack[:key]) == 0:
            raise BaseException("Winding up at the top level scope is not yet supported")

        return gc_scope(self._scope_stack[:key])

    def frame_statements(self, key):
        'Return the nth frame block. -1 means the last one, 0 means the deepest (top) one.'
        return self._scope_stack[key]

    def declare_variable(self, var) -> None:
        'Declare a class at the scope level'
        self._scope_stack[-1].declare_variable(var)

    def starts_with(self, c):
        '''
        Return true if the scope c matches the first part of our scope. False otherwise.
        '''
        if c.is_top_level() and self.is_top_level():
            return True
        if c.is_top_level():
            return True
        if self.is_top_level():
            return False
            
        if len(c._scope_stack) > len(self._scope_stack):
            return False
        
        return all([a is b for a,b in zip(self._scope_stack, c._scope_stack[:len(self._scope_stack)])])

    def is_top_level(self):
        return False

class gc_scope_top_level:
    def is_top_level(self):
        return True
    def __getitem__(self, key: int) -> gc_scope:
        raise BaseException("This should never be called. Internal error")
    
    def starts_with(self, c):
        'Starts with can only be true for top level if the other guy is top level'
        return type(c) is gc_scope_top_level

def deepest_scope(v1, v2):
    '''
    Returns the variable that is at the deepest scope. If they are equal in scope, then return v1.
    '''
    s1 = v1.scope()
    s2 = v2.scope()
    if not s2.starts_with(s1):
        return v1
    if s1.starts_with(s2):
        return v1
    return v2
