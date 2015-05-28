# encoding: utf-8
import sys
from . import BaseULObject
from .component import resolve_reference, write_reference, Reference
from nineml.xmlns import NINEML, E
from nineml.annotations import read_annotations, annotate_xml
from nineml.exceptions import NineMLRuntimeError
from .component import DynamicsProperties, ConnectionRuleProperties
from .population import Population
from itertools import chain
import nineml.units as un
from nineml.utils import (
    expect_single, check_tag, normalise_parameter_as_list,
    expect_none_or_single)
from .values import SingleValue
from .component import Quantity
from nineml import DocumentLevelObject
from nineml.exceptions import handle_xml_exceptions
from nineml.abstraction.ports import Port


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
    element_name = "Projection"
    defining_attributes = ("name", "pre", "post", "connectivity",
                           "response", "plasticity", "delay")

    _component_roles = set(['pre', 'post', 'plasticity', 'response'])

    def __init__(self, name, pre, post, response,
                 plasticity, connectivity, delay, url=None):
        """
        Create a new projection.
        """
        BaseULObject.__init__(self)
        DocumentLevelObject.__init__(self, url)
        assert isinstance(name, basestring)
        self.name = name
        # Check types of input arguments
        if not isinstance(pre, Pre):
            pre = Pre(*normalise_parameter_as_list(pre))
        if not isinstance(post, Post):
            post = Post(*normalise_parameter_as_list(post))
        if not isinstance(response, Response):
            response = Response(*normalise_parameter_as_list(response))
        if plasticity is not None and not isinstance(plasticity, Plasticity):
            plasticity = Plasticity(*normalise_parameter_as_list(plasticity))
        if isinstance(delay, tuple):
            value, units = delay
            delay = Delay(SingleValue(value), units)
        self._pre = pre
        self._post = post
        self._response = response
        self._plasticity = plasticity
        self._connectivity = connectivity
        self._delay = delay
        # Connect ports between terminuses
        for terminus in (self.pre, self.post, self.response, self.plasticity):
            if terminus is not None:
                terminus.bind_ports(self)

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
        components = [self.connectivity, self.response.component]
        if self.plasticity is not None:
            components.append(self.plasticity.component)
        return components

    @property
    def attributes_with_units(self):
        return chain([self.delay],
                     *[c.attributes_with_units for c in self.components])

    @write_reference
    @annotate_xml
    def to_xml(self):
        children = (self.pre, self.post, self.response, self.plasticity,
                    self.connectivity, self.delay)
        return E(self.element_name,
                 *(m.to_xml() for m in children if m is not None),
                 name=self.name)

    @classmethod
    @resolve_reference
    @read_annotations
    @handle_xml_exceptions
    def from_xml(cls, element, document):
        cls.check_tag(element)
        # Get Name
        name = element.attrib['name']
        # Get Pre
        pre = Pre.from_xml(expect_single(element.findall(NINEML + 'Pre')),
                           document)
        post = Post.from_xml(expect_single(element.findall(NINEML + 'Post')),
                             document)
        response = Response.from_xml(
            expect_single(element.findall(NINEML + 'Response')), document)
        elem = expect_none_or_single(element.findall(NINEML + 'Plasticity'))
        plasticity = (Plasticity.from_xml(elem, document)
                      if elem is not None else None)
        connectivity = Connectivity.from_xml(
            expect_single(element.findall(NINEML + 'Connectivity')), document)
        # Get Delay
        delay = Delay.from_xml(
            expect_single(element.findall(NINEML + 'Delay')), document)
        return cls(name=name,
                   pre=pre,
                   post=post,
                   response=response,
                   plasticity=plasticity,
                   connectivity=connectivity,
                   delay=delay,
                   url=document.url)


class Terminus(BaseULObject):

    defining_attributes = ('_object', '_port_connections')

    def __init__(self, obj, port_connections=None):
        BaseULObject.__init__(self)
        self._object = obj
        self._port_connections = dict(
            (pc.port_name, pc)
            for pc in normalise_parameter_as_list(port_connections))

    def bind_ports(self, container):
        for pc in self.port_connections:
            pc.bind_ports(self, container)

    @property
    def port_connections(self):
        return self._port_connections.itervalues()

    @property
    def port_connection_port_names(self):
        return self._port_connections.iterkeys()

    def port_connection(self, port_name):
        return self._port_connections[port_name]

    @property
    def object(self):
        return self._object

    @annotate_xml
    def _port_connections_to_xml(self):
        return (pc.to_xml() for pc in self.port_connections)

    @classmethod
    def _port_connections_from_xml(cls, element, document):
        return (PortConnection.from_xml(e, document)
                for e in element.findall(NINEML + 'PortConnection'))


class PopulationTerminus(Terminus):

    def __init__(self, population, port_connections=None):
        assert isinstance(population, Population)
        super(PopulationTerminus, self).__init__(population, port_connections)

    @property
    def population(self):
        return self.object

    @property
    def component(self):
        return self.object.cell

    @annotate_xml
    def to_xml(self):
        if self.population.from_reference is None:  # Generated objects
            # Assumes that population is written in same file as projection
            pop_elem = E.Reference(self.population.name)
        else:
            pop_elem = self.population.to_xml(as_reference=True)
        return E(self.element_name, pop_elem,
                 *self._port_connections_to_xml())

    @classmethod
    @read_annotations
    def from_xml(cls, element, document):  # @UnusedVariable
        cls.check_tag(element)
        population = Reference.from_xml(
            expect_single(element.findall(NINEML + 'Reference')),
            document).user_layer_object
        return cls(population,
                   cls._port_connections_from_xml(element, document))


class ComponentTerminus(Terminus):

    def __init__(self, component, port_connections=None):
        assert isinstance(component, Component)
        super(ComponentTerminus, self).__init__(component, port_connections)

    @property
    def component(self):
        return self.object

    @annotate_xml
    def to_xml(self):
        return E(self.element_name, self.component.to_xml(),
                 *self._port_connections_to_xml())

    @classmethod
    @read_annotations
    def from_xml(cls, element, document):  # @UnusedVariable
        cls.check_tag(element)
        component = Component.from_xml(
            expect_single(element.findall(NINEML + 'Component')),
            document)
        return cls(component,
                   cls._port_connections_from_xml(element, document))


class Pre(PopulationTerminus):

    element_name = 'Pre'


class Post(PopulationTerminus):

    element_name = 'Post'


class Response(ComponentTerminus):

    element_name = 'Response'


class Plasticity(ComponentTerminus):

    element_name = 'Plasticity'


class BasePortConnection(BaseULObject):

    defining_attributes = ('port_name',)

    def __init__(self, port):
        BaseULObject.__init__(self)
        self._set_port(port)

    @property
    def port_name(self):
        try:
            return self._port.name
        except AttributeError:
            return self._port_name

    @property
    def port(self):
        try:
            return self._port
        except AttributeError:
            raise NineMLRuntimeError(
                "PortConnection '{}' not bound".format(self._port_name))

    def _set_port(self, port):
        if isinstance(port, Port):
            self._port = port
            try:
                del self._port_name
            except AttributeError:
                pass
        else:
            self._port_name = port


class PortConnection(BasePortConnection):

    element_name = 'PortConnection'
    defining_attributes = (BasePortConnection.defining_attributes +
                           ('_senders',))

    def __init__(self, port, senders):
        super(PortConnection, self).__init__(port)
        senders = normalise_parameter_as_list(senders)
        assert all(isinstance(s, Sender) for s in senders)
        self._senders = dict((s.key(), s) for s in senders)

    def __repr__(self):
        return ("PortConnection('{}' with {} senders)"
                .format(self.port_name, len(self.senders)))

    @property
    def senders(self):
        return self._senders.itervalues()

    @property
    def sender_keys(self):
        return self._senders.iterkeys()

    def sender(self, *key):
        return self._senders[key]

    def bind_ports(self, receiver, container):
        """
        Binds the PortConnection to the components it is connecting
        """
        self._set_port(
            receiver.component.component_class.receive_port(self.port_name))
        for sender in self.senders:
            sender.bind_port(container)

    @annotate_xml
    def to_xml(self):
        return E(self.element_name, *(s.to_xml() for s in self.senders),
                 port=self.port_name)

    @classmethod
    @read_annotations
    def from_xml(cls, element, document):
        cls.check_tag(element)
        return cls(port=element.get('port'),
                   senders=[Sender.from_xml(e, document) for e in element])


class Sender(BasePortConnection):

    def __init__(self, port):
        BaseULObject.__init__(self)
        self._set_port(port)

    def key(self):
        """
        Generates a unique key for the Sender so it can be stored in a dict
        """
        return (self.element_name, self._port_name)

    @annotate_xml
    def to_xml(self):
        return E(self.element_name, port=self.port_name)

    @classmethod
    def from_xml(cls, element, document):
        return getattr(sys.modules[__name__],
                       element.tag[len(NINEML):])._from_xml(element, document)

    @classmethod
    @read_annotations
    def _from_xml(cls, element, document):  # @UnusedVariable
        cls.check_tag(element)
        return cls(port=element.get('port'))


class FromPre(Sender):

    element_name = 'FromPre'

    def bind_port(self, projection):
        self._set_port(
            projection.pre.population.cell.component_class.send_port(
                self.port_name))


class FromPost(Sender):

    element_name = 'FromPost'

    def bind_port(self, projection):
        self._set_port(
            projection.post.population.cell.component_class.send_port(
                self.port_name))


class FromPlasticity(Sender):

    element_name = 'FromPlasticity'

    def bind_port(self, projection):
        self._set_port(
            projection.plasticity.component.component_class.send_port(
                self.port_name))


class FromResponse(Sender):

    element_name = 'FromResponse'

    def bind_port(self, projection):
        self._set_port(projection.response.component.component_class.send_port(
            self.port_name))


class Delay(Quantity):
    """
    Representation of the connection delay.

    **Arguments**:
        *value*
            a numerical value, array of such values, or a component which
            generates such values (e.g. a random number generator). Allowed
            types are :class:`int`, :class:`float`, :class:`SingleValue`,
            :class:`ArrayValue', :class:`ExternalArrayValue`,
            :class:`ComponentValue`.
        *units*
            a :class:`Unit` object representing the physical units of the
            value.

    Numerical values may either be numbers, or a component that generates
    numbers, e.g. a RandomDistribution instance.
    """
    element_name = 'Delay'

    def __init__(self, value, units):
        if units.dimension != un.time:
            raise Exception("Units for delay must be of the time dimension "
                            "(found {})".format(units))
        Quantity.__init__(self, value, units)


class Connectivity(ConnectionRuleProperties):

    @annotate_xml
    def to_xml(self):
        return E.Connectivity(ConnectionRuleProperties.to_xml(self))

    @classmethod
    @read_annotations
    def from_xml(cls, element, document):
        assert element.tag in ('Connectivity', NINEML + 'Connectivity'), (
            "Found '{}' element, expected '{}'".format(element.tag,
                                                       'Connectivity'))
        component = ConnectionRuleProperties.from_xml(
            expect_single(element.findall(
                NINEML + 'ConnectionRuleProperties')), document)
        return cls(*component.__getinitargs__())
