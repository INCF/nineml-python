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

    def __init__(self, name, document, url=None):
        super(BaseReference, self).__init__()
        if url:
            if url.startswith('.'):
                if document is None:
                    raise NineMLRuntimeError(
                        "Must supply the document that is being referenced "
                        "from if definition is a relative URL string, '{}'"
                        .format(url))
                relative_to = os.path.dirname(document.url)
            else:
                relative_to = None
            remote_doc = read(url, relative_to=relative_to)
        else:
            remote_doc = document
        self._url = url
        self._referred_to = remote_doc[name]

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

    @property
    def user_object(self):
        """The object being referred to."""
        return self._referred_to


def resolve_reference(from_xml):
    def resolving_from_xml(cls, element, document, **kwargs):  # @UnusedVariable @IgnorePep8
        if element.tag in (ns + Reference.element_name for ns in ALL_NINEML):
            reference = Reference.from_xml(element, document)
            obj = reference.user_object
        else:
            obj = from_xml(cls, element, document)
        return obj
    return resolving_from_xml


def write_reference(to_xml):
    def unresolving_to_xml(self, document, as_ref=None, absolute_refs=False,
                           prefer_refs=False, **kwargs):
        # Determine whether to write the elemnt as a reference or not depending
        # on whether it needs to be, as determined by `as_ref`, e.g. in the
        # case of populations referenced from projections, or whether the user
        # would prefer it to be, `prefer_refs`. If neither kwarg is set whether
        # the element is written as a reference is determined by whether it
        # has already been added to a document or not.
        if (as_ref or prefer_refs) and self.document is None:
            # Add the object to the current document
            document.add(self)
            as_ref = True
        elif as_ref is None:
            as_ref = self.document is not None
        if as_ref:
            # If the object is already in the current document the url is None
            if self.document is document:
                url = None
            # Use the full ref if the `absolute_refs` kwarg is provided
            elif absolute_refs:
                url = self.document.url
            # Otherwise use the relative path, which is recommended as it makes
            # directories of files transportable
            else:
                url = os.path.relpath(self.document.url,
                                      os.path.dirname(document.url))
            # Write the element as a reference
            xml = Reference(self.name, document, url=url).to_xml(
                document, **kwargs)
        else:
            # Write the element inline. NB: This will effectively duplicate the
            # object in the saved xml if it is referred to in multiple places.
            # To avoid this from happening it is safer to avoid inline
            # definitions by setting the `prefer_refs` kwarg.
            xml = to_xml(self, document, absolute_refs=absolute_refs,
                         prefer_refs=prefer_refs, **kwargs)
        return xml
    return unresolving_to_xml


from .document import read
