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
------------

.. autoclass:: Parameter
   :members:

Mathematics
-----------

When writing mathematical expressions, the Python NineML library uses a
notation similar to C/C++. That is::

    (3B + 1)V^2

is not valid, it should be written as::

    (3*B + 1) * V * V

The functions 'exp', 'sin', 'cos', 'log', 'log10', 'pow', 'sinh', 'cosh',
'tanh', 'sqrt', 'mod', 'sum', 'atan', 'asin', 'acos', 'asinh', 'acosh',
'atanh', 'atan2', 'uniform', 'binomial', 'poisson', 'exponential' can be used
in expressions, together with the constant 'pi'.


:mod:`dynamics` module
======================

.. autoclass:: Dynamics
   :members:

.. autoclass:: Regime
   :members:

.. autoclass:: TimeDerivative
   :members:

.. autoclass:: StateVariable
   :members:

.. autoclass:: Expression
   :members:

.. autoclass:: Alias
   :members:

.. autoclass:: Condition
   :members:

.. autoclass:: OnCondition
   :members:

.. autoclass:: OnEvent
   :members:

.. autoclass:: StateAssignment
   :members:

.. autoclass:: OutputEvent
   :members:

.. autoclass:: AnalogSendPort
   :members:

.. autoclass:: AnalogReceivePort
   :members:

.. autoclass:: AnalogReducePort
   :members:

.. autoclass:: EventSendPort
   :members:

.. autoclass:: EventReceivePort
   :members:


:mod:`connectionrule` module
============================

.. autoclass:: ConnectionRule
   :members:


:mod:`randomdistribution` module
================================

.. autoclass:: RandomDistribution
   :members:


