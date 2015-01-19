"""
Python module for reading and writing 9ML abstraction layer files in XML
format.

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from nineml.xmlns import nineml_namespace, NINEML, MATHML
from nineml import __version__
import urllib
from lxml import etree
from base import Parameter, ComponentClass as ComponentClass
from dynamics.component import (ComponentClass as DynamicsClass, Regime, On,
                                EventOut, StateAssignment, TimeDerivative,
                                AnalogSendPort, AnalogReceivePort,
                                AnalogReducePort, EventSendPort,
                                EventReceivePort, Dynamics, OnCondition,
                                Condition, StateVariable, NamespaceAddress,
                                Alias, OnEvent, SpikeOutputEvent, Expression)
from dynamics.component.util import parse
import dynamics
from dynamics import component, visitors, readers, writers, validators, testing_utils
from nineml.abstraction_layer.dynamics import flattening2
from nineml.abstraction_layer import modifiers
                      component_modifiers, flattening, testing_utils)
from units import Unit, Dimension
import connectionrule
from nineml.abstraction_layer import distribution
