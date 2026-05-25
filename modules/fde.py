"""Fetch-Decode-Execute (and writeback) deep-dive page."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import streamlit as st
import pandas as pd
from core.cpu import CPU, INSTRUCTIONS
from core.reference import to_binary, to_hex, bit_groups


CYCLE_STAGES = [
    {
        "name": "1 — FETCH (Address)",
        "short": "Fetch addr",
        "color": "#cff4fc",
        "text_color": "#055160",
        "description": "The CPU places the **Program Counter (PC)** value onto the **address bus**. "
                       "The control bus asserts **RD** (read). This tells memory: 'give me what's at this address'.",
        "registers": ["PC → MAR"],
        "buses": ["Address bus: carries PC value", "Control bus: RD asserted"],
        "analogy": "Like giving the post office an address and saying 'what letter is here?'",
        "advanced": "The MAR (Memory Address Register) buffers the address so the PC can increment independently. "
                    "Modern CPUs pipeline this — the next instruction's address is sent before the current one is decoded.",
    },
    {
        "name": "2 — FETCH (Data)",
        "short": "Fetch data",
        "color": "#cff4fc",
        "text_color": "#055160",
        "description": "Memory responds by putting the instruction byte on the **data bus**. "
                       "The CPU reads it into the **MDR**, then copies it to the **IR** (Instruction Register). "
                       "The **PC increments** to point at the next byte.",
        "registers": ["Memory → MDR", "MDR → IR", "PC = PC + 1"],
        "buses": ["Data bus: carries opcode byte"],
        "analogy": "The post office hands you the letter. You open the envelope (MDR) and read the first line (IR).",
        "advanced": "This is the 'fetch' in Harvard vs Von Neumann: Von Neumann uses the same bus for instructions "
                    "and data (bottleneck). Harvard has separate buses — instruction fetch and data read can overlap.",
    },
    {
        "name": "3 — DECODE",
        "short": "Decode",
        "color": "#fff3cd",
        "text_color": "#664d03",
        "description": "The **control unit** reads the opcode in the IR and generates **micro-operations** — "
                       "internal signals that configure the ALU, multiplexers, and register paths for the next phase.",
        "registers": ["IR → Control Unit → micro-ops"],
        "buses": ["Internal control signals only (no external bus activity)"],
        "analogy": "Reading the recipe title and understanding what ingredients and steps you'll need.",
        "advanced": "In CISC processors (x86), complex instructions are decoded into multiple micro-ops (μops). "
                    "RISC processors have fixed-length, simple instructions that decode in a single cycle. "
                    "Modern CPUs use a decode cache (μop cache) to skip re-decoding hot instructions.",
    },
    {
        "name": "4 — EXECUTE",
        "short": "Execute",
        "color": "#d1e7dd",
        "text_color": "#0a3622",
        "description": "The **ALU** performs the operation (arithmetic, logic, comparison, or address calculation). "
                       "For memory instructions, the MAR is loaded with the target address and another memory cycle begins.",
        "registers": ["ALU_A + ALU_B → ALU_OUT", "Flags updated (Z, C, N, V)"],
        "buses": ["Address bus + Data bus (for LOAD/STORE)", "Control bus: RD or WR"],
        "analogy": "Actually cooking — mixing ingredients, applying heat, making the dish.",
        "advanced": "Out-of-order execution (OoO): modern CPUs reorder instructions to avoid stalls — "
                    "execute instruction 3 before instruction 2 if instruction 2 is waiting on a cache miss. "
                    "The reservation station holds instructions waiting for their operands.",
    },
    {
        "name": "5 — WRITEBACK",
        "short": "Writeback",
        "color": "#e2d9f3",
        "text_color": "#3d0a91",
        "description": "The result from the ALU is written back to a **register** (or to memory for STORE). "
                       "The **flags register** is updated. Pending **interrupts** are checked.",
        "registers": ["ALU_OUT → destination register", "FLAGS updated", "IRQ check"],
        "buses": ["Address + Data bus for write-through cache STORE operations"],
        "analogy": "Setting out the dish, noting in the recipe book that you completed this step.",
        "advanced": "Write-back vs write-through caches: write-back only writes to RAM when a cache line is evicted "
                    "(faster, more complex). Write-through writes to RAM on every store (slower, simpler, safer). "
                    "Register renaming eliminates write-after-write (WAW) hazards in superscalar CPUs.",
    },
]


def render_stage_card(stage, expanded=False):
    with st.expander(stage["name"], expanded=expanded):
        level = st.session_state.get("level","Intermediate")
        st.markdown(f"""
<div style="background:{stage['color']};color:{stage['text_color']};
     border-radius:8px;padding:12px 16px;margin-bottom:10px">
{stage['description']}
</div>""", unsafe_allow_html=True)
        rc1, rc2 = st.columns(2)
        with rc1:
            st.markdown("**Register operations:**")
            for r in stage["registers"]:
                st.markdown(f"- `{r}`")
        with rc2:
            st.markdown("**Bus activity:**")
            for b in stage["buses"]:
                st.markdown(f"- {b}")
        if level == "Beginner":
            st.info(stage["analogy"])
        if level == "Advanced":
            st.markdown("---")
            st.markdown(f"**Deep dive:** {stage['advanced']}")


def render_fde_animation():
    """Interactive step-through of a concrete LOAD instruction."""
    st.markdown("## Worked Example: `LOAD 0xA0`")
    st.caption("Click through each micro-step of loading value from address 0xA0 into register A.")

    steps = [
        {"label": "PC on address bus",
         "state": {"PC":0x70,"MAR":0x70,"MDR":"—","IR":"—","A":"—","Bus_addr":"0x0070","Bus_data":"—","Bus_ctrl":"RD"},
         "explain": "PC=0x70 placed on address bus. MAR latches 0x70. Control bus: RD asserted."},
        {"label": "Opcode arrives (0x01 = LOAD)",
         "state": {"PC":0x71,"MAR":0x70,"MDR":"0x01","IR":"0x01","A":"—","Bus_addr":"0x0070","Bus_data":"0x01","Bus_ctrl":"RD"},
         "explain": "Memory puts 0x01 (LOAD opcode) on data bus. MDR=0x01. IR=0x01. PC increments to 0x71."},
        {"label": "Fetch operand (address 0xA0)",
         "state": {"PC":0x72,"MAR":0x71,"MDR":"0xA0","IR":"0x01","A":"—","Bus_addr":"0x0071","Bus_data":"0xA0","Bus_ctrl":"RD"},
         "explain": "Second fetch cycle: PC=0x71 on address bus. MDR=0xA0 (the address to load from). PC→0x72."},
        {"label": "Decode: LOAD instruction",
         "state": {"PC":0x72,"MAR":0x71,"MDR":"0xA0","IR":"0x01","A":"—","Bus_addr":"—","Bus_data":"—","Bus_ctrl":"—"},
         "explain": "Control unit decodes 0x01 as LOAD. Prepares: route MDR→MAR, then memory read, then MDR→A."},
        {"label": "Execute: address phase (MAR←0xA0)",
         "state": {"PC":0x72,"MAR":0xA0,"MDR":"0xA0","IR":"0x01","A":"—","Bus_addr":"0x00A0","Bus_data":"—","Bus_ctrl":"RD"},
         "explain": "MAR←0xA0. Address bus = 0x00A0. Control bus: RD. Waiting for data from memory/cache."},
        {"label": "Execute: data phase (MDR←value)",
         "state": {"PC":0x72,"MAR":0xA0,"MDR":"0x48","IR":"0x01","A":"—","Bus_addr":"0x00A0","Bus_data":"0x48","Bus_ctrl":"RD"},
         "explain": "Memory responds: 0x48 ('H') on data bus. MDR=0x48. Cache line loaded if miss."},
        {"label": "Writeback: A←MDR",
         "state": {"PC":0x72,"MAR":0xA0,"MDR":"0x48","IR":"0x01","A":"0x48","Bus_addr":"—","Bus_data":"—","Bus_ctrl":"—"},
         "explain": "ALU routes MDR→A. A=0x48='H'. Zero flag=0. Interrupt check. Next cycle starts at PC=0x72."},
    ]

    if "fde_step" not in st.session_state:
        st.session_state["fde_step"] = 0

    step_idx = st.session_state["fde_step"]
    step     = steps[step_idx]
    s        = step["state"]

    st.progress((step_idx+1)/len(steps))
    st.markdown(f"**Step {step_idx+1}/{len(steps)}: {step['label']}**")
    st.info(step["explain"])

    # Register file display
    reg_cols = st.columns(8)
    reg_items = [("PC",s["PC"]),("MAR",s["MAR"]),("MDR",s["MDR"]),
                 ("IR",s["IR"]),("A",s["A"]),
                 ("ADDR bus",s["Bus_addr"]),("DATA bus",s["Bus_data"]),("CTRL",s["Bus_ctrl"])]
    for col,(name,val) in zip(reg_cols, reg_items):
        if isinstance(val,int):
            col.markdown(f"**{name}**\n\n`0x{val:02X}`")
        else:
            highlight = val != "—"
            col.markdown(f"**{name}**\n\n`{val}`" + (" 🔵" if highlight else ""))

    nav1,nav2,nav3 = st.columns([1,1,4])
    with nav1:
        if st.button("◀ Prev", disabled=step_idx==0):
            st.session_state["fde_step"] -= 1
            st.rerun()
    with nav2:
        if st.button("Next ▶", disabled=step_idx==len(steps)-1):
            st.session_state["fde_step"] += 1
            st.rerun()
    with nav3:
        if st.button("Reset to start"):
            st.session_state["fde_step"] = 0
            st.rerun()


def render():
    st.title("Fetch-Decode-Execute Cycle")
    level = st.session_state.get("level","Intermediate")

    st.info("**The Fetch-Decode-Execute cycle** is the heartbeat of every computer. "
                "The CPU repeats it billions of times per second, forever, for every instruction in every program you run.")

    st.markdown("""
The CPU never 'reads a program'. It blindly follows a loop:
1. **Fetch** the next instruction byte from memory
2. **Decode** what that byte means
3. **Execute** the operation
4. **Writeback** the result
5. Go back to step 1
""")

    # Architecture overview
    st.markdown("## The Five Stages")
    for i, stage in enumerate(CYCLE_STAGES):
        render_stage_card(stage, expanded=(i==0))

    st.divider()

    # Interactive walkthrough
    render_fde_animation()

    # Instruction set reference
    st.divider()
    st.markdown("## Instruction Set Reference")
    st.caption("Every opcode the simulator understands:")
    rows = []
    for opcode, (mnemonic, desc, operands) in INSTRUCTIONS.items():
        rows.append({
            "Opcode (hex)": f"0x{opcode:02X}",
            "Opcode (bin)": to_binary(opcode),
            "Mnemonic":     mnemonic,
            "Operands":     ", ".join(operands) if operands else "none",
            "Description":  desc,
        })
    df = pd.DataFrame(rows)
    st.dataframe(df, hide_index=True, use_container_width=True)

    if level == "Advanced":
        st.divider()
        st.markdown("## Pipeline Hazards")
        st.markdown("""
Modern CPUs pipeline stages: while one instruction executes, the next is being decoded, and the one after that is being fetched.
Three classes of hazard disrupt this:

| Hazard | Cause | Solution |
|---|---|---|
| **Structural** | Two instructions need the same hardware unit | Stall one pipeline stage |
| **Data (RAW)** | Instruction B reads a register that A hasn't written yet | Operand forwarding (bypass) |
| **Control** | Branch target isn't known until execute | Branch prediction + speculative execution |

*Example RAW hazard:*
```asm
ADD  A, 0x10    ; writes A
STORE A, [0x50] ; reads A — must wait for ADD to writeback
```
Forwarding sends A's result directly from the ALU output to STORE's input without waiting for the writeback register file write.
""")
