# Testing helper. Create an AST for a query and write it out to a final in a pickle format.
from adl_func_client.event_dataset import EventDataset
import pickle
import sys

f_ds = EventDataset(r'localds://mc16_13TeV.311309.MadGraphPythia8EvtGen_A14NNPDF31LO_HSS_LLP_mH125_mS5_ltlow.deriv.DAOD_EXOT15.e7270_e5984_s3234_r9364_r9315_p3795')

def ast_jet_pt():
    return f_ds \
        .SelectMany('lambda e: e.Jets("AntiKt4EMTopoJets")') \
        .Select('lambda j: j.pt()/1000.0') \
        .AsROOTTTree('output.root', 'dudetree', 'JetPt') \
        .value(executor=lambda a: a)

def generate_ast(ast_number:int):
    'Return an ast'
    if ast_number == 0:
        return ast_jet_pt()
    else:
        raise BaseException(f'Internal error - unknown ast request number {ast_number}')

def write_ast (ast_number:int, output_filename: str):
    'Write an ast'
    a = generate_ast(ast_number)
    with open(output_filename, 'wb') as f:
        pickle.dump(a, f)

if __name__ == '__main__':
    bad_args = False
    bad_args = len(sys.argv) != 3
    bad_args = bad_args or not str.isdigit(sys.argv[1])
    bad_args = bad_args or int(sys.argv[1]) != 0

    if bad_args:
        print ("Usage: python write_ast.py <ast-number> <outputfile>")
        print ("       Where ast version is:")
        print ("       0 - Simple jet pt from ATLAS xAOD")
    else:
        write_ast(int(sys.argv[1]), sys.argv[2])

