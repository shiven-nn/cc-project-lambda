import time
 
class Metrics:
    def __init__(self):
        self.store = []

    def record(self, func_id, response_time, errors, resources):
        self.store.append({
            "func_id": func_id,
            "response_time": response_time,
            "errors": errors,
            "resources": resources,
            "timestamp": time.time()
        })

    def get_metrics(self, func_id=None):
        if func_id:
            return [m for m in self.store if m["func_id"] == func_id]
        return self.store