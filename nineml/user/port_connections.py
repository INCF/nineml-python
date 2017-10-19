from past.builtins import basestring
from . import BaseULObject
from abc import ABCMeta, abstractmethod
import nineml.units as un
from nineml.exceptions import (
    NineMLUsageError, NineMLNameError, NineMLDimensionError,
    NineMLNotBoundException)
from nineml.abstraction.ports import (
    AnalogSendPort, AnalogReceivePort, AnalogReducePort, EventSendPort,
    EventReceivePort)
import nineml.user.multi
from future.utils import with_metaclass
from nineml.utils import validate_identifier


class BasePortConnection(with_metaclass(ABCMeta, BaseULObject)):

    nineml_attr = ('send_port_name', 'receive_port_name',
                    'sender_role', 'receiver_role',
                    'sender_name', 'receiver_name')

    _projection_roles = ('pre', 'post', 'response', 'plasticity')

    def __init__(self, send_port_name, receive_port_name,
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
        assert isinstance(send_port_name, basestring)
        assert isinstance(receive_port_name, basestring)
        self._send_port_name = validate_identifier(send_port_name)
        self._send_port = None
        self._receive_port_name = validate_identifier(receive_port_name)
        self._receive_port = None
        if sender_role is not None:
            if sender_name is not None:
                raise NineMLUsageError(
                    "Both 'sender_role' ({}) and 'sender_name' ({}) cannot"
                    " be provided to PortConnection __init__"
                    .format(sender_role, sender_name))
            assert isinstance(sender_role, basestring)
            sender_role = str(sender_role)
        elif sender_name is not None:
            sender_name = validate_identifier(sender_name)
        else:
            raise NineMLUsageError(
                "Either 'sender_role' or 'sender_name' must be "
                "provided to PortConnection __init__")
        if receiver_role is not None:
            if receiver_name is not None:
                raise NineMLUsageError(
                    "Both 'receiver_role' ({}) and 'receiver_name' ({}) cannot"
                    " be provided to PortConnection __init__"
                    .format(receiver_role, receiver_name))
            assert isinstance(receiver_role, basestring)
            receiver_role = str(receiver_role)
        elif receiver_name is not None:
            receiver_name = validate_identifier(receiver_name)
        else:
            raise NineMLUsageError(
                "Either 'receiver_role' or 'receiver_name' must be "
                "provided to PortConnection __init__")
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
        return '__'.join((
            (self.sender_role if self._sender_role is not None
             else self.sender_name), self.send_port_name,
            (self.receiver_role if self._receiver_role is not None
             else self.receiver_name), self.receive_port_name))

    @property
    def sender(self):
        if not self.is_bound():
            raise NineMLUsageError("Ports have not been bound")
        return self._sender

    @property
    def receiver(self):
        if not self.is_bound():
            raise NineMLUsageError("Ports have not been bound")
        return self._receiver

    @property
    def send_port(self):
        if not self.is_bound():
            raise NineMLUsageError("Ports have not been bound")
        return self._send_port

    @property
    def receive_port(self):
        if not self.is_bound():
            raise NineMLUsageError("Ports have not been bound")
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
            raise NineMLNotBoundException(
                "Sender object was not identified by its role")
        return self._sender_role

    @property
    def receiver_role(self):
        if self._receiver_role is None:
            raise NineMLNotBoundException(
                "Sender object was not identified by its role")
        return self._receiver_role

    @property
    def sender_name(self):
        if self._sender_name is None:
            raise NineMLNotBoundException(
                "Sender object was not identified by its name")
        return self._sender_name

    @property
    def receiver_name(self):
        if self._receiver_name is None:
            raise NineMLNotBoundException(
                "Sender object was not identified by its name")
        return self._receiver_name

    @property
    def send_key(self):
        return self.sender_name, self.send_port_name

    @property
    def receive_key(self):
        return self.receiver_name, self.receive_port_name

    def assign_names_from_roles(self, role_map):
        """
        Returns a new port connection with the sender/receiver roles mapped to
        the name of a sub-component, which can be used in the aggregation of
        synapses and post-synaptic cells into single MultiDynamics objects

        Parameters
        ----------
        role_map : dict(str,str)
            A dictionary containing maps from the port-connection role to sub-
            component name

        Returns
        -------
        port_connection : PortConnection
            Returns a port connection of the same type with the roles of the
            sender/receiver mapped to sub-component names in the role_map arg
        """
        # Return a new port connection with the roles mapped to names or new
        # roles
        return self.__class__(send_port_name=self.send_port_name,
                              receive_port_name=self.receive_port_name,
                              sender_name=role_map[self.sender_role],
                              receiver_name=role_map[self.receiver_role])

    def append_namespace_from_roles(self, role_map):
        """
        Appends role names to port_connection ports for use in the creation of
        MultiDynamics objects

        Parameters
        ----------
        role_map : dict(str,str)
            A dictionary containing maps from the port-connection role to sub-
            component name

        Returns
        -------
        port_connection : PortConnection
            Returns a port connection of the same type with the port names
            appended with the namespace of the sub-component the
            sender/receiver maps to
        """
        send_port_name = nineml.user.append_namespace(
            self.send_port_name, role_map[self.sender_role])
        receive_port_name = nineml.user.append_namespace(
            self.receive_port_name, role_map[self.receiver_role])
        # An additional suffix is appended to the names given to reduce ports
        # to allow internal connections to the alias
        if isinstance(self.receive_port, AnalogReducePort):
            receive_port_name += (
                nineml.user.multi.AnalogReducePortExposure.SUFFIX)
        # Return a new port connection with the role namespace appended to the
        # port names.
        return self.__class__(send_port_name=send_port_name,
                              receive_port_name=receive_port_name,
                              sender_role=self.sender_role,
                              receiver_role=self.receiver_role)

    def expose_ports(self, role_map):
        """
        Create port exposures for the send and/or receive ports in the role
        map. Used when aggregating synapse and post-synaptic cell dynamics into
        MultiDynamics object to expose the ports required for the port
        connection

        Parameters
        ----------
        role_map : dict(str,str)
            A dictionary containing maps from the port-connection role to sub-
            component name

        Returns
        -------
        exposures : list(PortExposure)
            Returns a list of port exposures of length 0-2 containing the port
            exposures required to connect the port connection to sub-
            component names in the role map.
        """
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
            bound = False
        else:
            bound = True
        return bound

    def serialize_node(self, node, **options):  # @UnusedVariable
        try:
            node.attr('sender_role', self.sender_role)
        except NineMLNotBoundException:
            node.attr('sender_name', self.sender_name)
        try:
            node.attr('receiver_role', self.receiver_role)
        except NineMLNotBoundException:
            node.attr('receiver_name', self.receiver_name)
        node.attr('send_port', self.send_port_name, **options)
        node.attr('receive_port', self.receive_port_name, **options)

    @classmethod
    def unserialize_node(cls, node, **options):  # @UnusedVariable
        return cls(send_port_name=node.attr('send_port', **options),
                   receive_port_name=node.attr('receive_port', **options),
                   sender_role=node.attr('sender_role', default=None,
                                         **options),
                   receiver_role=node.attr('receiver_role', default=None,
                                           **options),
                   sender_name=node.attr('sender_name', default=None,
                                         **options),
                   receiver_name=node.attr('receiver_name', default=None,
                                           **options))

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
            except (TypeError, KeyError) as e:
                raise NineMLUsageError(
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
            except (TypeError, KeyError) as e:
                raise NineMLUsageError(
                    "Did not find receiver {} '{}' in '{}' container"
                    .format('name' if isinstance(e, KeyError) else 'role',
                            receiver, container.name))
        port_type = None
        for dyn in sender_dynamicss:
            pt = dyn.port(send_port).nineml_type
            if port_type is None:
                port_type = pt
            elif port_type != pt:
                raise NineMLUsageError(
                    "Mismatching port types for '{}' port in populations in "
                    "Selection '{}'".format(send_port, container.name))
        if port_type in ('AnalogSendPort', 'AnalogSendPortExposure'):
            port_connection = AnalogPortConnection(
                receive_port_name=receive_port,
                send_port_name=send_port, **init_kwargs)
        elif port_type in ('EventSendPort', 'EventSendPortExposure'):
            port_connection = EventPortConnection(
                receive_port_name=receive_port, send_port_name=send_port,
                **init_kwargs)
        else:
            assert False, "'{}' should be a send port not '{}'".format(
                send_port, port_type)
        return port_connection


class AnalogPortConnection(BasePortConnection):

    nineml_type = 'AnalogPortConnection'
    communicates = 'analog'

    def _check_ports(self):
        if not isinstance(self.send_port, AnalogSendPort):
            raise NineMLUsageError(
                "Send port '{}' must be an AnalogSendPort to be connected with"
                " an AnalogPortConnection".format(self.send_port.name))
        if not isinstance(self.receive_port, (AnalogReceivePort,
                                              AnalogReducePort)):
            raise NineMLUsageError(
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
            raise NineMLUsageError(
                "Send port '{}' must be an EventSendPort to be connected with"
                " an EventPortConnection".format(self.send_port.name))
        if not isinstance(self.receive_port, EventReceivePort):
            raise NineMLUsageError(
                "Send port '{}' must be an EventSendPort to be connected with"
                " an EventPortConnection".format(self.receive_port.name))

    @property
    def delay(self):
        """
        Included for compatibility with code written in
        nineml.user.multi.dynamics for future versions
        """
        return 0.0 * un.s


import nineml.user.multi  # @IgnorePep8
