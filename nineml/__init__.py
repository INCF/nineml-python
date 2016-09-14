"""
A Python library for working with 9ML model descriptions.

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from .document import read, write, Document
from . import abstraction
from . import user
from . import exceptions
from . import units
from .units import Unit, Dimension, Quantity
from abstraction import (
    Dynamics, ConnectionRule, RandomDistribution)
from .user import (
    Selection, Population, Projection, Property, Definition,
    DynamicsProperties, ConnectionRuleProperties, RandomDistributionProperties,
    Network, MultiDynamics, MultiDynamicsProperties, Concatenate,
    ComponentArray, EventConnectionGroup, AnalogConnectionGroup)
from .values import SingleValue, ArrayValue, RandomValue

__version__ = "0.1"
