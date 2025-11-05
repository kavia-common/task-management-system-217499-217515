#!/usr/bin/env python3
"""
Initialize SQLite database for todo_database.

This script ensures the required schema exists for the tasks table and
(optionally) seeds example data if the table is empty. It preserves compatibility
with existing utilities by using the same myapp.db path in this folder.

Usage:
    python init_db.py
"""

import os
import sqlite3
from datetime import datetime, timezone

DB_NAME = "myapp.db"

def get_db_path() -> str:
    """Return absolute path to the SQLite database file."""
    return os.path.join(os.path.dirname(__file__), DB_NAME)

def get_connection() -> sqlite3.Connection:
    """Create a SQLite connection and ensure foreign keys are enforced."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def ensure_tasks_table(conn: sqlite3.Connection) -> None:
    """
    Create the tasks table if it does not already exist.

    Required schema:
      - id INTEGER PRIMARY KEY AUTOINCREMENT
      - title TEXT NOT NULL
      - description TEXT
      - completed INTEGER DEFAULT 0
      - created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      - updated_at TIMESTAMP
    """
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            completed INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP
        )
        """
    )
    conn.commit()

def seed_sample_tasks(conn: sqlite3.Connection) -> None:
    """
    Seed 1-2 sample tasks if the table is empty.
    """
    cur = conn.execute("SELECT COUNT(*) AS c FROM tasks")
    count = cur.fetchone()["c"]
    if count and count > 0:
        return

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    # Insert 2 sample tasks
    conn.execute(
        """
        INSERT INTO tasks (title, description, completed, created_at, updated_at)
        VALUES (?, ?, ?, COALESCE(?, CURRENT_TIMESTAMP), ?)
        """,
        ("Welcome to your To-Do List", "Try creating, editing, and completing tasks.", 0, now, now),
    )
    conn.execute(
        """
        INSERT INTO tasks (title, description, completed, created_at, updated_at)
        VALUES (?, ?, ?, COALESCE(?, CURRENT_TIMESTAMP), ?)
        """,
        ("Sample completed task", "This one is already done.", 1, now, now),
    )
    conn.commit()

def write_connection_info():
    """
    Write connection details to db_connection.txt for convenience (maintains compatibility with utilities).
    """
    current_dir = os.path.dirname(__file__)
    db_path_abs = get_db_path()
    connection_string = f"sqlite:///{db_path_abs}"
    try:
        with open(os.path.join(current_dir, "db_connection.txt"), "w") as f:
            f.write("# SQLite connection methods:\n")
            f.write(f"# Python: sqlite3.connect('{DB_NAME}')\n")
            f.write(f"# Connection string: {connection_string}\n")
            f.write(f"# File path: {db_path_abs}\n")
    except Exception as e:
        print(f"Warning: Could not save connection info: {e}")

def write_db_visualizer_env():
    """
    Ensure db_visualizer/sqlite.env contains the SQLITE_DB path for the bundled viewer.
    """
    db_path_abs = get_db_path()
    visualizer_dir = os.path.join(os.path.dirname(__file__), "db_visualizer")
    try:
        os.makedirs(visualizer_dir, exist_ok=True)
        with open(os.path.join(visualizer_dir, "sqlite.env"), "w") as f:
            f.write(f'export SQLITE_DB="{db_path_abs}"\n')
    except Exception as e:
        print(f"Warning: Could not save environment variables: {e}")

def main() -> None:
    print("Starting SQLite setup...")
    db_path = get_db_path()
    db_exists = os.path.exists(db_path)

    if db_exists:
        print(f"SQLite database already exists at {db_path}")
        try:
            conn = get_connection()
            conn.execute("SELECT 1")
            conn.close()
            print("Database is accessible and working.")
        except Exception as e:
            print(f"Warning: Database exists but may be corrupted: {e}")
    else:
        print("Creating new SQLite database...")

    conn = get_connection()
    try:
        # Ensure required tasks table exists (required by the application)
        ensure_tasks_table(conn)

        # Optionally seed initial sample tasks if table is empty
        seed_sample_tasks(conn)

        # Provide some quick stats
        cur = conn.execute("SELECT COUNT(*) AS c FROM tasks")
        tasks_count = cur.fetchone()["c"]
    finally:
        conn.close()

    # Maintain compatibility artifacts
    write_connection_info()
    write_db_visualizer_env()

    # Final output
    print("\nSQLite setup complete!")
    print(f"Database: {DB_NAME}")
    print(f"Location: {db_path}")
    print("")
    print("Database statistics:")
    print(f"  Tasks: {tasks_count}")

    # If sqlite3 CLI is available, show how to use it
    try:
        import subprocess
        result = subprocess.run(['which', 'sqlite3'], capture_output=True, text=True)
        if result.returncode == 0:
            print("")
            print("SQLite CLI is available. You can also use:")
            print(f"  sqlite3 {db_path}")
    except Exception:
        pass

    print("\nScript completed successfully.")

if __name__ == "__main__":
    main()
