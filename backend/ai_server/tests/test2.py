import pandas as pd
from ai_server.services.model_service import ModelService

if __name__ == "__main__":
    """Example of how to use the enhanced ModelService."""
    # Create service
    service = ModelService()

    # Example 1: Train model directly from DataFrames
    interaction_data = pd.DataFrame({
        'user_id': ['u1', 'u1', 'u2', 'u2'],
        'item_id': ['i1', 'i2', 'i1', 'i3'],
        'rating': [5, 4, 3, 5]
    })

    result = service.train_no_save_model(
        model_id='ncf_example',
        model_name='ncf_example',
        message='Training NCF model with interaction data',
        algorithm='ncf',
        interaction_data=interaction_data,
        hyperparameters={'factors': 50, 'iterations': 10},
        training_time=3600,
    )

    predict = service.predict_recommendations(
        model_id='ncf_example',
        user_id='u1',
        top_k=5
    )
    print("Predictions for user 'u1':", predict)

    # # Example 2: Register datasets and use them later
    # service.register_dataset('my_interactions', interaction_data)
    #
    # config = service.create_model_config(
    #     model_id='als_cached',
    #     algorithm='als',
    #     dataset_source='my_interactions',  # Reference to cached dataset
    #     hyperparameters={'factors': 50}
    # )
    #
    # # Example 3: Mixed usage - some data from files, some from DataFrames
    # item_features = pd.DataFrame({
    #     'item_id': ['i1', 'i2', 'i3'],
    #     'category': ['A', 'B', 'A'],
    #     'price': [10.0, 15.0, 12.0]
    # })
    #
    # config = service.create_model_config(
    #     model_id='feature_mixed',
    #     algorithm='feature',
    #     dataset_source='data/interactions.csv',  # File path
    #     item_features_source=item_features,  # DataFrame
    #     hyperparameters={'similarity_metric': 'cosine'}
    # )
