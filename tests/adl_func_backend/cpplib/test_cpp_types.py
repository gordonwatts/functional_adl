# Test the cpp representations. These objects are quite simple, so there
# aren't that many tests. Mostly when bugs are found something gets added here.

# Following two lines necessary b.c. I can't figure out how to get pytest to pick up the python path correctly
# despite reading a bunch of docs.
import sys
sys.path.append('.')

import adl_func_backend.cpplib.cpp_types as ctyp
from adl_func_backend.xAODlib.util_scope import top_level_scope

def test_int_pointer():
    t_int = ctyp.terminal('int')
    assert False == t_int.is_pointer()

def test_no_method_type_found():
    assert None == ctyp.method_type_info("bogus", "pt")

def test_method_type_found():
    ctyp.add_method_type_info("bogus", "pt", ctyp.terminal('double'))
    assert 'double' == str(ctyp.method_type_info("bogus", "pt"))