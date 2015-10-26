from itertools import chain
from . import BaseULObject
from .component import resolve_reference, write_reference, DynamicsProperties
from nineml.base import DocumentLevelObject
from nineml.xml import NINEML, E, unprocessed_xml, from_child_xml, get_xml_attr
from nineml.annotations import annotate_xml, read_annotations


class Population(BaseULObject, DocumentLevelObject):
    """
    A collection of spiking neurons all of the same type.

    **Arguments**:
        *name*
            a name for the population.
        *size*
            an integer, the size of neurons in the population
        *cell*
            a :class:`Component`, or :class:`Reference` to a component defining
            the cell type (i.e. the mathematical model and its
            parameterisation).
    """
    element_name = "Population"
    defining_attributes = ("name", "size", "cell")

    def __init__(self, name, size, cell, url=None):
        BaseULObject.__init__(self)
        DocumentLevelObject.__init__(self, url)
        self.name = name
        self.size = size
        self.cell = cell

    def __str__(self):
        return ("Population '{}' of size {} with dynamics '{}'"
                .format(self.name, self.size, self.cell.name, self.positions))

    def __repr__(self):
        return ("Population(name='{}', size={}, cell={}{})"
                .format(self.name, self.size, self.cell.name,
                        'positions={}'.format(self.positions)
                        if self.positions else ''))

    @property
    def component_class(self):
        return self.cell.component_class

    def get_components(self):
        """
        Return a list of all components used by the population.
        """
        components = []
        if self.cell:
            components.append(self.cell)
            components.extend(
                self.cell.get_random_distributions())
            components.extend(
                self.cell.get_random_distributions())
        return components

    @property
    def attributes_with_units(self):
        return chain(*[c.attributes_with_units for c in self.get_components()])

    @write_reference
    @annotate_xml
    def to_xml(self, document, **kwargs):
        return E(self.element_name,
                 E.Size(str(self.size)),
                 E.Cell(self.cell.to_xml(document, **kwargs)),
                 name=self.name)

    @classmethod
    @resolve_reference
    @read_annotations
    @unprocessed_xml
    def from_xml(cls, element, document, **kwargs):
        cell = from_child_xml(element, DynamicsProperties, document,
                              allow_reference=True, within='Cell', **kwargs)
        return cls(name=get_xml_attr(element, 'name', document, **kwargs),
                   size=get_xml_attr(element, 'Size', document, in_block=True,
                                     dtype=int, **kwargs),
                   cell=cell, url=document.url)


def qstr(obj):
    if isinstance(obj, basestring):
        return '"%s"' % obj
    else:
        return obj.__str__()
