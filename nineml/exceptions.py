"""
Exceptions specific to the 9ML library

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""


class NineMLRuntimeError(Exception):
    pass


class NineMLDimensionError(NineMLRuntimeError):
    pass


class NineMLMathParseError(ValueError):
    pass


class NineMLUnitMismatchError(ValueError):
    pass


class NineMLNamespaceError(ValueError):
    pass


class NineMLMissingElementError(KeyError):
    pass


class NineMLInvalidElementTypeException(TypeError):
    pass


class NineMLImmutableError(NineMLRuntimeError):
    pass


class NineMLXMLAttributeError(NineMLRuntimeError):
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


def handle_xml_exceptions(from_xml):
    def from_xml_with_exception_handling(cls, element, *args, **kwargs):  # @UnusedVariable @IgnorePep8
        try:
            return from_xml(cls, element, *args, **kwargs)
        except KeyError, e:
            if isinstance(e, NineMLMissingElementError):
                raise
            try:
                element_name = cls.element_name  # UL classes
                url = args[0].url  # should be a Document class
            except AttributeError:
                # AL classes, relies on naming convention of load methods
                # to get the name of the element
                name_parts = from_xml.__name__[5:].split('_')
                element_name = ''.join(p.capitalize() for p in name_parts)
                url = cls.document.url
            raise NineMLXMLAttributeError(
                "{} XML element{} in '{}' is missing the {} attribute "
                "(found '{}' attributes)"
                .format(element_name,
                        (" '" + element.attrib['name'] + "'"
                         if 'name' in element.attrib else ''),
                        url, e, "', '".join(element.attrib.iterkeys())))
    return from_xml_with_exception_handling