
"""NEXORA V2 - AI CEO Task Planner."""

import json

from .agent_config import AGENT_CONFIG
from .llm import LLMError, chat


PLANNER_SYSTEM_PROMPT = """
Anda adalah AI CEO dan Chief Strategy Officer NEXORA AI COMPANY.

Tugas Anda:
1. Memahami tujuan pengguna.
2. Menentukan departemen AI yang relevan.
3. Memecah pekerjaan menjadi tugas yang spesifik.
4. Menentukan urutan dan dependensi pekerjaan.
5. Menetapkan kriteria keberhasilan setiap tugas.
6. Memperhatikan risiko dan keterbatasan informasi.

Pilih hanya agent yang benar-benar diperlukan.
Jangan mengarang fakta.
Jangan mengklaim tindakan eksternal sudah dilakukan.
Jangan membuat tugas yang tidak berhubungan dengan tujuan pengguna.

Balas HANYA dengan JSON valid menggunakan struktur:

{
  "project_title": "Judul proyek",
  "objective": "Tujuan utama",
  "strategy": "Strategi pelaksanaan",
  "tasks": [
    {
      "id": "task_1",
      "agent": "research",
      "title": "Judul tugas",
      "description": "Instruksi terperinci untuk agent",
      "depends_on": [],
      "priority": "HIGH",
      "acceptance_criteria": [
        "Kriteria keberhasilan"
      ]
    }
  ],
  "risks": [
    "Risiko yang perlu diperhatikan"
  ],
  "final_deliverable": "Hasil akhir yang diharapkan"
}

Agent yang tersedia:
ceo, research, content, marketing, sales, finance, hr,
project, admin, business, design, developer, video.

AI CEO tidak boleh dimasukkan sebagai tugas spesialis.
"""


def _extract_json(text: str) -> dict:
    """Extract and validate JSON returned by the AI."""

    cleaned = text.strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1]
        if cleaned.rstrip().endswith("```"):
            cleaned = cleaned.rstrip()[:-3].strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError("AI Planner menghasilkan JSON tidak valid.") from exc

    if not isinstance(data, dict):
        raise ValueError("Format rencana harus berupa objek JSON.")

    return data


def validate_plan(plan: dict) -> dict:
    """Validate the AI-generated execution plan."""

    if not isinstance(plan, dict):
        raise ValueError("Rencana harus berupa objek.")

    required_fields = [
        "project_title",
        "objective",
        "strategy",
        "tasks",
        "risks",
        "final_deliverable",
    ]

    for field in required_fields:
        if field not in plan:
            raise ValueError(f"Field wajib tidak ditemukan: {field}")

    if not isinstance(plan["tasks"], list) or not plan["tasks"]:
        raise ValueError("Rencana harus memiliki minimal satu tugas.")

    if len(plan["tasks"]) > 20:
        raise ValueError("Maksimal 20 tugas per workflow.")

    valid_agents = set(AGENT_CONFIG.keys()) - {"ceo"}
    task_ids = set()

    for task in plan["tasks"]:
        if not isinstance(task, dict):
            raise ValueError("Format tugas tidak valid.")

        required_task_fields = [
            "id",
            "agent",
            "title",
            "description",
            "depends_on",
            "priority",
            "acceptance_criteria",
        ]

        for field in required_task_fields:
            if field not in task:
                raise ValueError(f"Field tugas tidak ditemukan: {field}")

        task_id = task["id"]
        agent = task["agent"]

        if not isinstance(task_id, str) or not task_id.strip():
            raise ValueError("ID tugas tidak valid.")

        if task_id in task_ids:
            raise ValueError(f"ID tugas duplikat: {task_id}")

        task_ids.add(task_id)

        if agent not in valid_agents:
            raise ValueError(f"Agent tidak dikenal: {agent}")

        if not isinstance(task["title"], str) or not task["title"].strip():
            raise ValueError("Judul tugas tidak valid.")

        if not isinstance(task["description"], str):
            raise ValueError("Deskripsi tugas harus berupa teks.")

        if not isinstance(task["depends_on"], list):
            raise ValueError("Dependensi harus berupa daftar.")

        if not isinstance(task["acceptance_criteria"], list):
            raise ValueError("Kriteria penerimaan harus berupa daftar.")

        if task["priority"] not in ("LOW", "MEDIUM", "HIGH", "CRITICAL"):
            raise ValueError("Prioritas tugas tidak valid.")

    for task in plan["tasks"]:
        for dependency in task["depends_on"]:
            if dependency not in task_ids:
                raise ValueError(
                    f"Dependensi {dependency} tidak ditemukan."
                )

            if dependency == task["id"]:
                raise ValueError("Tugas tidak boleh bergantung pada dirinya sendiri.")

    return plan


def create_plan(user_goal: str) -> dict:
    """Generate a structured project plan using the AI CEO."""

    if not isinstance(user_goal, str) or not user_goal.strip():
        raise ValueError("Instruksi pengguna tidak boleh kosong.")

    if len(user_goal) > 12000:
        raise ValueError("Instruksi terlalu panjang. Maksimal 12000 karakter.")

    agent_summary = "\n".join(
        f"- {key}: {config['description']}"
        for key, config in AGENT_CONFIG.items()
        if key != "ceo"
    )

    prompt = f"""
TUJUAN PENGGUNA:
{user_goal.strip()}

DEPARTEMEN YANG TERSEDIA:
{agent_summary}

Buat rencana kerja yang realistis, terstruktur, dan dapat dieksekusi.
Gunakan hanya agent yang relevan.
Pastikan setiap dependensi merujuk pada ID tugas yang benar.
"""

    response = chat(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        system_prompt=PLANNER_SYSTEM_PROMPT,
        temperature=0.2,
        max_tokens=3000,
    )

    try:
        plan = _extract_json(response)
        return validate_plan(plan)
    except (ValueError, TypeError) as exc:
        raise LLMError(
            f"Rencana AI tidak lolos validasi: {exc}"
        ) from exc
