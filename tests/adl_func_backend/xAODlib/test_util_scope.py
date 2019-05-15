# Test the scope utilities

# Following two lines necessary b.c. I can't figure out how to get pytest to pick up the python path correctly
# despite reading a bunch of docs.
import sys
sys.path.append('.')

from adl_func_backend.xAODlib.generated_code import generated_code
import adl_func_backend.xAODlib.statement as statement
import adl_func_backend.cpplib.cpp_types as ctyp
import adl_func_backend.cpplib.cpp_representation as crep
from adl_func_backend.xAODlib.util_scope import deepest_scope

def test_deepest_scope_one_greater():
    g = generated_code()
    s1 = statement.iftest("true")
    s2 = statement.iftest("true")
    g.add_statement(s1)
    scope_1 = g.current_scope()
    g.add_statement(s2)
    scope_2 = g.current_scope()

    v1 = crep.cpp_value("v1", scope_1, ctyp.terminal('int'))
    v2 = crep.cpp_value("v2", scope_2, ctyp.terminal('int'))

    assert v2 == deepest_scope(v1, v2)
    assert v2 == deepest_scope(v2, v1)

def test_deepest_scope_equal():
    g = generated_code()
    s1 = statement.iftest("true")
    s2 = statement.set_var("v1", "true")
    g.add_statement(s1)
    scope_1 = g.current_scope()

    v1 = crep.cpp_value("v1", scope_1, ctyp.terminal('int'))
    v2 = crep.cpp_value("v2", scope_1, ctyp.terminal('int'))

    assert v1 == deepest_scope(v1, v2)
    assert v2 == deepest_scope(v2, v1)
