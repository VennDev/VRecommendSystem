import json
from pathlib import Path

import loguru


class SchedulerService:
    """
    Service to manage scheduling tasks in the AI server.
    """

    def __init__(self, scheduler_dir: str = "scheduler") -> None:
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
