#!/usr/bin/env python
from nineml.abstraction import (
    Dynamics, On, OutputEvent, AnalogReceivePort, AnalogSendPort,
    Regime)

c = Dynamics(
    name='C',
    aliases=['C1:=cp1', 'C2 := cIn1', 'C3 := SV1'],
    regimes=[
        Regime(
            'dSV1/dt = -SV1/cp2',
            transitions=[On('SV1>cp1', do=[OutputEvent('emit')]),
                         On('spikein', do=[OutputEvent('c_emit')])],
            name='r1',
        ),
        Regime(name='r2', transitions=On('SV1>1', to='r1'))
    ],
    analog_ports=[AnalogReceivePort('cIn1'), AnalogReceivePort('cIn2'),
                  AnalogSendPort('C1'), AnalogSendPort('C2')],
    parameters=['cp1', 'cp2']
)

c.write('example_component_class.xml')

