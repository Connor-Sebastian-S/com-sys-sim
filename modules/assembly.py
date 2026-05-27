import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import streamlit as st
import pandas as pd
from core.cpu import CPU, INSTRUCTIONS, process_input
from core.reference import to_binary, to_hex, bit_groups


# ── Example programs ──────────────────────────────────────────────────────────

EXAMPLE_PROGRAMS = {
    "Add two numbers": {
        "description": "Load two values from memory, add them, store the result.",
        "concepts": ["LOAD / STORE", "ADD", "HLT"],
        "walkthrough": (
            "We start simple: fetch two numbers from memory, add them in the accumulator, "
            "and write the result back. This is the skeleton of almost every arithmetic "
            "operation a CPU performs."
        ),
        "source": """; Add value at 0xA0 to value at 0xA1, store result at 0xA2
LOAD  [0xA0]   ; A ← first operand  (42)
ADD   [0xA1]   ; A ← A + second operand (13) = 55
STORE [0xA2]   ; [0xA2] ← 55
HLT            ; stop""",
        "bytecode": [0x01, 0xA0, 0x03, 0xA1, 0x02, 0xA2, 0xFF],
        "setup": lambda cpu: (cpu.memory.write(0xA0, 42), cpu.memory.write(0xA1, 13)),
    },
    "Hello (store 'H')": {
        "description": "Load ASCII value of 'H' (0x48) and write it to the display buffer.",
        "concepts": ["LOAD", "STORE", "OUT", "I/O ports"],
        "walkthrough": (
            "Characters are just numbers. 'H' is ASCII 72 (0x48). We load that byte, "
            "write it to the video buffer in memory, and also send it to I/O port 6 "
            "(the display port). Memory-mapped I/O in action."
        ),
        "source": """; Store the letter 'H' to display buffer
; 'H' = ASCII 72 = 0x48
LOAD  [0xD0]   ; A ← keyboard I/O register (pre-loaded with 0x48)
STORE [0xF0]   ; [0xF0] ← A  (video buffer)
OUT   6        ; send A to display port
HLT""",
        "bytecode": [0x01, 0xD0, 0x02, 0xF0, 0x11, 0x06, 0xFF],
        "setup": lambda cpu: cpu.memory.write(0xD0, 0x48),
    },
    "Countdown loop": {
        "description": "Load 5, decrement until zero — demonstrates branches and flags.",
        "concepts": ["SUB", "CMP", "JNZ", "Zero flag", "loops"],
        "walkthrough": (
            "This is how every loop works at the hardware level. Decrement a counter, "
            "compare it to zero, and jump back if the Zero flag isn't set. "
            "When A hits 0 the Zero flag fires, JNZ falls through, and we halt."
        ),
        "source": """; Countdown from 5 to 0
LOAD  [0xA0]   ; A ← 5 (our counter)
loop:
SUB   1        ; A ← A - 1
STORE [0xA0]   ; save updated counter
CMP   0        ; set Zero flag if A == 0
JNZ   loop     ; if A != 0, jump back to loop
HLT            ; A == 0, done""",
        "bytecode": [0x01, 0xA0, 0x04, 0x01, 0x02, 0xA0, 0x08, 0x00, 0x0B, 0x71, 0xFF],
        "setup": lambda cpu: cpu.memory.write(0xA0, 5),
    },
    "Push/pop stack": {
        "description": "Push three values, pop them back — demonstrating LIFO order.",
        "concepts": ["PUSH", "POP", "stack pointer", "LIFO"],
        "walkthrough": (
            "The stack is a Last-In First-Out buffer. Each PUSH decrements the stack "
            "pointer and writes A there. Each POP reads from that address and increments "
            "SP. Notice the pop order is always the reverse of the push order."
        ),
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
        "bytecode": [0x01, 0xA0, 0x0C,
                     0x01, 0xA1, 0x0C,
                     0x01, 0xA2, 0x0C,
                     0x0D, 0x02, 0xB0,
                     0x0D, 0x02, 0xB1,
                     0x0D, 0x02, 0xB2,
                     0xFF],
        "setup": lambda cpu: (cpu.memory.write(0xA0, 0x10),
                              cpu.memory.write(0xA1, 0x20),
                              cpu.memory.write(0xA2, 0x30)),
    },
    "Subroutine call": {
        "description": "Call a subroutine that doubles A, then return.",
        "concepts": ["CALL", "RET", "stack frames", "subroutines"],
        "walkthrough": (
            "CALL pushes the return address onto the stack and jumps to the subroutine. "
            "RET pops that address back into the Program Counter. This is exactly how "
            "function calls work in C, Python — every language, all the way down."
        ),
        "source": """; main: call double() subroutine
LOAD  [0xA0]   ; A ← 7
CALL  double   ; push return addr, jump to double
STORE [0xA1]   ; save result (14)
HLT

double:
ADD   A        ; A ← A + A  (double it)
RET            ; return to caller""",
        "bytecode": [0x01, 0xA0, 0x0E, 0x79, 0x02, 0xA1, 0xFF,
                     0x03, 0x07, 0x0F],
        "setup": lambda cpu: cpu.memory.write(0xA0, 7),
    },
    "I/O: read and echo": {
        "description": "Read a byte from I/O port 0 (keyboard) and echo it to port 6 (display).",
        "concepts": ["IN", "OUT", "I/O ports", "memory-mapped I/O"],
        "walkthrough": (
            "IN reads from a hardware port into A. OUT writes A to a port. "
            "Port 0 is the keyboard register; port 6 is the display. "
            "This two-instruction sequence is the core of every terminal echo loop."
        ),
        "source": """; Read from keyboard port, echo to display
IN    0        ; A ← I/O port 0 (keyboard register)
OUT   6        ; I/O port 6 ← A  (display)
STORE [0xF0]   ; also store to video buffer
HLT""",
        "bytecode": [0x10, 0x00, 0x11, 0x06, 0x02, 0xF0, 0xFF],
        "setup": lambda cpu: cpu.memory.write(0xD0, ord('Z')),
    },
}

# Grouped ISA for chapter 2
ISA_GROUPS = {
    "Memory & registers": ["LOAD", "STORE", "NOP"],
    "Arithmetic":         ["ADD", "SUB"],
    "Logic":              ["AND", "OR", "XOR"],
    "Compare & branch":   ["CMP", "JMP", "JZ", "JNZ"],
    "Stack":              ["PUSH", "POP"],
    "Subroutines":        ["CALL", "RET"],
    "I/O":                ["IN", "OUT"],
    "Control":            ["HLT"],
}

ISA_EXAMPLES = {
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
    "PUSH":  "PUSH         ; push A onto stack",
    "POP":   "POP          ; pop stack → A",
    "CALL":  "CALL func    ; call subroutine",
    "RET":   "RET          ; return from sub",
    "IN":    "IN 0         ; A ← port 0",
    "OUT":   "OUT 6        ; port 6 ← A",
    "NOP":   "NOP          ; do nothing",
    "HLT":   "HLT          ; halt CPU",
}


# ── Navigation helpers ────────────────────────────────────────────────────────

CHAPTERS = [
    "What is assembly?",
    "The instruction set",
    "Reading machine code",
    "Example programs",
    "Step-by-step execution",
    "Write your own program",
]


def _nav_html(current: int) -> str:
    dots = []
    for i, title in enumerate(CHAPTERS):
        if i < current:
            colour = "#888"
        elif i == current:
            colour = "#1D9E75"
        else:
            colour = "#ddd"
        dots.append(
            f'<span title="{title}" style="display:inline-block;width:10px;height:10px;'
            f'border-radius:50%;background:{colour};margin:0 4px"></span>'
        )
    return (
        f'<div style="text-align:center;margin-bottom:8px">{"".join(dots)}</div>'
        f'<div style="text-align:center;font-size:12px;color:#888;margin-bottom:1rem">'
        f'Chapter {current + 1} of {len(CHAPTERS)} — {CHAPTERS[current]}</div>'
    )


def _prev_next(ch: int):
    cols = st.columns([1, 4, 1])
    with cols[0]:
        if ch > 0 and st.button("← Back", key=f"back_{ch}"):
            st.session_state["asm_chapter"] = ch - 1
            st.rerun()
    with cols[2]:
        label = "Continue →" if ch < len(CHAPTERS) - 1 else "Finish ✓"
        if st.button(label, key=f"next_{ch}", type="primary"):
            if ch < len(CHAPTERS) - 1:
                st.session_state["asm_chapter"] = ch + 1
                st.rerun()


def _bytecode_table(bytecode: list) -> pd.DataFrame:
    rows = []
    i = 0
    while i < len(bytecode):
        opcode = bytecode[i]
        if opcode in INSTRUCTIONS:
            mnemonic, _, operands = INSTRUCTIONS[opcode]
            ops = bytecode[i + 1: i + 1 + len(operands)]
            rows.append({
                "Address": f"0x{0x70 + i:02X}",
                "Hex":     " ".join(f"{b:02X}" for b in [opcode] + ops),
                "Binary":  " ".join(to_binary(b) for b in [opcode] + ops),
                "Assembly": f"{mnemonic} {' '.join(f'0x{o:02X}' for o in ops)}".strip(),
            })
            i += 1 + len(operands)
        else:
            rows.append({
                "Address": f"0x{0x70 + i:02X}",
                "Hex": f"{opcode:02X}",
                "Binary": to_binary(opcode),
                "Assembly": f"??? (0x{opcode:02X})",
            })
            i += 1
    return pd.DataFrame(rows)


# ── Chapter renderers ─────────────────────────────────────────────────────────

def _ch0_what_is_assembly():
    st.markdown("""
Assembly is the lowest level of programming that humans can reasonably read and write.
Every line maps to exactly one CPU instruction. There's no compiler translating your
intent — what you write is what the chip executes.
""")

    st.info(
        "**Where does assembly sit?**  \n"
        "High-level code (Python, C) → compiler → **Assembly** → assembler → "
        "Machine code (raw bytes) → CPU"
    )

    st.markdown("#### The key idea: mnemonics ↔ opcodes")
    st.markdown("""
An **assembler** does one mechanical job: replace human-readable mnemonics with
their numeric opcode equivalents. That's the entire translation.
""")

    col1, col2, col3 = st.columns(3)
    col1.markdown("**You write**")
    col1.code("ADD 5\nSTORE [0xA0]\nHLT", language="asm")
    col2.markdown("**Assembler produces**")
    col2.code("03 05\n02 A0\nFF", language="text")
    col3.markdown("**CPU sees (binary)**")
    col3.code("00000011 00000101\n00000010 10100000\n11111111", language="text")

    st.divider()

    st.markdown("#### Registers — the CPU's scratchpad")
    st.markdown("""
Our 8-bit CPU has a small set of registers. Unlike memory, registers live
**inside** the CPU — accessing them takes zero clock cycles.
""")

    reg_data = {
        "Register": ["A (accumulator)", "PC (program counter)", "SP (stack pointer)",
                     "MAR", "MDR", "CIR", "Flags (Z N C V)"],
        "Width": ["8-bit", "16-bit", "8-bit", "16-bit", "8-bit", "8-bit", "4 bits"],
        "Purpose": [
            "All ALU operations happen here — it's the main working register",
            "Address of the next instruction to fetch",
            "Points to the top of the stack in memory",
            "Memory Address Register — holds the address being accessed",
            "Memory Data Register — holds the data just read or to be written",
            "Current Instruction Register — holds the instruction being decoded",
            "Zero, Negative, Carry, Overflow — set by ALU operations",
        ],
    }
    st.dataframe(pd.DataFrame(reg_data), hide_index=True, use_container_width=True)

    st.divider()
    st.markdown("#### The fetch-decode-execute cycle")
    st.markdown("""
Every instruction follows the same three-phase rhythm, repeated endlessly:

1. **Fetch** — copy the byte at `memory[PC]` into the CIR; increment PC
2. **Decode** — figure out which instruction that opcode means, and how many operand bytes follow
3. **Execute** — carry out the operation (ALU, memory access, jump…)

The execution trace in chapter 5 shows you exactly this cycle for each instruction.
""")


def _ch1_instruction_set():
    st.markdown("""
Our CPU understands 19 instructions. That's enough to write loops, call functions,
read from hardware ports, and push data onto the stack. Every program on this page
is assembled from exactly these opcodes.
""")

    # Full table in an expander so it doesn't dominate the page
    with st.expander("Full ISA reference table", expanded=True):
        isa_rows = []
        for opcode, (mnemonic, desc, operands) in INSTRUCTIONS.items():
            isa_rows.append({
                "Opcode": f"0x{opcode:02X}",
                "Mnemonic": mnemonic,
                "Size": 1 + len(operands),
                "Description": desc,
                "Example": ISA_EXAMPLES.get(mnemonic, mnemonic),
            })
        st.dataframe(pd.DataFrame(isa_rows), hide_index=True,
                     use_container_width=True, height=340)

    st.divider()
    st.markdown("#### Instructions by category")
    st.caption("Select a group to see just those instructions.")

    group = st.radio("Category", list(ISA_GROUPS.keys()), horizontal=True,
                     key="isa_group")
    mnemonics_in_group = ISA_GROUPS[group]

    group_rows = []
    for opcode, (mnemonic, desc, operands) in INSTRUCTIONS.items():
        if mnemonic in mnemonics_in_group:
            group_rows.append({
                "Opcode": f"0x{opcode:02X}",
                "Mnemonic": mnemonic,
                "Operands": len(operands),
                "Description": desc,
                "Example": ISA_EXAMPLES.get(mnemonic, ""),
            })
    if group_rows:
        st.dataframe(pd.DataFrame(group_rows), hide_index=True, use_container_width=True)

    # Brief notes per group
    notes = {
        "Memory & registers": (
            "LOAD reads a byte from a memory address into register A. "
            "STORE writes A back out to an address. "
            "These two instructions account for the majority of memory traffic in any program."
        ),
        "Arithmetic": (
            "All arithmetic happens through A. ADD and SUB update the accumulator "
            "and set the Zero (Z), Negative (N), and Carry (C) flags accordingly. "
            "The CPU has no MUL/DIV — those are built from shifts and adds."
        ),
        "Logic": (
            "AND, OR, XOR operate bitwise on every bit of A simultaneously. "
            "Classic uses: AND for masking (`A AND 0x0F` = low nibble), "
            "XOR for toggling, OR for setting specific bits."
        ),
        "Compare & branch": (
            "CMP subtracts its operand from A but discards the result — "
            "it only sets the flags. Then JZ or JNZ checks those flags to decide "
            "whether to redirect the Program Counter."
        ),
        "Stack": (
            "PUSH decrements SP then writes A to memory[SP]. "
            "POP reads from memory[SP] into A then increments SP. "
            "Last in, first out — always."
        ),
        "Subroutines": (
            "CALL pushes the return address (PC+2) onto the stack, then jumps. "
            "RET pops that address back into PC. "
            "This mechanism is how every function call in every language works at the hardware level."
        ),
        "I/O": (
            "IN reads a byte from a numbered hardware port into A. "
            "OUT writes A to a port. Port 0 = keyboard, port 6 = display in our emulator."
        ),
        "Control": (
            "HLT stops the clock. The CPU will do nothing further until reset. "
            "NOP burns one cycle without side effects — useful for timing padding."
        ),
    }
    if group in notes:
        st.info(notes[group])


def _ch2_reading_machine_code():
    st.markdown("""
Before writing assembly, it helps to be able to *read* raw machine code — the hex
bytes a CPU actually sees. Given a stream of bytes, can you work out what the
program does?
""")

    st.markdown("#### Hex → instructions decoder")
    st.caption(
        "Enter space-separated hex bytes. The decoder will split them into "
        "instructions based on each opcode's expected operand count."
    )

    hex_input = st.text_input(
        "Hex bytes",
        value="01 A0 03 05 02 A1 FF",
        help="Each opcode is one byte; operand bytes follow immediately.",
        key="dissect_hex",
    )

    if hex_input:
        try:
            raw_bytes = [int(b, 16) for b in hex_input.strip().split()]
            decoded = []
            i = 0
            while i < len(raw_bytes):
                opcode = raw_bytes[i]
                addr = 0x70 + i
                if opcode in INSTRUCTIONS:
                    mnemonic, desc, operands = INSTRUCTIONS[opcode]
                    ops = []
                    for _ in operands:
                        i += 1
                        ops.append(f"0x{raw_bytes[i]:02X}" if i < len(raw_bytes) else "??")
                    decoded.append({
                        "Address":     f"0x{addr:02X}",
                        "Bytes":       " ".join(f"{raw_bytes[addr - 0x70 + j]:02X}"
                                                for j in range(len(ops) + 1)),
                        "Instruction": f"{mnemonic} {' '.join(ops)}".strip(),
                        "Description": desc,
                    })
                else:
                    decoded.append({
                        "Address":     f"0x{addr:02X}",
                        "Bytes":       f"{opcode:02X}",
                        "Instruction": f"??? (0x{opcode:02X})",
                        "Description": "Unknown opcode",
                    })
                i += 1
            st.dataframe(pd.DataFrame(decoded), hide_index=True, use_container_width=True)
        except Exception as e:
            st.error(f"Parse error: {e}")

    st.divider()
    st.markdown("#### How to decode manually")
    st.markdown("""
The rule is straightforward:

1. Read the first byte — look up its opcode in the ISA table.
2. That opcode tells you how many operand bytes follow (0, 1, or 2).
3. Consume those bytes as the operand(s).
4. Advance to the next opcode and repeat.

Try decoding `01 A0 FF` by hand:
- `0x01` → `LOAD`, needs 1 operand byte → reads `0xA0` → **LOAD [0xA0]**
- `0xFF` → `HLT`, no operands → **HLT**

Two instructions. Program loads the value at address 0xA0 into A, then halts.
""")

    st.markdown("#### Quick challenge")
    st.info(
        "What does `03 0A 08 00 0B 71 FF` do?  \n"
        "Hint: look up opcodes 0x03, 0x08, 0x0B, 0xFF in the ISA table (chapter 2). "
        "Paste it into the decoder above to check."
    )


def _ch3_example_programs():
    st.markdown("""
The best way to learn assembly is to read real programs. Each example below
highlights a different concept — start with *Add two numbers* if this is your
first time, or jump to whichever concept interests you.
""")

    prog_name = st.selectbox(
        "Select a program",
        list(EXAMPLE_PROGRAMS.keys()),
        key="prog_sel",
    )
    prog = EXAMPLE_PROGRAMS[prog_name]

    # Concept badges
    badges = "  ".join(
        f'`{c}`' for c in prog["concepts"]
    )
    st.markdown(f"**Concepts covered:** {badges}")

    st.markdown(f"_{prog['walkthrough']}_")

    st.divider()

    col_src, col_bc = st.columns([3, 2])

    with col_src:
        st.markdown("##### Assembly source")
        st.code(prog["source"], language="asm")

    with col_bc:
        st.markdown("##### Assembled bytes")
        st.caption("Each source line becomes 1–3 bytes.")
        bc_df = _bytecode_table(prog["bytecode"])
        st.dataframe(bc_df[["Address", "Hex", "Assembly"]],
                     hide_index=True, use_container_width=True)

    st.divider()
    st.markdown("##### Binary representation of each byte")
    st.caption("The CPU sees only these bits — the mnemonic names are purely for us.")
    st.dataframe(
        _bytecode_table(prog["bytecode"])[["Address", "Binary", "Assembly"]],
        hide_index=True, use_container_width=True,
    )

    # Store selected program for chapter 4
    st.session_state["asm_selected_prog"] = prog_name


def _ch4_execution():
    st.markdown("""
Now let's actually run a program and watch the CPU work through it cycle by cycle.
Each instruction passes through **fetch → decode → execute**, and you can see
exactly what changes in registers and memory at each step.
""")

    # Let the user pick (defaulting to whatever they were looking at in ch3)
    default_prog = st.session_state.get("asm_selected_prog", "Add two numbers")
    default_idx = list(EXAMPLE_PROGRAMS.keys()).index(default_prog) \
        if default_prog in EXAMPLE_PROGRAMS else 0

    prog_name = st.selectbox(
        "Program to run",
        list(EXAMPLE_PROGRAMS.keys()),
        index=default_idx,
        key="run_prog_sel",
    )
    prog = EXAMPLE_PROGRAMS[prog_name]
    st.caption(prog["description"])
    st.code(prog["source"], language="asm")

    if st.button("▶ Run and trace", type="primary", key="run_btn"):
        cpu = CPU()
        prog["setup"](cpu)
        steps = cpu.run_program(prog["bytecode"])
        st.session_state["asm_cpu"]    = cpu
        st.session_state["asm_steps"]  = steps
        st.session_state["asm_prog"]   = prog_name

    if "asm_cpu" not in st.session_state:
        st.info("Select a program above and click **▶ Run and trace** to see the execution.")
        return

    cpu   = st.session_state["asm_cpu"]
    steps = st.session_state["asm_steps"]

    if st.session_state.get("asm_prog") != prog_name:
        st.info("Click **▶ Run and trace** to execute the selected program.")
        return

    st.divider()
    st.markdown(f"#### Execution trace: *{prog_name}*")

    m1, m2, m3 = st.columns(3)
    m1.metric("Clock cycles",   cpu.cycle)
    m2.metric("Instructions",   sum(1 for s in steps if s.phase == "execute"))
    m3.metric("Memory writes",  sum(len(s.mem_changed) for s in steps))

    st.divider()

    tab_trace, tab_regs = st.tabs(["Cycle-by-cycle log", "Final register state"])

    phase_colours = {
        "fetch":     "#cff4fc",
        "decode":    "#fff3cd",
        "execute":   "#d1e7dd",
        "writeback": "#e2d9f3",
        "interrupt": "#f8d7da",
        "dma":       "#fde8d8",
    }
    phase_labels = {
        "fetch":     "1 · FETCH",
        "decode":    "2 · DECODE",
        "execute":   "3 · EXECUTE",
        "writeback": "4 · WRITEBACK",
    }

    with tab_trace:
        st.caption(
            "Each row is one clock cycle. Expand to see register state and any memory writes."
        )
        for step in steps:
            colour = phase_colours.get(step.phase, "#f8f9fa")
            label  = phase_labels.get(step.phase, step.phase.upper())
            with st.expander(
                f"{label:16s}  |  cycle {step.cycle:3d}  —  {step.description}"
            ):
                st.markdown(
                    f'<div style="background:{colour};border-radius:6px;padding:10px;'
                    f'font-size:14px">{step.detail}</div>',
                    unsafe_allow_html=True,
                )
                if step.reg_snapshot:
                    r = step.reg_snapshot
                    st.code(
                        f"A=0x{r['A']:02X} ({r['A']:3d})  "
                        f"PC=0x{r['PC']:04X}  "
                        f"SP=0x{r['SP']:02X}  "
                        f"MAR=0x{r['MAR']:04X}  "
                        f"MDR=0x{r['MDR']:02X}  "
                        f"CIR={r['CIR']}",
                        language="text",
                    )
                for addr, val in step.mem_changed:
                    region = cpu.memory.region_for(addr)
                    rname  = region.name if region else "unknown"
                    char   = chr(val) if 32 <= val <= 126 else "?"
                    st.caption(
                        f"Memory write → [{rname}]  "
                        f"0x{addr:02X} ← 0x{val:02X}  ({val})  '{char}'"
                    )

    with tab_regs:
        r = steps[-1].reg_snapshot if steps else {}
        if r:
            st.caption("Final state of every register after the program halted.")
            rcols = st.columns(4)
            for col, (k, v) in zip(rcols * 4, r.items()):
                if isinstance(v, int):
                    col.metric(k, f"0x{v:02X}", delta=f"= {v}")


def _ch5_write_your_own():
    st.markdown("""
You've read assembly. You've watched it execute. Now write some yourself.

Enter hex opcodes below — use the ISA table (chapter 2) for reference.
The program is loaded at address `0x70`, and you can pre-set any memory
locations before it runs.
""")

    st.markdown("#### Starter ideas")
    col1, col2, col3 = st.columns(3)
    col1.info("**Add 3 numbers**  \nLoad A0, add A1, add A2, store to A3, HLT")
    col2.info("**Double a value**  \nLoad a number, ADD it to itself (ADD A), store, HLT")
    col3.info("**Simple loop**  \nLoad a counter, SUB 1, CMP 0, JNZ back, HLT")

    st.divider()

    custom_hex = st.text_area(
        "Hex program (space or newline separated)",
        value="01 A0\n03 A1\n02 A2\nFF",
        height=130,
        help="Loaded at 0x70. Each opcode on its own line is fine.",
        key="custom_hex",
    )
    mem_setup = st.text_input(
        "Pre-set memory  (addr=val, comma separated)",
        value="A0=10, A1=20",
        help="Hex addresses, decimal values. e.g. A0=42, B0=7",
        key="mem_setup",
    )

    col_run, col_dis = st.columns([1, 1])

    with col_run:
        run_clicked = st.button("▶ Run", type="primary", key="run_custom")

    with col_dis:
        dis_clicked = st.button("Decode bytes (no run)", key="dis_custom")

    # Disassemble without running
    if dis_clicked and custom_hex.strip():
        try:
            raw = [int(b, 16) for b in custom_hex.replace('\n', ' ').split() if b]
            decoded = []
            i = 0
            while i < len(raw):
                opcode = raw[i]
                addr   = 0x70 + i
                if opcode in INSTRUCTIONS:
                    mnemonic, desc, operands = INSTRUCTIONS[opcode]
                    ops = []
                    for _ in operands:
                        i += 1
                        ops.append(f"0x{raw[i]:02X}" if i < len(raw) else "??")
                    decoded.append({
                        "Address":     f"0x{addr:02X}",
                        "Instruction": f"{mnemonic} {' '.join(ops)}".strip(),
                        "Description": desc,
                    })
                else:
                    decoded.append({
                        "Address":     f"0x{addr:02X}",
                        "Instruction": f"??? (0x{opcode:02X})",
                        "Description": "Unknown opcode",
                    })
                i += 1
            st.dataframe(pd.DataFrame(decoded), hide_index=True, use_container_width=True)
        except Exception as e:
            st.error(f"Decode error: {e}")

    # Run
    if run_clicked:
        try:
            raw = [int(b, 16) for b in custom_hex.replace('\n', ' ').split() if b]
            if not raw:
                st.warning("No bytes entered.")
                return

            cpu2 = CPU()
            for pair in mem_setup.split(","):
                pair = pair.strip()
                if "=" in pair:
                    a, v = pair.split("=")
                    cpu2.memory.write(int(a.strip(), 16), int(v.strip()))

            steps2 = cpu2.run_program(raw)

            st.success(
                f"Completed — {len(raw)} bytes  ·  {cpu2.cycle} cycles  ·  "
                f"{sum(1 for s in steps2 if s.phase == 'execute')} instructions executed"
            )

            r = steps2[-1].reg_snapshot if steps2 else {}
            if r:
                rc1, rc2, rc3, rc4 = st.columns(4)
                rc1.metric("A",  f"0x{r['A']:02X}", delta=f"= {r['A']}")
                rc2.metric("PC", f"0x{r['PC']:04X}")
                rc3.metric("SP", f"0x{r['SP']:02X}")
                rc4.metric("Cycles", cpu2.cycle)

            writes = [(addr, val) for s in steps2 for addr, val in s.mem_changed]
            if writes:
                st.markdown("**Memory writes:**")
                for addr, val in writes:
                    char = chr(val) if 32 <= val <= 126 else "?"
                    st.caption(f"  0x{addr:02X} ← 0x{val:02X}  ({val})  '{char}'")

            # Compact cycle log
            with st.expander("Full execution trace"):
                phase_colours = {
                    "fetch": "#cff4fc", "decode": "#fff3cd",
                    "execute": "#d1e7dd", "writeback": "#e2d9f3",
                }
                for step in steps2:
                    colour = phase_colours.get(step.phase, "#f8f9fa")
                    with st.expander(
                        f"[{step.phase.upper():12s}] cycle {step.cycle} — {step.description}"
                    ):
                        st.markdown(
                            f'<div style="background:{colour};border-radius:6px;'
                            f'padding:8px">{step.detail}</div>',
                            unsafe_allow_html=True,
                        )
                        if step.reg_snapshot:
                            r2 = step.reg_snapshot
                            st.code(
                                f"A=0x{r2['A']:02X}  PC=0x{r2['PC']:04X}  "
                                f"SP=0x{r2['SP']:02X}  CIR={r2['CIR']}",
                                language="text",
                            )
        except Exception as e:
            st.error(f"Runtime error: {e}")

    st.divider()
    st.markdown("#### Quick ISA reminder")
    st.caption("Key opcodes — for the full table see chapter 2.")
    quick = [
        ("0x01", "LOAD [addr]",  "A ← memory[addr]"),
        ("0x02", "STORE [addr]", "memory[addr] ← A"),
        ("0x03", "ADD val",      "A ← A + val"),
        ("0x04", "SUB val",      "A ← A - val"),
        ("0x08", "CMP val",      "set flags; A - val (discard)"),
        ("0x0A", "JZ addr",      "jump if Zero flag set"),
        ("0x0B", "JNZ addr",     "jump if Zero flag clear"),
        ("0x0C", "PUSH",         "push A onto stack"),
        ("0x0D", "POP",          "pop stack → A"),
        ("0xFF", "HLT",          "halt"),
    ]
    st.dataframe(
        pd.DataFrame(quick, columns=["Opcode", "Mnemonic", "Effect"]),
        hide_index=True,
        use_container_width=True,
    )


# ── Chapter dispatch ──────────────────────────────────────────────────────────

CHAPTER_FNS = [
    _ch0_what_is_assembly,
    _ch1_instruction_set,
    _ch2_reading_machine_code,
    _ch3_example_programs,
    _ch4_execution,
    _ch5_write_your_own,
]


# ── Main render ───────────────────────────────────────────────────────────────

def render():
    st.title("Assembly Language")
    st.caption("The lowest level a human can read — one line, one instruction, one opcode.")

    if "asm_chapter" not in st.session_state:
        st.session_state["asm_chapter"] = 0

    ch = st.session_state["asm_chapter"]

    st.markdown(_nav_html(ch), unsafe_allow_html=True)
    st.progress(ch / (len(CHAPTERS) - 1))

    st.subheader(CHAPTERS[ch])
    st.divider()

    CHAPTER_FNS[ch]()

    st.divider()
    _prev_next(ch)

    with st.sidebar:
        st.markdown("### Assembly Language")
        for i, title in enumerate(CHAPTERS):
            icon = "✅" if i < ch else ("▶️" if i == ch else "○")
            if st.button(
                f"{icon} {title}",
                key=f"sidebar_asm_{i}",
                use_container_width=True,
                type="primary" if i == ch else "secondary",
            ):
                st.session_state["asm_chapter"] = i
                st.rerun()
