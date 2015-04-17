"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from nineml.abstraction_layer.componentclass.namespace import NamespaceAddress
from ...componentclass.utils.cloner import (
    ComponentExpandPortDefinition, ComponentExpandAliasDefinition,
    ComponentCloner)
from .visitors import DynamicsActionVisitor


class DynamicsExpandPortDefinition(DynamicsActionVisitor,
                                   ComponentExpandPortDefinition):

    def action_stateassignment(self, assignment, **kwargs):  # @UnusedVariable
        assignment.name_transform_inplace(self.namemap)

    def action_timederivative(self, time_derivative, **kwargs):  # @UnusedVariable @IgnorePep8
        time_derivative.name_transform_inplace(self.namemap)

    def action_trigger(self, trigger, **kwargs):  # @UnusedVariable
        trigger.rhs_name_transform_inplace(self.namemap)


class DynamicsExpandAliasDefinition(DynamicsActionVisitor,
                                    ComponentExpandAliasDefinition):

    """ An action-class that walks over a component_class, and expands an alias in
    Assignments, Aliases, TimeDerivatives and Conditions
    """

    def action_stateassignment(self, assignment, **kwargs):  # @UnusedVariable
        assignment.name_transform_inplace(self.namemap)

    def action_timederivative(self, time_derivative, **kwargs):  # @UnusedVariable @IgnorePep8
        time_derivative.name_transform_inplace(self.namemap)

    def action_trigger(self, trigger, **kwargs):  # @UnusedVariable
        trigger.rhs_name_transform_inplace(self.namemap)


class DynamicsCloner(ComponentCloner):

    def visit_componentclass(self, component_class, **kwargs):
        cc = component_class.__class__(
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
            subnodes=dict([(k, v.accept_visitor(self, **kwargs))
                           for (k, v) in component_class.subnodes.iteritems()]),
            portconnections=component_class.portconnections[:])
        self.copy_indices(component_class, cc)
        return cc

    def visit_regime(self, regime, **kwargs):
        r = regime.__class__(
            name=regime.name,
            time_derivatives=[t.accept_visitor(self, **kwargs)
                              for t in regime.time_derivatives],
            transitions=[t.accept_visitor(self, **kwargs)
                         for t in regime.transitions])
        self.copy_indices(regime, r)
        return r

    def visit_statevariable(self, state_variable, **kwargs):
        return state_variable.__class__(
            name=self.prefix_variable(state_variable.name, **kwargs),
            dimension=state_variable.dimension)

    def visit_analogreceiveport(self, port, **kwargs):
        return port.__class__(
            name=self.prefix_variable(port.name, **kwargs),
            dimension=port.dimension)

    def visit_analogreduceport(self, port, **kwargs):
        return port.__class__(
            name=self.prefix_variable(port.name, **kwargs),
            dimension=port.dimension)

    def visit_analogsendport(self, port, **kwargs):
        return port.__class__(
            name=self.prefix_variable(port.name, **kwargs),
            dimension=port.dimension)

    def visit_eventsendport(self, port, **kwargs):
        return port.__class__(
            name=self.prefix_variable(port.name, **kwargs))

    def visit_eventreceiveport(self, port, **kwargs):
        return port.__class__(
            name=self.prefix_variable(port.name, **kwargs))

    def visit_outputevent(self, event_out, **kwargs):
        return event_out.__class__(
            port_name=self.prefix_variable(event_out.port_name, **kwargs))

    def visit_stateassignment(self, assignment, **kwargs):
        prefix = kwargs.get('prefix', '')
        prefix_excludes = kwargs.get('prefix_excludes', [])

        lhs = self.prefix_variable(assignment.lhs, **kwargs)
        rhs = assignment.rhs_suffixed(suffix='', prefix=prefix,
                                      excludes=prefix_excludes)
        return assignment.__class__(lhs=lhs, rhs=rhs)

    def visit_timederivative(self, time_derivative, **kwargs):
        prefix = kwargs.get('prefix', '')
        prefix_excludes = kwargs.get('prefix_excludes', [])

        dep = self.prefix_variable(time_derivative.variable,
                                   **kwargs)

        rhs = time_derivative.rhs_suffixed(suffix='', prefix=prefix,
                                           excludes=prefix_excludes)
        return time_derivative.__class__(variable=dep, rhs=rhs)

    def visit_trigger(self, trigger, **kwargs):
        prefix = kwargs.get('prefix', '')
        prefix_excludes = kwargs.get('prefix_excludes', [])
        rhs = trigger.rhs_suffixed(suffix='', prefix=prefix,
                                   excludes=prefix_excludes)
        return trigger.__class__(rhs=rhs)

    def visit_oncondition(self, on_condition, **kwargs):
        oc = on_condition.__class__(
            trigger=on_condition.trigger.accept_visitor(self, **kwargs),
            output_events=[e.accept_visitor(self, **kwargs)
                           for e in on_condition.output_events],
            state_assignments=[s.accept_visitor(self, **kwargs)
                               for s in on_condition.state_assignments],
            random_variables=[rv.accept_visitor(self, **kwargs)
                               for rv in on_condition.random_variables],
            target_regime=on_condition.target_regime.name
        )
        self.copy_indices(on_condition, oc)
        return oc

    def visit_onevent(self, on_event, **kwargs):
        oe = on_event.__class__(
            src_port_name=self.prefix_variable(on_event.src_port_name,
                                               **kwargs),
            output_events=[e.accept_visitor(self, **kwargs)
                           for e in on_event.output_events],
            state_assignments=[s.accept_visitor(self, **kwargs)
                               for s in on_event.state_assignments],
            random_variables=[rv.accept_visitor(self, **kwargs)
                               for rv in on_event.random_variables],
            target_regime=on_event.target_regime.name
        )
        self.copy_indices(on_event, oe, **kwargs)
        return oe


# TODO: TGC 4/15 should just merge functionality into cloner I think.
class DynamicsClonerPrefixNamespace(DynamicsCloner):

    """
    A visitor that walks over a hierarchical component_class, and prefixes every
    variable with the namespace that that variable is in. This is preparation
    for flattening
    """

    def visit_componentclass(self, component_class, **kwargs):  # @UnusedVariable @IgnorePep8
        prefix = component_class.get_node_addr().get_str_prefix()
        if prefix == '_':
            prefix = ''
        prefix_excludes = ['t']
        kwargs = {'prefix': prefix, 'prefix_excludes': prefix_excludes}

        port_connections = []
        for src, sink in component_class.portconnections:
            # To calculate the new address of the ports, we take of the 'local'
            # port address, i.e. the parent address, then add the prefixed
            # string:
            src_new = NamespaceAddress.concat(
                src.get_parent_addr(),
                NamespaceAddress.concat(
                    component_class.get_node_addr(),
                    src.get_parent_addr()).get_str_prefix() +
                self.prefix_variable(src.get_local_name()))
            sink_new = NamespaceAddress.concat(
                sink.get_parent_addr(), NamespaceAddress.concat(
                    component_class.get_node_addr(),
                    sink.get_parent_addr()).get_str_prefix() +
                self.prefix_variable(sink.get_local_name()))
            port_connections.append((src_new, sink_new))
        return component_class.__class__(
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
            subnodes=dict([(k, v.accept_visitor(self, **kwargs))
                           for (k, v) in component_class.subnodes.iteritems()]),
            portconnections=port_connections)
