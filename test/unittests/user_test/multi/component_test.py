import os.path
import unittest
import sympy
from nineml import units as un
from nineml import Document
from nineml.user.multi.component import (
    MultiDynamicsProperties, SubDynamicsProperties, MultiDynamics,
    AnalogReceivePortExposure)
from nineml.abstraction import (
    Dynamics, Regime, AnalogReceivePort, AnalogReducePort, OutputEvent,
    AnalogSendPort, On, StateAssignment, Constant)
from nineml.user.port_connections import AnalogPortConnection
from nineml.user.component import DynamicsProperties
from nineml.exceptions import NineMLRuntimeError
from nineml.utils import TestableComponent
from nineml.user.multi.port_exposures import (
    _LocalAnalogPortConnections, _ReceivePortExposureAlias)
from lxml import etree


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
        xml = Document(comp1, self.a, self.b).to_xml()
        comp2 = Document.load(xml)['test']
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

#     def test_Flattening2(self):
#         c = Dynamics(
#             name='C',
#             aliases=['C1:=cp1', 'C2 := cIn1', 'C3 := SV1'],
#             regimes=[
#                 Regime(
#                     'dSV1/dt = -SV1/(cp2*t)',
#                     transitions=[On('SV1>cp1', do=[OutputEvent('emit')]),
#                                  On('spikein', do=[OutputEvent('c_emit')])],
#                     name='r1',
#                 ),
#                 Regime(name='r2', transitions=On('SV1>1', to='r1'))
#             ],
#             analog_ports=[AnalogReceivePort('cIn1'), AnalogReceivePort('cIn2'),
#                           AnalogSendPort('C1'), AnalogSendPort('C2')],
#             parameters=['cp1', 'cp2']
#         )
# 
#         d = Dynamics(
#             name='D',
#             aliases=['D1:=dp1', 'D2 := dIn1', 'D3 := SV1'],
#             regimes=[
#                 Regime(
#                     'dSV1/dt = -SV1/(dp2*t)',
#                     transitions=[On('SV1>dp1', do=[OutputEvent('emit')]),
#                                  On('spikein', do=[OutputEvent('d_emit')])],
#                     name='r1',
#                 ),
#                 Regime(name='r2', transitions=On('SV1>1', to='r1'))
#             ],
#             analog_ports=[AnalogReceivePort('dIn1'), AnalogReceivePort('dIn2'),
#                           AnalogSendPort('D1'), AnalogSendPort('D2')],
#             parameters=['dp1', 'dp2']
#         )
# 
#         # Test Cloner, 1 level of hierachy
#         # ------------------------------ #
# 
#         # Everything should be as before:
#         b = MultiDynamics(
#             name='B',
#             sub_components={'c1': c, 'c2': c, 'd': d},
#             port_connections=[
#                 ('c1', 'C1', 'c2', 'cIn1'),
#                 ('c2', 'emit', 'c1', 'spikein')])
# 
#         b_flat = b.flatten(b)
# 
#         # Name
#         self.assertEqual(b_flat.name, 'B')
# 
#         # Aliases
#         self.assertEqual(
#             set(b_flat.alias_names),
#             set(['c1_C1', 'c1_C2', 'c1_C3', 'c2_C1', 'c2_C2', 'c2_C3',
#                  'd_D1', 'd_D2', 'd_D3']))
# 
#         # - Regimes and Transitions:
#         self.assertEqual(len(b_flat._regimes), 8)
#         r_c1_1_c2_1_d_1 = b_flat.flattener.get_new_regime('d:r1 c1:r1 c2:r1 ')
#         r_c1_1_c2_2_d_1 = b_flat.flattener.get_new_regime('d:r1 c1:r1 c2:r2 ')
#         r_c1_2_c2_1_d_1 = b_flat.flattener.get_new_regime('d:r1 c1:r2 c2:r1')
#         r_c1_2_c2_2_d_1 = b_flat.flattener.get_new_regime('d:r1 c1:r2 c2:r2')
#         r_c1_1_c2_1_d_2 = b_flat.flattener.get_new_regime('d:r2 c1:r1 c2:r1 ')
#         r_c1_1_c2_2_d_2 = b_flat.flattener.get_new_regime('d:r2 c1:r1 c2:r2 ')
#         r_c1_2_c2_1_d_2 = b_flat.flattener.get_new_regime('d:r2 c1:r2 c2:r1')
#         r_c1_2_c2_2_d_2 = b_flat.flattener.get_new_regime('d:r2 c1:r2 c2:r2')
# 
#         # Do we have the right number of on_events and on_conditions:
#         self.assertEqual(len(list(r_c1_1_c2_1_d_1.on_events)), 3)
#         self.assertEqual(len(list(r_c1_1_c2_1_d_1.on_conditions)), 3)
#         self.assertEqual(len(list(r_c1_1_c2_2_d_1.on_events)), 2)
#         self.assertEqual(len(list(r_c1_1_c2_2_d_1.on_conditions)), 3)
#         self.assertEqual(len(list(r_c1_2_c2_1_d_1.on_events)), 2)
#         self.assertEqual(len(list(r_c1_2_c2_1_d_1.on_conditions)), 3)
#         self.assertEqual(len(list(r_c1_2_c2_2_d_1.on_events)), 1)
#         self.assertEqual(len(list(r_c1_2_c2_2_d_1.on_conditions)), 3)
# 
#         self.assertEqual(len(list(r_c1_1_c2_1_d_2.on_events)), 2)
#         self.assertEqual(len(list(r_c1_1_c2_1_d_2.on_conditions)), 3)
#         self.assertEqual(len(list(r_c1_1_c2_2_d_2.on_events)), 1)
#         self.assertEqual(len(list(r_c1_1_c2_2_d_2.on_conditions)), 3)
#         self.assertEqual(len(list(r_c1_2_c2_1_d_2.on_events)), 1)
#         self.assertEqual(len(list(r_c1_2_c2_1_d_2.on_conditions)), 3)
#         self.assertEqual(len(list(r_c1_2_c2_2_d_2.on_events)), 0)
#         self.assertEqual(len(list(r_c1_2_c2_2_d_2.on_conditions)), 3)
# 
#         # All on_events return to thier same transition:
#         self.assertEqual((list(r_c1_1_c2_1_d_1.on_events))[0].target_regime,
#                           r_c1_1_c2_1_d_1)
#         self.assertEqual((list(r_c1_1_c2_1_d_1.on_events))[1].target_regime,
#                           r_c1_1_c2_1_d_1)
#         self.assertEqual((list(r_c1_1_c2_1_d_1.on_events))[2].target_regime,
#                           r_c1_1_c2_1_d_1)
#         self.assertEqual((list(r_c1_1_c2_2_d_1.on_events))[0].target_regime,
#                           r_c1_1_c2_2_d_1)
#         self.assertEqual((list(r_c1_1_c2_2_d_1.on_events))[1].target_regime,
#                           r_c1_1_c2_2_d_1)
#         self.assertEqual((list(r_c1_2_c2_1_d_1.on_events))[0].target_regime,
#                           r_c1_2_c2_1_d_1)
#         self.assertEqual((list(r_c1_2_c2_1_d_1.on_events))[1].target_regime,
#                           r_c1_2_c2_1_d_1)
#         self.assertEqual((list(r_c1_2_c2_2_d_1.on_events))[0].target_regime,
#                           r_c1_2_c2_2_d_1)
#         self.assertEqual((list(r_c1_1_c2_1_d_2.on_events))[0].target_regime,
#                           r_c1_1_c2_1_d_2)
#         self.assertEqual((list(r_c1_1_c2_1_d_2.on_events))[1].target_regime,
#                           r_c1_1_c2_1_d_2)
#         self.assertEqual((list(r_c1_1_c2_2_d_2.on_events))[0].target_regime,
#                           r_c1_1_c2_2_d_2)
#         self.assertEqual((list(r_c1_2_c2_1_d_2.on_events))[0].target_regime,
#                           r_c1_2_c2_1_d_2)
# 
#         # Check On-Event port names are remapped properly:
#         self.assertEqual(set([ev.src_port_name
#                               for ev in r_c1_1_c2_1_d_1.on_events]),
#                          set(['c1_spikein', 'c2_spikein', 'd_spikein']))
#         self.assertEqual(
#             set([ev.src_port_name for ev in r_c1_1_c2_2_d_1.on_events]),
#             set(['c1_spikein', 'd_spikein']))
#         self.assertEqual(
#             set([ev.src_port_name for ev in r_c1_2_c2_1_d_1.on_events]),
#             set(['c2_spikein', 'd_spikein']))
#         self.assertEqual(
#             set([ev.src_port_name for ev in r_c1_2_c2_2_d_1.on_events]),
#             set(['d_spikein']))
#         self.assertEqual(
#             set([ev.src_port_name for ev in r_c1_1_c2_1_d_2.on_events]),
#             set(['c1_spikein', 'c2_spikein']))
#         self.assertEqual(
#             set([ev.src_port_name for ev in r_c1_1_c2_2_d_2.on_events]),
#             set(['c1_spikein', ]))
#         self.assertEqual(
#             set([ev.src_port_name for ev in r_c1_2_c2_1_d_2.on_events]),
#             set(['c2_spikein', ]))
#         self.assertEqual(set([ev.src_port_name
#                               for ev in r_c1_2_c2_2_d_2.on_events]), set([]))
# 
#         # ToDo: Check the OnConditions:
#         #  - Ports & Parameters:
#         self.assertEqual(
#             set(b_flat.analog_port_names),
#             set(['c1_cIn1', 'c1_cIn2', 'c1_C1', 'c1_C2', 'c2_cIn1', 'c2_cIn2',
#                  'c2_C1', 'c2_C2', 'd_dIn1', 'd_dIn2', 'd_D1', 'd_D2']))
# 
#         self.assertEqual(
#             set(b_flat.event_port_names),
#             set(['c1_spikein', 'c1_emit', 'c1_c_emit', 'c2_spikein', 'c2_emit',
#                  'c2_c_emit', 'd_spikein', 'd_emit', 'd_d_emit']))
# 
#         self.assertEqual(
#             set(b_flat.parameter_names),
#             set(['c1_cp1', 'c1_cp2', 'c2_cp1', 'c2_cp2', 'd_dp1', 'd_dp2', ]))
# 
#         self.assertEqual(
#             set(b_flat.state_variable_names),
#             set(['c1_SV1', 'c2_SV1', 'd_SV1']))
# 
#     def test_Flattening3(self):
# 
#         c = Dynamics(
#             name='C',
#             aliases=['C1:=cp1', 'C2 := cIn1', 'C3 := SV1'],
#             regimes=[
#                 Regime(
#                     'dSV1/dt = -SV1/(cp2*t)',
#                     transitions=[On('SV1>cp1', do=[OutputEvent('emit')]),
#                                  On('spikein', do=[OutputEvent('c_emit')])],
#                     name='r1',
#                 ),
#                 Regime(name='r2', transitions=On('SV1>1', to='r1'))
#             ],
#             analog_ports=[AnalogReceivePort('cIn1'), AnalogReceivePort('cIn2'),
#                           AnalogSendPort('C1'), AnalogSendPort('C2')],
#             parameters=['cp1', 'cp2']
#         )
# 
#         d = Dynamics(
#             name='D',
#             aliases=['D1:=dp1', 'D2 := dIn1', 'D3 := SV1'],
#             regimes=[
#                 Regime(
#                     'dSV1/dt = -SV1/(dp2*t)',
#                     transitions=[On('SV1>dp1', do=[OutputEvent('emit')]),
#                                  On('spikein', do=[OutputEvent('d_emit')])],
#                     name='r1',
#                 ),
#                 Regime(name='r2', transitions=On('SV1>1', to='r1'))
#             ],
#             analog_ports=[AnalogReceivePort('dIn1'), AnalogReceivePort('dIn2'),
#                           AnalogSendPort('D1'), AnalogSendPort('D2')],
#             parameters=['dp1', 'dp2']
#         )
# 
#         # Test Cloner, 2 levels of hierachy
#         # ------------------------------ #
# 
#         # Everything should be as before:
#         b = MultiDynamics(name='B', sub_components={'c1': c, 'c2': c, 'd': d},
#                           port_connections=[('c1', 'C1', 'c2', 'cIn1'),
#                                             ('c2', 'C1', 'c1', 'cIn1'),
#                                             ('c2', 'C2', 'd', 'dIn2')])
#         a = MultiDynamics(name='A', sub_components={'b': b, 'c': c})
# 
#         a_flat = b.flatten(a)
# 
#         # Name
#         self.assertEqual(a_flat.name, 'A')
# 
#         # Aliases
#         self.assertEqual(
#             set(a_flat.alias_names),
#             set(['b_c1_C1', 'b_c1_C2', 'b_c1_C3', 'b_c2_C1', 'b_c2_C2',
#                  'b_c2_C3', 'b_d_D1', 'b_d_D2', 'b_d_D3', 'c_C1', 'c_C2',
#                  'c_C3']))
# 
#         # - Regimes and Transitions:
#         self.assertEqual(len(a_flat._regimes), 16)
#         r_c1_1_c2_1_d_1_c_1 = a_flat.flattener.get_new_regime('b.d:r1 b.c1:r1 b.c2:r1 c:r1')
#         r_c1_1_c2_2_d_1_c_1 = a_flat.flattener.get_new_regime('b.d:r1 b.c1:r1 b.c2:r2 c:r1')
#         r_c1_2_c2_1_d_1_c_1 = a_flat.flattener.get_new_regime('b.d:r1 b.c1:r2 b.c2:r1 c:r1')
#         r_c1_2_c2_2_d_1_c_1 = a_flat.flattener.get_new_regime('b.d:r1 b.c1:r2 b.c2:r2 c:r1')
#         r_c1_1_c2_1_d_2_c_1 = a_flat.flattener.get_new_regime('b.d:r2 b.c1:r1 b.c2:r1 c:r1')
#         r_c1_1_c2_2_d_2_c_1 = a_flat.flattener.get_new_regime('b.d:r2 b.c1:r1 b.c2:r2 c:r1')
#         r_c1_2_c2_1_d_2_c_1 = a_flat.flattener.get_new_regime('b.d:r2 b.c1:r2 b.c2:r1 c:r1')
#         r_c1_2_c2_2_d_2_c_1 = a_flat.flattener.get_new_regime('b.d:r2 b.c1:r2 b.c2:r2 c:r1')
#         r_c1_1_c2_1_d_1_c_2 = a_flat.flattener.get_new_regime('b.d:r1 b.c1:r1 b.c2:r1 c:r2')
#         r_c1_1_c2_2_d_1_c_2 = a_flat.flattener.get_new_regime('b.d:r1 b.c1:r1 b.c2:r2 c:r2')
#         r_c1_2_c2_1_d_1_c_2 = a_flat.flattener.get_new_regime('b.d:r1 b.c1:r2 b.c2:r1 c:r2')
#         r_c1_2_c2_2_d_1_c_2 = a_flat.flattener.get_new_regime('b.d:r1 b.c1:r2 b.c2:r2 c:r2')
#         r_c1_1_c2_1_d_2_c_2 = a_flat.flattener.get_new_regime('b.d:r2 b.c1:r1 b.c2:r1 c:r2')
#         r_c1_1_c2_2_d_2_c_2 = a_flat.flattener.get_new_regime('b.d:r2 b.c1:r1 b.c2:r2 c:r2')
#         r_c1_2_c2_1_d_2_c_2 = a_flat.flattener.get_new_regime('b.d:r2 b.c1:r2 b.c2:r1 c:r2')
#         r_c1_2_c2_2_d_2_c_2 = a_flat.flattener.get_new_regime('b.d:r2 b.c1:r2 b.c2:r2 c:r2')
# 
#         regimes = [
#             r_c1_1_c2_1_d_1_c_1,
#             r_c1_1_c2_2_d_1_c_1,
#             r_c1_2_c2_1_d_1_c_1,
#             r_c1_2_c2_2_d_1_c_1,
#             r_c1_1_c2_1_d_2_c_1,
#             r_c1_1_c2_2_d_2_c_1,
#             r_c1_2_c2_1_d_2_c_1,
#             r_c1_2_c2_2_d_2_c_1,
#             r_c1_1_c2_1_d_1_c_2,
#             r_c1_1_c2_2_d_1_c_2,
#             r_c1_2_c2_1_d_1_c_2,
#             r_c1_2_c2_2_d_1_c_2,
#             r_c1_1_c2_1_d_2_c_2,
#             r_c1_1_c2_2_d_2_c_2,
#             r_c1_2_c2_1_d_2_c_2,
#             r_c1_2_c2_2_d_2_c_2]
#         self.assertEqual(len(set(regimes)), 16)
# 
#         # Do we have the right number of on_events and on_conditions:
#         self.assertEqual(len(list(r_c1_1_c2_1_d_1_c_1.on_events)), 4)
#         self.assertEqual(len(list(r_c1_1_c2_1_d_1_c_1.on_conditions)), 4)
#         self.assertEqual(len(list(r_c1_1_c2_2_d_1_c_1.on_events)), 3)
#         self.assertEqual(len(list(r_c1_1_c2_2_d_1_c_1.on_conditions)), 4)
#         self.assertEqual(len(list(r_c1_2_c2_1_d_1_c_1.on_events)), 3)
#         self.assertEqual(len(list(r_c1_2_c2_1_d_1_c_1.on_conditions)), 4)
#         self.assertEqual(len(list(r_c1_2_c2_2_d_1_c_1.on_events)), 2)
#         self.assertEqual(len(list(r_c1_2_c2_2_d_1_c_1.on_conditions)), 4)
#         self.assertEqual(len(list(r_c1_1_c2_1_d_2_c_1.on_events)), 3)
#         self.assertEqual(len(list(r_c1_1_c2_1_d_2_c_1.on_conditions)), 4)
#         self.assertEqual(len(list(r_c1_1_c2_2_d_2_c_1.on_events)), 2)
#         self.assertEqual(len(list(r_c1_1_c2_2_d_2_c_1.on_conditions)), 4)
#         self.assertEqual(len(list(r_c1_2_c2_1_d_2_c_1.on_events)), 2)
#         self.assertEqual(len(list(r_c1_2_c2_1_d_2_c_1.on_conditions)), 4)
#         self.assertEqual(len(list(r_c1_2_c2_2_d_2_c_1.on_events)), 1)
#         self.assertEqual(len(list(r_c1_2_c2_2_d_2_c_1.on_conditions)), 4)
# 
#         self.assertEqual(len(list(r_c1_1_c2_1_d_1_c_2.on_events)), 3)
#         self.assertEqual(len(list(r_c1_1_c2_1_d_1_c_2.on_conditions)), 4)
#         self.assertEqual(len(list(r_c1_1_c2_2_d_1_c_2.on_events)), 2)
#         self.assertEqual(len(list(r_c1_1_c2_2_d_1_c_2.on_conditions)), 4)
#         self.assertEqual(len(list(r_c1_2_c2_1_d_1_c_2.on_events)), 2)
#         self.assertEqual(len(list(r_c1_2_c2_1_d_1_c_2.on_conditions)), 4)
#         self.assertEqual(len(list(r_c1_2_c2_2_d_1_c_2.on_events)), 1)
#         self.assertEqual(len(list(r_c1_2_c2_2_d_1_c_2.on_conditions)), 4)
#         self.assertEqual(len(list(r_c1_1_c2_1_d_2_c_2.on_events)), 2)
#         self.assertEqual(len(list(r_c1_1_c2_1_d_2_c_2.on_conditions)), 4)
#         self.assertEqual(len(list(r_c1_1_c2_2_d_2_c_2.on_events)), 1)
#         self.assertEqual(len(list(r_c1_1_c2_2_d_2_c_2.on_conditions)), 4)
#         self.assertEqual(len(list(r_c1_2_c2_1_d_2_c_2.on_events)), 1)
#         self.assertEqual(len(list(r_c1_2_c2_1_d_2_c_2.on_conditions)), 4)
#         self.assertEqual(len(list(r_c1_2_c2_2_d_2_c_2.on_events)), 0)
#         self.assertEqual(len(list(r_c1_2_c2_2_d_2_c_2.on_conditions)), 4)
# 
# # All on_events return to thier same transition:
#         for r in a_flat.regimes:
#             for on_ev in r.on_events:
#                 self.assertEquals(on_ev.target_regime, r)
# 
#         # Check On-Event port names are remapped properly:
#         self.assertEqual(set([ev.src_port_name
#                               for ev in r_c1_1_c2_1_d_1_c_1.on_events]),
#                          set(['c_spikein', 'b_c1_spikein', 'b_c2_spikein',
#                               'b_d_spikein']))
#         self.assertEqual(set([ev.src_port_name
#                               for ev in r_c1_1_c2_2_d_1_c_1.on_events]),
#                          set(['c_spikein', 'b_c1_spikein', 'b_d_spikein']))
#         self.assertEqual(set([ev.src_port_name
#                               for ev in r_c1_2_c2_1_d_1_c_1.on_events]),
#                          set(['c_spikein', 'b_c2_spikein', 'b_d_spikein']))
#         self.assertEqual(
#             set([ev.src_port_name for ev in r_c1_2_c2_2_d_1_c_1.on_events]),
#             set(['c_spikein', 'b_d_spikein']))
#         self.assertEqual(set([ev.src_port_name
#                               for ev in r_c1_1_c2_1_d_2_c_1.on_events]),
#                          set(['c_spikein', 'b_c1_spikein', 'b_c2_spikein']))
#         self.assertEqual(
#             set([ev.src_port_name for ev in r_c1_1_c2_2_d_2_c_1.on_events]),
#             set(['c_spikein', 'b_c1_spikein', ]))
#         self.assertEqual(
#             set([ev.src_port_name for ev in r_c1_2_c2_1_d_2_c_1.on_events]),
#             set(['c_spikein', 'b_c2_spikein', ]))
#         self.assertEqual(
#             set([ev.src_port_name for ev in r_c1_2_c2_2_d_2_c_1.on_events]),
#             set(['c_spikein']))
# 
#         self.assertEqual(set([ev.src_port_name
#                               for ev in r_c1_1_c2_1_d_1_c_2.on_events]),
#                          set(['b_c1_spikein', 'b_c2_spikein', 'b_d_spikein']))
#         self.assertEqual(
#             set([ev.src_port_name for ev in r_c1_1_c2_2_d_1_c_2.on_events]),
#             set(['b_c1_spikein', 'b_d_spikein']))
#         self.assertEqual(
#             set([ev.src_port_name for ev in r_c1_2_c2_1_d_1_c_2.on_events]),
#             set(['b_c2_spikein', 'b_d_spikein']))
#         self.assertEqual(
#             set([ev.src_port_name for ev in r_c1_2_c2_2_d_1_c_2.on_events]),
#             set(['b_d_spikein']))
#         self.assertEqual(
#             set([ev.src_port_name for ev in r_c1_1_c2_1_d_2_c_2.on_events]),
#             set(['b_c1_spikein', 'b_c2_spikein']))
#         self.assertEqual(
#             set([ev.src_port_name for ev in r_c1_1_c2_2_d_2_c_2.on_events]),
#             set(['b_c1_spikein', ]))
#         self.assertEqual(
#             set([ev.src_port_name for ev in r_c1_2_c2_1_d_2_c_2.on_events]),
#             set(['b_c2_spikein', ]))
#         self.assertEqual(set([ev.src_port_name
#                               for ev in r_c1_2_c2_2_d_2_c_2.on_events]),
#                          set([]))
# 
#         # ToDo: Check the OnConditions:
# 
#         #  - Ports & Parameters:
#         self.assertEqual(
#             set(a_flat.analog_port_names),
#             set(['b_c1_cIn1', 'b_c1_cIn2', 'b_c1_C1', 'b_c1_C2',
#                  'b_c2_cIn1', 'b_c2_cIn2', 'b_c2_C1', 'b_c2_C2',
#                  'b_d_dIn1', 'b_d_dIn2', 'b_d_D1', 'b_d_D2',
#                  'c_cIn1', 'c_cIn2', 'c_C1', 'c_C2']))
# 
#         self.assertEqual(
#             set(a_flat.event_port_names),
#             set(['b_c1_spikein', 'b_c1_emit', 'b_c1_c_emit',
#                  'b_c2_spikein', 'b_c2_emit', 'b_c2_c_emit',
#                  'b_d_spikein', 'b_d_emit', 'b_d_d_emit',
#                  'c_spikein', 'c_emit', 'c_c_emit', ]))
# 
#         self.assertEqual(
#             set(a_flat.parameter_names),
#             set(['c_cp1', 'c_cp2',
#                  'b_c1_cp1', 'b_c1_cp2',
#                  'b_c2_cp1', 'b_c2_cp2',
#                  'b_d_dp1', 'b_d_dp2', ]))
# 
#         self.assertEqual(
#             set(a_flat.state_variable_names),
#             set(['b_c1_SV1', 'b_c2_SV1', 'b_d_SV1', 'c_SV1']))
# 
#     def test_Flattening4(self):
# 
#         c = Dynamics(
#             name='C',
#             aliases=['C1:=cp1', 'C2 := cIn1', 'C3 := SV1', 'C4:=cIn2'],
#             regimes=[
#                 Regime(
#                     'dSV1/dt = -SV1/(cp2*t)',
#                     transitions=[On('SV1>cp1', do=[OutputEvent('emit')]),
#                                  On('spikein', do=[OutputEvent('c_emit')])],
#                     name='r1',
#                 ),
#                 Regime(name='r2', transitions=On('SV1>1', to='r1'))
#             ],
#             analog_ports=[AnalogReceivePort('cIn1'), AnalogReceivePort('cIn2'),
#                           AnalogSendPort('C1'), AnalogSendPort('C2')],
#             parameters=['cp1', 'cp2']
#         )
# 
#         d = Dynamics(
#             name='D',
#             aliases=['D1:=dp1', 'D2 := dIn1 + dp2', 'D3 := SV1'],
#             regimes=[
#                 Regime(
#                     'dSV1/dt = -SV1/(dp2*t)',
#                     transitions=[On('SV1>dp1', do=[OutputEvent('emit')]),
#                                  On('spikein', do=[OutputEvent('d_emit')])],
#                     name='r1',
#                 ),
#                 Regime(name='r2', transitions=On('SV1>1', to='r1'))
#             ],
#             analog_ports=[AnalogReceivePort('dIn1'), AnalogReceivePort('dIn2'),
#                           AnalogSendPort('D1'), AnalogSendPort('D2')],
#             parameters=['dp1', 'dp2']
#         )
# 
#         # Test Cloner, 2 levels of hierachy
#         # ------------------------------ #
# 
#         # Everything should be as before:
#         b = MultiDynamics(
#             name='B',
#             sub_components={'c1': c, 'c2': c, 'd': d},
#             port_connections=[('c1', 'C1', 'c2', 'cIn2'),
#                               ('c2', 'C1', 'c1', 'cIn1')])
# 
#         a = MultiDynamics(
#             name='A',
#             sub_components={'b': b, 'c': c},
#             port_connections=[('b', 'c1', 'C1', 'b', 'c1', 'cIn2'),
#                               ('b', 'c1', 'C1', 'b', 'c2', 'cIn1'),
#                               ('b', 'c1', 'C2', 'b', 'd', 'dIn1')])
# 
#         a_flat = a.flatten()
# 
#         # Name
#         self.assertEqual(a_flat.name, 'A')
# 
#         # Aliases
#         self.assertEqual(
#             set(a_flat.alias_names),
#             set(['b_c1_C1', 'b_c1_C2', 'b_c1_C3', 'b_c1_C4',
#                  'b_c2_C1', 'b_c2_C2', 'b_c2_C3', 'b_c2_C4',
#                  'b_d_D1', 'b_d_D2', 'b_d_D3',
#                  'c_C1', 'c_C2', 'c_C3', 'c_C4']))
# 
#         # - Regimes and Transitions:
#         self.assertEqual(len(a_flat._regimes), 16)
#         r_c1_1_c2_1_d_1_c_1 = a_flat.flattener.get_new_regime('b.d:r1 b.c1:r1 b.c2:r1 c:r1')
#         r_c1_1_c2_2_d_1_c_1 = a_flat.flattener.get_new_regime('b.d:r1 b.c1:r1 b.c2:r2 c:r1')
#         r_c1_2_c2_1_d_1_c_1 = a_flat.flattener.get_new_regime('b.d:r1 b.c1:r2 b.c2:r1 c:r1')
#         r_c1_2_c2_2_d_1_c_1 = a_flat.flattener.get_new_regime('b.d:r1 b.c1:r2 b.c2:r2 c:r1')
#         r_c1_1_c2_1_d_2_c_1 = a_flat.flattener.get_new_regime('b.d:r2 b.c1:r1 b.c2:r1 c:r1')
#         r_c1_1_c2_2_d_2_c_1 = a_flat.flattener.get_new_regime('b.d:r2 b.c1:r1 b.c2:r2 c:r1')
#         r_c1_2_c2_1_d_2_c_1 = a_flat.flattener.get_new_regime('b.d:r2 b.c1:r2 b.c2:r1 c:r1')
#         r_c1_2_c2_2_d_2_c_1 = a_flat.flattener.get_new_regime('b.d:r2 b.c1:r2 b.c2:r2 c:r1')
#         r_c1_1_c2_1_d_1_c_2 = a_flat.flattener.get_new_regime('b.d:r1 b.c1:r1 b.c2:r1 c:r2')
#         r_c1_1_c2_2_d_1_c_2 = a_flat.flattener.get_new_regime('b.d:r1 b.c1:r1 b.c2:r2 c:r2')
#         r_c1_2_c2_1_d_1_c_2 = a_flat.flattener.get_new_regime('b.d:r1 b.c1:r2 b.c2:r1 c:r2')
#         r_c1_2_c2_2_d_1_c_2 = a_flat.flattener.get_new_regime('b.d:r1 b.c1:r2 b.c2:r2 c:r2')
#         r_c1_1_c2_1_d_2_c_2 = a_flat.flattener.get_new_regime('b.d:r2 b.c1:r1 b.c2:r1 c:r2')
#         r_c1_1_c2_2_d_2_c_2 = a_flat.flattener.get_new_regime('b.d:r2 b.c1:r1 b.c2:r2 c:r2')
#         r_c1_2_c2_1_d_2_c_2 = a_flat.flattener.get_new_regime('b.d:r2 b.c1:r2 b.c2:r1 c:r2')
#         r_c1_2_c2_2_d_2_c_2 = a_flat.flattener.get_new_regime('b.d:r2 b.c1:r2 b.c2:r2 c:r2')
# 
#         regimes = [
#             r_c1_1_c2_1_d_1_c_1,
#             r_c1_1_c2_2_d_1_c_1,
#             r_c1_2_c2_1_d_1_c_1,
#             r_c1_2_c2_2_d_1_c_1,
#             r_c1_1_c2_1_d_2_c_1,
#             r_c1_1_c2_2_d_2_c_1,
#             r_c1_2_c2_1_d_2_c_1,
#             r_c1_2_c2_2_d_2_c_1,
#             r_c1_1_c2_1_d_1_c_2,
#             r_c1_1_c2_2_d_1_c_2,
#             r_c1_2_c2_1_d_1_c_2,
#             r_c1_2_c2_2_d_1_c_2,
#             r_c1_1_c2_1_d_2_c_2,
#             r_c1_1_c2_2_d_2_c_2,
#             r_c1_2_c2_1_d_2_c_2,
#             r_c1_2_c2_2_d_2_c_2]
#         self.assertEqual(len(set(regimes)), 16)
# 
#         # Do we have the right number of on_events and on_conditions:
#         self.assertEqual(len(list(r_c1_1_c2_1_d_1_c_1.on_events)), 4)
#         self.assertEqual(len(list(r_c1_1_c2_1_d_1_c_1.on_conditions)), 4)
#         self.assertEqual(len(list(r_c1_1_c2_2_d_1_c_1.on_events)), 3)
#         self.assertEqual(len(list(r_c1_1_c2_2_d_1_c_1.on_conditions)), 4)
#         self.assertEqual(len(list(r_c1_2_c2_1_d_1_c_1.on_events)), 3)
#         self.assertEqual(len(list(r_c1_2_c2_1_d_1_c_1.on_conditions)), 4)
#         self.assertEqual(len(list(r_c1_2_c2_2_d_1_c_1.on_events)), 2)
#         self.assertEqual(len(list(r_c1_2_c2_2_d_1_c_1.on_conditions)), 4)
#         self.assertEqual(len(list(r_c1_1_c2_1_d_2_c_1.on_events)), 3)
#         self.assertEqual(len(list(r_c1_1_c2_1_d_2_c_1.on_conditions)), 4)
#         self.assertEqual(len(list(r_c1_1_c2_2_d_2_c_1.on_events)), 2)
#         self.assertEqual(len(list(r_c1_1_c2_2_d_2_c_1.on_conditions)), 4)
#         self.assertEqual(len(list(r_c1_2_c2_1_d_2_c_1.on_events)), 2)
#         self.assertEqual(len(list(r_c1_2_c2_1_d_2_c_1.on_conditions)), 4)
#         self.assertEqual(len(list(r_c1_2_c2_2_d_2_c_1.on_events)), 1)
#         self.assertEqual(len(list(r_c1_2_c2_2_d_2_c_1.on_conditions)), 4)
# 
#         self.assertEqual(len(list(r_c1_1_c2_1_d_1_c_2.on_events)), 3)
#         self.assertEqual(len(list(r_c1_1_c2_1_d_1_c_2.on_conditions)), 4)
#         self.assertEqual(len(list(r_c1_1_c2_2_d_1_c_2.on_events)), 2)
#         self.assertEqual(len(list(r_c1_1_c2_2_d_1_c_2.on_conditions)), 4)
#         self.assertEqual(len(list(r_c1_2_c2_1_d_1_c_2.on_events)), 2)
#         self.assertEqual(len(list(r_c1_2_c2_1_d_1_c_2.on_conditions)), 4)
#         self.assertEqual(len(list(r_c1_2_c2_2_d_1_c_2.on_events)), 1)
#         self.assertEqual(len(list(r_c1_2_c2_2_d_1_c_2.on_conditions)), 4)
#         self.assertEqual(len(list(r_c1_1_c2_1_d_2_c_2.on_events)), 2)
#         self.assertEqual(len(list(r_c1_1_c2_1_d_2_c_2.on_conditions)), 4)
#         self.assertEqual(len(list(r_c1_1_c2_2_d_2_c_2.on_events)), 1)
#         self.assertEqual(len(list(r_c1_1_c2_2_d_2_c_2.on_conditions)), 4)
#         self.assertEqual(len(list(r_c1_2_c2_1_d_2_c_2.on_events)), 1)
#         self.assertEqual(len(list(r_c1_2_c2_1_d_2_c_2.on_conditions)), 4)
#         self.assertEqual(len(list(r_c1_2_c2_2_d_2_c_2.on_events)), 0)
#         self.assertEqual(len(list(r_c1_2_c2_2_d_2_c_2.on_conditions)), 4)
# 
# # All on_events return to thier same transition:
#         for r in a_flat.regimes:
#             for on_ev in r.on_events:
#                 self.assertEquals(on_ev.target_regime, r)
# 
#         # Check On-Event port names are remapped properly:
#         self.assertEqual(set([ev.src_port_name
#                               for ev in r_c1_1_c2_1_d_1_c_1.on_events]), set(
#             ['c_spikein', 'b_c1_spikein', 'b_c2_spikein', 'b_d_spikein']))
#         self.assertEqual(set([ev.src_port_name
#                               for ev in r_c1_1_c2_2_d_1_c_1.on_events]), set(
#             ['c_spikein', 'b_c1_spikein', 'b_d_spikein']))
#         self.assertEqual(set([ev.src_port_name
#                               for ev in r_c1_2_c2_1_d_1_c_1.on_events]), set(
#             ['c_spikein', 'b_c2_spikein', 'b_d_spikein']))
#         self.assertEqual(
#             set([ev.src_port_name for ev in r_c1_2_c2_2_d_1_c_1.on_events]),
#             set(['c_spikein', 'b_d_spikein']))
#         self.assertEqual(set([ev.src_port_name
#                               for ev in r_c1_1_c2_1_d_2_c_1.on_events]), set(
#             ['c_spikein', 'b_c1_spikein', 'b_c2_spikein']))
#         self.assertEqual(
#             set([ev.src_port_name for ev in r_c1_1_c2_2_d_2_c_1.on_events]),
#             set(['c_spikein', 'b_c1_spikein', ]))
#         self.assertEqual(
#             set([ev.src_port_name for ev in r_c1_2_c2_1_d_2_c_1.on_events]),
#             set(['c_spikein', 'b_c2_spikein', ]))
#         self.assertEqual(
#             set([ev.src_port_name for ev in r_c1_2_c2_2_d_2_c_1.on_events]),
#             set(['c_spikein']))
# 
#         self.assertEqual(set([ev.src_port_name
#                               for ev in r_c1_1_c2_1_d_1_c_2.on_events]),
#                          set(['b_c1_spikein', 'b_c2_spikein', 'b_d_spikein']))
#         self.assertEqual(
#             set([ev.src_port_name for ev in r_c1_1_c2_2_d_1_c_2.on_events]),
#             set(['b_c1_spikein', 'b_d_spikein']))
#         self.assertEqual(
#             set([ev.src_port_name for ev in r_c1_2_c2_1_d_1_c_2.on_events]),
#             set(['b_c2_spikein', 'b_d_spikein']))
#         self.assertEqual(
#             set([ev.src_port_name for ev in r_c1_2_c2_2_d_1_c_2.on_events]),
#             set(['b_d_spikein']))
#         self.assertEqual(
#             set([ev.src_port_name for ev in r_c1_1_c2_1_d_2_c_2.on_events]),
#             set(['b_c1_spikein', 'b_c2_spikein']))
#         self.assertEqual(
#             set([ev.src_port_name for ev in r_c1_1_c2_2_d_2_c_2.on_events]),
#             set(['b_c1_spikein', ]))
#         self.assertEqual(
#             set([ev.src_port_name for ev in r_c1_2_c2_1_d_2_c_2.on_events]),
#             set(['b_c2_spikein', ]))
#         self.assertEqual(set([ev.src_port_name
#                               for ev in r_c1_2_c2_2_d_2_c_2.on_events]),
#                          set([]))
# 
#         # ToDo: Check the OnConditions:
# 
#         #  - Ports & Parameters:
#         self.assertEqual(
#             set(a_flat.analog_port_names),
#             set(['b_c1_C1', 'b_c1_C2',
#                  'b_c2_C1', 'b_c2_C2',
#                  'b_d_dIn2', 'b_d_D1', 'b_d_D2',
#                  'c_cIn1', 'c_cIn2', 'c_C1', 'c_C2']))
# 
#         self.assertEqual(
#             set(a_flat.event_port_names),
#             set(['b_c1_spikein', 'b_c1_emit', 'b_c1_c_emit',
#                  'b_c2_spikein', 'b_c2_emit', 'b_c2_c_emit',
#                  'b_d_spikein', 'b_d_emit', 'b_d_d_emit',
#                  'c_spikein', 'c_emit', 'c_c_emit', ]))
# 
#         self.assertEqual(
#             set(a_flat.parameter_names),
#             set(['c_cp1', 'c_cp2',
#                  'b_c1_cp1', 'b_c1_cp2',
#                  'b_c2_cp1', 'b_c2_cp2',
#                  'b_d_dp1', 'b_d_dp2', ]))
# 
#         self.assertEqual(
#             set(a_flat.state_variable_names),
#             set(['b_c1_SV1', 'b_c2_SV1', 'b_d_SV1', 'c_SV1']))
# 
#         # Back-sub everything - then do we get the correct port mappings:
#         a_flat.backsub_all()
# 
#         self.assertEqual(
#             set(a_flat.alias('b_c2_C4').rhs_atoms),
#             set(['b_c1_cp1']))
# 
#         self.assertEqual(
#             set(a_flat.alias('b_c1_C2').rhs_atoms),
#             set(['b_c2_cp1']))
# 
#         self.assertEqual(
#             set(a_flat.alias('b_c1_C4').rhs_atoms),
#             set(['b_c1_cp1']))
# 
#         self.assertEqual(
#             set(a_flat.alias('b_c2_C2').rhs_atoms),
#             set(['b_c1_cp1']))
# 
#         self.assertEqual(
#             set(a_flat.alias('b_d_D2').rhs_atoms),
#             set(['b_c2_cp1', 'b_d_dp2']))








    # These are done in the Testflatten and ComponentFlattener_test
    # Classes instead.
    # def test_flattener(self):
    # def test_is_flat(self):
    # def test_set_flattener(self):
    # def test_was_flattened(self):
    # Hierachical
#     def test_get_node_addr(self):
#         # Signature: name(self)
#                 # Get the namespace address of this component
# 
#         d = Dynamics(name='D',)
#         e = Dynamics(name='E')
#         f = Dynamics(name='F')
#         g = Dynamics(name='G')
#         b = Dynamics(name='B', sub_components={'d': d, 'e': e})
#         c = Dynamics(name='C', sub_components={'f': f, 'g': g})
#         a = Dynamics(name='A', sub_components={'b': b, 'c': c})
# 
#         # Construction of the objects causes cloning to happen:
#         # Therefore we test by looking up and checking that there
#         # are the correct component names:
#         bNew = a.get_subnode('b')
#         cNew = a.get_subnode('c')
#         dNew = a.get_subnode('b.d')
#         eNew = a.get_subnode('b.e')
#         fNew = a.get_subnode('c.f')
#         gNew = a.get_subnode('c.g')
# 
#         self.assertEquals(a.get_node_addr(),
#                           NamespaceAddress.create_root())
#         self.assertEquals(bNew.get_node_addr(),
#                           NamespaceAddress('b'))
#         self.assertEquals(cNew.get_node_addr(),
#                           NamespaceAddress('c'))
#         self.assertEquals(dNew.get_node_addr(),
#                           NamespaceAddress('b.d'))
#         self.assertEquals(eNew.get_node_addr(),
#                           NamespaceAddress('b.e'))
#         self.assertEquals(fNew.get_node_addr(),
#                           NamespaceAddress('c.f'))
#         self.assertEquals(gNew.get_node_addr(),
#                           NamespaceAddress('c.g'))
# 
#         self.assertEquals(a.name, 'A')
#         self.assertEquals(bNew.name, 'B')
#         self.assertEquals(cNew.name, 'C')
#         self.assertEquals(dNew.name, 'D')
#         self.assertEquals(eNew.name, 'E')
#         self.assertEquals(fNew.name, 'F')
#         self.assertEquals(gNew.name, 'G')

#     def test_insert_subnode(self):
#         """
#         Signature: name(self, subnode, namespace)
#         Insert a subnode into this component
# 
# 
#         :param subnode: An object of type ``Dynamics``.
#         :param namespace: A `string` specifying the name of the component in
#             this components namespace.
# 
#         :raises: ``NineMLRuntimeException`` if there is already a subcomponent
#             at the same namespace location
# 
#         .. note::
# 
#         This method will clone the subnode.
#         """
# 
#         d = Dynamics(name='D')
#         e = Dynamics(name='E')
#         f = Dynamics(name='F')
#         g = Dynamics(name='G')
# 
#         b = Dynamics(name='B')
#         b.insert_subnode(namespace='d', subnode=d)
#         b.insert_subnode(namespace='e', subnode=e)
# 
#         c = Dynamics(name='C')
#         c.insert_subnode(namespace='f', subnode=f)
#         c.insert_subnode(namespace='g', subnode=g)
# 
#         a = Dynamics(name='A')
#         a.insert_subnode(namespace='b', subnode=b)
#         a.insert_subnode(namespace='c', subnode=c)
# 
#         # Construction of the objects causes cloning to happen:
#         # Therefore we test by looking up and checking that there
#         # are the correct component names:
#         bNew = a.get_subnode('b')
#         cNew = a.get_subnode('c')
#         dNew = a.get_subnode('b.d')
#         eNew = a.get_subnode('b.e')
#         fNew = a.get_subnode('c.f')
#         gNew = a.get_subnode('c.g')
# 
# #         self.assertEquals(a.get_node_addr(),
# #                           NamespaceAddress.create_root())
# #         self.assertEquals(bNew.get_node_addr(),
# #                           NamespaceAddress('b'))
# #         self.assertEquals(cNew.get_node_addr(),
# #                           NamespaceAddress('c'))
# #         self.assertEquals(dNew.get_node_addr(),
# #                           NamespaceAddress('b.d'))
# #         self.assertEquals(eNew.get_node_addr(),
# #                           NamespaceAddress('b.e'))
# #         self.assertEquals(fNew.get_node_addr(),
# #                           NamespaceAddress('c.f'))
# #         self.assertEquals(gNew.get_node_addr(),
# #                           NamespaceAddress('c.g'))
# 
#         self.assertEquals(a.name, 'A')
#         self.assertEquals(bNew.name, 'B')
#         self.assertEquals(cNew.name, 'C')
#         self.assertEquals(dNew.name, 'D')
#         self.assertEquals(eNew.name, 'E')
#         self.assertEquals(fNew.name, 'F')
#         self.assertEquals(gNew.name, 'G')
# 
#         self.assertRaises(NineMLRuntimeError, a.get_subnode, 'x')
#         self.assertRaises(NineMLRuntimeError, a.get_subnode, 'a.')
#         self.assertRaises(NineMLRuntimeError, a.get_subnode, 'a.X')
#         self.assertRaises(NineMLRuntimeError, a.get_subnode, 'a.b.')
#         self.assertRaises(NineMLRuntimeError, a.get_subnode, 'a.b.X')
# 
#         # Adding to the same namespace twice:
#         d1 = Dynamics(name='D1')
#         d2 = Dynamics(name='D2')
#         a = Dynamics(name='B')
# 
#         a.insert_subnode(namespace='d', subnode=d1)
#         self.assertRaises(
#             NineMLRuntimeError,
#             a.insert_subnode, namespace='d', subnode=d2)




#     def test_connect_ports(self):
#         # Signature: name(self, src, sink)
#                 # Connects the ports of 2 sub_components.
#                 #
#                 # The ports can be specified as ``string`` s or ``NamespaceAddresses`` es.
#                 #
#                 #
#                 # :param src: The source port of one sub-component; this should either an
#                 #     event port or analog port, but it *must* be a send port.
#                 #
#                 # :param sink: The sink port of one sub-component; this should either an
#                 #     event port or analog port, but it *must* be either a 'recv' or a
#                 #     'reduce' port.
# 
#         tIaf = TestableComponent('iaf')
#         tCoba = TestableComponent('coba_synapse')
# 
#         # Should be fine:
#         c = MultiDynamics(name='C1',
#                           sub_components={'iaf': tIaf(), 'coba': tCoba()},
#                           port_connections=[('iaf', 'V', 'coba', 'V')])
# 
#         c = MultiDynamics(name='C1',
#                           sub_components={'iaf': tIaf(), 'coba': tCoba()},
#                           port_connections=[('iaf', 'V', 'coba', 'V')])
# 
#         # Non existant Ports:
#         c = MultiDynamics(name='C1',
#                           sub_components={'iaf': tIaf(), 'coba': tCoba()})
#         self.assertRaises(
#             NineMLRuntimeError,
#             c.connect_ports, 'iaf', 'V1', 'coba', 'V')
#         self.assertRaises(
#             NineMLRuntimeError,
#             c.connect_ports, 'iaf', 'V', 'coba', 'V1')
# 
#         self.assertRaises(
#             NineMLRuntimeError,
#             MultiDynamics,
#             name='C1',
#             sub_components={'iaf': tIaf(), 'coba': tCoba()},
#             port_connections=[('iaf', 'V1', 'coba', 'V')])
# 
#         self.assertRaises(
#             NineMLRuntimeError,
#             MultiDynamics,
#             name='C1',
#             sub_components={'iaf': tIaf(), 'coba': tCoba()},
#             port_connections=[('iaf', 'V', 'coba', 'V1')])
# 
#         # Connect ports the wrong way around:
#         # [Check the wright way around works:]
#         c = MultiDynamics(name='C1',
#                           sub_components={'iaf': tIaf(), 'coba': tCoba()},
#                           port_connections=[('coba', 'I', 'iaf', 'ISyn')])
#         # And the wrong way around:
#         self.assertRaises(
#             NineMLRuntimeError,
#             MultiDynamics,
#             name='C1',
#             sub_components={'iaf': tIaf(), 'coba': tCoba()},
#             port_connections=[('iaf', 'ISyn', 'coba', 'I')])
#         self.assertRaises(
#             NineMLRuntimeError,
#             MultiDynamics,
#             name='C1',
#             sub_components={'iaf': tIaf(), 'coba': tCoba()},
#             port_connections=[('coba', 'V', 'iaf', 'V')])
# 
#         # Error raised on duplicate port-connection:
#         c = MultiDynamics(name='C1',
#                            sub_components={'iaf': tIaf(), 'coba': tCoba()},
#                            )
# 
#         c.connect_ports('coba', 'I', 'iaf', 'ISyn')
#         self.assertRaises(
#             NineMLRuntimeError,
#             c.connect_ports, 'coba', 'I', 'iaf', 'ISyn')






#     def test_get_fully_qualified_port_connections(self):
#         # Signature: name(self)
#                 # Used by the flattening code.
#                 #
#                 # This method returns a d list of tuples of the
#                 # the fully-qualified port connections
#         # from nineml.abstraction.component.componentqueryer import
#         # ComponentClassQueryer
# 
#         # Signature: name(self)
#                 # Get the namespace address of this component
#         d = Dynamics(
#             name='D', aliases=['A:=1', 'B:=2'],
#             analog_ports=[AnalogSendPort('A'), AnalogSendPort('B')])
#         e = Dynamics(name='E', analog_ports=[AnalogReceivePort('C')])
#         f = Dynamics(name='F', analog_ports=[AnalogReceivePort('D')])
#         g = Dynamics(name='G', analog_ports=[AnalogReceivePort('E')])
#         b = Dynamics(name='B', sub_components={'d': d, 'e': e},
#                      port_connections=[('d', 'A', 'e', 'C')])
#         c = Dynamics(name='C',
#                            aliases=['G:=-1'],
#                            analog_ports=[AnalogSendPort('G')],
#                            sub_components={'f': f, 'g': g},
#                            port_connections=[('G', 'f.D')])
# 
#         a = Dynamics(name='A',
#                            sub_components={'b': b, 'c': c},
#                            analog_ports=[AnalogReceivePort('F')],
#                            port_connections=[('b.d.A', 'F')]
#                            )
# 
#         bNew = a.get_subnode('b')
#         cNew = a.get_subnode('c')
#         # dNew = a.get_subnode('b.d')
#         # eNew = a.get_subnode('b.e')
#         # fNew = a.get_subnode('c.f')
#         # gNew = a.get_subnode('c.g')
# 
#         self.assertEquals(list(a.fully_qualified_port_connections),
#                           [(NamespaceAddress('b.d.A'), NamespaceAddress('F'))])
# 
#         self.assertEquals(list(bNew.fully_qualified_port_connections),
#                           [(NamespaceAddress('b.d.A'), NamespaceAddress('b.e.C'))])
# 
#         self.assertEquals(list(cNew.fully_qualified_port_connections),
#                           [(NamespaceAddress('c.G'), NamespaceAddress('c.f.D'))])

#     def test_recurse_all_components(self):
#         # Signature: name
#                 # Returns an iterator over this component and all sub_components
# 
#         d = Dynamics(name='D')
#         e = Dynamics(name='E')
#         f = Dynamics(name='F')
#         g = Dynamics(name='G')
# 
#         b = Dynamics(name='B')
#         b.insert_subnode(namespace='d', subnode=d)
#         b.insert_subnode(namespace='e', subnode=e)
# 
#         c = Dynamics(name='C')
#         c.insert_subnode(namespace='f', subnode=f)
#         c.insert_subnode(namespace='g', subnode=g)
# 
#         a = Dynamics(name='A')
#         a.insert_subnode(namespace='b', subnode=b)
#         a.insert_subnode(namespace='c', subnode=c)
# 
#         # Construction of the objects causes cloning to happen:
#         # Therefore we test by looking up and checking that there
#         # are the correct component names:
#         bNew = a.get_subnode('b')
#         cNew = a.get_subnode('c')
#         dNew = a.get_subnode('b.d')
#         eNew = a.get_subnode('b.e')
#         fNew = a.get_subnode('c.f')
#         gNew = a.get_subnode('c.g')
# 
#         self.assertEquals(
#             set(a.all_components),
#             set([a, bNew, cNew, dNew, eNew, fNew, gNew]))
#         self.assertEquals(
#             set(bNew.all_components),
#             set([bNew, dNew, eNew]))
#         self.assertEquals(
#             set(cNew.all_components),
#             set([cNew, fNew, gNew]))
#         self.assertEquals(
#             set(dNew.all_components),
#             set([dNew]))
#         self.assertEquals(
#             set(eNew.all_components),
#             set([eNew]))
#         self.assertEquals(
#             set(fNew.all_components),
#             set([fNew]))
#         self.assertEquals(
#             set(gNew.all_components),
#             set([gNew]))

# 
# class NamespaceAddress_test(unittest.TestCase):
# 
#     def test_Constructor(self):
#         pass
# 
#     def test_concat(self):
#         # Signature: name(cls, *args)
#                 # Concatenates all the Namespace Addresses.
#                 #
#                 # This method take all the arguments supplied, converts each one into a
#                 # namespace object, then, produces a new namespace object which is the
#                 # concatentation of all the arugements namespaces.
#                 #
#                 # For example:
#                 #
#                 # >>> NamespaceAddress.concat('first.second','third.forth','fifth.sixth')
#                 #     NameSpaceAddress: '/first/second/third/forth/fifth/sixth'
#         # from nineml.abstraction.component.namespaceaddress import NamespaceAddress
#         self.assertEqual(
#             NSA.concat(NSA('a.b.c'), NSA('d.e.f'), NSA('g.h.i')),
#             NSA('a.b.c.d.e.f.g.h.i'))
#         self.assertEqual(
#             NSA.concat(NSA.create_root(), NSA('a.b.c'), NSA.create_root()),
#             NSA('a.b.c')
#         )
#         self.assertEqual(
#             NSA.concat(NSA.create_root(), NSA.create_root()),
#             NSA.create_root()
#         )
# 
#     def test_create_root(self):
#         # Signature: name(cls)
#                 # Returns a empty (root) namespace address
#                 #
#                 #
#                 # >>> nineml.abstraction.NamespaceAddress.create_root()
#                 # NameSpaceAddress: '//'
#         # from nineml.abstraction.component.namespaceaddress import NamespaceAddress
#         self.assertEqual(NSA.create_root().loctuple, ())
# 
#     def test_get_local_name(self):
#         # Signature: name(self)
#                 # Returns the local reference; i.e. the last field in the
#                 # address, as a ``string``
#         # from nineml.abstraction.component.namespaceaddress import NamespaceAddress
#         self.assertEqual(
#             NSA('a.b.c.d.e.f.g.h.i').get_local_name(),
#             'i')
#         self.assertEqual(
#             NSA('a.b.lastname').get_local_name(),
#             'lastname')
#         self.assertRaises(
#             NineMLRuntimeError,
#             NSA.create_root().get_local_name,
#         )
# 
#     def test_get_parent_addr(self):
#         # Signature: name(self)
#                 # Return the address of an namespace higher
#                 #
#                 # >>> a = NamespaceAddress('level1.level2.level3')
#                 # >>> a
#                 # NameSpaceAddress: '/level1/level2/level3/'
#                 # >>> a.get_parent_addr()
#                 # NameSpaceAddress: '/level1/level2/'
# 
#         self.assertEqual(
#             NSA('a.b.c.d.e.f.g.h.i').get_parent_addr(),
#             NSA('a.b.c.d.e.f.g.h')
#         )
# 
#         self.assertEqual(
#             NSA('a.b.lastname').get_parent_addr(),
#             NSA('a.b')
#         )
# 
#         self.assertRaises(
#             NineMLRuntimeError,
#             NSA.create_root().get_local_name,
#         )
# 
#     def test_get_subns_addr(self):
#         # Signature: name(self, component_name)
#                 # Returns the address of a subcomponent at this address.
#                 #
#                 # For example:
#                 #
#                 # >>> a = NamespaceAddress('level1.level2.level3')
#                 # >>> a.get_subns_addr('subcomponent')
#                 # NameSpaceAddress: '/level1/level2/level3/subcomponent/'
# 
#         d = Dynamics(name='D',)
#         e = Dynamics(name='E')
#         f = Dynamics(name='F')
#         g = Dynamics(name='G')
#         b = MultiDynamics(name='B', sub_components={'atD': d, 'atE': e})
#         c = MultiDynamics(name='C', sub_components={'atF': f, 'atG': g})
#         a = MultiDynamics(name='A', sub_components={'atB': b, 'atC': c})
# 
#         # Construction of the objects causes cloning to happen:
#         # Therefore we test by looking up and checking that there
#         # are the correct component names:
#         bNew = a.get_subnode('atB')
#         cNew = a.get_subnode('atC')
#         dNew = a.get_subnode('atB.atD')
#         eNew = a.get_subnode('atB.atE')
#         fNew = a.get_subnode('atC.atF')
#         gNew = a.get_subnode('atC.atG')
# 
#         self.assertEquals(
#             gNew.get_node_addr().get_subns_addr('MyObject1'),
#             NSA('atC.atG.MyObject1')
#         )
# 
#         self.assertEquals(
#             eNew.get_node_addr().get_subns_addr('MyObject2'),
#             NSA('atB.atE.MyObject2')
#         )
# 
#         self.assertEquals(
#             bNew.get_node_addr().get_subns_addr('MyObject3'),
#             NSA('atB.MyObject3')
#         )
# 
#     def test_getstr(self):
#         # Signature: name(self, join_char='_')
#                 # Returns the namespace address as a string.
#                 #
#                 # :param join_char: The character used to join the levels in the address.
#         # from nineml.abstraction.component.namespaceaddress import NamespaceAddress
# 
#         self.assertEqual(
#             NSA('a.b.c.d.e.f.g.h.i').getstr('.'),
#             'a.b.c.d.e.f.g.h.i'
#         )
# 
#         self.assertEqual(
#             NSA.concat(NSA.create_root(), NSA.create_root(), NSA(
#                        'a.b.c.d.e.f.g.h.i')).getstr('.'),
#             'a.b.c.d.e.f.g.h.i'
#         )
# 
#         self.assertEqual(
#             NSA.concat(NSA.create_root(), NSA.create_root(), NSA(
#                        'a.b.c.d.e.f.g.h.i'), NSA.create_root(),).getstr('.'),
#             'a.b.c.d.e.f.g.h.i'
#         )
# 
#         self.assertEqual(
#             NSA('a.b.c.d.e.f.g.h.i').getstr('/'),
#             'a/b/c/d/e/f/g/h/i'
#         )
# 
#     def test_get_str_prefix(self):
#         # Signature: name(self, join_char='_')
#                 # Returns the same as ``getstr``, but prepends the ``join_char`` to
#                 # the end of the string, so that the string can be used to prefix
#                 # variables.
#                 #
#                 # :param join_char: The character used to join the levels in the address.
#         # from nineml.abstraction.component.namespaceaddress import NamespaceAddress
# 
#         self.assertEqual(
#             NSA('a.b.c.d.e.f.g.h.i').get_str_prefix('.'),
#             'a.b.c.d.e.f.g.h.i.'
#         )
# 
#         self.assertEqual(
#             NSA.concat(NSA.create_root(), NSA.create_root(),
#                        NSA('a.b.c.d.e.f.g.h.i')).get_str_prefix('.'),
#             'a.b.c.d.e.f.g.h.i.'
#         )
# 
#         self.assertEqual(
#             NSA.concat(NSA.create_root(), NSA.create_root(),
#                        NSA('a.b.c.d.e.f.g.h.i'), NSA.create_root(),).get_str_prefix('.'),
#             'a.b.c.d.e.f.g.h.i.'
#         )
# 
#         self.assertEqual(
#             NSA('a.b.c.d.e.f.g.h.i').get_str_prefix('/'),
#             'a/b/c/d/e/f/g/h/i/'
#         )
