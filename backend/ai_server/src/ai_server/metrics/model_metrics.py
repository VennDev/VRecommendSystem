from prometheus_client import Gauge

TOTAL_ACTIVATING_MODELS = Gauge(
    'total_activating_models',
    'Total number of models being activated'
)

TOTAL_TRAINING_MODELS = Gauge(
    'total_training_models',
    'Total number of models being trained'
)
