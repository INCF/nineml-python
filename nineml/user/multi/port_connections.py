import operator
import sympy
from nineml.base import BaseNineMLObject
import nineml.units as un
from nineml.abstraction import (
    StateVariable, StateAssignment, Trigger)
from .namespace import (
    _NamespaceOnCondition, make_delay_trigger_name)
from nineml.abstraction import (
    Alias, Constant)
from nineml.exceptions import NineMLImmutableError
from .namespace import append_namespace
from functools import reduce


class _DelayedOnEvent(_NamespaceOnCondition):
    """
    OnEvents that are triggered by delayed local connections are represented
    by OnConditions, which are triggered by a "delay trigger" state variable
    being passed by the simulation time 't'
    """

    temporary = True

    def __init__(self, on_event, port_connection):
        BaseNineMLObject.__init__(self)
        self._sub_component = on_event,
        self._port_connection = port_connection

    @property
    def trigger(self):
        state_var = make_delay_trigger_name(self._port_connection)
        return Trigger('t > {}'.format(state_var))


class _UnconnectedAnalogReducePort(Constant):
    """
    AnalogReducePorts that aren't connected are replaced by constants with
    zero value
    """

    temporary = True

    def __init__(self, port, sub_component):
        BaseNineMLObject.__init__(self)
        self._port = port
        self._parent = sub_component

    @property
    def name(self):
        return append_namespace(self._port.name, self._parent.name)

    @property
    def value(self):
        return 0.0

    @property
    def units(self):
        return self._port.dimension.origin.units


class _DelayedOnEventStateVariable(StateVariable):

    temporary = True

    def __init__(self, port_connection):
        BaseNineMLObject.__init__(self)
        self._parent = port_connection

    @property
    def name(self):
        return make_delay_trigger_name(self._parent)

    @property
    def dimension(self):
        return un.time


class _DelayedOnEventStateAssignment(StateAssignment):

    temporary = True

    def __init__(self, port_connection):
        BaseNineMLObject.__init__(self)
        self._parent = port_connection

    @property
    def variable(self):
        return make_delay_trigger_name(self._parent)

    @property
    def rhs(self):
        return sympy.sympify('t + {}'.format(self._parent.delay))


class _LocalAnalogPortConnections(Alias):

    temporary = True

    def __init__(self, receive_port, receiver, port_connections, parent):
        BaseNineMLObject.__init__(self)
        self._receive_port_name = receive_port
        self._receiver_name = receiver
        self._port_connections = port_connections
        self._parent = parent

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
