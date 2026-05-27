"""
Computer System Simulation Engine
Simulates: CPU registers, ALU, buses, cache hierarchy, RAM, ROM, interrupts, DMA
"""
from __future__ import annotations
import random
import time
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


# ── Memory types ──────────────────────────────────────────────────────────────

class MemoryType(Enum):
    SRAM   = "SRAM"          # Static RAM (cache)
    DRAM   = "DRAM"          # Dynamic RAM (main memory)
    ROM    = "ROM"            # Mask ROM (fixed)
    PROM   = "PROM"          # Programmable ROM
    EPROM  = "EPROM"         # Erasable PROM (UV)
    EEPROM = "EEPROM"        # Electrically erasable
    FLASH  = "Flash"          # Flash (BIOS/firmware)
    VMEM   = "Virtual"       # Virtual memory page


@dataclass
class MemoryCell:
    address: int
    value: int = 0
    label: str = ""
    writable: bool = True
    mem_type: MemoryType = MemoryType.DRAM
    last_accessed: float = 0.0
    access_count: int = 0

    def read(self) -> int:
        self.last_accessed = time.time()
        self.access_count += 1
        return self.value

    def write(self, val: int):
        if not self.writable:
            raise PermissionError(f"Write to read-only address 0x{self.address:04X}")
        self.value = val & 0xFF
        self.last_accessed = time.time()
        self.access_count += 1


@dataclass
class MemoryRegion:
    name: str
    start: int
    size: int
    mem_type: MemoryType
    writable: bool = True
    description: str = ""
    cells: list[MemoryCell] = field(default_factory=list)

    def __post_init__(self):
        self.cells = [
            MemoryCell(self.start + i, 0, writable=self.writable, mem_type=self.mem_type)
            for i in range(self.size)
        ]


# ── Memory map ─────────────────────────────────────────────────────────────────

class MemoryMap:
    """Simulates a flat 256-byte address space with typed regions."""
    def __init__(self):
        self.size = 256
        self.cells: list[MemoryCell] = [MemoryCell(i) for i in range(self.size)]
        self.regions: list[MemoryRegion] = []
        self._setup_regions()

    def _setup_regions(self):
        self.regions = [
            MemoryRegion("Interrupt Vector Table", 0x00, 16, MemoryType.ROM,   False, "Fixed jump addresses for interrupt handlers"),
            MemoryRegion("BIOS / Firmware",        0x10, 16, MemoryType.FLASH, False, "Startup code and hardware initialisation"),
            MemoryRegion("Stack",                  0x20, 32, MemoryType.DRAM,  True,  "LIFO store for return addresses & local vars"),
            MemoryRegion("Heap",                   0x40, 48, MemoryType.DRAM,  True,  "Dynamically allocated data"),
            MemoryRegion("Program Code",           0x70, 48, MemoryType.DRAM,  True,  "Loaded executable instructions"),
            MemoryRegion("Data Segment",           0xA0, 48, MemoryType.DRAM,  True,  "Global & static variables"),
            MemoryRegion("I/O Mapped Registers",   0xD0, 16, MemoryType.DRAM,  True,  "Memory-mapped I/O device registers"),
            MemoryRegion("DMA Buffer",             0xE0, 16, MemoryType.DRAM,  True,  "Direct Memory Access transfer buffer"),
            MemoryRegion("Video / Display Buffer", 0xF0, 16, MemoryType.DRAM,  True,  "Frame buffer for display output"),
        ]
        for region in self.regions:
            for i, cell in enumerate(region.cells):
                self.cells[region.start + i] = cell

        # Pre-load some ROM content
        ivt_values = [0x00, 0x20, 0x01, 0x20, 0x02, 0x20, 0x03, 0x20,
                      0x04, 0x20, 0x05, 0x20, 0x06, 0x20, 0x07, 0x20]
        for i, v in enumerate(ivt_values):
            self.cells[i].value = v

        bios_values = [0xF3, 0x8B, 0x47, 0x00, 0x50, 0xE8, 0x05, 0x00,
                       0x58, 0xC3, 0x90, 0x90, 0x90, 0x90, 0x90, 0x90]
        for i, v in enumerate(bios_values):
            self.cells[0x10 + i].value = v

    def region_for(self, addr: int) -> Optional[MemoryRegion]:
        for r in self.regions:
            if r.start <= addr < r.start + r.size:
                return r
        return None

    def read(self, addr: int) -> int:
        if 0 <= addr < self.size:
            return self.cells[addr].read()
        raise IndexError(f"Address 0x{addr:04X} out of range")

    def write(self, addr: int, val: int):
        if 0 <= addr < self.size:
            self.cells[addr].write(val)
        else:
            raise IndexError(f"Address 0x{addr:04X} out of range")


# ── Cache ──────────────────────────────────────────────────────────────────────

@dataclass
class CacheLine:
    tag: int = -1
    data: list[int] = field(default_factory=lambda: [0]*4)
    valid: bool = False
    dirty: bool = False
    last_used: float = 0.0


class Cache:
    """4-way set-associative cache with LRU eviction (L1 SRAM simulation)."""
    SETS = 4
    WAYS = 4
    LINE_SIZE = 4   # bytes per line

    def __init__(self, name: str, latency_cycles: int):
        self.name = name
        self.latency = latency_cycles
        self.lines: list[list[CacheLine]] = [
            [CacheLine() for _ in range(self.WAYS)] for _ in range(self.SETS)
        ]
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total else 0.0

    def _set_idx(self, addr: int) -> int:
        return (addr // self.LINE_SIZE) % self.SETS

    def _tag(self, addr: int) -> int:
        return addr // (self.LINE_SIZE * self.SETS)

    def lookup(self, addr: int) -> tuple[bool, Optional[CacheLine]]:
        s = self._set_idx(addr)
        t = self._tag(addr)
        for line in self.lines[s]:
            if line.valid and line.tag == t:
                self.hits += 1
                line.last_used = time.time()
                return True, line
        self.misses += 1
        return False, None

    def load(self, addr: int, data: list[int]) -> Optional[CacheLine]:
        """Load a cache line; evict LRU if set is full."""
        s = self._set_idx(addr)
        t = self._tag(addr)
        # Find empty slot first
        for line in self.lines[s]:
            if not line.valid:
                line.tag = t
                line.data = data[:self.LINE_SIZE]
                line.valid = True
                line.dirty = False
                line.last_used = time.time()
                return None  # no eviction
        # LRU eviction
        lru = min(self.lines[s], key=lambda l: l.last_used)
        evicted = CacheLine(lru.tag, lru.data[:], lru.valid, lru.dirty)
        self.evictions += 1
        lru.tag = t
        lru.data = data[:self.LINE_SIZE]
        lru.valid = True
        lru.dirty = False
        lru.last_used = time.time()
        return evicted

    def invalidate(self):
        for s in self.lines:
            for line in s:
                line.valid = False


# ── CPU Registers ──────────────────────────────────────────────────────────────

@dataclass
class Flags:
    zero:     bool = False   # Z — result was zero
    carry:    bool = False   # C — arithmetic carry/borrow
    negative: bool = False   # N — result was negative
    overflow: bool = False   # V — signed overflow
    interrupt: bool = True   # I — interrupts enabled

    def as_dict(self) -> dict:
        return {"Z": self.zero, "C": self.carry, "N": self.negative,
                "V": self.overflow, "I": self.interrupt}


@dataclass
class Registers:
    # General-purpose (8-bit)
    A: int = 0      # Accumulator
    B: int = 0      # General purpose
    C: int = 0      # General purpose
    D: int = 0      # General purpose
    # Special (16-bit)
    PC: int = 0x70  # Program Counter (points into code segment)
    SP: int = 0x3F  # Stack Pointer (top of stack)
    # Internal CPU registers
    MAR: int = 0    # Memory Address Register
    MDR: int = 0    # Memory Data Register
    IR:  int = 0    # Instruction Register (opcode)
    CIR: str = ""   # Current Instruction (decoded mnemonic)
    # ALU
    ALU_A: int = 0
    ALU_B: int = 0
    ALU_OUT: int = 0
    FLAGS: Flags = field(default_factory=Flags)

    def as_dict(self) -> dict:
        return {
            "A": self.A, "B": self.B, "C": self.C, "D": self.D,
            "PC": self.PC, "SP": self.SP,
            "MAR": self.MAR, "MDR": self.MDR,
            "IR": self.IR, "CIR": self.CIR,
            "ALU_A": self.ALU_A, "ALU_B": self.ALU_B, "ALU_OUT": self.ALU_OUT,
        }


# ── Bus ────────────────────────────────────────────────────────────────────────

class BusState(Enum):
    IDLE     = "idle"
    FETCH    = "fetch"        # Instruction fetch
    READ     = "mem_read"     # Data read
    WRITE    = "mem_write"    # Data write
    IO_READ  = "io_read"
    IO_WRITE = "io_write"
    DMA      = "dma"
    IRQ      = "irq"

@dataclass
class BusSnapshot:
    state:   BusState
    address: int
    data:    int
    control: str    # "RD", "WR", "INTA", "DMA", etc.
    cycle:   int
    notes:   str = ""


# ── Interrupt system ──────────────────────────────────────────────────────────

class InterruptType(Enum):
    NMI      = "NMI"        # Non-maskable interrupt (hardware fault)
    IRQ0     = "IRQ0"       # Timer tick
    IRQ1     = "IRQ1"       # Keyboard
    IRQ2     = "IRQ2"       # Serial port
    IRQ3     = "IRQ3"       # Disk controller
    SOFTWARE = "SW"         # Software interrupt (syscall)
    DMA_DONE = "DMA_DONE"   # DMA transfer complete

@dataclass
class InterruptEvent:
    itype: InterruptType
    vector: int
    priority: int
    description: str
    cycle_raised: int


# ── Instruction set ───────────────────────────────────────────────────────────

INSTRUCTIONS = {
    0x01: ("LOAD",  "Load value from address into A",       ["addr"]),
    0x02: ("STORE", "Store A to address",                   ["addr"]),
    0x03: ("ADD",   "A = A + operand",                      ["operand"]),
    0x04: ("SUB",   "A = A - operand",                      ["operand"]),
    0x05: ("AND",   "A = A AND operand (bitwise)",          ["operand"]),
    0x06: ("OR",    "A = A OR operand (bitwise)",           ["operand"]),
    0x07: ("XOR",   "A = A XOR operand (bitwise)",          ["operand"]),
    0x08: ("CMP",   "Compare A with operand, set flags",    ["operand"]),
    0x09: ("JMP",   "Unconditional jump to address",        ["addr"]),
    0x0A: ("JZ",    "Jump if Zero flag set",                ["addr"]),
    0x0B: ("JNZ",   "Jump if Zero flag clear",              ["addr"]),
    0x0C: ("PUSH",  "Push A onto stack, SP--",              []),
    0x0D: ("POP",   "Pop from stack into A, SP++",          []),
    0x0E: ("CALL",  "Push PC, jump to subroutine",          ["addr"]),
    0x0F: ("RET",   "Pop PC, return from subroutine",       []),
    0x10: ("IN",    "Read from I/O port into A",            ["port"]),
    0x11: ("OUT",   "Write A to I/O port",                  ["port"]),
    0x12: ("NOP",   "No operation",                         []),
    0xFF: ("HLT",   "Halt the CPU",                         []),
}


# ── Simulation step log ────────────────────────────────────────────────────────

@dataclass
class SimStep:
    phase: str          # "fetch" | "decode" | "execute" | "writeback" | "interrupt" | "dma"
    cycle: int
    description: str
    detail: str
    bus: Optional[BusSnapshot] = None
    reg_snapshot: Optional[dict] = None
    mem_changed: list[tuple[int,int]] = field(default_factory=list)  # [(addr, val)]
    cache_event: str = ""   # "hit" | "miss" | "evict" | ""
    flags_snapshot: Optional[dict] = None


# ── CPU ────────────────────────────────────────────────────────────────────────

class CPU:
    """
    Simulated 8-bit CPU with:
    - Full register set (A, B, C, D, PC, SP, MAR, MDR, IR, FLAGS)
    - Three-bus architecture (data, address, control)
    - Two-level cache (L1 SRAM, L2 SRAM)
    - Interrupt controller (IRQ + NMI)
    - DMA controller
    - Fetch-Decode-Execute-Writeback cycle logging
    """
    def __init__(self):
        self.registers   = Registers()
        self.memory      = MemoryMap()
        self.l1_cache    = Cache("L1 SRAM", latency_cycles=1)
        self.l2_cache    = Cache("L2 SRAM", latency_cycles=4)
        self.cycle       = 0
        self.halted      = False
        self.bus_log: list[BusSnapshot]    = []
        self.irq_queue: list[InterruptEvent] = []
        self.step_log: list[SimStep]       = []
        self.dma_active  = False
        self.dma_src     = 0
        self.dma_dst     = 0
        self.dma_len     = 0

    # ── Internal helpers ────────────────────────────────────────────────────

    def _tick(self, n: int = 1):
        self.cycle += n

    def _bus(self, state: BusState, addr: int, data: int, ctrl: str, notes: str = ""):
        snap = BusSnapshot(state, addr, data, ctrl, self.cycle, notes)
        self.bus_log.append(snap)
        return snap

    def _step(self, phase: str, desc: str, detail: str,
              bus=None, mem_changed=None, cache_event="", flags=None):
        snap = SimStep(
            phase=phase, cycle=self.cycle,
            description=desc, detail=detail,
            bus=bus,
            reg_snapshot=self.registers.as_dict(),
            mem_changed=mem_changed or [],
            cache_event=cache_event,
            flags_snapshot=self.registers.FLAGS.as_dict() if flags else None,
        )
        self.step_log.append(snap)
        return snap

    def _cache_read(self, addr: int) -> tuple[int, str]:
        """Try L1 → L2 → RAM. Returns (value, event_str)."""
        hit, line = self.l1_cache.lookup(addr)
        if hit:
            offset = addr % self.l1_cache.LINE_SIZE
            return line.data[offset], "L1 hit"

        hit2, line2 = self.l2_cache.lookup(addr)
        if hit2:
            offset = addr % self.l2_cache.LINE_SIZE
            val = line2.data[offset]
            # promote to L1
            data = [self.memory.read(addr - (addr % self.l1_cache.LINE_SIZE) + i)
                    for i in range(self.l1_cache.LINE_SIZE)]
            self.l1_cache.load(addr, data)
            self._tick(self.l1_cache.latency + self.l2_cache.latency)
            return val, "L2 hit → L1 fill"

        # RAM fetch
        val = self.memory.read(addr)
        data = [self.memory.read(max(0, addr - addr % self.l1_cache.LINE_SIZE + i))
                for i in range(self.l1_cache.LINE_SIZE)]
        evicted = self.l1_cache.load(addr, data)
        self.l2_cache.load(addr, data)
        self._tick(self.l1_cache.latency + 10)   # RAM latency penalty
        event = "miss → RAM fetch"
        if evicted:
            event += " + eviction"
        return val, event

    # ── ALU ────────────────────────────────────────────────────────────────

    def _alu(self, op: str, a: int, b: int) -> int:
        r = self.registers
        r.ALU_A = a & 0xFF
        r.ALU_B = b & 0xFF
        result = {
            "ADD": a + b,
            "SUB": a - b,
            "AND": a & b,
            "OR":  a | b,
            "XOR": a ^ b,
            "CMP": a - b,
        }.get(op, a)
        r.FLAGS.zero     = (result & 0xFF) == 0
        r.FLAGS.negative = bool(result & 0x80)
        r.FLAGS.carry    = result > 0xFF or result < 0
        r.FLAGS.overflow = ((a ^ result) & (b ^ result) & 0x80) != 0
        r.ALU_OUT = result & 0xFF
        self._tick(1)
        return r.ALU_OUT

    # ── Stack ──────────────────────────────────────────────────────────────

    def _push(self, val: int):
        self.memory.write(self.registers.SP, val & 0xFF)
        self.step_log.append(SimStep(
            phase="execute", cycle=self.cycle,
            description=f"PUSH 0x{val:02X} → [SP=0x{self.registers.SP:02X}]",
            detail=f"Stack pointer decrements. Value 0x{val:02X} written to 0x{self.registers.SP:02X}.",
            reg_snapshot=self.registers.as_dict(),
            mem_changed=[(self.registers.SP, val & 0xFF)],
        ))
        self.registers.SP = (self.registers.SP - 1) & 0xFF

    def _pop(self) -> int:
        self.registers.SP = (self.registers.SP + 1) & 0xFF
        val = self.memory.read(self.registers.SP)
        self.step_log.append(SimStep(
            phase="execute", cycle=self.cycle,
            description=f"POP [SP=0x{self.registers.SP:02X}] → 0x{val:02X}",
            detail=f"Stack pointer increments. Value 0x{val:02X} read from 0x{self.registers.SP:02X}.",
            reg_snapshot=self.registers.as_dict(),
        ))
        return val

    # ── Interrupt handling ─────────────────────────────────────────────────

    def raise_interrupt(self, itype: InterruptType, description: str = ""):
        vectors = {
            InterruptType.NMI:      0x00,
            InterruptType.IRQ0:     0x02,
            InterruptType.IRQ1:     0x04,
            InterruptType.IRQ2:     0x06,
            InterruptType.IRQ3:     0x08,
            InterruptType.SOFTWARE: 0x0A,
            InterruptType.DMA_DONE: 0x0C,
        }
        priorities = {
            InterruptType.NMI: 0,
            InterruptType.IRQ0: 1, InterruptType.IRQ1: 2,
            InterruptType.IRQ2: 3, InterruptType.IRQ3: 4,
            InterruptType.SOFTWARE: 5, InterruptType.DMA_DONE: 6,
        }
        evt = InterruptEvent(itype, vectors.get(itype, 0x00),
                             priorities.get(itype, 9),
                             description or itype.value,
                             self.cycle)
        self.irq_queue.append(evt)
        self.irq_queue.sort(key=lambda e: e.priority)

    def _handle_interrupt(self, evt: InterruptEvent):
        if not self.registers.FLAGS.interrupt and evt.itype != InterruptType.NMI:
            self._step("interrupt",
                       f"IRQ masked: {evt.itype.value}",
                       "Interrupt flag (I) is clear — IRQ ignored by CPU.")
            return
        bus = self._bus(BusState.IRQ, evt.vector, self.registers.PC, "INTA",
                        f"{evt.itype.value} acknowledged")
        self._step("interrupt",
                   f"Interrupt: {evt.itype.value}",
                   f"CPU acknowledges {evt.description}. Pushing PC=0x{self.registers.PC:04X} to stack. "
                   f"Loading vector 0x{evt.vector:02X} from IVT. Jumping to handler.",
                   bus=bus)
        self._push(self.registers.PC & 0xFF)
        self._push((self.registers.PC >> 8) & 0xFF)
        self.registers.FLAGS.interrupt = False
        self.registers.PC = self.memory.read(evt.vector)
        self._tick(6)

    # ── DMA ────────────────────────────────────────────────────────────────

    def dma_transfer(self, src: int, dst: int, length: int):
        """Simulate DMA block transfer, pausing CPU (bus hold)."""
        self.dma_active = True
        steps_before = len(self.step_log)
        bus = self._bus(BusState.DMA, src, 0, "HOLD", f"DMA: 0x{src:02X}→0x{dst:02X} × {length}")
        self._step("dma",
                   f"DMA Transfer: 0x{src:02X} → 0x{dst:02X}, {length} bytes",
                   f"DMA controller asserts HOLD. CPU suspends bus access (HLDA). "
                   f"DMA autonomously transfers {length} bytes from 0x{src:02X} to 0x{dst:02X} "
                   f"without CPU involvement — saving {length * 4} CPU cycles.",
                   bus=bus)
        changed = []
        for i in range(length):
            s, d = (src + i) & 0xFF, (dst + i) & 0xFF
            val = self.memory.read(s)
            self.memory.write(d, val)
            changed.append((d, val))
            self._tick(2)
        self._step("dma",
                   "DMA Complete — bus released to CPU",
                   f"Transfer done. DMA raises DMA_DONE interrupt. CPU resumes (HLDA released).",
                   mem_changed=changed)
        self.raise_interrupt(InterruptType.DMA_DONE, "DMA block transfer complete")
        self.dma_active = False

    # ── Fetch-Decode-Execute-Writeback ─────────────────────────────────────

    def _fetch(self) -> int:
        """Fetch opcode at PC. Returns opcode byte."""
        r = self.registers
        r.MAR = r.PC
        bus = self._bus(BusState.FETCH, r.MAR, 0, "RD",
                        f"Fetch opcode at 0x{r.MAR:04X}")
        self._step("fetch",
                   f"FETCH — address bus: 0x{r.MAR:04X}",
                   f"MAR ← PC (0x{r.MAR:04X}). "
                   f"Address placed on address bus. Control bus asserts RD. "
                   f"Waiting for memory response…",
                   bus=bus)
        self._tick(1)

        val, cache_event = self._cache_read(r.MAR)
        r.MDR = val
        r.IR  = val
        r.PC  = (r.PC + 1) & 0xFFFF
        bus2 = self._bus(BusState.FETCH, r.MAR, r.MDR, "RD",
                         f"Opcode 0x{r.MDR:02X} on data bus")
        self._step("fetch",
                   f"FETCH complete — opcode 0x{r.MDR:02X} received",
                   f"MDR ← 0x{r.MDR:02X} ({cache_event}). IR ← 0x{r.IR:02X}. PC advances to 0x{r.PC:04X}.",
                   bus=bus2, cache_event=cache_event)
        self._tick(1)
        return r.IR

    def _fetch_operand(self) -> int:
        r = self.registers
        r.MAR = r.PC
        val, cache_event = self._cache_read(r.MAR)
        r.MDR = val
        r.PC  = (r.PC + 1) & 0xFFFF
        bus = self._bus(BusState.READ, r.MAR, r.MDR, "RD", "Fetch operand")
        self._step("fetch",
                   f"FETCH operand — 0x{r.MDR:02X} from 0x{r.MAR:04X}",
                   f"Second memory cycle: operand 0x{val:02X} fetched ({cache_event}). PC → 0x{r.PC:04X}.",
                   bus=bus, cache_event=cache_event)
        self._tick(1)
        return r.MDR

    def _decode(self, opcode: int) -> tuple[str, str, list[str]]:
        mnemonic, desc, operands = INSTRUCTIONS.get(opcode, ("???", "Unknown opcode", []))
        self.registers.CIR = mnemonic
        self._step("decode",
                   f"DECODE — 0x{opcode:02X} → {mnemonic}",
                   f"Instruction decoder identifies opcode 0x{opcode:02X} as '{mnemonic}'. "
                   f"{desc}. Operands needed: {len(operands)}. "
                   f"Control unit generates microoperations.",
                   flags=True)
        self._tick(1)
        return mnemonic, desc, operands

    def execute_instruction(self, opcode: int):
        """Execute one full fetch-decode-execute-writeback cycle."""
        r = self.registers
        mnemonic, desc, operand_names = self._decode(opcode)
        operand = self._fetch_operand() if operand_names else None
        result_addr = None
        result_val  = None

        if mnemonic == "LOAD":
            r.MAR = operand
            val, cache_event = self._cache_read(r.MAR)
            r.MDR = val
            r.ALU_A = val
            r.A = val
            bus = self._bus(BusState.READ, r.MAR, r.MDR, "RD")
            self._step("execute",
                       f"EXECUTE LOAD — A ← [0x{r.MAR:02X}] = 0x{val:02X}",
                       f"MAR = 0x{r.MAR:02X}. Memory read ({cache_event}). "
                       f"MDR = 0x{val:02X}. Accumulator A ← 0x{val:02X}.",
                       bus=bus, cache_event=cache_event, flags=True)

        elif mnemonic == "STORE":
            r.MAR = operand
            r.MDR = r.A
            self.memory.write(r.MAR, r.MDR)
            bus = self._bus(BusState.WRITE, r.MAR, r.MDR, "WR")
            self._step("execute",
                       f"EXECUTE STORE — [0x{r.MAR:02X}] ← A (0x{r.A:02X})",
                       f"MAR = 0x{r.MAR:02X}. MDR = A = 0x{r.A:02X}. "
                       f"Write cycle: data bus carries 0x{r.MDR:02X}, WR asserted.",
                       bus=bus, mem_changed=[(r.MAR, r.MDR)])
            result_addr, result_val = r.MAR, r.MDR

        elif mnemonic in ("ADD","SUB","AND","OR","XOR"):
            old_a = r.A
            r.A = self._alu(mnemonic, r.A, operand)
            self._step("execute",
                       f"EXECUTE {mnemonic} — A: 0x{old_a:02X} {mnemonic} 0x{operand:02X} = 0x{r.A:02X}",
                       f"ALU performs {mnemonic}. Inputs: A=0x{old_a:02X}, operand=0x{operand:02X}. "
                       f"Result: 0x{r.A:02X}. Flags updated: Z={r.FLAGS.zero} C={r.FLAGS.carry} N={r.FLAGS.negative}.",
                       flags=True)

        elif mnemonic == "CMP":
            self._alu("CMP", r.A, operand)
            self._step("execute",
                       f"EXECUTE CMP — A(0x{r.A:02X}) vs 0x{operand:02X}",
                       f"ALU subtracts without storing result. Only flags updated: "
                       f"Z={r.FLAGS.zero} C={r.FLAGS.carry} N={r.FLAGS.negative}.",
                       flags=True)

        elif mnemonic == "JMP":
            old_pc = r.PC
            r.PC = operand
            self._step("execute",
                       f"EXECUTE JMP → 0x{operand:02X}",
                       f"PC overwritten: 0x{old_pc:04X} → 0x{operand:02X}. "
                       f"Next fetch will come from 0x{operand:02X}.")

        elif mnemonic == "JZ":
            if r.FLAGS.zero:
                r.PC = operand
                self._step("execute", f"EXECUTE JZ → TAKEN (Z=1)",
                           f"Zero flag is set. PC ← 0x{operand:02X}.")
            else:
                self._step("execute", f"EXECUTE JZ → NOT TAKEN (Z=0)",
                           f"Zero flag is clear. PC stays at 0x{r.PC:04X}.")

        elif mnemonic == "JNZ":
            if not r.FLAGS.zero:
                r.PC = operand
                self._step("execute", f"EXECUTE JNZ → TAKEN (Z=0)",
                           f"Zero flag is clear. PC ← 0x{operand:02X}.")
            else:
                self._step("execute", f"EXECUTE JNZ → NOT TAKEN (Z=1)",
                           f"Zero flag is set. PC stays at 0x{r.PC:04X}.")

        elif mnemonic == "PUSH":
            self._push(r.A)
            self._step("execute", f"EXECUTE PUSH A (0x{r.A:02X})",
                       f"A pushed to stack. SP was 0x{(r.SP+1)&0xFF:02X}, now 0x{r.SP:02X}.")

        elif mnemonic == "POP":
            r.A = self._pop()
            self._step("execute", f"EXECUTE POP → A = 0x{r.A:02X}",
                       f"Popped 0x{r.A:02X} from stack. SP was 0x{(r.SP-1)&0xFF:02X}, now 0x{r.SP:02X}.")

        elif mnemonic == "CALL":
            self._push(r.PC & 0xFF)
            self._push((r.PC >> 8) & 0xFF)
            r.PC = operand
            self._step("execute", f"EXECUTE CALL 0x{operand:02X}",
                       f"Return address pushed to stack. PC ← 0x{operand:02X}.")

        elif mnemonic == "RET":
            hi = self._pop()
            lo = self._pop()
            r.PC = ((hi << 8) | lo) & 0xFFFF
            self._step("execute", f"EXECUTE RET → PC = 0x{r.PC:04X}",
                       f"Return address popped. PC ← 0x{r.PC:04X}.")

        elif mnemonic == "IN":
            port = operand
            io_addr = 0xD0 + (port & 0x0F)
            val = self.memory.read(io_addr)
            r.A = val
            bus = self._bus(BusState.IO_READ, port, val, "IOR",
                            f"Read I/O port {port}")
            self._step("execute", f"EXECUTE IN port {port} → A = 0x{val:02X}",
                       f"I/O read cycle. Port {port} mapped to 0x{io_addr:02X}. "
                       f"Data bus: 0x{val:02X}. A ← 0x{val:02X}.", bus=bus)

        elif mnemonic == "OUT":
            port = operand
            io_addr = 0xD0 + (port & 0x0F)
            self.memory.write(io_addr, r.A)
            bus = self._bus(BusState.IO_WRITE, port, r.A, "IOW",
                            f"Write I/O port {port}")
            self._step("execute", f"EXECUTE OUT A(0x{r.A:02X}) → port {port}",
                       f"I/O write cycle. Port {port} mapped to 0x{io_addr:02X}. "
                       f"A = 0x{r.A:02X} placed on data bus. IOW asserted.",
                       bus=bus, mem_changed=[(io_addr, r.A)])

        elif mnemonic == "NOP":
            self._step("execute", "EXECUTE NOP", "No operation performed. PC already advanced.")
            self._tick(1)

        elif mnemonic == "HLT":
            self.halted = True
            self._step("execute", "EXECUTE HLT — CPU halted",
                       "CPU enters halt state. Clock cycles continue but no fetch occurs. "
                       "Only an NMI or RESET can resume execution.")
            return

        # Writeback phase
        self._step("writeback",
                   f"WRITEBACK — {mnemonic} complete",
                   f"Results committed. Any pending register writes finalised. "
                   f"Interrupt check: {len(self.irq_queue)} pending. "
                   f"Next fetch at PC = 0x{r.PC:04X}.")
        self._tick(1)

        # Service pending interrupts
        if self.irq_queue:
            evt = self.irq_queue.pop(0)
            self._handle_interrupt(evt)

    def run_program(self, program: list[int], load_addr: int = 0x70) -> list[SimStep]:
        """Load and run a program, return full step log."""
        self.step_log = []
        self.bus_log  = []
        # Load into code segment
        for i, byte in enumerate(program):
            if load_addr + i < 256:
                self.memory.write(load_addr + i, byte)
        self.registers.PC = load_addr

        self._step("fetch",
                   "CPU RESET — starting execution",
                   f"Program loaded at 0x{load_addr:02X}. "
                   f"PC = 0x{load_addr:02X}. SP = 0x{self.registers.SP:02X}. "
                   f"All registers cleared. Interrupt flag enabled.")

        max_cycles = 200
        while not self.halted and self.cycle < max_cycles:
            if self.irq_queue and self.registers.FLAGS.interrupt:
                evt = self.irq_queue.pop(0)
                self._handle_interrupt(evt)
            opcode = self._fetch()
            if opcode == 0xFF:
                self.execute_instruction(opcode)
                break
            self.execute_instruction(opcode)

        return self.step_log


# ── Convenience: process user input ───────────────────────────────────────────

def process_input(raw: str, mode: str) -> tuple[CPU, list[SimStep]]:
    """
    Build a small program based on user input, run it, return (cpu, steps).
    mode: 'key' | 'int' | 'str'
    """
    cpu = CPU()

    if mode == "key":
        char = raw[0] if raw else 'A'
        val  = ord(char) & 0xFF
        # Program: IN port0, STORE result, ADD 1 (increment), STORE, HLT
        prog = [0x10, 0x00,           # IN port 0
                0x02, 0xA0,           # STORE [0xA0]
                0x03, 0x01,           # ADD 1
                0x02, 0xA1,           # STORE [0xA1] (val+1)
                0x11, 0x00,           # OUT port 0
                0xFF]                 # HLT
        cpu.memory.write(0xD0, val)   # pre-load I/O port 0 with keycode
        cpu.raise_interrupt(InterruptType.IRQ1, f"Keyboard: '{char}' (ASCII {val})")

    elif mode == "int":
        n   = max(0, min(255, int(raw) if raw.lstrip('-').isdigit() else 0))
        val = n & 0xFF
        prog = [0x01, 0xD0,           # LOAD [0xD0]  (I/O register)
                0x03, 0x10,           # ADD 0x10
                0x08, val,            # CMP val
                0x0A, 0x7E,           # JZ  done
                0x02, 0xA0,           # STORE [0xA0]
                0x09, 0x70,           # JMP  start (loop back — unrolled for demo)
                0xFF]                 # HLT (0x7E relative)
        cpu.memory.write(0xD0, val)

    else:  # str
        chars = [ord(c) & 0xFF for c in raw[:8]]
        # Program: load each char, store to data segment
        prog = []
        for i, c in enumerate(chars):
            prog += [0x01, 0xD0 + i,   # LOAD [I/O+i]
                     0x02, 0xA0 + i]   # STORE [0xA0+i]
            cpu.memory.write(0xD0 + i, c)
        prog += [0x11, 0x00, 0xFF]     # OUT port 0, HLT

    # Schedule a timer IRQ mid-execution
    cpu.raise_interrupt(InterruptType.IRQ0, "Timer tick (1ms interval)")

    steps = cpu.run_program(prog)
    return cpu, steps
