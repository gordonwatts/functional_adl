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
            url = list(url)

            if len(url) == 0:
                raise EventDatasetURLException("EventDataset initialized with an empty URL")

            # Make sure we can parse this URL. We don't, at some level, care about the actual contents.
            r_list = [parse.urlparse(u) for u in url]
            for r in r_list:
                if r.scheme is None or len(r.scheme) == 0:
                    raise EventDatasetURLException(f'EventDataSet({url}) has no scheme (file://, localds://, etc.)')
                if r.netloc is None or len(r.netloc) == 0:
                    raise EventDatasetURLException(f'EventDataSet({url}) has no dataset or filename')

        self.url = url
        self._ast = self
        self._fields = ('url',)