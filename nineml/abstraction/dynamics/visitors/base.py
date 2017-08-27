from nineml.visitors import BaseVisitor
from ..base import Dynamics


class BaseDynamicsVisitor(BaseVisitor):

    visits_class = Dynamics
