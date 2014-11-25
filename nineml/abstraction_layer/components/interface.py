"""
Contains the classes for defining the interface for a componentclass

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""


from nineml.utility import ensure_valid_c_variable_name
from ..base import BaseALObject
from ..units import dimensionless


class Parameter(BaseALObject):

    """A class representing a state-variable in a ``ComponentClass``.

    This was originally a string, but if we intend to support units in the
    future, wrapping in into its own object may make the transition easier
    """

    defining_attributes = ('name', 'dimension')

    def __init__(self, name, dimension=None):
        """Parameter Constructor

        :param name:  The name of the parameter.
        """
        name = name.strip()
        ensure_valid_c_variable_name(name)

        self._name = name
        self._dimension = dimension if dimension is not None else dimensionless

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

    def __repr__(self):
        return ("Parameter({}{})"
                .format(self.name,
                        ', dimension={}'.format(self.dimension.name)
                        if self.dimension else ''))

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_parameter(self, **kwargs)
