"""
Contains the classes for defining the interface for a componentclass

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""


from nineml.utility import ensure_valid_c_variable_name


class Parameter(object):

    """A class representing a state-variable in a ``ComponentClass``.

    This was originally a string, but if we intend to support units in the
    future, wrapping in into its own object may make the transition easier
    """

    def __init__(self, name, dimension=""):
        """Parameter Constructor

        :param name:  The name of the parameter.
        """
        name = name.strip()
        ensure_valid_c_variable_name(name)

        self._name = name
        self._dimension = dimension

    @property
    def name(self):
        """Returns the name of the parameter"""
        return self._name

    @property
    def dimension(self):
        """Returns the dimensions of the parameter"""
        return self._dimension

    def __repr__(self):
        return "<Parameter: %r (%r)>" % (self.name, self.dimension)

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_parameter(self, **kwargs)
