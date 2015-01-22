from nineml.abstraction_layer.componentclass.utils.equality_checker import ComponentEqualityChecker
from .base import PerNamespaceValidator
from .general import (
    AliasesAreNotRecursiveComponentValidator,
    NoUnresolvedSymbolsComponentValidator,
    NoDuplicatedObjectsComponentValidator,
    CheckNoLHSAssignmentsToMathsNamespaceComponentValidator)
from .namingconflicts import (LocalNameConflictsComponentValidator,
                              DimensionNameConflictsComponentValidator)
from .types import TypesComponentValidator
from .ports import PortConnectionsComponentValidator
