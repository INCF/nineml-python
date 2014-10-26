#!/usr/bin/env python

from setuptools import setup  #, find_packages
# from nineml.__init__ import __version__

setup(
    name="9ML",
    # version = __version__,
    version="0.3dev",
    packages=['nineml',
              'nineml.abstraction_layer',
              'nineml.abstraction_layer.components',
              'nineml.abstraction_layer.connection_generator',
              'nineml.abstraction_layer.dynamics',
              'nineml.abstraction_layer.dynamics.component',
              'nineml.abstraction_layer.dynamics.flattening',
              'nineml.abstraction_layer.dynamics.readers',
              'nineml.abstraction_layer.dynamics.testing_utils',
              'nineml.abstraction_layer.dynamics.validators',
              'nineml.abstraction_layer.dynamics.visitors',
              'nineml.abstraction_layer.dynamics.writers',
              'nineml.abstraction_layer.structure'
              ],
    package_data={'nineml': ['examples/AL/demos/*.py', "examples/AL/sample_components/*.py"]},
    # packages = find_packages(),
    author="Andrew P. Davison, Eilif Muller, Mike Hull",
    # add your name here if you contribute to the code
    author_email="nineml-users@incf.org",
    description="A tool for reading, writing and generally working with 9ML files.",
    long_description=open("README").read(),
    license="BSD 3 License",
    keywords="computational neuroscience modeling interoperability XML",
    url="http://nineml.incf.org",
    classifiers=['Development Status :: 3 - Alpha',
                 'Environment :: Console',
                 'Intended Audience :: Science/Research',
                 'License :: OSI Approved :: BSD License',
                 'Natural Language :: English',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python :: 2',
                 'Topic :: Scientific/Engineering'],
    install_requires=['lxml', 'ply', 'csa', 'quantities'],
    tests_require=['nose']
)
