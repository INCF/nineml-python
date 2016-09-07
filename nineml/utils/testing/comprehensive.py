"""
Contains an example document with every type 9ML element in it for use in
comprehensive testing over all 9ML elements
"""
import nineml.units as un
from nineml.units import Quantity
from nineml.document import Document
from nineml.abstraction import (
    Parameter, Constant, Dynamics, Regime, Alias,
    OutputEvent, StateVariable, StateAssignment, On, AnalogSendPort,
    AnalogReceivePort, AnalogReducePort, ConnectionRule, RandomDistribution,
    EventReceivePort, EventSendPort, OnEvent, OnCondition,
    TimeDerivative, Expression)
from nineml.user import (
    Population, Selection, Concatenate, Projection, Property,
    Definition, Prototype, Initial, DynamicsProperties,
    ConnectionRuleProperties, RandomDistributionProperties,
    MultiDynamicsProperties, AnalogPortConnection,
    EventPortConnection, Network)
from nineml.xml import nineml_v1_ns


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
            transitions=[On('SV1 > P3', do=[OutputEvent('ESP1')]),
                         On('ERP1', do=[OutputEvent('ESP2')])],
            name='R1'
        ),
        Regime(name='R2',
               transitions=[
                   OnCondition('(SV1 > C1) & (SV2 < P4)', target_regime='R1')])
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
            transitions=[On('SV1 > P1', do=[OutputEvent('ESP1')]),
                         On('ERP1', do=[
                            OutputEvent('ESP1'),
                            StateAssignment('SV1', 'P1')])],
            name='R1',
        ),
        Regime(name='R2', transitions=[
            On('SV1 > 1', to='R1'),
            On('SV3 < 0.001', to='R2',
               do=[StateAssignment('SV3', 1)])])
    ],
    analog_ports=[AnalogReducePort('ARP1', operator='+'),
                  AnalogReceivePort('ARP2'),
                  AnalogSendPort('A1'),
                  AnalogSendPort('A2'),
                  AnalogSendPort('SV3')],
    event_ports=[EventSendPort('ESP1'),
                 EventReceivePort('ERP1')],
    parameters=['P1', 'P2', 'P3']
)


dynC = Dynamics(
    name='dynC',
    aliases=['A1:=P1', 'A2 := ARP1 + SV2', 'A3 := SV1'],
    regimes=[
        Regime(
            'dSV1/dt = -SV1 / (P2*t)',
            'dSV2/dt = SV1 / (ARP1*t) + SV2 / (P1*t)',
            transitions=[On('SV1 > P1', do=[OutputEvent('ESP1')]),
                         On('ERP1', do=[OutputEvent('ESP1')])],
            aliases=[Alias('A1', 'P1 * 2')],
            name='R1',
        ),
        Regime(name='R2', transitions=On('SV1 > 1', to='R1'))
    ],
    analog_ports=[AnalogReceivePort('ARP1'), AnalogReceivePort('ARP2'),
                  AnalogSendPort('A1'), AnalogSendPort('A2')],
    parameters=['P1', 'P2']
)

dynD = Dynamics(
    name='dynD',
    state_variables=[
        StateVariable('SV1', dimension=un.voltage)],
    regimes=[
        Regime(
            'dSV1/dt = -SV1 / P1',
            transitions=[On('SV1 > P2', do=[OutputEvent('ESP1')]),
                         On('ERP1', do=[StateAssignment('SV1', 'P2')])],
            name='R1'
        ),
    ],
    constants=[Constant('C1', 1.0 * un.Mohm)],
    aliases=[Alias('A1', Expression('SV1 / C1'))],
    analog_ports=[AnalogSendPort('A1', dimension=un.current)],
    parameters=[Parameter('P1', dimension=un.time),
                Parameter('P2', dimension=un.voltage)]
)

dynE = Dynamics(
    name='dynE',
    state_variables=[
        StateVariable('SV1', dimension=un.voltage)],
    regimes=[
        Regime(
            'dSV1/dt = -SV1 / P1 + ARP1 / P2',
            name='R1',
            transitions=[
                On('SV1 > P3', do=[OutputEvent('ESP1')])])
    ],
    analog_ports=[AnalogReceivePort('ARP1', dimension=un.current)],
    parameters=[Parameter('P1', dimension=un.time),
                Parameter('P2', dimension=un.capacitance),
                Parameter('P3', dimension=un.voltage)])

dynF = Dynamics(
    name='dynF',
    state_variables=[
        StateVariable('SV1', dimension=un.current)],
    regimes=[
        Regime(
            'dSV1/dt = -SV1 / P1',
            transitions=[On('ERP1',
                            do=[StateAssignment('SV1', 'SV1 + P2')])],
            name='R1'
        ),
    ],
    analog_ports=[AnalogSendPort('SV1', dimension=un.current)],
    parameters=[Parameter('P1', dimension=un.time),
                Parameter('P2', dimension=un.current)]
)

dynG = Dynamics(
    name='dynG',
    state_variables=[
        StateVariable('SV1', dimension=un.dimensionless)],
    event_ports=[
        EventReceivePort('ERP1')],
    analog_ports=[
        AnalogSendPort('SV1', dimension=un.dimensionless)],
    parameters=[
        Parameter('P1', dimension=un.dimensionless),
        Parameter('P2', dimension=un.time)],
    regimes=[
        Regime(
            name='R1',
            time_derivatives=[
                TimeDerivative('SV1', Expression('-1/P2'))],
            transitions=[
                OnEvent('ERP1', state_assignments=[
                    StateAssignment('SV1', 'SV1 + P1')])])])

dynPropA = DynamicsProperties(
    name='dynA',
    definition=dynA,
    properties={
        'P1': 1.0 * un.mV,
        'P2': 1.0 * un.ms,
        'P3': 1.0 * un.mV,
        'P4': 1.0 * un.nA},
    initial_values={
        'SV1': 1.0 * un.unitless,
        'SV2': 1.0 * un.unitless})

dynPropB = DynamicsProperties(
    name='dynB',
    definition=Definition(dynB),
    properties={
        'P1': 1.0 * un.unitless,
        'P2': 1.0 * un.unitless,
        'P3': 1.0 * un.unitless})

dynPropC = DynamicsProperties(
    name='dynCProp',
    definition=dynC,
    properties={
        'P1': 1.0 * un.unitless,
        'P2': 1.0 * un.unitless},
    initial_values=[Initial('SV1', 0.0 * un.unitless),
                    Initial('SV2', Quantity(0.0, un.unitless)),
                    Initial('SV3', 0.0)])

dynPropD = Dynamics(
    name='dynPropD',
    definition=dynD,
    properties={'P1': 1.0 * un.ms,
                'P2': 1.0 * un.V})

dynPropE = Dynamics(
    name='dynPropE',
    definition=dynE,
    properties={'P1': 1.0 * un.ms,
                'P2': 1.0 * un.uF,
                'P3': 1.0 * un.mV})

dynPropG = DynamicsProperties(
    name='dynPropG',
    definition=dynG,
    properties={'P1': 1.0,
                'P2': 10 * un.ms})

dynPropA2 = DynamicsProperties(
    name='dynPropA2',
    definition=Prototype(dynPropA),
    properties=[Property('P4', Quantity(2.0, un.mA))])


multiDynPropsA = MultiDynamicsProperties(
    name='multiDynA',
    sub_components={
        'd': dynD, 'e': dynE},
    port_connections=[
        ('d', 'A1', 'e', 'ARP1'),
        ('e', 'ESP1', 'd', 'ERP1')])

ranDistrA = RandomDistribution(
    name="RanDistrA",
    standard_library="http://www.uncertml.org/distributions/exponential",
    parameters=[Parameter('P1', dimension=un.dimensionless)])

ranDistrPropA = RandomDistributionProperties(
    name="RanDistrPropA",
    definition=ranDistrA,
    properties={'P1': 1.0 * un.unitless})

popA = Population(
    name="popA",
    size=10,
    cell=dynPropA)

popB = Population(
    name='popB',
    size=100,
    cell=dynPropB)

popC = Population(
    name='popC',
    size=50,
    cell=dynPropC)

popD = Population(
    name="popD",
    size=1,
    cell=DynamicsProperties(
        name="dynDProps", definition=dynD,
        properties={'P1': 1 * un.ms, 'P2': -65 * un.mV}))

popE = Population(
    name="popE",
    size=1,
    cell=DynamicsProperties(
        name="dynEProps", definition=dynE,
        properties={'P1': 1 * un.ms, 'P2': 1 * un.uF}))


selA = Selection(
    name="selA",
    operation=Concatenate(popA, popC))

selB = Selection(
    name='selB',
    operation=Concatenate(popB, popD, popE))


conA = ConnectionRule(
    name="ConA",
    standard_library=nineml_v1_ns + '/connectionrules/RandomFanIn',
    parameters=[Parameter('P1', dimension=un.dimensionless)])

conPropA = ConnectionRuleProperties(
    name="ConPropA",
    definition=conA,
    properties={'P1': 1.0 * un.unitless})

conB = ConnectionRule(
    name="ConB",
    standard_library=(nineml_v1_ns + '/connectionrules/OneToOne'))

projA = Projection(
    name="projA",
    pre=popA,
    post=popB,
    response=dynPropG,
    delay=Quantity(2, un.ms),
    connectivity=conPropA,
    port_connections=[
        ('pre', 'ESP1', 'response', 'ERP1'),
        ('response', 'SV1', 'post', 'ARP1')])

projB = Projection(
    name="projB",
    pre=popD,
    post=popE,
    response=DynamicsProperties(
        name="dynFProps",
        definition=dynF,
        properties={'P1': 10 * un.ms, 'P2': 1 * un.nA}),
    connectivity=ConnectionRuleProperties(
        name="ConnectionRuleProps",
        definition=conB),
    delay=1 * un.ms,
    port_connections=[
        EventPortConnection(
            send_port='ESP1',
            receive_port='ERP1',
            sender_role='pre',
            receiver_role='response'),
        AnalogPortConnection(
            send_port='SV1',
            receive_port='ARP1',
            sender_role='response',
            receiver_role='post')])

netA = Network(
    name='netA',
    populations=[popA, popB],
    projections=[projA])

netB = Network(
    name='netB',
    populations=[popA, popB, popC, popD],
    projections=[projA, projB])

document = Document(
    dynA, dynB, dynC, dynE, dynF, dynPropA, dynPropB, dynPropC, ranDistrA,
    ranDistrPropA, popA, popB, popC, popD, popE, selA, conA, conPropA,
    conB, netA, netB)

if __name__ == '__main__':
    print 'loaded successfully'
