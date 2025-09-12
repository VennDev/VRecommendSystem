from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Dict, Any

from ai_server.services.model_service import ModelService, SAMPLE_INTERACTION_DATA
from ai_server.services.scheduler_service import SchedulerService
from ai_server.services import scheduler_service, data_chef_service

router = APIRouter()


class DataChefEditRequest(BaseModel):
    """Request model for editing data chef values"""
    values: Dict[str, Any]


@router.post("/create_model/{model_id}/{model_name}/{algorithm}/{message}")
def create_model(model_id: str, model_name: str, algorithm: str, message: str) -> dict:
    """
    Create and train a new recommendation model.

    :param model_id: ID of the model to be created
    :param model_name: Name of the model
    :param algorithm: Algorithm to be used for training
    :param message: Message or description for the model
    :return: a Confirmation message
    """
    try:
        service = ModelService()
        service.initialize_training(
            model_id=model_id,
            model_name=model_name,
            algorithm=algorithm,
            message=message
        )
        service.train_batch(model_id, SAMPLE_INTERACTION_DATA)
        service.finalize_training(model_id)
        service.save_model(model_id)

        return {"message": f"Model {model_id} created and saved successfully."}
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


@router.post("/add_model_task/{task_name}/{model_id}/{data_chef_id}/{interval}")
def add_model_task(task_name: str, model_id: str, data_chef_id: str, interval: int) -> dict:
    """
    Add a new model training task to the scheduler.

    :param task_name: Name of the task
    :param model_id: ID of the model to be trained
    :param data_chef_id: ID of the data chef to be used
    :param interval: Interval in seconds for the task to run
    :return: a Confirmation message
    """

    try:
        scheduler = SchedulerService()
        scheduler.add_model_task(
            task_name=task_name,
            model_id=model_id,
            interactions_data_chef_id=data_chef_id,
            interval=interval
        )
        return {"message": f"Task {task_name} added successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/remove_model_task/{task_name}")
def remove_model_task(task_name: str) -> dict:
    """
    Remove a model training task from the scheduler.

    :param task_name: Name of the task to be removed from
    :return: a Confirmation message
    """

    try:
        scheduler = SchedulerService()
        scheduler.remove_model_task(task_name)
        return {"message": f"Task {task_name} removed successfully."}
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


@router.post("/set_task_name/{old_name}/{new_name}")
def set_task_name(old_name: str, new_name: str) -> dict:
    """
    Rename a scheduled task.

    :param old_name: Current name of the task
    :param new_name: New name for the task
    :return: a Confirmation message
    """
    try:
        scheduler = SchedulerService()
        scheduler.set_task_name(old_name, new_name)
        return {"message": f"Task renamed from {old_name} to {new_name} successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/set_task_model_id/{task_name}/{model_id}")
def set_task_model_id(task_name: str, model_id: str) -> dict:
    """
    Update the model ID for a scheduled task.

    :param task_name: Name of the task to be updated
    :param model_id: New model ID to be set
    :return: a Confirmation message
    """
    try:
        scheduler = SchedulerService()
        scheduler.set_model_id(task_name, model_id)
        return {"message": f"Task {task_name} model_id updated to {model_id} successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/set_task_interactions_data_chef_id/{task_name}/{data_chef_id}")
def set_task_data_chef_id(task_name: str, data_chef_id: str) -> dict:
    """
    Update the interaction data chef ID for a scheduled task.

    :param task_name: Name of the task to be updated
    :param data_chef_id: New data chef ID to be set
    :return: a Confirmation message
    """
    try:
        scheduler = SchedulerService()
        scheduler.set_interactions_data_chef_id(task_name, data_chef_id)
        return {"message": f"Task {task_name} interactions_data_chef_id updated to {data_chef_id} successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/set_task_item_features_data_chef_id/{task_name}/{data_chef_id}")
def set_task_item_features_data_chef_id(task_name: str, data_chef_id: str) -> dict:
    """
    Update the item features data chef ID for a scheduled task.

    :param task_name: Name of the task to be updated
    :param data_chef_id: New data chef ID to be set
    :return: A confirmation message
    """
    try:
        scheduler = SchedulerService()
        scheduler.set_item_features_data_chef_id(task_name, data_chef_id)
        return {"message": f"Task {task_name} item_features_data_chef_id updated to {data_chef_id} successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/set_task_user_features_data_chef_id/{task_name}/{data_chef_id}")
def set_task_user_features_data_chef_id(task_name: str, data_chef_id: str) -> dict:
    """
    Update the user features data chef ID for a scheduled task.

    :param task_name:
    :param data_chef_id:
    :return: A confirmation message
    """
    try:
        scheduler = SchedulerService()
        scheduler.set_user_features_data_chef_id(task_name, data_chef_id)
        return {"message": f"Task {task_name} user_features_data_chef_id updated to {data_chef_id} successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/set_task_interval/{task_name}/{interval}")
def set_task_interval(task_name: str, interval: int) -> dict:
    """
    Update the interval for a scheduled task.

    :param task_name: Name of the task to be updated
    :param interval: New interval in seconds to be set
    :return: a Confirmation message
    """
    try:
        scheduler = SchedulerService()
        scheduler.set_interval(task_name, interval)
        return {"message": f"Task {task_name} interval updated to {interval} seconds successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop_scheduler/{timeout}")
def stop_scheduler(timeout: float) -> dict:
    """
    Stop the scheduler.

    :return: A confirmation message
    """
    try:
        scheduler = scheduler_service.get_scheduler_manager()
        scheduler.stop(timeout)
        return {"message": "Scheduler started successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/restart_scheduler/{timeout}")
def restart_scheduler(timeout: float) -> dict:
    """
    Restart the scheduler.

    :return: A confirmation message
    """
    try:
        scheduler = scheduler_service.get_scheduler_manager()
        scheduler.restart(timeout)
        return {"message": "Scheduler restarted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create_data_chef_from_csv/{data_chef_id}/{file_path}/{rename_columns}")
def create_data_chef_from_csv(data_chef_id: str, file_path: str, rename_columns: str) -> dict:
    """
    Create a new data chef from a CSV file.

    :param data_chef_id: ID of the data chef to be created
    :param file_path: Path to the CSV file
    :param rename_columns: Column renaming mapping in the format "old_key1->new_key1,old_key2->new_key2"
    :return: A confirmation message
    """
    try:
        data_chef_service.DataChefService().create_data_chef_csv(
            name=data_chef_id,
            path=file_path,
            rename_columns=rename_columns
        )
        return {"message": f"Data chef {data_chef_id} created successfully from {file_path}."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create_data_chef_from_sql/{data_chef_id}/{query}/{rename_columns}")
def create_data_chef_from_sql(data_chef_id: str, query: str, rename_columns: str) -> dict:
    """
    Create a new data chef from an SQL query.

    :param data_chef_id: ID of the data chef to be created
    :param query: SQL query to fetch data
    :param rename_columns: Column renaming mapping in the format "old_key1->new_key1,old_key2->new_key2"
    :return: A confirmation message
    """
    try:
        data_chef_service.DataChefService().create_data_chef_sql(
            name=data_chef_id,
            query=query,
            rename_columns=rename_columns
        )
        return {"message": f"Data chef {data_chef_id} created successfully from SQL query."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create_data_chef_from_nosql/{data_chef_id}/{database}/{collection}/{rename_columns}")
def create_data_chef_from_nosql(data_chef_id: str, database: str, collection: str, rename_columns: str) -> dict:
    """
    Create a new data chef from a NoSQL database collection.

    :param data_chef_id: ID of the data chef to be created
    :param database: Name of the NoSQL database
    :param collection: Name of the collection within the database
    :param rename_columns: Column renaming mapping in the format "old_key1->new_key1,old_key2->new_key2"
    :return: A confirmation message
    """
    try:
        data_chef_service.DataChefService().create_data_chef_nosql(
            name=data_chef_id,
            database=database,
            collection=collection,
            rename_columns=rename_columns
        )
        return {"message": f"Data chef {data_chef_id} created successfully from NoSQL collection."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/create_data_chef_from_api/{data_chef_id}/{api_endpoint}/{rename_columns}/{paginated}/{pagination_param}/{size_param}/{size_value}")
def create_data_chef_from_api(
        data_chef_id: str,
        api_endpoint: str,
        rename_columns: str,
        paginated: bool = False,
        pagination_param: str = "page",
        size_param: str = "size",
        size_value: int = 100
) -> dict:
    """
    Create a new data chef from a REST API endpoint.

    :param data_chef_id: ID of the data chef to be created
    :param api_endpoint: URL of the REST API endpoint
    :param rename_columns: Column renaming mapping in the format "old_key1->new_key1,old_key2->new_key2"
    :param paginated: Whether the API is paginated (default is False)
    :param pagination_param: Name of the pagination parameter (default is "page")
    :param size_param: Name of the page size parameter (default is "size")
    :param size_value: Value for the page size parameter (default is 100)
    :return: A confirmation message
    """
    try:
        data_chef_service.DataChefService().create_data_chef_api(
            name=data_chef_id,
            url=api_endpoint,
            rename_columns=rename_columns,
            paginated=paginated,
            page_param=pagination_param,
            size_param=size_param,
            page_size=size_value
        )
        return {"message": f"Data chef {data_chef_id} created successfully from API endpoint."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create_data_chef_from_message_queue/{data_chef_id}/{brokers}/{topic}/{rename_columns}/{group_id}")
def create_data_chef_from_message_queue(
        data_chef_id: str,
        brokers: str,
        topic: str,
        rename_columns: str,
        group_id: str
) -> dict:
    """
    Create a new data chef from a message queue (e.g., Kafka).

    :param data_chef_id: ID of the data chef to be created
    :param brokers: Comma-separated list of broker addresses
    :param topic: Topic to consume messages from
    :param rename_columns: Column renaming mapping in the format "old_key1->new_key1,old_key2->new_key2"
    :param group_id: Consumer group ID
    :return: A confirmation message
    """
    try:
        data_chef_service.DataChefService().create_data_chef_messaging_queue(
            name=data_chef_id,
            brokers=brokers,
            topic=topic,
            rename_columns=rename_columns,
            group_id=group_id
        )
        return {"message": f"Data chef {data_chef_id} created successfully from message queue."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
