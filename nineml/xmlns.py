"""
docstring goes here

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from lxml import etree  # @UnusedImport
from lxml.builder import ElementMaker
from nineml.exceptions import NineMLXMLError
import re


nineml_ns = 'http://nineml.net/9ML/2.0'
nineml_v1_ns = 'http://nineml.net/9ML/1.0'
NINEML = '{' + nineml_ns + '}'
NINEML_V1 = '{' + nineml_v1_ns + '}'
MATHML = "{http://www.w3.org/1998/Math/MathML}"
UNCERTML = "{http://www.uncertml.org/2.0}"

# Extracts the xmlns from an lxml element tag
xmlns_re = re.compile(r'(\{.*\}).*')


def extract_xmlns(tag_name):
    xmlns = xmlns_re.match(tag_name).group(1)
    if xmlns not in (NINEML, NINEML_V1, MATHML, UNCERTML):
        raise NineMLXMLError(
            "Unrecognised namespace '{}'".format(xmlns[1:-1]))
    return xmlns


E = ElementMaker(namespace=nineml_ns, nsmap={None: nineml_ns})
