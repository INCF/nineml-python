"""
docstring needed

:copyright: Copyright 2010-2017 by the NineML Python team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from ....componentclass.visitors.validators import (
    LocalNameConflictsComponentValidator,
    DimensionNameConflictsComponentValidator)
from ..base import BaseConnectionRuleVisitor


# Check that the sub-components stored are all of the
# right types:
class LocalNameConflictsConnectionRuleValidator(
        LocalNameConflictsComponentValidator,
        BaseConnectionRuleVisitor):

    """
    Check for conflicts between Aliases, Parameters, and Ports
    """
    pass


class DimensionNameConflictsConnectionRuleValidator(
        DimensionNameConflictsComponentValidator,
        BaseConnectionRuleVisitor):
    pass
