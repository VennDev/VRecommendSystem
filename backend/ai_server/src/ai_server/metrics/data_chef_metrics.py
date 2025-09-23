from prometheus_client import Gauge

TOTAL_DATA_CHEFS = Gauge(
    'total_data_chefs',
    'Total number of data chefs created'
)
