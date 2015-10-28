"""
Exceptions specific to the 9ML library

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""


class NineMLRuntimeError(Exception):
    pass


class NineMLDimensionError(NineMLRuntimeError):
    pass


class NineMLMathParseError(ValueError, NineMLRuntimeError):
    pass


class NineMLUnitMismatchError(ValueError, NineMLRuntimeError):
    pass


class NineMLNamespaceError(KeyError, NineMLRuntimeError):
    pass


class NineMLNameError(KeyError, NineMLRuntimeError):
    pass


class NineMLInvalidElementTypeException(TypeError, NineMLRuntimeError):
    pass


class NineMLImmutableError(NineMLRuntimeError):
    pass


class NineMLXMLError(NineMLRuntimeError):
    pass


class NineMLXMLAttributeError(NineMLXMLError):
    pass


class NineMLXMLBlockError(NineMLXMLError):
    pass


def internal_error(s):
    assert False, 'INTERNAL ERROR:' + s


# FIXME: Not sure what this is used for TGC 16/10/2015
def raise_exception(exception=None):
    if exception:
        if isinstance(exception, basestring):
            raise NineMLRuntimeError(exception)
        else:
            raise exception
    else:
        raise NineMLRuntimeError()
