==============
User layer API
==============

.. currentmodule:: nineml

A NineML model is made up of populations of cells, connected via synapses,
which may exhibit plasticity. The models for the cells, synapses and plasticity
mechanisms are all instances of subclasses of :class:`Component`. Populations
of cells are represented by :class:`Population`, the set of connections between
two populations by :class:`Projection`. Finally, the entire model is
encapsulated in :class:`Network`.

Components
==========

.. autoclass:: Component
   :members: component_class, properties, initial_values

.. autoclass:: DynamicsProperties

.. autoclass:: ConnectionRuleProperties

.. autoclass:: RandomDistributionProperties

References
==========

NineML has three closely-related objects used to refer to other NineML objects.
:class:`Definition` is used inside :class:`Component`\s to refer to abstraction
layer :class:`~nineml.abstraction.ComponentClass` definitions.
:class:`Prototype` is used inside :class:`Component`\s to refer to
previously-defined :class:`Component`\s. :class:`Reference` is used inside
:class:`Selection`\s to refer to :class:`Population` objects, and inside
:class:`Projection`\s to refer to :class:`Population`\s and
:class:`Selection`\s.

.. autoclass:: Definition
   :members: component_class

.. autoclass:: Prototype
   :members: component

.. autoclass:: Reference
   :members: user_object


Values and Physical Quantities
==============================

.. autoclass:: SingleValue

.. autoclass:: ArrayValue

.. autoclass:: RandomDistributionValue

.. autoclass:: Quantity


Properties
==========

.. autoclass:: Property
   :members: value, quantity

   .. attribute:: name

      The name of the parameter.

   .. attribute:: unit

      The units of the parameter.

   .. attribute:: value

      The value of the parameter (magnitude and units).

.. autoclass:: Initial

Populations
===========

.. autoclass:: Population
   :members:

.. autoclass:: Selection
   :members:

.. autoclass:: Concatenate
   :members:


Projections
===========

.. autoclass:: Projection
   :members:

.. autoclass:: AnalogPortConnection
   :members: sender, receiver

   .. attribute:: send_port

      The name of the send port.

   .. attribute:: receive_port

      The name of the receive or reduce port.


.. autoclass:: EventPortConnection
   :members: sender, receiver

   .. attribute:: send_port

      The name of the send port.

   .. attribute:: receive_port

      The name of the receive or reduce port.


Networks
========

.. autoclass:: Network
   :members:
