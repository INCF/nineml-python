from itertools import chain
from . import BaseULObject
from abc import ABCMeta
from nineml.abstraction import (
    Dynamics, Alias, TimeDerivative, Regime, AnalogSendPort, AnalogReceivePort,
    AnalogReducePort, EventSendPort, EventReceivePort, OnEvent, OnCondition,
    StateAssignment, Trigger, OutputEvent, StateVariable)
from nineml.reference import resolve_reference, write_reference
from nineml import DocumentLevelObject
from nineml.xmlns import NINEML, E
from nineml.utils import expect_single, normalise_parameter_as_list
from nineml.user import DynamicsProperties
from nineml.annotations import annotate_xml, read_annotations
from nineml.values import ArrayValue
from nineml.exceptions import NineMLRuntimeError
from .port_connections import AnalogPortConnection, EventPortConnection


class MultiDynamicsProperties(DynamicsProperties):

    element_name = "MultiDynamics"
    defining_attributes = ('_name', '_sub_dynamics_properties',
                           '_port_exposures', '_port_connections')

    def __init__(self, name, sub_dynamics_properties, port_connections,
                 port_exposures=[]):
        BaseULObject.__init__(self)
        DocumentLevelObject.__init__(self)
        self._name = name
        self._sub_dynamics_properties = dict((c.name, c)
                                             for c in sub_dynamics_properties)
        self._port_exposures = dict((pe.name, pe) for pe in port_exposures)
        self._port_connections = []
        for port_connection in port_connections:
            snd_name, rcv_name, snd_port_name, _ = port_connection
            sender = self.subcomponent(snd_name).component.component_class
            receiver = self.subcomponent(rcv_name).component.component_class
            if isinstance(port_connection, tuple):
                if sender.port(snd_port_name).communication_type == 'analog':
                    PortConnectionClass = AnalogPortConnection
                else:
                    PortConnectionClass = EventPortConnection
                port_connection = PortConnectionClass(*port_connection)
            port_connection.bind_ports(sender, receiver)
            self._port_connections.append(port_connection)

    @property
    def name(self):
        return self._name

    @property
    def sub_dynamics_properties(self):
        return self._sub_dynamics_properties.itervalues()

    @property
    def port_connections(self):
        return iter(self._port_connections)

    @property
    def port_exposures(self):
        return self._port_exposures.itervalues()

    def sub_dynamics_properties_element(self, name):
        return self._dynamics_properties[name]

    def port_exposure(self, name):
        return self._port_exposures[name]

    @property
    def sub_component_names(self):
        return self.sub_dynamics_properties.iterkeys()

    @property
    def port_exposure_names(self):
        return self._port_exposures.iterkeys()

    @property
    def attributes_with_units(self):
        return chain(*[c.attributes_with_units
                       for c in self.sub_dynamics_properties])

    @write_reference
    @annotate_xml
    def to_xml(self, document, **kwargs):
        members = [c.to_xml(document, **kwargs)
                   for c in self.sub_dynamics_properties]
        members.extend(pe.to_xml(document, **kwargs)
                        for pe in self.port_exposures)
        members.extend(pc.to_xml(document, **kwargs)
                       for pc in self.port_connections)
        return E(self.element_name, *members, name=self.name)

    @classmethod
    @resolve_reference
    @read_annotations
    def from_xml(cls, element, document, **kwargs):
        cls.check_tag(element)
        sub_dynamics_properties = [
            SubDynamicsProperties.from_xml(e, document, **kwargs)
            for e in element.findall(NINEML + 'SubDynamics')]
        port_exposures = [
            AnalogSendPortExposure.from_xml(e, document, **kwargs)
            for e in element.findall(NINEML + 'AnalogSendPortExposure')]
        port_exposures.extend(
            AnalogReceivePortExposure.from_xml(e, document, **kwargs)
            for e in element.findall(NINEML + 'AnalogReceivePortExposure'))
        port_exposures.extend(
            AnalogReducePortExposure.from_xml(e, document, **kwargs)
            for e in element.findall(NINEML + 'AnalogReducePortExposure'))
        port_exposures.extend(
            EventSendPortExposure.from_xml(e, document, **kwargs)
            for e in element.findall(NINEML + 'EventSendPortExposure'))
        port_exposures.extend(
            EventReceivePortExposure.from_xml(e, document, **kwargs)
            for e in element.findall(NINEML + 'EventReceivePortExposure'))
        analog_port_connections = [
            AnalogPortConnection.from_xml(e, document, **kwargs)
            for e in element.findall(NINEML + 'AnalogPortConnection')]
        event_port_connections = [
            EventPortConnection.from_xml(e, document, **kwargs)
            for e in element.findall(NINEML + 'EventPortConnection')]
        return cls(name=element.attrib['name'],
                   sub_dynamics_properties=sub_dynamics_properties,
                   port_exposures=port_exposures,
                   port_connections=chain(analog_port_connections,
                                          event_port_connections))


class SubDynamicsProperties(BaseULObject):

    element_name = 'SubDynamicsProperties'
    defining_attributes = ('_name', '_dynamics')

    def __init__(self, name, dynamics_properties):
        BaseULObject.__init__(self)
        self._name = name
        self._dynamics_properties = dynamics_properties

    @property
    def name(self):
        return self._name

    @property
    def dynamics_properties(self):
        return self._dynamics_properties

    @property
    def attributes_with_units(self):
        return self._dynamics.attributes_with_units

    @annotate_xml
    def to_xml(self, document, **kwargs):  # @UnusedVariable
        return E(self.element_name, self._dynamics.to_xml(document, **kwargs),
                 name=self.name)

    @classmethod
    @read_annotations
    def from_xml(cls, element, document, **kwargs):
        try:
            dynamics_properties = DynamicsProperties.from_xml(
                expect_single(
                    element.findall(NINEML + 'DynamicsProperties')),
                document, **kwargs)
        except NineMLRuntimeError:
            dynamics_properties = MultiDynamicsProperties.from_xml(
                expect_single(
                    element.findall(NINEML + 'MultiDynamics')),
                document, **kwargs)
        return cls(element.attrib['name'], dynamics_properties)


class MultiDynamics(Dynamics):
    pass


class SubDynamics(Dynamics):
    pass


class MultiRegime(Regime):
    pass


class NamespaceStateVariable(StateVariable):
    pass


class NamespaceAlias(Alias):
    pass


class NamespaceTimeDerivative(TimeDerivative):
    pass


class NamespaceOnEvent(OnEvent):
    pass


class NamespaceOnCondition(OnCondition):
    pass


class NamespaceStateAssignment(StateAssignment):
    pass


class NamespaceTrigger(Trigger):
    pass


class NamespaceOutputEvent(OutputEvent):
    pass


class LocalAnalogPortConnection(AnalogPortConnection, Alias):

    def __init__(self):
        pass


class LocalEventPortConnection(EventPortConnection):

    def __init__(self):
        raise NotImplementedError(
            "Local event port connections are not currently "
            "supported")


class BasePortExposure(BaseULObject):

    defining_attributes = ('_name', '_component', '_port')

    def __init__(self, name, component, port):
        super(BasePortExposure, self).__init__()
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
        return chain(*[c.attributes_with_units for c in self.sub_dynamics])

    @write_reference
    @annotate_xml
    def to_xml(self, document, **kwargs):  # @UnusedVariable
        return E(self.element_name,
                 name=self.name,
                 component=self.component,
                 port=self.port)

    @classmethod
    @resolve_reference
    @read_annotations
    def from_xml(cls, element, document, **kwargs):  # @UnusedVariable
        cls.check_tag(element)
        return cls(name=element.attrib['name'],
                   component=element.attrib['component'],
                   port=element.attrib['port'])


class AnalogSendPortExposure(BasePortExposure, AnalogSendPort):

    element_name = 'AnalogSendPortExposure'


class AnalogReceivePortExposure(BasePortExposure, AnalogReceivePort):

    element_name = 'AnalogReceivePortExposure'


class AnalogReducePortExposure(BasePortExposure, AnalogReducePort):

    element_name = 'AnalogReducePortExposure'


class EventSendPortExposure(BasePortExposure, EventSendPort):

    element_name = 'EventSendPortExposure'


class EventReceivePortExposure(BasePortExposure, EventReceivePort):

    element_name = 'EventReceivePortExposure'

# =============================================================================
# Code for Multi-compartment tree representations (Experimental)
# =============================================================================


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
    defining_attributes = ('_name', '_tree', '_mapping', '_domains')

    def __init__(self, name, tree, mapping, domains, url=None):
        BaseULObject.__init__(self)
        DocumentLevelObject.__init__(self, url)
        assert isinstance(name, basestring)
        self._name = name
        self._domains = dict((d.name, d) for d in domains)
        assert isinstance(mapping, Mapping)
        self._mapping = mapping
        if isinstance(tree, Tree):
            self._tree = tree
        elif hasattr(tree, '__iter__'):
            self._tree = Tree(normalise_parameter_as_list(tree))

    @property
    def name(self):
        return self._name

    @property
    def mapping(self):
        return self._mapping

    @property
    def domains(self):
        return self._domains.itervalues()

    def domain(self, name_or_index):
        """
        Returns the domain corresponding to either the compartment index if
        provided an int or the domain name if provided a str
        """
        if isinstance(name_or_index, int):
            name = self.mapping.domain_name(name_or_index)
        elif isinstance(name_or_index, basestring):
            name = name_or_index
        else:
            raise NineMLRuntimeError(
                "Unrecognised type of 'name_or_index' ({}) can be either int "
                "or str".format(name_or_index))
        return self._domains[name]

    @property
    def domain_names(self):
        return self._domains.iterkeys()

    @property
    def tree(self):
        return self._tree.indices

    def __str__(self):
        return ("MultiCompartment(name='{}', {} compartments, {} domains)"
                .format(self.name, len(self.tree), len(self._domains)))

    @property
    def attributes_with_units(self):
        return chain(*[d.attributes_with_units for d in self.domains])

    @write_reference
    @annotate_xml
    def to_xml(self, document, **kwargs):  # @UnusedVariable
        return E(self.element_name,
                 self._tree.to_xml(document, **kwargs),
                 self._mapping.to_xml(document, **kwargs),
                 *[d.to_xml(document, **kwargs) for d in self.domains],
                 name=self.name)

    @classmethod
    @resolve_reference
    @read_annotations
    def from_xml(cls, element, document, **kwargs):
        cls.check_tag(element)
        tree = Tree.from_xml(
            expect_single(element.findall(NINEML + 'Tree')),
            document, **kwargs)
        mapping = Mapping.from_xml(
            expect_single(element.findall(NINEML + 'Mapping')),
            document, **kwargs)
        domains = [Domain.from_xml(e, document, **kwargs)
                   for e in element.findall(NINEML + 'Domain')]
        return cls(name=element.attrib['name'], tree=tree, mapping=mapping,
                   domains=domains)


class Tree(BaseULObject):

    element_name = "Tree"
    __metaclass__ = ABCMeta  # Abstract base class

    defining_attributes = ("_indices",)

    def __init__(self, indices):
        super(Tree, self).__init__()
        if any(not isinstance(i, int) for i in indices):
            raise NineMLRuntimeError(
                "Mapping keys need to be ints ({})"
                .format(', '.join(str(i) for i in indices)))
        self._indices = indices

    @property
    def indices(self):
        return self._indices

    @annotate_xml
    def to_xml(self, document, **kwargs):  # @UnusedVariable
        return E(self.element_name,
                 ArrayValue(self._indices).to_xml(document, **kwargs))

    @classmethod
    @read_annotations
    def from_xml(cls, element, document, **kwargs):
        array = ArrayValue.from_xml(
            expect_single(element.findall(NINEML + 'ArrayValue')),
            document, **kwargs)
        return cls(array.values)


class Mapping(BaseULObject):

    element_name = "Mapping"
    defining_attributes = ("_indices", '_keys')

    def __init__(self, keys, indices):
        super(Mapping, self).__init__()
        self._keys = keys
        if any(not isinstance(k, int) for k in keys.iterkeys()):
            raise NineMLRuntimeError(
                "Mapping keys need to be ints ({})"
                .format(', '.join(str(k) for k in keys.iterkeys())))
        if any(i not in keys.iterkeys() for i in indices):
            raise NineMLRuntimeError(
                "Some mapping indices ({}) are not present in key"
                .format(', '.join(set(str(i) for i in indices
                                      if i not in keys.iterkeys()))))
        self._indices = indices

    @property
    def keys(self):
        return self._keys

    @property
    def indices(self):
        return self._indices

    def domain_name(self, index):
        domain_index = self.indices[index]
        return self.keys[domain_index]

    @annotate_xml
    def to_xml(self, document, **kwargs):  # @UnusedVariable
        return E(self.element_name,
                 ArrayValue(self._indices).to_xml(document, **kwargs),
                 *[Key(i, n).to_xml(document, **kwargs)
                   for i, n in self.keys.iteritems()])

    @classmethod
    @read_annotations
    def from_xml(cls, element, document, **kwargs):
        array = ArrayValue.from_xml(
            expect_single(element.findall(NINEML + 'ArrayValue')),
            document, **kwargs)
        keys = [Key.from_xml(e, document, **kwargs)
                for e in element.findall(NINEML + 'Key')]
        return cls(dict((k.index, k.domain) for k in keys), array.values)


class Key(BaseULObject):

    element_name = 'Key'

    def __init__(self, index, domain):
        BaseULObject.__init__(self)
        self._index = index
        self._domain = domain

    @property
    def index(self):
        return self._index

    @property
    def domain(self):
        return self._domain

    @annotate_xml
    def to_xml(self, document, **kwargs):  # @UnusedVariable
        return E(self.element_name, index=str(self.index),
                 domain=self.domain)

    @classmethod
    @read_annotations
    def from_xml(cls, element, document, **kwargs):  # @UnusedVariable
        return cls(int(element.attrib['index']), element.attrib['domain'])


class Domain(SubDynamics):

    element_name = 'Domain'
