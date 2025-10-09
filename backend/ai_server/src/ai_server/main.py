import loguru
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ai_server.initialize import (
    logger, scheduler, config, routers, prometheus
)
from ai_server.middlewares import verify_authentication


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

    cfg = config.Config().get_config()

    # Create FastAPI app
    app = FastAPI(
        title=cfg.name,
        description=cfg.description,
        version=cfg.version,
    )

    # Set all CORS enabled origins
    cfg_cors = cfg.middleware.cors
    app.add_middleware(
        CORSMiddleware,
        allow_credentials=cfg_cors.credentials,
        allow_origins=cfg_cors.origins,
        allow_methods=cfg_cors.methods,
        allow_headers=cfg_cors.headers,
    )

    # Add authentication middleware
    app.middleware("http")(verify_authentication)
    loguru.logger.info("Authentication middleware initialized.")

    # Initialize routers
    routers.init(app)

    # Initialize prometheus
    prometheus.init(app)

    # Run the app with Uvicorn
    uvicorn.run(app, host=cfg.host, port=cfg.port)
