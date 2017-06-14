import os.path
import unittest
import sympy
from nineml import units as un, Document
from nineml.serialization.xml import XMLUnserializer
from nineml.user.multi.dynamics import (
    MultiDynamicsProperties, MultiDynamics)
from nineml.abstraction import (
    Dynamics, Regime, AnalogReceivePort, AnalogReducePort, OutputEvent,
    AnalogSendPort, On, StateAssignment, Constant)
from nineml.user.dynamics import DynamicsProperties
from nineml.user.multi.port_exposures import (
    _LocalAnalogPortConnections, _ReceivePortExposureAlias)


examples_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..',
                            'xml', 'neurons')


class MultiDynamicsXML_test(unittest.TestCase):

    def setUp(self):

        self.a = Dynamics(
            name='A',
            aliases=['A1:=P1', 'A2 := ARP1 + SV2', 'A3 := SV1'],
            regimes=[
                Regime(
                    'dSV1/dt = -SV1 / (P2*t)',
                    'dSV2/dt = SV1 / (ARP1*t) + SV2 / (P1*t)',
                    transitions=[On('SV1 > P1', do=[OutputEvent('emit')]),
                                 On('spikein', do=[OutputEvent('emit')])],
                    name='R1',
                ),
                Regime(name='R2', transitions=On('SV1 > 1', to='R1'))
            ],
            analog_ports=[AnalogReceivePort('ARP1'),
                          AnalogReceivePort('ARP2'),
                          AnalogSendPort('A1'),
                          AnalogSendPort('A2')],
            parameters=['P1', 'P2']
        )

        self.b = Dynamics(
            name='B',
            aliases=['A1:=P1', 'A2 := ARP1 + SV2', 'A3 := SV1',
                     'A4 := SV1^3 + SV2^3'],
            regimes=[
                Regime(
                    'dSV1/dt = -SV1 / (P2*t)',
                    'dSV2/dt = SV1 / (ARP1*t) + SV2 / (P1*t)',
                    'dSV3/dt = -SV3/t + P3/t',
                    transitions=[On('SV1 > P1', do=[OutputEvent('emit')]),
                                 On('spikein', do=[
                                    OutputEvent('emit'),
                                    StateAssignment('SV1', 'P1')])],
                    name='R1',
                ),
                Regime(name='R2', transitions=[
                    On('SV1 > 1', to='R1'),
                    On('SV3 < 0.001', to='R2',
                       do=[StateAssignment('SV3', 1)])])
            ],
            analog_ports=[AnalogReceivePort('ARP1'),
                          AnalogReceivePort('ARP2'),
                          AnalogSendPort('A1'),
                          AnalogSendPort('A2'),
                          AnalogSendPort('A3'),
                          AnalogSendPort('SV3')],
            parameters=['P1', 'P2', 'P3']
        )

        self.a_props = DynamicsProperties(
            name="AProps", definition=self.a, properties={'P1': 1, 'P2': 2})
        self.b_props = DynamicsProperties(
            name="BProps", definition=self.b, properties={'P1': 1, 'P2': 2,
                                                          'P3': 3})

    def test_multicomponent_xml_roundtrip(self):
        comp1 = MultiDynamicsProperties(
            name='test',
            sub_components={'a': self.a_props, 'b': self.b_props},
            port_exposures=[("b", "ARP2", "b_ARP2")],
            port_connections=[('a', 'A1', 'b', 'ARP1'),
                              ('b', 'A1', 'a', 'ARP1'),
                              ('b', 'A3', 'a', 'ARP2')])
        xml = Document(comp1, self.a, self.b).serialize(version=2)
        comp2 = XMLUnserializer(root=xml).unserialize()['test']
        if comp1 != comp2:
            print comp2.find_mismatch(comp1)
        self.assertEquals(comp1, comp2)


class MultiDynamicsFlattening_test(unittest.TestCase):

    def test_basic_flattening(self):

        c = Dynamics(
            name='C',
            aliases=['C1:=cp1', 'C2 := cIn1', 'C3 := SV1'],
            regimes=[
                Regime(
                    'dSV1/dt = -SV1/(cp2*t)',
                    transitions=[On('SV1>cp1', do=[OutputEvent('emit')]),
                                 On('spikein',
                                    do=[OutputEvent('emit'),
                                        StateAssignment('SV1', '10')])],
                    name='r1',
                ),
                Regime(name='r2', transitions=On('SV1>1', to='r1'))
            ],
            analog_ports=[AnalogReceivePort('cIn1'), AnalogReceivePort('cIn2'),
                          AnalogSendPort('C1'), AnalogSendPort('C2')],
            parameters=['cp1', 'cp2']
        )

        d = Dynamics(
            name='D',
            aliases=['D1:=dp1', 'D2 := dIn1', 'D3 := SV1'],
            regimes=[
                Regime(
                    'dSV1/dt = -SV1/(dp2*t)',
                    transitions=[On('SV1>dp1', do=[OutputEvent('emit')]),
                                 On('spikein', do=[OutputEvent('emit')])],
                    name='r1',
                ),
                Regime(name='r2', transitions=On('SV1>1', to='r1'))
            ],
            analog_ports=[AnalogReceivePort('dIn1'), AnalogReceivePort('dIn2'),
                          AnalogSendPort('D1'), AnalogSendPort('D2')],
            parameters=['dp1', 'dp2']
        )

        e = MultiDynamics(
            name='E', sub_components={'a': c, 'b': d},
            port_connections=[('a', 'C1', 'b', 'dIn1'),
                              ('a', 'C2', 'b', 'dIn2')],
            port_exposures=[('a', 'cIn1', 'ARP1'),
                            ('a', 'cIn2', 'ARP2'),
                            ('a', 'spikein', 'ERP1'),
                            ('a', 'emit', 'ESP1')])

        # =====================================================================
        # General properties
        # =====================================================================
        self.assertEqual(e.name, 'E')
        self.assertEqual(set(e.parameter_names),
                         set(['cp1__a', 'cp2__a', 'dp1__b', 'dp2__b']))
        cp1 = e.parameter('cp1__a')
        self.assertEqual(cp1.dimension, un.dimensionless)
        self.assertEqual(set(e.analog_receive_port_names),
                         set(['ARP1', 'ARP2']))
        arp1 = e.analog_receive_port('ARP1')
        self.assertEqual(arp1.dimension, un.dimensionless)
        self.assertEqual(set(e.event_receive_port_names), set(['ERP1']))
        self.assertEqual(set(e.event_send_port_names), set(['ESP1']))
        self.assertEqual(set(e.alias_names),
                         set(['C1__a', 'C2__a', 'C3__a', 'D1__b', 'D2__b',
                              'D3__b', 'cIn1__a', 'cIn2__a', 'dIn1__b',
                              'dIn2__b']))
        self.assertEqual(e.alias('C1__a').rhs, sympy.sympify('cp1__a'))
        self.assertIsInstance(e.alias('cIn1__a'), _ReceivePortExposureAlias)
        self.assertIsInstance(e.alias('dIn1__b'), _LocalAnalogPortConnections)
        self.assertEqual(set(e.state_variable_names),
                         set(['SV1__a', 'SV1__b']))
        self.assertEqual(e.state_variable('SV1__a').dimension,
                         un.dimensionless)
        # - Regimes and Transitions:
        self.assertEqual(set(e.regime_names),
                         set(['r1___r1', 'r1___r2',
                              'r2___r1', 'r2___r2']))
        # =====================================================================
        # Regime a=1, b=2
        # =====================================================================
        r11 = e.regime('r1___r1')
        self.assertEqual(r11.num_on_conditions, 2)
        self.assertEqual(r11.num_on_events, 1)
        oe1 = r11.on_event('ERP1')
        self.assertEqual(oe1.num_output_events, 1)
        out1 = oe1.output_event('ESP1')
        self.assertEqual(out1.port, e.event_send_port('ESP1'))
        self.assertEqual(oe1.num_state_assignments, 1)
        self.assertEqual(oe1.state_assignment('SV1__a').rhs, 10)
        self.assertEqual(set(oe1.state_assignment_variables),
                         set(('SV1__a',)))
        self.assertEqual(r11.num_on_conditions, 2)
        oc1 = r11.on_condition('SV1__a > cp1__a')
        self.assertEqual(oc1.num_output_events, 1)
        self.assertEqual(oc1.target_regime, r11)
        out1 = oc1.output_event('ESP1')
        self.assertEqual(out1.port, e.event_send_port('ESP1'))
        self.assertEqual(oc1.num_state_assignments, 0)
        oc2 = r11.on_condition('SV1__b > dp1__b')
        self.assertEqual(oc2.num_output_events, 0)
        self.assertEqual(oc2.num_state_assignments, 0)
        self.assertEqual(oc2.target_regime, r11)
        # =====================================================================
        # Regime a=1, b=2
        # =====================================================================
        r12 = e.regime('r1___r2')
        self.assertEqual(r12.num_on_conditions, 2)
        oc1 = r12.on_condition('SV1__a > cp1__a')
        self.assertEqual(set(oc1.output_event_port_names), set(('ESP1',)))
        self.assertEqual(oc1.target_regime, r12)
        oc2 = r12.on_condition('SV1__b > 1')
        self.assertEqual(oc2.num_output_events, 0)
        self.assertEqual(oc2.target_regime, r11)
        self.assertEqual(r12.num_on_events, 1)
        self.assertEqual(r12.on_event('ERP1').port.port,
                         c.event_receive_port('spikein'))
        # =====================================================================
        # Regime a=2, b=1
        # =====================================================================
        r21 = e.regime('r2___r1')
        self.assertEqual(r21.num_on_conditions, 2)
        oc1 = r21.on_condition('SV1__a > 1')
        self.assertEqual(oc1.num_output_events, 0)
        self.assertEqual(oc1.num_state_assignments, 0)
        self.assertEqual(oc1.target_regime, r11)
        oc2 = r21.on_condition('SV1__b > dp1__b')
        self.assertEqual(oc2.num_output_events, 0)
        self.assertEqual(oc2.num_state_assignments, 0)
        self.assertEqual(oc2.target_regime, r21)
        self.assertEqual(r21.num_on_events, 0)
        # =====================================================================
        # Regime a=2, b=2
        # =====================================================================
        r22 = e.regime('r2___r2')
        self.assertEqual(r21.num_on_conditions, 2)
        oc1 = r22.on_condition('SV1__a > 1')
        self.assertEqual(oc1.num_output_events, 0)
        self.assertEqual(oc1.num_state_assignments, 0)
        self.assertEqual(oc1.target_regime, r12)
        oc2 = r22.on_condition('SV1__b > 1')
        self.assertEqual(oc2.num_output_events, 0)
        self.assertEqual(oc2.num_state_assignments, 0)
        self.assertEqual(oc2.target_regime, r21)
        #  - Ports & Parameters:
        self.assertEqual(set(e.analog_receive_port_names),
                         set(['ARP1', 'ARP2']))
        self.assertEqual(set(e.parameter_names),
                         set(['cp1__a', 'cp2__a', 'dp1__b', 'dp2__b']))
        self.assertEqual(set(e.state_variable_names),
                         set(['SV1__a', 'SV1__b']))

    def test_unused_reduce_ports(self):
        """
        Tests whether empty reduce ports are "closed" by inserting a zero-
        valued constant in their stead
        """
        test_dyn = Dynamics(
            name='TestDyn',
            regimes=[
                Regime(
                    'dSV1/dt = -P1/t + ADP1', name='r1')],
            analog_ports=[AnalogReducePort('ADP1', un.per_time)],
            parameters=['P1']
        )

        test_multi = MultiDynamics(
            name="TestMultiDyn",
            sub_components={'cell': test_dyn})

        self.assert_(Constant('ADP1__cell', 0.0, un.per_time.origin.units)
                     in test_multi.constants,
                     "Zero-valued constant wasn't inserted for unused reduce "
                     "port")
