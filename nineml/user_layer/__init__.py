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
    PropertySet
    Value
    Network
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
from .dynamics import SpikingNodeType, SynapseType, ConnectionType
from .connectivity import ConnectionRule
from .population import Population, PositionList, Structure
from .containers import Network, Selection, Concatenate
from .projection import Projection, PortConnection
from .random import RandomDistribution
from .components import (PropertySet, Property, BaseComponent as Component,
                         Definition, Prototype)
from .base import Reference
