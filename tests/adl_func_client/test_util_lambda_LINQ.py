# Test the finding and location of LINQ operators
# Following two lines necessary b.c. I can't figure out how to get pytest to pick up the python path correctly
# despite reading a bunch of docs.
import sys
sys.path.append('.')

# Code to do the testing starts here.
# Now the real test code starts.
from clientlib.function_simplifier import simplify_chained_calls, convolute
from clientlib.find_LINQ_operators import replace_LINQ_operators
from clientlib.ast_util import lambda_unwrap
from tests.clientlib.util_test_ast import *
import ast
import copy

def get_ast(ast_in):
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

    a_updated = simplify_chained_calls().visit(a_source_linq)

    s_updated = ast.dump(normalize_ast().visit(a_updated))
    s_expected = ast.dump(normalize_ast().visit(a_expected_linq))

    assert s_updated == s_expected

# Now the real test code starts.
def test_First_after_select():
    util_process("event.Select(lambda x: x.jets).Select(lambda y: y.First())", "event.Select(lambda x: x.jets.First())")

def test_First_after_sequence():
    util_process("event.Select(lambda x: (x.jets, x.tracks)).Select(lambda y: y[0].First())", "event.Select(lambda x: x.jets.First())")

def test_First_in_func():
    a = get_ast("abs(j.First())")
    ast_s = ast.dump(a)
    assert "First(source" in ast_s