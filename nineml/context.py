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

    top_level = ['ComponentClass', 'Component', 'PopulationGroup',
                 'Population', 'Projection', 'Unit', 'UnitDimension']
    _elem_lookup = dict((NINEML + e.element_name, e)
                        for e in TOP_LEVEL_ELEMS)

#     def __init__(self, componentclasses=[], components=[], groups=[],
#                  populations=[], projections=[]):
#         self.component_classes = dict((c.name, c) for c in componentclasses)
#         self.components = dict((c.name, c) for c in components)
#         self.groups = dict((g.name, g) for g in groups)
#         self.populations = dict((p.name, p) for p in populations)
#         self.projections = dict((p.name, p) for p in projections)

    def to_xml(self):
        return E(self.element_tag,
                 *(c.to_xml() for c in self.children))

    @classmethod
    def from_xml(cls, element):
        if element.tag != NINEML + cls.element_name:
            raise Exception("Not a NineML root ({})".format(element.tag))
        kwargs = defaultdict(list)
        for child_elem in element.getchildren():
            try:
                child_cls = cls._elem_lookup[child_elem.tag]
            except KeyError:
                raise Exception("NineML root element contains invalid element "
                                "'{}'".format(child_elem.tag))
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
