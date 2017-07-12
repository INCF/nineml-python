"""
This file contains utility classes for modifying components.

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from nineml.exceptions import NineMLRuntimeError, NineMLNameError
from .base import ComponentActionVisitor
from nineml.base import BaseNineMLVisitor


class ComponentModifier(object):

    """Utility classes for modifying components"""

    pass


class ComponentExpandPortDefinition(ComponentActionVisitor):

    def __init__(self, originalname, targetname):

        super(ComponentExpandPortDefinition, self).__init__(
            require_explicit_overrides=False)
        self.originalname = originalname
        self.targetname = targetname
        self.namemap = {originalname: targetname}

    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        alias.name_transform_inplace(self.namemap)


class ComponentExpandAliasDefinition(ComponentActionVisitor):

    """ An action-class that walks over a component, and expands an alias in
    Assignments, Aliases, TimeDerivatives and Conditions
    """

    def __init__(self, originalname, targetname):

        super(ComponentExpandAliasDefinition, self).__init__(
            require_explicit_overrides=False)
        self.originalname = originalname
        self.targetname = targetname
        self.namemap = {originalname: targetname}

    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        alias.rhs_name_transform_inplace(self.namemap)


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
        component_class._update_member_key(
            self.old_symbol_name, self.new_symbol_name)

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
        for elem in component_class.elements():
            component_class.index_of(elem)


class ComponentSubstituteAliases(BaseNineMLVisitor):
    """
    Substitutes all references to aliases in expressions with their RHS,
    so that all expressions are defined interms of inputs to the (e.g. analog
    receive/reduce ports and parameters), constants and reserved identifiers.
    The only aliases that are retained are ones that map to analog output ports

    Parameters
    ----------
    component_class : ComponentClass
        The component class to expand the expressions of
    new_name : str
        The name for the expanded class
    """

    def __init__(self, component_class):
        super(ComponentSubstituteAliases, self).__init__()
        self.component_class = component_class
        self.expanded_exprs = {}
        self.expanded_regimes = {}
        # Outputs of the class for which corresponding aliases needed to be
        # retained. Set in 'action' method of component_class
        self.outputs = set()
        self.visit(component_class)

    @property
    def expanded(self):
        return self._expanded

    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        return self.expand(alias)

    def expand(self, expr):
        # Get key to store the expression under. Aliases that are not part of
        # a regime use a key == None
        key = self.context_key(expr.key)
        try:
            expanded = self.expanded_exprs[key]
        except KeyError:
            expanded = expr.clone()
            for sym in expr.rhs_symbols:
                # Expand all symbols that are not inputs to the Dynamics class
                if str(sym) in self.component_class.alias_names:
                    alias = self.alias(str(sym))
                    expanded.subs(sym, self.expand(alias).rhs)
            expanded.simplify()
            self.expanded_exprs[key] = expanded
        return expanded

    def alias(self, name):
        alias = None
        for context in reversed(self.contexts):
            try:
                alias = context.parent.alias(name)
                break
            except (NineMLNameError, AttributeError):
                continue
        if alias is None:
            raise NineMLRuntimeError("Did not find alias '{}' in any "
                                     "context".format(name))
        return alias

    def remove_uneeded_aliases(self, container):
        container.remove(a for a in container.aliases
                         if a.name not in self.outputs)
