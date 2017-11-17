"""
docstring needed

:copyright: Copyright 2010-2017 by the NineML Python team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from ...base import Parameter
from nineml.abstraction.expressions import Alias, Constant
from nineml.visitors import BaseVisitor
from nineml.units import Dimension, Unit


class TypesComponentValidator(BaseVisitor):

    def __init__(self, component_class, **kwargs):  # @UnusedVariable
        BaseVisitor.__init__(self)
        self.visit(component_class)

    def action_parameter(self, parameter, **kwargs):  # @UnusedVariable
        assert isinstance(parameter, Parameter), \
            "{} != {}".format(type(parameter), Parameter)

    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        assert isinstance(alias, Alias)

    def action_constant(self, constant, **kwargs):  # @UnusedVariable
        try:
            assert isinstance(constant, Constant)
        except:
            raise

    def action_dimension(self, dimension, **kwargs):  # @UnusedVariable
        assert isinstance(dimension, Dimension)

    def action_unit(self, unit, **kwargs):  # @UnusedVariable
        assert isinstance(unit, Unit)
