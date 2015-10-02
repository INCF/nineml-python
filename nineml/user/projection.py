# encoding: utf-8
from . import BaseULObject
from nineml.reference import resolve_reference, write_reference, Reference
from nineml.xmlns import NINEML, E
from nineml.annotations import read_annotations, annotate_xml
from .component import ConnectionRuleProperties, DynamicsProperties
from copy import copy
from itertools import chain
from nineml.utils import (
    expect_single, expect_none_or_single)
from .component import Quantity
from nineml import DocumentLevelObject
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
    element_name = "Projection"
    defining_attributes = ("name", "pre", "post", "connectivity",
                           "response", "plasticity", "delay")

    _component_roles = set(['pre', 'post', 'plasticity', 'response'])

    def __init__(self, name, pre, post, response, connectivity,
                 delay, plasticity=None, port_connections=[], url=None):
        """
        Create a new projection.
        """
        BaseULObject.__init__(self)
        DocumentLevelObject.__init__(self, url)
        assert isinstance(name, basestring)
        assert isinstance(delay, Quantity)
        self.name = name
        assert pre.name != post.name
        self._pre = pre
        self._post = post
        self._response = response
        self._plasticity = plasticity
        self._connectivity = connectivity
        self._delay = delay
        self._port_connections = []
        for port_connection in port_connections:
            if isinstance(port_connection, tuple):
                port_connection = BasePortConnection.from_tuple(
                    port_connection, self)
            port_connection.bind(self, to_roles=True)
            self._port_connections.append(port_connection)

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
    def port_connections(self):
        return self._port_connections

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
    def to_xml(self, document, **kwargs):  # @UnusedVariable
        as_ref_kwargs = copy(kwargs)
        as_ref_kwargs['as_reference'] = True
        members = []
        for pop, tag_name in ((self.pre, 'Pre'), (self.post, 'Post')):
            pop.set_local_reference(document, overwrite=False)
            members.append(E(tag_name, pop.to_xml(document, **as_ref_kwargs)))
        members.extend([
            E.Response(self.response.to_xml(document, **kwargs)),
            E.Connectivity(self.connectivity.to_xml(document, **kwargs)),
            E.Delay(self.delay.to_xml(document, **kwargs))])
        if self.plasticity is not None:
            members.append(
                E.Plasticity(self.plasticity.to_xml(document, **kwargs)))
        members.extend([pc.to_xml(document, **kwargs)
                        for pc in self.port_connections])
        return E(self.element_name, *members, name=self.name)

    @classmethod
    @resolve_reference
    @read_annotations
    def from_xml(cls, element, document, **kwargs):  # @UnusedVariable
        cls.check_tag(element)
        # Get Name
        name = element.get('name')
        # Get Pre
        pre = Reference.from_xml(
            expect_single(
                expect_single(element.findall(NINEML + 'Pre'))
                .findall(
                    NINEML + 'Reference')), document, **kwargs).user_object
        post = Reference.from_xml(
            expect_single(
                expect_single(element.findall(NINEML + 'Post'))
                .findall(
                    NINEML + 'Reference')), document, **kwargs).user_object
        response = DynamicsProperties.from_xml(
            expect_single(
                expect_single(element.findall(NINEML + 'Response'))
                .findall(NINEML + 'DynamicsProperties')), document, **kwargs)
        plasticity = expect_none_or_single(
            element.findall(NINEML + 'Plasticity'))
        if plasticity is not None:
            plasticity = DynamicsProperties.from_xml(
                expect_single(
                    plasticity.findall(
                        NINEML + 'DynamicsProperties')), document, **kwargs)
        connectivity = ConnectionRuleProperties.from_xml(
            expect_single(
                expect_single(element.findall(NINEML + 'Connectivity'))
                .findall(
                    NINEML + 'ConnectionRuleProperties')), document, **kwargs)
        analog_port_connections = [
            AnalogPortConnection.from_xml(pc, document, **kwargs)
            for pc in element.findall(NINEML + 'AnalogPortConnection')]
        event_port_connections = [
            EventPortConnection.from_xml(pc, document, **kwargs)
            for pc in element.findall(NINEML + 'EventPortConnection')]
        # Get Delay
        delay = Quantity.from_xml(
            expect_single(
                expect_single(element.findall(NINEML + 'Delay'))
                .findall(NINEML + 'Quantity')), document, **kwargs)
        return cls(name=name,
                   pre=pre,
                   post=post,
                   response=response,
                   plasticity=plasticity,
                   connectivity=connectivity,
                   delay=delay,
                   port_connections=chain(analog_port_connections,
                                          event_port_connections),
                   url=document.url)
