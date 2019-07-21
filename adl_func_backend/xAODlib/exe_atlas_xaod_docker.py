# Use an in-process docker container to do the actual execution work.
from adl_func_backend.xAODlib.atlas_xaod_executor import atlas_xaod_executor
import adl_func_backend.xAODlib.result_handlers as rh

import ast
import tempfile
from urllib.parse import urlparse
import subprocess
import os
import asyncio

# Use this to turn on dumping of output and C++
dump_running_log = True
dump_cpp = False

class AtlasXAODDockerException(BaseException):
    def __init__ (self, message):
        BaseException.__init__(self, message)

# Result handlers - for each return type representation, add a handler that can process it
result_handlers = {
        rh.cpp_ttree_rep: rh.extract_result_TTree,
        rh.cpp_awkward_rep: rh.extract_awkward_result,
        rh.cpp_pandas_rep: rh.extract_pandas_result,
}

async def use_executor_xaod_docker(a: ast.AST):
    '''
    Execute a query on the local machine, in a docker container.
    '''
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
            for u in f_spec.input_urls:
                (scheme, netloc, path, _, _, _) = urlparse(u)

                # How we process this is going to depend a bit on the scheme that we are going to handle.
                if scheme == 'file':
                    if len(netloc) != 0:
                        raise AtlasXAODDockerException(f'Only file URLs that have no node specification can be used (e.g. file:///path) : {u}')
                    ds_path = path[1:]
                    datafile = os.path.basename(ds_path)
                    flist_out.write(f'/data/{datafile}\n')
                    if datafile_dir is None:
                        datafile_dir = os.path.dirname(ds_path)
                    else:
                        t = os.path.dirname(ds_path)
                        if t != datafile_dir:
                            raise BaseException(f'Data files must be from the same directory. Have seen {t} and {datafile_dir} so far.')
                elif scheme == 'root':
                    flist_out.write(f'{scheme}://{netloc}/{path}')
                else:
                    raise AtlasXAODDockerException(f'Only URLs with scheme `file` can be used: {u}')

        # Build a docker command to run this.
        datafile_mount = "" if datafile_dir is None else f'-v {datafile_dir}:/data'
        docker_cmd = f'docker run --rm -v {f_spec.output_path}:/scripts -v {f_spec.output_path}:/results {datafile_mount} atlas/analysisbase:21.2.62 /scripts/{f_spec.main_script} /results'
        proc = await asyncio.create_subprocess_shell(docker_cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE)
        p_stdout, p_stderr = await proc.communicate()
        if proc.returncode != 0 or dump_running_log:
            print (f"Result of run: {proc.returncode}")
            print (f'Output:\n{p_stdout}')
            print (f'Error:\n{p_stderr}')
        if proc.returncode != 0:
            raise BaseException("Docker command failed with error {0}".format(proc.returncode))
        if dump_cpp:
            os.system("type " + os.path.join(str(local_run_dir), "query.cxx"))

        # Now that we have run, we can pluck out the result.
        if type(f_spec.result_rep) not in result_handlers:
            raise BaseException(f'Do not know how to process result of type {type(f_spec.result_rep.__name__)}.')
        return result_handlers[type(f_spec.result_rep)](f_spec.result_rep, local_run_dir)
