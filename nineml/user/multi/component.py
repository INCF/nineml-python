from itertools import chain
from .. import BaseULObject
import re
from copy import copy
from itertools import product
from nineml.abstraction import (
    Dynamics, Regime, AnalogReceivePort, AnalogReducePort, EventReceivePort,
    StateVariable)
from nineml.reference import resolve_reference, write_reference
from nineml import DocumentLevelObject
from nineml.xmlns import NINEML, E
from nineml.utils import expect_single
from nineml.user import DynamicsProperties
from nineml.annotations import annotate_xml, read_annotations
from nineml.exceptions import NineMLRuntimeError
from ..port_connections import (
    AnalogPortConnection, EventPortConnection, BasePortConnection)
from nineml.abstraction import BaseALObject
from nineml.base import MemberContainerObject
from nineml.utils import ensure_valid_identifier
from nineml.annotations import VALIDATE_DIMENSIONS
from .ports import (
    EventReceivePortExposure, EventSendPortExposure, AnalogReducePortExposure,
    AnalogReceivePortExposure, AnalogSendPortExposure, BasePortExposure,
    LocalReducePortConnections, LocalEventPortConnections,
    LocalAnalogPortConnection)
from .namespace import (
    NamespaceAlias, NamespaceRegime, NamespaceStateVariable, NamespaceConstant,
    NamespaceParameter, NamespaceProperty)


# Matches multiple underscores, so they can be escaped by appending another
# underscore (double underscores are used to delimit namespaces).
multiple_underscore_re = re.compile(r'(.*)(__+)()')
# Match only double underscores (no more or less)
double_underscore_re = re.compile(r'(?<!_)__(?!_)')
# Match more than double underscores to reverse escaping of double underscores
# in sub-component suffixes by adding an additional underscore.
more_than_double_underscore_re = re.compile(r'(__)_+')


class MultiDynamicsProperties(DynamicsProperties):

    element_name = "MultiDynamics"
    defining_attributes = ('_name', '_sub_component_properties',
                           '_port_exposures', '_port_connections')

    def __init__(self, name, sub_components, port_connections,
                 port_exposures=[]):
        if isinstance(sub_components, dict):
            sub_components = [
                SubDynamics(n, sc.component_class)
                for n, sc in sub_components.iteritems()]
        else:
            sub_components = [
                SubDynamics(sc.name, sc.component.component_class)
                for sc in sub_components]
        component_class = MultiDynamics(
            name + '_Dynamics', sub_components,
            port_exposures=port_exposures, port_connections=port_connections)
        super(MultiDynamicsProperties, self).__init__(
            name, definition=component_class,
            properties=chain(*[p.properties for p in sub_components]))
        self._sub_component_properties = dict(
            (p.name, p) for p in sub_components)

    @property
    def name(self):
        return self._name

    @property
    def sub_components(self):
        return self._sub_component_properties.itervalues()

    @property
    def port_connections(self):
        return iter(self._port_connections)

    @property
    def port_exposures(self):
        return self._port_exposures.itervalues()

    def sub_component(self, name):
        return self._sub_component_properties[name]

    def port_exposure(self, name):
        return self._port_exposures[name]

    @property
    def sub_component_names(self):
        return self.sub_component.iterkeys()

    @property
    def port_exposure_names(self):
        return self._port_exposures.iterkeys()

    @property
    def attributes_with_units(self):
        return chain(*[c.attributes_with_units
                       for c in self.sub_component])

    @write_reference
    @annotate_xml
    def to_xml(self, document, **kwargs):
        members = [c.to_xml(document, **kwargs)
                   for c in self.sub_component_properties]
        members.extend(pe.to_xml(document, **kwargs)
                        for pe in self.port_exposures)
        members.extend(pc.to_xml(document, **kwargs)
                       for pc in self.port_connections)
        return E(self.element_name, *members, name=self.name)

    @classmethod
    @resolve_reference
    @read_annotations
    def from_xml(cls, element, document, **kwargs):
        cls.check_tag(element)
        sub_component_properties = [
            SubDynamicsProperties.from_xml(e, document, **kwargs)
            for e in element.findall(NINEML + 'SubDynamics')]
        port_exposures = [
            AnalogSendPortExposure.from_xml(e, document, **kwargs)
            for e in element.findall(NINEML + 'AnalogSendPortExposure')]
        port_exposures.extend(
            AnalogReceivePortExposure.from_xml(e, document, **kwargs)
            for e in element.findall(NINEML + 'AnalogReceivePortExposure'))
        port_exposures.extend(
            AnalogReducePortExposure.from_xml(e, document, **kwargs)
            for e in element.findall(NINEML + 'AnalogReducePortExposure'))
        port_exposures.extend(
            EventSendPortExposure.from_xml(e, document, **kwargs)
            for e in element.findall(NINEML + 'EventSendPortExposure'))
        port_exposures.extend(
            EventReceivePortExposure.from_xml(e, document, **kwargs)
            for e in element.findall(NINEML + 'EventReceivePortExposure'))
        analog_port_connections = [
            AnalogPortConnection.from_xml(e, document, **kwargs)
            for e in element.findall(NINEML + 'AnalogPortConnection')]
        event_port_connections = [
            EventPortConnection.from_xml(e, document, **kwargs)
            for e in element.findall(NINEML + 'EventPortConnection')]
        return cls(name=element.attrib['name'],
                   sub_component_properties=sub_component_properties,
                   port_exposures=port_exposures,
                   port_connections=chain(analog_port_connections,
                                          event_port_connections))


class SubDynamicsProperties(BaseULObject):

    element_name = 'SubDynamicsProperties'
    defining_attributes = ('_name', '_dynamics')

    def __init__(self, name, component):
        BaseULObject.__init__(self)
        self._name = name
        self._component = component

    @property
    def name(self):
        return self._name

    @property
    def component(self):
        return self._component

    @property
    def properties(self):
        return (NamespaceProperty(self, p) for p in self._component.properties)

    def __iter__(self):
        return self.properties

    @annotate_xml
    def to_xml(self, document, **kwargs):  # @UnusedVariable
        return E(self.element_name, self._component.to_xml(document, **kwargs),
                 name=self.name)

    @classmethod
    @read_annotations
    def from_xml(cls, element, document, **kwargs):
        try:
            dynamics_properties = DynamicsProperties.from_xml(
                expect_single(
                    element.findall(NINEML + 'DynamicsProperties')),
                document, **kwargs)
        except NineMLRuntimeError:
            dynamics_properties = MultiDynamicsProperties.from_xml(
                expect_single(
                    element.findall(NINEML + 'MultiDynamics')),
                document, **kwargs)
        return cls(element.attrib['name'], dynamics_properties)


class MultiDynamics(Dynamics):

    def __init__(self, name, sub_components, port_connections,
                 port_exposures=None, url=None, validate_dimensions=True):
        ensure_valid_identifier(name)
        self._name = name
        BaseALObject.__init__(self)
        DocumentLevelObject.__init__(self, url)
        MemberContainerObject.__init__(self)
        # =====================================================================
        # Create the structures unique to MultiDynamics
        # =====================================================================
        if isinstance(sub_components, dict):
            self._sub_components = dict(
                (name, SubDynamics(name, dyn))
                for name, dyn in sub_components.iteritems())
        else:
            self._sub_components = dict((d.name, d) for d in sub_components)
        self._analog_port_connections = {}
        self._event_port_connections = {}
        self._reduce_port_connections = {}
        # Insert an empty list for each event and reduce port in the combined
        # model
        for sub_component in self.sub_components:
            self._event_port_connections.update(
                (sub_component.append_namespace(p.name),
                 LocalEventPortConnections(p.name, sub_component.name))
                for p in sub_component.component_class.event_send_ports)
            self._reduce_port_connections.update(
                (sub_component.append_namespace(p.name),
                 LocalReducePortConnections(p.name, sub_component.name))
                for p in sub_component.component_class.analog_reduce_ports)
        # Parse port connections (from tuples if required), bind them to the
        # ports within the subcomponents and append them to their respective
        # member dictionaries
        for port_connection in port_connections:
            if isinstance(port_connection, tuple):
                port_connection = BasePortConnection.from_tuple(
                    port_connection, self)
            port_connection.bind(self)
            snd_name = port_connection.sender.append_namespace(
                port_connection.send_port_name)
            rcv_name = port_connection.receiver.append_namespace(
                port_connection.receive_port_name)
            if isinstance(port_connection.receive_port, AnalogReceivePort):
                if rcv_name in self._analog_port_connections:
                    raise NineMLRuntimeError(
                        "Multiple connections to receive port '{}' in '{} "
                        "sub-component of '{}'"
                        .format(port_connection.receive_port_name,
                                port_connection.receiver_name, name))
                port_connection = LocalAnalogPortConnection(
                    port_connection)
                self._analog_port_connections[rcv_name] = port_connection
            elif isinstance(port_connection.receive_port, EventReceivePort):
                self._event_port_connections[snd_name].add(port_connection)
            elif isinstance(port_connection.receive_port, AnalogReducePort):
                self._reduce_port_connections[rcv_name].add(port_connection)
            else:
                raise NineMLRuntimeError(
                    "Unrecognised port connection type '{}'"
                    .format(port_connection))
        # =====================================================================
        # Create the structures required for the Dynamics base class
        # =====================================================================
        # Create multi-regimes for each combination of regimes
        # from across all the sub components
        regime_combins = product(*[sc.regimes for sc in self.sub_components])
        multi_regimes = (MultiRegime(dict(zip(self.sub_component_names, rc)))
                         for rc in regime_combins)
        self._regimes = dict((mr.name, mr) for mr in multi_regimes)
        # =====================================================================
        # Save port exposurs into separate member dictionaries
        # =====================================================================
        self._analog_send_port_exposures = {}
        self._analog_receive_port_exposures = {}
        self._analog_reduce_port_exposures = {}
        self._event_send_port_exposures = {}
        self._event_receive_port_exposures = {}
        if port_exposures is not None:
            for exposure in port_exposures:
                if isinstance(exposure, tuple):
                    exposure = BasePortExposure.from_tuple(exposure, self)
                exposure.bind(self)
                if isinstance(exposure, AnalogSendPortExposure):
                    self._analog_send_port_exposures[exposure.name] = exposure
                elif isinstance(exposure, AnalogReceivePortExposure):
                    self._analog_receive_port_exposures[
                        exposure.name] = exposure
                elif isinstance(exposure, AnalogReducePortExposure):
                    self._analog_reduce_port_exposures[
                        exposure.name] = exposure
                elif isinstance(exposure, EventSendPortExposure):
                    self._event_send_port_exposures[exposure.name] = exposure
                elif isinstance(exposure, EventSendPortExposure):
                    self._event_receive_port_exposures[
                        exposure.name] = exposure
                else:
                    raise NineMLRuntimeError(
                        "Unrecognised port exposure '{}'".format(exposure))
        self.annotations[NINEML][VALIDATE_DIMENSIONS] = validate_dimensions
        self.validate()

    def __getitem__(self, name):
        return self.sub_component(name)

    @property
    def sub_components(self):
        return self._sub_components.itervalues()

    @property
    def sub_component_names(self):
        return self._sub_components.iterkeys()

    @property
    def num_sub_components(self):
        return len(self._sub_components)

    @property
    def analog_port_connections(self):
        return self._analog_port_connections.itervalues()

    @property
    def event_port_connections(self):
        return self._analog_port_connections.itervalues()

    @property
    def reduce_port_connections(self):
        return self._reduce_port_connections.itervalues()

    @property
    def port_connections(self):
        return chain(self.analog_port_connections, self.event_port_connections,
                     self.reduce_port_connections)

    def sub_component(self, name):
        return self._sub_components[name]

    # =========================================================================
    # Dynamics members properties and accessors
    # =========================================================================

    @property
    def parameters(self):
        return chain(*[sc.parameters for sc in self.sub_components])

    @property
    def aliases(self):
        return chain(self.analog_port_connections,
                     self.reduce_port_connections,
                     *[sc.aliases for sc in self.sub_components])

    @property
    def constants(self):
        return chain(*[sc.constants for sc in self.sub_components])

    @property
    def state_variables(self):
        return chain(*[(StateVariable(sc, sv) for sv in sc.state_variables)
                       for sc in self.sub_components])

    @property
    def analog_send_ports(self):
        """Returns an iterator over the local |AnalogSendPort| objects"""
        return self._analog_send_port_exposures.itervalues()

    @property
    def analog_receive_ports(self):
        """Returns an iterator over the local |AnalogReceivePort| objects"""
        return self._analog_receive_port_exposures.itervalues()

    @property
    def analog_reduce_ports(self):
        """Returns an iterator over the local |AnalogReducePort| objects"""
        return self._analog_reduce_port_exposures.itervalues()

    @property
    def event_send_ports(self):
        """Returns an iterator over the local |EventSendPort| objects"""
        return self._event_send_port_exposures.itervalues()

    @property
    def event_receive_ports(self):
        """Returns an iterator over the local |EventReceivePort| objects"""
        return self._event_receive_port_exposures.itervalues()

    @property
    def parameter_names(self):
        return (p.name for p in self.parameters)

    @property
    def alias_names(self):
        return (a.name for a in self.aliases)

    @property
    def constant_names(self):
        return (c.name for c in self.constants)

    @property
    def state_variable_names(self):
        return (sv.name for sv in self.state_variables)

    @property
    def analog_send_port_names(self):
        """Returns an iterator over the local |AnalogSendPort| names"""
        return self._analog_send_port_exposures.iterkeys()

    @property
    def analog_receive_port_names(self):
        """Returns an iterator over the local |AnalogReceivePort| names"""
        return self._analog_receive_port_exposures.iterkeys()

    @property
    def analog_reduce_port_names(self):
        """Returns an iterator over the local |AnalogReducePort| names"""
        return self._analog_reduce_port_exposures.iterkeys()

    @property
    def event_send_port_names(self):
        """Returns an iterator over the local |EventSendPort| names"""
        return self._event_send_port_exposures.iterkeys()

    @property
    def event_receive_port_names(self):
        """Returns an iterator over the local |EventReceivePort| names"""
        return self._event_receive_port_exposures.iterkeys()

    def parameter(self, name):
        name, comp_name = self.split_namespace(name)
        return self.sub_component(comp_name).component_class.parameter(name)

    def state_variable(self, name):
        name, comp_name = self.split_namespace(name)
        component_class = self.sub_component(comp_name).component_class
        return component_class.state_variable(name)

    def alias(self, name):
        try:
            alias = self._analog_port_connections[name]
        except KeyError:
            try:
                alias = self._reduce_port_connections[name]
            except KeyError:
                name, comp_name = self.split_namespace(name)
                component_class = self.sub_component(comp_name).component_class
                alias = component_class.alias(name)
        return alias

    def constant(self, name):
        name, comp_name = self.split_namespace(name)
        return self.sub_component(comp_name).component_class.constant(name)

    def analog_send_port(self, name):
        return self._analog_send_port_exposures[name]

    def analog_receive_port(self, name):
        return self._analog_receive_port_exposures[name]

    def analog_reduce_port(self, name):
        return self._analog_reduce_port_exposures[name]

    def event_send_port(self, name):
        return self._event_send_port_exposures[name]

    def event_receive_port(self, name):
        return self._event_receive_port_exposures[name]

    @property
    def num_parameters(self):
        return len(list(self.parameters))

    @property
    def num_aliases(self):
        return len(list(self.aliases))

    @property
    def num_constants(self):
        return len(list(self.constants))

    @property
    def num_state_variables(self):
        return len(list(self.state_variables))

    @property
    def num_analog_send_ports(self):
        """Returns an iterator over the local |AnalogSendPort| objects"""
        return len(self._analog_send_port_exposures)

    @property
    def num_analog_receive_ports(self):
        """Returns an iterator over the local |AnalogReceivePort| objects"""
        return len(self._analog_receive_port_exposures)

    @property
    def num_analog_reduce_ports(self):
        """Returns an iterator over the local |AnalogReducePort| objects"""
        return len(self._analog_reduce_port_exposures)

    @property
    def num_event_send_ports(self):
        """Returns an iterator over the local |EventSendPort| objects"""
        return len(self._event_send_port_exposures)

    @property
    def num_event_receive_ports(self):
        """Returns an iterator over the local |EventReceivePort| objects"""
        return len(self._event_receive_port_exposures)

    def lookup_member_dict(self, element):
        """
        Looks up the appropriate member dictionary for objects of type element
        """
        dct_name = self.lookup_member_dict_name(element)
        comp_name = self.split_namespace(element._name)[1]
        return getattr(self.sub_component[comp_name], dct_name)

    @property
    def all_member_dicts(self):
        return chain(
            *[(getattr(sc.component, n)
               for n in sc.component.class_to_member_dict.itervalues())
              for sc in self.sub_components])

    @classmethod
    def split_namespace(cls, full_name):
        parts = double_underscore_re.split(full_name)
        name = '__'.join(parts[:-1])
        comp_name = parts[-1]
        comp_name = more_than_double_underscore_re.sub('_', comp_name)
        return name, comp_name


class SubDynamics(object):

    def __init__(self, name, component_class):
        self._name = name
        self._component_class = component_class

    @property
    def name(self):
        return self._name

    def append_namespace(self, name):
        """
        The suffix appended to names within the sub-component to distinguish
        them in the global namespace
        """
        # Since double underscores are used to delimit namespaces from names
        # within the namesapace (and 9ML names are not allowed to start or end
        # in underscores) we append an underscore to each multiple underscore
        # to avoid clash with the delimeter in the suffix
        return (name + '__' +
                multiple_underscore_re.sub(r'/1/2_/3', self.name))

    @property
    def component_class(self):
        return self._component_class

    @property
    def parameters(self):
        return (NamespaceParameter(self, p)
                for p in self.component_class.parameters)

    @property
    def aliases(self):
        return (NamespaceAlias(self, a) for a in self.component_class.aliases)

    @property
    def state_variables(self):
        return (NamespaceStateVariable(self, v)
                for v in self.component.state_variables)

    @property
    def constants(self):
        return (NamespaceConstant(self, p)
                for p in self.component_class.constants)

    @property
    def regimes(self):
        return (NamespaceRegime(self, r)
                for r in self.component_class.regimes)


# =============================================================================
# Namespace wrapper objects, which append namespaces to their names and
# expressions
# =============================================================================


class MultiRegime(Regime):

    def __init__(self, sub_regimes_dict):
        """
        `sub_regimes_dict` -- a dictionary containing the sub_regimes and
                              referenced by the names of the sub_components
                              they respond to
        """
        self._sub_regimes = copy(sub_regimes_dict)

    @property
    def sub_regimes(self):
        return self._sub_regimes.itervalues()

    @property
    def sub_component_names(self):
        return self._sub_regimes.iterkeys()

    @property
    def num_sub_regimes(self):
        return len(self._sub_regimes)

    def sub_regime(self, sub_component_name):
        return self._sub_regimes[sub_component_name]

    @property
    def name(self):
        return '__'.join(r.name for r in self.sub_regimes) + '__regime'

    def lookup_member_dict(self, element):
        """
        Looks up the appropriate member dictionary for objects of type element
        """
        dct_name = self.lookup_member_dict_name(element)
        comp_name = MultiDynamics.split_namespace(element._name)[1]
        return getattr(self.sub_regime(comp_name), dct_name)

    @property
    def all_member_dicts(self):
        return chain(*[
            (getattr(r, n) for n in r.class_to_member_dict.itervalues())
            for r in self.sub_regimes])

    # Member Properties:
    # ------------------

    @property
    def time_derivatives(self):
        return chain(*[r.time_derivatives for r in self.sub_regimes])

    @property
    def aliases(self):
        return chain(*[r.aliases for r in self.sub_regimes])

    @property
    def on_events(self):
        raise NotImplementedError

    @property
    def on_conditions(self):
        raise NotImplementedError

    def time_derivative(self, variable):
        name, comp_name = self.split_namespace(variable)
        return self.sub_regime(comp_name).time_derivative(name)

    def alias(self, name):
        name, comp_name = self.split_namespace(name)
        return self.sub_regime(comp_name).alias(name)

    def on_event(self, port_name):
        raise NotImplementedError

    def on_condition(self, condition):
        raise NotImplementedError

    @property
    def time_derivative_variables(self):
        return (td.variable for td in self.time_derivatives)

    @property
    def alias_names(self):
        return (a.name for a in self.aliases)

    @property
    def on_event_port_names(self):
        return (oe.src_port_name for oe in self.on_events)

    @property
    def on_condition_triggers(self):
        return (oc.trigger for oc in self.on_conditions)

    @property
    def num_time_derivatives(self):
        return len(list(self.time_derivatives))

    @property
    def num_on_events(self):
        return len(list(self.on_events))

    @property
    def num_on_conditions(self):
        return len(list(self.on_conditions))

    @property
    def num_aliases(self):
        return len(list(self.aliases))


class MultiTransition(object):
    pass
