import docker

class ContainerPool:
    def __init__(self):
        self.pool = {}
        self.client = docker.from_env()

    def get_container(self, func_id, language, code):
        if func_id not in self.pool:
            # Map language to correct image name
            image_map = {
                "python": "python-base",
                "javascript": "js-base"  # Use "js-base" instead of "javascript-base"
            }
            image = image_map.get(language, f"{language}-base")  # Fallback for unknown languages
            self.pool[func_id] = self.client.containers.create(image, command="tail -f /dev/null")
            self.pool[func_id].start()
        return self.pool[func_id]