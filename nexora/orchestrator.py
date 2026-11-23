
from .agents import AGENTS, run_agent
from .db import create_task, save_run, finish_task, log

# DEMO orchestration: predictable local outputs, no external API calls.
def execute_workflow(db_path, title, selected_agents=None):
    chosen = selected_agents or [a[0] for a in AGENTS if a[0] != "ceo"]
    task_id = create_task(db_path, title)
    log(db_path, "INFO", f"Workflow #{task_id} dimulai: {title}")
    try:
        ceo = run_agent("ceo", title)
        save_run(db_path, task_id, "ceo", "AI CEO", "COMPLETED", ceo)
        for key, name, _ in AGENTS:
            if key == "ceo" or key not in chosen:
                continue
            output = run_agent(key, title)
            save_run(db_path, task_id, key, name, "COMPLETED", output)
            log(db_path, "INFO", f"{name} menyelesaikan tugas #{task_id}")
        finish_task(db_path, task_id)
        log(db_path, "INFO", f"Workflow #{task_id} selesai")
    except Exception as exc:
        finish_task(db_path, task_id, "FAILED")
        log(db_path, "ERROR", f"Workflow #{task_id} gagal: {exc}")
        raise
    return task_id
