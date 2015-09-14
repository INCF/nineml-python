from . import BaseULObject
from itertools import chain
from nineml.xmlns import E
from nineml.annotations import read_annotations, annotate_xml
from nineml.exceptions import NineMLRuntimeError


class BasePortConnection(BaseULObject):

    defining_attributes = ('sender_id', 'receiver_id', 'sender', 'receiver'
                           'send_port', 'receive_port', 'send_port_name',
                           'receive_port_name')

    def __init__(self, sender_relationship, receiver_relationship,
                 send_port_name, receive_port_name):
        super(BasePortConnection, self).__init__()
        self._sender_rel = sender_relationship
        self._receiver_rel = receiver_relationship
        self._send_port_name = send_port_name
        self._receive_port_name = receive_port_name
        self._sender = None
        self._receiver = None
        self._send_port = None
        self._receive_port = None

    def __repr__(self):
        return ("{}(sender={}->{}, receiver={}->{})"
                .format(self.element_name, self.sender_rel,
                        self.send_port_name, self.receiver_rel,
                        self.receive_port_name))

    @property
    def sender(self):
        if self._sender is None:
            raise NineMLRuntimeError("Ports have not been bound")
        return self._sender

    @property
    def receiver(self):
        if self._receiver is None:
            raise NineMLRuntimeError("Ports have not been bound")
        return self._receiver

    @property
    def send_port(self):
        if self._send_port is None:
            raise NineMLRuntimeError("Ports have not been bound")
        return self._send_port

    @property
    def receive_port(self):
        if self._receive_port is None:
            raise NineMLRuntimeError("Ports have not been bound")
        return self.receive_port

    @property
    def sender_relationship(self):
        return self._sender_rel

    @property
    def receiver_relationship(self):
        return self._receiver_rel

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

    def bind_ports(self, sender, receiver):
        """
        Binds the PortConnection to the components it is connecting
        """
        self._sender = sender
        self._receiver = receiver
        self._send_port = sender.port(self._send_port_name)
        self._receive_port = receiver.port(self._receive_port_name)

    @annotate_xml
    def to_xml(self):
        return E(
            self.element_name,
            sender=self.sender_relationship,
            receiver=self.receiver_relationship,
            send_port=self.send_port_name, receive_port=self.receive_port_name)

    @classmethod
    @read_annotations
    def from_xml(cls, element, document, **kwargs):  # @UnusedVariable
        cls.check_tag(element)
        return cls(element.attrib['sender'], element.attrib['receiver'],
                   element.attrib['send_port'], element.attrib['receive_port'])


class AnalogPortConnection(BasePortConnection):

    element_name = 'AnalogPortConnection'


class EventPortConnection(BasePortConnection):

    element_name = 'EventPortConnection'
