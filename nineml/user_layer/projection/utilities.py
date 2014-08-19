"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

# from nineml.user_layer.connection_generator import ConnectionGenerator, cgClosureFromURI
from nineml.user_layer.cg_closure import alConnectionRuleFromURI
from nineml.user_layer.explicit_list_of_connections import ExplicitListOfConnections  # @IgnorePep8
from nineml.user_layer.grids import createUnstructuredGrid, GeometryImplementation  # @IgnorePep8

# memoizedConnectionGenerators = {}


def connectionGeneratorFromProjection(projection, geometry):
    """
    Returns an object that supports ConnectionGenerator interface.

    :param projection: user-layer Projection object
    :param geometry: Geometry-derived object

    :rtype: ConnectionGenerator-derived object
    :raises: RuntimeError
    """
    rule = projection.rule

    """
    ACHTUNG, ACHTUNG!!
    Testing for attribute is a temporal workaround.
    Will be fixed when the XML serialization is implemented.
    """
    if hasattr(rule, 'connections'):
        connections = getattr(rule, 'connections')
        cg = ExplicitListOfConnections(connections)
        return cg

    # Assembling a CG instantiation
    cgClosure = alConnectionRuleFromURI(rule.definition.url)
    cg = cgClosure(rule.parameters)
    return cg


def geometryFromProjection(projection):
    """
    Returns an object that supports Geometry interface.

    :param projection: user-layer Projection object

    :rtype: Geometry-derived object
    :raises: RuntimeError
    """
    source_grid = createUnstructuredGrid(projection.source)
    target_grid = createUnstructuredGrid(projection.target)

    geometry = GeometryImplementation(source_grid, target_grid)
    return geometry
