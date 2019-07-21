# Simple command line that will translate an AST to a C++ program.
from adl_func_backend.xAODlib.exe_atlas_xaod_hash_cache import use_executor_xaod_hash_cache

import sys
import os
import pickle
import ast

def translate_ast_to_cpp(ast_filename:str, output_path:str):
    'Load an ast from the ast file and write it out as C++ files'

    # Load the ast
    a = None
    with open(ast_filename, 'rb') as f:
        a = pickle.load(f)
    if (a is None) or not issubclass(a, type(ast.AST)):
        print (f'The ast file {ast_filename} did not contain an ast object!')
        return

    # Now do the translation.
    r = use_executor_xaod_hash_cache (a, output_path)

    # Dump to stdout the results of this
    print (r.hash)
    print (r.main_script)
    print (type(r.result_rep).__name__)
    print (', '.join(r.filelist))

if __name__ == "__main__":
    bad_args = len(sys.argv) != 3
    bad_args = bad_args or not os.path.isfile(sys.argv[1])
    bad_args = bad_args or not os.path.isdir(sys.argv[2])
    if bad_args:
        print ("Usage: python translate_ast_to_cpp.py <ast-pickle_filename> <output-directory>")
        print ("  Input file and output directory must exist.")
    else:
        translate_ast_to_cpp(sys.argv[1], sys.argv[2])