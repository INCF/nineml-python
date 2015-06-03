"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from ....componentclass.visitors.validators import (
    LocalNameConflictsComponentValidator,
    DimensionNameConflictsComponentValidator)
from . import BaseConnectionRuleValidator
from ..base import ConnectionRuleActionVisitor


# Check that the sub-components stored are all of the
# right types:
class LocalNameConflictsConnectionRuleValidator(
        LocalNameConflictsComponentValidator,
        ConnectionRuleActionVisitor):

    """
    Check for conflicts between Aliases, Parameters, and Ports
    """
    pass


class DimensionNameConflictsConnectionRuleValidator(
        DimensionNameConflictsComponentValidator,
        BaseConnectionRuleValidator):
    pass
