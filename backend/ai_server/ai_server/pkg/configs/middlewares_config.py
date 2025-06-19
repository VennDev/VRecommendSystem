import os
from dataclasses import dataclass

@dataclass
class MiddlewareConfigResult:
    origins: list[str]
    credentials: bool
    methods: list[str]
    headers: list[str]

def get_middleware_config() -> MiddlewareConfigResult:
    return MiddlewareConfigResult(
        origins=os.getenv("ORIGINS", "*").split(","),
        credentials=os.getenv("CREDENTIALS", "true").lower() == "true",
        methods=os.getenv("METHODS", "GET, POST, PUT, DELETE, OPTIONS").split(","),
        headers=os.getenv("HEADERS", "Content-Type, Authorization").split(",")
    )