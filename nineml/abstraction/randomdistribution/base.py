from ..componentclass import ComponentClass, MainBlock


class RandomDistributionBlock(MainBlock):

    defining_attributes = ('standard_library',)

    def __init__(self, standard_library):
        super(RandomDistributionBlock, self).__init__()
        self.standard_library = standard_library

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_randomdistributionblock(self, **kwargs)


class RandomDistribution(ComponentClass):

    defining_attributes = ('name', '_parameters', '_main_block')

    def __init__(self, name, randomdistributionblock, parameters=None,
                 url=None):
        super(RandomDistribution, self).__init__(
            name, parameters, main_block=randomdistributionblock, url=url)

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_componentclass(self, **kwargs)

    def __copy__(self, memo=None):  # @UnusedVariable
        return RandomDistributionCloner().visit(self)

    def rename_symbol(self, old_symbol, new_symbol):
        RandomDistributionRenameSymbol(self, old_symbol, new_symbol)

    def assign_indices(self):
        RandomDistributionAssignIndices(self)

    def required_for(self, expressions):
        return RandomDistributionRequiredDefinitions(self, expressions)

    def _find_element(self, element):
        return RandomDistributionElementFinder(element).found_in(self)

    def validate(self):
        RandomDistributionValidator.validate_componentclass(self)

    @property
    def standard_library(self):
        return self._main_block.standard_library

from .utils.cloner import RandomDistributionCloner
from .utils.modifiers import(
    RandomDistributionRenameSymbol, RandomDistributionAssignIndices)
from .utils.visitors import (RandomDistributionRequiredDefinitions,
                             RandomDistributionElementFinder)
from .validators import RandomDistributionValidator
