"""
This file contains utility classes for modifying components.

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from nineml.exceptions import NineMLRuntimeError, NineMLNameError
from nineml.visitors import BaseVisitor
from nineml.abstraction.expressions import Expression, Constant, Alias
from nineml.abstraction.expressions.utils import is_builtin_symbol
from nineml.base import (
    ContainerObject, accessor_name_from_type, clone_id)
from ..base import Parameter


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

    def default_action(self, obj, **kwargs):
        pass


class ComponentAssignIndices(BaseVisitor):

    """
    Forces the generation of indices for all commonly index elements of the
    component class
    """

    def __init__(self, component_class):
        super(ComponentAssignIndices, self).__init__()
        self.component_class = component_class
        self.visit(component_class)

    def action_componentclass(self, component_class, **kwargs):  # @UnusedVariable @IgnorePep8
        for elem in component_class.elements():
            component_class.index_of(elem)

    def default_action(self, obj, **kwargs):
        pass


class ComponentSubstituteAliases(BaseVisitor):
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
        assert isinstance(expr, Expression)
        # Get key to store the expression under. Aliases that are not part of
        # a regime use a key == None
        cache_key = self.context_key(expr.key)
        try:
            rhs = self.cache[cache_key]
        except KeyError:
            for sym in list(expr.rhs_symbols):
                # Substitute all alias symbols with their RHS expresssions
                if str(sym) in self.component_class.alias_names:
                    alias = self.get_alias(str(sym))
                    expr.subs(sym, self.substitute(alias))
            self.cache[cache_key] = rhs = expr.rhs
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
            raise NineMLRuntimeError("Did not find alias '{}' in any "
                                     "context".format(name))
        return alias

    def remove_uneeded_aliases(self, container):
        container.remove(*(a for a in container.aliases
                           if a.name not in self.outputs))

    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        return self.substitute(alias)

    def default_action(self, obj, **kwargs):
        pass


def lookup_memo(visit_elem):
    """
    Decorator that checks the cloner's "memo" dictionary for a previously
    cloned version before returning a new clone
    """
    def visit_elem_with_memo_lookup(cloner, elem, **kwargs):
        try:
            clone = cloner.memo[clone_id(elem)]
            assert clone == visit_elem(cloner, elem, **kwargs)
        except KeyError:
            clone = visit_elem(cloner, elem, **kwargs)
            cloner.memo[clone_id(elem)] = clone
        return clone
    return visit_elem_with_memo_lookup


class ComponentFlattener(object):
    """
    Abstract base class for cloning abstraction layer objects

    Parameters
    ----------
    memo : dict[int, BaseNineMLObject]
        A dictionary containing mapping of object IDs of previously cloned
        objects to avoid re-cloning the same objects
    """
    def __init__(self, component_class, memo=None, **kwargs):
        super(ComponentFlattener, self).__init__(**kwargs)
        if memo is None:
            memo = {}
        self.memo = memo
        self.flattened = self.visit_componentclass(component_class)

    def prefix_variable(self, variable, **kwargs):
        prefix = kwargs.get('prefix', '')
        prefix_excludes = kwargs.get('prefix_excludes', [])
        if variable in prefix_excludes:
            return variable

        if is_builtin_symbol(variable):
            return variable
        else:
            return prefix + variable

    @lookup_memo
    def visit_parameter(self, parameter, **kwargs):
        return Parameter(
            name=self.prefix_variable(parameter.name, **kwargs),
            dimension=parameter.dimension.clone(self.memo, **kwargs))

    @lookup_memo
    def visit_alias(self, alias, **kwargs):
        new_alias = Alias(lhs=alias.lhs, rhs=alias.rhs)
        name_map = dict([(a, self.prefix_variable(a, **kwargs))
                         for a in new_alias.atoms])
        new_alias.name_transform_inplace(name_map=name_map)
        # FIXME:? TGC 1/15 Doesn't the LHS need updating too?
        return new_alias

    @lookup_memo
    def visit_constant(self, constant, **kwargs):  # @UnusedVariable
        new_constant = Constant(
            name=self.prefix_variable(constant.name, **kwargs),
            value=constant.value, units=constant.units.clone(memo=self.memo,
                                                             **kwargs))
        return new_constant

    def copy_indices(self, source, destination, **kwargs):  # @UnusedVariable
        # Copy indices if destination is of same type (i.e. not flattened)
        if source.nineml_type == destination.nineml_type:
            assert isinstance(source, ContainerObject)
            for s in source.elements():
                d = destination._member_dict(s)[s.key]
                key = accessor_name_from_type(source.class_to_member, s)
                index = source.index_of(s)
                destination._indices[key][d] = index

