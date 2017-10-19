"""
This file contains utility classes for modifying components.

:copyright: Copyright 2010-2017 by the NineML Python team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from nineml.exceptions import NineMLUsageError, NineMLNameError
from nineml.visitors import BaseVisitor, BasePreAndPostVisitorWithContext
from nineml.abstraction.expressions import Expression


class ComponentRenameSymbol(BaseVisitor):

    """ Can be used for:
    StateVariables, Aliases, Ports
    """

    def __init__(self, component_class, old_symbol_name, new_symbol_name):
        super(ComponentRenameSymbol, self).__init__()
        self.old_symbol_name = old_symbol_name
        self.new_symbol_name = new_symbol_name
        self.namemap = {old_symbol_name: new_symbol_name}

        self.lhs_changes = []
        self.rhs_changes = []
        self.port_changes = []

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

    def default_action(self, obj, nineml_cls, **kwargs):
        pass


class ComponentSubstituteAliases(BasePreAndPostVisitorWithContext):
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
        # Outputs of the class for which corresponding aliases needed to be
        # retained. Set in 'action' method of component_class
        self.outputs = set()
        # Cache to the previously substituted aliases
        self.cache = {}
        self.visit(component_class)

    def substitute(self, expr):
        """
        Substitute alias symbols in expression with equivalent expression
        of inputs, constants and reserved identifiers

        Parameters
        ----------
        nineml_obj : Expression
            An expression object to substitute alias symbols in
        """
        if expr.temporary:
            raise NineMLUsageError(
                "Attempting to substitute aliases using temporary object "
                "{}({})".format(type(expr).__name__, expr))
        assert isinstance(expr, Expression)
        try:
            rhs = self.cache[expr.id]
        except KeyError:
            for sym in list(expr.rhs_symbols):
                # Substitute all alias symbols with their RHS expresssions
                if str(sym) in self.component_class.alias_names:
                    alias = self.get_alias(str(sym))
                    expr.subs(sym, self.substitute(alias))
            self.cache[expr.id] = rhs = expr.rhs
        return rhs

    def get_alias(self, name):
        alias = None
        for context in reversed(self.contexts):
            try:
                alias = context.parent.alias(name)
                break
            except (NineMLNameError, AttributeError):
                continue
        if alias is None:
            raise NineMLUsageError("Did not find alias '{}' in any "
                                     "context".format(name))
        return alias

    def remove_uneeded_aliases(self, container):
        container.remove(*(a for a in container.aliases
                           if a.name not in self.outputs))

    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        return self.substitute(alias)

    def default_action(self, obj, nineml_cls, **kwargs):
        pass

    def default_post_action(self, *args, **kwargs):
        pass
