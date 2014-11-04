# encoding: utf-8
"""
Python module for reading/writing any top level 9ml objects within a NineML
root tag.

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from . import E, NINEML
from .utility import expect_single
import collections


class Context(dict):

    element_name = 'NineML'

    ## Valid top-level NineML element names
    top_level = ['UnitDimension', 'Unit', 'ComponentClass', 'Component',
                 'PositionList', 'Population', 'PopulationGroup', 'Projection']

    # A tuple to hold the unresolved elements
    _Unloaded = collections.namedtuple('_Unloaded', 'name xml cls')

    def __init__(self, *args, **kwargs):
        super(Context, self).__init__(*args, **kwargs)
        # Stores the list of elements that are being loaded to check for
        # circular references
        self._loading = []
        self.url = None

    def __getitem__(self, name):
        """
        Returns the element referenced by the given name
        """
        try:
            elem = super(Context, self)[name]
        except KeyError:
            raise KeyError("'{}' was not found in the NineML context{} ("
                           "elements in the context were '{}')."
                           .format(name, self.url or '',
                                   "', '".join(self.iterkeys())))
        if isinstance(elem, self._Unloaded):
            elem = self._load_elem_from_xml(elem)
        return elem

    def _load_elem_from_xml(self, unloaded):
        """
        Resolve an element from its XML description and store back in the
        element dictionary
        """
        if unloaded in self._loading:
            raise Exception("Circular reference detected in '{}(name={})' "
                            "element. Resolution stack was:\n"
                            .format(unloaded.name,
                                    "\n".join('{}(name={})'.format(u.tag,
                                                                   u.name)
                                              for u in self._loading)))
        self._loading.append(unloaded)
        elem = unloaded.cls.from_xml(unloaded.xml, self)
        assert self._loading[-1] is unloaded
        self._loading.pop()
        super(Context, self)[unloaded.name] = elem
        return elem

    def to_xml(self):
        return E(self.element_name,
                 *[c.to_xml() for c in self.itervalues()])

    @classmethod
    def from_xml(cls, element, url=None):
        if element.tag != NINEML + cls.element_name:
            raise Exception("Not a NineML root ('{}')".format(element.tag))
        # These modules are imported here to avoid circular imports between
        # layers. Can you think of a better way to do this Andrew?
        from nineml import user_layer
        from nineml import abstraction_layer
        # Initialise the context
        context = cls()
        # This isn't set in the constructor to avoid screwing up the standard
        # dictionary constructor
        context.url = url
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
            context[child.tag][name] = cls._Unloaded(name, child, child_cls)
        return context
