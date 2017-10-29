
"""
Each 9ML abstraction layer module will define its own ComponentClass class.

This module provides the base class for these.

:copyright: Copyright 2010-2017 by the NineML Python team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from builtins import next
from past.builtins import basestring
from abc import ABCMeta
from .. import BaseALObject
from nineml.base import ContainerObject
from nineml.utils.iterables import (
    filter_discrete_types,
    normalise_parameter_as_list)
from nineml.utils import validate_identifier
from ..expressions import Alias, Constant
from nineml.base import DocumentLevelObject
from nineml.exceptions import name_error
from ..base import Parameter  # @IgnorePep8
from future.utils import with_metaclass


class ComponentClass(with_metaclass(
        ABCMeta, type('NewBase', (BaseALObject, DocumentLevelObject,
                                  ContainerObject), {}))):
    """Base class for ComponentClasses in different 9ML modules."""
    nineml_type_v1 = 'ComponentClass'
    nineml_attr = ('name',)
    nineml_children = (Parameter, Alias, Constant)

    def __init__(self, name, parameters=(), aliases=(), constants=()):
        self._name = validate_identifier(name)
        BaseALObject.__init__(self)
        DocumentLevelObject.__init__(self)
        ContainerObject.__init__(self)

        # Caches the dimension resolver so that it can be reused in subsequent
        # calls
        self._dimension_resolver = None

        # Turn any strings in the parameter list into Parameters:
        param_types = (basestring, Parameter)
        param_td = filter_discrete_types(parameters, param_types)
        params_from_strings = [Parameter(s) for s in param_td[basestring]]
        parameters = param_td[Parameter] + params_from_strings

        # Load the aliases as objects or strings:
        aliases = normalise_parameter_as_list(aliases)
        alias_td = filter_discrete_types(aliases, (basestring, Alias))
        aliases_from_strs = [Alias.from_str(o) for o in alias_td[basestring]]
        aliases = alias_td[Alias] + aliases_from_strs

        constants = normalise_parameter_as_list(constants)

        self.add(*parameters)
        self.add(*aliases)
        self.add(*constants)

    @property
    def name(self):
        """Returns the name of the component"""
        return self._name

    @name.setter
    def name(self, name):
        self._name = validate_identifier(name)

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
        return iter(self._parameters.values())

    @property
    def aliases(self):
        return iter(self._aliases.values())

    @property
    def constants(self):
        return iter(self._constants.values())

    @name_error
    def parameter(self, name):
        return self._parameters[name]

    @name_error
    def alias(self, name):
        return self._aliases[name]

    @name_error
    def constant(self, name):
        return self._constants[name]

    @property
    def parameter_names(self):
        return iter(self._parameters.keys())

    @property
    def alias_names(self):
        return iter(self._aliases.keys())

    @property
    def constant_names(self):
        return iter(self._constants.keys())

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
