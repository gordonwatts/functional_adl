# Test out the grid dataset resolver code
from adl_func_backend.dataset_resolvers.gridds import resolve_local_ds_url, GridDsException
from tempfile import NamedTemporaryFile
from urllib.parse import urlparse
import os
import pytest
import unittest.mock as mock
from unittest.mock import Mock

# Local files
def test_local_ds_good():
    with NamedTemporaryFile() as f:
        f.write(b'hi')
        url = f'file://{f.name}'
        r = resolve_local_ds_url(url)
        assert r is not None
        assert len(r) == 1
        assert r[0] == url

def test_local_ds_notfound():
    url = 'file://bogus.root'
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
        status_mock.json.return_value={'status': 'local', 'filelist': ['mc16_13TeV.311309.MadGraphPythia8EvtGen_A14NNPDF31LO_HSS_LLP_mH125_mS5_ltlow.deriv.DAOD_EXOT15.e7270_e5984_s3234_r10724_r10726_p3795/DAOD_EXOT15.17545510._000001.pool.root.1', 'mc16_13TeV.311309.MadGraphPythia8EvtGen_A14NNPDF31LO_HSS_LLP_mH125_mS5_ltlow.deriv.DAOD_EXOT15.e7270_e5984_s3234_r10724_r10726_p3795/DAOD_EXOT15.17545510._000002.pool.root.1', 'mc16_13TeV.311309.MadGraphPythia8EvtGen_A14NNPDF31LO_HSS_LLP_mH125_mS5_ltlow.deriv.DAOD_EXOT15.e7270_e5984_s3234_r10724_r10726_p3795/DAOD_EXOT15.17545510._000003.pool.root.1', 'mc16_13TeV.311309.MadGraphPythia8EvtGen_A14NNPDF31LO_HSS_LLP_mH125_mS5_ltlow.deriv.DAOD_EXOT15.e7270_e5984_s3234_r10724_r10726_p3795/DAOD_EXOT15.17545510._000004.pool.root.1', 'mc16_13TeV.311309.MadGraphPythia8EvtGen_A14NNPDF31LO_HSS_LLP_mH125_mS5_ltlow.deriv.DAOD_EXOT15.e7270_e5984_s3234_r10724_r10726_p3795/DAOD_EXOT15.17545510._000005.pool.root.1', 'mc16_13TeV.311309.MadGraphPythia8EvtGen_A14NNPDF31LO_HSS_LLP_mH125_mS5_ltlow.deriv.DAOD_EXOT15.e7270_e5984_s3234_r10724_r10726_p3795/DAOD_EXOT15.17545510._000006.pool.root.1', 'mc16_13TeV.311309.MadGraphPythia8EvtGen_A14NNPDF31LO_HSS_LLP_mH125_mS5_ltlow.deriv.DAOD_EXOT15.e7270_e5984_s3234_r10724_r10726_p3795/DAOD_EXOT15.17545510._000007.pool.root.1']}
        return push_mock

# desktop-rucio download dataset
def test_dr_good(already_present_ds):
    url = 'localds://mc16_13TeV.311309.MadGraphPythia8EvtGen_A14NNPDF31LO_HSS_LLP_mH125_mS5_ltlow.deriv.DAOD_EXOT15.e7270_e5984_s3234_r10724_r10726_p3795'
    r = resolve_local_ds_url(url)
    already_present_ds.assert_called_once_with('http://localhost:8000/ds?ds_name=mc16_13TeV.311309.MadGraphPythia8EvtGen_A14NNPDF31LO_HSS_LLP_mH125_mS5_ltlow.deriv.DAOD_EXOT15.e7270_e5984_s3234_r10724_r10726_p3795')
    assert r is not None
    assert len(r) == 7
    for u in r:
        parsed = urlparse(u)
        f = f'{parsed.netloc}{parsed.path}'
        assert os.path.exists(f)

# Weird schemes
def test_weird_url_scheme():
    url = 'bogus://dataset_du_jour'
    try:
        resolve_local_ds_url(url)
        assert False
    except GridDsException:
        pass

