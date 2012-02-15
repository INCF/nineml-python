#!/usr/bin/env python
# -*- coding: utf-8 -*-

import math
from abc import ABCMeta, abstractmethod

class StructureInterface(object):
    """
    Structure Interface exposed by *nineml.user_layer.Structure* objects.
    
    It has got three methods:
     * metric: returns a distance between two neurones
     * position: returns x,y,z coordinates of a neurone
     * positions: returns a list of x,y,z coordinates of all neurones 
    """
    
    __metaclass__ = ABCMeta
    
    @abstractmethod
    def metric(self, source_index, target_index):
        """
        Returns a distance between two points (units: ???) specified by the *source_index*
        and the *source_index* arguments.
        
        :param source_index: Integer
        :param target_index: Integer
        
        :rtype: Float
        :raises: RuntimeError, IndexError, NotImplementedError
        """
        pass

    @abstractmethod
    def position(self, index):
        """
        Returns a coordinate (tuple: (x, y, z); units: ???) of a point specified by the *index* argument.
        
        :param index: Integer
        
        :rtype: Float
        :raises: RuntimeError, IndexError, NotImplementedError
        """
        pass

    @abstractmethod
    def positions(self):
        """
        Returns a list of coordinates (list of tuples: (x, y, z); units: ???) for all points in the structure.
        
        :rtype: list of (float, float, float) tuples
        :raises: RuntimeError, IndexError, NotImplementedError
        """
        pass

class UnstructuredGrid(StructureInterface):
    def __init__(self, positions):
        if not positions:
            raise RuntimeError('')
        if not isinstance(positions, list):
            raise RuntimeError('')
        
        self.positions = positions
    
    def metric(self, source_index, target_index):
        (sx, sy, sz) = self.positions[source_index]
        (tx, ty, tz) = self.positions[target_index]
        return math.sqrt( (sx - tx) ** 2 + (sy - ty) ** 2 + (sz - tz) ** 2 )

    def position(self, index):
        return self.positions[index]
    
    def positions(self):
        return self.positions
        
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
    
    