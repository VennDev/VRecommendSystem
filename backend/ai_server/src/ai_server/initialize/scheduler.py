import threading
from typing import Optional

import loguru
from scheduler import Scheduler

from ai_server.config.config import Config
from ai_server.tasks.model_trainer_task import ModelTrainerTask


class SchedulerManager:
    """
    Manager class to handle scheduler lifecycle with ability to stop and restart.
    """

    def __init__(self):
        self.scheduler: Optional[Scheduler] = None
        self.scheduler_thread: Optional[threading.Thread] = None
        self.stop_event: Optional[threading.Event] = None
        self.is_running = False

    def _start_scheduler_loop(self, scheduler: Scheduler, stop_event: threading.Event) -> None:
        """
        Start the scheduler in a loop that can be stopped.
        """
        while not stop_event.is_set():
            scheduler.exec_jobs()
            # Use the stop_event.wait() instead of threading.Event().wait()
            # This allows the loop to be interrupted when stop_event is set
            if stop_event.wait(timeout=1.0):
                break

    def init(self) -> bool:
        """
        Initialize the scheduler.
        Returns True if successfully initialized, False if already running.
        """
        if self.is_running:
            loguru.logger.warning("Scheduler is already running. Stop it first before reinitializing.")
            return False

        cfg = Config().get_config()
        self.scheduler = Scheduler(n_threads=cfg.scheduler.threads)

        # Inject the ModelTrainerTask into the scheduler
        ModelTrainerTask().inject(self.scheduler)

        # Create stop event
        self.stop_event = threading.Event()

        # Start the scheduler in a separate thread
        self.scheduler_thread = threading.Thread(
            target=self._start_scheduler_loop,
            args=(self.scheduler, self.stop_event),
            daemon=True,
            name="SchedulerThread"
        )
        self.scheduler_thread.start()
        self.is_running = True

        loguru.logger.info("Scheduler initialized and started successfully.")
        return True

    def stop(self, timeout: float = 5.0) -> bool:
        """
        Stop the scheduler gracefully.

        Args:
            timeout: Maximum time to wait for the scheduler to stop (seconds)

        Returns:
            True if stopped successfully, False if timeout occurred
        """
        if not self.is_running:
            loguru.logger.info("Scheduler is not running.")
            return True

        loguru.logger.info("Stopping scheduler...")

        # Signal the scheduler loop to stop
        if self.stop_event:
            self.stop_event.set()

        # Wait for the thread to finish
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=timeout)

            if self.scheduler_thread.is_alive():
                loguru.logger.info(f"Warning: Scheduler thread did not stop within {timeout} seconds.")
                return False

        # Clean up
        self.scheduler = None
        self.scheduler_thread = None
        self.stop_event = None
        self.is_running = False

        loguru.logger.info("Scheduler stopped successfully.")
        return True

    def restart(self, timeout: float = 5.0) -> bool:
        """
        Restart the scheduler (stop and then init).

        Args:
            timeout: Maximum time to wait for the scheduler to stop (seconds)

        Returns:
            True if restarted successfully, False otherwise
        """
        loguru.logger.info("Restarting scheduler...")

        if not self.stop(timeout=timeout):
            loguru.logger.warning("Failed to stop scheduler, cannot restart.")
            return False

        return self.init()

    def is_alive(self) -> bool:
        """
        Check if the scheduler is running.
        """
        return (self.is_running and
                self.scheduler_thread is not None and
                self.scheduler_thread.is_alive())

    def get_status(self) -> dict:
        """
        Get the current status of the scheduler.
        """
        return {
            "is_running": self.is_running,
            "thread_alive": self.scheduler_thread.is_alive() if self.scheduler_thread else False,
            "thread_name": self.scheduler_thread.name if self.scheduler_thread else None,
            "scheduler_exists": self.scheduler is not None
        }


# Global instance
_scheduler_manager: Optional[SchedulerManager] = None


def get_scheduler_manager() -> SchedulerManager:
    """
    Get the global scheduler manager instance (singleton pattern).
    """
    global _scheduler_manager
    if _scheduler_manager is None:
        _scheduler_manager = SchedulerManager()
    return _scheduler_manager


def init() -> bool:
    """
    Initialize the scheduler using the global manager.
    """
    return get_scheduler_manager().init()


def stop_scheduler(timeout: float = 5.0) -> bool:
    """
    Stop the scheduler using the global manager.
    """
    return get_scheduler_manager().stop(timeout)


def restart_scheduler(timeout: float = 5.0) -> bool:
    """
    Restart the scheduler using the global manager.
    """
    return get_scheduler_manager().restart(timeout)


def get_scheduler_status() -> dict:
    """
    Get the current scheduler status.
    """
    return get_scheduler_manager().get_status()
