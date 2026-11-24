
"""NEXORA V2 - Persistent Workflow Storage."""

import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect(db_path):
    """Open a SQLite connection with foreign keys enabled."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    con = sqlite3.connect(str(path), timeout=30)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def init_workflow_store(db_path):
    """Create or safely upgrade V2 workflow tables."""

    with connect(db_path) as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS v2_workflows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_title TEXT NOT NULL,
            objective TEXT NOT NULL,
            strategy TEXT,
            final_deliverable TEXT,
            plan_json TEXT NOT NULL,
            status TEXT NOT NULL,
            total_tasks INTEGER DEFAULT 0,
            completed_tasks INTEGER DEFAULT 0,
            failed_tasks INTEGER DEFAULT 0,
            blocked_tasks INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            completed_at TEXT
        );

        CREATE TABLE IF NOT EXISTS v2_workflow_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow_id INTEGER NOT NULL,
            task_id TEXT NOT NULL,
            agent_key TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            priority TEXT,
            depends_on_json TEXT,
            acceptance_criteria_json TEXT,
            status TEXT NOT NULL,
            output TEXT,
            quality_json TEXT,
            attempts INTEGER DEFAULT 0,
            error TEXT,
            created_at TEXT NOT NULL,
            completed_at TEXT,
            UNIQUE(workflow_id, task_id),
            FOREIGN KEY(workflow_id)
                REFERENCES v2_workflows(id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS v2_workflow_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow_id INTEGER NOT NULL,
            task_id TEXT,
            event_type TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(workflow_id)
                REFERENCES v2_workflows(id)
                ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_v2_tasks_workflow
        ON v2_workflow_tasks(workflow_id);

        CREATE INDEX IF NOT EXISTS idx_v2_events_workflow
        ON v2_workflow_events(workflow_id);
        """)

        # Backward-compatible database migration.
        columns = {
            row["name"]
            for row in con.execute(
                "PRAGMA table_info(v2_workflows)"
            ).fetchall()
        }

        if "final_review_json" not in columns:
            con.execute("""
                ALTER TABLE v2_workflows
                ADD COLUMN final_review_json TEXT
            """)


def create_workflow(db_path, plan):
    """Save a validated workflow plan and its pending tasks."""

    if not isinstance(plan, dict):
        raise ValueError("Rencana workflow tidak valid.")

    tasks = plan.get("tasks", [])

    with connect(db_path) as con:
        cur = con.execute("""
            INSERT INTO v2_workflows (
                project_title, objective, strategy,
                final_deliverable, plan_json, status,
                total_tasks, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(plan.get("project_title", "NEXORA Workflow")),
            str(plan.get("objective", "")),
            str(plan.get("strategy", "")),
            str(plan.get("final_deliverable", "")),
            json.dumps(plan, ensure_ascii=False),
            "PENDING",
            len(tasks),
            _now(),
        ))

        workflow_id = cur.lastrowid

        for task in tasks:
            con.execute("""
                INSERT INTO v2_workflow_tasks (
                    workflow_id, task_id, agent_key, title,
                    description, priority, depends_on_json,
                    acceptance_criteria_json, status, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                workflow_id,
                task["id"],
                task["agent"],
                task["title"],
                task["description"],
                task["priority"],
                json.dumps(task["depends_on"]),
                json.dumps(task["acceptance_criteria"]),
                "PENDING",
                _now(),
            ))

        con.execute("""
            INSERT INTO v2_workflow_events (
                workflow_id, event_type, message, created_at
            )
            VALUES (?, ?, ?, ?)
        """, (
            workflow_id,
            "CREATED",
            "Workflow dibuat dan rencana disimpan.",
            _now(),
        ))

        return workflow_id


def update_workflow_status(db_path, workflow_id, status):
    """Update workflow status."""

    allowed = {
        "PENDING",
        "RUNNING",
        "COMPLETED",
        "NEEDS_REVIEW",
        "FAILED",
    }

    if status not in allowed:
        raise ValueError("Status workflow tidak dikenal.")

    with connect(db_path) as con:
        completed_at = _now() if status in {
            "COMPLETED", "NEEDS_REVIEW", "FAILED"
        } else None

        con.execute("""
            UPDATE v2_workflows
            SET status = ?, completed_at = ?
            WHERE id = ?
        """, (status, completed_at, workflow_id))


def update_task_result(db_path, workflow_id, result):
    """Save one agent execution result."""

    task_id = result["task_id"]
    status = result["status"]

    allowed = {"PENDING", "RUNNING", "COMPLETED", "FAILED", "BLOCKED"}

    if status not in allowed:
        raise ValueError("Status tugas tidak dikenal.")

    with connect(db_path) as con:
        con.execute("""
            UPDATE v2_workflow_tasks
            SET status = ?,
                output = ?,
                quality_json = ?,
                attempts = ?,
                error = ?,
                completed_at = ?
            WHERE workflow_id = ? AND task_id = ?
        """, (
            status,
            result.get("output", ""),
            json.dumps(result.get("quality", {}), ensure_ascii=False),
            result.get("attempts", 0),
            result.get("error"),
            _now(),
            workflow_id,
            task_id,
        ))

        con.execute("""
            INSERT INTO v2_workflow_events (
                workflow_id, task_id, event_type, message, created_at
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            workflow_id,
            task_id,
            status,
            f"Tugas {task_id}: {status}",
            _now(),
        ))


def update_workflow_review(db_path, workflow_id, review):
    """Persist the complete AI CEO final review."""

    if not isinstance(review, dict):
        raise ValueError("Laporan AI CEO tidak valid.")

    review_json = json.dumps(review, ensure_ascii=False)

    with connect(db_path) as con:
        cur = con.execute("""
            UPDATE v2_workflows
            SET final_review_json = ?
            WHERE id = ?
        """, (review_json, workflow_id))

        if cur.rowcount == 0:
            raise ValueError(
                f"Workflow {workflow_id} tidak ditemukan."
            )

        con.execute("""
            INSERT INTO v2_workflow_events (
                workflow_id, event_type, message, created_at
            )
            VALUES (?, ?, ?, ?)
        """, (
            workflow_id,
            "CEO_FINAL_REVIEW",
            (
                "AI CEO memberikan keputusan "
                f"{review.get('decision', 'UNKNOWN')} "
                f"dengan skor {review.get('score', 0)}."
            ),
            _now(),
        ))


def update_workflow_summary(db_path, workflow_id, summary, status):
    """Save final workflow counters and status."""

    with connect(db_path) as con:
        con.execute("""
            UPDATE v2_workflows
            SET total_tasks = ?,
                completed_tasks = ?,
                failed_tasks = ?,
                blocked_tasks = ?,
                status = ?,
                completed_at = ?
            WHERE id = ?
        """, (
            summary.get("total", 0),
            summary.get("completed", 0),
            summary.get("failed", 0),
            summary.get("blocked", 0),
            status,
            _now(),
            workflow_id,
        ))


def get_workflow(db_path, workflow_id):
    """Retrieve one workflow with tasks, events and CEO review."""

    with connect(db_path) as con:
        workflow = con.execute(
            "SELECT * FROM v2_workflows WHERE id = ?",
            (workflow_id,),
        ).fetchone()

        if workflow is None:
            return None

        tasks = con.execute("""
            SELECT * FROM v2_workflow_tasks
            WHERE workflow_id = ?
            ORDER BY id
        """, (workflow_id,)).fetchall()

        events = con.execute("""
            SELECT * FROM v2_workflow_events
            WHERE workflow_id = ?
            ORDER BY id
        """, (workflow_id,)).fetchall()

        workflow_data = dict(workflow)

        review_json = workflow_data.get("final_review_json")

        try:
            final_review = (
                json.loads(review_json)
                if review_json else None
            )
        except (json.JSONDecodeError, TypeError):
            final_review = None

        workflow_data["final_review"] = final_review

        return {
            "workflow": workflow_data,
            "tasks": [dict(row) for row in tasks],
            "events": [dict(row) for row in events],
        }


def list_workflows(db_path, limit=50):
    """List recent workflows."""

    limit = max(1, min(int(limit), 200))

    with connect(db_path) as con:
        rows = con.execute("""
            SELECT id, project_title, status, total_tasks,
                   completed_tasks, failed_tasks, blocked_tasks,
                   created_at, completed_at
            FROM v2_workflows
            ORDER BY id DESC
            LIMIT ?
        """, (limit,)).fetchall()

        return [dict(row) for row in rows]
