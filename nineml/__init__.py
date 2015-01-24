"""
A Python library for working with 9ML model descriptions.

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

__version__ = "0.2dev"

from itertools import chain
from operator import and_


class BaseNineMLObject(object):

    """
    Base class for user layer classes
    """
    children = []

    def __init__(self):
        self.annotations = None

    def __eq__(self, other):
        return reduce(and_, [isinstance(other, self.__class__)] +
                            [getattr(self, name) == getattr(other, name)
                             for name in self.__class__.defining_attributes])

    def __ne__(self, other):
        return not self == other

    def get_children(self):
        return chain(getattr(self, attr) for attr in self.children)

    def accept_visitor(self, visitor):
        visitor.visit(self)


class TopLevelObject(object):

    @property
    def _attributes_with_dimension(self):
        return []  # To be overridden in derived classes

    @property
    def _attributes_with_units(self):
        return []  # To be overridden in derived classes

    @property
    def all_units(self):
        return [a.units for a in self._attributes_with_units]

    @property
    def all_dimensions(self):
        return [a.dimension for a in self._attributes_with_dimension]

    def standardize_units(self, reference_units=None,
                          reference_dimensions=None):
        """Standardized the units used to avoid naming conflicts writing to
        """
        if reference_units is None:
            reference_units = self.all_units
        if reference_dimensions is None:
            reference_dimensions = set(u.dimension for u in reference_units)
        else:
            # Ensure that the units reference the same set of dimensions
            for u in reference_units:
                if u.dimension not in reference_dimensions:
                    u.set_dimension(next(d for d in reference_units
                                         if d == u.dimension))
        for a in self._attributes_with_dimension:
            try:
                std_unit = next(u for u in reference_units if u == a.units)
            except StopIteration:
                continue
            a.set_units(std_unit)

    def write(self, fname):
        write(self, fname)  # Calls nineml.document.Document.write


import abstraction_layer
import user_layer
import exceptions
from abstraction_layer import Unit, Dimension
from document import read, write, load, Document
