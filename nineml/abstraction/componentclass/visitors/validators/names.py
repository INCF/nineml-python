"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from nineml.exceptions import NineMLRuntimeError
from base import BaseValidator


# Check that the sub-components stored are all of the
# right types:
class LocalNameConflictsComponentValidator(BaseValidator):

    """
    Check for conflicts between Aliases, StateVariables, Parameters, and
    EventPorts, and analog input ports

    We do not need to check for comflicts with output AnalogPorts, since, these
    will use names.
    """

    def __init__(self, component_class):
        BaseValidator.__init__(
            self, require_explicit_overrides=False)
        self.symbols = []
        self.component_class = component_class
        self.visit(component_class)

    def check_conflicting_symbol(self, symbol):
        if symbol in self.symbols:
            raise NineMLRuntimeError(
                "Duplication of symbol found: {}".format(symbol))
        self.symbols.append(symbol)

    def action_parameter(self, parameter, **kwargs):  # @UnusedVariable @IgnorePep8
        self.check_conflicting_symbol(symbol=parameter.name)

    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        # Exclude aliases defined within sub scopes (as they should match the
        # outer scope anyway)
        if alias in self.component_class.aliases:
            self.check_conflicting_symbol(symbol=alias.lhs)

    def action_constant(self, constant, **kwargs):  # @UnusedVariable @IgnorePep8
        self.check_conflicting_symbol(symbol=constant.name)


class DimensionNameConflictsComponentValidator(BaseValidator):

    def __init__(self, component_class):
        BaseValidator.__init__(
            self, require_explicit_overrides=False)
        self.dimensions = {}
        self.visit(component_class)

    def check_conflicting_dimension(self, dimension):
        try:
            if dimension != self.dimensions[dimension.name]:
                err = ("Duplication of dimension name '{}' for differing "
                       "dimensions ('{}', '{}')"
                       .format(dimension.name, dimension,
                               self.dimensions[dimension.name]))
                raise NineMLRuntimeError(err)
        except KeyError:
            self.dimensions[dimension.name] = dimension

    def action_parameter(self, parameter, **kwargs):  # @UnusedVariable @IgnorePep8
        self.check_conflicting_dimension(parameter.dimension)

    def action_constant(self, constant, **kwargs):  # @UnusedVariable @IgnorePep8
        self.check_conflicting_dimension(constant.units.dimension)
