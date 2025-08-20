import loguru

from ai_server.initialize import logger, scheduler, config


def main():
    """
    Main entry point for the application.
    """
    # Initialize config
    config.init()
    print("Initializing configuration...")

    # Initialize logger
    logger.init()
    loguru.logger.info("Logger initialized.")

    # Initialize scheduler
    scheduler.init()
    loguru.logger.info("Scheduler initialized.")

    while True:
        pass
