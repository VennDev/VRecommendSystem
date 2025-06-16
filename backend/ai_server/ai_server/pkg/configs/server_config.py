import os
from dataclasses import dataclass

@dataclass
class ServerConfigResult:
    name: str
    version: str
    description: str

def get_server_config() -> ServerConfigResult:
    return ServerConfigResult(
        name=os.getenv("SERVER_NAME", "AI Server"),
        version=os.getenv("SERVER_VERSION", "1.0.0"),
        description=os.getenv("SERVER_DESCRIPTION", "AI Server"),
    )