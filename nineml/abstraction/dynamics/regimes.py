"""
This file contains the main classes for defining dynamics

:copyright: Copyright 2010-2017 by the NineML Python team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from past.builtins import basestring
from itertools import chain
import re
import sympy
from nineml.utils import validate_identifier, assert_no_duplicates
from nineml.utils.iterables import (filter_discrete_types,
                                    normalise_parameter_as_list)
from nineml.exceptions import NineMLUsageError, name_error
from ..expressions import ODE
from .. import BaseALObject
from nineml.units import dimensionless, Dimension
from nineml.base import ContainerObject
from ..expressions import Alias, Expression  # @IgnorePep8
from .transitions import OnEvent, OnCondition, Trigger  # @IgnorePep8


class StateVariable(BaseALObject):

    """A class representing a state-variable in a ``Dynamics``.

    This was originally a string, but if we intend to support units in the
    future, wrapping in into its own object may make the transition easier
    """

    nineml_type = 'StateVariable'
    nineml_attr = ('name',)
    nineml_child = {'dimension': Dimension}

    def __init__(self, name, dimension=None):
        """StateVariable Constructor

        :param name:  The name of the state variable.
        """
        super(StateVariable, self).__init__()
        self._name = validate_identifier(name)
        self._dimension = dimension if dimension is not None else dimensionless
        assert isinstance(self._dimension, Dimension)
        validate_identifier(self._name)

    @property
    def name(self):
        return self._name

    @property
    def dimension(self):
        return self._dimension

    def set_dimension(self, dimension):
        self._dimension = dimension

    def __repr__(self):
        return ("StateVariable({}{})"
                .format(self.name,
                        ', dimension={}'.format(self.dimension.name)))

    def _sympy_(self):
        return sympy.Symbol(self.name)

    def serialize_node(self, node, **options):  # @UnusedVariable
        node.attr('name', self.name, **options)
        node.attr('dimension', self.dimension.name, **options)

    @classmethod
    def unserialize_node(cls, node, **options):  # @UnusedVariable
        name = node.attr('name', **options)
        dimension = node.visitor.document[node.attr('dimension', **options)]
        return cls(name=name, dimension=dimension)


class TimeDerivative(ODE, BaseALObject):
    """
    Represents a first-order, ordinary differential equation with respect to
    time.

    .. math::

        \\frac{dg}{dt} = \\frac{g}{gtau}

    Then this would be constructed as::

        TimeDerivative( variable='g', rhs='g/gtau' )

    Note that although initially the time variable
    (independent_variable) is ``t``, this can be changed using the
    methods: ``td.lhs_name_transform_inplace({'t':'T'} )`` for example.

    Parameters
    ----------
    variable : str
         The name of the variable.
    rhs : str | Expression | sympy.Basic
        The right-hand-side of the equation.

    For example, if our time derivative was:
    """

    nineml_type = 'TimeDerivative'
    nineml_attr = ('variable',) + ODE.nineml_attr

    def __init__(self, variable, rhs):
        ODE.__init__(self,
                     dependent_variable=variable,
                     independent_variable='t',
                     rhs=rhs)
        BaseALObject.__init__(self)

    @property
    def key(self):
        """
        This is included to allow Time-derivatives to be polymorphic with other
        named structures
        """
        return self.variable

    @property
    def variable(self):
        return self.dependent_variable

    def __repr__(self):
        return "TimeDerivative( d%s/dt = %s )" % \
            (self.variable, self.rhs)

    def str(self):
        return 'd-{}/dt := {}'.format(self.variable, self.rhs)

    @classmethod
    def from_str(cls, time_derivative_string):
        """Creates an TimeDerivative object from a string"""
        # Note: \w = [a-zA-Z0-9_]
        tdre = re.compile(r"""\s* d(?P<dependent_var>[a-zA-Z][a-zA-Z0-9_]*)/dt
                           \s* = \s*
                           (?P<rhs> .*) """, re.VERBOSE)

        match = tdre.match(time_derivative_string)
        if not match:
            err = "Unable to load time derivative: %s" % time_derivative_string
            raise NineMLUsageError(err)
        variable = match.groupdict()['dependent_var']
        rhs = match.groupdict()['rhs']
        return TimeDerivative(variable=variable, rhs=rhs)

    def serialize_node(self, node, **options):  # @UnusedVariable @IgnorePep8
        node.attr('variable', self.variable, **options)
        node.attr('MathInline', self.rhs_xml, in_body=True, **options)

    @classmethod
    def unserialize_node(cls, node, **options):  # @UnusedVariable
        variable = node.attr('variable', **options)
        expr = node.attr('MathInline', in_body=True, dtype=Expression,
                         **options)
        return cls(variable=variable, rhs=expr)


class Regime(BaseALObject, ContainerObject):
    """
    A Regime is something that contains TimeDerivatives, has temporal extent,
    defines a set of Transitions which occur based on |Conditions|, and can
    be join the Regimes to other Regimes.

    Parameters
    ----------
    name : str
        The name of the constructor. If none, then a name will
        be automatically generated.
    time_derivatives : list(TimeDerivative)
        A list of time derivatives, as
        either ``string``s (e.g 'dg/dt = g/gtau') or as
        |TimeDerivative| objects.
    transitions : list(Transition)
        A list containing either OnEvent or OnCondition objects, which will
        automatically be sorted into the appropriate classes automatically.
    on_conditions : list(OnCondition)
        A list containing either OnEvent or OnCondition objects, which will
        automatically be sorted into the appropriate classes automatically.
    on_events : list(OnEvent)
        A list containing either OnEvent or OnCondition objects, which will
        automatically be sorted into the appropriate classes automatically.
    \*args : list(TimeDerivative)
        Any non-keyword arguments will be treated as a TimeDerivative.
    """

    nineml_type = 'Regime'
    nineml_attr = ('name',)
    nineml_children = (TimeDerivative, OnEvent, OnCondition, Alias)

    _n = 0

    @classmethod
    def get_next_name(cls):
        """Return the next distinct autogenerated name
        """
        Regime._n = Regime._n + 1
        return 'Regime%d' % Regime._n

    def __init__(self, *args, **kwargs):
        BaseALObject.__init__(self)
        ContainerObject.__init__(self)
        valid_kwargs = ('name', 'transitions', 'on_events', 'on_conditions',
                        'time_derivatives', 'aliases')
        for arg in kwargs:
            if arg not in valid_kwargs:
                err = 'Unexpected Arg: %s' % arg
                raise NineMLUsageError(err)

        name = kwargs.get('name', None)
        if name is None:
            self._name = 'default'
        else:
            self._name = validate_identifier(name)
            validate_identifier(self._name)

        # Get Time derivatives from args or kwargs
        kw_tds = normalise_parameter_as_list(
            kwargs.get('time_derivatives', None))
        time_derivatives = list(args) + kw_tds
        # Un-named arguments are time_derivatives:
        time_derivatives = normalise_parameter_as_list(time_derivatives)
        # time_derivatives.extend( args )
        td_types = (basestring, TimeDerivative)
        td_type_dict = filter_discrete_types(time_derivatives, td_types)
        td_from_str = [TimeDerivative.from_str(o)
                       for o in td_type_dict[basestring]]
        time_derivatives = td_type_dict[TimeDerivative] + td_from_str
        # Check for double definitions:
        td_dep_vars = [td.variable for td in time_derivatives]
        assert_no_duplicates(
            td_dep_vars,
            ("Multiple time derivatives found for the same state variable "
                 "in regime '{}' (found '{}')".format(
                     self.name,
                     "', '".join(td.variable for td in time_derivatives))))
        self.add(*time_derivatives)

        # We support passing in 'transitions', which is a list of both OnEvents
        # and OnConditions as well as separate on_conditions and on_events.
        transitions = normalise_parameter_as_list(
            kwargs.get('transitions', None))
        self.add(*transitions)
        on_conditions = normalise_parameter_as_list(
            kwargs.get('on_conditions', None))
        self.add(*on_conditions)
        on_events = normalise_parameter_as_list(
            kwargs.get('on_events', None))
        self.add(*on_events)

        # Add regime specific aliases
        aliases = normalise_parameter_as_list(kwargs.get('aliases', None))
        self.add(*aliases)

    def add(self, *elements):
        """Add an element to the regime

        If the element is a transistion resolve references to target regime
        """
        for elem in elements:
            if isinstance(elem, (OnEvent, OnCondition)):
                elem.set_source_regime(self)
        super(Regime, self).add(*elements)

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, self.name)

    # Regime Properties:
    # ------------------
    @property
    def num_time_derivatives(self):
        return len(self._time_derivatives)

    @property
    def num_on_events(self):
        return len(self._on_events)

    @property
    def num_on_conditions(self):
        return len(self._on_conditions)

    @property
    def num_aliases(self):
        return len(self._aliases)

    @property
    def time_derivatives(self):
        """Returns the state-variable time-derivatives in this regime.

        .. note::

            This is not guaranteed to contain the time derivatives for all the
            state-variables specified in the component. If they are not
            defined, they are assumed to be zero in this regime.

        """
        return iter(self._time_derivatives.values())

    @property
    def on_events(self):
        """Returns all the transitions out of this regime trigger by events"""
        return iter(self._on_events.values())

    @property
    def on_conditions(self):
        """Returns all the transitions out of this regime trigger by
        conditions"""
        return iter(self._on_conditions.values())

    @property
    def aliases(self):
        return iter(self._aliases.values())

    @name_error
    def time_derivative(self, variable):
        return self._time_derivatives[variable]

    @name_error
    def on_event(self, port_name):
        return self._on_events[port_name]

    @name_error
    def on_condition(self, condition):
        if not isinstance(condition, sympy.Basic):
            condition = Trigger(condition).rhs
        return self._on_conditions[condition]

    @name_error
    def alias(self, name):
        return self._aliases[name]

    @property
    def time_derivative_variables(self):
        return iter(self._time_derivatives.keys())

    @property
    def time_derivative_keys(self):
        return self.time_derivative_variables

    @property
    def on_event_port_names(self):
        return iter(self._on_events.keys())

    @property
    def on_event_keys(self):
        return self.on_event_port_names

    @property
    def on_condition_triggers(self):
        return iter(self._on_conditions.keys())

    @property
    def on_condition_keys(self):
        return (Expression(t).rhs_str for t in self.on_condition_triggers)

    @property
    def alias_names(self):
        return iter(self._aliases.keys())

    @property
    def transitions(self):
        """Returns all the transitions leaving this regime.

        Returns an iterator over both the on_events and on_conditions of this
        regime"""

        return chain(self.on_events, self.on_conditions)

    def all_triggers(self):
        return (oc.trigger for oc in self.on_conditions)

    def all_target_triggers(self):
        return chain(*[[oc.trigger for oc in t.target_regime.on_conditions]
                       for t in self.transitions if t.target_regime != self])

    def all_state_assignments(self):
        return chain(*(t.state_assignments for t in self.transitions))

    @property
    def name(self):
        return self._name

    def no_time_derivatives(self, state_variables):
        """
        Returns the state variables from the list provided that don't have
        time derivatives in the current regime
        """
        return (sv for sv in state_variables
                if sv.name not in self.time_derivative_variables)

    def serialize_node(self, node, **options):
        node.attr('name', self.name, **options)
        node.children(self.time_derivatives)
        node.children(self.on_events)
        node.children(self.on_conditions)
        node.children(self.aliases)

    @classmethod
    def unserialize_node(cls, node, **options):
        return cls(name=node.attr('name', **options),
                      time_derivatives=node.children(TimeDerivative,
                                                     **options),
                      transitions=(node.children(OnEvent, **options) +
                                   node.children(OnCondition, **options)),
                      aliases=node.children(Alias, **options))
