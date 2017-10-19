"""
docstring needed

:copyright: Copyright 2010-2017 by the NineML Python team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from nineml.utils import assert_no_duplicates
from ....componentclass.visitors.validators import (
    LocalNameConflictsComponentValidator,
    DimensionNameConflictsComponentValidator)
from nineml.exceptions import NineMLUsageError
from ..base import BaseDynamicsVisitor


# Check that the sub-components stored are all of the
# right types:
class LocalNameConflictsDynamicsValidator(
        LocalNameConflictsComponentValidator,
        BaseDynamicsVisitor):

    """
    Check for conflicts between Aliases, StateVariables, Parameters, and
    EventPorts, and analog input ports

    We do not need to check for comflicts with output AnalogPorts, since, these
    will use names.
    """

    def action_statevariable(self, state_variable, **kwargs):  # @UnusedVariable @IgnorePep8
        self.check_conflicting_symbol(symbol=state_variable.name)

    def action_analogreceiveport(self, port, **kwargs):  # @UnusedVariable @IgnorePep8
        self.check_conflicting_symbol(symbol=port.name)

    def action_analogreduceport(self, port, **kwargs):  # @UnusedVariable @IgnorePep8
        self.check_conflicting_symbol(symbol=port.name)

    def action_eventreceiveport(self, port, **kwargs):  # @UnusedVariable @IgnorePep8
        self.check_conflicting_symbol(symbol=port.name)


class DimensionNameConflictsDynamicsValidator(
        DimensionNameConflictsComponentValidator,
        BaseDynamicsVisitor):

    def action_statevariable(self, state_variable, **kwargs):  # @UnusedVariable @IgnorePep8
        self.check_conflicting_dimension(state_variable.dimension)

    def action_analogreceiveport(self, port, **kwargs):  # @UnusedVariable @IgnorePep8
        self.check_conflicting_dimension(port.dimension)

    def action_analogreduceport(self, port, **kwargs):  # @UnusedVariable @IgnorePep8
        self.check_conflicting_dimension(port.dimension)

    def action_analogsendport(self, port, **kwargs):  # @UnusedVariable @IgnorePep8
        self.check_conflicting_dimension(port.dimension)


class DuplicateRegimeNamesDynamicsValidator(BaseDynamicsVisitor):

    def __init__(self, component_class, **kwargs):  # @UnusedVariable
        super(DuplicateRegimeNamesDynamicsValidator, self).__init__()
        self.visit(component_class)

    def action_dynamics(self, component_class, **kwargs):  # @UnusedVariable @IgnorePep8
        regime_names = [r.name for r in component_class.regimes]
        assert_no_duplicates(regime_names)

    def default_action(self, obj, nineml_cls, **kwargs):
        pass


class RegimeAliasMatchesBaseScopeValidator(BaseDynamicsVisitor):

    def __init__(self, component_class, **kwargs):  # @UnusedVariable
        super(RegimeAliasMatchesBaseScopeValidator, self).__init__()
        self.component_class = component_class

    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        if alias.name not in self.component_class.alias_names:
            raise NineMLUsageError(
                "Alias '{}' in regime scope does not match any in the base "
                "scope of the Dynamics class '{}'"
                .format(alias.name,
                        "', '".join(self.component_class.alias_names)))
