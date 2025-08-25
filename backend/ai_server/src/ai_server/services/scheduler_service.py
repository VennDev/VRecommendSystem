import asyncio
import json
from pathlib import Path
from typing import Generator

import loguru


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

    def add_model_task(self, task_name: str, model_id: str, data_chef_id: str, interval: int) -> None:
        """
        Add a model training task to the scheduler.

        :param task_name: Name of the task.
        :param model_id: ID of the model to be trained.
        :param data_chef_id: ID of the data chef associated with the model.
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
            "data_chef_id": data_chef_id,
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
                tasks[task_config['task_name']] = task_config
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

    def set_data_chef_id(self, task_name: str, data_chef_id: str) -> None:
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
            task_config['data_chef_id'] = data_chef_id
            f.seek(0)
            json.dump(task_config, f)
            f.truncate()

        loguru.logger.info(f"Data Chef ID for task {task_name} updated to {data_chef_id}.")

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
