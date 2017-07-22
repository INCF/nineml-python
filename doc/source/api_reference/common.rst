==========
Common API
==========

A number of elements are common across all modules.

Document
--------

.. autoclass:: Document
    :members:


Dimensions and units
--------------------

.. autoclass:: Dimension
   :members:

.. autoclass:: Unit
   :members:

A number of :class:`Dimension`\s and :class:`Unit`\ have been pre-defined,
for example:

.. code-block:: python

    >>> from nineml.abstraction.units import time, voltage, capacitance, nA, mol_per_cm3, Mohm
    >>> voltage
    Dimension(name='voltage', i=-1, m=1, t=-3, l=2)
    >>> nA
    Unit(name='nA', dimension='current', power=-9)

