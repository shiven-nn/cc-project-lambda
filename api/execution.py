import docker
import asyncio
import tarfile
import io
import json
import logging
from .container_pool import ContainerPool

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

pool = ContainerPool()
client = docker.from_env()

async def execute_function(func, payload):
    container = pool.get_container(func.id, func.language, func.code)
    try:
        start_time = asyncio.get_event_loop().time()
        
        if func.language == "python":
            temp_file = "/tmp/script.py"
            code_bytes = func.code.encode('utf-8')
            tar_stream = io.BytesIO()
            with tarfile.open(fileobj=tar_stream, mode="w") as tar:
                tarinfo = tarfile.TarInfo(name="script.py")
                tarinfo.size = len(code_bytes)
                tar.addfile(tarinfo, io.BytesIO(code_bytes))
            tar_stream.seek(0)
            logger.info(f"Writing code to {temp_file} in container {container.id}")
            container.put_archive("/tmp", tar_stream)
            cmd = f"python {temp_file}"
        elif func.language == "javascript":
            temp_file = "/tmp/script.js"
            code_bytes = func.code.encode('utf-8')
            tar_stream = io.BytesIO()
            with tarfile.open(fileobj=tar_stream, mode="w") as tar:
                tarinfo = tarfile.TarInfo(name="script.js")
                tarinfo.size = len(code_bytes)
                tar.addfile(tarinfo, io.BytesIO(code_bytes))
            tar_stream.seek(0)
            logger.info(f"Writing code to {temp_file} in container {container.id}")
            container.put_archive("/tmp", tar_stream)
            cmd = f"node {temp_file}"
        else:
            raise ValueError(f"Unsupported language: {func.language}")
        
        logger.info(f"Executing command: {cmd}")
        # Pass payload as JSON string to stdin
        payload_json = json.dumps(payload) if payload else "{}"
        
        # Create exec instance with stdin enabled
        exec_id = container.client.api.exec_create(
            container.id,
            cmd,
            stdin=True,
            stdout=True,
            stderr=True,
            environment={"PYTHONUNBUFFERED": "1"}
        )["Id"]
        
        # Start execution, send payload, and capture output
        logger.info(f"Sending payload: {payload_json}")
        socket = container.client.api.exec_start(exec_id, socket=True, detach=False)
        socket._sock.send(payload_json.encode('utf-8'))  # Write to stdin
        socket._sock.shutdown(1)  # Close stdin (SHUT_WR)
        
        # Read output from the socket, stripping Docker stream headers
        output = b""
        while True:
            data = socket._sock.recv(4096)
            if not data:
                break
            # Parse Docker stream header (8 bytes: type[1], reserved[3], length[4])
            while len(data) >= 8:
                stream_type = data[0]  # 1 = stdout, 2 = stderr
                length = int.from_bytes(data[4:8], "big")  # Payload length
                if len(data) < 8 + length:
                    break  # Wait for more data if incomplete
                payload_data = data[8:8 + length]
                if stream_type in (1, 2):  # stdout or stderr
                    output += payload_data
                data = data[8 + length:]  # Move to next chunk
        output = output.decode('utf-8')
        socket.close()  # Fully close the socket
        
        # Wait for execution to complete with a timeout
        async def wait_for_exec():
            while True:
                result = container.client.api.exec_inspect(exec_id)
                if not result["Running"]:
                    return result
                await asyncio.sleep(0.1)
        
        exec_result = await asyncio.wait_for(wait_for_exec(), timeout=func.timeout or 30)
        response_time = asyncio.get_event_loop().time() - start_time
        
        logger.info(f"Execution completed with exit code: {exec_result['ExitCode']}, output: {output}")
        if exec_result["ExitCode"] != 0:
            return output, response_time, f"Execution failed with exit code {exec_result['ExitCode']}: {output}", {"cpu": "unknown"}
        return output, response_time, None, {"cpu": "unknown"}
    except asyncio.TimeoutError:
        container.kill()
        response_time = asyncio.get_event_loop().time() - start_time
        logger.error("Execution timed out")
        return "Timeout", response_time, "timeout", {"cpu": "unknown"}
    except Exception as e:
        response_time = asyncio.get_event_loop().time() - start_time
        error_msg = f"Execution error: {str(e)}"
        logger.error(error_msg)
        return "Error", response_time, error_msg, {"cpu": "unknown"}