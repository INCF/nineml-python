

# parameter
def serialize(self, node, **options):  # @UnusedVariable
    node.attr('name', self.name, **options)
    node.attr('dimension', self.dimension.name, **options)


# alias
def serialize(self, node, **options):  # @UnusedVariable
    node.attr('MathInline', self.rhs_xml, in_body=True, **options)
    node.attr('name', self.lhs, **options)


# constant
def serialize(self, node, **options):  # @UnusedVariable
    node.attr('name', self.name, **options)
    node.attr('units', self.units.name, **options)
    if node.later_version(2.0, equal=True):
        node.attr('value', self.value, **options)
    else:
        node.body(self.value, sole=False)


# dynamics
def serialize(self, node, **options):  # @UnusedVariable @IgnorePep8
    node.attr('name', self.name, **options)
    if node.later_version(2.0, equal=True):
        within = None
    else:
        within = 'Dynamics'
    node.children(self.parameters, **options)
    node.children(self.ports, **options)
    node.children(self.state_variables, within=within, **options)
    node.children(self.regimes, within=within, **options)


# regime
def serialize(self, node, **options):  # @UnusedVariable
    node.attr('name', self.name, **options)
    node.children(self.sorted_elements())


# statevariable
def serialize(self, node, **options):  # @UnusedVariable
    node.attr('name', self.name, **options)
    node.attr('dimension', self.dimension.name, **options)


# outputevent
def serialize(self, node, **options):  # @UnusedVariable
    node.attr('port', self.port_name, **options)


# analogreceiveport
def serialize(self, node, **options):  # @UnusedVariable
    node.attr('name', self.name, **options)
    node.attr('dimension', self.dimension.name, **options)


# analogreduceport
def serialize(self, node, **options):  # @UnusedVariable
    node.attr('name', self.name, **options)
    node.attr('dimension', self.dimension.name, **options)
    node.attr('operator', self.operator, **options)


# analogsendport
def serialize(self, node, **options):  # @UnusedVariable
    node.attr('name', self.name, **options)
    node.attr('dimension', self.dimension.name, **options)


# eventsendport
def serialize(self, node, **options):  # @UnusedVariable
    node.attr('name', self.name, **options)


# eventreceiveport
def serialize(self, node, **options):  # @UnusedVariable
    node.attr('name', self.name, **options)


# stateassignment
def serialize(self, node, **options):  # @UnusedVariable
    node.attr('MathInline', self.rhs_xml, in_body=True, **options)
    node.attr('variable', self.lhs, **options)


# timederivative
def serialize(self, node, **options):  # @UnusedVariable @IgnorePep8
    node.attr('MathInline', self.rhs_xml, in_body=True, **options)
    node.attr('variable', self.variable, **options)


# oncondition
def serialize(self, node, **options):  # @UnusedVariable
    node.child(self.trigger, **options)
    node.attr('target_regime', self._target_regime.name, **options),
    node.children(self.sorted_elements())


# trigger
def serialize(self, node, **options):  # @UnusedVariable
    node.attr('MathInline', self.rhs_xml, in_body=True, **options)


# onevent
def serialize(self, node, **options):  # @UnusedVariable
    node.attr('port', self.src_port_name, **options)
    node.attr('target_regime', self.target_regime.name, **options)
    node.children(self.sorted_elements())

# connection_rule
def serialize(self, node, **options):  # @UnusedVariable @IgnorePep8
    node.children(self.sorted_elements())
    node.attr('name', self.name, **options)
    if node.later_version(2.0, equal=True):
        node.attr('standard_library', self.standard_library, **options)
    else:
        node.attr('standard_library', self.standard_library,
                  within='ConnectionRule', **options)

# random_distribution
def serialize(self, node, **options):  # @UnusedVariable @IgnorePep8
    node.children(self.sorted_elements())
    node.attr('name', self.name, **options)
    if node.later_version(2.0, equal=True):
        node.attr('standard_library', self.standard_library, **options)
    else:
        node.attr('standard_library', self.standard_library,
                  within='RandomDistribution', **options)
