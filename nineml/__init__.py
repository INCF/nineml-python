"""
A Python library for working with 9ML model descriptions.

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

__version__ = "0.2dev"

from .base import BaseNineMLObject, DocumentLevelObject
from document import read, write, load, Document
from . import abstraction
from . import user
from . import exceptions
from . import units
from .units import Unit, Dimension
from abstraction import (
    Dynamics, ConnectionRule, RandomDistribution,
    ComponentClass)
from .user import (
    Selection, Population, Projection, Property, Definition, Component,
    DynamicsProperties, ConnectionRuleProperties, RandomDistributionProperties,
    Network, MultiDynamics)
