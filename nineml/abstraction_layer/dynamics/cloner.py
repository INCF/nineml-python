"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from ...exceptions import NineMLRuntimeError
from ..maths import is_builtin_symbol
from ..maths.expressions import MathUtil
from .subcomponent import NamespaceAddress
from .visitors import ActionVisitor, ComponentVisitor


class ExpandPortDefinition(ActionVisitor):

    def __init__(self, originalname, targetname):

        ActionVisitor.__init__(self, explicitly_require_action_overrides=False)

        self.originalname = originalname
        self.targetname = targetname
        self.namemap = {originalname: targetname}

    def action_assignment(self, assignment, **kwargs):  # @UnusedVariable
        assignment.name_transform_inplace(self.namemap)

    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        alias.name_transform_inplace(self.namemap)

    def action_timederivative(self, time_derivative, **kwargs):  # @UnusedVariable @IgnorePep8
        time_derivative.name_transform_inplace(self.namemap)

    def action_condition(self, condition, **kwargs):  # @UnusedVariable
        condition.rhs_name_transform_inplace(self.namemap)


class ExpandAliasDefinition(ActionVisitor):

    """ An action-class that walks over a component, and expands an alias in
    Assignments, Aliases, TimeDerivatives and Conditions
    """

    def __init__(self, originalname, targetname):

        ActionVisitor.__init__(self, explicitly_require_action_overrides=False)

        self.originalname = originalname
        self.targetname = targetname
        self.namemap = {originalname: targetname}

    def action_assignment(self, assignment, **kwargs):  # @UnusedVariable
        assignment.name_transform_inplace(self.namemap)

    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        alias.rhs_name_transform_inplace(self.namemap)

    def action_timederivative(self, time_derivative, **kwargs):  # @UnusedVariable @IgnorePep8
        time_derivative.name_transform_inplace(self.namemap)

    def action_condition(self, condition, **kwargs):  # @UnusedVariable
        condition.rhs_name_transform_inplace(self.namemap)


class RenameSymbol(ActionVisitor):

    """ Can be used for:
    StateVariables, Aliases, Ports
    """

    def __init__(self, component, old_symbol_name, new_symbol_name):
        ActionVisitor.__init__(self, explicitly_require_action_overrides=True)
        self.old_symbol_name = old_symbol_name
        self.new_symbol_name = new_symbol_name
        self.namemap = {old_symbol_name: new_symbol_name}

        if not component.is_flat():
            raise NineMLRuntimeError('Rename Symbol called on non-flat model')

        self.lhs_changes = []
        self.rhs_changes = []
        self.port_changes = []

        self.visit(component)
        component._validate_self()

    def note_lhs_changed(self, what):
        self.lhs_changes.append(what)

    def note_rhs_changed(self, what):
        self.rhs_changes.append(what)

    def note_port_changed(self, what):
        self.port_changes.append(what)

    def action_componentclass(self, component, **kwargs):
        pass

    def action_dynamics(self, dynamics, **kwargs):
        pass

    def action_regime(self, regime, **kwargs):
        pass

    def action_statevariable(self, state_variable, **kwargs):  # @UnusedVariable @IgnorePep8
        if state_variable.name == self.old_symbol_name:
            state_variable._name = self.new_symbol_name
            self.note_lhs_changed(state_variable)

    def action_parameter(self, parameter, **kwargs):  # @UnusedVariable
        if parameter.name == self.old_symbol_name:
            parameter._name = self.new_symbol_name
            self.note_lhs_changed(parameter)

    def _action_port(self, port, **kwargs):  # @UnusedVariable
        if port.name == self.old_symbol_name:
            port._name = self.new_symbol_name
            self.note_port_changed(port)

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

    def action_outputevent(self, output_event, **kwargs):  # @UnusedVariable
        if output_event.port_name == self.old_symbol_name:
            output_event._port_name = self.new_symbol_name
            self.note_rhs_changed(output_event)

    def action_assignment(self, assignment, **kwargs):  # @UnusedVariable
        if self.old_symbol_name in assignment.atoms:
            self.note_rhs_changed(assignment)
            assignment.name_transform_inplace(self.namemap)

    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        if alias.lhs == self.old_symbol_name:
            self.note_lhs_changed(alias)
            alias.name_transform_inplace(self.namemap)
        elif self.old_symbol_name in alias.atoms:
            self.note_rhs_changed(alias)
            alias.name_transform_inplace(self.namemap)

    def action_timederivative(self, timederivative, **kwargs):  # @UnusedVariable
        if timederivative.dependent_variable == self.old_symbol_name:
            self.note_lhs_changed(timederivative)
            timederivative.name_transform_inplace(self.namemap)
        elif self.old_symbol_name in timederivative.atoms:
            self.note_rhs_changed(timederivative)
            timederivative.name_transform_inplace(self.namemap)

    def action_condition(self, condition, **kwargs):  # @UnusedVariable
        if self.old_symbol_name in condition.rhs_atoms:
            self.note_rhs_changed(condition)
            condition.rhs_name_transform_inplace(self.namemap)

    def action_oncondition(self, on_condition, **kwargs):
        """ Handled in action_condition """
        pass

    def action_onevent(self, on_event, **kwargs):  # @UnusedVariable
        if on_event.src_port_name == self.old_symbol_name:
            on_event._port_name = self.new_symbol_name
            self.note_rhs_changed(on_event)


class ClonerVisitor(ComponentVisitor):

    def prefix_variable(self, variable, **kwargs):
        prefix = kwargs.get('prefix', '')
        prefix_excludes = kwargs.get('prefix_excludes', [])
        if variable in prefix_excludes:
            return variable

        if is_builtin_symbol(variable):
            return variable

        else:
            return prefix + variable

    def visit_componentclass(self, component, **kwargs):
        ccn = component.__class__(
            name=component.name,
            parameters=[p.accept_visitor(self, **kwargs)
                        for p in component.parameters],
            analog_ports=[p.accept_visitor(self, **kwargs)
                          in component.analog_ports],
            event_ports=[p.accept_visitor(self, **kwargs)
                         for p in component.event_ports],
            dynamics=(component.dynamics.accept_visitor(self, **kwargs)
                      if component.dynamics else None),
            subnodes=dict([(k, v.accept_visitor(self, **kwargs))
                           for (k, v) in component.subnodes.iteritems()]),
            portconnections=component.portconnections[:])
        return ccn

    def visit_dynamics(self, dynamics, **kwargs):
        return dynamics.__class__(
            regimes=[r.accept_visitor(self, **kwargs)
                     for r in dynamics.regimes],
            aliases=[
                a.accept_visitor(self, **kwargs) for a in dynamics.aliases],
            state_variables=[s.accept_visitor(self, **kwargs)
                             for s in dynamics.state_variables])

    def visit_regime(self, regime, **kwargs):
        return regime.__class__(
            name=regime.name,
            time_derivatives=[t.accept_visitor(self, **kwargs)
                              for t in regime.time_derivatives],
            transitions=[t.accept_visitor(self, **kwargs)
                         for t in regime.transitions])

    def visit_statevariable(self, state_variable, **kwargs):
        return state_variable.__class__(
            name=self.prefix_variable(state_variable.name, **kwargs),
            dimension=state_variable.dimension)

    def visit_parameter(self, parameter, **kwargs):
        return parameter.__class__(
            name=self.prefix_variable(parameter.name, **kwargs),
            dimension=parameter.dimension)

    def visit_analogreceiveport(self, port, **kwargs):
        return port.__class__(
            name=self.prefix_variable(port.name, **kwargs))

    def visit_analogreduceport(self, port, **kwargs):
        return port.__class__(
            name=self.prefix_variable(port.name, **kwargs))

    def visit_analogsendport(self, port, **kwargs):
        return port.__class__(
            name=self.prefix_variable(port.name, **kwargs))

    def visit_eventsendport(self, port, **kwargs):
        return port.__class__(
            name=self.prefix_variable(port.name, **kwargs))

    def visit_eventreceiveport(self, port, **kwargs):
        return port.__class__(
            name=self.prefix_variable(port.name, **kwargs))

    def visit_outputevent(self, output_event, **kwargs):
        return output_event.__class__(
            port_name=self.prefix_variable(output_event.port_name, **kwargs))

    def visit_assignment(self, assignment, **kwargs):
        prefix = kwargs.get('prefix', '')
        prefix_excludes = kwargs.get('prefix_excludes', [])

        lhs = self.prefix_variable(assignment.lhs, **kwargs)
        rhs = MathUtil.get_prefixed_rhs_string(
            expr_obj=assignment, prefix=prefix, exclude=prefix_excludes)

        return assignment.__class__(lhs=lhs, rhs=rhs)

    def visit_alias(self, alias, **kwargs):
        new_alias = alias.__class__(lhs=alias.lhs, rhs=alias.rhs)
        name_map = dict([(a, self.prefix_variable(a, **kwargs))
                         for a in new_alias.atoms])
        new_alias.name_transform_inplace(name_map=name_map)
        return new_alias

    def visit_timederivative(self, time_derivative, **kwargs):
        prefix = kwargs.get('prefix', '')
        prefix_excludes = kwargs.get('prefix_excludes', [])

        dep = self.prefix_variable(time_derivative.dependent_variable,
                                   **kwargs)

        rhs = MathUtil.get_prefixed_rhs_string(
            expr_obj=time_derivative, prefix=prefix, exclude=prefix_excludes)
        return time_derivative.__class__(dependent_variable=dep, rhs=rhs)

    def visit_condition(self, condition, **kwargs):
        prefix = kwargs.get('prefix', '')
        prefix_excludes = kwargs.get('prefix_excludes', [])
        rhs = MathUtil.get_prefixed_rhs_string(
            expr_obj=condition, prefix=prefix, exclude=prefix_excludes)
        return condition.__class__(rhs=rhs)

    def visit_oncondition(self, on_condition, **kwargs):
        return on_condition.__class__(
            trigger=on_condition.trigger.accept_visitor(self, **kwargs),
            event_outputs=[e.accept_visitor(self, **kwargs)
                           for e in on_condition.event_outputs],
            state_assignments=[s.accept_visitor(self, **kwargs)
                               for s in on_condition.state_assignments],
            target_regime_name=on_condition.target_regime_name
        )

    def visit_onevent(self, on_event, **kwargs):
        return on_event.__class__(
            src_port_name=self.prefix_variable(on_event.src_port_name,
                                               **kwargs),
            event_outputs=[e.accept_visitor(self, **kwargs)
                           for e in on_event.event_outputs],
            state_assignments=[s.accept_visitor(self, **kwargs)
                               for s in on_event.state_assignments],
            target_regime_name=on_event.target_regime_name
        )


class ClonerVisitorPrefixNamespace(ClonerVisitor):

    """ A visitor that walks over a hierarchical component, and prefixes every
    variable with the namespace that that variable is in. This is preparation
    for flattening
    """

    def visit_componentclass(self, component, **kwargs):  # @UnusedVariable
        prefix = component.get_node_addr().get_str_prefix()
        if prefix == '_':
            prefix = ''
        prefix_excludes = ['t']
        kwargs = {'prefix': prefix, 'prefix_excludes': prefix_excludes}

        port_connections = []
        for src, sink in component.portconnections:
            # To calculate the new address of the ports, we take of the 'local'
            # port address, i.e. the parent address, then add the prefixed
            # string:
            src_new = NamespaceAddress.concat(
                src.get_parent_addr(),
                NamespaceAddress.concat(
                    component.get_node_addr(),
                    src.get_parent_addr()).get_str_prefix() +
                self.prefix_variable(src.get_local_name()))
            sink_new = NamespaceAddress.concat(
                sink.get_parent_addr(), NamespaceAddress.concat(
                    component.get_node_addr(),
                    sink.get_parent_addr()).get_str_prefix() +
                self.prefix_variable(sink.get_local_name()))
            # self.prefix_variable(sink.get_local_name(), **kwargs) )

            # print 'Mapping Ports:', src, '->', src_new, '(%s)' %
#                  src.get_local_name(), prefix
            # print 'Mapping Ports:', sink, '->', sink_new
            # src_new = NamespaceAddress.concat(
#                 src.get_parent_addr(), src.getstr() )
            # sink_new = NamespaceAddress.concat(
#                 sink.get_parent_addr(), sink.getstr() )
            port_connections.append((src_new, sink_new))
        return component.__class__(
            name=component.name,
            parameters=[p.accept_visitor(self, **kwargs)
                        for p in component.parameters],
            analog_ports=[p.accept_visitor(self, **kwargs)
                          for p in component.analog_ports],
            event_ports=[p.accept_visitor(self, **kwargs)
                         for p in component.event_ports],
            dynamics=(component.dynamics.accept_visitor(self, **kwargs)
                      if component.dynamics else None),
            subnodes=dict([(k, v.accept_visitor(self, **kwargs))
                           for (k, v) in component.subnodes.iteritems()]),
            portconnections=port_connections)
