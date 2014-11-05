"""
A Python library for working with 9ML model descriptions.

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

__version__ = "0.2dev"

from urllib import urlopen
from lxml import etree
from lxml.builder import ElementMaker

nineml_namespace = 'http://nineml.net/9ML/1.0'
NINEML = "{%s}" % nineml_namespace
E = ElementMaker(namespace=nineml_namespace,
                 nsmap={"nineml": nineml_namespace})

import maths
import exceptions
import utility
from context import Context


def load(root_element):
    return Context.from_xml(root_element)


def read(url):
    """
    Read a NineML file and parse its child elements

    If the URL does not have a scheme identifier, it is taken to refer to a
    local file.
    """
    try:
        if not isinstance(url, file):
            try:
                f = urlopen(url)
                xml = etree.parse(f)
            except:  # FIXME: Need to work out what exceptions urlopen raises
                raise Exception("Could not read URL '{}'".format(url))
            finally:
                f.close()
        else:
            xml = etree.parse(url)
    except:  # FIXME: Need to work out what exceptions etree raises
        raise Exception("Could not parse XML file '{}'".format(url))
    root = xml.getroot()
#     try:
    return load(root)
#     except Exception as e:
#         raise Exception("Could not parse NineML file '{}', with error: \n "
#                         "{}".format(url, e))
