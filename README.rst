NineML Python Library
=====================

.. image:: https://travis-ci.org/INCF/nineml-python.svg?branch=master
   :target: https://travis-ci.org/ICNF/nineml-python
   :alt: Unit Test Status
.. image:: https://coveralls.io/repos/INCF/nineml-python/badge.svg
   :target: https://coveralls.io/github/ICNF/nineml-python
   :alt: Unit Test Coverage
.. image:: https://readthedocs.org/projects/nineml/badge/?version=latest
   :target: http://nineml.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

NineML (9ML) is a language for describing the dynamics and connectivity of neuronal
network simulations (http://nineml.net). The language is defined as an object
model, described in the NineML specification (http://nineml.net/specification).

The NineML Python Library (9ML-Python) is a software library written in Python,
which maps the NineML object model onto Python classes for convenient creation,
manipulation and validation of NineML models, as well as handling their
serialization to and from XML_, JSON_, YAML_, and HDF5_.


Installation
------------

HDF5
~~~~

To add support to read/write HDF5_ serializations you must first install the
HDF5_ library.

On macOS it can be installed using Homebrew_

    $ brew install hdf5

On Ubuntu/Debian it can be installed via the ``libhdf5-serial-dev`` (serial)
``libhdf5-openmpi-dev/`` (parallel with Open MPI), or ``libhdf5-mpich-dev``
(parallel with MPICH) packages.

.. note: If you don't install it other serializations can be used.

Pip
~~~

9ML-Python can be installed using ``pip`` from the
cloned/downloaded repo directory

    $ pip install -r requirements.txt .

which, will also install the prerequisites packages sympy_,
lxml_, and h5py_ if they are not already installed.

If you have not installed the HDF5 library in the previous step (and you don't
plan to use HDF5 serialization), you can avoid having to install h5py_ by
installing sympy_, pyyaml_ and lxml_ separately (pyaml_ and lxml_ are also optional if you
don't require XML or YAML support).

NB: As of 12/10/2016 Sympy v1.0 has a bug in its ccode printer, which is
used by 9ML-python to write expressions within MathInline elements. This bug has
been fixed in the development branch so please either use sympy >= 1.0dev or
the earlier version e.g. 0.7.6.1. If you need to use the latest version of
Sympy for a different project see virtualenv_.


Relation to the NineML Specification
------------------------------------

The layout of the Python modules and classes in 9ML-Python relates closely to the
structure of the `NineML specification v1.0`_. However, there are
notable exceptions where 9ML-Python uses names and relationships that are planned
to be changed in v2.0 of the specification (9ML-Python will be backwards compatible),
such as the renaming of ``ComponentClass`` elements to separate ``Dynamics``,
``ConnectionRule`` and ``RandomDistribution`` elements
(see https://github.com/INCF/nineml/issues/94).
A full list of changes planned for NineML v2.0 can be found at
https://github.com/INCF/nineml/milestone/3. When serializing 9ML models
the v1.0 syntax is used unless the version=2.0 keyword argument is used.

In addition to classes that directly correspond to the 9ML object model, a
range of shorthand notations ("syntactic sugar") exist to make writing 9ML
models by hand more convenient (see the *nineml.sugar* module). These notations
are frequently demonstrated in the *examples* directory of the repository.


NineML Catalog
--------------

The NineML Catalog (http://github.com/INCF/NineMLCatalog) contains a collection
of validated NineML models that can be loaded and maninpulated with nineml-python.
If you create a model that you believe will be of wider use to the
computational neuroscience community please consider contributing to the
catalog via a pull request.


Links
-----

* Documentation: http://nineml-python.readthedocs.org
* Mailing list: nineml-users@incf.org
* Issue tracker: https://github.com/INCF/nineml-python/issues


:copyright: Copyright 20011-2017 by the nineml-python team, see AUTHORS.
:license: BSD 3, see LICENSE for details.
  
.. _HDF5: http://support.hdfgroup.org/HDF5/
.. _YAML: http://yaml.org
.. _JSON: http://www.json.org
.. _XML: http://www.w3.org/XML/
.. _h5py: http://h5py.org/
.. _pyyaml: http://pyyaml.org/
.. _sympy: http://sympy.org
.. _lxml: http://pypi.python.org/pypi/lxml
.. _virtualenv: https://virtualenv.readthedocs.io/en/latest/
.. _Homebrew: https://brew.sh/
.. _NineML specification: http://nineml-spec.readthedocs.io

 
