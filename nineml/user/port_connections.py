from . import BaseULObject
from itertools import chain
from nineml.xmlns import E
from nineml.annotations import read_annotations, annotate_xml
from nineml.exceptions import NineMLRuntimeError


class BasePortConnection(BaseULObject):

    _member_types = ('sender', 'receiver', 'send_port', 'receive_port')
    defining_attributes = list(
        chain(('_' + m, '_' + m + '_name') for m in _member_types))

    def __init__(self, sender, receiver, send_port, receive_port):
        super(BasePortConnection, self).__init__()
        self._set_member('sender', sender)
        self._set_member('receiver', receiver)
        self._set_member('send_port', send_port)
        self._set_member('receive_port', receive_port)

    def __repr__(self):
        return ("{}('{}' with {} senders)"
                .format(self.element_name, self.port_name, len(self.senders)))

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
    def sender_name(self):
        if self._sender is None:
            return self._sender_name
        else:
            return self._sender.name

    @property
    def receiver_name(self):
        if self._receiver is None:
            return self._receiver_name
        else:
            return self._receiver.name

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

    def bind_ports(self, container):
        """
        Binds the PortConnection to the components it is connecting
        """
        for member_type in self._member_types:
            member_name = getattr(self, '_' + member_type + '_name')
            if member_name is not None:
                setattr(self, '_' + member_type, container.port(member_name))
                setattr(self, '_' + member_type + '_name', None)
            else:
                member = getattr(self, '_' + member_type)
                assert container.port(member.name) is member

    @annotate_xml
    def to_xml(self):
        return E(
            self.element_name,
            sender=self.sender_name, receiver=self.receiver_name,
            send_port=self.send_port_name, receive_port=self.receive_port_name)

    @classmethod
    @read_annotations
    def from_xml(cls, element, document, **kwargs):  # @UnusedVariable
        cls.check_tag(element)
        return cls(element.attrib['sender'], element.attrib['receiver'],
                   element.attrib['send_port'], element.attrib['receive_port'])

    def _set_member(self, member_type, obj):
        if isinstance(obj, basestring):
            setattr(self, '_' + member_type, None)
            setattr(self, '_' + member_type + '_name', obj)
        else:
            setattr(self, '_' + member_type, obj)
            setattr(self, '_' + member_type + '_name', None)


class AnalogPortConnection(BasePortConnection):

    element_name = 'AnalogPortConnection'


class EventPortConnection(BasePortConnection):

    element_name = 'EventPortConnection'
