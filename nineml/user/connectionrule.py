from itertools import chain
import math
from abc import ABCMeta, abstractmethod
from copy import copy
from itertools import izip, repeat, tee
import random
from nineml.exceptions import NineMLRuntimeError
from nineml.user.component import Component


class ConnectionRuleProperties(Component):
    """
    docstring needed
    """
    nineml_type = 'ConnectionRuleProperties'

    def get_nineml_type(self):
        return self.nineml_type

    @property
    def standard_library(self):
        return self.component_class.standard_library

    @property
    def lib_type(self):
        return self.component_class.lib_type


class BaseConnectivity(object):

    __metaclass__ = ABCMeta

    def __init__(self, connection_rule_properties, source_size,
                 destination_size,
                 **kwargs):  # @UnusedVariable
        if (connection_rule_properties.lib_type == 'OneToOne' and
                source_size != destination_size):
            raise NineMLRuntimeError(
                "Cannot connect to populations of different sizes "
                "({} and {}) with OneToOne connection rule"
                .format(source_size, destination_size))
        self._rule_props = connection_rule_properties
        self._src_size = source_size
        self._dest_size = destination_size
        self._cache = None
        self._kwargs = kwargs

    def __eq__(self, other):
        try:
            result = (self._rule_props == other._rule_props and
                      self._src_size == other._src_size and
                      self._dest_size == other._dest_size)
            return result
        except AttributeError:
            return False

    @property
    def rule_properties(self):
        return self._rule_props

    @property
    def rule(self):
        return self.rule_properties.component_class

    @property
    def lib_type(self):
        return self.rule_properties.lib_type

    @property
    def source_size(self):
        return self._src_size

    @property
    def destination_size(self):
        return self._dest_size

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        return ("{}(rule={}, src_size={}, dest_size={})"
                .format(self.__class__.__name__, self.lib_type,
                        self.source_size, self.destination_size))

    @abstractmethod
    def connections(self):
        pass

    @abstractmethod
    def has_been_sampled(self):
        pass


class InverseConnectivity(object):
    """
    Inverts the connectivity so that the source and destination are effectively
    flipped. Used when mapping a projection connectivity to a reverse
    connection to from the synapse or post-synaptic cell to the pre-synaptic
    cell
    """

    def __init__(self, connectivity):  # @UnusedVariable
        self._connectivity = connectivity

    def __eq__(self, other):
        return self._connectivity == other._connectivity

    @property
    def rule_properties(self):
        return self._connectivity._rule_props

    @property
    def rule(self):
        return self.rule_properties.component_class

    @property
    def lib_type(self):
        return self.rule_properties.lib_type

    @property
    def source_size(self):
        return self._connectivity.destination_size

    @property
    def destination_size(self):
        return self._connectivity.source_size

    def __repr__(self):
        return ("{}(rule={}, src_size={}, dest_size={})"
                .format(self.__class__.__name__, self.lib_type,
                        self.source_size, self.destination_size))

    @abstractmethod
    def connections(self):
        return ((j, i) for i, j in self._connectivity.connections)

    @abstractmethod
    def has_been_sampled(self):
        return self._connectivity.has_been_sampled


class Connectivity(BaseConnectivity):
    """
    A reference implementation of the Connectivity class, it is not recommended
    for large networks as it is not designed for efficiency (although perhaps
    with JIT it would be okay, see PyPy). More efficient implementations, which
    use external libraries such as NumPy can be supplied to the Projection as a
    kwarg.
    """

    def connections(self, **kwargs):
        """
        Returns an iterator over all the source/destination index pairings
        with a connection.
        `src`  -- the indices to get the connections from
        `dest` -- the indices to get the connections to
        """
        if self._kwargs:
            kw = kwargs
            kwargs = copy(self._kwargs)
            kwargs.update(kw)
        if self.lib_type == 'AllToAll':
            conn = self._all_to_all(**kwargs)
        elif self.lib_type == 'OneToOne':
            conn = self._one_to_one(**kwargs)
        elif self.lib_type == 'Explicit':
            conn = self._explicit_connection_list(**kwargs)
        elif self.lib_type == 'Probabilistic':
            conn = self._probabilistic_connectivity(**kwargs)
        elif self.lib_type == 'RandomFanIn':
            conn = self._random_fan_in(**kwargs)
        elif self.lib_type == 'RandomFanOut':
            conn = self._random_fan_out(**kwargs)
        else:
            assert False
        return conn

    def _all_to_all(self, **kwargs):  # @UnusedVariable
        return chain(*(((s, d) for d in xrange(self._dest_size))
                       for s in xrange(self._src_size)))

    def _one_to_one(self, **kwargs):  # @UnusedVariable
        return ((i, i) for i in xrange(self._src_size))

    def _explicit_connection_list(self, **kwargs):  # @UnusedVariable
        return izip(
            self._rule_props.property('sourceIndices').value.values,
            self._rule_props.property('destinationIndices').value.values)

    def _probabilistic_connectivity(self, **kwargs):  # @UnusedVariable
        if self._cache:
            conn = iter(self._cache)
        else:
            p = self._rule_props.property('probability').value
            # Get an iterator over all of the source dest pairs to test
            conn = chain(*(((s, d) for d in xrange(self._dest_size)
                            if random.random() < p)
                           for s in xrange(self._src_size)))
            conn, cpy = tee(conn)
            self._cache = list(cpy)
        return conn

    def _random_fan_in(self, **kwargs):  # @UnusedVariable
        if self._cache:
            conn = iter(self._cache)
        else:
            N = int(self._rule_props.property('number').value)
            conn = chain(*(
                izip((int(math.floor(random.random() * self._src_size))
                      for _ in xrange(N)),
                     repeat(d))
                for d in xrange(self._dest_size)))
            conn, cpy = tee(conn)
            self._cache = list(cpy)
        return conn

    def _random_fan_out(self, **kwargs):  # @UnusedVariable
        if self._cache:
            conn = iter(self._cache)
        else:
            N = int(self._rule_props.property('number').value)
            conn = chain(*(
                izip(repeat(s),
                     (int(math.floor(random.random() * self._dest_size))
                      for _ in xrange(N)))
                for s in xrange(self._src_size)))
            conn, cpy = tee(conn)
            self._cache = list(cpy)
        return conn

    def has_been_sampled(self):
        """
        Check to see whether randomly drawn values in the Connectivity object
        have been sampled (and cached) or not. Caching of random values allows
        multiple connection groups to reference the same instance of the
        connectivity (for example if they form part of one logical projection)
        """
        return (self.lib_type not in ('AllToAll', 'OneToOne',
                                      'ExplicitConnectionList') and
                self._cache is not None)
