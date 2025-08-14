import hydra
from omegaconf import DictConfig


class Config:
    """
    Configuration management class using Hydra.
    """

    def get_config(self, name: str = "local") -> DictConfig:
        """
        Load and return the configuration for the given environment.
        """
        hydra.initialize(config_path="../../../config", version_base=None)
        cfg = hydra.compose(config_name=name)
        return cfg
