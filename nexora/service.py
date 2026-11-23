
"""NEXORA V2 - Main Workflow Service."""

from .executor import execute_agent_task
from .planner import create_plan
from .workflow_engine import validate_dependencies
from .workflow_store import (
    create_workflow,
    init_workflow_store,
    update_workflow_status,
    update_task_result,
    update_workflow_summary,
)


def run_project(user_goal: str, db_path: str, progress_callback=None) -> dict:
    """Plan, persist, execute, and report a complete AI workflow."""

    if not isinstance(user_goal, str) or not user_goal.strip():
        raise ValueError("Instruksi proyek tidak boleh kosong.")

    # 1. Initialize storage.
    init_workflow_store(db_path)

    # 2. AI CEO creates and validates a plan.
    plan = create_plan(user_goal)

    # 3. Validate task dependencies before saving or executing.
    ordered_tasks = validate_dependencies(plan["tasks"])

    # 4. Persist the plan.
    workflow_id = create_workflow(db_path, plan)
    update_workflow_status(db_path, workflow_id, "RUNNING")

    results = []
    result_by_id = {}
    total = len(ordered_tasks)

    try:
        # 5. Execute tasks in dependency order.
        for index, task in enumerate(ordered_tasks, start=1):
            task_id = task["id"]
            dependencies = task.get("depends_on", [])

            failed_dependencies = [
                dependency
                for dependency in dependencies
                if result_by_id.get(dependency, {}).get("status")
                != "COMPLETED"
            ]

            if failed_dependencies:
                result = {
                    "task_id": task_id,
                    "agent_key": task["agent"],
                    "title": task["title"],
                    "status": "BLOCKED",
                    "output": "",
                    "quality": {
                        "score": 0,
                        "passed": False,
                        "issues": [
                            "Dependensi gagal atau belum selesai: "
                            + ", ".join(failed_dependencies)
                        ],
                        "recommendation": "REVIEW",
                    },
                    "attempts": 0,
                    "error": "Tugas diblokir karena dependensi gagal.",
                }

            else:
                previous_results = [
                    result_by_id[dependency]
                    for dependency in dependencies
                    if dependency in result_by_id
                ]

                result = execute_agent_task(
                    task=task,
                    project_context=(
                        f"Tujuan proyek: {plan['objective']}\n"
                        f"Strategi: {plan['strategy']}\n"
                        f"Hasil akhir: {plan['final_deliverable']}"
                    ),
                    previous_results=previous_results,
                )

            # Save every result immediately.
            update_task_result(db_path, workflow_id, result)

            results.append(result)
            result_by_id[task_id] = result

            if progress_callback:
                progress_callback({
                    "workflow_id": workflow_id,
                    "current": index,
                    "total": total,
                    "task_id": task_id,
                    "agent": task["agent"],
                    "title": task["title"],
                    "status": result["status"],
                })

        # 6. Calculate workflow summary.
        completed = sum(
            1 for item in results
            if item["status"] == "COMPLETED"
        )

        failed = sum(
            1 for item in results
            if item["status"] == "FAILED"
        )

        blocked = sum(
            1 for item in results
            if item["status"] == "BLOCKED"
        )

        summary = {
            "total": total,
            "completed": completed,
            "failed": failed,
            "blocked": blocked,
            "success": completed == total,
        }

        final_status = (
            "COMPLETED"
            if completed == total
            else "NEEDS_REVIEW"
        )

        update_workflow_summary(
            db_path,
            workflow_id,
            summary,
            final_status,
        )

        return {
            "workflow_id": workflow_id,
            "plan": plan,
            "results": results,
            "summary": summary,
            "status": final_status,
        }

    except Exception:
        # Preserve the workflow record if execution is interrupted.
        update_workflow_status(
            db_path,
            workflow_id,
            "FAILED",
        )
        raise
