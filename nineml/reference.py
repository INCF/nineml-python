import os
from operator import and_
from . import BaseNineMLObject
from nineml.xmlns import NINEML, E
from nineml.annotations import annotate_xml, read_annotations


class BaseReference(BaseNineMLObject):

    """
    Base class for references to model components that are defined in the
    abstraction layer.
    """

    def __init__(self, name, document, url=None):
        super(BaseReference, self).__init__()
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
                    .format(self.__class__.__name__, self._referred_to.name,
                            ' in "{}"'.format(self.url) if self.url else ''))

    @annotate_xml
    def to_xml(self):
        kwargs = {'url': self.url} if self.url else {}
        element = E(self.element_name,
                    self._referred_to.name,
                    **kwargs)
        return element

    @classmethod
    @read_annotations
    def from_xml(cls, element, document):
        if element.tag != NINEML + cls.element_name:
            raise Exception("Expecting tag name %s%s, actual tag name %s" % (
                NINEML, cls.element_name, element.tag))
        name = element.text
        url = element.attrib.get("url", None)
        return cls(name, document, url)

from .document import read
