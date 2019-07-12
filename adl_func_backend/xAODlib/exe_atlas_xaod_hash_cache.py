# Contains code to transform the AST into files and C++ code, but not actually run them.
import ast
from collections import namedtuple
import os
import pickle
from typing import Iterable
from adl_func_backend.ast import ast_hash
from adl_func_backend.xAODlib.atlas_xaod_executor import atlas_xaod_executor
from adl_func_backend.util_LINQ import find_dataset
from adl_func_client.query_result_asts import ResultTTree

class CacheExeException(BaseException):
    def __init__ (self, message):
        BaseException.__init__(self, message)

# Return info
HashXAODExecutorInfo = namedtuple('HashXAODExecutorInfo', 'hash main_script treename output_filename, filelist')

def _build_result(cache: tuple, url_list: Iterable[str]) -> HashXAODExecutorInfo:
    'Helper routine to build out a full result'
    return HashXAODExecutorInfo(cache[0], cache[1], cache[2], cache[3], url_list)

def use_executor_xaod_hash_cache(a: ast.AST, cache_path: str) -> HashXAODExecutorInfo:
    r'''Write out the C++ code and supporting files to a cache
    
    Arguments:
        a           The ast that will be transformed
        cache_path  Path the cache directory. We will write everything out in there.

    Returns:
        HashXAODExecutorInfo    Named tuple with the hash and the list of files in it.
    '''
    # We can only do this if the result is going to be a ROOT file(s). So make sure.
    if not isinstance(a, ResultTTree):
        raise CacheExeException(f'Can only cache results for a ROOT tree, not for {type(a).__name__}.')

    # Calculate the AST hash. If this is already around then we don't need to do very much!
    hash = ast_hash.calc_ast_hash(a)

    # Next, see if the hash file is there.
    query_file_path = os.path.join(cache_path, hash)
    if os.path.isdir(query_file_path):
        # We have a cache hit. Look it up.
        file = find_dataset(a)
        with open(os.path.join(query_file_path, 'rep_cache.pickle'), 'rb') as f:
            result_cache = pickle.load(f)
            return _build_result(result_cache, file.url)

    # Create the files to run in that location.
    os.mkdir(query_file_path)
    exe = atlas_xaod_executor()
    f_spec = exe.write_cpp_files(exe.apply_ast_transformations(a), query_file_path)

    # Write out the basic info for the result rep and the runner into that location.
    result_cache = (hash, f_spec.main_script, f_spec.result_rep.treename, f_spec.result_rep.filename)
    with open(os.path.join(query_file_path, 'rep_cache.pickle'), 'wb') as f:
        pickle.dump(result_cache, f)
    
    return _build_result(result_cache, f_spec.input_urls)
