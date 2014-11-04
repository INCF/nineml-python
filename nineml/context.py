# encoding: utf-8
"""
Python module for reading/writing any top level 9ml objects within a NineML
root tag.

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from . import E, NINEML
from collections import defaultdict


class Context(defaultdict):

    element_name = 'NineML'
    # A dictionary with the XML tag names as keys, and a tuple consisting of
    # the modules they are found in (imports are performed on demand to prevent
    # circular imports), the class name and the name of the identifier field 
    # (typically name)
    top_level = {'ComponentClass': ('nineml.abstraction_layer.components.base',
                                    'BaseComponentClass', 'name'),
                 'Component': ('nineml.user_layer.components.base',
                               'BasComponent', 'name'),
                 'PopulationGroup': ('nineml.user_layer.containers',
                                     'PopulationGroup', 'name'),
                 'Population', ('nineml.user_layer.population', 'Population',
                                'Projection', 'Unit', 'UnitDimension']

    def __init__(self):
        super(Context, self).__init__(dict)

    def to_xml(self):
        return E(self.element_name,
                 *(child.to_xml()
                   for child in self.itervalues()))

    @classmethod
    def from_xml(cls, element):
        if element.tag != NINEML + cls.element_name:
            raise Exception("Not a NineML root ({})".format(element.tag))
        context = cls()
        for child in element.getchildren():
            if child not in cls.top_level:
                raise TypeError("Invalid top-level element '{}' found in "
                                "NineML document (valid elements are '{}')."
                                .format(child.tag, "', '".join(cls.top_level)))
            child_cls = cls._elem_lookup[child_elem.tag]
            # Get the name of the element type and convert to lower case
            key = child_elem.tag.lower()
            # Strip namespace and add plural to get the kwarg for the
            # __init__ method of Context
            key = key[len(NINEML):] + ('s' if key[-1] != 's' else 'es')
            # Add chile to kwargs
            if key == 'components':
                child_args = (child_elem, kwargs['components'])
            else:
                child_args = (child_elem,)
            kwargs[key].append(child_cls.from_xml(*child_args))
        return cls(**kwargs)
