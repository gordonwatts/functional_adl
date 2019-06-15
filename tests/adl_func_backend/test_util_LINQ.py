# A few tests on the LINQ ast funcitonality
from adl_func_client.event_dataset import EventDataset
from adl_func_backend.util_LINQ import find_dataset
import ast


def test_find_EventDataSet_good():
    a = EventDataset("file://junk.root") \
        .value(executor=lambda a: a)

    assert ["file:///junk.root"] == find_dataset(a).url

def test_find_EventDataSet_none():
    a = ast.parse("a+b*2")

    try:
        find_dataset(a)
        assert False
    except:
        pass

def test_find_EventDataset_Select():
    a = EventDataset("file://dude.root") \
        .Select("lambda x: x") \
        .value(executor=lambda a: a)

    assert ["file:///dude.root"] == find_dataset(a).url

def test_find_EventDataset_SelectMany():
    a = EventDataset("file://dude.root") \
        .SelectMany("lambda x: x") \
        .value(executor=lambda a: a)

    assert ["file:///dude.root"] == find_dataset(a).url

def test_find_EventDataset_Select_and_Many():
    a = EventDataset("file://dude.root") \
        .Select("lambda x: x") \
        .SelectMany("lambda x: x") \
        .value(executor=lambda a: a)

    assert ["file:///dude.root"] == find_dataset(a).url