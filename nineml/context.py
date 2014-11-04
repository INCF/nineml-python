# encoding: utf-8
"""
Python module for reading/writing any top level 9ml objects within a NineML
root tag.

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from . import E, NINEML
from .utility import expect_single
import itertools
import collections
from . import user_layer
from . import abstraction_layer
from .user_layer.components.base import Reference


class Context(dict):

    element_name = 'NineML'

    ## Valid top-level NineML element names
    top_level_abstraction = ['ComponentClass']
    top_level_user = ['UnitDimension', 'Unit', 'Component', 'PositionList',
                      'Population', 'PopulationGroup', 'Projection']

    # A tuple to hold the unresolved elements
    _Unloaded = collections.namedtuple('_Unloaded', 'name xml cls')

    @property
    @classmethod
    def top_level(cls):
        return itertools.chain(cls.top_level_abstraction, cls.top_level_user)

    def __init__(self, *args, **kwargs):
        super(Context, self).__init__(*args, **kwargs)
        # Stores the list of elements that are being loaded to check for
        # circular references
        self._loading = []
        self.url = None

    def resolve_ref(self, containing_elem, expected_type):
        elem = expect_single(containing_elem.getchildren())
        if elem.tag == NINEML + Reference.element_name:
            ref = Reference.from_xml(elem, self)
            if not isinstance(ref.object, expected_type):
                raise Exception("Type of referenced object ('{}') does not "
                                "match expected type ('{}')"
                                .format(ref.object.__class__, expected_type))
            obj = ref.object
        else:
            obj = expected_type.from_xml(elem, self)
        return obj

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
        # Initialise the context
        context = cls()
        # This isn't set in the constructor to avoid screwing up the standard
        # dictionary constructor
        context.url = url
        # Loop through child elements, determine the class needed to extract
        # them and add them to the dictionary
        for child in element.getchildren():
            if child.tag in cls.top_level_user:
                child_cls = getattr(user_layer, child.tag)
            elif child.tag in cls.top_level_abstraction:
                child_cls = getattr(abstraction_layer, child.tag)
            else:
                raise TypeError("Invalid top-level element '{}' found in "
                                "NineML document (valid elements are '{}')."
                                .format(child.tag, "', '".join(cls.top_level)))
            # Units use 'symbol' as their unique identifier (from LEMS) all
            # other elements use 'name'
            name = child.attrib.get('name', child.attrib.get('symbol'))
            context[child.tag][name] = cls._Unloaded(name, child, child_cls)
        return context
