from itertools import chain, izip
from copy import copy
import operator
from collections import defaultdict, Iterator, Iterable
import sympy
from nineml.exceptions import (
    NineMLRuntimeError, NineMLNameError, NineMLInvalidElementTypeException,
    NineMLSerializationError)


def sort_key(elem):
    return elem.sort_key


def hash_non_str(key):
    if not isinstance(key, basestring):
        key = hash(key)
    return key


def clone_id(obj):
    """
    Used in storing cloned objects in 'memo' dictionary to avoid duplicate
    clones of the same object referenced from different points in a complex
    data tree. First looks for special method 'clone_id' and falls back on the
    'id' function that returns a memory-address based ID.

    Parameters
    ----------
    obj : object
        Any object
    """
    try:
        return obj.clone_id
    except AttributeError:
        return id(obj)


class BaseNineMLObject(object):

    """
    Base class for user layer classes
    """
    children = []
    v1_nineml_type = None

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

    def clone(self, memo=None, **kwargs):
        """
        General purpose clone operation, which copies the attributes used
        to define equality between 9ML objects. Other attributes, such as
        the document the 9ML object belongs to are re-initialized. Use this
        in favour of Python's copy and deepcopy functions unless you know what
        you want (i.e. things are likely to break if you are not careful).

        Parameters
        ----------
        memo : dict
            A dictionary to hold copies of objects that have already been
            cloned to avoid issues with circular references
        exclude_annotations : bool
            Flags that annotations should be omitted from the clone
        """
        if memo is None:
            memo = {}
        try:
            # See if the attribute has already been cloned in memo
            clone = memo[clone_id(self)]
        except KeyError:
            clone = copy(self)  # Create a new object of the same type
            clone.__dict__ = {}  # Wipe it clean to start from scratch
            # Save the element in the memo to avoid it being cloned twice in
            # the object hierarchy. Due to possible recursion this needs to be
            # set before the '_copy_to_clone' method is called.
            memo[clone_id(self)] = clone
            # The actual setting of attributes is handled by _copy_to_clone is
            # used to allow sub classes to override it and control inheritance
            # from super classes
            self._copy_to_clone(clone, memo, **kwargs)
        return clone

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
        for element_type in self.class_to_member:
            member_dict = self._member_dict(element_type)
            try:
                member_dict[new_key] = member_dict.pop(old_key)
            except KeyError:
                pass

    def elements(self, class_map=None):
        """
        Iterates through all the core member elements of the container. For
        core 9ML objects this will be the same as those iterated by the
        __iter__ magic method, where as for 9ML extensions.
        """
        if class_map is None:
            class_map = self.class_to_member
        return chain(*(self._members_iter(et, class_map=class_map)
                       for et in class_map))

    def element(self, name, class_map=None, include_send_ports=False):
        """
        Looks a member item by "name" (identifying characteristic)

        Parameters
        ----------
        name : str
            Name of the element to return
        class_map : dict[str, str]
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
        if class_map is None:
            class_map = self.class_to_member
        send_port = None
        for element_type in class_map:
            try:
                elem = self._member_accessor(
                    element_type, class_map=class_map)(name)
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

    def num_elements(self, class_map=None):
        if class_map is None:
            class_map = self.class_to_member
        return reduce(operator.add,
                      (self._num_members(et, class_map=class_map)
                       for et in class_map))

    def element_keys(self, class_map=None):
        if class_map is None:
            class_map = self.class_to_member
        all_keys = set()
        for element_type in class_map:
            # Some of these do not meet the stereotypical *_names format, e.g.
            # time_derivative_variables, could change these to *_keys instead
            try:
                for key in self._member_keys_iter(element_type,
                                                    class_map=class_map):
                    # Because send ports can have the same name as state
                    # variables and aliases duplicates need to be avoided
                    all_keys.add(key)
            except AttributeError:
                pass
        return iter(all_keys)

    def __iter__(self):
        raise TypeError("{} containers are not iterable"
                         .format(type(self).__name__))

    def index_of(self, element, key=None, class_map=None):
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

        dct = self._get_indices_dict(element, key, class_map)
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

    def from_index(self, index, element_type=None, key=None, class_map=None):
        """
        The inverse of the index_of method for retrieving an object from its
        index
        """
        try:
            dct = self._get_indices_dict(element_type, key, class_map)
            for elem, i in dct.iteritems():
                if i == index:
                    return elem
        except KeyError:
            pass
        raise NineMLRuntimeError(
            "Could not find index {} for '{}'".format(
                index, (element_type if element_type is not None else key)))

    def _get_indices_dict(self, element_type, key, class_map):
        if class_map is None:
            class_map = self.class_to_member
        if key is None:
            key = accessor_name_from_type(element_type, class_map)
        return self._indices[key]

    def all_indices(self):
        for key, dct in self._indices.iteritems():
            for elem, index in dct.iteritems():
                yield key, elem, index

    # =========================================================================
    # Each member nineml_type is associated with a member accessor by the
    # class attribute 'class_to_member' dictionary. From this name accessors
    # for the set of members of this type, and their names and length, can be
    # derrived from the stereotypical naming structure used
    # =========================================================================

    def _member_accessor(self, element_type, class_map):
        try:
            return getattr(self, accessor_name_from_type(element_type,
                                                         class_map))
        except:
            raise

    def _members_iter(self, element_type, class_map):
        """
        Looks up the name of values iterator from the nineml_type of the
        element argument.
        """
        acc_name = accessor_name_from_type(element_type, class_map)
        return getattr(self, pluralise(acc_name))

    def _member_keys_iter(self, element_type, class_map):
        acc_name = accessor_name_from_type(element_type, class_map)
        try:
            return getattr(self, (acc_name + '_names'))
        except AttributeError:
            # For members that don't have proper names, such as OnConditions
            return getattr(self, (acc_name + '_keys'))

    def _num_members(self, element_type, class_map):
        acc_name = accessor_name_from_type(element_type, class_map)
        return getattr(self, 'num_' + pluralise(acc_name))

    def _member_dict(self, element_type):
        acc_name = accessor_name_from_type(element_type, self.class_to_member)
        return getattr(self, '_' + pluralise(acc_name))

    def _copy_to_clone(self, clone, memo, **kwargs):
        super(ContainerObject, self)._copy_to_clone(clone, memo, **kwargs)
        clone._indices = defaultdict(dict)
        clone._parent = (self._parent.clone(memo, **kwargs)
                         if self._parent is not None else None)

    @classmethod
    def _accessor_name(cls):
        return cls.__name__.lower()

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


def accessor_name_from_type(element_type, class_map):
    """
    Looks up the name of the accessor method from the nineml_type of the
    element argument for a given container type
    """
    if not isinstance(element_type, basestring):
        try:
            element_type = element_type.nineml_type
        except:
            raise
    try:
        return class_map[element_type]
    except KeyError:
        raise NineMLInvalidElementTypeException(
            "Could not get member attr for element of type '{}', available "
            "types are {}".format(element_type, ", ".join(class_map.keys())))


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


class BaseNineMLVisitor(object):
    """
    Generic visitor base class that visits a 9ML object and all children (and
    children's children etc...) and calls 'action_<nineml-type>' and
    'post_action_<nineml-type>'. These methods are not implemented in this
    base class but can be overridden in derived classes that wish to perform
    an action on specific element types.

    For example to perform an action on all units (and nothing else) in the
    object a derived class can be written as

    class UnitVisitor(Visitor):

        def action_unit(unit, **kwargs):
            # Do action here

    """

    class_to_visit = None

    class Context(object):
        "The context within which the current element is situated"

        def __init__(self, parent, parent_result, attr_name=None, dct=None):
            self._parent = parent
            self._parent_result = parent_result
            self._attr_name = attr_name
            self._dct = dct

        @property
        def parent(self):
            return self._parent

        @property
        def parent_result(self):
            return self._parent_result

        @property
        def attr_name(self):
            return self._attr_name

        @property
        def dct(self):
            return self._dct

        def replace(self, old, new):
            if self.attr_name is not None:
                setattr(self.parent, self.attr_name, new)
            elif self.dct is not None:
                del self.dct[old.name]
                self.dct[new.name] = new

    class Results(object):

        def __init__(self, action_result):
            self._action = action_result
            self._post_action = None
            self._attr = {}
            self._children = defaultdict(dict)

        @property
        def action(self):
            return self._action

        @property
        def post_action(self):
            return self._post_action

        @property
        def children(self):
            return self._children.itervalues()

        @property
        def child_names(self):
            return self._children.iterkeys()

        def attr_result(self, name):
            return self._attr[name]

        def child_result(self, child):
            return self._children[child.nineml_type][child.key]

        def child_results(self, child_type):
            return self._children[child_type].itervalues()

    def __init__(self):
        self.contexts = []
        self._method_name = None
        self._stop = False

    def visit(self, obj, **kwargs):
        # Allow deriving classes to run a function when visiting the top most
        # object in the hierarchy
        if not self.contexts:
            self.initial(obj, **kwargs)
        # Run the 'action_<obj-nineml_type>' method on the visited object
        action_result = self.action(obj, **kwargs)
        # Visit all the attributes of the object that are 9ML objects
        # themselves
        results = self.Results(action_result)
        # Add the container object to the list of scopes
        for attr_name in obj.defining_attributes:
            try:
                attr = getattr(obj, attr_name)
            except AttributeError:
                if attr_name.startswith('_'):
                    attr = getattr(obj, attr_name[1:])
                else:
                    raise
            if isinstance(attr, BaseNineMLObject):
                # Create the context around the visit of the attribute
                context = self.Context(obj, action_result, attr_name)
                self.contexts.append(context)
                results._attr[attr_name] = self.visit(attr, **kwargs)
                popped = self.contexts.pop()
                assert context is popped
        # Visit children of the object
        if isinstance(obj, ContainerObject):
            if (self.class_to_visit is not None and
                    isinstance(obj, self.class_to_visit)):
                # Used for derived classes (e.g. MultiDynamics) that are
                # polymorphic accessors with the base class in terms of
                # accessors but have different internal structure.
                class_map = self.class_to_visit.class_to_member
            else:
                class_map = obj.class_to_member
            for child_type in class_map:
                try:
                    dct = obj._member_dict(child_type)
                except (NineMLInvalidElementTypeException, AttributeError):
                    dct = None  # If class_map comes from class_to_visit
                context = self.Context(obj, action_result, dct=dct)
                self.contexts.append(context)
                for child in obj._members_iter(child_type, class_map):
                    results._children[
                        child_type][child.key] = self.visit(child, **kwargs)
                popped = self.contexts.pop()
                assert context is popped
        # Peform "post-action" method that runs after the children/attributes
        # have been visited
        self.post_action(obj, results, **kwargs)
        if not self.contexts:
            self.final(obj, **kwargs)
        return results

    def action(self, obj, **kwargs):
        self._action(obj, prefix='action_', default=self.default_action,
                     **kwargs)

    def post_action(self, obj, results, **kwargs):
        self._action(obj, prefix='post_action_', results=results,
                     default=self.default_post_action, **kwargs)

    def _action(self, obj, prefix, default=None, action_type=None,
                results=None, **kwargs):
        try:
            method_name = prefix + action_type
        except TypeError:
            method_name = prefix + obj.nineml_type.lower()
        try:
            method = getattr(self, method_name)
        except AttributeError:
            if default is None:
                raise
            try:
                for action_type in obj.alternative_actions:
                    try:
                        self._action(obj, prefix, action_type=action_type,
                                     **kwargs)
                    except AttributeError:
                        continue
            except AttributeError:
                pass
            method = default
        return method(obj, results=results, **kwargs)

    def initial(self, obj, **kwargs):
        """
        Ran after the object at the top of the hierarchy is visited
        """
        pass

    def final(self, obj, **kwargs):
        """
        Ran after all the children and attributes the object at the top of the
        hierarchy is visited
        """
        pass

    @property
    def context(self):
        if self.contexts:
            context = self.contexts[-1]
        else:
            context = None
        return context

    def context_key(self, key):
        return tuple([c.parent for c in self.contexts] + [key])

    def default_action(self, obj, **kwargs):  # @UnusedVariable
        """
        Default action performed on every object that doesn't define an
        explicit '<nineml-type-name>_action' method
        """
        return None

    def default_post_action(self, obj, results, **kwargs):  # @UnusedVariable
        """
        Default action performed on every object that doesn't define an
        explicit '<nineml-type-name>_post_action' method
        """
        return results


import nineml  # @IgnorePep8
