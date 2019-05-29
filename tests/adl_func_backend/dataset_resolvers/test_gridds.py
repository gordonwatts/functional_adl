# Test out the grid dataset resolver code
from adl_func_backend.dataset_resolvers.gridds import resolve_local_ds_url, GridDsException
from tempfile import NamedTemporaryFile
from urllib.parse import urlparse
import os

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

# desktop-rucio download dataset
def test_dr_good():
    url = 'localds://mc16_13TeV.311309.MadGraphPythia8EvtGen_A14NNPDF31LO_HSS_LLP_mH125_mS5_ltlow.deriv.DAOD_EXOT15.e7270_e5984_s3234_r10724_r10726_p3795'
    r = resolve_local_ds_url(url)
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

