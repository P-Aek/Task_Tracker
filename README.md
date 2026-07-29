# Task Tracker CLI (FastAPI)

A simple REST API for tracking and managing your tasks — built as a solution to the
[Task Tracker](https://roadmap.sh/projects/task-tracker) project on
[roadmap.sh](https://roadmap.sh/), implemented with **FastAPI** instead of a plain CLI.

Tasks are stored in a local JSON file (`task.json`), with no external database required.

## Features

- Create a task
- List all tasks
- List tasks filtered by status (`to-do`, `in-progress`, `done`)
- Mark a task as **in-progress**
- Mark a task as **done**
- Delete a task
- Automatic `id`, `createdAt`, `updatedAt` fields for every task
- Interactive API docs via Swagger UI
- Automated test suite (`pytest`)

## Tech Stack

- [Python 3](https://www.python.org/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Pydantic](https://docs.pydantic.dev/)
- [Uvicorn](https://www.uvicorn.org/) (ASGI server)
- [pytest](https://docs.pytest.org/) + [httpx](https://www.python-httpx.org/) for automated tests
- JSON file storage (no database)

## Project Structure

```
.
├── main.py           # FastAPI app: routes, models, and JSON file storage logic
├── conftest.py        # pytest fixtures (isolated test client & test data file)
├── test_main.py        # automated test suite
├── requirements.txt    # Python dependencies
├── task.json           # local data file (auto-created on first run)
└── README.md
```

## Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/P-Aek/Task_Tracker.git
cd Task_Tracker/backend
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the server

```bash
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

Interactive docs (Swagger UI): `http://127.0.0.1:8000/docs`

## API Reference

| Method   | Endpoint                          | Description                          |
|----------|------------------------------------|---------------------------------------|
| `GET`    | `/tasks`                          | List all tasks (optional `?status=` filter) |
| `POST`   | `/task`                           | Create a new task                    |
| `PATCH`  | `/task/{task_id}/mark-in-progress` | Mark a task as `in-progress`         |
| `PATCH`  | `/task/{task_id}/mark-done`        | Mark a task as `done`                |
| `DELETE` | `/task/{task_id}`                  | Delete a task                        |

Valid `status` values: `to-do`, `in-progress`, `done`.

### Example: create a task

```bash
curl -X POST http://127.0.0.1:8000/task \
  -H "Content-Type: application/json" \
  -d '{"description": "Buy groceries"}'
```

Response:

```json
{
  "description": "Buy groceries",
  "status": "to-do",
  "id": "b3f1c9e2-...",
  "createdAt": "2026-07-29T10:00:00.000000",
  "updatedAt": "2026-07-29T10:00:00.000000"
}
```

### Example: filter tasks by status

```bash
curl "http://127.0.0.1:8000/tasks?status=in-progress"
```

## Running Tests

The project includes an automated pytest suite covering task creation, listing,
filtering, status updates, deletion, and full end-to-end workflows. Each test
runs against an isolated, temporary `task.json` so your real data is never touched.

```bash
pytest -v
```

## Roadmap / Reference

This project follows the requirements defined by the
[Task Tracker](https://roadmap.sh/projects/task-tracker) project on roadmap.sh,
adapted from a CLI tool into a FastAPI-based REST API.

## License

This project is open source and available for learning purposes.

## ⚠️ Deviations from the Original Requirements

This project is inspired by the [Task Tracker](https://roadmap.sh/projects/task-tracker)
project on roadmap.sh, but it does **not** follow the original spec exactly. The original
project asks for a **command-line application**, and this implementation is a **REST API**
instead. Below is an honest list of where this project differs from the stated requirements,
for transparency (and as a note-to-self for anyone reviewing this repo):

1. **Not actually a CLI.**
   The original requirement is: *"The application should run from the command line, accept
   user actions and inputs as arguments... Use positional arguments in command line to accept
   user inputs."* (e.g. `task-cli add "Buy groceries"`, `task-cli list done`).
   This project is a FastAPI web server accessed via HTTP requests (`curl`, Swagger UI, etc.)
   instead of a `task-cli <command> <args>` interface.

2. **Uses external libraries/frameworks, which the spec explicitly disallows.**
   The requirement states: *"Use the native file system module of your programming language
   to interact with the JSON file. Do not use any external libraries or frameworks to build
   this project."*
   This project uses **FastAPI**, **Pydantic**, and **Uvicorn** — all third-party frameworks —
   rather than sticking to Python's standard library only (`argparse`, `json`, `sys`, etc.).

3. **Missing the "update" command.**
   The spec requires an `update` action (`task-cli update <id> "new description"`) to edit an
   existing task's description. This API defines a `TaskUpdate` model but never wires it up to
   an actual endpoint — there is currently no way to update a task's description after creation,
   only its status (via mark-in-progress / mark-done).

4. **No argument/positional-input parsing.**
   Since there's no CLI, there's no argument parsing logic (e.g. `argparse`) as implied by the
   original project — input instead comes from JSON request bodies and query parameters.

**Why I built it this way:** mainly as a personal exercise to practice FastAPI, Pydantic
models, and REST API design using the Task Tracker requirements as a starting point — not as
a strict, spec-compliant submission for the roadmap.sh project. If you're looking for a
requirement-compliant solution, check out the "how to run" commands (`task-cli add ...`) in
other implementations linked from the [official project page](https://roadmap.sh/projects/task-tracker).
