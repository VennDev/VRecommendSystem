from ai_server.config.config import Config
from ai_server.services.data_chef_service import DataChefService

if __name__ == "__main__":
    Config().init()

    service = DataChefService()
    for v in service.cook("data_a"):
        print(v)
