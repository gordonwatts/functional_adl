# Test out various things connected to the Aggregate call.
# That code is more complex than I'd like it!
from tests.adl_func_backend.xAODlib.utils_for_testing import *
from adl_func_client.event_dataset import EventDataset

def test_Aggregate_not_initial_const_SUM():
    r = EventDataset("file://root.root") \
        .Select("lambda e: e.Jets('AntiKt4EMTopoJets').Select(lambda j: j.pt()/1000).Sum()") \
        .AsROOTTTree('dude.root', 'analysis', 'jetPT') \
        .value(executor=exe_for_test)
    lines = get_lines_of_code(r)
    print_lines(lines)
    l_sets = find_line_numbers_with("/1000", lines)
    assert 2 == len(l_sets)

def test_count_after_single_sequence():
    r = EventDataset("file://root.root") \
        .Select('lambda e: e.Jets("AllMyJets").Select(lambda j: j.pt()).Count()') \
        .AsROOTTTree('dude.root', 'analysis', 'JetPt') \
        .value(executor=exe_for_test)
    lines = get_lines_of_code(r)
    print_lines(lines)
    # Make sure there is just one for loop in here.
    assert 1 == ["for" in l for l in lines].count(True)
    # Make sure the +1 happens after the for, and before another } bracket.
    num_for = find_line_with("for", lines)
    num_inc = find_line_with("+1", lines[num_for:])
    num_close = find_next_closing_bracket(lines[num_for:])
    assert num_close > num_inc

def test_count_after_single_sequence_with_filter():
    r = EventDataset("file://root.root") \
        .Select('lambda e: e.Jets("AllMyJets").Select(lambda j: j.pt()).Where(lambda jpt: jpt>10.0).Count()') \
        .AsROOTTTree('dude.root', 'analysis', 'JetPt') \
        .value(executor=exe_for_test)
    lines = get_lines_of_code(r)
    print_lines(lines)
    # Make sure there is just one for loop in here.
    assert 1 == ["for" in l for l in lines].count(True)
    # Make sure the +1 happens after the for, and before another } bracket.
    num_for = find_line_with("if", lines)
    num_inc = find_line_with("+1", lines[num_for:])
    num_close = find_next_closing_bracket(lines[num_for:])
    assert num_close > num_inc

def test_count_after_double_sequence():
    r = EventDataset("file://root.root") \
        .Select('lambda e: e.Jets("AllMyJets").SelectMany(lambda j: e.Tracks("InnerTracks")).Count()') \
        .AsROOTTTree('dude.root', 'analysis', 'JetPt') \
        .value(executor=exe_for_test)
    lines = get_lines_of_code(r)
    print_lines(lines)
    # Make sure there is just one for loop in here.
    assert 2 == ["for" in l for l in lines].count(True)
    # Make sure the +1 happens after the for, and before another } bracket.
    num_for = find_line_with("for", lines)
    num_inc = find_line_with("+1", lines[num_for:])
    num_close = find_next_closing_bracket(lines[num_for:])
    assert num_close > num_inc

def test_count_after_single_sequence_of_sequence():
    r = EventDataset("file://root.root") \
        .Select('lambda e: e.Jets("AllMyJets").Select(lambda j: e.Tracks("InnerTracks")).Count()') \
        .AsROOTTTree('dude.root', 'analysis', 'JetPt') \
        .value(executor=exe_for_test)
    lines = get_lines_of_code(r)
    print_lines(lines)
    # Make sure there is just one for loop in here.
    assert 1 == ["for" in l for l in lines].count(True)
    # Make sure the +1 happens after the for, and before another } bracket.
    num_for = find_line_with("for", lines)
    num_inc = find_line_with("+1", lines[num_for:])
    num_close = find_next_closing_bracket(lines[num_for:])
    assert num_close > num_inc

def test_count_after_double_sequence_with_filter():
    r = EventDataset("file://root.root") \
        .Select('lambda e: e.Jets("AllMyJets").SelectMany(lambda j: e.Tracks("InnerTracks").Where(lambda t: t.pt()>10.0)).Count()') \
        .AsROOTTTree('dude.root', 'analysis', 'JetPt') \
        .value(executor=exe_for_test)
    lines = get_lines_of_code(r)
    print_lines(lines)
    # Make sure there is just one for loop in here.
    assert 2 == ["for" in l for l in lines].count(True)
    # Make sure the +1 happens after the for, and before another } bracket.
    num_for = find_line_with("if", lines)
    num_inc = find_line_with("+1", lines[num_for:])
    num_close = find_next_closing_bracket(lines[num_for:])
    assert num_close > num_inc

def test_count_after_single_sequence_of_sequence_unwound():
    r = EventDataset("file://root.root") \
        .Select('lambda e: e.Jets("AllMyJets").Select(lambda j: e.Tracks("InnerTracks")).SelectMany(lambda ts: ts).Count()') \
        .AsROOTTTree('dude.root', 'analysis', 'JetPt') \
        .value(executor=exe_for_test)
    lines = get_lines_of_code(r)
    print_lines(lines)
    # Make sure there is just one for loop in here.
    assert 2 == ["for" in l for l in lines].count(True)
    # Make sure the +1 happens after the for, and before another } bracket.
    num_for = find_line_with("for", lines)
    num_inc = find_line_with("+1", lines[num_for:])
    num_close = find_next_closing_bracket(lines[num_for:])
    assert num_close > num_inc

def test_count_after_single_sequence_of_sequence_with_useless_where():
    r = EventDataset("file://root.root") \
        .Select('lambda e: e.Jets("AllMyJets").Select(lambda j: e.Tracks("InnerTracks").Where(lambda pt: pt > 10.0)).Count()') \
        .AsROOTTTree('dude.root', 'analysis', 'JetPt') \
        .value(executor=exe_for_test)
    lines = get_lines_of_code(r)
    print_lines(lines)
    # Make sure there is just one for loop in here.
    l_increment = find_line_with('+1', lines)
    block_headers = find_open_blocks(lines[:l_increment])
    assert 1 == ["for" in l for l in block_headers].count(True)
    # Make sure the +1 happens after the for, and before another } bracket.
    num_for = find_line_with("for", lines)
    num_inc = find_line_with("+1", lines[num_for:])
    num_close = find_next_closing_bracket(lines[num_for:])
    assert num_close > num_inc

def test_first_can_be_iterable_after_where():
    # This was found while trying to generate a tuple for some training, below, simplified.
    # The problem was that First() always returned something you weren't allowed to iterate over. Which is not what we want here.
    r = EventDataset("file://root.root") \
        .Select('lambda e: e.Jets("AllMyJets").Select(lambda j: e.Tracks("InnerTracks").Where(lambda t: t.pt() > 1000.0)).First().Count()') \
        .AsROOTTTree('dude.root', 'analysis', 'JetPt') \
        .value(executor=exe_for_test)

def test_first_can_be_iterable():
    # Make sure a First() here gets called back correctly and generated.
    r = EventDataset("file://root.root") \
        .Select('lambda e: e.Jets("AllMyJets").Select(lambda j: e.Tracks("InnerTracks")).First().Count()') \
        .AsROOTTTree('dude.root', 'analysis', 'JetPt') \
        .value(executor=exe_for_test)

def test_Aggregate_per_jet():
    r = EventDataset("file://root.root") \
        .Select("lambda e: e.Jets('AntiKt4EMTopoJets').Select(lambda j: j.pt()).Count()") \
        .AsROOTTTree('dude.root', 'analysis', 'JetPt') \
        .value(executor=exe_for_test)

def test_generate_Max():
    r = EventDataset("file://root.root") \
        .Select("lambda e: e.Jets('AntiKt4EMTopoJets').Select(lambda j: j.pt()).Max()") \
        .AsROOTTTree('dude.root', 'analysis', 'JetPt') \
        .value(executor=exe_for_test)
    lines = get_lines_of_code(r)
    print_lines(lines)


def test_First_selects_collection_count():
    # Make sure that we have the "First" predicate after if Where's if statement.
    r = EventDataset("file://root.root") \
        .Select('lambda e: e.Jets("AntiKt4EMTopoJets").Select(lambda j: e.Tracks("InDetTrackParticles")).First().Count()') \
        .AsPandasDF('TrackCount') \
        .value(executor=exe_for_test)
    lines = get_lines_of_code(r)
    print_lines(lines)
    l = find_line_numbers_with("for", lines)
    assert 2==len(l)

def test_sequence_with_where_first():
    r = EventDataset("file://root.root") \
        .Select('lambda e: e.Jets("AntiKt4EMTopoJets").Select(lambda j: e.Tracks("InDetTrackParticles").Where(lambda t: t.pt() > 1000.0)).First().Count()') \
        .AsPandasDF('dude') \
        .value(executor=exe_for_test)
    lines = get_lines_of_code(r)
    print_lines(lines)
    l_first = find_line_numbers_with("if (is_first", lines)
    assert 1 == len(l_first)
    active_blocks = find_open_blocks(lines[:l_first[0]])
    assert 1==["for" in a for a in active_blocks].count(True)
    l_agg = find_line_with("+1", lines)
    active_blocks = find_open_blocks(lines[:l_agg])
    assert 1==[">1000" in a for a in active_blocks].count(True)
