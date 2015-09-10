=====================
Common API
=====================

.. currentmodule:: nineml

The abstraction layer is intended to provide explicit mathematical descriptions of any components used in a
neuronal network model, where such components may be neuron models, synapse models, synaptic plasticity
algorithms, connectivity rules, etc.

The abstraction layer therefore has a modular structure, to support different types of components, and allow
extensions to the language. The current modules are:

    * dynamics - for describing hybrid dynamical systems, whose behaviour is governed both by differential equations
                 and by discontinuous events. Such systems are often used to model point neurons, synapses and
                 synaptic plasticity mechanisms.
    * connectionrule - a module containing several "built-in" connectivity rules ('all-to-all', etc.).
    * random - a module for specifying random distributions.
    * structure - a module for describing the spatial positioning of neurons (under development, not yet documented).


Common elements
===============

A number of elements are common across all modules.

Dimensions and units
--------------------

.. autoclass:: Dimension
   :members:

.. autoclass:: Unit
   :members:

A number of :class:`Dimension`\s and :class:`Unit`\ have been pre-defined, for example:

.. code-block:: python

    >>> from nineml.abstraction.units import time, voltage, capacitance, nA, mol_per_cm3, Mohm
    >>> voltage
    Dimension(name='voltage', i=-1, m=1, t=-3, l=2)
    >>> nA
    Unit(name='nA', dimension='current', power=-9)

