# Syllabus — Linux per Ingegneri di Sistema (Sysadmin → SRE)

> **Lingua:** italiano · **Aggiornamento:** 2026-05-23
> **Versioni:** kernel 6.1/6.6/6.12 LTS; systemd 254+; ZFS 2.2/2.3; Docker 27+; nginx 1.26+; PostgreSQL 16+; Prometheus 2.x; Ansible 9.x.
> **Moduli:** 35 + 2 case study + scaffolding
> **Tempo stimato:** 16-20 settimane (studio part-time) + 4-6 settimane capstone

---

## Identità

**"Linux per ingegneri di sistema"** — sysadmin → SRE foundations. Storage avanzato (ZFS, LVM perf cliffs), kernel test matrix, systemd hardening, SSH CA at scale, SELinux/AppArmor playbook, compliance scanning automation.

**Target:** competent → proficient → expert (3 → 5). Capace di hardening Debian/RHEL produzione + observability stack + compliance audit.

## Prerequisiti

CLI fluent; networking basics; vim/nano; comprensione concetti OS.

## Obiettivi di Apprendimento

Al completamento del corso, lo studente sarà in grado di:

1. Navigare e gestire il filesystem Linux con permessi, ACL e xattr.
2. Padroneggiare Bash/Zsh avanzato: scripting difensivo con `set -euo pipefail`, trap, parallel.
3. Gestire pacchetti su Debian/RHEL: dependency resolution, holds, repository management.
4. Configurare e hardenizzare systemd: unit, target, timer, socket activation, security directives.
5. Amministrare ZFS in produzione: degraded recovery, scrub I/O impact, snapshot retention, encryption.
6. Comprendere il kernel Linux: moduli, sysctl tuning, eBPF, scheduler, memory management.
7. Configurare networking avanzato: nftables firewalling, VPN (WireGuard/OpenVPN), policy routing.
8. Implementare SSH CA at scale con revocation e audit.
9. Applicare MAC framework: SELinux/AppArmor enforcing + compliance scanning (Lynis, AIDE, osquery).
10. Gestire container in produzione: rootless, security scanning, Quadlet, registry auth.
11. Costruire stack di observability: Prometheus + Grafana + Alertmanager + Loki.
12. Automatizzare con Ansible: playbook, ruoli, vault, molecule, CI/CD integration.
13. Progettare HA: Pacemaker/Corosync, DRBD, Keepalived, fencing, DR planning.
14. Eseguire hardening CIS Benchmark Level 2 e compliance scanning automatizzato.

## Struttura del Corso

### Fase 1 — Fondamenti (settimane 1-2)

| # | Modulo | Argomenti chiave |
|---|--------|-----------------|
| 01 | [Filesystem e gerarchia](01-filesystem-e-gerarchia.md) | FHS, permessi, ACL, xattr, mount, inode |
| 02 | [Shell mastery](02-shell-mastery.md) | Bash/Zsh, redirezione, pipeline, expansion, job control |
| 12 | [Utenti e gruppi](12-utenti-e-gruppi.md) | PAM, LDAP/SSSD, sudoers, password policy |

### Fase 2 — Sistema (settimane 3-5)

| # | Modulo | Argomenti chiave |
|---|--------|-----------------|
| 03 | [Gestione pacchetti](03-gestione-pacchetti.md) | APT, DNF, repository, dependency hell, holds |
| 04 | [systemd](04-systemd.md) | Unit, target, timer, hardening, socket activation |
| 09 | [Gestione processi](09-gestione-processi.md) | Lifecycle, segnali, nice, cgroups, CFS/EEVDF |
| 13 | [Logging](13-logging.md) | journald, rsyslog, rotazione, centralizzazione |
| 08 | [Performance](08-performance.md) | CPU, memoria, I/O, rete, perf, bpftrace |

### Fase 3 — Storage e Networking (settimane 6-8)

| # | Modulo | Argomenti chiave |
|---|--------|-----------------|
| 06 | [Storage](06-storage.md) | Dischi, filesystem, LVM, RAID, LUKS, NFS |
| 25 | [ZFS guida operativa](25-zfs-guida-operativa.md) | Pool, vdev, snapshot, send/recv, scrub, recovery |
| 05 | [Networking](05-networking.md) | TCP/IP, routing, bridge, VLAN, bonding |
| 24 | [iptables/nftables](24-iptables-nftables-guida-completa.md) | Netfilter, nftables, NAT, conntrack, firewalld |
| 32 | [VPN](32-vpn-wireguard-openvpn.md) | WireGuard, OpenVPN, Tailscale, PKI, kill switch |

### Fase 4 — Servizi (settimane 9-11)

| # | Modulo | Argomenti chiave |
|---|--------|-----------------|
| 17 | [Web server](17-web-server.md) | Apache, Nginx, reverse proxy, TLS, virtual host |
| 28 | [Nginx avanzato](28-nginx-configurazione-avanzata.md) | Architettura, caching, rate limiting, HTTP/2-3, API gateway |
| 18 | [Database](18-database.md) | PostgreSQL, MySQL, Redis, backup, replica |
| 29 | [PostgreSQL admin](29-postgresql-amministrazione.md) | Configurazione, VACUUM, replica, backup, monitoring |
| 19 | [Servizi rete](19-servizi-rete.md) | DNS, DHCP, NTP, mail, Samba |

### Fase 5 — Sicurezza (settimane 12-14)

| # | Modulo | Argomenti chiave |
|---|--------|-----------------|
| 11 | [Sicurezza](11-sicurezza.md) | Crittografia, firewall, audit, IDS, hardening base |
| 27 | [SELinux/AppArmor](27-selinux-apparmor-guida-completa.md) | MAC, policy, profili, seccomp, LSM, audit |
| 34 | [Hardening avanzato](34-hardening-sicurezza-avanzata.md) | CIS Benchmark, STIG, kernel hardening, boot security |
| 10 | [SSH avanzato](10-ssh-avanzato.md) | SSH CA, tunneling, hardening, audit |
| 16 | [Backup](16-backup.md) | 3-2-1-1-0, rsync, BorgBackup, Restic, DR drill |

### Fase 6 — Operations e Automazione (settimane 15-18)

| # | Modulo | Argomenti chiave |
|---|--------|-----------------|
| 14 | [Containerizzazione](14-containerizzazione.md) | Docker, Podman, Buildah, Compose, security |
| 26 | [Docker operativo](26-docker-guida-operativa.md) | Dockerfile, networking, storage, debugging, Quadlet |
| 15 | [Virtualizzazione](15-virtualizzazione.md) | KVM, QEMU, libvirt, Proxmox, live migration |
| 20 | [Monitoring](20-monitoring.md) | Metriche, alerting, SLI/SLO, observability |
| 30 | [Prometheus + Grafana](30-prometheus-grafana-monitoring.md) | TSDB, PromQL, Alertmanager, exporters, Thanos |
| 21 | [Automazione](21-automazione.md) | cron, systemd timer, scripting, CI/CD |
| 31 | [Ansible operativo](31-ansible-guida-operativa.md) | Inventory, playbook, role, vault, molecule, AWX |
| 22 | [Troubleshooting](22-troubleshooting.md) | Alberi decisionali, strumenti, scenari |
| 33 | [HA clustering](33-high-availability-clustering.md) | Pacemaker, DRBD, Keepalived, fencing, STONITH |
| 23 | [Bash scripting avanzato](23-bash-scripting-progetti-avanzati.md) | Defensive scripting, parallel, testing, IPC |
| 07 | [Kernel](07-kernel.md) | Build, moduli, sysctl, eBPF, scheduler, debugging |
| 35 | [Compliance scanning](35-compliance-scanning-automazione.md) | Lynis, OpenSCAP, AIDE, osquery, SBOM, CI pipeline |

### Fase 7 — Capstone (settimane 19-24)

Vedi [00-CAPSTONE.md](00-CAPSTONE.md) per il brief completo.

## Capstone

Hardening + observability stack su VM Debian 12: CIS Benchmark Level 2 applicato, ZFS encrypted root, systemd hardened, Prometheus+Grafana+Alertmanager, lynis+aide+osquery integration, Ansible playbook idempotente, runbook operativo completo. Dettagli in [00-CAPSTONE.md](00-CAPSTONE.md).

---

## Materiale Supplementare

| Risorsa | Scopo |
|---------|-------|
| [00-INDEX.md](00-INDEX.md) | Indice completo con sinossi |
| [00-GLOSSARIO.md](00-GLOSSARIO.md) | Glossario termini del corso |
| [00-BIBLIOGRAFIA.md](00-BIBLIOGRAFIA.md) | Fonti primarie consolidate |
| [00-CAPSTONE.md](00-CAPSTONE.md) | Progetto finale: brief, deliverable, rubric |
| [99-CASE-STUDY/](99-CASE-STUDY/) | Case study: CVE-2021-4034, CVE-2024-3094 |
| [99-ESERCIZI/](99-ESERCIZI/) | Esercizi aggiuntivi per modulo |

---

## Valutazione

| Componente | Peso |
|------------|------|
| Esercizi per modulo (autovalutazione) | — |
| Capstone: Storage/ZFS | 15% |
| Capstone: Hardening CIS L2 | 25% |
| Capstone: Servizi (Nginx+PostgreSQL) | 15% |
| Capstone: Observability | 20% |
| Capstone: Automazione/DR | 15% |
| Capstone: Documentazione | 10% |

**Pass ≥ 70%, Distinction ≥ 90%.** Vedi [00-CAPSTONE.md](00-CAPSTONE.md) per la rubric dettagliata.
