import re
from itertools import chain
from abc import ABCMeta, abstractmethod
from .population import Population
from .projection import Projection
from .selection import Selection
from . import BaseULObject
from .component import write_reference, resolve_reference
from nineml.annotations import annotate_xml, read_annotations
from nineml.exceptions import NineMLNameError
from nineml.base import DocumentLevelObject, ContainerObject
from nineml.xml import E, from_child_xml, unprocessed_xml, get_xml_attr
from nineml.user.port_connections import EventPortConnection
from nineml.abstraction.ports import (
    SendPort, ReceivePort, EventPort, AnalogPort, Port)


class Network(BaseULObject, DocumentLevelObject, ContainerObject):
    """
    Container for populations and projections between those populations.

    **Arguments**:
        *name*
            a name for the network.
        *populations*
            a dict containing the populations contained in the network.
        *projections*
            a dict containing the projections contained in the network.
        *selections*
            a dict containing the selections contained in the network.
    """
    nineml_type = "Network"
    defining_attributes = ('name', "_populations", "_projections",
                           "_selections")
    class_to_member = {'Population': 'population',
                       'Projection': 'projection',
                       'Selection': 'selection'}
    write_order = ('Population', 'Selection', 'Projection')

    def __init__(self, name, populations=[], projections=[],
                 selections=[], document=None):
        # better would be *items, then sort by type, taking the name from the
        # item
        BaseULObject.__init__(self)
        DocumentLevelObject.__init__(self, document=document)
        ContainerObject.__init__(self)
        self._name = name
        self._populations = dict((p.name, p) for p in populations)
        self._projections = dict((p.name, p) for p in projections)
        self._selections = dict((s.name, s) for s in selections)

    @property
    def name(self):
        return self._name

    def population(self, name):
        return self._populations[name]

    def projection(self, name):
        return self._projections[name]

    def selection(self, name):
        return self._selections[name]

    @property
    def populations(self):
        return self._populations.itervalues()

    @property
    def projections(self):
        return self._projections.itervalues()

    @property
    def selections(self):
        return self._selections.itervalues()

    @property
    def population_names(self):
        return self._populations.iterkeys()

    @property
    def projection_names(self):
        return self._projections.iterkeys()

    @property
    def selection_names(self):
        return self._selections.iterkeys()

    @property
    def num_populations(self):
        return len(self._populations)

    @property
    def num_projections(self):
        return len(self._projections)

    @property
    def num_selections(self):
        return len(self._selections)

    # =========================================================================
    # Core accessors
    # =========================================================================

    @property
    def component_arrays(self):
        return chain((ComponentArray(p.name, p.size, p.cell)
                      for p in self.populations),
                     (ComponentArray(p.name + '__psr', len(p), p.response)
                      for p in self.projections),
                     (ComponentArray(p.name + '__pls', len(p), p.plasticity)
                      for p in self.projections))

    @property
    def connection_groups(self):
        return chain(*(
            (BaseConnectionGroup.from_port_connection(pc, p)
             for pc in p.port_connections)
            for p in self.projections))

    def component_array(self, name):
        try:
            return next(ca for ca in self.component_arrays if ca.name == name)
        except StopIteration:
            raise NineMLNameError(
                "No component group named '{}' in '{}' network (found '{}')"
                .format(name, self.name,
                        "', '".join(self.component_arrays_names)))

    def connection_group(self, name):
        try:
            return next(cg for cg in self.connection_groups
                        if cg.name == name)
        except StopIteration:
            raise NineMLNameError(
                "No connection group named '{}' in '{}' network (found '{}')"
                .format(name, self.name,
                        "', '".join(self.connection_group_names)))

    @property
    def component_array_names(self):
        return (ca.name for ca in self.component_arrays)

    @property
    def connection_group_names(self):
        return (cg.name for cg in self.connection_groups)

    @property
    def num_component_arrays(self):
        return len(list(self.component_arrays))

    @property
    def num_connection_groups(self):
        return len(list(self.connection_groups))

    def get_components(self):
        components = []
        for p in chain(self.populations.values(), self.projections.values()):
            components.extend(p.get_components())
        return components

    def resample_connectivity(self, **kwargs):
        for projection in self.projections:
            projection.resample_connectivity(**kwargs)

    def connectivity_has_been_sampled(self):
        return any(p.connectivity.has_been_sampled() for p in self.projections)

    @write_reference
    @annotate_xml
    def to_xml(self, document, E=E, **kwargs):  # @UnusedVariable
        member_elems = []
        for member in chain(self.populations, self.selections,
                            self.projections):
            member_elems.append(member.to_xml(
                document, E=E, as_ref=True, **kwargs))
        return E(self.nineml_type, name=self.name, *member_elems)

    @classmethod
    @resolve_reference
    @read_annotations
    @unprocessed_xml
    def from_xml(cls, element, document, **kwargs):
        populations = from_child_xml(element, Population, document,
                                     multiple=True, allow_reference='only',
                                     allow_none=True, **kwargs)
        projections = from_child_xml(element, Projection, document,
                                     multiple=True, allow_reference='only',
                                     allow_none=True, **kwargs)
        selections = from_child_xml(element, Selection, document,
                                    multiple=True, allow_reference='only',
                                    allow_none=True, **kwargs)
        network = cls(name=get_xml_attr(element, 'name', document, **kwargs),
                      populations=populations, projections=projections,
                      selections=selections)
        return network

    _conn_group_name_re = re.compile(
        r'(\w+)__(\w+)_(\w+)__(\w+)_(\w+)__connection_group')


class ComponentArray(BaseULObject):

    nineml_type = "ComponentArray"
    defining_attributes = ('name', "_size", "_dynamics")

    def __init__(self, name, size, dynamics):
        self._name = name
        self._size = size
        self._dynamics = dynamics

    @property
    def name(self):
        return self._name

    @property
    def size(self):
        return self._size

    @property
    def dynamics(self):
        return self._dynamics


class BaseConnectionGroup(BaseULObject):

    __metaclass__ = ABCMeta

    defining_attributes = ('name', 'source', 'destination', 'source_port',
                           'destination_port', 'connectivity')

    def __init__(self, name, source, destination, source_port,
                 destination_port, connectivity, delay):
        assert isinstance(name, basestring)
        assert isinstance(source, basestring)
        assert isinstance(destination, basestring)
        self._name = name
        self._source = source
        self._destination = destination
        self._source_port = source_port
        self._destination_port = destination_port
        self._connectivity = connectivity
        self._delay = delay
        if isinstance(source_port, Port):
            self._check_ports(source_port, destination_port)

    @property
    def name(self):
        return self._name

    @property
    def source(self):
        return self._source

    @property
    def destination(self):
        return self._destination

    @property
    def source_port(self):
        return self._source_port

    @property
    def connectivity(self):
        return self._connectivity

    @property
    def destination_port(self):
        return self._destination_port

    @property
    def delay(self):
        return self._delay

    @property
    def connections(self):
        return self._connectivity.connections()

    @classmethod
    def from_port_connection(self, port_connection, projection):
        if isinstance(port_connection, EventPortConnection):
            cls = AnalogConnectionGroup
        else:
            cls = EventConnectionGroup
        name = '__'.join((
            projection.name, port_connection.sender_role,
            port_connection.send_port_name, port_connection.receiver_role,
            port_connection.receive_port_name))
        if port_connection.receiver_role == 'pre':
            connectivity = InverseConnectivity(projection.connectivity)
        else:
            connectivity = projection.connectivity
        # FIXME: This will need to change in version 2, when each connection
        #        has its own delay
        if port_connection.sender_role == 'pre':
            delay = projection.delay
        else:
            delay = None
        return cls(name, projection.pre.name, projection.post.name,
                   source_port=port_connection.send_port_name,
                   destination_port=port_connection.receive_port_name,
                   connectivity=connectivity,
                   delay=delay)

    @abstractmethod
    def _check_ports(self, source_port, destination_port):
        try:
            assert isinstance(source_port, SendPort)
            assert isinstance(destination_port, ReceivePort)
        except:
            raise


class AnalogConnectionGroup(BaseConnectionGroup):

    nineml_type = 'AnalogConnectionGroup'

    def _check_ports(self, source_port, destination_port):
        super(AnalogConnectionGroup, self)._check_ports(source_port,
                                                        destination_port)
        assert isinstance(source_port, AnalogPort)
        assert isinstance(destination_port, AnalogPort)


class EventConnectionGroup(BaseConnectionGroup):

    nineml_type = 'EventConnectionGroup'

    def _check_ports(self, source_port, destination_port):
        super(EventConnectionGroup, self)._check_ports(source_port,
                                                       destination_port)
        assert isinstance(source_port, EventPort)
        assert isinstance(destination_port, EventPort)


class InverseConnectivity(object):
    """
    Inverts the connectivity so that the source and destination are effectively
    flipped. Used when mapping a projection connectivity to a reverse
    connection to from the synapse or post-synaptic cell to the pre-synaptic
    cell
    """

    def __init__(self, connectivity):  # @UnusedVariable
        self._connectivity = connectivity

    def __eq__(self, other):
        return self._connectivity == other._connectivity

    @property
    def rule_properties(self):
        return self._connectivity._rule_props

    @property
    def rule(self):
        return self.rule_properties.component_class

    @property
    def lib_type(self):
        return self.rule_properties.lib_type

    @property
    def source_size(self):
        return self._connectivity.destination_size

    @property
    def destination_size(self):
        return self._connectivity.source_size

    def __repr__(self):
        return ("{}(rule={}, src_size={}, dest_size={})"
                .format(self.__class__.__name__, self.lib_type,
                        self.source_size, self.destination_size))

    @abstractmethod
    def connections(self):
        return ((j, i) for i, j in self._connectivity.connections)

    @abstractmethod
    def has_been_sampled(self):
        return self._connectivity.has_been_sampled

