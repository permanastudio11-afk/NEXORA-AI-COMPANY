
import os
import streamlit as st
from nexora.llm import chat, is_configured
from nexora.agent_config import get_all_agents
from nexora.service import run_project
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


# Command Center
if page == "Command Center":

    st.header("🚀 AI CEO Command Center")

    st.write(
        "Masukkan tujuan proyek. AI CEO akan menyusun "
        "rencana dan membagikan tugas kepada AI Agent."
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

            progress_state = {
                "current": 0,
                "total": 0,
            }

            def show_progress(data):
                progress_state["current"] = data["current"]
                progress_state["total"] = data["total"]

                progress_area.progress(
                    data["current"] / max(data["total"], 1)
                )

                status_area.info(
                    f"Menjalankan {data['agent']} — "
                    f"{data['title']} "
                    f"({data['current']}/{data['total']})"
                )

            try:
                with st.spinner("AI CEO sedang menyusun dan menjalankan proyek..."):
                    result = run_project(
                        user_goal=goal,
                        db_path=DB_PATH,
                        progress_callback=show_progress,
                    )

                st.success(
                    f"Workflow selesai dengan status: {result['status']}"
                )

                st.subheader("Ringkasan Proyek")

                summary = result["summary"]

                col1, col2, col3, col4 = st.columns(4)

                col1.metric("Total Tugas", summary["total"])
                col2.metric("Berhasil", summary["completed"])
                col3.metric("Gagal", summary["failed"])
                col4.metric("Terblokir", summary["blocked"])

                st.subheader("Rencana AI CEO")

                st.write("**Judul:**", result["plan"]["project_title"])
                st.write("**Tujuan:**", result["plan"]["objective"])
                st.write("**Strategi:**", result["plan"]["strategy"])
                st.write(
                    "**Hasil akhir:**",
                    result["plan"]["final_deliverable"],
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
                    "Periksa konfigurasi API AI dan detail error "
                    "sebelum menjalankan ulang."
                )


# AI Departments
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


# Workflow History
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
                    st.json(details)
                else:
                    st.warning("Detail workflow tidak ditemukan.")
