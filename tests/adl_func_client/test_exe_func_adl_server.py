# Tests to make sure we get at the functionality in the remote executor.
from adl_func_client.event_dataset import EventDataset
from adl_func_client.use_exe_func_adl_server import use_exe_func_adl_server
from unittest.mock import Mock
import pandas as pd

import pytest

@pytest.fixture()
def one_file_remote_query_return(monkeypatch):
    'Setup mocks for a remote call that returns a single valid file to read from'
    push_mock = Mock()
    status_mock = Mock()
    push_mock.return_value = status_mock
    monkeypatch.setattr('requests.post', push_mock)
    status_mock.json.return_value={'files': [['file.root', 'dudetree3']], 'phase': 'done', 'done': True, 'jobs': 1}
    return None

@pytest.fixture()
def one_actual_file(monkeypatch):
    'Setup mocks for a remote call that returns local file that points to a real file'
    push_mock = Mock()
    status_mock = Mock()
    push_mock.return_value = status_mock
    monkeypatch.setattr('requests.post', push_mock)
    status_mock.json.return_value={'files': [['tests/adl_func_client/sample_root_result.root', 'dudetree3']], 'phase': 'done', 'done': True, 'jobs': 1}
    return None

@pytest.fixture()
def two_actual_files(monkeypatch):
    'Setup mocks for a remote call that returns local file that points to a real file'
    push_mock = Mock()
    status_mock = Mock()
    push_mock.return_value = status_mock
    monkeypatch.setattr('requests.post', push_mock)
    status_mock.json.return_value={'files': [['tests/adl_func_client/sample_root_result.root', 'dudetree3'], ['tests/adl_func_client/sample_root_result.root', 'dudetree3']], 'phase': 'done', 'done': True, 'jobs': 1}
    return None

@pytest.fixture()
def one_file_remote_query_return_two(monkeypatch):
    'Setup mocks for a remote call that returns a single valid file to read from'
    push_mock = Mock()
    status_mock1 = Mock()
    status_mock2 = Mock()
    push_mock.side_effect = [status_mock1, status_mock2]
    monkeypatch.setattr('requests.post', push_mock)
    status_mock1.json.return_value={'files': [], 'phase': 'done', 'done': False, 'jobs': 1}
    status_mock2.json.return_value={'files': [['file.root', 'dudetree3']], 'phase': 'done', 'done': True, 'jobs': 1}
    return None

@pytest.fixture()
def ds_returns_bit_by_bit(monkeypatch):
    'Setup mocks for a remote call that returns a single valid file to read from'
    push_mock = Mock()
    status_mock1 = Mock()
    status_mock2 = Mock()
    push_mock.side_effect = [status_mock1, status_mock2]
    monkeypatch.setattr('requests.post', push_mock)
    status_mock1.json.return_value={'files': [['file1.root', 'dudetree3']], 'phase': 'done', 'done': False, 'jobs': 1}
    status_mock2.json.return_value={'files': [['file1.root', 'dudetree3'], ['file2.root', 'dudetree3']], 'phase': 'done', 'done': True, 'jobs': 1}
    return None

@pytest.fixture()
def simple_query_ast_ROOT():
    'Return a simple ast for a query'
    f_ds = EventDataset(r'localds://bogus_ds')
    return f_ds \
        .SelectMany('lambda e: e.Jets("AntiKt4EMTopoJets")') \
        .Select('lambda j: j.pt()/1000.0') \
        .AsROOTTTree('output.root', 'trees', 'JetPt') \
        .value(executor=lambda a: a)

@pytest.fixture()
def simple_query_ast_Pandas():
    'Return a simple ast for a query'
    f_ds = EventDataset(r'localds://bogus_ds')
    return f_ds \
        .SelectMany('lambda e: e.Jets("AntiKt4EMTopoJets")') \
        .Select('lambda j: j.pt()/1000.0') \
        .AsPandasDF('JetPt') \
        .value(executor=lambda a: a)

@pytest.fixture()
def simple_query_ast_awkward():
    'Return a simple ast for a query'
    f_ds = EventDataset(r'localds://bogus_ds')
    return f_ds \
        .SelectMany('lambda e: e.Jets("AntiKt4EMTopoJets")') \
        .Select('lambda j: j.pt()/1000.0') \
        .AsAwkwardArray('JetPt') \
        .value(executor=lambda a: a)

def test_simple_root_query(one_file_remote_query_return, simple_query_ast_ROOT):
    'Most simple implementation'
    r = use_exe_func_adl_server(simple_query_ast_ROOT)
    assert type(r) is dict
    assert 'files' in r
    assert len(r['files']) == 1
    assert r['files'][0][0] == 'file.root'
    assert r['files'][0][1] == 'dudetree3'

def test_simple_root_query_not_read_at_first(one_file_remote_query_return_two, simple_query_ast_ROOT):
    'Most simple implementation'
    r = use_exe_func_adl_server(simple_query_ast_ROOT, sleep_interval=0)
    assert type(r) is dict
    assert 'files' in r
    assert len(r['files']) == 1
    assert r['files'][0][0] == 'file.root'

def test_first_file_good_enough(ds_returns_bit_by_bit, simple_query_ast_ROOT):
    r = use_exe_func_adl_server(simple_query_ast_ROOT, sleep_interval=0, wait_for_finished=False)
    assert len(r['files']) == 1
    assert r['files'][0][0] == 'file1.root'

def test_wait_for_all_files(ds_returns_bit_by_bit, simple_query_ast_ROOT):
    r = use_exe_func_adl_server(simple_query_ast_ROOT, sleep_interval=0, wait_for_finished=True)
    assert len(r['files']) == 2
    assert r['files'][0][0] == 'file1.root'
    assert r['files'][1][0] == 'file2.root'

def test_get_pandas(one_actual_file, simple_query_ast_Pandas):
    r = use_exe_func_adl_server(simple_query_ast_Pandas)
    assert type(r) is pd.DataFrame
    assert len(r) == 356159

def test_get_pandas_from_two_files(two_actual_files, simple_query_ast_Pandas):
    r = use_exe_func_adl_server(simple_query_ast_Pandas)
    assert type(r) is pd.DataFrame
    assert len(r) == 356159*2

def test_get_awkward(one_actual_file, simple_query_ast_awkward):
    r = use_exe_func_adl_server(simple_query_ast_awkward)
    assert type(r) is dict
    assert len(r.keys()) == 1
    assert list(r.keys())[0] == b'JetPt'
    assert len(r[b'JetPt']) == 356159

def test_get_awkward_from_two_files(two_actual_files, simple_query_ast_awkward):
    r = use_exe_func_adl_server(simple_query_ast_awkward)
    assert type(r) is dict
    assert len(r.keys()) == 1
    assert list(r.keys())[0] == b'JetPt'
    assert len(r[b'JetPt']) == 356159*2
