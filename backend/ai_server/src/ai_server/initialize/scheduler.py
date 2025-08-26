from ai_server.services.scheduler_service import get_scheduler_manager


def init() -> bool:
    """
    Initialize the scheduler using the global manager.
    """
    return get_scheduler_manager().init()
