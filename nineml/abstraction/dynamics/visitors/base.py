from nineml.base import BaseNineMLVisitor
from ..base import Dynamics


class BaseDynamicsVisitor(BaseNineMLVisitor):

    class_to_visit = Dynamics

    def __getattr__(self, attr):
        if (attr in ('action_dynamics', 'action_multidynamics') and
                hasattr(self, 'action_componentclass')):
            return self.action_componentclass
        else:
            raise AttributeError(attr)
