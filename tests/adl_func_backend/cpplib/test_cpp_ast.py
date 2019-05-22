# Test out substituting in routines of various types

from adl_func_backend.cpplib.math_utils import DeltaR
from adl_func_client.event_dataset import EventDataset
from tests.adl_func_backend.xAODlib.utils_for_testing import exe_for_test

def test_deltaR_call():
    r=EventDataset("file://root.root").Select('lambda e: DeltaR(1.0, 1.0, 1.0, 1.0)').AsROOTTTree('root.root', 'analysis', 'RunNumber').value(executor=exe_for_test)
    vs = r.QueryVisitor._gc._class_vars
    assert 1 == len(vs)
    assert "double" == str(vs[0].cpp_type())
