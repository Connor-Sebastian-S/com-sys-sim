"""
Basics page — The absolute fundamentals.
Bits, bytes, why computers use binary, what data really is.
Every level sees the beginner content; Intermediate and Advanced get additional depth layered on top.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import streamlit as st


# ── Reusable section builder ───────────────────────────────────────────────────
# Each section has:
#   beginner   — always shown, plain English
#   intermediate — shown at Intermediate + Advanced, adds technical depth
#   advanced   — shown only at Advanced, full hardware/theory detail

def section(title: str, icon: str, beginner: str, intermediate: str = "", advanced: str = ""):
    level = st.session_state.get("level", "Intermediate")
    st.markdown(f"## {icon} {title}")
    # Beginner block — always visible
    st.markdown(f"""
<div style="background:#0a2010;border-left:4px solid #2a6a3a;border-radius:0 8px 8px 0;
     padding:14px 18px;margin-bottom:10px;font-size:14px;line-height:1.7">
{beginner}
</div>""", unsafe_allow_html=True)

    # Intermediate block — visible at Intermediate and Advanced
    if intermediate and level in ("Intermediate", "Advanced"):
        st.markdown(f"""
<div style="background:#0a1a30;border-left:4px solid #2a5a9e;border-radius:0 8px 8px 0;
     padding:14px 18px;margin-bottom:10px;font-size:14px;line-height:1.7">
<span style="font-size:11px;font-weight:700;color:#5a9;letter-spacing:.08em">▲ INTERMEDIATE</span><br><br>
{intermediate}
</div>""", unsafe_allow_html=True)

    # Advanced block — visible only at Advanced
    if advanced and level == "Advanced":
        st.markdown(f"""
<div style="background:#1a0a20;border-left:4px solid #6a3a9e;border-radius:0 8px 8px 0;
     padding:14px 18px;margin-bottom:10px;font-size:14px;line-height:1.7">
<span style="font-size:11px;font-weight:700;color:#a5d;letter-spacing:.08em">▲ ADVANCED</span><br><br>
{advanced}
</div>""", unsafe_allow_html=True)

    st.divider()


# ── Interactive bit builder ───────────────────────────────────────────────────

def bit_builder():
    st.markdown("## 🧱 Build a Byte")
    st.caption("Click each switch to flip a bit on or off. Watch the value change.")

    if "bits" not in st.session_state:
        st.session_state["bits"] = [0] * 8

    cols = st.columns(8)
    labels = ["Bit 7", "Bit 6", "Bit 5", "Bit 4", "Bit 3", "Bit 2", "Bit 1", "Bit 0"]
    weights = [128, 64, 32, 16, 8, 4, 2, 1]

    for i, (col, label, weight) in enumerate(zip(cols, labels, weights)):
        with col:
            bit = st.session_state["bits"][i]
            # Show weight label
            st.markdown(f"<div style='text-align:center;font-size:10px;color:#888;font-family:monospace'>"
                        f"2<sup>{7-i}</sup>={weight}</div>", unsafe_allow_html=True)
            # Toggle button — green if 1, dark if 0
            btn_color = "#1a6e3a" if bit else "#1a1d27"
            border     = "#5d5" if bit else "#333"
            if col.button(str(bit), key=f"bit_{i}",
                          help=f"{label} — place value {weight}",
                          use_container_width=True):
                st.session_state["bits"][i] ^= 1
                st.rerun()
            st.markdown(f"<div style='text-align:center;font-size:10px;color:#888'>{label}</div>",
                        unsafe_allow_html=True)

    bits = st.session_state["bits"]
    value = sum(b * w for b, w in zip(bits, weights))
    binary_str = "".join(str(b) for b in bits)
    grouped = binary_str[:4] + " " + binary_str[4:]

    # Result display
    level = st.session_state.get("level", "Intermediate")
    st.markdown(f"""
<div style="background:#12151e;border:1px solid #2a2d3a;border-radius:8px;
     padding:16px 20px;margin-top:8px;font-family:monospace">
  <div style="display:flex;gap:32px;align-items:center;flex-wrap:wrap">
    <div>
      <div style="font-size:10px;color:#666;letter-spacing:.1em">BINARY</div>
      <div style="font-size:22px;font-weight:700;color:#fff;letter-spacing:4px">{grouped}</div>
    </div>
    <div>
      <div style="font-size:10px;color:#666;letter-spacing:.1em">DECIMAL</div>
      <div style="font-size:22px;font-weight:700;color:#5af">{value}</div>
    </div>
    <div>
      <div style="font-size:10px;color:#666;letter-spacing:.1em">HEXADECIMAL</div>
      <div style="font-size:22px;font-weight:700;color:#e8a020">0x{value:02X}</div>
    </div>
    <div>
      <div style="font-size:10px;color:#666;letter-spacing:.1em">ASCII</div>
      <div style="font-size:22px;font-weight:700;color:#5d5">
        {'<i>'+chr(value)+'</i>' if 32 <= value <= 126 else '<span style="color:#555">N/A</span>'}
      </div>
    </div>
  </div>
  <div style="margin-top:10px;font-size:12px;color:#555">
    Calculation: {" + ".join(f"{b}×{w}" for b,w in zip(bits,weights) if b) or "0"} = {value}
  </div>
</div>""", unsafe_allow_html=True)

    if level in ("Intermediate", "Advanced"):
        st.markdown(f"""
<div style="margin-top:8px;font-size:12px;color:#888;font-family:monospace;
     background:#0a1a30;border-radius:6px;padding:10px 14px">
High nibble: <b style="color:#e8a020">0x{value >> 4:X}</b> ({binary_str[:4]}) &nbsp;|&nbsp;
Low nibble: <b style="color:#e8a020">0x{value & 0xF:X}</b> ({binary_str[4:]}) &nbsp;|&nbsp;
Signed (two's complement): <b style="color:#5af">{value - 256 if value >= 128 else value}</b>
</div>""", unsafe_allow_html=True)

    if st.button("Reset byte", key="reset_byte"):
        st.session_state["bits"] = [0] * 8
        st.rerun()

    st.divider()


# ── Data types table ──────────────────────────────────────────────────────────

def data_types_table():
    level = st.session_state.get("level", "Intermediate")
    st.markdown("## 📐 Common Data Sizes")

    rows_beginner = [
        ("Bit",    "1",  "0 or 1",            "A single switch: on or off"),
        ("Nibble", "4",  "0 – 15",            "Half a byte. One hex digit."),
        ("Byte",   "8",  "0 – 255",           "One character, one pixel channel, one small number"),
        ("Word",   "16", "0 – 65,535",        "Two bytes. Common on older CPUs."),
        ("Dword",  "32", "0 – 4,294,967,295", "Four bytes. Standard int on most systems."),
        ("Qword",  "64", "0 – ~18 quintillion","Eight bytes. Modern 64-bit integer."),
    ]

    rows_advanced = [
        ("float32",  "32", "±3.4×10³⁸",       "IEEE-754 single precision. Sign + 8-bit exp + 23-bit mantissa."),
        ("float64",  "64", "±1.8×10³⁰⁸",      "IEEE-754 double precision. Sign + 11-bit exp + 52-bit mantissa."),
        ("SIMD 128", "128","4×float32",         "XMM register (SSE). Four floats operated on simultaneously."),
        ("SIMD 256", "256","8×float32",         "YMM register (AVX). Eight floats per cycle."),
        ("SIMD 512", "512","16×float32",        "ZMM register (AVX-512). Used in HPC/ML workloads."),
    ]

    import pandas as pd
    df = pd.DataFrame(rows_beginner, columns=["Type", "Bits", "Range", "What it stores"])
    st.dataframe(df, hide_index=True, use_container_width=True)

    if level == "Advanced":
        st.markdown("**Extended types (intermediate/advanced):**")
        df2 = pd.DataFrame(rows_advanced, columns=["Type", "Bits", "Range", "Notes"])
        st.dataframe(df2, hide_index=True, use_container_width=True)

    st.divider()


# ── Analogy cards ─────────────────────────────────────────────────────────────

def analogy_cards():
    st.markdown("## 🏠 Real-World Analogies")
    level = st.session_state.get("level", "Intermediate")

    analogies = [
        ("🔦", "Bit", "A light switch",
         "On (1) or off (0). That's it. A single bit can only express two possibilities.",
         "The physical realisation is a transistor: a semiconductor switch that conducts (1) or blocks (0) current. A modern CPU contains ~50 billion of these on a chip the size of a postage stamp.",
         "MOSFETs operate in saturation (logic 1) or cut-off (logic 0). Threshold voltage Vt defines the boundary. Sub-threshold leakage is a major power concern at small nodes (<7nm)."),

        ("📦", "Byte", "A small box with 8 compartments",
         "Each compartment holds a 0 or 1. Together, 8 bits can represent 256 different things — every letter, every digit, every colour channel.",
         "A byte is the fundamental addressable unit of memory. Every address in RAM points to exactly one byte. Even if you only want one bit, you read a whole byte and mask the rest.",
         "This is the von Neumann legacy — byte addressability. Some early architectures were word-addressed (e.g. CDC 6600 with 60-bit words). Most modern ISAs are byte-addressed even when the bus is 64 bits wide."),

        ("📚", "RAM", "A massive open-plan library",
         "Every book (byte) has a numbered shelf (address). You can reach any shelf instantly — that's why it's called Random Access Memory. But when the power goes off, all the books vanish.",
         "RAM is volatile DRAM. Each bit is a capacitor + transistor. Capacitors leak, so DRAM must be refreshed every ~64ms. Access latency is ~100ns — slow compared to CPU cache (~1ns).",
         "DRAM row/column addressing uses RAS/CAS signals. A DRAM access: assert RAS (selects row, entire row loaded into sense amplifiers) → assert CAS (selects column). Modern LPDDR5X: 8533 MT/s, ~40ns tRCD latency."),

        ("🧠", "CPU", "A very fast but forgetful chef",
         "The CPU can only work with a tiny amount of data at once (its registers). It has to keep fetching ingredients from the cupboard (RAM), do one tiny step, put the result back, and start again — billions of times per second.",
         "Registers are the fastest storage (0-cycle access, part of the CPU itself). A modern core has ~16–32 general-purpose registers plus hundreds of hidden rename registers. The register file is SRAM built into the die.",
         "Modern CPUs have 100–500 physical registers (register renaming via ROB). Out-of-order execution means the CPU reorders instructions dynamically. A superscalar core can retire 4–6 instructions per cycle. IPC (instructions per clock) is a key performance metric."),

        ("🗃️", "Cache", "A sticky-notes pad on the chef's workbench",
         "Instead of walking to the cupboard (RAM) every single time, the chef keeps their most-used ingredients on the workbench. Cache is the same — small, fast memory right next to the CPU.",
         "L1 cache: ~32KB, 1–4 cycle latency, SRAM, on-die. L2: ~256KB, ~10 cycles. L3: ~8–32MB, ~30 cycles. On a cache miss the CPU stalls — this is why cache-friendly code (good spatial/temporal locality) matters enormously.",
         "Cache lines are typically 64 bytes. A miss fetches the whole line. Prefetchers predict which lines you'll need next. TLBs (Translation Lookaside Buffers) cache virtual→physical address translations — a TLB miss causes a page table walk (100s of cycles)."),

        ("🚌", "Bus", "A road between buildings",
         "Data travels between the CPU, RAM, and devices along the bus — a set of parallel wires. The address bus says where, the data bus carries what, and the control bus says how (read or write).",
         "Bus width directly limits bandwidth. A 64-bit data bus transfers 8 bytes per cycle. At 3200 MHz with DDR (2 transfers/cycle), that's 51.2 GB/s. Modern CPUs use point-to-point connections (PCIe, HyperTransport) rather than shared buses to avoid contention.",
         "In PCIe 5.0, each lane is a differential serial pair at 32 GT/s. x16 = 512 GT/s raw, ~128 GB/s after 128b/130b encoding overhead. Compare to the old FSB (Front Side Bus) shared by all components at ~12 GB/s — a single point of contention."),
    ]

    for icon, name, one_liner, beg, inter, adv in analogies:
        level = st.session_state.get("level", "Intermediate")
        with st.expander(f"{icon} **{name}** — {one_liner}", expanded=(name == "Bit")):
            st.markdown(f"""
<div style="background:#0a2010;border-left:4px solid #2a6a3a;border-radius:0 8px 8px 0;
     padding:12px 16px;margin-bottom:8px;font-size:14px;line-height:1.7">{beg}</div>""",
                        unsafe_allow_html=True)
            if level in ("Intermediate", "Advanced"):
                st.markdown(f"""
<div style="background:#0a1a30;border-left:4px solid #2a5a9e;border-radius:0 8px 8px 0;
     padding:12px 16px;margin-bottom:8px;font-size:14px;line-height:1.7">
<span style="font-size:10px;font-weight:700;color:#5a9;letter-spacing:.08em">▲ INTERMEDIATE</span><br><br>
{inter}</div>""", unsafe_allow_html=True)
            if level == "Advanced":
                st.markdown(f"""
<div style="background:#1a0a20;border-left:4px solid #6a3a9e;border-radius:0 8px 8px 0;
     padding:12px 16px;font-size:14px;line-height:1.7">
<span style="font-size:10px;font-weight:700;color:#a5d;letter-spacing:.08em">▲ ADVANCED</span><br><br>
{adv}</div>""", unsafe_allow_html=True)

    st.divider()


# ── Why binary? ───────────────────────────────────────────────────────────────

def why_binary():
    section(
        title="Why Does a Computer Use Binary?",
        icon="⚡",
        beginner="""
Computers are made of billions of tiny electrical switches called <b>transistors</b>.
A transistor can be in exactly two states: <b>conducting electricity</b> (we call this 1)
or <b>not conducting</b> (we call this 0).<br><br>
That's it. There's no "a little bit on". Either current flows or it doesn't.
So every single piece of information inside a computer — your photos, your messages,
this webpage — is ultimately stored as a huge sequence of 1s and 0s.<br><br>
We call this <b>binary</b> (from the Latin for "two at a time").
""",
        intermediate="""
The choice of binary is <b>engineering pragmatism</b>, not mathematical necessity.
Two states are easy to distinguish reliably even with electrical noise:
a voltage of 0V–0.8V means 0; 2V–3.3V means 1; everything in between is undefined/forbidden.<br><br>
<b>Why not ternary (base 3) or decimal?</b> You could build a ternary computer
(the Soviets built one: the Setun, 1958). But distinguishing three voltage levels
reliably is harder — noise margins shrink, and the logic gates become more complex.
The engineering benefit doesn't outweigh the cost.<br><br>
<b>Signal integrity</b> is the core constraint: as wires get shorter and faster,
noise, crosstalk, and thermal effects increase. Binary's wide noise margins
make it extraordinarily robust.
""",
        advanced="""
At deep-sub-micron nodes (≤5nm), transistors are no longer clean switches —
<b>subthreshold leakage</b> means a "0" transistor still conducts ~nA of current.
This is a major power problem (static power = Vdd × Ileak × N transistors)
and is why FinFETs and GAA (Gate-All-Around) transistors replaced planar MOSFETs.<br><br>
<b>Multi-level cell (MLC) NAND flash</b> deliberately exploits more than two charge
levels per cell (2 bits/cell = 4 levels, TLC = 3 bits = 8 levels, QLC = 4 bits = 16 levels)
— but at the cost of endurance and read latency. This is why QLC SSDs wear out faster.<br><br>
<b>Quantum computing</b> uses qubits which exist in superposition (both 0 and 1 simultaneously
until measured), enabling parallelism classical bits cannot achieve for specific problem classes.
Not a replacement for classical computing — a complement for certain algorithms (Shor's, Grover's).
""",
    )


# ── What is data? ─────────────────────────────────────────────────────────────

def what_is_data():
    section(
        title="What Actually Is 'Data'?",
        icon="🧬",
        beginner="""
A computer doesn't know what a letter is. It doesn't know what a colour is.
It only knows numbers.<br><br>
So we invent <b>agreements</b> about what numbers mean:<br>
<ul style="margin:8px 0 0 16px">
  <li>The number <b>65</b> means the letter <b>'A'</b> — we agreed this in a standard called ASCII.</li>
  <li>Three numbers <b>(255, 0, 0)</b> mean the colour <b>red</b> — we agreed this for screens.</li>
  <li>The number <b>440</b> means the musical note <b>A4</b> (concert pitch) — we agreed this for audio.</li>
</ul><br>
<b>Data is just numbers. Context decides what those numbers mean.</b>
The byte <code>01000001</code> is the number 65, the letter 'A', or something else entirely —
depending on what program is looking at it.
""",
        intermediate="""
This context-dependence is fundamental to understanding how computers work.
A CPU doesn't operate on "text" or "images" — it operates on bytes.
It is entirely the <b>program's responsibility</b> to interpret those bytes correctly.<br><br>
This is why type systems exist in programming languages: they track the intended
interpretation of each chunk of memory. A <code>char*</code> and an <code>int*</code>
might point to the same memory address — but the program treats the bytes differently.<br><br>
<b>Common encodings:</b>
<ul style="margin:8px 0 0 16px">
  <li><b>ASCII</b>: 7-bit, 128 characters (English only)</li>
  <li><b>UTF-8</b>: variable 1–4 bytes, covers all Unicode (109,000+ characters)</li>
  <li><b>RGB</b>: 3 bytes per pixel (red, green, blue, each 0–255)</li>
  <li><b>IEEE 754</b>: 4 or 8 bytes represent a decimal number approximately</li>
  <li><b>Two's complement</b>: how negative integers are stored in binary</li>
</ul>
""",
        advanced="""
The absence of type information at the hardware level is a <b>security attack surface</b>.
Buffer overflows overwrite adjacent memory, turning data into code (shellcode).
<b>DEP/NX</b> (Data Execution Prevention / No-Execute) marks memory pages as either
executable or writable, but not both — preventing injected data from being treated as code.<br><br>
<b>Endianness</b> is another interpretation issue: on x86 (little-endian),
the number 0x12345678 is stored as bytes <code>78 56 34 12</code> in memory
(least significant byte first). On SPARC/network protocols (big-endian) it's <code>12 34 56 78</code>.
This bites every programmer writing binary serialisation or networking code.<br><br>
<b>ASLR</b> (Address Space Layout Randomisation) randomises the addresses of code,
stack, and heap each run — making it harder to craft exploits that rely on
knowing where a particular piece of data/code lives.
""",
    )


# ── How much can we store? ────────────────────────────────────────────────────

def storage_scales():
    section(
        title="How Much Is a Gigabyte?",
        icon="💾",
        beginner="""
These prefixes tell you how many bytes something is:<br><br>
<table style="font-family:monospace;border-collapse:collapse;width:100%">
<tr style="border-bottom:1px solid #2a2d3a">
  <td style="padding:6px 12px;color:#e8a020"><b>1 Bit</b></td>
  <td style="padding:6px 12px;color:#ccc">A single 0 or 1</td>
  <td style="padding:6px 12px;color:#888">The smallest possible piece of information</td>
</tr>
<tr style="border-bottom:1px solid #2a2d3a">
  <td style="padding:6px 12px;color:#e8a020"><b>1 Byte</b></td>
  <td style="padding:6px 12px;color:#ccc">8 bits</td>
  <td style="padding:6px 12px;color:#888">One character of text</td>
</tr>
<tr style="border-bottom:1px solid #2a2d3a">
  <td style="padding:6px 12px;color:#e8a020"><b>1 Kilobyte (KB)</b></td>
  <td style="padding:6px 12px;color:#ccc">1,024 bytes</td>
  <td style="padding:6px 12px;color:#888">A short text message</td>
</tr>
<tr style="border-bottom:1px solid #2a2d3a">
  <td style="padding:6px 12px;color:#e8a020"><b>1 Megabyte (MB)</b></td>
  <td style="padding:6px 12px;color:#ccc">1,024 KB</td>
  <td style="padding:6px 12px;color:#888">One medium-resolution photo</td>
</tr>
<tr style="border-bottom:1px solid #2a2d3a">
  <td style="padding:6px 12px;color:#e8a020"><b>1 Gigabyte (GB)</b></td>
  <td style="padding:6px 12px;color:#ccc">1,024 MB</td>
  <td style="padding:6px 12px;color:#888">~200 songs, or a short film</td>
</tr>
<tr style="border-bottom:1px solid #2a2d3a">
  <td style="padding:6px 12px;color:#e8a020"><b>1 Terabyte (TB)</b></td>
  <td style="padding:6px 12px;color:#ccc">1,024 GB</td>
  <td style="padding:6px 12px;color:#888">~500 hours of HD video</td>
</tr>
<tr>
  <td style="padding:6px 12px;color:#e8a020"><b>1 Petabyte (PB)</b></td>
  <td style="padding:6px 12px;color:#ccc">1,024 TB</td>
  <td style="padding:6px 12px;color:#888">~11 years of HD video, non-stop</td>
</tr>
</table>
""",
        intermediate="""
There's an important distinction between <b>kibibytes (KiB)</b> and <b>kilobytes (KB)</b>:<br><br>
<ul style="margin:0 0 0 16px">
  <li><b>1 KB</b> = 1,000 bytes (SI standard — used by hard drive manufacturers)</li>
  <li><b>1 KiB</b> = 1,024 bytes (IEC standard — used by operating systems and programmers)</li>
</ul><br>
This is why a "1TB" hard drive shows as ~931GB in Windows — the drive uses decimal prefixes,
Windows uses binary. Neither is wrong; they're just different conventions.<br><br>
Memory addresses are also constrained by bus width:
a <b>16-bit address bus</b> can address 2¹⁶ = 65,536 bytes (64 KiB).
A <b>32-bit address bus</b> can address 4 GiB — which is why 32-bit Windows
couldn't use more than ~3.5 GB of RAM.
A <b>64-bit address bus</b> can theoretically address 16 exabytes —
though current CPUs only implement 48 physical address bits (256 TiB).
""",
        advanced="""
The <b>physical address space</b> on x86-64 is 52 bits (4 PiB) in hardware,
with 48 bits used by current OSes (256 TiB). The upper bits of a virtual address
must be sign-extended (canonical form) — a requirement that catches many pointer bugs.<br><br>
<b>Memory compression</b> (e.g. Apple's memory compression, Linux zswap) can store
2–4 bytes of data per byte of physical RAM using LZ4/ZSTD, effectively extending
addressable RAM at the cost of CPU cycles.<br><br>
<b>Near-memory and Processing-in-Memory (PIM)</b>: as data movement (DRAM ↔ CPU)
consumes more energy than computation, architectures like Samsung HBM-PIM and
Micron's UPMEM embed compute units inside the DRAM package itself — eliminating the bus bottleneck.
""",
    )


# ── Main render ───────────────────────────────────────────────────────────────

def render():
    level = st.session_state.get("level", "Intermediate")

    st.title("🌱 The Basics")

    # Level indicator banner
    level_colors = {
        "Beginner":     ("#0a2010", "#2a6a3a", "#5d5", "You're seeing essential beginner content."),
        "Intermediate": ("#0a1a30", "#2a5a9e", "#5af", "You're seeing beginner content + technical depth."),
        "Advanced":     ("#1a0a20", "#6a3a9e", "#a5d", "You're seeing all levels: beginner + intermediate + advanced detail."),
    }
    bg, border, text, msg = level_colors[level]
    st.markdown(f"""
<div style="background:{bg};border:1px solid {border};border-radius:8px;
     padding:10px 16px;margin-bottom:20px;font-size:13px;color:{text}">
📊 <b>Difficulty: {level}</b> — {msg}
Use the slider in the sidebar to change level.
</div>""", unsafe_allow_html=True)

    st.markdown("""
Before anything else — before CPUs, before operating systems, before the internet —
there are just two things: **0** and **1**. Everything a computer has ever done
comes down to manipulating those two values at incredible speed.

This page builds from that foundation up.
""")

    st.divider()
    why_binary()
    what_is_data()

    # Interactive bit builder
    bit_builder()

    data_types_table()
    storage_scales()
    analogy_cards()