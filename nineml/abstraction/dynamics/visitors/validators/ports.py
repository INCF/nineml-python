"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from itertools import chain
from nineml.exceptions import NineMLRuntimeError
from . import BaseDynamicsValidator
from ....componentclass.visitors.validators.ports import (
    PortConnectionsComponentValidator)
from ..base import DynamicsActionVisitor


class EventPortsDynamicsValidator(BaseDynamicsValidator):

    """
    Check that each OutputEvent and OnEvent has a corresponding EventPort
    defined, and that the EventPort has the right direction.
    """

    def __init__(self, component_class):
        super(EventPortsDynamicsValidator, self).__init__(
            require_explicit_overrides=False)

        # Mapping component_class to list of events/eventports at that
        # component_class
        self.event_send_ports = {}
        self.event_receive_ports = {}
        self.output_events = []
        self.input_events = []

        self.visit(component_class)

        # Check that each output event has a corresponding event_port with a
        # send mode:
        for output_event in self.output_events:
            if output_event not in self.event_send_ports:
                raise NineMLRuntimeError(
                    "Can't find port definition matching OutputEvent: {}"
                    .format(output_event))

        # Check that each input event has a corresponding event_port with a
        # recv/reduce mode:
        for input_event in self.input_events:
            if input_event not in self.event_receive_ports:
                raise NineMLRuntimeError(
                    "Can't find port definition matching input event: {}"
                    .format(input_event))

        # Check that each Event port emits/recieves at least one
        for event_ports in (self.event_send_ports, self.event_receive_ports):
            for evt_port_name in event_ports.keys():
                op_evts_on_port = [ev for ev in self.output_events
                                   if ev == evt_port_name]
                ip_evts_on_port = [ev for ev in self.input_events
                                   if ev == evt_port_name]

                if len(op_evts_on_port) + len(ip_evts_on_port) == 0:
                    raise NineMLRuntimeError(
                        "Unable to find events generated for '{}'"
                        .format(evt_port_name))

    def action_eventsendport(self, port, **kwargs):  # @UnusedVariable @IgnorePep8
        assert port.name not in self.event_send_ports
        self.event_send_ports[port.name] = port

    def action_eventreceiveport(self, port, **kwargs):  # @UnusedVariable @IgnorePep8
        assert port.name not in self.event_receive_ports
        self.event_receive_ports[port.name] = port

    def action_outputevent(self, event_out, **kwargs):  # @UnusedVariable @IgnorePep8
        self.output_events.append(event_out.port_name)

    def action_onevent(self, on_event, **kwargs):  # @UnusedVariable
        self.input_events.append(on_event.src_port_name)


# Check that the sub-components stored are all of the
# right types:
class OutputAnalogPortsDynamicsValidator(BaseDynamicsValidator):

    """
    Check that all output AnalogPorts reference a local symbol, either an alias
    or a state variable
    """

    def __init__(self, component_class):
        super(OutputAnalogPortsDynamicsValidator, self).__init__(
            require_explicit_overrides=False)
        self.output_analogports = []
        self.available_symbols = []
        self.component_class = component_class
        self.visit(component_class)
        for ap in self.output_analogports:
            if ap not in self.available_symbols:
                raise NineMLRuntimeError(
                    "Unable to find an Alias or State variable for "
                    "analog-port '{}' (available '{}')"
                    .format(ap, "', '".join(self.available_symbols)))

    def add_symbol(self, symbol):
        assert symbol not in self.available_symbols
        self.available_symbols.append(symbol)

    def action_analogsendport(self, port, **kwargs):  # @UnusedVariable @IgnorePep8
        self.output_analogports.append(port.name)

    def action_statevariable(self, state_variable, **kwargs):  # @UnusedVariable @IgnorePep8
        self.add_symbol(symbol=state_variable.name)

    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        if alias not in chain(*(r.aliases
                                for r in self.component_class.regimes)):
            self.add_symbol(symbol=alias.lhs)


class PortConnectionsDynamicsValidator(
        DynamicsActionVisitor,
        PortConnectionsComponentValidator):

    """Check that all the port connections point to a port, and that
    each send & recv port only has a single connection.
    """

    def action_analogsendport(self, analogsendport):
        self._action_port(analogsendport)

    def action_analogreceiveport(self, analogreceiveport):
        self._action_port(analogreceiveport)

    def action_analogreduceport(self, analogreduceport):
        self._action_port(analogreduceport)

    def action_eventsendport(self, eventsendport):
        self._action_port(eventsendport)

    def action_eventreceiveport(self, eventreceiveport):
        self._action_port(eventreceiveport)
