#!/usr/bin/env python
"""
docstring goes here

.. module:: connection_generator.py
   :platform: Unix, Windows
   :synopsis:

.. moduleauthor:: Mikael Djurfeldt <mikael.djurfeldt@incf.org>
.. moduleauthor:: Dragan Nikolic <dnikolic@incf.org>

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from ..componentclass import ComponentClass, Parameter
from nineml.exceptions import NineMLRuntimeError, NineMLSerializationError
import nineml.units as un


class ConnectionRule(ComponentClass):

    nineml_type = 'ConnectionRule'
    defining_attributes = ('_name', '_parameters', '_standard_library')

    standard_library_basepath = 'http://nineml.net/9ML/1.0/connectionrules/'
    _base_len = len(standard_library_basepath)
    standard_types = ('AllToAll', 'OneToOne', 'Explicit',
                      'Probabilistic', 'RandomFanIn',
                      'RandomFanOut')

    def __init__(self, name, standard_library, parameters=None):
        super(ConnectionRule, self).__init__(name, parameters)
        # Convert to lower case
        if (not standard_library.startswith(self.standard_library_basepath) or
                standard_library[self._base_len:] not in self.standard_types):
            raise NineMLRuntimeError(
                "Unrecognised connection rule library path '{}'. "
                "Available options are '{}'".format(
                    standard_library,
                    "', '".join(self.standard_library_basepath + t
                                for t in self.standard_types)))
        self._standard_library = standard_library

    @property
    def standard_library(self):
        return self._standard_library

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_componentclass(self, **kwargs)

    def rename_symbol(self, old_symbol, new_symbol):
        ConnectionRuleRenameSymbol(self, old_symbol, new_symbol)

    def assign_indices(self):
        ConnectionRuleAssignIndices(self)

    def required_for(self, expressions):
        return ConnectionRuleRequiredDefinitions(self, expressions)

    def clone(self, memo=None, **kwargs):  # @UnusedVariable
        return ConnectionRuleCloner(memo=memo).visit(self, **kwargs)

    def dimension_of(self, element):
        try:
            resolver = self._dimension_resolver
        except AttributeError:  # If dimension resolver hasn't been set
            resolver = ConnectionRuleDimensionResolver(self)
            self._dimension_resolver = resolver
        return resolver.dimension_of(element)

    def find_element(self, element):
        return ConnectionRuleElementFinder(element).found_in(self)

    def validate(self, **kwargs):
        ConnectionRuleValidator.validate_componentclass(self, **kwargs)

    @property
    def all_expressions(self):
        extractor = ConnectionRuleExpressionExtractor()
        extractor.visit(self)
        return extractor.expressions

    # connection_rule
    def serialize_node(self, node, **options):  # @UnusedVariable @IgnorePep8
        node.attr('name', self.name, **options)
        node.children(self.parameters, **options)
        node.attr('standard_library', self.standard_library, **options)

    @classmethod
    def unserialize_node(cls, node, **options):  # @UnusedVariable
        standard_library = node.attr('standard_library', **options)
        return cls(
            name=node.attr('name', **options),
            standard_library=standard_library,
            parameters=node.children(Parameter, **options))

    # connection_rule
    def serialize_node_v1(self, node, **options):  # @UnusedVariable @IgnorePep8
        node.attr('name', self.name, **options)
        node.children(self.parameters, **options)
        cr_elem = node.visitor.create_elem(
            'ConnectionRule', parent=node.serial_element, **options)
        node.visitor.set_attr(cr_elem, 'standard_library',
                              self.standard_library, **options)

    @classmethod
    def unserialize_node_v1(cls, node, **options):  # @UnusedVariable
        cr_elem = node.visitor.get_child(node.serial_element, 'ConnectionRule',
                                         **options)
        node.unprocessed_children.remove('ConnectionRule')
        if list(node.visitor.get_all_children(cr_elem)):
            raise NineMLSerializationError(
                "Not expecting {} blocks within 'ConnectionRule' block"
                .format(', '.join(node.visitor.get_children(cr_elem))))
        standard_library = node.visitor.get_attr(
            cr_elem, 'standard_library', **options)
        return cls(
            name=node.attr('name', **options),
            standard_library=standard_library,
            parameters=node.children(Parameter, **options))

    @property
    def lib_type(self):
        return self.standard_library[self._base_len:]

    def is_random(self):
        return self.lib_type in ('Probabilistic', 'RandomFanIn',
                                 'RandomFanOut')


from .visitors.modifiers import (  # @IgnorePep8
    ConnectionRuleRenameSymbol, ConnectionRuleAssignIndices)
from .visitors.queriers import (  # @IgnorePep8
    ConnectionRuleRequiredDefinitions, ConnectionRuleElementFinder,
    ConnectionRuleExpressionExtractor, ConnectionRuleDimensionResolver)
from .visitors.validators import ConnectionRuleValidator  # @IgnorePep8
from .visitors.cloner import ConnectionRuleCloner  # @IgnorePep8


one_to_one_connection_rule = ConnectionRule(
    name='one_to_one',
    standard_library=(ConnectionRule.standard_library_basepath + 'OneToOne'))

all_to_all_connection_rule = ConnectionRule(
    name='all_to_all',
    standard_library=(ConnectionRule.standard_library_basepath + 'AllToAll'))

explicit_connection_rule = ConnectionRule(
    name='explicit',
    standard_library=(ConnectionRule.standard_library_basepath + 'Explicit'),
    parameters=[
        Parameter(dimension=un.dimensionless,
                  name="destinationIndices"),
        Parameter(dimension=un.dimensionless,
                  name="sourceIndices")])

probabilistic_connection_rule = ConnectionRule(
    name='probabilistic',
    standard_library=(ConnectionRule.standard_library_basepath +
                      'Probabilistic'),
    parameters=[Parameter(dimension=un.dimensionless,
                          name='probability')])

random_fan_in_connection_rule = ConnectionRule(
    name='random_fan_in',
    standard_library=(ConnectionRule.standard_library_basepath +
                      'RandomFanIn'),
    parameters=[Parameter(dimension=un.dimensionless,
                          name='number')])

random_fan_out_connection_rule = ConnectionRule(
    name='random_fan_out',
    standard_library=(ConnectionRule.standard_library_basepath +
                      'RandomFanOut'),
    parameters=[Parameter(dimension=un.dimensionless,
                          name='number')])
