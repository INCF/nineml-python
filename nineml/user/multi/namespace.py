"""
A module containing wrappers for abstraction layer elements that
append the namespace of a sub component to every identifier to avoid
name clashes in the global scope
"""
import re
import sympy
from ..component import Property
from nineml.abstraction import (
    Alias, TimeDerivative, Regime, OnEvent, OnCondition, StateAssignment,
    Trigger, OutputEvent, StateVariable, Constant, Parameter)
from nineml.exceptions import NineMLImmutableError, NineMLNamespaceError
from nineml.abstraction.expressions import reserved_identifiers


# Matches multiple underscores, so they can be escaped by appending another
# underscore (double underscores are used to delimit namespaces).
multiple_underscore_re = re.compile(r'(.*)(__+)()')
# Match only double underscores (no more or less)
double_underscore_re = re.compile(r'(?<!_)__(?!_)')
# Match only triple underscores (no more or less)
triple_underscore_re = re.compile(r'(?<!_)___(?!_)')
# Match more than double underscores to reverse escaping of double underscores
# in sub-component suffixes by adding an additional underscore.
more_than_double_underscore_re = re.compile(r'__(_+)')
# Match more than double underscores to reverse escaping of double underscores
# in sub-component suffixes by adding an additional underscore.
more_than_triple_underscore_re = re.compile(r'___(_+)')


def append_namespace(identifier, namespace):
    """
    Appends a namespace to an identifier in such a way that it avoids name
    clashes and the two parts can be split again using 'split_namespace'
    """
    # Since double underscores are used to delimit namespaces from names
    # within the namesapace (and 9ML names are not allowed to start or end
    # in underscores) we append an underscore to each multiple underscore
    # to avoid clash with the delimeter in the suffix
    return (str(identifier) + '__' +
            multiple_underscore_re.sub(r'\1\2_\3', namespace))


def split_namespace(identifier_in_namespace):
    """
    Splits an identifer and a namespace that have been concatenated by
    'append_namespace'
    """
    parts = double_underscore_re.split(identifier_in_namespace)
    if len(parts) < 2:
        raise NineMLNamespaceError(
            "Identifier '{}' does not belong to a sub-namespace")
    name = '__'.join(parts[:-1])
    comp_name = parts[-1]
    comp_name = more_than_double_underscore_re.sub('_\1', comp_name)
    return name, comp_name


def make_delay_trigger_name(port_conn):
    """
    Creates a name for a delay trigger statevariable from a given event port
    connection object
    """
    parts = (
        (port_conn.sender_role
         if port_conn.sender_role is not None else port_conn.sender_name),
        port_conn.send_port_name,
        (port_conn.receiver_role
         if port_conn.receiver_role is not None else port_conn.receiver_name),
        port_conn.receive_port_name)
    return ('___'.join(multiple_underscore_re.sub(r'\1\2__\3', p)
                       for p in parts)
            + '___delay_trigger')


def split_delay_trigger_name(name):
    parts = triple_underscore_re.split(name)[:-1]
    return [more_than_triple_underscore_re.sub('_\1', p) for p in parts]


def make_regime_name(sub_regimes_dict):
    sorted_keys = sorted(sub_regimes_dict.iterkeys())
    return '___'.join(
        multiple_underscore_re.sub(
            r'\1\2__\3', sub_regimes_dict[k].relative_name)
        for k in sorted_keys) + '___regime'


def split_multi_regime_name(name):
    parts = triple_underscore_re.split(name)[:-1]
    return [more_than_triple_underscore_re.sub('_\1', p) for p in parts]


class _NamespaceObject(object):

    defining_attributes = ('_sub_component', '_object')

    def __init__(self, sub_component, element, parent):
        self._sub_component = sub_component
        self._object = element
        self._parent = parent

    def __hash__(self):
        return (hash(self.sub_component) ^ hash(self._object)
                ^ hash(self._parent))

    @property
    def sub_component(self):
        return self._sub_component


class _NamespaceNamed(_NamespaceObject):
    """
    Abstract base class for wrappers of abstraction layer objects with names
    """

    @property
    def name(self):
        return self.sub_component.append_namespace(self._object.name)

    @property
    def _name(self):
        return self.name

    @property
    def relative_name(self):
        return self._object.name


class _NamespaceExpression(_NamespaceObject):

    @property
    def lhs(self):
        return self._object.lhs

    def lhs_name_transform_inplace(self, name_map):
        raise NineMLImmutableError(
            "Cannot change LHS of expression in global namespace of "
            "multi-component element. The multi-component elemnt should either"
            " be flattened or the substitution should be done in the "
            "sub-component")

    @property
    def rhs(self):
        """Return copy of rhs with all free symols suffixed by the namespace"""
        try:
            return self._object.rhs.xreplace(dict(
                (s, sympy.Symbol(append_namespace(s, self.sub_component.name)))
                for s in self._object.rhs.free_symbols
                if str(s) not in reserved_identifiers))
        except AttributeError:  # If rhs has been simplified to ints/floats
            assert float(self._object.rhs)
            return self.rhs

    @rhs.setter
    def rhs(self, rhs):
        raise NineMLImmutableError(
            "Cannot change expression in global namespace of "
            "multi-component element. The multi-component elemnt should either"
            " be flattened or the substitution should be done in the "
            "sub-component")

    def rhs_name_transform_inplace(self, name_map):
        raise NineMLImmutableError(
            "Cannot change expression in global namespace of "
            "multi-component element. The multi-component elemnt should either"
            " be flattened or the substitution should be done in the "
            "sub-component")

    def rhs_substituted(self, name_map):
        raise NineMLImmutableError(
            "Cannot change expression in global namespace of "
            "multi-component element. The multi-component elemnt should either"
            " be flattened or the substitution should be done in the "
            "sub-component")

    def subs(self, old, new):
        raise NineMLImmutableError(
            "Cannot change expression in global namespace of "
            "multi-component element. The multi-component elemnt should either"
            " be flattened or the substitution should be done in the "
            "sub-component")

    def rhs_str_substituted(self, name_map={}, funcname_map={}):
        raise NineMLImmutableError(
            "Cannot change expression in global namespace of "
            "multi-component element. The multi-component elemnt should either"
            " be flattened or the substitution should be done in the "
            "sub-component")


class _NamespaceDimensioned(object):

    @property
    def dimension(self):
        return self._object._dimension


class _NamespaceTransition(_NamespaceNamed):

    @property
    def target_regime(self):
        return _NamespaceRegime(self.sub_component,
                                self._object.target_regime,
                                self._parent._parent)

    @property
    def target_regime_name(self):
        return append_namespace(self._object.target_regime_name,
                                self.sub_component.name)

    @property
    def state_assignments(self):
        return (_NamespaceStateAssignment(self.sub_component, sa, self)
                for sa in self._object.state_assignments)

    @property
    def output_events(self):
        return (_NamespaceOutputEvent(self.sub_component, oe, self)
                for oe in self._object.output_events)

    def state_assignment(self, name):
        return _NamespaceStateAssignment(
            self.sub_component, self._object.state_assignment(name), self)

    def output_event(self, name):
        return _NamespaceOutputEvent(
            self.sub_component, self._object.output_event(name), self)

    @property
    def num_state_assignments(self):
        return self._object.num_state_assignments

    @property
    def num_output_events(self):
        return self._object.num_output_events


class _NamespaceOnEvent(_NamespaceTransition, OnEvent):

    @property
    def src_port_name(self):
        return self._object.src_port_name


class _NamespaceOnCondition(_NamespaceTransition, OnCondition):

    @property
    def trigger(self):
        return _NamespaceTrigger(self.sub_component,
                                 self._object.trigger, self)


class _NamespaceTrigger(_NamespaceExpression, Trigger):
    pass


class _NamespaceOutputEvent(_NamespaceObject, OutputEvent):

    @property
    def port_name(self):
        return append_namespace(self._object.port_name,
                                self.sub_component.name)

    @property
    def relative_port_name(self):
        return self._object.port_name


class _NamespaceStateVariable(_NamespaceNamed, _NamespaceDimensioned,
                              StateVariable):
    pass


class _NamespaceAlias(_NamespaceNamed, _NamespaceExpression, Alias):

    @property
    def lhs(self):
        return self.name


class _NamespaceParameter(_NamespaceNamed, _NamespaceDimensioned, Parameter):

    def _sympy_(self):
        return sympy.Symbol(self.name)


class _NamespaceConstant(_NamespaceNamed, Constant):
    pass


class _NamespaceTimeDerivative(_NamespaceNamed, _NamespaceExpression,
                               TimeDerivative):

    @property
    def variable(self):
        return append_namespace(self._object.variable,
                                self._sub_component.name)


class _NamespaceStateAssignment(_NamespaceNamed, _NamespaceExpression,
                                StateAssignment):

    @property
    def lhs(self):
        return self.name


class _NamespaceProperty(_NamespaceNamed, Property):
    pass


class _NamespaceRegime(_NamespaceNamed, Regime):

    @property
    def time_derivatives(self):
        return (_NamespaceTimeDerivative(self.sub_component, td, self)
                for td in self._object.time_derivatives)

    @property
    def aliases(self):
        return (_NamespaceAlias(self.sub_component, a, self)
                for a in self._object.aliases)

    @property
    def on_events(self):
        return (_NamespaceOnEvent(self.sub_component, oe, self)
                for oe in self._object.on_events)

    @property
    def on_conditions(self):
        return (_NamespaceOnCondition(self.sub_component, oc, self)
                for oc in self._object.on_conditions)

    def time_derivative(self, name):
        return _NamespaceTimeDerivative(self.sub_component,
                                        self._object.time_derivative(name),
                                        self)

    def alias(self, name):
        return _NamespaceAlias(self.sub_component, self._object.alias(name),
                               self)

    def on_event(self, name):
        return _NamespaceOnEvent(self.sub_component,
                                 self._object.on_event(name), self)

    def on_condition(self, name):
        return _NamespaceOnCondition(self.sub_component,
                                     self._object.on_condition(name), self)

    @property
    def num_time_derivatives(self):
        return self._object.num_time_derivatives

    @property
    def num_aliases(self):
        return self.num_object.aliases

    @property
    def num_on_events(self):
        return self._object.num_on_events

    @property
    def num_on_conditions(self):
        return self._object.num_on_conditions
