"""
A Python library for working with 9ML model descriptions.

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

__version__ = "0.2dev"

from .base import BaseNineMLObject, DocumentLevelObject
from document import read, write, load, Document
import abstraction_layer
import user_layer
import exceptions
import units
from .units import Unit, Dimension
from abstraction_layer import (
    DynamicsClass, ConnectionRuleClass, RandomDistributionClass,
    ComponentClass)
from user_layer import (
    Dynamics, ConnectionRule, RandomDistribution, Selection, Population,
    Projection, Property, Definition, Component)
