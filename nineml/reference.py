import os
from operator import and_
from . import BaseNineMLObject
from nineml.xmlns import NINEML, E
from nineml.annotations import annotate_xml, read_annotations
from nineml.exceptions import handle_xml_exceptions, NineMLRuntimeError
from nineml.user import BaseULObject
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
        self.url = url
        if self.url:
            if document.url is None:
                document = read(url, relative_to=os.getcwd())
            else:
                document = read(url, relative_to=os.path.dirname(document.url))
        self._referred_to = document[name]

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return reduce(and_, (self._referred_to == other._referred_to,
                             self.url == other.url))

    def __hash__(self):
        return (hash(self.__class__) ^ hash(self.component_name) ^
                hash(self.url))

    def __repr__(self):
            return ('{}(name="{}"{})'
                    .format(self.__class__.__name__,
                            (self._referred_to.name if self._referred_to
                             else ''),
                            ' in "{}"'.format(self.url) if self.url else ''))

    @annotate_xml
    def to_xml(self, **kwargs):  # @UnusedVariable
        kwargs = {'name': self._referred_to.name}
        if self.url:
            kwargs['url'] = self.url
        element = E(self.element_name, **kwargs)
        return element

    @classmethod
    @read_annotations
    @handle_xml_exceptions
    def from_xml(cls, element, document, **kwargs):  # @UnusedVariable
        if element.tag != NINEML + cls.element_name:
            raise Exception("Expecting tag name %s%s, actual tag name %s" % (
                NINEML, cls.element_name, element.tag))
        try:
            name = element.attrib["name"]
        except KeyError:
            raise
        url = element.attrib.get("url", None)
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
        if not isinstance(self._referred_to, BaseULObject):
            msg = ("Reference points to a non-user-layer object '{}'"
                   .format(self._referred_to.name))
            raise NineMLRuntimeError(msg)
        self._referred_to.from_reference = self

    @property
    def user_object(self):
        """The object being referred to."""
        return self._referred_to


class Definition(BaseReference):

    """
    Base class for model components that are defined in the abstraction layer.
    """
    element_name = "Definition"

    @property
    def component_class(self):
        return self._referred_to


class Prototype(BaseReference):

    element_name = "Prototype"

    @property
    def component(self):
        return self._referred_to


def resolve_reference(from_xml):
    def resolving_from_xml(cls, element, document, **kwargs):  # @UnusedVariable
        if element.tag == NINEML + Reference.element_name:
            reference = Reference.from_xml(element, document)
            ul_object = reference.user_object
        else:
            cls.check_tag(element)
            ul_object = from_xml(cls, element, document)
        return ul_object
    return resolving_from_xml


def write_reference(to_xml):
    def unresolving_to_xml(self, as_reference=True):
        if self.from_reference is not None and as_reference:
            xml = self.from_reference.to_xml()
        else:
            xml = to_xml(self)
        return xml
    return unresolving_to_xml


from .document import read
