import sys, os, importlib
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st

st.set_page_config(
    page_title="Computer System Fundamentals",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.reg-card { background:#f8f9fa; border:1px solid #dee2e6; border-radius:6px; padding:8px 12px; margin-bottom:6px; }
.reg-name { font-size:11px; color:#6c757d; font-weight:600; letter-spacing:.05em; }
.reg-val  { font-family:monospace; font-size:15px; font-weight:700; color:#212529; }
.phase-fetch     { background:#cff4fc; color:#055160; border-radius:4px; padding:2px 8px; font-size:11px; font-weight:600; }
.phase-decode    { background:#fff3cd; color:#664d03; border-radius:4px; padding:2px 8px; font-size:11px; font-weight:600; }
.phase-execute   { background:#d1e7dd; color:#0a3622; border-radius:4px; padding:2px 8px; font-size:11px; font-weight:600; }
.phase-writeback { background:#e2d9f3; color:#3d0a91; border-radius:4px; padding:2px 8px; font-size:11px; font-weight:600; }
.phase-interrupt { background:#f8d7da; color:#58151c; border-radius:4px; padding:2px 8px; font-size:11px; font-weight:600; }
.phase-dma       { background:#fde8d8; color:#7c2d12; border-radius:4px; padding:2px 8px; font-size:11px; font-weight:600; }
.cache-hit  { color:#198754; font-weight:700; }
.cache-miss { color:#dc3545; font-weight:700; }
.info-box { background:#e8f4f8; border-left:3px solid #0d6efd; padding:8px 12px; border-radius:0 4px 4px 0; margin:8px 0; font-size:13px; }
</style>
""", unsafe_allow_html=True)

MODULES = [
    ("Home",                       "modules.home"),
#    ("Live CPU Simulator",       "modules.simulator"),
    ("ALU",           "modules.alu"),
    
#    ("Fetch-Decode-Execute",      "modules.fde"),
#    ("Memory & Storage Types",   "modules.memory_types"),
#    ("Cache Hierarchy",           "modules.cache"),
#    ("Stack & Heap",             "modules.stack_heap"),
#    ("Interrupts & I/O",         "modules.interrupts"),
#    ("Buses (Data/Address/Control)", "modules.buses"),
#    ("Assembly Walkthrough",     "modules.assembly"),
#    ("Von Neumann vs Harvard",   "modules.architecture"),
#    ("DMA & Direct Access",      "modules.dma"),

]

MODULE_LABELS = [label for label, _ in MODULES]
MODULE_MAP    = {label: mod for label, mod in MODULES}

with st.sidebar:
    st.title("CPU Fundamentals")
    st.caption("Interactive Computer Architecture Simulator")
    st.divider()
    selected = st.radio("Module", MODULE_LABELS, label_visibility="collapsed")
    st.divider()
    st.markdown("**Information Level**")
    level = st.select_slider("", ["Beginner", "Intermediate", "Advanced"],
                              value="Intermediate", label_visibility="collapsed")
    st.session_state["level"] = level
    lvl_info = {
        "Beginner":     "Plain-English with analogies.",
        "Intermediate": "Technical detail with worked examples.",
        "Advanced":     "Full hardware-level depth and edge cases.",
    }
    st.info(lvl_info[level])

module_path = MODULE_MAP.get(selected, "modules.home")
page = importlib.import_module(module_path)
page.render()
