# A 9ml version of:
# nrn/share/examples/nrniv/netcon/ampa.mod
# r473 from the main repository (http://www.neuron.yale.edu/hg/neuron/nrn) pasted here:
"""

TITLE simple AMPA receptors

COMMENT
-----------------------------------------------------------------------------

	Simple model for glutamate AMPA receptors
	=========================================

  - FIRST-ORDER KINETICS, FIT TO WHOLE-CELL RECORDINGS

    Whole-cell recorded postsynaptic currents mediated by AMPA/Kainate
    receptors (Xiang et al., J. Neurophysiol. 71: 2552-2556, 1994) were used
    to estimate the parameters of the present model; the fit was performed
    using a simplex algorithm (see Destexhe et al., J. Computational Neurosci.
    1: 195-230, 1994).

  - SHORT PULSES OF TRANSMITTER (0.3 ms, 0.5 mM)

    The simplified model was obtained from a detailed synaptic model that
    included the release of transmitter in adjacent terminals, its lateral
    diffusion and uptake, and its binding on postsynaptic receptors (Destexhe
    and Sejnowski, 1995).  Short pulses of transmitter with first-order
    kinetics were found to be the best fast alternative to represent the more
    detailed models.

  - ANALYTIC EXPRESSION

    The first-order model can be solved analytically, leading to a very fast
    mechanism for simulating synapses, since no differential equation must be
    solved (see references below).



References

   Destexhe, A., Mainen, Z.F. and Sejnowski, T.J.  An efficient method for
   computing synaptic conductances based on a kinetic model of receptor binding
   Neural Computation 6: 10-14, 1994.

   Destexhe, A., Mainen, Z.F. and Sejnowski, T.J. Synthesis of models for
   excitable membranes, synaptic transmission and neuromodulation using a
   common kinetic formalism, Journal of Computational Neuroscience 1:
   195-230, 1994.

-----------------------------------------------------------------------------
ENDCOMMENT



NEURON {
	POINT_PROCESS AMPA_S
	RANGE R, g
	NONSPECIFIC_CURRENT i
	GLOBAL Cdur, Alpha, Beta, Erev, Rinf, Rtau
}
UNITS {
	(nA) = (nanoamp)
	(mV) = (millivolt)
	(umho) = (micromho)
	(mM) = (milli/liter)
}

PARAMETER {

	Cdur	= 0.3	(ms)		: transmitter duration (rising phase)
	Alpha	= 0.94	(/ms)	: forward (binding) rate
	Beta	= 0.18	(/ms)		: backward (unbinding) rate
	Erev	= 0	(mV)		: reversal potential
}


ASSIGNED {
	v		(mV)		: postsynaptic voltage
	i 		(nA)		: current = g*(v - Erev)
	g 		(umho)		: conductance
	Rinf				: steady state channels open
	Rtau		(ms)		: time constant of channel binding
	synon
}

STATE {Ron Roff}

INITIAL {
	Rinf = Alpha / (Alpha + Beta)
	Rtau = 1 / (Alpha + Beta)
	synon = 0
}

BREAKPOINT {
	SOLVE release METHOD cnexp
	g = (Ron + Roff)*1(umho)
	i = g*(v - Erev)
}

DERIVATIVE release {
	Ron' = (synon*Rinf - Ron)/Rtau
	Roff' = -Beta*Roff
}

: following supanalog_analog_ports both saturation from single input and
: summation from multiple inputs
: if spike occurs during CDur then new off time is t + CDur
: ie. transmitter concatenates but does not summate
: Note: automatic initialization of all reference args to 0 except first

NET_RECEIVE(weight, on, nspike, r0, t0 (ms)) {
	: flag is an implicit argument of NET_RECEIVE and  normally 0
        if (flag == 0) { : a spike, so turn on if not already in a Cdur pulse
		nspike = nspike + 1
		if (!on) {
			r0 = r0*exp(-Beta*(t - t0))
			t0 = t
			on = 1
			synon = synon + weight
			state_discontinuity(Ron, Ron + r0)
			state_discontinuity(Roff, Roff - r0)
		}
		: come again in Cdur with flag = current value of nspike
		net_send(Cdur, nspike)
        }
	if (flag == nspike) { : if this associated with last spike then turn off
		r0 = weight*Rinf + (r0 - weight*Rinf)*exp(-(t - t0)/Rtau)
		t0 = t
		synon = synon - weight
		state_discontinuity(Ron, Ron - r0)
		state_discontinuity(Roff, Roff + r0)
		on = 0
	}
}

"""

# Author: Eilif Muller, Mike Hull
# This code has not yet been verified.

# Attention units have not yet been checked.
# g = (Ron + Roff)*1(umho)

# Erev -> E, i -> Isyn, v->V
# synon could be removed, using the concept of Regimes
# All the nspike business could be removed due to Regimes and Transitions

from nineml.abstraction_layer import Regime, On, RecvPort, SendPort, DynamicsClass


def get_component():
    off_regime = Regime(
        name="off_regime",
        time_derivatives=[
            "dRon/dt =  -Ron/Rtau",
            "dRoff/dt = -Beta*Roff",
        ],
        transitions=On('spikeoutput',
                       do=["t_off = t+Cdur",
                           "r0 = r0*exp(-Beta*(t - t0))",
                           "t0 = t",
                           "Ron = Ron +r0",
                           "Roff = Roff - r0"
                           ],
                       to="on_regime"
                       )
    )

    on_regime = Regime(
        name="on_regime",
        time_derivatives=[
            "dRon/dt = (weight*Rinf - Ron)/Rtau",
            "dRoff/dt = -Beta*Roff",
        ],
        transitions=[On('spikeoutput', do="t_off = t+Cdur"),     # Extend duration if input spike arrives while on
                     On("t_off>t",                              # What to do when its time to turn off
                        do=["r0 = weight*Rinf + (r0 - weight*Rinf)*exp(-(t - t0)/Rtau)",
                            "t0 = t",
                            "Ron = Ron - r0",
                            "Roff = Roff - r0"
                            ],
                        to='off_regime'
                        )
                     ]
    )

    analog_ports = [RecvPort("weight"),
                    RecvPort("V"),
                    SendPort("Isyn"),
                    SendPort("gsyn")]

    c1 = DynamicsClass("AMPA",
                        regimes=[off_regime, on_regime],
                        analog_ports=analog_ports,
                        aliases=[
                        "g := (on + off)",
                        "Isyn := g*(E-V)",
                        "gsyn := g"
                        ]
                        )
    return c1


if __name__ == '__main__':
    get_component()
