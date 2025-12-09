import loguru
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ai_server.initialize import config, logger, prometheus, routers, scheduler
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

    # Get CORS configuration from config file
    cors_config = cfg.middleware.cors if hasattr(cfg, "middleware") and hasattr(cfg.middleware, "cors") else {}

    # Default CORS settings if not provided in config
    default_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
    default_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
    default_headers = ["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin", "Cookie"]

    allow_credentials = cors_config.get("allow_credentials", True) if cors_config else True
    allow_origins = cors_config.get("allow_origins", default_origins) if cors_config else default_origins
    allow_methods = cors_config.get("allow_methods", default_methods) if cors_config else default_methods
    allow_headers = cors_config.get("allow_headers", default_headers) if cors_config else default_headers
    expose_headers = cors_config.get("expose_headers", ["*"]) if cors_config else ["*"]

    loguru.logger.info(f"CORS Configuration - Origins: {allow_origins}")

    # Set all CORS enabled origins
    app.add_middleware(
        CORSMiddleware,
        allow_credentials=allow_credentials,
        allow_origins=allow_origins,
        allow_methods=allow_methods,
        allow_headers=allow_headers,
        expose_headers=expose_headers,
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


if __name__ == "__main__":
    main()
