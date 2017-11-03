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

.. autoclass:: DynamicsProperties
   :members: component_class, properties, initial_values

.. autoclass:: ConnectionRuleProperties
   :members: component_class, properties

.. autoclass:: RandomDistributionProperties
   :members: component_class, properties

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
   :members: name, value, units, quantity

.. autoclass:: ArrayValue
   :members: name, value, units, quantity

.. autoclass:: RandomDistributionValue
   :members: name, value, units, quantity

.. autoclass:: Quantity
   :members: name, value, units, quantity


Properties
==========

.. autoclass:: Property
   :members: name, value, units, quantity

.. autoclass:: Initial
   :members: name, value, units, quantity

Populations
===========

.. autoclass:: Population
   :members: all_components, cell, component_class, component_classes, name, size

.. autoclass:: Selection
   :members: port, receive_port, send_port, name, populations, ports, size, operation

.. autoclass:: Concatenate
   :members: items, num_items, populations


Projections
===========

.. autoclass:: Projection
   :members: all_components, connections, connectivity, delay, name, plasticity, post, pre, response, port_connections

.. autoclass:: AnalogPortConnection
   :members: sender, receiver, send_port, receive_port


.. autoclass:: EventPortConnection
   :members: sender, receiver, send_port, receive_port


Networks
========

.. autoclass:: Network
   :members: all_components, delay_limits, flatten, name, scale, resample_connectivity, connectivity_has_been_sampled
