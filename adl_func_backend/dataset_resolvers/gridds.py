# Python code to help with working with a grid dataset
# that should be downloaded locally to be run on.False
import ast
from adl_func_client.event_dataset import EventDataset
from urllib import parse
import os
import errno
from typing import List, Optional
import requests
from time import sleep
from adl_func_backend.xAODlib.exe_atlas_xaod_docker import use_executor_xaod_docker
import asyncio

# Resolvers:
def resolve_file(parsed_url, url:str):
    if len(parsed_url.netloc) != 0:
        raise FileNotFoundError(errno.ENOENT, f'Unable to find files that are remote: {parsed_url.netloc} and path {parsed_url.path}.')
    l = parsed_url.path[1:]
    if not os.path.exists(l):
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), l)
    return [url]

def resolve_localds(parsed_url, url:str):
    ds = parsed_url.netloc
    r = requests.post(f'http://localhost:8000/ds?ds_name={ds}')
    result = r.json()
    if result['status'] is 'downloading':
        return None
    if result['status'] is 'does_not_exist':
        raise GridDsException(f'Dataset {url} does not exist and cannot be downloaded locally.')

    # Turn these into file url's, relative to the file location returned.
    return [f for f in result['filelist']]

# We use this here so we can mock things for testing
resolve_callbacks = {
    'file': resolve_file,
    'localds': resolve_localds
}

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

    # Run resolver callbacks.
    if parsed.scheme in resolve_callbacks:
        return resolve_callbacks[parsed.scheme](parsed, url)

    # If we are here, then we don't know what to do.
    raise GridDsException(f'Do not know how to resolve dataset of type {parsed.scheme} from url {url}.')
    

class dataset_finder (ast.NodeTransformer):
    'Any event datasets are resolved to be local.'
    def __init__ (self):
        'Dataset Locally Resolved becomes true only if all datasets are local.'
        self.DatasetsLocallyResolves = False
    def visit_EventDataset(self, node: EventDataset):
        '''
        Look at the URL's for the event dataset. Try to replace them with
        files that have been downloaded locally, if we can.
        '''
        # Resolve all the url's
        resolved_urls = [resolve_local_ds_url(u) for u in node.url]

        # If any None's, then we aren't ready to go.
        if any(u is None for u in resolved_urls):
            return node

        u_list = [u for ulist in resolved_urls for u in ulist]
        if len(u_list) == 0:
            raise GridDsException(f'Resolving the dataset urls {node.url} gave the empty list of files')

        # All good! Create a new event dataset!
        self.DatasetsLocallyResolves = True
        return EventDataset(u_list)

async def use_executor_dataset_resolver(a: ast.AST, chained_executor=use_executor_xaod_docker):
    'Run - keep re-doing query until we crash or we can run'
    finder = dataset_finder()
    am = None
    while not finder.DatasetsLocallyResolves:
        am = finder.visit(a)
        if finder.DatasetsLocallyResolves:
            break
        await asyncio.sleep(5*60)
    
    # Ok, we have a modified AST and we can now get it processed.
    if am is None:
        raise BaseException("internal programming error - resolved AST should not be null")
    return await chained_executor(am)
