import unittest
from nineml.abstraction import (
    Parameter, Dynamics, Alias, StateVariable,
    Regime, TimeDerivative, OnCondition)
from nineml.serialization import ext_to_format
from nineml.exceptions import NineMLSerializerNotImportedError
import logging
import sys
import nineml
from tempfile import mkstemp


logger = logging.getLogger('NineML')
logger.setLevel(logging.ERROR)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class TestPreserveIndices(unittest.TestCase):

    def setUp(self):
        self.parameters = ['P4', 'P1', 'P3', 'P5', 'P2']
        self.state_variables = ['SV3', 'SV5', 'SV4', 'SV2', 'SV1']
        self.regimes = ['R2', 'R3', 'R1']
        self.time_derivatives = {'R1': ['SV5', 'SV1', 'SV4', 'SV3', 'SV2'],
                                 'R2': ['SV2', 'SV4'],
                                 'R3': ['SV4', 'SV2', 'SV1']}
        self.aliases = ['A4', 'A3', 'A1', 'A2']

        # Create a dynamics object with elements in a particular order
        self.d = Dynamics(
            name='d',
            parameters=[Parameter(p) for p in self.parameters],
            state_variables=[StateVariable(sv) for sv in self.state_variables],
            regimes=[Regime(name=r,
                            time_derivatives=[
                                TimeDerivative(td, '{}/t'.format(td))
                                for td in self.time_derivatives[r]],
                            transitions=[
                                OnCondition(
                                    'SV1 > P5',
                                    target_regime_name=self.regimes[
                                        self.regimes.index(r) - 1])])
                     for r in self.regimes],
            aliases=[Alias(a, 'P{}'.format(i + 1))
                     for i, a in enumerate(self.aliases)])

    def test_clone(self):
        clone_d = self.d.clone()
        self._test_indices(clone_d)

    def test_serialization(self):
        for ext in ext_to_format:
            fname = mkstemp(suffix=ext)[1]
            try:
                self.d.write(fname)
            except NineMLSerializerNotImportedError:
                continue
            reread_d = nineml.read(fname + '#d')
            self._test_indices(reread_d)

    def _test_indices(self, dyn):
        # Set indices of parameters in non-ascending order so that they
        # can be differentiated from indices on read.
        for i, p in enumerate(self.parameters):
            self.assertEqual(dyn.index_of(dyn.parameter(p)), i)
        for i, sv in enumerate(self.state_variables):
            self.assertEqual(dyn.index_of(dyn.state_variable(sv)), i)
        for i, r in enumerate(self.regimes):
            self.assertEqual(dyn.index_of(dyn.regime(r)), i)
        for r, tds in self.time_derivatives.iteritems():
            regime = dyn.regime(r)
            for i, td in enumerate(tds):
                self.assertEquals(
                    regime.index_of(regime.time_derivative(td)), i)
        for i, a in enumerate(self.aliases):
            self.assertEqual(dyn.index_of(dyn.alias(a)), i)
