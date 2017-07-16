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


class NineMLTargetMissingError(NineMLRuntimeError):
    pass


class NineMLXMLError(NineMLRuntimeError):
    pass


class NineMLSerializationError(NineMLRuntimeError):
    pass


class NineMLMissingSerializationError(NineMLSerializationError):
    pass


class NineMLSerializationNotSupportedError(NineMLRuntimeError):
    pass


class NineMLUnexpectedMultipleSerializationError(NineMLSerializationError):
    pass


class NineMLXMLTagError(NineMLXMLError):
    pass


class NineMLXMLAttributeError(NineMLXMLError):
    pass


class NineMLXMLBlockError(NineMLXMLError):
    pass


class NineMLNoSolutionException(NineMLException):
    pass


class NineMLIOError(NineMLRuntimeError):
    pass


class NineMLReloadDocumentException(NineMLException):
    pass


class NineMLStopVisitException(NineMLException):
    pass


class NineMLRandomDistributionDelayException(NineMLException):
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
            try:
                available = getattr(self, accessor.__name__ + '_names')
            except AttributeError:
                available = []
            raise NineMLNameError(
                "'{}' {} does not have {} named '{}' ('{}')"
                .format(self.key, self.nineml_type, type_name, name,
                        "', '".join(available)))
    return accessor_with_handling
