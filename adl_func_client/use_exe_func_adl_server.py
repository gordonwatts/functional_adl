# Code to support running an ast at a remote func-adl server.
import ast
import requests
import pickle
import os
import time
import uproot
import pandas as pd
import numpy as np
from adl_func_client.query_result_asts import ResultPandasDF, ResultTTree, ResultAwkwardArray
import urllib
import time
import asyncio
from retry import retry
import logging
from io import StringIO

class FuncADLServerException (BaseException):
    'Thrown when an exception happens contacting the server'
    def __init__(self, msg):
        BaseException.__init__(self, msg)

def _uri_exists(uri):
    'Look to see if a file:// uri exists'
    r = urllib.parse.urlparse(uri)
    if r.scheme != 'file':
        return False
    if os.path.exists(r.path):
        return True
    # Give a chance for a relative path.
    return os.path.exists(r.path[1:])

@retry(tries=10, delay=0.5)
def _make_request(node:str, ast_data):
    'Make the request from the end point'
    r = requests.post(f'{node}/query',
        headers={"content-type": "application/octet-stream"},
        data=ast_data)

    # Need to handle errors (see https://github.com/gordonwatts/functional_adl/issues/22).
    try:
        return r.json()
    except Exception as e:
        # Wrap the error in the full text if possible.
        raise FuncADLServerException(f'Error from server "{str(e)}" while parsing response "{r.text}"') from e

def _best_access(files):
    'Given a list of ways to a file, determine which one is best'
    for uri, t_name in files:
        r = urllib.parse.urlparse(uri)
        if r.scheme == 'file':
            if os.path.exists(r.path):
                return [uri, t_name]
            if os.path.exists(r.path[1:]):
                return [uri, t_name]
        else:
            # A different method of accessing besides a local file. Assume it is
            # awesome.
            return [uri, t_name]

class walk_ast(ast.NodeTransformer):
    'Walk the AST, replace the ROOT lookup node by something we know how to deal with.'
    def __init__(self, node:ast.AST, sleep_interval_seconds:int, partial_ds_ok:bool, quiet:bool):
        'Set the node were we can go pick up the data'
        self._node = node
        self._sleep_time = sleep_interval_seconds
        self._partial_ds_ok = partial_ds_ok
        self._quiet = quiet

    def extract_filespec(self, response: dict):
        'Given the dictionary of info that came back from the webservice, extract the proper set of files'

        # Get a list of the valid items we can load into uproot
        access_list = ['localfiles', 'files', 'httpfiles']
        if os.name == 'nt':
            # We can't do root:// easily on windows, so drop it.
            access_list = ['localfiles', 'httpfiles']
        access_list = [a for a in access_list if a in response]

        if len(access_list) == 0:
            raise FuncADLServerException(f'No viable data sources came back accessible on platform "{os.name}". The complete response from the server was {response}."')

        # Next, check for visibility of all of these things.
        pairs = zip(*[response[n] for n in access_list])
        r = [_best_access(fr) for fr in pairs]
        return r

    def visit_ResultTTree(self, node: ResultTTree):
        'Send a query to the remote node. Then hang out until something we can work with shows up.'

        # Pickle up the ast and send in the request.
        ast_data = pickle.dumps(node)

        # Repeat until we get a good-enough answer.
        phases = {}
        print_count = 0
        while True:
            dr = _make_request(self._node, ast_data)
            logging.info(f'returned info: {dr}')

            # Accumulate statistics
            p = dr['phase']
            if p in phases:
                phases[p] += 1
            else:
                phases[p] = 1

            # If we are done, return the information.
            if dr['done'] or (self._partial_ds_ok and len(dr['files']) > 0):
                if not self._quiet and len(phases) > 1:
                    # Report on how much time we spent waiting.
                    total = sum([phases[k] for k in phases.keys()])
                    print ('Where we spent time waiting for column data:')
                    for k in phases.keys():
                        print (f'  {k}: {phases[k]*100/total}%')

                if dr['phase'] != 'done':
                    # Yikes! Something bad happened. Try to assemble a error messages and blow up.
                    with StringIO() as s:
                        print('The request failed:', file=s)
                        if 'message' in dr:
                            print(f'  Message: {dr["message"]}', file=s)
                        if 'log' in dr:
                            print('  Log lines:', file=s)
                            for l in dr['log']:
                                print(f'    {l}', file=s)
                        raise FuncADLServerException(s.getvalue())

                r = {'files': self.extract_filespec(dr)}
                if not self._quiet:
                    print ('Files that were returned:')
                    for f in r['files']:
                        print (f'  {f}')
                
                return r

            # See if we should print
            if not self._quiet:
                if print_count == 0:
                    localtime = time.asctime( time.localtime(time.time()) )
                    print (f'{localtime} : Status: {dr["phase"]}')
                print_count = (print_count + 1) % 10

            # Wait a short amount of time before pinging again.
            if self._sleep_time > 0:
                time.sleep(self._sleep_time)

    def _clean_name(self, fname):
        'Clean up a name. Mostly dealing with URIs, uproot, and windows.'
        p = urllib.parse.urlparse(fname)
        if p.scheme != 'file':
            return fname
        if os.path.exists(p.path):
            return fname
        return f'file://{p.path[1:]}'

    def _load_df (self, f_name, t_name):
        data_file = uproot.open(self._clean_name(f_name))
        df_new = data_file[t_name].pandas.df()
        data_file._context.source.close()
        return df_new

    def _load_awkward (self, f_name, t_name):
        data_file = uproot.open(self._clean_name(f_name))
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
        # Build the root TTree result so we can get a list of files, and
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
        # Build the root TTree result so we can get a list of files, and
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

async def use_exe_func_adl_server(a: ast.AST,
        node='http://localhost:30000',
        sleep_interval = 5,
        wait_for_finished=True,
        quiet=True):
    r'''
    Run a query against a func-adl server backend. The appropriate part of the AST is shipped there, and it is interpreted.

    Arguments:

        a:                  The ast that we should evaluate
        node:               The remote node/port combo where we can make the query. Defaults to the local thing.
        sleep_interval:     How many seconds to wait between queries to the server when the data isn't yet ready
        wait_for_finished:  If true will wait until the dataset has been fully processed. Otherwise will
                            come back without a complete dataset just fine, as long as a least one file is done.
        quiet               If true, run with as little output as possible.

    Returns:
        A dictionary with the following keys:
        'files'          A list of files that contain the requested data. These are either local
                         or they are availible via xrootd (they will be file:// or root://). 
    '''

    # The func-adl server can only deal with certian types of queries. So we need to
    # make sure we only send those. Do that by walking the nodes.
    # This is syncrhonous code, unfortunately, so we have to have it running 
    # in another thread to make this async (there is no way to fix this since the NodeVisitor
    # class is totally synchronous).
    walker = walk_ast(node, sleep_interval, partial_ds_ok=not wait_for_finished, quiet=quiet)
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, walker.visit, a)

    # r = walk_ast(node, sleep_interval, partial_ds_ok=not wait_for_finished, quiet=quiet).visit(a)
    # return r
