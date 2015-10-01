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
from nineml.exceptions import NineMLRuntimeError, NineMLImmutableError
from ..port_connections import AnalogPortConnection


class _BasePortExposure(BaseULObject):

    defining_attributes = ('_name', '_component', '_port')

    def __init__(self, name, component, port):
        super(_BasePortExposure, self).__init__()
        self._name = name
        self._component_name = component
        self._port_name = port
        self._sub_component = None
        self._port = None

    @property
    def name(self):
        return self._name

    @property
    def sub_component(self):
        if self._sub_component is None:
            raise NineMLRuntimeError(
                "Port exposure is not bound")
        return self._sub_component

    @property
    def port(self):
        if self._port is None:
            raise NineMLRuntimeError(
                "Port exposure is not bound")
        return self._port

    @property
    def sub_component_name(self):
        try:
            return self.sub_component.name
        except NineMLRuntimeError:
            return self._sub_component_name

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
                 sub_component=self.sub_component_name,
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
        self._sub_component = container[self._component_name]
        self._port = self._sub_component.component_class.port(self._port_name)
        self._component_name = None
        self._port_name = None


class _BaseAnalogPortExposure(_BasePortExposure):

    def lhs_name_transform_inplace(self, name_map):
        raise NineMLImmutableError(
            "Cannot rename LHS of Alias '{}' because it is a analog port "
            "exposure".format(self.lhs))

    @property
    def dimension(self):
        return self.port.dimension

    def set_dimension(self, dimension):
        raise NineMLImmutableError(
            "Cannot set dimension of port exposure (need to change the "
            "dimension of the referenced port).")


class PortExposureAlias(Alias):

    def __init__(self, exposure):
        self._exposure = exposure

    @property
    def _name(self):
        return self.lhs

    @property
    def exposure(self):
        return self._exposure


class SendPortExposureAlias(PortExposureAlias):

    element_name = 'SendPortExposureAlias'

    @property
    def lhs(self):
        return self.exposure.name

    @property
    def rhs(self):
        return sympy.Symbol(
            self.exposure.sub_component.append_namespace(
                self.exposure.port_name))


class ReceivePortExposureAlias(PortExposureAlias):

    element_name = 'ReceivePortExposureAlias'

    @property
    def lhs(self):
        return self.exposure.sub_component.append_namespace(
            self.exposure.port_name)

    @property
    def rhs(self):
        return sympy.Symbol(self.exposure.name)


class AnalogSendPortExposure(_BaseAnalogPortExposure, AnalogSendPort):

    element_name = 'AnalogSendPortExposure'

    @property
    def alias(self):
        return SendPortExposureAlias(self)


class AnalogReceivePortExposure(_BaseAnalogPortExposure, AnalogReceivePort):

    element_name = 'AnalogReceivePortExposure'

    @property
    def alias(self):
        return ReceivePortExposureAlias(self)


class AnalogReducePortExposure(_BaseAnalogPortExposure, AnalogReducePort):

    element_name = 'AnalogReducePortExposure'

    @property
    def alias(self):
        return ReceivePortExposureAlias(self)


class EventSendPortExposure(_BasePortExposure, EventSendPort):

    element_name = 'EventSendPortExposure'


class EventReceivePortExposure(_BasePortExposure, EventReceivePort):

    element_name = 'EventReceivePortExposure'


class _LocalAnalogPortConnection(AnalogPortConnection, Alias):

    def __init__(self, port_connection):
        snd_name = port_connection.sender_name
        rcv_name = port_connection.receiver_name
        snd_prt_name = port_connection.send_port_name
        rcv_prt_name = port_connection.receive_port_name
        AnalogPortConnection.__init__(
            self, sender_name=snd_name, send_port=snd_prt_name,
            receiver_name=rcv_name, receive_port=rcv_prt_name)

    @property
    def lhs(self):
        return self.receiver.append_namespace(self.receive_port_name)

    @property
    def rhs(self):
        return sympy.Symbol(self.sender.append_namespace(self.send_port_name))

    def lhs_name_transform_inplace(self, name_map):
        raise NineMLImmutableError(
            "Cannot rename LHS of Alias '{}' because it is a local "
            "AnalogPortConnection".format(self.lhs))

    @property
    def _name(self):
        return self.lhs


class _LocalReducePortConnections(Alias):

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
