#!/usr/bin/env python
"""
.. module:: nineml_point_neurone_network.py
   :platform: Unix, Windows
   :synopsis:

.. moduleauthor:: Dragan Nikolic <dnikolic@incf.org>
"""

import os, sys, urllib, re, traceback, csv, gc, subprocess
from time import localtime, strftime, time
import numpy, numpy.random

import nineml
import nineml.user_layer
import nineml.connection_generator as connection_generator
import nineml.geometry as geometry
from nineml.user_layer_aux import explicit_list_of_connections
from nineml.user_layer_aux import ConnectionGenerator
from nineml.user_layer_aux import connectionGeneratorFromProjection, geometryFromProjection

from daetools.pyDAE import daeLogs, pyCore, pyActivity, pyDataReporting, pyIDAS, pyUnits
from daetools.solvers import pySuperLU

import nineml_daetools_component
from nineml_daetools_component import daetoolsRNG, createPoissonSpikeTimes, daetoolsSpikeSource, daetoolsComponentInfo
from nineml_daetools_component import daetoolsComponent, daetoolsComponentSetup, fixObjectName

from sedml_support import *
from path_parser import CanonicalNameParser, pathItem

import matplotlib
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure

try:
    from _heapq import heappush, heappop, heapify, heapreplace
except ImportError:
    from heapq import heappush, heappop, heapify, heapreplace

# Select implementation for CSA connection-rule language
import csa
ConnectionGenerator.selectImplementation \
  ('{http://software.incf.org/software/csa/1.0}CSA', csa)

def fixParametersDictionary(parameters):
    """
    :param parameters: ParameterSet object.
    
    :rtype: A dictionary made of the following key:value pairs: ``{'name' : (value, unit) }``.
    :raises: 
    """
    new_parameters = {}
    for name, parameter in parameters.iteritems():
        new_parameters[name] = (parameter.value, parameter.unit) 
    return new_parameters

class daetoolsOnSpikeOutAction(pyCore.daeAction):
    """
    daeAction-derived class that handles all trigerred events from neurones.
    When a spike is fired the function Execute() is called which adds a delay
    to the firing time and places the event into a priority queue. 
    Currently, the priority queue is a global (network-wide) object.
    """
    def __init__(self, neurone, eventPort):
        pyCore.daeAction.__init__(self)
        
        self.neurone   = neurone
        self.eventPort = eventPort

    def Execute(self):
        #print('{0} FIRED AT {1}'.format(self.neurone.CanonicalName, time))
        
        # The floating point value of the data sent with the event is a current time 
        time         = float(self.eventPort.EventData)
        delayed_time = 0.0
        for (synapse, event_port_index, delay, target_neurone) in self.neurone.target_synapses:
            inlet_event_port = synapse.getInletEventPort(event_port_index)
            delayed_time = time + delay
            #print('    {0} should be triggered at {1}'.format(target_neurone.Name, delayed_time))
            heappush(self.neurone.events_heap, (delayed_time, inlet_event_port, target_neurone))

def createNeurone(name, component_info, rng, parameters):
    """
    Returns daetoolsComponent object based on the supplied daetoolsComponentInfo object.
    There are some special cases which are handled individually such as:
     
     * SpikeSourcePoisson
    
    :param name: string
    :param component_info: AL Component object
    :param rng: numpy.random.RandomState object
    :param parameters: python dictionary 'name' : value
    
    :rtype: daetoolsComponent object
    :raises: RuntimeError 
    """
    neurone = None
    """
    ACHTUNG, ACHTUNG!!
    We should handle components' with names that mean something. How can we know that 
    the spike_source_poisson component should be treated differently by a simulator?
    The same stands for other types of components.
    """
    if component_info.name == 'spike_source_poisson':
        if 'rate' in parameters:
            rate = float(parameters['rate'][0])
        else:
            raise RuntimeError('The SpikeSourcePoisson component: must have [rate] parameter')
        
        if 'duration' in parameters:
            duration = float(parameters['duration'][0])
        else:
            raise RuntimeError('The SpikeSourcePoisson component: must have [duration] parameter')
        
        if 't0' in parameters:
            t0 = float(parameters['t0'][0])
        else:
            t0 = 0.0

        lambda_ = rate * duration

        spiketimes = createPoissonSpikeTimes(rate, duration, t0, rng, lambda_, rng)
        neurone    = daetoolsSpikeSource(spiketimes, name, None, '')
    
    else:
        neurone = daetoolsComponent(component_info, fixObjectName(name), None, '')
        neurone.Nitems = 1
        neurone.initialize()
    
    spike_event_port = neurone.getOutletEventPort()
    neurone.on_spike_out_action = daetoolsOnSpikeOutAction(neurone, spike_event_port)
    neurone.ON_EVENT(spike_event_port, userDefinedActions = [neurone.on_spike_out_action])
    
    return neurone

def creatALFromULComponent(ul_component, random_number_generators):
    """
    Creates AL component referenced in the given UL component and does some additional
    processing depending on its type. Returns an AL Component object. 
    An exception can be thrown for the following reasons:
     
     * The component at the specified URL does not exist, invalid url, etc.
     * The component exists but the parser cannot parse it
     * Vatican
     * The Illuminati
     * Jesuits
     * WZO
     * Freemasons
     * The Knights of Malta
     * The Order of the Rose Cross
     * Communists
     * :-)
    
    :param ul_component: UL Component object
    :param random_number_generators: python dictionary 'UL Component name' : daetoolsRNG object (numpy RandomState based)
    
    :rtype: tuple (daetoolsComponentInfo object, AL Component object, UL Component object, dictionary with parameters)
    :raises: RuntimeError 
    """
    
    try:
        # Check if the URL is valid and load it
        f = urllib.urlopen(ul_component.definition.url)
    
    except Exception as e:
        raise RuntimeError('Cannot resolve the component: {0}, definition url: {1}, error: {2}'.format(ul_component.name, ul_component.definition.url, str(e)))
    
    try:
        # Parse the xml file and create the component-info object needed 
        # to repeatedly instantiate neurones/synapses:
        al_component   = nineml.abstraction_layer.readers.XMLReader.read(ul_component.definition.url) 
        component_info = daetoolsComponentInfo(al_component.name, al_component)
        parameters     = fixParametersDictionary(ul_component.parameters)
    
    except Exception as e:
        raise RuntimeError('The component: {0} failed to parse: {1}'.format(ul_component.name, str(e)))

    # Do the additional processing, depending on the component's type.
    # Should be completed (as needed) in the future.
    try:
        if isinstance(ul_component, nineml.user_layer.ConnectionRule):
            pass
        
        elif isinstance(ul_component, nineml.user_layer.ConnectionType):
            pass
        
        elif isinstance(ul_component, nineml.user_layer.SpikingNodeType):
            pass
        
        elif isinstance(ul_component, nineml.user_layer.SynapseType):
            pass
        
        elif isinstance(ul_component, nineml.user_layer.CurrentSourceType):
            pass
        
        elif isinstance(ul_component, nineml.user_layer.Structure):
            pass
        
        elif isinstance(ul_component, nineml.user_layer.RandomDistribution):
            # Add a new RNG with the name of the UL component as a key
            # to the *random_number_generators* dictionary
            if not ul_component.name in random_number_generators:
                rng = daetoolsRNG.createRNG(al_component, parameters)
                random_number_generators[ul_component.name] = rng
    
    except Exception as e:
        raise RuntimeError('The component: {0} failed to parse: {1}'.format(ul_component.name, str(e)))
    
    return (component_info, al_component, ul_component, parameters)

class daetoolsPointNeuroneNetwork(object):
    """
    Wraps and handles user-layer Model objects.
    """
    def __init__(self, ul_model):
        """
        :param ul_model: UL Model object
        
        :raises: RuntimeError
        """
        self._name            = fixObjectName(ul_model.name)
        self._components      = {}
        self._groups          = {}
        self._rngs            = {}
        
        for name, ul_component in ul_model.components.iteritems():
            self._components[name] = creatALFromULComponent(ul_component, self._rngs)
        
        for name, ul_group in ul_model.groups.iteritems():
            self._groups[name] = daetoolsGroup(name, ul_group, self)
        
    def __repr__(self):
        res = 'daetoolsPointNeuroneNetwork({0})\n'.format(self._name)
        res += '  components:\n'
        for name, o in list(self._components.items()):
            res += '  {0} : {1}\n'.format(name, repr(o))
        res += '  groups:\n'
        for name, o in list(self._groups.items()):
            res += '  {0} : {1}\n'.format(name, repr(o))
        return res

    def getComponentInfo(self, name):
        """
        :param name: string
        
        :rtype: AL Component object
        :raises: RuntimeError, IndexError
        """
        if not name in self._components:
            raise RuntimeError('Component [{0}] does not exist in the network'.format(name)) 
        return self._components[name][0]

    def getALComponent(self, name):
        """
        :param name: string
        
        :rtype: AL Component object
        :raises: RuntimeError, IndexError
        """
        if not name in self._components:
            raise RuntimeError('Component [{0}] does not exist in the network'.format(name)) 
        return self._components[name][1]

    def getULComponent(self, name):
        """
        :param name: string
        
        :rtype: UL BaseComponent-derived object
        :raises: RuntimeError, IndexError
        """
        if not name in self._components:
            raise RuntimeError('Component [{0}] does not exist in the network'.format(name)) 
        return self._components[name][2]

    def getComponentParameters(self, name):
        """
        :param name: string
        
        :rtype: dictionary 'name':(value, unit)
        :raises: RuntimeError, IndexError
        """
        if not name in self._components:
            raise RuntimeError('Component [{0}] does not exist in the network'.format(name)) 
        return self._components[name][3]

    def getGroup(self, name):
        """
        :param name: string
        
        :rtype: daetoolsGroup object
        :raises: RuntimeError
        """
        if not name in self._groups:
            raise RuntimeError('Group [{0}] does not exist in the network'.format(name)) 
        return self._groups[name]

    @property
    def randomNumberGenerators(self):
        return self._rngs
    
    @property
    def globalRandomNumberGenerator(self):
        return nineml_daetools_component._global_rng_

class daetoolsGroup(object):
    """
    Wraps and handles user-layer Group objects.
    """
    def __init__(self, name, ul_group, network):
        """
        :param name: string
        :param ul_group: UL Group object
        :param network: daetoolsPointNeuroneNetwork object
        
        :rtype:
        :raises: RuntimeError
        """
        self._name        = fixObjectName(name)
        self._populations = {}
        self._projections = {}
        
        for i, (name, ul_population) in enumerate(ul_group.populations.iteritems()):
            self._populations[name] = daetoolsPopulation(name, ul_population, network, i)
        
        for i, (name, ul_projection) in enumerate(ul_group.projections.items()):
            self._projections[name] = daetoolsProjection(name, ul_projection, self, network)
    
    def __repr__(self):
        res = 'daetoolsGroup({0})\n'.format(self._name)
        res += '  populations:\n'
        for name, o in list(self._populations.items()):
            res += '  {0} : {1}\n'.format(name, repr(o))
        res += '  projections:\n'
        for name, o in list(self._projections.items()):
            res += '  {0} : {1}\n'.format(name, repr(o))
        return res

    def getPopulation(self, name):
        """
        :param name: string
        
        :rtype: daetoolsPopulation object
        :raises: RuntimeError
        """
        if not name in self._populations:
            raise RuntimeError('Population [{0}] does not exist in the group'.format(name)) 
        return self._populations[name]
        
    def getProjection(self, name):
        """
        :param name: string
        
        :rtype: daetoolsProjection object
        :raises: RuntimeError
        """
        if not name in self._projections:
            raise RuntimeError('Projection [{0}] does not exist in the group'.format(name)) 
        return self._projections[name]

class daetoolsPopulation(object):
    """
    A class that wraps and handles user-layer Population objects.
    """
    def __init__(self, name, ul_population, network, population_id):
        """
        :param name: string
        :param ul_population: UL Population object
        :param network: daetoolsPointNeuroneNetwork object
        :param population_id: integer
        
        :rtype: 
        :raises: RuntimeError
        """
        self._name           = fixObjectName(name)
        self._population_id  = population_id
        self._parameters     = network.getComponentParameters(ul_population.prototype.name)
        
        _component_info  = network.getComponentInfo(ul_population.prototype.name) 
        
        self.neurones = [
                           createNeurone(
                                           'p{0}({1:0>4})'.format(self._population_id, i),  # Name
                                           _component_info,                                 # daetoolsComponentInfo object
                                           network.globalRandomNumberGenerator,             # RNG 
                                           self._parameters                                 # dict with init. parameters
                                        ) for i in xrange(0, ul_population.number)
                         ]
        
    def getNeurone(self, index):
        """
        :param index: integer
        
        :rtype: daetoolsComponent object
        :raises: IndexError
        """
        return self.neurones[int(index)]

    def __repr__(self):
        res = 'daetoolsPopulation({0})\n'.format(self._name)
        res += '  neurones:\n'
        for o in self.neurones:
            res += '  {0}\n'.format(repr(o))
        return res

class daetoolsProjection(object):
    """
    Wraps and handles user-layer Projection objects.
    
    ACHTUNG, ACHTUNG!!
    Currently, we support only populations of spiking neurones (not groups).
    """
    def __init__(self, name, ul_projection, group, network):
        """
        :param name: string
        :param ul_projection: UL Projection object
        :param group: daetoolsGroup object
        :param network: daetoolsPointNeuroneNetwork object
        
        :rtype:
        :raises: RuntimeError
        """
        self.name          = fixObjectName(name)
        self.minimal_delay = 1.0e10
        
        if not isinstance(ul_projection.source.prototype, nineml.user_layer.SpikingNodeType):
            raise RuntimeError('Currently, only populations of spiking neurones (not groups) are supported')
        if not isinstance(ul_projection.target.prototype, nineml.user_layer.SpikingNodeType):
            raise RuntimeError('Currently, only populations of spiking neurones (not groups) are supported')
        
        source_population  = group.getPopulation(ul_projection.source.name)
        target_population  = group.getPopulation(ul_projection.target.name)
        psr_parameters     = network.getComponentParameters(ul_projection.synaptic_response.name)
        connection_rule    = network.getALComponent(ul_projection.rule.name)
        connection_type    = network.getALComponent(ul_projection.connection_type.name)
        psr_component_info = network.getComponentInfo(ul_projection.synaptic_response.name)
        source_name        = fixObjectName(ul_projection.source.name)
        target_name        = fixObjectName(ul_projection.target.name)
        synapse_name       = fixObjectName(ul_projection.synaptic_response.name)
        
        self._synapses = [
                          daetoolsComponent(
                                             psr_component_info, 
                                            's(p{0},p{1})'.format(source_population._population_id, target_population._population_id),
                                            target_population.getNeurone(i), 
                                            ''
                                           ) for i in xrange(0, ul_projection.target.number)
                         ]               
        
        for i, neurone in enumerate(target_population.neurones):
            neurone.incoming_synapses.append( (self._synapses[i], psr_parameters) ) 
        
        # Create an object that supports the Geometry interface 
        geometry = geometryFromProjection(ul_projection)
        #print('Metric({0},{1}) = {2}'.format(0, 15, geometry.metric(0, 15)))
        
        # Create an object that supports the ConnectionGenerator interface and set-up connections
        mask = connection_generator.Mask([(0, ul_projection.source.number - 1)], [(0, ul_projection.target.number - 1)])
        cgi = connectionGeneratorFromProjection(ul_projection, geometry)
        cgi.setMask(mask)
        self.createConnections(cgi, source_population, target_population)
        
        # Now we are done with connections. Initialize synapses
        for i, neurone in enumerate(target_population.neurones):
            synapse = self._synapses[i]
            synapse.initialize()
            neurone.connectAnaloguePorts(synapse, neurone)

    def __repr__(self):
        res = 'daetoolsProjection({0})\n'.format(self.name)
        return res
        
    def getSynapse(self, index):
        """
        :param index: integer
        
        :rtype: None
        :raises: IndexError
        """
        return self._synapses[index]

    def createConnections(self, cgi, source_population, target_population):
        """
        Iterates over ConnectionGeneratorInterface object and creates connections.
        It connects source->target neurones and (optionally) sets weights and delays
        
        :param cgi: ConnectionGenerator interface object
        
        :rtype: None
        :raises: RuntimeError
        """
        count = 0
        for connection in cgi:
            size = len(connection)
            if(size < 2):
                raise RuntimeError('Not enough data in the explicit lists of connections')
            
            source_index = int(connection[0])
            target_index = int(connection[1])
            weight       = 0.0
            delay        = 0.0
            parameters   = []
            
            if cgi.arity == 1:
                weight = float(connection[2]) * 1E-6 # nS -> S
            elif cgi.arity == 2:
                weight = float(connection[2]) * 1E-6 # nS -> S
                delay  = float(connection[3]) * 1E-3 # ms -> s
            elif cgi.arity >= 3:
                weight = float(connection[2]) * 1E-6 # nS -> S
                delay  = float(connection[3]) * 1E-3 # ms -> s
                for i in range(4, size):
                    parameters.append(float(connection[i]))           
            
            source_neurone = source_population.getNeurone(source_index)
            target_neurone = target_population.getNeurone(target_index)
            synapse        = self.getSynapse(target_index)
            
            if delay < self.minimal_delay:
                self.minimal_delay = delay
            
            # Add the new item to the list of connected synapse event ports and connection delays.
            # Here we cannot add an event port directly since it does not exist yet.
            # Therefore, we add the synapse object and the index of the event port.
            source_neurone.target_synapses.append( (synapse, synapse.Nitems, delay, target_neurone) )
            synapse.Nitems += 1
            # Weights cannot be set right now. Thus, we put them into an array.
            synapse.synapse_weights.append(weight)
            count += 1
        
        print('{0}: created {1} connections'.format(self.name, count))

class daetoolsPointNeuroneSimulation(pyActivity.daeSimulation):
    """
    Simulates a single neurone with all *incoming* synapses.
    """
    def __init__(self, neurone, neurone_parameters, neurone_report_variables):
        """
        :rtype:
        :raises: RuntimeError
        """
        pyActivity.daeSimulation.__init__(self)
        
        neurone.simulation = self
        
        self.m                        = neurone
        self.neurone_parameters       = neurone_parameters
        self.neurone_report_variables = neurone_report_variables
        self.forthcoming_events       = []
        self.daesolver                = pyIDAS.daeIDAS()
        
        """
        Regarding the linear solver, we have three options:
         1. Built-in dense LU
         2. SuperLU 
         3. Dense Lapack (libblas.so and liblapack.so are required; that can be Atlas, ACML, MKL, GotoBlas ...)
        Uncomment one of 3 options below and comment the rest.
        
        Some hints:
         * For small networks: some dense it does not really matter which solver.
         * For medium networks: dense Lapack.
         * For large networks: SuperLU
        """
        # 1. No need to do anything (Sundials LU is the default solver)
        
        # 2. SuperLU LA Solver (uncomment the lines below)
        #self.lasolver                 = pySuperLU.daeCreateSuperLUSolver()
        #self.daesolver.SetLASolver(self.lasolver)
        
        # 3. Lapack LA Solver (uncomment the lines below)
        self.daesolver.SetLASolver(pyIDAS.eSundialsLapack)

    def init(self, log, datareporter, reportingInterval, timeHorizon):
        self.ReportingInterval = reportingInterval
        self.TimeHorizon       = timeHorizon
        self.Initialize(self.daesolver, datareporter, log)
        
    def SetUpParametersAndDomains(self):
        """
        :rtype: None
        :raises: RuntimeError
        """
        # 1. Set the neurone model parameters
        daetoolsComponentSetup.setUpParametersAndDomains(self.m, self.neurone_parameters)
        
        # 2a. Set the incoming synapses' parameters (for they belong to this neurone)
        # 2b. Set the incoming synapses' weights
        for (synapse, synapse_parameters) in self.m.incoming_synapses:
            daetoolsComponentSetup.setUpParametersAndDomains(synapse, synapse_parameters)
            daetoolsComponentSetup.setWeights(synapse, synapse.synapse_weights)            
        
    def SetUpVariables(self):
        """
        :rtype: None
        :raises: RuntimeError
        """
        daetoolsComponentSetup.setUpVariables(self.m, self.neurone_parameters, self.neurone_report_variables)
        for (synapse, synapse_parameters) in self.m.incoming_synapses:
            daetoolsComponentSetup.setUpVariables(synapse, synapse_parameters, {})

    def CleanUpSetupData(self):
        pyActivity.daeSimulation.CleanUpSetupData(self)
        self.m.CleanUpSetupData()

class daetoolsPointNeuroneNetworkSimulation(object):
    """
    Simulates a network of neurones (specified by a daetoolsPointNeuroneNetworkSimulation object) 
    and produces outputs according to information in a SED-ML experiment object.
    The daetoolsPointNeuroneNetworkSimulation object can be obtained from the SED-ML experiment object.
    """
    def __init__(self, sedml_experiment):
        """
        :rtype: None
        :raises: RuntimeError
        """
        self.name                = ''
        self.network             = None
        self.reportingInterval   = 0.0
        self.timeHorizon         = 0.0        
        self.log                 = daeLogs.daePythonStdOutLog()
        self.datareporter        = pyDataReporting.daeNoOpDataReporter() #pyDataReporting.daeTCPIPDataReporter()
        self.simulations         = []
        self.events_heap         = []
        self.average_firing_rate = {}
        self.raster_plot_data    = []
        self.pathParser          = CanonicalNameParser()
        self.report_variables    = {}
        self.output_plots        = []
        self.number_of_equations = 0
        self.number_of_neurones  = 0
        self.number_of_synapses  = 0
        self.spike_count         = 0
        self.minimal_delay       = 1.0E10

        heapify(self.events_heap)
        
        # Create daetoolsPointNeuroneNetwork object and the simulation runtime information
        self.processSEDMLExperiment(sedml_experiment)
        
        # Connect the DataReporter
        simName = self.name + strftime(" [%d.%m.%Y %H.%M.%S]", localtime())
        if not self.datareporter.Connect("", simName):
            raise RuntimeError('Cannot connect the data reporter')
        
        # Set the random number generators of the daetoolsComponentSetup
        daetoolsComponentSetup._random_number_generators = self.network.randomNumberGenerators

        # Setup neurones
        try:
            self.log.Enabled = False
            
            for group_name, group in self.network._groups.iteritems():
                for projection_name, projection in group._projections.iteritems():
                    if projection.minimal_delay < self.minimal_delay:
                        self.minimal_delay = projection.minimal_delay
                    
                for population_name, population in group._populations.iteritems():
                    print("Creating simulations for: {0}...".format(population_name))
                    for neurone in population.neurones:
                        simulation = daetoolsPointNeuroneSimulation(neurone, population._parameters, {})
                        neurone.events_heap = self.events_heap
                        self.simulations.append(simulation)
                        self.number_of_neurones += 1
                        for (synapse, params) in neurone.incoming_synapses:
                            self.number_of_synapses += synapse.Nitems                            
            
            self.simulations.sort()
            
            if self.minimal_delay < self.reportingInterval:
                raise RuntimeError('The minimal delay ({0}s) is greater than the reporting interval ({1}s)'.format(self.minimal_delay, self.reportingInterval))
            
        except:
            raise
        
        finally:
            self.log.Enabled = True

    def initializeAndSolveInitial(self):
        try:
            self.log.Enabled = False
            
            self.number_of_equations = 0
            for i, simulation in enumerate(self.simulations):
                print 'Setting up the neurone {0} out of {1} (total number of equations: {2})...'.format(i+1, self.number_of_neurones, self.number_of_equations), "\r",
                sys.stdout.flush()
                
                simulation.init(self.log, self.datareporter, self.reportingInterval, self.timeHorizon)
                self.number_of_equations += simulation.daesolver.NumberOfVariables
                
                simulation.SolveInitial()
                simulation.CleanUpSetupData()
        
        except:
            raise
        
        finally:
            print '\n'
            self.log.Enabled = True
        
        # Run the garbage collector to free some memory
        #print('garbage before collect:\n'.format(gc.garbage))
        collected = gc.collect()
        #print "Garbage collector: collected %d objects." % (collected)  
        #print('garbage after collect:\n'.format(gc.garbage))
    
    def run(self):
        # First create the reporting times list
        reporting_times = numpy.arange(self.reportingInterval, self.timeHorizon, self.reportingInterval)
        
        prev_time = 0.0
        # Iterate over the queue. The (delayed) events will be added to the queue as they are trigerred.
        for next_time in reporting_times:
            self.log.Message("Simulating from {0:.5f}s to {1:.5f}s...".format(prev_time, next_time), 0)
            
            try:
                while True:
                    # Get the first item from the heap
                    (t_event, inlet_event_port, target_neurone) = heappop(self.events_heap)
                    
                    # If out of the interval put it back
                    if t_event > next_time:
                        heappush(self.events_heap, (t_event, inlet_event_port, target_neurone))
                        break
                    
                    #print('{0} --> {1}s (trigger event on {2})'.format(target_neurone.Name, t_event, inlet_event_port.CanonicalName))
                    
                    # Integrate until next event time and report the data if there is a discontinuity
                    target_neurone.simulation.IntegrateUntilTime(t_event, pyActivity.eDoNotStopAtDiscontinuity, True)
                    
                    # Trigger the event and reinitialize the system
                    inlet_event_port.ReceiveEvent(t_event)
                    target_neurone.simulation.Reinitialize()
                    
                    self.spike_count += 1
            
            except IndexError:
                pass
                
            # Integrate each neurone until the *next_time* is reached and report the data
            for simulation in self.simulations:
                #print('{0}........ {1} {2} {3}'.format(simulation.m.Name, 
                #                                       simulation.CurrentTime, 
                #                                       '<' if simulation.CurrentTime < next_time else '=' , 
                #                                       next_time))
                if simulation.CurrentTime < next_time:
                    simulation.IntegrateUntilTime(next_time, pyActivity.eDoNotStopAtDiscontinuity, True)
                simulation.ReportData(next_time)
            
            # Set the progress
            self.log.SetProgress(100.0 * next_time / self.timeHorizon)
            prev_time = next_time
                    
        print('Simulation has ended successfuly.')
        print('Processing the results...')
        
        # Finally, process the results (generate 2D plots, raster plots, and other voodoo-mojo stuff)
        self.processResults()
    
    def processSEDMLExperiment(self, sedml_experiment):
        if len(sedml_experiment.tasks) != 1:
            raise RuntimeError('The number of SED-ML tasks must be one')
        sedml_task = sedml_experiment.tasks[0]
 
        self.name    = sedml_task.simulation.name
        ul_model     = sedml_task.model.getUserLayerModel()
        self.network = daetoolsPointNeuroneNetwork(ul_model)
        
        self.reportingInterval = float(sedml_task.simulation.outputEndTime - sedml_task.simulation.outputStartTime) / (sedml_task.simulation.numberOfPoints - 1)
        self.timeHorizon       = float(sedml_task.simulation.outputEndTime)
        
        for data_generator in sedml_experiment.data_generators:
            for variable in data_generator.variables:
                if variable.target:
                    try:
                        items = self.pathParser.parse(str(variable.target))
                    except Exception as e:
                        RuntimeError('Invalid SED-ML variable name: {0}'.format(variable.target))
                    
                    if len(items) != 3:
                        raise RuntimeError('Invalid SED-ML variable name: {0}'.format(variable.target))
                    
                    if items[0].Type != pathItem.typeID:
                        raise RuntimeError('Invalid SED-ML variable name: {0}'.format(variable.target))
                    group = self.network.getGroup(items[0].Name)       
                    
                    if items[1].Type != pathItem.typeIndexedID:
                        raise RuntimeError('Invalid SED-ML variable name: {0}'.format(variable.target))
                    population = group.getPopulation(items[1].Name)  
                    neurone = population.getNeurone(items[1].Index)
                    
                    if items[2].Type != pathItem.typeID:
                        raise RuntimeError('Invalid SED-ML variable name: {0}'.format(variable.target))
                    variable_name = items[2].Name
                    
                    if variable_name in neurone.nineml_aliases:
                        dae_variable = neurone.nineml_aliases[variable_name]
                    
                    elif variable_name in neurone.nineml_variables:
                        dae_variable = neurone.nineml_variables[variable_name]
                    
                    elif variable_name in neurone.nineml_inlet_ports:
                        dae_variable = neurone.nineml_inlet_ports[variable_name]
                    
                    elif variable_name in neurone.nineml_reduce_ports:
                        dae_variable = neurone.nineml_reduce_ports[variable_name]
                    
                    else:
                        raise RuntimeError('Cannot find SED-ML variable: {0}'.format(variable.target))
                        
                    self.report_variables[variable.target] = dae_variable
                    dae_variable.ReportingOn = True
                    
                elif variable.symbol:
                    if variable.symbol == 'urn:sedml:symbol:time':
                        self.report_variables['time'] = None
                    else:
                        raise RuntimeError('Unsupported SED-ML symbol: {0}'.format(variable.symbol))
                
                else:
                    raise RuntimeError('Both SED-ML variable symbol and target are None')
              
        for output in sedml_experiment.outputs:
            variable_names  = []
            x_label         = 'Time, s'
            y_labels        = []
            x_log           = False
            y_log           = False
            
            for curve in output.curves:
                if curve.logX:
                    x_log = True
                if curve.logY:
                    y_log = True
                
                x_dg = curve.xDataRefference
                y_dg = curve.yDataRefference
                
                if (len(x_dg.variables) != 1) or (not x_dg.variables[0].symbol) or (x_dg.variables[0].symbol != 'urn:sedml:symbol:time'):
                    raise RuntimeError('The number of variables in data referrence: {0} must be one with the symbol = urn:sedml:symbol:time'.format(x_dg.id))
                
                for variable in y_dg.variables:
                    if not variable.target:
                        raise RuntimeError('SED-ML variable: {0} target is invalid'.format(variable.name))
                    if not variable.target in self.report_variables:
                        raise RuntimeError('SED-ML variable {0} does not exist in the network'.format(variable.name))
                    
                    variable_names.append(self.report_variables[variable.target].CanonicalName)
                    y_labels.append(variable.name)
            
            self.output_plots.append( (output.name, variable_names, x_label, y_labels, x_log, y_log) )
        
    def processResults(self):
        results_dir = '{0} {1}'.format(self.name, strftime("[%d.%m.%Y %H.%M.%S]", localtime()))
        os.mkdir(results_dir)
        
        print('  Total number of equations: {0:>10d}'.format(self.number_of_equations))
        print('  Total number of neurones:  {0:>10d}'.format(self.number_of_neurones))
        print('  Total number of synapses:  {0:>10d}'.format(self.number_of_synapses))
        print('  Total number of spikes:    {0:>10d}'.format(self.spike_count))
        print('  Minimal network delay:    {0:>10.6f}s'.format(self.minimal_delay))
        
        # 1. Create a raster plot file (.ras)
        neurone_index = 0
        population_events = {}
        for group_name, group in self.network._groups.iteritems():
            for population_name, population in group._populations.iteritems():
                count = 0
                events = []
                for neurone in population.neurones:
                    event_port = neurone.getOutletEventPort()
                    count += len(event_port.Events)
                    for (t, data) in event_port.Events:
                        self.raster_plot_data.append((t, neurone_index))
                        events.append((t, neurone_index))
                    neurone_index += 1
                
                population_events[population_name] = sorted(events)
                self.average_firing_rate[population_name] = count / (self.timeHorizon * len(population.neurones))
                print('  [{0}] average firing rate: {1:.3f} Hz'.format(population_name, self.average_firing_rate[population_name]))
        
        self.raster_plot_data.sort()
        self.createRasterFile(os.path.join(results_dir, 'raster-plot.ras'), self.raster_plot_data, self.number_of_neurones)
        
        # 2. Create a raster plot image (.png)
        pop_times   = []
        pop_indexes = []
        pop_names   = []
        for i, (population_name, events) in enumerate(population_events.iteritems()):
            if len(events) > 0:
                pop_times.append( [item[0] for item in events] )
                pop_indexes.append( [item[1] for item in events] )
                pop_names.append( population_name )
        self.createRasterPlot(os.path.join(results_dir, 'raster-plot.png'), pop_times, pop_indexes, pop_names)
        
        # 3. Create 2D plots (.png)
        for (name, variable_names, x_label, y_labels, x_log, y_log) in self.output_plots:
            x_values = []
            y_values = []
            for var_canonical_name in variable_names:
                for variable in self.datareporter.Process.Variables:
                    if var_canonical_name == variable.Name:
                        x_values.append(variable.TimeValues)
                        y_values.append(variable.Values.reshape(len(variable.Values)))
            
            self.create2DPlot(os.path.join(results_dir, '{0}.png'.format(name)), x_values, y_values, x_label, y_labels, x_log, y_log)

    @staticmethod
    def createRasterFile(filename, data, n):
        """
        :param filename: string
        :param data: list of floats
        :param n: integer
        
        :rtype: None
        :raises: IOError
        """
        f = open(filename, "w")
        f.write('# size = {0}\n'.format(n))
        f.write('# first_index = {0}\n'.format(0))
        f.write('# first_id = {0}\n'.format(0))
        f.write('# n = {0}\n'.format(len(data)))
        f.write('# variable = spikes\n')
        f.write('# last_id = {0}\n'.format(n - 1))
        f.write('# dt = {0}\n'.format(0.0))
        f.write('# label = {0}\n'.format('spikes'))
        for t, index in data:
            f.write('%.14e\t%d\n' % (t, index))
        f.close()

    @staticmethod
    def createRasterPlot(filename, pop_times, pop_indexes, pop_names):
        """
        :param filename: string
        :param pop_times: 2D list (list of float lists)
        :param pop_indexes: 2D list (list of integer lists)
        :param pop_names: string list
        
        :rtype: None
        :raises: ValueError, IOError
        """
        font = {'family' : 'serif',
                'weight' : 'normal',
                'size'   : 8}
        matplotlib.rc('font', **font)
        params = {'axes.labelsize' : 10,
                  'legend.fontsize': 5,
                  'text.fontsize'  : 8,
                  'xtick.labelsize': 8,
                  'ytick.labelsize': 8,
                  'text.usetex':     False}
        matplotlib.rcParams.update(params)

        colors = ['red', 'blue', 'green', 'black', 'c', 'm', 'k', 'y']
        
        figure = Figure(figsize=(8, 6))
        canvas = FigureCanvas(figure)
        axes = figure.add_subplot(111)
        
        axes.set_xlabel('Time, s')
        axes.set_ylabel('Neurones')
        axes.grid(True, linestyle = '-', color = '0.75')
        
        i = 0
        min_times   = 1.0E10
        max_times   = 0.0
        min_indexes = 1E10
        max_indexes = 0
        for (times, indexes, name) in zip(pop_times, pop_indexes, pop_names):
            color = colors[i % len(colors)]
            if len(times) > 0:
                axes.scatter(times, indexes, label = name, marker = 's', s = 1, color = color)
                
                min_times   = min(min_times,   min(times))
                max_times   = max(max_times,   max(times))
                min_indexes = min(min_indexes, min(indexes))
                max_indexes = max(max_indexes, max(indexes)) + 1
            i += 1
        
        box = axes.get_position()
        axes.set_position([box.x0, box.y0, box.width * 0.9, box.height])
        axes.legend(loc = 'center left', bbox_to_anchor = (1, 0.5), ncol = 1, scatterpoints = 1, fancybox = True)
        
        axes.set_xbound(lower = min_times,   upper = max_times)
        axes.set_ybound(lower = min_indexes, upper = max_indexes)
        
        canvas.print_figure(filename, dpi = 300)        
    
    @staticmethod
    def create2DPlot(filename, x_values, y_values, x_label, y_labels, x_log, y_log):
        """
        :param filename: string
        :param x_values: 2D list (list of float lists)
        :param y_values: 2D list (list of float lists)
        :param x_label: string
        :param y_labels: string list
        :param x_log: bool
        :param y_log: bool
        
        :rtype: None
        :raises: ValueError, IOError
        """
        font = {'family' : 'serif',
                'weight' : 'normal',
                'size'   : 8}
        matplotlib.rc('font', **font)
        params = {'axes.labelsize':  9,
                  'legend.fontsize': 6,
                  'text.fontsize':   8,
                  'xtick.labelsize': 8,
                  'ytick.labelsize': 8,
                  'text.usetex':     False}
        matplotlib.rcParams.update(params)
        
        colors = ['blue', 'red', 'green', 'black', 'c', 'm', 'k', 'y']

        figure = Figure(figsize=(8, 6))
        canvas = FigureCanvas(figure)
        axes = figure.add_subplot(111)
        axes.set_xlabel(x_label)
        axes.grid(True, linestyle = '-', color = '0.75')
        
        i = 0
        for (x, y, label) in zip(x_values, y_values, y_labels):
            color = colors[i % len(colors)]
            axes.plot(x, y, label = label, 
                            color = color, 
                            linewidth = 0.5, 
                            linestyle = 'solid', 
                            marker  ='', 
                            markersize = 0, 
                            markerfacecolor = color, 
                            markeredgecolor = color)
            i += 1
            
        axes.legend(loc = 0, ncol = 1, fancybox = True)
        
        if x_log: 
            axes.set_xscale('log')
        else:
            axes.set_xscale('linear')
        if y_log:
            axes.set_yscale('log')
        else:
            axes.set_yscale('linear')
        
        canvas.print_figure(filename, dpi = 300)        
        
    def finalize(self):
        for simulation in self.simulations:
            simulation.Finalize()
        
def readCSV_pyNN(filename):
    """
    Reads pyNN .conn files and returns a list of connections: [(int, int, float, float), ...]
    
    ACHTUNG, ACHTUNG!!!
    Weights are given in nano-Siemens and delays in mili-seconds!
    """
    connections_out = []
    connections = csv.reader(open(filename, 'rb'), delimiter='\t')
    for connection in connections:
        s = int(float(connection[0]))
        t = int(float(connection[1]))
        w = float(connection[2]) # nS
        d = float(connection[3]) # ms
        connections_out.append((s, t, w, d))
        
    print('Parsed [{0}] file; number of connections: {1}'.format(filename, len(connections_out)))
    return connections_out
        
def profileSimulate():
    """
    Some voodoo mojo stuff needed to profile the script.
    """
    import hotshot
    from hotshot import stats
    
    prof = hotshot.Profile("nineml_point_neurone_network.profile", lineevents = 1)
    try:
        prof.runcall(simulate)
    except:
        pass
    prof.close()
    
    s = stats.load("nineml_point_neurone_network.profile")
    s.strip_dirs().sort_stats("time").print_stats()

def getULModelAndSimulationInputs():
    """
    Returns a sedmlExperiment object including a neural-network 
    (in an user-layer Model object), run-time simulation data and
    information needed to produce results.
    """
    
    ###############################################################################
    #                           NineML UserLayer Model
    ###############################################################################
    """
    If True use CSA to handle connections; 
    otherwise use the lists of explicit connections
    """
    useCSA = True
    
    """
    If explicit lists of connections are used then the number of neurones can be 100, 1000 and 2000
    since we have generated connections only for that numbers.
    Otherwise, CSA can handle any number.
    """
    N_neurons = 100
    N_exc     = int(N_neurons * 0.8)
    N_inh     = int(N_neurons * 0.2)
    N_poisson = 20
    
    connections_folder = str(N_neurons)

    if not useCSA:
        if N_neurons not in [100, 1000, 2000]:
            raise RuntimeError('If explicit lists of connections are used then the number of neurones can only be 100, 1000 and 2000')
    
    """
    Ideally the catalog folder should be:
       catalog = 'file://' + os.path.join(sys.path[0], 'catalog')
    but for some reasons it can't be resolved in windows. 
    """
    catalog = 'catalog'
       
    """
    All parameters values are in base SI units. The values are adopted from the Brette et al paper.
    Their values are for the network with 4000 neurones; the weights here should be changed to
    account for the lower number of neurones.
    """
    
    rnd_uniform_params = {
                          'lowerBound': (-0.060, "dimensionless"),
                          'upperBound': (-0.040, "dimensionless")
                         }
    uni_distr = nineml.user_layer.RandomDistribution("uniform(-0.060, -0.040)", os.path.join(catalog, "uniform_distribution.xml"), rnd_uniform_params)
    
    poisson_params = {
                      'rate'     : (100.00, 'Hz'),
                      'duration' : (  0.05, 's'),
                      't0'       : (  0.00, 's')
                    }
    
    neurone_params = {
                      'tspike' :    ( -1.000,   's'),
                      'V' :         (uni_distr, 'V'),
                      'gl' :        ( 1.0E-8,   'S'),
                      'vreset' :    ( -0.060,   'V'),
                      'taurefrac' : (  0.001,   's'),
                      'vthresh' :   ( -0.040,   'V'),
                      'vrest' :     ( -0.060,   'V'),
                      'cm' :        ( 0.2E-9,   'F')
                     }
    
    psr_poisson_params = {
                          'vrev'   : (   0.000, 'V'),
                          'weight' : (100.0E-9, 'S'),
                          'tau'    : (   0.005, 's'),
                          'g'      : (   0.000, 'S')
                         }

    psr_excitatory_params = {
                             'vrev'  : (  0.000, 'V'),
                             'weight': ( 4.0E-9, 'S'),
                             'tau'   : (  0.005, 's'),
                             'g'     : (  0.000, 'S')
                            }
                    
    psr_inhibitory_params = {
                             'vrev'   : ( -0.080, 'V'),
                             'weight' : (51.0E-9, 'S'),
                             'tau'    : (  0.010, 's'),
                             'g'      : (  0.000, 'S')
                            }
    
    neurone_IAF     = nineml.user_layer.SpikingNodeType("IAF neurone", os.path.join(catalog, "iaf.xml"), neurone_params)
    
    neurone_poisson = nineml.user_layer.SpikingNodeType("Poisson Source", os.path.join(catalog, "spike_source_poisson.xml"), poisson_params)
    
    psr_poisson     = nineml.user_layer.SynapseType("COBA poisson",    os.path.join(catalog, "coba_synapse.xml"), psr_poisson_params)
    psr_excitatory  = nineml.user_layer.SynapseType("COBA excitatory", os.path.join(catalog, "coba_synapse.xml"), psr_excitatory_params)
    psr_inhibitory  = nineml.user_layer.SynapseType("COBA inhibitory", os.path.join(catalog, "coba_synapse.xml"), psr_inhibitory_params)
    
    grid2d_params = {
                      'x0'            : (0.00, 'm'),
                      'y0'            : (0.00, 'm'), 
                      'dx'            : (1E-5, 'm'),
                      'dy'            : (1E-5, 'm'),
                      'fillOrder'     : (0.00, ' '),
                      'aspectRatioXY' : (0.00, ' ')
                    }
    grid2D = nineml.user_layer.Structure("2D Grid", os.path.join(catalog, "grid_2d.xml"), grid2d_params)
    
    connection_type = nineml.user_layer.ConnectionType("ConnectionType - not used", os.path.join(catalog, "not_used.xml"))
    
    population_excitatory = nineml.user_layer.Population("Excitatory population", N_exc,     neurone_IAF,     nineml.user_layer.PositionList(structure=grid2D))
    population_inhibitory = nineml.user_layer.Population("Inhibitory population", N_inh,     neurone_IAF,     nineml.user_layer.PositionList(structure=grid2D))
    population_poisson    = nineml.user_layer.Population("Poisson population",    N_poisson, neurone_poisson, nineml.user_layer.PositionList(structure=grid2D))

    # Create connection rules (using CSA or lists of explicit connections)
    if useCSA:
        exc_params = {
                       'p'      : (0.020, None),
                       'weight' : (0.004, 'nS'),
                       'delay'  : (0.200, 'ms')
                     }
        inh_params = {
                       'p'      : (0.020, None),
                       'weight' : (0.051, 'nS'),
                       'delay'  : (0.200, 'ms')
                     }
        poi_params = {
                       'p'      : (0.020,  None),
                       'weight' : (0.100, 'nS'),
                       'delay'  : (0.200, 'ms')
                     }
        
        connection_rule_exc_exc     = nineml.user_layer.ConnectionRule("Connections exc_exc",     os.path.join(catalog, "random_fixed_probability_w_d.xml"), exc_params)
        connection_rule_exc_inh     = nineml.user_layer.ConnectionRule("Connections exc_inh",     os.path.join(catalog, "random_fixed_probability_w_d.xml"), exc_params)
        connection_rule_inh_inh     = nineml.user_layer.ConnectionRule("Connections inh_inh",     os.path.join(catalog, "random_fixed_probability_w_d.xml"), inh_params)
        connection_rule_inh_exc     = nineml.user_layer.ConnectionRule("Connections inh_exc",     os.path.join(catalog, "random_fixed_probability_w_d.xml"), inh_params)
        connection_rule_poisson_exc = nineml.user_layer.ConnectionRule("Connections poisson_exc", os.path.join(catalog, "random_fixed_probability_w_d.xml"), poi_params)
        connection_rule_poisson_inh = nineml.user_layer.ConnectionRule("Connections poisson_inh", os.path.join(catalog, "random_fixed_probability_w_d.xml"), poi_params)
    
    else:
        connections_exc_exc     = readCSV_pyNN(os.path.join(connections_folder, 'e2e.conn'))
        connections_exc_inh     = readCSV_pyNN(os.path.join(connections_folder, 'e2i.conn'))
        connections_inh_inh     = readCSV_pyNN(os.path.join(connections_folder, 'i2i.conn'))
        connections_inh_exc     = readCSV_pyNN(os.path.join(connections_folder, 'i2e.conn'))
        connections_poisson_exc = readCSV_pyNN(os.path.join(connections_folder, 'ext2e.conn'))
        connections_poisson_inh = readCSV_pyNN(os.path.join(connections_folder, 'ext2i.conn'))
        
        connection_rule_exc_exc     = nineml.user_layer.ConnectionRule("Explicit Connections exc_exc",     os.path.join(catalog, "explicit_list_of_connections.xml"))
        connection_rule_exc_inh     = nineml.user_layer.ConnectionRule("Explicit Connections exc_inh",     os.path.join(catalog, "explicit_list_of_connections.xml"))
        connection_rule_inh_inh     = nineml.user_layer.ConnectionRule("Explicit Connections inh_inh",     os.path.join(catalog, "explicit_list_of_connections.xml"))
        connection_rule_inh_exc     = nineml.user_layer.ConnectionRule("Explicit Connections inh_exc",     os.path.join(catalog, "explicit_list_of_connections.xml"))
        connection_rule_poisson_exc = nineml.user_layer.ConnectionRule("Explicit Connections poisson_exc", os.path.join(catalog, "explicit_list_of_connections.xml"))
        connection_rule_poisson_inh = nineml.user_layer.ConnectionRule("Explicit Connections poisson_inh", os.path.join(catalog, "explicit_list_of_connections.xml"))
        
        # A temporal workaround until the support for explicit connections is finished
        setattr(connection_rule_exc_exc,     'connections', connections_exc_exc)
        setattr(connection_rule_exc_inh,     'connections', connections_exc_inh)
        setattr(connection_rule_inh_inh,     'connections', connections_inh_inh)
        setattr(connection_rule_inh_exc,     'connections', connections_inh_exc)
        setattr(connection_rule_poisson_exc, 'connections', connections_poisson_exc)
        setattr(connection_rule_poisson_inh, 'connections', connections_poisson_inh)

    # Create projections
    projection_exc_exc     = nineml.user_layer.Projection("Projection exc_exc",     population_excitatory, population_excitatory, connection_rule_exc_exc,     psr_excitatory, connection_type)
    projection_exc_inh     = nineml.user_layer.Projection("Projection exc_inh",     population_excitatory, population_inhibitory, connection_rule_exc_inh,     psr_excitatory, connection_type)
    projection_inh_inh     = nineml.user_layer.Projection("Projection inh_inh",     population_inhibitory, population_inhibitory, connection_rule_inh_inh,     psr_inhibitory, connection_type)
    projection_inh_exc     = nineml.user_layer.Projection("Projection inh_exc",     population_inhibitory, population_excitatory, connection_rule_inh_exc,     psr_inhibitory, connection_type)
    projection_poisson_exc = nineml.user_layer.Projection("Projection poisson_exc", population_poisson,    population_excitatory, connection_rule_poisson_exc, psr_poisson,    connection_type)
    projection_poisson_inh = nineml.user_layer.Projection("Projection poisson_inh", population_poisson,    population_inhibitory, connection_rule_poisson_inh, psr_poisson,    connection_type)

    # Add everything to a single group
    group = nineml.user_layer.Group("Group 1")
    
    # Add populations
    group.add(population_poisson)
    group.add(population_excitatory)
    group.add(population_inhibitory)
    
    # Add projections
    group.add(projection_poisson_exc)
    group.add(projection_poisson_inh)
    group.add(projection_exc_exc)
    group.add(projection_exc_inh)
    group.add(projection_inh_inh)
    group.add(projection_inh_exc)

    # Create a network and add the group to it
    name = 'Brette (2007)'
    ul_model = nineml.user_layer.Model(name)
    ul_model.add_group(group)
    ul_model.write("%s.xml" % name)

    ###############################################################################
    #                            SED-ML experiment
    ###############################################################################
    timeHorizon       = 0.2000 # seconds
    reportingInterval = 0.0001 # seconds
    noPoints          = 1 + int(timeHorizon / reportingInterval)
    
    sedml_simulation = sedmlUniformTimeCourseSimulation('simulation', 'Brette 2007 simulation', 0.0, 0.0, timeHorizon, noPoints, 'KISAO:0000283')
    
    sedml_model      = sedmlModel('model', 'Brette 2007 model', 'urn:sedml:language:nineml', ul_model) 
    
    sedml_task       = sedmlTask('task', 'Brette 2007 task', sedml_model, sedml_simulation)
    
    sedml_variable_time  = sedmlVariable('time', 'Time',    sedml_task, symbol='urn:sedml:symbol:time')
    sedml_variable_excV1 = sedmlVariable('excV1', 'Excitatory neurone[0] voltage, V',  sedml_task, target='Group 1.Excitatory population[0].V')
    sedml_variable_excV2 = sedmlVariable('excV2', 'Excitatory neurone[3] voltage, V',  sedml_task, target='Group 1.Excitatory population[3].V')
    sedml_variable_excV3 = sedmlVariable('excV3', 'Excitatory neurone[12] voltage, V', sedml_task, target='Group 1.Excitatory population[12].V')
    sedml_variable_inhV  = sedmlVariable('inhV',  'Inhibitory neurone[5] voltage, V',  sedml_task, target='Group 1.Inhibitory population[5].V')

    sedml_data_generator_time = sedmlDataGenerator('DG time', 'DG time', [sedml_variable_time])
    sedml_data_generator_excV = sedmlDataGenerator('DG excV', 'DG excV', [sedml_variable_excV1, sedml_variable_excV2, sedml_variable_excV3])
    sedml_data_generator_inhV = sedmlDataGenerator('DG inhV', 'DG inhV', [sedml_variable_inhV])

    curve_excV = sedmlCurve('ExcV', 'ExcV', False, False, sedml_data_generator_time, sedml_data_generator_excV)
    curve_inhV = sedmlCurve('InhV', 'InhV', False, False, sedml_data_generator_time, sedml_data_generator_inhV)

    plot_excV  = sedmlPlot2D('Plot excV', 'Plot excV', [curve_excV])
    plot_inhV  = sedmlPlot2D('Plot inhV', 'Plot inhV', [curve_inhV])

    sedml_experiment = sedmlExperiment([sedml_simulation], 
                                       [sedml_model], 
                                       [sedml_task], 
                                       [sedml_data_generator_time, sedml_data_generator_excV, sedml_data_generator_inhV],
                                       [plot_excV, plot_inhV])
    
    return sedml_experiment

def simulate():
    #gc.enable()
    #gc.set_debug(gc.DEBUG_STATS | gc.DEBUG_COLLECTABLE | gc.DEBUG_UNCOLLECTABLE | gc.DEBUG_INSTANCES | gc.DEBUG_OBJECTS | gc.DEBUG_SAVEALL)
    
    try:
        network_create_time_start = 0
        network_create_time_end = 0
        simulation_initialize_and_solve_initial_time_start = 0
        simulation_initialize_and_solve_initial_time_end = 0
        simulation_run_time_start = 0
        simulation_run_time_end = 0
        simulation_finalize_time_start = 0
        simulation_finalize_time_end = 0

        # 1. Get a SED-ML experiment object 
        sedml_experiment = getULModelAndSimulationInputs()

        # 3. Create daetools point neurone network simulation
        network_create_time_start = time()
        simulation = daetoolsPointNeuroneNetworkSimulation(sedml_experiment)
        network_create_time_end = time()
        
        # 4. Initialize the simulation and apply the parameters values and initial conditions
        simulation_initialize_and_solve_initial_time_start = time()
        simulation.initializeAndSolveInitial()
        simulation_initialize_and_solve_initial_time_end = time()
        
        # 5. Run the simulation
        simulation_run_time_start = time()
        simulation.run()
        simulation_run_time_end = time()
        
        # 5. Finalize the simulation
        simulation_finalize_time_start = time()
        simulation.finalize()
        simulation_finalize_time_end = time()
        
        print('Simulation statistics:          ')
        print('  Network create time:                       {0:>8.3f}s'.format(network_create_time_end - network_create_time_start))
        print('  Simulation initialize/solve initial time:  {0:>8.3f}s'.format(simulation_initialize_and_solve_initial_time_end - simulation_initialize_and_solve_initial_time_start))
        print('  Simulation run time:                       {0:>8.3f}s'.format(simulation_run_time_end - simulation_run_time_start))
        print('  Simulation finalize time:                  {0:>8.3f}s'.format(simulation_finalize_time_end - simulation_finalize_time_start))
        print('  Total run time:                            {0:>8.3f}s'.format(simulation_finalize_time_end - network_create_time_start))
    
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        messages = traceback.format_tb(exc_traceback)
        print(e)
        print('\n'.join(messages))
    
if __name__ == "__main__":
    simulate()
    #profileSimulate()
    
