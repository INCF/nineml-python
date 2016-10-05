"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from ...componentclass.visitors.cloner import ComponentCloner
from ..regimes import TimeDerivative, Regime, StateVariable
from ..transitions import (
    OnCondition, OnEvent, Trigger, StateAssignment, OutputEvent)
from ...ports import (
    AnalogSendPort, AnalogReceivePort, AnalogReducePort, EventSendPort,
    EventReceivePort)


class DynamicsCloner(ComponentCloner):

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

    def visit_statevariable(self, state_variable, **kwargs):
        return StateVariable(
            name=self.prefix_variable(state_variable.name, **kwargs),
            dimension=state_variable.dimension)

    def visit_analogreceiveport(self, port, **kwargs):
        return AnalogReceivePort(
            name=self.prefix_variable(port.name, **kwargs),
            dimension=port.dimension)

    def visit_analogreduceport(self, port, **kwargs):
        return AnalogReducePort(
            name=self.prefix_variable(port.name, **kwargs),
            dimension=port.dimension)

    def visit_analogsendport(self, port, **kwargs):
        return AnalogSendPort(
            name=self.prefix_variable(port.name, **kwargs),
            dimension=port.dimension)

    def visit_eventsendport(self, port, **kwargs):
        return EventSendPort(
            name=self.prefix_variable(port.name, **kwargs))

    def visit_eventreceiveport(self, port, **kwargs):
        return EventReceivePort(
            name=self.prefix_variable(port.name, **kwargs))

    def visit_outputevent(self, event_out, **kwargs):
        return OutputEvent(
            port_name=self.prefix_variable(event_out.port_name, **kwargs))

    def visit_stateassignment(self, assignment, **kwargs):
        prefix = kwargs.get('prefix', '')
        prefix_excludes = kwargs.get('prefix_excludes', [])

        lhs = self.prefix_variable(assignment.lhs, **kwargs)
        rhs = assignment.rhs_suffixed(suffix='', prefix=prefix,
                                      excludes=prefix_excludes)
        return StateAssignment(lhs=lhs, rhs=rhs)

    def visit_timederivative(self, time_derivative, **kwargs):
        prefix = kwargs.get('prefix', '')
        prefix_excludes = kwargs.get('prefix_excludes', [])

        dep = self.prefix_variable(time_derivative.variable,
                                   **kwargs)

        rhs = time_derivative.rhs_suffixed(suffix='', prefix=prefix,
                                           excludes=prefix_excludes)
        return TimeDerivative(variable=dep, rhs=rhs)

    def visit_trigger(self, trigger, **kwargs):
        prefix = kwargs.get('prefix', '')
        prefix_excludes = kwargs.get('prefix_excludes', [])
        rhs = trigger.rhs_suffixed(suffix='', prefix=prefix,
                                   excludes=prefix_excludes)
        return Trigger(rhs=rhs)

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
