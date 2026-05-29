def render_interactive_visualiser(json, cpu, steps):
    """
    Renders an interactive, animated HTML/JS component displaying 
    the step-by-step CPU execution dashboard.
    """
    import streamlit.components.v1 as components
    
    sim_json = json
    _sim_json_placeholder = "___SIM_JSON___"
    
    # Standard string literal (no 'f' prefix) to keep JavaScript structures intact
    html_code = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            @keyframes flash-green {
                0% { background-color: rgba(34, 197, 94, 0.4); }
                100% { background-color: transparent; }
            }
            .register-flash {
                animation: flash-green 0.8s ease-out;
            }
        </style>
    </head>
    <body class="bg-slate-950 text-slate-100 p-3 font-mono antialiased h-full min-h-screen">

        <div class="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-xl mb-4">
            <div class="flex flex-wrap items-center justify-between gap-4">
                <div>
                    <span id="phase-badge" class="px-3 py-1 rounded-full text-xs font-bold tracking-wider uppercase bg-cyan-500/20 text-cyan-400">
                        FETCH
                    </span>
                    <h2 class="text-lg font-bold mt-1 text-slate-200">
                        Clock Cycle <span id="cycle-num" class="text-emerald-400">1</span>
                    </h2>
                </div>
                
                <div class="flex items-center space-x-2 bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800">
                    <button id="btn-first" class="px-2 py-1 text-xs hover:bg-slate-800 rounded text-slate-400 hover:text-white">⏮</button>
                    <button id="btn-prev" class="px-2 py-1 text-xs hover:bg-slate-800 rounded text-slate-400 hover:text-white">◀ Prev</button>
                    <button id="btn-play" class="px-3 py-1 text-xs bg-emerald-600 hover:bg-emerald-500 font-bold rounded text-white min-w-[60px]">▶ Play</button>
                    <button id="btn-next" class="px-2 py-1 text-xs hover:bg-slate-800 rounded text-slate-400 hover:text-white">Next ▶</button>
                    <button id="btn-last" class="px-2 py-1 text-xs hover:bg-slate-800 rounded text-slate-400 hover:text-white">⏭</button>
                </div>

                <div class="flex items-center space-x-2">
                    <span class="text-xs text-slate-400">Speed:</span>
                    <input id="speed-slider" type="range" min="200" max="2000" value="800" step="100" class="w-24 h-1 bg-slate-700 rounded-lg appearance-none cursor-pointer">
                    <span id="speed-text" class="text-xs text-slate-400 w-12">800ms</span>
                </div>

                <button id="btn-guide" onclick="toggleGuide()"
                    class="px-3 py-1.5 text-xs rounded-lg border font-semibold transition-all duration-200 border-amber-600 bg-amber-600/20 text-amber-400 hover:bg-amber-600/40">
                    💡 Guide: ON
                </button>
            </div>

            <div class="mt-4 p-3 bg-slate-950/60 rounded-lg border border-slate-800/60">
                <div id="step-desc" class="text-sm font-semibold text-slate-300">Loading description...</div>
                <div id="step-detail" class="text-xs text-slate-400 mt-1 leading-relaxed">Loading details...</div>
            </div>

            <div id="guide-panel" class="mt-3 p-3 rounded-lg border border-amber-700/60 bg-amber-950/30 transition-all duration-300">
                <div class="flex items-start gap-2">
                    <span class="text-amber-400 text-base mt-0.5 shrink-0">💡</span>
                    <div>
                        <div class="text-[10px] font-bold uppercase tracking-widest text-amber-500 mb-1">Guide</div>
                        <div id="guide-text" class="text-xs text-amber-200 leading-relaxed"></div>
                    </div>
                </div>
            </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            
            <div class="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-xl flex flex-col justify-between">
                <div>
                    <h3 class="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 pb-1 border-b border-slate-800">
                        Registers & ALU
                    </h3>
                    <div class="grid grid-cols-2 gap-3">
                        <div id="reg-box-A" class="bg-slate-950 p-2.5 rounded-lg border border-slate-800 transition-all">
                            <div class="text-[10px] text-slate-500 uppercase">Reg A</div>
                            <div id="reg-val-A" class="text-xl font-bold text-slate-200">0x00</div>
                        </div>
                        <div id="reg-box-B" class="bg-slate-950 p-2.5 rounded-lg border border-slate-800 transition-all">
                            <div class="text-[10px] text-slate-500 uppercase">Reg B</div>
                            <div id="reg-val-B" class="text-xl font-bold text-slate-200">0x00</div>
                        </div>
                        <div id="reg-box-PC" class="bg-slate-950 p-2.5 rounded-lg border border-slate-800 transition-all">
                            <div class="text-[10px] text-slate-500 uppercase">Prog Counter (PC)</div>
                            <div id="reg-val-PC" class="text-xl font-bold text-sky-400">0x0000</div>
                        </div>
                        <div id="reg-box-SP" class="bg-slate-950 p-2.5 rounded-lg border border-slate-800 transition-all">
                            <div class="text-[10px] text-slate-500 uppercase">Stack Pointer (SP)</div>
                            <div id="reg-val-SP" class="text-xl font-bold text-slate-200">0x00</div>
                        </div>
                        <div id="reg-box-IR" class="bg-slate-950 p-2.5 rounded-lg border border-slate-800 transition-all col-span-2">
                            <div class="text-[10px] text-slate-500 uppercase">Instr Reg (IR) / CIR</div>
                            <div class="text-sm font-bold text-purple-400 mt-0.5">
                                <span id="reg-val-IR">0x00</span> <span id="reg-val-CIR" class="text-xs font-normal text-slate-400 ml-1"></span>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="mt-4 bg-slate-950 p-3 rounded-lg border border-slate-800">
                    <div class="text-[10px] text-slate-500 uppercase mb-1">Arithmetic Logic Unit</div>
                    <div class="flex items-center justify-between text-xs text-slate-300">
                        <span>Input A: <strong id="alu-in" class="text-slate-100">0x00</strong></span>
                        <span class="text-slate-600">➔</span>
                        <span>Output: <strong id="alu-out" class="text-emerald-400">0x00</strong></span>
                    </div>
                </div>
            </div>

            <div class="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-xl flex flex-col justify-between">
                <div>
                    <h3 class="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 pb-1 border-b border-slate-800">
                        System Bus Status
                    </h3>
                    
                    <div class="space-y-4 py-2">
                        <div class="relative bg-slate-950 p-3 rounded-lg border border-slate-800">
                            <div id="bus-line-addr" class="absolute left-0 top-0 bottom-0 w-1 rounded-l transition-all duration-300 bg-slate-700"></div>
                            <div class="text-[10px] text-slate-500 uppercase tracking-tight">Address Bus</div>
                            <div id="bus-val-addr" class="text-sm font-bold text-slate-400 mt-0.5">0x0000</div>
                        </div>

                        <div class="relative bg-slate-950 p-3 rounded-lg border border-slate-800">
                            <div id="bus-line-data" class="absolute left-0 top-0 bottom-0 w-1 rounded-l transition-all duration-300 bg-slate-700"></div>
                            <div class="text-[10px] text-slate-500 uppercase tracking-tight">Data Bus</div>
                            <div id="bus-val-data" class="text-sm font-bold text-slate-400 mt-0.5">0x00</div>
                        </div>

                        <div class="relative bg-slate-950 p-3 rounded-lg border border-slate-800">
                            <div id="bus-line-ctrl" class="absolute left-0 top-0 bottom-0 w-1 rounded-l transition-all duration-300 bg-slate-700"></div>
                            <div class="text-[10px] text-slate-500 uppercase tracking-tight">Control Signals</div>
                            <div id="bus-val-ctrl" class="text-xs font-bold text-slate-400 mt-0.5 italic">IDLE</div>
                        </div>
                    </div>
                </div>

                <div class="bg-slate-950/50 p-2 rounded text-[11px] text-slate-500 border border-slate-900">
                    💡 Active operations turn bus lanes vibrant colours matching the processor's current operational state.
                </div>
            </div>

            <div class="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-xl">
                <h3 class="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 pb-1 border-b border-slate-800">
                    Bus Interface Unit
                </h3>
                <div class="space-y-3">
                    <div id="reg-box-MAR" class="bg-slate-950 p-2.5 rounded-lg border border-slate-800 transition-all">
                        <div class="text-[10px] text-slate-500 uppercase">Memory Address Reg (MAR)</div>
                        <div id="reg-val-MAR" class="text-base font-bold text-slate-300">0x0000</div>
                    </div>
                    
                    <div id="reg-box-MDR" class="bg-slate-950 p-2.5 rounded-lg border border-slate-800 transition-all">
                        <div class="text-[10px] text-slate-500 uppercase">Memory Data Reg (MDR)</div>
                        <div id="reg-val-MDR" class="text-base font-bold text-slate-300">0x00</div>
                    </div>

                    <div id="cache-alert" class="p-3 rounded-lg border text-xs font-medium hidden transition-all duration-300">
                        <span class="font-bold">Cache Event:</span> <span id="cache-msg"></span>
                    </div>
                </div>
            </div>

        </div>

        <script>
            const simData = ___SIM_JSON___;
            const steps = simData.steps;
            
            let currentIndex = 0;
            let playInterval = null;
            let stepDelay = 800;
            let guideEnabled = true;
            let isStepping = false;

            function getAnnotation(step, index) {
                const r = step.regs;
                const phase = step.phase;
                const cir = r.CIR || "";
                const desc = step.desc || "";

                if (index === 0) {
                    return "This is the reset state. Every register is zero. " +
                           "The Program Counter (PC) points to 0x0070 — the first byte of your program. " +
                           "Nothing has executed yet.";
                }

                if (phase === "fetch" && desc.includes("address bus") && !desc.includes("operand")) {
                    const pc = "0x" + r.PC.toString(16).toUpperCase().padStart(4, "0");
                    return "FETCH phase. The CPU puts the Program Counter value (" + pc + ") " +
                           "onto the address bus and asks memory: \\"what byte lives here?\\" " +
                           "This happens at the start of every instruction, every time.";
                }

                if (phase === "fetch" && desc.includes("FETCH complete")) {
                    const ir = "0x" + r.IR.toString(16).toUpperCase().padStart(2, "0");
                    const cacheNote = step.cache
                        ? (step.cache.includes("hit")
                            ? " Cache hit — the byte was already in L1. No trip to RAM."
                            : " Cache miss — the CPU had to wait for RAM. The cache is now loaded for next time.")
                        : "";
                    return "The opcode " + ir + " arrived in the MDR and was copied into the " +
                           "Instruction Register (IR). PC has already advanced to the next byte." + cacheNote;
                }

                if (phase === "fetch" && desc.includes("operand")) {
                    return "The decoder found that this instruction needs an operand — " +
                           "an extra byte giving the address or value to use. " +
                           "The CPU fetches it with another memory read cycle.";
                }

                if (phase === "decode") {
                    const op = "0x" + r.IR.toString(16).toUpperCase().padStart(2, "0");
                    return "DECODE phase. The Control Unit looks up opcode " + op + " " +
                           "and works out what to do. The decoded mnemonic is now in CIR: \\"" + cir + "\\". " +
                           "It also determines how many operand bytes follow.";
                }

                if (phase === "execute") {
                    if (desc.includes("EXECUTE") && (cir === "LOAD" || desc.includes("LOAD"))) {
                        const val = "0x" + r.A.toString(16).toUpperCase().padStart(2, "0");
                        const dec = r.A;
                        const ch = (dec >= 32 && dec <= 126) ? " ('" + String.fromCharCode(dec) + "')" : "";
                        return "EXECUTE: LOAD. A byte was read from memory into register A. " +
                               "A is now " + val + " = " + dec + ch + ". " +
                               "Every ALU operation uses A as its primary input.";
                    }
                    if (desc.includes("EXECUTE") && (cir === "STORE" || desc.includes("STORE"))) {
                        const val = "0x" + r.A.toString(16).toUpperCase().padStart(2, "0");
                        return "EXECUTE: STORE. The value in A (" + val + ") is being written to memory. " +
                               "The address bus carries the destination, the data bus carries the byte, " +
                               "and the control bus asserts WR (write enable).";
                    }
                    if (desc.includes("EXECUTE IN")) {
                        const val = r.A;
                        const ch = (val >= 32 && val <= 126) ? " ('" + String.fromCharCode(val) + "')" : "";
                        return "EXECUTE: IN. The CPU read from an I/O input port. " +
                               "Port 0 maps to the keyboard register at 0xD0. " +
                               "A is now 0x" + val.toString(16).toUpperCase().padStart(2, "0") +
                               " = " + val + ch + " — the ASCII code of the character typed.";
                    }
                    if (desc.includes("EXECUTE OUT")) {
                        const val = r.A;
                        const ch = (val >= 32 && val <= 126) ? " ('" + String.fromCharCode(val) + "')" : "";
                        return "EXECUTE: OUT. The CPU writes A to an output port. " +
                               "Port 0 maps to Output Register 0xD8 — the display character port. " +
                               "Value 0x" + val.toString(16).toUpperCase().padStart(2, "0") +
                               " = " + val + ch + " is now there. " +
                               "This is how the CPU sends data to hardware devices.";
                    }
                    if (desc.includes("EXECUTE ADD")) {
                        const inn = "0x" + r.ALU_A.toString(16).toUpperCase().padStart(2, "0");
                        const out = "0x" + r.ALU_OUT.toString(16).toUpperCase().padStart(2, "0");
                        return "EXECUTE: ADD. The ALU added the operand to A (" + inn + "). " +
                               "Result: " + out + " — written back into A. " +
                               "The Zero, Carry, Negative and Overflow flags are updated to reflect the result.";
                    }
                    if (desc.includes("EXECUTE SUB")) {
                        return "EXECUTE: SUB. The ALU subtracted the operand from A. " +
                               "Internally this is two's complement addition — the operand is negated then added. " +
                               "Flags are updated; if the result is zero, the Z flag is set.";
                    }
                    if (desc.includes("EXECUTE CMP")) {
                        return "EXECUTE: CMP (compare). The ALU subtracts the operand from A " +
                               "but discards the result — only the flags are updated. " +
                               "This is how the CPU evaluates conditions like 'is A equal to zero?'";
                    }
                    if (desc.includes("EXECUTE J")) {
                        const newpc = "0x" + r.PC.toString(16).toUpperCase().padStart(4, "0");
                        const taken = desc.toLowerCase().includes("taken") || desc.toLowerCase().includes("→ pc");
                        return "EXECUTE: " + cir + " (branch). " +
                               (taken
                                 ? "The condition was met — PC jumped to " + newpc + ". Execution continues from there."
                                 : "The condition was not met — PC was not changed. Execution falls through.");
                    }
                    if (desc.includes("PUSH")) {
                        const sp = "0x" + r.SP.toString(16).toUpperCase().padStart(2, "0");
                        return "PUSH. The value in A was written to the stack and SP decremented to " + sp + ". " +
                               "The stack grows downward in memory. PUSH moves SP down, POP moves it back up.";
                    }
                    if (desc.includes("POP")) {
                        const sp = "0x" + r.SP.toString(16).toUpperCase().padStart(2, "0");
                        return "POP. SP was incremented to " + sp + " and the byte there was read into A. " +
                               "Last In, First Out (LIFO) — you always get back what was pushed most recently.";
                    }
                    if (desc.includes("CALL")) {
                        const dest = "0x" + r.PC.toString(16).toUpperCase().padStart(4, "0");
                        return "EXECUTE: CALL. The return address was pushed onto the stack, " +
                               "then PC jumped to the subroutine at " + dest + ". " +
                               "This is exactly how function calls work in every programming language.";
                    }
                    if (desc.includes("RET")) {
                        const dest = "0x" + r.PC.toString(16).toUpperCase().padStart(4, "0");
                        return "EXECUTE: RET. The return address was popped off the stack into PC (" + dest + "). " +
                               "Execution resumes exactly where the CALL came from. " +
                               "The stack is back to the state it was in before the call.";
                    }
                    if (cir === "NOP") {
                        return "NOP — No Operation. The CPU does nothing for one cycle. " +
                               "This byte is part of the interrupt service routine stub in the BIOS region (0x1E). " +
                               "It precedes the RET that returns control to your program.";
                    }
                    if (cir === "HLT" || desc.includes("HLT")) {
                        return "HLT — the CPU has stopped. The program finished normally. " +
                               "Check the memory map panel to see every byte that was written during execution.";
                    }
                }

                if (phase === "writeback") {
                    const m = desc.match(/(\d+) pending/);
                    return "WRITEBACK phase. Any pending register writes are committed. " +
                           (m && parseInt(m[1]) > 0
                             ? m[1] + " interrupt" + (parseInt(m[1]) > 1 ? "s are" : " is") +
                               " queued — it will be serviced before the next fetch."
                             : "No interrupts pending. The CPU moves straight to the next FETCH.");
                }

                if (phase === "interrupt") {
                    if (desc.includes("masked")) {
                        return "An interrupt arrived but the Interrupt flag (I) is clear — " +
                               "the CPU is ignoring it. This prevents nested interrupts inside an ISR.";
                    }
                    const sp = "0x" + r.SP.toString(16).toUpperCase().padStart(2, "0");
                    return "⚡ INTERRUPT. The CPU paused the program to handle an urgent event. " +
                           "The return address was pushed onto the stack (SP is now " + sp + "). " +
                           "PC jumped to the Interrupt Vector Table to find the handler address. " +
                           "When the handler finishes with RET, execution resumes exactly where it left off.";
                }

                if (phase === "dma") {
                    return "⇄ DMA transfer. The DMA controller took over the buses. " +
                           "The CPU is in HOLD state while data is copied between memory regions " +
                           "without CPU involvement — far faster than LOAD/STORE loops.";
                }

                if (step.cache && step.cache.includes("evict")) {
                    return "Cache eviction. The L1 cache was full so the Least Recently Used " +
                           "line was replaced with the new data. This is the LRU replacement policy.";
                }

                return "Step " + (index + 1) + " of " + steps.length + ".  " +
                       "Phase: " + phase.toUpperCase() + ". " +
                       "Use the panels to see exactly what changed this cycle.";
            }

            function toggleGuide() {
                guideEnabled = !guideEnabled;
                const btn = document.getElementById("btn-guide");
                const panel = document.getElementById("guide-panel");
                if (guideEnabled) {
                    btn.className = "px-3 py-1.5 text-xs rounded-lg border font-semibold transition-all duration-200 border-amber-600 bg-amber-600/20 text-amber-400 hover:bg-amber-600/40";
                    btn.innerText = "💡 Guide: ON";
                    panel.style.display = "";
                    document.getElementById("guide-text").innerText = getAnnotation(steps[currentIndex], currentIndex);
                } else {
                    btn.className = "px-3 py-1.5 text-xs rounded-lg border font-semibold transition-all duration-200 border-slate-700 bg-slate-800/40 text-slate-500 hover:bg-slate-700/40";
                    btn.innerText = "💡 Guide: OFF";
                    panel.style.display = "none";
                }
            }

            const PHASE_COLORS = {
                "fetch": { badge: "bg-cyan-500/20 text-cyan-400", bus: "bg-cyan-500" },
                "decode": { badge: "bg-purple-500/20 text-purple-400", bus: "bg-purple-500" },
                "execute": { badge: "bg-amber-500/20 text-amber-400", bus: "bg-amber-500" },
                "writeback": { badge: "bg-emerald-500/20 text-emerald-400", bus: "bg-emerald-500" },
                "interrupt": { badge: "bg-red-500/20 text-red-400", bus: "bg-red-500" },
                "dma": { badge: "bg-orange-500/20 text-orange-400", bus: "bg-orange-500" }
            };

            let lastRegSnapshot = {};

            function updateUI(index) {
                if (index < 0 || index >= steps.length || isStepping) return;
                
                isStepping = true;
                currentIndex = index;
                const step = steps[index];

                const badge = document.getElementById("phase-badge");
                badge.innerText = step.phase;
                badge.className = "px-3 py-1 rounded-full text-xs font-bold tracking-wider uppercase " + 
                                  (PHASE_COLORS[step.phase]?.badge || "bg-slate-800 text-slate-400");

                document.getElementById("cycle-num").innerText = step.cycle;
                document.getElementById("step-desc").innerText = step.desc;
                document.getElementById("step-detail").innerText = step.detail;

                updateRegister("A", step.regs.A, "0x" + step.regs.A.toString(16).toUpperCase().padStart(2, '0'));
                updateRegister("B", step.regs.B, "0x" + step.regs.B.toString(16).toUpperCase().padStart(2, '0'));
                updateRegister("PC", step.regs.PC, "0x" + step.regs.PC.toString(16).toUpperCase().padStart(4, '0'));
                updateRegister("SP", step.regs.SP, "0x" + step.regs.SP.toString(16).toUpperCase().padStart(2, '0'));
                updateRegister("MAR", step.regs.MAR, "0x" + step.regs.MAR.toString(16).toUpperCase().padStart(4, '0'));
                updateRegister("MDR", step.regs.MDR, "0x" + step.regs.MDR.toString(16).toUpperCase().padStart(2, '0'));
                updateRegister("IR", step.regs.IR, "0x" + step.regs.IR.toString(16).toUpperCase().padStart(2, '0'));
                
                document.getElementById("reg-val-CIR").innerText = step.regs.CIR ? " (" + step.regs.CIR + ")" : "";
                document.getElementById("alu-in").innerText = "0x" + step.regs.ALU_A.toString(16).toUpperCase().padStart(2, '0');
                document.getElementById("alu-out").innerText = "0x" + step.regs.ALU_OUT.toString(16).toUpperCase().padStart(2, '0');

                const cacheBox = document.getElementById("cache-alert");
                if (step.cache) {
                    cacheBox.classList.remove("hidden");
                    document.getElementById("cache-msg").innerText = step.cache;
                    if (step.cache.toLowerCase().includes("hit")) {
                        cacheBox.className = "p-3 rounded-lg border text-xs font-medium bg-emerald-950/40 border-emerald-800 text-emerald-400 mt-3";
                    } else {
                        cacheBox.className = "p-3 rounded-lg border text-xs font-medium bg-rose-950/40 border-rose-800 text-rose-400 mt-3";
                    }
                } else {
                    cacheBox.classList.add("hidden");
                }

                const b = step.bus;
                const addrLine = document.getElementById("bus-line-addr");
                const dataLine = document.getElementById("bus-line-data");
                const ctrlLine = document.getElementById("bus-line-ctrl");
                
                if (b && b.state !== "idle") {
                    const activeColor = PHASE_COLORS[step.phase]?.bus || "bg-slate-600";
                    
                    addrLine.className = "absolute left-0 top-0 bottom-0 w-1 rounded-l transition-all duration-300 " + activeColor;
                    dataLine.className = "absolute left-0 top-0 bottom-0 w-1 rounded-l transition-all duration-300 " + activeColor;
                    ctrlLine.className = "absolute left-0 top-0 bottom-0 w-1 rounded-l transition-all duration-300 " + activeColor;

                    document.getElementById("bus-val-addr").innerText = "0x" + b.addr.toString(16).toUpperCase().padStart(4, '0');
                    document.getElementById("bus-val-data").innerText = "0x" + b.data.toString(16).toUpperCase().padStart(2, '0');
                    document.getElementById("bus-val-ctrl").innerText = b.state.toUpperCase() + (b.ctrl ? " [" + b.ctrl + "]" : "");
                    document.getElementById("bus-val-ctrl").className = "text-xs font-bold text-slate-200 uppercase";
                } else {
                    addrLine.className = "absolute left-0 top-0 bottom-0 w-1 rounded-l transition-all duration-300 bg-slate-800";
                    dataLine.className = "absolute left-0 top-0 bottom-0 w-1 rounded-l transition-all duration-300 bg-slate-800";
                    ctrlLine.className = "absolute left-0 top-0 bottom-0 w-1 rounded-l transition-all duration-300 bg-slate-800";

                    document.getElementById("bus-val-addr").innerText = "0x0000";
                    document.getElementById("bus-val-data").innerText = "0x00";
                    document.getElementById("bus-val-ctrl").innerText = "IDLE";
                    document.getElementById("bus-val-ctrl").className = "text-xs font-bold text-slate-600 uppercase italic";
                }

                lastRegSnapshot = { ...step.regs };

                if (guideEnabled) {
                    document.getElementById("guide-text").innerText = getAnnotation(step, index);
                }
                
                isStepping = false;
            }

            function updateRegister(regName, rawVal, stringFormatted) {
                const textEl = document.getElementById("reg-val-" + regName);
                const containerEl = document.getElementById("reg-box-" + regName);
                
                textEl.innerText = stringFormatted;
                
                if (lastRegSnapshot[regName] !== undefined && lastRegSnapshot[regName] !== rawVal) {
                    containerEl.classList.remove("register-flash");
                    void containerEl.offsetWidth;
                    containerEl.classList.add("register-flash");
                }
            }

            function play() {
                if (playInterval) return;
                document.getElementById("btn-play").innerText = "⏸ Pause";
                document.getElementById("btn-play").className = "px-3 py-1 text-xs bg-amber-600 hover:bg-emerald-500 font-bold rounded text-white min-w-[60px]";
                playInterval = setInterval(() => {
                    if (currentIndex < steps.length - 1) {
                        updateUI(currentIndex + 1);
                    } else {
                        pause();
                    }
                }, stepDelay);
            }

            function pause() {
                if (playInterval) {
                    clearInterval(playInterval);
                    playInterval = null;
                }
                document.getElementById("btn-play").innerText = "▶ Play";
                document.getElementById("btn-play").className = "px-3 py-1 text-xs bg-emerald-600 hover:bg-emerald-500 font-bold rounded text-white min-w-[60px]";
            }

            // Interactive Controls with Asynchronous Task Queue Isolation
            document.getElementById("btn-play").addEventListener("click", (e) => {
                e.preventDefault();
                if (playInterval) pause(); else play();
            });
            document.getElementById("btn-prev").addEventListener("click", (e) => { 
                e.preventDefault();
                pause(); 
                setTimeout(() => updateUI(currentIndex - 1), 0); 
            });
            document.getElementById("btn-next").addEventListener("click", (e) => { 
                e.preventDefault();
                pause(); 
                setTimeout(() => updateUI(currentIndex + 1), 0); 
            });
            document.getElementById("btn-first").addEventListener("click", (e) => { 
                e.preventDefault();
                pause(); 
                setTimeout(() => updateUI(0), 0); 
            });
            document.getElementById("btn-last").addEventListener("click", (e) => { 
                e.preventDefault();
                pause(); 
                setTimeout(() => updateUI(steps.length - 1), 0); 
            });

            const slider = document.getElementById("speed-slider");
            slider.addEventListener("input", (e) => {
                stepDelay = parseInt(e.target.value);
                document.getElementById("speed-text").innerText = stepDelay + "ms";
                if (playInterval) {
                    pause();
                    play();
                }
            });

            updateUI(0);
        </script>
    </body>
    </html>
    """
    
    # Target and safely substitute the template identifier string literal token
    html_code = html_code.replace(_sim_json_placeholder, sim_json)
    
    # Hand off final raw markup string to Streamlit component abstraction framework
    components.html(html_code, height=1200, scrolling=False)