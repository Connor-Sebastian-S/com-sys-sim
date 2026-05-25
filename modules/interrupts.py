"""Interrupts & I/O page."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import streamlit as st
import pandas as pd
import time
from core.cpu import CPU, InterruptType


INTERRUPT_TABLE = [
    ("NMI",    0, 0x00, "Non-maskable — hardware fault, power failure, memory error. Cannot be ignored.", "🔴"),
    ("IRQ0",   1, 0x02, "Timer — fires every 1ms (PIT/APIC). OS scheduler tick. Cannot be disabled easily.", "🟡"),
    ("IRQ1",   2, 0x04, "Keyboard controller — key pressed or released.", "🔵"),
    ("IRQ2",   3, 0x06, "Serial port (COM1) — byte received.", "🔵"),
    ("IRQ3",   4, 0x08, "Disk controller — read/write complete.", "🟢"),
    ("IRQ4",   5, 0x0A, "Network card — packet received.", "🟢"),
    ("SW",     6, 0x0C, "Software interrupt — system call from user program (e.g. INT 0x80 on x86).", "⚪"),
    ("DMA_DONE",7,0x0E,"DMA transfer complete — device signals CPU that block copy is done.", "🟣"),
]


def render():
    st.title("Interrupts & I/O")
    level = st.session_state.get("level","Intermediate")

    if level == "Beginner":
        st.info("An **interrupt** is like a tap on the shoulder while you're reading. "
                "You bookmark your page (save state), deal with whoever tapped you (interrupt handler), "
                "then return to exactly where you left off (restore state). "
                "Computers use this so the CPU doesn't have to constantly check if a key was pressed — "
                "the keyboard tells the CPU when it's ready.")

    # Polling vs Interrupts
    st.markdown("## Polling vs Interrupts")
    pc1,pc2 = st.columns(2)
    with pc1:
        st.markdown("### Polling (busy-wait)")
        st.code("""while True:
    if keyboard.has_key_ready():
        key = keyboard.read()
        handle(key)
    # CPU spins here wasting cycles
    # Nothing else can run""", language="python")
        st.error("**Problem:** CPU is 100% busy *waiting*. Cannot do other work. Wastes energy.")
    with pc2:
        st.markdown("### Interrupts (event-driven)")
        st.code("""# CPU does useful work...
def keyboard_isr():          # Interrupt Service Routine
    key = keyboard.read()    # Called ONLY when key pressed
    handle(key)
    return_to_previous()     # Resume what was running

# CPU is free to do other things
# until IRQ1 fires""", language="python")
        st.success("**Benefit:** CPU does useful work until hardware needs attention.")

    # Interrupt sequence
    st.divider()
    st.markdown("## The Interrupt Sequence (step by step)")

    interrupt_steps = [
        ("Hardware asserts IRQ line",
         "The keyboard controller puts a signal on the **IRQ1 line** (physical wire to the CPU's interrupt controller)."),
        ("PIC acknowledges",
         "The **Programmable Interrupt Controller (PIC/APIC)** arbitrates priority. "
         "If IRQ1 has higher priority than current task, it asserts **INTR** on the CPU."),
        ("CPU checks interrupt flag (I bit)",
         "After the current instruction's writeback, the CPU checks if the **I flag** is set. "
         "If clear (interrupts disabled), the IRQ waits. If set, proceed."),
        ("CPU sends INTA (Interrupt Acknowledge)",
         "CPU asserts **INTA** on the control bus. PIC responds with the **interrupt vector number** (e.g. 0x04 for IRQ1)."),
        ("Save context (push PC, FLAGS)",
         "CPU **pushes PC** (return address) and **FLAGS** onto the stack. "
         "This is the 'bookmark' — exactly where we'll return to."),
        ("Load ISR address from IVT",
         "CPU reads address from **Interrupt Vector Table** at vector × 2 = 0x08. "
         "This is the address of the keyboard handler routine."),
        ("Jump to ISR",
         "**PC ← ISR address**. Interrupts disabled (I=0). CPU begins executing the handler."),
        ("ISR executes, reads data",
         "The Interrupt Service Routine reads the keycode from the I/O port, processes it, "
         "and signals the PIC with **EOI** (End Of Interrupt)."),
        ("IRET — restore context",
         "**IRET** instruction: pop FLAGS and PC from stack. CPU resumes exactly where it was interrupted."),
    ]
    for i, (title, detail) in enumerate(interrupt_steps):
        with st.expander(f"Step {i+1}: {title}"):
            st.markdown(detail)

    # Live interrupt demo
    st.divider()
    st.markdown("## Live Interrupt Simulation")
    st.caption("Trigger interrupts manually and watch how the CPU handles them.")

    if "irq_cpu" not in st.session_state:
        st.session_state["irq_cpu"]  = CPU()
        st.session_state["irq_log"]  = []

    cpu = st.session_state["irq_cpu"]

    # Load a trivial program to be 'interrupted'
    prog = [0x12, 0x12, 0x12, 0x12, 0x12, 0x12, 0x12, 0x12, 0xFF]  # NOPs + HLT
    for i,b in enumerate(prog):
        cpu.memory.write(0x70+i, b)
    cpu.registers.PC = 0x70

    itype_map = {
        "NMI (Non-maskable)":          InterruptType.NMI,
        "IRQ0 — Timer tick":           InterruptType.IRQ0,
        "IRQ1 — Keyboard keypress":    InterruptType.IRQ1,
        "IRQ2 — Serial data received": InterruptType.IRQ2,
        "IRQ3 — Disk I/O complete":    InterruptType.IRQ3,
        "Software interrupt (syscall)":InterruptType.SOFTWARE,
    }

    sel_irq = st.selectbox("Select interrupt to trigger", list(itype_map.keys()))
    irq_flags = st.checkbox("Interrupts enabled (I flag)", value=True)
    cpu.registers.FLAGS.interrupt = irq_flags

    if st.button("Raise interrupt", type="primary"):
        itype = itype_map[sel_irq]
        cpu.raise_interrupt(itype, sel_irq)
        # Execute one NOP then service the interrupt
        opcode = cpu._fetch()
        cpu.execute_instruction(opcode)
        new_steps = cpu.step_log[-6:]  # last few steps
        for step in new_steps:
            entry = {
                "Cycle":  step.cycle,
                "Phase":  step.phase.upper(),
                "Event":  step.description,
                "Detail": step.detail[:100]+"…" if len(step.detail)>100 else step.detail,
            }
            st.session_state["irq_log"].insert(0, entry)
        cpu.step_log = []

    if st.session_state["irq_log"]:
        df = pd.DataFrame(st.session_state["irq_log"][:15])
        def irq_style(row):
            colors = {"INTERRUPT":"#f8d7da","FETCH":"#cff4fc","EXECUTE":"#d1e7dd","DECODE":"#fff3cd"}
            c = colors.get(row["Phase"],"")
            return [f"background-color:{c}"]*len(row)
        st.dataframe(df.style.apply(irq_style,axis=1), hide_index=True, use_container_width=True)

    if st.button("Reset interrupt CPU"):
        del st.session_state["irq_cpu"]
        del st.session_state["irq_log"]
        st.rerun()

    # Interrupt vector table
    st.divider()
    st.markdown("## Interrupt Vector Table (IVT)")
    st.caption("Maps interrupt numbers to handler addresses. Sits at fixed low memory (0x0000 in our sim).")
    df = pd.DataFrame(INTERRUPT_TABLE, columns=["Type","Priority","Vector (hex)","Description",""])
    df["Vector (hex)"] = df["Vector (hex)"].apply(lambda x: f"0x{x:02X}")
    st.dataframe(df, hide_index=True, use_container_width=True)

    # I/O ports
    st.divider()
    st.markdown("## I/O Ports & Memory-Mapped I/O")
    if level == "Beginner":
        st.markdown("The CPU talks to devices (keyboard, disk, screen) using special addresses called **I/O ports**.")

    st.markdown("""
**Two approaches:**

| Method | How | Example |
|---|---|---|
| **Port-mapped I/O** | Separate address space. Special `IN`/`OUT` instructions. | x86 `IN AL, 0x60` (keyboard) |
| **Memory-mapped I/O** | Devices appear as normal RAM addresses. `LOAD`/`STORE` work. | ARM, our simulator (0xD0–0xDF) |

In our simulator, I/O ports 0–15 are mapped to addresses **0xD0–0xDF**.
Reading `IN 0` is equivalent to reading memory at `0xD0`.
""")

    if level in ("Intermediate","Advanced"):
        st.markdown("### I/O Port Map (our 256-byte system)")
        io_map = [
            ("0xD0", "0", "Keyboard data register — keycode of last key pressed"),
            ("0xD1", "1", "Keyboard status — bit 0 = key ready"),
            ("0xD2", "2", "Serial TX register — write byte to send"),
            ("0xD3", "3", "Serial RX register — read last received byte"),
            ("0xD4", "4", "Timer counter low byte"),
            ("0xD5", "5", "Timer counter high byte"),
            ("0xD6", "6", "Display control — write char to screen"),
            ("0xD7", "7", "Interrupt mask register — enable/disable IRQs"),
            ("0xD8–0xDF","8–15","General purpose I/O (GPIO)"),
        ]
        df2 = pd.DataFrame(io_map, columns=["Memory addr","Port","Function"])
        st.dataframe(df2, hide_index=True, use_container_width=True)

    if level == "Advanced":
        st.divider()
        st.markdown("## Interrupt Latency & Real-Time Systems")
        st.markdown("""
**Interrupt latency** = time from IRQ assertion → first ISR instruction.

Components:
1. Current instruction completion (1–many cycles)
2. Pipeline flush (if pipelined)
3. Context save (push PC + FLAGS: ~5–10 cycles)
4. Vector fetch (1–2 cycles)
5. ISR instruction fetch (1+ cycles)

Typical x86 latency: **~100–1000 ns** depending on pipeline state.

**Real-time systems (RTOS)** require *bounded* latency — no matter what the CPU is doing, the ISR must start within a guaranteed window (e.g. 50 µs for motor control).

This is why RT kernels (FreeRTOS, Zephyr, VxWorks) run with interrupts enabled almost always, use **prioritised preemptive scheduling**, and avoid long non-preemptible critical sections.
""")
