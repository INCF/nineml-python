"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from ...base import ComponentClass, Parameter
from nineml.abstraction.expressions import Alias, Constant
from nineml.base import BaseNineMLVisitor


class TypesComponentValidator(BaseNineMLVisitor):

    def __init__(self, component_class, **kwargs):  # @UnusedVariable
        BaseNineMLVisitor.__init__(self)
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
