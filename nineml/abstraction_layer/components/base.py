"""
Each 9ML abstraction layer module will define its own ComponentClass class.

This module provides the base class for these.

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from operator import and_
# from nineml.utility import filter_discrete_types
# from .interface import Parameter
from nineml import NINEML


class BaseComponentClass(object):
    """Base class for ComponentClasses in different 9ML modules."""

    element_name = 'ComponentClass'

    def to_xml(self):
        exec('from nineml.abstraction_layer.{}.writers import XMLWriter'
             .format(self.writer_name))
        return XMLWriter().visit(self)  # @UndefinedVariable

    @classmethod
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

    def __init__(self, name, parameters=[]):
        self._name = name
        self._parameters = dict((p.name, p) for p in parameters)
#       FIXME TGC 11/11/14: I didn't think this was necessary any more but have
#                           kept it here just in case
#
#         # Turn any strings in the parameter list into Parameters:
#         if parameters is None:
#
#         else:
#             param_types = (basestring, Parameter)
#             param_td = filter_discrete_types(parameters, param_types)
#             params_from_strings =[Parameter(s) for s in param_td[basestring]]
#             self._parameters = param_td[Parameter] + params_from_strings

    @property
    def name(self):
        """Returns the name of the component"""
        return self._name

    @property
    def parameters(self):
        """Returns an iterator over the local |Parameter| objects"""
        return self._parameters.itervalues()

    def parameter(self, name):
        return self._parameters[name]

    def __eq__(self, other):
        return reduce(and_, [isinstance(other, self.__class__)] +
                            [getattr(self, name) == getattr(other, name)
                             for name in self.__class__.defining_attributes])
