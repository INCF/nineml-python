from ..componentclass import ComponentClass
from nineml.annotations import read_annotations, annotate_xml
from nineml.exceptions import handle_xml_exceptions


class RandomDistribution(ComponentClass):

    element_name = 'RandomDistribution'
    defining_attributes = ('name', '_parameters')

    def __init__(self, name, parameters=None):
        super(RandomDistribution, self).__init__(
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

    def dimension_of(self, element):
        try:
            resolver = self._dimension_resolver
        except AttributeError:
            resolver = RandomDistributionDimensionResolver(self)
            self._dimension_resolver = resolver
        return resolver.dimension_of(element)

    def _find_element(self, element):
        return RandomDistributionElementFinder(element).found_in(self)

    def validate(self):
        RandomDistributionValidator.validate_componentclass(self)

    @property
    def all_expressions(self):
        extractor = RandomDistributionExpressionExtractor()
        extractor.visit(self)
        return extractor.expressions

    def to_xml(self, **kwargs):  # @UnusedVariable
        self.standardize_unit_dimensions()
        self.validate()
        return RandomDistributionXMLWriter().visit(self)

    @classmethod
    def from_xml(cls, element, document, **kwargs):  # @UnusedVariable
        return RandomDistributionXMLLoader(
            document).load_randomdistributionclass(element)

from .visitors.cloner import RandomDistributionCloner
from .visitors.modifiers import(
    RandomDistributionRenameSymbol, RandomDistributionAssignIndices)
from .visitors.queriers import (RandomDistributionRequiredDefinitions,
                                RandomDistributionElementFinder,
                                RandomDistributionExpressionExtractor,
                                RandomDistributionDimensionResolver)
from .visitors.validators import RandomDistributionValidator
from .visitors.xml import (
    RandomDistributionXMLLoader, RandomDistributionXMLWriter)
