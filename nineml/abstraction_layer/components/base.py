"""
Each 9ML abstraction layer module will define its own ComponentClass class.

This module provides the base class for these.

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from nineml.utility import filter_discrete_types
from .interface import Parameter
from nineml import NINEML
import nineml.abstraction_layer.dynamics.readers
import nineml.abstraction_layer.connection_generator.readers
import nineml.abstraction_layer.random.readers


class BaseComponentClass(object):
    """Base class for ComponentClasses in different 9ML modules."""

    element_name = 'ComponentClass'

    def to_xml(self):
        raise NotImplementedError

    @classmethod
    def from_xml(cls, element):
        if element.find(NINEML + 'Dynamics'):
            loader = nineml.abstraction_layer.dynamics.readers.XMLLoader()
        elif element.find(NINEML + 'ConnectionRule'):
            loader = nineml.abstraction_layer.connection_generator.readers.\
                                                                    XMLLoader()
        elif element.find(NINEML + 'RandomDistribution'):
            loader = nineml.abstraction_layer.random.readers.XMLLoader()
        return loader.load_componentclass(element)

    def __init__(self, name, parameters=None):
        self._name = name

        # Turn any strings in the parameter list into Parameters:
        if parameters is None:
            self._parameters = []
        else:
            param_types = (basestring, Parameter)
            param_td = filter_discrete_types(parameters, param_types)
            params_from_strings = [Parameter(s) for s in param_td[basestring]]
            self._parameters = param_td[Parameter] + params_from_strings

    @property
    def name(self):
        """Returns the name of the component"""
        return self._name

    @property
    def parameters(self):
        """Returns an iterator over the local |Parameter| objects"""
        return iter(self._parameters)
