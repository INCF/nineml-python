from nineml.base import BaseNineMLVisitor
from ..base import RandomDistribution


class BaseRandomDistributionVisitor(BaseNineMLVisitor):

    class_to_visit = RandomDistribution
