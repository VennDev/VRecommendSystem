import asyncio
import json
import threading
from pathlib import Path
from typing import Optional

import loguru
from scheduler import Scheduler

from ai_server.config.config import Config
from ai_server.metrics import scheduler_metrics
from ai_server.tasks.model_trainer_task import ModelTrainerTask


class SchedulerManager:
    """
    Manager class to handle scheduler lifecycle with the ability to stop and restart.
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

        # Increment the running tasks metric
        scheduler_metrics.TOTAL_RUNNING_TASKS.inc()

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


class SchedulerService:
    """
    Service to manage scheduling tasks in the AI server.
    """

    def __init__(self, scheduler_dir: str = "tasks") -> None:
        """
        Initialize the SchedulerService with the directory where the scheduler is located.
        """
        self.scheduler_dir = Path(scheduler_dir)
        self.scheduler_dir.mkdir(exist_ok=True)

    def add_model_task(self, task_name: str, model_id: str, interactions_data_chef_id: str,
                       user_features_data_chef_id: Optional[str] = None,
                       item_features_data_chef_id: Optional[str] = None,
                       interval: int = 3600) -> None:
        """
        Add a model training task to the scheduler.

        :param task_name: Name of the task.
        :param model_id: ID of the model to be trained.
        :param interactions_data_chef_id: ID of the interaction data chef associated with the model.
        :param user_features_data_chef_id: ID of the user features data chef (optional).
        :param item_features_data_chef_id: ID of the item features data chef (optional).
        :param interval: Interval in seconds for the task to run.
        """
        task_file = self.scheduler_dir / f"{task_name}.json"

        # Check if the task already exists
        if task_file.exists():
            loguru.logger.error(f"Task {task_name} already exists. Overwriting the existing task.")
            return

        task_config = {
            "task_name": task_name,
            "model_id": model_id,
            "interactions_data_chef_id": interactions_data_chef_id,
            "user_features_data_chef_id": user_features_data_chef_id,
            "item_features_data_chef_id": item_features_data_chef_id,
            "interval": interval
        }

        with open(task_file, 'w') as f:
            json.dump(task_config, f)

        loguru.logger.info(f"Task {task_name} added for model {model_id} with interval {interval} seconds.")

    def remove_model_task(self, task_name: str) -> None:
        """
        Remove a model training task from the scheduler.
        :param task_name:
        :return:
        Remove a model training task from the scheduler.
        """
        task_file = self.scheduler_dir / f"{task_name}.json"

        if not task_file.exists():
            loguru.logger.error(f"Task {task_name} does not exist.")
            return

        task_file.unlink()
        loguru.logger.info(f"Task {task_name} removed from scheduler.")

    async def list_tasks(self) -> dict:
        """
        List all scheduled tasks.
        :return: A dictionary with task names as keys and their configurations as values.
        """
        tasks = {}
        for task_file in self.scheduler_dir.glob("*.json"):
            with open(task_file, 'r') as f:
                task_config = json.load(f)
                name_file = task_file.stem
                tasks[name_file] = task_config
            await asyncio.sleep(0)  # Yield control to the event loop
        return tasks

    def set_task_name(self, old_name: str, new_name: str) -> None:
        """
        Rename a scheduled task.
        :param old_name: Current name of the task.
        :param new_name: New name for the task.
        """
        old_task_file = self.scheduler_dir / f"{old_name}.json"
        new_task_file = self.scheduler_dir / f"{new_name}.json"

        if not old_task_file.exists():
            loguru.logger.error(f"Task {old_name} does not exist.")
            return

        if new_task_file.exists():
            loguru.logger.error(f"Task {new_name} already exists. Choose a different name.")
            return

        old_task_file.rename(new_task_file)

        # set the task_name inside the file to the new name
        with open(new_task_file, 'r+') as f:
            task_config = json.load(f)
            task_config['task_name'] = new_name
            f.seek(0)
            json.dump(task_config, f)
            f.truncate()

        loguru.logger.info(f"Task renamed from {old_name} to {new_name}.")

    def set_model_id(self, task_name: str, model_id: str) -> None:
        """
        Update the model ID for a scheduled task.

        :param task_name: Name of the task to update.
        :param model_id: New model ID to set.
        """
        task_file = self.scheduler_dir / f"{task_name}.json"

        if not task_file.exists():
            loguru.logger.error(f"Task {task_name} does not exist.")
            return

        with open(task_file, 'r+') as f:
            task_config = json.load(f)
            task_config['model_id'] = model_id
            f.seek(0)
            json.dump(task_config, f)
            f.truncate()

        loguru.logger.info(f"Model ID for task {task_name} updated to {model_id}.")

    def set_interactions_data_chef_id(self, task_name: str, data_chef_id: str) -> None:
        """
        Update the data chef ID for a scheduled task.

        :param task_name: Name of the task to update.
        :param data_chef_id: New data chef ID to set.
        """
        task_file = self.scheduler_dir / f"{task_name}.json"

        if not task_file.exists():
            loguru.logger.error(f"Task {task_name} does not exist.")
            return

        with open(task_file, 'r+') as f:
            task_config = json.load(f)
            task_config['interactions_data_chef_id'] = data_chef_id
            f.seek(0)
            json.dump(task_config, f)
            f.truncate()

        loguru.logger.info(f"Interaction Data Chef ID for task {task_name} updated to {data_chef_id}.")

    def set_item_features_data_chef_id(self, task_name: str, data_chef_id: str) -> None:
        """
        Update the item features data chef ID for a scheduled task.

        :param task_name: Name of the task to update.
        :param data_chef_id: New item features data chef ID to set.
        """
        task_file = self.scheduler_dir / f"{task_name}.json"

        if not task_file.exists():
            loguru.logger.error(f"Task {task_name} does not exist.")
            return

        with open(task_file, 'r+') as f:
            task_config = json.load(f)
            task_config['item_features_data_chef_id'] = data_chef_id
            f.seek(0)
            json.dump(task_config, f)
            f.truncate()

        loguru.logger.info(f"Item Features Data Chef ID for task {task_name} updated to {data_chef_id}.")

    def set_user_features_data_chef_id(self, task_name: str, data_chef_id: str) -> None:
        """
        Update the user features data chef ID for a scheduled task.

        :param task_name: Name of the task to update.
        :param data_chef_id: New user features data chef ID to set.
        """
        task_file = self.scheduler_dir / f"{task_name}.json"

        if not task_file.exists():
            loguru.logger.error(f"Task {task_name} does not exist.")
            return

        with open(task_file, 'r+') as f:
            task_config = json.load(f)
            task_config['user_features_data_chef_id'] = data_chef_id
            f.seek(0)
            json.dump(task_config, f)
            f.truncate()

        loguru.logger.info(f"User Features Data Chef ID for task {task_name} updated to {data_chef_id}.")

    def set_interval(self, task_name: str, interval: int) -> None:
        """
        Update the interval for a scheduled task.

        :param task_name:
        :param interval:
        :return:
        """
        task_file = self.scheduler_dir / f"{task_name}.json"

        if not task_file.exists():
            loguru.logger.error(f"Task {task_name} does not exist.")
            return

        with open(task_file, 'r+') as f:
            task_config = json.load(f)
            task_config['interval'] = interval
            f.seek(0)
            json.dump(task_config, f)
            f.truncate()

        loguru.logger.info(f"Interval for task {task_name} updated to {interval} seconds.")


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
