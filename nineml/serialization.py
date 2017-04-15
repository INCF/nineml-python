from abc import ABCMeta, abstractmethod


class BaseSerializer(object):

    __metaclass__ = ABCMeta

    @abstractmethod
    def __call__(self):
        pass


class BaseUnserializer(object):

    __metaclass__ = ABCMeta

    @abstractmethod
    def __call__(self):
        pass
