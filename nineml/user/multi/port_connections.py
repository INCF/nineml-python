import sympy
from nineml.base import BaseNineMLObject
import nineml.units as un
from nineml.abstraction import (
    StateVariable, StateAssignment, Trigger)
from .namespace import (
    _NamespaceOnCondition, make_delay_trigger_name)
from nineml.abstraction import (
    Alias, Constant)
from nineml.exceptions import NineMLImmutableError, NineMLUsageError
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


class _LocalAnalogReceivePortConnection(Alias):

    temporary = True

    def __init__(self, receive_port, receiver, port_connection, parent):
        BaseNineMLObject.__init__(self)
        self._port = receive_port
        self._receiver = receiver
        self._port_conn = port_connection
        self._parent = parent

    @property
    def port_name(self):
        return self._port.name

    @property
    def receiver_name(self):
        return self._receiver.name

    @property
    def port_connection(self):
        return self._port_conn

    @property
    def name(self):
        return self.lhs

    @property
    def key(self):
        # Required for duck-typing
        return self.name

    @property
    def lhs(self):
        return append_namespace(self.port_name, self.receiver_name)

    @property
    def rhs(self):
        return sympy.Symbol(self._port_conn.sender.append_namespace(
            self._port_conn.send_port_name))

    def lhs_name_transform_inplace(self, name_map):
        raise NineMLImmutableError(
            "Cannot rename LHS of Alias '{}' because it is a local "
            "AnalogPortConnection".format(self.lhs))


class _LocalAnalogReducePortConnections(_LocalAnalogReceivePortConnection):

    temporary = True

    def __init__(self, reduce_port, receiver, port_connections, parent,
                 exposure=None):
        BaseNineMLObject.__init__(self)
        self._port = reduce_port
        self._receiver = receiver
        self._port_connections = port_connections
        self._parent = parent
        self._exposure = exposure
        if exposure is not None and exposure.name == exposure.local_port_name:
            raise NineMLUsageError(
                "Must provide a unique name for analog reduce port exposure "
                "'{}' as it is locally connected by {}".format(
                    exposure.name, ', '.join(str(pc)
                                             for pc in port_connections)))

    @property
    def port_connections(self):
        return iter(self._port_connections)

    @property
    def rhs(self):
        operands = [sympy.Symbol(pc.sender.append_namespace(pc.send_port_name))
                    for pc in self.port_connections]
        if self._exposure is not None:
            operands.append(sympy.Symbol(self._exposure.name))
        return reduce(self._port.python_op, operands)
