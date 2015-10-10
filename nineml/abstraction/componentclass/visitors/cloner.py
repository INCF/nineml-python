"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from ...expressions.utils import is_builtin_symbol
from .base import ComponentVisitor
from nineml.base import ContainerObject, accessor_name_from_type
from ..base import Parameter, Constant, Alias


class ComponentCloner(ComponentVisitor):

    def prefix_variable(self, variable, **kwargs):
        prefix = kwargs.get('prefix', '')
        prefix_excludes = kwargs.get('prefix_excludes', [])
        if variable in prefix_excludes:
            return variable

        if is_builtin_symbol(variable):
            return variable
        else:
            return prefix + variable

    def visit_parameter(self, parameter, **kwargs):
        return Parameter(
            name=self.prefix_variable(parameter.name, **kwargs),
            dimension=parameter.dimension)

    def visit_alias(self, alias, **kwargs):
        new_alias = Alias(lhs=alias.lhs, rhs=alias.rhs)
        name_map = dict([(a, self.prefix_variable(a, **kwargs))
                         for a in new_alias.atoms])
        new_alias.name_transform_inplace(name_map=name_map)
        # FIXME:? TGC 1/15 Doesn't the LHS need updating too?
        return new_alias

    def visit_constant(self, constant, **kwargs):  # @UnusedVariable
        new_constant = Constant(
            name=self.prefix_variable(constant.name, **kwargs),
            value=constant.value, units=constant.units)
        return new_constant

    def copy_indices(self, source, destination, **kwargs):  # @UnusedVariable
        if source == destination:  # a work around until I remove NSs
            assert isinstance(source, ContainerObject)
            for s in source.elements():
                d = destination._member_dict(s)[s._name]
                key = accessor_name_from_type(source, s)
                index = source.index_of(source, s)
                destination._indices[key][d] = index
