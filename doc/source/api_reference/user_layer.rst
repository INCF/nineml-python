==============
User layer API
==============

.. currentmodule:: nineml.user

A NineML model is made up of populations of cells, connected via synapses, which may exhibit plasticity. The models for the cells, synapses and plasticity mechanisms are all instances of :class:`Component`. Populations of cells are represented by :class:`Population`, the set of connections between two populations by :class:`Projection`. Finally, the entire model is encapsulated in :class:`Network`.

Components
==========

.. autoclass:: Component
   :show-inheritance:

.. autoclass:: nineml.user.components.BaseComponent
   :members: component_class, properties, initial_values, diff

:class:`SpikingNodeType` and :class:`SynapseType` are subclasses of :class:`Component`. In the current version they
do not have any additional behaviour, but could potentially increase the readability of your Python script.

References
==========

NineML has three closely-related objects used to refer to other NineML objects. :class:`Definition` is used inside
:class:`Component`\s to refer to abstraction layer :class:`~nineml.abstraction.ComponentClass` definitions.
:class:`Prototype` is used inside :class:`Component`\s to refer to previously-defined :class:`Component`\s.
:class:`Reference` is used inside :class:`Selection`\s to refer to :class:`Population` objects, and inside
:class:`Projection`\s to refer to :class:`Population`\s and :class:`Selection`\s.

.. autoclass:: Definition
   :members: component_class

.. autoclass:: Prototype
   :members: component

.. autoclass:: Reference
   :members: user_object


Properties and physical quantities
==================================

.. note:: is Quantity in the spec?

.. autoclass:: Property
   :members: is_single, is_array, is_random, value, quantity

   .. attribute:: name

      The name of the parameter.

   .. attribute:: unit

      The units of the parameter.

   .. attribute:: quantity

      The value of the parameter (magnitude and units).

.. currentmodule:: nineml.user.values

.. autoclass:: SingleValue

.. autoclass:: ArrayValue

.. autoclass:: ArrayValueRow

.. autoclass:: ExternalArrayValue

.. autoclass:: ComponentValue


.. currentmodule:: nineml.user

.. autoclass:: RandomDistribution

.. autoclass:: InitialValue

.. autoclass:: PropertySet
   :members: complete, get_random_distributions

.. autoclass:: InitialValueSet
   :members: complete, get_random_distributions

Populations
===========

.. autoclass:: Population
   :members: get_components

.. autoclass:: Selection
   :members:

.. autoclass:: Concatenate
   :members: items

Spatial structure
=================

.. autoclass:: PositionList
   :members: get_positions

.. autoclass:: Structure
   :members: generate_positions


Projections
===========

.. autoclass:: Projection
   :members: get_components

.. autoclass:: Delay

.. autoclass:: PortConnection
   :members: sender, receiver, send_class, receive_class

   .. attribute:: send_port

      The name of the send port.

   .. attribute:: receive_port

      The name of the receive or reduce port.

Networks
========

.. autoclass:: Network
   :members: add
