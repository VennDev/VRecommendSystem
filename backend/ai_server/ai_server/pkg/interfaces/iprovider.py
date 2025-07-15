from abc import ABC, abstractmethod
from typing import Any

class IProvider(ABC):

    @abstractmethod
    def connect(self) -> Any:
        pass
