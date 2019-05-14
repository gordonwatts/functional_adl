# Helpers for LINQ operators and LINQ expressions in AST form.
# Utility routines to manipulate LINQ expressions.
import adl_func_client.query_ast as query_ast
from adl_func_client.event_dataset import EventDataset
import ast
from typing import Optional

def find_dataset(a: ast.AST) -> EventDataset:
    r'''
    Given an input query ast, find the EventDataSet and return it.

    Args:
        a:      An AST that represents a query

    Returns:
        The `EventDataSet` at the root of this query. It will not be None.

    Exceptions:
        If there is more than one `EventDataSet` found in the query or if there
        is no `EventDataSet` at the root of the query, then an exception is thrown.
    '''

    class ds_finder(ast.NodeVisitor):
        def __init__(self):
            self.ds: Optional[EventDataset] = None
        
        def visit_EventDataset(self, node):
            if self.ds is not None:
                raise BaseException("AST Query has more than one EventDataSet in it!")
            self.ds = node

        def generic_visit(self, node):
            ast.NodeVisitor.generic_visit(self, node)
    
    ds_f = ds_finder()
    ds_f.visit(a)

    if ds_f.ds is None:
        raise BaseException("AST Query has no root EventDataset")

    return ds_f.ds
