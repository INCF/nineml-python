# encoding: utf-8
import sys
from . import BaseULObject
from .component import resolve_reference, write_reference, Reference
from nineml.xmlns import NINEML, E
from nineml.annotations import read_annotations, annotate_xml
from nineml.user_layer.component import Component
from itertools import chain
from .. import units as un
from nineml.utils import expect_single, check_tag
from .values import SingleValue
from .component import Quantity
from nineml import DocumentLevelObject


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
                           "response", "plasticity", "port_connections",
                           "delay")

    _component_roles = set(['pre', 'post', 'plasticity', 'response'])

    def __init__(self, name, pre, post, response,
                 plasticity, connectivity, delay, url=None):
        """
        Create a new projection.
        """
        BaseULObject.__init__(self)
        DocumentLevelObject.__init__(self, url)
        self.name = name
        self.pre = pre
        self.post = post
        self.response = response
        self.plasticity = plasticity
        self.connectivity = connectivity
        if isinstance(delay, tuple):
            value, units = delay
            delay = Delay(SingleValue(value), units)
        self.delay = delay
        for terminus in (self.pre, self.post, self.response, self.plasticity):
            terminus.connect(self)

    def __repr__(self):
        return ('Projection(name="{}", pre={}, post={}, '
                'connectivity={}, response={}{}, delay={})'
                .format(self.name, repr(self.pre), repr(self.post),
                        repr(self.connectivity), repr(self.response),
                        ('plasticity={}'.format(repr(self.plasticity))
                         if self.plasticity else ''), repr(self.delay)))

    def get_components(self):
        """
        Return a list of all components used by the projection.
        """
        components = []
        for name in ('connectivity', 'response', 'plasticity'):
            component = getattr(self, name)
            if component is not None:
                components.append(component)
        return components

    @property
    def attributes_with_units(self):
        return chain([self.delay],
                     *[c.attributes_with_units for c in self.get_components()])

    @write_reference
    @annotate_xml
    def to_xml(self):
        args = [E.Pre(self.pre.to_xml()),
                E.Post(self.post.to_xml()),
                E.Connectivity(self.connectivity.to_xml()),
                E.Response(self.response.to_xml())]
        if self.plasticity:
            args.append(E.Plasticity(self.plasticity.to_xml()))
        args.append(self.delay.to_xml())
        return E(self.element_name, *args, name=self.name)

    @classmethod
    @resolve_reference
    @read_annotations
    def from_xml(cls, element, document):
        check_tag(element, cls)
        # Get Name
        name = element.get('name')
        # Get Pre
        pre = Pre.from_xml(expect_single(element.findall(NINEML + 'Pre')))
        post = Post.from_xml(expect_single(element.findall(NINEML + 'Post')))
        response = Post.from_xml(
            expect_single(element.findall(NINEML + 'Response')))
        plasticity = Post.from_xml(
            expect_single(element.findall(NINEML + 'Plasticity')))
        connectivity = Connectivity.from_xml(
            expect_single(element.findall(NINEML + 'Connectivity')))
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

    def __init__(self, obj, port_connections):
        assert isinstance(obj, Component)
        self._object = obj
        self._port_connections = port_connections

    def connect(self, container):
        for pc in self.port_connections:
            pc.connect(self, container)

    @property
    def object(self):
        return self._object

    @annotate_xml
    def to_xml(self):
        return E(self.element_name, self.object.to_xml(),
                 (pc.to_xml() for pc in self._port_connections))

    @classmethod
    def _port_connections_from_xml(cls, element):
        return (PortConnection.from_xml(e)
                for e in element.findall(NINEML + 'PortConnection'))


class PopulationTerminus(Terminus):

    @property
    def population(self):
        return self.object

    @classmethod
    @read_annotations
    def from_xml(cls, element, document):  # @UnusedVariable
        check_tag(element, cls)
        population = Reference.from_xml(element, document).user_layer_object
        return cls(population, cls._port_connections_from_xml(element))


class ComponentTerminus(Terminus):

    @property
    def component(self):
        return self.object

    @classmethod
    @read_annotations
    def from_xml(cls, element, document):  # @UnusedVariable
        check_tag(element, cls)
        component = Component.from_xml(
            expect_single(element.findall(NINEML + 'Component')))
        return cls(component, cls._port_connections_from_xml(element))


class Pre(PopulationTerminus):

    element_name = 'Pre'


class Post(PopulationTerminus):

    element_name = 'Post'


class Response(ComponentTerminus):

    element_name = 'Response'


class Plasticity(ComponentTerminus):

    element_name = 'Plasticity'


class PortConnection(object):
    element_name = 'PortConnection'
    defining_attributes = ('_port_name', '_senders')

    def __init__(self, port, senders):
        assert isinstance(port, basestring)
        assert all(isinstance(s, Sender) for s in senders)
        self._port_name = port
        self._port = None
        self._senders = sorted(senders)

    def __repr__(self):
        return ("PortConnection('{}' with {} senders)"
                .format(self.port_name, len(self.senders)))

    @property
    def port_name(self):
        return self._port_name

    @property
    def senders(self):
        return self._senders

    @property
    def port(self):
        assert self._port is not None, "PortConnection not bound"
        return self._port

    def connect(self, receiver, container):
        """
        Binds the PortConnection to the components it is connecting
        """
        self._port = receiver.port(self.port_name)
        for sender in self.senders:
            sender.connect(container)

    @annotate_xml
    def to_xml(self):
        return E(self.element_name, *(s.to_xml() for s in self.senders),
                 port=self.port_name)

    @classmethod
    @read_annotations
    def from_xml(cls, element, document):
        check_tag(element, cls)
        cls(port=element.get('port'),
            senders=(Sender.from_xml(e, document) for e in element))


class Sender(BaseULObject):

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
        check_tag(element, cls)
        return getattr(sys.modules[__name__], element.tag).from_xml(element,
                                                                    document)

    def __hash__(self):
        return hash(self.element_name) ^ hash(self._port_name)


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
    numbers, e.g. a RandomDistribution instance.
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
        return E(self.element_name, super(Connectivity, self).to_xml())

    @classmethod
    @read_annotations
    def from_xml(cls, element, document):
        check_tag(element, cls)
        component = Component.from_xml(element, document)
        return cls(component.__getinitargs__())
