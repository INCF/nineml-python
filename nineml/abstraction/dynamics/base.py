"""
Definitions for the Dynamics. Dynamics derives from 2 other mixin
classes, which provide functionality for hierachical components and for local
components definitions of interface and dynamics

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from nineml.exceptions import NineMLRuntimeError, name_error
from nineml.utils import normalise_parameter_as_list, filter_discrete_types
from itertools import chain
from nineml.abstraction.componentclass import (
    ComponentClass, Parameter)
from ..ports import (AnalogReceivePort, AnalogSendPort,
                     AnalogReducePort, EventReceivePort,
                     EventSendPort)
from nineml.utils import (check_list_contain_same_items,
                          assert_no_duplicates)
from nineml.xml import nineml_ns, E
from nineml.annotations import VALIDATE_DIMENSIONS


class Dynamics(ComponentClass):

    """A Dynamics object represents a *component* in NineML.

      .. todo::

         For more information, see

    """
    nineml_type = 'Dynamics'
    defining_attributes = (ComponentClass.defining_attributes +
                           ('_analog_send_ports', '_analog_receive_ports',
                            '_analog_reduce_ports', '_event_send_ports',
                            '_event_receive_ports', '_regimes',
                            '_state_variables'))
    class_to_member = dict(
        tuple(ComponentClass.class_to_member.iteritems()) +
        (('AnalogSendPort', 'analog_send_port'),
         ('AnalogReceivePort', 'analog_receive_port'),
         ('AnalogReducePort', 'analog_reduce_port'),
         ('EventSendPort', 'event_send_port'),
         ('EventReceivePort', 'event_receive_port'),
         ('Regime', 'regime'),
         ('StateVariable', 'state_variable')))

    # Maintains order of elements between writes
    write_order = ('Parameter', 'EventReceivePort', 'AnalogReceivePort',
                   'AnalogReducePort', 'EventSendPort', 'AnalogSendPort',
                   'StateVariable', 'Regime', 'Alias', 'Constant',
                   'Annotations')

    send_port_dicts = ('_analog_send_ports', '_event_send_ports')
    receive_port_dicts = ('_analog_receive_ports', '_analog_reduce_ports',
                          '_event_send_ports')

    def __init__(self, name, parameters=None, analog_ports=[],
                 event_ports=[], regimes=None, aliases=None,
                 state_variables=None, constants=None,
                 validate_dimensions=True, document=None):
        """Constructs a Dynamics

        :param name: The name of the component_class.
        :param parameters: A list containing either |Parameter| objects
            or strings representing the parameter names. If ``None``, then the
            parameters are automatically inferred from the |Dynamics| block.
        :param analog_ports: A list of |AnalogPorts|, which will be the
            local |AnalogPorts| for this object.
        :param event_ports: A list of |EventPorts| objects, which will be the
            local event-ports for this object. If this is ``None``, then they
            will be automatically inferred from the dynamics block.
        :param interface: A shorthand way of specifying the **interface** for
            this component_class; |Parameters|, |AnalogPorts| and |EventPorts|.
            ``interface`` takes a list of these objects, and automatically
            resolves them by type into the correct types.

        Examples:

        >>> a = Dynamics(name='MyComponent1')

        .. todo::

            Point this towards and example of constructing ComponentClasses.
            This can't be here, because we also need to know about dynamics.
            For examples

        """
        ComponentClass.__init__(self, name=name, parameters=parameters,
                                aliases=aliases, constants=constants,
                                document=document)
        regimes = normalise_parameter_as_list(regimes)
        state_variables = normalise_parameter_as_list(state_variables)

        # Load the state variables as objects or strings:
        sv_types = (basestring, StateVariable)
        sv_td = filter_discrete_types(state_variables, sv_types)
        sv_from_strings = [StateVariable(o, dimension=None)
                           for o in sv_td[basestring]]
        state_variables = sv_td[StateVariable] + sv_from_strings

        assert_no_duplicates(r.name for r in regimes)
        assert_no_duplicates(s.name for s in state_variables)

        self._regimes = dict((r.name, r) for r in regimes)
        self._state_variables = dict((s.name, s) for s in state_variables)

        # Ensure analog_ports is a list not an iterator
        analog_ports = list(analog_ports)
        event_ports = list(event_ports)

        # Check there aren't any duplicates in the port and parameter names
        assert_no_duplicates(p if isinstance(p, basestring) else p.name
                             for p in chain(parameters if parameters else [],
                                            analog_ports, event_ports))

        self._analog_send_ports = dict((p.name, p) for p in analog_ports
                                       if isinstance(p, AnalogSendPort))
        self._analog_receive_ports = dict((p.name, p) for p in analog_ports
                                          if isinstance(p, AnalogReceivePort))
        self._analog_reduce_ports = dict((p.name, p) for p in analog_ports
                                         if isinstance(p, AnalogReducePort))

        # Create dummy event ports to keep the ActionVisitor base class of
        # the interface inferrer happy
        self._event_receive_ports = self._event_send_ports = self.subnodes = {}

        # EventPort, StateVariable and Parameter Inference:
        inferred_struct = DynamicsInterfaceInferer(self)

        # Check any supplied parameters match:
        if parameters is not None:
            inf_check(self._parameters.keys(), inferred_struct.parameter_names,
                      desc=("\nPlease check for references to missing "
                            "parameters in component class '{}'.\n"
                            .format(self.name)))
        else:
            self._parameters = dict((n, Parameter(n))
                                    for n in inferred_struct.parameter_names)

        # Check any supplied state_variables match:
        if self.num_state_variables:
            state_var_names = [p.name for p in self.state_variables]
            inf_check(state_var_names, inferred_struct.state_variable_names,
                      ("\nPlease check for time derivatives of missing state "
                       "variables in component class '{}'.\n"
                       .format(self.name)))
        else:
            state_vars = dict((n, StateVariable(n)) for n in
                              inferred_struct.state_variable_names)
            self._state_variables = state_vars

        # Set and check event receive ports match inferred
        self._event_receive_ports = dict(
            (p.name, p) for p in event_ports if isinstance(p,
                                                           EventReceivePort))
        if len(self._event_receive_ports):
            # FIXME: not all OutputEvents are necessarily exposed as Ports,
            # so really we should just check that all declared output event
            # ports are in the list of inferred ports, not that the declared
            # list is identical to the inferred one.
            inf_check(self._event_receive_ports.keys(),
                      inferred_struct.input_event_port_names,
                      ("\nPlease check OnEvents for references to missing "
                       "EventReceivePorts in component class '{}'.\n"
                       .format(self.name)))
        else:
            # Event ports not supplied, so lets use the inferred ones.
            for pname in inferred_struct.input_event_port_names:
                self._event_receive_ports[pname] = EventReceivePort(name=pname)

        # Set and check event send ports match inferred
        self._event_send_ports = dict(
            (p.name, p) for p in event_ports if isinstance(p, EventSendPort))
        if len(self._event_send_ports):
            inf_check(self._event_send_ports.keys(),
                      inferred_struct.event_out_port_names,
                      ("\nPlease check OutputEvent for references to missing "
                       "EventSendPorts in component class '{}'.\n"
                       .format(self.name)))
        else:
            # Event ports not supplied, so lets use the inferred ones.
            for pname in inferred_struct.event_out_port_names:
                self._event_send_ports[pname] = EventSendPort(name=pname)

        self.annotations[nineml_ns][VALIDATE_DIMENSIONS] = validate_dimensions
        for transition in self.all_transitions():
            transition.bind(self)
        # Is the finished component_class valid?:
        self.validate()

    # -------------------------- #

    def rename_symbol(self, old_symbol, new_symbol):
        DynamicsRenameSymbol(self, old_symbol, new_symbol)

    def assign_indices(self):
        DynamicsAssignIndices(self)

    def required_for(self, expressions):
        return DynamicsRequiredDefinitions(self, expressions)

    def dimension_of(self, element):
        try:
            resolver = self._dimension_resolver
        except AttributeError:
            resolver = DynamicsDimensionResolver(self)
            self._dimension_resolver = resolver
        return resolver.dimension_of(element)

    def overridden_in_regimes(self, alias):
        return (r for r in self.regimes if alias.name in r.alias_names)

    def _find_element(self, element):
        return DynamicsElementFinder(element).found_in(self)

    def __repr__(self):
        return "<dynamics.Dynamics %s>" % self.name

    def validate(self, validate_dimensions=None):
        if validate_dimensions is None:
            validate_dimensions = self.annotations[nineml_ns].get(
                VALIDATE_DIMENSIONS, True)
        self._resolve_transition_regimes()
        DynamicsValidator.validate_componentclass(self, validate_dimensions)

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_componentclass(self, **kwargs)

    @property
    def num_state_variables(self):
        return len(list(self._state_variables))

    @property
    def num_regimes(self):
        return len(list(self._regimes))

    @property
    def attributes_with_dimension(self):
        return chain(super(Dynamics, self).attributes_with_dimension,
                     self.analog_ports, self.state_variables)

    @property
    def num_analog_send_ports(self):
        """Returns an iterator over the local |AnalogSendPort| objects"""
        return len(self._analog_send_ports)

    @property
    def num_analog_receive_ports(self):
        """Returns an iterator over the local |AnalogReceivePort| objects"""
        return len(self._analog_receive_ports)

    @property
    def num_analog_reduce_ports(self):
        """Returns an iterator over the local |AnalogReducePort| objects"""
        return len(self._analog_reduce_ports)

    @property
    def num_event_send_ports(self):
        """Returns an iterator over the local |EventSendPort| objects"""
        return len(self._event_send_ports)

    @property
    def num_event_receive_ports(self):
        """Returns an iterator over the local |EventReceivePort| objects"""
        return len(self._event_receive_ports)

    @property
    def analog_send_ports(self):
        """Returns an iterator over the local |AnalogSendPort| objects"""
        return self._analog_send_ports.itervalues()

    @property
    def analog_receive_ports(self):
        """Returns an iterator over the local |AnalogReceivePort| objects"""
        return self._analog_receive_ports.itervalues()

    @property
    def analog_reduce_ports(self):
        """Returns an iterator over the local |AnalogReducePort| objects"""
        return self._analog_reduce_ports.itervalues()

    @property
    def event_send_ports(self):
        """Returns an iterator over the local |EventSendPort| objects"""
        return self._event_send_ports.itervalues()

    @property
    def event_receive_ports(self):
        """Returns an iterator over the local |EventReceivePort| objects"""
        return self._event_receive_ports.itervalues()

    @property
    def ports(self):
        return chain(super(Dynamics, self).ports,
                     self.analog_send_ports, self.analog_receive_ports,
                     self.analog_reduce_ports, self.event_send_ports,
                     self.event_receive_ports)

    def port(self, name):
        try:
            return self.send_port(name)
        except KeyError:
            return self.receive_port(name)

    def receive_port(self, name):
        try:
            return self.event_receive_port(name)
        except KeyError:
            try:
                return self.analog_receive_port(name)
            except KeyError:
                return self.analog_reduce_port(name)

    def send_port(self, name):
        try:
            return self.event_send_port(name)
        except KeyError:
            return self.analog_send_port(name)

    @property
    def send_ports(self):
        return chain(self.analog_send_ports, self.event_send_ports)

    @property
    def receive_ports(self):
        return chain(self.analog_receive_ports, self.analog_reduce_ports,
                     self.event_receive_ports)

    @property
    def send_port_names(self):
        return chain(self.analog_send_port_names, self.event_send_port_names)

    @property
    def receive_port_names(self):
        return chain(self.analog_receive_port_names,
                     self.analog_reduce_port_names,
                     self.event_receive_port_names)

    @property
    def num_send_ports(self):
        return self.num_analog_send_ports + self.num_event_send_ports

    @property
    def num_receive_ports(self):
        return (self.num_analog_receive_ports + self.num_analog_reduce_ports +
                self.num_event_receive_ports)

    @property
    def analog_ports(self):
        """Returns an iterator over the local analog port objects"""
        return chain(self.analog_send_ports, self.analog_receive_ports,
                     self.analog_reduce_ports)

    @property
    def event_ports(self):
        return chain(self.event_send_ports, self.event_receive_ports)

    def analog_port(self, name):
        try:
            return self.analog_send_port(name)
        except KeyError:
            try:
                return self.analog_receive_port(name)
            except KeyError:
                return self.analog_reduce_port(name)

    def event_port(self, name):
        try:
            return self.event_send_port(name)
        except KeyError:
            return self.event_receive_port(name)

    @property
    def regimes(self):
        """Forwarding function to self._regimes"""
        return self._regimes.itervalues()

    @property
    def state_variables(self):
        """Forwarding function to self._state_variables"""
        return self._state_variables.itervalues()

    @name_error
    def regime(self, name):
        return self._regimes[name]

    @name_error
    def state_variable(self, name):
        return self._state_variables[name]

    @name_error
    def analog_send_port(self, name):
        return self._analog_send_ports[name]

    @name_error
    def analog_receive_port(self, name):
        return self._analog_receive_ports[name]

    @name_error
    def analog_reduce_port(self, name):
        return self._analog_reduce_ports[name]

    @name_error
    def event_send_port(self, name):
        return self._event_send_ports[name]

    @name_error
    def event_receive_port(self, name):
        return self._event_receive_ports[name]

    @property
    def regime_names(self):
        return self._regimes.iterkeys()

    @property
    def state_variable_names(self):
        return self._state_variables.iterkeys()

    @property
    def port_names(self):
        return chain(self.analog_port_names, self.event_port_names)

    @property
    def analog_port_names(self):
        """Returns an iterator over the local analog port objects"""
        return chain(self.analog_send_port_names,
                     self.analog_receive_port_names,
                     self.analog_reduce_port_names)

    @property
    def event_port_names(self):
        """Returns an iterator over the local analog port objects"""
        return chain(self.event_send_port_names,
                     self.event_receive_port_names)

    @property
    def analog_send_port_names(self):
        """Returns an iterator over the local |AnalogSendPort| names"""
        return self._analog_send_ports.iterkeys()

    @property
    def analog_receive_port_names(self):
        """Returns an iterator over the local |AnalogReceivePort| names"""
        return self._analog_receive_ports.iterkeys()

    @property
    def analog_reduce_port_names(self):
        """Returns an iterator over the local |AnalogReducePort| names"""
        return self._analog_reduce_ports.iterkeys()

    @property
    def event_send_port_names(self):
        """Returns an iterator over the local |EventSendPort| names"""
        return self._event_send_ports.iterkeys()

    @property
    def event_receive_port_names(self):
        """Returns an iterator over the local |EventReceivePort| names"""
        return self._event_receive_ports.iterkeys()

    @property
    def all_components(self):
        """
        Returns an iterator over this component_class and all sub_dynamics
        """
        yield self
        for subcomponent in self.subnodes.values():
            for subcomp in subcomponent.all_components:
                yield subcomp

    @property
    def all_expressions(self):
        extractor = DynamicsExpressionExtractor()
        extractor.visit(self)
        return extractor.expressions

    @property
    def transitions(self):
        return self.all_transitions()

    def all_transitions(self):
        return chain(*(r.transitions for r in self.regimes))

    def all_on_conditions(self, trigger=None):
        return chain(*((oc for oc in r.on_conditions
                        if trigger is None or oc.trigger == trigger)
                       for r in self.regimes))

    def all_on_events(self, event_port=None):
        return chain(*((oe for oe in r.on_events
                        if event_port is None or oe.port == event_port)
                       for r in self.regimes))

    def all_time_derivatives(self, state_variable=None):
        return chain(*((td for td in r.time_derivatives
                        if (state_variable is None or
                            td.variable == state_variable.name))
                        for r in self.regimes))

    def all_output_analogs(self):
        """
        Returns an iterator over all aliases that are required for analog
        send ports
        """
        return (a for a in self.aliases
                if a.name in self.analog_send_port_names)

    # -------------------------- #

    def backsub_all(self):
        """Expand all alias definitions in local equations.

        This function finds |Aliases|, |TimeDerivatives|, *send* |AnalogPorts|,
        |StateAssignments| and |Conditions| which are defined in terms of other
        |Aliases|, and expands them, such that each only has |Parameters|,
        |StateVariables| and recv/reduce |AnalogPorts| on the RHS.

        """

        for alias in self.aliases:
            alias_expander = DynamicsExpandAliasDefinition(
                originalname=alias.lhs, targetname=("(%s)" % alias.rhs))
            alias_expander.visit(self)

    def _resolve_transition_regimes(self):
        # Check that the names of the regimes are unique:
        assert_no_duplicates([r.name for r in self.regimes])
        # We only worry about 'target' regimes, since source regimes are taken
        # care of for us by the Regime objects they are attached to.
        for regime in self.regimes:
            for trans in regime.transitions:
                trans.set_source_regime(regime)
                target = trans.target_regime_name
                if target is None:
                    target = regime  # to same regime
                else:
                    try:
                        target = self.regime(target)  # Lookup by name
                    except KeyError:
                        self.regime(target)
                        raise NineMLRuntimeError(
                            "Can't find regime '{}' referenced from '{}' "
                            "transition".format(trans.target_regime,
                                                trans._name))
                trans.set_target_regime(target)

    def to_xml(self, document, E=E, **kwargs):  # @UnusedVariable
        self.standardize_unit_dimensions()
        self.validate()
        return DynamicsXMLWriter(document, E).visit(self)

    @classmethod
    def from_xml(cls, element, document, **kwargs):
        return DynamicsXMLLoader(document).load_dynamics(
            element, **kwargs)


def inf_check(l1, l2, desc):
    check_list_contain_same_items(l1, l2, desc1='Declared',
                                  desc2='Inferred', ignore=['t'], desc=desc)

# Import visitor modules and those which import visitor modules
from .regimes import StateVariable
from .visitors.validators import DynamicsValidator
from .visitors import DynamicsInterfaceInferer
from .visitors.queriers import (DynamicsElementFinder,
                                DynamicsRequiredDefinitions,
                                DynamicsExpressionExtractor,
                                DynamicsDimensionResolver)
from .visitors.modifiers import (
    DynamicsRenameSymbol, DynamicsAssignIndices,
    DynamicsExpandAliasDefinition)
from .visitors.xml import DynamicsXMLLoader, DynamicsXMLWriter
