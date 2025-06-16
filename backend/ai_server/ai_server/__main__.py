import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .pkg.configs.middlewares_config import get_middleware_config
from .pkg.configs.server_config import get_server_config

if __name__ == "__main__":
    sv_config = get_server_config()
    mw_config = get_middleware_config() 

    app = FastAPI(
        title=sv_config.name, 
        version=sv_config.version, 
        description=sv_config.description)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=mw_config.origins,
        allow_credentials=mw_config.credentials,
        allow_methods=mw_config.methods,
        allow_headers=mw_config.headers,
    )

    app.add_api_route("/", lambda: {"message": "Welcome to the AI Server!"})

    uvicorn.run(app, host=sv_config.host, port=sv_config.port)