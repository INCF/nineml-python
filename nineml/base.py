from itertools import chain, izip
import re
# from copy import copy
import operator
from collections import defaultdict, Iterator, Iterable
import sympy
from nineml.exceptions import (
    NineMLRuntimeError, NineMLNameError, NineMLInvalidElementTypeException,
    NineMLSerializationError)
from .visitors.cloner import Cloner
from .visitors.queriers import ObjectFinder


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
    children = []
    v1_nineml_type = None
    nineml_attr = ()
    nineml_child = {}
    nineml_children = ()

    def __eq__(self, other):
        return self.equals(other)

    def equals(self, other, defining_attributes=None, **kwargs):
        """
        Check for equality between 9ML objects.

        Parameters
        ----------
        defining_attributes : list(str)
            Overrides list of attributes to include in the check. If None, uses
            class member of same name
        annotations_ns : list(str)
            List of annotation namespaces to check for in equality check

        Returns
        -------
        equality : bool
            Whether the two 9ML objects are equal
        """
        # Not equal if of different types
        try:
            if self.nineml_type != other.nineml_type:
                return False
        except AttributeError:
            return False
        # If defining attributes aren't passed explicitly use the ones for the
        # current class
        if defining_attributes is None:
            defining_attributes = self.defining_attributes
        # Check if any attribute in the defining attributes doesn't match and
        # if so return False
        for name in defining_attributes:
            try:
                # Attempt to compare attributes directly
                self_elem = getattr(self, name)
                other_elem = getattr(other, name)
            except AttributeError:
                # If one or both of self and other are extended classes use the
                # associated property with the same name as the attribute minus
                # the leading '_'.
                assert name.startswith('_')
                self_elem = getattr(self, name[1:])
                other_elem = getattr(other, name[1:])
            # Convert iterators to list of sorted values so they can be
            # compared
            if isinstance(self_elem, Iterator):
                assert isinstance(other_elem, Iterator)
                self_elem = sorted(self_elem, key=sort_key)
                other_elem = sorted(other_elem, key=sort_key)
            if isinstance(self_elem, BaseNineMLObject):
                if not self_elem.equals(other_elem, **kwargs):
                    return False
            elif isinstance(self_elem, dict):
                try:
                    if set(self_elem.keys()) != set(other_elem.keys()):
                        return False
                except AttributeError:
                    return False
                for k, v in self_elem.iteritems():
                    try:
                        if not v.equals(other_elem[k], **kwargs):
                            return False
                    except AttributeError:
                        if v != other_elem[k]:
                            return False
            elif isinstance(self_elem, list):
                if len(self_elem) != len(other_elem):
                    return False
                try:
                    if not all(s.equals(o, **kwargs)
                               for s, o in izip(self_elem, other_elem)):
                        return False
                except AttributeError:
                    if self_elem != other_elem:
                        return False
            else:
                if self_elem != other_elem:
                    return False
        return True

    @classmethod
    def _sorted_values(self, container):
        if isinstance(container, dict):
            container = dict.itervalues()
        return sorted(container)

    def __repr__(self):
        return "{}(name='{}')".format(self.nineml_type, self.key)

    def __str__(self):
        try:
            return repr(self)
        except:
            raise

    def __ne__(self, other):
        return not self == other

    def get_children(self):
        return chain(getattr(self, attr) for attr in self.children)

    def accept_visitor(self, visitor):
        raise NotImplementedError(
            "Derived class '{}' has not overriden accept_visitor method."
            .format(self.__class__.__name__))

    def find_mismatch(self, other, indent='    '):
        """
        A method for displaying where two NineML objects differ. Used in
        debugging and error messages.
        """
        if not indent:
            result = ("Mismatch between '{}' types:"
                      .format(self.nineml_type))
        else:
            result = ''
        try:
            if self.nineml_type != other.nineml_type:
                result += ("mismatch in nineml_type, self:'{}' and other:'{}' "
                           "({} and {})"
                           .format(self.nineml_type, other.nineml_type,
                                   self, other))
            else:
                for attr_name in self.defining_attributes:
                    self_attr = getattr(self, attr_name)
                    other_attr = getattr(other, attr_name)
                    if isinstance(self_attr, Iterator):
                        assert isinstance(other_attr, Iterator)
                        self_attr = sorted(self_attr, key=sort_key)
                        other_attr = sorted(other_attr, key=sort_key)
                    if self_attr != other_attr:
                        result += "\n{}Attribute '{}': ".format(indent,
                                                                attr_name)
                        result += self._unwrap_mismatch(self_attr, other_attr,
                                                        indent + '  ')
        except AttributeError:
            if type(self) != type(other):
                result += ("mismatch in type self:{} and other:{} "
                           "({} and {})".format(type(self).__name__,
                                                type(other).__name__, self,
                                                other))
            elif self != other:
                result += ("self:{} != other:{}"
                           .format(self, other))
        return result

    @classmethod
    def _unwrap_mismatch(cls, s, o, indent):
        result = ''
        if isinstance(s, BaseNineMLObject):
            result += s.find_mismatch(o, indent=indent + '    ')
        elif isinstance(s, dict):
            s_keys = set(s.keys())
            o_keys = set(o.keys())
            if s_keys != o_keys:
                result += (
                    "keys do not match:\n{}  self:{}\n{}  other:{}".format(
                        indent, ", ".join(
                            "'{}'".format(k)
                            if isinstance(k, basestring)
                            else str(k) for k in sorted(s_keys,
                                                        key=hash_non_str)),
                        indent, ", ".join(
                            "'{}'".format(k)
                            if isinstance(k, basestring)
                            else str(k) for k in sorted(o_keys,
                                                        key=hash_non_str))))
            else:
                for k in s:
                    if s[k] != o[k]:
                        result += "\n{}Key '{}':".format(indent + '    ', k)
                        result += cls._unwrap_mismatch(s[k], o[k],
                                                       indent + '  ')
        elif isinstance(s, list):
            if len(s) != len(o):
                result += ('differ in length (self:{} to other:{})'
                           .format(len(s), len(o)))
            else:
                for i, (s_elem, o_elem) in enumerate(zip(s, o)):
                    if s_elem != o_elem:
                        result += "\n{}Index {}:".format(indent + '    ', i)
                        result += cls._unwrap_mismatch(s_elem, o_elem,
                                                       indent + '    ')
        else:
            if type(s) != type(o):
                result += ("mismatch in type self:{} != other:{} "
                           "({} and {})".format(
                               type(s).__name__, type(o).__name__,
                               s, o))
            else:
                result += "self:{} != other:{}".format(s, o)
        return result

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

    def clone(self, cloner=None, **kwargs):
        """
        General purpose clone operation, which copies the attributes used
        to define equality between 9ML objects. Other attributes, such as
        the document the 9ML object belongs to are re-initialized. Use this
        in favour of Python's copy and deepcopy functions unless you know what
        you want (i.e. things are likely to break if you are not careful).

        Parameters
        ----------
        exclude_annotations : bool
            Flags that annotations should be omitted from the clone
        """
        if cloner is None:
            cloner = Cloner(**kwargs)
        return cloner.clone(self, **kwargs)

#     def clone(self, memo=None, **kwargs):
#         """
#         General purpose clone operation, which copies the attributes used
#         to define equality between 9ML objects. Other attributes, such as
#         the document the 9ML object belongs to are re-initialized. Use this
#         in favour of Python's copy and deepcopy functions unless you know what
#         you want (i.e. things are likely to break if you are not careful).
# 
#         Parameters
#         ----------
#         memo : dict
#             A dictionary to hold copies of objects that have already been
#             cloned to avoid issues with circular references
#         exclude_annotations : bool
#             Flags that annotations should be omitted from the clone
#         """
#         if memo is None:
#             memo = {}
#         try:
#             # See if the attribute has already been cloned in memo
#             clone = memo[clone_id(self)]
#         except KeyError:
#             clone = copy(self)  # Create a new object of the same type
#             clone.__dict__ = {}  # Wipe it clean to start from scratch
#             # Save the element in the memo to avoid it being cloned twice in
#             # the object hierarchy. Due to possible recursion this needs to be
#             # set before the '_copy_to_clone' method is called.
#             memo[clone_id(self)] = clone
#             # The actual setting of attributes is handled by _copy_to_clone is
#             # used to allow sub classes to override it and control inheritance
#             # from super classes
#             self._copy_to_clone(clone, memo, **kwargs)
#         return clone

    def _copy_to_clone(self, clone, memo, **kwargs):
        self._clone_defining_attr(clone, memo, **kwargs)

    def _clone_defining_attr(self, clone, memo, **kwargs):
        for attr_name in self.defining_attributes:
            setattr(clone, attr_name,
                    _clone_attr(getattr(self, attr_name), memo, **kwargs))

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
    def unserialize(cls, serial_elem, format, **kwargs):  # @ReservedAssignment
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
        return nineml.unserialize(serial_elem, cls, format=format, **kwargs)

    def serialize_node(self, node, **options):  # @UnusedVariable
        """
        A generic serialize_node for classes that only implement
        the serialize_body method (e.g. SingleValue). All other classes should
        override this method.
        """
        try:
            node.body(self.serialize_body(**options), **options)
        except AttributeError:
            raise NineMLSerializationError(
                "'serialize_node (or serialize_body) not implemented for "
                "'{}' class".format(self.nineml_type))

    @classmethod
    def unserialize_node(cls, node, **options):  # @UnusedVariable
        """
        A generic unserialize_node for classes that only implement the
        unserialize_body method (e.g. SingleValue). All other classes should
        override this method.
        """
        try:
            return cls.unserialize_body(node.body(**options), **options)
        except AttributeError:
            raise NineMLSerializationError(
                "'serialize_node (or serialize_body) not implemented for "
                "'{}' class".format(cls.nineml_type))

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


def _clone_attr(attr, memo, **kwargs):
    """Recursively clone an attribute"""
    if attr is None or isinstance(attr, (basestring, float, int, bool,
                                         sympy.Basic)):
        clone = attr  # "primitive" type that doesn't need to be cloned
    elif hasattr(attr, 'clone'):
        clone = attr.clone(memo=memo, **kwargs)
    elif isinstance(attr, defaultdict):
        clone = type(attr)(attr.default_factory,
                            ((k, _clone_attr(v, memo, **kwargs))
                             for k, v in attr.iteritems()))
    elif isinstance(attr, dict):
        clone = type(attr)((k, _clone_attr(v, memo, **kwargs))
                           for k, v in attr.iteritems())
    elif isinstance(attr, Iterable):
        try:
            assert not isinstance(attr, Iterator)
        except:
            raise
        clone = attr.__class__(_clone_attr(a, memo, **kwargs)
                               for a in attr)
    else:
        assert False, "Unhandled attribute type {} ({})".format(type(attr),
                                                                attr)
    return clone


class AnnotatedNineMLObject(BaseNineMLObject):

    def __init__(self, annotations=None):
        if annotations is None:
            annotations = nineml.annotations.Annotations()
        else:
            assert isinstance(annotations, nineml.annotations.Annotations)
        self._annotations = annotations

    def _copy_to_clone(self, clone, memo, exclude_annotations=False, **kwargs):
        super(AnnotatedNineMLObject, self)._copy_to_clone(clone, memo,
                                                          **kwargs)
        if exclude_annotations:
            clone._annotations = nineml.annotations.Annotations()
        else:
            clone._annotations = self._annotations.clone(memo, **kwargs)

    def equals(self, other, **kwargs):
        return (super(AnnotatedNineMLObject, self).equals(other, **kwargs) and
                self.annotations_equal(other, **kwargs))

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

    def _copy_to_clone(self, clone, memo, **kwargs):
        super(DocumentLevelObject, self)._copy_to_clone(clone, memo, **kwargs)
        clone._document = None


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

    Deriving classes are expected to have the 'class_to_member' class
    attribute
    """

    def __init__(self):
        self._indices = defaultdict(dict)
        self._parent = None  # Used to link up the the containing document

    def add(self, *elements):
        add_to_doc_visitor = nineml.document.AddToDocumentVisitor(
            self.document)
        for element in elements:
            dct = self._member_dict(element)
            if element.key in dct:
                raise NineMLRuntimeError(
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
                raise NineMLRuntimeError(
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

    def index_of(self, element, key=None):
        """
        Returns the index of an element amongst others of its type. The indices
        are generated on demand but then remembered to allow them to be
        referred to again. The `key` argument can be provided to manually
        override the types with which the element is grouped, which allows the
        indexing of elements within supersets of various types.

        This function can be useful during code-generation from 9ML, where the
        name of an element can be replaced with a unique integer value (and
        referenced elsewhere in the code).
        """

        dct = self._get_indices_dict(key, type(element))
        try:
            index = dct[element]
        except KeyError:
            # Get the first index ascending from 0 not in the set
            try:
                index = next(iter(sorted(
                    set(xrange(len(dct))).difference(dct.itervalues()))))
            except StopIteration:
                index = len(dct)
            dct[element] = index
        return index

    def from_index(self, index, child_type, key=None):
        """
        The inverse of the index_of method for retrieving an object from its
        index
        """
        try:
            dct = self._get_indices_dict(key, child_type)
            for elem, i in dct.iteritems():
                if i == index:
                    return elem
        except KeyError:
            pass
        raise NineMLRuntimeError(
            "Could not find index {} for '{}'".format(
                index, (child_type if key is None else key)))

    # =========================================================================
    # Each member nineml_type is associated with a member accessor by the
    # class attribute 'class_to_member' dictionary. From this name accessors
    # for the set of members of this type, and their names and length, can be
    # derrived from the stereotypical naming structure used
    # =========================================================================

    def _get_indices_dict(self, key, child_type):
        if key is None:
            if child_type not in self.nineml_children:
                raise NineMLInvalidElementTypeException(
                    "{} is not a valid child type for container {} (valid "
                    " types are {}). Please use explicit key"
                    .format(child_type.__name__, self,
                            ", ".join(t.__name__
                                      for t in self.nineml_children)))
            key = child_type._child_accessor_name()
        return self._indices[key]

    def all_indices(self):
        for key, dct in self._indices.iteritems():
            for elem, index in dct.iteritems():
                yield key, elem, index

    def _member_accessor(self, child_type):
        return getattr(self, child_type._child_accessor_name())

    def _members_iter(self, child_type):
        return getattr(self, child_type._children_iter_name())

    def _member_keys_iter(self, child_type):
        return getattr(self, child_type._children_keys_name())

    def _num_members(self, child_type):
        return getattr(self, child_type._num_children_name())

    def _member_dict(self, child_type):
        return getattr(self, child_type._children_dict_name())

    @property
    def parent(self):
        return self._parent

    @property
    def document(self):
        try:
            # If a document level object return its document attribute
            document = DocumentLevelObject.document(self)
        except TypeError:
            # Otherwise return parent's document if set
            if self.parent is not None:
                document = self.parent.document
            else:
                document = None
        return document

# 
#     def _copy_to_clone(self, clone, memo, **kwargs):
#         super(ContainerObject, self)._copy_to_clone(clone, memo, **kwargs)
#         clone._indices = defaultdict(dict)
#         clone._parent = (self._parent.clone(memo, **kwargs)
#                          if self._parent is not None else None)


def pluralise(word):
    if word.endswith('s'):
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
