Serialization
=============

Formats
-------



General
-------

To write a collection of NineML "document-level" objects to file, in either
XML, YAML, JSON, HDF5, Python Pickle use the ``nineml.write`` method

.. currentmodule:: nineml.serialization

.. autofunction:: write
   :members:


which takes the filename as the first parameter followed by the objects to add
to the document::

     # Construct the component:
     dyn = Dynamics(...)
     pop = Population(...)

     # Save the component as NineML-XML:
     nineml.write('test.xml', dyn, pop)


``write`` is a simple wrapper around ``XMLWriter.write``. We could also
have written::

     # Construct the component:
     c = ComponentClass(...)

     # Save the component as NineML-XML:
     from nineml.abstraction.writers import XMLWriter
     XMLWriter.write(c,"test.xml")


Reading from file
-----------------

We can load files from XML; we do this with the ``XMLReader``::


    from nineml.abstraction.readers import XMLReader
    c = XMLReader.read("test.xml")

This will work provided there is just a single component specified in the file.
If more than one component is specified, then we need to explicitly name the
component we want to load::


    from nineml.abstraction.readers import XMLReader
    c = XMLReader.read("test.xml", component_name='MyComponent')

If we want to load all the components from a file, we can use::

    from nineml.abstraction.readers import XMLReader
    component_list = XMLReader.read_components("test.xml")



