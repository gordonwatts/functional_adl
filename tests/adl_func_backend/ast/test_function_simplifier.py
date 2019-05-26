# Some tests to look at function simplifier
# Now the real test code starts.
#from adl_func_backend.util_ast_LINQ import simplify_chained_calls
from adl_func_client.util_ast_LINQ import replace_LINQ_operators
from adl_func_backend.ast.function_simplifier import simplify_chained_calls
from tests.util_debug_ast import normalize_ast
import ast

def util_process(ast_in, ast_out):
    'Make sure ast in is the same as out after running through - this is a utility routine for the harness'

    # Make sure the arguments are ok
    a_source = ast_in if isinstance(ast_in, ast.AST) else ast.parse(ast_in)
    a_expected = ast_out if isinstance(ast_out, ast.AST) else ast.parse(ast_out)

    a_source_linq = replace_LINQ_operators().visit(a_source)
    a_expected_linq = replace_LINQ_operators().visit(a_expected)

    a_updated_raw = simplify_chained_calls().visit(a_source_linq)

    s_updated = ast.dump(normalize_ast().visit(a_updated_raw))
    s_expected = ast.dump(normalize_ast().visit(a_expected_linq))

    print(s_updated)
    print(s_expected)
    assert s_updated == s_expected
    return a_updated_raw

################
# Test convolutions
def test_function_replacement():
    util_process('(lambda x: x+1)(z)', 'z+1')

def test_function_convolution_2deep():
    util_process('(lambda x: x+1)((lambda y: y)(z))', 'z+1')

def test_function_convolution_3deep():
    util_process('(lambda x: x+1)((lambda y: y)((lambda z: z)(a)))', 'a+1')

################
# Testing out Select from the start
#
def test_select_simple():
    # Select statement shouldn't be altered on its own.
    util_process("jets.Select(lambda j: j*2)", "jets.Select(lambda j: j*2)")

def test_select_select_convolution():
    util_process('jets.Select(lambda j: j).Select(lambda j2: j2*2)', 'jets.Select(lambda j2: j2*2)')

def test_select_identity():
    util_process('jets.Select(lambda j: j)', 'jets')

def test_where_simple():
    util_process('jets.Where(lambda j: j.pt>10)', 'jets.Where(lambda j: j.pt>10)')

################
# Test out Where
def test_where_always_true():
    util_process('jets.Where(lambda j: True)', 'jets')

def test_where_where():
    util_process('jets.Where(lambda j: j.pt>10).Where(lambda j1: j1.eta < 4.0)', 'jets.Where(lambda j: (j.pt>10) and (j.eta < 4.0))')

def test_where_select():
    util_process('jets.Select(lambda j: j.pt).Where(lambda p: p > 40)', 'jets.Where(lambda j: j.pt > 40).Select(lambda k: k.pt)')

def test_where_first():
    util_process('events.Select(lambda e: e.jets.First()).Select(lambda j: j.pt()).Where(lambda jp: jp>40.0)', \
        'events.Where(lambda e: e.jets.First().pt() > 40.0).Select(lambda e1: e1.jets.First().pt())')

################
# Testing out SelectMany
def test_selectmany_simple():
    # SelectMany statement shouldn't be altered on its own.
    util_process("jets.SelectMany(lambda j: j.tracks)", "jets.SelectMany(lambda j: j.tracks)")

def test_selectmany_where():
    a = util_process("jets.SelectMany(lambda j: j.tracks).Select(lambda z: z.pt()).Where(lambda k: k>40)", "jets.SelectMany(lambda e: e.tracks.Where(lambda t: t.pt()>40).Select(lambda k: k.pt()))")
    print(ast.dump(a))
    # Make sure the z.pT() was a deep copy, not a shallow one.
    zpt_first = a.body[0].value.selection.body.source.filter.body.left
    zpt_second = a.body[0].value.selection.body.selection.body
    assert zpt_first is not zpt_second
    assert zpt_first.func is not zpt_second.func

def test_selectmany_where():
    a = util_process("jets.SelectMany(lambda j: j.tracks).Select(lambda z: z.pt()).Where(lambda k: k>40)", "jets.SelectMany(lambda e: e.tracks.Where(lambda t: t.pt()>40).Select(lambda k: k.pt()))")
    print(ast.dump(a))
    # Make sure the z.pT() was a deep copy, not a shallow one.
    zpt_first = a.body[0].value.selection.body.source.filter.body.left
    zpt_second = a.body[0].value.selection.body.selection.body
    assert zpt_first is not zpt_second
    assert zpt_first.func is not zpt_second.func

###############
# Testing first

################
# Tuple tests
def test_tuple_select():
    # (t1, t2)[0] should be t1.
    util_process('(t1,t2)[0]', 't1')

def test_tuple_in_lambda():
    util_process('(lambda t: t[0])((j1, j2))', 'j1')
def test_tuple_in_lambda_2deep():
    util_process('(lambda t: t[0])((lambda s: s[1])((j0, (j1, j2))))', 'j1')

def test_tuple_around_first():
    util_process('events.Select(lambda e: e.jets.Select(lambda j: (j, e)).First()[0])', 'events.Select(lambda e: e.jets.First())')