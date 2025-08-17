from abc import ABC, abstractmethod

from scheduler import Scheduler


class BaseTask(ABC):

    @abstractmethod
    def inject(self, scheduler: Scheduler) -> None:
        """
        Abstract method to run the scheduler task.
        This method should be implemented by subclasses to define the specific scheduling logic.
        """
        pass
