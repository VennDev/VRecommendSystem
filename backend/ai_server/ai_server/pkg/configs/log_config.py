import os
from dataclasses import dataclass

@dataclass
class LogConfigResult:
    maxSize: int 
    maxBackups: int
    maxAge: int
    compress: bool
    localTime: bool

def get_log_config() -> LogConfigResult:
    return LogConfigResult(
        maxSize=int(os.getenv("LOG_MAX_SIZE", 10)),
        maxBackups=int(os.getenv("LOG_MAX_BACKUPS", 5)),
        maxAge=int(os.getenv("LOG_MAX_AGE", 30)),
        compress=bool(os.getenv("LOG_COMPRESS", True)),
        localTime=bool(os.getenv("LOG_LOCAL_TIME", True))
    )