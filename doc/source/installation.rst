============
Installation
============

Use of the Python 9ML API requires that you have Python (version 2.7) and the
`lxml`, `ply`, `numpy` and `quantities` packages installed.

Installing Python
=================

If you are using Linux, Python is available via your package management system.
For Mac OS X or Windows, you can download the Python installer from http://www.python.org,
or install an all-in-one package for scientific computing with Python from
Enthought (http://www.enthought.com/products/epd.php; free academic licence),
Python(x,y) (http://www.pythonxy.com/; free) or Anaconda (http://continuum.io/downloads).
We strongly recommend using virtualenv or Anaconda's virtual Python environments.

Installing dependencies
=======================

On Linux, most or all of the dependencies can be installed via the package management system.
If using Anaconda, use "conda install". Otherwise:

* lxml - see http://lxml.de/installation.html
* ply - `pip install ply`
* NumPy - see http://docs.scipy.org/doc/numpy/user/install.html
* quantities - `pip install quantities`


Installing the nineml package
=============================

::

    $ pip install nineml
