# Code to support running an ast at a remote func-adl server.
import ast
import requests
import pickle
import time

class walk_ast(ast.NodeTransformer):
    'Walk the AST, replace the ROOT lookup node by something we know how to deal with.'
    def __init__(self, node:ast.AST, sleep_interval_seconds:int, partial_ds_ok:bool):
        'Set the node were we can go pick up the data'
        self._node = node
        self._sleep_time = sleep_interval_seconds
        self._partial_ds_ok = partial_ds_ok

    def visit_ResultTTree(self, node):
        'Send a query to the remote node. Then hang out until something we can work with shows up.'

        # Pickle up the ast and send in the request.
        ast_data = pickle.dumps(node)

        # Repeat until we get a good-enough answer.
        while True:
            r = requests.post(f'{self._node}/query',
                headers={"content-type": "application/octet-stream"},
                data=ast_data)

            # TODO: properly handle errors
            dr = r.json()

            if dr['done'] or (self._partial_ds_ok and len(dr['files']) > 0):
                return {'files': dr['files']}
            if self._sleep_time > 0:
                time.sleep(self._sleep_time)

def use_exe_func_adl_server(a: ast.AST, node='http://localhost:30000', sleep_interval = 5, wait_for_finished=True):
    r'''
    Run a query against a func-adl server backend. The appropriate part of the AST is shipped there, and it is interpreted.

    Arguments:

        a:                  The ast that we should evaluate
        node:               The remote node/port combo where we can make the query. Defaults to the local thing.
        sleep_interval:     How many seconds to wait between queries to the server when the data isn't yet ready
        wait_for_finished:  If true will wait until the dataset has been fully processed. Otherwise will
                            come back without a complete dataset just fine, as long as a least one file is done.

    Returns:
        A dictionary with the following keys:
        'files'          A list of files that contain the requested data. These are either local
                         or they are availible via xrootd (they will be file:// or root://). 
    '''

    # The func-adl server can only deal with certian types of queries. So we need to
    # make sure we only send those. Do that by walking the nodes.
    r = walk_ast(node, sleep_interval, partial_ds_ok=not wait_for_finished).visit(a)
    return r