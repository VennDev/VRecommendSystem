import loguru
from ai_server.config.config import Config


def init() -> None:
    """
    Initialize the logger.
    """
    cfg = Config().get_config()
    pattern_time = "{time:YYYY-MM-DD}"
    if cfg.logger.local_time:
        pattern_time = "{time:YYYY-MM-DD HH:mm}"

    loguru.logger.add(
        "logs/" + pattern_time + ".log",
        rotation=str(cfg.logger.max_size) + " MB",
        retention=str(cfg.logger.max_backups) + " days",
        compression="zip" if cfg.logger.compression else None,
        enqueue=True,
        serialize=True,
    )

    loguru.logger.info("Initializing logger.")
