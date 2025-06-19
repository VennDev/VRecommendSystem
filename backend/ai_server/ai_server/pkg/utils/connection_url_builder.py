import os

def build_connection_url(name: str) -> str:
    if name == "postgres":
        return (
            f"postgresql://{os.getenv('DATABASE_USER')}:{os.getenv('DATABASE_PASSWORD')}"
            f"@{os.getenv('DATABASE_HOST')}:{os.getenv('DATABASE_PORT')}/{os.getenv('DATABASE_NAME')}?"
            f"sslmode={os.getenv('DATABASE_SSL_MODE', 'prefer')}"
        )
    elif name == "mysql":
        print(os.getenv('DATABASE_PORT'))
        return (
            f"mysql+mysqlconnector://{os.getenv('DATABASE_USER')}:{os.getenv('DATABASE_PASSWORD')}"
            f"@{os.getenv('DATABASE_HOST')}:{os.getenv('DATABASE_PORT')}/{os.getenv('DATABASE_NAME')}"
        )
    elif name == "redis":
        return f"redis://{os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT')}"
    elif name == "fastapi":
        return f"http://{os.getenv('SERVER_HOST')}:{os.getenv('SERVER_PORT')}"
    else:
        raise ValueError(f"Connection name '{name}' is not supported.")
