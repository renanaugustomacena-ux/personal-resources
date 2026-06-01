#!/usr/bin/env python3
"""Generate presentations 7 (Enterprise AD/Mobile) and 8 (ICS/RF/Automotive)."""

import io
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
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
    a = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, x1, y1, x2-x1, y2-y1); a.fill.solid(); a.fill.fore_color.rgb = c; a.line.fill.background(); return a

def arrow_d(s, x, y, ln, c=CYAN):
    a = s.shapes.add_shape(MSO_SHAPE.DOWN_ARROW, x, y, Inches(0.3), ln); a.fill.solid(); a.fill.fore_color.rgb = c; a.line.fill.background(); return a

def thin_line(s, x1, y1, x2, y2, c=CYAN):
    ln = s.shapes.add_connector(1, x1, y1, x2, y2); ln.line.color.rgb = c; ln.line.width = Pt(1.5); return ln

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
        box(s, Inches(1.0), y, Inches(11), Inches(0.45), DGRAY, f"▸  {item}", 13, LGRAY, colors[i%len(colors)])
        y += Inches(0.55)


# ════════════════════════════════════════════════════════════════════
#  PRESENTATION 7 — Enterprise Security: AD, Windows & Mobile
# ════════════════════════════════════════════════════════════════════
def gen_pres_07():
    prs = new_prs()
    title_slide(prs, "Enterprise Security —\nActive Directory, Windows & Mobile", "Domains 14-15  ·  AD Attacks  ·  Kerberos  ·  ADCS  ·  iOS/Android  ·  5G")

    agenda_slide(prs, [
        "Active Directory Architecture", "AD Attack Kill Chain",
        "Kerberoasting & AS-REP Roasting", "AD CS Abuse (ESC1-ESC8)",
        "Delegation Attacks", "NTLM Coercion & Relay",
        "Golden/Silver Ticket", "DCSync", "Exchange/M365 Attack Surface",
        "Android Security Architecture", "iOS Security Architecture",
        "iOS Exploit Chains", "Mobile Threats & 5G", "Enterprise Mobile Defense",
    ])

    # 3 — AD Architecture
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "Active Directory Architecture", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    box(slide, Inches(4), Inches(1.3), Inches(5), Inches(0.6), DGRAY, "Forest: corp.example.com", 14, CYAN, CYAN)
    box(slide, Inches(1.5), Inches(2.3), Inches(3.5), Inches(0.6), DGRAY, "Domain: na.corp.example.com", 12, GREEN, GREEN)
    box(slide, Inches(5.5), Inches(2.3), Inches(3.5), Inches(0.6), DGRAY, "Domain: eu.corp.example.com", 12, GREEN, GREEN)
    box(slide, Inches(9.5), Inches(2.3), Inches(3), Inches(0.6), DGRAY, "Child / Trust", 12, YELLOW, YELLOW)
    arrow_d(slide, Inches(3), Inches(1.9), Inches(0.3), GREEN)
    arrow_d(slide, Inches(7), Inches(1.9), Inches(0.3), GREEN)
    components = [
        ("Domain Controller", "NTDS.dit, SYSVOL, Group Policy, Kerberos KDC, LDAP, DNS", CYAN),
        ("Organizational Units", "Hierarchical containers for users, computers, groups. GPO linkage.", GREEN),
        ("Trusts", "Parent-child (transitive), forest (selective), external (NTLM). Direction matters.", YELLOW),
        ("Group Policy", "GPO → SYSVOL → client pull. Attack: GPO abuse, SYSVOL share access.", PURPLE),
        ("ADCS / PKI", "Enterprise CA, certificate templates, auto-enrollment. ESC1-ESC8 vulns.", RED),
    ]
    y = Inches(3.3)
    for name, desc, clr in components:
        box(slide, Inches(1), y, Inches(2.5), Inches(0.45), DGRAY, name, 11, clr, clr)
        add_text(slide, Inches(3.8), y, Inches(8.5), Inches(0.45), desc, 12, LGRAY)
        y += Inches(0.55)

    # 4 — AD Attack Kill Chain
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "AD Attack Kill Chain", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    chain = [
        ("Initial Access\nPhishing, RDP, VPN", RED),
        ("Reconnaissance\nBloodHound, LDAP", CYAN),
        ("Privilege Escalation\nKerberoast, ADCS", YELLOW),
        ("Lateral Movement\nPsExec, WMI, RDP", GREEN),
        ("Domain Dominance\nDCSync, Golden Ticket", PURPLE),
    ]
    x = Inches(0.3)
    for txt, clr in chain:
        box(slide, x, Inches(1.4), Inches(2.2), Inches(1.0), DGRAY, txt, 11, clr, clr)
        if x < Inches(9):
            arrow_r(slide, x+Inches(2.3), Inches(1.8), x+Inches(2.5), Inches(1.8), clr)
        x += Inches(2.6)
    add_text(slide, Inches(0.5), Inches(2.8), Inches(12), Inches(3.5),
        "Tools at each stage:\n"
        "▸ Initial Access: phishing (Evilginx2, GoPhish), exposed RDP (Shodan), VPN cred stuffing\n"
        "▸ Recon: BloodHound/SharpHound (graph-based path finding), ADRecon, ldapsearch, PowerView\n"
        "▸ PrivEsc: Rubeus (Kerberoast/AS-REP), Certify/Certipy (ADCS), PrintSpooler/EfsPotato\n"
        "▸ Lateral: Impacket (psexec/wmiexec/smbexec), CrackMapExec, Evil-WinRM, PsExec\n"
        "▸ Dominance: Mimikatz (DCSync, Golden/Silver), Impacket secretsdump, DCShadow\n\n"
        "Detection: monitor Kerberos TGS requests (4769), LDAP queries for sensitive attributes,\n"
        "DRSUAPI replication (4662), lateral movement signatures (4624 type 3/10), honey tokens.",
        13, LGRAY)

    # 5 — Kerberoasting
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "Kerberoasting Attack Flow", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    kerb = [("Any domain\nuser", CYAN), ("Request TGS\nfor SPN", GREEN), ("KDC returns\nRC4/AES ticket", YELLOW), ("Extract\nticket hash", RED), ("Offline crack\n(hashcat)", PURPLE)]
    x = Inches(0.3)
    for txt, clr in kerb:
        box(slide, x, Inches(1.4), Inches(2.1), Inches(0.9), DGRAY, txt, 11, clr, clr)
        if x < Inches(9): arrow_r(slide, x+Inches(2.2), Inches(1.75), x+Inches(2.4), Inches(1.75), clr)
        x += Inches(2.5)
    add_text(slide, Inches(0.5), Inches(2.8), Inches(12), Inches(3),
        "Any authenticated domain user can request a TGS ticket for any SPN.\n"
        "The TGS is encrypted with the service account's NTLM hash → offline crackable.\n\n"
        "Tools: Rubeus kerberoast, Impacket GetUserSPNs.py, PowerView Get-DomainSPNTicket\n"
        "Crack: hashcat -m 13100 (RC4) or -m 19700 (AES256) — RC4 tickets crack ~10x faster.\n\n"
        "Defense:\n"
        "▸ Enforce AES-only encryption (harder to crack, larger key space)\n"
        "▸ 25+ character random passwords on service accounts\n"
        "▸ gMSA (Group Managed Service Accounts) — auto-rotated 120+ char passwords\n"
        "▸ Monitor event 4769 for anomalous TGS request patterns (many SPNs, RC4 downgrade)",
        13, LGRAY)

    # 6 — AS-REP Roasting
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "AS-REP Roasting Attack Flow", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    asrep = [("Find users with\nDONT_REQ_PREAUTH", CYAN), ("Send AS-REQ\nwithout pre-auth", GREEN), ("KDC returns\nAS-REP", YELLOW), ("Extract encrypted\ntimestamp", RED), ("Offline crack\n(hashcat -m 18200)", PURPLE)]
    x = Inches(0.3)
    for txt, clr in asrep:
        box(slide, x, Inches(1.4), Inches(2.1), Inches(0.9), DGRAY, txt, 11, clr, clr)
        if x < Inches(9): arrow_r(slide, x+Inches(2.2), Inches(1.75), x+Inches(2.4), Inches(1.75), clr)
        x += Inches(2.5)
    add_text(slide, Inches(0.5), Inches(2.8), Inches(12), Inches(2.5),
        "Kerberos pre-authentication: client proves identity by encrypting timestamp with password hash.\n"
        "DONT_REQUIRE_PREAUTH flag disables this → KDC sends encrypted data without proof of identity.\n\n"
        "Unlike Kerberoasting, requires specific account misconfiguration. Often legacy accounts.\n"
        "Detection: monitor event 4768 with pre-authentication failure, audit DONT_REQUIRE_PREAUTH flag.\n"
        "Fix: remove DONT_REQUIRE_PREAUTH from all accounts. Strong passwords on any remaining.",
        13, LGRAY)

    # 7 — AD CS Abuse
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "AD CS Abuse — ESC1 through ESC8", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    escs = [
        ("ESC1", "Template allows SAN (Subject Alt Name) + low-priv enrollment → impersonate any user", RED),
        ("ESC2", "Template has Any Purpose EKU or SubCA → create arbitrary certificates", RED),
        ("ESC3", "Certificate request agent template → enroll on behalf of others", YELLOW),
        ("ESC4", "Template ACL misconfiguration → modify template to add SAN/EKU", YELLOW),
        ("ESC6", "CA has EDITF_ATTRIBUTESUBJECTALTNAME2 flag → SAN in any request", CYAN),
        ("ESC7", "CA ACL allows ManageCA/ManageCertificates → approve pending + ESC6", CYAN),
        ("ESC8", "HTTP enrollment endpoint → NTLM relay to CA web enrollment", GREEN),
        ("ESC9-13", "Newer variants: CT_FLAG_NO_SECURITY_EXTENSION, schema abuse, OID group link", PURPLE),
    ]
    y = Inches(1.2)
    for name, desc, clr in escs:
        box(slide, Inches(0.8), y, Inches(1), Inches(0.4), DGRAY, name, 11, clr, clr)
        add_text(slide, Inches(2.0), y, Inches(10.5), Inches(0.4), desc, 11, LGRAY)
        y += Inches(0.48)
    add_text(slide, Inches(0.8), y+Inches(0.1), Inches(11), Inches(0.8),
        "Tools: Certify (C#), Certipy (Python), ForgeCert. ESC1 = most common and most impactful.\n"
        "Defense: audit templates (Certify find), remove SAN from unnecessary templates, restrict enrollment.",
        12, YELLOW)

    # 8 — Delegation
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "Kerberos Delegation Attacks", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    deleg = [
        ("Unconstrained", "Service stores user's full TGT. Compromise service → impersonate anyone who connected.\nCoerce (PrinterBug/PetitPotam) DC → DC TGT → DCSync.", RED),
        ("Constrained (S4U)", "msDS-AllowedToDelegateTo specifies target SPNs.\nS4U2Self + S4U2Proxy → get ticket for allowed service as any user.", YELLOW),
        ("RBCD", "msDS-AllowedToActOnBehalfOfOtherIdentity on TARGET (not source).\nIf you can write this attribute → full S4U chain → access target as any user.", GREEN),
    ]
    y = Inches(1.3)
    for name, desc, clr in deleg:
        box(slide, Inches(0.8), y, Inches(2.2), Inches(0.7), DGRAY, name, 13, clr, clr)
        add_text(slide, Inches(3.3), y, Inches(9.2), Inches(0.7), desc, 12, LGRAY)
        y += Inches(0.9)
    add_text(slide, Inches(0.8), Inches(4.3), Inches(11), Inches(2),
        "RBCD is the most abused because:\n"
        "▸ Any user with WriteProperty on a computer's msDS-AllowedToActOnBehalfOfOtherIdentity can set it\n"
        "▸ Computer accounts created by users (default: 10 per user via ms-DS-MachineAccountQuota)\n"
        "▸ No need for SeEnableDelegationPrivilege (required for unconstrained/constrained)\n\n"
        "Tools: Rubeus s4u, Impacket getST.py, StandIn.exe\n"
        "Detection: monitor 4662 for writes to msDS-AllowedToActOnBehalfOfOtherIdentity",
        13, LGRAY)

    # 9 — NTLM Coercion
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "NTLM Coercion & Relay Attacks", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    coerce = [
        ("PetitPotam", "EfsRpcOpenFileRaw → DC authenticates to attacker. CVE-2021-36942.", RED),
        ("PrinterBug", "RpcRemoteFindFirstPrinterChangeNotification → force auth callback.", YELLOW),
        ("DFSCoerce", "NetrDfsRemoveStdRoot → abuse DFS namespace for coercion.", GREEN),
        ("ShadowCoerce", "MS-FSRVP FileServerVSSAgent → VSS-based coercion.", CYAN),
    ]
    y = Inches(1.3)
    for name, desc, clr in coerce:
        box(slide, Inches(0.8), y, Inches(2), Inches(0.45), DGRAY, name, 12, clr, clr)
        add_text(slide, Inches(3.1), y, Inches(9.4), Inches(0.45), desc, 12, LGRAY)
        y += Inches(0.55)
    add_text(slide, Inches(0.8), Inches(3.7), Inches(11), Inches(3),
        "Relay chain: Coerce DC → relay NTLM to AD CS (ESC8) → get DC certificate → authenticate as DC → DCSync.\n\n"
        "This is a complete domain takeover from any network position that can reach the DC.\n\n"
        "Defense:\n"
        "▸ Enforce EPA (Extended Protection for Authentication) on all services\n"
        "▸ Require LDAP signing and LDAP channel binding\n"
        "▸ Disable NTLM where possible (Kerberos only)\n"
        "▸ Remove HTTP enrollment endpoints from CAs\n"
        "▸ Monitor 4624 logon events for NTLM from DC computer accounts",
        13, LGRAY)

    # 10 — Golden/Silver Ticket
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "Golden Ticket vs Silver Ticket", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    box(slide, Inches(0.5), Inches(1.3), Inches(5.8), Inches(0.6), DGRAY, "Golden Ticket (TGT forgery)", 14, YELLOW, YELLOW)
    add_text(slide, Inches(0.7), Inches(2.1), Inches(5.5), Inches(2.5),
        "▸ Requires: krbtgt NTLM hash (from DCSync)\n"
        "▸ Forges TGT for ANY user, ANY group\n"
        "▸ Valid for 10 years (default TGT lifetime)\n"
        "▸ Works across entire domain\n"
        "▸ Survives password resets (except krbtgt 2x)\n"
        "▸ Detection: TGT with unusual lifetime, no AS-REQ\n"
        "▸ Remediation: reset krbtgt TWICE (12h apart)",
        12, LGRAY)
    box(slide, Inches(7), Inches(1.3), Inches(5.8), Inches(0.6), DGRAY, "Silver Ticket (TGS forgery)", 14, PURPLE, PURPLE)
    add_text(slide, Inches(7.2), Inches(2.1), Inches(5.5), Inches(2.5),
        "▸ Requires: service account NTLM hash\n"
        "▸ Forges TGS for specific service only\n"
        "▸ Never touches KDC → harder to detect\n"
        "▸ Limited to single service (CIFS, HTTP, etc.)\n"
        "▸ PAC validation bypass (service trusts TGS)\n"
        "▸ Detection: TGS without corresponding TGT\n"
        "▸ Defense: enable PAC validation on services",
        12, LGRAY)
    add_text(slide, Inches(0.5), Inches(5.2), Inches(12), Inches(1),
        "Diamond Ticket: modify legitimate TGT (Rubeus diamond) — harder to detect than Golden.\n"
        "Sapphire Ticket: S4U2Self with krbtgt → get legitimate PAC → even stealthier.",
        13, YELLOW)

    # 11 — DCSync
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "DCSync Attack Mechanism", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    dc_steps = [("Attacker with\nreplication rights", RED), ("DRS GetNCChanges\n(DRSUAPI)", CYAN), ("DC replicates\nNTDS.dit data", YELLOW), ("Extract all\nhashes (krbtgt)", GREEN)]
    x = Inches(1)
    for txt, clr in dc_steps:
        box(slide, x, Inches(1.4), Inches(2.5), Inches(0.8), DGRAY, txt, 12, clr, clr)
        if x < Inches(8): arrow_r(slide, x+Inches(2.6), Inches(1.7), x+Inches(3.0), Inches(1.7), clr)
        x += Inches(3.1)
    add_text(slide, Inches(0.5), Inches(2.8), Inches(12), Inches(3),
        "Required privileges: DS-Replication-Get-Changes + DS-Replication-Get-Changes-All\n"
        "Default holders: Domain Admins, Enterprise Admins, DC computer accounts, replication partners.\n\n"
        "Tools: Mimikatz lsadump::dcsync, Impacket secretsdump.py, DSInternals\n\n"
        "Detection:\n"
        "▸ Event 4662: DS-Replication operations from non-DC source\n"
        "▸ Network: DRSUAPI traffic from workstation IPs\n"
        "▸ Honey: deploy decoy replication rights → alert on use\n\n"
        "DCSync extracts: NTLM hashes, Kerberos keys, password history, supplemental credentials.\n"
        "Follow-up: forge Golden Ticket (krbtgt), crack passwords offline, access any resource.",
        13, LGRAY)

    # 12 — Exchange/M365
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "Exchange Server & M365 Attack Surface", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    attacks_ex = [
        ("ProxyLogon (CVE-2021-26855)", "SSRF → bypass auth → write webshell. Pre-auth RCE. HAFNIUM campaign.", RED),
        ("ProxyShell (CVE-2021-34473)", "SSRF + path confusion + PowerShell deserialization. Pre-auth RCE.", RED),
        ("ProxyNotShell (CVE-2022-41040)", "SSRF + RCE but requires authentication. Abuses Autodiscover.", YELLOW),
        ("OWASSRF (CVE-2022-41080)", "OWA SSRF → bypass ProxyNotShell patches. Privilege escalation.", YELLOW),
        ("M365: Consent Phishing", "Trick user into granting app permissions → read mail, files, calendar.", CYAN),
        ("M365: Token Theft", "Steal OAuth refresh token → persistent access. AiTM proxy (Evilginx2).", GREEN),
        ("M365: Business Email Compromise", "Compromised mailbox → invoice fraud, wire transfer redirect.", PURPLE),
    ]
    y = Inches(1.2)
    for name, desc, clr in attacks_ex:
        box(slide, Inches(0.5), y, Inches(3.2), Inches(0.45), DGRAY, name, 10, clr, clr)
        add_text(slide, Inches(3.9), y, Inches(8.6), Inches(0.45), desc, 11, LGRAY)
        y += Inches(0.53)

    # 13 — Section divider
    section_slide(prs, "Mobile Security")

    # 14 — Android Architecture
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "Android Security Architecture", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    android_layers = [
        ("Applications", "Each app = unique UID + separate process. Permission model (runtime + install).", PURPLE),
        ("Framework", "Activity Manager, Package Manager, Content Providers. Intent-based IPC.", CYAN),
        ("ART Runtime", "AOT + JIT compilation. Memory safety improvements in each release.", GREEN),
        ("HAL / Native", "Camera, Audio, Sensors. Vendor blobs. HIDL/AIDL interfaces.", YELLOW),
        ("Linux Kernel", "SELinux (mandatory), seccomp-bpf, dm-verity, GKI (Generic Kernel Image).", RED),
    ]
    y = Inches(1.3)
    for name, desc, clr in android_layers:
        box(slide, Inches(1), y, Inches(2.2), Inches(0.55), DGRAY, name, 12, clr, clr)
        add_text(slide, Inches(3.5), y, Inches(9), Inches(0.55), desc, 12, LGRAY)
        y += Inches(0.65)
    add_text(slide, Inches(1), Inches(5.0), Inches(11), Inches(1.5),
        "Security features by version:\n"
        "▸ Android 10: scoped storage, BiometricPrompt API, TLS 1.3 default\n"
        "▸ Android 12: approximate location, Rust in platform, Bluetooth privacy\n"
        "▸ Android 13: photo picker, notification permissions, per-app language\n"
        "▸ Android 14: credential manager, MTE support, minimum SDK enforcement",
        13, LGRAY)

    # 15 — Android Sandbox
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "Android Application Sandbox Model", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    sandbox_comp = [
        ("Process Isolation", "Each app runs in own process with unique Linux UID/GID", CYAN),
        ("SELinux", "Mandatory Access Control — app_data_file type for each app", GREEN),
        ("Seccomp-BPF", "Restrict available syscalls per process (zygote policy)", YELLOW),
        ("App Sandbox", "/data/data/<package> — only readable by app's UID", RED),
        ("Verified Boot", "dm-verity ensures system partition integrity. AVB 2.0.", PURPLE),
        ("KeyStore (TEE)", "Hardware-backed key storage in TrustZone / StrongBox.", CYAN),
    ]
    y = Inches(1.2)
    for name, desc, clr in sandbox_comp:
        box(slide, Inches(1), y, Inches(2.5), Inches(0.45), DGRAY, name, 11, clr, clr)
        add_text(slide, Inches(3.8), y, Inches(8.7), Inches(0.45), desc, 12, LGRAY)
        y += Inches(0.55)
    add_text(slide, Inches(1), Inches(4.8), Inches(11), Inches(1),
        "Escape vectors: kernel vuln (dirty pipe/COW), driver bugs (GPU/camera), binder deserialization,\n"
        "WebView RCE → sandbox escape, accessibility service abuse, device admin abuse.",
        13, YELLOW)

    # 16 — iOS Architecture
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "iOS Security Architecture", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    ios_layers = [
        ("Secure Enclave (SEP)", "Separate processor. Key management, biometrics, boot verification. Own OS.", CYAN),
        ("KTRR / CTRR", "Kernel Text Readonly Region — hardware-enforced kernel code integrity.", GREEN),
        ("PAC (ARMv8.3)", "Pointer Authentication — forward/backward edge CFI in kernel + userspace.", YELLOW),
        ("PPL (Page Protection Layer)", "Protects code signing enforcement. Kernel can't modify code pages.", RED),
        ("Sandbox (Seatbelt)", "Per-app sandbox profiles. Mandatory for App Store apps.", PURPLE),
        ("Data Protection (NSFileProtection)", "Per-file encryption classes tied to device passcode + hardware key.", CYAN),
    ]
    y = Inches(1.2)
    for name, desc, clr in ios_layers:
        box(slide, Inches(0.5), y, Inches(3), Inches(0.45), DGRAY, name, 10, clr, clr)
        add_text(slide, Inches(3.8), y, Inches(8.7), Inches(0.45), desc, 11, LGRAY)
        y += Inches(0.55)
    add_text(slide, Inches(0.5), Inches(4.8), Inches(12), Inches(1),
        "iOS 16+: Lockdown Mode (reduces attack surface), Rapid Security Response,\n"
        "WebKit JIT disabled in Lockdown Mode, passkeys (FIDO2).",
        13, LGRAY)

    # 17 — iOS Exploit Chain
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "iOS Exploit Chain Structure", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    ios_chain = [
        ("WebKit\nType Confusion", RED),
        ("Renderer\nSandbox Escape", YELLOW),
        ("Kernel\nExploit", CYAN),
        ("PAC\nBypass", GREEN),
        ("Persistence\n(rare on iOS)", PURPLE),
    ]
    x = Inches(0.3)
    for txt, clr in ios_chain:
        box(slide, x, Inches(1.4), Inches(2.1), Inches(0.9), DGRAY, txt, 11, clr, clr)
        if x < Inches(9): arrow_r(slide, x+Inches(2.2), Inches(1.75), x+Inches(2.4), Inches(1.75), clr)
        x += Inches(2.5)
    add_text(slide, Inches(0.5), Inches(2.8), Inches(12), Inches(3),
        "Notable exploit chains:\n"
        "▸ FORCEDENTRY (NSO/Pegasus, 2021): zero-click iMessage → CoreGraphics integer overflow\n"
        "  → JBIG2 Turing-complete sandbox → kernel exploit. No user interaction.\n"
        "▸ BLASTPASS (2023): zero-click iMessage → PassKit attachment → WebP heap overflow.\n"
        "▸ Operation Triangulation (2023): iMessage → TrueType font → kernel → hardware feature abuse.\n\n"
        "NSO Pegasus: commercial spyware. Full device compromise. Used against journalists, activists.\n"
        "Pricing: iOS zero-click chain worth $1.5-2M on exploit market (Zerodium, gray market).\n\n"
        "Detection: iVerify, Amnesty International MVT, Apple Threat Notifications.",
        13, LGRAY)

    # 18 — Mobile Attack Comparison Chart
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "Mobile Attack Vectors — Android vs iOS", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    mpl_theme()
    fig, ax = plt.subplots(figsize=(10, 4.5))
    vectors = ["Malicious\nApps", "Phishing\n/SMS", "WebKit\nExploit", "Kernel\nVuln", "Zero-Click\n(iMessage)", "Physical\n(USB/JTAG)", "MDM\nBypass"]
    android_risk = [9, 8, 6, 7, 3, 7, 5]
    ios_risk = [2, 7, 7, 5, 8, 3, 4]
    x = range(len(vectors))
    w = 0.35
    ax.bar([p-w/2 for p in x], android_risk, w, label="Android", color="#00FF88", edgecolor="#444466")
    ax.bar([p+w/2 for p in x], ios_risk, w, label="iOS", color="#00D4FF", edgecolor="#444466")
    ax.set_xticks(x); ax.set_xticklabels(vectors, fontsize=9)
    ax.set_ylabel("Risk Level (1-10)", fontsize=12)
    ax.set_title("Mobile Attack Vector Comparison", fontsize=14, color="#00D4FF")
    ax.legend(facecolor="#1a1a2e", edgecolor="#444466", labelcolor="#cccccc")
    ax.grid(axis="y", alpha=0.3)
    embed_chart(slide, fig, Inches(1.5), Inches(1.2), Inches(10), Inches(5.5))

    # 19 — 5G Security
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "5G Security Architecture", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    fiveg = [
        ("SUPI → SUCI", "Permanent ID (SUPI) encrypted before transmission → SUCI. Prevents IMSI catching.", CYAN),
        ("Network Slicing", "Isolated virtual networks. Risk: slice isolation bypass, resource exhaustion.", GREEN),
        ("SEPP", "Security Edge Protection Proxy — replaces SS7 roaming with TLS+JWS. N32 interface.", YELLOW),
        ("PRINS/PFCP", "User plane function security. GTP-U encapsulation. Risk: UPF bypass.", RED),
        ("Edge Computing (MEC)", "Compute at network edge. Risk: shared infrastructure, lateral movement.", PURPLE),
        ("SBA (Service-Based)", "HTTP/2+TLS between NFs. Risk: NF impersonation, API abuse.", CYAN),
    ]
    y = Inches(1.2)
    for name, desc, clr in fiveg:
        box(slide, Inches(0.8), y, Inches(2.2), Inches(0.45), DGRAY, name, 11, clr, clr)
        add_text(slide, Inches(3.3), y, Inches(9.2), Inches(0.45), desc, 12, LGRAY)
        y += Inches(0.55)
    add_text(slide, Inches(0.8), Inches(4.8), Inches(11), Inches(1),
        "5G still vulnerable to: downgrade attacks (force 4G/3G fallback), baseband exploits,\n"
        "rogue gNB, RAN sharing vulnerabilities, O-RAN open interface attacks.",
        13, YELLOW)

    # 20 — Mobile malware timeline
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "Mobile Malware Family Timeline", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    mpl_theme()
    fig, ax = plt.subplots(figsize=(11, 4.5))
    years_m = [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
    families = ["Stagefright\n(Android)", "Pegasus\n(iOS) v1", "BankBot\nTrojan", "Triada\n(system)", "Joker\n(billing)", "EventBot\n(banking)", "FluBot\n(SMS worm)", "SharkBot\n(overlay)", "SpyNote\nRAT", "Vultur\nv2 (screen)"]
    colors_m = ["#FF4444","#00D4FF","#FF4444","#FFD700","#FF4444","#00FF88","#FF4444","#FFD700","#BB86FC","#FF4444"]
    ax.scatter(years_m, range(len(years_m)), c=colors_m, s=80, zorder=3)
    for i, (y_val, fam) in enumerate(zip(years_m, families)):
        ax.annotate(fam, (y_val, i), textcoords="offset points", xytext=(15,-5), fontsize=8, color="#cccccc")
    ax.set_xlabel("Year", fontsize=12)
    ax.set_title("Notable Mobile Malware Families", fontsize=14, color="#00D4FF")
    ax.set_yticks([]); ax.grid(axis="x", alpha=0.3)
    embed_chart(slide, fig, Inches(1), Inches(1.2), Inches(11.3), Inches(5.5))

    # 21 — Enterprise Mobile Defense
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "Enterprise Mobile Defense Stack", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    defenses = [
        ("MDM (Mobile Device Management)", "Enforce policies, remote wipe, certificate deployment. Intune, JAMF, VMware WS1.", CYAN),
        ("MAM (Mobile App Management)", "App-level policies without device enrollment. App protection policies, DLP.", GREEN),
        ("MTD (Mobile Threat Defense)", "On-device detection: network MitM, malicious apps, OS exploits. Lookout, Zimperium.", YELLOW),
        ("Conditional Access", "Require device compliance, MFA, location-based access. Azure AD / Entra ID.", RED),
        ("App Vetting", "Analyze apps before enterprise deployment. SAST/DAST on mobile apps.", PURPLE),
        ("Zero Trust Network Access", "Per-app VPN, identity-aware proxy. Replace full-device VPN.", CYAN),
    ]
    y = Inches(1.2)
    for name, desc, clr in defenses:
        box(slide, Inches(0.5), y, Inches(3.2), Inches(0.45), DGRAY, name, 10, clr, clr)
        add_text(slide, Inches(4.0), y, Inches(8.5), Inches(0.45), desc, 12, LGRAY)
        y += Inches(0.55)

    # 22 — Cross-reference
    takeaway_slide(prs, [
        "Domain 8: Web security → Exchange/OWA is primary initial access for AD compromise",
        "Domain 10: Cloud → Azure AD/Entra ID extends AD attack surface to cloud",
        "Domain 11: Malware → Mimikatz, Cobalt Strike used in lateral movement phase",
        "Domain 13: Cryptography → Kerberos, NTLM, certificate-based attacks",
        "Domain 17: Physical security → mobile device hardware attacks (JTAG, chip-off)",
        "Domain 23: Social engineering → phishing is #1 initial access for AD environments",
        "Domain 25: Threat intel → APT groups target AD (APT29, APT41, FIN7)",
        "Domain 27: Detection engineering → AD telemetry is core SOC data source",
    ], heading="Cross-Reference Map")

    out = "/media/renan/New Volume/PROIECT/STUDIO-LAVORO/library/15-SECURITY/presentations/07_Enterprise_AD_Mobile.pptx"
    prs.save(out)
    print(f"[+] Saved {out.split('/')[-1]}")


# ════════════════════════════════════════════════════════════════════
#  PRESENTATION 8 — ICS/OT, RF/SDR & Automotive Security
# ════════════════════════════════════════════════════════════════════
def gen_pres_08():
    prs = new_prs()
    title_slide(prs, "ICS/OT Security,\nRF/SDR & Automotive", "Domains 16, 20-21  ·  Purdue Model  ·  TRITON  ·  SDR  ·  CAN Bus  ·  V2X")

    agenda_slide(prs, [
        "Purdue Model Architecture", "ICS Attack Timeline",
        "TRITON Attack Chain", "Modbus TCP Protocol", "ICS Defense Architecture",
        "ICS Protocol Comparison", "SDR Architecture", "RF Signal Processing",
        "RF Attack Taxonomy", "Cellular Attack Surface", "GPS Spoofing",
        "Vehicle Network Architecture", "CAN Bus Structure & Attacks",
        "Keyless Entry Relay", "ADAS Attack Surface", "V2X Security",
    ])

    # 3 — Purdue Model
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "Purdue Model — ICS/OT Network Architecture", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    purdue = [
        ("Level 5", "Enterprise Network", "ERP, email, internet access", PURPLE),
        ("Level 4", "Site Business Planning", "Historian mirror, site scheduling", CYAN),
        ("Level 3.5", "DMZ / IDMZ", "Data diodes, jump servers, unidirectional gateways", RED),
        ("Level 3", "Site Operations", "Historian, OPC server, engineering workstation", GREEN),
        ("Level 2", "Area Supervisory", "HMI, SCADA server, alarm management", YELLOW),
        ("Level 1", "Basic Control", "PLC, RTU, DCS controllers", RED),
        ("Level 0", "Process", "Sensors, actuators, field devices", CYAN),
    ]
    y = Inches(1.2)
    for level, name, desc, clr in purdue:
        box(slide, Inches(0.8), y, Inches(1.2), Inches(0.45), DGRAY, level, 11, clr, clr)
        box(slide, Inches(2.2), y, Inches(2.2), Inches(0.45), DGRAY, name, 11, WHITE, clr)
        add_text(slide, Inches(4.7), y, Inches(7.8), Inches(0.45), desc, 12, LGRAY)
        y += Inches(0.55)
    add_text(slide, Inches(0.8), Inches(5.2), Inches(11), Inches(1),
        "Critical boundary: Level 3.5 DMZ separates IT (L4-5) from OT (L0-3).\n"
        "Attackers cross this boundary via: compromised jump servers, dual-homed hosts, USB drives,\n"
        "vendor remote access, or exposed OPC/SCADA protocols on IT network.",
        13, YELLOW)

    # 4 — ICS Attack Timeline Chart
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "ICS/OT Attack Timeline", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    mpl_theme()
    fig, ax = plt.subplots(figsize=(11, 4.5))
    ics_years = [2010, 2014, 2015, 2016, 2017, 2020, 2021, 2022]
    ics_events = ["Stuxnet\n(centrifuges)", "Havex\n(energy recon)", "BlackEnergy\n(Ukraine grid)", "INDUSTROYER\n(substation)", "TRITON\n(safety system)", "EKANS\n(ransomware)", "Oldsmar\n(water plant)", "PIPEDREAM\n(multi-ICS)"]
    impact = [10, 5, 8, 9, 10, 6, 4, 9]
    colors_i = ["#FF4444","#FFD700","#FF4444","#FF4444","#FF4444","#FFD700","#00D4FF","#FF4444"]
    ax.bar(ics_years, impact, color=colors_i, edgecolor="#444466", width=0.8)
    for y_val, yr, evt in zip(impact, ics_years, ics_events):
        ax.text(yr, y_val+0.2, evt, ha="center", fontsize=7, color="#cccccc")
    ax.set_xlabel("Year", fontsize=12); ax.set_ylabel("Impact Severity (1-10)", fontsize=12)
    ax.set_title("Major ICS/OT Attacks", fontsize=14, color="#00D4FF")
    ax.set_ylim(0, 12); ax.grid(axis="y", alpha=0.3)
    embed_chart(slide, fig, Inches(1), Inches(1.2), Inches(11.3), Inches(5.5))

    # 5 — TRITON
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "TRITON/TRISIS Attack Chain (2017)", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    triton = [("IT Network\nInitial Access", RED), ("Pivot to\nOT Network", YELLOW), ("Engineering\nWorkstation", CYAN), ("Triconex SIS\nController", GREEN), ("Safety Logic\nModified", PURPLE)]
    x = Inches(0.3)
    for txt, clr in triton:
        box(slide, x, Inches(1.4), Inches(2.1), Inches(0.9), DGRAY, txt, 11, clr, clr)
        if x < Inches(9): arrow_r(slide, x+Inches(2.2), Inches(1.75), x+Inches(2.4), Inches(1.75), clr)
        x += Inches(2.5)
    add_text(slide, Inches(0.5), Inches(2.8), Inches(12), Inches(3.5),
        "Target: Schneider Electric Triconex Safety Instrumented System (SIS) at Saudi petrochemical plant.\n"
        "Goal: Disable safety system → allow physical damage to plant. Could cause explosion/release.\n\n"
        "Attack details:\n"
        "▸ Custom framework: TRITON/TriStation protocol reverse-engineered\n"
        "▸ Injected rogue Triconex program via TriStation protocol (UDP port 1502)\n"
        "▸ Exploited 0-day in Triconex firmware (CVE-2018-7522)\n"
        "▸ Failed: logic bug caused SIS to enter safe state → attack detected\n\n"
        "Attribution: XENOTIME / TEMP.Veles → linked to Russian Central Scientific Research Institute (TsNIIkhM)\n\n"
        "First known attack specifically targeting safety systems — intent was physical harm.",
        13, LGRAY)

    # 6 — Modbus TCP
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "Modbus TCP Protocol Structure", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    fields = [
        ("Transaction ID\n(2 bytes)", CYAN),
        ("Protocol ID\n(2 bytes, 0x0000)", GREEN),
        ("Length\n(2 bytes)", YELLOW),
        ("Unit ID\n(1 byte)", RED),
        ("Function Code\n(1 byte)", PURPLE),
        ("Data\n(N bytes)", CYAN),
    ]
    x = Inches(0.3)
    for txt, clr in fields:
        box(slide, x, Inches(1.4), Inches(1.8), Inches(0.8), DGRAY, txt, 10, clr, clr)
        x += Inches(2.0)
    funcs = [
        ("FC 01", "Read Coils", "FC 05", "Write Single Coil"),
        ("FC 02", "Read Discrete Inputs", "FC 06", "Write Single Register"),
        ("FC 03", "Read Holding Registers", "FC 15", "Write Multiple Coils"),
        ("FC 04", "Read Input Registers", "FC 16", "Write Multiple Registers"),
    ]
    y = Inches(2.8)
    add_text(slide, Inches(1), y-Inches(0.4), Inches(5), Inches(0.4), "Common Function Codes:", 14, CYAN, True)
    for fc1, desc1, fc2, desc2 in funcs:
        add_text(slide, Inches(1), y, Inches(1), Inches(0.3), fc1, 12, YELLOW, True)
        add_text(slide, Inches(2.1), y, Inches(3), Inches(0.3), desc1, 12, LGRAY)
        add_text(slide, Inches(6), y, Inches(1), Inches(0.3), fc2, 12, YELLOW, True)
        add_text(slide, Inches(7.1), y, Inches(3), Inches(0.3), desc2, 12, LGRAY)
        y += Inches(0.35)
    add_text(slide, Inches(1), Inches(4.5), Inches(11), Inches(2),
        "Modbus has NO authentication, NO encryption, NO integrity checking.\n"
        "Any device on the network can read/write any register on any PLC.\n\n"
        "Attack: read sensor values (recon), write coils/registers (manipulate process),\n"
        "DoS via malformed packets, man-in-the-middle to forge responses.\n"
        "Defense: network segmentation, Modbus-aware IDS (e.g., Suricata), data diodes, allowlisting.",
        13, LGRAY)

    # 7 — ICS Defense Architecture
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "ICS/OT Defense Architecture", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    defenses = [
        ("Data Diodes", "Unidirectional network gateways. Physically prevent inbound traffic to OT. Waterfall, OPSWAT.", CYAN),
        ("IDMZ (Industrial DMZ)", "Segmentation between IT/OT. Jump servers, bastion hosts, no direct routing.", GREEN),
        ("OT IDS/IPS", "Deep packet inspection for ICS protocols. Claroty, Nozomi Networks, Dragos Platform.", YELLOW),
        ("Asset Inventory", "Passive discovery of all OT assets. MAC, IP, firmware versions, vulnerabilities.", RED),
        ("Allowlisting", "Application allowlisting on HMI/EWS. CyberArk, Carbon Black, SELinux.", PURPLE),
        ("Patch Management", "Vendor-validated patches only. Test in staging OT environment. Scheduled outage windows.", CYAN),
        ("Backup & Recovery", "Offline backups of PLC logic, HMI configs, historian data. Air-gapped.", GREEN),
    ]
    y = Inches(1.2)
    for name, desc, clr in defenses:
        box(slide, Inches(0.5), y, Inches(2.3), Inches(0.45), DGRAY, name, 11, clr, clr)
        add_text(slide, Inches(3.1), y, Inches(9.4), Inches(0.45), desc, 11, LGRAY)
        y += Inches(0.53)

    # 8 — ICS Protocol Comparison Chart
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "ICS Protocol Comparison", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    mpl_theme()
    fig, ax = plt.subplots(figsize=(10, 4.5))
    protos = ["Modbus\nTCP", "DNP3", "OPC UA", "EtherNet/IP\n(CIP)", "PROFINET", "IEC 61850\n(MMS)"]
    auth = [0, 2, 8, 3, 4, 5]
    encrypt = [0, 1, 9, 2, 5, 4]
    w = 0.35
    x = range(len(protos))
    ax.bar([p-w/2 for p in x], auth, w, label="Authentication", color="#00D4FF", edgecolor="#444466")
    ax.bar([p+w/2 for p in x], encrypt, w, label="Encryption", color="#00FF88", edgecolor="#444466")
    ax.set_xticks(x); ax.set_xticklabels(protos, fontsize=9)
    ax.set_ylabel("Security Feature Level (0-10)", fontsize=12)
    ax.set_title("ICS Protocol Security Features", fontsize=14, color="#00D4FF")
    ax.legend(facecolor="#1a1a2e", edgecolor="#444466", labelcolor="#cccccc")
    ax.set_ylim(0, 10); ax.grid(axis="y", alpha=0.3)
    embed_chart(slide, fig, Inches(1.5), Inches(1.2), Inches(10), Inches(5.5))

    # 9 — Section divider
    section_slide(prs, "RF and SDR Security")

    # 10 — SDR Architecture
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "Software Defined Radio Architecture", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    sdr = [("Antenna\n(Rx/Tx)", CYAN), ("RF Frontend\n(LNA, Filter)", GREEN), ("ADC / DAC\nConversion", YELLOW), ("Digital Signal\nProcessing (FPGA)", RED), ("Host Software\n(GNU Radio)", PURPLE)]
    x = Inches(0.3)
    for txt, clr in sdr:
        box(slide, x, Inches(1.4), Inches(2.1), Inches(0.9), DGRAY, txt, 11, clr, clr)
        if x < Inches(9): arrow_r(slide, x+Inches(2.2), Inches(1.75), x+Inches(2.4), Inches(1.75), clr)
        x += Inches(2.5)
    platforms = [
        ("RTL-SDR ($25)", "Rx only, 24-1766 MHz, 8-bit ADC, 2.4 MSPS. Great for beginners.", CYAN),
        ("HackRF One ($300)", "Tx+Rx, 1-6000 MHz, 8-bit, 20 MSPS. Half-duplex. Most popular.", GREEN),
        ("USRP B200 ($1000+)", "Full duplex, 70-6000 MHz, 12-bit, 56 MSPS. Professional.", YELLOW),
        ("BladeRF 2.0 ($480)", "Full duplex, 47-6000 MHz, 12-bit, 61.44 MSPS. FPGA flexibility.", RED),
        ("LimeSDR ($300)", "Full duplex, 100 kHz-3.8 GHz, 12-bit, 61.44 MSPS. Open source.", PURPLE),
    ]
    y = Inches(2.8)
    for name, desc, clr in platforms:
        box(slide, Inches(0.8), y, Inches(2.5), Inches(0.4), DGRAY, name, 10, clr, clr)
        add_text(slide, Inches(3.5), y, Inches(9), Inches(0.4), desc, 11, LGRAY)
        y += Inches(0.48)

    # 11 — RF Signal Processing Pipeline
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "RF Signal Processing Pipeline", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    pipeline = [("RF\nCapture", CYAN), ("IQ\nRecording", GREEN), ("Demodulation\n(AM/FM/PSK)", YELLOW), ("Protocol\nDecoding", RED), ("Data\nAnalysis", PURPLE)]
    x = Inches(0.3)
    for txt, clr in pipeline:
        box(slide, x, Inches(1.4), Inches(2.1), Inches(0.9), DGRAY, txt, 11, clr, clr)
        if x < Inches(9): arrow_r(slide, x+Inches(2.2), Inches(1.75), x+Inches(2.4), Inches(1.75), clr)
        x += Inches(2.5)
    add_text(slide, Inches(0.5), Inches(2.8), Inches(12), Inches(3.5),
        "GNU Radio flow: Source → Channel Filter → Demod → Clock Recovery → Slicer → Decoder\n\n"
        "Key analysis tools:\n"
        "▸ Inspectrum: spectrogram analysis, manual bit extraction\n"
        "▸ Universal Radio Hacker (URH): automated signal analysis and protocol RE\n"
        "▸ SigDigger: real-time signal inspection with GNU Radio backend\n"
        "▸ rtl_433: automated decoding of 400+ IoT protocols (weather stations, TPMS, doorbells)\n"
        "▸ gr-lora / gr-lorawan: LoRa demodulation and decoding\n\n"
        "IQ data: In-phase + Quadrature representation of RF signal. Complex samples.\n"
        "Sample rate = bandwidth. Nyquist: sample at ≥ 2× signal bandwidth.",
        13, LGRAY)

    # 12 — RF Attack Taxonomy
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "RF Protocol Attack Taxonomy", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    rf_attacks = [
        ("Replay", "Record and retransmit valid signal. Effective vs fixed-code systems (garage doors, old car fobs).", RED),
        ("Relay", "Real-time relay of signal over distance. Keyless entry attack (extends range to 100m+).", YELLOW),
        ("Jamming", "Overwhelm legitimate signal. Selective jamming (jam response, not request) for stealthiness.", CYAN),
        ("Spoofing", "Generate fake signal (GPS, ADS-B, cellular). Can redirect navigation, fake aircraft.", GREEN),
        ("Eavesdropping", "Passive interception. Analog: trivial. Digital: depends on encryption (often none).", PURPLE),
        ("Protocol Exploitation", "Fuzzing wireless protocols. Discover parsing bugs in firmware receivers.", RGBColor(0x80,0x80,0xFF)),
    ]
    y = Inches(1.2)
    for name, desc, clr in rf_attacks:
        box(slide, Inches(0.8), y, Inches(2), Inches(0.45), DGRAY, name, 12, clr, clr)
        add_text(slide, Inches(3.1), y, Inches(9.4), Inches(0.45), desc, 11, LGRAY)
        y += Inches(0.55)

    # 13 — GSM/Cellular
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "Cellular Network Attack Surface", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    cell_attacks = [
        ("IMSI Catcher", "Fake BTS (Stingray). Phone connects to strongest signal. Intercept calls, SMS, location.", RED),
        ("A5/1 Crack", "GSM encryption broken. Rainbow tables (Kraken project). Real-time decryption.", YELLOW),
        ("Downgrade Attack", "Force phone from 4G/5G to 2G (no auth). Then IMSI catch or intercept.", CYAN),
        ("Baseband Exploit", "Attack modem processor directly via OTA messages. No user interaction.", GREEN),
        ("SIM Swapping", "Social engineer carrier to port number. Bypass SMS 2FA. Account takeover.", PURPLE),
        ("TETRA:BURST", "TETRA radio encryption broken (2023). Affects police, military, utilities globally.", RED),
    ]
    y = Inches(1.2)
    for name, desc, clr in cell_attacks:
        box(slide, Inches(0.8), y, Inches(2.2), Inches(0.45), DGRAY, name, 11, clr, clr)
        add_text(slide, Inches(3.3), y, Inches(9.2), Inches(0.45), desc, 11, LGRAY)
        y += Inches(0.55)

    # 14 — GPS Spoofing
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "GPS Spoofing Attack Mechanism", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    gps_flow = [("SDR Transmitter\n(HackRF/USRP)", RED), ("Generate Fake\nGPS L1 Signal", YELLOW), ("Overpower Real\nSatellite Signal", CYAN), ("Victim GPS Lock\non Fake Position", GREEN)]
    x = Inches(1)
    for txt, clr in gps_flow:
        box(slide, x, Inches(1.4), Inches(2.5), Inches(0.8), DGRAY, txt, 11, clr, clr)
        if x < Inches(8): arrow_r(slide, x+Inches(2.6), Inches(1.7), x+Inches(3.0), Inches(1.7), clr)
        x += Inches(3.1)
    add_text(slide, Inches(0.5), Inches(2.8), Inches(12), Inches(3),
        "GPS signals are weak (~-130 dBm at surface). A few watts of TX power can overpower them.\n\n"
        "Targets: drones (forced landing/redirect), shipping (route manipulation), financial timestamps,\n"
        "autonomous vehicles, precision agriculture, cellular network timing.\n\n"
        "Tools: gps-sdr-sim + HackRF, Spirent (commercial), custom USRP setups.\n\n"
        "Defense: multi-constellation (GPS+Galileo+GLONASS+BeiDou), chipset-level spoofing detection,\n"
        "antenna arrays for direction-of-arrival, authenticated civil signals (Galileo OSNMA).\n"
        "CAUTION: GPS spoofing transmission is illegal in most jurisdictions (federal offense in US).",
        13, LGRAY)

    # 15 — Section divider
    section_slide(prs, "Automotive Security")

    # 16 — Vehicle Network Architecture
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "Vehicle Network Architecture", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    bus_types = [
        ("CAN Bus (Classic)", "500 kbps, broadcast, no auth. Powertrain, chassis. Dominant bus.", CYAN),
        ("CAN FD", "Up to 8 Mbps data phase, 64-byte payload. Backward compatible.", GREEN),
        ("Automotive Ethernet", "100BASE-T1/1000BASE-T1. Point-to-point. ADAS, infotainment. TCP/IP stack.", YELLOW),
        ("LIN Bus", "20 kbps, single-wire. Low-cost: mirrors, seats, windows.", RED),
        ("FlexRay", "10 Mbps, time-triggered. Safety-critical: steer-by-wire, brake-by-wire.", PURPLE),
        ("Central Gateway ECU", "Bridges all buses. Firewall rules between domains. Attack bottleneck.", CYAN),
    ]
    y = Inches(1.2)
    for name, desc, clr in bus_types:
        box(slide, Inches(0.5), y, Inches(2.8), Inches(0.45), DGRAY, name, 11, clr, clr)
        add_text(slide, Inches(3.6), y, Inches(9), Inches(0.45), desc, 12, LGRAY)
        y += Inches(0.55)
    add_text(slide, Inches(0.5), Inches(4.8), Inches(12), Inches(1),
        "Modern vehicles: 70-150 ECUs, 100M+ lines of code. Attack surface spans OBD-II, Bluetooth,\n"
        "Wi-Fi, cellular (telematics), USB, TPMS (tire pressure), key fob, and OTA update channels.",
        13, YELLOW)

    # 17 — CAN Bus Frame Structure
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "CAN Bus Frame Structure", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    can_fields = [
        ("SOF\n1 bit", CYAN), ("Arb ID\n11/29 bit", GREEN), ("Control\n6 bits", YELLOW), ("Data\n0-8 bytes", RED), ("CRC\n15 bits", PURPLE), ("ACK\n2 bits", CYAN), ("EOF\n7 bits", GREEN)]
    x = Inches(0.3)
    for txt, clr in can_fields:
        w = Inches(1.5) if "Data" in txt or "Arb" in txt else Inches(1.3)
        box(slide, x, Inches(1.4), w, Inches(0.7), DGRAY, txt, 10, clr, clr)
        x += w + Inches(0.15)
    add_text(slide, Inches(0.5), Inches(2.5), Inches(12), Inches(3.5),
        "CAN bus security problems:\n"
        "▸ No authentication: any node can send any arbitration ID\n"
        "▸ No encryption: all data transmitted in plaintext on shared bus\n"
        "▸ Broadcast: every node sees every message\n"
        "▸ Priority by ID: lower arbitration ID = higher priority → DoS via ID 0x000\n"
        "▸ No source identification: impossible to determine which ECU sent a frame\n\n"
        "SecOC (Secure Onboard Communication) — AUTOSAR standard:\n"
        "▸ Adds MAC (Message Authentication Code) to CAN frames\n"
        "▸ Freshness value prevents replay\n"
        "▸ Challenge: limited payload space (8 bytes classic CAN), key distribution\n"
        "▸ Adoption: new vehicles from 2023+, but retrofit impossible for existing fleet",
        13, LGRAY)

    # 18 — CAN Attack Types Chart
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "CAN Bus Attack Classification", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    can_attacks = [
        ("Replay", "Record valid CAN frames → retransmit. Unlock doors, start engine, disable brakes.", RED),
        ("Injection", "Send crafted CAN messages. Steer, accelerate, apply brakes (Miller & Valasek, 2015 Jeep).", RED),
        ("Bus-Off DoS", "Trigger error frames → increment error counter → target ECU enters bus-off state.", YELLOW),
        ("Fuzzing", "Send random CAN IDs/data. Discover undocumented commands. Map ECU responses.", CYAN),
        ("Diagnostic Abuse", "UDS (Unified Diagnostic Services) commands: flash ECU, disable immobilizer.", GREEN),
        ("Masquerade", "Impersonate legitimate ECU after disabling it. Undetectable without sender ID.", PURPLE),
    ]
    y = Inches(1.2)
    for name, desc, clr in can_attacks:
        box(slide, Inches(0.8), y, Inches(2), Inches(0.45), DGRAY, name, 12, clr, clr)
        add_text(slide, Inches(3.1), y, Inches(9.4), Inches(0.45), desc, 11, LGRAY)
        y += Inches(0.55)
    add_text(slide, Inches(0.8), Inches(4.8), Inches(11), Inches(1),
        "Tools: can-utils (Linux), SavvyCAN, CANtact, PCAN adapters, python-can, caringcaribou.\n"
        "Access: OBD-II port (physical), compromised telematics unit (remote — Jeep hack 2015).",
        13, YELLOW)

    # 19 — Keyless Entry Relay
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "Keyless Entry Relay Attack (PKES)", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    relay_steps = [("Key Fob\n(in house)", GREEN), ("Relay Device 1\n(near key)", RED), ("RF Signal\nAmplified", YELLOW), ("Relay Device 2\n(near car)", RED), ("Car Unlocks\n+ Starts", PURPLE)]
    x = Inches(0.3)
    for txt, clr in relay_steps:
        box(slide, x, Inches(1.4), Inches(2.1), Inches(0.9), DGRAY, txt, 11, clr, clr)
        if x < Inches(9): arrow_r(slide, x+Inches(2.2), Inches(1.75), x+Inches(2.4), Inches(1.75), clr)
        x += Inches(2.5)
    add_text(slide, Inches(0.5), Inches(2.8), Inches(12), Inches(3),
        "PKES (Passive Keyless Entry and Start): car sends LF challenge → key responds UHF.\n"
        "Relay extends the range from ~2m to 100m+. Key thinks it's next to car.\n\n"
        "Equipment: ~$50-200 (Bluetooth relay boards, RTL-SDR + amplifier, or commercial kits).\n"
        "Time to steal: <60 seconds. No forensic evidence on the vehicle.\n\n"
        "Defense:\n"
        "▸ UWB (Ultra-Wideband) ranging — measures actual distance, not just presence. Apple AirTag tech.\n"
        "▸ Motion sensor in key fob — disable transmission when fob is stationary\n"
        "▸ Faraday pouch for key storage at home\n"
        "▸ BLE + UWB combo (BMW Digital Key Plus, Apple Car Key)",
        13, LGRAY)

    # 20 — ADAS Attack Surface
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "ADAS / Autonomous Vehicle Attack Surface", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    adas = [
        ("Camera (Vision)", "Adversarial patches on signs → misclassify STOP as speed limit. Physical adversarial ML.", RED),
        ("LiDAR", "Spoofing with IR laser → inject ghost objects. Relay attack → remove real objects.", YELLOW),
        ("Radar", "Jamming → blind the sensor. Spoofing with signal generator. Less explored.", CYAN),
        ("GPS/GNSS", "Position spoofing → incorrect localization. Route manipulation. Drift attacks.", GREEN),
        ("V2X Messages", "Forge BSM (Basic Safety Messages) → phantom vehicles, fake hazard warnings.", PURPLE),
        ("OTA Updates", "Compromise update server or intercept update → flash malicious firmware.", RED),
    ]
    y = Inches(1.2)
    for name, desc, clr in adas:
        box(slide, Inches(0.5), y, Inches(2.3), Inches(0.45), DGRAY, name, 11, clr, clr)
        add_text(slide, Inches(3.1), y, Inches(9.4), Inches(0.45), desc, 11, LGRAY)
        y += Inches(0.55)
    add_text(slide, Inches(0.5), Inches(4.8), Inches(12), Inches(1),
        "Sensor fusion: combining camera+LiDAR+radar should increase robustness.\n"
        "But: if attacker can affect multiple sensors consistently, fusion can be fooled.\n"
        "ISO/SAE 21434: automotive cybersecurity engineering standard. UNECE WP.29 R155/R156.",
        13, YELLOW)

    # 21 — V2X Security
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "V2X Communication Security", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    v2x_comp = [
        ("DSRC (IEEE 802.11p)", "5.9 GHz, 10 MHz channels. Low latency. US originally. WAVE/1609.x stack.", CYAN),
        ("C-V2X (3GPP)", "PC5 sidelink (direct) + Uu (network-assisted). Cellular ecosystem. Gaining adoption.", GREEN),
        ("PKI (SCMS)", "Security Credential Management System. Pseudonym certificates for privacy.", YELLOW),
        ("Misbehavior Detection", "V2X messages signed but can be semantically false. ML-based detection needed.", RED),
        ("Privacy", "Rotating pseudonym certificates prevent long-term tracking. Certificate change strategy.", PURPLE),
    ]
    y = Inches(1.2)
    for name, desc, clr in v2x_comp:
        box(slide, Inches(0.5), y, Inches(2.8), Inches(0.45), DGRAY, name, 10, clr, clr)
        add_text(slide, Inches(3.6), y, Inches(9), Inches(0.45), desc, 12, LGRAY)
        y += Inches(0.55)
    add_text(slide, Inches(0.5), Inches(4.3), Inches(12), Inches(2),
        "V2X attacks: forge BSM (collision avoidance manipulation), Sybil (fake multiple vehicles),\n"
        "replay old BSMs, DoS via channel flooding, position falsification.\n\n"
        "Challenge: real-time verification. 10 Hz BSM rate × hundreds of vehicles = thousands of\n"
        "signature verifications per second. Hardware crypto acceleration required (e.g., Infineon SLI 97).",
        13, LGRAY)

    # 22 — Defense Recommendations
    slide = blank(prs)
    add_text(slide, Inches(0.8), Inches(0.3), Inches(11), Inches(0.7), "ICS/RF/Automotive Defense Recommendations", 28, WHITE, True)
    thin_line(slide, Inches(0.8), Inches(1.0), Inches(12.5), Inches(1.0), CYAN)
    recs = [
        "ICS: Implement Purdue Model segmentation with IDMZ, deploy OT-specific IDS (Dragos/Claroty)",
        "ICS: Data diodes for historian replication, never allow inbound IT→OT unless through bastion",
        "RF: Monitor spectrum for unauthorized transmissions, use frequency hopping where possible",
        "RF: Encrypt all wireless links, mutual authentication, rolling codes instead of fixed codes",
        "Auto: Implement SecOC on all safety-critical CAN messages, UWB for keyless entry",
        "Auto: Segment vehicle buses via gateway ECU, IDS on CAN bus for anomaly detection",
        "Cross-domain: OT assets should be inventoried and monitored like IT assets",
        "Compliance: IEC 62443 (ICS), ISO/SAE 21434 (auto), ETSI EN 303 645 (IoT)",
    ]
    y = Inches(1.2)
    colors = [CYAN, CYAN, GREEN, GREEN, YELLOW, YELLOW, RED, PURPLE]
    for i, rec in enumerate(recs):
        box(slide, Inches(0.8), y, Inches(11.5), Inches(0.45), DGRAY, f"▸  {rec}", 12, LGRAY, colors[i])
        y += Inches(0.53)

    # 23 — Cross-reference
    takeaway_slide(prs, [
        "Domain 9: Network security → ICS protocols are network protocols with zero security",
        "Domain 12: Reverse engineering → firmware RE is critical for ICS/automotive vuln research",
        "Domain 17: Physical security → fault injection, side channels apply to automotive ECUs",
        "Domain 18: Adversarial ML → ADAS sensor attacks are adversarial ML in the physical world",
        "Domain 20: RF/SDR → GPS spoofing, keyless entry, cellular attacks are RF attacks",
        "Domain 25: Threat intel → ICS-focused APT groups (XENOTIME, SANDWORM, CHERNOVITE)",
        "Domain 27: Defense architecture → ICS requires specialized security architecture",
        "Domain 28: IoT → vehicle telematics units are IoT devices with automotive constraints",
    ], heading="Cross-Reference Map")

    out = "/media/renan/New Volume/PROIECT/STUDIO-LAVORO/library/15-SECURITY/presentations/08_ICS_RF_Automotive.pptx"
    prs.save(out)
    print(f"[+] Saved {out.split('/')[-1]}")


if __name__ == "__main__":
    gen_pres_07()
    gen_pres_08()
    print("[✓] Presentations 7 & 8 generated successfully.")
