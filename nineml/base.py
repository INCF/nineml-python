from itertools import chain
import operator
from collections import defaultdict
from nineml.exceptions import (
    NineMLRuntimeError, NineMLInvalidElementTypeException)
from nineml.xmlns import NINEML


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

    def __eq__(self, other):
        try:
            if self.element_name != other.element_name:
                return False
        except AttributeError:
            return False
        if self.defining_attributes != other.defining_attributes:
            return False
        for name in self.defining_attributes:
            self_elem = getattr(self, name)
            other_elem = getattr(other, name)
            if not isinstance(self_elem, dict):
                # Try to sort the elements (so they are order non-specific) if
                # they are an iterable list, ask forgiveness and fall back to
                # standard equality if they aren't
                try:
                    if len(self_elem) > 1 and len(other_elem) > 1:
                        self_elem = sorted(self_elem, key=lambda x: x._name)
                        other_elem = sorted(other_elem, key=lambda x: x._name)
                except (TypeError, AttributeError):
                    pass
            if self_elem != other_elem:
                return False
        return True

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
                      .format(self.__class__.__name__))
        else:
            result = ''
        if type(self) != type(other):
            result += "mismatch in type ({} and {})".format(type(self),
                                                            type(other))
        else:
            for attr_name in self.__class__.defining_attributes:
                self_attr = getattr(self, attr_name)
                other_attr = getattr(other, attr_name)
                if self_attr != other_attr:
                    result += "\n{}Attribute '{}': ".format(indent, attr_name)
                    result += self._unwrap_mismatch(self_attr, other_attr,
                                                    indent + '  ')
        return result

    @classmethod
    def _unwrap_mismatch(cls, s, o, indent):
        result = ''
        if isinstance(s, BaseNineMLObject):
            result += s.find_mismatch(o, indent=indent + '  ')
        elif isinstance(s, dict):
            if set(s.keys()) != set(o.keys()):
                result += ('keys do not match:\n{}  {}\n{}  {})'
                           .format(indent, set(s.keys()), indent,
                                   set(o.keys())))
            else:
                for k in s:
                    if s[k] != o[k]:
                        result += "\n{}Key '{}':".format(indent + '  ', k)
                        result += cls._unwrap_mismatch(s[k], o[k],
                                                       indent + '  ')
        elif isinstance(s, list):
            if len(s) != len(o):
                result += 'differ in length ({} to {})'.format(len(s), len(o))
            else:
                for i, (s_elem, o_elem) in enumerate(zip(s, o)):
                    if s_elem != o_elem:
                        result += "\n{}Index {}:".format(indent + '  ', i)
                        result += cls._unwrap_mismatch(s_elem, o_elem,
                                                       indent + '  ')
        else:
            result += "{} != {}".format(s, o)
        return result

    @classmethod
    def check_tag(cls, element):
        assert element.tag in (cls.element_name, NINEML + cls.element_name), (
            "Found '{}' element, expected '{}'".format(element.tag,
                                                       cls.element_name))


class DocumentLevelObject(object):

    def __init__(self, url):
        self._url = url

    @property
    def url(self):
        return self._url

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


class ContainerObject(object):
    """
    An abstract base class for handling the manipulation of member objects
    (which are stored in dictionaries that can be detected by member type).

    Deriving classes are expected to have the 'class_to_member' class
    attribute
    """

    def __init__(self):
        self._indices = defaultdict(dict)

    def add(self, element):
        dct = self._member_dict(element)
        if element._name in dct:
            raise NineMLRuntimeError(
                "Could not add '{}' {} to component class as it clashes with "
                "an existing element of the same name"
                .format(element.name, type(element).__name__))
        dct[element._name] = element

    def remove(self, element):
        dct = self._member_dict(element)
        try:
            del dct[element._name]
        except KeyError:
            raise NineMLRuntimeError(
                "Could not remove '{}' from component class as it was not "
                "found in member dictionary (use 'ignore_missing' option "
                "to ignore)".format(element._name))

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

    def elements(self, as_class=None):
        """
        Iterates through all the core member elements of the container. For
        core 9ML objects this will be the same as those iterated by the
        __iter__ magic method, where as for 9ML extensions.
        """
        if as_class is None:
            as_class = type(self)
        return chain(*(self._members_iter(et, as_class=as_class)
                       for et in as_class.class_to_member))

    def element(self, name, as_class=None):
        """
        Looks a member item by "name" (identifying characteristic)
        """
        if as_class is None:
            as_class = type(self)
        for element_type in as_class.class_to_member:
            try:
                elem = self._member_accessor(
                    element_type, as_class=as_class)(name)
                # Ignore send ports as they otherwise mask
                # aliases/state variables
                if not isinstance(elem, SendPortBase):
                    return elem
            except KeyError:
                pass
        raise KeyError("'{}' was not found in '{}' {} object"
                       .format(name, self._name, as_class.__name__))

    def num_elements(self, as_class=None):
        if as_class is None:
            as_class = type(self)
        return reduce(operator.add,
                      *(self._num_members(et, as_class=as_class)
                        for et in as_class.class_to_member))

    def element_names(self, as_class=None):
        if as_class is None:
            as_class = type(self)
        for element_type in as_class.class_to_member:
            # Some of these do not meet the stereotypical *_names format, e.g.
            # time_derivative_variables, could change these to *_keys instead
            try:
                for name in self._member_names_iter(element_type,
                                                    as_class=as_class):
                    yield name
            except AttributeError:
                pass

    def __getitem__(self, name):
        """
        Looks a member item by "name" (identifying characteristic) in any of
        of the base classes in the same order as the MRO.
        """
        # Loop through all base classes to see if the name fits any member
        # of any base class
        for cls in type(self).__mro__:
            if hasattr(cls, 'class_to_member'):
                try:
                    return self.element(name, as_class=cls)
                except KeyError:
                    pass
        raise KeyError("'{}' was not found in '{}' {} object"
                       .format(name, self._name, type(self).__name__))

    def __contains__(self, element):
        """
        Checks whether the element belongs to the container object or any sub-
        containers. The element can either be a string representing a named
        object or an element that is meant to equal an element within the
        container.
        """
        if isinstance(element, basestring):
            for cls in type(self).__mro__:
                try:
                    for type_name in cls.class_to_member:
                        if element in self._member_dict(type_name):
                            return True
                        for member in self._members_iter(type_name):
                            if (isinstance(member, ContainerObject) and
                                    element in member):
                                return True
                except AttributeError:
                    pass
            return False
        else:
            return self._find_element(element)  # Lookup via full-search

    def __iter__(self):
        raise ValueError("'{}' {} container is not iterable"
                         .format(self.name, type(self).__name__))

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
        if key is None:
            for cls in type(self).__mro__:
                if hasattr(cls, 'class_to_member'):
                    try:
                        key = accessor_name_from_type(cls, element)
                    except NineMLInvalidElementTypeException:
                        pass
            if key is None:
                raise NineMLInvalidElementTypeException(
                    "Could not find member of type {} in {} or its base "
                    "classes".format(type(element), type(self)))
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
    # Each member element_name is associated with a member accessor by the
    # class attribute 'class_to_member' dictionary. From this name accessors
    # for the set of members of this type, and their names and length, can be
    # derrived from the stereotypical naming structure used
    # =========================================================================

    def _member_accessor(self, element_type, as_class=None):
        if as_class is None:
            as_class = type(self)
        return getattr(self, accessor_name_from_type(as_class,
                                                     element_type))

    def _members_iter(self, element_type, as_class=None):
        """
        Looks up the name of values iterator from the element_name of the
        element argument.
        """
        if as_class is None:
            as_class = type(self)
        return getattr(
            self, pluralise(accessor_name_from_type(as_class,
                                                    element_type)))

    def _member_names_iter(self, element_type, as_class=None):
        if as_class is None:
            as_class = type(self)
        try:
            return getattr(
                self, (accessor_name_from_type(as_class, element_type)
                       + '_names'))
        except AttributeError:
            raise AttributeError(
                "Elements of type {} aren't named".format(element_type))

    def _num_members(self, element_type, as_class=None):
        if as_class is None:
            as_class = type(self)
        return getattr(
            self, ('num_' +
                   pluralise(accessor_name_from_type(as_class,
                                                     element_type))))

    def _member_dict(self, element_type):
        return getattr(
            self, '_' + pluralise(accessor_name_from_type(
                self, element_type)))


def accessor_name_from_type(class_type, element_type):
    """
    Looks up the name of the accessor method from the element_name of the
    element argument for a given container type
    """
    if not isinstance(element_type, basestring):
        element_type = element_type.element_name
    try:
        return class_type.class_to_member[element_type]
    except KeyError:
        raise NineMLInvalidElementTypeException(
            "Could not get member attr for element of type '{}' for object "
            "'{}' container".format(element_type, class_type))


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


import nineml
