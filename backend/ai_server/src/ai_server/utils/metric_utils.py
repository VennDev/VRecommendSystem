def get_metric_value(counter):
    for metric in counter.collect():
        for sample in metric.samples:
            return sample.value
    return None
