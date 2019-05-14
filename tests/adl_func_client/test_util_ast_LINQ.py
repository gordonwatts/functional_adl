# Code to do the testing starts here.
# Now the real test code starts.
# from clientlib.function_simplifier import simplify_chained_calls, convolute
from adl_func_client.util_ast_LINQ import replace_LINQ_operators
# from clientlib.ast_util import lambda_unwrap
# from tests.adl_func_client.test_util_ast import *
import ast
# import copy
from adl_func_client.util_ast_LINQ import parse_as_ast
from adl_func_client.util_ast import lambda_unwrap

from tests.util_debug_ast import pretty_print, normalize_ast
import ast

def get_ast(ast_in):
    'Helper func that returns an ast.'
    a_source = ast_in if isinstance(ast_in, ast.AST) else ast.parse(ast_in)
    a_source_linq = replace_LINQ_operators().visit(a_source)
    return a_source_linq    

def util_process(ast_in, ast_out):
    'Make sure ast in is the same as out after running through - this is a utility routine for the harness'

    # Make sure the arguments are ok
    a_source = ast_in if isinstance(ast_in, ast.AST) else ast.parse(ast_in)
    a_expected = ast_out if isinstance(ast_out, ast.AST) else ast.parse(ast_out)

    a_source_linq = replace_LINQ_operators().visit(a_source)
    a_expected_linq = replace_LINQ_operators().visit(a_expected)

    # a_updated = simplify_chained_calls().visit(a_source_linq)

    s_updated = ast.dump(normalize_ast().visit(a_source_linq))
    s_expected = ast.dump(normalize_ast().visit(a_expected_linq))

    assert s_updated == s_expected

def test_First_in_func():
    a = get_ast("abs(j.First())")
    ast_s = ast.dump(a)
    assert "First(source" in ast_s

def test_Select_in_func():
    a = get_ast("jets.Select(lambda x: j.pt())")
    ast_s = ast.dump(a)
    assert "Select(source" in ast_s


#########################
# Test the util_ast_LINQ functionality

def test_parse_as_ast_none():
    try:
        parse_as_ast(None)
        assert False
    except:
        pass

def test_parse_as_ast_good_text():
    r = parse_as_ast("lambda x: x+1")
    assert isinstance(r, ast.Lambda)
    s = ast.dump(r)
    assert "op=Add" in s

def test_parse_as_ast_bad_text():
    try:
        parse_as_ast("x+1")
        assert False
    except:
        pass

def test_parse_as_ast_wrapped_lambda():
    l = ast.parse("lambda x: x + 1")
    r = parse_as_ast(l)
    assert isinstance(r, ast.Lambda)

def test_parse_as_ast_lambda():
    l = lambda_unwrap(ast.parse("lambda x: x + 1"))
    r = parse_as_ast(l)
    assert isinstance(r, ast.Lambda)