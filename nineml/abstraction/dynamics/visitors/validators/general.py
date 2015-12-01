"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from collections import defaultdict
from nineml.exceptions import NineMLRuntimeError
from nineml.utils import assert_no_duplicates
from ....componentclass.visitors.validators import (
    AliasesAreNotRecursiveComponentValidator,
    NoUnresolvedSymbolsComponentValidator,
    NoDuplicatedObjectsComponentValidator,
    CheckNoLHSAssignmentsToMathsNamespaceComponentValidator,
    DimensionalityComponentValidator)
from . import BaseDynamicsValidator
from nineml import units as un


class TimeDerivativesAreDeclaredDynamicsValidator(
        BaseDynamicsValidator):

    """ Check all variables used in TimeDerivative blocks are defined
        as  StateVariables.
    """

    def __init__(self, component_class):
        BaseDynamicsValidator.__init__(
            self, require_explicit_overrides=False)
        self.sv_declared = []
        self.time_derivatives_used = []
        self.visit(component_class)
        for td in self.time_derivatives_used:
            if td not in self.sv_declared:
                raise NineMLRuntimeError(
                    "StateVariable '{}' not declared".format(td))

    def action_statevariable(self, state_variable, **kwargs):  # @UnusedVariable @IgnorePep8
        self.sv_declared.append(state_variable.name)

    def action_timederivative(self, timederivative, **kwargs):  # @UnusedVariable @IgnorePep8
        self.time_derivatives_used.append(
            timederivative.variable)


class StateAssignmentsAreOnStateVariablesDynamicsValidator(
        BaseDynamicsValidator):

    """ Check that we only attempt to make StateAssignments to state-variables.
    """

    def __init__(self, component_class):
        BaseDynamicsValidator.__init__(
            self, require_explicit_overrides=False)
        self.sv_declared = []
        self.state_assignments_lhs = []
        self.visit(component_class)
        for sa in self.state_assignments_lhs:
            if sa not in self.sv_declared:
                raise NineMLRuntimeError(
                    "Not Assigning to state-variable: {}".format(sa))

    def action_statevariable(self, state_variable, **kwargs):  # @UnusedVariable @IgnorePep8
        self.sv_declared.append(state_variable.name)

    def action_stateassignment(self, state_assignment, **kwargs):  # @UnusedVariable @IgnorePep8
        self.state_assignments_lhs.append(state_assignment.lhs)


class AliasesAreNotRecursiveDynamicsValidator(
        AliasesAreNotRecursiveComponentValidator,
        BaseDynamicsValidator):

    """Check that aliases are not self-referential"""

    pass


class NoUnresolvedSymbolsDynamicsValidator(
        NoUnresolvedSymbolsComponentValidator,
        BaseDynamicsValidator):
    """
    Check that aliases and timederivatives are defined in terms of other
    parameters, aliases, statevariables and ports
    """

    def action_analogreceiveport(self, port, **kwargs):  # @UnusedVariable @IgnorePep8
        self.available_symbols.append(port.name)

    def action_analogreduceport(self, port, **kwargs):  # @UnusedVariable @IgnorePep8
        self.available_symbols.append(port.name)

    def action_statevariable(self, state_variable, **kwargs):  # @UnusedVariable @IgnorePep8
        self.add_symbol(symbol=state_variable.name)

    def action_timederivative(self, time_derivative, **kwargs):  # @UnusedVariable @IgnorePep8
        self.time_derivatives.append(time_derivative)

    def action_stateassignment(self, state_assignment, **kwargs):  # @UnusedVariable @IgnorePep8
        self.state_assignments.append(state_assignment)


class RegimeGraphDynamicsValidator(BaseDynamicsValidator):

    def __init__(self, component_class):
        BaseDynamicsValidator.__init__(
            self, require_explicit_overrides=False)
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
                raise NineMLRuntimeError("Transition graph contains islands")
            elif len(connected) > len(self.regimes):
                for r1 in connected:
                    for r2 in connected:
                        if r1.name == r2.name:
                            r1 == r2
                assert False

    def action_componentclass(self, component_class):
        self.regimes = list(component_class.regimes)

    def action_regime(self, regime):  # @UnusedVariable
        for transition in regime.transitions:
            regime == transition.target_regime
            self.connected_regimes_from_regime[regime].add(
                transition.target_regime)
            self.connected_regimes_from_regime[transition.target_regime].add(
                regime)


class NoDuplicatedObjectsDynamicsValidator(
        NoDuplicatedObjectsComponentValidator,
        BaseDynamicsValidator):

    def action_regime(self, regime, **kwargs):  # @UnusedVariable
        self.all_objects.append(regime)

    def action_statevariable(self, state_variable, **kwargs):  # @UnusedVariable @IgnorePep8
        self.all_objects.append(state_variable)

    def action_analogsendport(self, port, **kwargs):  # @UnusedVariable
        self.all_objects.append(port)

    def action_analogreceiveport(self, port, **kwargs):  # @UnusedVariable
        self.all_objects.append(port)

    def action_analogreduceport(self, port, **kwargs):  # @UnusedVariable
        self.all_objects.append(port)

    def action_eventsendport(self, port, **kwargs):  # @UnusedVariable
        self.all_objects.append(port)

    def action_eventreceiveport(self, port, **kwargs):  # @UnusedVariable
        self.all_objects.append(port)

    def action_outputevent(self, event_out, **kwargs):  # @UnusedVariable
        self.all_objects.append(event_out)

    def action_stateassignment(self, assignment, **kwargs):  # @UnusedVariable
        self.all_objects.append(assignment)

    def action_timederivative(self, time_derivative, **kwargs):  # @UnusedVariable @IgnorePep8
        self.all_objects.append(time_derivative)

    def action_trigger(self, trigger, **kwargs):  # @UnusedVariable
        self.all_objects.append(trigger)

    def action_oncondition(self, on_condition, **kwargs):  # @UnusedVariable
        self.all_objects.append(on_condition)

    def action_onevent(self, on_event, **kwargs):  # @UnusedVariable
        self.all_objects.append(on_event)


class RegimeOnlyHasOneHandlerPerEventDynamicsValidator(
        BaseDynamicsValidator):

    def __init__(self, component_class):
        BaseDynamicsValidator.__init__(
            self, require_explicit_overrides=False)
        self.visit(component_class)

    def action_regime(self, regime, **kwargs):  # @UnusedVariable
        event_triggers = [on_event.src_port_name
                          for on_event in regime.on_events]
        assert_no_duplicates(event_triggers)


class CheckNoLHSAssignmentsToMathsNamespaceDynamicsValidator(
        CheckNoLHSAssignmentsToMathsNamespaceComponentValidator,
        BaseDynamicsValidator):

    """
    This class checks that there is not a mathematical symbols, (e.g. pi, e)
    on the left-hand-side of an equation
    """

    def action_statevariable(self, state_variable, **kwargs):  # @UnusedVariable @IgnorePep8
        self.check_lhssymbol_is_valid(state_variable.name)

    def action_stateassignment(self, assignment, **kwargs):  # @UnusedVariable
        self.check_lhssymbol_is_valid(assignment.lhs)

    def action_timederivative(self, time_derivative, **kwargs):  # @UnusedVariable @IgnorePep8
        self.check_lhssymbol_is_valid(time_derivative.variable)


class DimensionalityDynamicsValidator(DimensionalityComponentValidator,
                                      BaseDynamicsValidator):

    def __init__(self, component_class):
        super(DimensionalityDynamicsValidator,
              self).__init__(component_class)

    def action_timederivative(self, timederivative, **kwargs):  # @UnusedVariable @IgnorePep8
        dimension = self._get_dimensions(timederivative)
        sv = self.component_class.state_variable(timederivative.variable)
        self._compare_dimensionality(
            dimension, sv.dimension / un.time, timederivative,
            'time derivative of ' + sv.name)

    def action_stateassignment(self, stateassignment, **kwargs):  # @UnusedVariable @IgnorePep8
        dimension = self._get_dimensions(stateassignment)
        sv = self.component_class.state_variable(stateassignment.variable)
        self._compare_dimensionality(
            dimension, sv.dimension, stateassignment, 'state variable ' +
            sv.name)

    def action_analogsendport(self, port, **kwargs):  # @UnusedVariable
        self._check_send_port(port)

    def action_trigger(self, trigger, **kwargs):  # @UnusedVariable
        self._flatten_dims(trigger.rhs, trigger)
