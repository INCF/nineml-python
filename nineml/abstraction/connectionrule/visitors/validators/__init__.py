from ....componentclass.visitors.validators.base import BaseValidator
from ..base import ConnectionRuleActionVisitor


class BaseConnectionRuleValidator(BaseValidator, ConnectionRuleActionVisitor):
    pass


from .base import ConnectionRuleValidator
