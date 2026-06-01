# Bibliografia del Corso — Migrazione VMware → Proxmox VE

> **Tipo:** hub centrale delle fonti primarie del corso
> **Lingua:** italiano (titolo); fonti in lingua originale (in massima parte inglese)
> **Ultimo aggiornamento:** 2026-04-26
> **Politica di citazione:**
> 1. **Primarie** (preferite): RFC, IEEE/ISO/NIST, CVE, doc ufficiali del produttore (Proxmox/VMware/QEMU/libguestfs/Ceph/OpenZFS), kernel.org, man page, paper peer-reviewed.
> 2. **Secondarie autorevoli**: libri con ISBN, talk a conferenze (USENIX, FOSDEM, KubeCon, BlackHat), blog di mantainer.
> 3. **Comunitarie**: ArchWiki, wiki di progetto, README ufficiali — ammesse quando canoniche.
> 4. **Da evitare come unica fonte**: Stack Overflow, Medium generico, marketing pagine vendor non documentazione, tutorial non verificabili.
>
> **Web search policy** (per regole globali della libreria): solo DuckDuckGo, mai Google. Per documentazione di librerie e framework, prima Context7, poi WebFetch sulla doc primaria.

Questo file e l'hub centrale. I singoli moduli citano per numero locale `[N]` e qui consolidiamo. Quando un modulo aggiunge una nuova fonte, la inseriamo qui con un identificatore stabile (`PVE-NN`, `VM-NN`, `RFC-NNNN`, `CVE-YYYY-NNNN`...). I link sono stati verificati il 2026-04-26 con `curl -L --max-time 12` (HTTP 200 atteso).

---

## 1. Proxmox VE — Documentazione ufficiale

| ID | Titolo | URL | Note di versione |
|---|---|---|---|
| `PVE-WIKI` | Proxmox VE Wiki — pagina principale | https://pve.proxmox.com/wiki/Main_Page | Riferimento top-level |
| `PVE-ADMIN` | Proxmox VE Administration Guide | https://pve.proxmox.com/pve-docs/pve-admin-guide.html | Esiste anche PDF |
| `PVE-API` | Proxmox VE API Viewer | https://pve.proxmox.com/pve-docs/api-viewer/ | Interattivo, browse-by-endpoint |
| `PVE-ROADMAP` | Proxmox VE Roadmap | https://pve.proxmox.com/wiki/Roadmap | Storia release; al 2026-04-26 ultima e PVE 9.1 (2025-11-19) |
| `PVE-STORAGE` | PVE Wiki — Storage | https://pve.proxmox.com/wiki/Storage | Tabella backend supportati |
| `PVE-CLUSTER` | PVE Wiki — Cluster Manager | https://pve.proxmox.com/wiki/Cluster_Manager | Corosync, pmxcfs, quorum |
| `PVE-HA` | PVE Wiki — High Availability | https://pve.proxmox.com/wiki/High_Availability | ha-manager, fencing |
| `PVE-MIGRATE-V2V` | PVE Wiki — Migration of servers to Proxmox VE | https://pve.proxmox.com/wiki/Migration_of_servers_to_Proxmox_VE | Pagina sintetica V2V |
| `PVE-CLOUDINIT` | PVE Wiki — Cloud-Init Support | https://pve.proxmox.com/wiki/Cloud-Init_Support | Template VM cloud-init |
| `PVE-FIREWALL` | PVE Wiki — Firewall | https://pve.proxmox.com/wiki/Firewall | Cluster + VM firewall |
| `PVE-SDN` | PVE Wiki — Software-Defined Network | https://pve.proxmox.com/wiki/Software-Defined_Network | EVPN/VXLAN/VLAN |
| `PVE-BUGZILLA` | Proxmox Bugzilla | https://bugzilla.proxmox.com/ | Tracking di bug noti |
| `PVE-FORUM` | Proxmox Community Forum | https://forum.proxmox.com/ | Comunita ufficiale |
| `PVE-GIT` | Proxmox Git | https://git.proxmox.com/ | Sorgenti pacchetti `pve-*` |
| `PVE-DOWNLOAD` | Proxmox Downloads | https://www.proxmox.com/en/downloads | ISO ufficiali, checksum SHA256 |

### Proxmox Backup Server

| ID | Titolo | URL |
|---|---|---|
| `PBS-DOCS` | Proxmox Backup Server Documentation | https://pbs.proxmox.com/docs/ |
| `PBS-API` | PBS REST API | https://pbs.proxmox.com/docs/api-viewer/ |
| `PBS-GIT` | Proxmox Backup Git | https://git.proxmox.com/?p=proxmox-backup.git |

---

## 2. VMware vSphere / Broadcom

| ID | Titolo | URL |
|---|---|---|
| `VM-DOCS` | VMware vSphere Documentation | https://docs.vmware.com/en/VMware-vSphere/ |
| `VM-KB` | Broadcom Knowledge Base (ex-VMware KB) | https://knowledge.broadcom.com/ |
| `VM-COMPAT` | VMware Compatibility Guide | https://www.vmware.com/resources/compatibility/search.php |
| `VM-LIFECYCLE` | ESXi 8.0 build numbers and versions | https://knowledge.broadcom.com/external/article?legacyId=2143832 |
| `VM-OVF` | OVF specification | https://www.dmtf.org/standards/ovf |

**Versioni ESXi 8.0 al 2026-04-26**:

| Versione | Data | Build |
|---|---|---|
| ESXi 8.0 GA | 2022-10-11 | 20513097 |
| ESXi 8.0 Update 1 | 2023-04-18 | 21495797 |
| ESXi 8.0 Update 2 | 2023-09-21 | 22380479 |
| ESXi 8.0 Update 3 | 2024-06-25 | 24022510 |
| ESXi 8.0.3 P08 (Update 3i) | 2026-02-24 | 25205845 |

(Fonte: `VM-LIFECYCLE`, retrieved 2026-04-26.)

---

## 3. QEMU / KVM / libvirt / libguestfs

| ID | Titolo | URL |
|---|---|---|
| `QEMU-DOCS` | QEMU Documentation (latest) | https://www.qemu.org/docs/master/ |
| `QEMU-IMG` | qemu-img(1) | https://www.qemu.org/docs/master/tools/qemu-img.html |
| `QEMU-WIKI` | QEMU Wiki | https://wiki.qemu.org/ |
| `KVM-DOCS` | Linux KVM Documentation | https://www.linux-kvm.org/page/Documents |
| `LIBVIRT-DOCS` | libvirt Documentation | https://libvirt.org/docs.html |
| `LIBVIRT-XML` | libvirt domain XML reference | https://libvirt.org/formatdomain.html |
| `V2V-MAN` | virt-v2v(1) man page | https://libguestfs.org/virt-v2v.1.html |
| `V2V-INPUT` | virt-v2v input modes | https://libguestfs.org/virt-v2v-input-vmware.1.html |
| `V2V-OUTPUT` | virt-v2v output modes | https://libguestfs.org/virt-v2v-output-local.1.html |
| `LIBGUESTFS` | libguestfs project | https://libguestfs.org/ |

---

## 4. Storage — ZFS, LVM, Ceph

| ID | Titolo | URL |
|---|---|---|
| `OPENZFS` | OpenZFS Documentation | https://openzfs.github.io/openzfs-docs/ |
| `OPENZFS-MAN` | OpenZFS man pages | https://openzfs.github.io/openzfs-docs/man/master/index.html |
| `ZFS-PERF` | ZFS Performance Tuning (OpenZFS) | https://openzfs.github.io/openzfs-docs/Performance%20and%20Tuning/Workload%20Tuning.html |
| `LVM2-MAN` | LVM2 man pages (kernel.org) | https://kernel.org/doc/man-pages/online/dir_section_8.html |
| `LVM-LWN` | LWN — LVM-Thin overview | https://lwn.net/Articles/465740/ |
| `CEPH-DOCS` | Ceph Documentation | https://docs.ceph.com/en/latest/ |
| `CEPH-RADOS` | RADOS architecture paper | https://www.ssrc.ucsc.edu/Papers/weil-osdi06.pdf |

---

## 5. Networking — Linux Bridge, Open vSwitch, RFC

| ID | Titolo | URL |
|---|---|---|
| `LINUX-BRIDGE` | Linux Foundation Wiki — bridge | https://wiki.linuxfoundation.org/networking/bridge |
| `OVS-DOCS` | Open vSwitch Documentation | https://docs.openvswitch.org/en/latest/ |
| `BONDING` | Linux Ethernet Bonding driver howto | https://www.kernel.org/doc/Documentation/networking/bonding.txt |
| `IPROUTE2` | iproute2 documentation | https://wiki.linuxfoundation.org/networking/iproute2 |
| `RFC-1918` | RFC 1918 — Address Allocation for Private Internets | https://datatracker.ietf.org/doc/html/rfc1918 |
| `RFC-2131` | RFC 2131 — DHCP | https://datatracker.ietf.org/doc/html/rfc2131 |
| `RFC-2132` | RFC 2132 — DHCP Options | https://datatracker.ietf.org/doc/html/rfc2132 |
| `RFC-2865` | RFC 2865 — RADIUS | https://datatracker.ietf.org/doc/html/rfc2865 |
| `RFC-3164` | RFC 3164 — BSD Syslog Protocol | https://datatracker.ietf.org/doc/html/rfc3164 |
| `RFC-4253` | RFC 4253 — SSH Transport Layer Protocol | https://datatracker.ietf.org/doc/html/rfc4253 |
| `RFC-4519` | RFC 4519 — LDAP Schema | https://datatracker.ietf.org/doc/html/rfc4519 |
| `RFC-5424` | RFC 5424 — Syslog Protocol | https://datatracker.ietf.org/doc/html/rfc5424 |
| `RFC-7159` | RFC 7159 — JSON | https://datatracker.ietf.org/doc/html/rfc7159 |
| `RFC-7230..7235` | RFC 7230-7235 — HTTP/1.1 (suite) | https://datatracker.ietf.org/doc/html/rfc7230 |
| `RFC-8446` | RFC 8446 — TLS 1.3 | https://datatracker.ietf.org/doc/html/rfc8446 |
| `IEEE-802.1Q` | IEEE 802.1Q — VLANs | https://standards.ieee.org/ieee/802.1Q/6844/ |
| `IEEE-802.1AX` | IEEE 802.1AX — Link Aggregation | https://standards.ieee.org/ieee/802.1AX/4940/ |

---

## 6. Cluster — Corosync, pcs, fencing

| ID | Titolo | URL |
|---|---|---|
| `COROSYNC-DOCS` | Corosync Project | https://corosync.github.io/corosync/ |
| `COROSYNC-MAN` | Corosync man pages | https://manpages.debian.org/bookworm/corosync/ |
| `KRONOSNET` | Kronosnet (knet) — Corosync transport | https://kronosnet.org/ |
| `CLUSTERLABS` | ClusterLabs — Pacemaker e fencing | https://clusterlabs.org/ |
| `STONITH-WIKI` | STONITH (ClusterLabs Wiki) | https://wiki.clusterlabs.org/wiki/STONITH |

---

## 7. Cloud-Init, Automation, IaC

| ID | Titolo | URL |
|---|---|---|
| `CLOUDINIT` | cloud-init Documentation | https://cloudinit.readthedocs.io/en/latest/ |
| `TERRAFORM-PROV` | Telmate Terraform Proxmox provider | https://github.com/Telmate/terraform-provider-proxmox |
| `BPG-PROV` | bpg/terraform-provider-proxmox | https://github.com/bpg/terraform-provider-proxmox |
| `ANSIBLE-PVE` | Ansible Galaxy — community.general / proxmox modules | https://docs.ansible.com/ansible/latest/collections/community/general/proxmox_module.html |

---

## 8. Sicurezza, identita, crypto

| ID | Titolo | URL |
|---|---|---|
| `OWASP-TOP-10` | OWASP Top 10 (latest) | https://owasp.org/www-project-top-ten/ |
| `OWASP-ASVS` | OWASP ASVS | https://owasp.org/www-project-application-security-verification-standard/ |
| `NIST-800-53` | NIST SP 800-53 — Security and Privacy Controls | https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final |
| `NIST-800-88` | NIST SP 800-88 — Media Sanitization | https://csrc.nist.gov/pubs/sp/800/88/r1/final |
| `NIST-800-92` | NIST SP 800-92 — Computer Security Log Management | https://csrc.nist.gov/pubs/sp/800/92/final |
| `LETSENCRYPT` | Let's Encrypt Documentation | https://letsencrypt.org/docs/ |
| `ACME-RFC` | RFC 8555 — ACME | https://datatracker.ietf.org/doc/html/rfc8555 |
| `OPENSSH-MANPAGES` | OpenSSH man pages | https://www.openssh.com/manual.html |

---

## 9. Performance, monitoring, observability

| ID | Titolo | URL |
|---|---|---|
| `BRENDAN-USE` | The USE Method (Brendan Gregg) | https://www.brendangregg.com/usemethod.html |
| `RED-METHOD` | The RED Method (Tom Wilkie) | https://www.weave.works/blog/the-red-method-key-metrics-for-microservices-architecture/ |
| `IOSTAT-MAN` | iostat(1) man page (sysstat) | https://manpages.debian.org/bookworm/sysstat/iostat.1.en.html |
| `ZABBIX-DOCS` | Zabbix Documentation | https://www.zabbix.com/documentation/current/ |
| `GRAFANA-DOCS` | Grafana Documentation | https://grafana.com/docs/ |
| `PROM-DOCS` | Prometheus Documentation | https://prometheus.io/docs/introduction/overview/ |
| `OTEL-DOCS` | OpenTelemetry Documentation | https://opentelemetry.io/docs/ |

---

## 10. Database — replica per cutover

| ID | Titolo | URL |
|---|---|---|
| `PG-REPL` | PostgreSQL — Streaming Replication | https://www.postgresql.org/docs/current/warm-standby.html#STREAMING-REPLICATION |
| `MYSQL-REPL` | MySQL — Replication | https://dev.mysql.com/doc/refman/8.0/en/replication.html |
| `MARIADB-REPL` | MariaDB — Replication overview | https://mariadb.com/kb/en/replication-overview/ |
| `MSSQL-AG` | SQL Server — Always On Availability Groups | https://learn.microsoft.com/en-us/sql/database-engine/availability-groups/windows/overview-of-always-on-availability-groups-sql-server |

---

## 11. CVE rilevanti per il periodo del corso

| ID | Sintesi | Rilevanza per il corso |
|---|---|---|
| `CVE-2024-37085` | ESXi — bypass di Active Directory authentication che permette escalation a admin in alcuni gruppi AD; sfruttato attivamente dal 2024-07. | Modulo 12 (sicurezza), 17 (troubleshooting). Ricorda perche disabilitare auth AD non hardenizzata su ESXi era importante prima della migrazione. |
| `CVE-2021-21974` | ESXi OpenSLP heap overflow → ESXiArgs ransomware (2023). | Modulo 15 (business case): un esempio di rischio concreto post-EOL. |
| `CVE-2022-31705` | VMware USB descriptor heap overflow (Hertzbleed-class). | Modulo 15. |
| `CVE-2024-3094` | Backdoor in xz-utils (liblzma) — supply chain. | Modulo 12 + 14 (build pipeline trust). |
| `CVE-2021-4034` | pwnkit (Polkit pkexec). | Modulo 12 + 15 (importanza di patching disciplinato). |

Il file `99-CASE-STUDY/broadcom-vmware-2024.md` analizza nel dettaglio l'effetto economico-operativo dell'acquisizione Broadcom-VMware (chiusa 2023-11) sul mercato e sulle migrazioni che hanno motivato questo corso.

---

## 12. Libri (secondaria autorevole)

| ID | Titolo | Autori | Editore | Edizione | ISBN | Note |
|---|---|---|---|---|---|---|
| `BK-MASTER-PVE` | *Mastering Proxmox* | Wasim Ahmed | Packt | 4th (2023) | 978-1801072304 | Libro principale di riferimento PVE |
| `BK-MASTER-KVM` | *Mastering KVM Virtualization* | Humble Devassy Chirammal et al. | Packt | 2nd (2020) | 978-1838828714 | KVM/QEMU/libvirt |
| `BK-FREEBSD-ZFS` | *FreeBSD Mastery: ZFS* | Michael W. Lucas, Allan Jude | Tilted Windmill Press | 2015 | 978-0692452356 | Concetti applicabili a OpenZFS Linux |
| `BK-FREEBSD-AZFS` | *FreeBSD Mastery: Advanced ZFS* | Michael W. Lucas, Allan Jude | Tilted Windmill Press | 2016 | 978-0692688687 | Approfondimento |
| `BK-LEARN-CEPH` | *Learning Ceph* | Anthony D'Atri, Vaibhav Bhembre, Karan Singh | Packt | 2nd (2017) | 978-1787127913 | Ceph cluster |
| `BK-TLPI` | *The Linux Programming Interface* | Michael Kerrisk | No Starch Press | 1st (2010) | 978-1593272203 | Linux syscalls e ipc |
| `BK-TCPIP-1` | *TCP/IP Illustrated, Volume 1* | W. Richard Stevens, Kevin Fall | Addison-Wesley | 2nd (2011) | 978-0321336316 | Networking fondamenta |
| `BK-LINUX-CMD` | *The Linux Command Line* | William Shotts | No Starch Press | 2nd (2019) | 978-1593279523 | Disponibile gratuitamente su linuxcommand.org |
| `BK-USL-HBK` | *UNIX and Linux System Administration Handbook* | Evi Nemeth et al. | Addison-Wesley | 5th (2017) | 978-0134277554 | Bibbia sysadmin |
| `BK-SRE-BOOK` | *Site Reliability Engineering* | Beyer, Jones, Petoff, Murphy (eds.) | O'Reilly | 1st (2016) | 978-1491929124 | SLO/SLI, postmortem, capacity (per moduli 13, 17) |

---

## 13. Talk e conferenze (secondaria autorevole)

| ID | Titolo | Speaker | Conferenza | Anno | URL |
|---|---|---|---|---|---|
| `TALK-PVE-FOSDEM-24` | Proxmox VE 8.x roadmap | Proxmox team | FOSDEM 2024 | 2024 | https://fosdem.org/2024/schedule/event/fosdem-2024-2229-proxmox-virtual-environment-8/ |
| `TALK-CEPH-CEPHA` | Ceph design and operations | Sage Weil et al. | Cephalocon | varia | https://ceph.io/en/community/events/ |
| `TALK-USE-METHOD` | Performance methodologies | Brendan Gregg | USENIX LISA | 2014 | https://www.brendangregg.com/usemethod.html |
| `TALK-ZFS-ALLAN` | ZFS internals series | Allan Jude | varie | 2018-2024 | https://www.youtube.com/@AllanJude |

---

## 14. Tool e CLI (citabili come fonte di verita per sintassi)

| Tool | Pacchetto Debian/Ubuntu | Riferimento |
|---|---|---|
| `qemu-img` | `qemu-utils` | `QEMU-IMG` |
| `virt-v2v` | `virt-v2v libguestfs-tools` | `V2V-MAN` |
| `ovftool` | Download manuale Broadcom | https://developer.vmware.com/web/tool/ovf-tool/ |
| `govc` | https://github.com/vmware/govmomi/releases | https://github.com/vmware/govmomi |
| `pvesh` | incluso in Proxmox VE | `PVE-API` |
| `vzdump` | incluso in Proxmox VE | `PVE-ADMIN` (cap. Backup) |
| `proxmox-backup-client` | `proxmox-backup-client` | `PBS-DOCS` |
| `zfs/zpool` | `zfsutils-linux` | `OPENZFS-MAN` |
| `ceph` | `pveceph install` (su PVE) | `CEPH-DOCS` |
| `terraform` | https://www.terraform.io/downloads | `TERRAFORM-PROV` |
| `ansible` | `ansible-core` (apt) | `ANSIBLE-PVE` |

---

## 15. Convenzioni di citazione interne

Nel testo di un modulo, citare con identificatore tra parentesi quadre:

> «Il quorum richiede maggioranza assoluta `(N/2)+1` [PVE-CLUSTER].»
> «virt-v2v inietta i driver VirtIO automaticamente per i guest Windows supportati [V2V-MAN].»

Quando si cita un comando o flag specifico, includere anche la versione del tool quando il comportamento e cambiato fra versioni:

> «`qemu-img convert -p -W` (parallelismo, da QEMU 5.1+) [QEMU-IMG].»

Per i CVE, usare la sintassi MITRE: `CVE-YYYY-NNNN`. Per gli RFC, `RFC NNNN`. Per i bug di Proxmox, `Proxmox bug #NNNN` con link a `PVE-BUGZILLA`.

---

## 16. Politica di aggiornamento di questo file

- Quando un modulo cita una nuova fonte primaria, aggiungerla qui con un ID stabile.
- Verificare i link al primo utilizzo (`curl -s -o /dev/null -w "%{http_code}" -L --max-time 12 <url>` deve restituire 200, eventuali 301/302 sono accettabili se il redirect punta a contenuto equivalente).
- Aggiornare la data di "Ultimo aggiornamento" all'inizio del file ad ogni modifica significativa.
- Se una fonte cambia URL canonico (es. dominio Broadcom dopo l'acquisizione di VMware), aggiornare l'URL e annotare l'URL storico.
- Quando un libro esce in nuova edizione, aggiungere la nuova riga senza rimuovere la vecchia (se l'edizione vecchia e stata effettivamente citata in qualche modulo).

---

## 17. Verifiche fatte il 2026-04-26

Verifica HEAD `curl -s -o /dev/null -w "%{http_code}" -L --max-time 12 <url>`:

| URL | HTTP |
|---|---|
| pve.proxmox.com/wiki/Main_Page | 200 |
| pve.proxmox.com/pve-docs/pve-admin-guide.html | 200 |
| pve.proxmox.com/pve-docs/api-viewer/ | 200 |
| pbs.proxmox.com/docs/ | 200 |
| qemu.org/docs/master/ | 200 |
| libguestfs.org/virt-v2v.1.html | 200 |
| linux-kvm.org/page/Documents | 200 |
| openzfs.github.io/openzfs-docs/ | 200 |
| docs.ceph.com/en/latest/ | 200 |
| corosync.github.io/corosync/ | 200 |
| docs.openvswitch.org/en/latest/ | 200 |
| docs.vmware.com/en/VMware-vSphere/ | 200 |
| knowledge.broadcom.com/external/article?legacyId=2143832 | 200 |
| datatracker.ietf.org/doc/html/rfc4253 | 200 |
| datatracker.ietf.org/doc/html/rfc1918 | 200 |
