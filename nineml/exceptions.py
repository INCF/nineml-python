"""
Exceptions specific to the 9ML library

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""


class NineMLException(Exception):
    pass


class NineMLRuntimeError(NineMLException):
    pass


class NineMLDimensionError(NineMLRuntimeError):
    pass


class NineMLMathParseError(ValueError, NineMLRuntimeError):
    pass


class NineMLUnitMismatchError(ValueError, NineMLRuntimeError):
    pass


class NineMLNameError(KeyError, NineMLRuntimeError):
    pass


class NineMLValueError(ValueError, NineMLRuntimeError):
    pass


class NineMLTypeError(TypeError, NineMLRuntimeError):
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


class NineMLNoSolutionException(NineMLException):
    pass


def internal_error(s):
    assert False, 'INTERNAL ERROR:' + s


def name_error(accessor):
    def accessor_with_handling(self, name):
        try:
            return accessor(self, name)
        except KeyError:
            # Get the name of the element type to be accessed making use of a
            # strict naming convention of the accessors
            type_name = ''.join(p.capitalize()
                                for p in accessor.__name__.split('_'))
            raise NineMLNameError(
                "'{}' {} does not have {} named '{}"
                .format(self._name, self.nineml_type, type_name, name))
    return accessor_with_handling
