from . import E


class Annotations(dict):
    """
    Defines the dimension used for quantity units
    """

    element_name = 'Annotation'

    def __repr__(self):
        return ("Annotation({})"
                .format(', '.join('{}={}'.format(k, v)
                                  for k, v in self.iteritems())))

    def to_xml(self):
        return E(self.element_name,
                 *self.itervalues())

    @classmethod
    def from_xml(cls, element):
        children = {}
        for child in element.getchildren():
            children[child.tag] = child
        return cls(**children)
