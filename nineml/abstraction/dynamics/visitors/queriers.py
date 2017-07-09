from collections import defaultdict
from itertools import chain
import sympy
from nineml.abstraction.expressions.base import (
    reserved_identifiers)
from .base import DynamicsActionVisitor
from ...componentclass.visitors.queriers import (
    ComponentClassInterfaceInferer, ComponentElementFinder,
    ComponentRequiredDefinitions, ComponentExpressionExtractor,
    ComponentDimensionResolver)
from ..base import Dynamics
from ..regimes import Regime
from nineml.base import BaseNineMLVisitor


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


class DynamicsHasRandomProcessQuerier(DynamicsActionVisitor):

    def __init__(self):
        super(DynamicsHasRandomProcessQuerier, self).__init__(
            require_explicit_overrides=False)
        self._found = False

    def visit_componentclass(self, component_class):
        super(DynamicsHasRandomProcessQuerier, self).visit_componentclass(
            component_class)
        return self._found

    def action_stateassignment(self, stateassignment):
        if list(stateassignment.rhs_random_distributions):
            self._found = True


class ExpandExpressionsQuerier(BaseNineMLVisitor):
    """
    A querier that expands all mathematical expressions into terms of inputs,
    (i.e. analog receive/reduce ports and parameters), constants and
    reserved identifiers

    Parameters
    ----------
    component_class : Dynamics
        The Dynamics class to expand the expressions of
    new_name : str
        The name for the new dynamics object
    """

    def __init__(self, component_class, new_name):
        self.component_class = component_class
        self.new_name = new_name
        self.expanded_exprs = defaultdict(dict)
        self.expanded_regimes = {}
        self.inputs = reserved_identifiers + [
            sympy.Symbol(n) for n in chain(
                component_class.parameter_names,
                component_class.analog_receive_port_names,
                component_class.analog_reduce_port_names,
                component_class.constant_names)]
        self.visit(component_class)

    @property
    def expanded(self):
        """
        Returns a clone of the component class passed to the __init__ method
        with all expressions defined in terms of inputs to the class (i.e.
        parameters, constants, analog ports or reserved symbols)
        """
        return Dynamics(
            name=self.new_name,
            parameters=(p.clone() for p in self.component_class.parameters),
            analog_ports=(p.clone()
                          for p in self.component_class.analog_ports),
            event_ports=(p.clone for p in self.component_class.event_ports),
            state_variables=(sv.clone()
                             for sv in self.component_class.state_variables),
            constants=(c.clone() for c in self.component_class.constants),
            regimes=(self.expanded_regimes[n]
                     for n in self.component_class.regime_names),
            aliases=(self.expanded_exprs[None][n]
                     for n in self.component_class.alias_names
                     if n in self.component_class.analog_send_port_names))

    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        if isinstance(self.context.parent, Regime):
            regime = self.context.parent
        else:
            regime = None
        self.expand(alias, regime=regime)

    def action_regime(self, regime, **kwargs):  # @UnusedVariable
        self.expanded_regimes[regime.name] = Regime(
            name=regime.name,
            time_derivatives=(self.expand(td, regime=regime)
                              for td in regime.time_derivatives),
            transitions=(t.clone() for t in regime.transitions),
            aliases=(self.expand(a, regime=regime) for a in regime.aliases))

    def expand(self, expr, regime=None):
        # Get key to store the expression under. Aliases that are not part of
        # a regime use a key == None
        regime_name = regime.name if regime is not None else None
        try:
            return self.expanded_exprs[regime_name][expr.key]
        except KeyError:
            expanded_expr = expr.clone()
            for sym in expr.rhs_symbols:
                # Expand all symbols that are not inputs to the Dynamics class
                if sym not in self.inputs:
                    expanded_expr.rhs.subs(sym, self.expand(sym, regime))
            expanded_expr.simplify()
            self.expanded_exprs[regime_name][expr.key] = expanded_expr
            return expanded_expr
