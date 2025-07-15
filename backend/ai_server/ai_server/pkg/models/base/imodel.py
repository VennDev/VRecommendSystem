from abc import ABC, abstractmethod


class IModel(ABC):
    @abstractmethod
    def predict(self, input_data):
        """
        Predicts the output based on the input data.
        :param input_data: The data to be processed by the model.
        :return: The predicted output.
        """
        pass
    
    @abstractmethod
    def train(self, training_data):
        """
        Trains the model using the provided training data.
        :param training_data: The data used to train the model.
        """
        pass
    
    @abstractmethod
    def save(self, file_path):
        """
        Saves the model to a specified file path.
        :param file_path: The path where the model should be saved.
        """
        pass
    
    @abstractmethod
    def load(self, file_path):
        """
        Loads the model from a specified file path.
        :param file_path: The path where the model is saved.
        """
        pass
    
    @abstractmethod
    def evaluate(self, test_data):
        """
        Evaluates the model performance on test data.
        :param test_data: The data used for evaluation.
        :return: Evaluation metrics.
        """
        pass
    
    @abstractmethod
    def get_model_info(self):
        """
        Returns information about the model.
        :return: Dictionary containing model information.
        """
        pass
