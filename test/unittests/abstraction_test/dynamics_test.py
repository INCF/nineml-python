from builtins import str
import unittest
from sympy import sympify
from nineml.abstraction import (
    Dynamics, AnalogSendPort, Alias,
    AnalogReceivePort, AnalogReducePort, Regime, On,
    OutputEvent, EventReceivePort, Constant, StateVariable, Parameter,
    OnCondition, OnEvent, Trigger)
import nineml.units as un
from nineml.exceptions import NineMLMathParseError, NineMLRuntimeError
from nineml.document import Document


class ComponentClass_test(unittest.TestCase):

    def test_aliases(self):
        # Signature: name
                # Forwarding function to self.dynamics.aliases

        # No Aliases:
        self.assertEqual(
            list(Dynamics(name='C1').aliases),
            []
        )

        # 2 Aliases
        C = Dynamics(name='C1', aliases=['G:= 0', 'H:=1'])
        self.assertEqual(len(list((C.aliases))), 2)
        self.assertEqual(
            set(C.alias_names), set(['G', 'H'])
        )

        C = Dynamics(name='C1', aliases=['G:= 0', 'H:=1', Alias('I', '3')])
        self.assertEqual(len(list((C.aliases))), 3)
        self.assertEqual(
            set(C.alias_names), set(['G', 'H', 'I'])
        )

        # Using DynamicsBlock Parameter:
        C = Dynamics(name='C1', aliases=['G:= 0', 'H:=1'])
        self.assertEqual(len(list((C.aliases))), 2)
        self.assertEqual(
            set(C.alias_names), set(['G', 'H'])
        )

        C = Dynamics(name='C1',
                           aliases=['G:= 0', 'H:=1', Alias('I', '3')])
        self.assertEqual(len(list((C.aliases))), 3)
        self.assertEqual(
            set(C.alias_names), set(['G', 'H', 'I'])
        )

        # Invalid Construction:
        # Invalid Valid String:
        self.assertRaises(
            NineMLRuntimeError,
            Dynamics, name='C1', aliases=['H=0']
        )

        # Duplicate Alias Names:
        Dynamics(name='C1', aliases=['H:=0', 'G:=1'])
        self.assertRaises(
            NineMLRuntimeError,
            Dynamics, name='C1', aliases=['H:=0', 'H:=1']
        )

        self.assertRaises(
            NineMLRuntimeError,
            Dynamics, name='C1', aliases=['H:=0', Alias('H', '1')]
        )

        # Self referential aliases:
        self.assertRaises(
            NineMLRuntimeError,
            Dynamics,
            name='C1', aliases=['H := H +1'],
        )
        self.assertRaises(
            NineMLRuntimeError,
            Dynamics,
            name='C1', aliases=['H := G + 1', 'G := H + 1'],
        )

        # Referencing none existent symbols:
        self.assertRaises(
            NineMLRuntimeError,
            Dynamics,
            name='C1',
            aliases=['H := G + I'],
            parameters=['P1'],
        )

        # Invalid Names:
        self.assertRaises(
            NineMLRuntimeError,
            Dynamics,
            name='C1', aliases=['H.2 := 0'],
        )

        self.assertRaises(
            NineMLRuntimeError,
            Dynamics,
            name='C1', aliases=['2H := 0'],
        )

        self.assertRaises(
            NineMLRuntimeError,
            Dynamics,
            name='C1', aliases=['E(H) := 0'],
        )

        self.assertRaises(
            NineMLRuntimeError,
            Dynamics,
            name='C1', aliases=['tanh := 0'],
        )
        self.assertRaises(
            NineMLRuntimeError,
            Dynamics,
            name='C1', aliases=['t := 0'],
        )

    def test_aliases_map(self):
        # Signature: name
                # Forwarding function to self.dynamics.alias_map

        self.assertEqual(
            Dynamics(name='C1')._aliases, {}
        )

        c1 = Dynamics(name='C1', aliases=['A:=3'])
        self.assertEqual(c1.alias('A').rhs_as_python_func(), 3)
        self.assertEqual(len(c1._aliases), 1)

        c2 = Dynamics(name='C1', aliases=['A:=3', 'B:=5'])
        self.assertEqual(c2.alias('A').rhs_as_python_func(), 3)
        self.assertEqual(c2.alias('B').rhs_as_python_func(), 5)
        self.assertEqual(len(c2._aliases), 2)

        c3 = Dynamics(name='C1', aliases=['C:=13', 'Z:=15'])
        self.assertEqual(c3.alias('C').rhs_as_python_func(), 13)
        self.assertEqual(c3.alias('Z').rhs_as_python_func(), 15)

        self.assertEqual(len(c3._aliases), 2)

    def test_analog_ports(self):
        # Signature: name
                # No Docstring

        c = Dynamics(name='C1')
        self.assertEqual(len(list(c.analog_ports)), 0)

        c = Dynamics(name='C1')
        self.assertEqual(len(list(c.analog_ports)), 0)

        c = Dynamics(name='C1', aliases=['A:=2'],
                     analog_ports=[AnalogSendPort('A')])
        self.assertEqual(len(list(c.analog_ports)), 1)
        self.assertEqual(list(c.analog_ports)[0].mode, 'send')
        self.assertEqual(len(list(c.analog_send_ports)), 1)
        self.assertEqual(len(list(c.analog_receive_ports)), 0)
        self.assertEqual(len(list(c.analog_reduce_ports)), 0)

        c = Dynamics(name='C1', analog_ports=[AnalogReceivePort('B')])
        self.assertEqual(len(list(c.analog_ports)), 1)
        self.assertEqual(list(c.analog_ports)[0].mode, 'recv')
        self.assertEqual(len(list(c.analog_send_ports)), 0)
        self.assertEqual(len(list(c.analog_receive_ports)), 1)
        self.assertEqual(len(list(c.analog_reduce_ports)), 0)

        c = Dynamics(name='C1',
                     analog_ports=[AnalogReducePort('B', operator='+')])
        self.assertEqual(len(list(c.analog_ports)), 1)
        self.assertEqual(list(c.analog_ports)[0].mode, 'reduce')
        self.assertEqual(list(c.analog_ports)[0].operator, '+')
        self.assertEqual(len(list(c.analog_send_ports)), 0)
        self.assertEqual(len(list(c.analog_receive_ports)), 0)
        self.assertEqual(len(list(c.analog_reduce_ports)), 1)

        # Duplicate Port Names:
        self.assertRaises(
            NineMLRuntimeError,
            Dynamics,
            name='C1',
            aliases=['A:=1'],
            analog_ports=[AnalogReducePort('B', operator='+'),
                          AnalogSendPort('B')]
        )

        self.assertRaises(
            NineMLRuntimeError,
            Dynamics,
            name='C1',
            aliases=['A:=1'],
            analog_ports=[AnalogSendPort('A'), AnalogSendPort('A')]
        )

        self.assertRaises(
            NineMLRuntimeError,
            Dynamics,
            name='C1',
            aliases=['A:=1'],
            analog_ports=[AnalogReceivePort('A'), AnalogReceivePort('A')]
        )

        self.assertRaises(
            NineMLRuntimeError,
            lambda: Dynamics(name='C1', analog_ports=[AnalogReceivePort('1')])
        )

        self.assertRaises(
            NineMLRuntimeError,
            lambda: Dynamics(name='C1', analog_ports=[AnalogReceivePort('?')])
        )

    def duplicate_port_name_event_analog(self):

        # Check different names are OK:
        Dynamics(
            name='C1', aliases=['A:=1'],
            event_ports=[EventReceivePort('A')],
            analog_ports=[AnalogSendPort('A')])

        self.assertRaises(
            NineMLRuntimeError,
            Dynamics,
            name='C1',
            aliases=['A:=1'],
            event_ports=[EventReceivePort('A')],
            analog_ports=[AnalogSendPort('A')]
        )

    def test_event_ports(self):
        # Signature: name
                # No Docstring

        # Check inference of output event ports:
        c = Dynamics(
            name='Comp1',
            regimes=Regime(
                transitions=[
                    On('V > a', do=OutputEvent('ev_port1')),
                    On('V > b', do=OutputEvent('ev_port1')),
                    On('V < c', do=OutputEvent('ev_port2')),
                ]
            ),
        )
        self.assertEquals(len(list(c.event_ports)), 2)

        # Check inference of output event ports:
        c = Dynamics(
            name='Comp1',
            regimes=[
                Regime(name='r1',
                       transitions=[
                           On('V > a', do=OutputEvent('ev_port1'), to='r2'),
                           On('V < b', do=OutputEvent('ev_port2'))]),

                Regime(name='r2',
                       transitions=[
                           On('V > a', do=OutputEvent('ev_port2'), to='r1'),
                           On('V < b', do=OutputEvent('ev_port3'))])
            ]
        )
        self.assertEquals(len(list(c.event_ports)), 3)

        # Check inference of output event ports:
        c = Dynamics(
            name='Comp1',
            regimes=[
                Regime(name='r1',
                       transitions=[
                           On('spikeinput1', do=[]),
                           On('spikeinput2', do=OutputEvent('ev_port2'),
                              to='r2')]),

                Regime(name='r2',
                       transitions=[
                           On('V > a', do=OutputEvent('ev_port2')),
                           On('spikeinput3', do=OutputEvent('ev_port3'),
                              to='r1')])
            ]
        )
        self.assertEquals(len(list(c.event_ports)), 5)

    def test_parameters(self):
        # Signature: name
                # No Docstring

        # No parameters; nothing to infer
        c = Dynamics(name='cl')
        self.assertEqual(len(list(c.parameters)), 0)

        # Mismatch between inferred and actual parameters
        self.assertRaises(
            NineMLRuntimeError,
            Dynamics, name='cl', parameters=['a'])

        # Single parameter inference from an alias block
        c = Dynamics(name='cl', aliases=['A:=a'])
        self.assertEqual(len(list(c.parameters)), 1)
        self.assertEqual(list(c.parameters)[0].name, 'a')

        # More complex inference:
        c = Dynamics(name='cl', aliases=['A:=a+e', 'B:=a+pi+b'],
                           constants=[Constant('pi', 3.141592653589793)])
        self.assertEqual(len(list(c.parameters)), 3)
        self.assertEqual(sorted([p.name for p in c.parameters]),
                         ['a', 'b', 'e'])

        # From State Assignments and Differential Equations, and Conditionals
        c = Dynamics(name='cl',
                     aliases=['A:=a+e', 'B:=a+pi+b'],
                     regimes=Regime('dX/dt = (6 + c + sin(d))/t',
                                    'dV/dt = 1.0/t',
                                    transitions=On('V>Vt',
                                                   do=['X = X + f', 'V=0'])),
                     constants=[Constant('pi', 3.1415926535)])
        self.assertEqual(len(list(c.parameters)), 7)
        self.assertEqual(
            sorted([p.name for p in c.parameters]),
            ['Vt', 'a', 'b', 'c', 'd', 'e', 'f'])

        self.assertRaises(
            NineMLRuntimeError,
            Dynamics,
            name='cl',
            aliases=['A:=a+e', 'B:=a+pi+b'],
            regimes=Regime('dX/dt = 6 + c + sin(d)',
                           'dV/dt = 1.0',
                           transitions=On('V>Vt', do=['X = X + f', 'V=0'])
                           ),
            parameters=['a', 'b', 'c'])

    def test_regimes(self):

        c = Dynamics(name='cl', )
        self.assertEqual(len(list(c.regimes)), 0)

        c = Dynamics(name='cl',
                     regimes=Regime('dX/dt=1/t',
                                    name='r1',
                                    transitions=On('X>X1', do=['X = X0'],
                                                   to=None)))
        self.assertEqual(len(list(c.regimes)), 1)

        c = Dynamics(name='cl',
                           regimes=[
                               Regime('dX/dt=1/t',
                                      name='r1',
                                      transitions=On('X>X1', do=['X=X0'],
                                                     to='r2')),
                               Regime('dX/dt=1/t',
                                      name='r2',
                                      transitions=On('X>X1', do=['X=X0'],
                                                     to='r3')),
                               Regime('dX/dt=1/t',
                                      name='r3',
                                      transitions=On('X>X1', do=['X=X0'],
                                                     to='r4')),
                               Regime('dX/dt=1/t',
                                      name='r4',
                                      transitions=On('X>X1', do=['X=X0'],
                                                     to='r1'))])
        self.assertEqual(len(list(c.regimes)), 4)
        self.assertEqual(
            set(c.regime_names),
            set(['r1', 'r2', 'r3', 'r4'])
        )

        c = Dynamics(name='cl',
                           regimes=[
                               Regime('dX/dt=1/t', name='r1',
                                      transitions=On('X>X1', do=['X=X0'],
                                                     to='r2')),
                               Regime('dX/dt=1/t',
                                       name='r2',
                                       transitions=On('X>X1', do=['X=X0'],
                                                      to='r3')),
                               Regime('dX/dt=1/t',
                                      name='r3',
                                      transitions=On('X>X1', do=['X=X0'],
                                                     to='r4')),
                               Regime('dX/dt=1/t',
                                      name='r4',
                                      transitions=On('X>X1', do=['X=X0'],
                                                     to='r1'))])
        self.assertEqual(len(list(c.regimes)), 4)
        self.assertEqual(
            set([r.name for r in c.regimes]),
            set(['r1', 'r2', 'r3', 'r4'])
        )

        # Duplicate Names:
        self.assertRaises(
            NineMLRuntimeError,
            Dynamics, name='cl',
            regimes=[
                Regime('dX/dt=1/t',
                       name='r',
                       transitions=On('X>X1', do=['X=X0'])),
                Regime('dX/dt=1/t',
                       name='r',
                       transitions=On('X>X1', do=['X=X0'],)), ]
        )

    def test_regime_aliases(self):
        a = Dynamics(
            name='a',
            aliases=[Alias('A', '4/t')],
            regimes=[
                Regime('dX/dt=1/t + A',
                       name='r1',
                       transitions=On('X>X1', do=['X=X0'], to='r2')),
                Regime('dX/dt=1/t + A',
                       name='r2',
                       transitions=On('X>X1', do=['X=X0'],
                                      to='r1'),
                       aliases=[Alias('A', '8 / t')])])
        self.assertEqual(a.regime('r2').alias('A'), Alias('A', '8 / t'))
        self.assertRaises(
            NineMLRuntimeError,
            Dynamics,
            name='a',
            regimes=[
                Regime('dX/dt=1/t + A',
                       name='r1',
                       transitions=On('X>X1', do=['X=X0'], to='r2')),
                Regime('dX/dt=1/t + A',
                       name='r2',
                       transitions=On('X>X1', do=['X=X0'],
                                      to='r1'),
                       aliases=[Alias('A', '8 / t')])])
        document = Document()
        a_xml = a.serialize(format='xml', version=1, document=document)
        b = Dynamics.unserialize(a_xml, format='xml', version=1,
                                 document=Document(un.dimensionless.clone()))
        self.assertEqual(a, b,
                         "Dynamics with regime-specific alias failed xml "
                         "roundtrip:\n{}".format(a.find_mismatch(b)))

    def test_state_variables(self):
        # No parameters; nothing to infer
        c = Dynamics(name='cl')
        self.assertEqual(len(list(c.state_variables)), 0)

        # From State Assignments and Differential Equations, and Conditionals
        c = Dynamics(
            name='cl',
            aliases=['A:=a+e', 'B:=a+pi+b'],
            regimes=Regime('dX/dt = (6 + c + sin(d))/t',
                           'dV/dt = 1.0/t',
                           transitions=On('V>Vt', do=['X = X + f', 'V=0'])))
        self.assertEqual(
            set(c.state_variable_names),
            set(['X', 'V']))

        self.assertRaises(
            NineMLRuntimeError,
            Dynamics,
            name='cl',
            aliases=['A:=a+e', 'B:=a+pi+b'],
            regimes=Regime('dX/dt = 6 + c + sin(d)',
                           'dV/dt = 1.0',
                           transitions=On('V>Vt', do=['X = X + f', 'V=0'])
                           ),
            state_variables=['X'])

        # Shouldn't pick up 'e' as a parameter:
        self.assertRaises(
            NineMLRuntimeError,
            Dynamics,
            name='cl',
            aliases=['A:=a+e', 'B:=a+pi+b'],
            regimes=Regime('dX/dt = 6 + c + sin(d)',
                           'dV/dt = 1.0',
                           transitions=On('V>Vt', do=['X = X + f', 'V=0'])
                           ),
            state_variables=['X', 'V', 'Vt'])

        c = Dynamics(name='cl',
                           regimes=[
                               Regime('dX1/dt=1/t',
                                      name='r1',
                                      transitions=On('X>X1', do=['X=X0'],
                                                     to='r2')),
                               Regime('dX1/dt=1/t',
                                      name='r2',
                                      transitions=On('X>X1', do=['X=X0'],
                                                     to='r3')),
                               Regime('dX2/dt=1/t',
                                      name='r3',
                                      transitions=On('X>X1', do=['X=X0'],
                                                     to='r4')),
                               Regime('dX2/dt=1/t',
                                      name='r4',
                                      transitions=On('X>X1', do=['X=X0'],
                                                     to='r1'))])
        self.assertEqual(set(c.state_variable_names),
                         set(['X1', 'X2', 'X']))

    def test_transitions(self):

        c = Dynamics(name='cl',
                           regimes=[
                               Regime('dX1/dt=1/t',
                                      name='r1',
                                      transitions=[On('X>X1', do=['X=X0'],
                                                      to='r2'),
                                                   On('X>X2', do=['X=X0'],
                                                      to='r3'), ]
                                      ),
                               Regime('dX1/dt=1/t',
                                      name='r2',
                                      transitions=On('X>X1', do=['X=X0'],
                                                     to='r3'),),
                               Regime('dX2/dt=1/t',
                                      name='r3',
                                      transitions=[On('X>X1', do=['X=X0'],
                                                      to='r4'),
                                                   On('X>X2', do=['X=X0'],
                                                      to=None)]),
                               Regime('dX2/dt=1/t',
                                      name='r4',
                                      transitions=On('X>X1', do=['X=X0'],
                                                     to=None))])

        self.assertEquals(len(list(c.all_transitions())), 6)

        r1 = c.regime('r1')
        r2 = c.regime('r2')
        r3 = c.regime('r3')
        r4 = c.regime('r4')

        self.assertEquals(len(list(r1.transitions)), 2)
        self.assertEquals(len(list(r2.transitions)), 1)
        self.assertEquals(len(list(r3.transitions)), 2)
        self.assertEquals(len(list(r4.transitions)), 1)

        target_regimes = lambda r: set([tr.target_regime
                                        for tr in r.transitions])
        self.assertEquals(target_regimes(r1), set([r2, r3]))
        self.assertEquals(target_regimes(r2), set([r3]))
        self.assertEquals(target_regimes(r3), set([r3, r4]))
        self.assertEquals(target_regimes(r4), set([r4]))

    def test_all_expressions(self):
        a = Dynamics(
            name='A',
            aliases=['A1:=P1 * SV2', 'A2 := ARP1 + SV2', 'A3 := SV1'],
            state_variables=[
                StateVariable('SV1', dimension=un.voltage),
                StateVariable('SV2', dimension=un.current)],
            regimes=[
                Regime(
                    'dSV1/dt = -SV1 / P2',
                    'dSV2/dt = A3 / ARP2 + SV2 / P2',
                    transitions=[On('SV1 > P3', do=[OutputEvent('emit')]),
                                 On('spikein', do=[OutputEvent('emit')])],
                    name='R1'
                ),
                Regime(name='R2', transitions=On('(SV1 > C1) & (SV2 < P4)',
                                                 to='R1'))
            ],
            analog_ports=[AnalogReceivePort('ARP1', dimension=un.current),
                          AnalogReceivePort('ARP2',
                                            dimension=(un.resistance *
                                                       un.time)),
                          AnalogSendPort('A1',
                                         dimension=un.voltage * un.current),
                          AnalogSendPort('A2', dimension=un.current)],
            parameters=[Parameter('P1', dimension=un.voltage),
                        Parameter('P2', dimension=un.time),
                        Parameter('P3', dimension=un.voltage),
                        Parameter('P4', dimension=un.current)],
            constants=[Constant('C1', value=1.0, units=un.mV)]
        )

        self.assertEqual(
            set(a.all_expressions), set((
                sympify('P1 * SV2'), sympify('ARP1 + SV2'), sympify('SV1'),
                sympify('-SV1 / P2'), sympify('-SV1 / P2'),
                sympify('A3 / ARP2 + SV2 / P2'), sympify('SV1 > P3'),
                sympify('(SV1 > C1) & (SV2 < P4)'))),
            "All expressions were not extracted from component class")


class TestOn(unittest.TestCase):

    def test_On(self):
        # Signature: name(trigger, do=None, to=None)
                # No Docstring

        # Test that we are correctly inferring OnEvents and OnConditions.

        self.assertEquals(type(On('V>0')), OnCondition)
        self.assertEquals(type(On('V<0')), OnCondition)
        self.assertEquals(type(On('(V<0) & (K>0)')), OnCondition)
        self.assertEquals(type(On('V==0')), OnCondition)

        self.assertEquals(
            type(On("q > 1 / (( 1 + mg_conc * eta *  exp ( -1 * gamma*V)))")),
            OnCondition)

        self.assertEquals(type(On('SP0')), OnEvent)
        self.assertEquals(type(On('SP1')), OnEvent)

        # Check we can use 'do' with single and multiple values
        tr = On('V>0')
        self.assertEquals(len(list(tr.output_events)), 0)
        self.assertEquals(len(list(tr.state_assignments)), 0)
        tr = On('SP0')
        self.assertEquals(len(list(tr.output_events)), 0)
        self.assertEquals(len(list(tr.state_assignments)), 0)

        tr = On('V>0', do=OutputEvent('spike'))
        self.assertEquals(len(list(tr.output_events)), 1)
        self.assertEquals(len(list(tr.state_assignments)), 0)
        tr = On('SP0', do=OutputEvent('spike'))
        self.assertEquals(len(list(tr.output_events)), 1)
        self.assertEquals(len(list(tr.state_assignments)), 0)

        tr = On('V>0', do=[OutputEvent('spike')])
        self.assertEquals(len(list(tr.output_events)), 1)
        self.assertEquals(len(list(tr.state_assignments)), 0)
        tr = On('SP0', do=[OutputEvent('spike')])
        self.assertEquals(len(list(tr.output_events)), 1)
        self.assertEquals(len(list(tr.state_assignments)), 0)

        tr = On('V>0', do=['y=2', OutputEvent('spike'), 'x=1'])
        self.assertEquals(len(list(tr.output_events)), 1)
        self.assertEquals(len(list(tr.state_assignments)), 2)
        tr = On('SP0', do=['y=2', OutputEvent('spike'), 'x=1'])
        self.assertEquals(len(list(tr.output_events)), 1)
        self.assertEquals(len(list(tr.state_assignments)), 2)


class OnCondition_test(unittest.TestCase):

    def test_trigger(self):

        invalid_triggers = ['true(',
                            'V < (V+10',
                            'V (< V+10)',
                            'V (< V+10)',
                            '1 / ( 1 + mg_conc * eta *  exp (( -1 * gamma*V))'
                            '1..0'
                            '..0']
        for tr in invalid_triggers:
            self.assertRaises(NineMLMathParseError, OnCondition, tr)

        # Test Come Conditions:
        namespace = {
            "A": 10,
            "B": 5,
            "tau_r": 5,
            "V": 20,
            "Vth": -50.0,
            "t_spike": 1.0,
            "q": 11.0,
            "t": 0.9,
            "tref": 0.1
        }

        cond_exprs = [
            ["A > -B/tau_r", ("A", "B", "tau_r"), ()],
            ["(V > 1.0) & !(V<10.0)", ("V",), ()],
            ["!!(V>10)", ("V"), ()],
            ["!!(V>10)", ("V"), ()],
            ["V>exp(Vth)", ("V", "Vth"), ('exp',)],
            ["!(V>Vth)", ("V", "Vth"), ()],
            ["!(V>Vth)", ("V", "Vth"), ()],
            ["exp(V)>Vth", ("V", "Vth"), ("exp",)],
            ["true", (), ()],
            ["(V < (Vth+q)) & (t > t_spike)", ("t_spike", "t", "q", "Vth",
                                               "V"), ()],
            ["(V < (Vth+q)) | (t > t_spike)", ("t_spike", "Vth", "q", "V",
                                               "t"), ()],
            ["(true)", (), ()],
            ["!true", (), ()],
            ["!false", (), ()],
            ["t >= t_spike + tref", ("t", "t_spike", "tref"), ()],
            ["true & !false", (), ()]
        ]

        return_values = [
            True,
            True,
            True,
            True,
            True,
            False,
            False,
            True,
            True,
            False,
            False,
            True,
            False,
            True,
            False,
            True
        ]

        for i, (expr, expt_vars, expt_funcs) in enumerate(cond_exprs):
            c = OnCondition(trigger=expr)
            self.assertEqual(set(c.trigger.rhs_symbol_names), set(expt_vars))
            self.assertEqual(set(str(f) for f in c.trigger.rhs_funcs),
                             set(expt_funcs))

            python_func = c.trigger.rhs_as_python_func
            param_dict = dict([(v, namespace[v]) for v in expt_vars])
            self.assertEquals(return_values[i], python_func(**param_dict))

    def test_trigger_crossing_time_expr(self):
        self.assertEqual(Trigger('t > t_next').crossing_time_expr.rhs,
                         sympify('t_next'))
        self.assertEqual(Trigger('t^2 > t_next').crossing_time_expr, None)
        self.assertEqual(Trigger('a < b').crossing_time_expr, None)
        self.assertEqual(
            Trigger('t > t_next || t > t_next2').crossing_time_expr.rhs,
            sympify('Min(t_next, t_next2)'))
        self.assertEqual(
            Trigger('t > t_next || a < b').crossing_time_expr, None)

    def test_make_strict(self):
        self.assertEqual(
            Trigger._make_strict(
                sympify('(a >= 0.5) & ~(b < (10 * c * e)) | (c <= d)')),
            sympify('(a > 0.5) & (b > (10 * c * e)) | (c < d)'))


class OnEvent_test(unittest.TestCase):

    def test_Constructor(self):
        pass

    def test_src_port_name(self):

        self.assertRaises(NineMLRuntimeError, OnEvent, '1MyEvent1 ')
        self.assertRaises(NineMLRuntimeError, OnEvent, 'MyEvent1 2')
        self.assertRaises(NineMLRuntimeError, OnEvent, 'MyEvent1* ')

        self.assertEquals(OnEvent(' MyEvent1 ').src_port_name, 'MyEvent1')
        self.assertEquals(OnEvent(' MyEvent2').src_port_name, 'MyEvent2')


class Regime_test(unittest.TestCase):

    def test_Constructor(self):
        pass

    def test_add_on_condition(self):
        # Signature: name(self, on_condition)
        # Add an OnCondition transition which leaves this regime
        #
        # If the on_condition object has not had its target regime name set in
        # the constructor, or by calling its ``set_target_regime_name()``, then
        # the target is assumed to be this regime, and will be set
        # appropriately.
        #
        # The source regime for this transition will be set as this regime.

        r = Regime(name='R1')
        self.assertEquals(set(r.on_conditions), set())
        r.add(OnCondition('sp1>0'))
        self.assertEquals(len(set(r.on_conditions)), 1)
        self.assertEquals(len(set(r.on_events)), 0)
        self.assertEquals(len(set(r.transitions)), 1)

    def test_add_on_event(self):
        # Signature: name(self, on_event)
        # Add an OnEvent transition which leaves this regime
        #
        # If the on_event object has not had its target regime name set in the
        # constructor, or by calling its ``set_target_regime_name()``, then the
        # target is assumed to be this regime, and will be set appropriately.
        #
        # The source regime for this transition will be set as this regime.
        # from nineml.abstraction.component.dynamics import Regime
        r = Regime(name='R1')
        self.assertEquals(set(r.on_events), set())
        r.add(OnEvent('sp'))
        self.assertEquals(len(set(r.on_events)), 1)
        self.assertEquals(len(set(r.on_conditions)), 0)
        self.assertEquals(len(set(r.transitions)), 1)

    def test_get_next_name(self):
        # Signature: name(cls)
        # Return the next distinct autogenerated name

        n1 = Regime.get_next_name()
        n2 = Regime.get_next_name()
        n3 = Regime.get_next_name()
        self.assertNotEqual(n1, n2)
        self.assertNotEqual(n2, n3)

    def test_name(self):

        self.assertRaises(NineMLRuntimeError, Regime, name='&Hello')
        self.assertRaises(NineMLRuntimeError, Regime, name='2Hello')

        self.assertEqual(Regime(name='Hello').name, 'Hello')
        self.assertEqual(Regime(name='Hello2').name, 'Hello2')

    def test_time_derivatives(self):
        # Signature: name
        # Returns the state-variable time-derivatives in this regime.
        #
        # .. note::
        #
        #     This is not guarenteed to contain the time derivatives for all
        #     the state-variables specified in the component. If they are not
        #     defined, they are assumed to be zero in this regime.

        r = Regime('dX1/dt=0',
                   'dX2/dt=0',
                   name='r1')

        self.assertEquals(
            set([td.variable for td in r.time_derivatives]),
            set(['X1', 'X2']))

        # Defining a time derivative twice:
        self.assertRaises(
            NineMLRuntimeError,
            Regime, 'dX/dt=1', 'dX/dt=2')

        # Assigning to a value:
        self.assertRaises(
            NineMLRuntimeError,
            Regime, 'X=1')


class StateVariable_test(unittest.TestCase):

    def test_name(self):
        # Signature: name
                # No Docstring

        self.assertRaises(NineMLRuntimeError, StateVariable, name='&Hello')
        self.assertRaises(NineMLRuntimeError, StateVariable, name='2Hello')

        self.assertEqual(StateVariable(name='Hello').name, 'Hello')
        self.assertEqual(StateVariable(name='Hello2').name, 'Hello2')


class Query_test(unittest.TestCase):

    def test_event_send_receive_ports(self):
        # Signature: name(self)
                # Get the ``recv`` EventPorts
        # from nineml.abstraction.component.componentqueryer import
        # ComponentClassQueryer

        # Check inference of output event ports:
        c = Dynamics(
            name='Comp1',
            regimes=Regime(
                transitions=[
                    On('in_ev1', do=OutputEvent('ev_port1')),
                    On('V < b', do=OutputEvent('ev_port1')),
                    On('V < c', do=OutputEvent('ev_port2')),
                ]
            ),
        )
        self.assertEquals(len(list(c.event_receive_ports)), 1)
        self.assertEquals((list(list(c.event_receive_ports))[0]).name,
                          'in_ev1')

        self.assertEquals(len(list(c.event_send_ports)), 2)
        self.assertEquals(set(c.event_send_port_names),
                          set(['ev_port1', 'ev_port2']))

        # Check inference of output event ports:
        c = Dynamics(
            name='Comp1',
            regimes=[
                Regime(name='r1',
                       transitions=[
                           On('V > a', do=OutputEvent('ev_port1'), to='r2'),
                           On('in_ev1', do=OutputEvent('ev_port2'))]),

                Regime(name='r2',
                       transitions=[
                           On('V > a', do=OutputEvent('ev_port2'), to='r1'),
                           On('in_ev2', do=OutputEvent('ev_port3'))])
            ]
        )
        self.assertEquals(len(list(c.event_receive_ports)), 2)
        self.assertEquals(set(c.event_receive_port_names),
                          set(['in_ev1', 'in_ev2']))

        self.assertEquals(len(list(c.event_send_ports)), 3)
        self.assertEquals(set(c.event_send_port_names),
                           set(['ev_port1', 'ev_port2', 'ev_port3']))

        # Check inference of output event ports:
        c = Dynamics(
            name='Comp1',
            regimes=[
                Regime(name='r1',
                       transitions=[
                           On('spikeinput1', do=[]),
                           On('spikeinput2', do=[
                               OutputEvent('ev_port1'),
                               OutputEvent('ev_port2')], to='r2')]),

                Regime(name='r2',
                       transitions=[
                           On('V > a', do=OutputEvent('ev_port2')),
                           On('spikeinput3', do=OutputEvent('ev_port3'),
                              to='r1')])
            ]
        )
        self.assertEquals(len(list(c.event_receive_ports)), 3)
        self.assertEquals(set(c.event_receive_port_names),
                          set(['spikeinput1', 'spikeinput2', 'spikeinput3']))

        self.assertEquals(len(list(c.event_send_ports)), 3)
        self.assertEquals(set(c.event_send_port_names),
                          set(['ev_port1', 'ev_port2', 'ev_port3']))

    def test_ports(self):
        # Signature: name
                # Return an iterator over all the port (Event & Analog) in the
                # component
        # from nineml.abstraction.component.componentqueryer import
        # ComponentClassQueryer

        c = Dynamics(
            name='Comp1',
            regimes=[
                Regime(name='r1',
                       transitions=[
                           On('spikeinput1', do=[]),
                           On('spikeinput2', do=OutputEvent('ev_port2'),
                              to='r2')]),

                Regime(name='r2',
                       transitions=[
                           On('V > a', do=OutputEvent('ev_port2')),
                           On('spikeinput3', do=OutputEvent('ev_port3'),
                              to='r1')])
            ],
            aliases=['A:=0', 'C:=0'],
            analog_ports=[AnalogSendPort('A'), AnalogReceivePort('B'),
                          AnalogSendPort('C')]
        )

        ports = list(list(c.ports))
        port_names = [p.name for p in ports]

        self.assertEquals(len(port_names), 8)
        self.assertEquals(set(port_names),
                          set(['A', 'B', 'C', 'spikeinput1', 'spikeinput2',
                               'spikeinput3', 'ev_port2', 'ev_port3'])
                          )

    def test_regime(self):
        # Signature: name(self, name=None)
        # Find a regime in the component by name
        # from nineml.abstraction.component.componentqueryer import
        # ComponentClassQueryer

        c = Dynamics(name='cl',
                     regimes=[
                          Regime('dX/dt=1/t',
                                 name='r1',
                                 transitions=On('X>X1', do=['X=X0'],
                                                to='r2')),
                          Regime('dX/dt=1/t',
                                 name='r2',
                                 transitions=On('X>X1', do=['X=X0'],
                                                to='r3')),
                          Regime('dX/dt=1/t',
                                 name='r3',
                                 transitions=On('X>X1', do=['X=X0'],
                                                to='r4')),
                          Regime('dX/dt=1/t',
                                 name='r4',
                                 transitions=On('X>X1', do=['X=X0'],
                                                to='r1'))])
        self.assertEqual(c.regime(name='r1').name, 'r1')
        self.assertEqual(c.regime(name='r2').name, 'r2')
        self.assertEqual(c.regime(name='r3').name, 'r3')
        self.assertEqual(c.regime(name='r4').name, 'r4')
