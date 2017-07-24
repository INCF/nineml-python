======================
Contributing to NineML
======================

Mailing list
============

Discussions about Python :mod:`nineml` take place in the
`NeuralEnsemble Google Group`_ and on the nineml-developers@incf.org mailing
list.


Setting up a development environment
====================================

Requirements
------------

In addition to the requirements listed in :doc:`../installation`, you will need
to install:

    * nose_
    * coverage_

to run tests, and:

    * Sphinx_
    * numpydoc_

to build the documentation.

Code checkout
-------------

NineML development is based around GitHub. Once you have a GitHub account, you
should fork_ the official `NineML repository`_, and then clone your fork to
your local machine::

    $ git clone https://github.com/<username>/nineml-python.git nineml_dev
    $ cd nineml_dev

To work on the development version::

    $ git checkout master

.. To work on the latest stable release (for bug-fixes)::

..    $ git checkout --track origin/0.7

To keep your NineML repository up-to-date with respect to the official
repository, add it as a remote::

    $ git remote add upstream https://github.com/INCF/nineml-python.git

and then you can pull in any upstream changes::

    $ git pull upstream master


We suggest developing in a virtualenv_, and installing :mod:`nineml` using::

    $ python setup.py develop

or::

    $ pip install -e .


Coding style
============

We follow the PEP8_ coding style. Please note in particular:

    - indentation of four spaces, no tabs
    - single space around most operators, but no space around the '=' sign when
      used to indicate a keyword argument or a default parameter value.
    - we currently only Python version 2.7 but Python 3 support is planned.


Testing
=======

Running the PyNN test suite requires the *nose_* packages, and
optionally the *coverage_* package. To run the entire test suite, in the
``lib9ml/python/test`` subdirectory of the source tree::

    $ nosetests unit

To see how well the codebase is covered by the tests, run::

    $ nosetests --with-coverage --cover-package=nineml --cover-erase --cover-html unit

If you add a new feature to :mod:`nineml`, or fix a bug, you should write a
unit test to cover the situation it arose.

Unit tests should where necessary make use of mock/fake/stub/dummy objects to
isolate the component under test as well as possible.


Submitting code
===============

The best way to get started with contributing code to NineML is to fix a small
bug (`bugs marked "minor" in the bug tracker`_) in your checkout of
the code. Once you are happy with your changes, **run the test suite again to
check that you have not introduced any new bugs**. If this is your first
contribution to the project, please add your name and affiliation/employer to
:file:`lib9ml/python/AUTHORS`.

After committing the changes to your local repository::

    $ git commit -m 'informative commit message'

first pull in any changes from the upstream repository::

    $ git pull upstream master

then push to your own account on GitHub::

    $ git push

Now, via the GitHub web interface, open a pull request.


Documentation
=============

Python NineML documentation is generated using Sphinx_.

To build the documentation in HTML format, run::

    $ make html

in the ``doc`` subdirectory of the source tree. Some of the files contain
examples of interactive Python sessions. The validity of this code can be
tested by running::

    $ make doctest

NineML documentation is hosted at http://readthedocs.org/nineml


Making a release
================

To make a release of NineML requires you to have permissions to upload Python
NineML packages to the `Python Package Index`_ and the INCF Software Center.
If you are interested in becoming release manager for Python NineML, please
contact us via the `mailing list`_.

When you think a release is ready, run through the following checklist one
last time:

    * do all the tests pass? This means running :command:`nosetests` and
      :command:`make doctest` as described above. You should do this on at
      least two Linux systems -- one a very recent version and one at least a
      year old, and on at least one version of macOS.
    * does the documentation build without errors? You should then at least
      skim the generated HTML pages to check for obvious problems.
    * have you updated the version numbers in :file:`setup.py`,
      :file:`__init__.py`, :file:`doc/source/conf.py` and
      :file:`doc/source/installation.rst`?
    * have you written release notes and added them to the documentation?

Once you've confirmed all the above, create a source package using::

    $ python setup.py sdist

and check that it installs properly (you will find it in the :file:`dist`
subdirectory.

Now you should commit any changes, then tag with the release number as follows::

    $ git tag x.y.z

where ``x.y.z`` is the release number.

If this is a development release (i.e. an *alpha* or *beta*), the final step is
to upload the source package to the INCF Software Center.
Do **not** upload development releases to PyPI.

To upload a package to the INCF Software Center, log-in, and then go to the
Contents_ tab. Click on "Add new..." then "File", then fill in the form and
upload the source package.

If this is a final release, there are a few more steps:

    * if it is a major release (i.e. an ``x.y.0`` release), create a new
      bug-fix branch::

        $ git branch x.y

    * upload the source package to PyPI::

        $ python setup.py sdist upload

    * make an announcement on the `mailing list`_

    * if it is a major release, write a blog post about it with a focus on the
      new features and major changes.


.. _Sphinx: http://sphinx-doc.org/
.. _numpydoc: https://pypi.python.org/pypi/numpydoc
.. _PEP8: http://www.python.org/dev/peps/pep-0008/
.. _nose: https://nose.readthedocs.org/
.. _mock: http://www.voidspace.org.uk/python/mock/
.. _coverage: http://nedbatchelder.com/code/coverage/
.. _`Python Package Index`: http://pypi.python.org/
.. _`mailing list`: http://groups.google.com/group/neuralensemble
.. _`NeuralEnsemble Google Group`: http://groups.google.com/group/neuralensemble
.. _virtualenv: http://www.virtualenv.org/
.. _`bugs marked "minor" in the bug tracker`: https://github.com/INCF/nineml/issues?labels=minor&state=open
.. _`issue tracker`: https://github.com/INCF/nineml/issues/
.. _fork: https://github.com/INCF/nineml/fork
.. _`NineML repository`: https://github.com/INCF/nineml/
.. _contents: http://software.incf.org/software/nineml/nineml/folder_contents