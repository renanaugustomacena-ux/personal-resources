# Glossario — Linux per Ingegneri di Sistema

> **Aggiornamento:** 2026-05-23
> **Nota:** Termini introdotti nei moduli del corso. Tra parentesi il modulo di prima introduzione.

| Termine | Definizione | Modulo |
|---------|------------|--------|
| **ACL** | Access Control List — permessi granulari oltre owner/group/other | 01 |
| **AIDE** | Advanced Intrusion Detection Environment — file integrity monitoring | 34, 35 |
| **Alertmanager** | Componente Prometheus per routing/grouping/silencing alert | 30 |
| **Ansible** | Agentless configuration management via SSH e YAML playbook | 31 |
| **AppArmor** | MAC framework path-based, default Ubuntu/Debian/SUSE | 27 |
| **APT** | Advanced Package Tool — gestore pacchetti Debian/Ubuntu | 03 |
| **ARC** | Adaptive Replacement Cache — cache L1 di ZFS in RAM | 25 |
| **auditd** | Daemon di audit del kernel Linux per syscall e file monitoring | 34 |
| **AVC** | Access Vector Cache — cache delle decisioni SELinux | 27 |
| **Bash** | Bourne Again Shell — shell predefinita su maggior parte delle distro | 02, 23 |
| **bpftrace** | Linguaggio di tracing basato su eBPF per analisi kernel | 07, 08 |
| **cgroups v2** | Control Groups v2 — resource limiting e accounting per processi | 07, 09 |
| **Chain** | Sequenza ordinata di regole firewall associata a un hook Netfilter | 24 |
| **CIS Benchmark** | Standard di hardening pubblicato dal Center for Internet Security | 34, 35 |
| **Conntrack** | Connection tracking — tracciamento stato connessioni per firewalling stateful | 24 |
| **Cryptokey routing** | Meccanismo WireGuard che associa chiavi pubbliche a IP consentiti | 32 |
| **DERP** | Designated Encrypted Relay for Packets — relay TCP per Tailscale | 32 |
| **Distroless** | Immagini container minimali senza shell, package manager, o utilità | 14, 26 |
| **DKMS** | Dynamic Kernel Module Support — compilazione automatica moduli kernel | 07 |
| **DNAT** | Destination NAT — modifica indirizzo/porta destinazione (port forwarding) | 24 |
| **DRBD** | Distributed Replicated Block Device — replica blocchi disco via rete | 33 |
| **Easy-RSA** | CLI per gestire PKI (CA, emissione, revoca certificati) con OpenVPN | 32 |
| **eBPF** | Extended Berkeley Packet Filter — esecuzione sicura di programmi nel kernel | 07 |
| **Exporter** | Processo che espone metriche in formato Prometheus da un servizio | 30 |
| **fail2ban** | Strumento che banna IP basandosi su pattern nei log | 24 |
| **FHS** | Filesystem Hierarchy Standard — struttura standard directory Linux | 01 |
| **firewalld** | Frontend zone-based per nftables, default RHEL/Fedora | 24 |
| **Flowtable** | Meccanismo nftables per fast-path: bypass stack completo per connessioni stabilite | 24 |
| **fwmark** | Marca numerica su pacchetti per policy routing nel kernel Linux | 32 |
| **Grafana** | Piattaforma di visualizzazione per metriche, log e trace | 30 |
| **Headscale** | Implementazione open source del coordination server Tailscale | 32 |
| **HTTP/3** | Protocollo HTTP basato su QUIC (UDP) | 28 |
| **ifunc** | GNU indirect function — meccanismo per dispatch a runtime | 99-CS |
| **iptables** | Strumento legacy userspace per configurare Netfilter | 24 |
| **journald** | Daemon di logging di systemd con journal binario strutturato | 13 |
| **Keepalived** | Implementazione VRRP per floating IP e health check | 33 |
| **Kill switch** | Regole firewall che bloccano tutto il traffico non-VPN | 32 |
| **KVM** | Kernel-based Virtual Machine — hypervisor tipo 1 integrato nel kernel | 15 |
| **L2TP/IPsec** | VPN legacy con doppio incapsulamento | 32 |
| **LDAP/SSSD** | Autenticazione centralizzata: directory service + system daemon | 12 |
| **libvirt** | API di astrazione per gestione virtualizzazione (KVM, QEMU, Xen) | 15 |
| **logrotate** | Rotazione automatica file di log con compressione e retention | 13 |
| **LSM** | Linux Security Module — framework kernel per moduli di sicurezza | 27 |
| **LTS** | Long Term Support — kernel con supporto esteso (6+ anni) | 07 |
| **Lynis** | Strumento di audit e hardening per sistemi Unix/Linux | 34, 35 |
| **MagicDNS** | Risoluzione automatica nomi nodi in rete mesh Tailscale | 32 |
| **MASQUERADE** | SNAT dinamico: usa automaticamente IP dell'interfaccia di uscita | 24 |
| **Molecule** | Framework di testing per ruoli Ansible | 31 |
| **mq-deadline** | I/O scheduler multi-queue per dispositivi a bassa latenza | 07 |
| **netplan** | Configurazione rete dichiarativa YAML per Ubuntu | 05 |
| **nftables** | Successore di iptables: sintassi unificata, operazioni atomiche, set nativi | 24 |
| **nginx** | Web server/reverse proxy ad alta performance, event-driven | 17, 28 |
| **Noise Protocol** | Framework crittografico per handshake (usato da WireGuard, variante IK) | 32 |
| **NTP** | Network Time Protocol — sincronizzazione orario di rete | 19 |
| **OCI** | Open Container Initiative — standard per container runtime e immagini | 14 |
| **OpenSCAP** | Strumento di compliance scanning basato su SCAP/OVAL | 35 |
| **OpenZFS** | Implementazione open source di ZFS per Linux e FreeBSD | 06, 25 |
| **osquery** | Introspezione del sistema operativo via query SQL | 34, 35 |
| **Pacemaker** | Cluster resource manager per HA — gestisce risorse e failover | 33 |
| **PAM** | Pluggable Authentication Modules — framework autenticazione Linux | 12, 34 |
| **pkexec** | Programma polkit per elevazione privilegi (oggetto CVE-2021-4034) | 99-CS |
| **PostgreSQL** | RDBMS open source avanzato con MVCC, WAL, replicazione | 18, 29 |
| **Prometheus** | Sistema di monitoring pull-based con TSDB integrato | 30 |
| **PromQL** | Linguaggio di query per dati time series di Prometheus | 30 |
| **PSK** | Pre-Shared Key — chiave simmetrica condivisa pre-distribuita | 32 |
| **Quadlet** | Integrazione systemd per container Podman via file .container | 14, 26 |
| **Recording rule** | Regola Prometheus che pre-calcola e salva espressioni PromQL | 30 |
| **rsyslog** | Daemon syslog avanzato con filtraggio, parsing, forwarding | 13 |
| **SBOM** | Software Bill of Materials — inventario componenti software | 35, 99-CS |
| **seccomp** | Secure Computing Mode — filtro syscall nel kernel Linux | 27 |
| **SELinux** | Security-Enhanced Linux — MAC framework label-based, default RHEL | 27 |
| **SNAT** | Source NAT — modifica indirizzo sorgente pacchetti in uscita | 24 |
| **softdog** | Software watchdog kernel per rilevamento hang di sistema | 33 |
| **STONITH** | Shoot The Other Node In The Head — fencing in cluster HA | 33 |
| **sysctl** | Interfaccia per tuning parametri kernel a runtime via /proc/sys | 07, 34 |
| **systemd** | Init system + service manager unificato per Linux moderno | 04 |
| **systemd.exec** | Direttive hardening per unit systemd (ProtectSystem, PrivateTmp, etc.) | 04, 34 |
| **Tailscale** | Overlay mesh network su WireGuard con control plane gestito | 32 |
| **Thanos** | Sistema per scaling orizzontale e long-term storage di Prometheus | 30 |
| **TLS** | Transport Layer Security — protocollo crittografico per comunicazioni sicure | 28, 32 |
| **tls-crypt** | Direttiva OpenVPN che cifra e autentica il control channel TLS | 32 |
| **ufw** | Uncomplicated Firewall — frontend iptables per Ubuntu | 24 |
| **Verdict map** | Struttura nftables che associa chiavi direttamente a verdict (accept/drop) | 24 |
| **VORACLE** | Attacco a compressione VPN derivato da CRIME/BREACH | 32 |
| **VRRP** | Virtual Router Redundancy Protocol — protocollo per floating IP | 33 |
| **wg-quick** | Wrapper bash per gestione semplificata interfacce WireGuard | 32 |
| **WireGuard** | VPN protocol kernel-native: Noise IK, ChaCha20-Poly1305, ~4000 righe | 32 |
| **ZFS** | Zettabyte File System — filesystem + volume manager con CoW, snapshot, RAID-Z | 06, 25 |
| **Zone (firewalld)** | Raggruppamento interfacce+sorgenti con livello di fiducia e regole predefiniti | 24 |
