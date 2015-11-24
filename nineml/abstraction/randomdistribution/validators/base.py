"""
This file contains the RandomDistributionValidator class for validating component

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from .general import (
    AliasesAreNotRecursiveRandomDistributionValidator,
    NoUnresolvedSymbolsRandomDistributionValidator,
    NoDuplicatedObjectsRandomDistributionValidator,
    CheckNoLHSAssignmentsToMathsNamespaceRandomDistributionValidator)
from .namingconflicts import (
    LocalNameConflictsRandomDistributionValidator,
    DimensionNameConflictsRandomDistributionValidator)
from .ports import (
    PortConnectionsRandomDistributionValidator)
from .types import (
    TypesRandomDistributionValidator)


class RandomDistributionValidator(object):

    """Class for grouping all the component-validations tests together"""

    @classmethod
    def validate_componentclass(cls, componentclass):
        """
        Tests a componentclassclass against a variety of tests, to verify its
        internal structure
        """
        # Check class structure:
        TypesRandomDistributionValidator(componentclass)
#         NoDuplicatedObjectsRandomDistributionValidator(componentclass)  # Commented out until perNamespaceValidator is removed @IgnorePep8
#         LocalNameConflictsRandomDistributionValidator(componentclass)
#         DimensionNameConflictsRandomDistributionValidator(componentclass)
#         AliasesAreNotRecursiveRandomDistributionValidator(componentclass)
#         NoUnresolvedSymbolsRandomDistributionValidator(componentclass)
#         PortConnectionsRandomDistributionValidator(componentclass)
#         CheckNoLHSAssignmentsToMathsNamespaceRandomDistributionValidator(
#             componentclass)
