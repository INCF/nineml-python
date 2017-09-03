from nineml.visitors import BaseVisitor
from ..base import RandomDistribution


class BaseRandomDistributionVisitor(BaseVisitor):

    visit_as_class = RandomDistribution
