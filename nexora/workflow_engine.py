
"""NEXORA V2 - Dependency-aware Workflow Engine."""

from collections import defaultdict, deque

from .executor import execute_agent_task
from .planner import create_plan


def validate_dependencies(tasks: list) -> list:
    """Validate dependencies and return tasks in execution order."""

    if not isinstance(tasks, list) or not tasks:
        raise ValueError("Workflow harus memiliki minimal satu tugas.")

    task_map = {}

    for task in tasks:
        if not isinstance(task, dict):
            raise ValueError("Format tugas tidak valid.")

        task_id = task.get("id")

        if not isinstance(task_id, str) or not task_id.strip():
            raise ValueError("Setiap tugas harus memiliki ID.")

        if task_id in task_map:
            raise ValueError(f"ID tugas duplikat: {task_id}")

        task_map[task_id] = task

    graph = defaultdict(list)
    indegree = {task_id: 0 for task_id in task_map}

    for task_id, task in task_map.items():
        dependencies = task.get("depends_on", [])

        if not isinstance(dependencies, list):
            raise ValueError(f"Dependensi {task_id} tidak valid.")

        for dependency in dependencies:
            if dependency not in task_map:
                raise ValueError(
                    f"Dependensi {dependency} tidak ditemukan."
                )

            if dependency == task_id:
                raise ValueError(
                    f"Tugas {task_id} tidak boleh bergantung pada dirinya sendiri."
                )

            graph[dependency].append(task_id)
            indegree[task_id] += 1

    queue = deque(
        task_id for task_id in task_map
        if indegree[task_id] == 0
    )

    ordered = []

    while queue:
        current = queue.popleft()
        ordered.append(task_map[current])

        for dependent in graph[current]:
            indegree[dependent] -= 1

            if indegree[dependent] == 0:
                queue.append(dependent)

    if len(ordered) != len(tasks):
        raise ValueError(
            "Workflow memiliki dependensi melingkar."
        )

    return ordered


def execute_workflow(
    user_goal: str,
    progress_callback=None,
) -> dict:
    """Plan and execute a complete NEXORA workflow.

    Tasks execute sequentially in dependency order.
    Failed dependencies block downstream tasks.
    """

    plan = create_plan(user_goal)
    ordered_tasks = validate_dependencies(plan["tasks"])

    results = []
    result_by_id = {}
    total = len(ordered_tasks)

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
                "error": (
                    "Dependensi gagal atau belum selesai: "
                    + ", ".join(failed_dependencies)
                ),
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
                    f"Tujuan: {plan['objective']}\n"
                    f"Strategi: {plan['strategy']}\n"
                    f"Judul proyek: {plan['project_title']}"
                ),
                previous_results=previous_results,
            )

        results.append(result)
        result_by_id[task_id] = result

        if progress_callback:
            progress_callback({
                "current": index,
                "total": total,
                "task_id": task_id,
                "agent": task["agent"],
                "status": result["status"],
                "title": task["title"],
            })

    completed = sum(
        1 for result in results
        if result["status"] == "COMPLETED"
    )

    failed = sum(
        1 for result in results
        if result["status"] == "FAILED"
    )

    blocked = sum(
        1 for result in results
        if result["status"] == "BLOCKED"
    )

    all_successful = completed == total

    return {
        "plan": plan,
        "results": results,
        "summary": {
            "total": total,
            "completed": completed,
            "failed": failed,
            "blocked": blocked,
            "success": all_successful,
        },
        "status": "COMPLETED" if all_successful else "NEEDS_REVIEW",
    }
