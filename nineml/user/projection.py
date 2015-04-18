# encoding: utf-8
import sys
from . import BaseULObject
from .component import resolve_reference, write_reference, Reference
from nineml.xmlns import NINEML, E
from nineml.annotations import read_annotations, annotate_xml
from .component import Component
from .population import Population
from itertools import chain
from .. import units as un
from nineml.utils import (
    expect_single, check_tag, normalise_parameter_as_list,
    expect_none_or_single)
from .values import SingleValue
from .component import Quantity
from nineml import DocumentLevelObject
from nineml.exceptions import handle_xml_exceptions


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
                terminus.bind_port_connections(self)

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

    def bind_port_connections(self, container):
        for pc in self.port_connections:
            pc.bind_port_connections(self, container)

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
    def to_xml(self):
        return E(self.element_name, self.object.to_xml(),
                 *(pc.to_xml() for pc in self.port_connections))

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


class PortConnection(BaseULObject):
    element_name = 'PortConnection'
    defining_attributes = ('_port_name', '_senders')

    def __init__(self, port, senders):
        BaseULObject.__init__(self)
        assert isinstance(port, basestring)
        senders = normalise_parameter_as_list(senders)
        assert all(isinstance(s, Sender) for s in senders)
        self._port_name = port
        self._port = None
        self._senders = dict((s.key(), s) for s in senders)

    def __repr__(self):
        return ("PortConnection('{}' with {} senders)"
                .format(self.port_name, len(self.senders)))

    @property
    def port_name(self):
        return self._port_name

    @property
    def senders(self):
        return self._senders.itervalues()

    @property
    def sender_keys(self):
        return self._senders.iterkeys()

    def sender(self, *key):
        return self._senders[key]

    @property
    def port(self):
        assert self._port is not None, "PortConnection not bound"
        return self._port

    def bind_port_connections(self, receiver, container):
        """
        Binds the PortConnection to the components it is connecting
        """
        self._port = receiver.component.port(self.port_name)
        for sender in self.senders:
            sender.connect(container)

    @annotate_xml
    def to_xml(self):
        return E(self.element_name, *(s.to_xml() for s in self.senders),
                 port=self.port_name)

    @classmethod
    @read_annotations
    def from_xml(cls, element, document):
        cls.check_tag(element)
        cls(port=element.get('port'),
            senders=(Sender.from_xml(e, document) for e in element))


class Sender(BaseULObject):

    defining_attributes = ('_port_name',)

    def __init__(self, port_name):
        self._port_name = port_name
        self._port = None

    @property
    def port_name(self):
        return self._port_name

    @property
    def port(self):
        assert self._port is not None, "PortConnection not bound"
        return self._port

    @annotate_xml
    def to_xml(self):
        return E(self.element_name, port=self.port_name)

    @classmethod
    @read_annotations
    def from_xml(cls, element, document):
        cls.check_tag(element)
        return getattr(sys.modules[__name__], element.tag).from_xml(element,
                                                                    document)

    def key(self):
        """
        Generates a unique key for the Sender so it can be stored in a dict
        """
        return (self.element_name, self._port_name)


class FromPre(Sender):

    element_name = 'FromPre'

    def connect(self, projection):
        self._port = projection.pre.population.port(self.port_name)


class FromPost(Sender):

    element_name = 'FromPost'

    def connect(self, projection):
        self._port = projection.post.population.port(self.port_name)


class FromPlasticity(Sender):

    element_name = 'FromPlasticity'

    def connect(self, projection):
        self._port = projection.plasticity.component.port(self.port_name)


class FromResponse(Sender):

    element_name = 'FromResponse'

    def connect(self, projection):
        self._port = projection.response.component.port(self.port_name)


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
    numbers, e.g. a RandomDistributionComponent instance.
    """
    element_name = 'Delay'

    def __init__(self, value, units):
        if units.dimension != un.time:
            raise Exception("Units for delay must be of the time dimension "
                            "(found {})".format(units))
        Quantity.__init__(self, value, units)


class Connectivity(Component):

    element_name = 'Connectivity'

    @annotate_xml
    def to_xml(self):
        return E.Connectivity(Component.to_xml(self))

    @classmethod
    @read_annotations
    def from_xml(cls, element, document):
        cls.check_tag(element)
        component = Component.from_xml(
            expect_single(element.findall(NINEML + 'Component')), document)
        return cls(*component.__getinitargs__())
