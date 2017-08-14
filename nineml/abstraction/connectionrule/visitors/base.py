from nineml.base import BaseNineMLVisitor
from ..base import ConnectionRule


class BaseConnectionRuleVisitor(BaseNineMLVisitor):

    class_to_visit = ConnectionRule

    def __getattr__(self, attr):
        if (attr in ('action_connectionrule') and
                hasattr(self, 'action_componentclass')):
            return self.action_componentclass
        else:
            raise AttributeError(attr)
