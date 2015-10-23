
"""
Each 9ML abstraction layer module will define its own ComponentClass class.

This module provides the base class for these.

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from abc import ABCMeta
import sympy
from .. import BaseALObject
from nineml.base import ContainerObject
from nineml.utils import (
    filter_discrete_types, ensure_valid_identifier,
    normalise_parameter_as_list, assert_no_duplicates)
from ..expressions import Alias, Constant
from ...units import dimensionless, Dimension
from nineml import DocumentLevelObject


class Parameter(BaseALObject):

    """A class representing a state-variable in a ``ComponentClass``.

    This was originally a string, but if we intend to support units in the
    future, wrapping in into its own object may make the transition easier
    """

    element_name = 'Parameter'
    defining_attributes = ('_name', '_dimension')

    def __init__(self, name, dimension=None):
        """Parameter Constructor

        `name` -- The name of the parameter.
        """
        super(Parameter, self).__init__()
        name = name.strip()
        ensure_valid_identifier(name)

        self._name = name
        self._dimension = dimension if dimension is not None else dimensionless
        assert isinstance(self._dimension, Dimension), (
            "dimension must be None or a nineml.Dimension instance")
        self.constraints = []  # TODO: constraints can be added in the future.

    def __eq__(self, other):
        if not isinstance(other, Parameter):
            return False
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

    def _sympy_(self):
        return sympy.Symbol(self.name)


class ComponentClass(BaseALObject, DocumentLevelObject, ContainerObject):
    """Base class for ComponentClasses in different 9ML modules."""

    __metaclass__ = ABCMeta  # Abstract base class

    defining_attributes = ('_name', '_parameters', '_aliases', '_constants')
    class_to_member = {'Parameter': 'parameter', 'Alias': 'alias',
                       'Constant': 'constant'}

    def __init__(self, name, parameters=None, aliases=None, constants=None,
                 url=None):
        ensure_valid_identifier(name)
        self._name = name
        BaseALObject.__init__(self)
        DocumentLevelObject.__init__(self, url)
        ContainerObject.__init__(self)

        # Turn any strings in the parameter list into Parameters:
        if parameters is None:
            parameters = []
        else:
            param_types = (basestring, Parameter)
            param_td = filter_discrete_types(parameters, param_types)
            params_from_strings = [Parameter(s) for s in param_td[basestring]]
            parameters = param_td[Parameter] + params_from_strings
        self._parameters = dict((p.name, p) for p in parameters)

        aliases = normalise_parameter_as_list(aliases)
        constants = normalise_parameter_as_list(constants)

        # Load the aliases as objects or strings:
        alias_td = filter_discrete_types(aliases, (basestring, Alias))
        aliases_from_strs = [Alias.from_str(o) for o in alias_td[basestring]]
        aliases = alias_td[Alias] + aliases_from_strs

        assert_no_duplicates(a.lhs for a in aliases)

        self._aliases = dict((a.lhs, a) for a in aliases)
        self._constants = dict((c.name, c) for c in constants)

    @property
    def name(self):
        """Returns the name of the component"""
        return self._name

    @property
    def ports(self):
        return []

    def send_port(self, port_name):
        for dct_name in self.send_port_dicts:
            try:
                return getattr(self, dct_name)[port_name]
            except KeyError:
                pass
        raise KeyError("Could not find send port '{}' in '{}' class"
                       .format(port_name, self.name))

    def receive_port(self, port_name):
        for dct_name in self.receive_port_dicts:
            try:
                return getattr(self, dct_name)[port_name]
            except KeyError:
                pass
        raise KeyError("Could not find receive port '{}' in '{}' class"
                       .format(port_name, self.name))

    @property
    def num_parameters(self):
        return len(self._parameters)

    @property
    def num_aliases(self):
        return len(self._aliases)

    @property
    def num_constants(self):
        return len(self._constants)

    @property
    def parameters(self):
        """Returns an iterator over the local |Parameter| objects"""
        return self._parameters.itervalues()

    @property
    def aliases(self):
        return self._aliases.itervalues()

    @property
    def constants(self):
        return self._constants.itervalues()

    def parameter(self, name):
        return self._parameters[name]

    def alias(self, name):
        return self._aliases[name]

    def constant(self, name):
        return self._constants[name]

    @property
    def parameter_names(self):
        return self._parameters.iterkeys()

    @property
    def alias_names(self):
        return self._aliases.iterkeys()

    @property
    def constant_names(self):
        return self._constants.iterkeys()

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
