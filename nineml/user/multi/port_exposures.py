from itertools import chain
from .. import BaseULObject
import sympy
import operator
from nineml.base import clone_id, BaseNineMLObject
from nineml.abstraction import (
    AnalogSendPort, AnalogReceivePort, AnalogReducePort, EventSendPort,
    EventReceivePort, Alias)
from nineml.xml import E, unprocessed_xml, get_xml_attr
from nineml.annotations import annotate_xml, read_annotations
from nineml.exceptions import (
    NineMLRuntimeError, NineMLImmutableError, NineMLTargetMissingError,
    NineMLNameError)
from .namespace import append_namespace
from nineml.utils import ensure_valid_identifier


class BasePortExposure(BaseULObject):

    defining_attributes = ('_name', '_port_name', '_sub_component_name')

    def __init__(self, component, port, name=None):
        super(BasePortExposure, self).__init__()
        if name is not None:
            ensure_valid_identifier(name)
        self._name = name
        if isinstance(component, basestring):
            self._sub_component_name = component
        else:
            self._sub_component_name = component.name
        if isinstance(port, basestring):
            self._port_name = port
        else:
            self._port_name = port.name
        self._parent = None

    def __hash__(self):
        return (hash(self._name) ^ hash(self._sub_component_name) ^
                hash(self._port_name))

    @property
    def name(self):
        if self._name is not None:
            name = self._name
        else:
            name = append_namespace(self.port_name, self.sub_component_name)
        return name

    @property
    def sub_component(self):
        if self._parent is None:
            raise NineMLRuntimeError(
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
            raise NineMLRuntimeError(
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
        return cls.from_port(name=name, port=port,
                             component_name=component_name)

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

    def _clone_defining_attr(self, clone, memo, **kwargs):
        super(BasePortExposure, self)._clone_defining_attr(clone, memo,
                                                           **kwargs)
        clone._port_name = self._port_name
        clone._sub_component_name = self._sub_component_name


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

    def _copy_to_clone(self, clone, memo, **kwargs):
        clone._exposure = self._exposure.clone(memo=memo, **kwargs)

    @property
    def clone_id(self):
        return (type(self), clone_id(self._exposure))


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
    def clone_id(self):
        return tuple(clone_id(pc) for pc in self._port_connections)

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

    def _copy_to_clone(self, clone, memo, **kwargs):
        clone._receive_port_name = self._receive_port_name
        clone._receiver_name = self._receiver_name
        clone._port_connections = [
            pc.clone(memo=memo, **kwargs) for pc in self._port_connections]
        clone._parent = self._parent.clone(memo=memo, **kwargs)


import nineml.user.multi.dynamics  # @IgnorePep8