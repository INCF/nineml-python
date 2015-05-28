from ..componentclass import ComponentClass
from nineml.annotations import read_annotations, annotate_xml
from nineml.exceptions import handle_xml_exceptions


class RandomDistribution(ComponentClass):

    element_name = 'RandomDistributionClass'
    defining_attributes = ('name', '_parameters', 'standard_library')

    def __init__(self, name, standard_library, parameters=None,
                 url=None):
        super(RandomDistributionClass, self).__init__(
            name, parameters, url=url)
        self.standard_library = standard_library

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
    def all_expressions(self):
        return RandomDistributionExpressionExtractor().visit(self)

    @property
    def standard_library(self):
        return self._main_block.standard_library

    @annotate_xml
    def to_xml(self):
        self.standardize_unit_dimensions()
        self.validate()
        return RandomDistributionXMLWriter().visit(self)

    @classmethod
    @read_annotations
    @handle_xml_exceptions
    def from_xml(cls, element, document):
        return RandomDistributionXMLLoader(
            document).load_randomdistributionclass(element)

from .visitors.cloner import RandomDistributionCloner
from .visitors.modifiers import(
    RandomDistributionRenameSymbol, RandomDistributionAssignIndices)
from .visitors.queriers import (RandomDistributionRequiredDefinitions,
                                RandomDistributionElementFinder,
                                RandomDistributionExpressionExtractor)
from .visitors.validators import RandomDistributionValidator
from .visitors.xml import (
    RandomDistributionXMLLoader, RandomDistributionXMLWriter)
