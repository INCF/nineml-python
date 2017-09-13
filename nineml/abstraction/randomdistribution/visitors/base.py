from nineml.visitors import BaseVisitor
from ..base import RandomDistribution


class BaseRandomDistributionVisitor(BaseVisitor):

    as_class = RandomDistribution
