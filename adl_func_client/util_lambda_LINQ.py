# Helpers for LINQ operators and lambda
import adl_func_client.query_ast as query_ast
import ast


def parse_as_ast (ast_source):
    r'''Return an AST for a lambda function from several sources.
    
    We are handed one of several things:
        - An AST that is a lambda function
        - An AST that is a pointer to a Module that wraps an AST
        - Text that contains properly formatted ast code for a lambda function.

    In all cases, return a lambda function as an AST starting from the AST top node,
    and one where calls to Select, SelectMany, etc., have been replaced with proper
    AST nodes.

    Args:
        ast_source:     An AST or text string that represnets the lambda.

    Returns:
        An ast starting from the Lambda AST node. 
    '''
    a = ast.parse(ast_source.strip())
    return lambda_unwrap(replace_LINQ_operators().visit(a))

class replace_LINQ_operators(ast.NodeTransformer):
    r'''
    We are called on expressions that are parsed in-line, and when we see calls to things like Select, we replace them
    with the AST entries appropriate.

    ObjectStream has methods called Select and SelectMany. When they are called, they build up the AST tree. But they do that
    by creating Select and SelectMany, etc., ast nodes. When we parse a lambda passed as text, that does not happen. This
    NodeTransformer does that replacement in-place.
    '''

    def visit_Call(self, node):
        '''Look for LINQ type calls and make a replacement with the appropriate AST entry
        TODO: Make sure this is recursive properly!
        '''
        if type(node.func) is ast.Attribute:
            func_name =  node.func.attr
            if func_name == "Select":
                source = self.visit(node.func.value)
                selection = self.visit(node.args[0])
                return query_ast.Select(source, selection)
            elif func_name == "SelectMany":
                source = self.visit(node.func.value)
                selection = self.visit(node.args[0])
                return query_ast.SelectMany(source, selection)
            elif func_name == "Where":
                source = self.visit(node.func.value)
                filter = self.visit(node.args[0])
                return query_ast.Where(source, filter)
            elif func_name == "First":
                source = self.visit(node.func.value)
                return query_ast.First(source)
            # Fall through to process the inside in the next step.
        return self.generic_visit(node)
