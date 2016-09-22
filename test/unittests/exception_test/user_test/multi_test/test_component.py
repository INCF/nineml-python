import unittest
from nineml.user.multi.component import (MultiDynamics, _MultiRegime, _MultiTransition, SubDynamicsProperties)
from nineml.utils.testing.comprehensive import instances_of_all_types
from nineml.exceptions import (NineMLNameError, KeyError, NineMLRuntimeError)


class TestMultiDynamicsExceptions(unittest.TestCase):

    def test_regime_ninemlnameerror(self):
        """
        line #: 820
        message: The number of regime names extracted from '{}' ({}) does not match the number of sub-components ('{}'). NB: the format for multi-regimes is '___' delimited list of regime names sorted by sub-component names)

        context:
        --------
    def regime(self, name):
        try:
            sub_regime_names = split_multi_regime_name(name)
        except TypeError:
            sub_regime_names = name  # Assume it is already an iterable
        if len(sub_regime_names) != len(self._sub_component_keys):
        """

        multidynamics = next(instances_of_all_types['MultiDynamics'].itervalues())
        self.assertRaises(
            NineMLNameError,
            multidynamics.regime,
            name=None)

    def test_validate_ninemlruntimeerror(self):
        """
        line #: 889
        message: Analog receive port '{}' in sub component '{}' was not connected via a port-connection or exposed via a port-exposure in MultiDynamics object '{}'

        context:
        --------
    def validate(self, **kwargs):
        exposed_ports = [pe.port for pe in self.analog_receive_ports]
        connected_ports = [pc.receive_port
                           for pc in self.analog_port_connections]
        for sub_component in self.sub_components:
            for port in sub_component.component_class.analog_receive_ports:
                if port not in chain(exposed_ports, connected_ports):
        """

        multidynamics = next(instances_of_all_types['MultiDynamics'].itervalues())
        self.assertRaises(
            NineMLRuntimeError,
            multidynamics.validate)


class Test_MultiRegimeExceptions(unittest.TestCase):

    def test_on_event_keyerror(self):
        """
        line #: 1033
        message: No OnEvent for receive port '{}'

        context:
        --------
    def on_event(self, port_name):
        port_exposure = self._parent.event_receive_port(port_name)
        sub_on_events = [oe for oe in self._all_sub_on_events
                         if oe.src_port_name == port_exposure.local_port_name]
        if not sub_on_events:
        """

        _multiregime = next(instances_of_all_types['_MultiRegime'].itervalues())
        self.assertRaises(
            KeyError,
            _multiregime.on_event,
            port_name=None)

    def test_on_condition_keyerror(self):
        """
        line #: 1041
        message: No OnCondition with trigger condition '{}'

        context:
        --------
    def on_condition(self, condition):
        sub_conds = [oc for oc in self._all_sub_on_conds
                     if oc.trigger.rhs == sympy.sympify(condition)]
        if not sub_conds:
        """

        _multiregime = next(instances_of_all_types['_MultiRegime'].itervalues())
        self.assertRaises(
            KeyError,
            _multiregime.on_condition,
            condition=None)


class Test_MultiTransitionExceptions(unittest.TestCase):

    def test___init___ninemlruntimeerror(self):
        """
        line #: 1130
        message: Transition loop with non-zero delay found in on-event chain beggining with {}

        context:
        --------
    def __init__(self, sub_transitions, parent):
        BaseALObject.__init__(self)
        ContainerObject.__init__(self)
        self._sub_transitions = dict(
            (st.sub_component.name, st) for st in sub_transitions)
        for chained_event in parent.daisy_chained_on_events(sub_transitions):
            namespace = chained_event.sub_component.name
            if namespace in self._sub_transitions:
        """

        _multitransition = next(instances_of_all_types['_MultiTransition'].itervalues())
        self.assertRaises(
            NineMLRuntimeError,
            _multitransition.__init__,
            sub_transitions=None,
            parent=None)

    def test_output_event_ninemlnameerror(self):
        """
        line #: 1205
        message: Output event for '{}' port is not present in transition

        context:
        --------
    def output_event(self, name):
        exposure = self._parent._parent.event_send_port(name)
        if exposure.port not in self._sub_output_event_ports:
        """

        _multitransition = next(instances_of_all_types['_MultiTransition'].itervalues())
        self.assertRaises(
            NineMLNameError,
            _multitransition.output_event,
            name=None)


class TestSubDynamicsPropertiesExceptions(unittest.TestCase):

    def test_initial_value_keyerror(self):
        """
        line #: 264
        message: name

        context:
        --------
    def initial_value(self, name):
        local_name, comp_name = split_namespace(name)
        if comp_name != self.name:
        """

        subdynamicsproperties = next(instances_of_all_types['SubDynamicsProperties'].itervalues())
        self.assertRaises(
            KeyError,
            subdynamicsproperties.initial_value,
            name=None)

    def test_property_keyerror(self):
        """
        line #: 284
        message: name

        context:
        --------
    def property(self, name):
        local_name, comp_name = split_namespace(name)
        if comp_name != self.name:
        """

        subdynamicsproperties = next(instances_of_all_types['SubDynamicsProperties'].itervalues())
        self.assertRaises(
            KeyError,
            subdynamicsproperties.property,
            name=None)

