"""
Utility functions for component core classes

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""


def parse(filename):
    """Left over from orignal Version. This will be deprecated"""

    from nineml.abstraction_layer.readers import XMLReader
    return XMLReader.read_component(filename)
