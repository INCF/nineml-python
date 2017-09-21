"""
This file contains the RandomDistributionValidator class for validating component

:copyright: Copyright 2010-2017 by the NineML Python team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from builtins import object
from nineml.visitors.validators import NoDuplicatedObjectsValidator
from .general import (
    AliasesAreNotRecursiveRandomDistributionValidator,
    NoUnresolvedSymbolsRandomDistributionValidator,
    CheckNoLHSAssignmentsToMathsNamespaceRandomDistributionValidator)
from .names import (
    LocalNameConflictsRandomDistributionValidator,
    DimensionNameConflictsRandomDistributionValidator)
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
        NoDuplicatedObjectsValidator(component_class, **kwargs)
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
