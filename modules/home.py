"""Home page for Computer Architecture Fundamentals."""

import streamlit as st


def render():
    level = st.session_state.get("level", "Intermediate")

    # ── Hero ────────────────────────────────────────────────────────────────
    st.title("Computer Architecture Fundamentals")

    st.markdown("""
    Learn how things work, I guess
    """)

    if level == "Beginner":
        st.info(
            "Think of a computer as a giant machine that follows instructions. "
            "This course starts with the basic building blocks and gradually "
            "works up to modern CPU design."
        )

    # ── Overview ────────────────────────────────────────────────────────────
    st.divider()
    st.markdown("## What You'll Learn")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("""
        ### CPU Fundamentals

        - Registers
        - ALU
        - Control Unit
        - Clock Cycle
        """)

    with c2:
        st.markdown("""
        ### Memory Systems

        - RAM
        - Cache
        - Virtual Memory
        - Memory Hierarchy
        """)

    with c3:
        st.markdown("""
        ### Instruction Execution

        - Fetch
        - Decode
        - Execute
        - Write Back
        """)

    # ── Learning Journey ────────────────────────────────────────────────────
    st.divider()
    st.markdown("## Learning Journey")

    journey = [
        "1. Binary & Number Systems",
        "2. Logic Gates",
        "3. Digital Circuits",
        "4. CPU Components",
        "5. Instruction Set Architecture (ISA)",
        "6. Memory Hierarchy",
        "7. Pipelining",
        "8. etc.",
    ]

    for step in journey:
        st.markdown(step)

    # ── Architecture Diagram ────────────────────────────────────────────────
    st.divider()
    st.markdown("## Computer at a Glance")

    st.code("We need a diagram")

    # ── Advanced Preview ────────────────────────────────────────────────────
    if level in ("Intermediate", "Advanced"):
        st.divider()
        st.markdown("## Topics You'll Eventually Explore")

        ac1, ac2 = st.columns(2)

        with ac1:
            st.markdown("""
            ### Processor Design

            - Pipelines
            - Hazards
            - Branch Prediction
            - Superscalar CPUs
            """)

        with ac2:
            st.markdown("""
            ### Performance

            - CPI
            - Clock Rate
            - Throughput
            """)

    # ── Quick Facts ─────────────────────────────────────────────────────────
    st.divider()
    st.markdown("## Quick Facts")

    f1, f2, f3 = st.columns(3)

    f1.metric("Bits in a Byte", "8")
    f2.metric("Hex Digits per Byte", "2")
    f3.metric("Common Word Size", "64-bit")

    # ── Start Learning ──────────────────────────────────────────────────────
    st.divider()
    st.success(
        "Use the navigation menu to begin with x and work your way "
        "toward modern CPU architecture."
    )