"""
Definitions for the Dynamics. Dynamics derives from 2 other mixin
classes, which provide functionality for hierachical components and for local
components definitions of interface and dynamics

:copyright: Copyright 2010-2017 by the NineML Python team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from past.builtins import basestring
from nineml.exceptions import NineMLUsageError, name_error
from nineml.utils.iterables import (
    normalise_parameter_as_list, filter_discrete_types)
from nineml.visitors import Cloner
from itertools import chain
from nineml.abstraction.componentclass import (
    ComponentClass, Parameter)
from ..ports import (AnalogReceivePort, AnalogSendPort,
                     AnalogReducePort, EventReceivePort,
                     EventSendPort)
from .regimes import Regime, StateVariable
from nineml.utils import (check_inferred_against_declared,
                          assert_no_duplicates)
from nineml.annotations import VALIDATION, DIMENSIONALITY, PY9ML_NS
from nineml.base import DynamicPortsObject
from ..componentclass.base import Alias
from ..expressions import Constant


class Dynamics(ComponentClass, DynamicPortsObject):

    """
    A Dynamics object represents a *component* in NineML.

    Parameters
    ----------
    name : str
        The name of the component_class.
    parameters : list(Parameter | str) | None
        A list containing either |Parameter| objects
        or strings representing the parameter names. If ``None``, then the
        parameters are automatically inferred from the |Dynamics| block.
    ports : list(Port)
        A list of ports for the dynamics class. The most general argument to
        pass ports into the constructor with. Note that you can also use the
        more specific arguments (e.g. analog_ports, analog_send_ports, et...),
        a they all get concatenated in the end in any case.
    analog_ports : list(AnalogPort)
        A list of analog ports for the dynamics class
    event_ports: list(EventPort)
        A list of event ports for the dynamics class
    event_send_ports: list(EventPort)
        A list of event send ports for the dynamics class
    event_receive_ports: list(EventPort)
        A list of event receive ports for the dynamics class
    analog_receive_ports : list(AnalogPort)
        A list of analog receive ports for the dynamics class
    analog_reduce_ports : list(AnalogPort)
        A list of analog reduce ports for the dynamics class
    analog_send_ports : list(AnalogPort)
        A list of analog send ports for the dynamics class
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

    Point this towards and example of constructing ComponentClasses.
    This can't be here, because we also need to know about dynamics.
    For examples
    """
    nineml_type = 'Dynamics'
    nineml_children = (StateVariable, AnalogSendPort, AnalogReceivePort,
                       AnalogReducePort, EventSendPort, EventReceivePort,
                       Regime) + ComponentClass.nineml_children

    def __init__(self, name, parameters=(), ports=(), analog_ports=(),
                 event_ports=(), analog_receive_ports=(),
                 analog_reduce_ports=(), analog_send_ports=(),
                 event_receive_ports=(), event_send_ports=(),
                 regimes=(), aliases=(), state_variables=(), constants=(),
                 validate=True, validate_dimensions=True, strict_unused=True,
                 **kwargs):

        ComponentClass.__init__(self, name=name, parameters=parameters,
                                aliases=aliases, constants=constants)
        # Load the state variables as objects or strings:
        state_variables = normalise_parameter_as_list(state_variables)
        sv_types = (basestring, StateVariable)
        sv_td = filter_discrete_types(state_variables, sv_types)
        sv_from_strings = [StateVariable(o, dimension=None)
                           for o in sv_td[basestring]]
        state_variables = sv_td[StateVariable] + sv_from_strings
        self.add(*state_variables)

        regimes = normalise_parameter_as_list(regimes)
        self.add(*regimes)

        # Combine various port arguments (there is redundancy due to backwards
        # compatibility and convenience of use)
        self.add(*ports)
        self.add(*analog_ports)
        self.add(*event_ports)
        self.add(*analog_receive_ports)
        self.add(*analog_reduce_ports)
        self.add(*analog_send_ports)
        self.add(*event_receive_ports)
        self.add(*event_send_ports)

        # Run the Interface inferer to either check the explicitly provided
        # members match the inferred or implicitly derive them.

        # EventPort, StateVariable and Parameter Inference:
        inferred_struct = DynamicsInterfaceInferer(self)

        # Check any supplied parameters match:
        if self.num_parameters:
            check_inferred_against_declared(
                list(self._parameters.keys()), inferred_struct.parameter_names,
                desc=("\nPlease check for references to missing "
                      "parameters in component class '{}'.\n"
                      .format(self.name)), strict_unused=strict_unused)
        else:
            self.add(*(Parameter(n) for n in inferred_struct.parameter_names))

        # Check any supplied state_variables match:
        if self.num_state_variables:
            state_var_names = [p.name for p in self.state_variables]
            check_inferred_against_declared(
                state_var_names, inferred_struct.state_variable_names,
                desc=("\nPlease check for time derivatives of missing state "
                      "variables in component class '{}'.\n"
                      .format(self.name)), strict_unused=False)
        else:
            self.add(*(StateVariable(n)
                       for n in inferred_struct.state_variable_names))

        # Set and check event receive ports match inferred
        if self.num_event_receive_ports:
            check_inferred_against_declared(
                self.event_receive_port_names,
                inferred_struct.input_event_port_names,
                desc=("\nPlease check OnEvents for references to missing "
                      "EventReceivePorts in component class '{}'.\n"
                      .format(self.name)))
        else:
            # Event ports not supplied, so lets use the inferred ones.
            self.add(*(EventReceivePort(name=p)
                       for p in inferred_struct.input_event_port_names))

        # Set and check event send ports match inferred
        if self.num_event_send_ports:
            # FIXME: not all OutputEvents are necessarily exposed as Ports,
            # so really we should just check that all declared output event
            # ports are in the list of inferred ports, not that the declared
            # list is identical to the inferred one.
            check_inferred_against_declared(
                self.event_send_port_names,
                inferred_struct.event_out_port_names,
                desc=("\nPlease check OutputEvent for references to missing "
                      "EventSendPorts in component class '{}'.\n"
                      .format(self.name)))
        else:
            # Event ports not supplied, so lets use the inferred ones.
            self.add(*(EventSendPort(name=p)
                       for p in inferred_struct.event_out_port_names))

        self.bind()

        if validate:
            self.validate(**kwargs)

        self.annotations.set((VALIDATION, PY9ML_NS), DIMENSIONALITY,
                             validate_dimensions)

    def rename_symbol(self, old_symbol, new_symbol):
        DynamicsRenameSymbol(self, old_symbol, new_symbol)

    def required_for(self, expressions):
        return DynamicsRequiredDefinitions(self, expressions)

    def flatten(self, name=None, **kwargs):
        return self.clone(name=name, **kwargs)

    def dimension_of(self, element):
        if self._dimension_resolver is None:
            self._dimension_resolver = DynamicsDimensionResolver(self)
        return self._dimension_resolver.dimension_of(element)

    def substitute_aliases(self):
        """
        Returns a equivalent Dynamics class with all references to aliases with
        substituted by their RHS expressions where they appear
        in time derivatives, state assignments, and triggers, and
        all aliases removed that do not correspond directly to analog send
        ports
        """
        substituted = self.clone(as_class=Dynamics)
        DynamicsSubstituteAliases(substituted)
        return substituted

    def overridden_in_regimes(self, alias):
        return (r for r in self.regimes if alias.name in r.alias_names)

    def bind(self):
        # Bind transitions to target regimes
        for transition in self.all_transitions():
            transition.bind(self)

        # Bind transition target regimes
        self._resolve_transition_regimes()

    def validate(self, validate_dimensions=None, **kwargs):
        if validate_dimensions is None:
            validate_dimensions = (
                self.annotations.get((VALIDATION, PY9ML_NS), DIMENSIONALITY,
                                     default='True') == 'True')
        DynamicsValidator.validate_componentclass(self, validate_dimensions,
                                                  **kwargs)

    @property
    def is_random(self):
        return DynamicsHasRandomProcess(self).found

    def is_linear(self, outputs=None):
        """
        Queries whether time derivative and analog send port expressions in the
        Dynamics class is linear w.r.t. inputs and states. I.e. don't contain
        piece-wise dynamics, multiplication/division of states by other states/
        inputs or non-linear functions (e.g. sin, cos, etc...).

        Parameters
        ----------
        outputs : list(str)
            List of relevant outputs to check for linearity. I.e. expressions
            that only mapped to analog send ports that aren't in the list are
            not checked for linearity (presumably as they are not connected).
            If outputs is None all expressions are checked.
        """
        return DynamicsIsLinear().is_linear(self, outputs=outputs)

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
        return iter(self._analog_send_ports.values())

    @property
    def analog_receive_ports(self):
        """Returns an iterator over the local |AnalogReceivePort| objects"""
        return iter(self._analog_receive_ports.values())

    @property
    def analog_reduce_ports(self):
        """Returns an iterator over the local |AnalogReducePort| objects"""
        return iter(self._analog_reduce_ports.values())

    @property
    def event_send_ports(self):
        """Returns an iterator over the local |EventSendPort| objects"""
        return iter(self._event_send_ports.values())

    @property
    def event_receive_ports(self):
        """Returns an iterator over the local |EventReceivePort| objects"""
        return iter(self._event_receive_ports.values())

    @property
    def regimes(self):
        """Forwarding function to self._regimes"""
        return iter(self._regimes.values())

    @property
    def state_variables(self):
        """Forwarding function to self._state_variables"""
        return iter(self._state_variables.values())

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
        return iter(self._regimes.keys())

    @property
    def state_variable_names(self):
        return iter(self._state_variables.keys())

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
        return iter(self._analog_send_ports.keys())

    @property
    def analog_receive_port_names(self):
        """Returns an iterator over the local |AnalogReceivePort| names"""
        return iter(self._analog_receive_ports.keys())

    @property
    def analog_reduce_port_names(self):
        """Returns an iterator over the local |AnalogReducePort| names"""
        return iter(self._analog_reduce_ports.keys())

    @property
    def event_send_port_names(self):
        """Returns an iterator over the local |EventSendPort| names"""
        return iter(self._event_send_ports.keys())

    @property
    def event_receive_port_names(self):
        """Returns an iterator over the local |EventReceivePort| names"""
        return iter(self._event_receive_ports.keys())

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
                        raise NineMLUsageError(
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
from .visitors.validators import DynamicsValidator  # @IgnorePep8
from .visitors.queriers import (DynamicsRequiredDefinitions,  # @IgnorePep8
                                DynamicsExpressionExtractor,
                                DynamicsDimensionResolver,
                                DynamicsHasRandomProcess,
                                DynamicsIsLinear,
                                DynamicsInterfaceInferer)
from .visitors.modifiers import (  # @IgnorePep8
    DynamicsRenameSymbol, DynamicsSubstituteAliases)
