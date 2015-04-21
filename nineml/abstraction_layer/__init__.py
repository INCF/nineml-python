"""
Python module for reading and writing 9ML abstraction layer files in XML
format.

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from .. import BaseNineMLObject


class BaseALObject(BaseNineMLObject):

    """
    Base class for abstraction layer classes
    """
    pass


import dynamics
import expressions
import connectionrule
import randomdistribution
import units
import ports
from .componentclass import Parameter, ComponentClass, NamespaceAddress
from .expressions import Alias, Expression, Constant
from .dynamics import (DynamicsClass, Regime,
                       OutputEvent, StateAssignment, TimeDerivative,
                       DynamicsBlock, OnCondition,
                       Trigger, StateVariable, OnEvent, On, SpikeOutputEvent)
from .ports import (AnalogSendPort, AnalogReceivePort,
                    AnalogReducePort, EventSendPort,
                    EventReceivePort, AnalogPort, EventPort, Port)
from nineml.abstraction_layer.dynamics.utils import flattener as flattening
from .connectionrule import ConnectionRuleClass
from .randomdistribution import RandomDistributionClass
from .units import Unit, Dimension
from .dynamics import DynamicsClassXMLLoader, DynamicsClassXMLWriter
from .randomdistribution import (
    RandomDistributionClassXMLLoader, RandomDistributionClassXMLWriter)
from .connectionrule import (ConnectionRuleClassXMLLoader,
                             ConnectionRuleClassXMLWriter)
