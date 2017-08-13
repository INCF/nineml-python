from nineml.base import BaseNineMLVisitor
from ..base import RandomDistribution


class BaseRandomDistributionVisitor(BaseNineMLVisitor):

    class_to_visit = RandomDistribution

    def action_randomdistribution(self, randomdistribution, **kwargs):
        if not hasattr(self, 'action_componentclass'):
            return None
        return self.action_componentclass(randomdistribution, **kwargs)
