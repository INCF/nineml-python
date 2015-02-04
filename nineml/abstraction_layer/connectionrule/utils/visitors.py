"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""


from ...componentclass.utils import ComponentActionVisitor


class ConnectionRuleActionVisitor(ComponentActionVisitor):

    def visit_componentclass(self, componentclass, **kwargs):
        super(ConnectionRuleActionVisitor, self).visit_componentclass(
            componentclass, **kwargs)
        componentclass.connectionruleblock.accept_visitor(self, **kwargs)

    def visit_connectionruleblock(self, connectionruleblock, **kwargs):
        self.action_connectionruleblock(connectionruleblock, **kwargs)
        nodes = connectionruleblock.aliases
        for p in nodes:
            p.accept_visitor(self, **kwargs)

    def action_connectionruleblock(self, connectionrule, **kwargs):  # @UnusedVariable @IgnorePep8
        self.check_pass()
