from nineml.abstraction import (
    Dynamics, Regime, OutputEvent, On, StateAssignment, StateVariable)
from nineml.abstraction import units as un


c = Dynamics(
    name='leakyIAF',
    regimes=[
        Regime('dv/dt = (g * (vRest - v) + iSyn) /cm',
               transitions=On('v > vThresh',
                              do=[OutputEvent('spikeOut'),
                                  StateAssignment('tSpike', 't'),
                                  StateAssignment('v', 'vReset')],
                              to='refractoryRegime'),
               name='subthresholdRegime'),
        Regime('dv/dt = 0',
               transitions=On('t > tSpike + tRefractory',
                              to='subthresholdRegime'),
               name='refractoryRegime')],
    state_variables=[StateVariable('v', dimension=un.voltage),
                     StateVariable('tSpike', dimension=un.time)])

c.write('leakyIAF.xml')
