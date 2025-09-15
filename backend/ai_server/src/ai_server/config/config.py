import yaml
from pathlib import Path
import hydra
from omegaconf import OmegaConf, DictConfig
from typing import Union, Dict, Any


class Config:
    """
    Configuration management class using Hydra for loading and direct file operations for saving.
    """

    def __init__(self):
        current_file = Path(__file__).resolve()

        config_candidates = [
            Path("config"),  # Relative to current working directory
            Path("../config"),
            Path("../../config"),
            Path("../../../config"),
            current_file.parent.parent.parent / "config"  # Based on file location
        ]

        self.config_path = None
        for candidate in config_candidates:
            if candidate.exists() and candidate.is_dir():
                self.config_path = candidate.resolve()
                break

        if self.config_path is None:
            self.config_path = Path("config").resolve()
            self.config_path.mkdir(parents=True, exist_ok=True)

        print(f"Using config path: {self.config_path}")

    def init(self):
        """
        Initialize the configuration management.
        This method is called by the main application to set up the configuration.
        """
        try:
            hydra.initialize(config_path="../../../config", version_base=None)
        except Exception as e:
            print(f"Hydra initialization failed: {e}")

    def get_config(self, name: str = "local") -> DictConfig:
        """
        Load and return the configuration for the given environment.
        """
        try:
            cfg = hydra.compose(config_name=name)
            OmegaConf.set_struct(cfg, False)
            return cfg
        except Exception as e:
            print(f"Configuration file '{name}.yaml' not found in {self.config_path}. Error: {e}")
            # If a file doesn't exist, return empty DictConfig
            return OmegaConf.create({})

    def set_config_with_dict(self, name: str, config_dict: Union[Dict[str, Any], DictConfig]) -> None:
        """
        Save configuration directly to YAML file.
        """
        # Convert DictConfig to regular dict if needed
        if isinstance(config_dict, DictConfig):
            config_dict = OmegaConf.to_object(config_dict)

        # Ensure config directory exists
        self.config_path.mkdir(parents=True, exist_ok=True)
        config_file_path = self.config_path / f"{name}.yaml"

        print(f"Saving config to: {config_file_path}")

        # Save to YAML file
        try:
            with open(config_file_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
            print(f"Config saved successfully to {config_file_path}")
        except Exception as e:
            print(f"Error saving config: {e}")
            raise

    def load_config_from_file(self, name: str) -> Dict[str, Any]:
        """
        Load configuration directly from YAML file (alternative to Hydra).
        """
        config_file_path = self.config_path / f"{name}.yaml"
        print(f"Loading config from: {config_file_path}")

        if not config_file_path.exists():
            print(f"Config file does not exist: {config_file_path}")
            return {}

        try:
            with open(config_file_path, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f) or {}
                print(f"Loaded config: {content}")
                return content
        except Exception as e:
            print(f"Error loading config: {e}")
            return {}

    def get_config_safe(self, name: str) -> Union[DictConfig, Dict[str, Any]]:
        """
        Get configuration with fallback to direct file loading if Hydra fails.
        """
        try:
            # Try Hydra first
            return self.get_config(name)
        except Exception as e:
            print(f"Hydra failed, trying direct file loading: {e}")
            # Fallback to direct file loading
            return self.load_config_from_file(name)
