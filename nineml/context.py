# encoding: utf-8
"""
Python module for reading/writing any top level 9ml objects within a NineML
root tag.

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from . import E, NINEML
import itertools
import collections
import nineml


class Context(dict):

    element_name = 'NineML'

    ## Valid top-level NineML element names
    top_level = ['UnitDimension', 'Unit', 'ComponentClass', 'Component',
                 'Population', 'PopulationGroup', 'Projection']

    # These modules are imported here to avoid circular imports between
    # layers
    _user_layer = getattr(nineml, 'user_layer')
    _abstraction_layer = getattr(nineml, 'abstraction_layer')

    # A tuple to hold the unresolved elements
    _Unresolved = collections.namedtuple('_Unresolved', 'name elem cls')

    def __init__(self):
        # Create an empty dictionary for each valid top-level dictionary
        super(Context, self).__init__((n, {}) for n in self.top_level)
        # Stores the list of elements that are being resolved to check for
        # circular references
        self._resolving = []

    def get(self, nineml_type, name):
        """
        Returns an element in the context, lazily resolving form XML on demand
        along with other the components in the context as they are
        cross-referenced
        """
        try:
            elem_dict = super(Context, self).__getitem__[nineml_type]
        except KeyError:
            raise KeyError("'{}' not a valid top-level NineML element. Valid "
                           "elements are '{}'"
                           .format(nineml_type, "', '".join(self.top_level)))
        try:
            stored = elem_dict[name]
        except KeyError:
            raise KeyError("No '{}' elements were found in current context "
                           "with name '{}' (available '{}')."
                           .format(nineml_type, name,
                                   "', '".join(elem_dict.iterkeys())))
        if isinstance(stored, self._Unresolved):
            if stored in self._resolving:
                raise Exception("Circular reference detected in '{}:{}' "
                                "element. Resolution stack was:\n"
                                .format(stored.name,
                                        "\n".join('{}:{}'.format(e.tag, e.name)
                                                  for e in self._resolving)))
            self._resolving.append(stored)
            elem_dict[name] = stored.cls.from_xml(stored.elem, self)
            assert self._resolving[-1] is stored
            self._resolving.pop()
            stored = elem_dict[name]
        return stored

    def __getitem__(self, nineml_type):
        elem_dict = super(Context, self).__getitem__[nineml_type]
        # Make sure all elements are resolved before returning
        for name in elem_dict.iterkeys():
            self.get(nineml_type, name)
        return elem_dict

    def to_xml(self):
        return E(self.element_name,
                 *itertools.chain((child.to_xml()
                                   for child in self[type_name].itervalues())
                                  for type_name in self.top_level))

    @classmethod
    def from_xml(cls, element):
        if element.tag != NINEML + cls.element_name:
            raise Exception("Not a NineML root ('{}')".format(element.tag))
        context = cls()
        # Loop through child elements, determine the class needed to extract
        # them and add them to the dictionary
        for child in element.getchildren():
            if child.tag not in cls.top_level:
                raise TypeError("Invalid top-level element '{}' found in "
                                "NineML document (valid elements are '{}')."
                                .format(child.tag, "', '".join(cls.top_level)))
            # Units use 'symbol' as their unique identifier (from LEMS) all
            # other elements use 'name'
            name = child.attrib.get('name', child.attrib.get('symbol'))
            # Try to get child attribute from user_layer, failing that try
            # abstraction layer
            try:
                child_cls = getattr(cls._user_layer, child.tag)
            except ImportError:
                child_cls = getattr(cls._abstraction_layer, child.tag)
            context[child.tag][name] = cls._Unresolved(name, child, child_cls)
        return context
