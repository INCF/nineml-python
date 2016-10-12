from ..componentclass import ComponentClass
from nineml.xml import E
from nineml.exceptions import NineMLRuntimeError


class RandomDistribution(ComponentClass):

    nineml_type = 'RandomDistribution'
    defining_attributes = ('_name', '_parameters')
    # Maintains order of elements between writes
    write_order = ('Parameter', 'Alias', 'Constant', 'Annotations')

    standard_library_basepath = 'http://www.uncertml.org/distributions/'
    _base_len = len(standard_library_basepath)
    standard_types = ('bernoulli', 'beta', 'binomial', 'cauchy', 'chi-square',
                      'dirichlet', 'exponential', 'f', 'gamma', 'geometric',
                      'hypergeometric', 'laplace', 'logistic', 'log-normal',
                      'multinomial', 'negative-binomial', 'normal',
                      'pareto', 'poisson', 'uniform', 'weibull')

    def __init__(self, name, standard_library, parameters=None,
                 document=None):
        super(RandomDistribution, self).__init__(
            name, parameters, document=document)
        if (not standard_library.startswith(self.standard_library_basepath) or
                standard_library[self._base_len:] not in self.standard_types):
            raise NineMLRuntimeError(
                "Unrecognised random distribution library path '{}'. "
                "Available options are '{}'".format(
                    standard_library,
                    "', '".join(self.standard_library_basepath + t
                                for t in self.standard_types)))
        self._standard_library = standard_library

# http://www.uncertml.org/distributions/normal

    @property
    def standard_library(self):
        return self._standard_library

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_componentclass(self, **kwargs)

    def rename_symbol(self, old_symbol, new_symbol):
        RandomDistributionRenameSymbol(self, old_symbol, new_symbol)

    def assign_indices(self):
        RandomDistributionAssignIndices(self)

    def required_for(self, expressions):
        return RandomDistributionRequiredDefinitions(self, expressions)

    def clone(self, memo=None, **kwargs):  # @UnusedVariable
        if memo is None:
            memo = {}
        try:
            clone = memo[id(self)]
        except KeyError:
            clone = RandomDistributionCloner().visit(self)
        return clone

    def dimension_of(self, element):
        try:
            resolver = self._dimension_resolver
        except AttributeError:
            resolver = RandomDistributionDimensionResolver(self)
            self._dimension_resolver = resolver
        return resolver.dimension_of(element)

    def _find_element(self, element):
        return RandomDistributionElementFinder(element).found_in(self)

    def validate(self, **kwargs):
        RandomDistributionValidator.validate_componentclass(self, **kwargs)

    @property
    def all_expressions(self):
        extractor = RandomDistributionExpressionExtractor()
        extractor.visit(self)
        return extractor.expressions

    def to_xml(self, document, E=E, **kwargs):  # @UnusedVariable
        self.standardize_unit_dimensions()
        self.validate()
        return RandomDistributionXMLWriter(document, E, **kwargs).visit(self)

    @classmethod
    def from_xml(cls, element, document, **kwargs):  # @UnusedVariable
        return RandomDistributionXMLLoader(
            document).load_randomdistributionclass(element)

from .visitors.modifiers import(  # @IgnorePep8
    RandomDistributionRenameSymbol, RandomDistributionAssignIndices)
from .visitors.queriers import (RandomDistributionRequiredDefinitions,  # @IgnorePep8
                                RandomDistributionElementFinder,
                                RandomDistributionExpressionExtractor,
                                RandomDistributionDimensionResolver)
from .visitors.validators import RandomDistributionValidator  # @IgnorePep8
from .visitors.cloner import RandomDistributionCloner  # @IgnorePep8
from .visitors.xml import (  # @IgnorePep8
    RandomDistributionXMLLoader, RandomDistributionXMLWriter)
