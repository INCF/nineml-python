from nineml.base import BaseNineMLVisitor
from ..base import Dynamics


class BaseDynamicsVisitor(BaseNineMLVisitor):

    class_to_visit = Dynamics
