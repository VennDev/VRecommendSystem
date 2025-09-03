from ai_server.services.model_service import ModelService

if __name__ == "__main__":
    service = ModelService()

    service.initialize_training(
        model_id="me_model",
        model_name="My Recommendation Model",
        algorithm="als",
        message="Training with incremental data"
    )

    service.save_model("me_model")
