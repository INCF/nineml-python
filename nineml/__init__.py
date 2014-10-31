"""
A Python library for working with 9ML model descriptions.

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

__version__ = "0.2dev"

from lxml.builder import ElementMaker
nineml_namespace = 'http://nineml.net/9ML/1.0'
NINEML = "{%s}" % nineml_namespace

E = ElementMaker(namespace=nineml_namespace,
                 nsmap={"nineml": nineml_namespace})

import maths
import exceptions
import utility
#import abstraction_layer, we don't have to explicitly import this do we?
from root import NineMLRoot


def parse(path):
    return NineMLRoot.from_file(path)
