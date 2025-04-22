import time
from collections import defaultdict

class Metrics:
    def __init__(self):
        self.data = defaultdict(list)

    def record(self, route: str, response_time: float, errors: str, resources: dict):
        self.data[route].append({
            "timestamp": time.time(),
            "response_time": response_time,
            "errors": errors,
            "resources": resources
        })

    def get_metrics(self, route: str = None):
        if route:
            return self.data.get(route, [])
        return [entry for route_data in self.data.values() for entry in route_data]