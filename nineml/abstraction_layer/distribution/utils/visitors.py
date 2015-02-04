"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""


from ...componentclass.utils import ComponentActionVisitor


class DistributionActionVisitor(ComponentActionVisitor):

    def visit_componentclass(self, componentclass, **kwargs):
        super(DistributionActionVisitor, self).visit_componentclass(
            componentclass, **kwargs)
        if componentclass.distribution:
            componentclass.distribution.accept_visitor(self, **kwargs)

    def visit_distributionblock(self, distributionblock, **kwargs):
        self.action_distributionblock(distributionblock, **kwargs)
        nodes = distributionblock.aliases
        for p in nodes:
            p.accept_visitor(self, **kwargs)

    def action_distributionblock(self, distributionblock, **kwargs):  # @UnusedVariable
        self.check_pass()
