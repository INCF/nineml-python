"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from ...componentclass.validators.types import TypesComponentValidator
from ..base import DistributionBlock
from ..utils.visitors import DistributionActionVisitor


class TypesDistributionValidator(DistributionActionVisitor,
                                 TypesComponentValidator):

    def action_distributionblock(self, distributionblock):
        assert isinstance(distributionblock, DistributionBlock)
