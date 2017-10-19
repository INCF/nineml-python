"""
docstring needed

:copyright: Copyright 2010-2017 by the NineML Python team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from itertools import chain
from nineml.exceptions import NineMLUsageError
from ..base import BaseDynamicsVisitor


class EventPortsDynamicsValidator(BaseDynamicsVisitor):

    """
    Check that each OutputEvent and OnEvent has a corresponding EventPort
    defined, and that the EventPort has the right direction.
    """

    def __init__(self, component_class, **kwargs):  # @UnusedVariable
        super(EventPortsDynamicsValidator, self).__init__()

        # Mapping component_class to list of events/eventports at that
        # component_class
        self.event_send_ports = {}
        self.event_receive_ports = {}
        self.output_events = []
        self.input_events = []

        # Visit all elements of the component class
        self.visit(component_class)

        # Check that each output event has a corresponding event_port with a
        # send mode:
        for output_event in self.output_events:
            if output_event not in self.event_send_ports:
                raise NineMLUsageError(
                    "Can't find port definition matching OutputEvent: {}"
                    .format(output_event))

        # Check that each input event has a corresponding event_port with a
        # recv/reduce mode:
        for input_event in self.input_events:
            if input_event not in self.event_receive_ports:
                raise NineMLUsageError(
                    "Can't find port definition matching input event: {}"
                    .format(input_event))

        # Check that each EventSendPort emits at least one output event
        for port_name in list(self.event_send_ports.keys()):
            if port_name not in self.output_events:
                raise NineMLUsageError(
                    "Unable to find events generated for '{}' in '{}'"
                    .format(port_name, component_class.name))

        # Check that each Event port emits/recieves at least one
        for port_name in list(self.event_receive_ports.keys()):
            if port_name not in self.input_events:
                raise NineMLUsageError(
                    "Unable to find event transitions triggered by '{}' in "
                    "'{}'".format(port_name, component_class.name))

    def action_eventsendport(self, port, **kwargs):  # @UnusedVariable @IgnorePep8
        assert port.name not in self.event_send_ports
        self.event_send_ports[port.name] = port

    def action_eventreceiveport(self, port, **kwargs):  # @UnusedVariable @IgnorePep8
        assert port.name not in self.event_receive_ports
        self.event_receive_ports[port.name] = port

    def action_outputevent(self, output_event, **kwargs):  # @UnusedVariable @IgnorePep8
        self.output_events.append(output_event.port_name)

    def action_onevent(self, on_event, **kwargs):  # @UnusedVariable
        self.input_events.append(on_event.src_port_name)

    def default_action(self, obj, nineml_cls, **kwargs):
        pass


# Check that the sub-components stored are all of the
# right types:
class OutputAnalogPortsDynamicsValidator(BaseDynamicsVisitor):

    """
    Check that all output AnalogPorts reference a local symbol, either an alias
    or a state variable
    """

    def __init__(self, component_class, **kwargs):  # @UnusedVariable
        super(OutputAnalogPortsDynamicsValidator, self).__init__()
        self.output_analogports = []
        self.available_symbols = []
        self.component_class = component_class
        self.visit(component_class)
        for ap in self.output_analogports:
            if ap not in self.available_symbols:
                raise NineMLUsageError(
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

    def default_action(self, obj, nineml_cls, **kwargs):
        pass
