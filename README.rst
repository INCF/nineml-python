NineML Python Library
=====================

.. image:: https://travis-ci.org/INCF/nineml-python.svg?branch=master
   :target: https://travis-ci.org/ICNF/nineml-python
   :alt: Unit Test Status
.. image:: https://coveralls.io/repos/github/INCF/nineml-python/badge.svg?branch=master
   :target: https://coveralls.io/github/INCF/nineml-python?branch=master
   :alt: Unit Test Coverage
.. image:: https://img.shields.io/pypi/pyversions/nineml.svg
    :target: https://pypi.python.org/pypi/nineml/
    :alt: Supported Python versions
.. image:: https://img.shields.io/pypi/v/nineml.svg
    :target: https://pypi.python.org/pypi/nineml/
    :alt: Latest Version    
.. image:: https://readthedocs.org/projects/nineml-python/badge/?version=latest
   :target: http://nineml-python.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

NineML (9ML) is a language for describing the dynamics and connectivity of
neuronal network simulations (http://nineml.net), which is defined by the
`NineML specification`_.

The NineML Python Library is a software package written in Python, which maps
the NineML object model onto Python classes for convenient creation,
manipulation and validation of NineML models, as well as handling their
serialisation to and from XML_, JSON_, YAML_, and HDF5_.


Links
-----

* Documentation: http://nineml-python.readthedocs.org
* Mailing list: `NeuralEnsemble Google Group`_
* Issue tracker: https://github.com/INCF/nineml-python/issues



Relation to the NineML Specification
------------------------------------

The layout of the Python modules and classes in the NineML Python Library
relates closely to the structure of the `NineML specification`_ v1.0. However,
there are notable exceptions where the NineML Python Library uses names and
relationships that are planned to be changed in v2.0 of the specification
(the NineML Python Library will be backwards compatible), such as the
renaming of ``ComponentClass`` elements to separate ``Dynamics``,
``ConnectionRule`` and ``RandomDistribution`` elements
(see https://github.com/INCF/nineml/issues/94).
A full list of changes planned for NineML v2.0 can be found at
https://github.com/INCF/nineml/milestone/3. When serializing 9ML models
the version 1.0 syntax is used unless the ``version=2`` keyword argument is
provided.

In addition to classes that directly correspond to the 9ML object model, a
range of shorthand notations ("syntactic sugar") exist to make writing 9ML
models by hand more convenient (see the ``nineml.sugar`` module). These notations
are frequently demonstrated in the *examples* directory of the repository.


The NineML Catalog
------------------

The `NineML Catalog`_ contains a collection of validated NineML models, which
can be loaded and maninpulated with the NineML Python Library. If you create a
model that you believe will be of wider use to the computational neuroscience
community please consider contributing to the catalog via a pull request.


Installation
------------

HDF5 (dev)
~~~~~~~~~~

To add support to read or write HDF5_ serialisations you must first install a
HDF5_ dev library (i.e. with headers).

On macOS HDF5_ can be installed using Homebrew_::

    $ brew install hdf5

On Ubuntu/Debian HDF5_ can be installed via the following packages:

* libhdf5-serial-dev (serial)
* libhdf5-openmpi-dev (parallel with Open MPI)
* libhdf5-mpich-dev (parallel with MPICH)

.. note: If you don't install a HDF5_ other serialisations can
         still be used but you will need to install the package manually.

Pip
~~~

The NineML Python Library can be installed using ``pip``::

    $ pip install nineml

:copyright: Copyright 20011-2017 by the NineML Python Library team, see AUTHORS.
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
.. _`NeuralEnsemble Google Group`: http://groups.google.com/group/neuralensemble
.. _`NineML Catalog`: http://github.com/INCF/nineml-catalog
 
