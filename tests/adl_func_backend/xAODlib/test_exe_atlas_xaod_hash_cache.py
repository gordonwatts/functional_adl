# Test out the hash cache generator

from adl_func_backend.xAODlib.exe_atlas_xaod_hash_cache import use_executor_xaod_hash_cache
from adl_func_client.event_dataset import EventDataset

import tempfile
import ast
import os

def build_ast() -> ast.AST:
    return EventDataset("file://root.root") \
        .Select('lambda e: e.Jets("jets").SelectMany(lambda j: e.Tracks("InnerTracks")).First()') \
        .AsROOTTTree('dude.root', 'analysis', 'JetPt') \
        .value(executor=lambda a: a)

def test_no_cache_ever():
    # Item hasn't been cached before.
    with tempfile.TemporaryDirectory() as local_run_dir:
        r = use_executor_xaod_hash_cache(build_ast(), local_run_dir)
        assert r is not None
        assert len(r.filelist) == 1
        assert r.filelist[0] == 'file:///root.root'
        assert os.path.exists(f'{local_run_dir}/{r.hash}/{r.main_script}')

def test_twice():
    # Item hasn't been cached before.
    with tempfile.TemporaryDirectory() as local_run_dir:
        r1 = use_executor_xaod_hash_cache(build_ast(), local_run_dir)
        r2 = use_executor_xaod_hash_cache(build_ast(), local_run_dir)
        assert r2 is not None
        assert len(r2.filelist) == 1
        assert r2.filelist[0] == 'file:///root.root'
        assert os.path.exists(f'{local_run_dir}/{r2.hash}/{r2.main_script}')
