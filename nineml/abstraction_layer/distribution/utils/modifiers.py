"""
This file contains utility classes for modifying components.

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from .cloner import DistributionExpandPortDefinition
from .visitors import DistributionActionVisitor
from ...componentclass.utils.modifiers import (
    ComponentModifier, ComponentRenameSymbol, ComponentAssignIndices)


class DistributionModifier(ComponentModifier):

    """Utility classes for modifying components"""

    _ExpandPortDefinition = DistributionExpandPortDefinition


class DistributionRenameSymbol(DistributionActionVisitor,
                               ComponentRenameSymbol):

    """ Can be used for:
    Aliases
    """
    pass


class DistributionAssignIndices(ComponentAssignIndices,
                                   DistributionActionVisitor):
    pass
