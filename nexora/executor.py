
"""NEXORA V2 - Specialist Agent Executor."""

from .agent_config import get_agent
from .llm import chat
from .quality import evaluate_output


MAX_OUTPUT_CHARS = 12000
MAX_CONTEXT_CHARS = 8000
MAX_RETRIES = 1


def execute_agent_task(
    task: dict,
    project_context: str = "",
    previous_results: list = None,
) -> dict:
    """Execute one specialist task and evaluate its result."""

    previous_results = previous_results or []

    if not isinstance(task, dict):
        raise ValueError("Format tugas tidak valid.")

    agent_key = task.get("agent", "")

    if agent_key == "ceo":
        raise ValueError("AI CEO bukan agent spesialis executor.")

    agent = get_agent(agent_key)

    title = task.get("title", "")
    description = task.get("description", "")

    if not isinstance(title, str) or not title.strip():
        raise ValueError("Judul tugas wajib diisi.")

    if not isinstance(description, str) or not description.strip():
        raise ValueError("Deskripsi tugas wajib diisi.")

    context_parts = []

    if project_context:
        context_parts.append(
            "KONTEKS PROYEK:\n" + str(project_context)
        )

    if previous_results:
        context_parts.append("HASIL PEKERJAAN SEBELUMNYA:")

        for result in previous_results[-5:]:
            if not isinstance(result, dict):
                continue

            context_parts.append(
                f"\nAgent: {result.get('agent_key', 'unknown')}\n"
                f"Hasil: {str(result.get('output', ''))[:1500]}"
            )

    context = "\n\n".join(context_parts)

    if len(context) > MAX_CONTEXT_CHARS:
        context = context[:MAX_CONTEXT_CHARS]

    system_prompt = (
        agent["system_prompt"]
        + "\n\nATURAN EKSEKUSI NEXORA:"
        + "\n- Kerjakan hanya tugas yang diberikan."
        + "\n- Gunakan konteks yang tersedia."
        + "\n- Pisahkan fakta dan asumsi."
        + "\n- Jangan mengarang sumber atau data."
        + "\n- Jangan mengklaim tindakan eksternal sudah dilakukan."
        + "\n- Jika informasi kurang, jelaskan keterbatasannya."
        + "\n- Berikan hasil terstruktur dan dapat diperiksa."
    )

    user_prompt = f"""
JUDUL TUGAS:
{title}

INSTRUKSI:
{description}

KONTEKS TAMBAHAN:
{context if context else "Tidak ada konteks tambahan."}

HASIL YANG DIHARAPKAN:
Berikan hasil kerja yang jelas, terstruktur, dan relevan.
"""

    last_error = None

    for attempt in range(MAX_RETRIES + 1):
        try:
            output = chat(
                messages=[
                    {
                        "role": "user",
                        "content": user_prompt,
                    }
                ],
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=2500,
            )

            output = output[:MAX_OUTPUT_CHARS]

            quality = evaluate_output(
                agent_key=agent_key,
                output=output,
                task=description,
            )

            if quality["passed"]:
                return {
                    "task_id": task.get("id"),
                    "agent_key": agent_key,
                    "agent_name": agent["name"],
                    "title": title,
                    "status": "COMPLETED",
                    "output": output,
                    "quality": quality,
                    "attempts": attempt + 1,
                    "error": None,
                }

            last_error = "Hasil tidak memenuhi pemeriksaan kualitas."

            if attempt < MAX_RETRIES:
                user_prompt += (
                    "\n\nPERBAIKI HASIL SEBELUMNYA. "
                    "Pastikan jawaban lebih lengkap, relevan, "
                    "dan memenuhi instruksi."
                )

        except Exception as exc:
            last_error = str(exc)

            if attempt >= MAX_RETRIES:
                break

    return {
        "task_id": task.get("id"),
        "agent_key": agent_key,
        "agent_name": agent["name"],
        "title": title,
        "status": "FAILED",
        "output": "",
        "quality": {
            "score": 0,
            "passed": False,
            "issues": [last_error or "Eksekusi gagal."],
            "recommendation": "REVIEW",
        },
        "attempts": MAX_RETRIES + 1,
        "error": last_error,
    }
