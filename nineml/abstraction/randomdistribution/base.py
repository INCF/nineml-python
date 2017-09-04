from ..componentclass import ComponentClass
from nineml.exceptions import NineMLRuntimeError, NineMLSerializationError
from .. import Parameter


class RandomDistribution(ComponentClass):

    nineml_type = 'RandomDistribution'
    defining_attributes = ('_name', '_parameters', '_standard_library',
                           '_aliases', '_constants')
    nineml_attr = ComponentClass.nineml_attr + ('standard_library',)

    standard_library_basepath = 'http://www.uncertml.org/distributions/'
    _base_len = len(standard_library_basepath)
    standard_types = ('bernoulli', 'beta', 'binomial', 'cauchy', 'chi-square',
                      'dirichlet', 'exponential', 'f', 'gamma', 'geometric',
                      'hypergeometric', 'laplace', 'logistic', 'log-normal',
                      'multinomial', 'negative-binomial', 'normal',
                      'pareto', 'poisson', 'uniform', 'weibull')

    def __init__(self, name, standard_library, parameters=None, **kwargs):  # @UnusedVariable @IgnorePep8
        super(RandomDistribution, self).__init__(name, parameters)
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

    def flatten(self):
        return RandomDistributionFlattener(self).flattened

    def dimension_of(self, element):
        try:
            resolver = self._dimension_resolver
        except AttributeError:
            resolver = RandomDistributionDimensionResolver(self)
            self._dimension_resolver = resolver
        return resolver.dimension_of(element)

    def find_element(self, element):
        return RandomDistributionElementFinder(element).found_in(self)

    def validate(self, **kwargs):
        RandomDistributionValidator.validate_componentclass(self, **kwargs)

    @property
    def all_expressions(self):
        extractor = RandomDistributionExpressionExtractor()
        extractor.visit(self)
        return extractor.expressions

    def serialize_node(self, node, **options):  # @UnusedVariable @IgnorePep8
        node.attr('name', self.name, **options)
        node.children(self.parameters, **options)
        node.attr('standard_library', self.standard_library, **options)

    @classmethod
    def unserialize_node(cls, node, **options):
        return cls(
            name=node.attr('name', **options),
            standard_library=node.attr('standard_library', **options),
            parameters=node.children(Parameter, **options))

    def serialize_node_v1(self, node, **options):  # @UnusedVariable @IgnorePep8
        node.attr('name', self.name, **options)
        node.children(self.parameters, **options)
        cr_elem = node.visitor.create_elem(
            'RandomDistribution', parent=node.serial_element, **options)
        node.visitor.set_attr(cr_elem, 'standard_library',
                              self.standard_library, **options)

    @classmethod
    def unserialize_node_v1(cls, node, **options):
        rd_elem = node.visitor.get_child(
            node.serial_element, 'RandomDistribution', **options)
        node.unprocessed_children.remove('RandomDistribution')
        if list(node.visitor.get_all_children(rd_elem)):
            raise NineMLSerializationError(
                "Not expecting {} blocks within 'RandomDistribution' block"
                .format(', '.join(node.visitor.get_children(rd_elem))))
        standard_library = node.visitor.get_attr(
            rd_elem, 'standard_library', **options)
        return cls(
            name=node.attr('name', **options),
            standard_library=standard_library,
            parameters=node.children(Parameter, **options))

from .visitors.modifiers import(  # @IgnorePep8
    RandomDistributionRenameSymbol, RandomDistributionAssignIndices)
from .visitors.queriers import (RandomDistributionRequiredDefinitions,  # @IgnorePep8
                                RandomDistributionElementFinder,
                                RandomDistributionExpressionExtractor,
                                RandomDistributionDimensionResolver)
from .visitors.validators import RandomDistributionValidator  # @IgnorePep8
from .visitors.modifiers import RandomDistributionFlattener  # @IgnorePep8
