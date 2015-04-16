"""
This file contains utility classes for modifying components.

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

import sympy
from ..base import Parameter
from .cloner import DynamicsExpandPortDefinition
from ...ports import AnalogSendPort, AnalogReducePort, AnalogReceivePort
from nineml.utils import filter_expect_single
from nineml.exceptions import NineMLRuntimeError
from ...componentclass.utils.modifiers import (
    ComponentModifier, ComponentRenameSymbol, ComponentAssignIndices)
from .visitors import DynamicsActionVisitor


class DynamicPortModifier(ComponentModifier):

    """Utility classes for modifying components"""

    _ExpandPortDefinition = DynamicsExpandPortDefinition

    @classmethod
    def close_analog_port(cls, component_class, port_name, value="0"):
        """Closes an incoming analog port by assigning its value to 0"""

        if not component_class.is_flat():
            raise NineMLRuntimeError('close_analog_port() on non-flat '
                                     'component_class')

        # Subsitute the value in:
        component_class.accept_visitor(cls._ExpandPortDefinition(port_name,
                                                                value))

        # Remove it from the list of ports:
        port = filter_expect_single(component_class.analog_ports,
                                    lambda ap: ap.name == port_name)
        if isinstance(port, AnalogSendPort):
            component_class._analog_send_ports.pop(port_name)
        elif isinstance(port, AnalogReceivePort):
            component_class._analog_receive_ports.pop(port_name)
        elif isinstance(port, AnalogReducePort):
            component_class._analog_reduce_ports.pop(port_name)
        else:
            raise TypeError("Expected an analog port")

    @classmethod
    def close_all_reduce_ports(cls, component_class, exclude=None):
        """
        Closes all the ``reduce`` ports on a component_class by assigning them a
        value of 0
        """
        if not component_class.is_flat():
            raise NineMLRuntimeError('close_all_reduce_ports() on non-flat '
                                     'component_class')

        for arp in component_class.query.analog_reduce_ports:
            if exclude and arp.name in exclude:
                continue
            cls.close_analog_port(component_class=component_class,
                                  port_name=arp.name, value=0)

    @classmethod
    def rename_port(cls, component_class, old_port_name, new_port_name):
        """ Renames a port in a component_class """
        if not component_class.is_flat():
            raise NineMLRuntimeError('rename_port() on non-flat '
                                     'component_class')

        # Find the old port:
        port = filter_expect_single(component_class.analog_ports,
                                    lambda ap: ap.name == old_port_name)
        port._name = new_port_name

    @classmethod
    def remap_port_to_parameter(cls, component_class, port_name):
        """ Renames a port in a component_class """
        if not component_class.is_flat():
            raise NineMLRuntimeError('rename_port_to_parameter() on non-flat '
                                     'component_class')

        # Find the old port:
        port = filter_expect_single(component_class.analog_ports,
                                    lambda ap: ap.name == port_name)
        component_class._analog_ports.remove(port)

        # Add a new parameter:
        component_class._parameters[port_name] = Parameter(port_name)


class DynamicsRenameSymbol(ComponentRenameSymbol,
                           DynamicsActionVisitor):

    """ Can be used for:
    StateVariables, Aliases, Ports
    """


    def action_componentclass(self, component_class, **kwargs):  # @UnusedVariable @IgnorePep8
        super(DynamicsRenameSymbol, self).action_componentclass(component_class)
        self._update_dicts(*component_class.all_member_dicts)

    def action_regime(self, regime, **kwargs):  # @UnusedVariable @IgnorePep8
        if regime.name == self.old_symbol_name:
            regime._name = self.new_symbol_name
        self._update_dicts(*regime.all_member_dicts)
        # Update the on condition trigger keys, which can't be updated via
        # the _update_dicts method
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
        self._update_dicts(*on_condition.all_member_dicts)

    def action_onevent(self, on_event, **kwargs):  # @UnusedVariable
        if on_event.src_port_name == self.old_symbol_name:
            on_event._src_port_name = self.new_symbol_name
            self.note_rhs_changed(on_event)
        if on_event._target_regime == self.old_symbol_name:
            on_event._target_regime = self.new_symbol_name
        self._update_dicts(*on_event.all_member_dicts)


class DynamicsAssignIndices(ComponentAssignIndices,
                            DynamicsActionVisitor):

    def action_regime(self, regime, **kwargs):  # @UnusedVariable @IgnorePep8
        for elem in regime:
            regime.index_of(elem)
        for trans in regime.transitions:
            self.component_class.index_of(trans, 'Transition')

    def action_oncondition(self, on_condition, **kwargs):  # @UnusedVariable
        for elem in on_condition:
            on_condition.index_of(elem)

    def action_onevent(self, on_event, **kwargs):  # @UnusedVariable
        for elem in on_event:
            on_event.index_of(elem)
