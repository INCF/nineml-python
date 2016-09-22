import unittest
from nineml.abstraction.dynamics.visitors.validators.ports import (OutputAnalogPortsDynamicsValidator, EventPortsDynamicsValidator)
from nineml.utils.testing.comprehensive import instances_of_all_types
from nineml.exceptions import (NineMLRuntimeError)


class TestOutputAnalogPortsDynamicsValidatorExceptions(unittest.TestCase):

    def test___init___ninemlruntimeerror(self):
        """
        line #: 99
        message: Unable to find an Alias or State variable for analog-port '{}' (available '{}')

        context:
        --------
    def __init__(self, component_class, **kwargs):  # @UnusedVariable
        super(OutputAnalogPortsDynamicsValidator, self).__init__(
            require_explicit_overrides=False, **kwargs)
        self.output_analogports = []
        self.available_symbols = []
        self.component_class = component_class
        self.visit(component_class)
        for ap in self.output_analogports:
            if ap not in self.available_symbols:
        """

        outputanalogportsdynamicsvalidator = instances_of_all_types['OutputAnalogPortsDynamicsValidator']
        self.assertRaises(
            NineMLRuntimeError,
            outputanalogportsdynamicsvalidator.__init__,
            component_class=None)


class TestEventPortsDynamicsValidatorExceptions(unittest.TestCase):

    def test___init___ninemlruntimeerror(self):
        """
        line #: 40
        message: Can't find port definition matching OutputEvent: {}

        context:
        --------
    def __init__(self, component_class, **kwargs):  # @UnusedVariable
        super(EventPortsDynamicsValidator, self).__init__(
            require_explicit_overrides=False, **kwargs)

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
        """

        eventportsdynamicsvalidator = instances_of_all_types['EventPortsDynamicsValidator']
        self.assertRaises(
            NineMLRuntimeError,
            eventportsdynamicsvalidator.__init__,
            component_class=None)

    def test___init___ninemlruntimeerror2(self):
        """
        line #: 48
        message: Can't find port definition matching input event: {}

        context:
        --------
    def __init__(self, component_class, **kwargs):  # @UnusedVariable
        super(EventPortsDynamicsValidator, self).__init__(
            require_explicit_overrides=False, **kwargs)

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
                raise NineMLRuntimeError(
                    "Can't find port definition matching OutputEvent: {}"
                    .format(output_event))

        # Check that each input event has a corresponding event_port with a
        # recv/reduce mode:
        for input_event in self.input_events:
            if input_event not in self.event_receive_ports:
        """

        eventportsdynamicsvalidator = instances_of_all_types['EventPortsDynamicsValidator']
        self.assertRaises(
            NineMLRuntimeError,
            eventportsdynamicsvalidator.__init__,
            component_class=None)

    def test___init___ninemlruntimeerror3(self):
        """
        line #: 55
        message: Unable to find events generated for '{}' in '{}'

        context:
        --------
    def __init__(self, component_class, **kwargs):  # @UnusedVariable
        super(EventPortsDynamicsValidator, self).__init__(
            require_explicit_overrides=False, **kwargs)

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

        # Check that each EventSendPort emits at least one output event
        for port_name in self.event_send_ports.keys():
            if port_name not in self.output_events:
        """

        eventportsdynamicsvalidator = instances_of_all_types['EventPortsDynamicsValidator']
        self.assertRaises(
            NineMLRuntimeError,
            eventportsdynamicsvalidator.__init__,
            component_class=None)

    def test___init___ninemlruntimeerror4(self):
        """
        line #: 62
        message: Unable to find event transitions triggered by '{}' in '{}'

        context:
        --------
    def __init__(self, component_class, **kwargs):  # @UnusedVariable
        super(EventPortsDynamicsValidator, self).__init__(
            require_explicit_overrides=False, **kwargs)

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

        # Check that each EventSendPort emits at least one output event
        for port_name in self.event_send_ports.keys():
            if port_name not in self.output_events:
                raise NineMLRuntimeError(
                    "Unable to find events generated for '{}' in '{}'"
                    .format(port_name, component_class.name))

        # Check that each Event port emits/recieves at least one
        for port_name in self.event_receive_ports.keys():
            if port_name not in self.input_events:
        """

        eventportsdynamicsvalidator = instances_of_all_types['EventPortsDynamicsValidator']
        self.assertRaises(
            NineMLRuntimeError,
            eventportsdynamicsvalidator.__init__,
            component_class=None)

