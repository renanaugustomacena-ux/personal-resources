# Tutorial Linux 35 — Compliance, OpenSCAP e Automazione della Sicurezza

> **Campo:** 02-LINUX-POWERUSER
> **Scope:** OpenSCAP, ansible compliance, NIST/CIS/PCI-DSS controls, automated remediation, reporting
> **Prerequisiti:** `tutorial_linux_34_hardening.md`, `tutorial_linux_31_ansible.md`
> **Durata stimata:** 12-16 ore

---

## Mappa concettuale

```
Compliance e Scanning
│
├── Standard di riferimento
│   ├── CIS Benchmark (Center for Internet Security)
│   ├── NIST SP 800-53 (US Government)
│   ├── PCI-DSS (Payment Card Industry)
│   └── DISA STIG (Department of Defense)
│
├── Strumenti
│   ├── OpenSCAP (SCAP scanner open source)
│   ├── oscap (CLI scanner)
│   ├── scap-workbench (GUI)
│   └── ComplianceAsCode (profili SCAP)
│
├── Automazione remediation
│   ├── Ansible role: ansible-lockdown
│   ├── Generazione automatica da OpenSCAP
│   └── CI/CD compliance gate
│
└── Reporting
    ├── HTML report oscap
    ├── Dashboard Grafana
    └── Integrazione SIEM
```

---

# Parte A — OpenSCAP

---

## A1. Installazione e setup

```bash
# OpenSCAP: implementazione open source dello standard SCAP
# SCAP = Security Content Automation Protocol (NIST)

apt install openscap-scanner scap-security-guide

# Profili disponibili (SSG = SCAP Security Guide)
ls /usr/share/xml/scap/ssg/content/
# ssg-ubuntu2204-ds.xml    — Ubuntu 22.04
# ssg-ubuntu2404-ds.xml    — Ubuntu 24.04
# ssg-debian12-ds.xml      — Debian 12
# ssg-rhel9-ds.xml         — RHEL 9

# Lista profili disponibili per Ubuntu
oscap info /usr/share/xml/scap/ssg/content/ssg-ubuntu2204-ds.xml \
    | grep "Profile\|Id:"

# Output (esempio):
# Id: xccdf_org.ssgproject.content_profile_cis_level1_server
# Title: CIS Ubuntu Linux 22.04 LTS Benchmark for Level 1 - Server
# Id: xccdf_org.ssgproject.content_profile_cis_level2_server
# Title: CIS Ubuntu Linux 22.04 LTS Benchmark for Level 2 - Server
# Id: xccdf_org.ssgproject.content_profile_stig
# Title: Canonical Ubuntu 22.04 LTS Security Technical Implementation Guide
```

> **Analogia:** OpenSCAP è come un ispettore di conformità con un libretto di controllo standardizzato (SCAP). Il libretto (profilo) definisce esattamente ogni regola da verificare — e come verificarla automaticamente. L'ispezione produce un rapporto con pass/fail per ogni regola e, spesso, anche le istruzioni precise per rimediare. Non è un parere soggettivo: ogni controllo ha una metodologia definita dall'ente che ha scritto lo standard.

---

## A2. Scansione di conformità

```bash
# Scansione completa con profilo CIS Level 1 Server
oscap xccdf eval \
    --profile xccdf_org.ssgproject.content_profile_cis_level1_server \
    --results /tmp/scan-results.xml \
    --report /tmp/scan-report.html \
    --oval-results \
    /usr/share/xml/scap/ssg/content/ssg-ubuntu2204-ds.xml

# Apri report HTML nel browser
# firefox /tmp/scan-report.html

# Scansione solo alcune regole (per velocità)
oscap xccdf eval \
    --profile xccdf_org.ssgproject.content_profile_cis_level1_server \
    --rule xccdf_org.ssgproject.content_rule_sshd_disable_root_login \
    /usr/share/xml/scap/ssg/content/ssg-ubuntu2204-ds.xml

# Risultato
echo "Exit code: $?"
# 0 = tutti i check passati
# 1 = errore di runtime
# 2 = almeno un check fallito
# 101 = almeno un risultato UNKNOWN

# Analizza risultati XML
oscap xccdf generate report /tmp/scan-results.xml > /tmp/report-da-xml.html

# Statistiche rapide
grep -E "pass|fail" /tmp/scan-results.xml | \
    awk -F'"' '{print $2}' | sort | uniq -c
```

---

## A3. Remediation automatica

```bash
# OpenSCAP può generare script di remediation automatica
# ATTENZIONE: verifica sempre lo script prima di eseguirlo su produzione!

# Genera script bash per remediation
oscap xccdf generate fix \
    --profile xccdf_org.ssgproject.content_profile_cis_level1_server \
    --fix-type sh \
    /usr/share/xml/scap/ssg/content/ssg-ubuntu2204-ds.xml \
    > /tmp/remediation.sh

# Genera playbook Ansible per remediation (più sicuro!)
oscap xccdf generate fix \
    --profile xccdf_org.ssgproject.content_profile_cis_level1_server \
    --fix-type ansible \
    /usr/share/xml/scap/ssg/content/ssg-ubuntu2204-ds.xml \
    > /tmp/remediation-playbook.yml

# Genera solo remediation per regole che hanno fallito
oscap xccdf generate fix \
    --result-id "" \
    --fix-type ansible \
    /tmp/scan-results.xml \
    > /tmp/remediation-only-failed.yml

# Applica remediation Ansible
ansible-playbook /tmp/remediation-playbook.yml --check   # dry run
ansible-playbook /tmp/remediation-playbook.yml           # applica
```

---

# Parte B — Ansible Compliance

---

## B1. ansible-lockdown

```bash
# ansible-lockdown: role Ansible per CIS Benchmark
# Repository: https://github.com/ansible-lockdown

pip install ansible
ansible-galaxy install MindPointGroup.UBUNTU22-CIS

# Playbook compliance
cat > compliance-playbook.yml << 'EOF'
---
- name: CIS Ubuntu 22.04 Hardening
  hosts: all
  become: true
  vars:
    # Disabilita regole troppo aggressive per il tuo ambiente
    ubuntu22cis_rule_1_1_1_1: true    # cramfs
    ubuntu22cis_rule_2_1_2: false     # disabilita servizi (potrebbe rompere cose)
    ubuntu22cis_rule_5_2_4: true      # SSH: no empty passwords
    ubuntu22cis_rule_5_2_11: true     # SSH: max auth tries
    
    # Personalizzazioni SSH
    ubuntu22cis_ssh_maxauthtries: 4
    ubuntu22cis_sshd_allow_groups: "sshusers"
    ubuntu22cis_sshd_deny_users: "root"

  roles:
    - MindPointGroup.UBUNTU22-CIS
EOF

# Dry run prima
ansible-playbook compliance-playbook.yml --check --diff -l staging

# Applica su staging
ansible-playbook compliance-playbook.yml -l staging

# Verifica con OpenSCAP dopo remediation
oscap xccdf eval \
    --profile xccdf_org.ssgproject.content_profile_cis_level1_server \
    --results /tmp/post-remediation.xml \
    --report /tmp/post-remediation.html \
    /usr/share/xml/scap/ssg/content/ssg-ubuntu2204-ds.xml
```

---

## B2. Compliance come CI/CD gate

```yaml
# .github/workflows/compliance-check.yml
name: Compliance Scan

on:
  push:
    branches: [main]
  schedule:
    - cron: '0 3 * * *'   # daily 03:00

jobs:
  compliance:
    runs-on: ubuntu-22.04
    steps:
      - uses: actions/checkout@v4

      - name: Installa OpenSCAP e SSG
        run: |
          sudo apt-get install -y openscap-scanner scap-security-guide

      - name: Scansione CIS Level 1
        run: |
          sudo oscap xccdf eval \
            --profile xccdf_org.ssgproject.content_profile_cis_level1_server \
            --results results.xml \
            --report compliance-report.html \
            /usr/share/xml/scap/ssg/content/ssg-ubuntu2204-ds.xml
          echo "Exit code: $?"

      - name: Verifica soglia minima
        run: |
          PASS=$(grep -c 'result>pass<' results.xml || true)
          FAIL=$(grep -c 'result>fail<' results.xml || true)
          TOTAL=$((PASS + FAIL))
          SCORE=$(echo "scale=2; $PASS * 100 / $TOTAL" | bc)
          echo "Score: $SCORE% ($PASS/$TOTAL)"
          # Fail se score < 80%
          if (( $(echo "$SCORE < 80" | bc -l) )); then
            echo "ERRORE: Compliance score sotto soglia (80%)"
            exit 1
          fi

      - name: Upload report
        uses: actions/upload-artifact@v4
        with:
          name: compliance-report
          path: compliance-report.html
```

---

# Parte C — Standard Specifici

---

## C1. PCI-DSS controlli chiave

```bash
# PCI-DSS Requirement 1 — Firewall
# Verifica regole firewall
ufw status verbose
iptables -L -n -v --line-numbers

# PCI-DSS Requirement 2 — No default password/config
# Verifica nessun servizio con credenziali di default
# Usa tool come Nmap con script nmap --script auth
nmap -sV --script auth 127.0.0.1

# PCI-DSS Requirement 6 — Patch management
# Verifica aggiornamenti pendenti
apt list --upgradable 2>/dev/null | wc -l
# Tutto dovrebbe essere aggiornato

# PCI-DSS Requirement 7 — Least privilege
# Verifica utenti con sudo
getent group sudo wheel | tr ':' '\n' | tail -1 | tr ',' '\n'

# PCI-DSS Requirement 8 — Identificazione e autenticazione
# Password policy
grep -E "minlen|minclass|maxrepeat" /etc/security/pwquality.conf
# Account lockout
grep -E "deny|unlock_time" /etc/pam.d/common-auth

# PCI-DSS Requirement 10 — Log e audit
# Verifica auditd
systemctl is-active auditd
auditctl -l | head -20   # regole audit attive

# PCI-DSS Requirement 11 — Test sicurezza regolari
# Scan vulnerabilità con OpenVAS (community)
# docker run -d -p 9392:9392 mikesplain/openvas

# PCI-DSS Requirement 12 — Policy sicurezza
# Documentazione, procedure, training
echo "Verificare documentazione manuale"
```

---

## C2. Script di audit continuo

```bash
#!/usr/bin/env bash
# /usr/local/bin/security-audit.sh
# Eseguito da cron, invia alert se trova problemi
set -euo pipefail

REPORT="/var/log/security-audit-$(date +%Y%m%d).log"
ALERT_EMAIL="security@esempio.it"
HOSTNAME=$(hostname -f)
PROBLEMS=0

log() { echo "[$(date '+%H:%M:%S')] $*" | tee -a "$REPORT"; }
problem() { log "PROBLEMA: $*"; ((PROBLEMS++)) || true; }
ok() { log "OK: $*"; }

# 1. SSH hardening
if sshd -T 2>/dev/null | grep -q "^permitrootlogin yes"; then
    problem "SSH: PermitRootLogin è abilitato!"
else
    ok "SSH: PermitRootLogin disabilitato"
fi

if sshd -T 2>/dev/null | grep -q "^passwordauthentication yes"; then
    problem "SSH: PasswordAuthentication è abilitato!"
else
    ok "SSH: PasswordAuthentication disabilitato"
fi

# 2. Firewall
if ! systemctl is-active ufw &>/dev/null && ! nft list ruleset &>/dev/null; then
    problem "Nessun firewall attivo!"
else
    ok "Firewall attivo"
fi

# 3. Servizi non necessari
for svc in telnet ftp rsh; do
    if systemctl is-active "$svc" &>/dev/null; then
        problem "Servizio insicuro attivo: $svc"
    fi
done

# 4. SUID/SGID file inattesi
SUID_FILES=$(find /usr /bin /sbin -perm /4000 -o -perm /2000 2>/dev/null | sort)
EXPECTED_SUID="/usr/bin/sudo /usr/bin/passwd /usr/bin/newgrp /usr/bin/gpasswd"
while IFS= read -r f; do
    if ! echo "$EXPECTED_SUID" | grep -qw "$f"; then
        problem "SUID/SGID inatteso: $f"
    fi
done <<< "$SUID_FILES"

# 5. Aggiornamenti sicurezza pendenti
SECURITY_UPDATES=$(apt list --upgradable 2>/dev/null | grep -c security || true)
if [[ $SECURITY_UPDATES -gt 0 ]]; then
    problem "$SECURITY_UPDATES aggiornamenti di sicurezza pendenti"
else
    ok "Sistema aggiornato"
fi

# 6. Utenti con UID 0 non root
EXTRA_ROOT=$(awk -F: '$3 == 0 && $1 != "root" {print $1}' /etc/passwd)
if [[ -n "$EXTRA_ROOT" ]]; then
    problem "Utenti con UID 0 oltre a root: $EXTRA_ROOT"
else
    ok "Nessun utente UID 0 oltre root"
fi

# 7. File world-writable
WORLD_WRITABLE=$(find /etc /usr /bin /sbin -perm -o+w -not -type l 2>/dev/null | head -10)
if [[ -n "$WORLD_WRITABLE" ]]; then
    problem "File world-writable trovati: $WORLD_WRITABLE"
else
    ok "Nessun file world-writable critico"
fi

# 8. Auditd
if ! systemctl is-active auditd &>/dev/null; then
    problem "auditd non attivo!"
else
    ok "auditd attivo"
fi

# Summary
log ""
log "=== RIEPILOGO: $PROBLEMS problemi trovati ==="

if [[ $PROBLEMS -gt 0 ]]; then
    mail -s "[$HOSTNAME] Security Audit: $PROBLEMS PROBLEMI" \
        "$ALERT_EMAIL" < "$REPORT"
fi

exit $((PROBLEMS > 0 ? 1 : 0))
```

```bash
# Pianifica audit quotidiano
cat > /etc/cron.d/security-audit << 'EOF'
30 6 * * * root /usr/local/bin/security-audit.sh
EOF
chmod +x /usr/local/bin/security-audit.sh
```

---

# Parte D — Reporting e Dashboard

---

## D1. OpenSCAP + Grafana

```python
#!/usr/bin/env python3
# parse_oscap_results.py — parsing risultati OpenSCAP per Prometheus
"""Espone metriche OpenSCAP come endpoint Prometheus"""

import xml.etree.ElementTree as ET
from prometheus_client import start_http_server, Gauge, Counter
import time
import glob
import os

# Metriche
COMPLIANCE_SCORE = Gauge(
    'oscap_compliance_score',
    'Score di conformità OpenSCAP (0-100)',
    ['profile', 'hostname']
)

RULE_RESULT = Gauge(
    'oscap_rule_result',
    'Risultato singola regola (1=pass, 0=fail)',
    ['rule_id', 'severity', 'hostname']
)

CHECKS_TOTAL = Gauge(
    'oscap_checks_total',
    'Numero totale di check',
    ['result', 'hostname']
)


def parse_results(xml_file: str, hostname: str) -> None:
    tree = ET.parse(xml_file)
    root = tree.getroot()
    ns = {
        'xccdf': 'http://checklists.nist.gov/xccdf/1.2',
        'oval': 'http://oval.mitre.org/XMLSchema/oval-results-5'
    }

    results = {'pass': 0, 'fail': 0, 'error': 0, 'notapplicable': 0}
    profile = 'unknown'

    for result in root.findall('.//xccdf:rule-result', ns):
        rule_id = result.get('idref', '').split('.')[-1]
        severity = result.get('severity', 'unknown')
        status = result.find('xccdf:result', ns)

        if status is not None:
            status_text = status.text.strip()
            results[status_text] = results.get(status_text, 0) + 1
            RULE_RESULT.labels(
                rule_id=rule_id,
                severity=severity,
                hostname=hostname
            ).set(1 if status_text == 'pass' else 0)

    total = results['pass'] + results['fail']
    if total > 0:
        score = (results['pass'] / total) * 100
        COMPLIANCE_SCORE.labels(profile=profile, hostname=hostname).set(score)

    for result_type, count in results.items():
        CHECKS_TOTAL.labels(result=result_type, hostname=hostname).set(count)


if __name__ == '__main__':
    import socket
    hostname = socket.gethostname()

    start_http_server(9200)
    print(f"Esportando metriche su :9200/metrics per {hostname}")

    while True:
        # Cerca ultimo file risultati
        files = sorted(glob.glob('/var/log/oscap-results-*.xml'))
        if files:
            parse_results(files[-1], hostname)
        time.sleep(300)  # aggiorna ogni 5 minuti
```

---

# Parte E — Riepilogo Completo

## Workflow compliance operativo

```
1. ASSESS (valuta stato)
   └── oscap xccdf eval → report HTML + XML risultati

2. REMEDIATE (rimedia)
   ├── oscap generate fix --fix-type ansible → playbook
   └── ansible-playbook remediation.yml --check → applica

3. VERIFY (verifica)
   └── oscap xccdf eval → confronta con baseline

4. REPORT (riporta)
   └── Metriche Prometheus → Dashboard Grafana

5. CONTINUOUS (continuo)
   └── Cron giornaliero + CI/CD gate + alert
```

## Standard e livelli

| Standard | Livello | Uso tipico |
|---|---|---|
| CIS Level 1 | Base | Server generico, tutti |
| CIS Level 2 | Avanzato | Server ad alta sicurezza |
| DISA STIG | Militare | US Government, DoD |
| PCI-DSS | Pagamenti | Aziende che gestiscono carte |
| NIST SP 800-53 | Federale US | Agenzie governative US |
| ISO 27001 | Internazionale | Certificazione sicurezza |

## Comandi OpenSCAP essenziali

```bash
# Info su profili disponibili
oscap info ssg-ubuntu2204-ds.xml

# Scansione completa
oscap xccdf eval --profile PROFILO \
    --results results.xml \
    --report report.html \
    ssg-ubuntu2204-ds.xml

# Genera remediation Ansible
oscap xccdf generate fix \
    --fix-type ansible \
    ssg-ubuntu2204-ds.xml > remediation.yml

# Valida solo check falliti
oscap xccdf generate fix \
    --fix-type ansible \
    results.xml > failed-only.yml

# Verifica singola regola
oscap xccdf eval \
    --rule RULE_ID \
    ssg-ubuntu2204-ds.xml
```

---

## Conclusione del campo 02-LINUX-POWERUSER

Con questo tutorial si completano tutti i 35 tutorial del campo **02-LINUX-POWERUSER**:

| Range | Argomenti |
|---|---|
| 01-02 | Filesystem, Shell mastery |
| 03-07 | Pacchetti, systemd, networking, storage, kernel |
| 08-13 | Performance, processi, SSH, sicurezza, utenti, logging |
| 14-19 | Container, virtualizzazione, backup, web server, database, servizi di rete |
| 20-24 | Monitoring, automazione, troubleshooting, bash avanzato, firewall |
| 25-27 | ZFS, Docker avanzato, SELinux/AppArmor |
| 28-35 | nginx avanzato, PostgreSQL HA, Prometheus/Grafana, Ansible, VPN, HA Cluster, hardening, compliance |

## Prossimi campi consigliati

- **03-CLOUD-AWS** o **04-CLOUD-GCP** — cloud engineering
- **05-KUBERNETES** — orchestrazione container
- **06-DEVOPS-CICD** — pipeline e automazione
