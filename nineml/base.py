from itertools import chain
import operator
from collections import defaultdict, Iterator
from nineml.exceptions import (
    NineMLRuntimeError, NineMLNameError, NineMLInvalidElementTypeException)


def sort_key(elem):
    return elem.sort_key


def hash_non_str(key):
    if not isinstance(key, basestring):
        key = hash(key)
    return key


class BaseNineMLObject(object):

    """
    Base class for user layer classes
    """
    children = []

    def __init__(self, annotations=None):
        if annotations is None:
            annotations = nineml.annotations.Annotations()
        else:
            assert isinstance(annotations, nineml.annotations.Annotations)
        self._annotations = annotations

    @property
    def annotations(self):
        return self._annotations

    def __eq__(self, other, defining_attributes=None):
        if defining_attributes is None:
            defining_attributes = self.defining_attributes
        try:
            if self.nineml_type != other.nineml_type:
                return False
        except AttributeError:
            return False
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
            if isinstance(self_elem, Iterator):
                assert isinstance(other_elem, Iterator)
                self_elem = sorted(self_elem, key=sort_key)
                other_elem = sorted(other_elem, key=sort_key)
            if self_elem != other_elem:
                return False
#             try:
#                 self_elem = getattr(self, name)
#             except AttributeError:
#                 # Extension classes will typically override the associated
#                 # property attribute, which has the same name as the defining
#                 # attribute minus the leading underscore (sorry if this feels
#                 # a bit hacky)
#                 assert name.startswith('_')
#                 self_elem = getattr(self, name[1:])
#                 if isinstance(self_elem, Iterator):
#                     compare_iterators = True
#                     self_elem = sorted(self_elem)   # Create list from iterator
#             try:
#                 other_elem = getattr(self, name)
#                 if compare_iterators:
#                     other_elem = self._sorted_values(other_elem)
#             except AttributeError:
#                 assert name.startswith('_')
#                 other_elem = getattr(self, name[1:])
#                 if isinstance(other_elem, Iterator):
#                     other_elem = sorted(other_elem)
#             if (isinstance(self_elem, (basestring, BaseNineMLObject)) or
#                     all(isinstance(e, dict) for e in (self_elem, other_elem))):
#                 equality = (self_elem == other_elem)
#             else:
#             if not all(isinstance(e, (dict, basestring, BaseNineMLObject))
#                        for e in (self_elem, other_elem)):
#                 # Try to sort the elements by their '_name' attribute (so they
#                 # are order non-specific) if they are an iterable
#                 try:
#                     self_elem = sorted(self_elem, key=lambda x: str(x.key))
#                     other_elem = sorted(other_elem, key=lambda x: str(x.key))
#                 except (TypeError, ValueError, AttributeError):
#                     pass
        return True

    @classmethod
    def _sorted_values(self, container):
        if isinstance(container, dict):
            container = dict.itervalues()
        return sorted(container)

    def __repr__(self):
        return "{}(name='{}')".format(self.nineml_type, self._name)

    def __str__(self):
        return repr(self)

    def __ne__(self, other):
        return not self == other

    def get_children(self):
        return chain(getattr(self, attr) for attr in self.children)

    def accept_visitor(self, visitor):
        raise NotImplementedError(
            "Derived class '{}' has not overriden accept_visitor method."
            .format(self.__class__.__name__))

    def find_mismatch(self, other, indent='  '):
        """
        A function used for debugging where two NineML objects differ
        """
        if not indent:
            result = ("Mismatch between '{}' types:"
                      .format(self.nineml_type))
        else:
            result = ''
        try:
            if self.nineml_type != other.nineml_type:
                result += ("mismatch in nineml_type, self:'{}' and other:'{}'"
                           .format(self.nineml_type, other.nineml_type))
            else:
                for attr_name in self.defining_attributes:
                    self_attr = getattr(self, attr_name)
                    other_attr = getattr(other, attr_name)
                    if self_attr != other_attr:
                        result += "\n{}Attribute '{}': ".format(indent,
                                                                attr_name)
                        result += self._unwrap_mismatch(self_attr, other_attr,
                                                        indent + '  ')
        except AttributeError:
            if type(self) != type(other):
                result += "mismatch in type self:{} and other:{}".format(
                    type(self).__name__, type(other).__name__)
            elif self != other:
                result += ("self:{} != other:{}"
                           .format(self, other))
        return result

    @classmethod
    def _unwrap_mismatch(cls, s, o, indent):
        result = ''
        if isinstance(s, BaseNineMLObject):
            result += s.find_mismatch(o, indent=indent + '  ')
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
                        result += "\n{}Key '{}':".format(indent + '  ', k)
                        result += cls._unwrap_mismatch(s[k], o[k],
                                                       indent + '  ')
        elif isinstance(s, list):
            if len(s) != len(o):
                result += ('differ in length (self:{} to other:{})'
                           .format(len(s), len(o)))
            else:
                for i, (s_elem, o_elem) in enumerate(zip(s, o)):
                    if s_elem != o_elem:
                        result += "\n{}Index {}:".format(indent + '  ', i)
                        result += cls._unwrap_mismatch(s_elem, o_elem,
                                                       indent + '  ')
        else:
            if type(s) != type(o):
                result += "mismatch in type self:{} != other:{}".format(
                    type(s).__name__, type(o).__name__)
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
        its class
        """
        return self.key


class DocumentLevelObject(object):

    def __init__(self, document):
        # Document level objects can be nested inside other document-level
        # objects, in which case they shouldn't belong to the document
        # directly
        # FIXME: Once network is its own element in the 9ML spec then the
        #        check for the nineml_type == 'Network' will no longer be
        #        necessary
        if document is not None and (self.name in document or
                                     self.nineml_type == 'Network'):
            self._document = document
        else:
            self._document = None

    @property
    def document(self):
        return self._document

    @property
    def url(self):
        if self.document:
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

    def write(self, fname):
        """
        Writes the top-level NineML object to file in XML.
        """
        nineml.write(self, fname)  # Calls nineml.document.Document.write


class DynamicPortsObject(object):
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


class ContainerObject(object):
    """
    An abstract base class for handling the manipulation of member objects
    (which are stored in dictionaries that can be detected by member type).

    Deriving classes are expected to have the 'class_to_member' class
    attribute
    """

    def __init__(self):
        self._indices = defaultdict(dict)

    def add(self, *elements):
        for element in elements:
            dct = self._member_dict(element)
            if element.key in dct:
                raise NineMLRuntimeError(
                    "Could not add '{}' {} to container as it clashes "
                    "with an existing element of the same name"
                    .format(element.name, type(element).__name__))
            dct[element.key] = element

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
                .format(name, self._name, self.__class__.__name__))

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
        if class_map is None:
            class_map = self.class_to_member
        if key is None:
            key = accessor_name_from_type(class_map, element)
        dct = self._indices[key]
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

    # =========================================================================
    # Each member nineml_type is associated with a member accessor by the
    # class attribute 'class_to_member' dictionary. From this name accessors
    # for the set of members of this type, and their names and length, can be
    # derrived from the stereotypical naming structure used
    # =========================================================================

    def _member_accessor(self, element_type, class_map):
        return getattr(self, accessor_name_from_type(class_map, element_type))

    def _members_iter(self, element_type, class_map):
        """
        Looks up the name of values iterator from the nineml_type of the
        element argument.
        """
        acc_name = accessor_name_from_type(class_map, element_type)
        return getattr(self, pluralise(acc_name))

    def _member_keys_iter(self, element_type, class_map):
        acc_name = accessor_name_from_type(class_map, element_type)
        try:
            return getattr(self, (acc_name + '_names'))
        except AttributeError:
            # For members that don't have proper names, such as OnConditions
            return getattr(self, (acc_name + '_keys'))

    def _num_members(self, element_type, class_map):
        acc_name = accessor_name_from_type(class_map, element_type)
        return getattr(self, 'num_' + pluralise(acc_name))

    def _member_dict(self, element_type):
        acc_name = accessor_name_from_type(self.class_to_member, element_type)
        return getattr(self, '_' + pluralise(acc_name))

    def sorted_elements(self, **kwargs):
        """Sorts the element into a consistent, logical order before write"""
        return sorted(
            self.elements(**kwargs),
            key=lambda e: (self.write_order.index(e.nineml_type),
                           str(e.key)))


def accessor_name_from_type(class_map, element_type):
    """
    Looks up the name of the accessor method from the nineml_type of the
    element argument for a given container type
    """
    if not isinstance(element_type, basestring):
        element_type = element_type.nineml_type
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


import nineml  # @IgnorePep8
