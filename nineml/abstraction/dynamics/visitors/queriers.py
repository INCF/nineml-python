from .base import DynamicsActionVisitor
from ...componentclass.visitors.queriers import (
    ComponentClassInterfaceInferer, ComponentElementFinder,
    ComponentRequiredDefinitions, ComponentExpressionExtractor,
    ComponentDimensionResolver)


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
        if self.element is regime:
            self._found()

    def action_statevariable(self, state_variable, **kwargs):  # @UnusedVariable @IgnorePep8
        if self.element is state_variable:
            self._found()

    def action_analogsendport(self, port, **kwargs):  # @UnusedVariable
        if self.element is port:
            self._found()

    def action_analogreceiveport(self, port, **kwargs):  # @UnusedVariable
        if self.element is port:
            self._found()

    def action_analogreduceport(self, port, **kwargs):  # @UnusedVariable
        if self.element is port:
            self._found()

    def action_eventsendport(self, port, **kwargs):  # @UnusedVariable
        if self.element is port:
            self._found()

    def action_eventreceiveport(self, port, **kwargs):  # @UnusedVariable
        if self.element is port:
            self._found()

    def action_outputevent(self, event_out, **kwargs):  # @UnusedVariable
        if self.element is event_out:
            self._found()

    def action_stateassignment(self, assignment, **kwargs):  # @UnusedVariable
        if self.element is assignment:
            self._found()

    def action_timederivative(self, time_derivative, **kwargs):  # @UnusedVariable @IgnorePep8
        if self.element is time_derivative:
            self._found()

    def action_trigger(self, trigger, **kwargs):  # @UnusedVariable
        if self.element is trigger:
            self._found()

    def action_oncondition(self, on_condition, **kwargs):  # @UnusedVariable
        if self.element is on_condition:
            self._found()

    def action_onevent(self, on_event, **kwargs):  # @UnusedVariable
        if self.element is on_event:
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

    def action_statevariable(self, state_variable, **kwargs):  # @UnusedVariable @IgnorePep8
        self._get_sympy_expr(state_variable)
