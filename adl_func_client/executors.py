# Executors for transmitting queries over the network.
import ast
from pickle import dumps


def use_executor_to_ast(ast: ast.AST):
    '''
    Return the pickle data for an ast as an executor.
    '''
    return dumps(ast)