from nineml.visitors import BaseVisitor
from ..base import ConnectionRule


class BaseConnectionRuleVisitor(BaseVisitor):

    visit_as_class = ConnectionRule
