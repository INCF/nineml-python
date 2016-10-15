from itertools import chain
import operator
from collections import defaultdict
from nineml.exceptions import (
    NineMLRuntimeError, NineMLNameError, NineMLInvalidElementTypeException)


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
                self_elem = getattr(self, name)
                other_elem = getattr(other, name)
            except AttributeError:
                # This is when comparing to derived classes that don't contain
                # the member dictionary, just an iterator over generated
                # members, e.g. _Namespace* classes. NB: The member iterator
                # could in principle be used for all cases, however that would
                # miss mis-matching dictionary keys (which shouldn't happen but
                # are tested using __eq__ in unit-tests just to make sure).
                if name.startswith('_'):
                    name = name[1:]
                    self_elem = getattr(self, name)
                    other_elem = getattr(other, name)
                else:
                    raise
            if not isinstance(self_elem,
                              (dict, basestring, nineml.values.BaseValue)):
                # Try to sort the elements by their '_name' attribute (so they
                # are order non-specific) if they are an iterable
                try:
                    self_elem = sorted(self_elem, key=lambda x: str(x._name))
                    other_elem = sorted(other_elem, key=lambda x: str(x._name))
                except (TypeError, ValueError, AttributeError):
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
        try:
            if self.nineml_type != other.nineml_type:
                result += ("mismatch in nineml_type, self:'{}' and other:'{}'"
                           .format(self.nineml_type, other.nineml_type))
            else:
                for attr_name in self.__class__.defining_attributes:
                    self_attr = getattr(self, attr_name)
                    other_attr = getattr(other, attr_name)
                    if self_attr != other_attr:
                        result += "\n{}Attribute '{}': ".format(indent,
                                                                attr_name)
                        result += self._unwrap_mismatch(self_attr, other_attr,
                                                        indent + '  ')
        except:
            raise
        return result

    @classmethod
    def _unwrap_mismatch(cls, s, o, indent):
        result = ''
        if isinstance(s, BaseNineMLObject):
            result += s.find_mismatch(o, indent=indent + '  ')
        elif isinstance(s, dict):
            if set(s.keys()) != set(o.keys()):
                result += (
                    "keys do not match:\n{}  self:{}\n{}  other:{}".format(
                        indent,
                        ", ".join("'{}'".format(k) if isinstance(k, basestring)
                                  else str(k) for k in sorted(s.keys())),
                        indent,
                        ", ".join("'{}'".format(k) if isinstance(k, basestring)
                                  else str(k) for k in sorted(o.keys()))))
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
            result += "self:{} != other:{}".format(s, o)
        return result


class DocumentLevelObject(object):

    def __init__(self, document):
        self._document = document

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

    def element(self, name, class_map=None):
        """
        Looks a member item by "name" (identifying characteristic)
        """
        if class_map is None:
            class_map = self.class_to_member
        for element_type in class_map:
            try:
                elem = self._member_accessor(
                    element_type, class_map=class_map)(name)
                # Ignore send ports as they otherwise mask
                # aliases/state variables
                if not isinstance(elem, SendPortBase):
                    return elem
            except NineMLNameError:
                pass
        raise NineMLNameError(
            "'{}' was not found in '{}' {} object"
            .format(name, self._name, self.__class__.__name__))

    def num_elements(self, class_map=None):
        if class_map is None:
            class_map = self.class_to_member
        return reduce(operator.add,
                      *(self._num_members(et, class_map=class_map)
                        for et in class_map))

    def element_names(self, class_map=None):
        if class_map is None:
            class_map = self.class_to_member
        for element_type in class_map:
            # Some of these do not meet the stereotypical *_names format, e.g.
            # time_derivative_variables, could change these to *_keys instead
            try:
                for name in self._member_names_iter(element_type,
                                                    class_map=class_map):
                    yield name
            except AttributeError:
                pass

    def __iter__(self):
        raise ValueError("'{}' {} container is not iterable"
                         .format(self.name, type(self).__name__))

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
        return getattr(
            self, pluralise(accessor_name_from_type(class_map, element_type)))

    def _member_names_iter(self, element_type, class_map):
        try:
            return getattr(
                self, (accessor_name_from_type(class_map, element_type)
                       + '_names'))
        except AttributeError:
            raise AttributeError(
                "Elements of type {} aren't named".format(element_type))

    def _num_members(self, element_type, class_map):
        return getattr(
            self, (
                'num_' +
                pluralise(accessor_name_from_type(class_map, element_type))))

    def _member_dict(self, element_type):
        return getattr(
            self, '_' + pluralise(accessor_name_from_type(self.class_to_member,
                                                          element_type)))

    def sorted_elements(self, **kwargs):
        """Sorts the element into a consistent, logical order before write"""
        return sorted(
            self.elements(**kwargs),
            key=lambda e: (self.write_order.index(e.nineml_type),
                           str(e._name)))


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


import nineml
