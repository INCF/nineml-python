from ..componentclass import ComponentClass
from nineml.annotations import read_annotations, annotate_xml


class RandomDistributionClass(ComponentClass):

    element_name = 'RandomDistributionClass'
    defining_attributes = ('name', '_parameters')

    def __init__(self, name, parameters=None):
        super(RandomDistributionClass, self).__init__(
            name, parameters)

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

    @annotate_xml
    def to_xml(self):
        self.standardize_unit_dimensions()
        self.validate()
        return RandomDistributionClassXMLWriter().visit(self)

    @classmethod
    @read_annotations
    def from_xml(cls, element, document):
        return RandomDistributionClassXMLLoader(
            document).load_randomdistributionclass(element)

from .utils.cloner import RandomDistributionCloner
from .utils.modifiers import(
    RandomDistributionRenameSymbol, RandomDistributionAssignIndices)
from .utils.visitors import (RandomDistributionRequiredDefinitions,
                             RandomDistributionElementFinder)
from .validators import RandomDistributionValidator
from .utils.xml import (
    RandomDistributionClassXMLLoader, RandomDistributionClassXMLWriter)
