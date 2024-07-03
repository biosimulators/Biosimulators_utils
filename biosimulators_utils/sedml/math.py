""" Data model for SED

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

import evalidate
import math
import mpmath
import numpy
import numpy.random

__all__ = [
    'log',
    'piecewise',
    'MATHEMATICAL_FUNCTIONS',
    'RESERVED_MATHEMATICAL_SYMBOLS',
    'AGGREGATE_MATH_FUNCTIONS',
    'VALID_MATH_EXPRESSION_NODES',
    'compile_math',
    'eval_math',
]


def log(*args):
    """ Evaluate a logarithm

    Args:
        *args (:obj:`list` of :obj:`float`): value optional proceeded by a base; otherwise the logarithm
            is calculated in base 10

    Returns:
        :obj:`float`
    """
    value = args[-1]
    if len(args) > 1:
        base = args[0]
    else:
        base = 10.

    return math.log(value, base)


def piecewise(*args):
    """ Evaluate a MathML piecewise function

    Args:
        *args (:obj:`list` of :obj:`float`): pairs of value and conditions followed by a default value

    Returns:
        :obj:`float`
    """
    if len(args) % 2 == 0:
        pieces = args
        otherwise = math.nan

    else:
        pieces = args[0:-1]
        otherwise = args[-1]

    for i_piece in range(0, len(pieces), 2):
        value = pieces[i_piece]
        condition = pieces[i_piece + 1]
        if condition:
            return value

    return otherwise


MATHEMATICAL_FUNCTIONS = {
    'root': lambda x, n: x**(1 / float(n)),
    'abs': abs,
    'exp': math.exp,
    'ln': math.log,
    'log': log,
    'floor': math.floor,
    'ceiling': math.ceil,
    'factorial': math.factorial,
    'sin': math.sin,
    'cos': math.cos,
    'tan': math.tan,
    'sec': mpmath.sec,
    'csc': mpmath.csc,
    'cot': mpmath.cot,
    'sinh': math.sinh,
    'cosh': math.cosh,
    'tanh': math.tanh,
    'sech': mpmath.sech,
    'csch': mpmath.csch,
    'coth': mpmath.coth,
    'arcsin': math.asin,
    'arccos': math.acos,
    'arctan': math.atan,
    'arcsec': mpmath.asec,
    'arccsc': mpmath.acsc,
    'arccot': mpmath.acot,
    'arcsinh': math.asinh,
    'arccosh': math.acosh,
    'arctanh': math.atanh,
    'arcsech': mpmath.asech,
    'arccsch': mpmath.acsch,
    'arccoth': mpmath.acoth,
    'min': numpy.min,
    'max': numpy.max,
    'sum': numpy.sum,
    'product': numpy.prod,
    'count': len,
    'mean': numpy.mean,
    'stdev': numpy.std,
    'variance': numpy.var,
    'uniform': numpy.random.uniform,
    'normal': numpy.random.normal,
    'lognormal': numpy.random.lognormal,
    'poisson': numpy.random.poisson,
    'gamma': numpy.random.gamma,
    'piecewise': piecewise,
}

RESERVED_MATHEMATICAL_SYMBOLS = {
    'true': True,
    'false': False,
    'notanumber': math.nan,
    'pi': math.pi,
    'infinity': math.inf,
    'exponentiale': math.e,
}

AGGREGATE_MATH_FUNCTIONS = (
    'min',
    'max',
    'sum',
    'product',
    'count',
    'mean',
    'stdev',
    'variance',
)


VALID_MATH_EXPRESSION_NODES = [
    'Eq',
    'NotEq',
    'Gt',
    'Lt',
    'GtE',
    'LtE',
    'Sub',
    'USub',
    'Mult',
    'Div',
    'Pow',
    'And',
    'Or',
    'Not',
    'BitAnd',
    'BitOr',
    'BitXor',
    'Call',
    'Constant',
]


def compile_math(math):
    """ Compile a mathematical expression

    Args:
        math (:obj:`str`): mathematical expression

    Returns:
        :obj:`_ast.Expression`: compiled expression
    """
    if isinstance(math, str):
        math = (
            math
            .replace('&&', 'and')
            .replace('||', 'or')
            .replace('^', '**')
        )

    model = evalidate.base_eval_model.clone()
    model.nodes.extend(VALID_MATH_EXPRESSION_NODES)
    model.allowed_functions.extend(MATHEMATICAL_FUNCTIONS.keys())

    math_node = evalidate.Expr(math, model=model)
    compiled_math = compile(math_node.node, '<math>', 'eval')
    return compiled_math


def eval_math(math, compiled_math, workspace):
    """ Compile a mathematical expression

    Args:
        math (:obj:`str`): mathematical expression
        compiled_math (:obj:`_ast.Expression`): compiled expression
        workspace (:obj:`dict`): values to use for the symbols in the expression

    Returns:
        :obj:`object`: result of the expression

    Raises:
        :obj:`ValueError`: if the expression could not be evaluated
    """
    invalid_symbols = set(RESERVED_MATHEMATICAL_SYMBOLS.keys()).intersection(set(workspace.keys()))
    if invalid_symbols:
        raise ValueError('Variables for mathematical expressions cannot have ids equal to the following reserved symbols:\n  - {}'.format(
            '\n  - '.join('`' + symbol + '`' for symbol in sorted(invalid_symbols))))

    try:
        return eval(compiled_math, MATHEMATICAL_FUNCTIONS, dict(**RESERVED_MATHEMATICAL_SYMBOLS, **workspace))
    except Exception as exception:
        raise ValueError('Expression `{}` could not be evaluated:\n\n  {}\n\n  workspace:\n    {}'.format(
            math, str(exception), '\n    '.join('{}: {}'.format(key, value) for key, value in workspace.items())))
