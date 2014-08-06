"""
Classes for defining spatial structures in 9ML

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.


Example:

grid2D = ComponentClass(
            name="square grid",
            parameters=['x0', 'y0', 'dx', 'dy', 'n'],
            structure=StructureGenerator(
                          aliases=['nx: math.floor(math.sqrt(n)) + 1',
                                   'ny: nx'],
                          coordinates=[
                                CoordinateGenerator(
                                        name='x',
                                        expression=Function(
                                            arg='i',
                                            value='x0 + math.floor(i/ny)'
                                        )),
                                CoordinateGenerator(
                                        name='y',
                                        expression=Function(
                                            arg='i',
                                            value='y0 + i%nx'
                                        ))]))
"""

# IMPORTANT NOTE - this is just a bunch of crazy ideas to kick about for now.

from nineml.abstraction_layer.components import BaseComponentClass


def Function(object):

    def __init__(self, name, value):
        self.name = name
        self.value = value


class StructureGenerator(object):
    """
    A representation of an algorithm for generating a list of positions in
    space given a list (or interval?) of indices.
    """

    def __init__(self, coordinates, aliases):
        self.coordinates = coordinates
        self.aliases = aliases


def CoordinateGenerator(object):
    """
    """

    def __init__(self, name, expression):
        self.name = name
        if isinstance(expression, Function):
            self.expression = expression
        else:
            self.expression = Function(i, expression)


class ComponentClass(BaseComponentClass):

    def __init__(self, name, parameters=None, structure=None):
        super(ComponentClass, self).__init__(name, parameters)
        self._structure = structure
