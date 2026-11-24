"""NEXORA V2 - AI CEO Final Review."""

import json
import re

from .llm import chat


CEO_REVIEW_SYSTEM_PROMPT = """
Kamu adalah AI CEO NEXORA AI COMPANY.

Tugasmu adalah melakukan evaluasi akhir terhadap hasil kerja seluruh
AI specialist setelah workflow selesai.

Evaluasi berdasarkan:
1. Tujuan utama proyek.
2. Strategi dan hasil akhir yang direncanakan.
3. Deskripsi setiap tugas.
4. Acceptance criteria setiap tugas.
5. Hasil aktual dari setiap agent.
6. Status dan hasil pemeriksaan kualitas setiap tugas.

Jangan menganggap tugas berhasil hanya karena agent menghasilkan teks.
Periksa apakah hasilnya benar-benar memenuhi tujuan dan kriteria penerimaan.

Jangan mengarang fakta, hasil implementasi, data, atau keberhasilan.
Jika ada informasi yang belum tersedia, sebutkan sebagai kekurangan.

Berikan keputusan:
- APPROVED: hasil proyek layak diterima.
- NEEDS_REVIEW: masih ada kekurangan yang perlu diperbaiki.

Gunakan skor 0 sampai 100.

Keluarkan hanya JSON valid tanpa Markdown atau penjelasan di luar JSON.

Format JSON wajib:
{
  "decision": "APPROVED atau NEEDS_REVIEW",
  "score": 0,
  "summary": "Ringkasan evaluasi akhir",
  "goal_achievement": "Penilaian pencapaian tujuan proyek",
  "strengths": ["Kekuatan hasil proyek"],
  "gaps": ["Kekurangan yang ditemukan"],
  "risks": ["Risiko yang perlu diperhatikan"],
  "recommendations": ["Rekomendasi perbaikan"],
  "task_reviews": [
    {
      "task_id": "ID tugas",
      "verdict": "PASS atau REVISE",
      "reason": "Alasan penilaian"
    }
  ]
}
"""


def _extract_json(text: str) -> dict:
    """Extract and parse JSON from the CEO response."""

    if not isinstance(text, str) or not text.strip():
        raise ValueError("Respons AI CEO kosong.")

    cleaned = text.strip()

    # Remove optional Markdown code fences.
    cleaned = re.sub(
        r"^```(?:json)?\s*|\s*```$",
        "",
        cleaned,
        flags=re.IGNORECASE,
    ).strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        # Try extracting the outermost JSON object.
        start = cleaned.find("{")
        end = cleaned.rfind("}")

        if start < 0 or end <= start:
            raise ValueError("AI CEO tidak menghasilkan JSON valid.")

        try:
            data = json.loads(cleaned[start:end + 1])
        except json.JSONDecodeError as exc:
            raise ValueError(
                "Format JSON dari AI CEO tidak valid."
            ) from exc

    if not isinstance(data, dict):
        raise ValueError("Hasil review harus berupa objek JSON.")

    return data


def _validate_review(review: dict, expected_task_ids: set) -> dict:
    """Validate and normalize the CEO review."""

    required_fields = {
        "decision",
        "score",
        "summary",
        "goal_achievement",
        "strengths",
        "gaps",
        "risks",
        "recommendations",
        "task_reviews",
    }

    missing = required_fields - set(review)

    if missing:
        raise ValueError(
            "Hasil review tidak lengkap: " + ", ".join(sorted(missing))
        )

    decision = review["decision"]

    if decision not in ("APPROVED", "NEEDS_REVIEW"):
        raise ValueError("Keputusan AI CEO tidak valid.")

    score = review["score"]

    if isinstance(score, bool) or not isinstance(score, int):
        raise ValueError("Skor AI CEO harus berupa angka bulat.")

    if not 0 <= score <= 100:
        raise ValueError("Skor AI CEO harus antara 0 dan 100.")

    for field in ("summary", "goal_achievement"):
        if not isinstance(review[field], str) or not review[field].strip():
            raise ValueError(f"Field {field} tidak boleh kosong.")

    for field in ("strengths", "gaps", "risks", "recommendations"):
        if not isinstance(review[field], list):
            raise ValueError(f"Field {field} harus berupa list.")

        if not all(isinstance(item, str) for item in review[field]):
            raise ValueError(f"Isi field {field} harus berupa teks.")

    task_reviews = review["task_reviews"]

    if not isinstance(task_reviews, list):
        raise ValueError("task_reviews harus berupa list.")

    normalized_reviews = {}

    for item in task_reviews:
        if not isinstance(item, dict):
            raise ValueError("Format task review tidak valid.")

        task_id = item.get("task_id")
        verdict = item.get("verdict")
        reason = item.get("reason")

        if task_id not in expected_task_ids:
            raise ValueError(f"ID tugas review tidak dikenal: {task_id}")

        if task_id in normalized_reviews:
            raise ValueError(f"Review tugas duplikat: {task_id}")

        if verdict not in ("PASS", "REVISE"):
            raise ValueError(f"Verdict tugas {task_id} tidak valid.")

        if not isinstance(reason, str) or not reason.strip():
            raise ValueError(f"Alasan review tugas {task_id} kosong.")

        normalized_reviews[task_id] = {
            "task_id": task_id,
            "verdict": verdict,
            "reason": reason.strip(),
        }

    # Missing task reviews must never be treated as passed.
    for task_id in expected_task_ids:
        if task_id not in normalized_reviews:
            normalized_reviews[task_id] = {
                "task_id": task_id,
                "verdict": "REVISE",
                "reason": "AI CEO tidak memberikan evaluasi untuk tugas ini.",
            }

    return {
        "decision": decision,
        "score": score,
        "summary": review["summary"].strip(),
        "goal_achievement": review["goal_achievement"].strip(),
        "strengths": review["strengths"],
        "gaps": review["gaps"],
        "risks": review["risks"],
        "recommendations": review["recommendations"],
        "task_reviews": list(normalized_reviews.values()),
    }


def review_project(
    user_goal: str,
    plan: dict,
    agent_results: list,
) -> dict:
    """
    Perform the final project evaluation as AI CEO.

    Returns a validated review dictionary.
    """

    if not isinstance(user_goal, str) or not user_goal.strip():
        raise ValueError("Tujuan proyek tidak boleh kosong.")

    if not isinstance(plan, dict):
        raise ValueError("Plan proyek tidak valid.")

    if not isinstance(agent_results, list):
        raise ValueError("Hasil agent harus berupa list.")

    tasks = plan.get("tasks", [])

    if not isinstance(tasks, list) or not tasks:
        raise ValueError("Plan tidak memiliki daftar tugas.")

    expected_task_ids = {
        task.get("id")
        for task in tasks
        if isinstance(task, dict) and task.get("id")
    }

    if not expected_task_ids:
        raise ValueError("Tidak ditemukan ID tugas yang valid.")

    review_context = {
        "user_goal": user_goal,
        "project_title": plan.get("project_title", ""),
        "objective": plan.get("objective", ""),
        "strategy": plan.get("strategy", ""),
        "final_deliverable": plan.get("final_deliverable", ""),
        "tasks": tasks,
        "agent_results": [
            {
                "task_id": result.get("task_id"),
                "agent_key": result.get("agent_key"),
                "title": result.get("title"),
                "status": result.get("status"),
                "output": str(result.get("output", ""))[:4000],
                "quality": result.get("quality", {}),
                "error": result.get("error", ""),
            }
            for result in agent_results
            if isinstance(result, dict)
        ],
    }

    response = chat(
        messages=[
            {
                "role": "user",
                "content": (
                    "Lakukan evaluasi akhir proyek berikut.\n\n"
                    + json.dumps(
                        review_context,
                        ensure_ascii=False,
                        indent=2,
                    )
                ),
            }
        ],
        system_prompt=CEO_REVIEW_SYSTEM_PROMPT,
        temperature=0.1,
        max_tokens=3000,
    )

    review = _extract_json(response)

    validated = _validate_review(
        review,
        expected_task_ids,
    )

    # Enforce a conservative decision:
    # incomplete tasks or failed CEO task reviews cannot be approved.
    all_tasks_completed = all(
        isinstance(result, dict)
        and result.get("status") == "COMPLETED"
        for result in agent_results
    ) and len(agent_results) == len(expected_task_ids)

    all_reviews_passed = all(
        item["verdict"] == "PASS"
        for item in validated["task_reviews"]
    )

    if (
        validated["decision"] != "APPROVED"
        or validated["score"] < 80
        or not all_tasks_completed
        or not all_reviews_passed
    ):
        validated["decision"] = "NEEDS_REVIEW"

    return validated
