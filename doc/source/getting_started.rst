===============
Getting started
===============


Reading model descriptions from XML files
=========================================

NineML documents can contain abstraction layer models, user layer models (with
references to abstraction layer models defined in other documents) or both.

To read a file containing only abstraction layer elements:

.. code-block:: python

   >>> import nineml
   >>> doc = nineml.read("BrunelIaF.xml")
   >>> doc.items()
   [('BrunelIaF', Dynamics(name='BrunelIaF')),
    ('current', Dimension(name='current', i=1)),
    ('resistance', Dimension(name='resistance', i=-2, m=1, t=-3, l=2)),
    ('time', Dimension(name='time', t=1)),
    ('voltage', Dimension(name='voltage', i=-1, m=1, t=-3, l=2)]

This gives us a :class:`~nineml.Document` instance, a dictionary-like object
containing a :class:`~nineml.abstraction.Dynamics` definition of an
integrate-and-fire neuron model, together with the definitions of the physical
dimensions of parameters and state variables used in the model.

Now for a file containing an entire user layer model (with references to other
NineML documents containing the abstraction layer definitions):

.. code-block:: python

    >>> doc = nineml.read("brunel_network_alpha_AI.xml")
    >>> from pprint import pprint
    >>> pprint(all_items)
    [('All': Selection(name='All')),
     ('Exc': Population(name='Exc', number=4000, cell=nrn)),
     ('Excitation': Projection(name="Excitation", source=Population(name='Exc', number=4000, cell=nrn), destination=Selection(name='All'), connectivity=BaseComponent(name="RandomExc", componentclass="RandomFanIn"), response=BaseComponent(name="syn", componentclass="AlphaPSR")plasticity=BaseComponent(name="ExcitatoryPlasticity", componentclass="StaticConnection"), delay=Delay(value=1.5, unit=ms), with 2 port-connections)),
     ('Ext': Population(name='Ext', number=5000, cell=stim)),
     ('External': Projection(name="External", source=Population(name='Ext', number=5000, cell=stim), destination=Selection(name='All'), connectivity=BaseComponent(name="OneToOne", componentclass="OneToOne"), response=BaseComponent(name="syn", componentclass="AlphaPSR")plasticity=BaseComponent(name="ExternalPlasticity", componentclass="StaticConnection"), delay=Delay(value=1.5, unit=ms), with 2 port-connections)),
     ('Hz': Unit(name='Hz', dimension='per_time', power=0)),
     ('Inh': Population(name='Inh', number=1000, cell=nrn)),
     ('Inhibition': Projection(name="Inhibition", source=Population(name='Inh', number=1000, cell=nrn), destination=Selection(name='All'), connectivity=BaseComponent(name="RandomInh", componentclass="RandomFanIn"), response=BaseComponent(name="syn", componentclass="AlphaPSR")plasticity=BaseComponent(name="InhibitoryPlasticity", componentclass="StaticConnection"), delay=Delay(value=1.5, unit=ms), with 2 port-connections)),
     ('Mohm': Unit(name='Mohm', dimension='resistance', power=6)),
     ('current': Dimension(name='current', i=1)),
     ('mV': Unit(name='mV', dimension='voltage', power=-3)),
     ('ms': Unit(name='ms', dimension='time', power=-3)),
     ('nA': Unit(name='nA', dimension='current', power=-9)),
     ('per_time': Dimension(name='per_time', t=-1)),
     ('resistance': Dimension(name='resistance', i=-2, m=1, t=-3, l=2)),
     ('time': Dimension(name='time', t=1)),
     ('voltage': Dimension(name='voltage', i=-1, m=1, t=-3, l=2))]

Again we get a :class:`~nineml.Document` instance object containing all the
NineML objects in the document. An alternative representation can be obtained
by reading the file as a :class:`~nineml.user.Network` object:

.. code-block:: python

    >>> from nineml.user import Network
    >>> net = doc.read("brunel_network_alpha_AI.xml").as_network('BrunelAI')
    >>> print(net)
    Network(name='BrunelAI')

This gives a much more structured representation. For example, all the
:class:`~nineml.user.Population`\s within the model are
available through the ``populations`` attribute:

.. code-block:: python

    >>> net.populations
    {'Exc': Population(name='Exc', number=4000, cell=nrn),
     'Ext': Population(name='Ext', number=5000, cell=stim),
     'Inh': Population(name='Inh', number=1000, cell=nrn)}


Introspecting NineML models
===========================

Introspecting abstraction layer models
--------------------------------------

Once we have loaded a model from an XML file we can begin to examine its structure.

.. code-block:: python

    >>> model = doc['BrunelIaF']
    >>> model
    Dynamics(name='BrunelIaF')

We can see a list of model parameters:

.. code-block:: python

    >>> list(model.parameters)
    [Parameter(theta, dimension=voltage),
    Parameter(Vreset, dimension=voltage),
    Parameter(R, dimension=resistance),
    Parameter(tau_rp, dimension=time),
    Parameter(tau, dimension=time)]

a list of state variables:

.. code-block:: python

    >>> list(model.state_variables)
    >>> [StateVariable(V, dimension=voltage), StateVariable(t_rpend, dimension=time)]

and a list of the variables that are imported from/exposed to the outside world:

.. code-block:: python

    >>> list(model.ports)
    [AnalogSendPort('V', dimension='Dimension(name='voltage', i=-1, m=1, t=-3, l=2)'),
     AnalogSendPort('t_rpend', dimension='Dimension(name='time', t=1)'),
     AnalogReducePort('Isyn', dimension='Dimension(name='current', i=1)', op='+'),
     EventSendPort('spikeOutput')]

Delving more deeply, we can examine the model's regimes more closely:

.. code-block:: python

    >>> list(model.regimes)
    [Regime(refractoryRegime), Regime(subthresholdRegime)]
    >>> r_ref, r_sth = model.regimes

Looking first at the subthreshold regime, we can see the differential equations:

.. code-block:: python

    >>> list(r_sth.time_derivatives)
    [TimeDerivative( dV/dt = (-V + R*Isyn)/tau )]

and the conditions under which the model will transition to the refractory regime:

.. code-block:: python

    >>> list(r_sth.transitions)
    [OnCondition( V > theta )]
    >>> tr_spike = list(r_sth.transitions)[0]

The trigger for this transition is for the variable ``V`` to pass a threshold (parameter ``theta``):

.. code-block:: python

    >>> tr_spike.trigger
    Condition('V > theta')

When the transition is initiated, the model will emit an output event (i.e. a spike) and discontinusouly change
the values of some of the state variables:

.. code-block:: python

    >>> tr_spike.event_outputs
    [OutputEvent('spikeOutput')]
    >>> tr_spike.state_assignments
    [StateAssignment('t_rpend', 't + tau_rp'), StateAssignment('V', 'Vreset')]

Then it will move to the refractory regime:

.. code-block:: python

    >>> tr_spike.target_regime
    Regime(refractoryRegime)

The refractory regime can be introspected in a similar way.

Introspecting user layer models
-------------------------------

As shown above, once a complete network model has been loaded as a :class:`~nineml.user.Network` object, we
can look at its neuron populations and the connections between these populations ("projections"):

.. code-block:: python

    >>> net.populations
    {'Exc': Population(name='Exc', number=4000, cell=nrn),
     'Ext': Population(name='Ext', number=5000, cell=stim),
     'Inh': Population(name='Inh', number=1000, cell=nrn)}

    >>> net.projections
    {'Excitation': Projection(name="Excitation", source=Population(name='Exc', number=4000, cell=nrn), destination=<nineml.user.containers.Selection object at 0x1097f39d0>, connectivity=BaseComponent(name="RandomExc", componentclass="RandomFanIn"), response=BaseComponent(name="syn", componentclass="AlphaPSR")plasticity=BaseComponent(name="ExcitatoryPlasticity", componentclass="StaticConnection"), delay=Delay(value=1.5, unit=ms), with 2 port-connections),
    'External': Projection(name="External", source=Population(name='Ext', number=5000, cell=stim), destination=<nineml.user.containers.Selection object at 0x1097f39d0>, connectivity=BaseComponent(name="OneToOne", componentclass="OneToOne"), response=BaseComponent(name="syn", componentclass="AlphaPSR")plasticity=BaseComponent(name="ExternalPlasticity", componentclass="StaticConnection"), delay=Delay(value=1.5, unit=ms), with 2 port-connections),
    'Inhibition': Projection(name="Inhibition", source=Population(name='Inh', number=1000, cell=nrn), destination=<nineml.user.containers.Selection object at 0x1097f39d0>, connectivity=BaseComponent(name="RandomInh", componentclass="RandomFanIn"), response=BaseComponent(name="syn", componentclass="AlphaPSR")plasticity=BaseComponent(name="InhibitoryPlasticity", componentclass="StaticConnection"), delay=Delay(value=1.5, unit=ms), with 2 port-connections)}

NineML also supports "selections", groupings of neurons which span populations:

.. code-block:: python

    >>> net.selections
    {'All neurons': Selection('All neurons', 'Concatenate(Reference(name="Exc"), Reference(name="Inh"))')}

.. note:: in NineML version 1, the only type of selection is a concatenation of two or more populations. In future
          versions it will be possible to select and combine sub-populations.

Looking more closely at a population, we can see its name, the number of neurons it contains and
the neuron model used (:class:`~nineml.user.Component`):

.. code-block:: python

    >>> p_exc = net.populations['Exc']
    >>> p_exc
    Population(name='Exc', number=4000, cell=nrn)
    >>> p_exc.number
    4000
    >>> p_exc.cell
    BaseComponent(name="nrn", componentclass="BrunelIaF")

In the neuron model component we can see its abstraction layer definition
(:class:`~nineml.abstraction.dynamics.ComponentClass`), it's properties (parameter values), and the initial
values of its state variables.

.. note:: the handling of initial values is likely to change in future versions of NineML.

.. code-block:: python

    >>> p_exc.cell.component_class
    Dynamics(name='BrunelIaF')
    >>> p_exc.cell.properties
    ({'Vreset': Property(name=Vreset, value=10.0, unit=mV), 'tau': Property(name=tau, value=20.0, unit=ms), 'R': Property(name=R, value=1.5, unit=Mohm), 'tau_rp': Property(name=tau_rp, value=2.0, unit=ms), 'theta': Property(name=theta, value=20.0, unit=mV)})
    >>> p_exc.cell.initial_values
    InitialValue({'t_rpend': Property(name=t_rpend, value=0.0, unit=ms), 'V': Property(name=V, value=0.0, unit=mV)})

Turning from a population to a projection:

.. code-block:: python

    >>> prj_inh = net.projections['Inhibition']
    >>> prj_inh.source
    Population(name='Inh', number=1000, cell=nrn)
    >>> prj_inh.destination
    Selection('All neurons', 'Concatenate(Reference(name="Exc"), Reference(name="Inh"))')
    >>> prj_inh.response
    BaseComponent(name="syn", componentclass="AlphaPSR")
    >>> prj_inh.connectivity
    BaseComponent(name="RandomInh", componentclass="RandomFanIn")
    >>> prj_inh.plasticity
    BaseComponent(name="InhibitoryPlasticity", componentclass="StaticConnection")
    >>> prj_inh.delay
    Delay(value=1.5, unit=ms)
    >>> prj_inh.port_connections
    [PortConnection('plasticity', 'response', 'weight', 'q'),
     PortConnection('response', 'destination', 'Isyn', 'Isyn')]

Note that the :attr:`source` and :attr:`destination` attributes point to
:class:`~nineml.user.Population`\s or :class:`~nineml.user.Projection`\s, the
:attr:`connectivity` rule, the post-synaptic :attr:`response` model and
the synaptic :attr:`plasticity` model are all
:class:`~nineml.user.Component`\s. The :attr:`port_connections`
attribute indicates which ports in the different components should be connected
together.


Writing model descriptions in Python
====================================

Writing abstraction layer models
--------------------------------

.. code-block:: python

    subthreshold_regime = Regime(
        name="subthreshold_regime",
        time_derivatives=[
            "dV/dt = alpha*V*V + beta*V + zeta - U + Isyn / C_m",
            "dU/dt = a*(b*V - U)", ],

        transitions=[On("V > theta",
                        do=["V = c",
                            "U =  U+ d",
                            OutputEvent('spike')],
                        to='subthreshold_regime')]
    )

    ports = [AnalogSendPort("V", un.voltage),
             AnalogReducePort("Isyn", un.current, operator="+")]

    parameters = [
        Parameter('theta', un.voltage),
        Parameter('a', un.per_time),
        Parameter('b', un.per_time),
        Parameter('c', un.voltage),
        Parameter('d', un.voltage / un.time),
        Parameter('C_m', un.capacitance),
        Parameter('alpha', un.dimensionless / (un.voltage * un.time)),
        Parameter('beta', un.per_time),
        Parameter('zeta', un.voltage / un.time)]

    state_variables = [
        StateVariable('V', un.voltage),
        StateVariable('U', un.voltage / un.time)]

    izhi = Dynamics(
        name="Izhikevich",
        parameters=parameters,
        state_variables=state_variables,
        regimes=[subthreshold_regime],
        analog_ports=ports)


Writing user layer models
-------------------------

.. code-block:: python

    # Meta-parameters
    order = 1000       # scales the size of the network
    Ne = 4 * order     # number of excitatory neurons
    Ni = 1 * order     # number of inhibitory neurons
    epsilon = 0.1      # connection probability
    Ce = int(epsilon * Ne)  # number of excitatory synapses per neuron
    Ci = int(epsilon * Ni)  # number of inhibitory synapses per neuron
    Cext = Ce          # effective number of external synapses per neuron
    delay = 1.5        # (ms) global delay for all neurons in the group
    J = 0.1            # (mV) EPSP size
    Jeff = 24.0 * J      # (nA) synaptic weight
    Je = Jeff          # excitatory weights
    Ji = -g * Je       # inhibitory weights
    Jext = Je          # external weights
    theta = 20.0       # firing thresholds
    tau = 20.0         # membrane time constant
    tau_syn = 0.1      # synapse time constant
    # nu_thresh = theta / (Je * Ce * tau * exp(1.0) * tau_syn) # threshold rate
    nu_thresh = theta / (J * Ce * tau)
    nu_ext = eta * nu_thresh      # external rate per synapse
    input_rate = 1000.0 * nu_ext * Cext   # mean input spiking rate

    # Parameters
    neuron_parameters = dict(tau=tau * ms,
                             v_threshold=theta * mV,
                             refractory_period=2.0 * ms,
                             v_reset=10.0 * mV,
                             R=1.5 * Mohm)  # units??
    psr_parameters = dict(tau=tau_syn * ms)

    # Initial Values
    v_init = RandomDistributionProperties(
        "uniform_rest_to_threshold",
        ninemlcatalog.load("randomdistribution/Uniform",
                           'UniformDistribution'),
        {'minimum': (0.0, unitless),
         'maximum': (theta, unitless)})
    neuron_initial_values = {"v": (v_init * mV),
                             "refractory_end": (0.0 * ms)}
    synapse_initial_values = {"a": (0.0 * nA), "b": (0.0 * nA)}
    tpoisson_init = RandomDistributionProperties(
        "exponential_beta",
        ninemlcatalog.load('randomdistribution/Exponential',
                           'ExponentialDistribution'),
        {"rate": (1000.0 / input_rate * unitless)})

    # Dynamics components
    celltype = DynamicsProperties(
        "nrn",
        ninemlcatalog.load('neuron/LeakyIntegrateAndFire',
                           'LeakyIntegrateAndFire'),
        neuron_parameters, initial_values=neuron_initial_values)
    ext_stim = DynamicsProperties(
        "stim",
        ninemlcatalog.load('input/Poisson', 'Poisson'),
        dict(rate=(input_rate, Hz)),
        initial_values={"t_next": (tpoisson_init, ms)})
    psr = DynamicsProperties(
        "syn",
        ninemlcatalog.load('postsynapticresponse/Alpha', 'Alpha'),
        psr_parameters,
        initial_values=synapse_initial_values)

    # Connecion rules
    one_to_one_class = ninemlcatalog.load(
        '/connectionrule/OneToOne', 'OneToOne')
    random_fan_in_class = ninemlcatalog.load(
        '/connectionrule/RandomFanIn', 'RandomFanIn')

    # Populations
    exc_cells = Population("Exc", Ne, celltype, positions=None)
    inh_cells = Population("Inh", Ni, celltype, positions=None)
    external = Population("Ext", Ne + Ni, ext_stim, positions=None)

    # Selections
    all_cells = Selection(
        "All", Concatenate(exc_cells, inh_cells))

    # Projections
    input_prj = Projection(
        "External", external, all_cells,
        connectivity=ConnectionRuleProperties(
            "OneToOne", one_to_one_class),
        response=psr,
        plasticity=DynamicsProperties(
            "ExternalPlasticity",
            ninemlcatalog.load("plasticity/Static", 'Static'),
            properties={"weight": (Jext, nA)}),
        port_connections=[
            EventPortConnection(
                'pre', 'response', 'spike_output', 'spike'),
            AnalogPortConnection(
                "plasticity", "response", "fixed_weight", "weight"),
            AnalogPortConnection(
                "response", "destination", "i_synaptic", "i_synaptic")],
        delay=(delay, ms))

    exc_prj = Projection(
        "Excitation", exc_cells, all_cells,
        connectivity=ConnectionRuleProperties(
            "RandomExc", random_fan_in_class, {"number": (Ce * unitless)}),
        response=psr,
        plasticity=DynamicsProperties(
            "ExcitatoryPlasticity",
            ninemlcatalog.load("plasticity/Static", 'Static'),
            properties={"weight": (Je, nA)}),
        port_connections=[
            EventPortConnection(
                'pre', 'response', 'spike_output', 'spike'),
            AnalogPortConnection(
                "plasticity", "response", "fixed_weight", "weight"),
            AnalogPortConnection(
                "response", "destination", "i_synaptic", "i_synaptic")],
        delay=(delay, ms))

    inh_prj = Projection(
        "Inhibition", inh_cells, all_cells,
        connectivity=ConnectionRuleProperties(
            "RandomInh", random_fan_in_class, {"number": (Ci * unitless)}),
        response=psr,
        plasticity=DynamicsProperties(
            "InhibitoryPlasticity",
            ninemlcatalog.load("plasticity/Static", 'Static'),
            properties={"weight": (Ji, nA)}),
        port_connections=[
            EventPortConnection(
                'pre', 'response', 'spike_output', 'spike'),
            AnalogPortConnection(
                "plasticity", "response", "fixed_weight", "weight"),
            AnalogPortConnection(
                "response", "destination", "i_synaptic", "i_synaptic")],
        delay=(delay, ms))

    # Save to document in NineML Catalog
    network = Network(name if name else "BrunelNetwork")
    network.add(exc_cells, inh_cells, external, all_cells, input_prj, exc_prj,
                inh_prj)
