import os

def build_connection_url(name: str) -> str:
    if name == "postgres":
        return (
            f"postgresql://{os.getenv('DATABASE_USER')}:{os.getenv('DATABASE_PASSWORD')}"
            f"@{os.getenv('DATABASE_HOST')}:{os.getenv('DATABASE_PORT')}/{os.getenv('DATABASE_NAME')}?"
            f"sslmode={os.getenv('DATABASE_SSL_MODE', 'prefer')}"
        )
    elif name == "mysql":
        return (
            f"mysql+mysqlconnector://{os.getenv('DATABASE_USER')}:{os.getenv('DATABASE_PASSWORD')}"
            f"@{os.getenv('DATABASE_HOST')}:{os.getenv('DATABASE_PORT')}/{os.getenv('DATABASE_NAME')}"
        )
    elif name == "redis":
        return (
            f"redis://{os.getenv('REDIS_USERNAME')}:{os.getenv('REDIS_PASSWORD')}"
            f"@{os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT')}/{os.getenv('REDIS_DB')}"
        )
    elif name == "fastapi":
        return f"http://{os.getenv('SERVER_HOST')}:{os.getenv('SERVER_PORT')}"
    elif name == "kafka":
        bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        topics = os.getenv("KAFKA_TOPICS", "topic1,topic2")
        return f"kafka://{bootstrap_servers}?topics={topics}"
    elif name == "spark":
        master = os.getenv("SPARK_MASTER", "local[*]")
        app_name = os.getenv("SPARK_APP_NAME", "MySparkApp")
        return f"spark://{master}?appName={app_name}"
    else:
        raise ValueError(f"Connection name '{name}' is not supported.")
