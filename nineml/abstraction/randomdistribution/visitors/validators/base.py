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
from .names import (
    LocalNameConflictsRandomDistributionValidator,
    DimensionNameConflictsRandomDistributionValidator)
from .ports import (
    PortConnectionsRandomDistributionValidator)
from .types import (
    TypesRandomDistributionValidator)


class RandomDistributionValidator(object):

    """Class for grouping all the component-validations tests together"""

    @classmethod
    def validate_componentclass(cls, component_class, **kwargs):
        """
        Tests a componentclassclass against a variety of tests, to verify its
        internal structure
        """
        # Check class structure:
        TypesRandomDistributionValidator(component_class, **kwargs)
#         NoDuplicatedObjectsRandomDistributionValidator(component_class,
#                                                        **kwargs)
#         LocalNameConflictsRandomDistributionValidator(component_class,
#                                                       **kwargs)
#         DimensionNameConflictsRandomDistributionValidator(component_class,
#                                                           **kwargs)
#         AliasesAreNotRecursiveRandomDistributionValidator(component_class,
#                                                           **kwargs)
#         NoUnresolvedSymbolsRandomDistributionValidator(component_class,
#                                                        **kwargs)
#         PortConnectionsRandomDistributionValidator(component_class, **kwargs)
#         CheckNoLHSAssignmentsToMathsNamespaceRandomDistributionValidator(
#             component_class, **kwargs)
