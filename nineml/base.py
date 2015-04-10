from itertools import chain
from collections import defaultdict
from nineml.exceptions import (
    NineMLRuntimeError, NineMLInvalidElementTypeException)


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
        if not (isinstance(other, self.__class__) or
                isinstance(self, other.__class__)):
            return False
        for name in self.defining_attributes:
            self_elem = getattr(self, name)
            other_elem = getattr(other, name)
            if not isinstance(self_elem, dict):
                # Try to sort the elements (so they are order non-specific) if
                # they are an iterable list, ask forgiveness and fall back to
                # standard equality if they aren't
                try:
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
                try:
                    self_attr = getattr(self, attr_name)
                    other_attr = getattr(other, attr_name)
                except:
                    raise
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
                result += ('keys do not match ({} and {})'
                           .format(set(s.keys()), set(o.keys())))
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


class TopLevelObject(object):

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


class MemberContainerObject(object):
    """
    An abstract base class for handling the manipulation of member objects
    (which are stored in dictionaries that can be detected by member type).

    Deriving classes are expected to have the '_class_to_member' class
    attribute
    """

    def __init__(self):
        self._indices = defaultdict(dict)

    def elements(self):
        return chain(*(d.itervalues() for d in self._all_member_dicts))

    def add(self, element):
        dct = self._member_dict(element)
        if element.name in dct:
            raise NineMLRuntimeError(
                "Could not add '{}' {} to component class as it clashes with "
                "an existing element of the same name"
                .format(element.name, type(element).__name__))
        dct[element.name] = element

    def remove(self, element, ignore_missing=False):
        dct = self._member_dict(element)
        try:
            del dct[element.name]
        except KeyError:
            if not ignore_missing:
                raise NineMLRuntimeError(
                    "Could not remove '{}' from component class as it was not "
                    "found in member dictionary".format(element.name))

    def __getitem__(self, name):
        for dct in self._all_member_dicts:
            try:
                return dct[name]
            except KeyError:
                pass
        raise KeyError("'{}' was not found in '{}' component class"
                       .format(name, self.name))

    def __contains__(self, element):
        """
        Comprehensively checks whether the element belongs to this component
        class or not. Useful for asserts and unit tests.
        """
        if isinstance(element, basestring):
            try:
                self[element]
            except KeyError:
                return False
        else:
            try:
                dct = self._member_dict(element)
                try:
                    found = dct[element.name]
                    assert(found == element)
                    return True
                except KeyError:
                    return False
            except NineMLInvalidElementTypeException:
                return self._find_element(element)

    @property
    def _all_member_dicts(self):
        return chain(*([m.itervalues() for m in self._class_to_member] +
                       [m.itervalues()
                        for m in self._main_block._class_to_member]))

    @property
    def elements(self):
        return chain(*(d.itervalues() for d in self._all_member_dicts))

    def index_of(self, element, key=None):
        """
        Returns the index of an element amongst others of its type. The indices
        are generated on demand but then remembered to allow them to be
        referred to again.

        This function is meant to be useful in code-generation, where an
        name of an element can be replaced with a unique integer value (and
        referenced elsewhere in the code).
        """
        if key is None:
            key = self._member_dict_name(element)
        dct = self._indices[key]
        try:
            index = dct[element]
        except KeyError:
            # Get the first index ascending from 0 not in the set
            try:
                index = next(iter(sorted(
                    set(xrange(len(dct)).difference(dct.itervalues())))))
            except:
                index = len(dct)
            dct[element] = index
        return index

    def _member_dict_name(self, element):
        # Try quick lookup by class type
        try:
            return self._class_to_member[type(element)]
        except KeyError:
            # For component classes with "main blocks" (to be removed in
            # version 2.0)
            try:
                return self._main_block._class_to_member[type(element)]
            except (AttributeError, KeyError):
                pass
        try:
            return next(
                d for cls, d in self._class_to_member.iteritems()
                if isinstance(element, cls))
        except StopIteration:
            # For component classes with "main blocks" (to be removed in
            # version 2.0)
            try:
                return next(
                    d for cls, d in
                    self._main_block._class_to_member.iteritems()
                    if isinstance(element, cls))
            except (AttributeError, StopIteration):
                raise NineMLInvalidElementTypeException(
                    "Could not get member dict for element of type "
                    "'{}' to '{}' class"
                    .format(element.__class__.__name__,
                            self.__class__.__name__))

    def _member_dict(self, element):
        name = self._member_dict_name(element)
        try:
            return getattr(self, name)
        except AttributeError:
            return getattr(self._main_block, name)


import nineml
