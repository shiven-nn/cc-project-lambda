import docker
import json
import time
import logging
import asyncio
import shlex
from .container_pool import ContainerPool

logger = logging.getLogger(__name__)

async def execute_function(func_data, payload):
    client = docker.from_env()
    pool = ContainerPool(client)
    
    # Change this line in execution.py:
    image = "python-base:latest" if func_data['language'] == "python" else "js-base:latest"
    container = None
    start_time = time.time()
    errors = None
    resources = {"cpu": "2.0 cores", "memory": "1Gi"}
    
    try:
        runtime = func_data.get('runtime', 'runc')
        logger.info(f"Acquiring container for image={image}, runtime={runtime}")
        container = pool.acquire(
            image,
            func_data['timeout'],
            runtime=runtime,
            code=func_data['code'],
            language=func_data['language']
        )
        
        container.reload()
        if container.status != 'running':
            logs = container.logs().decode() if container.logs() else "No logs available"
            raise docker.errors.APIError(f"Container {container.id} is not running, status: {container.status}, logs: {logs}")
        
        # Prepare command and payload
        code = func_data['code']
        input_data = json.dumps(payload)
        input_data_escaped = shlex.quote(input_data)
        if func_data['language'] == "python":
            cmd = ["python", "-c", code]
        else:
            cmd = ["node", "-e", code]
        exec_cmd = f"echo {input_data_escaped} | {' '.join([shlex.quote(c) for c in cmd])}"
        logger.info(f"Executing command: {exec_cmd}")
        
        async def run_exec():
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                lambda: container.exec_run(
                    ["/bin/sh", "-c", exec_cmd],
                    stdout=True,
                    stderr=True,
                    user="nobody",
                    environment={"TIMEOUT": str(func_data['timeout'])}
                )
            )
        
        try:
            output = await asyncio.wait_for(run_exec(), timeout=func_data['timeout'])
        except asyncio.TimeoutError:
            errors = "Execution timed out"
            logger.warning(f"Timeout for container {container.id}")
            container.stop(timeout=15)
            return None, time.time() - start_time, errors, resources
        
        result = output.output.decode()
        response_time = time.time() - start_time
        
        if output.exit_code != 0:
            errors = result
            result = None
            logger.error(f"Command failed in container {container.id}: {errors}")
            
        return result, response_time, errors, resources
        
    except docker.errors.APIError as e:
        logger.error(f"Execution failed: {str(e)}")
        errors = str(e)
        return None, time.time() - start_time, errors, resources
        
    finally:
        if container:
            logger.info(f"Releasing container {container.id}")
            pool.release(container)