"""
This file contains the definitions for the Events

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from copy import copy
import sympy.solvers
from nineml.utils import ensure_valid_identifier, filter_discrete_types
from nineml.abstraction.componentclass import BaseALObject
from ..expressions import Expression, ExpressionWithSimpleLHS, t
from nineml.exceptions import (NineMLRuntimeError,
                               NineMLInvalidElementTypeException, name_error)
from nineml.base import ContainerObject
from nineml.utils import normalise_parameter_as_list
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

    def __init__(self, lhs, rhs):
        """StateAssignment Constructor

        `lhs` -- A `string`, which must be a state-variable of the
                 component_class.
        `rhs` -- A `string`, representing the new value of the state after
                 this assignment.

        """
        BaseALObject.__init__(self)
        ExpressionWithSimpleLHS.__init__(self, lhs=lhs, rhs=rhs)

    @property
    def variable(self):
        return self.lhs

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_stateassignment(self, **kwargs)

    def __repr__(self):
        return "StateAssignment('%s', '%s')" % (self.lhs, self.rhs)

    @classmethod
    def from_str(cls, state_assignment_string):
        """Creates an StateAssignment object from a string"""
        lhs, rhs = state_assignment_string.split('=')
        return StateAssignment(lhs=lhs, rhs=rhs)


class OutputEvent(BaseALObject):

    """OutputEvent

    OutputEvents can occur during transitions, and correspond to
    an event being generated on the relevant EventPort port in
    the component.
    """

    nineml_type = 'OutputEvent'
    defining_attributes = ('port_name',)

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_outputevent(self, **kwargs)

    def __init__(self, port_name):
        """OutputEvent Constructor

        :param port: The name of the output EventPort that should
            transmit an event. An `EventPort` with a mode of 'send' must exist
            with a corresponding name in the component_class, otherwise a
            ``NineMLRuntimeException`` will be raised.

        """
        super(OutputEvent, self).__init__()
        self._port_name = port_name.strip()
        self._port = None
        ensure_valid_identifier(self._port_name)

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
            raise NineMLRuntimeError(
                "Cannot access port as output event has not been bound")
        return self._port

    def __str__(self):
        return 'OutputEvent( port: %s )' % self.port_name

    def __repr__(self):
        return "OutputEvent('%s')" % self.port_name

    @property
    def _name(self):
        """
        This is included to allow State-assignments to be polymorphic with
        other named structures
        """
        return self.port_name

    def bind(self, component_class):
        self._port = component_class.event_send_port(self.port_name)
        self._port_name = None


class Transition(BaseALObject, ContainerObject):

    defining_attributes = ('_state_assignments', '_output_events',
                           'target_regime_name')
    class_to_member = {'StateAssignment': 'state_assignment',
                       'OutputEvent': 'output_event'}
    write_order = ('Trigger', 'StateAssignment', 'OutputEvent')

    def __init__(self, state_assignments=None, output_events=None,
                 target_regime=None):
        """Abstract class representing a transition from one |Regime| to
        another.

        |Transition| objects are not created directly, but via the subclasses
        |OnEvent| and |OnCondition|.

        :param state_assignments: A list of the state-assignments performed
            when this transition occurs. Objects in this list are either
            `string` (e.g A = A+13) or |StateAssignment| objects.
        :param output_events: A list of |OutputEvent| objects emitted when
            this transition occurs.
        :param target_regime_name: The name of the regime to go into after this
            transition.  ``None`` implies staying in the same regime. This has
            to be specified as a string, not the object, because in general the
            |Regime| object is not yet constructed. This is automatically
            resolved by the |Dynamics| in
            ``_ResolveTransitionRegimeNames()`` during construction.


        .. todo::

            For more information about what happens at a regime transition, see
            here: XXXXXXX

        """
        BaseALObject.__init__(self)
        ContainerObject.__init__(self)

        # Load state-assignment objects as strings or StateAssignment objects
        state_assignments = state_assignments or []

        sa_types = (basestring, StateAssignment)
        sa_type_dict = filter_discrete_types(state_assignments, sa_types)
        sa_from_str = [StateAssignment.from_str(o)
                       for o in sa_type_dict[basestring]]
        self._state_assignments = dict(
            (sa.lhs, sa) for sa in sa_type_dict[StateAssignment] + sa_from_str)

        self._output_events = dict(
            (oe.port_name, oe)
            for oe in normalise_parameter_as_list(output_events))

        if isinstance(target_regime, basestring):
            self._target_regime = None
            self._target_regime_name = target_regime
        else:
            self._target_regime = target_regime
            self._target_regime_name = None
        self._source_regime = None

    def _find_element(self, element):
        return DynamicsElementFinder(element).found_in(self)

    @property
    def target_regime(self):
        """Returns the target regime of this transition.

        .. note::

            This method will only be available after the Dynamics
            containing this transition has been built. See
            ``set_source_regime``
        """
        if self._target_regime is None:
            raise NineMLRuntimeError(
                "Target regime ({}) has not been set (use 'validate()' "
                "of Dynamics first)."
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
        """Returns the source regime of this transition.

        .. note::

            This method will only be available after the |Dynamics|
            containing this transition has been built. See
            ``set_source_regime``
        """
        if self._source_regime is None:
            raise NineMLRuntimeError(
                "Source regime has not been set (use 'validate()' "
                "of Dynamics first)."
                .format(self.target_regime_name))
        return self._source_regime

    def set_target_regime(self, regime):
        """Returns the target regime of this transition.

        .. note::

            This method will only be available after the Dynamics
            containing this transition has been built. See
            ``set_source_regime``
        """
        assert regime.nineml_type == 'Regime'
        self._target_regime = regime
        self._target_regime_name = None

    def set_source_regime(self, regime):
        """Returns the target regime of this transition.

        .. note::

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
        return self._state_assignments.itervalues()

    @name_error
    def state_assignment(self, variable):
        return self._state_assignments[variable]

    @property
    def state_assignment_variables(self):
        return self._state_assignments.iterkeys()

    @property
    def output_event_port_names(self):
        return self._output_events.iterkeys()

    @property
    def output_events(self):
        """|Events| that happen when this transitions occurs"""
        return self._output_events.itervalues()

    @name_error
    def output_event(self, port):
        return self._output_events[port]

    def add(self, element):
        if isinstance(element, StateAssignment):
            self._state_assignments[element.name] = element
        elif isinstance(element, OutputEvent):
            self._output_events[element.name] = element
        else:
            raise NineMLInvalidElementTypeException(
                "Could not add element of type '{}' to {} class"
                .format(element.__class__.__name__, self.__class__.__name__))

    def remove(self, element):
        if isinstance(element, StateAssignment):
            self._state_assignments.pop(element.name)
        elif isinstance(element, OutputEvent):
            self._output_events.pop(element.name)
        else:
            raise NineMLInvalidElementTypeException(
                "Could not remove element of type '{}' to {} class"
                .format(element.__class__.__name__, self.__class__.__name__))

    def bind(self, component_class):
        for output_event in self.output_events:
            output_event.bind(component_class)


class OnEvent(Transition):

    nineml_type = "OnEvent"
    defining_attributes = (Transition.defining_attributes + ('src_port_name',))

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_onevent(self, **kwargs)

    def __init__(self, src_port_name, state_assignments=None,
                 output_events=None, target_regime=None):
        """Constructor for ``OnEvent``

            :param src_port_name: The name of the |EventPort| that triggers
            this transition

            See ``Transition.__init__`` for the definitions of the remaining
            parameters.
        """
        Transition.__init__(self, state_assignments=state_assignments,
                            output_events=output_events,
                            target_regime=target_regime)
        self._src_port_name = src_port_name.strip()
        self._port = None
        ensure_valid_identifier(self._src_port_name)

    @property
    def src_port_name(self):
        return self._src_port_name

    @property
    def port(self):
        if self._port is None:
            raise NineMLRuntimeError(
                "OnEvent is not bound to a component class")
        return self._port

    def __repr__(self):
        return """OnEvent( %s )""" % self.src_port_name

    @property
    def _name(self):
        """
        This is included to allow OnEvents to be polymorphic with
        other named structures
        """
        return self.src_port_name

    def bind(self, component_class):
        super(OnEvent, self).bind(component_class)
        self._port = component_class.event_receive_port(self.src_port_name)
        self._port_name = None


class OnCondition(Transition):

    nineml_type = "OnCondition"
    defining_attributes = (Transition.defining_attributes + ('trigger',))

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_oncondition(self, **kwargs)

    def __init__(self, trigger, state_assignments=None,
                 output_events=None, target_regime=None):
        """Constructor for ``OnEvent``

            :param trigger: Either a |Trigger| object or a ``string`` object
                specifying the conditions under which this transition should
                occur.

            See ``Transition.__init__`` for the definitions of the remaining
            parameters.
        """
        if isinstance(trigger, Trigger):
            trigger = trigger.rhs
        self._trigger = Trigger(rhs=trigger)
        Transition.__init__(self, state_assignments=state_assignments,
                            output_events=output_events,
                            target_regime=target_regime)

    def __repr__(self):
        return 'OnCondition({})'.format(self.trigger.rhs)

    @property
    def trigger(self):
        return self._trigger

    @property
    def _name(self):
        """
        This is included to allow OnConditions to be polymorphic with
        other named structures
        """
        return self.trigger.rhs


class Trigger(BaseALObject, Expression):

    nineml_type = 'Trigger'

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_trigger(self, **kwargs)

    def __init__(self, rhs):
        BaseALObject.__init__(self)
        Expression.__init__(self, rhs)

    def __repr__(self):
        return "Trigger('%s')" % (self.rhs)

    @property
    def _name(self):
        """
        This is included to allow OnConditions to be polymorphic with
        other named structures
        """
        return self.rhs

    @property
    def reactivate_condition(self):
        negated = copy(self)
        negated.negate()
        return negated

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


from .visitors.queriers import DynamicsElementFinder  # @IgnorePep8
