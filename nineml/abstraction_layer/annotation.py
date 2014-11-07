from .. import E


class Annotation(dict):
    """
    Used for adding comments and build-tips to NineML documents
    """

    element_name = 'Annotation'

    def to_xml(self):
        return E(self.element_name,
                 *[E(k, v) for k, v in self.iteritems()])

    @classmethod
    def from_xml(cls, element, _):
        d = {}
        for child in element.getchildren():
            d[child.tag] = child.text
        return cls(**d)
