import os
import sys
import unittest
from sympy import sympify
from nineml.exceptions import NineMLRuntimeError
from nineml.abstraction import (
    Dynamics, AnalogSendPort, Alias,
    AnalogReceivePort, AnalogReducePort, Regime, On, NamespaceAddress,
    OutputEvent, EventReceivePort, Constant, StateVariable, Parameter)
import nineml.units as un
from nineml.utils import restore_sys_path
from nineml.utils import LocationMgr
from nineml.document import Document


class ComponentClass_test(unittest.TestCase):

    def test_Constructor(self):
        pass

    def test_accept_visitor(self):
        # Signature: name(self, visitor, **kwargs)
                # |VISITATION|
        # Check the Component is forwarding arguments:

        class TestVisitor(object):

            def visit(self, obj, **kwargs):
                return obj.accept_visitor(self, **kwargs)

            def visit_componentclass(self, component, **kwargs):
                return kwargs

        c = Dynamics(name='MyComponent')
        v = TestVisitor()

        self.assertEqual(
            v.visit(c, kwarg1='Hello', kwarg2='Hello2'),
            {'kwarg1': 'Hello', 'kwarg2': 'Hello2'}
        )

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

        # Referencing none existant symbols:
        self.assertRaises(
            NineMLRuntimeError,
            Dynamics,
            name='C1',
            aliases=['H := G + I'],
            parameters=[],
            analog_ports=[],
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

        c = Dynamics(name='C1', aliases=['A:=2'], analog_ports=[AnalogSendPort('A')])
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

        c = Dynamics(name='C1', analog_ports=[AnalogReducePort('B', operator='+')])
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
            analog_ports=[AnalogReducePort('B', operator='+'), AnalogSendPort('B')]
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

    # Testing done in test_backsub_all()
    def test_backsub_aliases(self):
        pass

    def test_backsub_equations(self):
        pass

    def test_backsub_all(self):

        # Check the aliases:
        # ====================== #
        c2 = Dynamics(name='C1', aliases=['A:=1.0+2.0', 'B:=5.0*A', 'C:=B+2.0'])
        self.assertEqual(c2.alias('A').rhs_as_python_func(), 3)

        # This should assert, because its not yet back-subbed
        c2.backsub_all()
        self.assertEqual(c2.alias('B').rhs_as_python_func(), 15)
        # Check the ordering:
        self.assertEqual(c2.alias('C').rhs_as_python_func(), ((5 * (3)) + 2))
        # ====================== #

        # Check the equations:
        # ====================== #
#         warnings.warn('Tests not implemented')
        pass
        # ====================== #

    
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
                       On('V < b', do=OutputEvent('ev_port2')),
                       ]
                       ),

                Regime(name='r2',
                       transitions=[
                       On('V > a', do=OutputEvent('ev_port2'), to='r1'),
                       On('V < b', do=OutputEvent('ev_port3')),
                       ]
                       )
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
                       On('spikeinput2', do=OutputEvent('ev_port2'), to='r2'),
                       ]
                       ),

                Regime(name='r2',
                       transitions=[
                       On('V > a', do=OutputEvent('ev_port2')),
                       On('spikeinput3', do=OutputEvent('ev_port3'), to='r1'),
                       ]
                       )
            ]
        )
        self.assertEquals(len(list(c.event_ports)), 5)

    # TESTED IN:
        # test_get_node_addr
    # def test_name(self):
        # Signature: name
                # No Docstring
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
        self.assertEqual(sorted([p.name for p in c.parameters]), ['a', 'b', 'e'])

        # From State Assignments and Differential Equations, and Conditionals
        c = Dynamics(name='cl',
                           aliases=['A:=a+e', 'B:=a+pi+b'],
                           regimes=Regime('dX/dt = (6 + c + sin(d))/t',
                                          'dV/dt = 1.0/t',
                                          transitions=On('V>Vt',
                                                         do=['X = X + f', 'V=0'])
                                          ),
                           constants=[Constant('pi', 3.1415926535)]
                           )
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
                                          transitions=On('X>X1', do=['X = X0'], to=None))
                           )
        self.assertEqual(len(list(c.regimes)), 1)

        c = Dynamics(name='cl',
                           regimes=[
                                Regime('dX/dt=1/t',
                                       name='r1',
                                       transitions=On('X>X1', do=['X=X0'], to='r2')),
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
                                                      to='r1')),
                           ]
                           )
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
        a_xml = a.to_xml(document)
        b = Dynamics.from_xml(a_xml, Document(un.dimensionless))
        self.assertEqual(a, b,
                         "Dynamics with regime-specific alias failed xml "
                         "roundtrip")

    def test_state_variables(self):
        # No parameters; nothing to infer
        c = Dynamics(name='cl')
        self.assertEqual(len(list(c.state_variables)), 0)

        # Mismatch between inferred and actual statevariables
        self.assertRaises(
            NineMLRuntimeError,
            Dynamics, name='cl', state_variables=['a'])

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


@restore_sys_path
def load_py_module(filename):
    """Takes the fully qualified path of a python file,
    loads it and returns the module object
    """

    if not os.path.exists(filename):
        print "CWD:", os.getcwd()
        raise NineMLRuntimeError('File does not exist %s' % filename)

    dirname, fname = os.path.split(filename)
    sys.path = [dirname] + sys.path

    module_name = fname.replace('.py', '')
    module_name_short = module_name

    module = __import__(module_name)
    return module


class TestableComponent(object):

    @classmethod
    def list_available(cls):
        """Returns a list of strings, of the available components"""
        compdir = LocationMgr.getComponentDir()
        comps = []
        for fname in os.listdir(compdir):
            fname, ext = os.path.splitext(fname)
            if not ext == '.py':
                continue
            if fname == '__init__':
                continue
            comps.append(fname)
        return comps

    functor_name = 'get_component'
    metadata_name = 'ComponentMetaData'

    def __str__(self):
        s = ('Testable Component from %s [MetaData=%s]' %
             (self.filename, self.has_metadata))
        return s

    def has_metadata(self):
        return self.metadata is not None

    def __call__(self):
        return self.component_functor()

    def __init__(self, filename):
        cls = TestableComponent

        # If we recieve a filename like 'iaf', that doesn't
        # end in '.py', then lets prepend the component directory
        # and append .py
        if not filename.endswith('.py'):
            compdir = LocationMgr.getComponentDir()
            filename = os.path.join(compdir, '%s.py' % filename)

        self.filename = filename
        self.mod = load_py_module(filename)

        # Get the component functor:
        if cls.functor_name not in self.mod.__dict__.keys():
            err = """Can't load TestableComponnet from %s""" % self.filename
            err += """Can't find required method: %s""" % cls.functor_name
            raise NineMLRuntimeError(err)

        self.component_functor = self.mod.__dict__[cls.functor_name]

        # Check the functor will actually return us an object:
        try:
            c = self.component_functor()
        except Exception, e:
            raise NineMLRuntimeError('component_functor() threw an exception:'
                                     '{}'.format(e))

        if not isinstance(c, Dynamics):
            raise NineMLRuntimeError('Functor does not return Component Class')

        # Try and get the meta-data
        self.metadata = None
        if cls.metadata_name in self.mod.__dict__.keys():
            self.metadata = self.mod.__dict__[cls.metadata_name]

    # Write is better tested in the round trip tests.
    # def test_write(self):
    


class ComponentClassQuery_test(unittest.TestCase):

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
