from .general import (
    AliasesAreNotRecursiveComponentValidator,
    NoUnresolvedSymbolsComponentValidator,
    CheckNoLHSAssignmentsToMathsNamespaceComponentValidator,
    DimensionalityComponentValidator)
from .names import (LocalNameConflictsComponentValidator,
                              DimensionNameConflictsComponentValidator)
from .types import TypesComponentValidator
