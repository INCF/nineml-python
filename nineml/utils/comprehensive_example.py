"""
Contains an example document with every type 9ML element in it for use in
comprehensive testing over all 9ML elements
"""
from __future__ import absolute_import
from past.builtins import basestring
import pkgutil
from collections import defaultdict
from itertools import chain
import nineml
import nineml.units as un
from nineml.annotations import Annotations
from nineml.units import Quantity
from nineml.values import SingleValue, ArrayValue, RandomDistributionValue
from nineml.document import Document
from nineml.reference import Reference
from nineml.abstraction import (
    Parameter, Constant, Dynamics, Regime, Alias,
    OutputEvent, StateVariable, StateAssignment, On, AnalogSendPort,
    AnalogReceivePort, AnalogReducePort, ConnectionRule, RandomDistribution,
    EventReceivePort, EventSendPort, OnEvent, OnCondition,
    TimeDerivative, Expression, Trigger)
from nineml.user import (
    Population, Selection, Concatenate, Projection, Property,
    Definition, Prototype, Initial, DynamicsProperties,
    ConnectionRuleProperties, RandomDistributionProperties,
    MultiDynamicsProperties, AnalogPortConnection,
    EventPortConnection, Network)
from nineml.user.multi import (
    EventSendPortExposure, EventReceivePortExposure, AnalogSendPortExposure,
    AnalogReceivePortExposure, AnalogReducePortExposure)
import sympy
from nineml.user.projection import Connectivity
from nineml.serialization import NINEML_V1_NS


ranDistrA = RandomDistribution(
    name="ranDistrA",
    standard_library="http://www.uncertml.org/distributions/exponential",
    parameters=[Parameter('P1', dimension=un.dimensionless)])

ranDistrPropA = RandomDistributionProperties(
    name="ranDistrPropA",
    definition=ranDistrA,
    properties={'P1': 81.0 * un.unitless})

dynA = Dynamics(
    name='dynA',
    aliases=['A1:=P1 * SV2', 'A2 := ARP1 + SV2', 'A3 := SV1',
             'A4 := C2 * SV1'],
    state_variables=[
        StateVariable('SV1', dimension=un.voltage),
        StateVariable('SV2', dimension=un.current)],
    regimes=[
        Regime(
            'dSV1/dt = -SV1 / P2',
            'dSV2/dt = A3 / ARP2 + SV2 / P2',
            transitions=[On(Trigger('SV1 > P3'), do=[OutputEvent('ESP1')]),
                         On('ERP1', do=[OutputEvent('ESP2')])],
            name='R1'
        ),
        Regime(name='R2',
               transitions=[
                   OnCondition('(SV1 > C1) & (SV2 < P4)',
                               target_regime_name='R1')])
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
    constants=[Constant('C1', value=-71.0, units=un.mV),
               Constant('C2', value=22.2, units=un.degC)])

dynB = Dynamics(
    name='dynB',
    aliases=['A1:=P1', 'A2 := ARP1/C1 + ADP1 + SV2', 'A3 := SV1',
             'A4 := SV1^3 + SV2^-3'],
    regimes=[
        Regime(
            'dSV1/dt = -SV1 / (P2*t)',
            'dSV2/dt = SV1 / (ARP1/C1*t) + SV2 / (P1*t)',
            'dSV3/dt = -SV3/t + P3/t',
            transitions=[On('SV1 > P1', do=[OutputEvent('ESP1')]),
                         On('ERP1', do=[
                            OutputEvent('ESP1'),
                            StateAssignment('SV1', 'P1 + random.uniform()')])],
            name='R1',
        ),
        Regime(name='R2', transitions=[
            On('SV1 > 1', to='R1'),
            On('SV3 < 0.001', to='R2',
               do=[StateAssignment('SV3', '2 * random.normal()')])])
    ],
    constants=[Constant('C1', 10.0 * un.mA, un.nA)],
    analog_receive_ports=[AnalogReceivePort('ARP1', dimension=un.current)],
    analog_reduce_ports=[AnalogReducePort('ADP1', operator='+')],
    analog_send_ports=[AnalogSendPort('A1'),
                       AnalogSendPort('A2'),
                       AnalogSendPort('SV3')],
    event_send_ports=[EventSendPort('ESP1')],
    event_receive_ports=[EventReceivePort('ERP1')],
    parameters=['P1', 'P2', 'P3']
)


dynC = Dynamics(
    name='dynC',
    aliases=['A1:=P1', 'A2 := ARP1 + SV2', 'A3 := SV1'],
    regimes=[
        Regime(
            'dSV1/dt = -SV1 / (P2*t)',
            'dSV2/dt = SV1 / (ARP1*t) + SV2 / (P1*t)',
            on_conditions=[OnCondition('SV1 > P1',
                                       output_events=[OutputEvent('ESP1')])],
            on_events=[OnEvent('ERP1', output_events=[OutputEvent('ESP1')])],
            aliases=[Alias('A1', 'P1 * 2')],
            name='R1',
        ),
        Regime(name='R2', transitions=On('SV1 > 1', to='R1'))
    ],
    ports=[AnalogReceivePort('ARP1'), AnalogReceivePort('ARP2'),
           AnalogSendPort('A1'), AnalogSendPort('A2')],
    parameters=['P1', 'P2']
)

dynD = Dynamics(
    name='dynD',
    state_variables=[
        StateVariable('SV1', dimension=un.voltage)],
    regimes=[
        Regime(
            'dSV1/dt = -SV1 / P1 + ADP1 + ARP1 * P3',
            transitions=[On('SV1 > P2', do=[OutputEvent('ESP1')]),
                         On('ERP1',
                            do=[StateAssignment(
                                'SV1', 'P2 * random.binomial(1,2)')])],
            name='R1'
        ),
    ],
    constants=[Constant('C1', -67.0 * un.Mohm)],
    aliases=[Alias('A1', Expression('SV1 / C1'))],
    ports=[AnalogSendPort('A1', dimension=un.current),
           AnalogReducePort('ADP1', dimension=(un.voltage / un.time)),
           AnalogReceivePort('ARP1', dimension=un.current),
           EventSendPort('ESP1'),
           EventReceivePort('ERP1')],
    parameters=[Parameter('P1', dimension=un.time),
                Parameter('P2', dimension=un.voltage),
                Parameter('P3', dimension=(un.voltage /
                                           (un.time * un.current)))]
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
    analog_ports=[AnalogReceivePort('ARP1', dimension=un.current),
                  AnalogSendPort('SV1', un.voltage)],
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
    aliases=[Alias('A1', 'SV1 * C1'),
             Alias('A2', 'A1 * P3 / P2')],
    event_ports=[
        EventReceivePort('ERP1')],
    analog_ports=[
        AnalogSendPort('SV1', dimension=un.dimensionless),
        AnalogSendPort('A1', dimension=un.current),
        AnalogSendPort('A2', dimension=un.voltage / un.time)],
    parameters=[
        Parameter('P1', dimension=un.dimensionless),
        Parameter('P2', dimension=un.time),
        Parameter('P3', dimension=un.resistance)],
    constants=[Constant('C1', 1.3 * un.nA)],
    regimes=[
        Regime(
            name='R1',
            time_derivatives=[
                TimeDerivative('SV1', Expression('-1/P2'))],
            transitions=[
                OnEvent('ERP1', state_assignments=[
                    StateAssignment('SV1', 'SV1 + P1')])])])

dynH = Dynamics(
    name='dynH',
    state_variables=[StateVariable('SV1', un.dimensionless)],
    aliases=['A1 := SV1 + P1'],
    regimes=[
        Regime(
            name='R1',
            transitions=[On('ERP1',
                            do=[StateAssignment(
                                'SV1',
                                'SV1 + P2 * random.exponential(5)')])])],
    analog_ports=[AnalogSendPort('A1', un.dimensionless)])

dynPropA = DynamicsProperties(
    name='dynPropA',
    definition=dynA,
    properties={
        'P1': -5.56 * un.mV,
        'P2': 78.0 * un.ms,
        'P3': -90.2 * un.mV,
        'P4': 152.0 * un.nA},
    initial_values={
        'SV1': -1.7 * un.V,
        'SV2': 8.1 * un.nA},
    check_initial_values=True)

dynPropB = DynamicsProperties(
    name='dynPropB',
    definition=Definition(dynB),
    properties={
        'P1': 11.1 * un.unitless,
        'P2': Quantity(RandomDistributionValue(ranDistrPropA), un.unitless),
        'P3': -101 * un.unitless})

dynPropC = DynamicsProperties(
    name='dynPropC',
    definition=dynC,
    properties={
        'P1': 23.3 * un.unitless,
        'P2': Quantity(ArrayValue([1.0, 2.0, 3.0, 4.0, 5.0]), un.unitless)},
    initial_values=[Initial('SV1', 3.3 * un.unitless),
                    Initial('SV2', Quantity(21.7, un.unitless)),
                    Initial('SV3', Quantity([8, 7, 6, 5, 4], un.unitless))],
    check_initial_values=True)

dynPropC2 = DynamicsProperties(
    name='dynPropC2',
    definition=dynPropC,
    properties={
        'P1': 100.0 * un.unitless})

dynPropD = DynamicsProperties(
    name='dynPropD',
    definition=dynD,
    properties={'P1': Quantity(SingleValue(1.0), un.ms),
                'P2': Quantity(44.1 * un.V, un.mV),
                'P3': -75.3 * un.mV / (un.s * un.pA)})

dynPropE = DynamicsProperties(
    name='dynPropE',
    definition=dynE,
    properties={'P1': 22.1 * un.ms,
                'P2': Quantity(34.2 * un.uF),
                'P3': -12.0 * un.mV})

dynPropG = DynamicsProperties(
    name='dynPropG',
    definition=dynG,
    properties={'P1': 8.8,
                'P2': 2.3 * un.ms,
                'P3': 55 * un.ohm})

dynPropH = DynamicsProperties(
    name='dynPropH',
    definition=dynH,
    properties={'P1': -3.3, 'P2': 40.5})

dynPropA2 = DynamicsProperties(
    name='dynPropA2',
    definition=Prototype(dynPropA),
    properties=[Property('P4', Quantity(42.0, un.mA))])


multiDynPropA = MultiDynamicsProperties(
    name='multiDynPropA',
    sub_components={
        'd': dynPropD, 'e': dynPropE},
    port_connections=[
        ('d', 'A1', 'e', 'ARP1'),
        ('e', 'ESP1', 'd', 'ERP1')],
    port_exposures=[
        ('d', 'ERP1'),
        ('d', 'ADP1'),
        ('d', 'ARP1'),
        ('e', 'SV1'),
        ('e', 'ESP1')])

multiDynA = multiDynPropA.component_class

multiDynA.validate()

multiDynPropB = MultiDynamicsProperties(
    name='multiDynPropB',
    sub_components={
        'multiA': multiDynPropA,
        'c': dynPropC,
        'g': dynPropG},
    port_connections=[
        EventPortConnection('ESP1__e', 'ERP1',
                            sender_name='multiA', receiver_name='g'),
        AnalogPortConnection('SV1', 'ARP2',
                             sender_name='g', receiver_name='c'),
        AnalogPortConnection('A2',
                             'ADP1__d' + AnalogReducePortExposure.SUFFIX,
                             sender_name='g',
                             receiver_name='multiA')],
    port_exposures=[
        EventSendPortExposure('multiA', 'ESP1__e', name='ESP1'),
        EventReceivePortExposure('multiA', 'ERP1__d', name='ERP1'),
        AnalogReducePortExposure(
            'multiA',
            'ADP1__d' + AnalogReducePortExposure.SUFFIX, name='ADP1'),
        AnalogSendPortExposure('g', 'SV1', name='ASP1'),
        AnalogReceivePortExposure('c', 'ARP1', name='ARP1'),
        AnalogReceivePortExposure('multiA', 'ARP1__d', name='ARP2')])

multiDynB = multiDynPropB.component_class

popA = Population(
    name="popA",
    size=102,
    cell=dynPropA2)

popB = Population(
    name='popB',
    size=100,
    cell=dynPropB)

popC = Population(
    name='popC',
    size=5,
    cell=dynPropC)

popD = Population(
    name="popD",
    size=1,
    cell=DynamicsProperties(
        name="dynDProps", definition=dynD,
        properties={'P1': 1.5 * un.ms, 'P2': -65.0 * un.mV,
                    'P3': 7.7 * un.V / (un.ms * un.uA)}))

popE = Population(
    name="popE",
    size=1,
    cell=DynamicsProperties(
        name="dynEProps", definition=dynE,
        properties={'P1': 3.2 * un.ms, 'P2': -20.3 * un.uF,
                    'P3': 0.0 * un.mV}))

popMultiA = Population(
    name='popMultiA',
    size=20,
    cell=multiDynPropA)


popMultiB = Population(
    name='popMultiB',
    size=20,
    cell=multiDynPropB)

selA = Selection(
    name="selA",
    operation=Concatenate((popA, popC)))

selB = Selection(
    name='selB',
    operation=Concatenate((popB, popD, popE)))


conA = ConnectionRule(
    name="conA",
    standard_library=NINEML_V1_NS + '/connectionrules/RandomFanIn',
    parameters=[Parameter('number', dimension=un.dimensionless)])

conPropA = ConnectionRuleProperties(
    name="conPropA",
    definition=conA,
    properties={'number': 5 * un.unitless})

conB = ConnectionRule(
    name="conB",
    standard_library=(NINEML_V1_NS + '/connectionrules/OneToOne'))


conPropB1 = ConnectionRuleProperties(
    name="conPropBA",
    definition=conB)

projA = Projection(
    name="projA",
    pre=popA,
    post=popB,
    response=dynPropG,
    delay=Quantity(3.1, un.ms),
    connection_rule_properties=conPropA,
    port_connections=[
        ('pre', 'ESP1', 'response', 'ERP1'),
        ('response', 'A1', 'post', 'ARP1')])

projB = Projection(
    name="projB",
    pre=popD,
    post=popE,
    response=DynamicsProperties(
        name="dynFPropsA",
        definition=dynF,
        properties={'P1': 10.7 * un.ms, 'P2': 3.1 * un.nA}),
    connection_rule_properties=ConnectionRuleProperties(
        name="conPropB2",
        definition=conB),
    delay=1 * un.ms,
    port_connections=[
        EventPortConnection(
            send_port_name='ESP1',
            receive_port_name='ERP1',
            sender_role='pre',
            receiver_role='response'),
        AnalogPortConnection(
            send_port_name='SV1',
            receive_port_name='ARP1',
            sender_role='response',
            receiver_role='post')])

projC = Projection(
    name='projC',
    pre=selA,
    post=popB,
    response=dynPropG,
    delay=2.4 * un.ms,
    connection_rule_properties=conPropA,
    port_connections=[
        ('pre', 'ESP1', 'response', 'ERP1'),
        ('response', 'A1', 'post', 'ARP1')])

projD = Projection(
    name='projD',
    pre=popA,
    post=selB,
    response=DynamicsProperties(
        name="dynFPropsB",
        definition=dynF,
        properties={'P1': -1.72 * un.ms, 'P2': 88.0 * un.nA}),
    connection_rule_properties=conPropB1,
    delay=1 * un.ms,
    port_connections=[
        EventPortConnection(
            send_port_name='ESP1',
            receive_port_name='ERP1',
            sender_role='pre',
            receiver_role='response'),
        AnalogPortConnection(
            send_port_name='SV1',
            receive_port_name='ARP1',
            sender_role='response',
            receiver_role='post')])

projE = Projection(
    name='projE',
    pre=popMultiA,
    post=popMultiB,
    response=dynPropH,
    delay=0.5 * un.s,
    connection_rule_properties=conPropB1,
    port_connections=[
        ('pre', 'ESP1__e', 'response', 'ERP1'),
        ('response', 'A1', 'post', 'ARP1')])

netA = Network(
    name='netA',
    populations=[popA, popB],
    projections=[projA])

netB = Network(
    name='netB',
    populations=[popC, popD],
    projections=[projB])

netC = Network(
    name='netC',
    populations=[popMultiA, popMultiB],
    projections=[projE])

arp = dynA.port('ARP2')
doc1 = Document(
    dynA, dynB, dynC, dynE, dynF, dynPropA, dynPropB, dynPropC, dynPropC2,
    multiDynPropA, multiDynPropB, ranDistrA, ranDistrPropA, popA, popB, popC,
    popD, popE, selA, conA, conPropA, conB, projA, projB, projC, projD, projE,
    netA, netB,
    *list(chain(*(netA.flatten() + netB.flatten() + netC.flatten()))))

doc2 = Document(
    dynA, dynB, dynC, dynE, dynF, dynPropA, dynPropB, dynPropC, dynPropC2,
    ranDistrA, ranDistrPropA, popA, popB, popC, popD, popE,
    selA, conA, conPropA, conB, projA, projB, projC, projD, netA, netB,
    clone_definitions=True)


# -----------------------------------------------------------------------------
# Create dictionaries holding all nineml types and corresponding examples in
# the example document
# -----------------------------------------------------------------------------

loading = [None]


def add_with_sub_elements(element):
    """
    Recursively adds 9ML elements from the example document to a dictionary
    sorted by 9ML types
    """
    if isinstance(element, (basestring, Document)) or element in loading:
        return
    if not isinstance(element, (dict, list, tuple, int, float, str,
                                sympy.Basic, Connectivity)):
        # If element has an attribute called 'nineml_type' add it to the
        # dictionary of all 9ML elements
        if element.nineml_type == 'Annotations':
            return

        instances_of_all_types[element.nineml_type][element.key] = element
        # Loop through all attributes of the element that are not in the class
        # definition and attempt to add them to the instances_of_all_types dict
        loading.append(element)
        for attr in set(dir(element)) - set(dir(element.__class__)):
            add_with_sub_elements(getattr(element, attr))
        loading.pop()
    else:
        # If element is a dictionary or list
        try:
            sub_elem_iter = iter(element.values())
        except AttributeError:
            try:
                sub_elem_iter = iter(element)
            except TypeError:
                return
        for elem in sub_elem_iter:
            add_with_sub_elements(elem)

v1_safe_docs = [doc2]

instances_of_all_types = defaultdict(dict)
instances_of_all_types[doc1.nineml_type]['doc1'] = doc1
instances_of_all_types[Reference.nineml_type] = dict((r.key, r) for r in (
    Reference(name=o, document=doc1) for o in (
        'dynA', 'dynB', 'dynC', 'dynE', 'dynF', 'dynPropA', 'dynPropB',
        'dynPropC', 'multiDynPropA', 'multiDynPropB', 'ranDistrA',
        'ranDistrPropA', 'popA', 'popB', 'popC', 'popD', 'popE', 'selA',
        'conA', 'conPropA', 'conB', 'projA', 'projB', 'projC',
        'projD', 'projE')))

annotations = Annotations()
annotations.set(('cat1', 'NS_1'), 'key1', 'value1')
annotations.set(('cat2', 'NS_2'), 'key2', 'value2')
instances_of_all_types[Annotations.nineml_type]['example'] = annotations
for elem in doc1.values():
    add_with_sub_elements(elem)
# Add remaining elements that are not picked up by recursive
# search
multiDynA = multiDynPropA.definition.target
multiDynB = multiDynPropB.definition.target
for elem in chain(multiDynA.sub_components,
                  multiDynB.sub_components, multiDynA.ports, multiDynB.ports,
                  multiDynA.port_connections, multiDynB.port_connections,
                  multiDynA.aliases, multiDynB.aliases):
    instances_of_all_types[elem.nineml_type][elem.key] = elem

all_types = {}

for importer, modname, ispkg in pkgutil.walk_packages(
        path=nineml.__path__, onerror=lambda x: None,  # @UnusedVariable
        prefix=nineml.__name__ + '.'):
    if modname != __name__:
        # This line was giving strange errors with super init methods
        # so I swapped for the less elegant one below
        # module = importer.find_module(modname).load_module(modname)
        exec('import {} as module'.format(modname))
        for cls in module.__dict__.values():  # @UndefinedVariable
            if (isinstance(cls, type) and cls.__module__ == module.__name__): # @UndefinedVariable @IgnorePep8
                try:
                    if not cls.nineml_type.startswith('_'):
                        all_types[cls.nineml_type] = cls
                except AttributeError:
                    pass  # Not a nineml type


_all_class_names = set(all_types.keys())
_all_instance_names = set(instances_of_all_types.keys())

assert not (_all_class_names - _all_instance_names), (
    "Not all 9ML elements are in comprehensive example document, '{}',"
    .format("', '".join(_all_class_names - _all_instance_names)))

if __name__ == '__main__':
    multiDynA.validate()
#     r = multiDynA.regime('R1___R1')
#     t = list(r.transitions)[2]
#     print list(list(t.sub_transitions)[0].output_events)
#     print list(t.output_events)
    print('done')
