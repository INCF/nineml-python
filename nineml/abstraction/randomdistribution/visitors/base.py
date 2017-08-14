from nineml.base import BaseNineMLVisitor
from ..base import RandomDistribution


class BaseRandomDistributionVisitor(BaseNineMLVisitor):

    class_to_visit = RandomDistribution

    def __getattr__(self, attr):
        if (attr in ('action_randomdistribution') and
                hasattr(self, 'action_componentclass')):
            return self.action_componentclass
        else:
            raise AttributeError(attr)
