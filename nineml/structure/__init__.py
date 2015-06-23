from .. import BaseNineMLObject


class BaseSLObject(BaseNineMLObject):

    """
    Base class for user layer classes
    """

    def __init__(self):
        super(BaseSLObject, self).__init__()
        self.from_reference = None

    def __lt__(self, other):
        if self.__class__.__name__ < other.__class__.__name__:
            return True
        else:
            return self.name < other.name
