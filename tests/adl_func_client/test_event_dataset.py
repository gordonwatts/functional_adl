# Test that the event dataset works correctly.

from adl_func_client.functional_events.event_dataset import EventDataset

def test_good_file_url():
    _ = EventDataset('file://test.root')

def test_good_grid_url():
    _ = EventDataset('gridds://mc16_13TeV.311309.MadGraphPythia8EvtGen_A14NNPDF31LO_HSS_LLP_mH125_mS5_ltlow.deriv.DAOD_EXOT15.e7270_e5984_s3234_r10201_r10210_p3795')

def test_good_local_grid_ds_url():
    _ = EventDataset('localds://mc16_13TeV.311309.MadGraphPythia8EvtGen_A14NNPDF31LO_HSS_LLP_mH125_mS5_ltlow.deriv.DAOD_EXOT15.e7270_e5984_s3234_r10201_r10210_p3795')

def test_good_url_with_options():
    'Note - these options are not necessarily valid!'
    _ = EventDataset('localds://mc16_13TeV.311309.MadGraphPythia8EvtGen_A14NNPDF31LO_HSS_LLP_mH125_mS5_ltlow.deriv.DAOD_EXOT15.e7270_e5984_s3234_r10201_r10210_p3795&nfiles=1')

def test_bad_url():
    try:
        _ = EventDataset('holyforkingshirtballs.root')
    except:
        return
    assert False

def test_empty_url():
    try:
        _ = EventDataset('')
    except:
        return
    assert False