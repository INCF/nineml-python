from ....componentclass.visitors.validators.base import BaseValidator
from ..base import RandomDistributionActionVisitor


class BaseRandomDistributionValidator(BaseValidator,
                                      RandomDistributionActionVisitor):
    pass


from .base import RandomDistributionValidator
