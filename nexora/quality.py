
"""NEXORA V2 - Quality Control Engine."""

from typing import Any


def evaluate_output(
    agent_key: str,
    output: str,
    task: str = "",
) -> dict:
    """Evaluate an agent response using transparent rule-based checks.

    This is a deterministic baseline evaluator, not an AI judge.
    """

    issues = []
    score = 100

    if not isinstance(output, str) or not output.strip():
        return {
            "agent_key": agent_key,
            "score": 0,
            "passed": False,
            "issues": ["Output kosong atau bukan teks."],
            "recommendation": "RETRY",
        }

    clean_output = output.strip()

    if len(clean_output) < 80:
        score -= 25
        issues.append("Output terlalu pendek.")

    if len(clean_output) < 30:
        score -= 20
        issues.append("Output belum memberikan penjelasan memadai.")

    if task and len(clean_output) > 100:
        task_words = {
            word.lower().strip(".,!?;:")
            for word in task.split()
            if len(word) > 4
        }
        output_words = {
            word.lower().strip(".,!?;:")
            for word in clean_output.split()
        }

        if task_words and not task_words.intersection(output_words):
            score -= 15
            issues.append(
                "Keterkaitan output dengan instruksi perlu diperiksa."
            )

    uncertain_markers = [
        "belum diketahui",
        "tidak tersedia",
        "perlu diverifikasi",
        "asumsi",
    ]

    if any(marker in clean_output.lower() for marker in uncertain_markers):
        issues.append(
            "Output mencantumkan ketidakpastian; periksa sebelum digunakan."
        )

    score = max(0, min(100, score))
    passed = score >= 70

    if passed:
        recommendation = "PASS"
    else:
        recommendation = "RETRY"

    return {
        "agent_key": agent_key,
        "score": score,
        "passed": passed,
        "issues": issues,
        "recommendation": recommendation,
    }


def evaluate_workflow(agent_results: list) -> dict:
    """Evaluate all agent outputs in one workflow."""

    if not agent_results:
        return {
            "score": 0,
            "passed": False,
            "total_agents": 0,
            "passed_agents": 0,
            "failed_agents": 0,
            "results": [],
            "recommendation": "REVIEW",
        }

    evaluations = []

    for result in agent_results:
        if not isinstance(result, dict):
            evaluations.append({
                "agent_key": "unknown",
                "score": 0,
                "passed": False,
                "issues": ["Format hasil agent tidak valid."],
                "recommendation": "RETRY",
            })
            continue

        evaluations.append(
            evaluate_output(
                agent_key=str(result.get("agent_key", "unknown")),
                output=result.get("output", ""),
                task=str(result.get("task", "")),
            )
        )

    total = len(evaluations)
    passed_count = sum(1 for item in evaluations if item["passed"])
    failed_count = total - passed_count
    average_score = round(
        sum(item["score"] for item in evaluations) / total,
        2,
    )

    passed = failed_count == 0 and average_score >= 70

    return {
        "score": average_score,
        "passed": passed,
        "total_agents": total,
        "passed_agents": passed_count,
        "failed_agents": failed_count,
        "results": evaluations,
        "recommendation": "PASS" if passed else "REVIEW",
    }
