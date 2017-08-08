===================
Developer reference
===================

The structure NineML Python library aims to closely match the
`NineML specification`_, with each NineML "layer" represented by a
sub-package (i.e. ``nineml.abstraction`` and ``nineml.user``) and each NineML
type mapping to a separate Python "type" class with the exception of some
simple types that just contain a single element (e.g. Size, Pre, Post, etc...)

Base classes
------------

There are number of base classes that should be derived from when designing
NineML-type classes, which one(s) depend on the structure of the type, e.g.
whether the contain annotations, child elements, etc...

BaseNineMLObject
~~~~~~~~~~~~~~~~

All NineML-type classes should derive from ``BaseNineMLObject``. 

``BaseNineMLObject`` defines a number of common methods such as ``clone``,
``equals``, ... (see :ref:`NineML Types`). To get these methods to work there a
couple class attributes that need to be present in the deriving classes,
``nineml_type`` and ``defining_attributes``.

``nineml_type``
^^^^^^^^^^^^^^^

``nineml_type`` is a string containing the name of the
corresponding NineML type in the `NineML specification`_. If the name differs
between v1 and v2 of the specification the ``v1_nineml_type`` should also be
defined to hold the corresponding type in the v1 syntax.

``defining_attributes``
^^^^^^^^^^^^^^^^^^^^^^^

``defining_attributes`` is a tuple of strings, listing the attributes of
the given NineML-type class that contain data (both attributes and child
objects) that are part of the `NineML specification`_.

For "internal attributes" (i.e. ones starting with '_') that are exposed in
the public API via @property methods, the name of the @property method is
preferred, with the exception of dictionary attributes (see ContainerObject_)
that are exposed as iterators (so their keys can be compared within unittests). 

AnnotatedObject
~~~~~~~~~~~~~~~

All NineML objects can be annotated, except ``Annotations`` objects themselves.
Therefore all other NineML-type classes should derive from ``AnnotatedObject``,
which itself derives from ``BaseNineMLObject``.

ContainerObject
~~~~~~~~~~~~~~~

NineML-type classes that have sets of children of the same type (e.g.
``Regime`` children in ``Dynamics``, ``StateAssignment`` children in
``OnEvent``,...), should derive from ``ContainerObject``. Child object sets
should be stored in dictionaries named by::

    _<pluralized-lowercase-nineml-type>
    
The container class should then define three properties and one access methods
with the following conventions



<pluralized-lowercase-nineml-type>:
    A property that returns an iterator over all children in the dictionary
num_<pluralized-lowercase-nineml-type>:
    A property that returns the number of children in the dictionary:
<pluralized-lowercase-nineml-type>_names (or <pluralized-lowercase-nineml-type>_keys if the child type doesn't have a ``name`` attribute):
    A property that returns an iterator over the keys of the dictionary
<lowercase-nineml-type>:
    An access method that takes the name (or key) of a child and return the
    child.
 

``class_to_member``
^^^^^^^^^^^^^^^^^^^

DocumentLevelObject
~~~~~~~~~~~~~~~~~~~

All NineML-type classes that are permitted at the top level in NineML documents
(see :ref:`Document-level types`) need to derive from ``DocumentLevelObject``,
this provides ``document`` and ``url`` attribute properties and is also used
in checks at various points in the code.

Visitors
--------

Serialization
-------------

``serialize_node``
~~~~~~~~~~~~~~~~~~


``unserialize_node``
~~~~~~~~~~~~~~~~~~~~


``serialize_body``
~~~~~~~~~~~~~~~~~~


``unserialize_body``
~~~~~~~~~~~~~~~~~~~~



    
.. _`NineML specification`: http://nineml.net/specification/