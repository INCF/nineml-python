from lxml.builder import ElementMaker
from itertools import chain
from operator import and_
from copy import copy
from nineml.utility import expect_none_or_single

nineml_namespace = 'http://nineml.net/9ML/1.0'
NINEML = "{%s}" % nineml_namespace
E = ElementMaker(namespace=nineml_namespace,
                 nsmap={"nineml": nineml_namespace})


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

    def get_children(self):
        return chain(getattr(self, attr) for attr in self.children)

    def accept_visitor(self, visitor):
        visitor.visit(self)


class Annotations(dict):
    """
    Defines the dimension used for quantity units
    """

    element_name = 'Annotations'

    def __repr__(self):
        return ("Annotations({})"
                .format(', '.join('{}={}'.format(k, v)
                                  for k, v in self.iteritems())))

    def to_xml(self):
        return E(self.element_name,
                 *self.itervalues())

    @classmethod
    def from_xml(cls, element):
        children = {}
        for child in element.getchildren():
            children[child.tag] = child
        return cls(**children)


def read_annotations(from_xml):
    def annotate_from_xml(cls, element, *args, **kwargs):
        annot_elem = expect_none_or_single(element.findall(NINEML + 
                                                     Annotations.element_name))
        if annot_elem is not None:
            # Extract the annotations
            annotations = Annotations.from_xml(annot_elem)
            # Get a copy of the element with the annotations stripped
            element = copy(element)
            element.remove(element.find(NINEML + Annotations.element_name))
        else:
            annotations = None
        nineml_object = from_xml(cls, element, *args, **kwargs)
        try:
            nineml_object.annotations = annotations
        except AttributeError:
            raise
        return nineml_object
    return annotate_from_xml


def annotate_xml(to_xml):
    def annotate_to_xml(self, *args, **kwargs):
        elem = to_xml(self, *args, **kwargs)
        # If User Layer class
        if hasattr(self, 'annotations') and self.annotations is not None:
            elem.append(self.annotations.to_xml())
        # If Abstraction Layer class
        elif (len(args) and hasattr(args[0], 'annotations') and
              args[0].annotations is not None):
            elem.append(args[0].annotations.to_xml())
        return elem
    return annotate_to_xml

