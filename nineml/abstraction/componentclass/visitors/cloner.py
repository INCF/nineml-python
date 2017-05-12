"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from ...expressions.utils import is_builtin_symbol
from .base import ComponentVisitor
from nineml.base import ContainerObject, accessor_name_from_type, clone_id
from ..base import Parameter
from ...expressions import Constant, Alias


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


class ComponentCloner(ComponentVisitor):
    """
    Abstract base class for cloning abstraction layer objects

    Parameters
    ----------
    memo : dict[int, BaseNineMLObject]
        A dictionary containing mapping of object IDs of previously cloned
        objects to avoid re-cloning the same objects
    """
    def __init__(self, memo=None, **kwargs):
        super(ComponentCloner, self).__init__(**kwargs)
        if memo is None:
            memo = {}
        self.memo = memo

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
            value=constant.value, units=constant.units)
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
