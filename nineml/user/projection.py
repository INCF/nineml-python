# encoding: utf-8
from . import BaseULObject
from collections import defaultdict
from nineml.exceptions import NineMLRuntimeError
from nineml.reference import resolve_reference, write_reference
from nineml.xml import (
    E, from_child_xml, unprocessed_xml, get_xml_attr, extract_xmlns, NINEMLv1)
from nineml.annotations import read_annotations, annotate_xml
from .connectionrule import ConnectionRuleProperties, Connectivity
from .dynamics import DynamicsProperties
from nineml.values import SingleValue, ArrayValue, RandomValue
from itertools import chain
from .population import Population
from .selection import Selection
from .component import Quantity
from nineml.base import DocumentLevelObject
from nineml.utils import expect_single, ensure_valid_identifier
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
                 delay, plasticity=None, port_connections=[], document=None,
                 connectivity_class=Connectivity, **kwargs):
        """
        Create a new projection.
        """
        ensure_valid_identifier(name)
        self._name = name
        BaseULObject.__init__(self)
        DocumentLevelObject.__init__(self, document)
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

    @write_reference
    @annotate_xml
    def to_xml(self, document, E=E, **kwargs):  # @UnusedVariable
        if E._namespace == NINEMLv1:
            pcs = defaultdict(list)
            for pc in self.port_connections:
                pcs[pc.receiver_role].append(
                    E('From' + self.v2tov1[pc.sender_role],
                      send_port=pc.send_port_name,
                      receive_port=pc.receive_port_name))
            args = [E.Source(self.pre.to_xml(document, E=E, as_ref=True,
                                             **kwargs), *pcs['pre']),
                    E.Destination(self.post.to_xml(document, E=E, as_ref=True,
                                                   **kwargs), *pcs['post']),
                    E.Response(self.response.to_xml(document, E=E, **kwargs),
                               *pcs['response']),
                    E.Connectivity(
                        self.connectivity.rule_properties.to_xml(document, E=E,
                                                                 **kwargs))]
            if self.plasticity:
                args.append(E.Plasticity(
                    self.plasticity.to_xml(document, E=E, **kwargs),
                    *pcs['plasticity']))
            args.append(E('Delay',
                          self.delay._value.to_xml(document, E=E, **kwargs),
                          units=self.delay.units.name))
            xml = E(self.nineml_type, *args, name=self.name)
        else:
            members = []
            for pop, tag_name in ((self.pre, 'Pre'), (self.post, 'Post')):
                members.append(E(tag_name, pop.to_xml(
                    document, E=E, as_ref=True, **kwargs)))
            members.extend([
                E.Response(self.response.to_xml(document, E=E, **kwargs)),
                E.Connectivity(self.connectivity.rule_properties.to_xml(
                    document, E=E, **kwargs)),
                E.Delay(self.delay.to_xml(document, E=E, **kwargs))])
            if self.plasticity is not None:
                members.append(
                    E.Plasticity(self.plasticity.to_xml(document, E=E,
                                                        **kwargs)))
            members.extend([pc.to_xml(document, E=E, **kwargs)
                            for pc in self.port_connections])
            xml = E(self.nineml_type, *members, name=self.name)
        return xml

    @classmethod
    @resolve_reference
    @read_annotations
    @unprocessed_xml
    def from_xml(cls, element, document, **kwargs):  # @UnusedVariable
        # Get Name
        name = get_xml_attr(element, 'name', document, **kwargs)
        xmlns = extract_xmlns(element.tag)
        if xmlns == NINEMLv1:
            pre_within = 'Source'
            post_within = 'Destination'
            multiple_within = True
            # Get Delay
            delay_elem = expect_single(element.findall(NINEMLv1 + 'Delay'))
            units = document[
                get_xml_attr(delay_elem, 'units', document, **kwargs)]
            value = from_child_xml(
                delay_elem,
                (SingleValue, ArrayValue, RandomValue),
                document, **kwargs)
            delay = Quantity(value, units)
            if 'unprocessed' in kwargs:
                kwargs['unprocessed'][0].discard(delay_elem)
        else:
            pre_within = 'Pre'
            post_within = 'Post'
            multiple_within = False
            delay = from_child_xml(element, Quantity, document, within='Delay',
                                   **kwargs)
        # Get Pre
        pre = from_child_xml(element, (Population, Selection), document,
                             allow_reference='only', within=pre_within,
                             multiple_within=multiple_within, **kwargs)
        post = from_child_xml(element, (Population, Selection), document,
                              allow_reference='only', within=post_within,
                              multiple_within=multiple_within, **kwargs)
        response = from_child_xml(element, DynamicsProperties, document,
                                  allow_reference=True, within='Response',
                                  multiple_within=multiple_within, **kwargs)
        plasticity = from_child_xml(element, DynamicsProperties, document,
                                    allow_reference=True, within='Plasticity',
                                    multiple_within=multiple_within,
                                    allow_none=True, **kwargs)
        connection_rule_props = from_child_xml(
            element, ConnectionRuleProperties, document, within='Connectivity',
            allow_reference=True, **kwargs)
        if xmlns == NINEMLv1:
            port_connections = []
            for receive_name in cls.version1_nodes:
                try:
                    receive_elem = expect_single(
                        element.findall(NINEMLv1 + receive_name))
                except NineMLRuntimeError:
                    if receive_name == 'Plasticity':
                        continue
                    else:
                        raise
                receiver = eval(cls.v1tov2[receive_name])
                for send_name in cls.version1_nodes:
                    for from_elem in receive_elem.findall(NINEMLv1 + 'From' +
                                                          send_name):
                        send_port_name = get_xml_attr(
                            from_elem, 'send_port', document, **kwargs)
                        receive_port_name = get_xml_attr(
                            from_elem, 'receive_port', document, **kwargs)
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
        else:
            port_connections = from_child_xml(
                element, (AnalogPortConnection, EventPortConnection),
                document, multiple=True, allow_none=True, **kwargs)
        return cls(name=name,
                   pre=pre,
                   post=post,
                   response=response,
                   plasticity=plasticity,
                   connectivity=connection_rule_props,
                   delay=delay,
                   port_connections=port_connections,
                   document=document)

    version1_nodes = ('Source', 'Destination', 'Response', 'Plasticity')
    v1tov2 = {'Source': 'pre', 'Destination': 'post',
              'Plasticity': 'plasticity', 'Response': 'response'}
    v2tov1 = dict((v, k) for k, v in v1tov2.iteritems())
