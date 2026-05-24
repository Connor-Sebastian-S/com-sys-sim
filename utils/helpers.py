# utils/helpers.py

import struct
import math

def to_bin(value: int, bits: int = 32) -> str:
    """
    Return binary representation with fixed width.
    """
    mask = (1 << bits) - 1
    value &= mask
    return format(value, f"0{bits}b")


def to_hex(value: int, bits: int = 32) -> str:
    """
    Return fixed-width hexadecimal representation.
    """
    hex_digits = bits // 4
    mask = (1 << bits) - 1
    value &= mask
    return format(value, f"0{hex_digits}X")

def real_id(value: int, bits: int = 32) -> int:
    """
    Force integer into fixed-width signed range.
    """
    mask = (1 << bits) - 1
    value &= mask

    # sign extension
    if value & (1 << (bits - 1)):
        value -= (1 << bits)

    return value


def sizeof(value) -> int:
    if isinstance(value, int):
        return 4
    elif isinstance(value, float):
        return 8
    elif isinstance(value, str):
        return len(value.encode("utf-8"))
    else:
        return len(str(value))


def int_to_bytes_repr(value: int, bits: int = 32) -> dict:
    mask = (1 << bits) - 1
    unsigned = value & mask

    signed = unsigned
    if unsigned & (1 << (bits - 1)):
        signed -= (1 << bits)

    byte_len = bits // 8
    byte_data = unsigned.to_bytes(byte_len, byteorder="little", signed=False)

    return {
        "decimal_signed": signed,
        "decimal_unsigned": unsigned,
        "bytes": byte_data,
    }


def str_to_bytes_repr(value: str, encoding: str = "utf-8") -> dict:
    encoded = value.encode(encoding)

    return {
        "length_chars": len(value),
        "length_bytes": len(encoded),
        "bytes": encoded,
        "hex": encoded.hex().upper(),
        "codepoints": [ord(c) for c in value],
    }


import struct

def float_to_ieee754(value: float) -> dict:
    # pack float into 32-bit binary
    packed = struct.pack("!f", value)
    as_int = int.from_bytes(packed, byteorder="big")
    bits = format(as_int, "032b")

    sign = int(bits[0])
    exponent_bits = bits[1:9]
    mantissa_bits = bits[9:]

    exponent_biased = int(exponent_bits, 2)
    exponent_actual = exponent_biased - 127

    mantissa_value = 1.0
    for i, bit in enumerate(mantissa_bits):
        if bit == "1":
            mantissa_value += 2 ** (-(i + 1))

    return {
        "raw_bits": bits,
        "sign": sign,
        "exponent_biased": exponent_biased,
        "exponent_actual": exponent_actual,
        "mantissa_value": mantissa_value,
        "hex": f"0x{as_int:08X}",
    }


def debug_registers(a32, b32, to_bin):
    """
    Likely used in UI like:
      f"A: {to_bin(a32,32)}"
    """
    return (
        f"  A: {to_bin(a32,32)}\n"
        f"  B: {to_bin(b32,32)}\n"
    )

def alu_op(a: int, b: int, op: str, bits: int = 32) -> dict:
    mask = (1 << bits) - 1

    a &= mask
    b &= mask
    op = op.upper()

    overflow = False

    if op == "ADD":
        result = a + b
        overflow = result > mask
        result &= mask

    elif op == "SUB":
        result = (a - b) & mask
        overflow = True  # simplified model (or compute properly later)

    elif op == "MUL":
        result = (a * b) & mask

    elif op == "AND":
        result = a & b

    elif op == "OR":
        result = a | b

    elif op == "XOR":
        result = a ^ b

    elif op == "NOT":
        result = (~a) & mask

    elif op == "SHL":
        result = (a << b) & mask

    elif op == "SHR":
        result = a >> b

    else:
        raise ValueError(f"Unsupported op: {op}")

    # signed interpretation
    signed = result if result < (1 << (bits - 1)) else result - (1 << bits)

    return {
        "result": signed,
        "result32": result,
        "result_bin": format(result, f"0{bits}b"),
        "result_hex": format(result, f"0{bits//4}X"),
        "zero_flag": result == 0,
        "negative_flag": (result & (1 << (bits - 1))) != 0,
        "overflow": overflow,
    }