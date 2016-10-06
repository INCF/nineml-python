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
from itertools import chain
import math
from abc import ABCMeta, abstractmethod
from copy import copy
from itertools import izip, repeat, tee
import random
from ..componentclass import ComponentClass, Parameter
from nineml.xml import E
from nineml.exceptions import NineMLRuntimeError
import nineml.units as un


class ConnectionRule(ComponentClass):

    nineml_type = 'ConnectionRule'
    defining_attributes = ('name', '_parameters', 'standard_library')
    # Maintains order of elements between writes
    write_order = ('Parameter', 'Alias', 'Constant', 'Annotations')

    standard_library_basepath = 'http://nineml.net/9ML/1.0/connectionrules/'
    _base_len = len(standard_library_basepath)
    standard_types = ('AllToAll', 'OneToOne', 'Explicit',
                      'Probabilistic', 'RandomFanIn',
                      'RandomFanOut')

    def __init__(self, name, standard_library, parameters=None,
                 document=None):
        super(ConnectionRule, self).__init__(
            name, parameters, document=document)
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

    def clone(self):
        return ConnectionRuleCloner().visit(self)

    def dimension_of(self, element):
        try:
            resolver = self._dimension_resolver
        except AttributeError:  # If dimension resolver hasn't been set
            resolver = ConnectionRuleDimensionResolver(self)
            self._dimension_resolver = resolver
        return resolver.dimension_of(element)

    def _find_element(self, element):
        return ConnectionRuleElementFinder(element).found_in(self)

    def validate(self, **kwargs):
        ConnectionRuleValidator.validate_componentclass(self, **kwargs)

    @property
    def all_expressions(self):
        extractor = ConnectionRuleExpressionExtractor()
        extractor.visit(self)
        return extractor.expressions

    def to_xml(self, document, E=E, **kwargs):  # @UnusedVariable
        self.standardize_unit_dimensions()
        self.validate()
        return ConnectionRuleXMLWriter(document, E, **kwargs).visit(self)

    @classmethod
    def from_xml(cls, element, document, **kwargs):  # @UnusedVariable
        return ConnectionRuleXMLLoader(document).load_connectionruleclass(
            element, **kwargs)

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
from .visitors.xml import (  # @IgnorePep8
    ConnectionRuleXMLLoader, ConnectionRuleXMLWriter)


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

probabilistic_rule = ConnectionRule(
    name='probabilistic',
    standard_library=(ConnectionRule.standard_library_basepath +
                      'Probabilistic'),
    parameters=[Parameter(dimension=un.dimensionless,
                          name='probability')])

random_fan_in_rule = ConnectionRule(
    name='random_fan_in',
    standard_library=(ConnectionRule.standard_library_basepath +
                      'RandomFanIn'),
    parameters=[Parameter(dimension=un.dimensionless,
                          name='number')])

random_fan_out_rule = ConnectionRule(
    name='random_fan_out',
    standard_library=(ConnectionRule.standard_library_basepath +
                      'RandomFanOut'),
    parameters=[Parameter(dimension=un.dimensionless,
                          name='number')])


class BaseConnectivity(object):

    __metaclass__ = ABCMeta

    def __init__(self, connection_rule_properties, source_size,
                 destination_size,
                 **kwargs):  # @UnusedVariable
        if (connection_rule_properties.lib_type == 'OneToOne' and
                source_size != destination_size):
            raise NineMLRuntimeError(
                "Cannot connect to populations of different sizes "
                "({} and {}) with OneToOne connection rule"
                .format(source_size, destination_size))
        self._rule_props = connection_rule_properties
        self._src_size = source_size
        self._dest_size = destination_size
        self._cache = None
        self._kwargs = kwargs

    def __eq__(self, other):
        try:
            result = (self._rule_props == other._rule_props and
                      self._src_size == other._src_size and
                      self._dest_size == other._dest_size)
            return result
        except AttributeError:
            return False

    @property
    def rule_properties(self):
        return self._rule_props

    @property
    def rule(self):
        return self.rule_properties.component_class

    @property
    def lib_type(self):
        return self.rule_properties.lib_type

    @property
    def source_size(self):
        return self._src_size

    @property
    def destination_size(self):
        return self._dest_size

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        return ("{}(rule={}, src_size={}, dest_size={})"
                .format(self.__class__.__name__, self.lib_type,
                        self.source_size, self.destination_size))

    @abstractmethod
    def connections(self):
        pass

    @abstractmethod
    def has_been_sampled(self):
        pass


class InverseConnectivity(object):
    """
    Inverts the connectivity so that the source and destination are effectively
    flipped. Used when mapping a projection connectivity to a reverse
    connection to from the synapse or post-synaptic cell to the pre-synaptic
    cell
    """

    def __init__(self, connectivity):  # @UnusedVariable
        self._connectivity = connectivity

    def __eq__(self, other):
        return self._connectivity == other._connectivity

    @property
    def rule_properties(self):
        return self._connectivity._rule_props

    @property
    def rule(self):
        return self.rule_properties.component_class

    @property
    def lib_type(self):
        return self.rule_properties.lib_type

    @property
    def source_size(self):
        return self._connectivity.destination_size

    @property
    def destination_size(self):
        return self._connectivity.source_size

    def __repr__(self):
        return ("{}(rule={}, src_size={}, dest_size={})"
                .format(self.__class__.__name__, self.lib_type,
                        self.source_size, self.destination_size))

    @abstractmethod
    def connections(self):
        return ((j, i) for i, j in self._connectivity.connections)

    @abstractmethod
    def has_been_sampled(self):
        return self._connectivity.has_been_sampled


class Connectivity(BaseConnectivity):
    """
    A reference implementation of the Connectivity class, it is not recommended
    for large networks as it is not designed for efficiency (although perhaps
    with JIT it would be okay, see PyPy). More efficient implementations, which
    use external libraries such as NumPy can be supplied to the Projection as a
    kwarg.
    """

    def connections(self, **kwargs):
        """
        Returns an iterator over all the source/destination index pairings
        with a connection.
        `src`  -- the indices to get the connections from
        `dest` -- the indices to get the connections to
        """
        if self._kwargs:
            kw = kwargs
            kwargs = copy(self._kwargs)
            kwargs.update(kw)
        if self.lib_type == 'AllToAll':
            conn = self._all_to_all(**kwargs)
        elif self.lib_type == 'OneToOne':
            conn = self._one_to_one(**kwargs)
        elif self.lib_type == 'Explicit':
            conn = self._explicit_connection_list(**kwargs)
        elif self.lib_type == 'Probabilistic':
            conn = self._probabilistic_connectivity(**kwargs)
        elif self.lib_type == 'RandomFanIn':
            conn = self._random_fan_in(**kwargs)
        elif self.lib_type == 'RandomFanOut':
            conn = self._random_fan_out(**kwargs)
        else:
            assert False
        return conn

    def _all_to_all(self, **kwargs):  # @UnusedVariable
        return chain(*(((s, d) for d in xrange(self._dest_size))
                       for s in xrange(self._src_size)))

    def _one_to_one(self, **kwargs):  # @UnusedVariable
        return ((i, i) for i in xrange(self._src_size))

    def _explicit_connection_list(self, **kwargs):  # @UnusedVariable
        return izip(self._rule_props.property('source_indices').values,
                    self._rule_props.property('destination_indices').values)

    def _probabilistic_connectivity(self, **kwargs):  # @UnusedVariable
        if self._cache:
            conn = iter(self._cache)
        else:
            p = self._rule_props.property('probability').value
            # Get an iterator over all of the source dest pairs to test
            conn = chain(*(((s, d) for d in xrange(self._dest_size)
                            if random.random() < p)
                           for s in xrange(self._src_size)))
            conn, cpy = tee(conn)
            self._cache = list(cpy)
        return conn

    def _random_fan_in(self, **kwargs):  # @UnusedVariable
        if self._cache:
            conn = iter(self._cache)
        else:
            N = int(self._rule_props.property('number').value)
            conn = chain(*(
                izip((int(math.floor(random.random() * self._src_size))
                      for _ in xrange(N)),
                     repeat(d))
                for d in xrange(self._dest_size)))
            conn, cpy = tee(conn)
            self._cache = list(cpy)
        return conn

    def _random_fan_out(self, **kwargs):  # @UnusedVariable
        if self._cache:
            conn = iter(self._cache)
        else:
            N = int(self._rule_props.property('number').value)
            conn = chain(*(
                izip(repeat(s),
                     (int(math.floor(random.random() * self._dest_size))
                      for _ in xrange(N)))
                for s in xrange(self._src_size)))
            conn, cpy = tee(conn)
            self._cache = list(cpy)
        return conn

    def has_been_sampled(self):
        """
        Check to see whether randomly drawn values in the Connectivity object
        have been sampled (and cached) or not. Caching of random values allows
        multiple connection groups to reference the same instance of the
        connectivity (for example if they form part of one logical projection)
        """
        return (self.lib_type not in ('AllToAll', 'OneToOne',
                                      'ExplicitConnectionList') and
                self._cache is not None)
