from nineml.visitors import BaseVisitor
from ..base import ConnectionRule


class BaseConnectionRuleVisitor(BaseVisitor):

    as_class = ConnectionRule
