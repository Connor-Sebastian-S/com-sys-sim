import streamlit as st
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.reference import (to_binary, to_hex, to_octal, bit_groups, alu_op,
                             decode_ascii, twos_complement, signed_str,
                             nibble_high, nibble_low, bcd_encode, ieee754_approx)

def render():
    st.title("ALU & Logic")
    st.caption("Where the actual computing happens — arithmetic and logic, gate by gate.")

    level = st.session_state.get("level", "Intermediate")

    tab1, tab2, tab3, tab4 = st.tabs(["ALU Operations", "Logic Gates", "8-bit Adder", "Numbers"])

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
        mc1, mc2 = st.columns(2)
        mc3, mc4 = st.columns(2)
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
                f"  {'A':>3}: {to_binary(a32,32)}\n"
                f"  {'B':>3}: {to_binary(b32,32)}\n"
                f"  {op:>3}: {'─'*32}\n"
                f"      : {r['result_bin']}\n"
                f"  hex: {r['result_hex']}",
                language="text"
            )
        elif op == "NOT":
            st.code(
                f"  A   : {to_binary(a32,32)}\n"
                f"  NOT : {'─'*32}\n"
                f"      : {r['result_bin']}\n"
                f"  hex : {r['result_hex']}",
                language="text"
            )
        else:
            shift = int(b) % 32
            st.code(
                f"  A    : {to_binary(a32,32)}\n"
                f"  {op} by {shift}: {'─'*32}\n"
                f"       : {r['result_bin']}\n"
                f"  hex  : {r['result_hex']}",
                language="text"
            )

        with st.expander("When does the CPU use these operations?"):
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
                "": "✅" if out else "❌"
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

        a_bits = [int(b) for b in to_binary(a_val, 8)]
        b_bits = [int(b) for b in to_binary(b_val, 8)]
        r_bits = [int(b) for b in to_binary(result8, 8)]

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
            f"  A: {to_binary(a_val,8)} ({a_val})\n"
            f"  B: {to_binary(b_val,8)} ({b_val})\n"
            f"  +  {'─'*8}\n"
            f"{'C: 1' if carry_out else '  '}  {''.join(str(s) for s in sums)} ({result8})"
            + (" ← overflow!" if carry_out else ""),
            language="text"
        )

    with tab4:
        st.subheader("Number Systems")

        st.info("Computers store **everything** as numbers — letters, images, sounds — "
                "but they only understand the digits 0 and 1. "
                "This page shows you how the same number looks in different systems.")

        # ── Live converter ─────────────────────────────────────────────────────────
        st.markdown("## Universal Number Converter")
        input_col, fmt_col = st.columns([2,1])
        with fmt_col:
            input_format = st.radio("Input format", ["Decimal", "Hexadecimal", "Binary", "Character"])
        with input_col:
            raw = st.text_input("Enter a value", value="65",
                                help="Try: 65 (decimal), 0x41 (hex), 01000001 (binary), or 'A' (character)")

        try:
            if input_format == "Decimal":
                n = int(raw) & 0xFF
            elif input_format == "Hexadecimal":
                n = int(raw.replace("0x","").replace("0X",""), 16) & 0xFF
            elif input_format == "Binary":
                n = int(raw.replace(" ",""), 2) & 0xFF
            else:
                n = ord(raw[0]) & 0xFF if raw else 65
            valid = True
        except Exception:
            st.error("Could not parse that value. Try a number between 0–255.")
            valid = False
            n = 65

        if valid:
            st.divider()
            c1,c2 = st.columns(2)
            c3,c4 = st.columns(2)
            c1.metric("Decimal",     str(n))
            c2.metric("Hexadecimal", f"0x{n:02X}")
            c3.metric("Binary",      bit_groups(to_binary(n)))
            c4.metric("Octal",       f"0o{n:03o}")

            st.markdown("---")
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("### Bit breakdown (8-bit)")
                bits = to_binary(n)
                # Annotated bit table
                headers = ["Bit 7","Bit 6","Bit 5","Bit 4","Bit 3","Bit 2","Bit 1","Bit 0"]
                powers  = [128, 64, 32, 16, 8, 4, 2, 1]
                bit_vals= list(bits)
                contrib = [int(b)*p for b,p in zip(bit_vals, powers)]
                import pandas as pd
                df = pd.DataFrame({
                    "Bit position": headers,
                    "Place value":  [f"2^{7-i} = {p}" for i,p in enumerate(powers)],
                    "Bit":          bit_vals,
                    "Contribution": contrib,
                })
                st.dataframe(df, hide_index=True, use_container_width=True)
                st.markdown(f"**Sum:** {' + '.join(str(c) for c in contrib if c)} = **{n}**")

                st.markdown("### Nibbles")
                hi, lo = nibble_high(n), nibble_low(n)
                #nc1 = st.container()
            # nc2 = st.container()
                st.caption(f"High nibble (bits 7–4): 0x{hi:X} = {to_binary(hi, 4)}")
                st.caption(f"Low nibble  (bits 3–0): 0x{lo:X} = {to_binary(lo,4)}")

            with col_b:
                st.markdown("### Interpretations")
                signed = twos_complement(n)
                st.markdown(f"""
    | Interpretation | Value |
    |---|---|
    | Unsigned integer | {n} |
    | Signed (two's complement) | {signed} |
    | ASCII character | `{decode_ascii(n)}` |
    | BCD tens / units | {bcd_encode(n)[0]} / {bcd_encode(n)[1]} |
    | High nibble hex | 0x{nibble_high(n):X} |
    | Low nibble hex  | 0x{nibble_low(n):X} |
    """)
                if level in ("Intermediate","Advanced"):
                    st.markdown("### Two's complement explained")
                    if n >= 128:
                        step1 = to_binary(n)
                        step2 = ''.join('1' if b=='0' else '0' for b in step1)
                        step3 = int(step2,2)+1
                        st.code(f"Original:  {step1}  ({n})\n"
                                f"Invert:    {step2}\n"
                                f"Add 1:     {to_binary(step3)}  → signed = -{256-n}")
                    else:
                        st.caption(f"{n} is positive, so the signed value equals the unsigned value.")

        # ── Hex colour explorer ───────────────────────────────────────────────────
        st.divider()
        st.markdown("## Hex Colour Explorer")
        st.caption("RGB colours are just three bytes. Here's how it works:")
        hcol = st.columns(3)
        r = hcol[0].slider("Red (0–255)",   0, 255, 255)
        g = hcol[1].slider("Green (0–255)", 0, 255, 100)
        b = hcol[2].slider("Blue (0–255)",  0, 255, 50)
        hex_col = f"#{r:02X}{g:02X}{b:02X}"
        st.markdown(f"""
    <div style="background:{hex_col};width:100%;height:80px;border-radius:8px;
        display:flex;align-items:center;justify-content:center;
        color:{'#000' if r*0.299+g*0.587+b*0.114>128 else '#fff'};
        font-family:monospace;font-size:18px;font-weight:700">
    {hex_col}  —  R=0x{r:02X} G=0x{g:02X} B=0x{b:02X}  —  {r},{g},{b}
    </div>""", unsafe_allow_html=True)

        # ── IEEE-754 ──────────────────────────────────────────────────────────────
        if level in ("Intermediate","Advanced"):
            st.divider()
            st.markdown("## IEEE-754 Floating Point")
            st.caption("How does a computer store 3.14? It uses 32 bits split into three fields.")
            fval = st.number_input("Float value", value=3.14159, format="%.6f", step=0.1)
            ieee = ieee754_approx(float(fval))
            fc1,fc2,fc3 = st.columns(3)
            fc1.metric("Sign bit", ieee["sign"], delta="negative" if ieee["sign"] else "positive", delta_color="inverse")
            fc2.metric("Exponent (biased)", f"{ieee['exponent_raw']} → 2^{ieee['exponent_val']}")
            fc3.metric("Mantissa", f"0x{ieee['mantissa']:06X}")
            bits = ieee["binary"]
            sign_b   = bits[0]
            exp_b    = bits[1:9]
            mant_b   = bits[9:]
            st.markdown(f"""
    <div style="font-family:monospace;font-size:14px;background:#1e1e1e;color:#d4d4d4;
        padding:14px;border-radius:8px;letter-spacing:2px">
    <span style="color:#f48771">{sign_b}</span> <span style="color:#4ec9b0">{exp_b}</span> <span style="color:#dcdcaa">{mant_b}</span>
    <br><span style="color:#f48771">sign</span>  <span style="color:#4ec9b0">exponent(8)</span>               <span style="color:#dcdcaa">mantissa(23 bits)</span>
    </div>""", unsafe_allow_html=True)

        # ── ASCII table ───────────────────────────────────────────────────────────
        st.divider()
        st.markdown("## ASCII Table (32–127)")
        import pandas as pd
        rows = []
        for i in range(32, 128):
            rows.append({
                "Dec": i, "Hex": f"0x{i:02X}", "Bin": to_binary(i),
                "Char": decode_ascii(i),
                "Category": ("Printable" if 32<=i<=126 else "Control"),
            })
        df = pd.DataFrame(rows)
        st.dataframe(df, hide_index=True, height=300, use_container_width=True)

        # ── Quiz ──────────────────────────────────────────────────────────────────
        st.divider()
        st.markdown("## Quick Quiz")
        import random
        if "quiz_n" not in st.session_state:
            st.session_state["quiz_n"] = random.randint(0, 255)
        qn = st.session_state["quiz_n"]
        quiz_type = random.choice(["binary","hex","decimal"]) if "quiz_type" not in st.session_state else st.session_state["quiz_type"]
        st.session_state["quiz_type"] = quiz_type

        prompts = {
            "binary":  (f"What is **{bit_groups(to_binary(qn))}** (binary) in decimal?", str(qn)),
            "hex":     (f"What is **0x{qn:02X}** in decimal?", str(qn)),
            "decimal": (f"What is **{qn}** (decimal) in hexadecimal?", f"0x{qn:02X}".upper()),
        }
        prompt, answer = prompts[quiz_type]
        st.markdown(prompt)
        ans = st.text_input("Your answer", key="quiz_ans")
        qc1,qc2 = st.columns([1,4])
        with qc1:
            if st.button("Check"):
                if ans.strip().upper() == answer.upper():
                    st.success(f"Correct! {answer}")
                else:
                    st.error(f"Fucking idiot. Answer: {answer}")
        with qc2:
            if st.button("New question"):
                st.session_state["quiz_n"] = random.randint(0, 255)
                del st.session_state["quiz_type"]
                if "quiz_ans" in st.session_state:
                    del st.session_state["quiz_ans"]
                st.rerun()
