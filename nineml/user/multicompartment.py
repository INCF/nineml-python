from itertools import chain
from . import BaseULObject
from abc import ABCMeta
from nineml.reference import resolve_reference, write_reference
from nineml import DocumentLevelObject
from nineml.xmlns import NINEML, E
from nineml.utils import expect_single
from nineml.annotations import annotate_xml, read_annotations
from .values import ArrayValue


class MultiCompartment(BaseULObject, DocumentLevelObject):
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
        *positions*
            TODO: need to check if positions/structure are in the v1 spec
    """
    element_name = "MultiCompartment"
    defining_attributes = ('name', 'branches', 'mapping', 'domains')

    def __init__(self, name, branches, mapping, domains, url=None):
        BaseULObject.__init__(self)
        DocumentLevelObject.__init__(self, url)
        self._name = name
        self._domains = domains
        self._mapping = mapping
        self._branches = branches

    @property
    def name(self):
        return self._name

    def __str__(self):
        return ('MultiCompartment "%s": %dx"%s" %s' %
                (self.name, self.size, self.cell.name, self.positions))

    @property
    def attributes_with_units(self):
        return chain(*[d.attributes_with_units for d in self.domains])

    @write_reference
    @annotate_xml
    def to_xml(self):
        return E(self.element_name,
                 self.branches.to_xml(),
                 self.mapping.to_xml(),
                 *[d.to_xml() for d in self.domains],
                 name=self.name)

    @classmethod
    @resolve_reference
    @read_annotations
    def from_xml(cls, element, document):
        cls.check_tag(element)
        branches = Branches.from_xml(
            expect_single(element.findall(NINEML + 'Branches')), document)
        mapping = Mapping.from_xml(
            expect_single(element.findall(NINEML + 'Mapping')), document)
        domains = [Domain.from_xml(e, document)
                   for e in element.findall(NINEML + 'Domain')]
        return cls(name=element.attrib['name'], branches, mapping, domains)


class IndexArray(BaseULObject):

    """
    Representation of a numerical- or string-valued parameter.

    A numerical parameter is a (name, value, units) triplet, a string parameter
    is a (name, value) pair.

    Numerical values may either be numbers, or a component_class that generates
    numbers, e.g. a RandomDistribution instance.
    """
    __metaclass__ = ABCMeta  # Abstract base class

    defining_attributes = ("_values",)

    def __init__(self, values):
        self._values = values

    @property
    def values(self):
        return self._values

    @annotate_xml
    def to_xml(self):
        return E(self.element_name,
                 self._values.to_xml(),
                 units=self.units.name)

    @classmethod
    @read_annotations
    def from_xml(cls, element, document):
        values = ArrayValue.from_xml(
            expect_single(element.findall(NINEML + 'ArrayValue')), document)
        return cls(values)


class Branches(IndexArray):
    pass


class Mapping(IndexArray):
    pass


class Domain(BaseULObject):

    def __init__(self, dynamics, port_connections):
        self._dynamics = dynamics
        self._port_connections = port_connections

    def to_xml(self):
        