# Test the simple type information system.

# Following two lines necessary b.c. I can't figure out how to get pytest to pick up the python path correctly
# despite reading a bunch of docs.
import sys
# Code to do the testing starts here.
from tests.adl_func_backend.xAODlib.utils_for_testing import *
import adl_func_backend.cpplib.cpp_types as ctyp

def test_cant_call_double():
    try: 
        MyEventStream() \
            .Select("lambda e: e.Jets('AntiKt4EMTopoJets').Select(lambda j: j.pt().eta()).Sum()") \
            .AsROOTFile("n_jets") \
            .value()
    except BaseException as e:
        if "Unable to call method 'eta' on type 'double'" not in str(e):
            raise e from None
        assert "Unable to call method 'eta' on type 'double'" in str(e)
        return
    # Should never get here!
    assert False

def test_can_call_prodVtx():
    ctyp.add_method_type_info("xAOD::TruthParticle", "prodVtx", ctyp.terminal('xAODTruth::TruthVertex', is_pointer=True))
    MyEventStream() \
        .Select("lambda e: e.TruthParticles('TruthParticles').Select(lambda t: t.prodVtx().x()).Sum()") \
        .AsROOTFile("n_jets") \
        .value()
