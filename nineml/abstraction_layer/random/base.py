from nineml.abstraction_layer.components import BaseComponentClass



class ComponentClass(BaseComponentClass):

    def __init__(self, name, parameters=None):
        super(ComponentClass, self).__init__(name, parameters)
