from fastapi import FastAPI

from ai_server.routers import public_routers, private_routers


def init(app: FastAPI) -> None:
    """
    Initialize the routers.
    This function is called by the main application to set up the routers.
    """

    app.include_router(public_routers.router, prefix="/api/v1", tags=["public"])
    app.include_router(private_routers.router, prefix="/api/v1", tags=["private"])
