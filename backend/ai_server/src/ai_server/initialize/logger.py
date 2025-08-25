import os
import loguru
from ai_server.config.config import Config


def init() -> None:
    """
    Initialize the logger.
    """
    cfg = Config().get_config()

    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    if cfg.logger.local_time:
        log_file = os.path.join(log_dir, "app_{time:YYYY-MM-DD_HH-mm}.log")
    else:
        log_file = os.path.join(log_dir, "app_{time:YYYY-MM-DD}.log")

    loguru.logger.add(
        log_file,
        rotation=f"{cfg.logger.max_size} MB",
        retention=f"{cfg.logger.max_backups} days",
        compression="zip" if cfg.logger.compression else None,
        enqueue=cfg.logger.enqueue,
        serialize=cfg.logger.serialize,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
    )

    loguru.logger.info("Logger initialized successfully.")
