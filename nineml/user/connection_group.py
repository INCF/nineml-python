from abc import ABCMeta, abstractmethod
from . import BaseULObject
from nineml.abstraction.connectionrule import (
    explicit_connection_rule, one_to_one_connection_rule)
from nineml.user.port_connections import EventPortConnection
from nineml.user.connectionrule import ConnectionRuleProperties, Connectivity
from nineml.units import Quantity
from nineml.abstraction.ports import (
    SendPort, ReceivePort, EventPort, AnalogPort, Port)
from nineml.user.component_array import ComponentArray
from nineml.base import DocumentLevelObject


class BaseConnectionGroup(BaseULObject, DocumentLevelObject):

    __metaclass__ = ABCMeta

    defining_attributes = ('_name', '_source', '_destination', '_source_port',
                           '_destination_port', '_connectivity', '_delay')

    def __init__(self, name, source, destination, source_port,
                 destination_port, connectivity, delay,
                 connectivity_class=Connectivity):
        self._name = name
        BaseULObject.__init__(self)
        DocumentLevelObject.__init__(self)
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
        return cls(name, source, destination,
                   source_port=port_conn.send_port_name,
                   destination_port=port_conn.receive_port_name,
                   connectivity=conn_props, delay=delay)

    @abstractmethod
    def _check_ports(self, source_port, destination_port):
        assert isinstance(source_port, SendPort)
        assert isinstance(destination_port, ReceivePort)

    def serialize_node(self, node, **options):  # @UnusedVariable
        source_elem = node.child(self.source, within='Source', **options)
        node.visitor.set_attr(source_elem, 'port', self.source_port,
                              **options)
        dest_elem = node.child(self.destination, within='Destination',
                               **options)
        node.visitor.set_attr(dest_elem, 'port', self.destination_port)
        node.child(self.connectivity.rule_properties, within='Connectivity')
        if self.delay is not None:
            node.child(self.delay, within='Delay')
        node.attr('name', self.name)

    @classmethod
    def unserialize_node(cls, node, **options):  # @UnusedVariable
        # Get Name
        name = node.attr('name', **options)
        connectivity = node.child(
            ConnectionRuleProperties, within='Connectivity', allow_ref=True,
            **options)
        source = node.child(ComponentArray, within='Source',
                            allow_ref='only', allow_within_attrs=True,
                            **options)
        destination = node.child(ComponentArray, within='Destination',
                                 allow_ref='only', allow_within_attrs=True,
                                 **options)
        source_elem = node.visitor.get_child(
            node.serial_element, 'Source', **options)
        source_port = node.visitor.get_attr(source_elem, 'port', **options)
        dest_elem = node.visitor.get_child(
            node.serial_element, 'Destination', **options)
        destination_port = node.visitor.get_attr(dest_elem, 'port', **options)
        delay = node.child(Quantity, within='Delay', allow_none=True,
                           **options)
        return cls(name=name, source=source, destination=destination,
                   source_port=source_port, destination_port=destination_port,
                   connectivity=connectivity, delay=delay)


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
