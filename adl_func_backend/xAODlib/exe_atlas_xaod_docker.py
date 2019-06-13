# Use an in-process docker container to do the actual execution work.
import adl_func_backend.cpplib.cpp_representation as crep
from adl_func_backend.xAODlib.util_scope import top_level_scope
from adl_func_backend.xAODlib.atlas_xaod_executor import atlas_xaod_executor
import adl_func_backend.xAODlib.result_handlers as rh

import ast
import tempfile
from urllib.parse import urlparse
import subprocess
import os

# Use this to turn on dumping of output and C++
dump_running_log = True
dump_cpp = False

# Result handlers - for each return type representation, add a handler that can process it
result_handlers = {
        rh.cpp_ttree_rep: rh.extract_result_TTree,
        rh.cpp_awkward_rep: rh.extract_awkward_result,
        rh.cpp_pandas_rep: rh.extract_pandas_result,
}


def use_executor_xaod_docker(a: ast.AST):
    '''
    Execute a query on the local machine, in a docker container.
    '''
    # Setup the rep for this filter
    from adl_func_backend.util_LINQ import find_dataset
    file = find_dataset(a)
    iterator = crep.cpp_variable("bogus-do-not-use", top_level_scope(), cpp_type=None)
    file.rep = crep.cpp_sequence(iterator, iterator)

    # Construct the files we will run.
    with tempfile.TemporaryDirectory() as local_run_dir:
        os.chmod(local_run_dir, 0o777)

        exe = atlas_xaod_executor()
        f_spec = exe.write_cpp_files(exe.apply_ast_transformations(a), local_run_dir)

        # Write out a file with the mapped in directories.
        # Until we better figure out how to deal with this, there are some restrictions
        # on file locations.
        datafile_dir = None
        with open(f'{local_run_dir}/filelist.txt', 'w') as flist_out:
            for u in file.url:
                (_, netloc, path, _, _, _) = urlparse(u)
                datafile = os.path.basename(netloc + path)
                flist_out.write(f'/data/{datafile}\n')

                if datafile_dir is None:
                    datafile_dir = os.path.dirname(netloc+path)
                else:
                    t = os.path.dirname(netloc+path)
                    if t != datafile_dir:
                        raise BaseException(f'Data files must be from the same directory. Have seen {t} and {datafile_dir} so far.')

        # Build a docker command to run this.
        docker_cmd = f'docker run --rm -v {f_spec.output_path}:/scripts -v {f_spec.output_path}:/results -v {datafile_dir}:/data  atlas/analysisbase:21.2.62 /scripts/{f_spec.main_script}'
        if dump_running_log:
            r = subprocess.call(docker_cmd, stderr=subprocess.STDOUT, shell=False)
            print ("Result of run: {0}".format(r))
        else:
            r = subprocess.call(docker_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, shell=False)
        if r != 0:
            raise BaseException("Docker command failed with error {0}".format(r))
        if dump_cpp:
            os.system("type " + os.path.join(str(local_run_dir), "query.cxx"))

        # Now that we have run, we can pluck out the result.
        if type(f_spec.result_rep) not in result_handlers:
            raise BaseException(f'Do not know how to process result of type {type(f_spec.result_rep.__name__)}.')
        return result_handlers[type(f_spec.result_rep)](f_spec.result_rep, local_run_dir)
