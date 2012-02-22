#!/usr/bin/env python
"""
.. module:: geometry.py
   :platform: Unix, Windows
   :synopsis: 

.. moduleauthor:: Mikael Djurfeldt <mikael.djurfeldt@incf.org>
.. moduleauthor:: Dragan Nikolic <dnikolic@incf.org>
"""

import math
from abc import ABCMeta, abstractmethod, abstractproperty

import nineml
import nineml.user_layer
from nineml.abstraction_layer import readers

def createGeometry(ul_projection):
    """
    Returns an object that supports Geometry interface (used by ConnectionRule components, ...).
    
    ACHTUNG, ACHTUNG!!
    Currently, we support only populations of spiking neurones (not groups).
    
    :param ul_projection: user-layer Projection object
    
    :rtype: Geometry-derived object
    :raises: RuntimeError, TypeError
    """
    if not isinstance(ul_projection.source.prototype, nineml.user_layer.SpikingNodeType):
        raise RuntimeError('Currently, only populations of spiking neurones (not groups) are supported')
    if not isinstance(ul_projection.target.prototype, nineml.user_layer.SpikingNodeType):
        raise RuntimeError('Currently, only populations of spiking neurones (not groups) are supported')
    
    source_grid = createUnstructuredGrid(ul_projection.source)
    target_grid = createUnstructuredGrid(ul_projection.target)
   
    geometry = GeometryImplementation(source_grid, target_grid)
    return geometry

class Geometry(object):
    """
    Geometry interface has got three methods:
     * metric: returns a distance between two neurones
     * sourcePosition: returns x,y,z coordinates of a neurone from the source Population/Selection/Group
     * targetPosition: returns x,y,z coordinates of a neurone from the target Population/Selection/Group
    """
    
    __metaclass__ = ABCMeta
    
    sourceIndex = 0
    targetindex = 1
    
    @abstractmethod
    def metric(self, source_index, target_index):
        """
        Returns a distance between two points (units: ???) specified by the *source_index*
        and the *target_index* arguments.
        
        :param source_index: Integer
        :param target_index: Integer
        
        :rtype: Float
        :raises: RuntimeError, IndexError, TypeError
        """
        pass

    @abstractmethod
    def sourcePosition(self, index):
        """
        Returns a coordinate (tuple: (x, y, z); units: ???) of a point specified by the *index* argument.
        
        :param index: Integer
        
        :rtype: Float
        :raises: RuntimeError, IndexError, TypeError
        """
        pass

    @abstractmethod
    def targetPosition(self, index):
        """
        Returns a coordinate (tuple: (x, y, z); units: ???) of a point specified by the *index* argument.
        
        :param index: Integer
        
        :rtype: Float
        :raises: RuntimeError, IndexError, TypeError
        """
        pass
    
class GeometryImplementation(Geometry):
    """
    Implementation of the Geometry interface. 
    It is a wrapper on top the source and target UnstructuredGrid object.
    """
    def __init__(self, source_unstructured_grid, target_unstructured_grid):
        if (not source_unstructured_grid) or (not isinstance(source_unstructured_grid, UnstructuredGrid)):
            raise RuntimeError('')
        if (not target_unstructured_grid) or (not isinstance(target_unstructured_grid, UnstructuredGrid)):
            raise RuntimeError('')
        
        self.source_unstructured_grid = source_unstructured_grid
        self.target_unstructured_grid = target_unstructured_grid
    
    def metric(self, source_index, target_index):
        (x1, y1, z1) = self.source_unstructured_grid.positions[source_index]
        (x2, y2, z2) = self.target_unstructured_grid.positions[target_index]
        return math.sqrt( (x1 - x2) ** 2 + (y1 - y2) ** 2 + (z1 - z2) ** 2 )
    
    def sourcePosition(self, index):
        return self.source_unstructured_grid.positions[index]
    
    def targetPosition(self, index):
        return self.target_unstructured_grid.positions[index]

def createUnstructuredGrid(ul_population):
    """
    """
    if ul_population.positions._positions:
        if len(ul_population.positions._positions) != ul_population.number:
            raise RuntimeError('')
        positions = ul_population.positions._positions
    
    elif ul_population.positions.structure:
        try:
            # Try to load the structure component
            url = ul_population.positions.structure.definition.url
            al_structure = nineml.abstraction_layer.readers.XMLReader.read(url) 
        
        except Exception as e:
            raise RuntimeError('Failed to load the Structure component: {0}; the reason: {1}'.format(url, str(e)))
        
        if al_structure.name == 'TwoDimensionalGrid':
            if 'x0' in al_structure.parameters:
                x0 = al_structure.parameters['x0']
            else:
                raise RuntimeError('')
            
            if 'y0' in al_structure.parameters:
                y0 = al_structure.parameters['y0']
            else:
                raise RuntimeError('')
            
            if 'width' in al_structure.parameters:
                width = al_structure.parameters['width']
            else:
                raise RuntimeError('')
            
            if 'height' in al_structure.parameters:
                height = al_structure.parameters['height']
            else:
                raise RuntimeError('')
            
            if 'Nx' in al_structure.parameters:
                Nx = al_structure.parameters['Nx']
            else:
                raise RuntimeError('')
            
            if 'Ny' in al_structure.parameters:
                Ny = al_structure.parameters['Ny']
            else:
                raise RuntimeError('')
            
            if Nx*Ny != ul_population.number:
                raise RuntimeError('')
            
            return Grid2D(x0, y0, width, height, Nx, Ny)
        
        else:
            raise RuntimeError('')
        
    else:
        raise RuntimeError('')
    
    return UnstructuredGrid(positions)

class UnstructuredGrid(object):
    """
    The base class for all objects created from user_layer.Structure objects. 
    """
    def __init__(self, positions):
        if not positions:
            raise RuntimeError('')
        if not isinstance(positions, list):
            raise RuntimeError('')
        
        self._positions = positions

    @property
    def positions(self):
        return self._positions

class Grid2D(UnstructuredGrid):
    def __init__(self, x0, y0, width, height, Nx, Ny):
        self.x0     = x0
        self.y0     = y0
        self.width  = width
        self.height = height
        self.Nx     = Nx
        self.Ny     = Ny
        
        dx = float(width)  / (Nx - 1)
        dy = float(height) / (Ny - 1)
        positions = [ (x0 + i*dx, y0 + j*dy, 0.0) for i in xrange(0, Nx) for j in xrange(0, Ny) ]
        
        UnstructuredGrid.__init__(self, positions)
    
    def __str__(self):
        return str(self.positions)
    
    def __repr__(self):
        return 'Grid2D({0}, {1}, {2}, {3}, {4}, {5})'.format(self.x0, self.y0, self.width, self.height, self.Nx, self.Ny)

if __name__ == "__main__":
    grid2d = Grid2D(0.0, 0.0, 0.1, 0.1, 20, 20)
    print(grid2d)
    print(repr(grid2d))
    print(grid2d.positions)
    
    