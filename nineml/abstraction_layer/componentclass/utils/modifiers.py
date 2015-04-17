"""
This file contains utility classes for modifying components.

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from itertools import chain
from nineml.exceptions import NineMLRuntimeError
from .visitors import ComponentActionVisitor


class ComponentModifier(object):

    """Utility classes for modifying components"""

    pass


class ComponentRenameSymbol(ComponentActionVisitor):

    """ Can be used for:
    StateVariables, Aliases, Ports
    """

    def __init__(self, component_class, old_symbol_name, new_symbol_name):
        ComponentActionVisitor.__init__(
            self, require_explicit_overrides=True)
        self.old_symbol_name = old_symbol_name
        self.new_symbol_name = new_symbol_name
        self.namemap = {old_symbol_name: new_symbol_name}

        if not component_class.is_flat():
            raise NineMLRuntimeError('Rename Symbol called on non-flat model')

        self.lhs_changes = []
        self.rhs_changes = []
        self.port_changes = []

        component_class.assign_indices()
        self.visit(component_class)
        component_class.validate()

    def note_lhs_changed(self, what):
        self.lhs_changes.append(what)

    def note_rhs_changed(self, what):
        self.rhs_changes.append(what)

    def note_port_changed(self, what):
        self.port_changes.append(what)

    def _update_dicts(self, *dicts):
        for d in dicts:
            # Can't use "pythonic" try/except because I want it to work for
            # defaultdicts (i.e. '_indices' dicts) as well
            assert isinstance(d, dict)
            if self.old_symbol_name in d:
                d[self.new_symbol_name] = d.pop(self.old_symbol_name)

    def _action_port(self, port, **kwargs):  # @UnusedVariable
        if port.name == self.old_symbol_name:
            port._name = self.new_symbol_name
            self.note_port_changed(port)

    def action_componentclass(self, component_class, **kwargs):  # @UnusedVariable @IgnorePep8
        self._update_dicts(*chain(component_class.all_member_dicts,
                                  component_class._indices.itervalues()))

    def action_parameter(self, parameter, **kwargs):  # @UnusedVariable
        if parameter.name == self.old_symbol_name:
            parameter._name = self.new_symbol_name
            self.note_lhs_changed(parameter)

    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        if alias.lhs == self.old_symbol_name:
            self.note_lhs_changed(alias)
            alias.name_transform_inplace(self.namemap)
        elif self.old_symbol_name in alias.atoms:
            self.note_rhs_changed(alias)
            alias.name_transform_inplace(self.namemap)

    def action_constant(self, constant, **kwargs):  # @UnusedVariable
        if constant.name == self.old_symbol_name:
            self.note_lhs_changed(constant)
            constant.name_transform_inplace(self.namemap)

    def action_randomvariable(self, random_variable, **kwargs):  # @UnusedVariable @IgnorePep8
        if random_variable.name == self.old_symbol_name:
            self.note_lhs_changed(random_variable)
            random_variable.name_transform_inplace(self.namemap)

    def action_randomdistribution(self, random_distribution, **kwargs):  # @UnusedVariable @IgnorePep8
        for key, var in random_distribution.parameters.iteritems():
            if var == self.old_symbol_name:
                random_distribution.parameters[key] = self.new_symbol_name


class ComponentAssignIndices(ComponentActionVisitor):

    """
    Forces the generation of indices for all commonly index elements of the
    component class
    """

    def __init__(self, component_class):
        ComponentActionVisitor.__init__(
            self, require_explicit_overrides=False)
        self.component_class = component_class
        self.visit(component_class)

    def action_componentclass(self, component_class, **kwargs):  # @UnusedVariable @IgnorePep8
        for elem in component_class:
            component_class.index_of(elem)
