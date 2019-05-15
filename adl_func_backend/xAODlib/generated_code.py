# Hold onto the generated code
from adl_func_backend.xAODlib.statement import block
import adl_func_backend.cpplib.cpp_representation as crep
from adl_func_backend.xAODlib.util_scope import gc_scope, gc_scope_top_level
from typing import Union

class generated_code:
    def __init__(self):
        self._block = block()
        self._book_block = block()
        self._class_vars = []
        self._scope_stack = (self._block,)
        self._include_files = []

    def declare_class_variable(self, var):
        'Declare a variable as an instance of the query class. var must be a cpp_rep'
        self._class_vars += [var]

    def declare_variable(self, v):
        'Declare a variable at the current scope'
        self._scope_stack[-1].declare_variable(v)

    def add_statement(self, st, below = None):
        '''
        Add a statement. By default it is added to whereever the current
        cursor/stack is pointing (to the end of the blow). If we are adding a new
        block, then the cursor is update so future insertions to that block.

        st - The statement to add
        below - If not none, then the statement is added below the given statement,
                and everything that was below is put inside the statement here. The
                current point of insertion is not affected.
        '''
        if below is None:
            self._scope_stack[-1].add_statement(st)
            if isinstance(st, block):
                self._scope_stack = self._scope_stack + (st,)
        else:
            if not isinstance(below, block):
                raise BaseException("Internal Error: Can't a statement below a statement that isn't a scoping block.")
            if not isinstance(st, block):
                raise BaseException("Internal Error: Can't a statement that isn't a scoping block.")
            for s in below._statements:
                st.add_statement(s)
            below._statements = []
            below.add_statement(st)

    def add_include (self, path):
        self._include_files += [path]

    def include_files(self):
        return self._include_files

    def pop_scope(self):
        self._scope_stack = self._scope_stack[:-1]

    def current_scope(self):
        'Return a token that can be later used to set the scoping'
        return gc_scope(self._scope_stack)

    def set_scope(self, scope_info: Union[gc_scope, gc_scope_top_level]):
        'Set the scope to a previously cached value'
        if scope_info is None:
            raise BaseException("Scope can't be set to null")
        if scope_info.is_top_level():
            # Special case this guy as it is a unicorn.
            self._scope_stack = self._scope_stack[:1]
            return

        # Restore it to whatever it was.
        self._scope_stack = scope_info._scope_stack

    def add_book_statement(self, st, below=None):
        self._book_block.add_statement(st)

    def emit_query_code(self, e):
        'Emit query code'
        self._block.emit(e)

    def emit_book_code(self, e):
        'Emit the book method code'
        self._book_block.emit(e)

    def class_declaration_code(self):
        'Return the class variable decls'
        s = []
        for v in self._class_vars:
            s += ["{0} {1};\n".format(v.cpp_type(), v.as_cpp())]

        return s
