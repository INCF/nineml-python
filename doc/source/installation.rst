============
Installation
============

Use of the Python 9ML API requires that you have Python (version 2.7) with the
`sympy` package installed. To serialize NineML_ to XML, YAML and HDF5
formats the `lxml`, 'pyyaml` and `h5py` packages are also required
respectively.

Depdendencies
-------------

macOS
~~~~~

If you are not already using another Python installation (e.g. Enthought,
Python(x,y), etc...) it is
recommended to install Python using the Homebrew_ package manager::
    
    $ brew install python

While other Python installations should work fine, it is not recommended to use
the system Python installation at `/usr/bin/python` for scientific
computing as some of the standard pacakges (e.g. `six`) have been modified and
this can cause problems with other packages down the track.

Before installing `h5py` you will also need to install a development version of
HDF5. With Homebrew_ this can be done with::

    $ brew install hdf5

Linux
~~~~~

On Linux, Python 2.7 and development packages for HDF5 (i.e. with headers)
should be available via your package management system. Please see the relevant
documentation for the appropriate package


Windows
~~~~~~~

On Windows, you can download the Python installer from http://www.python.org.
To use HDF5 serialization you will need to install HDF5 from source, see
http://docs.h5py.org/en/latest/build.html.


Install Python packages
-----------------------

To install the Python package it is recommeded to install from PyPI using
`pip`::

    $ pip install nineml
    
Otherwise for the latest version you can clone the repository at
http://github.com/INCF/nineml-python and run::


    $ pip install -r <path-to-repo>/requirements.txt <path-to-repo>

To install the `nineml` package without one of the serialization depdencies
(e.g. h5py) you can manually install the dependencies you require and then
just use pip without the requirements file::

    $ pip install <path-to-repo>

.. _NineML: http://nineml.net
.. _Homebrew: http://brew.sh