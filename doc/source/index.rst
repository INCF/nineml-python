=================
NineML Python API
=================

NineML_ is a language for describing the dynamics and connectivity of neuronal network
simulations; in particular for large-scale simulations of many point neurons.

The language is defined as an object model, described in the `NineML specification`_,
with a standardized serialization as XML, although other serializations are possible.

This documentation describes the :py:mod:`nineml` Python package, which implements the
NineML object model using Python classes, allowing models to be created, edited, introspected, etc.
using Python, and then written to/read from the NineML XML format.

Users' guide
------------

.. toctree::
    :maxdepth: 2 
    
    motivation
    installation
    getting_started
    examples/index
    api_reference/index
    getting_help


Developers' guide
-----------------

.. toctree::
    :maxdepth: 2

    contributing
    implementation_reference



.. _NineML: http://nineml.net
.. _`NineML specification`: http://nineml.net/specification/
