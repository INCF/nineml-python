from itertools import chain
from .. import BaseULObject
import sympy
import operator
from nineml.abstraction import (
    AnalogSendPort, AnalogReceivePort, AnalogReducePort, EventSendPort,
    EventReceivePort, Alias, Dynamics)
from nineml.xml import E, unprocessed_xml, get_xml_attr
from nineml.annotations import annotate_xml, read_annotations
from nineml.exceptions import NineMLRuntimeError, NineMLImmutableError
from .namespace import append_namespace


class BasePortExposure(BaseULObject):

    defining_attributes = ('_name', '_sub_component', '_port')

    def __init__(self, component, port, name=None):
        super(BasePortExposure, self).__init__()
        self._name = name
        if isinstance(component, basestring):
            self._sub_component_name = component
            self._sub_component = None
        else:
            self._sub_component_name = None
            try:
                assert isinstance(component, Dynamics)
            except:
                raise
            self._sub_component = component
        if isinstance(port, basestring):
            self._port_name = port
            self._port = None
        else:
            self._port = port
            self._port_name = None

    @property
    def name(self):
        if self._name is not None:
            name = self._name
        else:
            name = append_namespace(self.port_name, self.sub_component_name)
        return name

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
    def local_port_name(self):
        return append_namespace(self.port_name, self.sub_component_name)

    @property
    def attributes_with_units(self):
        return chain(*[c.attributes_with_units for c in self.sub_component])

    @annotate_xml
    def to_xml(self, document, E=E, **kwargs):  # @UnusedVariable
        return E(self.nineml_type,
                 name=self.name,
                 sub_component=self.sub_component_name,
                 port=self.port_name)

    @classmethod
    @read_annotations
    @unprocessed_xml
    def from_xml(cls, element, document, **kwargs):  # @UnusedVariable
        return cls(name=get_xml_attr(element, 'name', document, **kwargs),
                   component=get_xml_attr(element, 'sub_component', document,
                                          **kwargs),
                   port=get_xml_attr(element, 'port', document, **kwargs))

    @classmethod
    def from_tuple(cls, tple, container):
        component_name, port_name = tple[:2]
        try:
            name = tple[2]
        except IndexError:
            name = None
        port = container.sub_component(component_name).component_class.port(
            port_name)
        return cls.from_port(name, port, component_name)

    @classmethod
    def from_port(cls, port, component_name, name=None):
        if isinstance(port, AnalogSendPort):
            exposure = AnalogSendPortExposure(
                name=name, component=component_name, port=port.name)
        elif isinstance(port, AnalogReceivePort):
            exposure = AnalogReceivePortExposure(
                name=name, component=component_name, port=port.name)
        elif isinstance(port, AnalogReducePort):
            exposure = AnalogReducePortExposure(
                name=name, component=component_name, port=port.name)
        elif isinstance(port, EventSendPort):
            exposure = EventSendPortExposure(
                name=name, component=component_name, port=port.name)
        elif isinstance(port, EventReceivePort):
            exposure = EventReceivePortExposure(
                name=name, component=component_name, port=port.name)
        else:
            assert False
        return exposure

    def bind(self, container):
        self._sub_component = container[self.sub_component_name]
        self._port = self._sub_component.component_class.port(self.port_name)
        self._sub_component_name = None
        self._port_name = None


class _BaseAnalogPortExposure(BasePortExposure):

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


class _PortExposureAlias(Alias):

    def __init__(self, exposure):
        self._exposure = exposure

    @property
    def _name(self):
        return self.lhs

    @property
    def exposure(self):
        return self._exposure


class _SendPortExposureAlias(_PortExposureAlias):

    nineml_type = '_SendPortExposureAlias'

    @property
    def lhs(self):
        return self.exposure.name

    @property
    def rhs(self):
        return sympy.Symbol(
            self.exposure.sub_component.append_namespace(
                self.exposure.port_name))


class _ReceivePortExposureAlias(_PortExposureAlias):

    nineml_type = '_ReceivePortExposureAlias'

    @property
    def lhs(self):
        return self.exposure.sub_component.append_namespace(
            self.exposure.port_name)

    @property
    def rhs(self):
        return sympy.Symbol(self.exposure.name)


class AnalogSendPortExposure(_BaseAnalogPortExposure, AnalogSendPort):

    nineml_type = 'AnalogSendPortExposure'

    @property
    def alias(self):
        return _SendPortExposureAlias(self)


class AnalogReceivePortExposure(_BaseAnalogPortExposure, AnalogReceivePort):

    nineml_type = 'AnalogReceivePortExposure'

    @property
    def alias(self):
        return _ReceivePortExposureAlias(self)


class AnalogReducePortExposure(_BaseAnalogPortExposure, AnalogReducePort):

    nineml_type = 'AnalogReducePortExposure'

    @property
    def alias(self):
        return _ReceivePortExposureAlias(self)


class EventSendPortExposure(BasePortExposure, EventSendPort):

    nineml_type = 'EventSendPortExposure'


class EventReceivePortExposure(BasePortExposure, EventReceivePort):

    nineml_type = 'EventReceivePortExposure'


class _LocalAnalogPortConnections(Alias):

    def __init__(self, receive_port, receiver, port_connections, parent):
        self._receive_port_name = receive_port
        self._receiver_name = receiver
        self._port_connections = port_connections
        self._parent = parent

    def __hash__(self):
        return (hash(self._receive_port_name) ^ hash(self._receiver_name) ^
                hash(self._parent))

    @property
    def receive_port_name(self):
        return self._receive_port_name

    @property
    def receiver_name(self):
        return self._receiver_name

    @property
    def port_connections(self):
        return iter(self._port_connections)

    @property
    def name(self):
        return self.lhs

    @property
    def _name(self):
        # Required for duck-typing
        return self.name

    @property
    def lhs(self):
        return append_namespace(self.receive_port_name, self.receiver_name)

    @property
    def rhs(self):
        return reduce(
            operator.add,
            (sympy.Symbol(pc.sender.append_namespace(pc.send_port_name))
             for pc in self.port_connections), 0)

    def lhs_name_transform_inplace(self, name_map):
        raise NineMLImmutableError(
            "Cannot rename LHS of Alias '{}' because it is a local "
            "AnalogPortConnection".format(self.lhs))
