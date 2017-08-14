from nineml.base import BaseNineMLVisitor
from ..base import ConnectionRule


class BaseConnectionRuleVisitor(BaseNineMLVisitor):

    class_to_visit = ConnectionRule
