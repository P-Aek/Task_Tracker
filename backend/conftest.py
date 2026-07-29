import pytest
from fastapi.testclient import TestClient

import main


@pytest.fixture
def client(tmp_path, monkeypatch):
    """
    Give every test its own isolated task.json file (via tmp_path) so tests
    never touch the real ./task.json and never leak state between tests.
    """
    test_file = tmp_path / "task.json"

    # main.py's route functions read the module-level `Task_File` global at
    # call time, so patching the attribute on the module is enough to
    # redirect all file I/O to our temp file.
    monkeypatch.setattr(main, "Task_File", str(test_file))

    # Using TestClient as a context manager triggers the `lifespan` handler,
    # which is what actually creates the (empty) task.json file.
    with TestClient(main.app) as c:
        yield c


@pytest.fixture
def created_task(client):
    """Helper fixture: creates one task and returns its JSON body."""
    resp = client.post("/task", json={"description": "Buy milk"})
    assert resp.status_code == 200
    return resp.json()