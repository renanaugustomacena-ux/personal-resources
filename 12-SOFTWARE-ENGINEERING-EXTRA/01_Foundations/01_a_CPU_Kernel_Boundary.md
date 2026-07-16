# Module 1.1.a: The CPU & The Kernel Boundary Deep Dive

> **Course:** SWE Masterclass · Phase 1 · Module 01.1.a · **Last updated:** 2026-05-22

## Guiding ideas
1. **Ring 0 (kernel) vs Ring 3 (user): hardware-enforced isolation.**
2. **Syscall: trap from user → kernel via INT/SYSCALL instruction.**
3. **VDSO (Virtual Dynamic Shared Object): syscall acceleration via shared mem.**
4. **Spectre/Meltdown 2018 broke decades of trust: retpoline mitigation cost.**

---

## 1. Hardware Privilege: Protection Rings (x86_64)

The CPU enforces security through **Protection Rings** (Privilege Domains). Although x86 supports 4 rings (0-3), modern operating systems use only two: **Ring 0 (Kernel Mode)** and **Ring 3 (User Mode)**.

### 1.1 The Four Rings (Historical)

```
        ┌─────────────────────────────────────┐
        │           Ring 0: Kernel             │
        │  Full hardware access: MMU, I/O,    │
        │  interrupts, privileged instructions │
        │  ┌─────────────────────────────────┐ │
        │  │       Ring 1: Device Drivers     │ │
        │  │  (unused in modern Linux/Win)    │ │
        │  │  ┌─────────────────────────────┐ │ │
        │  │  │     Ring 2: Services        │ │ │
        │  │  │  (unused in modern OS)      │ │ │
        │  │  │  ┌─────────────────────────┐│ │ │
        │  │  │  │   Ring 3: User Apps     ││ │ │
        │  │  │  │   No direct HW access   ││ │ │
        │  │  │  │   Must use syscalls     ││ │ │
        │  │  │  └─────────────────────────┘│ │ │
        │  │  └─────────────────────────────┘ │ │
        │  └─────────────────────────────────┘ │
        └─────────────────────────────────────┘

Modern usage:
  Ring 0: Kernel (Linux, Windows NT, macOS XNU)
  Ring 1: Unused (some hypervisors historically)
  Ring 2: Unused
  Ring 3: All userspace (apps, libraries, services)

Virtualization extension:
  Ring -1: VMX root (hypervisor, via VT-x/AMD-V)
  Ring -2: SMM (System Management Mode, firmware)
  Ring -3: Intel ME / AMD PSP (management engine)
```

### 1.2 The Mechanics of Privilege

**CPL (Current Privilege Level):** Stored in the bottom 2 bits of the `CS` (Code Segment) register.
- `00` = Ring 0 (Kernel)
- `11` = Ring 3 (User)

**DPL (Descriptor Privilege Level):** Stored in the GDT/IDT entry. Defines "How privileged must you be to access this segment or gate?"

**RPL (Requester Privilege Level):** Stored in the Selector (e.g., when you push a segment to DS/SS). Ensures a kernel process acting on behalf of a user cannot accidentally access kernel data (the "Confused Deputy" problem).

**The Access Rule:** `MAX(CPL, RPL) <= DPL`

Interpretation: Your current rank (CPL) AND the rank of the entity that requested the access (RPL) must both be at least as privileged (numerically lower or equal) as the target's requirement (DPL).

### 1.3 Privileged Instructions

These instructions can only execute at Ring 0. Attempting them at Ring 3 triggers a `#GP` (General Protection Fault):

| Instruction | Purpose |
|-------------|---------|
| `MOV CR0/CR3/CR4, ...` | Control register manipulation (paging, protection) |
| `LGDT / LIDT / LLDT / LTR` | Load descriptor tables |
| `WRMSR / RDMSR` | Read/write Model-Specific Registers |
| `IN / OUT` | Direct I/O port access (unless I/O bitmap allows) |
| `HLT` | Halt the CPU |
| `INVLPG` | Invalidate TLB entry |
| `CLI / STI` | Clear/set interrupt flag |
| `SWAPGS` | Swap GS base (kernel entry) |
| `INVPCID` | Invalidate PCID-tagged TLB entries |

### 1.4 The GDT (Global Descriptor Table)

The GDT defines memory segments and their privilege levels. In 64-bit long mode, segmentation is mostly vestigial (flat address space), but the GDT is still required for:

```
GDT Layout (typical Linux x86_64):

Index    Descriptor              DPL    Notes
─────────────────────────────────────────────────
  0      Null descriptor          -     Required by CPU
  1      Kernel Code Segment      0     CS for Ring 0
  2      Kernel Data Segment      0     DS/SS for Ring 0
  3      User Code Segment (32)   3     Compatibility mode
  4      User Data Segment        3     DS/SS for Ring 3
  5      User Code Segment (64)   3     CS for Ring 3
  6      TSS Descriptor           0     Task State Segment (16 bytes)
  7      TSS (upper half)         -     Continuation of TSS descriptor
 ...     Per-CPU entries          -     TLS, per-CPU data
```

In 64-bit mode, the GDT mainly serves to:
1. Set the CPL via code segment descriptors.
2. Point to the TSS for stack switching on privilege transitions.
3. Hold TLS (Thread-Local Storage) descriptors.

---

## 2. Crossing the Boundary: System Calls

### 2.1 The Legacy Way: `int 0x80` (32-bit)

**Mechanism:** Software Interrupt.

**Steps:**
1. User loads `EAX` with syscall number (e.g., `1` for `exit`).
2. User loads arguments into `EBX, ECX, EDX, ESI, EDI, EBP`.
3. User executes `int 0x80`.
4. CPU looks up vector `0x80` in the **IDT** (Interrupt Descriptor Table).
5. CPU checks DPL of the gate (must be Ring 3 accessible).
6. CPU saves `CS`, `EIP`, `EFLAGS`, `SS`, `ESP` to the **Kernel Stack** (found via TSS.ESP0).
7. CPU switches to Ring 0 and jumps to the handler.

**Performance:** Slow (~300-500 cycles). Requires memory lookups (IDT, GDT) and complex permission checks.

```nasm
; x86 32-bit: write "hello" using int 0x80
section .data
    msg db "hello", 10
    len equ $ - msg

section .text
global _start
_start:
    mov eax, 4          ; sys_write
    mov ebx, 1          ; stdout
    mov ecx, msg        ; buffer
    mov edx, len        ; length
    int 0x80            ; syscall

    mov eax, 1          ; sys_exit
    xor ebx, ebx        ; status 0
    int 0x80
```

### 2.2 The Modern Way: `syscall` (x86_64)

**Mechanism:** Specialized hardware instruction (opcode `0F 05`).

**Steps:**
1. User loads `RAX` with syscall number.
2. User loads arguments into `RDI, RSI, RDX, R10, R8, R9`.
3. User executes `syscall`.
4. **Hardware actions (all in one instruction):**
   - Saves `RIP` to `RCX`.
   - Saves `RFLAGS` to `R11`.
   - Masks `RFLAGS` with `MSR_SYSCALL_MASK` (disables interrupts).
   - Loads `RIP` from `MSR_LSTAR` (Long System Target Address Register).
   - Loads `CS` and `SS` from `MSR_STAR`.
   - Forces CPL to Ring 0.
   - **Does NOT switch RSP.** The kernel entry point must immediately load a kernel stack.
5. Kernel entry code (`entry_SYSCALL_64`):
   - `swapgs` — swap user GS base with kernel GS base.
   - Load kernel stack pointer from per-CPU data: `movq %rsp, PER_CPU(cpu_tss_rw + TSS_sp0)`.
   - Push user registers onto kernel stack.
   - Look up syscall handler in `sys_call_table[RAX]`.
   - Call handler function.
   - Restore registers.
   - `sysretq` — return to Ring 3.

**Performance:** Very fast (~100-150 cycles). Bypasses IDT/GDT lookups entirely.

```
syscall instruction internals:

  User mode (Ring 3)                     Kernel mode (Ring 0)
  ┌──────────────────┐                  ┌──────────────────────────┐
  │ RAX = syscall nr │                  │ entry_SYSCALL_64:        │
  │ RDI = arg1       │                  │   swapgs                 │
  │ RSI = arg2       │ ──── syscall ──► │   mov rsp, kernel_stack  │
  │ RDX = arg3       │   (hardware)     │   push user regs         │
  │ R10 = arg4       │                  │   call sys_call_table[rax]│
  │ R8  = arg5       │                  │   pop user regs          │
  │ R9  = arg6       │ ◄── sysretq ──  │   swapgs                 │
  │                  │   (hardware)     │   sysretq                │
  └──────────────────┘                  └──────────────────────────┘

  RCX = saved RIP (return address)
  R11 = saved RFLAGS
```

### 2.3 The Syscall Table

Linux x86_64 syscall numbers are defined in `arch/x86/entry/syscalls/syscall_64.tbl`:

| Number | Name | Category |
|--------|------|----------|
| 0 | `read` | File I/O |
| 1 | `write` | File I/O |
| 2 | `open` | File I/O |
| 3 | `close` | File I/O |
| 9 | `mmap` | Memory |
| 56 | `clone` | Process |
| 57 | `fork` | Process |
| 59 | `execve` | Process |
| 60 | `exit` | Process |
| 61 | `wait4` | Process |
| 62 | `kill` | Signal |
| 202 | `futex` | Synchronization |
| 231 | `exit_group` | Process |
| 257 | `openat` | File I/O |
| 318 | `getrandom` | Random |
| 435 | `clone3` | Process |
| 441 | `epoll_pwait2` | I/O multiplex |
| 451 | `io_uring_setup` | Async I/O |

### 2.4 Syscall Cost Measurement

```c
/* C: measure raw syscall overhead */
#include <stdio.h>
#include <time.h>
#include <unistd.h>
#include <sys/syscall.h>

#define ITERATIONS 10000000

int main(void) {
    struct timespec start, end;

    /* Warm up */
    for (int i = 0; i < 1000; i++)
        syscall(SYS_getpid);

    clock_gettime(CLOCK_MONOTONIC, &start);
    for (int i = 0; i < ITERATIONS; i++)
        syscall(SYS_getpid);
    clock_gettime(CLOCK_MONOTONIC, &end);

    double ns = (end.tv_sec - start.tv_sec) * 1e9 +
                (end.tv_nsec - start.tv_nsec);
    printf("getpid() via syscall: %.1f ns/call\n", ns / ITERATIONS);

    /* Compare with VDSO-accelerated call */
    clock_gettime(CLOCK_MONOTONIC, &start);
    for (int i = 0; i < ITERATIONS; i++)
        getpid();  /* glibc caches this — unfair comparison */
    clock_gettime(CLOCK_MONOTONIC, &end);

    ns = (end.tv_sec - start.tv_sec) * 1e9 +
         (end.tv_nsec - start.tv_nsec);
    printf("getpid() via glibc cache: %.1f ns/call\n", ns / ITERATIONS);

    return 0;
}
```

---

## 3. VDSO — Virtual Dynamic Shared Object

### 3.1 The Problem

Some syscalls are called extremely frequently but only read kernel data:
- `gettimeofday()` / `clock_gettime()` — called millions of times per second in web servers.
- `getcpu()` — needed for NUMA-aware allocation.

Making a full Ring 3 → Ring 0 transition for each is wasteful.

### 3.2 The Solution

The kernel maps a small shared library (`linux-vdso.so.1`) into every process's address space. This library contains userspace implementations of selected syscalls that read kernel data from shared memory pages.

```
Process Address Space:
                                    
  ┌─────────────────────┐ 0x7fff...
  │     Stack            │
  ├─────────────────────┤
  │     VDSO             │ ◄── Kernel maps this page (read-only)
  │  linux-vdso.so.1     │     Contains: __vdso_clock_gettime
  │  (1-2 pages)         │              __vdso_gettimeofday
  ├─────────────────────┤              __vdso_getcpu
  │     vvar pages       │ ◄── Kernel data pages (read-only)
  │  (time, CPU info)    │     Updated by kernel on timer tick
  ├─────────────────────┤
  │     mmap region      │
  │     ...              │
```

### 3.3 How VDSO clock_gettime Works

```
Without VDSO:                         With VDSO:
                                      
User: clock_gettime()                 User: clock_gettime()
  │                                     │
  ├──► syscall instruction              ├──► call __vdso_clock_gettime
  │    (Ring 3 → Ring 0)                │    (stays in Ring 3)
  │    kernel reads TSC                 │    read vvar page (shared mem)
  │    kernel computes time             │    read TSC (RDTSC instruction)
  │    kernel copies to user            │    compute time in userspace
  │    sysret (Ring 0 → Ring 3)         │    return
  │                                     │
  Cost: ~200-500 ns                     Cost: ~20-40 ns
```

The kernel keeps a `vvar` page updated with:
- Clock source parameters (TSC frequency, offset, multiplier).
- Coarse time (`CLOCK_REALTIME_COARSE`, `CLOCK_MONOTONIC_COARSE`).
- Sequence counter for lock-free reads.

```bash
# Inspect VDSO in a running process
cat /proc/self/maps | grep vdso
# 7ffff7fc0000-7ffff7fc2000 r-xp 00000000 00:00 0  [vdso]
# 7ffff7fbe000-7ffff7fc0000 r--p 00000000 00:00 0  [vvar]

# Dump VDSO symbols
objdump -T /proc/self/exe 2>/dev/null | head
# Or:
LD_SHOW_AUXV=1 /bin/true | grep VDSO
# AT_SYSINFO_EHDR: 0x7ffff7fc0000
```

### 3.4 VDSO-Accelerated Syscalls

| Syscall | VDSO? | Notes |
|---------|-------|-------|
| `clock_gettime` | Yes | Most important; used by profilers, loggers |
| `gettimeofday` | Yes | Legacy; prefer clock_gettime |
| `time` | Yes | Coarse; returns seconds |
| `getcpu` | Yes | NUMA node and CPU identification |
| `clock_getres` | Yes | Clock resolution query |
| `getpid` | No | glibc caches it instead |
| `read` | No | Requires kernel I/O |
| `write` | No | Requires kernel I/O |

---

## 4. Interrupt Handling & The IDT

When hardware needs attention (keyboard, NIC, timer), it fires an interrupt.

### 4.1 The IDT (Interrupt Descriptor Table)

An array of 256 **Gate Descriptors** (16 bytes each in 64-bit mode).

```
IDTR Register:
┌────────────────────────────────────────┐
│  Limit (16 bits)  │  Base (64 bits)    │
│  256*16 - 1       │  Address of IDT    │
└────────────────────────────────────────┘

IDT Entry (Gate Descriptor, 16 bytes):
┌────────────────────────────────────────────────────┐
│ Bytes 0-1:  Offset[15:0]   (handler address low)   │
│ Bytes 2-3:  Segment Selector (usually kernel CS)   │
│ Byte  4:    IST index (0-7, 0 = no IST switch)    │
│ Byte  5:    Type (0xE=Interrupt, 0xF=Trap) + DPL   │
│ Bytes 6-7:  Offset[31:16]  (handler address mid)   │
│ Bytes 8-11: Offset[63:32]  (handler address high)  │
│ Bytes 12-15: Reserved (must be 0)                   │
└────────────────────────────────────────────────────┘
```

**Vector allocation:**

| Range | Purpose | Examples |
|-------|---------|----------|
| 0-31 | CPU Exceptions | #DE(0) Divide, #DB(1) Debug, #NMI(2), #BP(3) Breakpoint, #OF(4) Overflow, #UD(6) Invalid Opcode, #NM(7) No FPU, #DF(8) Double Fault, #GP(13) General Protection, #PF(14) Page Fault, #MF(16) FPU Error, #AC(17) Alignment |
| 32-47 | Legacy IRQs (PIC) | Timer(32), Keyboard(33), COM2(35), COM1(36), LPT(39), RTC(40), Mouse(44), FPU(45), ATA1(46), ATA2(47) |
| 48-255 | APIC IRQs & software | Configurable; Linux uses 0x80 for legacy syscall, 0xFE for thermal, 0xFF for APIC spurious |

### 4.2 The Interrupt Sequence (Detailed)

```
Hardware interrupt arrives at CPU:

1. CPU finishes current instruction (or aborts for exceptions)
2. CPU checks IF (Interrupt Flag) in RFLAGS
   - If IF=0 and not NMI/exception: interrupt is held pending
   - If IF=1: proceed
3. CPU reads vector number from LAPIC (Local APIC)
4. CPU reads IDT[vector]
5. Privilege check:
   - For hardware interrupts: always allowed
   - For software interrupts (INT n): check CPL <= DPL of gate
6. Stack switch (if privilege change Ring 3 → Ring 0):
   a. Load RSP from TSS.RSP0
   b. OR: if IST field non-zero, load from TSS.IST[n]
7. Push onto new stack:
   ┌──────────────┐ ◄── old RSP (if IST or privilege change)
   │     SS        │
   │     RSP       │ (old stack pointer)
   │   RFLAGS      │
   │     CS        │
   │     RIP       │ (return address)
   │  Error Code   │ (only for some exceptions)
   └──────────────┘ ◄── new RSP
8. Clear IF (for Interrupt Gates; Trap Gates leave IF alone)
9. Load CS:RIP from gate descriptor
10. Execute ISR (Interrupt Service Routine)
```

### 4.3 Interrupt Gate vs Trap Gate

| Feature | Interrupt Gate | Trap Gate |
|---------|---------------|-----------|
| Clears IF? | Yes (disables interrupts) | No (allows nesting) |
| Used for | Hardware IRQs | Exceptions, syscalls |
| Re-entrancy | Not re-entrant by default | Can be interrupted |

### 4.4 Top Half / Bottom Half Processing

The interrupt handler must be fast (interrupts are disabled or partially disabled). Linux splits work:

```
IRQ fires
    │
    ▼
┌─────────────────────────────────────────┐
│  TOP HALF (hardirq context)             │
│  - Runs with interrupts disabled        │
│  - Must be fast (< few μs)             │
│  - Acknowledge hardware                 │
│  - Copy data from device to buffer      │
│  - Schedule bottom half                 │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  BOTTOM HALF (softirq / tasklet / wq)   │
│  - Runs with interrupts enabled         │
│  - Can do heavier processing            │
│  - Network packet processing (NAPI)     │
│  - Block I/O completion                 │
│  - Timer callbacks                      │
└─────────────────────────────────────────┘

Bottom half mechanisms:
┌────────────┬──────────────┬────────────────────┐
│ Softirq    │ Tasklet      │ Workqueue           │
├────────────┼──────────────┼────────────────────┤
│ Static set │ Dynamic      │ Dynamic              │
│ Per-CPU    │ Per-CPU      │ Kernel threads       │
│ No sleep   │ No sleep     │ CAN sleep            │
│ Fastest    │ Fast         │ Flexible             │
│ NET_RX,    │ Custom       │ Deferred work        │
│ BLOCK,     │ drivers      │ that needs           │
│ TIMER      │              │ process context      │
└────────────┴──────────────┴────────────────────┘
```

### 4.5 The APIC (Advanced Programmable Interrupt Controller)

Modern systems use the APIC, not the legacy 8259 PIC:

```
                    ┌──────────┐
  Device 1 ───────►│          │
  Device 2 ───────►│  I/O     │          ┌──────────┐
  Device 3 ───────►│  APIC    │──────────│  LAPIC   │──► CPU 0
  Device 4 ───────►│          │    ┌─────│  (Local) │
                    └──────────┘    │    └──────────┘
                                   │
                                   │    ┌──────────┐
                                   └────│  LAPIC   │──► CPU 1
                                        │  (Local) │
                                        └──────────┘

I/O APIC:
  - Receives external hardware interrupts
  - Routes to specific CPU's LAPIC via redirection table
  - Supports: fixed delivery, lowest priority, round-robin

LAPIC:
  - Per-CPU, handles local timer, IPI, thermal, performance
  - Timer: used for scheduler tick (one-shot or periodic)
  - IPI (Inter-Processor Interrupt): for TLB shootdown, reschedule
```

---

## 5. DMA (Direct Memory Access)

### 5.1 Why DMA Exists

Without DMA, the CPU must copy every byte between I/O devices and memory (PIO — Programmed I/O). For a 10 Gbps NIC receiving at full rate, this would consume the entire CPU.

### 5.2 DMA Mechanics

```
Without DMA (PIO):                  With DMA:

CPU reads byte from device          CPU programs DMA controller:
CPU writes byte to RAM              - Source: device register
CPU reads byte from device          - Destination: RAM address
CPU writes byte to RAM              - Length: N bytes
... (repeat N times)                DMA controller transfers N bytes
CPU is 100% busy                    CPU is free during transfer
                                    DMA raises IRQ when done
                                    CPU handles completion
```

### 5.3 DMA Address Spaces

```
  CPU Virtual     CPU Physical     Bus Address
  Address Space   Address Space    (IOMMU)
  ┌──────────┐   ┌──────────┐    ┌──────────┐
  │ Process  │   │          │    │          │
  │ pages    │──►│ Physical │    │ Device   │
  │          │   │ frames   │◄───│ DMA      │
  └──────────┘   └──────────┘    └──────────┘
  
  MMU translates   1:1 or IOMMU    Device sees
  virtual → phys   translates      bus addresses
```

**IOMMU (I/O Memory Management Unit):**
- Translates device DMA addresses to physical addresses.
- Provides device isolation (device A cannot DMA into device B's memory).
- Foundation for VFIO device passthrough in VMs.
- Intel VT-d, AMD-Vi.

```c
/* C: DMA-capable memory allocation (kernel module context) */
/* This is kernel code, not userspace */
#include <linux/dma-mapping.h>

/* Allocate DMA-coherent memory */
dma_addr_t dma_handle;
void *buf = dma_alloc_coherent(dev, size, &dma_handle, GFP_KERNEL);
/* buf = CPU virtual address
   dma_handle = bus address for the device */

/* Program the device with dma_handle */
writel(dma_handle, dev->regs + DMA_ADDR_REG);
writel(size, dev->regs + DMA_LEN_REG);
writel(DMA_START, dev->regs + DMA_CTRL_REG);

/* When done, free */
dma_free_coherent(dev, size, buf, dma_handle);
```

### 5.4 Scatter-Gather DMA

Modern devices support scatter-gather lists: DMA from/to multiple non-contiguous physical memory regions in one operation.

```
Scatter-Gather List:
┌─────────────────────────┐
│ Entry 0: addr=0x1000    │──► Physical page at 0x1000
│          len=4096       │
├─────────────────────────┤
│ Entry 1: addr=0x5000    │──► Physical page at 0x5000
│          len=8192       │
├─────────────────────────┤
│ Entry 2: addr=0x9000    │──► Physical page at 0x9000
│          len=4096       │
└─────────────────────────┘

Device reads the SG list and DMAs from all three regions
without CPU involvement. No need for physically contiguous memory.
```

---

## 6. MMIO (Memory-Mapped I/O)

### 6.1 Port I/O vs MMIO

| Feature | Port I/O (`IN`/`OUT`) | MMIO |
|---------|----------------------|------|
| Address space | Separate 64K I/O port space | Shared physical address space |
| Instructions | `IN`, `OUT` (privileged) | Regular `MOV` (via page tables) |
| Speed | Slower (serializing) | Faster (pipelined) |
| Modern usage | Legacy (PCI config, PS/2) | All modern devices (PCIe BARs) |

### 6.2 MMIO Mechanics

```
Physical Address Space:

0x00000000 ┌──────────────────────┐
           │    RAM (DRAM)         │
           │                      │
0x80000000 ├──────────────────────┤
           │    PCI MMIO Region    │ ◄── Device registers mapped here
           │                      │     Reads/writes go to device, not RAM
           │    NIC BAR0: 0xFEB80000-0xFEB9FFFF (128 KB)
           │    GPU BAR0: 0xC0000000-0xCFFFFFFF (256 MB)
           │                      │
0xFED00000 ├──────────────────────┤
           │    LAPIC              │ 0xFEE00000 (4 KB)
           │    I/O APIC           │ 0xFEC00000 (4 KB)
           │    HPET               │ 0xFED00000 (4 KB)
0xFFFFFFFF └──────────────────────┘
```

```c
/* C: accessing MMIO registers (kernel context) */
#include <linux/io.h>

/* Map device registers into kernel virtual address space */
void __iomem *regs = ioremap(pci_resource_start(pdev, 0),
                             pci_resource_len(pdev, 0));

/* Read/write device registers (with memory barriers) */
u32 status = readl(regs + STATUS_REG);
writel(CMD_START, regs + COMMAND_REG);

/* Unmap when done */
iounmap(regs);
```

**Critical: MMIO requires memory barriers.** The CPU may reorder normal memory accesses, but device register accesses must be strictly ordered. `readl()`/`writel()` include implicit barriers.

---

## 7. Speculative Execution Side Channels

### 7.1 Background: Speculative Execution

Modern CPUs execute instructions before knowing if they are on the correct path:

```
Branch prediction pipeline:

  Fetch → Decode → Execute → Memory → Writeback
                      │
                   Speculate past branch
                      │
              ┌───────┴───────┐
              │               │
         Branch taken    Branch not taken
         (speculated)    (speculated)
              │               │
              ▼               ▼
         Execute          Execute
         speculatively    speculatively
              │               │
         When branch resolves:
         - Correct path: commit results
         - Wrong path: squash results
                        BUT: microarchitectural
                        state changes (cache)
                        are NOT rolled back
```

### 7.2 Meltdown (CVE-2017-5754) — "Rogue Data Cache Load"

**The Vulnerability:**
```
Ring 3 code:
1. Speculatively read kernel memory address K
   (will fault — permission denied)
2. Use the value at K as an index into a user array:
   access user_array[kernel_data * 256]
3. CPU resolves the permission check → squash
4. BUT: user_array[kernel_data * 256] is now in L1 cache
5. Time access to each user_array[i * 256]:
   - Fast access = i was the kernel data value
   - FLUSH+RELOAD side channel extracts kernel memory
```

**Impact:** Any userspace process could read all kernel memory (and other processes' memory, since the kernel maps all physical memory).

**Mitigation: KPTI (Kernel Page Table Isolation)**
```
Before KPTI:
  User page table maps: user pages + ALL kernel pages
  (kernel pages marked supervisor-only, but Meltdown bypasses this)

After KPTI:
  User page table:   user pages + minimal kernel stub
  Kernel page table: user pages + ALL kernel pages

  On syscall entry:
    1. Stub in user page table handles transition
    2. Switch CR3 to kernel page table (full mapping)
  On syscall return:
    1. Switch CR3 to user page table (kernel unmapped)
    2. Return to user mode

  Cost: Two CR3 switches per syscall ≈ 1-5% overhead
        (PCID mitigates by avoiding full TLB flush)
```

### 7.3 Spectre (CVE-2017-5753 & CVE-2017-5715)

**Variant 1: Bounds Check Bypass**

```c
/* Vulnerable pattern */
if (x < array1_size) {              /* branch predicted as taken */
    y = array2[array1[x] * 256];    /* speculatively executed */
}
/* Attacker controls x to be out-of-bounds.
   Branch predictor trained to predict "taken".
   Speculative execution reads array1[x] (arbitrary memory)
   and leaves a cache trace in array2. */
```

**Mitigation:** `lfence` after bounds checks, compiler barriers, array index masking.

**Variant 2: Branch Target Injection**

```
Attacker trains the Branch Target Buffer (BTB) to predict
that an indirect call in the victim will jump to a gadget
of the attacker's choice. The gadget speculatively executes
and leaks data via cache side channel.
```

**Mitigation: Retpoline**
```nasm
; Normal indirect call:
call *rax        ; uses BTB prediction (vulnerable)

; Retpoline:
call load_label
capture_spec:
  pause           ; trap speculative execution in a loop
  lfence
  jmp capture_spec
load_label:
  mov [rsp], rax  ; overwrite return address on stack
  ret             ; "return" to rax (not predicted by BTB)
```

The retpoline forces the CPU to use the Return Stack Buffer (RSB) instead of the BTB. The RSB entry is controlled by the `call` instruction, not by attacker-trained BTB state.

**Cost:** Retpoline adds ~5-20% overhead to syscall-heavy workloads. Modern CPUs (Ice Lake+) support IBRS (Indirect Branch Restricted Speculation) in hardware, which is cheaper.

### 7.4 Post-2018 Speculative Execution Vulnerabilities

| Vulnerability | Year | Target | Mitigation |
|--------------|------|--------|------------|
| Meltdown | 2018 | Kernel memory from userspace | KPTI |
| Spectre v1 | 2018 | Bounds check bypass | lfence, masking |
| Spectre v2 | 2018 | Branch target injection | Retpoline, IBRS |
| L1TF (Foreshadow) | 2018 | L1 cache / VM isolation | L1D flush on vmentry |
| MDS (ZombieLoad) | 2019 | Internal CPU buffers | Microcode + buffer flush |
| TAA | 2019 | TSX async abort | Microcode, TSX disable |
| SRBDS | 2020 | Special register reads | Microcode |
| Downfall (GDS) | 2023 | AVX gather instructions | Microcode |
| Inception | 2023 | Return address prediction (AMD) | Microcode, IBPB |
| Indirector | 2024 | IBPB bypass | Microcode updates |

### 7.5 Mitigation Performance Impact

```bash
# Check which mitigations are active
cat /sys/devices/system/cpu/vulnerabilities/*

# Example output:
# itlb_multihit: Not affected
# l1tf: Mitigation: PTE Inversion
# mds: Mitigation: Clear CPU buffers; SMT vulnerable
# meltdown: Mitigation: PTI
# spec_store_bypass: Mitigation: Speculative Store Bypass disabled
# spectre_v1: Mitigation: usercopy/swapgs barriers
# spectre_v2: Mitigation: Retpoline; IBPB: conditional; STIBP: disabled

# Disable mitigations for benchmarking (NOT for production!)
# Boot param: mitigations=off
# Typical performance gain: 5-30% depending on workload
```

---

## 8. eBPF — Extended Berkeley Packet Filter

### 8.1 What Is eBPF?

eBPF is a virtual machine inside the Linux kernel that runs sandboxed programs at native speed. Originally for packet filtering, it now supports:

```
eBPF Programs can attach to:

  ┌──────────────────────────────────────────┐
  │  Tracing & Profiling                      │
  │  - kprobes (any kernel function)          │
  │  - tracepoints (stable kernel events)     │
  │  - uprobes (userspace function entry)     │
  │  - perf events (hardware counters)        │
  │  - USDT probes (userspace markers)        │
  ├──────────────────────────────────────────┤
  │  Networking                               │
  │  - XDP (eXpress Data Path) — driver level │
  │  - TC (Traffic Control)                   │
  │  - Socket filters                         │
  │  - sk_msg (socket redirect)               │
  ├──────────────────────────────────────────┤
  │  Security                                 │
  │  - LSM (Linux Security Module) hooks      │
  │  - seccomp (syscall filtering)            │
  ├──────────────────────────────────────────┤
  │  Scheduling                               │
  │  - sched_ext (custom schedulers)          │
  ├──────────────────────────────────────────┤
  │  Storage                                  │
  │  - fentry/fexit (function entry/exit)     │
  │  - io_uring                               │
  └──────────────────────────────────────────┘
```

### 8.2 eBPF Architecture

```
User Space                              Kernel Space
┌─────────────────────┐                ┌─────────────────────────────┐
│  C source code       │                │                             │
│  (restricted subset) │                │  eBPF Verifier              │
│         │            │                │  ┌───────────────────────┐  │
│  Clang/LLVM          │                │  │ - Checks memory safety│  │
│  (compile to BPF     │   bpf()        │  │ - No loops (bounded)  │  │
│   bytecode)          │──syscall──────►│  │ - Stack < 512 bytes   │  │
│         │            │                │  │ - No null derefs      │  │
│  .o file (ELF)       │                │  │ - Terminates          │  │
│                      │                │  └───────┬───────────────┘  │
│  Loader (libbpf)     │                │          │ Pass             │
│                      │                │          ▼                  │
│  User-space maps     │◄── shared ────►│  JIT Compiler              │
│  (ring buffer,       │    memory      │  (BPF bytecode → native    │
│   hash map,          │    (maps)      │   x86_64 instructions)     │
│   array, etc.)       │                │          │                  │
└─────────────────────┘                │          ▼                  │
                                       │  Attached to hook point     │
                                       │  (kprobe, XDP, tracepoint)  │
                                       │  Runs at native speed       │
                                       └─────────────────────────────┘
```

### 8.3 eBPF Safety Guarantees

The verifier ensures:
1. **No infinite loops:** All loops must have provably bounded iteration count.
2. **Memory safety:** All pointer accesses are bounds-checked.
3. **Stack limit:** Maximum 512 bytes of stack per program.
4. **No sleeping:** Programs cannot call functions that might sleep.
5. **Bounded complexity:** Verifier limits the number of instructions examined.
6. **Helper functions only:** Programs can only call approved kernel helpers.

### 8.4 eBPF Maps (Shared Data Structures)

```
Map Types:
┌────────────────────┬──────────────────────────────────┐
│ BPF_MAP_TYPE_HASH  │ Key-value hash table              │
│ BPF_MAP_TYPE_ARRAY │ Fixed-size array                  │
│ BPF_MAP_TYPE_RINGBUF│ Efficient event streaming        │
│ BPF_MAP_TYPE_PERCPU_HASH │ Per-CPU hash (no locks)    │
│ BPF_MAP_TYPE_LRU_HASH │ Auto-evicting LRU hash       │
│ BPF_MAP_TYPE_STACK_TRACE│ Stack trace storage         │
│ BPF_MAP_TYPE_PROG_ARRAY│ Tail call jump table        │
│ BPF_MAP_TYPE_BLOOM_FILTER│ Probabilistic membership  │
└────────────────────┴──────────────────────────────────┘
```

### 8.5 Practical eBPF: Tracing with bpftrace

```bash
# Count syscalls per process
bpftrace -e 'tracepoint:raw_syscalls:sys_enter { @[comm] = count(); }'

# Trace file opens
bpftrace -e 'tracepoint:syscalls:sys_enter_openat {
    printf("%s opened %s\n", comm, str(args->filename));
}'

# Histogram of read() sizes
bpftrace -e 'tracepoint:syscalls:sys_exit_read /args->ret > 0/ {
    @bytes = hist(args->ret);
}'

# Track scheduling latency per process
bpftrace -e 'tracepoint:sched:sched_switch {
    @[args->prev_comm] = hist(nsecs - @start[args->prev_pid]);
}
tracepoint:sched:sched_wakeup {
    @start[args->pid] = nsecs;
}'
```

### 8.6 XDP — eXpress Data Path

XDP runs eBPF programs at the network driver level, before the kernel allocates an `sk_buff`. This enables packet processing at millions of packets per second.

```
Packet arrives at NIC
         │
         ▼
  ┌──────────────┐
  │  XDP Program  │ ← runs in driver context
  │               │
  │  Actions:     │
  │  XDP_DROP     │──► Drop packet (never reaches kernel)
  │  XDP_TX       │──► Bounce back out same NIC
  │  XDP_REDIRECT │──► Send to different NIC/CPU/socket
  │  XDP_PASS     │──► Normal kernel networking stack
  │  XDP_ABORTED  │──► Drop + trace error
  └──────────────┘
```

Use cases:
- DDoS mitigation: drop bad packets before kernel overhead.
- Load balancing: redirect packets to appropriate backend.
- Monitoring: count packets without kernel stack overhead.

```python
# Python: simple eBPF program using bcc
from bcc import BPF

program = """
int hello(void *ctx) {
    bpf_trace_printk("Hello from eBPF!\\n");
    return 0;
}
"""

b = BPF(text=program)
b.attach_kprobe(event="__x64_sys_clone", fn_name="hello")
print("Tracing sys_clone... Ctrl+C to stop")
b.trace_print()
```

---

## 9. The TSS (Task State Segment) in x86_64

In 32-bit mode, the TSS was used for hardware context switching. In 64-bit mode, hardware task switching is removed. The TSS serves three purposes:

### 9.1 RSP0 — Kernel Stack Pointer

When a privilege change happens (Ring 3 → Ring 0 via syscall/interrupt), the CPU needs to know where the kernel stack is. It reads `TSS.RSP0`.

```
TSS Structure (x86_64):
┌─────────────────────────────┐
│  Reserved (4 bytes)          │ Offset 0x00
├─────────────────────────────┤
│  RSP0 (8 bytes)              │ 0x04  ← Ring 0 stack
├─────────────────────────────┤
│  RSP1 (8 bytes)              │ 0x0C  ← Ring 1 stack (unused)
├─────────────────────────────┤
│  RSP2 (8 bytes)              │ 0x14  ← Ring 2 stack (unused)
├─────────────────────────────┤
│  Reserved (8 bytes)          │ 0x1C
├─────────────────────────────┤
│  IST1 (8 bytes)              │ 0x24  ← Emergency stack 1
│  IST2 (8 bytes)              │ 0x2C  ← Emergency stack 2
│  IST3 (8 bytes)              │ 0x34
│  IST4 (8 bytes)              │ 0x3C
│  IST5 (8 bytes)              │ 0x44
│  IST6 (8 bytes)              │ 0x4C
│  IST7 (8 bytes)              │ 0x54
├─────────────────────────────┤
│  Reserved (10 bytes)         │ 0x5C
├─────────────────────────────┤
│  IOPB Offset (2 bytes)       │ 0x66  ← I/O Permission Bitmap
├─────────────────────────────┤
│  I/O Permission Bitmap       │ Variable
│  (up to 8 KB)                │
└─────────────────────────────┘
```

### 9.2 IST (Interrupt Stack Table)

7 pointers to emergency stacks for critical exceptions:

| IST Entry | Linux usage | Why |
|-----------|-------------|-----|
| IST1 | #DF (Double Fault) | If kernel stack is corrupted, need a known-good stack |
| IST2 | #NMI (Non-Maskable Interrupt) | NMI can arrive at any time, even during stack switch |
| IST3 | #DB (Debug) | Debug exceptions during sensitive code |
| IST4 | #MC (Machine Check) | Hardware error, need reliable stack |

### 9.3 I/O Permission Bitmap

A bitmap where each bit represents an I/O port (0-65535). If bit N is 0, the process can access port N with `IN`/`OUT` even from Ring 3. Used for legacy hardware access (e.g., X11 direct video).

---

## 10. Performance Analysis: CPU and Kernel Boundary

### 10.1 Measuring Syscall Overhead

```bash
# Count syscalls for a command
strace -c ls /tmp
# Shows: calls, errors, time per syscall

# Trace only specific syscalls
strace -e trace=open,read,write,close -p <pid>

# Time individual syscalls (nanosecond precision)
strace -T -e trace=write -p <pid>
# T flag adds elapsed time per syscall

# System-wide syscall monitoring with perf
perf stat -e 'syscalls:sys_enter_*' -a -- sleep 5
```

### 10.2 Identifying Kernel Boundary Bottlenecks

**Symptom: High system time in `top`.**

```bash
# Check user vs system time
top
# Look at %sy (system) vs %us (user)
# Normal: %sy < 10%
# Concerning: %sy > 30%

# Find which syscalls consume system time
perf top -e cycles:k   # kernel-only cycles
# Shows kernel functions consuming CPU

# Common causes of high system time:
# 1. Too many small I/O operations (high syscall rate)
#    Fix: batch reads/writes, use mmap, use io_uring
# 2. Excessive context switches
#    Fix: reduce thread count, use async I/O
# 3. Lock contention in kernel (futex, mmap_lock)
#    Fix: reduce shared memory contention
# 4. TLB misses (KPTI overhead)
#    Fix: use huge pages
```

### 10.3 Syscall Batching Strategies

```
Strategy comparison for handling 10,000 I/O operations:

Individual syscalls:    10,000 syscalls × ~200 ns = ~2 ms overhead
io_uring batching:      ~10 submit calls × ~200 ns = ~2 μs overhead
                        1000× reduction in syscall overhead
```

---

## 11. Real-World Troubleshooting Scenarios

### Scenario 1: Application Crashes with SIGSEGV

```bash
# Get the crash address
dmesg | tail
# segfault at 0x7f... ip 0x... sp 0x... error 4 in libc.so

# Error code bits:
# Bit 0: 0 = no page found, 1 = protection fault
# Bit 1: 0 = read access, 1 = write access
# Bit 2: 0 = kernel mode, 1 = user mode

# Error 4 = binary 100 = user mode read of non-present page
# Error 6 = binary 110 = user mode write of non-present page
# Error 7 = binary 111 = user mode write protection fault

# Generate core dump for analysis
ulimit -c unlimited
./crashing_app
gdb ./crashing_app core
```

### Scenario 2: Spectre Mitigation Causing Performance Regression

```bash
# Check if mitigations are active
grep . /sys/devices/system/cpu/vulnerabilities/*

# Benchmark with and without mitigations
# WARNING: only for testing, never disable in production
# Boot with: mitigations=off

# If you need maximum performance in a trusted environment:
# - Disable KPTI (nopti boot param) — only if no Meltdown-vulnerable CPU
# - Use IBRS instead of retpoline (less overhead on newer CPUs)
# - Disable STIBP if not running untrusted code in SMT siblings
```

### Scenario 3: eBPF Program Rejected by Verifier

```
Common verifier errors and fixes:

"R1 type=ctx expected=fp"
  → Using context pointer where frame pointer expected
  → Solution: copy context data to stack variable first

"unbounded loop"
  → Loop without provable bound
  → Solution: add explicit loop counter with #pragma unroll

"invalid indirect read from stack"
  → Reading uninitialized stack memory
  → Solution: initialize all stack variables before use

"back-edge from insn X to insn Y"
  → Backward jump (potential infinite loop)
  → Solution: use bounded loop (kernel 5.17+) or unroll

"permission denied"
  → Missing CAP_BPF / CAP_SYS_ADMIN
  → Solution: run as root or set capabilities
```

---

## 12. Q&A — Common Questions

**Q1: Why doesn't Linux use Ring 1 and Ring 2?**

Performance. Every ring transition has overhead. Using only Ring 0 and Ring 3 means only one privilege boundary to cross. Additionally, page-based protection (NX bit, read-only pages, SMAP/SMEP) provides finer-grained security than segment-based rings. Microkernels (like L4) that put drivers in Ring 1 pay a measurable performance penalty for the extra transitions.

**Q2: Why is `syscall` faster than `int 0x80`?**

`int 0x80` requires: IDT lookup → gate descriptor fetch → GDT lookup → privilege check → stack switch. Each step involves memory reads. `syscall` uses MSR registers pre-loaded at boot time: `MSR_LSTAR` (handler address), `MSR_STAR` (segment selectors). No memory lookups. The entire transition is hardwired in silicon.

**Q3: Can eBPF programs access arbitrary kernel memory?**

No. The verifier ensures all memory accesses go through approved helper functions (`bpf_probe_read_kernel`, `bpf_map_lookup_elem`, etc.). Direct pointer dereference of kernel addresses is forbidden. The verifier tracks the type and bounds of every register.

**Q4: What is the performance cost of KPTI?**

Depends on syscall frequency. Syscall-heavy workloads (database, web server) see 2-5% overhead. Computation-heavy workloads (scientific, ML training) see < 1%. With PCID support (most CPUs since Westmere/2010), the TLB flush cost is greatly reduced.

**Q5: How does VDSO handle time zone changes?**

VDSO provides raw kernel time (UTC nanoseconds). Time zone conversion is a userspace operation in libc. The kernel only updates the `vvar` page with clock source parameters, not time zone data.

**Q6: What happens if the kernel stack overflows?**

On x86_64, each task has a fixed kernel stack (usually 16 KB, configurable 8/16/32 KB via `THREAD_SIZE`). If a kernel function recurses too deeply:
- Without guard pages: silent memory corruption, eventual crash/panic.
- With `CONFIG_VMAP_STACK` (default since 4.9): kernel stack is vmalloc-backed with guard pages. Overflow triggers a `#PF` → double fault → IST-based handler → panic with stack trace.

**Q7: Explain SMAP and SMEP.**

**SMEP (Supervisor Mode Execution Prevention):** CR4 bit 20. If set, the CPU will `#GP` if Ring 0 tries to execute code from Ring 3 pages. Prevents ret2user attacks.

**SMAP (Supervisor Mode Access Prevention):** CR4 bit 21. If set, the CPU will `#GP` if Ring 0 tries to read/write Ring 3 pages. Prevents kernel from accidentally (or maliciously) accessing user memory. Kernel uses `copy_from_user()`/`copy_to_user()` which temporarily clear the AC flag in RFLAGS to allow controlled access.

---

## 13. Hands-On Exercises

### Exercise 1: Syscall Tracing

1. Write a minimal C program that prints "hello" and exits.
2. Compile statically: `gcc -static -o hello hello.c`.
3. Trace with `strace -c ./hello` and count total syscalls.
4. Now compile dynamically and compare. Explain the difference (dynamic linker opens many files).
5. Write the same program using raw `syscall()` and compare.

### Exercise 2: VDSO Benchmark

1. Benchmark `clock_gettime(CLOCK_MONOTONIC)` (VDSO-accelerated).
2. Benchmark `clock_gettime(CLOCK_MONOTONIC)` via raw `syscall(SYS_clock_gettime, ...)` (forces real syscall, bypasses VDSO).
3. Measure the difference. Expected: 5-10x faster via VDSO.
4. Use `perf stat` to compare instruction counts and cache behavior.

### Exercise 3: Interrupt Analysis

```bash
# Watch interrupt rates
watch -n 1 cat /proc/interrupts

# Tasks:
# 1. Identify the timer interrupt line. What is its frequency?
# 2. Generate network traffic (ping flood) and observe NIC interrupt changes.
# 3. Check /proc/irq/<N>/smp_affinity to see which CPUs handle each IRQ.
# 4. Pin an IRQ to a single CPU and observe the effect.
```

### Exercise 4: eBPF Exploration

```bash
# Install bpftrace

# 1. Count syscalls by type for 10 seconds:
bpftrace -e 'tracepoint:raw_syscalls:sys_enter {
    @[ksym(*(kaddr("sys_call_table") + args->id * 8))] = count();
} END { print(@, 20); }'

# 2. Trace context switches with scheduling latency:
bpftrace -e 'tracepoint:sched:sched_switch {
    printf("%-16s -> %-16s on CPU %d\n",
           args->prev_comm, args->next_comm, cpu);
}'

# 3. Write a custom BPF program that counts page faults per process.
# 4. Write an XDP program that drops ICMP packets (requires root).
```

### Exercise 5: MMIO Exploration

```bash
# 1. List PCI devices and their BAR (Base Address Register) mappings:
lspci -v | grep -A5 "Memory at"

# 2. Read /proc/iomem to see the physical address map:
cat /proc/iomem

# 3. Identify which regions are RAM vs MMIO.
# 4. Find your NIC's MMIO region and calculate its size.

# 5. Use devmem2 (if available) to read a device register:
# WARNING: reading wrong addresses can crash the system
# devmem2 0xFEE00020 w  # read LAPIC version register
```

### Exercise 6: Speculative Execution Side Channel Demo

```c
/* C: simplified Flush+Reload cache timing (educational only) */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <x86intrin.h>

#define CACHE_LINE 64

/* Probe array: 256 entries, each CACHE_LINE apart */
static uint8_t probe[256 * CACHE_LINE];

static inline uint64_t rdtsc_fence(void) {
    unsigned int aux;
    _mm_mfence();
    uint64_t tsc = __rdtscp(&aux);
    _mm_mfence();
    return tsc;
}

/* Flush all probe array entries from cache */
static void flush_probe(void) {
    for (int i = 0; i < 256; i++)
        _mm_clflush(&probe[i * CACHE_LINE]);
}

/* Time access to each probe entry; cached entries are fast */
static void reload_probe(void) {
    uint64_t threshold = 100; /* cycles; tune per CPU */
    for (int i = 0; i < 256; i++) {
        uint64_t start = rdtsc_fence();
        volatile uint8_t tmp = probe[i * CACHE_LINE];
        uint64_t elapsed = rdtsc_fence() - start;
        (void)tmp;
        if (elapsed < threshold && i != 0) /* skip 0, often noise */
            printf("  Cached: probe[%d] (%lu cycles)\n", i, elapsed);
    }
}

int main(void) {
    /* Demonstrate: access probe[42 * CACHE_LINE],
       then show that index 42 is cached */
    flush_probe();

    volatile uint8_t x = probe[42 * CACHE_LINE]; /* bring into cache */
    (void)x;

    printf("After accessing probe[42 * CACHE_LINE]:\n");
    reload_probe();
    /* Expected: index 42 shows fast access (< threshold) */

    return 0;
}
```

Tasks:
1. Compile with `gcc -O0 -msse2 -o flush_reload flush_reload.c`.
2. Run and observe which index shows as cached.
3. Change the accessed index and verify the output changes.
4. Explain how this technique could be combined with speculative execution to leak data.
5. Why is the threshold CPU-dependent?

### Exercise 7: DMA Coherency Exploration

```bash
# 1. List IOMMU groups
find /sys/kernel/iommu_groups/ -type l

# 2. Check if IOMMU is enabled
dmesg | grep -i iommu

# 3. List DMA allocations for a device
cat /sys/kernel/debug/dma-buf/bufinfo 2>/dev/null

# 4. Check IOMMU page faults
dmesg | grep -i "DMAR.*fault"
```

---

## 14. Deep Dive: CPU Cache Architecture and Kernel Interaction

### 14.1 Cache Hierarchy

```
  ┌─────────────────────────────────────────────────────────┐
  │  CPU Core 0                    CPU Core 1               │
  │  ┌──────────────────────┐     ┌──────────────────────┐  │
  │  │  L1i Cache   32 KB   │     │  L1i Cache   32 KB   │  │
  │  │  (instruction, 4 cyc)│     │  (instruction, 4 cyc)│  │
  │  │  L1d Cache   48 KB   │     │  L1d Cache   48 KB   │  │
  │  │  (data, 4-5 cycles)  │     │  (data, 4-5 cycles)  │  │
  │  ├──────────────────────┤     ├──────────────────────┤  │
  │  │  L2 Cache    1.25 MB │     │  L2 Cache    1.25 MB │  │
  │  │  (unified, 12 cycles)│     │  (unified, 12 cycles)│  │
  │  └─────────┬────────────┘     └─────────┬────────────┘  │
  │            │                             │               │
  │  ┌─────────┴─────────────────────────────┴────────────┐  │
  │  │              L3 Cache (shared)                      │  │
  │  │              30-50 MB, ~40-50 cycles                │  │
  │  │              Inclusive or non-inclusive              │  │
  │  └─────────────────────────┬──────────────────────────┘  │
  │                            │                              │
  └────────────────────────────┼──────────────────────────────┘
                               │
                     ┌─────────┴──────────┐
                     │  DRAM (Main Memory) │
                     │  ~60-100 ns         │
                     │  ~100 cycles        │
                     └────────────────────┘
```

### 14.2 Cache Coherence: MESI Protocol

When multiple cores share data, the hardware maintains coherence:

```
MESI States per cache line:

┌───────────┬──────────────────────────────────────────┐
│ Modified  │ This core has the only copy, it's dirty  │
│           │ Must write back before others can read   │
├───────────┼──────────────────────────────────────────┤
│ Exclusive │ This core has the only copy, it's clean  │
│           │ Can be promoted to Modified without bus   │
├───────────┼──────────────────────────────────────────┤
│ Shared    │ Multiple cores have clean copies          │
│           │ Must invalidate others before writing     │
├───────────┼──────────────────────────────────────────┤
│ Invalid   │ This line is not valid                    │
│           │ Must fetch from memory or another core    │
└───────────┴──────────────────────────────────────────┘

State transitions:
  Read hit:  M→M, E→E, S→S (no bus transaction)
  Write hit: M→M, E→M, S→M (invalidate others)
  Read miss: I→E (if no other copy) or I→S (if shared)
  Write miss: I→M (invalidate all others)
```

### 14.3 Cache Line Bouncing and False Sharing

**False sharing** occurs when two cores write to different variables that happen to share the same cache line (typically 64 bytes):

```c
/* C: false sharing example */
#include <pthread.h>
#include <stdio.h>
#include <time.h>

#define N 100000000

/* BAD: two counters on the same cache line */
struct {
    long counter_a;  /* bytes 0-7 */
    long counter_b;  /* bytes 8-15 — same 64-byte cache line! */
} shared_bad;

/* GOOD: pad to separate cache lines */
struct {
    long counter_a;
    char pad[64 - sizeof(long)];  /* push to next cache line */
    long counter_b;
} shared_good;

void *thread_a(void *arg) {
    long *counter = (long *)arg;
    for (long i = 0; i < N; i++)
        (*counter)++;
    return NULL;
}

int main(void) {
    pthread_t t1, t2;
    struct timespec start, end;

    /* BAD version */
    clock_gettime(CLOCK_MONOTONIC, &start);
    pthread_create(&t1, NULL, thread_a, &shared_bad.counter_a);
    pthread_create(&t2, NULL, thread_a, &shared_bad.counter_b);
    pthread_join(t1, NULL);
    pthread_join(t2, NULL);
    clock_gettime(CLOCK_MONOTONIC, &end);
    double bad_time = (end.tv_sec - start.tv_sec) +
                      (end.tv_nsec - start.tv_nsec) / 1e9;

    /* GOOD version */
    clock_gettime(CLOCK_MONOTONIC, &start);
    pthread_create(&t1, NULL, thread_a, &shared_good.counter_a);
    pthread_create(&t2, NULL, thread_a, &shared_good.counter_b);
    pthread_join(t1, NULL);
    pthread_join(t2, NULL);
    clock_gettime(CLOCK_MONOTONIC, &end);
    double good_time = (end.tv_sec - start.tv_sec) +
                       (end.tv_nsec - start.tv_nsec) / 1e9;

    printf("False sharing:  %.3f s\n", bad_time);
    printf("Padded:         %.3f s\n", good_time);
    printf("Speedup:        %.1fx\n", bad_time / good_time);

    return 0;
}
```

Typical result: the padded version runs 3-10x faster because each core owns its cache line exclusively.

```bash
# Detect false sharing with perf
perf c2c record -g -- ./my_app
perf c2c report
# Shows "hot" cache lines that bounce between cores
```

### 14.4 Cache and Kernel Context Switches

Context switches pollute caches:

| Event | Cache impact |
|-------|-------------|
| Thread switch (same process) | L1/L2 data cache cold (~50-70% miss initially) |
| Process switch | L1/L2 cold + potential L3 cold |
| Process switch + TLB flush | All of above + TLB rebuild (~1000s of walks) |
| KPTI CR3 switch | iTLB/dTLB flush for kernel entries |

**Measuring cache pollution from context switches:**
```bash
perf stat -e cache-misses,cache-references,context-switches \
    -a -- sleep 10
# High cache-misses/context-switches ratio = expensive switching
```

---

## 15. Deep Dive: MSR (Model-Specific Registers)

### 15.1 Critical MSRs for Kernel Boundary

| MSR | Address | Purpose |
|-----|---------|---------|
| `MSR_LSTAR` | `0xC0000082` | `syscall` target RIP (64-bit) |
| `MSR_STAR` | `0xC0000081` | `syscall`/`sysret` CS/SS selectors |
| `MSR_SYSCALL_MASK` | `0xC0000084` | RFLAGS mask on `syscall` |
| `MSR_GS_BASE` | `0xC0000101` | GS base address (user) |
| `MSR_KERNEL_GS_BASE` | `0xC0000102` | GS base address (kernel, for `swapgs`) |
| `MSR_FS_BASE` | `0xC0000100` | FS base address (TLS in user space) |
| `IA32_EFER` | `0xC0000080` | Extended feature enable (SCE, NXE, LMA) |
| `IA32_PAT` | `0x00000277` | Page attribute table (cache policies) |
| `IA32_SPEC_CTRL` | `0x00000048` | Speculation control (IBRS, STIBP, SSBD) |

### 15.2 Reading MSRs from Userspace

```bash
# Read MSR_LSTAR (syscall entry point)
rdmsr 0xC0000082
# Output: ffffffff82000000 (example kernel address)

# Read IA32_SPEC_CTRL
rdmsr 0x48
# Bit 0: IBRS, Bit 1: STIBP, Bit 2: SSBD

# Install msr-tools: apt install msr-tools
# Load msr kernel module: modprobe msr
```

---

## 16. Deep Dive: Virtualization and the CPU Boundary

### 16.1 Hardware Virtualization Extensions

```
Privilege levels with VT-x/AMD-V:

  Ring -1: VMX Root Mode (Hypervisor)
           ┌──────────────────────────────┐
           │  KVM / Xen / VMware ESXi     │
           │  Full hardware control        │
           │  Intercepts VM exits          │
           └──────────────┬───────────────┘
                          │ VM Entry / VM Exit
                          ▼
  Ring 0:  VMX Non-Root Mode (Guest Kernel)
           ┌──────────────────────────────┐
           │  Guest Linux kernel           │
           │  Thinks it's at Ring 0        │
           │  Privileged ops cause VM Exit │
           └──────────────┬───────────────┘
                          │ syscall / sysret
                          ▼
  Ring 3:  VMX Non-Root Mode (Guest User)
           ┌──────────────────────────────┐
           │  Guest applications           │
           │  Normal user mode             │
           └──────────────────────────────┘
```

### 16.2 VM Exit Causes

When the guest executes certain instructions, the CPU traps to the hypervisor:

| Cause | Typical cost | Example |
|-------|-------------|---------|
| I/O instruction | ~1-5 μs | `IN`/`OUT` to emulated device |
| CR3 write | ~0.5-2 μs | Address space switch (mitigated by EPT) |
| MSR access | ~0.5-1 μs | Guest reads/writes controlled MSR |
| CPUID | ~1-3 μs | Feature enumeration |
| External interrupt | ~0.5-1 μs | Hardware IRQ during guest execution |
| EPT violation | ~1-5 μs | Nested page fault |
| HLT | ~0.5-1 μs | Guest idle |

### 16.3 EPT (Extended Page Tables) / NPT (Nested Page Tables)

Without EPT, every guest page table modification causes a VM Exit (shadow page tables). With EPT:

```
Guest Virtual Address
       │
       │ Guest Page Tables (managed by guest kernel)
       ▼
Guest Physical Address
       │
       │ EPT/NPT (managed by hypervisor)
       ▼
Host Physical Address (actual DRAM)

TLB walk: 4 guest levels × 4 EPT levels = up to 24 memory accesses
          (in the worst case with no TLB hits at any level)
```

### 16.4 VMCS (Virtual Machine Control Structure)

The VMCS is a 4 KB page that stores guest state, host state, and control fields:

```
VMCS Fields (key ones):
┌──────────────────────────────────────────┐
│  Guest State Area:                        │
│    CR0, CR3, CR4                          │
│    RSP, RIP, RFLAGS                       │
│    CS, DS, ES, SS, GS, FS                 │
│    GDTR, IDTR, LDTR, TR                   │
│    IA32_EFER, IA32_PAT                    │
├──────────────────────────────────────────┤
│  Host State Area:                         │
│    CR0, CR3, CR4                          │
│    RSP, RIP                               │
│    CS, DS, ES, SS, GS, FS, TR            │
├──────────────────────────────────────────┤
│  VM-Execution Control Fields:             │
│    Pin-based controls (interrupt handling) │
│    Proc-based controls (which ops exit)   │
│    Exception bitmap (which exceptions exit)│
│    EPT pointer                             │
│    MSR bitmap (which MSRs cause exit)     │
├──────────────────────────────────────────┤
│  VM-Exit Information Fields:              │
│    Exit reason, exit qualification         │
│    Guest-linear address, guest-phys addr   │
│    VM-instruction error                    │
└──────────────────────────────────────────┘
```

---

## 17. Deep Dive: swapgs and Kernel Entry

### 17.1 The swapgs Instruction

On syscall/interrupt entry from user mode, the kernel needs access to per-CPU data. The GS register holds the base address, but it currently points to user data.

```
User mode:
  GS base → user TLS (Thread-Local Storage)
  KernelGSBase MSR → per-CPU kernel data

After swapgs:
  GS base → per-CPU kernel data
  KernelGSBase MSR → user TLS (saved for later)

Kernel can now access:
  gs:[0]    → current task_struct pointer
  gs:[N]    → per-CPU variables
  gs:[M]    → kernel stack pointer for this CPU
```

### 17.2 The Spectre v1 swapgs Gadget

If an interrupt arrives while the kernel is in the process of executing `swapgs`, speculative execution could proceed with the wrong GS base, leaking kernel data. Mitigated by:
- `lfence` before conditional `swapgs`.
- Careful assembly in `entry_SYSCALL_64` and interrupt handlers.

### 17.3 Full Kernel Entry Sequence (Annotated)

```nasm
; entry_SYSCALL_64 (simplified from arch/x86/entry/entry_64.S)

entry_SYSCALL_64:
    swapgs                      ; GS now points to per-CPU data
    movq    %rsp, PER_CPU_VAR(cpu_tss_rw + TSS_sp2)
                                ; save user RSP in per-CPU area
    movq    PER_CPU_VAR(cpu_current_top_of_stack), %rsp
                                ; load kernel stack pointer

    ; Build pt_regs on the kernel stack
    pushq   $__USER_DS          ; user SS
    pushq   PER_CPU_VAR(cpu_tss_rw + TSS_sp2)
                                ; user RSP (saved above)
    pushq   %r11                ; user RFLAGS (saved by syscall)
    pushq   $__USER_CS          ; user CS
    pushq   %rcx                ; user RIP (saved by syscall)
    pushq   %rax                ; syscall number (orig_rax)

    ; Push remaining registers
    pushq   %rdi %rsi %rdx %rcx %rax %r8 %r9 %r10 %r11
    pushq   %rbx %rbp %r12 %r13 %r14 %r15

    ; Call C handler
    movq    %rsp, %rdi          ; first arg = pointer to pt_regs
    call    do_syscall_64       ; dispatches to sys_call_table[rax]

    ; Return path
    ; ... restore registers ...
    ; ... check for signals, schedule ...
    swapgs                      ; restore user GS
    sysretq                     ; return to Ring 3
```

---

## 18. Summary Cheat Sheet

```
┌─────────────────────────────────────────────────────────────────┐
│              CPU & KERNEL BOUNDARY CHEAT SHEET                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PRIVILEGE: Ring 0 (kernel) vs Ring 3 (user)                    │
│    CPL in CS register; checked on every memory access           │
│    Privileged instructions: MOV CRx, WRMSR, HLT, CLI, IN/OUT   │
│                                                                 │
│  SYSCALL:                                                       │
│    User: RAX=nr, RDI-R9=args → syscall instruction              │
│    CPU:  RCX=RIP, R11=RFLAGS, RIP=MSR_LSTAR, CPL=0             │
│    Kernel: swapgs, switch RSP, push regs, call handler          │
│    Return: restore regs, swapgs, sysretq                        │
│    Cost: ~100-200 ns                                            │
│                                                                 │
│  VDSO:                                                          │
│    Kernel maps code+data pages into every process               │
│    clock_gettime avoids syscall entirely (~20-40 ns)            │
│                                                                 │
│  INTERRUPTS:                                                    │
│    IDT[vector] → handler address + privilege check              │
│    Top half (fast, IRQs off) → bottom half (deferred work)      │
│    LAPIC per-CPU, I/O APIC for external devices                 │
│                                                                 │
│  DMA:                                                           │
│    Device reads/writes memory directly (no CPU)                 │
│    IOMMU provides address translation + isolation               │
│    Scatter-gather for non-contiguous memory                     │
│                                                                 │
│  eBPF:                                                          │
│    Verified, JIT-compiled programs in kernel                    │
│    Tracing (kprobe, tracepoint), networking (XDP, TC),          │
│    security (LSM), scheduling (sched_ext)                       │
│                                                                 │
│  SPECTRE/MELTDOWN:                                              │
│    Meltdown: read kernel via speculation → KPTI                 │
│    Spectre v1: bounds bypass → lfence                           │
│    Spectre v2: BTB poisoning → retpoline / IBRS                 │
│    Cost: 1-5% syscall overhead (with PCID)                      │
│                                                                 │
│  VIRTUALIZATION:                                                │
│    VT-x adds VMX root (Ring -1) for hypervisor                  │
│    VM Exit on privileged ops (~0.5-5 μs)                       │
│    EPT eliminates shadow page table exits                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 19. Deep Dive: CPU Architecture Features Affecting Kernel Design

### 19.1 SMAP and SMEP

**SMEP (Supervisor Mode Execution Prevention):** CR4 bit 20.
- CPU will `#GP` if Ring 0 tries to execute code from a Ring 3 page.
- Prevents ret2user attacks where an attacker overwrites a kernel function pointer to jump to user-space shellcode.
- Enabled by default in Linux since 3.0.

**SMAP (Supervisor Mode Access Prevention):** CR4 bit 21.
- CPU will `#GP` if Ring 0 tries to read or write Ring 3 pages.
- Prevents the kernel from accidentally dereferencing user-controlled pointers.
- Kernel uses `copy_from_user()` / `copy_to_user()` which temporarily set the AC (Alignment Check) flag via `stac`/`clac` instructions to allow controlled access.

```
Without SMAP:
  Kernel code can read/write user memory directly
  → Exploitable: attacker controls user page content

With SMAP:
  Kernel access to user pages → #GP fault
  Except: stac instruction sets AC flag (temporary whitelist)
  
  copy_from_user(kernel_buf, user_ptr, len):
    stac               ; allow user page access
    rep movsb           ; copy bytes
    clac               ; revoke user page access
```

### 19.2 PCID (Process Context Identifiers) Deep Dive

```
Without PCID:
  Context switch → write CR3 → TLB fully flushed
  Next process starts with empty TLB → thousands of TLB misses

With PCID (CR4.PCIDE = 1):
  Each address space gets a 12-bit tag (0-4095)
  TLB entries tagged with PCID
  CR3 write with bit 63 set = "don't flush"
  TLB entries from other PCIDs remain valid
  
  INVPCID instruction for selective invalidation:
    Type 0: individual address + PCID
    Type 1: single PCID (all entries)
    Type 2: all entries (all PCIDs) except global
    Type 3: all entries including global
```

Impact on KPTI: Without PCID, KPTI requires two full TLB flushes per syscall (enter kernel, return to user). With PCID, the user and kernel page tables get different PCIDs, and TLB entries are preserved across switches.

### 19.3 CET (Control-Flow Enforcement Technology)

Intel CET (since 11th gen / Tiger Lake) provides hardware-based control flow integrity:

**Shadow Stack:**
- A second, read-only stack that stores only return addresses.
- On `CALL`: CPU pushes return address to both regular stack and shadow stack.
- On `RET`: CPU compares return addresses from both stacks.
- Mismatch → `#CP` (Control Protection) exception.
- Prevents ROP (Return-Oriented Programming) attacks.

**Indirect Branch Tracking (IBT):**
- Every valid indirect branch target must start with `ENDBR64` instruction.
- If an indirect jump/call lands on a non-`ENDBR64` instruction → `#CP` exception.
- Prevents JOP (Jump-Oriented Programming) attacks.

```
Shadow Stack Protection:

Regular Stack:      Shadow Stack:
┌──────────┐       ┌──────────┐
│ ret addr │  ═══  │ ret addr │  ← Must match!
├──────────┤       ├──────────┤
│ local var│       │ ret addr │  (previous frame)
├──────────┤       ├──────────┤
│ ret addr │  ═══  │ ret addr │  ← Must match!
└──────────┘       └──────────┘

Attacker overwrites ret addr on regular stack:
  RET → compare: regular stack ≠ shadow stack → #CP exception
```

### 19.4 FRED (Flexible Return and Event Delivery)

FRED (Intel, announced for Arrow Lake) modernizes exception/interrupt delivery:
- Replaces IDT-based delivery with a new mechanism.
- Separate kernel and user event stacks.
- Eliminates need for IST entries (cleaner NMI handling).
- Automatic `swapgs` equivalent (no more swapgs gadget vulnerabilities).
- Expected to reduce syscall and interrupt handling overhead by 10-20%.

---

## 20. Deep Dive: ARM64 (AArch64) Comparison

### 20.1 Privilege Levels: Exception Levels

ARM64 uses **Exception Levels (EL)** instead of rings:

```
ARM64 Exception Levels:

  EL3: Secure Monitor (firmware, TrustZone)
       ├── Handles SMC (Secure Monitor Call)
       └── Switches between Secure/Non-Secure worlds
       
  EL2: Hypervisor
       ├── Handles HVC (Hypervisor Call)
       └── Stage-2 page translation (like EPT)
       
  EL1: Kernel (OS)
       ├── Handles SVC (Supervisor Call) ← equivalent to syscall
       └── Stage-1 page translation
       
  EL0: User Application
       └── Can only execute SVC to request services
```

### 20.2 System Call Comparison: x86_64 vs ARM64

| Aspect | x86_64 | ARM64 |
|--------|--------|-------|
| Instruction | `syscall` | `svc #0` |
| Syscall number | `RAX` | `X8` |
| Arguments | `RDI, RSI, RDX, R10, R8, R9` | `X0-X5` |
| Return value | `RAX` | `X0` |
| Clobbered | `RCX, R11` | None (separate registers) |
| Stack switch | Manual (`swapgs` + load RSP) | Automatic (hardware saves SP_EL0) |
| Return | `sysretq` | `eret` |

### 20.3 ARM Pointer Authentication (PAC)

ARM64 (ARMv8.3+) adds hardware pointer signing:
- Return addresses and function pointers are signed with a per-process key.
- On dereference, the signature is verified.
- Corrupted pointers (e.g., from buffer overflow) fail verification.
- Provides hardware ROP/JOP mitigation similar to Intel CET.

### 20.4 ARM Memory Tagging Extension (MTE)

ARMv8.5+ adds 4-bit tags to every 16-byte memory granule:
- `malloc` assigns a random tag to each allocation.
- Pointer top bits carry the expected tag.
- Hardware checks tag on every access.
- Mismatch → fault (use-after-free, buffer overflow detected by hardware).
- Similar goal to AddressSanitizer but with near-zero overhead.

---

## 21. Advanced Q&A

**Q8: How does `strace` actually work?**

`strace` uses `ptrace(PTRACE_SYSCALL)` to stop the target at every syscall entry and exit. On entry, it reads the syscall number and arguments from registers. On exit, it reads the return value. This adds two context switches per syscall (stop + resume), making traced processes 10-100x slower.

Modern alternative: use eBPF tracepoints (`tracepoint:raw_syscalls:sys_enter/sys_exit`) which have near-zero overhead because the BPF program runs in kernel context without stopping the target.

**Q9: Why does Linux have both `sysenter` (Intel 32-bit) and `syscall` (AMD64)?**

Historical divergence. Intel designed `sysenter`/`sysexit` for 32-bit mode. AMD designed `syscall`/`sysret` for 64-bit mode. In x86_64 long mode, both Intel and AMD support `syscall`/`sysret`, and that is what Linux uses. `sysenter` is only used in 32-bit compatibility mode.

**Q10: What is the vsyscall page and why was it deprecated?**

`vsyscall` was the predecessor to VDSO: a single page mapped at a fixed address (`0xffffffffff600000`) containing userspace implementations of `gettimeofday`, `time`, and `getcpu`. It was deprecated because:
1. Fixed address → ASLR bypass (attackers could predict gadget locations).
2. Single page → limited functionality.
3. VDSO uses ASLR, supports more functions, and is more flexible.

Linux still emulates vsyscall for compatibility (`CONFIG_X86_VSYSCALL_EMULATION`) but traps to the kernel instead of executing directly, adding syscall overhead.

**Q11: What is KASAN and how does it interact with the kernel boundary?**

KASAN (Kernel Address Sanitizer) instruments kernel code at compile time to detect:
- Out-of-bounds access to kernel heap/stack/globals
- Use-after-free of kernel objects
- Double-free

It works by maintaining a shadow memory region (1 byte per 8 bytes of kernel memory) that tracks allocation state. Every memory access is instrumented with a shadow check. This adds ~2-3x memory overhead and ~50% CPU overhead, so it is used only in development/testing builds.

**Q12: Explain the sysret bug (CVE-2012-0217).**

The `sysretq` instruction checks if the return RIP is canonical (bits 63-48 must all be 0 or all be 1). If non-canonical, the CPU raises `#GP`. But `sysretq` checks this AFTER switching to Ring 3, meaning the `#GP` fires in Ring 3 context but with the kernel stack pointer still loaded. An attacker who can control RIP (e.g., via `ptrace` on a child) can exploit this to execute code with a kernel stack. The fix: Linux validates RIP before executing `sysretq` and falls back to `iretq` for non-canonical addresses.

---

## 22. Additional Exercises

### Exercise 8: Kernel Module for MSR Reading

```c
/* Kernel module: read and display critical MSRs */
#include <linux/module.h>
#include <linux/kernel.h>
#include <asm/msr.h>

static int __init msr_reader_init(void) {
    u64 val;

    rdmsrl(MSR_LSTAR, val);
    pr_info("MSR_LSTAR (syscall entry): 0x%llx\n", val);

    rdmsrl(MSR_STAR, val);
    pr_info("MSR_STAR (selectors): 0x%llx\n", val);

    rdmsrl(MSR_SYSCALL_MASK, val);
    pr_info("MSR_SYSCALL_MASK: 0x%llx\n", val);

    rdmsrl(MSR_GS_BASE, val);
    pr_info("MSR_GS_BASE: 0x%llx\n", val);

    return 0;
}

static void __exit msr_reader_exit(void) {
    pr_info("MSR reader unloaded\n");
}

module_init(msr_reader_init);
module_exit(msr_reader_exit);
MODULE_LICENSE("GPL");
```

Tasks:
1. Build and load this module (`insmod`).
2. Check `dmesg` for the output.
3. Verify MSR_LSTAR matches the address of `entry_SYSCALL_64` in `/proc/kallsyms`.
4. Compare MSR_SYSCALL_MASK with the RFLAGS bits that should be cleared on syscall entry.

### Exercise 9: Write a Minimal VDSO-like Function

1. Create a shared memory page between kernel and userspace (via a kernel module).
2. In the kernel module, update a counter on every timer tick.
3. In userspace, read the counter via the shared page (no syscall).
4. Compare performance with reading via `ioctl` syscall.
5. This demonstrates the VDSO principle at a basic level.

### Exercise 10: Hardware Interrupt Latency Measurement

```bash
# Use cyclictest (from rt-tests package) to measure IRQ-to-userspace latency
cyclictest --mlockall --priority=80 --interval=1000 --distance=0 \
    --loops=100000 --histogram=200

# Typical results:
# Min: 1-3 μs, Avg: 3-8 μs, Max: 10-50 μs (non-RT kernel)
# Min: 1-2 μs, Avg: 2-5 μs, Max: 5-15 μs (PREEMPT_RT kernel)

# Tasks:
# 1. Run on default kernel and record max latency
# 2. Run under load (stress -c $(nproc))
# 3. Compare with PREEMPT_RT kernel if available
# 4. Identify which IRQ or kernel path causes worst-case latency
```

---

## 23. Further Reading

- **Intel SDM (Software Developer Manual):** Vol. 3, Chapters 6 (Interrupts), 7 (Task Management), 10 (APIC)
- **AMD64 Architecture Programmer's Manual:** Vol. 2, System Programming
- **ARM Architecture Reference Manual (ARMv8-A):** Exception handling, system registers
- **"Spectre Attacks: Exploiting Speculative Execution"** — Kocher et al., 2018
- **"Meltdown: Reading Kernel Memory from User Space"** — Lipp et al., 2018
- **Linux kernel source:** `arch/x86/entry/entry_64.S` (syscall entry), `arch/x86/kernel/idt.c`
- **"BPF Performance Tools"** by Brendan Gregg
- **bpftrace reference guide:** https://github.com/bpftrace/bpftrace/blob/master/docs/reference_guide.md
- **Retpoline whitepaper:** Google, "Retpoline: A Branch Target Injection Mitigation"
- **LWN KPTI articles:** https://lwn.net/Articles/741878/
- **Intel CET specification:** Control-Flow Enforcement Technology Preview
- **man pages:** `syscall(2)`, `vdso(7)`, `bpf(2)`, `io_uring(7)`, `ptrace(2)`
- **OSDev wiki:** GDT, IDT, APIC, TSS, VMCS documentation
- **KVM documentation:** `Documentation/virt/kvm/` in kernel source
- **RISC-V Privileged Specification:** Machine/Supervisor/User modes comparison
- **"A Guide to Kernel Exploitation"** by Perla & Oldani — kernel exploit techniques
- **Eli Bendersky's blog:** Excellent articles on x86 instruction encoding and syscalls
- **cpu.land:** Interactive visual guides to CPU architecture concepts
- **Agner Fog's optimization manuals:** Instruction latency tables for Intel/AMD CPUs
- **"Computer Architecture: A Quantitative Approach"** by Hennessy & Patterson

---

*End of Module 1.1.a — The CPU & The Kernel Boundary Deep Dive*

---

## Appendix: Quick Reference — x86_64 Syscall Registers

```
┌──────────────┬────────────────────────────────────────┐
│  Register    │  Usage in syscall convention            │
├──────────────┼────────────────────────────────────────┤
│  RAX         │  Syscall number (input) / return value  │
│  RDI         │  Argument 1                             │
│  RSI         │  Argument 2                             │
│  RDX         │  Argument 3                             │
│  R10         │  Argument 4 (NOT RCX — used by CPU)     │
│  R8          │  Argument 5                             │
│  R9          │  Argument 6                             │
│  RCX         │  Destroyed (CPU saves RIP here)         │
│  R11         │  Destroyed (CPU saves RFLAGS here)      │
│  RBX, RBP    │  Preserved across syscall               │
│  R12-R15     │  Preserved across syscall               │
│  RSP         │  Preserved (user stack pointer)         │
└──────────────┴────────────────────────────────────────┘
```
