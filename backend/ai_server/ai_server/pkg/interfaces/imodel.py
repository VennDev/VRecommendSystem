from abc import ABC, abstractmethod

class IModel(ABC):
    @abstractmethod
    def train(self, data):
        """
        Train the model with the provided data.
        
        :param data: Training data
        """
        pass
    
    @abstractmethod
    def predict(self, input_data):
        """
        Make predictions using the model.
        
        :param input_data: Data to make predictions on
        :return: Predictions
        """
        pass
    
    @abstractmethod
    def evaluate(self, test_data):
        """
        Evaluate the model on the provided test data.
        
        :param test_data: Data to evaluate the model
        :return: Evaluation metrics
        """
        pass
    
    @abstractmethod
    def save(self, file_path):
        """
        Save the model to a file.
        
        :param file_path: Path to save the model
        """
        pass
    
    @abstractmethod
    def load(self, file_path):
        """
        Load the model from a file.
        
        :param file_path: Path to load the model from
        """
        pass
    
    @abstractmethod
    def get_model_info(self):
        """
        Get information about the model.
        
        :return: Dictionary containing model information
        """
        pass 