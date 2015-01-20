from equality_checker import ComponentEqualityChecker
from .base import PerNamespaceValidator
from .general import (
    AliasesAreNotRecursiveValidator, TimeDerivativesAreDeclaredValidator,
    StateAssignmentsAreOnStateVariablesValidator, NoUnresolvedSymbolsValidator,
    PortConnectionsValidator, RegimeGraphValidator,
    NoDuplicatedObjectsValidator, RegimeOnlyHasOneHandlerPerEventValidator,
    CheckNoLHSAssignmentsToMathsNamespaceValidator)
from .namingconflicts import (LocalNameConflictsValidator,
                              DimensionNameConflictsValidator)
from .ports import (EventPortsValidator, OutputAnalogPortsValidator)
from .regimenames import DuplicateRegimeNamesValidator
from .types import TypesValidator
