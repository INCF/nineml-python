from past.builtins import basestring
from itertools import chain
from .. import BaseULObject
import sympy
import operator
from nineml.base import BaseNineMLObject
from nineml.abstraction import (
    AnalogSendPort, AnalogReceivePort, AnalogReducePort, EventSendPort,
    EventReceivePort, Alias)
from nineml.exceptions import (
    NineMLNotBoundException, NineMLImmutableError, NineMLTargetMissingError,
    NineMLNameError)
from .namespace import append_namespace
from nineml.utils import validate_identifier
from functools import reduce


class BasePortExposure(BaseULObject):

    nineml_attr = ('name', 'port_name', 'sub_component_name')
    nineml_child = {}

    def __init__(self, sub_component_name, port_name, name=None):
        super(BasePortExposure, self).__init__()
        assert isinstance(sub_component_name, basestring)
        self._sub_component_name = sub_component_name
        assert isinstance(port_name, basestring)
        self._port_name = port_name
        if name is None:
            name = append_namespace(self.port_name, self.sub_component_name)
        else:
            validate_identifier(name)
        self._name = name
        self._parent = None

    def __hash__(self):
        return (hash(self._name) ^ hash(self._sub_component_name) ^
                hash(self._port_name))

    def __repr__(self):
        return "{}(comp={}, port={})".format(
            self.nineml_type, self.sub_component_name, self.port_name)

    @property
    def name(self):
        return self._name

    @property
    def sub_component(self):
        if self._parent is None:
            raise NineMLNotBoundException(
                "Port exposure is not bound")
        try:
            return self._parent[self.sub_component_name]
        except NineMLNameError:
            raise NineMLTargetMissingError(
                "Did not find sub-component '{}' the target sub-component "
                "may have been moved after the '{}' port-exposure was bound.")

    @property
    def port(self):
        if self._parent is None:
            raise NineMLNotBoundException(
                "Port exposure is not bound")
        try:
            return self.sub_component.component_class.port(self.port_name)
        except NineMLNameError:
            raise NineMLTargetMissingError(
                "Did not find port '{}' in sub-component '{}', target port "
                "may have been moved after the '{}' port-exposure was bound.")

    @property
    def sub_component_name(self):
        return self._sub_component_name

    @property
    def port_name(self):
        return self._port_name

    @property
    def local_port_name(self):
        return append_namespace(self.port_name, self.sub_component_name)

    @property
    def attributes_with_units(self):
        return chain(*[c.attributes_with_units for c in self.sub_component])

    def serialize_node(self, node, **options):  # @UnusedVariable
        node.attr('name', self.name, **options)
        node.attr('sub_component', self.sub_component_name, **options)
        node.attr('port', self.port_name, **options)

    @classmethod
    def unserialize_node(cls, node, **options):  # @UnusedVariable
        return cls(name=node.attr('name', **options),
                   sub_component_name=node.attr('sub_component', **options),
                   port_name=node.attr('port', **options))

    @classmethod
    def from_tuple(cls, tple, container):
        component_name, port_name = tple[:2]
        try:
            name = tple[2]
        except IndexError:
            name = None
        port = container.sub_component(component_name).component_class.port(
            port_name)
        return cls.from_port(name=name, port=port,
                             component_name=component_name)

    @classmethod
    def from_port(cls, port, component_name, name=None):
        if isinstance(port, AnalogSendPort):
            exposure = AnalogSendPortExposure(
                name=name, sub_component_name=component_name,
                port_name=port.name)
        elif isinstance(port, AnalogReceivePort):
            exposure = AnalogReceivePortExposure(
                name=name, sub_component_name=component_name,
                port_name=port.name)
        elif isinstance(port, AnalogReducePort):
            exposure = AnalogReducePortExposure(
                name=name, sub_component_name=component_name,
                port_name=port.name)
        elif isinstance(port, EventSendPort):
            exposure = EventSendPortExposure(
                name=name, sub_component_name=component_name,
                port_name=port.name)
        elif isinstance(port, EventReceivePort):
            exposure = EventReceivePortExposure(
                name=name, sub_component_name=component_name,
                port_name=port.name)
        else:
            assert False
        return exposure

    def bind(self, container):
        """
        "Bind" the port exposure to a MultiDynamics object, checking to see
        whether the sub-component/port-name pair refers to an existing port

        Parameters
        ----------
        container : MultiDynamics
            The MultiDynamics object the port exposure will belong to
        """
        self._parent = container
        self.port  # This will check to see whether the path to the port exists


class _BaseAnalogPortExposure(BasePortExposure):

    def lhs_name_transform_inplace(self, name_map):
        raise NineMLImmutableError(
            "Cannot rename LHS of Alias '{}' because it is a analog port "
            "exposure".format(self.lhs))

    @property
    def dimension(self):
        return self.port.dimension

    def set_dimension(self, dimension):
        self.port.set_dimension(dimension)


class _PortExposureAlias(Alias):

    temporary = True

    def __init__(self, exposure):
        self._exposure = exposure

    @property
    def name(self):
        return self.lhs

    @property
    def exposure(self):
        return self._exposure

    def __repr__(self):
        return "{}(name='{}', rhs='{}')".format(self.nineml_type,
                                                self.lhs, self.rhs)


class _SendPortExposureAlias(_PortExposureAlias):

    @property
    def lhs(self):
        return self.exposure.name

    @property
    def rhs(self):
        return sympy.Symbol(
            self.exposure.sub_component.append_namespace(
                self.exposure.port_name))


class _ReceivePortExposureAlias(_PortExposureAlias):

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

    @property
    def operator(self):
        return self.port.operator


class EventSendPortExposure(BasePortExposure, EventSendPort):

    nineml_type = 'EventSendPortExposure'


class EventReceivePortExposure(BasePortExposure, EventReceivePort):

    nineml_type = 'EventReceivePortExposure'


class _LocalAnalogPortConnections(Alias):

    temporary = True

    def __init__(self, receive_port, receiver, port_connections, parent):
        BaseNineMLObject.__init__(self)
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
    def key(self):
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
