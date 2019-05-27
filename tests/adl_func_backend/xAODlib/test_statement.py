# Test the statement objects
from adl_func_backend.xAODlib.statement import block, BlockException
# Looking up representations in blocks

def test_create_top_level_block():
    _ = block()

def test_lookup_rep_not_in_block():
    b = block()
    assert None is b.get_rep("dude")

def test_lookup_rep_in_block():
    b = block()
    n = "dude"
    b.set_rep(n, 5)
    assert 5 is b.get_rep(n)

def test_set_rep_twice_fail():
    b = block()
    n = "dude"
    b.set_rep(n, 5)
    try:
        b.set_rep(n, 10)
        assert False
    except BlockException:
        pass
