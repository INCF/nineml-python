from . import BaseULObject
from abc import ABCMeta, abstractmethod
from nineml.xml import E, unprocessed_xml, get_xml_attr
from nineml.annotations import read_annotations, annotate_xml
from nineml.exceptions import (
    NineMLRuntimeError, NineMLNameError, NineMLDimensionError)
from nineml.abstraction.ports import (
    AnalogSendPort, AnalogReceivePort, AnalogReducePort, EventSendPort,
    EventReceivePort)


class BasePortConnection(BaseULObject):

    __metaclass__ = ABCMeta

    defining_attributes = ('send_port_name', 'receive_port_name',
                           '_sender_role', '_receiver_role',
                           '_sender_name', '_receiver_name')

    _projection_roles = ('pre', 'post', 'response', 'plasticity')

    def __init__(self, send_port, receive_port,
                 sender_role=None, receiver_role=None,
                 sender_name=None, receiver_name=None):
        """
        `send_port`     -- The name of the sending port
        `receiver_port` -- The name of the receiving port
        `sender_role`   -- A reference to the sending object via the role it
                           plays in the container
        `receiver_role` -- A reference to the receiving object via the role it
                           plays in the container
        `sender_name`   -- A reference to the sending object via its name,
                           which uniquely identifies it within the container
        `receiver_name` -- A reference to the receiving object via its name,
                           which uniquely identifies it within the container
        """
        BaseULObject.__init__(self)
        if isinstance(send_port, basestring):
            self._send_port_name = send_port
            self._send_port = None
        else:
            self._send_port = send_port
            self._send_port_name = None
        if isinstance(receive_port, basestring):
            self._receive_port_name = receive_port
            self._receive_port = None
        else:
            self._receive_port = receive_port
            self._receive_port_name = None
        if sender_role is not None:
            if sender_name is not None:
                raise NineMLRuntimeError(
                    "Both 'sender_role' ({}) and 'sender_name' ({}) cannot"
                    " be provided to PortConnection __init__"
                    .format(sender_role, sender_name))
        elif sender_name is None:
            raise NineMLRuntimeError(
                "Either 'sender_role' or 'sender_name' must be "
                "provided to PortConnection __init__")
        if receiver_role is not None:
            if receiver_name is not None:
                raise NineMLRuntimeError(
                    "Both 'receiver_role' ({}) and 'receiver_name' ({}) cannot"
                    " be provided to PortConnection __init__"
                    .format(receiver_role, receiver_name))
        elif receiver_name is None:
            raise NineMLRuntimeError(
                "Either 'receiver_role' or 'receiver_name' must be "
                "provided to PortConnection __init__")
        assert isinstance(sender_role, (basestring, type(None)))
        assert isinstance(sender_name, (basestring, type(None)))
        assert isinstance(receiver_name, (basestring, type(None)))
        assert isinstance(receiver_role, (basestring, type(None)))
        self._sender_role = sender_role
        self._sender_name = sender_name
        self._receiver_name = receiver_name
        self._receiver_role = receiver_role
        # Initialise members that will hold the connected objects once they are
        # bound
        self._sender = None
        self._receiver = None
        # check to see if the ports are either all bound or all not bound,
        # raising an error if they are inconsistent
        self.is_bound()

    def __repr__(self):
        return ("{}(sender={}->{}, receiver={}->{})"
                .format(self.nineml_type,
                        (self._sender_name if self._sender_name is not None
                         else 'role:' + self.sender_role),
                        self.send_port_name,
                        (self._receiver_name if self._receiver_name is not None
                         else 'role:' + self.receiver_role),
                        self.receive_port_name))

    @property
    def name(self):
        return '_'.join((
            (self.sender_role if self._sender_role is not None
             else self.sender_name), self.send_port_name,
            (self.receiver_role if self._receiver_role is not None
             else self.receiver_name), self.receive_port_name))

    @property
    def _name(self):
        return self.name  # For generic methods that look for a name in all obj

    @property
    def sender(self):
        if not self.is_bound():
            raise NineMLRuntimeError("Ports have not been bound")
        return self._sender

    @property
    def receiver(self):
        if not self.is_bound():
            raise NineMLRuntimeError("Ports have not been bound")
        return self._receiver

    @property
    def send_port(self):
        if not self.is_bound():
            raise NineMLRuntimeError("Ports have not been bound")
        return self._send_port

    @property
    def receive_port(self):
        if not self.is_bound():
            raise NineMLRuntimeError("Ports have not been bound")
        return self._receive_port

    @property
    def send_port_name(self):
        if self._send_port is None:
            return self._send_port_name
        else:
            return self._send_port.name

    @property
    def receive_port_name(self):
        if self._receive_port is None:
            return self._receive_port_name
        else:
            return self._receive_port.name

    @property
    def sender_role(self):
        if self._sender_role is None:
            raise NineMLRuntimeError(
                "Sender object was not identified by its role")
        return self._sender_role

    @property
    def receiver_role(self):
        if self._receiver_role is None:
            raise NineMLRuntimeError(
                "Sender object was not identified by its role")
        return self._receiver_role

    @property
    def sender_name(self):
        if self._sender_name is None:
            raise NineMLRuntimeError(
                "Sender object was not identified by its name")
        return self._sender_name

    @property
    def receiver_name(self):
        if self._receiver_name is None:
            raise NineMLRuntimeError(
                "Sender object was not identified by its name")
        return self._receiver_name

    def assign_roles(self, name_map={}, role_map={}, port_namespaces={}):
        """
        Assigns a name to a role, or specifies a new role for any role in the
        role map. Roles not in the map are left as they are.
        """
        # Check role doesn't appear in both name_map and role_map
        assert not (set(name_map.iterkeys()) & set(role_map.iterkeys()))
        kwargs = {}
        try:
            kwargs['sender_name'] = name_map[self.sender_role]
        except KeyError:
            kwargs['sender_role'] = role_map.get(self.sender_role,
                                                 self.sender_role)
        try:
            kwargs['receiver_name'] = name_map[self.receiver_role]
        except KeyError:
            kwargs['receiver_role'] = role_map.get(self.receiver_role,
                                                   self.receiver_role)
        try:
            send_port = nineml.user.append_namespace(
                self.send_port_name, port_namespaces[self.sender_role])
        except KeyError:
            send_port = self.send_port_name
        try:
            receive_port = nineml.user.append_namespace(
                self.receive_port_name, port_namespaces[self.receiver_role])
        except KeyError:
            receive_port = self.receive_port_name
        # Return a new port connection with the roles mapped to names or new
        # roles
        return self.__class__(send_port=send_port, receive_port=receive_port,
                              **kwargs)

    def expose_ports(self, role_map):
        exposures = []
        try:
            exposures.append(nineml.user.multi.BasePortExposure.from_port(
                self.send_port, role_map[self.sender_role]))
        except KeyError:
            pass
        try:
            exposures.append(nineml.user.multi.BasePortExposure.from_port(
                self.receive_port, role_map[self.receiver_role]))
        except KeyError:
            pass
        return exposures

    def bind(self, container, to_roles=False):
        """
        Binds the PortConnection to the components it is connecting
        """
        # If the sender and receiver should be identified by their role
        # i.e. pre, pos, response, plasticity, etc... or by name
        if to_roles:
            self._sender = getattr(container, self.sender_role)
            self._receiver = getattr(container, self.receiver_role)
        else:
            self._sender = container[self.sender_name]
            self._receiver = container[self.receiver_name]
        try:
            self._send_port = self._sender.send_port(self.send_port_name)
        except NineMLNameError:
            raise NineMLNameError(
                "Could not bind to missing send port, '{}', in '{}'"
                .format(self.send_port_name, self.sender.name))
        try:
            self._receive_port = self._receiver.receive_port(
                self.receive_port_name)
        except NineMLNameError:
            raise NineMLNameError(
                "Could not bind {} to missing receive port, '{}', in '{}'"
                .format(self, self.receive_port_name, self.receiver.name))
        self._check_ports()

    def is_bound(self):
        if self._sender is None:
#             assert self._receiver is None
#             assert self._send_port is None
#             assert self._receive_port is None
            bound = False
        else:
#             assert self._receiver is not None
#             assert self._send_port is not None
#             assert self._receive_port is not None
            bound = True
        return bound

    @annotate_xml
    def to_xml(self, document, E=E, **kwargs):  # @UnusedVariable
        attribs = {}
        try:
            attribs['sender_role'] = self.sender_role
        except NineMLRuntimeError:
            attribs['sender_name'] = self.sender_name
        try:
            attribs['receiver_role'] = self.receiver_role
        except NineMLRuntimeError:
            attribs['receiver_name'] = self.receiver_name
        return E(
            self.nineml_type,
            send_port=self.send_port_name, receive_port=self.receive_port_name,
            **attribs)

    @classmethod
    @read_annotations
    @unprocessed_xml
    def from_xml(cls, element, document, **kwargs):  # @UnusedVariable
        return cls(send_port=get_xml_attr(element, 'send_port',
                                          document, **kwargs),
                   receive_port=get_xml_attr(element, 'receive_port', document,
                                             **kwargs),
                   sender_role=get_xml_attr(element, 'sender_role', document,
                                            default=None, **kwargs),
                   receiver_role=get_xml_attr(element, 'receiver_role',
                                              document, default=None,
                                              **kwargs),
                   sender_name=get_xml_attr(element, 'sender_name', document,
                                            default=None, **kwargs),
                   receiver_name=get_xml_attr(element, 'receiver_name',
                                              document, default=None,
                                              **kwargs))

    @abstractmethod
    def _check_ports(self):
        pass

    @classmethod
    def from_tuple(cls, tple, container):
        # FIXME: Needs comments to explain what is going on and better
        #        exception messages
        sender, send_port, receiver, receive_port = tple
        init_kwargs = {}
        try:
            sender_dynamicss = getattr(container, sender).component_classes
            init_kwargs['sender_role'] = sender
        except AttributeError:
            try:
                sender_dynamicss = [container[sender].component_class]
                init_kwargs['sender_name'] = sender
            except (TypeError, KeyError), e:
                raise NineMLRuntimeError(
                    "Did not find sender {} '{}' in '{}' container"
                    .format('name' if isinstance(e, KeyError) else 'role',
                            receiver, container.name))
        try:
            getattr(container, receiver).component_classes
            init_kwargs['receiver_role'] = receiver
        except AttributeError:
            try:
                container[receiver].component_class
                init_kwargs['receiver_name'] = receiver
            except (TypeError, KeyError), e:
                raise NineMLRuntimeError(
                    "Did not find receiver {} '{}' in '{}' container"
                    .format('name' if isinstance(e, KeyError) else 'role',
                            receiver, container.name))
        port_type = None
        for dyn in sender_dynamicss:
            pt = dyn.port(send_port).nineml_type
            if port_type is None:
                port_type = pt
            elif port_type != pt:
                raise NineMLRuntimeError(
                    "Mismatching port types for '{}' port in populations in "
                    "Selection '{}'".format(send_port, container.name))
        if port_type in ('AnalogSendPort', 'AnalogSendPortExposure'):
            port_connection = AnalogPortConnection(
                receive_port=receive_port, send_port=send_port, **init_kwargs)
        elif port_type in ('EventSendPort', 'EventSendPortExposure'):
            port_connection = EventPortConnection(
                receive_port=receive_port, send_port=send_port, **init_kwargs)
        else:
            assert False, "'{}' should be a send port not '{}'".format(
                send_port, port_type)
        return port_connection


class AnalogPortConnection(BasePortConnection):

    nineml_type = 'AnalogPortConnection'
    communicates = 'analog'

    def _check_ports(self):
        if not isinstance(self.send_port, AnalogSendPort):
            raise NineMLRuntimeError(
                "Send port '{}' must be an AnalogSendPort to be connected with"
                " an AnalogPortConnection".format(self.send_port.name))
        if not isinstance(self.receive_port, (AnalogReceivePort,
                                              AnalogReducePort)):
            raise NineMLRuntimeError(
                "Send port '{}' must be an AnalogSendPort to be connected with"
                " an AnalogPortConnection".format(self.receive_port.name))
        if self.send_port.dimension != self.receive_port.dimension:
            raise NineMLDimensionError(
                "Dimensions do not match in analog port connection: sender "
                "port" " '{}' has dimensions of '{}' and receive port '{}' has"
                " dimensions of '{}'"
                .format(self.send_port.name, self.send_port.dimension,
                        self.receive_port.name, self.receive_port.dimension))


class EventPortConnection(BasePortConnection):

    nineml_type = 'EventPortConnection'
    communicates = 'event'

    def _check_ports(self):
        if not isinstance(self.send_port, EventSendPort):
            raise NineMLRuntimeError(
                "Send port '{}' must be an EventSendPort to be connected with"
                " an EventPortConnection".format(self.send_port.name))
        if not isinstance(self.receive_port, EventReceivePort):
            raise NineMLRuntimeError(
                "Send port '{}' must be an EventSendPort to be connected with"
                " an EventPortConnection".format(self.receive_port.name))

    @property
    def delay(self):
        """
        Included for compatibility with code written in
        nineml.user.multi.component for future versions
        """
        return 0.0

import nineml.user
