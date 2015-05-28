"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""


from ...componentclass.visitors import (
    ComponentActionVisitor, ComponentElementFinder)



class ConnectionRuleActionVisitor(ComponentActionVisitor):

    def visit_componentclass(self, component_class, **kwargs):
        super(ConnectionRuleActionVisitor, self).visit_componentclass(
            component_class, **kwargs)

