"""Shared helpers for the CPU simulator."""
import struct, sys, ctypes, dis, io
from typing import Any

# ── binary / encoding helpers ────────────────────────────────────────────────

def to_bin(n: int, bits: int = 8) -> str:
    """Return zero-padded binary string."""
    return format(n & ((1 << bits) - 1), f"0{bits}b")

def to_hex(n: int, nibbles: int = 2) -> str:
    return format(n & ((1 << nibbles * 4) - 1), f"0{nibbles}X")

def int_to_bytes_repr(n: int) -> dict:
    """Full breakdown of an integer."""
    signed = ctypes.c_int32(n).value
    unsigned = n & 0xFFFFFFFF
    return {
        "decimal_signed":   signed,
        "decimal_unsigned": unsigned,
        "hex":              f"0x{to_hex(unsigned, 8)}",
        "binary":           to_bin(unsigned, 32),
        "bytes_le":         list(struct.pack("<I", unsigned)),
        "bytes_be":         list(struct.pack(">I", unsigned)),
        "size_bytes":       4,
    }

def float_to_ieee754(f: float) -> dict:
    """Decompose a float into IEEE-754 fields."""
    bits = struct.unpack(">I", struct.pack(">f", f))[0]
    sign     = (bits >> 31) & 1
    exponent = (bits >> 23) & 0xFF
    mantissa =  bits        & 0x7FFFFF
    return {
        "raw_bits":   to_bin(bits, 32),
        "sign":       sign,
        "exponent_biased": exponent,
        "exponent_actual": exponent - 127,
        "mantissa_bits":   to_bin(mantissa, 23),
        "mantissa_value":  1 + mantissa / (2**23),
        "hex":        f"0x{to_hex(bits, 8)}",
    }

def str_to_bytes_repr(s: str, encoding: str = "utf-8") -> dict:
    raw = s.encode(encoding)
    return {
        "encoding":  encoding,
        "bytes":     list(raw),
        "hex":       raw.hex(" ").upper(),
        "length_chars": len(s),
        "length_bytes": len(raw),
        "codepoints":  [ord(c) for c in s],
    }

# ── memory helpers ───────────────────────────────────────────────────────────

def real_id(obj: Any) -> str:
    """Return CPython object address as hex."""
    return f"0x{id(obj):016X}"

def sizeof(obj: Any) -> int:
    return sys.getsizeof(obj)

# ── disassembly helper ───────────────────────────────────────────────────────

def disassemble(source: str) -> str:
    """Compile source and return dis.dis() output."""
    try:
        code = compile(source, "<input>", "exec")
        buf  = io.StringIO()
        dis.dis(code, file=buf)
        return buf.getvalue()
    except SyntaxError as e:
        return f"SyntaxError: {e}"

def get_bytecode_instructions(source: str) -> list[dict]:
    """Return list of instruction dicts for table display."""
    try:
        code = compile(source, "<input>", "exec")
        rows = []
        for instr in dis.get_instructions(code):
            rows.append({
                "Offset": instr.offset,
                "Opcode": instr.opname,
                "Arg":    instr.arg if instr.arg is not None else "—",
                "Arg repr": instr.argrepr or "—",
                "Stack effect": dis.stack_effect(instr.opcode, instr.arg) if instr.arg is not None else "—",
            })
        return rows
    except SyntaxError as e:
        return [{"Offset": "—", "Opcode": f"SyntaxError: {e}", "Arg": "—", "Arg repr": "—", "Stack effect": "—"}]

# ── ALU helpers ──────────────────────────────────────────────────────────────

def alu_op(a: int, b: int, op: str) -> dict:
    ops = {
        "ADD":  lambda x,y: x + y,
        "SUB":  lambda x,y: x - y,
        "MUL":  lambda x,y: x * y,
        "AND":  lambda x,y: x & y,
        "OR":   lambda x,y: x | y,
        "XOR":  lambda x,y: x ^ y,
        "SHL":  lambda x,y: x << (y % 32),
        "SHR":  lambda x,y: x >> (y % 32),
        "NOT":  lambda x,y: ~x & 0xFFFFFFFF,
    }
    result = ops[op](a, b) if op in ops else 0
    result32 = result & 0xFFFFFFFF
    return {
        "op": op,
        "a": a, "b": b,
        "result": result,
        "result32": result32,
        "result_bin": to_bin(result32, 32),
        "result_hex": f"0x{to_hex(result32, 8)}",
        "zero_flag":  result32 == 0,
        "negative_flag": bool(result32 >> 31),
        "overflow":   result != result32,
    }

# ── pipeline helpers ─────────────────────────────────────────────────────────

PIPELINE_STAGES = ["IF", "ID", "EX", "MEM", "WB"]
STAGE_LABELS = {
    "IF":  "Instruction Fetch",
    "ID":  "Instruction Decode",
    "EX":  "Execute (ALU)",
    "MEM": "Memory Access",
    "WB":  "Write Back",
}
STAGE_COLORS = {
    "IF":  "#4B8DE8",
    "ID":  "#9B6DD4",
    "EX":  "#E87B4B",
    "MEM": "#4BB8A8",
    "WB":  "#68C46A",
}

def simulate_pipeline(instructions: list[str]) -> list[dict]:
    """Return a cycle-by-cycle pipeline table."""
    n = len(instructions)
    total_cycles = n + len(PIPELINE_STAGES) - 1
    table = []
    for i, instr in enumerate(instructions):
        row = {"Instruction": instr}
        for c in range(total_cycles):
            stage_idx = c - i
            if 0 <= stage_idx < len(PIPELINE_STAGES):
                row[f"C{c+1}"] = PIPELINE_STAGES[stage_idx]
            else:
                row[f"C{c+1}"] = ""
        table.append(row)
    return table
