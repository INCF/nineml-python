import unittest
from nineml.abstraction.dynamics.regimes import (TimeDerivative, Regime)
from nineml.utils.testing.comprehensive import instances_of_all_types
from nineml.exceptions import (NineMLRuntimeError)


class TestTimeDerivativeExceptions(unittest.TestCase):

    def test_from_str_ninemlruntimeerror(self):
        """
        line #: 143
        message: err

        context:
        --------
    def from_str(cls, time_derivative_string):
        \"\"\"Creates an TimeDerivative object from a string\"\"\"
        # Note: \w = [a-zA-Z0-9_]
        tdre = re.compile(r\"\"\"\s* d(?P<dependent_var>[a-zA-Z][a-zA-Z0-9_]*)/dt
                           \s* = \s*
                           (?P<rhs> .*) \"\"\", re.VERBOSE)

        match = tdre.match(time_derivative_string)
        if not match:
            err = "Unable to load time derivative: %s" % time_derivative_string
        """

        self.assertRaises(
            NineMLRuntimeError,
            TimeDerivative.from_str,
            time_derivative_string=None)


class TestRegimeExceptions(unittest.TestCase):

    def test___init___ninemlruntimeerror(self):
        """
        line #: 204
        message: err

        context:
        --------
    def __init__(self, *args, **kwargs):
        \"\"\"Regime constructor

            :param name: The name of the constructor. If none, then a name will
                be automatically generated.
            :param time_derivatives: A list of time derivatives, as
                either ``string``s (e.g 'dg/dt = g/gtau') or as
                |TimeDerivative| objects.
            :param transitions: A list containing either |OnEvent| or
                |OnCondition| objects, which will automatically be sorted into
                the appropriate classes automatically.
            :param *args: Any non-keyword arguments will be treated as
                time_derivatives.


        \"\"\"
        BaseALObject.__init__(self)
        ContainerObject.__init__(self)
        valid_kwargs = ('name', 'transitions', 'time_derivatives', 'aliases')
        for arg in kwargs:
            if arg not in valid_kwargs:
                err = 'Unexpected Arg: %s' % arg
        """

        regime = instances_of_all_types['Regime']
        self.assertRaises(
            NineMLRuntimeError,
            regime.__init__)

    def test___init___ninemlruntimeerror2(self):
        """
        line #: 252
        message: '{}' provided to Regime 'aliases' kwarg, 'Alias' expected

        context:
        --------
    def __init__(self, *args, **kwargs):
        \"\"\"Regime constructor

            :param name: The name of the constructor. If none, then a name will
                be automatically generated.
            :param time_derivatives: A list of time derivatives, as
                either ``string``s (e.g 'dg/dt = g/gtau') or as
                |TimeDerivative| objects.
            :param transitions: A list containing either |OnEvent| or
                |OnCondition| objects, which will automatically be sorted into
                the appropriate classes automatically.
            :param *args: Any non-keyword arguments will be treated as
                time_derivatives.


        \"\"\"
        BaseALObject.__init__(self)
        ContainerObject.__init__(self)
        valid_kwargs = ('name', 'transitions', 'time_derivatives', 'aliases')
        for arg in kwargs:
            if arg not in valid_kwargs:
                err = 'Unexpected Arg: %s' % arg
                raise NineMLRuntimeError(err)

        name = kwargs.get('name', None)
        if name is None:
            self._name = 'default'
        else:
            self._name = name.strip()
            ensure_valid_identifier(self._name)
        # Get Time derivatives from args or kwargs
        kw_tds = normalise_parameter_as_list(
            kwargs.get('time_derivatives', None))
        time_derivatives = list(args) + kw_tds
        # Un-named arguments are time_derivatives:
        time_derivatives = normalise_parameter_as_list(time_derivatives)
        # time_derivatives.extend( args )
        td_types = (basestring, TimeDerivative)
        td_type_dict = filter_discrete_types(time_derivatives, td_types)
        td_from_str = [TimeDerivative.from_str(o)
                       for o in td_type_dict[basestring]]
        time_derivatives = td_type_dict[TimeDerivative] + td_from_str
        # Check for double definitions:
        td_dep_vars = [td.variable for td in time_derivatives]
        assert_no_duplicates(
            td_dep_vars,
            ("Multiple time derivatives found for the same state variable "
                 "in regime '{}' (found '{}')".format(
                     self.name,
                     "', '".join(td.variable for td in time_derivatives))))
        # Store as a dictionary
        self._time_derivatives = dict((td.variable, td)
                                      for td in time_derivatives)

        # We support passing in 'transitions', which is a list of both OnEvents
        # and OnConditions. So, lets filter this by type and add them
        # appropriately:
        transitions = normalise_parameter_as_list(kwargs.get('transitions',
                                                             None))
        f_dict = filter_discrete_types(transitions, (OnEvent, OnCondition))
        self._on_events = {}
        self._on_conditions = {}
        # Add all the OnEvents and OnConditions:
        for elem in chain(f_dict[OnEvent], f_dict[OnCondition]):
            self.add(elem)

        self._aliases = {}
        # Add regime specific aliases
        for alias in normalise_parameter_as_list(kwargs.get('aliases', None)):
            if not isinstance(alias, Alias):
        """

        regime = instances_of_all_types['Regime']
        self.assertRaises(
            NineMLRuntimeError,
            regime.__init__)

