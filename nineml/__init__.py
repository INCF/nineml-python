"""
A Python library for working with 9ML model descriptions.

:copyright: Copyright 2010-2017 by the NineML Python team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from .version import __version__
from . import annotations  # @IgnorePep8
from . import units  # @IgnorePep8
from .document import Document  # @IgnorePep8
from . import abstraction  # @IgnorePep8
from . import user  # @IgnorePep8
from . import exceptions  # @IgnorePep8
from .units import Unit, Dimension, Quantity  # @IgnorePep8
from .abstraction import (  # @IgnorePep8
    Dynamics, ConnectionRule, RandomDistribution)
from .user import (  # @IgnorePep8
    Selection, Population, Projection, Property, Definition, Initial,
    Prototype, DynamicsProperties, ConnectionRuleProperties,
    RandomDistributionProperties, Network, MultiDynamics,
    MultiDynamicsProperties, Concatenate, ComponentArray, EventConnectionGroup,
    AnalogConnectionGroup)
from .values import SingleValue, ArrayValue, RandomDistributionValue  # @IgnorePep8
from .serialization import read, write, serialize, unserialize  # @IgnorePep8
from .reference import Reference  # @IgnorePep8
from .annotations import Annotations  # @IgnorePep8
