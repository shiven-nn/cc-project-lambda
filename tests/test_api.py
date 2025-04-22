import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_create_function():
    response = client.post("/functions/", json={"name": "test", "language": "python", "code": "print('hello')", "timeout": 30})
    assert response.status_code == 200
    assert response.json()["name"] == "test"