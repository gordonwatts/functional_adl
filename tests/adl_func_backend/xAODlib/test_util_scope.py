# Test the scope utilities


from adl_func_backend.xAODlib.generated_code import generated_code
import adl_func_backend.xAODlib.statement as statement
import adl_func_backend.cpplib.cpp_types as ctyp
import adl_func_backend.cpplib.cpp_representation as crep
from adl_func_backend.xAODlib.util_scope import deepest_scope, gc_scope_top_level

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

def test_everything_starts_with_top_level_scope():
    top = gc_scope_top_level()
    g = generated_code()
    s1 = statement.iftest("true")
    g.add_statement(s1)
    scope_1 = g.current_scope()

    assert scope_1.starts_with(top)

def test_nothing_else_starts_with_top_level_scope():
    top = gc_scope_top_level()
    g = generated_code()
    s1 = statement.iftest("true")
    g.add_statement(s1)
    scope_1 = g.current_scope()

    assert not top.starts_with(scope_1)

def test_top_level_starts_with_top_level():
    top1 = gc_scope_top_level()
    top2 = gc_scope_top_level()

    assert top1.starts_with(top2)