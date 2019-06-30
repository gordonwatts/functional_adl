# Test out the hash cache generator

from adl_func_backend.xAODlib.exe_atlas_xaod_hash_cache import use_executor_xaod_hash_cache, CacheExeException
from adl_func_client.event_dataset import EventDataset

import tempfile
import ast
import os

def build_ast() -> ast.AST:
    return EventDataset("file://root.root") \
        .Select('lambda e: e.Jets("jets").SelectMany(lambda j: e.Tracks("InnerTracks")).First()') \
        .AsROOTTTree('dude.root', 'forkme', 'JetPt') \
        .value(executor=lambda a: a)

def build_ast_dr() -> ast.AST:
    return EventDataset("file://root.root") \
        .Select('lambda e: e.Jets("jets").SelectMany(lambda j: e.Tracks("InnerTracks")).First()') \
        .Select('lambda e: DeltaR(e.eta(), e.phi(), e.eta(), e.phi())') \
        .AsROOTTTree('dude.root', 'forkme', 'JetPt') \
        .value(executor=lambda a: a)

def build_ast_pandas() -> ast.AST:
    return EventDataset("file://root.root") \
        .Select('lambda e: e.Jets("jets").SelectMany(lambda j: e.Tracks("InnerTracks")).First()') \
        .AsPandasDF('JetPt') \
        .value(executor=lambda a: a)

def test_no_cache_ever():
    # Item hasn't been cached before.
    with tempfile.TemporaryDirectory() as local_run_dir:
        r = use_executor_xaod_hash_cache(build_ast(), local_run_dir)
        assert r is not None
        assert len(r.filelist) == 1
        assert r.filelist[0] == 'file:///root.root'
        assert os.path.exists(f'{local_run_dir}/{r.hash}/{r.main_script}')
        assert r.treename.startswith('forkme')
        # Because it isn't easy to change this in the ATLAS framework
        assert r.output_filename == 'ANALYSIS.root'

def test_deltaR():
    'Make sure there is no exception when doing a deltaR'
    with tempfile.TemporaryDirectory() as local_run_dir:
        r = use_executor_xaod_hash_cache(build_ast_dr(), local_run_dir)


def test_cant_cache_non_root():
    try:
        with tempfile.TemporaryDirectory() as local_run_dir:
            use_executor_xaod_hash_cache(build_ast_pandas(), local_run_dir)
            assert False
    except CacheExeException:
        pass

def test_twice():
    # Item hasn't been cached before.
    with tempfile.TemporaryDirectory() as local_run_dir:
        _ = use_executor_xaod_hash_cache(build_ast(), local_run_dir)
        r = use_executor_xaod_hash_cache(build_ast(), local_run_dir)
        assert r is not None
        assert len(r.filelist) == 1
        assert r.filelist[0] == 'file:///root.root'
        assert os.path.exists(f'{local_run_dir}/{r.hash}/{r.main_script}')
        assert r.treename.startswith('forkme')
        # Because it isn't easy to change this in the ATLAS framework
        assert r.output_filename == 'ANALYSIS.root'
