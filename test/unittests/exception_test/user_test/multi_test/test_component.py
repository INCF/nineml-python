import unittest
from nineml.user.multi.dynamics import (
    MultiDynamics, _MultiRegime, _MultiTransition, SubDynamicsProperties)
from nineml.utils.testing.comprehensive import (
    multiDynPropA, multiDynA, dynD, dynE)
from nineml.exceptions import (NineMLNameError, NineMLRuntimeError)
from nineml.user.multi.port_exposures import AnalogReceivePortExposure
from nineml.user.multi.dynamics import SubDynamics


class TestMultiDynamicsExceptions(unittest.TestCase):

    def test___init___ninemlruntimeerror(self):
        """
        line #: 546
        message: Unrecognised port exposure '{}'
        """
        d = SubDynamics('d', dynD)
        e = SubDynamics('e', dynE)
        self.assertRaises(
            NineMLRuntimeError,
            MultiDynamics,
            name='multiDyn',
            sub_components=[d, e],
            port_connections=[
                ('d', 'A1', 'e', 'ARP1'),
                ('e', 'ESP1', 'd', 'ERP1')],
            port_exposures=[AnalogReceivePortExposure('d', 'A1', 'A1_expose')])

    @unittest.skip('Skipping autogenerated unittest skeleton')
    def test___init___ninemlruntimeerror2(self):
        """
        line #: 573
        message: Multiple connections to receive port '{}' in '{} sub-component of '{}'

        context:
        --------
    def __init__(self, name, sub_components, port_connections=[],
                 port_exposures=[], validate_dimensions=True,
                 **kwargs):
        ensure_valid_identifier(name)
        self._name = name
        BaseALObject.__init__(self)
        DocumentLevelObject.__init__(self)
        ContainerObject.__init__(self)
        # =====================================================================
        # Create the structures unique to MultiDynamics
        # =====================================================================
        if isinstance(sub_components, dict):
            self._sub_components = dict(
                (name, SubDynamics(name, dyn))
                for name, dyn in sub_components.iteritems())
        else:
            self._sub_components = dict((d.name, d) for d in sub_components)
        self._analog_send_ports = {}
        self._analog_receive_ports = {}
        self._analog_reduce_ports = {}
        self._event_send_ports = {}
        self._event_receive_ports = {}
        self._analog_port_connections = {}
        self._event_port_connections = {}
        # =====================================================================
        # Save port exposurs into separate member dictionaries
        # =====================================================================
        for exposure in port_exposures:
            if isinstance(exposure, tuple):
                exposure = BasePortExposure.from_tuple(exposure, self)
            exposure.bind(self)
            if isinstance(exposure, AnalogSendPortExposure):
                self._analog_send_ports[exposure.name] = exposure
            elif isinstance(exposure, AnalogReceivePortExposure):
                self._analog_receive_ports[
                    exposure.name] = exposure
            elif isinstance(exposure, AnalogReducePortExposure):
                self._analog_reduce_ports[
                    exposure.name] = exposure
            elif isinstance(exposure, EventSendPortExposure):
                self._event_send_ports[exposure.name] = exposure
            elif isinstance(exposure, EventReceivePortExposure):
                self._event_receive_ports[
                    exposure.name] = exposure
            else:
                raise NineMLRuntimeError(
                    "Unrecognised port exposure '{}'".format(exposure))
        # =====================================================================
        # Set port connections
        # =====================================================================
        # Parse port connections (from tuples if required), bind them to the
        # ports within the subcomponents and append them to their respective
        # member dictionaries
        for port_connection in port_connections:
            if isinstance(port_connection, tuple):
                port_connection = BasePortConnection.from_tuple(
                    port_connection, self)
            port_connection.bind(self)
            snd_key = (port_connection.sender_name,
                       port_connection.send_port_name)
            rcv_key = (port_connection.receiver_name,
                       port_connection.receive_port_name)
            if isinstance(port_connection.receive_port, EventReceivePort):
                if snd_key not in self._event_port_connections:
                    self._event_port_connections[snd_key] = {}
                self._event_port_connections[
                    snd_key][rcv_key] = port_connection
            else:
                if rcv_key not in self._analog_port_connections:
                    self._analog_port_connections[rcv_key] = {}
                elif isinstance(port_connection.receive_port,
                                 AnalogReceivePort):
        """

        multidynamics = next(instances_of_all_types['MultiDynamics'].itervalues())
        self.assertRaises(
            NineMLRuntimeError,
            multidynamics.__init__,
            name=None,
            sub_components=None,
            port_connections=[],
            port_exposures=[],
            document=None,
            validate_dimensions=True)

    @unittest.skip('Skipping autogenerated unittest skeleton')
    def test_analog_port_connection_ninemlnameerror(self):
        """
        line #: 730
        message: Name provided to analog_port_connection '{}' was not a 4-tuple of (sender, send_port, receiver, receive_port)

        context:
        --------
    def analog_port_connection(self, name):
        try:
            sender, send_port, receiver, receive_port = name.split('___')
        except (ValueError, AttributeError):
        """

        multidynamics = next(instances_of_all_types['MultiDynamics'].itervalues())
        self.assertRaises(
            NineMLNameError,
            multidynamics.analog_port_connection,
            name=None)

    @unittest.skip('Skipping autogenerated unittest skeleton')
    def test_analog_port_connection_ninemlnameerror2(self):
        """
        line #: 737
        message: No analog port connection with between {}->{} and {}->{}

        context:
        --------
    def analog_port_connection(self, name):
        try:
            sender, send_port, receiver, receive_port = name.split('___')
        except (ValueError, AttributeError):
            raise NineMLNameError(
                "Name provided to analog_port_connection '{}' was not a "
                "4-tuple of (sender, send_port, receiver, receive_port)")
        try:
            return self._analog_port_connections[
                (sender, send_port)][(receiver, receive_port)]
        except KeyError:
        """

        multidynamics = next(instances_of_all_types['MultiDynamics'].itervalues())
        self.assertRaises(
            NineMLNameError,
            multidynamics.analog_port_connection,
            name=None)

    @unittest.skip('Skipping autogenerated unittest skeleton')
    def test_event_port_connection_ninemlnameerror(self):
        """
        line #: 745
        message: Name provided to analog_port_connection '{}' was not a 4-tuple of (sender, send_port, receiver, receive_port)

        context:
        --------
    def event_port_connection(self, name):
        try:
            sender, send_port, receiver, receive_port = name.split('___')
        except (ValueError, AttributeError):
        """

        multidynamics = next(instances_of_all_types['MultiDynamics'].itervalues())
        self.assertRaises(
            NineMLNameError,
            multidynamics.event_port_connection,
            name=None)

    @unittest.skip('Skipping autogenerated unittest skeleton')
    def test_event_port_connection_ninemlnameerror2(self):
        """
        line #: 752
        message: No event port connection with between {}->{} and {}->{}

        context:
        --------
    def event_port_connection(self, name):
        try:
            sender, send_port, receiver, receive_port = name.split('___')
        except (ValueError, AttributeError):
            raise NineMLNameError(
                "Name provided to analog_port_connection '{}' was not a "
                "4-tuple of (sender, send_port, receiver, receive_port)")
        try:
            return self._event_port_connections[
                (sender, send_port)][(receiver, receive_port)]
        except KeyError:
        """

        multidynamics = next(instances_of_all_types['MultiDynamics'].itervalues())
        self.assertRaises(
            NineMLNameError,
            multidynamics.event_port_connection,
            name=None)

    @unittest.skip('Skipping autogenerated unittest skeleton')
    def test_alias_ninemlnameerror(self):
        """
        line #: 786
        message: Could not find alias corresponding to '{}' in sub-components or port connections/exposures

        context:
        --------
    def alias(self, name):
        try:
            local, comp_name = split_namespace(name)
            try:
                # An alias that is actually a local analog port connection
                alias = _LocalAnalogPortConnections(
                    name, comp_name,
                    self._analog_port_connections[(comp_name, local)].values(),
                    self)
            except KeyError:
                # An alias of a sub component
                alias = self.sub_component(comp_name).alias(name)
        except KeyError:
            try:
                alias = self.analog_send_port(name).alias
            except KeyError:
                try:
                    alias = next(
                        p.alias for p in chain(self.analog_receive_ports,
                                               self.analog_reduce_ports)
                        if p.alias.lhs == name and p.local_port_name != p.name)
                except StopIteration:
        """

        multidynamics = next(instances_of_all_types['MultiDynamics'].itervalues())
        self.assertRaises(
            NineMLNameError,
            multidynamics.alias,
            name=None)

    @unittest.skip('Skipping autogenerated unittest skeleton')
    def test_constant_ninemlnameerror(self):
        """
        line #: 805
        message: '{}' corresponds to a AnalogReduce port, but one thatis used and so is represented by an Alias instead ofa Constant in '{}'

        context:
        --------
    def constant(self, name):
        port_name, comp_name = split_namespace(name)
        sub_component = self.sub_component(comp_name)
        try:
            return sub_component.constant(name)
        except NineMLNameError:
            try:
                reduce_port = sub_component.analog_reduce_port(port_name)
                if ((sub_component.name, reduce_port) not in
                        self._connected_reduce_ports()):
                    return Constant(
                        name, 0.0, reduce_port.dimension.origin.units)
                else:
        """

        multidynamics = next(instances_of_all_types['MultiDynamics'].itervalues())
        self.assertRaises(
            NineMLNameError,
            multidynamics.constant,
            name=None)

    @unittest.skip('Skipping autogenerated unittest skeleton')
    def test_constant_ninemlnameerror2(self):
        """
        line #: 810
        message: Could not find Constant '{}' in '{}

        context:
        --------
    def constant(self, name):
        port_name, comp_name = split_namespace(name)
        sub_component = self.sub_component(comp_name)
        try:
            return sub_component.constant(name)
        except NineMLNameError:
            try:
                reduce_port = sub_component.analog_reduce_port(port_name)
                if ((sub_component.name, reduce_port) not in
                        self._connected_reduce_ports()):
                    return Constant(
                        name, 0.0, reduce_port.dimension.origin.units)
                else:
                    raise NineMLNameError(
                        "'{}' corresponds to a AnalogReduce port, but one that"
                        "is used and so is represented by an Alias instead of"
                        "a Constant in '{}'".format(port_name, comp_name))
            except NineMLNameError:
        """

        multidynamics = next(instances_of_all_types['MultiDynamics'].itervalues())
        self.assertRaises(
            NineMLNameError,
            multidynamics.constant,
            name=None)

    @unittest.skip('Skipping autogenerated unittest skeleton')
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

    @unittest.skip('Skipping autogenerated unittest skeleton')
    def test_analog_receive_port_exposure_ninemlnameerror(self):
        """
        line #: 839
        message: No port exposure that exposes '{}'

        context:
        --------
    def analog_receive_port_exposure(self, exposed_port_name):
        port_name, comp_name = split_namespace(exposed_port_name)
        try:
            exposure = next(pe for pe in chain(self.analog_receive_ports,
                                               self.analog_reduce_ports)
                            if (pe.port_name == port_name and
                                pe.sub_component.name == comp_name))
        except StopIteration:
        """

        multidynamics = next(instances_of_all_types['MultiDynamics'].itervalues())
        self.assertRaises(
            NineMLNameError,
            multidynamics.analog_receive_port_exposure,
            exposed_port_name=None)

    @unittest.skip('Skipping autogenerated unittest skeleton')
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

    @unittest.skip('Skipping autogenerated unittest skeleton')
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

    @unittest.skip('Skipping autogenerated unittest skeleton')
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

    @unittest.skip('Skipping autogenerated unittest skeleton')
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

    @unittest.skip('Skipping autogenerated unittest skeleton')
    def test_state_assignment_ninemlnameerror(self):
        """
        line #: 1198
        message: No state assignment for variable '{}' found in transition

        context:
        --------
    def state_assignment(self, variable):
        try:
            return next(sa for sa in self.state_assignments
                        if sa.variable == variable)
        except StopIteration:
        """

        _multitransition = next(instances_of_all_types['_MultiTransition'].itervalues())
        self.assertRaises(
            NineMLNameError,
            _multitransition.state_assignment,
            variable=None)

    @unittest.skip('Skipping autogenerated unittest skeleton')
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

    @unittest.skip('Skipping autogenerated unittest skeleton')
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

    @unittest.skip('Skipping autogenerated unittest skeleton')
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

