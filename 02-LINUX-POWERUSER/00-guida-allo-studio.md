# Guida allo Studio — Linux Power User

## Indice

- [Panoramica](#panoramica)
- [Piano di Studio](#piano-di-studio)
- [Glossario Termini Linux](#glossario-termini-linux)
- [Risorse e Riferimenti](#risorse-e-riferimenti)

---

## Panoramica

Questo percorso di studio è progettato per portare un professionista IT dalla conoscenza base di Linux alla padronanza completa dell'amministrazione di sistema, networking, sicurezza, containerizzazione, virtualizzazione e troubleshooting. Il focus è pratico e operativo: ogni argomento include comandi reali, configurazioni concrete e best practice da applicare immediatamente in ambienti di produzione.

Il percorso è rivolto a: IT Systems Manager, System Administrator, DevOps Engineer, Cybersecurity Specialist, sviluppatori che vogliono padroneggiare l'ambiente Linux.

**Tempo stimato**: 300-400 ore di studio e pratica, distribuite su 4-8 mesi.

---

## Piano di Studio

### Struttura del Programma

Il percorso è organizzato in 22 moduli progressivi:

**Fase 1 — Fondamenti del Sistema (moduli 01-04)**
- 01-Filesystem e gerarchia: struttura FHS, mount, permessi, ACL, link, inode
- 02-Shell mastery: Bash fondamenti, scripting, text processing, regex, tmux, Zsh
- 03-Gestione pacchetti: apt, dnf, pacman, snap, flatpak, compilazione da sorgente
- 04-Systemd: unit, servizi, timer, target, journalctl, boot process

**Fase 2 — Networking e Storage (moduli 05-06)**
- 05-Networking: TCP/IP, interfacce, routing, firewall, DNS, DHCP, VPN, WiFi
- 06-Storage: partizioni, LVM, RAID, filesystem, NFS, iSCSI, quota

**Fase 3 — Kernel e Performance (moduli 07-09)**
- 07-Kernel: architettura, moduli, compilazione, sysctl, parametri boot
- 08-Performance: benchmarking, CPU, memoria, I/O, rete, tuning
- 09-Gestione processi: ps, top, nice, cgroups, namespace, scheduling

**Fase 4 — Sicurezza (moduli 10-12)**
- 10-SSH avanzato: tunneling, key management, hardening, jump host, agent forwarding
- 11-Sicurezza: hardening, SELinux/AppArmor, audit, firewall, IDS, crittografia
- 12-Utenti e gruppi: gestione account, sudo, PAM, LDAP, policy password

**Fase 5 — Servizi e Infrastruttura (moduli 13-20)**
- 13-Logging: syslog, journald, log rotation, centralizzazione, analisi
- 14-Containerizzazione: Docker, Podman, Compose, Kubernetes base, registry
- 15-Virtualizzazione: KVM, QEMU, libvirt, Vagrant, cloud-init
- 16-Backup: strategie, rsync, borgbackup, snapshot, disaster recovery
- 17-Web server: Nginx, Apache, reverse proxy, SSL/TLS, load balancing
- 18-Database: MySQL/MariaDB, PostgreSQL, Redis, MongoDB, backup DB
- 19-Servizi rete: DNS (Bind), DHCP, NTP, mail, LDAP, Samba
- 20-Monitoring: Prometheus, Grafana, Nagios, alerting, dashboard

**Fase 6 — Automazione e Troubleshooting (moduli 21-22)**
- 21-Automazione: Ansible, Terraform, scripting avanzato, CI/CD
- 22-Troubleshooting: diagnostica sistematica, recovery, guide pratiche

### Metodologia

1. **Ambiente di pratica**: configurare VM (VirtualBox/KVM) o container per sperimentare
2. **Per ogni modulo**: leggere la teoria → eseguire i comandi → provare scenari di troubleshooting
3. **Progetto pratico**: costruire e gestire un piccolo datacenter virtuale (web server + DB + monitoring + backup)
4. **Certificazioni**: questo percorso copre il materiale per LPIC-1, LPIC-2, RHCSA

---

## Glossario Termini Linux

### Filesystem e Sistema

| Termine | Definizione |
|---|---|
| **FHS** | Filesystem Hierarchy Standard — struttura standard delle directory Linux |
| **inode** | Struttura dati che descrive un file (permessi, proprietario, blocchi dati) |
| **mount point** | Directory dove un filesystem viene reso accessibile |
| **LVM** | Logical Volume Manager — gestione flessibile dei volumi disco |
| **RAID** | Redundant Array of Independent Disks |
| **ext4/XFS/Btrfs** | Filesystem Linux principali |
| **swap** | Spazio disco usato come memoria virtuale |
| **ACL** | Access Control List — permessi estesi oltre owner/group/other |

### Processo e Kernel

| Termine | Definizione |
|---|---|
| **PID** | Process ID — identificatore unico del processo |
| **daemon** | Processo in background che fornisce un servizio |
| **cgroup** | Control Group — limita risorse (CPU, RAM) per gruppi di processi |
| **namespace** | Isolamento di risorse kernel (base dei container) |
| **init/systemd** | Primo processo (PID 1), gestisce tutti i servizi |
| **sysctl** | Interfaccia per modificare parametri kernel a runtime |
| **modprobe** | Carica/scarica moduli kernel |

### Networking

| Termine | Definizione |
|---|---|
| **netfilter/iptables/nftables** | Framework firewall del kernel Linux |
| **socket** | Endpoint di comunicazione di rete (IP:porta) |
| **bridge** | Collegamento layer 2 tra interfacce di rete |
| **VLAN** | Virtual LAN — segmentazione logica della rete |
| **bonding** | Aggregazione di interfacce di rete per ridondanza/throughput |
| **tun/tap** | Interfacce di rete virtuali per VPN/tunneling |

### Sicurezza

| Termine | Definizione |
|---|---|
| **SELinux** | Security-Enhanced Linux — MAC (Mandatory Access Control) |
| **AppArmor** | Alternativa a SELinux, basata su profili per applicazione |
| **PAM** | Pluggable Authentication Modules |
| **LUKS** | Linux Unified Key Setup — crittografia disco |
| **SSH** | Secure Shell — protocollo per accesso remoto cifrato |
| **sudoers** | File di configurazione dei privilegi sudo |

### Containerizzazione e Virtualizzazione

| Termine | Definizione |
|---|---|
| **Docker** | Piattaforma di containerizzazione |
| **Podman** | Alternativa rootless a Docker |
| **KVM** | Kernel-based Virtual Machine — hypervisor nativo Linux |
| **libvirt** | API per gestire virtualizzazione (virsh, virt-manager) |
| **OCI** | Open Container Initiative — standard per container |

---

## Risorse e Riferimenti

### Libri Fondamentali
- "The Linux Command Line" — William Shotts (base, gratuito online)
- "How Linux Works" — Brian Ward (come funziona il sistema)
- "UNIX and Linux System Administration Handbook" — Evi Nemeth (bibbia sysadmin)
- "Linux Bible" — Christopher Negus (riferimento completo)
- "The Practice of System and Network Administration" — Limoncelli (operazioni)

### Documentazione Online
- **man pages**: `man comando` — la prima risorsa da consultare sempre
- **ArchWiki**: wiki.archlinux.org — la documentazione Linux più completa e aggiornata
- **TLDR pages**: tldr.sh — esempi pratici per ogni comando
- **Linux Documentation Project**: tldp.org — guide e HOWTO storici
- **Red Hat documentation**: access.redhat.com/documentation

### Comunità
- r/linux, r/linuxadmin, r/sysadmin (Reddit)
- Server Fault (Stack Exchange per sysadmin)
- Linux Foundation (training e certificazioni)
- Fedora, Debian, Arch community forum

### Certificazioni
- **LPIC-1/LPIC-2**: certificazioni vendor-neutral Linux Professional Institute
- **RHCSA/RHCE**: certificazioni Red Hat (hands-on, molto rispettate)
- **CompTIA Linux+**: certificazione entry-level
- **LFCS/LFCE**: Linux Foundation Certified System Administrator/Engineer
