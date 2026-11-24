
"""NEXORA V2 - Main Workflow Service."""

from .executor import execute_agent_task
from .planner import create_plan
from .final_review import review_project
from .workflow_engine import validate_dependencies

from .workflow_store import (
    create_workflow,
    init_workflow_store,
    update_workflow_status,
    update_task_result,
    update_workflow_summary,
    update_workflow_review,
)


def run_project(user_goal: str, db_path: str, progress_callback=None) -> dict:
    """Plan, execute, review, and persist a complete AI workflow."""

    if not isinstance(user_goal, str) or not user_goal.strip():
        raise ValueError("Instruksi proyek tidak boleh kosong.")

    # 1. Initialize database.
    init_workflow_store(db_path)

    # 2. AI CEO creates the project plan.
    plan = create_plan(user_goal)

    # 3. Validate task dependencies.
    ordered_tasks = validate_dependencies(plan["tasks"])

    # 4. Save workflow plan.
    workflow_id = create_workflow(db_path, plan)
    update_workflow_status(db_path, workflow_id, "RUNNING")

    results = []
    result_by_id = {}
    total = len(ordered_tasks)

    try:
        # 5. Execute specialist agents.
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

            # Save every agent result immediately.
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

        # 6. Calculate execution statistics.
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

        # 7. AI CEO performs final review.
        try:
            final_review = review_project(
                user_goal=user_goal,
                plan=plan,
                agent_results=results,
            )

        except Exception as review_error:
            final_review = {
                "decision": "NEEDS_REVIEW",
                "score": 0,
                "summary": (
                    "Evaluasi akhir AI CEO gagal. "
                    "Hasil agent tetap tersimpan."
                ),
                "goal_achievement": (
                    "Belum dapat dipastikan karena evaluasi gagal."
                ),
                "strengths": [],
                "gaps": [
                    "AI CEO Final Review gagal: "
                    + str(review_error)[:500]
                ],
                "risks": [
                    "Proyek belum mendapatkan persetujuan AI CEO."
                ],
                "recommendations": [
                    "Periksa koneksi AI provider dan evaluasi ulang."
                ],
                "task_reviews": [],
            }

        # 8. Persist complete CEO review.
        update_workflow_review(
            db_path,
            workflow_id,
            final_review,
        )

        # 9. Determine final workflow status.
        final_status = (
            "COMPLETED"
            if (
                completed == total
                and final_review["decision"] == "APPROVED"
            )
            else "NEEDS_REVIEW"
        )

        # 10. Save final workflow summary.
        summary = {
            "total": total,
            "completed": completed,
            "failed": failed,
            "blocked": blocked,
            "success": final_status == "COMPLETED",
            "ceo_decision": final_review["decision"],
            "ceo_score": final_review["score"],
        }

        update_workflow_summary(
            db_path,
            workflow_id,
            summary,
            final_status,
        )

        # 11. Return complete workflow report.
        return {
            "workflow_id": workflow_id,
            "plan": plan,
            "results": results,
            "summary": summary,
            "final_review": final_review,
            "status": final_status,
        }

    except Exception:
        update_workflow_status(
            db_path,
            workflow_id,
            "FAILED",
        )
        raise
