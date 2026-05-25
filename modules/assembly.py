"""Assembly Language Walkthrough page."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import streamlit as st
import pandas as pd
from core.cpu import CPU, INSTRUCTIONS, process_input
from core.reference import to_binary, to_hex, bit_groups


EXAMPLE_PROGRAMS = {
    "Hello (store 'H')": {
        "description": "Load ASCII value of 'H' (0x48) and store it to the display buffer.",
        "source": """; Store the letter 'H' to display buffer
; 'H' = ASCII 72 = 0x48

LOAD  [0xD0]   ; A ← keyboard I/O register (pre-loaded with 0x48)
STORE [0xF0]   ; [0xF0] ← A  (video buffer)
OUT   6        ; Send A to display port
HLT            ; Stop""",
        "bytecode": [0x01, 0xD0,   # LOAD [0xD0]
                     0x02, 0xF0,   # STORE [0xF0]
                     0x11, 0x06,   # OUT 6
                     0xFF],        # HLT
        "setup": lambda cpu: cpu.memory.write(0xD0, 0x48),
    },
    "Add two numbers": {
        "description": "Load two values from memory, add them, store the result.",
        "source": """; Add value at 0xA0 to value at 0xA1, store result at 0xA2
LOAD  [0xA0]   ; A ← first operand (42)
ADD   [0xA1]   ; A ← A + second operand (13) = 55
STORE [0xA2]   ; [0xA2] ← 55
HLT""",
        "bytecode": [0x01, 0xA0,
                     0x03, 0xA1,
                     0x02, 0xA2,
                     0xFF],
        "setup": lambda cpu: (cpu.memory.write(0xA0, 42), cpu.memory.write(0xA1, 13)),
    },
    "Countdown loop": {
        "description": "Load 5, decrement until zero, then halt. Demonstrates branches and flags.",
        "source": """; Countdown from 5 to 0
LOAD  [0xA0]   ; A ← 5 (our counter)
loop:
SUB   1        ; A ← A - 1
STORE [0xA0]   ; save updated counter
CMP   0        ; set Zero flag if A == 0
JNZ   loop     ; if A != 0, jump back to loop
HLT            ; A == 0, done""",
        "bytecode": [0x01, 0xA0,   # LOAD [0xA0]  (counter=5)
                     0x04, 0x01,   # SUB 1
                     0x02, 0xA0,   # STORE [0xA0]
                     0x08, 0x00,   # CMP 0
                     0x0B, 0x71,   # JNZ loop (back to 0x71 = SUB)
                     0xFF],        # HLT
        "setup": lambda cpu: cpu.memory.write(0xA0, 5),
    },
    "Push/pop stack": {
        "description": "Push three values, pop them back — demonstrating LIFO order.",
        "source": """; Push 3 values, pop them back (LIFO)
LOAD  [0xA0]   ; A ← 0x10
PUSH           ; push 0x10
LOAD  [0xA1]   ; A ← 0x20
PUSH           ; push 0x20
LOAD  [0xA2]   ; A ← 0x30
PUSH           ; push 0x30
POP            ; A ← 0x30  (last in, first out)
STORE [0xB0]   ; save it
POP            ; A ← 0x20
STORE [0xB1]
POP            ; A ← 0x10
STORE [0xB2]
HLT""",
        "bytecode": [0x01, 0xA0,  0x0C,
                     0x01, 0xA1,  0x0C,
                     0x01, 0xA2,  0x0C,
                     0x0D,        0x02, 0xB0,
                     0x0D,        0x02, 0xB1,
                     0x0D,        0x02, 0xB2,
                     0xFF],
        "setup": lambda cpu: (cpu.memory.write(0xA0, 0x10),
                              cpu.memory.write(0xA1, 0x20),
                              cpu.memory.write(0xA2, 0x30)),
    },
    "Subroutine call": {
        "description": "Call a subroutine, which doubles A, then return.",
        "source": """; main: call double() subroutine
LOAD  [0xA0]   ; A ← 7
CALL  double   ; push return addr, jump to double
STORE [0xA1]   ; save result (14)
HLT

double:
ADD   A        ; A ← A + A  (double it)
RET            ; return to caller""",
        "bytecode": [0x01, 0xA0,   # LOAD [0xA0]  A=7
                     0x0E, 0x79,   # CALL 0x79 (double routine)
                     0x02, 0xA1,   # STORE [0xA1]
                     0xFF,         # HLT
                     # double at 0x77:
                     0x03, 0x07,   # ADD 7  (A=7+7=14, simulated)
                     0x0F],        # RET
        "setup": lambda cpu: cpu.memory.write(0xA0, 7),
    },
    "I/O: read and echo": {
        "description": "Read a byte from I/O port 0 (keyboard) and write it to port 6 (display).",
        "source": """; Read from keyboard port, echo to display
IN    0        ; A ← I/O port 0 (keyboard register)
OUT   6        ; I/O port 6 ← A  (display)
STORE [0xF0]   ; also store to video buffer
HLT""",
        "bytecode": [0x10, 0x00,   # IN 0
                     0x11, 0x06,   # OUT 6
                     0x02, 0xF0,   # STORE [0xF0]
                     0xFF],        # HLT
        "setup": lambda cpu: cpu.memory.write(0xD0, ord('Z')),
    },
}


def render():
    st.title("Assembly Language Walkthrough")
    level = st.session_state.get("level", "Intermediate")

    st.info("**Assembly language** is the lowest level language humans can read. "
                "Each line is one instruction the CPU understands directly. "
                "Below machine code (raw numbers), above nothing.")

    st.markdown("""
Assembly is a 1-to-1 mapping between human-readable **mnemonics** and machine **opcodes**.
When you write `ADD 5`, the assembler translates it to `0x03 0x05` — two bytes the CPU fetches and executes.
""")

    # Instruction set reference
    st.markdown("## Instruction Set (our 8-bit ISA)")
    isa_rows = []
    for opcode, (mnemonic, desc, operands) in INSTRUCTIONS.items():
        size = 1 + len(operands)
        example = {
            "LOAD":  "LOAD [0xA0]  ; A ← memory[0xA0]",
            "STORE": "STORE [0xA0] ; memory[0xA0] ← A",
            "ADD":   "ADD 5        ; A ← A + 5",
            "SUB":   "SUB 1        ; A ← A - 1",
            "AND":   "AND 0x0F     ; mask low nibble",
            "OR":    "OR  0x80     ; set bit 7",
            "XOR":   "XOR 0xFF     ; invert all bits",
            "CMP":   "CMP 0        ; set Z if A == 0",
            "JMP":   "JMP 0x70     ; jump to 0x70",
            "JZ":    "JZ  done     ; jump if Z=1",
            "JNZ":   "JNZ loop     ; jump if Z=0",
            "PUSH":  "PUSH         ; push A to stack",
            "POP":   "POP          ; pop stack → A",
            "CALL":  "CALL func    ; call subroutine",
            "RET":   "RET          ; return from sub",
            "IN":    "IN 0         ; A ← port 0",
            "OUT":   "OUT 6        ; port 6 ← A",
            "NOP":   "NOP          ; do nothing",
            "HLT":   "HLT          ; halt CPU",
        }.get(mnemonic, mnemonic)
        isa_rows.append({
            "Opcode": f"0x{opcode:02X}",
            "Binary": to_binary(opcode),
            "Mnemonic": mnemonic,
            "Size (bytes)": size,
            "Description": desc,
            "Example": example,
        })
    df = pd.DataFrame(isa_rows)
    st.dataframe(df, hide_index=True, use_container_width=True, height=350)

    # Machine code dissection
    st.divider()
    st.markdown("## Machine Code Dissection")
    st.caption("Enter hex bytes and see them decoded instruction by instruction.")

    hex_input = st.text_input("Hex bytes (space-separated)", value="01 A0 03 05 02 A1 FF",
                               help="Each opcode is one byte; operands follow immediately.")
    if hex_input:
        try:
            raw_bytes = [int(b, 16) for b in hex_input.strip().split()]
            decoded = []
            i = 0
            while i < len(raw_bytes):
                opcode = raw_bytes[i]
                if opcode in INSTRUCTIONS:
                    mnemonic, desc, operands = INSTRUCTIONS[opcode]
                    ops = []
                    for op_name in operands:
                        i += 1
                        if i < len(raw_bytes):
                            ops.append(f"0x{raw_bytes[i]:02X}")
                        else:
                            ops.append("??")
                    decoded.append({
                        "Addr": f"0x{0x70+i-len(ops):02X}",
                        "Bytes": " ".join(f"{raw_bytes[i-len(ops)+j]:02X}" for j in range(len(ops)+1)),
                        "Instruction": f"{mnemonic} {' '.join(ops)}".strip(),
                        "Description": desc,
                    })
                else:
                    decoded.append({"Addr": f"0x{0x70+i:02X}", "Bytes": f"{opcode:02X}",
                                    "Instruction": f"??? (0x{opcode:02X})", "Description": "Unknown opcode"})
                i += 1
            df2 = pd.DataFrame(decoded)
            st.dataframe(df2, hide_index=True, use_container_width=True)
        except Exception as e:
            st.error(f"Parse error: {e}")

    # Example programs
    st.divider()
    st.markdown("## Example Programs")
    prog_name = st.selectbox("Select program", list(EXAMPLE_PROGRAMS.keys()))
    prog = EXAMPLE_PROGRAMS[prog_name]

    st.markdown(f"**{prog['description']}**")
    st.code(prog["source"], language="asm")

    # Show bytecode
    with st.expander("Machine code (assembled bytes)"):
        bytecode = prog["bytecode"]
        bc_rows = []
        i = 0
        while i < len(bytecode):
            opcode = bytecode[i]
            if opcode in INSTRUCTIONS:
                mnemonic, _, operands = INSTRUCTIONS[opcode]
                ops = bytecode[i+1:i+1+len(operands)]
                bc_rows.append({
                    "Address": f"0x{0x70+i:02X}",
                    "Hex": " ".join(f"{b:02X}" for b in [opcode]+ops),
                    "Binary": " ".join(to_binary(b) for b in [opcode]+ops),
                    "Assembly": f"{mnemonic} {' '.join(f'0x{o:02X}' for o in ops)}".strip(),
                })
                i += 1 + len(operands)
            else:
                bc_rows.append({"Address": f"0x{0x70+i:02X}",
                                "Hex": f"{opcode:02X}", "Binary": to_binary(opcode), "Assembly": "???"})
                i += 1
        df3 = pd.DataFrame(bc_rows)
        st.dataframe(df3, hide_index=True, use_container_width=True)

    if st.button("Run this program", type="primary"):
        cpu = CPU()
        prog["setup"](cpu)
        bytecode = prog["bytecode"]
        steps = cpu.run_program(bytecode)
        st.session_state["asm_cpu"]   = cpu
        st.session_state["asm_steps"] = steps
        st.session_state["asm_prog"]  = prog_name

    if "asm_cpu" in st.session_state:
        cpu   = st.session_state["asm_cpu"]
        steps = st.session_state["asm_steps"]
        st.divider()
        st.markdown(f"### Execution trace: *{st.session_state['asm_prog']}*")

        m1,m2,m3 = st.columns(3)
        m1.metric("Clock cycles",    cpu.cycle)
        m2.metric("Instructions",    sum(1 for s in steps if s.phase=="execute"))
        m3.metric("Memory writes",   sum(len(s.mem_changed) for s in steps))

        tab1, tab2 = st.tabs(["Step log", "Final register state"])
        with tab1:
            phase_colors = {"fetch":"#cff4fc","decode":"#fff3cd","execute":"#d1e7dd",
                            "writeback":"#e2d9f3","interrupt":"#f8d7da","dma":"#fde8d8"}
            for step in steps:
                color = phase_colors.get(step.phase, "#f8f9fa")
                with st.expander(f"[{step.phase.upper():12s}] Cycle {step.cycle:3d} — {step.description}"):
                    st.markdown(f"""<div style="background:{color};border-radius:6px;padding:10px">
{step.detail}</div>""", unsafe_allow_html=True)
                    if step.reg_snapshot:
                        r = step.reg_snapshot
                        st.code(f"A={r['A']:3d} (0x{r['A']:02X})  B={r['B']:3d}  PC=0x{r['PC']:04X}  "
                                f"SP=0x{r['SP']:02X}  MAR=0x{r['MAR']:04X}  MDR=0x{r['MDR']:02X}  "
                                f"CIR={r['CIR']}", language="text")
                    for addr, val in step.mem_changed:
                        region = cpu.memory.region_for(addr)
                        rname  = region.name if region else "unknown"
                        st.caption(f"Memory write: [{rname}] 0x{addr:02X} ← 0x{val:02X} = {val} = '{chr(val) if 32<=val<=126 else '?'}'")

        with tab2:
            r = steps[-1].reg_snapshot if steps else {}
            if r:
                rcols = st.columns(4)
                for col, (k,v) in zip(rcols*4, r.items()):
                    if isinstance(v,int):
                        col.metric(k, f"0x{v:02X}", delta=f"={v}")

    # Write-your-own
    st.divider()
    st.markdown("## Write Your Own Program")
    st.caption("Enter hex opcodes directly. Use the instruction table above for reference.")
    custom_hex = st.text_area("Hex program (space or newline separated)",
                               value="01 A0\n03 05\n02 A1\nFF",
                               height=120, help="Loaded at 0x70. Pre-set 0xA0=10.")
    mem_setup = st.text_input("Pre-set memory (format: addr=val, comma separated)", value="A0=10, A1=20")

    if st.button("Run custom program"):
        try:
            raw = [int(b, 16) for b in custom_hex.replace('\n',' ').split() if b]
            cpu2 = CPU()
            for pair in mem_setup.split(","):
                pair = pair.strip()
                if "=" in pair:
                    a,v = pair.split("=")
                    cpu2.memory.write(int(a.strip(),16), int(v.strip()))
            steps2 = cpu2.run_program(raw)
            st.success(f"Ran {len(raw)} bytes — {cpu2.cycle} cycles — {sum(1 for s in steps2 if s.phase=='execute')} instructions executed.")
            m1,m2 = st.columns(2)
            r = steps2[-1].reg_snapshot if steps2 else {}
            if r:
                m1.markdown(f"**A** = 0x{r['A']:02X} ({r['A']})")
                m1.markdown(f"**PC** = 0x{r['PC']:04X}")
                m2.markdown(f"**SP** = 0x{r['SP']:02X}")
                m2.markdown(f"**Cycles** = {cpu2.cycle}")
            for step in steps2:
                for addr,val in step.mem_changed:
                    st.caption(f"Wrote 0x{val:02X} to 0x{addr:02X}")
        except Exception as e:
            st.error(f"Error: {e}")
