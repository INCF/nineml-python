from nineml.base import BaseNineMLVisitor


class BaseDynamicsVisitor(BaseNineMLVisitor):

    def action_dynamics(self, **kwargs):
        return self.action_componentclass(self, **kwargs)
