import loguru
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from ai_server.initialize import (
    logger, scheduler, config, routers, prometheus
)
from ai_server.middlewares import verify_authentication


def main():
    """
    Main entry point for the application.
    """

    # Load environment variables from .env file
    load_dotenv()
    print("Loading environment variables...")

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

    # Get host and port from environment variables or config
    import os
    host = os.getenv("HOST", cfg.host if hasattr(cfg, 'host') else "0.0.0.0")
    port = int(os.getenv("PORT", cfg.port if hasattr(cfg, 'port') else 9999))

    loguru.logger.info(f"Starting AI Server on {host}:{port}")

    # Create FastAPI app
    app = FastAPI(
        title=cfg.name if hasattr(cfg, 'name') else "AI Server",
        description=cfg.description if hasattr(cfg, 'description') else "AI Recommendation Server",
        version=cfg.version if hasattr(cfg, 'version') else "1.0.0",
    )

    # Set all CORS enabled origins
    cfg_cors = cfg.middleware.cors if hasattr(cfg, 'middleware') else None
    if cfg_cors:
        app.add_middleware(
            CORSMiddleware,
            allow_credentials=cfg_cors.credentials,
            allow_origins=cfg_cors.origins,
            allow_methods=cfg_cors.methods,
            allow_headers=cfg_cors.headers,
        )
    else:
        # Default CORS settings
        app.add_middleware(
            CORSMiddleware,
            allow_credentials=True,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Add authentication middleware
    app.middleware("http")(verify_authentication)
    loguru.logger.info("Authentication middleware initialized.")

    # Initialize routers
    routers.init(app)

    # Initialize prometheus
    prometheus.init(app)

    # Run the app with Uvicorn
    uvicorn.run(app, host=host, port=port)
