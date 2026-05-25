# Computer System Fundamentals — Interactive Simulator

An interactive app for learning computer architecture from the ground up, with a difficulty slider (Beginner → Advanced).

## Modules

| Module | Topics covered |
|---|---|
| Number Systems | Binary, hex, octal, ASCII, two's complement, IEEE-754, colour codes, quiz |

## Running locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Try on fly.io
Open this link to see the current version:
https://computer-systems-sim.fly.dev/

## Project structure

```
cpu_sim/
├── app.py                  # Main entry point & sidebar navigation
├── requirements.txt
├── core/
│   ├── cpu.py              # CPU simulation engine (registers, ALU, cache, buses, DMA, IRQ)
│   └── reference.py        # Number system utils, memory/cache/bus reference data
└── pages/
    ├── numbers.py          # Number systems
```

## Proosed architecture of the simulation engine

- **Registers**: A, B, C, D (8-bit GP), PC, SP (16-bit), MAR, MDR, IR, CIR (internal), ALU_A/B/OUT
- **Flags**: Zero, Carry, Negative, Overflow, Interrupt-enable
- **Memory**: 256-byte flat address space with typed regions (ROM, Flash, Stack, Heap, Code, Data, I/O, DMA, Video)
- **Cache**: 2-level (L1 + L2), 4-way set-associative, LRU eviction, hit/miss/eviction tracking
- **Buses**: Address, Data, Control — full transaction log with state, address, data, control signals
- **Interrupts**: NMI, IRQ0–IRQ3, Software, DMA_DONE — prioritised queue, IVT lookup, context save/restore
- **DMA**: Source/destination/length programming, HOLD/HLDA handshake, scatter-gather, DMA_DONE IRQ
- **Instruction set**: 19 instructions (LOAD, STORE, ADD, SUB, AND, OR, XOR, CMP, JMP, JZ, JNZ, PUSH, POP, CALL, RET, IN, OUT, NOP, HLT)
- **Step log**: Every micro-operation logged with phase, cycle count, register snapshot, bus snapshot, memory writes, cache event, flags
