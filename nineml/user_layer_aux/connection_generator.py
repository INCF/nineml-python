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
        return _skip

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
    @property
    def arity(self):
        """
        Returns the number of parameters specified for an individual
        connection. It can be zero.
        
        :rtype: Integer
        :raises: IndexError
        """
        raise NotImplementedError
        return 0

    def setMask (self, mask):
        """
        Inform the generator of which source and target indexes exist
        (must always be called before any of the methods below)
   
        skip (specified in mask) can be used in round-robin allocation
        schemes.
        """
        raise NotImplementedError        

    def setMask (self, masks, local):
        """
        For a parallel simulator, we want to know the masks for all ranks
        """
        raise NotImplementedError
    
    @property
    def size(self):
        """
        :rtype: Integer (the number of the connections).
        :raises: RuntimeError 
        """
        raise NotImplementedError
        return 0
        
    def start(self):
        """
        Initializes the iterator.
        
        :rtype:
        :raises: 
        """
        pass
    
    def __iter__(self):
        """
        Initializes and returns the iterator.
        
        :rtype: ConnectionGenerator-derived object (self)
        :raises: 
        """
        self.start()
        raise NotImplementedError
        return self
    
    def next(self):
        """
        Returns the connection and moves the counter to the next one.
        The connection is a tuple: (source_index, target_index, [zero or more floating point values])
        
        :rtype: tuple
        :raises: StopIteration (as required by the python iterator concept)
        """
        raise NotImplementedError
        return (0, 0)

"""
                    ACHTUNG, ACHTUNG!

 * A name of the class? ExplicitListOfConnections?
 * Should we put it here or in a separate file?
 * Should we use Abstract Base Class (abc) package for ConnectionGenerator interface (see geometry.py file)?
 * Should we implement masks here as well?
"""
class ExplicitListOfConnections(ConnectionGenerator):
    """
    The implementation of the ConnectionGenerator interface for the explicit list of connections.
    
    **Achtung, Achtung!** 
    All indexes are zero based, for both source and target populations.
    """
    def __init__(self, connections):
        """
        Initializes the list of connections that the simulator can iterate on.
        
        :param connections: a list of tuples: (int, int) or (int, int, weight) or (int, int, weight, delay) 
                            or (int, int, weight, delay, parameters)
    
        :rtype:        
        :raises: RuntimeError 
        """
        if not connections or len(connections) == 0:
            raise RuntimeError('The connections argument is either None or an empty list')
        
        n_values = len(connections[0])
        if n_values < 2:
            raise RuntimeError('The number of items in each connection must be at least 2')
        
        for c in connections:
            if len(c) != n_values:
                raise RuntimeError('An invalid number of items in the connection: {0}; it should be {1}'.format(c, n_values))
        
        self._connections = connections
        self._current     = 0
    
    @property
    def size(self):
        """
        :rtype: Integer (the number of the connections).
        :raises:  
        """
        return len(self._connections)
        
    @property
    def arity(self):
        """
        Returns the number of values stored in an individual connection. It can be zero.
        The first two are always weight and delay; the rest are connection specific parameters.
        
        :rtype: Integer
        :raises: IndexError
        """
        return len(self._connections[0]) - 2
    
    def __iter__(self):
        """
        Initializes and returns the iterator.
        
        :rtype: explicit_connections_generator_interface object (self)
        :raises: 
        """
        self.start()
        return self
    
    def start(self):
        """
        Initializes the iterator.
        
        :rtype:
        :raises: 
        """
        self._current = 0
    
    def next(self):
        """
        Returns the connection and moves the counter to the next one.
        The connection is a tuple: (source_index, target_index, [zero or more floating point values])
        
        :rtype: tuple
        :raises: StopIteration (as required by the python iterator concept)
        """
        if self._current >= len(self._connections):
            raise StopIteration
        
        connection = self._connections[self._current]
        self._current += 1
        
        return connection
