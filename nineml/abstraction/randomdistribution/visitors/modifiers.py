"""
This file contains utility classes for modifying components.

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from ...componentclass.visitors.modifiers import (
    ComponentRenameSymbol, ComponentAssignIndices, ComponentFlattener,
    lookup_memo)
from .base import BaseRandomDistributionVisitor


class RandomDistributionRenameSymbol(ComponentRenameSymbol,
                                     BaseRandomDistributionVisitor):

    def action_randomdistribution(self, randomdistribution, **kwargs):
        return self.action_componentclass(randomdistribution, **kwargs)


class RandomDistributionAssignIndices(ComponentAssignIndices,
                                      BaseRandomDistributionVisitor):

    def action_randomdistribution(self, randomdistribution, **kwargs):
        return self.action_componentclass(randomdistribution, **kwargs)


class RandomDistributionFlattener(ComponentFlattener):

    @lookup_memo
    def visit_randomdistribution(self, component_class, **kwargs):
        ccn = component_class.__class__(
            name=component_class.name,
            standard_library=component_class.standard_library,
            parameters=[p.accept_visitor(self, **kwargs)
                        for p in component_class.parameters])
        return ccn
