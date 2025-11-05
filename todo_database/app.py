#!/usr/bin/env python3
"""
FastAPI backend for todo_database

This app exposes a lightweight REST API over a local SQLite database (myapp.db).
It provides CRUD endpoints for managing to-do tasks.

Run (development):
    pip install -r requirements.txt
    uvicorn app:app --host 0.0.0.0 --port 5001 --reload

Notes:
- Uses SQLite file `myapp.db` in the same directory.
- Ensures PRAGMA foreign_keys=ON.
- Uses sqlite3.Row row_factory to return dict-like rows.
- CORS allows http://localhost:3000 (frontend dev) and common dev methods/headers.

OpenAPI/Docs:
- Swagger UI:       http://localhost:5001/docs
- ReDoc:            http://localhost:5001/redoc
- OpenAPI JSON:     http://localhost:5001/openapi.json
"""
from typing import List, Optional, Any, Dict
from datetime import datetime, timezone
import os
import sqlite3

from fastapi import FastAPI, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

DB_FILE = os.path.join(os.path.dirname(__file__), "myapp.db")


def get_connection() -> sqlite3.Connection:
    """
    Create a SQLite connection with row factory for dict-like access and
    enable foreign key constraints.
    """
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # enables dict-like row access
    # Ensure foreign keys are enforced
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def ensure_tasks_table() -> None:
    """
    Ensures the tasks table exists with the required schema.
    """
    conn = get_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                completed INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


# Pydantic models for request/response

class TaskBase(BaseModel):
    title: str = Field(..., description="Short title for the task")
    description: Optional[str] = Field("", description="Detailed description of the task")


class TaskCreate(TaskBase):
    """Payload to create a new task."""
    pass


class TaskUpdate(BaseModel):
    """Payload to replace a task (PUT)."""
    title: str = Field(..., description="Short title for the task")
    description: Optional[str] = Field("", description="Detailed description of the task")
    completed: bool = Field(..., description="Completion status of the task")


class TaskOut(BaseModel):
    """Serialized task to return to clients."""
    id: int
    title: str
    description: str
    completed: bool
    created_at: str
    updated_at: str


# Initialize FastAPI app with metadata and tags
app = FastAPI(
    title="To-Do Tasks API",
    description="Lightweight REST API over SQLite for managing to-do tasks.",
    version="1.0.0",
    openapi_tags=[
        {"name": "health", "description": "Service health and readiness"},
        {"name": "tasks", "description": "CRUD operations for tasks"},
    ],
)

# Configure CORS for development (frontend on http://localhost:3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    """Create schema at startup if it doesn't exist."""
    ensure_tasks_table()


# PUBLIC_INTERFACE
@app.get("/api/health", tags=["health"], summary="Health check", description="Returns API status and basic database connectivity info.")
def health() -> Dict[str, Any]:
    """
    Health endpoint to verify the API is running and SQLite is accessible.

    Returns:
        dict: Contains status, database file path, and current timestamp.
    """
    # Quick DB check
    try:
        conn = get_connection()
        cur = conn.execute("SELECT 1")
        cur.fetchone()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}") from e
    finally:
        try:
            conn.close()
        except Exception:
            pass

    return {
        "status": "ok",
        "db_file": DB_FILE,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def row_to_task_out(row: sqlite3.Row) -> TaskOut:
    """Convert a sqlite3.Row to TaskOut."""
    return TaskOut(
        id=row["id"],
        title=row["title"],
        description=row["description"],
        completed=bool(row["completed"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


# PUBLIC_INTERFACE
@app.get(
    "/api/tasks",
    response_model=List[TaskOut],
    tags=["tasks"],
    summary="List tasks",
    description="Retrieve all tasks ordered by creation time descending.",
)
def list_tasks() -> List[TaskOut]:
    """
    List all tasks.

    Returns:
        List[TaskOut]: All tasks ordered by created_at DESC, id DESC.
    """
    conn = get_connection()
    try:
        cur = conn.execute("SELECT * FROM tasks ORDER BY datetime(created_at) DESC, id DESC")
        rows = cur.fetchall()
        return [row_to_task_out(r) for r in rows]
    finally:
        conn.close()


# PUBLIC_INTERFACE
@app.post(
    "/api/tasks",
    response_model=TaskOut,
    status_code=201,
    tags=["tasks"],
    summary="Create task",
    description="Create a new task with title and optional description.",
)
def create_task(payload: TaskCreate) -> TaskOut:
    """
    Create a new task.

    Args:
        payload (TaskCreate): The task details (title, optional description).

    Returns:
        TaskOut: The created task.
    """
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    conn = get_connection()
    try:
        cur = conn.execute(
            """
            INSERT INTO tasks (title, description, completed, created_at, updated_at)
            VALUES (?, ?, 0, ?, ?)
            """,
            (payload.title, payload.description or "", now, now),
        )
        task_id = cur.lastrowid
        conn.commit()

        cur = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=500, detail="Failed to retrieve created task")
        return row_to_task_out(row)
    finally:
        conn.close()


# PUBLIC_INTERFACE
@app.put(
    "/api/tasks/{task_id}",
    response_model=TaskOut,
    tags=["tasks"],
    summary="Replace task",
    description="Replace title, description, and completed status of a task.",
)
def replace_task(
    task_id: int = Path(..., description="ID of the task to replace"),
    payload: TaskUpdate = None,
) -> TaskOut:
    """
    Replace a task with new values.

    Args:
        task_id (int): Task ID.
        payload (TaskUpdate): New values for the task.

    Returns:
        TaskOut: The updated task.

    Raises:
        HTTPException 404: If the task does not exist.
    """
    conn = get_connection()
    try:
        cur = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        existing = cur.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Task not found")

        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        conn.execute(
            """
            UPDATE tasks
            SET title = ?, description = ?, completed = ?, updated_at = ?
            WHERE id = ?
            """,
            (payload.title, payload.description or "", 1 if payload.completed else 0, now, task_id),
        )
        conn.commit()

        cur = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cur.fetchone()
        return row_to_task_out(row)
    finally:
        conn.close()


# PUBLIC_INTERFACE
@app.patch(
    "/api/tasks/{task_id}/complete",
    response_model=TaskOut,
    tags=["tasks"],
    summary="Mark task as complete/incomplete",
    description="Toggle completion status of a task. If 'complete' query param is omitted, defaults to true.",
)
def complete_task(
    task_id: int = Path(..., description="ID of the task to modify"),
    complete: Optional[bool] = True,
) -> TaskOut:
    """
    Mark a task as complete or incomplete.

    Args:
        task_id (int): Task ID.
        complete (bool, optional): Desired completion state. Defaults to True.

    Returns:
        TaskOut: The updated task.

    Raises:
        HTTPException 404: If the task does not exist.
    """
    conn = get_connection()
    try:
        cur = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Task not found")

        now = datetime.utcnow().isoformat(timespec="seconds")
        conn.execute(
            "UPDATE tasks SET completed = ?, updated_at = ? WHERE id = ?",
            (1 if complete else 0, now, task_id),
        )
        conn.commit()

        cur = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        updated = cur.fetchone()
        return row_to_task_out(updated)
    finally:
        conn.close()


# PUBLIC_INTERFACE
@app.delete(
    "/api/tasks/{task_id}",
    status_code=204,
    tags=["tasks"],
    summary="Delete task",
    description="Delete a task by ID.",
)
def delete_task(task_id: int = Path(..., description="ID of the task to delete")) -> None:
    """
    Delete a task.

    Args:
        task_id (int): Task ID.

    Returns:
        None

    Raises:
        HTTPException 404: If the task does not exist.
    """
    conn = get_connection()
    try:
        cur = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        if cur.rowcount == 0:
            # Not found
            raise HTTPException(status_code=404, detail="Task not found")
        conn.commit()
    finally:
        conn.close()
