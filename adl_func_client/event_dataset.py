# Event dataset
from urllib import parse
from adl_func_client.ObjectStream import ObjectStream
import ast
from typing import Union, Iterable

class EventDatasetURLException (BaseException):
    '''
    Exception thrown if the URL passed is not valid
    '''
    def __init__ (self, message):
        BaseException.__init__(self, message)

def fixup_url(url:str, parsed_url) -> str:
    'Fix up the url if we need to normalize anything'
    if parsed_url.scheme != 'file':
        return url

    # For file, we need to deal with file://path and file:///path.
    # If netloc is something we can quickly recognize as a local path or empty, then this url is in good shape.
    if len(parsed_url.netloc) == 0 or parsed_url.netloc == 'localhost':
        return f'file://{parsed_url.path}'

    # Assume that netloc was part of the path.
    path = parsed_url.netloc
    if len(parsed_url.path) > 0:
        path = path + parsed_url.path
    return f'file:///{path}'

class EventDataset(ObjectStream, ast.AST):
    r'''
    The URL for an event dataset. 
    '''
    def __init__(self, url: Union[str, Iterable[str]]=None):
        r'''
        Create and hold an event dataset reference. From one file, to multiple files, to a
        dataset specified otherwise.

        Args:
            url (str):  Must be a valid URL that points to a valid dataset

        Raises:
            Invalid URL
        '''
        if url is not None:
            # Normalize the URL as a list
            if isinstance(url, str):
                url = [url]
            l_url = list(url)

            if len(l_url) == 0:
                raise EventDatasetURLException("EventDataset initialized with an empty URL")

            # Make sure we can parse this URL. We don't, at some level, care about the actual contents.
            r_list = [parse.urlparse(u) for u in l_url]
            for r in r_list:
                if r.scheme is None or len(r.scheme) == 0:
                    raise EventDatasetURLException(f'EventDataSet({l_url}) has no scheme (file://, localds://, etc.)')
                if (r.netloc is None or len(r.netloc) == 0) and len(r.path) == 0:
                    raise EventDatasetURLException(f'EventDataSet({l_url}) has no dataset or filename')
            self.url = [fixup_url(u, r) for u in l_url]
        else:
            self.url = url

        self._ast = self
        self._fields = ('url',)