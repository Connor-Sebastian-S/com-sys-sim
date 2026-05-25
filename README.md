# Computer System Fundamentals — Interactive Simulator

An interactive app for learning computer architecture from the ground up, with a difficulty slider (Beginner → Advanced).

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

## Coverage

| Unit topic | Coverage |
|---|---|
|CPU architecture (ALU, registers, control unit, fetch‑execute cycle) |	fde.py – detailed 5‑stage FDE + interactive animation |
|Buses (address, data, control) | buses.py – bus transactions, width/bandwidth, arbitration
|Memory hierarchy & types (SRAM, DRAM, ROM, EPROM, EEPROM, Flash, virtual) |	memory_types.py – hierarchy visual, deep‑dive cards, memory map |
|Storage (HDD, SSD, NVMe, tape) | memory_types.py – hierarchy includes HDD/SSD/NVMe, speed comparison |
|Number systems (binary, decimal, hex) & conversions | alu.py – universal converter, bit breakdown, nibbles
Two’s complement, signed/unsigned |	alu.py – two’s complement explanation |
|Arithmetic in non‑decimal (addition, subtraction) | alu.py – 8‑bit ripple‑carry adder, binary operations |
|Logic operations (AND, OR, NOT, XOR) |	alu.py – ALU ops, truth tables, interactive gates |
|ASCII / Unicode / string encoding | encoding.py – character inspector, UTF‑8/16, code points |
|IEEE‑754 floating point | encoding.py – 32‑bit layout, 0.1+0.2 example |
|Assembly / machine code / instruction set | assembly.py – full ISA, runnable examples, custom programs |
|Interrupts & DMA | buses.py – INTA cycle, DMA HOLD/HLDA walkthrough |
|Stack, heap, virtual memory | memory_types.py – virtual memory page fault, stack/heap mentioned (though not deeply) |
