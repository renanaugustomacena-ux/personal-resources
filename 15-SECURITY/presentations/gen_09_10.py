#!/usr/bin/env python3
"""Generate presentations 9 (Physical/IoT/Payment) and 10 (Threat Intel/DFIR/Architecture)."""

import io
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DARK_BG = RGBColor(0x12, 0x12, 0x24)
CYAN    = RGBColor(0x00, 0xD4, 0xFF)
RED     = RGBColor(0xFF, 0x44, 0x44)
GREEN   = RGBColor(0x00, 0xFF, 0x88)
YELLOW  = RGBColor(0xFF, 0xD7, 0x00)
PURPLE  = RGBColor(0xBB, 0x86, 0xFC)
WHITE   = RGBColor(0xFF, 0xFF, 0xFF)
LGRAY   = RGBColor(0xCC, 0xCC, 0xCC)
DGRAY   = RGBColor(0x22, 0x22, 0x3A)
MGRAY   = RGBColor(0x33, 0x33, 0x50)
W = Inches(13.333); H = Inches(7.5)

def mpl_theme():
    plt.rcParams.update({"figure.facecolor":"#121224","axes.facecolor":"#1a1a2e","axes.edgecolor":"#444466","axes.labelcolor":"#cccccc","text.color":"#cccccc","xtick.color":"#999999","ytick.color":"#999999","grid.color":"#333350","grid.alpha":0.5,"font.size":11})

def new_prs():
    p = Presentation(); p.slide_width = W; p.slide_height = H; return p

def bg(s):
    f = s.background.fill; f.solid(); f.fore_color.rgb = DARK_BG

def blank(p):
    s = p.slides.add_slide(p.slide_layouts[6]); bg(s); return s

def add_text(s, l, t, w, h, txt, size=14, color=LGRAY, bold=False, align=PP_ALIGN.LEFT):
    tb = s.shapes.add_textbox(l, t, w, h); tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; p.text = txt; p.font.size = Pt(size); p.font.color.rgb = color; p.font.bold = bold; p.alignment = align
    return tb

def box(s, l, t, w, h, fc, txt="", fs=11, ftc=WHITE, bc=None):
    sh = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, l, t, w, h)
    sh.fill.solid(); sh.fill.fore_color.rgb = fc
    if bc: sh.line.color.rgb = bc; sh.line.width = Pt(1.5)
    else: sh.line.fill.background()
    tf = sh.text_frame; tf.word_wrap = True; tf.paragraphs[0].alignment = PP_ALIGN.CENTER
    p = tf.paragraphs[0]; p.text = txt; p.font.size = Pt(fs); p.font.color.rgb = ftc; p.font.bold = True
    tf.margin_left = Pt(4); tf.margin_right = Pt(4); tf.margin_top = Pt(2); tf.margin_bottom = Pt(2)
    return sh

def arrow_r(s, x1, y1, x2, y2, c=CYAN):
    a = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, x1, y1, x2-x1, y2-y1); a.fill.solid(); a.fill.fore_color.rgb = c; a.line.fill.background()

def arrow_d(s, x, y, ln, c=CYAN):
    a = s.shapes.add_shape(MSO_SHAPE.DOWN_ARROW, x, y, Inches(0.3), ln); a.fill.solid(); a.fill.fore_color.rgb = c; a.line.fill.background()

def thin_line(s, x1, y1, x2, y2, c=CYAN):
    ln = s.shapes.add_connector(1, x1, y1, x2, y2); ln.line.color.rgb = c; ln.line.width = Pt(1.5)

def title_slide(p, title, sub):
    s = blank(p)
    add_text(s, Inches(1), Inches(2.2), Inches(11), Inches(1.5), title, 40, WHITE, True, PP_ALIGN.CENTER)
    add_text(s, Inches(1), Inches(3.8), Inches(11), Inches(1), sub, 20, CYAN, False, PP_ALIGN.CENTER)
    thin_line(s, Inches(3), Inches(3.7), Inches(10.3), Inches(3.7), CYAN)

def section_slide(p, title):
    s = blank(p)
    add_text(s, Inches(1), Inches(2.8), Inches(11), Inches(1.2), title, 36, CYAN, True, PP_ALIGN.CENTER)
    thin_line(s, Inches(4), Inches(4.2), Inches(9.3), Inches(4.2), PURPLE)

def agenda_slide(p, items):
    s = blank(p)
    add_text(s, Inches(0.8), Inches(0.4), Inches(5), Inches(0.7), "AGENDA", 32, WHITE, True)
    thin_line(s, Inches(0.8), Inches(1.1), Inches(12.5), Inches(1.1), CYAN)
    y = Inches(1.4)
    for i, item in enumerate(items):
        c = CYAN if i%2==0 else PURPLE
        box(s, Inches(1.2), y, Inches(10.5), Inches(0.4), DGRAY, f"{i+1}.  {item}", 13, LGRAY, c)
        y += Inches(0.5)

def chart_img(fig, dpi=150):
    b = io.BytesIO(); fig.savefig(b, format="png", dpi=dpi, bbox_inches="tight", pad_inches=0.3); b.seek(0); plt.close(fig); return b

def embed_chart(s, fig, l, t, w, h=None):
    return s.shapes.add_picture(chart_img(fig), l, t, w, h)

def takeaway_slide(p, items, heading="Key Takeaways"):
    s = blank(p)
    add_text(s, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), heading, 28, WHITE, True)
    thin_line(s, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    y = Inches(1.3); colors = [CYAN, GREEN, YELLOW, RED, PURPLE, CYAN, GREEN, YELLOW]
    for i, item in enumerate(items):
        box(s, Inches(1.0), y, Inches(11), Inches(0.45), DGRAY, f"▸  {item}", 12, LGRAY, colors[i%len(colors)])
        y += Inches(0.55)


# ════════════════════════════════════════════════════════════════════
#  PRESENTATION 9 — Physical/Hardware Security, IoT & Payment Systems
# ════════════════════════════════════════════════════════════════════
def gen_pres_09():
    prs = new_prs()
    title_slide(prs, "Physical/Hardware Security,\nIoT & Payment Systems", "Domains 17, 22, 28  ·  Side Channels  ·  Fault Injection  ·  EMV  ·  IoT Botnets")

    agenda_slide(prs, [
        "Side-Channel Attack Taxonomy", "Power Analysis Setup",
        "Voltage & EM Fault Injection", "Laser Fault Injection",
        "DFA on AES", "PCB Reverse Engineering", "IC Decapsulation",
        "JTAG TAP & Debug Interfaces", "Secure Boot Chain",
        "EMV Transaction Flow", "ATM Attack Taxonomy",
        "Blockchain Attack Surface", "IoT Protocol Stack",
        "IoT Device Attack Surface", "IoT Botnet Lifecycle", "Defense Architecture",
    ])

    # 3 — Side-Channel Taxonomy
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "Side-Channel Attack Taxonomy", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    box(slide, Inches(4.5), Inches(1.3), Inches(4), Inches(0.6), DGRAY, "Side-Channel Attacks", 14, WHITE, CYAN)
    # Tree branches
    branches = [
        ("Power Analysis", Inches(0.5), CYAN, ["SPA (Simple)", "DPA (Differential)", "CPA (Correlation)"]),
        ("EM Emanation", Inches(3.5), GREEN, ["Near-field probe", "DEMA", "SEMA"]),
        ("Timing", Inches(6.5), YELLOW, ["Cache timing", "Branch timing", "RSA key recovery"]),
        ("Acoustic", Inches(9.5), RED, ["Coil whine", "Keyboard acoustic", "CPU frequency"]),
    ]
    for name, x, clr, subs in branches:
        box(slide, x, Inches(2.3), Inches(2.5), Inches(0.5), DGRAY, name, 12, clr, clr)
        arrow_d(slide, x + Inches(1.1), Inches(1.9), Inches(0.3), clr)
        y = Inches(3.0)
        for sub in subs:
            add_text(slide, x + Inches(0.2), y, Inches(2.2), Inches(0.3), f"▸ {sub}", 11, LGRAY)
            y += Inches(0.3)
    add_text(slide, Inches(0.5), Inches(4.5), Inches(12), Inches(2),
        "All exploit information leakage from physical implementation, not algorithm weakness.\n\n"
        "Power/EM: most practical against embedded crypto (smartcards, HSMs, secure elements).\n"
        "Timing: most practical against software implementations (OpenSSL, GnuPG).\n"
        "Acoustic: demonstrated for RSA key extraction at 4m distance (Genkin et al., 2014).\n\n"
        "Countermeasures: constant-time code, masking/blinding, noise injection, shielding.",
        13, LGRAY)

    # 4 — Power Analysis Setup
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "Power Analysis Attack Setup", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    pa_steps = [("Target Device\n(smartcard/MCU)", CYAN), ("Shunt Resistor\n(1-10 Ω)", GREEN), ("Oscilloscope\n(high bandwidth)", YELLOW), ("Trace Collection\n(10K+ traces)", RED), ("Statistical\nAnalysis (CPA)", PURPLE)]
    x = Inches(0.3)
    for txt, clr in pa_steps:
        box(slide, x, Inches(1.4), Inches(2.1), Inches(0.9), DGRAY, txt, 11, clr, clr)
        if x < Inches(9): arrow_r(slide, x+Inches(2.2), Inches(1.75), x+Inches(2.4), Inches(1.75), clr)
        x += Inches(2.5)
    add_text(slide, Inches(0.5), Inches(2.8), Inches(12), Inches(3.5),
        "SPA (Simple Power Analysis): visual inspection of single trace. Identify crypto rounds, branches.\n"
        "DPA (Differential Power Analysis): statistical correlation over many traces. Recover key bytes.\n"
        "CPA (Correlation Power Analysis): Hamming weight/distance model. Most efficient.\n\n"
        "Equipment:\n"
        "▸ ChipWhisperer ($50-300): integrated capture + glitch platform. Open source.\n"
        "▸ PicoScope ($400-2000): general oscilloscope with high sample rate.\n"
        "▸ Riscure Inspector ($50K+): professional SCA platform.\n"
        "▸ Langer probes: near-field EM probes for DEMA/SEMA.\n\n"
        "Typical attack: CPA on AES-128 → recover 16 key bytes independently → ~10K traces needed.\n"
        "Time: setup 1-2 days, trace collection ~hours, analysis ~minutes.",
        13, LGRAY)

    # 5 — Voltage Fault Injection
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "Voltage & EM Fault Injection", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    fi_types = [
        ("Voltage Glitching", "Brief VCC drop (10-100ns) → skip instruction, corrupt computation.\nCrowbar circuit: MOSFET shorts VCC to GND briefly.", CYAN),
        ("Clock Glitching", "Extra clock edge or shortened period → setup/hold violation.\nTarget: clock input of MCU. ChipWhisperer excels here.", GREEN),
        ("EMFI", "Electromagnetic pulse via coil → localized fault.\nPicoEMP ($50), NewAE ($200), custom coils.\nX-Y positioning for spatial targeting.", YELLOW),
        ("Laser Fault Injection", "IR/UV laser through silicon backside → single-bit flip.\nMost precise but requires IC decapsulation. $50K+ setup.", RED),
    ]
    y = Inches(1.2)
    for name, desc, clr in fi_types:
        box(slide, Inches(0.5), y, Inches(2.5), Inches(0.6), DGRAY, name, 12, clr, clr)
        add_text(slide, Inches(3.3), y, Inches(9.2), Inches(0.6), desc, 11, LGRAY)
        y += Inches(0.75)
    add_text(slide, Inches(0.5), Inches(4.4), Inches(12), Inches(2),
        "Attack targets: secure boot bypass (skip signature check), PIN verification bypass,\n"
        "key extraction via DFA, privilege escalation, secure element lockout bypass.\n\n"
        "Notable: Starlink terminal rooted via voltage glitch on first boot (2022, Lennert Wouters).\n"
        "Nintendo Switch: Tegra X1 bootROM bypass via short on USB data pin (Fusée Gelée).",
        13, LGRAY)

    # 6 — EMFI Setup
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "EMFI Attack Setup — Precision Targeting", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    emfi_flow = [("Trigger\nIdentification", CYAN), ("X-Y Stage\nPositioning", GREEN), ("Pulse\nCalibration", YELLOW), ("Sweep: Location\n+ Timing + Power", RED), ("Analyze\nFault Effects", PURPLE)]
    x = Inches(0.3)
    for txt, clr in emfi_flow:
        box(slide, x, Inches(1.4), Inches(2.1), Inches(0.9), DGRAY, txt, 11, clr, clr)
        if x < Inches(9): arrow_r(slide, x+Inches(2.2), Inches(1.75), x+Inches(2.4), Inches(1.75), clr)
        x += Inches(2.5)
    add_text(slide, Inches(0.5), Inches(2.8), Inches(12), Inches(3.5),
        "EMFI advantages over voltage glitching:\n"
        "▸ Non-invasive: no physical connection to VCC/GND needed\n"
        "▸ Spatial selectivity: target specific IC regions (crypto core, CPU, memory)\n"
        "▸ Works through packaging (BGA, QFN) and PCB layers\n"
        "▸ Can affect specific operations while leaving others undisturbed\n\n"
        "X-Y positioning: CNC stage or 3D printer frame. Step through grid.\n"
        "For each position: sweep timing (ns resolution) and pulse amplitude.\n"
        "Output classification: normal, crash, mute (no response), exploitable fault.\n\n"
        "Tools: PicoEMP (open source, ~$50 BOM), ChipWhisperer Husky, Riscure EM-FI,\n"
        "NewAE CW521 (calibrated EM probe).",
        13, LGRAY)

    # 7 — Laser FI
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "Laser Fault Injection — Single-Bit Precision", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    laser_steps = [("IC Decapsulation\n(expose silicon)", RED), ("IR Laser Source\n(1064nm typical)", CYAN), ("Optical System\n(microscope + stage)", GREEN), ("Target: Individual\nTransistor / SRAM Cell", YELLOW), ("Observe:\nBit flip / Skip", PURPLE)]
    x = Inches(0.3)
    for txt, clr in laser_steps:
        box(slide, x, Inches(1.4), Inches(2.1), Inches(0.9), DGRAY, txt, 11, clr, clr)
        if x < Inches(9): arrow_r(slide, x+Inches(2.2), Inches(1.75), x+Inches(2.4), Inches(1.75), clr)
        x += Inches(2.5)
    add_text(slide, Inches(0.5), Inches(2.8), Inches(12), Inches(3),
        "Laser FI is the gold standard for precision fault attacks:\n"
        "▸ Spatial resolution: < 1μm (individual transistor targeting)\n"
        "▸ Temporal resolution: < 1ns (sub-clock-cycle faults)\n"
        "▸ Backside attack: through thinned silicon substrate (100-200μm)\n"
        "▸ Repeatable: same fault location and timing every time\n\n"
        "Required: optical bench ($50K-200K), IC prep (decap + thin), high-end XYZ stage.\n"
        "Typically used by: government labs, high-assurance evaluation (CC EAL5+), well-funded researchers.\n\n"
        "Countermeasures: light sensors (on-die), active shields (metal mesh), dual-rail logic,\n"
        "temporal/spatial redundancy (execute twice, compare), glitch detectors.",
        13, LGRAY)

    # 8 — DFA on AES
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "Differential Fault Analysis on AES", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    dfa_flow = [("Encrypt with\ncorrect key", CYAN), ("Fault during\nround 8 or 9", RED), ("Get faulty\nciphertext", YELLOW), ("Compare correct\nvs faulty output", GREEN), ("Solve key bytes\nvia equations", PURPLE)]
    x = Inches(0.3)
    for txt, clr in dfa_flow:
        box(slide, x, Inches(1.4), Inches(2.1), Inches(0.9), DGRAY, txt, 11, clr, clr)
        if x < Inches(9): arrow_r(slide, x+Inches(2.2), Inches(1.75), x+Inches(2.4), Inches(1.75), clr)
        x += Inches(2.5)
    add_text(slide, Inches(0.5), Inches(2.8), Inches(12), Inches(3),
        "Piret-Quisquater DFA (2003): fault in round 8 MixColumns input.\n"
        "One fault → reduces key space from 2^128 to ~2^32. Two faults → unique key.\n\n"
        "How: fault propagates through MixColumns differently than unfaulted computation.\n"
        "Difference between correct and faulty ciphertexts reveals SubBytes input/output pairs.\n"
        "Each pair constrains 4 key bytes. With 2+ faults on different columns → full key recovery.\n\n"
        "Practical setup: ChipWhisperer + target board. Trigger on AES start. Glitch at round 8.\n"
        "Success rate depends on fault model (single-byte vs multi-byte, random vs stuck-at).\n\n"
        "Countermeasure: AES infective computation (detect fault → randomize output), temporal redundancy.",
        13, LGRAY)

    # 9 — PCB Reverse Engineering
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "PCB Reverse Engineering Workflow", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    pcb_steps = [("High-Res\nPhotography", CYAN), ("Component\nIdentification", GREEN), ("Layer Imaging\n(X-ray / delaminate)", YELLOW), ("Schematic\nReconstruction", RED), ("Circuit\nAnalysis", PURPLE)]
    x = Inches(0.3)
    for txt, clr in pcb_steps:
        box(slide, x, Inches(1.4), Inches(2.1), Inches(0.9), DGRAY, txt, 11, clr, clr)
        if x < Inches(9): arrow_r(slide, x+Inches(2.2), Inches(1.75), x+Inches(2.4), Inches(1.75), clr)
        x += Inches(2.5)
    add_text(slide, Inches(0.5), Inches(2.8), Inches(12), Inches(3.5),
        "Photography: DSLR macro lens, ring light, calibrated color chart. Multiple angles.\n"
        "Component ID: read markings, cross-reference datasheets, multimeter verification.\n"
        "Multi-layer: X-ray (non-destructive) or chemical delamination (destructive).\n\n"
        "Tools:\n"
        "▸ KiCad: open-source schematic + PCB layout (for reconstruction)\n"
        "▸ OpenBoardView: view board CAD files if available\n"
        "▸ Multimeter + logic analyzer: trace connections, identify buses\n"
        "▸ JTAGulator: automated JTAG/UART/SWD pin identification\n"
        "▸ X-ray: Faxitron (professional), dental X-ray (budget)\n\n"
        "Goals: find debug ports (UART, JTAG, SWD), identify flash chips (SPI/NAND),\n"
        "locate test points, understand power delivery, find unpopulated connectors.",
        13, LGRAY)

    # 10 — IC Decapsulation Chart
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "IC Decapsulation Methods", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    mpl_theme()
    fig, ax = plt.subplots(figsize=(10, 4.5))
    methods = ["Chemical\n(HNO₃/H₂SO₄)", "Plasma\n(O₂/CF₄)", "Mechanical\n(CNC mill)", "Laser\nDecap"]
    cost = [2, 7, 4, 9]
    precision = [6, 9, 3, 10]
    speed_val = [7, 4, 8, 5]
    x = range(len(methods))
    w = 0.25
    ax.bar([p-w for p in x], cost, w, label="Cost (1=low)", color="#FF4444", edgecolor="#444466")
    ax.bar(x, precision, w, label="Precision", color="#00D4FF", edgecolor="#444466")
    ax.bar([p+w for p in x], speed_val, w, label="Speed", color="#00FF88", edgecolor="#444466")
    ax.set_xticks(x); ax.set_xticklabels(methods, fontsize=10)
    ax.set_ylabel("Score (1-10)", fontsize=12)
    ax.set_title("IC Decapsulation Method Comparison", fontsize=14, color="#00D4FF")
    ax.legend(facecolor="#1a1a2e", edgecolor="#444466", labelcolor="#cccccc")
    ax.set_ylim(0, 11); ax.grid(axis="y", alpha=0.3)
    embed_chart(slide, fig, Inches(1.5), Inches(1.2), Inches(10), Inches(5.5))

    # 11 — JTAG TAP
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "JTAG TAP State Machine & Debug Interfaces", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    jtag_states = [
        ("Test-Logic-Reset", "Entry state. TMS=1 for 5 clocks returns here from anywhere.", CYAN),
        ("Run-Test/Idle", "Idle state between operations.", GREEN),
        ("Shift-DR", "Shift data through data register (boundary scan, debug).", YELLOW),
        ("Shift-IR", "Shift instruction into instruction register.", RED),
        ("Update-DR/IR", "Latch shifted data/instruction.", PURPLE),
    ]
    y = Inches(1.2)
    for name, desc, clr in jtag_states:
        box(slide, Inches(0.8), y, Inches(2.5), Inches(0.45), DGRAY, name, 11, clr, clr)
        add_text(slide, Inches(3.6), y, Inches(9), Inches(0.45), desc, 12, LGRAY)
        y += Inches(0.55)
    add_text(slide, Inches(0.8), Inches(4.1), Inches(11), Inches(2.5),
        "JTAG pins: TCK (clock), TMS (mode select), TDI (data in), TDO (data out), TRST (optional reset).\n"
        "SWD (Serial Wire Debug): ARM alternative. 2 pins only (SWDIO + SWCLK). Same debug features.\n\n"
        "Attack uses: read/write memory, extract firmware, bypass secure boot, debug running code,\n"
        "set hardware breakpoints, single-step execution, read CPU registers.\n\n"
        "Finding JTAG: JTAGulator (automated pin identification), multimeter continuity testing,\n"
        "PCB silkscreen labels, known pinouts for common SoCs, logic analyzer to capture boot activity.\n"
        "Protection: JTAG lock bits, fuse-based disable, password-protected debug, debug authentication (ARM DAP).",
        13, LGRAY)

    # 12 — Secure Boot Chain
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "Secure Boot Chain", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    boot = [("BootROM\n(immutable)", CYAN), ("1st Stage\nBootloader", GREEN), ("2nd Stage\nBootloader", YELLOW), ("Kernel\nImage", RED), ("Userspace\nInit", PURPLE)]
    x = Inches(0.3)
    for txt, clr in boot:
        box(slide, x, Inches(1.4), Inches(2.1), Inches(0.9), DGRAY, txt, 11, clr, clr)
        if x < Inches(9): arrow_r(slide, x+Inches(2.2), Inches(1.75), x+Inches(2.4), Inches(1.75), clr)
        x += Inches(2.5)
    add_text(slide, Inches(0.5), Inches(2.8), Inches(12), Inches(3.5),
        "Each stage verifies the next stage's signature before executing it.\n"
        "Root of trust: BootROM. Burned into silicon at manufacturing. Cannot be patched.\n\n"
        "Bypass attacks:\n"
        "▸ Fault injection during signature verification (glitch → skip check)\n"
        "▸ BootROM vulnerability (checkm8 on Apple A5-A11: buffer overflow in DFU mode)\n"
        "▸ Key extraction from OTP/fuses (laser fault + readback)\n"
        "▸ Downgrade attack (load older vulnerable firmware, then exploit)\n"
        "▸ TOCTOU: modify image between check and use\n\n"
        "Measured Boot (TPM): doesn't prevent boot of modified firmware — just records it.\n"
        "Verified Boot (Android/ChromeOS): actively blocks unverified code from executing.\n"
        "UEFI Secure Boot: verifies bootloader + kernel signatures against db/dbx keys in firmware.",
        13, LGRAY)

    # 13 — Section divider
    section_slide(prs, "Payment Systems Security")

    # 14 — EMV Transaction Flow
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "EMV Transaction Flow", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    emv_flow = [("Card\nInsertion", CYAN), ("Application\nSelection", GREEN), ("Read Card\nData (GPO)", YELLOW), ("Cardholder\nVerification", RED), ("Online\nAuthorization", PURPLE)]
    x = Inches(0.3)
    for txt, clr in emv_flow:
        box(slide, x, Inches(1.4), Inches(2.1), Inches(0.9), DGRAY, txt, 11, clr, clr)
        if x < Inches(9): arrow_r(slide, x+Inches(2.2), Inches(1.75), x+Inches(2.4), Inches(1.75), clr)
        x += Inches(2.5)
    add_text(slide, Inches(0.5), Inches(2.8), Inches(12), Inches(3.5),
        "EMV (Europay, MasterCard, Visa) chip transaction:\n\n"
        "1. SELECT: terminal selects payment application (AID: A0000000031010 = Visa)\n"
        "2. GPO (Get Processing Options): card returns AIP + AFL\n"
        "3. READ RECORD: terminal reads card data (PAN, expiry, certificates)\n"
        "4. Data Authentication: SDA (static), DDA (dynamic), or CDA (combined)\n"
        "5. Cardholder Verification: PIN (online/offline), signature, or CVM bypass (contactless low-value)\n"
        "6. Generate AC: card generates cryptogram (ARQC for online, TC for offline, AAC for decline)\n"
        "7. Online Auth: terminal sends ARQC to issuer → issuer validates → returns ARPC\n\n"
        "Key vulnerabilities:\n"
        "▸ PIN bypass: modify CVM list in relay attack (Cambridge research, 2020)\n"
        "▸ Contactless: Visa PIN bypass via protocol manipulation (ETH Zurich, 2020)\n"
        "▸ Pre-play: predict unpredictable number (UN) → pre-generate cryptograms",
        12, LGRAY)

    # 15 — EMV Protocol Details
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "EMV Chip Authentication Methods", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    auth_methods = [
        ("SDA (Static Data Auth)", "Card signs static data with issuer key. Clone-detectable but not clone-proof.\nVulnerable: attacker can replay signed data to different terminal.", RED),
        ("DDA (Dynamic Data Auth)", "Card signs dynamic challenge from terminal. Proves card has private key.\nPrevents cloning. Requires RSA coprocessor on chip.", GREEN),
        ("CDA (Combined DDA/AC)", "Authentication integrated with cryptogram generation.\nStrongest: links auth to specific transaction. Prevents relay in some cases.", CYAN),
        ("fDDA (Fast DDA)", "Contactless variant. Faster computation for NFC timing constraints.\nUsed by Visa payWave and MasterCard PayPass.", YELLOW),
    ]
    y = Inches(1.2)
    for name, desc, clr in auth_methods:
        box(slide, Inches(0.5), y, Inches(3), Inches(0.55), DGRAY, name, 10, clr, clr)
        add_text(slide, Inches(3.8), y, Inches(8.7), Inches(0.55), desc, 11, LGRAY)
        y += Inches(0.7)

    # 16 — ATM Attack Taxonomy Chart
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "ATM Attack Taxonomy", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    mpl_theme()
    fig, ax = plt.subplots(figsize=(10, 4.5))
    atm_types = ["Card\nSkimming", "Shimming\n(chip)", "Jackpotting\n(Ploutus)", "Black Box\n(dispenser)", "Network\nMitM", "Malware\n(Tyupkin)"]
    frequency = [35, 15, 20, 12, 8, 10]
    colors_a = ["#FF4444", "#FFD700", "#00D4FF", "#00FF88", "#BB86FC", "#FF4444"]
    bars = ax.bar(atm_types, frequency, color=colors_a, edgecolor="#444466", width=0.6)
    ax.set_ylabel("Relative Frequency (%)", fontsize=12)
    ax.set_title("ATM Attack Type Distribution", fontsize=14, color="#00D4FF")
    ax.grid(axis="y", alpha=0.3)
    for bar, val in zip(bars, frequency):
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.5, f"{val}%", ha="center", fontsize=10, color="#cccccc")
    embed_chart(slide, fig, Inches(1.5), Inches(1.2), Inches(10), Inches(5.5))

    # 17 — Blockchain Attack Surface
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "Blockchain & Smart Contract Attack Surface", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    bc_attacks = [
        ("Reentrancy", "External call before state update → recursive withdrawal. The DAO hack (2016, $60M).", RED),
        ("Flash Loan Attack", "Uncollateralized instant loan → market manipulation → repay in same tx. DeFi-specific.", YELLOW),
        ("51% Attack", "Majority hashrate → double-spend. Ethereum Classic attacked multiple times.", CYAN),
        ("Front-Running (MEV)", "Observe mempool → insert tx before victim → profit from price movement.", GREEN),
        ("Bridge Exploit", "Cross-chain bridge compromise. Ronin ($625M), Wormhole ($325M), Nomad ($190M).", RED),
        ("Oracle Manipulation", "Corrupt price feed → exploit protocol logic. TWAP vs spot price.", PURPLE),
        ("Private Key Compromise", "Weak entropy, leaked mnemonic, compromised signer. Ronin: social engineering.", YELLOW),
    ]
    y = Inches(1.2)
    for name, desc, clr in bc_attacks:
        box(slide, Inches(0.5), y, Inches(2.5), Inches(0.4), DGRAY, name, 10, clr, clr)
        add_text(slide, Inches(3.2), y, Inches(9.3), Inches(0.4), desc, 11, LGRAY)
        y += Inches(0.5)
    add_text(slide, Inches(0.5), Inches(4.9), Inches(12), Inches(1),
        "Defense: Slither/Mythril static analysis, formal verification (Certora), audits (Trail of Bits, OpenZeppelin),\n"
        "bug bounties (Immunefi), timelocks + multisig, oracle diversification.",
        12, YELLOW)

    # 18 — Section divider
    section_slide(prs, "IoT Security")

    # 19 — IoT Protocol Stack
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "IoT Wireless Protocol Comparison", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    iot_protos = [
        ("Zigbee (802.15.4)", "2.4 GHz, 250 kbps, AES-128. Mesh. Home automation. 128-bit network key.", CYAN),
        ("Z-Wave (800/900 MHz)", "Sub-GHz, 100 kbps, AES-128 (S2 framework). Mesh. Smart locks/sensors.", GREEN),
        ("BLE (Bluetooth LE)", "2.4 GHz, 2 Mbps, AES-CCM. Star topology. Wearables, beacons.", YELLOW),
        ("Thread (802.15.4)", "2.4 GHz, 250 kbps, AES-128 + DTLS. Mesh. Low-power IPv6. Google/Apple.", RED),
        ("Matter (over Thread/Wi-Fi)", "Application layer standard. End-to-end encryption. Interoperability.", PURPLE),
        ("LoRaWAN", "Sub-GHz, 50 kbps, AES-128 (AppSKey + NwkSKey). Star-of-stars. 10 km+ range.", CYAN),
    ]
    y = Inches(1.2)
    for name, desc, clr in iot_protos:
        box(slide, Inches(0.3), y, Inches(2.8), Inches(0.45), DGRAY, name, 10, clr, clr)
        add_text(slide, Inches(3.4), y, Inches(9.1), Inches(0.45), desc, 11, LGRAY)
        y += Inches(0.55)
    add_text(slide, Inches(0.3), Inches(4.8), Inches(12), Inches(1),
        "Common weakness: default/hardcoded keys, unencrypted pairing, firmware not signed,\n"
        "no OTA update capability, cleartext provisioning, weak random number generation.",
        13, YELLOW)

    # 20 — IoT Device Attack Surface
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "IoT Device Attack Surface", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    iot_surface = [
        ("Firmware", "Extract via SPI/JTAG, find hardcoded creds, reverse engineer update protocol.", RED),
        ("Debug Ports", "UART console (115200 baud), JTAG/SWD access to CPU. Often left enabled.", CYAN),
        ("Wireless Interface", "BLE/Wi-Fi/Zigbee: sniff traffic, replay commands, injection attacks.", GREEN),
        ("Cloud API", "REST API for device management. Auth bypass, IDOR, excessive data exposure.", YELLOW),
        ("Mobile App", "Companion app: API keys in APK, insecure storage, certificate pinning bypass.", PURPLE),
        ("Physical", "Chip-off (flash extraction), bus sniffing (I2C/SPI), tampering detection bypass.", RED),
    ]
    y = Inches(1.2)
    for name, desc, clr in iot_surface:
        box(slide, Inches(0.8), y, Inches(2.2), Inches(0.45), DGRAY, name, 12, clr, clr)
        add_text(slide, Inches(3.3), y, Inches(9.2), Inches(0.45), desc, 12, LGRAY)
        y += Inches(0.55)
    add_text(slide, Inches(0.8), Inches(4.8), Inches(11), Inches(1),
        "Tools: binwalk (firmware extraction), Ghidra/IDA (RE), Flashrom (SPI read/write),\n"
        "Saleae logic analyzer, nRF Connect (BLE), Killerbee (Zigbee), Scapy (protocol fuzzing).",
        13, LGRAY)

    # 21 — IoT Botnet Lifecycle
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "IoT Botnet Lifecycle", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    botnet = [("Internet\nScanning", CYAN), ("Exploit / Default\nCredentials", RED), ("Payload\nDelivery", YELLOW), ("C2 Registration\n(IRC/HTTP/P2P)", GREEN), ("DDoS / Proxy\n/ Cryptomining", PURPLE)]
    x = Inches(0.3)
    for txt, clr in botnet:
        box(slide, x, Inches(1.4), Inches(2.1), Inches(0.9), DGRAY, txt, 11, clr, clr)
        if x < Inches(9): arrow_r(slide, x+Inches(2.2), Inches(1.75), x+Inches(2.4), Inches(1.75), clr)
        x += Inches(2.5)
    add_text(slide, Inches(0.5), Inches(2.8), Inches(12), Inches(3.5),
        "Notable IoT botnets:\n"
        "▸ Mirai (2016): 600K+ devices, 1.2 Tbps DDoS on Dyn DNS. Telnet default creds.\n"
        "▸ Mozi (2019-2023): P2P DHT-based C2. Exploited UPnP, HNAP, TR-069. 1.5M nodes.\n"
        "▸ Hajime (2017): P2P, no DDoS payload — blocked Mirai. \"White hat\" botnet.\n"
        "▸ HEH (2020): wiper botnet — bricked devices instead of DDoS.\n"
        "▸ RapperBot (2022): SSH brute-force, DDoS. Targeted Linux IoT devices.\n\n"
        "Infection vectors: default credentials (admin/admin), known CVEs in UPnP/SOAP,\n"
        "TR-069 (ISP management protocol) vulnerabilities, exposed telnet/SSH.\n\n"
        "Scale: estimated 15-20 billion IoT devices by 2025. Even 0.1% compromise = millions of bots.",
        13, LGRAY)

    # 22 — Defense Architecture
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "IoT / Physical Security Defense Architecture", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    defenses = [
        "Physical: tamper-evident enclosures, active mesh shields, fuse-based JTAG disable, secure boot",
        "Hardware: TPM/secure element for key storage, PUF (Physical Unclonable Functions), side-channel countermeasures",
        "Firmware: signed OTA updates, encrypted firmware images, secure bootloader chain, rollback protection",
        "Network: IoT VLAN segmentation, MUD (Manufacturer Usage Description) profiles, DNS-based monitoring",
        "Cloud: device identity certificates (X.509), mTLS for API communication, rate limiting per device",
        "Payment: PCI-DSS compliance, P2PE (Point-to-Point Encryption), tokenization, EMV migration",
        "Standards: ETSI EN 303 645 (IoT baseline), NIST 8259A, IEC 62443, PCI PIN Security",
    ]
    y = Inches(1.2)
    colors = [CYAN, GREEN, YELLOW, RED, PURPLE, CYAN, GREEN]
    for i, rec in enumerate(defenses):
        box(slide, Inches(0.5), y, Inches(12), Inches(0.45), DGRAY, f"▸  {rec}", 11, LGRAY, colors[i%len(colors)])
        y += Inches(0.53)

    # 23 — Cross-reference
    takeaway_slide(prs, [
        "Domain 6-7: Mitigation bypass & hardware — fault injection bypasses software mitigations",
        "Domain 12: Reverse engineering — firmware RE is prerequisite for IoT/embedded exploitation",
        "Domain 13: Cryptography — side-channel attacks target crypto implementations, not algorithms",
        "Domain 20: RF/SDR — wireless IoT protocols are attacked via SDR",
        "Domain 22: Payment systems — EMV/blockchain are specialized applications of crypto + hardware",
        "Domain 27: Defense architecture — IoT defense requires network segmentation + monitoring",
        "Domain 28: IoT protocols — Zigbee/Z-Wave/Thread/BLE are the wireless layer for IoT",
    ], heading="Cross-Reference Map")

    out = "/media/renan/New Volume/PROIECT/STUDIO-LAVORO/library/15-SECURITY/presentations/09_Physical_IoT_Payment.pptx"
    prs.save(out)
    print(f"[+] Saved {out.split('/')[-1]}")


# ════════════════════════════════════════════════════════════════════
#  PRESENTATION 10 — Threat Intel, DFIR & Security Architecture
# ════════════════════════════════════════════════════════════════════
def gen_pres_10():
    prs = new_prs()
    title_slide(prs, "Threat Intelligence, DFIR &\nSecurity Architecture", "Domains 23-27, 29-31  ·  OSINT  ·  DFIR  ·  ATT&CK  ·  Zero Trust  ·  Detection Engineering")

    agenda_slide(prs, [
        "OSINT Methodology", "Social Engineering Kill Chain",
        "Phishing Infrastructure", "DFIR Process (PICERL)",
        "Memory Forensics Workflow", "Cloud Forensics Sources",
        "IR Playbook Types", "Diamond Model",
        "MITRE ATT&CK Overview", "TI-to-Detection Pipeline",
        "TLP 2.0 Classification", "Zero Trust Architecture",
        "SIEM/SOAR Architecture", "Detection Engineering Lifecycle",
        "SOC Tier Structure", "Purple Teaming",
        "Defense Maturity Model", "Cross-Reference Map",
    ])

    # 3 — OSINT Methodology
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "OSINT Methodology — Intelligence Cycle", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    osint = [("Planning &\nDirection", CYAN), ("Collection\n(Passive/Active)", GREEN), ("Processing &\nCorrelation", YELLOW), ("Analysis &\nProduction", RED), ("Dissemination\n& Feedback", PURPLE)]
    x = Inches(0.3)
    for txt, clr in osint:
        box(slide, x, Inches(1.4), Inches(2.1), Inches(0.9), DGRAY, txt, 11, clr, clr)
        if x < Inches(9): arrow_r(slide, x+Inches(2.2), Inches(1.75), x+Inches(2.4), Inches(1.75), clr)
        x += Inches(2.5)
    add_text(slide, Inches(0.5), Inches(2.8), Inches(12), Inches(3.5),
        "Collection sources:\n"
        "▸ Passive: search engines, social media, public records, breach databases, DNS/WHOIS, CT logs\n"
        "▸ Semi-passive: web scraping, cached pages, Wayback Machine, Shodan/Censys\n"
        "▸ Active: port scanning, banner grabbing, social engineering (higher OPSEC risk)\n\n"
        "Tools: Maltego (link analysis), SpiderFoot (automated recon), theHarvester (email/domain),\n"
        "Shodan/Censys (internet-facing assets), Recon-ng (framework), Amass (subdomain enum),\n"
        "FOCA (metadata extraction), Metagoofil (document metadata), Sherlock (username search).\n\n"
        "OPSEC: use VPN/Tor, burner accounts, separate research infrastructure.\n"
        "Legal: OSINT is generally legal but jurisdiction-specific. GDPR considerations for EU targets.",
        13, LGRAY)

    # 4 — Social Engineering Kill Chain
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "Social Engineering Kill Chain", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    se_chain = [("Target\nReconnaissance", CYAN), ("Pretext\nDevelopment", GREEN), ("Engagement\n& Trust", YELLOW), ("Exploitation\n(Action)", RED), ("Exit &\nPersistence", PURPLE)]
    x = Inches(0.3)
    for txt, clr in se_chain:
        box(slide, x, Inches(1.4), Inches(2.1), Inches(0.9), DGRAY, txt, 11, clr, clr)
        if x < Inches(9): arrow_r(slide, x+Inches(2.2), Inches(1.75), x+Inches(2.4), Inches(1.75), clr)
        x += Inches(2.5)
    add_text(slide, Inches(0.5), Inches(2.8), Inches(12), Inches(3.5),
        "Attack types by vector:\n"
        "▸ Phishing: spear-phishing email → credential harvesting or malware delivery\n"
        "▸ BEC: impersonate executive → wire transfer redirect ($2.7B losses in 2022 — FBI IC3)\n"
        "▸ Vishing: phone-based social engineering → IT helpdesk password reset\n"
        "▸ Smishing: SMS-based lure → malicious link / app install\n"
        "▸ Physical: tailgating, badge cloning, USB drops, impersonation\n\n"
        "Advanced techniques:\n"
        "▸ AiTM (Adversary-in-the-Middle): Evilginx2 → real-time proxy → steal session token post-MFA\n"
        "▸ QR code phishing (Quishing): bypass email link scanners\n"
        "▸ Deepfake voice: clone executive voice for vishing (multiple $25M+ incidents in 2023-2024)\n"
        "▸ Multi-channel: combine email + phone + SMS for higher success rate",
        13, LGRAY)

    # 5 — Phishing Infrastructure
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "Phishing Infrastructure Diagram", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    phish_infra = [("Lookalike Domain\n(typosquat)", RED), ("Landing Page\n(cloned login)", YELLOW), ("Credential\nHarvesting", CYAN), ("Real-Time\nRelay (AiTM)", GREEN), ("Exfiltration\n(Telegram/API)", PURPLE)]
    x = Inches(0.3)
    for txt, clr in phish_infra:
        box(slide, x, Inches(1.4), Inches(2.1), Inches(0.9), DGRAY, txt, 11, clr, clr)
        if x < Inches(9): arrow_r(slide, x+Inches(2.2), Inches(1.75), x+Inches(2.4), Inches(1.75), clr)
        x += Inches(2.5)
    add_text(slide, Inches(0.5), Inches(2.8), Inches(12), Inches(3.5),
        "Modern phishing infrastructure:\n"
        "▸ Domain: typosquat or homoglyph (Punycode). Bulletproof hosting. Let's Encrypt for HTTPS.\n"
        "▸ Evilginx2 / Modlishka: reverse proxy → intercepts session cookies → bypasses MFA.\n"
        "▸ GoPhish: open-source phishing framework for red team campaigns.\n"
        "▸ Exfil: Telegram bot API, Slack webhook, Google Forms, or custom API endpoint.\n\n"
        "Detection:\n"
        "▸ Certificate Transparency monitoring (CT logs for domain lookalikes)\n"
        "▸ DMARC/DKIM/SPF enforcement (prevents domain spoofing)\n"
        "▸ URL reputation + sandbox detonation (clicking link in sandbox)\n"
        "▸ Phishing-resistant MFA (FIDO2/WebAuthn — immune to AiTM proxy)\n"
        "▸ Conditional Access policies: device compliance, location, risk level",
        13, LGRAY)

    # 6 — Section divider
    section_slide(prs, "Digital Forensics &\nIncident Response")

    # 7 — DFIR Process
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "DFIR Process — PICERL Framework", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    picerl = [
        ("Preparation", "IR plan, playbooks, tooling, retainers, tabletop exercises, logging baseline.", CYAN),
        ("Identification", "Detect & triage. Alert validation. Scope assessment. Evidence preservation.", GREEN),
        ("Containment", "Short-term: isolate host. Long-term: credential reset, firewall rules.", YELLOW),
        ("Eradication", "Remove malware, close access vectors, patch vulnerabilities, rebuild systems.", RED),
        ("Recovery", "Restore from clean backups, monitor for re-compromise, phased service restoration.", PURPLE),
        ("Lessons Learned", "Post-incident review within 72h. Update playbooks. Track remediation items.", CYAN),
    ]
    y = Inches(1.2)
    for name, desc, clr in picerl:
        box(slide, Inches(0.5), y, Inches(2.2), Inches(0.45), DGRAY, name, 12, clr, clr)
        add_text(slide, Inches(3.0), y, Inches(9.5), Inches(0.45), desc, 12, LGRAY)
        y += Inches(0.55)
    add_text(slide, Inches(0.5), Inches(4.8), Inches(12), Inches(1.5),
        "Critical first 24 hours: preserve volatile evidence (memory, network connections, running processes),\n"
        "establish timeline, determine initial access vector, assess scope of compromise.\n"
        "Evidence handling: chain of custody, write-blockers, forensic images (dd/FTK Imager), hashing (SHA-256).",
        13, LGRAY)

    # 8 — Memory Forensics
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "Memory Forensics Workflow", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    mem_flow = [("Memory\nAcquisition", CYAN), ("Profile\nIdentification", GREEN), ("Process\nAnalysis", YELLOW), ("Network\nArtifacts", RED), ("Malware\nExtraction", PURPLE)]
    x = Inches(0.3)
    for txt, clr in mem_flow:
        box(slide, x, Inches(1.4), Inches(2.1), Inches(0.9), DGRAY, txt, 11, clr, clr)
        if x < Inches(9): arrow_r(slide, x+Inches(2.2), Inches(1.75), x+Inches(2.4), Inches(1.75), clr)
        x += Inches(2.5)
    add_text(slide, Inches(0.5), Inches(2.8), Inches(12), Inches(3.5),
        "Acquisition: WinPmem, LiME (Linux), AVML (Azure), DumpIt, Magnet RAM Capture.\n"
        "Cloud: VM memory snapshot (AWS EC2, Azure VM, GCP).\n\n"
        "Analysis tools:\n"
        "▸ Volatility 3: process list, DLL analysis, network connections, registry, malware detection\n"
        "▸ Rekall: alternative framework (now largely archived)\n"
        "▸ MemProcFS: memory as filesystem — browse with standard tools\n\n"
        "Key artifacts: injected code (malfind), hidden processes (psxview), API hooks,\n"
        "network connections (netscan), command history, credential material (hashdump/mimikatz),\n"
        "encryption keys (aeskeyfind), browser history, clipboard contents.\n\n"
        "Memory forensics catches what disk forensics misses: fileless malware, injected shellcode,\n"
        "decrypted payloads, process hollowing, reflective DLL injection.",
        13, LGRAY)

    # 9 — Cloud Forensics
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "Cloud Forensics Evidence Sources", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    cloud_ev = [
        ("AWS", "CloudTrail (API), VPC Flow Logs, GuardDuty, S3 access logs, EBS snapshots, CloudWatch", CYAN),
        ("Azure", "Activity Log, NSG Flow Logs, Sentinel, Defender, Disk snapshots, AAD sign-in logs", GREEN),
        ("GCP", "Cloud Audit Logs, VPC Flow Logs, SCC, Chronicle, Disk snapshots, IAM logs", YELLOW),
        ("Kubernetes", "Audit logs, Falco alerts, pod logs, etcd snapshots, network policies", RED),
        ("SaaS (M365)", "Unified Audit Log, Purview, Defender, Azure AD sign-ins, Mailbox audit", PURPLE),
    ]
    y = Inches(1.2)
    for name, desc, clr in cloud_ev:
        box(slide, Inches(0.5), y, Inches(1.5), Inches(0.5), DGRAY, name, 13, clr, clr)
        add_text(slide, Inches(2.3), y, Inches(10.2), Inches(0.5), desc, 12, LGRAY)
        y += Inches(0.6)
    add_text(slide, Inches(0.5), Inches(4.4), Inches(12), Inches(2),
        "Cloud forensics challenges:\n"
        "▸ Shared responsibility: provider owns infrastructure logs, customer owns application logs\n"
        "▸ Ephemeral resources: containers, Lambda, spot instances — evidence vanishes\n"
        "▸ Log retention: default retention varies (CloudTrail: 90 days without S3 delivery)\n"
        "▸ Multi-region: attacker may pivot across regions; logs must be centralized\n"
        "▸ Encryption: EBS snapshots encrypted with customer KMS keys — need key access for analysis\n\n"
        "Best practice: centralize all logs to SIEM, enable all audit logging BEFORE incident.",
        13, LGRAY)

    # 10 — IR Playbook Chart
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "IR Playbook Types — Response Strategy Comparison", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    mpl_theme()
    fig, ax = plt.subplots(figsize=(10, 4.5))
    playbooks = ["Ransomware", "APT /\nNation-State", "Insider\nThreat", "BEC /\nFraud", "Cloud\nCompromise"]
    urgency = [10, 7, 6, 9, 8]
    complexity = [7, 10, 8, 5, 9]
    legal = [8, 9, 10, 7, 6]
    x = range(len(playbooks))
    w = 0.25
    ax.bar([p-w for p in x], urgency, w, label="Urgency", color="#FF4444", edgecolor="#444466")
    ax.bar(x, complexity, w, label="Complexity", color="#00D4FF", edgecolor="#444466")
    ax.bar([p+w for p in x], legal, w, label="Legal Sensitivity", color="#FFD700", edgecolor="#444466")
    ax.set_xticks(x); ax.set_xticklabels(playbooks, fontsize=10)
    ax.set_ylabel("Score (1-10)", fontsize=12)
    ax.set_title("IR Playbook Characteristics", fontsize=14, color="#00D4FF")
    ax.legend(facecolor="#1a1a2e", edgecolor="#444466", labelcolor="#cccccc")
    ax.set_ylim(0, 11); ax.grid(axis="y", alpha=0.3)
    embed_chart(slide, fig, Inches(1.5), Inches(1.2), Inches(10), Inches(5.5))

    # 11 — Section divider
    section_slide(prs, "Threat Intelligence")

    # 12 — Diamond Model
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "Diamond Model of Intrusion Analysis", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    # Diamond shape
    box(slide, Inches(4.5), Inches(1.3), Inches(4), Inches(0.7), DGRAY, "Adversary", 14, RED, RED)
    box(slide, Inches(1), Inches(3.0), Inches(3.5), Inches(0.7), DGRAY, "Infrastructure", 14, CYAN, CYAN)
    box(slide, Inches(8.5), Inches(3.0), Inches(3.5), Inches(0.7), DGRAY, "Capability", 14, GREEN, GREEN)
    box(slide, Inches(4.5), Inches(4.7), Inches(4), Inches(0.7), DGRAY, "Victim", 14, YELLOW, YELLOW)
    # Connecting lines (approximate diamond)
    thin_line(slide, Inches(5.5), Inches(2.0), Inches(2.5), Inches(3.2), LGRAY)  # Adv → Infra
    thin_line(slide, Inches(7.5), Inches(2.0), Inches(10), Inches(3.2), LGRAY)  # Adv → Cap
    thin_line(slide, Inches(2.5), Inches(3.7), Inches(5.5), Inches(4.9), LGRAY)  # Infra → Victim
    thin_line(slide, Inches(10), Inches(3.7), Inches(7.5), Inches(4.9), LGRAY)  # Cap → Victim
    add_text(slide, Inches(0.5), Inches(5.7), Inches(12), Inches(1.2),
        "Meta-features: timestamp, phase, result, direction, methodology, resources.\n"
        "Activity threads: chain events across time. Activity groups: cluster by shared vertices.\n"
        "Pivot analysis: from IOC (infrastructure) → adversary → capability → other victims.",
        13, LGRAY)

    # 13 — MITRE ATT&CK
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "MITRE ATT&CK Matrix — Simplified", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    tactics = [
        ("Recon", "T1595\nScanning", CYAN),
        ("Resource\nDev", "T1583\nDomains", GREEN),
        ("Initial\nAccess", "T1566\nPhishing", RED),
        ("Execution", "T1059\nCmd/Script", YELLOW),
        ("Persistence", "T1053\nScheduled", PURPLE),
        ("Priv Esc", "T1068\nExploit", RED),
        ("Defense\nEvasion", "T1070\nLog Clear", CYAN),
        ("Cred\nAccess", "T1003\nDumping", GREEN),
        ("Discovery", "T1087\nAccount", YELLOW),
        ("Lateral\nMovement", "T1021\nRemote", PURPLE),
        ("Collection", "T1005\nLocal Data", CYAN),
        ("Exfil", "T1041\nC2 Channel", RED),
        ("Impact", "T1486\nEncrypt", RED),
    ]
    x = Inches(0.1)
    for tactic, technique, clr in tactics:
        box(slide, x, Inches(1.3), Inches(0.95), Inches(0.5), DGRAY, tactic, 7, clr, clr)
        box(slide, x, Inches(1.9), Inches(0.95), Inches(0.5), MGRAY, technique, 6, LGRAY)
        x += Inches(1.0)
    add_text(slide, Inches(0.5), Inches(2.8), Inches(12), Inches(3.5),
        "ATT&CK usage:\n"
        "▸ Threat profiling: map adversary TTPs to matrix → understand capabilities\n"
        "▸ Detection gaps: overlay detections on matrix → identify blind spots\n"
        "▸ Purple teaming: red team emulates specific techniques → blue team validates detection\n"
        "▸ CTI reporting: standardized language for describing adversary behavior\n\n"
        "Matrices: Enterprise (Windows, Linux, macOS, Cloud, Network, SaaS), Mobile, ICS.\n"
        "14 tactics, 200+ techniques, 400+ sub-techniques (Enterprise v15).\n\n"
        "Tools: ATT&CK Navigator (heatmap), CALDERA (automated adversary emulation),\n"
        "Atomic Red Team (unit tests per technique), MITRE D3FEND (defensive countermeasures).",
        13, LGRAY)

    # 14 — TI-to-Detection Pipeline
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "Threat Intelligence to Detection Pipeline", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    ti_pipe = [("Raw Intel\n(feeds, reports)", CYAN), ("Enrichment\n(MISP, VirusTotal)", GREEN), ("IOC/TTP\nExtraction", YELLOW), ("Detection Rule\n(Sigma/YARA)", RED), ("SIEM Alert\n+ Response", PURPLE)]
    x = Inches(0.3)
    for txt, clr in ti_pipe:
        box(slide, x, Inches(1.4), Inches(2.1), Inches(0.9), DGRAY, txt, 11, clr, clr)
        if x < Inches(9): arrow_r(slide, x+Inches(2.2), Inches(1.75), x+Inches(2.4), Inches(1.75), clr)
        x += Inches(2.5)
    add_text(slide, Inches(0.5), Inches(2.8), Inches(12), Inches(3.5),
        "Intel feeds: OSINT (abuse.ch, AlienVault OTX), commercial (Recorded Future, Mandiant),\n"
        "ISAC (sector-specific), government (CISA alerts, FBI Flash).\n\n"
        "Processing: STIX 2.1 format → TAXII transport → MISP platform → enrich with context.\n"
        "IOC types: IP, domain, URL, file hash, certificate fingerprint, YARA rule, Sigma rule.\n\n"
        "Rule languages:\n"
        "▸ Sigma: vendor-agnostic SIEM detection rules → compile to Splunk/Elastic/Sentinel\n"
        "▸ YARA: file pattern matching rules for malware detection\n"
        "▸ Snort/Suricata: network-based detection rules\n"
        "▸ KQL/SPL: SIEM-specific query languages for complex behavioral detection\n\n"
        "Maturity: IOC matching (reactive) → TTP detection (proactive) → threat hunting (hypothesis-driven).",
        13, LGRAY)

    # 15 — TLP 2.0
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "TLP 2.0 — Traffic Light Protocol", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    tlp = [
        ("TLP:RED", "Named recipients only. No sharing beyond the conversation/meeting.", RGBColor(0xFF, 0x00, 0x00)),
        ("TLP:AMBER+STRICT", "Organization only. No sharing beyond the recipient's org.", RGBColor(0xFF, 0xBF, 0x00)),
        ("TLP:AMBER", "Organization + clients/customers who need-to-know.", RGBColor(0xFF, 0xBF, 0x00)),
        ("TLP:GREEN", "Community sharing. Peers, partner orgs, sector. Not public.", RGBColor(0x00, 0xFF, 0x00)),
        ("TLP:CLEAR", "No restrictions. Can be shared publicly.", RGBColor(0xFF, 0xFF, 0xFF)),
    ]
    y = Inches(1.3)
    for name, desc, clr in tlp:
        box(slide, Inches(1), y, Inches(2.8), Inches(0.55), DGRAY, name, 14, clr, clr)
        add_text(slide, Inches(4.2), y, Inches(8.3), Inches(0.55), desc, 13, LGRAY)
        y += Inches(0.7)
    add_text(slide, Inches(1), Inches(5.0), Inches(11), Inches(1.5),
        "TLP 2.0 (FIRST, 2022) replaces TLP 1.0. Key change: AMBER+STRICT added.\n"
        "Used in: CTI sharing, ISAC communications, CERT coordination, vendor advisories.\n"
        "Violation = loss of trust and future intelligence access. Enforcement is community-based.",
        13, LGRAY)

    # 16 — Section divider
    section_slide(prs, "Security Architecture &\nDetection Engineering")

    # 17 — Zero Trust
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "Zero Trust Architecture (NIST SP 800-207)", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    zt_components = [
        ("Policy Engine (PE)", "Makes access decisions based on policy + context. Trust score computation.", CYAN),
        ("Policy Administrator (PA)", "Establishes/shuts down communication paths. Session management.", GREEN),
        ("Policy Enforcement Point (PEP)", "Enables/disables connections. Data plane gateway.", YELLOW),
        ("Identity Provider (IdP)", "Authenticates subjects. MFA, SSO, certificate-based auth.", RED),
        ("Device Trust", "MDM compliance, EDR status, patch level, health attestation.", PURPLE),
        ("Data Security", "Encryption at rest + transit, DLP, classification, access logging.", CYAN),
    ]
    y = Inches(1.2)
    for name, desc, clr in zt_components:
        box(slide, Inches(0.3), y, Inches(3), Inches(0.45), DGRAY, name, 10, clr, clr)
        add_text(slide, Inches(3.6), y, Inches(9), Inches(0.45), desc, 12, LGRAY)
        y += Inches(0.55)
    add_text(slide, Inches(0.3), Inches(4.8), Inches(12), Inches(1.5),
        "Core principle: 'Never trust, always verify.' No implicit trust based on network location.\n"
        "Every access request evaluated: identity, device, context, risk, data sensitivity.\n"
        "Implementation: microsegmentation, ZTNA (Zscaler, Cloudflare), identity-aware proxy, mTLS.",
        13, YELLOW)

    # 18 — SIEM/SOAR
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "SIEM / SOAR Architecture", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    siem_flow = [("Log Sources\n(EDR, firewall, cloud)", CYAN), ("Collection\n(agents, syslog)", GREEN), ("Message Queue\n(Kafka)", YELLOW), ("SIEM\n(detection, correlation)", RED), ("SOAR\n(automation, response)", PURPLE)]
    x = Inches(0.3)
    for txt, clr in siem_flow:
        box(slide, x, Inches(1.4), Inches(2.1), Inches(0.9), DGRAY, txt, 11, clr, clr)
        if x < Inches(9): arrow_r(slide, x+Inches(2.2), Inches(1.75), x+Inches(2.4), Inches(1.75), clr)
        x += Inches(2.5)
    add_text(slide, Inches(0.5), Inches(2.8), Inches(12), Inches(3.5),
        "SIEM platforms: Splunk, Microsoft Sentinel, Elastic Security, Chronicle (Google), QRadar.\n"
        "SOAR platforms: Palo Alto XSOAR, Splunk SOAR, Swimlane, Tines.\n\n"
        "Scale for conglomerate (thousands of companies):\n"
        "▸ Ingestion: 10-100 TB/day. Cost optimization: hot/warm/cold tiers.\n"
        "▸ Architecture: multi-tenant SIEM with per-company workspaces\n"
        "▸ Detection: centralized detection rules + company-specific custom rules\n"
        "▸ SOAR playbooks: auto-enrich, auto-contain, analyst handoff for complex cases\n\n"
        "Critical log sources: EDR telemetry, DNS queries, proxy/firewall, authentication events,\n"
        "email gateway, cloud API audit logs, identity provider (sign-in, MFA), network flow data.",
        13, LGRAY)

    # 19 — Detection Engineering Lifecycle
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "Detection Engineering Lifecycle", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    det_steps = [("Hypothesis\n(TI-informed)", CYAN), ("Rule\nDevelopment", GREEN), ("Testing\n(Atomic RT)", YELLOW), ("Deployment\n(SIEM/EDR)", RED), ("Tuning &\nMaintenance", PURPLE)]
    x = Inches(0.3)
    for txt, clr in det_steps:
        box(slide, x, Inches(1.4), Inches(2.1), Inches(0.9), DGRAY, txt, 11, clr, clr)
        if x < Inches(9): arrow_r(slide, x+Inches(2.2), Inches(1.75), x+Inches(2.4), Inches(1.75), clr)
        x += Inches(2.5)
    add_text(slide, Inches(0.5), Inches(2.8), Inches(12), Inches(3.5),
        "Detection-as-Code: detection rules managed in Git, CI/CD pipeline, version controlled.\n"
        "Testing: Atomic Red Team, CALDERA, or manual emulation → validate detection fires.\n"
        "Metrics: true positive rate, false positive rate, MTTD (Mean Time to Detect), coverage %.\n\n"
        "Detection types:\n"
        "▸ Signature/IOC: exact match (hash, IP, domain). Fast but fragile — adversary changes IOCs.\n"
        "▸ Behavioral: patterns of activity (process tree, command-line args). More durable.\n"
        "▸ Anomaly: deviation from baseline (ML-based). High FP rate but catches novel threats.\n"
        "▸ Threat hunting: proactive, hypothesis-driven. Human-in-the-loop. ATT&CK-mapped.\n\n"
        "Rule quality: Sigma rules for portability, unit tested, versioned, mapped to ATT&CK technique ID.",
        13, LGRAY)

    # 20 — SOC Tier Structure
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "SOC Tier Structure", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    soc_tiers = [
        ("L1 — Triage Analyst", "Alert triage, initial classification, false positive closure.\n24/7 coverage. Follow runbooks. Escalate confirmed incidents.", CYAN),
        ("L2 — Investigation", "Deep-dive investigation. Timeline reconstruction. IOC extraction.\nCorrelate across log sources. Determine scope and impact.", GREEN),
        ("L3 — Hunt / Engineering", "Proactive threat hunting. Detection rule development.\nTool development. Malware analysis. Purple teaming.", YELLOW),
        ("IR Lead / Manager", "Incident coordination. Stakeholder communication.\nEscalation to CISO. External coordination (CERT, LE).", RED),
    ]
    y = Inches(1.2)
    for name, desc, clr in soc_tiers:
        box(slide, Inches(0.5), y, Inches(2.8), Inches(0.7), DGRAY, name, 11, clr, clr)
        add_text(slide, Inches(3.6), y, Inches(9), Inches(0.7), desc, 11, LGRAY)
        y += Inches(0.85)
    add_text(slide, Inches(0.5), Inches(4.8), Inches(12), Inches(1),
        "Modern trend: flatten tiers. Automation handles L1 triage → analysts start at investigation level.\n"
        "SOAR reduces toil: auto-enrich, auto-close known FPs, playbook-driven containment.",
        13, YELLOW)

    # 21 — Ransomware Kill Chain
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "Ransomware Kill Chain — Detection Opportunities", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    ransom = [
        ("Initial Access\n(phishing/RDP/VPN)", RED, "DETECT: email gateway, brute-force alerts"),
        ("Persistence\n(scheduled task, service)", YELLOW, "DETECT: new services, autoruns, registry"),
        ("Lateral Movement\n(RDP, PsExec, WMI)", CYAN, "DETECT: 4624 type 3, SMB sessions"),
        ("Exfiltration\n(rclone, megasync)", GREEN, "DETECT: unusual egress, DLP, proxy logs"),
        ("Encryption\n(BitLocker, custom)", PURPLE, "DETECT: mass file rename, vssadmin delete"),
    ]
    x = Inches(0.1)
    for txt, clr, detect in ransom:
        box(slide, x, Inches(1.4), Inches(2.3), Inches(0.8), DGRAY, txt, 10, clr, clr)
        add_text(slide, x, Inches(2.3), Inches(2.3), Inches(0.5), detect, 8, GREEN, align=PP_ALIGN.CENTER)
        if x < Inches(9): arrow_r(slide, x+Inches(2.4), Inches(1.7), x+Inches(2.55), Inches(1.7), clr)
        x += Inches(2.6)
    add_text(slide, Inches(0.5), Inches(3.2), Inches(12), Inches(3.5),
        "Average dwell time before encryption: 5-21 days (varies by group).\n"
        "Every stage is a detection opportunity. Best chance: lateral movement phase (noisiest).\n\n"
        "Double extortion: exfiltrate data before encrypting. Triple: DDoS victim's customers.\n"
        "RaaS groups: LockBit, BlackCat/ALPHV, Cl0p, Play, Royal, BianLian, Akira.\n\n"
        "Critical controls:\n"
        "▸ Offline immutable backups (3-2-1 rule: 3 copies, 2 media types, 1 offsite)\n"
        "▸ EDR on all endpoints (not just servers)\n"
        "▸ MFA on all remote access (RDP, VPN, email, SaaS)\n"
        "▸ Network segmentation (limit blast radius)\n"
        "▸ Disable RDP where not needed. If needed: NLA, MFA, jump server only.",
        13, LGRAY)

    # 22 — Purple Teaming
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "Purple Teaming Methodology", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    purple = [("Emulation\nPlan (ATT&CK)", CYAN), ("Red: Execute\nTechnique", RED), ("Blue: Detect\n& Respond", GREEN), ("Gap\nAnalysis", YELLOW), ("Remediation\n& Re-test", PURPLE)]
    x = Inches(0.3)
    for txt, clr in purple:
        box(slide, x, Inches(1.4), Inches(2.1), Inches(0.9), DGRAY, txt, 11, clr, clr)
        if x < Inches(9): arrow_r(slide, x+Inches(2.2), Inches(1.75), x+Inches(2.4), Inches(1.75), clr)
        x += Inches(2.5)
    add_text(slide, Inches(0.5), Inches(2.8), Inches(12), Inches(3.5),
        "Purple team ≠ red team + blue team sitting together. It's a structured feedback loop.\n\n"
        "Process:\n"
        "1. Select threat profile (APT29, FIN7, etc.) or specific techniques\n"
        "2. Red team executes technique in controlled manner (Atomic Red Team / CALDERA)\n"
        "3. Blue team observes: did detection fire? Was alert actionable? Was response effective?\n"
        "4. Document gaps: missing log source, no detection rule, alert too noisy, no playbook\n"
        "5. Build/improve detection → re-execute technique → validate detection\n\n"
        "Frameworks: MITRE ATT&CK Evaluations, Atomic Red Team, SCYTHE, AttackIQ, SafeBreach.\n"
        "Output: ATT&CK coverage heatmap, prioritized detection backlog, improved playbooks.",
        13, LGRAY)

    # 23 — Defense Maturity Chart
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "Security Program Maturity Model", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    mpl_theme()
    fig, ax = plt.subplots(figsize=(10, 4.5))
    levels = ["Ad-Hoc\n(Level 1)", "Repeatable\n(Level 2)", "Defined\n(Level 3)", "Managed\n(Level 4)", "Optimizing\n(Level 5)"]
    capabilities = [15, 35, 60, 80, 95]
    colors_m = ["#FF4444", "#FFD700", "#00D4FF", "#00FF88", "#BB86FC"]
    bars = ax.bar(levels, capabilities, color=colors_m, edgecolor="#444466", width=0.6)
    ax.set_ylabel("Threat Coverage (%)", fontsize=12)
    ax.set_title("Security Maturity vs Threat Coverage", fontsize=14, color="#00D4FF")
    ax.set_ylim(0, 100); ax.grid(axis="y", alpha=0.3)
    for bar, val in zip(bars, capabilities):
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+1, f"{val}%", ha="center", fontsize=11, color="#cccccc")
    embed_chart(slide, fig, Inches(1.5), Inches(1.2), Inches(10), Inches(5.5))

    # 24 — Cross-Reference Map
    takeaway_slide(prs, [
        "All domains: ATT&CK maps techniques from every domain into unified taxonomy",
        "Domain 8-9: Web/network — primary initial access vectors for enterprise compromise",
        "Domain 10: Cloud — cloud forensics requires provider-specific knowledge and tooling",
        "Domain 11: Malware/tradecraft — detection engineering must understand adversary tools",
        "Domain 13: Cryptography — TI sharing relies on STIX/TAXII, detection uses Sigma/YARA",
        "Domain 14: AD/Windows — #1 target for enterprise attacks, richest telemetry source",
        "Domain 22: Payment — financial fraud detection parallels SOC operations",
        "Domains 29-31: New domains extend architecture, AI security, and advanced defense topics",
    ], heading="Cross-Reference Map — All 31 Domains")

    out = "/media/renan/New Volume/PROIECT/STUDIO-LAVORO/library/15-SECURITY/presentations/10_ThreatIntel_DFIR_Architecture.pptx"
    prs.save(out)
    print(f"[+] Saved {out.split('/')[-1]}")


if __name__ == "__main__":
    gen_pres_09()
    gen_pres_10()
    print("[✓] Presentations 9 & 10 generated successfully.")
