from prometheus_client import Counter

TOTAL_DATA_CHEFS = Counter(
    'total_data_chefs',
    'Total number of data chefs created'
)
