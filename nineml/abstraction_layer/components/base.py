"""
Each 9ML abstraction layer module will define its own ComponentClass class.

This module provides the base class for these.

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from ..base import BaseALObject
from ...base import read_annotations, annotate_xml, NINEML
from .interface import Parameter
from ...utility import filter_discrete_types


class BaseComponentClass(BaseALObject):
    """Base class for ComponentClasses in different 9ML modules."""

    element_name = 'ComponentClass'

    @annotate_xml
    def to_xml(self):
        exec('from nineml.abstraction_layer.{}.writers import XMLWriter'
             .format(self.writer_name))
        return XMLWriter().visit(self)  # @UndefinedVariable

    @classmethod
    @read_annotations
    def from_xml(cls, element, context):  # @UnusedVariable
        if element.find(NINEML + 'Dynamics') is not None:
            module_name = 'dynamics'
        elif element.find(NINEML + 'ConnectionRule') is not None:
            module_name = 'connectionrule'
        elif element.find(NINEML + 'RandomDistribution') is not None:
            module_name = 'random'
        exec('from nineml.abstraction_layer.{}.readers import XMLLoader'
             .format(module_name))
        return XMLLoader(context).load_componentclass(element)  # @UndefinedVariable @IgnorePep8

    def __init__(self, name, parameters=None):
        BaseALObject.__init__(self)
        self._name = name
        # Turn any strings in the parameter list into Parameters:
        if parameters is None:
            parameters = []
        else:
            param_types = (basestring, Parameter)
            param_td = filter_discrete_types(parameters, param_types)
            params_from_strings = [Parameter(s) for s in param_td[basestring]]
            parameters = param_td[Parameter] + params_from_strings
        self._parameters = dict((p.name, p) for p in parameters)

    @property
    def name(self):
        """Returns the name of the component"""
        return self._name

    @property
    def parameters(self):
        """Returns an iterator over the local |Parameter| objects"""
        return self._parameters.itervalues()

    @property
    def parameter_names(self):
        return self._parameters.iterkeys()

    def parameter(self, name):
        return self._parameters[name]
