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
ComponentClass->Dynamics/ConnectionRule, Projection, Quantity.

There are also cases where an element in the specification is a thin wrapper
around a body element, such as Delay, Size. 

MathInline expressions  



Features and methods
====================

All types
---------



Container types
---------------

NineML types that have child elements, i.e.

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
 
all derive from the ``ContainerObject`` class, which defines several useful
methods.

Document-level types
--------------------

  ``document`` and ``url`` attributes 


.. _`NineML specification`: http://nineml.net/specification/


