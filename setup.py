#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name="nineml",
    version="1.0rc1",
    packages=find_packages(),
    # add your name here if you contribute to the code
    author="Andrew P. Davison, Thomas G. Close, Mike Hull, Eilif Muller",
    author_email="tom.g.close@gmail.com",
    description=(
        "A tool for reading, writing and generally working with 9ML objects "
        "and files."),
    long_description=open("README.rst").read(),
    license="BSD 3 License",
    keywords=("computational neuroscience modeling interoperability XML YAML"
              "HDF5 JSON"),
    url="http://nineml-python.readthedocs.io",
    classifiers=['Development Status :: 4 - Beta',
                 'Environment :: Console',
                 'Intended Audience :: Science/Research',
                 'License :: OSI Approved :: BSD License',
                 'Natural Language :: English',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python :: 2',
                 'Programming Language :: Python :: 2.7',
                 'Programming Language :: Python :: 3',
                 'Programming Language :: Python :: 3.4',
                 'Programming Language :: Python :: 3.5',
                 'Programming Language :: Python :: 3.6',
                 'Topic :: Scientific/Engineering'],
    install_requires=['lxml>=3.7.3',
                      'future>=0.16.0',
                      'h5py>=2.7.0',
                      'pyyaml>=3.1',
                      'sympy>=1.1'],
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, <4',
    tests_require=['nose', 'numpy']
)
