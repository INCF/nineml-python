from nineml.base import BaseNineMLVisitor
from ..base import ConnectionRule


class BaseConnectionRuleVisitor(BaseNineMLVisitor):

    class_to_visit = ConnectionRule

    def action_connectionrule(self, connectionrule, **kwargs):
        if not hasattr(self, 'action_componentclass'):
            return None
        return self.action_componentclass(connectionrule, **kwargs)
