
lib9ML
======

NineML is a language for describing the dynamics and connectivity of neuronal
network simulations (http://nineml.net). The language is defined as an object
model, described in the NineML specification (http://nineml.net/specification),
with a standardized serialization as XML, although other serializations are
possible.

lib9ML is a software library written in Python, which maps the NineML object
model onto Python classes for convenient creation, manipulation and validation
of NineML models, as well as handling their serialization to and from XML.


Installation
------------
lib9ML can be installed using `pip` from the cloned/downloaded repo 

    pip install -r requirements.txt .

which, will also install the prerequisites packages sympy (http://sympy.org) and lxml
(http://pypi.python.org/pypi/lxml) if they are not already installed.

NB: As of 12/10/2016 Sympy v1.0 has a bug in its ccode printer, which is
used by lib9ML to write expressions within MathInline elements. This bug has
been fixed in the development branch so please either use sympy >= 1.0dev or
the earlier version e.g. 0.7.6.1. If you need to use the latest version of
Sympy for a different project see https://virtualenvwrapper.readthedocs.io/en/latest/.


Relation to the NineML Specification
------------------------------------

The layout of the Python modules and classes in lib9ML relates closely to the
structure of the NineML specification v1.0 
(http://incf.github.io/nineml/9ML/1.0/NineML_v1.0.pdf). However, there are
notable exceptions where lib9ML uses names and relationships that are planned
to be changed in v2.0 of the specification (lib9ML will be backwards compatible),
such as the renaming of ``ComponentClass`` elements to separate ``Dynamics``,
``ConnectionRule`` and ``RandomDistribution`` elements
(see https://github.com/INCF/nineml/issues/94).
A full list of changes planned for NineML v2.0 can be found at
https://github.com/INCF/nineml/milestone/3. When serializing NineML models to
XML the v1.0 syntax is used unless the version=2.0 keyword argument is used.

In addition to classes that directly correspond to the NineML object model, a
range of shorthand notations ("syntactic sugar") exist to make writing 9ML
models by hand more convenient (see the *nineml.sugar* module). These notations
are frequently demonstrated in the *examples* directory of the repository.


NineML Catalog
--------------

The NineML Catalog (http://github.com/INCF/NineMLCatalog) contains a collection
of validated NineML models that can be loaded and maninpulated with lib9ML.
If you create a model that you believe will be of wider use to the
computational neuroscience community please consider contributing to the
catalog via a pull request.


Links
-----

* Documentation: http://nineml.readthedocs.org
* Mailing list: nineml-users@incf.org
* Issue tracker: https://github.com/INCF/lib9ML/issues


:copyright: Copyright 20011-2016 by the lib9ML team, see AUTHORS.
:license: BSD 3, see LICENSE for details.

.. image:: https://travis-ci.org/ICNF/lib9ML.svg?branch=master
   :target: https://travis-ci.org/ICNF/lib9ML
   :alt: Unit Test Status
.. image:: https://coveralls.io/repos/INCF/lib9ML/badge.svg
   :target: https://coveralls.io/github/ICNF/lib9ML
   :alt: Unit Test Coverage
 
