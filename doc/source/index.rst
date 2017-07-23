=====================
NineML Python library
=====================

NineML_ is a language for describing the dynamics and connectivity of neuronal
network simulations; in particular for large-scale simulations of many point
neurons.

The language is defined as an object model, described in the
`NineML specification`_, with standardized serializations to XML, JSON, YAML
and HDF5.

This documentation describes the :py:mod:`nineml` Python package, which
implements the NineML_ object model using Python classes, allowing models to be
created, edited, introspected, etc. using Python, and then written to/read from
the NineML_ XML format.

Users' guide
------------

.. toctree::
    :maxdepth: 2 
    
    motivation
    installation
    getting_started
    serialization
    al_structure
    overview
    hierarchical
    examples
    api_reference/index
    annotations
    getting_help
    releases/index

Developers' guide
-----------------

.. toctree::
    :maxdepth: 2

    contributing
    implementation


.. _NineML: http://nineml.net
.. _`NineML specification`: http://nineml.net/specification/
