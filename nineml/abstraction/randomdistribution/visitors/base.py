from nineml.visitors import BaseVisitor
from ..base import RandomDistribution


class BaseRandomDistributionVisitor(BaseVisitor):

    visits_class = RandomDistribution
