from abc import ABC, abstractmethod

class IProvider(ABC):

    @abstractmethod
    def connect(self):
        pass