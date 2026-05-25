"""Cache Hierarchy page."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import streamlit as st
import pandas as pd
import random
from core.reference import CACHE_LEVEL_INFO
from core.cpu import Cache


def render():
    st.title("Cache Hierarchy")
    level = st.session_state.get("level","Intermediate")

    st.info("**Cache is a small, fast memory close to the CPU.** "
                "The CPU keeps recently-used data in cache so it doesn't have to make slow trips to main memory (RAM). "
                "It's like keeping your most-used tools on your desk instead of in a cupboard across the room.")

    st.markdown("""
Accessing main RAM takes ~100 ns — roughly **200 CPU cycles** on a modern processor.
Without cache, the CPU would spend most of its time waiting. Cache turns a 200-cycle wait into a 1–4 cycle access.
""")

    # Cache levels reference
    st.markdown("## Cache Levels")
    cols = st.columns(4)
    level_keys = ["L1","L2","L3","RAM"]
    level_colors = {"L1":"#cff4fc","L2":"#d1e7dd","L3":"#fff3cd","RAM":"#f8d7da"}
    for col, lk in zip(cols, level_keys):
        info = CACHE_LEVEL_INFO[lk]
        with col:
            st.markdown(f"""
<div style="background:{level_colors[lk]};border-radius:8px;padding:12px;height:220px">
<h4 style="margin:0 0 8px">{lk}</h4>
<p style="font-size:12px;margin:4px 0"><b>Size:</b> {info['size']}</p>
<p style="font-size:12px;margin:4px 0"><b>Latency:</b> {info['latency']}</p>
<p style="font-size:12px;margin:4px 0"><b>Type:</b> {info['type']}</p>
<p style="font-size:12px;margin:4px 0"><b>Mapping:</b> {info['associativity']}</p>
<p style="font-size:11px;margin:8px 0 0;color:#555">{info['notes']}</p>
</div>""", unsafe_allow_html=True)

    # Interactive cache simulator
    st.divider()
    st.markdown("## Interactive Cache Simulator (4-way set-associative)")
    st.caption("Access memory addresses and watch what happens to the cache. Observe hits, misses, and evictions.")

    if "cache_sim" not in st.session_state:
        st.session_state["cache_sim"] = Cache("L1", 1)
        st.session_state["cache_log"] = []
        st.session_state["sim_mem"]   = {i: random.randint(0,255) for i in range(64)}

    cache = st.session_state["cache_sim"]
    sim_mem = st.session_state["sim_mem"]

    addr_col, btn_col = st.columns([2,1])
    with addr_col:
        addr = st.number_input("Memory address to access (0–63)", min_value=0, max_value=63, value=12, step=1)
    with btn_col:
        st.markdown("<br>", unsafe_allow_html=True)
        access = st.button("Access address", use_container_width=True)
        rand   = st.button("Random access",  use_container_width=True)

    if rand:
        addr = random.randint(0, 63)
        st.session_state["last_addr"] = addr

    if access or rand:
        hit, line = cache.lookup(int(addr))
        log_entry = {"Address": f"0x{int(addr):02X}", "Result": "HIT" if hit else "MISS",
                     "Data": f"0x{sim_mem[int(addr)]:02X}", "Cache set": (int(addr)//4)%4,
                     "Tag": int(addr)//(4*4)}
        if not hit:
            data = [sim_mem.get(int(addr)-int(addr)%4+i, 0) for i in range(4)]
            evicted = cache.load(int(addr), data)
            log_entry["Action"] = "Loaded line" + (" + evicted old line" if evicted else "")
        else:
            log_entry["Action"] = "Served from cache"
        st.session_state["cache_log"].insert(0, log_entry)

    # Stats
    m1,m2,m3,m4 = st.columns(4)
    m1.metric("L1 Hits",    cache.hits)
    m2.metric("L1 Misses",  cache.misses)
    m3.metric("Hit rate",   f"{cache.hit_rate*100:.1f}%")
    m4.metric("Evictions",  cache.evictions)

    # Cache state
    st.markdown("#### Current cache contents")
    cache_rows = []
    for si, s in enumerate(cache.lines):
        for wi, line in enumerate(s):
            cache_rows.append({
                "Set": si, "Way": wi,
                "Valid": "✓" if line.valid else "✗",
                "Tag": f"0x{line.tag:02X}" if line.valid else "—",
                "Data": " ".join(f"{b:02X}" for b in line.data) if line.valid else "—",
                "Dirty": "dirty" if line.dirty else "clean",
            })
    df = pd.DataFrame(cache_rows)
    def highlight_valid(row):
        return ['background-color:#d1e7dd' if row["Valid"]=="✓" else '']*len(row)
    st.dataframe(df.style.apply(highlight_valid,axis=1), hide_index=True, use_container_width=True)

    # Access log
    if st.session_state["cache_log"]:
        st.markdown("#### Access log (most recent first)")
        log_df = pd.DataFrame(st.session_state["cache_log"][:20])
        st.dataframe(log_df, hide_index=True, use_container_width=True)

    if st.button("Reset cache"):
        st.session_state["cache_sim"] = Cache("L1", 1)
        st.session_state["cache_log"] = []
        st.rerun()

    # Replacement policies
    st.divider()
    st.markdown("## Cache Replacement Policies")

    st.markdown("When the cache is full and we need to load a new line, which old line do we throw out?")

    policies = {
        "LRU (Least Recently Used)": {
            "desc": "Evict the line not accessed for the longest time.",
            "pro": "Good temporal locality approximation. Used in most real CPUs.",
            "con": "Requires tracking last-access time (hardware overhead).",
            "used": "Most CPU caches (approximated with pseudo-LRU).",
        },
        "LFU (Least Frequently Used)": {
            "desc": "Evict the line with the lowest access count.",
            "pro": "Keeps 'hot' data in cache.",
            "con": "Old frequently-used data can crowd out new data. Counter overflow.",
            "used": "Some TLBs, specialised caches.",
        },
        "FIFO (First In, First Out)": {
            "desc": "Evict the line that was loaded earliest.",
            "pro": "Trivial to implement.",
            "con": "Poor performance — ignores access patterns.",
            "used": "Rarely. Some L1 victim caches.",
        },
        "Random": {
            "desc": "Evict a random line.",
            "pro": "Zero hardware overhead. No pathological cases.",
            "con": "Unpredictable performance.",
            "used": "ARM CPUs (Cortex-A series). Simpler than LRU.",
        },
    }
    for name, info in policies.items():
        with st.expander(f"**{name}**"):
            c1,c2 = st.columns(2)
            c1.markdown(f"**How it works:** {info['desc']}\n\n**Used in:** {info['used']}")
            c2.markdown(f"**Advantage:** {info['pro']}\n\n**Disadvantage:** {info['con']}")

    if level == "Advanced":
        st.divider()
        st.markdown("## Cache Coherence (multi-core)")
        st.markdown("""
In a multi-core CPU, each core has its own L1/L2 cache. If Core 0 writes to address 0x50 and Core 1 has a copy in its cache, Core 1's copy is now stale (**dirty**).

**MESI Protocol** tracks each cache line's state:
| State | Meaning |
|---|---|
| **M** odified | Dirty. This core has the only valid copy. Must write back before eviction. |
| **E** xclusive | Clean. Only this cache has it. Can silently evict. |
| **S** hared | Clean. Other caches may also have it. |
| **I** nvalid | Stale or not present. |

When Core 0 writes to a Shared line, it broadcasts an **Invalidate** message. All other cores mark their copies Invalid.
The memory controller tracks ownership via a **directory** (or snooping on the bus).
""")
