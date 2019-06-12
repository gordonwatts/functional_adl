# Test out the executors code.
from adl_func_client import ObjectStream
from adl_func_client.event_dataset import EventDataset
from adl_func_client.executors import use_executor_to_ast
import ast
import pickle

def dummy_executor(a: ast.AST) -> ast.AST:
    'Called by the executor to run an AST'
    return a

def execute_query(exer):
    'Build a query and run the supplied executor'
    return EventDataset("file://junk.root") \
        .Where("lambda e: e.jets.Select(lambda j: j.pT()).Where(lambda j: j > 10).Count() > 0") \
        .SelectMany("lambda e: e.jets()") \
        .AsROOTTTree("junk.root", "analysis", "jetPT") \
        .value(exer)


def test_pickle_comes_back():
    # Get back the actual AST
    a1 = execute_query(dummy_executor)

    # Next, get back the pickle dude.
    p = execute_query(use_executor_to_ast)
    a2 = pickle.loads(p)

    assert ast.dump(a2) == ast.dump(a1)
    