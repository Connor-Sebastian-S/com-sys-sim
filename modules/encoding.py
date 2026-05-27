"""Data & Encoding — guided chapter-by-chapter page."""
import streamlit as st
import sys, struct, random
import pandas as pd

from core.reference import (to_binary, to_hex, to_octal, bit_groups, alu_op,
                             decode_ascii, twos_complement, signed_str,
                             nibble_high, nibble_low, bcd_encode, ieee754_approx,
                             str_to_bytes_repr, int_to_bytes_repr)


# ── Navigation helpers ────────────────────────────────────────────────────────

CHAPTERS = [
    "Everything is bits",
    "Integers",
    "Floating point (IEEE-754)",
    "Text & Unicode",
    "Python object memory",
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
        if ch > 0 and st.button("← Back", key=f"enc_back_{ch}"):
            st.session_state["enc_chapter"] = ch - 1
            st.rerun()
    with cols[2]:
        label = "Continue →" if ch < len(CHAPTERS) - 1 else "Finish ✓"
        if st.button(label, key=f"enc_next_{ch}", type="primary"):
            if ch < len(CHAPTERS) - 1:
                st.session_state["enc_chapter"] = ch + 1
                st.rerun()


def _bit_html(bits: str, group_size: int = 4) -> str:
    """Render a binary string as coloured bit boxes."""
    colours = [("#1a3a5c", "white"), ("#2d4a72", "white")]
    off_bg, off_fg = "#f0f0f0", "#888"
    groups = [bits[i:i + group_size] for i in range(0, len(bits), group_size)]
    html = '<div style="display:flex;flex-wrap:wrap;gap:2px;margin:6px 0">'
    for gi, g in enumerate(groups):
        bg_on, fg_on = colours[gi % 2]
        for b in g:
            bg = bg_on if b == "1" else off_bg
            fg = fg_on if b == "1" else off_fg
            html += (
                f'<span style="display:inline-flex;align-items:center;justify-content:center;'
                f'width:24px;height:26px;border-radius:4px;font-family:monospace;'
                f'font-size:13px;font-weight:700;background:{bg};color:{fg}">{b}</span>'
            )
        html += '<span style="width:6px"></span>'
    html += "</div>"
    return html


# ── Chapter renderers ─────────────────────────────────────────────────────────

def _ch0_everything_is_bits():
    st.markdown("""
A computer has no concept of a number, a letter, a colour, or a song.
It only knows two states: **on** and **off**. We call those 1 and 0.

Every piece of data your computer handles — a spreadsheet, a photo, a voice call —
is ultimately a long sequence of those two states. *Encoding* is the set of rules
that decides what a particular sequence means.
""")

    st.info(
        "**The core idea:** There is no such thing as 'the number 65' stored in memory. "
        "There's a byte — `01000001` — and depending on the context, "
        "that's the integer 65, the hex value 0x41, or the ASCII character 'A'. "
        "The same bits, three completely different meanings."
    )

    st.markdown("#### The same byte, different interpretations")

    val = st.slider("Pick a byte value (0–255)", 0, 255, 65, key="enc_demo_val")
    bits = to_binary(val, 8)

    st.markdown(_bit_html(bits), unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Unsigned integer", val)
    c2.metric("Hex", f"0x{val:02X}")
    signed = val if val < 128 else val - 256
    c3.metric("Signed integer", signed)
    c4.metric("ASCII character", chr(val) if 32 <= val <= 126 else "—")

    st.divider()
    st.markdown("#### The encoding hierarchy")
    st.markdown("""
Everything builds upward from single bits:

```
Bit        → 0 or 1
Nibble     → 4 bits  (one hex digit)
Byte       → 8 bits  (0–255)
Word       → 16/32/64 bits (depends on architecture)
Integer    → bytes interpreted as a number (signed or unsigned)
Float      → bytes interpreted via IEEE-754 standard
Character  → byte(s) interpreted via an encoding standard (ASCII, UTF-8 …)
String     → sequence of character bytes
```
""")

    st.markdown("#### Why does this matter?")
    st.markdown("""
- **Bugs**: treating signed bytes as unsigned (or vice versa) is a classic bug.
- **Efficiency**: choosing the right data type saves memory — a boolean doesn't need 32 bits.
- **Security**: many vulnerabilities (buffer overflows, format string attacks) exploit
  assumptions about how data is encoded.
- **Interoperability**: network protocols and file formats must agree on encoding — that's
  why standards like UTF-8 and IEEE-754 exist.
""")


def _ch1_integers():
    level = st.session_state.get("level", "Intermediate")

    st.markdown("""
Integers are the simplest case: a fixed number of bits, read as a binary number.
But even here there are choices — how many bits? Signed or unsigned? Which byte comes first?
""")

    col_in, col_opt = st.columns([2, 1])
    with col_in:
        n = st.number_input("Integer value", value=65, step=1,
                            min_value=-(2 ** 31), max_value=2 ** 31 - 1,
                            key="enc_int_val")
    with col_opt:
        bits = st.select_slider("Bit width", [8, 16, 32], value=8, key="enc_int_bits")

    n = int(n)
    u = n & ((1 << bits) - 1)
    binary_str = to_binary(u, bits)
    r = int_to_bytes_repr(n)

    st.divider()
    st.markdown("#### Binary representation")
    st.markdown(_bit_html(binary_str), unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Decimal (signed)", r["decimal_signed"])
    c2.metric("Decimal (unsigned)", u)
    c3.metric("Hexadecimal", f"0x{to_hex(u, bits // 4)}")
    c4.metric("Octal", f"0o{oct(u)[2:]}")

    if bits == 8 and 32 <= u <= 126:
        st.info(f"💡 This byte is also the ASCII character **`{chr(u)}`**.")

    st.divider()
    st.markdown("#### Place values — what each bit contributes")
    powers = [2 ** (bits - 1 - i) for i in range(bits)]
    bit_vals = [int(b) for b in binary_str]
    contributions = [bv * p for bv, p in zip(bit_vals, powers)]
    df = pd.DataFrame({
        "Bit":          [f"bit {bits-1-i}" for i in range(bits)],
        "Place value":  [f"2^{bits-1-i} = {p}" for i, p in enumerate(powers)],
        "Is set":       bit_vals,
        "Contributes":  contributions,
    })
    st.dataframe(df, hide_index=True, use_container_width=True)
    active = [str(c) for c in contributions if c]
    st.markdown("**Sum:** " + " + ".join(active) + f" = **{u}**" if active else "**Sum: 0**")

    st.divider()
    st.markdown("#### Two's complement — how negative numbers work")

    with st.expander("Why does −1 become 0xFF?", expanded=False):
        st.markdown("""
Computers don't have a minus sign in hardware. Instead, negative numbers use
**two's complement**:

1. Start with the positive version in binary
2. **Flip every bit** (one's complement)
3. **Add 1**

The clever property: adding a number to its two's complement always gives zero
(with a carry out that's discarded). So the hardware can add and subtract using
the exact same circuit.
""")

    tc_val = st.slider("Show two's complement of:", -128, 127, -1, key="enc_tc")
    pos_bits = to_binary(abs(tc_val) & 0xFF, 8)
    flipped  = to_binary((~tc_val) & 0xFF, 8)
    result   = to_binary((-tc_val) & 0xFF, 8)

    if tc_val < 0:
        st.markdown(f"**Step 1 — positive form:** `{pos_bits}` = {abs(tc_val)}")
        st.markdown(f"**Step 2 — flip all bits:** `{flipped}`")
        st.markdown(f"**Step 3 — add 1:** `{result}` = 0x{(-tc_val)&0xFF:02X}")
        st.success(f"Stored representation of {tc_val} in 8 bits: `{to_binary(tc_val & 0xFF, 8)}`")
    else:
        st.info(f"{tc_val} is positive — stored as `{pos_bits}` = 0x{tc_val:02X}.")

    if bits >= 16:
        st.divider()
        st.markdown("#### Byte order (endianness)")
        st.markdown("""
A multi-byte integer can be stored with the **most significant byte first** (big-endian)
or **least significant byte first** (little-endian). x86 and ARM use little-endian.
Network protocols use big-endian (called "network byte order").
""")
        bcol1, bcol2 = st.columns(2)
        fmt_char = "i" if n < 0 else "I"
        try:
            le_bytes = struct.pack(f"<{fmt_char}", u)
            be_bytes = struct.pack(f">{fmt_char}", u)
            with bcol1:
                st.markdown("**Little-endian** (x86 / ARM)")
                for i, byte in enumerate(le_bytes[:bits // 8]):
                    st.code(f"addr +{i}: 0x{byte:02X}  {byte:08b}")
            with bcol2:
                st.markdown("**Big-endian** (network byte order)")
                for i, byte in enumerate(be_bytes[:bits // 8]):
                    st.code(f"addr +{i}: 0x{byte:02X}  {byte:08b}")
        except struct.error:
            st.warning("Value out of range for selected bit width.")


def _ch2_floats():
    st.markdown("""
Integers are easy — they're just binary numbers. But what about decimals?
`3.14`, `–0.001`, `6.022 × 10²³`?

The answer is **IEEE-754**, a 1985 standard that nearly every processor on earth
follows. It's essentially scientific notation in binary.
""")

    st.info(
        "**The formula:** `value = (−1)^sign × mantissa × 2^exponent`  \n"
        "A 32-bit float splits its bits: 1 for sign, 8 for exponent, 23 for mantissa."
    )

    f_val = st.number_input("Float value to inspect", value=3.14,
                            format="%.10f", key="enc_float_val")
    r = ieee754_approx(float(f_val))

    sign_bits = r["binary"][0]
    exp_bits  = r["binary"][1:9]
    mant_bits = r["binary"][9:]

    st.divider()
    st.markdown("#### 32-bit layout")

    def _field(bits_str, label, bg, fg="white"):
        return (
            f'<div style="display:inline-block;background:{bg};border-radius:6px;'
            f'padding:6px 10px;margin:3px;vertical-align:top">'
            f'<div style="font-size:10px;color:{fg};opacity:.8;margin-bottom:2px">{label}</div>'
            f'<div style="font-family:monospace;font-size:13px;color:{fg};letter-spacing:2px">{bits_str}</div>'
            f'</div>'
        )

    st.markdown(
        _field(sign_bits,  "Sign (1 bit)",       "#C0392B") +
        _field(exp_bits,   "Exponent (8 bits)",   "#8E44AD") +
        _field(mant_bits,  "Mantissa (23 bits)",  "#2471A3"),
        unsafe_allow_html=True,
    )

    mantissa_float = (
        1.0 + r["mantissa"] / (1 << 23)
        if r["exponent_raw"] != 0
        else r["mantissa"] / (1 << 23)
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Sign", "− (negative)" if r["sign"] else "+ (positive)")
    c2.metric("Exponent (stored)", r["exponent_raw"],
              delta=f"actual: {r['exponent_val']} (subtract bias 127)")
    c3.metric("Mantissa", f"{mantissa_float:.8f}")

    st.markdown(
        f"**Reconstructed:** `(−1)^{r['sign']} × {mantissa_float:.8f} × 2^{r['exponent_val']}"
        f" ≈ {float(f_val)}`  \n"
        f"**Hex:** `0x{r['hex']}`"
    )

    st.divider()
    st.markdown("#### Special values")
    st.markdown("""
IEEE-754 reserves certain bit patterns for special cases:

| Pattern | Meaning |
|---------|---------|
| Exponent = 0, mantissa = 0 | ±Zero |
| Exponent = 255, mantissa = 0 | ±Infinity |
| Exponent = 255, mantissa ≠ 0 | NaN (Not a Number) |
| Exponent = 0, mantissa ≠ 0 | Subnormal (very small numbers near zero) |
""")

    st.divider()
    st.markdown("#### Why does `0.1 + 0.2 ≠ 0.3`?")

    with st.expander("The famous floating-point trap — click to explore"):
        a, b = 0.1, 0.2
        ra = ieee754_approx(a)
        rb = ieee754_approx(b)
        rc = ieee754_approx(a + b)
        rd = ieee754_approx(0.3)

        st.markdown("""
`0.1` in binary is `0.0001100110011…` — a repeating pattern, like 1/3 in decimal.
It can't be represented exactly in 23 mantissa bits, so it gets rounded.
That rounding error is tiny, but it accumulates.
""")
        tbl = pd.DataFrame([
            {"Value": "0.1",       "Exact decimal stored": f"{a:.20f}", "Hex": f"0x{ra['hex']}"},
            {"Value": "0.2",       "Exact decimal stored": f"{b:.20f}", "Hex": f"0x{rb['hex']}"},
            {"Value": "0.1 + 0.2", "Exact decimal stored": f"{a+b:.20f}", "Hex": f"0x{rc['hex']}"},
            {"Value": "0.3",       "Exact decimal stored": f"{0.3:.20f}", "Hex": f"0x{rd['hex']}"},
        ])
        st.dataframe(tbl, hide_index=True, use_container_width=True)
        st.info(
            "**Fix:** Use `math.isclose(a, b)` for comparisons, or `decimal.Decimal` "
            "for exact arithmetic (e.g. financial calculations)."
        )

    st.divider()
    st.markdown("#### Double precision (64-bit)")
    st.markdown("""
Most modern code uses `double` (float64) by default:
- **1** sign bit
- **11** exponent bits (bias 1023)
- **52** mantissa bits

That gives about 15–17 significant decimal digits of precision — much better than
float32's 7. Python's `float` type is always float64.
""")


def _ch3_strings():
    st.markdown("""
Text is stored as a sequence of numbers. The question is: which number represents
which character? That mapping is called an **encoding**.

For the first few decades of computing, ASCII was enough — 128 characters covering
the English alphabet, digits, and punctuation. Then the internet connected the world,
and we needed something bigger.
""")

    st.info(
        "**Unicode** assigns a unique number (a *code point*) to every character in "
        "every human writing system — over 140,000 so far, from Latin to Arabic to emoji. "
        "**UTF-8** is the most popular encoding of Unicode, and it's backward-compatible "
        "with ASCII."
    )

    st.divider()
    st.markdown("#### ASCII — the foundation")
    st.markdown("""
ASCII uses 7 bits to encode 128 characters. The key ranges to know:

| Range | Characters |
|-------|-----------|
| 0–31 | Control characters (newline, tab, null…) |
| 32–126 | Printable: space, `!` … `~` |
| 48–57 | `'0'` to `'9'` |
| 65–90 | `'A'` to `'Z'` |
| 97–122 | `'a'` to `'z'` |
""")

    ascii_val = st.slider("Explore ASCII", 32, 126, 65, key="enc_ascii")
    abits = to_binary(ascii_val, 8)
    ac1, ac2, ac3 = st.columns(3)
    ac1.metric("Character", chr(ascii_val))
    ac2.metric("Decimal", ascii_val)
    ac3.metric("Hex", f"0x{ascii_val:02X}")
    st.markdown(_bit_html(abits), unsafe_allow_html=True)

    st.divider()
    st.markdown("#### String inspector")

    scol1, scol2 = st.columns([2, 1])
    with scol1:
        s = st.text_input("String to inspect", value="Hello, 世界! 🌍", key="enc_str")
    with scol2:
        enc = st.selectbox("Encoding", ["utf-8", "utf-16", "ascii", "latin-1"],
                           key="enc_enc")

    try:
        r = str_to_bytes_repr(s, enc)

        m1, m2, m3 = st.columns(3)
        m1.metric("Characters", r["length_chars"])
        m2.metric("Bytes stored", r["length_bytes"],
                  delta="multi-byte chars present" if r["length_bytes"] > r["length_chars"] else "all single-byte")
        m3.metric("Bytes per char (avg)",
                  f"{r['length_bytes']/r['length_chars']:.1f}" if r["length_chars"] else "—")

        st.markdown("#### Character breakdown")
        st.caption("Each card shows the character, its Unicode code point, and its encoded bytes.")

        # Show up to 12 characters
        display_chars = list(zip(s, r["codepoints"]))[:12]
        card_cols = st.columns(min(len(display_chars), 6))
        for i, (char, cp) in enumerate(display_chars):
            col = card_cols[i % 6]
            try:
                raw = char.encode(enc)
                hex_str = raw.hex().upper()
            except (UnicodeEncodeError, LookupError):
                hex_str = "N/A"
            col.markdown(
                f'<div style="text-align:center;background:var(--secondary-background-color);'
                f'border-radius:8px;padding:8px 4px;margin-bottom:8px">'
                f'<div style="font-size:22px;line-height:1.3">{char}</div>'
                f'<div style="font-size:11px;font-family:monospace;color:#666">U+{cp:04X}</div>'
                f'<div style="font-size:10px;color:#999;margin-top:2px">{hex_str}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        if len(s) > 12:
            st.caption(f"… and {len(s) - 12} more characters.")

        st.markdown(f"**Full hex dump:** `{r['hex']}`")
        st.markdown(
            f"**Code points:** `{' '.join(f'U+{cp:04X}' for cp in r['codepoints'])}`"
        )

    except (UnicodeEncodeError, LookupError) as e:
        st.error(f"Encoding error: {e}. Try a different encoding or a simpler string.")

    st.divider()
    st.markdown("#### How UTF-8 works")

    with st.expander("The variable-length encoding scheme"):
        st.markdown("""
UTF-8 is clever: it's **backward-compatible with ASCII** (the first 128 code points
are stored as a single byte, identical to ASCII), but it can encode the full Unicode
range using up to 4 bytes.

The leading bits of the first byte tell you how many bytes the character uses:

| First byte pattern | Bytes | Code point range | Example |
|---|---|---|---|
| `0xxxxxxx` | 1 | U+0000–U+007F | `A` (U+0041) |
| `110xxxxx 10xxxxxx` | 2 | U+0080–U+07FF | `é` (U+00E9) |
| `1110xxxx 10xxxxxx 10xxxxxx` | 3 | U+0800–U+FFFF | `世` (U+4E16) |
| `11110xxx 10xxxxxx 10xxxxxx 10xxxxxx` | 4 | U+10000–U+10FFFF | `🌍` (U+1F30D) |

Continuation bytes always start with `10`, which means a decoder can always
re-sync even if it starts reading in the middle of a stream.
""")


def _ch4_python_memory():
    st.markdown("""
Everything so far has been abstract. Let's make it concrete: look at real Python
objects living at real memory addresses in this very process.

In CPython, every object has a **header** containing its type pointer and reference
count, followed by its actual data. `id(x)` returns the raw memory address.
""")

    st.info(
        "**Reference counting:** CPython tracks how many variables point to each object. "
        "When the count hits zero, the memory is freed. This is why `del x` doesn't "
        "immediately free memory if another variable still holds a reference."
    )

    st.divider()
    st.markdown("#### Object inspector")

    expr = st.text_input(
        "Python expression to inspect",
        value="[1, 2, 3]",
        key="enc_py_expr",
        help="Try: 42, 3.14, 'hello', [1,2,3], {'a':1}, (1,2)",
    )

    try:
        obj  = eval(expr, {"__builtins__": __builtins__})
        addr = id(obj)
        size = sys.getsizeof(obj)

        mc1, mc2, mc3, mc4 = st.columns(4)
        mc1.metric("Type", type(obj).__name__)
        mc2.metric("Memory address", f"0x{addr:012X}")
        mc3.metric("Object size", f"{size} bytes")
        mc4.metric("Reference count", sys.getrefcount(obj) - 1,
                   help="sys.getrefcount adds 1 for its own argument")

        type_name = type(obj).__name__

        st.divider()

        if type_name == "int":
            st.markdown("#### Integer memory layout")
            st.markdown(f"""
Python `int` is **arbitrary precision** — it grows as needed. Small integers
(−5 to 256) are **pre-allocated** and cached at startup, so `id(1) == id(1)` is
always true. For larger values, a new object is created each time.

This `int` uses **{size} bytes**: 28 bytes of base overhead (ob_refcnt + ob_type + ob_digit)
plus {max(0, size - 28)} bytes for the actual digits.
""")
            st.code(
                f">>> x = {expr}\n"
                f">>> id(x)   # memory address\n"
                f"0x{addr:016X}\n"
                f">>> sys.getsizeof(x)\n"
                f"{size}",
                language="python",
            )
            if -5 <= int(obj) <= 256:
                st.success(
                    f"✓ {int(obj)} is in the CPython integer cache (−5 to 256). "
                    "Every reference to this value points to the same object."
                )

        elif type_name == "str":
            enc_type = "Latin-1 (1 byte/char)" if all(ord(c) < 256 for c in str(obj)) else "UCS-2 or UCS-4"
            st.markdown("#### String memory layout")
            st.markdown(f"""
Python strings are **immutable** — once created, the bytes never change.
This allows CPython to share (intern) string objects aggressively.

- Base overhead: 49 bytes (header + kind/hash/length fields)
- Char data: {len(str(obj))} chars × {1 if all(ord(c)<256 for c in str(obj)) else 2} bytes/char = {size - 49} bytes
- Internal encoding: {enc_type}
""")

        elif type_name == "list":
            elem_size = sum(sys.getsizeof(x) for x in obj)
            st.markdown("#### List memory layout")
            st.markdown(f"""
A Python `list` is an **array of 8-byte pointers**, not the objects themselves.
The objects live elsewhere in memory; the list just stores addresses pointing to them.

- List object (pointer array): **{size} bytes**
- Elements (separate objects): ~{elem_size} bytes
- Total memory: ~{size + elem_size} bytes

Lists **over-allocate** capacity so that `.append()` is O(1) amortised.
""")

        elif type_name == "dict":
            st.markdown("#### Dict memory layout")
            st.markdown(f"""
Python dicts are **hash tables**. Each key–value pair occupies one hash table slot.
From Python 3.7+ they preserve insertion order.

- Dict object: **{size} bytes** (includes the initial hash table)
- Each entry: hash (8 bytes) + key pointer (8 bytes) + value pointer (8 bytes)
""")

        if isinstance(obj, (list, tuple, dict)):
            st.markdown("#### Element addresses")
            items = list(obj.items()) if isinstance(obj, dict) else list(obj)
            for i, item in enumerate(items[:8]):
                st.code(
                    f"[{i}]  type={type(item).__name__:8s}  "
                    f"id=0x{id(item):016X}  "
                    f"size={sys.getsizeof(item):4d}B  "
                    f"value={repr(item)[:40]}",
                    language="text",
                )
            if len(items) > 8:
                st.caption(f"… and {len(items) - 8} more elements.")

    except Exception as e:
        st.error(f"Could not evaluate `{expr}`: {e}")

    st.divider()
    st.markdown("#### Integer interning — a quirk worth knowing")

    with st.expander("Why is `a is b` True for small integers?"):
        st.markdown("""
```python
>>> a = 256
>>> b = 256
>>> a is b
True          # same object! (cached)

>>> a = 257
>>> b = 257
>>> a is b
False         # different objects (not cached)
```

CPython pre-allocates integer objects for −5 to 256 at interpreter startup.
Any variable assigned one of these values gets a reference to the same object.

This is an **implementation detail** — don't rely on `is` for value comparisons.
Always use `==`.
""")



# ── Chapter dispatch ──────────────────────────────────────────────────────────

CHAPTER_FNS = [
    _ch0_everything_is_bits,
    _ch1_integers,
    _ch2_floats,
    _ch3_strings,
    _ch4_python_memory,
]


# ── Main render ───────────────────────────────────────────────────────────────

def render():
    st.title("Data & Encoding")
    st.caption("How does a computer represent anything? It all starts here.")

    if "enc_chapter" not in st.session_state:
        st.session_state["enc_chapter"] = 0

    ch = st.session_state["enc_chapter"]

    st.markdown(_nav_html(ch), unsafe_allow_html=True)
    st.progress(ch / (len(CHAPTERS) - 1))

    st.subheader(CHAPTERS[ch])
    st.divider()

    CHAPTER_FNS[ch]()

    st.divider()
    _prev_next(ch)

    with st.sidebar:
        st.markdown("### Data & Encoding")
        for i, title in enumerate(CHAPTERS):
            icon = "✅" if i < ch else ("▶️" if i == ch else "○")
            if st.button(
                f"{icon} {title}",
                key=f"sidebar_enc_{i}",
                use_container_width=True,
                type="primary" if i == ch else "secondary",
            ):
                st.session_state["enc_chapter"] = i
                st.rerun()