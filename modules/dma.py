"""DMA & Direct Memory Access page."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import streamlit as st
import pandas as pd
from core.cpu import CPU, InterruptType


def render():
    st.title("DMA — Direct Memory Access")
    level = st.session_state.get("level", "Intermediate")

    st.info("Normally the CPU moves every single byte of data itself — "
                "read from disk, write to RAM, one byte at a time. "
                "**DMA** is like hiring a removal van: you tell it 'move these 4096 bytes from A to B' "
                "and it does the job while you get on with other things.")

    st.markdown("""
When a disk, network card, or sound card needs to transfer a large block of data into RAM,
using the CPU wastes thousands of cycles on trivial byte-moving.

**DMA** gives a dedicated controller access to the memory bus, so it can transfer data
directly between a device and RAM — without CPU involvement for each byte.
""")

    # CPU-driven vs DMA comparison
    st.markdown("## CPU-driven Transfer vs DMA")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### Without DMA (PIO)")
        st.code("""for i in range(4096):       # 4 KB block
    A = IN(disk_data_port)  # CPU reads byte
    memory[buf + i] = A     # CPU writes byte
    # ~6 cycles per byte
    # 4096 × 6 = 24,576 cycles
    # CPU blocked the whole time""", language="python")
        st.error("CPU fully occupied. No other process can run during transfer.")

    with c2:
        st.markdown("### With DMA")
        st.code("""# CPU programs the DMA controller:
DMA.source      = disk_data_port
DMA.destination = RAM_buffer_address
DMA.length      = 4096
DMA.start()          # hand off to DMA

# CPU is now FREE:
while not DMA.done:
    do_other_work()  # scheduler runs other tasks

# DMA raises IRQ when done → CPU handles result""", language="python")
        st.success("CPU free during transfer. DMA does the byte-moving independently.")

    # DMA sequence
    st.divider()
    st.markdown("## DMA Transfer Sequence")
    dma_steps = [
        ("CPU programs DMA controller",
         "CPU writes source address, destination address, transfer length, and transfer mode "
         "into the DMA controller's registers via I/O ports. Then writes '1' to the start bit."),
        ("DMA requests bus (HOLD)",
         "DMA controller asserts the **HOLD** signal on the control bus — "
         "asking the CPU to release bus control."),
        ("CPU grants bus (HLDA)",
         "CPU finishes its current bus cycle, then asserts **HLDA** (Hold Acknowledge) "
         "and releases the address, data, and control buses — all lines go high-impedance (floating)."),
        ("DMA transfers bytes autonomously",
         "DMA controller takes over: it puts the source address on the address bus, "
         "asserts RD, reads data from the device into its internal buffer, "
         "then puts the destination address on the bus, asserts WR, and writes to RAM. "
         "It does this for every byte/word, decrementing a counter each time."),
        ("DMA releases bus periodically",
         "In **cycle-stealing mode**, the DMA releases the bus between bytes so the CPU can "
         "run a few instructions — reducing latency at the cost of transfer speed. "
         "In **burst mode**, DMA holds the bus for the entire block."),
        ("Transfer complete — interrupt",
         "When the byte counter reaches zero, DMA de-asserts HOLD and raises a **DMA_DONE** interrupt. "
         "The CPU resumes full bus control and its ISR processes the transferred data."),
    ]
    for i, (title, detail) in enumerate(dma_steps):
        with st.expander(f"Step {i+1}: {title}"):
            st.markdown(detail)

    # Live DMA simulation
    st.divider()
    st.markdown("## Live DMA Simulation")
    st.caption("Configure a DMA transfer and watch it execute, cycle by cycle.")

    col1, col2, col3 = st.columns(3)
    with col1:
        src_addr = st.number_input("Source address (hex)", min_value=0xD0, max_value=0xDF,
                                    value=0xD0, format="%X",
                                    help="I/O device buffer (0xD0–0xDF)")
    with col2:
        dst_addr = st.number_input("Destination address (hex)", min_value=0xE0, max_value=0xEF,
                                    value=0xE0, format="%X",
                                    help="DMA buffer in RAM (0xE0–0xEF)")
    with col3:
        dma_len  = st.slider("Transfer length (bytes)", 1, 16, 8)

    dma_mode = st.radio("DMA mode", ["Burst (holds bus for full transfer)",
                                      "Cycle-stealing (releases bus between bytes)"],
                         horizontal=True)

    if st.button("Run DMA transfer", type="primary"):
        cpu = CPU()
        # Pre-load source data with interesting values
        for i in range(16):
            cpu.memory.write(0xD0 + i, 0x41 + i)  # 'A', 'B', 'C', ...

        # Run a couple CPU cycles first to show normal operation
        prog = [0x12, 0x12, 0x12, 0xFF]  # NOP NOP NOP HLT
        for i, b in enumerate(prog):
            cpu.memory.write(0x70 + i, b)
        cpu.registers.PC = 0x70

        # Execute 2 NOPs before DMA
        cpu._fetch(); cpu.execute_instruction(0x12)
        cpu._fetch(); cpu.execute_instruction(0x12)

        # DMA transfer
        cpu.dma_transfer(int(src_addr), int(dst_addr), dma_len)

        st.session_state["dma_cpu"]   = cpu
        st.session_state["dma_steps"] = cpu.step_log

    if "dma_cpu" in st.session_state:
        cpu   = st.session_state["dma_cpu"]
        steps = st.session_state["dma_steps"]

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total cycles",  cpu.cycle)
        m2.metric("Bus transactions", len(cpu.bus_log))
        m3.metric("Bytes transferred", dma_len if "dma_len" in dir() else "—")
        m4.metric("CPU cycles saved", dma_len * 4)

        tab1, tab2 = st.tabs(["Step log", "Memory before/after"])
        with tab1:
            phase_colors = {"fetch":"#cff4fc","decode":"#fff3cd","execute":"#d1e7dd",
                            "writeback":"#e2d9f3","dma":"#fde8d8","interrupt":"#f8d7da"}
            for step in steps:
                color = phase_colors.get(step.phase, "#f8f9fa")
                icon  = "ACCESS" if step.phase == "dma" else ("INTERRUPT" if step.phase == "interrupt" else "")
                with st.expander(f"{icon} [{step.phase.upper():12s}] Cycle {step.cycle:3d} — {step.description}"):
                    st.markdown(f'<div style="background:{color};padding:10px;border-radius:6px">'
                                f'{step.detail}</div>', unsafe_allow_html=True)
                    if step.mem_changed:
                        rows = [{"Address": f"0x{a:02X}", "Value (hex)": f"0x{v:02X}",
                                 "Value (dec)": v,
                                 "ASCII": chr(v) if 32 <= v <= 126 else "—"}
                                for a, v in step.mem_changed]
                        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

        with tab2:
            src_rows = []
            dst_rows = []
            for i in range(16):
                src_rows.append({"Address": f"0x{0xD0+i:02X}", "Value": f"0x{cpu.memory.cells[0xD0+i].value:02X}",
                                  "ASCII": chr(cpu.memory.cells[0xD0+i].value) if 32<=cpu.memory.cells[0xD0+i].value<=126 else "—"})
                dst_rows.append({"Address": f"0x{0xE0+i:02X}", "Value": f"0x{cpu.memory.cells[0xE0+i].value:02X}",
                                  "ASCII": chr(cpu.memory.cells[0xE0+i].value) if 32<=cpu.memory.cells[0xE0+i].value<=126 else "—"})
            sc1, sc2 = st.columns(2)
            with sc1:
                st.markdown("**Source (I/O buffer 0xD0–0xDF)**")
                st.dataframe(pd.DataFrame(src_rows), hide_index=True, use_container_width=True)
            with sc2:
                st.markdown("**Destination (DMA buffer 0xE0–0xEF)**")
                st.dataframe(pd.DataFrame(dst_rows), hide_index=True, use_container_width=True)

    # DMA modes
    st.divider()
    st.markdown("## DMA Transfer Modes")
    modes = [
        ("Burst mode",        "DMA holds the bus for the entire block. Fastest transfer, but CPU is blocked completely.",
         "Large block I/O where latency doesn't matter (disk sector reads).", "🔴 CPU blocked"),
        ("Cycle-stealing",    "DMA takes one bus cycle, then releases it. CPU can interleave instructions between bytes.",
         "Sound cards, moderate-speed devices.", "🟡 Shared"),
        ("Transparent (fly-by)", "DMA only uses the bus during CPU's idle cycles (e.g. during memory refresh).",
         "Very slow devices; older systems.", "🟢 CPU unaffected"),
        ("Scatter-Gather",    "DMA transfers to/from a linked list of non-contiguous memory buffers in one operation.",
         "Network packets, filesystem I/O (modern OS DMA engines).", "🔴 CPU blocked (but flexible)"),
    ]
    df = pd.DataFrame(modes, columns=["Mode", "Description", "Typical use", "CPU impact"])
    st.dataframe(df, hide_index=True, use_container_width=True)

    if level in ("Intermediate", "Advanced"):
        st.divider()
        st.markdown("## Real-World DMA in Modern Systems")
        st.markdown("""
| System | DMA usage |
|---|---|
| **Hard disk / SSD** | Disk controller DMA's sector data directly into kernel buffers in RAM |
| **Network card (NIC)** | NIC DMA's received packet data into ring buffer; raises IRQ when done |
| **GPU** | PCIe DMA copies vertex/texture data to GPU VRAM |
| **USB** | USB host controller DMA's packets; no CPU intervention per byte |
| **Audio (DMA double-buffer)** | DMA fills buffer A while CPU generates audio into buffer B, then swap |
| **IOMMU** | Protects memory from rogue DMA: maps device's view of addresses, prevents DMA attacks |
""")

    if level == "Advanced":
        st.divider()
        st.markdown("## DMA Security: IOMMU")
        st.markdown("""
DMA is a **privilege escalation risk**: a malicious or compromised PCIe device could DMA-write to any physical RAM address — including the kernel, other processes, or BIOS — bypassing all OS memory protections.

**IOMMU** (Intel VT-d, AMD-Vi) is a hardware MMU for devices:
- Each device gets a **virtual I/O address space**
- IOMMU translates device addresses → physical RAM, enforcing access limits
- A NIC can only DMA into its allocated kernel buffer, not into `/proc/kcore`

Used by:
- Hypervisors: pass-through PCIe devices to VMs safely
- OS kernel: `iommu=force` on Linux
- Thunderbolt security (Thunderbolt DMA attacks were a real exploit vector)

**DMA attacks** (e.g. "Evil Maid", Thunderspy): plug in a malicious Thunderbolt/PCIe device → DMA read from RAM → extract encryption keys or inject code. IOMMU + Secure Boot blocks this.
""")
