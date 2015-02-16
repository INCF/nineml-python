"""
This file contains utility classes for modifying components.

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from nineml.exceptions import NineMLRuntimeError
from .visitors import ComponentActionVisitor


class ComponentModifier(object):

    """Utility classes for modifying components"""

    pass


class ComponentRenameSymbol(ComponentActionVisitor):

    """ Can be used for:
    StateVariables, Aliases, Ports
    """

    def __init__(self, componentclass, old_symbol_name, new_symbol_name):
        ComponentActionVisitor.__init__(
            self, require_explicit_overrides=True)
        self.old_symbol_name = old_symbol_name
        self.new_symbol_name = new_symbol_name
        self.namemap = {old_symbol_name: new_symbol_name}

        if not componentclass.is_flat():
            raise NineMLRuntimeError('Rename Symbol called on non-flat model')

        self.lhs_changes = []
        self.rhs_changes = []
        self.port_changes = []

        self.visit(componentclass)
        componentclass._validate_self()

    def note_lhs_changed(self, what):
        self.lhs_changes.append(what)

    def note_rhs_changed(self, what):
        self.rhs_changes.append(what)

    def note_port_changed(self, what):
        self.port_changes.append(what)

    def action_componentclass(self, component, **kwargs):
        pass

    def action_parameter(self, parameter, **kwargs):  # @UnusedVariable
        if parameter.name == self.old_symbol_name:
            parameter._name = self.new_symbol_name
            self.note_lhs_changed(parameter)

    def _action_port(self, port, **kwargs):  # @UnusedVariable
        if port.name == self.old_symbol_name:
            port._name = self.new_symbol_name
            self.note_port_changed(port)

    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        if alias.lhs == self.old_symbol_name:
            self.note_lhs_changed(alias)
            alias.name_transform_inplace(self.namemap)
        elif self.old_symbol_name in alias.atoms:
            self.note_rhs_changed(alias)
            alias.name_transform_inplace(self.namemap)

    def action_randomvariable(self, randomvariable, **kwargs):  # @UnusedVariable @IgnorePep8
        if randomvariable.name == self.old_symbol_name:
            self.note_lhs_changed(randomvariable)
            randomvariable.name_transform_inplace(self.namemap)

    def action_constant(self, constant, **kwargs):  # @UnusedVariable
        if constant.name == self.old_symbol_name:
            self.note_lhs_changed(constant)
            constant.name_transform_inplace(self.namemap)

    def action_piecewise(self, piecewise, **kwargs):  # @UnusedVariable
        if piecewise.name == self.old_symbol_name:
            self.note_lhs_changed(piecewise)
            piecewise.name_transform_inplace(self.namemap)
        elif self.old_symbol_name in piecewise.atoms:
            self.note_rhs_changed(piecewise)
            piecewise.name_transform_inplace(self.namemap)
