
"""NEXORA V2 - Intelligent Multi-Agent AI Company Dashboard."""

import os
import json
import streamlit as st

from nexora.agent_config import get_all_agents
from nexora.service import run_project
from nexora.llm import chat, is_configured
from nexora.workflow_store import (
    init_workflow_store,
    list_workflows,
    get_workflow,
)


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="NEXORA AI COMPANY V2",
    page_icon="🧠",
    layout="wide",
)

DB_PATH = os.getenv("DATABASE_PATH", "data/nexora.db")

init_workflow_store(DB_PATH)


# =========================================================
# DISPLAY HELPERS
# =========================================================

def display_list(title, items):
    st.write(f"**{title}**")

    if not items:
        st.write("- Tidak ada data.")
        return

    for item in items:
        st.write(f"- {item}")


def display_ceo_review(review):
    """Display the final review from AI CEO."""

    if not isinstance(review, dict) or not review:
        st.warning("Laporan AI CEO belum tersedia.")
        return

    decision = review.get("decision", "NEEDS_REVIEW")
    score = review.get("score", 0)

    st.subheader("🧠 AI CEO Final Review")

    if decision == "APPROVED":
        st.success("AI CEO menyetujui hasil proyek.")
    else:
        st.warning("Proyek membutuhkan pemeriksaan lebih lanjut.")

    col1, col2 = st.columns(2)

    col1.metric("CEO Score", f"{score}/100")
    col2.metric("CEO Decision", decision)

    st.write("**Ringkasan:**")
    st.write(review.get("summary", "-"))

    st.write("**Pencapaian tujuan:**")
    st.write(review.get("goal_achievement", "-"))

    display_list("Kekuatan", review.get("strengths", []))
    display_list("Kekurangan", review.get("gaps", []))
    display_list("Risiko", review.get("risks", []))
    display_list("Rekomendasi", review.get("recommendations", []))

    task_reviews = review.get("task_reviews", [])

    if task_reviews:
        st.write("**Evaluasi setiap tugas:**")

        for task in task_reviews:
            if not isinstance(task, dict):
                continue

            st.write(
                f"- **{task.get('task_id', 'Unknown')}** "
                f"| {task.get('verdict', 'UNKNOWN')} "
                f"| {task.get('reason', '')}"
            )


def parse_json(value, default=None):
    """Safely parse JSON stored in database."""

    if default is None:
        default = {}

    if isinstance(value, (dict, list)):
        return value

    if not value:
        return default

    try:
        return json.loads(value)
    except (ValueError, TypeError):
        return default


# =========================================================
# MAIN HEADER
# =========================================================

st.title("🧠 NEXORA AI COMPANY V2")
st.caption("Intelligent Multi-Agent AI Company")


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.title("NEXORA CONTROL")
    st.write("AI Company System V2")

    st.divider()

    page = st.radio(
        "Navigasi",
        [
            "Command Center",
            "AI Departments",
            "Workflow History",
        ],
    )

    st.divider()

    st.caption("V2 Intelligent Agents")

    st.divider()

    st.subheader("AI Connection")

    if st.button("Test AI Connection"):

        if not is_configured():

            st.error("API Key belum terkonfigurasi.")

        else:

            try:
                with st.spinner("Menghubungkan ke AI provider..."):

                    response = chat(
                        messages=[
                            {
                                "role": "user",
                                "content": (
                                    "Balas persis: "
                                    "NEXORA AI CONNECTED"
                                ),
                            }
                        ],
                        max_tokens=256
                    )

                if not isinstance(response, str) or not response.strip():
                    raise ValueError("Jawaban AI kosong atau tidak valid.")

                st.success("Koneksi AI berhasil!")
                st.write(response)

            except Exception as error:

                st.error(f"Koneksi gagal: {error}")


# =========================================================
# COMMAND CENTER
# =========================================================

if page == "Command Center":

    st.header("🚀 AI CEO Command Center")

    st.write(
        "Masukkan tujuan proyek. AI CEO akan menyusun rencana, "
        "membagikan tugas kepada AI Agent, dan mengevaluasi "
        "hasil pekerjaan secara menyeluruh."
    )

    goal = st.text_area(
        "Instruksi proyek",
        placeholder=(
            "Contoh: Buat strategi pemasaran digital "
            "untuk toko sembako selama 30 hari."
        ),
        height=160,
    )

    if st.button("JALANKAN AI COMPANY", type="primary"):

        if not goal.strip():

            st.warning("Masukkan instruksi proyek terlebih dahulu.")

        else:

            progress_area = st.empty()
            status_area = st.empty()

            def show_progress(data):

                current = data.get("current", 0)
                total = data.get("total", 1)

                progress_area.progress(
                    current / max(total, 1)
                )

                status_area.info(
                    f"Menjalankan {data.get('agent', 'AI Agent')} — "
                    f"{data.get('title', '')} "
                    f"({current}/{total})"
                )

            try:

                with st.spinner(
                    "AI CEO sedang menyusun dan menjalankan proyek..."
                ):

                    result = run_project(
                        user_goal=goal,
                        db_path=DB_PATH,
                        progress_callback=show_progress,
                    )

                st.success(
                    f"Workflow selesai dengan status: "
                    f"{result.get('status', 'UNKNOWN')}"
                )

                # PROJECT SUMMARY

                st.subheader("📊 Ringkasan Proyek")

                summary = result.get("summary", {})

                col1, col2, col3, col4 = st.columns(4)

                col1.metric(
                    "Total Tugas",
                    summary.get("total", 0),
                )

                col2.metric(
                    "Berhasil",
                    summary.get("completed", 0),
                )

                col3.metric(
                    "Gagal",
                    summary.get("failed", 0),
                )

                col4.metric(
                    "Terblokir",
                    summary.get("blocked", 0),
                )

                # CEO PLAN

                plan = result.get("plan", {})

                st.subheader("📋 Rencana AI CEO")

                st.write(
                    "**Judul:**",
                    plan.get("project_title", "-"),
                )

                st.write(
                    "**Tujuan:**",
                    plan.get("objective", "-"),
                )

                st.write(
                    "**Strategi:**",
                    plan.get("strategy", "-"),
                )

                st.write(
                    "**Hasil akhir:**",
                    plan.get("final_deliverable", "-"),
                )

                # CEO FINAL REVIEW

                display_ceo_review(
                    result.get("final_review")
                )

                # AGENT RESULTS

                st.subheader("🤖 Hasil AI Agent")

                for item in result.get("results", []):

                    if not isinstance(item, dict):
                        continue

                    agent_name = item.get(
                        "agent_name",
                        item.get("agent_key", "AI Agent"),
                    )

                    with st.expander(
                        f"{agent_name} — "
                        f"{item.get('title', 'Tugas')} — "
                        f"{item.get('status', 'UNKNOWN')}"
                    ):

                        st.write(
                            item.get("output", "Tidak ada output.")
                        )

                        st.write("**Quality Evaluation**")

                        st.json(
                            item.get("quality", {})
                        )

                        if item.get("error"):
                            st.error(item["error"])

                st.caption(
                    f"Workflow ID: {result.get('workflow_id', '-')}"
                )

            except Exception as error:

                st.error(f"Workflow gagal: {error}")

                st.info(
                    "Periksa konfigurasi AI dan log aplikasi "
                    "untuk mengetahui penyebab kesalahan."
                )


# =========================================================
# AI DEPARTMENTS
# =========================================================

elif page == "AI Departments":

    st.header("🏢 AI Departments")

    agents = get_all_agents()

    if not isinstance(agents, dict):
        st.error("Format konfigurasi AI Agent tidak valid.")

    else:

        st.write(f"Jumlah AI Agent: {len(agents)}")

        # agents is a dictionary: key -> agent configuration
        for agent_key, agent in agents.items():

            if not isinstance(agent, dict):
                continue

            with st.expander(
                f"{agent.get('name', agent_key)} — "
                f"{agent.get('department', 'General')}"
            ):

                st.write(
                    agent.get("description", "-")
                )

                st.write(
                    "**Peran:**",
                    agent.get("role", "-"),
                )

                st.write("**Tanggung jawab:**")

                responsibilities = agent.get(
                    "responsibilities",
                    [],
                )

                if isinstance(responsibilities, list):

                    for responsibility in responsibilities:
                        st.write(f"- {responsibility}")

                else:
                    st.write(responsibilities)


# =========================================================
# WORKFLOW HISTORY
# =========================================================

elif page == "Workflow History":

    st.header("📚 Workflow History")

    workflows = list_workflows(DB_PATH)

    if not workflows:

        st.info("Belum ada workflow tersimpan.")

    else:

        for workflow in workflows:

            workflow_id = workflow.get("id")

            with st.expander(
                f"Workflow #{workflow_id} — "
                f"{workflow.get('project_title', 'Untitled')} — "
                f"{workflow.get('status', 'UNKNOWN')}"
            ):

                details = get_workflow(DB_PATH, workflow_id)

                if not details:

                    st.warning(
                        "Detail workflow tidak ditemukan."
                    )

                    continue

                # Support both flat and nested workflow formats.
                workflow_data = details.get("workflow", details)

                st.write(
                    "**Judul:**",
                    workflow_data.get("project_title", "-"),
                )

                st.write(
                    "**Status:**",
                    workflow_data.get("status", "-"),
                )

                col1, col2, col3, col4 = st.columns(4)

                col1.metric(
                    "Total",
                    workflow_data.get("total_tasks", 0),
                )

                col2.metric(
                    "Berhasil",
                    workflow_data.get("completed_tasks", 0),
                )

                col3.metric(
                    "Gagal",
                    workflow_data.get("failed_tasks", 0),
                )

                col4.metric(
                    "Terblokir",
                    workflow_data.get("blocked_tasks", 0),
                )

                # CEO REVIEW

                review = details.get(
                    "final_review",
                    workflow_data.get("final_review"),
                )

                if review is None:
                    review = parse_json(
                        workflow_data.get("final_review_json"),
                        {},
                    )

                if isinstance(review, str):
                    review = parse_json(review, {})

                display_ceo_review(review)

                # TASK HISTORY

                st.subheader("📝 Riwayat Tugas")

                tasks = details.get("tasks", [])

                for task in tasks:

                    quality = parse_json(
                        task.get("quality_json"),
                        {},
                    )

                    with st.expander(
                        f"{task.get('title', task.get('task_id', 'Task'))} "
                        f"— {task.get('status', 'UNKNOWN')}"
                    ):

                        st.write(
                            "**Agent:**",
                            task.get("agent_key", "-"),
                        )

                        st.write(
                            "**Deskripsi:**",
                            task.get("description", "-"),
                        )

                        st.write(
                            "**Hasil:**",
                            task.get("output", "-"),
                        )

                        st.write("**Quality:**")
                        st.json(quality)

                        if task.get("error"):
                            st.error(task["error"])

                # EVENT HISTORY

                st.subheader("📌 Workflow Events")

                events = details.get("events", [])

                if events:

                    for event in events:

                        st.write(
                            f"- {event.get('created_at', '')} "
                            f"| {event.get('event_type', '')} "
                            f"| {event.get('message', '')}"
                        )

                else:

                    st.info("Belum ada event tersimpan.")
