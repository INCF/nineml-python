Serialization
=============

.. currentmodule:: nineml

All NineML Python objects can be written to file via their ``write`` method,
which simply wraps the object in a :ref:`Document` and
passes it to the ``nineml.write`` function (alternatively the ``nineml.write``
function can be called directly). NineML documents can be read from files
into :ref:`Document` objects using the ``nineml.read`` method, e.g.::

    >>> dynA =  nineml.Dynamics('A', ...)
    >>> dynA.write('example.xml')  # Alternatively nineml.write('example.xml', dynA, ...)
    >>> doc = nineml.read('example.xml')
    >>> dynA = doc['dynA']

Documents that are read or written to/from files will be cached in the
:ref:`Document` class unless the ``register`` keyword argument is set to
``False``.

.. autofunction:: read

.. autofunction:: write

NineML objects can also be serialized to string and/or basic Python objects
and back again using the ``serialize`` and ``unserialize`` methods depending
on the data format chosen (see Formats_). 

.. autofunction:: serialize

.. autofunction:: unserialize


Formats
-------

There are currently six supported formats for serialization with the NineML
Python library: XML_, YAML_, JSON_, HDF5_, `Python Pickle`_ and Python
dictionary (the JSON_, YAML_ and `Python Pickle`_ formats are derived from the
Python dictionary serializer). Noting that the serialization module is written
in a modular way that can support additional hierarchical formats if required
by deriving the ``BaseSerializer`` and ``BaseUnserializer`` classes.

Depending on the format used, NineML can be serialized to file, string or
standard Python objects (i.e dictionary or pickled dictionary).

+-------------------+------+--------+--------+
| Format            | File | String | Object |
+===================+======+========+========+
| XML_              | X    | X      | X      |
+-------------------+------+--------+--------+
| JSON_             | X    | X      |        |
+-------------------+------+--------+--------+
| YAML_             | X    | X      |        |
+-------------------+------+--------+--------+
| HDF5_             | X    |        |        |
+-------------------+------+--------+--------+
| `Python Pickle`_  | X    |        | X      |
+-------------------+------+--------+--------+
| Python dictionary |      |        | X      |
+-------------------+------+--------+--------+

.. note::
   Although the set of hierarchical object models that can be represented by
   XML_, JSON_/YAML_ and HDF5_ are very similar there are slight differences
   that prevent general one-to-one mappings between them. These issues,
   and how they are overcome are explained in the `Serialization`_ of the
   `NineML Specification`_.


Versions
--------

The NineML Python Library is fully interoperable with the NineML v1
syntax the v2 syntax currently under development. While this
will not be feasible as non-compatible features are added to v2, the aim is to
maintain full backwards compatibility with v1.

Referencing style
-----------------

References from one serialized NineML object to another can either be "local",
where both objects are contained in the same document, or "remote", where the
referenced object is in a different document to the object that references it.

Remote references enable large and complex models to be split across a number
of files, or to reference standardized models from the `NineML catalog`_ for
example. However, in some circumstances it may be desirable to copy all
references to the local document, for ease-of-portability or to reduce the
complexity of the read methods required by supporting tools.

The ``ref_style`` keyword argument can be used to control the referencing style
used when serializing NineML documents. Valid options are


local:
   All references are written locallly to the serialized document.
prefer:
   Objects are written as references where possible
inline:
   Objects are written inline where possible
None:
   Whether an object is written as a reference or inline is preserved from when
   the document was read
 

.. _XML: http://www.w3.org/XML/
.. _YAML: http://yaml.org
.. _HDF5: http://www.hdfgroup.org/HDF5/
.. _JSON: http://www.json.org/
.. _`Python Pickle`: https://docs.python.org/3/library/pickle.html
.. _`NineML specification`: http://nineml.net/specification/
.. _`NineML catalog`: http://github.com/INCF/nineml-catalog