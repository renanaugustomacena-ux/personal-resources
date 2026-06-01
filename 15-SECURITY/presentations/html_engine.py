#!/usr/bin/env python3
"""
HTML/Reveal.js Presentation Engine with SVG animations.
Generates self-contained HTML presentations with dark theme,
CSS transitions, animated SVG diagrams, and interactive elements.
"""

import json
import html as html_module
import math

# ════════════════════════════════════════════════════════════════════
#  COLOR CONSTANTS (matching PPTX theme)
# ════════════════════════════════════════════════════════════════════
COLORS = {
    "bg": "#0A0A1A", "card": "#14142A", "elevated": "#1C1C34",
    "hover": "#24244A", "accent_bg": "#1A1A2E",
    "cyan": "#00D4FF", "cyan_dim": "#008CB4",
    "teal": "#00E5A0", "green": "#00FF88", "green_dim": "#00AA5C",
    "red": "#FF4444", "red_dim": "#CC2222",
    "orange": "#FF8C00", "yellow": "#FFD700", "yellow_dim": "#CCAA00",
    "purple": "#BB86FC", "purple_dim": "#8860CC",
    "magenta": "#FF0080", "pink": "#FF6BB5",
    "blue": "#4488FF", "blue_dim": "#3366CC", "indigo": "#6644FF",
    "white": "#FFFFFF", "lgray": "#CCCCCC", "mgray": "#999999",
    "dgray": "#555566", "border": "#333350", "grid": "#222240",
    "critical": "#FF2222", "high": "#FF6600",
    "medium": "#FFCC00", "low": "#00CC66", "info": "#4488FF",
}

ACCENT_CYCLE = ["cyan", "green", "yellow", "red", "purple", "orange",
                "teal", "magenta", "blue", "pink", "indigo"]


def _e(text):
    return html_module.escape(str(text))


class HTMLPresentation:
    def __init__(self, title="Presentation", theme="dark"):
        self.title = title
        self.slides = []
        self.custom_css = ""
        self.custom_js = ""

    def _add_slide(self, content, classes="", data_attrs=""):
        self.slides.append(f'<section class="{classes}" {data_attrs}>\n{content}\n</section>')

    def save(self, path):
        html = self._render()
        with open(path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"  [+] Saved: {path} ({len(self.slides)} slides)")

    def _render(self):
        slides_html = "\n".join(self.slides)
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{_e(self.title)}</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/theme/black.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/highlight.js@11.9.0/styles/atom-one-dark.min.css">
<style>
:root {{
    --bg: {COLORS["bg"]};
    --card: {COLORS["card"]};
    --elevated: {COLORS["elevated"]};
    --cyan: {COLORS["cyan"]};
    --green: {COLORS["green"]};
    --red: {COLORS["red"]};
    --yellow: {COLORS["yellow"]};
    --purple: {COLORS["purple"]};
    --orange: {COLORS["orange"]};
    --teal: {COLORS["teal"]};
    --magenta: {COLORS["magenta"]};
    --blue: {COLORS["blue"]};
    --white: {COLORS["white"]};
    --lgray: {COLORS["lgray"]};
    --mgray: {COLORS["mgray"]};
    --dgray: {COLORS["dgray"]};
    --border: {COLORS["border"]};
}}

.reveal {{
    font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
    color: var(--lgray);
}}
.reveal .slides {{
    text-align: left;
}}
.reveal .slides section {{
    padding: 30px 50px;
}}
.reveal h1, .reveal h2, .reveal h3 {{
    color: var(--white);
    font-weight: 700;
    text-transform: none;
    letter-spacing: -0.02em;
}}
.reveal h1 {{ font-size: 2.2em; }}
.reveal h2 {{ font-size: 1.6em; border-bottom: 2px solid var(--cyan); padding-bottom: 8px; display: inline-block; }}
.reveal h3 {{ font-size: 1.2em; color: var(--cyan); }}

/* ── Top Accent Bar ── */
.slide-header::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    background: linear-gradient(90deg, var(--cyan), var(--purple), var(--magenta));
}}

/* ── Cards ── */
.card {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 16px 20px;
    margin: 8px 0;
    transition: all 0.3s ease;
}}
.card:hover {{
    border-color: var(--cyan);
    transform: translateY(-2px);
    box-shadow: 0 4px 20px rgba(0, 212, 255, 0.15);
}}
.card-accent {{
    border-left: 4px solid var(--cyan);
}}
.card-accent.green {{ border-left-color: var(--green); }}
.card-accent.red {{ border-left-color: var(--red); }}
.card-accent.yellow {{ border-left-color: var(--yellow); }}
.card-accent.purple {{ border-left-color: var(--purple); }}
.card-accent.orange {{ border-left-color: var(--orange); }}

/* ── Grid Layouts ── */
.grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
.grid-3 {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; }}
.grid-4 {{ display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 12px; }}
.grid-2-1 {{ display: grid; grid-template-columns: 2fr 1fr; gap: 16px; }}
.grid-1-2 {{ display: grid; grid-template-columns: 1fr 2fr; gap: 16px; }}

/* ── Badges/Pills ── */
.badge {{
    display: inline-block;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 0.7em;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}}
.badge-cyan {{ background: rgba(0,212,255,0.2); color: var(--cyan); border: 1px solid var(--cyan); }}
.badge-green {{ background: rgba(0,255,136,0.2); color: var(--green); border: 1px solid var(--green); }}
.badge-red {{ background: rgba(255,68,68,0.2); color: var(--red); border: 1px solid var(--red); }}
.badge-yellow {{ background: rgba(255,215,0,0.2); color: var(--yellow); border: 1px solid var(--yellow); }}
.badge-purple {{ background: rgba(187,134,252,0.2); color: var(--purple); border: 1px solid var(--purple); }}
.badge-orange {{ background: rgba(255,140,0,0.2); color: var(--orange); border: 1px solid var(--orange); }}

/* ── Severity Labels ── */
.severity {{ padding: 2px 10px; border-radius: 4px; font-size: 0.65em; font-weight: 700; text-transform: uppercase; }}
.severity-critical {{ background: #FF222240; color: #FF4444; border: 1px solid #FF4444; }}
.severity-high {{ background: #FF660040; color: #FF8800; border: 1px solid #FF8800; }}
.severity-medium {{ background: #FFCC0040; color: #FFD700; border: 1px solid #FFD700; }}
.severity-low {{ background: #00CC6640; color: #00FF88; border: 1px solid #00FF88; }}

/* ── Code Blocks ── */
.code-window {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 8px;
    overflow: hidden;
    margin: 10px 0;
}}
.code-titlebar {{
    background: var(--elevated);
    padding: 6px 12px;
    display: flex;
    align-items: center;
    gap: 6px;
    border-bottom: 1px solid var(--border);
}}
.code-dot {{ width: 10px; height: 10px; border-radius: 50%; }}
.code-dot.red {{ background: var(--red); }}
.code-dot.yellow {{ background: var(--yellow); }}
.code-dot.green {{ background: var(--green); }}
.code-window pre {{
    margin: 0;
    padding: 16px;
    font-size: 0.65em;
    line-height: 1.5;
}}
.code-window code {{
    font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
}}

/* ── Tables ── */
.styled-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.7em;
}}
.styled-table th {{
    background: var(--elevated);
    color: var(--cyan);
    padding: 10px 14px;
    text-align: left;
    font-weight: 600;
    border-bottom: 2px solid var(--cyan);
}}
.styled-table td {{
    padding: 8px 14px;
    border-bottom: 1px solid var(--border);
}}
.styled-table tr:nth-child(even) td {{
    background: rgba(20, 20, 42, 0.5);
}}
.styled-table tr:hover td {{
    background: rgba(0, 212, 255, 0.05);
}}

/* ── Flow Diagrams ── */
.flow-container {{
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0;
    margin: 20px 0;
    flex-wrap: wrap;
}}
.flow-node {{
    background: var(--card);
    border: 2px solid var(--cyan);
    border-radius: 8px;
    padding: 12px 18px;
    text-align: center;
    font-size: 0.75em;
    font-weight: 600;
    min-width: 120px;
    transition: all 0.3s ease;
}}
.flow-node:hover {{
    transform: scale(1.05);
    box-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
}}
.flow-arrow {{
    color: var(--cyan);
    font-size: 1.5em;
    margin: 0 8px;
    opacity: 0.7;
}}

/* ── Stats Cards ── */
.stat-card {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 20px;
    text-align: center;
}}
.stat-value {{
    font-size: 2.2em;
    font-weight: 700;
    line-height: 1;
    margin-bottom: 8px;
}}
.stat-label {{
    font-size: 0.7em;
    color: var(--mgray);
    text-transform: uppercase;
    letter-spacing: 0.1em;
}}

/* ── Progress Bars ── */
.progress-bar {{
    background: var(--elevated);
    border-radius: 4px;
    height: 8px;
    margin: 4px 0;
    overflow: hidden;
}}
.progress-fill {{
    height: 100%;
    border-radius: 4px;
    transition: width 1s ease;
}}

/* ── SVG Animation Keyframes ── */
@keyframes drawLine {{
    from {{ stroke-dashoffset: 1000; }}
    to {{ stroke-dashoffset: 0; }}
}}
@keyframes fadeInUp {{
    from {{ opacity: 0; transform: translateY(20px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes pulse {{
    0%, 100% {{ opacity: 1; }}
    50% {{ opacity: 0.5; }}
}}
@keyframes glow {{
    0%, 100% {{ filter: drop-shadow(0 0 3px currentColor); }}
    50% {{ filter: drop-shadow(0 0 10px currentColor); }}
}}
@keyframes flowRight {{
    0% {{ transform: translateX(-10px); opacity: 0; }}
    50% {{ opacity: 1; }}
    100% {{ transform: translateX(10px); opacity: 0; }}
}}
@keyframes rotateIn {{
    from {{ transform: rotate(-180deg) scale(0); opacity: 0; }}
    to {{ transform: rotate(0) scale(1); opacity: 1; }}
}}
@keyframes typewriter {{
    from {{ width: 0; }}
    to {{ width: 100%; }}
}}
@keyframes scanline {{
    0% {{ transform: translateY(-100%); }}
    100% {{ transform: translateY(100vh); }}
}}
@keyframes dataFlow {{
    0% {{ stroke-dashoffset: 20; }}
    100% {{ stroke-dashoffset: 0; }}
}}
@keyframes nodeAppear {{
    0% {{ r: 0; opacity: 0; }}
    100% {{ r: 6; opacity: 1; }}
}}

.svg-animated line, .svg-animated path {{
    stroke-dasharray: 1000;
    stroke-dashoffset: 1000;
    animation: drawLine 2s ease forwards;
}}
.svg-animated circle {{
    animation: nodeAppear 0.5s ease forwards;
}}
.svg-animated .flow-particle {{
    animation: flowRight 2s ease-in-out infinite;
}}
.svg-animated .pulse-node {{
    animation: pulse 2s ease-in-out infinite;
}}
.svg-animated .glow-element {{
    animation: glow 3s ease-in-out infinite;
}}

/* ── Animated Entry for fragments ── */
.reveal .fragment.fade-in-then-semi-out {{
    opacity: 0;
    transition: opacity 0.5s ease;
}}

/* ── Comparison Layout ── */
.vs-container {{
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    gap: 20px;
    align-items: start;
}}
.vs-badge {{
    background: var(--elevated);
    border: 2px solid var(--yellow);
    border-radius: 50%;
    width: 50px;
    height: 50px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    color: var(--yellow);
    align-self: center;
}}

/* ── Timeline ── */
.timeline {{
    position: relative;
    padding: 10px 0;
}}
.timeline::before {{
    content: '';
    position: absolute;
    left: 50%;
    top: 0;
    bottom: 0;
    width: 2px;
    background: var(--border);
}}
.timeline-item {{
    display: flex;
    margin: 8px 0;
    font-size: 0.7em;
}}
.timeline-item:nth-child(odd) {{
    flex-direction: row;
    padding-right: 52%;
    text-align: right;
}}
.timeline-item:nth-child(even) {{
    flex-direction: row-reverse;
    padding-left: 52%;
}}
.timeline-dot {{
    width: 12px;
    height: 12px;
    border-radius: 50%;
    position: absolute;
    left: calc(50% - 5px);
}}

/* ── Layer Stack ── */
.layer-stack {{
    display: flex;
    flex-direction: column;
    gap: 4px;
}}
.layer {{
    padding: 12px 20px;
    border-radius: 6px;
    text-align: center;
    font-weight: 600;
    font-size: 0.8em;
    transition: all 0.3s ease;
}}
.layer:hover {{
    transform: scaleX(1.02);
}}

/* ── Risk Matrix ── */
.risk-matrix {{
    display: grid;
    gap: 2px;
    font-size: 0.6em;
}}
.risk-cell {{
    padding: 8px;
    text-align: center;
    font-weight: 600;
    border-radius: 4px;
}}

/* ── Scrolling animation for background ── */
.cyber-bg {{
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    pointer-events: none;
    overflow: hidden;
    z-index: -1;
}}
.cyber-bg::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: repeating-linear-gradient(
        0deg,
        transparent,
        transparent 48px,
        rgba(0,212,255,0.03) 48px,
        rgba(0,212,255,0.03) 50px
    );
}}

{self.custom_css}
</style>
</head>
<body>
<div class="reveal">
<div class="slides">
{slides_html}
</div>
</div>

<script src="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.js"></script>
<script src="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/plugin/highlight/highlight.js"></script>
<script>
Reveal.initialize({{
    hash: true,
    slideNumber: 'c/t',
    transition: 'slide',
    transitionSpeed: 'default',
    backgroundTransition: 'fade',
    center: false,
    width: 1280,
    height: 720,
    margin: 0.04,
    plugins: [ RevealHighlight ],
    highlight: {{
        beforeHighlight: hljs => hljs.configure({{ languages: ['c', 'python', 'javascript', 'bash', 'x86asm', 'json', 'yaml'] }})
    }}
}});
{self.custom_js}
</script>
</body>
</html>'''

    # ════════════════════════════════════════════════════════════
    #  SLIDE GENERATORS
    # ════════════════════════════════════════════════════════════

    def title_slide(self, title, subtitle, domain="", chapter=""):
        badge = f'<span class="badge badge-cyan">{_e(domain)}</span>' if domain else ""
        chapter_html = f'<p style="color:{COLORS["dgray"]};font-size:0.6em;margin-top:30px">{_e(chapter)}</p>' if chapter else ""
        self._add_slide(f'''
<div class="cyber-bg"></div>
<div style="text-align:center;padding-top:80px">
    {badge}
    <h1 style="margin-top:30px;background:linear-gradient(135deg,{COLORS["white"]},{COLORS["cyan"]});-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-size:2.4em">{_e(title)}</h1>
    <div style="width:200px;height:2px;background:linear-gradient(90deg,transparent,{COLORS["cyan"]},transparent);margin:20px auto"></div>
    <p style="color:{COLORS["lgray"]};font-size:0.9em">{_e(subtitle)}</p>
    {chapter_html}
</div>''', "slide-header")

    def section_slide(self, title, section_num=None, description=""):
        num_html = f'<div style="font-size:3em;color:{COLORS["purple"]};font-weight:700;opacity:0.3;margin-bottom:-20px">{section_num}</div>' if section_num is not None else ""
        desc_html = f'<p style="color:{COLORS["lgray"]};font-size:0.85em;max-width:600px;margin:15px auto 0">{_e(description)}</p>' if description else ""
        self._add_slide(f'''
<div style="text-align:center;padding-top:120px">
    {num_html}
    <h2 style="border-bottom:3px solid {COLORS["purple"]};display:inline-block;padding-bottom:10px">{_e(title)}</h2>
    {desc_html}
</div>''')

    def agenda_slide(self, items, title="AGENDA"):
        mid = (len(items) + 1) // 2
        left = items[:mid]
        right = items[mid:]
        left_html = ""
        for i, item in enumerate(left):
            c = COLORS[ACCENT_CYCLE[i % len(ACCENT_CYCLE)]]
            left_html += f'<div class="card" style="border-left:3px solid {c};padding:8px 14px;margin:5px 0"><span style="color:{c};font-weight:700;margin-right:10px">{i+1:02d}</span>{_e(item)}</div>\n'
        right_html = ""
        for i, item in enumerate(right):
            idx = mid + i
            c = COLORS[ACCENT_CYCLE[idx % len(ACCENT_CYCLE)]]
            right_html += f'<div class="card" style="border-left:3px solid {c};padding:8px 14px;margin:5px 0"><span style="color:{c};font-weight:700;margin-right:10px">{idx+1:02d}</span>{_e(item)}</div>\n'
        self._add_slide(f'''
<h2>{_e(title)}</h2>
<div class="grid-2" style="margin-top:15px;font-size:0.75em">
    <div>{left_html}</div>
    <div>{right_html}</div>
</div>''', "slide-header")

    def content_slide(self, heading, bullets, sub_heading=""):
        sub = f'<h3>{_e(sub_heading)}</h3>' if sub_heading else ""
        items = "\n".join(f'<div class="card card-accent" style="font-size:0.75em;padding:8px 14px;margin:4px 0">{_e(b)}</div>' for b in bullets)
        self._add_slide(f'''<h2>{_e(heading)}</h2>{sub}\n{items}''', "slide-header")

    def content_slide_rich(self, heading, blocks, sub_heading=""):
        sub = f'<h3>{_e(sub_heading)}</h3>' if sub_heading else ""
        items = ""
        for accent, title, desc in blocks:
            c = COLORS.get(accent, accent) if isinstance(accent, str) else accent
            items += f'''<div class="card card-accent" style="border-left-color:{c};padding:10px 16px;margin:5px 0">
    <strong style="color:{c};font-size:0.8em">{_e(title)}</strong>
    <div style="font-size:0.72em;color:{COLORS["lgray"]};margin-top:4px">{_e(desc)}</div>
</div>\n'''
        self._add_slide(f'<h2>{_e(heading)}</h2>{sub}\n{items}', "slide-header")

    def two_column_slide(self, heading, left_title, left_items, right_title, right_items,
                         left_color="cyan", right_color="green"):
        lc = COLORS[left_color]
        rc = COLORS[right_color]
        left_html = "\n".join(f'<div style="font-size:0.7em;padding:4px 0;border-bottom:1px solid {COLORS["border"]}">▸ {_e(i)}</div>' for i in left_items)
        right_html = "\n".join(f'<div style="font-size:0.7em;padding:4px 0;border-bottom:1px solid {COLORS["border"]}">▸ {_e(i)}</div>' for i in right_items)
        self._add_slide(f'''
<h2>{_e(heading)}</h2>
<div class="grid-2">
    <div class="card" style="border-top:3px solid {lc}">
        <h3 style="color:{lc};font-size:0.9em;margin-top:0">{_e(left_title)}</h3>
        {left_html}
    </div>
    <div class="card" style="border-top:3px solid {rc}">
        <h3 style="color:{rc};font-size:0.9em;margin-top:0">{_e(right_title)}</h3>
        {right_html}
    </div>
</div>''', "slide-header")

    def three_column_slide(self, heading, columns):
        cols_html = ""
        for title, color, items in columns[:3]:
            c = COLORS.get(color, color) if isinstance(color, str) else color
            items_html = "\n".join(f'<div style="font-size:0.65em;padding:3px 0">▸ {_e(i)}</div>' for i in items)
            cols_html += f'''<div class="card" style="border-top:3px solid {c}">
    <h3 style="color:{c};font-size:0.85em;margin-top:0">{_e(title)}</h3>
    {items_html}
</div>\n'''
        self._add_slide(f'<h2>{_e(heading)}</h2>\n<div class="grid-3">{cols_html}</div>', "slide-header")

    def diagram_flow_slide(self, heading, nodes, sub_heading=""):
        sub = f'<h3>{_e(sub_heading)}</h3>' if sub_heading else ""
        flow_html = '<div class="flow-container">\n'
        for i, (label, color) in enumerate(nodes):
            c = COLORS.get(color, color) if isinstance(color, str) else color
            flow_html += f'<div class="flow-node" style="border-color:{c};color:{c}">{_e(label)}</div>\n'
            if i < len(nodes) - 1:
                flow_html += f'<div class="flow-arrow" style="color:{c}">→</div>\n'
        flow_html += '</div>'
        self._add_slide(f'<h2>{_e(heading)}</h2>{sub}\n{flow_html}', "slide-header")

    def svg_flow_slide(self, heading, nodes, sub_heading=""):
        """Animated SVG flow diagram."""
        sub = f'<h3>{_e(sub_heading)}</h3>' if sub_heading else ""
        n = len(nodes)
        w = 1100
        node_w = min(150, (w - 40) // n - 20)
        node_h = 50
        y_center = 80
        svg = f'<svg class="svg-animated" viewBox="0 0 {w} 200" style="width:100%;max-height:200px;margin:15px 0">\n'
        for i, (label, color) in enumerate(nodes):
            c = COLORS.get(color, color) if isinstance(color, str) else color
            x = 20 + i * (node_w + 30)
            delay = i * 0.3
            svg += f'''  <g style="animation-delay:{delay}s">
    <rect x="{x}" y="{y_center - node_h//2}" width="{node_w}" height="{node_h}"
          rx="8" fill="{COLORS["card"]}" stroke="{c}" stroke-width="2"
          style="animation:fadeInUp 0.5s ease {delay}s both"/>
    <text x="{x + node_w//2}" y="{y_center + 5}" text-anchor="middle"
          fill="{c}" font-size="11" font-weight="600"
          style="animation:fadeInUp 0.5s ease {delay + 0.1}s both">{_e(label)}</text>
  </g>\n'''
            if i < n - 1:
                ax1 = x + node_w + 4
                ax2 = x + node_w + 26
                svg += f'''  <line x1="{ax1}" y1="{y_center}" x2="{ax2}" y2="{y_center}"
        stroke="{c}" stroke-width="2" marker-end="url(#arrowhead)"
        style="animation:drawLine 0.5s ease {delay + 0.2}s both;stroke-dasharray:30;stroke-dashoffset:30"/>\n'''
        svg += f'''  <defs><marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
    <polygon points="0 0, 10 3.5, 0 7" fill="{COLORS["cyan"]}"/>
  </marker></defs>\n'''
        svg += '</svg>'
        self._add_slide(f'<h2>{_e(heading)}</h2>{sub}\n{svg}', "slide-header")

    def svg_layers_slide(self, heading, layers):
        """Animated layered architecture SVG."""
        n = len(layers)
        h_per = 45
        total_h = n * (h_per + 6) + 20
        w = 900
        svg = f'<svg class="svg-animated" viewBox="0 0 {w} {total_h}" style="width:90%;margin:10px auto;display:block">\n'
        for i, (label, color, desc) in enumerate(layers):
            c = COLORS.get(color, color) if isinstance(color, str) else color
            y = 10 + i * (h_per + 6)
            lw = w * 0.5 - i * 15
            x = (w * 0.5 - lw) / 2
            delay = i * 0.2
            svg += f'''  <g style="animation:fadeInUp 0.6s ease {delay}s both">
    <rect x="{x}" y="{y}" width="{lw}" height="{h_per}" rx="6"
          fill="{COLORS["card"]}" stroke="{c}" stroke-width="1.5"/>
    <text x="{x + lw/2}" y="{y + h_per/2 + 4}" text-anchor="middle"
          fill="{c}" font-size="12" font-weight="600">{_e(label)}</text>
    <text x="{x + lw + 20}" y="{y + h_per/2 + 4}" text-anchor="start"
          fill="{COLORS["lgray"]}" font-size="10">{_e(desc)}</text>
  </g>\n'''
        svg += '</svg>'
        self._add_slide(f'<h2>{_e(heading)}</h2>\n{svg}', "slide-header")

    def svg_network_slide(self, heading, center_label, satellites):
        """Animated radial network SVG. satellites: list of (label, color)."""
        n = len(satellites)
        cx, cy = 450, 180
        r = 140
        svg = f'<svg class="svg-animated" viewBox="0 0 900 380" style="width:90%;margin:10px auto;display:block">\n'
        svg += f'''  <circle cx="{cx}" cy="{cy}" r="40" fill="{COLORS["card"]}"
          stroke="{COLORS["cyan"]}" stroke-width="2" class="glow-element"/>
  <text x="{cx}" y="{cy + 4}" text-anchor="middle" fill="{COLORS["cyan"]}"
        font-size="11" font-weight="700">{_e(center_label)}</text>\n'''
        for i, (label, color) in enumerate(satellites):
            c = COLORS.get(color, color) if isinstance(color, str) else color
            angle = (2 * math.pi * i / n) - math.pi / 2
            sx = cx + r * math.cos(angle)
            sy = cy + r * math.sin(angle)
            delay = i * 0.15
            svg += f'''  <line x1="{cx}" y1="{cy}" x2="{sx:.0f}" y2="{sy:.0f}"
        stroke="{c}" stroke-width="1" stroke-dasharray="5,5"
        style="animation:drawLine 1s ease {delay}s both"/>
  <circle cx="{sx:.0f}" cy="{sy:.0f}" r="30" fill="{COLORS["card"]}"
          stroke="{c}" stroke-width="1.5"
          style="animation:fadeInUp 0.5s ease {delay + 0.2}s both"/>
  <text x="{sx:.0f}" y="{sy + 4:.0f}" text-anchor="middle" fill="{c}"
        font-size="9" font-weight="600"
        style="animation:fadeInUp 0.5s ease {delay + 0.3}s both">{_e(label)}</text>\n'''
        svg += '</svg>'
        self._add_slide(f'<h2>{_e(heading)}</h2>\n{svg}', "slide-header")

    def code_slide(self, heading, code_text, language="c", notes=None):
        notes_html = ""
        if notes:
            notes_html = '<div style="margin-top:10px;font-size:0.65em;color:' + COLORS["mgray"] + '">'
            for n in notes[:3]:
                notes_html += f'<div>→ {_e(n)}</div>'
            notes_html += '</div>'
        self._add_slide(f'''
<h2>{_e(heading)}</h2>
<div class="code-window">
    <div class="code-titlebar">
        <div class="code-dot red"></div>
        <div class="code-dot yellow"></div>
        <div class="code-dot green"></div>
        <span style="margin-left:10px;font-size:0.65em;color:{COLORS["mgray"]}">{_e(language)}</span>
    </div>
    <pre><code class="language-{_e(language)}">{_e(code_text)}</code></pre>
</div>
{notes_html}''', "slide-header")

    def table_slide(self, heading, headers, rows, sub_heading=""):
        sub = f'<h3>{_e(sub_heading)}</h3>' if sub_heading else ""
        th = "".join(f"<th>{_e(h)}</th>" for h in headers)
        tr = ""
        for row in rows:
            tr += "<tr>" + "".join(f"<td>{_e(c)}</td>" for c in row) + "</tr>\n"
        self._add_slide(f'''
<h2>{_e(heading)}</h2>{sub}
<table class="styled-table">
    <thead><tr>{th}</tr></thead>
    <tbody>{tr}</tbody>
</table>''', "slide-header")

    def stats_slide(self, heading, stats, sub_heading=""):
        cards = ""
        for value, label, color in stats:
            c = COLORS.get(color, color) if isinstance(color, str) else color
            cards += f'''<div class="stat-card" style="border-top:3px solid {c}">
    <div class="stat-value" style="color:{c}">{_e(value)}</div>
    <div class="stat-label">{_e(label)}</div>
</div>\n'''
        sub = f'<h3>{_e(sub_heading)}</h3>' if sub_heading else ""
        cols = min(len(stats), 4)
        self._add_slide(f'<h2>{_e(heading)}</h2>{sub}\n<div class="grid-{cols}" style="margin-top:20px">{cards}</div>', "slide-header")

    def comparison_slide(self, heading, left_title, left_items, right_title, right_items,
                         left_color="red", right_color="green"):
        lc = COLORS[left_color]
        rc = COLORS[right_color]
        left_html = "\n".join(f'<div style="font-size:0.7em;padding:5px 0;border-bottom:1px solid {COLORS["border"]}">▸ {_e(i)}</div>' for i in left_items)
        right_html = "\n".join(f'<div style="font-size:0.7em;padding:5px 0;border-bottom:1px solid {COLORS["border"]}">▸ {_e(i)}</div>' for i in right_items)
        self._add_slide(f'''
<h2>{_e(heading)}</h2>
<div class="vs-container" style="margin-top:15px">
    <div class="card" style="border-top:3px solid {lc}">
        <h3 style="color:{lc};margin-top:0">{_e(left_title)}</h3>
        {left_html}
    </div>
    <div class="vs-badge">VS</div>
    <div class="card" style="border-top:3px solid {rc}">
        <h3 style="color:{rc};margin-top:0">{_e(right_title)}</h3>
        {right_html}
    </div>
</div>''', "slide-header")

    def timeline_slide(self, heading, events):
        items = ""
        for i, (label, desc, color) in enumerate(events):
            c = COLORS.get(color, color) if isinstance(color, str) else color
            items += f'''<div class="timeline-item">
    <div class="card" style="border-left:3px solid {c};font-size:0.7em;padding:6px 12px">
        <strong style="color:{c}">{_e(label)}</strong><br>{_e(desc)}
    </div>
</div>\n'''
        self._add_slide(f'''
<h2>{_e(heading)}</h2>
<div class="timeline" style="margin-top:10px">{items}</div>''', "slide-header")

    def warning_slide(self, heading, warnings):
        items = ""
        for severity, text in warnings:
            items += f'<div style="margin:6px 0;display:flex;align-items:center;gap:12px"><span class="severity severity-{severity.lower()}">{_e(severity)}</span><span style="font-size:0.75em">{_e(text)}</span></div>\n'
        self._add_slide(f'<h2>{_e(heading)}</h2>\n{items}', "slide-header")

    def takeaway_slide(self, items, heading="Key Takeaways"):
        items_html = ""
        for i, item in enumerate(items):
            c = COLORS[ACCENT_CYCLE[i % len(ACCENT_CYCLE)]]
            items_html += f'''<div class="card card-accent" style="border-left-color:{c};padding:8px 16px;margin:5px 0;font-size:0.75em">
    <span style="color:{c};font-weight:700;margin-right:8px">{i+1:02d}</span>{_e(item)}
</div>\n'''
        self._add_slide(f'<h2>{_e(heading)}</h2>\n{items_html}', "slide-header")

    def quote_slide(self, text, attribution=""):
        attr = f'<div style="color:{COLORS["mgray"]};font-size:0.8em;margin-top:15px">— {_e(attribution)}</div>' if attribution else ""
        self._add_slide(f'''
<div style="text-align:center;padding-top:100px">
    <div style="font-size:3em;color:{COLORS["cyan"]};line-height:0.5">&#10077;</div>
    <blockquote style="font-size:1.1em;color:{COLORS["white"]};font-style:italic;max-width:700px;margin:20px auto;line-height:1.6">
        {_e(text)}
    </blockquote>
    {attr}
</div>''')

    def definition_slide(self, heading, definitions):
        items = ""
        for term, defn, color in definitions:
            c = COLORS.get(color, color) if isinstance(color, str) else color
            items += f'''<div style="display:flex;gap:15px;margin:6px 0;align-items:baseline">
    <span class="badge" style="background:rgba(0,0,0,0.3);color:{c};border:1px solid {c};min-width:120px;text-align:center">{_e(term)}</span>
    <span style="font-size:0.72em;color:{COLORS["lgray"]}">{_e(defn)}</span>
</div>\n'''
        self._add_slide(f'<h2>{_e(heading)}</h2>\n{items}', "slide-header")

    def icon_grid_slide(self, heading, items, cols=4):
        cards = ""
        for icon, label, desc, color in items:
            c = COLORS.get(color, color) if isinstance(color, str) else color
            cards += f'''<div class="card" style="text-align:center;border-top:3px solid {c};padding:12px 8px">
    <div style="font-size:1.8em;margin-bottom:8px">{icon}</div>
    <div style="color:{c};font-weight:700;font-size:0.75em">{_e(label)}</div>
    <div style="font-size:0.6em;color:{COLORS["mgray"]};margin-top:6px">{_e(desc)}</div>
</div>\n'''
        self._add_slide(f'<h2>{_e(heading)}</h2>\n<div class="grid-{cols}" style="margin-top:15px">{cards}</div>', "slide-header")

    def detail_slide(self, heading, blocks):
        content = ""
        for title, lines, color in blocks:
            c = COLORS.get(color, color) if isinstance(color, str) else color
            items = "\n".join(f'<div style="font-size:0.7em;padding:2px 0;margin-left:12px">▸ {_e(l)}</div>' for l in lines)
            content += f'''<div style="margin:8px 0">
    <strong style="color:{c};font-size:0.85em">{_e(title)}</strong>
    {items}
</div>\n'''
        self._add_slide(f'<h2>{_e(heading)}</h2>\n{content}', "slide-header")

    def cross_reference_slide(self, items, heading="Cross-Reference Map"):
        content = ""
        for i, (ref, desc) in enumerate(items):
            c = COLORS[ACCENT_CYCLE[i % len(ACCENT_CYCLE)]]
            content += f'''<div style="display:flex;gap:12px;margin:5px 0;align-items:center">
    <span class="badge" style="background:rgba(0,0,0,0.3);color:{c};border:1px solid {c};min-width:90px;text-align:center;font-size:0.6em">{_e(ref)}</span>
    <span style="font-size:0.72em">{_e(desc)}</span>
</div>\n'''
        self._add_slide(f'<h2>{_e(heading)}</h2>\n{content}', "slide-header")

    def end_slide(self, title="End of Presentation", subtitle=""):
        sub = f'<p style="color:{COLORS["lgray"]};font-size:0.8em">{_e(subtitle)}</p>' if subtitle else ""
        self._add_slide(f'''
<div style="text-align:center;padding-top:150px">
    <h1 style="background:linear-gradient(135deg,{COLORS["cyan"]},{COLORS["purple"]});-webkit-background-clip:text;-webkit-text-fill-color:transparent">{_e(title)}</h1>
    {sub}
</div>''')

    def process_slide(self, heading, steps, sub_heading=""):
        self.diagram_flow_slide(heading, steps, sub_heading)

    def architecture_slide(self, heading, layers, annotations=None):
        self.svg_layers_slide(heading, layers)

    def risk_matrix_slide(self, heading, items=None):
        colors_map = [
            ["#00CC66", "#00CC66", "#CCAA00", "#FFD700", "#FF8C00"],
            ["#00CC66", "#CCAA00", "#FFD700", "#FF8C00", "#CC2222"],
            ["#CCAA00", "#FFD700", "#FF8C00", "#CC2222", "#FF2222"],
            ["#FFD700", "#FF8C00", "#CC2222", "#FF2222", "#FF2222"],
            ["#FF8C00", "#CC2222", "#FF2222", "#FF2222", "#FF2222"],
        ]
        impact = ["Negligible", "Minor", "Moderate", "Major", "Critical"]
        likelihood = ["Rare", "Unlikely", "Possible", "Likely", "Certain"]
        cells = ""
        cells += f'<div style="grid-column:1"></div>'
        for imp in impact:
            cells += f'<div style="text-align:center;font-size:0.6em;color:{COLORS["cyan"]};font-weight:600">{imp}</div>'
        for ri in range(4, -1, -1):
            cells += f'<div style="font-size:0.6em;color:{COLORS["lgray"]};text-align:right;padding-right:8px;display:flex;align-items:center;justify-content:flex-end">{likelihood[ri]}</div>'
            for ci in range(5):
                c = colors_map[ri][ci]
                label = ""
                if items:
                    for li, ii, lbl in items:
                        if li == ri and ii == ci:
                            label = lbl
                cells += f'<div class="risk-cell" style="background:{c}40;border:1px solid {c};font-size:0.55em;color:{COLORS["white"]}">{_e(label)}</div>'
        self._add_slide(f'''
<h2>{_e(heading)}</h2>
<div style="text-align:center;font-size:0.7em;color:{COLORS["cyan"]};margin:5px 0">IMPACT →</div>
<div class="risk-matrix" style="grid-template-columns:80px repeat(5,1fr);max-width:700px;margin:10px auto">
{cells}
</div>
<div style="text-align:left;font-size:0.6em;color:{COLORS["lgray"]};margin-top:5px;margin-left:20px">↑ LIKELIHOOD</div>''', "slide-header")

    def summary_slide(self, heading, summary_text, key_points=None):
        kp = ""
        if key_points:
            kp = '<div style="margin-top:15px">'
            for i, p in enumerate(key_points):
                c = COLORS[ACCENT_CYCLE[i % len(ACCENT_CYCLE)]]
                kp += f'<div class="card card-accent" style="border-left-color:{c};font-size:0.72em;padding:6px 14px;margin:4px 0">{_e(p)}</div>'
            kp += '</div>'
        self._add_slide(f'''
<h2>{_e(heading)}</h2>
<div style="font-size:0.8em;color:{COLORS["lgray"]};line-height:1.6;margin-top:10px">{_e(summary_text)}</div>
{kp}''', "slide-header")

    def bar_chart_placeholder(self, heading, data_desc):
        self._add_slide(f'''
<h2>{_e(heading)}</h2>
<div class="card" style="text-align:center;padding:40px;margin-top:30px">
    <div style="font-size:2em;margin-bottom:10px">📊</div>
    <div style="color:{COLORS["mgray"]}">{_e(data_desc)}</div>
    <div style="font-size:0.7em;color:{COLORS["dgray"]};margin-top:8px">Interactive chart — see PPTX version for rendered visualization</div>
</div>''', "slide-header")
