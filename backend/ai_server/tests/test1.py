import unittest

from ai_server.services.model_service import ModelService

if __name__ == '__main__':
    service = ModelService()
    config = service.create_model_config(
        model_id="my_als_model",
        algorithm="als",
        hyperparameters={"factors": 100, "regularization": 0.01},
        dataset_path="data/ecommerce_clickstream_transactions.csv"
    )
    result = service.train_model("my_als_model")
    predictions = service.predict_with_model("my_als_model", "1", top_k=10)
    print("Predictions for user 1:", predictions)
