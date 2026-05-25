"""Buses (Data, Address, Control) page."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import streamlit as st
import pandas as pd
from core.reference import BUS_INFO


def render():
    st.title("Buses: Data, Address & Control")
    level = st.session_state.get("level", "Intermediate")

    st.info("A **bus** is just a set of parallel wires that carry signals between parts of the computer. "
                "Think of it like a motorway with multiple lanes — each lane carries one bit (0 or 1) at a time.")

    st.markdown("""
Every time the CPU reads from or writes to memory (or a device), three buses are involved simultaneously:
- The **address bus** says *where*
- The **data bus** carries *what*
- The **control bus** says *how* (read or write, and other signals)
""")

    # Three bus diagram (text-based since we're in Streamlit)
    st.markdown("## The Three-Bus Architecture")
    st.markdown("""
```
┌─────────────────────────────────────────────────────────────────┐
│                            CPU                                   │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  │
│  │  PC  │  │ MAR  │  │ MDR  │  │  IR  │  │  A   │  │ ALU  │  │
│  └──┬───┘  └──┬───┘  └──┬───┘  └──────┘  └──────┘  └──────┘  │
└─────┼─────────┼──────────┼───────────────────────────────────────┘
      │         │          │
      │    ADDRESS BUS     │                   CONTROL BUS
      │  (16 lines, →)     │              (RD, WR, INTA, HOLD…)
      │         │          │  DATA BUS         │
      │         │        (8 lines, ↔)          │
      ▼         ▼          ▼                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Memory / Devices                         │
│   ROM (0x00)   RAM (0x20)   I/O (0xD0)   DMA buffer (0xE0)     │
└─────────────────────────────────────────────────────────────────┘
```
""")

    # Detailed bus cards
    st.divider()
    st.markdown("## Bus Details")
    bus_colors = {"address":"#cff4fc", "data":"#d1e7dd", "control":"#fff3cd"}

    for bus_name, info in BUS_INFO.items():
        with st.expander(f"**{bus_name.capitalize()} Bus**", expanded=True):
            st.markdown(f"""
<div style="background:{bus_colors[bus_name]};border-radius:8px;padding:12px 16px;margin-bottom:10px">
<table style="width:100%;font-size:13px">
<tr><td><b>Width</b></td><td><code>{info['width']}</code></td>
    <td><b>Direction</b></td><td>{info['direction']}</td></tr>
<tr><td><b>Lines</b></td><td><code>{info['lines']}</code></td>
    <td><b>Addressable</b></td><td>{info['addressable']}</td></tr>
</table>
<p style="margin:10px 0 0"><b>Role:</b> {info['role']}</p>
</div>""", unsafe_allow_html=True)

    # Bus transaction walkthrough
    st.divider()
    st.markdown("## Bus Transaction Walkthrough")
    st.caption("Select an operation to see what happens on each bus, cycle by cycle.")

    transaction = st.selectbox("Operation", [
        "Memory READ (LOAD instruction)",
        "Memory WRITE (STORE instruction)",
        "I/O READ (IN instruction)",
        "I/O WRITE (OUT instruction)",
        "Interrupt Acknowledge (INTA cycle)",
        "DMA Bus Hold (HOLD/HLDA)",
    ])

    transactions = {
        "Memory READ (LOAD instruction)": [
            ("T1", "CPU puts target address (e.g. 0x00A0) on address bus",   "0x00A0", "—",      "RD↓ (asserted)"),
            ("T2", "Memory decodes address, accesses cell",                   "0x00A0", "—",      "RD"),
            ("T3", "Memory puts data (0x48) on data bus",                     "0x00A0", "0x48",   "RD"),
            ("T4", "CPU reads data bus → MDR=0x48. RD deasserted.",           "—",      "0x48",   "RD↑ (released)"),
        ],
        "Memory WRITE (STORE instruction)": [
            ("T1", "CPU puts target address on address bus",                  "0x00A0", "—",      "WR↓ (asserted)"),
            ("T2", "CPU puts data (0x72) on data bus",                        "0x00A0", "0x72",   "WR"),
            ("T3", "Memory latches data from data bus into cell",             "0x00A0", "0x72",   "WR"),
            ("T4", "WR deasserted. Write complete.",                          "—",      "—",      "WR↑ (released)"),
        ],
        "I/O READ (IN instruction)": [
            ("T1", "CPU puts port number on address bus (lower 8 bits)",      "0x0000", "—",      "IOR↓ (I/O read)"),
            ("T2", "I/O controller decodes port, reads device register",      "0x0000", "—",      "IOR"),
            ("T3", "Device puts data on data bus",                            "0x0000", "0x41",   "IOR"),
            ("T4", "CPU latches data → A register. IOR released.",            "—",      "0x41",   "IOR↑"),
        ],
        "I/O WRITE (OUT instruction)": [
            ("T1", "CPU puts port number on address bus",                     "0x0006", "—",      "IOW↓ (I/O write)"),
            ("T2", "CPU puts A register value on data bus",                   "0x0006", "0x48",   "IOW"),
            ("T3", "Device latches data — e.g. display outputs character 'H'","0x0006", "0x48",   "IOW"),
            ("T4", "IOW released.",                                           "—",      "—",      "IOW↑"),
        ],
        "Interrupt Acknowledge (INTA cycle)": [
            ("T1", "PIC asserts INTR line. CPU finishes current instruction.", "—",      "—",      "INTR↓"),
            ("T2", "CPU asserts INTA (interrupt acknowledge) on control bus.", "—",      "—",      "INTA↓"),
            ("T3", "PIC puts interrupt vector number (e.g. 0x04) on data bus","—",      "0x04",   "INTA"),
            ("T4", "CPU reads vector → looks up ISR in IVT. INTA released.",  "0x0008", "0x04",   "INTA↑"),
        ],
        "DMA Bus Hold (HOLD/HLDA)": [
            ("T1", "DMA controller asserts HOLD on control bus.",             "—",      "—",      "HOLD↓"),
            ("T2", "CPU finishes current bus cycle, then floats all buses.",  "—",      "—",      "HLDA↓ (CPU grants)"),
            ("T3", "DMA takes control. Puts src address on address bus.",     "0x00D0", "—",      "RD↓ (DMA reads)"),
            ("T4", "DMA reads data from source.",                             "0x00D0", "0x41",   "RD"),
            ("T5", "DMA puts dst address, writes data to destination.",       "0x00E0", "0x41",   "WR"),
            ("T6", "DMA repeats for all bytes. Then releases HOLD.",          "—",      "—",      "HOLD↑, HLDA↑"),
        ],
    }

    steps = transactions[transaction]
    df = pd.DataFrame(steps, columns=["Cycle","Description","Address Bus","Data Bus","Control Bus"])

    def style_bus(row):
        if "INTA" in row["Control Bus"] or "HOLD" in row["Control Bus"]:
            return ["background-color:#f8d7da"]*len(row)
        if "WR" in row["Control Bus"]:
            return ["background-color:#fff3cd"]*len(row)
        if "RD" in row["Control Bus"] or "IOR" in row["Control Bus"]:
            return ["background-color:#cff4fc"]*len(row)
        return [""]*len(row)

    st.dataframe(df.style.apply(style_bus, axis=1), hide_index=True, use_container_width=True)

    # Bus width and bandwidth
    st.divider()
    st.markdown("## Bus Width & Bandwidth")
    st.caption("Try different bus widths to see the effect on maximum bandwidth.")

    bw_col1, bw_col2 = st.columns(2)
    with bw_col1:
        bus_width = st.select_slider("Data bus width (bits)", [8, 16, 32, 64, 128], value=64)
        freq_mhz  = st.slider("Bus clock frequency (MHz)", 33, 6400, 3200, step=100)
        transfers = st.selectbox("Transfers per cycle", [1, 2, 4], index=1,
                                 help="Double Data Rate (DDR) does 2; QDR does 4")
    with bw_col2:
        bytes_per_transfer = bus_width // 8
        bandwidth_gb = (bytes_per_transfer * transfers * freq_mhz * 1e6) / 1e9
        st.metric("Bytes per transfer", f"{bytes_per_transfer} bytes")
        st.metric("Peak bandwidth", f"{bandwidth_gb:.1f} GB/s")
        st.metric("Address space (16-bit addr bus)", "64 KB")
        st.metric("Address space (32-bit addr bus)", "4 GB")
        st.metric("Address space (64-bit addr bus)", "16 EB (theoretical)")

    if level in ("Intermediate", "Advanced"):
        st.divider()
        st.markdown("## Modern Bus Standards")
        bus_standards = [
            ("PCIe 5.0 x16",     "CPU ↔ GPU",          "128 GB/s",  "Differential serial (×16 lanes)"),
            ("DDR5-6400",        "CPU ↔ RAM",           "51.2 GB/s", "Parallel, dual-channel"),
            ("USB 3.2 Gen2×2",   "CPU ↔ Peripheral",   "2.4 GB/s",  "Serial, differential pair"),
            ("SATA III",         "CPU ↔ HDD/SSD",       "0.6 GB/s",  "Serial ATA"),
            ("I²C",              "MCU ↔ Sensors",        "0.4 MB/s",  "2-wire serial, multi-device"),
            ("SPI",              "MCU ↔ Flash/Display",  "50 MB/s",   "4-wire synchronous serial"),
            ("System bus (FSB)", "CPU ↔ Chipset (legacy)","12.8 GB/s","Parallel, now replaced by HyperTransport/QPI"),
        ]
        df2 = pd.DataFrame(bus_standards, columns=["Standard", "Connection", "Peak bandwidth", "Technology"])
        st.dataframe(df2, hide_index=True, use_container_width=True)

    if level == "Advanced":
        st.divider()
        st.markdown("## Bus Arbitration")
        st.markdown("""
When multiple devices share a bus (CPU, DMA, GPU), only one can use it at a time.
**Bus arbitration** decides who gets access:

| Scheme | How | Used in |
|---|---|---|
| **Daisy chain** | Grant signal passes device→device; first device with request keeps bus | Simple embedded systems |
| **Centralised arbiter** | Dedicated arbiter chip; devices send REQ, arbiter asserts GNT | ISA, PCI |
| **Distributed (self-select)** | Devices broadcast priority; highest wins | CAN bus (automotive) |
| **Time-division** | Each device gets a fixed time slot | Some SoC interconnects |

**PCIe** avoids arbitration entirely — it's **point-to-point** (CPU has a dedicated lane to each device).
No sharing = no arbitration = no wait. This is why PCIe replaced PCI (shared bus).
""")
