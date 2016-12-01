"""
This file contains the ConnectionRuleValidator class for validating component

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from .general import (
    AliasesAreNotRecursiveConnectionRuleValidator,
    NoUnresolvedSymbolsConnectionRuleValidator,
    NoDuplicatedObjectsConnectionRuleValidator,
    CheckNoLHSAssignmentsToMathsNamespaceConnectionRuleValidator)
from .names import (
    LocalNameConflictsConnectionRuleValidator,
    DimensionNameConflictsConnectionRuleValidator)
from .ports import (
    PortConnectionsConnectionRuleValidator)
from .types import (
    TypesConnectionRuleValidator)


class ConnectionRuleValidator(object):

    """Class for grouping all the component-validations tests together"""

    @classmethod
    def validate_componentclass(cls, component_class, **kwargs):
        """
        Tests a componentclassclass against a variety of tests, to verify its
        internal structure
        """
        # Check class structure:
        TypesConnectionRuleValidator(component_class, **kwargs)
#         NoDuplicatedObjectsConnectionRuleValidator(component_class, **kwargs)
#         LocalNameConflictsConnectionRuleValidator(component_class, **kwargs)
#         DimensionNameConflictsConnectionRuleValidator(component_class,
#                                                       **kwargs)
#         AliasesAreNotRecursiveConnectionRuleValidator(component_class,
#                                                       **kwargs)
#         NoUnresolvedSymbolsConnectionRuleValidator(component_class, **kwargs)
#         PortConnectionsConnectionRuleValidator(component_class, **kwargs)
#         CheckNoLHSAssignmentsToMathsNamespaceConnectionRuleValidator(
#             component_class, **kwargs)
