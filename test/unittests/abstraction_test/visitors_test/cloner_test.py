import unittest

from nineml.abstraction import (
    Dynamics as Dynamics, Regime, On, OutputEvent,
    AnalogSendPort as SendPort, AnalogReceivePort as RecvPort)
from nineml.user.multi.dynamics import MultiDynamics
# from nineml.abstraction.dynamics.visitors.modifiers import DynamicsFlattener


# Testing Skeleton for class: DynamicsClonerPrefixNamespace
class DynamicsClonerPrefixNamespace_test(unittest.TestCase):

    def test_Constructor(self):

        d = Dynamics(
            name='D',
            aliases=['D1:=dp1', 'D2 := dIn1', 'D3 := SV1'],
            regimes=[
                Regime('dSV1/dt = -SV1/(dp2*t)', name='r1',
                       transitions=On('input', 'SV1=SV1+1'))],
            analog_ports=[RecvPort('dIn1'), SendPort('D1'), SendPort('D2')],
            parameters=['dp1', 'dp2']
        )

        c = Dynamics(
            name='C',
            aliases=['C1:=cp1', 'C2 := cIn1', 'C3 := SV1'],
            regimes=[
                Regime(
                    'dSV1/dt = -SV1/(cp2*t)',
                    transitions=[On('SV1>cp1', do=[OutputEvent('emit')]),
                                 On('spikein', do=[OutputEvent('emit')])],
                    name='r1',
                ),
                Regime(name='r2', transitions=On('SV1>1', to='r1'))
            ],
            analog_ports=[RecvPort('cIn1'), RecvPort('cIn2'), SendPort('C1'),
                          SendPort('C2')],
            parameters=['cp1', 'cp2']
        )

        # Test Cloner, no hierachy
        # Everything should be as before:
#         c_clone = DynamicsCloner().visit(c)
        c_clone = DynamicsFlattener(c).flattened

        self.assertEqual(c_clone.name, 'C')
        self.assertEqual(set(c_clone.alias_names), set(['C1', 'C2', 'C3']))

        # - Regimes and Transitions:
        self.assertEqual(set(c_clone.regime_names), set(['r1', 'r2']))
        self.assertEqual(len(list(c_clone.regime('r1').on_events)), 1)
        self.assertEqual(len(list(c_clone.regime('r1').on_conditions)), 1)
        self.assertEqual(len(list(c_clone.regime('r2').on_events)), 0)
        self.assertEqual(len(list(c_clone.regime('r2').on_conditions)), 1)
        self.assertEqual(len(list(c_clone.regime('r2').on_conditions)), 1)

        #  - Ports & Parameters:
        self.assertEqual(
            set(c_clone.analog_port_names),
            set(['cIn2', 'cIn1', 'C1', 'C2']))
        self.assertEqual(set(c_clone.event_send_port_names),
                         set(['emit']))
        self.assertEqual(set(c_clone.event_receive_port_names),
                         set(['spikein']))
        self.assertEqual(set(c_clone.parameter_names),
                         set(['cp1', 'cp2']))
        self.assertEqual(set(c_clone.state_variable_names),
                         set(['SV1']))

        del c_clone

        # Test Cloner, 1 level of hierachy
        # Everything should be as before:
        b = MultiDynamics(name='B',
                          sub_components={'c1': c, 'c2': c},
                          port_connections=[('c1', 'C1', 'c2', 'cIn1'),
                                            ('c2', 'emit', 'c1', 'spikein')],
                          port_exposures=[('c2', 'cIn2', 'cIn2_c2'),
                                          ('c1', 'cIn1', 'cIn1_c1')])

        b_clone = DynamicsFlattener(b).flattened
#         c1_clone = b_clone.get_subnode('c1')
#         c2_clone = b_clone.get_subnode('c2')
# 
#         self.assertEqual(c1_clone.name, 'C')
#         self.assertEqual(c2_clone.name, 'C')
#         self.assertEqual(set(c1_clone.alias_names), set(['c1_C1', 'c1_C2',
#                                                          'c1_C3']))
#         self.assertEqual(set(c2_clone.alias_names), set(['c2_C1', 'c2_C2',
#                                                          'c2_C3']))
# 
#         # - Regimes and Transitions:
#         self.assertEqual(set(c1_clone.regime_names), set(['r1', 'r2']))
#         self.assertEqual(len(list(c1_clone.regime('r1').on_events)), 1)
#         self.assertEqual(len(list(c1_clone.regime('r1').on_conditions)), 1)
#         self.assertEqual(len(list(c1_clone.regime('r2').on_events)), 0)
#         self.assertEqual(len(list(c1_clone.regime('r2').on_conditions)), 1)
#         self.assertEqual(len(list(c1_clone.regime('r2').on_conditions)), 1)
# 
#         self.assertEqual(set(c2_clone.regime_names), set(['r1', 'r2']))
#         self.assertEqual(len(list(c2_clone.regime('r1').on_events)), 1)
#         self.assertEqual(len(list(c2_clone.regime('r1').on_conditions)), 1)
#         self.assertEqual(len(list(c2_clone.regime('r2').on_events)), 0)
#         self.assertEqual(len(list(c2_clone.regime('r2').on_conditions)), 1)
#         self.assertEqual(len(list(c2_clone.regime('r2').on_conditions)), 1)
# 
#         #  - Ports & Parameters:
#         self.assertEqual(
#             set(c1_clone.analog_port_names),
#             set(['c1_cIn1', 'c1_cIn2', 'c1_C1', 'c1_C2']))
#         self.assertEqual(
#             set(c2_clone.analog_port_names),
#             set(['c2_cIn1', 'c2_cIn2', 'c2_C1', 'c2_C2']))
# 
#         self.assertEqual(set(c1_clone.event_send_port_names),
#                          set(['c1_emit']))
#         self.assertEqual(set(c2_clone.event_send_port_names),
#                          set(['c2_emit']))
#         self.assertEqual(set(c1_clone.event_receive_port_names),
#                          set(['c1_spikein']))
#         self.assertEqual(set(c2_clone.event_receive_port_names),
#                          set(['c2_spikein']))
# 
#         self.assertEqual(
#             set(c1_clone.parameter_names),
#             set(['c1_cp1', 'c1_cp2']))
#         self.assertEqual(
#             set(c2_clone.parameter_names),
#             set(['c2_cp1', 'c2_cp2']))
#         self.assertEqual(
#             set(c1_clone.state_variable_names),
#             set(['c1_SV1']))
#         self.assertEqual(
#             set(c2_clone.state_variable_names),
#             set(['c2_SV1']))
# 
#         del b_clone
#         del c1_clone
#         del c2_clone
# 
#         # Two Levels of nesting:
#         a = Dynamics(name='A',
#                      subnodes={'b1': b, 'b2': b, 'c3': c},
#                      port_connections=[('b1.c1.emit', 'c3.spikein'),
#                                        ('c3.C2', 'b1.c2.cIn2')])
#         a_clone = DynamicsCloner().visit(a)
# 
#         b1_clone = a_clone.get_subnode('b1')
#         b2_clone = a_clone.get_subnode('b2')
#         b1c1_clone = a_clone.get_subnode('b1.c1')
#         b1c2_clone = a_clone.get_subnode('b1.c2')
#         b2c1_clone = a_clone.get_subnode('b2.c1')
#         b2c2_clone = a_clone.get_subnode('b2.c2')
#         c3_clone = a_clone.get_subnode('c3')
# 
#         clones = [b1_clone,
#                   b2_clone,
#                   b1c1_clone,
#                   b1c2_clone,
#                   b2c1_clone,
#                   b2c2_clone,
#                   c3_clone, ]
# 
#         # Check for duplicates:
#         self.assertEquals(len(clones), len(set(clones)))
# 
#         # Names:
#         self.assertEqual(b1_clone.name, 'B')
#         self.assertEqual(b2_clone.name, 'B')
#         self.assertEqual(b1c1_clone.name, 'C')
#         self.assertEqual(b1c2_clone.name, 'C')
#         self.assertEqual(c3_clone.name, 'C')
#         self.assertEqual(b2c1_clone.name, 'C')
#         self.assertEqual(b2c2_clone.name, 'C')
# 
#         # Aliases:
#         self.assertEqual(set(b1_clone.alias_names), set([]))
#         self.assertEqual(set(b2_clone.alias_names), set([]))
#         self.assertEqual(set(b1c1_clone.alias_names), set(
#             ['b1_c1_C1', 'b1_c1_C2', 'b1_c1_C3']))
#         self.assertEqual(set(b1c2_clone.alias_names), set(
#             ['b1_c2_C1', 'b1_c2_C2', 'b1_c2_C3']))
#         self.assertEqual(set(b2c1_clone.alias_names), set(
#             ['b2_c1_C1', 'b2_c1_C2', 'b2_c1_C3']))
#         self.assertEqual(set(b2c2_clone.alias_names), set(
#             ['b2_c2_C1', 'b2_c2_C2', 'b2_c2_C3']))
#         self.assertEqual(set(c3_clone.alias_names), set(['c3_C1', 'c3_C2',
#                                                          'c3_C3']))
# 
#         # Regimes:
#         self.assertEqual(set(b1_clone.regime_names), set([]))
#         self.assertEqual(set(b2_clone.regime_names), set([]))
#         self.assertEqual(set(b1c1_clone.regime_names), set(['r1', 'r2']))
#         self.assertEqual(set(b1c2_clone.regime_names), set(['r1', 'r2']))
#         self.assertEqual(set(b2c1_clone.regime_names), set(['r1', 'r2']))
#         self.assertEqual(set(b2c2_clone.regime_names), set(['r1', 'r2']))
#         self.assertEqual(set(c3_clone.regime_names), set(['r1', 'r2']))
# 
#         self.assertEqual(len(list(b1c1_clone.regime('r1').on_events)), 1)
#         self.assertEqual(len(list(b1c1_clone.regime('r1').on_conditions)), 1)
#         self.assertEqual(len(list(b1c1_clone.regime('r2').on_events)), 0)
#         self.assertEqual(len(list(b1c1_clone.regime('r2').on_conditions)), 1)
#         self.assertEqual(len(list(b1c1_clone.regime('r2').on_conditions)), 1)
# 
#         self.assertEqual(len(list(b1c2_clone.regime('r1').on_events)), 1)
#         self.assertEqual(len(list(b1c2_clone.regime('r1').on_conditions)), 1)
#         self.assertEqual(len(list(b1c2_clone.regime('r2').on_events)), 0)
#         self.assertEqual(len(list(b1c2_clone.regime('r2').on_conditions)), 1)
#         self.assertEqual(len(list(b1c2_clone.regime('r2').on_conditions)), 1)
# 
#         self.assertEqual(len(list(b2c1_clone.regime('r1').on_events)), 1)
#         self.assertEqual(len(list(b2c1_clone.regime('r1').on_conditions)), 1)
#         self.assertEqual(len(list(b2c1_clone.regime('r2').on_events)), 0)
#         self.assertEqual(len(list(b2c1_clone.regime('r2').on_conditions)), 1)
#         self.assertEqual(len(list(b2c1_clone.regime('r2').on_conditions)), 1)
# 
#         self.assertEqual(len(list(b2c2_clone.regime('r1').on_events)), 1)
#         self.assertEqual(len(list(b2c2_clone.regime('r1').on_conditions)), 1)
#         self.assertEqual(len(list(b2c2_clone.regime('r2').on_events)), 0)
#         self.assertEqual(len(list(b2c2_clone.regime('r2').on_conditions)), 1)
#         self.assertEqual(len(list(b2c2_clone.regime('r2').on_conditions)), 1)
# 
#         self.assertEqual(len(list(c3_clone.regime('r1').on_events)), 1)
#         self.assertEqual(len(list(c3_clone.regime('r1').on_conditions)), 1)
#         self.assertEqual(len(list(c3_clone.regime('r2').on_events)), 0)
#         self.assertEqual(len(list(c3_clone.regime('r2').on_conditions)), 1)
#         self.assertEqual(len(list(c3_clone.regime('r2').on_conditions)), 1)
# 
#         # Ports, params and state-vars:
#         # c1:
#         self.assertEqual(set(b1c1_clone.analog_port_names), set(
#             ['b1_c1_cIn1', 'b1_c1_cIn2', 'b1_c1_C1', 'b1_c1_C2']))
#         self.assertEqual(
#             set(b1c1_clone.event_port_names),
#             set(['b1_c1_spikein', 'b1_c1_emit']))
#         self.assertEqual(
#             set(b1c1_clone.parameter_names), set(['b1_c1_cp1', 'b1_c1_cp2']))
#         self.assertEqual(set(b1c1_clone.state_variable_names),
#                          set(['b1_c1_SV1']))
# 
#         self.assertEqual(set(b1c2_clone.analog_port_names), set(
#             ['b1_c2_cIn1', 'b1_c2_cIn2', 'b1_c2_C1', 'b1_c2_C2']))
#         self.assertEqual(
#             set(b1c2_clone.event_port_names),
#             set(['b1_c2_spikein', 'b1_c2_emit']))
#         self.assertEqual(
#             set(b1c2_clone.parameter_names), set(['b1_c2_cp1', 'b1_c2_cp2']))
#         self.assertEqual(set(b1c2_clone.state_variable_names),
#                          set(['b1_c2_SV1']))
# 
#         self.assertEqual(set(b2c1_clone.analog_port_names),
#                          set(['b2_c1_cIn1', 'b2_c1_cIn2',
#                               'b2_c1_C1', 'b2_c1_C2']))
#         self.assertEqual(
#             set(b2c1_clone.event_port_names),
#             set(['b2_c1_spikein', 'b2_c1_emit']))
#         self.assertEqual(
#             set(b2c1_clone.parameter_names), set(['b2_c1_cp1', 'b2_c1_cp2']))
#         self.assertEqual(set(b2c1_clone.state_variable_names),
#                          set(['b2_c1_SV1']))
# 
#         self.assertEqual(set(b2c2_clone.analog_port_names), set(
#             ['b2_c2_cIn1', 'b2_c2_cIn2', 'b2_c2_C1', 'b2_c2_C2']))
#         self.assertEqual(
#             set(b2c2_clone.event_port_names),
#             set(['b2_c2_spikein', 'b2_c2_emit']))
#         self.assertEqual(
#             set(b2c2_clone.parameter_names), set(['b2_c2_cp1', 'b2_c2_cp2']))
#         self.assertEqual(set(b2c2_clone.state_variable_names),
#                          set(['b2_c2_SV1']))
# 
#         self.assertEqual(set(c3_clone.analog_port_names), set(
#             ['c3_cIn1', 'c3_cIn2', 'c3_C1', 'c3_C2']))
#         self.assertEqual(
#             set(c3_clone.event_port_names),
#             set(['c3_spikein', 'c3_emit']))
#         self.assertEqual(
#             set(c3_clone.parameter_names),
#             set(['c3_cp1', 'c3_cp2']))
#         self.assertEqual(set(c3_clone.state_variable_names), set(['c3_SV1']))
# 
#         self.assertEqual(set(b1_clone.analog_port_names), set([]))
#         self.assertEqual(set(b1_clone.event_port_names), set([]))
#         self.assertEqual(set(b1_clone.parameter_names), set([]))
#         self.assertEqual(set(b1_clone.state_variable_names), set([]))
# 
#         self.assertEqual(set(b2_clone.analog_port_names), set([]))
#         self.assertEqual(set(b2_clone.event_port_names), set([]))
#         self.assertEqual(set(b2_clone.parameter_names), set([]))
#         self.assertEqual(set(b2_clone.state_variable_names), set([]))
