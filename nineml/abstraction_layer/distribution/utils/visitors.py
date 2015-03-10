"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""


from ...componentclass.utils import (
    ComponentActionVisitor, ComponentElementFinder)
from ...componentclass.utils.visitors import ComponentRequiredDefinitions


class DistributionActionVisitor(ComponentActionVisitor):

    def visit_componentclass(self, componentclass, **kwargs):
        super(DistributionActionVisitor, self).visit_componentclass(
            componentclass, **kwargs)
        componentclass._main_block.accept_visitor(self, **kwargs)

    def visit_distributionblock(self, distributionblock, **kwargs):
        self.action_distributionblock(distributionblock, **kwargs)
        nodes = distributionblock.aliases
        for p in nodes:
            p.accept_visitor(self, **kwargs)

    def action_distributionblock(self, distributionblock, **kwargs):  # @UnusedVariable @IgnorePep8
        self.check_pass()


class DistributionRequiredDefinitions(ComponentRequiredDefinitions,
                                      DistributionActionVisitor):

    def __init__(self, componentclass, expressions):
        DistributionActionVisitor.__init__(self,
                                           require_explicit_overrides=False)
        ComponentRequiredDefinitions.__init__(self, componentclass,
                                              expressions)

    def action_distributionblock(self, distributionblock, **kwargs):  # @UnusedVariable @IgnorePep8
        self.action_mainblock(distributionblock, **kwargs)


class DistributionElementFinder(ComponentElementFinder,
                                DistributionActionVisitor):

    def __init__(self, element):
        DistributionActionVisitor.__init__(self,
                                           require_explicit_overrides=True)
        ComponentElementFinder.__init__(self, element)

    def action_distributionblock(self, dynamicsblock, **kwargs):
        pass
