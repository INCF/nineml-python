from ..base import BaseNineMLObject, NINEML
from ..context import BaseReference
from ..exceptions import NineMLRuntimeError


class BaseULObject(BaseNineMLObject):

    """
    Base class for user layer classes
    """

    def __init__(self):
        super(BaseULObject, self).__init__()
        self._from_reference = None

    def __lt__(self, other):
        if self.__class__.__name__ < other.__class__.__name__:
            return True
        else:
            return self.name < other.name

#     def set_reference(self, reference):
#         self._from_reference = reference
#
#     def to_xml(self, as_reference=True):
#         if self._from_reference and as_reference:
#             xml = self._from_reference.to_xml()
#         else:
#             xml = self._to_xml()
#         return xml


class Reference(BaseReference):

    """
    Base class for model components that are defined in the abstraction layer.
    """
    element_name = "Reference"

    # initial_values is temporary, the idea longer-term is to use a separate
    # library such as SEDML
    def __init__(self, name, context, url=None):
        """
        Create a new component with the given name, definition and properties,
        or create a prototype to another component that will be resolved later.

        `name`    -- a name of an existing component to refer to
        `context` -- a nineml.context.Context object containing the top-level
                     objects in the current file
        `url`     -- a url of the file containing the exiting component
        """
        super(Reference, self).__init__(name, context, url)
        if not isinstance(self._referred_to, BaseULObject):
            msg = ("Reference points to a non-user-layer object '{}'"
                   .format(self._referred_to.name))
            raise NineMLRuntimeError(msg)
        self._referred_to._from_reference = self

    @property
    def user_layer_object(self):
        return self._referred_to


def resolve_reference(from_xml):
    def resolving_from_xml(cls, element, context):
        if element.tag == NINEML + Reference.element_name:
            reference = Reference.from_xml(element, context)
            ul_object = reference.user_layer_object
        else:
            assert element.tag == NINEML + cls.element_name
            ul_object = from_xml(cls, element, context)
        return ul_object
    return resolving_from_xml


def write_reference(to_xml):
    def unresolving_to_xml(self, as_reference=True):
        if self._from_reference is not None and as_reference:
            xml = self._from_reference.to_xml()
        else:
            xml = to_xml(self)
        return xml
    return unresolving_to_xml
