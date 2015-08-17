import unittest
from itertools import chain
from nineml.abstraction.dynamics import (
    Dynamics, Regime, On, OutputEvent)
from nineml.abstraction import Alias
from nineml.abstraction.ports import AnalogSendPort, AnalogReceivePort
from nineml.abstraction.expressions import reserved_identifiers


# Testing Skeleton for class: DynamicsClonerPrefixNamespace
class DynamicsRequiredDefinitions_test(unittest.TestCase):

    def setUp(self):

        self.a = Dynamics(
            name='A',
            aliases=['A1:=P1', 'A2 := ARP2', 'A3 := SV1'],
            regimes=[
                Regime('dSV1/dt = -SV1 / (P2*t)',
                       'dSV2/dt = A2/t + A3/t + ARP1/t',
                       name='R1',
                       transitions=On('input', 'SV1 = SV1 + 1'))],
            analog_ports=[AnalogReceivePort('ARP1'),
                          AnalogReceivePort('ARP2'),
                          AnalogSendPort('A1'),
                          AnalogSendPort('A2')],
            parameters=['P1', 'P2']
        )

        self.b = Dynamics(
            name='B',
            aliases=['A1:=P1', 'A2 := ARP1 + SV2', 'A3 := SV1'],
            regimes=[
                Regime(
                    'dSV1/dt = -SV1 / (P2*t)',
                    'dSV2/dt = SV1 / (ARP1*t) + SV2 / (P1*t)',
                    aliases=[Alias('A1', '2*P1')],
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
        atoms_to_find = list(set(expression.rhs_atoms) - reserved_identifiers)
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
        for component_class in (self.a, self.b):
            for regime in component_class.regimes:
                for td in regime.time_derivatives:
                    self._test_expression_requirements(td)
                for oc in regime.on_conditions:
                    self._test_expression_requirements(oc.trigger)
                    for sa in oc.state_assignments:
                        self._test_expression_requirements(sa)
                for oe in regime.on_events:
                    for sa in oe.state_assignments:
                        self._test_expression_requirements(sa)
