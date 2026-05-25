"""Memory & Storage Types page."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import streamlit as st
from core.reference import MEMORY_TYPE_INFO


MEMORY_HIERARCHY = [
    ("CPU Registers",  "< 1 ns",    "~1 KB",      "SRAM (flip-flops)", "#2d6a4f"),
    ("L1 Cache",       "~1 ns",     "32–64 KB",   "SRAM", "#40916c"),
    ("L2 Cache",       "~4 ns",     "256 KB–1 MB","SRAM", "#52b788"),
    ("L3 Cache",       "~10 ns",    "8–32 MB",    "SRAM", "#74c69d"),
    ("Main RAM",       "~100 ns",   "8–128 GB",   "DRAM", "#b7e4c7"),
    ("NVMe SSD",       "~100 µs",   "500 GB–4 TB","Flash NAND", "#d8f3dc"),
    ("HDD",            "~10 ms",    "1–20 TB",    "Magnetic", "#f0f0f0"),
    ("Tape / Archive", "~minutes",  "Petabytes",  "Magnetic tape", "#e0e0e0"),
]


def render():
    st.title("Memory & Storage Types")
    level = st.session_state.get("level","Intermediate")

    st.info("Think of memory like a building with different floors. "
                "The top floors are tiny, expensive, and super fast (CPU registers). "
                "The basement is huge, cheap, and slow (hard disk). "
                "The CPU tries to keep the data it uses most often on the top floors.")

    # Memory hierarchy triangle
    st.markdown("## The Memory Hierarchy")
    for i, (name, latency, capacity, tech, color) in enumerate(MEMORY_HIERARCHY):
        pct   = 20 + i * 10
        width = f"{min(100, 20 + i*11)}%"
        speed_emoji = "⚡" if i<=1 else ("🔵" if i<=3 else ("🟡" if i<=5 else "🔴"))
        st.markdown(f"""
<div style="width:{width};background:{color};border-radius:4px;padding:7px 14px;
     margin:3px 0;color:{'#1b4332' if i<5 else '#333'};font-size:13px;
     display:flex;justify-content:space-between;align-items:center;
     border-left:4px solid {'#1b4332' if i<4 else '#888'}">
  <span><b>{speed_emoji} {name}</b></span>
  <span style="font-family:monospace">{latency}</span>
  <span>{capacity}</span>
  <span style="color:#666;font-size:11px">{tech}</span>
</div>""", unsafe_allow_html=True)

    # Memory type cards
    st.divider()
    st.markdown("## Memory Type Deep-Dive")
    types_in_order = ["SRAM","DRAM","ROM","PROM","EPROM","EEPROM","Flash","Virtual"]

    for mtype in types_in_order:
        info = MEMORY_TYPE_INFO[mtype]
        vol_badge   = "Volatile"  if info["volatile"]   else "Non-volatile"
        write_badge = "Read/Write" if info["rewritable"] else "Read-only"
        with st.expander(f" **{info['full']}** ({mtype})"):
            c1,c2 = st.columns([2,1])
            with c1:
                st.markdown(f"""
**Technology:** {info['tech']}

**Speed:** `{info['speed']}`

**Primary use:** {info['use']}

**Notes:** {info['notes']}
""")
            with c2:
                st.markdown(f"{vol_badge}  \n{write_badge}")
                if mtype == "Virtual" and level in ("Intermediate","Advanced"):
                    st.markdown("""
**Page fault sequence:**
1. CPU accesses virtual address
2. MMU checks page table → not in RAM
3. OS raises page fault exception
4. OS loads page from swap on disk
5. Page table updated, CPU retries
                    """)
                if mtype == "DRAM" and level in ("Intermediate","Advanced"):
                    st.markdown("""
**Refresh cycles:**
- DRAM capacitors leak charge
- Must be refreshed every ~64 ms
- Refresh controller sends RAS-only cycles
- During refresh: no CPU access (wait state)
                    """)
                if mtype == "Flash" and level == "Advanced":
                    st.markdown("""
**NAND vs NOR Flash:**
- **NOR**: random access reads, fast, expensive. Used in microcontrollers, BIOS.
- **NAND**: sequential, dense, cheap. Used in SSDs, USB drives, phones.
- Wear levelling required: each cell survives ~10K–100K writes.
                    """)

    # Comparison table
    st.divider()
    st.markdown("## Comparison Table")
    import pandas as pd
    rows = []
    for mtype in types_in_order:
        info = MEMORY_TYPE_INFO[mtype]
        rows.append({
            "Type": mtype,
            "Full name": info["full"],
            "Volatile?": "Yes" if info["volatile"] else "No",
            "Writable?": "Yes" if info["rewritable"] else "No",
            "Speed": info["speed"],
            "Typical use": info["use"],
        })
    df = pd.DataFrame(rows)
    st.dataframe(df, hide_index=True, use_container_width=True)

    # Memory map of our simulated system
    st.divider()
    st.markdown("## Simulated Memory Map (256-byte system)")
    from core.cpu import CPU
    cpu = CPU()
    map_rows = []
    for region in cpu.memory.regions:
        map_rows.append({
            "Start": f"0x{region.start:02X}",
            "End": f"0x{region.start+region.size-1:02X}",
            "Size (bytes)": region.size,
            "Name": region.name,
            "Type": region.mem_type.value,
            "Writable": "Yes" if region.writable else "No (ROM)",
            "Purpose": region.description,
        })
    df2 = pd.DataFrame(map_rows)

    def color_rows(row):
        colors = {"ROM":"#fff3cd","Flash":"#fde8d8","DRAM":"#d1e7dd","SRAM":"#cff4fc","Virtual":"#e2d9f3"}
        c = colors.get(row["Type"],"")
        return [f"background-color:{c}"]*len(row) if c else [""]*len(row)

    styled = df2.style.apply(color_rows, axis=1)
    st.dataframe(styled, hide_index=True, use_container_width=True)
