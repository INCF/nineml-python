================
Common Types API
================

There a few NineML types are common across all layers


.. currentmodule:: nineml

Document
--------

.. autoclass:: Document
    :members: add, remove, as_network, pop, elements, url, values, items, keys


Dimensions and units
--------------------

.. autoclass:: Dimension
   :members: power, to_SI_units_str, amount, current, length, luminous_intensity, temperature, time, i, j, k, l, m, n, t, origin

.. autoclass:: Unit
   :members: to_SI_units_str, dimension, name, offset, power, symbol


A number of :class:`Dimension`\s and :class:`Unit`\ have been pre-defined,
in the ``nineml.units`` module, for example:

.. code-block:: python

    >>> from nineml.units import time, voltage, capacitance, nA, mol_per_cm3, Mohm
    >>> voltage
    Dimension(name='voltage', i=-1, m=1, t=-3, l=2)
    >>> nA
    Unit(name='nA', dimension='current', power=-9)

Dimension and units implement multiplication/division operators to allow the
quick creation of compound units and dimensions

.. code-block:: python
    
    >>> from nineml.units import mV, ms
    >>> mV / ms
    Unit(name='mV_per_ms', dimension='voltage_per_time', power=0)