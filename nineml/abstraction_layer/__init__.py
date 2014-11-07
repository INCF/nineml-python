"""
Python module for reading and writing 9ML abstraction layer files in XML
format.

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from xmlns import nineml_namespace, NINEML, MATHML
from nineml import __version__
import urllib
from lxml import etree
from components import Parameter, BaseComponentClass as ComponentClass
from dynamics.component import (ComponentClass as DynamicsClass, Regime, On,
                                OutputEvent, StateAssignment, TimeDerivative,
                                AnalogSendPort, AnalogReceivePort,
                                AnalogReducePort, EventSendPort,
                                EventReceivePort, Dynamics, OnCondition,
                                Condition, StateVariable, NamespaceAddress,
                                Alias, OnEvent, SpikeOutputEvent, Expression)
from dynamics.component.util import parse
import dynamics
from dynamics import (component, visitors, readers, writers, validators,
                      component_modifiers, flattening, testing_utils)
from units import Unit, Dimension
from annotation import Annotation

import structure
import connection_generator
import random

# Commented Out by TGC 2/11/14 - There is now a parse in the top-level module
#                                which can load both user layer and abstraction
#                                layer objects.
# def parse(url):
#     """
#     Read a NineML abstraction layer file and return all component classes
# 
#     If the URL does not have a scheme identifier, it is taken to refer to a
#     local file.
#     """
#     if not isinstance(url, file):
#         f = urllib.urlopen(url)
#         doc = etree.parse(f)
#         f.close()
#     else:
#         doc = etree.parse(url)
# 
#     root = doc.getroot()
#     for import_element in root.findall(NINEML + "import"):
#         url = import_element.find(NINEML + "url").text
#         imported_doc = etree.parse(url)
#         root.extend(imported_doc.getroot().iterchildren())
#     return Model.from_xml(root)