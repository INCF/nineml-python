"""
Each 9ML abstraction layer module will define its own ComponentClass class.

This module provides the base class for these.

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
import inspect
from nineml.utility import filter_discrete_types
from .interface import Parameter
from nineml import NINEML


class BaseComponentClass(object):
    """Base class for ComponentClasses in different 9ML modules."""

    element_name = 'ComponentClass'

    #FIXME: Not sure if this works for dynamics class but definitely won't
    #       for other classes.
    def to_xml(self):
        return inspect.getmodule(self.__class__).writers.XMLWriter().\
                                                                    visit(self)

    @classmethod
    def from_xml(cls, element, context):  # @UnusedVariable
        if element.find(NINEML + 'Dynamics'):
            module_name = 'dynamics'
        elif element.find(NINEML + 'ConnectionRule'):
            module_name = 'connection_generator'
        elif element.find(NINEML + 'RandomDistribution'):
            module_name = 'random'
        exec('from nineml.abstraction_layer.{}.readers import XMLLoader'
             .format(module_name))
        return XMLLoader().load_componentclass(element)  # @UndefinedVariable

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
