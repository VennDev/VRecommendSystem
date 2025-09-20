from fastapi import FastAPI

from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import make_asgi_app


def init(app: FastAPI) -> None:
    """
    Initialize Prometheus monitoring for the FastAPI app.
    This function sets up the Prometheus ASGI app and integrates it with the FastAPI app.
    """

    # Create the Prometheus ASGI app
    prometheus_app = make_asgi_app()

    # Mount the Prometheus app at the /metrics endpoint
    app.mount("/metrics", prometheus_app)

    # Instrument the FastAPI app to collect metrics
    Instrumentator().instrument(app).expose(app)
