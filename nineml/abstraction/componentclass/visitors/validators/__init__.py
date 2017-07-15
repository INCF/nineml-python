from .general import (
    AliasesAreNotRecursiveComponentValidator,
    NoUnresolvedSymbolsComponentValidator,
    NoDuplicatedObjectsComponentValidator,
    CheckNoLHSAssignmentsToMathsNamespaceComponentValidator,
    DimensionalityComponentValidator)
from .names import (LocalNameConflictsComponentValidator,
                              DimensionNameConflictsComponentValidator)
from .types import TypesComponentValidator
