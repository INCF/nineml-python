============
NineML Types
============

.. currentmodule:: nineml

Relationship to specification
=============================

There is a near one-to-one mapping between NineML types as defined in the
`NineML specification`_ and classes in the ``nineml`` Python package.

The most significant exceptions are classes in the ``nineml`` package that are
modelled on proposed changes to the `NineML specification`_
(see http://github.com/INCF/nineml-spec/issues), e.g.
ComponentClass->Dynamics/ConnectionRule, Projection, Quantity.

There are also cases where an element in the specification is a thin wrapper
around a body element, such as Delay, Size. 

MathInline expressions  



Generic features and methods
============================

All types
---------

Methods:

 * equals
 * find_mismatch
 * key
 * sort_key
 * clone
 * write
 * serialize
 * unserialize

Document-level types
--------------------

 * document
 * url


Container types
---------------

NineML types that can have multiple child elements of one or more types, i.e.:

 * Dynamics
 * ConnectionRule
 * RandomDistribution
 * DynamicsProperties
 * ConnectionRuleProperties
 * RandomDistributionProperties
 * Regime
 * OnEvent
 * OnCondition
 * Network
 * Selection
 
derive from the ``ContainerObject`` class, which defines several
methods to accessing, adding and removing their children. Internally, each
child is stored in a dictionary according to its type. However, access to
children is provided through four standardised accessor methods for each
child type the container can hold:

    ``<child-type-plural>``:
        Property that returns an iterator over child elements of the given
        type (e.g. ``aliases``, ``parameters``, ``on_conditions``)
    ``<child-type>_names/keys``:
        Property that returns an iterator over the names of child elements.
        (e.g. ``alias_names``, ``parameter_names``, ``on_condition_keys``)
    ``num_<child-type-plural>``:
        Property that returns the number child elements in the container
    ``<child-type>``:
        Accessor method that takes the name/key of the child type and returns
        the corresponding element in the container.

 * add
 * remove
 * elements
 * element
 * num_elements
 * element_keys
 * index_of
 * from_index
 * parent
 * document
 
Annotations
-----------

All NineML types can be annotated (except Annotations themselves) via their
``annotations`` property.

.. autoclass:: Annotations
    :members: set, get, add, pop, delete, empty

.. _`NineML specification`: http://nineml.net/specification/


