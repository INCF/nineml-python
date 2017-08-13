from nineml.base import BaseNineMLVisitor


class BaseRandomDistributionVisitor(BaseNineMLVisitor):

    def action_randomdistribution(self, **kwargs):
        return self.action_componentclass(self, **kwargs)
