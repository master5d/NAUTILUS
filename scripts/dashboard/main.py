import streamlit as st
import subprocess
import requests
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="Agentic AI v3.3 Dashboard", layout="wide")

st.title("🚀 Agentic AI v3.3 — Solo Vibe Coder Dashboard")

# --- Service Status Sidebar ---
st.sidebar.header("Service Status")

def check_service(url, name):
    try:
        response = requests.get(url, timeout=2)
        if response.status_code == 200:
            st.sidebar.success(f"{name}: Online")
            return True
        else:
            st.sidebar.warning(f"{name}: {response.status_code}")
    except:
        st.sidebar.error(f"{name}: Offline")
    return False

lite_llm = check_service("http://localhost:4000/health", "LiteLLM")
llama_server = check_service("http://localhost:8080/health", "LLaMA Server")
langfuse = check_service("http://localhost:3000/api/public/health", "Langfuse")

st.sidebar.divider()
st.sidebar.info(f"Last update: {datetime.now().strftime('%H:%M:%S')}")

# --- Main Dashboard ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("📝 Sprint Status (Phase 1)")
    tasks = [
        {"Task": "Environment Setup", "Status": "✅ Done"},
        {"Task": "Observability (Langfuse)", "Status": "✅ Done"},
        {"Task": "Editor Stack (Zed/Aider/Claude)", "Status": "✅ Done"},
        {"Task": "Gmail AI Ingest", "Status": "⏳ Pending"},
        {"Task": "PARA Consolidation", "Status": "⏳ Starting"}
    ]
    st.table(pd.DataFrame(tasks))

with col2:
    st.subheader("🕵️ Agent activity")
    # Placeholder for reading actual logs
    log_path = "/mnt/c/Warp Projects/Efforts/Ongoing/SOVRN/Calendar/Logs/activity.log"
    if os.path.exists(log_path):
        with open(log_path, "r") as f:
            logs = f.readlines()[-10:]
            st.code("".join(logs), language="text")
    else:
        st.write("No agent activity logs found in /Calendar/Logs/.")

st.divider()

# --- Weekly Digest Preview ---
st.subheader("📊 Weekly Digest Preview")
st.write("Next run: Monday Sep 04, 09:00")
st.button("Run health check manual")

# --- LiteLLM Config Quick Look ---
with st.expander("🔍 LiteLLM Model Pool"):
    st.code("""
- Fast Pool: Cerebras, Groq, NIM
- Primary Brain: Gemini 2.5 Flash
- Local Fallback: Qwen3-Coder-30B
    """, language="text")
