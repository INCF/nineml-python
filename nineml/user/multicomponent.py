from itertools import chain
from . import BaseULObject
from abc import ABCMeta
from nineml.reference import resolve_reference, write_reference
from nineml import DocumentLevelObject
from nineml.xmlns import NINEML, E
from nineml.utils import expect_single
from nineml.user import DynamicsProperties
from nineml.annotations import annotate_xml, read_annotations
from .values import ArrayValue
from nineml.exceptions import NineMLRuntimeError
from .port_connections import PortConnection, Sender


class MultiComponent(BaseULObject, DocumentLevelObject):

    element_name = "MultiComponent"

    def __init__(self, name, subcomponents, port_exposures):
        super(MultiComponent, self).__init__()
        self._name = name
        self._subcomponents = subcomponents
        self._port_exposures = port_exposures

    @property
    def name(self):
        return self._name

    @property
    def subcomponents(self):
        return self._subcomponents

    @property
    def port_exposures(self):
        return self._port_exposures

    @property
    def attributes_with_units(self):
        return chain(*[c.attributes_with_units for c in self.subcomponents])

    @write_reference
    @annotate_xml
    def to_xml(self):
        return E(self.element_name,
                 *chain((c.to_xml() for c in self.subcomponents),
                        (pe.to_xml() for pe in self.port_exposures)),
                 name=self.name)

    @classmethod
    @resolve_reference
    @read_annotations
    def from_xml(cls, element, document):
        cls.check_tag(element)
        subcomponents = [SubComponent.from_xml(e, document)
                         for e in element.findall(NINEML + 'SubComponent')]
        port_exposures = [PortExposure.from_xml(e, document)
                          for e in element.findall(NINEML + 'PortExposure')]
        return cls(name=element.attrib['name'],
                   subcomponents=subcomponents, port_exposures=port_exposures)


class PortExposure(BaseULObject):

    element_name = 'PortExposure'

    def __init__(self, name, component, port):
        super(PortExposure, self).__init__()
        self._name = name
        self._component = component
        self._port = port

    @property
    def name(self):
        return self._name

    @property
    def component(self):
        return self._component

    @property
    def port(self):
        return self._port

    @property
    def attributes_with_units(self):
        return chain(*[c.attributes_with_units for c in self.subcomponents])

    @write_reference
    @annotate_xml
    def to_xml(self):
        return E(self.element_name,
                 name=self.name,
                 component=self.component,
                 port=self.port)

    @classmethod
    @resolve_reference
    @read_annotations
    def from_xml(cls, element, document):  # @UnusedVariable
        cls.check_tag(element)
        return cls(name=element.attrib['name'],
                   component=element.attrib['component'],
                   port=element.attrib['port'])


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
    defining_attributes = ('name', 'tree', 'mapping', 'domains')

    def __init__(self, name, tree, mapping, domains, url=None):
        BaseULObject.__init__(self)
        DocumentLevelObject.__init__(self, url)
        self._name = name
        self._domains = domains
        self._mapping = mapping
        self._tree = tree

    @property
    def name(self):
        return self._name

    @property
    def domains(self):
        return self._domains

    @property
    def mapping(self):
        return self._mapping

    @property
    def tree(self):
        return self._tree

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
                 self.tree.to_xml(),
                 self.mapping.to_xml(),
                 *[d.to_xml() for d in self.domains],
                 name=self.name)

    @classmethod
    @resolve_reference
    @read_annotations
    def from_xml(cls, element, document):
        cls.check_tag(element)
        tree = Tree.from_xml(
            expect_single(element.findall(NINEML + 'Tree')), document)
        mapping = Mapping.from_xml(
            expect_single(element.findall(NINEML + 'Mapping')), document)
        domains = [Domain.from_xml(e, document)
                   for e in element.findall(NINEML + 'Domain')]
        return cls(name=element.attrib['name'], tree=tree, mapping=mapping,
                   domains=domains)


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
        super(IndexArray, self).__init__()
        self._values = values

    @property
    def values(self):
        return self._values

    @annotate_xml
    def to_xml(self):
        return E(self.element_name,
                 ArrayValue(self._values).to_xml())

    @classmethod
    @read_annotations
    def from_xml(cls, element, document):
        array = ArrayValue.from_xml(
            expect_single(element.findall(NINEML + 'ArrayValue')), document)
        return cls(array.values)


class Tree(IndexArray):

    element_name = "Tree"


class Mapping(IndexArray):

    element_name = "Mapping"


class SubComponent(BaseULObject):

    element_name = 'SubComponent'

    def __init__(self, name, dynamics, port_connections):
        BaseULObject.__init__(self)
        self._name = name
        self._dynamics = dynamics
        self._port_connections = port_connections

    @property
    def name(self):
        return self._name

    @property
    def dynamics(self):
        return self._dynamics

    @property
    def port_connections(self):
        return self._port_connections

    @property
    def attributes_with_units(self):
        return self._dynamics.attributes_with_units

    @annotate_xml
    def to_xml(self):
        return E(self.element_name, self._dynamics.to_xml(),
                 *[pc.to_xml() for pc in self._port_connections])

    @classmethod
    @read_annotations
    def from_xml(cls, element, document):
        try:
            dynamics = DynamicsProperties.from_xml(expect_single(
                element.findall(NINEML + 'DynamicsProperties')), document)
        except NineMLRuntimeError:
            dynamics = MultiComponent.from_xml(expect_single(
                element.findall(NINEML + 'MultiComponent')), document)
        port_connections = [
            PortConnection.from_xml(e, document)
            for e in element.findall(NINEML + 'PortConnection')]
        return cls(dynamics, port_connections)


class Domain(SubComponent):

    element_name = 'Domain'

    def __init__(self, index, dynamics, port_connections):
        BaseULObject.__init__(self)
        super(Domain, self).__init__(str(index), dynamics, port_connections)
        self._index = index

    @property
    def index(self):
        return self._index


class FromSibling(Sender):

    element_name = 'FromSibling'

    def __init__(self, component, port):
        super(FromSibling, self).__init__(port)
        self.component = component

    def key(self):
        """
        Generates a unique key for the Sender so it can be stored in a dict
        """
        return (self.element_name, self.component, self._port_name)

    @annotate_xml
    def to_xml(self):
        return E(self.element_name, component=self.component,
                 port=self.port_name)

    @classmethod
    @read_annotations
    def _from_xml(cls, element, document):  # @UnusedVariable
        cls.check_tag(element)
        return cls(component=element.attrib['component'],
                   port=element.attrib['port'])


class MultiCompartmentSender(Sender):

    def __init__(self, port, domain=None):
        super(MultiCompartmentSender, self).__init__(port)
        self.domain = domain

    def key(self):
        """
        Generates a unique key for the Sender so it can be stored in a dict
        """
        return (self.element_name, self.domain, self._port_name)

    @annotate_xml
    def to_xml(self):
        kwargs = {'port': self.port_name}
        if self.domain:
            kwargs['domain'] = str(self.domain)
        return E(self.element_name, **kwargs)

    @classmethod
    @read_annotations
    def _from_xml(cls, element, document):  # @UnusedVariable
        cls.check_tag(element)
        return cls(domain=element.attrib['domain'],
                   port=element.attrib['port'])


class FromProximal(MultiCompartmentSender):

    element_name = 'FromProximal'


class FromDistal(MultiCompartmentSender):

    element_name = 'FromDistal'
