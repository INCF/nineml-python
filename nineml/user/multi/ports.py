from itertools import chain
from .. import BaseULObject
import sympy
import operator
from nineml.abstraction import (
    AnalogSendPort, AnalogReceivePort, AnalogReducePort, EventSendPort,
    EventReceivePort, Alias)
from nineml.reference import resolve_reference, write_reference
from nineml.xmlns import E
from nineml.annotations import annotate_xml, read_annotations
from nineml.exceptions import NineMLRuntimeError
from ..port_connections import AnalogPortConnection
from .namespace import append_namespace


class LocalAnalogPortConnection(AnalogPortConnection, Alias):

    def __init__(self, port_connection):
        snd_name = port_connection.sender_name
        rcv_name = port_connection.receiver_name
        snd_prt_name = port_connection.send_port_name
        rcv_prt_name = port_connection.receive_port_name
        AnalogPortConnection.__init__(
            self, sender_name=snd_name, send_port=snd_prt_name,
            receiver_name=rcv_name, receive_port=rcv_prt_name)
        Alias.__init__(
            self, port_connection.receiver.append_namespace(rcv_prt_name),
            port_connection.sender.append_namespace(snd_prt_name))


class LocalReducePortConnections(Alias):

    def __init__(self, receive_port, receiver, port_connections):
        self._receive_port_name = receive_port
        self._receiver = receiver
        self._port_connections = port_connections

    @property
    def receive_port_name(self):
        return self._receive_port_name

    @property
    def receiver(self):
        return self._receiver

    @property
    def receiver_name(self):
        return self._receiver.name

    @property
    def port_connections(self):
        return iter(self._port_connections)

    @property
    def name(self):
        return self._receiver.append_namespace(self.receive_port_name)

    @property
    def _name(self):
        # Required for duck-typing
        return self.name

    @property
    def rhs(self):
        return reduce(
            operator.add,
            (sympy.Symbol(pc.sender.append_namespace(pc.send_port_name))
             for pc in self.port_connections))


class BasePortExposure(BaseULObject):

    defining_attributes = ('_name', '_component', '_port')

    def __init__(self, name, component, port):
        super(BasePortExposure, self).__init__()
        self._name = name
        self._component_name = component
        self._port_name = port
        self._component = None
        self._port = None

    @property
    def name(self):
        return self._name

    @property
    def component(self):
        if self._component is None:
            raise NineMLRuntimeError(
                "Port exposure is not bound")
        return self._component

    @property
    def port(self):
        if self._port is None:
            raise NineMLRuntimeError(
                "Port exposure is not bound")
        return self._port

    @property
    def component_name(self):
        try:
            return self.component.name
        except NineMLRuntimeError:
            return self._component_name

    @property
    def port_name(self):
        try:
            return self.port.name
        except NineMLRuntimeError:
            return self._port_name

    @property
    def attributes_with_units(self):
        return chain(*[c.attributes_with_units for c in self.sub_component])

    @write_reference
    @annotate_xml
    def to_xml(self, document, **kwargs):  # @UnusedVariable
        return E(self.element_name,
                 name=self.name,
                 component=self.component_name,
                 port=self.port_name)

    @classmethod
    @resolve_reference
    @read_annotations
    def from_xml(cls, element, document, **kwargs):  # @UnusedVariable
        cls.check_tag(element)
        return cls(name=element.attrib['name'],
                   component=element.attrib['component'],
                   port=element.attrib['port'])

    @classmethod
    def from_tuple(cls, tple, container):
        name, component_name, port_name = tple
        port = container.sub_component(component_name).component_class.port(
            port_name)
        if isinstance(port, AnalogSendPort):
            exposure = AnalogSendPortExposure(name, component_name, port_name)
        elif isinstance(port, AnalogReceivePort):
            exposure = AnalogReceivePortExposure(name, component_name,
                                                 port_name)
        elif isinstance(port, AnalogReducePort):
            exposure = AnalogReducePortExposure(name, component_name,
                                                port_name)
        elif isinstance(port, EventSendPort):
            exposure = EventSendPortExposure(name, component_name, port_name)
        elif isinstance(port, EventReceivePort):
            exposure = EventReceivePortExposure(name, component_name,
                                                port_name)
        else:
            assert False
        return exposure

    def bind(self, container):
        self._component = container[self._component_name]
        self._port = self._component.component_class.port(self._port_name)
        self._component_name = None
        self._port_name = None


class AnalogSendPortExposure(BasePortExposure, AnalogSendPort):

    element_name = 'AnalogSendPortExposure'


class AnalogReceivePortExposure(BasePortExposure, AnalogReceivePort):

    element_name = 'AnalogReceivePortExposure'


class AnalogReducePortExposure(BasePortExposure, AnalogReducePort):

    element_name = 'AnalogReducePortExposure'


class EventSendPortExposure(BasePortExposure, EventSendPort):

    element_name = 'EventSendPortExposure'


class EventReceivePortExposure(BasePortExposure, EventReceivePort):

    element_name = 'EventReceivePortExposure'
