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
from nineml.utils import (check_inferred_against_declared,
                          assert_no_duplicates)
from nineml.annotations import VALIDATION, DIMENSIONALITY, PY9ML_NS
from nineml.base import DynamicPortsObject
from ..componentclass.base import Alias
from ..expressions import Constant


class Dynamics(ComponentClass, DynamicPortsObject):

    """
    A Dynamics object represents a *component* in NineML.
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

    send_port_dicts = ('_analog_send_ports', '_event_send_ports')
    receive_port_dicts = ('_analog_receive_ports', '_analog_reduce_ports',
                          '_event_send_ports')

    def __init__(self, name, parameters=None, analog_ports=[],
                 event_ports=[], regimes=None, aliases=None,
                 state_variables=None, constants=None,
                 validate_dimensions=True, strict_unused=True,
                 **kwargs):
        """
        Constructs a Dynamics component class

        Parameters
        ----------
        name : str
            The name of the component_class.
        parameters : list(Parameter | str) | None
            A list containing either |Parameter| objects
            or strings representing the parameter names. If ``None``, then the
            parameters are automatically inferred from the |Dynamics| block.
        analog_ports : list(AnalogPort)
            A list of |AnalogPorts|, which will be the
            local |AnalogPorts| for this object.
        event_ports: list(EventPort)
            A list of |EventPorts| objects, which will be the
            local event-ports for this object. If this is ``None``, then they
            will be automatically inferred from the dynamics block.
        regimes: list(Regime)
            List of the regimes within the Dynamics component class
        aliases : list(Alias)
            List of the aliases within the Dynamics component class
        state_variables : list(StateVariable)
            List of the state variables within the Dynamics component class
        constants : list(Constant)
            List of the constants within the Dynamics component class
        validate_dimensions : bool
            Flags whether to perform dimensionality checking on the component
            class or not
        document : Document
            The NineML document the dynamics object belongs to (if any)
        strict_unused : bool
            Flags whether to raise an Exception if there are unused parameters
            or ports within the Dynamics component class. Very useful when
            manually creating a dynamics class as it typically signifies an
            error but needs to be disabled when flattening a multi-dynamics
            class as some on-event transitions are omitted if their ports are
            not exposed, which can lead to unused parameters/analog ports.

        Examples:

        >>> a = Dynamics(name='MyComponent1')

        .. todo::

            Point this towards and example of constructing ComponentClasses.
            This can't be here, because we also need to know about dynamics.
            For examples

        """
        ComponentClass.__init__(self, name=name, parameters=parameters,
                                aliases=aliases, constants=constants)
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
            check_inferred_against_declared(
                self._parameters.keys(), inferred_struct.parameter_names,
                desc=("\nPlease check for references to missing "
                      "parameters in component class '{}'.\n"
                      .format(self.name)), strict_unused=strict_unused)
        else:
            self._parameters = dict((n, Parameter(n))
                                    for n in inferred_struct.parameter_names)

        # Check any supplied state_variables match:
        if self.num_state_variables:
            state_var_names = [p.name for p in self.state_variables]
            check_inferred_against_declared(
                state_var_names, inferred_struct.state_variable_names,
                desc=("\nPlease check for time derivatives of missing state "
                      "variables in component class '{}'.\n"
                      .format(self.name)), strict_unused=False)
        else:
            state_vars = dict((n, StateVariable(n)) for n in
                              inferred_struct.state_variable_names)
            self._state_variables = state_vars

        # Set and check event receive ports match inferred
        self._event_receive_ports = dict((p.name, p) for p in event_ports
                                         if isinstance(p, EventReceivePort))
        if len(self._event_receive_ports):
            check_inferred_against_declared(
                self._event_receive_ports.keys(),
                inferred_struct.input_event_port_names,
                desc=("\nPlease check OnEvents for references to missing "
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
            # FIXME: not all OutputEvents are necessarily exposed as Ports,
            # so really we should just check that all declared output event
            # ports are in the list of inferred ports, not that the declared
            # list is identical to the inferred one.
            check_inferred_against_declared(
                self._event_send_ports.keys(),
                inferred_struct.event_out_port_names,
                desc=("\nPlease check OutputEvent for references to missing "
                      "EventSendPorts in component class '{}'.\n"
                      .format(self.name)))
        else:
            # Event ports not supplied, so lets use the inferred ones.
            for pname in inferred_struct.event_out_port_names:
                self._event_send_ports[pname] = EventSendPort(name=pname)
        # TODO: Add check for inferred analog ports??
        self.annotations.set((VALIDATION, PY9ML_NS), DIMENSIONALITY,
                             validate_dimensions)
        for transition in self.all_transitions():
            transition.bind(self)
        # Is the finished component_class valid?:
        self.validate(**kwargs)

    def rename_symbol(self, old_symbol, new_symbol):
        DynamicsRenameSymbol(self, old_symbol, new_symbol)

    def assign_indices(self):
        DynamicsAssignIndices(self)

    def required_for(self, expressions):
        return DynamicsRequiredDefinitions(self, expressions)

    def clone(self, memo=None, **kwargs):  # @UnusedVariable
        return DynamicsCloner(memo=memo).visit(self, **kwargs)

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

    def validate(self, validate_dimensions=None, **kwargs):
        if validate_dimensions is None:
            validate_dimensions = (
                self.annotations.get((VALIDATION, PY9ML_NS), DIMENSIONALITY,
                                     default='True') == 'True')
        self._resolve_transition_regimes()
        DynamicsValidator.validate_componentclass(self, validate_dimensions,
                                                  **kwargs)

    @property
    def is_random(self):
        return DynamicsHasRandomProcessQuerier().visit(self)

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_componentclass(self, **kwargs)

    def is_linear(self):
        if self.num_regimes > 1:
            return False
        # FIXME: Need to analyse all the time derivatives and determine whether
        # they are all linear (i.e. +-*/ of other states)
        return True

    def is_flat(self):
        return True

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
                                                trans.key))
                trans.set_target_regime(target)

    def serialize_node(self, node, **options):  # @UnusedVariable @IgnorePep8
        node.attr('name', self.name, **options)
        node.children(self.parameters, **options)
        node.children(self.event_receive_ports, **options)
        node.children(self.analog_receive_ports, **options)
        node.children(self.analog_reduce_ports, **options)
        node.children(self.event_send_ports, **options)
        node.children(self.analog_send_ports, **options)
        node.children(self.state_variables, **options)
        node.children(self.regimes, **options)
        node.children(self.aliases, **options)
        node.children(self.constants, **options)

    @classmethod
    def unserialize_node(cls, node, **options):  # @UnusedVariable
        return cls(
            name=node.attr('name', **options),
            parameters=node.children(Parameter, **options),
            analog_ports=node.children([AnalogSendPort, AnalogReceivePort,
                                        AnalogReducePort], **options),
            event_ports=node.children([EventSendPort, EventReceivePort],
                                      **options),
            regimes=node.children(Regime, **options),
            aliases=node.children(Alias, **options),
            state_variables=node.children(StateVariable, **options),
            constants=node.children(Constant, **options))

    def serialize_node_v1(self, node, **options):  # @UnusedVariable @IgnorePep8
        node.attr('name', self.name, **options)
        node.children(self.parameters, **options)
        node.children(self.event_receive_ports, **options)
        node.children(self.analog_receive_ports, **options)
        node.children(self.analog_reduce_ports, **options)
        node.children(self.event_send_ports, **options)
        node.children(self.analog_send_ports, **options)
        dyn_elem = node.visitor.create_elem('Dynamics',
                                            parent=node.serial_element)
        node.children(self.state_variables, parent_elem=dyn_elem, **options)
        node.children(self.regimes, parent_elem=dyn_elem, **options)
        node.children(self.aliases, parent_elem=dyn_elem, **options)
        node.children(self.constants, parent_elem=dyn_elem, **options)

    @classmethod
    def unserialize_node_v1(cls, node, **options):  # @UnusedVariable
        dyn_elem = node.visitor.get_child(node.serial_element, 'Dynamics',
                                          **options)
        node.unprocessed_children.remove('Dynamics')
        return cls(
            name=node.attr('name', **options),
            parameters=node.children(Parameter, **options),
            analog_ports=node.children([AnalogSendPort, AnalogReceivePort,
                                        AnalogReducePort], **options),
            event_ports=node.children([EventSendPort, EventReceivePort],
                                      **options),
            regimes=node.children(Regime, parent_elem=dyn_elem, **options),
            aliases=node.children(Alias, parent_elem=dyn_elem, **options),
            state_variables=node.children(StateVariable, parent_elem=dyn_elem,
                                          **options),
            constants=node.children(Constant, parent_elem=dyn_elem, **options))

# Import visitor modules and those which import visitor modules
from .regimes import StateVariable, Regime  # @IgnorePep8
from .visitors.validators import DynamicsValidator  # @IgnorePep8
from .visitors import DynamicsInterfaceInferer  # @IgnorePep8
from .visitors.cloner import DynamicsCloner  # @IgnorePep8
from .visitors.queriers import (DynamicsElementFinder,  # @IgnorePep8
                                DynamicsRequiredDefinitions,
                                DynamicsExpressionExtractor,
                                DynamicsDimensionResolver,
                                DynamicsHasRandomProcessQuerier)
from .visitors.modifiers import (  # @IgnorePep8
    DynamicsRenameSymbol, DynamicsAssignIndices,
    DynamicsExpandAliasDefinition)
