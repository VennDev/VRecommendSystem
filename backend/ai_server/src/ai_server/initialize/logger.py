from loguru import logger
import hydra
from omegaconf import DictConfig

@hydra.main(config_path='../config', config_name='local', version_base=None)
def init(cfg: DictConfig):
    pattern_time = "{time:YYYY-MM-DD}"
    if cfg.logger.local_time:
        pattern_time = "{time:YYYY-MM-DD HH:mm}"
    logger.add(
        "logs/" + pattern_time + ".log",
        rotation=str(cfg.logger.max_size) + " MB",
        retention=str(cfg.logger.max_backups) + " days",
        compression="zip" if cfg.logger.compression else None,
        enqueue=True,
        serialize=True,
    )
