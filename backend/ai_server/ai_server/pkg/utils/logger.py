from loguru import logger
from ..configs.log_config import get_log_config

def logger_init():
    cfg = get_log_config()
    logger.add(
        "logs/{time:YYYY-MM-DD}.log", 
        rotation=str(cfg.maxSize) + " MB",
        retention=str(cfg.maxBackups) + " days",
        compression="zip" if cfg.compress else None,
        enqueue=True,
        serialize=True,
    )