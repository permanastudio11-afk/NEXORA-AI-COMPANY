
import os
import streamlit as st

from nexora.agent_config import get_all_agents
from nexora.service import run_project
from nexora.llm import chat, is_configured
from nexora.workflow_store import (
    init_workflow_store,
    list_workflows,
    get_workflow,
)


st.set_page_config(
    page_title="NEXORA AI COMPANY V2",
    page_icon="🧠",
    layout="wide",
)

st.title("🧠 NEXORA AI COMPANY V2")
st.caption("Intelligent Multi-Agent AI Company")

DB_PATH = os.getenv("DATABASE_PATH", "data/nexora.db")

init_workflow_store(DB_PATH)


def display_ceo_review(review):
    """Display the AI CEO final project evaluation."""

    if not review:
        st.warning("Laporan AI CEO belum tersedia.")
        return

    st.subheader("🧠 AI CEO Final Review")

    decision = review.get("decision", "NEEDS_REVIEW")
    score = review.get("score", 0)

    if decision == "APPROVED":
        st.success("AI CEO APPROVED — Proyek disetujui.")
    else:
        st.warning("AI CEO NEEDS REVIEW — Proyek perlu diperiksa.")

    col1, col2 = st.columns(2)
    col1.metric("CEO Evaluation Score", f"{score}/100")
    col2.metric("CEO Decision", decision)

    st.markdown("### Ringkasan Evaluasi")
    st.write(review.get("summary", ""))

    st.markdown("### Pencapaian Tujuan")
    st.write(review.get("goal_achievement", ""))

    sections = [
        ("Kekuatan Proyek", "strengths"),
        ("Kekurangan Proyek", "gaps"),
        ("Risiko Proyek", "risks"),
        ("Rekomendasi CEO", "recommendations"),
    ]

    for title, key in sections:
        st.markdown(f"### {title}")
        items = review.get(key, [])

        if items:
            for item in items:
                st.write(f"- {item}")
        else:
            st.write("Tidak ada catatan.")

    st.markdown("### Evaluasi Setiap Tugas")

    for item in review.get("task_reviews", []):
        verdict = item.get("verdict", "REVISE")
        task_title = item.get("task_id", "Unknown task")

        with st.expander(
            f"{task_title} — {verdict}"
        ):
            st.write(item.get("reason", ""))


# Sidebar
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
                                "content": "Balas persis: NEXORA AI CONNECTED"
                            }
                        ],
                        max_tokens=50,
                    )

                st.success("Koneksi AI berhasil!")
                st.write(response)

            except Exception as error:
                st.error(f"Koneksi gagal: {error}")


# COMMAND CENTER
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
                progress_area.progress(
                    data["current"] / max(data["total"], 1)
                )

                status_area.info(
                    f"Menjalankan {data['agent']} — "
                    f"{data['title']} "
                    f"({data['current']}/{data['total']})"
                )

            try:
                with st.spinner(
                    "AI CEO sedang menyusun, menjalankan, "
                    "dan mengevaluasi proyek..."
                ):
                    result = run_project(
                        user_goal=goal,
                        db_path=DB_PATH,
                        progress_callback=show_progress,
                    )

                if result["status"] == "COMPLETED":
                    st.success("Workflow selesai dan disetujui AI CEO.")
                else:
                    st.warning(
                        "Workflow selesai dengan status NEEDS_REVIEW."
                    )

                st.subheader("Ringkasan Proyek")

                summary = result["summary"]

                col1, col2, col3, col4 = st.columns(4)

                col1.metric("Total Tugas", summary["total"])
                col2.metric("Berhasil", summary["completed"])
                col3.metric("Gagal", summary["failed"])
                col4.metric("Terblokir", summary["blocked"])

                st.subheader("Rencana AI CEO")

                st.write(
                    "**Judul:**",
                    result["plan"]["project_title"]
                )
                st.write(
                    "**Tujuan:**",
                    result["plan"]["objective"]
                )
                st.write(
                    "**Strategi:**",
                    result["plan"]["strategy"]
                )
                st.write(
                    "**Hasil akhir:**",
                    result["plan"]["final_deliverable"]
                )

                # AI CEO Final Review
                display_ceo_review(
                    result.get("final_review")
                )

                st.subheader("Hasil AI Agent")

                for item in result["results"]:
                    with st.expander(
                        f"{item.get('agent_name', item['agent_key'])} — "
                        f"{item['title']} — {item['status']}"
                    ):
                        st.write(item.get("output", ""))
                        st.json(item.get("quality", {}))

                st.caption(
                    f"Workflow ID: {result['workflow_id']}"
                )

            except Exception as error:
                st.error(f"Workflow gagal: {error}")
                st.info(
                    "Periksa konfigurasi AI provider, "
                    "database, dan detail error."
                )


# AI DEPARTMENTS
elif page == "AI Departments":

    st.header("🏢 AI Departments")

    agents = get_all_agents()

    st.write(f"Jumlah AI Agent: {len(agents)}")

    for agent in agents:
        with st.expander(
            f"{agent['name']} — {agent['department']}"
        ):
            st.write(agent["description"])
            st.write("**Peran:**", agent["role"])
            st.write("**Tanggung jawab:**")

            for responsibility in agent["responsibilities"]:
                st.write(f"- {responsibility}")


# WORKFLOW HISTORY
elif page == "Workflow History":

    st.header("📚 Workflow History")

    workflows = list_workflows(DB_PATH)

    if not workflows:
        st.info("Belum ada workflow tersimpan.")

    else:
        for workflow in workflows:
            workflow_id = workflow["id"]

            with st.expander(
                f"Workflow #{workflow_id} — "
                f"{workflow.get('status', 'UNKNOWN')}"
            ):
                details = get_workflow(DB_PATH, workflow_id)

                if details:
                    workflow_data = details["workflow"]

                    st.markdown("### Informasi Proyek")
                    st.write(
                        "**Judul:**",
                        workflow_data.get("project_title", "")
                    )
                    st.write(
                        "**Status:**",
                        workflow_data.get("status", "")
                    )

                    st.markdown("### Ringkasan Tugas")

                    col1, col2, col3, col4 = st.columns(4)

                    col1.metric(
                        "Total",
                        workflow_data.get("total_tasks", 0)
                    )
                    col2.metric(
                        "Berhasil",
                        workflow_data.get("completed_tasks", 0)
                    )
                    col3.metric(
                        "Gagal",
                        workflow_data.get("failed_tasks", 0)
                    )
                    col4.metric(
                        "Terblokir",
                        workflow_data.get("blocked_tasks", 0)
                    )

                    st.markdown("### Laporan AI CEO")

                    display_ceo_review(
                        workflow_data.get("final_review")
                    )

                    st.markdown("### Hasil Tugas Agent")

                    for task in details["tasks"]:
                        with st.expander(
                            f"{task['agent_key']} — "
                            f"{task['title']} — {task['status']}"
                        ):
                            st.write(task.get("output") or "Belum ada output.")

                            quality = task.get("quality_json")

                            if quality:
                                try:
                                    import json
                                    st.json(json.loads(quality))
                                except (ValueError, TypeError):
                                    st.write(quality)

                    st.markdown("### Riwayat Aktivitas")
                    for event in details["events"]:
                        st.write(
                            f"- {event['created_at']} — "
                            f"{event['event_type']}: "
                            f"{event['message']}"
                        )

                else:
                    st.warning("Detail workflow tidak ditemukan.")
