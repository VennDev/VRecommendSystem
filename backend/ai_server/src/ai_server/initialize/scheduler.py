import threading
from scheduler import Scheduler

from ai_server.config.config import Config
from ai_server.tasks.model_trainer_task import ModelTrainerTask


def _start_scheduler(scheduler: Scheduler) -> None:
    """
    Start the scheduler in a separate thread.
    This function is called by the init function to initialize the scheduler.
    """
    while True:
        scheduler.exec_jobs()
        # Sleep for a while to avoid busy waiting
        threading.Event().wait(1)


def init() -> None:
    """
    Initialize the scheduler.
    """
    cfg = Config().get_config()
    scheduler = Scheduler(n_threads=cfg.scheduler.threads)

    # Inject the ModelTrainerTask into the scheduler
    ModelTrainerTask().inject(scheduler)

    # Start the scheduler in a separate thread
    scheduler_thread = threading.Thread(target=_start_scheduler, args=(scheduler,), daemon=True)
    scheduler_thread.start()
