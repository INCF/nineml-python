import sys
from itertools import chain, product
import math
from abc import ABCMeta, abstractmethod
from itertools import izip, repeat
from random import Random, randint
from nineml.base import clone_id, BaseNineMLObject
from nineml.exceptions import NineMLRuntimeError
from nineml.user.component import Component
from nineml.abstraction.connectionrule import ConnectionRule


class ConnectionRuleProperties(Component):
    """
    docstring needed
    """
    nineml_type = 'ConnectionRuleProperties'
    nineml_child = {'definition': ConnectionRule}

    def get_nineml_type(self):
        return self.nineml_type

    @property
    def standard_library(self):
        return self.component_class.standard_library

    @property
    def lib_type(self):
        return self.component_class.lib_type


class BaseConnectivity(BaseNineMLObject):
    """
    An abstract base classes for instances of connectivity
    (i.e. connection-rule + properties + random seed)
    """

    __metaclass__ = ABCMeta
    defining_attributes = ('_rule_properties', '_source_size',
                           '_destination_size')
    nineml_attr = ('rule_properties', 'source_size', 'destination_size')

    def __init__(self, rule_properties, source_size,
                 destination_size, **kwargs):  # @UnusedVariable
        if (rule_properties.lib_type == 'OneToOne' and
                source_size != destination_size):
            raise NineMLRuntimeError(
                "Cannot connect to populations of different sizes "
                "({} and {}) with OneToOne connection rule"
                .format(source_size, destination_size))
        self._rule_properties = rule_properties
        self._source_size = source_size
        self._destination_size = destination_size

    def __eq__(self, other):
        try:
            return (self._rule_properties == other._rule_properties and
                    self._source_size == other._source_size and
                    self._destination_size == other._destination_size)
        except AttributeError:
            return False

    @property
    def rule_properties(self):
        return self._rule_properties

    @property
    def rule(self):
        return self.rule_properties.component_class

    @property
    def lib_type(self):
        return self.rule_properties.lib_type

    @property
    def source_size(self):
        return self._source_size

    @property
    def destination_size(self):
        return self._destination_size

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

    @abstractmethod
    def clone(self, memo, **kwargs):
        pass


class InverseConnectivity(BaseNineMLObject):
    """
    Inverts the connectivity so that the source and destination are effectively
    flipped. Used when mapping a projection connectivity to a reverse
    connection to from the synapse or post-synaptic cell to the pre-synaptic
    cell
    """
    nineml_type = '_InverseConnectivity'
    defining_attributes = ('_connectivity',)

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
    A reference implementation of the Connectivity class.
    """
    nineml_type = '_Connectivity'

    def __init__(self, rule_properties, source_size,
                 destination_size, random_seed=None, rng_cls=None):
        """
        Parameters
        ----------
        rule_properties: ConnectionRuleProperties
            Connection rule and properties that define the connectivity
            instance
        source_size : int
            Size of the source component array
        destination_size : int
            Size of the destination component array
        random_seed : int | None
            Seed for the random generator (if required). If None then a
            random integer is drawn from random.randint
        rng_cls : random generator class (i.e. random.Random) | None
            Class for the random generator. Can be any random generator that
            implements the 'random' method to return a float between 0 and 1
            (e.g. numpy.Random). If not supplied then random.Random is used
        """
        super(Connectivity, self).__init__(
            rule_properties, source_size, destination_size)
        if random_seed is None:
            random_seed = randint(0, sys.maxint)
        self._seed = random_seed
        if rng_cls is None:
            rng_cls = Random
        self._rng_cls = rng_cls

    def connections(self):
        """
        Returns an iterator over all the source/destination index pairings
        with a connection.
        `src`  -- the indices to get the connections from
        `dest` -- the indices to get the connections to
        """
        if self.lib_type == 'AllToAll':
            conn = self._all_to_all()
        elif self.lib_type == 'OneToOne':
            conn = self._one_to_one()
        elif self.lib_type == 'Explicit':
            conn = self._explicit_connection_list()
        elif self.lib_type == 'Probabilistic':
            conn = self._probabilistic_connectivity()
        elif self.lib_type == 'RandomFanIn':
            conn = self._random_fan_in()
        elif self.lib_type == 'RandomFanOut':
            conn = self._random_fan_out()
        else:
            assert False
        return conn

    def _all_to_all(self):  # @UnusedVariable
        return product(xrange(self._source_size),
                       xrange(self._destination_size))

    def _one_to_one(self):  # @UnusedVariable
        assert self._source_size == self._destination_size
        return ((i, i) for i in xrange(self._source_size))

    def _explicit_connection_list(self):  # @UnusedVariable
        return izip(
            self._rule_properties.property('sourceIndices').value.values,
            self._rule_properties.property('destinationIndices').value.values)

    def _probabilistic_connectivity(self):  # @UnusedVariable
        # Reinitialize the connectivity generator with the same RNG so that
        # it selects the same numbers
        rng = self._rng_cls(self._seed)
        p = float(self._rule_properties.property('probability').value)
        # Get an iterator over all of the source dest pairs to test
        return chain(*(((s, d) for d in xrange(self._destination_size)
                        if rng.random() < p)
                       for s in xrange(self._source_size)))

    def _random_fan_in(self):  # @UnusedVariable
        N = int(self._rule_properties.property('number').value)
        rng = self._rng_cls(self._seed)
        return chain(*(
            izip((int(math.floor(rng.random() * self._source_size))
                  for _ in xrange(N)),
                 repeat(d))
            for d in xrange(self._destination_size)))

    def _random_fan_out(self):  # @UnusedVariable
        N = int(self._rule_properties.property('number').value)
        rng = self._rng_cls(self._seed)
        return chain(*(
            izip(repeat(s),
                 (int(math.floor(rng.random() * self._destination_size))
                  for _ in xrange(N)))
            for s in xrange(self._source_size)))

    def clone(self, memo=None, random_seeds=False, **kwargs):
        if memo is None:
            memo = {}
        try:
            # See if the attribute has already been cloned in memo
            clone = memo[clone_id(self)]
        except KeyError:
            if random_seeds:
                random_seed = self._seed
            else:
                random_seed = None
            clone = self.__class__(
                self.rule_properties.clone(memo=memo,
                                           random_seeds=random_seeds,
                                           **kwargs),
                self.source_size, self.destination_size,
                random_seed=random_seed, rng_cls=self._rng_cls)
            memo[clone_id(self)] = clone
        return clone

    def has_been_sampled(self):
        return True  # Because seed and RNG class is set at start
