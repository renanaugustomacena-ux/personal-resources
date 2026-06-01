#!/usr/bin/env python3
"""Generate presentations 3 (Mitigation Bypass & Hardware) and 4 (Web & Network Security)."""

import io
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# ── Theme ──
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

W = Inches(13.333)
H = Inches(7.5)

def mpl_theme():
    plt.rcParams.update({
        "figure.facecolor": "#121224",
        "axes.facecolor": "#1a1a2e",
        "axes.edgecolor": "#444466",
        "axes.labelcolor": "#cccccc",
        "text.color": "#cccccc",
        "xtick.color": "#999999",
        "ytick.color": "#999999",
        "grid.color": "#333350",
        "grid.alpha": 0.5,
        "font.size": 11,
    })

def new_prs():
    prs = Presentation()
    prs.slide_width = W
    prs.slide_height = H
    return prs

def bg(slide):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = DARK_BG

def blank(prs):
    layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(layout)
    bg(slide)
    return slide

def add_text(slide, left, top, width, height, text, size=14, color=LGRAY, bold=False, align=PP_ALIGN.LEFT):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(size)
    p.font.color.rgb = color
    p.font.bold = bold
    p.alignment = align
    return txBox

def add_para(tf, text, size=14, color=LGRAY, bold=False, align=PP_ALIGN.LEFT):
    p = tf.add_paragraph()
    p.text = text
    p.font.size = Pt(size)
    p.font.color.rgb = color
    p.font.bold = bold
    p.alignment = align
    return p

def box(slide, left, top, w, h, fill_color, text="", font_size=11, font_color=WHITE, border_color=None):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, w, h)
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    if border_color:
        shape.line.color.rgb = border_color
        shape.line.width = Pt(1.5)
    else:
        shape.line.fill.background()
    tf = shape.text_frame
    tf.word_wrap = True
    tf.paragraphs[0].alignment = PP_ALIGN.CENTER
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(font_size)
    p.font.color.rgb = font_color
    p.font.bold = True
    shape.text_frame.margin_left = Pt(4)
    shape.text_frame.margin_right = Pt(4)
    shape.text_frame.margin_top = Pt(2)
    shape.text_frame.margin_bottom = Pt(2)
    return shape

def arrow_right(slide, x1, y1, x2, y2, color=CYAN):
    connector = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, x1, y1, x2 - x1, y2 - y1)
    connector.fill.solid()
    connector.fill.fore_color.rgb = color
    connector.line.fill.background()
    return connector

def arrow_down(slide, x, y, length, color=CYAN):
    connector = slide.shapes.add_shape(MSO_SHAPE.DOWN_ARROW, x, y, Inches(0.3), length)
    connector.fill.solid()
    connector.fill.fore_color.rgb = color
    connector.line.fill.background()
    return connector

def thin_line(slide, x1, y1, x2, y2, color=CYAN):
    line = slide.shapes.add_connector(1, x1, y1, x2, y2)
    line.line.color.rgb = color
    line.line.width = Pt(1.5)
    return line

def title_slide(prs, title, subtitle):
    slide = blank(prs)
    add_text(slide, Inches(1), Inches(2.2), Inches(11), Inches(1.5), title, size=40, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, Inches(1), Inches(3.8), Inches(11), Inches(1), subtitle, size=20, color=CYAN, align=PP_ALIGN.CENTER)
    thin_line(slide, Inches(3), Inches(3.7), Inches(10.3), Inches(3.7), CYAN)
    return slide

def section_slide(prs, title):
    slide = blank(prs)
    add_text(slide, Inches(1), Inches(2.8), Inches(11), Inches(1.2), title, size=36, color=CYAN, bold=True, align=PP_ALIGN.CENTER)
    thin_line(slide, Inches(4), Inches(4.2), Inches(9.3), Inches(4.2), PURPLE)
    return slide

def agenda_slide(prs, items):
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.4), Inches(5), Inches(0.7), "AGENDA", size=32, color=WHITE, bold=True)
    thin_line(slide, Inches(0.8), Inches(1.1), Inches(12.5), Inches(1.1), CYAN)
    y = Inches(1.4)
    for i, item in enumerate(items):
        c = CYAN if i % 2 == 0 else PURPLE
        box(slide, Inches(1.2), y, Inches(10.5), Inches(0.4), DGRAY, f"{i+1}.  {item}", font_size=13, font_color=LGRAY, border_color=c)
        y += Inches(0.5)
    return slide

def chart_to_image(fig, dpi=150):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight", pad_inches=0.3)
    buf.seek(0)
    plt.close(fig)
    return buf

def embed_chart(slide, fig, left, top, width, height=None):
    buf = chart_to_image(fig)
    pic = slide.shapes.add_picture(buf, left, top, width, height)
    return pic

def content_slide(prs, heading, body_lines):
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), heading, size=28, color=WHITE, bold=True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    y = Inches(1.2)
    for line in body_lines:
        add_text(slide, Inches(1.0), y, Inches(11), Inches(0.4), line, size=14, color=LGRAY)
        y += Inches(0.42)
    return slide

def takeaway_slide(prs, items, heading="Key Takeaways"):
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), heading, size=28, color=WHITE, bold=True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    y = Inches(1.3)
    colors = [CYAN, GREEN, YELLOW, RED, PURPLE, CYAN, GREEN, YELLOW]
    for i, item in enumerate(items):
        box(slide, Inches(1.0), y, Inches(11), Inches(0.45), DGRAY, f"▸  {item}", font_size=13, font_color=LGRAY, border_color=colors[i % len(colors)])
        y += Inches(0.55)
    return slide


# ════════════════════════════════════════════════════════════════════
#  PRESENTATION 3 — Mitigation Bypass & Hardware-Level Attacks
# ════════════════════════════════════════════════════════════════════
def gen_pres_03():
    prs = new_prs()

    # 1 — Title
    title_slide(prs, "Mitigation Bypass &\nHardware-Level Attacks", "Domains 4B, 6, 7  ·  Speculative Execution  ·  CFI/PAC/MTE  ·  Cache Side Channels")

    # 2 — Agenda
    agenda_slide(prs, [
        "Defense-in-Depth Mitigation Stack",
        "Intel CET: Shadow Stack & IBT",
        "ARM PAC & MTE Mechanisms",
        "CFG / XFG / Clang CFI",
        "KASLR & ASLR Bypass Techniques",
        "DEP/W^X Bypass via ROP",
        "Stack Canary & RELRO Bypass",
        "Kernel Mitigation Stack",
        "Spectre & Meltdown Attack Flows",
        "Cache Side-Channel Taxonomy",
        "SGX & Rowhammer Attacks",
        "Microarchitectural Defense Timeline",
    ])

    # 3 — Defense-in-Depth Mitigation Stack
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "Defense-in-Depth Mitigation Stack", size=28, color=WHITE, bold=True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    layers = [
        ("CFI / CET / PAC", PURPLE, "Forward-edge + backward-edge control flow"),
        ("Stack Canaries", YELLOW, "Buffer overflow detection at function return"),
        ("ASLR / KASLR", CYAN, "Randomize virtual address layout each execution"),
        ("DEP / W^X / NX", GREEN, "Non-executable data pages, non-writable code pages"),
        ("RELRO / FORTIFY", RED, "GOT hardening, bounds-checked libc functions"),
        ("Seccomp / Sandboxing", RGBColor(0x80, 0x80, 0xFF), "Syscall filtering, least privilege execution"),
    ]
    y = Inches(1.3)
    for name, color, desc in layers:
        box(slide, Inches(2), y, Inches(9), Inches(0.65), DGRAY, f"{name}  —  {desc}", font_size=13, font_color=LGRAY, border_color=color)
        y += Inches(0.78)
    add_text(slide, Inches(2), y + Inches(0.1), Inches(9), Inches(0.4), "▲  Each layer compensates if the one above is bypassed  ▲", size=12, color=CYAN, align=PP_ALIGN.CENTER)

    # 4 — Intel CET
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "Intel CET — Shadow Stack & IBT", size=28, color=WHITE, bold=True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    # Shadow Stack side
    add_text(slide, Inches(1), Inches(1.2), Inches(5), Inches(0.5), "Shadow Stack (Backward-Edge)", size=18, color=CYAN, bold=True)
    ss_items = [
        ("CALL instruction", "Push return addr to both stacks"),
        ("RET instruction", "Compare shadow vs regular stack"),
        ("Mismatch", "#CP exception → process killed"),
        ("Protected by", "Supervisor shadow stack flag in PTE"),
    ]
    y = Inches(1.8)
    for label, desc in ss_items:
        box(slide, Inches(1.2), y, Inches(2), Inches(0.4), DGRAY, label, font_size=11, font_color=CYAN, border_color=CYAN)
        add_text(slide, Inches(3.4), y, Inches(3), Inches(0.4), desc, size=11, color=LGRAY)
        y += Inches(0.5)
    # IBT side
    add_text(slide, Inches(7), Inches(1.2), Inches(5), Inches(0.5), "IBT — Indirect Branch Tracking (Forward-Edge)", size=18, color=GREEN, bold=True)
    ibt_items = [
        ("Indirect JMP/CALL", "Sets TRACKER state machine"),
        ("Target must start with", "ENDBR64 / ENDBR32"),
        ("Missing ENDBR", "#CP exception → process killed"),
        ("Legacy interop", "NOTRACK prefix + LE bit"),
    ]
    y = Inches(1.8)
    for label, desc in ibt_items:
        box(slide, Inches(7.2), y, Inches(2.2), Inches(0.4), DGRAY, label, font_size=11, font_color=GREEN, border_color=GREEN)
        add_text(slide, Inches(9.6), y, Inches(3), Inches(0.4), desc, size=11, color=LGRAY)
        y += Inches(0.5)
    add_text(slide, Inches(1), Inches(5.5), Inches(11), Inches(0.4), "CET available since Intel Tiger Lake (11th gen, 2020). Requires OS + compiler support. Linux 5.18+, Windows 10+ (Hardware-enforced Stack Protection).", size=12, color=YELLOW)

    # 5 — ARM PAC
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "ARM Pointer Authentication (PAC)", size=28, color=WHITE, bold=True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    # Flow diagram
    steps = [
        ("Pointer\n(48-bit VA)", CYAN),
        ("PAC Key\n(128-bit)", GREEN),
        ("QARMA\nCipher", YELLOW),
        ("PAC Bits\n(7-16 bits)", PURPLE),
        ("Signed\nPointer", RED),
    ]
    x = Inches(0.8)
    for txt, clr in steps:
        box(slide, x, Inches(1.5), Inches(1.8), Inches(0.9), DGRAY, txt, font_size=12, font_color=clr, border_color=clr)
        if x < Inches(9):
            arrow_right(slide, x + Inches(1.9), Inches(1.8), x + Inches(2.4), Inches(1.8), clr)
        x += Inches(2.5)
    add_text(slide, Inches(1), Inches(2.8), Inches(11), Inches(0.4), "64-bit pointer layout:  [PAC bits | upper VA bits | 48-bit virtual address]", size=14, color=LGRAY)
    add_text(slide, Inches(1), Inches(3.3), Inches(11), Inches(0.4), "Keys: APIAKey, APIBKey, APDAKey, APDBKey, APGAKey  —  5 distinct key families in ARMv8.3+", size=13, color=LGRAY)
    pac_attacks = [
        "PACMAN (2022): speculative execution to brute-force PAC without crashing",
        "ForgePAC: signing gadgets that compute valid PACs from leaked keys",
        "PAC bypass via kernel gadgets: find AUT+BR sequence without check",
    ]
    y = Inches(4.0)
    add_text(slide, Inches(1), y - Inches(0.4), Inches(5), Inches(0.4), "Known Bypass Research:", size=16, color=RED, bold=True)
    for item in pac_attacks:
        add_text(slide, Inches(1.2), y, Inches(10.5), Inches(0.35), f"▸ {item}", size=12, color=LGRAY)
        y += Inches(0.38)

    # 6 — ARM MTE
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "ARM Memory Tagging Extension (MTE)", size=28, color=WHITE, bold=True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    # Tag diagram
    box(slide, Inches(1), Inches(1.3), Inches(3), Inches(0.7), DGRAY, "Pointer Tag (4-bit)\nStored in top byte", font_size=12, font_color=CYAN, border_color=CYAN)
    box(slide, Inches(5), Inches(1.3), Inches(3), Inches(0.7), DGRAY, "Memory Tag (4-bit)\nPer 16-byte granule", font_size=12, font_color=GREEN, border_color=GREEN)
    box(slide, Inches(9), Inches(1.3), Inches(3.5), Inches(0.7), DGRAY, "Hardware Compare\nTag match? → proceed\nMismatch? → fault", font_size=11, font_color=RED, border_color=RED)
    arrow_right(slide, Inches(4.1), Inches(1.55), Inches(4.8), Inches(1.55), CYAN)
    arrow_right(slide, Inches(8.1), Inches(1.55), Inches(8.8), Inches(1.55), GREEN)
    modes = [
        ("Synchronous MTE", "Immediate fault on tag mismatch. Precise. High overhead (~3-5%)"),
        ("Asynchronous MTE", "Deferred reporting via TFSR. Lower overhead (~1-2%). Less precise"),
        ("Asymmetric MTE", "Sync for reads, async for writes. Balance precision/performance"),
    ]
    y = Inches(2.5)
    for name, desc in modes:
        box(slide, Inches(1.2), y, Inches(2.5), Inches(0.5), DGRAY, name, font_size=12, font_color=YELLOW, border_color=YELLOW)
        add_text(slide, Inches(4), y, Inches(8), Inches(0.5), desc, size=12, color=LGRAY)
        y += Inches(0.6)
    add_text(slide, Inches(1), Inches(4.8), Inches(11), Inches(1), "MTE detects: heap overflow, use-after-free, double-free, uninitialized memory access.\nPixel 8 = first production device with MTE (2023). Android 14+ supports MTE in userspace.\n4-bit tag = 1/16 probability of collision (brute-force requires ~16 attempts on average).", size=13, color=LGRAY)

    # 7 — CFG/XFG bitmap
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "Windows CFG / XFG Architecture", size=28, color=WHITE, bold=True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    cfg_flow = [
        ("Indirect Call\nSite", CYAN),
        ("CFG Bitmap\nLookup", GREEN),
        ("Valid Target?\nCheck bit", YELLOW),
        ("Call\nProceeds", GREEN),
    ]
    x = Inches(1)
    for txt, clr in cfg_flow:
        box(slide, x, Inches(1.3), Inches(2.2), Inches(0.8), DGRAY, txt, font_size=12, font_color=clr, border_color=clr)
        if x < Inches(8):
            arrow_right(slide, x + Inches(2.3), Inches(1.6), x + Inches(2.9), Inches(1.6), clr)
        x += Inches(3)
    add_text(slide, Inches(1), Inches(2.5), Inches(11), Inches(0.4), "CFG (Control Flow Guard): 1-bit per 8-byte aligned address. Coarse-grained.", size=14, color=LGRAY)
    add_text(slide, Inches(1), Inches(3.0), Inches(11), Inches(0.4), "XFG (Xtended Flow Guard): adds type hash — indirect call must match function prototype.", size=14, color=LGRAY)
    add_text(slide, Inches(1), Inches(3.5), Inches(5), Inches(0.4), "CFG Bypasses:", size=16, color=RED, bold=True)
    bypasses = [
        "Call existing valid targets (JIT code, longjmp, coroutines)",
        "Abuse 8-byte granularity to land at unintended instruction boundary",
        "Mark writable pages as valid via VirtualAlloc/VirtualProtect",
        "XFG hash collision: find valid target with matching type signature",
    ]
    y = Inches(4.0)
    for b in bypasses:
        add_text(slide, Inches(1.2), y, Inches(10), Inches(0.35), f"▸ {b}", size=12, color=LGRAY)
        y += Inches(0.38)

    # 8 — Clang CFI
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "Clang CFI — Type-Based Control Flow Integrity", size=28, color=WHITE, bold=True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    cfi_schemes = [
        ("cfi-vcall", "Virtual call check — vtable pointer must reference valid vtable for the static type", CYAN),
        ("cfi-nvcall", "Non-virtual member call — validate derived class pointer", GREEN),
        ("cfi-derived-cast", "Derived cast check — static_cast must be valid", YELLOW),
        ("cfi-unrelated-cast", "Unrelated cast check — reinterpret_cast validation", PURPLE),
        ("cfi-icall", "Indirect call — function pointer must match expected signature", RED),
    ]
    y = Inches(1.3)
    for scheme, desc, clr in cfi_schemes:
        box(slide, Inches(1), y, Inches(2.2), Inches(0.5), DGRAY, scheme, font_size=11, font_color=clr, border_color=clr)
        add_text(slide, Inches(3.5), y, Inches(9), Inches(0.5), desc, size=12, color=LGRAY)
        y += Inches(0.6)
    add_text(slide, Inches(1), y + Inches(0.2), Inches(11), Inches(1), "Requires LTO (Link-Time Optimization) for cross-module enforcement.\nAndroid uses Clang CFI for kernel (KCFI) since Android 13.\nBypass: type confusion within same CFI equivalence class.", size=13, color=LGRAY)

    # 9 — KASLR bypass chart
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "KASLR Bypass Techniques — Comparison", size=28, color=WHITE, bold=True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    mpl_theme()
    fig, ax = plt.subplots(figsize=(10, 4.5))
    techniques = ["Info Leak\n(/proc, dmesg)", "Prefetch\nSide Channel", "TSX-based\nTiming", "EntryBleed\n(CVE-2022-4543)", "Uninitialized\nStack Data", "Spectre v1\nGadget"]
    effectiveness = [95, 75, 85, 90, 70, 80]
    colors_hex = ["#00D4FF", "#FF4444", "#00FF88", "#FFD700", "#BB86FC", "#00D4FF"]
    bars = ax.barh(techniques, effectiveness, color=colors_hex, edgecolor="#444466", height=0.6)
    ax.set_xlabel("Reliability (%)", fontsize=12)
    ax.set_xlim(0, 100)
    ax.set_title("KASLR Bypass Technique Effectiveness", fontsize=14, color="#00D4FF")
    ax.grid(axis="x", alpha=0.3)
    for bar, val in zip(bars, effectiveness):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2, f"{val}%", va="center", fontsize=10, color="#cccccc")
    embed_chart(slide, fig, Inches(1.5), Inches(1.2), Inches(10), Inches(5.5))

    # 10 — ASLR entropy
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "ASLR Entropy Comparison", size=28, color=WHITE, bold=True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    mpl_theme()
    fig, ax = plt.subplots(figsize=(10, 4.5))
    categories = ["Stack\n32-bit", "Stack\n64-bit", "Heap\n32-bit", "Heap\n64-bit", "mmap\n32-bit", "mmap\n64-bit", "PIE Base\n32-bit", "PIE Base\n64-bit"]
    entropy_bits = [19, 30, 13, 28, 8, 28, 8, 28]
    colors_e = ["#FF4444", "#00D4FF", "#FF4444", "#00D4FF", "#FF4444", "#00D4FF", "#FF4444", "#00D4FF"]
    bars = ax.bar(categories, entropy_bits, color=colors_e, edgecolor="#444466", width=0.6)
    ax.set_ylabel("Entropy (bits)", fontsize=12)
    ax.set_title("ASLR Entropy by Region (Linux)", fontsize=14, color="#00D4FF")
    ax.grid(axis="y", alpha=0.3)
    for bar, val in zip(bars, entropy_bits):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, str(val), ha="center", fontsize=10, color="#cccccc")
    embed_chart(slide, fig, Inches(1.5), Inches(1.2), Inches(10), Inches(5.5))

    # 11 — DEP/W^X bypass via ROP
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "DEP / W^X Bypass via ROP Chain", size=28, color=WHITE, bold=True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    rop_steps = [
        ("Buffer\nOverflow", RED, "Corrupt return address"),
        ("Gadget 1:\npop rdi; ret", CYAN, "Load /bin/sh address"),
        ("Gadget 2:\npop rsi; ret", GREEN, "Set argv = NULL"),
        ("Gadget 3:\npop rdx; ret", YELLOW, "Set envp = NULL"),
        ("execve\nsyscall", PURPLE, "Execute shell"),
    ]
    x = Inches(0.5)
    for txt, clr, desc in rop_steps:
        box(slide, x, Inches(1.4), Inches(2.0), Inches(0.8), DGRAY, txt, font_size=11, font_color=clr, border_color=clr)
        add_text(slide, x, Inches(2.3), Inches(2.0), Inches(0.4), desc, size=10, color=LGRAY, align=PP_ALIGN.CENTER)
        if x < Inches(9):
            arrow_right(slide, x + Inches(2.1), Inches(1.7), x + Inches(2.5), Inches(1.7), clr)
        x += Inches(2.5)
    add_text(slide, Inches(1), Inches(3.2), Inches(11), Inches(2.5),
        "ROP works because DEP only prevents execution of data — existing code (gadgets) is still executable.\n\n"
        "Advanced variants:\n"
        "▸ JOP (Jump-Oriented Programming): uses indirect jumps, no return instructions\n"
        "▸ SROP (Sigreturn-Oriented Programming): single sigreturn gadget → control all registers\n"
        "▸ BROP (Blind ROP): brute-force gadgets over network without binary access\n"
        "▸ ret2dlresolve: forge relocation entries to resolve arbitrary library functions\n\n"
        "Countered by: CET shadow stack (ROP), IBT (JOP), CFI (both), ASLR (all — raises cost)",
        size=13, color=LGRAY)

    # 12 — Stack Canary Bypass
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "Stack Canary Bypass Methods", size=28, color=WHITE, bold=True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    bypasses = [
        ("Information Leak", "Read canary via format string (%p), out-of-bounds read, or /proc/self/mem", CYAN),
        ("Byte-by-Byte Brute Force", "Fork-based servers: child inherits canary → try 256 values per byte × 8 bytes", GREEN),
        ("Overwrite Past Canary", "Corrupt function pointer or local variable before canary check", YELLOW),
        ("Canary-less Functions", "Small functions, leaf functions may not have canaries (-fno-stack-protector)", RED),
        ("Thread-Local Bypass", "Overwrite __stack_chk_guard in TLS (adjacent to stack on some archs)", PURPLE),
        ("Signal Handler Abuse", "Trigger signal before __stack_chk_fail → hijack execution", RGBColor(0x80, 0x80, 0xFF)),
    ]
    y = Inches(1.3)
    for name, desc, clr in bypasses:
        box(slide, Inches(1), y, Inches(2.8), Inches(0.5), DGRAY, name, font_size=11, font_color=clr, border_color=clr)
        add_text(slide, Inches(4.1), y, Inches(8.5), Inches(0.5), desc, size=12, color=LGRAY)
        y += Inches(0.6)

    # 13 — RELRO Bypass
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "RELRO Bypass Techniques", size=28, color=WHITE, bold=True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    # Partial vs Full comparison
    box(slide, Inches(1), Inches(1.3), Inches(5.5), Inches(0.6), DGRAY, "Partial RELRO  (gcc default)", font_size=14, font_color=YELLOW, border_color=YELLOW)
    add_text(slide, Inches(1.2), Inches(2.1), Inches(5.3), Inches(2),
        "▸ .got → read-only (non-PLT GOT entries)\n"
        "▸ .got.plt → still WRITABLE\n"
        "▸ Attacker: overwrite .got.plt entries\n"
        "▸ Bypass: any arbitrary write primitive",
        size=12, color=LGRAY)
    box(slide, Inches(7), Inches(1.3), Inches(5.5), Inches(0.6), DGRAY, "Full RELRO  (-z now)", font_size=14, font_color=GREEN, border_color=GREEN)
    add_text(slide, Inches(7.2), Inches(2.1), Inches(5.3), Inches(2),
        "▸ All GOT entries resolved at load time\n"
        "▸ Entire .got and .got.plt → read-only\n"
        "▸ Attacker: cannot overwrite GOT\n"
        "▸ Bypass: __free_hook, __malloc_hook (removed glibc 2.34+),\n"
        "   ld.so internal structures, or target non-GOT pointers",
        size=12, color=LGRAY)
    add_text(slide, Inches(1), Inches(4.8), Inches(11), Inches(1.5),
        "Post-glibc 2.34 landscape: hooks removed, Full RELRO + PIE standard.\n"
        "Modern bypass targets: _IO_FILE vtable corruption (FSOP), TLS-DTV, ld.so _r_debug,\n"
        "exit handlers (__exit_funcs), custom allocator metadata.\n\n"
        "Detection: checksec (pwntools), readelf -l (GNU_RELRO segment), readelf -d (BIND_NOW flag).",
        size=13, color=LGRAY)

    # 14 — Kernel Mitigation Stack
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "Linux Kernel Mitigation Stack", size=28, color=WHITE, bold=True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    kmits = [
        ("KASLR", "Randomize kernel base by up to 1GB (x86_64). ~9 bits entropy", CYAN),
        ("SMEP", "Supervisor Mode Execution Prevention — no exec of userspace code from ring 0", GREEN),
        ("SMAP", "Supervisor Mode Access Prevention — no read/write userspace from ring 0", YELLOW),
        ("KPTI", "Kernel Page Table Isolation — separate page tables for user/kernel (Meltdown fix)", RED),
        ("KCFI", "Kernel CFI — Clang's type-based CFI for indirect calls in kernel", PURPLE),
        ("Stack Protector", "Per-task canary, __stack_chk_guard in task_struct", RGBColor(0x80, 0x80, 0xFF)),
        ("RANDSTRUCT", "Randomize layout of sensitive kernel structs at compile time", CYAN),
        ("Hardened Usercopy", "Validate user ↔ kernel copy bounds against slab metadata", GREEN),
    ]
    y = Inches(1.2)
    for name, desc, clr in kmits:
        box(slide, Inches(1), y, Inches(1.8), Inches(0.45), DGRAY, name, font_size=11, font_color=clr, border_color=clr)
        add_text(slide, Inches(3.1), y, Inches(9.5), Inches(0.45), desc, size=12, color=LGRAY)
        y += Inches(0.55)

    # 15 — Section divider
    section_slide(prs, "Speculative Execution &\nHardware Attacks")

    # 16 — Spectre v1
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "Spectre v1 — Bounds Check Bypass", size=28, color=WHITE, bold=True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    spectre_steps = [
        ("Attacker trains\nbranch predictor", RED),
        ("Victim executes\nbounds check", CYAN),
        ("Speculative\nOOB access", YELLOW),
        ("Data-dependent\ncache load", GREEN),
        ("Flush+Reload\nrecovers secret", PURPLE),
    ]
    x = Inches(0.5)
    for txt, clr in spectre_steps:
        box(slide, x, Inches(1.4), Inches(2.0), Inches(0.9), DGRAY, txt, font_size=11, font_color=clr, border_color=clr)
        if x < Inches(9):
            arrow_right(slide, x + Inches(2.1), Inches(1.75), x + Inches(2.4), Inches(1.75), clr)
        x += Inches(2.5)
    add_text(slide, Inches(1), Inches(2.8), Inches(11), Inches(3),
        "if (x < array1_size)  →  y = array2[array1[x] * 256]\n\n"
        "Speculative window: CPU executes past branch before branch resolves.\n"
        "Even though result is architecturally discarded, cache state persists.\n\n"
        "Mitigations:\n"
        "▸ lfence / speculation barrier after bounds check\n"
        "▸ Array index masking (x & (size-1))\n"
        "▸ Retpoline (Spectre v2 — indirect branch)\n"
        "▸ IBRS / STIBP / IBPB (microcode-level)\n"
        "▸ BHI_DIS_S, RRSBA mitigation (newer variants)",
        size=13, color=LGRAY)

    # 17 — Meltdown
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "Meltdown — Rogue Data Cache Load (CVE-2017-5754)", size=28, color=WHITE, bold=True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    melt_steps = [
        ("Userspace\nprocess", CYAN),
        ("Access kernel\nmemory (faults)", RED),
        ("CPU speculatively\nloads value", YELLOW),
        ("Use value as\ncache oracle", GREEN),
        ("Recover byte\nvia timing", PURPLE),
    ]
    x = Inches(0.5)
    for txt, clr in melt_steps:
        box(slide, x, Inches(1.4), Inches(2.0), Inches(0.8), DGRAY, txt, font_size=11, font_color=clr, border_color=clr)
        if x < Inches(9):
            arrow_right(slide, x + Inches(2.1), Inches(1.7), x + Inches(2.4), Inches(1.7), clr)
        x += Inches(2.5)
    add_text(slide, Inches(1), Inches(2.8), Inches(11), Inches(2.5),
        "Exploits the race between permission check and speculative execution.\n"
        "Kernel virtual memory mapped into every process (for syscall performance).\n"
        "Out-of-order execution reads kernel data before fault is raised.\n\n"
        "Impact: Read arbitrary kernel memory from userspace at ~500 KB/s.\n"
        "Affected: Intel (most pre-2019), some ARM. AMD largely unaffected.\n\n"
        "Fix: KPTI (Kernel Page Table Isolation) — separate page tables for user/kernel.\n"
        "Performance cost: 5-30% depending on syscall frequency.",
        size=13, color=LGRAY)

    # 18 — Spectre variant comparison chart
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "Spectre / Meltdown Variant Landscape", size=28, color=WHITE, bold=True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    variants = [
        ("Spectre v1 (BCB)", "2018", "Bounds Check Bypass", "lfence, masking"),
        ("Spectre v2 (BTI)", "2018", "Branch Target Injection", "Retpoline, IBRS, eIBRS"),
        ("Meltdown (RDCL)", "2018", "Rogue Data Cache Load", "KPTI"),
        ("Spectre v4 (SSB)", "2018", "Speculative Store Bypass", "SSBD bit"),
        ("MDS/RIDL/Fallout", "2019", "Microarch Data Sampling", "Verw, buffer overwrite"),
        ("LVI", "2020", "Load Value Injection", "lfence everywhere"),
        ("Retbleed", "2022", "Return prediction bypass", "IBPB, eIBRS+retpoline"),
        ("Downfall (GDS)", "2023", "Gather Data Sampling", "Microcode update"),
        ("Inception", "2023", "Phantom speculation (AMD)", "Safe RET, IBPB"),
        ("BHI (Spectre-BHB)", "2024", "Branch History Injection", "BHI_DIS_S"),
    ]
    y = Inches(1.2)
    headers = ["Variant", "Year", "Mechanism", "Primary Mitigation"]
    hx = [Inches(0.8), Inches(3.5), Inches(4.8), Inches(8.2)]
    for i, h in enumerate(headers):
        add_text(slide, hx[i], y, Inches(3), Inches(0.35), h, size=12, color=CYAN, bold=True)
    y += Inches(0.4)
    thin_line(slide, Inches(0.8), y, Inches(12.5), y, MGRAY)
    y += Inches(0.05)
    for name, year, mech, mit in variants:
        add_text(slide, hx[0], y, Inches(2.7), Inches(0.3), name, size=10, color=WHITE, bold=True)
        add_text(slide, hx[1], y, Inches(1.2), Inches(0.3), year, size=10, color=LGRAY)
        add_text(slide, hx[2], y, Inches(3.3), Inches(0.3), mech, size=10, color=LGRAY)
        add_text(slide, hx[3], y, Inches(4), Inches(0.3), mit, size=10, color=LGRAY)
        y += Inches(0.35)

    # 19 — Cache Side-Channel Taxonomy
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "Cache Side-Channel Taxonomy", size=28, color=WHITE, bold=True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    channels = [
        ("Flush+Reload", "Shared memory. Flush target line → victim executes → time reload. Precise, cross-core.", CYAN),
        ("Prime+Probe", "No shared memory needed. Fill cache set → victim evicts → probe for eviction. Noisier.", GREEN),
        ("Evict+Reload", "Like Flush+Reload but uses eviction instead of clflush. Works without clflush.", YELLOW),
        ("Flush+Flush", "Measure clflush time itself (cached vs uncached). Stealthier — no memory access.", RED),
        ("Cache Occupancy", "Monitor total cache pressure. Coarse-grained. Used for keystroke timing.", PURPLE),
    ]
    y = Inches(1.3)
    for name, desc, clr in channels:
        box(slide, Inches(1), y, Inches(2.2), Inches(0.5), DGRAY, name, font_size=12, font_color=clr, border_color=clr)
        add_text(slide, Inches(3.5), y, Inches(9), Inches(0.5), desc, size=12, color=LGRAY)
        y += Inches(0.6)
    add_text(slide, Inches(1), Inches(4.6), Inches(11), Inches(1),
        "All exploit timing differences between cache hit (~4 cycles) and cache miss (~200+ cycles).\n"
        "Flush+Reload requires shared pages (dedup, shared libs) — most precise at ~byte granularity.\n"
        "Prime+Probe works across VMs (L3 cache shared) — used in cloud cross-tenant attacks.",
        size=13, color=LGRAY)

    # 20 — SGX Attack Surface
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "Intel SGX — Enclave Attack Surface", size=28, color=WHITE, bold=True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    box(slide, Inches(4.5), Inches(1.3), Inches(4), Inches(0.8), DGRAY, "SGX Enclave\n(Encrypted Memory Region)", font_size=13, font_color=GREEN, border_color=GREEN)
    attacks = [
        ("Controlled-Channel\n(Page Fault)", Inches(1), Inches(2.8), RED),
        ("SGAxe / CacheOut\n(L1D Eviction)", Inches(4.5), Inches(2.8), YELLOW),
        ("Plundervolt\n(Voltage Glitch)", Inches(8), Inches(2.8), PURPLE),
        ("SmashEx\n(Async Exception)", Inches(1), Inches(4.2), CYAN),
        ("Enclave Interface\n(ECALL Fuzzing)", Inches(4.5), Inches(4.2), GREEN),
        ("AEX-Notify\n(Interrupt Storm)", Inches(8), Inches(4.2), RED),
    ]
    for txt, ax, ay, clr in attacks:
        box(slide, ax, ay, Inches(3), Inches(0.7), DGRAY, txt, font_size=11, font_color=clr, border_color=clr)
    add_text(slide, Inches(1), Inches(5.5), Inches(11), Inches(1),
        "SGX deprecated on 12th+ gen Intel (Alder Lake). Replaced by TDX for VM-level confidential computing.\n"
        "Key lesson: hardware isolation without side-channel resistance is insufficient.",
        size=13, color=YELLOW)

    # 21 — Rowhammer
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "Rowhammer — DRAM Disturbance Attack", size=28, color=WHITE, bold=True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    row_steps = [
        ("Aggressor Row\nRepeated Access", RED),
        ("Charge Leakage\n→ Adjacent Rows", YELLOW),
        ("Bit Flip in\nVictim Row", PURPLE),
        ("Exploit:\nPTE Manipulation", GREEN),
    ]
    x = Inches(1)
    for txt, clr in row_steps:
        box(slide, x, Inches(1.4), Inches(2.5), Inches(0.8), DGRAY, txt, font_size=12, font_color=clr, border_color=clr)
        if x < Inches(8):
            arrow_right(slide, x + Inches(2.6), Inches(1.7), x + Inches(3.0), Inches(1.7), clr)
        x += Inches(3.1)
    add_text(slide, Inches(1), Inches(2.8), Inches(11), Inches(3),
        "DRAM cells store bits as charge in capacitors. Repeated row activations cause charge leakage\n"
        "into physically adjacent rows, flipping bits in victim rows.\n\n"
        "Exploitation: flip PTE bits → gain write access to page table → arbitrary kernel R/W.\n"
        "Variants: single-sided, double-sided, one-location, TRRespass, Half-Double, Blacksmith.\n\n"
        "Mitigations:\n"
        "▸ ECC RAM (detects single-bit, corrects — but multiple flips bypass)\n"
        "▸ TRR (Target Row Refresh) — hardware mitigation, repeatedly bypassed\n"
        "▸ LPDDR5 / DDR5: per-row refresh counters, RFM (Refresh Management)\n"
        "▸ Software: memory isolation, guard rows, DRAMA-based detection",
        size=13, color=LGRAY)

    # 22 — Timeline chart
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "Microarchitectural Attack & Defense Timeline", size=28, color=WHITE, bold=True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    mpl_theme()
    fig, ax = plt.subplots(figsize=(11, 4.5))
    years = [2014, 2016, 2018, 2018, 2019, 2020, 2021, 2022, 2023, 2023, 2024]
    events = ["Rowhammer\ndiscovered", "Flip Feng\nShui", "Spectre/\nMeltdown", "KPTI\ndeployed", "MDS/\nRIDL", "LVI\nattack", "Transient\nExec. Survey", "Retbleed\n(AMD/Intel)", "Downfall\n(GDS)", "Inception\n(AMD)", "BHI\n(Spectre-BHB)"]
    colors_t = ["#FF4444", "#FF4444", "#FF4444", "#00FF88", "#FF4444", "#FF4444", "#FFD700", "#FF4444", "#FF4444", "#FF4444", "#FF4444"]
    ax.scatter(years, range(len(years)), c=colors_t, s=80, zorder=3)
    for i, (y, evt) in enumerate(zip(years, events)):
        ax.annotate(evt, (y, i), textcoords="offset points", xytext=(15, -5), fontsize=8, color="#cccccc")
    ax.set_xlabel("Year", fontsize=12)
    ax.set_title("Hardware Vulnerability Discovery Timeline", fontsize=14, color="#00D4FF")
    ax.set_yticks([])
    ax.grid(axis="x", alpha=0.3)
    embed_chart(slide, fig, Inches(1), Inches(1.2), Inches(11.3), Inches(5.5))

    # 23 — Cross-reference
    takeaway_slide(prs, [
        "Domain 1-2: ELF/PE binary formats → understanding PLT/GOT for RELRO bypass context",
        "Domain 3: Stack/heap corruption → the vulnerability classes these mitigations address",
        "Domain 4A: ROP/JOP/SROP — the code reuse attacks CET/PAC/CFI are designed to stop",
        "Domain 5: Kernel exploitation → SMEP/SMAP/KPTI are the kernel-side mitigations",
        "Domain 6B: Kernel mitigation bypass — extends this presentation with KASLR/kCFI specifics",
        "Domain 11: EDR evasion → attackers bypass these mitigations in practice",
        "Domain 14: Windows enterprise — CFG/XFG are the Windows-specific implementations",
        "Domain 26: Vuln research — exploit developers must defeat these mitigations",
    ], heading="Cross-Reference Map")

    out = "/media/renan/New Volume/PROIECT/STUDIO-LAVORO/library/15-SECURITY/presentations/03_Mitigation_Bypass_Hardware.pptx"
    prs.save(out)
    print(f"[+] Saved {out.split('/')[-1]}")


# ════════════════════════════════════════════════════════════════════
#  PRESENTATION 4 — Web Application & Network Security
# ════════════════════════════════════════════════════════════════════
def gen_pres_04():
    prs = new_prs()

    # 1 — Title
    title_slide(prs, "Web Application &\nNetwork Security", "Domains 8-9  ·  OWASP Top 10  ·  Browser Internals  ·  Protocol Attacks")

    # 2 — Agenda
    agenda_slide(prs, [
        "OWASP Top 10 (2021)",
        "XSS Types & Attack Flows",
        "SQL Injection Mechanics",
        "SSRF Attack Chain",
        "OAuth 2.0 & JWT Attacks",
        "CSP & Browser Security Model",
        "V8 Engine & Chrome Sandbox",
        "TCP/IP Attack Surface",
        "DNS Attack Taxonomy",
        "TLS 1.3 Handshake",
        "Wireless & SDN Security",
    ])

    # 3 — OWASP Top 10 chart
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "OWASP Top 10 — 2021", size=28, color=WHITE, bold=True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    mpl_theme()
    fig, ax = plt.subplots(figsize=(10, 5))
    owasp = [
        "A01: Broken\nAccess Control", "A02: Crypto\nFailures", "A03:\nInjection",
        "A04: Insecure\nDesign", "A05: Security\nMisconfig", "A06: Vulnerable\nComponents",
        "A07: Auth\nFailures", "A08: Software\nIntegrity", "A09: Logging\nFailures",
        "A10: SSRF"
    ]
    incidence = [94.55, 72.21, 69.09, 65.34, 62.12, 58.74, 55.41, 47.22, 42.51, 38.19]
    colors_o = ["#FF4444", "#FF4444", "#FF4444", "#FFD700", "#FFD700", "#FFD700", "#00D4FF", "#00D4FF", "#BB86FC", "#BB86FC"]
    bars = ax.barh(owasp[::-1], incidence[::-1], color=colors_o[::-1], edgecolor="#444466", height=0.6)
    ax.set_xlabel("Incidence Rate (%)", fontsize=12)
    ax.set_title("OWASP Top 10 2021 — Incidence Rate", fontsize=14, color="#00D4FF")
    ax.set_xlim(0, 100)
    ax.grid(axis="x", alpha=0.3)
    for bar, val in zip(bars, incidence[::-1]):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2, f"{val}%", va="center", fontsize=9, color="#cccccc")
    embed_chart(slide, fig, Inches(1.5), Inches(1.2), Inches(10), Inches(5.5))

    # 4 — XSS types
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "Cross-Site Scripting (XSS) — Type Comparison", size=28, color=WHITE, bold=True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    xss_types = [
        ("Reflected XSS", [
            ("Attacker crafts\nmalicious URL", RED),
            ("Victim clicks\nlink", CYAN),
            ("Server reflects\ninput in response", YELLOW),
            ("Browser executes\nscript", PURPLE),
        ]),
        ("Stored XSS", [
            ("Attacker submits\npayload", RED),
            ("Server stores\nin database", CYAN),
            ("Other users\nrequest page", YELLOW),
            ("Payload served\nto all victims", PURPLE),
        ]),
        ("DOM-based XSS", [
            ("Attacker crafts\nURL fragment", RED),
            ("Client JS reads\nlocation.hash", CYAN),
            ("JS writes to\ninnerHTML/eval", YELLOW),
            ("Script executes\nclient-side only", PURPLE),
        ]),
    ]
    y_start = Inches(1.3)
    for label, steps in xss_types:
        add_text(slide, Inches(0.5), y_start, Inches(2), Inches(0.4), label, size=13, color=CYAN, bold=True)
        x = Inches(2.5)
        for txt, clr in steps:
            box(slide, x, y_start, Inches(2.2), Inches(0.65), DGRAY, txt, font_size=10, font_color=clr, border_color=clr)
            if x < Inches(9):
                arrow_right(slide, x + Inches(2.3), y_start + Inches(0.25), x + Inches(2.5), y_start + Inches(0.25), clr)
            x += Inches(2.7)
        y_start += Inches(0.9)
    add_text(slide, Inches(0.5), y_start + Inches(0.2), Inches(12), Inches(1),
        "Defense: Context-aware output encoding, CSP with nonce, Trusted Types API, DOMPurify for sanitization.\n"
        "Reflected/Stored: server-side escaping. DOM-based: avoid dangerous sinks (innerHTML, eval, document.write).",
        size=12, color=LGRAY)

    # 5 — SQL Injection
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "SQL Injection — Attack Flow", size=28, color=WHITE, bold=True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    sqli_steps = [
        ("User Input\n' OR 1=1 --", RED),
        ("String\nConcatenation", YELLOW),
        ("Malformed\nSQL Query", PURPLE),
        ("Database\nExfiltration", GREEN),
    ]
    x = Inches(1)
    for txt, clr in sqli_steps:
        box(slide, x, Inches(1.4), Inches(2.5), Inches(0.8), DGRAY, txt, font_size=12, font_color=clr, border_color=clr)
        if x < Inches(8):
            arrow_right(slide, x + Inches(2.6), Inches(1.7), x + Inches(3.0), Inches(1.7), clr)
        x += Inches(3.1)
    sqli_variants = [
        ("Union-Based", "UNION SELECT to extract data from other tables", CYAN),
        ("Error-Based", "Trigger verbose errors that leak data", RED),
        ("Blind Boolean", "Infer data from true/false response differences", GREEN),
        ("Blind Time-Based", "SLEEP/BENCHMARK to infer data via response timing", YELLOW),
        ("Out-of-Band", "DNS/HTTP exfiltration via LOAD_FILE, UTL_HTTP", PURPLE),
        ("Second-Order", "Stored payload triggered in different query context", RGBColor(0x80, 0x80, 0xFF)),
    ]
    y = Inches(2.8)
    for name, desc, clr in sqli_variants:
        box(slide, Inches(1), y, Inches(2.2), Inches(0.4), DGRAY, name, font_size=11, font_color=clr, border_color=clr)
        add_text(slide, Inches(3.5), y, Inches(9), Inches(0.4), desc, size=12, color=LGRAY)
        y += Inches(0.5)
    add_text(slide, Inches(1), Inches(5.8), Inches(11), Inches(0.5), "Defense: Parameterized queries / prepared statements. NEVER string concatenation. WAF as defense-in-depth only.", size=13, color=YELLOW)

    # 6 — SSRF Attack Chain
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "Server-Side Request Forgery (SSRF) Attack Chain", size=28, color=WHITE, bold=True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    ssrf_flow = [
        ("Attacker sends\nURL to app", RED),
        ("App fetches\nattacker URL", YELLOW),
        ("Target:\n169.254.169.254", CYAN),
        ("Cloud metadata\ncredentials", GREEN),
        ("Lateral movement\nvia stolen creds", PURPLE),
    ]
    x = Inches(0.5)
    for txt, clr in ssrf_flow:
        box(slide, x, Inches(1.4), Inches(2.0), Inches(0.8), DGRAY, txt, font_size=11, font_color=clr, border_color=clr)
        if x < Inches(9):
            arrow_right(slide, x + Inches(2.1), Inches(1.7), x + Inches(2.4), Inches(1.7), clr)
        x += Inches(2.5)
    add_text(slide, Inches(1), Inches(2.8), Inches(11), Inches(3),
        "Capital One breach (2019): SSRF → EC2 metadata → IAM role credentials → S3 bucket access → 106M records.\n\n"
        "SSRF targets beyond cloud metadata:\n"
        "▸ Internal services (Redis, Elasticsearch, Consul — often no auth on localhost)\n"
        "▸ File:// protocol → local file read (e.g., /etc/passwd, /proc/self/environ)\n"
        "▸ Gopher:// → interact with TCP services (memcached, SMTP)\n"
        "▸ DNS rebinding → bypass allowlist by resolving to internal IP after check\n\n"
        "Defense: IMDSv2 (token-required), allowlist outbound URLs, disable unnecessary protocols,\n"
        "network-level egress filtering, avoid passing raw URLs from user input.",
        size=13, color=LGRAY)

    # 7 — OAuth 2.0
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "OAuth 2.0 Authorization Code Flow", size=28, color=WHITE, bold=True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    actors = [
        ("Client\n(App)", Inches(0.5), CYAN),
        ("Authorization\nServer", Inches(4.5), GREEN),
        ("Resource\nServer", Inches(9), YELLOW),
    ]
    for txt, x_pos, clr in actors:
        box(slide, x_pos, Inches(1.3), Inches(2.5), Inches(0.7), DGRAY, txt, font_size=13, font_color=clr, border_color=clr)
    flow_steps = [
        ("1. Auth request + PKCE challenge", Inches(1.3), Inches(2.3), Inches(4.5), Inches(2.3), CYAN),
        ("2. User authenticates + consents", Inches(4.5), Inches(2.7), Inches(4.5), Inches(3.0), GREEN),
        ("3. Auth code returned to redirect_uri", Inches(4.5), Inches(3.2), Inches(1.3), Inches(3.2), GREEN),
        ("4. Exchange code + PKCE verifier for tokens", Inches(1.3), Inches(3.6), Inches(4.5), Inches(3.6), CYAN),
        ("5. Access token + refresh token", Inches(4.5), Inches(4.0), Inches(1.3), Inches(4.0), GREEN),
        ("6. API request with Bearer token", Inches(1.3), Inches(4.4), Inches(9), Inches(4.4), YELLOW),
    ]
    for label, x1, y1, x2, y2, clr in flow_steps:
        add_text(slide, min(x1, x2), y1 - Inches(0.15), Inches(5), Inches(0.3), label, size=10, color=clr)
    add_text(slide, Inches(0.5), Inches(5.0), Inches(12), Inches(1.5),
        "Attacks: authorization code interception, redirect_uri manipulation, token leakage via referrer,\n"
        "state parameter CSRF, implicit flow token exposure, client_secret compromise.\n\n"
        "Defense: PKCE (RFC 7636) mandatory, exact redirect_uri match, short-lived access tokens,\n"
        "token binding, DPoP (RFC 9449), avoid implicit grant entirely.",
        size=12, color=LGRAY)

    # 8 — JWT
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "JWT Structure & Attack Surface", size=28, color=WHITE, bold=True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    jwt_parts = [
        ("HEADER\n{\"alg\":\"RS256\",\n\"typ\":\"JWT\"}", RED, "Base64url encoded"),
        ("PAYLOAD\n{\"sub\":\"1234\",\n\"role\":\"admin\"}", CYAN, "Claims (not encrypted!)"),
        ("SIGNATURE\nHMAC/RSA/ECDSA\nover header.payload", GREEN, "Integrity verification"),
    ]
    x = Inches(0.5)
    for txt, clr, desc in jwt_parts:
        box(slide, x, Inches(1.3), Inches(3.5), Inches(1.2), DGRAY, txt, font_size=11, font_color=clr, border_color=clr)
        add_text(slide, x, Inches(2.6), Inches(3.5), Inches(0.35), desc, size=11, color=LGRAY, align=PP_ALIGN.CENTER)
        x += Inches(4.2)
    attacks_jwt = [
        ("alg: none", "Set algorithm to 'none' — server accepts unsigned token", RED),
        ("Key Confusion", "RS256→HS256: use RSA public key as HMAC secret", YELLOW),
        ("JWK Header Injection", "Embed attacker's public key in JWK/JKU header field", PURPLE),
        ("Weak Secret Brute Force", "hashcat -m 16500 → crack HS256 shared secrets", CYAN),
        ("Claim Tampering", "Modify 'role', 'sub', or 'exp' claims if signature not verified", GREEN),
    ]
    y = Inches(3.2)
    for name, desc, clr in attacks_jwt:
        box(slide, Inches(1), y, Inches(2.5), Inches(0.45), DGRAY, name, font_size=11, font_color=clr, border_color=clr)
        add_text(slide, Inches(3.8), y, Inches(8.5), Inches(0.45), desc, size=12, color=LGRAY)
        y += Inches(0.55)

    # 9 — CSP Architecture
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "Content Security Policy (CSP) Architecture", size=28, color=WHITE, bold=True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    directives = [
        ("default-src", "Fallback for all resource types", CYAN),
        ("script-src", "JavaScript execution (most critical)", RED),
        ("style-src", "CSS stylesheets", GREEN),
        ("img-src", "Images", YELLOW),
        ("connect-src", "XHR, WebSocket, fetch()", PURPLE),
        ("frame-src", "iframe embedding", RGBColor(0x80, 0x80, 0xFF)),
        ("object-src", "Plugins (Flash, Java — should be 'none')", RED),
        ("base-uri", "Base URL restriction (prevent base tag injection)", YELLOW),
    ]
    y = Inches(1.2)
    for name, desc, clr in directives:
        box(slide, Inches(1), y, Inches(2), Inches(0.4), DGRAY, name, font_size=11, font_color=clr, border_color=clr)
        add_text(slide, Inches(3.3), y, Inches(9), Inches(0.4), desc, size=12, color=LGRAY)
        y += Inches(0.5)
    add_text(slide, Inches(1), Inches(5.4), Inches(11), Inches(1),
        "Best practice: nonce-based CSP ('nonce-{random}') over domain allowlists.\n"
        "Trusted Types API: enforce DOM XSS prevention at the API level (createPolicy).\n"
        "CSP bypass: JSONP endpoints on allowed domains, angular.js expression injection, base-uri override.",
        size=13, color=YELLOW)

    # 10 — Browser Security Model
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "Browser Security Model", size=28, color=WHITE, bold=True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    layers = [
        ("Same-Origin Policy (SOP)", "scheme + host + port must match for cross-origin access", CYAN),
        ("CORS", "Controlled relaxation of SOP via server headers (Access-Control-*)", GREEN),
        ("Process Isolation", "Site Isolation: each origin in separate renderer process (Spectre mitigation)", YELLOW),
        ("Sandbox", "Renderer process has no direct filesystem/network/GPU access", RED),
        ("Permissions API", "Camera, mic, geolocation, notifications — user opt-in", PURPLE),
        ("Certificate Transparency", "All TLS certs logged to public CT logs for auditability", RGBColor(0x80, 0x80, 0xFF)),
    ]
    y = Inches(1.3)
    for name, desc, clr in layers:
        box(slide, Inches(1), y, Inches(3), Inches(0.5), DGRAY, name, font_size=11, font_color=clr, border_color=clr)
        add_text(slide, Inches(4.3), y, Inches(8.2), Inches(0.5), desc, size=12, color=LGRAY)
        y += Inches(0.6)
    add_text(slide, Inches(1), Inches(5.1), Inches(11), Inches(1),
        "SOP exceptions: <script src>, <img src>, <link> — cross-origin embeds allowed by default.\n"
        "This is why CSP exists: restrict which origins can serve scripts/styles to your page.\n"
        "Attacks exploiting SOP gaps: DNS rebinding, CORS misconfiguration, postMessage abuse.",
        size=13, color=LGRAY)

    # 11 — V8 & Chrome Sandbox
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "V8 Engine & Chrome Sandbox Architecture", size=28, color=WHITE, bold=True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    # V8 pipeline
    add_text(slide, Inches(1), Inches(1.2), Inches(5), Inches(0.4), "V8 JIT Compilation Pipeline", size=16, color=CYAN, bold=True)
    v8_stages = [("JS Source", CYAN), ("Parser\n→ AST", GREEN), ("Ignition\n(Bytecode)", YELLOW), ("TurboFan\n(Optimized)", RED), ("Maglev\n(Mid-tier)", PURPLE)]
    x = Inches(0.5)
    for txt, clr in v8_stages:
        box(slide, x, Inches(1.7), Inches(2.0), Inches(0.7), DGRAY, txt, font_size=11, font_color=clr, border_color=clr)
        if x < Inches(9):
            arrow_right(slide, x + Inches(2.1), Inches(1.95), x + Inches(2.4), Inches(1.95), clr)
        x += Inches(2.5)
    # Sandbox
    add_text(slide, Inches(1), Inches(2.8), Inches(5), Inches(0.4), "Chrome Multi-Process Sandbox", size=16, color=GREEN, bold=True)
    sandbox_layers = [
        ("Renderer Process", "Untrusted. Runs JS/HTML. Seccomp-BPF filtered. No direct syscalls.", CYAN),
        ("Broker Process", "Mediates all IPC. Validates requests from renderer.", GREEN),
        ("Browser Process", "Privileged. File I/O, network, GPU. Minimal attack surface.", YELLOW),
        ("GPU Process", "Sandboxed. Validates all GPU commands. Separate from renderer.", PURPLE),
    ]
    y = Inches(3.3)
    for name, desc, clr in sandbox_layers:
        box(slide, Inches(1), y, Inches(2.2), Inches(0.45), DGRAY, name, font_size=11, font_color=clr, border_color=clr)
        add_text(slide, Inches(3.5), y, Inches(9), Inches(0.45), desc, size=12, color=LGRAY)
        y += Inches(0.55)
    add_text(slide, Inches(1), Inches(5.8), Inches(11), Inches(0.5),
        "Exploit chain: JIT type confusion → V8 RCE → sandbox escape (Mojo IPC bug) → browser process code exec.",
        size=12, color=YELLOW)

    # 12 — Section divider
    section_slide(prs, "Network Security")

    # 13 — TCP/IP Attack Surface
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "TCP/IP Protocol Attack Surface", size=28, color=WHITE, bold=True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    tcp_attacks = [
        ("SYN Flood", "Exhaust server connection table with half-open connections. Defense: SYN cookies.", RED),
        ("RST Injection", "Send forged RST to tear down active connections. Used by GFW. Defense: TCP-AO.", YELLOW),
        ("Session Hijacking", "Predict sequence numbers to inject data. Modern: randomized ISN.", CYAN),
        ("IP Spoofing", "Forge source IP. UDP easy; TCP requires seq prediction. Defense: BCP38/uRPF.", GREEN),
        ("TCP Reset Attack", "Off-path attacker sends RST with guessed seq. BGP sessions vulnerable.", PURPLE),
        ("Covert Channels", "Data in IP ID, TCP timestamp, TTL fields. Detection: statistical analysis.", RGBColor(0x80, 0x80, 0xFF)),
    ]
    y = Inches(1.2)
    for name, desc, clr in tcp_attacks:
        box(slide, Inches(1), y, Inches(2), Inches(0.45), DGRAY, name, font_size=11, font_color=clr, border_color=clr)
        add_text(slide, Inches(3.3), y, Inches(9.2), Inches(0.45), desc, size=12, color=LGRAY)
        y += Inches(0.55)
    add_text(slide, Inches(1), Inches(4.8), Inches(11), Inches(1.5),
        "Modern mitigations: TCP-AO (RFC 5925) replaces MD5 for BGP, randomized ISN (RFC 6528),\n"
        "SYN cookies (RFC 4987), RPKI for BGP origin validation, strict uRPF (BCP 38/84).",
        size=13, color=LGRAY)

    # 14 — DNS Attack Taxonomy
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "DNS Attack Taxonomy", size=28, color=WHITE, bold=True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    dns_attacks = [
        ("Cache Poisoning", "Forge DNS responses to redirect queries. Kaminsky attack (2008): birthday attack on TXID.", RED),
        ("DNS Tunneling", "Encode data in DNS queries/responses (iodine, dnscat2). Exfil over UDP/53.", CYAN),
        ("DNS Rebinding", "Switch DNS response from external to internal IP. Bypass SOP/firewall rules.", GREEN),
        ("DDoS Amplification", "Open resolvers + spoofed source IP. 50-70x amplification factor. Defense: RRL.", YELLOW),
        ("Domain Hijacking", "Compromise registrar account or DNS provider. BGP + DNS hijack combo.", PURPLE),
        ("NXDOMAIN Attack", "Flood random subdomains to exhaust recursive resolver cache.", RGBColor(0x80, 0x80, 0xFF)),
    ]
    y = Inches(1.2)
    for name, desc, clr in dns_attacks:
        box(slide, Inches(1), y, Inches(2.5), Inches(0.45), DGRAY, name, font_size=11, font_color=clr, border_color=clr)
        add_text(slide, Inches(3.8), y, Inches(8.7), Inches(0.45), desc, size=11, color=LGRAY)
        y += Inches(0.55)
    add_text(slide, Inches(1), Inches(4.8), Inches(11), Inches(1.5),
        "DNSSEC: cryptographic signatures on DNS records. Prevents cache poisoning.\n"
        "DoH/DoT: encrypt DNS queries (privacy). DNS over HTTPS (:443), DNS over TLS (:853).\n"
        "ECH (Encrypted Client Hello): hides SNI from network observers. Requires DoH.",
        size=13, color=LGRAY)

    # 15 — TLS 1.3 Handshake
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "TLS 1.3 Handshake (1-RTT)", size=28, color=WHITE, bold=True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    # Client / Server columns
    box(slide, Inches(1.5), Inches(1.3), Inches(2), Inches(0.6), DGRAY, "Client", font_size=14, font_color=CYAN, border_color=CYAN)
    box(slide, Inches(9), Inches(1.3), Inches(2), Inches(0.6), DGRAY, "Server", font_size=14, font_color=GREEN, border_color=GREEN)
    steps = [
        ("ClientHello + key_share (ECDHE)", Inches(2.2), CYAN, "→"),
        ("ServerHello + key_share + EncryptedExtensions + Cert + CertVerify + Finished", Inches(2.8), GREEN, "←"),
        ("Finished (encrypted)", Inches(3.4), CYAN, "→"),
        ("Application Data (encrypted)", Inches(4.0), YELLOW, "↔"),
    ]
    for label, y_pos, clr, direction in steps:
        thin_line(slide, Inches(2.5), y_pos, Inches(10), y_pos, clr)
        add_text(slide, Inches(3), y_pos - Inches(0.2), Inches(7), Inches(0.25), f"{direction}  {label}", size=11, color=clr)
    add_text(slide, Inches(1), Inches(4.6), Inches(11), Inches(2),
        "TLS 1.3 improvements over TLS 1.2:\n"
        "▸ 1-RTT handshake (vs 2-RTT). 0-RTT for resumption (replay risk).\n"
        "▸ Removed: RSA key exchange, CBC, RC4, SHA-1, compression, renegotiation.\n"
        "▸ Only AEAD ciphers: AES-128-GCM, AES-256-GCM, ChaCha20-Poly1305.\n"
        "▸ Forward secrecy mandatory (ECDHE/DHE only).\n"
        "▸ Encrypted certificate (server cert hidden from passive observers).\n\n"
        "Attacks on TLS: RACCOON (DH timing), Bleichenbacher (RSA PKCS#1 v1.5 — TLS 1.2),\n"
        "certificate misissuance, CT log monitoring for phishing domains.",
        size=13, color=LGRAY)

    # 16 — BGP Hijacking
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "BGP Hijacking Attack Flow", size=28, color=WHITE, bold=True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    bgp_steps = [
        ("Attacker AS\nannounces prefix", RED),
        ("More-specific\nroute propagates", YELLOW),
        ("Internet routes\ntraffic to attacker", CYAN),
        ("MitM or\nblack hole", PURPLE),
    ]
    x = Inches(1)
    for txt, clr in bgp_steps:
        box(slide, x, Inches(1.4), Inches(2.5), Inches(0.8), DGRAY, txt, font_size=12, font_color=clr, border_color=clr)
        if x < Inches(8):
            arrow_right(slide, x + Inches(2.6), Inches(1.7), x + Inches(3.0), Inches(1.7), clr)
        x += Inches(3.1)
    add_text(slide, Inches(1), Inches(2.8), Inches(11), Inches(3),
        "BGP has no built-in authentication — any AS can announce any prefix.\n\n"
        "Notable incidents:\n"
        "▸ Pakistan Telecom → YouTube (2008): /24 more-specific hijacked YouTube's /22\n"
        "▸ Rostelecom → Mastercard/Visa (2017): financial traffic rerouted\n"
        "▸ China Telecom → US military prefixes (2018-2019): systematic interception\n\n"
        "Defense: RPKI (Resource Public Key Infrastructure) — cryptographically signed ROAs.\n"
        "BGPsec (path validation) — not widely deployed. IRR filtering. MANRS initiative.\n"
        "Monitoring: RIPE RIS, RouteViews, BGPStream, Cisco BGPMon.",
        size=13, color=LGRAY)

    # 17 — Layer 2 Attacks
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "Layer 2 Network Attacks", size=28, color=WHITE, bold=True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    l2_attacks = [
        ("ARP Spoofing", "Gratuitous ARP → poison ARP cache → MitM. Defense: DAI + DHCP snooping.", RED),
        ("VLAN Hopping", "Double tagging (802.1Q) or switch spoofing. Defense: native VLAN ≠ user VLAN.", CYAN),
        ("STP Manipulation", "Send superior BPDUs → become root bridge → intercept traffic. Defense: BPDU Guard.", GREEN),
        ("MAC Flooding", "Overflow CAM table → switch becomes hub. Defense: port security, MAC limiting.", YELLOW),
        ("DHCP Starvation", "Exhaust IP pool with spoofed MACs. Defense: DHCP snooping + rate limiting.", PURPLE),
        ("802.1X Bypass", "Hub between supplicant and switch. EAP relay. Defense: MACsec (802.1AE).", RGBColor(0x80, 0x80, 0xFF)),
    ]
    y = Inches(1.2)
    for name, desc, clr in l2_attacks:
        box(slide, Inches(1), y, Inches(2.2), Inches(0.45), DGRAY, name, font_size=11, font_color=clr, border_color=clr)
        add_text(slide, Inches(3.5), y, Inches(9), Inches(0.45), desc, size=12, color=LGRAY)
        y += Inches(0.55)

    # 18 — Wireless Attack Taxonomy
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "Wireless Protocol Attack Taxonomy", size=28, color=WHITE, bold=True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    wireless = [
        ("WPA3-SAE", "Dragonblood (CVE-2019-9494): side-channel on SAE handshake. Defense: updated implementations.", CYAN),
        ("KRACK (WPA2)", "Key Reinstallation Attack: replay handshake msg 3 → reset nonce → decrypt. Patched.", RED),
        ("Evil Twin", "Rogue AP with same SSID. Captive portal credential harvesting. Defense: 802.1X, EAP-TLS.", GREEN),
        ("PMKID Attack", "Capture PMKID from first EAPOL frame — no client needed. Offline crack.", YELLOW),
        ("Deauth Flood", "802.11 management frames unprotected → forge deauth. Defense: MFP (802.11w).", PURPLE),
        ("Bluetooth", "KNOB: negotiate 1-byte entropy → brute-force. BLURtooth: CTKD cross-transport key derivation.", RGBColor(0x80, 0x80, 0xFF)),
    ]
    y = Inches(1.2)
    for name, desc, clr in wireless:
        box(slide, Inches(1), y, Inches(2), Inches(0.45), DGRAY, name, font_size=11, font_color=clr, border_color=clr)
        add_text(slide, Inches(3.3), y, Inches(9.2), Inches(0.45), desc, size=11, color=LGRAY)
        y += Inches(0.55)

    # 19 — Network protocol vuln chart
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "Network Protocol Vulnerability Severity", size=28, color=WHITE, bold=True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    mpl_theme()
    fig, ax = plt.subplots(figsize=(10, 4.5))
    protocols = ["BGP", "DNS", "TLS 1.2", "HTTP/2", "SMTP", "SS7", "SNMP v2", "NTP"]
    critical = [3, 5, 8, 4, 3, 12, 6, 4]
    high = [7, 12, 15, 9, 8, 8, 10, 7]
    x_pos = range(len(protocols))
    w = 0.35
    ax.bar([p - w/2 for p in x_pos], critical, w, label="Critical CVEs", color="#FF4444", edgecolor="#444466")
    ax.bar([p + w/2 for p in x_pos], high, w, label="High CVEs", color="#FFD700", edgecolor="#444466")
    ax.set_xticks(x_pos)
    ax.set_xticklabels(protocols, fontsize=10)
    ax.set_ylabel("CVE Count (2018-2024)", fontsize=12)
    ax.set_title("Protocol Vulnerability Distribution", fontsize=14, color="#00D4FF")
    ax.legend(facecolor="#1a1a2e", edgecolor="#444466", labelcolor="#cccccc")
    ax.grid(axis="y", alpha=0.3)
    embed_chart(slide, fig, Inches(1.5), Inches(1.2), Inches(10), Inches(5.5))

    # 20 — SS7/Diameter
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "SS7 / Diameter Telecom Attack Surface", size=28, color=WHITE, bold=True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    ss7_attacks = [
        ("Location Tracking", "SendRoutingInfo/PSI → get subscriber's serving cell. Track real-time movement.", RED),
        ("SMS Interception", "RegisterSS/UpdateLocation → redirect SMS to attacker-controlled MSC.", CYAN),
        ("Call Interception", "InsertSubscriberData → set call forwarding to attacker number.", GREEN),
        ("DoS", "CancelLocation/PurgeMS → detach subscriber from network.", YELLOW),
        ("Fraud", "Manipulate charging records. Free calls. Premium-rate fraud.", PURPLE),
    ]
    y = Inches(1.3)
    for name, desc, clr in ss7_attacks:
        box(slide, Inches(1), y, Inches(2.3), Inches(0.45), DGRAY, name, font_size=11, font_color=clr, border_color=clr)
        add_text(slide, Inches(3.6), y, Inches(9), Inches(0.45), desc, size=12, color=LGRAY)
        y += Inches(0.55)
    add_text(slide, Inches(1), Inches(4.5), Inches(11), Inches(2),
        "SS7 designed in 1980s — no authentication between operators. Still used for 2G/3G fallback.\n"
        "Diameter (4G/LTE): similar attacks via S6a/Cx interfaces. IPX interconnect adds complexity.\n\n"
        "Defense: SS7 firewall (Category 1-3 filtering per GSMA FS.11/FS.19),\n"
        "Diameter Edge Agent, SEPP (Security Edge Protection Proxy) for 5G roaming.",
        size=13, color=LGRAY)

    # 21 — SDN Architecture Security
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "Software-Defined Networking Security", size=28, color=WHITE, bold=True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    sdn_layers = [
        ("Application Plane", "SDN apps (firewall, LB, IDS). Risk: malicious app → full network control.", PURPLE, Inches(1.3)),
        ("Northbound API", "REST/gRPC. Risk: authentication bypass, API injection.", YELLOW, Inches(2.1)),
        ("Control Plane", "SDN Controller (ONOS, ODL). Single point of failure. Risk: controller compromise.", RED, Inches(2.9)),
        ("Southbound API", "OpenFlow, P4, NETCONF. Risk: flow rule injection, MitM.", CYAN, Inches(3.7)),
        ("Data Plane", "Switches/routers. Execute flow rules. Risk: flow table overflow DoS.", GREEN, Inches(4.5)),
    ]
    for name, desc, clr, y_pos in sdn_layers:
        box(slide, Inches(1), y_pos, Inches(2.5), Inches(0.5), DGRAY, name, font_size=12, font_color=clr, border_color=clr)
        add_text(slide, Inches(3.8), y_pos, Inches(8.5), Inches(0.5), desc, size=12, color=LGRAY)
    add_text(slide, Inches(1), Inches(5.5), Inches(11), Inches(1),
        "SDN centralizes control — compromise controller = compromise entire network.\n"
        "Defense: controller clustering, TLS on southbound, RBAC on northbound, flow rule validation.",
        size=13, color=YELLOW)

    # 22 — Cross-reference
    takeaway_slide(prs, [
        "Domain 3: Memory corruption → feeds directly into web browser exploitation (V8/JIT bugs)",
        "Domain 4: Code reuse attacks → ROP used in browser exploit chains after JIT bug",
        "Domain 10: Cloud security → SSRF is the bridge from web vuln to cloud compromise",
        "Domain 11: C2/malware → web shells, DNS tunneling for C2 communication",
        "Domain 13: Cryptography → TLS attacks, JWT crypto, OAuth token security",
        "Domain 14: Windows/AD → web apps as initial access vector for enterprise compromise",
        "Domain 20: RF/SDR → wireless protocol attacks extend the network security surface",
        "Domain 26: Vuln research → browser fuzzing is one of the highest-value targets",
    ], heading="Cross-Reference Map")

    out = "/media/renan/New Volume/PROIECT/STUDIO-LAVORO/library/15-SECURITY/presentations/04_Web_Network_Security.pptx"
    prs.save(out)
    print(f"[+] Saved {out.split('/')[-1]}")


if __name__ == "__main__":
    gen_pres_03()
    gen_pres_04()
    print("[✓] Presentations 3 & 4 generated successfully.")
