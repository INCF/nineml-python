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


class MemberContainerObject(object):
    """
    An abstract base class for handling the manipulation of member objects
    (which are stored in dictionaries that can be detected by member type).

    Deriving classes are expected to have the 'class_to_member_dict' class
    attribute
    """

    def __init__(self):
        self._indices = defaultdict(dict)

    def __iter__(self):
        return chain(*(d.itervalues() for d in self.all_member_dicts))

    def add(self, element):
        dct = self.lookup_member_dict(element)
        if element._name in dct:
            raise NineMLRuntimeError(
                "Could not add '{}' {} to component class as it clashes with "
                "an existing element of the same name"
                .format(element.name, type(element).__name__))
        dct[element._name] = element

    def remove(self, element):
        dct = self.lookup_member_dict(element)
        try:
            del dct[element._name]
        except KeyError:
            raise NineMLRuntimeError(
                "Could not remove '{}' from component class as it was not "
                "found in member dictionary (use 'ignore_missing' option "
                "to ignore)".format(element._name))

    def __contains__(self, element):
        """
        Comprehensively checks whether the element belongs to this component
        class or not. Useful for asserts and unit tests.
        """
        if isinstance(element, basestring):
            for dct in self.all_member_dicts:
                if element in dct:
                    return True
            return False
        else:
            try:
                dct = self.lookup_member_dict(element)
                try:
                    found = dct[element._name]
                    return found is element
                except KeyError:
                    return False
            except NineMLInvalidElementTypeException:
                return self._find_element(element)

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
            key = self.lookup_member_dict_name(element)
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

    def lookup_member_dict(self, element):
        """
        Looks up the appropriate member dictionary for objects of type element
        """
        return getattr(self, self.lookup_member_dict_name(element))

    def lookup_member_dict_name(self, element):
        """
        Looks up the appropriate member dictionary name for objects of type
        element
        """
        # Try quick lookup by class type
        try:
            return self.class_to_member_dict[type(element)]
        except KeyError:
            # Iterate through and find by isinstance lookup
            try:
                l = [d for clss, d in self.class_to_member_dict.iteritems()
                     if isinstance(element, clss)]
                assert len(l) < 2, ("Multiple base classes found for '{}' type"
                                    .format(type(element)))
                return l[0]
            except IndexError:
                raise NineMLInvalidElementTypeException(
                    "Could not get member dict for element of type "
                    "'{}' from '{}' class" .format(type(element).__name__,
                                                   type(self).__name__))

    @property
    def all_member_dicts(self):
        return (getattr(self, n)
                for n in self.class_to_member_dict.itervalues())


class SendPortBase(object):
    """
    Dummy class to allow look up via inheritence of SendPort in this module
    without causing circular import problems
    """


import nineml
