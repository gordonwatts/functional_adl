# Test out the grid dataset resolver code
from adl_func_backend.dataset_resolvers.gridds import resolve_local_ds_url, GridDsException, dataset_finder
from adl_func_client.event_dataset import EventDataset
from tempfile import NamedTemporaryFile
import pytest
from unittest.mock import Mock
import tempfile

# Local files
def test_local_ds_good():
    with NamedTemporaryFile() as f:
        f.write(b'hi')
        url = f'file:///{f.name}'
        r = resolve_local_ds_url(url)
        assert r is not None
        assert len(r) == 1
        assert r[0] == url

def test_local_ds_notfound():
    url = 'file:///bogus.root'
    try:
        resolve_local_ds_url(url)
        assert False
    except FileNotFoundError:
        pass


@pytest.fixture
def already_present_ds(monkeypatch):
    push_mock = Mock()
    status_mock = Mock()
    push_mock.return_value = status_mock
    monkeypatch.setattr('requests.post', push_mock)
    status_mock.json.return_value={'status': 'local', 'filelist': [
            'file:///mc16_13TeV.311309.MadGraphPythia8EvtGen_A14NNPDF31LO_HSS_LLP_mH125_mS5_ltlow.deriv.DAOD_EXOT15.e7270_e5984_s3234_r10724_r10726_p3795/DAOD_EXOT15.17545510._000001.pool.root.1',
            'file:///mc16_13TeV.311309.MadGraphPythia8EvtGen_A14NNPDF31LO_HSS_LLP_mH125_mS5_ltlow.deriv.DAOD_EXOT15.e7270_e5984_s3234_r10724_r10726_p3795/DAOD_EXOT15.17545510._000002.pool.root.1',
            'file:///mc16_13TeV.311309.MadGraphPythia8EvtGen_A14NNPDF31LO_HSS_LLP_mH125_mS5_ltlow.deriv.DAOD_EXOT15.e7270_e5984_s3234_r10724_r10726_p3795/DAOD_EXOT15.17545510._000003.pool.root.1',
            'file:///mc16_13TeV.311309.MadGraphPythia8EvtGen_A14NNPDF31LO_HSS_LLP_mH125_mS5_ltlow.deriv.DAOD_EXOT15.e7270_e5984_s3234_r10724_r10726_p3795/DAOD_EXOT15.17545510._000004.pool.root.1',
            'file:///mc16_13TeV.311309.MadGraphPythia8EvtGen_A14NNPDF31LO_HSS_LLP_mH125_mS5_ltlow.deriv.DAOD_EXOT15.e7270_e5984_s3234_r10724_r10726_p3795/DAOD_EXOT15.17545510._000005.pool.root.1',
            'file:///mc16_13TeV.311309.MadGraphPythia8EvtGen_A14NNPDF31LO_HSS_LLP_mH125_mS5_ltlow.deriv.DAOD_EXOT15.e7270_e5984_s3234_r10724_r10726_p3795/DAOD_EXOT15.17545510._000006.pool.root.1',
            'file:///mc16_13TeV.311309.MadGraphPythia8EvtGen_A14NNPDF31LO_HSS_LLP_mH125_mS5_ltlow.deriv.DAOD_EXOT15.e7270_e5984_s3234_r10724_r10726_p3795/DAOD_EXOT15.17545510._000007.pool.root.1']}
    return push_mock

@pytest.fixture
def downloading_present_ds(monkeypatch):
    push_mock = Mock()
    status_mock = Mock()
    push_mock.return_value = status_mock
    monkeypatch.setattr('requests.post', push_mock)
    status_mock.json.return_value={'status': 'downloading', 'filelist': []}
    return push_mock

@pytest.fixture
def no_exist_present_ds(monkeypatch):
    push_mock = Mock()
    status_mock = Mock()
    push_mock.return_value = status_mock
    monkeypatch.setattr('requests.post', push_mock)
    status_mock.json.return_value={'status': 'does_not_exist', 'filelist': []}
    return push_mock

@pytest.fixture
def local_ds_file():
    with tempfile.NamedTemporaryFile() as fp:
        fp.write(b'hi')
        yield fp.name

# desktop-rucio download dataset
def test_ds_good(already_present_ds):
    url = 'localds://mc16_13TeV.311309.MadGraphPythia8EvtGen_A14NNPDF31LO_HSS_LLP_mH125_mS5_ltlow.deriv.DAOD_EXOT15.e7270_e5984_s3234_r10724_r10726_p3795'
    r = resolve_local_ds_url(url)
    already_present_ds.assert_called_once_with('http://localhost:8000/ds?ds_name=mc16_13TeV.311309.MadGraphPythia8EvtGen_A14NNPDF31LO_HSS_LLP_mH125_mS5_ltlow.deriv.DAOD_EXOT15.e7270_e5984_s3234_r10724_r10726_p3795')
    assert r is not None
    assert len(r) == 7
    for i in range(1,7):
            assert f'file:///mc16_13TeV.311309.MadGraphPythia8EvtGen_A14NNPDF31LO_HSS_LLP_mH125_mS5_ltlow.deriv.DAOD_EXOT15.e7270_e5984_s3234_r10724_r10726_p3795/DAOD_EXOT15.17545510._00000{i}.pool.root.1' in r

def test_df_good(local_ds_file):
        url = f'file:///{local_ds_file}'
        r = resolve_local_ds_url(url)
        assert r is not None
        assert len(r) == 1
        assert r[0] is url

def test_ds_downloading(downloading_present_ds):
    url = 'localds://bogus2'
    r = resolve_local_ds_url(url)
    assert r is None

def test_ds_no_exist(no_exist_present_ds):
    url = 'localds://bogus2'
    try:
        resolve_local_ds_url(url)
        assert False
    except GridDsException:
        pass

def test_event_dataset_not_ready(downloading_present_ds):
    url = 'localds://bogus2'
    eds = EventDataset(url)
    resolver = dataset_finder()
    r = resolver.visit(eds)
    assert r is eds
    assert resolver.DatasetsLocallyResolves is False
    
def test_event_dataset_ready(already_present_ds):
    url = 'localds://bogus2'
    eds = EventDataset(url)
    resolver = dataset_finder()
    r = resolver.visit(eds)
    assert r is not eds
    assert resolver.DatasetsLocallyResolves is True
    assert len(r.url) == 7

# Weird schemes
def test_weird_url_scheme():
    url = 'bogus://dataset_du_jour'
    try:
        resolve_local_ds_url(url)
        assert False
    except GridDsException:
        pass

