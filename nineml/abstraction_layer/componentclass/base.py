
"""
Each 9ML abstraction layer module will define its own ComponentClass class.

This module provides the base class for these.

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from itertools import chain
from abc import ABCMeta
from collections import namedtuple, defaultdict
from .. import BaseALObject
import nineml
from nineml.annotations import read_annotations, annotate_xml
from nineml.utils import filter_discrete_types, ensure_valid_identifier
from ..expressions.utils import get_reserved_and_builtin_symbols
from ..units import dimensionless, Dimension
from nineml import TopLevelObject
from ..expressions import ExpressionSymbol


Dependencies = namedtuple('Dependencies',
                          ('parameters', 'ports', 'constants',
                           'randomvariables', 'expressions'))


class ComponentClass(BaseALObject, TopLevelObject):
    """Base class for ComponentClasses in different 9ML modules."""

    __metaclass__ = ABCMeta  # Abstract base class

    element_name = 'ComponentClass'

    def __init__(self, name, parameters, main_block):
        ensure_valid_identifier(name)
        BaseALObject.__init__(self)
        self._name = name
        self._main_block = main_block
        # Turn any strings in the parameter list into Parameters:
        if parameters is None:
            parameters = []
        else:
            param_types = (basestring, Parameter)
            param_td = filter_discrete_types(parameters, param_types)
            params_from_strings = [Parameter(s) for s in param_td[basestring]]
            parameters = param_td[Parameter] + params_from_strings
        self._parameters = dict((p.name, p) for p in parameters)
        self._indices = {}

    @property
    def name(self):
        """Returns the name of the component"""
        return self._name

    @property
    def ports(self):
        return []

    def index_of(self, element, key=None):
        """
        Returns the index of an element amongst others of its type. The indices
        are generated on demand but then remembered to allow them to be
        referred to again.

        This function is meant to be useful during code-generation, where an
        name of an element can be replaced with a unique integer value (and
        referenced elsewhere in the code).

        WARNING! It is assumed but not checked that the element is part of the
        component class.
        """
        if key is None:
            try:
                key = element.__class__.index_key
            except AttributeError:
                key = element.__class__.__name__
        if key not in self._indices:
            # Create a new defaultdict to generate new indices for the given
            # type.
            self._indices[key] = defaultdict(lambda: len(self._indices[key]))
        return self._indices[key][element]

    @property
    def parameters(self):
        """Returns an iterator over the local |Parameter| objects"""
        return self._parameters.itervalues()

    @property
    def parameters_map(self):
        """Returns the underlying parameters dictionary containing the local
          |Parameter| objects"""
        return self._parameters

    @property
    def parameter_names(self):
        return self._parameters.iterkeys()

    def parameter(self, name):
        return self._parameters[name]

    @property
    def aliases(self):
        return self._main_block.aliases

    @property
    def aliases_map(self):
        return self._main_block.aliases_map

    @property
    def constants(self):
        return self._main_block.constants

    @property
    def constants_map(self):
        return self._main_block.constants_map

    @property
    def dimensions(self):
        return set(a.dimension for a in self.attributes_with_dimension)

    @property
    def attributes_with_dimension(self):
        return self.parameters

    @property
    def attributes_with_units(self):
        return self.constants

    def standardize_unit_dimensions(self, reference_set=None):
        """
        Replaces dimension objects with ones from a reference set so that their
        names do not conflict when writing to file
        """
        if reference_set is None:
            reference_set = self.dimensions
        for a in self.attributes_with_dimension:
            try:
                std_dim = next(d for d in reference_set if d == a.dimension)
            except StopIteration:
                continue
            a.set_dimension(std_dim)

    @annotate_xml
    def to_xml(self):
        self.standardize_unit_dimensions()
        XMLWriter = getattr(nineml.abstraction_layer,
                            self.__class__.__name__ + 'XMLWriter')
        return XMLWriter().visit(self)

    @classmethod
    @read_annotations
    def from_xml(cls, element, document):  # @UnusedVariable
        XMLLoader = getattr(nineml.abstraction_layer,
                            ComponentClassXMLLoader.read_class_type(element) +
                            'ClassXMLLoader')
        return XMLLoader(document).load_componentclass(element)

    def get_dependencies(self, expression):
        """
        Gets lists of required parameters, states, ports, random variables,
        constants and expressions (in resolved order of execution).
        """
        # Expression can either be a single expression or an iterable of
        # expressions
        try:
            required_atoms = set(expression.rhs_atoms)
        except AttributeError:
            try:
                required_atoms = set(chain(*(e.rhs_atoms for e in expression)))
            except TypeError:
                raise TypeError(
                    "Unrecognised expression type {}".format(type(expression)))
        # Strip builtin symbols from required atoms
        required_atoms.difference_update(get_reserved_and_builtin_symbols())
        # Strip symbols which are assumed predefined for the current
        # componentclass type (i.e. state variables in DynamicsClass')
        required_atoms.difference_update(self._assumed_defined)
        # Initialise dependency container
        dp = Dependencies(parameters=set(), ports=set(), constants=set(),
                          randomvariables=set(), expressions=list())
        # Add corresponding param, port, constant, random variable or
        # expression for each atom and atom dependencies
        for atom in required_atoms:
            if atom in self.parameters_map:
                dp.parameters.add(self.parameters_map[atom])
            elif atom in self.analog_receive_ports_map:
                dp.ports.add(self.analog_receive_ports_map[atom])
            elif atom in self.analog_reduce_ports_map:
                dp.ports.add(self.analog_reduce_ports_map[atom])
            elif atom in self.constants_map:
                dp.constants.add(self.constants_map[atom])
            elif atom in self.randomvariables_map:
                dp.randomvariables.add(self.randomvariables_map[atom])
            else:
                try:
                    expr = self.aliases_map[atom]
                except KeyError:
                    expr = self.piecewises_map[atom]
                expr_dp = self.get_dependencies(expr)
                dp.parameters.update(expr_dp.parameters)
                dp.ports.update(expr_dp.ports)
                dp.constants.update(expr_dp.constants)
                dp.randomvariables.update(expr_dp.randomvariables)
                # Add expression dependencies in order of execution
                dp.expressions.extend(e for e in expr_dp.expressions
                                      if e not in dp.expressions)
                dp.expressions.append(expr)
        return dp

    @property
    def _assumed_defined(self):
        return []


class Parameter(BaseALObject, ExpressionSymbol):

    """A class representing a state-variable in a ``ComponentClass``.

    This was originally a string, but if we intend to support units in the
    future, wrapping in into its own object may make the transition easier
    """

    element_name = 'Parameter'
    defining_attributes = ('name', 'dimension')

    def __init__(self, name, dimension=None):
        """Parameter Constructor

        `name` -- The name of the parameter.
        """
        name = name.strip()
        ensure_valid_identifier(name)

        self._name = name
        self._dimension = dimension if dimension is not None else dimensionless
        assert isinstance(self._dimension, Dimension), (
            "dimension must be None or a nineml.Dimension instance")
        self.constraints = []  # TODO: constraints can be added in the future.

    def __eq__(self, other):
        return self.name == other.name and self.dimension == other.dimension

    @property
    def name(self):
        """Returns the name of the parameter"""
        return self._name

    @property
    def dimension(self):
        """Returns the dimensions of the parameter"""
        return self._dimension

    def set_dimension(self, dimension):
        self._dimension = dimension

    def __repr__(self):
        return ("Parameter({}{})"
                .format(self.name,
                        ', dimension={}'.format(self.dimension.name)))

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_parameter(self, **kwargs)


from .utils.xml import ComponentClassXMLLoader
