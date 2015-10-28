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
from ..componentclass import ComponentClass
from nineml.xml import E


class ConnectionRule(ComponentClass):

    element_name = 'ConnectionRule'
    defining_attributes = ('name', '_parameters', 'standard_library')
    # Maintains order of elements between writes
    write_order = ('Parameter', 'Alias', 'Constant', 'Annotations')

    def __init__(self, name, standard_library, parameters=None):
        super(ConnectionRule, self).__init__(
            name, parameters)
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

    def dimension_of(self, element):
        try:
            resolver = self._dimension_resolver
        except AttributeError:  # If dimension resolver hasn't been set
            resolver = ConnectionRuleDimensionResolver(self)
            self._dimension_resolver = resolver
        return resolver.dimension_of(element)

    def _find_element(self, element):
        return ConnectionRuleElementFinder(element).found_in(self)

    def validate(self):
        ConnectionRuleValidator.validate_componentclass(self)

    @property
    def all_expressions(self):
        extractor = ConnectionRuleExpressionExtractor()
        extractor.visit(self)
        return extractor.expressions

    def to_xml(self, document, E=E, **kwargs):  # @UnusedVariable
        self.standardize_unit_dimensions()
        self.validate()
        return ConnectionRuleXMLWriter(document, E).visit(self)

    @classmethod
    def from_xml(cls, element, document, **kwargs):  # @UnusedVariable
        return ConnectionRuleXMLLoader(document).load_connectionruleclass(
            element, **kwargs)


from .visitors.modifiers import (
    ConnectionRuleRenameSymbol, ConnectionRuleAssignIndices)
from .visitors.queriers import (
    ConnectionRuleRequiredDefinitions, ConnectionRuleElementFinder,
    ConnectionRuleExpressionExtractor, ConnectionRuleDimensionResolver)
from .visitors.validators import ConnectionRuleValidator
from .visitors.xml import (
    ConnectionRuleXMLLoader, ConnectionRuleXMLWriter)
