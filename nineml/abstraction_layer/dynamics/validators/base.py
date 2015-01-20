"""
This file contains the ComponentValidator class for validating component

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from ...base.validators.types import TypesValidator
from ...base.validators.ports import (
    EventPortsValidator, OutputAnalogPortsValidator)
from ...base.validators.namingconflicts import (
    LocalNameConflictsValidator, DimensionNameConflictsValidator)
from ...base.validators.general import (
    TimeDerivativesAreDeclaredValidator, NoDuplicatedObjectsValidator,
    NoUnresolvedSymbolsValidator,
    PortConnectionsValidator, StateAssignmentsAreOnStateVariablesValidator,
    AliasesAreNotRecursiveValidator, RegimeGraphValidator,
    RegimeOnlyHasOneHandlerPerEventValidator,
    CheckNoLHSAssignmentsToMathsNamespaceValidator)
from ...base.validators.regimenames import DuplicateRegimeNamesValidator


class ComponentValidator(object):

    """Class for grouping all the component-validations tests together"""

    @classmethod
    def validate_componentclass(cls, componentclass):
        """
        Tests a componentclassclass against a variety of tests, to verify its
        internal structure
        """
        # Check class structure:
        TypesValidator(componentclass)
        NoDuplicatedObjectsValidator(componentclass)
        DuplicateRegimeNamesValidator(componentclass)
        LocalNameConflictsValidator(componentclass)
        DimensionNameConflictsValidator(componentclass)
        EventPortsValidator(componentclass)
        OutputAnalogPortsValidator(componentclass)
        TimeDerivativesAreDeclaredValidator(componentclass)
        StateAssignmentsAreOnStateVariablesValidator(componentclass)
        AliasesAreNotRecursiveValidator(componentclass)
        NoUnresolvedSymbolsValidator(componentclass)
        PortConnectionsValidator(componentclass)
        RegimeGraphValidator(componentclass)
        RegimeOnlyHasOneHandlerPerEventValidator(componentclass)
        CheckNoLHSAssignmentsToMathsNamespaceValidator(componentclass)
