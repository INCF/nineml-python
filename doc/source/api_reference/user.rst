==============
User layer API
==============

.. currentmodule:: nineml.user

A NineML model is made up of populations of cells, connected via synapses,
which may exhibit plasticity. The models for the cells, synapses and plasticity
mechanisms are all instances of subclasses of :class:`Component`. Populations
of cells are represented by :class:`Population`, the set of connections between
two populations by :class:`Projection`. Finally, the entire model is
encapsulated in :class:`Network`.

Components
==========

.. currentmodule:: nineml.user

.. autoclass:: nineml.user.components.Component
   :members: component_class, properties, initial_values, diff

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


Properties and physical quantities
==================================

.. autoclass:: Property
   :members: is_single, is_array, is_random, value, quantity

   .. attribute:: name

      The name of the parameter.

   .. attribute:: unit

      The units of the parameter.

   .. attribute:: value

      The value of the parameter (magnitude and units).

.. autoclass:: InitialValue

.. currentmodule:: nineml.user.values

.. autoclass:: SingleValue

.. autoclass:: ArrayValue

.. autoclass:: ArrayValueRow

.. autoclass:: ExternalArrayValue

.. autoclass:: ComponentValue


.. currentmodule:: nineml.user

Populations
===========

.. autoclass:: Population
   :members: all_components

.. autoclass:: Selection
   :members:

.. autoclass:: Concatenate
   :members: items


Projections
===========

.. autoclass:: Projection
   :members: all_components

.. autoclass:: Delay

.. autoclass:: AnalogPortConnection
   :members: sender, receiver, send_class, receive_class

   .. attribute:: send_port

      The name of the send port.

   .. attribute:: receive_port

      The name of the receive or reduce port.


.. autoclass:: EventPortConnection
   :members: sender, receiver, send_class, receive_class

   .. attribute:: send_port

      The name of the send port.

   .. attribute:: receive_port

      The name of the receive or reduce port.


Networks
========

.. autoclass:: Network
   :members: add
