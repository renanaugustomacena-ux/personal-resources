# Compliance Scanning e Automazione per Linux

> **Modulo 35** · **Aggiornamento:** 2026-05-22

---

## Indice

1. [Panoramica dei framework di compliance](#1-panoramica-dei-framework-di-compliance)
2. [OpenSCAP](#2-openscap)
3. [CIS-CAT](#3-cis-cat)
4. [Lynis](#4-lynis)
5. [Chef InSpec](#5-chef-inspec)
6. [Ansible per la compliance](#6-ansible-per-la-compliance)
7. [Puppet e Chef per l'hardening](#7-puppet-e-chef-per-lhardening)
8. [Compliance nel cloud](#8-compliance-nel-cloud)
9. [Compliance per container e Kubernetes](#9-compliance-per-container-e-kubernetes)
10. [Remediation automatizzata](#10-remediation-automatizzata)
11. [Reporting e raccolta evidenze](#11-reporting-e-raccolta-evidenze)
12. [Drift detection](#12-drift-detection)
13. [Integrazione con vulnerability management](#13-integrazione-con-vulnerability-management)
14. [Compliance gate nelle pipeline CI/CD](#14-compliance-gate-nelle-pipeline-cicd)
15. [Troubleshooting](#15-troubleshooting)
16. [FAQ](#16-faq)
17. [Guida all'implementazione da zero](#17-guida-allimplementazione-da-zero)
18. [Checklist template](#18-checklist-template)
19. [Glossario](#19-glossario)
20. [Letture e riferimenti](#20-letture-e-riferimenti)
21. [Esercizi](#21-esercizi)

---

## 1. Panoramica dei framework di compliance

La compliance non e' un prodotto: e' un processo continuo che verifica che i sistemi Linux siano configurati secondo standard riconosciuti. Ogni framework impone requisiti specifici che si traducono in controlli tecnici misurabili.

### 1.1 CIS Benchmarks

I CIS (Center for Internet Security) Benchmarks sono guide di hardening sviluppate da una comunita' di esperti. Coprono ogni distribuzione Linux rilevante (RHEL, Ubuntu, Debian, SUSE, Amazon Linux, Oracle Linux).

**Struttura tipica di un CIS Benchmark:**

| Sezione | Contenuto | Esempio Linux |
|---------|-----------|---------------|
| Initial Setup | Filesystem, bootloader, ASLR | Disabilitare mounting di `cramfs`, `freevxfs`, `udf` |
| Services | Servizi non necessari | Disabilitare `avahi-daemon`, `cups` se non servono |
| Network | Stack TCP/IP, firewall | `net.ipv4.conf.all.send_redirects = 0` |
| Logging & Auditing | rsyslog, auditd | Garantire log immutabili con `auditd` |
| Access & Auth | PAM, sudo, SSH | `PermitRootLogin no`, password complexity via `pam_pwquality` |
| System Maintenance | Permessi file, integrità | Verificare permessi su `/etc/passwd`, `/etc/shadow` |

**Livelli CIS:**

- **Level 1**: hardening di base, impatto operativo minimo. Adatto a tutti i server.
- **Level 2**: hardening approfondito, puo' interferire con alcune applicazioni. Consigliato per ambienti ad alto rischio.

**Cosa richiede concretamente su Linux:**

```bash
# Esempio: CIS RHEL 9 Benchmark 1.1.1.1 — Disabilitare cramfs
echo "install cramfs /bin/true" > /etc/modprobe.d/cramfs.conf
echo "blacklist cramfs" >> /etc/modprobe.d/cramfs.conf

# Esempio: CIS 5.2.5 — MaxAuthTries in sshd
grep -q "^MaxAuthTries" /etc/ssh/sshd_config && \
  sed -i 's/^MaxAuthTries.*/MaxAuthTries 4/' /etc/ssh/sshd_config || \
  echo "MaxAuthTries 4" >> /etc/ssh/sshd_config
```

### 1.2 DISA STIG

I Security Technical Implementation Guides (STIG) sono pubblicati dalla Defense Information Systems Agency (DISA) del Dipartimento della Difesa USA. Sono obbligatori per i sistemi governativi USA e largamente adottati come standard de facto nel settore difesa/aerospazio globale.

**Differenze chiave rispetto a CIS:**

| Aspetto | CIS Benchmark | DISA STIG |
|---------|---------------|-----------|
| Origine | Community-driven | Governo USA (DoD) |
| Severità | Level 1 / Level 2 | CAT I (High) / CAT II (Medium) / CAT III (Low) |
| Formato | PDF + XCCDF | XCCDF + OVAL (SCAP nativo) |
| Aggiornamento | Trimestrale | Trimestrale |
| Obbligo legale | Volontario | Obbligatorio per DoD |

**Categorie di severità STIG:**

- **CAT I (High)**: vulnerabilita' che permettono accesso non autorizzato immediato o denial of service. Remediation richiesta entro 30 giorni.
- **CAT II (Medium)**: vulnerabilita' che possono contribuire a un compromesso. Remediation entro 90 giorni.
- **CAT III (Low)**: debolezze che riducono la defense-in-depth. Remediation nel prossimo ciclo di manutenzione.

**Esempio di un finding STIG:**

```
Rule ID:    SV-230222r858697_rule
STIG ID:    RHEL-09-010010
Severity:   CAT II
Title:      RHEL 9 must display the Standard Mandatory DoD Notice
            and Consent Banner before granting local or remote access.
Fix:        Configurare /etc/issue con il banner DoD approvato.
Check:      grep -i "you are accessing" /etc/issue
```

### 1.3 PCI-DSS

Il Payment Card Industry Data Security Standard si applica a qualsiasi organizzazione che processa, trasmette o archivia dati di carte di pagamento. La versione 4.0.1 (in vigore dal 2025) ha introdotto requisiti piu' prescrittivi per la gestione dei sistemi.

**Requisiti PCI-DSS con impatto diretto su Linux:**

| Requisito | Descrizione | Controllo Linux |
|-----------|-------------|-----------------|
| 1.x | Firewall e segmentazione rete | `iptables`/`nftables`, zone di rete |
| 2.2 | Eliminare default non necessari | Rimuovere pacchetti, disabilitare servizi |
| 2.2.7 | Cifrare traffico non-console | TLS su tutto il traffico amministrativo |
| 5.x | Protezione anti-malware | ClamAV o equivalente, aggiornamenti firme |
| 6.3.3 | Patch management | Aggiornamenti di sicurezza entro 30 giorni (critici: 15 giorni) |
| 8.x | Identificazione e autenticazione | Password policy, MFA per accesso remoto, no shared accounts |
| 10.x | Logging e monitoraggio | auditd, rsyslog, log retention 12 mesi, timestamp sincronizzati via NTP |
| 11.5 | File integrity monitoring | AIDE, OSSEC, Wazuh |

```bash
# PCI-DSS 10.2.2 — Logging di tutte le azioni dell'utente root
# Regola auditd per tracciare tutti i comandi eseguiti da root
cat >> /etc/audit/rules.d/pci-dss.rules << 'EOF'
-a always,exit -F arch=b64 -F euid=0 -S execve -k pci_root_commands
-a always,exit -F arch=b32 -F euid=0 -S execve -k pci_root_commands
EOF

# PCI-DSS 8.3.6 — Password complexity
cat > /etc/security/pwquality.conf << 'EOF'
minlen = 12
dcredit = -1
ucredit = -1
lcredit = -1
ocredit = -1
maxrepeat = 3
EOF
```

### 1.4 HIPAA

L'Health Insurance Portability and Accountability Act si applica alle organizzazioni sanitarie USA (e ai loro fornitori IT). Non prescrive controlli tecnici specifici ma richiede "safeguards" ragionevoli per proteggere PHI (Protected Health Information).

**Technical safeguards HIPAA tradotti in controlli Linux:**

| Safeguard | Implementazione Linux |
|-----------|----------------------|
| Access control (§164.312(a)) | PAM, sudo, RBAC, SELinux |
| Audit controls (§164.312(b)) | auditd con regole per accesso a file PHI |
| Integrity (§164.312(c)) | AIDE per file integrity monitoring |
| Transmission security (§164.312(e)) | TLS 1.2+, cifratura disco (LUKS) |
| Authentication (§164.312(d)) | MFA, certificate-based auth per SSH |

```bash
# HIPAA — Cifratura disco per dati PHI at rest
cryptsetup luksFormat /dev/sdb1
cryptsetup open /dev/sdb1 phi_data
mkfs.xfs /dev/mapper/phi_data
mount /dev/mapper/phi_data /mnt/phi

# HIPAA — Audit trail per accesso a directory PHI
auditctl -w /mnt/phi -p rwxa -k hipaa_phi_access
```

### 1.5 SOC 2

SOC 2 (Service Organization Control Type 2) si basa sui Trust Services Criteria dell'AICPA. Non e' una checklist tecnica ma un framework basato su cinque principi: Security, Availability, Processing Integrity, Confidentiality, Privacy.

**Controlli SOC 2 mappati su Linux:**

| Trust Service Criteria | Controllo Linux |
|------------------------|-----------------|
| CC6.1 — Logical access | Gestione utenti, sudo policy, SSH key management |
| CC6.6 — System boundaries | Firewall, segmentazione, network ACL |
| CC7.1 — Monitoring | Centralizzazione log, alerting, SIEM integration |
| CC7.2 — Incident detection | HIDS (OSSEC/Wazuh), auditd, osquery |
| CC8.1 — Change management | Git-based config, Ansible, change approval workflow |

### 1.6 ISO 27001 / ISO 27002

ISO 27001 definisce un ISMS (Information Security Management System). L'Annex A (aggiornato nel 2022) elenca 93 controlli organizzati in 4 temi. ISO 27002 fornisce le linee guida di implementazione.

**Controlli ISO 27001 Annex A rilevanti per Linux:**

| Controllo | Titolo | Implementazione |
|-----------|--------|-----------------|
| A.8.5 | Secure authentication | PAM stack, SSH hardening |
| A.8.6 | Capacity management | Monitoring risorse, alert soglie |
| A.8.7 | Protection against malware | ClamAV, immutable infrastructure |
| A.8.8 | Management of technical vulnerabilities | Vulnerability scanning periodico |
| A.8.9 | Configuration management | Ansible/Puppet, golden images |
| A.8.15 | Logging | Centralizzazione, retention, integrità |
| A.8.16 | Monitoring activities | SIEM, alerting in tempo reale |

### 1.7 NIS2

La Direttiva NIS2 (Network and Information Security Directive 2) dell'UE, in vigore dal 17 ottobre 2024, amplia significativamente gli obblighi di cybersecurity per le organizzazioni europee. Si applica a "entita' essenziali" e "entita' importanti" in 18 settori.

**Requisiti NIS2 con impatto tecnico su Linux:**

| Articolo NIS2 | Requisito | Implementazione Linux |
|---------------|-----------|----------------------|
| Art. 21(2)(a) | Risk analysis, information system security policies | Compliance scanning continuo, CIS/STIG baseline |
| Art. 21(2)(b) | Incident handling | auditd, SIEM, playbook di risposta automatizzati |
| Art. 21(2)(d) | Supply chain security | SBOM, verifica integrita' pacchetti, pinning versioni |
| Art. 21(2)(e) | Security in acquisition, development, maintenance | Compliance gates in CI/CD |
| Art. 21(2)(g) | Basic cyber hygiene practices and training | Hardening automatizzato, patching sistematico |
| Art. 21(2)(h) | Cryptography and encryption | TLS 1.3, LUKS, algoritmi approvati |
| Art. 21(2)(j) | Multi-factor authentication | PAM MFA, FIDO2 per SSH |

**Sanzioni NIS2:**

- Entita' essenziali: fino a 10 milioni EUR o 2% del fatturato globale
- Entita' importanti: fino a 7 milioni EUR o 1.4% del fatturato globale

### 1.8 Matrice comparativa

| Framework | Obbligatorio per | Cadenza audit | Formato SCAP | Auto-remediation |
|-----------|------------------|---------------|--------------|------------------|
| CIS Benchmarks | Volontario | Continuo | Si (XCCDF/OVAL) | Si (script) |
| DISA STIG | DoD USA | Trimestrale | Si (SCAP nativo) | Si (fix scripts) |
| PCI-DSS | Chi processa carte | Annuale + trimestrale | Parziale | Manuale |
| HIPAA | Sanita' USA | Annuale | No | Manuale |
| SOC 2 | SaaS/servizi | Annuale (Type 2) | No | Manuale |
| ISO 27001 | Volontario (UE diffuso) | Triennale + annuale | No | Manuale |
| NIS2 | UE settori critici | Continuo | No | Consigliata |

### 1.9 NIST SP 800-53

Il NIST Special Publication 800-53 (Revisione 5, aggiornato a Release 5.2.0 nell'agosto 2025) definisce un catalogo di oltre 1.000 controlli di sicurezza e privacy organizzati in 20 famiglie. E' il riferimento per i sistemi informativi federali USA (FISMA) e viene adottato globalmente come framework tecnico di riferimento per la sicurezza.

**Famiglie di controlli NIST 800-53 piu' rilevanti per Linux:**

| Famiglia | ID | Descrizione | Implementazione Linux |
|----------|----|-------------|----------------------|
| Access Control | AC | Gestione accessi, separazione privilegi | PAM, sudo, SELinux, SSH key management |
| Audit and Accountability | AU | Generazione, revisione, protezione log | auditd, rsyslog, log forwarding, retention policy |
| Configuration Management | CM | Baseline, change control, inventario | Ansible/Puppet, golden images, AIDE, Git-based config |
| Identification and Authentication | IA | Autenticazione utenti, device, servizi | PAM stack, MFA, SSSD, certificati SSH |
| System and Communications Protection | SC | Cifratura, segmentazione, boundary protection | TLS 1.3, LUKS, nftables, SELinux network labeling |
| System and Information Integrity | SI | Patching, malware protection, FIM | dnf-automatic, ClamAV, AIDE, vulnerability scanning |
| Risk Assessment | RA | Vulnerability scanning, threat assessment | OpenSCAP OVAL, Trivy, Lynis |
| System and Services Acquisition | SA | Supply chain, SBOM, secure development | SBOM generation (syft/cyclonedx), package signature verification |

**Relazione con profili SCAP:**

Il profilo OSPP (Protection Profile for General Purpose Operating Systems) disponibile in SCAP Security Guide e' derivato direttamente dai controlli NIST 800-53. Rappresenta il sottoinsieme di controlli tecnici applicabili a un singolo sistema operativo.

```bash
# Scansione con profilo OSPP (NIST 800-53 derived)
sudo oscap xccdf eval \
  --profile xccdf_org.ssgproject.content_profile_ospp \
  --results /var/log/oscap/ospp-results.xml \
  --report /var/log/oscap/ospp-report.html \
  /usr/share/xml/scap/ssg/content/ssg-rhel9-ds.xml
```

**Crosswalk NIST 800-53 con altri framework:**

NIST pubblica mappature ufficiali tramite il catalogo OLIR (Online Informative References). La mappatura CSF 2.0 a SP 800-53 Rev 5 (finalizzata a novembre 2025) permette di soddisfare piu' framework con un singolo set di controlli implementati:

| Controllo 800-53 | CIS Benchmark | STIG | PCI-DSS 4.0 |
|-------------------|---------------|------|-------------|
| AC-2 (Account Management) | 5.4.x | SV-230378r | 8.1.x |
| AU-2 (Audit Events) | 4.1.x | SV-230386r | 10.2.x |
| CM-6 (Configuration Settings) | 1.x-6.x | Multiple | 2.2.x |
| IA-5 (Authenticator Management) | 5.3.x | SV-230370r | 8.3.x |
| SC-8 (Transmission Confidentiality) | 5.2.x (SSH) | SV-230244r | 2.2.7 |
| SI-2 (Flaw Remediation) | — | SV-230221r | 6.3.3 |

Quando un'organizzazione deve conformarsi contemporaneamente a NIST 800-53, CIS, e PCI-DSS, queste mappature consentono di implementare un singolo controllo tecnico che soddisfa requisiti in tutti e tre i framework, riducendo il lavoro duplicato.

---

## 2. OpenSCAP

OpenSCAP e' l'implementazione open source dello standard SCAP (Security Content Automation Protocol) del NIST. E' lo strumento di riferimento per la compliance automatizzata su RHEL, CentOS, Fedora, e supporta anche Ubuntu e SUSE.

### 2.1 Installazione

```bash
# RHEL / CentOS / Rocky / AlmaLinux / Fedora
sudo dnf install openscap-scanner scap-security-guide

# Ubuntu / Debian
sudo apt install libopenscap8 ssg-debian ssg-ubuntu

# SUSE
sudo zypper install openscap openscap-utils scap-security-guide

# Verifica installazione
oscap --version
```

**Contenuto SCAP installato:**

```bash
# Elenco datastream disponibili
ls /usr/share/xml/scap/ssg/content/

# Output tipico su RHEL 9:
# ssg-rhel9-ds.xml          — Datastream completo
# ssg-rhel9-xccdf.xml       — XCCDF benchmark
# ssg-rhel9-oval.xml        — OVAL definitions
# ssg-rhel9-cpe-dictionary.xml
```

### 2.2 Concetti fondamentali SCAP

| Componente | Descrizione |
|------------|-------------|
| XCCDF | Extensible Configuration Checklist Description Format — struttura del benchmark |
| OVAL | Open Vulnerability and Assessment Language — definizioni dei test |
| CPE | Common Platform Enumeration — identificazione piattaforma |
| Datastream (DS) | Singolo file XML che aggrega XCCDF + OVAL + CPE |
| Profile | Selezione di regole attive per uno specifico standard |
| Rule | Singolo controllo di compliance |
| Fix | Script di remediation associato a una rule |

### 2.3 Profili disponibili

```bash
# Elenco profili in un datastream
oscap info /usr/share/xml/scap/ssg/content/ssg-rhel9-ds.xml

# Output parziale:
# Profiles:
#   xccdf_org.ssgproject.content_profile_cis
#   xccdf_org.ssgproject.content_profile_cis_server_l1
#   xccdf_org.ssgproject.content_profile_cis_workstation_l1
#   xccdf_org.ssgproject.content_profile_cis_workstation_l2
#   xccdf_org.ssgproject.content_profile_stig
#   xccdf_org.ssgproject.content_profile_stig_gui
#   xccdf_org.ssgproject.content_profile_pci-dss
#   xccdf_org.ssgproject.content_profile_hipaa
#   xccdf_org.ssgproject.content_profile_ospp
#   xccdf_org.ssgproject.content_profile_e8
```

### 2.4 Scansione con oscap CLI

**Scansione base con report HTML:**

```bash
# Scansione CIS Level 1 Server su RHEL 9
sudo oscap xccdf eval \
  --profile xccdf_org.ssgproject.content_profile_cis_server_l1 \
  --results /var/log/oscap/cis-l1-results-$(date +%Y%m%d).xml \
  --report /var/log/oscap/cis-l1-report-$(date +%Y%m%d).html \
  /usr/share/xml/scap/ssg/content/ssg-rhel9-ds.xml

# Scansione STIG
sudo oscap xccdf eval \
  --profile xccdf_org.ssgproject.content_profile_stig \
  --results /var/log/oscap/stig-results.xml \
  --report /var/log/oscap/stig-report.html \
  /usr/share/xml/scap/ssg/content/ssg-rhel9-ds.xml

# Scansione PCI-DSS
sudo oscap xccdf eval \
  --profile xccdf_org.ssgproject.content_profile_pci-dss \
  --results /var/log/oscap/pci-results.xml \
  --report /var/log/oscap/pci-report.html \
  /usr/share/xml/scap/ssg/content/ssg-rhel9-ds.xml
```

**Scansione con filtro su specifiche rule:**

```bash
# Solo regole relative a SSH
oscap xccdf eval \
  --profile xccdf_org.ssgproject.content_profile_cis_server_l1 \
  --rule xccdf_org.ssgproject.content_rule_sshd_disable_root_login \
  --rule xccdf_org.ssgproject.content_rule_sshd_set_max_auth_tries \
  --results /tmp/ssh-check.xml \
  /usr/share/xml/scap/ssg/content/ssg-rhel9-ds.xml
```

**Scansione remota via SSH:**

```bash
# Scansione di un host remoto
oscap-ssh root@target-server.example.com 22 \
  xccdf eval \
  --profile xccdf_org.ssgproject.content_profile_stig \
  --results /var/log/oscap/remote-stig.xml \
  --report /var/log/oscap/remote-stig.html \
  /usr/share/xml/scap/ssg/content/ssg-rhel9-ds.xml
```

### 2.5 Interpretazione dei risultati

Ogni rule puo' avere uno dei seguenti esiti:

| Risultato | Significato |
|-----------|-------------|
| `pass` | Il sistema soddisfa il controllo |
| `fail` | Il sistema NON soddisfa il controllo |
| `error` | Errore durante la valutazione (check OVAL non valido) |
| `unknown` | Impossibile determinare lo stato |
| `notapplicable` | La rule non si applica a questa piattaforma |
| `notchecked` | La rule richiede verifica manuale |
| `notselected` | La rule non e' inclusa nel profilo |
| `informational` | Solo informativo, non contribuisce allo score |

**Calcolo dello score:**

```
Score = (numero pass / (numero pass + numero fail)) * 100
```

Le rule con esito `notapplicable`, `notchecked`, `notselected` non incidono sullo score.

### 2.6 Generazione di script di remediation

```bash
# Generare un Bash script di remediation
oscap xccdf generate fix \
  --fix-type bash \
  --profile xccdf_org.ssgproject.content_profile_cis_server_l1 \
  --output /tmp/remediate-cis-l1.sh \
  /usr/share/xml/scap/ssg/content/ssg-rhel9-ds.xml

# Generare un playbook Ansible di remediation
oscap xccdf generate fix \
  --fix-type ansible \
  --profile xccdf_org.ssgproject.content_profile_stig \
  --output /tmp/remediate-stig.yml \
  /usr/share/xml/scap/ssg/content/ssg-rhel9-ds.xml

# Generare remediation SOLO per le rule fallite (da un risultato precedente)
oscap xccdf generate fix \
  --fix-type bash \
  --result-id xccdf_org.open-scap_testresult_default-profile \
  --output /tmp/remediate-failed.sh \
  /var/log/oscap/cis-l1-results.xml
```

**ATTENZIONE**: non eseguire mai script di remediation senza revisione. Esempio di effetto collaterale: la regola `sshd_disable_root_login` imposta `PermitRootLogin no` e puo' bloccare l'accesso se non esiste un utente sudo configurato.

### 2.7 Tailoring

Il tailoring permette di personalizzare un profilo SCAP senza modificare il datastream originale.

```bash
# Creare un profilo tailored con oscap
# 1. Partire dal profilo CIS L1 e disabilitare alcune regole
oscap xccdf generate guide \
  --profile xccdf_org.ssgproject.content_profile_cis_server_l1 \
  /usr/share/xml/scap/ssg/content/ssg-rhel9-ds.xml > /tmp/cis-guide.html
```

**Tailoring file XML:**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<xccdf-1.2:Tailoring xmlns:xccdf-1.2="http://checklists.nist.gov/xccdf/1.2"
  id="xccdf_custom_tailoring_azienda">
  <xccdf-1.2:version time="2026-05-22T00:00:00">1</xccdf-1.2:version>
  <xccdf-1.2:Profile id="xccdf_custom_profile_cis_l1_tailored"
    extends="xccdf_org.ssgproject.content_profile_cis_server_l1">
    <xccdf-1.2:title>CIS L1 Tailored per ambiente produzione</xccdf-1.2:title>
    <!-- Disabilitare rule che confligge con il nostro LDAP -->
    <xccdf-1.2:select idref="xccdf_org.ssgproject.content_rule_accounts_password_pam_unix_remember"
      selected="false"/>
    <!-- Rafforzare MaxAuthTries da 4 a 3 -->
    <xccdf-1.2:refine-value idref="xccdf_org.ssgproject.content_value_sshd_max_auth_tries_value"
      selector="3"/>
  </xccdf-1.2:Profile>
</xccdf-1.2:Tailoring>
```

```bash
# Usare il tailoring file nella scansione
sudo oscap xccdf eval \
  --profile xccdf_custom_profile_cis_l1_tailored \
  --tailoring-file /etc/oscap/tailoring.xml \
  --results /var/log/oscap/tailored-results.xml \
  --report /var/log/oscap/tailored-report.html \
  /usr/share/xml/scap/ssg/content/ssg-rhel9-ds.xml
```

### 2.8 Scansione automatizzata con cron

```bash
#!/bin/bash
# /etc/cron.weekly/oscap-compliance-scan
# Scansione settimanale CIS L1 con invio report

PROFILE="xccdf_org.ssgproject.content_profile_cis_server_l1"
DS="/usr/share/xml/scap/ssg/content/ssg-rhel9-ds.xml"
DATE=$(date +%Y%m%d)
RESULTS_DIR="/var/log/oscap"
HOSTNAME=$(hostname -f)

mkdir -p "$RESULTS_DIR"

oscap xccdf eval \
  --profile "$PROFILE" \
  --results "${RESULTS_DIR}/cis-results-${DATE}.xml" \
  --report "${RESULTS_DIR}/cis-report-${DATE}.html" \
  "$DS" 2>&1 | tee "${RESULTS_DIR}/oscap-scan-${DATE}.log"

# Estrarre score dal risultato
SCORE=$(oscap xccdf eval \
  --profile "$PROFILE" "$DS" 2>&1 | grep "Score" | awk '{print $NF}')

# Alert se score sotto soglia
if (( $(echo "$SCORE < 80" | bc -l) )); then
  echo "ALERT: Compliance score ${SCORE}% su ${HOSTNAME}" | \
    mail -s "[COMPLIANCE] Score sotto soglia - ${HOSTNAME}" security@example.com \
    -A "${RESULTS_DIR}/cis-report-${DATE}.html"
fi

# Pulizia report oltre 90 giorni
find "$RESULTS_DIR" -name "*.xml" -mtime +90 -delete
find "$RESULTS_DIR" -name "*.html" -mtime +90 -delete
```

### 2.9 SCAP Workbench (GUI)

```bash
# Installazione
sudo dnf install scap-workbench    # RHEL/Fedora
sudo apt install scap-workbench    # Ubuntu/Debian

# Avvio
scap-workbench &
```

SCAP Workbench permette di:
- Caricare datastream e selezionare profili visualmente
- Creare tailoring file con interfaccia grafica
- Eseguire scansioni locali o remote
- Visualizzare risultati in formato tabellare
- Esportare report HTML/PDF

### 2.10 Tailoring avanzato con autotailor

Il comando `autotailor` (parte del pacchetto `openscap-utils`) consente di generare tailoring file XCCDF direttamente da riga di comando, eliminando la necessita' di scrivere XML manualmente o di usare una GUI.

```bash
# Installazione
sudo dnf install openscap-utils    # RHEL 9 / Fedora
sudo apt install libopenscap8      # Ubuntu/Debian (incluso in openscap-utils)

# Verificare disponibilita'
autotailor --help
```

**Sintassi base:**

```bash
autotailor \
  --new-profile-id xccdf_custom_profile_cis_l1_prod \
  --title "CIS L1 Produzione - Adattato" \
  --select xccdf_org.ssgproject.content_rule_sshd_disable_root_login \
  --unselect xccdf_org.ssgproject.content_rule_accounts_password_pam_unix_remember \
  --unselect xccdf_org.ssgproject.content_rule_disable_ctrlaltdel_reboot \
  /usr/share/xml/scap/ssg/content/ssg-rhel9-ds.xml \
  xccdf_org.ssgproject.content_profile_cis_server_l1 \
  > /etc/oscap/tailoring-prod.xml
```

L'output e' un tailoring file XML valido che estende il profilo originale. Parametri principali:

| Parametro | Funzione |
|-----------|----------|
| `--new-profile-id` | ID univoco del profilo personalizzato |
| `--title` | Titolo descrittivo leggibile |
| `--select RULE_ID` | Abilitare una rule non inclusa nel profilo base |
| `--unselect RULE_ID` | Disabilitare una rule dal profilo base |
| `--var-value VALUE_ID=SELECTOR` | Modificare il valore di una variabile XCCDF |

**Esempio pratico: profilo STIG senza controlli USB per server virtualizzati:**

```bash
autotailor \
  --new-profile-id xccdf_custom_profile_stig_vm \
  --title "STIG RHEL9 per VM - senza controlli USB/fisici" \
  --unselect xccdf_org.ssgproject.content_rule_service_usbguard_enabled \
  --unselect xccdf_org.ssgproject.content_rule_usbguard_allow_hid \
  --unselect xccdf_org.ssgproject.content_rule_bios_enable_execution_restrictions \
  --var-value xccdf_org.ssgproject.content_value_sshd_idle_timeout_value=600 \
  /usr/share/xml/scap/ssg/content/ssg-rhel9-ds.xml \
  xccdf_org.ssgproject.content_profile_stig \
  > /etc/oscap/tailoring-stig-vm.xml

# Usare il tailoring generato nella scansione
sudo oscap xccdf eval \
  --profile xccdf_custom_profile_stig_vm \
  --tailoring-file /etc/oscap/tailoring-stig-vm.xml \
  --results /var/log/oscap/stig-vm-results.xml \
  --report /var/log/oscap/stig-vm-report.html \
  /usr/share/xml/scap/ssg/content/ssg-rhel9-ds.xml
```

**Vantaggi di autotailor rispetto all'editing manuale XML:**

- Elimina errori di sintassi XML (namespace, chiusura tag, encoding)
- Integrabile in pipeline CI/CD e script di provisioning
- Versionabile in Git: il comando stesso documenta le personalizzazioni
- Ripetibile: rigenerare il tailoring quando il datastream SSG viene aggiornato
- Auditabile: il diff Git del comando mostra esattamente cosa e' cambiato

**Workflow consigliato per gestire tailoring in Git:**

```bash
# Struttura repository compliance
compliance-config/
├── Makefile
├── profiles/
│   ├── cis-l1-prod.sh       # Script autotailor per produzione
│   ├── cis-l1-staging.sh    # Script autotailor per staging
│   └── stig-vm.sh           # Script autotailor per VM
└── generated/
    ├── tailoring-cis-l1-prod.xml
    ├── tailoring-cis-l1-staging.xml
    └── tailoring-stig-vm.xml

# Makefile per rigenerare i tailoring
# make all rigenera tutti i file XML dai rispettivi script
```

**Combinare autotailor con oscap generate fix:**

```bash
# 1. Generare tailoring
autotailor \
  --new-profile-id xccdf_custom_profile_cis_l1_hardened \
  --title "CIS L1 Hardened" \
  --select xccdf_org.ssgproject.content_rule_sshd_use_strong_macs \
  --var-value xccdf_org.ssgproject.content_value_sshd_max_auth_tries_value=3 \
  /usr/share/xml/scap/ssg/content/ssg-rhel9-ds.xml \
  xccdf_org.ssgproject.content_profile_cis_server_l1 \
  > /tmp/tailoring-hardened.xml

# 2. Generare playbook Ansible dal profilo tailored
oscap xccdf generate fix \
  --fix-type ansible \
  --profile xccdf_custom_profile_cis_l1_hardened \
  --tailoring-file /tmp/tailoring-hardened.xml \
  --output /tmp/remediate-hardened.yml \
  /usr/share/xml/scap/ssg/content/ssg-rhel9-ds.xml

# 3. Applicare la remediation
ansible-playbook -i inventory.ini /tmp/remediate-hardened.yml --check
ansible-playbook -i inventory.ini /tmp/remediate-hardened.yml
```

---

## 3. CIS-CAT

CIS-CAT (Configuration Assessment Tool) e' lo strumento ufficiale del Center for Internet Security per valutare la conformita' ai CIS Benchmarks.

### 3.1 Versioni

| Versione | Licenza | Funzionalita' |
|----------|---------|----------------|
| CIS-CAT Lite | Gratuita (CIS SecureSuite membership) | Benchmark limitati, HTML report |
| CIS-CAT Pro | CIS SecureSuite (a pagamento) | Tutti i benchmark, remediation, API, dashboard |

### 3.2 Installazione e configurazione

```bash
# CIS-CAT Pro Assessor v4 (richiede Java 11+)
# Scaricare da CIS WorkBench dopo autenticazione SecureSuite

# Prerequisiti
sudo dnf install java-17-openjdk-headless   # RHEL
sudo apt install openjdk-17-jre-headless     # Ubuntu

# Estrazione
unzip Assessor-CLI-v4.x.x.zip -d /opt/cis-cat
chmod +x /opt/cis-cat/Assessor-CLI.sh

# Verifica
/opt/cis-cat/Assessor-CLI.sh --version
```

### 3.3 Esecuzione assessment

```bash
# Assessment interattivo — seleziona benchmark e profilo
sudo /opt/cis-cat/Assessor-CLI.sh -i

# Assessment diretto con benchmark specifico
sudo /opt/cis-cat/Assessor-CLI.sh \
  -b /opt/cis-cat/benchmarks/CIS_Red_Hat_Enterprise_Linux_9_Benchmark_v1.0.0-xccdf.xml \
  -p "Level 1 - Server" \
  -r /var/log/cis-cat/ \
  -html

# Assessment con output JSON (per integrazione API)
sudo /opt/cis-cat/Assessor-CLI.sh \
  -b /opt/cis-cat/benchmarks/CIS_Ubuntu_Linux_22.04_LTS_Benchmark_v2.0.0-xccdf.xml \
  -p "Level 2 - Server" \
  -r /var/log/cis-cat/ \
  -json

# Assessment su host remoto
sudo /opt/cis-cat/Assessor-CLI.sh \
  -b /opt/cis-cat/benchmarks/CIS_Red_Hat_Enterprise_Linux_9_Benchmark_v1.0.0-xccdf.xml \
  -p "Level 1 - Server" \
  --sessions ssh://admin@192.168.1.100:22 \
  -r /var/log/cis-cat/
```

### 3.4 Report e scoring

Il report CIS-CAT fornisce:

- **Score complessivo**: percentuale di rule superate
- **Breakdown per sezione**: filesystem, network, logging, access control, ecc.
- **Dettaglio per rule**: pass/fail, descrizione, remediation suggerita
- **Trend**: confronto con scansioni precedenti (Pro)

```bash
# Esempio di output CLI
# ========================================
# CIS-CAT Pro Assessor Assessment Results
# ========================================
# Benchmark: CIS Red Hat Enterprise Linux 9 v1.0.0
# Profile:   Level 1 - Server
# Score:     82.4% (187 of 227 recommendations passed)
# Failures:  40
# ========================================
```

### 3.5 CIS-CAT Pro Dashboard

CIS-CAT Pro include un dashboard web che:
- Aggrega risultati da piu' host
- Mostra trend storici di compliance
- Genera report per auditor
- Invia alert su regressioni

```bash
# Import risultati nel dashboard
/opt/cis-cat/Assessor-CLI.sh \
  -b /opt/cis-cat/benchmarks/CIS_RHEL_9.xml \
  -p "Level 1 - Server" \
  -D https://dashboard.example.com/api \
  -nts   # No TLS verification (solo per test)
```

---

## 4. Lynis

Lynis e' uno strumento di auditing open source sviluppato da CISOfy. A differenza di OpenSCAP (che valuta conformita' a un profilo specifico), Lynis esegue una scansione olistica della sicurezza del sistema e produce un Hardening Index numerico.

### 4.1 Installazione

```bash
# Da repository di sistema
sudo apt install lynis          # Debian/Ubuntu
sudo dnf install lynis          # RHEL/Fedora (EPEL richiesto)

# Da repository CISOfy (versione aggiornata)
sudo wget -O - https://packages.cisofy.com/keys/cisofy-software-public.key | sudo apt-key add -
echo "deb https://packages.cisofy.com/community/lynis/deb/ stable main" | \
  sudo tee /etc/apt/sources.list.d/cisofy-lynis.list
sudo apt update && sudo apt install lynis

# Da Git (per sviluppo/testing)
git clone https://github.com/CISOfy/lynis.git /opt/lynis
cd /opt/lynis && sudo ./lynis audit system

# Verifica versione
lynis --version
```

### 4.2 Audit completo del sistema

```bash
# Audit interattivo
sudo lynis audit system

# Audit non interattivo (per automazione)
sudo lynis audit system --no-colors --quiet

# Audit rapido (skip test lenti)
sudo lynis audit system --quick

# Audit con profilo personalizzato
sudo lynis audit system --profile /etc/lynis/custom.prf

# Audit con pentest (aggressivo — richiede permessi)
sudo lynis audit system --pentest
```

### 4.3 Interpretazione dei risultati

**Hardening Index:**

| Range | Significato |
|-------|-------------|
| 0-49 | Critico — richiede intervento immediato |
| 50-69 | Debole — molte aree da migliorare |
| 70-79 | Buono — sopra la media |
| 80-89 | Forte — hardening solido |
| 90-100 | Eccellente — hardening completo |

**Categorie di risultato:**

```
[WARNING]  — Problema di sicurezza significativo, azione richiesta
[SUGGESTION] — Miglioramento consigliato
[OK]       — Test superato
[FOUND]    — Elemento rilevato (informativo)
[NOT FOUND] — Elemento non rilevato
[SKIPPED]  — Test saltato (non applicabile)
```

**Report files:**

```bash
# Log dettagliato
/var/log/lynis.log

# Report strutturato (parsabile)
/var/log/lynis-report.dat

# Estrarre suggerimenti dal report
grep "suggestion\[\]" /var/log/lynis-report.dat

# Estrarre warning
grep "warning\[\]" /var/log/lynis-report.dat

# Estrarre Hardening Index
grep "hardening_index" /var/log/lynis-report.dat
```

### 4.4 Profili personalizzati

```ini
# /etc/lynis/custom.prf
# Profilo personalizzato per server web in produzione

# Saltare test non rilevanti per container
skip-test=FILE-6310    # NFS check
skip-test=STRG-1840    # USB storage check
skip-test=NETW-2600    # Wireless check

# Aggiungere test specifici
test-group=malware
test-group=authentication
test-group=networking
test-group=storage
test-group=filesystems

# Soglia minima Hardening Index
min-hardening-index=75

# Configurazione plugin
plugin=authentication
plugin=file-integrity

# Report
report-file=/var/log/lynis/audit-report.dat
log-file=/var/log/lynis/audit.log
```

### 4.5 Test personalizzati

Lynis supporta test custom tramite plugin nella directory `/usr/share/lynis/plugins/` (o nel percorso del profilo).

```bash
#!/bin/sh
# /usr/share/lynis/plugins/custom_plugin_webserver.sh
# Plugin Lynis per controlli specifici web server

# Header obbligatorio
PLUGIN_NAME="webserver_custom"
PLUGIN_VERSION="1.0"
PLUGIN_AUTHOR="Security Team"

# Test: verificare che directory /var/www non sia world-writable
Register --test-no CUST-0001 --weight M --description "Check /var/www permissions"
if [ ${SKIPTEST} -eq 0 ]; then
    FIND=$(find /var/www -type d -perm -o+w 2>/dev/null)
    if [ -n "${FIND}" ]; then
        ReportWarning "${TEST_NO}" "World-writable directories found in /var/www"
        LogText "Result: found world-writable dirs: ${FIND}"
    else
        ReportResult "${TEST_NO}" "OK"
    fi
fi

# Test: verificare che il server web non giri come root
Register --test-no CUST-0002 --weight H --description "Check web server not running as root"
if [ ${SKIPTEST} -eq 0 ]; then
    WEBPROCS=$(ps aux | grep -E "(nginx|apache2|httpd)" | grep -v grep | awk '{print $1}' | sort -u)
    if echo "${WEBPROCS}" | grep -q "^root$"; then
        # Root puo' essere il master process, verificare i worker
        WORKERS=$(ps aux | grep -E "(nginx|apache2|httpd)" | grep -v grep | grep -v root)
        if [ -z "${WORKERS}" ]; then
            ReportWarning "${TEST_NO}" "Web server workers running as root"
        else
            ReportResult "${TEST_NO}" "OK"
            LogText "Result: master as root, workers as unprivileged user"
        fi
    else
        ReportResult "${TEST_NO}" "OK"
    fi
fi
```

### 4.6 Ciclo di vita dei plugin e fasi di esecuzione

Lynis organizza l'esecuzione dei test in due fasi distinte. Comprendere questa architettura e' fondamentale per scrivere plugin corretti e performanti.

**Fase 1 — Raccolta dati (detection/gathering):**

Durante la fase 1, Lynis raccoglie informazioni sul sistema operativo, sui servizi installati, sulle configurazioni attive e sull'ambiente di runtime. Non vengono eseguiti test di compliance veri e propri. I plugin di fase 1 popolano variabili globali che saranno poi disponibili ai test di fase 2.

```bash
#!/bin/sh
# /usr/share/lynis/plugins/plugin_webserver_phase1
# Plugin fase 1: raccolta dati web server

PLUGIN_NAME="webserver_data"
PLUGIN_VERSION="1.0"
PLUGIN_AUTHOR="Security Team"
PLUGIN_PHASE=1

# Rilevare quale web server e' installato
if command -v nginx >/dev/null 2>&1; then
    WEBSERVER_TYPE="nginx"
    WEBSERVER_VERSION=$(nginx -v 2>&1 | grep -oP '\d+\.\d+\.\d+')
    WEBSERVER_CONF="/etc/nginx/nginx.conf"
    WEBSERVER_RUNNING=$(systemctl is-active nginx 2>/dev/null)
elif command -v apache2ctl >/dev/null 2>&1 || command -v httpd >/dev/null 2>&1; then
    WEBSERVER_TYPE="apache"
    WEBSERVER_VERSION=$(apache2ctl -v 2>/dev/null | head -1 | grep -oP '\d+\.\d+\.\d+')
    WEBSERVER_CONF="/etc/httpd/conf/httpd.conf"
    WEBSERVER_RUNNING=$(systemctl is-active httpd 2>/dev/null || systemctl is-active apache2 2>/dev/null)
else
    WEBSERVER_TYPE="none"
fi

# Esportare le variabili per fase 2
LogText "Info: detected web server type: ${WEBSERVER_TYPE}"
LogText "Info: web server version: ${WEBSERVER_VERSION}"
Report "webserver_type=${WEBSERVER_TYPE}"
Report "webserver_version=${WEBSERVER_VERSION}"
Report "webserver_running=${WEBSERVER_RUNNING}"
```

**Fase 2 — Esecuzione test (testing/auditing):**

La fase 2 esegue i test veri e propri, valutando la conformita' in base ai dati raccolti in fase 1. I test di fase 2 possono accedere alle variabili popolate dai plugin di fase 1 e produrre risultati (pass, warning, suggestion).

```bash
#!/bin/sh
# /usr/share/lynis/plugins/plugin_webserver_phase2
# Plugin fase 2: test di compliance web server

PLUGIN_NAME="webserver_tests"
PLUGIN_VERSION="1.0"
PLUGIN_AUTHOR="Security Team"
PLUGIN_PHASE=2

# Eseguire test solo se un web server e' stato rilevato in fase 1
DETECTED_WS=$(grep "webserver_type" /tmp/lynis.$$  2>/dev/null | cut -d= -f2)
if [ "${DETECTED_WS}" = "none" ]; then
    LogText "Info: no web server detected, skipping web tests"
    return
fi

# Test: verificare TLS 1.2+ abilitato
Register --test-no CUST-WEB-0010 --weight H --description "Check TLS 1.2+ only"
if [ ${SKIPTEST} -eq 0 ]; then
    if [ "${DETECTED_WS}" = "nginx" ]; then
        TLS_CONF=$(grep -r "ssl_protocols" /etc/nginx/ 2>/dev/null)
        if echo "${TLS_CONF}" | grep -qE "TLSv1[^.]|TLSv1\.0|TLSv1\.1|SSLv"; then
            ReportWarning "${TEST_NO}" "Protocolli TLS deprecati abilitati in nginx"
            AddHP 0 5
        else
            ReportResult "${TEST_NO}" "OK"
            AddHP 5 5
        fi
    fi
fi

# Test: verificare assenza di server token/header
Register --test-no CUST-WEB-0020 --weight M --description "Check server header suppression"
if [ ${SKIPTEST} -eq 0 ]; then
    if [ "${DETECTED_WS}" = "nginx" ]; then
        if grep -rq "server_tokens off" /etc/nginx/ 2>/dev/null; then
            ReportResult "${TEST_NO}" "OK"
            AddHP 3 3
        else
            ReportSuggestion "${TEST_NO}" "Aggiungere 'server_tokens off' alla configurazione nginx"
            AddHP 0 3
        fi
    fi
fi
```

**Ordine di caricamento ed esecuzione:**

| Aspetto | Fase 1 | Fase 2 |
|---------|--------|--------|
| Quando | Prima di tutti i test built-in | Dopo i test built-in del gruppo corrispondente |
| Scopo | Raccolta dati, rilevamento | Valutazione, scoring |
| Output | Variabili e log | Warning, suggestion, hardening points |
| Dipendenze | Nessuna | Puo' dipendere da dati di fase 1 |
| Performance | Leggero, solo lettura | Puo' essere intensivo |

**Convenzioni di naming per plugin custom:**

```
plugin_<nome_dominio>_phase1    # Raccolta dati
plugin_<nome_dominio>_phase2    # Test di compliance
custom_plugin_<nome>.sh         # Plugin singola fase (legacy)
```

**Debug dei plugin:**

```bash
# Eseguire Lynis con debug per vedere l'ordine di caricamento plugin
lynis audit system --debug --verbose 2>&1 | grep -i "plugin"

# Verificare che il plugin venga riconosciuto
lynis show plugins

# Testare un singolo plugin in isolamento
lynis audit system --tests-from-group "custom" --verbose
```

### 4.7 Automazione con cron

```bash
#!/bin/bash
# /etc/cron.weekly/lynis-audit
# Scansione settimanale Lynis con invio risultati

DATE=$(date +%Y%m%d)
REPORT_DIR="/var/log/lynis"
HOSTNAME=$(hostname -f)

mkdir -p "$REPORT_DIR"

# Esecuzione audit
lynis audit system --no-colors --quiet \
  --report-file "${REPORT_DIR}/report-${DATE}.dat" \
  --logfile "${REPORT_DIR}/audit-${DATE}.log" \
  2>&1

# Estrarre hardening index
HI=$(grep "hardening_index" "${REPORT_DIR}/report-${DATE}.dat" | cut -d= -f2)

# Estrarre conteggio warning e suggerimenti
WARNINGS=$(grep -c "warning\[\]" "${REPORT_DIR}/report-${DATE}.dat")
SUGGESTIONS=$(grep -c "suggestion\[\]" "${REPORT_DIR}/report-${DATE}.dat")

# Log strutturato per SIEM (JSON)
cat > "${REPORT_DIR}/summary-${DATE}.json" << EOJSON
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "hostname": "${HOSTNAME}",
  "hardening_index": ${HI},
  "warnings": ${WARNINGS},
  "suggestions": ${SUGGESTIONS},
  "report_file": "${REPORT_DIR}/report-${DATE}.dat"
}
EOJSON

# Alert se sotto soglia
if [ "$HI" -lt 70 ]; then
  echo "ALERT: Hardening Index ${HI} su ${HOSTNAME}" | \
    mail -s "[LYNIS] Hardening Index sotto soglia - ${HOSTNAME}" security@example.com
fi

# Forward JSON al SIEM via webhook
curl -s -X POST "https://siem.example.com/api/ingest" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${SIEM_TOKEN}" \
  -d @"${REPORT_DIR}/summary-${DATE}.json"

# Pulizia vecchi report
find "$REPORT_DIR" -name "*.dat" -mtime +180 -delete
find "$REPORT_DIR" -name "*.log" -mtime +180 -delete
```

### 4.8 Integrazione CI/CD

```yaml
# .gitlab-ci.yml — Lynis nel pipeline
lynis-audit:
  stage: security
  image: cisofy/lynis:latest
  script:
    - lynis audit system --no-colors --quiet
    - |
      HI=$(grep "hardening_index" /var/log/lynis-report.dat | cut -d= -f2)
      echo "Hardening Index: $HI"
      if [ "$HI" -lt 70 ]; then
        echo "FAIL: Hardening Index $HI sotto soglia 70"
        exit 1
      fi
  artifacts:
    paths:
      - /var/log/lynis-report.dat
      - /var/log/lynis.log
    when: always
```

### 4.9 osquery per interrogazione SQL dello stato OS

osquery trasforma il sistema operativo in un database SQL. E' complementare a Lynis per query ad-hoc e monitoraggio continuo.

```bash
# Installazione
curl -L https://pkg.osquery.io/deb/osquery_5.x_amd64.deb -o /tmp/osquery.deb
sudo dpkg -i /tmp/osquery.deb

# Query interattiva
osqueryi

# Query utili per compliance
```

```sql
-- Utenti con UID 0 diversi da root (CIS 6.2.2)
SELECT name, uid, gid, shell FROM users WHERE uid = 0 AND name != 'root';

-- File SUID/SGID nel sistema (CIS 6.1.13-14)
SELECT path, mode, uid, gid FROM suid_bin;

-- File di sistema modificati nelle ultime 24 ore
SELECT path, mtime, size
FROM file
WHERE path LIKE '/etc/%'
  AND mtime > (strftime('%s','now') - 86400);

-- Porte in ascolto con processo associato
SELECT l.port, l.address, l.protocol, p.name, p.cmdline
FROM listening_ports l
JOIN processes p ON l.pid = p.pid
WHERE l.address != '127.0.0.1';

-- Pacchetti con vulnerabilita' note (richiede tabella vulnerabilities)
SELECT name, version, source FROM deb_packages
WHERE name IN ('openssl', 'libssl3', 'openssh-server');

-- Verifica mount options (CIS 1.1.x)
SELECT device, path, type, flags FROM mounts
WHERE path IN ('/tmp', '/var', '/var/log', '/var/log/audit', '/home');

-- Stato dei servizi (systemd)
SELECT name, state, sub_state FROM systemd_units
WHERE name IN ('sshd.service', 'auditd.service', 'firewalld.service');
```

### 4.9 AIDE per file integrity monitoring

AIDE (Advanced Intrusion Detection Environment) verifica l'integrita' dei file confrontando lo stato attuale con un database di riferimento (baseline).

```bash
# Installazione
sudo apt install aide       # Debian/Ubuntu
sudo dnf install aide       # RHEL/Fedora

# Configurazione: /etc/aide/aide.conf (Debian) o /etc/aide.conf (RHEL)
```

```ini
# /etc/aide.conf — configurazione essenziale
database_in=file:/var/lib/aide/aide.db
database_out=file:/var/lib/aide/aide.db.new

# Regole custom
NORMAL = p+i+n+u+g+s+b+m+c+sha256
PERMS = p+i+u+g
LOG = p+i+n+u+g+S

# Monitorare file critici
/etc/passwd     NORMAL
/etc/shadow     NORMAL
/etc/group      NORMAL
/etc/sudoers    NORMAL
/etc/ssh/sshd_config NORMAL
/etc/pam.d      NORMAL

# Directory di log (solo permessi, non contenuto)
/var/log        LOG

# Esclusioni
!/var/log/journal
!/var/cache
!/tmp
!/proc
!/sys
```

```bash
# Inizializzazione baseline
sudo aide --init
sudo mv /var/lib/aide/aide.db.new /var/lib/aide/aide.db

# Verifica integrita'
sudo aide --check

# Output tipico:
# AIDE found differences between database and filesystem!!
#
# Summary:
#   Total number of entries:  42875
#   Added entries:            3
#   Removed entries:          0
#   Changed entries:          7

# Aggiornamento baseline dopo remediation legittima
sudo aide --update
sudo mv /var/lib/aide/aide.db.new /var/lib/aide/aide.db
```

```bash
# Cron giornaliero per AIDE
# /etc/cron.daily/aide-check
#!/bin/bash
AIDE_OUT=$(aide --check 2>&1)
CHANGES=$(echo "$AIDE_OUT" | grep -c "changed:")

if [ "$CHANGES" -gt 0 ]; then
  echo "$AIDE_OUT" | mail -s "[AIDE] File integrity changes detected on $(hostname)" security@example.com
fi
```

---

## 5. Chef InSpec

InSpec tratta la compliance come codice. I profili InSpec sono test eseguibili scritti in Ruby DSL che verificano lo stato del sistema contro aspettative dichiarative.

### 5.1 Installazione

```bash
# Installazione standalone
curl https://omnitruck.chef.io/install.sh | sudo bash -s -- -P inspec

# Via gem (richiede Ruby)
gem install inspec

# Verifica
inspec version
inspec detect   # Mostra info sulla piattaforma
```

### 5.2 Struttura di un profilo

```
my-compliance-profile/
├── inspec.yml            # Metadata del profilo
├── controls/
│   ├── ssh.rb            # Controlli SSH
│   ├── filesystem.rb     # Controlli filesystem
│   ├── users.rb          # Controlli utenti
│   └── network.rb        # Controlli rete
├── files/
│   └── expected_sshd.conf
└── libraries/
    └── helpers.rb
```

**Metadata del profilo:**

```yaml
# inspec.yml
name: linux-hardening
title: Linux Server Hardening Profile
version: 1.0.0
maintainer: Security Team
summary: CIS-aligned Linux hardening checks
license: Apache-2.0
supports:
  - platform-family: redhat
  - platform-family: debian
depends:
  - name: linux-baseline
    url: https://github.com/dev-sec/linux-baseline
    version: ">= 3.0"
```

### 5.3 Scrivere controlli

```ruby
# controls/ssh.rb

title "SSH Server Configuration"

control "ssh-01" do
  impact 1.0
  title "Ensure SSH root login is disabled"
  desc "Root login via SSH should be disabled per CIS 5.2.10"
  tag cis: "5.2.10"
  tag severity: "high"

  describe sshd_config do
    its("PermitRootLogin") { should eq "no" }
  end
end

control "ssh-02" do
  impact 0.7
  title "Ensure SSH MaxAuthTries is set to 4 or less"
  desc "Limit authentication attempts per CIS 5.2.7"
  tag cis: "5.2.7"

  describe sshd_config do
    its("MaxAuthTries") { should cmp <= 4 }
  end
end

control "ssh-03" do
  impact 1.0
  title "Ensure SSH Protocol is set to 2"
  desc "Only SSH protocol version 2 connections should be permitted"

  describe sshd_config do
    its("Protocol") { should cmp 2 }
  end
end

control "ssh-04" do
  impact 0.7
  title "Ensure SSH idle timeout interval is configured"

  describe sshd_config do
    its("ClientAliveInterval") { should cmp <= 300 }
    its("ClientAliveCountMax") { should cmp <= 3 }
  end
end
```

```ruby
# controls/filesystem.rb

title "Filesystem Hardening"

control "fs-01" do
  impact 0.5
  title "Ensure /tmp is a separate partition"
  tag cis: "1.1.2"

  describe mount("/tmp") do
    it { should be_mounted }
  end
end

control "fs-02" do
  impact 0.5
  title "Ensure noexec option set on /tmp"
  tag cis: "1.1.5"

  describe mount("/tmp") do
    its("options") { should include "noexec" }
  end
end

control "fs-03" do
  impact 1.0
  title "Ensure permissions on /etc/shadow are configured"
  tag cis: "6.1.3"

  describe file("/etc/shadow") do
    its("mode") { should cmp "0640" }
    its("owner") { should eq "root" }
    its("group") { should be_in ["root", "shadow"] }
  end
end
```

```ruby
# controls/users.rb

title "User Account Configuration"

control "users-01" do
  impact 1.0
  title "Ensure no duplicate UIDs exist"
  tag cis: "6.2.15"

  describe command("awk -F: '{print $3}' /etc/passwd | sort | uniq -d") do
    its("stdout") { should be_empty }
  end
end

control "users-02" do
  impact 1.0
  title "Ensure root is the only UID 0 account"
  tag cis: "6.2.2"

  describe users.where { uid == 0 } do
    its("usernames") { should eq ["root"] }
  end
end

control "users-03" do
  impact 0.7
  title "Ensure default group for root is GID 0"
  tag cis: "6.2.1"

  describe user("root") do
    its("gid") { should eq 0 }
  end
end
```

### 5.4 Risorse InSpec comuni

| Risorsa | Scopo | Esempio |
|---------|-------|---------|
| `file` | Verifica attributi file | `describe file('/etc/passwd') { its('mode') { should cmp '0644' } }` |
| `service` | Stato servizi | `describe service('sshd') { it { should be_running } }` |
| `package` | Pacchetti installati | `describe package('openssl') { it { should be_installed } }` |
| `port` | Porte in ascolto | `describe port(22) { it { should be_listening } }` |
| `sshd_config` | Configurazione SSH | `describe sshd_config { its('PermitRootLogin') { should eq 'no' } }` |
| `kernel_parameter` | Parametri sysctl | `describe kernel_parameter('net.ipv4.ip_forward') { its('value') { should eq 0 } }` |
| `auditd_rules` | Regole audit | `describe auditd_rules { its('lines') { should include ... } }` |
| `grub_conf` | Config bootloader | `describe grub_conf('/boot/grub2/grub.cfg') { ... }` |
| `mount` | Mount point | `describe mount('/tmp') { its('options') { should include 'noexec' } }` |
| `users` | Utenti di sistema | `describe users.where { uid >= 1000 } { ... }` |
| `command` | Esecuzione comando | `describe command('sysctl net.ipv4.ip_forward') { ... }` |
| `json` | Parsing JSON | `describe json('/etc/config.json') { its('key') { should eq 'val' } }` |
| `ini` | Parsing INI | `describe ini('/etc/security/limits.conf') { ... }` |

### 5.5 Esecuzione e report

```bash
# Esecuzione locale
sudo inspec exec linux-hardening/

# Esecuzione su host remoto via SSH
inspec exec linux-hardening/ -t ssh://admin@192.168.1.100 -i ~/.ssh/id_rsa

# Esecuzione su container Docker
inspec exec linux-hardening/ -t docker://container_id

# Con output specifico
inspec exec linux-hardening/ --reporter cli json:/tmp/results.json html:/tmp/report.html

# Profili community da Supermarket
inspec supermarket exec dev-sec/linux-baseline

# Con specifica soglia di errore
inspec exec linux-hardening/ --controls ssh-01 ssh-02 --reporter cli

# Output JSON per integrazione
inspec exec linux-hardening/ --reporter json | jq '.profiles[].controls[] | {id, status: .results[].status}'
```

### 5.6 Profili community dev-sec

La community dev-sec.io mantiene profili InSpec di alta qualita':

```bash
# Linux baseline (hardening generale)
inspec supermarket exec dev-sec/linux-baseline

# SSH baseline
inspec supermarket exec dev-sec/ssh-baseline

# MySQL/MariaDB baseline
inspec supermarket exec dev-sec/mysql-baseline

# PostgreSQL baseline
inspec supermarket exec dev-sec/postgres-baseline

# Nginx baseline
inspec supermarket exec dev-sec/nginx-baseline

# CIS Distribution Independent Linux Benchmark
inspec supermarket exec dev-sec/cis-dil-benchmark
```

---

## 6. Ansible per la compliance

Ansible e' lo strumento di automazione piu' diffuso per applicare e verificare la compliance su flotte di server Linux.

### 6.1 Ruoli ansible-lockdown

Il progetto ansible-lockdown fornisce ruoli Ansible che implementano CIS Benchmarks e DISA STIG per le principali distribuzioni.

```bash
# Installazione ruoli
ansible-galaxy install ansible-lockdown.rhel9_cis
ansible-galaxy install ansible-lockdown.rhel9_stig
ansible-galaxy install ansible-lockdown.ubuntu2204_cis

# Struttura di un ruolo CIS
# roles/rhel9_cis/
# ├── defaults/main.yml         # Variabili per abilitare/disabilitare rule
# ├── handlers/main.yml         # Handler per restart servizi
# ├── tasks/
# │   ├── main.yml              # Entry point
# │   ├── section_1/            # Initial Setup
# │   ├── section_2/            # Services
# │   ├── section_3/            # Network
# │   ├── section_4/            # Logging
# │   ├── section_5/            # Access and Auth
# │   └── section_6/            # System Maintenance
# └── vars/main.yml             # Variabili interne
```

### 6.2 Playbook di hardening CIS

```yaml
# playbooks/cis-hardening.yml
---
- name: Applicare CIS Benchmark Level 1 Server
  hosts: production_servers
  become: true
  vars:
    # Abilitare/disabilitare sezioni intere
    rhel9cis_section1: true   # Initial Setup
    rhel9cis_section2: true   # Services
    rhel9cis_section3: true   # Network
    rhel9cis_section4: true   # Logging and Auditing
    rhel9cis_section5: true   # Access, Authentication, Authorization
    rhel9cis_section6: true   # System Maintenance

    # Disabilitare regole specifiche che conflittano con l'applicazione
    rhel9cis_rule_1_1_1_1: true    # cramfs
    rhel9cis_rule_1_1_1_2: true    # freevxfs
    rhel9cis_rule_5_2_5: true      # MaxAuthTries
    rhel9cis_rule_5_2_10: true     # PermitRootLogin

    # Override valori
    rhel9cis_sshd_max_auth_tries: 3
    rhel9cis_password_min_length: 14

    # Esclusioni per servizi che devono restare attivi
    rhel9cis_avahi_server: false    # NON disabilitare avahi (usato da mDNS)
    rhel9cis_cups_server: false     # NON disabilitare cups (server di stampa)

  roles:
    - ansible-lockdown.rhel9_cis

  post_tasks:
    - name: Verifica post-hardening
      ansible.builtin.command: lynis audit system --quick --no-colors
      register: lynis_result
      changed_when: false

    - name: Salvare report Lynis
      ansible.builtin.copy:
        content: "{{ lynis_result.stdout }}"
        dest: "/var/log/lynis/post-hardening-{{ ansible_date_time.date }}.log"
        mode: "0600"
```

### 6.3 Playbook di compliance check (senza remediation)

```yaml
# playbooks/compliance-check.yml
---
- name: Verificare compliance CIS senza apportare modifiche
  hosts: all
  become: true
  gather_facts: true

  tasks:
    - name: "[CIS 1.1.1.1] Verificare che cramfs sia disabilitato"
      ansible.builtin.shell: |
        modprobe -n -v cramfs 2>&1 | grep -q "install /bin/true" && \
        lsmod | grep -qv cramfs
      register: cramfs_check
      changed_when: false
      failed_when: false

    - name: "[CIS 5.2.10] Verificare PermitRootLogin"
      ansible.builtin.command: grep -E "^\s*PermitRootLogin\s+no" /etc/ssh/sshd_config
      register: root_login_check
      changed_when: false
      failed_when: false

    - name: "[CIS 5.2.5] Verificare MaxAuthTries"
      ansible.builtin.shell: |
        VALUE=$(grep -E "^\s*MaxAuthTries" /etc/ssh/sshd_config | awk '{print $2}')
        [ "$VALUE" -le 4 ] 2>/dev/null
      register: max_auth_check
      changed_when: false
      failed_when: false

    - name: "[CIS 4.1.3] Verificare auditd attivo"
      ansible.builtin.service_facts:

    - name: Verificare auditd running
      ansible.builtin.assert:
        that:
          - "'auditd.service' in ansible_facts.services"
          - "ansible_facts.services['auditd.service']['state'] == 'running'"
      ignore_errors: true
      register: auditd_check

    - name: "[CIS 6.1.2] Verificare permessi /etc/passwd"
      ansible.builtin.stat:
        path: /etc/passwd
      register: passwd_stat

    - name: Asserzione permessi passwd
      ansible.builtin.assert:
        that:
          - "passwd_stat.stat.mode == '0644'"
          - "passwd_stat.stat.pw_name == 'root'"
      ignore_errors: true
      register: passwd_perm_check

    - name: Generare report compliance
      ansible.builtin.template:
        src: compliance-report.j2
        dest: "/var/log/compliance/report-{{ ansible_date_time.date }}.json"
        mode: "0600"
      vars:
        checks:
          - { id: "CIS-1.1.1.1", name: "cramfs disabled", status: "{{ 'PASS' if cramfs_check.rc == 0 else 'FAIL' }}" }
          - { id: "CIS-5.2.10", name: "PermitRootLogin no", status: "{{ 'PASS' if root_login_check.rc == 0 else 'FAIL' }}" }
          - { id: "CIS-5.2.5", name: "MaxAuthTries <= 4", status: "{{ 'PASS' if max_auth_check.rc == 0 else 'FAIL' }}" }
          - { id: "CIS-4.1.3", name: "auditd running", status: "{{ 'PASS' if auditd_check is not failed else 'FAIL' }}" }
          - { id: "CIS-6.1.2", name: "passwd permissions", status: "{{ 'PASS' if passwd_perm_check is not failed else 'FAIL' }}" }
```

### 6.4 Template Jinja2 per report

```jinja2
{# compliance-report.j2 #}
{
  "hostname": "{{ ansible_fqdn }}",
  "timestamp": "{{ ansible_date_time.iso8601 }}",
  "os": "{{ ansible_distribution }} {{ ansible_distribution_version }}",
  "kernel": "{{ ansible_kernel }}",
  "checks": [
{% for check in checks %}
    {
      "id": "{{ check.id }}",
      "name": "{{ check.name }}",
      "status": "{{ check.status }}"
    }{{ "," if not loop.last else "" }}
{% endfor %}
  ],
  "summary": {
    "total": {{ checks | length }},
    "passed": {{ checks | selectattr('status', 'equalto', 'PASS') | list | length }},
    "failed": {{ checks | selectattr('status', 'equalto', 'FAIL') | list | length }},
    "score": {{ ((checks | selectattr('status', 'equalto', 'PASS') | list | length) / (checks | length) * 100) | round(1) }}
  }
}
```

### 6.5 Ansible Molecule per testing dei ruoli

```yaml
# molecule/default/molecule.yml
---
dependency:
  name: galaxy
driver:
  name: docker
platforms:
  - name: rhel9-compliance
    image: rockylinux:9
    privileged: true
    command: /usr/sbin/init
    volumes:
      - /sys/fs/cgroup:/sys/fs/cgroup:rw
  - name: ubuntu2204-compliance
    image: ubuntu:22.04
    privileged: true
    command: /usr/sbin/init
provisioner:
  name: ansible
  playbooks:
    converge: converge.yml
    verify: verify.yml
verifier:
  name: ansible
```

---

## 7. Puppet e Chef per l'hardening

### 7.1 Puppet: moduli CIS/STIG

```puppet
# Puppetfile
mod 'fervid-secure_linux_cis', '4.0.0'
mod 'puppet-auditd', '5.0.0'
mod 'camptocamp-openscap', '1.0.0'

# manifests/compliance.pp
class profile::compliance {
  class { 'secure_linux_cis':
    enforcement_level   => '1',       # CIS Level 1
    include_stig        => false,
    # Override specifiche
    cis_1_1_1_1         => true,      # cramfs
    cis_5_2_5           => true,      # MaxAuthTries
    max_auth_tries      => 4,
    cis_5_2_10          => true,      # PermitRootLogin
    permit_root_login   => 'no',
    # Esclusioni
    cis_2_2_2           => false,     # Non disabilitare X Window (desktop)
  }

  class { 'auditd':
    rules => [
      '-w /etc/passwd -p wa -k identity',
      '-w /etc/shadow -p wa -k identity',
      '-w /etc/group -p wa -k identity',
      '-w /etc/sudoers -p wa -k sudoers',
      '-a always,exit -F arch=b64 -S execve -F euid=0 -k root_commands',
    ],
  }

  # Scansione periodica OpenSCAP
  class { 'openscap':
    profile   => 'xccdf_org.ssgproject.content_profile_cis_server_l1',
    schedule  => 'weekly',
    report_to => 'https://compliance-dashboard.example.com/api/reports',
  }
}
```

### 7.2 Chef: cookbook per hardening

```ruby
# Berksfile
source 'https://supermarket.chef.io'
cookbook 'os-hardening', '~> 5.0'
cookbook 'ssh-hardening', '~> 3.0'
cookbook 'audit', '~> 10.0'

# recipes/compliance.rb

# OS hardening base
include_recipe 'os-hardening::default'

# SSH hardening
include_recipe 'ssh-hardening::default'

# Configurazione attributi
node.default['os-hardening']['security']['suid_sgid_whitelist'] = [
  '/usr/bin/sudo',
  '/usr/bin/passwd',
  '/usr/bin/chsh',
]

node.default['ssh-hardening']['ssh']['server']['permit_root_login'] = 'no'
node.default['ssh-hardening']['ssh']['server']['max_auth_tries'] = 4
node.default['ssh-hardening']['ssh']['server']['password_authentication'] = 'no'

# InSpec audit integrato
node.default['audit']['profiles'] = [
  { name: 'linux-baseline', url: 'https://github.com/dev-sec/linux-baseline' },
  { name: 'ssh-baseline', url: 'https://github.com/dev-sec/ssh-baseline' },
]
node.default['audit']['reporter'] = 'chef-automate'
node.default['audit']['waiver_file'] = '/etc/chef/compliance-waivers.yml'
```

**Waiver file per esclusioni legittime:**

```yaml
# /etc/chef/compliance-waivers.yml
os-01:
  expiration_date: "2026-12-31"
  justification: "Server di stampa richiede cups attivo"
  run: false

ssh-04:
  expiration_date: "2026-08-01"
  justification: "Applicazione legacy richiede password auth fino a migrazione"
  run: true   # Eseguire il test ma non fallire
```

---

## 8. Compliance nel cloud

### 8.1 AWS Systems Manager Compliance

AWS SSM State Manager e Compliance permettono di applicare e verificare la conformita' di istanze EC2.

```bash
# Associare un documento SSM per scansione OpenSCAP
aws ssm create-association \
  --name "AWS-RunInspecChecks" \
  --targets "Key=tag:Environment,Values=production" \
  --parameters '{
    "sourceType": ["GitHub"],
    "sourceInfo": ["{\"owner\":\"dev-sec\",\"repository\":\"linux-baseline\"}"]
  }' \
  --schedule-expression "rate(7 days)"

# Visualizzare compliance
aws ssm list-compliance-items \
  --resource-ids "i-0123456789abcdef0" \
  --resource-types "ManagedInstance" \
  --filters "Key=ComplianceType,Values=Association,Type=EQUAL"
```

**AWS Config Rules per compliance Linux:**

```json
{
  "ConfigRuleName": "ec2-instances-in-vpc",
  "Source": {
    "Owner": "AWS",
    "SourceIdentifier": "INSTANCES_IN_VPC"
  }
}
```

```bash
# Regole AWS Config rilevanti per compliance Linux
aws configservice put-config-rule --config-rule '{
  "ConfigRuleName": "ec2-ssh-restricted",
  "Source": {
    "Owner": "AWS",
    "SourceIdentifier": "INCOMING_SSH_DISABLED"
  }
}'

# Verifica stato compliance
aws configservice get-compliance-details-by-config-rule \
  --config-rule-name "ec2-ssh-restricted" \
  --compliance-types "NON_COMPLIANT"
```

### 8.2 Azure Policy Guest Configuration

Azure Guest Configuration verifica la configurazione interna delle VM Linux.

```bash
# Assegnare policy di audit per CIS su VM Linux
az policy assignment create \
  --name "cis-linux-audit" \
  --policy-set-definition "CIS Microsoft Azure Foundations Benchmark" \
  --scope "/subscriptions/{sub-id}/resourceGroups/{rg}" \
  --params '{
    "effect": "AuditIfNotExists"
  }'

# Visualizzare risultati Guest Configuration
az policy state list \
  --resource-group "production-rg" \
  --filter "complianceState eq 'NonCompliant'" \
  --query "[].{policy:policyDefinitionName, resource:resourceId}"
```

**Creare una Guest Configuration personalizzata:**

```powershell
# DSC configuration per Linux
Configuration LinuxHardening {
    Import-DscResource -ModuleName 'nx'

    Node "localhost" {
        nxFile SSHConfig {
            DestinationPath = "/etc/ssh/sshd_config"
            Ensure = "Present"
            Contents = @"
PermitRootLogin no
MaxAuthTries 4
PasswordAuthentication no
"@
        }

        nxService AuditdRunning {
            Name = "auditd"
            State = "Running"
            Enabled = $true
        }
    }
}
```

### 8.3 GCP Organization Policy

```bash
# Impostare vincoli a livello di organizzazione
gcloud resource-manager org-policies enable-enforce \
  --organization=ORG_ID \
  compute.requireOsLogin

# Policy per richiedere shielded VM
gcloud resource-manager org-policies enable-enforce \
  --organization=ORG_ID \
  compute.requireShieldedVm

# Visualizzare compliance
gcloud scc findings list ORG_ID \
  --source="-" \
  --filter="category=\"OS_VULNERABILITY\" AND state=\"ACTIVE\""
```

**GCP VM Manager OS Policies per compliance:**

```yaml
# os-policy-assignment.yaml
osPolicies:
  - id: cis-hardening
    mode: ENFORCEMENT
    resourceGroups:
      - resources:
          - id: ensure-auditd
            pkg:
              desiredState: INSTALLED
              apt:
                name: auditd
          - id: sshd-config
            file:
              path: /etc/ssh/sshd_config
              state: CONTENTS_MATCH
              content:
                inline: |
                  PermitRootLogin no
                  MaxAuthTries 4
                  X11Forwarding no
    inventoryFilters:
      - osShortName: ubuntu
        osVersion: "22.04"
```

---

## 9. Compliance per container e Kubernetes

### 9.1 Docker Bench for Security

Docker Bench for Security verifica la conformita' al CIS Docker Benchmark.

```bash
# Esecuzione rapida
docker run --rm --net host --pid host --userns host --cap-add audit_control \
  -e DOCKER_CONTENT_TRUST=$DOCKER_CONTENT_TRUST \
  -v /var/lib:/var/lib:ro \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -v /usr/lib/systemd:/usr/lib/systemd:ro \
  -v /etc:/etc:ro \
  docker/docker-bench-security

# Output parziale:
# [PASS] 1.1 - Ensure a separate partition for containers has been created
# [WARN] 1.2 - Ensure only trusted users are allowed to control Docker daemon
# [PASS] 2.1 - Run the Docker daemon as a non-root user
# [WARN] 2.2 - Ensure network traffic is restricted between containers
# [PASS] 4.1 - Ensure a user for the container has been created
# [WARN] 4.6 - Ensure HEALTHCHECK instructions have been added to container images
# [PASS] 5.1 - Ensure that, if applicable, an AppArmor Profile is enabled
```

### 9.2 kube-bench (CIS Kubernetes Benchmark)

```bash
# Installazione
curl -L https://github.com/aquasecurity/kube-bench/releases/download/v0.8.0/kube-bench_0.8.0_linux_amd64.tar.gz | tar xz
sudo mv kube-bench /usr/local/bin/

# Esecuzione su nodo master
sudo kube-bench run --targets master

# Esecuzione su nodo worker
sudo kube-bench run --targets node

# Output JSON per integrazione
sudo kube-bench run --targets master --json > /tmp/kube-bench-master.json

# Esecuzione come Job nel cluster
kubectl apply -f https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job.yaml
kubectl logs job/kube-bench
```

**Output tipico kube-bench:**

```
[INFO] 1 Control Plane Components
[PASS] 1.1.1 Ensure that the API server pod specification file permissions are set to 600
[PASS] 1.1.2 Ensure that the API server pod specification file ownership is root:root
[FAIL] 1.1.3 Ensure that the controller manager pod specification has permissions 600
[WARN] 1.2.1 Ensure that the --anonymous-auth argument is set to false

== Summary ==
45 checks PASS
8 checks FAIL
12 checks WARN
0 checks INFO
```

### 9.3 Trivy per compliance container

Trivy non si limita alla vulnerability scanning: supporta misconfiguration detection e compliance check.

```bash
# Installazione
sudo apt install trivy    # Via repository Aqua Security

# Scansione vulnerabilita' immagine
trivy image --severity HIGH,CRITICAL nginx:latest

# Scansione misconfiguration di un Dockerfile
trivy config ./Dockerfile

# Scansione compliance Kubernetes
trivy k8s --compliance k8s-cis --report summary cluster

# Scansione compliance NSA-CISA
trivy k8s --compliance k8s-nsa --report summary cluster

# Scansione filesystem per secret esposti
trivy fs --scanners secret ./

# Output SARIF per integrazione CI/CD
trivy image --format sarif -o trivy-results.sarif myapp:latest
```

### 9.4 Compliance per immagini container

```dockerfile
# Dockerfile conforme alle best practice CIS
FROM ubuntu:22.04 AS base

# CIS 4.1 — Creare utente non-root
RUN groupadd -r appuser && useradd -r -g appuser -s /sbin/nologin appuser

# CIS 4.3 — Non installare pacchetti non necessari
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      ca-certificates \
      curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# CIS 4.6 — HEALTHCHECK
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# CIS 4.9 — Copiare solo file necessari
COPY --chown=appuser:appuser ./app /opt/app

# CIS 4.1 — Eseguire come utente non-root
USER appuser

# CIS 4.7 — Non usare ADD per URL
# (usa COPY + download separato se necessario)

EXPOSE 8080
ENTRYPOINT ["/opt/app/server"]
```

---

## 10. Remediation automatizzata

### 10.1 Principi di remediation sicura

La remediation automatizzata e' potente ma pericolosa. Un singolo errore puo' rendere inaccessibile un'intera flotta di server.

**Principio 1: Dry-run first, always**

```bash
# OpenSCAP: generare script di remediation ma NON eseguirlo
oscap xccdf generate fix \
  --fix-type bash \
  --profile xccdf_org.ssgproject.content_profile_cis_server_l1 \
  --output /tmp/remediate.sh \
  /usr/share/xml/scap/ssg/content/ssg-rhel9-ds.xml

# Revisione manuale obbligatoria
less /tmp/remediate.sh

# Ansible: check mode (dry-run)
ansible-playbook cis-hardening.yml --check --diff
```

**Principio 2: Canary deployment della remediation**

```yaml
# playbooks/remediate-canary.yml
---
- name: "Remediation canary — 1 server per gruppo"
  hosts: canary_servers
  serial: 1
  become: true
  max_fail_percentage: 0

  pre_tasks:
    - name: Snapshot pre-remediation
      ansible.builtin.command: >
        lvm snapshot create /dev/vg0/root-snap
      when: ansible_lvm is defined
      ignore_errors: true

    - name: Registrare stato servizi pre-remediation
      ansible.builtin.shell: systemctl list-units --type=service --state=running --no-pager
      register: services_pre

  roles:
    - ansible-lockdown.rhel9_cis

  post_tasks:
    - name: Verificare servizi critici post-remediation
      ansible.builtin.service_facts:

    - name: Assert servizi critici attivi
      ansible.builtin.assert:
        that:
          - "'sshd.service' in ansible_facts.services"
          - "ansible_facts.services['sshd.service']['state'] == 'running'"
          - "'auditd.service' in ansible_facts.services"
          - "ansible_facts.services['auditd.service']['state'] == 'running'"
        fail_msg: "SERVIZIO CRITICO DOWN — rollback necessario"

    - name: Verificare connettivita' SSH
      ansible.builtin.wait_for:
        host: "{{ inventory_hostname }}"
        port: 22
        timeout: 30

    - name: Pausa per verifica manuale
      ansible.builtin.pause:
        prompt: "Canary {{ inventory_hostname }} completato. Verificare e premere Enter per continuare"
      when: canary_pause | default(true)
```

**Principio 3: Rollback automatico**

```yaml
# handlers/rollback.yml
- name: Rollback SSH config
  ansible.builtin.copy:
    src: /etc/ssh/sshd_config.backup
    dest: /etc/ssh/sshd_config
    remote_src: true
  notify: Restart sshd

- name: Restart sshd
  ansible.builtin.service:
    name: sshd
    state: restarted
```

### 10.2 Workflow di approvazione

```yaml
# Pipeline di remediation con approvazione
# 1. Scan → 2. Report → 3. Review → 4. Approve → 5. Remediate → 6. Verify

# Esempio con GitLab CI
stages:
  - scan
  - report
  - approve
  - remediate
  - verify

compliance-scan:
  stage: scan
  script:
    - ansible-playbook compliance-check.yml -i inventory.yml
  artifacts:
    paths:
      - reports/compliance-*.json

generate-report:
  stage: report
  script:
    - python3 scripts/generate-compliance-report.py
  artifacts:
    paths:
      - reports/compliance-summary.html

manual-approval:
  stage: approve
  script:
    - echo "Remediation approvata da $(whoami) in data $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  when: manual
  allow_failure: false

apply-remediation:
  stage: remediate
  script:
    - ansible-playbook cis-hardening.yml -i inventory.yml --limit canary
    - sleep 300  # Attesa 5 minuti per verifica canary
    - ansible-playbook cis-hardening.yml -i inventory.yml
  needs:
    - manual-approval

post-remediation-scan:
  stage: verify
  script:
    - ansible-playbook compliance-check.yml -i inventory.yml
    - python3 scripts/compare-before-after.py
```

### 10.3 Esclusioni e waiver

```yaml
# compliance-waivers.yml
# Documentare ogni esclusione con:
# - Chi ha approvato
# - Perche' e' necessaria
# - Quando scade
# - Controlli compensativi

waivers:
  - rule_id: "CIS-2.2.2"
    description: "X Window System necessario su workstation sviluppatori"
    approved_by: "CISO"
    approval_date: "2026-03-15"
    expiration_date: "2026-09-15"
    compensating_controls:
      - "Screen lock dopo 5 minuti di inattivita'"
      - "Firewall host-based attivo"
      - "EDR installato"

  - rule_id: "CIS-5.3.4"
    description: "Password authentication necessaria per integrazione LDAP legacy"
    approved_by: "Security Lead"
    approval_date: "2026-01-10"
    expiration_date: "2026-07-10"
    compensating_controls:
      - "Fail2ban configurato con ban dopo 3 tentativi"
      - "MFA via PAM per utenti LDAP"
      - "Monitoraggio accessi SSH in tempo reale"
    migration_plan: "Migrazione a certificate-based auth prevista per Q3 2026"
```

---

## 11. Reporting e raccolta evidenze

### 11.1 Architettura di reporting

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  OpenSCAP   │────>│              │────>│  Dashboard   │
│  Lynis      │     │  Collector   │     │  (Grafana)   │
│  InSpec     │     │  (Logstash/  │     │              │
│  kube-bench │     │   Fluentd)   │     │  Reports     │
│  Ansible    │     │              │     │  (PDF/HTML)  │
└─────────────┘     └──────┬───────┘     └──────────────┘
                           │
                    ┌──────▼───────┐
                    │ Data Store   │
                    │ (Elastic /   │
                    │  PostgreSQL) │
                    └──────────────┘
```

### 11.2 Script di raccolta evidenze per auditor

```bash
#!/bin/bash
# collect-evidence.sh — Raccolta evidenze per audit di compliance
# Eseguire su ogni server da auditare

set -euo pipefail

EVIDENCE_DIR="/tmp/evidence-$(hostname -f)-$(date +%Y%m%d)"
mkdir -p "$EVIDENCE_DIR"

echo "[*] Raccolta evidenze su $(hostname -f) — $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# 1. Informazioni sistema
{
  echo "=== SISTEMA ==="
  uname -a
  cat /etc/os-release
  uptime
  echo ""
  echo "=== KERNEL ==="
  sysctl -a 2>/dev/null | grep -E "(ip_forward|send_redirects|accept_source|accept_redirects|log_martians|syncookies)"
} > "$EVIDENCE_DIR/01-system-info.txt"

# 2. Utenti e accesso
{
  echo "=== UTENTI CON UID 0 ==="
  awk -F: '$3 == 0 {print}' /etc/passwd
  echo ""
  echo "=== UTENTI CON SHELL VALIDA ==="
  grep -v "/nologin\|/false" /etc/passwd
  echo ""
  echo "=== SUDOERS ==="
  cat /etc/sudoers 2>/dev/null
  ls -la /etc/sudoers.d/ 2>/dev/null
  echo ""
  echo "=== GRUPPI PRIVILEGIATI ==="
  getent group wheel sudo adm 2>/dev/null
} > "$EVIDENCE_DIR/02-users-access.txt"

# 3. SSH config
{
  echo "=== SSHD CONFIG ==="
  sshd -T 2>/dev/null | grep -E "(permitrootlogin|maxauthtries|passwordauthentication|x11forwarding|allowtcpforwarding|clientalive)"
} > "$EVIDENCE_DIR/03-ssh-config.txt"

# 4. Servizi attivi
{
  echo "=== SERVIZI IN ESECUZIONE ==="
  systemctl list-units --type=service --state=running --no-pager
  echo ""
  echo "=== PORTE IN ASCOLTO ==="
  ss -tulnp
} > "$EVIDENCE_DIR/04-services-ports.txt"

# 5. Firewall
{
  echo "=== FIREWALL RULES ==="
  iptables -L -n -v 2>/dev/null || nft list ruleset 2>/dev/null || echo "No firewall detected"
} > "$EVIDENCE_DIR/05-firewall.txt"

# 6. Logging
{
  echo "=== AUDITD STATUS ==="
  auditctl -s 2>/dev/null
  echo ""
  echo "=== AUDITD RULES ==="
  auditctl -l 2>/dev/null
  echo ""
  echo "=== RSYSLOG/JOURNALD CONFIG ==="
  cat /etc/rsyslog.conf 2>/dev/null | grep -v "^#\|^$"
  echo ""
  echo "=== LOG ROTATION ==="
  cat /etc/logrotate.conf 2>/dev/null | grep -v "^#\|^$"
} > "$EVIDENCE_DIR/06-logging.txt"

# 7. Patch status
{
  echo "=== ULTIMO AGGIORNAMENTO ==="
  rpm -qa --last 2>/dev/null | head -20 || apt list --installed 2>/dev/null | tail -20
  echo ""
  echo "=== AGGIORNAMENTI DISPONIBILI ==="
  dnf check-update --security 2>/dev/null || apt list --upgradable 2>/dev/null
} > "$EVIDENCE_DIR/07-patch-status.txt"

# 8. Cifratura
{
  echo "=== LUKS VOLUMES ==="
  lsblk -o NAME,FSTYPE,SIZE,MOUNTPOINT | grep -i crypt
  echo ""
  echo "=== TLS CONFIG (openssl) ==="
  openssl version
} > "$EVIDENCE_DIR/08-encryption.txt"

# 9. Integrity monitoring
{
  echo "=== AIDE DATABASE ==="
  ls -la /var/lib/aide/aide.db* 2>/dev/null
  echo ""
  echo "=== ULTIMO CHECK AIDE ==="
  grep -i "aide" /var/log/cron* 2>/dev/null | tail -5
} > "$EVIDENCE_DIR/09-integrity.txt"

# 10. Scansione compliance
{
  echo "=== LYNIS AUDIT ==="
  lynis audit system --quick --no-colors 2>/dev/null | tail -30
} > "$EVIDENCE_DIR/10-compliance-scan.txt"

# Creare archivio
tar czf "${EVIDENCE_DIR}.tar.gz" -C /tmp "$(basename $EVIDENCE_DIR)"
echo "[+] Evidenze salvate in ${EVIDENCE_DIR}.tar.gz"

# Calcolare hash per integrita'
sha256sum "${EVIDENCE_DIR}.tar.gz" > "${EVIDENCE_DIR}.tar.gz.sha256"
echo "[+] Hash: $(cat ${EVIDENCE_DIR}.tar.gz.sha256)"
```

### 11.3 Dashboard Grafana per compliance

```json
{
  "dashboard": {
    "title": "Linux Compliance Dashboard",
    "panels": [
      {
        "title": "Compliance Score per Host",
        "type": "gauge",
        "datasource": "Elasticsearch",
        "targets": [
          {
            "query": "compliance_score",
            "metrics": [{ "type": "avg", "field": "score" }],
            "bucketAggs": [{ "type": "terms", "field": "hostname.keyword" }]
          }
        ],
        "fieldConfig": {
          "defaults": {
            "thresholds": {
              "steps": [
                { "value": 0, "color": "red" },
                { "value": 70, "color": "yellow" },
                { "value": 85, "color": "green" }
              ]
            },
            "min": 0, "max": 100
          }
        }
      },
      {
        "title": "Trend Compliance Settimanale",
        "type": "timeseries",
        "datasource": "Elasticsearch",
        "targets": [
          {
            "query": "compliance_score",
            "metrics": [{ "type": "avg", "field": "score" }],
            "bucketAggs": [
              { "type": "date_histogram", "field": "@timestamp", "settings": { "interval": "1w" } }
            ]
          }
        ]
      },
      {
        "title": "Top 10 Failing Rules",
        "type": "barchart",
        "datasource": "Elasticsearch",
        "targets": [
          {
            "query": "rule_status:fail",
            "metrics": [{ "type": "count" }],
            "bucketAggs": [{ "type": "terms", "field": "rule_id.keyword", "size": 10 }]
          }
        ]
      }
    ]
  }
}
```

### 11.4 Report automatico per auditor

```python
#!/usr/bin/env python3
"""generate_audit_report.py — Genera report compliance in formato auditor-friendly."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

def load_results(results_dir: str) -> list[dict]:
    results = []
    for f in Path(results_dir).glob("compliance-*.json"):
        with open(f) as fh:
            results.append(json.load(fh))
    return results

def generate_html_report(results: list[dict], output_path: str) -> None:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    total_hosts = len(results)
    compliant = sum(1 for r in results if r["summary"]["score"] >= 80)
    non_compliant = total_hosts - compliant

    html = f"""<!DOCTYPE html>
<html>
<head><title>Compliance Report — {timestamp}</title>
<style>
  body {{ font-family: sans-serif; margin: 2rem; }}
  table {{ border-collapse: collapse; width: 100%; margin-top: 1rem; }}
  th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
  th {{ background: #333; color: white; }}
  .pass {{ background: #d4edda; }}
  .fail {{ background: #f8d7da; }}
  .summary {{ display: flex; gap: 2rem; margin: 1rem 0; }}
  .card {{ padding: 1rem; border-radius: 4px; min-width: 150px; text-align: center; }}
</style>
</head>
<body>
<h1>Report di Compliance — {timestamp}</h1>
<div class="summary">
  <div class="card pass"><h2>{compliant}</h2><p>Host Conformi</p></div>
  <div class="card fail"><h2>{non_compliant}</h2><p>Host Non Conformi</p></div>
  <div class="card" style="background:#e2e3e5"><h2>{total_hosts}</h2><p>Host Totali</p></div>
</div>
<table>
<tr><th>Hostname</th><th>OS</th><th>Score</th><th>Pass</th><th>Fail</th><th>Timestamp</th></tr>
"""
    for r in sorted(results, key=lambda x: x["summary"]["score"]):
        css = "pass" if r["summary"]["score"] >= 80 else "fail"
        html += f"""<tr class="{css}">
  <td>{r['hostname']}</td><td>{r['os']}</td>
  <td>{r['summary']['score']}%</td>
  <td>{r['summary']['passed']}</td><td>{r['summary']['failed']}</td>
  <td>{r['timestamp']}</td>
</tr>\n"""

    html += "</table></body></html>"

    with open(output_path, "w") as fh:
        fh.write(html)
    print(f"Report generato: {output_path}")

if __name__ == "__main__":
    results_dir = sys.argv[1] if len(sys.argv) > 1 else "/var/log/compliance"
    output_path = sys.argv[2] if len(sys.argv) > 2 else "/tmp/compliance-report.html"
    results = load_results(results_dir)
    if not results:
        print("Nessun risultato trovato", file=sys.stderr)
        sys.exit(1)
    generate_html_report(results, output_path)
```

---

## 12. Drift detection

Il drift detection identifica quando la configurazione di un sistema si discosta dalla baseline di compliance approvata. E' il complemento essenziale della scansione periodica: senza drift detection, le deviazioni vengono scoperte solo alla scansione successiva.

### 12.1 AIDE per drift detection

```bash
# Inizializzare baseline dopo hardening
sudo aide --init
sudo mv /var/lib/aide/aide.db.new /var/lib/aide/aide.db

# Verificare drift
sudo aide --check

# Output in caso di drift:
# AIDE found differences between database and filesystem!!
# Changed entries:
# ---------------------------------------------------
# f = p..S..    : /etc/ssh/sshd_config
# f = ...H..    : /etc/pam.d/common-auth
# d = .....a.   : /etc/audit/rules.d
```

### 12.2 Git-based compliance (GitOps)

Versionate le configurazioni di compliance in Git. Ogni modifica e' tracciabile, reversibile, e soggetta a review.

```bash
# Struttura repository compliance
# compliance-configs/
# ├── hosts/
# │   ├── web-prod-01/
# │   │   ├── etc/
# │   │   │   ├── ssh/sshd_config
# │   │   │   ├── audit/auditd.conf
# │   │   │   └── pam.d/common-auth
# │   │   └── compliance-status.json
# │   ├── db-prod-01/
# │   └── ...
# ├── baselines/
# │   ├── cis-l1-server.yml
# │   └── stig-rhel9.yml
# └── waivers/
#     └── approved-waivers.yml
```

**Script di drift detection basato su Git:**

```bash
#!/bin/bash
# drift-check.sh — Confronto configurazione attuale con baseline Git

set -euo pipefail

REPO_DIR="/opt/compliance-configs"
HOST_DIR="$REPO_DIR/hosts/$(hostname -f)"
DRIFT_FOUND=0

# File da monitorare
WATCHED_FILES=(
  "/etc/ssh/sshd_config"
  "/etc/audit/auditd.conf"
  "/etc/audit/rules.d/audit.rules"
  "/etc/pam.d/common-auth"
  "/etc/pam.d/common-password"
  "/etc/security/limits.conf"
  "/etc/sysctl.d/99-hardening.conf"
  "/etc/login.defs"
)

for FILE in "${WATCHED_FILES[@]}"; do
  RELATIVE="${FILE#/}"
  BASELINE="$HOST_DIR/$RELATIVE"

  if [ ! -f "$BASELINE" ]; then
    echo "[WARN] Baseline mancante per $FILE"
    continue
  fi

  if ! diff -q "$FILE" "$BASELINE" > /dev/null 2>&1; then
    echo "[DRIFT] $FILE differisce dalla baseline"
    diff --unified "$BASELINE" "$FILE" || true
    DRIFT_FOUND=1
  else
    echo "[OK] $FILE conforme alla baseline"
  fi
done

if [ "$DRIFT_FOUND" -eq 1 ]; then
  echo ""
  echo "[ALERT] Drift rilevato su $(hostname -f) — $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  # Notifica
  curl -s -X POST "https://hooks.slack.com/services/T.../B.../..." \
    -H "Content-Type: application/json" \
    -d "{\"text\":\"Configuration drift rilevato su $(hostname -f)\"}"
  exit 1
fi

echo "[OK] Nessun drift rilevato"
```

### 12.3 Drift detection continuo con osquery

```ini
# /etc/osquery/osquery.conf
{
  "schedule": {
    "sshd_config_changes": {
      "query": "SELECT path, mtime, sha256 FROM hash WHERE path = '/etc/ssh/sshd_config';",
      "interval": 300,
      "description": "Monitorare modifiche a sshd_config ogni 5 minuti"
    },
    "sudoers_changes": {
      "query": "SELECT path, mtime, sha256 FROM hash WHERE path = '/etc/sudoers';",
      "interval": 300,
      "description": "Monitorare modifiche a sudoers ogni 5 minuti"
    },
    "new_listening_ports": {
      "query": "SELECT port, protocol, pid, name FROM listening_ports l JOIN processes p ON l.pid = p.pid WHERE port NOT IN (22, 80, 443);",
      "interval": 60,
      "description": "Rilevare nuove porte in ascolto non standard"
    },
    "new_users": {
      "query": "SELECT username, uid, gid, directory, shell FROM users WHERE uid >= 1000;",
      "interval": 600,
      "description": "Monitorare creazione nuovi utenti"
    },
    "suid_binaries": {
      "query": "SELECT path, mode, uid, gid FROM suid_bin WHERE path NOT IN ('/usr/bin/sudo', '/usr/bin/passwd', '/usr/bin/chsh', '/usr/bin/newgrp');",
      "interval": 3600,
      "description": "Rilevare nuovi binari SUID"
    }
  },
  "packs": {
    "compliance": "/etc/osquery/packs/compliance.conf"
  }
}
```

### 12.4 Alerting automatizzato su drift

```yaml
# Ansible playbook per drift alerting
---
- name: Verifica drift configurazione
  hosts: all
  become: true
  gather_facts: true

  vars:
    expected_sshd_settings:
      PermitRootLogin: "no"
      MaxAuthTries: "4"
      PasswordAuthentication: "no"
      X11Forwarding: "no"

  tasks:
    - name: Leggere configurazione sshd effettiva
      ansible.builtin.command: sshd -T
      register: sshd_actual
      changed_when: false

    - name: Verificare ogni parametro sshd
      ansible.builtin.assert:
        that:
          - "sshd_actual.stdout | regex_search('(?m)^' + item.key | lower + ' ' + item.value)"
        fail_msg: "DRIFT: {{ item.key }} non e' impostato a {{ item.value }}"
        success_msg: "OK: {{ item.key }} = {{ item.value }}"
      loop: "{{ expected_sshd_settings | dict2items }}"
      ignore_errors: true
      register: drift_results

    - name: Raccogliere drift trovati
      ansible.builtin.set_fact:
        drifts: "{{ drift_results.results | selectattr('failed', 'true') | map(attribute='item') | list }}"

    - name: Inviare alert se drift rilevato
      ansible.builtin.uri:
        url: "https://hooks.slack.com/services/T.../B.../..."
        method: POST
        body_format: json
        body:
          text: "Configuration drift su {{ ansible_fqdn }}: {{ drifts | map(attribute='key') | join(', ') }}"
      when: drifts | length > 0
```

---

## 13. Integrazione con vulnerability management

### 13.1 CVE scanning + compliance = risk score combinato

La compliance scanning (CIS/STIG) e la vulnerability scanning (CVE) rispondono a domande diverse ma complementari:

| Aspetto | Compliance Scan | Vulnerability Scan |
|---------|-----------------|-------------------|
| Domanda | "Il sistema e' configurato correttamente?" | "Il sistema ha software vulnerabile?" |
| Fonte | CIS Benchmark, STIG | CVE database (NVD) |
| Strumenti | OpenSCAP profile, Lynis, InSpec | OpenSCAP OVAL, Nessus, Qualys, Trivy |
| Output | Pass/Fail per regola | CVE con CVSS score |
| Remediation | Modifica configurazione | Patch/aggiornamento |

**Score combinato:**

```python
def calculate_combined_risk(compliance_score: float, vuln_data: dict) -> dict:
    """
    Calcola un risk score combinato compliance + vulnerabilita'.

    compliance_score: 0-100 (da OpenSCAP/Lynis)
    vuln_data: { "critical": N, "high": N, "medium": N, "low": N }
    """
    # Peso per severita' CVE
    vuln_penalty = (
        vuln_data.get("critical", 0) * 10 +
        vuln_data.get("high", 0) * 5 +
        vuln_data.get("medium", 0) * 2 +
        vuln_data.get("low", 0) * 0.5
    )

    # Normalizzare penalty (max 50 punti di penalita')
    normalized_penalty = min(vuln_penalty, 50)

    # Risk score: compliance contribuisce per 50%, vuln per 50%
    compliance_component = compliance_score * 0.5
    vuln_component = max(0, 50 - normalized_penalty)

    combined_score = compliance_component + vuln_component

    risk_level = (
        "CRITICAL" if combined_score < 40 else
        "HIGH" if combined_score < 60 else
        "MEDIUM" if combined_score < 80 else
        "LOW"
    )

    return {
        "combined_score": round(combined_score, 1),
        "risk_level": risk_level,
        "compliance_score": compliance_score,
        "vulnerability_penalty": normalized_penalty,
    }
```

### 13.2 OpenSCAP per vulnerability scanning

```bash
# Scaricare OVAL definitions per la propria distribuzione
# RHEL
wget https://access.redhat.com/security/data/oval/v2/RHEL9/rhel-9.oval.xml.bz2
bunzip2 rhel-9.oval.xml.bz2

# Ubuntu
wget https://security-metadata.canonical.com/oval/com.ubuntu.jammy.usn.oval.xml.bz2
bunzip2 com.ubuntu.jammy.usn.oval.xml.bz2

# Scansione OVAL per vulnerabilita'
oscap oval eval \
  --results /var/log/oscap/oval-results.xml \
  --report /var/log/oscap/oval-report.html \
  rhel-9.oval.xml

# Estrarre CVE rilevate
oscap oval eval --results /tmp/oval.xml rhel-9.oval.xml
grep 'result="true"' /tmp/oval.xml | grep -o 'CVE-[0-9-]*'
```

### 13.3 Pipeline combinata compliance + vulnerability

```yaml
# gitlab-ci.yml
stages:
  - compliance
  - vulnerability
  - risk-assessment
  - report

compliance-scan:
  stage: compliance
  script:
    - oscap xccdf eval --profile cis_server_l1 --results compliance.xml $DS
    - SCORE=$(oscap xccdf eval --profile cis_server_l1 $DS 2>&1 | grep Score | awk '{print $NF}')
    - echo "{\"compliance_score\": $SCORE}" > metrics/compliance.json
  artifacts:
    paths: [compliance.xml, metrics/]

vulnerability-scan:
  stage: vulnerability
  script:
    - oscap oval eval --results oval.xml rhel-9.oval.xml
    - trivy rootfs --format json -o trivy.json /
    - python3 scripts/extract-vuln-counts.py trivy.json > metrics/vuln.json
  artifacts:
    paths: [oval.xml, trivy.json, metrics/]

risk-assessment:
  stage: risk-assessment
  script:
    - python3 scripts/combined-risk.py metrics/compliance.json metrics/vuln.json > metrics/risk.json
    - cat metrics/risk.json
  artifacts:
    paths: [metrics/risk.json]

generate-report:
  stage: report
  script:
    - python3 scripts/generate-combined-report.py
  artifacts:
    paths: [reports/combined-report.html]
```

---

## 14. Compliance gate nelle pipeline CI/CD

### 14.1 Principi

Un compliance gate e' un checkpoint nella pipeline CI/CD che blocca il deployment se il sistema target (o l'artefatto) non soddisfa i requisiti di compliance.

**Dove inserire i gate:**

```
Build → Test → [Compliance Gate: Image] → Stage → [Compliance Gate: Config] → Prod
```

### 14.2 Gate per immagini container

```yaml
# GitHub Actions — compliance gate per immagini Docker
name: Compliance Gate
on:
  push:
    branches: [main]

jobs:
  build-and-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build image
        run: docker build -t myapp:${{ github.sha }} .

      - name: Trivy vulnerability scan
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: myapp:${{ github.sha }}
          format: json
          output: trivy-results.json
          severity: CRITICAL,HIGH
          exit-code: 1

      - name: Docker Bench scan
        run: |
          docker run --rm \
            -v /var/run/docker.sock:/var/run/docker.sock:ro \
            docker/docker-bench-security 2>&1 | tee docker-bench.txt

          # Fallire se ci sono WARN di severita' alta
          WARNS=$(grep -c "\[WARN\]" docker-bench.txt)
          if [ "$WARNS" -gt 5 ]; then
            echo "Troppi warning Docker Bench: $WARNS"
            exit 1
          fi

      - name: InSpec compliance check
        run: |
          inspec exec https://github.com/dev-sec/linux-baseline \
            -t docker://$(docker create myapp:${{ github.sha }}) \
            --reporter json:inspec-results.json || true

          # Verificare che il punteggio sia >= 80%
          TOTAL=$(jq '.profiles[].controls | length' inspec-results.json)
          PASSED=$(jq '[.profiles[].controls[].results[].status] | map(select(. == "passed")) | length' inspec-results.json)
          SCORE=$((PASSED * 100 / TOTAL))

          echo "InSpec score: ${SCORE}%"
          if [ "$SCORE" -lt 80 ]; then
            echo "FAIL: Score $SCORE% sotto soglia 80%"
            exit 1
          fi
```

### 14.3 Gate per infrastruttura (Terraform + compliance)

```hcl
# Checkov per IaC compliance
# checkov -d ./terraform --framework terraform --check CIS

# tfsec per security scanning
# tfsec ./terraform --format json --out tfsec-results.json
```

```yaml
# Pipeline con gate IaC
infra-compliance:
  stage: validate
  script:
    # Checkov — CIS per cloud resources
    - checkov -d ./terraform --framework terraform --compact --quiet
      --check CKV_AWS_18,CKV_AWS_19,CKV_AWS_21,CKV_AWS_24
      --hard-fail-on HIGH,CRITICAL

    # tfsec — Security misconfigurations
    - tfsec ./terraform --minimum-severity HIGH --exclude-downloaded-modules

    # Conftest — Policy-as-code con OPA
    - conftest test ./terraform --policy ./policy/ --all-namespaces
  allow_failure: false
```

### 14.4 Gate pre-deployment con Ansible

```yaml
# playbooks/pre-deploy-compliance-gate.yml
---
- name: Compliance gate pre-deployment
  hosts: "{{ target_hosts }}"
  become: true
  gather_facts: true

  vars:
    min_compliance_score: 80
    required_services:
      - auditd
      - sshd
      - firewalld
    blocked_packages:
      - telnet-server
      - rsh-server
      - tftp-server

  tasks:
    - name: Verificare servizi di sicurezza attivi
      ansible.builtin.service_facts:

    - name: Assert servizi richiesti running
      ansible.builtin.assert:
        that:
          - "item + '.service' in ansible_facts.services"
          - "ansible_facts.services[item + '.service']['state'] == 'running'"
        fail_msg: "GATE FAIL: servizio {{ item }} non attivo"
      loop: "{{ required_services }}"

    - name: Verificare pacchetti bloccati non installati
      ansible.builtin.package_facts:

    - name: Assert pacchetti bloccati assenti
      ansible.builtin.assert:
        that:
          - "item not in ansible_facts.packages"
        fail_msg: "GATE FAIL: pacchetto {{ item }} installato"
      loop: "{{ blocked_packages }}"

    - name: Eseguire scansione Lynis rapida
      ansible.builtin.command: lynis audit system --quick --no-colors
      register: lynis_scan
      changed_when: false

    - name: Estrarre Hardening Index
      ansible.builtin.shell: grep "hardening_index" /var/log/lynis-report.dat | cut -d= -f2
      register: hardening_index
      changed_when: false

    - name: Assert compliance score minimo
      ansible.builtin.assert:
        that:
          - "hardening_index.stdout | int >= min_compliance_score"
        fail_msg: "GATE FAIL: Hardening Index {{ hardening_index.stdout }}% < {{ min_compliance_score }}%"
        success_msg: "GATE PASS: Hardening Index {{ hardening_index.stdout }}%"

    - name: Verificare nessun utente UID 0 non autorizzato
      ansible.builtin.shell: awk -F':' '$3 == 0 && $1 != "root" {print $1}' /etc/passwd
      register: uid0_users
      changed_when: false

    - name: Assert no UID 0 non autorizzati
      ansible.builtin.assert:
        that:
          - "uid0_users.stdout == ''"
        fail_msg: "GATE FAIL: utenti non-root con UID 0: {{ uid0_users.stdout }}"

    - name: Gate superato
      ansible.builtin.debug:
        msg: "Compliance gate SUPERATO per {{ ansible_fqdn }} — deployment autorizzato"
```

### 14.5 Policy-as-Code con OPA/Rego

```rego
# policy/linux-compliance.rego
package linux.compliance

# Negare deployment se SSH permette root login
deny[msg] {
  input.sshd_config.PermitRootLogin != "no"
  msg := "PermitRootLogin deve essere 'no'"
}

# Negare deployment se password authentication e' abilitata
deny[msg] {
  input.sshd_config.PasswordAuthentication != "no"
  msg := "PasswordAuthentication deve essere 'no'"
}

# Negare deployment se auditd non e' attivo
deny[msg] {
  input.services.auditd.state != "running"
  msg := "auditd deve essere in esecuzione"
}

# Negare deployment se hardening index sotto soglia
deny[msg] {
  input.hardening_index < 80
  msg := sprintf("Hardening Index %d%% sotto soglia 80%%", [input.hardening_index])
}

# Negare deployment se CVE critiche non patchate
deny[msg] {
  count(input.vulnerabilities.critical) > 0
  msg := sprintf("%d CVE critiche non patchate", [count(input.vulnerabilities.critical)])
}
```

---

## 15. Troubleshooting

### Problema 1: OpenSCAP segnala FAIL su `sshd_disable_root_login` ma PermitRootLogin e' gia' "no"

**Sintomo**: `oscap xccdf eval` riporta FAIL per la regola `xccdf_org.ssgproject.content_rule_sshd_disable_root_login` nonostante `/etc/ssh/sshd_config` contenga `PermitRootLogin no`.

**Causa**: il parametro e' impostato in un file drop-in in `/etc/ssh/sshd_config.d/` che viene processato prima o dopo la direttiva nel file principale. OpenSCAP verifica solo il file principale.

**Fix**:
```bash
# Verificare configurazione effettiva
sshd -T | grep permitrootlogin

# Se il drop-in sovrascrive il file principale, spostare la direttiva
# nel drop-in con priorita' alta
echo "PermitRootLogin no" > /etc/ssh/sshd_config.d/99-hardening.conf

# Aggiornare il content SCAP se disponibile una versione piu' recente
sudo dnf update scap-security-guide
```

### Problema 2: Remediation OpenSCAP disabilita PasswordAuthentication e blocca accesso LDAP

**Sintomo**: dopo l'applicazione dello script di remediation CIS, gli utenti LDAP non riescono piu' ad autenticarsi via SSH.

**Causa**: la rule `sshd_disable_password_authentication` imposta `PasswordAuthentication no`, ma gli utenti LDAP usano password authentication (non SSH key).

**Fix**:
```bash
# 1. Ripristinare accesso (da console o out-of-band)
sed -i 's/^PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
systemctl restart sshd

# 2. Creare tailoring file che esclude la rule
# (vedi sezione 2.7)

# 3. Documentare waiver con controllo compensativo
# Controllo compensativo: fail2ban + MFA via PAM
```

### Problema 3: Lynis Hardening Index cala dopo aggiornamento del sistema

**Sintomo**: dopo `dnf update`, il Hardening Index scende di 5-10 punti.

**Causa**: l'aggiornamento ha resettato file di configurazione (es. sshd_config, auditd.conf) ai valori di default del pacchetto.

**Fix**:
```bash
# Verificare quali file sono stati modificati dall'aggiornamento
rpm -V openssh-server    # RHEL
dpkg -V openssh-server   # Debian

# Riapplicare hardening sui file resettati
ansible-playbook cis-hardening.yml --tags ssh

# Prevenzione: usare file drop-in invece di modificare il file principale
# /etc/ssh/sshd_config.d/99-hardening.conf (non viene sovrascritto da aggiornamenti)
```

### Problema 4: CIS-CAT score non corrisponde a OpenSCAP per lo stesso benchmark

**Sintomo**: CIS-CAT Pro da' 87% e OpenSCAP da' 78% sullo stesso server per il CIS Benchmark Level 1.

**Causa**: versioni diverse del benchmark, interpretazioni diverse dei test, o timing diverso dei check. CIS-CAT usa il benchmark ufficiale CIS; OpenSCAP usa il progetto SCAP Security Guide (SSG) che e' un'implementazione community del CIS.

**Fix**:
```bash
# Verificare le versioni
# CIS-CAT: controllare la versione del benchmark nella CLI
/opt/cis-cat/Assessor-CLI.sh --list-benchmarks

# OpenSCAP: verificare versione SSG
rpm -q scap-security-guide

# Confrontare le regole: estrarre lista regole da entrambi
oscap info --profiles /usr/share/xml/scap/ssg/content/ssg-rhel9-ds.xml

# Usare lo stesso strumento per trend interni; usare entrambi per cross-validation
```

### Problema 5: InSpec fallisce con "Could not determine platform" su container

**Sintomo**: `inspec exec profile/ -t docker://container_id` restituisce errore sulla piattaforma.

**Causa**: il container non ha `/etc/os-release` o il comando `uname` non e' disponibile (immagine distroless o scratch).

**Fix**:
```bash
# Specificare la piattaforma manualmente
inspec exec profile/ -t docker://container_id --platform-name=ubuntu --platform-release=22.04

# Oppure aggiungere al profilo un fallback
# inspec.yml:
# supports:
#   - platform-family: linux
```

### Problema 6: Ansible compliance playbook fallisce con "Timeout waiting for privilege escalation"

**Sintomo**: il playbook di hardening va in timeout su `become: true` quando eseguito su molti host.

**Causa**: la remediation di una regola precedente ha modificato la configurazione sudo, imponendo un TTY che Ansible non fornisce via pipelining.

**Fix**:
```yaml
# ansible.cfg
[defaults]
pipelining = True

[privilege_escalation]
become_flags = -H -S   # Non richiedere TTY

# Oppure: escludere la rule che modifica sudoers requiretty
# nel ruolo ansible-lockdown
rhel9cis_rule_5_3_7: false   # Disabilitare requiretty enforcement
```

### Problema 7: auditd si ferma e non riparte dopo remediation STIG

**Sintomo**: `systemctl status auditd` mostra `failed`, il log riporta "Error: too many rules".

**Causa**: lo script di remediation STIG ha aggiunto centinaia di regole auditd che superano il buffer del kernel.

**Fix**:
```bash
# Verificare numero regole
auditctl -l | wc -l

# Aumentare il buffer se necessario
auditctl -b 8192

# Configurare permanentemente
echo "-b 8192" > /etc/audit/rules.d/00-buffer.rules

# Oppure: consolidare regole ridondanti
# Molte regole STIG possono essere combinate con wildcard
```

### Problema 8: OpenSCAP OVAL scan consuma tutta la RAM

**Sintomo**: la scansione OVAL per vulnerabilita' causa OOM killer su server con < 2GB RAM.

**Causa**: i file OVAL definition per RHEL possono essere molto grandi (>50MB XML) e oscap li carica interamente in memoria.

**Fix**:
```bash
# Limitare la memoria con cgroup
systemd-run --scope -p MemoryMax=1G oscap oval eval --results /tmp/oval.xml rhel-9.oval.xml

# Oppure: usare Trivy per vulnerability scanning (piu' efficiente in memoria)
trivy rootfs --severity HIGH,CRITICAL /
```

### Problema 9: Falso positivo su "Ensure AIDE is installed" quando si usa alternativa

**Sintomo**: CIS check "1.3.1 Ensure AIDE is installed" fallisce, ma si usa OSSEC/Wazuh come alternativa per file integrity.

**Causa**: il check verifica letteralmente la presenza del pacchetto `aide`, non la funzionalita'.

**Fix**:
```bash
# Opzione 1: installare AIDE comunque (pochi KB)
sudo dnf install aide

# Opzione 2: creare waiver documentato
# Il check CIS 1.3.1 verifica la presenza di un FIM.
# OSSEC/Wazuh fornisce funzionalita' equivalente.
# Documentare nel waiver con riferimento alla policy approvata.

# Opzione 3: se si usa OpenSCAP, creare tailoring file che esclude la rule
```

### Problema 10: kube-bench riporta FAIL su managed Kubernetes (EKS/AKS/GKE)

**Sintomo**: kube-bench su nodo worker EKS mostra molti FAIL per controlli del control plane.

**Causa**: kube-bench esegue i check del CIS Kubernetes Benchmark standard, ma su managed K8s il control plane e' gestito dal provider.

**Fix**:
```bash
# Usare il benchmark specifico per il provider
kube-bench run --targets node   # Solo worker node checks su managed K8s

# EKS-specifico
kube-bench run --benchmark eks-1.2.0

# Le regole del control plane (sezione 1.x) non si applicano a managed K8s.
# Documentare nel report.
```

### Problema 11: Scansione compliance rallenta il server in produzione

**Sintomo**: durante la scansione OpenSCAP settimanale, il server mostra latenza elevata e CPU al 100%.

**Causa**: oscap esegue centinaia di check in sequenza senza throttling.

**Fix**:
```bash
# Impostare nice + ionice
nice -n 19 ionice -c 3 oscap xccdf eval --profile $PROFILE $DS

# Limitare con cgroup
systemd-run --scope -p CPUQuota=25% -p IOWeight=10 \
  oscap xccdf eval --profile $PROFILE --results /tmp/results.xml $DS

# Eseguire in finestra di manutenzione o su snapshot/clone
```

### Problema 12: Conflitto tra rule CIS e applicazione specifica

**Sintomo**: la rule CIS 2.2.3 "Ensure DHCP Server is not installed" rimuove il pacchetto dhcpd, ma il server e' un DHCP server legittimo.

**Causa**: il profilo CIS e' pensato per server generici; i server con ruolo specifico richiedono tailoring.

**Fix**:
```bash
# Creare tailoring file per il ruolo specifico
# Ruolo: DHCP Server
# Escludere: CIS 2.2.3 (DHCP), CIS 2.2.5 (DNS se anche DNS server)

# Documentare nel waiver:
# - Ruolo del server
# - Regola esclusa e motivazione
# - Controlli compensativi (firewall, segmentazione, monitoring)
```

### Problema 13: Ansible remediation modifica file ma il servizio non ricarica

**Sintomo**: il playbook modifica `/etc/ssh/sshd_config` ma `sshd -T` mostra ancora i vecchi valori.

**Causa**: il task Ansible modifica il file ma manca il handler per ricaricare il servizio.

**Fix**:
```yaml
# Assicurarsi che il task notifichi l'handler
- name: Set PermitRootLogin
  ansible.builtin.lineinfile:
    path: /etc/ssh/sshd_config
    regexp: '^PermitRootLogin'
    line: 'PermitRootLogin no'
  notify: Reload sshd   # <-- handler mancante

handlers:
  - name: Reload sshd
    ansible.builtin.service:
      name: sshd
      state: reloaded
```

### Problema 14: Trivy riporta CVE in pacchetti base dell'immagine che non sono aggiornabili

**Sintomo**: Trivy segnala CVE critiche in `libc6` nell'immagine `ubuntu:22.04`, ma non esistono fix upstream.

**Causa**: alcune CVE hanno fix rilasciati solo per versioni piu' recenti della distribuzione, o sono disputed/contested.

**Fix**:
```bash
# Verificare se il fix e' disponibile
trivy image --ignore-unfixed ubuntu:22.04

# Creare file .trivyignore per CVE note senza fix
echo "CVE-2023-XXXXX" >> .trivyignore

# Verificare stato effettivo della CVE
# Consultare il tracker della distribuzione:
# Ubuntu: https://ubuntu.com/security/cves
# RHEL: https://access.redhat.com/security/cve/
```

### Problema 15: AIDE genera falsi allarmi dopo aggiornamenti legittimi

**Sintomo**: dopo `apt upgrade`, AIDE segnala centinaia di file modificati in `/usr/`.

**Causa**: AIDE non distingue tra aggiornamenti legittimi e modifiche non autorizzate.

**Fix**:
```bash
# Procedura corretta dopo aggiornamento:
# 1. Eseguire aggiornamento
apt upgrade -y

# 2. Verificare con AIDE (aspettarsi le differenze)
aide --check | tee /tmp/aide-post-update.txt

# 3. Verificare che le differenze siano coerenti con i pacchetti aggiornati
dpkg -l --no-pager | grep "^ii" > /tmp/installed-packages.txt

# 4. Aggiornare baseline AIDE
aide --update
mv /var/lib/aide/aide.db.new /var/lib/aide/aide.db

# 5. Documentare l'aggiornamento nel change log
```

### Problema 16: Score compliance oscilla tra scansioni consecutive senza modifiche

**Sintomo**: due scansioni OpenSCAP a distanza di minuti danno score diversi (es. 82% e 79%).

**Causa**: alcune rule dipendono dallo stato runtime (processi in esecuzione, connessioni attive, mount temporanei) che puo' variare.

**Fix**:
```bash
# Identificare le regole con risultati oscillanti
diff <(grep 'result=' scan1-results.xml | sort) <(grep 'result=' scan2-results.xml | sort)

# Tipiche rule oscillanti:
# - Check su processi (un cron job puo' essere in esecuzione o no)
# - Check su mount temporanei
# - Check su porte (servizio in fase di restart)

# Escludere rule oscillanti dal calcolo dello score
# oppure eseguire sempre in condizioni controllate (no cron attivi)
```

---

## 16. FAQ

### Q1: Quale strumento di compliance dovrei usare come primo approccio?

**R**: Dipende dal contesto:
- **Server generici in azienda**: OpenSCAP con profilo CIS Level 1. E' gratuito, ben mantenuto, e produce report in formato standard.
- **Startup SaaS senza compliance specifica**: Lynis. E' agnostico rispetto ai framework, facile da integrare, e il Hardening Index da' un feedback immediato.
- **Compliance-as-code, team DevOps**: InSpec. Si integra nativamente in CI/CD, i profili sono testabili, e la community dev-sec.io e' eccellente.
- **Ambiente DoD/governo**: OpenSCAP con profilo STIG. E' lo standard de facto.

### Q2: CIS Level 1 o Level 2? Quando usare quale?

**R**: Level 1 e' sufficiente per la maggior parte degli ambienti. Level 2 aggiunge controlli che possono interferire con applicazioni legittime (es. disabilitare IPv6, SELinux enforcing su tutto). Usare Level 2 su server ad alta criticita' (database con dati PCI, server con PHI) dopo aver testato in staging.

### Q3: Come gestire i falsi positivi senza ignorarli permanentemente?

**R**: Tre approcci, in ordine di preferenza:
1. **Tailoring file** (OpenSCAP): disabilitare la specifica rule nel profilo. Versionare il tailoring file in Git.
2. **Waiver file** (InSpec/Chef): documentare la giustificazione con data di scadenza. Il test viene eseguito ma il risultato non blocca.
3. **Esclusione nel profilo Lynis**: `skip-test=XXXX` nel file `.prf`. Documentare nel commento.

In tutti i casi, il waiver deve avere: approvatore, data, scadenza, e controllo compensativo.

### Q4: Ogni quanto devo eseguire le scansioni di compliance?

**R**: Almeno settimanalmente con scansione completa. Per ambienti PCI-DSS o con requisiti di continuous monitoring (NIS2, SOC 2), giornalmente o ad ogni change via CI/CD. La drift detection (AIDE, osquery) deve essere continua (intervalli da 5 minuti a 1 ora).

### Q5: Come integro compliance scanning con il mio SIEM?

**R**: Ogni strumento produce output strutturato che puo' essere inoltrato al SIEM:
- **OpenSCAP**: risultati XML/ARF → parser specifico o conversione JSON
- **Lynis**: `/var/log/lynis-report.dat` → parser line-based
- **InSpec**: output JSON nativo con `--reporter json`
- **kube-bench**: output JSON con `--json`
- **Wazuh**: ha integrazione nativa con OpenSCAP e SCA (Security Configuration Assessment)

### Q6: Come gestire la compliance su immutable infrastructure?

**R**: Spostare il compliance check nel pipeline di build dell'immagine:
1. Build golden image (Packer/Image Builder)
2. Compliance scan dell'immagine (InSpec con target Docker o chroot)
3. Gate: bloccare l'immagine se non conforme
4. Deploy: solo immagini che hanno passato il gate
5. Runtime: verificare che l'istanza usi l'immagine approvata (no drift possibile)

### Q7: OpenSCAP o Lynis? Quando usare quale?

**R**: Non sono mutualmente esclusivi. OpenSCAP e' lo standard per compliance formale (audit, certificazioni): produce risultati in formato SCAP, supporta profili ufficiali CIS/STIG, e genera remediation script. Lynis e' migliore per hardening operativo quotidiano: e' piu' veloce, il Hardening Index e' un KPI immediato, e i suggerimenti sono pragmatici. Usare entrambi: OpenSCAP per audit, Lynis per monitoring continuo.

### Q8: Come gestire la compliance in ambienti multi-distribuzione?

**R**: Usare un livello di astrazione:
- **Ansible**: i ruoli ansible-lockdown gestiscono le differenze tra distribuzioni
- **InSpec**: i profili community (dev-sec/linux-baseline) sono cross-distribution
- **OpenSCAP**: ha datastream separati per ogni distro — eseguire il datastream corretto per ogni host

Centralizzare il reporting con un dashboard che normalizza i risultati.

### Q9: Quanto tempo richiede un progetto di compliance da zero a "production-ready"?

**R**: Tempistiche realistiche:
- **Settimana 1-2**: Assessment iniziale con Lynis/OpenSCAP, identificazione gap
- **Settimana 3-4**: Remediation dei finding critici e alti
- **Settimana 5-6**: Automazione (Ansible playbook, cron scan, alerting)
- **Settimana 7-8**: Drift detection, CI/CD gates, reporting
- **Mese 3+**: Tuning falsi positivi, waiver management, audit preparation

Per CIS Level 1 su un ambiente omogeneo, 6-8 settimane. Per STIG o PCI-DSS, 3-6 mesi.

### Q10: Posso usare la compliance scanning come sostituto del penetration testing?

**R**: No. Sono complementari ma rispondono a domande diverse:
- **Compliance scanning**: "Il sistema e' configurato secondo lo standard X?" (preventivo, deterministico)
- **Penetration testing**: "Un attaccante puo' compromettere il sistema?" (offensivo, creativo)

Un sistema 100% compliant CIS Level 2 puo' avere vulnerabilita' applicative, misconfiguration custom, o attacchi supply chain non coperti dal benchmark. Compliance e' necessaria ma non sufficiente.

### Q11: Come automatizzare la compliance per auto-scaling groups?

**R**: Due approcci:
1. **Bake compliance nell'AMI/immagine**: hardening durante il build dell'immagine, compliance gate prima della pubblicazione. Le nuove istanze nascono gia' conformi.
2. **Bootstrap compliance al launch**: user-data script che esegue Ansible hardening al primo boot. Piu' flessibile ma introduce una finestra temporale di non-conformita'.

Il primo approccio e' preferibile per immutable infrastructure. Aggiungere una scansione periodica per verificare che nessun drift sia avvenuto post-launch.

### Q12: Come gestire la compliance durante incident response?

**R**: Durante un incidente, la compliance e' secondaria rispetto al contenimento. Tuttavia:
- Documentare ogni deviazione dalla baseline di compliance effettuata durante l'IR
- Al termine dell'incidente, riportare il sistema alla baseline
- Se le deviazioni hanno rivelato gap nel processo di compliance, aggiornare policy e profili
- Non disabilitare mai logging o auditing durante un incidente

### Q13: Quali sono i costi nascosti della compliance automation?

**R**:
- **Manutenzione profili**: i benchmark vengono aggiornati trimestralmente; i profili tailored devono essere rivalutati
- **Falsi positivi**: ogni falso positivo richiede investigazione e potenzialmente un waiver
- **Competenze**: il team deve comprendere sia lo strumento sia il framework di compliance
- **Storage**: i report occupano spazio; retention 12 mesi per PCI-DSS, piu' a lungo per altri framework
- **Performance**: le scansioni consumano CPU/IO; pianificare in finestre di basso traffico

### Q14: InSpec o OpenSCAP per compliance-as-code?

**R**: InSpec ha una curva di apprendimento piu' bassa per sviluppatori (Ruby DSL leggibile). OpenSCAP e' piu' formale (XML) ma produce output riconosciuti da auditor. Per team DevOps, InSpec. Per compliance officer, OpenSCAP. In ambienti maturi, entrambi: InSpec in CI/CD, OpenSCAP per audit formali.

### Q15: Come gestire la compliance per edge/IoT Linux?

**R**: Le sfide specifiche sono: risorse limitate, connettivita' intermittente, aggiornamenti difficili.
- Usare Lynis (leggero, ~2MB) invece di OpenSCAP (pesante)
- Eseguire scansioni locali e inviare solo il report (JSON compatto) quando online
- Usare profili CIS ridotti (solo rule applicabili a embedded)
- Preferire immutable rootfs (dm-verity, read-only root) per eliminare il drift alla radice

### Q16: NIS2 richiede strumenti specifici? Quali sono i requisiti tecnici minimi?

**R**: NIS2 non prescrive strumenti specifici, ma richiede dimostrabilita'. Per soddisfare i requisiti:
- Art. 21(2)(a): scansione periodica con reportistica tracciabile (OpenSCAP + report archiviati)
- Art. 21(2)(b): logging centralizzato + playbook di incident response testati
- Art. 21(2)(d): SBOM (Software Bill of Materials) per ogni servizio
- Art. 21(2)(e): compliance gate in CI/CD
- Art. 21(2)(g): hardening automatizzato con evidenza di esecuzione

La chiave e' l'evidenza: ogni controllo deve produrre un artefatto verificabile dall'autorita' competente.

---

## 17. Guida all'implementazione da zero

### Fase 1: Assessment iniziale (Settimana 1-2)

```bash
# 1. Inventario sistemi
ansible all -m setup -a 'filter=ansible_distribution*' -i inventory.yml > /tmp/inventory.json

# 2. Prima scansione Lynis (veloce, non invasiva)
ansible all -m command -a 'lynis audit system --quick --no-colors' -i inventory.yml

# 3. Prima scansione OpenSCAP (completa)
ansible all -m command -a 'oscap xccdf eval --profile cis_server_l1 --results /tmp/initial-scan.xml /usr/share/xml/scap/ssg/content/ssg-rhel9-ds.xml' -i inventory.yml

# 4. Raccogliere risultati
ansible all -m fetch -a 'src=/tmp/initial-scan.xml dest=./results/' -i inventory.yml
ansible all -m fetch -a 'src=/var/log/lynis-report.dat dest=./results/' -i inventory.yml

# 5. Generare report aggregato
python3 scripts/aggregate-results.py ./results/ > initial-assessment.html
```

### Fase 2: Prioritizzazione e planning (Settimana 2)

```markdown
# Matrice di prioritizzazione

| Priorita' | Tipo finding | Azione | Timeline |
|-----------|-------------|--------|----------|
| P0 | CVE critiche (CVSS >= 9.0) | Patch immediata | 48 ore |
| P0 | CAT I STIG / CIS rule con impatto sicurezza diretto | Remediation immediata | 1 settimana |
| P1 | CVE alte (CVSS 7.0-8.9) | Patch programmata | 2 settimane |
| P1 | CAT II STIG / CIS L1 majority failures | Remediation programmata | 2 settimane |
| P2 | CVE medie + CIS L1 remaining failures | Sprint successivo | 4 settimane |
| P3 | CIS L2 / suggerimenti Lynis | Backlog | Quando possibile |

# Waiver per regole non applicabili
# Documentare immediatamente le regole che richiedono waiver.
```

### Fase 3: Remediation (Settimana 3-6)

```yaml
# 1. Testare in staging
ansible-playbook cis-hardening.yml -i staging-inventory.yml --check --diff

# 2. Applicare in staging
ansible-playbook cis-hardening.yml -i staging-inventory.yml

# 3. Verificare in staging
ansible-playbook compliance-check.yml -i staging-inventory.yml

# 4. Canary in produzione (1 server per gruppo)
ansible-playbook cis-hardening.yml -i prod-inventory.yml --limit canary_servers

# 5. Verifica canary
ansible-playbook compliance-check.yml -i prod-inventory.yml --limit canary_servers

# 6. Rollout completo (dopo approvazione)
ansible-playbook cis-hardening.yml -i prod-inventory.yml
```

### Fase 4: Automazione (Settimana 5-8)

```bash
# 1. Configurare scansione periodica
# /etc/cron.d/compliance-scan
0 3 * * 0  root  /opt/scripts/oscap-weekly-scan.sh
0 4 * * *  root  /opt/scripts/lynis-daily-scan.sh
0 */6 * * *  root  aide --check

# 2. Configurare drift detection
# osquery con pack compliance attivo
# AIDE con check giornaliero
# Git-based config tracking

# 3. Configurare alerting
# Soglie:
# - Score < 80%: WARNING via email
# - Score < 70%: CRITICAL via PagerDuty/Slack
# - Drift detection: ALERT immediato

# 4. Configurare CI/CD gates
# - Compliance scan su ogni build di immagine
# - Gate pre-deployment su target server
# - Scan post-deployment di verifica
```

### Fase 5: Continuous improvement (Mese 3+)

```markdown
1. Revisione mensile:
   - Trend compliance score (deve salire o restare stabile)
   - Nuovi finding da aggiornamenti benchmark
   - Waiver in scadenza da rinnovare o risolvere

2. Revisione trimestrale:
   - Aggiornamento benchmark CIS/STIG (nuove versioni)
   - Aggiornamento profili tailored
   - Revisione falsi positivi accumulati
   - Test di efficacia delle remediation

3. Revisione annuale:
   - Allineamento con nuovi requisiti normativi (NIS2 updates, PCI-DSS changes)
   - Valutazione nuovi strumenti
   - Formazione team su novita'
```

---

## 18. Checklist template

### 18.1 Checklist pre-audit

```markdown
# Checklist Pre-Audit di Compliance

## Preparazione documentale
- [ ] Inventario aggiornato di tutti i sistemi Linux in scope
- [ ] Matrice di responsabilita' (chi gestisce cosa)
- [ ] Policy di sicurezza documentata e approvata
- [ ] Procedura di gestione degli accessi documentata
- [ ] Piano di patch management documentato
- [ ] Piano di backup e recovery testato

## Scansioni eseguite
- [ ] OpenSCAP scan con profilo appropriato (CIS/STIG/PCI-DSS)
- [ ] Lynis audit system su tutti gli host
- [ ] Vulnerability scan (OVAL/Trivy/Nessus) su tutti gli host
- [ ] AIDE check recente (< 24 ore)
- [ ] kube-bench (se Kubernetes in scope)
- [ ] Docker Bench (se container in scope)

## Evidenze raccolte
- [ ] Report compliance in formato HTML/PDF per ogni host
- [ ] Log di remediation applicata (con date)
- [ ] Waiver approvati e documentati con controlli compensativi
- [ ] Log di accesso centralizzati (ultimi 12 mesi per PCI-DSS)
- [ ] Evidenza di patching regolare
- [ ] Configurazione firewall documentata

## Stato servizi di sicurezza
- [ ] auditd attivo e configurato su tutti gli host
- [ ] rsyslog/journald con forwarding attivo
- [ ] AIDE/OSSEC/Wazuh file integrity monitoring attivo
- [ ] Firewall (iptables/nftables/firewalld) attivo
- [ ] SELinux/AppArmor in enforcing mode
- [ ] Antimalware attivo (se richiesto dal framework)

## Accesso e autenticazione
- [ ] PermitRootLogin no su tutti i server
- [ ] Password policy conforme (lunghezza, complessita', scadenza)
- [ ] MFA attivo per accesso remoto privilegiato
- [ ] SSH key-based authentication preferita
- [ ] Nessun utente con UID 0 diverso da root
- [ ] Account di servizio con shell /sbin/nologin

## Rete
- [ ] Firewall configurato con default deny
- [ ] Porte non necessarie chiuse
- [ ] TLS 1.2+ su tutti i servizi
- [ ] Segmentazione di rete verificata
```

### 18.2 Checklist hardening Linux CIS L1

```markdown
# Checklist Hardening CIS Level 1 — Linux Server

## 1. Initial Setup
- [ ] 1.1.1.x — Filesystem non necessari disabilitati (cramfs, freevxfs, jffs2, hfs, hfsplus, udf)
- [ ] 1.1.2-5 — /tmp montato come partizione separata con noexec,nosuid,nodev
- [ ] 1.1.6 — /dev/shm con noexec,nosuid,nodev
- [ ] 1.3.1 — AIDE installato e inizializzato
- [ ] 1.3.2 — AIDE check periodico (cron)
- [ ] 1.4.1 — Bootloader password configurata
- [ ] 1.5.1 — core dump limitati
- [ ] 1.5.3 — ASLR abilitato
- [ ] 1.6.x — SELinux/AppArmor in enforcing mode

## 2. Services
- [ ] 2.1.x — Servizi inetd/xinetd rimossi
- [ ] 2.2.x — Servizi non necessari disabilitati (avahi, cups, dhcpd, slapd, nfs, bind, vsftpd, httpd, dovecot, smb, squid, snmpd, rsyncd)
- [ ] 2.3.x — Client non necessari rimossi (nis, rsh, talk, telnet, ldap-utils)

## 3. Network Configuration
- [ ] 3.1.1 — IPv6 disabilitato (se non usato)
- [ ] 3.2.x — Parametri rete sicuri (no IP forwarding, no source routing, no ICMP redirect)
- [ ] 3.3.x — IPv6 parametri sicuri
- [ ] 3.4.x — Firewall attivo e configurato
- [ ] 3.5.x — Wireless disabilitato (se non necessario)

## 4. Logging and Auditing
- [ ] 4.1.1 — auditd installato e attivo
- [ ] 4.1.2 — auditd service abilitato
- [ ] 4.1.3+ — Regole audit per: login/logout, session init, date/time, MAC, network, file deletion, sudoers, kernel module loading
- [ ] 4.2.1 — rsyslog configurato
- [ ] 4.2.2 — journald configurato
- [ ] 4.2.3 — Log permissions corretti

## 5. Access, Authentication, and Authorization
- [ ] 5.1.x — Cron access ristretto
- [ ] 5.2.x — SSH hardened (PermitRootLogin no, MaxAuthTries 4, Protocol 2, LogLevel INFO, X11Forwarding no, MaxStartups, LoginGraceTime 60)
- [ ] 5.3.x — PAM configurato (password quality, lockout, password reuse)
- [ ] 5.4.x — Shadow password suite (PASS_MAX_DAYS 365, PASS_MIN_DAYS 1, PASS_WARN_AGE 7, INACTIVE 30)
- [ ] 5.5 — Root login ristretto a console

## 6. System Maintenance
- [ ] 6.1.x — Permessi file di sistema (passwd 644, shadow 640, group 644, gshadow 640)
- [ ] 6.2.x — User and Group Settings (no UID 0 duplicati, no home dir assenti, no .forward files)
```

### 18.3 Checklist CI/CD compliance gate

```markdown
# Checklist Compliance Gate CI/CD

## Gate build-time (immagine/artefatto)
- [ ] Vulnerability scan con soglia (no CRITICAL, max 5 HIGH)
- [ ] Secret detection (no credenziali nel codice)
- [ ] License compliance (no licenze incompatibili)
- [ ] SBOM generato e archiviato
- [ ] Immagine base approvata (da registry interno)
- [ ] Utente non-root nel Dockerfile
- [ ] HEALTHCHECK definito

## Gate pre-deployment (target server)
- [ ] Compliance score >= soglia (es. 80%)
- [ ] Servizi di sicurezza attivi (auditd, firewall, HIDS)
- [ ] No CVE critiche non patchate
- [ ] Nessun drift dalla baseline
- [ ] Backup recente verificato
- [ ] Rollback plan documentato

## Gate post-deployment (verifica)
- [ ] Servizio risponde correttamente
- [ ] No nuove porte aperte non previste
- [ ] Log funzionanti (verificare ingestion nel SIEM)
- [ ] Compliance scan post-deployment superato
- [ ] Nessun alert di sicurezza generato
```

### 18.4 Checklist waiver di compliance

```markdown
# Template Waiver di Compliance

## Informazioni generali
- **Data richiesta**: ___________
- **Richiedente**: ___________
- **Approvatore**: ___________
- **Data approvazione**: ___________

## Dettaglio
- **Rule ID**: ___________
- **Framework**: [ ] CIS [ ] STIG [ ] PCI-DSS [ ] HIPAA [ ] Altro: _________
- **Severita'**: [ ] Critical [ ] High [ ] Medium [ ] Low
- **Sistemi interessati**: ___________

## Giustificazione
- **Motivo dell'esclusione**: ___________
- **Impatto se applicata la rule**: ___________
- **Durata waiver**: dal ___________ al ___________

## Controlli compensativi
1. ___________
2. ___________
3. ___________

## Piano di risoluzione
- **La rule potra' essere applicata in futuro?** [ ] Si [ ] No
- **Se si, timeline stimata**: ___________
- **Azioni necessarie**: ___________

## Approvazioni
- [ ] Security Lead
- [ ] CISO (se severita' Critical/High)
- [ ] Compliance Officer (se framework regolamentare)

## Revisione
- **Data prossima revisione**: ___________
- **Responsabile revisione**: ___________
```

---

## 19. Glossario

| Termine | Definizione |
|---------|-------------|
| **AIDE** | Advanced Intrusion Detection Environment — strumento di file integrity monitoring che confronta lo stato attuale del filesystem con una baseline. |
| **ARF** | Asset Reporting Format — formato NIST per report di assessment standardizzati. |
| **Benchmark** | Insieme di regole di configurazione raccomandate per una specifica piattaforma (es. CIS Benchmark per RHEL 9). |
| **CAT I/II/III** | Categorie di severita' DISA STIG: CAT I (High), CAT II (Medium), CAT III (Low). |
| **CCE** | Common Configuration Enumeration — identificatore univoco per configurazioni di sicurezza. |
| **CIS** | Center for Internet Security — organizzazione che pubblica benchmark di hardening per OS, database, cloud. |
| **CIS-CAT** | CIS Configuration Assessment Tool — strumento ufficiale CIS per valutare conformita' ai CIS Benchmarks. |
| **Compliance drift** | Deviazione progressiva della configurazione dalla baseline di compliance approvata. |
| **Compliance gate** | Checkpoint in una pipeline CI/CD che blocca il deployment se i requisiti di compliance non sono soddisfatti. |
| **CPE** | Common Platform Enumeration — schema di naming standardizzato per piattaforme IT. |
| **CVE** | Common Vulnerabilities and Exposures — identificatore univoco per vulnerabilita' note. |
| **CVSS** | Common Vulnerability Scoring System — sistema di scoring per la severita' delle vulnerabilita'. |
| **CWE** | Common Weakness Enumeration — catalogo di debolezze software e hardware. |
| **Datastream** | File XML aggregato che contiene XCCDF, OVAL, e CPE in un singolo artefatto SCAP. |
| **DISA** | Defense Information Systems Agency — agenzia del DoD USA che pubblica gli STIG. |
| **Dry-run** | Esecuzione simulata di una remediation senza applicare modifiche effettive al sistema. |
| **FIM** | File Integrity Monitoring — monitoraggio continuo delle modifiche a file critici (AIDE, OSSEC, Wazuh). |
| **Hardening** | Processo di riduzione della superficie di attacco di un sistema tramite configurazione sicura. |
| **Hardening Index** | Punteggio numerico (0-100) prodotto da Lynis che indica il livello di hardening del sistema. |
| **HIDS** | Host-based Intrusion Detection System — sistema di rilevamento intrusioni basato sull'analisi dell'host. |
| **HIPAA** | Health Insurance Portability and Accountability Act — legge USA per la protezione dei dati sanitari. |
| **InSpec** | Framework di compliance-as-code di Chef/Progress che permette di scrivere test di compliance in Ruby DSL. |
| **ISO 27001** | Standard internazionale per i sistemi di gestione della sicurezza delle informazioni (ISMS). |
| **kube-bench** | Strumento Aqua Security per verificare la conformita' dei cluster Kubernetes al CIS Kubernetes Benchmark. |
| **Lynis** | Strumento di auditing e hardening open source per sistemi Linux/Unix sviluppato da CISOfy. |
| **NIS2** | Network and Information Security Directive 2 — direttiva UE per la cybersecurity delle infrastrutture critiche. |
| **NVD** | National Vulnerability Database — database USA di vulnerabilita' gestito dal NIST. |
| **OPA** | Open Policy Agent — motore di policy-as-code general purpose. |
| **OpenSCAP** | Implementazione open source del protocollo SCAP per la valutazione automatizzata della compliance. |
| **osquery** | Framework che espone lo stato del sistema operativo come database SQL interrogabile. |
| **OVAL** | Open Vulnerability and Assessment Language — linguaggio XML per definire test di vulnerabilita' e configurazione. |
| **PCI-DSS** | Payment Card Industry Data Security Standard — standard per la protezione dei dati delle carte di pagamento. |
| **PHI** | Protected Health Information — dati sanitari protetti secondo HIPAA. |
| **Profile** | Selezione di regole attive all'interno di un benchmark SCAP per uno specifico caso d'uso. |
| **Rego** | Linguaggio di policy di OPA (Open Policy Agent). |
| **Remediation** | Azione correttiva applicata a un sistema per risolvere un finding di compliance. |
| **SBOM** | Software Bill of Materials — inventario completo dei componenti software di un sistema. |
| **SCAP** | Security Content Automation Protocol — suite di specifiche NIST per la gestione automatizzata della sicurezza. |
| **SOC 2** | Service Organization Control Type 2 — framework di audit per service provider basato sui Trust Services Criteria. |
| **SSG** | SCAP Security Guide — progetto open source che fornisce contenuti SCAP per diverse distribuzioni Linux. |
| **STIG** | Security Technical Implementation Guide — guide di implementazione della sicurezza pubblicate da DISA. |
| **Tailoring** | Personalizzazione di un profilo SCAP senza modificare il datastream originale. |
| **Waiver** | Documento che giustifica l'esclusione temporanea di una specifica regola di compliance. |
| **XCCDF** | Extensible Configuration Checklist Description Format — formato XML per descrivere checklist di configurazione. |

---

## 20. Letture e riferimenti

### Standard e framework

- CIS Benchmarks: https://www.cisecurity.org/cis-benchmarks
- DISA STIG: https://public.cyber.mil/stigs/
- PCI-DSS v4.0.1: https://www.pcisecuritystandards.org/
- NIST SCAP: https://csrc.nist.gov/projects/security-content-automation-protocol
- NIS2 Directive: https://eur-lex.europa.eu/eli/dir/2022/2555

### Strumenti

- OpenSCAP: https://www.open-scap.org/
- SCAP Security Guide: https://github.com/ComplianceAsCode/content
- Lynis: https://cisofy.com/lynis/
- AIDE: https://aide.github.io/
- osquery: https://osquery.io/
- Chef InSpec: https://docs.chef.io/inspec/
- dev-sec.io: https://dev-sec.io/
- ansible-lockdown: https://github.com/ansible-lockdown
- kube-bench: https://github.com/aquasecurity/kube-bench
- Trivy: https://github.com/aquasecurity/trivy
- Docker Bench: https://github.com/docker/docker-bench-security
- OPA / Conftest: https://www.openpolicyagent.org/

### Cloud

- AWS SSM Compliance: https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-compliance.html
- Azure Guest Configuration: https://learn.microsoft.com/en-us/azure/governance/machine-configuration/
- GCP VM Manager: https://cloud.google.com/compute/docs/manage-os

---

## 21. Esercizi

### Lab 1 — OpenSCAP: scansione CIS e remediation

1. Installare openscap-scanner e scap-security-guide sulla propria distribuzione.
2. Elencare i profili disponibili con `oscap info`.
3. Eseguire una scansione CIS Level 1 con report HTML.
4. Generare uno script Bash di remediation per le sole regole fallite.
5. Revisionare lo script: identificare almeno 3 remediation potenzialmente pericolose.
6. Creare un tailoring file che escluda 2 regole non applicabili.
7. Rieseguire la scansione con il tailoring file e confrontare lo score.

### Lab 2 — Lynis + AIDE + alerting

1. Installare Lynis e eseguire un audit completo. Annotare l'Hardening Index.
2. Implementare almeno 5 suggerimenti di Lynis.
3. Rieseguire l'audit e verificare che l'Hardening Index sia aumentato.
4. Installare e inizializzare AIDE.
5. Modificare `/etc/ssh/sshd_config` e verificare che AIDE rilevi la modifica.
6. Creare uno script cron settimanale che esegue Lynis e invia un alert se l'HI scende sotto 70.
7. Configurare osquery con almeno 3 query di compliance (utenti UID 0, porte in ascolto, mount options).

### Lab 3 — InSpec: profilo di compliance personalizzato

1. Creare un profilo InSpec con almeno 10 controlli coprendo: SSH, filesystem, utenti, servizi, rete.
2. Eseguire il profilo sulla propria macchina e interpretare i risultati.
3. Aggiungere tag (cis, severity) a ogni controllo.
4. Eseguire il profilo su un container Docker.
5. Generare output in formato JSON e HTML.
6. Integrare il profilo in un Makefile o script CI che fallisce se lo score e' < 80%.

### Lab 4 — Ansible compliance automation

1. Installare il ruolo ansible-lockdown appropriato per la propria distribuzione.
2. Eseguire il playbook di hardening in `--check --diff` mode (dry-run).
3. Identificare 3 regole che richiedono waiver nel proprio ambiente.
4. Applicare il hardening su una VM di test.
5. Creare un playbook di compliance check (senza remediation) con almeno 10 verifiche.
6. Implementare il pattern canary: applicare la remediation a un solo host, verificare, poi a tutti.

### Lab 5 — CI/CD compliance gate

1. Creare un Dockerfile per un'applicazione web semplice.
2. Configurare Trivy per scansione dell'immagine con soglia: 0 CRITICAL, max 3 HIGH.
3. Aggiungere un check InSpec sull'immagine come gate nel pipeline.
4. Far fallire intenzionalmente il gate (es. aggiungere un pacchetto vulnerabile) e verificare che il pipeline si blocchi.
5. Correggere l'immagine e verificare che il gate passi.

### Lab 6 — Drift detection e remediation automatizzata

1. Stabilire una baseline con AIDE.
2. Configurare osquery con almeno 5 scheduled queries di compliance.
3. Creare uno script di drift detection basato su Git (vedi sezione 12.2).
4. Simulare un drift (modificare sshd_config manualmente).
5. Verificare che il drift venga rilevato da: AIDE, osquery, e lo script Git.
6. Creare un playbook Ansible che rileva il drift e lo corregge automaticamente (con dry-run e approvazione).

### Lab 7 (stretch) — Compliance dashboard end-to-end

1. Configurare un'istanza Elasticsearch + Grafana.
2. Integrare output di OpenSCAP, Lynis, e InSpec nel SIEM.
3. Creare una dashboard Grafana con: score per host, trend settimanale, top 10 failing rules.
4. Configurare alert su regressione dello score (calo > 5% in una settimana).
5. Generare un report HTML automatico settimanale per il team di security.
