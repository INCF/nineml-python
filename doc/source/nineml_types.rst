============
NineML Types
============

Relationship to specification
=============================

There is a near one-to-one mapping between NineML types as defined in the
`NineML specification`_ and classes in the ``nineml`` Python package.

The most significant exceptions are classes in the ``nineml`` package that are
modelled on proposed changes to the `NineML specification`_
(see http://github.com/INCF/nineml-spec/issues), e.g.
ComponentClass->:ref:`Dynamics`/:ref:`ConnectionRule`, :ref:`Projection`,
:ref:`Quantity`.

There are also cases where a type in the specification is just a thin wrapper
around a body element (e.g. Delay, Size), which are "flattened" to be
attributes in the NineML Python Library. 

Mathematical expressions
------------------------

All expressions in the NineML Python Library are represented using Sympy_
objects. Whereas in the `NineML Specification`_ mathematical expressions are
specified to be enclosed within `MathInline` elements (with a subset of
`MathML` planned as an alternative in future versions), in the NineML Python
Library the Sympy_ object representing is accessed via the ``rhs`` property
of the relevant objects.


Common properties/methods
=========================

All types
---------

All NineML types in the NineML Python Library derive from ``BaseNineMLObject``,
which adds some common methods.


.. currentmodule:: nineml.base

.. autoclass:: BaseNineMLObject
    :members: equals, find_mismatch, key, sort_key, clone, write, serialize, unserialize  

Document-level types
--------------------

There are 12 types that are permitted in the root of a NineML document

 * Dynamics
 * DynamicsProperties
 * ConnectionRule
 * ConnectionRuleProperties
 * RandomDistribution
 * RandomDistribution
 * Population
 * Projection
 * Selection
 * Network
 * Unit
 * Dimension

Instances of these types has a ``document`` property to access the document it
belongs to and a ``url`` property to access the url of the document. If the
instance has not been added to a document then they will return ``None``.


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
        Property that returns an iterator over the keys of child elements that
        are used to store the child in the internal dictionary. If
        the child type has a name, then the access will be
        ``<child-type>_names``, otherwise it will be ``<child-type>_keys``
        (e.g. ``alias_names``, ``parameter_names``, ``on_condition_keys``)
    ``num_<child-type-plural>``:
        Property that returns the number child elements in the container
    ``<child-type>``:
        Accessor method that takes the name/key of the child type and returns
        the corresponding element in the container.

There are a number of standard methods for container types


.. currentmodule:: nineml.base

.. autoclass:: ContainerObject
   :members: add, remove, elements, element, num_elements, element_keys, index_of, from_index, parent, document 

 
Annotations
-----------

All NineML elements can be annotated (except Annotations themselves) via their
``annotations`` property. The ``annotations`` property returns an ``Annotations``
element, with several convenient methods for setting attributes of nested
elements.


.. currentmodule:: nineml.annotations

.. autoclass:: Annotations
    :members: set, get, add, pop, delete, empty

.. _`NineML specification`: http://nineml.net/specification/
.. _Sympy: http://sympy.org/

