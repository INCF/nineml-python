"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""


# from itertools import chain
from ...componentclass.utils import (
    ComponentActionVisitor, ComponentElementFinder)
from ...componentclass.utils.visitors import ComponentRequiredDefinitions


class DynamicsActionVisitor(ComponentActionVisitor):

    def visit_componentclass(self, componentclass, **kwargs):
        for e in componentclass:
            e.accept_visitor(self, **kwargs)
        for subnode in componentclass.subnodes.values():
            subnode.accept_visitor(self, **kwargs)

    def visit_regime(self, regime, **kwargs):
        self.action_regime(regime, **kwargs)
        for e in regime:
            e.accept_visitor(self, **kwargs)

    def visit_statevariable(self, state_variable, **kwargs):
        self.action_statevariable(state_variable, **kwargs)

    def visit_analogsendport(self, port, **kwargs):
        self.action_analogsendport(port, **kwargs)

    def visit_analogreceiveport(self, port, **kwargs):
        self.action_analogreceiveport(port, **kwargs)

    def visit_analogreduceport(self, port, **kwargs):
        self.action_analogreduceport(port, **kwargs)

    def visit_eventsendport(self, port, **kwargs):
        self.action_eventsendport(port, **kwargs)

    def visit_eventreceiveport(self, port, **kwargs):
        self.action_eventreceiveport(port, **kwargs)

    def visit_outputevent(self, event_out, **kwargs):
        self.action_outputevent(event_out, **kwargs)

    def visit_stateassignment(self, assignment, **kwargs):
        self.action_stateassignment(assignment, **kwargs)

    def visit_timederivative(self, time_derivative, **kwargs):
        self.action_timederivative(time_derivative, **kwargs)

    def visit_trigger(self, trigger, **kwargs):
        self.action_trigger(trigger, **kwargs)

    def visit_oncondition(self, on_condition, **kwargs):
        self.action_oncondition(on_condition, **kwargs)
        on_condition.trigger.accept_visitor(self, **kwargs)
        for e in on_condition:
            e.accept_visitor(self, **kwargs)

    def visit_onevent(self, on_event, **kwargs):
        self.action_onevent(on_event, **kwargs)
        for e in on_event:
            e.accept_visitor(self, **kwargs)

    def action_regime(self, regime, **kwargs):  # @UnusedVariable
        self.check_pass()

    def action_statevariable(self, state_variable, **kwargs):  # @UnusedVariable @IgnorePep8
        self.check_pass()

    def action_analogsendport(self, port, **kwargs):  # @UnusedVariable
        self.check_pass()

    def action_analogreceiveport(self, port, **kwargs):  # @UnusedVariable
        self.check_pass()

    def action_analogreduceport(self, port, **kwargs):  # @UnusedVariable
        self.check_pass()

    def action_eventsendport(self, port, **kwargs):  # @UnusedVariable
        self.check_pass()

    def action_eventreceiveport(self, port, **kwargs):  # @UnusedVariable
        self.check_pass()

    def action_outputevent(self, event_out, **kwargs):  # @UnusedVariable
        self.check_pass()

    def action_stateassignment(self, assignment, **kwargs):  # @UnusedVariable
        self.check_pass()

    def action_timederivative(self, time_derivative, **kwargs):  # @UnusedVariable @IgnorePep8
        self.check_pass()

    def action_trigger(self, trigger, **kwargs):  # @UnusedVariable
        self.check_pass()

    def action_oncondition(self, on_condition, **kwargs):  # @UnusedVariable
        self.check_pass()

    def action_onevent(self, on_event, **kwargs):  # @UnusedVariable
        self.check_pass()


class DynamicsRequiredDefinitions(ComponentRequiredDefinitions,
                                  DynamicsActionVisitor):

    def __init__(self, componentclass, expressions):
        DynamicsActionVisitor.__init__(self, require_explicit_overrides=False)
        self.state_variables = set()
        ComponentRequiredDefinitions.__init__(self, componentclass,
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
