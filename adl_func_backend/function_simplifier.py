# Various node visitors to clean up nested function calls of various types.
from clientlib.query_ast import Select, Where, SelectMany, First
from clientlib.ast_util import lambda_body, lambda_body_replace, lambda_unwrap, lambda_call, lambda_build, lambda_is_identity, lambda_test, lambda_is_true
import copy
import ast

argument_var_counter = 0
def arg_name():
    'Return a unique name that can be used as an argument'
    global argument_var_counter
    n = 'arg_{0}'.format(argument_var_counter)
    argument_var_counter += 1
    return n

def convolute(ast_g, ast_f):
    'Return an AST that represents g(f(args))'
    #TODO: fix up the ast.Calls to use lambda_call if possible

    # Sanity checks. For example, g can have only one input argument (e.g. f's result)
    if (not lambda_test(ast_g)) or (not lambda_test(ast_f)):
        raise BaseException("Only lambdas in Selects!")
    
    # Combine the lambdas into a single call by calling g with f as an argument
    l_g = lambda_unwrap(ast_g)
    l_f = lambda_unwrap(ast_f)

    x = arg_name()
    f_arg = ast.Name(x, ast.Load())
    call_g = ast.Call(l_g, [ast.Call(l_f, [f_arg], [])], [])

    # TODO: Rewrite with lambda_build
    args = ast.arguments(args=[ast.arg(arg=x)])
    call_g_lambda = ast.Lambda(args=args, body=call_g)

    # Build a new call to nest the functions
    return call_g_lambda

