# Test the object stream
from adl_func_client import ObjectStream
from adl_func_client.event_dataset import EventDataset
import ast

def dummy_executor(a: ast.AST) -> ast.AST:
    'Called by the executor to run an AST'
    return a

def test_simple_query():
    r = EventDataset("file://junk.root") \
        .SelectMany("lambda e: e.jets()") \
        .Select("lambda j: j.pT()") \
        .AsROOTTTree("junk.root", "analysis", "jetPT") \
        .value(dummy_executor)
    assert isinstance(r, ast.AST)

def test_nested_query_rendered_correctly():
    r = EventDataset("file://junk.root") \
        .Where("lambda e: e.jets.Select(lambda j: j.pT()).Where(lambda j: j > 10).Count() > 0") \
        .SelectMany("lambda e: e.jets()") \
        .AsROOTTTree("junk.root", "analysis", "jetPT") \
        .value(dummy_executor)
    assert isinstance(r, ast.AST)
    assert "Select(source" in ast.dump(r)
