"""Home page for Computer Systems Fundamentals."""

import streamlit as st

def render():
    st.title("Computer Systems Fundamentals")
    
    st.markdown("""
    Demystifying the machine. From raw logic gates up to complete operating systems.
    """)


    # ── Global Level Selector inside modules/home.py ───────────────────────────
    st.divider()

    # Map the 3 slider states down to the 2 track options on the home page
    #current_global_level = st.session_state.get("level", "Intermediate")
    
    # ── BEGINNER TRACK (Mandatory SQA Spec) ─────────────────────────────────
    if st.session_state["level"] == "Beginner":
        st.info(
            "**The Core Fundamentals:** Think of a computer as a giant machine that follows instructions. "
            "This track covers all the mandatory building blocks required to understand hardware, software, and basic logic."
        )

        st.markdown("## What You'll Learn")
        c1, c2, c3 = st.columns(3)

        with c1:
            st.markdown("""
            ### The Hardware Stack
            - **CPU Core:** Registers, ALU, Control Unit
            - **Memory Hierarchy:** RAM, ROM, & Storage
            - **Data Transfer:** System Buses & I/O
            - **Execution:** The Fetch-Execute Cycle
            """)

        with c2:
            st.markdown("""
            ### Number Systems & Logic
            - **Number Bases:** Binary, Hexadecimal, Decimal
            - **Logic Gates:** AND, OR, NOT, XOR
            - **Arithmetic:** 8-bit Adders & Two's Complement
            - **Data Types:** ASCII Character encoding
            """)

        with c3:
            st.markdown("""
            ### Software & OS
            - **OS Layers:** Kernel vs User Space
            - **Memory:** Virtual Memory & Paging
            - **File Systems:** Hierarchy & Permissions
            - **Practical:** Software & OS Installation
            """)

        st.divider()
        st.markdown("## Learning Journey")
        journey = [
            "1. **Number Systems:** Translate human data to machine data.",
            "2. **Logic Gates:** See how transistors make decisions.",
            "3. **The ALU:** Watch binary addition happen in real-time.",
            "4. **The CPU:** Understand how the ALU, Registers, and Memory communicate.",
            "5. **Operating Systems:** Learn how software manages all this hardware."
        ]
        for step in journey:
            st.markdown(step)

        st.divider()

    # ── ADVANCED TRACK (Beyond the Spec) ────────────────────────────────────
    else:
        st.success(
            "**Under the Hood:** Taking the training wheels off. This track explores low-level programming, "
            "complex data representations, and modern processor design."
        )

        st.markdown("## Advanced Topics")
        ac1, ac2, ac3 = st.columns(3)

        with ac1:
            st.markdown("""
            ### Low-Level Execution
            - **Assembly Language:** Mnemonics to Opcodes
            - **Machine Code:** Reading raw hex instructions
            - **Stack Operations:** LIFO, PUSH, POP
            - **Subroutines:** Memory jumps and returns
            """)

        with ac2:
            st.markdown("""
            ### Modern CPU Architecture
            - **Pipelining:** Overlapping instructions
            - **Hazards:** Data & Control bottlenecks
            - **Hardware Interrupts:** NMI & DMA
            - **Performance:** Clock rate & CPI throughput
            """)

        with ac3:
            st.markdown("""
            ### Complex Systems
            - **Advanced Math:** IEEE-754 Floating Point
            - **Bitwise Logic:** Shifts, Masks, and bit manipulation
            - **Appliance Design:** Bootloaders & Custom OS initialization
            - **I/O Ports:** Direct hardware communication
            """)

        st.divider()
        st.markdown("## Interactive Tools Available")
        st.markdown("""
        * **Assembly Walkthrough:** Write and execute raw 8-bit machine code instructions, watching the CPU registers update cycle by cycle.
        * **IEEE-754 Explorer:** See exactly how the computer splits 32 bits into a sign, exponent, and mantissa to represent decimals like `3.14159`.
        * **Advanced ALU:** Perform bitwise operations (`SHL`, `SHR`, `AND` masking) and check status flags (Zero, Carry, Overflow, Negative).
        """)

        st.divider()

    # ── Architecture Diagram ────────────────────────────────────────────────
    st.markdown("## System Architecture at a Glance")
    st.info("Diagram placeholder")