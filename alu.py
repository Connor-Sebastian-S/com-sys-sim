import streamlit as st
from utils.helpers import to_bin, to_hex, alu_op

def show():
    st.title("ALU & Logic")
    st.caption("Where the actual computing happens — arithmetic and logic, gate by gate.")

    tab1, tab2, tab3 = st.tabs(["ALU Operations", "Logic Gates", "8-bit Adder"])

    # ── TAB 1: ALU Operations ─────────────────────────────────────────────
    with tab1:
        st.subheader("ALU Operation Explorer")
        st.markdown("""
        The **Arithmetic Logic Unit** is the part of the CPU that does all computation.
        It takes two inputs (operands) and an operation selector, and produces a result + status flags.
        """)

        col1, col2, col3 = st.columns(3)
        with col1:
            a = st.number_input("Operand A", -2147483648, 4294967295, 60, key="alu_a")
        with col2:
            b = st.number_input("Operand B", -2147483648, 4294967295, 15, key="alu_b")
        with col3:
            op = st.selectbox("Operation", [
                "ADD", "SUB", "MUL", "AND", "OR", "XOR", "NOT", "SHL", "SHR"
            ], key="alu_op")

        r = alu_op(int(a), int(b), op)
        a32 = int(a) & 0xFFFFFFFF
        b32 = int(b) & 0xFFFFFFFF

        st.divider()
        mc1, mc2, mc3, mc4 = st.columns(4)
        mc1.metric("Result (decimal)", r["result"])
        mc2.metric("Result (32-bit)", r["result32"])
        mc3.metric("Hex", r["result_hex"])
        mc4.metric("Result binary", r["result_bin"][:16] + "…")

        # Flags
        st.markdown("#### Status Flags")
        fc1, fc2, fc3, fc4 = st.columns(4)
        def flag_md(label, val, desc):
            colour = "#68C46A" if val else "#888"
            return f'<div style="background:{colour};color:white;border-radius:6px;padding:6px 10px;text-align:center"><b>{label}</b><br><small>{desc}</small></div>'

        fc1.markdown(flag_md("Z — Zero",     r["zero_flag"],     "Result = 0"), unsafe_allow_html=True)
        fc2.markdown(flag_md("N — Negative", r["negative_flag"], "MSB = 1"),   unsafe_allow_html=True)
        fc3.markdown(flag_md("C — Carry",    r["overflow"] and op in ("ADD","SUB"), "Carry out"), unsafe_allow_html=True)
        fc4.markdown(flag_md("V — Overflow", r["overflow"],      "Signed overflow"), unsafe_allow_html=True)

        # Binary operation display
        st.markdown("#### Binary operation")
        if op not in ("NOT", "SHL", "SHR"):
            st.code(
                f"  {'A':>3}: {to_bin(a32,32)}\n"
                f"  {'B':>3}: {to_bin(b32,32)}\n"
                f"  {op:>3}: {'─'*32}\n"
                f"      : {r['result_bin']}\n"
                f"  hex: {r['result_hex']}",
                language="text"
            )
        elif op == "NOT":
            st.code(
                f"  A   : {to_bin(a32,32)}\n"
                f"  NOT : {'─'*32}\n"
                f"      : {r['result_bin']}\n"
                f"  hex : {r['result_hex']}",
                language="text"
            )
        else:
            shift = int(b) % 32
            st.code(
                f"  A    : {to_bin(a32,32)}\n"
                f"  {op} by {shift}: {'─'*32}\n"
                f"       : {r['result_bin']}\n"
                f"  hex  : {r['result_hex']}",
                language="text"
            )

        with st.expander("💡 When does the CPU use these operations?"):
            st.markdown("""
| Operation | When used |
|-----------|-----------|
| ADD | Arithmetic, array indexing, pointer arithmetic |
| SUB | Subtraction, also used for CMP (sets flags, discards result) |
| AND | Bit masking (`x & 0xFF` gets low byte), checking flags |
| OR  | Setting bits, combining flags |
| XOR | Toggling bits; `x XOR x = 0` (fast zero/compare trick) |
| NOT | One's complement; used in two's complement negation |
| SHL | Multiply by powers of 2 (`x << 3` = `x × 8`) |
| SHR | Divide by powers of 2; arithmetic vs logical variants |
| MUL | Multiplication — often multi-cycle, sometimes a shift+add |
            """)

    # ── TAB 2: Logic Gates ────────────────────────────────────────────────
    with tab2:
        st.subheader("Logic Gates")
        st.markdown("All digital circuits are built from these seven primitive gates.")

        gate_sel = st.selectbox("Select gate", ["AND", "OR", "NOT", "NAND", "NOR", "XOR", "XNOR"], key="gate_sel")

        gates = {
            "AND":  {"fn": lambda a,b: a&b,  "sym": "A AND B",  "desc": "Output is 1 only when BOTH inputs are 1."},
            "OR":   {"fn": lambda a,b: a|b,  "sym": "A OR B",   "desc": "Output is 1 when AT LEAST ONE input is 1."},
            "NOT":  {"fn": lambda a,b: 1-a,  "sym": "NOT A",    "desc": "Output is the opposite of the input (inverter)."},
            "NAND": {"fn": lambda a,b: 1-(a&b), "sym": "NOT(A AND B)", "desc": "NAND = NOT AND. Functionally complete — you can build any logic from NAND alone."},
            "NOR":  {"fn": lambda a,b: 1-(a|b), "sym": "NOT(A OR B)",  "desc": "NOR = NOT OR. Also functionally complete."},
            "XOR":  {"fn": lambda a,b: a^b,  "sym": "A XOR B",  "desc": "Output is 1 when inputs are DIFFERENT. Used in adders and parity checks."},
            "XNOR": {"fn": lambda a,b: 1-(a^b),"sym":"NOT(A XOR B)","desc":"Output is 1 when inputs are the SAME (equivalence)."},
        }

        g = gates[gate_sel]
        st.caption(g["desc"])
        st.markdown(f"**Expression:** `{g['sym']}`")

        # Truth table
        st.markdown("#### Truth table")
        rows = []
        inputs = [(0,0),(0,1),(1,0),(1,1)]
        for a_in, b_in in inputs:
            out = g["fn"](a_in, b_in)
            rows.append({
                "A": a_in,
                "B": b_in if gate_sel != "NOT" else "—",
                "Output": out,
                "": "Y" if out else "N"
            })
        import pandas as pd
        st.dataframe(pd.DataFrame(rows), use_container_width=False, hide_index=True)

        # Interactive
        st.markdown("#### Try it")
        gc1, gc2 = st.columns(2)
        with gc1:
            ia = st.radio("Input A", [0, 1], horizontal=True, key="gate_a")
        with gc2:
            ib = st.radio("Input B", [0, 1], horizontal=True, key="gate_b") if gate_sel != "NOT" else 0
        result = g["fn"](int(ia), int(ib))
        colour = "#68C46A" if result else "#E85D24"
        st.markdown(
            f'<div style="font-size:48px;text-align:center;color:{colour};font-weight:bold">'
            f'{"1 (HIGH)" if result else "0 (LOW)"}</div>',
            unsafe_allow_html=True
        )

    # ── TAB 3: 8-bit Ripple-Carry Adder ──────────────────────────────────
    with tab3:
        st.subheader("8-bit Ripple-Carry Adder")
        st.markdown("""
        This is how CPUs actually add numbers at the transistor level.
        Each **full adder** takes three inputs (A bit, B bit, carry-in) and produces a sum bit + carry-out.
        The carry ripples left through all 8 stages.
        """)

        ac1, ac2 = st.columns(2)
        with ac1:
            add_a = st.number_input("Number A (0–255)", 0, 255, 45, key="add_a")
        with ac2:
            add_b = st.number_input("Number B (0–255)", 0, 255, 78, key="add_b")

        a_val, b_val = int(add_a), int(add_b)
        result_val = a_val + b_val
        carry_out  = result_val > 255
        result8    = result_val & 0xFF

        a_bits = [int(b) for b in to_bin(a_val, 8)]
        b_bits = [int(b) for b in to_bin(b_val, 8)]
        r_bits = [int(b) for b in to_bin(result8, 8)]

        # Show full adder stages
        st.markdown("#### Bit-by-bit addition (right to left)")
        carries = [0] * 9
        sums    = [0] * 8
        for i in range(7, -1, -1):
            ai = a_bits[i]
            bi = b_bits[i]
            ci = carries[i+1]
            s  = ai ^ bi ^ ci
            co = (ai & bi) | (bi & ci) | (ai & ci)
            sums[i]   = s
            carries[i] = co

        header = "Stage |  A  |  B  | Cin | Sum | Cout"
        st.code(header + "\n" + "─"*len(header))
        for i in range(7, -1, -1):
            bit = 7 - i
            st.code(
                f"  {bit+1:2d}  |  {a_bits[i]}  |  {b_bits[i]}  |  {carries[i+1]}  |  {sums[i]}  |  {carries[i]}",
                language="text"
            )

        st.markdown("#### Result")
        rc1, rc2, rc3 = st.columns(3)
        rc1.metric(f"{a_val} + {b_val}", f"= {result_val}")
        rc2.metric("8-bit result", f"{result8} (0x{result8:02X})")
        rc3.metric("Carry out (overflow)", "YES — overflow!" if carry_out else "No")

        st.code(
            f"  A: {to_bin(a_val,8)} ({a_val})\n"
            f"  B: {to_bin(b_val,8)} ({b_val})\n"
            f"  +  {'─'*8}\n"
            f"{'C: 1' if carry_out else '  '}  {''.join(str(s) for s in sums)} ({result8})"
            + (" ← overflow!" if carry_out else ""),
            language="text"
        )