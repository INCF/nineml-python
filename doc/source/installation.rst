============
Installation
============

Use of the Python 9ML API requires that you have Python (version 2.7 or >=3.4)
with the ``sympy`` package installed. To serialize NineML_ to XML, YAML and
HDF5 formats the ``lxml``, ``pyyaml`` and ``h5py`` packages are also required
respectively.

Dependencies
------------

macOS
~~~~~

If you are not already using another Python installation (e.g. Enthought,
Python(x,y), etc...) it can be a good idea to install Python using the
Homebrew_ package manager rather than using the system version as Apple has
modified some package versions (e.g. ``six``), which can cause difficulties
down the track. ::
    
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

On Linux, development packages for HDF5 (i.e. with headers). For Ubuntu/Debian
the following packages can be used

    * libhdf5-serial-dev (serial)
    * libhdf5-openmpi-dev (parallel with Open MPI)
    * libhdf5-mpich-dev (parallel with MPICH)

Please consult the relevant documentation to find the appropriate package for
other distributions.


Windows
~~~~~~~

On Windows, you can download the Python installer from http://www.python.org.
To use HDF5 serialisation you will need to install HDF5 from source, see
http://docs.h5py.org/en/latest/build.html.


Install Python packages
-----------------------

To install the Python package it is recommeded to install from PyPI using
`pip`::

    $ pip install nineml
    
Otherwise for the latest version you can clone the repository at
http://github.com/INCF/nineml-python or install directly with::


    $ pip install git+http://github.com/INCF/nineml-python

.. _NineML: http://nineml.net
.. _Homebrew: http://brew.sh