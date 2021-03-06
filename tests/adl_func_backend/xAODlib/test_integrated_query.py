# Contains test that will run the full query.

# These are very long running do not run them normally!!
import pytest
pytestmark = pytest.mark.skipif(True, reason='Long running tests, skipped except when run by hand')

# These are *long* tests and so should not normally be run. Each test can take of order 30 seconds or so!!
from adl_func_client.event_dataset import EventDataset
from adl_func_backend.cpplib.math_utils import DeltaR
from adl_func_backend.dataset_resolvers.gridds import use_executor_dataset_resolver
import asyncio
import os

# The file we are going to go after:
f_location = 'file://G:/mc16_13TeV/AOD.16300985._000011.pool.root.1'
f_location = 'file://C:/Users/gordo/Documents/Code/IRIS-HEP/AOD.16300985._000011.pool.root.1'
f_root_remote = EventDataset('root://194.12.190.44:2300//DAOD_EXOT15.17545510._000001.pool.root.1')
f = EventDataset(f_location)
f_multiple = EventDataset([f_location, f_location])
f_ds = EventDataset(r'localds://mc16_13TeV.311309.MadGraphPythia8EvtGen_A14NNPDF31LO_HSS_LLP_mH125_mS5_ltlow.deriv.DAOD_EXOT15.e7270_e5984_s3234_r9364_r9315_p3795')

#f = EventDataset(r"file://C:/Users/gordo/Documents/mc16_13TeV/AOD.16300985._000011.pool.root.1")

def test_select_first_of_array():
    # The hard part is that First() here does not return a single item, but, rather, an array that
    # has to be aggregated over.
    training_df = f \
            .Select('lambda e: e.Jets("AntiKt4EMTopoJets").Select(lambda j: e.Tracks("InDetTrackParticles")).First().Count()') \
            .AsPandasDF('dude') \
            .value(executor=use_executor_dataset_resolver)
    assert training_df.iloc[0]['dude'] == 1897
    assert training_df.iloc[1]['dude'] == 605
    assert training_df.iloc[1999]['dude'] == 231

@pytest.yield_fixture()
def event_loop():
    'Get the loop done right on windows'
    if os.name == 'nt':
        loop = asyncio.ProactorEventLoop()
    else:
        loop = asyncio.SelectorEventLoop()
    yield loop
    loop.close()

@pytest.mark.asyncio
async def test_two_simultaneous_runs():
    # Test the future return stuff
    f_training_df_1 = f \
            .Select('lambda e: e.Jets("AntiKt4EMTopoJets").Select(lambda j: e.Tracks("InDetTrackParticles")).First().Count()') \
            .AsPandasDF('dude') \
            .future_value(executor=use_executor_dataset_resolver)
    f_training_df_2 = f \
            .Select('lambda e: e.Jets("AntiKt4EMTopoJets").Select(lambda j: e.Tracks("InDetTrackParticles")).First().Count()') \
            .AsPandasDF('dude') \
            .future_value(executor=use_executor_dataset_resolver)
    r1, r2 = await asyncio.gather(f_training_df_1, f_training_df_2)
    assert r1.iloc[0]['dude'] == 1897
    assert r2.iloc[0]['dude'] == 1897

# def test_select_first_of_array_ds():
#     # The hard part is that First() here does not return a single item, but, rather, an array that
#     # has to be aggregated over.
#     training_df = f_ds \
#             .Select('lambda e: e.Jets("AntiKt4EMTopoJets").Select(lambda j: e.Tracks("InDetTrackParticles")).First().Count()') \
#             .AsPandasDF('dude') \
#             .value(executor=use_executor_dataset_resolver)
#     assert training_df.iloc[0]['dude'] == 190

def test_flatten_array():
    # A very simple flattening of arrays
    training_df = f \
        .SelectMany('lambda e: e.Jets("AntiKt4EMTopoJets")') \
        .Select('lambda j: j.pt()/1000.0') \
        .AsPandasDF('JetPt') \
        .value(executor=use_executor_dataset_resolver)
    assert int(training_df.iloc[0]['JetPt']) == 257
    assert int(training_df.iloc[0]['JetPt']) != int(training_df.iloc[1]['JetPt'])

def test_flatten_array_remote():
    # A very simple flattening of arrays
    training_df = f_root_remote \
        .SelectMany('lambda e: e.Jets("AntiKt4EMTopoJets")') \
        .Select('lambda j: j.pt()/1000.0') \
        .AsPandasDF('JetPt') \
        .value(executor=use_executor_dataset_resolver)
    assert int(training_df.iloc[0]['JetPt']) == 64
    assert int(training_df.iloc[0]['JetPt']) != int(training_df.iloc[1]['JetPt'])

def test_First_two_outer_loops():
    # THis is a little tricky because the First there is actually running over one jet in the event. Further, the Where
    # on the number of tracks puts us another level down. So it is easy to produce code that compiles, but the First's if statement
    # is very much in the wrong place.
    training_df = f \
            .Select('lambda e: e.Jets("AntiKt4EMTopoJets").Select(lambda j: e.Tracks("InDetTrackParticles").Where(lambda t: t.pt() > 1000.0)).First().Count()') \
            .AsPandasDF('dude') \
            .value(executor=use_executor_dataset_resolver)
    assert training_df.iloc[0]['dude'] == 693

def test_first_object_in_event():
    # Make sure First puts it if statement in the right place.
    training_df = f \
        .Select('lambda e: e.Jets("AntiKt4EMTopoJets").First().pt()/1000.0') \
        .AsPandasDF('FirstJetPt') \
        .value(executor=use_executor_dataset_resolver)
    assert int(training_df.iloc[0]['FirstJetPt']) == 257

def test_first_object_in_event_with_where():
    # Make sure First puts it's if statement in the right place.
    training_df = f \
        .Select('lambda e: e.Jets("AntiKt4EMTopoJets").Select(lambda j: j.pt()/1000.0).Where(lambda jpt: jpt > 10.0).First()') \
        .AsPandasDF('FirstJetPt') \
        .value(executor=use_executor_dataset_resolver)
    assert int(training_df.iloc[0]['FirstJetPt']) == 257
    assert len(training_df) == 2000

def test_truth_particles():
    training_df = f \
        .Select("lambda e: e.TruthParticles('TruthParticles').Count()") \
        .AsPandasDF('NTruthParticles') \
        .value(executor=use_executor_dataset_resolver)
    assert training_df.iloc[0]['NTruthParticles'] == 1557

def test_truth_particles_awk():
    training_df = f \
        .Select("lambda e: e.TruthParticles('TruthParticles').Count()") \
        .AsAwkwardArray('NTruthParticles') \
        .value(executor=use_executor_dataset_resolver)
    print (training_df)
    assert len(training_df[b'NTruthParticles']) == 2000