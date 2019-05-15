# Tests that make sure the xaod executor is working correctly
from adl_func_client.event_dataset import EventDataset
from adl_func_client.util_ast_LINQ import replace_LINQ_operators
from adl_func_backend.xAODlib.atlas_xaod_executor import atlas_xaod_executor
from adl_func_backend.util_LINQ import find_dataset
from adl_func_backend.xAODlib.util_scope import top_level_scope
from tests.adl_func_backend.xAODlib.utils_for_testing import *
from adl_func_client.event_dataset import EventDataset
import ast

class Atlas_xAOD_File_Type:
    def __init__(self):
        pass

def test_per_event_item():
    r=EventDataset("file://root.root").Select('lambda e: e.EventInfo("EventInfo").runNumber()').AsROOTTTree('root.root', 'analysis', 'RunNumber').value(executor=exe_for_test)
    vs = r.QueryVisitor._gc._class_vars
    assert 1 == len(vs)
    assert "double" == str(vs[0].cpp_type())

def test_func_sin_call():
    EventDataset("file://root.root").Select('lambda e: sin(e.EventInfo("EventInfo").runNumber())').AsROOTTTree('file.root', 'analysis', 'RunNumber').value(executor=exe_for_test)

def test_per_jet_item_as_call():
    EventDataset("file://root.root").SelectMany('lambda e: e.Jets("bogus")').Select('lambda j: j.pt()').AsROOTTTree('file.root', 'analysis', 'dude').value(executor=exe_for_test)

def test_Select_is_an_array_with_where():
    # The following statement should be a straight sequence, not an array.
    r = EventDataset("file://root.root") \
        .Select('lambda e: e.Jets("AntiKt4EMTopoJets").Select(lambda j: j.pt()/1000.0).Where(lambda jpt: jpt > 10.0)') \
        .AsPandasDF('JetPts') \
        .value(executor=exe_for_test)
    # Check to see if there mention of push_back anywhere.
    lines = get_lines_of_code(r)
    print_lines(lines)
    assert 1==["push_back" in l for l in lines].count(True)
    l_push_back = find_line_with("Fill()", lines)
    active_blocks = find_open_blocks(lines[:l_push_back])
    assert 0==["for" in a for a in active_blocks].count(True)

def test_Select_is_an_array():
    # The following statement should be a straight sequence, not an array.
    r = EventDataset("file://root.root") \
        .Select('lambda e: e.Jets("AntiKt4EMTopoJets").Select(lambda j: j.pt())') \
        .AsPandasDF('JetPts') \
        .value(executor=exe_for_test)
    # Check to see if there mention of push_back anywhere.
    lines = get_lines_of_code(r)
    print_lines(lines)
    assert 1==["push_back" in l for l in lines].count(True)
    l_push_back = find_line_with("Fill()", lines)
    active_blocks = find_open_blocks(lines[:l_push_back])
    assert 0==["for" in a for a in active_blocks].count(True)

def test_Select_is_not_an_array():
    # The following statement should be a straight sequence, not an array.
    r = EventDataset("file://root.root") \
        .SelectMany('lambda e: e.Jets("AntiKt4EMTopoJets").Select(lambda j: j.pt())') \
        .AsPandasDF('JetPts') \
        .value(executor=exe_for_test)
    # Check to see if there mention of push_back anywhere.
    lines = get_lines_of_code(r)
    print_lines(lines)
    assert 0==["push_back" in l for l in lines].count(True)
    l_push_back = find_line_with("Fill()", lines)
    active_blocks = find_open_blocks(lines[:l_push_back])
    assert 1==["for" in a for a in active_blocks].count(True)

def test_Select_Multiple_arrays():
    # The following statement should be a straight sequence, not an array.
    r = EventDataset("file://root.root") \
        .Select('lambda e: (e.Jets("AntiKt4EMTopoJets").Select(lambda j: j.pt()/1000.0),e.Jets("AntiKt4EMTopoJets").Select(lambda j: j.eta()))') \
        .AsPandasDF(('JetPts','JetEta')) \
        .value(executor=exe_for_test)
    # Check to see if there mention of push_back anywhere.
    lines = get_lines_of_code(r)
    print_lines(lines)
    assert 2==["push_back" in l for l in lines].count(True)
    l_push_back = find_line_with("Fill()", lines)
    active_blocks = find_open_blocks(lines[:l_push_back])
    assert 0==["for" in a for a in active_blocks].count(True)

def test_Select_Multiple_arrays_2_step():
    # The following statement should be a straight sequence, not an array.
    r = EventDataset("file://root.root") \
        .Select('lambda e: e.Jets("AntiKt4EMTopoJets")') \
        .Select('lambda jets: (jets.Select(lambda j: j.pt()/1000.0),jets.Select(lambda j: j.eta()))') \
        .AsPandasDF(('JetPts','JetEta')) \
        .value(executor=exe_for_test)
    # Check to see if there mention of push_back anywhere.
    lines = get_lines_of_code(r)
    print_lines(lines)
    l_push_back = find_line_numbers_with("push_back", lines)
    assert all([len([l for l in find_open_blocks(lines[:pb]) if "for" in l])==1 for pb in l_push_back])
    assert 2==["push_back" in l for l in lines].count(True)
    l_push_back = find_line_with("Fill()", lines)
    active_blocks = find_open_blocks(lines[:l_push_back])
    assert 0==["for" in a for a in active_blocks].count(True)

def test_Select_of_2D_array_fails():
    # The following statement should be a straight sequence, not an array.
    try:
        EventDataset("file://root.root") \
            .Select('lambda e: e.Jets("AntiKt4EMTopoJets").Select(lambda j: (j.pt()/1000.0, j.eta()))') \
            .AsPandasDF(['JetInfo']) \
            .value(executor=exe_for_test)
    except BaseException as e:
        assert "Nested data structures" in str(e)

def test_SelectMany_of_tuple_is_not_array():
    # The following statement should be a straight sequence, not an array.
    r = EventDataset("file://root.root") \
            .SelectMany('lambda e: e.Jets("AntiKt4EMTopoJets").Select(lambda j: (j.pt()/1000.0, j.eta()))') \
            .AsPandasDF(['JetPts', 'JetEta']) \
            .value(executor=exe_for_test)
    lines = get_lines_of_code(r)
    print_lines(lines)
    assert 0==["push_back" in l for l in lines].count(True)
    l_push_back = find_line_with("Fill()", lines)
    active_blocks = find_open_blocks(lines[:l_push_back])
    assert 1==["for" in a for a in active_blocks].count(True)

def test_generate_binary_operators():
    # Make sure the binary operators work correctly - that they don't cause a crash in generation.
    ops = ['+','-','*','/']
    for o in ops:
        EventDataset("file://root.root") \
            .SelectMany('lambda e: e.Jets("AntiKt4EMTopoJets").Select(lambda j: j.pt(){0}1)'.format(o)) \
            .AsPandasDF(['JetInfo']) \
            .value(executor=exe_for_test)
