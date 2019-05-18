# Code to aid with accessing jet collections
import adl_func_backend.cpplib.cpp_ast as cpp_ast
import adl_func_backend.cpplib.cpp_representation as crep
import adl_func_backend.cpplib.cpp_types as ctyp 
from adl_func_backend.cpplib.cpp_vars import unique_name
import ast

def getAttributeFloatAst(call_node: ast.Call):
    r'''
    Return an attribute on one of the xAOD objects.
    '''
    # Get the name of the moment out
    if len(call_node.args) != 1:
        raise BaseException("Calling getMomentFloat - only one argument is allowed")
    if not isinstance(call_node.args[0], ast.Str):
        raise BaseException("Calling getMomentFloat - only acceptable argument is a string")

    r = cpp_ast.CPPCodeValue()
    # We don't need include files for this - just quick access
    r.args = ['moment_name',]
    r.replacement_instance_obj = ('obj_j', call_node.func.value.id)
    r.running_code += ['float result = obj_j->getAttribute<float>(moment_name);']
    r.result = 'result'
    r.result_rep = lambda sc: crep.cpp_variable(unique_name("jet_attrib"), scope=sc, cpp_type=ctyp.terminal('float'))

    # Replace it as the function that is going to get called.
    call_node.func = r

    return call_node

def getAttributeVectorFloatAst(call_node: ast.Call):
    r'''
    Return a cpp ast accessing a vector of doubles for an xAOD attribute
    '''
    # Get the name of the moment out
    if len(call_node.args) != 1:
        raise BaseException("Calling getMomentFloat - only one argument is allowed")
    if not isinstance(call_node.args[0], ast.Str):
        raise BaseException("Calling getMomentFloat - only acceptable argument is a string")

    r = cpp_ast.CPPCodeValue()
    r.include_files += ['vector']
    r.args = ['moment_name',]
    r.replacement_instance_obj = ('obj_j', call_node.func.value.id)
    r.running_code += ['auto result = obj_j->getAttribute<std::vector<double>>(moment_name);']
    r.result = 'result'
    r.result_rep = lambda sc: crep.cpp_collection(unique_name("jet_vec_attrib_"), scope=sc, collection_type=ctyp.collection(ctyp.terminal('double')))

    # Replace it as the function that is going to get called.
    call_node.func = r

    return call_node

# Config everything.
cpp_ast.method_names['getAttributeFloat'] = getAttributeFloatAst
cpp_ast.method_names['getAttributeVectorFloat'] = getAttributeVectorFloatAst

