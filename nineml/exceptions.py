"""
Exceptions specific to the 9ML library

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""


def handle_xml_exceptions(from_xml):
    def from_xml_with_exception_handling(cls, element, *args, **kwargs):  # @UnusedVariable @IgnorePep8
        try:
            return from_xml(cls, element, *args, **kwargs)
        except KeyError, e:
            raise NineMLXMLAttributeError(
                "{} XML element{} is missing a {} attribute (found '{}')"
                .format(
                    cls.element_name,
                    (" '" + element.attrib['name'] + "'"
                     if 'name' in element.attrib else ''),
                    e, "', '".join(element.attrib.iterkeys())))
    return from_xml_with_exception_handling


class NineMLRuntimeError(Exception):
    pass


class NineMLDimensionError(NineMLRuntimeError):
    pass


class NineMLMathParseError(ValueError):
    pass


class NineMLUnitMismatchError(ValueError):
    pass


class NineMLMissingElementError(KeyError):
    pass


class NineMLInvalidElementTypeException(TypeError):
    pass


class NineMLImmutableError(NineMLRuntimeError):
    pass


class NineMLXMLAttributeError(KeyError):
    pass


def internal_error(s):
    assert False, 'INTERNAL ERROR:' + s


def raise_exception(exception=None):
    if exception:
        if isinstance(exception, basestring):
            raise NineMLRuntimeError(exception)
        else:
            raise exception
    else:
        raise NineMLRuntimeError()
