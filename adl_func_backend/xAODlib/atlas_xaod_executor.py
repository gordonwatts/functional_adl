# Drive the translate of the AST from start into a set of files, which one can then do whatever
# is needed to.
import sys
import os
import jinja2
import ast
from collections import namedtuple

from adl_func_backend.ast.tuple_simplifier import remove_tuple_subscripts
from adl_func_backend.ast.function_simplifier import simplify_chained_calls
from adl_func_backend.ast.aggregate_shortcuts import aggregate_node_transformer
from adl_func_backend.cpplib.cpp_functions import find_known_functions
import adl_func_backend.cpplib.cpp_ast as cpp_ast
from adl_func_backend.xAODlib.ast_to_cpp_translator import query_ast_visitor
import adl_func_backend.cpplib.cpp_representation as crep
from adl_func_backend.xAODlib.util_scope import top_level_scope

xAODExecutionInfo = namedtuple('xAODExecutionInfo', 'input_urls result_rep output_path main_script all_filenames')

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
    for dirname in (sys.path + ['/usr/local']):
        candidate = os.path.join(dirname, pathname)
        if matchFunc(candidate):
            return candidate
    raise BaseException("Can't find file %s" % pathname)

def find_file(pathname):
    return _find(pathname)

def find_dir(path):
    return _find(path, matchFunc=os.path.isdir)

class atlas_xaod_executor:
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

    def write_cpp_files(self, ast: ast.AST, output_path: str) -> xAODExecutionInfo:
        r"""
        Given the AST generate the C++ files that need to run. Return them along with
        the input files.
        """

        # Find the base file dataset and mark it.
        from adl_func_backend.util_LINQ import find_dataset
        file = find_dataset(ast)
        iterator = crep.cpp_variable("bogus-do-not-use", top_level_scope(), cpp_type=None)
        file.rep = crep.cpp_sequence(iterator, iterator)

        # Visit the AST to generate the code structure and find out what the
        # result is going to be.
        qv = query_ast_visitor()
        result_rep = qv.get_rep(ast)

        # Emit the C++ code into our dictionaries to be used in template generation below.
        query_code = cpp_source_emitter()
        qv.emit_query(query_code)
        book_code = cpp_source_emitter()
        qv.emit_book(book_code)
        class_dec_code = qv.class_declaration_code()
        includes = qv.include_files()

        # The replacement dict to pass to the template generator can now be filled
        info = {}
        info['query_code'] = query_code.lines_of_query_code()
        info['book_code'] = book_code.lines_of_query_code()
        info['class_dec'] = class_dec_code
        info['include_files'] = includes

        # We use jinja2 templates. Write out everything.
        template_dir = find_dir("adl_func_backend/R21Code")
        j2_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir))
        self.copy_template_file(
            j2_env, info, 'ATestRun_eljob.py', output_path)
        self.copy_template_file(
            j2_env, info, 'package_CMakeLists.txt', output_path)
        self.copy_template_file(j2_env, info, 'query.cxx', output_path)
        self.copy_template_file(j2_env, info, 'query.h', output_path)
        self.copy_template_file(j2_env, info, 'runner.sh', output_path)

        os.chmod(os.path.join(str(output_path), 'runner.sh'), 0o755)

        # Build the return object.
        return xAODExecutionInfo(file.url, result_rep, output_path, 'runner.sh', ['ATestRun_eljob.py', 'package_CMakeLists.txt', 'query.cxx', 'query.h', 'runner.sh'])