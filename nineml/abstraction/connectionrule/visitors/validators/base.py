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
from .namingconflicts import (
    LocalNameConflictsConnectionRuleValidator,
    DimensionNameConflictsConnectionRuleValidator)
from .ports import (
    PortConnectionsConnectionRuleValidator)
from .types import (
    TypesConnectionRuleValidator)


class ConnectionRuleValidator(object):

    """Class for grouping all the component-validations tests together"""

    @classmethod
    def validate_componentclass(cls, component_class):
        """
        Tests a componentclassclass against a variety of tests, to verify its
        internal structure
        """
        # Check class structure:
        TypesConnectionRuleValidator(component_class)
#         NoDuplicatedObjectsConnectionRuleValidator(component_class)  # Commented out until perNamespaceValidator is removed @IgnorePep8
#         LocalNameConflictsConnectionRuleValidator(component_class)
#         DimensionNameConflictsConnectionRuleValidator(component_class)
#         AliasesAreNotRecursiveConnectionRuleValidator(component_class)
#         NoUnresolvedSymbolsConnectionRuleValidator(component_class)
#         PortConnectionsConnectionRuleValidator(component_class)
#         CheckNoLHSAssignmentsToMathsNamespaceConnectionRuleValidator(
#             component_class)
