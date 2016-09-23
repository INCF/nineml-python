import unittest
from nineml.abstraction.dynamics.transitions import (Trigger, Transition, OutputEvent, OnEvent)
from nineml.utils.testing.comprehensive import instances_of_all_types
from nineml.exceptions import (NineMLNoSolutionException, NineMLInvalidElementTypeException, NineMLRuntimeError)


class TestTriggerExceptions(unittest.TestCase):

    def test__becomes_true_ninemlnosolutionexception(self):
        """
        line #: 469
        message: 

        context:
        --------
    def _becomes_true(cls, expr):
        if t not in expr.atoms():
            # TODO: For sub expressions that don't involve t, this could be
            #       handled by a piecewise expression
        """

        self.assertRaises(
            NineMLNoSolutionException,
            Trigger._becomes_true,
            expr=None)

    def test__becomes_true_ninemlnosolutionexception2(self):
        """
        line #: 477
        message: 

        context:
        --------
    def _becomes_true(cls, expr):
        if t not in expr.atoms():
            # TODO: For sub expressions that don't involve t, this could be
            #       handled by a piecewise expression
            raise NineMLNoSolutionException
        if isinstance(expr, (sympy.StrictGreaterThan,
                             sympy.StrictLessThan)):
            # Get the equation for the transition between true and false
            equality = sympy.Eq(*expr.args)
            solution = sympy.solvers.solve(equality, t)
            try:
                if len(solution) != 1:
        """

        self.assertRaises(
            NineMLNoSolutionException,
            Trigger._becomes_true,
            expr=None)

    def test__becomes_true_ninemlnosolutionexception3(self):
        """
        line #: 479
        message: 

        context:
        --------
    def _becomes_true(cls, expr):
        if t not in expr.atoms():
            # TODO: For sub expressions that don't involve t, this could be
            #       handled by a piecewise expression
            raise NineMLNoSolutionException
        if isinstance(expr, (sympy.StrictGreaterThan,
                             sympy.StrictLessThan)):
            # Get the equation for the transition between true and false
            equality = sympy.Eq(*expr.args)
            solution = sympy.solvers.solve(equality, t)
            try:
                if len(solution) != 1:
                    raise NineMLNoSolutionException
            except TypeError:
        """

        self.assertRaises(
            NineMLNoSolutionException,
            Trigger._becomes_true,
            expr=None)

    def test__becomes_true_ninemlnosolutionexception4(self):
        """
        line #: 487
        message: 

        context:
        --------
    def _becomes_true(cls, expr):
        if t not in expr.atoms():
            # TODO: For sub expressions that don't involve t, this could be
            #       handled by a piecewise expression
            raise NineMLNoSolutionException
        if isinstance(expr, (sympy.StrictGreaterThan,
                             sympy.StrictLessThan)):
            # Get the equation for the transition between true and false
            equality = sympy.Eq(*expr.args)
            solution = sympy.solvers.solve(equality, t)
            try:
                if len(solution) != 1:
                    raise NineMLNoSolutionException
            except TypeError:
                raise NineMLNoSolutionException
            time_expr = solution[0]
        elif isinstance(expr, sympy.Or):
            time_expr = sympy.Min(*(cls._becomes_true(a) for a in expr.args))
        else:
            # TODO: Should add handling for And expressions but will need
            # conditional handling for expressions that are true and then
            # become false.
        """

        self.assertRaises(
            NineMLNoSolutionException,
            Trigger._becomes_true,
            expr=None)


class TestTransitionExceptions(unittest.TestCase):

    def test_target_regime_ninemlruntimeerror(self):
        """
        line #: 206
        message: Target regime ({}) has not been set (use 'validate()' of Dynamics first).

        context:
        --------
    def target_regime(self):
        \"\"\"Returns the target regime of this transition.

        .. note::

            This method will only be available after the Dynamics
            containing this transition has been built. See
            ``set_source_regime``
        \"\"\"
        if self._target_regime is None:
        """

        transition = next(instances_of_all_types['Transition'].itervalues())
        with self.assertRaises(NineMLRuntimeError):
            print transition.target_regime

    def test_source_regime_ninemlruntimeerror(self):
        """
        line #: 231
        message: Source regime has not been set (use 'validate()' of Dynamics first).

        context:
        --------
    def source_regime(self):
        \"\"\"Returns the source regime of this transition.

        .. note::

            This method will only be available after the |Dynamics|
            containing this transition has been built. See
            ``set_source_regime``
        \"\"\"
        if self._source_regime is None:
        """

        transition = next(instances_of_all_types['Transition'].itervalues())
        with self.assertRaises(NineMLRuntimeError):
            print transition.source_regime

    def test_add_ninemlinvalidelementtypeexception(self):
        """
        line #: 306
        message: Could not add element of type '{}' to {} class

        context:
        --------
    def add(self, element):
        if isinstance(element, StateAssignment):
            self._state_assignments[element.name] = element
        elif isinstance(element, OutputEvent):
            self._output_events[element.name] = element
        else:
        """

        transition = next(instances_of_all_types['Transition'].itervalues())
        self.assertRaises(
            NineMLInvalidElementTypeException,
            transition.add,
            element=None)

    def test_remove_ninemlinvalidelementtypeexception(self):
        """
        line #: 316
        message: Could not remove element of type '{}' to {} class

        context:
        --------
    def remove(self, element):
        if isinstance(element, StateAssignment):
            self._state_assignments.pop(element.name)
        elif isinstance(element, OutputEvent):
            self._output_events.pop(element.name)
        else:
        """

        transition = next(instances_of_all_types['Transition'].itervalues())
        self.assertRaises(
            NineMLInvalidElementTypeException,
            transition.remove,
            element=None)


class TestOutputEventExceptions(unittest.TestCase):

    def test_port_ninemlruntimeerror(self):
        """
        line #: 109
        message: Cannot access port as output event has not been bound

        context:
        --------
    def port(self):
        if self._port is None:
        """

        outputevent = next(instances_of_all_types['OutputEvent'].itervalues())
        with self.assertRaises(NineMLRuntimeError):
            print outputevent.port


class TestOnEventExceptions(unittest.TestCase):

    def test_port_ninemlruntimeerror(self):
        """
        line #: 358
        message: OnEvent is not bound to a component class

        context:
        --------
    def port(self):
        if self._port is None:
        """

        onevent = next(instances_of_all_types['OnEvent'].itervalues())
        with self.assertRaises(NineMLRuntimeError):
            print onevent.port

