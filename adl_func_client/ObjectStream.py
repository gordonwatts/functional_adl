# An Object stream represents a stream of objects, floats, integers, etc.
import adl_func_client.query_ast as query_ast
from adl_func_client.query_result_asts import ResultTTree, ResultAwkwardArray, ResultPandasDF
from adl_func_client.util_ast_LINQ import parse_as_ast
# import ast
from typing import Any


class ObjectStream:
    r'''
    Represents the AST to produce a stream of objects. The objects can be events,
    jets, electrons, or just floats, or arrays of floats.

    `ObjectStream` holds onto the AST that will produce this stream of objects.
    '''
    def __init__(self, the_ast):
        r"""
        Initialize the stream with the ast that will produce this stream of objects.
        The user will almost never use this initializer.
        """
        self._ast = the_ast

    def SelectMany(self, func):
        r"""
        Given the current stream's object type is an array or other iterable, return
        the items in this objects type, one-by-one. This has the effect of flattening a
        nested array.

        Args:
            func:   The function that should be applied to this stream's objects to return
                    an iterable. Each item of the iterable is now the stream of objects.                

        Returns:
            A new ObjectStream.
        """
        return ObjectStream(query_ast.SelectMany(self._ast, parse_as_ast(func)))

    def Select(self, f):
        r"""
        Apply a transformation function to each object in the stream, yielding a new type of
        object.

        Args:
            f:      selection function (lambda)

        Returns:
            A new ObjectStream of the transformed elements.
        """
        return ObjectStream(query_ast.Select(self._ast, parse_as_ast(f)))

    def Where(self, filter):
        r'''
        Filter the object stream, allowing only items for which `filter` evaluates as try through.

        Args:
            filter:     A filter lambda that returns True/False.

        Returns:
            A new ObjectStream that contains only elements that pass the filter function
        '''
        return ObjectStream(query_ast.Where(self._ast, parse_as_ast(filter)))

    def AsPandasDF(self, columns=[]):
        r"""
        Return a pandas dataframe. We do this by running the conversion.

        columns - Array of names of the columns. Will default to "col0", "call1", etc.
        """

        # We do this by first generating a simple ROOT file, then loading it into a dataframe with
        # uproot.
        return ObjectStream(ResultPandasDF(self._ast, columns))

    def AsROOTTTree(self, filename, treename, columns=[]):
        r"""
        Return the sequence of items as a ROOT TTree. Each item in the ObjectStream
        will get one entry in the file. The items must be of types that the infrastructure
        can work with:
            Float:              A tree with a single float in each entry will be written.
            vector<float>:      A tree with a list of floats in each entry will be written.
            (<tuple>):          A tree with multiple items (leaves) will be written. Each leaf
                                must have one of the above types. Nested tuples are not supported.

        Args:
            filename:       Name of the file in which a TTree of the objects will be written.
            treename:       Name of the tree to be written to the file
            columns:        Array of names of the columns. This must match the number of items
                            in a tuple to be written out.

        Returns:
            A new ObjectStream with type [(filename, treename)]. This is because multiple tree's
            may be written by the back end, and need to be concatenated together to get the full
            dataset.
        """
        return ObjectStream(ResultTTree(self._ast, columns, treename, filename))

    def AsAwkwardArray(self, columns=[]):
        r'''
        Terminal - take the AST and return a root file.

        columns - Array of names of the columns
        '''
        return ObjectStream(ResultAwkwardArray(self._ast, columns))

    def value(self, executor = None) -> Any:
        r"""
        Trigger the evaluation of the AST. Returns the results of the execution to the caller.

        Args:
            executor:       A function that when called with the ast will return the result. If
                            None, then use the default executor.

        Returns:
            Whatever the executor evaluates to.
        """
        # See if we are given an executor
        if executor is not None:
            return executor(self._ast)


        # By default we use the in-process docker executor which is, relatively speaking
        # portable as long as you have docker installed.
        from adl_func_backend.xAODlib.atlas_xaod_executor import use_executor_xaod_docker
        return use_executor_xaod_docker(self._ast)