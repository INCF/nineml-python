import unittest
from itertools import chain
from nineml.abstraction_layer.dynamics import (
    DynamicsClass, Regime, On, OutputEvent)
from nineml.abstraction_layer.ports import AnalogSendPort, AnalogReceivePort


# Testing Skeleton for class: DynamicsClonerPrefixNamespace
class DynamicsRequiredDefinitions_test(unittest.TestCase):

    def setUp(self):

        self.a = DynamicsClass(
            name='A',
            aliases=['A1:=P1', 'A2 := ARP2', 'A3 := SV1'],
            regimes=[
                Regime('dSV1/dt = -SV1 / P2',
                       'dSV2/dt = A2 + A3 + ARP1',
                       name='R1',
                       transitions=On('input', 'SV1 = SV1 + 1'))],
            analog_ports=[AnalogReceivePort('ARP1'),
                          AnalogReceivePort('ARP2'),
                          AnalogSendPort('A1'),
                          AnalogSendPort('A2')],
            parameters=['P1', 'P2']
        )

        self.b = DynamicsClass(
            name='B',
            aliases=['A1:=P1', 'A2 := ARP1 + SV2', 'A3 := SV1'],
            regimes=[
                Regime(
                    'dSV1/dt = -SV1 / P2',
                    'dSV2/dt = SV1 / ARP1 + SV2 / P1',
                    transitions=[On('SV1 > P1', do=[OutputEvent('emit')]),
                                 On('spikein', do=[OutputEvent('emit')])],
                    name='R1',
                ),
                Regime(name='R2', transitions=On('SV1 > 1', to='R1'))
            ],
            analog_ports=[AnalogReceivePort('ARP1'), AnalogReceivePort('ARP2'),
                          AnalogSendPort('A1'), AnalogSendPort('A2')],
            parameters=['P1', 'P2']
        )

    def _test_expression_requirements(self, expression):
        required = self.a.required_for(expression)
        # Check for duplicates in expression names
        self.assertEqual(len(list(required.expression_names)),
                         len(set(required.expression_names)),
                         "Expresions are duplicated in those required for {}: "
                         "{}".format(expression, required.expression_names))
        # Check all atoms are accounted for
        atoms_to_find = list(expression.rhs_atoms)
        atoms_found = set()
        while atoms_to_find:
            atom = atoms_to_find.pop()
            if atom in atoms_found:
                pass
            elif atom in chain(required.parameter_names,
                               required.port_names,
                               required.constant_names,
                               required.state_variable_names):
                atoms_found.add(atom)
            elif atom in required.expression_names:
                atoms_found.add(atom)
                expr = next(e for e in required.expressions if e.name == atom)
                atoms_to_find.extend(expr.rhs_atoms)
            else:
                self.fail("'{}' atom was not found in required definitions for"
                          " {}: {}"
                          .format(atom, expression, repr(required)))

    def test_required_definitions(self):
        for componentclass in (self.a, self.b):
            for regime in componentclass.regimes:
                for td in regime.time_derivatives:
                    self._test_expression_requirements(td)
                for oc in regime.on_conditions:
                    self._test_expression_requirements(oc.trigger)
                    for sa in oc.state_assignments:
                        self._test_expression_requirements(sa)
                for oe in regime.on_events:
                    for sa in oe.state_assignments:
                        self._test_expression_requirements(sa)
