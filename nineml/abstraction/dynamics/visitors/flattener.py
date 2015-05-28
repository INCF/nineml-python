"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

import itertools
from collections import defaultdict
from nineml.utils import flatten_first_level
from .cloner import (
    DynamicsCloner, DynamicsClonerPrefixNamespace,
    DynamicsExpandPortDefinition)
from nineml.abstraction.componentclass.namespace import NamespaceAddress
from nineml.exceptions import NineMLRuntimeError
from nineml.abstraction.dynamics.regimes import Regime
from ..transitions import OnCondition, OnEvent
from operator import add, mul
import sympy

reduce_ops = {'+': add, '*': mul}


class TransitionResolver(object):

    RecurseEventTransitions = True

    def __init__(self, oldtransition, regime_tuple,
                 transition_regime_tuple_index, flattener):

        # Store where we are starting and going to:
        self.src_regime_tuple = tuple(regime_tuple)
        self.dst_regime_tuple = tuple(regime_tuple)

        # Clone the old Node
        oldtransition = DynamicsCloner().visit(oldtransition)

        # Store a pointer to the flattener:
        self.flattener = flattener

        # Store the StateAssignments and OutputEvents for this
        # newly mapped transitions
        self.state_assignments = []
        self.output_events = []

        # Construct a map of { send ports -> [recv ports] }.
        # This makes it easy to iterate over send events:
        portconnections = [
            model.portconnections for model in flattener.all_components]
        portconnections = list(itertools.chain(* portconnections))
        self.send_rev_map = {}
        for src, dst in portconnections:
            if not src.get_local_name() in self.send_rev_map:
                self.send_rev_map[src.get_local_name()] = []
            self.send_rev_map[src.get_local_name()].append(
                dst.get_local_name())

        # Variables used in recursion:
        self.unresolved_transitions = [
            (oldtransition, transition_regime_tuple_index)]
        self.changed_regime_indices = set()

        # Recursively solve the transitions:
        self.resolve_transitions()

        # Find the new target regime:
        self.target_regime = flattener.old_regime_tuple_to_new_regime_map[
            tuple(self.dst_regime_tuple)]

    def resolve_transitions(self):
        while self.unresolved_transitions:
            transition, regime_index = self.unresolved_transitions.pop()

            if regime_index in self.changed_regime_indices:
                raise NineMLRuntimeError(
                    'Something has gone wrong with event resolution. '
                    'Changing Regime Twice!')
            self.changed_regime_indices.add(regime_index)

            self.resolve_transition(transition, regime_index)

    def resolve_transition(self, transition, transition_regime_tuple_index):
        # Update the target regime:
        self.dst_regime_tuple = self.get_new_regime_tuple_from_transition(
            current_regime_tuple=self.dst_regime_tuple,
            regime_index=transition_regime_tuple_index,
            oldtransition=transition)

        for ev_out in transition.output_events:
            self.output_events.append(DynamicsCloner().visit(ev_out))
        for state_ass in transition.state_assignments:
            self.state_assignments.append(DynamicsCloner().visit(state_ass))

        # Are we recursing? Or will the simulation engine take care
        # off this for us??
        if not TransitionResolver.RecurseEventTransitions:
            return

        # Are any of the output events connected to other event_ports?
        # print self.send_rev_map.keys()
        for ev_out in transition.output_events:
            # print ' -- Checking for port connections from:', ev_out
            if ev_out.port_name not in self.send_rev_map:
                continue

            for recv_port in self.send_rev_map[ev_out.port_name]:
                # print '    -> Connection to ', recv_port

                # So this port is connected, but are we in a regime that
                # triggers from this port??
                for cascade_regime_index, regime in enumerate(
                        self.dst_regime_tuple):
                    for cascade_ev in regime.on_events:
                        if cascade_ev.src_port_name == recv_port:
                            # print '     (**Cascade found**)'
                            self.unresolved_transitions.append(
                                (cascade_ev, cascade_regime_index))

    def get_new_regime_tuple_from_transition(self, current_regime_tuple,
                                             regime_index, oldtransition):

        # Make a list from the old tuple, so its mutable:
        dst_regime_tuple = list(current_regime_tuple)

        name = oldtransition._target_regime
        dst_regime_old = self.flattener.componentswithregimes[
            regime_index].query.regime(name=name)
        dst_regime_tuple[regime_index] = dst_regime_old

        # Return the tuple:
        return tuple(dst_regime_tuple)


class ComponentFlattener(object):

    # Utility Functions:
    # ------------------ #

    @classmethod
    def flatten_namespace(cls, ns_str):
        return ns_str.replace('.', '_')

    @classmethod
    def flatten_namespace_dict(cls, ns_dict):
        new_dict = {}
        for k, v in ns_dict.iteritems():
            new_dict[cls.flatten_namespace(k)] = v
        return new_dict

    # Useful function possibly called later #
    # ------------------------------------- #
    def get_new_regime(self, old_regime_string):
        """
        for example:
        old_regime_string = ('iaf:subthresholdregime '
                             'cobaInhib:cobadefaultregime '
                             'cobaExcit:cobadefaultregime')
        """

        # Lets create a dictionary that maps 'NamespaceAddress' to regime name
        # from the input string:
        # old_regime_string = 'iaf:subthresholdregime'
        #                     'cobaInhib:cobadefaultregime'
        #                     'cobaExcit:cobadefaultregime'
        nsstr_regimename = [l.split(':') for l in old_regime_string.split()]
        ns_regimename = dict([(NamespaceAddress(ns), regime_name)
                              for (ns, regime_name) in nsstr_regimename])

        # OK, now lets go through our old componentswithregimes,
        # and find the regime that was specified.
        target_regime_tuple = []
        for c in self.componentswithregimes:
            comp_ns = c.get_node_addr()
            if comp_ns not in ns_regimename:
                err = ('Looking for a regime in namespace: {}, but not found.'
                       .format(comp_ns))
                err += ('\nNamespaces: {}'
                        .format(','.join([str(ns)
                                          for ns in ns_regimename.keys()])))
                err += '\nSpecified String: {}'.format(old_regime_string)
                raise NineMLRuntimeError(err)
            target_regime_name = ns_regimename[comp_ns]

            regime_map = dict([(r.name, r) for r in c.regimes])
            if target_regime_name not in regime_map:
                err = 'Namespace has no regime named: %s'
                err += '\nRegimes: %s' % (str(regime_map.keys()))
                raise NineMLRuntimeError(err)

            target_regime_tuple.append(regime_map[target_regime_name])

        target_regime_tuple = tuple(target_regime_tuple)

        new_regime = self.old_regime_tuple_to_new_regime_map[
            target_regime_tuple]
        return new_regime

    # Flattening Functions:
    # --------------------- #
    def __init__(self, component_class, componentname=None):
        assert isinstance(component_class, Dynamics)

        # Is our component_class already flat??
        if component_class.is_flat():
            self.reducedcomponent = DynamicsCloner().visit(component_class)
            if component_class.was_flattened():
                self.reducedcomponent.set_flattener(component_class.flattener)
            return

        # New components name
        self.componentname = componentname if componentname else component_class.name

        # Make a clone of the component_class; in which all hierachical components
        # have their internal symbols prefixed:
        cloned_comp = DynamicsClonerPrefixNamespace().visit(component_class)

        # Make a list of all components, and those components with regimes:
        self.all_components = list(cloned_comp.query.recurse_all_components)
        self.componentswithregimes = [
            m for m in self.all_components if list(m.regimes)]

        # This will get filled in build_new_regime_space(): (It maps {
        # (Regime,Regime,...,Regime) : Regime, (Regime,Regime,...,Regime) :
        # Regime,} Where the key tuple represents the regimes in the
        # hierachical component_class, corresponding to self.componentswithregimes.
        # And the values are the regimes in the new component_class.
        self.old_regime_tuple_to_new_regime_map = None

        # OK, Heavy-lifting Code:
        # ===================== #
        self.build_new_regime_space()

        # Build Our New Component
        self.reducedcomponent = Dynamics(
            name=self.componentname,
            aliases=flatten_first_level(
                [m.aliases for m in self.all_components]),
            state_variables=flatten_first_level(
                [m.state_variables for m in self.all_components]),
            constants=flatten_first_level(
                [c.constants for c in self.all_components]),
            regimes=self.old_regime_tuple_to_new_regime_map.values(),
            analog_ports=flatten_first_level(
                [comp.analog_ports for comp in self.all_components]),
            event_ports=flatten_first_level(
                [comp.event_ports for comp in self.all_components]),
            parameters=flatten_first_level([m.parameters
                                            for m in self.all_components]))

        self.remap_analog_ports()

        # Attach this flattening information to the component_class:
        self.reducedcomponent.set_flattener(self)

    @classmethod
    def create_compound_regime(cls, regimetuple, name):

        # Copy accross all the odes from each regime.
        # We don't worry about transitions yet, we deal with them later.

        # We need to clone the time_derivatives:
        time_derivs = flatten_first_level(
            [r.time_derivatives for r in regimetuple])
        time_derivs = [DynamicsCloner().visit(td) for td in time_derivs]

        return Regime(name=name, time_derivatives=time_derivs)

    def build_new_regime_space(self):

        # Build the new Regime Space, by taking the cross-product of
        # the old regimes. We create a map linking the old regimes tuples
        # to the new Regime.
        # At this point, there are no transitions:
        self.old_regime_tuple_to_new_regime_map = {}
        regimes = [comp.regimes for comp in self.componentswithregimes]
        for regimetuple in itertools.product(*regimes):
            name = '_and_'.join(r.name for r in regimetuple)
            new_regime = ComponentFlattener.create_compound_regime(regimetuple,
                                                                   name)
            self.old_regime_tuple_to_new_regime_map[regimetuple] = new_regime

        # Create New Events for the Regime-Map
        for regimetuple, regime_new in (self.old_regime_tuple_to_new_regime_map
                                        .iteritems()):
            for regime_index, regime in enumerate(regimetuple):

                for oldtransition in regime.on_conditions:

                    tr = TransitionResolver(
                        oldtransition=oldtransition,
                        regime_tuple=regimetuple,
                        transition_regime_tuple_index=regime_index,
                        flattener=self,
                    )
                    new_oncondition = OnCondition(
                        oldtransition.trigger,
                        state_assignments=tr.state_assignments,
                        output_events=tr.output_events,
                        target_regime=tr.target_regime.name)

                    regime_new.add(new_oncondition)

                for oldtransition in regime.on_events:
                    tr = TransitionResolver(
                        oldtransition=oldtransition,
                        regime_tuple=regimetuple,
                        transition_regime_tuple_index=regime_index,
                        flattener=self,
                    )
                    new_onevent = OnEvent(
                        oldtransition.src_port_name,
                        state_assignments=tr.state_assignments,
                        output_events=tr.output_events,
                        target_regime=tr.target_regime.name)
                    regime_new.add(new_onevent)

    def remap_analog_ports(self):
        new_analog_ports = flatten_first_level(
            [comp.analog_ports for comp in self.all_components])
        new_analog_ports = dict([(p.name, p) for p in new_analog_ports])

        # Handle port mappings:
        # portconnections = [ (NS -> NS), (NS -> NS ), (NS -> NS) ]
        portconnections = [
            model.portconnections for model in self.all_components]
        portconnections = list(itertools.chain(* portconnections))

        # ONLY ANALOG PORTS
        portconnections = [pc for pc in portconnections if pc[
            0].get_local_name() in new_analog_ports]

        # A. Handle Receive Ports:
        for src_addr, dst_addr in portconnections[:]:

            srcport = new_analog_ports[src_addr.get_local_name()]
            dstport = new_analog_ports[dst_addr.get_local_name()]
            if dstport.mode == 'recv':

                DynamicsExpandPortDefinition(
                    originalname=dstport.name, targetname=srcport.name).visit(
                        self.reducedcomponent)

                del new_analog_ports[dst_addr.get_local_name()]
                del self.reducedcomponent._analog_receive_ports[
                    dst_addr.get_local_name()]
#                    expect_single(
#                        [p for p in self.reducedcomponent.analog_receive_ports
#                         if p.name == ]))

                portconnections.remove((src_addr, dst_addr))

        # B. Handle Reduce Ports:
        # 1/ Make a map { reduce_port -> [send_port1, send_port2, send_port3],
        # ...}
        reduce_connections = defaultdict(list)
        for src, dst in portconnections:
            dstport = new_analog_ports[dst.get_local_name()]
            srcport = new_analog_ports[src.get_local_name()]
            if dstport.mode == 'reduce':
                reduce_connections[dstport].append(srcport)

        # 2/ Substitute each reduce port in turn:
        for dstport, srcport_list in reduce_connections.iteritems():
            src_subs = [s.name for s in srcport_list]
            terms = [dstport.name] + src_subs
            reduce_expr = reduce(reduce_ops[dstport.operator],
                                 (sympy.Symbol(s) for s in terms))

            # globalRemapPort( dstport.name, reduce_expr )
            DynamicsExpandPortDefinition(
                originalname=dstport.name, targetname=reduce_expr).visit(
                    self.reducedcomponent)


def flatten(model, componentname=None):
    reducer = ComponentFlattener(model, componentname)
    return reducer.reducedcomponent

from ..base import Dynamics
