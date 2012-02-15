class IntervalSet:
    def __init__ (self, initializer):
        pass

class Mask:
    def __init__ (self, sourceSkip = 1, targetSkip = 1, sources = [], targets = []):
        pass

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
        
        :rtype: explicit_connections_generator_interface object (self)
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
