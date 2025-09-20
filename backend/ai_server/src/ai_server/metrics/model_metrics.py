from prometheus_client import Counter

TOTAL_ACTIVATING_MODELS = Counter(
    'total_activating_models',
    'Total number of models being activated'
)

TOTAL_TRAINING_MODELS = Counter(
    'total_training_models',
    'Total number of models being trained'
)
