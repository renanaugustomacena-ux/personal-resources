---
corso: "Cybersecurity Masterclass"
fase: "Domain 17 — Physical & Hardware Security"
modulo: "17.3"
titolo: "PCB Reverse Engineering and Chip-Level Analysis"
versione: "SAE AS6171/AS6081, Degate 0.1.x, flashrom 1.4, binwalk 2.4, sigrok/PulseView 0.5"
livello: "Advanced"
prerequisiti:
  - "Domain 17.1 (physical security, side-channel overview)"
  - "Domain 17.2 (fault injection — decapsulation context, die-level access)"
  - "PCB fundamentals (layer stackup, vias, trace routing, component packages)"
  - "Firmware reverse engineering basics (Domain 12 — Ghidra, disassembly)"
  - "Soldering skills (hot-air rework, fine-pitch QFN/BGA, SPI flash probing)"
obiettivi:
  - "Perform multi-layer PCB reverse engineering using X-ray imaging, chemical delayering, and Gerber reconstruction to extract a complete connectivity netlist"
  - "Identify and extract firmware from SPI NOR, NAND, eMMC, and UFS memory devices using flashrom, chip-off rework, and in-system reading techniques"
  - "Decapsulate IC packages using fuming nitric acid, plasma ashing, and mechanical methods while preserving bond wires for functional analysis"
  - "Detect counterfeit ICs using SAE AS6171 workflow including visual inspection, X-ray comparison, SAM, XRF/FTIR material analysis, and destructive physical analysis"
  - "Extract gate-level netlists from delayered die images using optical microscopy, SEM, FIB circuit edit, and automated cell-matching tools (Degate)"
tag: [pcb-reverse-engineering, chip-decapsulation, memory-extraction, counterfeit-detection, die-analysis, sem, fib, nand, emmc, hardware-trojans, x-ray, flashrom, binwalk]
---

# Domain 17, Chapter 17C — PCB Reverse Engineering and Chip-Level Analysis

> **Learning Objectives.** After completing this module the student will be able to: (1) execute a full PCB reverse engineering workflow — visual inspection, layer counting, X-ray CT imaging, chemical/mechanical delayering, image stitching, vectorization, and Gerber reconstruction — to produce a complete connectivity netlist; (2) extract firmware from embedded memory devices (SPI NOR via flashrom/CH341A, parallel NAND via chip-off rework, eMMC via ISP/EMMC adapter, UFS via protocol analyzer) and perform initial triage with binwalk entropy analysis; (3) decapsulate IC packages using fuming nitric acid, O2 plasma ashing, and CNC micro-milling while preserving bond wires, and perform die-level optical/SEM/FIB analysis; (4) detect counterfeit ICs using the SAE AS6171 structured workflow including stereomicroscope/UV visual inspection, X-ray overlay comparison, scanning acoustic microscopy, XRF/FTIR material analysis, and destructive physical analysis; (5) extract gate-level netlists from delayered die images using standard cell template matching, Degate, and automated image-processing pipelines, and verify against known-good functional behavior.

> **Scope.** PCB reverse engineering methodology: visual inspection and documentation (photography, microscopy), multi-layer PCB identification (layer counting, via analysis), X-ray imaging (2D projection, X-ray CT/micro-CT, laminography), chemical delayering (cupric chloride, sodium hydroxide, mechanical peel-back), mechanical cross-sectioning and grinding, automated image stitching and PCB vectorization (PCBFlow, altium import, Gerber reconstruction), signal tracing and connectivity mapping. Component identification: IC package identification (BGA, QFN, QFP, TSOP, SOIC, CSP, WLP, PoP), marking analysis (date codes, lot codes, manufacturer logos), unmarked/remarked chip identification (decapsulation, die marking analysis, electron microscopy), passive component analysis (0201/0402 identification, measurement, function inference), counterfeit IC detection (visual, X-ray, electrical, material analysis). Chip decapsulation: chemical decapsulation (fuming nitric acid 98%, red fuming HNO₃, sulfuric acid + hydrogen peroxide piranha etch, proprietary decapsulants), mechanical decapsulation (CNC milling, manual grinding, dental burs), laser decapsulation (Nd:YAG ablation), plasma decapsulation (O₂ plasma asher), semi-destructive vs destructive methods, bond wire preservation, rebonding. Die-level analysis: optical microscopy (bright-field, dark-field, DIC/Nomarski), scanning electron microscopy (SEM — SE, BSE, EDS/EDX), focused ion beam (FIB — milling, deposition, circuit edit, TEM lamella preparation), transmission electron microscopy (TEM for sub-10nm node imaging), die delayering (wet etch chemistry per layer — metal/oxide/polysilicon, dry etch/RIE, CMP-based polishing), metal layer imaging and stitching, standard cell identification and library matching, gate-level netlist extraction (Degate, RE-NNET, Chipjuice), full-chip reverse engineering workflow. Memory extraction: NAND flash deep dive (raw NAND, page structure, OOB/spare area, ECC algorithms, bad block tables, FTL reconstruction, wear leveling artifacts), NOR flash (SPI NOR command set, CFI query, parallel NOR pinout, read disturb), eMMC deep dive (JEDEC standard, partitions — boot0/boot1/user/RPMB/GPP, CID/CSD/EXT_CSD registers, eMMC protocol analyzer, RPMB authentication key recovery, eMMC forensic tools), UFS (SCSI command set adaptation, LUN structure, UFS descriptor hierarchy, RPMB in UFS), EEPROM (I²C/SPI interface, page write, wear characteristics), OTP/eFuse reading (electrical probing, FIB cross-section, read-back circuits), in-system vs chip-off reading, chip-off forensic methodology (hot-air rework, BGA reballing, thermal profile optimization). Hardware Trojans: taxonomy (combinational vs sequential vs analog, activation — always-on/time-bomb/trigger-based, payload — information leakage/denial-of-service/kill-switch), detection methodologies (golden reference comparison, side-channel fingerprinting, formal verification, path-delay analysis, optical inspection/image comparison), notable research (Illinois Trojans, A2 Trojan, analog Trojans evading digital inspection), real-world allegations and investigations, prevention (split manufacturing, logic locking/camouflaging, runtime Trojan detection via side-channels). IC counterfeit detection: taxonomy (recycled, remarked, cloned, overproduced, defective/out-of-spec, tampered), detection methods (visual/X-ray/SAM, electrical parametric testing, material analysis — XRF/FTIR/ion chromatography, authentication — PUF/DNA marking/blockchain provenance), SAE AS6171/AS6081 standards, GIDEP/ERAI reporting. Defensive PCB and chip design: anti-tamper PCB design (BGA underfill, buried vias, impedance-matched trace routing, ground flood obfuscation), conformal coating and potting, anti-reverse-engineering IC design (camouflaged gates, active shields, PUF-based authentication, logic locking — SAT-attack-resistant schemes), ROM/fuse protection (anti-FIB coatings, metal mesh shields).
>
> **Audience.** Hardware reverse engineers analyzing devices for vulnerability assessment, forensic examiners extracting data from embedded systems, supply chain security professionals detecting counterfeit components, detection engineers understanding hardware-attack prerequisites, and architects designing tamper-resistant hardware.
>
> **Prerequisites.** Domain 17, Chapter 17A (side-channel analysis — power measurement setups, EM probes). Domain 17, Chapter 17B (fault injection — decapsulation context, die-level access). Domain 12 (firmware reverse engineering — what to do with extracted firmware images). Domain 28 (IoT protocols — embedded device context).

---

## 1. PCB reverse engineering methodology

### 1.1 Visual inspection and documentation

Every hardware reverse engineering campaign begins with thorough documentation of the target board. High-resolution photography captures the board's top and bottom surfaces, capturing component placement, silkscreen markings, test points, and connector pinouts. A systematic photographic workflow uses a calibrated macro lens (or stereomicroscope with camera adapter) to photograph each board quadrant at sufficient resolution to read component markings and trace widths. The photographs are stitched into a single high-resolution composite image that serves as the reference map for all subsequent analysis.

Test points, labeled headers, and unpopulated footprints are particularly valuable to the reverse engineer. Test points often correspond to JTAG/SWD signals, UART TX/RX, power rails, or diagnostic buses that the manufacturer uses during production testing and debugging. Unpopulated footprints may indicate debug headers that were designed in but not populated in production units — populating these footprints (soldering on the appropriate connector) may restore debug access. Silkscreen labels near these points (common labels include "TP1", "TXD", "RXD", "JTAG", "DBG", "SWD", "RST", "GND") provide direct clues about their function. On boards without silkscreen labels, continuity testing with a multimeter traces each test point to the IC pin it connects to, identifying its function by reference to the IC's datasheet.

Board dimensions, mounting hole patterns, and connector types provide context about the product class and intended application. An automotive ECU has different design patterns (conformal coating, high-temperature rated components, CAN bus transceivers) than a consumer IoT device (commodity SoC, Wi-Fi module, cost-optimized layout). This context informs the analyst's expectations about security features, debug lockout level, and countermeasure sophistication.

### 1.2 Layer identification and counting

Determining the number of PCB layers is essential for understanding how signals are routed and whether critical traces are buried on inner layers (inaccessible without destructive analysis). Common methods for layer counting:

**Edge inspection.** A cross-section of the board edge (cut with a fine-tooth saw or diamond blade) reveals the copper-layer stackup under a microscope. Each copper layer appears as a bright line separated by the dielectric (FR-4 prepreg or core). A 4-layer board shows 4 copper lines; a 6-layer board shows 6. The layer thicknesses and dielectric gaps reveal the stackup (e.g., a standard 4-layer stackup is signal-ground-power-signal, with the two inner layers being ground and power planes).

**Via analysis.** Through-hole vias connect all layers (visible from both sides). Blind vias connect an outer layer to an inner layer (visible from only one side). Buried vias connect two inner layers (not visible from either side — detectable only by X-ray). Micro-vias (used in HDI boards) are small laser-drilled vias connecting adjacent layers. The presence of blind and buried vias indicates a high-layer-count board (typically 6+ layers) and HDI construction, suggesting a complex, high-speed design where critical signals may be on inner layers.

**X-ray transmission.** A quick 2D X-ray image of the board reveals the internal copper patterns: via placement, internal plane shapes, and trace routing on inner layers. This provides a non-destructive preview of the board's internal structure.

### 1.3 X-ray imaging

**2D projection X-ray.** The board is placed between an X-ray source and a flat-panel detector. The X-ray image shows the shadow of all copper layers superimposed. Component leads, bond wires inside IC packages, BGA solder balls, vias, and internal traces are all visible. 2D X-ray is fast (seconds per image) and non-destructive. It reveals BGA solder joint quality (for counterfeit detection), wire bond integrity inside IC packages, and the overall internal routing topology. Equipment: benchtop X-ray systems (Yxlon, Nikon/X-Tek, Nordson DAGE) cost $50,000–$300,000; service bureau imaging is available for $50–$500 per board.

**X-ray computed tomography (CT).** The board is rotated through 360° while acquiring hundreds or thousands of X-ray projections. Software reconstruction (filtered back-projection or iterative algorithms) produces a 3D voxel model of the board. Individual layers can be extracted as virtual cross-sections, revealing the routing on each copper layer independently. Micro-CT systems achieve voxel resolutions of 1–50 µm, sufficient to resolve individual traces and vias on all but the most advanced HDI boards.

X-ray CT is the gold standard for non-destructive PCB analysis: it provides the complete internal structure without cutting, grinding, or etching. The main limitations are cost (micro-CT systems cost $200,000–$2,000,000), scan time (minutes to hours per board depending on resolution), and artifact issues (copper planes cause beam-hardening artifacts that can obscure fine traces on adjacent layers).

**Laminography.** A variant of CT optimized for flat objects (PCBs). Instead of full 360° rotation, laminography uses a limited angular range (typically ±30°) to produce high-resolution images of a specific layer depth. Laminography trades full 3D reconstruction for faster acquisition and higher in-plane resolution, making it practical for inspecting specific layers of interest.

### 1.4 Chemical and mechanical delayering

When non-destructive methods are insufficient (or unavailable), the analyst physically removes PCB layers one at a time.

**Chemical delayering.** Cupric chloride (CuCl₂) solution selectively etches copper without attacking the FR-4 substrate, removing the top copper layer and exposing the next layer. Sodium hydroxide (NaOH) solution strips solder mask. The process: strip the solder mask from the region of interest, etch the exposed copper with CuCl₂, photograph the revealed substrate (showing the via connections to the next layer), then mechanically remove the prepreg/core dielectric (by careful sanding or peeling) to expose the next copper layer. Repeat for each layer. This is a destructive process — the board is consumed layer by layer.

**Mechanical cross-sectioning.** The board is potted in epoxy resin, then ground and polished to a specific plane (either perpendicular to the board surface for via cross-sections, or parallel to the surface for layer-by-layer exposure). Automated metallographic grinders (Struers, Buehler) with calibrated abrasive sequences (600 → 1200 → 2400 → 4000 grit → polishing compound) produce optically flat surfaces suitable for microscopy. Cross-sections reveal via geometry (aspect ratio, barrel quality, pad connection integrity), layer stackup, and dielectric thickness with micrometer precision.

### 1.5 PCB vectorization and Gerber reconstruction

After imaging all layers (via X-ray CT or destructive delayering), the analyst converts the raster images into vector format (Gerber RS-274X or ODB++) for analysis in EDA tools. This process involves:

**Image stitching.** If the layers were photographed in segments (common with optical microscopy), the segments are stitched into full-layer composite images using image-registration software (Hugin, FIJI/ImageJ stitching plugins, or commercial tools like ZeissZEN).

**Vectorization.** The raster images are converted to vector polygons representing copper traces, pads, and fills. Manual tracing is accurate but extremely labor-intensive (a complex board may have thousands of traces per layer). Semi-automated tools use edge detection and pattern recognition: the analyst defines the trace width and clearance rules, and the software traces connected copper regions. Fully automated tools (commercial offerings from Techinsights, System Plus Consulting) use trained neural networks to identify standard trace geometries, pad shapes, and via connections.

**Netlist extraction.** Once all layers are vectorized, the software identifies through-hole and blind/buried via connections between layers and builds a connectivity netlist (a list of which component pins are connected to which other pins). This netlist, combined with component identification (§2), produces a schematic-equivalent representation of the board — the same information as the original design files.

The reconstruction accuracy depends on the imaging resolution and vectorization quality. For a 4-layer consumer board with 6-mil traces and standard components, a skilled analyst can produce a complete, accurate netlist in 1–3 weeks. A 12-layer HDI board with 3-mil traces and blind/buried vias may require 2–6 months.

### 1.6 PCB RE software tools

**ZofzPCB.** A free 3D PCB viewer that imports Gerber files (or reconstructed Gerber files from PCB RE) and renders the board in 3D with interactive layer-by-layer exploration. The analyst can selectively show/hide layers, highlight nets, and navigate the board structure spatially. ZofzPCB is particularly useful for understanding multi-layer board routing and verifying that the reconstructed Gerber files match the physical board.

**Altium Designer / KiCad.** Professional EDA tools (Altium Designer is commercial; KiCad is open-source) are used to import reconstructed Gerber files or manually-drawn schematics during PCB RE. The analyst creates a schematic by tracing the connectivity from the reconstructed netlist, then lays out the traced components and connections in the EDA tool. The resulting project file serves as the definitive documentation of the reverse-engineered board.

**OpenBoardView.** An open-source tool for viewing board view files (.brd, .bvr, .fz) that are sometimes available from repair communities or leaked from manufacturers. Board view files contain the component placement, netlist, and test point map for a specific board revision, providing a shortcut for PCB RE when available.

**Custom scripting.** For large or repetitive boards (analyzing multiple revisions of the same product, or analyzing a product line with shared design modules), custom scripts (Python with OpenCV for image processing, networkx for graph analysis, or numpy for signal analysis) automate repetitive tasks: component identification from photographs (using template matching or object detection models), trace following (using edge detection to follow copper traces from one pad to another), and netlist comparison (diffing the extracted netlist against a reference to identify modifications).

### 1.7 Signal analysis during PCB RE

Beyond physical layer analysis, active signal analysis provides functional insight that static reverse engineering cannot:

**Bus probing.** Connecting a logic analyzer (Saleae Logic Pro 16, DSLogic U3Pro32, or similar) to identified buses (I²C, SPI, UART, JTAG, CAN, USB) and capturing traffic during device operation. Protocol decoding reveals the data flowing between components, identifying which IC sends commands to which, what data is read from flash at boot, and what debug messages are emitted on UART. This functional analysis often reveals more about the device's operation in hours than physical PCB RE reveals in weeks.

**Power rail analysis.** Probing each power rail with an oscilloscope identifies which components are powered by which regulator, the power-up sequence (which rails come up first — important for understanding boot timing and for planning glitch timing, Chapter 17B §1.6), and the current draw of each subsystem (which can be correlated with the device's operational state). Power rail mapping also identifies which rails to target for voltage fault injection.

**Clock tree analysis.** Identifying and probing the clock signals on the board (crystal oscillators, PLL outputs, clock distribution buffers) reveals the clock architecture: which components share a clock domain (important for understanding timing relationships), the clock frequencies (needed for protocol decoding and for clock glitching setup), and whether the clock is internally generated (complicating clock glitching, Chapter 17B §2.1) or externally supplied.

**RF emission scanning.** For devices with wireless interfaces, a spectrum analyzer or SDR (Domain 20) can identify active RF transmissions without physical probing: Wi-Fi, Bluetooth, Zigbee, LoRa, cellular, and proprietary RF signals. The frequency, modulation, and power level reveal the wireless standard in use and help identify the wireless IC on the board.

### 1.8 PCB RE automation tools and commands

Tooling transforms manual PCB reverse engineering into a repeatable, scriptable discipline. The following workflows cover the tools most frequently used during board-level analysis.

**binwalk for firmware image triage.** After extracting a firmware image from SPI flash, eMMC, or NAND (methods in §5), binwalk is the first-pass analysis tool. A basic extraction scan identifies embedded file systems, compressed archives, and known binary headers:

```bash
# Signature scan — identify all recognized headers in the image
binwalk firmware.bin

# Recursive extraction — unpack nested archives and filesystems
binwalk -eM firmware.bin

# Entropy visualization — identify encrypted, compressed, and plaintext regions
# Produces a PNG graph; flat high-entropy regions suggest encryption or compression,
# low-entropy regions suggest plaintext, structured data, or padding
binwalk -E firmware.bin

# Custom magic signature file — extend binwalk with device-specific patterns
# (e.g., proprietary header formats found during RE of a specific vendor)
binwalk --signature custom_sigs.magic firmware.bin

# Diff two firmware images — compare revisions to find patched regions
binwalk -W firmware_v1.bin firmware_v2.bin
```

Custom magic signatures follow the libmagic format. When analyzing a product family where the vendor uses a proprietary firmware container, a custom signature file accelerates analysis of subsequent firmware extractions.

**flashrom for SPI NOR flash.** flashrom supports hundreds of SPI NOR flash chips and multiple programmers. The CH341A USB programmer ($3–$8 on commodity markets) is the most common low-cost option, though its 5V output can damage 1.8V or 3.3V flash parts without a level-shifting adapter (an important caveat that has destroyed many targets in practice):

```bash
# Detect the SPI flash chip (probe connected via CH341A)
flashrom -p ch341a_spi

# Full chip read — dump entire flash contents to file
# The --noverify-all flag skips readback verification for speed on large chips
flashrom -p ch341a_spi -r firmware_dump.bin

# Verify a dump against the chip contents (integrity check)
flashrom -p ch341a_spi -v firmware_dump.bin

# Write a modified image back to flash
flashrom -p ch341a_spi -w modified_firmware.bin

# Erase only a specific region (offset 0x10000, length 0x1000)
# Useful for clearing a specific configuration block without full reflash
flashrom -p ch341a_spi --layout layout.txt --image config -E

# Using a Raspberry Pi's SPI bus as the programmer (no extra hardware needed)
flashrom -p linux_spi:dev=/dev/spidev0.0,spispeed=1000
```

When reading in-system (with the SoC still soldered), bus contention is the primary challenge. The SoC's SPI controller competes for the bus. Mitigations: hold the SoC in reset (assert RESET low), remove the SoC's SPI chip-select (CS) resistor to isolate it from the bus, or power the flash chip from the external programmer while the rest of the board is unpowered (requires cutting the flash VCC trace and feeding power from the programmer).

**Bus Pirate for interactive protocol probing.** The Bus Pirate (v3.6 or v5) provides a text-mode interface for bit-banging I2C, SPI, UART, and JTAG from a serial terminal. It is the hardware reverse engineer's Swiss army knife for initial protocol identification:

```bash
# Enter I2C mode (Bus Pirate terminal)
# m → 4 (I2C) → set speed (100kHz typical for EEPROMs)
# Scan for I2C devices (7-bit address search):
(1)

# Read 16 bytes from I2C EEPROM at address 0xA0 (device 0x50 in 7-bit):
[0xA0 0x00 0x00 [0xA1 r:16]

# Enter SPI mode
# m → 5 (SPI) → configure clock polarity, phase, speed
# Send RDID command (0x9F) and read 3 bytes (manufacturer + device ID):
[0x9F r:3]

# Enter UART bridge mode — transparent passthrough at detected baud
# m → 3 (UART) → set baud rate → macro (1) for transparent bridge
```

The Bus Pirate's 3.3V logic levels match most embedded targets. For 1.8V targets (common in modern mobile devices), a level-shifting adapter or a voltage-tolerant probe (Tigard, Glasgow Interface Explorer) is required.

**sigrok and PulseView for logic analysis and protocol decoding.** sigrok is the open-source framework underpinning PulseView (the GUI) and sigrok-cli. It supports dozens of logic analyzers and over 100 protocol decoders:

```bash
# Capture 10 million samples at 24 MHz on channels 0–3 using a fx2lafw device
sigrok-cli --driver fx2lafw --config samplerate=24M \
  --samples 10M --channels 0-3 -o capture.sr

# Decode I2C from channels 0 (SCL) and 1 (SDA)
sigrok-cli --driver fx2lafw --config samplerate=24M \
  --samples 10M --channels 0-1 \
  -P i2c:scl=0:sda=1

# Stack decoders — decode I2C then interpret as EEPROM 24xx transactions
sigrok-cli --driver fx2lafw --config samplerate=24M \
  --samples 10M --channels 0-1 \
  -P i2c:scl=0:sda=1,eeprom24xx

# Decode SPI with protocol stacking for SPI flash commands
sigrok-cli --driver fx2lafw --config samplerate=24M \
  --samples 10M --channels 0-3 \
  -P spi:clk=0:mosi=1:miso=2:cs=3,spi_nor_flash
```

For protocol reverse engineering on unknown buses, PulseView's GUI is more practical than the CLI: the analyst captures a broad trace, visually identifies clock and data patterns, then iterates through candidate decoders until the traffic is correctly parsed. Unrecognized protocols can be decoded by writing a custom sigrok protocol decoder in Python.

**OpenOCD for boundary scan pin mapping.** While Chapter 17D covers OpenOCD for debug port exploitation (halt, memory read/write, flash programming), boundary scan (IEEE 1149.1 EXTEST/SAMPLE) is a PCB-level technique that predates debug access. Boundary scan reads or drives every pin on a JTAG-enabled IC, providing a complete pin-level connectivity map of the board without any debug authentication:

```bash
# Scan the JTAG chain — identify all devices by IDCODE
openocd -f interface/ftdi/minimodule.cfg -c "adapter speed 1000" \
  -c "jtag newtap chip0 tap -irlen 4 -expected-id 0x4ba00477" \
  -c "init" -c "scan_chain" -c "shutdown"

# Load a BSDL file for the target IC (BSDL files describe pin-to-boundary-cell mapping)
# BSDL files are published by IC manufacturers and define which boundary scan cell
# corresponds to which package pin
# After loading, SAMPLE/PRELOAD reads the current logic state of every pin
```

Boundary scan's value for PCB RE is that it provides a pin-level view of every JTAG-enabled IC on the board: which pins are inputs, which are outputs, and what their current state is. This accelerates bus identification (confirming which pins carry I2C, SPI, or UART signals by observing their logical behavior during device operation) without requiring an oscilloscope or logic analyzer on every pin simultaneously.

---

## 2. Component identification and analysis

### 2.1 IC package identification

Modern ICs use a variety of package types, each presenting different reverse engineering challenges:

**Ball Grid Array (BGA).** Solder balls on the bottom surface connect to the PCB. The ball pitch (distance between ball centers) ranges from 1.0 mm (standard BGA) to 0.3 mm (micro-BGA/CSP). BGA packages hide the solder connections underneath the IC, making visual inspection of connections impossible without X-ray. Desoldering BGAs requires a hot-air rework station (Hakko FR-810B, JBC JNAE-2QA, or equivalent) with a matched nozzle for the specific package size. After desoldering, the BGA site on the PCB reveals the pad pattern, which is a fingerprint for the IC type (the pad count and arrangement are package-specific).

**Quad Flat No-lead (QFN).** A leadless package with exposed pads on the bottom surface and an exposed thermal pad in the center. QFN packages are common for microcontrollers, power management ICs, and RF components. The pad pattern and pin count identify the package class; the die pad (central thermal pad) can be inspected after desoldering to reveal the die surface.

**Wafer-Level Package (WLP).** The chip is packaged at the wafer level — the solder bumps are placed directly on the silicon die, and the die is diced and placed on the PCB without a traditional package. WLP ICs are difficult to identify because there is no package marking — the top surface is bare silicon or a thin redistribution layer. Identification requires decapsulation (removing the redistribution layer) or X-ray (to see the bump pattern and die size).

**Package-on-Package (PoP).** Two or more IC packages stacked vertically, connected by solder bumps between the top of the lower package and the bottom of the upper package. Common in mobile devices (the application processor on the bottom, DRAM on top). PoP complicates memory extraction because the DRAM is physically bonded to the processor package — separating them without damage requires specialized rework equipment.

### 2.2 Marking analysis and part number lookup

IC package markings follow manufacturer-specific conventions. The top surface of a marked IC typically contains: the manufacturer's logo (a standardized symbol — the "N" with a tail for ON Semiconductor, the "TI" logo for Texas Instruments, the stylized "ST" for STMicroelectronics), the part number (the primary identifier for datasheet lookup), the date code (a 4-digit code: 2-digit year + 2-digit week, e.g., "2348" = week 48 of 2023), a lot code (manufacturer-internal, sometimes useful for supply chain tracking), and sometimes a country of origin marking.

For standard components, the part number leads directly to a publicly available datasheet that specifies the IC's function, pinout, electrical characteristics, and (often) block diagram. For custom ASICs (application-specific ICs designed for a particular product), the package marking may be a vendor-specific part number that has no public datasheet. In this case, the analyst must determine the IC's function through other means: circuit tracing (where does it connect on the PCB?), pin-probing (what signals appear on its pins?), or decapsulation (what does the die look like?).

### 2.3 Passive component analysis and functional block identification

Resistors, capacitors, inductors, and discrete semiconductors (diodes, MOSFETs, ESD protection) are identified by their package size (0201, 0402, 0603, 0805 — the package dimensions in hundredths of an inch), their value (measured with an LCR meter after desoldering, or estimated from markings — 3-digit codes for resistors, where "103" means 10 × 10³ = 10 kΩ), and their circuit context.

Passive component analysis reveals circuit function: a 10 kΩ resistor and a 100 nF capacitor in an RC filter configuration suggest a low-pass filter with a cutoff frequency of approximately 160 Hz. A 4.7 kΩ pull-up resistor on a two-wire bus identifies an I²C interface. A ferrite bead in series with a power trace indicates EMI filtering. A common-mode choke on a differential pair identifies a high-speed data interface (USB, HDMI, Ethernet).

Identifying functional blocks on a complex PCB requires combining component identification with circuit topology analysis. The analyst groups components into functional blocks based on their connectivity and function: power supply (voltage regulators, inductors, filter capacitors), processor subsystem (SoC, DRAM, flash, decoupling capacitors, crystal oscillator), wireless module (RF IC, matching network, antenna connector or PCB antenna), sensor interface (ADC, sensor IC, signal conditioning components), debug interface (JTAG/SWD header, level shifters, series resistors on debug lines), and security subsystem (secure element, tamper switches, battery backup for key storage). This functional-block decomposition guides the subsequent analysis: the security-relevant blocks receive detailed attention, while commodity blocks (power supply, standard interfaces) are documented but not deeply analyzed.

Thermal imaging (using an IR camera — FLIR, Seek Thermal) of a powered board identifies which components dissipate significant power, helping to locate the main processor, power regulators, and other active components. Components that run hot during specific operations (e.g., a crypto accelerator that heats up during key generation) are identified by comparing thermal images during idle vs. active states.

### 2.3 Counterfeit IC detection

Counterfeit components are a significant supply chain security threat, particularly in aerospace, defense, and medical electronics where component reliability is safety-critical. The taxonomy of counterfeit ICs:

**Recycled.** Used components desoldered from discarded boards, cleaned, and resold as new. Indicators: lead or ball surface shows signs of prior soldering (dull, irregular, or pitted surfaces vs. the bright, uniform finish of new components), stress marks on the package (scratches, discoloration), internal bond wire degradation visible on X-ray, and electrical parametric drift (degraded timing margins, elevated leakage current).

**Remarked.** Legitimate ICs whose markings are altered to represent a higher-grade, higher-speed, or different part number. The original marking is removed (by sanding, sandblasting, or chemical stripping) and a new marking is printed or laser-engraved. Indicators: under UV light, the remarking material fluoresces differently from the original mold compound; acetone swab testing dissolves laser markings (original markings are molded into the package surface or laser-engraved into the mold compound and resist acetone); cross-section microscopy reveals the sanding/blasting damage to the package surface beneath the new marking.

**Cloned.** Unauthorized copies manufactured from stolen mask sets or reverse-engineered designs. Clones may have identical die layouts to the original (if made from stolen masks) or functionally equivalent but physically different die layouts (if reverse-engineered). Detection requires die-level comparison with a known-good reference (golden sample).

**Overproduced.** Legitimate components manufactured by the authorized foundry beyond the contracted quantity and sold through unauthorized channels. Overproduced parts are electrically identical to genuine parts but lack the design owner's quality-control testing and are sold without authorization (violating the foundry's contract). Detection is extremely difficult because the parts are physically and electrically genuine — only supply chain provenance tracking (purchase records, distributor authorization) can identify them.

**Tampered.** Genuine components that have been physically modified to change their function — eFuses burned to change configuration, firmware modified through debug interfaces, or die-level modifications via FIB. Tampered components are the hardware equivalent of supply chain software attacks (Domain 19): a genuine product is modified to include a backdoor or weakness before reaching the end user. Detection requires full functional verification against the manufacturer's specification, die-level inspection for FIB marks, and firmware hash verification against known-good images.

**Scanning Acoustic Microscopy (SAM).** C-mode SAM uses an ultrasonic transducer (typically 15–230 MHz) to scan the IC package and generate a cross-sectional image at a specific depth. The ultrasonic pulse reflects at material interfaces (epoxy-to-die, die-attach-to-leadframe, bond-pad-to-wire), producing an acoustic image that reveals: delamination (gaps between the mold compound and the die surface, indicating thermal stress from recycling), die-attach voids (incomplete die-attach adhesive, common in recycled parts where the original die-attach has degraded), and internal cracks (from thermal cycling during previous use). SAM is non-destructive and can inspect a component in seconds. It is the primary screening tool for detecting recycled components in incoming inspection.

SAM systems (Sonoscan C-SAM, PVA TePla SAM 400) cost $50,000–$200,000. For organizations without in-house SAM capability, third-party testing laboratories (SGS, Eurofins, CTG) offer per-component SAM inspection at $10–$50 per component.

**Material analysis techniques.** X-Ray Fluorescence (XRF) identifies the elemental composition of the component's external surfaces — verifying lead-free compliance (RoHS mandates < 1000 ppm lead in solder and < 100 ppm lead in homogeneous material), detecting tin whisker risk (pure tin finishes without lead grow conductive whiskers that can cause shorts), and identifying non-standard materials that indicate remarking (the top surface of a remarked chip may have a different composition from the original mold compound). Fourier Transform Infrared Spectroscopy (FTIR) identifies the polymer composition of the mold compound — each manufacturer's mold compound has a characteristic FTIR spectrum, and a mismatch between the claimed manufacturer and the FTIR spectrum indicates a recycled or remarked part.

**SAE AS6171 / AS6081 standards.** These aerospace standards define comprehensive test procedures for detecting counterfeit components: external visual inspection (marking quality, lead condition, package surface anomalies), X-ray inspection (internal structure comparison with known-good samples, wire bond integrity, die size and position), SAM (delamination, die-attach integrity), electrical testing (parametric testing against datasheet specifications, burn-in testing for accelerated aging), material analysis (XRF, FTIR, ion chromatography for contamination), and destructive physical analysis (DPA — die decapsulation, bond pull testing, die shear testing on a sample from each lot). The standard defines accept/reject criteria for each test and escalation procedures when suspect parts are found.

**Authentication technologies.** Beyond inspection-based detection, the industry is adopting proactive authentication: Physical Unclonable Functions (PUFs, §8.2) provide cryptographic device identity that cannot be cloned. DNA-based authentication (Applied DNA Sciences, now LineaRx) applies a unique DNA marker (a custom-synthesized oligonucleotide sequence) to the component's surface during manufacture; authenticity is verified by extracting and sequencing the DNA marker. Blockchain-based provenance tracking records each component's chain of custody (manufacturer → distributor → assembly → end product) in an immutable ledger, making it harder to insert counterfeit components into the supply chain without detection. GIDEP (Government-Industry Data Exchange Program) and ERAI provide industry-wide databases of known counterfeit components and suspicious suppliers.

### 2.4 Counterfeit IC detection practical workflow

A structured incoming-inspection workflow following SAE AS6171 transforms ad-hoc part screening into a repeatable, auditable process. The workflow is a decision tree: each test either passes (proceed to next test) or fails (escalate to destructive analysis or reject the lot).

**Step 1: External visual inspection (EVI).** Under a stereomicroscope at 10–30x magnification, inspect package surface finish (uniform matte or gloss consistent with the manufacturer's known finish), marking quality (font consistency, alignment, sharpness), lead or ball condition (bright and uniform for new parts, dull or pitted for recycled), and date-code plausibility (does the date code match the claimed procurement timeline). UV inspection: under 365 nm UV lamp, the mold compound should fluoresce uniformly; patches of different fluorescence indicate sanding, remarking, or blacktopping (applying a new coating to hide rework damage). Acetone test: a cotton swab dipped in acetone is rubbed across the package marking for 30 seconds. Laser-engraved original markings resist acetone; ink-printed or pad-printed remark coatings dissolve partially or completely.

Automating a portion of EVI with machine vision reduces human fatigue on large incoming lots. The following prototype uses OpenCV to compare a suspect component's package markings against a golden reference image:

```python
#!/usr/bin/env python3
"""counterfeit_visual_check.py — Automated package marking comparison.

Compares a suspect IC package photo against a golden reference using
structural similarity (SSIM) on the marking region. Low SSIM flags
the part for manual inspection.

Requires: opencv-python, scikit-image, numpy.
"""

import sys
import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim


def preprocess(image_path: str, roi: tuple[int, int, int, int]) -> np.ndarray:
    """Load image, crop to ROI, convert to grayscale, normalize."""
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Cannot load {image_path}")
    x, y, w, h = roi
    crop = img[y:y + h, x:x + w]
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    # Adaptive histogram equalization for consistent contrast
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(gray)


def compare_markings(
    golden_path: str,
    suspect_path: str,
    roi: tuple[int, int, int, int],
    threshold: float = 0.85,
) -> dict:
    """Compare marking regions. Returns similarity score and verdict."""
    golden = preprocess(golden_path, roi)
    suspect = preprocess(suspect_path, roi)

    # Resize suspect to match golden dimensions (handles slight framing differences)
    suspect = cv2.resize(suspect, (golden.shape[1], golden.shape[0]))

    score, diff_map = ssim(golden, suspect, full=True)
    verdict = "PASS" if score >= threshold else "FAIL — flag for manual review"

    # Highlight discrepancy regions on the diff map
    diff_map = (diff_map * 255).astype(np.uint8)
    _, thresh_img = cv2.threshold(diff_map, 200, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thresh_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    return {
        "ssim_score": round(score, 4),
        "verdict": verdict,
        "discrepancy_regions": len(contours),
    }


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: counterfeit_visual_check.py <golden.jpg> <suspect.jpg> [x y w h]")
        sys.exit(1)
    golden_img = sys.argv[1]
    suspect_img = sys.argv[2]
    # Default ROI covers center 60% of a 640x480 image (typical marking area)
    roi = (128, 96, 384, 288) if len(sys.argv) < 7 else tuple(map(int, sys.argv[3:7]))
    result = compare_markings(golden_img, suspect_img, roi)
    print(f"SSIM: {result['ssim_score']}  |  Regions: {result['discrepancy_regions']}  |  {result['verdict']}")
```

This script is a screening aid, not a definitive pass/fail gate. SSIM below the threshold triggers human review under the microscope. The threshold should be calibrated per component family: identical parts from the same lot typically score > 0.95; parts from different lots (different date codes) score 0.88–0.94; remarked counterfeits score 0.60–0.80.

**Step 2: X-ray inspection.** Compare the suspect component's 2D X-ray image against a golden reference X-ray. The comparison evaluates: die size and position within the package (a cloned or recycled part may have a different die size), wire bond count and routing (a recycled part may have degraded or missing bond wires), die-attach voiding (visible as bright spots under the die — recycled parts show higher voiding from thermal degradation), and lead frame geometry (clones from a different manufacturer may use a different lead frame design). The golden reference X-ray must be from an authenticated part — procured directly from the manufacturer's authorized distribution channel with full traceability. Overlay comparison (superimposing the golden and suspect X-ray images at matched scale and alignment) quickly highlights geometric discrepancies.

**Step 3: Electrical parametric testing.** Measure the suspect component's key electrical parameters and compare against the manufacturer's datasheet specifications. The test matrix depends on the component type, but always includes: supply current (IDD/ICC) at specified voltage and temperature — recycled parts show elevated leakage; timing parameters (propagation delay, setup/hold times) — recycled or remarked lower-grade parts fail at the tighter timing margins of the claimed part number; functional test at the extremes of the rated temperature range — remarked commercial-grade parts (0°C to 70°C) fail when tested at industrial-grade specifications (-40°C to 85°C). Automated parametric testing uses an ATE (automated test equipment) system or a benchtop curve tracer (Keithley 2400 series) with a custom test fixture.

**Step 4: Material analysis interpretation.** When Steps 1–3 produce inconclusive results, material analysis provides definitive chemical evidence.

XRF spectral interpretation: the primary diagnostic signatures are lead content in the lead/ball finish (RoHS-compliant parts have < 1000 ppm Pb; recycled pre-RoHS parts often have high Pb from SnPb solder), tin whisker risk (pure Sn finishes without Pb or Bi alloying), and anomalous elements on the package surface (Sb, Bi, or other elements not expected for the claimed mold compound formulation). Each manufacturer's standard mold compound has a known elemental profile; significant deviation indicates a different compound (remarking or recycling from a different product).

FTIR peak interpretation for common mold compounds: epoxy-based compounds show characteristic absorption bands at 830 cm⁻¹ (epoxide ring), 1035 cm⁻¹ (C-O-C), 1510 cm⁻¹ (aromatic C=C), and 1608 cm⁻¹ (aromatic C=C). Silica filler (present in most modern mold compounds) shows a broad band at 1000–1100 cm⁻¹ (Si-O-Si asymmetric stretch). If the claimed manufacturer uses an epoxy novolac compound but the FTIR shows silicone-characteristic bands at 1260 cm⁻¹ (Si-CH₃) and 800 cm⁻¹ (Si-O-Si symmetric stretch), the compound is inconsistent — the part is likely remarked or from a different manufacturer.

**Step 5: Escalation — destructive physical analysis (DPA).** If material analysis raises suspicion, a sample (typically 3–5 parts per lot) undergoes DPA: decapsulation (§3), die marking comparison against the manufacturer's known die markings (each manufacturer marks the die surface with an internal lot code, die revision, and sometimes a logo that is visible only after decapsulation), bond pull testing (measuring the force required to detach bond wires — degraded wires in recycled parts pull at lower force), and die shear testing (measuring the die-attach adhesion strength — degraded die-attach in recycled parts fails at lower shear force). DPA results are definitive: a die marking mismatch conclusively identifies a counterfeit.

---

## 3. Chip decapsulation

### 3.1 Chemical decapsulation

Chemical decapsulation dissolves the epoxy mold compound that encases the silicon die, exposing the die surface for inspection. The standard chemistry:

**Fuming nitric acid (HNO₃ 98%).** The workhorse decapsulant for most epoxy-packaged ICs. The package is immersed in heated fuming HNO₃ (80–100°C) for 10–60 minutes (depending on package size and mold compound type). The acid dissolves the epoxy without attacking silicon, aluminum metallization, or gold bond wires. After dissolution, the die is rinsed in acetone, then isopropanol, then deionized water, and dried under nitrogen.

Safety requirements for fuming HNO₃ work: a fume hood with acid-rated exhaust, chemical splash goggles, acid-resistant gloves (butyl rubber or PVA), a face shield, and a chemical apron. Fuming HNO₃ is a strong oxidizer and produces toxic NO₂ fumes (brown gas). The work area must have NO₂ detection and emergency shower/eyewash facilities.

**Sulfuric acid + hydrogen peroxide (piranha etch).** A mixture of concentrated H₂SO₄ and 30% H₂O₂ (typically 3:1 ratio) generates a highly reactive persulfuric acid that aggressively dissolves organic material. Piranha etch is faster than HNO₃ for some mold compounds but more dangerous (exothermic, potentially explosive with incompatible materials) and more difficult to control. It is used when HNO₃ is insufficient (some modern mold compounds contain fillers that resist HNO₃).

**Proprietary decapsulants.** Commercial products (Nisene JetEtch Pro, Dynasolve COP) provide controlled decapsulation with reduced safety hazards. These are typically warm acid baths with agitation, providing more consistent results than manual acid processing.

### 3.2 Mechanical and laser decapsulation

**Mechanical decapsulation.** CNC micro-milling machines (Ultratec ASAP-1, Nisene JetEtch) remove the mold compound by precision grinding. The CNC program mills to a specified depth above the die surface (determined by package cross-section data or X-ray), leaving a thin layer of mold compound that is either dissolved chemically (a hybrid approach) or carefully ground away under microscope observation. Mechanical decapsulation is faster than pure chemical methods and produces less toxic waste, but risks mechanical damage to bond wires and the die surface.

**Laser decapsulation.** Nd:YAG laser ablation (1064 nm) removes mold compound by thermally decomposing the epoxy. The laser is scanned across the package surface, layer by layer, until the die is exposed. Laser decapsulation offers precise depth control and is suitable for packages with sensitive die-attach materials, but the heat from the laser can damage bond wires and the die if not carefully controlled. Modern laser decapsulation systems (Hesse Mechatronics, DISCO) use pulse-shape optimization and real-time depth monitoring (via laser confocal measurement) to minimize thermal damage.

**Plasma decapsulation.** Oxygen plasma (O₂ plasma asher) removes organic mold compound through reactive ion etching. The plasma chemically reacts with the carbon in the epoxy, converting it to CO₂ and H₂O. Plasma decapsulation is extremely gentle (no mechanical force, no liquid chemicals), preserving bond wires and the die surface intact. The disadvantage is speed: plasma decapsulation takes hours to days for thick packages (the etch rate is typically 10–100 µm/hour). It is the method of choice for failure analysis where die integrity is paramount.

Plasma asher systems (PVA TePla, Diener Electronic, YES-FS) range from $10,000 (benchtop) to $100,000+ (production-grade). The process parameters — O₂ flow rate, chamber pressure, RF power, and temperature — must be tuned for the specific mold compound. Some modern mold compounds contain inorganic fillers (silica, alumina) that resist plasma etching, leaving a residue layer that must be removed mechanically or chemically after the organic matrix has been ashed away.

**Selective decapsulation.** For packages where only a portion of the die needs to be exposed (e.g., to inspect the security fuse area without exposing the entire die), selective chemical or laser decapsulation removes mold compound from a targeted region. The operator applies acid (using a micropipette or a jet-etching system that directs a fine stream of acid onto the target area) or laser ablation (scanning the laser only over the region of interest). Selective decapsulation preserves the device's functionality outside the exposed region, allowing the device to continue operating during or after the analysis — essential for combined decapsulation + electrical testing or decapsulation + side-channel analysis workflows.

**Encapsulant identification.** Before selecting a decapsulation method, the analyst must identify the encapsulant type. Modern IC packages use various materials beyond standard epoxy mold compound: silicone gels (in power modules and sensors), polyimide (in flexible packages), underfill epoxy (in flip-chip packages), and glob-top (a UV-cured or thermally-cured coating applied over wire-bonded die in low-cost packages). Each requires a different removal method: silicone gels dissolve in TBAF (tetrabutylammonium fluoride); polyimide is resistant to most acids and requires hot NMP (N-methyl-2-pyrrolidone) or plasma; underfill requires mechanical removal (CNC) because it fills the gap between the die and the substrate, making chemical access difficult; glob-top compositions vary widely and may require iterative testing with different solvents.

### 3.3 Bond wire preservation and rebonding

The bond wires (gold, aluminum, or copper) connecting the die pads to the package lead frame are fragile and easily damaged during decapsulation. Chemical decapsulation with HNO₃ preserves gold bond wires (gold is chemically inert to HNO₃) but attacks aluminum bond wires (dissolved by HNO₃). Copper bond wires are dissolved by HNO₃. For packages with aluminum or copper bond wires, the analyst must use mechanical or plasma methods.

After decapsulation, if the bond wires are damaged or removed, the die can be rebonded — new bond wires are attached from the die pads to the lead frame (or to a test fixture) using a wire bonder (Kulicke & Soffa, Hesse). Rebonding allows the device to function electrically after decapsulation, enabling combined optical inspection and electrical testing (e.g., probing individual die pads while the chip operates, or performing side-channel analysis on a decapsulated and rewired device).

---

## 4. Die-level analysis

### 4.1 Optical microscopy

The first step in die analysis is optical microscopy of the exposed die surface. Modern silicon dies have 5–15 metal layers; the top metal layer is the largest-geometry layer (widest traces, largest pads) and is visible after decapsulation.

**Bright-field microscopy.** Standard reflected-light imaging. The microscope illuminator sends light down through the objective, and light reflected from the die surface forms the image. Metal features (traces, pads, vias) appear bright; dielectric regions (oxide, low-k) appear dark. Bright-field imaging provides the basic layout view of the top metal layer.

**Dark-field microscopy.** The illumination is angled so that only scattered light (from edges, defects, and topographic features) reaches the objective. Flat surfaces appear dark; edges and surface features appear bright. Dark-field is useful for detecting scratches, cracks, and thin-film thickness variations that are invisible in bright-field.

**Differential Interference Contrast (DIC / Nomarski).** Polarized light is split into two beams that traverse slightly different optical paths across the specimen surface. The recombined beams produce interference that maps the surface topography with high sensitivity. DIC reveals very shallow surface features (height differences of a few nanometers) and produces a pseudo-3D appearance that makes metal step heights and via topography clearly visible.

Die images are captured at multiple magnifications: low magnification (5×–10×) for the full-die overview, medium (20×–50×) for block-level layout, and high (100×–150×) for individual standard cells and transistors. At each magnification, multiple fields of view are captured and stitched into a seamless mosaic using image-stitching software.

### 4.2 Scanning Electron Microscopy (SEM)

SEM provides higher resolution than optical microscopy (down to ~1 nm vs. ~200 nm diffraction limit for optical) and greater depth of field (the entire die surface remains in focus, even with significant topography). SEM is essential for analyzing features on advanced process nodes (28 nm and below) where optical microscopy cannot resolve individual transistors.

**Secondary Electron (SE) imaging.** SE detectors capture low-energy secondary electrons ejected from the specimen surface by the primary electron beam. SE images show surface topography with high resolution and contrast. SE imaging is the primary mode for die-surface inspection after delayering.

**Backscattered Electron (BSE) imaging.** BSE detectors capture high-energy electrons that bounce back from the specimen. BSE signal intensity depends on the atomic number of the material: heavier elements (tungsten vias, copper metallization) appear brighter than lighter elements (silicon, oxide). BSE imaging is useful for distinguishing material composition without chemical analysis.

**Energy-Dispersive X-ray Spectroscopy (EDS/EDX).** The electron beam excites characteristic X-rays from the specimen's atoms. An EDS detector measures the X-ray energies, producing an elemental composition map. EDS identifies the materials present in each layer (aluminum vs. copper metallization, tungsten vs. copper vias, silicon dioxide vs. low-k dielectric).

### 4.3 Focused Ion Beam (FIB)

FIB uses a focused beam of gallium ions (Ga+) to mill, image, and deposit material on the die surface with nanometer precision. FIB is the most versatile tool in semiconductor failure analysis and hardware reverse engineering.

**FIB milling.** The gallium ion beam sputters material from the die surface, creating precise cuts, cross-sections, and trenches. FIB milling can expose a specific cross-section of a via, interconnect, or transistor for SEM imaging. The milling resolution is approximately 5–10 nm, sufficient to cross-section individual transistors on nodes down to 7 nm.

**FIB deposition.** Metal (platinum, tungsten) or insulator (SiO₂) can be deposited by introducing a precursor gas near the die surface while scanning the ion beam. The ion beam decomposes the precursor, leaving a thin film of the deposited material. FIB deposition creates new electrical connections on the die — the reverse engineer can rewire a circuit by cutting existing connections (milling) and depositing new ones (deposition). This is called **circuit edit** and is used in failure analysis (to test design fixes before re-fabrication) and in security research (to bypass security fuses, reconnect disabled debug ports, or modify circuit behavior).

**TEM lamella preparation.** For the highest-resolution imaging (individual atoms in a crystal lattice), Transmission Electron Microscopy (TEM) is required. FIB prepares the specimen: a thin lamella (50–100 nm thick) is cut from the region of interest using FIB milling, then lifted out with a micro-manipulator and mounted on a TEM grid. The TEM images the lamella in transmission, achieving sub-angstrom resolution. TEM is used to verify transistor gate dimensions on advanced nodes, detect process defects, and analyze diffusion profiles.

### 4.4 Advanced die analysis techniques

**Photon emission microscopy (PEM).** When CMOS transistors switch, hot carriers in the channel emit photons in the near-infrared range (850–1100 nm wavelength). An InGaAs or silicon avalanche-photodiode camera, positioned above the die (frontside PEM) or below it looking through the silicon substrate (backside PEM — silicon is transparent to IR above 1100 nm), captures these faint emissions over extended exposure times (seconds to minutes). The resulting image overlays switching activity onto the die layout, identifying which circuit blocks are active during a specific operation.

PEM is essential for hardware security analysis because it maps the spatial activation pattern of security-critical operations. Before performing fault injection or side-channel analysis, the analyst uses PEM to identify: which die region executes the boot signature verification (target for glitching, Chapter 17B §4.1), which die region contains the AES engine (target for DPA/CPA, Chapter 17A §1.1), and which die region performs the RDP/APPROTECT check (target for readout-protection bypass, Chapter 17B §9.2).

Frontside PEM requires die decapsulation (removing the package to expose the die surface). Backside PEM does not require decapsulation but requires thinning the silicon substrate (polishing the back of the die to < 100 µm to improve IR transmission) or removing the package heat spreader. Hamamatsu PHEMOS and Quantum Focus Instruments (QFI) InfraScope are standard PEM systems, costing $200,000–$1,000,000.

**Optical Beam Induced Resistance Change (OBIRCH).** A focused laser beam (typically 1.3 µm wavelength) is scanned across the die surface (or backside through silicon). The laser locally heats the interconnect, changing its resistance. The resulting change in current draw is measured at the device's power pins. Regions where the laser produces a strong current change correspond to high-current-density paths — short circuits, electromigration-damaged interconnects, or highly resistive junctions. OBIRCH is primarily a failure-analysis technique, but in security context it identifies active power distribution paths, helping the analyst understand which supply rails power which functional blocks.

**Laser Voltage Probing (LVP) and Laser Timing (LTA).** LVP and LTA use a focused laser beam through the silicon backside to measure voltage levels and timing at specific circuit nodes. The reflected laser light is modulated by the electric field in the transistor (the electro-optic effect in silicon), allowing the analyst to observe logic levels and timing at individual nodes without physical probe contact. This enables the analyst to observe internal signals — clock trees, data buses, control signals — at any accessible point on the die, providing signal-level visibility equivalent to an internal logic analyzer.

LVP/LTA systems (Hamamatsu PHEMOS with LVP option, Quantum Focus InfraProbe) are sophisticated instruments used primarily in semiconductor failure analysis labs, but their capabilities are directly applicable to hardware reverse engineering: the analyst can observe the exact cycle at which a security check occurs, the data values flowing through the security logic, and the control signals that gate security decisions.

### 4.5 Die delayering

Delayering the die — removing metal and dielectric layers one at a time — exposes each layer for imaging and analysis. The delayering sequence works from the top of the die (the last metal layer fabricated) downward to the transistor level.

**Wet etch chemistry.** Each material requires a specific etchant:
- Aluminum metallization: phosphoric acid + acetic acid + nitric acid (PAN etch) at 50°C. Etch rate ~100 nm/min for Al.
- Copper metallization: ferric chloride (FeCl₃) or ammonium persulfate ((NH₄)₂S₂O₈). Copper etch is more challenging than aluminum because copper is used with barrier metals (tantalum, tantalum nitride) that require separate etch steps.
- Silicon dioxide (interlayer dielectric): buffered hydrofluoric acid (BHF — a mixture of HF and NH₄F). Etch rate ~100 nm/min for thermal oxide.
- Low-k dielectric: varies by material; some low-k dielectrics are etched by BHF, others require oxygen plasma.
- Tungsten (vias): hydrogen peroxide (H₂O₂ 30%) at 50°C.
- Silicon nitride (passivation, etch stop): hot phosphoric acid (H₃PO₄ at 160°C).
- Polysilicon (gates): potassium hydroxide (KOH) or tetramethylammonium hydroxide (TMAH).

**Dry etch / Reactive Ion Etching (RIE).** For more controlled, directional etching (especially on advanced nodes where wet etch selectivity is insufficient), RIE uses reactive gas plasmas (CF₄ for oxide, Cl₂/BCl₃ for metal, O₂ for organics) in a vacuum chamber. RIE provides better anisotropy (vertical etch profiles) and selectivity than wet etch, but requires expensive equipment (an RIE system costs $100,000–$500,000).

**Chemical-Mechanical Polishing (CMP).** CMP uses a rotating polishing pad with an abrasive slurry to planarize the die surface, removing material uniformly. CMP-based delayering produces extremely flat surfaces suitable for high-resolution imaging, but requires careful endpoint detection (monitoring the polishing to stop at exactly the right layer). CMP is the preferred method for delayering advanced nodes (14 nm and below) where wet-etch selectivity between materials is problematic.

Endpoint detection methods for CMP-based delayering include: optical monitoring (measuring the reflectivity of the polished surface in real time — reflectivity changes when the polishing crosses a material boundary, e.g., from copper to oxide), electrical monitoring (measuring the resistance between two probes on the die surface — resistance changes dramatically when a conductive layer is removed), and thickness monitoring (using ellipsometry or interferometry to measure the remaining film thickness during polishing). Automated CMP systems with integrated endpoint detection (Allied High Tech MultiPrep, South Bay Technology Model 920) can achieve layer-by-layer removal with sub-50 nm accuracy, essential for delayering advanced nodes where the interlayer dielectric thickness may be only 100–200 nm.

**Delayering on advanced FinFET nodes.** At 14 nm and below, the back-end-of-line (BEOL) stack contains 10–15 metal layers with alternating copper metallization and low-k dielectric. The low-k dielectric (carbon-doped silicon oxide, porous SiOCH) is mechanically fragile and chemically sensitive — aggressive wet etch can damage the porous structure, creating artifacts that obscure the underlying features. The preferred approach at these nodes is a CMP-dominated workflow: each layer is removed by CMP with a metal-selective slurry (removing copper while stopping on the barrier metal), followed by a brief plasma etch (removing the barrier and inter-metal dielectric) to expose the next layer. The entire workflow is performed in a controlled environment (temperature, humidity) to prevent dielectric damage from moisture absorption.

### 4.6 Gate-level netlist extraction

The ultimate goal of die-level reverse engineering is to extract the complete gate-level netlist — the logical circuit description at the level of individual logic gates (AND, OR, NAND, NOR, XOR, flip-flops, multiplexers). The process:

**Standard cell identification.** On ASIC designs (and the logic portions of SoCs), the layout is composed of standard cells — pre-designed logic gates from a cell library (e.g., Synopsys DesignWare, ARM Artisan). Each standard cell has a characteristic layout pattern (a specific arrangement of transistors within a fixed cell height). The reverse engineer identifies these patterns by comparing delayered images with known cell libraries (either from published libraries or from libraries reconstructed from other chips fabricated in the same process node).

**Automated tools.** Degate (open-source) provides a complete workflow for die-image analysis: import die images, define wire layers, trace interconnections, identify standard cells by template matching, and extract the netlist. Chipworks (now TechInsights) and System Plus Consulting offer commercial full-chip reverse engineering services that produce verified gate-level netlists for customer chips.

**RE-NNET and neural-network approaches.** Research groups (TU Berlin, University of Florida) have applied convolutional neural networks to automate standard cell recognition from die images. A CNN trained on labeled die images (images of known cells with their logic function) can classify unknown cells with high accuracy (>95% on mature process nodes), dramatically reducing the manual effort of cell identification. These approaches are particularly effective on older nodes (65 nm and above) where cell features are large enough for optical imaging; on advanced nodes (14 nm and below) where SEM imaging is required, the reduced contrast and smaller feature sizes make automated recognition harder.

**Netlist verification.** The extracted netlist is verified against the chip's known behavior: the netlist is simulated in a logic simulator (Cadence Xcelium, Synopsys VCS, or open-source Verilator) and the simulated behavior is compared with the real chip's measured behavior (input-output responses, timing characteristics). Discrepancies indicate extraction errors or undocumented features (which may be backdoors, hidden test modes, or hardware Trojans).

Verification is performed at multiple levels. Functional verification compares the netlist's logical behavior against the chip's documented specification (datasheet, reference manual): does the simulated chip respond correctly to the same inputs? Timing verification compares the netlist's simulated timing (propagation delays through combinational logic paths) against measured timing from silicon (using high-speed digital oscilloscope probing or LVP, §4.4). Coverage verification uses random or directed test patterns to exercise as many logic paths as possible, checking that the simulated responses match the real chip for all tested inputs. The practical coverage achieved depends on the chip's complexity: for a simple 8-bit microcontroller (10,000 gates), near-complete coverage is feasible; for a modern SoC (100 million+ gates), only a fraction of logic paths can be practically verified, and the analyst must focus coverage on security-critical modules (crypto engine, boot ROM logic, access-control logic, privilege management).

For security-focused RE, the analyst specifically searches the extracted netlist for: undocumented I/O connections (signals routed to package pins or test points that are not documented in the datasheet), hidden state machines (FSMs that are not part of the chip's documented functionality — potential backdoors), and unexpected data paths between the security subsystem and external interfaces (potential information-leakage channels).

### 4.7 Die analysis automation code

The die-level analysis phases described in §4.1–4.6 produce large volumes of image data that benefit from automation. The following scripts address three core needs: automated firmware analysis of extracted flash images (Ghidra headless), die-image stitching for full-die composites (OpenCV), and standard cell template matching.

**Ghidra headless analysis of extracted firmware.** After chip-off or in-system extraction (§5), the firmware image is analyzed for structure and code entry points. Ghidra's headless analyzer performs automated disassembly, function identification, and script execution without the GUI:

```bash
#!/usr/bin/env bash
# ghidra_headless_fw.sh — Automated firmware analysis pipeline
# Requires: Ghidra 11.x installed at $GHIDRA_HOME

GHIDRA_HOME="${GHIDRA_HOME:-/opt/ghidra}"
PROJECT_DIR="/tmp/ghidra_projects"
PROJECT_NAME="fw_analysis"
FIRMWARE="$1"
PROCESSOR="${2:-ARM:LE:32:Cortex}"   # default: ARM Cortex 32-bit little-endian

if [ -z "$FIRMWARE" ]; then
    echo "Usage: $0 <firmware.bin> [processor_id]"
    echo "Example processor IDs: ARM:LE:32:Cortex, MIPS:BE:32:default, x86:LE:32:default"
    exit 1
fi

mkdir -p "$PROJECT_DIR"

# Import and auto-analyze the binary
"$GHIDRA_HOME/support/analyzeHeadless" \
    "$PROJECT_DIR" "$PROJECT_NAME" \
    -import "$FIRMWARE" \
    -processor "$PROCESSOR" \
    -analysisTimeoutPerFile 600 \
    -postScript FindCryptoConstants.java \
    -postScript FindStrings.java \
    -scriptlog "$PROJECT_DIR/script_output.log" \
    -log "$PROJECT_DIR/analysis.log" \
    2>&1 | tee "$PROJECT_DIR/headless_stdout.log"

echo "[+] Analysis complete. Project at $PROJECT_DIR/$PROJECT_NAME.rep"
echo "[+] Script output at $PROJECT_DIR/script_output.log"
```

The `FindCryptoConstants.java` script (bundled with Ghidra) searches for known cryptographic S-box tables, round constants, and initialization vectors — identifying crypto implementations in the firmware. Custom Ghidra scripts can extract function names, cross-references to hardware register addresses, and string tables for further RE work.

**Die image stitching and alignment.** When imaging a full die layer-by-layer under a microscope, each layer is captured as a grid of overlapping fields. The following script stitches these fields into a single composite and aligns layers to a common coordinate system:

```python
#!/usr/bin/env python3
"""die_stitch_align.py — Die image stitching and multi-layer alignment.

Stitches a grid of overlapping microscope fields into a full-layer composite,
then aligns multiple layer composites using feature-based registration.

Requires: opencv-python, numpy.
"""

import glob
import os
import sys

import cv2
import numpy as np


def stitch_grid(image_dir: str, rows: int, cols: int, overlap_pct: float = 0.15) -> np.ndarray:
    """Stitch a grid of images with specified overlap.

    Images must be named in row-major order: 00_00.tif, 00_01.tif, ... row_col.tif
    """
    files = sorted(glob.glob(os.path.join(image_dir, "*.tif")))
    if len(files) != rows * cols:
        raise ValueError(f"Expected {rows * cols} images, found {len(files)}")

    sample = cv2.imread(files[0], cv2.IMREAD_GRAYSCALE)
    tile_h, tile_w = sample.shape
    step_x = int(tile_w * (1 - overlap_pct))
    step_y = int(tile_h * (1 - overlap_pct))

    canvas_h = tile_h + (rows - 1) * step_y
    canvas_w = tile_w + (cols - 1) * step_x
    canvas = np.zeros((canvas_h, canvas_w), dtype=np.float64)
    weight = np.zeros_like(canvas)

    for idx, fpath in enumerate(files):
        r, c = divmod(idx, cols)
        tile = cv2.imread(fpath, cv2.IMREAD_GRAYSCALE).astype(np.float64)
        y0, x0 = r * step_y, c * step_x
        canvas[y0:y0 + tile_h, x0:x0 + tile_w] += tile
        weight[y0:y0 + tile_h, x0:x0 + tile_w] += 1.0

    weight[weight == 0] = 1.0
    return (canvas / weight).astype(np.uint8)


def align_layers(ref_path: str, mov_path: str) -> tuple[np.ndarray, np.ndarray]:
    """Align a moving layer to a reference layer using ORB feature matching + affine."""
    ref = cv2.imread(ref_path, cv2.IMREAD_GRAYSCALE)
    mov = cv2.imread(mov_path, cv2.IMREAD_GRAYSCALE)

    orb = cv2.ORB_create(nfeatures=5000)
    kp1, des1 = orb.detectAndCompute(ref, None)
    kp2, des2 = orb.detectAndCompute(mov, None)

    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
    matches = bf.knnMatch(des1, des2, k=2)

    # Lowe's ratio test
    good = [m for m, n in matches if m.distance < 0.75 * n.distance]
    if len(good) < 10:
        raise RuntimeError(f"Insufficient matches ({len(good)}); layers may be too dissimilar")

    src_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)

    matrix, mask = cv2.estimateAffinePartial2D(dst_pts, src_pts, method=cv2.RANSAC)
    aligned = cv2.warpAffine(mov, matrix, (ref.shape[1], ref.shape[0]))
    return aligned, matrix


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: die_stitch_align.py <tile_dir> <rows> <cols>")
        print("  Stitches tiles, writes stitched.tif")
        sys.exit(1)
    tile_dir = sys.argv[1]
    rows, cols = int(sys.argv[2]), int(sys.argv[3])
    composite = stitch_grid(tile_dir, rows, cols)
    cv2.imwrite("stitched.tif", composite)
    print(f"[+] Stitched {rows}x{cols} grid → stitched.tif ({composite.shape[1]}x{composite.shape[0]} px)")
```

The alignment function uses ORB features (fast, license-free) rather than SIFT/SURF. For layer-to-layer registration, the reference layer is typically the top metal layer (which has the most prominent features), and subsequent layers are warped to match. Registration accuracy of < 0.5 pixel is achievable with a sufficient number of inlier matches.

**Standard cell matching prototype.** Once a cell library has been characterized (from a golden reference chip or from published cell layout data), template matching identifies instances of each cell across a delayered die image:

```python
#!/usr/bin/env python3
"""cell_match.py — Standard cell template matching on delayered die images.

Slides each cell template across the die image and reports match locations
above a confidence threshold. Intended as a starting point for building
a cell-library recognition pipeline.

Requires: opencv-python, numpy.
"""

import json
import os
import sys

import cv2
import numpy as np


def match_cell(
    die_image: np.ndarray,
    template: np.ndarray,
    threshold: float = 0.80,
) -> list[tuple[int, int, float]]:
    """Find all occurrences of template in die_image above threshold."""
    result = cv2.matchTemplate(die_image, template, cv2.TM_CCOEFF_NORMED)
    locations = np.where(result >= threshold)
    hits = []
    h, w = template.shape[:2]
    for pt in zip(*locations[::-1]):
        hits.append((int(pt[0]), int(pt[1]), float(result[pt[1], pt[0]])))
    # Non-maximum suppression: remove overlapping detections
    hits.sort(key=lambda x: -x[2])
    filtered = []
    for hx, hy, hs in hits:
        if all(abs(hx - fx) > w // 2 or abs(hy - fy) > h // 2 for fx, fy, _ in filtered):
            filtered.append((hx, hy, hs))
    return filtered


def scan_library(die_path: str, library_dir: str, threshold: float = 0.80) -> dict:
    """Scan die image against all templates in library_dir."""
    die_img = cv2.imread(die_path, cv2.IMREAD_GRAYSCALE)
    if die_img is None:
        raise FileNotFoundError(f"Cannot load {die_path}")

    results = {}
    for tpl_file in sorted(os.listdir(library_dir)):
        if not tpl_file.lower().endswith((".tif", ".png", ".bmp")):
            continue
        tpl = cv2.imread(os.path.join(library_dir, tpl_file), cv2.IMREAD_GRAYSCALE)
        cell_name = os.path.splitext(tpl_file)[0]
        hits = match_cell(die_img, tpl, threshold)
        if hits:
            results[cell_name] = [{"x": x, "y": y, "confidence": round(c, 3)} for x, y, c in hits]
            print(f"  {cell_name}: {len(hits)} instances")
    return results


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: cell_match.py <die_image.tif> <cell_library_dir/> [threshold]")
        sys.exit(1)
    die_path = sys.argv[1]
    lib_dir = sys.argv[2]
    thresh = float(sys.argv[3]) if len(sys.argv) > 3 else 0.80
    print(f"[*] Scanning {die_path} against library {lib_dir} (threshold={thresh})")
    all_hits = scan_library(die_path, lib_dir, thresh)
    with open("cell_matches.json", "w") as f:
        json.dump(all_hits, f, indent=2)
    total = sum(len(v) for v in all_hits.values())
    print(f"[+] Found {total} cell instances across {len(all_hits)} cell types → cell_matches.json")
```

Template matching works well for mature nodes (65 nm+) where standard cells are optically resolvable and have high contrast. At advanced nodes requiring SEM imaging, contrast variations and drift artifacts reduce matching reliability. For sub-28 nm work, CNN-based approaches (RE-NNET, §4.6) are more robust than correlation-based template matching.

### 4.8 Full-chip reverse engineering workflow

A complete chip reverse engineering project follows a structured workflow that may span months for a complex SoC:

**Phase 1: Package-level analysis (1–5 days).** X-ray the package to determine the die size, bond wire count, and die-attach configuration. Identify the package type and pin count. If the package has multiple die (multi-chip module), X-ray reveals the die arrangement and interconnections.

**Phase 2: Decapsulation and top-layer imaging (1–3 days).** Decapsulate the chip using the appropriate method (§3). Image the top metal layer at multiple magnifications. The top metal layer provides the first layout overview: large power rails, bonding-pad ring, and the gross functional block arrangement are visible.

**Phase 3: Layer-by-layer delayering and imaging (weeks to months).** This is the most time-consuming phase. Each metal layer is removed and imaged. For a 10-metal-layer chip, this requires 10 delayering steps, each followed by full-die imaging (which may involve capturing and stitching hundreds or thousands of microscope fields). The polysilicon (gate) layer and active-area (diffusion) layers are imaged after all metal layers are removed. On a mature process node (65 nm), optical microscopy suffices for all layers. On advanced nodes (14 nm and below), SEM imaging is required for the lower metal layers and the transistor level, dramatically increasing the imaging time and cost.

**Phase 4: Image processing and alignment (weeks).** The images from each layer are stitched, aligned to a common coordinate system, and registered (aligning corresponding features across layers so that vias connect correctly between layers). Layer-to-layer registration accuracy must be better than half the minimum feature size — sub-100 nm for modern processes.

**Phase 5: Feature extraction and netlist construction (weeks to months).** Standard cells are identified by template matching against a cell library. Interconnections are traced. The gate-level netlist is assembled. For a chip with 100 million transistors (a mid-range SoC), this step is infeasible by manual methods alone and requires automated or semi-automated tools.

**Phase 6: Netlist analysis and documentation (days to weeks).** The extracted netlist is analyzed: functional blocks are identified (processor core, memory controller, peripherals, security engine), the security-relevant circuitry is isolated and studied in detail, and the results are documented.

The total cost of a full-chip RE project ranges from $50,000 (small microcontroller, mature process, done by a skilled individual with access to equipment) to $50,000,000+ (advanced SoC at 7 nm or below, requiring a large team with cutting-edge SEM and FIB equipment over many months). Commercial RE services (TechInsights, System Plus Consulting) offer various levels of analysis from package identification ($500) to full transistor-level extraction ($1,000,000+).

### 4.9 Process-node challenges

As semiconductor process nodes shrink, hardware reverse engineering becomes progressively harder.

**At 65 nm and above**, optical microscopy resolves all features. Standard cells are large enough for reliable template matching. A single analyst with a good microscope and delayering equipment can reverse-engineer a moderately complex chip in weeks.

**At 28–45 nm**, the finest metal layers and transistor features approach the optical diffraction limit. SEM is required for the lower layers. Standard cell identification remains feasible because cell libraries are well-characterized. Cost and time increase by approximately 3–5× compared to 65 nm.

**At 14–16 nm (FinFET)**, the transition from planar transistors to 3D fin structures makes transistor-level imaging significantly more complex. The fins (vertical silicon structures that form the transistor channel) are 10–15 nm wide and require TEM cross-sectioning for reliable characterization. SEM alone cannot resolve fin count and spacing on some process variants. Standard cell libraries are not publicly available for most FinFET nodes, requiring the analyst to build a cell library from scratch. Cost increases 10–50× compared to 65 nm.

**At 7 nm and below**, extreme ultraviolet (EUV) lithography introduces complex patterning that produces layout features not directly corresponding to the drawn design (the physical shapes on the die are the result of optical proximity correction and multi-patterning, making them look different from the logical layout). Multi-patterning techniques (SADP, SAQP) create features where a single drawn line becomes two or four physical lines, complicating pattern recognition. Full-chip RE at these nodes requires teams of specialists, state-of-the-art SEM/TEM/FIB equipment, and months to years of effort — practical only for nation-state actors and top-tier commercial RE firms.

---

## 5. Memory extraction deep dive

### 5.1 NAND flash internals

NAND flash stores data in floating-gate or charge-trap transistors organized in pages and blocks. Understanding the internal structure is essential for forensic extraction.

**Page structure.** Each NAND page consists of a data area (typically 2048, 4096, 8192, or 16384 bytes) and a spare area (also called OOB — Out-Of-Band, typically 64–1024 bytes per page). The spare area contains ECC data (error correction codes), bad-block markers, and metadata (page sequence numbers, logical-to-physical mapping data for the FTL).

**ECC algorithms.** The ECC in the spare area corrects bit errors caused by read disturb, program disturb, and charge leakage. Common algorithms: Hamming code (corrects 1 bit per 512 bytes — used in older SLC NAND), BCH codes (corrects 4–72 bits per 1 kilobyte — standard for MLC/TLC NAND), and LDPC codes (low-density parity-check, used in modern TLC/QLC NAND with high error rates). To read a NAND dump correctly, the analyst must determine the ECC algorithm and parameters, then apply the correction to recover the original data from the raw dump (which contains bit errors).

**Bad block management.** NAND chips ship with some blocks already marked as bad (manufacturing defects), and additional blocks go bad during the device's lifetime. The bad-block table (BBT) maps logical block addresses to physical block addresses, skipping bad blocks. The BBT is typically stored in a reserved area of the NAND (the last few blocks, or the first few pages of each block's spare area). Reconstructing the BBT is necessary to correctly interpret a raw NAND dump.

**FTL reconstruction.** The Flash Translation Layer (FTL) maps the host's logical block addresses (LBAs) to physical NAND pages. FTL algorithms (page-level mapping for SSDs, block-level mapping for simpler embedded FTLs) are implemented in the NAND controller firmware. A raw NAND dump without FTL knowledge produces scrambled data — the pages are not in logical order. FTL reconstruction requires either: extracting and reverse-engineering the controller's FTL firmware (the definitive approach), or using heuristic methods (searching for known file-system signatures at each page offset and reconstructing the logical order from the found signatures).

### 5.2 eMMC deep dive

eMMC (embedded Multi-Media Controller) integrates a NAND flash array, a NAND controller, and an eMMC interface controller in a single BGA package. The eMMC standard (JEDEC JESD84-B51 for eMMC 5.1) defines the interface protocol, partition structure, and access modes.

**Partition structure.** An eMMC device contains multiple partitions: the user data area (the main storage partition, visible as a block device to the host), boot partition 0 and boot partition 1 (separate small partitions for boot images — the BootROM can be configured to read from these), the RPMB partition (Replay Protected Memory Block — authenticated access for secure storage), and up to 4 General Purpose Partitions (GPP, optional). Each partition has independent access control.

**CID, CSD, and EXT_CSD registers.** The CID (Card Identification) register contains the manufacturer ID, OEM/application ID, product name, product revision, serial number, and manufacturing date. The CSD (Card-Specific Data) register contains the card's data transfer parameters (maximum clock frequency, read/write block sizes, capacity). The EXT_CSD (Extended CSD) register (512 bytes) contains detailed configuration: partition sizes, boot configuration, RPMB size, life-span estimation (device health metrics), HS200/HS400 timing mode support, and security features (secure erase, secure trim, sanitize).

**RPMB authentication.** The RPMB partition uses HMAC-SHA256 authentication for all write operations and authenticated reads. The authentication key is a 256-bit key programmed into the eMMC during manufacturing (via the `CMD23` + `CMD25` sequence with the key-programming data frame). Once programmed, the key cannot be read back or changed. Without the key, RPMB reads return data but the analyst cannot verify its authenticity, and RPMB writes are impossible.

**eMMC forensic tools.** Dedicated eMMC readers (Allsocket eMMC-to-SD adapter, Easy-JTAG Plus, Medusa Pro, Z3X) provide physical-level access to eMMC devices. These tools support: reading all partitions (user, boot0, boot1, RPMB if key is available), reading EXT_CSD and CID/CSD registers, and performing password unlock (if the eMMC password-lock feature is enabled, the tool brute-forces or supplies the password). For in-system eMMC access (without desoldering), the analyst connects to the eMMC's CMD, CLK, and DAT0 lines on the PCB (identified by tracing from the eMMC BGA pads to accessible test points or by following the datasheet's recommended layout). The eMMC interface is electrically compatible with SD (at the protocol level, eMMC uses the same command set as MMC/SD), so a properly wired SD card reader can communicate with an eMMC in-system.

### 5.3 EEPROM extraction

EEPROMs (Electrically Erasable Programmable Read-Only Memory) are small non-volatile memories (typically 256 bytes to 1 Mbit) used to store configuration data, calibration parameters, serial numbers, cryptographic keys, and device credentials. Two interface standards dominate:

**I²C EEPROM (e.g., Microchip 24LC256, Atmel AT24C02).** Two-wire interface (SDA data, SCL clock) with a 7-bit device address (A0–A2 pins set the lower 3 bits, allowing up to 8 EEPROMs on one bus). Reading an I²C EEPROM is straightforward: the analyst connects an I²C master (Bus Pirate, FTDI adapter with Python pyftdi, or a dedicated EEPROM programmer) to the SDA and SCL lines and issues sequential read commands. In-system reading requires identifying the I²C bus on the PCB (often labeled in silkscreen or identifiable by the pull-up resistors on SDA and SCL lines — typically 4.7 kΩ to VCC). Write protection (WP pin tied high) prevents modification but does not prevent reading.

**SPI EEPROM (e.g., Microchip 25LC256, Winbond W25X series).** Four-wire interface (MOSI, MISO, SCK, CS). SPI EEPROMs use a simple command protocol: `0x03` (READ), `0x02` (WRITE), `0x05` (RDSR — read status register). Reading requires a SPI master connected to the four interface lines. The CS (chip select) line must be identified and controlled — in-system reading with the SoC still connected to the SPI bus may require holding the SoC in reset (asserting its RESET line) to prevent bus contention.

**Security-relevant EEPROM data.** EEPROMs commonly store: Wi-Fi credentials (SSID and PSK in plaintext or lightly obfuscated), Bluetooth pairing keys, device serial numbers and MAC addresses, factory calibration data (ADC coefficients, sensor offsets), software license keys, and (in poorly designed systems) cryptographic keys and authentication tokens. Extracting and analyzing EEPROM contents is often the fastest path to understanding a device's security-critical configuration.

### 5.4 OTP, eFuse, and secure storage

**One-Time Programmable (OTP) memory** stores security-critical data: boot configuration, security key hashes, JTAG disable bits, RDP level (on STM32), APPROTECT (on nRF52). OTP is implemented as either: eFuses (electrically programmable fuses — thin polysilicon or metal interconnects that are permanently open-circuited by passing a high current), anti-fuses (dielectric layers that are permanently short-circuited by applying a high voltage), or flash-based OTP (a section of flash memory with the erase circuitry disabled after programming, making it write-once).

Reading OTP values is straightforward if the OTP is memory-mapped and the debug port is accessible — the analyst reads the OTP address range via JTAG/SWD. If the debug port is locked (which is often the purpose of the OTP in the first place), extracting OTP values requires either: fault injection to bypass the debug lock (Chapter 17B §9.2–9.4), or die-level analysis — FIB cross-sectioning of the fuse array to visually determine which fuses are intact (0) and which are blown (1). Blown eFuses show a visible gap in the fuse element under SEM; intact fuses show a continuous conductor.

For anti-fuse-based OTP, the analysis is reversed: a programmed anti-fuse shows a short circuit (visible as a dark spot in the dielectric under SEM), while an unprogrammed anti-fuse shows intact dielectric. The analysis requires SEM or TEM resolution to detect the sub-micron breakdown region in the dielectric.

### 5.5 Chip-off forensics

Chip-off is the forensic technique of physically removing a flash memory chip from a device's PCB and reading it on external equipment. The process:

**Hot-air desoldering.** A hot-air rework station (set to the appropriate temperature profile for the solder type — 217°C liquidus for SAC305 lead-free, with a 30–60 second reflow plateau) is used to desolder the flash chip. For BGA packages, the bottom of the PCB is preheated to 150–180°C (to prevent thermal shock), and the top surface is heated by the hot-air nozzle until the solder balls reflow. The chip is then lifted off with vacuum tweezers.

**BGA reballing.** After removal, the BGA chip's solder balls are typically damaged (smeared, bridged, or missing). Reballing involves: cleaning the ball pads (with solder wick and flux), placing new solder balls (using a reballing stencil — a metal plate with holes matching the ball pattern, filled with solder paste), and reflowing the balls (in a reflow oven or with hot air). The reballed chip can then be mounted in a socket adapter for reading.

**Reading.** The reballed chip is placed in a BGA socket (Allsocket, eMMC Pro, or custom socket) connected to a flash reader (Rusolut VisualNAND, PC-3000 Flash, ACE Lab, or open-source tools with FPGA-based readers). The reader communicates with the flash chip using its native interface (eMMC, UFS, raw NAND parallel interface) and dumps the contents.

**Thermal profile control.** Excessive heat during desoldering can damage the flash chip (corrupting data in NAND cells, degrading oxide layers). Best practice is to use the minimum temperature and duration necessary, monitor the chip-surface temperature with a thermocouple, and avoid multiple reflow cycles. For forensic cases where data integrity is paramount, the thermal profile is documented as part of the chain of custody.

### 5.6 UFS deep dive

Universal Flash Storage (UFS) is the successor to eMMC, used in modern smartphones, automotive infotainment, and high-performance embedded systems. UFS uses the MIPI M-PHY physical layer (serial, differential signaling) and UniPro transport layer, providing much higher throughput than eMMC's parallel interface (UFS 3.1: up to 2.9 GB/s vs. eMMC 5.1: up to 400 MB/s).

**SCSI command set adaptation.** UFS uses a subset of the SCSI Architecture Model (SAM) for command processing. The host sends SCSI commands (READ(10), WRITE(10), INQUIRY, REQUEST SENSE) encapsulated in UFS Protocol Information Units (UPIUs) over the UniPro transport. This is a significant departure from eMMC's MMC command set and requires UFS-specific forensic tools.

**Logical Unit (LUN) structure.** A UFS device contains multiple Logical Units: well-known LUs (boot LU for device-level boot, RPMB LU, device-info LU) and configurable LUs (the main storage partitions). Each LU has its own capacity, boot enable flag, and memory type (enhanced vs. normal). The LU configuration is stored in the device's Configuration Descriptor and can be queried via the UFS Device Manager (a separate command interface from the SCSI command path).

**UFS descriptor hierarchy.** UFS devices expose configuration through a hierarchy of descriptors: Device Descriptor (overall device parameters), Configuration Descriptor (LU allocation), Unit Descriptor (per-LU parameters), Interconnect Descriptor (M-PHY/UniPro parameters), String Descriptor (manufacturer/product strings), Geometry Descriptor (maximum capacities and allocation units), Power Descriptor, and Health Descriptor (device wear indicators, ECC error counts, temperature history). These descriptors provide detailed device characterization for forensic analysis.

**UFS forensic challenges.** UFS is harder to read forensically than eMMC because: the serial M-PHY interface is more complex to implement in custom tooling (eMMC's parallel interface is simpler), the SCSI command set is more complex than eMMC's MMC commands, and many UFS devices use inline encryption (UFS Crypto, defined in JEDEC JESD223D) that encrypts data between the host controller and the NAND flash using AES-256-XTS with per-LU keys. If inline encryption is enabled, a chip-off dump produces encrypted data. Recovering the encryption key requires either: exploiting a vulnerability in the UFS device's key management (the key is typically derived from a hardware root-of-trust key fused into the UFS controller), or accessing the key through the SoC's trusted execution environment (TEE) that provisioned it.

### 5.7 In-system vs chip-off tradeoffs

**In-system reading** connects to the flash chip while it remains soldered to the PCB, using the chip's native interface signals accessible via test points, debug headers, or direct soldering to the signal traces. Advantages: non-destructive, preserves the device's functionality, avoids thermal damage risk, and can be performed repeatedly. Disadvantages: requires identifying and accessing the interface signals on the PCB, may be blocked by the SoC's bus controller (the SoC may not release the bus when the flash needs to be accessed independently), and some interface signals may be inaccessible (routed under BGA packages on inner layers).

**Chip-off reading** removes the flash chip from the PCB. Advantages: direct access to the chip without bus contention from the SoC, works even when the device is non-functional (broken SoC, damaged PCB), and provides access to all partitions including those not normally visible through the SoC's interface (raw NAND pages, spare areas, hidden partitions). Disadvantages: destructive (the device is no longer functional after chip removal), risk of thermal damage to the chip and the PCB, and requires specialized equipment (rework station, reballing setup, compatible socket/adapter).

For forensic investigations, in-system reading is attempted first (less risk, non-destructive). Chip-off is used when in-system access is blocked (debug ports locked, SoC non-functional) or when raw flash access is needed (to recover deleted data from NAND spare areas, analyze FTL metadata, or bypass filesystem-level encryption by accessing the raw encrypted blocks for offline analysis).

A hybrid approach combines both methods: the analyst first performs in-system reading to capture the accessible partitions and filesystem state (preserving timestamps, directory structures, and logical file organization). If more data is needed (deleted files, hidden partitions, raw flash analysis), the analyst then proceeds to chip-off. Comparing the in-system dump with the chip-off dump reveals discrepancies that may indicate hidden partitions, steganographic storage, or filesystem manipulation designed to conceal data from normal access. The in-system dump also serves as a reference for validating the chip-off dump's integrity — if the accessible partitions match between both dumps, the analyst can be confident that the chip-off process did not introduce data corruption.

### 5.8 Memory extraction automation scripts

The following scripts automate the most common post-extraction workflows: parsing raw NAND dumps, reading eMMC partitions, dumping SPI NOR flash and I2C EEPROMs from Python, and analyzing firmware entropy to locate encrypted, compressed, and plaintext regions.

**NAND flash dump parser.** A raw NAND dump (obtained via chip-off or a NAND reader) contains interleaved data and spare/OOB bytes. The controller's page layout, ECC scheme, and FTL mapping must be reconstructed before the data is usable. This script handles the common case of BCH-protected NAND with a block-level FTL:

```python
#!/usr/bin/env python3
"""nand_dump_parser.py — Parse raw NAND dump, apply ECC, reconstruct FTL.

Reads a raw NAND dump file, splits pages into data + spare, applies BCH ECC
correction, and reconstructs the logical block order from FTL metadata in
the spare area.

Requires: bchlib (pip install bchlib), numpy.
"""

import struct
import sys
from pathlib import Path

import numpy as np

try:
    import bchlib
except ImportError:
    sys.exit("Install bchlib: pip install bchlib")


class NANDConfig:
    """NAND geometry and ECC parameters — adjust per target device."""
    page_data: int = 2048          # data bytes per page
    page_spare: int = 64           # spare/OOB bytes per page
    pages_per_block: int = 64
    bch_bits: int = 8              # BCH correction capability (bits per 512B sector)
    bch_poly: int = 8219           # BCH primitive polynomial
    sectors_per_page: int = 4      # 2048 / 512 = 4 ECC sectors per page
    ecc_bytes_per_sector: int = 13 # BCH(8) over 512B needs 13 parity bytes
    # FTL metadata offset within spare area (device-specific)
    ftl_lba_offset: int = 2        # offset in spare where logical block number is stored
    ftl_lba_size: int = 2          # 16-bit logical block number


def parse_dump(dump_path: str, cfg: NANDConfig) -> tuple[dict, bytearray]:
    """Parse raw dump into ECC-corrected pages with FTL reconstruction."""
    raw = Path(dump_path).read_bytes()
    full_page = cfg.page_data + cfg.page_spare
    total_pages = len(raw) // full_page
    total_blocks = total_pages // cfg.pages_per_block

    bch = bchlib.BCH(cfg.bch_poly, cfg.bch_bits)

    corrected_pages = {}
    ecc_failures = 0
    ftl_map: dict[int, int] = {}  # logical_block -> physical_block

    for blk in range(total_blocks):
        for pg in range(cfg.pages_per_block):
            page_idx = blk * cfg.pages_per_block + pg
            offset = page_idx * full_page
            data = bytearray(raw[offset:offset + cfg.page_data])
            spare = raw[offset + cfg.page_data:offset + full_page]

            # Per-sector ECC correction
            corrected = bytearray()
            page_ok = True
            for sec in range(cfg.sectors_per_page):
                sec_data = data[sec * 512:(sec + 1) * 512]
                ecc_off = sec * cfg.ecc_bytes_per_sector
                ecc_data = spare[ecc_off:ecc_off + cfg.ecc_bytes_per_sector]
                try:
                    bitflips = bch.decode(sec_data, ecc_data)
                    bch.correct(sec_data, ecc_data)
                except Exception:
                    page_ok = False
                    ecc_failures += 1
                corrected.extend(sec_data)

            corrected_pages[page_idx] = bytes(corrected)

            # Extract FTL logical block from spare (first page of each block)
            if pg == 0 and page_ok:
                lba_raw = spare[cfg.ftl_lba_offset:cfg.ftl_lba_offset + cfg.ftl_lba_size]
                if len(lba_raw) == cfg.ftl_lba_size:
                    lba = struct.unpack("<H", lba_raw)[0]
                    if lba != 0xFFFF:  # 0xFFFF = erased / unused
                        ftl_map[lba] = blk

    # Reconstruct logical image from FTL map
    logical_image = bytearray()
    for lba in sorted(ftl_map.keys()):
        phys_blk = ftl_map[lba]
        for pg in range(cfg.pages_per_block):
            page_idx = phys_blk * cfg.pages_per_block + pg
            logical_image.extend(corrected_pages.get(page_idx, b"\xff" * cfg.page_data))

    print(f"[+] Parsed {total_pages} pages ({total_blocks} blocks)")
    print(f"[+] ECC failures: {ecc_failures} sectors")
    print(f"[+] FTL mapped {len(ftl_map)} logical blocks")
    return ftl_map, logical_image


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: nand_dump_parser.py <raw_dump.bin> [output.bin]")
        sys.exit(1)
    dump_file = sys.argv[1]
    out_file = sys.argv[2] if len(sys.argv) > 2 else "nand_logical.bin"
    _, image = parse_dump(dump_file, NANDConfig())
    Path(out_file).write_bytes(image)
    print(f"[+] Logical image written to {out_file} ({len(image)} bytes)")
```

The `NANDConfig` parameters must be adapted per target: page and spare sizes are read from the NAND datasheet (or discovered by analyzing the raw dump for the 0xFF pattern that marks erased spare areas), BCH strength is typically documented in the controller datasheet or inferred from the spare area size, and the FTL metadata layout is controller-specific (requiring either controller firmware RE or heuristic analysis of the spare bytes across multiple blocks).

**eMMC partition extractor.** Connecting to an eMMC device via an SD adapter (or a dedicated eMMC socket) and reading all partitions including boot areas and the EXT_CSD register:

```python
#!/usr/bin/env python3
"""emmc_extractor.py — Dump eMMC partitions and register data.

Accesses eMMC via a Linux block device (e.g., /dev/mmcblk0). Reads boot0,
boot1, user data, and EXT_CSD register. Requires root privileges.

Run on a system with the eMMC connected via an SD adapter or eMMC socket
mapped as /dev/mmcblkX.
"""

import struct
import subprocess
import sys
from pathlib import Path


def read_ext_csd(device: str) -> bytes:
    """Read 512-byte EXT_CSD register via MMC ioctl."""
    # mmc-utils provides 'mmc extcsd read' for parsing EXT_CSD
    result = subprocess.run(
        ["mmc", "extcsd", "read", device],
        capture_output=True, text=True,
    )
    print(result.stdout[:2000])  # print first 2000 chars of parsed EXT_CSD
    # Also dump raw EXT_CSD via sysfs if available
    sysfs_path = Path(f"/sys/block/{Path(device).name}/device/ext_csd")
    if sysfs_path.exists():
        return sysfs_path.read_bytes()
    return b""


def dump_partition(device: str, output: str, size_bytes: int = 0) -> None:
    """Dump a block device partition to a file."""
    cmd = ["dd", f"if={device}", f"of={output}", "bs=4M", "status=progress"]
    if size_bytes > 0:
        cmd.append(f"count={size_bytes // (4 * 1024 * 1024) + 1}")
    subprocess.run(cmd, check=True)


def read_cid(device: str) -> str:
    """Read the CID register (manufacturer ID, serial, date code)."""
    cid_path = Path(f"/sys/block/{Path(device).name}/device/cid")
    if cid_path.exists():
        cid = cid_path.read_text().strip()
        # Parse CID fields (JEDEC standard)
        mid = int(cid[0:2], 16)
        oid = bytes.fromhex(cid[2:6]).decode("ascii", errors="replace")
        pnm = bytes.fromhex(cid[6:18]).decode("ascii", errors="replace")
        prv = int(cid[18:20], 16)
        psn = int(cid[20:28], 16)
        mdt = int(cid[28:32], 16)
        print(f"[CID] MID={mid:#x} OID={oid} PNM={pnm} PRV={prv} PSN={psn:#x} MDT={mdt:#x}")
        return cid
    return ""


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: emmc_extractor.py /dev/mmcblk0 [output_dir]")
        sys.exit(1)
    dev = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "./emmc_dump"
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    print("[*] Reading CID register...")
    read_cid(dev)

    print("[*] Reading EXT_CSD register...")
    ext_csd = read_ext_csd(dev)
    if ext_csd:
        Path(f"{out_dir}/ext_csd.bin").write_bytes(ext_csd)

    # Dump boot partitions (boot0 and boot1)
    for bp in ("boot0", "boot1"):
        bp_dev = f"{dev}{bp}"
        if Path(bp_dev).exists():
            print(f"[*] Dumping {bp}...")
            dump_partition(bp_dev, f"{out_dir}/{bp}.bin")

    # Dump user data area
    print(f"[*] Dumping user data area...")
    dump_partition(dev, f"{out_dir}/user_data.bin")

    print(f"[+] All partitions dumped to {out_dir}/")
```

The script requires `mmc-utils` (packaged in most Linux distributions) for EXT_CSD parsing. For eMMC devices connected via an SD adapter, the kernel's `mmc` driver handles the protocol translation. RPMB partition access requires the authentication key and is handled separately via the `mmc rpmb` subcommand.

**SPI NOR flash reader (spidev).** Reading SPI flash directly from a Linux host with a connected SPI programmer (Raspberry Pi GPIO, CH341A mapped to spidev, or FTDI with spi-tools):

```python
#!/usr/bin/env python3
"""spi_flash_reader.py — Read SPI NOR flash via Linux spidev.

Opens a spidev device, sends JEDEC RDID to identify the chip, then reads
the entire flash contents page by page.

Requires: spidev (pip install spidev). Run as root or with spi group membership.
"""

import sys
import time
from pathlib import Path

try:
    import spidev
except ImportError:
    sys.exit("Install spidev: pip install spidev")

# SPI NOR flash standard commands
CMD_RDID = 0x9F        # Read JEDEC ID (manufacturer + device)
CMD_READ = 0x03        # Read data (24-bit address)
CMD_RDSR = 0x05        # Read status register
CMD_FAST_READ = 0x0B   # Fast read (24-bit address + dummy byte)
PAGE_SIZE = 256


def identify_chip(spi) -> tuple[int, int, int]:
    """Send RDID command, return (manufacturer_id, memory_type, capacity)."""
    resp = spi.xfer2([CMD_RDID, 0x00, 0x00, 0x00])
    mfr, mem_type, capacity = resp[1], resp[2], resp[3]
    capacity_bytes = 1 << capacity if capacity > 0 else 0
    print(f"[+] JEDEC ID: MFR={mfr:#04x} TYPE={mem_type:#04x} CAP={capacity:#04x} ({capacity_bytes} bytes)")
    return mfr, mem_type, capacity


def read_flash(spi, size: int, output: str) -> None:
    """Read entire flash contents, page by page."""
    data = bytearray()
    total_pages = size // PAGE_SIZE
    start = time.time()
    for page in range(total_pages):
        addr = page * PAGE_SIZE
        cmd = [CMD_READ, (addr >> 16) & 0xFF, (addr >> 8) & 0xFF, addr & 0xFF]
        resp = spi.xfer2(cmd + [0x00] * PAGE_SIZE)
        data.extend(resp[4:])  # skip command echo bytes
        if page % 1000 == 0 and page > 0:
            elapsed = time.time() - start
            rate = len(data) / elapsed / 1024
            print(f"  {len(data)}/{size} bytes ({rate:.1f} KB/s)")
    Path(output).write_bytes(data)
    elapsed = time.time() - start
    print(f"[+] Read {len(data)} bytes in {elapsed:.1f}s → {output}")


if __name__ == "__main__":
    bus = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    device = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    output = sys.argv[3] if len(sys.argv) > 3 else "spi_flash_dump.bin"

    spi = spidev.SpiDev()
    spi.open(bus, device)
    spi.max_speed_hz = 1_000_000  # 1 MHz — conservative; most flash supports 20+ MHz
    spi.mode = 0b00               # SPI mode 0 (CPOL=0, CPHA=0)

    mfr, mem_type, cap_code = identify_chip(spi)
    flash_size = 1 << cap_code if cap_code > 0 else 0
    if flash_size == 0:
        sys.exit("[-] Could not determine flash size from JEDEC ID")

    read_flash(spi, flash_size, output)
    spi.close()
```

**I2C EEPROM dumper (smbus2).** Sequential read of an entire I2C EEPROM, handling both 8-bit and 16-bit address modes:

```python
#!/usr/bin/env python3
"""i2c_eeprom_dump.py — Dump I2C EEPROM contents via smbus2.

Reads the entire address space of an I2C EEPROM (24Cxx series).
Supports both small (24C02 = 256 bytes, 8-bit address) and large
(24C256 = 32KB, 16-bit address) devices.

Requires: smbus2 (pip install smbus2). Run as root or with i2c group membership.
"""

import sys
import time
from pathlib import Path

try:
    from smbus2 import SMBus, i2c_msg
except ImportError:
    sys.exit("Install smbus2: pip install smbus2")


def dump_eeprom(
    bus_num: int,
    dev_addr: int,
    size: int,
    addr_16bit: bool = False,
    page_size: int = 32,
) -> bytes:
    """Read entire EEPROM in sequential page reads."""
    data = bytearray()
    with SMBus(bus_num) as bus:
        offset = 0
        while offset < size:
            chunk = min(page_size, size - offset)
            if addr_16bit:
                # 16-bit address: write two address bytes, then read
                write = i2c_msg.write(dev_addr, [(offset >> 8) & 0xFF, offset & 0xFF])
                read = i2c_msg.read(dev_addr, chunk)
                bus.i2c_rdwr(write, read)
            else:
                # 8-bit address: write one address byte, then read
                write = i2c_msg.write(dev_addr, [offset & 0xFF])
                read = i2c_msg.read(dev_addr, chunk)
                bus.i2c_rdwr(write, read)
            data.extend(list(read))
            offset += chunk
            time.sleep(0.005)  # brief delay between reads (EEPROM timing)
    return bytes(data)


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: i2c_eeprom_dump.py <bus> <addr_hex> <size_bytes> [16bit]")
        print("Example: i2c_eeprom_dump.py 1 0x50 256      (24C02, 8-bit addr)")
        print("         i2c_eeprom_dump.py 1 0x50 32768 16  (24C256, 16-bit addr)")
        sys.exit(1)
    bus_num = int(sys.argv[1])
    dev_addr = int(sys.argv[2], 16)
    size = int(sys.argv[3])
    addr_16 = len(sys.argv) > 4 and sys.argv[4].startswith("16")
    output = f"eeprom_0x{dev_addr:02x}.bin"

    print(f"[*] Reading {size} bytes from I2C bus {bus_num}, device {dev_addr:#x}...")
    content = dump_eeprom(bus_num, dev_addr, size, addr_16bit=addr_16)
    Path(output).write_bytes(content)
    print(f"[+] Dumped {len(content)} bytes → {output}")
```

**Firmware entropy analysis.** Shannon entropy per block reveals the internal structure of an extracted firmware image — encrypted regions (entropy near 8.0), compressed regions (entropy 6.5–7.5), plaintext/code (entropy 4.0–6.0), and padding/erased blocks (entropy near 0.0):

```python
#!/usr/bin/env python3
"""fw_entropy.py — Shannon entropy analysis with block-level visualization.

Reads a firmware binary, computes per-block Shannon entropy, classifies
regions, and generates an entropy graph (matplotlib PNG or ASCII fallback).

Requires: numpy. Optional: matplotlib for graphical output.
"""

import math
import sys
from collections import Counter
from pathlib import Path

import numpy as np


def shannon_entropy(data: bytes) -> float:
    """Compute Shannon entropy in bits per byte (0.0 – 8.0)."""
    if not data:
        return 0.0
    counts = Counter(data)
    length = len(data)
    return -sum(
        (c / length) * math.log2(c / length)
        for c in counts.values()
        if c > 0
    )


def classify_region(entropy: float) -> str:
    """Heuristic classification based on entropy value."""
    if entropy < 0.5:
        return "PADDING/ERASED"
    elif entropy < 4.0:
        return "STRUCTURED_DATA"
    elif entropy < 6.0:
        return "CODE/PLAINTEXT"
    elif entropy < 7.2:
        return "COMPRESSED"
    else:
        return "ENCRYPTED/RANDOM"


def analyze(firmware_path: str, block_size: int = 4096) -> list[dict]:
    """Compute per-block entropy for the entire firmware image."""
    data = Path(firmware_path).read_bytes()
    blocks = []
    for offset in range(0, len(data), block_size):
        block = data[offset:offset + block_size]
        ent = shannon_entropy(block)
        blocks.append({
            "offset": offset,
            "entropy": round(ent, 4),
            "classification": classify_region(ent),
        })
    return blocks


def plot_entropy(blocks: list[dict], output_png: str = "entropy.png") -> None:
    """Generate entropy graph — matplotlib if available, else ASCII."""
    offsets = [b["offset"] for b in blocks]
    entropies = [b["entropy"] for b in blocks]

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(14, 4))
        ax.fill_between(offsets, entropies, alpha=0.4, color="steelblue")
        ax.plot(offsets, entropies, linewidth=0.5, color="steelblue")
        ax.axhline(y=7.2, color="red", linestyle="--", linewidth=0.8, label="Encrypted threshold")
        ax.axhline(y=6.0, color="orange", linestyle="--", linewidth=0.8, label="Compressed threshold")
        ax.set_xlabel("Offset (bytes)")
        ax.set_ylabel("Shannon Entropy (bits/byte)")
        ax.set_title("Firmware Entropy Profile")
        ax.set_ylim(0, 8.2)
        ax.legend(loc="lower right", fontsize=8)
        fig.tight_layout()
        fig.savefig(output_png, dpi=150)
        print(f"[+] Entropy graph saved to {output_png}")
    except ImportError:
        # ASCII fallback
        print("\n--- Entropy Profile (ASCII) ---")
        max_width = 60
        for b in blocks:
            bar_len = int(b["entropy"] / 8.0 * max_width)
            bar = "#" * bar_len
            print(f"  {b['offset']:#010x} [{b['entropy']:5.2f}] {bar} {b['classification']}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: fw_entropy.py <firmware.bin> [block_size]")
        sys.exit(1)
    fw_path = sys.argv[1]
    blk_size = int(sys.argv[2]) if len(sys.argv) > 2 else 4096
    blocks = analyze(fw_path, blk_size)

    # Summary statistics
    classifications = {}
    for b in blocks:
        classifications.setdefault(b["classification"], []).append(b["offset"])
    print(f"[+] Analyzed {len(blocks)} blocks ({blk_size} bytes each)")
    for cls, offsets in sorted(classifications.items()):
        print(f"  {cls}: {len(offsets)} blocks ({len(offsets) * blk_size} bytes)")

    plot_entropy(blocks)
```

The entropy graph is the single most useful triage artifact for an unknown firmware image. A flat line at 7.9–8.0 across the entire image indicates full-disk encryption (common in modern smartphones with UFS inline encryption). A characteristic sawtooth pattern (alternating high and low entropy blocks) suggests a filesystem with mixed file types. A sharp transition from low entropy to high entropy at a specific offset often marks the boundary between a plaintext bootloader and an encrypted application partition.

---

## 6. Debug interfaces and protocol analysis

### 6.1 JTAG: IEEE 1149.1 and ARM DAP

JTAG (Joint Test Action Group, IEEE 1149.1) was designed for boundary-scan testing but became the de facto debug interface for embedded processors. The interface uses five signals: TDI (Test Data In), TDO (Test Data Out), TMS (Test Mode Select), TCK (Test Clock), and optionally TRST (Test Reset). Data flows serially through the TAP (Test Access Port) controller, a 16-state finite state machine driven by TMS. Critical TAP states: Shift-DR (shift data through the selected data register), Shift-IR (load an instruction selecting the active data register), Run-Test/Idle. Five consecutive TMS=1 clocks from any state force Test-Logic-Reset.

On ARM processors, JTAG connects to the DAP (Debug Access Port) architecture. The DAP consists of a DP (Debug Port) and APs (Access Ports). The AHB-AP provides direct memory-mapped access to the processor's AHB bus — flash, SRAM, peripheral registers, debug control. This grants full firmware extraction, live memory inspection, breakpoint insertion, and register-level control.

JTAG discovery on unknown targets uses combinatorial search across candidate pins. The JTAGulator (Joe Grand) connects to up to 24 pins and tests all permutations, sending TAP sequences and checking for valid IDCODE. JTAGEnum provides an Arduino-based alternative. Manual identification: check for pull-up resistors on TMS/TDI, identify standard ARM debug headers (10-pin Cortex Debug, 20-pin Standard), probe for clock signals during power-up.

Security mechanisms include readout protection (STM32 RDP Level 1/2, nRF52 APPROTECT, ESP32 JTAG disable fuse), ARM CoreSight debug authentication (DBGEN/NIDEN/SPIDEN signals), and password-protected debug. Bypass techniques: voltage glitching the lock-bit read during boot (Domain 17B §9.2–9.4), UV erasure of EPROM-based lock bits on legacy devices, FIB circuit modification on the die, and exploiting firmware vulnerabilities to re-enable debug from software.

Tools: OpenOCD (open-source, GDB server integration, flash programming — supports FTDI/ST-Link/J-Link/CMSIS-DAP), pyOCD (Python scripting for Cortex-M automated extraction), J-Link (SEGGER commercial probe with "connect under reset" to bypass soft-lock), Black Magic Probe (open-source on-probe GDB server).

### 6.2 SWD: ARM Serial Wire Debug

SWD is a two-wire JTAG alternative for ARM Cortex processors (SWDIO + SWCLK), providing identical DAP access. The packet structure: 8-bit request (start/APnDP/RnW/address/parity/stop/park), 3-bit acknowledge (OK/WAIT/FAULT), 33-bit data phase (32 data + parity). SWJ-DP supports both JTAG and SWD on shared pins, switching via a specific bit sequence.

Flash dumping on unprotected targets reads the flash region sequentially through AHB-AP word reads. At 10 MHz SWCLK, 1 MB reads in 2–5 seconds. SWD v2 (ARM ADI v6) adds multi-drop: multiple cores share one bus via TARGETSEL addressing. If one core is locked but another unlocked, the unlocked core may access shared memory — a lateral path that some designs inadequately restrict.

### 6.3 UART identification and exploitation

UART debug consoles are the most common embedded attack surface. Manufacturers frequently ship products with active UART debug in production firmware. TX identification: unpopulated 3/4-pin headers near the processor, pins at VCC that pulse during boot (UART idles high). Baud rate detection: measure shortest pulse width on a logic analyzer, or iterate standard rates (9600/115200/etc.) checking for printable ASCII.

Exploitation paths: Linux root shells with full privilege, U-Boot bootloader prompts (memory read/write via `md`/`mw`, SPI flash access via `sf read`, TFTP boot, boot parameter modification via `setenv`/`saveenv`), proprietary diagnostic shells, and unsigned firmware update interfaces.

### 6.4 SPI and I2C protocol analysis

SPI flash dumping clips an SOIC-8 clip (Pomona 5250) onto external NOR flash (Winbond W25Q, Macronix MX25L, GigaDevice GD25Q), reads via Flashrom using standard SPI commands: RDID (0x9F), READ (0x03 + 24-bit address), RDSR (0x05). Bus contention mitigated by holding processor in reset. Post-extraction: `binwalk -e` for filesystem extraction, `binwalk -E` for entropy visualization.

I2C EEPROM extraction targets configuration storage (Microchip 24LC, Atmel AT24C series) via standard read protocol with Bus Pirate or FTDI adapter. Hardware protocol analyzers (Saleae Logic Pro 16, Total Phase Beagle I2C/SPI) capture live bus traffic non-intrusively, revealing key exchanges, authentication sequences, and configuration operations.

---

## 7. Hardware Trojans

### 7.1 Taxonomy

Hardware Trojans are malicious modifications to an integrated circuit — extra logic inserted during design or fabrication that provides a covert capability (data exfiltration, denial of service, or kill switch). The taxonomy classifies Trojans along several axes.

**Activation mechanism.** Always-on Trojans continuously exfiltrate data (e.g., a covert side channel that leaks key bits through power consumption modulation). Time-bomb Trojans activate after a counter reaches a specific value (e.g., after 2^32 clock cycles — approximately 4 seconds at 1 GHz). Trigger-based Trojans activate only when a specific rare condition occurs (a particular input sequence, a specific date, a combination of register values that never occurs in normal operation). Trigger-based Trojans are the hardest to detect because they are dormant during all normal testing.

**Payload.** Information leakage Trojans exfiltrate secret data (cryptographic keys, military encryption keys) through a covert channel (power, EM, timing, or an added RF transmitter circuit). Denial-of-service Trojans degrade or disable the chip's function when activated (corrupting computation, asserting reset, destroying fuses). Kill-switch Trojans permanently disable the chip (blowing internal fuses, shorting power rails, triggering latch-up in the CMOS substrate).

**Abstraction level.** Gate-level Trojans add extra logic gates to the design (detectable by comparing with a golden reference netlist). Transistor-level Trojans modify individual transistor parameters (channel doping, threshold voltage) without adding extra gates — these are invisible to digital netlist comparison and require analog characterization or side-channel analysis to detect. Analog Trojans (the "A2" Trojan from the University of Michigan, 2016) use a charge-pump circuit built from a single capacitor-connected transistor that slowly charges over billions of clock cycles until it reaches a threshold that flips a security-critical register — an entirely analog activation mechanism that evades all digital detection methods.

### 7.2 Detection methodologies

**Golden reference comparison.** The most direct detection method: compare the suspect chip's die images (obtained through delayering and imaging, §4) with a known-good reference (the "golden" chip, verified to be Trojan-free). Any additional or modified features indicate a potential Trojan. This method is effective against gate-level Trojans but fails against transistor-level modifications (which do not add visible features) and requires a verified golden reference (which may not be available for commercial chips).

**Side-channel fingerprinting.** Each chip has a unique power and EM signature determined by its transistor characteristics and layout. A Trojan that adds extra logic modifies the chip's power profile: the additional switching activity produces a measurable increase in dynamic power consumption, and the additional leakage paths produce a measurable increase in static power. Statistical analysis (comparing the suspect chip's power signature with a population of known-good chips) can detect Trojans that add as few as ~100 gates on a 100,000-gate chip.

**Path-delay analysis.** Logic path delays are sensitive to Trojan modifications that add extra gates to a path. By measuring the propagation delay through multiple logic paths and comparing with expected delays (from simulation or known-good measurement), the analyst can identify paths with anomalous delays that may contain Trojan logic.

**Formal verification.** The chip's extracted netlist (§4.5) is formally verified against a specification or against the original design intent. Properties such as "the key register is never connected to any output pin" can be checked formally. If the netlist violates a property, the violation identifies the potential Trojan. The limitation: formal verification requires a complete and accurate specification, which may not exist for complex commercial chips.

### 7.3 Prevention

**Split manufacturing.** The chip design is split between two or more foundries: one fabricates the front-end-of-line (FEOL — transistors), and another fabricates the back-end-of-line (BEOL — metal interconnections). Neither foundry has the complete design, preventing either from inserting a fully functional Trojan. The limitation: a Trojan in the FEOL (transistor-level modification) would be undetectable by the BEOL foundry, and vice versa.

**Logic locking.** Extra key-controlled gates are added to the design. Without the correct key (stored in a tamper-proof memory on the chip), the circuit produces incorrect outputs. The foundry fabricates the locked design; the key is loaded after fabrication by the design owner. A foundry that steals the design gets a locked (non-functional) netlist. Logic locking must resist SAT-based attacks (Subramanyan et al., 2015): an attacker with input-output access to a functional chip can use a SAT solver to recover the key by iteratively eliminating incorrect key hypotheses using distinguishing input patterns. SAT-attack-resistant locking schemes (Anti-SAT, SARLock, TTLock) add structures that exponentially increase the number of SAT iterations required.

### 7.4 Notable research and real-world context

**The Illinois Trojan (King et al., 2008).** A research group at the University of Illinois demonstrated a hardware Trojan inserted into a SPARC processor core. The Trojan added a shadow memory access mechanism: a specific sequence of rare instructions triggered a mode change that allowed an unprivileged process to access arbitrary physical memory, bypassing the MMU protection. The Trojan added only ~1,000 gates to a ~1,000,000-gate design (0.1% area overhead), making it virtually undetectable by power-based side-channel methods (the additional switching activity is below the measurement noise floor).

**The A2 Trojan (Yang, Hicks, Dong, Austin, Sylvester, 2016).** A capacitor-connected transistor charges over billions of clock cycles through sub-threshold leakage current. When the accumulated charge exceeds the threshold of a sensing inverter, the Trojan activates, modifying a privilege register in the processor. The entire Trojan consists of a single transistor and requires no added logic gates — it is invisible to gate-level netlist comparison. The A2 Trojan demonstrated that purely analog mechanisms can implement hardware Trojans that are undetectable by all digital verification methods, including exhaustive simulation and formal verification.

**Bloomberg/Supermicro allegation (2018).** Bloomberg Businessweek reported that Chinese intelligence agencies had implanted tiny chips (smaller than a grain of rice) on Supermicro server motherboards, compromising servers at Apple, Amazon, and other companies. The companies and the US government agencies involved denied the report, and no independently verified evidence of the implant has been published. The incident, regardless of its factual basis, catalyzed industry attention to hardware supply chain security and led to increased investment in PCB inspection programs, component authentication, and hardware bill of materials (HBOM) tracking.

**Runtime Trojan detection.** Beyond pre-deployment detection (§7.2), runtime Trojan detection monitors the chip's behavior during operation. Side-channel monitoring (continuous power and EM measurement during field operation) can detect the activation of a dormant Trojan — the additional switching activity when the Trojan activates produces a measurable change in the power profile. Built-in self-test (BIST) structures can periodically verify the chip's logic function against expected outputs. Ring oscillator networks (PUF-like structures distributed across the die) detect local temperature and voltage anomalies caused by Trojan activation. These runtime techniques transform Trojan detection from a one-time test into a continuous monitoring capability.

### 7.5 Hardware Trojan detection practical workflow

Translating the detection methodologies of §7.2 into a repeatable pipeline requires integrating optical, electrical, and side-channel techniques into a structured process. The following workflow covers the end-to-end procedure from receiving a suspect batch through issuing a detection verdict.

**Phase 1: Establish the golden reference.** Obtain a known-good sample directly from the IC manufacturer under auditable chain-of-custody. Decapsulate and image the golden sample layer-by-layer (§4.5, §4.8). Store the golden die images in a version-controlled repository at calibrated resolution and magnification. Simultaneously, perform baseline side-channel characterization (power traces during known operations, EM scans at key frequency bands) using the measurement infrastructure described in Chapter 17A §1.1–1.2. The golden power/EM profiles become the statistical reference population; at least 5 golden-sample chips are needed for meaningful statistical comparison (to capture chip-to-chip process variation).

**Phase 2: Side-channel fingerprinting of suspect batch.** For each suspect chip, capture power and EM traces during the same operations used for the golden baseline. The measurement setup (Chapter 17A) is identical, but the analysis here is Trojan-specific: rather than extracting cryptographic keys, the analyst computes the statistical distance (Mahalanobis distance, T-test, or principal component analysis) between the suspect trace population and the golden reference population. A Trojan that adds switching activity shifts the mean and variance of the power profile. The detection sensitivity depends on the Trojan's area overhead relative to the total chip: Trojans above ~0.1% area overhead are detectable via statistical power analysis on chips up to ~1M gates; below 0.1%, the Trojan's switching activity falls within the normal process-variation noise.

**Phase 3: Golden reference die image comparison with ImageJ/FIJI.** For suspect chips that fail or produce borderline side-channel results, proceed to optical die-level comparison. Decapsulate the suspect chip and image the top metal layer. Using ImageJ/FIJI (open-source, Java-based):

The practical workflow in FIJI: open the golden and suspect die images as a two-image stack (Image → Stacks → Images to Stack). Register the two images (Plugins → Registration → StackReg, using rigid-body or affine transformation). After registration, compute the pixel-by-pixel difference (Process → Image Calculator → Subtract). Threshold the difference image (Image → Adjust → Threshold) to highlight regions where the suspect differs from the golden. Regions that exceed the threshold are candidate Trojan sites — they require high-magnification SEM inspection to determine whether the difference is a real structural modification (Trojan) or an artifact (imaging noise, minor process variation in metal line-edge roughness).

For automated batch comparison, FIJI's macro language scripts the entire pipeline:

```
// FIJI macro (ImageJ Macro Language) for automated die comparison
// Save as compare_dies.ijm, run via: fiji --headless -macro compare_dies.ijm

open("/path/to/golden_top_metal.tif");
rename("golden");
open("/path/to/suspect_top_metal.tif");
rename("suspect");
run("Images to Stack", "name=comparison title=[] use");
run("StackReg", "transformation=[Rigid Body]");
run("Stack to Images");
imageCalculator("Subtract create", "golden", "suspect");
selectWindow("Result of golden");
setAutoThreshold("Otsu dark");
run("Analyze Particles...", "size=100-Infinity show=Outlines display");
saveAs("Results", "/path/to/diff_results.csv");
```

The `Analyze Particles` step reports the location, area, and shape of each discrepancy region. Discrepancies smaller than 100 pixels (at the imaging resolution) are filtered as noise. Remaining discrepancies are manually classified: process variation (gradual, diffuse intensity changes across large areas) vs. structural modification (sharp-edged additions or deletions of metal features in localized regions).

**Phase 4: Path-delay measurement.** Trojans that insert extra gates along a signal path increase the path's propagation delay. The measurement setup uses a high-bandwidth oscilloscope (at least 4 GHz analog bandwidth for chips operating above 500 MHz) or a time-to-digital converter (TDC). The analyst identifies critical paths in the chip (from the golden reference netlist or from the chip's specification) and measures the delay through each path by injecting a test pattern on the input and measuring the output transition time. Comparing the measured delay against the golden reference (or against simulation) reveals paths with anomalous extra delay. A Trojan inserting a single extra NAND gate on a path adds approximately 20–50 ps of delay (depending on the process node) — detectable with a TDC or a high-speed sampling oscilloscope, but at the edge of measurement precision for paths with inherently large delays.

**Phase 5: Ring oscillator array for runtime monitoring.** For deployed systems where destructive analysis is not possible, ring oscillator (RO) arrays provide runtime Trojan detection. An array of identical ring oscillators distributed across the die (either as part of the original design or as an IP block added to the design for supply-chain security) measures local process, voltage, and temperature (PVT) conditions. A Trojan that activates on the die creates a localized power or thermal perturbation, which the nearest RO detects as a frequency shift. The RO frequencies are periodically sampled and compared against a baseline (established at manufacturing time under known PVT conditions). A frequency shift exceeding the expected PVT envelope indicates a potential local anomaly — either a Trojan activation or a reliability event (electromigration, hot carrier degradation).

**Phase 6: Verdict and reporting.** The results from all phases are aggregated into a detection report with a three-level verdict: CLEAR (all tests pass, no discrepancies above threshold), SUSPECT (borderline results in one or more tests — requires additional analysis or a larger sample size), or COMPROMISED (definitive evidence of structural modification or anomalous behavior inconsistent with process variation). A COMPROMISED verdict triggers the security response protocol: quarantine the suspect lot, notify the IC manufacturer and upstream suppliers, file a GIDEP/ERAI report, and initiate a broader investigation across all components sourced through the same supply chain.

---

## 8. Defensive PCB and chip design

### 8.1 Anti-tamper PCB design

**BGA underfill.** Applying epoxy underfill beneath BGA packages prevents physical access to the solder balls and makes IC desoldering difficult (the underfill mechanically bonds the IC to the PCB, requiring aggressive heating or chemical dissolution to remove). Underfill is standard on automotive and aerospace PCBs for reliability (thermal cycling resistance) and provides a tamper-deterrence benefit.

**Buried and blind vias.** Routing critical signals on inner layers (using buried vias that connect only internal layers) hides them from surface probing. An attacker with only surface access cannot tap or monitor these signals without destructive delayering.

**Signal integrity obfuscation.** Running security-critical signals alongside high-speed differential pairs (which generate significant EM emissions) makes it harder to isolate the security signal from the surrounding noise. Ground-plane flooding (filling unused PCB area with ground copper) adds shielding that reduces EM emanations from internal traces.

### 8.2 Anti-reverse-engineering IC design

**Camouflaged gates.** IC design techniques that make standard cells visually identical under optical microscopy, despite having different logic functions. By modifying the dopant implants (which are invisible to optical or SEM imaging without cross-sectioning every gate) while keeping the metal layout identical, the designer creates cells where the visual appearance does not reveal the logic function. The reverse engineer must individually probe or cross-section each cell to determine its function — multiplying the analysis effort by orders of magnitude.

**Active shield.** A fine metal mesh (typically the top metal layer, routed as a dense, random-looking pattern that covers the entire die surface) is continuously monitored for continuity and integrity. If the mesh is cut (by FIB milling) or shorted (by probe contact), the shield circuit detects the change and triggers a tamper response (key zeroization, chip lockout). The shield mesh is designed to be difficult to bypass: the routing is randomized, the monitoring circuit uses multiple redundant sense points, and the shield integrity is checked at random intervals.

**PUF-based authentication (Physical Unclonable Functions).** PUFs generate a unique, device-specific key derived from manufacturing process variations (SRAM power-up state, ring oscillator frequencies, arbiter circuit race conditions). The PUF output is used for device authentication: the device proves its identity by demonstrating that it possesses the correct PUF response for a given challenge. Because the PUF is based on physical characteristics of the specific die (not stored data), it cannot be cloned or extracted by read-out attacks. SRAM PUFs (the power-up state of uninitialized SRAM cells is determined by random threshold-voltage variations) are the most widely deployed PUF type, used in NXP LPC microcontrollers, Microsemi SmartFusion2 FPGAs, and Intrinsic ID's QuiddiKey IP.

### 8.3 Anti-FIB and anti-probing measures

**Metal mesh shields with redundant sensing.** Advanced secure elements (Infineon SLE 78, NXP SmartMX3, Samsung SE) implement multi-layer active mesh shields: two or more metal layers are used for mesh routing, with the mesh patterns on different layers being complementary (the mesh on layer N covers the gaps in the mesh on layer N-1). The mesh is driven with a pseudo-random bit stream, and the integrity of the stream is verified at the receive end. Cutting any mesh wire interrupts the bit stream, triggering tamper detection within one clock cycle (nanoseconds). FIB rerouting (cutting the mesh and depositing a bypass connection) must be done for every mesh wire in the analyst's path to the target — which may number in the hundreds, making bypass infeasible within a reasonable timeframe.

**Glue logic obfuscation.** Instead of using standard cells from a library (which can be identified by template matching, §4.6), the designer places custom logic structures that do not correspond to any standard cell. The reverse engineer cannot use automated cell recognition and must manually analyze each custom structure — equivalent to solving a unique logic puzzle for each gate.

**Buried interconnect and via encryption.** On advanced process nodes, security-critical interconnections are routed on the lower metal layers (closest to the transistors), buried under 10+ layers of upper metallization. The analyst must delayer through all upper layers to reach the security logic, destroying the upper-layer routing information in the process. Combined with camouflaged gates (§8.2), this forces the reverse engineer to perform a complete, destructive, layer-by-layer analysis of the entire chip — the most expensive and time-consuming form of hardware RE.

**Self-destructing key storage.** Some secure elements store cryptographic keys in volatile SRAM that is powered by an internal battery or capacitor. If the tamper-detection system triggers (mesh cut, decapsulation detected, voltage/temperature anomaly), the power to the key SRAM is immediately cut, erasing the keys. The battery backup ensures the keys survive power removal during normal operation but not during a tamper event. This architecture means that any successful physical attack on the chip erases the keys before the attacker can extract them.

### 8.4 PCB-level anti-tampering for fielded systems

For systems deployed in physically hostile environments (ATMs in unattended locations, military equipment in contested areas, IoT gateways in public infrastructure), PCB-level anti-tampering measures complement IC-level protections:

**Tamper-responsive enclosures.** The PCB is enclosed in a sealed housing with tamper-detection mechanisms: micro-switches on the enclosure seams (detecting opening attempts), conductive mesh embedded in the enclosure walls (detected if cut or drilled through), pressure sensors (detecting pressure changes from drilling or milling), and light sensors (detecting enclosure breach). When tamper is detected, the enclosure's tamper-response circuit triggers key zeroization in the secure processor and may disable the device permanently.

**Conformal coating and potting.** Conformal coating (a thin polymer layer — urethane, silicone, or acrylic — applied to the entire PCB surface) provides moisture and dust protection and makes component desoldering harder (the coating must be removed first). Potting (filling the entire enclosure with opaque epoxy resin) encapsulates all components, making physical access to any IC or trace require cutting through hardened resin. Potting compounds can be formulated to be thermally insulating (making hot-air rework infeasible without overheating the target components) and chemically resistant (resisting solvents that might dissolve the resin).

**FIPS 140-3 Level 4 requirements.** The highest physical security level in FIPS 140-3 requires: tamper detection and response (active monitoring with key zeroization on tamper), environmental protection (voltage and temperature monitoring with fault-injection resistance — Domain 17B §9), and multi-fault resistance (the device must resist combined attacks — simultaneous temperature, voltage, and physical tampering). Level 4 certification requires extensive physical testing by an accredited laboratory, including: decapsulation attempts, FIB probing, fault injection campaigns, and side-channel analysis — the same techniques described throughout Domain 17 are used to evaluate the device's resistance. Achieving FIPS 140-3 Level 4 typically costs $500,000–$2,000,000 in certification testing alone, in addition to the engineering cost of implementing the countermeasures.

---

## 9. Cost and capability tiers for hardware RE

Hardware reverse engineering capability scales across distinct tiers, each with different equipment requirements, costs, and achievable outcomes. Understanding these tiers helps both attackers (assessing feasibility) and defenders (calibrating countermeasure investment).

**Tier 1: Hobbyist/researcher ($500–$5,000).** Equipment: multimeter, soldering station, USB logic analyzer (Saleae Logic 8), USB oscilloscope (PicoScope), Bus Pirate or FTDI breakout, flash programmers (CH341A, RT809H). Capabilities: UART console access, SPI/I²C EEPROM dumping, basic JTAG/SWD if pins are known, in-system flash reading, bus traffic capture. Limitations: cannot desolider BGA components, no X-ray, no microscopy beyond basic USB microscope, no decapsulation capability.

**Tier 2: Professional lab ($50,000–$500,000).** Equipment: hot-air rework station with BGA nozzles, stereomicroscope with camera, dedicated logic analyzer (DSLogic Plus, Saleae Logic Pro 16), benchtop oscilloscope (Keysight, Tektronix), ChipWhisperer-Husky (for combined RE/fault injection), JTAGulator, dedicated eMMC/UFS readers (Easy-JTAG Plus, Z3X), fume hood with acid decapsulation capability. Capabilities: BGA desoldering and chip-off forensics, chemical decapsulation, basic die imaging, eMMC/UFS full-partition dumping, JTAG/SWD pin discovery, protocol analysis on all standard buses, voltage glitching and basic EMFI.

**Tier 3: Advanced lab ($500,000–$5,000,000).** Equipment: X-ray CT/micro-CT system, SEM with EDS, metallographic grinding/polishing station, plasma asher, wire bonder, Riscure Inspector (SCA + FI), ChipSHOUTER, motorized X-Y-Z probe station. Capabilities: full multi-layer PCB RE via X-ray CT, die delayering and imaging (optical + SEM), FIB cross-sectioning (if FIB system included), standard cell identification on mature nodes, complete chip-off forensics with reballing, advanced fault injection campaigns, side-channel analysis, counterfeit IC detection per SAE AS6171.

**Tier 4: Nation-state / top-tier commercial ($5,000,000+).** Equipment: FIB-SEM dual-beam system, TEM, laser voltage probing system, photon emission microscopy, advanced laser FI station, clean-room decapsulation facility, automated delayering and imaging pipeline. Capabilities: full transistor-level reverse engineering at any process node, circuit edit via FIB, hardware Trojan insertion or detection at the transistor level, breaking state-of-the-art secure elements. Organizations at this tier include TechInsights, the NSA's Trusted Access Program Office (TAPO), GCHQ's hardware laboratory, and the Chinese MSS/PLA hardware labs.

---

## 10. Firmware anomaly detection rules

Firmware images extracted via chip-off (§5.5) or in-system reading (§5.7) should be scanned for anomalies before deep manual analysis. The following YARA and Sigma rules target patterns commonly found in backdoored, tampered, or poorly secured embedded firmware. These rules are complementary to — and do not duplicate — the UEFI/secure-boot-specific detection rules in Chapter 17D §7.7.

### 10.1 YARA rules for firmware anomalies

**Embedded backdoor credentials.** Firmware with hardcoded default passwords is a pervasive issue in embedded devices (routers, cameras, industrial controllers). These rules detect common patterns:

```yara
rule Firmware_Backdoor_Credentials
{
    meta:
        description = "Detects hardcoded default credentials in firmware images"
        severity    = "HIGH"
        category    = "backdoor"
        date        = "2026-05-08"
    strings:
        // Common default username:password pairs
        $cred01 = "admin:admin" ascii wide
        $cred02 = "root:root" ascii wide
        $cred03 = "admin:password" ascii wide
        $cred04 = "root:12345" ascii wide
        $cred05 = "admin:1234" ascii wide
        $cred06 = "user:user" ascii wide
        $cred07 = "root:toor" ascii wide
        $cred08 = "supervisor:supervisor" ascii wide
        // /etc/shadow patterns with known weak hashes
        $shadow01 = "root:$1$" ascii    // MD5crypt root hash
        $shadow02 = "root::0:0" ascii   // empty root password in passwd format
        $shadow03 = "admin:$1$" ascii
        // Hardcoded credentials in C strings
        $csrc01 = "default_password" ascii nocase
        $csrc02 = "hardcoded_key" ascii nocase
        $csrc03 = "backdoor" ascii nocase
    condition:
        2 of them
}

rule Firmware_Hardcoded_Crypto_Keys
{
    meta:
        description = "Detects patterns consistent with hardcoded cryptographic key material"
        severity    = "CRITICAL"
        category    = "crypto"
        date        = "2026-05-08"
    strings:
        // RSA private key headers (PEM)
        $rsa_pem    = "-----BEGIN RSA PRIVATE KEY-----" ascii
        $ec_pem     = "-----BEGIN EC PRIVATE KEY-----" ascii
        $pk8_pem    = "-----BEGIN PRIVATE KEY-----" ascii
        // Known test/default AES keys (128-bit)
        $aes_test1  = { 00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f }
        $aes_test2  = { 2b 7e 15 16 28 ae d2 a6 ab f7 15 88 09 cf 4f 3c } // FIPS AES test vector
        // Symmetric key-like high-entropy sequences near string references
        $keyref01   = "encryption_key" ascii nocase
        $keyref02   = "aes_key" ascii nocase
        $keyref03   = "secret_key" ascii nocase
        $keyref04   = "master_key" ascii nocase
    condition:
        any of ($rsa_pem, $ec_pem, $pk8_pem) or
        any of ($aes_test*) or
        2 of ($keyref*)
}

rule Firmware_Modified_Bootloader
{
    meta:
        description = "Detects bootloader images with anomalous signature patterns"
        severity    = "HIGH"
        category    = "integrity"
        date        = "2026-05-08"
    strings:
        // U-Boot banner with modification indicators
        $uboot_mod  = "U-Boot" ascii
        $uboot_cust = "custom" ascii nocase
        $uboot_mod2 = "modified" ascii nocase
        $uboot_dbg  = "debug build" ascii nocase
        // Disabled signature verification strings
        $sigdis01   = "signature check disabled" ascii nocase
        $sigdis02   = "verify=no" ascii nocase
        $sigdis03   = "secure_boot=0" ascii nocase
        $sigdis04   = "skip_verify" ascii nocase
        // Padding with 0x00 where signature should be (nulled signature field)
        $null_sig   = { 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
                        00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
                        00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
                        00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 }
    condition:
        $uboot_mod and (any of ($uboot_cust, $uboot_mod2, $uboot_dbg, $sigdis*)) or
        (any of ($sigdis*) and $null_sig)
}

rule Firmware_Embedded_Debug_Server
{
    meta:
        description = "Detects firmware with embedded shell/debug servers bound to all interfaces"
        severity    = "HIGH"
        category    = "backdoor"
        date        = "2026-05-08"
    strings:
        // Telnet daemon listening on all interfaces
        $telnet01  = "telnetd" ascii
        $bind_all  = "0.0.0.0" ascii
        $bind_any  = "INADDR_ANY" ascii
        // SSH debug server
        $sshd01    = "/usr/sbin/sshd" ascii
        $dropbear  = "dropbear" ascii
        // Debug shell spawners
        $shell01   = "/bin/sh -i" ascii
        $shell02   = "exec /bin/bash" ascii
        $shell03   = "/system/bin/sh" ascii
        // GDB server stubs (embedded debug)
        $gdbstub   = "gdbserver" ascii
        $gdbport   = ":1234" ascii
        // Busybox debug applets
        $bbox_tel  = "busybox telnetd" ascii
    condition:
        ($telnet01 or $sshd01 or $dropbear or $bbox_tel) and ($bind_all or $bind_any) or
        ($shell01 or $shell02) and ($bind_all or $bind_any) or
        $gdbstub and $gdbport
}

rule Firmware_Packed_UPX
{
    meta:
        description = "Detects UPX-packed or custom-packed firmware binaries"
        severity    = "MEDIUM"
        category    = "packing"
        date        = "2026-05-08"
    strings:
        // UPX magic signatures
        $upx_magic  = "UPX!" ascii
        $upx_header = { 55 50 58 21 }
        // UPX section names in ELF
        $upx_elf    = ".UPX" ascii
        // LZMA header (commonly used by custom firmware packers)
        $lzma_hdr   = { 5D 00 00 }
        // Custom packer indicators
        $stub01     = "decompressor" ascii nocase
        $stub02     = "unpacker" ascii nocase
        $stub03     = "self-extracting" ascii nocase
    condition:
        any of ($upx_*) or
        ($lzma_hdr at 0 and filesize < 5MB) or
        2 of ($stub*)
}
```

These rules should be run against extracted firmware images using `yara -r rules/ firmware_dump.bin`. The `-r` flag enables recursive rule loading from a directory. For large firmware images (> 100 MB), use `yara --fast-scan` to reduce scan time at the cost of some detection granularity.

### 10.2 Sigma rules for hardware tampering indicators

Sigma rules for hardware-level events target log sources from firmware update daemons, secure boot verification logs, and hardware monitoring systems. These are distinct from the debug interface and UEFI Sigma rules in Chapter 17D §7.7 — the rules here focus on physical tampering indicators observable through firmware or system logs.

```yaml
title: SPI Flash Write Outside Firmware Update Window
id: a3c7e501-9b2f-4d1a-8e3c-1f2a5b6c7d8e
status: experimental
description: >
  Detects SPI flash write operations occurring outside a scheduled firmware
  update window, which may indicate unauthorized firmware modification via
  a hardware debug interface or an in-circuit SPI programmer.
date: 2026-05-08
logsource:
  product: embedded_firmware
  service: spi_flash_monitor
detection:
  selection:
    event_type: "spi_flash_write"
  filter_legitimate:
    update_mode: true
  condition: selection and not filter_legitimate
level: high
tags:
  - attack.persistence
  - attack.t1542.001
falsepositives:
  - Legitimate firmware updates that do not set the update_mode flag
  - Factory provisioning operations
---
title: Tamper Switch Triggered
id: b4d8f602-ac3f-5e2b-9f4d-2g3b6c7d8e9f
status: experimental
description: >
  Detects tamper switch activation events from hardware security modules
  or tamper-responsive enclosures. Indicates physical access attempt to
  protected hardware.
date: 2026-05-08
logsource:
  product: hsm
  service: tamper_monitor
detection:
  selection:
    event_type|contains:
      - "tamper_alert"
      - "enclosure_breach"
      - "mesh_fault"
      - "case_open"
  condition: selection
level: critical
tags:
  - attack.initial_access
  - attack.t1200
falsepositives:
  - Authorized maintenance with tamper override credentials
---
title: Firmware Integrity Check Failure at Boot
id: c5e9g703-bd4g-6f3c-ag5e-3h4c7d8e9f0g
status: experimental
description: >
  Detects firmware hash/signature verification failures during the boot
  process, indicating either firmware corruption or deliberate modification
  (e.g., via chip-off + reflash attack).
date: 2026-05-08
logsource:
  product: bootloader
  service: secure_boot
detection:
  selection:
    event_type|contains:
      - "signature_verify_fail"
      - "hash_mismatch"
      - "integrity_check_fail"
      - "fw_verify_error"
  condition: selection
level: critical
tags:
  - attack.defense_evasion
  - attack.t1542
falsepositives:
  - Firmware corruption from power loss during update
  - Flash memory bit-rot on aging devices
```

### 10.3 Physical tamper indicators checklist

During incoming inspection of devices returned from the field or received from untrusted supply chains, the following physical indicators warrant further investigation:

Evidence of enclosure opening manifests as scratched or marred screw heads (particularly security Torx/pentalobe screws), cracked or re-glued ultrasonic weld seams on plastic enclosures, adhesive residue from removed tamper-evident labels, or misaligned enclosure seams that do not match the factory tolerance. On the PCB itself, signs of rework include flux residue around ICs that were not present during factory assembly (indicating desoldering and resoldering), solder joint morphology inconsistent with the original reflow profile (hand-soldered joints have a characteristically different surface texture from machine-reflowed joints), missing or replaced components (comparing against the board's BOM and placement data), and added components (extra ICs, wires, or passive components not on the original BOM — potential hardware implants).

For supply chain verification, a Hardware Bill of Materials (HBOM) serves the same role as a Software Bill of Materials (SBOM) in software supply chain security. The HBOM lists every component on the board with its manufacturer, part number, authorized distributor source, lot code, and inspection status. HBOM validation compares the physical board against the declared HBOM: each component is visually verified (marking matches BOM entry), and a sample undergoes the counterfeit detection workflow (§2.4). Automated HBOM validation uses machine vision (photographing the assembled board and using OCR + component database lookup to verify each component's marking against the BOM) — an emerging capability being adopted by defense and aerospace contractors for high-assurance hardware procurement.

---

## 11. CVE reference table for hardware and firmware vulnerabilities

The following table maps hardware and firmware CVEs to specific device families, attack classes, equipment requirements (mapped to the tiers in §9), and detection methods. This provides a quick-reference for assessing whether a specific hardware target has known vulnerability research applicable to its analysis.

| CVE | Device / Family | Attack Type | Tier | Detection Method |
|-----|----------------|-------------|------|-----------------|
| CVE-2020-13629 | STM32F0/F1/F3 (RDP Level 1) | Debug readout bypass via voltage glitch during RDP check | Tier 2 ($200 — ChipWhisperer) | Monitor power trace during boot for glitch signature; verify RDP fuse state via FIB cross-section |
| CVE-2020-27212 | STM32F1 (RDP Level 2) | Voltage fault injection during option-byte load bypasses RDP2 irreversible lock | Tier 2 ($500 — ChipWhisperer + custom target board) | RDP2 fuse verification via SEM; power trace anomaly detection during boot |
| CVE-2020-17445 | nRF52840 (APPROTECT) | Voltage glitch on APPROTECT register read window enables debug re-attach | Tier 2 ($200 — ChipWhisperer-Lite) | SWD response monitoring; verify APPROTECT fuse via die inspection |
| CVE-2019-15894 | ESP32 (Secure Boot v1) | TOCTOU fault injection during signature verification allows unsigned code execution | Tier 2 ($300 — EMFI probe + pulse generator) | Boot log integrity monitoring; secure boot v2 migration eliminates the attack surface |
| CVE-2017-13156 | Android (Janus) | APK signature bypass via DEX/APK polyglot — not hardware but affects firmware delivered via OTA | Tier 1 ($0 — software only) | APK signature verification with v2/v3 scheme enforcement |
| CVE-2020-0069 | MediaTek MT67xx (DA mode) | Unauthorized memory read/write via Download Agent (DA) in BROM — accesses all eMMC partitions | Tier 1 ($50 — USB cable + mtkclient) | Disable DA download in production fuses; monitor USB enumeration for DA mode entry |
| CVE-2017-6249 | Qualcomm EDL (Firehose) | Programmer image loaded via EDL mode enables raw eMMC read — authentication bypass through signed programmer leak | Tier 1 ($50 — USB cable + QDL tools) | Block EDL entry in production fuses; RPMB key isolation |
| CVE-2021-1961 | Qualcomm (DSP) | Heap overflow in Qualcomm DSP firmware (Hexagon) allows code execution on the DSP — enables side-channel from co-processor | Tier 1 ($0 — software exploit) | DSP firmware hash verification; runtime integrity monitoring |
| CVE-2020-13799 | eMMC RPMB (various) | RPMB authentication key derivable from CID on some vendors' implementations — CID is public, key is supposed to be secret | Tier 1 ($10 — eMMC reader) | Verify RPMB key derivation uses device-unique entropy beyond CID; test with known-CID computation |
| CVE-2019-14615 | Intel (GPU) | Uninitialized GPU memory readable by unprivileged processes — leaks kernel/other-process data residue | Tier 1 ($0 — software) | Kernel patch verification; GPU memory scrubbing |
| CVE-2023-20569 | AMD (Inception / SRSO) | Speculative return address injection via branch predictor training — transient execution side channel | Tier 1 ($0 — software) | Microcode update verification; kernel mitigation (IBPB on VMEXIT) |
| CVE-2017-5715 | Intel/AMD/ARM (Spectre v2) | Branch target injection via indirect branch predictor poisoning — cross-process secret extraction | Tier 1 ($0 — software) | Retpoline deployment verification; microcode IBRS/STIBP enablement |

The tier ratings reflect the minimum equipment needed to execute the attack, not the skill level required. Many Tier 1 attacks require substantial reverse engineering expertise despite needing only commodity hardware. The detection methods focus on what a defender can verify or monitor — not on preventing the attack (which often requires silicon revision or vendor firmware updates).

---

## 12. Advanced PCB analysis techniques

### 12.1 X-ray computed tomography for multi-layer PCB inspection

While §1.3 introduced X-ray CT in the context of initial reconnaissance, advanced CT workflows extract far more intelligence from the raw volumetric data. Modern micro-CT systems (Zeiss Xradia Versa, Nikon XT H 225 ST, Bruker SkyScan 2214) achieve voxel resolutions below 1 µm, sufficient to resolve individual traces on 6-layer HDI boards with 75 µm line/space geometries. The workflow for a full-board CT-based reverse engineering campaign:

**Scan planning.** The analyst selects the region of interest (ROI) — typically the area around the main SoC, secure element, or a suspicious component identified during visual inspection. Scan parameters (voltage 80–225 kV, current 50–200 µA, exposure time 0.5–4 seconds per projection, number of projections 1600–3200) trade off resolution against scan time. A 10 mm × 10 mm ROI at 2 µm voxel resolution takes approximately 2–4 hours; a full 100 mm × 100 mm board at 10 µm resolution takes 8–16 hours.

**Reconstruction and segmentation.** Raw projections are reconstructed using filtered back-projection (FBP) or iterative algebraic reconstruction technique (ART). Beam-hardening correction is essential for PCBs — the high-Z copper layers cause cupping artifacts that obscure low-contrast features. Metal artifact reduction (MAR) algorithms reduce streak artifacts from BGA balls and thick copper planes. After reconstruction, the volume is segmented into material classes: copper (traces, planes, vias), solder (balls, joints), FR-4 dielectric, component bodies (ceramic, plastic, silicon). Segmentation is performed via thresholding (Hounsfield unit ranges) or ML-assisted classification.

**Virtual delayering.** The segmented volume is sliced along the Z-axis at each copper-layer depth, producing virtual cross-sections equivalent to physical delayering but without destroying the board. Each virtual layer is exported as a high-resolution image (TIFF or PNG at native voxel resolution) for subsequent trace extraction and vectorization. This approach is repeatable — the same dataset can be re-analyzed at different orientations or depths.

**Gerber reconstruction from CT data.** The virtual layer images are imported into vectorization software (see §1.5 for PCBFlow and manual vectorization). Specialized tools such as diondo d-trace and Volume Graphics VGStudio MAX offer semi-automated trace extraction from CT volumes, producing DXF or Gerber files from the voxel data. The resulting Gerber files can be imported into KiCad, Altium, or Cadence for schematic reverse engineering.

```bash
# Example: Bruker SkyScan CT reconstruction using NRecon CLI
NRecon --input /data/scan_001/ \
       --output /data/recon_001/ \
       --smoothing 1 \
       --beam-hardening-correction 40 \
       --ring-artifact-correction 8 \
       --misalignment-correction auto \
       --output-format TIFF16

# Virtual slicing with ImageJ/Fiji macro for layer extraction
fiji --headless --run "Virtual Slicer" \
     "input=/data/recon_001/,axis=Z,start=120,end=125,step=1,output=/data/layers/"
```

### 12.2 Time-domain reflectometry for hidden interconnect detection

Time-domain reflectometry (TDR) transmits a fast-rise-time pulse (typically 35–150 ps rise time) into a PCB trace and measures the reflected waveform. Impedance discontinuities — junctions, vias, stubs, unterminated branches, or covert taps — produce reflections whose amplitude and timing reveal the location and nature of the discontinuity. TDR is invaluable for detecting covert hardware modifications: a surreptitious wire tap, solder bridge, or interposer introduces an impedance discontinuity that is invisible to visual inspection but detectable by TDR.

**Equipment.** High-bandwidth TDR modules are available as options on sampling oscilloscopes: Keysight N1930B TDR module (35 ps rise time, 20 GHz bandwidth), Tektronix DSA8300 with 80E10B module (15 ps rise time, 50 GHz bandwidth), or standalone instruments like the Mohr CT100 (dedicated TDR for PCB characterization). Cost ranges from $5,000 (used Tektronix TDR head) to $150,000 (new high-end sampling oscilloscope with TDR).

**Procedure for covert interconnect detection:**

1. Obtain a known-good reference board (golden sample) — or a board from a trusted batch.
2. Probe each critical trace (power rail, data bus, clock line) with the TDR and record the baseline impedance profile.
3. Probe the same traces on the suspect board.
4. Compare the two impedance profiles. Discrepancies indicate physical differences — added components, extra trace stubs, or modified via structures.
5. Localize the anomaly using the TDR time-to-distance calculation: distance = (propagation velocity × round-trip time) / 2. For FR-4, propagation velocity is approximately 15 cm/ns (half the speed of light in vacuum, adjusted for the dielectric constant εr ≈ 4.2).

```
# Keysight TDR measurement setup (SCPI commands via LAN/GPIB)
:CHAN1:TDR ON
:CHAN1:TDR:STEP:RISETIME 40E-12
:TIMebase:SCALe 500E-12       # 500 ps/div for fine resolution
:TIMebase:POSition 2E-9       # 2 ns offset to center the reflection
:CHAN1:SCALe 5                 # 5 ohms/div impedance scale
:CHAN1:OFFSet 50               # center on 50 ohms
# Capture and export
:WAVeform:SOURce CHANnel1
:WAVeform:FORMat ASCII
:WAVeform:DATA?                # read impedance vs time data
```

A difference of more than ±2 ohms from the golden reference warrants physical inspection of the trace segment at the indicated distance. Differential TDR (using both channels simultaneously on a differential pair) is essential for high-speed interfaces (PCIe, USB 3.x, DDR4/5) where common-mode and differential-mode impedance both matter.

### 12.3 Thermal imaging for active component identification

Infrared thermography reveals which components are actively drawing current and dissipating power during operation. A thermal camera (FLIR A700, InfraTec ImageIR 8300, or a lower-cost FLIR C5 for initial screening) images the board surface during normal operation, revealing the thermal signature of each component.

**Applications in hardware RE:**

- **Identifying unknown ICs.** An unmarked IC that runs hot during specific operations (e.g., network traffic, cryptographic computation) is likely the main processor or crypto accelerator, narrowing the identification search.
- **Detecting active hardware implants.** A covert component drawing power produces a thermal signature that was not present on the golden reference board. Even a small implant (2 mm × 2 mm) dissipating 50 mW produces a detectable thermal delta of 1–3°C above ambient on a typical PCB.
- **Power rail mapping.** Components sharing a voltage rail heat up together when that rail is loaded, revealing the power distribution network topology.
- **Fault localization.** A shorted component or solder bridge draws excess current and produces a localized hot spot visible in the thermal image.

**Lock-in thermography** improves sensitivity by modulating the stimulus (e.g., toggling a peripheral on/off at a known frequency) and correlating the thermal response at that frequency. This technique rejects DC thermal background and detects sub-milliwatt power dissipation changes, sufficient to identify quiescent-mode hardware Trojans that draw microampere-level currents.

### 12.4 Automated component recognition with ML and computer vision

Manual component identification (§2) is time-consuming on boards with hundreds of components. Machine-learning-based automated optical inspection (AOI) accelerates the process:

**Marking OCR.** Convolutional neural networks trained on IC package marking datasets read part numbers, date codes, and manufacturer logos from high-resolution board photographs. Open-source OCR pipelines (Tesseract with fine-tuning on component marking fonts, PaddleOCR for multi-orientation text) achieve >90% accuracy on clearly printed markings. The extracted text is automatically queried against component databases (Octopart API, DigiKey API, LCSC) to retrieve datasheets and pinout diagrams.

**Package classification.** A classifier trained on IC package silhouettes identifies the package type (QFP-48, BGA-256, TSSOP-20, etc.) from the board photograph, enabling automated BOM generation even when markings are unreadable.

**Anomaly detection for counterfeit screening.** A model trained on images of genuine components flags deviations — font inconsistencies, logo distortions, incorrect pin-1 markings, package dimension outliers — that indicate counterfeiting. This complements the manual counterfeit detection methods in §2.3.

```python
# Example: Automated IC marking extraction using PaddleOCR
from paddleocr import PaddleOCR
import requests

ocr = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=False)
result = ocr.ocr('/data/board_photos/ic_u5_crop.png', cls=True)

for line in result[0]:
    text = line[1][0]
    confidence = line[1][1]
    if confidence > 0.85:
        print(f"Detected marking: {text} (confidence: {confidence:.2f})")
        # Query Octopart for component identification
        resp = requests.get(
            "https://octopart.com/api/v4/rest/search",
            params={"q": text, "limit": 3},
            headers={"Authorization": f"Token {OCTOPART_API_KEY}"},
            timeout=10,
        )
        if resp.ok:
            for part in resp.json().get("results", []):
                print(f"  Match: {part['item']['mpn']} by {part['item']['manufacturer']['name']}")
```

### 12.5 Signal integrity analysis for covert channel detection

Covert channels on PCBs can exfiltrate data via modulated signals on legitimate buses — for example, a hardware implant that modulates the amplitude, timing, or spectral content of a clock signal to encode stolen data. Signal integrity (SI) analysis detects these anomalies:

**Jitter analysis.** A high-bandwidth oscilloscope (Keysight UXR, Tektronix DPO70000SX) measures the jitter on clock and data signals. A legitimate clock has characteristic jitter components (random jitter from thermal noise, periodic jitter from power supply coupling). A covert data channel introduces deterministic jitter components that correlate with exfiltrated data. Period jitter histograms, jitter spectral analysis (FFT of the time-interval-error sequence), and eye diagram analysis reveal non-random jitter components.

**Spectrum analysis.** An RF spectrum analyzer (or the FFT function of a high-bandwidth oscilloscope) captures the spectral content of signals on critical buses. Unexpected spectral lines — especially narrowband tones not explained by the legitimate signal protocol — indicate covert modulation. The covert signal may use amplitude modulation (AM), frequency modulation (FM), or spread-spectrum techniques to hide within the legitimate signal's spectral envelope.

**Power rail spectral analysis.** Covert channels can also use modulated current draw to exfiltrate data via the power rail. A current probe (Tektronix TCP0030A, 120 MHz bandwidth) on the power supply line, combined with spectral analysis, detects modulated current signatures.

### 12.6 PCB design file reverse engineering from physical board

When original design files (.brd, .kicad_pcb, Gerber RS-274X) are unavailable, the analyst reconstructs them from the physical board. The full workflow:

1. **Photography and CT scanning** (§1.1, §1.3, §12.1) to capture all layers.
2. **Image stitching** using Hugin, Microsoft ICE, or dedicated PCB stitching tools to create seamless composite images of each layer.
3. **Trace vectorization** using PCBFlow, OpenBoardView, or manual tracing in KiCad. Each copper trace is converted from a raster image to a vector polygon with accurate coordinates and widths.
4. **Netlist extraction.** Connected traces, vias, and component pads are grouped into nets. Each net is named (where possible from silkscreen labels or inferred function). The result is a netlist equivalent to what the original designer's EDA tool produced.
5. **Schematic capture.** From the netlist and component identification (§2), the analyst draws a schematic in KiCad or Altium. Components are placed and connected per the extracted netlist. The schematic is the analyst's primary working document for understanding circuit function.
6. **Simulation and verification.** Critical subcircuits (power supplies, clock generation, reset circuits) are simulated in SPICE to verify the analyst's understanding of the circuit topology.

```bash
# KiCad CLI: import a DXF trace extraction into a PCB file
kicad-cli pcb import-dxf \
    --input /data/vectorized/layer_top.dxf \
    --output /data/project/board.kicad_pcb \
    --layer F.Cu

# OpenBoardView for quick netlist inspection from a .brd file
openboardview /data/extracted/board.brd
```

---

## 13. Chip-level attack case studies

### 13.1 Microchip/Atmel secure microcontroller glitch attacks

Secure microcontrollers from Microchip (formerly Atmel) have been repeatedly broken via voltage and electromagnetic fault injection:

**STM32F1 RDP2 bypass (CVE-2020-27212).** The STM32F1 series implements Read-out Protection Level 2 (RDP2) as an "irreversible" lock — once set, JTAG/SWD debug access is permanently disabled and flash cannot be read externally. Researchers at Technische Universität Berlin demonstrated that a precisely timed voltage glitch (amplitude: −1.2 V to −1.8 V below nominal VDD, duration: 10–50 ns) during the option-byte loading sequence at boot causes the processor to misread the RDP2 fuse as RDP0 (no protection). The attack requires:

- ChipWhisperer-Pro or ChipWhisperer-Husky ($300–$650)
- Custom target board with decoupling capacitor removed from VDD
- Glitch parameter search: voltage offset [−1.0, −2.0 V], width [5, 80 ns], ext_offset [1000, 50000 clock cycles after reset]
- Success rate: approximately 1 in 10,000 to 1 in 100,000 attempts (minutes to hours of automated sweeping)

```python
# ChipWhisperer glitch parameter sweep for STM32 RDP bypass
import chipwhisperer as cw

scope = cw.scope()
target = cw.target(scope, cw.targets.SimpleSerial)
scope.clock.clkgen_freq = 8_000_000  # match target HSI

scope.glitch.clk_src = "clkgen"
scope.glitch.output = "enable_only"
scope.glitch.trigger_src = "ext_single"

for width in range(5, 80, 2):          # glitch width in clock cycles
    for offset in range(1000, 50000, 50):  # ext_offset after reset
        scope.glitch.width = width
        scope.glitch.ext_offset = offset
        scope.io.nrst = 'low'
        time.sleep(0.01)
        scope.arm()
        scope.io.nrst = 'high'
        ret = scope.capture()
        # Check if SWD responds (RDP bypassed)
        if check_swd_access(target):
            print(f"SUCCESS: width={width}, offset={offset}")
            dump_flash(target, "/data/stm32_dump.bin")
            break
```

**nRF52840 APPROTECT bypass (CVE-2020-17445).** The Nordic nRF52840's APPROTECT mechanism disables debug access by gating the SWD interface. LimitedResults disclosed that a voltage glitch during the narrow window when the APPROTECT register is read at boot re-enables SWD. The attack uses a ChipWhisperer-Lite ($250) or even a simple MOSFET crowbar circuit. Once debug is re-enabled, the attacker has full read/write access to all flash and RAM, including cryptographic keys and BLE bonding data.

### 13.2 Smart card chip attacks

Smart card ICs represent some of the most hardened commercial silicon, yet they are not immune to physical attacks:

**Differential power analysis on SIM cards.** Kocher's 1999 DPA technique, applied to SIM card authentication, recovers the Ki (subscriber authentication key) by analyzing power consumption during the COMP128 or Milenage algorithm execution. The attacker issues repeated authentication challenges via the SIM card reader and records the power trace for each. Statistical correlation between the power traces and hypothesized intermediate values of the algorithm reveals the key byte-by-byte. Modern SIM cards implement DPA countermeasures (random masking, shuffled execution order, constant-time operations), but older cards (pre-2010 COMP128v1) remain vulnerable. Equipment: a current sense resistor (10 ohm) in series with the SIM VCC line, a 200 MHz+ oscilloscope, and a programmable SIM card reader (e.g., SIM trace board or PC/SC reader with APDU-level control).

**EMV chip cloning attempts.** EMV chip cards use asymmetric cryptography (RSA or ECC) for transaction authentication, making bit-for-bit cloning infeasible without extracting the private key. However, implementation flaws have enabled attacks: the "pre-play" attack (documented by Anderson et al., Cambridge, 2014) exploits predictable unpredictable numbers (UN) in some terminal implementations to pre-compute authentication codes. The "PIN bypass" attack (CVE-2020-8758 in certain terminal firmware) manipulates the card-terminal communication to skip PIN verification. These are protocol-level attacks that do not require chip decapsulation but illustrate the interaction between chip security and protocol design.

### 13.3 Automotive ECU chip extraction and analysis workflow

Automotive electronic control units (ECUs) contain firmware that controls engine management, transmission, braking (ABS/ESC), airbag deployment, and advanced driver assistance systems (ADAS). Extracting and analyzing ECU firmware is relevant for security research, emissions compliance verification, and forensic investigation.

**Typical automotive ECU RE workflow:**

1. **Physical access.** Remove the ECU from the vehicle. Photograph the housing, connectors, and any tamper-evident seals. Open the housing (typically aluminum with Torx or specialized fasteners).
2. **Board-level analysis.** Identify the main processor (common: Infineon TriCore TC2xx/TC3xx, Renesas RH850, NXP MPC5xxx, STM32), flash memory (internal to MCU or external SPI/parallel NOR), and communication interfaces (CAN transceivers — NXP TJA1050/TJA1145, LIN transceivers, Ethernet PHYs on newer ECUs).
3. **Firmware extraction.** Attempt non-invasive extraction first: check for UDS (Unified Diagnostic Services) read-memory commands (Service 0x23) via OBD-II port. Many ECUs restrict this service, but some leave it open on development or early-production units. If UDS is locked, proceed to chip-level extraction: desolder the external flash and read it with a programmer (FlashcatUSB, TNM5000), or use debug interfaces (JTAG/SWD via Lauterbach TRACE32 or iSYSTEM tools — standard in automotive development).
4. **Firmware analysis.** Import the extracted binary into Ghidra with the appropriate processor module (TriCore, V850, PowerPC). Load the SVD file for the specific MCU to map peripheral registers. Identify the calibration data region, bootloader, application code, and diagnostic handlers.

```bash
# Automotive ECU flash dump via OpenOCD (TriCore example)
openocd -f interface/jlink.cfg \
        -f target/tricore_tc2xx.cfg \
        -c "init; halt; flash read_image /data/ecu_dump.bin 0x80000000 0x200000; shutdown"

# Import into Ghidra with TriCore support
ghidra_headless /data/ghidra_project ecu_analysis \
    -import /data/ecu_dump.bin \
    -processor "tricore:LE:32:default" \
    -scriptPath /data/scripts/ \
    -postScript SVDLoader.py /data/svd/TC277.svd
```

### 13.4 IoT SoC security fuse bypass techniques

Low-cost IoT system-on-chips (SoCs) implement security fuses (eFuses or OTP bits) that disable debug access and enable secure boot. These fuses are the primary security boundary on commodity IoT hardware:

**ESP32 Secure Boot v1 bypass (CVE-2019-15894).** The original ESP32 secure boot implementation (v1) verifies the bootloader signature using a hardware-accelerated RSA check. Researchers demonstrated a time-of-check-to-time-of-use (TOCTOU) fault injection attack: a precisely timed electromagnetic fault during the signature verification causes the verification result to be misread as "valid" even for unsigned code. The attack requires an EMFI probe (a small coil driven by a pulse generator, total cost ~$300) positioned over the die. Espressif addressed this in Secure Boot v2 (using the RSA-PSS scheme with hardware-enforced anti-rollback), but millions of devices running v1 remain deployed.

**nRF52 series APPROTECT bypass.** As detailed in §13.1 (CVE-2020-17445), the entire nRF52 family (nRF52810, nRF52832, nRF52833, nRF52840) shares the same APPROTECT vulnerability. Nordic Semiconductor issued an advisory (nRF52-anomaly-notice) and released silicon revisions (QIAA-Dx0 stepping for nRF52840) with a hardware fix. Detecting vulnerable vs. fixed silicon requires checking the chip's FICR.INFO.VARIANT register or die markings under magnification.

**MediaTek BROM Download Agent (CVE-2020-0069).** MediaTek MT67xx-series SoCs contain a Boot ROM (BROM) that enters Download Agent (DA) mode via USB. An authentication bypass in the BROM allows loading an unsigned DA, which has full read/write access to eMMC storage including all partitions. The tool `mtkclient` exploits this:

```bash
# Full eMMC dump via MediaTek BROM exploit
python mtk rl /data/mtk_dump/ --skip userdata
# Read specific partitions
python mtk r boot boot.img
python mtk r preloader preloader.bin
# Dump the hardware fuse configuration (EFUSE)
python mtk da efuse read
```

### 13.5 FPGA bitstream extraction and reverse engineering

Field-programmable gate arrays (FPGAs) store their configuration in a bitstream that defines the logic function. Extracting and reversing the bitstream reveals the implemented hardware design:

**Xilinx 7-series bitstream encryption bypass (Starbleed, 2020).** Researchers at Ruhr-Universität Bochum demonstrated that the Xilinx 7-series (Artix-7, Kintex-7, Virtex-7) bitstream encryption can be bypassed using a self-reconfiguration attack. The attack exploits the FPGA's internal configuration access port (ICAP) to read back the decrypted bitstream from within the FPGA itself. A malicious partial bitstream (loaded via the unencrypted JTAG interface) instantiates an ICAP reader that captures the decrypted configuration and exfiltrates it via JTAG. This defeats AES-256 encryption of the bitstream without recovering the key. Xilinx addressed this in UltraScale+ with authenticated encryption (AES-GCM), but 7-series devices remain vulnerable if they use encryption-only (without HMAC authentication).

**Lattice iCE40 bitstream documentation.** The Lattice iCE40 family's bitstream format has been fully documented by the open-source Project IceStorm. This enables complete reverse engineering of any iCE40 design from its bitstream:

```bash
# Lattice iCE40 bitstream reverse engineering with Project IceStorm
# Dump bitstream from the FPGA's SPI configuration flash
flashrom -p ft2232_spi:type=232H -r bitstream.bin

# Convert binary bitstream to ASCII representation
iceunpack bitstream.bin > bitstream.asc

# Convert to Verilog netlist for analysis
icebox_vlog bitstream.asc > design.v

# Visualize the placement and routing
icebox_explain bitstream.asc
```

**Microsemi/Microchip SmartFusion2 and PolarFire** FPGAs implement more robust bitstream protection (AES-256 with HMAC, PUF-derived keys, and DPA-resistant implementations). Attacking these requires Tier 3+ capabilities (die-level FIB access to extract PUF helper data or key storage).

### 13.6 Real-world hardware implant detection case studies

**Bloomberg "Big Hack" allegations (2018).** Bloomberg Businessweek reported that tiny chips (the size of a pencil tip) were allegedly implanted on Supermicro server motherboards during manufacturing in China, targeting Apple and Amazon data centers. Both companies, Supermicro, and government agencies publicly denied finding evidence. The technical plausibility analysis: a chip small enough to escape visual inspection could be embedded in the PCB substrate or disguised as a passive component (capacitor or resistor). Such an implant would need to intercept the BMC (baseboard management controller) SPI flash bus to modify BMC firmware, enabling network-level exfiltration. Detection methods applicable to this scenario: X-ray CT comparison against golden reference (§12.1), TDR impedance profiling of SPI bus traces (§12.2), BOM verification of all components against design files (§14.4).

**NSA ANT catalog hardware implants (disclosed 2013).** Leaked NSA documents described hardware implants including COTTONMOUTH (USB implant in a modified connector housing), FIREWALK (Ethernet implant in a modified RJ45 jack), and IRONCHEF (BIOS-level persistence via compromised I/O controller). These implants were designed for targeted access operations. Detection relies on: physical inspection of connectors and components against known-good references, X-ray imaging to detect additional silicon inside modified connector housings, and firmware integrity verification of I/O controllers and BMCs.

**Supply chain interdiction countermeasures.** Organizations concerned about hardware implants implement:
- Randomized procurement (ordering identical boards from different suppliers/batches)
- Incoming inspection with X-ray and electrical testing against golden reference
- Tamper-evident packaging with chain-of-custody tracking from fab to deployment
- Runtime monitoring (power consumption baselines, network traffic analysis for unexpected egress)

---

## 14. PCB/chip detection engineering

### 14.1 Sigma rules for hardware supply chain anomalies

Sigma rules express detection logic for SIEM and log-analysis platforms. In hardware supply chain monitoring, the relevant log sources are firmware update systems, asset management databases, and hardware inventory scanners:

```yaml
title: Firmware Hash Mismatch on Production Hardware
id: hw-supply-001
status: experimental
description: >
  Detects when a firmware image extracted from production hardware does not
  match the approved firmware hash in the asset management database. This may
  indicate supply chain tampering, unauthorized firmware modification, or
  counterfeit components with non-genuine firmware.
author: Hardware Security Team
date: 2025-06-15
references:
  - https://csrc.nist.gov/publications/detail/sp/800-193/final
logsource:
  category: firmware_verification
  product: asset_management
detection:
  selection:
    EventType: "firmware_hash_check"
    Result: "MISMATCH"
  condition: selection
falsepositives:
  - Legitimate firmware update not yet reflected in asset database
  - Firmware extraction error (bit flip, incomplete read)
level: high
tags:
  - attack.supply_chain
  - attack.t1195.003
```

```yaml
title: Unexpected Debug Interface Detected on Production Device
id: hw-supply-002
status: experimental
description: >
  Detects when a production device responds to JTAG, SWD, or UART probe
  during incoming hardware inspection, indicating debug interfaces were not
  disabled as required by the security specification.
author: Hardware Security Team
date: 2025-06-15
logsource:
  category: hardware_inspection
  product: incoming_inspection_system
detection:
  selection:
    EventType: "debug_interface_probe"
    InterfaceType|contains:
      - "JTAG"
      - "SWD"
      - "UART"
    Response: "ACTIVE"
  filter_expected:
    DeviceCategory: "development_unit"
  condition: selection and not filter_expected
falsepositives:
  - Development or engineering sample incorrectly tagged as production
level: high
tags:
  - attack.initial_access
  - attack.t1200
```

```yaml
title: Hardware BOM Component Substitution Detected
id: hw-supply-003
status: experimental
description: >
  Detects when automated optical inspection (AOI) or manual inspection
  identifies a component on a production board that does not match the
  approved bill of materials. May indicate counterfeit component substitution
  or unauthorized design change.
author: Hardware Security Team
date: 2025-06-15
logsource:
  category: hardware_inspection
  product: aoi_system
detection:
  selection:
    EventType: "component_verification"
    Result: "MISMATCH"
    Severity|gte: "WARNING"
  condition: selection
falsepositives:
  - Approved component substitution not yet updated in BOM
  - OCR misread of component marking
level: medium
tags:
  - attack.supply_chain
  - attack.t1195.003
```

### 14.2 YARA rules for extracted firmware analysis

After extracting firmware from flash memory (§5), YARA rules scan the binary for indicators of compromise — backdoors, hardcoded credentials, embedded shells, and trojanized libraries:

```yara
rule Hardcoded_Credentials_in_Firmware
{
    meta:
        description = "Detects common hardcoded credential patterns in extracted firmware images"
        author = "Hardware Security Team"
        date = "2025-06-15"
        severity = "HIGH"
        reference = "CWE-798"

    strings:
        $passwd1 = "password=" ascii nocase
        $passwd2 = "passwd=" ascii nocase
        $passwd3 = "default_password" ascii nocase
        $root1 = "root:$1$" ascii                  // MD5 shadow hash
        $root2 = "root:$5$" ascii                  // SHA-256 shadow hash
        $root3 = "root:$6$" ascii                  // SHA-512 shadow hash
        $root4 = "root::0:0:" ascii                // empty password in passwd
        $apikey1 = /[Aa][Pp][Ii]_?[Kk][Ee][Yy]\s*[:=]\s*["'][A-Za-z0-9]{16,}["']/
        $aws_key = "AKIA" ascii                    // AWS access key prefix
        $private_key = "-----BEGIN RSA PRIVATE KEY-----" ascii
        $private_key2 = "-----BEGIN EC PRIVATE KEY-----" ascii

    condition:
        any of them
}

rule Embedded_Shell_Backdoor
{
    meta:
        description = "Detects patterns indicating an embedded reverse shell or backdoor in firmware"
        author = "Hardware Security Team"
        date = "2025-06-15"
        severity = "CRITICAL"
        reference = "CWE-912"

    strings:
        $busybox_shell = "/bin/sh -c" ascii
        $nc_reverse = { 6E 63 20 2D [1-20] 20 2D 65 20 2F 62 69 6E 2F 73 68 }  // nc ... -e /bin/sh
        $telnetd_noauth = "telnetd -l /bin/sh" ascii
        $dropbear_noauth = "dropbear -B" ascii      // allow blank passwords
        $bind_shell = "socket" ascii
        $dup2_pattern = { 6D 6F 76 ?? ?? 01 }       // dup2 syscall patterns (MIPS)
        $wget_pipe = "wget -q -O - " ascii           // fetch-and-execute pattern
        $curl_pipe = "curl -s " ascii
        $bash_tcp = "/dev/tcp/" ascii                // bash reverse shell

    condition:
        2 of them and filesize < 64MB
}

rule Suspicious_Firmware_Packing
{
    meta:
        description = "Detects firmware images with unusual packing or obfuscation layers"
        author = "Hardware Security Team"
        date = "2025-06-15"
        severity = "MEDIUM"

    strings:
        $upx_magic = "UPX!" ascii
        $lzma_header = { 5D 00 00 }
        $xor_loop_arm = { 00 00 50 E3 [2-8] 20 00 1A }   // ARM XOR decryption loop
        $xor_loop_mips = { 00 00 00 00 [2-8] 26 }          // MIPS XOR pattern
        $rc4_sbox = { 00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F }
        $custom_header = { 48 44 52 30 }                    // "HDR0" non-standard header

    condition:
        2 of them and filesize < 32MB
}

rule Debug_Access_Left_Enabled
{
    meta:
        description = "Detects debug and diagnostic services left enabled in production firmware"
        author = "Hardware Security Team"
        date = "2025-06-15"
        severity = "HIGH"
        reference = "CWE-489"

    strings:
        $gdb_stub = "GDB stub" ascii nocase
        $gdbserver = "gdbserver" ascii
        $strace = "strace" ascii
        $debug_enable = "DEBUG_ENABLED=1" ascii
        $uart_shell = "console=ttyS0" ascii            // kernel console on UART
        $ssh_root = "PermitRootLogin yes" ascii
        $telnet_enable = "CONFIG_TELNETD=y" ascii
        $jtag_enable = "JTAG_ENABLE" ascii

    condition:
        2 of them
}
```

```bash
# Scanning extracted firmware with YARA
yara -r /data/yara_rules/firmware_backdoors.yar /data/extracted_firmware/
# Combine with binwalk for filesystem extraction + YARA scan
binwalk -e /data/firmware.bin -C /data/extracted/
yara -r /data/yara_rules/firmware_backdoors.yar /data/extracted/
```

### 14.3 Automated PCB inspection workflows (AOI integration)

Automated optical inspection (AOI) systems (Koh Young Zenith, Mirtec MV-6 OMNI, Nordson YESTECH FX-942) scan every component placement against the golden reference design files. For hardware security, AOI integration extends beyond manufacturing quality control to supply chain integrity verification:

**Incoming inspection workflow:**

1. Receive boards from supplier. Log batch number, supplier, date, chain-of-custody documentation.
2. Select sample boards per AQL (Acceptable Quality Level) sampling plan — or 100% inspection for high-security applications.
3. Run AOI scan: compare each component placement, marking, and orientation against the approved BOM and placement file.
4. Flag discrepancies: missing components, extra components (potential implants), wrong component values, component substitutions, marking anomalies.
5. Escalate flagged boards to manual inspection with microscope and X-ray.
6. Record all findings in the asset management system for traceability.

### 14.4 Hardware bill of materials (HBOM) verification automation

An HBOM enumerates every component on the board with manufacturer part number, quantity, reference designator, and approved alternates. Automated HBOM verification:

```bash
# Generate HBOM from KiCad design files
kicad-cli sch export bom \
    --input /data/design/board.kicad_sch \
    --output /data/hbom/design_bom.csv \
    --fields "Reference,Value,Footprint,MPN,Manufacturer"

# Compare design BOM against physical board BOM (from AOI or manual inspection)
diff <(sort /data/hbom/design_bom.csv) <(sort /data/hbom/inspected_bom.csv) \
    | grep "^[<>]" > /data/hbom/discrepancies.txt

# Verify component authenticity via GIDEP/ERAI database queries
python3 /tools/verify_components.py \
    --bom /data/hbom/inspected_bom.csv \
    --check-gidep --check-erai \
    --output /data/hbom/verification_report.json
```

The HBOM verification process catches:
- Counterfeit component substitution (wrong manufacturer for a given MPN)
- Unauthorized alternates (component not on the approved alternates list)
- Date code anomalies (components older than expected, suggesting recycled parts)
- Lot code inconsistencies (components from different lots mixed in a single batch, suggesting a broker aggregated from multiple sources)

### 14.5 Supply chain provenance tracking for critical components

For high-assurance hardware (defense, critical infrastructure, aerospace), component provenance tracking requires:

**Unique device identity.** Each critical IC is tracked by its unique identifier — either a manufacturer-programmed serial number (e.g., STM32 96-bit unique ID at address 0x1FFF7A10) or a physically unclonable function (PUF) response that serves as a device fingerprint. The identifier is recorded at each supply chain handoff.

**Blockchain-based or cryptographically signed manifests.** Each supply chain participant (foundry, OSAT, distributor, integrator) signs a manifest attesting to the components they received and shipped. The chain of signed manifests provides provenance from wafer fab to final assembly. Standards: NIST SP 800-193 (Platform Firmware Resiliency Guidelines) and the emerging SAE J3061 (Cybersecurity Guidebook for Cyber-Physical Vehicle Systems) address aspects of hardware provenance.

**Tamper-evident packaging.** Physical tamper-evident seals (holographic labels, serialized tape-and-reel seals, epoxy-sealed connector housings) provide visual indication of unauthorized access during transit. These are supplemented by environmental sensors (temperature, humidity, shock) in the shipping container that log conditions and flag excursions.

### 14.6 Anti-tamper monitoring systems and alerting

Runtime tamper monitoring provides continuous assurance that deployed hardware has not been physically modified:

**Mesh shield monitoring.** A PCB-level mesh of thin traces (typically on an inner layer) forms a continuous circuit. Any attempt to drill, cut, or probe through the mesh breaks the circuit or creates a short, triggering an alert. The mesh is monitored by a dedicated security controller that erases key material upon tamper detection. Implementations: Maxim Integrated (now Analog Devices) DS36xx secure supervisors, NXP SE050/SE051 secure elements with tamper mesh support.

**Environmental monitoring.** Temperature, voltage, and clock frequency sensors detect fault-injection preparation: abnormal temperatures (decapsulation chemicals, laser attacks), voltage glitches (§13.1), and clock manipulation. The Arm TrustZone CryptoCell and some secure microcontrollers (Infineon OPTIGA Trust, Microchip ATECC608) implement environmental monitoring in hardware.

**Power consumption baselines.** The device's power consumption during normal operation is baselined. Significant deviations (especially correlated with network activity) indicate potential hardware implant activity. Monitoring is performed at the system level (smart PDU with per-port power measurement) or board level (INA226 current/power monitor on each rail, read via I²C by the BMC or system management controller).

---

## 15. Hardware RE lab setup and methodology

### 15.1 Lab equipment inventory

A hardware reverse engineering lab requires equipment across several categories:

**Observation and measurement.**

| Equipment | Specification | Typical Cost | Use Case |
|-----------|--------------|-------------|----------|
| Stereo microscope | 7×–45× zoom, LED ring light | $800–$3,000 | Visual inspection, soldering, marking identification |
| Digital microscope | 200×–2000×, HDMI/USB output | $300–$1,500 | Die photography, trace inspection, documentation |
| Metallurgical microscope | 50×–1000×, brightfield/darkfield/DIC | $5,000–$50,000 | Die-level imaging after decapsulation |
| Oscilloscope | 4-ch, 200 MHz–1 GHz, 2.5–10 GS/s | $1,500–$30,000 | Signal analysis, glitch characterization, protocol decode |
| Logic analyzer | 16–32 ch, 200 MHz–500 MHz | $400–$5,000 | Protocol analysis (SPI, I²C, UART, JTAG) |
| Multimeter | 6.5-digit bench DMM | $200–$2,000 | Continuity testing, voltage measurement |
| Spectrum analyzer | 9 kHz–3 GHz (or higher) | $3,000–$30,000 | RF analysis, covert channel detection |
| Thermal camera | 320×240 resolution, <50 mK NETD | $500–$15,000 | Active component identification (§12.3) |

**Soldering and rework.**

| Equipment | Specification | Typical Cost |
|-----------|--------------|-------------|
| Hot-air rework station | Digital, 100–500°C, precision nozzles | $200–$2,000 |
| Soldering station | Temperature-controlled, fine tip (0.2 mm+) | $100–$500 |
| Preheater | IR or hot-plate, for BGA rework | $200–$1,500 |
| BGA reballing station | Stencils + solder paste/balls | $50–$300 |
| Solder paste stencil | Custom for specific BGA footprints | $10–$50 per stencil |

**Flash memory readers and programmers.**

| Equipment | Specification | Typical Cost |
|-----------|--------------|-------------|
| FlashcatUSB XPORT | SPI, I²C, JTAG, parallel NOR/NAND | $30–$100 |
| TNM5000 / T56 Universal | DIP, SOIC, TSOP, BGA adapters | $200–$600 |
| Easy JTAG / Medusa Pro | eMMC, UFS, ISP, forensic-grade | $300–$800 |
| Segger J-Link | JTAG/SWD debug probe (ARM, RISC-V) | $60–$1,000 |
| FTDI FT2232H breakout | USB-to-SPI/I²C/JTAG/UART, 30 MHz | $15–$30 |

**Fault injection equipment.**

| Equipment | Specification | Typical Cost |
|-----------|--------------|-------------|
| ChipWhisperer-Husky | Voltage glitch, clock glitch, power analysis | $650 |
| ChipWhisperer-Lite | Basic voltage glitching and power analysis | $250 |
| NewAE EMFI probe | Electromagnetic fault injection coil | $200–$500 |
| PicoEMP | Open-source EM pulse injector | $50 (DIY) |
| Riscure FI Inspector | Professional-grade fault injection platform | $50,000+ |

### 15.2 Software toolchain

**PCB and schematic analysis:**

| Tool | Purpose | License/Cost |
|------|---------|-------------|
| KiCad | Schematic capture, PCB layout, Gerber viewer | FOSS (GPLv3) |
| Altium Designer Viewer | Read-only viewing of Altium .PcbDoc/.SchDoc | Free viewer |
| OpenBoardView | Board view file viewer (.brd, .bvr, .fz) | FOSS |
| PCBFlow | Automated PCB image vectorization | Research tool |
| Boardview (various) | Interactive board visualization with netlist | varies |

**Firmware analysis:**

| Tool | Purpose | License/Cost |
|------|---------|-------------|
| Ghidra | Disassembly, decompilation, scripting (Java/Python) | FOSS (Apache 2.0) |
| Ghidra + SVD Loader | Peripheral register mapping from SVD files | FOSS plugin |
| Binary Ninja | Disassembly, IL-based analysis, API | Commercial ($300+) |
| Radare2/Rizin | CLI disassembler, hex editor, debugger | FOSS |
| binwalk | Firmware filesystem extraction, signature scan | FOSS (MIT) |
| ubi_reader | UBI/UBIFS filesystem extraction (NAND) | FOSS |
| jefferson | JFFS2 filesystem extraction | FOSS |

**Debug and flash tools:**

| Tool | Purpose | License/Cost |
|------|---------|-------------|
| OpenOCD | JTAG/SWD debug, flash programming (ARM, RISC-V, MIPS) | FOSS |
| pyOCD | Python-based ARM Cortex debug (CMSIS-DAP) | FOSS |
| flashrom | SPI/parallel flash read/write (in-system) | FOSS |
| mtkclient | MediaTek BROM exploit tool | FOSS |
| esptool.py | ESP32/ESP8266 flash read/write | FOSS (GPLv2) |
| Lauterbach TRACE32 | Professional multi-architecture debugger | Commercial ($10,000+) |

**Side-channel and fault injection:**

| Tool | Purpose | License/Cost |
|------|---------|-------------|
| ChipWhisperer Jupyter | Glitch parameter sweeping, power analysis | FOSS |
| SCA Toolbox (Riscure) | Professional DPA/CPA analysis | Commercial |
| Lascar | Lightweight side-channel analysis framework (Python) | FOSS |
| Daredevil | CPA attack tool optimized for large traces | FOSS |
| Jlsca | Julia-based side-channel analysis | FOSS |

### 15.3 Chip decapsulation safety procedures

Chemical decapsulation involves hazardous materials that require strict safety protocols:

**Chemical hazards and PPE requirements:**

| Chemical | Hazard | Required PPE | Ventilation |
|----------|--------|-------------|-------------|
| Fuming nitric acid (98% HNO₃) | Severe oxidizer, toxic fumes (NOx), corrosive | Acid-resistant apron, face shield, nitrile+neoprene double gloves, closed-toe shoes | Fume hood with acid-rated exhaust (minimum 100 fpm face velocity) |
| Sulfuric acid + H₂O₂ (piranha etch) | Extreme oxidizer, exothermic, explosive with organics | Same as above + blast shield | Fume hood; never mix in sealed container |
| Acetone | Flammable, vapor heavier than air | Nitrile gloves, safety glasses | Fume hood or well-ventilated area; no open flames |
| Red fuming nitric acid (RFNA) | All hazards of fuming HNO₃ plus NO₂ gas (highly toxic) | Full-face respirator (if outside fume hood), acid suit | Fume hood mandatory; SCBA available for spill response |

**Procedure checklist:**

1. Verify fume hood airflow (smoke test or anemometer reading ≥100 fpm).
2. Prepare neutralization materials: sodium bicarbonate (NaHCO₃) for acid spills, spill containment trays.
3. Ensure emergency eyewash station and safety shower are within 10 seconds of travel.
4. Place the IC in a PTFE (Teflon) or borosilicate glass dish — never metal or standard plastic.
5. Apply acid dropwise using a borosilicate pipette. Monitor reaction (bubbling, color change).
6. Rinse with deionized water between acid applications. Collect rinse water as chemical waste.
7. After decapsulation, neutralize all acid waste with NaHCO₃ and dispose per local hazardous waste regulations.
8. Document the entire process with photographs (before, during, after each acid application).

### 15.4 Evidence preservation for hardware forensics

Hardware forensics requires the same chain-of-custody rigor as digital forensics, with additional physical evidence considerations:

**Chain of custody documentation:**

- Photograph the device as received (all sides, labels, seals, condition) with a calibrated ruler for scale.
- Record: date/time (UTC ISO 8601), location, examiner name, case number, device serial number, and condition notes.
- Assign a unique evidence identifier. Label the physical device and all derived artifacts (extracted firmware images, photographs, decapsulated dies) with this identifier.
- Log every action performed on the device: disassembly, probing, firmware extraction, decapsulation. Each log entry includes timestamp, action, tool used, result, and examiner initials.

**Photography standards:**

- Use a calibrated macro lens with a color calibration chart (X-Rite ColorChecker) in the first frame of each session.
- RAW format for archival; processed JPEG/TIFF for working copies.
- Include a scale reference (ruler or calibration target) in every photograph.
- Photograph: overall device, board top/bottom, each IC marking (macro), each connector, any anomalies or damage, and each stage of disassembly/decapsulation.
- EXIF metadata provides timestamps; additionally log timestamps in the chain-of-custody document.

**Hash verification of extracted data:**

```bash
# Hash the extracted firmware image immediately after extraction
sha256sum /data/extracted/firmware.bin > /data/evidence/firmware.sha256
# Sign the hash with the examiner's GPG key
gpg --armor --detach-sign /data/evidence/firmware.sha256
# Verify before analysis
sha256sum -c /data/evidence/firmware.sha256
gpg --verify /data/evidence/firmware.sha256.asc
```

### 15.5 Cost-effective lab setup tiers

**Tier 1 — Entry level ($500)**

Suitable for firmware extraction from IoT devices with accessible debug ports and SPI/I²C flash memory.

| Item | Cost |
|------|------|
| FTDI FT2232H breakout board | $15 |
| Segger J-Link EDU Mini (SWD/JTAG) | $20 |
| Bus Pirate or Glasgow Interface Explorer | $30–$50 |
| FlashcatUSB XPORT (SPI/parallel flash) | $30 |
| USB logic analyzer (Saleae clone, 24 MHz) | $15 |
| Soldering station (Pinecil or Hakko FX-888D clone) | $30–$80 |
| Hot-air rework station (858D) | $40 |
| Digital microscope (USB, 50×–200×) | $30 |
| Multimeter (Uni-T UT61E or equivalent) | $40 |
| Breadboard, jumper wires, test clips, adapters | $50 |
| Software (Ghidra, OpenOCD, binwalk, flashrom, KiCad) | $0 (FOSS) |
| **Total** | **~$300–$400** |

**Tier 2 — Intermediate ($5,000)**

Adds fault injection capability, proper microscopy, and higher-bandwidth measurement.

| Item | Incremental Cost (above Tier 1) |
|------|------|
| ChipWhisperer-Husky (glitching + power analysis) | $650 |
| Oscilloscope (Rigol DS1104Z+, 100 MHz, 4-ch) | $400 |
| Saleae Logic Pro 16 (500 MS/s, 16-ch) | $1,500 |
| Stereo microscope (AmScope SM-4TZ-144A, 7×–45×) | $300 |
| EasyJTAG Plus (eMMC/UFS forensic reader) | $400 |
| PicoEMP (open-source EM fault injection) | $50 |
| Lauterbach TRACE32 PowerDebug USB 3 (used) | $800–$1,500 |
| Consumables (BGA stencils, solder paste, flux, PCB holder) | $200 |
| **Total (incremental)** | **~$4,300–$5,000** |

**Tier 3 — Professional ($50,000)**

Adds die-level analysis capability, professional fault injection, and advanced imaging.

| Item | Incremental Cost (above Tier 2) |
|------|------|
| Metallurgical microscope (Olympus BX53M or equivalent) | $10,000 |
| SEM access (university partnership or service bureau retainer) | $5,000/year |
| Riscure FI Inspector (professional fault injection) | $15,000 |
| Benchtop X-ray system (used Nordson DAGE or equivalent) | $10,000–$20,000 |
| Chemical decapsulation setup (fume hood, chemicals, PPE, waste disposal) | $3,000 |
| High-bandwidth oscilloscope (Keysight MSOX4104A, 1 GHz) | $8,000 |
| Thermal camera (FLIR E96, 640×480, ±2°C accuracy) | $5,000 |
| **Total (incremental)** | **~$46,000–$56,000** |

### 15.6 Training resources and certification paths

**Hands-on training courses:**

| Course/Provider | Focus | Duration | Cost |
|----------------|-------|----------|------|
| Joe Grand (GrandIdea Studio) — Hardware Hacking | PCB RE, debug interfaces, firmware extraction | 2–4 days | $2,000–$4,000 |
| Riscure Hardware Security Training | Side-channel, fault injection, secure element attacks | 3–5 days | $3,000–$6,000 |
| Colin O'Flynn — ChipWhisperer workshops | Hands-on power analysis and glitching | 1–2 days | $500–$1,500 |
| Hardwear.io training | Various hardware security topics | 1–3 days | $1,500–$3,500 |
| Offensive Security AWE (replaces AWAE for hardware) | Exploit dev with hardware component | 3 days | $2,000 |

**Self-study resources:**

- *The Hardware Hacking Handbook* (Jasper van Woudenberg, Colin O'Flynn) — comprehensive practical guide covering power analysis, fault injection, and embedded security.
- *Practical IoT Hacking* (Fotios Chantzis et al.) — IoT-focused hardware and firmware attack methodologies.
- ChipWhisperer tutorials (https://chipwhisperer.readthedocs.io/) — free, hands-on Jupyter notebooks for power analysis and glitching.
- wrongbaud.github.io — detailed blog posts on embedded device reverse engineering with JTAG, SPI, and firmware analysis.
- LiveOverflow hardware hacking YouTube series — accessible video walkthroughs of hardware attack techniques.
- Microcorruption CTF (microcorruption.com) — embedded security CTF focused on MSP430 exploitation.

**Relevant certifications:**

| Certification | Issuer | Focus |
|--------------|--------|-------|
| GIAC GPEN (Penetration Tester) | SANS | Includes hardware/IoT attack vectors |
| OSCP (Offensive Security Certified Professional) | OffSec | General offensive security (limited hardware) |
| Certified Hardware Security Professional (CHSP) — emerging | Various | Dedicated hardware security (program developing) |
| CompTIA PenTest+ | CompTIA | Includes IoT/embedded device testing |

The hardware security field lacks a single definitive certification equivalent to OSCP for software. Demonstrable skills (CTF results, published research, conference talks at Hardwear.io/REcon/Black Hat) carry more weight than certifications in this specialty.

---

## 16. Cross-references

**To Domain 17A (side-channel analysis).** Die-level analysis (§4) provides the spatial context for EM side-channel attacks: knowing the die layout allows the analyst to position near-field EM probes (Chapter 17A §1.2) directly above the cryptographic engine, maximizing signal quality. Photon emission analysis (§5.3 of Chapter 17B, referenced here) provides temporal context for fault injection targeting. Hardware Trojan detection via side-channel fingerprinting (§7.2) uses the same power and EM measurement infrastructure as DPA/CPA (Chapter 17A §1.1).

**To Domain 17B (fault injection).** Chip decapsulation (§3) is a prerequisite for laser FI (Chapter 17B §4) and body biasing injection (Chapter 17B §6). eFuse and OTP analysis (§5.3) determines which security fuses are programmed, informing the analyst about which fault-injection targets are available (e.g., whether the debug-disable fuse is set, making fault-injection bypass of the debug lock necessary). FIB circuit edit (§4.3) can rewire security-critical circuits to bypass protections without fault injection.

**To Domain 12 (reverse engineering).** Memory extraction (§5) feeds directly into firmware reverse engineering (Chapter 12B §3). The extracted firmware image (from NAND, NOR, eMMC, or UFS) is the input to the static and dynamic analysis workflows described in Chapter 12. JTAG and SWD access (covered in depth in Chapter 17D) provides the debug interface for dynamic firmware analysis (single-stepping, breakpoints, memory inspection) described in Chapter 12B §2.2.

**To Domain 7B (hardware vulnerabilities).** Hardware Trojans (§7) represent a hardware-level supply chain attack. The detection methodologies (golden reference comparison, side-channel fingerprinting, formal verification) are the hardware counterpart of the software supply chain integrity measures described in Domain 19.

**To Domain 19 (supply chain security).** Counterfeit IC detection (§2.3) is the hardware component of supply chain security. The SAE AS6171/AS6081 standards for counterfeit detection complement the software-focused SLSA and SBOM frameworks described in Domain 19. Hardware supply chain attacks (chip-level Trojans, counterfeit components) represent a different attack vector than software supply chain attacks (dependency confusion, build-process compromise) but target the same organizational trust boundary.

**To Domain 28 (IoT).** IoT device security (Chapter 28B) depends on the physical-layer protections described here. IoT devices with accessible UART, JTAG/SWD, and desoldering-friendly flash memory are the primary targets for the hardware RE techniques in this chapter. The economics of IoT (high volume, low per-unit cost, minimal physical security budget) create a target-rich environment for hardware attacks.

**To Domain 17D (debug interfaces and secure boot bypass).** This chapter (17C) covers the PCB-level and chip-level analysis that precedes debug exploitation. The memory extraction scripts (§5.8) produce firmware images that are the input to the analysis workflows in Chapter 12 and the secure-boot bypass techniques in Chapter 17D. The YARA rules in §10.1 target generic firmware anomalies (hardcoded credentials, embedded servers, packed binaries) and are complementary to the UEFI-specific and secure-boot-specific YARA rules in Chapter 17D §7.7. For OpenOCD/pyOCD debug exploitation commands, ARM CoreSight debug authentication bypass, and specific secure-boot bypass PoC walkthroughs (checkm8, BootHole, BlackLotus), refer to Chapter 17D. The boundary-scan usage of OpenOCD in §1.8 of this chapter addresses only PCB-level pin mapping (SAMPLE/PRELOAD, EXTEST) and does not overlap with the debug-access exploitation covered in 17D.

---

## 17. Exercises

**Exercise 17.3-1 — SPI NOR flash extraction and firmware triage.**
Using a CH341A programmer (with 3.3V level-shifting adapter) or Raspberry Pi SPI bus: (a) Identify a target device with an SPI NOR flash chip (consumer router, IP camera, or IoT device). Locate the SPI flash on the PCB — identify the chip marking, look up the datasheet, and confirm the pinout (VCC, GND, CS, CLK, MOSI, MISO). (b) Connect the programmer to the flash chip in-system (with the SoC held in reset via the RESET pin or with power removed from the SoC). Read the full chip using flashrom: `flashrom -p ch341a_spi -r firmware.bin`. Verify the dump by reading twice and comparing SHA-256 hashes. (c) Analyze the extracted image with binwalk: run signature scan (`binwalk firmware.bin`), entropy analysis (`binwalk -E firmware.bin`), and recursive extraction (`binwalk -eM firmware.bin`). Identify the filesystem type, kernel image, and any configuration files. (d) Search the extracted filesystem for hardcoded credentials (`grep -r "password\|passwd\|secret" .`), SSH keys, and TLS certificates. Deliverable: flashrom output log, binwalk analysis report, entropy graph, extracted filesystem listing, and a findings table of any discovered credentials or keys.

**Exercise 17.3-2 — PCB layer identification and signal tracing.**
Select a 4+ layer PCB from a consumer electronic device: (a) Photograph the top and bottom surfaces at sufficient resolution to read all component markings. Identify and label all ICs (processor, flash, DRAM, power management, RF, etc.) with their part numbers. (b) Count the PCB layers using edge cross-section inspection (cut a small corner with a jeweler's saw, inspect under a stereo microscope at 20x). Document the layer stackup. (c) Identify all visible test points and unpopulated footprints. Using a multimeter in continuity mode, trace at least 5 test points back to their connected IC pins. Identify their probable function (UART TX/RX, JTAG TCK/TMS/TDI/TDO, SWD SWCLK/SWDIO, RESET, GND) based on the IC's datasheet pinout. (d) Capture bus traffic on any identified UART with a logic analyzer (Saleae or compatible) using sigrok/PulseView: determine the baud rate, decode the output, and document any boot messages. Deliverable: annotated board photographs, layer-count cross-section image, test-point mapping table, and decoded UART boot log.

**Exercise 17.3-3 — Chip decapsulation and die-level inspection.**
Using a sacrificial IC (commodity microcontroller in a DIP or QFP package — NOT a production device): (a) Perform chemical decapsulation using fuming nitric acid (98% HNO3) in a fume hood with full PPE (acid-resistant gloves, face shield, chemical apron). Heat the acid to 80°C, immerse the IC for 15–30 minutes until the die is exposed. Rinse in acetone → IPA → DI water → dry under N2. (b) Inspect the exposed die under a stereo microscope (10x–40x). Photograph the full die at low magnification. Identify the major functional blocks visible on the top metal layer (SRAM arrays — regular rectangular patterns; logic — irregular dense patterns; I/O pads — large square pads at the die periphery; analog blocks — distinctive large-transistor patterns). (c) If a metallurgical microscope is available (100x): image individual I/O pad structures and attempt to identify the bond pad metal (gold wire bonds on aluminum pads). (d) Document the die dimensions, bond wire count, and identified functional blocks with annotated die photographs. Deliverable: pre-decapsulation and post-decapsulation photographs, die micrographs, functional block map, and a safety protocol document for the acid handling procedures used.

**Exercise 17.3-4 — Counterfeit IC detection screening.**
Obtain two samples of the same IC: one from an authorized distributor (genuine) and one from an unverified source (potentially counterfeit or recycled): (a) Perform external visual inspection under a stereomicroscope (20x): compare marking quality, font consistency, lead/ball finish condition, and date-code plausibility. Document with side-by-side photographs. (b) Perform UV inspection (365 nm UV lamp): compare fluorescence uniformity. Document any patches of different fluorescence on the suspect part. (c) Perform the acetone swab test: rub a cotton swab dipped in acetone across the package marking for 30 seconds. Compare marking resistance between genuine and suspect. (d) If X-ray equipment is available: compare the internal structures (die size, wire bond count, die-attach quality). If not available: perform electrical parametric testing using a curve tracer or bench supply — measure supply current (IDD) at nominal voltage and compare against the datasheet specification. (e) Write a pass/fail determination following the SAE AS6171 escalation criteria. Deliverable: side-by-side comparison photographs (visual, UV, acetone), parametric test data, and the AS6171-format inspection report.

**Exercise 17.3-5 — eMMC in-system firmware extraction.**
Using a target device with an eMMC flash chip (e.g., a smartphone, set-top box, or automotive infotainment unit): (a) Identify the eMMC chip on the PCB and locate its CLK, CMD, DAT0 (minimum), VCC, VCCQ, and GND pins from the datasheet. (b) Connect to the eMMC in-system using an eMMC ISP adapter (solder fine wires to the CMD, CLK, DAT0 pads; connect VCC/VCCQ from the adapter; hold the SoC in reset). Alternatively, use a chip-off approach: desolder the eMMC with a hot-air station (260°C, 30 seconds preheat, appropriate nozzle), reball if necessary, and mount on an eMMC-to-SD adapter. (c) Read the eMMC partitions: use `mmc` Linux tools to enumerate partitions (`mmc extcsd read /dev/mmcblk0`), identify boot0, boot1, user data, and RPMB areas. Read the user partition: `dd if=/dev/mmcblk0 of=emmc_user.bin bs=1M`. (d) Analyze the extracted image with binwalk for filesystem structure. If the image is encrypted, document the entropy analysis showing flat high-entropy regions. Deliverable: eMMC partition map, extcsd register dump, extracted firmware image, binwalk analysis, and a procedure document covering the ISP or chip-off methodology used.

---

## 18. Readings and References

- Torrance, Randy and James, Dick, "The State-of-the-Art in IC Reverse Engineering," CHES 2009
- Quadir, Saad E. et al., "A Survey on Chip Level Hardware Trojan Detection," ACM JETC, 2016
- Bhunia, Swarup and Tehranipoor, Mark, *Hardware Security: A Hands-On Learning Approach*, Morgan Kaufmann, 2018
- RayPCB, "PCB Reverse Engineering: Complete Guide (2026)," https://www.raypcb.com/pcb-reverse-engineering/ (retrieved: 2026-05-29)
- Moskvin, Slava, "Extracting Firmware: Every Method Explained," https://slava-moskvin.medium.com/extracting-firmware-every-method-explained-e94aa094d0dd (retrieved: 2026-05-29)
- SAE International, "AS6171 — Test Methods Standard for Counterfeit Electronic Parts," https://www.sae.org/standards/content/as6171/ (retrieved: 2026-05-29)
- SAE International, "AS6081 — Counterfeit Electronic Parts: Avoidance, Detection, Mitigation"
- NewAE Technology, "ChipWhisperer and Hardware Hacking Tools," https://github.com/orgs/newaetech/repositories (retrieved: 2026-05-29)
- swisskyrepo, "HardwareAllTheThings — Hardware Hacking Reference," https://github.com/swisskyrepo/HardwareAllTheThings (retrieved: 2026-05-29)
- Wrongbaud, "Hardware Debugging for Reverse Engineers — SWD, OpenOCD, and Xbox One Controllers," https://wrongbaud.github.io/posts/stm-xbox-jtag/ (retrieved: 2026-05-29)
- Degate Project, "Gate-Level Netlist Extraction from Die Images," https://github.com/DegateCommunity/Degate (retrieved: 2026-05-29)
- flashrom Project, "flashrom — Universal Flash Programming Tool," https://www.flashrom.org/ (retrieved: 2026-05-29)
- sigrok Project, "PulseView and sigrok-cli," https://sigrok.org/ (retrieved: 2026-05-29)
- Bozzato, Claudio et al., "Shaping the Glitch: Optimizing Voltage Fault Injection Attacks," IACR TCHES, 2019

---

## 19. Cross-References (tabular)

| Domain/Chapter | Topic | Relationship to This Chapter |
|---|---|---|
| Domain 17A (Side-Channel Analysis) | EM probes, power measurement | Die layout from this chapter enables precise EM probe positioning for DPA/CPA; PEM maps switching activity for targeting |
| Domain 17B (Fault Injection) | Decapsulation, die access, eFuse analysis | Decapsulation (§3) prerequisites laser FI and BBI; eFuse analysis informs which FI targets are available; FIB circuit edit bypasses protections without FI |
| Domain 12 (Reverse Engineering) | Firmware RE, static/dynamic analysis | Memory extraction (§5) produces firmware images for Domain 12 analysis; JTAG/SWD (17D) provides debug interface for dynamic analysis |
| Domain 7B (Hardware Vulnerabilities) | Hardware Trojans, supply chain | Hardware Trojans (§7) are hardware-level supply chain attacks; detection methods complement software supply chain integrity (Domain 19) |
| Domain 19 (Supply Chain) | Counterfeit detection, provenance | SAE AS6171/AS6081 counterfeit detection (§2.3) is the hardware component of supply chain security alongside software SLSA/SBOM frameworks |
| Domain 17D (Debug & Secure Boot) | JTAG/SWD exploitation, secure boot | This chapter covers PCB-level analysis preceding debug exploitation; memory extraction scripts produce inputs for 17D secure-boot bypass |

---

## 20. Glossary

| Term | Definition |
|---|---|
| **BGA (Ball Grid Array)** | IC package with solder balls on the bottom surface; connections hidden underneath, requiring X-ray for inspection and hot-air rework for desoldering |
| **Decapsulation** | Process of removing IC mold compound (via acid, plasma, or mechanical milling) to expose the silicon die for inspection or probing |
| **FIB (Focused Ion Beam)** | Gallium-ion beam tool for nanometer-precision milling, deposition, and circuit editing on die surfaces — enables rewiring security-critical circuits |
| **SEM (Scanning Electron Microscopy)** | High-resolution imaging (sub-nm) using an electron beam; essential for analyzing features on advanced process nodes where optical microscopy is insufficient |
| **Chip-Off** | Forensic technique of desoldering a memory chip from a PCB for direct reading on an external programmer, bypassing any SoC-level access controls |
| **NAND Flash** | Non-volatile memory using floating-gate transistors in serial strings; requires FTL reconstruction to interpret raw page data including ECC and bad-block management |
| **eMMC** | Embedded MultiMediaCard — NAND flash with integrated controller in a BGA package; partitions include boot0/boot1/user/RPMB with JEDEC-standardized register interface |
| **RPMB** | Replay Protected Memory Block — authenticated storage partition in eMMC/UFS using HMAC-SHA-256 with a pre-provisioned key, used for anti-rollback counters |
| **Hardware Trojan** | Malicious modification to an IC (combinational, sequential, or analog) inserted during design or fabrication — payload may leak data, deny service, or provide a kill switch |
| **Golden Reference** | Authenticated known-good sample of a component or firmware image used as the comparison baseline for detecting tampering, counterfeits, or Trojans |
| **SAM (Scanning Acoustic Microscopy)** | Ultrasonic imaging technique that reveals internal IC package defects (delamination, die-attach voids, cracks) non-destructively — primary recycled-part screening tool |
| **Gerber (RS-274X)** | Industry-standard vector file format describing PCB copper layers, solder mask, and silkscreen — the output of PCB reverse engineering vectorization |
| **Conformal Coating** | Protective polymer layer (acrylic, urethane, silicone) applied over a PCB surface to prevent inspection, probing, and environmental damage |
| **PUF (Physical Unclonable Function)** | Silicon fingerprint derived from manufacturing process variation; provides unique device identity that cannot be cloned or predicted — used for IC authentication |

---

## Exercises

**Exercise 1 — PCB Reverse Engineering and Signal Tracing.**
Select a consumer IoT device (e.g., a smart plug, IP camera, or Wi-Fi router). (a) Photograph the PCB (top and bottom) at sufficient resolution to read all component markings. Identify the main SoC, flash memory IC, power management IC, and wireless module by part number lookup. (b) Using a multimeter in continuity mode, trace the connections from all unpopulated test points and headers to IC pins. Identify UART TX/RX (look for 3.3V idle-high signals at 115200 baud), SPI flash connections (CLK/MOSI/MISO/CS), and any JTAG/SWD pads. (c) Connect a logic analyzer (Saleae or sigrok-compatible) to the identified UART and capture boot messages. Decode the baud rate and extract any debug output. (d) If SPI flash is identified, connect a CH341A programmer (with level-shifting if 1.8V) and dump the flash contents using `flashrom -p ch341a_spi -r firmware.bin`. (e) Perform initial firmware triage with `binwalk -eM firmware.bin` and `binwalk -E firmware.bin` (entropy analysis). Identify the filesystem type, kernel image, and any plaintext credentials or hardcoded keys.

**Exercise 2 — Firmware Extraction from eMMC.**
Using a target device with an eMMC storage IC (e.g., an Android set-top box or automotive infotainment unit): (a) Identify the eMMC IC on the PCB by its BGA package and part number. Determine the pinout from the datasheet (CMD, CLK, DAT0–DAT7, VCC, VCCQ, GND). (b) Attempt in-system reading: solder fine wires to the eMMC CMD/CLK/DAT0 pads (or use a pogo-pin jig) while holding the SoC in reset. Connect to an eMMC reader (e.g., Easy JTAG, Medusa Pro, or a Raspberry Pi with mmc-utils). (c) Read the CID, CSD, and EXT_CSD registers to identify the manufacturer, capacity, and partition configuration. (d) Dump the boot0, boot1, and user partitions. (e) Analyze the user partition: identify the partition table (GPT or MBR), mount the filesystem partitions, and extract the bootloader, kernel, and root filesystem. Search for hardcoded credentials, API keys, and certificate private keys.

**Exercise 3 — IC Decapsulation and Die Inspection.**
Using a sacrificial IC (e.g., an inexpensive microcontroller in a DIP or QFP package): (a) Perform chemical decapsulation using fuming nitric acid (98% HNO3) in a fume hood with full PPE (acid-resistant gloves, face shield, chemical apron). Heat the acid to 80°C, immerse the IC for 15–30 minutes, rinse in acetone → IPA → DI water, and dry under nitrogen. (b) Inspect the exposed die under an optical microscope at 5x, 20x, and 100x magnification. Photograph the top metal layer and identify functional blocks (pad ring, core logic, memory arrays, I/O buffers). (c) Read the die markings (manufacturer logo, lot code, die revision) and compare against the package markings. Document any discrepancy (potential counterfeit indicator). (d) If available, inspect the die under SEM at higher magnification to resolve individual metal traces and via structures. (e) Compare the die photo against a known-good reference (from a golden sample or published die shot). Document any differences that could indicate remarking, cloning, or modification.

**Exercise 4 — Counterfeit IC Detection Workflow (SAE AS6171).**
Obtain a batch of ICs from a secondary-market supplier (or use intentionally prepared samples — one genuine, one recycled, one remarked). (a) External visual inspection under stereomicroscope (10–30x): assess package surface finish, marking quality, lead/ball condition, date code plausibility. Perform UV inspection (365 nm) for fluorescence anomalies. Perform acetone swab test on markings. (b) X-ray inspection (if available): compare die size, position, and wire bond pattern against a golden reference. (c) Electrical parametric testing: measure IDD at specified voltage, timing parameters at temperature extremes, and functional behavior at rated speed. (d) Run the counterfeit visual comparison script from this module (SSIM-based marking comparison) against golden-reference photographs. (e) Document findings in a SAE AS6171-format inspection report with accept/reject determination and escalation recommendation (DPA if suspect).

**Exercise 5 — Hardware Trojan Detection via Side-Channel Fingerprinting.**
Using two identical ICs (e.g., STM32F4 — one unmodified, one with a simulated Trojan implemented as a modified firmware that activates a hidden function after a trigger count): (a) Capture 1,000 power traces from the genuine IC during a known workload (AES encryption of random plaintexts) using a ChipWhisperer. (b) Capture 1,000 power traces from the "Trojanized" IC during the same workload. (c) Compute the average power trace for each IC and overlay them. Identify any divergence regions (where the Trojan's additional logic consumes measurably different power). (d) Apply Welch's t-test (TVLA methodology) between the two trace sets. Identify time samples where |t| > 4.5, indicating statistically significant power consumption differences. (e) Correlate the identified divergence with the known Trojan activation logic. Discuss the limitations of side-channel-based Trojan detection: minimum detectable Trojan size, false-positive rate from process variation, and scalability to production testing.

---

## Readings and References

1. Anindya Sankar Roy. "Analysing and Extracting Firmware Using Binwalk 3.1.0 in 2025." <https://fr3ak-hacks.medium.com/analysing-and-extracting-firmware-using-binwalk-982012281ff6> (retrieved: 2026-05-29).
2. Ivan Orsolic. "Hardware Hacking Tutorial: Dumping and Reversing Firmware." <https://ivanorsolic.github.io/post/hardwarehacking1/> (retrieved: 2026-05-29).
3. Westside Electronics. "Reverse Engineering IoT: Firmware Extraction." <https://westsideelectronics.com/reverse-engineering-firmware/> (retrieved: 2026-05-29).
4. Steven Foerster. "Firmware RE with Binwalk and Ghidra." <https://stevenfoerster.com/tutorials/firmware-extraction-and-reverse-engineering-with-binwalk-and-ghidra/> (retrieved: 2026-05-29).
5. Infosec Institute. "Firmware Reverse Engineering: A Step-by-Step Guide." <https://www.infosecinstitute.com/resources/iot-security/iot-security-fundamentals-reverse-engineering-firmware/> (retrieved: 2026-05-29).
6. BugProve. "Firmware Reverse Engineering for Embedded Systems and Security Research." <https://bugprove.com/firmware-reverse-engineering/> (retrieved: 2026-05-29).
7. DEV Community (picoable). "A Practical Guide to Extracting and Analyzing IoT Firmware." <https://dev.to/picoable/a-practical-guide-to-extracting-and-analyzing-iot-firmware-4p20> (retrieved: 2026-05-29).
8. gl0bal01. "Firmware Reverse Engineering SOP." <https://gl0bal01.com/intel-codex/Security/Pentesting/sop-firmware-reverse-engineering> (retrieved: 2026-05-29).
9. NewAE Technology. "ChipWhisperer Documentation." <https://chipwhisperer.readthedocs.io/en/latest/> (retrieved: 2026-05-29).
10. NewAE Technology. "Introduction to Side-Channel Analysis." <https://learn.chipwhisperer.io/courses/introduction-to-side-channel-analysis> (retrieved: 2026-05-29).
11. Packet Labs. "ChipWhisperer: Open Source Platform for Side Channel Security Testing." <https://www.packetlabs.net/posts/chipwisperer-an-open-source-platform-for-side-channel-security-testing/> (retrieved: 2026-05-29).
12. PT SWARM. "GigaVulnerability: Readout Protection Bypass on GigaDevice GD32 MCUs." <https://swarm.ptsecurity.com/gigavulnerability-readout-protection-bypass-on-gigadevice-gd32-mcus/> (retrieved: 2026-05-29).

---

## Cross-References

| Module | Relationship |
|--------|-------------|
| Domain 17A — Physical and Hardware Security | Foundation module covering physical security zones, lock bypass, RFID cloning, USB attacks, and side-channel overview |
| Domain 17B — Fault Injection | Fault injection techniques (voltage/EM/laser) that require die-level access obtained through decapsulation methods from this chapter |
| Domain 17D — Debug Interfaces and Secure Boot | JTAG/SWD debug ports identified during PCB RE; firmware images extracted in this chapter analyzed for secure-boot bypass in 17D |
| Domain 12 — Reverse Engineering | Firmware analysis (Ghidra, IDA) applied to images extracted via flashrom/chip-off/eMMC dump from this chapter |
| Domain 16A — ICS/OT Security | PCB RE and firmware extraction applied to ICS field devices: PLC firmware dumps, RTU flash analysis, ICS protocol RE |
| Domain 13 — Cryptography | Cryptographic key material extracted from firmware images (hardcoded keys, certificate private keys) and die-level analysis of crypto accelerators |
