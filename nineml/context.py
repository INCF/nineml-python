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


class Context(dict):

    element_name = 'NineML'

    ## Valid top-level NineML element names
    top_level = ['UnitDimension', 'Unit', 'ComponentClass', 'Component',
                 'Population', 'PopulationGroup', 'Projection']

    # A tuple to hold the unresolved elements
    _Unresolved = collections.namedtuple('_Unresolved', 'name xml cls')

    def __init__(self):
        # Create an empty dictionary for each valid top-level dictionary
        super(Context, self).__init__((n, {}) for n in self.top_level)
        # Stores the list of elements that are being resolved to check for
        # circular references
        self._resolving = []

    def __getitem__(self, nineml_type):
        """
        Returns a dictionary containing resolved 9ml objects for all elements
        matching the `nineml_type`
        """
        try:
            elem_dict = super(Context, self).__getitem__[nineml_type]
        except KeyError:
            raise KeyError("'{}' not a valid top-level NineML element. Valid "
                           "elements are '{}'"
                           .format(nineml_type, "', '".join(self.top_level)))
        # Make sure all elements are resolved before returning
        for elem in elem_dict.itervalues():
            if isinstance(elem, self._Unresolved):
                self._resolve(elem, elem_dict)
        return elem_dict

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
            elem = elem_dict[name]
        except KeyError:
            raise KeyError("No '{}' elements were found in current context "
                           "with name '{}' (available '{}')."
                           .format(nineml_type, name,
                                   "', '".join(elem_dict.iterkeys())))
        if isinstance(elem, self._Unresolved):
            elem = self._resolve(elem, elem_dict)
        return elem

    def _resolve(self, unresolved, elem_dict):
        """
        Resolve an element from its XML description and store back in the
        element dictionary
        """
        if unresolved in self._resolving:
            raise Exception("Circular reference detected in '{}(name={})' "
                            "element. Resolution stack was:\n"
                            .format(unresolved.name,
                                    "\n".join('{}(name={})'.format(u.tag,
                                                                   u.name)
                                              for u in self._resolving)))
        self._resolving.append(unresolved)
        elem_dict[unresolved.name] = unresolved.cls.from_xml(unresolved.xml,
                                                             self)
        assert self._resolving[-1] is unresolved
        self._resolving.pop()
        return elem_dict[unresolved.name]

    def to_xml(self):
        return E(self.element_name,
                 *itertools.chain((child.to_xml()
                                   for child in self[type_name].itervalues())
                                  for type_name in self.top_level))

    @classmethod
    def from_xml(cls, element):
        if element.tag != NINEML + cls.element_name:
            raise Exception("Not a NineML root ('{}')".format(element.tag))
        # These modules are imported here to avoid circular imports between
        # layers. Can you think of a better way to do this Andrew?
        from nineml import user_layer
        from nineml import abstraction_layer
        # Initialise the context
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
                child_cls = getattr(user_layer, child.tag)
            except ImportError:
                child_cls = getattr(abstraction_layer, child.tag)
            context[child.tag][name] = cls._Unresolved(name, child, child_cls)
        return context
