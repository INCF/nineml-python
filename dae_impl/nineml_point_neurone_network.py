#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
.. module:: nineml_point_neurone_network
   :platform: Unix, Windows
   :synopsis: A useful module indeed.

.. moduleauthor:: Dragan Nikolic <dnikolic@incf.org>

"""

#from __future__ import print_function
import os, sys, urllib, re, traceback, csv, gc
from time import localtime, strftime, time
import numpy, numpy.random

import nineml
import nineml.user_layer
from nineml.abstraction_layer import readers
from nineml.abstraction_layer.testing_utils import TestableComponent

from daetools.pyDAE import *
from nineml_daetools_component import ninemlRNG, createPoissonSpikeTimes, daetools_spike_source, al_component_info, dae_component, dae_component_setup, fixObjectName
from daetools.solvers import pySuperLU

from sedml_support import *
import subprocess

class MemoryMonitor(object):
    """
    Usage:
    memory_mon  = MemoryMonitor('ciroki')
    print 'Memory usage = {0} MB'.format(memory_mon.usage()/1000.0)
    """
    def __init__(self, username):
        """Create new MemoryMonitor instance."""
        self.username = username

    def usage(self):
        """Return int containing memory used by user's processes."""
        self.process = subprocess.Popen("ps -u %s -o rss | awk '{sum+=$1} END {print sum}'" % self.username,
                                        shell=True,
                                        stdout=subprocess.PIPE,
                                        )
        self.stdout_list = self.process.communicate()[0].split('\n')
        return int(self.stdout_list[0])

def fixParametersDictionary(parameters):
    """
    :param parameters: ParameterSet object.
    
    :rtype: A dictionary made of the following key:value pairs: ``{'name' : (value, unit) }``.
    :raises: 
    """
    new_parameters = {}
    for name, parameter in list(parameters.items()):
        new_parameters[name] = (parameter.value, parameter.unit) 
    return new_parameters

class on_spikeout_action(pyCore.daeAction):
    def __init__(self, neurone, eventPort):
        pyCore.daeAction.__init__(self)
        
        self.neurone   = neurone
        self.eventPort = eventPort

    def Execute(self):
        #print('{0} FIRED AT {1}'.format(self.neurone.CanonicalName, time))
        
        # The floating point value of the data sent with the event is a current time 
        time         = float(self.eventPort.EventData)
        delayed_time = 0.0
        for synapse, event_port_index, delay in self.neurone.target_synapses:
            inlet_event_port = synapse.getInletEventPort(event_port_index)
            delayed_time = time + delay
            if delayed_time in self.neurone.event_queue:
                self.neurone.event_queue[delayed_time].append(inlet_event_port)
            else:
                self.neurone.event_queue[delayed_time] = [inlet_event_port]

def create_neurone(name, component_info, rng, parameters):
    """
    Creates 'dae_component' object for a given 'al_component_info' object.
    There are some special cases which are handled individually such as:
     * SpikeSourcePoisson
    
    :param name: string
    :param al_component_info: AL Component object
    :param rng: numpy.random.RandomState object
    :param parameters: python dictionary 'name' : value
    
    :rtype: dae_component object
    :raises: RuntimeError 
    """
    #print('create_neurone: {0}'.format(name))
    
    neurone = None
    if component_info.name == 'SpikeSourcePoisson':
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
        neurone    = daetools_spike_source(spiketimes, name, None, '')
    
    else:
        neurone = dae_component(component_info, fixObjectName(name), None, '')
        neurone.Nitems = 1
        neurone.initialize()
    
    spike_event_port = neurone.getOutletEventPort()
    neurone.on_spike_out_action = on_spikeout_action(neurone, spike_event_port)
    neurone.ON_EVENT(spike_event_port, userDefinedActions = [neurone.on_spike_out_action])
    
    return neurone

def create_al_from_ul_component(ul_component, random_number_generators):
    """
    Creates AL component referenced in the given UL component and does some additional
    processing depending on its type. Returns the AL Component object. 
    It always checks if the url is valid and throws an exception if it ain't.
    
    Achtung!! Check if the component-data are needed at all.
    
    :param ul_component: UL Component object
    :param random_number_generators: python dictionary 'UL Component name' : ninemlRNG object (numpy RandomState based)
    
    :rtype: tuple (AL Component object, list component_data)
    :raises: RuntimeError 
    """
    
    # Getting an exception can occur for two reasons:
    #  1. The component at the specified URL does not exist
    #  2. The component exists but the parser cannot parse it
    try:
        # First check if the component exists; if not - raise an exception.
        f = urllib.urlopen(ul_component.definition.url)
    
    except Exception as e:
        raise RuntimeError('Cannot resolve the component: {0}, definition url: {1}, error: {2}'.format(ul_component.name, ul_component.definition.url, str(e)))
    
    try:
        # Try to load the component
        al_component   = nineml.abstraction_layer.readers.XMLReader.read(ul_component.definition.url) 
        component_info = al_component_info(al_component.name, al_component)
        parameters     = fixParametersDictionary(ul_component.parameters)
    
    except Exception as e:
        raise RuntimeError('The component: {0} failed to parse: {1}'.format(ul_component.name, str(e)))

    # Do the additional processing, depending on the component's type.
    # Should be completed (if needed) in the future.
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
                rng = ninemlRNG.create_rng(al_component, parameters)
                random_number_generators[ul_component.name] = rng
        
        else:
            RuntimeError('Unsupported UL Component type: {0}, component name: {1}'.format(type(ul_component), ul_component.name))
    
    except Exception as e:
        raise RuntimeError('The component: {0} failed to parse: {1}'.format(ul_component.name, str(e)))
    
    return (component_info, al_component, ul_component, parameters)

class explicit_connections_generator_interface:
    """
    The simplest implementation of the ConnectionGenerator interface (Mikael Djurfeldt)
    built on top of the explicit list of connections.
    
    **Achtung, Achtung!** All indexes are zero-index based, for both source and target populations.
    """
    def __init__(self, connections):
        """
        Initializes the list of connections that the simulator can iterate on.
        
        :param connections: a list of tuples: (int, int) or (int, int, weight) or (int, int, weight, delay) or (int, int, weight, delay, parameters)
    
        :rtype:        
        :raises: RuntimeError 
        """
        if not connections or len(connections) == 0:
            raise RuntimeError('The connections argument is either None or an empty list')
        
        n_values = len(connections[0])
        if n_values < 2:
            raise RuntimeError('The number of items in each connection must be at least 2')
        
        for c in connections:
            if len(c) != n_values:
                raise RuntimeError('An invalid number of items in the connection: {0}; it should be {1}'.format(c, n_values))
        
        self._connections = connections
        self._current     = 0
    
    @property
    def size(self):
        """
        :rtype: Integer (the number of the connections).
        :raises: RuntimeError 
        """
        return len(self._connections)
        
    @property
    def arity(self):
        """
        Returns the number of values stored in an individual connection. It can be zero.
        The first two are always weight and delay; the rest are connection specific parameters.
        
        :rtype: Integer
        :raises: IndexError
        """
        return len(self._connections[0]) - 2
    
    def __iter__(self):
        """
        Initializes and returns the iterator.
        
        :rtype: explicit_connections_generator_interface object (self)
        :raises: 
        """
        self.start()
        return self
    
    def start(self):
        """
        Initializes the iterator.
        
        :rtype:
        :raises: 
        """
        self._current = 0
    
    def next(self):
        """
        Returns the connection and moves the counter to the next one.
        The connection is a tuple: (source_index, target_index, [zero or more floating point values])
        
        :rtype: tuple
        :raises: StopIteration (as required by the python iterator concept)
        """
        if self._current >= len(self._connections):
            raise StopIteration
        
        connection = self._connections[self._current]
        self._current += 1
        
        return connection

class daetools_point_neurone_network:
    """
    A top-level daetools model. All other models will be added to it (neurones, synapses):
     * Neurone names will be: model_name.population_name_Neurone(xxx)
     * Synapse names will be: model_name.projection_name_Synapsexxx(source_index,target_index)
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
        self._global_rng      = numpy.random.RandomState()
        
        for name, ul_component in list(ul_model.components.items()):
            self._components[name] = create_al_from_ul_component(ul_component, self._rngs)
        
        for name, ul_group in list(ul_model.groups.items()):
            self._groups[name] = daetools_group(name, ul_group, self)
        
    def __repr__(self):
        res = 'daetools_point_neurone_network({0})\n'.format(self._name)
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
        :rtype: daetools_group object
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
        return self._global_rng

class daetools_group:
    """
    """
    def __init__(self, name, ul_group, network):
        """
        :param name: string
        :param ul_group: UL Group object
        :param network: daetools_point_neurone_network object
        
        :rtype:
        :raises: RuntimeError
        """
        self._name        = fixObjectName(name)
        self._populations = {}
        self._projections = {}
        
        for name, ul_population in list(ul_group.populations.items()):
            self._populations[name] = daetools_population(name, ul_population, network, len(self._populations))
        
        for name, ul_projection in list(ul_group.projections.items()):
            self._projections[name] = daetools_projection(name, ul_projection, self, network)
    
    def __repr__(self):
        res = 'daetools_group({0})\n'.format(self._name)
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
        :rtype: daetools_population object
        :raises: RuntimeError
        """
        if not name in self._populations:
            raise RuntimeError('Population [{0}] does not exist in the group'.format(name)) 
        return self._populations[name]
        
    def getProjection(self, name):
        """
        :param name: string
        :rtype: daetools_projection object
        :raises: RuntimeError
        """
        if not name in self._projections:
            raise RuntimeError('Projection [{0}] does not exist in the group'.format(name)) 
        return self._projections[name]

class daetools_population:
    """
    """
    def __init__(self, name, ul_population, network, population_id):
        """
        :param name: string
        :param ul_population: UL Population object
        :param network: daetools_point_neurone_network object
        
        :rtype: 
        :raises: RuntimeError
        """
        self._name           = fixObjectName(name)
        self._population_id  = population_id
        self._parameters     = network.getComponentParameters(ul_population.prototype.name)
        
        _component_info  = network.getComponentInfo(ul_population.prototype.name) 
        
        self.neurones = [
                           create_neurone(
                                           'p{0}({1:0>4})'.format(self._population_id, i),  # Name
                                           _component_info,                                 # al_component_info object
                                           network.globalRandomNumberGenerator,             # RNG 
                                           self._parameters                                 # dict with init. parameters
                                         ) for i in xrange(0, ul_population.number)
                         ]
        
        #try:
        #    self._positions = ul_population.positions.get_positions(ul_population)
        #except Exception as e:
        #    print(str(e))
        
    def getNeurone(self, index):
        """
        :param name: integer
        :rtype: None
        :raises: IndexError
        """
        return self.neurones[int(index)]
    
    def __repr__(self):
        res = 'daetools_population({0})\n'.format(self._name)
        res += '  neurones:\n'
        for o in self.neurones:
            res += '  {0}\n'.format(repr(o))
        return res

class daetools_projection:
    """
    Data members:    
     * name : string
    """
    def __init__(self, name, ul_projection, group, network):
        """
        :param name: string
        :param ul_projection: UL Projection object
        :param group: daetools_group object
        :param network: daetools_point_neurone_network object
        
        :rtype:
        :raises: RuntimeError
        """
        self.name = fixObjectName(name)
        
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
                          dae_component(
                                         psr_component_info, 
                                         's(p{0},p{1})'.format(source_population._population_id, target_population._population_id),
                                         target_population.getNeurone(i), 
                                         ''
                                       ) for i in xrange(0, ul_projection.target.number)
                         ]               
        
        for i, neurone in enumerate(target_population.neurones):
            neurone.incoming_synapses.append( (self._synapses[i], psr_parameters) ) 
        
        ul_connection_rule = network.getULComponent(ul_projection.rule.name)
        if hasattr(ul_connection_rule, 'connections'): # Explicit connections
            connections = getattr(ul_connection_rule, 'connections') 
            cgi = explicit_connections_generator_interface(connections)
            self._createConnections(cgi, source_population, target_population)
        
        else: # It should be the CSA component then
            self._handleConnectionRuleComponent(_connection_rule)

            
            neurones    = []
            connections = []
            dot_graph_template = '''
            digraph finite_state_machine {{
                rankdir=LR;
                node [shape=ellipse]; {0};
                {1}
            }}
            '''
            if len(regimes_list) > 1:
                dot_graph = dot_graph_template.format(' '.join(regimes_list), '\n'.join(transitions_list))
                graph     = dot2tex.dot2tex(dot_graph, autosize=True, texmode='math', format='tikz', crop=True, figonly=True)

        # Now we are done with connections. Initialize synapses
        for i, neurone in enumerate(target_population.neurones):
            synapse = self._synapses[i]
            synapse.initialize()
            neurone.connectAnaloguePorts(synapse, neurone)

    def __repr__(self):
        res = 'daetools_projection({0})\n'.format(self.name)
        #res += '  source_population:\n'
        #res += '    {0}\n'.format(self._source_population)
        #res += '  target_population:\n'
        #res += '    {0}\n'.format(self._target_population)
        #res += '  psr:\n'
        #res += '    {0}\n'.format(self._psr)
        #res += '  connection_rule:\n'
        #res += '    {0}\n'.format(self._connection_rule)
        #res += '  connection_type:\n'
        #res += '    {0}\n'.format(self._connection_type)
        return res

    def getSynapse(self, index):
        """
        :param name: integer
        :rtype: None
        :raises: IndexError
        """
        return self._synapses[index]

    def _handleConnectionRuleComponent(self, al_connection_rule):
        """
        :param al_connection_rule: AL Component object (CSA or other)
        
        :rtype: None
        :raises: RuntimeError
        """
        raise RuntimeError('Support for connection rule component not implemented yet')

    def _createConnections(self, cgi, source_population, target_population):
        """
        Iterates over ConnectionGeneratorInterface object and creates connections.
        Based on the connections, connects source->target neurones and (optionally) sets weights and delays
        
        :param cgi: ConnectionGeneratorInterface object
        
        :rtype: None
        :raises: RuntimeError
        """
        #import pygraphviz
        #graph = pygraphviz.AGraph(strict=False,directed=True)
        #graph.node_attr['shape']='circle'
        
        #for i, neurone in enumerate(target_population.neurones):
        #    graph.add_node(neurone.Name)
        #for i, neurone in enumerate(source_population.neurones):
        #    graph.add_node(neurone.Name)
        
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
                weight = float(connection[2])
            elif cgi.arity == 2:
                weight = float(connection[2])
                delay  = float(connection[3])
            elif cgi.arity >= 3:
                weight = float(connection[2])
                delay  = float(connection[3])
                for i in range(4, size):
                    parameters.append(float(connection[i]))           
            
            source_neurone = source_population.getNeurone(source_index)
            target_neurone = target_population.getNeurone(target_index)
            synapse        = self.getSynapse(target_index)
            
            #graph.add_edge(source_neurone.Name, target_neurone.Name)
            
            # Add a new item to the list of connected synapse event ports and connection delays.
            # Here we cannot add an event port directly since it does not exist yet.
            # Hence, we add the synapse object and the index of the event port.
            source_neurone.target_synapses.append( (synapse, synapse.Nitems, delay) )
            synapse.Nitems += 1
            
            # Increase the number of connections in the synapse
            # ACHTUNG!! Here we should set the weight somehow but that is undefined at the moment
        
        #graph.layout()
        #graph.write('{0}.dot'.format(self.name))
        #graph.draw('{0}.png'.format(self.name))

class point_neurone_simulation(pyActivity.daeSimulation):
    """
    """
    #count = 0
    def __init__(self, neurone, neurone_parameters, neurone_report_variables):
        """
        :rtype: None
        :raises: RuntimeError
        """
        pyActivity.daeSimulation.__init__(self)
        
        self.m                        = neurone
        self.neurone_parameters       = neurone_parameters
        self.neurone_report_variables = neurone_report_variables
        
        self.daesolver    = pyIDAS.daeIDAS()
        self.lasolver     = pySuperLU.daeCreateSuperLUSolver()
        self.daesolver.SetLASolver(self.lasolver)

    def init(self, log, datareporter, reportingInterval, timeHorizon):
        self.ReportingInterval = reportingInterval
        self.TimeHorizon       = timeHorizon
        
        self.Initialize(self.daesolver, datareporter, log)
        
        #if point_neurone_simulation.count == 0:
        #    self.m.SaveModelReport(self.m.Name + "__.xml")
        #point_neurone_simulation.count += 1
        
    def SetUpParametersAndDomains(self):
        """
        :rtype: None
        :raises: RuntimeError
        """
        dae_component_setup.SetUpParametersAndDomains(self.m, self.neurone_parameters)
        for (synapse, synapse_parameters) in self.m.incoming_synapses:
            dae_component_setup.SetUpParametersAndDomains(synapse, synapse_parameters)
        
    def SetUpVariables(self):
        """
        :rtype: None
        :raises: RuntimeError
        """
        dae_component_setup.SetUpVariables(self.m, self.neurone_parameters, self.neurone_report_variables)
        for (synapse, synapse_parameters) in self.m.incoming_synapses:
            dae_component_setup.SetUpVariables(synapse, synapse_parameters, {})

    def CleanUpSetupData(self):
        pyActivity.daeSimulation.CleanUpSetupData(self)
        self.m.CleanUpSetupData()
        
class point_neurone_network_simulation:
    """
    """
    def __init__(self, network, reportingInterval, timeHorizon, report_variables, plots_to_create):
        """
        :rtype: None
        :raises: RuntimeError
        """
        self.network             = network
        self.reportingInterval   = reportingInterval
        self.timeHorizon         = timeHorizon        
        self.log                 = daeLogs.daePythonStdOutLog()
        self.datareporter        = pyDataReporting.daeTCPIPDataReporter()
        self.simulations         = {}
        self.event_queue         = {}
        self.number_of_vars      = 0
        self.number_of_neurones  = 0
        self.average_firing_rate = {}

        simName = 'Brette' + strftime(" [%d.%m.%Y %H:%M:%S]", localtime())
        if(self.datareporter.Connect("", simName) == False):
            raise RuntimeError('Cannot connect the data reporter')
        
        dae_component_setup._random_number_generators = network.randomNumberGenerators

        try:
            self.log.Enabled = False
            
            self.event_port = None
            # Setup neurones in populations
            for group_name, group in network._groups.iteritems():
                for population_name, population in group._populations.iteritems():
                    print("Creating the population: {0}...".format(population_name))
                    for neurone in population.neurones:
                        simulation = point_neurone_simulation(neurone, population._parameters, {})
                        neurone.event_queue = self.event_queue
                        self.simulations[neurone.Name] = simulation
                        
                        self.number_of_neurones += 1
                        if not self.event_port:
                            self.event_port = neurone.getOutletEventPort()
        
        except:
            raise
        
        finally:
            self.log.Enabled = True

    def InitializeAndSolveInitial(self):
        try:
            self.log.Enabled = False
            
            count = 0
            self.number_of_vars = 0
            for target_neuron_name, simulation in self.simulations.iteritems():
                simulation.init(self.log, self.datareporter, self.reportingInterval, self.timeHorizon)
                self.number_of_vars += simulation.daesolver.NumberOfVariables
                
                simulation.SolveInitial()
                simulation.CleanUpSetupData()
                
                count += 1
                print 'Setting up the neurone {0} out of {1} (total number of variables: {2})...'.format(count, self.number_of_neurones, self.number_of_vars), "\r",
                sys.stdout.flush()
        
        except:
            raise
        
        finally:
            print '\n   Done\n'
            self.log.Enabled = True
        
        #print('garbage before collect:\n'.format(gc.garbage))
        collected = gc.collect()
        #print "Garbage collector: collected %d objects." % (collected)  
        #print('garbage after collect:\n'.format(gc.garbage))
    
    def Run(self):
        times = numpy.arange(self.reportingInterval, self.timeHorizon, self.reportingInterval)
        for t in times:
            self.event_queue[float(t)] = []

        prev_time = 0.0
        (next_time, send_events_to) = sorted(self.event_queue.iteritems())[0]
        del self.event_queue[next_time] 
        while next_time <= self.timeHorizon:
            #print(sorted(self.event_queue.iteritems()))
            #print('next_time = {0}\nsend_events_to = {1}\n'.format(next_time, send_events_to))
            
            print("Integrating from {0} to {1}...".format(prev_time, next_time))
            for target_neuron_name, simulation in self.simulations.iteritems():
                simulation.IntegrateUntilTime(next_time, pyActivity.eDoNotStopAtDiscontinuity, False)
                #simulation.ReportData(next_time)
                simulation.Log.SetProgress(int(100.0 * simulation.CurrentTime/simulation.TimeHorizon))
            
            for port in send_events_to:
                port.ReceiveEvent(next_time)
                
            # Take the next time and ports where events should be sent and remove them from the 'event_queue' dictionary
            if len(self.event_queue) == 0:
                break
            
            prev_time      = next_time
            next_time      = min(self.event_queue.keys())
            send_events_to = self.event_queue[next_time]
            del self.event_queue[next_time] 
            
        print('Neurone [{0}] spike events: {1}'.format(self.event_port.CanonicalName, self.event_port.Events))
        
        for group_name, group in self.network._groups.iteritems():
            for population_name, population in group._populations.iteritems():
                count = 0
                for neurone in population.neurones:
                    event_port = neurone.getOutletEventPort()
                    count += len(event_port.Events)
                
                self.average_firing_rate[population_name] = count / (self.timeHorizon * len(population.neurones))
                print('Population [{0}] average firing rate: {1}'.format(population_name, self.average_firing_rate[population_name]))
        
    def Finalize(self):
        # Finalize
        for target_neuron_name, simulation in self.simulations.iteritems():
            simulation.Finalize()
        
def readCSV_pyNN(filename):
    """
    Reads pyNN .conn files and returns a list of connections: [(int, int, float, float), ...]
    """
    connections_out = []
    connections = csv.reader(open(filename, 'rb'), delimiter='\t')
    for connection in connections:
        s = int(float(connection[0]))
        t = int(float(connection[1]))
        w = float(connection[2]) * 1E-6 # nS -> S
        d = float(connection[3]) * 1E-3 # ms -> s
        connections_out.append((s, t, w, d))
        
    print filename, len(connections_out)
    return connections_out

def unique(connections):
    info = {}
    for (s, t, w, d) in connections:
        if t in info:
            info[t] += 1
        else:
            info[t] = 1
    unique_set = set(info.values())
    print(unique_set)
        
def profile_simulate():
    import hotshot
    from hotshot import stats
    #prof = hotshot.Profile("nineml_point_neurone_network.profile")
    #prof.runcall(simulate)
    #prof.close()
    
    s = stats.load("nineml_point_neurone_network.profile")
    s.strip_dirs().sort_stats("time").print_stats()

def get_ul_model_and_simulation_inputs():
    ###############################################################################
    #                           NineML UserLayer Model
    ###############################################################################
    catalog = "file:///home/ciroki/Data/NineML/experimental/lib9ml/python/dae_impl/"

    rnd_uniform = {
                    'lowerBound': (-0.060, "dimensionless"),
                    'upperBound': (-0.040, "dimensionless")
                }
    uni_distr = nineml.user_layer.RandomDistribution("uniform(-0.060, -0.040)", catalog + "uniform_distribution.xml", rnd_uniform)
    
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
                        'vrev' : (   0.000, 'V'),
                        'q'    : (100.0E-9, 'S'),
                        'tau'  : (   0.005, 's'),
                        'g'    : (   0.000, 'S')
                        }

    psr_excitatory_params = {
                            'vrev' : (  0.000, 'V'),
                            'q'    : ( 4.0E-9, 'S'),
                            'tau'  : (  0.005, 's'),
                            'g'    : (  0.000, 'S')
                            }
                    
    psr_inhibitory_params = {
                            'vrev' : ( -0.080, 'V'),
                            'q'    : (51.0E-9, 'S'),
                            'tau'  : (  0.010, 's'),
                            'g'    : (  0.000, 'S')
                            }
    
    neurone_IAF     = nineml.user_layer.SpikingNodeType("IAF neurones", catalog + "iaf.xml", neurone_params)
    
    neurone_poisson = nineml.user_layer.SpikingNodeType("Poisson Source", catalog + "spike_source_poisson.xml", poisson_params)
    
    psr_poisson     = nineml.user_layer.SynapseType("COBA poisson",    catalog + "coba_synapse.xml", psr_poisson_params)
    psr_excitatory  = nineml.user_layer.SynapseType("COBA excitatory", catalog + "coba_synapse.xml", psr_excitatory_params)
    psr_inhibitory  = nineml.user_layer.SynapseType("COBA inhibitory", catalog + "coba_synapse.xml", psr_inhibitory_params)
    
    grid2D          = nineml.user_layer.Structure("2D grid", catalog + "2Dgrid.xml")
    connection_type = nineml.user_layer.ConnectionType("Static weights and delays", catalog + "static_weights_delays.xml")
    
    population_excitatory = nineml.user_layer.Population("Excitatory population", 800, neurone_IAF,     nineml.user_layer.PositionList(structure=grid2D))
    population_inhibitory = nineml.user_layer.Population("Inhibitory population", 200, neurone_IAF,     nineml.user_layer.PositionList(structure=grid2D))
    population_poisson    = nineml.user_layer.Population("Poisson population",     20, neurone_poisson, nineml.user_layer.PositionList(structure=grid2D))

    connections_folder      = '1000/'
    connections_exc_exc     = readCSV_pyNN(connections_folder + 'e2e.conn')
    connections_exc_inh     = readCSV_pyNN(connections_folder + 'e2i.conn')
    connections_inh_inh     = readCSV_pyNN(connections_folder + 'i2i.conn')
    connections_inh_exc     = readCSV_pyNN(connections_folder + 'i2e.conn')
    connections_poisson_exc = readCSV_pyNN(connections_folder + 'ext2e.conn')
    connections_poisson_inh = readCSV_pyNN(connections_folder + 'ext2i.conn')
    
    connection_rule_exc_exc     = nineml.user_layer.ConnectionRule("Explicit Connections exc_exc", catalog + "explicit_list_of_connections.xml")
    connection_rule_exc_inh     = nineml.user_layer.ConnectionRule("Explicit Connections exc_inh", catalog + "explicit_list_of_connections.xml")
    connection_rule_inh_inh     = nineml.user_layer.ConnectionRule("Explicit Connections inh_inh", catalog + "explicit_list_of_connections.xml")
    connection_rule_inh_exc     = nineml.user_layer.ConnectionRule("Explicit Connections inh_exc", catalog + "explicit_list_of_connections.xml")
    connection_rule_poisson_exc = nineml.user_layer.ConnectionRule("Explicit Connections poisson_exc", catalog + "explicit_list_of_connections.xml")
    connection_rule_poisson_inh = nineml.user_layer.ConnectionRule("Explicit Connections poisson_inh", catalog + "explicit_list_of_connections.xml")

    setattr(connection_rule_exc_exc,     'connections', connections_exc_exc)
    setattr(connection_rule_exc_inh,     'connections', connections_exc_inh)
    setattr(connection_rule_inh_inh,     'connections', connections_inh_inh)
    setattr(connection_rule_inh_exc,     'connections', connections_inh_exc)
    setattr(connection_rule_poisson_exc, 'connections', connections_poisson_exc)
    setattr(connection_rule_poisson_inh, 'connections', connections_poisson_inh)

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
    ul_model = nineml.user_layer.Model("Simple 9ML example model")
    ul_model.add_group(group)
    ul_model.write("Brette et al., J. Computational Neuroscience (2007).xml")

    ###############################################################################
    #                            SED-ML experiment
    ###############################################################################
    timeHorizon       = 0.0600
    reportingInterval = 0.0001
    noPoints          = 1 + int(timeHorizon / reportingInterval)
    
    sedml_simulation = sedmlUniformTimeCourseSimulation('Brette simulation', 'Brette 2007 simulation', 0.0, 0.0, timeHorizon, noPoints, 'KISAO:0000283')
    
    sedml_model      = sedmlModel('Brette model', 'Brette model', 'urn:sedml:language:nineml', ul_model) 
    
    sedml_task       = sedmlTask('task1', 'task1', sedml_model, sedml_simulation)
    
    sedml_variable_time  = sedmlVariable('time', 'time',    sedml_task, symbol='urn:sedml:symbol:time')
    sedml_variable_excV  = sedmlVariable('excV', 'Voltage', sedml_task, target='Group 1/Excitatory population/V[0]')
    sedml_variable_inhV  = sedmlVariable('inhV', 'Voltage', sedml_task, target='Group 1/Inhibitory population/V[0]')

    sedml_data_generator_time = sedmlDataGenerator('DG time', 'DG time', [sedml_variable_time])
    sedml_data_generator_excV = sedmlDataGenerator('DG excV', 'DG excV', [sedml_variable_excV])
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
    
    return sedml_experiment.get_daetools_simulation_inputs()

def simulate():
    #gc.enable()
    #gc.set_debug(gc.DEBUG_STATS | gc.DEBUG_COLLECTABLE | gc.DEBUG_UNCOLLECTABLE | gc.DEBUG_INSTANCES | gc.DEBUG_OBJECTS | gc.DEBUG_SAVEALL)
    
    try:
        network_create_time_start = 0
        network_create_time_end = 0
        simulation_create_time_start = 0
        simulation_create_time_end = 0
        simulation_initialize_and_solve_initial_time_start = 0
        simulation_initialize_and_solve_initial_time_end = 0
        simulation_run_time_start = 0
        simulation_run_time_end = 0
        simulation_finalize_time_start = 0
        simulation_finalize_time_end = 0

        # 1. Get UL Model and simulation inputs from SED-ML file 
        ul_model, timeHorizon, reportingInterval, variables_to_report, plots_to_generate = get_ul_model_and_simulation_inputs()
        #print ul_model, timeHorizon, reportingInterval, variables_to_report, plots_to_generate

        # 2. Create daetools point neurone network
        network_create_time_start = time()
        network = daetools_point_neurone_network(ul_model)
        network_create_time_end = time()
        
        # 3. Create daetools point neurone network simulation
        simulation_create_time_start = time()
        simulation = point_neurone_network_simulation(network, reportingInterval, timeHorizon, variables_to_report, plots_to_generate)
        del ul_model
        simulation_create_time_end = time()
        
        # 4. Initialize the simulation and apply the parameters values and initial conditions
        simulation_initialize_and_solve_initial_time_start = time()
        simulation.InitializeAndSolveInitial()
        simulation_initialize_and_solve_initial_time_end = time()
        
        # 5. Run the simulation
        simulation_run_time_start = time()
        simulation.Run()
        simulation_run_time_end = time()
        
        # 5. Finalize the simulation
        simulation_finalize_time_start = time()
        simulation.Finalize()
        simulation_finalize_time_end = time()
    
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        messages = traceback.format_tb(exc_traceback)
        print('\n'.join(messages))
        print(e)
    
    print('Simulation statistics:          ')
    print('  Network create time:                       {0:>8.3f}s'.format(network_create_time_end - network_create_time_start))
    print('  Simulation create time:                    {0:>8.3f}s'.format(simulation_create_time_end - simulation_create_time_start))
    print('  Simulation initialize/solve initial time:  {0:>8.3f}s'.format(simulation_initialize_and_solve_initial_time_end - simulation_initialize_and_solve_initial_time_start))
    print('  Simulation run time:                       {0:>8.3f}s'.format(simulation_run_time_end - simulation_run_time_start))
    print('  Simulation finalize time:                  {0:>8.3f}s'.format(simulation_finalize_time_end - simulation_finalize_time_start))
    print('  Total run time:                            {0:>8.3f}s'.format(simulation_finalize_time_end - network_create_time_start))
   
if __name__ == "__main__":
    simulate()
    #profile_simulate()
    