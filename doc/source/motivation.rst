==========
Motivation
==========

Why NineML?
===========

NineML_ (or "9ML") is a language for describing the dynamics and connectivity of neuronal network
simulations; in particular for large-scale simulations of many point neurons (where the neuron model does
not explicitly represent dendrites).

At present, networks of point-neurons are typically simulated by writing either a custom
simulation program in a general-purpose programming language (such as Python, MATLAB)
or by writing a model for a particular simulator (NEURON_, NEST_, Brian_, etc.) As models
of neuronal dynamics and connectivity become more and more complex, writing a
simulation from scratch in Python or Matlab can become more and more complex, taking
time to debug and producing hard to find bugs. Writing simulator-specific models
can reduce some of this duplication, but this means the model will only run on a single simulator
and is hence difficult to share.

Programmatic model description APIs such as PyNN_ provide simulator independence at the expense of
(i) having to choose from a limited library of neuron models (note however that PyNN now works with
neuron/synapse models defined in NineML_, for certain simulators), (ii) being tied to a particular programming
language. Having access to a full programming language is also a temptation to writing over-complex,
difficult to maintain model descriptions when compared to a declarative language such as NineML_.

NineML_ tries to mitigate some of these problems by providing an language for
defining smaller components of a simulation in a declarative, language-independent way.
Various tools are then available for generating code for various simulators from this description
(see http://nineml.net/software).

.. note::  NineML_ and NeuroML_ version 2 are both languages for mathematically-explicit descriptions
           of biological neuronal network models. NineML_ currently works only for point-neuron/single-compartment
           neuron models, while NeuroML also supports multi-compartment, morphologically-detailed models.
           The two languages evolved in parallel, although with considerable cross-influence in both
           directions. It is possible they will merge in future; tools are under development to allow
           conversion between the formats where possible. Which one you should choose depends largely
           on what you want to do, and what tools are available for working with the two languages.


*Abstraction* and *User* Layers
===============================

In NineML_, the definition of a component is split into two parts;

Abstraction Layer
    Components on this layer can be thought of as parameterised models. For
    example, we could specify a general integrate-and-fire neuron, with a
    firing threshold, ``V_Threshold`` and a reset voltage ``V_Reset``. We are
    able to define the dynamics of the neuron in terms of these parameters.

User Layer
    In order to simulate a network, we need to take the *parameterised* models
    from the *Abstraction Layer*, fill in the parameters, and specify the
    number of each type of component we wish to simulate and how they should be
    connected. For example, we might specify for our neurons that
    ``V_Threshold`` was -45 mV and ``V_Reset`` was -60 mV.


The flow for a simulation using NineML_ would look like:

.. image::
    _static/images/AL_UL_Overview.png



An obvious question is *"Why do this?!"*

For a single, relatively simple simulation, it may not be worth the effort!
But imagine we are modelling a (relatively simple) network of neurons, which
contains five different types of neurons. The neurons synapse onto each other,
and there are three different classes of synapses, with different models for
their dynamics. If we were to implement this naively, we could potentially
copy and paste the same code 15 times, *for each simulator*. By factoring out
basic functionality, we make our workflow much more manageable.


The :mod:`nineml` Python library
================================

NineML_ is defined by an object model (the specification can be found at
nineml.net_), with standardized serializations to XML, JSON, YAML and HDF5.
The Python :mod:`nineml` library provides tools for reading and writing 
NineML_ models to and from the supported serialization formats and an API for 
building/introspecting/manipulating/validating NineML_ models in Python 
(including a shorthand notation for building NineML_ models). The library is
intended as a base for other Python tools working with NineML_, for example
tools for code generation.


.. _NineML: http://nineml.net
.. _NEURON: http://www.neuron.yale.edu/neuron/
.. _NEST: http://www.nest-simulator.org
.. _Brian: http://www.briansimulator.org
.. _PyNN: http://neuralensemble.org/PyNN/
.. _NeuroML: http://neuroml.org
.. _nineml.net: http://nineml.net/specification/nineml_version1.pdf