from itertools import chain
from .population import Population
from .projection import Projection
from .selection import Selection
from . import BaseULObject
from .component import write_reference, resolve_reference
from nineml.annotations import annotate_xml, read_annotations
from nineml.base import DocumentLevelObject, ContainerObject
from nineml.xml import E, from_child_xml, unprocessed_xml, get_xml_attr
from .multi import (
    MultiDynamics, AnalogReceivePortExposure, EventReceivePortExposure,
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
    element_name = "Network"
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

    def post_synaptic_dynamics(self, population_name):
        """
        Returns a multi-dynamics object containing the cell and all
        post-synaptic response/plasticity dynamics
        """
        # Get the population
        pop = self.population(population_name)
        # Get all the projections that project to the given population
        received = [p for p in self.projections if p.post == pop]
        # Get all sub-dynamics, port connections and port exposures
        sub_dynamics = {'cell': pop.cell}
        port_connections = []
        port_exposures = []
        for proj in received:
            sub_dynamics[p.name + '_psr'] = proj.response
            sub_dynamics[p.name + '_pls'] = proj.plasticity
            # Get all projection port connections that don't project to/from
            # the "pre" population and convert them into local MultiDynamics
            # port connections
            port_connections.extend(
                pc.cls(sender_name=self._role2dyn(proj.name, pc.sender_role),
                       receiver_name=self._role2dyn(proj.name,
                                                    pc.receiver_role),
                       send_port=pc.send_port, receive_port=pc.receive_port)
                for pc in proj.port_connections
                if 'pre' not in (pc.sender_role, pc.receiver_role))
            # Get all the projection port connections that project to/from the
            # the "pre" population and convert them into port exposures
            port_exposures.extend(
                AnalogReceivePortExposure(
                    component=self._role2dyn(pc.receiver_role),
                    port=pc.receive_port)
                for pc in proj.analog_port_connections
                if 'pre' == pc.sender_role)
            port_exposures.extend(
                EventReceivePortExposure(
                    component=self._role2dyn(pc.receiver_role),
                    port=pc.receive_port)
                for pc in proj.event_port_connections
                if 'pre' == pc.sender_role)
            port_exposures.extend(
                AnalogSendPortExposure(
                    component=self._role2dyn(pc.sender_role),
                    port=pc.send_port)
                for pc in proj.analog_port_connections
                if 'pre' == pc.receiver_role)
            port_exposures.extend(
                EventSendPortExposure(
                    component=self._role2dyn(pc.sender_role),
                    port=pc.send_port)
                for pc in proj.event_port_connections
                if 'pre' == pc.receiver_role)
        return MultiDynamics(
            name=pop.name + 'Dynamics',
            sub_dynamics=sub_dynamics, port_connections=port_connections,
            port_exposures=port_exposures)

    def pre_synaptic_connections(self, projection_name):
        proj = self.projection(projection_name)
        return (
            pc.cls(
                sender_role=pc.sender_role, receiver_role=pc.receiver_role,
                receive_port=append_namespace(
                    pc.receive_port, self._role2dyn(proj.name,
                                                    pc.sender_role)),
                send_port=append_namespace(
                    pc.send_port, self._role2dyn(proj.name, pc.receiver_role)))
            for pc in proj.port_connections
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
        return E(self.element_name, name=self.name, *member_elems)

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
        if role == 'post':
            dyn_name = 'cell'
        elif role == 'response':
            dyn_name = name + '_psr'
        elif role == 'plasticity':
            dyn_name = name + '_pls'
        else:
            assert False
        return dyn_name
