"""
This file contains the definitions for the Events

:copyright: Copyright 2010-2017 by the NineML Python team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from past.builtins import basestring
import sympy.solvers
from sympy.logic.boolalg import BooleanTrue, BooleanFalse
from nineml.utils import validate_identifier
from nineml.abstraction.componentclass import BaseALObject
from nineml.abstraction.expressions import (
    Expression, ExpressionWithSimpleLHS, t)
from nineml.exceptions import NineMLUsageError, name_error
from nineml.base import ContainerObject
from nineml.utils.iterables import (normalise_parameter_as_list,
                                    filter_discrete_types)
from nineml.exceptions import NineMLNoSolutionException


class StateAssignment(BaseALObject, ExpressionWithSimpleLHS):

    """Assignments represent a change that happens to the value of a
    ``StateVariable`` during a transition between regimes.

    For example, in an integrate-and-fire neuron, we may want to reset the
    voltage back to zero, after it has reached a certain threshold. In this
    case, we would have an ``OnCondition`` object, that is triggered when
    ``v>vthres``. Attached to this OnCondition transition, we would attach an
    StateAssignment which sets ``v=vreset``.

    The left-hand-side symbol must be a state-variable of the component.

    """

    nineml_type = 'StateAssignment'
    nineml_attr = ('variable', 'rhs')

    def __init__(self, variable, rhs):
        """
        StateAssignment

        Parameters
        ----------
        lhs: str
            A state-variable of the component_class.
        rhs: str | sympy.Basic
            A expression for the new value of the state after an assignment.
        """
        BaseALObject.__init__(self)
        ExpressionWithSimpleLHS.__init__(self, lhs=variable, rhs=rhs)

    @property
    def variable(self):
        return self.lhs

    def __repr__(self):
        return "StateAssignment('{}', '{}')".format(self.variable, self.rhs)

    @classmethod
    def from_str(cls, state_assignment_string):
        """Creates an StateAssignment object from a string"""
        lhs, rhs = state_assignment_string.split('=')
        return StateAssignment(variable=lhs, rhs=rhs)

    def serialize_node(self, node, **options):  # @UnusedVariable
        node.attr('variable', self.variable, **options)
        node.attr('MathInline', self.rhs_xml, in_body=True, **options)

    @classmethod
    def unserialize_node(cls, node, **options):  # @UnusedVariable
        variable = node.attr('variable', **options)
        rhs = node.attr('MathInline', in_body=True, dtype=Expression,
                        **options)
        return cls(variable=variable, rhs=rhs)

    @classmethod
    def _children_keys_name(cls):
        return 'state_assignment_variables'


class OutputEvent(BaseALObject):
    """
    OutputEvents can occur during transitions, and correspond to
    an event being generated on the relevant EventPort port in
    the component.
    """

    nineml_type = 'OutputEvent'
    nineml_attr = ('port_name',)

    def __init__(self, port_name):
        """
        Parameters
        ----------
        port_name: str
            The name of the output EventPort that should
            transmit an event. An `EventPort` with a mode of 'send' must exist
            with a corresponding name in the component_class, otherwise a
            ``NineMLRuntimeException`` will be raised.

        """
        super(OutputEvent, self).__init__()
        self._port_name = validate_identifier(port_name)
        self._port = None

    @property
    def port_name(self):
        '''Returns the name of the port'''
        if self._port is not None:
            name = self._port.name
        else:
            name = self._port_name
        return name

    @property
    def port(self):
        if self._port is None:
            raise NineMLUsageError(
                "Cannot access port as output event has not been bound")
        return self._port

    def __str__(self):
        return 'OutputEvent( port: %s )' % self.port_name

    def __repr__(self):
        return "OutputEvent('%s')" % self.port_name

    @property
    def key(self):
        """
        This is included to allow State-assignments to be polymorphic with
        other named structures
        """
        return self.port_name

    def bind(self, component_class):
        self._port = component_class.event_send_port(self.port_name)
        self._port_name = None

    def serialize_node(self, node, **options):  # @UnusedVariable
        node.attr('port', self.port_name, **options)

    @classmethod
    def unserialize_node(cls, node, **options):  # @UnusedVariable
        port_name = node.attr('port', **options)
        return cls(port_name=port_name)


class Transition(BaseALObject, ContainerObject):

    nineml_attr = ('target_regime_name',)
    nineml_children = (StateAssignment, OutputEvent)

    def __init__(self, state_assignments=None, output_events=None,
                 target_regime_name=None):
        """Abstract class representing a transition from one Regime to
        another.

        Transition objects are not created directly, but via the subclasses
        OnEvent and OnCondition.

        Parameters
        ----------
        state_assignments: list(StateAssignment)
            A list of the state-assignments performed
            when this transition occurs. Objects in this list are either
            `string` (e.g A = A+13) or StateAssignment objects.
        output_events: list(OutputEvent)
            A list of OutputEvent objects emitted when
            this transition occurs.
        target_regime_name: str | None
            The name of the regime to go into after this
            transition.  `None` implies staying in the same regime. This has
            to be specified as a string, not the object, because in general the
            |Regime| object is not yet constructed. This is automatically
            resolved by the Dynamics during construction.
        """
        BaseALObject.__init__(self)
        ContainerObject.__init__(self)

        # Load state-assignment objects as strings or StateAssignment objects
        state_assignments = state_assignments or []

        sa_types = (basestring, StateAssignment)
        sa_type_dict = filter_discrete_types(state_assignments, sa_types)
        sa_from_str = [StateAssignment.from_str(o)
                       for o in sa_type_dict[basestring]]

        self.add(*(sa_type_dict[StateAssignment] + sa_from_str))
        self.add(*normalise_parameter_as_list(output_events))

        self._target_regime_name = (
            validate_identifier(target_regime_name)
            if target_regime_name is not None else None)
        self._target_regime = None
        self._source_regime = None

    @property
    def target_regime(self):
        """
        Returns the target regime of this transition.

        Notes
        -----
        This method will only be available after the Dynamics
        containing this transition has been built. See
        ``set_source_regime``
        """
        if self._target_regime is None:
            raise NineMLUsageError(
                "Target regime ({}) has not been set ("
                "'_resolve_transition_regimes' needs to be called on "
                "containing Dynamics object first)."
                .format(self.target_regime_name))
        return self._target_regime

    @property
    def target_regime_name(self):
        if self._target_regime is None:
            name = self._target_regime_name
        else:
            name = self.target_regime.name
        return name

    @property
    def source_regime(self):
        """
        Returns the source regime of this transition.

        Notes
        -----
        This method will only be available after the |Dynamics|
        containing this transition has been built. See
        ``set_source_regime``
        """
        if self._source_regime is None:
            raise NineMLUsageError(
                "Source regime ({}) has not been set ("
                "'_resolve_transition_regimes' needs to be called on "
                "containing Dynamics object first)."
                .format(self.target_regime_name))
        return self._source_regime

    def set_target_regime(self, regime):
        """Returns the target regime of this transition.

        Notes
        -----
        This method will only be available after the Dynamics
        containing this transition has been built. See
        ``set_source_regime``
        """
        assert regime.nineml_type == 'Regime'
        self._target_regime = regime
        self._target_regime_name = None

    def set_source_regime(self, regime):
        """Returns the target regime of this transition.

        Notes
        -----
        This method will only be available after the Dynamics
        containing this transition has been built. See
        ``set_source_regime``
        """
        assert regime.nineml_type == 'Regime'
        self._source_regime = regime

    @property
    def num_state_assignments(self):
        return len(self._state_assignments)

    @property
    def num_output_events(self):
        """|Events| that happen when this transitions occurs"""
        return len(self._output_events)

    @property
    def state_assignments(self):
        return iter(self._state_assignments.values())

    @name_error
    def state_assignment(self, variable):
        return self._state_assignments[variable]

    @property
    def state_assignment_variables(self):
        return iter(self._state_assignments.keys())

    @property
    def state_assignment_keys(self):
        return self.state_assignment_variables

    @property
    def output_event_port_names(self):
        return iter(self._output_events.keys())

    @property
    def output_event_keys(self):
        return self.output_event_port_names

    @property
    def output_events(self):
        """|Events| that happen when this transitions occurs"""
        return iter(self._output_events.values())

    @name_error
    def output_event(self, port):
        return self._output_events[port]

    def bind(self, component_class):
        for output_event in self.output_events:
            output_event.bind(component_class)

    def serialize_node(self, node, **options):  # @UnusedVariable
        node.attr('target_regime', self.target_regime.name, **options)
        node.children(self.state_assignments)
        node.children(self.output_events)


class OnEvent(Transition):

    nineml_type = "OnEvent"
    nineml_attr = (Transition.nineml_attr + ('src_port_name',))

    def __init__(self, src_port_name, state_assignments=None,
                 output_events=None, target_regime_name=None):
        """
        Constructor for ``OnEvent``

        Parameters
        ----------
        src_port_name: str
            The name of the |EventPort| that triggers this transition
        """
        Transition.__init__(self, state_assignments=state_assignments,
                            output_events=output_events,
                            target_regime_name=target_regime_name)
        self._src_port_name = validate_identifier(src_port_name)
        self._port = None

    def __repr__(self):
        return "OnEvent({})".format(self.src_port_name)

    @property
    def src_port_name(self):
        if self._port is not None:
            name = self._port.name
        else:
            name = self._src_port_name
        return name

    @property
    def port(self):
        if self._port is None:
            raise NineMLUsageError(
                "OnEvent is not bound to a component class")
        return self._port

    @property
    def key(self):
        """
        This is included to allow OnEvents to be polymorphic with
        other named structures
        """
        return self.src_port_name

    def bind(self, component_class):
        super(OnEvent, self).bind(component_class)
        self._port = component_class.event_receive_port(self.src_port_name)
        self._src_port_name = None

    def serialize_node(self, node, **options):  # @UnusedVariable
        node.attr('port', self.src_port_name, **options)
        super(OnEvent, self).serialize_node(node, **options)

    @classmethod
    def unserialize_node(cls, node, **options):  # @UnusedVariable
        target_regime = node.attr('target_regime', **options)
        return cls(src_port_name=node.attr('port', **options),
                   state_assignments=node.children(StateAssignment,
                                                   **options),
                   output_events=node.children(OutputEvent, **options),
                   target_regime_name=target_regime)


class Trigger(BaseALObject, Expression):

    nineml_type = 'Trigger'

    def __init__(self, rhs):
        BaseALObject.__init__(self)
        Expression.__init__(self, rhs)
        self._rhs = self._make_strict(self.rhs)

    def __repr__(self):
        return "Trigger('%s')" % (self.rhs)

    @property
    def key(self):
        """
        This is included to allow OnConditions to be polymorphic with
        other named structures
        """
        return self.rhs

    @property
    def sort_key(self):
        return str(self.rhs)

    @property
    def reactivate_condition(self):
        """
        Return the condition under which the trigger should be reactivated
        after it has been triggered.
        """
        return Expression(self._make_strict(sympy.Not(self.rhs)))

    @property
    def crossing_time_expr(self):
        """
        Get an expression for the exact time of the trigger if it depends on
        t. Will not be able to solve for time from complex equations but should
        be able to handle common basic cases (e.g. t > next_spike_time).
        """
        try:
            return ExpressionWithSimpleLHS('t', self._becomes_true(self.rhs),
                                           assign_to_reserved=True)
        except NineMLNoSolutionException:
            return None

    @classmethod
    def _becomes_true(cls, expr):
        if t not in expr.atoms():
            # TODO: For sub expressions that don't involve t, this could be
            #       handled by a piecewise expression
            raise NineMLNoSolutionException
        if isinstance(expr, (sympy.StrictGreaterThan,
                             sympy.StrictLessThan)):
            # Get the equation for the transition between true and false
            equality = sympy.Eq(*expr.args)
            solution = sympy.solvers.solve(equality, t)
            try:
                if len(solution) != 1:
                    raise NineMLNoSolutionException
            except TypeError:
                raise NineMLNoSolutionException
            time_expr = solution[0]
        elif isinstance(expr, sympy.Or):
            time_expr = sympy.Min(*(cls._becomes_true(a) for a in expr.args))
        else:
            # TODO: Should add handling for And expressions but will need
            # conditional handling for expressions that are true and then
            # become false.
            raise NineMLNoSolutionException
        return time_expr

    @classmethod
    def _make_strict(cls, expr):
        """
        Converts inequalities to strict inequalities
        """
        if isinstance(expr, sympy.GreaterThan):
            expr = sympy.StrictGreaterThan(*expr.args)
        elif isinstance(expr, sympy.LessThan):
            expr = sympy.StrictLessThan(*expr.args)
        elif not isinstance(expr, (sympy.Symbol, sympy.Number, BooleanTrue,
                                   BooleanFalse, int, float, bool)):
            expr = expr.__class__(*(cls._make_strict(a) for a in expr.args))
        return expr

    def serialize_node(self, node, **options):  # @UnusedVariable
        node.attr('MathInline', self.rhs_xml, in_body=True, **options)

    @classmethod
    def unserialize_node(cls, node, **options):  # @UnusedVariable
        return cls(node.attr('MathInline', in_body=True, dtype=Expression,
                             **options))


class OnCondition(Transition):

    nineml_type = "OnCondition"
    nineml_child = {'trigger': Trigger}

    def __init__(self, trigger, state_assignments=None,
                 output_events=None, target_regime_name=None):
        """
        Parameters
        ----------
        trigger: str | sympy.Basic | Trigger
            Either a |Trigger| object, sympy expr or a ``string`` object
            specifying the conditions under which this transition should
            occur.
        """
        if isinstance(trigger, Trigger):
            trigger = trigger.rhs
        self._trigger = Trigger(rhs=trigger)
        Transition.__init__(self, state_assignments=state_assignments,
                            output_events=output_events,
                            target_regime_name=target_regime_name)

    def __repr__(self):
        return 'OnCondition({})'.format(self.trigger.rhs)

    @property
    def trigger(self):
        return self._trigger

    @property
    def key(self):
        """
        This is included to allow OnConditions to be polymorphic with
        other named structures
        """
        return self.trigger.rhs

    @property
    def sort_key(self):
        return self.trigger.sort_key

    def serialize_node(self, node, **options):  # @UnusedVariable
        node.child(self.trigger, **options)
        super(OnCondition, self).serialize_node(node, **options)

    @classmethod
    def unserialize_node(cls, node, **options):  # @UnusedVariable
        target_regime = node.attr('target_regime', **options)
        trigger = node.child(Trigger, **options)
        return cls(trigger=trigger,
                   state_assignments=node.children(StateAssignment, **options),
                   output_events=node.children(OutputEvent, **options),
                   target_regime_name=target_regime)

    @classmethod
    def _children_keys_name(cls):
        return 'on_condition_triggers'


# import nineml.abstraction.dynamics.visitors.queriers
