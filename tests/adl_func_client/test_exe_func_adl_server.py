# Tests to make sure we get at the functionality in the remote executor.
from adl_func_client.event_dataset import EventDataset
from adl_func_client.use_exe_func_adl_server import use_exe_func_adl_server, FuncADLServerException
from unittest.mock import Mock
import pandas as pd
import pytest
import os
import asyncio

@pytest.yield_fixture()
def event_loop():
    'Get the loop done right on windows'
    if os.name == 'nt':
        loop = asyncio.ProactorEventLoop()
    else:
        loop = asyncio.SelectorEventLoop()
    yield loop
    loop.close()

@pytest.fixture()
def one_file_remote_query_return(monkeypatch):
    'Setup mocks for a remote call that returns a single valid file to read from'
    push_mock = Mock()
    status_mock = Mock()
    push_mock.return_value = status_mock
    monkeypatch.setattr('requests.post', push_mock)
    status_mock.json.return_value={'files': [['root://localhost/file.root', 'dudetree3']], 'phase': 'done', 'done': True, 'jobs': 1}
    return None

@pytest.fixture()
def one_file_root_local_and_http(monkeypatch):
    'Mocks to return a file with root and http access'
    push_mock = Mock()
    status_mock = Mock()
    push_mock.return_value = status_mock
    monkeypatch.setattr('requests.post', push_mock)
    status_mock.json.return_value={'files': [['root://localhost/file.root', 'dudetree3']], 'httpfiles': [['http://localhost:30000/file.root', 'dudetree3']], 'phase': 'done', 'done': True, 'jobs': 1}
    return None

@pytest.fixture()
def one_file_with_local_access_nonlocal(monkeypatch):
    'Setup mocks for a remote call that returns a single file with a local access list'
    push_mock = Mock()
    status_mock = Mock()
    push_mock.return_value = status_mock
    monkeypatch.setattr('requests.post', push_mock)
    status_mock.json.return_value={'files': [['root://localhost/file.root', 'dudetree3']], 'phase': 'done', 'done': True, 'jobs': 1, 'localfiles': [['file:///data/file.root', 'dudetree3']]}
    return None

@pytest.fixture()
def one_file_with_local_access(monkeypatch):
    'Setup mocks for a remote call that returns a single file with a local access list'
    push_mock = Mock()
    status_mock = Mock()
    push_mock.return_value = status_mock
    monkeypatch.setattr('requests.post', push_mock)
    status_mock.json.return_value={'files': [['root://localhost/file.root', 'dudetree3']], 'phase': 'done', 'done': True, 'jobs': 1, 'localfiles': [['file:///tests/adl_func_client/sample_root_result.root', 'dudetree3']]}
    return None

@pytest.fixture()
def one_actual_file(monkeypatch):
    'Setup mocks for a remote call that returns local file that points to a real file'
    push_mock = Mock()
    status_mock = Mock()
    push_mock.return_value = status_mock
    monkeypatch.setattr('requests.post', push_mock)
    status_mock.json.return_value={
        'files': [
            ['root://localhost/tests/adl_func_client/sample_root_result.root', 'dudetree3']
            ],
        'localfiles': [
            ['file:///tests/adl_func_client/sample_root_result.root', 'dudetree3']
            ],
        'phase': 'done', 'done': True, 'jobs': 1}
    return None

@pytest.fixture()
def two_actual_files(monkeypatch):
    'Setup mocks for a remote call that returns local file that points to a real file'
    push_mock = Mock()
    status_mock = Mock()
    push_mock.return_value = status_mock
    monkeypatch.setattr('requests.post', push_mock)
    status_mock.json.return_value={
        'files': [
                    ['root://localhost/tests/adl_func_client/sample_root_result.root', 'dudetree3'],
                    ['root://localhost/tests/adl_func_client/sample_root_result.root', 'dudetree3']
                ],
        'localfiles': [
                    ['file:///tests/adl_func_client/sample_root_result.root', 'dudetree3'],
                    ['file:///tests/adl_func_client/sample_root_result.root', 'dudetree3']
                ],
        'phase': 'done', 'done': True, 'jobs': 1}
    return None

@pytest.fixture()
def one_file_remote_query_return_two(monkeypatch):
    'Setup mocks for a remote call that returns a single valid file to read from'
    push_mock = Mock()
    status_mock1 = Mock()
    status_mock2 = Mock()
    push_mock.side_effect = [status_mock1, status_mock2]
    monkeypatch.setattr('requests.post', push_mock)
    status_mock1.json.return_value={'files': [], 'phase': 'running', 'done': False, 'jobs': 1}
    status_mock2.json.return_value={'files': [['root://localhost/file.root', 'dudetree3']], 'phase': 'done', 'done': True, 'jobs': 1}
    return None

@pytest.fixture()
def ds_returns_bit_by_bit(monkeypatch):
    'Setup mocks for a remote call that returns a single valid file to read from'
    push_mock = Mock()
    status_mock1 = Mock()
    status_mock2 = Mock()
    push_mock.side_effect = [status_mock1, status_mock2]
    monkeypatch.setattr('requests.post', push_mock)
    status_mock1.json.return_value={'files': [['root://localhost/file1.root', 'dudetree3']], 'phase': 'done', 'done': False, 'jobs': 1}
    status_mock2.json.return_value={'files': [['root://localhost/file1.root', 'dudetree3'], ['root://localhost/file2.root', 'dudetree3']], 'phase': 'done', 'done': True, 'jobs': 1}
    return None

@pytest.fixture()
def query_crashes(monkeypatch):
    'Setup mocks for a remote call that returns a single valid file to read from'
    push_mock = Mock()
    status_mock = Mock()
    push_mock.return_value = status_mock
    monkeypatch.setattr('requests.post', push_mock)
    status_mock.json.return_value={'files': [], 'phase': 'crashed_request', 'done': True, 'jobs': 1, 'message': "failed totally", 'log': ['line1', 'line2', 'line3']}
    return None

@pytest.fixture()
def running_on_posix(monkeypatch):
    'os.name returns posix'
    monkeypatch.setattr('os.name', 'posix')
    return None

@pytest.fixture()
def running_on_nt(monkeypatch):
    'os.name returns nt'
    monkeypatch.setattr('os.name', 'nt')
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

@pytest.mark.asyncio
async def test_simple_root_query(one_file_remote_query_return, simple_query_ast_ROOT, running_on_posix):
    'Most simple implementation'
    r = await use_exe_func_adl_server(simple_query_ast_ROOT)
    assert type(r) is dict
    assert 'files' in r
    assert len(r['files']) == 1
    assert r['files'][0][0] == 'root://localhost/file.root'
    assert r['files'][0][1] == 'dudetree3'

def test_print_files(one_file_remote_query_return, simple_query_ast_ROOT):
    'Simple query, print out things'
    _ = use_exe_func_adl_server(simple_query_ast_ROOT, quiet=False)

@pytest.mark.asyncio
async def test_simple_root_query_not_read_at_first(one_file_remote_query_return_two, simple_query_ast_ROOT, running_on_posix):
    'Most simple implementation'
    r = await use_exe_func_adl_server(simple_query_ast_ROOT, sleep_interval=0)
    assert type(r) is dict
    assert 'files' in r
    assert len(r['files']) == 1
    assert r['files'][0][0] == 'root://localhost/file.root'

def test_dump_phases(one_file_remote_query_return_two, simple_query_ast_ROOT):
    'Most simple implementation'
    _ = use_exe_func_adl_server(simple_query_ast_ROOT, sleep_interval=0, quiet=False)

@pytest.mark.asyncio
async def test_first_file_good_enough(ds_returns_bit_by_bit, simple_query_ast_ROOT, running_on_posix):
    r = await use_exe_func_adl_server(simple_query_ast_ROOT, sleep_interval=0, wait_for_finished=False)
    assert len(r['files']) == 1
    assert r['files'][0][0] == 'root://localhost/file1.root'

@pytest.mark.asyncio
async def test_wait_for_all_files(ds_returns_bit_by_bit, simple_query_ast_ROOT, running_on_posix):
    r = await use_exe_func_adl_server(simple_query_ast_ROOT, sleep_interval=0, wait_for_finished=True)
    assert len(r['files']) == 2
    assert r['files'][0][0] == 'root://localhost/file1.root'
    assert r['files'][1][0] == 'root://localhost/file2.root'

@pytest.mark.asyncio
async def test_get_pandas(one_actual_file, simple_query_ast_Pandas, running_on_posix):
    r = await use_exe_func_adl_server(simple_query_ast_Pandas)
    assert type(r) is pd.DataFrame
    assert len(r) == 356159

@pytest.mark.asyncio
async def test_get_pandas_from_two_files(two_actual_files, simple_query_ast_Pandas, running_on_posix):
    r = await use_exe_func_adl_server(simple_query_ast_Pandas)
    assert type(r) is pd.DataFrame
    assert len(r) == 356159*2

@pytest.mark.asyncio
async def test_get_awkward(one_actual_file, simple_query_ast_awkward, running_on_posix):
    r = await use_exe_func_adl_server(simple_query_ast_awkward)
    assert type(r) is dict
    assert len(r.keys()) == 1
    assert list(r.keys())[0] == b'JetPt'
    assert len(r[b'JetPt']) == 356159

@pytest.mark.asyncio
async def test_get_awkward_from_two_files(two_actual_files, simple_query_ast_awkward, running_on_posix):
    r = await use_exe_func_adl_server(simple_query_ast_awkward)
    assert type(r) is dict
    assert len(r.keys()) == 1
    assert list(r.keys())[0] == b'JetPt'
    assert len(r[b'JetPt']) == 356159*2

@pytest.mark.asyncio
async def test_prefer_local_access_not_on_this_system(one_file_with_local_access_nonlocal, simple_query_ast_ROOT, running_on_posix):
    'Check to make sure we do not choose the local access guy since we cannot see it'
    r = await use_exe_func_adl_server(simple_query_ast_ROOT)
    assert r['files'][0][0] == 'root://localhost/file.root'
    assert r['files'][0][1] == 'dudetree3'

@pytest.mark.asyncio
async def test_prefer_local_access(one_file_with_local_access, simple_query_ast_ROOT, running_on_posix):
    'Check to make sure we do not choose the local access guy since we cannot see it'
    r = await use_exe_func_adl_server(simple_query_ast_ROOT)
    assert r['files'][0][0] == 'file:///tests/adl_func_client/sample_root_result.root'
    assert r['files'][0][1] == 'dudetree3'

@pytest.mark.asyncio
async def test_prefer_local_access_pandas(one_file_with_local_access, simple_query_ast_Pandas, running_on_posix):
    'Check to make sure we do not choose the local access guy since we cannot see it'
    r = await use_exe_func_adl_server(simple_query_ast_Pandas)
    assert len(r) == 356159
 
@pytest.mark.asyncio
async def test_prefer_local_access_awkward(one_file_with_local_access, simple_query_ast_awkward, running_on_posix):
    'Check to make sure we do not choose the local access guy since we cannot see it'
    r = await use_exe_func_adl_server(simple_query_ast_awkward)
    assert len(r[b'JetPt']) == 356159

@pytest.mark.asyncio
async def test_prefer_root_over_http_posix(one_file_root_local_and_http, simple_query_ast_ROOT, running_on_posix):
    r = await use_exe_func_adl_server(simple_query_ast_ROOT)
    assert r['files'][0][0] == 'root://localhost/file.root'
    assert r['files'][0][1] == 'dudetree3'

@pytest.mark.asyncio
async def test_prefer_http_over_root_nt(one_file_root_local_and_http, simple_query_ast_ROOT, running_on_nt):
    r = await use_exe_func_adl_server(simple_query_ast_ROOT)
    assert r['files'][0][0] == 'http://localhost:30000/file.root'
    assert r['files'][0][1] == 'dudetree3'

@pytest.mark.asyncio
async def test_nothing_good(one_file_remote_query_return, simple_query_ast_ROOT, running_on_nt):
    try:
        _ = await use_exe_func_adl_server(simple_query_ast_ROOT)
        assert False
    except FuncADLServerException:
        return

@pytest.mark.asyncio
async def test_crashed_query(simple_query_ast_ROOT, running_on_posix, query_crashes):
    try:
        await use_exe_func_adl_server(simple_query_ast_ROOT)
        assert False
    except FuncADLServerException as e:
        assert "line1" in str(e)
        return
