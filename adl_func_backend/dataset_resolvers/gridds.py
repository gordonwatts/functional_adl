# Python code to help with working with a grid dataset
# that should be downloaded locally to be run on.False
import ast
from adl_func_client.event_dataset import EventDataset
from urllib import parse
import os
import errno
from typing import List, Optional
import requests

# We use this here so we can mock things for testing

class GridDsException (BaseException):
    'Thrown when an error occurs going after a grid dataset of some sort'
    def __init__(self, message):
        BaseException.__init__(self, message)

def resolve_local_ds_url(url: str) -> Optional[List[str]]:
    '''
    Given a url, check that it is either a local dataset request or a file.
    If it is a file, return it. If it is a local dataset, attempt to resolve it.
    Trigger a download if need be.

    Args:
        url:        The URL of the dataset

    Returns:
        None        We've asked for the file, but it isn't local yet.
        [urls]      List of URL's this translates to
    
    Exceptions:
        xxx                 The url scheme isn't `file` or `localds`
        FileNotFoundError   a url with "file" on it was not found on this machine.
        Other               For example, can't get a hold of desktop-rucio to do the download.
    '''
    parsed = parse.urlparse(url)

    # If it is a file, then this is pretty trivial.
    if parsed.scheme == 'file':
        l = f'{parsed.netloc}{parsed.path}'
        if not os.path.exists(l):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), l)
        return [url]

    # If it is a local dataset, try to resolve it.
    if parsed.scheme == 'localds':
        ds = parsed.netloc
        r = requests.post(f'http://localhost:8000/ds?ds_name={ds}')
        result = r.json()
        if result['status'] != 'local':
            return [url]
        return [f'file://{f}' for f in result['filelist']]

    # If we are here, then we don't know what to do.
    raise GridDsException(f'Do not know how to resolve dataset of type {parsed.scheme} from url {url}.')
    

def use_executor_dataset_resolver(a: ast.AST):
    class dataset_finder (ast.NodeTransformer):
        def visit_EventDataset(self, node: EventDataset):
            '''
            Look at the URL's for the event dataset. Try to replace them with
            files that have been downloaded locally, if we can.
            '''
    pass