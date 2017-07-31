Serialization
=============

Formats
-------

There are currently six supported formats for serialization with the NineML
Python library : XML_, YAML_, JSON_, HDF5_, `Python Pickle`_ and Python
dictionary (the JSON_, YAML_ and `Python Pickle`_ formats are derived from the
Python dictionary serializer). Noting that the serialization module is written
in a modular way that supports additional hierarchical formats by deriving the
``BaseSerializer`` and ``BaseUnserializer`` classes if required.

XML_, YAML_, JSON_, HDF5 and `Python Pickle`_ formats can be serialized to
file, XML_, YAML_, JSON_ formats can be serialized to Python strings, and
`Python Pickle`_ and Python dictionary formats can be serialized to Python
objects (i.e. maintaining floating point representations of values). 

Although these six formats are similar, in that they all represent hierarchical
object models, there are slight differences that prevent general one-to-one
mappings between all of them. These issues, and how they are overcome are
explained in the `Serialization`_ of the `NineML Specification`_.   

Documents
---------


Options
-------
 * 
 * reference handling

General
-------

To write a collection of NineML "document-level" objects to file, in either
XML, YAML, JSON, HDF5, Python Pickle use the ``nineml.write`` method

.. automodule:: nineml.serialization
   :members: read, write


which takes the filename as the first parameter followed by the objects to add
to the document::

     # Construct the component:
     dyn = Dynamics(...)
     pop = Population(...)

     # Save the component as NineML-XML:
     nineml.write('test.xml', dyn, pop)


``write`` is a simple wrapper around the relevant serializer for the selected
data format, e.g. ``XMLSerializer.write`` for XML_ serialization. Therefore,
we could also have written::

     # Construct the component:
     c = ComponentClass(...)

     # Save the component as NineML-XML:
     from nineml.serialization.xml import XMLSerialzer
     XMLSerializer(c).write_to_file("test.xml")


Reading from file
-----------------

We can load files from serialized files; we do this with an Unserializer class::


    from nineml.serialization.hdf5 import HDF5Unserializer
    c = HDF5Unserializer("test.xml").read()['comp_class_name']

This will work provided there is just a single component specified in the file.
If more than one component is specified, then we need to explicitly name the
component we want to load::


    from nineml.abstraction.readers import XMLReader
    c = XMLReader.read("test.xml", component_name='MyComponent')

If we want to load all the components from a file, we can use::

    from nineml.abstraction.readers import XMLReader
    component_list = XMLReader.read_components("test.xml")

.. _XML: http://www.w3.org/XML/
.. _YAML: http://yaml.org
.. _HDF5: http://www.hdfgroup.org/HDF5/
.. _JSON: http://www.json.org/
.. _`Python Pickle`: https://docs.python.org/3/library/pickle.html