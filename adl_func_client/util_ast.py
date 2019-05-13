# Some ast utils
import ast

# TODO: lambda_unwrap should only be used in the parse_ast code, no where else - we shoudl be moving
# Lambda ASTs around, not Module AST's.
def lambda_unwrap(l):
    '''Given an AST of a lambda node, return the lambda node. If it is burried in a module, then unwrap it first
    Python, when it parses an module, returns the lambda wrapped in a `Module` AST node. This gets rid of it, but
    is also flexible.

    Args:
        l:      Lambda AST. It may be wrapped in a module as well.

    Returns:
        `Lambda` AST node, regardless of how the `Lambda` was wrapped in `l`.

    Exceptions:
        If the AST node isn't a lambda or a module wrapping a labmda.
    '''
    lb = l.body[0].value if type(l) is ast.Module else l
    if type(lb) is not ast.Lambda:
        raise BaseException('Attempt to get lambda expression body from {0}, which is not a lambda.'.format(type(l)))

    return lb

def lambda_args(l):
    'Return the arguments of a lambda, no matter what form the lambda is in.'
    return lambda_unwrap(l).args

def lambda_body(l):
    '''
    Given an AST lambda node, get the expression it uses and return it. This just makes life easier,
    no real logic is occuring here.
    '''
    return lambda_unwrap(l).body

def lambda_call(args, l):
    '''
    Create a `Call` AST that calls a lambda with the named args.

    Args:
        args:       a single string or a list of strings, each string is an argument name to be passed in.
        l:          The lambda we want to call.

    Returns:
        A `Call` AST that calls the labmda with the given arguments.
    '''
    if type(args) is str:
        args = [args]
    named_args = [ast.Name(x, ast.Load()) for x in args]
    return ast.Call(lambda_unwrap(l), named_args, [])

def lambda_build(args, l_expr):
    '''
    Given a named argument(s), and an expression, build a `Lambda` AST node.

    Args:
        args:       the string names of the arguments to the lambda. May be a list or a single name
        l_expr:     An AST node that is the body of the lambda.

    Returns:
        The `Lambda` AST node.
    '''
    if type(args) is str:
        args = [args]

    ast_args = ast.arguments(args=[ast.arg(arg=x) for x in args])
    call_lambda = ast.Lambda(args=ast_args, body=l_expr)

    return call_lambda

def lambda_body_replace(l, new_expr):
    '''
    Return a new lambda function that has new_expr as the body rather than the old one. Otherwise, everything is the same.

    Args:
        l:          A ast.Lambda or ast.Module that points to a lambda.
        new_expr:   Expression that should replace this one.

    Returns:
        new_l: New lambda that looks just like the old one, other than the expression is new. If the old one was an ast.Module, so will this one be.
    '''
    if type(l) is not ast.Lambda:
        raise BaseException('Attempt to get lambda expression body from {0}, which is not a lambda.'.format(type(l)))

    new_l = ast.Lambda(l.args, new_expr)
    return new_l

def lambda_assure(east, nargs=None):
    r'''
    Make sure the Python expression ast is a lambda call, and that it has the right number of args.

    Args:
        east:        python expression ast (module ast)
        nargs:      number of args it is required to have. If None, no check is done.
    '''
    if not lambda_test(east, nargs):
        raise BaseException(
            'Expression AST is not a lambda function with the right number of arguments')

    return east

def lambda_is_identity(l):
    'Return true if this is a lambda with 1 argument that returns the argument'
    if not lambda_test(l, 1):
        return False
    
    b = lambda_unwrap(l)
    if type(b.body) is not ast.Name:
        return False
    
    a = b.args.args[0].arg
    return a == b.body.id

def lambda_is_true(l):
    'Return true if this lambda always returns true'
    if not lambda_test(l):
        return False
    rl = lambda_unwrap(l)
    if type(rl.body) is not ast.NameConstant:
        return False

    return rl.body.value == True
    
def lambda_test(l, nargs = None):
    r''' Test arguments
    '''
    if type(l) is not ast.Lambda:
        if type(l) is not ast.Module:
            return False
        if len(l.body) != 1:
            return False
        if type (l.body[0]) is not ast.Expr:
            return False
        if type(l.body[0].value) is not ast.Lambda:
            return False
    rl = lambda_unwrap(l) if type(l) is ast.Module else l
    if type(rl) is not ast.Lambda:
        return False
    if nargs == None:
        return True
    return len(lambda_unwrap(l).args.args) == nargs
