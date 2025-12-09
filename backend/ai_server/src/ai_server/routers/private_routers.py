from fastapi import APIRouter, HTTPException, Body, UploadFile, File, Form
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime
import json
import os
import shutil
from pathlib import Path

from ai_server.metrics import scheduler_metrics, model_metrics
from ai_server.services.model_service import ModelService, SAMPLE_INTERACTION_DATA
from ai_server.services.scheduler_service import SchedulerService
from ai_server.services import scheduler_service, data_chef_service
from ai_server.utils import metric_utils

router = APIRouter()


# Request Models
class CreateModelRequest(BaseModel):
    """Request model for creating a new model"""
    model_id: str
    model_name: str
    algorithm: str
    message: str
    hyperparameters: Optional[Dict[str, Any]] = None


class UpdateModelHyperparametersRequest(BaseModel):
    """Request model for updating model hyperparameters"""
    hyperparameters: Dict[str, Any]


class GetModelInfoRequest(BaseModel):
    """Request model for getting model information"""
    model_id: str


class AddModelTaskRequest(BaseModel):
    """Request model for adding a model task"""
    task_name: str
    model_id: str
    data_chef_id: str
    interval: int


class RemoveModelTaskRequest(BaseModel):
    """Request model for removing a model task"""
    task_name: str


class RenameTaskRequest(BaseModel):
    """Request model for renaming a task"""
    old_name: str
    new_name: str


class UpdateTaskModelIdRequest(BaseModel):
    """Request model for updating task model ID"""
    task_name: str
    model_id: str


class UpdateTaskDataChefIdRequest(BaseModel):
    """Request model for updating task data chef IDs"""
    task_name: str
    data_chef_id: str


class UpdateTaskIntervalRequest(BaseModel):
    """Request model for updating task interval"""
    task_name: str
    interval: int


class StopSchedulerRequest(BaseModel):
    """Request model for stopping scheduler"""
    timeout: float


class RestartSchedulerRequest(BaseModel):
    """Request model for restarting scheduler"""
    timeout: float


class CreateDataChefFromCsvRequest(BaseModel):
    """Request model for creating data chef from CSV"""
    data_chef_id: str
    file_path: str
    rename_columns: str


class DatabaseConfig(BaseModel):
    """Database configuration model"""
    type: str  # mysql, postgresql, sqlite, mongodb
    host: str
    port: int
    user: Optional[str] = None
    username: Optional[str] = None
    password: str
    database: str
    ssl: bool = False
    auth_source: Optional[str] = "admin"


class CreateDataChefFromSqlRequest(BaseModel):
    """Request model for creating data chef from SQL"""
    data_chef_id: str
    query: str
    rename_columns: str
    db_config: Optional[DatabaseConfig] = None


class CreateDataChefFromNosqlRequest(BaseModel):
    """Request model for creating data chef from NoSQL"""
    data_chef_id: str
    database: str
    collection: str
    rename_columns: str
    db_config: Optional[DatabaseConfig] = None


class CreateDataChefFromApiRequest(BaseModel):
    """Request model for creating data chef from API"""
    data_chef_id: str
    api_endpoint: str
    rename_columns: str
    paginated: bool = False
    pagination_param: str = "page"
    size_param: str = "size"
    size_value: int = 100


class CreateDataChefFromMessageQueueRequest(BaseModel):
    """Request model for creating data chef from message queue"""
    data_chef_id: str
    brokers: str
    topic: str
    rename_columns: str
    group_id: str


class DataChefEditRequest(BaseModel):
    """Request model for editing data chef values"""
    values: Dict[str, Any]


# Model Endpoints
@router.post("/create_model")
def create_model(request: CreateModelRequest) -> dict:
    """
    Create and train a new recommendation model.

    :param request: Request containing model creation parameters
    :return: A confirmation message
    """
    try:
        service = ModelService()
        service.initialize_training(
            model_id=request.model_id,
            model_name=request.model_name,
            algorithm=request.algorithm,
            message=request.message,
            hyperparameters=request.hyperparameters
        )
        service.train_batch(request.model_id, SAMPLE_INTERACTION_DATA)
        service.finalize_training(request.model_id)
        service.save_model(request.model_id)

        return {"message": f"Model {request.model_id} created and saved successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list_models")
async def list_models() -> dict:
    """
    List all available models.

    :return: A list of available models
    """
    try:
        service = ModelService()
        models = await service.list_models()
        return models
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get_model_info/{model_id}")
def get_model_info(model_id: str) -> dict:
    """
    Get detailed information about a specific model.

    :param model_id: ID of the model
    :return: Model information including hyperparameters
    """
    try:
        service = ModelService()
        model_info = service.get_model_info(model_id)
        return model_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/update_model_hyperparameters/{model_id}")
def update_model_hyperparameters(model_id: str, request: UpdateModelHyperparametersRequest) -> dict:
    """
    Update hyperparameters of a model. Model will need to be retrained after update.

    :param model_id: ID of the model to update
    :param request: Request containing new hyperparameters
    :return: A confirmation message
    """
    try:
        service = ModelService()

        if model_id not in service.model_configs:
            raise ValueError(f"Model {model_id} not found")

        config = service.model_configs[model_id]
        old_hyperparameters = config.get("hyperparameters", {})

        config["hyperparameters"].update(request.hyperparameters)

        config["status"] = "modified"
        config["modified_at"] = datetime.now().isoformat()

        config_path = service.models_dir / f"{model_id}_config.json"
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2, default=str)

        return {
            "message": f"Hyperparameters updated for model {model_id}. Model needs to be retrained.",
            "old_hyperparameters": old_hyperparameters,
            "new_hyperparameters": config["hyperparameters"],
            "status": "modified"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get_available_algorithms")
def get_available_algorithms() -> dict:
    """
    Get list of available algorithms and their default hyperparameters.

    :return: Dictionary of available algorithms with details
    """
    try:
        service = ModelService()
        algorithms = service.get_algorithm_details()
        return {"algorithms": algorithms}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate_hyperparameters/{algorithm}")
def validate_hyperparameters(algorithm: str, hyperparameters: Dict[str, Any] = Body(...)) -> dict:
    """
    Validate hyperparameters for a specific algorithm.

    :param algorithm: Algorithm to validate parameters for
    :param hyperparameters: Hyperparameters to validate
    :return: Validation result with errors/warnings
    """
    try:
        service = ModelService()
        validation_result = service.validate_algorithm_parameters(algorithm, hyperparameters)
        return validation_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete_model/{model_id}")
def delete_model(model_id: str) -> dict:
    """
    Delete a model and all its associated files.

    :param model_id: ID of the model to delete
    :return: A confirmation message
    """
    try:
        service = ModelService()
        result = service.delete_model(model_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Task Management Endpoints
@router.post("/add_model_task")
def add_model_task(request: AddModelTaskRequest) -> dict:
    """
    Add a new model training task to the scheduler.

    :param request: Request containing task parameters
    :return: A confirmation message
    """
    try:
        scheduler = SchedulerService()
        scheduler.add_model_task(
            task_name=request.task_name,
            model_id=request.model_id,
            interactions_data_chef_id=request.data_chef_id,
            interval=request.interval
        )
        return {"message": f"Task {request.task_name} added successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/remove_model_task")
def remove_model_task(request: RemoveModelTaskRequest) -> dict:
    """
    Remove a model training task from the scheduler.

    :param request: Request containing task name to remove
    :return: A confirmation message
    """
    try:
        scheduler = SchedulerService()
        scheduler.remove_model_task(request.task_name)
        return {"message": f"Task {request.task_name} removed successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list_tasks")
async def list_tasks() -> dict:
    """
    List all scheduled tasks.

    :return: A list of scheduled tasks
    """
    try:
        scheduler = SchedulerService()
        tasks = await scheduler.list_tasks()
        return tasks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rename_task")
def rename_task(request: RenameTaskRequest) -> dict:
    """
    Rename a scheduled task.

    :param request: Request containing old and new task names
    :return: A confirmation message
    """
    try:
        scheduler = SchedulerService()
        scheduler.set_task_name(request.old_name, request.new_name)
        return {"message": f"Task renamed from {request.old_name} to {request.new_name} successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update_task_model_id")
def update_task_model_id(request: UpdateTaskModelIdRequest) -> dict:
    """
    Update the model ID for a scheduled task.

    :param request: Request containing task name and new model ID
    :return: A confirmation message
    """
    try:
        scheduler = SchedulerService()
        scheduler.set_model_id(request.task_name, request.model_id)
        return {"message": f"Task {request.task_name} model_id updated to {request.model_id} successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update_task_interactions_data_chef_id")
def update_task_interactions_data_chef_id(request: UpdateTaskDataChefIdRequest) -> dict:
    """
    Update the interaction data chef ID for a scheduled task.

    :param request: Request containing task name and new data chef ID
    :return: A confirmation message
    """
    try:
        scheduler = SchedulerService()
        scheduler.set_interactions_data_chef_id(request.task_name, request.data_chef_id)
        return {
            "message": f"Task {request.task_name} interactions_data_chef_id updated to {request.data_chef_id} successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update_task_item_features_data_chef_id")
def update_task_item_features_data_chef_id(request: UpdateTaskDataChefIdRequest) -> dict:
    """
    Update the item features data chef ID for a scheduled task.

    :param request: Request containing task name and new data chef ID
    :return: A confirmation message
    """
    try:
        scheduler = SchedulerService()
        scheduler.set_item_features_data_chef_id(request.task_name, request.data_chef_id)
        return {
            "message": f"Task {request.task_name} item_features_data_chef_id updated to {request.data_chef_id} successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update_task_user_features_data_chef_id")
def update_task_user_features_data_chef_id(request: UpdateTaskDataChefIdRequest) -> dict:
    """
    Update the user features data chef ID for a scheduled task.

    :param request: Request containing task name and new data chef ID
    :return: A confirmation message
    """
    try:
        scheduler = SchedulerService()
        scheduler.set_user_features_data_chef_id(request.task_name, request.data_chef_id)
        return {
            "message": f"Task {request.task_name} user_features_data_chef_id updated to {request.data_chef_id} successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update_task_interval")
def update_task_interval(request: UpdateTaskIntervalRequest) -> dict:
    """
    Update the interval for a scheduled task.

    :param request: Request containing task name and new interval
    :return: A confirmation message
    """
    try:
        scheduler = SchedulerService()
        scheduler.set_interval(request.task_name, request.interval)
        return {"message": f"Task {request.task_name} interval updated to {request.interval} seconds successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Scheduler Management Endpoints
@router.post("/stop_scheduler")
def stop_scheduler(request: StopSchedulerRequest) -> dict:
    """
    Stop the scheduler.

    :param request: Request containing timeout value
    :return: A confirmation message
    """
    try:
        scheduler = scheduler_service.get_scheduler_manager()
        scheduler.stop(request.timeout)
        return {"message": "Scheduler stopped successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/restart_scheduler")
def restart_scheduler(request: RestartSchedulerRequest) -> dict:
    """
    Restart the scheduler.

    :param request: Request containing timeout value
    :return: A confirmation message
    """
    try:
        scheduler = scheduler_service.get_scheduler_manager()
        scheduler.restart(request.timeout)
        return {"message": "Scheduler restarted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Data Chef Creation Endpoints
@router.post("/upload_csv")
async def upload_csv(
    file: UploadFile = File(...),
    data_chef_id: str = Form(...),
    rename_columns: str = Form("")
) -> dict:
    """
    Upload a CSV file and create a data chef from it.

    :param file: The CSV file to upload
    :param data_chef_id: ID for the data chef
    :param rename_columns: Column rename mapping
    :return: A confirmation message with file path
    """
    file_path = None
    try:
        upload_dir = Path("/app/data/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)

        file_extension = Path(file.filename).suffix if file.filename else ".csv"
        safe_filename = f"{data_chef_id}{file_extension}"
        file_path = upload_dir / safe_filename

        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        data_chef_service.DataChefService().create_data_chef_csv(
            name=data_chef_id,
            path=str(file_path),
            rename_columns=rename_columns
        )

        return {
            "message": f"File uploaded and data chef {data_chef_id} created successfully",
            "file_path": str(file_path),
            "original_filename": file.filename
        }
    except Exception as e:
        if file_path and file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create_data_chef_from_csv")
def create_data_chef_from_csv(request: CreateDataChefFromCsvRequest) -> dict:
    """
    Create a new data chef from a CSV file path (file must already exist on server).

    :param request: Request containing CSV data chef parameters
    :return: A confirmation message
    """
    try:
        data_chef_service.DataChefService().create_data_chef_csv(
            name=request.data_chef_id,
            path=request.file_path,
            rename_columns=request.rename_columns
        )
        return {"message": f"Data chef {request.data_chef_id} created successfully from {request.file_path}."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create_data_chef_from_sql")
def create_data_chef_from_sql(request: CreateDataChefFromSqlRequest) -> dict:
    """
    Create a new data chef from an SQL query.

    :param request: Request containing SQL data chef parameters
    :return: A confirmation message
    """
    try:
        # Convert db_config to dict if provided
        db_config_dict = None
        if request.db_config:
            db_config_dict = request.db_config.model_dump()

        data_chef_service.DataChefService().create_data_chef_sql(
            name=request.data_chef_id,
            query=request.query,
            rename_columns=request.rename_columns,
            db_config=db_config_dict
        )
        return {"message": f"Data chef {request.data_chef_id} created successfully from SQL query."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create_data_chef_from_nosql")
def create_data_chef_from_nosql(request: CreateDataChefFromNosqlRequest) -> dict:
    """
    Create a new data chef from a NoSQL database collection.

    :param request: Request containing NoSQL data chef parameters
    :return: A confirmation message
    """
    try:
        # Convert db_config to dict if provided
        db_config_dict = None
        if request.db_config:
            db_config_dict = request.db_config.model_dump()

        data_chef_service.DataChefService().create_data_chef_nosql(
            name=request.data_chef_id,
            database=request.database,
            collection=request.collection,
            rename_columns=request.rename_columns,
            db_config=db_config_dict
        )
        return {"message": f"Data chef {request.data_chef_id} created successfully from NoSQL collection."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create_data_chef_from_api")
def create_data_chef_from_api(request: CreateDataChefFromApiRequest) -> dict:
    """
    Create a new data chef from a REST API endpoint.

    :param request: Request containing API data chef parameters
    :return: A confirmation message
    """
    try:
        data_chef_service.DataChefService().create_data_chef_api(
            name=request.data_chef_id,
            url=request.api_endpoint,
            rename_columns=request.rename_columns,
            paginated=request.paginated,
            page_param=request.pagination_param,
            size_param=request.size_param,
            page_size=request.size_value
        )
        return {"message": f"Data chef {request.data_chef_id} created successfully from API endpoint."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create_data_chef_from_message_queue")
def create_data_chef_from_message_queue(request: CreateDataChefFromMessageQueueRequest) -> dict:
    """
    Create a new data chef from a message queue (e.g., Kafka).

    :param request: Request containing message queue data chef parameters
    :return: A confirmation message
    """
    try:
        data_chef_service.DataChefService().create_data_chef_messaging_queue(
            name=request.data_chef_id,
            brokers=request.brokers,
            topic=request.topic,
            rename_columns=request.rename_columns,
            group_id=request.group_id
        )
        return {"message": f"Data chef {request.data_chef_id} created successfully from message queue."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Data Chef Management Endpoints
@router.get("/list_data_chefs")
def list_data_chefs() -> dict:
    """
    List all available data chefs.

    :return: A list of available data chefs
    """
    try:
        data_chef = data_chef_service.DataChefService()
        data_chefs = data_chef.list_data_chefs()
        return data_chefs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get_data_chef/{data_chef_id}")
def get_data_chef(data_chef_id: str) -> dict:
    """
    Get details of a specific data chef.

    :param data_chef_id: ID of the data chef to retrieve
    :return: Details of the specified data chef
    """
    try:
        data_chef = data_chef_service.DataChefService()
        details = data_chef.get_data_chef(data_chef_id)
        return details
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete_data_chef/{data_chef_id}")
def delete_data_chef(data_chef_id: str) -> dict:
    """
    Delete a specific data chef.

    :param data_chef_id: ID of the data chef to delete
    :return: A confirmation message
    """
    try:
        data_chef = data_chef_service.DataChefService()
        data_chef.delete_data_chef(data_chef_id)
        return {"message": f"Data chef {data_chef_id} deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/edit_data_chef/{data_chef_id}")
def edit_data_chef(data_chef_id: str, request: DataChefEditRequest) -> dict:
    """
    Edit a specific data chef.

    :param data_chef_id: ID of the data chef to edit
    :param request: Request containing the new values for the data chef
    :return: A confirmation message
    """
    try:
        data_chef = data_chef_service.DataChefService()
        data_chef.edit_data_chef(data_chef_id, request.values)
        return {"message": f"Data chef {data_chef_id} edited successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get_total_data_chefs")
def get_total_data_chefs() -> dict:
    """
    Get the total number of data chefs.

    :return: Total count of data chefs
    """
    try:
        data_chef = data_chef_service.DataChefService()
        total = data_chef.get_total_data_chefs()
        return {"data": total}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


##### Metrics Endpoints #####

@router.get("/get_total_running_tasks")
def get_total_running_tasks() -> dict:
    """
    Get the total number of currently running tasks.

    :return: Total count of running tasks
    """
    try:
        total = metric_utils.get_metric_value(scheduler_metrics.TOTAL_RUNNING_TASKS)
        return {"data": total}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get_total_count_run_tasks")
def get_total_count_run_tasks() -> dict:
    """
    Get the total number of tasks that have been run.

    :return: Total count of run tasks
    """
    try:
        total = metric_utils.get_metric_value(scheduler_metrics.TOTAL_COUNT_RUN_TASKS)
        return {"data": total}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get_total_activated_tasks")
def get_total_activated_tasks() -> dict:
    """
    Get the total number of tasks that have been activated.

    :return: Total count of activated tasks
    """
    try:
        total = metric_utils.get_metric_value(scheduler_metrics.TOTAL_ACTIVATED_TASKS)
        return {"data": total}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get_task_runtime_seconds")
def get_task_runtime_seconds() -> dict:
    """
    Get the total runtime of tasks in seconds.

    :return: Total runtime of tasks in seconds
    """
    try:
        total = metric_utils.get_metric_value(scheduler_metrics.TASK_RUNTIME_SECONDS)
        return {"data": total}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get_total_activating_models")
def get_total_activating_models() -> dict:
    """
    Get the total number of models being activated.

    :return: Total count of activating models
    """
    try:
        total = metric_utils.get_metric_value(model_metrics.TOTAL_ACTIVATING_MODELS)
        return {"data": total}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get_total_training_models")
def get_total_training_models() -> dict:
    """
    Get the total number of models being trained.

    :return: Total count of training models
    """
    try:
        total = metric_utils.get_metric_value(model_metrics.TOTAL_TRAINING_MODELS)
        return {"data": total}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get_scheduler_status")
def get_scheduler_status() -> dict:
    """
    Get the current status of the scheduler.

    :return: Scheduler status information
    """
    try:
        scheduler = scheduler_service.get_scheduler_manager()
        is_running = scheduler.is_alive() if hasattr(scheduler, 'scheduler') else False

        return {
            "data": {
                "is_running": is_running,
                "status": "running" if is_running else "stopped"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get_server_logs")
def get_server_logs(limit: int = 50) -> dict:
    """
    Get recent server logs.

    :param limit: Maximum number of log entries to return
    :return: List of recent log entries
    """
    try:
        import os
        from datetime import datetime

        logs = []

        # Try to read from log file if it exists
        log_dir = os.path.join(os.getcwd(), "logs")
        if os.path.exists(log_dir):
            log_files = sorted([f for f in os.listdir(log_dir) if f.endswith('.log')], reverse=True)

            for log_file in log_files[:1]:  # Read only the most recent log file
                log_path = os.path.join(log_dir, log_file)
                try:
                    with open(log_path, 'r') as f:
                        lines = f.readlines()
                        for line in lines[-limit:]:
                            if line.strip():
                                logs.append({
                                    "timestamp": datetime.now().isoformat(),
                                    "message": line.strip(),
                                    "level": "INFO"
                                })
                except Exception as e:
                    pass

        # If no logs from file, return system info
        if not logs:
            logs = [
                {
                    "timestamp": datetime.now().isoformat(),
                    "message": "AI Server is running",
                    "level": "INFO"
                },
                {
                    "timestamp": datetime.now().isoformat(),
                    "message": f"Scheduler status: {'running' if scheduler_service.get_scheduler_manager().scheduler.is_running else 'stopped'}",
                    "level": "INFO"
                }
            ]

        return {"data": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
