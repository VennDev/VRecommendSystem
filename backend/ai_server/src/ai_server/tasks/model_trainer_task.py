import datetime
import os
import glob
import yaml
import loguru
from pathlib import Path
from scheduler import Scheduler

from ai_server.tasks.base_task import BaseTask


def _train_model_task(config: dict, yaml_file: str):
    """
    Placeholder function for model training logic.
    You will implement this later.
    """
    model_name = config.get("model_name", "Unknown Model")
    loguru.logger.info(f"Training task triggered for {model_name} from {yaml_file}")
    loguru.logger.info(f"Config: {config}")

    # TODO: Implement actual training logic here
    # This is where you will add your model training code
    pass


class ModelTrainerTask(BaseTask):
    def inject(self, scheduler: Scheduler) -> None:
        """
        Scheduler task that reads YAML configuration files from models folder
        and schedules training tasks based on running_time values.
        """
        try:
            # Get the path to models folder (outside src folder, at project root)
            current_file_path = Path(__file__)
            project_root = current_file_path.parent.parent.parent.parent
            models_folder = project_root / "models"

            loguru.logger.info(f"Looking for YAML files in: {models_folder}")

            if not models_folder.exists():
                loguru.logger.warning(f"Models folder does not exist: {models_folder}")
                return

            # Find all YAML files in models folder
            yaml_files = glob.glob(str(models_folder / "*.yaml")) + glob.glob(
                str(models_folder / "*.yml")
            )

            if not yaml_files:
                loguru.logger.info("No YAML files found in models folder")
                return

            loguru.logger.info(f"Found {len(yaml_files)} YAML files")

            # Process each YAML file
            for yaml_file in yaml_files:
                try:
                    with open(yaml_file, "r", encoding="utf-8") as file:
                        config = yaml.safe_load(file)

                    # Extract running_time from config
                    running_time = config.get("running_time")

                    if running_time is None:
                        loguru.logger.warning(f"No 'running_time' found in {yaml_file}")
                        continue

                    if not isinstance(running_time, (int, float)) or running_time <= 0:
                        loguru.logger.warning(
                            f"Invalid 'running_time' value in {yaml_file}: {running_time}"
                        )
                        continue

                    model_name = config.get("model_name", os.path.basename(yaml_file))
                    loguru.logger.info(
                        f"Scheduling task for {model_name} with running_time: {running_time} seconds"
                    )

                    # Schedule the training task to run every running_time second
                    scheduler.minutely(
                        timing=datetime.time(second=running_time),
                        handle=_train_model_task,
                        args=(config, yaml_file)
                    )
                except yaml.YAMLError as e:
                    loguru.logger.error(f"Error parsing YAML file {yaml_file}: {e}")
                except Exception as e:
                    loguru.logger.error(f"Error processing file {yaml_file}: {e}")

            loguru.logger.info("All YAML files processed and scheduled")
        except Exception as e:
            loguru.logger.error(f"Error in run_task: {e}")
