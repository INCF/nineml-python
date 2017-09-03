from nineml.visitors import BaseVisitor
from ..base import Dynamics


class BaseDynamicsVisitor(BaseVisitor):

    visit_as_class = Dynamics
