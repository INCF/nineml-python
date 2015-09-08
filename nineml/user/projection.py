# encoding: utf-8
from . import BaseULObject
from nineml.reference import resolve_reference, write_reference, Reference
from nineml.xmlns import NINEML, E
from nineml.annotations import read_annotations, annotate_xml
from .component import ConnectionRuleProperties
from itertools import chain
import nineml.units as un
from nineml.utils import (
    expect_single, expect_none_or_single)
from .values import SingleValue
from .component import Quantity
from nineml import DocumentLevelObject
from .port_connections import AnalogPortConnection, EventPortConnection
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

    def __init__(self, name, pre, post, response, plasticity, connectivity,
                 delay, port_connections=[], url=None):
        """
        Create a new projection.
        """
        BaseULObject.__init__(self)
        DocumentLevelObject.__init__(self, url)
        assert isinstance(name, basestring)
        self.name = name
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
        for port_connection in port_connections:
            port_connection.bind_ports()

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
    def to_xml(self, document, **kwargs):  # @UnusedVariable
        children = (self.pre, self.post, self.response, self.plasticity,
                    self.connectivity, self.delay)
        return E(self.element_name,
                 *[m.to_xml(document, **kwargs) for m in children
                   if m is not None],
                 name=self.name)

    @classmethod
    @resolve_reference
    @read_annotations
    @handle_xml_exceptions
    def from_xml(cls, element, document, **kwargs):  # @UnusedVariable
        cls.check_tag(element)
        # Get Name
        name = element.attrib['name']
        # Get Pre
        pre = expect_single(element.findall(NINEML + 'Pre'))
        post = expect_single(element.findall(NINEML + 'Post'))
        response = expect_single(element.findall(NINEML + 'Response'))
        plasticity = expect_none_or_single(element.findall(NINEML +
                                                           'Plasticity'))
        if plasticity is None:
            pass
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
    def to_xml(self, document, **kwargs):  # @UnusedVariable
        return E.Connectivity(ConnectionRuleProperties.to_xml(
            self, document, **kwargs))

    @classmethod
    @read_annotations
    def from_xml(cls, element, document, **kwargs):  # @UnusedVariable
        assert element.tag in ('Connectivity', NINEML + 'Connectivity'), (
            "Found '{}' element, expected '{}'".format(element.tag,
                                                       'Connectivity'))
        component = ConnectionRuleProperties.from_xml(
            expect_single(element.findall(
                NINEML + 'ConnectionRuleProperties')), document)
        return cls(*component.__getinitargs__())
