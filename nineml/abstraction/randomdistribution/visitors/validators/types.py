"""
docstring needed

:copyright: Copyright 2010-2017 by the NineML Python team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from ....componentclass.visitors.validators.types import (
    TypesComponentValidator)
from ..base import BaseRandomDistributionVisitor
from ...base import RandomDistribution


class TypesRandomDistributionValidator(TypesComponentValidator,
                                       BaseRandomDistributionVisitor):

    def action_randomdistribution(self, randomdistribution, **kwargs):  # @UnusedVariable @IgnorePep8
        assert isinstance(randomdistribution, RandomDistribution)
