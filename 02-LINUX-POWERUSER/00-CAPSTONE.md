# Capstone — Linux per Ingegneri di Sistema

> **Tempo stimato:** 40-60 ore in 4-6 settimane
> **Livello:** proficient → expert
> **Prerequisiti:** completamento di tutti i moduli del corso (Fasi 1-6)
> **Aggiornamento:** 2026-05-23

---

## Scenario

Sei l'unico system administrator di una startup che sta migrando la propria infrastruttura da un provider cloud gestito a server bare-metal dedicati. Il tuo compito è configurare un server Debian 12 production-grade che ospiterà servizi web interni, un database PostgreSQL e un sistema di monitoring. Il server deve essere hardened secondo lo standard CIS Benchmark Level 2, monitorato con uno stack di observability completo e documentato con runbook operativi.

---

## Deliverable

### D1 — Installazione e Storage (8-10 ore)

1. **Installazione Debian 12** su VM (o bare-metal se disponibile) con:
   - Root su ZFS con cifratura nativa (`encryption=aes-256-gcm`)
   - Auto-unlock via chiave su partizione separata (simulare TPM se non disponibile)
   - Layout ZFS: `rpool/ROOT/debian`, `rpool/var`, `rpool/var/log`, `rpool/home`
   - Snapshot policy automatizzata: orario (keep 24), giornaliero (keep 30), settimanale (keep 12)
   
2. **Partizioni separate** con mount option di sicurezza:
   - `/tmp` → `noexec,nosuid,nodev`
   - `/var/tmp` → `noexec,nosuid,nodev`
   - `/home` → `nosuid,nodev`
   - `/boot` → `ro` (remount rw solo per aggiornamenti kernel)

### D2 — Hardening CIS Benchmark Level 2 (10-12 ore)

1. **Applicazione CIS Benchmark Debian 12 Level 2** con documentazione di ogni eccezione:
   - Kernel: sysctl hardening (ASLR, ptrace_scope, dmesg_restrict, kptr_restrict)
   - Boot: GRUB2 password, Secure Boot (se UEFI)
   - Account: password policy via PAM pam_pwquality, faillock, UMASK 027
   - SSH: AllowGroups, MaxAuthTries 3, PermitRootLogin no, PubkeyOnly
   - Audit: auditd con regole per syscall critiche, file integrity, command logging
   
2. **SELinux** (se RHEL/CentOS) o **AppArmor** (se Debian) in enforcing mode con profili per:
   - nginx
   - PostgreSQL
   - Prometheus/Grafana
   
3. **Firewall nftables** con:
   - Policy DROP default
   - SSH limitato a rete management
   - HTTP/HTTPS aperti (con rate limiting)
   - PostgreSQL solo da localhost e rete applicativa
   - Monitoring (9090, 3000) solo da rete management
   - Kill switch per VPN (se configurata)

4. **Scansione automatizzata**:
   - Lynis: score ≥ 85
   - AIDE: database inizializzato, check giornaliero
   - osquery: query schedule per SUID, listening ports, user activity

### D3 — Servizi (8-10 ore)

1. **Nginx** come reverse proxy:
   - TLS 1.3 con certificati Let's Encrypt (o self-signed per lab)
   - OCSP stapling
   - Security headers (CSP, HSTS, X-Frame-Options)
   - Rate limiting per-IP
   - Proxy verso applicazione interna (porta 8080)
   
2. **PostgreSQL 16** hardened:
   - `pg_hba.conf`: solo connessioni SSL, no trust
   - Utente dedicato per ogni applicazione (minimo privilegio)
   - WAL archiving configurato
   - Backup automatizzato con pg_basebackup + WAL shipping
   - Monitoring con pg_stat_statements
   
3. **Servizio systemd** custom per un'applicazione di esempio:
   - Unit hardened (ProtectSystem=strict, PrivateTmp, NoNewPrivileges, CapabilityBoundingSet)
   - Logging strutturato via journald
   - Health check con systemd watchdog

### D4 — Observability Stack (8-10 ore)

1. **Prometheus** con:
   - node_exporter su tutti i servizi monitorati
   - postgres_exporter per metriche database
   - blackbox_exporter per probe HTTP/HTTPS
   - Recording rules per metriche derivate
   - Retention e storage sizing documentato
   
2. **Grafana** con:
   - Dashboard: host overview (USE method), PostgreSQL, Nginx, security
   - Provisioning automatizzato (datasource + dashboard YAML/JSON)
   - Alert rules per: disco >80%, CPU >90% sustained, servizi down, SSH login failure
   
3. **Alertmanager** con:
   - Routing: critical → email/webhook, warning → solo log
   - Inhibition: se host down, sopprimi alert specifici
   - Silencing documentato
   
4. **Loki + Promtail** (opzionale, per log aggregation):
   - Raccolta log da journald e file
   - Dashboard Grafana per log correlation

### D5 — Automazione e DR (4-6 ore)

1. **Ansible playbook** che riproduce l'intera configurazione:
   - Ruoli separati: base, hardening, nginx, postgres, monitoring
   - Vault per secret
   - Idempotente (eseguibile più volte senza effetti collaterali)
   
2. **Backup e DR**:
   - ZFS snapshot + send/recv verso storage remoto (o locale per lab)
   - PostgreSQL backup con retention (7 giornalieri, 4 settimanali)
   - Procedura documentata di restore testata
   
3. **Runbook operativo** con procedure per:
   - Sostituzione disco degradato (ZFS)
   - Restore PostgreSQL da backup
   - Rinnovo certificati TLS
   - Risposta a incidente sicurezza (playbook)
   - Aggiornamento kernel con rollback

### D6 — Documentazione e Demo (2-4 ore)

1. **Documento architetturale** con diagramma dell'infrastruttura
2. **Registro decisioni** (ADR): per ogni scelta non ovvia, perché è stata presa
3. **Demo live**: presentazione 15 minuti che mostra:
   - Stato del sistema (monitoring dashboard)
   - Simulazione failure (kill servizio, disco pieno) e recovery
   - Scansione di compliance (lynis score)
   - Verifica hardening (tentativo SSH fallito, port scan, nftables log)

---

## Rubric di Valutazione

| Area | Peso | Pass (70%) | Distinction (90%) |
|------|------|------------|-------------------|
| **Storage/ZFS** | 15% | ZFS funzionante con snapshot | ZFS encrypted + auto-unlock + retention policy |
| **Hardening** | 25% | CIS L1 applicato, Lynis ≥ 75 | CIS L2, Lynis ≥ 85, SELinux/AppArmor enforcing |
| **Servizi** | 15% | Nginx+PostgreSQL funzionanti | TLS hardened, systemd hardened, backup automatizzato |
| **Observability** | 20% | Prometheus+Grafana con dashboard base | Alert rules, Alertmanager routing, recording rules |
| **Automazione/DR** | 15% | Ansible playbook funzionante | Idempotente, vault, restore testato, runbook |
| **Documentazione** | 10% | Diagramma + procedure base | ADR, demo live, registro decisioni |

**Totale: 100%. Pass ≥ 70%, Distinction ≥ 90%.**

---

## Vincoli

- **Solo strumenti open source** (nessuna licenza commerciale richiesta)
- **Ambiente**: una singola VM con almeno 4 vCPU, 8 GB RAM, 40 GB storage (o bare-metal equivalente)
- **Distribuzione**: Debian 12 (preferito) o RHEL 9 / Rocky 9 / AlmaLinux 9
- **Nessun accesso cloud**: tutto locale, simulando un ambiente bare-metal
- **Tempo**: 4-6 settimane a ritmo personale, stimato 40-60 ore totali

---

## Suggerimenti

1. **Inizia dal hardening** — è più difficile hardened un sistema già configurato che configurare servizi su un sistema già hardened.
2. **Usa Ansible dall'inizio** — non configurare manualmente e poi scrivere il playbook. Scrivi il playbook e lascia che configuri per te.
3. **Testa il restore** — un backup non testato non è un backup. Esegui almeno un restore completo.
4. **Documenta mentre fai** — le decisioni prese oggi saranno dimenticate domani. Scrivi il perché, non il come (il come è nel playbook).
5. **Simula failure** — kill -9 un processo, riempi un disco, blocca una porta. Verifica che monitoring rilevi e che le procedure di recovery funzionino.

---

## Cross-link al percorso

Questo capstone integra conoscenze da tutti i moduli del corso. I moduli più rilevanti per ogni deliverable:

| Deliverable | Moduli chiave |
|-------------|---------------|
| D1 Storage | 06, 25 (ZFS), 01 (filesystem) |
| D2 Hardening | 11, 27 (SELinux/AppArmor), 34, 24 (nftables), 10 (SSH) |
| D3 Servizi | 28 (Nginx), 29 (PostgreSQL), 04 (systemd) |
| D4 Observability | 30 (Prometheus/Grafana), 20 (monitoring), 13 (logging) |
| D5 Automazione | 31 (Ansible), 16 (backup), 22 (troubleshooting) |
| D6 Documentazione | 35 (compliance), 33 (HA), 23 (bash scripting) |
