import os
from operator import and_
from .base import BaseNineMLObject
from nineml.xml import (
    E, ALL_NINEML, unprocessed_xml, get_xml_attr, extract_xmlns, NINEMLv1)
from nineml.annotations import annotate_xml, read_annotations
from nineml.exceptions import NineMLRuntimeError, NineMLXMLAttributeError
from nineml.document import Document


class BaseReference(BaseNineMLObject):

    """
    Base class for references to model components that are defined in the
    abstraction layer.
    """

    def __init__(self, name, document=None, url=None):
        super(BaseReference, self).__init__()
        if document is None:
            document = Document()
        self._url = url
        if self.url:
            if document.url is None or not os.path.dirname(document.url):
                rel_dir = os.getcwd()
            else:
                rel_dir = os.path.dirname(document.url)
            document = read(url, relative_to=rel_dir)
        self._referred_to = document[name]

    @property
    def url(self):
        return self._url

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return reduce(and_, (self._referred_to == other._referred_to,
                             self.url == other.url))

    def __hash__(self):
        return (hash(self.__class__) ^ hash(self._referred_to.name) ^
                hash(self.url))

    def __repr__(self):
            return ('{}(name="{}"{})'
                    .format(self.__class__.__name__, self._referred_to.name,
                            ' in "{}"'.format(self.url) if self.url else ''))

    def to_xml(self, document, E=E, **kwargs):  # @UnusedVariable
        name = self._referred_to.name
        if E._namespace == NINEMLv1:
            attrs = {}
            body = [name]
        else:
            attrs = {'name': name}
            body = []
        if self.url:
            attrs['url'] = self.url
        element = E(self.element_name, *body, **attrs)
        return element

    @classmethod
    @read_annotations
    @unprocessed_xml
    def from_xml(cls, element, document, **kwargs):  # @UnusedVariable
        xmlns = extract_xmlns(element.tag)
        if xmlns == NINEMLv1:
            name = element.text
            if name is None:
                raise NineMLXMLAttributeError(
                    "References require the element name provided in the XML "
                    "element text")
        else:
            name = get_xml_attr(element, 'name', document, **kwargs)
        url = get_xml_attr(element, 'url', document, default=None, **kwargs)
        return cls(name=name, document=document, url=url)


class Reference(BaseReference):
    """
    A reference to a NineML user layer object previously defined or defined
    elsewhere.

    **Arguments**:
        *name*
            The name of a NineML object which already exists, or which is
            defined in a separate XML file.
        *document*
            A dictionary or :class:`Document` object containing the object
            being referred to, if the object already exists.
        *url*
            If the object is defined in a separate XML file, the URL
            of the file.

    """
    element_name = "Reference"

    def __init__(self, name, document=None, url=None):
        """
        docstring needed

        `name`     -- a name of an existing component_class to refer to
        `document` -- a Document object containing the top-level
                      objects in the current file
        `url`      -- a url of the file containing the exiting component_class
        """
        super(Reference, self).__init__(name, document, url)
        try:
            self._referred_to.from_reference = self
        except AttributeError:
            NineMLRuntimeError(
                "Reference points to a non-user-layer object '{}'"
                .format(self._referred_to.name))

    @property
    def user_object(self):
        """The object being referred to."""
        return self._referred_to

    @annotate_xml
    def to_xml(self, document, E=E, **kwargs):
        return super(Reference, self).to_xml(document, E=E, **kwargs)


def resolve_reference(from_xml):
    def resolving_from_xml(cls, element, document, **kwargs):  # @UnusedVariable @IgnorePep8
        if element.tag in (ns + Reference.element_name for ns in ALL_NINEML):
            reference = Reference.from_xml(element, document)
            ul_object = reference.user_object
        else:
            ul_object = from_xml(cls, element, document)
        return ul_object
    return resolving_from_xml


def write_reference(to_xml):
    def unresolving_to_xml(self, document, as_reference=True, **kwargs):
        if self.from_reference is not None and as_reference:
            xml = self.from_reference.to_xml(document, **kwargs)
        else:
            xml = to_xml(self, document, **kwargs)
        return xml
    return unresolving_to_xml


from .document import read
