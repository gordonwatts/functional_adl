# Use an in process docker container to do the actual execution work.
import adl_func_backend.cpplib.cpp_representation as crep
from adl_func_backend.xAODlib.util_scope import top_level_scope
from adl_func_backend.xAODlib.atlas_xaod_executor import atlas_xaod_executor

import ast


def use_executor_xaod_docker(a: ast.AST):
    '''
    Execute a query on the local machine, in a docker container.
    '''
    # Setup the rep for this filter
    from adl_func_backend.util_LINQ import find_dataset
    file = find_dataset(a)
    iterator = crep.cpp_variable("bogus-do-not-use", top_level_scope(), cpp_type=None)
    file.rep = crep.cpp_sequence(iterator, iterator)

    # Use the dummy executor to process this, and return it.
    exe = atlas_xaod_executor(file.url)
    return exe.evaluate(exe.apply_ast_transformations(a))

    