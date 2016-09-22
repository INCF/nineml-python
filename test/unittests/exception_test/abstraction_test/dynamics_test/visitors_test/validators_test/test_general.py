import unittest
from nineml.abstraction.dynamics.visitors.validators.general import (RegimeGraphDynamicsValidator, TimeDerivativesAreDeclaredDynamicsValidator, StateAssignmentsAreOnStateVariablesDynamicsValidator)
from nineml.utils.testing.comprehensive import instances_of_all_types
from nineml.exceptions import (NineMLRuntimeError)


class TestRegimeGraphDynamicsValidatorExceptions(unittest.TestCase):

    def test___init___ninemlruntimeerror(self):
        """
        line #: 120
        message: Transition graph contains islands

        context:
        --------
    def __init__(self, component_class, **kwargs):  # @UnusedVariable
        BaseDynamicsValidator.__init__(
            self, require_explicit_overrides=False, **kwargs)
        self.connected_regimes_from_regime = defaultdict(set)
        self.regimes = set
        self.visit(component_class)
        def add_connected_regimes_recursive(regime, connected):  # @IgnorePep8
            connected.add(regime)
            for r in self.connected_regimes_from_regime[regime]:
                if r not in connected:
                    add_connected_regimes_recursive(r, connected)
        connected = set()
        if self.regimes:
            add_connected_regimes_recursive(self.regimes[0], connected)
            if len(connected) < len(self.regimes):
        """

        regimegraphdynamicsvalidator = instances_of_all_types['RegimeGraphDynamicsValidator']
        self.assertRaises(
            NineMLRuntimeError,
            regimegraphdynamicsvalidator.__init__,
            component_class=None)


class TestTimeDerivativesAreDeclaredDynamicsValidatorExceptions(unittest.TestCase):

    def test___init___ninemlruntimeerror(self):
        """
        line #: 35
        message: StateVariable '{}' not declared

        context:
        --------
    def __init__(self, component_class, **kwargs):  # @UnusedVariable
        BaseDynamicsValidator.__init__(
            self, require_explicit_overrides=False, **kwargs)
        self.sv_declared = []
        self.time_derivatives_used = []
        self.visit(component_class)
        for td in self.time_derivatives_used:
            if td not in self.sv_declared:
        """

        timederivativesaredeclareddynamicsvalidator = instances_of_all_types['TimeDerivativesAreDeclaredDynamicsValidator']
        self.assertRaises(
            NineMLRuntimeError,
            timederivativesaredeclareddynamicsvalidator.__init__,
            component_class=None)


class TestStateAssignmentsAreOnStateVariablesDynamicsValidatorExceptions(unittest.TestCase):

    def test___init___ninemlruntimeerror(self):
        """
        line #: 60
        message: Not Assigning to state-variable: {}

        context:
        --------
    def __init__(self, component_class, **kwargs):  # @UnusedVariable
        BaseDynamicsValidator.__init__(
            self, require_explicit_overrides=False, **kwargs)
        self.sv_declared = []
        self.state_assignments_lhs = []
        self.visit(component_class)
        for sa in self.state_assignments_lhs:
            if sa not in self.sv_declared:
        """

        stateassignmentsareonstatevariablesdynamicsvalidator = instances_of_all_types['StateAssignmentsAreOnStateVariablesDynamicsValidator']
        self.assertRaises(
            NineMLRuntimeError,
            stateassignmentsareonstatevariablesdynamicsvalidator.__init__,
            component_class=None)
