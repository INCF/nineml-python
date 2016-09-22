import unittest
from nineml.user.port_connections import (EventPortConnection, BasePortConnection, AnalogPortConnection)
from nineml.utils.testing.comprehensive import instances_of_all_types
from nineml.exceptions import (NineMLDimensionError, NineMLRuntimeError)


class TestEventPortConnectionExceptions(unittest.TestCase):

    def test__check_ports_ninemlruntimeerror(self):
        """
        line #: 378
        message: Send port '{}' must be an EventSendPort to be connected with an EventPortConnection

        context:
        --------
    def _check_ports(self):
        if not isinstance(self.send_port, EventSendPort):
        """

        eventportconnection = instances_of_all_types['EventPortConnection']
        self.assertRaises(
            NineMLRuntimeError,
            eventportconnection._check_ports)

    def test__check_ports_ninemlruntimeerror2(self):
        """
        line #: 382
        message: Send port '{}' must be an EventSendPort to be connected with an EventPortConnection

        context:
        --------
    def _check_ports(self):
        if not isinstance(self.send_port, EventSendPort):
            raise NineMLRuntimeError(
                "Send port '{}' must be an EventSendPort to be connected with"
                " an EventPortConnection".format(self.send_port.name))
        if not isinstance(self.receive_port, EventReceivePort):
        """

        eventportconnection = instances_of_all_types['EventPortConnection']
        self.assertRaises(
            NineMLRuntimeError,
            eventportconnection._check_ports)


class TestBasePortConnectionExceptions(unittest.TestCase):

    def test___init___ninemlruntimeerror(self):
        """
        line #: 52
        message: Both 'sender_role' ({}) and 'sender_name' ({}) cannot be provided to PortConnection __init__

        context:
        --------
    def __init__(self, send_port, receive_port,
                 sender_role=None, receiver_role=None,
                 sender_name=None, receiver_name=None):
        \"\"\"
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
        \"\"\"
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
        """

        baseportconnection = instances_of_all_types['BasePortConnection']
        self.assertRaises(
            NineMLRuntimeError,
            baseportconnection.__init__,
            send_port=None,
            receive_port=None,
            sender_role=None,
            receiver_role=None,
            sender_name=None,
            receiver_name=None)

    def test___init___ninemlruntimeerror2(self):
        """
        line #: 62
        message: Both 'receiver_role' ({}) and 'receiver_name' ({}) cannot be provided to PortConnection __init__

        context:
        --------
    def __init__(self, send_port, receive_port,
                 sender_role=None, receiver_role=None,
                 sender_name=None, receiver_name=None):
        \"\"\"
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
        \"\"\"
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
        """

        baseportconnection = instances_of_all_types['BasePortConnection']
        self.assertRaises(
            NineMLRuntimeError,
            baseportconnection.__init__,
            send_port=None,
            receive_port=None,
            sender_role=None,
            receiver_role=None,
            sender_name=None,
            receiver_name=None)

    def test_sender_ninemlruntimeerror(self):
        """
        line #: 107
        message: Ports have not been bound

        context:
        --------
    def sender(self):
        if not self.is_bound():
        """

        baseportconnection = instances_of_all_types['BasePortConnection']
        with self.assertRaises(NineMLRuntimeError):
            print baseportconnection.sender

    def test_receiver_ninemlruntimeerror(self):
        """
        line #: 113
        message: Ports have not been bound

        context:
        --------
    def receiver(self):
        if not self.is_bound():
        """

        baseportconnection = instances_of_all_types['BasePortConnection']
        with self.assertRaises(NineMLRuntimeError):
            print baseportconnection.receiver

    def test_send_port_ninemlruntimeerror(self):
        """
        line #: 119
        message: Ports have not been bound

        context:
        --------
    def send_port(self):
        if not self.is_bound():
        """

        baseportconnection = instances_of_all_types['BasePortConnection']
        with self.assertRaises(NineMLRuntimeError):
            print baseportconnection.send_port

    def test_receive_port_ninemlruntimeerror(self):
        """
        line #: 125
        message: Ports have not been bound

        context:
        --------
    def receive_port(self):
        if not self.is_bound():
        """

        baseportconnection = instances_of_all_types['BasePortConnection']
        with self.assertRaises(NineMLRuntimeError):
            print baseportconnection.receive_port

    def test_sender_role_ninemlruntimeerror(self):
        """
        line #: 145
        message: Sender object was not identified by its role

        context:
        --------
    def sender_role(self):
        if self._sender_role is None:
        """

        baseportconnection = instances_of_all_types['BasePortConnection']
        with self.assertRaises(NineMLRuntimeError):
            print baseportconnection.sender_role

    def test_receiver_role_ninemlruntimeerror(self):
        """
        line #: 152
        message: Sender object was not identified by its role

        context:
        --------
    def receiver_role(self):
        if self._receiver_role is None:
        """

        baseportconnection = instances_of_all_types['BasePortConnection']
        with self.assertRaises(NineMLRuntimeError):
            print baseportconnection.receiver_role

    def test_sender_name_ninemlruntimeerror(self):
        """
        line #: 159
        message: Sender object was not identified by its name

        context:
        --------
    def sender_name(self):
        if self._sender_name is None:
        """

        baseportconnection = instances_of_all_types['BasePortConnection']
        with self.assertRaises(NineMLRuntimeError):
            print baseportconnection.sender_name

    def test_receiver_name_ninemlruntimeerror(self):
        """
        line #: 166
        message: Sender object was not identified by its name

        context:
        --------
    def receiver_name(self):
        if self._receiver_name is None:
        """

        baseportconnection = instances_of_all_types['BasePortConnection']
        with self.assertRaises(NineMLRuntimeError):
            print baseportconnection.receiver_name


class TestAnalogPortConnectionExceptions(unittest.TestCase):

    def test__check_ports_ninemlruntimeerror(self):
        """
        line #: 354
        message: Send port '{}' must be an AnalogSendPort to be connected with an AnalogPortConnection

        context:
        --------
    def _check_ports(self):
        if not isinstance(self.send_port, AnalogSendPort):
        """

        analogportconnection = instances_of_all_types['AnalogPortConnection']
        self.assertRaises(
            NineMLRuntimeError,
            analogportconnection._check_ports)

    def test__check_ports_ninemlruntimeerror2(self):
        """
        line #: 359
        message: Send port '{}' must be an AnalogSendPort to be connected with an AnalogPortConnection

        context:
        --------
    def _check_ports(self):
        if not isinstance(self.send_port, AnalogSendPort):
            raise NineMLRuntimeError(
                "Send port '{}' must be an AnalogSendPort to be connected with"
                " an AnalogPortConnection".format(self.send_port.name))
        if not isinstance(self.receive_port, (AnalogReceivePort,
                                              AnalogReducePort)):
        """

        analogportconnection = instances_of_all_types['AnalogPortConnection']
        self.assertRaises(
            NineMLRuntimeError,
            analogportconnection._check_ports)

    def test__check_ports_ninemldimensionerror(self):
        """
        line #: 363
        message: Dimensions do not match in analog port connection: sender port '{}' has dimensions of '{}' and receive port '{}' has dimensions of '{}'

        context:
        --------
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
        """

        analogportconnection = instances_of_all_types['AnalogPortConnection']
        self.assertRaises(
            NineMLDimensionError,
            analogportconnection._check_ports)

