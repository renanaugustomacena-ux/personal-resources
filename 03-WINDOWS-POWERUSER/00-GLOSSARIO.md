# Glossario — Amministrazione Windows Enterprise

> **Aggiornamento:** 2026-05-23
> **Nota:** Termini introdotti nei moduli del corso. Per definizioni estese, consultare il modulo indicato.

---

## A

| Termine | Definizione | Modulo |
|---------|-------------|--------|
| **ACL** | Access Control List — lista di ACE che definisce permessi su un oggetto (file, registro, AD). | 08 |
| **ACE** | Access Control Entry — singola voce in una ACL (allow/deny + SID + permission). | 08 |
| **AD CS** | Active Directory Certificate Services — ruolo server per PKI enterprise. | 11, 28 |
| **AD DS** | Active Directory Domain Services — servizio di directory per identità, autenticazione e policy. | 01 |
| **AD FS** | Active Directory Federation Services — identity federation on-premises (SAML, WS-Fed). | 13, 30 |
| **AD LDS** | Active Directory Lightweight Directory Services — LDAP standalone senza domain. | 01 |
| **ADK** | Assessment and Deployment Kit — tool per imaging e deployment Windows. | 12 |
| **AdminSDHolder** | Oggetto AD che protegge i gruppi privilegiati riscrivendo ACL ogni 60 minuti. | 25, 29 |
| **ADMX/ADML** | Template XML per Group Policy (ADMX = definizione, ADML = localizzazione). | 21 |
| **ADMT** | Active Directory Migration Tool — migrazione utenti/gruppi/computer tra domini/forest. | 33 |
| **AGDLP** | Account → Global → Domain Local → Permissions — pattern di nesting gruppi AD. | 01, 08 |
| **AIA** | Authority Information Access — estensione certificato con URL per download CA issuer. | 28 |
| **AppLocker** | Policy di application whitelisting basata su regole (publisher, path, hash). | 24 |
| **ARR** | Application Request Routing — modulo IIS per reverse proxy e load balancing L7. | 31 |
| **ASR** | Attack Surface Reduction — regole Defender che bloccano comportamenti malware comuni. | 24 |
| **Attestation** | Verifica identità/integrità di un host, usata in HGS per Shielded VMs. | 23 |
| **Autopilot** | Windows Autopilot — provisioning zero-touch per device Intune. | 32 |

## B

| Termine | Definizione | Modulo |
|---------|-------------|--------|
| **BCD** | Boot Configuration Data — database di configurazione boot (sostituisce boot.ini). | 19 |
| **BitLocker** | Full Volume Encryption con AES-256 e protezione TPM/PIN/chiave USB. | 05 |
| **BloodHound** | Tool open-source per analisi attack path in Active Directory (graph-based). | 29 |
| **BPA** | Best Practices Analyzer — tool integrato in Server Manager per audit configurazione. | 20 |
| **Bridgehead server** | DC designato per replicazione inter-site; eletto da ISTG. | 25 |
| **BYOD** | Bring Your Own Device — dispositivi personali gestiti con MAM (senza MDM full). | 26, 32 |

## C

| Termine | Definizione | Modulo |
|---------|-------------|--------|
| **CA** | Certification Authority — entità che emette e firma certificati digitali. | 11, 28 |
| **CAPolicy.inf** | File di configurazione CA che definisce parametri durante installazione AD CS. | 28 |
| **CAU** | Cluster-Aware Updating — patching orchestrato su nodi cluster senza downtime. | 27 |
| **CDP** | CRL Distribution Point — URL dove è pubblicata la CRL (LDAP, HTTP, file). | 28 |
| **Certipy** | Tool Python per enumerazione e attacco AD CS (ESC1-ESC8). | 28 |
| **Checkpoint** | Snapshot di VM Hyper-V — standard (include RAM) o production (VSS-based). | 23 |
| **CIS Benchmark** | Center for Internet Security — baseline di hardening per OS e servizi. | 29 |
| **Cloud Witness** | Quorum witness basato su Azure Blob Storage per cluster senza SAN condivisa. | 27 |
| **Conditional Access** | Policy Entra ID che valuta condizioni (device, location, risk) per grant/block accesso. | 26, 30 |
| **Configuration Manager** | SCCM/MECM — piattaforma endpoint management on-premises (OSD, software, compliance). | 12 |
| **Constrained Delegation** | Kerberos delegation limitata a servizi specifici (S4U2Proxy). | 01, 25 |
| **CRL** | Certificate Revocation List — lista firmata di certificati revocati prima della scadenza. | 28 |
| **CSV** | Cluster Shared Volumes — filesystem condiviso che permette accesso simultaneo multi-nodo. | 27 |

## D

| Termine | Definizione | Modulo |
|---------|-------------|--------|
| **DC** | Domain Controller — server che ospita replica di AD DS e autentica utenti. | 01 |
| **dcdiag** | Tool diagnostico che verifica salute di un DC (DNS, replication, FSMO, etc.). | 01, 19 |
| **DDA** | Discrete Device Assignment — passthrough GPU/NVMe diretto a VM Hyper-V. | 23 |
| **Defender for Endpoint** | EDR cloud Microsoft — rilevamento, investigation, response su endpoint. | 24 |
| **DFS** | Distributed File System — namespace unificato (DFS-N) e replicazione file (DFS-R). | 07 |
| **DHCP** | Dynamic Host Configuration Protocol — assegnazione automatica IP (scope, reservation, failover). | 03, 06 |
| **DISM** | Deployment Image Servicing and Management — tool per servicing immagini WIM/VHD. | 12 |
| **DNS** | Domain Name System — risoluzione nomi; in AD è AD-integrated con zone replicate. | 03, 06 |
| **DNSSEC** | DNS Security Extensions — firma crittografica di zone DNS contro spoofing. | 06 |
| **DSC** | Desired State Configuration — framework PowerShell per configuration-as-code. | 22 |
| **DSRM** | Directory Services Restore Mode — modalità boot per restore offline di AD database. | 34 |

## E

| Termine | Definizione | Modulo |
|---------|-------------|--------|
| **EAP-TLS** | Extensible Authentication Protocol con TLS — autenticazione 802.1X basata su certificato. | 28 |
| **EDITF_ATTRIBUTESUBJECTALTNAME2** | Flag CA pericoloso che permette al richiedente di specificare SAN arbitrario (ESC6). | 28 |
| **EKU** | Extended Key Usage — estensione certificato che limita gli usi (server auth, client auth, code signing). | 28 |
| **Entra Connect** | Sync engine tra AD on-premises e Entra ID (ex Azure AD Connect). | 13, 30 |
| **Entra ID** | Microsoft Entra ID (ex Azure AD) — identity provider cloud per Microsoft 365 e Azure. | 13, 30 |
| **ESAE** | Enhanced Security Admin Environment — architettura Red Forest per isolamento Tier 0. | 25, 29 |
| **ESC1-ESC8** | Certified Pre-Owned attack vectors contro AD CS (template misconfiguration, NTLM relay, etc.). | 28 |
| **EternalBlue** | Exploit SMBv1 (CVE-2017-0144) usato da WannaCry e NotPetya. | CS |
| **Event ID** | Identificatore numerico per eventi Windows (4624=logon, 4688=process creation, etc.). | 19 |

## F

| Termine | Definizione | Modulo |
|---------|-------------|--------|
| **Failover Clustering** | Ruolo Windows Server per alta disponibilità con failover automatico tra nodi. | 27 |
| **Fine-Grained Password Policy** | Password policy granulare applicata a gruppi/utenti specifici (PSO) invece che a dominio intero. | 01, 29 |
| **Forest** | Container top-level AD — confine di sicurezza, schema e configuration condivisi. | 01, 25 |
| **Forest trust** | Trust transitivo bidirezionale tra due forest AD. | 33 |
| **FSMO** | Flexible Single-Master Operations — 5 ruoli unici in AD (Schema, Domain Naming, PDC, RID, Infrastructure). | 01, 25 |
| **FSLogix** | Profile container per virtualizzazione profili (VHD/VHDX mounted at logon). | 16 |

## G

| Termine | Definizione | Modulo |
|---------|-------------|--------|
| **GC** | Global Catalog — replica parziale di tutti gli oggetti nella forest; porta 3268/3269. | 01, 25 |
| **gMSA** | Group Managed Service Account — account servizio con password auto-rotata da AD. | 01, 29 |
| **GPO** | Group Policy Object — collezione di policy settings linkati a site/domain/OU. | 21 |
| **GPP** | Group Policy Preferences — preference items (drive map, printer, registry, scheduled task). | 21 |
| **`gpresult /h`** | Genera report HTML delle GPO applicate a un computer/utente. | 21 |
| **`gpupdate /force`** | Forza rielaborazione immediata di tutte le GPO. | 21 |

## H

| Termine | Definizione | Modulo |
|---------|-------------|--------|
| **HGS** | Host Guardian Service — servizio attestation per Shielded VMs. | 23 |
| **Hive** | File di registro Windows (HKLM\SYSTEM, HKLM\SOFTWARE, HKCU, etc.). | 04 |
| **HSM** | Hardware Security Module — dispositivo hardware per protezione chiavi crittografiche. | 28 |
| **HTTP.sys** | Kernel-mode HTTP listener usato da IIS e altri servizi Windows. | 31 |
| **Hyper-V** | Hypervisor type-1 Microsoft integrato in Windows Server e Windows Pro/Enterprise. | 23 |
| **Hyper-V Replica** | Replicazione asincrona di VM tra host Hyper-V per DR (RPO 30s-15min). | 23 |

## I

| Termine | Definizione | Modulo |
|---------|-------------|--------|
| **IIS** | Internet Information Services — web server Microsoft (HTTP/HTTPS, FTP, WebDAV). | 31 |
| **Intune** | Microsoft Intune — piattaforma MDM/MAM cloud per gestione endpoint moderno. | 26, 32 |
| **IPsec** | Internet Protocol Security — encryption e autenticazione a livello network (transport/tunnel mode). | 06 |
| **iSCSI** | Internet Small Computer Systems Interface — storage a blocchi su rete IP. | 07 |
| **ISTG** | Intersite Topology Generator — processo DC che seleziona bridgehead server. | 25 |

## J

| Termine | Definizione | Modulo |
|---------|-------------|--------|
| **JEA** | Just Enough Administration — endpoint PowerShell con permessi granulari role-based. | 22 |

## K

| Termine | Definizione | Modulo |
|---------|-------------|--------|
| **KCC** | Knowledge Consistency Checker — processo AD che genera automaticamente la topology di replicazione. | 25 |
| **Kerberos** | Protocollo di autenticazione basato su ticket (TGT, service ticket, delegation). | 01 |
| **KMS** | Key Management Service — attivazione volume license Windows/Office. | 03 |
| **KRA** | Key Recovery Agent — certificato che permette recovery di chiavi private archiviate dalla CA. | 28 |

## L

| Termine | Definizione | Modulo |
|---------|-------------|--------|
| **LAPS** | Local Administrator Password Solution — rotazione automatica password admin locale via AD/Entra. | 05, 29 |
| **LDAP** | Lightweight Directory Access Protocol — protocollo accesso directory (porta 389/636). | 01 |
| **Live Migration** | Spostamento di VM in esecuzione tra host Hyper-V senza downtime. | 23, 27 |
| **Loopback Processing** | GPO setting che applica user configuration basata sul computer (replace/merge mode). | 21 |
| **LSA Protection** | RunAsPPL — protezione del processo LSASS contro dump credenziali. | 29 |

## M

| Termine | Definizione | Modulo |
|---------|-------------|--------|
| **MAM** | Mobile Application Management — protezione dati app senza gestione dispositivo completo. | 32 |
| **MBAM** | Microsoft BitLocker Administration and Monitoring — gestione centralizzata BitLocker. | 05 |
| **MDM** | Mobile Device Management — gestione completa del dispositivo (enrollment, policy, wipe). | 26, 32 |
| **MDT** | Microsoft Deployment Toolkit — framework gratuito per deployment OS. | 12 |
| **Metadata cleanup** | Rimozione da AD dei metadati di un DC dismesso/distrutto (ntdsutil). | 34 |
| **MFA** | Multi-Factor Authentication — autenticazione con 2+ fattori (password + OTP/biometric). | 30 |
| **Mimikatz** | Tool di estrazione credenziali da memoria LSASS (sekurlsa, lsadump, kerberos). | 29, CS |

## N

| Termine | Definizione | Modulo |
|---------|-------------|--------|
| **NIC Teaming** | Aggregazione di interfacce di rete per throughput e failover (LBFO o SET). | 06 |
| **NLB** | Network Load Balancing — clustering L4 Windows per distribuzione carico. | 06 |
| **NTDS.dit** | File database Active Directory (ESE engine) su ogni DC. | 01, 34 |
| **NTFS** | New Technology File System — filesystem Windows con ACL, journaling, compression, encryption. | 08 |
| **NTLM** | NT LAN Manager — protocollo di autenticazione legacy (challenge-response, no delegation). | 01 |
| **ntdsutil** | Tool CLI per manutenzione AD (FSMO seizure, metadata cleanup, snapshot, DSRM password). | 25, 34 |

## O

| Termine | Definizione | Modulo |
|---------|-------------|--------|
| **OCSP** | Online Certificate Status Protocol — verifica stato certificato in tempo reale (alternativa CRL). | 28 |
| **OCSP Stapling** | Server web che allega risposta OCSP firmata al TLS handshake. | 28, 31 |
| **OSD** | Operating System Deployment — deployment automatizzato OS via SCCM/MDT. | 12 |
| **OU** | Organizational Unit — container AD per organizzare oggetti e linkare GPO. | 01 |

## P

| Termine | Definizione | Modulo |
|---------|-------------|--------|
| **PAW** | Privileged Access Workstation — workstation dedicata per amministrazione Tier 0. | 25, 29 |
| **PCR** | Platform Configuration Registers — registri TPM che misurano integrità boot chain. | 05 |
| **PDC Emulator** | FSMO role — time source, password change, legacy PDC compatibility, GPO central store. | 01, 25 |
| **Pester** | Framework di testing per PowerShell (Describe/Context/It, Should assertions). | 22 |
| **PHS** | Password Hash Sync — sincronizzazione hash password da AD on-prem a Entra ID. | 30 |
| **PIM** | Privileged Identity Management — attivazione just-in-time di ruoli privilegiati in Entra ID. | 30 |
| **PingCastle** | Tool per assessment sicurezza Active Directory (scoring, vulnerability report). | 29 |
| **PKI** | Public Key Infrastructure — infrastruttura per gestione certificati digitali (CA, CRL, trust chain). | 28 |
| **Protected Users** | Gruppo AD che disabilita NTLM, delegation, e caching credenziali per i membri. | 29 |
| **PSO** | Password Settings Object — fine-grained password policy applicata a gruppo/utente specifico. | 01 |
| **PSRemoting** | PowerShell Remoting — esecuzione comandi remota via WinRM (WS-Man) o SSH. | 02, 22 |
| **PTA** | Pass-Through Authentication — autenticazione on-prem per Entra ID senza sync hash. | 30 |

## Q

| Termine | Definizione | Modulo |
|---------|-------------|--------|
| **Quorum** | Meccanismo di voto che determina quanti nodi cluster devono essere online per operare. | 27 |

## R

| Termine | Definizione | Modulo |
|---------|-------------|--------|
| **RBAC** | Role-Based Access Control — autorizzazione basata su ruoli anziché utenti individuali. | 08, 22 |
| **RBCD** | Resource-Based Constrained Delegation — delegation configurata sull'oggetto risorsa. | 25 |
| **ReFS** | Resilient File System — filesystem con integrità dati, repair online, ottimizzato per Hyper-V. | 07 |
| **repadmin** | Tool CLI per monitoraggio e troubleshooting replicazione AD. | 01, 25 |
| **RID Master** | FSMO role — allocazione pool RID ai DC per creazione nuovi oggetti AD. | 01, 25 |
| **RODC** | Read-Only Domain Controller — DC senza write, con Password Replication Policy. | 01, 25 |
| **RPO** | Recovery Point Objective — massima perdita dati accettabile (tempo). | 34 |
| **RTO** | Recovery Time Objective — tempo massimo per ripristino servizio. | 34 |

## S

| Termine | Definizione | Modulo |
|---------|-------------|--------|
| **S2D** | Storage Spaces Direct — storage software-defined convergente per cluster. | 07, 27 |
| **SAN** | Subject Alternative Name — estensione certificato con nomi aggiuntivi (DNS, IP, email). | 28 |
| **SCEP** | Simple Certificate Enrollment Protocol — enrollment certificati per device Intune. | 32 |
| **Schema Master** | FSMO role — unico DC autorizzato a modificare lo schema AD. | 01, 25 |
| **Selective Authentication** | Trust setting che richiede permessi espliciti per accesso cross-forest. | 33 |
| **SET** | Switch Embedded Teaming — NIC teaming integrato nel vSwitch Hyper-V. | 23 |
| **Shielded VM** | VM Hyper-V protetta da HGS con vTPM, BitLocker automatico e accesso console limitato. | 23 |
| **SID** | Security Identifier — identificatore unico per ogni principal di sicurezza in Windows/AD. | 01, 08 |
| **SID History** | Attributo AD che preserva SID originale durante migrazione cross-domain. | 33 |
| **Site Link** | Oggetto AD che definisce costo e frequenza replicazione inter-site. | 25 |
| **Sites & Subnets** | Configurazione AD per mapping rete fisica → topologia di replicazione. | 25 |
| **SMB** | Server Message Block — protocollo di condivisione file Windows (3.0+ con encryption). | 06, 29 |
| **SMB Signing** | Firma digitale dei pacchetti SMB contro tampering (man-in-the-middle). | 29 |
| **SNI** | Server Name Indication — estensione TLS per hosting multipli siti HTTPS su un IP. | 31 |
| **SR-IOV** | Single Root I/O Virtualization — bypass hypervisor per NIC ad alte prestazioni in VM. | 23 |
| **SRI** | Subresource Integrity — hash per verificare integrità risorse web caricate da CDN. | 31 |
| **SSO** | Single Sign-On — autenticazione unica per accesso a più applicazioni. | 13, 30 |
| **STIG** | Security Technical Implementation Guide — checklist DISA per hardening DOD. | 29 |
| **Storage Spaces** | Virtualizzazione storage Windows con mirroring, parity, tiering. | 07 |
| **Sysinternals** | Suite Microsoft di tool avanzati per diagnostica (Process Monitor, ProcExp, Autoruns, etc.). | 19 |
| **System State** | Backup che include AD database, SYSVOL, registry, boot files, certificate store. | 15, 34 |

## T

| Termine | Definizione | Modulo |
|---------|-------------|--------|
| **Tier 0/1/2** | Modello di separazione amministrativa: T0=identity (DC, CA), T1=server, T2=workstation. | 25, 29 |
| **TLS** | Transport Layer Security — protocollo crittografico per comunicazione sicura (1.2, 1.3). | 31 |
| **Tombstone** | Oggetto AD marcato per cancellazione; mantenuto per tombstoneLifetime (default 180 giorni). | 25, 34 |
| **TPM** | Trusted Platform Module — chip hardware per operazioni crittografiche (BitLocker, Credential Guard). | 05 |
| **Trust** | Relazione tra domini/forest AD che permette autenticazione cross-boundary. | 33 |

## U

| Termine | Definizione | Modulo |
|---------|-------------|--------|
| **UAC** | User Account Control — elevazione privilegi con prompt di consenso/credenziali. | 05 |
| **URL Rewrite** | Modulo IIS per riscrittura URL (redirect, rewrite, reverse proxy rules). | 31 |

## V

| Termine | Definizione | Modulo |
|---------|-------------|--------|
| **VHDX** | Virtual Hard Disk eXtended — formato disco virtuale Hyper-V (max 64 TB, log-based resiliency). | 23 |
| **VSS** | Volume Shadow Copy Service — framework per snapshot consistenti (backup, system restore). | 15 |
| **vSwitch** | Virtual Switch Hyper-V — switch di rete virtuale (external, internal, private). | 23 |
| **vTPM** | Virtual TPM — TPM emulato per VM Hyper-V (richiede Gen2 + Shielded VM o attestation). | 23 |

## W

| Termine | Definizione | Modulo |
|---------|-------------|--------|
| **WAC** | Windows Admin Center — console web di amministrazione centralizzata. | 20 |
| **WDAC** | Windows Defender Application Control — application whitelisting kernel-mode (code integrity). | 24 |
| **WDS** | Windows Deployment Services — PXE boot per deployment OS via rete. | 03, 12 |
| **WHQL** | Windows Hardware Quality Labs — certificazione driver Microsoft (signing obbligatorio). | 18 |
| **WinRM** | Windows Remote Management — implementazione Microsoft di WS-Management (porta 5985/5986). | 02, 22 |
| **WMI** | Windows Management Instrumentation — interfaccia di gestione e query (CIM-based). | 09 |
| **WMI Filter** | Filtro GPO basato su query WMI (es. applica solo a laptop, solo a Windows 11). | 21 |
| **WSL** | Windows Subsystem for Linux — layer di compatibilità per esecuzione binari Linux su Windows. | 17 |
| **WSUS** | Windows Server Update Services — server on-premises per gestione patch Microsoft. | 03, 10 |
| **WUFB** | Windows Update for Business — gestione aggiornamenti via cloud (ring deployment, deferral). | 10 |

---

## Abbreviazioni Case Study

| Termine | Definizione | Case Study |
|---------|-------------|------------|
| **EternalBlue** | Exploit SMBv1 (CVE-2017-0144) usato da WannaCry e NotPetya per propagazione laterale. | NotPetya |
| **MEDoc** | Software contabile ucraino il cui update server è stato compromesso per distribuire NotPetya. | NotPetya |
| **MSA Token** | Microsoft Account token — chiave crittografica di firma token compromessa da Storm-0558. | Storm-0558 |
| **Storm-0558** | Threat actor state-sponsored cinese che ha compromesso chiave di firma Microsoft (2023). | Storm-0558 |

---

> **Conteggio termini:** ~170
> **Ultimo aggiornamento:** 2026-05-23
