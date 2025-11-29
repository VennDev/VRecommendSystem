import loguru
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ai_server.initialize import config, logger, prometheus, routers, scheduler
from ai_server.middlewares import verify_authentication

# Allowed origins for CORS with credentials
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://192.168.2.12:5173",
    "http://localhost:3456",
    "http://127.0.0.1:3456",
    "http://192.168.2.12:3456",
    "http://localhost:9999",
    "http://127.0.0.1:9999",
    "http://192.168.2.12:9999",
]


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

    host = os.getenv("HOST", cfg.host if hasattr(cfg, "host") else "0.0.0.0")
    port = int(os.getenv("PORT", cfg.port if hasattr(cfg, "port") else 9999))

    loguru.logger.info(f"Starting AI Server on {host}:{port}")

    # Create FastAPI app
    app = FastAPI(
        title=cfg.name if hasattr(cfg, "name") else "AI Server",
        description=cfg.description
        if hasattr(cfg, "description")
        else "AI Recommendation Server",
        version=cfg.version if hasattr(cfg, "version") else "1.0.0",
    )

    # Set all CORS enabled origins
    # Always use explicit origins list for credentials support
    app.add_middleware(
        CORSMiddleware,
        allow_credentials=True,
        allow_origins=ALLOWED_ORIGINS,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=[
            "Content-Type",
            "Authorization",
            "X-Requested-With",
            "Accept",
            "Origin",
            "Cookie",
        ],
        expose_headers=["*"],
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
