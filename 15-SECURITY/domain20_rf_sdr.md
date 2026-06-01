---
corso: "Cybersecurity Masterclass"
fase: "Domain 20 — RF and Software-Defined Radio Security"
modulo: "20.A"
titolo: "Radio Frequency and Software-Defined Radio"
versione: "GNU Radio 3.10 / HackRF One / RTL-SDR v3 / Proxmark3 RDV4 / Ubertooth One"
livello: "Advanced"
prerequisiti:
  - "Fundamentals of electromagnetic wave propagation and RF spectrum allocation"
  - "Linux command-line proficiency and Python scripting"
  - "Basic DSP concepts: sampling, Fourier transforms, modulation"
  - "Network protocol analysis (Wireshark, tcpdump)"
  - "Domain 9 — Network Security fundamentals"
obiettivi:
  - "Configure and operate SDR hardware (RTL-SDR, HackRF, USRP) for signal capture and transmission"
  - "Build GNU Radio 3.10 flowgraphs for RF protocol demodulation and signal analysis"
  - "Reverse-engineer unknown RF protocols using URH, inspectrum, and IQ analysis"
  - "Execute and defend against RF replay, jamming, and GPS spoofing attacks in a shielded lab"
  - "Assess RFID/NFC system security using Proxmark3 (Darkside, nested, hardnested attacks)"
tag: [rf-security, sdr, gnu-radio, hackrf, replay-attack, rfid, nfc, bluetooth, zigbee, gps-spoofing, tempest, lora, spectrum-analysis]
---

# Domain 20 — Radio Frequency and Software-Defined Radio

> **Learning objectives.** After completing this module the student will be able to: (1) select appropriate SDR hardware and antennas for a given frequency range and assessment scenario; (2) construct end-to-end GNU Radio 3.10 flowgraphs that capture, filter, demodulate, and decode ISM-band signals; (3) perform systematic RF protocol reverse engineering from raw IQ capture through bit extraction to protocol field dissection; (4) demonstrate fixed-code replay, RollJam, and GPS spoofing attacks in a controlled shielded environment and articulate their real-world impact; (5) conduct RFID/NFC security assessments against Mifare Classic, HID ProxCard, and BLE targets using Proxmark3 and Ubertooth, documenting findings with CVSS scores and remediation guidance.

> **Scope.** SDR platforms and GNU Radio. IQ sampling and modulation recognition. RF protocol reverse engineering (URH, inspectrum). GSM baseband (gr-gsm). Private cellular (OpenBTS, srsRAN). RF attacks: fixed-code replay, rolling-code analysis (KeeLoq, HITAG2, RollJam), RF jamming (reactive, constant, deceptive). GPS spoofing (gps-sdr-sim). ADS-B spoofing (dump1090). AIS spoofing. TPMS tracking. LoRa/LoRaWAN security. RFID/NFC (Proxmark3, Mifare Classic). Bluetooth (Ubertooth, BLE, KNOB, BrakTooth). Zigbee (KillerBee, IEEE 802.15.4). Satellite reception. Wireless alarm systems. RF shielding and TEMPEST.

---

## 1. Software-Defined Radio Fundamentals

### 1.1 SDR Hardware Comparison

| Parameter | RTL-SDR v3 | HackRF One | USRP B210 | bladeRF 2.0 micro xA4 | LimeSDR Mini 2.0 |
|---|---|---|---|---|---|
| Freq. range | 24 MHz – 1.766 GHz | 1 MHz – 6 GHz | 70 MHz – 6 GHz | 47 MHz – 6 GHz | 10 MHz – 3.5 GHz |
| Bandwidth | 2.4 MHz (stable) | 20 MHz | 56 MHz (2x2 MIMO) | 56 MHz | 30.72 MHz |
| ADC bits | 8 | 8 | 12 | 12 | 12 |
| TX capable | No | Yes (half-duplex) | Yes (full-duplex) | Yes (full-duplex) | Yes (full-duplex) |
| Duplex | RX only | Half | Full (2T2R) | Full (2T2R) | Full (2T2R) |
| USB interface | USB 2.0 | USB 2.0 | USB 3.0 | USB 3.0 | USB 3.0 |
| FPGA | None | CPLD (Xilinx) | Spartan-6 | Cyclone V | Intel MAX 10 |
| Clock accuracy | 1 ppm (with TCXO) | 20 ppm | 2 ppm (GPSDO opt.) | 1 ppm (VCTCXO) | 1 ppm (VCTCXO) |
| Approx. price | $25–$35 | $300–$350 | $1,500–$2,200 | $480–$720 | $200–$300 |
| Primary use | Passive RX, ADS-B, FM, trunking, passive recon | Replay, GPS spoofing, signal injection, protocol RE | Cellular research, radar, high-dynamic-range work | Private cellular, MIMO, full-duplex research | LoRa/LTE labs, mid-range TX/RX |

**Antenna considerations.** Impedance match (50 ohm standard). Frequency-specific antennas outperform wideband whips by 10–20 dB. For HF below 30 MHz, use an upconverter (e.g., Ham It Up) with RTL-SDR. Directional antennas (Yagi, patch, horn) are required for direction finding and long-range work.

### 1.2 Core SDR Command-Line Tools

**RTL-SDR utilities** — the `rtl-sdr` package provides low-level capture and analysis tools:

```bash
# Capture raw IQ samples to file (center freq 433.92 MHz, sample rate 2.048 MS/s)
rtl_sdr -f 433920000 -s 2048000 -g 40 capture_433.iq

# Real-time spectrum display (ncurses)
rtl_power -f 400M:450M:10k -g 40 -i 10 -e 1h power_scan.csv

# FM broadcast receiver (88.5 MHz, output WAV)
rtl_fm -f 88500000 -M wbfm -s 200000 -r 48000 - | aplay -r 48000 -f S16_LE -t raw
```

**HackRF utilities** — the `hackrf` package provides TX and RX:

```bash
# Receive raw IQ to file (center 915 MHz, 10 MS/s, LNA gain 32, VGA gain 20)
hackrf_transfer -r capture_915.iq -f 915000000 -s 10000000 -l 32 -g 20

# Transmit IQ from file (center 433.92 MHz, 2 MS/s, TX VGA gain 47)
hackrf_transfer -t replay.iq -f 433920000 -s 2000000 -x 47

# Sweep spectrum 1 MHz – 6 GHz
hackrf_sweep -f 1:6000 -w 100000 -l 32 -g 20 > sweep_output.csv

# Query device info
hackrf_info
```

**USRP (UHD) utilities:**

```bash
# Probe connected USRP devices
uhd_find_devices
uhd_usrp_probe

# Capture IQ samples (center 900 MHz, rate 5 MS/s, gain 30, 10M samples)
rx_samples_to_file --freq 900e6 --rate 5e6 --gain 30 --nsamps 10000000 --file capture.dat

# Transmit from file
tx_samples_from_file --freq 900e6 --rate 5e6 --gain 20 --file tx_data.dat
```

### 1.3 GNU Radio

GNU Radio is the standard open-source DSP framework for SDR. Processing is defined as a **flowgraph**: directed graph of interconnected blocks (sources, processing, sinks). Blocks are implemented in C++ (performance-critical) or Python (rapid prototyping). The **GNURadio Companion (GRC)** provides a graphical flowgraph editor that generates Python code.

#### gr-osmosdr Source Configuration

The `gr-osmosdr` library provides a hardware-abstraction source/sink that works across RTL-SDR, HackRF, USRP, LimeSDR, and bladeRF:

```python
import osmosdr

# Create source (auto-detect device, or specify device string)
src = osmosdr.source(args="numchan=1")

# Device-specific strings:
# RTL-SDR:  args="rtl=0"
# HackRF:   args="hackrf=0"
# USRP:     args="uhd,type=b200"
# LimeSDR:  args="soapy=0,driver=lime"
# bladeRF:  args="bladerf=0"

src.set_sample_rate(2.048e6)
src.set_center_freq(433.92e6)
src.set_gain(40)
src.set_if_gain(20)
src.set_bb_gain(20)
src.set_bandwidth(0)  # 0 = auto
```

#### Python Flowgraph Example — FM Demodulation

```python
#!/usr/bin/env python3
from gnuradio import gr, analog, audio, filter
import osmosdr

class FMReceiver(gr.top_block):
    def __init__(self, freq=88.5e6):
        gr.top_block.__init__(self, "FM Receiver")
        samp_rate = 2.048e6
        audio_rate = 48000
        audio_decimation = int(samp_rate / audio_rate)

        # Source
        self.src = osmosdr.source(args="rtl=0")
        self.src.set_sample_rate(samp_rate)
        self.src.set_center_freq(freq)
        self.src.set_gain(40)

        # Low-pass filter
        self.lpf = filter.fir_filter_ccf(
            1,
            filter.firdes.low_pass(1, samp_rate, 100e3, 10e3,
                                    filter.firdes.WIN_HAMMING))

        # WBFM demodulator
        self.demod = analog.wfm_rcv(
            quad_rate=samp_rate,
            audio_decimation=audio_decimation)

        # Audio sink
        self.audio_sink = audio.sink(audio_rate, "", True)

        # Connect flowgraph
        self.connect(self.src, self.lpf, self.demod, self.audio_sink)

if __name__ == "__main__":
    tb = FMReceiver(freq=88.5e6)
    tb.start()
    input("Press Enter to stop...")
    tb.stop()
    tb.wait()
```

#### Custom Block Development (OOT Module)

```bash
# Create out-of-tree module
gr_modtool newmod my_blocks
cd gr-my_blocks

# Add a Python block
gr_modtool add -t sync -l python my_decoder

# Add a C++ block
gr_modtool add -t sync -l cpp my_fast_decoder

# Build and install
mkdir build && cd build
cmake ..
make -j$(nproc)
sudo make install
sudo ldconfig
```

Custom Python block skeleton (`python/my_blocks/my_decoder.py`):

```python
import numpy as np
from gnuradio import gr

class my_decoder(gr.sync_block):
    def __init__(self, threshold=0.5):
        gr.sync_block.__init__(self,
            name="my_decoder",
            in_sig=[np.complex64],
            out_sig=[np.float32])
        self.threshold = threshold

    def work(self, input_items, output_items):
        in0 = input_items[0]
        out = output_items[0]
        magnitude = np.abs(in0)
        out[:] = (magnitude > self.threshold).astype(np.float32)
        return len(out)
```

### 1.4 IQ Sampling

SDR hardware samples radio signals as **IQ (In-phase / Quadrature)** pairs: two time-domain signals at the same sample rate representing the real (I) and imaginary (Q) components of the complex baseband signal. The complex representation preserves both amplitude and phase, enabling any modulation scheme to be demodulated entirely in software.

**Nyquist constraint:** the sample rate must be at least twice the signal bandwidth. A 2.048 MS/s sample rate gives 2.048 MHz of observable bandwidth. Signals outside this bandwidth alias into the passband.

**Quadrature mixing:** the SDR's mixer multiplies the incoming RF signal by a local oscillator at the tuned center frequency, producing cos (I channel) and sin (Q channel) products. After low-pass filtering, these become the complex baseband signal: `s(t) = I(t) + jQ(t)`.

**DC offset:** direct-conversion receivers produce a DC spike at the center frequency (LO leakage). Mitigate by tuning slightly off-center and compensating in software, or using the DC offset correction in `gr-osmosdr`.

**IQ file formats:**

| Format | Structure | Bits/sample | Tools |
|---|---|---|---|
| Raw interleaved I/Q | I0,Q0,I1,Q1,... (binary) | 8 (RTL-SDR), 16 (HackRF), 32 (float32) | rtl_sdr, hackrf_transfer |
| WAV (2-channel) | Standard WAV, ch1=I, ch2=Q | 16 or 32 | SDR#, GQRX |
| SigMF | JSON metadata + raw binary | Any | SigMF tools, GNU Radio |
| Complex float32 | IEEE 754 float pairs | 32 per component | GNU Radio (.fc32) |

### 1.5 Modulation Recognition and Signal Analysis

**Frequency-domain analysis** via FFT reveals occupied bandwidth, center frequency, and signal shape. Waterfall plots show frequency vs. time, revealing intermittent transmissions and frequency hopping.

**Modulation types and identification characteristics:**

| Modulation | Time domain | Freq. domain | Constellation | Use cases |
|---|---|---|---|---|
| AM / OOK | Amplitude envelope varies | Symmetric sidebands | Single point + origin | Remote controls, ASK keyfobs |
| FM / WBFM | Constant envelope | Wider bandwidth (150 kHz FM broadcast) | Circle | FM broadcast, analog voice |
| FSK (2-FSK, 4-FSK) | Constant envelope, freq shifts | Discrete spectral lines | N/A (frequency plot) | Pagers, POCSAG, tire sensors, keyfobs |
| BPSK | Phase flips 180 deg | Narrow, symmetric | 2 points on real axis | Satellite, GPS C/A |
| QPSK | Phase shifts 90 deg | Narrow, symmetric | 4 points, 90 deg apart | DVB-S, CDMA |
| GMSK | Constant envelope, Gaussian-shaped frequency transitions | Narrow, efficient | Circle | GSM, AIS |
| QAM-16/64/256 | Amplitude + phase vary | Compact, high spectral efficiency | Grid (4x4, 8x8, 16x16) | Cable, Wi-Fi, LTE |
| OFDM | Sum of many subcarriers | Many narrow subcarriers | Per-subcarrier QAM | Wi-Fi, LTE, 5G NR, DVB-T |
| CSS (Chirp) | Frequency sweeps linearly | Chirp pattern | N/A | LoRa |

**Visual analysis tools:**

```bash
# GQRX — real-time spectrum analyzer with waterfall
gqrx   # GUI: set device to rtl=0, tune frequency, adjust gain

# osmocom_fft — lightweight FFT display
osmocom_fft -a rtl=0 -f 433.92e6 -s 2.048e6

# inspectrum — post-capture spectrogram analysis
inspectrum capture_433.iq
# Set sample rate in GUI, zoom to signal, use cursors to measure symbol rate
```

**Automated modulation classification** approaches:
1. **Energy detection** — signal present if power exceeds noise floor by threshold.
2. **Cyclostationary feature analysis** — periodic statistics unique to each modulation.
3. **Higher-order statistics** — kurtosis, cumulants distinguish AM from FM from PSK.
4. **ML-based** — CNN on IQ spectrograms or raw IQ windows; achieves >90% accuracy across 10+ modulation types at SNR > 5 dB.

---

## 2. RF Protocol Reverse Engineering

### 2.1 Universal Radio Hacker (URH)

URH provides an end-to-end workflow: capture, demodulate, extract bits, dissect protocol fields, and fuzz.

**Step 1 — Signal capture:**

```bash
# Launch URH
urh

# Or capture from CLI with rtl_sdr / hackrf_transfer first, then open in URH:
rtl_sdr -f 433920000 -s 2048000 -g 40 -n 20000000 keyfob_capture.iq
# Open keyfob_capture.iq in URH → File → Open
```

**Step 2 — Automatic demodulation:**
URH auto-detects modulation (ASK, FSK, PSK) and parameters (center frequency, bit length, noise threshold). Manual override: Interpretation tab → set modulation type, samples per symbol, error tolerance.

**Step 3 — Bit extraction:**
URH displays the decoded bitstream. Identify preamble (repeating pattern like `10101010`), sync word, payload, and checksum fields. URH's "Analysis" tab auto-correlates fields across multiple captures to identify static vs. dynamic fields.

**Step 4 — Protocol dissection:**
- Label fields (address, command, counter, CRC)
- URH calculates common CRC polynomials (CRC-8, CRC-16, CRC-CCITT) and tests against observed checksums
- Identify encoding: Manchester, differential Manchester, NRZ, Miller

**Step 5 — Fuzzing and injection:**

```bash
# URH provides a built-in fuzzer:
# Generator tab → define message template → set fuzz ranges for identified fields
# Send via connected SDR (HackRF, USRP)

# Or export crafted bitstream and transmit:
hackrf_transfer -t crafted_signal.iq -f 433920000 -s 2000000 -x 40
```

### 2.2 inspectrum

inspectrum provides visual spectrogram analysis of captured IQ files. The analyst identifies signal boundaries, measures symbol rate, and extracts timing parameters.

```bash
# Open IQ capture
inspectrum capture.iq

# In GUI:
# 1. Set sample rate (must match capture rate)
# 2. Zoom to signal region
# 3. Right-click → Add derived plot → Add amplitude/frequency/phase plot
# 4. Use cursors to measure symbol period
# 5. Extract symbol rate = 1 / symbol_period
# 6. Right-click → Extract symbols → export to file for further analysis
```

### 2.3 GSM Baseband (gr-gsm)

**gr-gsm** provides GNU Radio blocks for GSM L1/L2 processing — captures the GSM downlink, demodulates GMSK, and decodes signaling and traffic channels.

```bash
# Live monitor — capture GSM downlink and decode BCCH
grgsm_livemon -f 939.4e6
# Listens on the specified ARFCN downlink frequency
# Outputs decoded GSM frames to UDP localhost:4729 (Wireshark-compatible)

# Scan for GSM base stations (all bands)
grgsm_scanner --band GSM900
grgsm_scanner --band DCS1800

# Capture to file, then decode offline
rtl_sdr -f 939400000 -s 2000000 -g 40 gsm_capture.iq
grgsm_decode -c capture.cfile -f 939.4e6 -s 2e6

# View decoded GSM frames in Wireshark
wireshark -k -i lo -f "udp port 4729" -Y gsmtap
```

**GSM channel types decoded by gr-gsm:**
- **BCCH** — Broadcast Control Channel (cell identity, LAC, neighbor list)
- **CCCH** — Common Control Channel (paging, immediate assignment)
- **SDCCH** — Standalone Dedicated Control Channel (SMS, location updates)
- **TCH** — Traffic Channel (voice, data)

**A5/1 decryption:** gr-gsm can apply Kraken rainbow tables to crack A5/1 encrypted GSM traffic. Requires pre-computed tables (~2 TB) and captured Kc from the air interface.

### 2.4 Private Cellular Networks

#### OpenBTS / YateBTS — GSM BTS

A GSM base station on commodity hardware. Phones within range associate with the BTS, enabling IMSI capture, SMS interception, and downgrade attacks.

```bash
# YateBTS configuration (yate.conf)
# Set ARFCN, MCC, MNC, LAC to match target network or create rogue cell
[ybts]
Radio.Band=900
Radio.C0=50          # ARFCN
Identity.MCC=001     # Test MCC
Identity.MNC=01      # Test MNC
Identity.LAC=1000
Radio.PowerManager.MaxAttenDB=35
```

#### srsRAN — 4G/5G RAN

srsRAN implements a complete LTE/5G stack: eNodeB/gNodeB (base station), UE (user equipment), and EPC/5GC (core network).

```bash
# Start the EPC (core network)
sudo srsepc epc.conf

# Start the eNodeB
sudo srsenb enb.conf

# Start a UE (for testing)
sudo srsue ue.conf
```

Key srsRAN config parameters (`enb.conf`):

```ini
[enb]
enb_id = 0x19B
mcc = 001
mnc = 01
n_prb = 50        # Number of PRBs (bandwidth: 25=5MHz, 50=10MHz, 100=20MHz)

[rf]
device_name = auto
device_args = auto
tx_gain = 80
rx_gain = 40

[expert]
# Security: set to force NIA1/NEA1 or test NULL ciphering
nas_enable_security = true
```

**Security research use cases:** testing UE behavior under rogue cell attachment, verifying VoLTE encryption enforcement, IMSI/SUPI exposure in attach procedures, RRC redirect attacks, QoS manipulation.

---

## 3. Common RF Protocols — ISM Band

### 3.1 ISM Band Overview

| Band | Region | Frequency | Typical devices |
|---|---|---|---|
| 315 MHz | US | 314.0–315.0 MHz | Garage doors, car keyfobs, TPMS (US) |
| 433 MHz | EU / Global | 433.05–434.79 MHz | Remote controls, weather stations, keyfobs, TPMS (EU) |
| 868 MHz | EU | 868.0–868.6 MHz | LoRa, Zigbee, alarm systems, smart meters |
| 915 MHz | US | 902.0–928.0 MHz | LoRa, Zigbee, industrial IoT |
| 2.4 GHz | Global | 2.400–2.4835 GHz | Wi-Fi, Bluetooth, Zigbee, microwave |

### 3.2 Fixed Code vs. Rolling Code

**Fixed code** devices transmit the same bitstream on every activation. The code is typically ASK/OOK modulated at 315/433 MHz, with a 20–28 bit address and a 4–8 bit command. Trivially replayable.

**Rolling code** (hopping code) devices increment a counter and encrypt it with a block cipher before transmission. The receiver maintains a synchronization window — it accepts codes within a range of counter values ahead of the last accepted code.

**Common rolling-code implementations:**

| System | Cipher | Key length | Known weaknesses |
|---|---|---|---|
| KeeLoq | KeeLoq (NLFSR) | 64-bit | Slide attacks, algebraic attacks, DPA on receiver |
| HITAG2 | HITAG2 (stream cipher) | 48-bit | Known-plaintext attack, time-memory trade-off |
| AUT64 | AUT64 | 120-bit | Weak key scheduling |
| Megamos Crypto | Proprietary | 96-bit | Key recovery from 3 authentications |
| DST40 | DST40 | 40-bit | Brute-forceable (2^40) |

---

## 4. RF Attacks

### 4.1 Fixed-Code Replay

Garage doors, older car keyfobs, and simple remote controls use fixed-code RF transmission (ASK/OOK at 315/433 MHz). The attacker records the transmission and replays it verbatim.

```bash
# Step 1: Record the transmission
hackrf_transfer -r garage_capture.iq -f 433920000 -s 2000000 -l 32 -g 20
# Press the remote button during capture

# Step 2: Trim the capture to just the transmission
# Use inspectrum or URH to identify start/end, then:
dd if=garage_capture.iq of=garage_trimmed.iq bs=1 skip=OFFSET count=LENGTH

# Step 3: Replay
hackrf_transfer -t garage_trimmed.iq -f 433920000 -s 2000000 -x 47

# Alternative: use rtl_433 to decode and identify the protocol
rtl_433 -f 433920000 -g 40
# rtl_433 identifies the device type, protocol, and decoded fields
```

**GRC flowgraph approach:** In GNU Radio Companion, create: `File Source → Multiply Const (amplitude) → osmocom Sink`. Set the sink frequency to the target, sample rate matching the capture, and TX gain to override the legitimate signal.

**Defense:** rolling codes, challenge-response, or time-windowed codes.

### 4.2 Rolling-Code Attacks

#### KeeLoq Cryptanalysis

KeeLoq uses a 64-bit key and a 32-bit non-linear feedback shift register. Known attacks:

1. **Slide attack** — recovers the manufacturer key from ~2^16 known plaintext-ciphertext pairs (captured legitimate transmissions). Once the manufacturer key is known, any device using that manufacturer's key can be cloned.
2. **Algebraic attack** — expresses KeeLoq as a system of multivariate equations; solvable with SAT solvers given sufficient known plaintexts.
3. **DPA (Differential Power Analysis)** — side-channel attack on the receiver's decryption. Requires physical access to the receiver and a power measurement probe. Recovers the device-specific key.

#### RollJam Attack

A sophisticated relay attack against rolling-code systems:

1. Attacker positions a device near the target (car/garage) with two radios: one jammer, one receiver.
2. Victim presses the keyfob button. The attacker simultaneously jams the receiver and captures the transmitted code (Code N).
3. The victim presses the button again (because the first press "didn't work"). The attacker captures Code N+1, stops jamming, and replays Code N to the receiver.
4. The receiver accepts Code N (counter advances to N). The attacker retains Code N+1 — a valid unused code.

```bash
# RollJam requires simultaneous TX (jam) and RX (capture)
# Half-duplex HackRF cannot do both — requires two HackRFs or a full-duplex SDR

# Radio 1: jam the receiver (transmit noise on the target frequency)
hackrf_transfer -t noise.iq -f 433920000 -s 2000000 -x 47

# Radio 2: capture the keyfob transmission
hackrf_transfer -r capture.iq -f 433920000 -s 2000000 -l 32 -g 20
```

#### HITAG2 Key Recovery

HITAG2 is used in older vehicle immobilizers. The attack recovers the 48-bit key from captured transponder-to-reader exchanges.

```bash
# Using Proxmark3 (Iceman fork) for HITAG2 attacks:
# Sniff transponder-reader communication
pm3 --> lf hitag sniff

# Perform cryptanalytic key recovery (requires captured nonces)
pm3 --> lf hitag crack

# Clone transponder with recovered key
pm3 --> lf hitag sim -k <recovered_key>
```

### 4.3 RF Jamming

Jamming denies legitimate communication by overwhelming the receiver with interference. Three primary types:

#### Constant Jamming

Continuous transmission on the target frequency. Simple but detectable and power-hungry.

```bash
# Generate continuous noise and transmit
# Create noise IQ file:
python3 -c "
import numpy as np
noise = (np.random.randn(10000000) + 1j * np.random.randn(10000000)).astype(np.complex64)
noise.tofile('noise.iq')
"

# Transmit continuously (loop the file)
hackrf_transfer -t noise.iq -f 433920000 -s 2000000 -x 47 -R
# -R = repeat transmission
```

#### Reactive Jamming

Listens for legitimate transmissions and jams only when a signal is detected. More power-efficient and harder to detect during idle periods. Requires low-latency signal detection.

**Implementation:** GNU Radio flowgraph with `Power Squelch → Noise Source → osmocom Sink`. When received power exceeds the squelch threshold, the noise source activates.

#### Deceptive Jamming

Transmits a valid-looking but corrupted signal. The receiver processes it as a legitimate transmission but decodes garbage. Effective against protocols without error detection or with weak checksums.

**Detection methods:**
- **Spectrum monitoring** — persistent high-power broadband signal at the target frequency
- **Signal quality metrics** — sudden SNR degradation, increased bit error rate
- **Direction finding** — triangulate the jammer using multiple receivers and time-difference-of-arrival (TDOA) or received-signal-strength (RSS) techniques
- **Frequency agility** — detect jammer by observing that interference follows frequency hops

**Mitigation:**
- **Spread spectrum** — FHSS (frequency hopping) makes narrowband jamming ineffective; DSSS (direct sequence) provides processing gain against broadband jamming
- **Adaptive power control** — increase TX power to overcome the jammer
- **Directional antennas** — null the jammer direction
- **Error-correcting codes** — FEC (forward error correction) recovers data from partially jammed signals
- **Protocol-level** — retransmission with randomized timing, channel switching

### 4.4 GPS Spoofing

Civilian GPS (L1 C/A at 1575.42 MHz) is unencrypted and unauthenticated. A spoofer generates counterfeit satellite signals that overpower the genuine ones.

```bash
# Step 1: Generate spoofed GPS IQ samples
# Clone gps-sdr-sim
git clone https://github.com/osqzss/gps-sdr-sim.git
cd gps-sdr-sim && make

# Download current GPS ephemeris (RINEX navigation file)
wget ftp://cddis.gsfc.nasa.gov/gnss/data/daily/2026/brdc/brdc1280.26n.Z
gunzip brdc1280.26n.Z

# Generate IQ samples for a static spoofed location (lat, lon, alt)
./gps-sdr-sim -e brdc1280.26n -l 48.8566,2.3522,30 -b 8 -o gps_spoof.bin
# -e = ephemeris file
# -l = target lat,lon,alt (Paris, Eiffel Tower)
# -b = 8-bit samples (HackRF)
# -o = output IQ file

# Step 2: Transmit spoofed GPS signal
hackrf_transfer -t gps_spoof.bin -f 1575420000 -s 2600000 -x 47
```

**Dynamic spoofing:** generate a trajectory (waypoints over time) to gradually pull the target away from its real position:

```bash
# User motion file (ECEF coordinates at 0.1s intervals)
./gps-sdr-sim -e brdc1280.26n -u trajectory.csv -b 8 -o gps_dynamic.bin
```

**Anti-spoofing techniques:**
- **Multi-constellation** — cross-check GPS vs. GLONASS vs. Galileo vs. BeiDou; spoofing all simultaneously is impractical
- **Receiver autonomous integrity monitoring (RAIM)** — detect inconsistencies between satellite signals
- **Signal authentication** — Galileo OSNMA (Open Service Navigation Message Authentication) provides cryptographic authentication of navigation messages
- **Antenna arrays** — spatial processing rejects signals arriving from the wrong direction
- **Inertial navigation** — IMU cross-check detects sudden position jumps
- **Clock monitoring** — GPS-disciplined clocks detect timing anomalies that accompany position spoofing

**Military GPS** (P(Y) code, M code) uses encrypted signals resistant to spoofing.

### 4.5 ADS-B

ADS-B (Automatic Dependent Surveillance — Broadcast) operates at 1090 MHz (Mode S Extended Squitter). Aircraft broadcast position, altitude, velocity, and identity in cleartext. No authentication, no encryption.

```bash
# Receive and decode ADS-B with RTL-SDR
# dump1090 (Mutability/FlightAware fork)
dump1090 --interactive --net --device-index 0 --gain 40

# dump1090 provides:
# - Interactive console with aircraft table
# - Web server (http://localhost:8080) with map
# - Raw and decoded output on TCP ports 30002, 30003, 30005

# Alternative: dump1090-fa (FlightAware fork with enhanced decoding)
dump1090-fa --device-index 0 --gain -10 --net --quiet

# Pipe to virtual radar server or feed to ADS-B Exchange
socat TCP:localhost:30005 TCP:data.adsbexchange.com:30005
```

**ADS-B message format (112-bit Extended Squitter):**
- Downlink Format (5 bits): DF=17 for ADS-B
- Capability (3 bits)
- ICAO Address (24 bits): unique aircraft identifier
- Type Code (5 bits): identifies message type
- Data (51 bits): position, velocity, identification
- Parity/CRC (24 bits)

**Spoofing risks:** injecting ghost aircraft on ATC displays, denial of service (flood with fake targets), track manipulation (modify reported position of real aircraft).

**Mitigations:** multilateration (MLAT) from multiple receivers verifies position consistency; signal fingerprinting identifies non-aviation transmitters; ADS-B security extensions (ADS-B IN with TIS-B validation) under development.

### 4.6 AIS

AIS (Automatic Identification System) operates at 161.975 MHz (ch. 87B) and 162.025 MHz (ch. 88B) using 9600 bps GMSK. Unencrypted, unauthenticated.

```bash
# Receive AIS with RTL-SDR
rtl_ais -p 0 -g 40
# Outputs NMEA sentences to stdout and UDP

# Or use GNU Radio + gr-ais for more control
# Or AIS-catcher for high-performance multi-channel decoding
AIS-catcher -d 0 -gr TUNER 40
```

**Attack surface:** spoof vessel positions, create ghost ships, alter reported course/speed, trigger false collision avoidance maneuvers.

### 4.7 TPMS

Tire Pressure Monitoring Systems operate at 315 MHz (US, mandated by TREAD Act) or 433 MHz (EU). Each sensor transmits a unique 32-bit ID, tire pressure, temperature, and battery status using OOK or FSK modulation. Transmissions occur every 60–90 seconds or on pressure change.

```bash
# Decode TPMS with rtl_433
rtl_433 -f 315000000 -g 40 -R 59 -R 60 -R 67
# -R 59 = Toyota TPMS
# -R 60 = Ford TPMS
# -R 67 = Schrader TPMS
# Outputs: sensor ID, pressure (kPa), temperature, battery status

# Track a specific vehicle by correlating 4 sensor IDs
rtl_433 -f 315000000 -g 40 -F json | jq 'select(.id == "AABBCCDD")'
```

**Attack vectors:**
- **Vehicle tracking** — TPMS IDs are static and unique per tire; correlate across roadside receivers to track movement patterns
- **Spoofed alerts** — replay or craft low-pressure alerts to force a driver to stop
- **Privacy** — identify specific vehicles at arbitrary locations

### 4.8 LoRa/LoRaWAN

#### Chirp Spread Spectrum (CSS)

LoRa uses Chirp Spread Spectrum: each symbol is a frequency chirp sweeping the entire bandwidth. Spreading Factor (SF7–SF12) controls the chirp duration — higher SF = longer range, lower data rate, more resistance to interference.

| SF | Chips/symbol | Bit rate (125 kHz BW) | Sensitivity | Range (urban) |
|---|---|---|---|---|
| 7 | 128 | 5,470 bps | -123 dBm | 2 km |
| 8 | 256 | 3,125 bps | -126 dBm | 3 km |
| 9 | 512 | 1,758 bps | -129 dBm | 4 km |
| 10 | 1024 | 977 bps | -132 dBm | 5 km |
| 11 | 2048 | 537 bps | -134.5 dBm | 7 km |
| 12 | 4096 | 293 bps | -137 dBm | 10 km |

#### LoRaWAN Security Architecture

**OTAA (Over-The-Air Activation):**
1. Device sends JoinRequest (DevEUI, AppEUI, DevNonce) encrypted with AppKey (AES-128 root key)
2. Network responds with JoinAccept (AppNonce, NetID, DevAddr)
3. Session keys derived: NwkSKey (network session) and AppSKey (application session)
4. Fresh keys per join — compromise of session keys doesn't compromise root key

**ABP (Activation By Personalization):**
- NwkSKey and AppSKey pre-provisioned on device — no join procedure
- Static session keys (no rotation mechanism in LoRaWAN 1.0)
- Frame counter starts at 0 on device reset — replay vulnerability

#### LoRa Capture and Analysis

```bash
# gr-lora — GNU Radio blocks for LoRa reception
# Install: https://github.com/rpp0/gr-lora
# GRC flowgraph: osmocom Source (868.1 MHz) → gr-lora Receiver → Message Debug

# RTL-SDR capture of LoRa signals for offline analysis
rtl_sdr -f 868100000 -s 1000000 -g 40 lora_capture.iq

# LoRa demodulation parameters:
# Bandwidth: 125 kHz, 250 kHz, or 500 kHz
# Spreading Factor: 7-12
# Code Rate: 4/5, 4/6, 4/7, 4/8
```

**LoRaWAN attacks:**
- **ABP replay** — capture frames, replay after device power-cycle resets the frame counter; server accepts if frame counter tracking is lax
- **Join replay** — capture JoinRequest, replay to force re-join and potentially desynchronize device
- **Bit-flipping** — LoRaWAN 1.0 uses AES-CTR for payload encryption; without authenticated encryption, bit-flipping the ciphertext produces predictable plaintext changes if the attacker knows the plaintext structure
- **ACK spoofing** — transmit forged ACKs to desynchronize the device
- **Jamming** — CSS is spread-spectrum but not immune; sustained broadband jamming at the LoRa frequency band denies service

**LoRaWAN 1.1 improvements:** separate NwkSKey for uplink/downlink, server-side frame counter persistence, JoinNonce replay protection, roaming security.

---

## 5. RFID and NFC

### 5.1 RFID Frequency Bands

| Band | Frequency | Range | Standards | Common cards/tags |
|---|---|---|---|---|
| LF (Low Frequency) | 125–134 kHz | <10 cm | EM4100, HID Prox, T5577, HITAG | Access cards, animal tags, car immobilizers |
| HF (High Frequency) | 13.56 MHz | <1 m | ISO 14443A/B, ISO 15693, NFC | Mifare, DESFire, NTAG, passports, payment cards |
| UHF | 860–960 MHz | <12 m | EPC Gen2, ISO 18000-6C | Supply chain, inventory, toll systems |

### 5.2 Proxmark3 Operations

The Proxmark3 (Iceman/RRG firmware) is the standard RFID security research tool, supporting LF and HF protocols.

```bash
# Connect to Proxmark3
pm3   # auto-detect
pm3 /dev/ttyACM0   # explicit device

# ---- LF (125 kHz) Operations ----

# Read unknown LF tag
pm3 --> lf search

# Read EM4100 tag
pm3 --> lf em 410x reader

# Clone EM4100 to T5577 writable card
pm3 --> lf em 410x clone --id 0102030405

# Read HID Prox card
pm3 --> lf hid reader

# Clone HID Prox to T5577
pm3 --> lf hid clone -r 2006ec0c86

# Brute-force HID facility code
pm3 --> lf hid brute -f 1 -t 255 --fc 101

# ---- HF (13.56 MHz) Operations ----

# Read unknown HF tag
pm3 --> hf search

# Read Mifare Classic 1K UID
pm3 --> hf mf info

# Dump all sectors of Mifare Classic (requires known keys or attack)
pm3 --> hf mf autopwn
# autopwn attempts: default keys → darkside → nested → hardnested
```

### 5.3 Mifare Classic Attacks

Mifare Classic uses the proprietary Crypto-1 stream cipher (48-bit key). Multiple attacks exist:

#### Darkside Attack (MFOC)

Exploits a weakness in Crypto-1's PRNG — recovers one sector key from a single card interaction without any known keys.

```bash
pm3 --> hf mf darkside
# Recovers key for one sector
# Typical time: 5-30 seconds
```

#### Nested Attack

Once one sector key is known, the nested attack exploits the weak PRNG to recover remaining sector keys.

```bash
# Nested attack (requires at least one known key)
pm3 --> hf mf nested --1k --blk 0 -a -k FFFFFFFFFFFF
# Recovers keys for all remaining sectors
# Typical time: 10-60 seconds per sector
```

#### Hardnested Attack

For cards with hardened PRNG (fixed nonce / encrypted nonce), the hardnested attack uses statistical analysis of encrypted nonces to recover keys.

```bash
# Hardnested attack
pm3 --> hf mf hardnested --blk 0 -a -k FFFFFFFFFFFF --tblk 4 --ta
# --blk 0 -a -k = known key for block 0, key A
# --tblk 4 --ta = target block 4, key A
# Requires 2-15 minutes depending on card variant
```

#### Full Card Clone

```bash
# Dump all data after key recovery
pm3 --> hf mf dump

# Write dump to blank Mifare Classic card (UID-writable "magic" card)
pm3 --> hf mf restore

# Clone UID (requires Gen1a/Gen2 magic card)
pm3 --> hf mf csetuid --uid 01020304
```

### 5.4 NFC / NDEF

NDEF (NFC Data Exchange Format) structures data on NFC tags (NTAG213/215/216, Mifare Ultralight).

```bash
# Read NDEF records
pm3 --> hf mfu info
pm3 --> hf mfu dump

# Write NDEF URI record to NTAG215
pm3 --> hf mfu wrbl -b 4 -d <NDEF_payload_hex>

# NFC phone-based tools: NFC TagInfo (Android), NXP TagWriter
```

**NDEF attack vectors:** malicious URI records (phishing), crafted NDEF messages triggering parser vulnerabilities in NFC-enabled devices, relay attacks (NFCGate for Android).

### 5.5 Mifare DESFire

DESFire uses AES-128 or 3DES with mutual authentication. Significantly stronger than Mifare Classic. No known practical cryptographic attacks against current DESFire EV2/EV3 implementations. Attack surface limited to implementation flaws, side-channel attacks on specific hardware, and relay/proxy attacks.

```bash
# Read DESFire tag info
pm3 --> hf mfdes info

# List applications
pm3 --> hf mfdes lsapp

# Authenticate (requires key)
pm3 --> hf mfdes auth -n 0 -t aes -k 00000000000000000000000000000000
```

---

## 6. Bluetooth

### 6.1 Bluetooth Classic (BR/EDR)

Bluetooth Classic operates in the 2.4 GHz ISM band (2402–2480 MHz) using 79 channels with adaptive frequency hopping (AFH) at 1600 hops/second.

**Ubertooth One** — an open-source 2.4 GHz platform designed for Bluetooth monitoring:

```bash
# Capture Bluetooth packets (requires Ubertooth One)
ubertooth-btle -f -c /tmp/ble_pipe
# -f = follow connections

# Spectrum analysis (2.4 GHz band)
ubertooth-specan
# Outputs real-time spectrum data; pipe to ubertooth-specan-ui for visualization

# Capture BR/EDR (limited — AFH makes full capture difficult without CLK)
ubertooth-btbb -l -c /tmp/btbb_pipe

# Determine Bluetooth clock of a target device
ubertooth-btbb -t AA:BB:CC:DD:EE:FF
```

### 6.2 BLE (Bluetooth Low Energy)

BLE uses 40 channels (3 advertising channels: 37, 38, 39; 37 data channels) with simplified frequency hopping.

```bash
# BLE scanning (Linux, built-in)
sudo hcitool lescan
sudo bluetoothctl
[bluetooth]# scan on

# BLE GATT enumeration
# gatttool (deprecated but functional)
gatttool -b AA:BB:CC:DD:EE:FF --primary    # List primary services
gatttool -b AA:BB:CC:DD:EE:FF --char-desc  # List characteristics
gatttool -b AA:BB:CC:DD:EE:FF --char-read -a 0x000e  # Read characteristic

# bettercap — BLE enumeration and attack
sudo bettercap
> ble.recon on
> ble.enum AA:BB:CC:DD:EE:FF
> ble.write AA:BB:CC:DD:EE:FF <service_uuid> <char_uuid> <hex_value>
```

**GATT (Generic Attribute Profile) attack surface:**
- Unauthenticated read/write on sensitive characteristics (unlock commands, firmware update)
- Characteristic value fuzzing
- Notification/indication flooding
- Service spoofing

### 6.3 Bluetooth Vulnerabilities

#### KNOB Attack (Key Negotiation of Bluetooth)

CVE-2019-9506. Exploits the entropy negotiation in Bluetooth BR/EDR pairing. The attacker forces both devices to agree on a 1-byte encryption key, then brute-forces it in real-time. Affects all Bluetooth BR/EDR devices up to Bluetooth 5.0.

**Mechanism:** during link key negotiation, the attacker injects messages to set the encryption key entropy to the minimum (1 byte = 8 bits). The resulting key is brute-forceable in <1 second. The attacker then decrypts the session.

**Mitigation:** enforce minimum key entropy (7 bytes); patched in Bluetooth Core Spec 5.1+ errata.

#### BLURtooth (BLUR)

CVE-2020-15802. Cross-transport key derivation (CTKD) vulnerability. An attacker paired over BLE can derive the BR/EDR link key (or vice versa), gaining access to profiles on the other transport without pairing. Affects dual-mode devices supporting CTKD.

**Mitigation:** restrict CTKD to authenticated pairings; enforce Secure Connections Only mode.

#### BrakTooth

A family of 16 vulnerabilities in commercial Bluetooth Classic (BR/EDR) stacks, discovered in 2021. Affects Qualcomm, Intel, Texas Instruments, and other chipsets. Impacts include:

- **Denial of service** — crash or freeze the Bluetooth firmware
- **Remote code execution** — on some chipsets (ESP32, certain Qualcomm)
- **Deadlock** — infinite loop in LMP (Link Manager Protocol) handling

**Tool:** BrakTooth PoC exploit framework (requires ESP32 development board as the attack platform).

**Mitigation:** vendor firmware updates; disable Bluetooth when not in use; monitor for unexpected LMP sequences.

#### BLESA (BLE Spoofing Attack)

Exploits the reconnection procedure in BLE. After a legitimate connection drops, the attacker spoofs the peripheral and reconnects to the central without re-authentication (exploiting implementations that skip authentication on reconnection).

### 6.4 Bluetooth Defensive Monitoring

```bash
# Monitor Bluetooth activity with btmon
sudo btmon
# Captures HCI (Host Controller Interface) traffic — all Bluetooth events

# Detect BLE advertisements in proximity
sudo hcitool lescan --duplicates | tee ble_scan.log

# Identify rogue BLE peripherals
# Cross-reference discovered BLE devices against known-good inventory
# Alert on new/unknown device UUIDs or MAC address anomalies
```

---

## 7. Zigbee (IEEE 802.15.4)

### 7.1 Protocol Overview

Zigbee operates on IEEE 802.15.4 at 2.4 GHz (16 channels, ch. 11–26) and 868/915 MHz. Uses DSSS modulation, 250 kbps data rate at 2.4 GHz. Mesh network topology with coordinator, routers, and end devices.

**Security layers:**
- **Network layer** — AES-128-CCM encryption with a network key (shared by all devices in the network)
- **Application layer** — optional link keys (per-device-pair AES-128 keys)
- **Trust Center** — the coordinator manages key distribution

**Weakness:** the network key is often transmitted in the clear during device joining (the "transport key" vulnerability). An attacker sniffing during the join procedure captures the network key, enabling decryption of all subsequent traffic.

### 7.2 KillerBee / ApiMote

KillerBee is a framework for IEEE 802.15.4 / Zigbee security research. ApiMote is a purpose-built IEEE 802.15.4 transceiver for use with KillerBee. Alternatively, TI CC2531 USB dongles (with custom firmware) can be used.

```bash
# Install KillerBee
pip install killerbee

# Scan for Zigbee networks (all 2.4 GHz channels)
zbstumbler

# Capture packets on channel 15
zbdump -c 15 -w zigbee_capture.pcap

# Replay captured packets
zbreplay -c 15 -r zigbee_capture.pcap

# Inject crafted IEEE 802.15.4 frames
zbinjection -c 15 -p <hex_payload>

# Decrypt Zigbee traffic (requires known network key)
zbdecrypt -k <network_key_hex> -r zigbee_capture.pcap -w decrypted.pcap
# View in Wireshark with Zigbee dissector

# OTA key sniffing during device join
zbdump -c 15 -w join_capture.pcap
# Then search for Transport Key frame in Wireshark:
# Filter: zbee_aps.cmd.id == 0x05
# The network key is in the payload if transmitted unencrypted
```

### 7.3 Zigbee Attack Vectors

- **Key sniffing during join** — capture the transport key frame when a new device joins; network key transmitted in plaintext on default-security-level networks
- **Replay attacks** — replay captured frames (Zigbee uses frame counters, but some implementations don't validate monotonicity)
- **Network key extraction from devices** — extract the key from flash memory of a captured Zigbee end device (JTAG/SWD debug interfaces often left enabled)
- **Touchlink commissioning abuse** — Zigbee Light Link (ZLL) touchlink can be exploited to steal devices from their network by issuing a factory reset via touchlink from close range
- **Insecure rejoin** — devices that rejoin without re-authentication can be impersonated

**Mitigation:** install-code-based key exchange (key not sent OTA in plaintext), disable default trust center link key, use Zigbee 3.0 security enhancements, disable touchlink on production devices, validate frame counters strictly.

---

## 8. Satellite Communications

### 8.1 Weather Satellite Reception

NOAA polar-orbiting satellites (NOAA 15, 18, 19) transmit APT (Automatic Picture Transmission) at 137 MHz using FM-modulated analog imagery.

```bash
# Receive NOAA APT with RTL-SDR
# NOAA 18: 137.9125 MHz
rtl_fm -f 137912500 -s 48000 -g 40 -p 0 -E dc -A fast - | sox -t raw -r 48000 -e signed -b 16 -c 1 - noaa18_pass.wav

# Decode APT image
# Use noaa-apt or WXtoImg
noaa-apt noaa18_pass.wav -o noaa18_image.png

# Track satellite passes with predict or gpredict
gpredict   # GUI satellite tracker with pass prediction
```

**Meteor-M satellites** transmit LRPT (Low Rate Picture Transmission) at 137.1 or 137.9 MHz using QPSK modulation. Higher resolution than APT but requires QPSK demodulation.

```bash
# Capture Meteor-M2 LRPT
rtl_sdr -f 137100000 -s 288000 -g 40 meteor_m2.iq

# Demodulate with meteor_demod (from meteor-decoder)
meteor_demod -B -s 288000 meteor_m2.iq meteor_m2.s

# Decode to image
medet meteor_m2.s meteor_m2_image -cd
```

### 8.2 Amateur Satellite Communications

Amateur radio satellites (AMSAT) operate on VHF/UHF (144/430 MHz) and higher bands. Linear transponders relay analog signals; digipeaters relay digital packets.

```bash
# ISS APRS digipeater (145.825 MHz)
rtl_fm -f 145825000 -s 22050 -g 40 - | direwolf -r 22050 -
# direwolf decodes APRS packets relayed through the ISS
```

### 8.3 Satellite Security Considerations

- **Unencrypted downlinks** — many satellite signals (weather, ADS-B relay, AIS relay, some military UHF SATCOM) are transmitted in the clear and receivable with consumer SDR
- **Uplink security** — satellite command and control channels are typically encrypted and authenticated; unauthorized uplink access is a federal/international crime
- **VSAT terminals** — exposed to eavesdropping (DVB-S downlinks are often unencrypted); terminal firmware vulnerabilities enable remote compromise
- **Iridium** — pager traffic decodable with `iridium-toolkit` and RTL-SDR; voice calls use proprietary encryption (broken in research)

---

## 9. Wireless Alarm Systems

### 9.1 Protocol Characteristics

Consumer wireless alarm systems typically operate at 315 MHz (US) or 433/868 MHz (EU). Sensors (door/window contacts, PIR motion detectors) communicate with the base station using simple OOK/ASK or FSK modulation with fixed or weakly-secured codes.

### 9.2 Attack Methodology

```bash
# Step 1: Identify alarm frequency and modulation
rtl_433 -g 40 -f 433920000
# Trigger the sensor (open door/window) and observe decoded output
# rtl_433 identifies many consumer alarm protocols automatically

# Step 2: Capture the sensor transmission
hackrf_transfer -r alarm_sensor.iq -f 433920000 -s 2000000 -l 32 -g 20

# Step 3: Analyze in URH or inspectrum
urh   # open alarm_sensor.iq, identify modulation, extract bits

# Step 4: Replay attack
hackrf_transfer -t alarm_sensor.iq -f 433920000 -s 2000000 -x 40
# If the alarm uses fixed codes, replaying the "all clear" signal
# after jamming the alarm signal can suppress alerts

# Step 5: Jamming attack
# Jam the alarm frequency during intrusion — the base station
# cannot receive sensor alerts
hackrf_transfer -t noise.iq -f 433920000 -s 2000000 -x 47 -R
```

### 9.3 Alarm Protocol Security Assessment

| Security level | Characteristics | Vulnerability |
|---|---|---|
| None | Fixed code, no encryption, no tamper detection | Full replay, jam + intrude |
| Low | Rolling code or obfuscation, no encryption | RollJam, protocol analysis |
| Medium | Encrypted payload, supervision (heartbeat) | Jam detection, but still susceptible to sophisticated attacks |
| High | AES encryption, bidirectional, anti-jam, tamper alerts | Requires key extraction or implementation flaws |

**Defense indicators for alarm systems:**
- **Supervision / heartbeat** — base station alerts if sensor check-in is missed (detects jamming)
- **Bidirectional communication** — base station acknowledges sensor messages; missing ACK triggers alert
- **Anti-jam detection** — base station monitors RF noise floor; sustained elevation triggers alarm
- **Encrypted rolling codes** — prevents replay and protocol analysis
- **Tamper switches** — sensor alerts on physical case opening

---

## 10. RF Jamming — Detection and Countermeasures

### 10.1 Jamming Detection

#### Spectrum Monitoring

Dedicated spectrum analyzers or SDR receivers continuously monitor the target frequency bands. Detection criteria:

- **Persistent elevated noise floor** — noise power consistently above baseline by >10 dB
- **Bandwidth analysis** — broadband jamming covers the entire band; narrowband jamming targets specific channels
- **Signal characteristics** — continuous wave (CW) jammer produces a single tone; noise jammer produces wideband energy; deceptive jammer mimics protocol structure

```bash
# Continuous spectrum monitoring with rtl_power
rtl_power -f 430M:440M:5k -g 40 -i 1 -e 0 monitor.csv
# -e 0 = continuous monitoring (no end time)
# Analyze monitor.csv for sustained power anomalies

# Real-time monitoring with osmocom_fft
osmocom_fft -a rtl=0 -f 433.92e6 -s 2.048e6 --averaging
```

#### Direction Finding

Locate the jammer using triangulation from multiple receiver positions:

- **TDOA (Time Difference of Arrival)** — measure signal arrival time at multiple synchronized receivers; compute hyperbolic position fix
- **RSS (Received Signal Strength)** — measure signal power at multiple locations; triangulate based on power gradient
- **Rotating directional antenna** — manually sweep a Yagi or log-periodic antenna to determine bearing to jammer; combine bearings from multiple positions

### 10.2 Frequency Hopping Spread Spectrum (FHSS)

FHSS rapidly switches the carrier frequency across a wide band according to a pseudo-random sequence known to both transmitter and receiver. A narrowband jammer can only disrupt one hop at a time; the protocol recovers on subsequent hops.

**Parameters affecting jamming resistance:**
- **Hop rate** — faster hopping (>1000 hops/sec) reduces the jammer's dwell time on any frequency
- **Hop bandwidth** — wider total bandwidth forces the jammer to spread energy across more spectrum
- **Hop sequence unpredictability** — cryptographically generated sequences prevent the jammer from predicting the next hop

### 10.3 Direct Sequence Spread Spectrum (DSSS)

DSSS multiplies the signal with a high-rate pseudo-random spreading code, spreading it across a wide bandwidth. The receiver correlates with the same code to recover the signal. The processing gain (ratio of spread bandwidth to signal bandwidth) provides inherent jamming resistance.

**Processing gain** = 10 * log10(chip_rate / data_rate) dB. A system with 10 Mchip/s spreading and 100 kbps data rate has 20 dB processing gain — the jammer must be 20 dB stronger than the signal to be effective.

---

## 11. RF Shielding and TEMPEST

### 11.1 Electromagnetic Emanation Security

Electronic devices emit unintentional electromagnetic radiation that can carry information. TEMPEST (a US DoD codename) refers to the study and control of these compromising emanations.

**Emanation attack types:**
- **Display emanation** — CRT and LCD video signals radiate at frequencies corresponding to pixel clock rates; an attacker can reconstruct the screen image from received emanations (Van Eck phreaking)
- **Keyboard emanation** — keystroke timing and electromagnetic signatures from keyboard cables/electronics leak keypress data
- **CPU/memory emanation** — data bus activity produces EM signatures correlated with processed data
- **Power line emanation** — data-correlated signals couple onto AC power lines and can be received remotely

**Distance:** compromising emanations are typically receivable at 10–100 meters with directional antennas and SDR, depending on equipment sensitivity, shielding quality, and ambient noise.

### 11.2 Faraday Cage / Shielded Enclosure

A Faraday cage attenuates electromagnetic fields by forming a conductive enclosure. Effectiveness depends on:

| Parameter | Requirement |
|---|---|
| Material | Copper mesh/sheet, steel, aluminum (copper preferred for HF) |
| Mesh aperture | < lambda/20 at highest frequency of concern (e.g., <1.5 cm for 1 GHz) |
| Seam treatment | Continuous welding or conductive gaskets (EMI gaskets) at all joints |
| Door seals | Finger-stock or knife-edge contacts with conductive gaskets |
| Penetrations | Filtered or waveguide-beyond-cutoff for all cables, pipes, ventilation |
| Grounding | Single-point ground to building ground system |
| Attenuation target | NSA/CSS EPL-listed: 100 dB at 10 GHz for TEMPEST Zone A |

**Shielding effectiveness testing:**
- MIL-STD-188-125 (HEMP shielding)
- IEEE 299 (shielded enclosure measurement)
- NSA 94-106 (TEMPEST shielding)

### 11.3 TEMPEST Countermeasures

| Measure | Application |
|---|---|
| Zone control | TEMPEST Zone A (0–20m) requires full shielding; Zone B (20–100m) requires controlled access |
| Filtered power | Power line filters block data-correlated signals from leaving the shielded area |
| Fiber optics | Replace copper data cables with fiber at the shielded boundary — no EM emanation |
| Font countermeasures | TEMPEST-resistant fonts add noise to character rendering to defeat display emanation recovery |
| Red/black separation | Classified (red) and unclassified (black) equipment physically separated and on separate power circuits |
| Noise generation | Broadband RF noise generators mask compromising emanations |
| TEMPEST-rated equipment | NSA TEMPEST-approved hardware (NATO SDIP-27 Level A/B/C) has built-in emanation suppression |

### 11.4 Practical RF Shielding for Labs

For SDR testing labs and RF research environments:

```text
# Minimum shielding for preventing unintentional TX leakage during testing:
# 1. Conduct all TX testing inside a shielded enclosure or use direct
#    cable connection (SMA cable from SDR TX to target device RX)
#    with appropriate attenuators to avoid damaging the receiver.

# Attenuator chain for direct cable testing:
# HackRF TX (max +15 dBm) → 30 dB attenuator → 20 dB attenuator → target RX
# Adjust attenuators to keep received power at target's expected input level

# 2. For over-the-air testing: use a shielded box (e.g., Ramsey STE-2200)
#    or a screen room rated for the frequency range under test.

# 3. Legal compliance: never transmit on frequencies you are not licensed
#    for outside a shielded enclosure. ISM band power limits apply even in
#    lab environments when not shielded.
```

---

## 12. RF Fingerprinting and Anomaly Detection

### 12.1 RF Fingerprinting

Every transmitter has unique hardware imperfections (oscillator drift, IQ imbalance, power amplifier nonlinearity, phase noise profile) that produce a distinctive "fingerprint" in the transmitted signal. RF fingerprinting identifies specific transmitter hardware from these characteristics.

**Applications:**
- **Device authentication** — verify that a transmitter is the expected device (detect cloned/spoofed transmitters)
- **ADS-B verification** — distinguish legitimate aircraft transponders from spoofing equipment
- **Rogue device detection** — identify unauthorized transmitters on a network
- **Forensic attribution** — link intercepted transmissions to specific hardware

**Techniques:**
1. **Transient analysis** — capture the turn-on transient (first microseconds of transmission); unique power-up signature per device
2. **Steady-state analysis** — IQ imbalance, carrier frequency offset, EVM (Error Vector Magnitude) characterize the transmitter
3. **ML-based classification** — train a CNN/LSTM on IQ samples from known devices; classify unknown transmissions by fingerprint similarity

### 12.2 Spectrum Anomaly Detection

Automated detection of unexpected RF activity in a monitored environment:

```bash
# Baseline spectrum measurement
rtl_power -f 1M:2000M:100k -g 40 -i 60 -e 24h baseline.csv

# Compare ongoing measurements against baseline
# Flag frequencies where measured power exceeds baseline by >threshold
# Python analysis:
python3 -c "
import pandas as pd
import numpy as np
baseline = pd.read_csv('baseline.csv', header=None)
current = pd.read_csv('current.csv', header=None)
# Compare power levels per frequency bin
# Alert on anomalies exceeding 15 dB above baseline
"
```

**Detection targets:**
- Unauthorized transmitters (rogue access points, covert bugs, illicit radios)
- Jamming activity (broadband or narrowband power anomalies)
- Spoofing (GPS, ADS-B, AIS — transmissions from unexpected directions or with unusual signal characteristics)
- Frequency-hopping signals (appear as periodic bursts across the spectrum)

---

## 13. Legal and Regulatory Framework

**Receiving** RF signals is legal in most jurisdictions (passive monitoring). **Transmitting** is regulated:

| Activity | Legal status |
|---|---|
| Passive reception (RTL-SDR) | Generally legal |
| Transmitting on ISM bands (low power) | Legal within power limits (FCC Part 15, ETSI EN 300 220) |
| Transmitting on licensed frequencies | Requires license (amateur radio, commercial) |
| GPS/ADS-B/AIS spoofing | Illegal (18 U.S.C. 32, ICAO Annex 10, ITU Radio Regulations) |
| Jamming | Illegal in virtually all jurisdictions (47 U.S.C. 333 in US) |
| IMSI catching / rogue BTS | Illegal without law enforcement authorization |
| Decrypting encrypted comms | Jurisdiction-dependent (ECPA in US, RIPA in UK) |

All offensive RF testing must operate under explicit written authorization with defined scope, frequencies, power levels, geographic boundaries, and time windows. Shielded enclosures eliminate regulatory risk for lab-based research.

---

## 14. GNU Radio Pipeline Engineering

### 14.1 Flowgraph Design Methodology

GNU Radio flowgraphs follow a dataflow programming model: samples flow from sources through processing blocks to sinks. Each block runs in its own thread (or shares a thread group), communicating through circular buffers. Designing robust pipelines requires attention to sample rate consistency, buffer dimensioning, and block interconnection semantics.

**Block port types and their implications:**

| Port type | Data format | Use case |
|---|---|---|
| `complex` (gr_complex / np.complex64) | 32-bit float I + 32-bit float Q | RF signals, baseband processing |
| `float` (np.float32) | 32-bit float | Demodulated audio, magnitude, phase |
| `int` / `short` / `byte` | Integer types | Decoded bits, symbols, packed bytes |
| `message` | PMT (Polymorphic Type) | Asynchronous control, decoded packets, metadata |

**Sample rate propagation:** every block that changes the sample rate (decimators, interpolators, resamplers) must maintain a consistent relationship between input and output rates. A decimation-by-N block consumes N input samples for every 1 output sample. The flowgraph will silently produce garbage if sample rates are inconsistent — GNU Radio does not enforce rate correctness at design time.

**GRC flowgraph design workflow:**

```bash
# Launch GNU Radio Companion
gnuradio-companion &

# GRC generates Python code from the graphical flowgraph
# The generated .py file is a standard GNU Radio top_block subclass
# GRC flowgraphs are saved as .grc (XML/YAML) files

# Run a GRC-generated flowgraph directly:
python3 my_flowgraph.py

# Convert .grc to .py without opening the GUI:
grcc my_flowgraph.grc -o output_directory/
```

### 14.2 Key Signal Processing Blocks

**Source blocks** interface with SDR hardware or files:

```python
# Hardware sources via gr-osmosdr (see section 1.3)
# File sources for offline analysis:
from gnuradio import blocks

file_src = blocks.file_source(gr.sizeof_gr_complex, "capture.fc32", repeat=False)
# gr.sizeof_gr_complex = 8 bytes (two float32 values)

# Throttle block prevents file sources from consuming CPU at 100%
# Required when no hardware source/sink provides timing
throttle = blocks.throttle(gr.sizeof_gr_complex, samp_rate)
```

**Filter blocks** — the workhorses of signal isolation:

```python
from gnuradio import filter as grfilter
from gnuradio.filter import firdes

# Low-pass FIR filter (isolate signal within bandwidth)
lpf_taps = firdes.low_pass(
    gain=1.0,
    sampling_freq=samp_rate,
    cutoff_freq=12500,       # passband edge
    transition_width=3000,   # transition band
    window=firdes.WIN_HAMMING
)
lpf = grfilter.fir_filter_ccf(1, lpf_taps)  # 1 = no decimation

# Band-pass filter (isolate a signal offset from center)
bpf_taps = firdes.band_pass(
    gain=1.0,
    sampling_freq=samp_rate,
    low_cutoff_freq=50000,
    high_cutoff_freq=75000,
    transition_width=5000,
    window=firdes.WIN_HAMMING
)
bpf = grfilter.fir_filter_ccf(1, bpf_taps)

# Frequency-translating FIR filter (shift + filter in one block)
# Shifts a signal at offset_freq to baseband while filtering
xlating_fir = grfilter.freq_xlating_fir_filter_ccf(
    decimation=int(samp_rate / channel_rate),
    taps=firdes.low_pass(1, samp_rate, channel_rate/2, channel_rate/10),
    center_freq=offset_freq,
    sampling_freq=samp_rate
)
```

**Resampling blocks:**

```python
from gnuradio import filter as grfilter

# Rational resampler — change sample rate by interpolation/decimation ratio
# Output rate = input_rate * interpolation / decimation
resampler = grfilter.rational_resampler_ccf(
    interpolation=48000,
    decimation=int(samp_rate),
    taps=[],           # empty = auto-designed filter
    fractional_bw=0.4  # transition bandwidth as fraction of output rate
)
```

**Demodulation blocks:**

```python
from gnuradio import analog, digital

# FM demodulation (NBFM — narrowband FM for voice, data)
nbfm_demod = analog.nbfm_rx(
    audio_rate=48000,
    quad_rate=48000,
    tau=75e-6,          # de-emphasis time constant (75us US, 50us EU)
    max_dev=5000        # max frequency deviation in Hz
)

# AM demodulation (envelope detection via magnitude)
# Complex input → float magnitude output
am_demod = blocks.complex_to_mag(1)

# FSK demodulation — quadrature demod extracts instantaneous frequency
quad_demod = analog.quadrature_demod_cf(
    gain=samp_rate / (2 * math.pi * fsk_deviation)
)

# ASK/OOK demodulation — magnitude + threshold
# complex_to_mag → binary_slicer
mag = blocks.complex_to_mag(1)
slicer = digital.binary_slicer_fb()  # float in, byte out (0 or 1)
```

**Synchronization blocks:**

```python
from gnuradio import digital

# Clock recovery — Mueller & Mueller (M&M)
# Recovers symbol timing from demodulated signal
clock_recovery = digital.clock_recovery_mm_ff(
    omega=samples_per_symbol,       # nominal samples/symbol
    gain_omega=0.25 * 0.175 * 0.175,  # gain for omega update
    mu=0.5,                         # initial fractional sample offset
    gain_mu=0.175,                  # gain for mu update
    omega_relative_limit=0.005      # max omega deviation
)

# Costas loop PLL (carrier recovery for PSK)
costas = digital.costas_loop_cc(
    loop_bw=2 * math.pi / 100,  # loop bandwidth (radians/sample)
    order=2                       # 2=BPSK, 4=QPSK
)

# Polyphase clock sync (preferred for modern designs)
nfilts = 32
rrc_taps = firdes.root_raised_cosine(nfilts, nfilts, 1.0/samples_per_symbol,
                                      0.35, 11*samples_per_symbol*nfilts)
pfb_clock = digital.pfb_clock_sync_ccf(
    sps=samples_per_symbol,
    loop_bw=2*math.pi/100,
    taps=rrc_taps,
    filter_size=nfilts,
    init_phase=nfilts/2,
    max_rate_deviation=1.5,
    osps=1
)
```

### 14.3 Custom OOT Module Development — C++ Block Implementation

The Python skeleton from section 1.3 is suitable for prototyping. Production blocks and performance-critical DSP require C++ implementation.

```bash
# Create a new OOT module
gr_modtool newmod rf_security
cd gr-rf_security

# Add a C++ sync block (1 input, 1 output, same rate)
gr_modtool add -t sync -l cpp power_detector
# gr_modtool generates:
#   lib/power_detector_impl.cc   — C++ implementation
#   lib/power_detector_impl.h    — C++ header
#   include/gnuradio/rf_security/power_detector.h — public interface
#   python/rf_security/bindings/power_detector_python.cc — pybind11
#   grc/rf_security_power_detector.block.yml — GRC block descriptor

# Add a C++ general block (arbitrary input/output ratio)
gr_modtool add -t general -l cpp packet_decoder

# Add a block with message ports (for asynchronous PDU handling)
gr_modtool add -t sync -l cpp frame_sync
```

**C++ block implementation example** (`lib/power_detector_impl.cc`):

```cpp
#include "power_detector_impl.h"
#include <gnuradio/io_signature.h>
#include <volk/volk.h>
#include <cstring>

namespace gr {
namespace rf_security {

power_detector::sptr power_detector::make(float threshold_db,
                                           int avg_length)
{
    return gnuradio::make_block_sptr<power_detector_impl>(
        threshold_db, avg_length);
}

power_detector_impl::power_detector_impl(float threshold_db,
                                          int avg_length)
    : gr::sync_block("power_detector",
                     gr::io_signature::make(1, 1, sizeof(gr_complex)),
                     gr::io_signature::make(1, 1, sizeof(float))),
      d_threshold_linear(std::pow(10.0f, threshold_db / 10.0f)),
      d_avg_length(avg_length),
      d_avg_power(0.0f)
{
    // Allocate VOLK-aligned buffer for magnitude squared
    const int alignment = volk_get_alignment();
    d_mag_sq = (float*)volk_malloc(8192 * sizeof(float), alignment);
}

power_detector_impl::~power_detector_impl()
{
    volk_free(d_mag_sq);
}

int power_detector_impl::work(int noutput_items,
                               gr_vector_const_void_star& input_items,
                               gr_vector_void_star& output_items)
{
    auto in = static_cast<const gr_complex*>(input_items[0]);
    auto out = static_cast<float*>(output_items[0]);

    // VOLK-accelerated magnitude squared: |I + jQ|^2 = I^2 + Q^2
    volk_32fc_magnitude_squared_32f(d_mag_sq, in, noutput_items);

    for (int i = 0; i < noutput_items; i++) {
        // Exponential moving average
        d_avg_power = d_avg_power * (1.0f - 1.0f / d_avg_length)
                    + d_mag_sq[i] * (1.0f / d_avg_length);
        out[i] = (d_avg_power > d_threshold_linear) ? 1.0f : 0.0f;
    }
    return noutput_items;
}

} // namespace rf_security
} // namespace gr
```

**Build and install the OOT module:**

```bash
cd gr-rf_security
mkdir build && cd build
cmake -DCMAKE_INSTALL_PREFIX=/usr/local ..
make -j$(nproc)

# Run unit tests (gr_modtool generates test stubs)
ctest --output-on-failure

sudo make install
sudo ldconfig

# Verify the module loads in GNU Radio
python3 -c "import gnuradio.rf_security; print('OOT module loaded')"
```

### 14.4 Example Pipelines

#### ISM Band Scanner (315/433/868/915 MHz)

Scans ISM bands, detects signal presence, and logs frequency, power, and timestamp for each detected transmission.

```python
#!/usr/bin/env python3
"""ISM band scanner — detects and logs RF transmissions across ISM frequencies."""
from gnuradio import gr, blocks, analog, fft
from gnuradio.filter import firdes
import osmosdr
import time
import json
import sys

ISM_BANDS = [
    {"name": "315_MHz", "center": 315e6, "bw": 2e6},
    {"name": "433_MHz", "center": 433.92e6, "bw": 2e6},
    {"name": "868_MHz", "center": 868.3e6, "bw": 2e6},
    {"name": "915_MHz", "center": 915e6, "bw": 2e6},
]

class ISMScanner(gr.top_block):
    def __init__(self, device_args="rtl=0", gain=40, dwell_time=2.0):
        gr.top_block.__init__(self, "ISM Scanner")
        self.samp_rate = 2.048e6
        self.dwell_time = dwell_time

        self.src = osmosdr.source(args=device_args)
        self.src.set_sample_rate(self.samp_rate)
        self.src.set_gain(gain)
        self.src.set_if_gain(20)
        self.src.set_bb_gain(20)

        # Power measurement: complex_to_mag_squared → moving average
        self.mag_sq = blocks.complex_to_mag_squared(1)
        self.avg = blocks.moving_average_ff(int(self.samp_rate * 0.01), 1.0/int(self.samp_rate * 0.01))
        self.probe = blocks.probe_signal_f()

        self.connect(self.src, self.mag_sq, self.avg, self.probe)

    def scan_all_bands(self, output_file="ism_scan.jsonl"):
        self.start()
        with open(output_file, "a") as f:
            for band in ISM_BANDS:
                self.src.set_center_freq(band["center"])
                time.sleep(self.dwell_time)  # dwell on frequency
                power_linear = self.probe.level()
                power_db = 10 * __import__('math').log10(max(power_linear, 1e-12))
                entry = {
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "band": band["name"],
                    "center_mhz": band["center"] / 1e6,
                    "power_dbfs": round(power_db, 2),
                    "detection": power_db > -30  # threshold for signal presence
                }
                f.write(json.dumps(entry) + "\n")
                if entry["detection"]:
                    print(f"[DETECT] {band['name']}: {power_db:.1f} dBFS")
        self.stop()
        self.wait()

if __name__ == "__main__":
    scanner = ISMScanner()
    while True:
        scanner.scan_all_bands()
        time.sleep(5)
```

#### ADS-B Decoder Pipeline

A complete GNU Radio flowgraph for 1090 MHz Mode S / ADS-B reception and decoding:

```python
#!/usr/bin/env python3
"""ADS-B Mode S decoder — GNU Radio pipeline for 1090 MHz Extended Squitter."""
from gnuradio import gr, blocks, analog, filter as grfilter
from gnuradio.filter import firdes
import osmosdr
import numpy as np

class ADSBReceiver(gr.top_block):
    def __init__(self):
        gr.top_block.__init__(self, "ADS-B Receiver")
        samp_rate = 2.0e6  # 2 MS/s — matches Mode S pulse timing

        # Source: tune to 1090 MHz
        self.src = osmosdr.source(args="rtl=0")
        self.src.set_sample_rate(samp_rate)
        self.src.set_center_freq(1090e6)
        self.src.set_gain(49.6)  # max gain for weak aircraft signals
        self.src.set_if_gain(0)

        # AM demodulation (Mode S uses pulse position modulation on amplitude)
        self.mag = blocks.complex_to_mag_squared(1)

        # Preamble detection and frame extraction
        # Mode S preamble: 8 us (16 samples at 2 MS/s)
        # Pattern: 1010000101000000 (at 1 sample/0.5us)
        self.file_sink = blocks.file_sink(gr.sizeof_float, "adsb_mag.f32")
        self.file_sink.set_unbuffered(False)

        self.connect(self.src, self.mag, self.file_sink)

if __name__ == "__main__":
    tb = ADSBReceiver()
    tb.start()
    print("Receiving ADS-B on 1090 MHz... Ctrl+C to stop")
    try:
        input()
    except (KeyboardInterrupt, EOFError):
        pass
    tb.stop()
    tb.wait()
    # Post-process with dump1090 or gr-adsb for frame decoding
```

For production ADS-B decoding, use `gr-adsb` (GNU Radio OOT module) or pipe captured IQ directly to `dump1090`:

```bash
# Pipe RTL-SDR IQ samples to dump1090 for real-time decode
rtl_sdr -f 1090000000 -s 2000000 -g 49.6 - | dump1090 --ifile - --iformat UInt8 --interactive
```

#### POCSAG Pager Decoder

POCSAG (Post Office Code Standardization Advisory Group) paging operates at 148–174 MHz (VHF) or 450–470 MHz (UHF), using 2-FSK modulation at 512, 1200, or 2400 baud.

```bash
# Real-time POCSAG decode with multimon-ng and RTL-SDR
# Frequency varies by region — example: 148.8125 MHz
rtl_fm -f 148812500 -s 22050 -g 40 -l 10 - | \
    multimon-ng -t raw -a POCSAG512 -a POCSAG1200 -a POCSAG2400 -f alpha -

# Output format: POCSAG1200: Address: 1234567  Function: 0  Alpha: <message text>

# For logging with timestamps:
rtl_fm -f 148812500 -s 22050 -g 40 - | \
    multimon-ng -t raw -a POCSAG512 -a POCSAG1200 -a POCSAG2400 -f alpha - | \
    while IFS= read -r line; do echo "$(date -u '+%Y-%m-%dT%H:%M:%SZ') $line"; done | \
    tee pocsag_log.txt
```

#### NOAA APT Weather Satellite Receiver (GNU Radio Pipeline)

```python
#!/usr/bin/env python3
"""NOAA APT satellite image receiver — complete GNU Radio pipeline."""
from gnuradio import gr, blocks, analog, filter as grfilter, audio
from gnuradio.filter import firdes
import osmosdr

class NOAAAPTReceiver(gr.top_block):
    def __init__(self, freq=137.9125e6):
        gr.top_block.__init__(self, "NOAA APT Receiver")
        samp_rate = 1.024e6
        audio_rate = 48000
        fm_bw = 34e3       # APT signal bandwidth ~34 kHz

        # Source — NOAA satellites at ~137 MHz
        self.src = osmosdr.source(args="rtl=0")
        self.src.set_sample_rate(samp_rate)
        self.src.set_center_freq(freq)
        self.src.set_gain(40)
        self.src.set_if_gain(20)

        # Low-pass filter to isolate the APT signal
        lpf_taps = firdes.low_pass(1, samp_rate, fm_bw, 5e3,
                                    firdes.WIN_HAMMING)
        self.lpf = grfilter.fir_filter_ccf(1, lpf_taps)

        # FM demodulation (NBFM, ±17 kHz deviation)
        self.fm_demod = analog.nbfm_rx(
            audio_rate=int(samp_rate),
            quad_rate=int(samp_rate),
            tau=0,              # no de-emphasis for data signals
            max_dev=17e3
        )

        # Rational resampler to audio rate
        self.resampler = grfilter.rational_resampler_fff(
            interpolation=48000,
            decimation=int(samp_rate),
            taps=[],
            fractional_bw=0.4
        )

        # Save as WAV for APT decoder (noaa-apt, WXtoImg, SatDump)
        self.wav_sink = blocks.wavfile_sink("noaa_apt_pass.wav",
                                            1, audio_rate,
                                            blocks.FORMAT_WAV,
                                            blocks.FORMAT_PCM_16)

        self.connect(self.src, self.lpf, self.fm_demod,
                     self.resampler, self.wav_sink)

if __name__ == "__main__":
    # NOAA 15: 137.6200 MHz, NOAA 18: 137.9125 MHz, NOAA 19: 137.1000 MHz
    tb = NOAAAPTReceiver(freq=137.9125e6)
    tb.start()
    print("Recording NOAA APT pass... Ctrl+C when satellite pass ends")
    try:
        input()
    except (KeyboardInterrupt, EOFError):
        pass
    tb.stop()
    tb.wait()
    print("Saved to noaa_apt_pass.wav — decode with: noaa-apt noaa_apt_pass.wav -o image.png")
```

### 14.5 Performance Tuning

**VOLK (Vector-Optimized Library of Kernels):** GNU Radio uses VOLK for SIMD-accelerated DSP operations (SSE, AVX, NEON). Run the VOLK profiler once per machine to select optimal kernels:

```bash
# Profile VOLK kernels (run once, takes 5-15 minutes)
volk_profile

# Results saved to ~/.volk/volk_config
# Each kernel maps to the fastest implementation for this CPU

# Verify VOLK is used:
python3 -c "import volk; print(volk.volk_version())"
```

**Buffer size tuning:** GNU Radio's default buffer sizes (32768 items for most blocks) work for typical flowgraphs. Adjust for specific scenarios:

```python
# Increase buffer size for high-throughput blocks
# Set via block method (before start):
self.src.set_max_output_buffer(65536)  # items, not bytes

# Or set globally via environment variable:
# GR_CONF_DEFAULT_MAX_MESSAGES=128
# GR_CONF_BUFFER_SIZE=65536

# For file-based processing, larger buffers reduce disk I/O overhead
self.file_sink.set_max_input_buffer(131072)
```

**Thread affinity and scheduling:**

```bash
# Pin GNU Radio to specific CPU cores (reduce context switching)
taskset -c 0-3 python3 my_flowgraph.py

# Increase scheduling priority for real-time processing
sudo chrt -f 50 python3 my_flowgraph.py

# Monitor GNU Radio thread utilization
# The gr-perf-monitorx tool provides per-block performance metrics
# Available in newer GNU Radio installations
```

**Avoiding common performance pitfalls:**
- Do not use Python blocks in high-sample-rate paths — the GIL limits throughput. Use C++ OOT blocks.
- Avoid unnecessary type conversions (e.g., complex→float→complex chains).
- Use the `Frequency Xlating FIR Filter` instead of separate mixer + filter + decimator — it fuses three operations.
- For multi-channel receivers, use a single wideband capture and channelize in software with a polyphase filter bank, rather than retuning the SDR per channel.

---

## 15. Advanced SDR Hardware Comparison and Configuration

### 15.1 Extended Hardware Comparison Matrix

The table in section 1.1 covers five primary platforms. This section adds hardware not covered there and provides deeper configuration guidance.

| Parameter | RTL-SDR v4 | YARD Stick One | PlutoSDR (ADALM-PLUTO) | KrakenSDR |
|---|---|---|---|---|
| Freq. range | HF–1.766 GHz (direct sampling to 28.8 MHz) | 300–348 / 391–464 / 782–928 MHz | 325 MHz–3.8 GHz (mod: 70 MHz–6 GHz) | 24 MHz–1.766 GHz (5x coherent) |
| Bandwidth | 2.4 MHz (stable) | N/A (packet-based) | 20 MHz | 2.4 MHz per channel |
| ADC bits | 8 | N/A (CC1111 SoC) | 12 | 8 (per channel) |
| TX capable | No | Yes (half-duplex, packet TX) | Yes (full-duplex) | No (RX only) |
| Interface | USB 2.0 | USB 2.0 | USB 2.0 (OTG) | USB 2.0 (5x RTL-SDR) |
| Clock accuracy | 1 ppm (TCXO) | 40 ppm | 25 ppm (mod: TCXO/GPSDO) | 1 ppm (shared TCXO) |
| Price | $35 | $100 | $150–$230 | $300–$500 |
| Key use case | HF reception, wideband scanning | Sub-GHz packet injection (rfcat) | Self-contained TX/RX lab, IIO framework | 5-channel coherent DF, passive radar |

**RTL-SDR v4** adds a built-in upconverter for HF direct sampling (no external upconverter needed for 0–28.8 MHz). The R828D tuner replaces the R820T2 and provides improved sensitivity below 30 MHz. Enable HF mode:

```bash
# RTL-SDR v4 direct sampling mode for HF (0-28.8 MHz)
rtl_sdr -f 7100000 -s 2048000 -g 0 -D 2 hf_capture.iq
# -D 2 = direct sampling on Q input (RTL-SDR v4 HF path)

# In GNU Radio / gr-osmosdr:
# args="rtl=0,direct_samp=2"
```

**YARD Stick One** operates through `rfcat` — a Python framework for packet-level RF interaction on sub-GHz ISM bands. Unlike SDR tools that process raw IQ, rfcat works at the packet layer (the CC1111 handles modulation/demodulation internally):

```bash
# Launch rfcat interactive shell
rfcat -r

# Configure for 433 MHz OOK
>>> d.setFreq(433920000)
>>> d.setMdmModulation(MOD_ASK_OOK)
>>> d.setMdmDRate(4800)       # data rate in bps
>>> d.setMaxPower()           # max TX power (~10 dBm)

# Receive packets
>>> d.RFrecv(timeout=10000)   # returns (data_bytes, metadata)

# Transmit raw bytes
>>> d.RFxmit(b'\xaa\xaa\xaa\x2d\xd4\x01\x02\x03')

# Replay captured packet
>>> data, meta = d.RFrecv(timeout=10000)
>>> d.RFxmit(data)
```

**PlutoSDR (ADALM-PLUTO)** uses the Analog Devices IIO framework and integrates a complete transceiver (AD9363) with an ARM processor running Linux. The firmware can be modified to extend the frequency range from the stock 325 MHz–3.8 GHz to 70 MHz–6 GHz:

```bash
# Stock PlutoSDR — configure via iio_attr
iio_attr -u ip:192.168.2.1 -d ad9361-phy RX_LO frequency 433920000
iio_attr -u ip:192.168.2.1 -d ad9361-phy voltage0 rf_bandwidth 2000000
iio_attr -u ip:192.168.2.1 -d ad9361-phy voltage0 sampling_frequency 2048000

# GNU Radio with PlutoSDR (gr-iio):
# Source: IIO Device Source, device_uri="ip:192.168.2.1"
# Or via gr-osmosdr: args="plutosdr=0"

# Frequency range mod (WARNING: out-of-spec operation, reduced performance)
# SSH into PlutoSDR and edit /etc/libiio.ini or use fw_setenv:
ssh root@192.168.2.1  # password: analog
fw_setenv attr_name compatible
fw_setenv attr_val ad9364  # enables wider freq range
fw_setenv maxcpus            # optional: enable second CPU core
reboot
```

### 15.2 Antenna Selection Guide

| Frequency range | Antenna type | Gain (dBi) | Beamwidth | Application |
|---|---|---|---|---|
| HF (3–30 MHz) | Wire dipole / random wire | 2–5 | Omnidirectional | Shortwave monitoring, HF SIGINT |
| VHF (30–300 MHz) | Discone | 0–3 | Omnidirectional | Wideband scanning (air band, marine, weather sat) |
| VHF (137 MHz) | QFH (Quadrifilar Helix) | 3 | Hemispherical | NOAA/Meteor satellite reception (RHCP) |
| 315/433 MHz | Quarter-wave whip | 2 | Omnidirectional | ISM band monitoring |
| 433 MHz | 3-element Yagi | 7 | ~60° | ISM direction finding |
| 868/915 MHz | Collinear | 5–8 | Omnidirectional | LoRa/Zigbee monitoring |
| 1090 MHz | ADS-B optimized (collinear/ground plane) | 5–8 | Omnidirectional | ADS-B reception |
| 1575 MHz | Active patch (RHCP) | 25+ (with LNA) | Hemispherical | GPS/GNSS reception |
| 2.4 GHz | Patch / panel | 8–14 | 30°–65° | Wi-Fi/BLE direction finding |
| 2.4 GHz | Omnidirectional rubber duck | 2–5 | Omnidirectional | Wi-Fi/BLE scanning |
| Wideband (25 MHz–6 GHz) | Log-periodic | 5–7 | ~60° | General-purpose directional |

**Impedance matching:** all SDR hardware uses 50-ohm SMA/MCX connections. Antenna impedance mismatch causes reflected power and signal loss. The voltage standing wave ratio (VSWR) quantifies mismatch: VSWR < 2:1 is acceptable; VSWR > 3:1 loses >25% of received power. Measure with a NanoVNA:

```bash
# NanoVNA-H4 — measure antenna VSWR at target frequency
# 1. Connect antenna to CH0 port via SMA cable
# 2. Calibrate with SOL (Short-Open-Load) standards
# 3. Set frequency sweep: center=433.92 MHz, span=50 MHz
# 4. Read VSWR at target frequency from the Smith chart display

# NanoVNA-saver (desktop software for NanoVNA)
pip install nanovna-saver
nanovna-saver &
# Connect NanoVNA via USB, set sweep range, read S11/VSWR
```

### 15.3 Clock Accuracy and Calibration

Frequency accuracy is critical for narrowband signal reception. An uncalibrated RTL-SDR with ±28 ppm oscillator drift at 900 MHz is off by ±25 kHz — enough to miss a narrowband ISM signal entirely.

**Kalibrate-RTL** — calibrate RTL-SDR frequency offset using GSM base station signals as a reference:

```bash
# Install kalibrate-rtl
git clone https://github.com/steve-m/kalibrate-rtl.git
cd kalibrate-rtl && ./bootstrap && ./configure && make

# Scan for GSM base stations (known-frequency reference)
./kal -s GSM900 -g 40
# Output: channel 50 (939.0 MHz): power 1234.56, offset -12.345 kHz
# The offset in ppm = (offset_Hz / freq_Hz) * 1e6

# Targeted measurement on strongest channel
./kal -c 50 -g 40
# Output: average absolute error: 14.2 ppm

# Apply correction in rtl_sdr / rtl_fm / GNU Radio:
rtl_sdr -f 433920000 -s 2048000 -g 40 -p 14 capture.iq
# -p 14 = apply +14 ppm correction
```

**GPSDO (GPS-Disciplined Oscillator)** — provides <1 ppb accuracy by locking a TCXO/OCXO to GPS timing signals. USRP B210 supports an external GPSDO via the GPSDO daughterboard. LimeSDR and bladeRF accept external 10 MHz reference input:

```bash
# USRP B210 with internal GPSDO
uhd_usrp_probe --args="type=b200"
# Look for "GPS Detected" in output

# Set USRP clock source to GPSDO
# In GNU Radio: UHD source → clock_source="gpsdo", time_source="gpsdo"

# LimeSDR with external 10 MHz reference
LimeUtil --refclk=10e6
# Or in SoapySDR: args="driver=lime,refclk=10e6"
```

### 15.4 Multi-SDR Coherent Receiver — KrakenSDR Direction Finding

KrakenSDR uses five phase-coherent RTL-SDR receivers sharing a common clock to perform direction finding via interferometry. Each receiver connects to one element of a uniform circular array (UCA) antenna.

```bash
# KrakenSDR software installation
git clone https://github.com/krakenrf/krakensdr_doa.git
cd krakensdr_doa

# The KrakenSDR runs a web-based interface for direction finding
# Configuration: _receiver/kraken_config.ini
# Key parameters:
#   center_freq = 433920000   # target frequency
#   sample_rate = 2048000
#   gain = [40, 40, 40, 40, 40]  # per-channel gain
#   antenna_arrangement = UCA     # Uniform Circular Array
#   array_radius = 0.3            # meters (optimize for wavelength)

# Direction finding algorithms available:
# - MUSIC (MUltiple SIgnal Classification) — high resolution, >2 sources
# - Bartlett beamforming — robust, lower resolution
# - Capon (MVDR) — minimum variance, good for closely spaced sources

# Start the KrakenSDR DAQ and DOA processing
./kraken_doa_start.sh
# Web interface: http://localhost:8080
```

**Applications:** locating rogue transmitters, RF jammers, unauthorized drones, and interference sources. Accuracy depends on array geometry, SNR, and multipath — typical bearing accuracy is ±2°–5° in open environments.

### 15.5 Remote SDR Access

**rtl_tcp** — streams raw IQ samples from a remote RTL-SDR over TCP:

```bash
# Server side (Raspberry Pi with RTL-SDR)
rtl_tcp -a 0.0.0.0 -p 1234 -g 40
# Listens on port 1234, gain 40 dB

# Client side (analysis workstation)
# GQRX: device string "rtl_tcp=192.168.1.100:1234"
# GNU Radio: osmosdr source args="rtl_tcp=192.168.1.100:1234"
```

**SpyServer** — SDR# streaming server with efficient bandwidth usage (streams only the selected bandwidth, not the full sample rate):

```bash
# Server side (Linux)
./spyserver spyserver.config
# Config file specifies: device_type, device_serial, fft_fps, buffer_size

# Client side: SDR# (Windows) → connect to spyserver://hostname:5555
# Or use SoapySpyServer for GNU Radio integration
```

**SoapyRemote** — hardware-agnostic remote SDR access for any SoapySDR-supported device:

```bash
# Server side
SoapySDRServer --bind="0.0.0.0:55132"
# Serves any locally connected SoapySDR device

# Client side (GNU Radio, CubicSDR, etc.)
# args="remote=192.168.1.100:55132,driver=rtlsdr"
# The SoapyRemote driver transparently proxies all API calls
```

---

## 16. RF Detection Engineering

This section covers detection rules and monitoring techniques that complement the Sigma rules and YARA rules in the companion document (Domain 20B §11). The focus here is on Suricata network-layer rules, YARA rules for IQ capture file analysis, USB device monitoring, and automated spectrum anomaly detection with scripted rtl_power pipelines.

### 16.1 Suricata Rules — Network-Layer RF Threat Indicators

SDR devices and RF attack tools generate detectable network traffic patterns: rtl_tcp streams, SoapyRemote sessions, and exfiltration of captured IQ data.

```yaml
# suricata-rf-detection.rules
# Deploy in /etc/suricata/rules/ and include in suricata.yaml

# Rule 1: rtl_tcp IQ streaming detected on network
# rtl_tcp sends a 12-byte dongle info header on connection, starting with "RTL0"
alert tcp any any -> any 1234 (msg:"RF-SDR rtl_tcp IQ stream detected"; \
    flow:established,to_server; \
    content:"|52 54 4C 30|"; offset:0; depth:4; \
    metadata:attack_target rf_monitoring, severity high; \
    classtype:policy-violation; sid:9100001; rev:1;)

# Rule 2: SoapyRemote SDR server communication
# SoapyRemote uses a custom protocol on port 55132
alert tcp any any -> any 55132 (msg:"RF-SDR SoapyRemote server access detected"; \
    flow:established; \
    metadata:attack_target rf_monitoring, severity medium; \
    classtype:policy-violation; sid:9100002; rev:1;)

# Rule 3: Large IQ file transfer (potential exfiltration of RF captures)
# IQ captures at 2 MS/s produce ~16 MB/s of data (complex float32)
# Flag sustained high-bandwidth transfers on common exfil channels
alert tcp $HOME_NET any -> $EXTERNAL_NET any (msg:"RF-SDR potential IQ capture exfiltration - sustained high bandwidth"; \
    flow:established,to_server; \
    dsize:>1400; \
    threshold:type both, track by_src, count 5000, seconds 10; \
    metadata:attack_target rf_exfil, severity medium; \
    classtype:policy-violation; sid:9100003; rev:1;)

# Rule 4: SpyServer streaming protocol detection
# SpyServer uses port 5555 by default with a specific handshake
alert tcp any any -> any 5555 (msg:"RF-SDR SpyServer IQ streaming detected"; \
    flow:established,to_server; \
    metadata:attack_target rf_monitoring, severity medium; \
    classtype:policy-violation; sid:9100004; rev:1;)

# Rule 5: gr-gsm GSMTAP traffic (GSM interception in progress)
# GSMTAP encapsulates decoded GSM frames over UDP port 4729
alert udp any any -> any 4729 (msg:"RF-SDR GSMTAP traffic detected - GSM interception"; \
    content:"|00 02 00 04|"; offset:0; depth:4; \
    metadata:attack_target cellular_intercept, severity critical; \
    classtype:attempted-admin; sid:9100005; rev:1;)
```

### 16.2 YARA Rules — IQ Capture File Signatures

IQ capture files on seized or compromised systems indicate RF surveillance activity. These YARA rules identify capture files by format signatures and metadata patterns.

```yara
rule SigMF_Recording_Metadata {
    meta:
        description = "Detects SigMF metadata files indicating RF signal capture"
        author = "RF Detection Engineering"
        date = "2026-05-13"
        severity = "medium"
        reference = "https://github.com/gnuradio/SigMF"
    strings:
        $sigmf_global = "\"global\"" ascii
        $sigmf_core = "core:datatype" ascii
        $sigmf_freq = "core:frequency" ascii
        $sigmf_rate = "core:sample_rate" ascii
        $sigmf_hw = "core:hw" ascii
        $sigmf_capture = "\"captures\"" ascii
        $sdr_hw1 = "RTL-SDR" ascii nocase
        $sdr_hw2 = "HackRF" ascii nocase
        $sdr_hw3 = "USRP" ascii nocase
        $sdr_hw4 = "LimeSDR" ascii nocase
        $sdr_hw5 = "bladeRF" ascii nocase
    condition:
        filesize < 10MB and
        ($sigmf_global and $sigmf_core and $sigmf_rate) and
        ($sigmf_capture or $sigmf_freq or any of ($sdr_hw*))
}

rule IQ_Raw_Capture_Large {
    meta:
        description = "Detects large raw IQ capture files by extension and binary pattern"
        author = "RF Detection Engineering"
        date = "2026-05-13"
        severity = "low"
        note = "High false-positive rate — correlate with other RF tool artifacts"
    strings:
        // Complex float32 IQ files have no header — detect by file properties
        // Look for files ending in common IQ extensions
        $ext_cfile = ".cfile" ascii
        $ext_fc32 = ".fc32" ascii
        $ext_cs8 = ".cs8" ascii
        $ext_cs16 = ".cs16" ascii
        $ext_cf32 = ".cf32" ascii
        $ext_raw_iq = ".raw" ascii
    condition:
        filesize > 50MB and
        any of ($ext_*)
}

rule URH_Project_File {
    meta:
        description = "Detects Universal Radio Hacker project files indicating RF protocol RE"
        author = "RF Detection Engineering"
        date = "2026-05-13"
        severity = "high"
    strings:
        $urh_xml = "<protocol>" ascii
        $urh_participants = "<participants>" ascii
        $urh_decodings = "<decodings>" ascii
        $urh_modulation = "modulation_type" ascii
        $urh_signal = "<signal " ascii
    condition:
        filesize < 50MB and
        $urh_xml and
        2 of ($urh_participants, $urh_decodings, $urh_modulation, $urh_signal)
}

rule GPS_Spoofing_IQ_Artifacts {
    meta:
        description = "Detects gps-sdr-sim output files used for GPS spoofing attacks"
        author = "RF Detection Engineering"
        date = "2026-05-13"
        severity = "critical"
        reference = "https://github.com/osqzss/gps-sdr-sim"
    strings:
        $gps_sim_src = "gps-sdr-sim" ascii
        $gps_ephem = "brdc" ascii
        $gps_rinex_hdr = "RINEX VERSION" ascii
        $gps_nav = "NAV DATA" ascii
        $gps_loc_pattern = /\-?\d{1,3}\.\d{4,},\-?\d{1,3}\.\d{4,},\d{1,5}/
    condition:
        ($gps_sim_src) or
        ($gps_rinex_hdr and $gps_nav) or
        ($gps_ephem and $gps_loc_pattern and filesize < 100MB)
}
```

### 16.3 USB Device Monitoring — Unauthorized SDR Detection

SDR devices connected to endpoint systems produce identifiable USB device descriptors. Monitor udev events and USB device enumeration to detect unauthorized SDR hardware.

```bash
# Known SDR USB vendor:product IDs
# RTL-SDR:         0bda:2838, 0bda:2832
# HackRF One:      1d50:6089
# YARD Stick One:   1d50:605b
# Ubertooth One:    1d50:6002
# USRP B200/B210:  2500:0020, 2500:0022
# LimeSDR:         1d50:6108
# PlutoSDR:        0456:b673
# bladeRF:         2cf0:5246
# CC2531 (Zigbee): 0451:16ae
# Proxmark3:       9ac4:4b8f, 2d2d:504d

# udev rule to log and optionally block SDR devices
# File: /etc/udev/rules.d/99-sdr-detection.rules
```

```ini
# Log all RTL-SDR connections
ACTION=="add", SUBSYSTEM=="usb", ATTR{idVendor}=="0bda", \
    ATTR{idProduct}=="2838", \
    RUN+="/usr/local/bin/sdr_alert.sh 'RTL-SDR' '%E{ID_SERIAL}' '%E{DEVNAME}'"

# Log HackRF connections (TX-capable — higher severity)
ACTION=="add", SUBSYSTEM=="usb", ATTR{idVendor}=="1d50", \
    ATTR{idProduct}=="6089", \
    RUN+="/usr/local/bin/sdr_alert.sh 'HackRF' '%E{ID_SERIAL}' '%E{DEVNAME}'"

# Log YARD Stick One connections
ACTION=="add", SUBSYSTEM=="usb", ATTR{idVendor}=="1d50", \
    ATTR{idProduct}=="605b", \
    RUN+="/usr/local/bin/sdr_alert.sh 'YardStickOne' '%E{ID_SERIAL}' '%E{DEVNAME}'"

# Log Ubertooth connections
ACTION=="add", SUBSYSTEM=="usb", ATTR{idVendor}=="1d50", \
    ATTR{idProduct}=="6002", \
    RUN+="/usr/local/bin/sdr_alert.sh 'Ubertooth' '%E{ID_SERIAL}' '%E{DEVNAME}'"

# Log Proxmark3 connections
ACTION=="add", SUBSYSTEM=="usb", ATTR{idVendor}=="9ac4", \
    ATTR{idProduct}=="4b8f", \
    RUN+="/usr/local/bin/sdr_alert.sh 'Proxmark3' '%E{ID_SERIAL}' '%E{DEVNAME}'"
```

**Alert script** (`/usr/local/bin/sdr_alert.sh`):

```bash
#!/bin/bash
# sdr_alert.sh — log and alert on SDR device connections
DEVICE_TYPE="$1"
SERIAL="$2"
DEVNAME="$3"
TIMESTAMP=$(date -u '+%Y-%m-%dT%H:%M:%SZ')

# Log to syslog (feeds into SIEM)
logger -p auth.warning -t sdr-detect \
    "SDR_DEVICE_CONNECTED type=${DEVICE_TYPE} serial=${SERIAL} dev=${DEVNAME} ts=${TIMESTAMP}"

# Write structured JSON log
echo "{\"timestamp\":\"${TIMESTAMP}\",\"event\":\"sdr_device_connected\",\"type\":\"${DEVICE_TYPE}\",\"serial\":\"${SERIAL}\",\"device\":\"${DEVNAME}\"}" \
    >> /var/log/sdr-detections.jsonl
```

**Sigma rule for SDR USB device detection** (for SIEM correlation):

```yaml
title: Unauthorized SDR Hardware Connected via USB
id: 2f4a8c10-b7d3-4e91-8f56-a1b2c3d4e5f6
status: experimental
description: >
  Detects USB connection events matching known SDR device vendor and
  product IDs. TX-capable devices (HackRF, YARD Stick One) are elevated
  to critical severity. Correlate with user context and authorization status.
date: 2026/05/13
tags:
  - attack.resource_development
  - attack.t1588.002
logsource:
  category: sdr_detection
  product: udev
detection:
  tx_capable:
    DeviceType|contains:
      - 'HackRF'
      - 'YardStickOne'
      - 'Ubertooth'
  rx_only:
    DeviceType|contains:
      - 'RTL-SDR'
  rfid_tool:
    DeviceType|contains:
      - 'Proxmark3'
  condition: tx_capable OR rx_only OR rfid_tool
falsepositives:
  - Authorized RF security testing personnel
  - Amateur radio operators using SDR as a receiver
level: high
```

**Sigma rule for Zigbee network key sniffing** (KillerBee / zbdump traffic):

Zigbee networks transmit the transport key in cleartext during device association (see §7.2). KillerBee's `zbdump` or Wireshark with the IEEE 802.15.4 dissector exposes these frames via `zbee_aps.cmd.id == 0x05` (APS Transport Key command). This Sigma rule detects log entries from Zigbee monitoring tools or NIDS that flag unencrypted transport key exchange — an indicator of either a misconfigured network or active key sniffing.

```yaml
title: Zigbee Transport Key Transmitted in Cleartext
id: 7c9e1a42-d8f5-4b23-a612-e3f8d7c6b5a9
status: experimental
description: >
  Detects Zigbee APS Transport Key frames (cmd_id 0x05) captured on the
  network, indicating cleartext key distribution during device joining.
  Attackers with an IEEE 802.15.4 sniffer (CC2531 + KillerBee, or
  Ubertooth in 802.15.4 mode) capture these frames to extract the
  network-wide transport key and decrypt all subsequent Zigbee traffic.
  Legitimate joining events should be rare and correlated with authorized
  device provisioning windows.
date: 2026/05/13
references:
  - https://www.zigbee.org/zigbee-for-developers/zigbee-3-0/
  - https://github.com/riverloopsec/killerbee
tags:
  - attack.credential_access
  - attack.t1040
  - attack.t1557
logsource:
  category: zigbee_monitor
  product: killerbee
detection:
  transport_key_frame:
    zbee_aps.cmd.id: 0x05
  nwk_key_type:
    zbee_aps.cmd.key_type|contains:
      - 'Standard Network Key'
      - 'Transport Key'
  killerbee_log:
    EventData|contains:
      - 'zbdump'
      - 'zbreplay'
      - 'zbassocflood'
  wireshark_export:
    EventData|contains:
      - 'ZigBee Application Support'
      - 'APS CMD: Transport Key'
  condition: transport_key_frame OR nwk_key_type OR killerbee_log OR wireshark_export
falsepositives:
  - Authorized Zigbee device provisioning during maintenance windows
  - Zigbee protocol testing in isolated lab environments
level: critical
```

Detection context: when a CC2531 dongle (USB `0451:16ae`, already covered in §16.3 udev rules above) appears alongside Zigbee transport key log events, the combined indicator strongly suggests active Zigbee key sniffing rather than routine device commissioning. Correlate the USB insertion timestamp with the first observed `zbee_aps.cmd.id == 0x05` frame to establish temporal proximity.

### 16.4 Automated Spectrum Anomaly Detection

The `rtl_power` heatmap approach from section 12.2 provides manual analysis. This section automates the pipeline: continuous capture, baseline comparison, and alerting.

```bash
#!/bin/bash
# rf_anomaly_monitor.sh — continuous spectrum monitoring with automated alerting
# Monitors ISM bands (430-440 MHz, 863-870 MHz, 2400-2485 MHz)
# Compares against established baseline, alerts on deviations > threshold

BASELINE_DIR="/var/lib/rf-monitor/baselines"
LOG_DIR="/var/log/rf-monitor"
ALERT_THRESHOLD_DB=15
SCAN_INTERVAL=60  # seconds between scans

mkdir -p "$BASELINE_DIR" "$LOG_DIR"

# Capture baseline (run once during known-clean period)
capture_baseline() {
    local band_name="$1" freq_start="$2" freq_end="$3" bin_size="$4"
    rtl_power -f "${freq_start}:${freq_end}:${bin_size}" \
        -g 40 -i 10 -e 1h \
        "${BASELINE_DIR}/${band_name}_baseline.csv"
}

# Monitor and compare against baseline
monitor_band() {
    local band_name="$1" freq_start="$2" freq_end="$3" bin_size="$4"
    local scan_file="${LOG_DIR}/${band_name}_$(date -u +%Y%m%dT%H%M%SZ).csv"

    rtl_power -f "${freq_start}:${freq_end}:${bin_size}" \
        -g 40 -i 1 -e "${SCAN_INTERVAL}s" \
        "$scan_file"

    # Compare against baseline
    python3 << 'PYEOF'
import csv
import json
import sys
import statistics
from datetime import datetime, timezone

band_name = sys.argv[1] if len(sys.argv) > 1 else "unknown"
baseline_file = f"/var/lib/rf-monitor/baselines/{band_name}_baseline.csv"
scan_file = sys.argv[2] if len(sys.argv) > 2 else ""
threshold_db = 15

baseline_power = {}
try:
    with open(baseline_file) as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 7:
                continue
            freq_start = float(row[2])
            freq_step = float(row[4])
            powers = [float(x) for x in row[6:] if x.strip()]
            for i, pwr in enumerate(powers):
                freq = freq_start + i * freq_step
                baseline_power.setdefault(freq, []).append(pwr)
    for freq in baseline_power:
        baseline_power[freq] = statistics.mean(baseline_power[freq])
except FileNotFoundError:
    print(f"No baseline for {band_name}", file=sys.stderr)
    sys.exit(0)

alerts = []
try:
    with open(scan_file) as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 7:
                continue
            freq_start = float(row[2])
            freq_step = float(row[4])
            powers = [float(x) for x in row[6:] if x.strip()]
            for i, pwr in enumerate(powers):
                freq = freq_start + i * freq_step
                if freq in baseline_power:
                    delta = pwr - baseline_power[freq]
                    if delta > threshold_db:
                        alerts.append({
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "band": band_name,
                            "frequency_mhz": freq / 1e6,
                            "measured_dbm": pwr,
                            "baseline_dbm": baseline_power[freq],
                            "delta_db": round(delta, 1),
                            "severity": "critical" if delta > 25 else "high"
                        })
except FileNotFoundError:
    sys.exit(0)

for alert in alerts:
    print(json.dumps(alert))
PYEOF
}

# Example: monitor 433 MHz ISM band
# capture_baseline "ism433" "430M" "440M" "5k"
# monitor_band "ism433" "430M" "440M" "5k"
```

**Kismet-based wireless IDS deployment architecture:**

```text
Deployment topology for enterprise RF monitoring:

┌─────────────────────────────────────────────────────────┐
│                    SIEM / Elastic                        │
│  (Sigma rules, correlation, dashboards, alerting)       │
└──────────────┬──────────────────────┬───────────────────┘
               │ syslog/webhook       │ REST API
    ┌──────────┴────────┐    ┌────────┴──────────┐
    │ Kismet Server      │    │ rtl_power Monitor │
    │ (central instance) │    │ (spectrum anomaly) │
    │ REST API: :2501    │    │ JSON log output    │
    └──────┬─────────────┘    └──────┬────────────┘
           │ Kismet remote cap        │ local SDR
    ┌──────┴──────────────────────────┴───────────┐
    │        Sensor Network (per-zone)             │
    │  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
    │  │ Sensor 1 │  │ Sensor 2 │  │ Sensor 3 │  │
    │  │ RPi + SDR│  │ RPi + SDR│  │ RPi + SDR│  │
    │  │ Wi-Fi    │  │ BLE+Zigbee│ │ Sub-GHz  │  │
    │  │ adapter  │  │ adapters │  │ RTL-SDR  │  │
    │  └──────────┘  └──────────┘  └──────────┘  │
    └─────────────────────────────────────────────┘
```

```bash
# Kismet remote capture sensor setup (Raspberry Pi)
# Install kismet on sensor node
sudo apt install kismet

# Start as remote capture source (connects back to central Kismet server)
kismet_cap_linux_wifi --connect=central-kismet:3501 \
    --source=wlan1:name=sensor_zone_a,type=linuxwifi

# For RTL-SDR spectrum monitoring on the same sensor
kismet_cap_sdr_rtl433 --connect=central-kismet:3501 \
    --source=rtl433-0:name=ism_sensor_zone_a

# Central Kismet server configuration (kismet.conf)
# Accept remote capture connections:
# server_listen=tcp://0.0.0.0:3501

# Kismet alerting — configure alerts in kismet_alerts.conf:
# APSPOOF — detect AP MAC/SSID mismatch
# BSSTIMESTAMP — detect AP timestamp anomalies (evil twin indicator)
# DEAUTHTOOL — detect deauthentication flood tools
# CHANCHANGE — detect AP unexpected channel change
```

### 16.5 WiFi Pineapple Detection

The WiFi Pineapple (Hak5) is a commonly deployed rogue AP platform. Detection relies on identifying its behavioral fingerprint:

```bash
# WiFi Pineapple detection indicators:
# 1. PineAP karma attack — responds to ALL probe requests
#    Detection: monitor for an AP responding to probes for SSIDs
#    it did not previously advertise

# 2. Management interface fingerprint — default SSID patterns
#    "Pineapple_XXXX", open network on channel 1 or 6

# 3. OUI identification — Hak5 devices use specific MAC OUI ranges
#    and commonly seen Ralink/Mediatek chipset OUIs

# Automated detection with Python + Scapy:
python3 << 'PYEOF'
from scapy.all import *
from collections import defaultdict
import time

# Track probe responses per BSSID
probe_responses = defaultdict(set)
KARMA_THRESHOLD = 10  # respond to >10 different SSIDs = suspicious

def detect_karma(pkt):
    if pkt.haslayer(Dot11ProbeResp):
        bssid = pkt[Dot11].addr2
        ssid = pkt[Dot11Elt].info.decode('utf-8', errors='replace')
        probe_responses[bssid].add(ssid)
        if len(probe_responses[bssid]) > KARMA_THRESHOLD:
            print(f"[ALERT] Potential Karma/PineAP attack from {bssid} "
                  f"- responding to {len(probe_responses[bssid])} SSIDs")

# Requires monitor-mode interface
sniff(iface="wlan0mon", prn=detect_karma, store=0)
PYEOF
```

---

## 17. RF Lab Setup and Calibration

### 17.1 Faraday Cage Construction and Verification

A properly constructed Faraday enclosure is mandatory for any TX-capable RF testing. This section covers construction details beyond the shielding effectiveness requirements discussed in section 11.

**Construction materials and methods:**

| Method | Material | SE at 1 GHz | Cost | Suitability |
|---|---|---|---|---|
| Welded steel panels | 1.5 mm mild steel | 80–100 dB | $$$ | Permanent lab installation |
| Copper foil room | 0.1 mm copper foil on plywood frame | 60–80 dB | $$ | Semi-permanent, excellent HF performance |
| Copper mesh enclosure | #20 copper mesh (0.9 mm aperture) | 50–70 dB | $ | Budget lab, adequate for ISM-band testing |
| Commercial RF enclosure | Varies (Ramsey STE, ETS-Lindgren) | 80–120 dB | $$$$ | Certified performance, minimal construction |

**Construction procedure for copper mesh enclosure:**

1. **Frame construction** — build a rigid frame from 2x4 lumber or aluminum extrusion (80/20). Internal dimensions determine maximum test equipment and antenna separation.
2. **Mesh attachment** — staple copper mesh (#20 or finer) to all six interior faces with 100% overlap at seams. Solder or copper-tape all mesh seam overlaps — gaps wider than lambda/20 at the highest test frequency leak RF.
3. **Door construction** — build a door frame with a continuous copper contact strip (finger stock or beryllium copper spring contact) around the entire perimeter. The door-to-frame contact must maintain <1 mm gap when closed.
4. **Cable penetrations** — install filtered feedthrough connectors (SMA, BNC, or N-type with integrated pi-filter or capacitive feedthrough rated for the frequency range) for every cable crossing the boundary. Alternatively, convert to fiber optic at the boundary.
5. **Power entry** — install a filtered power entry module (IEC 320 inlet with integrated EMI filter, rated for the current draw of all internal equipment).
6. **Ground** — connect the enclosure to building safety ground with a single, short, heavy-gauge conductor. Avoid ground loops.

**Shielding effectiveness verification with NanoVNA and signal generator:**

```bash
# Method: measure insertion loss between TX antenna inside and RX antenna outside

# Equipment needed:
# - NanoVNA-H4 (or better: dedicated signal generator + spectrum analyzer)
# - Two identical antennas (matched to test frequency)
# - SMA cables and adapters

# Procedure using a known signal source:
# 1. Place HackRF inside enclosure, transmit CW at test frequency
hackrf_transfer -t /dev/zero -f 433920000 -s 2000000 -x 20
# (transmitting zeros = CW carrier)

# 2. Measure received power outside enclosure with RTL-SDR + rtl_power
rtl_power -f 433M:435M:1k -g 49.6 -i 10 -e 30 shielding_test.csv

# 3. Repeat with enclosure door open (reference measurement)
# 4. SE = power_door_open (dBm) - power_door_closed (dBm)

# For swept-frequency SE measurement (more thorough):
# Use NanoVNA in S21 mode:
# - Port 1 (TX): inside enclosure via feedthrough
# - Port 2 (RX): outside enclosure
# - Sweep 1 MHz to 3 GHz
# - SE = -S21 at each frequency point

# Minimum acceptable SE for common testing scenarios:
# ISM band testing (433 MHz, +15 dBm TX):  >60 dB
# Cellular testing (700 MHz, +23 dBm TX):  >80 dB
# Wi-Fi testing (2.4 GHz, +20 dBm TX):    >70 dB
```

### 17.2 Test Equipment

**Spectrum analyzer** — measures signal power vs. frequency. For RF security labs, a USB-based spectrum analyzer (TinySA Ultra, 100 kHz–5.3 GHz, ~$130) covers most needs. Professional labs use bench instruments (Rigol DSA815, Siglent SSA3021X, or Keysight N9000B for higher dynamic range).

```bash
# TinySA Ultra — USB-connected spectrum analyzer
# Control via serial interface or tinySA desktop app
# Useful for: verifying shielding effectiveness, measuring TX power,
# confirming frequency accuracy, identifying interference sources

# Signal generator — required for calibration and injection testing
# Affordable options:
# - HackRF One (used as a signal generator with hackrf_transfer or GNU Radio)
# - NanoVNA-H4 (built-in signal generator, limited power)
# - RF Explorer signal generator module

# HackRF as a CW signal generator:
hackrf_transfer -t /dev/zero -f 433920000 -s 2000000 -x 30
# Outputs CW at 433.92 MHz, ~0 dBm with -x 30
```

**Vector Network Analyzer (VNA)** — NanoVNA measures S-parameters (S11 = return loss/VSWR, S21 = insertion loss/gain) for antenna characterization, cable loss measurement, and filter verification:

```bash
# NanoVNA calibration procedure (SOLT: Short-Open-Load-Through)
# 1. Connect calibration standards to Port 1:
#    Short → save S  |  Open → save O  |  Load (50Ω) → save L
# 2. Connect through cable between Port 1 and Port 2:
#    Through → save T
# 3. Apply calibration — reference plane now at cable ends

# Measure antenna S11 (return loss / VSWR):
# Connect antenna to Port 1 via test cable
# Read S11 at target frequency:
#   S11 < -10 dB → VSWR < 1.93 → acceptable match
#   S11 < -15 dB → VSWR < 1.43 → good match
#   S11 < -20 dB → VSWR < 1.22 → excellent match

# Measure cable loss (S21):
# Connect cable under test between Port 1 and Port 2
# S21 reading is the insertion loss (negative dB = loss)
# Typical: RG-316 loses ~1.1 dB/m at 1 GHz, LMR-400 loses ~0.13 dB/m
```

### 17.3 Calibration Procedures

Accurate measurements require calibrated signal paths. Every component in the chain (cable, adapter, attenuator, amplifier) contributes gain or loss.

**Gain/loss characterization of the signal chain:**

```bash
# Measure total system gain/loss from antenna to SDR input
# Signal chain: Antenna → Cable → LNA → Cable → SDR
#
# Step 1: Characterize each component individually with NanoVNA S21
#   Cable 1 (antenna to LNA): S21 = -2.3 dB at 433 MHz
#   LNA:                      S21 = +15.0 dB at 433 MHz
#   Cable 2 (LNA to SDR):    S21 = -1.5 dB at 433 MHz
#
# Step 2: Calculate system gain
#   Total = -2.3 + 15.0 + (-1.5) = +11.2 dB
#
# Step 3: Determine absolute power at SDR input
#   Antenna factor (AF) converts field strength to antenna terminal voltage:
#   P_antenna (dBm) = E (dBuV/m) - AF (dB/m) - cable_loss + LNA_gain
#
# Step 4: Verify with known source
#   Transmit a known-power signal (e.g., HackRF at calibrated output)
#   Measure at SDR input with rtl_power
#   Compare measured vs. expected → difference is system calibration error

# Attenuator verification
# Connect attenuator between NanoVNA ports, measure S21
# A "20 dB" attenuator should read -20.0 ± 0.5 dB
# Label each attenuator with its measured value at key frequencies
```

**RTL-SDR gain calibration:**

```bash
# RTL-SDR gain is not linear — map actual gain vs. reported gain
# Use a calibrated signal source and step through gain settings:
for gain in 0 10 20 30 40 49.6; do
    rtl_power -f 433M:434M:10k -g "$gain" -i 5 -e 10 "gain_${gain}.csv"
done

# Compare measured power at each gain setting against the known source
# Build a gain correction table for accurate power measurements
```

### 17.4 RF Safety

Transmitting RF energy creates human exposure hazards. The applicable limits depend on frequency and modulation.

**FCC OET Bulletin 65 — maximum permissible exposure (MPE) limits for uncontrolled environments:**

| Frequency range | Power density limit | E-field limit |
|---|---|---|
| 300 kHz – 1.34 MHz | 100 mW/cm² | 614 V/m |
| 1.34 – 30 MHz | 180/f² mW/cm² | 824/f V/m |
| 30 – 300 MHz | 0.2 mW/cm² | 27.5 V/m |
| 300 MHz – 1.5 GHz | f/1500 mW/cm² | variable |
| 1.5 – 100 GHz | 1.0 mW/cm² | 61.4 V/m |

**ICNIRP reference levels** (general public exposure) are similar but differ in averaging time (6 minutes for ICNIRP vs. 30 minutes for FCC).

**Safe distance calculation** for an isotropic radiator:

```
d = sqrt(P_eirp / (4 * pi * S_limit))

Where:
  d         = minimum safe distance (meters)
  P_eirp    = effective isotropic radiated power (watts)
  S_limit   = power density limit (W/m²)

Example: HackRF at max output (+15 dBm = 31.6 mW), 433 MHz
  S_limit at 433 MHz = 0.2 mW/cm² = 2 W/m² (FCC uncontrolled)
  d = sqrt(0.0316 / (4 * pi * 2)) = 0.035 m = 3.5 cm

  → HackRF at max power is safe at any normal operating distance.
  
Example: USRP B210 with external PA, 10W EIRP at 900 MHz
  S_limit at 900 MHz = 900/1500 mW/cm² = 0.6 mW/cm² = 6 W/m²
  d = sqrt(10 / (4 * pi * 6)) = 0.36 m = 36 cm

  → Maintain >36 cm distance from antenna during transmission.
```

**Lab safety rules:**
1. Never connect an SDR transmitter directly to a receiver without appropriate attenuation — even low-power TX can damage receiver front-ends. Minimum 30 dB attenuation for HackRF-to-RTL-SDR conducted testing.
2. Always know the transmit power before keying up. Verify with a power meter or calibrated attenuator + spectrum analyzer.
3. Disable TX-capable SDRs when not in active use.
4. Post RF safety signage at Faraday cage entrances when high-power equipment is operating inside.

### 17.5 Lab Network Isolation and IQ Sample Management

**Air-gapped analysis workstation:** RF analysis may involve processing sensitive IQ captures (intercepted communications, classified signals). The analysis workstation should be air-gapped from production networks:

```bash
# Air-gapped workstation configuration checklist:
# [ ] No wired or wireless network interfaces active
# [ ] Wi-Fi and Bluetooth hardware disabled in BIOS/UEFI
# [ ] Full disk encryption (LUKS on Linux, BitLocker + TPM on Windows)
# [ ] USB port policy: only authorized SDR devices and encrypted transfer media
# [ ] Local-only tool installation: GNU Radio, URH, inspectrum, multimon-ng, Wireshark

# IQ sample management — organize captures with metadata
# Directory structure:
# /data/rf-captures/
#   YYYY-MM-DD/
#     <project>_<freq>_<rate>_<description>/
#       capture.fc32      # raw IQ data
#       capture.sigmf-meta # SigMF metadata (JSON)
#       notes.txt         # analyst notes
#       sha256sums.txt    # integrity verification

# Generate SigMF metadata for a capture:
python3 << 'PYEOF'
import json
meta = {
    "global": {
        "core:datatype": "cf32_le",
        "core:sample_rate": 2048000,
        "core:hw": "RTL-SDR v3 + wideband whip antenna",
        "core:description": "433 MHz ISM band capture - keyfob analysis",
        "core:author": "RF Lab"
    },
    "captures": [{
        "core:sample_start": 0,
        "core:frequency": 433920000,
        "core:datetime": "2026-05-13T14:30:00Z"
    }],
    "annotations": []
}
with open("capture.sigmf-meta", "w") as f:
    json.dump(meta, f, indent=2)
PYEOF

# Hash all capture files for chain-of-custody
find /data/rf-captures/ -type f -name "*.fc32" -o -name "*.cs8" \
    -o -name "*.sigmf-meta" | sort | xargs sha256sum > checksums.sha256
```

**Evidence preservation for RF forensics:**
- All IQ captures must be hashed (SHA-256) immediately after recording.
- Store the hash alongside the capture with a UTC timestamp.
- Never modify original captures — work on copies.
- SigMF metadata provides a standardized, machine-readable provenance record.
- Maintain a chain-of-custody log documenting who accessed each capture, when, and for what purpose.

---

## 18. Cross-References

**To Domain 9 (network):** ADS-B, AIS, and TPMS are radio-layer protocols with the same "no authentication" problem as early network protocols (ARP, DNS before DNSSEC). GPS spoofing affects NTP-over-GPS timing, which cascades to TLS certificate validation and Kerberos ticket timestamps. LoRaWAN and Zigbee network-layer attacks parallel IP-layer attacks. The Suricata rules in section 16.1 detect network-layer indicators of RF attacks (GSMTAP traffic, IQ stream exfiltration).

**To Domain 12 (RE):** RF protocol RE (section 2) uses the same analysis methodology as network protocol RE but applied to physical-layer signals. URH and inspectrum are the RF equivalents of Wireshark. RFID firmware extraction (JTAG/SWD) connects to embedded RE techniques. GNU Radio OOT module development (section 14.3) parallels custom dissector development in network protocol RE.

**To Domain 15 (mobile):** Private cellular networks (section 2.4) enable the IMSI-catcher attacks described in Domain 15. srsRAN provides the research platform for testing 4G/5G security properties. Bluetooth attacks (section 6) target the mobile device ecosystem directly.

**To Domain 17 (physical):** RF hardware (SDR, antennas, amplifiers) is the physical-layer complement to the side-channel and fault-injection tools in Domain 17. TEMPEST and emanation security (section 11) bridge RF security and physical security. The same lab equipment (oscilloscopes, signal generators, spectrum analyzers, VNA) supports both disciplines (section 17.2). Proxmark3 RFID attacks (section 5) enable physical access control bypass. Faraday cage construction (section 17.1) applies to both RF testing isolation and TEMPEST countermeasures.

**To Domain 18 (wireless networks):** Wi-Fi operates in the same 2.4/5 GHz ISM bands as Bluetooth and Zigbee. Rogue AP detection (Domain 18) and BLE rogue device detection (section 6.4) share spectrum monitoring methodologies. The WIDS deployment architecture in section 16.4 integrates Kismet and spectrum monitoring to provide a unified wireless threat detection capability. Jamming countermeasures (section 10) apply across all wireless protocols.

**To Domain 20B (RF attacks and exploitation):** Detection engineering rules in section 16 complement the Sigma rules and YARA rules in Domain 20B section 11, adding Suricata network-layer detection, IQ file forensic signatures, and automated spectrum monitoring. Lab calibration procedures (section 17) support the RF lab setup methodology in Domain 20B section 12.

---

## Exercises

**Exercise 1 — ISM Band Signal Capture and Protocol Identification with HackRF.**
Connect a HackRF One to a Linux workstation running GNU Radio 3.10. Capture 30 seconds of IQ data at 433.92 MHz (2 MS/s, LNA gain 32, VGA gain 20). Open the capture in inspectrum, identify at least three distinct transmissions (e.g., weather station, keyfob, TPMS sensor). For each signal: measure the bandwidth, determine the modulation type (OOK, FSK, or GQFSK), estimate the symbol rate using inspectrum cursors, and document your findings with annotated screenshots. Load the same capture in URH and compare the automated demodulation results against your manual analysis. Deliverable: a technical report with spectrum plots, modulation classification rationale, and URH bit extraction output for each identified protocol.

**Exercise 2 — Fixed-Code Replay Attack (Shielded Lab).**
Inside a Faraday enclosure or using direct SMA cable connection with attenuators, perform a complete fixed-code replay attack against a 433 MHz ASK/OOK remote control (garage door opener test unit or lab-provided transmitter). (a) Capture the transmission with `hackrf_transfer -r`. (b) Identify and trim the signal using inspectrum or URH. (c) Replay the trimmed IQ file with `hackrf_transfer -t` and verify successful actuation of the receiver. (d) Decode the protocol fields (preamble, sync, address, command, CRC) using URH's Analysis tab. (e) Modify one field (e.g., the command byte) in URH's Generator tab, export a new IQ file, and transmit it. Document whether the modified frame is accepted or rejected by the receiver. Discuss: what defense mechanism would prevent this attack?

**Exercise 3 — BLE Advertisement Sniffing and GATT Enumeration with Ubertooth.**
Using an Ubertooth One, capture BLE advertisements for 5 minutes in a controlled environment with known BLE peripherals (smart lock, fitness tracker, or BLE beacon). (a) Run `ubertooth-btle -f -c /tmp/ble_capture.pcap` and identify all advertising devices by BD_ADDR and advertisement data. (b) Follow one connection (`ubertooth-btle -f -t <target_addr>`) and capture the GATT service discovery exchange. (c) Open the PCAP in Wireshark with the `btle` dissector and enumerate all services, characteristics, and their properties (read/write/notify). (d) Identify any characteristics that permit unauthenticated write access. Deliverable: a risk assessment table listing each writable characteristic, its UUID, potential abuse scenario, and recommended mitigation (e.g., require bonding, enable LESC).

**Exercise 4 — GNU Radio 3.10 Custom Decoder Flowgraph.**
Build a GNU Radio 3.10 flowgraph (Python, not GRC) that: (a) reads an IQ file captured from a 433 MHz weather station transmitting FSK-modulated data; (b) applies a frequency-translating FIR filter to isolate the signal; (c) demodulates using `analog.quadrature_demod_cf`; (d) recovers symbol timing with `digital.clock_recovery_mm_ff`; (e) slices bits with `digital.binary_slicer_fb`; (f) outputs the decoded bitstream to a file sink. Run the flowgraph, extract the bitstream, and manually identify the preamble, device ID, temperature, and humidity fields by correlating with known sensor readings. Create an OOT Python block (`gr_modtool add -t sync -l python`) that parses the decoded bitstream and outputs structured JSON (device ID, temperature in Celsius, humidity in percent, CRC status).

**Exercise 5 — Mifare Classic Full Security Assessment with Proxmark3.**
Using a Proxmark3 RDV4 (Iceman firmware), perform a complete security assessment against a Mifare Classic 1K card. (a) Run `hf search` to identify the card type, UID, ATQA, and SAK. (b) Test all sectors for default keys using `hf mf chk --1k -f mfc_default_keys.dic`. (c) If default keys are found, execute the nested attack (`hf mf nested --1k`) to recover all sector keys. If no default keys exist, perform the Darkside attack (`hf mf darkside`) to recover one key, then chain with nested/hardnested. (d) Dump the full card contents (`hf mf dump`). (e) Analyze the dump: identify the data structure (access control bits, stored value, application data). (f) Clone the card to a UID-writable magic card (`hf mf cload`). (g) Write a finding report with: attack technique used, time to full key recovery, data sensitivity assessment, and remediation recommendation (migration to DESFire EV3 with AES-128 mutual authentication).

---

## Readings and References

- Great Scott Gadgets, "HackRF One — Open-Source SDR Platform," <https://greatscottgadgets.com/hackrf/one/> (retrieved: 2026-05-29)
- GNU Radio Project, "GNU Radio 3.10 Documentation," <https://wiki.gnuradio.org/index.php/Main_Page> (retrieved: 2026-05-29)
- Osmocom, "rtl-sdr — DVB-T Dongles as SDR Receivers," <https://osmocom.org/projects/rtl-sdr/wiki> (retrieved: 2026-05-29)
- Pohl, J. and Nober, A., "Universal Radio Hacker (URH) — A Complete Suite for Wireless Protocol Investigation," <https://github.com/jopohl/urh> (retrieved: 2026-05-29)
- Nohl, K. et al., "Wideband GSM Sniffing," presented at 27C3, 2010. <https://events.ccc.de/congress/2010/Fahrplan/events/4208.en.html>
- Kamkar, S., "Drive It Like You Hacked It: New Attacks and Tools to Wirelessly Steal Cars," DEF CON 23, 2015. <https://samy.pl/defcon2015/>
- Verdult, R., Garcia, F. D., and Balasch, J., "Gone in 360 Seconds: Hijacking with Hitag2," USENIX Security 2012. <https://www.usenix.org/conference/usenixsecurity12/technical-sessions/presentation/verdult>
- Garcia, F. D. et al., "Dismantling MIFARE Classic," ESORICS 2008. <https://doi.org/10.1007/978-3-540-88313-5_7>
- Garcia, F. D. et al., "Wirelessly Lockpicking a Smart Card Reader," USENIX Security 2020 (hardnested). <https://www.usenix.org/conference/usenixsecurity20>
- Antonioli, D. et al., "KNOB Is Not Knocking Anymore: Bluetooth Key Negotiation Attacks," USENIX Security 2019. CVE-2019-9506. <https://knobattack.com/>
- Garbelini, M. et al., "BrakTooth: Causing Havoc on Bluetooth Link Manager via Directed Fuzzing," USENIX Security 2022. <https://asset-group.github.io/disclosures/braktooth/>
- Rupprecht, D. et al., "Breaking LTE on Layer Two," IEEE S&P 2019 (aLTEr attack). <https://alter-attack.net/>
- Wright, J., "KillerBee: IEEE 802.15.4/ZigBee Security Research Toolkit," <https://github.com/riverloopsec/killerbee> (retrieved: 2026-05-29)
- CVE-2019-9506 — KNOB: Key Negotiation of Bluetooth (BR/EDR entropy downgrade). CVSS 9.3.
- CVE-2020-15802 — BLURtooth: Cross-Transport Key Derivation in dual-mode Bluetooth. CVSS 5.3.
- CVE-2020-10135 — BIAS: Bluetooth Impersonation Attacks on SSP. CVSS 6.3.
- Ahmadi, S. et al., "Security Issues in Software-Defined Radio: A Review," Cybersecurity, Springer Nature, 2025. <https://link.springer.com/article/10.1186/s42400-025-00433-x> (retrieved: 2026-05-29)

---

## Cross-References

| Domain | Section | Relationship | Direction |
|---|---|---|---|
| Domain 9 — Network Security | §9A (protocol analysis) | ADS-B, AIS, LoRaWAN share the "no authentication" pattern with ARP/DNS; Suricata rules detect GSMTAP and IQ exfiltration | Bidirectional |
| Domain 12 — Reverse Engineering | §12B (embedded RE) | RF protocol RE via URH/inspectrum parallels network protocol RE; RFID firmware extraction via JTAG/SWD | RF → RE |
| Domain 15 — Mobile Security | §15A (cellular) | srsRAN private-cell research; IMSI-catcher fundamentals; BLE phone-as-key attacks | RF → Mobile |
| Domain 17 — Physical & Side-Channel | §17A (emanation) | TEMPEST/shielding (§11); RF fingerprinting uses same ML/statistical techniques as power-trace SCA | Bidirectional |
| Domain 18 — Wireless Networks | §18A (Wi-Fi) | Shared 2.4/5 GHz ISM bands; rogue AP vs. rogue BLE detection share spectrum monitoring methods | Bidirectional |
| Domain 20B — RF Exploitation | §20B (cellular, RFID, Wi-Fi advanced) | 20A provides SDR/GNU Radio foundations; 20B extends to cellular cryptanalysis, advanced BLE/RFID/Wi-Fi exploitation | 20A → 20B |

---

## Glossary

| Term | Definition |
|---|---|
| **IQ (In-phase / Quadrature)** | Complex baseband signal representation where I is the real component and Q the imaginary component; preserves both amplitude and phase information for software demodulation. |
| **SDR (Software-Defined Radio)** | Radio system where signal processing traditionally done in hardware (mixing, filtering, demodulation) is performed in software, enabling protocol-agnostic reception and transmission. |
| **GNU Radio** | Open-source DSP framework for SDR; processing is defined as flowgraphs of interconnected blocks (sources, filters, demodulators, sinks). |
| **OOK (On-Off Keying)** | Binary amplitude-shift keying where the carrier is either present (1) or absent (0); used in simple ISM-band remote controls. |
| **FSK (Frequency-Shift Keying)** | Digital modulation where the carrier frequency shifts between discrete values to encode data; variants include 2-FSK, 4-FSK, GFSK. |
| **Rolling code (hopping code)** | Scheme where each keyfob transmission uses a counter-derived, cipher-encrypted code; the receiver accepts codes within a synchronization window. |
| **RollJam** | Attack against rolling-code systems: jam + capture code N, jam + capture code N+1, replay N; attacker retains valid unused code N+1. |
| **Crypto-1** | Proprietary 48-bit LFSR-based stream cipher used in Mifare Classic RFID cards; comprehensively broken via Darkside, nested, and hardnested attacks. |
| **GATT (Generic Attribute Profile)** | BLE protocol layer defining how data attributes (services, characteristics, descriptors) are organized and accessed between peripherals and centrals. |
| **FHSS (Frequency-Hopping Spread Spectrum)** | Technique that rapidly switches the carrier frequency across a wide band according to a pseudo-random sequence, providing resistance to narrowband jamming. |
| **DSSS (Direct Sequence Spread Spectrum)** | Technique that spreads the signal across a wide bandwidth by multiplying with a high-rate pseudo-random code; processing gain provides inherent jamming resistance. |
| **TEMPEST** | US DoD codename for the study and countermeasures of compromising electromagnetic emanations from electronic equipment; specifies shielding and zone-control requirements. |
| **SigMF (Signal Metadata Format)** | Standardized JSON metadata schema for IQ capture files, providing machine-readable provenance (frequency, sample rate, hardware, timestamp) for RF forensic evidence. |
| **CSS (Chirp Spread Spectrum)** | Modulation used by LoRa where each symbol is a linear frequency chirp sweeping the entire bandwidth; spreading factor controls range vs. data rate tradeoff. |
| **Faraday cage** | Conductive enclosure that attenuates electromagnetic fields; used in RF labs to prevent unintentional transmission leakage and for TEMPEST countermeasures. |
