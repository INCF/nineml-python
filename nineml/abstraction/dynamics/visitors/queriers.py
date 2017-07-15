from itertools import chain
import sympy
from .base import DynamicsActionVisitor
from ...componentclass.visitors.queriers import (
    ComponentClassInterfaceInferer, ComponentElementFinder,
    ComponentRequiredDefinitions, ComponentExpressionExtractor,
    ComponentDimensionResolver)
from nineml.base import BaseNineMLVisitor
from nineml.abstraction.expressions import reserved_symbols
from .modifiers import DynamicsSubstituteAliases
from nineml.exceptions import NineMLStopVisitException
from sympy.polys.polyerrors import PolynomialError


class DynamicsInterfaceInferer(ComponentClassInterfaceInferer,
                               DynamicsActionVisitor):

    """ Used to infer output |EventPorts|, |StateVariables| & |Parameters|."""

    def __init__(self, dynamicsclass):
        self.state_variable_names = set()
        super(DynamicsInterfaceInferer, self).__init__(dynamicsclass)

    def action_statevariable(self, state_variable):
        self.declared_symbols.add(state_variable.name)

    def action_outputevent(self, event_out):
        self.event_out_port_names.add(event_out.port_name)

    def action_onevent(self, on_event):
        self.input_event_port_names.add(on_event.src_port_name)

    def action_analogreceiveport(self, analog_receive_port):
        self.declared_symbols.add(analog_receive_port.name)

    def action_analogreduceport(self, analog_reduce_port):
        self.declared_symbols.add(analog_reduce_port.name)

    def action_stateassignment(self, assignment):
        inferred_sv = assignment.lhs
        self.declared_symbols.add(inferred_sv)
        self.state_variable_names.add(inferred_sv)
        self.atoms.update(assignment.rhs_atoms)

    def action_timederivative(self, time_derivative):
        inferred_sv = time_derivative.variable
        self.state_variable_names.add(inferred_sv)
        self.declared_symbols.add(inferred_sv)
        self.atoms.update(time_derivative.rhs_atoms)

    def action_trigger(self, trigger):
        self.atoms.update(trigger.rhs_atoms)


class DynamicsRequiredDefinitions(ComponentRequiredDefinitions,
                                  DynamicsActionVisitor):

    def __init__(self, component_class, expressions):
        DynamicsActionVisitor.__init__(self, require_explicit_overrides=False)
        self.state_variables = set()
        ComponentRequiredDefinitions.__init__(self, component_class,
                                              expressions)

    def __repr__(self):
        return ("State-variables: {}\n"
                .format(', '.join(self.state_variable_names)) +
                super(DynamicsRequiredDefinitions, self).__repr__())

    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        # Check to see if the alias is a top level alias, and not nested within
        # a regime
        if alias in self.component_class.aliases:
            super(DynamicsRequiredDefinitions, self).action_alias(alias,
                                                                  **kwargs)

    def action_statevariable(self, statevariable, **kwargs):  # @UnusedVariable
        if self._is_required(statevariable):
            self.state_variables.add(statevariable)

    @property
    def state_variable_names(self):
        return (r.name for r in self.state_variables)


class DynamicsElementFinder(ComponentElementFinder, DynamicsActionVisitor):

    def __init__(self, element):
        DynamicsActionVisitor.__init__(self, require_explicit_overrides=True)
        ComponentElementFinder.__init__(self, element)

    def action_regime(self, regime, **kwargs):  # @UnusedVariable
        if self.element == regime:
            self._found()

    def action_statevariable(self, state_variable, **kwargs):  # @UnusedVariable @IgnorePep8
        if self.element == state_variable:
            self._found()

    def action_analogsendport(self, port, **kwargs):  # @UnusedVariable
        if self.element == port:
            self._found()

    def action_analogreceiveport(self, port, **kwargs):  # @UnusedVariable
        if self.element == port:
            self._found()

    def action_analogreduceport(self, port, **kwargs):  # @UnusedVariable
        if self.element == port:
            self._found()

    def action_eventsendport(self, port, **kwargs):  # @UnusedVariable
        if self.element == port:
            self._found()

    def action_eventreceiveport(self, port, **kwargs):  # @UnusedVariable
        if self.element == port:
            self._found()

    def action_outputevent(self, event_out, **kwargs):  # @UnusedVariable
        if self.element == event_out:
            self._found()

    def action_stateassignment(self, assignment, **kwargs):  # @UnusedVariable
        if self.element == assignment:
            self._found()

    def action_timederivative(self, time_derivative, **kwargs):  # @UnusedVariable @IgnorePep8
        if self.element == time_derivative:
            self._found()

    def action_trigger(self, trigger, **kwargs):  # @UnusedVariable
        if self.element == trigger:
            self._found()

    def action_oncondition(self, on_condition, **kwargs):  # @UnusedVariable
        if self.element == on_condition:
            self._found()

    def action_onevent(self, on_event, **kwargs):  # @UnusedVariable
        if self.element == on_event:
            self._found()


class DynamicsExpressionExtractor(ComponentExpressionExtractor,
                                  DynamicsActionVisitor):

    def __init__(self):
        DynamicsActionVisitor.__init__(self,
                                             require_explicit_overrides=True)
        ComponentExpressionExtractor.__init__(self)

    def action_stateassignment(self, assignment, **kwargs):  # @UnusedVariable
        self.expressions.append(assignment.rhs)

    def action_timederivative(self, time_derivative, **kwargs):  # @UnusedVariable @IgnorePep8
        self.expressions.append(time_derivative.rhs)

    def action_trigger(self, trigger, **kwargs):  # @UnusedVariable
        self.expressions.append(trigger.rhs)


class DynamicsDimensionResolver(ComponentDimensionResolver,
                                DynamicsActionVisitor):

    def action_statevariable(self, statevariable):
        self._flatten(statevariable)


class DynamicsHasRandomProcess(DynamicsActionVisitor):

    def __init__(self):
        super(DynamicsHasRandomProcess, self).__init__(
            require_explicit_overrides=False)
        self._found = False

    def visit_componentclass(self, component_class):
        super(DynamicsHasRandomProcess, self).visit_componentclass(
            component_class)
        return self._found

    def action_stateassignment(self, stateassignment):
        if list(stateassignment.rhs_random_distributions):
            self._found = True


class DynamicsIsLinear(BaseNineMLVisitor):
    """
    Checks to see whether the dynamics class is linear or nonlinear

    Parameters
    ----------
    dynamics : Dynamics
        The dynamics element to check linearity of
    outputs : list(str) | None
        List of outputs that are relevant to the check. For example, if there
        is an analog send port on a synapse that is not connected to the cell
        then any alias that maps the state variable/inputs to the analog send
        port is not relevant.
    """

    def __init__(self, dynamics, outputs=None):
        super(DynamicsIsLinear, self).__init__()
        self._result = True
        self.outputs = (set(dynamics.analog_send_port_names)
                        if outputs is None else outputs)
        substituted = dynamics.clone()
        DynamicsSubstituteAliases(substituted)
        self.input_and_states = [
            sympy.Symbol(i) for i in chain(
                substituted.state_variable_names,
                substituted.analog_receive_port_names,
                substituted.analog_reduce_port_names)]
        try:
            self.visit(substituted)
        except NineMLStopVisitException:
            pass

    @property
    def result(self):
        return self._result

    def action_dynamics(self, dynamics, **kwargs):  # @UnusedVariable
        # Dynamics are piecewise
        if dynamics.num_regimes > 1:
            self._report_nonlinear()

    def action_oncondition(self, on_condition, **kwargs):  # @UnusedVariable
        # Dynamics are piecewise
        if on_condition.num_state_assignments:
            self._report_nonlinear()

    def action_stateassignment(self, state_assignment, **kwargs):  # @UnusedVariable @IgnorePep8
        self._check_linear(state_assignment)

    def action_timederivative(self, time_derivative, **kwargs):  # @UnusedVariable @IgnorePep8
        self._check_linear(time_derivative)

    def action_alias(self, alias, **kwargs):  # @UnusedVariable @IgnorePep8
        if alias.name in self.outputs:
            self._check_linear(alias)

    def _is_linear(self, expr):
        try:
            # Check to see whether expression represents linear dynamics
            return sympy.poly(expr.rhs, *self.input_and_states).is_linear
        except PolynomialError:
            # Return false if not a polynomial
            return False

    def _check_linear(self, expr):
        if not self._is_linear(expr):
            self._report_nonlinear()

    def _report_nonlinear(self):
        self._result = False
        raise NineMLStopVisitException()
