"""
This file contains utility classes for modifying components.

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from ...componentclass.visitors.modifiers import ComponentRenameSymbol
from .base import BaseRandomDistributionVisitor


class RandomDistributionRenameSymbol(ComponentRenameSymbol,
                                     BaseRandomDistributionVisitor):

    def action_randomdistribution(self, randomdistribution, **kwargs):
        return self.action_componentclass(randomdistribution, **kwargs)
