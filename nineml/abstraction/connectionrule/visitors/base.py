from nineml.visitors import BaseVisitor
from ..base import ConnectionRule


class BaseConnectionRuleVisitor(BaseVisitor):

    visits_class = ConnectionRule
