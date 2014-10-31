from itertools import chain
from operator import and_
from lxml.builder import ElementMaker

nineml_namespace = 'http://nineml.net/9ML/1.0'
NINEML = "{%s}" % nineml_namespace

E = ElementMaker(namespace=nineml_namespace,
                 nsmap={"nineml": nineml_namespace})


class BaseULObject(object):

    """
    Base class for user layer classes
    """
    children = []

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
