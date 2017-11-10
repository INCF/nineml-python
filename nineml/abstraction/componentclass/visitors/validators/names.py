"""
docstring needed

:copyright: Copyright 2010-2017 by the NineML Python team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from nineml.exceptions import NineMLUsageError
from nineml.visitors import BaseVisitor


# Check that the sub-components stored are all of the
# right types:
class LocalNameConflictsComponentValidator(BaseVisitor):

    """
    Check for conflicts between Aliases, StateVariables, Parameters, and
    EventPorts, and analog input ports

    We do not need to check for comflicts with output AnalogPorts, since, these
    will use names.
    """

    def __init__(self, component_class, **kwargs):  # @UnusedVariable
        BaseVisitor.__init__(self)
        self.symbols = []
        self.component_class = component_class
        self.visit(component_class)

    def check_conflicting_symbol(self, symbol):
        symbol = symbol.lower()
        if symbol in self.symbols:
            raise NineMLUsageError(
                "Found duplication of '{}' symbol in {} "
                "(Note that symbols must be case-insensitively unique despite "
                "being case-sensitive in general)"
                .format(symbol, self.component_class))
        self.symbols.append(symbol)

    def action_parameter(self, parameter, **kwargs):  # @UnusedVariable @IgnorePep8
        self.check_conflicting_symbol(parameter.name)

    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        # Exclude aliases defined within sub scopes (as they should match the
        # outer scope anyway)
        if alias in self.component_class.aliases:
            self.check_conflicting_symbol(alias.lhs)

    def action_constant(self, constant, **kwargs):  # @UnusedVariable @IgnorePep8
        self.check_conflicting_symbol(constant.name)

    def default_action(self, obj, nineml_cls, **kwargs):
        pass


class DimensionNameConflictsComponentValidator(BaseVisitor):

    def __init__(self, component_class, **kwargs):  # @UnusedVariable
        BaseVisitor.__init__(self)
        self.dimensions = {}
        self.visit(component_class)

    def check_conflicting_dimension(self, dimension):
        try:
            if dimension != self.dimensions[dimension.name]:
                err = ("Duplication of dimension name '{}' for differing "
                       "dimensions ('{}', '{}')"
                       .format(dimension.name, dimension,
                               self.dimensions[dimension.name]))
                raise NineMLUsageError(err)
        except KeyError:
            self.dimensions[dimension.name] = dimension

    def action_parameter(self, parameter, **kwargs):  # @UnusedVariable @IgnorePep8
        self.check_conflicting_dimension(parameter.dimension)

    def action_constant(self, constant, **kwargs):  # @UnusedVariable @IgnorePep8
        self.check_conflicting_dimension(constant.units.dimension)

    def default_action(self, obj, nineml_cls, **kwargs):
        pass
