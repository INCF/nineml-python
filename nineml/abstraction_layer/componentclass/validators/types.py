"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from ..utils import ComponentActionVisitor
from ..base import ComponentClass, Parameter
from ...expressions import Alias, Constant, RandomVariable, RandomDistribution


class TypesComponentValidator(ComponentActionVisitor):

    def __init__(self, component_class):
        super(TypesComponentValidator, self).__init__()
        self.visit(component_class)

    def action_componentclass(self, component):
        assert isinstance(component, ComponentClass)

    def action_parameter(self, parameter):
        assert isinstance(parameter, Parameter), \
            "{} != {}".format(type(parameter), Parameter)

    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        assert isinstance(alias, Alias)

    def action_constant(self, constant, **kwargs):  # @UnusedVariable
        assert isinstance(constant, Constant)

    def action_randomvariable(self, randomvariable, **kwargs):  # @UnusedVariable @IgnorePep8
        assert isinstance(randomvariable, RandomVariable)

    def action_randomdistribution(self, random_distribution, **kwargs):  # @UnusedVariable @IgnorePep8
        assert isinstance(random_distribution, RandomDistribution)
