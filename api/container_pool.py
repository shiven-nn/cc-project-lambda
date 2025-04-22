import docker
import time
import logging
from docker.errors import APIError

logger = logging.getLogger(__name__)

class ContainerPool:
    def __init__(self, client):
        self.client = client
        self.pool = []
        
    def acquire(self, image, timeout, runtime='runc', code=None, language='python', max_retries=2):
        logger.info(f"Preparing container with image={image}, runtime={runtime}, language={language}")
        
        for attempt in range(max_retries + 1):
            logger.info(f"Attempt {attempt + 1}/{max_retries + 1}: Creating container with image={image}, runtime={runtime}")
            try:
                # Use a non-exiting command to keep the container running
                command = ["tail", "-f", "/dev/null"]
                container = self.client.containers.create(
                    image,
                    command=command,
                    detach=True,
                    mem_limit='1g',
                    nano_cpus=int(2.0 * 1e9),
                    runtime=runtime,
                    init=True,
                    stdin_open=True,
                    user="nobody"
                )
                container.start()
                logger.info(f"Started container {container.id}")
                self.pool.append(container)
                return container
            except APIError as e:
                logger.error(f"Failed to create/start container: {str(e)}")
                if attempt == max_retries:
                    raise
                time.sleep(1)
        
    def release(self, container):
        try:
            logger.info(f"Stopping container {container.id}")
            container.stop(timeout=15)
            container.remove()
            self.pool.remove(container)
        except APIError as e:
            logger.error(f"Failed to release container {container.id}: {str(e)}")