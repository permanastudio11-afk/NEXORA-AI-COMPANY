
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

def connect(db_path):
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    return con

def init_db(db_path):
    with connect(db_path) as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS tasks (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          title TEXT NOT NULL,
          status TEXT NOT NULL,
          created_at TEXT NOT NULL,
          completed_at TEXT
        );
        CREATE TABLE IF NOT EXISTS agent_runs (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          task_id INTEGER NOT NULL,
          agent_key TEXT NOT NULL,
          agent_name TEXT NOT NULL,
          status TEXT NOT NULL,
          output TEXT,
          created_at TEXT NOT NULL,
          FOREIGN KEY(task_id) REFERENCES tasks(id)
        );
        CREATE TABLE IF NOT EXISTS activity_logs (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          level TEXT NOT NULL,
          message TEXT NOT NULL,
          created_at TEXT NOT NULL
        );
        """)

def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def log(db_path, level, message):
    with connect(db_path) as con:
        con.execute("INSERT INTO activity_logs(level,message,created_at) VALUES(?,?,?)",
                    (level, message, now()))

def create_task(db_path, title):
    with connect(db_path) as con:
        cur = con.execute("INSERT INTO tasks(title,status,created_at) VALUES(?,?,?)",
                          (title, "RUNNING", now()))
        return cur.lastrowid

def save_run(db_path, task_id, key, name, status, output):
    with connect(db_path) as con:
        con.execute("""INSERT INTO agent_runs(task_id,agent_key,agent_name,status,output,created_at)
                       VALUES(?,?,?,?,?,?)""",
                    (task_id, key, name, status, output, now()))

def finish_task(db_path, task_id, status="COMPLETED"):
    with connect(db_path) as con:
        con.execute("UPDATE tasks SET status=?, completed_at=? WHERE id=?",
                    (status, now(), task_id))

def fetch_all(db_path, query, params=()):
    with connect(db_path) as con:
        return [dict(r) for r in con.execute(query, params).fetchall()]
