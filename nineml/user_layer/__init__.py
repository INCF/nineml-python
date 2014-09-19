# encoding: utf-8
"""
Python module for reading/writing 9ML user layer files in XML format.

Functions
---------

    parse - read a 9ML file in XML format and parse it into a Model instance.

Classes
-------
    Model
    Definition
    BaseComponent
        SpikingNodeType
        SynapseType
        CurrentSourceType
        Structure
        ConnectionRule
        ConnectionType
        RandomDistribution
    Parameter
    ParameterSet
    Value
    Group
    Population
    PositionList
    Projection
    Selection
    Operator
        Any
        All
        Not
        Comparison
        Eq
        In


:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

import urllib
from lxml import etree
from .base import NINEML


from .dynamics import SpikingNodeType, SynapseType, CurrentSourceType
from .population import (Population, PositionList, Structure, Selection,
                         Operator, Any, All, Not, Comparison, Eq, In)
from .containers import Model, Group
from .projection import Projection, ConnectionRule, ConnectionType
from .random import RandomDistribution
from .components import ParameterSet


def parse(url):
    """
    Read a NineML user-layer file and return a Model object.

    If the URL does not have a scheme identifier, it is taken to refer to a
    local file.
    """
    if not isinstance(url, file):
        f = urllib.urlopen(url)
        doc = etree.parse(f)
        f.close()
    else:
        doc = etree.parse(url)

    root = doc.getroot()
    for import_element in root.findall(NINEML + "import"):
        url = import_element.find(NINEML + "url").text
        imported_doc = etree.parse(url)
        root.extend(imported_doc.getroot().iterchildren())
    return Model.from_xml(root)
