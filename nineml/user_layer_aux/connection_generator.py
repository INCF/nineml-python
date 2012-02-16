#!/usr/bin/env python
"""
.. module:: connection_generator.py
   :platform: Unix, Windows
   :synopsis: 

.. moduleauthor:: Mikael Djurfeldt <mikael.djurfeldt@incf.org>
"""

from abc import ABCMeta, abstractmethod, abstractproperty

class IntervalSet:
    def __init__ (self, intervals = [], skip = 1):
        """
        intervals is a list of 2-tuples (FROM, TO) representing all
        integers i, FROM <= i <= TO
        """
        self.intervals = intervals
        self._skip = skip

    @property
    def skip (self):
        return self._skip

    def __iter__ (self):
        return self.intervals.__iter__ ()


class Mask:
    def __init__ (self,
                  sources = [], targets = [],
                  sourceSkip = 1, targetSkip = 1):
        """
        sources and targets are lists of 2-tuples (FROM, TO)
        representing all integers i, FROM <= i <= TO
        """
        self.sources = IntervalSet (sources, sourceSkip)
        self.targets = IntervalSet (targets, targetSkip)


class ConnectionGenerator:
    """
    The ConnectionGenerator interface.
    """
    
    __metaclass__ = ABCMeta
    
    @abstractproperty
    def size(self):
        """
        Returns the number of connections in the generator.
        
        :rtype: Integer (the number of the connections).
        :raises: TypeError 
        """
        pass
    
    @abstractproperty
    def arity(self):
        """
        Returns the number of parameters specified for an individual
        connection. It can be zero.
        
        :rtype: Integer
        :raises: TypeError
        """
        pass

    @abstractmethod
    def setMask (self, mask):
        """
        Inform the generator of which source and target indexes exist
        (must always be called before any of the methods below)
   
        :param mask: Mask object. skip (specified in mask) can be used in 
                     round-robin allocation schemes.
        
        :rtype: None
        :raises: TypeError
        """
        pass        

    def setMasks (self, masks, local):
        """
        For a parallel simulator, we want to know the masks for all ranks
        
        :rtype: None
        :raises: TypeError
        """
        self.setMask(masks[local])
    
    @abstractmethod
    def __iter__(self):
        """
        Initializes and returns the iterator.
        
        :rtype: ConnectionGenerator-derived object (self)
        :raises: TypeError
        """
        pass
    
    @abstractmethod
    def next(self):
        """
        Returns the connection and moves the counter to the next one.
        The connection is a tuple: (source_index, target_index, [parameters]).
        The number of parameters returned is equal to *arity*.
        
        :rtype: tuple
        :raises: TypeError, StopIteration (as required by the python iterator concept)
        """
        pass
