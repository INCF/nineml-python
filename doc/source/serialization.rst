Serialization
=============

Writing to file
---------------

To write a NineML "document-level" object to file, we can use the ``write``
method, which takes the filename as a parameter::

     # Construct the component:
     c = ComponentClass(...)

     # Save the component as NineML-XML:
     c.write("test.xml")


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



