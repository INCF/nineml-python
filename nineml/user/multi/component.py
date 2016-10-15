from itertools import chain
from copy import copy
from .. import BaseULObject
import sympy
import operator
from itertools import product, groupby, izip
from nineml.reference import resolve_reference, write_reference
from nineml.base import DocumentLevelObject
from nineml.xml import (
    nineml_ns, E, from_child_xml, unprocessed_xml, get_xml_attr)
from nineml.user import DynamicsProperties, Definition
from nineml.annotations import annotate_xml, read_annotations
from nineml.abstraction.dynamics.visitors.cloner import DynamicsCloner
from nineml.exceptions import (
    NineMLRuntimeError, NineMLNameError, name_error)
from ..port_connections import (
    AnalogPortConnection, EventPortConnection, BasePortConnection)
from nineml.abstraction import BaseALObject
from nineml.base import ContainerObject
from nineml.utils import ensure_valid_identifier, normalise_parameter_as_list
from nineml import units as un
from nineml.annotations import VALIDATE_DIMENSIONS
from nineml.abstraction import (
    Dynamics, Regime, AnalogReceivePort, EventReceivePort,
    StateVariable, OnEvent, OnCondition, OutputEvent, StateAssignment,
    Trigger, Constant)
from .port_exposures import (
    EventReceivePortExposure, EventSendPortExposure, AnalogReducePortExposure,
    AnalogReceivePortExposure, AnalogSendPortExposure, BasePortExposure,
    _LocalAnalogPortConnections)
from .namespace import (
    _NamespaceAlias, _NamespaceRegime, _NamespaceStateVariable,
    _NamespaceConstant, _NamespaceParameter, _NamespaceProperty,
    _NamespaceOnCondition, append_namespace, split_namespace, make_regime_name,
    make_delay_trigger_name, split_multi_regime_name)


class MultiDynamicsProperties(DynamicsProperties):

    nineml_type = "MultiDynamicsProperties"
    defining_attributes = ('name', 'definition', '_sub_components')
    class_to_member = {'SubDynamicsProperties': 'sub_component'}

    def __init__(self, name, sub_components, port_connections=[],
                 port_exposures=[], document=None, check_initial_values=False):
        # Initiate inherited base classes
        BaseULObject.__init__(self)
        DocumentLevelObject.__init__(self, document)
        ContainerObject.__init__(self)
        # Extract abstraction layer component of sub-dynamics object (won't be
        # necessary from v2) and convert dict of name: DynamicsProperties pairs
        # into SubDynamics objects
        if isinstance(sub_components, dict):
            sub_components = [
                SubDynamicsProperties(n, p)
                for n, p in sub_components.iteritems()]
        self._name = name
        self._sub_components = dict(
            (p.name, p) for p in sub_components)
        self._definition = self._extract_definition(
            sub_components, port_exposures, port_connections)
        # Check for property/parameter matches
        self.check_properties()
        if check_initial_values:
            self.check_initial_values()

    def _extract_definition(self, sub_components, port_exposures,
                            port_connections):
        sub_dynamics = [
            SubDynamics(sc.name, sc.component.component_class)
            for sc in sub_components]
        # Construct component class definition
        return Definition(MultiDynamics(
            self.name + '_Dynamics', sub_dynamics,
            port_exposures=port_exposures,
            port_connections=port_connections))

    @property
    def name(self):
        return self._name

    @property
    def sub_components(self):
        return self._sub_components.itervalues()

    @property
    def port_exposures(self):
        return self.component_class.ports

    @property
    def port_connections(self):
        return self.component_class.port_connections

    @name_error
    def sub_component(self, name):
        return self._sub_components[name]

    @name_error
    def port_exposure(self, name):
        return self.component_class.port(name)

    @name_error
    def port_connection(self, name):
        return self.component_class.port_connection(name)

    @property
    def sub_component_names(self):
        return self._sub_components.iterkeys()

    @property
    def port_exposure_names(self):
        return self.component_class.port_exposure_names

    @property
    def attributes_with_units(self):
        return chain(*[c.attributes_with_units
                       for c in self.sub_components])

    @write_reference
    @annotate_xml
    def to_xml(self, document, E=E, **kwargs):
        members = [c.to_xml(document, E=E, **kwargs)
                   for c in self.sub_components]
        members.extend(pe.to_xml(document, E=E, **kwargs)
                        for pe in self.port_exposures)
        members.extend(pc.to_xml(document, E=E, **kwargs)
                       for pc in self.port_connections)
        return E(self.nineml_type, *members, name=self.name)

    @classmethod
    @resolve_reference
    @read_annotations
    @unprocessed_xml
    def from_xml(cls, element, document, **kwargs):
        sub_component_properties = from_child_xml(
            element, SubDynamicsProperties, document, multiple=True,
            **kwargs)
        port_exposures = from_child_xml(
            element,
            (AnalogSendPortExposure, AnalogReceivePortExposure,
             AnalogReducePortExposure, EventSendPortExposure,
             EventReceivePortExposure), document, multiple=True,
            allow_none=True, **kwargs)
        port_connections = from_child_xml(
            element,
            (AnalogPortConnection, EventPortConnection), document,
            multiple=True, allow_none=True, **kwargs)
        return cls(name=get_xml_attr(element, 'name', document, **kwargs),
                   sub_components=sub_component_properties,
                   port_exposures=port_exposures,
                   port_connections=port_connections)

    @property
    def initial_values(self):
        return chain(*(sc.initial_values for sc in self.sub_components))

    @name_error
    def initial_value(self, name):
        _, comp_name = split_namespace(name)
        return self.sub_component(comp_name).initial_value(name)

    @property
    def initial_value_names(self):
        return (iv.name for iv in self.initial_values)

    @property
    def num_initial_values(self):
        return len(list(self.initial_values))

    @property
    def properties(self):
        """
        The set of component_class properties (parameter values).
        """
        return chain(*(sc.properties for sc in self.sub_components))

    @property
    def property_names(self):
        return (p.name for p in self.properties)

    @property
    def num_properties(self):
        return len(list(self.properties))

    # Property is declared last so as not to overwrite the 'property' decorator

    @name_error
    def property(self, name):
        _, comp_name = split_namespace(name)
        return self.sub_component(comp_name).property(name)


class SubDynamicsProperties(BaseULObject):

    nineml_type = 'SubDynamicsProperties'
    defining_attributes = ('_name', '_component')

    def __init__(self, name, component):
        BaseULObject.__init__(self)
        self._name = name
        self._component = component

    def __repr__(self):
        return "SubDynamics(name={}, component={})".format(self.name,
                                                           self.component)

    @property
    def name(self):
        return self._name

    @property
    def component(self):
        return self._component

    def __iter__(self):
        return self.properties

    def append_namespace(self, name):
        return append_namespace(name, self.name)

    @property
    def attributes_with_units(self):
        return set(p for p in self.properties if p.units is not None)

    @annotate_xml
    def to_xml(self, document, E=E, **kwargs):  # @UnusedVariable
        return E(self.nineml_type,
                 self._component.to_xml(document, E=E, **kwargs),
                 name=self.name)

    @classmethod
    @resolve_reference
    @read_annotations
    @unprocessed_xml
    def from_xml(cls, element, document, **kwargs):
        dynamics_properties = from_child_xml(
            element, (DynamicsProperties, MultiDynamicsProperties), document,
            allow_reference=True, **kwargs)
        return cls(get_xml_attr(element, 'name', document, **kwargs),
                   dynamics_properties)

    @property
    def initial_values(self):
        return (_NamespaceProperty(self, iv)
                for iv in self._component.initial_values)

    @property
    def num_initial_values(self):
        return len(list(self.initial_values))

    @property
    def initial_value_names(self):
        return (iv.name for iv in self.initial_values)

    @name_error
    def initial_value(self, name):
        local_name, comp_name = split_namespace(name)
        if comp_name != self.name:
            raise KeyError(name)
        return self._component.initial_value(local_name)

    @property
    def properties(self):
        return (_NamespaceProperty(self, p)
                for p in self._component.properties)

    @property
    def num_properties(self):
        return len(list(self.properties))

    @property
    def property_names(self):
        return (p.name for p in self.properties)

    @name_error
    def property(self, name):
        local_name, comp_name = split_namespace(name)
        if comp_name != self.name:
            raise KeyError(name)
        return self._component.property(local_name)


class SubDynamics(BaseULObject):

    nineml_type = 'SubDynamics'
    defining_attributes = ('_name', '_component_class')

    def __init__(self, name, component_class):
        assert isinstance(name, basestring)
        assert isinstance(component_class, Dynamics)
        self._name = name
        self._component_class = component_class

    @property
    def name(self):
        return self._name

    def append_namespace(self, name):
        return append_namespace(name, self.name)

    @property
    def component_class(self):
        return self._component_class

    @property
    def parameters(self):
        return (_NamespaceParameter(self, p, self)
                for p in self.component_class.parameters)

    @property
    def aliases(self):
        return (_NamespaceAlias(self, a, self)
                for a in self.component_class.aliases)

    @property
    def state_variables(self):
        return (_NamespaceStateVariable(self, v, self)
                for v in self.component_class.state_variables)

    @property
    def constants(self):
        return (_NamespaceConstant(self, p, self)
                for p in self.component_class.constants)

    @property
    def regimes(self):
            return (_NamespaceRegime(self, r, self)
                    for r in self.component_class.regimes)

    @name_error
    def parameter(self, name):
        elem_name, _ = split_namespace(name)
        return _NamespaceParameter(
            self, self.component_class.parameter(elem_name), self)

    @name_error
    def alias(self, name):
        elem_name, _ = split_namespace(name)
        return _NamespaceAlias(self, self.component_class.alias(elem_name),
                               self)

    @name_error
    def state_variable(self, variable):
        elem_name, _ = split_namespace(variable)
        return _NamespaceStateVariable(
            self, self.component_class.state_variable(elem_name), self)

    @name_error
    def constant(self, name):
        elem_name, _ = split_namespace(name)
        return _NamespaceConstant(self,
                                  self.component_class.constant(elem_name),
                                  self)

    @name_error
    def regime(self, name):
        elem_name, _ = split_namespace(name)
        return _NamespaceRegime(self, self.component_class.regime(elem_name),
                                self)

    @property
    def num_parameters(self):
        return len(list(self.component_class.parameters))

    @property
    def num_aliases(self):
        return len(list(self.component_class.aliases))

    @property
    def num_state_variables(self):
        return len(list(self.component_class.state_variables))

    @property
    def num_constants(self):
        return len(list(self.component_class.constants))

    @property
    def num_regimes(self):
        return len(list(self.component_class.regimes))

    @property
    def parameter_names(self):
        return (p.name for p in self.parameters)

    @property
    def alias_names(self):
        return (p.name for p in self.aliases)

    @property
    def state_variable_names(self):
        return (p.name for p in self.state_variables)

    @property
    def constant_names(self):
        return (p.name for p in self.constants)

    @property
    def regime_names(self):
        return (p.name for p in self.regimes)

    @name_error
    def port(self, name):
        return self.component_class.port(name)

    @property
    def ports(self):
        return self.component_class.ports

    @property
    def port_names(self):
        return self.component_class.port_names

    @property
    def num_ports(self):
        return self.component_class.num_ports

    @name_error
    def receive_port(self, name):
        return self.component_class.receive_port(name)

    @property
    def receive_ports(self):
        return self.component_class.receive_ports

    @property
    def receive_port_names(self):
        return self.component_class.receive_port_names

    @property
    def num_receive_ports(self):
        return self.component_class.num_receive_ports

    def send_port(self, name):
        return self.component_class.send_port(name)

    @property
    def send_ports(self):
        return self.component_class.send_ports

    @property
    def send_port_names(self):
        return self.component_class.send_port_names

    @property
    def num_send_ports(self):
        return self.component_class.num_send_ports

    @name_error
    def analog_receive_port(self, name):
        return self.component_class.analog_receive_port(name)

    @property
    def analog_receive_ports(self):
        return self.component_class.analog_receive_ports

    @property
    def analog_receive_port_names(self):
        return self.component_class.analog_receive_port_names

    @property
    def num_analog_receive_ports(self):
        return self.component_class.num_analog_receive_ports

    def analog_send_port(self, name):
        return self.component_class.analog_send_port(name)

    @property
    def analog_send_ports(self):
        return self.component_class.analog_send_ports

    @property
    def analog_send_port_names(self):
        return self.component_class.analog_send_port_names

    @property
    def num_analog_send_ports(self):
        return self.component_class.num_analog_send_ports

    @name_error
    def analog_reduce_port(self, name):
        return self.component_class.analog_reduce_port(name)

    @property
    def analog_reduce_ports(self):
        return self.component_class.analog_reduce_ports

    @property
    def analog_reduce_port_names(self):
        return self.component_class.analog_reduce_port_names

    @property
    def num_analog_reduce_ports(self):
        return self.component_class.num_analog_reduce_ports

    @name_error
    def event_receive_port(self, name):
        return self.component_class.event_receive_port(name)

    @property
    def event_receive_ports(self):
        return self.component_class.event_receive_ports

    @property
    def event_receive_port_names(self):
        return self.component_class.event_receive_port_names

    @property
    def num_event_receive_ports(self):
        return self.component_class.num_event_receive_ports

    @name_error
    def event_send_port(self, name):
        return self.component_class.event_send_port(name)

    @property
    def event_send_ports(self):
        return self.component_class.event_send_ports

    @property
    def event_send_port_names(self):
        return self.component_class.event_send_port_names


class MultiDynamics(Dynamics):

    nineml_type = 'MultiDynamics'
    defining_attributes = (
        '_name', '_sub_components', '_analog_port_connections',
        '_event_port_connections', '_analog_send_ports',
        '_analog_receive_ports', '_analog_reduce_ports', '_event_send_ports',
        '_event_receive_ports')
    class_to_member = {
        'SubDynamics': 'sub_component',
        'AnalogPortConnection': 'analog_port_connection',
        'EventPortConnection': 'event_port_connection',
        'AnalogSendPortExposure': 'analog_send_port',
        'AnalogReceivePortExposure': 'analog_receive_port',
        'AnalogReducePortExposure': 'analog_reduce_port',
        'EventSendPortExposure': 'event_send_port',
        'EventReceivePortExposure': 'event_receive_port'}
    core_type = Dynamics

    def __init__(self, name, sub_components, port_connections=[],
                 port_exposures=[], document=None, validate_dimensions=True,
                 **kwargs):
        ensure_valid_identifier(name)
        self._name = name
        BaseALObject.__init__(self)
        DocumentLevelObject.__init__(self, document)
        ContainerObject.__init__(self)
        # =====================================================================
        # Create the structures unique to MultiDynamics
        # =====================================================================
        if isinstance(sub_components, dict):
            self._sub_components = dict(
                (name, SubDynamics(name, dyn))
                for name, dyn in sub_components.iteritems())
        else:
            self._sub_components = dict((d.name, d) for d in sub_components)
        self._analog_send_ports = {}
        self._analog_receive_ports = {}
        self._analog_reduce_ports = {}
        self._event_send_ports = {}
        self._event_receive_ports = {}
        self._analog_port_connections = {}
        self._event_port_connections = {}
        # =====================================================================
        # Save port exposurs into separate member dictionaries
        # =====================================================================
        for exposure in port_exposures:
            if isinstance(exposure, tuple):
                exposure = BasePortExposure.from_tuple(exposure, self)
            exposure.bind(self)
            if isinstance(exposure, AnalogSendPortExposure):
                self._analog_send_ports[exposure.name] = exposure
            elif isinstance(exposure, AnalogReceivePortExposure):
                self._analog_receive_ports[
                    exposure.name] = exposure
            elif isinstance(exposure, AnalogReducePortExposure):
                self._analog_reduce_ports[
                    exposure.name] = exposure
            elif isinstance(exposure, EventSendPortExposure):
                self._event_send_ports[exposure.name] = exposure
            elif isinstance(exposure, EventReceivePortExposure):
                self._event_receive_ports[
                    exposure.name] = exposure
            else:
                raise NineMLRuntimeError(
                    "Unrecognised port exposure '{}'".format(exposure))
        # =====================================================================
        # Set port connections
        # =====================================================================
        # Parse port connections (from tuples if required), bind them to the
        # ports within the subcomponents and append them to their respective
        # member dictionaries
        for port_connection in port_connections:
            if isinstance(port_connection, tuple):
                port_connection = BasePortConnection.from_tuple(
                    port_connection, self)
            port_connection.bind(self)
            snd_key = (port_connection.sender_name,
                       port_connection.send_port_name)
            rcv_key = (port_connection.receiver_name,
                       port_connection.receive_port_name)
            if isinstance(port_connection.receive_port, EventReceivePort):
                if snd_key not in self._event_port_connections:
                    self._event_port_connections[snd_key] = {}
                self._event_port_connections[
                    snd_key][rcv_key] = port_connection
            else:
                if rcv_key not in self._analog_port_connections:
                    self._analog_port_connections[rcv_key] = {}
                elif isinstance(port_connection.receive_port,
                                 AnalogReceivePort):
                    raise NineMLRuntimeError(
                        "Multiple connections to receive port '{}' in '{} "
                        "sub-component of '{}'"
                        .format(port_connection.receive_port_name,
                                port_connection.receiver_name, name))
                self._analog_port_connections[
                    rcv_key][snd_key] = port_connection
        self.annotations[nineml_ns][VALIDATE_DIMENSIONS] = validate_dimensions
        self.validate(**kwargs)

    def __getitem__(self, comp_name):
        return self._sub_components[comp_name]

    def flatten(self):
        return DynamicsCloner().visit(self)

    def __repr__(self):
        return "<multi.MultiDynamics {}>".format(self.name)

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
        return chain(*(d.itervalues()
                       for d in self._analog_port_connections.itervalues()))

    @property
    def event_port_connections(self):
        return chain(*(d.itervalues()
                       for d in self._event_port_connections.itervalues()))

    @property
    def zero_delay_event_port_connections(self):
        return (pc for pc in self.event_port_connections if pc.delay == 0.0)

    @property
    def nonzero_delay_event_port_connections(self):
        return (pc for pc in self.event_port_connections if pc.delay != 0.0)

    @property
    def port_connections(self):
        return chain(self.analog_port_connections, self.event_port_connections)

    # =========================================================================
    # Dynamics members properties and accessors
    # =========================================================================

    @property
    def parameters(self):
        return chain(*[sc.parameters for sc in self.sub_components])

    @property
    def aliases(self):
        """
        Chains port connections to analog receive and reduce ports, which
        are treated simply as aliases in the flattened representation, with
        all aliases defined in the sub components
        """
        return chain(
            (p.alias for p in chain(self.analog_send_ports,
                                    self.analog_receive_ports,
                                    self.analog_reduce_ports)
             if p.name != p.local_port_name),
            (_LocalAnalogPortConnections(
                receive_port=rcv[1], receiver=rcv[0],
                port_connections=snd_dct.values(), parent=self)
             for rcv, snd_dct in self._analog_port_connections.iteritems()),
            *(sc.aliases for sc in self.sub_components))

    @property
    def constants(self):
        # We need to insert a 0-valued constant for each internal reduce port
        # that doesn't receive any connections
        unused_reduce_ports = []
        for sub_comp in self.sub_components:
            for port in sub_comp.analog_reduce_ports:
                if (((sub_comp.name, port.name) not in
                     self._analog_port_connections) and
                    (append_namespace(port.name, sub_comp.name) not in
                     pe.local_port_name for pe in self.analog_reduce_ports)):
                    unused_reduce_ports.append(
                        Constant(append_namespace(port.name, sub_comp.name),
                                 0.0, port.dimension.origin.units))
        return chain(unused_reduce_ports,
                     *[sc.constants for sc in self.sub_components])

    @property
    def state_variables(self):
        # All statevariables in all subcomponents mapped into the container
        # namespace, plus state variables used to trigger local event
        # connections after a delays
        return chain((StateVariable(make_delay_trigger_name(pc),
                                    dimension=un.time)
                      for pc in self.nonzero_delay_event_port_connections),
                     *(sc.state_variables for sc in self.sub_components))

    @property
    def regimes(self):
        # Create multi-regimes for each combination of regimes across the
        # sub components
        combinations = product(*[sc.regimes for sc in self.sub_components])
        return (self._create_multi_regime(comb) for comb in combinations)

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
    def regime_names(self):
        return (r.name for r in self.regimes)

    @property
    def analog_port_connection_names(self):
        return chain(*(d.iterkeys()
                       for d in self._analog_port_connections.itervalues()))

    @property
    def event_port_connection_names(self):
        return chain(*(d.iterkeys()
                       for d in self._event_port_connections.itervalues()))

    @name_error
    def sub_component(self, name):
        return self._sub_components[name]

    def analog_port_connection(self, name):
        try:
            sender, send_port, receiver, receive_port = name.split('___')
        except ValueError:
            raise NineMLNameError(
                "Name provided to analog_port_connection '{}' was not a "
                "4-tuple of (sender, send_port, receiver, receive_port)")
        return self._analog_port_connections[
            (receiver, receive_port)][(sender, send_port)]

    def event_port_connection(self, name):
        try:
            sender, send_port, receiver, receive_port = name.split('___')
        except ValueError:
            raise NineMLNameError(
                "Name provided to analog_port_connection '{}' was not a "
                "4-tuple of (sender, send_port, receiver, receive_port)")
        return self._event_port_connections[
            (sender, send_port)][(receiver, receive_port)]

    def parameter(self, name):
        _, comp_name = split_namespace(name)
        return self.sub_component(comp_name).parameter(name)

    def state_variable(self, name):
        _, comp_name = split_namespace(name)
        return self.sub_component(comp_name).state_variable(name)

    def alias(self, name):
        try:
            local, comp_name = split_namespace(name)
            try:
                # An alias that is actually a local analog port connection
                alias = _LocalAnalogPortConnections(
                    name, comp_name,
                    self._analog_port_connections[(comp_name, local)].values(),
                    self)
            except KeyError:
                # An alias of a sub component
                alias = self.sub_component(comp_name).alias(name)
        except KeyError:
            try:
                alias = self.analog_send_port(name).alias
            except KeyError:
                try:
                    alias = next(p.alias
                                 for p in chain(self.analog_receive_ports,
                                                self.analog_reduce_ports)
                                 if p.alias.lhs == name)
                except StopIteration:
                    raise NineMLNameError(
                        "Could not find alias corresponding to '{}' in "
                        "sub-components or port connections/exposures"
                        .format(name))
        return alias

    def constant(self, name):
        port_name, comp_name = split_namespace(name)
        sub_component = self.sub_component(comp_name)
        try:
            return sub_component.constant(name)
        except NineMLNameError:
            try:
                reduce_port = sub_component.analog_reduce_port(port_name)
                if (comp_name, port_name) not in self._analog_port_connections:
                    return Constant(name, 0.0,
                                    reduce_port.dimension.origin.units)
                else:
                    raise NineMLNameError(
                        "'{}' corresponds to a AnalogReduce port, but one that"
                        "is used and so is represented by an Alias instead of"
                        "a Constant in '{}'".format(port_name, comp_name))
            except NineMLNameError:
                raise NineMLNameError(
                    "Could not find Constant '{}' in '{}"
                    .format(name, self.name))

    def regime(self, name):
        try:
            sub_regime_names = split_multi_regime_name(name)
        except TypeError:
            sub_regime_names = name  # Assume it is already an iterable
        if len(sub_regime_names) != len(self._sub_component_keys):
            raise NineMLNameError(
                "The number of regime names extracted from '{}' ({}) does not "
                "match the number of sub-components ('{}'). NB: the format for"
                " multi-regimes is '___' delimited list of regime names sorted"
                " by sub-component names)".format(
                    name, len(sub_regime_names),
                    "', '".join(self._sub_component_keys)))
        return self._create_multi_regime(
            self.sub_component(sc_n).regime(append_namespace(r_n, sc_n))
            for sc_n, r_n in izip(self._sub_component_keys, sub_regime_names))

    def analog_receive_port_exposure(self, exposed_port_name):
        port_name, comp_name = split_namespace(exposed_port_name)
        try:
            exposure = next(pe for pe in chain(self.analog_receive_ports,
                                               self.analog_reduce_ports)
                            if (pe.port_name == port_name and
                                pe.sub_component.name == comp_name))
        except StopIteration:
            raise NineMLNameError(
                "No port exposure that exposes '{}'".format(exposed_port_name))
        return exposure

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
    def num_regimes(self):
        return len(list(self.regimes))

    @property
    def num_state_variables(self):
        return len(list(self.state_variables))

    @property
    def num_analog_port_connections(self):
        return reduce(
            operator.add,
            (len(d) for d in self._analog_port_connections.itervalues()))

    @property
    def num_event_port_connections(self):
        return reduce(
            operator.add,
            (len(d) for d in self._event_port_connections.itervalues()))

    @property
    def _sub_component_keys(self):
        return sorted(self.sub_component_names)

    def _create_multi_regime(self, sub_regimes):
        return _MultiRegime(sub_regimes, self)

    def validate(self, **kwargs):
        exposed_ports = [pe.port for pe in self.analog_receive_ports]
        connected_ports = [pc.receive_port
                           for pc in self.analog_port_connections]
        for sub_component in self.sub_components:
            for port in sub_component.component_class.analog_receive_ports:
                if port not in chain(exposed_ports, connected_ports):
                    raise NineMLRuntimeError(
                        "Analog receive port '{}' in sub component '{}' was "
                        "not connected via a port-connection or exposed via a "
                        "port-exposure in MultiDynamics object '{}'"
                        .format(port.name, sub_component.name, self.name))
        super(MultiDynamics, self).validate(**kwargs)

# =============================================================================
# _Namespace wrapper objects, which append namespaces to their names and
# expressions
# =============================================================================


class _MultiRegime(Regime):

    def __init__(self, sub_regimes, parent):
        """
        `sub_regimes_dict` -- a dictionary containing the sub_regimes and
                              referenced by the names of the
                              sub_components they respond to
        `parent`           -- the MultiDynamics object that generates the
                              MultiRegime
        """
        BaseALObject.__init__(self)
        ContainerObject.__init__(self)
        self._sub_regimes = dict((r.sub_component.name, copy(r))
                                 for r in sub_regimes)
        # Set the parent of the sub regimes to the multi regime to get hashing
        # of the generated namespace objects to work (i.e. equivalent
        # namespace objects generated from the property generators of the same
        # MultiRegime will have the same hash values, but the equivalent object
        # in a different multi regime will have a different hash object
        for sub_regime in self.sub_regimes:
            sub_regime._parent = self
        self._parent = parent

    def __hash__(self):
        # Since a new MultiRegime will be created each time it is accessed from
        # a MultiDynamics object, in order to use MultiRegimes in sets or dicts
        # with equivalence between the same MultiRegime
        return hash(self.name) ^ hash(self._parent)

    @property
    def sub_regimes(self):
        return self._sub_regimes.itervalues()

    @property
    def sub_components(self):
        return self._sub_regimes.iterkeys()

    @property
    def num_sub_regimes(self):
        return len(self._sub_regimes)

    def sub_regime(self, sub_component):
        return self._sub_regimes[sub_component]

    @property
    def _name(self):
        return make_regime_name(self._sub_regimes)

    def lookup_member_dict(self, element):
        """
        Looks up the appropriate member dictionary for objects of type element
        """
        dct_name = self.lookup_members_name(element)
        comp_name = MultiDynamics.split_namespace(element._name)[1]
        return getattr(self.sub_regime(comp_name), dct_name)

    @property
    def all_member_dicts(self):
        return chain(*[
            (getattr(r, n) for n in r.class_to_member.itervalues())
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
        """
        All OnEvents in sub_regimes that are exposed via an event receive
        port exposure
        """
        list_of_args = []
        for port_exposure in self._parent.event_receive_ports:
            exposed_on_events = [
                oe for oe in self._all_sub_on_events
                if oe.src_port_name == port_exposure.local_port_name]
            if exposed_on_events:
                list_of_args.append((port_exposure, exposed_on_events))
        return (_MultiOnEvent(pe, oes, self) for pe, oes in list_of_args)

    @property
    def on_conditions(self):
        """
        All conditions across all sub-regimes sorted, grouped by their trigger
        and chained output-event -> on-events
        """
        # Group on conditions by their trigger condition and return as an
        # _MultiOnCondition
        all_on_conds = list(self._all_sub_on_conds)
        # Get all event connection ports that receive connections with non-zero
        # delay
        nonzero_delay_receive_ports = [
            pc.receive_port.name
            for pc in self._parent.nonzero_delay_event_port_connections]
        key = lambda oc: oc.trigger  # Group key for on conditions
        # Chain delayed on events and grouped on conditions
        return chain(
            (_MultiOnCondition((_DelayedOnEvent(oe),), self)
             for oe in self._all_sub_on_events
             if oe.src_port_name in nonzero_delay_receive_ports),
            (_MultiOnCondition(grp, self)
             for _, grp in groupby(sorted(all_on_conds, key=key), key=key)))

    def time_derivative(self, variable):
        name, comp_name = split_namespace(variable)
        return self.sub_regime(comp_name).time_derivative(name)

    def alias(self, name):
        name, comp_name = split_namespace(name)
        return self.sub_regime(comp_name).alias(name)

    def on_event(self, port_name):
        port_exposure = self._parent.event_receive_port(port_name)
        sub_on_events = [oe for oe in self._all_sub_on_events
                         if oe.src_port_name == port_exposure.local_port_name]
        if not sub_on_events:
            raise KeyError(
                "No OnEvent for receive port '{}'".format(port_name))
        return _MultiOnEvent(port_exposure, sub_on_events, self)

    def on_condition(self, condition):
        sub_conds = [oc for oc in self._all_sub_on_conds
                     if oc.trigger.rhs == sympy.sympify(condition)]
        if not sub_conds:
            raise KeyError(
                "No OnCondition with trigger condition '{}'".format(condition))
        return _MultiOnCondition(sub_conds, self)

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

    def daisy_chained_on_events(self, sub_on_events):
        """
        Yields a sub-OnEvent (i.e. an OnEvent in a sub-regime) along with
        all the other sub-OnEvents that are daisy-chained with it via event
        event port connections with zero delay.
        """
        sub_on_events = normalise_parameter_as_list(sub_on_events)
        for sub_on_event in sub_on_events:
            # Loop through all its output events and yield any daisy chained
            # events
            for output_event in sub_on_event.output_events:
                # Get all receive ports that are activated by this output event
                # i.e. all zero-delay event port connections that are linked to
                # this output_event
                try:
                    active_ports = set(
                        (pc.receiver_name, pc.receive_port_name)
                        for pc in self._parent._event_port_connections[
                            (output_event.sub_component.name,
                             output_event.relative_port_name)].itervalues()
                        if pc.delay == 0.0)
                except KeyError:
                    active_ports = []
                # Get all the OnEvent transitions that are connected to this
                for on_event in self._all_sub_on_events:
                    if (on_event.sub_component.name,
                            on_event.src_port_name) in active_ports:
                        yield on_event
                        for chained in self.daisy_chained_on_events(on_event):
                            yield chained

    @property
    def _all_sub_on_events(self):
        return chain(*[r.on_events for r in self.sub_regimes])

    @property
    def _all_sub_on_conds(self):
        return chain(*[r.on_conditions for r in self.sub_regimes])


class _MultiTransition(BaseALObject, ContainerObject):
    """
    Collects multiple simultaneous transitions into a single transition
    """

    def __init__(self, sub_transitions, parent):
        BaseALObject.__init__(self)
        ContainerObject.__init__(self)
        self._sub_transitions = dict(
            (st.sub_component.name, st) for st in sub_transitions)
        for chained_event in parent.daisy_chained_on_events(sub_transitions):
            namespace = chained_event.sub_component.name
            if namespace in self._sub_transitions:
                raise NineMLRuntimeError(
                    "Transition loop with non-zero delay found in on-event "
                    "chain beggining with {}".format(chained_event._name))
            self._sub_transitions[namespace] = chained_event
        self._parent = parent

    def __hash__(self):
        # Since a new MultiRegime will be created each time it is accessed from
        # a MultiDynamics object, in order to use MultiRegimes in sets or dicts
        # with equivalence between the same MultiRegime
        return (reduce(operator.xor,
                       (hash(st) for st in self.sub_transitions)) ^
                hash(self._parent))

    @property
    def target_regime(self):
        sub_regimes = copy(self._parent._sub_regimes)
        sub_regimes.update(
            (k, t.target_regime)
            for k, t in self._sub_transitions.iteritems())
        return self._parent._parent._create_multi_regime(
            sub_regimes.itervalues())

    @property
    def target_regime_name(self):
        sub_regime_names = copy(self._parent._sub_regimes)
        sub_regime_names.update(
            (k, t.target_regime) for k, t in self._sub_transitions.iteritems())
        return make_regime_name(sub_regime_names)

    @property
    def sub_transitions(self):
        return self._sub_transitions.itervalues()

    def sub_transition(self, sub_component):
        return next(t for t in self._sub_transitions
                    if t.sub_component is sub_component)

    @property
    def sub_transition_namespaces(self):
        return self._sub_transitions.iterkeys()

    @property
    def state_assignments(self):
        # All state assignments within the sub_transitions plus
        # state-assignments of delay triggers for output events connected to
        # local event port connections with non-zero delay
        return chain(
            (StateAssignment(make_delay_trigger_name(pc),
                             't + {}'.format(pc.delay))
             for pc in
                 self._parent._parent.nonzero_delay_event_port_connections
             if pc.port in self._sub_output_event_ports),
            *[t.state_assignments for t in self.sub_transitions])

    @property
    def output_events(self):
        # Return all output events that are exposed by port exposures
        return (
            _ExposedOutputEvent(pe)
            for pe in self._parent._parent.event_send_ports
            if pe.port in self._sub_output_event_ports)

    def state_assignment(self, variable):
        try:
            return next(sa for sa in self.state_assignments
                        if sa.variable == variable)
        except StopIteration:
            raise NineMLNameError(
                "No state assignment for variable '{}' found in transition"
                .format(variable))

    def output_event(self, name):
        exposure = self._parent._parent.event_send_port(name)
        if exposure.port not in self._sub_output_event_ports:
            raise NineMLNameError(
                "Output event for '{}' port is not present in transition"
                .format(name))
        return _ExposedOutputEvent(exposure)

    @property
    def num_state_assignments(self):
        return len(list(self.state_assignments))

    @property
    def num_output_events(self):
        return len(list(self.output_events))

    @property
    def state_assignment_variables(self):
        return (sa.variable for sa in self.state_assignments)

    @property
    def output_event_port_names(self):
        return (oe.port_name for oe in self.output_events)

    @property
    def _sub_output_event_ports(self):
        return set(oe.port for oe in chain(*[t.output_events
                                             for t in self.sub_transitions]))


class _MultiOnEvent(_MultiTransition, OnEvent):

    def __init__(self, port_exposure, sub_transitions, parent):
        sub_transitions = normalise_parameter_as_list(sub_transitions)
        self._port_exposure = port_exposure
        assert all(st.src_port_name == self._port_exposure.local_port_name
                   for st in sub_transitions)
        _MultiTransition.__init__(self, sub_transitions, parent)

    def __hash__(self):
        # Since a new MultiRegime will be created each time it is accessed from
        # a MultiDynamics object, in order to use MultiRegimes in sets or dicts
        # with equivalence between the same MultiRegime
        return hash(self.src_port_name) ^ hash(self._parent)

    def __repr__(self):
        return '_MultiOnEvent({})'.format(self.src_port_name)

    @property
    def src_port_name(self):
        return self._port_exposure.name

    @property
    def port(self):
        return self._port_exposure


class _MultiOnCondition(_MultiTransition, OnCondition):

    def __init__(self, sub_transitions, parent):
        sub_transitions = normalise_parameter_as_list(sub_transitions)
        self._trigger = sub_transitions[0].trigger
        assert all(st.trigger == self._trigger for st in sub_transitions[1:])
        _MultiTransition.__init__(self, sub_transitions, parent)

    def __repr__(self):
        return '_MultiOnCondition({})'.format(self.trigger.rhs)

    def __hash__(self):
        # Since a new MultiRegime will be created each time it is accessed from
        # a MultiDynamics object, in order to use MultiRegimes in sets or dicts
        # with equivalence between the same MultiRegime
        return hash(self.trigger.rhs) ^ hash(self._parent)

    @property
    def trigger(self):
        return self._trigger


class _ExposedOutputEvent(OutputEvent):

    def __init__(self, port_exposure):
        self._port_exposure = port_exposure

    @property
    def _name(self):
        return self.port_name

    @property
    def port_name(self):
        return self._port_exposure.name

    @property
    def port(self):
        return self._port_exposure


class _DelayedOnEvent(_NamespaceOnCondition):
    """
    OnEvents that are triggered by delayed local connections are represented
    by OnConditions, which are triggered by a "delay trigger" state variable
    being passed by the simulation time 't'
    """

    def __init__(self, on_event, port_connection):
        self._sub_componet = on_event,
        self._port_connection = port_connection

    @property
    def trigger(self):
        state_var = make_delay_trigger_name(self._port_connection)
        return Trigger('t > {}'.format(state_var))
