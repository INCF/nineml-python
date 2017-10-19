from ..componentclass import ComponentClass
from nineml.exceptions import NineMLUsageError, NineMLSerializationError
from .. import Parameter


class RandomDistribution(ComponentClass):

    nineml_type = 'RandomDistribution'
    nineml_attr = ComponentClass.nineml_attr + ('standard_library',)

    standard_library_basepath = 'http://www.uncertml.org/distributions/'
    _base_len = len(standard_library_basepath)
    standard_types = ('bernoulli', 'beta', 'binomial', 'cauchy', 'chi-square',
                      'dirichlet', 'exponential', 'f', 'gamma', 'geometric',
                      'hypergeometric', 'laplace', 'logistic', 'log-normal',
                      'multinomial', 'negative-binomial', 'normal',
                      'pareto', 'poisson', 'uniform', 'weibull')

    def __init__(self, name, standard_library, parameters=(),
                 validate=True, **kwargs):  # @UnusedVariable @IgnorePep8
        super(RandomDistribution, self).__init__(name, parameters)
        if (not standard_library.startswith(self.standard_library_basepath) or
                standard_library[self._base_len:] not in self.standard_types):
            raise NineMLUsageError(
                "Unrecognised random distribution library path '{}'. "
                "Available options are '{}'".format(
                    standard_library,
                    "', '".join(self.standard_library_basepath + t
                                for t in self.standard_types)))
        self._standard_library = str(standard_library)
        if validate:
            self.validate(**kwargs)

    @property
    def standard_library(self):
        return self._standard_library

    def rename_symbol(self, old_symbol, new_symbol):
        RandomDistributionRenameSymbol(self, old_symbol, new_symbol)

    def required_for(self, expressions):
        return RandomDistributionRequiredDefinitions(self, expressions)

    def dimension_of(self, element):
        if self._dimension_resolver is None:
            self._dimension_resolver = RandomDistributionDimensionResolver(
                self)
        return self._dimension_resolver.dimension_of(element)

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

from .visitors.modifiers import RandomDistributionRenameSymbol  # @IgnorePep8
from .visitors.queriers import (RandomDistributionRequiredDefinitions,  # @IgnorePep8
                                RandomDistributionExpressionExtractor,
                                RandomDistributionDimensionResolver)
from .visitors.validators import RandomDistributionValidator  # @IgnorePep8
