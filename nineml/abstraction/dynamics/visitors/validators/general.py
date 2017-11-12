"""
docstring needed

:copyright: Copyright 2010-2017 by the NineML Python team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from __future__ import division
from future.utils import itervalues
from collections import defaultdict
from nineml.exceptions import NineMLUsageError
from nineml.utils import assert_no_duplicates
from ....componentclass.visitors.validators import (
    AliasesAreNotRecursiveComponentValidator,
    NoUnresolvedSymbolsComponentValidator,
    CheckNoLHSAssignmentsToMathsNamespaceComponentValidator,
    DimensionalityComponentValidator)
from ..base import BaseDynamicsVisitor
import nineml.units as un


class TimeDerivativesAreDeclaredDynamicsValidator(BaseDynamicsVisitor):

    """ Check all variables used in TimeDerivative blocks are defined
        as  StateVariables.
    """

    def __init__(self, component_class, **kwargs):  # @UnusedVariable
        BaseDynamicsVisitor.__init__(self)
        self.sv_declared = []
        self.time_derivatives_used = []
        self.visit(component_class)
        for td in self.time_derivatives_used:
            if td not in self.sv_declared:
                raise NineMLUsageError(
                    "StateVariable '{}' not declared".format(td))

    def action_statevariable(self, state_variable, **kwargs):  # @UnusedVariable @IgnorePep8
        self.sv_declared.append(state_variable.name)

    def action_timederivative(self, timederivative, **kwargs):  # @UnusedVariable @IgnorePep8
        self.time_derivatives_used.append(
            timederivative.variable)

    def default_action(self, obj, nineml_cls, **kwargs):
        pass


class StateAssignmentsAreOnStateVariablesDynamicsValidator(
        BaseDynamicsVisitor):

    """ Check that we only attempt to make StateAssignments to state-variables.
    """

    def __init__(self, component_class, **kwargs):  # @UnusedVariable
        BaseDynamicsVisitor.__init__(self)
        self.sv_declared = []
        self.state_assignments_lhs = []
        self.visit(component_class)
        for sa in self.state_assignments_lhs:
            if sa not in self.sv_declared:
                raise NineMLUsageError(
                    "Not Assigning to state-variable: {}".format(sa))

    def action_statevariable(self, state_variable, **kwargs):  # @UnusedVariable @IgnorePep8
        self.sv_declared.append(state_variable.name)

    def action_stateassignment(self, state_assignment, **kwargs):  # @UnusedVariable @IgnorePep8
        self.state_assignments_lhs.append(state_assignment.lhs)

    def default_action(self, obj, nineml_cls, **kwargs):
        pass


class AliasesAreNotRecursiveDynamicsValidator(
        AliasesAreNotRecursiveComponentValidator,
        BaseDynamicsVisitor):

    """Check that aliases are not self-referential"""

    def action_dynamics(self, dynamics, **kwargs):
        return self.action_componentclass(dynamics, **kwargs)


class NoUnresolvedSymbolsDynamicsValidator(
        NoUnresolvedSymbolsComponentValidator,
        BaseDynamicsVisitor):
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


class RegimeGraphDynamicsValidator(BaseDynamicsVisitor):

    def __init__(self, component_class, **kwargs):  # @UnusedVariable
        BaseDynamicsVisitor.__init__(self)
        self.connected_regimes_from_regime = defaultdict(set)
        self.component_class = component_class
        self.regimes = {}
        self.visit(component_class)
        self.connected = set()
        if self.regimes:
            first_regime = next(iter(itervalues(self.regimes)))
            # Recursively add all regimes connected to the first regime
            self._add_connected_regimes_recursive(first_regime)
            if len(self.connected) < len(self.regimes):
                # FIXME: This should probably be a warning not an error
                raise NineMLUsageError(
                    "Transition graph of {} contains islands: {} regimes "
                    "('{}') and {} connected ('{}'):\n\n{}".format(
                        component_class,
                        len(self.regimes),
                        "', '".join(r.name for r in self.regimes),
                        len(self.connected),
                        "', '".join(r.name for r in self.connected),
                        self.connected_regimes_from_regime))
            elif len(self.connected) > len(self.regimes):
                assert False

    def action_regime(self, regime, **kwargs):  # @UnusedVariable
        self.regimes[regime.id] = regime
        for transition in regime.transitions:
            self.connected_regimes_from_regime[regime.id].add(
                transition.target_regime.id)
            self.connected_regimes_from_regime[
                transition.target_regime.id].add(regime.id)

    def _add_connected_regimes_recursive(self, regime):  # @IgnorePep8
        self.connected.add(regime.id)
        for id_ in self.connected_regimes_from_regime[regime.id]:
            if id_ not in self.connected:
                self._add_connected_regimes_recursive(self.regimes[id_])

    def default_action(self, obj, nineml_cls, **kwargs):
        pass


class RegimeOnlyHasOneHandlerPerEventDynamicsValidator(BaseDynamicsVisitor):

    def __init__(self, component_class, **kwargs):  # @UnusedVariable
        BaseDynamicsVisitor.__init__(self)
        self.visit(component_class)

    def action_regime(self, regime, **kwargs):  # @UnusedVariable
        event_triggers = [on_event.src_port_name
                          for on_event in regime.on_events]
        assert_no_duplicates(event_triggers)

    def default_action(self, obj, nineml_cls, **kwargs):
        pass


class CheckNoLHSAssignmentsToMathsNamespaceDynamicsValidator(
        CheckNoLHSAssignmentsToMathsNamespaceComponentValidator,
        BaseDynamicsVisitor):

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

    def default_action(self, obj, nineml_cls, **kwargs):
        pass


class DimensionalityDynamicsValidator(DimensionalityComponentValidator,
                                      BaseDynamicsVisitor):

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

    def default_action(self, obj, nineml_cls, **kwargs):
        pass
