"""Number Systems page: binary, hex, octal, ASCII, two's complement, IEEE-754."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import streamlit as st
from core.reference import (to_binary, to_hex, to_octal, bit_groups,
                             decode_ascii, twos_complement, signed_str,
                             nibble_high, nibble_low, bcd_encode, ieee754_approx)


def render():
    st.title("Number Systems")
    level = st.session_state.get("level", "Intermediate")

    if level == "Beginner":
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
            nc1,nc2 = st.columns(2)
            nc1.metric("High nibble (bits 7–4)", f"0x{hi:X} = {to_binary(hi,4)}")
            nc2.metric("Low nibble  (bits 3–0)", f"0x{lo:X} = {to_binary(lo,4)}")

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
