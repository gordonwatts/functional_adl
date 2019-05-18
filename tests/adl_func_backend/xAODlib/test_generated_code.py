# Test the generated code object
from adl_func_backend.xAODlib.generated_code import generated_code
import adl_func_backend.xAODlib.statement as statement

class dummy_emitter:
    def __init__ (self):
        self.Lines = []

    def add_line (self, l):
        self.Lines += [l]

    def process (self, func):
        func(self)
        return self

def test_nothing():
    g = generated_code()
    assert 0 == len(g.class_declaration_code())
    assert 2 == len(dummy_emitter().process(g.emit_query_code).Lines)

def test_insert_two_levels():
    s1 = statement.iftest("true")
    s2 = statement.set_var("v1", "true")
    g = generated_code()

    g.add_statement(s1)
    g.add_statement(s2)

    assert 1 == len(s1._statements)

def test_insert_in_middle():
    s1 = statement.iftest("true")
    s2 = statement.set_var("v1", "true")
    g = generated_code()

    g.add_statement(s1)
    g.add_statement(s2)

    s3 = statement.iftest("fork")
    g.add_statement(s3, below=s1)

    assert 1 == len(s1._statements)
    assert 1 == len(s3._statements)

    assert s1._statements[0] is s3
    assert s3._statements[0] is s2