# encoding: utf-8
from itertools import chain
from . import BaseULObject
from nineml.exceptions import (
    NineMLMissingSerializationError, NineMLSerializationError)
from .connectionrule import ConnectionRuleProperties, Connectivity
from .dynamics import DynamicsProperties
from .population import Population
from .selection import Selection
from .component import Quantity
from nineml.base import DocumentLevelObject
from nineml.utils import ensure_valid_identifier
from nineml.abstraction.ports import EventReceivePort
from .port_connections import (
    AnalogPortConnection, EventPortConnection, BasePortConnection)


class Projection(BaseULObject, DocumentLevelObject):
    """
    A collection of connections between two :class:`Population`\s.

    **Arguments**:
        *name*
            a name for this projection.
        *pre*
            the presynaptic :class:`Population`.
        *post*
            the postsynaptic :class:`Population`.
        *response*
            a `dynamics` :class:`Component` that defines the post-synaptic
            response.
        *plasticity*
            a `dynamics` :class:`Component` that defines the plasticity
            rule for the synaptic weight/efficacy.
        *connectivity*
            a `connection rule` :class:`Component` that defines
            an algorithm for wiring up the neurons.
        *delay*
            a :class:`Delay` object specifying the delay of the connections.

    **Attributes**:

    Each of the arguments to the constructor is available as an attribute of
    the same name.

    """
    nineml_type = "Projection"
    defining_attributes = ('_name', '_pre', '_post', '_connectivity',
                           '_response', '_plasticity', '_delay',
                           '_analog_port_connections',
                           '_event_port_connections')

    _component_roles = set(['pre', 'post', 'plasticity', 'response'])

    def __init__(self, name, pre, post, response, connectivity,
                 delay, plasticity=None, port_connections=[],
                 connectivity_class=Connectivity, **kwargs):
        """
        Create a new projection.
        """
        ensure_valid_identifier(name)
        self._name = name
        BaseULObject.__init__(self)
        DocumentLevelObject.__init__(self)
        assert isinstance(name, basestring)
        assert isinstance(delay, Quantity)
        assert isinstance(pre, (Population, Selection))
        assert isinstance(post, (Population, Selection))
        assert isinstance(response, DynamicsProperties)
        assert isinstance(plasticity, (DynamicsProperties, type(None)))
        self._pre = pre
        self._post = post
        self._response = response
        self._plasticity = plasticity
        self._connectivity = connectivity_class(
            connectivity, pre.size, post.size, **kwargs)
        self._delay = delay
        self._analog_port_connections = []
        self._event_port_connections = []
        for port_connection in port_connections:
            if isinstance(port_connection, tuple):
                port_connection = BasePortConnection.from_tuple(
                    port_connection, self)
            port_connection.bind(self, to_roles=True)
            if isinstance(port_connection, EventPortConnection):
                self._event_port_connections.append(port_connection)
            else:
                self._analog_port_connections.append(port_connection)

    def __len__(self):
        return sum(1 for _ in self.connectivity.connections())

    @property
    def name(self):
        return self._name

    @property
    def pre(self):
        return self._pre

    @property
    def post(self):
        return self._post

    @property
    def response(self):
        return self._response

    @property
    def plasticity(self):
        return self._plasticity

    @property
    def connectivity(self):
        return self._connectivity

    def connections(self):
        return self.connectivity.connections()

    @property
    def delay(self):
        return self._delay

    @property
    def analog_port_connections(self):
        return self._analog_port_connections

    @property
    def event_port_connections(self):
        return self._event_port_connections

    @property
    def port_connections(self):
        return chain(self.analog_port_connections, self.event_port_connections)

    def resample_connectivity(self, connectivity_class=None, **kwargs):
        if connectivity_class is None:
            connectivity_class = type(self.connectivity)
        self._connectivity = connectivity_class(
            self.connectivity.rule_properties, self.connectivity.source_size,
            self.connectivity.destination_size, **kwargs)

    def __repr__(self):
        return ('Projection(name="{}", pre={}, post={}, '
                'connectivity={}, response={}{}, delay={},'
                'event_port_connections=[{}], '
                'analog_port_connections=[{}])'
                .format(self.name, repr(self.pre), repr(self.post),
                        repr(self.connectivity), repr(self.response),
                        ('plasticity={}'.format(repr(self.plasticity))
                         if self.plasticity else ''), repr(self.delay),
                        ', '.join(str(pc)
                                  for pc in self.event_port_connections),
                        ', '.join(str(pc)
                                  for pc in self.analog_port_connections)))

    @property
    def components(self):
        """
        Return a list of all components used by the projection.
        """
        components = [self.connectivity.rule_properties, self.response]
        if self.plasticity is not None:
            components.append(self.plasticity)
        return components

    @property
    def attributes_with_units(self):
        return chain([self.delay],
                     *[c.attributes_with_units for c in self.components])

    def serialize_node(self, node, **options):  # @UnusedVariable
        node.attr('name', self.name, **options)
        node.child(self.pre, reference=True, within='Pre', **options)
        node.child(self.post, reference=True, within='Post', **options)
        node.child(self.connectivity.rule_properties,
                   within='Connectivity', **options)
        node.child(self.response, within='Response', **options),
        if self.plasticity is not None:
            node.child(self.plasticity, within='Plasticity', **options)
        node.child(self.delay, within='Delay', **options)
        node.children(self.event_port_connections, **options)
        node.children(self.analog_port_connections, **options)

    @classmethod
    def unserialize_node(cls, node, **options):  # @UnusedVariable
        # Get Name
        name = node.attr('name', **options)
        pre_within = 'Pre'
        post_within = 'Post'
        delay = node.child(Quantity, within='Delay', **options)
        # Get Pre
        pre = node.child(
            (Population, Selection), allow_ref='only', within=pre_within,
            **options)
        post = node.child(
            (Population, Selection), allow_ref='only', within=post_within,
            **options)
        response = node.child(DynamicsProperties, within='Response',
                              allow_ref=True, **options)
        plasticity = node.child(
            DynamicsProperties, allow_ref=True, within='Plasticity',
            allow_none=True, **options)
        connection_rule_props = node.child(
            ConnectionRuleProperties, within='Connectivity',
            allow_ref=True, **options)
        port_connections = node.children(
            (AnalogPortConnection, EventPortConnection), **options)
        return cls(name=name,
                   pre=pre,
                   post=post,
                   response=response,
                   plasticity=plasticity,
                   connectivity=connection_rule_props,
                   delay=delay,
                   port_connections=port_connections)

    def serialize_node_v1(self, node, **options):  # @UnusedVariable
        node.attr('name', self.name, **options)
        endpoints = {}
        endpoints['pre'] = node.child(
            self.pre, within='Source', reference=True, **options)
        endpoints['post'] = node.child(
            self.post, within='Destination', reference=True, **options)
        node.child(self.connectivity.rule_properties,
                   within='Connectivity', **options)
        endpoints['response'] = node.child(
            self.response, within='Response', **options)
        if self.plasticity:
            endpoints['plasticity'] = node.child(
                self.plasticity, within='Plasticity', **options)
        for pc in self.port_connections:
            pc_elem = node.visitor.create_elem(
                'From' + self.v2tov1[pc.sender_role],
                parent=endpoints[pc.receiver_role], multiple=True)
            node.visitor.set_attr(pc_elem, 'send_port', pc.send_port_name,
                                  **options)
            node.visitor.set_attr(pc_elem, 'receive_port',
                                  pc.receive_port_name, **options)
        delay_elem = node.child(self.delay._value, within='Delay',
                                **options)
        node.visitor.set_attr(delay_elem, 'units', self.delay.units.name,
                              **options)

    @classmethod
    def unserialize_node_v1(cls, node, **options):  # @UnusedVariable
        # Get Name
        name = node.attr('name', **options)
        pre_within = 'Source'
        post_within = 'Destination'
        # Get Delay
        _, delay_elem = node.visitor.get_single_child(node.serial_element,
                                                      'Delay')
        node.unprocessed_children.remove('Delay')
        units = node.document[
            node.visitor.get_attr(delay_elem, 'units', **options)]
        nineml_type, value_elem = node.visitor.get_single_child(
            delay_elem, ('SingleValue', 'ArrayValue', 'RandomValue'),
            **options)
        value = node.visitor.visit(
            value_elem,
            node.visitor.get_nineml_class(nineml_type, value_elem,
                                          assert_doc_level=False),
            **options)
        delay = Quantity(value, units)
        # Get Pre
        pre = node.child(
            (Population, Selection), allow_ref='only', within=pre_within,
            **options)
        post = node.child(
            (Population, Selection), allow_ref='only', within=post_within,
            **options)
        response = node.child(DynamicsProperties, within='Response',
                              allow_ref=True, **options)
        plasticity = node.child(
            DynamicsProperties, allow_ref=True, within='Plasticity',
            allow_none=True, **options)
        connection_rule_props = node.child(
            ConnectionRuleProperties, within='Connectivity',
            allow_ref=True, **options)
        port_connections = []
        for receive_name in cls.version1_nodes:
            try:
                _, receive_elem = node.visitor.get_single_child(
                    node.serial_element, receive_name, **options)
            except NineMLMissingSerializationError:
                if receive_name == 'Plasticity':
                    continue  # Plasticity is optional
                else:
                    raise
            receiver = eval(cls.v1tov2[receive_name])
            for elem_name, _, send_elem in node.visitor.get_children(
                    receive_elem, **options):
                if elem_name in ('Component', 'Reference'):
                    continue
                elif (not elem_name.startswith('From') or
                      elem_name[4:] not in cls.version1_nodes):
                    raise NineMLSerializationError(
                        "Unrecognised element '{}' in {} element of "
                        "'{}' projection"
                        .format(elem_name, receive_name, name))
                send_name = elem_name[4:]
                send_port_name = node.visitor.get_attr(
                    send_elem, 'send_port', **options)
                receive_port_name = node.visitor.get_attr(
                    send_elem, 'receive_port', **options)
                receive_port = receiver.port(receive_port_name)
                if isinstance(receive_port, EventReceivePort):
                    pc_cls = EventPortConnection
                else:
                    pc_cls = AnalogPortConnection
                port_connections.append(pc_cls(
                    receiver_role=cls.v1tov2[receive_name],
                    sender_role=cls.v1tov2[send_name],
                    send_port=send_port_name,
                    receive_port=receive_port_name))
        return cls(name=name,
                   pre=pre,
                   post=post,
                   response=response,
                   plasticity=plasticity,
                   connectivity=connection_rule_props,
                   delay=delay,
                   port_connections=port_connections)

    version1_nodes = ('Source', 'Destination', 'Response', 'Plasticity')
    v1tov2 = {'Source': 'pre', 'Destination': 'post',
              'Plasticity': 'plasticity', 'Response': 'response'}
    v2tov1 = dict((v, k) for k, v in v1tov2.iteritems())
