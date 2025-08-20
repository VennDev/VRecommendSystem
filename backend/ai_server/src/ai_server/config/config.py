import hydra
from omegaconf import DictConfig


class Config:
    """
    Configuration management class using Hydra.
    """

    def init(self):
        """
        Initialize the configuration management.
        This method is called by the main application to set up the configuration.
        """
        hydra.initialize(config_path="../../../config", version_base=None)

    def get_config(self, name: str = "local") -> DictConfig:
        """
        Load and return the configuration for the given environment.
        """
        cfg = hydra.compose(config_name=name)
        return cfg
