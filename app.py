
import os
import streamlit as st
import pandas as pd
from nexora.agents import AGENTS
from nexora.db import init_db, fetch_all
from nexora.orchestrator import execute_workflow

st.set_page_config(page_title="NEXORA AI COMPANY", page_icon="🧠", layout="wide")
DB_PATH = os.getenv("DATABASE_PATH", "data/nexora.db")
os.makedirs("data", exist_ok=True)
init_db(DB_PATH)

st.markdown("""
<style>
.block-container {padding-top: 1.5rem; max-width: 1450px;}
.hero {padding: 1.3rem; border-radius: 18px; background: linear-gradient(120deg,#101a36,#203e68); color:white;}
.small-muted {color:#9aa6b2;font-size:.85rem}
div[data-testid="stMetric"] {border:1px solid rgba(128,128,128,.25);padding:12px;border-radius:12px}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="hero"><h1>🧠 NEXORA AI COMPANY</h1><p>Virtual AI workspace • Multi-agent orchestration • DEMO MODE</p><span class="small-muted">Semua output saat ini adalah hasil simulasi lokal, bukan klaim AI eksternal.</span></div>', unsafe_allow_html=True)
st.write("")
tasks = fetch_all(DB_PATH, "SELECT * FROM tasks ORDER BY id DESC")
runs = fetch_all(DB_PATH, "SELECT * FROM agent_runs ORDER BY id DESC")
logs = fetch_all(DB_PATH, "SELECT * FROM activity_logs ORDER BY id DESC LIMIT 30")
completed = sum(1 for t in tasks if t["status"] == "COMPLETED")
c1,c2,c3,c4 = st.columns(4)
c1.metric("Total workflow", len(tasks))
c2.metric("Selesai", completed)
c3.metric("Agent", len(AGENTS))
c4.metric("Mode", "PAPER / DEMO")

tab1,tab2,tab3,tab4 = st.tabs(["🏢 Command Center","🤖 Departemen","📋 Riwayat & Hasil","🧾 Activity Log"])
with tab1:
    st.subheader("Berikan instruksi kepada AI CEO")
    prompt = st.text_area("Instruksi pekerjaan", placeholder="Contoh: Buat rencana peluncuran toko online produk kebutuhan harian...", height=120)
    selected = st.multiselect("Departemen yang dilibatkan", options=[(a[0],a[1]) for a in AGENTS if a[0]!="ceo"],
                              default=[(a[0],a[1]) for a in AGENTS if a[0]!="ceo"],
                              format_func=lambda x: x[1])
    if st.button("🚀 Jalankan workflow DEMO", type="primary", disabled=not prompt.strip()):
        with st.spinner("AI CEO membagi pekerjaan ke departemen..."):
            task_id = execute_workflow(DB_PATH, prompt.strip(), [x[0] for x in selected])
        st.success(f"Workflow DEMO #{task_id} selesai. Buka tab Riwayat & Hasil.")
        st.rerun()
    st.info("Mode DEMO menjalankan agent secara lokal dengan template keluaran. Belum melakukan browsing, mengirim pesan, memublikasikan konten, atau memanggil model AI.")
with tab2:
    st.subheader("Peta departemen")
    cols = st.columns(3)
    for i, (key,name,desc) in enumerate(AGENTS):
        with cols[i%3]:
            st.markdown(f"**{name}**")
            st.caption(desc)
            st.caption("Status: Siap (DEMO)")
with tab3:
    st.subheader("Workflow")
    if tasks:
        st.dataframe(pd.DataFrame(tasks), use_container_width=True, hide_index=True)
        for task in tasks:
            with st.expander(f"#{task['id']} — {task['title'][:90]} [{task['status']}]"):
                outputs = [r for r in runs if r["task_id"] == task["id"]]
                for out in outputs:
                    st.markdown(f"**{out['agent_name']}**")
                    st.write(out["output"])
                    st.divider()
    else:
        st.caption("Belum ada workflow. Masukkan instruksi pada Command Center.")
with tab4:
    if logs:
        st.dataframe(pd.DataFrame(logs), use_container_width=True, hide_index=True)
    else:
        st.caption("Belum ada aktivitas.")

st.divider()
st.caption("NEXORA AI COMPANY • Starter v1 • Local SQLite • DEMO MODE • Jangan gunakan untuk tindakan eksternal tanpa integrasi dan persetujuan.")
