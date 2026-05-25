"""Stack & Heap Memory page."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import streamlit as st
import pandas as pd


def render():
    st.title("Stack & Heap Memory")
    level = st.session_state.get("level","Intermediate")

    st.info("**Stack** = a tidy pile of trays in a cafeteria. Last one on = first one off (LIFO). "
                "The computer uses it for function calls.\n\n"
                "**Heap** = a messy storeroom where you can put things anywhere, label them, and come back later. "
                "Your program uses it for data that needs to last a long time.")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Stack")
        st.markdown("""
- **LIFO** (Last In, First Out)
- Fixed size, determined at program start
- Managed **automatically** by the CPU (SP register)
- Stores: local variables, return addresses, saved registers
- Direction: grows **downward** (high → low addresses)
- Speed: **very fast** (SP is just a register)
- Overflow → **stack overflow** (crash)
""")
    with col2:
        st.markdown("### Heap")
        st.markdown("""
- **Dynamic** — any size, any order
- Managed by your **program** (malloc/free, new/delete)
- Stores: objects, arrays, data with variable lifetime
- Direction: grows **upward** (low → high addresses)
- Speed: **slower** (needs allocator bookkeeping)
- Leak → **memory leak** (wasted RAM never freed)
""")

    # Interactive stack simulator
    st.divider()
    st.markdown("## Interactive Stack Simulator")
    st.caption("Simulate PUSH and POP operations. Watch the stack pointer move and memory fill.")

    if "stack_mem" not in st.session_state:
        st.session_state["stack_mem"] = [None] * 16   # 16 slots, 0=top
        st.session_state["sp"]        = 15             # starts at bottom
        st.session_state["stack_log"] = []

    def draw_stack():
        rows = []
        for i in range(15, -1, -1):
            addr = 0x20 + i
            val  = st.session_state["stack_mem"][i]
            is_sp = (i == st.session_state["sp"] + 1 and val is not None) or \
                    (st.session_state["sp"] == 15 and i == 15 and val is None)
            sp_mark = "← SP" if i == (st.session_state["sp"]) else ""
            rows.append({
                "Address": f"0x{addr:02X}",
                "Value": f"0x{val:02X} ({val})" if val is not None else "— (empty)",
                "SP": sp_mark,
            })
        df = pd.DataFrame(rows)
        def style_row(row):
            if row["SP"]:
                return ["background-color:#fff3cd"]*3
            if "empty" not in row["Value"]:
                return ["background-color:#d1e7dd"]*3
            return [""]*3
        st.dataframe(df.style.apply(style_row,axis=1), hide_index=True, use_container_width=True)

    sc1,sc2,sc3 = st.columns([2,1,1])
    with sc1:
        push_val = st.number_input("Value to push (0–255)", 0, 255, 72, step=1)
    with sc2:
        st.markdown("<br>",unsafe_allow_html=True)
        if st.button("PUSH ↓", use_container_width=True):
            sp = st.session_state["sp"]
            if sp >= 0:
                st.session_state["stack_mem"][sp] = int(push_val)
                st.session_state["stack_log"].insert(0, f"PUSH 0x{int(push_val):02X} → [0x{0x20+sp:02X}]  SP: 0x{0x20+sp+1:02X}→0x{0x20+sp:02X}")
                st.session_state["sp"] -= 1
            else:
                st.error("Stack overflow! No more space.")
    with sc3:
        st.markdown("<br>",unsafe_allow_html=True)
        if st.button("POP ↑", use_container_width=True):
            sp = st.session_state["sp"]
            if sp < 15:
                popped = st.session_state["stack_mem"][sp+1]
                st.session_state["stack_mem"][sp+1] = None
                st.session_state["sp"] += 1
                st.session_state["stack_log"].insert(0, f"POP  0x{popped:02X} ← [0x{0x20+sp+1:02X}]  SP: 0x{0x20+sp:02X}→0x{0x20+sp+1:02X}")
            else:
                st.warning("Stack is empty.")

    sp_disp = st.session_state["sp"]
    st.metric("Stack Pointer (SP)", f"0x{0x20+sp_disp:02X}",
              delta=f"{15-sp_disp} items on stack")
    draw_stack()

    if st.session_state["stack_log"]:
        st.markdown("**Operation log:**")
        for entry in st.session_state["stack_log"][:8]:
            st.code(entry, language="text")

    if st.button("Reset stack"):
        st.session_state["stack_mem"] = [None]*16
        st.session_state["sp"] = 15
        st.session_state["stack_log"] = []
        st.rerun()

    # Function call walkthrough
    st.divider()
    st.markdown("## How a Function Call Uses the Stack")
    st.markdown("""
When `main()` calls `add(3, 5)`:

```
[High address]
0x3F  main's local variables
0x3E  saved register A
0x3D  argument 2: 5            ← pushed by caller
0x3C  argument 1: 3            ← pushed by caller
0x3B  return address (0x0075)  ← pushed by CALL instruction
0x3A  add()'s local variables  ← pushed by add() itself
       ↑ SP points here during add()
[Low address]
```

When `add()` executes `RET`:
1. Pop return address `0x0075` from stack into PC
2. SP increments back to where main's frame starts
3. Execution resumes in `main()` at `0x0075`

This is why recursion crashes with **stack overflow** — each recursive call pushes a new frame,
and if recursion is too deep, SP hits the heap or zero.
""")

    # Heap simulation
    st.divider()
    st.markdown("## Heap Memory & Dynamic Allocation")
    if level == "Beginner":
        st.markdown("Unlike the stack, **heap memory must be managed manually** (in C/C++) or by a garbage collector (Python, Java).")

    if "heap_blocks" not in st.session_state:
        st.session_state["heap_blocks"] = {}  # addr → (size, label, freed)
        st.session_state["heap_next"]   = 0x40

    hc1,hc2,hc3 = st.columns(3)
    with hc1: alloc_size  = st.number_input("Allocate bytes", 1, 32, 8, step=1)
    with hc2: alloc_label = st.text_input("Label (variable name)", "myArray")
    with hc3:
        st.markdown("<br>",unsafe_allow_html=True)
        if st.button("malloc()", use_container_width=True):
            addr = st.session_state["heap_next"]
            st.session_state["heap_blocks"][addr] = (int(alloc_size), alloc_label, False)
            st.session_state["heap_next"] += int(alloc_size)

    # Free a block
    active = {addr:(sz,lbl,fr) for addr,(sz,lbl,fr) in st.session_state["heap_blocks"].items() if not fr}
    if active:
        free_addr = st.selectbox("Select block to free()",
                                  [f"0x{a:02X}: {lbl} ({sz}B)" for a,(sz,lbl,_) in active.items()])
        if st.button("free()"):
            selected_addr = int(free_addr.split(":")[0], 16)
            sz,lbl,_ = st.session_state["heap_blocks"][selected_addr]
            st.session_state["heap_blocks"][selected_addr] = (sz, lbl, True)

    # Draw heap
    heap_rows = []
    for addr,(sz,lbl,freed) in sorted(st.session_state["heap_blocks"].items()):
        heap_rows.append({
            "Address": f"0x{addr:02X}–0x{addr+sz-1:02X}",
            "Size (bytes)": sz,
            "Label": lbl,
            "Status": "Allocated" if not freed else "Freed (memory leak if not reused)",
        })
    if heap_rows:
        df = pd.DataFrame(heap_rows)
        def style_heap(row):
            return ["background-color:#d1e7dd"]*len(row) if "Allocated" in row["Status"] else ["background-color:#f8d7da"]*len(row)
        st.dataframe(df.style.apply(style_heap,axis=1), hide_index=True, use_container_width=True)

    if level in ("Intermediate","Advanced"):
        st.divider()
        st.markdown("## Memory Layout of a Running Process")
        st.markdown("""
```
High addresses ──────────────────────────────
  0xFFFF   Kernel / OS space (protected)
           ────────────────────────────────
  0xBFFF   Environment variables, argv
           Stack (grows ↓)
           │
           ▼
           [unmapped — crash if collision]
           ▲
           │
           Heap (grows ↑)
  0x0804   BSS  (uninitialised global data)
  0x0603   Data segment (initialised globals)
  0x0401   Text segment (program code — read-only)
Low addresses ───────────────────────────────
```
""")

    if level == "Advanced":
        st.markdown("## Stack vs Heap: Allocation Internals")
        st.markdown("""
**Stack allocation** is just `SUB SP, N` — subtract N from the stack pointer, reserving N bytes. O(1), no bookkeeping.

**Heap allocation** (e.g. `malloc` in glibc) uses a **free list**:
- Memory maintained as linked list of free/used blocks
- Each block has a header: `[size | next_free_ptr | data...]`
- `malloc(N)` walks the free list for a block ≥ N bytes (first-fit, best-fit, buddy system)
- `free(ptr)` inserts the block back into the free list and attempts **coalescing** with adjacent free blocks

**Fragmentation:**
- *External*: free blocks exist but are too small and scattered (solve: compaction or buddy allocator)
- *Internal*: allocated block is larger than requested (solve: slab allocator for fixed-size objects)

**Garbage collection** (Python, Java, Go): the runtime tracks all live references and frees unreachable objects automatically.
Common algorithms: reference counting, mark-and-sweep, generational GC (young/old generation).
""")
