# Guide to cpu.py — Computer System Simulation Engine

## What this script does

This script is a simulation of how a simple 8-bit computer works at the hardware level. It models a CPU, a two-level memory cache, a flat 256-byte address space, an interrupt system, and a DMA controller. Every major step the CPU takes — fetching an instruction, waiting for memory, handling an interrupt — is recorded in a detailed log so you can trace exactly what the hardware is doing and why.

The simulation is not meant to run real software or compete with actual hardware. Its purpose is to make the internal mechanics of a CPU visible and understandable. It is well suited as a base for a visualiser, or a reference for studying computer architecture concepts.


## How the memory system is organised

The entire memory space is 256 bytes, addressed from 0x00 to 0xFF. Rather than a plain array of bytes, this space is divided into named regions that mirror how a real computer assigns meaning to different parts of memory.

Addresses 0x00 to 0x0F hold the Interrupt Vector Table, which is read-only ROM. This table contains eight 16-bit entries, each pointing to the address of an interrupt handler routine. Addresses 0x10 to 0x1F contain BIOS/firmware code stored in Flash memory, pre-loaded with placeholder NOP instructions and a generic interrupt service routine stub at 0x1E and 0x1F.

The stack lives at 0x20 to 0x3F and grows downward: the stack pointer starts at 0x3F and decrements as values are pushed onto it. The heap (0x40–0x6F) is the region for dynamically allocated data, and the program code segment (0x70–0x9F) is where programs are loaded before execution — the program counter starts pointing here. The data segment (0xA0–0xCF) holds global and static variables.

Addresses 0xD0 to 0xD7 are memory-mapped input ports. When the CPU executes an IN instruction to read from a port, it is actually reading from one of these addresses. Port 0 corresponds to a simulated keyboard input. Output ports live at 0xD8 to 0xDF, where port 0 drives a simulated display character and port 1 controls a status LED. Addresses 0xE0 to 0xEF serve as the DMA transfer buffer, and 0xF0 to 0xFF are the video/display buffer.

Each individual byte in memory is represented by a MemoryCell object, which tracks whether it is writable, what memory technology it belongs to (SRAM, DRAM, ROM, FLASH, and so on), and how many times it has been accessed. Writing to a read-only cell raises a PermissionError, and all values are enforced to 8-bit range using a bitwise mask.


## The cache hierarchy

The CPU does not read directly from main RAM. Instead it first checks a two-level cache system, which is where the most realistic simulation of memory latency comes from.

L1 cache (labelled "L1 SRAM") has a latency of 1 cycle. If the data is here, it is returned almost immediately. L2 cache ("L2 SRAM") has a latency of 4 cycles. If the data is only in L2, it is promoted to L1 before being returned, incurring the combined latency of both levels. If the data is in neither cache, the CPU must fetch it directly from RAM, which costs roughly 11 cycles, after which the data is loaded into both L1 and L2 for future use.

The cache is 4-way set-associative with 4 sets and 4 bytes per cache line. When all four ways of a set are occupied and new data needs to be loaded, the least recently used line is evicted to make room. The cache tracks hit and miss counts, so after a simulation run you can calculate the hit rate by inspecting cpu.l1_cache.hit_rate.

All of this latency — cache misses, cache fills, RAM fetches — shows up in the step log as clearly labelled stall cycles, which is one of the most educational aspects of the script.


## CPU registers

The CPU has four general-purpose 8-bit registers: A (the accumulator, which is the primary register for arithmetic and I/O), B, C, and D. The program counter (PC) and stack pointer (SP) are 16-bit, though in this 256-byte address space they effectively behave as 8-bit values in practice.

There are also several internal registers that would be invisible to a programmer on real hardware but are exposed here for educational purposes. MAR (Memory Address Register) holds the address currently being sent to memory. MDR (Memory Data Register) holds the data being transferred to or from memory. IR (Instruction Register) holds the opcode byte currently being processed. CIR (Current Instruction Register) holds the decoded mnemonic string for that opcode.

The ALU has its own internal registers — ALU_A, ALU_B, and ALU_OUT — which show the inputs and output of each arithmetic or logical operation.

The FLAGS register contains five status bits: Z (zero, set when a result is zero), C (carry, set on arithmetic overflow or borrow), N (negative, set when the high bit of the result is 1), V (overflow, set on signed integer overflow), and I (interrupt enable, controlling whether hardware interrupts are accepted).


## The instruction set

The CPU understands 19 instructions, each identified by a single opcode byte. Instructions that need a parameter (such as an address or an immediate value) are followed immediately by a second byte in memory. The full set is defined in the INSTRUCTIONS dictionary at module level and covers the following operations.

LOAD (0x01) reads a value from a given memory address into the accumulator A. STORE (0x02) writes the accumulator's current value to a given address. ADD (0x03), SUB (0x04), AND (0x05), OR (0x06), and XOR (0x07) each take a single operand byte and apply the corresponding arithmetic or bitwise operation to A, updating the flags register with the result. CMP (0x08) subtracts the operand from A without storing the result, purely to update the flags — useful before conditional jumps.

JMP (0x09) performs an unconditional jump to an address by overwriting the program counter. JZ (0x0A) jumps only if the zero flag is set, and JNZ (0x0B) jumps only if it is clear, allowing simple conditional branching.

PUSH (0x0C) writes the accumulator to the current stack address and decrements SP. POP (0x0D) increments SP and reads the value back into A. CALL (0x0E) saves the return address on the stack before jumping to a subroutine address. RET (0x0F) pops that return address and restores the program counter.

IN (0x10) reads from a memory-mapped I/O input port into A. OUT (0x11) writes A to a memory-mapped output port. NOP (0x12) does nothing for one cycle. HLT (0xFF) stops the CPU; only an NMI or RESET can restart it.


## The fetch-decode-execute cycle

Each instruction goes through four distinct phases, each of which generates one or more entries in the step log.

During the fetch phase, the CPU places the program counter's value into MAR, asserts the read (RD) signal on the control bus, and waits for memory to return the byte at that address. The cache hierarchy is consulted and stall cycles are added if needed. When the byte arrives, it is stored in MDR and IR, and the program counter advances by one.

During the decode phase, the opcode in IR is looked up in the INSTRUCTIONS table. The CPU identifies the mnemonic, notes how many operand bytes are required, and generates the microoperation signals for the relevant functional units. If an operand is needed, a second fetch cycle retrieves it from the next byte in memory.

During the execute phase, the identified operation is carried out. For arithmetic instructions this means running the ALU. For memory instructions it means performing a read or write. For jump instructions it means overwriting the program counter. I/O instructions read from or write to the memory-mapped port addresses. The execute phase for stack operations (PUSH, POP, CALL, RET) internally calls helper methods that also generate their own step log entries.

The writeback phase is a brief final step that confirms any pending register updates are committed and checks whether there are any interrupts waiting to be serviced.


## Interrupts

The interrupt system models both maskable hardware interrupts and non-maskable interrupts. Seven interrupt types are defined: NMI (non-maskable, highest priority), four hardware IRQ lines (IRQ0 for timer, IRQ1 for keyboard, IRQ2 for serial port, IRQ3 for disk controller), a software interrupt, and a DMA completion signal.

When an interrupt is raised via raise_interrupt, it is added to the irq_queue and the queue is sorted by priority so that NMI is always handled first. Between instructions, if the interrupt flag is enabled and the queue is not empty, the CPU calls _handle_interrupt.

Handling an interrupt involves three steps: the CPU asserts INTA (Interrupt Acknowledge) on the control bus and saves the current program counter to the stack; it then looks up the appropriate handler address from the Interrupt Vector Table at the start of memory; and finally it loads that address into the program counter and clears the interrupt flag to prevent nested interrupts. The entire sequence stalls the CPU for several cycles and all of this overhead is logged. After the handler is finished (by executing a RET), the program counter is restored from the stack and normal execution resumes.


## DMA transfers

The dma_transfer method simulates a Direct Memory Access controller, which can copy a block of bytes from one memory address to another without involving the CPU in each individual byte move.

When a DMA transfer begins, the DMA controller asserts a HOLD signal, suspending the CPU's access to the bus (the CPU enters the HLDA — Hold Acknowledge — state). The controller then moves each byte one at a time, with a 2-cycle cost per byte, generating stall log entries for each. When the transfer is complete, the DMA controller releases the bus and raises a DMA_DONE interrupt to notify the CPU that it can resume.

This is significantly faster than having the CPU perform the equivalent number of LOAD and STORE instructions, and the step log makes this saving visible.


## The process_input function

The process_input function at the bottom of the file is a convenience entry point that builds and runs a small demonstration program based on some input text. It takes a raw string and a mode parameter.

In 'key' mode, it treats the first character of the input as a simulated keypress, raises a keyboard interrupt, then runs a short program that reads from I/O port 0 (where the keycode was pre-loaded), stores the value to the data segment, increments it by 1, stores the incremented value, and sends it back out on port 0 before halting.

In 'int' mode, it clamps the input to a value between 0 and 255, loads it from an I/O register into the accumulator, stores it, adds 1, stores the result, outputs it to port 6, and halts.

In 'str' mode (the default for anything else), it handles up to 16 characters. For each character it generates a LOAD from the appropriate I/O address and a STORE into the data segment, pre-loads each I/O port with the character's ASCII value, and ends with an OUT and a HLT.

All three modes call run_program with timer_irq=True, which means a timer interrupt (IRQ0) is automatically scheduled after the second instruction executes, demonstrating interrupt handling mid-program.


## How to use the simulation

The simplest way to run a simulation is to call process_input directly:

    cpu, steps = process_input("Hello", "str")

After the call, cpu is the CPU object in its final state and steps is the full list of SimStep objects. You can inspect the final register values with cpu.registers.as_dict(), the cache statistics with cpu.l1_cache.hits and cpu.l1_cache.misses, and the memory contents by reading from cpu.memory.

To trace what happened step by step, iterate over the steps list:

    for step in steps:
        print(step.cycle, step.phase, step.description)
        print("   ", step.detail)

Each SimStep also carries reg_snapshot (a dictionary snapshot of all register values at that point), flags_snapshot (the flag register state, when relevant), mem_changed (a list of addresses and values that were written during that step), cache_event (a string like "L1 hit", "L2 hit → L1 fill", or "miss → RAM fetch"), and an optional reference to the bus state at that cycle.

You can also write and load your own programs by constructing a list of opcode bytes and calling cpu.run_program directly:

    cpu = CPU()
    program = [
        0x03, 0x05,   # ADD 5  (A = A + 5)
        0x03, 0x03,   # ADD 3  (A = A + 8)
        0x02, 0xA0,   # STORE [0xA0]
        0xFF          # HLT
    ]
    steps = cpu.run_program(program)

This loads the program into the code segment starting at address 0x70 and begins execution from there. The 200-cycle cap in run_program prevents infinite loops from running forever.


## Extending the simulation

The design is fairly modular. To add new instructions, add an entry to the INSTRUCTIONS dictionary with a new opcode, mnemonic, description, and operand list, and then add a corresponding elif branch in the execute_instruction method. The logging infrastructure will pick it up automatically.

To extend the cache, adjust the Cache class constants (SETS, WAYS, LINE_SIZE) or add a third cache level by extending the _cache_read method to check an L3 before going to RAM. To add more interrupt types, add members to the InterruptType enum, assign them vectors and priorities in the raise_interrupt method, and optionally pre-populate the IVT entries in MemoryMap._setup_regions.

The step log format is rich enough that building a visual step-through interface on top of this script would be straightforward — each SimStep already contains everything needed to render a register panel, bus activity indicator, memory view, and cache status at each clock cycle.
