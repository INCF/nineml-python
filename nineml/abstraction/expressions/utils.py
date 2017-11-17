"""
This module defines the namespace of functions and symbols available to 9ML
expressions.

:copyright: Copyright 2010-2017 by the NineML Python team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

import re
import numpy
from .base import reserved_identifiers


def is_single_symbol(expr):
    """Returns ``True`` if the expression is a single symbol, possibly
    surrounded with white-spaces

    >>> is_single_symbol('hello')
    True

    >>> is_single_symbol('hello * world')
    False

    """
    expr = expr.strip()
    single_symbol = re.compile("^[a-zA-Z_]+[a-zA-Z_0-9]*$")
    m = single_symbol.match(expr)
    return m is not None

str_to_npfunc_map = {
    "exp": numpy.exp,
    "sqrt": numpy.sqrt,
    "sin": numpy.sin,
    "cos": numpy.cos,
    "atan2": numpy.arctan2,
    "log": numpy.log,
    "pi": numpy.pi,
    "e": numpy.e
}


def str_expr_replacement(frm, to, expr_string, func_ok=False):
    """ replaces all occurences of name 'frm' with 'to' in expr_string
    ('frm' may not occur as a function name on the rhs) ...
    'to' can be an arbitrary string so this function can also be used for
    argument substitution.

    This function *will* substitute standard builtin symbols, for example
    ``e`` and ``sin``.

    Returns the resulting string. """

    # Escape the original string, so we can handle special
    # characters.
    frm = re.escape(frm)

    # do replace using regex this matches names, using lookahead and
    # lookbehind to be sure we don't match for example 'xp' in name 'exp'
    # ...
    if func_ok:
        # func_ok indicates we may replace a function name
        p_func = re.compile(r"(?<![a-zA-Z_0-9])(%s)(?![a-zA-Z_0-9])" % frm)
    else:
        # this will not replace a function name even if its name matches
        # from due to the lookahead disallowing '('
        p_func = re.compile(r"(?<![a-zA-Z_0-9])(%s)(?![(a-zA-Z_0-9])" %
                            frm)
    return p_func.sub(to, expr_string)


def is_builtin_symbol(sym):
    return sym in reserved_identifiers


def is_valid_lhs_target(sym):
    return sym not in reserved_identifiers
