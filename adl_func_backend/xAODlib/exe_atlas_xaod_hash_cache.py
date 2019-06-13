# Contains code to transform the AST into files and C++ code, but not actually run them.
import ast
from collections import namedtuple


# Return info
HashXAODExecutorInfo = namedtuple('HashXAODExecutorInfo', 'hash filelist')

def use_executor_xaod_hash_cache(a: ast.AST, cache_path: str) -> HashXAODExecutorInfo:
    r'''Write out the C++ code and supporting files to a cache
    
    Arguments:
        a           The ast that will be transformed
        cache_path  Path the cache directory. We will write everything out in there.

    Returns:
        HashXAODExecutorInfo    Named tuple with the hash and the list of files in it.
    '''

    # Calculate the AST hash. If this is already around then we don't need to do very much!
    import hashlib
    b = bytearray()
    b.extend(map(ord, ast.dump(a)))
    hash = hashlib.md5(b).hexdigest()

    # Next, see if the hash file is there.
    return None