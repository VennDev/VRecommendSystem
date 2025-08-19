import datetime
import os
import glob
import json
import loguru
from pathlib import Path
from scheduler import Scheduler

from ai_server.tasks.base_task import BaseTask


def _train_model_task(config: dict, json_file: str) -> None:
    """
    Placeholder function for model training logic.
    You will implement this later.
    """
    model_name = config.get("model_name", "Unknown Model")
    loguru.logger.info(f"Training task triggered for {model_name} from {json_file}")
    loguru.logger.info(f"Config: {config}")

    # TODO: Implement actual training logic here
    # This is where you will add your model training code
    pass


class ModelTrainerTask(BaseTask):
    def inject(self, scheduler: Scheduler) -> None:
        """
        Scheduler task that reads JSON configuration files from models folder
        and schedules training tasks based on interval values.
        """
        try:
            # Get the path to models folder (outside src folder, at project root)
            current_file_path = Path(__file__)
            project_root = current_file_path.parent.parent.parent.parent
            tasks_folder = project_root / "tasks"

            loguru.logger.info(f"Looking for JSON files in: {tasks_folder}")

            if not tasks_folder.exists():
                loguru.logger.warning(f"Models folder does not exist: {tasks_folder}")
                return

            # Find all JSON files in models folder
            json_files = glob.glob(str(tasks_folder / "*.json"))

            if not json_files:
                loguru.logger.info("No JSON files found in models folder")
                return

            loguru.logger.info(f"Found {len(json_files)} JSON files")

            # Process each JSON file
            for json_file in json_files:
                try:
                    with open(json_file, "r", encoding="utf-8") as file:
                        config = json.load(file)

                    # Extract an interval from config
                    interval = config.get("interval")

                    if interval is None:
                        loguru.logger.warning(f"No 'interval' found in {json_file}")
                        continue

                    if not isinstance(interval, (int, float)) or interval <= 0:
                        loguru.logger.warning(
                            f"Invalid 'interval' value in {json_file}: {interval}"
                        )
                        continue

                    model_name = config.get("model_name", os.path.basename(json_file))
                    loguru.logger.info(
                        f"Scheduling task for {model_name} with interval: {interval} seconds"
                    )

                    # Schedule the training task to run every interval second
                    scheduler.minutely(
                        timing=datetime.time(second=interval),
                        handle=_train_model_task,
                        args=(config, json_file)
                    )
                except json.JSONDecodeError as e:
                    loguru.logger.error(f"Error parsing JSON file {json_file}: {e}")
                except Exception as e:
                    loguru.logger.error(f"Error processing file {json_file}: {e}")

            loguru.logger.info("All JSON files processed and scheduled")
        except Exception as e:
            loguru.logger.error(f"Error in run_task: {e}")
