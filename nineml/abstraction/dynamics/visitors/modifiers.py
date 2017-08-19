"""
This file contains utility classes for modifying components.

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

import sympy
from .base import BaseDynamicsVisitor
from ...componentclass.visitors.modifiers import (
    ComponentRenameSymbol, ComponentAssignIndices,
    ComponentSubstituteAliases, ComponentFlattener, lookup_memo)


class DynamicsRenameSymbol(ComponentRenameSymbol,
                           BaseDynamicsVisitor):

    """ Can be used for:
    StateVariables, Aliases, Ports
    """

    def action_regime(self, regime, **kwargs):  # @UnusedVariable @IgnorePep8
        if regime.name == self.old_symbol_name:
            regime._name = self.new_symbol_name
        regime._update_member_key(
            self.old_symbol_name, self.new_symbol_name)
        # Update the on condition trigger keys, which can't be updated via
        # the _update_member_key method
        for trigger in regime.on_condition_triggers:
            if sympy.Symbol(self.old_symbol_name) in trigger.free_symbols:
                new_trigger = trigger.xreplace(
                    {sympy.Symbol(self.old_symbol_name):
                     sympy.Symbol(self.new_symbol_name)})
                regime._on_conditions[new_trigger] = (regime._on_conditions.
                                                      pop(trigger))

    def action_statevariable(self, state_variable, **kwargs):  # @UnusedVariable @IgnorePep8
        if state_variable.name == self.old_symbol_name:
            state_variable._name = self.new_symbol_name
            self.note_lhs_changed(state_variable)

    def action_analogsendport(self, port, **kwargs):  # @UnusedVariable
        self._action_port(port, **kwargs)

    def action_analogreceiveport(self, port, **kwargs):  # @UnusedVariable
        self._action_port(port, **kwargs)

    def action_analogreduceport(self, port, **kwargs):  # @UnusedVariable
        self._action_port(port, **kwargs)

    def action_eventsendport(self, port, **kwargs):  # @UnusedVariable
        self._action_port(port, **kwargs)

    def action_eventreceiveport(self, port, **kwargs):  # @UnusedVariable
        self._action_port(port, **kwargs)

    def action_outputevent(self, event_out, **kwargs):  # @UnusedVariable
        if event_out.port_name == self.old_symbol_name:
            event_out._port_name = self.new_symbol_name
            self.note_rhs_changed(event_out)

    def action_stateassignment(self, assignment, **kwargs):  # @UnusedVariable
        if self.old_symbol_name in assignment.atoms:
            self.note_rhs_changed(assignment)
            assignment.name_transform_inplace(self.namemap)

    def action_timederivative(self, timederivative, **kwargs):  # @UnusedVariable @IgnorePep8
        if timederivative.variable == self.old_symbol_name:
            self.note_lhs_changed(timederivative)
            timederivative.name_transform_inplace(self.namemap)
        elif self.old_symbol_name in timederivative.atoms:
            self.note_rhs_changed(timederivative)
            timederivative.name_transform_inplace(self.namemap)

    def action_trigger(self, trigger, **kwargs):  # @UnusedVariable
        if self.old_symbol_name in trigger.rhs_atoms:
            self.note_rhs_changed(trigger)
            trigger.rhs_name_transform_inplace(self.namemap)

    def action_oncondition(self, on_condition, **kwargs):  # @UnusedVariable
        if on_condition._target_regime == self.old_symbol_name:
            on_condition._target_regime = self.new_symbol_name
        on_condition._update_member_key(
            self.old_symbol_name, self.new_symbol_name)

    def action_onevent(self, on_event, **kwargs):  # @UnusedVariable
        if on_event.src_port_name == self.old_symbol_name:
            on_event._src_port_name = self.new_symbol_name
            self.note_rhs_changed(on_event)
        if on_event._target_regime.name == self.old_symbol_name:
            on_event._target_regime._name = self.new_symbol_name
        on_event._update_member_key(
            self.old_symbol_name, self.new_symbol_name)


class DynamicsAssignIndices(ComponentAssignIndices,
                            BaseDynamicsVisitor):

    def action_regime(self, regime, **kwargs):  # @UnusedVariable @IgnorePep8
        for elem in regime.elements():
            regime.index_of(elem)
        for trans in regime.transitions:
            self.component_class.index_of(trans, 'Transition')

    def action_oncondition(self, on_condition, **kwargs):  # @UnusedVariable
        for elem in on_condition.elements():
            on_condition.index_of(elem)

    def action_onevent(self, on_event, **kwargs):  # @UnusedVariable
        for elem in on_event.elements():
            on_event.index_of(elem)


class DynamicsSubstituteAliases(ComponentSubstituteAliases,
                                BaseDynamicsVisitor):

    def action_dynamics(self, dynamics, **kwargs):  # @UnusedVariable
        self.outputs.update(dynamics.analog_send_port_names)

    def action_timederivative(self, time_derivative, **kwargs):  # @UnusedVariable @IgnorePep8
        self.substitute(time_derivative)

    def action_stateassignment(self, state_assignment, **kwargs):  # @UnusedVariable @IgnorePep8
        self.substitute(state_assignment)

    def action_trigger(self, trigger, **kwargs):  # @UnusedVariable @IgnorePep8
        old_rhs = trigger.rhs
        self.substitute(trigger)
        # If trigger expression has changed update on_condition key
        if trigger.rhs != old_rhs:
            member_dict = self.contexts[-2].parent._on_conditions
            member_dict[trigger.rhs] = member_dict.pop(old_rhs)

    def post_action_dynamics(self, dynamics, results, **kwargs):  # @UnusedVariable @IgnorePep8
        self.remove_uneeded_aliases(dynamics)

    def post_action_regime(self, regime, results, **kwargs):  # @UnusedVariable
        self.remove_uneeded_aliases(regime)


class DynamicsFlattener(ComponentFlattener):

    @lookup_memo
    def visit_componentclass(self, component_class, **kwargs):
        try:
            cls = component_class.core_type
        except AttributeError:
            cls = type(component_class)
        cc = cls(
            name=component_class.name,
            parameters=[p.accept_visitor(self, **kwargs)
                        for p in component_class.parameters],
            analog_ports=[p.accept_visitor(self, **kwargs)
                          for p in component_class.analog_ports],
            event_ports=[p.accept_visitor(self, **kwargs)
                         for p in component_class.event_ports],
            regimes=[r.accept_visitor(self, **kwargs)
                     for r in component_class.regimes],
            aliases=[
                a.accept_visitor(self, **kwargs)
                for a in component_class.aliases],
            state_variables=[
                s.accept_visitor(self, **kwargs)
                for s in component_class.state_variables],
            constants=[c.accept_visitor(self, **kwargs)
                       for c in component_class.constants],
            strict_unused=False)
        self.copy_indices(component_class, cc)
        return cc

    @lookup_memo
    def visit_regime(self, regime, **kwargs):
        r = Regime(
            name=regime.name,
            time_derivatives=[t.accept_visitor(self, **kwargs)
                              for t in regime.time_derivatives],
            transitions=[t.accept_visitor(self, **kwargs)
                         for t in regime.transitions],
            aliases=[a.accept_visitor(self, **kwargs)
                     for a in regime.aliases])
        self.copy_indices(regime, r)
        return r

    @lookup_memo
    def visit_statevariable(self, state_variable, **kwargs):
        return StateVariable(
            name=self.prefix_variable(state_variable.name, **kwargs),
            dimension=state_variable.dimension.clone(self.memo, **kwargs))

    @lookup_memo
    def visit_analogreceiveport(self, port, **kwargs):
        return AnalogReceivePort(
            name=self.prefix_variable(port.name, **kwargs),
            dimension=port.dimension.clone(self.memo, **kwargs))

    @lookup_memo
    def visit_analogreduceport(self, port, **kwargs):
        return AnalogReducePort(
            name=self.prefix_variable(port.name, **kwargs),
            dimension=port.dimension.clone(self.memo, **kwargs))

    @lookup_memo
    def visit_analogsendport(self, port, **kwargs):
        return AnalogSendPort(
            name=self.prefix_variable(port.name, **kwargs),
            dimension=port.dimension.clone(self.memo, **kwargs))

    @lookup_memo
    def visit_eventsendport(self, port, **kwargs):
        return EventSendPort(
            name=self.prefix_variable(port.name, **kwargs))

    @lookup_memo
    def visit_eventreceiveport(self, port, **kwargs):
        return EventReceivePort(
            name=self.prefix_variable(port.name, **kwargs))

    @lookup_memo
    def visit_outputevent(self, event_out, **kwargs):
        return OutputEvent(
            port_name=self.prefix_variable(event_out.port_name, **kwargs))

    @lookup_memo
    def visit_stateassignment(self, assignment, **kwargs):
        prefix = kwargs.get('prefix', '')
        prefix_excludes = kwargs.get('prefix_excludes', [])

        lhs = self.prefix_variable(assignment.lhs, **kwargs)
        rhs = assignment.rhs_suffixed(suffix='', prefix=prefix,
                                      excludes=prefix_excludes)
        return StateAssignment(lhs=lhs, rhs=rhs)

    @lookup_memo
    def visit_timederivative(self, time_derivative, **kwargs):
        prefix = kwargs.get('prefix', '')
        prefix_excludes = kwargs.get('prefix_excludes', [])

        dep = self.prefix_variable(time_derivative.variable,
                                   **kwargs)

        rhs = time_derivative.rhs_suffixed(suffix='', prefix=prefix,
                                           excludes=prefix_excludes)
        return TimeDerivative(variable=dep, rhs=rhs)

    @lookup_memo
    def visit_trigger(self, trigger, **kwargs):
        prefix = kwargs.get('prefix', '')
        prefix_excludes = kwargs.get('prefix_excludes', [])
        rhs = trigger.rhs_suffixed(suffix='', prefix=prefix,
                                   excludes=prefix_excludes)
        return Trigger(rhs=rhs)

    @lookup_memo
    def visit_oncondition(self, on_condition, **kwargs):
        oc = OnCondition(
            trigger=on_condition.trigger.accept_visitor(self, **kwargs),
            output_events=[e.accept_visitor(self, **kwargs)
                           for e in on_condition.output_events],
            state_assignments=[s.accept_visitor(self, **kwargs)
                               for s in on_condition.state_assignments],
            target_regime=on_condition.target_regime.name
        )
        self.copy_indices(on_condition, oc)
        return oc

    @lookup_memo
    def visit_onevent(self, on_event, **kwargs):
        oe = OnEvent(
            src_port_name=self.prefix_variable(on_event.src_port_name,
                                               **kwargs),
            output_events=[e.accept_visitor(self, **kwargs)
                           for e in on_event.output_events],
            state_assignments=[s.accept_visitor(self, **kwargs)
                               for s in on_event.state_assignments],
            target_regime=on_event.target_regime.name
        )
        self.copy_indices(on_event, oe, **kwargs)
        return oe


from ..regimes import TimeDerivative, Regime, StateVariable  # @IgnorePep8
from ..transitions import (  # @IgnorePep8
    OnCondition, OnEvent, Trigger, StateAssignment, OutputEvent)
from ...ports import (  # @IgnorePep8
    AnalogSendPort, AnalogReceivePort, AnalogReducePort, EventSendPort,
    EventReceivePort)
