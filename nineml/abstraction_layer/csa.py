
from component.interface import Parameter


class ConnectionSetTemplate(object):

    def __init__(self, expr):
        self.parameters = [Parameter('p')]  # This is a temporary hack
