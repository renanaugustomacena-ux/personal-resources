# Indice — Linux per Ingegneri di Sistema

> **Corso:** Linux per ingegneri di sistema (sysadmin → SRE)
> **Aggiornamento:** 2026-05-23
> **Moduli:** 35 + 2 guide operative legacy + scaffolding
> **Percorso consigliato:** vedi [00-SYLLABUS.md](00-SYLLABUS.md)

---

## File di Scaffolding

| File | Scopo | Stato |
|------|-------|-------|
| [00-SYLLABUS.md](00-SYLLABUS.md) | Percorso formativo, fasi, prerequisiti, capstone | stable |
| [00-INDEX.md](00-INDEX.md) | Questo file — indice completo | stable |
| [00-GLOSSARIO.md](00-GLOSSARIO.md) | Glossario termini introdotti nel corso | stable |
| [00-BIBLIOGRAFIA.md](00-BIBLIOGRAFIA.md) | Fonti primarie consolidate | stable |
| [00-CAPSTONE.md](00-CAPSTONE.md) | Progetto finale: brief, deliverable, rubric | stable |
| [00-guida-allo-studio.md](00-guida-allo-studio.md) | Guida allo studio originale (legacy) | base |

---

## Moduli del Corso

### Fase 1 — Fondamenti

| # | Modulo | Sinossi | Stato |
|---|--------|---------|-------|
| 01 | [filesystem-e-gerarchia.md](01-filesystem-e-gerarchia.md) | FHS, permessi, ACL, xattr, mount, fstab, inode | stable |
| 02 | [shell-mastery.md](02-shell-mastery.md) | Bash/Zsh avanzato, redirezione, pipeline, expansion, job control | stable |
| 12 | [utenti-e-gruppi.md](12-utenti-e-gruppi.md) | Gestione utenti, gruppi, PAM, LDAP/SSSD, sudoers | stable |

### Fase 2 — Sistema

| # | Modulo | Sinossi | Stato |
|---|--------|---------|-------|
| 03 | [gestione-pacchetti.md](03-gestione-pacchetti.md) | APT, DNF, pacchetti, repository, dependency hell, holds | stable |
| 04 | [systemd.md](04-systemd.md) | Unit, target, timer, service hardening, socket activation, cgroups | stable |
| 09 | [gestione-processi.md](09-gestione-processi.md) | Process lifecycle, segnali, nice, cgroups, scheduler CFS/EEVDF | stable |
| 13 | [logging.md](13-logging.md) | journald, rsyslog, log strutturati, rotazione, centralizzazione | stable |
| 08 | [performance.md](08-performance.md) | CPU, memoria, I/O, rete, profiling, perf, bpftrace, benchmarking | stable |

### Fase 3 — Storage e Networking

| # | Modulo | Sinossi | Stato |
|---|--------|---------|-------|
| 06 | [storage.md](06-storage.md) | Dischi, partizioni, filesystem, LVM, RAID, LUKS, NFS, iSCSI | stable |
| 25 | [zfs-guida-operativa.md](25-zfs-guida-operativa.md) | ZFS pool, vdev, snapshot, send/recv, scrub, degraded recovery | stable |
| 05 | [networking.md](05-networking.md) | TCP/IP, routing, bridge, VLAN, bonding, NetworkManager, netplan | stable |
| 24 | [iptables-nftables-guida-completa.md](24-iptables-nftables-guida-completa.md) | Netfilter, iptables, nftables, NAT, conntrack, firewalld, fail2ban | stable |
| 32 | [vpn-wireguard-openvpn.md](32-vpn-wireguard-openvpn.md) | WireGuard, OpenVPN, Tailscale/Headscale, PKI, split tunnel, HA | stable |

### Fase 4 — Servizi

| # | Modulo | Sinossi | Stato |
|---|--------|---------|-------|
| 17 | [web-server.md](17-web-server.md) | Apache, Nginx, reverse proxy, TLS, virtual host, load balancing | stable |
| 28 | [nginx-configurazione-avanzata.md](28-nginx-configurazione-avanzata.md) | Nginx architettura, caching, rate limiting, HTTP/2-3, API gateway | stable |
| 18 | [database.md](18-database.md) | PostgreSQL, MySQL/MariaDB, Redis, backup, replica, tuning | stable |
| 29 | [postgresql-amministrazione.md](29-postgresql-amministrazione.md) | PostgreSQL admin: configurazione, VACUUM, replica, backup, monitoring | stable |
| 19 | [servizi-rete.md](19-servizi-rete.md) | DNS (BIND, Unbound), DHCP, NTP, mail, FTP, Samba | stable |

### Fase 5 — Sicurezza

| # | Modulo | Sinossi | Stato |
|---|--------|---------|-------|
| 11 | [sicurezza.md](11-sicurezza.md) | Sicurezza Linux: crittografia, firewall, audit, IDS, hardening base | stable |
| 27 | [selinux-apparmor-guida-completa.md](27-selinux-apparmor-guida-completa.md) | MAC: SELinux policy, AppArmor profiles, seccomp, LSM, audit | stable |
| 34 | [hardening-sicurezza-avanzata.md](34-hardening-sicurezza-avanzata.md) | CIS Benchmark, STIG, kernel hardening, boot security, audit system | stable |
| 10 | [ssh-avanzato.md](10-ssh-avanzato.md) | SSH CA, agent forwarding threat model, tunneling, hardening, audit | stable |
| 16 | [backup.md](16-backup.md) | Strategie backup, 3-2-1-1-0, rsync, BorgBackup, Restic, DR drill | stable |

### Fase 6 — Operations e Automazione

| # | Modulo | Sinossi | Stato |
|---|--------|---------|-------|
| 14 | [containerizzazione.md](14-containerizzazione.md) | Container, Docker, Podman, Buildah, Compose, orchestrazione, security | stable |
| 26 | [docker-guida-operativa.md](26-docker-guida-operativa.md) | Docker operativo: Dockerfile, networking, storage, debugging, Quadlet | stable |
| 15 | [virtualizzazione.md](15-virtualizzazione.md) | KVM, QEMU, libvirt, Proxmox, Hyper-V, virt-manager, live migration | stable |
| 20 | [monitoring.md](20-monitoring.md) | Monitoring stack, metriche, alerting, SLI/SLO, observability | stable |
| 30 | [prometheus-grafana-monitoring.md](30-prometheus-grafana-monitoring.md) | Prometheus TSDB, PromQL, Alertmanager, Grafana, exporters, Thanos | stable |
| 21 | [automazione.md](21-automazione.md) | Automazione: cron, systemd timer, at, scripting, CI/CD intro | stable |
| 31 | [ansible-guida-operativa.md](31-ansible-guida-operativa.md) | Ansible: inventory, playbook, role, vault, molecule, AWX | stable |
| 22 | [troubleshooting.md](22-troubleshooting.md) | Troubleshooting sistematico: alberi decisionali, strumenti, scenari | stable |
| 33 | [high-availability-clustering.md](33-high-availability-clustering.md) | HA: Pacemaker, Corosync, DRBD, Keepalived, quorum, fencing, STONITH | stable |
| 23 | [bash-scripting-progetti-avanzati.md](23-bash-scripting-progetti-avanzati.md) | Bash avanzato: defensive scripting, parallel, testing, IPC | stable |
| 07 | [kernel.md](07-kernel.md) | Kernel: build, moduli, sysctl, eBPF, scheduler, memory, debugging | stable |
| 35 | [compliance-scanning-automazione.md](35-compliance-scanning-automazione.md) | Compliance: Lynis, OpenSCAP, AIDE, osquery, SBOM, pipeline CI | stable |

---

## Materiale Supplementare

### Case Study

| File | Argomento |
|------|-----------|
| [99-CASE-STUDY/CVE-2021-4034-pwnkit.md](99-CASE-STUDY/CVE-2021-4034-pwnkit.md) | Escalation di privilegi via pkexec — analisi tecnica e lezioni |
| [99-CASE-STUDY/CVE-2024-3094-xz-utils.md](99-CASE-STUDY/CVE-2024-3094-xz-utils.md) | Supply chain attack via backdoor in liblzma — timeline e impatto |

### Esercizi Extra

| Directory | Contenuto |
|-----------|-----------|
| [99-ESERCIZI/](99-ESERCIZI/) | Esercizi aggiuntivi per modulo (in sviluppo) |
