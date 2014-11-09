from .. import E


class Dimension(object):
    """
    Defines the dimension used for quantity units
    """

    element_name = 'Dimension'
    valid_dims = ['m', 'l', 't', 'i', 'n', 'k', 'j']

    def __init__(self, name, **kwargs):
        self.name = name
        for k in kwargs:
            if k not in self.valid_dims:
                raise Exception("'{}' is not a valid dimension name ('{}')"
                                .format(k, "', '".join(self.valid_dims)))
        self._dims = kwargs

    def __eq__(self, other):
        assert isinstance(other, Dimension)
        return all(self.power(d) == other.power(d) for d in self.valid_dims)

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        return ("Dimension(name='{}'{})"
                .format(self.name, ''.join(", {}={}".format(d, p)
                                           for d, p in self._dims.items())))

    def power(self, dim_name):
        return self._dims.get(dim_name, 0)

    def to_xml(self):
        kwargs = {'name': self.name}
        kwargs.update(self._dims)
        return E(self.element_name,
                 **kwargs)

    @classmethod
    def from_xml(cls, element, _):
        kwargs = dict(element.attrib)
        name = kwargs.pop('name')
        return cls(name, **kwargs)


class Unit(object):
    """
    Defines the units of a quantity
    """

    element_name = 'Unit'

    def __init__(self, name, dimension, power, offset=0.0):
        self.name = name
        self.dimension = dimension
        self.power = power
        self.offset = offset

    def __eq__(self, other):
        assert isinstance(other, Unit)
        return (self.power == other.power and self.offset == other.power and
                self.dimension == other.dimension)

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        return ("Unit(name='{}', dimension='{}', power={}{})"
                .format(self.name, self.dimension.name, self.power,
                        (", offset='{}'".format(self.offset)
                         if self.offset else '')))

    @property
    def symbol(self):
        return self.name

    def to_xml(self):
        kwargs = {'symbol': self.symbol, 'dimension': self.dimension,
                  'power': self.power}
        if self.offset:
            kwargs['offset'] = self.offset
        return E(self.element_name,
                 **kwargs)

    @classmethod
    def from_xml(cls, element, context):
        name = element.attrib['symbol']
        dimension = context[element.attrib['dimension']]
        power = element.attrib['power']
        offset = element.attrib.get('name', 0.0)
        return cls(name, dimension, power, offset)
