"""
docstring goes here

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from lxml import etree  # @UnusedImport
from lxml.builder import ElementMaker

nineml_namespace = 'http://nineml.net/9ML/2.0'
NINEML = '{' + nineml_namespace + '}'
MATHML = "{http://www.w3.org/1998/Math/MathML}"
UNCERTML = "{http://www.uncertml.org/2.0}"

E = ElementMaker(namespace=nineml_namespace, nsmap={None: nineml_namespace})
