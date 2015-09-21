import unittest
from nineml.exceptions import NineMLMathParseError, NineMLRuntimeError
from nineml.abstraction import (On, OnCondition, OnEvent, OutputEvent,
                                      Regime, StateVariable)


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

    def test_accept_visitor(self):

        class TestVisitor(object):

            def visit(self, obj, **kwargs):
                return obj.accept_visitor(self, **kwargs)

            def visit_oncondition(self, component, **kwargs):
                return kwargs

        c = OnCondition(trigger='V>0')
        v = TestVisitor()

        self.assertEqual(
            v.visit(c, kwarg1='Hello', kwarg2='Hello2'),
            {'kwarg1': 'Hello', 'kwarg2': 'Hello2'}
        )

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


class OnEvent_test(unittest.TestCase):

    def test_Constructor(self):
        pass

    def test_accept_visitor(self):
        # Signature: name(self, visitor, **kwargs)
                # |VISITATION|


        class TestVisitor(object):

            def visit(self, obj, **kwargs):
                return obj.accept_visitor(self, **kwargs)

            def visit_onevent(self, component, **kwargs):
                return kwargs

        c = OnEvent('SP')
        v = TestVisitor()

        self.assertEqual(
            v.visit(c, kwarg1='Hello', kwarg2='Hello2'),
            {'kwarg1': 'Hello', 'kwarg2': 'Hello2'}
        )

    def test_src_port_name(self):

        self.assertRaises(NineMLRuntimeError, OnEvent, '1MyEvent1 ')
        self.assertRaises(NineMLRuntimeError, OnEvent, 'MyEvent1 2')
        self.assertRaises(NineMLRuntimeError, OnEvent, 'MyEvent1* ')

        self.assertEquals(OnEvent(' MyEvent1 ').src_port_name, 'MyEvent1')
        self.assertEquals(OnEvent(' MyEvent2').src_port_name, 'MyEvent2')


class Regime_test(unittest.TestCase):

    def test_Constructor(self):
        pass

    def test_accept_visitor(self):
        # Signature: name(self, visitor, **kwargs)
                # |VISITATION|

        class TestVisitor(object):

            def visit(self, obj, **kwargs):
                return obj.accept_visitor(self, **kwargs)

            def visit_regime(self, component, **kwargs):
                return kwargs

        c = Regime(name='R1')
        v = TestVisitor()

        self.assertEqual(
            v.visit(c, kwarg1='Hello', kwarg2='Hello2'),
            {'kwarg1': 'Hello', 'kwarg2': 'Hello2'}
        )

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

        self.assertEqual(Regime(name=' Hello ').name, 'Hello')
        self.assertEqual(Regime(name=' Hello2 ').name, 'Hello2')

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

    def test_accept_visitor(self):

        class TestVisitor(object):

            def visit(self, obj, **kwargs):
                return obj.accept_visitor(self, **kwargs)

            def visit_statevariable(self, component, **kwargs):
                return kwargs

        c = StateVariable('R1')
        v = TestVisitor()

        self.assertEqual(
            v.visit(c, kwarg1='Hello', kwarg2='Hello2'),
            {'kwarg1': 'Hello', 'kwarg2': 'Hello2'}
        )

    def test_name(self):
        # Signature: name
                # No Docstring

        self.assertRaises(NineMLRuntimeError, StateVariable, name='&Hello')
        self.assertRaises(NineMLRuntimeError, StateVariable, name='2Hello')

        self.assertEqual(StateVariable(name=' Hello ').name, 'Hello')
        self.assertEqual(StateVariable(name=' Hello2 ').name, 'Hello2')
