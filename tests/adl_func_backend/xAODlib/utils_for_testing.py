# Some utilities to help with testing out when we have to run a dummy version of the
# xaod executor.
#
from adl_func_backend.xAODlib.atlas_xaod_executor import atlas_xaod_executor
from adl_func_backend.cpplib.cpp_representation import cpp_variable, cpp_sequence
from adl_func_backend.xAODlib.util_scope import top_level_scope
from adl_func_client.ObjectStream import ObjectStream
import ast


class dummy_executor(atlas_xaod_executor):
    'Override the docker part of the execution engine'
    def __init__ (self):
        self.QueryVisitor = None
        self.ResultRep = None

    def get_result(self, q_visitor, result_rep):
        'Got the result. Cache for use in tests'
        self.QueryVisitor = q_visitor
        self.ResultRep = result_rep
        return self

# Define a dataset we can use
class test_stream(ast.AST):
    def __init__ (self):
        iter = cpp_variable("bogus-do-not-use", scope=top_level_scope(), cpp_type=None)
        self.rep = cpp_sequence(iter, iter)
        self.rep._ast = self # So that we get used properly when passed on.

    def get_executor(self):
        return dummy_executor()

class dummy_emitter:
    def __init__ (self):
        self.Lines = []
        self._indent_level = 0

    def add_line (self, l):
        if l == '}':
            self._indent_level -= 1

        self.Lines += [
            "{0}{1}".format("  " * self._indent_level, l)]

        if l == '{':
            self._indent_level += 1

    def process (self, func):
        func(self)
        return self
        
class MyEventStream(ObjectStream):
    def __init__ (self):
        ObjectStream.__init__(self, test_stream())

def get_lines_of_code(executor):
    'Return all lines of code'
    qv = executor.QueryVisitor
    d = dummy_emitter()
    qv.emit_query(d)
    return d.Lines

def find_line_with(text, lines, throw_if_not_found = True):
    'Find the first line with the text. Return its index, zero based'
    for index, l in enumerate(lines):
        if text in l:
            return index
    if throw_if_not_found:
        raise BaseException("Unable to find text '{0}' in any lines in text output".format(text))
    return -1

def find_line_numbers_with(text, lines):
    return [index for index,l in enumerate(lines) if text in l]

def print_lines(lines):
    for l in lines:
        print(l)

def find_next_closing_bracket(lines):
    'Find the next closing bracket. If there is an opening one, then track through to the matching closing one.'
    depth = 0
    for index, l in enumerate(lines):
        if l.strip() == "{":
            depth += 1
        if l.strip() == "}":
            depth -= 1
            if depth < 0:
                return index
    return -1

def find_open_blocks(lines):
    'Search through and record the lines before a {. If a { is closed, then remove that lines'
    stack = []
    last_line_seen = 'xxx-xxx-xxx'
    for l in lines:
        if l.strip() == '{':
            stack += [last_line_seen]
        elif l.strip() == '}':
            stack = stack[:-1]
        last_line_seen = l
    return stack
