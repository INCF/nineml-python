from itertools import chain
from operator import and_
import os.path
from .. import NINEML, nineml_namespace, E, read_annotations, annotate_xml, read  # @UnusedImport
from ..base import BaseNineMLObject
from ..exceptions import NineMLRuntimeError


class BaseULObject(BaseNineMLObject):

    """
    Base class for user layer classes
    """

    def __init__(self):
        self._from_reference = None

#     def set_reference(self, reference):
#         self._from_reference = reference
# 
#     def to_xml(self, as_reference=True):
#         if self._from_reference and as_reference:
#             xml = self._from_reference.to_xml()
#         else:
#             xml = self._to_xml()
#         return xml


def resolve_reference(from_xml):
    def resolving_from_xml(cls, element, context):
        if element.tag == NINEML + Reference.element_name:
            reference = Reference.from_xml(element, context)
            ul_object = reference.user_layer_object
        else:
            assert element.tag == cls.element_name
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


class BaseReference(BaseULObject):

    """
    Base class for model components that are defined in the abstraction layer.
    """

    # initial_values is temporary, the idea longer-term is to use a separate
    # library such as SEDML
    def __init__(self, name, context, url=None):
        """
        Create a new component with the given name, definition and properties,
        or create a prototype to another component that will be resolved later.

        `name` - a name of an existing component to refer to
        `url`            - a url of the file containing the exiting component
        """
        self.url = url
        if self.url:
            context = read(url, relative_to=os.path.dirname(context.url))
        self._referred_to = context[name]

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
    def from_xml(cls, element, context):
        if element.tag != NINEML + cls.element_name:
            raise Exception("Expecting tag name %s%s, actual tag name %s" % (
                NINEML, cls.element_name, element.tag))
        name = element.text
        url = element.attrib.get("url", None)
        return cls(name, context, url)


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
