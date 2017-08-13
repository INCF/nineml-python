from nineml.base import BaseNineMLVisitor
from ..base import Dynamics


class BaseDynamicsVisitor(BaseNineMLVisitor):

    class_to_visit = Dynamics

    def action_dynamics(self, dynamics, **kwargs):
        if not hasattr(self, 'action_componentclass'):
            return None
        return self.action_componentclass(dynamics, **kwargs)
