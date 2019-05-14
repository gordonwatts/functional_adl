# A few tests on the LINQ ast funcitonality
from adl_func_client.event_dataset import EventDataset
from adl_func_backend.util_ast_LINQ import find_dataset
import ast


def test_find_EventDataSet_good():
    a = EventDataset("file://junk.root") \
        .value(executor=lambda a: a)

    assert "file://junk.root" == find_dataset(a).url

def test_find_EventDataSet_none():
    a = ast.parse("a+b*2")

    try:
        find_dataset(a)
        assert False
    except:
        pass


