from ai_server.models.base.imodel import IModel
import pandas as pd

class BaseModel(IModel):

    def __init__(self, name_model: str = "base_model", verbose: bool = False):
        """
        Initialize the base model with optional data.

        :param name_model: Name of the model.
        :param verbose: If True, enables verbose output.
        """
        self.name_model = name_model
        self.verbose = verbose

    def fit(self, train_data: pd.DataFrame, **kwargs) -> None:
        """
        Train the model on the given training data.

        :param train_data: DataFrame containing training data.
        :param kwargs: Additional keyword arguments for model fitting.
        """
        if self.verbose:
            print(f"Fitting model {self.name_model} with training data of shape {train_data.shape}")
        # Implement fitting logic here
        pass
