"""
Number system utilities: binary, hex, octal, ASCII, two's complement
"""
from __future__ import annotations
import struct, sys, ctypes, dis, io
from typing import Any

"""Return zero-padded binary string."""
def to_binary(n: int, bits: int = 8) -> str:
    if n < 0:
        n = n & ((1 << bits) - 1)
    return format(n & ((1 << bits) - 1), f'0{bits}b')


def to_hex(n: int, digits: int = 2) -> str:
    return format(n & 0xFFFF, f'0{digits}X')


def to_octal(n: int) -> str:
    return format(n & 0xFF, '03o')

"""Interpret n as signed two's complement."""
def twos_complement(n: int, bits: int = 8) -> int:
    if n >= (1 << (bits - 1)):
        return n - (1 << bits)
    return n


def signed_str(n: int, bits: int = 8) -> str:
    s = twos_complement(n, bits)
    return f"{s:+d}"


"""Group binary string for readability: '10110011' → '1011 0011'"""
def bit_groups(binary: str, group: int = 4) -> str:
    return ' '.join(binary[i:i+group] for i in range(0, len(binary), group))


def decode_ascii(n: int) -> str:
    if 32 <= n <= 126:
        return chr(n)
    return {0: 'NUL', 8: 'BS', 9: 'TAB', 10: 'LF', 13: 'CR',
            27: 'ESC', 127: 'DEL'}.get(n, f'\\x{n:02X}')


def nibble_high(n: int) -> int:
    return (n >> 4) & 0x0F


def nibble_low(n: int) -> int:
    return n & 0x0F

"""BCD: tens digit, units digit."""
def bcd_encode(n: int) -> tuple[int, int]:
    return (n // 10) & 0xF, n % 10

"""Very rough IEEE-754 single-precision breakdown."""
def ieee754_approx(n: float) -> dict:
    import struct
    packed = struct.pack('>f', n)
    bits = int.from_bytes(packed, 'big')
    sign     = (bits >> 31) & 1
    exponent = (bits >> 23) & 0xFF
    mantissa = bits & 0x7FFFFF
    return {
        "sign":        sign,
        "exponent_raw": exponent,
        "exponent_val": exponent - 127,
        "mantissa":    mantissa,
        "binary":      format(bits, '032b'),
        "hex":         format(bits, '08X'),
    }

def int_to_bytes_repr(n: int) -> dict:
    """Full breakdown of an integer."""
    signed = ctypes.c_int32(n).value
    unsigned = n & 0xFFFFFFFF
    return {
        "decimal_signed":   signed,
        "decimal_unsigned": unsigned,
        "hex":              f"0x{to_hex(unsigned, 8)}",
        "binary":           to_binary(unsigned, 32),
        "bytes_le":         list(struct.pack("<I", unsigned)),
        "bytes_be":         list(struct.pack(">I", unsigned)),
        "size_bytes":       4,
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
        "result_bin": to_binary(result32, 32),
        "result_hex": f"0x{to_hex(result32, 8)}",
        "zero_flag":  result32 == 0,
        "negative_flag": bool(result32 >> 31),
        "overflow":   result != result32,
    }

MEMORY_TYPE_INFO = {
    "SRAM": {
        "full": "Static RAM",
        "tech": "6-transistor flip-flop per cell",
        "speed": "0.5–2 ns access time",
        "use": "CPU registers, L1/L2 cache",
        "volatile": True,
        "rewritable": True,
        "notes": "Holds data as long as power is supplied. Fast but expensive and bulky.",
    },
    "DRAM": {
        "full": "Dynamic RAM",
        "tech": "1 transistor + 1 capacitor per cell",
        "speed": "50–100 ns access time",
        "use": "Main memory (RAM sticks)",
        "volatile": True,
        "rewritable": True,
        "notes": "Capacitors leak; must be refreshed every ~64ms. Slow but dense and cheap.",
    },
    "ROM": {
        "full": "Read-Only Memory",
        "tech": "Mask-programmed during fabrication",
        "speed": "~50 ns",
        "use": "Fixed lookup tables, character generators",
        "volatile": False,
        "rewritable": False,
        "notes": "Contents fixed at manufacture. Cannot be changed in the field.",
    },
    "PROM": {
        "full": "Programmable ROM",
        "tech": "Fusible links (one-time programmable)",
        "speed": "~50 ns",
        "use": "Field-programmable firmware (once)",
        "volatile": False,
        "rewritable": False,
        "notes": "Written once by 'blowing' fuses. Permanent after programming.",
    },
    "EPROM": {
        "full": "Erasable Programmable ROM",
        "tech": "Floating-gate transistors, UV erased",
        "speed": "~150 ns",
        "use": "Legacy firmware, development prototypes",
        "volatile": False,
        "rewritable": True,
        "notes": "Erased by exposing to UV light through a quartz window. Takes ~20 min to erase.",
    },
    "EEPROM": {
        "full": "Electrically Erasable Programmable ROM",
        "tech": "Floating-gate, electrically erased byte-by-byte",
        "speed": "~200 ns read, ms per write",
        "use": "BIOS settings, microcontroller config",
        "volatile": False,
        "rewritable": True,
        "notes": "Erased and written electrically. Slow writes but very convenient. ~1M write cycles.",
    },
    "Flash": {
        "full": "Flash Memory",
        "tech": "NAND/NOR floating-gate, block-erased",
        "speed": "~100 µs erase, ~10 µs write",
        "use": "SSDs, USB drives, BIOS chips, phones",
        "volatile": False,
        "rewritable": True,
        "notes": "Like EEPROM but erased in blocks. Very dense. Wear levelling needed. ~10K–100K cycles.",
    },
    "Virtual": {
        "full": "Virtual Memory",
        "tech": "Page table + MMU mapping to disk (swap)",
        "speed": "Milliseconds if paged out to disk",
        "use": "Extending addressable space beyond physical RAM",
        "volatile": True,
        "rewritable": True,
        "notes": "OS maps virtual pages to physical frames or disk. A page fault triggers a disk read.",
    },
}

CACHE_LEVEL_INFO = {
    "L1": {
        "size": "32–64 KB",
        "latency": "1–4 cycles (~0.5–2 ns)",
        "type": "SRAM, on-die",
        "associativity": "4–8 way set-associative",
        "notes": "Smallest, fastest. Separate I-cache and D-cache per core.",
    },
    "L2": {
        "size": "256 KB – 1 MB",
        "latency": "4–12 cycles (~2–6 ns)",
        "type": "SRAM, on-die",
        "associativity": "8–16 way",
        "notes": "Shared or per-core. Holds recently evicted L1 lines.",
    },
    "L3": {
        "size": "8–64 MB",
        "latency": "30–40 cycles (~15–20 ns)",
        "type": "SRAM, on-die (shared)",
        "associativity": "16+ way",
        "notes": "Shared across all cores. Last stop before main RAM.",
    },
    "RAM": {
        "size": "8–128 GB",
        "latency": "~100 ns (~200–300 cycles)",
        "type": "DRAM",
        "associativity": "N/A",
        "notes": "Much slower. Cache miss penalty is significant.",
    },
}

REGISTER_INFO = {
    "A":   ("Accumulator",        "Primary register for arithmetic/logic results. Most instructions write here."),
    "B":   ("General Purpose B",  "Holds operands or intermediate values during computation."),
    "C":   ("General Purpose C",  "Often used as a counter in loop instructions."),
    "D":   ("General Purpose D",  "Used for extended data operations and I/O."),
    "PC":  ("Program Counter",    "Holds the address of the NEXT instruction to fetch. Advances automatically."),
    "SP":  ("Stack Pointer",      "Points to the top of the stack. Decrements on PUSH, increments on POP."),
    "MAR": ("Memory Address Reg", "Holds the address to be read from or written to. Connected to address bus."),
    "MDR": ("Memory Data Reg",    "Holds data being transferred to/from memory. Connected to data bus."),
    "IR":  ("Instruction Reg",    "Holds the current opcode fetched from memory."),
    "CIR": ("Current Instruction","The decoded mnemonic (human-readable) of the instruction in IR."),
}

BUS_INFO = {
    "address": {
        "width": "16-bit (simulated) / 64-bit (modern)",
        "direction": "CPU → Memory/Devices",
        "role": "Carries the memory address the CPU wants to read from or write to.",
        "lines": 16,
        "addressable": "64 KB (16-bit) / 16 EB (64-bit)",
    },
    "data": {
        "width": "8-bit (simulated) / 64-bit (modern)",
        "direction": "Bidirectional",
        "role": "Carries the actual data being read or written.",
        "lines": 8,
        "addressable": "N/A — transfers 1 byte (8-bit) or 8 bytes (64-bit) per cycle",
    },
    "control": {
        "width": "Several lines",
        "direction": "CPU ↔ Devices",
        "role": "Signals like RD (read), WR (write), INTA (interrupt ack), HOLD/HLDA (DMA).",
        "lines": "~10",
        "addressable": "N/A",
    },
}

VON_NEUMANN_VS_HARVARD = {
    "von_neumann": {
        "name": "Von Neumann Architecture",
        "description": "Single shared bus for instructions and data. CPU alternates between fetching instructions and data.",
        "pros": ["Simpler design", "Flexible — code and data can share the same memory", "Easier to program"],
        "cons": ["Von Neumann bottleneck: bus is shared → slower", "Cannot fetch instruction while reading data"],
        "examples": ["Most desktop/laptop CPUs", "x86, ARM (Cortex-A)"],
    },
    "harvard": {
        "name": "Harvard Architecture",
        "description": "Separate buses and memory for instructions and data. Can fetch and read simultaneously.",
        "pros": ["Faster — instruction fetch and data access in parallel", "No bottleneck"],
        "cons": ["More complex hardware", "Less flexible memory usage"],
        "examples": ["Microcontrollers (AVR, PIC)", "DSPs", "ARM Cortex-M (modified Harvard)"],
    },
}
