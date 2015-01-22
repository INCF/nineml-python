from equality_checker import ComponentEqualityChecker
from .base import PerNamespaceValidator
from .general import (
    AliasesAreNotRecursiveComponentValidator,
    NoUnresolvedSymbolsComponentValidator, PortConnectionsComponentValidator,
    NoDuplicatedObjectsComponentValidator,
    CheckNoLHSAssignmentsToMathsNamespaceComponentValidator)
from .namingconflicts import (LocalNameConflictsComponentValidator,
                              DimensionNameConflictsComponentValidator)
from .types import TypesComponentValidator
