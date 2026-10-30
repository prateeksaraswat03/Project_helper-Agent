import os
from typing import Any

import psycopg
from psycopg.types.json import Jsonb
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is missing. Add it to your .env file."
    )


def get_connection():
    """Open a connection to PostgreSQL."""
    return psycopg.connect(DATABASE_URL)


def init_memory_db():
    """Create the project memory table if it doesn't exist."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS project_memory (
                    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                    project_name TEXT NOT NULL,
                    idea TEXT NOT NULL,
                    blueprint JSONB NOT NULL DEFAULT '{}'::jsonb,
                    status TEXT NOT NULL DEFAULT 'planned',
                    current_milestone TEXT,
                    progress_notes TEXT NOT NULL DEFAULT '',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
            """)


def save_project(
    project_name: str,
    idea: str,
    blueprint: dict[str, Any] | None = None,
) -> int:
    """Save a new project and return its database ID."""
    init_memory_db()

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO project_memory
                    (project_name, idea, blueprint)
                VALUES (%s, %s, %s)
                RETURNING id;
                """,
                (
                    project_name,
                    idea,
                    Jsonb(blueprint or {}),
                ),
            )
            project_id = cur.fetchone()[0]

    return project_id


def get_project(project_id: int) -> dict | None:
    """Retrieve one saved project by ID."""
    init_memory_db()

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, project_name, idea, blueprint,
                       status, current_milestone, progress_notes,
                       created_at, updated_at
                FROM project_memory
                WHERE id = %s;
                """,
                (project_id,),
            )

            row = cur.fetchone()

            if row is None:
                return None

            columns = [column.name for column in cur.description]
            return dict(zip(columns, row))


def update_progress(
    project_id: int,
    status: str,
    milestone: str,
    notes: str,
) -> bool:
    """Update the status and progress of a saved project."""
    init_memory_db()

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE project_memory
                SET status = %s,
                    current_milestone = %s,
                    progress_notes = %s,
                    updated_at = NOW()
                WHERE id = %s;
                """,
                (status, milestone, notes, project_id),
            )

            return cur.rowcount > 0


def list_projects() -> list[dict]:
    """List saved projects, newest first."""
    init_memory_db()

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, project_name, idea, status,
                       current_milestone, updated_at
                FROM project_memory
                ORDER BY updated_at DESC;
            """)

            columns = [column.name for column in cur.description]
            return [
                dict(zip(columns, row))
                for row in cur.fetchall()
            ]


if __name__ == "__main__":
    init_memory_db()
    print("Project memory database initialized successfully.")
    print("Saved projects:", list_projects())
