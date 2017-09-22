===================
Developer reference
===================

The structure NineML Python library aims to closely match the
`NineML specification`_, with each NineML "layer" represented by a
sub-package (i.e. ``nineml.abstraction`` and ``nineml.user``) and each NineML
type mapping to a separate Python class, with the exception of some
simple types that just contain a single element (e.g. Size) or are used just to
provide a name to a singleton child class (e.g. Pre, Post, etc...).

Base classes
------------

There are number of base classes that should be derived from when designing
NineML classes, which one(s) depend on the structure of the type, e.g.
whether the contain annotations, child elements, or can be placed at the
top-level of a NineML document.

BaseNineMLObject
~~~~~~~~~~~~~~~~

All classes that represent objects in the "NineML object model" should derive
from ``BaseNineMLObject``.

``BaseNineMLObject`` defines a number of common methods such as ``clone``,
``equals``, ``write``, etc... (see :ref:`NineML Types`). As well as default
values for class attributes that are required for all NineML classes,
``nineml_type``, ``nineml_attr``, ``nineml_child``, ``nineml_children``.
These class attributes match the structure of the `NineML specification`_ and
are used extensively within the visitor architecture (including
serialization).  

nineml_type
^^^^^^^^^^^

``nineml_type`` should be a string containing the name of the
corresponding NineML type in the `NineML specification`_.

nineml_type_v1
^^^^^^^^^^^^^^

If the nineml_type differs between v1 and v2 of the specification,
``nineml_type_v1`` should also be defined to hold the name of the type
in the v1 syntax.

nineml_attr
^^^^^^^^^^^

``nineml_attr`` should be a tuple of strings, listing the
attributes of the given NineML class that are part of the
`NineML specification`_ and are not NineML types themselves, such as ``str``,
``int`` and ``float`` fields.

nineml_child
^^^^^^^^^^^^

``nineml_child`` should be a dictionary, which lists the names of singleton
NineML child attributes in the class along with a mapping to their
expected class. If the the child attribute can be one of several NineML
classes then the attribute should map to None.

nineml_children
^^^^^^^^^^^^^^^

``nineml_children`` should be a tuple listing the NineML classes that
are contained within the object as children sets (e.g. ``(Property, Initial)``
for the ``DynamicsProperties`` class). Note that if a class has
non-empty ``nineml_children`` it should derive from ``ContainerObject``.

.. note:
    ``classproperty`` decorators can be used to define ``nineml_child`` and
    ``nineml_children`` class attributes to avoid circular definitions.
    See the ``BaseAnnotations`` class.
    
temporary
^^^^^^^^^

"Temporary" NineML objects are created when calling iterator properties and
accessor methods of the ``MultiDynamics`` class that override corresponding in
the ``Dynamics`` class, allowing ``MultiDynamics`` objects to duck-type (i.e.
pretend to be) ``Dynamics`` objects. Such classes should override the
``temporary`` class attribute and set it to ``True``. This prevents their
address in memory being used to identify the object (e.g. in the cloner "memo"
dictionary) as it since they are generated on the fly, this address will change
between accesses.

.. note::
    The ``id`` property in BaseNineMLObject should always be used to check
    whether two Python objects are the representing the same NineML object for
    this reason.
   

AnnotatedObject
~~~~~~~~~~~~~~~

The `NineML specification`_ states that all NineML objects can be annotated
except ``Annotations`` objects themselves. Therefore, all bar ``Annotations``
NineML classes should derive from ``AnnotatedObject``, which itself derives
from ``BaseNineMLObject``. This provides the ``annotations`` attribute, which
can provides access to any annotations associated with the object.

ContainerObject
~~~~~~~~~~~~~~~

"Container classes" are classes that contain sets of children, such as
:ref:`Dynamics`` (contains parameters, regimes, state-variables) or
:ref:`OnCondition` (contains state assignments and output events), as opposed
to classes that have nested singleton objects such as :ref:`Dimension` objects
in :ref:`Parameter` objects. Such classes should derive from ``ContainerObject``.

``ContainerObject`` adds a number of convenient methods, including ``add``,
``remove``, and general iterators used to traverse the object hierarchy.

The ``ContainerObject.__init__`` method creates an ``OrderedDict`` for each
child set with the name supplied by the child class' ``_children_dict_name``
method (which is ``_<pluralized-lowercase-child-type>`` by default).
    
Iterators and accessors
^^^^^^^^^^^^^^^^^^^^^^^

Container classes need to define three iterator properties and one
accessor method for each children-set, corresponding to the method names
supplied by the class methods in the child class, ``_children_iter_name``,
``_num_children_name``, ``_children_keys_name`` and ``_child_accessor_name``.
By default the method names returned by these class methods will be
*<pluralized-lowercase-nineml_type>*, *num_<pluralized-lowercase-nineml_type>*,
*<pluralized-lowercase-nineml_type>_names*, and *<lowercase-nineml_type>*
respectively. These properties/method should return:

*children_iter*:
    A property that returns an iterator over all children in the dictionary
*num_children* :
    A property that returns the number of children in the dictionary:
*children_keys*:
    A property that returns an iterator over the keys of the dictionary.
    If the child type doesn't have a ``name`` attribute then the iterator
    should be named <pluralized-lowercase-nineml-type>_keys instead.
*child_accessor*:
    An accessor that takes the name (or key) of a child and returns the child.

.. note::
    It would be possible to implement these properties/methods in the
    ``ContainerObject`` base class using ``__getattr__`` but since they are
    part of the public API that could be confusing to the user. 

DocumentLevelObject
~~~~~~~~~~~~~~~~~~~

All NineML classes that are permitted at the top level in NineML documents
(see :ref:`Document-level types`) need to derive from ``DocumentLevelObject``,
this provides ``document`` and ``url`` attribute properties and is also used
in checks at various points in the code.

Visitors
--------

Visitor patterns are used extensively within the NineML Python to find,
validate, modify and analyze NineML structures, including their serialization.

Base Visitors
~~~~~~~~~~~~~

Visitor base classes are found in the ``nineml.visitors.base`` module,
which search the object hierarchy and perform an "action" each object. These
visitors use the ``nineml_*`` class attributes (see BaseNineMLObject_) to
navigate the object hierarchy and therefore can be used search to any NineML
object.

If not overridden, the action method applied to each object will first check
whether a specialized method for that type of object called
``action_<lowercase-nineml_type>`` has been implemented and call it if it
has, otherwise call ``default_action`` method. Note that if specialized methods
are not required then the visitor can just override the ``action`` method
directly.

There are a number of different base visitor classes to derive from depending
on the requirements of the visitor pattern in question.

BaseVisitor
^^^^^^^^^^^

If no contextual information or results of child objects are required then a
visitor can derive directly from the ``BaseVisitor`` class. The action method
will be called before child objects are actioned.


BaseVisitorWithContext
^^^^^^^^^^^^^^^^^^^^^^
If contextual information is required, such as the parent container (and its
parent, etc...) then the ``BaseVisitorWithContext`` can be derived instead. The
immediate context is available via the ``context`` property and the context
of all parent containers via the ``contexts`` attribute.


BaseChildResultsVisitor
^^^^^^^^^^^^^^^^^^^^^^^

For visitors that require the results of child objects (e.g. ``Cloner``) to
in their action methods. The child/children results can be accessed via the
``child_result`` and ``children_result`` dictionaries. If context information
is also required use the ``BaseChildResultsVisitorWithContext`` visitor.


BasePreAndPostVisitor
^^^^^^^^^^^^^^^^^^^^^

For visitors the need to perform and action before and after the child results
are actioned. The "pre" action methods are the same as in the ``BaseVisitor``
class and the "post" action method is called ``post_action``, which by
default will call the ``post_action_<lowercase-nineml_type>`` or
``default_post_action`` methods. If context information
is also required use the ``BasePreAndPostVisitorWithContext`` visitor.


BaseDualVisitor
^^^^^^^^^^^^^^^

This visitor visits two objects side by side, raising exceptions if their
structure doesn't match. As such it is probably only useful for equality
checking (and is derived by the ``EqualityChecker`` and ``MismatchFinder``
visitors). A ``BaseDualVisitorWithContext`` visitor is also available.


Validation
~~~~~~~~~~

Validation is currently only performed on component classes (i.e. ``Dynamics``,
``ConnectionRule``, and ``RandomDistribution``). A separate visitor is
implemented for every aspect of the component classes that need to be validated
(e.g. name-conflicts, mismatching-dimensions).


Base validators are implemented in the
``nineml.abstraction.componentclassvisitors.validators`` package with
specializations for each component class type in the corresponding
``nineml.abstraction.<componentclass-type>.visitors.validators`` packages (at
this stage only the ``Dynamics`` component class has specialised validators).

Serialization
~~~~~~~~~~~~~

For serialization visitors to be able to serialize a NineML object it needs to
define both ``serialize_node`` and ``unserialize_node`` methods.

``serialize_node``/``unserialize_node``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Both ``serialize_node`` and ``unserialize_node`` take a single argument, a
``NodeToSerialize`` or ``NodeToUnSerialize`` instance respectively. These
node objects wrap a serial element of the given serialization format (e.g.
``lxml.etree._Element`` for the ``XMLSerializer``) and provide convenient
methods for adding, or accessing, children, attributes and body elements to the
node. 

The node method calls then call format-specific method of the serialization
visitor to un/serialize the NineML objects.  However, in some cases
(particularly in some awkward v1.0 syntax), the serialization visitor may need
to be accessed directly, which is available at ``node.visitor``.

Both ``serialize_node`` and ``unserialize_node`` should accept arbitrary
keyword arguments and pass them on to all calls made to methods of the nodes
and the visitor directly. However, these arguments are not currently used by
any of the current serializers.

``has_serial_body``
^^^^^^^^^^^^^^^^^^^

NineML classes that contain "body" text when serialized (to a supporting
serial format) should override the class attribute ``has_serial_body`` to set
it to ``True``. If the class has a body only in NineML v1.0 syntax but not v2.0
then it should be set to ``'v1'``.  

NineML classes that just contain a single body element (e.g.
``SingleValue``) should set has_serial_body to ``'only'``, to allow them to be
collapsed into an attribute in formats that don't support body text (i.e. YAML,
JSON).

    
.. _`NineML specification`: http://nineml.net/specification/