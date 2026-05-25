import streamlit as st
import sys, struct

from core.reference import (to_binary, to_hex, to_octal, bit_groups, alu_op,
                             decode_ascii, twos_complement, signed_str,
                             nibble_high, nibble_low, bcd_encode, ieee754_approx,
                             str_to_bytes_repr, int_to_bytes_repr
                             )


def render():
    st.title("Data & Encoding")
    st.caption("How does a computer represent *anything*? It all starts here.")

    level = st.session_state.get("level","Intermediate")

    tab1, tab2, tab3, tab4 = st.tabs([
        "Integers", "Floats (IEEE-754)", "Strings & Unicode", "Python Object Memory"
    ])

    # ── TAB 1: Integers ────────────────────────────────────────────────────
    with tab1:
        st.subheader("Integer Representation")
        st.markdown("""
        Computers store numbers in binary. But *how* exactly?
        Enter any integer and see its full internal representation.
        """)

        col_in, col_info = st.columns([1, 2])
        with col_in:
            n = st.number_input("Integer value", value=65, step=1,
                                min_value=-2**31, max_value=2**31-1, key="int_val")
            bits = st.select_slider("Display width (bits)", [8, 16, 32], value=8)

        r = int_to_bytes_repr(int(n))
        u = int(n) & ((1 << bits) - 1)

        with col_info:
            st.markdown(f"**Decimal (signed):** `{r['decimal_signed']}`")
            st.markdown(f"**Decimal (unsigned 32-bit):** `{r['decimal_unsigned']}`")
            st.markdown(f"**Hexadecimal:** `0x{to_hex(u, bits//4)}`")

        st.markdown("#### Binary breakdown")
        binary_str = to_binary(u, bits)

        # Colour-coded bit display
        groups = [binary_str[i:i+4] for i in range(0, bits, 4)]
        html_bits = ""
        colours = ["#3B8BD4", "#9B6DD4"]
        for gi, g in enumerate(groups):
            c = colours[gi % 2]
            for b in g:
                bg = "#1a3a5c" if b == "1" else "#f0f0f0"
                fc = "white" if b == "1" else "#888"
                html_bits += (
                    f'<span style="display:inline-block;width:22px;height:26px;'
                    f'line-height:26px;text-align:center;font-family:monospace;'
                    f'font-size:14px;font-weight:bold;background:{bg};color:{fc};'
                    f'margin:1px;border-radius:3px;">{b}</span>'
                )
        st.markdown(html_bits, unsafe_allow_html=True)

        # Byte layout
        if bits >= 16:
            st.markdown("#### Byte layout in memory")
            bcol1, bcol2 = st.columns(2)
            with bcol1:
                st.markdown("**Little-endian** (x86 / ARM — most common)")
                le_bytes = struct.pack(f"<{'i' if int(n)<0 else 'I'}", u)
                for i, byte in enumerate(le_bytes[:bits//8]):
                    st.code(f"Address +{i}: 0x{byte:02X}  ({byte:3d})  {byte:08b}")
            with bcol2:
                st.markdown("**Big-endian** (network byte order)")
                be_bytes = struct.pack(f">{'i' if int(n)<0 else 'I'}", u)
                for i, byte in enumerate(be_bytes[:bits//8]):
                    st.code(f"Address +{i}: 0x{byte:02X}  ({byte:3d})  {byte:08b}")

        if bits == 8 and 0 <= u <= 127:
            st.info(f"💡 ASCII character for {u}: **`{chr(u)}`** — this is how text characters are stored as numbers.")

        st.markdown("#### Two's complement (signed negative numbers)")
        with st.expander("How does -1 become 0xFF? Click to learn"):
            st.markdown("""
To store a negative number, computers use **two's complement**:
1. Start with the positive version in binary
2. **Flip all bits** (this is the one's complement)
3. **Add 1**

Example: `–1` in 8 bits:
- `+1` = `00000001`
- Flip bits → `11111110`
- Add 1 → `11111111` = `0xFF`

This is why `0xFF` = 255 unsigned, but = –1 signed.
The top bit acts as the **sign bit** (1 = negative).
            """)
            ex = st.slider("Show two's complement of:", -128, 127, -1, key="tc_demo")
            pos = abs(ex) & 0xFF
            flipped = (~ex) & 0xFF
            result = (-ex) & 0xFF
            st.code(f"Value:       {ex}\nPositive:    {to_binary(abs(ex),8)} = {abs(ex)}\nFlip bits:   {to_binary(flipped,8)}\nAdd 1:       {to_binary(result,8)} = 0x{result:02X}")

    # ── TAB 2: IEEE-754 Floats ─────────────────────────────────────────────
    with tab2:
        st.subheader("IEEE-754 Floating Point")
        st.markdown("""
        Floating point is how computers store decimals. It's similar to scientific notation: 
        **sign × mantissa × 2^exponent**. Understanding this explains quirks like `0.1 + 0.2 ≠ 0.3`.
        """)

        f_val = st.number_input("Float value", value=3.14, format="%.10f", key="float_val")
        r = ieee754_approx(float(f_val))

        # Visual bit layout (Updated to match reference.py's 'binary' key)
        sign_bits   = r["binary"][0]
        exp_bits    = r["binary"][1:9]
        mant_bits   = r["binary"][9:]

        st.markdown("#### 32-bit layout (single precision)")
        def coloured_field(bits, label, bg, fg="white"):
            html = f'<div style="display:inline-block;background:{bg};border-radius:4px;padding:3px 7px;margin:2px">'
            html += f'<div style="font-size:10px;color:{fg};opacity:0.8">{label}</div>'
            html += f'<div style="font-family:monospace;font-size:13px;color:{fg};letter-spacing:2px">{bits}</div></div>'
            return html

        html = (
            coloured_field(sign_bits,  "Sign (1 bit)",      "#E85D24") +
            coloured_field(exp_bits,   "Exponent (8 bits)", "#9B6DD4") +
            coloured_field(mant_bits,  "Mantissa (23 bits)","#3B8BD4")
        )
        st.markdown(html, unsafe_allow_html=True)
        
        # Calculate the actual decimal mantissa value 
        # (1 + fractional part) unless it's a subnormal number (exponent_raw == 0)
        mantissa_float = 1.0 + (r["mantissa"] / (1 << 23)) if r["exponent_raw"] != 0 else (r["mantissa"] / (1 << 23))

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Sign", "Negative (–)" if r["sign"] else "Positive (+)")
        with c2:
            st.metric("Exponent (biased)", r["exponent_raw"],
                      delta=f"actual: {r['exponent_val']} (bias 127)")
        with c3:
            st.metric("Mantissa value", f"{mantissa_float:.8f}")

        st.markdown(f"""
**Formula:** `(–1)^{r['sign']} × {mantissa_float:.8f} × 2^{r['exponent_val']} ≈ {float(f_val)}`

**Hex representation:** `0x{r['hex']}`
        """)

        with st.expander("🔍 Why does 0.1 + 0.2 ≠ 0.3?"):
            a, b = 0.1, 0.2
            ra, rb, rc = ieee754_approx(a), ieee754_approx(b), ieee754_approx(a+b)
            st.markdown(f"""
`0.1` cannot be represented exactly in binary (just like 1/3 can't in decimal).

| Value | Exact decimal stored | Hex |
|-------|---------------------|-----|
| `0.1` | `{a:.20f}` | `0x{ra['hex']}` |
| `0.2` | `{b:.20f}` | `0x{rb['hex']}` |
| `0.1 + 0.2` | `{a+b:.20f}` | `0x{rc['hex']}` |
| `0.3` | `{0.3:.20f}` | `0x{ieee754_approx(0.3)['hex']}` |

The rounding error accumulates at the 17th decimal place.
Use `decimal.Decimal` or `math.isclose()` for precise comparisons.
            """)

    # ── TAB 3: Strings ────────────────────────────────────────────────────
    with tab3:
        st.subheader("Strings & Unicode")
        st.markdown("Text is just numbers. Here's how.")

        scol1, scol2 = st.columns([1, 1])
        with scol1:
            s = st.text_input("String to inspect", value="Hello, 世界! 🌍", key="str_val")
            enc = st.selectbox("Encoding", ["utf-8", "utf-16", "ascii", "latin-1"], key="enc_val")

        try:
            r = str_to_bytes_repr(s, enc)
            with scol2:
                st.metric("Characters", r["length_chars"])
                st.metric("Bytes stored", r["length_bytes"],
                          delta=f"{'multi-byte!' if r['length_bytes'] > r['length_chars'] else 'same as char count'}")

            st.markdown("#### Byte-by-byte breakdown")
            cols = st.columns(min(len(s), 8))
            for i, (char, cp) in enumerate(zip(s, r["codepoints"])):
                if i < len(cols):
                    with cols[i]:
                        raw = char.encode(enc) if enc != "ascii" or cp < 128 else b"?"
                        hex_str = raw.hex().upper()
                        st.markdown(
                            f'<div style="text-align:center;background:var(--secondary-background-color);'
                            f'border-radius:6px;padding:6px">'
                            f'<div style="font-size:20px">{char}</div>'
                            f'<div style="font-size:11px;font-family:monospace">U+{cp:04X}</div>'
                            f'<div style="font-size:10px;color:#888">{hex_str}</div>'
                            f'</div>',
                            unsafe_allow_html=True
                        )

            st.markdown(f"**Full hex dump:** `{r['hex']}`")
            st.markdown(f"**Unicode code points:** `{' '.join(f'U+{cp:04X}' for cp in r['codepoints'])}`")

        except (UnicodeEncodeError, LookupError) as e:
            st.error(f"Encoding error: {e}")

        with st.expander("📖 ASCII vs UTF-8 vs UTF-16 — what's the difference?"):
            st.markdown("""
| Encoding | Range | Bytes/char | Notes |
|----------|-------|-----------|-------|
| ASCII | 0–127 | 1 | English only; 7-bit |
| Latin-1 | 0–255 | 1 | Western European |
| UTF-8 | All Unicode | 1–4 | ASCII-compatible; dominant on the web |
| UTF-16 | All Unicode | 2 or 4 | Used internally by Python, Windows, Java |
| UTF-32 | All Unicode | 4 | Fixed width; simple but wasteful |

UTF-8 is clever: the first byte tells you how many bytes follow.
- `0xxxxxxx` — 1 byte (ASCII range)
- `110xxxxx 10xxxxxx` — 2 bytes
- `1110xxxx 10xxxxxx 10xxxxxx` — 3 bytes (CJK characters)
- `11110xxx …` — 4 bytes (emoji, rare scripts)
            """)

    # ── TAB 4: Python Object Memory ───────────────────────────────────────
    with tab4:
        st.subheader("Python Object Memory — Real Addresses")
        st.markdown("""
        In CPython, every object lives at a real memory address. `id(x)` returns it.
        Here you can inspect *actual* Python objects and see where they live in your RAM.
        """)

        expr = st.text_input(
            "Python expression to inspect",
            value="[1, 2, 3]",
            key="py_obj",
            help="Any valid Python expression: a number, string, list, dict…"
        )

        try:
            obj = eval(expr, {"__builtins__": __builtins__})
            addr = id(obj)
            size = sys.getsizeof(obj)

            mc1, mc2, mc3, mc4 = st.columns(4)
            mc1.metric("Type", type(obj).__name__)
            mc2.metric("Memory address", f"0x{addr:016X}"[:18] + "…")
            mc3.metric("Object size", f"{size} bytes")
            mc4.metric("Reference count", sys.getrefcount(obj) - 1,
                       help="sys.getrefcount adds 1 for the call itself")

            st.markdown(f"**Full address:** `0x{addr:016X}`")
            st.markdown(f"**Size breakdown:**")

            type_name = type(obj).__name__
            if type_name == "int":
                st.info(f"""
Python `int` objects are variable-size! Small ints (-5 to 256) are **interned** (cached).
This int occupies `{size}` bytes: 28 bytes base overhead + digits.
Try: compare `id(1)` and `id(1)` — they'll be identical (same cached object).
                """)
            elif type_name == "str":
                st.info(f"""
Python strings are **immutable** and may be **interned** (shared).
This `str` of {len(obj)} chars occupies {size} bytes.
Internal encoding: {'Latin-1 (1 byte/char)' if all(ord(c) < 256 for c in obj) else 'UCS-2 or UCS-4'}.
                """)
            elif type_name == "list":
                elem_size = sum(sys.getsizeof(x) for x in obj)
                st.info(f"""
A Python `list` is an **array of pointers** (8 bytes each on 64-bit).
- List object itself: {size} bytes (header + pointer array)
- Elements (separate objects): ~{elem_size} bytes
- Total in memory: ~{size + elem_size} bytes
The list over-allocates slots to make `.append()` fast (amortised O(1)).
                """)

            if isinstance(obj, (list, dict, tuple)):
                st.markdown("#### Element addresses")
                items = list(obj.items()) if isinstance(obj, dict) else list(obj)
                for i, item in enumerate(items[:8]):
                    st.code(f"[{i}] type={type(item).__name__:8s}  id=0x{id(item):016X}  size={sys.getsizeof(item):4d}B  value={repr(item)[:40]}")

        except Exception as e:
            st.error(f"Could not evaluate: {e}")