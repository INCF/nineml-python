from .. import BaseALObject
from ..componentclass import ComponentClass


class DistributionBlock(BaseALObject):

    defining_attributes = ('standard_library',)

    def __init__(self, standard_library):
        self.standard_library = standard_library

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_distributionblock(self, **kwargs)


class DistributionClass(ComponentClass):

    defining_attributes = ('name', '_parameters', '_main_block')

    def __init__(self, name, distributionblock, parameters=None):
        super(DistributionClass, self).__init__(
            name, parameters, main_block=distributionblock)

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_componentclass(self, **kwargs)

    def __deepcopy__(self, memo=None):  # @UnusedVariable
        return DistributionCloner().visit(self)

    def rename_symbol(self, old_symbol, new_symbol):
        DistributionRenameSymbol(self, old_symbol, new_symbol)

    def required_for(self, expressions):
        return DistributionRequiredDefinitions(self, expressions)

from .utils.cloner import DistributionCloner
from .utils.modifiers import DistributionRenameSymbol
from .utils.visitors import DistributionRequiredDefinitions
