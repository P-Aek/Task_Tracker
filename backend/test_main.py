"""
Automation tests for the Task Tracker CLI FastAPI app.

Run with:
    pytest -v

Each test uses the `client` fixture from conftest.py, which points the app
at a fresh, isolated task.json (via monkeypatch + tmp_path) so tests never
interfere with each other or with your real data file.
"""
import json
import time
import uuid

import pytest


# ---------------------------------------------------------------------------
# POST /task - create task
# ---------------------------------------------------------------------------

class TestCreateTask:
    def test_create_task_success(self, client):
        resp = client.post("/task", json={"description": "Buy milk"})
        assert resp.status_code == 200

        body = resp.json()
        assert body["description"] == "Buy milk"
        assert body["status"] == "to-do"          # default status
        assert body["createdAt"] == body["updatedAt"]

        # id must be a valid uuid4 string
        uuid.UUID(body["id"])  # raises ValueError if invalid

    def test_create_task_with_explicit_status(self, client):
        resp = client.post(
            "/task", json={"description": "Write report", "status": "in-progress"}
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "in-progress"

    def test_create_task_missing_description_fails(self, client):
        resp = client.post("/task", json={})
        assert resp.status_code == 422

    def test_create_task_invalid_status_fails(self, client):
        resp = client.post(
            "/task", json={"description": "bad status", "status": "not-a-status"}
        )
        assert resp.status_code == 422

    def test_create_task_persists_to_file(self, client):
        resp = client.post("/task", json={"description": "Persisted task"})
        task_id = resp.json()["id"]

        # read straight from the (patched) Task_File to make sure it was
        # actually written to disk, not just held in memory
        import main
        with open(main.Task_File) as f:
            saved = json.load(f)

        assert len(saved) == 1
        assert saved[0]["id"] == task_id
        assert saved[0]["description"] == "Persisted task"

    def test_create_multiple_tasks_each_get_unique_id(self, client):
        ids = set()
        for i in range(5):
            resp = client.post("/task", json={"description": f"Task {i}"})
            ids.add(resp.json()["id"])
        assert len(ids) == 5


# ---------------------------------------------------------------------------
# GET /tasks - list & filter
# ---------------------------------------------------------------------------

class TestGetTasks:
    def test_get_tasks_empty_initially(self, client):
        resp = client.get("/tasks")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_get_tasks_returns_created_tasks(self, client):
        client.post("/task", json={"description": "Task A"})
        client.post("/task", json={"description": "Task B"})

        resp = client.get("/tasks")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body) == 2
        descriptions = {t["description"] for t in body}
        assert descriptions == {"Task A", "Task B"}

    def test_filter_tasks_by_status(self, client):
        client.post("/task", json={"description": "Todo task"})  # default to-do
        client.post(
            "/task", json={"description": "In progress task", "status": "in-progress"}
        )
        client.post("/task", json={"description": "Done task", "status": "done"})

        resp = client.get("/tasks", params={"status": "in-progress"})
        assert resp.status_code == 200
        body = resp.json()
        assert len(body) == 1
        assert body[0]["description"] == "In progress task"

    def test_filter_tasks_by_status_no_match_returns_empty(self, client):
        client.post("/task", json={"description": "Todo task"})
        resp = client.get("/tasks", params={"status": "done"})
        assert resp.status_code == 200
        assert resp.json() == []

    def test_filter_tasks_invalid_status_fails(self, client):
        resp = client.get("/tasks", params={"status": "bogus"})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# PATCH /task/{id}/mark-in-progress and /mark-done
# ---------------------------------------------------------------------------

class TestUpdateTaskStatus:
    def test_mark_in_progress(self, client, created_task):
        task_id = created_task["id"]
        time.sleep(0.001)  # ensure updatedAt timestamp differs from createdAt

        resp = client.patch(f"/task/{task_id}/mark-in-progress")
        assert resp.status_code == 200

        body = resp.json()
        assert body["id"] == task_id
        assert body["status"] == "in-progress"
        assert body["createdAt"] == created_task["createdAt"]  # unchanged
        assert body["updatedAt"] != created_task["updatedAt"]  # changed

    def test_mark_done(self, client, created_task):
        task_id = created_task["id"]

        resp = client.patch(f"/task/{task_id}/mark-done")
        assert resp.status_code == 200
        assert resp.json()["status"] == "done"

    def test_mark_status_persists(self, client, created_task):
        task_id = created_task["id"]
        client.patch(f"/task/{task_id}/mark-done")

        resp = client.get("/tasks")
        body = resp.json()
        assert body[0]["status"] == "done"

    def test_mark_in_progress_nonexistent_id_404(self, client):
        resp = client.patch(f"/task/{uuid.uuid4()}/mark-in-progress")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Task not found"

    def test_mark_done_nonexistent_id_404(self, client):
        resp = client.patch(f"/task/{uuid.uuid4()}/mark-done")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Task not found"

    def test_marking_one_task_does_not_affect_others(self, client):
        r1 = client.post("/task", json={"description": "Task 1"}).json()
        r2 = client.post("/task", json={"description": "Task 2"}).json()

        client.patch(f"/task/{r1['id']}/mark-done")

        resp = client.get("/tasks")
        body = {t["id"]: t["status"] for t in resp.json()}
        assert body[r1["id"]] == "done"
        assert body[r2["id"]] == "to-do"


# ---------------------------------------------------------------------------
# DELETE /task/{id}
# ---------------------------------------------------------------------------

class TestDeleteTask:
    def test_delete_task_success(self, client, created_task):
        task_id = created_task["id"]

        resp = client.delete(f"/task/{task_id}")
        assert resp.status_code == 200
        assert resp.json() == []  # no tasks left

    def test_delete_task_removes_only_target(self, client):
        r1 = client.post("/task", json={"description": "Keep me"}).json()
        r2 = client.post("/task", json={"description": "Delete me"}).json()

        resp = client.delete(f"/task/{r2['id']}")
        assert resp.status_code == 200

        remaining_ids = {t["id"] for t in resp.json()}
        assert remaining_ids == {r1["id"]}

    def test_delete_task_persists(self, client, created_task):
        task_id = created_task["id"]
        client.delete(f"/task/{task_id}")

        resp = client.get("/tasks")
        assert resp.json() == []

    def test_delete_nonexistent_task_404(self, client):
        resp = client.delete(f"/task/{uuid.uuid4()}")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Task not found"

    def test_delete_same_task_twice_second_time_404(self, client, created_task):
        task_id = created_task["id"]
        assert client.delete(f"/task/{task_id}").status_code == 200
        assert client.delete(f"/task/{task_id}").status_code == 404


# ---------------------------------------------------------------------------
# End-to-end workflow
# ---------------------------------------------------------------------------

class TestFullWorkflow:
    def test_full_task_lifecycle(self, client):
        # 1. Start empty
        assert client.get("/tasks").json() == []

        # 2. Create
        created = client.post("/task", json={"description": "Write tests"}).json()
        task_id = created["id"]
        assert created["status"] == "to-do"

        # 3. Appears in listing
        assert len(client.get("/tasks").json()) == 1

        # 4. Move to in-progress
        in_progress = client.patch(f"/task/{task_id}/mark-in-progress").json()
        assert in_progress["status"] == "in-progress"
        assert client.get("/tasks", params={"status": "in-progress"}).json()[0]["id"] == task_id

        # 5. Mark done
        done = client.patch(f"/task/{task_id}/mark-done").json()
        assert done["status"] == "done"
        assert client.get("/tasks", params={"status": "to-do"}).json() == []

        # 6. Delete
        resp = client.delete(f"/task/{task_id}")
        assert resp.status_code == 200
        assert resp.json() == []
        assert client.get("/tasks").json() == []