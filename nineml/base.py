from itertools import chain
from operator import and_
from . import NINEML, nineml_namespace, E  # @UnusedImport
from .annotations import Annotations


class BaseNineMLObject(object):

    """
    Base class for user layer classes
    """
    children = []

    def __init__(self):
        self.annotations = None

    def __eq__(self, other):
        return reduce(and_, [isinstance(other, self.__class__)] +
                            [getattr(self, name) == getattr(other, name)
                             for name in self.__class__.defining_attributes])

    def __ne__(self, other):
        return not self == other

    def __lt__(self, other):
        if self.__class__.__name__ < other.__class__.__name__:
            return True
        else:
            return self.name < other.name

    def get_children(self):
        if hasattr(self, "children"):
            return chain(getattr(self, attr) for attr in self.children)
        else:
            return []

    def accept_visitor(self, visitor):
        visitor.visit(self)


def read_annotations(from_xml):
    def annotate_from_xml(cls, element, context):
        nineml_object = from_xml(cls, element, context)
        annot_elem = element.find(NINEML + Annotations.element_name)
        if annot_elem is not None:
            nineml_object.annotations = Annotations.from_xml(element, context)
        return nineml_object
    return annotate_from_xml


def annotate_xml(to_xml):
    def annotate_to_xml(self):
        elem = to_xml(self)
        if self._annotations is not None:
            elem.append(self.annotations.to_xml())
        return elem
    return annotate_to_xml
