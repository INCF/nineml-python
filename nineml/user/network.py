import re
import math
from itertools import chain
from .component import Property
import nineml.units as un
from .population import Population
from .projection import Projection
from .selection import Selection
from . import BaseULObject
from nineml.exceptions import name_error
from nineml.base import DocumentLevelObject, ContainerObject
from nineml.utils import validate_identifier
from .component_array import ComponentArray
from .connection_group import BaseConnectionGroup
from nineml.values import RandomDistributionValue
from nineml.exceptions import NineMLRandomDistributionDelayException


class Network(BaseULObject, DocumentLevelObject, ContainerObject):
    """
    Container for populations and projections between those populations.

    Parameters
    ----------
    name : str
        A name for the network.
    populations : iterable(Population)
        An iterable containing the populations contained in the network.
    projections : iterable(Projection)
        An iterable containing the projections contained in the network.
    selections : iterable(Selection)
        An iterable containing the selections contained in the network.
    """
    nineml_type = "Network"
    nineml_children = (Population, Projection, Selection)
    nineml_attr = ('name',)

    def __init__(self, name, populations=[], projections=[],
                 selections=[]):
        # better would be *items, then sort by type, taking the name from the
        # item
        self._name = validate_identifier(name)
        BaseULObject.__init__(self)
        DocumentLevelObject.__init__(self)
        ContainerObject.__init__(self)
        self.add(*populations)
        self.add(*projections)
        self.add(*selections)

    @property
    def name(self):
        return self._name

    @property
    def attributes_with_units(self):
        return chain(*[c.attributes_with_units for c in chain(
            self.populations, self.selections, self.projections)])

    @name_error
    def population(self, name):
        return self._populations[name]

    @name_error
    def projection(self, name):
        return self._projections[name]

    @name_error
    def selection(self, name):
        return self._selections[name]

    @property
    def populations(self):
        return iter(self._populations.values())

    @property
    def projections(self):
        return iter(self._projections.values())

    @property
    def selections(self):
        return iter(self._selections.values())

    @property
    def population_names(self):
        return iter(self._populations.keys())

    @property
    def projection_names(self):
        return iter(self._projections.keys())

    @property
    def selection_names(self):
        return iter(self._selections.keys())

    @property
    def num_populations(self):
        return len(self._populations)

    @property
    def num_projections(self):
        return len(self._projections)

    @property
    def num_selections(self):
        return len(self._selections)

    # =========================================================================
    # Core accessors
    # =========================================================================

    def all_components(self):
        components = []
        for p in chain(self.populations, self.projections):
            components.extend(p.all_components())
        return components

    def resample_connectivity(self, *args, **kwargs):
        for projection in self.projections:
            projection.resample_connectivity(*args, **kwargs)

    def connectivity_has_been_sampled(self):
        return any(p.connectivity.has_been_sampled() for p in self.projections)

    def delay_limits(self):
        """
        Returns the minimum delay and the maximum delay of projections in the
        network in ms
        """
        if not self.num_projections:
            min_delay = 0.0 * un.s
            max_delay = 0.0 * un.s
        else:
            min_delay = float('inf') * un.ms
            max_delay = 0.0 * un.ms
            for proj in self.projections:
                delay = proj.delay
                if isinstance(delay.value, RandomDistributionValue):
                    raise NineMLRandomDistributionDelayException(
                        "Delay of '{}' projection is randomly distributed "
                        "so cannot determine delay limits".format(proj.name))
                if delay > max_delay:
                    max_delay = delay
                if delay < min_delay:
                    min_delay = delay
        return {'min_delay': min_delay, 'max_delay': max_delay}

    def serialize_node(self, node, **options):  # @UnusedVariable
        node.attr('name', self.name, **options)
        node.children(self.populations, **options)
        node.children(self.selections, **options)
        node.children(self.projections, **options)

    @classmethod
    def unserialize_node(cls, node, **options):
        populations = node.children(Population, allow_ref=True, **options)
        projections = node.children(Projection, allow_ref=True, **options)
        selections = node.children(Selection, allow_ref=True, **options)
        network = cls(name=node.attr('name', **options),
                      populations=populations, projections=projections,
                      selections=selections)
        return network

    _conn_group_name_re = re.compile(
        r'(\w+)__(\w+)_(\w+)__(\w+)_(\w+)__connection_group')

    def flatten(self):
        """
        Flattens the populations and projections of the network into
        component arrays and connection groups (i.e. core 9ML objects)

        Returns
        -------
        component_arrays : list(ComponentArray)
            List of component arrays the populations and projection synapses
            have been flattened to
        connection_groups : list(ConnectionGroup)
            List of connection groups the projections have been flattened to
        """
        component_arrays = dict((ca.name, ca) for ca in chain(
            (ComponentArray(p.name + ComponentArray.suffix['post'], len(p),
                            p.cell.flatten())
             for p in self.populations),
            (ComponentArray(p.name + ComponentArray.suffix['response'], len(p),
                            p.response.flatten())
             for p in self.projections),
            (ComponentArray(p.name + ComponentArray.suffix['plasticity'],
                            len(p), p.plasticity.flatten())
             for p in self.projections if p.plasticity is not None)))
        connection_groups = list(chain(*(
            (BaseConnectionGroup.from_port_connection(pc, p, component_arrays)
             for pc in p.port_connections)
            for p in self.projections)))
        return list(component_arrays.values()), connection_groups

    def scale(self, scale):
        """
        Scales the size of the populations in the network and corresponding
        projection sizes

        Parameters
        ----------
        scale : float
            Scalar with which to scale the size of the network

        Returns
        -------
        scaled : Network
            A scaled copy of the network
        """
        scaled = self.clone()
        # rescale populations
        for pop in scaled.populations:
            pop.size = int(math.ceil(pop.size * scale))
        for proj in scaled.projections:
            conn = proj.connectivity
            props = conn.rule_properties
            conn._source_size = proj.pre.size
            conn._destination_size = proj.post.size
            if 'number' in props.property_names:
                number = props.property('number')
                props.set(Property(
                    number.name,
                    int(math.ceil(float(number.value) * scale)) * un.unitless))
        return scaled
