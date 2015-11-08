# encoding: utf-8
from abc import ABCMeta, abstractmethod
from . import BaseULObject
from itertools import izip
from collections import defaultdict
from nineml.exceptions import NineMLRuntimeError
from nineml.reference import resolve_reference, write_reference
from nineml.xml import (
    E, from_child_xml, unprocessed_xml, get_xml_attr, extract_xmlns, NINEMLv1)
from nineml.annotations import read_annotations, annotate_xml
from .component import (
    ConnectionRuleProperties, DynamicsProperties)
from nineml.values import SingleValue, ArrayValue, RandomValue
import random
from itertools import chain
from .population import Population
from .selection import Selection
from .component import Quantity
from nineml.base import DocumentLevelObject
from nineml.utils import expect_single
from nineml.abstraction.ports import EventReceivePort
from .port_connections import (
    AnalogPortConnection, EventPortConnection, BasePortConnection)


class BaseConnectivity(object):

    __metaclass__ = ABCMeta

    def __init__(self, connection_rule, source, destination, **kwargs):
        self._source = source
        self._dest = destination
        self._rule = connection_rule
        self._src_size = self._source.size
        self._dest_size = self._dest.size
        self.reset(**kwargs)

    @property
    def rule(self):
        return self._rule

    def connections(self, source_indices=None, destination_indices=None):  # @UnusedVariable @IgnorePep8
        """
        Returns an iterator over all the source/destination index pairings
        with a connection.
        `src`  -- the indices to get the connections from
        `dest` -- the indices to get the connections to
        """
        if self._src_size != self._source.size:
            raise NineMLRuntimeError(
                "Source has changed size ({} to {}) since last reset"
                .format(self._src_size, self._source.size))
        if self._dest_size != self._dest.size:
            raise NineMLRuntimeError(
                "Destination has changed size ({} to {}) since last reset"
                .format(self._dest_size, self._dest.size))
        if self.rule.lib_type == 'AllToAll':
            conn = self._all_to_all(source_indices, destination_indices)
        elif self.rule.lib_type == 'OneToOne':
            conn = self._one_to_one(source_indices, destination_indices)
        elif self.rule.lib_type == 'ExplicitConnectionList':
            conn = self._explicit_connection_list(source_indices,
                                                  destination_indices)
        elif self.rule.lib_type == 'ProbabilisticConnectivity':
            conn = self._probabilistic_connectivity(source_indices,
                                                    destination_indices)
        elif self.rule.lib_type == 'RandomFanIn':
            conn = self._random_fan_in(source_indices, destination_indices)
        elif self.rule.lib_type == 'RandomFanOut':
            conn = self._random_fan_out(source_indices, destination_indices)
        else:
            assert False
        return conn

    def reset(self, **kwargs):  # @UnusedVariable
        self._src_size = self._source.size
        self._dest_size = self._dest.size

    @abstractmethod
    def _all_to_all(self, source_indices, destination_indices):
        pass

    @abstractmethod
    def _one_to_one(self, source_indices, destination_indices):
        pass

    @abstractmethod
    def _explicit_connection_list(self, source_indices, destination_indices):
        pass

    @abstractmethod
    def _probabilistic_connectivity(self, source_indices, destination_indices):
        pass

    @abstractmethod
    def _random_fan_in(self, source_indices, destination_indices):
        pass

    @abstractmethod
    def _random_fan_out(self, source_indices, destination_indices):
        pass


class Connectivity(BaseConnectivity):
    """
    A reference implementation of the Connectivity class, it is not recommended
    for large networks as it is not designed for efficiency. For more efficient
    implementations the BaseConnectivity class can be overridden for more
    (e.g. using NumPy etc...)
    """

    def reset(self, seed=None):
        super(Connectivity, self).reset()
        if self.rule.is_random():
            self._cache = {}

    def _all_to_all(self, source_indices, destination_indices):
        if source_indices is not None:
            src = source_indices
        else:
            src = xrange(self._src_size)
        if destination_indices is not None:
            dest = destination_indices
        else:
            dest = xrange(self._dest_size)
        return chain(*(((s, d) for d in dest) for s in src))

    def _one_to_one(self, source_indices, destination_indices):
        if self._src_size != self._dest_size:
            raise NineMLRuntimeError(
                "Cannot connect to populations of different sizes "
                "({} and {}) with OneToOne connection rule"
                .format(self._src_size, self._dest_size))
        if source_indices is not None:
            if destination_indices is not None:
                # Get the intersection between the source and destination
                # sets
                inds = set(source_indices) ^ set(destination_indices)
            else:
                inds = source_indices
        elif destination_indices is not None:
            inds = destination_indices
        else:
            inds = xrange(self._src_size)  # All indices
        return ((i, i) for i in inds)

    def _explicit_connection_list(self, source_indices, destination_indices):
        conns = izip(self.rule.property('source_indices').values,
                     self.rule.property('destination_indices').values)
        if source_indices is not None:
            if destination_indices is not None:
                conns = (
                    (s, d) for s, d in conns
                    if s in source_indices and d in destination_indices)
            else:
                conns = ((s, d) for s, d in conns if s in source_indices)
        elif destination_indices:
            conns = ((s, d) for s, d in conns if d in destination_indices)

    def _probabilistic_connectivity(self, source_indices, destination_indices):
        self._check_seed()
        if source_indices is not None:
            src = source_indices
        else:
            src = xrange(self._src_size)
        if destination_indices is not None:
            dest = destination_indices
        else:
            dest = xrange(self._dest_size)
        p = self.rule.property('probability')
        if self._cache:
            conn = chain(*((self._cache.get((s, d), random.random() < p)
                            for d in dest) for s in src))
        else:
            conn = chain(*(((s, d) for d in dest if random.random() < p)
                           for s in src))
        return conn

    def _random_fan_in(self, source_indices, destination_indices):
        self._check_seed()
        raise NotImplementedError

    def _random_fan_out(self, source_indices, destination_indices):
        self._check_seed()
        raise NotImplementedError

    def _check_seed(self):
        if self._seed is None:
            raise NineMLRuntimeError(
                "Random number generator seed must be set before connections "
                "can be read as connection rule '{}' has stochastic "
                "components".format(self._connection_rule.name))

    @property
    def seed(self):
        return self._seed


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
    defining_attributes = ("name", "pre", "post", "connectivity",
                           "response", "plasticity", "delay")

    _component_roles = set(['pre', 'post', 'plasticity', 'response'])

    def __init__(self, name, pre, post, response, connection_rule_props,
                 delay, plasticity=None, port_connections=[], document=None,
                 connectivity_class=Connectivity, rng_seed=None):
        """
        Create a new projection.
        """
        BaseULObject.__init__(self)
        DocumentLevelObject.__init__(self, document)
        assert isinstance(name, basestring)
        assert isinstance(delay, Quantity)
        assert isinstance(pre, Population)
        assert isinstance(post, Population)
        assert isinstance(response, DynamicsProperties)
        assert isinstance(plasticity, (DynamicsProperties, type(None)))
        self._name = name
        self._pre = pre
        self._post = post
        self._response = response
        self._plasticity = plasticity
        self._connectivity = connectivity_class(
            connection_rule_props, pre, post, rng_seed)
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

    def __repr__(self):
        return ('Projection(name="{}", pre={}, post={}, '
                'connectivity={}, response={}{}, delay={})'
                .format(self.name, repr(self.pre), repr(self.post),
                        repr(self.connectivity), repr(self.response),
                        ('plasticity={}'.format(repr(self.plasticity))
                         if self.plasticity else ''), repr(self.delay)))

    @property
    def components(self):
        """
        Return a list of all components used by the projection.
        """
        components = [self.connectivity, self.response]
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
                    E('From' + pc.sender_role.capitalize(),
                      send_port=pc.send_port_name,
                      receive_port=pc.receive_port_name))
            args = [E.Source(self.pre.to_xml(document, E=E, **kwargs),
                             *pcs['pre']),
                    E.Destination(self.post.to_xml(document, E=E, **kwargs),
                                  *pcs['post']),
                    E.Response(self.response.to_xml(document, E=E, **kwargs),
                               *pcs['response']),
                    E.Connectivity(
                        self.connectivity.to_xml(document, E=E, **kwargs))]
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
                E.Connectivity(self.connectivity.to_xml(document, E=E,
                                                        **kwargs)),
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
        connectivity = from_child_xml(element, ConnectionRuleProperties,
                                      document, within='Connectivity',
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
                   connectivity=connectivity,
                   delay=delay,
                   port_connections=port_connections,
                   document=document)

    version1_nodes = ('Source', 'Destination', 'Response', 'Plasticity')
    v1tov2 = {'Source': 'pre', 'Destination': 'post',
              'Plasticity': 'plasticity', 'Response': 'response'}
