"""
A collection of objects that are not part of the offical 9ML specification but
can be used as shorthand when drafting 9ML models in Python.
"""
from past.builtins import basestring
from nineml.utils.iterables import filter_discrete_types
from nineml.exceptions import NineMLUsageError
from nineml.abstraction.dynamics.transitions import (
    OutputEvent, Trigger, StateAssignment, OnEvent, OnCondition)
from nineml.abstraction.expressions.utils import is_single_symbol


def SpikeOutputEvent():
    return OutputEvent('spikeoutput')


def do_to_assignments_and_events(doList):
    if not doList:
        return [], []
    # 'doList' is a list of strings, OutputEvents, and StateAssignments.
    do_type_list = (OutputEvent, basestring, StateAssignment)
    do_types = filter_discrete_types(doList, do_type_list)
    # Convert strings to StateAssignments:
    sa_from_strs = [StateAssignment.from_str(s)
                    for s in do_types[basestring]]
    return do_types[StateAssignment] + sa_from_strs, do_types[OutputEvent]


# Forwarding Function:
def On(trigger, do=None, to=None):

    if isinstance(do, (OutputEvent, basestring)):
        do = [do]
    elif do is None:
        do = []
    if isinstance(trigger, basestring):
        if is_single_symbol(trigger):
            return DoOnEvent(input_event=trigger, do=do, to=to)
        else:
            return DoOnCondition(condition=trigger, do=do, to=to)

    elif isinstance(trigger, Trigger):
        return DoOnCondition(condition=trigger, do=do, to=to)
    else:
        raise NineMLUsageError(
            "Unexpected Type for On() trigger: {} {}".format(
                type(trigger), str(trigger)))


def DoOnEvent(input_event, do=None, to=None):
    assert isinstance(input_event, basestring)
    assignments, output_events = do_to_assignments_and_events(do)
    return OnEvent(src_port_name=input_event,
                   state_assignments=assignments,
                   output_events=output_events,
                   target_regime_name=to)


def DoOnCondition(condition, do=None, to=None):
    assignments, output_events = do_to_assignments_and_events(do)
    return OnCondition(trigger=condition,
                       state_assignments=assignments,
                       output_events=output_events,
                       target_regime_name=to)
