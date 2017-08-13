from nineml.base import BaseNineMLVisitor


class BaseConnectionRuleVisitor(BaseNineMLVisitor):

    def action_connectionrule(self, **kwargs):
        return self.action_componentclass(self, **kwargs)
