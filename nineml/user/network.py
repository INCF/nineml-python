import os.path
import re
from itertools import chain
from abc import ABCMeta, abstractmethod
from .population import Population
from .projection import Projection
from .selection import Selection
from . import BaseULObject
from .component import write_reference, resolve_reference
from nineml.abstraction.connectionrule import (
    explicit_connection_rule, one_to_one_connection_rule)
from nineml.annotations import annotate_xml, read_annotations
from nineml.exceptions import name_error
from nineml.base import DocumentLevelObject, ContainerObject
from nineml.xml import (
    E, from_child_xml, unprocessed_xml, get_xml_attr)
from nineml.user.port_connections import EventPortConnection
from nineml.user.dynamics import DynamicsProperties
from nineml.user.connectionrule import ConnectionRuleProperties, Connectivity
from nineml.units import Quantity
from nineml.abstraction.ports import (
    SendPort, ReceivePort, EventPort, AnalogPort, Port)
from nineml.utils import ensure_valid_identifier
import nineml.document


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
    defining_attributes = ('_name', "_populations", "_projections",
                           "_selections")
    class_to_member = {'Population': 'population',
                       'Projection': 'projection',
                       'Selection': 'selection'}
    write_order = ('Population', 'Selection', 'Projection')

    def __init__(self, name, populations=[], projections=[],
                 selections=[], document=None):
        # better would be *items, then sort by type, taking the name from the
        # item
        ensure_valid_identifier(name)
        self._name = name
        BaseULObject.__init__(self)
        DocumentLevelObject.__init__(self, document=document)
        ContainerObject.__init__(self)
        self._populations = dict((p.name, p) for p in populations)
        self._projections = dict((p.name, p) for p in projections)
        self._selections = dict((s.name, s) for s in selections)

    @property
    def name(self):
        return self._name

    @name_error
    def population(self, name):
        return self._populations[name]

    @name_error
    def projection(self, name):
        return self._projections[name]

    @name_error
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

    def get_components(self):
        components = []
        for p in chain(self.populations.values(), self.projections.values()):
            components.extend(p.get_components())
        return components

    def resample_connectivity(self, *args, **kwargs):
        for projection in self.projections:
            projection.resample_connectivity(*args, **kwargs)

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

    @classmethod
    def from_document(cls, document):
        name = os.path.splitext(os.path.basename(document.url))[0]
        return Network(name=name, populations=document.populations,
                       projections=document.projections,
                       selections=document.selections, document=document)

    @classmethod
    def read(cls, url):
        document = nineml.document.read(url)
        return cls.from_document(document)

    _conn_group_name_re = re.compile(
        r'(\w+)__(\w+)_(\w+)__(\w+)_(\w+)__connection_group')

    def flatten(self):
        component_arrays = dict((ca.name, ca) for ca in chain(
            (ComponentArray(p.name + ComponentArray.suffix['post'], len(p),
                            p.cell)
             for p in self.populations),
            (ComponentArray(p.name + ComponentArray.suffix['response'], len(p),
                            p.response)
             for p in self.projections),
            (ComponentArray(p.name + ComponentArray.suffix['plasticity'],
                            len(p), p.plasticity)
             for p in self.projections if p.plasticity is not None)))
        connection_groups = list(chain(*(
            (BaseConnectionGroup.from_port_connection(pc, p, component_arrays)
             for pc in p.port_connections)
            for p in self.projections)))
        return component_arrays.values(), connection_groups


class ComponentArray(BaseULObject, DocumentLevelObject):

    nineml_type = "ComponentArray"
    defining_attributes = ('_name', "_size", "_dynamics_properties")
    suffix = {'pre': '__cell', 'post': '__cell', 'response': '__psr',
              'plasticity': '__pls'}

    def __init__(self, name, size, dynamics_properties, document=None):
        self._name = name
        BaseULObject.__init__(self)
        DocumentLevelObject.__init__(self, document)
        self.size = size
        self._dynamics_properties = dynamics_properties

    @property
    def name(self):
        return self._name

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, size):
        self._size = int(size)

    @property
    def dynamics_properties(self):
        return self._dynamics_properties

    @property
    def component_class(self):
        return self.dynamics_properties.component_class

    @write_reference
    @annotate_xml
    def to_xml(self, document, E=E, **kwargs):  # @UnusedVariable
        return E(self.nineml_type,
                 E.Size(str(self.size)),
                 self.dynamics_properties.to_xml(document, E=E, **kwargs),
                 name=self.name)

    @classmethod
    @resolve_reference
    @read_annotations
    @unprocessed_xml
    def from_xml(cls, element, document, **kwargs):
        dynamics_properties = from_child_xml(
            element, DynamicsProperties, document,
            allow_reference=True, **kwargs)
        return cls(name=get_xml_attr(element, 'name', document, **kwargs),
                   size=get_xml_attr(element, 'Size', document, in_block=True,
                                     dtype=int, **kwargs),
                   dynamics_properties=dynamics_properties, document=document)


class BaseConnectionGroup(BaseULObject, DocumentLevelObject):

    __metaclass__ = ABCMeta

    defining_attributes = ('_name', '_source', '_destination', '_source_port',
                           '_destination_port', '_connectivity', '_delay')

    def __init__(self, name, source, destination, source_port,
                 destination_port, connectivity, delay, document=None,
                 connectivity_class=Connectivity):
        self._name = name
        BaseULObject.__init__(self)
        DocumentLevelObject.__init__(self, document)
        self._source = source
        self._destination = destination
        self._source_port = source_port
        self._destination_port = destination_port
        if isinstance(connectivity, ConnectionRuleProperties):
            connectivity = connectivity_class(connectivity, source.size,
                                              destination.size)
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
    def from_port_connection(self, port_conn, projection, component_arrays):
        if isinstance(port_conn, EventPortConnection):
            cls = AnalogConnectionGroup
        else:
            cls = EventConnectionGroup
        name = '__'.join((
            projection.name, port_conn.sender_role,
            port_conn.send_port_name, port_conn.receiver_role,
            port_conn.receive_port_name))
        if (port_conn.sender_role in ('response', 'plasticity') and
                port_conn.receiver_role in ('response', 'plasticity')):
            conn_props = ConnectionRuleProperties(
                name=name + '_connectivity',
                definition=one_to_one_connection_rule)
        else:
            if (port_conn.sender_role == 'pre' and
                    port_conn.receiver_role == 'post'):
                source_inds, dest_inds = zip(*projection.connections())
            elif (port_conn.sender_role == 'post' and
                  port_conn.receiver_role == 'pre'):
                source_inds, dest_inds = zip(*(
                    (d, s) for s, d in projection.connections()))
            elif port_conn.sender_role == 'pre':
                source_inds, dest_inds = zip(*(
                    (s, i) for i, (s, _) in enumerate(
                        sorted(projection.connections()))))
            elif port_conn.receiver_role == 'post':
                source_inds, dest_inds = zip(*(
                    (i, d) for i, (_, d) in enumerate(
                        sorted(projection.connections()))))
            else:
                assert False
            conn_props = ConnectionRuleProperties(
                name=name + '_connectivity',
                definition=explicit_connection_rule,
                properties={'sourceIndices': source_inds,
                            'destinationIndices': dest_inds})
        # FIXME: This will need to change in version 2, when each connection
        #        has its own delay
        if port_conn.sender_role == 'pre':
            delay = projection.delay
        else:
            delay = None
        try:
            source = component_arrays[
                (projection.pre.name
                 if port_conn.sender_role in ('pre', 'post')
                 else projection.name) +
                ComponentArray.suffix[port_conn.sender_role]]
            destination = component_arrays[
                (projection.pre.name
                 if port_conn.receiver_role in ('pre', 'post')
                 else projection.name) +
                ComponentArray.suffix[port_conn.receiver_role]]
        except:
            raise
        return cls(name, source, destination,
                   source_port=port_conn.send_port_name,
                   destination_port=port_conn.receive_port_name,
                   connectivity=conn_props, delay=delay)

    @abstractmethod
    def _check_ports(self, source_port, destination_port):
        assert isinstance(source_port, SendPort)
        assert isinstance(destination_port, ReceivePort)

    @write_reference
    @annotate_xml
    def to_xml(self, document, E=E, **kwargs):  # @UnusedVariable
        members = [
            E.Source(self.source.to_xml(document, E=E, **kwargs),
                     port=self.source_port),
            E.Destination(self.destination.to_xml(document, E=E, **kwargs),
                          port=self.destination_port),
            E.Connectivity(self.connectivity.rule_properties.to_xml(
                document, E=E, **kwargs))]
        if self.delay is not None:
            members.append(E.Delay(self.delay.to_xml(document, E=E, **kwargs)))
        xml = E(self.nineml_type,
                *members,
                name=self.name)
        return xml

    @classmethod
    @resolve_reference
    @read_annotations
    @unprocessed_xml
    def from_xml(cls, element, document, **kwargs):  # @UnusedVariable
        # Get Name
        name = get_xml_attr(element, 'name', document, **kwargs)
        connectivity = from_child_xml(
            element, ConnectionRuleProperties, document, within='Connectivity',
            allow_reference=True, **kwargs)
        source = from_child_xml(
            element, ComponentArray, document, within='Source',
            allow_reference=True, allowed_attrib=['port'], **kwargs)
        destination = from_child_xml(
            element, ComponentArray, document, within='Destination',
            allow_reference=True, allowed_attrib=['port'], **kwargs)
        source_port = get_xml_attr(element, 'port', document,
                                   within='Source', **kwargs)
        destination_port = get_xml_attr(element, 'port', document,
                                        within='Destination', **kwargs)
        delay = from_child_xml(element, Quantity, document, within='Delay',
                               allow_none=True, **kwargs)
        return cls(name=name, source=source, destination=destination,
                   source_port=source_port, destination_port=destination_port,
                   connectivity=connectivity, delay=delay, document=None)


class AnalogConnectionGroup(BaseConnectionGroup):

    nineml_type = 'AnalogConnectionGroup'
    communicates = 'analog'

    def _check_ports(self, source_port, destination_port):
        super(AnalogConnectionGroup, self)._check_ports(source_port,
                                                        destination_port)
        assert isinstance(source_port, AnalogPort)
        assert isinstance(destination_port, AnalogPort)


class EventConnectionGroup(BaseConnectionGroup):

    nineml_type = 'EventConnectionGroup'
    communicates = 'event'

    def _check_ports(self, source_port, destination_port):
        super(EventConnectionGroup, self)._check_ports(source_port,
                                                       destination_port)
        assert isinstance(source_port, EventPort)
        assert isinstance(destination_port, EventPort)
