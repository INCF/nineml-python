=====================
Abstraction layer API
=====================

.. currentmodule:: nineml.abstraction

The abstraction layer is intended to provide explicit mathematical descriptions
of any components used in a neuronal network model, where such components may
be neuron models, synapse models, synaptic plasticity algorithms, connectivity
rules, etc.

The abstraction layer therefore has a modular structure, to support different
types of components, and allow extensions to the language. The current modules
are:

    dynamics:
        for describing hybrid dynamical systems, whose behaviour is
        governed both by differential equations and by discontinuous events.
        Such systems are often used to model point neurons, synapses and
        synaptic plasticity mechanisms.
    connectionrule:
        a module containing several "built-in" connectivity rules
        ('all-to-all', etc.).
    randomdistribution:
        a module for specifying random distributions.

Common types
============

.. autoclass:: Parameter
   :members: name, dimension, set_dimension

Mathematics
===========

Mathematical expressions are stored in Sympy_ objects throughout the Python
NineML library. However, they are typically constructed by passing a string
representation to a derived class of the ``Expression`` class (
e.g. ``Trigger``, ``Alias``). The Sympy_ string parsing has been slightly
extended to handle the ANSI-C-based format in the NineML specification, such as
using the caret symbol to signify raising to the power of (Sympy_ uses the
Python syntax of '**' to signify raising to the power of), e.g::

    (3 * B + 1) * V ^ 2

.. note::
    Currently, trigonometric functions are parsed as generic functions but this
    is planned to change in later versions of the library to use in-built
    Sympy_ functions. For the most part this will not have much effect on the
    represented expressions but in some cases it may prevent Sympy_'s solving
    and simplifying algorithms from making use of additional assumptions.

.. autoclass:: Expression
   :members: negate, expand_integer_powers, rhs_name_transform_inplace, rhs_str_substituted, rhs_suffixed, simplify, subs, rhs_as_python_func, rhs_atoms, rhs_cstr, rhs_funcs, rhs_random_distributions, rhs_str, rhs_symbol_names, rhs_symbols

:mod:`dynamics` module
======================

.. autoclass:: Dynamics
   :members: all_on_conditions, all_on_events, all_output_analogs, all_time_derivatives, all_transitions, dimension_of, find_element, is_random, is_flat, is_linear, rename_symbol, overridden_in_regimes, required_for, substitute_aliases, validate, all_expressions, regimes, state_variables, parameters, analog_receive_ports, analog_reduce_ports, analog_send_ports, event_send_ports, event_receive_ports

.. autoclass:: Alias
   :members: from_str, is_alias_str, name

Ports
-----

.. autoclass:: AnalogSendPort
   :members: name, is_incoming, can_connect_to, dimension

.. autoclass:: AnalogReceivePort
   :members: name, is_incoming, can_connect_to, dimension

.. autoclass:: AnalogReducePort
   :members: name, is_incoming, can_connect_to, dimension, operator

.. autoclass:: EventSendPort
   :members: name, is_incoming, can_connect_to

.. autoclass:: EventReceivePort
   :members: name, is_incoming, can_connect_to

Time derivatives
----------------

.. autoclass:: Regime
   :members: all_state_assignments, all_target_triggers, add, remove, find_element, no_time_derivatives, time_derivatives, on_conditions, on_events

.. autoclass:: TimeDerivative
   :members: variable, from_str, rhs, key

.. autoclass:: StateVariable
   :members: set_dimension, dimension, name

Transitions
-----------

.. autoclass:: OnEvent
   :members: src_port_name, port, target_regime, source_regime, target_regime_name, set_target_regime, set_source_regime, state_assignments, output_events

.. autoclass:: OnCondition
   :members: trigger, target_regime, source_regime, target_regime_name, set_target_regime, set_source_regime, state_assignments, output_events

.. autoclass:: Trigger
   :members: reactivate_condition, crossing_time_expr, key

.. autoclass:: StateAssignment
   :members: variable, from_str

.. autoclass:: OutputEvent
   :members: port, port_name


:mod:`connectionrule` module
============================

.. autoclass:: ConnectionRule
   :members: standard_library, standard_types


:mod:`randomdistribution` module
================================

.. autoclass:: RandomDistribution
   :members: standard_library, standard_types


.. _SymPy: http://www.sympy.org/
