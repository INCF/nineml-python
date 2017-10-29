from past.builtins import basestring
from builtins import object
from itertools import chain
import re
# from copy import copy
import operator
from collections import OrderedDict
from nineml.exceptions import (
    NineMLUsageError, NineMLNameError, NineMLInvalidElementTypeException)
from .visitors.cloner import Cloner
from .visitors.queriers import ObjectFinder
from .visitors.equality import EqualityChecker, Hasher, MismatchFinder
from functools import reduce


def sort_key(elem):
    return elem.sort_key


def hash_non_str(key):
    if not isinstance(key, basestring):
        key = hash(key)
    return key


camel_caps_re = re.compile(r'([a-z])([A-Z])')


class BaseNineMLObject(object):
    """
    Base class for all 9ML-type classes
    """

    nineml_type_v1 = None
    nineml_attr = ()
    nineml_child = {}
    nineml_children = ()
    # Used to distinguish between permanent objects and those that are created
    # on the fly, such as the ones used to duck-type MultiDynamics objects with
    # Dynamics objects
    temporary = False
    # Specifies whether a serialized object has a "body" (i.e. in XML)
    has_serial_body = False

    @classmethod
    def _sorted_values(self, container):
        if isinstance(container, dict):
            container = iter(dict.values())
        return sorted(container)

    def __repr__(self):
        return "{}(name='{}')".format(self.nineml_type, self.key)

    def __str__(self):
        return repr(self)

    def __eq__(self, other):
        return self.equals(other)

    def __hash__(self):
        return Hasher().hash(self)

    def __ne__(self, other):
        return not self == other

    @property
    def id(self):
        """
        An ID used to distinguish two objects from each other.

        If a "non-temporary" object (i.e. not a namespace escaped object
        generated on the fly to duck type with a base class, such as
        _MultiRegime, _NamespaceParameter, etc...) then this method returns
        the address of the object in memory.

        If a temporary object, this is the ID of its parent combined with
        its class type and unique key
        """
        if self.temporary:
            # Create a unique string from the id of the parent (which should
            # be anchored in the memory location of a "non-temporary" object)
            # plus the name of the type and its key.
            try:
                parent_id = hex(self._parent.id)
            except TypeError:
                parent_id = self._parent.id  # Temporary object ID
            id_ = parent_id + type(self).__name__ + '_' + str(self.key)
        else:
            id_ = id(self)
        return id_

    def equals(self, other, **kwargs):
        checker = EqualityChecker(**kwargs)
        return checker.check(self, other, **kwargs)

    def find_mismatch(self, other, **kwargs):
        finder = MismatchFinder(**kwargs)
        return finder.find(self, other, **kwargs)

    def clone(self, cloner=None, name=None, **kwargs):
        """
        General purpose clone operation, which copies the attributes used
        to define equality between 9ML objects. Other attributes, such as
        the document the 9ML object belongs to are re-initialized. Use this
        in favour of Python's copy and deepcopy functions unless you know what
        you want (i.e. things are likely to break if you are not careful).

        Parameters
        ----------
        cloner : Cloner
            A Cloner instance to be used to clone the object with. If None,
            a new instance is created using the **kwargs
        name : str
            A new name for the clone. If none the original name is kept.
        exclude_annotations : bool
            Flags that annotations should be omitted from the clone
        """
        if cloner is None:
            cloner = Cloner(**kwargs)
        clone = cloner.clone(self, **kwargs)
        if name is not None:
            clone._name = name
        return clone

    def find(self, nineml_obj):
        """
        Finds the element within the container that equals the given
        element

        Parameters
        ----------
        nineml_obj : BaseNineMLObject
            The object to find within the container
        """
        return ObjectFinder(nineml_obj, self).found

    def write(self, url, **kwargs):
        """
        Serialize and writes the 9ML object to file

        Parameters
        ----------
        url : str
            A path on the local file system (either absoluate or relative).
            The format for the serialization is written in is determined by the
            extension of the url.
        register : bool
            Whether to store the document in the cache after writing
        version : str | float | int
            The version to serialize the NineML objects to
        """
        nineml.write(url, self, **kwargs)

    def serialize(self, **kwargs):
        """
        Serializes a NineML object into a serialized element

        Parameters
        ----------
        format : str
            The name of the format (which matches a key format_to_serializer)
        version : str | float | int
            The version to serialize the NineML objects to
        document : Document
            The document to write local references to
        to_str : bool
            To serialize to a string instead of a serial element.
        """
        return nineml.serialize(self, **kwargs)

    @classmethod
    def unserialize(cls, serial_elem, format, version, **kwargs):  # @ReservedAssignment @IgnorePep8
        """
        Unserializes a serial element to the given NineML class

        Parameters
        ----------
        serial_elem : <serial-element>
            A serial element in the format given
        format : str
            The name of the format (which matches a key format_to_serializer)
        version : str | float | int
            The version to serialize the NineML objects to
        document : Document | None
            The document to read local references from
        url : URL | None
            The url to assign to the unserialized object
        root : <serial-element>
            A serial element of containing the document to read local
            references from
        """
        return nineml.unserialize(serial_elem, cls, format=format,
                                  version=version, **kwargs)

    @property
    def key(self):
        """
        Key with which to uniquely identify the 9ML object from others in its
        container
        """
        try:
            return self.name
        except AttributeError:
            assert False, (
                "{} class does not have a name and doesn't implement the 'key'"
                " property".format(self.__class__.__name__))

    @property
    def sort_key(self):
        """
        Returns a key that can be used to sort the 9ML object with others in
        its class. Typically the same as 'key' but in some classes such as
        Triggers and OnConditions, which use the condition equation as a key
        a string representation needs to be used instead.
        """
        return self.key

    @classmethod
    def _child_accessor_name(cls):
        return camel_caps_re.sub(r'\1_\2', cls.nineml_type).lower()

    @classmethod
    def _children_iter_name(cls):
        name = cls._child_accessor_name()
        return pluralise(name)

    @classmethod
    def _children_dict_name(cls):
        return '_' + cls._children_iter_name()

    @classmethod
    def _num_children_name(cls):
        return 'num_' + cls._children_iter_name()

    @classmethod
    def _children_keys_name(cls):
        return cls._child_accessor_name() + (
            '_names' if hasattr(cls, 'name') else '_keys')


class AnnotatedNineMLObject(BaseNineMLObject):

    def __init__(self, annotations=None):
        if annotations is None:
            annotations = nineml.annotations.Annotations()
        else:
            assert isinstance(annotations, nineml.annotations.Annotations)
        self._annotations = annotations

    @property
    def annotations(self):
        return self._annotations

    def annotations_equal(self, other, annotations_ns=[], **kwargs):  # @UnusedVariable @IgnorePep8
        """
        Check for equality between annotations within specified namespaces of
        two 9ML objects.

        Parameters
        ----------
        annotations_ns : list(str)
            List of annotation namespaces to check for in equality check

        Returns
        -------
        equality : bool
            Whether the annotations of the two 9ML objects are equal
        """
        if not hasattr(self, 'annotations'):
            return True
        for name, ns in self.annotations:
            if ns in annotations_ns:
                try:
                    if self.annotations[(name, ns)] != other.annotations[(name,
                                                                          ns)]:
                        return False
                except NineMLNameError:
                    return False
        return True


class DocumentLevelObject(BaseNineMLObject):

    def __init__(self):
        # _document is set when the object is added to a document
        self._document = None

    @property
    def document(self):
        return self._document

    @property
    def url(self):
        if self.document is not None:
            url = self.document.url
        else:
            url = None
        return url

    @property
    def attributes_with_dimension(self):
        return []  # To be overridden in derived classes

    @property
    def attributes_with_units(self):
        return []  # To be overridden in derived classes

    @property
    def all_units(self):
        return [a.units for a in self.attributes_with_units]

    @property
    def all_dimensions(self):
        return [a.dimension for a in self.attributes_with_dimension]

    def write(self, fname, **kwargs):
        """
        Writes the top-level NineML object to file in XML.
        """
        nineml.write(fname, self, **kwargs)


class DynamicPortsObject(BaseNineMLObject):
    """
    Defines generic iterators and accessors for objects that expose
    dynamic ports
    """

    @property
    def ports(self):
        return chain(self.analog_send_ports, self.analog_receive_ports,
                     self.analog_reduce_ports, self.event_send_ports,
                     self.event_receive_ports)

    def port(self, name):
        try:
            return self.send_port(name)
        except NineMLNameError:
            try:
                return self.receive_port(name)
            except NineMLNameError:
                raise NineMLNameError(
                    "'{}' Dynamics object does not have a port named '{}'"
                    .format(self.name, name))

    @property
    def port_names(self):
        return (p.name for p in self.ports)

    def receive_port(self, name):
        try:
            return self.event_receive_port(name)
        except NineMLNameError:
            try:
                return self.analog_receive_port(name)
            except NineMLNameError:
                try:
                    return self.analog_reduce_port(name)
                except NineMLNameError:
                    raise NineMLNameError(
                        "'{}' Dynamics object does not have a receive port "
                        "named '{}'".format(self.name, name))

    def send_port(self, name):
        try:
            return self.event_send_port(name)
        except NineMLNameError:
            try:
                return self.analog_send_port(name)
            except NineMLNameError:
                raise NineMLNameError(
                    "'{}' Dynamics object does not have a send port "
                    "named '{}'".format(self.name, name))

    @property
    def send_ports(self):
        return chain(self.analog_send_ports, self.event_send_ports)

    @property
    def receive_ports(self):
        return chain(self.analog_receive_ports, self.analog_reduce_ports,
                     self.event_receive_ports)

    @property
    def send_port_names(self):
        return chain(self.analog_send_port_names, self.event_send_port_names)

    @property
    def receive_port_names(self):
        return chain(self.analog_receive_port_names,
                     self.analog_reduce_port_names,
                     self.event_receive_port_names)

    @property
    def num_send_ports(self):
        return self.num_analog_send_ports + self.num_event_send_ports

    @property
    def num_receive_ports(self):
        return (self.num_analog_receive_ports + self.num_analog_reduce_ports +
                self.num_event_receive_ports)

    @property
    def num_analog_ports(self):
        return (self.num_analog_receive_ports + self.num_analog_send_ports +
                self.num_analog_reduce_ports)

    @property
    def num_event_ports(self):
        return (self.num_event_receive_ports + self.num_event_send_ports)

    @property
    def num_ports(self):
        return self.num_send_ports + self.num_receive_ports

    @property
    def analog_ports(self):
        """Returns an iterator over the local analog port objects"""
        return chain(self.analog_send_ports, self.analog_receive_ports,
                     self.analog_reduce_ports)

    @property
    def analog_port_names(self):
        return (p.name for p in self.analog_ports)

    @property
    def event_ports(self):
        return chain(self.event_send_ports, self.event_receive_ports)

    def analog_port(self, name):
        try:
            return self.analog_send_port(name)
        except KeyError:
            try:
                return self.analog_receive_port(name)
            except KeyError:
                return self.analog_reduce_port(name)

    def event_port(self, name):
        try:
            return self.event_send_port(name)
        except KeyError:
            return self.event_receive_port(name)

    @property
    def event_port_names(self):
        return (p.name for p in self.event_ports)


class ContainerObject(BaseNineMLObject):
    """
    An abstract base class for handling the manipulation of member objects
    (which are stored in dictionaries that can be detected by member type).

    Deriving classes are expected to have the 'nineml_children' class
    attribute listing the classes of the children in the container.
    """

    def __init__(self):
        for children_type in self.nineml_children:
            setattr(self, children_type._children_dict_name(), OrderedDict())

        self._parent = None  # Used to link up the the containing document

    def add(self, *elements):
        add_to_doc_visitor = nineml.document.AddToDocumentVisitor(
            self.document)
        for element in elements:
            dct = self._member_dict(element)
            if element.key in dct:
                raise NineMLUsageError(
                    "Could not add '{}' {} to container as it clashes "
                    "with an existing element with the same key"
                    .format(element.key, type(element).__name__))
            dct[element.key] = element
            # Set parent if a property of the child element to add
            if hasattr(element, 'parent'):
                element._parent = self
            # Add nested references to document
            if self.document is not None:
                add_to_doc_visitor.visit(element)

    def remove(self, *elements):
        for element in elements:
            dct = self._member_dict(element)
            try:
                del dct[element.key]
            except KeyError:
                raise NineMLUsageError(
                    "Could not remove '{}' from container as it was not "
                    "found in member dictionary (use 'ignore_missing' option "
                    "to ignore)".format(element.key))
            # Remove reference to parent if present
            try:
                if element.parent is self:
                    element._parent = None
            except AttributeError:
                pass

    def _update_member_key(self, old_key, new_key):
        """
        Updates the member key for a given element_type
        """
        for child_type in self.nineml_children:
            member_dict = self._member_dict(child_type)
            try:
                member_dict[new_key] = member_dict.pop(old_key)
            except KeyError:
                pass

    def elements(self, child_types=None):
        """
        Iterates through all the core member elements of the container. For
        core 9ML objects this will be the same as those iterated by the
        __iter__ magic method, where as for 9ML extensions.
        """
        if child_types is None:
            child_types = self.nineml_children
        return chain(*(self._members_iter(child_type)
                       for child_type in child_types))

    def element(self, name, child_types=None, include_send_ports=False):
        """
        Looks a member item by "name" (identifying characteristic)

        Parameters
        ----------
        name : str
            Name of the element to return
        nineml_children : dict[str, str]
            Mapping from element type to accessor name
        include_send_ports:
            As send ports will typically mask the name as an alias or
            state variable (although not necessarily in MultiDynamics objects)
            they are ignored unless this kwarg is set to True, in which case
            they will be returned only if no state variable or alias is found.

        Returns
        -------
        elem : NineMLBaseObject
            The element corresponding to the provided 'name' argument
        """
        if child_types is None:
            child_types = self.nineml_children
        send_port = None
        for child_type in child_types:
            try:
                elem = self._member_accessor(child_type)(name)
                # Ignore send ports as they otherwise mask
                # aliases/state variables
                if isinstance(elem, SendPortBase):
                    send_port = elem
                else:
                    return elem  # No need to wait to end of loop
            except NineMLNameError:
                pass
        if include_send_ports and send_port is not None:
            return send_port
        else:
            raise NineMLNameError(
                "'{}' was not found in '{}' {} object"
                .format(name, self.key, self.__class__.__name__))

    def num_elements(self, child_types=None):
        if child_types is None:
            child_types = self.nineml_children
        return reduce(operator.add,
                      (self._num_members(child_type)
                       for child_type in child_types))

    def element_keys(self, child_types=None):
        if child_types is None:
            child_types = self.nineml_children
        all_keys = set()
        for child_type in child_types:
            # Some of these do not meet the stereotypical *_names format, e.g.
            # time_derivative_variables, could change these to *_keys instead
            try:
                for key in self._member_keys_iter(child_type):
                    # Because send ports can have the same name as state
                    # variables and aliases duplicates need to be avoided
                    all_keys.add(key)
            except AttributeError:
                pass
        return iter(all_keys)

    def __iter__(self):
        raise TypeError("{} containers are not iterable"
                         .format(type(self).__name__))

    def index_of(self, element):
        """
        Returns the index of an element amongst others of its type.

        This function can be useful during code-generation from 9ML, where the
        name of an element can be replaced with a unique integer value (and
        referenced elsewhere in the code).
        """
        return list(self._member_keys_iter(element)).index(element.key)

    def from_index(self, index, child_type):
        """
        The inverse of the index_of method for retrieving an object from its
        index
        """
        return list(self._members_iter(child_type))[index]

    def _member_accessor(self, child_type):
        try:
            return getattr(self, child_type._child_accessor_name())
        except AttributeError:
            if child_type not in self.nineml_children:
                raise NineMLInvalidElementTypeException(
                    "{} does not have children of type {}"
                    .format(self, child_type))
            else:
                raise

    def _members_iter(self, child_type):
        try:
            return getattr(self, child_type._children_iter_name())
        except AttributeError:
            if child_type not in self.nineml_children:
                raise NineMLInvalidElementTypeException(
                    "{} does not have children of type {}"
                    .format(self, child_type))
            else:
                raise

    def _member_keys_iter(self, child_type):
        try:
            return getattr(self, child_type._children_keys_name())
        except AttributeError:
            if child_type not in self.nineml_children:
                raise NineMLInvalidElementTypeException(
                    "{} does not have children of type {}"
                    .format(self, child_type))
            else:
                raise

    def _num_members(self, child_type):
        try:
            return getattr(self, child_type._num_children_name())
        except AttributeError:
            if child_type not in self.nineml_children:
                raise NineMLInvalidElementTypeException(
                    "{} does not have children of type {}"
                    .format(self, child_type))
            else:
                raise

    def _member_dict(self, child_type):
        try:
            return getattr(self, child_type._children_dict_name())
        except AttributeError:
            if child_type not in self.nineml_children:
                raise NineMLInvalidElementTypeException(
                    "{} does not have children of type {}"
                    .format(self, child_type))
            else:
                raise

    @property
    def parent(self):
        return self._parent

    @property
    def document(self):
        if isinstance(self, DocumentLevelObject):
            document = self._document
        elif self.parent is not None:
            # Otherwise return parent's document if set
            document = self.parent.document
        else:
            document = None
        return document


def pluralise(word):
    if word.endswith('ies'):
        word = word + 's'  # Not a proper plural but we can't use an apostrophe
    elif word.endswith('s') or word.endswith('h'):
        word = word + 'es'
    elif word.endswith('y'):
        word = word[:-1] + 'ies'
    else:
        word = word + 's'
    return word


class SendPortBase(object):
    """
    Dummy class to allow look up via inheritence of SendPort in this module
    without causing circular import problems
    """


import nineml  # @IgnorePep8
