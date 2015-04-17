from nineml.utils import filter_discrete_types
from nineml.exceptions import NineMLRuntimeError
from .transitions import (OutputEvent, Trigger, StateAssignment, OnEvent,
                          OnCondition)
from nineml.abstraction_layer.expressions import RandomVariable
from nineml.abstraction_layer.expressions.utils import is_single_symbol


def SpikeOutputEvent():
    return OutputEvent('spikeoutput')


def cond_to_obj(cond_str):
    if isinstance(cond_str, Trigger):
        return cond_str
    elif cond_str is None:
        return None
    elif isinstance(cond_str, str):
        return Trigger(cond_str.strip())
    raise ValueError("Trigger: expected None, str, or Trigger object")


def do_to_assignments_and_events(doList):
    if not doList:
        return [], [], []
    # 'doList' is a list of strings, OutputEvents, and StateAssignments.
    do_type_list = (OutputEvent, basestring, StateAssignment, RandomVariable)
    do_types = filter_discrete_types(doList, do_type_list)
    # Convert strings to StateAssignments:
    sa_from_strs = [StateAssignment.from_str(s)
                    for s in do_types[basestring]]
    return (do_types[StateAssignment] + sa_from_strs, do_types[OutputEvent],
            do_types[RandomVariable])


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

    elif isinstance(trigger, OnCondition):
        return DoOnCondition(condition=trigger, do=do, to=to)
    else:
        err = "Unexpected Type for On() trigger: %s %s" % (type(trigger),
                                                           str(trigger))
        raise NineMLRuntimeError(err)


def DoOnEvent(input_event, do=None, to=None):
    assert isinstance(input_event, basestring)
    (assignments, output_events,
     random_variables) = do_to_assignments_and_events(do)
    return OnEvent(src_port_name=input_event,
                   state_assignments=assignments,
                   output_events=output_events,
                   random_variables=random_variables,
                   target_regime=to)


def DoOnCondition(condition, do=None, to=None):
    (assignments, output_events,
     random_variables) = do_to_assignments_and_events(do)
    return OnCondition(trigger=condition,
                       state_assignments=assignments,
                       output_events=output_events,
                       random_variables=random_variables,
                       target_regime=to)
