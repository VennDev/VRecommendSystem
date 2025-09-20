class MetricsService:
    def __init__(self):
        self.metrics = {}

    def record_metric(self, name, value):
        if name not in self.metrics:
            self.metrics[name] = []
        self.metrics[name].append(value)

    def get_metrics(self, name):
        return self.metrics.get(name, [])
