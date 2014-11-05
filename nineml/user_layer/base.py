from itertools import chain
from operator import and_
from .. import NINEML, nineml_namespace, E  # @UnusedImport


class BaseULObject(object):

    """
    Base class for user layer classes
    """
    children = []

    def __init__(self):
        self._from_reference = None

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

    def set_reference(self, reference):
        self._from_reference = reference

    def to_xml(self):
        if self._from_reference:
            xml = self._from_reference.to_xml()
        else:
            xml = self._to_xml()
        return xml
