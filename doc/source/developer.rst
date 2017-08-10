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

The `NineML specification`_ states that all NineML objects can be annotated,
(except ``Annotations`` objects themselves). Therefore, all NineML-type classes
should derive from ``AnnotatedObject``, which itself derives from
``BaseNineMLObject``. This provides the ``annotations`` attribute, which can
provides access to any annotations associated with the object.

ContainerObject
~~~~~~~~~~~~~~~

"Container" NineML-type classes that contain sets of children, such as
:ref:`Dynamics`` (contains parameters, regimes, state-variables) or
:ref:`OnCondition` (contains state assignments and output events), should
derive from ``ContainerObject``. ``ContainerObject`` adds a number of methods,
including ``add``, ``remove``, and general iterators used to traverse the
object hierarchy.

Children of container objects should be stored with separate dictionary
attributes for each child type named::

    _<pluralized-lowercase-child-type>
    
Iterators and accessors
^^^^^^^^^^^^^^^^^^^^^^^

The container class also needs to define three iterator properties and one
accessor method following the conventions

<pluralized-lowercase-child-type>:
    A property that returns an iterator over all children in the dictionary
num_<pluralized-lowercase-child-type>:
    A property that returns the number of children in the dictionary:
<pluralized-lowercase-child-type>_names
    A property that returns an iterator over the keys of the dictionary.
    If the child type doesn't have a ``name`` attribute then the iterator
    should be named <pluralized-lowercase-nineml-type>_keys instead.
<lowercase-child-type>:
    An accessor that takes the name (or key) of a child and returns the child.

``class_to_member``
^^^^^^^^^^^^^^^^^^^

Container classes must also have a ``class_to_member`` attribute that maps the
name of the child type to the accessor method i.e. ``<lowercase-child-type>``.


DocumentLevelObject
~~~~~~~~~~~~~~~~~~~

All NineML-type classes that are permitted at the top level in NineML documents
(see :ref:`Document-level types`) need to derive from ``DocumentLevelObject``,
this provides ``document`` and ``url`` attribute properties and is also used
in checks at various points in the code.

Visitors
--------

Visitor patterns are used extensively within the abstraction layer sub-package
to validate, modify and analyze component classes, and more generally to
serialize all NineML-types and added units and dimensions to documents. As long
as the guidelines above are followed (i.e. derive from the appropriate base
classes and ``nineml_type``, ``defining_attributes``, etc... attributes), then
the visitors will be able to visit new NineML-types added to the library. 

Serialization
~~~~~~~~~~~~~

For serialization visitors to be able to serialize a NineML-type it needs to
define either ``serialize_node`` and ``unserialize_node`` or
``serialize_body`` and ``unserialize_body`` methods

``serialize_node``/``unserialize_node``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Both ``serialize_node`` and ``unserialize_node`` take a single argument, which
is a ``NodeToSerialize`` or ``NodeToUnSerialize`` node respectively. These
nodes wrap a serial element of the given serialization format (e.g.
``lxml.etree._Element`` for the ``XMLSerializer``) and provide convenient
methods for adding, or accessing, children, attributes and body elements to the
node. 

The node method calls then call format-specific method of the serialization
visitor to un/serialize the NineML objects.  However, in some cases (
particularly in some fiddly v1.0 syntax), the serialization visitor needs to
be accessed directly, which is available at ``node.visitor``.

 
Both ``serialize_node`` and ``unserialize_node`` should accept arbitrary
keyword arguments and pass them on to all calls made to methods of the nodes
and the visitor directly. However, these arguments are not currently used by
any of the current serializers.

``serialize_body``/``unserialize_body``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Simple NineML-types that just contain a single body element (e.g.
``SingleValue``) should implement ``serialize_body`` and ``unserialize_body``
instead of ``serialize_node`` and ``unserialize_node``. This is to allow
JSON and YAML formats to flatten the body into the sole value of the
element. ``serialize_node`` does not take any arguments (except the arbitrary
keyword arguments) and returns the value, and ``unserialize_node`` takes a
single value and return the type.

.. note::
    For data formats that support body elements (e.g. XML) these methods are
    not used directly in the visitors but are referenced in the default
    ``serialize_node`` and ``unserialize_node`` methods in the
    ``BaseNineMLObject`` class.  

    
.. _`NineML specification`: http://nineml.net/specification/