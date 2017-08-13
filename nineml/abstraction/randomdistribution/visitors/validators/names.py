"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from ....componentclass.visitors.validators import (
    LocalNameConflictsComponentValidator,
    DimensionNameConflictsComponentValidator)


# Check that the sub-components stored are all of the
# right types:
class LocalNameConflictsRandomDistributionValidator(
        LocalNameConflictsComponentValidator):

    """
    Check for conflicts between Aliases, Parameters, and Ports
    """
    pass


class DimensionNameConflictsRandomDistributionValidator(
        DimensionNameConflictsComponentValidator):
    pass
