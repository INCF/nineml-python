"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""


from ...componentclass.utils import ComponentActionVisitor


class RandomDistributionActionVisitor(ComponentActionVisitor):

    def visit_componentclass(self, componentclass, **kwargs):
        super(RandomDistributionActionVisitor, self).visit_componentclass(
            componentclass, **kwargs)
        if componentclass.randomdistribution:
            componentclass.randomdistribution.accept_visitor(self, **kwargs)

    def visit_randomdistributionblock(self, randomdistributionblock, **kwargs):
        self.action_randomdistributionblock(randomdistributionblock, **kwargs)
        nodes = randomdistributionblock.aliases
        for p in nodes:
            p.accept_visitor(self, **kwargs)

    def action_randomdistributionblock(self, randomdistributionblock, **kwargs):  # @UnusedVariable
        self.check_pass()
