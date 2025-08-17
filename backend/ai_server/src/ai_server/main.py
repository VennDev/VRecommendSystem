import loguru

from ai_server.initialize import logger, scheduler


def main():
    """
    Main entry point for the application.
    """
    # Initialize logger
    logger.init()
    loguru.logger.info("Logger initialized.")

    # Initialize scheduler
    scheduler.init()
    loguru.logger.info("Scheduler initialized.")
