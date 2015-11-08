import re
from itertools import chain
from nineml.user import ConnectionRuleProperties
from .population import Population
from .projection import Projection
from .selection import Selection
from . import BaseULObject
from .component import write_reference, resolve_reference
from nineml.annotations import annotate_xml, read_annotations
from nineml.exceptions import NineMLNameError
from nineml.base import DocumentLevelObject, ContainerObject
from nineml.xml import E, from_child_xml, unprocessed_xml, get_xml_attr
from .multi.component import MultiDynamics
from nineml.user.port_connections import EventPortConnection
from .multi.port_exposures import (
    AnalogReceivePortExposure, EventReceivePortExposure,
    AnalogSendPortExposure, EventSendPortExposure)
from .multi.namespace import append_namespace


class Network(BaseULObject, DocumentLevelObject, ContainerObject):
    """
    Container for populations and projections between those populations.

    **Arguments**:
        *name*
            a name for the network.
        *populations*
            a dict containing the populations contained in the network.
        *projections*
            a dict containing the projections contained in the network.
        *selections*
            a dict containing the selections contained in the network.
    """
    nineml_type = "Network"
    defining_attributes = ('name', "_populations", "_projections",
                           "_selections")
    class_to_member = {'Population': 'population',
                       'Projection': 'projection',
                       'Selection': 'selection'}
    write_order = ('Population', 'Selection', 'Projection')

    def __init__(self, name, populations=[], projections=[],
                 selections=[], document=None):
        # better would be *items, then sort by type, taking the name from the
        # item
        BaseULObject.__init__(self)
        DocumentLevelObject.__init__(self, document=document)
        ContainerObject.__init__(self)
        self._name = name
        self._populations = dict((p.name, p) for p in populations)
        self._projections = dict((p.name, p) for p in projections)
        self._selections = dict((s.name, s) for s in selections)

    @property
    def name(self):
        return self._name

    def population(self, name):
        return self._populations[name]

    def projection(self, name):
        return self._projections[name]

    def selection(self, name):
        return self._selections[name]

    @property
    def populations(self):
        return self._populations.itervalues()

    @property
    def projections(self):
        return self._projections.itervalues()

    @property
    def selections(self):
        return self._selections.itervalues()

    @property
    def population_names(self):
        return self._populations.iterkeys()

    @property
    def projection_names(self):
        return self._projections.iterkeys()

    @property
    def selection_names(self):
        return self._selections.iterkeys()

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

    def dynamics_array(self, name):
        return self._dyn_array_from_pop(self.population(name))

    @property
    def dynamics_arrays(self):
        return (self._dyn_array_from_pop(p) for p in self.populations)

    @property
    def dynamics_array_names(self):
        return self.population_names

    @property
    def num_dynamics_arrays(self):
        return self.num_populations

    def connection_group(self, name):
        try:
            return next(cg for cg in self.connection_groups
                        if cg.name == name)
        except StopIteration:
            raise NineMLNameError(
                "No connection group named '{}' in '{}' network (found '{}')"
                .format(name, self.name,
                        "', '".join(self.connection_group_names)))

    @property
    def connection_groups(self):
        dyn_dct = dict((da.name, da) for da in self.dynamics_arrays)
        return chain(*(self._conn_groups_from_proj(p, dynamics_arrays=dyn_dct)
                       for p in self.projections))

    @property
    def connection_group_names(self):
        return (cg.name for cg in self.connection_groups)

    @property
    def num_connection_groups(self):
        return len(list(self.connection_groups))

    def _dyn_array_from_pop(self, population):
        """
        Returns a multi-dynamics object containing the cell and all
        post-synaptic response/plasticity dynamics
        """
        # Get all the projections that project to/from the given population
        receiving = [p for p in self.projections if p.post == population]
        sending = [p for p in self.projections if p.pre == population]
        # Get all sub-dynamics, port connections and port exposures
        sub_dynamics = {'cell': population.cell.component_class}
        # =====================================================================
        # Get all the port connections between Response, Plasticity and Post
        # nodes and convert them to MultiDynamics port connections (i.e.
        # referring to sub-component names instead of projection roles)
        # =====================================================================
        port_connections = []
        for proj in receiving:
            sub_dynamics[proj.name + '_psr'] = proj.response.component_class
            sub_dynamics[proj.name + '_pls'] = proj.plasticity.component_class
            # Get all projection port connections that don't project to/from
            # the "pre" population and convert them into local MultiDynamics
            # port connections
            port_connections.extend(
                pc.__class__(
                    sender_name=self._role2dyn(proj.name, pc.sender_role),
                    receiver_name=self._role2dyn(proj.name, pc.receiver_role),
                    send_port=pc.send_port, receive_port=pc.receive_port)
                for pc in proj.port_connections
                if 'pre' not in (pc.sender_role, pc.receiver_role))
        # =====================================================================
        # Get all the ports that are connected to/from the Pre node and insert
        # a port exposure to handle them
        # =====================================================================
        port_exposures = []
        for proj in sending:
            port_exposures.extend(
                AnalogSendPortExposure(component='cell', port=pc.send_port)
                for pc in proj.analog_port_connections
                if 'pre' == pc.sender_role)
            port_exposures.extend(
                EventSendPortExposure(component='cell', port=pc.send_port)
                for pc in proj.event_port_connections
                if 'pre' == pc.sender_role)
            port_exposures.extend(
                AnalogReceivePortExposure(component='cell',
                                          port=pc.receive_port)
                for pc in proj.analog_port_connections
                if 'pre' == pc.receiver_role)
            port_exposures.extend(
                EventReceivePortExposure(component='cell',
                                         port=pc.receive_port)
                for pc in proj.event_port_connections
                if 'pre' == pc.receiver_role)
        for proj in receiving:
            port_exposures.extend(
                AnalogReceivePortExposure(
                    component=self._role2dyn(proj.name, pc.receiver_role),
                    port=pc.receive_port)
                for pc in proj.analog_port_connections
                if 'pre' == pc.sender_role)
            port_exposures.extend(
                EventReceivePortExposure(
                    component=self._role2dyn(proj.name, pc.receiver_role),
                    port=pc.receive_port)
                for pc in proj.event_port_connections
                if 'pre' == pc.sender_role)
            port_exposures.extend(
                AnalogSendPortExposure(
                    component=self._role2dyn(proj.name, pc.sender_role),
                    port=pc.send_port)
                for pc in proj.analog_port_connections
                if 'pre' == pc.receiver_role)
            port_exposures.extend(
                EventSendPortExposure(
                    component=self._role2dyn(proj.name, pc.sender_role),
                    port=pc.send_port)
                for pc in proj.event_port_connections
                if 'pre' == pc.receiver_role)
        dyn = MultiDynamics(
            name=population.name + 'Dynamics',
            sub_components=sub_dynamics, port_connections=port_connections,
            port_exposures=port_exposures)
        return DynamicsArray(population.name, population.size, dyn)

    def _conn_groups_from_proj(self, projection, dynamics_arrays=None):
        if dynamics_arrays:
            source = dynamics_arrays[projection.pre.name]
            dest = dynamics_arrays[projection.post.name]
        else:
            source = self._dyn_array_from_pop(projection.pre)
            dest = self._dyn_array_from_pop(projection.post)
        return (
            BaseConnectionGroup.cls_from_port_connection(pc)(
                '{}__{}_{}__{}_{}___connection_group'.format(
                    projection.name, pc.sender_role, pc.send_port_name,
                    pc.receiver_role, pc.receive_port_name),
                source, dest,
                source_port=append_namespace(
                    pc.send_port,
                    self._role2dyn(projection.name, pc.sender_role)),
                destination_port=append_namespace(
                    pc.receive_port,
                    self._role2dyn(projection.name, pc.receiver_role)),
                projection.connectivity)
            for pc in projection.port_connections
            if 'pre' in (pc.sender_role, pc.receiver_role))

    def get_components(self):
        components = []
        for p in chain(self.populations.values(), self.projections.values()):
            components.extend(p.get_components())
        return components

    @write_reference
    @annotate_xml
    def to_xml(self, document, E=E, **kwargs):  # @UnusedVariable
        member_elems = []
        for member in chain(self.populations, self.selections,
                            self.projections):
            member_elems.append(member.to_xml(
                document, E=E, as_ref=True, **kwargs))
        return E(self.nineml_type, name=self.name, *member_elems)

    @classmethod
    @resolve_reference
    @read_annotations
    @unprocessed_xml
    def from_xml(cls, element, document, **kwargs):
        populations = from_child_xml(element, Population, document,
                                     multiple=True, allow_reference='only',
                                     allow_none=True, **kwargs)
        projections = from_child_xml(element, Projection, document,
                                     multiple=True, allow_reference='only',
                                     allow_none=True, **kwargs)
        selections = from_child_xml(element, Selection, document,
                                    multiple=True, allow_reference='only',
                                    allow_none=True, **kwargs)
        network = cls(name=get_xml_attr(element, 'name', document, **kwargs),
                      populations=populations, projections=projections,
                      selections=selections)
        return network

    @classmethod
    def _role2dyn(cls, name, role):
        if role in ('post', 'pre'):
            dyn_name = 'cell'
        elif role == 'response':
            dyn_name = name + '_psr'
        elif role == 'plasticity':
            dyn_name = name + '_pls'
        else:
            assert False
        return dyn_name

    _conn_group_name_re = re.compile(
        r'(\w+)__(\w+)_(\w+)__(\w+)_(\w+)__connection_group')


class DynamicsArray(BaseULObject):

    nineml_type = "DynamicsArray"
    defining_attributes = ('name', "_size", "_dynamics")

    def __init__(self, name, size, dynamics):
        self._name = name
        self._size = size
        self._dynamics = dynamics

    @property
    def name(self):
        return self._name

    @property
    def size(self):
        return self._size

    @property
    def dynamics(self):
        return self._dynamics


class BaseConnectionGroup(BaseULObject):

    defining_attributes = ('name', "source", "destination",
                           "source_port", "destination_port",
                           "_connections")

    def __init__(self, name, source, destination, source_port,
                 destination_port, connections):
        assert isinstance(name, basestring)
        assert isinstance(source, DynamicsArray)
        assert isinstance(destination, DynamicsArray)
        assert isinstance(source_port, basestring)
        assert isinstance(destination_port, basestring)
        assert isinstance(connections, ConnectionRuleProperties)
        self._name = name
        self._source = source
        self._destination = destination
        self._source_port = source_port
        self._destination_port = destination_port
        self._connections = connections

    @property
    def name(self):
        return self._name

    @property
    def source(self):
        return self._source

    @property
    def destination(self):
        return self._destination

    @property
    def source_port(self):
        return self._source_port

    @property
    def destination_port(self):
        return self._destination_port

    @property
    def connections(self):
        return self._connections

    @classmethod
    def cls_from_port_connection(cls, port_connection):
        if isinstance(port_connection, EventPortConnection):
            conn_grp_cls = EventConnectionGroup
        else:
            conn_grp_cls = AnalogConnectionGroup
        return conn_grp_cls


class AnalogConnectionGroup(BaseConnectionGroup):

    nineml_type = 'AnalogConnectionGroup'


class EventConnectionGroup(BaseConnectionGroup):

    nineml_type = 'EventConnectionGroup'


class Connections(object):

    def __init__(self, connection_rule):
        self._connection_rule = connection_rule
