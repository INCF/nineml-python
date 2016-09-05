import nineml.units as un
from nineml.document import Document
from nineml.abstraction import (
    Parameter, Constant, Dynamics, Regime,
    OutputEvent, StateVariable, StateAssignment, On, AnalogSendPort,
    AnalogReceivePort, ConnectionRule, RandomDistribution)
from nineml.user import (
    Population, Selection, Concatenate, Projection, Property, Component,
    Definition, Prototype, resolve_reference, write_reference, Initial,
    DynamicsProperties, ConnectionRuleProperties, RandomDistributionProperties,
    Quantity, MultiDynamics, MultiDynamicsProperties, AnalogPortConnection,
    EventPortConnection, Network, ComponentArray, AnalogConnectionGroup,
    EventConnectionGroup)


dynA = Dynamics(
    name='dynA',
    aliases=['A1:=P1 * SV2', 'A2 := ARP1 + SV2', 'A3 := SV1'],
    state_variables=[
        StateVariable('SV1', dimension=un.voltage),
        StateVariable('SV2', dimension=un.current)],
    regimes=[
        Regime(
            'dSV1/dt = -SV1 / P2',
            'dSV2/dt = A3 / ARP2 + SV2 / P2',
            transitions=[On('SV1 > P3', do=[OutputEvent('emit')]),
                         On('spikein', do=[OutputEvent('emit')])],
            name='R1'
        ),
        Regime(name='R2', transitions=On('(SV1 > C1) & (SV2 < P4)',
                                         to='R1'))
    ],
    analog_ports=[AnalogReceivePort('ARP1', dimension=un.current),
                  AnalogReceivePort('ARP2', dimension=(un.resistance *
                                                       un.time)),
                  AnalogSendPort('A1', dimension=un.voltage * un.current),
                  AnalogSendPort('A2', dimension=un.current)],
    parameters=[Parameter('P1', dimension=un.voltage),
                Parameter('P2', dimension=un.time),
                Parameter('P3', dimension=un.voltage),
                Parameter('P4', dimension=un.current)],
    constants=[Constant('C1', value=1.0, units=un.mV)]
)

dynB = Dynamics(
    name='dynB',
    aliases=['A1:=P1', 'A2 := ARP1 + SV2', 'A3 := SV1',
             'A4 := SV1^3 + SV2^-3'],
    regimes=[
        Regime(
            'dSV1/dt = -SV1 / (P2*t)',
            'dSV2/dt = SV1 / (ARP1*t) + SV2 / (P1*t)',
            'dSV3/dt = -SV3/t + P3/t',
            transitions=[On('SV1 > P1', do=[OutputEvent('emit')]),
                         On('spikein', do=[
                            OutputEvent('emit'),
                            StateAssignment('SV1', 'P1')])],
            name='R1',
        ),
        Regime(name='R2', transitions=[
            On('SV1 > 1', to='R1'),
            On('SV3 < 0.001', to='R2',
               do=[StateAssignment('SV3', 1)])])
    ],
    analog_ports=[AnalogReceivePort('ARP1'),
                  AnalogReceivePort('ARP2'),
                  AnalogSendPort('A1'),
                  AnalogSendPort('A2'),
                  AnalogSendPort('SV3')],
    parameters=['P1', 'P2', 'P3']
)

dynPropA = DynamicsProperties(
    name='dynA',
    definition=dynA,
    properties={
        'P1': 1.0 * un.mV,
        'P2': 1.0 * un.ms,
        'P3': 1.0 * un.mV,
        'P4': 1.0 * un.nA})

dynPropB = DynamicsProperties(
    name='dynB',
    definition=dynB,
    properties={
        'P1': 1.0 * un.unitless,
        'P2': 1.0 * un.unitless,
        'P3': 1.0 * un.unitless})

ConA = ConnectionRule(
    name="ConA",
    standard_library='http://nineml.net/9ML/1.0/connectionrules/RandomFanIn',
    parameters=[Parameter('P1', dimension=un.dimensionless)])

ConPropA = ConnectionRuleProperties(
    name="ConPropA",
    definition=ConA,
    properties={'P1': 1.0 * un.unitless})

RanDistrA = RandomDistribution(
    name="RanDistrA",
    standard_library="http://www.uncertml.org/distributions/exponential",
    parameters=[Parameter('P1', dimension=un.dimensionless)])

RanDistrPropA = RandomDistributionProperties(
    name="RanDistrPropA",
    definition=RanDistrA,
    properties={'P1': 1.0 * un.unitless})

PopA = Population(
    name="PopA",
    size=10,
    cell=dynPropA)

doc = Document((dynA, PopA))
