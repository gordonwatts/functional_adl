# Tests that make sure the xaod executor is working correctly
from adl_func_client.event_dataset import EventDataset
from adl_func_backend.xAODlib.atlas_xaod_executor import atlas_xaod_executor
import ast


# An executor that will run the xAOD infrastructure. This would be defaulted for the actual user.
def xaod_process_ast(a: ast.AST):
    exe = atlas_xaod_executor(None)
    return exe.evaluate(exe.apply_ast_transformations(ast))

def test_simple_query_run_rootfile():
    'This will do a simple test on a local file - it takes a while to run, so may not want it as part of regular testing'
    rf = EventDataset("file://D:/GRIDDSDR/mc16_13TeV.311309.MadGraphPythia8EvtGen_A14NNPDF31LO_HSS_LLP_mH125_mS5_ltlow.deriv.DAOD_EXOT15.e7270_e5984_s3234_r10201_r10210_p3795/DAOD_EXOT15.17545497._000001.pool.root.1") \
        .SelectMany("lambda e: e.Jets('AntiKt4EMTopoJets')") \
        .Select("lambda j: j.pt()") \
        .AsROOTTTree("output.root", "analysis", columns=['JetPt']) \
        .value()
    
    assert rf is not None
    # Check the file comes back ok.
    assert False