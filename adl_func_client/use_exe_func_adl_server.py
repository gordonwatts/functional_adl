# Code to support running an ast at a remote func-adl server.
import ast
import requests
import pickle
import time
import uproot
import pandas as pd
import numpy as np
from adl_func_client.query_result_asts import ResultPandasDF, ResultTTree, ResultAwkwardArray

class walk_ast(ast.NodeTransformer):
    'Walk the AST, replace the ROOT lookup node by something we know how to deal with.'
    def __init__(self, node:ast.AST, sleep_interval_seconds:int, partial_ds_ok:bool):
        'Set the node were we can go pick up the data'
        self._node = node
        self._sleep_time = sleep_interval_seconds
        self._partial_ds_ok = partial_ds_ok

    def visit_ResultTTree(self, node: ResultTTree):
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

    def _load_df (self, f_name, t_name):
        data_file = uproot.open(f_name)
        df_new = data_file[t_name].pandas.df()
        data_file._context.source.close()
        return df_new

    def _load_awkward (self, f_name, t_name):
        data_file = uproot.open(f_name)
        df_new = data_file[t_name].arrays()
        data_file._context.source.close()
        return df_new

    def visit_ResultPandasDF (self, node: ResultPandasDF):
        r'''
        Our backend only does root-tuples. So we will open them and load them into a DF. By whatever
        method they are fetched, we don't care. As long as they show up here in the same form as ResultTTree above.False

        Arguments:
            node:               The AST node represending the request for the pandas dataframe

        Returns:
            df:                 The data frame, ready to go, with all events loaded.
        '''
        # Build the root ttree result so we can get a list of files, and
        # render it.
        a_root = ResultTTree(node.source,
            node.column_names,
            'pandas_tree',
            'output.root')

        files = self.visit(a_root)
        if not isinstance(files, dict) or "files" not in files:
            raise BaseException(f"Fetch of data for conversion to pandas cameback in a format we don't know: {files}.")

        # Now, open them, one by one.
        frames = [self._load_df(f_name, t_name) for f_name,t_name in files['files']]
        if len(frames) == 1:
            return frames[0]
        else:
            return pd.concat(frames)

    def visit_ResultAwkwardArray (self, node: ResultAwkwardArray):
        r'''
        Our backend only does root-tuples. So we will open them and load them into a awkward array. By whatever
        method they are fetched, we don't care. As long as they show up here in the same form as ResultTTree above.False

        Arguments:
            node:               The AST node represending the request for the pandas dataframe

        Returns:
            df:                 The data frame, ready to go, with all events loaded.
        '''
        # Build the root ttree result so we can get a list of files, and
        # render it.
        a_root = ResultTTree(node.source,
            node.column_names,
            'pandas_tree',
            'output.root')

        files = self.visit(a_root)
        if not isinstance(files, dict) or "files" not in files:
            raise BaseException(f"Fetch of data for conversion to pandas cameback in a format we don't know: {files}.")

        # Now, open them, one by one.
        frames = [self._load_awkward(f_name, t_name) for f_name,t_name in files['files']]
        if len(frames) == 1:
            return frames[0]
        else:
            col_names = frames[0].keys()
            return {c: np.concatenate([ar[c] for ar in frames]) for c in col_names}

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