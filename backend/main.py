import os
import uuid
from fastapi import FastAPI , HTTPException 
from pydantic import BaseModel
from datetime import datetime
from enum import Enum
from typing import Optional
from contextlib import asynccontextmanager
import json

Task_File = "./task.json"

@asynccontextmanager
# create Task_file when have not.
async def lifespan(app: FastAPI) :
    if not os.path.exists(Task_File):
        with open(Task_File, "w") as file:
            json.dump([], file)
    yield


app = FastAPI(lifespan=lifespan)



class StatusEnum(str, Enum):
    pending = "to-do"
    inProcess = "in-progress" 
    isDone = "done"


class TaskCreate(BaseModel) :
    description: str
    status: StatusEnum = StatusEnum.pending # status default = "to-do"

class Task(TaskCreate) :
    id: str
    createdAt: datetime
    updatedAt: datetime

class TaskUpdate(BaseModel):
    description: Optional[str] = None
    status: Optional[StatusEnum] = None

# list all tasks
@app.get("/tasks")
def get_tasks(status: Optional[StatusEnum] = None):
    # open task.json
    with open(Task_File, "r") as file :
        # load task
        tasks = json.load(file)

    # return all task
    if status is None :
        return tasks

    # Filter task with status
    filter_task = []
    for t in tasks :
        if t["status"] == status.value :
            filter_task.append(t)

    return filter_task

# Add task
@app.post("/task")
def write_tasks(task: TaskCreate):
    # open task.json
    with open(Task_File, "r") as file :
        # load task
        tasks = json.load(file)
    now = datetime.now()
    # create id 
    new_task = Task(
        id = str(uuid.uuid4()),
        description = task.description,
        status = task.status,
        createdAt = now,
        updatedAt = now
    )
    # add task
    tasks.append(new_task.model_dump(mode="json"))

    # write task to json file
    tmp_file = Task_File + ".tmp" 
    with open(tmp_file, "w") as file :
        json.dump(tasks, file, indent=2)

    os.replace(tmp_file, Task_File)

    return new_task

# Update task
@app.patch("/task/{task_id}/mark-in-progress") # mark in-progress
def mark_in_progree(task_id: str):
    return _mark_status(task_id, StatusEnum.inProcess)

@app.patch("/task/{task_id}/mark-done") # mark done
def mark_done(task_id: str):
    return _mark_status(task_id, StatusEnum.isDone)

def _mark_status(task_id: str , status: StatusEnum):
    with open(Task_File, "r") as file:
        tasks = json.load(file)

    for t in tasks:
        if t["id"] == task_id :
            t["status"] = status.value
            t["updatedAt"] = datetime.now().isoformat()
            break
    else :
        raise HTTPException(status_code=404 , detail="Task not found")

    tmp_file = Task_File + ".tmp"
    with open(tmp_file, "w") as file :
        json.dump(tasks, file, indent=2)

    os.replace(tmp_file, Task_File)    

    return t

# delete task
@app.delete("/task/{task_id}")
def delete_task(task_id: str):
    # open task
    with open(Task_File, "r") as file :
        tasks = json.load(file)

    # check id 
    if not any(t["id"] == task_id for t in tasks) :
        raise HTTPException(status_code = 404, detail = "Task not found")

    # create new list
    new_tasks = []
    for t in tasks :
        if t["id"] != task_id :
            new_tasks.append(t)

    tasks = new_tasks

    # save file
    tmp_file = Task_File + ".tmp"
    with open(tmp_file, "w") as file :
        json.dump(tasks, file, indent=2)

    os.replace(tmp_file, Task_File)    

    return tasks




