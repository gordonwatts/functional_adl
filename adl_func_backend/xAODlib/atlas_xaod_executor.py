# Drive the translate of the AST from start into a set of files
import sys
import os
import tempfile
from urllib.parse import urlparse
import jinja2
import subprocess

from adl_func_backend.ast.tuple_simplifier import remove_tuple_subscripts
from adl_func_backend.ast.function_simplifier import simplify_chained_calls
from adl_func_backend.ast.aggregate_shortcuts import aggregate_node_transformer
from adl_func_backend.cpplib.cpp_functions import find_known_functions
import adl_func_backend.cpplib.cpp_ast as cpp_ast
from adl_func_backend.xAODlib.ast_to_cpp_translator import query_ast_visitor
import adl_func_backend.xAODlib.result_handlers as rh

# Use this to turn on dumping of output and C++
dump_running_log = True
dump_cpp = False

# Result handlers - for each return type representation, add a handler that can process it
result_handlers = {
        rh.cpp_ttree_rep: rh.extract_result_TTree,
        rh.cpp_awkward_rep: rh.extract_awkward_result,
        rh.cpp_pandas_rep: rh.extract_pandas_result,
}


class cpp_source_emitter:
    r'''
    Helper class to emit C++ code as we go
    '''

    def __init__(self):
        self._lines_of_query_code = []
        self._indent_level = 0

    def add_line(self, l):
        'Add a line of code, automatically deal with the indent'
        if l == '}':
            self._indent_level -= 1

        self._lines_of_query_code += [
            "{0}{1}".format("  " * self._indent_level, l)]

        if l == '{':
            self._indent_level += 1

    def lines_of_query_code(self):
        return self._lines_of_query_code

# The following was copied from: https://www.oreilly.com/library/view/python-cookbook/0596001673/ch04s22.html
def _find(pathname, matchFunc=os.path.isfile):
    for dirname in sys.path:
        candidate = os.path.join(dirname, pathname)
        if matchFunc(candidate):
            return candidate
    raise BaseException("Can't find file %s" % pathname)

def find_file(pathname):
    return _find(pathname)

def find_dir(path):
    return _find(path, matchFunc=os.path.isdir)

class atlas_xaod_executor:
    def __init__(self, dataset):
        self._ds = dataset

    def copy_template_file(self, j2_env, info, template_file, final_dir):
        'Copy a file to a final directory'
        j2_env.get_template(template_file).stream(info).dump(final_dir + '/' + template_file)
    
    def apply_ast_transformations(self, ast):
        r'''
        Run through all the transformations that we have on tap to be run on the client side.
        Return a (possibly) modified ast.
        '''

        # Do tuple resolutions. This might eliminate a whole bunch fo code!
        ast = aggregate_node_transformer().visit(ast)
        ast = simplify_chained_calls().visit(ast)
        ast = remove_tuple_subscripts().visit(ast)
        ast = find_known_functions().visit(ast)

        # Any C++ custom code needs to be threaded into the ast
        ast = cpp_ast.cpp_ast_finder().visit(ast)

        # And return the modified ast
        return ast

    def evaluate(self, ast):
        r"""
        Evaluate the ast over the file that we have been asked to run over
        """

        # Visit the AST to generate the code structure and find out what the
        # result is going to be.
        qv = query_ast_visitor()
        result_rep = qv.get_rep(ast)
        return self.get_result(qv, result_rep)

    def get_result(self, qv, result_rep):
        # Emit the C++ code into our dictionaries to be used in template generation below.
        query_code = cpp_source_emitter()
        qv.emit_query(query_code)
        book_code = cpp_source_emitter()
        qv.emit_book(book_code)
        class_dec_code = qv.class_declaration_code()
        includes = qv.include_files()

        # Create a temp directory in which we can run everything.
        with tempfile.TemporaryDirectory() as local_run_dir:
            os.chmod(local_run_dir, 0o777)

            # Parse the dataset. Eventually, this needs to be normalized, but for now.
            # Some current restrictions:
            #   - Can only deal with files in the same directory due to the way we map them into our
            #     docker containers
            datafile_dir = None
            with open(f'{local_run_dir}/filelist.txt', 'w') as flist_out:
                for u in self._ds:
                    (_, netloc, path, _, _, _) = urlparse(u)
                    datafile = os.path.basename(netloc + path)
                    flist_out.write(f'/data/{datafile}\n')

                    if datafile_dir is None:
                        datafile_dir = os.path.dirname(netloc+path)
                    else:
                        t = os.path.dirname(netloc+path)
                        if t != datafile_dir:
                            raise BaseException(f'Data files must be from the same directory. Have seen {t} and {datafile_dir} so far.')

            # The replacement dict to pass to the template generator can now be filled
            info = {}
            info['query_code'] = query_code.lines_of_query_code()
            info['book_code'] = book_code.lines_of_query_code()
            info['class_dec'] = class_dec_code
            info['include_files'] = includes

            # Next, copy over and fill the template files that will control the xAOD running.
            # Assume they are located relative to the python include path.
            template_dir = find_dir("adl_func_backend/R21Code")
            j2_env = jinja2.Environment(
                loader=jinja2.FileSystemLoader(template_dir))
            self.copy_template_file(
                j2_env, info, 'ATestRun_eljob.py', local_run_dir)
            self.copy_template_file(
                j2_env, info, 'package_CMakeLists.txt', local_run_dir)
            self.copy_template_file(j2_env, info, 'query.cxx', local_run_dir)
            self.copy_template_file(j2_env, info, 'query.h', local_run_dir)
            self.copy_template_file(j2_env, info, 'runner.sh', local_run_dir)

            os.chmod(os.path.join(str(local_run_dir), 'runner.sh'), 0o755)

            # Now use docker to run this mess
            docker_cmd = "docker run --rm -v {0}:/scripts -v {0}:/results -v {1}:/data  atlas/analysisbase:21.2.62 /scripts/runner.sh".format(
                local_run_dir, datafile_dir)
            
            if dump_running_log:
                r = subprocess.call(docker_cmd, stderr=subprocess.STDOUT, shell=False)
                print ("Result of run: {0}".format(r))
            else:
                r = subprocess.call(docker_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, shell=False)
            if r != 0:
                raise BaseException("Docker command failed with error {0}".format(r))

            if dump_cpp:
                os.system("type " + os.path.join(str(local_run_dir), "query.cxx"))

            # Extract the result.
            if type(result_rep) not in result_handlers:
                raise BaseException('Do not know how to process result of type {0}.'.format(type(result_rep).__name__))
            return result_handlers[type(result_rep)](result_rep, local_run_dir)
