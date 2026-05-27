import streamlit as st
import sys, os
import random
import pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.reference import (to_binary, to_hex, to_octal, bit_groups, alu_op,
                             decode_ascii, twos_complement, signed_str,
                             nibble_high, nibble_low, bcd_encode, ieee754_approx)

# ── Helpers ───────────────────────────────────────────────────────────────────

CHAPTERS = [
    "What is the ALU?",
    "Try an ALU operation",
    "Logic gates",
    "From gates to an adder",
    "The 8-bit ripple-carry adder",
    "Number systems",
]

def _nav_html(current: int) -> str:
    """Render a small dot progress bar."""
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
        f'<div style="text-align:center;font-size:12px;color:#888;margin-bottom:1.5rem">'
        f'Chapter {current+1} of {len(CHAPTERS)} — {CHAPTERS[current]}</div>'
    )


def _flag_html(label: str, active: bool, desc: str) -> str:
    colour = "#1D9E75" if active else "#888"
    bg     = "#E1F5EE" if active else "#f5f5f5"
    return (
        f'<div style="background:{bg};border:1px solid {colour};border-radius:8px;'
        f'padding:8px 10px;text-align:center;flex:1;min-width:60px">'
        f'<b style="color:{colour}">{label}</b>'
        f'<div style="font-size:11px;color:#666;margin-top:2px">{desc}</div></div>'
    )


def _bit_html(bit: str, style: str = "neutral") -> str:
    colours = {
        "on":     ("background:#1D9E75;color:#E1F5EE;border-color:#0F6E56", "1"),
        "off":    ("background:#f0f0f0;color:#888;border-color:#ccc",        "0"),
        "carry":  ("background:#BA7517;color:#FAEEDA;border-color:#854F0B",  bit),
        "result": ("background:#185FA5;color:#E6F1FB;border-color:#0C447C",  bit),
        "neutral":("background:#f0f0f0;color:#333;border-color:#ccc",        bit),
    }
    css, label = colours.get(style, colours["neutral"])
    return (
        f'<span style="display:inline-flex;align-items:center;justify-content:center;'
        f'width:28px;height:28px;border-radius:5px;border:1px solid;'
        f'font-family:monospace;font-size:13px;font-weight:600;margin:2px;{css}">'
        f'{label}</span>'
    )


def _bits_html(value: int, bits: int = 8, style: str = "on") -> str:
    b = to_binary(value, bits)
    return "".join(_bit_html(c, "on" if c == "1" else "off") for c in b)


def _prev_next(ch: int):
    """Render Back / Continue buttons."""
    cols = st.columns([1, 4, 1])
    with cols[0]:
        if ch > 0 and st.button("← Back", key=f"back_{ch}"):
            st.session_state["alu_chapter"] = ch - 1
            st.rerun()
    with cols[2]:
        label = "Continue →" if ch < len(CHAPTERS) - 1 else "Finish ✓"
        if st.button(label, key=f"next_{ch}", type="primary"):
            if ch < len(CHAPTERS) - 1:
                st.session_state["alu_chapter"] = ch + 1
                st.rerun()


# ── Chapter renderers ─────────────────────────────────────────────────────────

def _ch0_what_is_alu():
    st.markdown("""
Every time your computer adds two numbers, checks if a condition is true, or shifts
bits around — that work is done by the **Arithmetic Logic Unit**. It's a dedicated
piece of hardware inside the CPU, and it has one job: take inputs, apply an operation,
produce an output.
""")

    st.info(
        "💡 **The ALU is the calculator inside the calculator.** "
        "Everything else in the CPU — fetching instructions, managing memory, "
        "keeping track of where you are in a program — exists to feed the right "
        "numbers into the ALU at the right time."
    )

    st.markdown("An ALU takes three things as input:")
    c1, c2, c3 = st.columns(3)
    c1.metric("Input A", "Operand A", help="The first number, e.g. 0b00111100")
    c2.metric("Input B", "Operand B", help="The second number, e.g. 0b00001111")
    c3.metric("Control", "Op-code",   help="Which operation: ADD, AND, XOR …")

    st.markdown("And it produces two outputs:")
    d1, d2 = st.columns(2)
    d1.metric("Result", "The computed value")
    d2.metric("Status flags", "Z  N  C  V", help="Zero, Negative, Carry, Overflow")

    st.divider()

    st.markdown("#### ALU block diagram")
    st.markdown("""
```
           ┌─────────────┐
 Operand A ─►             │
           │     ALU      ├──► Result
 Operand B ─►             │
           │              ├──► Flags (Z N C V)
  Op-code ──►             │
           └─────────────┘
```
""")


def _ch1_try_alu():
    st.markdown("""
Let's put the ALU to work. Choose an operation and two operands — the result and
status flags update instantly.
""")

    col1, col2, col3 = st.columns(3)
    with col1:
        a = st.number_input("Operand A (0–255)", 0, 255, 60, key="alu_a2")
    with col2:
        b = st.number_input("Operand B (0–255)", 0, 255, 15, key="alu_b2")
    with col3:
        op = st.selectbox("Operation", ["ADD","SUB","AND","OR","XOR","NOT","SHL","SHR"],
                          key="alu_op2")

    r   = alu_op(int(a), int(b), op)
    a32 = int(a) & 0xFF
    b32 = int(b) & 0xFF

    st.divider()

    mc1, mc2, mc3 = st.columns(3)
    mc1.metric("Result (decimal)", r["result32"])
    mc2.metric("Hex", r["result_hex"])
    mc3.metric("Binary", to_binary(r["result32"] & 0xFF))

    # Bit visualisation
    st.markdown("#### Bit view")
    a_bits = "".join(_bit_html(c, "on" if c=="1" else "off") for c in to_binary(a32))
    b_bits = "".join(_bit_html(c, "on" if c=="1" else "off") for c in to_binary(b32))
    r_bits = "".join(_bit_html(c, "result") for c in to_binary(r["result32"] & 0xFF))

    st.markdown(f"**A &nbsp;&nbsp;** {a_bits}", unsafe_allow_html=True)
    if op not in ("NOT",):
        st.markdown(f"**B &nbsp;&nbsp;** {b_bits}", unsafe_allow_html=True)
    st.markdown(f"**{op}** {r_bits}", unsafe_allow_html=True)

    # Flags
    st.markdown("#### Status flags")
    flags_html = '<div style="display:flex;gap:8px;flex-wrap:wrap">'
    flags_html += _flag_html("Z — Zero",     r["zero_flag"],     "result = 0")
    flags_html += _flag_html("N — Negative", r["negative_flag"], "MSB = 1")
    flags_html += _flag_html("C — Carry",    r["overflow"] and op in ("ADD","SUB"), "carry out")
    flags_html += _flag_html("V — Overflow", r["overflow"],      "signed overflow")
    flags_html += "</div>"
    st.markdown(flags_html, unsafe_allow_html=True)

    # Contextual explanation
    st.divider()
    explanations = {
        "ADD": f"Adding {int(a)} + {int(b)} = {int(a)+int(b)}. "
               f"{'That overflows 8 bits — result wraps to ' + str((int(a)+int(b))&0xFF) + '.' if int(a)+int(b) > 255 else 'Fits in 8 bits fine.'}",
        "SUB": f"Subtracting {int(b)} from {int(a)}. "
               "Internally, the CPU negates B using two's complement then adds.",
        "AND": f"AND keeps only the bits that are 1 in **both** A and B. "
               "Useful for masking: `value AND 0x0F` extracts the low nibble.",
        "OR":  "OR sets a bit wherever **either** A or B has a 1. "
               "Used for combining flags or setting specific bits.",
        "XOR": f"XOR is 1 where inputs **differ**. Trick: {int(a)} XOR {int(a)} = 0 — "
               "anything XORed with itself is zero. Used in checksums and crypto.",
        "NOT": f"NOT flips every bit. {to_binary(a32)} → {to_binary((~a32)&0xFF)}.",
        "SHL": f"Left-shifting by {int(b)%8} is the same as multiplying by {2**(int(b)%8)}.",
        "SHR": f"Right-shifting by {int(b)%8} is the same as integer-dividing by {2**(int(b)%8)}.",
    }
    st.info(explanations.get(op, ""))

    with st.expander("When does the CPU use each operation?"):
        st.markdown("""
| Operation | When used |
|-----------|-----------|
| ADD | Arithmetic, array indexing, pointer arithmetic |
| SUB | Subtraction; also used for CMP (sets flags, discards result) |
| AND | Bit masking, checking flags |
| OR  | Setting bits, combining flags |
| XOR | Toggling bits; fast zero / compare trick |
| NOT | One's complement; part of two's complement negation |
| SHL | Multiply by powers of 2 |
| SHR | Divide by powers of 2; arithmetic vs logical variants |
""")


def _ch2_logic_gates():
    st.markdown("""
Every operation the ALU performs is built from just **seven primitive gates**. A gate
is a tiny circuit that takes one or two binary inputs and produces one binary output,
following a fixed rule. Let's explore them all.
""")

    gate_sel = st.selectbox(
        "Select a gate",
        ["AND", "OR", "NOT", "NAND", "NOR", "XOR", "XNOR"],
        key="gate_sel2"
    )

    gates = {
        "AND":  {"fn": lambda a,b: a&b,      "sym": "A AND B",         "unary": False,
                 "desc": "Output is **1** only when **both** inputs are 1. Core of multiplication circuits."},
        "OR":   {"fn": lambda a,b: a|b,      "sym": "A OR B",          "unary": False,
                 "desc": "Output is **1** when **at least one** input is 1. Used to combine flags."},
        "NOT":  {"fn": lambda a,b: 1-a,      "sym": "NOT A",           "unary": True,
                 "desc": "Output is the **opposite** of the single input. Also called an inverter."},
        "NAND": {"fn": lambda a,b: 1-(a&b),  "sym": "NOT (A AND B)",   "unary": False,
                 "desc": "NAND = NOT AND. **Functionally complete** — you can build any logic circuit from NAND gates alone."},
        "NOR":  {"fn": lambda a,b: 1-(a|b),  "sym": "NOT (A OR B)",    "unary": False,
                 "desc": "NOR = NOT OR. Also **functionally complete**."},
        "XOR":  {"fn": lambda a,b: a^b,      "sym": "A XOR B",         "unary": False,
                 "desc": "Output is **1** when inputs are **different**. The key building block of adder circuits and parity checks."},
        "XNOR": {"fn": lambda a,b: 1-(a^b),  "sym": "NOT (A XOR B)",   "unary": False,
                 "desc": "Output is **1** when inputs are the **same** (logical equivalence)."},
    }

    g = gates[gate_sel]
    st.info(g["desc"])
    st.markdown(f"**Expression:** `{g['sym']}`")

    col_tt, col_try = st.columns([1, 1])

    with col_tt:
        st.markdown("##### Truth table")
        rows = []
        inputs = [(0, 0), (0, 1), (1, 0), (1, 1)] if not g["unary"] else [(0, 0), (1, 0)]
        for a_in, b_in in inputs:
            out = g["fn"](a_in, b_in)
            row = {"A": a_in, "Output": out}
            if not g["unary"]:
                row = {"A": a_in, "B": b_in, "Output": out}
            rows.append(row)
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

    with col_try:
        st.markdown("##### Try it live")
        ia = st.radio("Input A", [0, 1], horizontal=True, key="gate_a2")
        ib = 0
        if not g["unary"]:
            ib = st.radio("Input B", [0, 1], horizontal=True, key="gate_b2")
        result = g["fn"](int(ia), int(ib))
        colour = "#1D9E75" if result else "#E24B4A"
        st.markdown(
            f'<div style="font-size:48px;text-align:center;color:{colour};'
            f'font-weight:600;font-family:monospace;padding:16px 0">'
            f'{"1" if result else "0"}</div>'
            f'<div style="text-align:center;font-size:13px;color:#888">{"HIGH" if result else "LOW"}</div>',
            unsafe_allow_html=True
        )

    st.divider()
    st.markdown("""
> **Key insight:** NAND and NOR are *functionally complete* — meaning every other gate
> (AND, OR, XOR, NOT…) can be built from NAND gates alone. Real CPUs are often
> implemented almost entirely in NAND logic for this reason.
""")


def _ch3_full_adder():
    st.markdown("""
Now we can see how gates combine into something useful. A **full adder** is a circuit
that adds three single bits (A, B, and a carry-in) and produces a sum bit and a
carry-out bit.
""")

    st.info(
        "**Key insight:** Addition in binary is just XOR and AND gates wired together.\n\n"
        "- **Sum** = A XOR B XOR Cin\n"
        "- **Carry-out** = (A AND B) OR (B AND Cin) OR (A AND Cin)"
    )

    st.markdown("##### Try the full adder — set the three inputs")

    col1, col2, col3 = st.columns(3)
    fa_a   = col1.radio("Input A",   [0, 1], horizontal=True, key="fa_a")
    fa_b   = col2.radio("Input B",   [0, 1], horizontal=True, key="fa_b")
    fa_cin = col3.radio("Carry-in",  [0, 1], horizontal=True, key="fa_cin")

    fa_sum  = fa_a ^ fa_b ^ fa_cin
    fa_cout = (fa_a & fa_b) | (fa_b & fa_cin) | (fa_a & fa_cin)

    r1, r2 = st.columns(2)
    r1.metric("Sum bit",      fa_sum,  help="A XOR B XOR Cin")
    r2.metric("Carry-out bit", fa_cout, help="(A AND B) OR (B AND Cin) OR (A AND Cin)")

    st.divider()
    st.markdown("##### Full adder truth table")
    rows = []
    for a in [0,1]:
        for b in [0,1]:
            for cin in [0,1]:
                rows.append({
                    "A": a, "B": b, "Cin": cin,
                    "Sum": a^b^cin,
                    "Cout": (a&b)|(b&cin)|(a&cin),
                })
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

    st.divider()
    st.markdown("""
Chain **8** of these full adders together — where each one's carry-out feeds the next
one's carry-in — and you can add any two 8-bit numbers. That's the **ripple-carry adder**,
coming up next.
""")


def _ch4_adder():
    st.markdown("""
Take 8 full adders, wire them in a chain so the carry-out of each feeds into the
carry-in of the next, and you can add any two 8-bit numbers. The carry *ripples* from
right (bit 0) to left (bit 7) — hence the name.
""")

    ac1, ac2 = st.columns(2)
    with ac1:
        add_a = st.number_input("Number A (0–255)", 0, 255, 45, key="add_a2")
    with ac2:
        add_b = st.number_input("Number B (0–255)", 0, 255, 78, key="add_b2")

    a_val, b_val = int(add_a), int(add_b)
    result_val   = a_val + b_val
    carry_out    = result_val > 255
    result8      = result_val & 0xFF

    a_bits  = [int(c) for c in to_binary(a_val, 8)]
    b_bits  = [int(c) for c in to_binary(b_val, 8)]
    carries = [0] * 9
    sums    = [0] * 8
    for i in range(7, -1, -1):
        ai = a_bits[i]; bi = b_bits[i]; ci = carries[i+1]
        sums[i]    = ai ^ bi ^ ci
        carries[i] = (ai & bi) | (bi & ci) | (ai & ci)

    st.divider()
    st.markdown("#### Bit-by-bit view")

    # Header row
    hdr = '<div style="display:flex;gap:4px;align-items:center;margin-bottom:4px">'
    hdr += '<span style="width:56px;font-size:11px;color:#888;text-align:right;padding-right:8px">bit →</span>'
    hdr += "".join(
        f'<span style="width:28px;text-align:center;font-size:10px;color:#888">{7-i}</span>'
        for i in range(8)
    )
    hdr += "</div>"
    st.markdown(hdr, unsafe_allow_html=True)

    def _row(label, values, style):
        html = f'<div style="display:flex;gap:4px;align-items:center;margin:2px 0">'
        html += f'<span style="width:56px;font-size:12px;color:#666;text-align:right;padding-right:8px">{label}</span>'
        for v in values:
            html += _bit_html(str(v), style if v else "off")
        html += "</div>"
        return html

    st.markdown(_row("A", a_bits, "on"),      unsafe_allow_html=True)
    st.markdown(_row("B", b_bits, "on"),      unsafe_allow_html=True)
    st.markdown(_row("Cin", carries[1:], "carry"), unsafe_allow_html=True)
    st.markdown(
        '<div style="border-top:1px solid #ddd;margin:6px 0 6px 64px;width:240px"></div>',
        unsafe_allow_html=True
    )
    st.markdown(_row("Sum", sums, "result"), unsafe_allow_html=True)

    if carry_out:
        st.markdown(
            '<div style="margin-top:4px;font-size:13px;color:#BA7517;'
            'font-family:monospace;padding-left:64px">Carry out: 1 ← overflow!</div>',
            unsafe_allow_html=True
        )

    st.divider()
    rc1, rc2, rc3 = st.columns(3)
    rc1.metric(f"{a_val} + {b_val}", f"= {result_val}")
    rc2.metric("8-bit result", f"{result8}  (0x{result8:02X})")
    rc3.metric("Carry out (overflow)", "YES — overflow!" if carry_out else "No")

    if carry_out:
        st.error(
            f"**Overflow!** {a_val} + {b_val} = {result_val}, but 8 bits can only hold "
            f"0–255. The result wraps to **{result8}**. The CPU sets the **Carry flag** to signal this."
        )
    else:
        st.success(
            f"{a_val} + {b_val} = {result8}. "
            "Watch how the carry ripples right-to-left through each stage in the Cin row above."
        )


def _ch5_numbers():
    level = st.session_state.get("level", "Intermediate")

    st.markdown("""
The ALU works in binary, but we use decimal. Computers also use hexadecimal as a
compact shorthand — two hex digits represent exactly one byte. Let's see how the
same value looks in every system and what the individual bits mean.
""")

    input_col, fmt_col = st.columns([2, 1])
    with fmt_col:
        input_format = st.radio("Input format",
                                ["Decimal", "Hexadecimal", "Binary", "Character"],
                                key="conv_fmt")
    with input_col:
        raw = st.text_input("Enter a value", value="65",
                            help="Try: 65 (decimal), 0x41 (hex), 01000001 (binary), or A (character)")

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
        st.error("Could not parse that value.")
        valid = False
        n = 65

    if not valid:
        return

    st.divider()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Decimal",     str(n))
    c2.metric("Hexadecimal", f"0x{n:02X}")
    c3.metric("Binary",      bit_groups(to_binary(n)))
    c4.metric("Octal",       f"0o{n:03o}")

    st.markdown("---")
    st.markdown("#### Bit breakdown")
    st.caption("Each bit is a power of 2. Click a value to understand its contribution.")

    powers  = [128, 64, 32, 16, 8, 4, 2, 1]
    headers = [f"Bit {7-i}" for i in range(8)]
    bits    = list(to_binary(n))
    contrib = [int(b)*p for b, p in zip(bits, powers)]

    df = pd.DataFrame({
        "Bit position": headers,
        "Place value":  [f"2^{7-i} = {p}" for i, p in enumerate(powers)],
        "Bit":          bits,
        "Contribution": contrib,
    })
    st.dataframe(df, hide_index=True, use_container_width=True)
    st.markdown(
        "**Sum:** " +
        " + ".join(str(c) for c in contrib if c) +
        f" = **{n}**"
    )

    st.markdown("---")
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("#### Nibbles")
        hi, lo = nibble_high(n), nibble_low(n)
        st.caption(f"High nibble (bits 7–4): 0x{hi:X}  =  {to_binary(hi, 4)}")
        st.caption(f"Low  nibble (bits 3–0): 0x{lo:X}  =  {to_binary(lo, 4)}")

    with col_b:
        st.markdown("#### Interpretations")
        signed = twos_complement(n)
        st.markdown(f"""
| Interpretation | Value |
|---|---|
| Unsigned integer | {n} |
| Signed (two's complement) | {signed} |
| ASCII character | `{decode_ascii(n)}` |
| High nibble | 0x{nibble_high(n):X} |
| Low nibble  | 0x{nibble_low(n):X} |
""")

    if level in ("Intermediate", "Advanced") and n >= 128:
        with st.expander("Two's complement — step by step"):
            step1 = to_binary(n)
            step2 = ''.join('1' if b=='0' else '0' for b in step1)
            step3 = int(step2, 2) + 1
            st.code(
                f"Original:  {step1}  ({n})\n"
                f"Invert:    {step2}\n"
                f"Add 1:     {to_binary(step3)}  → signed = -{256-n}",
                language="text"
            )

    st.divider()
    st.markdown("#### Hex colour explorer")
    st.caption("RGB colours are just three bytes packed together.")
    hcol = st.columns(3)
    r = hcol[0].slider("Red",   0, 255, 255)
    g = hcol[1].slider("Green", 0, 255, 100)
    b = hcol[2].slider("Blue",  0, 255, 50)
    hex_col = f"#{r:02X}{g:02X}{b:02X}"
    text_col = '#000' if r*0.299 + g*0.587 + b*0.114 > 128 else '#fff'
    st.markdown(
        f'<div style="background:{hex_col};width:100%;height:72px;border-radius:8px;'
        f'display:flex;align-items:center;justify-content:center;'
        f'color:{text_col};font-family:monospace;font-size:16px;font-weight:700">'
        f'{hex_col} — R=0x{r:02X} G=0x{g:02X} B=0x{b:02X}</div>',
        unsafe_allow_html=True
    )

    if level in ("Intermediate", "Advanced"):
        st.divider()
        st.markdown("#### IEEE-754 floating point")
        st.caption("How does a CPU store 3.14? It uses 32 bits split into three fields.")
        fval = st.number_input("Float value", value=3.14159, format="%.6f", step=0.1, key="ieee_val")
        ieee = ieee754_approx(float(fval))
        fc1, fc2, fc3 = st.columns(3)
        fc1.metric("Sign bit", ieee["sign"],
                   delta="negative" if ieee["sign"] else "positive",
                   delta_color="inverse")
        fc2.metric("Exponent (biased)", f"{ieee['exponent_raw']} → 2^{ieee['exponent_val']}")
        fc3.metric("Mantissa", f"0x{ieee['mantissa']:06X}")
        bits  = ieee["binary"]
        sign_b, exp_b, mant_b = bits[0], bits[1:9], bits[9:]
        st.markdown(
            f'<div style="font-family:monospace;font-size:14px;background:#1e1e1e;'
            f'color:#d4d4d4;padding:14px;border-radius:8px;letter-spacing:2px">'
            f'<span style="color:#f48771">{sign_b}</span> '
            f'<span style="color:#4ec9b0">{exp_b}</span> '
            f'<span style="color:#dcdcaa">{mant_b}</span><br>'
            f'<span style="color:#f48771">sign</span>  '
            f'<span style="color:#4ec9b0">exponent (8 bits)</span> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
            f'<span style="color:#dcdcaa">mantissa (23 bits)</span></div>',
            unsafe_allow_html=True
        )


# ── Main render ───────────────────────────────────────────────────────────────

CHAPTER_FNS = [
    _ch0_what_is_alu,
    _ch1_try_alu,
    _ch2_logic_gates,
    _ch3_full_adder,
    _ch4_adder,
    _ch5_numbers,
]


def render():
    st.title("ALU & Logic")
    st.caption("Where the actual computing happens — arithmetic and logic, gate by gate.")

    if "alu_chapter" not in st.session_state:
        st.session_state["alu_chapter"] = 0

    ch = st.session_state["alu_chapter"]

    # Progress bar + chapter label
    st.markdown(_nav_html(ch), unsafe_allow_html=True)
    st.progress((ch) / (len(CHAPTERS) - 1))

    st.subheader(CHAPTERS[ch])
    st.divider()

    # Render current chapter
    CHAPTER_FNS[ch]()

    # Navigation
    st.divider()
    _prev_next(ch)

    # Optional: jump-to chapter selector in sidebar
    with st.sidebar:
        st.markdown("### ALU & Logic")
        for i, title in enumerate(CHAPTERS):
            icon = "✅" if i < ch else ("▶️" if i == ch else "○")
            if st.button(f"{icon} {title}", key=f"sidebar_ch_{i}",
                         use_container_width=True,
                         type="primary" if i == ch else "secondary"):
                st.session_state["alu_chapter"] = i
                st.rerun()