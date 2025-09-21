import datetime
import os
import glob
import json
import threading
from typing import Optional

import loguru
from pathlib import Path

from scheduler import Scheduler

from ai_server.metrics import scheduler_metrics
from ai_server.services.data_chef_service import DataChefService
from ai_server.services.model_service import ModelService
from ai_server.utils.result_processing import dict_to_dataframe
from ai_server.tasks.base_task import BaseTask


def _train_model_task_async(
        config: dict,
        json_file: str,
        interactions_data_chef_id: str,
        item_features_data_chef_id: Optional[str] = None,
        user_features_data_chef_id: Optional[str] = None,
) -> None:
    """
    Non-blocking training task that spawns training in separate thread
    """
    # Increment the running tasks metric
    scheduler_metrics.TOTAL_RUNNING_TASKS.inc()

    model_name = config.get("model_name", "Unknown Model")
    model_id = config.get("model_id")

    loguru.logger.info(f"Training task triggered for {model_name} from {json_file}")

    # Check if the model is already training
    service = ModelService()
    try:
        current_status = service.get_training_status(model_id)

        if current_status and current_status.get('status') == 'training':
            loguru.logger.warning(f"Model {model_id} is already training. Skipping this iteration.")
            return
    except Exception as e:
        loguru.logger.error(f"Error checking training status for {model_id}: {e}")

    # Create a separate thread for the actual training
    training_thread = threading.Thread(
        target=_execute_training_in_background,
        args=(config, json_file, interactions_data_chef_id, item_features_data_chef_id, user_features_data_chef_id),
        daemon=False,  # Changed to False for better debugging
        name=f"Training-{model_id}"
    )

    training_thread.start()
    loguru.logger.info(f"Training started in background thread for {model_name} (Thread: {training_thread.name})")

    # Optional: Monitor thread for debugging
    def monitor_thread():
        try:
            training_thread.join(timeout=300)  # Wait max 5 minutes
            if training_thread.is_alive():
                loguru.logger.warning(f"Training thread for {model_name} is still alive after 5 minutes")
            else:
                loguru.logger.info(f"Training thread for {model_name} completed")
        except Exception as e:
            loguru.logger.error(f"Error monitoring thread for {model_name}: {e}")
        finally:
            # Ensure the metric is decremented in case of monitoring issues
            scheduler_metrics.TOTAL_RUNNING_TASKS.dec()

            loguru.logger.info(f"Monitor thread for {model_name} is finishing")

    monitor_thread_instance = threading.Thread(target=monitor_thread, daemon=True, name=f"Monitor-{model_id}")
    monitor_thread_instance.start()


def _execute_training_in_background(
        config: dict,
        json_file: str,
        interactions_data_chef_id: str,
        item_features_data_chef_id: Optional[str] = None,
        user_features_data_chef_id: Optional[str] = None,
) -> None:
    """
    The actual training logic that runs in background thread
    """
    model_name = config.get("model_name", "Unknown Model")
    model_id = config.get("model_id")
    service = None

    try:
        loguru.logger.info(f"Background training started for {model_name}")

        service = ModelService()

        # Initialize training with error handling
        try:
            service.initialize_training(
                model_id=model_id,
                model_name=model_name,
                algorithm=config.get("algorithm"),
                message=config.get("message"),
                hyperparameters=config.get("hyperparameters", {}),
            )
            loguru.logger.info(f"Training initialization completed for {model_name}")
        except Exception as init_error:
            loguru.logger.error(f"Error during training initialization for {model_name}: {str(init_error)}")
            loguru.logger.exception("Full initialization error traceback:")
            raise

        data_chef = DataChefService()

        # Get data generators with error handling
        try:
            interactions_gen = data_chef.cook(interactions_data_chef_id)
            loguru.logger.info(f"Interactions data generator created for {model_name}")
        except Exception as data_error:
            loguru.logger.error(f"Error creating interactions data generator for {model_name}: {str(data_error)}")
            raise

        item_features_gen = None
        if item_features_data_chef_id is not None:
            try:
                item_features_gen = data_chef.cook(item_features_data_chef_id)
                loguru.logger.info(f"Item features data generator created for {model_name}")
            except Exception as item_error:
                loguru.logger.warning(f"Error creating item features generator for {model_name}: {str(item_error)}")

        user_features_gen = None
        if user_features_data_chef_id is not None:
            try:
                user_features_gen = data_chef.cook(user_features_data_chef_id)
                loguru.logger.info(f"User features data generator created for {model_name}")
            except Exception as user_error:
                loguru.logger.warning(f"Error creating user features generator for {model_name}: {str(user_error)}")

        # Process batches with error handling
        batch_count = 0
        try:
            for interactions_data in interactions_gen:
                try:
                    interactions_df = dict_to_dataframe(interactions_data)

                    item_features_df = None
                    if item_features_gen:
                        try:
                            item_data = next(item_features_gen)
                            item_features_df = dict_to_dataframe(item_data) if item_data else None
                        except StopIteration:
                            loguru.logger.warning("Item features generator exhausted, using None")
                        except Exception as item_batch_error:
                            loguru.logger.warning(f"Error processing item features batch: {item_batch_error}")

                    user_features_df = None
                    if user_features_gen:
                        try:
                            user_data = next(user_features_gen)
                            user_features_df = dict_to_dataframe(user_data) if user_data else None
                        except StopIteration:
                            loguru.logger.warning("User features generator exhausted, using None")
                        except Exception as user_batch_error:
                            loguru.logger.warning(f"Error processing user features batch: {user_batch_error}")

                    # Train batch with error handling
                    service.train_batch(model_id, interactions_df, item_features=item_features_df,
                                        user_features=user_features_df)
                    batch_count += 1

                    # Non-blocking progress logging
                    try:
                        progress = service.get_training_status(model_id)
                        loguru.logger.info(f"Training progress for {model_name}: batch {batch_count}")
                    except Exception as progress_error:
                        loguru.logger.warning(f"Could not get training progress: {progress_error}")

                except Exception as batch_error:
                    loguru.logger.error(
                        f"Error processing batch {batch_count + 1} for {model_name}: {str(batch_error)}")
                    # Continue with the next batch instead of stopping
                    continue

            loguru.logger.info(f"Completed processing {batch_count} batches for {model_name}")

        except Exception as batch_loop_error:
            loguru.logger.error(f"Error in batch processing loop for {model_name}: {str(batch_loop_error)}")
            raise

        # The critical finalize_training call with enhanced error handling
        loguru.logger.info(f"Starting finalization for {model_name} (this may take time...)")
        try:
            # Set a reasonable timeout for finalization if your service supports it
            service.finalize_training(model_id)
            loguru.logger.info(f"Finalization completed for {model_name}")

            # Save model with error handling
            try:
                service.save_model(model_id)
                loguru.logger.info(f"Model saved successfully for {model_name}")
            except Exception as save_error:
                loguru.logger.error(f"Error saving model for {model_name}: {str(save_error)}")
                # Don't raise here, training was successful even if save failed

        except Exception as finalize_error:
            loguru.logger.critical(f"Error during finalization for {model_name}: {str(finalize_error)}")
            loguru.logger.exception("Full finalization error traceback:")

            # Try to update training status to fail
            try:
                if hasattr(service, 'update_training_status'):
                    service.update_training_status(model_id, 'failed', str(finalize_error))
            except Exception as status_error:
                loguru.logger.error(f"Could not update training status to failed: {status_error}")

            raise  # Re-raise to ensure the error is not silently ignored

        loguru.logger.info(f"Training completed successfully for {model_name}")

    except Exception as e:
        loguru.logger.error(f"Background training failed for {model_name}: {str(e)}")
        loguru.logger.exception("Full training error traceback:")

        # Ensure training status is updated to failed
        try:
            if service and hasattr(service, 'update_training_status'):
                service.update_training_status(model_id, 'failed', str(e))
        except Exception as status_error:
            loguru.logger.error(f"Could not update training status: {status_error}")

        # Don't re-raise here to prevent thread from crashing the main process
        loguru.logger.error(f"Thread for {model_name} will terminate due to error")
    finally:
        # Decrement the running tasks metric
        scheduler_metrics.TOTAL_RUNNING_TASKS.dec()

        loguru.logger.info(f"Training thread for {model_name} is finishing")


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
            models_folder = project_root / "models"

            loguru.logger.info(f"Looking for JSON files in tasks folder at: {tasks_folder}")
            loguru.logger.info(f"Models folder: {models_folder}")

            if not tasks_folder.exists():
                loguru.logger.warning(f"Tasks folder does not exist: {tasks_folder}")
                return

            if not models_folder.exists():
                loguru.logger.warning(f"Models folder does not exist: {models_folder}")
                return

            # Find all JSON files in models folder
            json_files = glob.glob(str(tasks_folder / "*.json"))

            if not json_files:
                loguru.logger.info("No JSON files found in tasks folder")
                return

            loguru.logger.info(f"Found {len(json_files)} JSON files")

            # Process each JSON file
            scheduled_count = 0
            for json_file in json_files:
                try:
                    with open(json_file, "r", encoding="utf-8") as file:
                        config = json.load(file)

                    # Extract required fields from config
                    interval = config.get("interval")
                    model_id = config.get("model_id")
                    interactions_data_chef_id = config.get("interactions_data_chef_id")
                    item_features_data_chef_id = config.get("item_features_data_chef_id")
                    user_features_data_chef_id = config.get("user_features_data_chef_id")

                    # Validate required fields
                    if interval is None:
                        loguru.logger.warning(f"No 'interval' found in {json_file}")
                        continue

                    if model_id is None:
                        loguru.logger.warning(f"No 'model_id' found in {json_file}")
                        continue

                    if interactions_data_chef_id is None:
                        loguru.logger.warning(f"No 'interactions_data_chef_id' found in {json_file}")
                        continue

                    if not isinstance(interval, (int, float)) or interval <= 0:
                        loguru.logger.warning(f"Invalid 'interval' value in {json_file}: {interval}")
                        continue

                    # Load model configuration
                    model_file_path = models_folder / f"{model_id}.json"
                    if not model_file_path.exists():
                        loguru.logger.warning(f"Model file not found: {model_file_path}")
                        continue

                    try:
                        with open(model_file_path, "r", encoding="utf-8") as model_file:
                            model_data = json.load(model_file)
                    except Exception as model_load_error:
                        loguru.logger.error(f"Error loading model file {model_file_path}: {model_load_error}")
                        continue

                    model_name = config.get("task_name", os.path.basename(json_file))
                    loguru.logger.info(f"Scheduling task for {model_name} with interval: {interval} seconds")

                    # Schedule the training task to run every interval second
                    scheduler.minutely(
                        timing=datetime.time(second=interval),
                        handle=_train_model_task_async,
                        args=(
                            model_data,
                            json_file,
                            interactions_data_chef_id,
                            item_features_data_chef_id,
                            user_features_data_chef_id,
                        )
                    )
                    scheduled_count += 1

                except json.JSONDecodeError as e:
                    loguru.logger.error(f"Error parsing JSON file {json_file}: {e}")
                except Exception as e:
                    loguru.logger.error(f"Error processing file {json_file}: {e}")

            # Update metrics
            scheduler_metrics.TOTAL_COUNT_RUN_TASKS.inc(scheduled_count)

            loguru.logger.info(f"Successfully scheduled {scheduled_count} out of {len(json_files)} JSON files")
        except Exception as e:
            loguru.logger.error(f"Error in inject method: {e}")
            loguru.logger.exception("Full inject error traceback:")
