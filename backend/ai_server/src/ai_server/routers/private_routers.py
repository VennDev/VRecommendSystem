from fastapi import APIRouter, HTTPException

from ai_server.services.model_service import ModelService, SAMPLE_INTERACTION_DATA
from ai_server.services.scheduler_service import SchedulerService
from ai_server.services import scheduler_service

router = APIRouter()


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
async def list_tasks() -> list[dict]:
    """
    List all scheduled tasks.

    :return: A list of scheduled tasks
    """
    try:
        scheduler = SchedulerService()
        tasks = list(await scheduler.list_tasks())
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
