# Rete Windows — Guida Completa

> **Modulo 06** · **Aggiornamento:** 2026-05-22

| Campo | Valore |
|---|---|
| **Modulo del corso** | Amministrazione Windows enterprise |
| **Prerequisiti** | Padronanza di PowerShell base (→ `02-powershell.md`), conoscenza di Active Directory (→ `01-active-directory.md`), familiarità con lo storage Windows (→ `07-storage-windows.md`) |
| **Obiettivi di apprendimento** | 1) Configurare e diagnosticare lo stack TCP/IP di Windows con cmdlet moderni (`Get-NetAdapter`, `Get-NetIPConfiguration`, `Test-NetConnection`) · 2) Amministrare DNS, DHCP e NIC teaming/SET in ambienti server e Hyper-V · 3) Configurare SMB 3.x con encryption, signing, Multichannel e SMB over QUIC · 4) Implementare Windows Firewall con regole avanzate e profili · 5) Progettare soluzioni di accesso remoto (Always On VPN, DirectAccess, RRAS) e NPS/RADIUS · 6) Comprendere SDN (Software Defined Networking) e tuning TCP/IP per workload ad alte prestazioni |
| **Tempo stimato** | lettura 90 min · lab 120 min |
| **Livello** | Proficient |
| **Ultimo aggiornamento** | 2026-05-24 |

## Idee guida
1. **`Get-NetAdapter`, `Get-NetIPConfiguration` cmdlet PS modern.**
2. **Windows Firewall via `Set-NetFirewallRule`.**
3. **NIC teaming via `New-NetLbfoTeam`.**
4. **DNS server roles, scavenging, conditional forwarders.**
5. **Stack di rete Windows: NDIS → WFP → TCP/IP → Winsock → SMB.**
6. **SMB 3.x: encryption, signing, Multichannel, Direct (RDMA).**
7. **Hyper-V networking: virtual switch, SET, VLAN tagging.**
8. **Remote access: Always On VPN, DirectAccess, RRAS.**
9. **Network Policy Server (NPS): RADIUS, 802.1X.**
10. **QoS, BranchCache, IPv6 — architettura completa.**
11. **SMB over QUIC: accesso file remoto senza VPN via UDP 443 (Server 2025+).**
12. **SDN (Software Defined Networking): Network Controller, tag-based segmentation, SDN Multisite.**
13. **TCP/IP tuning: autotuning levels, RSS, RSC, congestion provider, ECN.**
14. **DNS-over-HTTPS (DoH): configurazione server e client in ambienti enterprise.**


## Indice

- [Panoramica — Architettura dello Stack di Rete](#panoramica--architettura-dello-stack-di-rete)
- [TCP/IP Configurazione](#tcpip-configurazione)
- [IPv6 su Windows](#ipv6-su-windows)
- [DNS Client — Risoluzione e Troubleshooting](#dns-client--risoluzione-e-troubleshooting)
- [Protocollo SMB](#protocollo-smb)
- [Configurazione Avanzata NIC e Teaming](#configurazione-avanzata-nic-e-teaming)
- [Hyper-V Networking](#hyper-v-networking)
- [Windows Firewall — Deep Dive](#windows-firewall--deep-dive)
- [Strumenti di Troubleshooting Rete](#strumenti-di-troubleshooting-rete)
- [Remote Access — VPN e DirectAccess](#remote-access--vpn-e-directaccess)
- [Network Policy Server (NPS) e RADIUS](#network-policy-server-nps-e-radius)
- [BranchCache](#branchcache)
- [Quality of Service (QoS)](#quality-of-service-qos)
- [Network Monitoring e Packet Capture](#network-monitoring-e-packet-capture)
- [Network Security Hardening](#network-security-hardening)
- [Software Defined Networking (SDN)](#software-defined-networking-sdn)
- [Tuning TCP/IP per Workload ad Alte Prestazioni](#tuning-tcpip-per-workload-ad-alte-prestazioni)
- [WINS e NetBIOS](#wins-e-netbios)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)

---

## Panoramica — Architettura dello Stack di Rete

La configurazione di rete in Windows Server e Client coinvolge TCP/IP, risoluzione DNS (critica per Active Directory), NIC avanzate (teaming, offloading), analisi del traffico e gestione dei protocolli legacy (NetBIOS, WINS). L'amministratore deve padroneggiare sia PowerShell che gli strumenti GUI per diagnosticare e risolvere problemi di rete.

### Stack di Rete Windows — Livelli Architetturali

Lo stack di rete Windows e' organizzato in livelli distinti, dalla scheda fisica fino all'applicazione user-mode.

```
┌──────────────────────────────────────────────────────┐
│                   APPLICAZIONE                       │
│           (browser, SMB client, RDP, ecc.)           │
├──────────────────────────────────────────────────────┤
│                    WINSOCK (ws2_32.dll)               │
│         API socket Berkeley-compatibile              │
│         TDI (legacy) / WSK (kernel-mode)             │
├──────────────────────────────────────────────────────┤
│             AFD.SYS  (Ancillary Function Driver)     │
│         Buffer management, connection tracking       │
├──────────────────────────────────────────────────────┤
│             TCP/IP STACK  (tcpip.sys)                 │
│         TCP, UDP, ICMP, IP routing                   │
│         Chimney Offload Engine (deprecato)           │
├──────────────────────────────────────────────────────┤
│        WFP (Windows Filtering Platform)              │
│         Filtraggio pacchetti, IPsec, NAT             │
│         Base per Windows Firewall                    │
├──────────────────────────────────────────────────────┤
│             NDIS 6.x (ndis.sys)                      │
│         Network Driver Interface Specification       │
│         Miniport drivers, protocol drivers,          │
│         lightweight filter drivers                   │
├──────────────────────────────────────────────────────┤
│          NIC DRIVER (miniport)                       │
│          Hardware / firmware NIC                      │
└──────────────────────────────────────────────────────┘
```

### NDIS (Network Driver Interface Specification)

NDIS e' il framework che permette ai driver di rete di comunicare con lo stack TCP/IP e viceversa. La versione attuale e' NDIS 6.80+ (Windows Server 2022 / Windows 11).

- **Miniport driver**: interfaccia diretta con l'hardware NIC. Gestisce invio/ricezione pacchetti, interrupt, DMA.
- **Protocol driver**: si registra sopra NDIS per ricevere frame (es. tcpip.sys).
- **Filter driver** (lightweight): si inserisce tra miniport e protocol per ispezionare/modificare pacchetti. Usato da antivirus, monitoring, NIC teaming.

```powershell
# Visualizzare binding NDIS
Get-NetAdapterBinding -Name "Ethernet"
# Visualizzare tutti i componenti bound
Get-NetAdapterBinding | Format-Table Name, ComponentID, DisplayName, Enabled

# Disabilitare un binding specifico (es. IPv6)
Disable-NetAdapterBinding -Name "Ethernet" -ComponentID ms_tcpip6

# Ordine dei binding (priorita' protocolli)
# GUI: ncpa.cpl → Advanced → Advanced Settings → Adapters and Bindings
```

### WFP (Windows Filtering Platform)

WFP e' il motore di filtraggio kernel-mode che sostituisce il vecchio TDI filter. Tutti i componenti di sicurezza di rete lo attraversano:

- **Windows Firewall** (mpssvc) utilizza WFP per applicare regole.
- **IPsec** si implementa tramite WFP callout.
- **Routing e NAT** sfruttano i layer WFP.
- **Antivirus/EDR** registrano callout WFP per ispezione deep-packet.

```
Layer WFP principali:
- FWPM_LAYER_INBOUND_TRANSPORT_V4    → pacchetti TCP/UDP in ingresso
- FWPM_LAYER_OUTBOUND_TRANSPORT_V4   → pacchetti TCP/UDP in uscita
- FWPM_LAYER_ALE_AUTH_CONNECT_V4     → autorizzazione nuove connessioni
- FWPM_LAYER_ALE_AUTH_RECV_ACCEPT_V4 → autorizzazione connessioni in ingresso
- FWPM_LAYER_STREAM_V4               → ispezione dati stream TCP
```

```powershell
# Visualizzare filtri WFP attivi (richiede netsh)
netsh wfp show filters

# Dump stato WFP (XML, utile per debug firewall)
netsh wfp show state

# Visualizzare provider WFP registrati
netsh wfp show providers
```

### TCP/IP Stack (tcpip.sys)

Il driver `tcpip.sys` implementa:

- **IP routing**: table lookup, forwarding, ECMP.
- **TCP**: gestione connessioni, finestre di congestione, Selective ACK (SACK), ECN, autotuning.
- **UDP**: datagrammi, multicast membership.
- **ICMP**: echo request/reply, destination unreachable, redirect.
- **Raw sockets**: accesso diretto per strumenti diagnostici.

```powershell
# TCP autotuning level
Get-NetTCPSetting | Select-Object SettingName, AutoTuningLevelLocal, ScalingHeuristics
# Modificare autotuning (raramente necessario)
Set-NetTCPSetting -SettingName InternetCustom -AutoTuningLevelLocal Normal

# Parametri TCP globali
netsh interface tcp show global
# Chimney Offload (deprecato da Windows Server 2016)
# TCP Receive Window Auto-Tuning
# ECN Capability
# Timestamps
```

### Winsock

Winsock (`ws2_32.dll`) e' l'API socket per applicazioni user-mode. Supporta:

- Socket TCP/UDP standard (Berkeley-style).
- WSAAsyncSelect / WSAEventSelect per I/O asincrono.
- Winsock Kernel (WSK) per driver kernel-mode.
- Layered Service Provider (LSP) — deprecato, sostituito da WFP.

```powershell
# Stato del catalogo Winsock
netsh winsock show catalog

# Reset Winsock (se LSP corrotti causano problemi di rete)
netsh winsock reset
# RICHIEDE REBOOT — resetta il catalogo Winsock ai default

# Verificare LSP installati (strumenti diagnostici)
# Autoruns (Sysinternals) → tab Winsock Providers
```

---

## TCP/IP Configurazione

### Configurazione Base

```powershell
# Visualizzare configurazione
Get-NetIPConfiguration
Get-NetIPAddress | Where-Object AddressFamily -eq IPv4 |
    Select-Object InterfaceAlias, IPAddress, PrefixLength

# Configurazione statica
New-NetIPAddress -InterfaceAlias "Ethernet" -IPAddress 192.168.10.20 `
    -PrefixLength 24 -DefaultGateway 192.168.10.1

# DNS
Set-DnsClientServerAddress -InterfaceAlias "Ethernet" `
    -ServerAddresses 192.168.10.10, 192.168.10.11

# Rimuovere IP
Remove-NetIPAddress -InterfaceAlias "Ethernet" -IPAddress 192.168.10.20 -Confirm:$false
Remove-NetRoute -InterfaceAlias "Ethernet" -DestinationPrefix 0.0.0.0/0 -Confirm:$false

# DHCP
Set-NetIPInterface -InterfaceAlias "Ethernet" -Dhcp Enabled
Set-DnsClientServerAddress -InterfaceAlias "Ethernet" -ResetServerAddresses

# Rinominare adattatore
Rename-NetAdapter -Name "Ethernet 2" -NewName "Management"

# Disabilitare/Abilitare
Disable-NetAdapter -Name "WiFi" -Confirm:$false
Enable-NetAdapter -Name "WiFi"

# Informazioni dettagliate adattatore
Get-NetAdapter | Select-Object Name, InterfaceDescription, Status, LinkSpeed, MacAddress
Get-NetAdapterAdvancedProperty -Name "Ethernet"
```

### Configurazione con netsh (CMD classico)

```cmd
:: Visualizzare configurazione
netsh interface ipv4 show config

:: Configurazione IP statica
netsh interface ipv4 set address "Ethernet" static 192.168.10.20 255.255.255.0 192.168.10.1

:: Configurazione DNS
netsh interface ipv4 set dnsservers "Ethernet" static 192.168.10.10 primary
netsh interface ipv4 add dnsservers "Ethernet" 192.168.10.11 index=2

:: Tornare a DHCP
netsh interface ipv4 set address "Ethernet" dhcp
netsh interface ipv4 set dnsservers "Ethernet" dhcp

:: Visualizzare tutte le interfacce
netsh interface show interface

:: Disabilitare/Abilitare interfaccia
netsh interface set interface "Ethernet" admin=disable
netsh interface set interface "Ethernet" admin=enable

:: Esportare/Importare configurazione (backup)
netsh -c interface dump > C:\Temp\netconfig-backup.txt
netsh -f C:\Temp\netconfig-backup.txt
```

### Comportamento DHCP Client

Il client DHCP di Windows segue il processo DORA (Discover, Offer, Request, Acknowledge):

```
1. DHCP Discover  → broadcast 255.255.255.255 (porta UDP 67)
2. DHCP Offer     → server risponde con IP proposto
3. DHCP Request   → client richiede l'IP offerto
4. DHCP Acknowledge → server conferma il lease

Rinnovo:
- Al 50% del lease time → unicast DHCP Request al server originale
- Al 87.5% del lease   → broadcast DHCP Request (qualsiasi server)
- Lease scaduto         → torna a DHCP Discover
```

```powershell
# Stato DHCP dell'interfaccia
Get-NetIPInterface -AddressFamily IPv4 | Select-Object InterfaceAlias, Dhcp

# Rilasciare e rinnovare lease DHCP
ipconfig /release
ipconfig /renew

# Rilasciare/rinnovare su interfaccia specifica
ipconfig /release "Ethernet"
ipconfig /renew "Ethernet"

# Visualizzare lease DHCP corrente
Get-NetIPAddress -InterfaceAlias "Ethernet" -AddressFamily IPv4 |
    Select-Object IPAddress, PrefixLength, PrefixOrigin, SuffixOrigin, ValidLifetime

# APIPA (Automatic Private IP Addressing)
# Se il client non ottiene risposta DHCP, assegna un IP nella subnet 169.254.0.0/16
# Per disabilitare APIPA (forza il client a riprovare senza fallback):
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces\{GUID}" `
    -Name "IPAutoconfigurationEnabled" -Value 0 -PropertyType DWord -Force

# Servizio DHCP Client
Get-Service -Name Dhcp
# Event log DHCP client
Get-WinEvent -LogName "Microsoft-Windows-Dhcp-Client/Operational" -MaxEvents 20
```

### Routing

```powershell
# Tabella routing
Get-NetRoute | Where-Object DestinationPrefix -ne "::/0" |
    Format-Table DestinationPrefix, NextHop, RouteMetric, InterfaceAlias -AutoSize

# Aggiungere route statica
New-NetRoute -DestinationPrefix "10.10.0.0/16" -NextHop 192.168.10.1 `
    -InterfaceAlias "Ethernet" -RouteMetric 10

# Route persistente (sopravvive al reboot)
# Le route PowerShell sono persistenti di default

# Abilitare routing (IP forwarding)
Set-NetIPInterface -InterfaceAlias "Ethernet" -Forwarding Enabled

# Verificare route per destinazione specifica
Find-NetRoute -RemoteIPAddress 10.10.20.50

# CMD classico
route print
tracert 8.8.8.8
pathping 8.8.8.8     # Combinazione di tracert + ping statistico
```

### Metriche e Multi-Gateway

```powershell
# Visualizzare metriche interfaccia
Get-NetIPInterface -AddressFamily IPv4 |
    Select-Object InterfaceAlias, InterfaceMetric, Dhcp

# Impostare metrica interfaccia (valore basso = priorita' alta)
Set-NetIPInterface -InterfaceAlias "Ethernet" -InterfaceMetric 10
Set-NetIPInterface -InterfaceAlias "WiFi" -InterfaceMetric 50

# Disabilitare metrica automatica
Set-NetIPInterface -InterfaceAlias "Ethernet" -AutomaticMetric Disabled
Set-NetIPInterface -InterfaceAlias "Ethernet" -InterfaceMetric 10

# Visualizzare default gateway con metrica
Get-NetRoute -DestinationPrefix "0.0.0.0/0" |
    Select-Object InterfaceAlias, NextHop, RouteMetric
```

---

## IPv6 su Windows

### Architettura IPv6 in Windows

Windows supporta IPv6 nativamente dal kernel. Il driver `tcpip.sys` gestisce sia IPv4 che IPv6 in un dual-stack unificato. IPv6 e' abilitato di default su tutte le interfacce.

```
Tipi di indirizzi IPv6 su Windows:
- Link-local (fe80::/10)   → sempre assegnato automaticamente, scope interfaccia
- Global unicast (2000::/3) → ottenuto via SLAAC, DHCPv6, o configurazione statica
- Unique local (fc00::/7)   → equivalente RFC 1918 di IPv4
- Loopback (::1)            → equivalente 127.0.0.1
- Multicast (ff00::/8)      → sostituto del broadcast IPv4
```

### Configurazione IPv6

```powershell
# Stato IPv6 su tutti gli adattatori
Get-NetAdapterBinding -ComponentID ms_tcpip6

# Indirizzi IPv6 assegnati
Get-NetIPAddress -AddressFamily IPv6 |
    Select-Object InterfaceAlias, IPAddress, PrefixLength, PrefixOrigin, AddressState

# Configurazione IPv6 statica
New-NetIPAddress -InterfaceAlias "Ethernet" -IPAddress "2001:db8:1::10" `
    -PrefixLength 64 -DefaultGateway "2001:db8:1::1"

# DNS IPv6
Set-DnsClientServerAddress -InterfaceAlias "Ethernet" `
    -ServerAddresses "2001:db8:1::53", "2001:4860:4860::8888"

# Visualizzare configurazione router advertisement
Get-NetIPInterface -AddressFamily IPv6 |
    Select-Object InterfaceAlias, RouterDiscovery, ManagedAddressConfiguration, OtherStatefulConfiguration
```

### Disabilitare IPv6

```powershell
# Disabilitare IPv6 su un adattatore (se non necessario)
Disable-NetAdapterBinding -Name "Ethernet" -ComponentID ms_tcpip6

# Riabilitare IPv6 su un adattatore
Enable-NetAdapterBinding -Name "Ethernet" -ComponentID ms_tcpip6

# Disabilitare IPv6 globalmente (via Registry)
# ATTENZIONE: Microsoft sconsiglia la disabilitazione completa di IPv6.
# Alcuni servizi (es. Hyper-V networking, cluster) possono dipendere da IPv6.

# 0xFF = disabilita completamente IPv6 su tutte le interfacce non-tunnel
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip6\Parameters" `
    -Name "DisabledComponents" -Value 0xFF -PropertyType DWord -Force
# Richiede reboot

# Valori DisabledComponents:
# 0x00 = IPv6 abilitato (default)
# 0x01 = disabilita tunnel interfaces
# 0x10 = disabilita IPv6 su interfacce non-tunnel
# 0x20 = preferisci IPv4 a IPv6 (prefix policies)
# 0x11 = disabilita tutti i tunnel + interfacce
# 0xFF = disabilita tutto tranne loopback

# Metodo preferito: preferire IPv4 senza disabilitare IPv6
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip6\Parameters" `
    -Name "DisabledComponents" -Value 0x20 -PropertyType DWord -Force

# Verificare stato attuale
Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip6\Parameters" `
    -Name "DisabledComponents" -ErrorAction SilentlyContinue
```

### Tecnologie di Transizione IPv6

Windows supporta diverse tecnologie di transizione per ambienti misti IPv4/IPv6:

```
Tecnologia     Uso                                      Porta
───────────────────────────────────────────────────────────────
6to4           Incapsula IPv6 in IPv4 unicast            Protocollo 41
Teredo         IPv6 attraverso NAT IPv4                  UDP 3544
ISATAP         IPv6 su rete interna IPv4                 Protocollo 41
IP-HTTPS       IPv6 incapsulato in HTTPS                 TCP 443
               (usato da DirectAccess)
```

```powershell
# Stato interfacce di transizione
Get-NetIPInterface | Where-Object InterfaceAlias -like "*tunnel*" -or
    Where-Object InterfaceAlias -like "*isatap*" -or
    Where-Object InterfaceAlias -like "*teredo*"

# Disabilitare Teredo (raccomandato se non necessario)
netsh interface teredo set state disabled

# Stato Teredo
netsh interface teredo show state

# Disabilitare ISATAP
netsh interface isatap set state disabled

# Disabilitare 6to4
netsh interface 6to4 set state disabled

# Verificare prefix policies (ordine di preferenza IPv4 vs IPv6)
netsh interface ipv6 show prefixpolicies

# Modificare prefix policy per preferire IPv4
netsh interface ipv6 set prefixpolicy ::ffff:0:0/96 50 0
netsh interface ipv6 set prefixpolicy ::1/128 40 1
netsh interface ipv6 set prefixpolicy ::/0 30 2
```

### IPv6 e Active Directory

```
IPv6 e' supportato nativamente in Active Directory:
- DNS: record AAAA per server AD
- Kerberos: funziona su IPv6
- LDAP: funziona su IPv6
- Replication: funziona su IPv6

ATTENZIONE:
- DHCP scope IPv6 separato dal DHCPv4
- GPO network settings: verificare che si applichino sia a IPv4 che IPv6
- Firewall: regole separate per IPv6
- Se si disabilita IPv6, testare tutti i servizi AD prima del rollout
```

---

## DNS Client — Risoluzione e Troubleshooting

### Ordine di Risoluzione Nomi Windows

L'ordine in cui Windows risolve un nome host e' critico per il troubleshooting:

```
Ordine di risoluzione nomi:
1. Cache DNS locale (in-memory, servita dal servizio DNS Client)
2. File hosts (C:\Windows\System32\drivers\etc\hosts)
3. DNS Server configurato sull'interfaccia
4. LLMNR (Link-Local Multicast Name Resolution) — porta UDP 5355
   ATTENZIONE: DISABILITARE in enterprise (vettore per Responder)
5. NetBIOS Name Resolution (WINS query / broadcast)
   ATTENZIONE: DISABILITARE se possibile
6. mDNS (Multicast DNS) — porta UDP 5353 (Windows 10 1703+)
   ATTENZIONE: DISABILITARE in enterprise se non necessario
```

### Risoluzione DNS Client

```powershell
# Cache DNS locale
Get-DnsClientCache | Select-Object Entry, RecordType, Data -First 20
Clear-DnsClientCache    # Flush cache

# Risoluzione nomi
Resolve-DnsName "webapp.corp.contoso.com"
Resolve-DnsName "corp.contoso.com" -Type MX
Resolve-DnsName "corp.contoso.com" -Type SRV
Resolve-DnsName "_ldap._tcp.dc._msdcs.corp.contoso.com" -Type SRV  # DC AD

# Query DNS specifico
Resolve-DnsName "example.com" -Server 8.8.8.8

# Configurare DNS suffix search list
Set-DnsClientGlobalSetting -SuffixSearchList @("corp.contoso.com", "contoso.com")

# Registrare nel DNS
Register-DnsClient
ipconfig /registerdns

# nslookup (classico)
# nslookup
# > server 192.168.10.10
# > set type=SRV
# > _ldap._tcp.dc._msdcs.corp.contoso.com
```

### DNS Cache — Dettagli

```powershell
# Visualizzare cache DNS completa (equivalente ipconfig /displaydns)
ipconfig /displaydns

# Via PowerShell con piu' dettagli
Get-DnsClientCache |
    Select-Object Entry, RecordName, RecordType, Status, Section, TimeToLive, DataLength, Data |
    Format-Table -AutoSize

# Filtrare cache per dominio
Get-DnsClientCache | Where-Object Entry -like "*contoso*"

# Flush cache (due metodi equivalenti)
Clear-DnsClientCache
ipconfig /flushdns

# Disabilitare la cache DNS locale (per debug — NON in produzione)
Stop-Service -Name Dnscache
# ATTENZIONE: disabilitare il servizio DNS Client impatta performance e
# impedisce la registrazione dinamica DNS del client.

# Dimensione cache DNS (default: 16MB)
# Configurabile via Registry:
Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\Dnscache\Parameters" `
    -Name "MaxCacheTtl" -ErrorAction SilentlyContinue
# MaxCacheTtl: TTL massimo in cache (default 86400 secondi = 1 giorno)
# MaxNegativeCacheTtl: TTL per risposte negative (default 900 secondi = 15 min)
```

### File hosts

```powershell
# Percorso file hosts
$hostsFile = "$env:SystemRoot\System32\drivers\etc\hosts"

# Visualizzare contenuto
Get-Content $hostsFile

# Aggiungere entry (richiede admin)
Add-Content -Path $hostsFile -Value "192.168.10.50`tapp.corp.contoso.com"

# Esempio formato hosts:
# 127.0.0.1       localhost
# ::1             localhost
# 192.168.10.50   app.corp.contoso.com  app
# 10.10.20.100    legacy-server

# Il file hosts ha PRIORITA' sulla query DNS (step 2 nell'ordine di risoluzione).
# Usare per:
# - Override temporanei durante migrazioni
# - Blocco domini (es. telemetria, malware)
# - Test locale di applicazioni web
#
# ATTENZIONE sicurezza: malware modifica il file hosts per redirect.
# Monitorare con: SIEM, file integrity monitoring, Sysmon (Event ID 11).
```

### NRPT (Name Resolution Policy Table)

La NRPT consente di definire regole di risoluzione DNS per namespace specifici, utile per:
- DirectAccess / Always On VPN (DNS split-tunnel)
- DNS-over-HTTPS (DoH) per domini specifici
- DNS condizionale senza dipendere dal server DNS

```powershell
# Visualizzare regole NRPT
Get-DnsClientNrptRule

# Aggiungere regola NRPT (es. dominio intranet via DNS server specifico)
Add-DnsClientNrptRule -Namespace ".corp.contoso.com" `
    -NameServers "10.10.10.10" -Comment "Intranet DNS"

# Regola NRPT per DNS-over-HTTPS
Add-DnsClientNrptRule -Namespace "." `
    -DohStatus Automatic -Comment "DoH per tutto il traffico"

# Rimuovere regola
Get-DnsClientNrptRule | Where-Object Namespace -eq ".corp.contoso.com" |
    Remove-DnsClientNrptRule -Force

# NRPT via GPO:
# Computer Configuration → Policies → Windows Settings
# → Name Resolution Policy → Create Rule
# Namespace: .corp.contoso.com
# DNS Servers: 10.10.10.10
# DNSSEC: enable/disable
# DirectAccess: enable (per DA split-tunnel)

# Verificare quale policy NRPT si applica a un nome
Resolve-DnsName "server.corp.contoso.com" -DnssecOk
```

### DNS-over-HTTPS (DoH)

```powershell
# Windows 11 / Windows Server 2022+ supporta DoH nativamente

# Configurare DoH per un'interfaccia
# Via Settings → Network & Internet → Ethernet → DNS
# Oppure via Registry:

# Abilitare DoH a livello di sistema
Set-DnsClientDohServerAddress -ServerAddress "8.8.8.8" `
    -DohTemplate "https://dns.google/dns-query" -AllowFallbackToUdp $true -AutoUpgrade $true

# Visualizzare server DoH configurati
Get-DnsClientDohServerAddress

# Nota: DoH cripta le query DNS impedendo l'ispezione da parte di
# firewalls e IDS/IPS. In ambienti enterprise, pianificare attentamente.
```

### DNS-over-HTTPS — Configurazione Enterprise Avanzata

A partire da Windows Server 2025 (con l'aggiornamento di sicurezza 2026-02, KB5075899 o successivo), il ruolo DNS Server supporta DoH anche lato server, non solo lato client. Questo consente di cifrare le query DNS tra client interni e il DNS server aziendale.

#### Prerequisiti DoH Server-Side

```
Requisiti per abilitare DoH sul DNS Server:
- Windows Server 2025 con KB5075899 o successivo
- Accesso a una CA (Microsoft Enterprise CA, Let's Encrypt, DigiCert, ecc.)
- Certificato con:
  - EKU: Server Authentication (OID 1.3.6.1.5.5.7.3.1)
  - SAN: FQDN o IP address del DNS server
- Regole firewall: TCP 443 in ingresso (per DoH)
- NOTA: la porta 53 (DNS tradizionale) resta attiva in parallelo
  I client legacy continuano a risolvere normalmente via UDP/TCP 53
```

```powershell
# Abilitare DoH sul DNS Server (Windows Server 2025+)
# 1. Importare il certificato nel certificate store del server
# 2. Ottenere il thumbprint del certificato
$cert = Get-ChildItem Cert:\LocalMachine\My |
    Where-Object Subject -like "*dns.corp.contoso.com*"
$cert.Thumbprint

# 3. Configurare DoH sul server DNS
# Il comando specifico dipende dalla versione di preview —
# consultare la documentazione Microsoft aggiornata:
# https://learn.microsoft.com/en-us/windows-server/networking/dns/enable-dns-over-https-server

# 4. Verificare che il listener DoH sia attivo
Test-NetConnection -ComputerName "dns.corp.contoso.com" -Port 443

# 5. Testare risoluzione DoH da un client Windows 11
Resolve-DnsName "test.corp.contoso.com" -DohStatus Mandatory -Server "dns.corp.contoso.com"
```

#### Configurazione DoH via GPO per Client Enterprise

```
Percorso GPO:
Computer Configuration → Policies → Administrative Templates
→ Network → DNS Client → Configure DNS over HTTPS (DoH) name resolution

Opzioni:
- Disabled:    DoH disabilitato (default)
- Enabled: Allow DoH     → il client usa DoH se disponibile, fallback a UDP 53
- Enabled: Require DoH   → SOLO DoH, nessun fallback

ATTENZIONE: NON usare "Require DoH" su client domain-joined in ambienti
dove il DNS server non supporta DoH. Active Directory dipende pesantemente
da DNS e il servizio DNS Server tradizionale (pre-2025) non supporta DoH.

Raccomandazione enterprise:
1. Fase 1: Abilitare DoH sul DNS Server (Server 2025+)
2. Fase 2: Configurare GPO con "Allow DoH" (fallback garantito)
3. Fase 3: Dopo validazione completa, valutare "Require DoH"
4. Monitorare con DNS analytics e firewall logs
```

```powershell
# Configurazione DoH client via Registry (alternativa a GPO)
# 0 = Disabled, 1 = Allow, 2 = Require
New-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\DNSClient" `
    -Name "DoHPolicy" -Value 1 -PropertyType DWord -Force

# Aggiungere un server DoH personalizzato (interno)
# Windows 11 mantiene una lista built-in di server DoH noti (Google, Cloudflare, Quad9)
# Per aggiungere un server DoH aziendale:
Add-DnsClientDohServerAddress -ServerAddress "10.10.10.10" `
    -DohTemplate "https://dns.corp.contoso.com/dns-query" `
    -AllowFallbackToUdp $true -AutoUpgrade $true

# Visualizzare tutti i server DoH configurati (built-in + custom)
Get-DnsClientDohServerAddress

# Rimuovere un server DoH custom
Remove-DnsClientDohServerAddress -ServerAddress "10.10.10.10"

# Verificare se DoH è in uso su una connessione
Get-DnsClientServerAddress -AddressFamily IPv4 |
    Select-Object InterfaceAlias, ServerAddresses

# Event log per diagnostica DoH
Get-WinEvent -LogName "Microsoft-Windows-DNS-Client/Operational" -MaxEvents 20 |
    Where-Object Message -like "*DoH*"
```

#### Considerazioni di Sicurezza DoH in Enterprise

```
Pro:
- Impedisce l'intercettazione e la manipolazione delle query DNS
- Protegge la privacy degli utenti su reti non fidate
- Mitiga attacchi DNS spoofing/hijacking

Contro / Rischi enterprise:
- Bypassa i filtri DNS aziendali (content filtering, threat intelligence)
- Impedisce l'ispezione DNS da parte di IDS/IPS e SIEM
- Client possono configurare DoH verso server esterni, eludendo il DNS aziendale
- Richiede gestione certificati aggiuntiva sul DNS server

Mitigazioni:
1. Usare NRPT per forzare i client a usare SOLO il DNS server aziendale
2. Bloccare traffico DoH verso server esterni (IP noti: 1.1.1.1, 8.8.8.8, 9.9.9.9)
3. Monitorare connessioni TCP 443 verso IP di resolver DoH pubblici
4. Configurare DoH solo verso il DNS server interno (trusted)
5. Usare firewall rules per bloccare DNS-over-TLS (porta 853) se non autorizzato
```

### Troubleshooting DNS

```powershell
# DIAGNOSI SISTEMATICA

# 1. Il client risolve?
Resolve-DnsName "hostname.corp.contoso.com"

# 2. Quale DNS server sta usando?
Get-DnsClientServerAddress -AddressFamily IPv4

# 3. Il DNS server risponde?
Test-Connection 192.168.10.10 -Count 2
Test-NetConnection 192.168.10.10 -Port 53

# 4. Il record esiste sul server DNS?
Resolve-DnsName "hostname.corp.contoso.com" -Server 192.168.10.10

# 5. Prova con DNS esterno (isolamento problema)
Resolve-DnsName "hostname.corp.contoso.com" -Server 8.8.8.8

# 6. Controllare hosts file
Get-Content C:\Windows\System32\drivers\etc\hosts

# 7. Reset stack DNS completo
Clear-DnsClientCache
ipconfig /registerdns
netsh winsock reset
# Riavviare

# 8. Verificare regole NRPT che potrebbero interferire
Get-DnsClientNrptRule

# 9. Controllare se il servizio DNS Client e' in esecuzione
Get-Service -Name Dnscache

# 10. Verificare il DNS suffix search list
Get-DnsClientGlobalSetting
```

---

## Protocollo SMB

### Panoramica SMB

SMB (Server Message Block) e' il protocollo di condivisione file e risorse in ambiente Windows. Le versioni moderne (SMB 2.x/3.x) hanno introdotto miglioramenti significativi in performance, sicurezza e affidabilita'.

```
Versione   OS Minimo                    Feature Principali
─────────────────────────────────────────────────────────────────────
SMB 1.0    Windows 2000/XP              Legacy, INSICURO, da disabilitare
SMB 2.0    Windows Vista / Server 2008  Reduced chattiness, pipelining
SMB 2.1    Windows 7 / Server 2008 R2   Large MTU, lease oplocks
SMB 3.0    Windows 8 / Server 2012      Encryption, Multichannel,
                                        SMB Direct (RDMA), scale-out
SMB 3.0.2  Windows 8.1 / Server 2012 R2 Miglioramenti stabilita'
SMB 3.1.1  Windows 10 / Server 2016+    Pre-auth integrity (SHA-512),
                                        encryption AES-128-GCM/CCM,
                                        cluster dialect fencing
```

### Configurazione SMB

```powershell
# Versione SMB in uso
Get-SmbConnection | Select-Object ServerName, ShareName, Dialect

# Versione SMB configurata sul server
Get-SmbServerConfiguration | Select-Object EnableSMB1Protocol, EnableSMB2Protocol

# DISABILITARE SMB 1.0 (CRITICO per sicurezza — WannaCry, EternalBlue)
Set-SmbServerConfiguration -EnableSMB1Protocol $false -Force
# Client-side:
Disable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol -NoRestart

# Verificare feature SMB1 installata
Get-WindowsOptionalFeature -Online -FeatureName SMB1Protocol

# Rimuovere completamente SMB1 (Windows Server)
Remove-WindowsFeature -Name FS-SMB1
# Windows Client:
Disable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol

# Visualizzare sessioni SMB attive
Get-SmbSession

# Visualizzare condivisioni
Get-SmbShare
# Condivisioni nascoste (terminano con $)
Get-SmbShare | Where-Object Name -like "*$"

# Creare condivisione
New-SmbShare -Name "Dati" -Path "D:\Dati" `
    -FullAccess "CONTOSO\Domain Admins" `
    -ChangeAccess "CONTOSO\Domain Users" `
    -ReadAccess "Everyone"
```

### SMB Signing

SMB Signing protegge contro attacchi man-in-the-middle (MITM) e relay. Il traffico viene firmato con la chiave di sessione.

```powershell
# Stato corrente SMB Signing
Get-SmbServerConfiguration | Select-Object RequireSecuritySignature, EnableSecuritySignature

# Server: richiedere firma su tutto il traffico
Set-SmbServerConfiguration -RequireSecuritySignature $true -Force

# Client: richiedere firma
Set-SmbClientConfiguration -RequireSecuritySignature $true -Force

# Via GPO (raccomandato per deployment enterprise):
# Computer Configuration → Policies → Windows Settings → Security Settings
# → Local Policies → Security Options:
# "Microsoft network server: Digitally sign communications (always)" = Enabled
# "Microsoft network client: Digitally sign communications (always)" = Enabled

# Nota: SMB Signing e' OBBLIGATORIO di default per le connessioni ai Domain Controller.
# Windows Server 2022+ e Windows 11 24H2+ lo richiedono di default per TUTTE le connessioni.

# Impatto performance: ~10-15% overhead su CPU per la firma.
# Con AES-GMAC (SMB 3.1.1 su Windows Server 2022), l'overhead e' minimo.
```

### SMB Encryption

SMB 3.0+ supporta encryption end-to-end del traffico SMB. Piu' sicuro di SMB Signing (cifra + firma).

```powershell
# Stato encryption
Get-SmbServerConfiguration | Select-Object EncryptData, RejectUnencryptedAccess

# Abilitare encryption globale
Set-SmbServerConfiguration -EncryptData $true -Force

# Rifiutare connessioni non cifrate
Set-SmbServerConfiguration -RejectUnencryptedAccess $true -Force

# Encryption per singola condivisione
Set-SmbShare -Name "Dati" -EncryptData $true

# Tipi di encryption supportati (SMB 3.1.1):
# AES-128-CCM (default SMB 3.0)
# AES-128-GCM (preferito, SMB 3.1.1+)
# AES-256-CCM (Windows Server 2022+)
# AES-256-GCM (Windows Server 2022+)

# Configurare algoritmo di encryption preferito
Set-SmbServerConfiguration -EncryptionCiphers "AES_256_GCM, AES_128_GCM" -Force

# Visualizzare cipher in uso sulle connessioni
Get-SmbConnection | Select-Object ServerName, Dialect, Encrypted, EncryptionType
```

### SMB Multichannel

SMB Multichannel utilizza automaticamente piu' connessioni di rete per aumentare throughput e resilienza. Richiede almeno due NIC, o una NIC con RSS.

```powershell
# Stato Multichannel
Get-SmbServerConfiguration | Select-Object EnableMultiChannel
Get-SmbClientConfiguration | Select-Object EnableMultiChannel

# Abilitare Multichannel (abilitato di default)
Set-SmbServerConfiguration -EnableMultiChannel $true -Force
Set-SmbClientConfiguration -EnableMultiChannel $true -Force

# Visualizzare canali SMB attivi
Get-SmbMultichannelConnection

# Requisiti per Multichannel:
# - Almeno 2 NIC (o 1 NIC con RSS enabled)
# - NIC nella stessa subnet O NIC con route verso la stessa destinazione
# - SMB 3.0+ su entrambi client e server
# - Non supportato con NIC Teaming LBFO (usare SET invece)

# Vincolamento interfacce Multichannel (opzionale)
New-SmbMultichannelConstraint -ServerName "FileServer01" `
    -InterfaceAlias "Ethernet 1", "Ethernet 2"
Get-SmbMultichannelConstraint
```

### SMB Direct (RDMA)

SMB Direct utilizza RDMA (Remote Direct Memory Access) per trasferimenti a latenza ultra-bassa e CPU overhead minimo. Usato primariamente per storage (Hyper-V, SQL Server).

```powershell
# Verificare supporto RDMA sulle NIC
Get-NetAdapterRdma

# Abilitare RDMA sulla NIC
Enable-NetAdapterRdma -Name "Ethernet"

# Protocolli RDMA supportati:
# iWARP   → funziona su infrastruttura Ethernet standard (raccomandato per semplicita')
# RoCE v2 → richiede switch con supporto DCB/PFC (performance superiori)
# InfiniBand → hardware dedicato (massime performance)

# Verificare connessioni SMB Direct
Get-SmbConnection | Select-Object ServerName, RdmaTransport

# Testare throughput RDMA
# Usare tool Microsoft: DiskSpd, NTttcp

# Requisiti:
# - NIC con supporto RDMA (Mellanox, Chelsio, Intel, Broadcom)
# - Driver RDMA installati
# - SMB 3.0+ su client e server
# - Windows Server 2012+ o Windows 10+
```

### SMB Compressione (Windows Server 2022+)

```powershell
# SMB Compression riduce l'utilizzo di banda per trasferimenti di file grandi

# Abilitare compression lato server
Set-SmbServerConfiguration -EnableCompressedTraffic $true -Force

# Richiedere compression lato client per una mappatura
New-SmbMapping -RemotePath "\\FileServer\Share" -CompressNetworkTraffic $true

# Compression su una condivisione specifica
Set-SmbShare -Name "Dati" -CompressData $true

# Nota: la compressione aggiunge overhead CPU.
# Utile per WAN / link lenti. Non necessaria su rete locale 10GbE+.
```

### SMB over QUIC (Windows Server 2025+)

SMB over QUIC introduce un trasporto alternativo a TCP per l'accesso ai file condivisi. Invece di usare la porta TCP 445 (spesso bloccata da firewall aziendali e ISP), SMB over QUIC crea un tunnel TLS 1.3 cifrato sulla porta UDP 443, permettendo l'accesso remoto alle condivisioni SMB senza la necessità di una VPN tradizionale.

```
Caratteristiche SMB over QUIC:
─────────────────────────────────────────────────────────────────
Trasporto         UDP 443 (internet-friendly, attraversa NAT/firewall)
Cifratura         TLS 1.3 end-to-end (obbligatoria, non opzionale)
Compatibilità     Client: Windows 11 22H2+ / Server: Windows Server 2025+
Edizioni server   Tutte: Datacenter, Standard, Azure Edition
Autenticazione    Certificato server obbligatorio (SAN con FQDN)
Fallback          Se QUIC non disponibile, il client tenta TCP 445
Caso d'uso        Accesso remoto file server senza VPN, edge/branch office
```

#### Prerequisiti e Certificato

```
Requisiti certificato per SMB over QUIC:
- Tipo: Server Authentication (EKU OID 1.3.6.1.5.5.7.3.1)
- SAN (Subject Alternative Name): FQDN del file server
- Fonti accettate:
  * CA interna Microsoft (Enterprise CA)
  * CA esterna (DigiCert, Let's Encrypt, GlobalSign, ecc.)
  * Certificato self-signed (solo per lab/test)
- Il certificato deve essere nel certificate store LocalMachine\My
- Il client deve fidarsi della CA che ha firmato il certificato
```

#### Configurazione Server

```powershell
# 1. Verificare che il server sia Windows Server 2025+
Get-ComputerInfo | Select-Object WindowsProductName, OsVersion

# 2. Ottenere il certificato (se si usa una CA interna)
$cert = Get-ChildItem Cert:\LocalMachine\My |
    Where-Object { $_.Subject -like "*fileserver.contoso.com*" -and
                   $_.EnhancedKeyUsageList.FriendlyName -contains "Server Authentication" }

# Se si usa un certificato self-signed per lab:
$cert = New-SelfSignedCertificate `
    -DnsName "fileserver.contoso.com" `
    -CertStoreLocation Cert:\LocalMachine\My `
    -KeyUsage DigitalSignature `
    -TextExtension @("2.5.29.37={text}1.3.6.1.5.5.7.3.1") `
    -NotAfter (Get-Date).AddYears(3)

# 3. Creare il mapping certificato-SMB
New-SmbServerCertificateMapping -Name "fileserver.contoso.com" `
    -Thumbprint $cert.Thumbprint `
    -StoreName "My" `
    -Subject "fileserver.contoso.com"

# 4. Verificare il mapping
Get-SmbServerCertificateMapping

# 5. Verificare che la porta UDP 443 sia in ascolto
Get-NetUDPEndpoint -LocalPort 443

# 6. Regola firewall per QUIC (UDP 443)
New-NetFirewallRule -DisplayName "SMB over QUIC (UDP 443)" `
    -Direction Inbound -Protocol UDP -LocalPort 443 `
    -Action Allow -Profile Any `
    -Description "Consente SMB over QUIC per accesso remoto file"
```

#### Configurazione Client

```powershell
# Il client Windows 11 22H2+ supporta SMB over QUIC automaticamente
# Mappare una condivisione via SMB over QUIC:
New-SmbMapping -RemotePath "\\fileserver.contoso.com\Share" -TransportType QUIC

# Se il client non si fida della CA del certificato server,
# importare il certificato root CA nel trust store del client:
Import-Certificate -FilePath "C:\Certs\ContosoRootCA.cer" `
    -CertStoreLocation Cert:\LocalMachine\Root

# Verificare la connessione QUIC
Get-SmbConnection | Select-Object ServerName, ShareName, Dialect, TransportType

# Forzare il trasporto QUIC (senza fallback TCP)
# Via GPO o Registry:
# HKLM\SYSTEM\CurrentControlSet\Services\LanmanWorkstation\Parameters
# "RequireQUIC" = 1 (DWORD)
```

#### Controllo Accessi Client (Client Access Control)

SMB over QUIC supporta il controllo degli accessi basato su certificati client, permettendo di creare allowlist e blocklist per i dispositivi autorizzati a connettersi.

```powershell
# Abilitare il controllo accessi client
Set-SmbServerCertificateMapping -Name "fileserver.contoso.com" `
    -RequireClientAuthentication $true

# Aggiungere un certificato client all'allowlist
Grant-SmbClientAccessToServer -Name "fileserver.contoso.com" `
    -IdentifierType SHA256 `
    -Identifier "CertificateThumbprintHere"

# Visualizzare le regole di accesso
Get-SmbClientAccessToServer

# Revocare l'accesso a un client specifico
Revoke-SmbClientAccessToServer -Name "fileserver.contoso.com" `
    -IdentifierType SHA256 `
    -Identifier "CertificateThumbprintHere"

# Bloccare un client specifico
Block-SmbClientAccessToServer -Name "fileserver.contoso.com" `
    -IdentifierType SHA256 `
    -Identifier "CertificateThumbprintHere"
```

#### Scenari di Deployment SMB over QUIC

```
Scenario                      Configurazione
──────────────────────────────────────────────────────────────────────
Branch office senza VPN       File server in sede → client remoti via QUIC
                              UDP 443 aperto sul firewall perimetrale
Lavoratori remoti             Accesso diretto alle condivisioni aziendali
                              senza tunnel VPN (Always On VPN non necessario)
Edge server                   File server in DMZ con certificato pubblico
                              Client accedono da Internet
Migrazione da VPN             Fase 1: QUIC + VPN in parallelo
                              Fase 2: dismissione VPN per accesso file
Azure Stack HCI               Accesso storage per workload ibridi
                              Integrazione nativa con Azure File Sync
```

---

## Configurazione Avanzata NIC e Teaming

### NIC Teaming (LBFO — Link Aggregation)

```powershell
# NIC Teaming combina 2+ NIC per ridondanza e/o throughput

# Creare team
New-NetLbfoTeam -Name "NIC-Team" -TeamMembers "Ethernet 1", "Ethernet 2" `
    -TeamingMode SwitchIndependent -LoadBalancingAlgorithm HyperVPort

# Modalità:
# SwitchIndependent  → Non richiede configurazione switch (consigliato per Hyper-V)
# Static             → Richiede LACP statico sullo switch
# LACP               → 802.3ad Link Aggregation (dinamico)

# Load Balancing:
# AddressHash         → Hash IP/MAC sorgente+destinazione
# HyperVPort          → Per Hyper-V (un NIC per VM)
# Dynamic             → Combinazione migliore (Windows Server 2012 R2+)

# Verificare
Get-NetLbfoTeam
Get-NetLbfoTeamMember

# Configurare IP sul team (non sulle NIC individuali)
New-NetIPAddress -InterfaceAlias "NIC-Team" -IPAddress 192.168.10.20 -PrefixLength 24

# SET (Switch Embedded Teaming) per Hyper-V
New-VMSwitch -Name "ConvergedSwitch" -NetAdapterName "Ethernet 1", "Ethernet 2" `
    -EnableEmbeddedTeaming $true -AllowManagementOS $true
```

### Dettagli Modalita' di Teaming

```
Modalita'          Requisiti Switch        Failover     Aggregazione Banda
──────────────────────────────────────────────────────────────────────────
Switch Independent Nessuno                 Si'          Solo in uscita *
Static Teaming     Port channel statico    Si'          Si' (bidirez.)
LACP (802.3ad)     LACP support switch     Si'          Si' (bidirez.)

* Switch Independent: il traffico in ingresso arriva su una sola NIC
  (la primaria). Solo il traffico in uscita e' distribuito.
  Per throughput bidirezionale, usare LACP.
```

```powershell
# Dettaglio modalita' LACP
New-NetLbfoTeam -Name "LACP-Team" -TeamMembers "NIC1", "NIC2", "NIC3" `
    -TeamingMode LACP -LoadBalancingAlgorithm Dynamic

# Standby adapter (failover manuale)
Add-NetLbfoTeamMember -Name "NIC4" -Team "LACP-Team"
Set-NetLbfoTeamMember -Name "NIC4" -Team "LACP-Team" -AdministrativeMode Standby

# Verificare stato dei membri
Get-NetLbfoTeamMember -Team "LACP-Team" |
    Select-Object Name, AdministrativeMode, OperationalStatus, FailureReason

# Rimuovere membro dal team
Remove-NetLbfoTeamMember -Name "NIC3" -Team "LACP-Team" -Confirm:$false

# Rimuovere team intero
Remove-NetLbfoTeam -Name "LACP-Team" -Confirm:$false
```

### Algoritmi di Load Distribution

```
Algoritmo       Basato Su             Scenario Ideale
──────────────────────────────────────────────────────────────
AddressHash     Hash L2+L3+L4         Traffico generico, molte connessioni
HyperVPort      vSwitch port          Hyper-V host (una NIC per VM)
Dynamic         Flowlets + Hyper-V    Best choice generale (Server 2012 R2+)
                port + hash
TransportPorts  Hash porte TCP/UDP    Alto numero di flussi TCP/UDP

Nota: "Dynamic" combina i vantaggi di tutti gli altri ed e' la scelta
raccomandata per la maggior parte degli scenari.
```

### Offloading e Proprieta' Avanzate

```powershell
# Proprietà avanzate NIC
Get-NetAdapterAdvancedProperty -Name "Ethernet" | Format-Table DisplayName, DisplayValue

# Jumbo Frames (se la rete lo supporta)
Set-NetAdapterAdvancedProperty -Name "Ethernet" -DisplayName "Jumbo Packet" -DisplayValue "9014"

# RSS (Receive Side Scaling)
Enable-NetAdapterRss -Name "Ethernet"
Get-NetAdapterRss -Name "Ethernet"

# VMQ (Virtual Machine Queue) per Hyper-V
Enable-NetAdapterVmq -Name "Ethernet"

# Offloading
Get-NetAdapterChecksumOffload -Name "Ethernet"
Set-NetAdapterChecksumOffload -Name "Ethernet" -TcpIPv4 RxTxEnabled

# RDMA (Remote Direct Memory Access) per SMB Direct
Get-NetAdapterRdma
Enable-NetAdapterRdma -Name "Ethernet"

# QoS
New-NetQosPolicy -Name "SMB" -SMB -PriorityValue8021Action 3
New-NetQosPolicy -Name "LiveMigration" -LiveMigration -PriorityValue8021Action 5
```

### LBFO vs SET — Confronto

```
Caratteristica          LBFO                    SET (Switch Embedded Teaming)
────────────────────────────────────────────────────────────────────────────
Disponibilita'          Tutti i Windows Server  Solo Hyper-V host
Max NIC                 32                      8
Modalita' switch        Ind/Static/LACP         Solo Switch Independent
RDMA supportato         No                      Si'
Virtual switch          Sopra il team           Integrato nel vSwitch
Live Migration          Supportato              Supportato (migliore)
Futuro                  Deprecato (Server 2025) Raccomandato

Nota: Microsoft raccomanda SET per tutti i nuovi deployment Hyper-V.
LBFO resta disponibile ma non riceve nuove feature.
```

### LBFO Deprecazione in Windows Server 2025

A partire da Windows Server 2025, LBFO è ufficialmente deprecato per gli scenari Hyper-V. Il tentativo di collegare un virtual switch Hyper-V a un team LBFO viene bloccato con un messaggio di errore esplicito. SET è l'unico metodo di teaming supportato per il networking virtualizzato.

```
Stato LBFO in Windows Server 2025:
─────────────────────────────────────────────────────────────────────
Hyper-V vSwitch        BLOCCATO — non è possibile collegare un vSwitch
                       a un team LBFO. Errore esplicito alla creazione.
Bare-metal (no Hyper-V) Ancora disponibile — LBFO funziona per server
                       fisici senza ruolo Hyper-V installato.
Nuove feature          NESSUNA — LBFO non riceve aggiornamenti o
                       miglioramenti. Solo fix di sicurezza critici.
Supporto               Supportato per backward compatibility, ma
                       Microsoft raccomanda la migrazione a SET.
```

#### Migrazione da LBFO a SET

```powershell
# Piano di migrazione LBFO → SET per un host Hyper-V

# 1. Documentare la configurazione LBFO corrente
Get-NetLbfoTeam | Format-List *
Get-NetLbfoTeamMember | Format-Table Name, Team, AdministrativeMode, OperationalStatus
$teamIP = Get-NetIPAddress -InterfaceAlias "NIC-Team" -AddressFamily IPv4

# 2. Documentare il virtual switch corrente
Get-VMSwitch | Format-List *
Get-VMNetworkAdapter -ManagementOS | Format-Table Name, SwitchName, IPAddresses

# 3. ATTENZIONE: la migrazione richiede downtime di rete
# Pianificare una finestra di manutenzione. Le VM perderanno
# connettività durante la transizione.

# 4. Disconnettere le VM dal vSwitch
Get-VM | Get-VMNetworkAdapter | Disconnect-VMNetworkAdapter

# 5. Rimuovere il virtual switch collegato al team LBFO
Remove-VMSwitch -Name "OldSwitch" -Force

# 6. Rimuovere il team LBFO
Remove-NetLbfoTeam -Name "NIC-Team" -Confirm:$false

# 7. Creare il nuovo vSwitch SET con le stesse NIC
New-VMSwitch -Name "SETSwitch" `
    -NetAdapterName "NIC1", "NIC2" `
    -EnableEmbeddedTeaming $true `
    -AllowManagementOS $true

# 8. Ripristinare la configurazione IP sul management OS
New-NetIPAddress -InterfaceAlias "vEthernet (SETSwitch)" `
    -IPAddress $teamIP.IPAddress -PrefixLength $teamIP.PrefixLength
Set-DnsClientServerAddress -InterfaceAlias "vEthernet (SETSwitch)" `
    -ServerAddresses "10.10.10.10", "10.10.10.11"

# 9. Riconnettere le VM al nuovo vSwitch SET
Get-VM | Get-VMNetworkAdapter | Connect-VMNetworkAdapter -SwitchName "SETSwitch"

# 10. Verificare il funzionamento
Get-VMSwitch -Name "SETSwitch" | Select-Object *Embedded*
Get-VMSwitchTeam -Name "SETSwitch"
Get-VM | Get-VMNetworkAdapter | Select-Object VMName, SwitchName, Status
Test-Connection -ComputerName "dc01.corp.contoso.com" -Count 2
```

#### Quando Mantenere LBFO

```
LBFO resta la scelta corretta in questi scenari:
- Server fisici senza Hyper-V (file server, print server, application server)
- Ambienti che richiedono LACP (802.3ad) — SET non supporta LACP
- Windows Server versioni precedenti (2016, 2019, 2022) — SET esiste
  ma LBFO è pienamente supportato
- NIC che non supportano SET (verificare compatibilità con il vendor)

Per server bare-metal su Windows Server 2025 senza Hyper-V:
- LBFO funziona senza restrizioni
- Non è necessario installare Hyper-V per usare SET
  (ma SET richiede il ruolo Hyper-V per la creazione del vSwitch)
```

---

## Hyper-V Networking

### Tipi di Virtual Switch

Hyper-V supporta tre tipi di virtual switch, ciascuno con uno scope diverso:

```
Tipo        Accesso VM      Accesso Host    Rete Esterna
───────────────────────────────────────────────────────
External    Si'             Si' (opzionale) Si'
Internal    Si'             Si'             No
Private     Si'             No              No
```

```powershell
# Creare virtual switch esterno (collegato a una NIC fisica)
New-VMSwitch -Name "ExternalSwitch" -NetAdapterName "Ethernet" `
    -AllowManagementOS $true    # $true = host OS puo' usare la stessa NIC

# Creare virtual switch interno (comunicazione host ↔ VM)
New-VMSwitch -Name "InternalSwitch" -SwitchType Internal

# Creare virtual switch privato (solo VM ↔ VM)
New-VMSwitch -Name "PrivateSwitch" -SwitchType Private

# Elencare virtual switch
Get-VMSwitch | Select-Object Name, SwitchType, NetAdapterInterfaceDescription

# Configurare IP sull'interfaccia interna (host side)
$ifAlias = (Get-NetAdapter | Where-Object Name -like "vEthernet (InternalSwitch)").Name
New-NetIPAddress -InterfaceAlias $ifAlias -IPAddress 172.16.0.1 -PrefixLength 24

# Collegare VM a un virtual switch
Get-VM "VM01" | Get-VMNetworkAdapter
Connect-VMNetworkAdapter -VMName "VM01" -SwitchName "ExternalSwitch"

# Aggiungere NIC virtuale a una VM
Add-VMNetworkAdapter -VMName "VM01" -SwitchName "InternalSwitch" -Name "NIC2"
```

### SET (Switch Embedded Teaming)

SET e' il metodo raccomandato per combinare NIC fisiche in un virtual switch Hyper-V:

```powershell
# Creare virtual switch con SET (team integrato)
New-VMSwitch -Name "ConvergedSwitch" `
    -NetAdapterName "NIC1", "NIC2", "NIC3", "NIC4" `
    -EnableEmbeddedTeaming $true `
    -AllowManagementOS $true

# Vantaggi SET vs LBFO:
# - Supporta RDMA sulle NIC fisiche
# - Gestione unificata (un solo oggetto: il vSwitch)
# - Migliore performance per SR-IOV + teaming
# - Non richiede team LBFO separato sotto il vSwitch

# Verificare stato SET
Get-VMSwitch -Name "ConvergedSwitch" | Select-Object *Embedded*
Get-VMSwitchTeam -Name "ConvergedSwitch"

# Aggiungere NIC al team SET
Set-VMSwitchTeam -Name "ConvergedSwitch" `
    -NetAdapterName "NIC1", "NIC2", "NIC3", "NIC4", "NIC5"

# Modalita' di bilanciamento SET
Set-VMSwitchTeam -Name "ConvergedSwitch" -LoadBalancingAlgorithm Dynamic
# Opzioni: Dynamic, HyperVPort
```

### VLAN Tagging

```powershell
# VLAN sull'host management OS
Set-VMNetworkAdapterVlan -ManagementOS -VMNetworkAdapterName "ConvergedSwitch" `
    -Access -VlanId 10

# VLAN su una VM
Set-VMNetworkAdapterVlan -VMName "VM01" -Access -VlanId 20

# VLAN trunk (VM che gestisce piu' VLAN, es. router VM)
Set-VMNetworkAdapterVlan -VMName "RouterVM" -Trunk `
    -AllowedVlanIdList "10,20,30" -NativeVlanId 1

# Verificare configurazione VLAN
Get-VMNetworkAdapterVlan -VMName "VM01"
Get-VMNetworkAdapterVlan -ManagementOS

# Rimuovere VLAN (tornare a untagged)
Set-VMNetworkAdapterVlan -VMName "VM01" -Untagged
```

### Bandwidth Management e QoS per VM

```powershell
# Abilitare bandwidth management sul virtual switch
Set-VMSwitch -Name "ConvergedSwitch" -DefaultFlowMinimumBandwidthWeight 10

# Impostare peso banda per VM (valore relativo)
Set-VMNetworkAdapter -VMName "CriticalVM" -MinimumBandwidthWeight 50
Set-VMNetworkAdapter -VMName "TestVM" -MinimumBandwidthWeight 10

# Impostare banda massima assoluta
Set-VMNetworkAdapter -VMName "TestVM" -MaximumBandwidth 1000000000  # 1 Gbps

# Banda minima assoluta
Set-VMNetworkAdapter -VMName "CriticalVM" -MinimumBandwidthAbsolute 500000000  # 500 Mbps
```

### SR-IOV (Single Root I/O Virtualization)

```powershell
# SR-IOV bypassa il virtual switch per accesso diretto hardware NIC → VM
# Riduce latenza e overhead CPU

# Creare vSwitch con SR-IOV (richiede hardware compatibile + BIOS VT-d/IOMMU)
New-VMSwitch -Name "SRIOVSwitch" -NetAdapterName "Ethernet" `
    -EnableIov $true -AllowManagementOS $true

# Abilitare SR-IOV su una VM
Set-VMNetworkAdapter -VMName "VM01" -IovWeight 100

# Verificare stato SR-IOV
Get-VMNetworkAdapter -VMName "VM01" | Select-Object IovWeight, IovQueuePairsRequested
Get-NetAdapterSriov -Name "Ethernet"
```

---

## Windows Firewall — Deep Dive

### Architettura Windows Firewall

Windows Defender Firewall con sicurezza avanzata (WF) opera a livello del Windows Filtering Platform (WFP) e gestisce tre profili:

```
Profilo      Quando si Attiva                    Default
──────────────────────────────────────────────────────────────
Domain       NLA rileva un dominio AD              Inbound: Block
             (DC raggiungibile via DNS)            Outbound: Allow
Private      Utente seleziona "rete privata"       Inbound: Block
                                                   Outbound: Allow
Public       Default per reti sconosciute          Inbound: Block
                                                   Outbound: Allow (piu' restrittivo)
```

```powershell
# Profilo corrente
Get-NetConnectionProfile |
    Select-Object InterfaceAlias, NetworkCategory, IPv4Connectivity

# Cambiare profilo (es. da Public a Private)
Set-NetConnectionProfile -InterfaceAlias "Ethernet" -NetworkCategory Private
# NOTA: il profilo "Domain" e' assegnato automaticamente da NLA e non puo'
# essere forzato manualmente. Se il DC non e' raggiungibile, resta Public/Private.

# Stato firewall per profilo
Get-NetFirewallProfile | Select-Object Name, Enabled, DefaultInboundAction, DefaultOutboundAction

# Abilitare/Disabilitare firewall per profilo
Set-NetFirewallProfile -Profile Domain -Enabled True
Set-NetFirewallProfile -Profile Public -Enabled True

# Impostare default action
Set-NetFirewallProfile -Profile Domain -DefaultInboundAction Block -DefaultOutboundAction Allow
```

### Gestione Regole Firewall

```powershell
# Elencare tutte le regole abilitate
Get-NetFirewallRule -Enabled True |
    Select-Object DisplayName, Direction, Action, Profile -First 30

# Cercare regola per nome
Get-NetFirewallRule -DisplayName "*Remote Desktop*"

# Creare regola inbound (permettere RDP)
New-NetFirewallRule -DisplayName "Allow RDP" `
    -Direction Inbound -Protocol TCP -LocalPort 3389 `
    -Action Allow -Profile Domain, Private `
    -Description "Consente Remote Desktop da rete interna"

# Creare regola con restrizione IP sorgente
New-NetFirewallRule -DisplayName "Allow SSH Management" `
    -Direction Inbound -Protocol TCP -LocalPort 22 `
    -Action Allow -Profile Domain `
    -RemoteAddress "10.10.0.0/16", "192.168.1.0/24" `
    -Description "SSH solo da subnet di management"

# Creare regola outbound (bloccare traffico)
New-NetFirewallRule -DisplayName "Block Telemetry" `
    -Direction Outbound -Protocol TCP `
    -RemoteAddress "13.107.0.0/16" `
    -Action Block -Profile Any

# Creare regola per applicazione
New-NetFirewallRule -DisplayName "Allow SQL Server" `
    -Direction Inbound -Program "C:\Program Files\Microsoft SQL Server\MSSQL16\MSSQL\Binn\sqlservr.exe" `
    -Action Allow -Profile Domain

# Modificare regola esistente
Set-NetFirewallRule -DisplayName "Allow RDP" -RemoteAddress "10.10.0.0/16"

# Disabilitare regola
Disable-NetFirewallRule -DisplayName "Allow RDP"

# Rimuovere regola
Remove-NetFirewallRule -DisplayName "Block Telemetry"

# Regole con dettagli completi (port + address filter)
Get-NetFirewallRule -DisplayName "Allow RDP" | Get-NetFirewallPortFilter
Get-NetFirewallRule -DisplayName "Allow RDP" | Get-NetFirewallAddressFilter
```

### Connection Security Rules (IPsec)

Le Connection Security Rules (CSR) stabiliscono connessioni IPsec tra host. A differenza delle regole firewall che filtrano traffico, le CSR negoziano autenticazione e cifratura.

```powershell
# Elencare regole di sicurezza connessione
Get-NetIPsecRule | Select-Object DisplayName, Enabled, InboundSecurity, OutboundSecurity

# Creare regola IPsec (autenticazione richiesta per traffico tra server)
New-NetIPsecRule -DisplayName "Server-to-Server Auth" `
    -InboundSecurity Require -OutboundSecurity Require `
    -Phase1AuthSet (New-NetIPsecAuthProposal -Machine -Cert `
        -Authority "DC=contoso,DC=com" -AuthorityType Root | Out-Null; "default") `
    -RemoteAddress "10.10.10.0/24"

# Regola IPsec con Kerberos (ambiente AD)
$authProposal = New-NetIPsecAuthProposal -Machine -Kerberos
$authSet = New-NetIPsecPhase1AuthSet -DisplayName "KerberosAuth" -Proposal $authProposal
New-NetIPsecRule -DisplayName "Domain IPsec" `
    -InboundSecurity Require -OutboundSecurity Request `
    -Phase1AuthSet $authSet.Name `
    -Profile Domain

# Visualizzare Security Associations attive
Get-NetIPsecMainModeSA
Get-NetIPsecQuickModeSA

# Monitoring IPsec
# wf.msc → Monitoring → Security Associations → Main Mode / Quick Mode
```

### Firewall Logging

```powershell
# Abilitare logging firewall
Set-NetFirewallProfile -Profile Domain -LogFileName "C:\Windows\System32\LogFiles\Firewall\pfirewall.log"
Set-NetFirewallProfile -Profile Domain -LogMaxSizeKilobytes 32767
Set-NetFirewallProfile -Profile Domain -LogAllowed True -LogBlocked True

# Visualizzare log
Get-Content "C:\Windows\System32\LogFiles\Firewall\pfirewall.log" -Tail 50

# Formato log:
# date time action protocol src-ip dst-ip src-port dst-port size tcpflags ...

# Event log firewall (piu' strutturato)
Get-WinEvent -LogName "Microsoft-Windows-Windows Firewall With Advanced Security/Firewall" `
    -MaxEvents 20 | Select-Object TimeCreated, Id, Message
```

### Deployment via GPO

```
Percorso GPO:
Computer Configuration → Policies → Windows Settings → Security Settings
→ Windows Defender Firewall with Advanced Security

Struttura:
├── Windows Defender Firewall Properties (profili/default)
├── Inbound Rules
├── Outbound Rules
└── Connection Security Rules

Best practices GPO firewall:
1. NON sovrascrivere le regole locali (merge mode) a meno che necessario
2. Testare le regole in "Audit mode" prima di applicare Block
3. Usare security filtering GPO per applicare regole a gruppi specifici
4. Documentare ogni regola con il campo Description
5. Usare gruppi di IP/subnet per semplificare la gestione
6. Preferire regole per applicazione + porta (piu' specifiche)
```

```powershell
# Esportare configurazione firewall (backup)
netsh advfirewall export "C:\Temp\firewall-backup.wfw"

# Importare configurazione firewall (restore)
netsh advfirewall import "C:\Temp\firewall-backup.wfw"

# Reset firewall ai default
netsh advfirewall reset

# Visualizzare regole GPO applicate vs locali
Get-NetFirewallRule | Where-Object PolicyStoreSource -ne "PersistentStore" |
    Select-Object DisplayName, PolicyStoreSource
```

### Automazione Avanzata Regole Firewall con PowerShell

La gestione del firewall su larga scala richiede automazione. PowerShell permette di creare, auditare, esportare e replicare regole firewall su più server tramite CIM session remote.

#### Creazione Bulk di Regole da File CSV

```powershell
# Struttura CSV (rules.csv):
# DisplayName,Direction,Protocol,LocalPort,RemoteAddress,Action,Profile,Description
# "Allow HTTPS","Inbound","TCP","443","Any","Allow","Domain","Web traffic"
# "Allow DNS","Inbound","UDP","53","10.10.0.0/16","Allow","Domain","DNS queries"
# "Block Telnet","Inbound","TCP","23","Any","Block","Any","Telnet disabled"

$rules = Import-Csv "C:\Admin\firewall-rules.csv"
foreach ($rule in $rules) {
    $params = @{
        DisplayName  = $rule.DisplayName
        Direction    = $rule.Direction
        Protocol     = $rule.Protocol
        LocalPort    = $rule.LocalPort
        Action       = $rule.Action
        Profile      = $rule.Profile
        Description  = $rule.Description
    }
    if ($rule.RemoteAddress -ne "Any") {
        $params.RemoteAddress = $rule.RemoteAddress
    }
    New-NetFirewallRule @params -ErrorAction SilentlyContinue
}
Write-Output "Importate $($rules.Count) regole firewall."
```

#### Audit delle Regole Firewall Esistenti

```powershell
# Report completo delle regole abilitate con dettagli porta/indirizzo
Get-NetFirewallRule -Enabled True | ForEach-Object {
    $portFilter = $_ | Get-NetFirewallPortFilter
    $addrFilter = $_ | Get-NetFirewallAddressFilter
    [PSCustomObject]@{
        Name            = $_.DisplayName
        Direction       = $_.Direction
        Action          = $_.Action
        Profile         = $_.Profile
        Protocol        = $portFilter.Protocol
        LocalPort       = $portFilter.LocalPort
        RemotePort      = $portFilter.RemotePort
        RemoteAddress   = $addrFilter.RemoteAddress
        LocalAddress    = $addrFilter.LocalAddress
        PolicyStore     = $_.PolicyStoreSource
    }
} | Export-Csv "C:\Admin\firewall-audit.csv" -NoTypeInformation

# Individuare regole ridondanti o in conflitto
# Regole Allow e Block sulla stessa porta
$allRules = Get-NetFirewallRule -Enabled True
$portGroups = $allRules | ForEach-Object {
    $pf = $_ | Get-NetFirewallPortFilter
    [PSCustomObject]@{ Name = $_.DisplayName; Action = $_.Action; Port = $pf.LocalPort; Protocol = $pf.Protocol }
} | Group-Object Port, Protocol | Where-Object Count -gt 1
$portGroups | ForEach-Object {
    Write-Warning "Possibile conflitto su porta $($_.Name): $($_.Group.Name -join ', ')"
}
```

#### Gestione Remota via CIM Session

```powershell
# Applicare regole firewall su più server remoti contemporaneamente
$servers = @("SRV01", "SRV02", "SRV03", "SRV04")
$sessions = New-CimSession -ComputerName $servers -Credential (Get-Credential)

# Creare regola su tutti i server
$sessions | ForEach-Object {
    New-NetFirewallRule -CimSession $_ `
        -DisplayName "Allow WinRM HTTPS" `
        -Direction Inbound -Protocol TCP -LocalPort 5986 `
        -Action Allow -Profile Domain `
        -Description "WinRM over HTTPS per gestione remota"
}

# Verificare stato firewall su tutti i server
$sessions | ForEach-Object {
    $profile = Get-NetFirewallProfile -CimSession $_ -Profile Domain
    [PSCustomObject]@{
        Server   = $_.ComputerName
        Enabled  = $profile.Enabled
        Inbound  = $profile.DefaultInboundAction
        Outbound = $profile.DefaultOutboundAction
    }
} | Format-Table -AutoSize

# Chiudere le sessioni CIM
Remove-CimSession -CimSession $sessions
```

#### Backup e Restore Automatizzato

```powershell
# Script di backup automatico con data nel nome file
$backupPath = "C:\Admin\FirewallBackups"
$timestamp = Get-Date -Format "yyyy-MM-dd_HHmm"
if (-not (Test-Path $backupPath)) { New-Item -Path $backupPath -ItemType Directory }

# Backup via netsh (formato binario .wfw)
netsh advfirewall export "$backupPath\firewall_$timestamp.wfw"

# Backup via PowerShell (formato CSV leggibile)
Get-NetFirewallRule | ForEach-Object {
    $pf = $_ | Get-NetFirewallPortFilter
    $af = $_ | Get-NetFirewallAddressFilter
    [PSCustomObject]@{
        DisplayName   = $_.DisplayName
        Enabled       = $_.Enabled
        Direction     = $_.Direction
        Action        = $_.Action
        Profile       = $_.Profile
        Protocol      = $pf.Protocol
        LocalPort     = $pf.LocalPort
        RemoteAddress = $af.RemoteAddress
    }
} | Export-Csv "$backupPath\firewall_rules_$timestamp.csv" -NoTypeInformation

# Pulizia backup vecchi (mantieni ultimi 30 giorni)
Get-ChildItem $backupPath -File |
    Where-Object LastWriteTime -lt (Get-Date).AddDays(-30) |
    Remove-Item -Force
```

---

## Strumenti di Troubleshooting Rete

### ping e Test-Connection

```powershell
# Ping classico
ping 192.168.10.1 -n 4
ping -l 1472 -f 192.168.10.1   # Test MTU (1472 + 28 header = 1500)

# Test-Connection (PowerShell)
Test-Connection -ComputerName "SRV01" -Count 4
Test-Connection -ComputerName "SRV01" -Count 4 -BufferSize 1500
Test-Connection -ComputerName "SRV01" -Quiet    # Restituisce solo $true/$false

# Ping continuo con timestamp
Test-Connection -ComputerName "SRV01" -Repeat |
    ForEach-Object { "[{0}] {1} ms" -f (Get-Date -Format "HH:mm:ss"), $_.Latency }
```

### tracert e pathping

```cmd
:: tracert — mostra ogni hop verso la destinazione
tracert 8.8.8.8
tracert -d 8.8.8.8              :: -d = no reverse DNS (piu' veloce)
tracert -h 30 -w 2000 10.10.20.1 :: -h max hops, -w timeout ms

:: pathping — combinazione di tracert + statistiche packet loss per hop
pathping 8.8.8.8                :: Esegue 25 secondi di analisi per hop
pathping -n 8.8.8.8             :: -n = no reverse DNS
```

```powershell
# PowerShell equivalente con Test-NetConnection
Test-NetConnection -ComputerName "8.8.8.8" -TraceRoute
Test-NetConnection -ComputerName "SRV01" -TraceRoute -Hops 15
```

### nslookup e Resolve-DnsName

```cmd
:: nslookup interattivo
nslookup
> server 192.168.10.10
> set type=A
> webapp.corp.contoso.com
> set type=MX
> contoso.com
> set type=SRV
> _ldap._tcp.dc._msdcs.corp.contoso.com
> set debug                    :: output dettagliato
> exit

:: nslookup one-liner
nslookup webapp.corp.contoso.com 192.168.10.10
nslookup -type=MX contoso.com
```

```powershell
# Resolve-DnsName (sostituto moderno, preferire a nslookup)
Resolve-DnsName "webapp.corp.contoso.com"
Resolve-DnsName "contoso.com" -Type MX
Resolve-DnsName "_ldap._tcp.dc._msdcs.corp.contoso.com" -Type SRV
Resolve-DnsName "example.com" -Server 8.8.8.8 -DnsOnly    # Solo DNS, no cache/hosts
Resolve-DnsName "example.com" -Type AAAA                    # Record IPv6
```

### netstat e Get-NetTCPConnection

```cmd
:: netstat — connessioni di rete e porte in ascolto
netstat -an         :: tutte le connessioni, numerico
netstat -ano        :: con PID processo
netstat -anb        :: con nome processo (richiede admin)
netstat -s          :: statistiche per protocollo
netstat -e          :: statistiche Ethernet (errori, collisioni)
netstat -r          :: tabella routing
```

```powershell
# Get-NetTCPConnection (sostituto moderno di netstat)
# Porte in ascolto
Get-NetTCPConnection -State Listen |
    Select-Object LocalAddress, LocalPort, OwningProcess,
        @{N='ProcessName';E={(Get-Process -Id $_.OwningProcess).Name}} |
    Sort-Object LocalPort

# Connessioni attive
Get-NetTCPConnection -State Established |
    Select-Object LocalAddress, LocalPort, RemoteAddress, RemotePort,
        @{N='Process';E={(Get-Process -Id $_.OwningProcess).Name}}

# Connessioni UDP
Get-NetUDPEndpoint |
    Select-Object LocalAddress, LocalPort, OwningProcess,
        @{N='ProcessName';E={(Get-Process -Id $_.OwningProcess).Name}}

# Filtrare per porta specifica
Get-NetTCPConnection -LocalPort 443 -State Listen
Get-NetTCPConnection -RemotePort 3389

# Statistiche rete
Get-NetAdapterStatistics -Name "Ethernet"
```

### Test-NetConnection — Analisi Completa

```powershell
# Test-NetConnection (sostituto moderno di telnet)
Test-NetConnection -ComputerName "SRV01" -Port 443
Test-NetConnection -ComputerName "SRV01" -Port 3389 -InformationLevel Detailed
Test-NetConnection -ComputerName "SRV01" -TraceRoute

# Output Detailed include:
# - TCP test result
# - DNS resolution
# - Network adapter/interface
# - Source IP
# - Latency
# - Remote address

# Test porte comuni in bulk
$ports = @(22, 53, 80, 443, 445, 3389, 5985)
$target = "SRV01"
$ports | ForEach-Object {
    $result = Test-NetConnection -ComputerName $target -Port $_ -WarningAction SilentlyContinue
    [PSCustomObject]@{
        Port   = $_
        Open   = $result.TcpTestSucceeded
    }
} | Format-Table -AutoSize

# Test connettivita' Internet
Test-NetConnection -ComputerName "dns.google" -Port 443 -InformationLevel Detailed
```

### arp, route, ipconfig — Comandi Classici

```cmd
:: ARP table
arp -a                          :: visualizzare cache ARP
arp -d *                        :: cancellare cache ARP

:: Route table
route print                     :: tabella routing completa
route add 10.10.0.0 mask 255.255.0.0 192.168.10.1 -p  :: -p = persistente

:: ipconfig
ipconfig /all                   :: configurazione completa
ipconfig /flushdns              :: flush cache DNS
ipconfig /registerdns           :: registrare nel DNS
ipconfig /displaydns            :: visualizzare cache DNS
ipconfig /release               :: rilasciare lease DHCP
ipconfig /renew                 :: rinnovare lease DHCP
ipconfig /showclassid "Ethernet" :: mostrare DHCP class ID
```

```powershell
# Equivalenti PowerShell
Get-NetNeighbor                 # ARP table
Remove-NetNeighbor -Confirm:$false  # Clear ARP cache
Get-NetRoute                    # Route table
```

### Metodologia Sistematica di Troubleshooting Rete con PowerShell

Un approccio strutturato per livelli (dal livello fisico all'applicativo) permette di isolare la causa di un problema di rete in modo efficiente, evitando di perdere tempo su ipotesi casuali.

```
Livelli di Diagnostica Rete — Approccio Bottom-Up:
──────────────────────────────────────────────────────────────────
L1 — Fisico        Link up/down, velocità, duplex, errori NIC
L2 — Data Link     ARP resolution, VLAN tagging, MAC address
L3 — Rete          IP addressing, routing, ICMP, MTU
L4 — Trasporto     TCP/UDP connectivity, porte aperte, firewall
L7 — Applicazione  DNS, SMB, HTTP, autenticazione, certificati
```

#### Script di Diagnostica Completa

```powershell
# Diagnostica sistematica multi-livello — eseguire come Administrator

function Invoke-NetworkDiagnostic {
    param(
        [Parameter(Mandatory)]
        [string]$TargetHost,
        [int[]]$Ports = @(445, 3389, 5985)
    )

    Write-Host "`n=== L1 — STATO FISICO NIC ===" -ForegroundColor Cyan
    Get-NetAdapter | Where-Object Status -eq "Up" |
        Select-Object Name, InterfaceDescription, Status, LinkSpeed, MediaType |
        Format-Table -AutoSize

    # Errori NIC (indica problemi L1: cavo, porta switch, driver)
    Get-NetAdapter | Where-Object Status -eq "Up" | ForEach-Object {
        $stats = Get-NetAdapterStatistics -Name $_.Name
        if ($stats.ReceivedPacketErrors -gt 0 -or $stats.OutboundPacketErrors -gt 0) {
            Write-Warning "ERRORI su $($_.Name): RX=$($stats.ReceivedPacketErrors) TX=$($stats.OutboundPacketErrors)"
        }
    }

    Write-Host "`n=== L2 — ARP e MAC ===" -ForegroundColor Cyan
    $arpEntry = Get-NetNeighbor | Where-Object { $_.IPAddress -eq $TargetHost }
    if ($arpEntry) {
        Write-Host "ARP entry trovata: $($arpEntry.LinkLayerAddress) — Stato: $($arpEntry.State)"
    } else {
        Write-Warning "Nessuna entry ARP per $TargetHost — potrebbe indicare problema L2"
    }

    Write-Host "`n=== L3 — ROUTING e ICMP ===" -ForegroundColor Cyan
    $route = Find-NetRoute -RemoteIPAddress $TargetHost -ErrorAction SilentlyContinue
    if ($route) {
        Write-Host "Route: via $($route.NextHop) su $($route.InterfaceAlias[0])"
    }
    $ping = Test-Connection -ComputerName $TargetHost -Count 3 -Quiet
    Write-Host "Ping $TargetHost : $( if ($ping) { 'OK' } else { 'FALLITO' } )"

    Write-Host "`n=== L4 — PORTE TCP ===" -ForegroundColor Cyan
    foreach ($port in $Ports) {
        $result = Test-NetConnection -ComputerName $TargetHost -Port $port `
            -WarningAction SilentlyContinue
        $status = if ($result.TcpTestSucceeded) { "APERTA" } else { "CHIUSA/FILTRATA" }
        Write-Host "  Porta $port : $status"
    }

    Write-Host "`n=== L7 — DNS ===" -ForegroundColor Cyan
    try {
        $dnsResult = Resolve-DnsName $TargetHost -ErrorAction Stop
        Write-Host "DNS: $($dnsResult.Name) → $($dnsResult.IPAddress)"
    } catch {
        Write-Warning "DNS resolution fallita per $TargetHost"
    }

    Write-Host "`n=== PROFILO FIREWALL ===" -ForegroundColor Cyan
    Get-NetConnectionProfile | Select-Object InterfaceAlias, NetworkCategory |
        Format-Table -AutoSize
}

# Uso:
# Invoke-NetworkDiagnostic -TargetHost "fileserver.corp.contoso.com" -Ports 445, 3389, 5985
```

#### Pattern di Errore Comuni e Comandi Diagnostici

```
Sintomo                         Livello   Comando Diagnostico
─────────────────────────────────────────────────────────────────────────
Link down / no carrier          L1        Get-NetAdapter | Select Status, LinkSpeed
Errori CRC / collision          L1        Get-NetAdapterStatistics
No ARP entry per gateway        L2        Get-NetNeighbor -IPAddress 192.168.1.1
VLAN mismatch                   L2        Get-VMNetworkAdapterVlan
IP errato / no default gw       L3        Get-NetIPConfiguration
Route mancante                  L3        Find-NetRoute -RemoteIPAddress x.x.x.x
MTU mismatch (frammentazione)   L3        ping -l 1472 -f target
Porta filtrata da firewall      L4        Test-NetConnection -Port 445
TCP retransmission elevate      L4        Get-Counter "\TCPv4\Segments Retransmitted/sec"
DNS non risolve                 L7        Resolve-DnsName hostname; Clear-DnsClientCache
SMB access denied               L7        Get-SmbConnection; Get-SmbShareAccess
Certificato scaduto/invalido    L7        Test-NetConnection -Port 443 -InformationLevel Detailed
Profilo firewall errato         L4        Get-NetConnectionProfile
```

---

## Remote Access — VPN e DirectAccess

### Panoramica Soluzioni Remote Access

```
Soluzione           Tipo               Stato              Scenario
──────────────────────────────────────────────────────────────────────
Always On VPN       VPN user-tunnel    Raccomandato        Client Windows 10+
                    + device-tunnel
DirectAccess        IPsec/IPv6 tunnel  Legacy/Supportato   Windows Enterprise solo
RRAS VPN            VPN tradizionale   Disponibile         Connessione on-demand
SSTP VPN            VPN su HTTPS       Disponibile         Attraversare proxy/firewall
Point-to-Site VPN   Azure VPN Gateway  Cloud               Accesso a Azure vNet
```

### Always On VPN

Always On VPN (AOVPN) e' il successore di DirectAccess. Supporta sia user-tunnel che device-tunnel e funziona con qualsiasi edizione di Windows 10/11 (non richiede Enterprise).

```
Componenti Always On VPN:
- VPN server: RRAS su Windows Server
- NPS: RADIUS authentication (opzionale, raccomandato)
- CA: certificati machine + user
- DNS: record per il VPN endpoint
- Conditional Access: Azure AD / Entra ID (opzionale)
- Profilo VPN: distribuito via Intune, SCCM, o PowerShell

Protocolli supportati:
- IKEv2 (raccomandato per device-tunnel)
- SSTP (fallback attraverso firewall/proxy)
- L2TP/IPsec
- PPTP (deprecato, non usare)
```

```powershell
# Configurare profilo VPN via PowerShell (client)
Add-VpnConnection -Name "Corporate VPN" `
    -ServerAddress "vpn.contoso.com" `
    -TunnelType IKEv2 `
    -AuthenticationMethod EAP `
    -EncryptionLevel Maximum `
    -SplitTunneling $true `
    -RememberCredential $true

# Aggiungere route split-tunnel
Add-VpnConnectionRoute -ConnectionName "Corporate VPN" -DestinationPrefix "10.0.0.0/8"
Add-VpnConnectionRoute -ConnectionName "Corporate VPN" -DestinationPrefix "172.16.0.0/12"

# DNS suffix per VPN
$vpnProfile = Get-VpnConnection -Name "Corporate VPN"
Set-VpnConnectionTriggerDnsConfiguration -ConnectionName "Corporate VPN" `
    -DnsSuffix ".corp.contoso.com" -DnsSuffixSearchList @("corp.contoso.com")

# Device-tunnel (richiede SYSTEM context — deployment via task/Intune)
# Permette accesso alla rete aziendale PRIMA del login utente
# Necessario per: Group Policy refresh, certificati, script di login

# Visualizzare connessioni VPN configurate
Get-VpnConnection

# Connettere/Disconnettere
rasdial "Corporate VPN"
rasdial "Corporate VPN" /disconnect
```

### DirectAccess (Legacy)

```
DirectAccess crea un tunnel trasparente IPv6-su-IPv4 (IP-HTTPS).
- Il client si connette automaticamente senza azione dell'utente
- Richiede Windows Enterprise edition
- Richiede PKI (certificati machine)
- Utilizza IPv6 transition (IP-HTTPS, Teredo, 6to4)
- Gestito via GPO

Stato: supportato ma non piu' sviluppato.
Microsoft raccomanda la migrazione ad Always On VPN.
```

```powershell
# Verificare stato DirectAccess (client)
Get-DAClientExperienceConfiguration
Get-DAConnectionStatus

# Server-side (RRAS + DA role)
Get-RemoteAccess
Get-DAServer
```

### RRAS (Routing and Remote Access Service)

```powershell
# Installare ruolo RRAS
Install-WindowsFeature -Name Routing -IncludeManagementTools
Install-WindowsFeature -Name DirectAccess-VPN -IncludeManagementTools

# Configurare RRAS come VPN server
Install-RemoteAccess -VpnType Vpn

# Configurare pool IP per client VPN
$vpnConfig = Get-RemoteAccess
# GUI: rrasmgmt.msc → Properties → IPv4 → Static Address Pool

# Aggiungere protocolli VPN
Set-VpnServerConfiguration -TunnelType IKEv2 -CustomPolicy `
    -AuthenticationTransformConstants SHA256128 `
    -CipherTransformConstants AES256 `
    -DHGroup Group14 `
    -EncryptionMethod AES256 `
    -IntegrityCheckMethod SHA256 `
    -PfsGroup PFS2048

# Stato connessioni VPN attive
Get-RemoteAccessConnectionStatistics
```

### Confronto Protocolli VPN

```
Protocollo   Porta           Sicurezza       Velocita'    Note
─────────────────────────────────────────────────────────────────────
IKEv2        UDP 500/4500    Forte           Alta         Raccomandato, supporta
                                                          mobility (MOBIKE)
SSTP         TCP 443         Forte           Media        Attraversa proxy/firewall,
                                                          non richiede UDP
L2TP/IPsec   UDP 500/4500    Buona           Media        Doppio incapsulamento,
             + UDP 1701                                    problemi NAT traversal
WireGuard    UDP 51820       Forte           Molto alta   Non nativo Windows Server,
                                                          richiede software terze parti
OpenVPN      TCP/UDP custom  Forte           Alta         Non nativo, richiede
                                                          software terze parti
PPTP         TCP 1723        DEBOLE          Alta         DEPRECATO — non usare,
             + GRE                                         MS-CHAPv2 crackabile
```

---

## Network Policy Server (NPS) e RADIUS

### Panoramica NPS

NPS e' l'implementazione Microsoft del server RADIUS. Gestisce autenticazione, autorizzazione e accounting (AAA) per:

- VPN authentication
- 802.1X wired/wireless authentication
- Network access control

```powershell
# Installare NPS
Install-WindowsFeature -Name NPAS -IncludeManagementTools

# Registrare NPS in Active Directory (necessario per accedere agli account AD)
netsh ras set registeredserver domain=corp.contoso.com
# Oppure: NPS console → Action → Register Server in Active Directory
```

### Configurazione RADIUS

```powershell
# Aggiungere RADIUS client (es. VPN server, switch, access point)
# Via NPS console (nps.msc):
# RADIUS Clients → New
# - Friendly name: VPN-Server-01
# - Address: 192.168.10.5
# - Shared secret: (password complessa)
# - Vendor: RADIUS Standard

# Via netsh:
netsh nps add client name="VPN-Server-01" address=192.168.10.5 `
    sharedsecret="ComplexPassword123!" vendor="RADIUS Standard"

# Visualizzare client RADIUS
netsh nps show client

# Esportare configurazione NPS (backup)
Export-NpsConfiguration -Path "C:\Backup\nps-config.xml"

# Importare configurazione NPS
Import-NpsConfiguration -Path "C:\Backup\nps-config.xml"
```

### 802.1X Authentication

```
802.1X fornisce port-based network access control.
Componenti:
1. Supplicant: il client (Windows PC)
2. Authenticator: switch / access point (inoltra richieste a NPS)
3. Authentication server: NPS (RADIUS)

Metodi EAP supportati:
- EAP-TLS:         certificato client + server (piu' sicuro)
- PEAP-MSCHAPv2:   password + certificato server (piu' comune)
- PEAP-TLS:        certificato client dentro tunnel PEAP
- EAP-TTLS:        tunnel TLS con inner authentication

Flusso 802.1X:
1. Client si connette alla porta switch/WiFi
2. Switch invia EAP Request Identity
3. Client risponde con identita'
4. Switch inoltra a NPS (RADIUS Access-Request)
5. NPS verifica credenziali contro AD
6. NPS invia RADIUS Access-Accept o Access-Reject
7. Switch apre/blocca la porta
```

```powershell
# Abilitare 802.1X sul client Windows (servizio Wired AutoConfig)
Set-Service -Name dot3svc -StartupType Automatic
Start-Service -Name dot3svc

# Configurare profilo 802.1X via netsh (wired)
netsh lan set profileparameter interface="Ethernet" `
    authmode=user eaptype=25  # 25 = PEAP
```

### VPN Authentication con NPS

```
NPS come RADIUS proxy/server per VPN:

1. RRAS invia RADIUS Access-Request a NPS
2. NPS valuta:
   a. Connection Request Policy (quale policy processsa la richiesta)
   b. Network Policy (condizioni: gruppo AD, ora, tipo connessione)
   c. Health Policy (opzionale: NAP compliance)
3. Se match: NPS invia Access-Accept con attributi RADIUS
   (es. framed-IP, idle-timeout, session-timeout)
4. Se no match: Access-Reject

Network Policies tipiche:
- VPN Users: gruppo "VPN-Users" + EAP-TLS → Access-Accept
- VPN Denied: default → Access-Reject
- WiFi Corporate: gruppo "Domain Computers" + PEAP → Access-Accept
```

---

## BranchCache

### Panoramica

BranchCache riduce il consumo di banda WAN memorizzando nella cache locale i contenuti scaricati da file server e web server centrali.

```
Modalita' BranchCache:
─────────────────────────────────────────────────────────────
Distributed Cache    I client condividono la cache tra loro
                     via multicast. Nessun server locale.
                     Ideale per: filiali piccole (<50 client)

Hosted Cache         Un server locale ospita la cache.
                     I client pubblicano e recuperano contenuti
                     dal hosted cache server.
                     Ideale per: filiali medie/grandi (50+ client)
```

```powershell
# Verificare stato BranchCache
Get-BCStatus

# Abilitare BranchCache sul client (Distributed Cache mode)
Enable-BCDistributed

# Abilitare BranchCache sul client (Hosted Cache mode)
Enable-BCHostedClient -ServerNames "BranchCacheSrv.corp.contoso.com"

# Abilitare BranchCache sul server (content server)
Install-WindowsFeature -Name BranchCache -IncludeManagementTools
Enable-BCHostedServer -RegisterSCP
# SCP = Service Connection Point in AD per auto-discovery

# Configurare BranchCache sul file server
Install-WindowsFeature -Name FS-BranchCache

# Abilitare hash generation su una condivisione
# Via Server Manager → File and Storage Services → Shares → Properties
# → Caching → Enable BranchCache

# Verificare cache locale
Get-BCDataCache
Get-BCHashCache

# Statistiche BranchCache
Get-BCStatus | Select-Object -ExpandProperty ContentServerStatistics
Get-BCStatus | Select-Object -ExpandProperty ClientConfiguration

# Svuotare cache
Clear-BCCache -Force

# Via GPO:
# Computer Configuration → Policies → Administrative Templates → Network → BranchCache
# - Turn on BranchCache: Enabled
# - Set BranchCache Hosted Cache mode: Enabled
# - Set percentage of disk space used for client computer cache: 5%
```

---

## Quality of Service (QoS)

### Policy-Based QoS

Windows QoS permette di prioritizzare il traffico di rete tramite DSCP marking e bandwidth throttling.

```
DSCP (Differentiated Services Code Point):
Valore DSCP    Classe            Uso Tipico
──────────────────────────────────────────────────
46 (EF)        Expedited Fwd     VoIP, video real-time
34 (AF41)      Assured Fwd 4     Video streaming
26 (AF31)      Assured Fwd 3     Transazioni critiche
18 (AF21)      Assured Fwd 2     Traffico business
10 (AF11)      Assured Fwd 1     Bulk data
0  (BE)        Best Effort       Traffico generico
```

```powershell
# Creare QoS policy (DSCP marking)
New-NetQosPolicy -Name "VoIP" -AppPathNameMatchCondition "lync.exe" `
    -IPProtocolMatchCondition TCP -DSCPAction 46

New-NetQosPolicy -Name "SMB-Priority" -SMB -DSCPAction 26
New-NetQosPolicy -Name "LiveMigration" -LiveMigration -DSCPAction 34

# QoS con throttling (limitare banda)
New-NetQosPolicy -Name "Backup-Throttle" -AppPathNameMatchCondition "backup.exe" `
    -ThrottleRateActionBitsPerSecond 100000000  # 100 Mbps

# QoS per porta
New-NetQosPolicy -Name "HTTP-QoS" -IPPort 80 -IPProtocolMatchCondition TCP `
    -DSCPAction 10

# QoS per subnet
New-NetQosPolicy -Name "Branch-Office" `
    -IPDstPrefixMatchCondition "10.20.0.0/16" -DSCPAction 18

# Visualizzare policy QoS
Get-NetQosPolicy
Get-NetQosPolicy -Name "SMB-Priority"

# Rimuovere policy
Remove-NetQosPolicy -Name "Backup-Throttle" -Confirm:$false

# Via GPO:
# Computer Configuration → Policies → Windows Settings → Policy-based QoS
# Right-click → Create new policy
# Configurare: DSCP, throttle, applicazione, protocollo, porta, subnet
```

### DCB (Data Center Bridging)

DCB e' usato in ambienti data center per QoS hardware-level (richiede switch e NIC compatibili).

```powershell
# Installare feature DCB
Install-WindowsFeature -Name Data-Center-Bridging

# Abilitare DCB sulla NIC
Enable-NetAdapterQos -Name "Ethernet"

# Configurare traffic class (es. 40% SMB, 50% default, 10% management)
New-NetQosTrafficClass -Name "SMB-Direct" -Priority 3 -BandwidthPercentage 40 -Algorithm ETS
New-NetQosTrafficClass -Name "Management" -Priority 7 -BandwidthPercentage 10 -Algorithm ETS
# Default class (priority 0-2, 4-6) prende il restante

# Priority Flow Control (PFC) — no-drop per classe di traffico
Enable-NetQosFlowControl -Priority 3
Disable-NetQosFlowControl -Priority 0,1,2,4,5,6,7

# Verificare configurazione DCB
Get-NetQosTrafficClass
Get-NetQosFlowControl
Get-NetAdapterQos -Name "Ethernet"
```

---

## Network Monitoring e Packet Capture

### Packet Capture Nativo

```powershell
# Windows ha un packet capture nativo (netsh trace)

# Avviare cattura
netsh trace start capture=yes tracefile=C:\Temp\capture.etl maxsize=512

# Con filtri
netsh trace start capture=yes tracefile=C:\Temp\capture.etl `
    IPv4.Address=192.168.10.20 Protocol=TCP

# Fermare cattura
netsh trace stop

# Convertire .etl in .pcapng (per Wireshark)
# Usare etl2pcapng (tool Microsoft su GitHub)
# etl2pcapng.exe C:\Temp\capture.etl C:\Temp\capture.pcapng

# PKTMON (Windows Server 2019+ / Windows 10 2004+)
# Più potente di netsh trace

# Elencare componenti di rete
pktmon list

# Avviare cattura
pktmon start --capture --file-name C:\Temp\pktmon.etl

# Con filtri
pktmon filter add -t TCP -p 443
pktmon start --capture --file-name C:\Temp\pktmon.etl

# Fermare
pktmon stop

# Convertire in pcapng
pktmon etl2pcap C:\Temp\pktmon.etl --out C:\Temp\pktmon.pcapng

# Rimuovere filtri
pktmon filter remove
```

### pktmon — Scenari Avanzati

```powershell
# pktmon puo' catturare a diversi livelli dello stack di rete

# Visualizzare componenti di rete e dove catturare
pktmon list --all

# Cattura su un componente specifico (es. miniport driver)
pktmon start --capture --comp-id 12 --file-name C:\Temp\nic-capture.etl

# Cattura con contatori (senza salvare pacchetti — per diagnostica perdita)
pktmon start --capture --counters-only

# Visualizzare contatori
pktmon counters

# Cattura real-time (visualizza pacchetti in console)
pktmon start --capture --log-mode real-time

# Filtri multipli
pktmon filter add -t TCP -p 445               # SMB
pktmon filter add -t TCP -p 3389              # RDP
pktmon filter add -i 192.168.10.0/24          # subnet

# Reset
pktmon filter remove
pktmon reset
```

### Performance Monitor — Contatori di Rete

```powershell
# Contatori di Performance Monitor per la rete:

# Network Interface
# - Bytes Received/sec
# - Bytes Sent/sec
# - Packets Received Errors
# - Packets Outbound Errors
# - Output Queue Length (se > 2, congestione)
# - Current Bandwidth

# Leggere contatori via PowerShell
Get-Counter "\Network Interface(*)\Bytes Total/sec" -SampleInterval 1 -MaxSamples 5
Get-Counter "\Network Interface(*)\Packets Received Errors" -SampleInterval 1 -MaxSamples 3
Get-Counter "\Network Interface(*)\Output Queue Length"

# TCPv4
Get-Counter "\TCPv4\Connections Established"
Get-Counter "\TCPv4\Connection Failures"
Get-Counter "\TCPv4\Segments Retransmitted/sec"   # Indicatore problemi rete

# DNS
Get-Counter "\DNS\Total Query Received/sec"        # Solo su DNS server

# Creare Data Collector Set per monitoraggio continuo
$counters = @(
    "\Network Interface(*)\Bytes Total/sec",
    "\Network Interface(*)\Packets Received Errors",
    "\TCPv4\Segments Retransmitted/sec",
    "\TCPv4\Connections Established"
)
# Via Performance Monitor GUI: perfmon.msc → Data Collector Sets → User Defined
```

### Event Log per Networking

```powershell
# Log di rete rilevanti
Get-WinEvent -ListLog "*Network*" | Where-Object RecordCount -gt 0 |
    Select-Object LogName, RecordCount

# DHCP Client events
Get-WinEvent -LogName "Microsoft-Windows-Dhcp-Client/Operational" -MaxEvents 10

# DNS Client events
Get-WinEvent -LogName "Microsoft-Windows-DNS-Client/Operational" -MaxEvents 10

# NIC events (driver, link up/down)
Get-WinEvent -LogName "Microsoft-Windows-NDIS/Operational" -MaxEvents 10

# Firewall events
Get-WinEvent -LogName "Microsoft-Windows-Windows Firewall With Advanced Security/Firewall" `
    -MaxEvents 10

# SMB Client events
Get-WinEvent -LogName "Microsoft-Windows-SMBClient/Operational" -MaxEvents 10

# IPsec events
Get-WinEvent -LogName "Microsoft-Windows-WFP/Operational" -MaxEvents 10

# Filtrare per EventID specifico
Get-WinEvent -FilterHashtable @{
    LogName = "System"
    ProviderName = "Microsoft-Windows-NDIS"
    Level = 2  # Error
} -MaxEvents 20
```

---

## Network Security Hardening

### SMB Hardening

```powershell
# 1. Disabilitare SMB 1.0 (CRITICO)
Set-SmbServerConfiguration -EnableSMB1Protocol $false -Force
Disable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol -NoRestart

# 2. Richiedere SMB Signing
Set-SmbServerConfiguration -RequireSecuritySignature $true -Force
Set-SmbClientConfiguration -RequireSecuritySignature $true -Force

# 3. Abilitare SMB Encryption
Set-SmbServerConfiguration -EncryptData $true -Force
Set-SmbServerConfiguration -RejectUnencryptedAccess $true -Force

# 4. Disabilitare SMB guest access (Windows 10 1709+)
# Via GPO: Computer Configuration → Administrative Templates → Network
# → Lanman Workstation → Enable insecure guest logons: Disabled

# 5. Limitare accesso alle named pipe e condivisioni anonime
# Registry:
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\LanManServer\Parameters" `
    -Name "RestrictNullSessAccess" -Value 1

# 6. Configurare cipher suite SMB 3.1.1
Set-SmbServerConfiguration -EncryptionCiphers "AES_256_GCM, AES_128_GCM" -Force

# 7. Audit accessi SMB
Set-SmbServerConfiguration -AuditSmb1Access $true -Force
# Event log: Applications and Services Logs → SMBServer → Audit
```

### LDAP Channel Binding e Signing

```powershell
# LDAP Channel Binding previene attacchi relay LDAP

# Verificare stato corrente
Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\NTDS\Parameters" `
    -Name "LdapEnforceChannelBinding" -ErrorAction SilentlyContinue

# Impostare LDAP Channel Binding (su Domain Controller)
# 0 = Disabled
# 1 = When Supported (raccomandato come step intermedio)
# 2 = Always (raccomandato finale)
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\NTDS\Parameters" `
    -Name "LdapEnforceChannelBinding" -Value 2

# LDAP Signing (su Domain Controller)
# Via GPO: Computer Configuration → Policies → Windows Settings
# → Security Settings → Local Policies → Security Options
# "Domain controller: LDAP server signing requirements" = Require signing

# Verificare LDAP signing requirement
Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\NTDS\Parameters" `
    -Name "LDAPServerIntegrity" -ErrorAction SilentlyContinue
# 1 = Negotiate, 2 = Require

# Client-side LDAP signing
# GPO: "Network security: LDAP client signing requirements" = Require signing
```

### RPC Restrictions

```powershell
# Limitare RPC endpoint mapper
# Forzare RPC su range porte specifico (utile per firewall)
# Registry su ogni server:
New-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Rpc\Internet" `
    -Name "Ports" -Value "49152-49200" -PropertyType MultiString -Force
New-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Rpc\Internet" `
    -Name "PortsInternetAvailable" -Value "Y" -PropertyType String -Force
New-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Rpc\Internet" `
    -Name "UseInternetPorts" -Value "Y" -PropertyType String -Force
# Riavviare il servizio dopo la modifica
Restart-Service -Name RpcSs

# Firewall rules per RPC ristretto
New-NetFirewallRule -DisplayName "RPC Restricted" `
    -Direction Inbound -Protocol TCP `
    -LocalPort 49152-49200 `
    -Action Allow -Profile Domain
```

### Disabilitare Protocolli Legacy di Rete

```powershell
# Disabilitare LLMNR (Link-Local Multicast Name Resolution)
# LLMNR e' un vettore per Responder/NTLM relay
# Via GPO (raccomandato):
# Computer Configuration → Administrative Templates → Network → DNS Client
# → Turn off multicast name resolution: Enabled
# Via Registry:
New-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\DNSClient" `
    -Name "EnableMulticast" -Value 0 -PropertyType DWord -Force

# Disabilitare NetBIOS over TCP/IP
$adapters = Get-ChildItem "HKLM:\SYSTEM\CurrentControlSet\Services\NetBT\Parameters\Interfaces"
foreach ($adapter in $adapters) {
    Set-ItemProperty -Path $adapter.PSPath -Name "NetbiosOptions" -Value 2
}

# Disabilitare mDNS
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\Dnscache\Parameters" `
    -Name "EnableMDNS" -Value 0 -PropertyType DWord -Force

# Disabilitare WPAD (Web Proxy Auto-Discovery)
# WPAD e' un vettore per attacchi MITM
# Via GPO: disabilitare "Automatically detect settings" in IE/Edge
New-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Internet Settings\WinHttp" `
    -Name "DisableWpad" -Value 1 -PropertyType DWord -Force
```

### Hardening NLA (Network Level Authentication)

```powershell
# Forzare NLA per RDP
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp" `
    -Name "UserAuthentication" -Value 1

# Verificare NLA
Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp" `
    -Name "UserAuthentication"
# 1 = NLA abilitato (raccomandato)
# 0 = NLA disabilitato (insicuro)
```

---

## Software Defined Networking (SDN)

### Panoramica SDN in Windows Server

Software Defined Networking (SDN) in Windows Server separa il piano di controllo (control plane) dal piano dati (data plane), permettendo la gestione centralizzata e programmabile dell'infrastruttura di rete virtualizzata. SDN è particolarmente rilevante in ambienti Hyper-V e Azure Stack HCI.

```
Componenti SDN in Windows Server:
──────────────────────────────────────────────────────────────────
Network Controller     Piano di controllo centralizzato. Gestisce
                       configurazione, policy e monitoraggio di
                       tutta l'infrastruttura SDN. Espone REST API.

Software Load         Load balancer distribuito per traffico
Balancer (SLB)        Nord-Sud (esterno→interno) e Est-Ovest
                      (interno→interno). Equivalente di Azure LB.

RAS Gateway           Gateway multi-tenant per connettività
                      site-to-site (IPsec VPN, GRE tunnel) e
                      L3 forwarding verso reti esterne.

Hyper-V Network       Estensione del virtual switch Hyper-V per
Virtualization (HNV)  overlay networking (VXLAN). Isolamento
                      multi-tenant a livello L2/L3.

Network Security      Firewall distribuito (ACL) applicato a
Groups (NSG)          livello di vNIC delle VM. Filtraggio
                      stateful per traffico Est-Ovest.
```

### Novità SDN in Windows Server 2025

Windows Server 2025 introduce miglioramenti significativi all'architettura SDN:

```
Feature                   Dettagli
──────────────────────────────────────────────────────────────────
Network Controller        Ora eseguito come servizio Failover Cluster
su Failover Cluster       direttamente sull'host fisico. Non richiede
                          più VM dedicate per il Network Controller.
                          Semplifica il deployment e riduce il consumo
                          di risorse.

Tag-Based Segmentation    Le NSG possono utilizzare service tag custom
                          invece di range IP per definire le policy di
                          accesso. Etichette auto-esplicative (es.
                          "WebServers", "DatabaseTier") al posto di
                          blocchi CIDR complessi.

Default Network Policies  Policy NSG predefinite (stile Azure) applicate
                          automaticamente alle VM create tramite Windows
                          Admin Center. Default: deny all inbound,
                          allow all outbound.

SDN Multisite             Connettività nativa L2/L3 tra due siti senza
                          componenti aggiuntivi. Le applicazioni possono
                          migrare tra siti senza riconfigurare rete o
                          applicazione.

Gateway L3 Performance    Miglioramento throughput del 15-30% e riduzione
                          utilizzo CPU del 25-40% rispetto a Server 2022.
                          Miglioramenti abilitati di default.
```

### Deployment SDN con Windows Admin Center

```powershell
# Prerequisiti SDN:
# - Windows Server 2025 Datacenter (SDN richiede Datacenter edition)
# - Hyper-V abilitato su tutti gli host
# - Failover Clustering configurato
# - Windows Admin Center installato

# Installare le feature necessarie sugli host
Install-WindowsFeature -Name Hyper-V, Failover-Clustering, `
    RSAT-Hyper-V-Tools, RSAT-Clustering -IncludeManagementTools

# Verificare che gli host siano pronti per SDN
Get-WindowsFeature -Name Hyper-V, Failover-Clustering |
    Select-Object Name, InstallState

# Il deployment SDN tramite Windows Admin Center:
# 1. Aprire WAC → Cluster Manager → selezionare il cluster
# 2. Navigare a Networking → SDN Infrastructure
# 3. Seguire il wizard per configurare:
#    - Network Controller (cluster role)
#    - Software Load Balancer (opzionale)
#    - RAS Gateway (opzionale)
# 4. WAC genera automaticamente la configurazione JSON
#    e deploya i componenti SDN sugli host

# Verificare lo stato del Network Controller (PowerShell)
# Eseguire su un nodo del cluster con il ruolo NC
Get-NetworkController
Get-NetworkControllerNode
Get-NetworkControllerCluster

# Visualizzare le reti virtuali create
Get-NetworkControllerVirtualNetwork -ConnectionUri "https://nc.corp.contoso.com"

# Visualizzare le NSG (Network Security Groups)
Get-NetworkControllerAccessControlList -ConnectionUri "https://nc.corp.contoso.com"
```

### Service Tag e NSG

```powershell
# Creare un service tag (Windows Server 2025+)
# I service tag semplificano la gestione delle NSG sostituendo
# i range IP con etichette logiche

# Esempio: creare tag per i web server
$tag = New-Object Microsoft.Windows.NetworkController.ServiceTag
$tag.Properties = New-Object Microsoft.Windows.NetworkController.ServiceTagProperties
$tag.Properties.Type = "Custom"
$tag.Properties.AddressPrefixes = @("10.10.1.0/24", "10.10.2.0/24")

# Creare regola NSG usando il service tag
# Via Windows Admin Center:
# Networking → Network Security Groups → New Rule
# Source: ServiceTag "WebServers"
# Destination: ServiceTag "DatabaseTier"
# Port: 1433 (SQL Server)
# Action: Allow

# Creare regola default deny all inbound (applicata automaticamente in Server 2025)
# Questa policy viene creata di default per nuove VM in WAC:
# Priority 65000: Deny All Inbound
# Priority 65001: Allow All Outbound
# L'amministratore aggiunge poi regole specifiche con priorità più alta
```

### SDN Multisite

```
SDN Multisite (Windows Server 2025) consente:

1. Connettività L2 tra due siti
   - Le VM in siti diversi possono essere nella stessa subnet virtuale
   - Il traffico viene incapsulato in VXLAN tra i siti
   - Utile per: failover cluster stretched, live migration inter-sito

2. Connettività L3 tra due siti
   - Routing tra subnet virtuali di siti diversi
   - Policy di rete unificate (stesse NSG applicate su entrambi i siti)
   - Gateway L3 gestisce il forwarding inter-sito

3. Migrazione applicazioni
   - Le VM possono essere migrate tra siti senza riconfigurare rete
   - Gli indirizzi IP virtuali restano invariati
   - Le policy NSG seguono la VM nel nuovo sito

Requisiti SDN Multisite:
- Windows Server 2025 Datacenter su entrambi i siti
- Network Controller configurato su entrambi i siti
- Connettività IP tra i siti (WAN, ExpressRoute, VPN site-to-site)
- Latenza inter-sito < 150ms (raccomandato < 5ms per live migration)
```

---

## Tuning TCP/IP per Workload ad Alte Prestazioni

### TCP Autotuning

Windows utilizza un meccanismo di autotuning per la TCP Receive Window, che regola dinamicamente la dimensione della finestra di ricezione in base alle condizioni della rete. Per workload ad alte prestazioni (storage, database, replica), il livello di autotuning può essere regolato.

```
Livelli di Autotuning TCP:
──────────────────────────────────────────────────────────────────
Disabled            Finestra di ricezione fissa al valore default (64KB).
                    Solo per troubleshooting, mai in produzione.

HighlyRestricted    Finestra limitata oltre il default, ma può crescere
                    leggermente. Per ambienti con problemi di compatibilità.

Restricted          Crescita moderata della finestra. Bilancia performance
                    e compatibilità con apparati di rete legacy.

Normal (DEFAULT)    Crescita automatica in base alle condizioni di rete.
                    Adeguato per la maggior parte degli scenari.

Experimental        Crescita aggressiva per massimizzare il throughput.
                    Raccomandato per link WAN ad alta latenza (datacenter-
                    to-datacenter). Può migliorare il throughput del 20-50%
                    su connessioni ad alta latenza.
```

```powershell
# Visualizzare il livello di autotuning corrente
Get-NetTCPSetting | Select-Object SettingName, AutoTuningLevelLocal

# Visualizzare parametri TCP globali
netsh interface tcp show global

# Modificare il livello di autotuning
# Per workload ad alte prestazioni su WAN:
Set-NetTCPSetting -SettingName InternetCustom -AutoTuningLevelLocal Experimental

# Per tornare al default:
Set-NetTCPSetting -SettingName InternetCustom -AutoTuningLevelLocal Normal

# ATTENZIONE: alcuni tool di "ottimizzazione" o GPO aziendali disabilitano
# l'autotuning. Questo DEGRADA le performance sulla maggior parte dei workload.
# Verificare sempre che l'autotuning sia su Normal o superiore.
netsh interface tcp show global
# Se "Receive Window Auto-Tuning Level" = disabled → problema
```

### Receive Side Scaling (RSS) — Configurazione Avanzata

RSS distribuisce l'elaborazione dei pacchetti in ingresso su più core CPU tramite code hardware della NIC. Senza RSS, tutto il traffico di rete viene elaborato da un singolo core, creando un collo di bottiglia su server con traffico elevato.

```powershell
# Verificare stato RSS
Get-NetAdapterRss -Name "Ethernet"

# Abilitare RSS
Enable-NetAdapterRss -Name "Ethernet"

# Configurazione avanzata RSS
# Numero di code (dipende dal numero di core e dal carico)
Set-NetAdapterRss -Name "Ethernet" -NumberOfReceiveQueues 8

# Selezionare i processori per RSS (CPU affinity)
# Evitare CPU 0 (usata per interrupt e kernel)
Set-NetAdapterRss -Name "Ethernet" `
    -BaseProcessorGroup 0 `
    -BaseProcessorNumber 2 `
    -MaxProcessorNumber 9 `
    -MaxProcessors 8

# Profilo RSS (per scenari diversi)
Set-NetAdapterRss -Name "Ethernet" -Profile NUMAStatic
# Profili disponibili:
# Closest        → processori più vicini alla NIC (NUMA-aware, default)
# ClosestStatic  → come Closest ma senza ribilanciamento automatico
# NUMA           → distribuisce su tutti i nodi NUMA
# NUMAStatic     → come NUMA senza ribilanciamento (max performance)
# Conservative   → pochi processori, risparmio energetico

# Verificare la distribuzione del traffico sulle code
Get-NetAdapterRss -Name "Ethernet" | Select-Object -ExpandProperty IndirectionTable
```

### Receive Segment Coalescing (RSC)

RSC combina più segmenti TCP ricevuti in un singolo segmento più grande prima di passarlo allo stack di rete, riducendo l'overhead di elaborazione per-pacchetto.

```powershell
# Verificare stato RSC
Get-NetAdapterRsc -Name "Ethernet"

# Abilitare RSC per IPv4 e IPv6
Enable-NetAdapterRsc -Name "Ethernet" -IPv4 -IPv6

# NOTA: in Windows Server 2025, RSC potrebbe essere disabilitato di default
# in alcune configurazioni. Verificare e abilitare esplicitamente:
Set-NetAdapterAdvancedProperty -Name "Ethernet" `
    -DisplayName "Recv Segment Coalescing (IPv4)" -DisplayValue "Enabled"
Set-NetAdapterAdvancedProperty -Name "Ethernet" `
    -DisplayName "Recv Segment Coalescing (IPv6)" -DisplayValue "Enabled"

# RSC nel vSwitch Hyper-V (disabilitato di default)
# Abilitare RSC nel virtual switch per VM con traffico elevato:
Set-VMSwitch -Name "ConvergedSwitch" -EnableSoftwareRsc $true

# Verificare contatori RSC
Get-NetAdapterStatistics -Name "Ethernet" |
    Select-Object ReceivedBytes, SentBytes
```

### Congestion Provider (Algoritmo di Congestione TCP)

Windows supporta diversi algoritmi di congestione TCP. La scelta impatta il throughput e l'equità di condivisione della banda.

```powershell
# Visualizzare il congestion provider corrente
Get-NetTCPSetting | Select-Object SettingName, CongestionProvider

# Provider disponibili:
# CUBIC    → Default in Windows Server 2019+. Aggressivo nel recupero
#            della banda dopo una perdita. Ottimale per link ad alta
#            banda e alta latenza (WAN, datacenter).
# NewReno  → Classico, conservativo. Buona equità di condivisione.
#            Meno aggressivo di CUBIC.
# CTCP     → Compound TCP (legacy Windows). Combina delay-based e
# (CompoundTCP) loss-based congestion control.
# DCTCP    → Data Center TCP. Usa ECN per ridurre le code nei switch
#            del datacenter. SOLO per reti datacenter con supporto ECN
#            end-to-end. NON usare su Internet o WAN.

# Impostare CUBIC (raccomandato per la maggior parte degli scenari)
Set-NetTCPSetting -SettingName InternetCustom -CongestionProvider CUBIC

# Impostare DCTCP (solo per datacenter con ECN)
Set-NetTCPSetting -SettingName DatacenterCustom -CongestionProvider DCTCP

# Abilitare ECN (Explicit Congestion Notification)
Set-NetTCPSetting -SettingName DatacenterCustom -EcnCapability Enabled
# ECN permette ai router di segnalare congestione senza perdere pacchetti.
# Richiede supporto ECN su tutti gli apparati nel path.

# Visualizzare tutti i parametri TCP
Get-NetTCPSetting | Format-List *
```

### TCP Timestamps e Opzioni Avanzate

```powershell
# TCP Timestamps (RFC 1323) — abilitato di default
# Utile per calcolo RTT accurato e protezione da sequence number wrap
netsh interface tcp show global
# Voce: "TCP Timestamps" → enabled

# Se disabilitato (da GPO o tool di "ottimizzazione"):
netsh interface tcp set global timestamps=enabled

# TCP Selective Acknowledgments (SACK) — abilitato di default
# SACK permette la ritrasmissione selettiva di segmenti persi
# invece di ritrasmettere tutto dalla prima perdita
# NON disabilitare — impatto severo sulle performance in reti con perdita

# TCP Fast Open (TFO) — riduce latenza per connessioni ripetute
# Invia dati nel SYN, eliminando un RTT per connessioni successive
netsh interface tcp show global
# Voce: "TCP Fast Open" → enabled/disabled

# Initial RTO (Retransmission Timeout)
# Default: 1 secondo su Windows Server
# Per ambienti datacenter con bassa latenza, ridurre a 300ms:
Set-NetTCPSetting -SettingName DatacenterCustom -InitialRto 300
# ATTENZIONE: valori troppo bassi causano ritrasmissioni spurie su WAN
```

### Interrupt Moderation e Offloading

```powershell
# Interrupt Moderation — bilancia latenza e throughput
# La NIC aggrega gli interrupt per ridurre il carico CPU
Get-NetAdapterAdvancedProperty -Name "Ethernet" -DisplayName "Interrupt Moderation"

# Per workload a bassa latenza (trading, real-time):
Set-NetAdapterAdvancedProperty -Name "Ethernet" `
    -DisplayName "Interrupt Moderation" -DisplayValue "Disabled"
# Per workload ad alto throughput (storage, backup):
Set-NetAdapterAdvancedProperty -Name "Ethernet" `
    -DisplayName "Interrupt Moderation" -DisplayValue "Adaptive"
# "Adaptive" è il default raccomandato per la maggior parte degli scenari

# Interrupt Moderation Rate (se supportato dalla NIC)
Set-NetAdapterAdvancedProperty -Name "Ethernet" `
    -DisplayName "Interrupt Moderation Rate" -DisplayValue "High"
# Opzioni tipiche: Off, Low, Medium, Adaptive, High, Extreme

# Large Send Offload (LSO) — la NIC segmenta i pacchetti grandi
Get-NetAdapterLso -Name "Ethernet"
Enable-NetAdapterLso -Name "Ethernet" -IPv4 -IPv6

# Checksum Offload — la NIC calcola i checksum TCP/IP
Get-NetAdapterChecksumOffload -Name "Ethernet"
Set-NetAdapterChecksumOffload -Name "Ethernet" `
    -TcpIPv4 RxTxEnabled -UdpIPv4 RxTxEnabled `
    -TcpIPv6 RxTxEnabled -UdpIPv6 RxTxEnabled

# Verifica completa delle proprietà avanzate della NIC
Get-NetAdapterAdvancedProperty -Name "Ethernet" |
    Where-Object DisplayValue -ne "" |
    Select-Object DisplayName, DisplayValue, ValidDisplayValues |
    Format-Table -AutoSize
```

### Checklist Tuning TCP/IP per Alta Performance

```
Prima di dichiarare il tuning completato:
- [ ] TCP Autotuning Level = Normal o Experimental (non Disabled)
- [ ] RSS abilitato con almeno 4 code (evitare CPU 0)
- [ ] RSC abilitato per IPv4 e IPv6
- [ ] Jumbo Frames 9014 (se tutta la catena li supporta)
- [ ] Congestion Provider = CUBIC (WAN) o DCTCP (datacenter con ECN)
- [ ] LSO e Checksum Offload abilitati
- [ ] Interrupt Moderation = Adaptive (o Disabled per bassa latenza)
- [ ] SACK e TCP Timestamps abilitati (non disabilitare)
- [ ] Driver NIC aggiornato all'ultima versione del vendor
- [ ] Firmware NIC aggiornato
- [ ] Nessun tool di "ottimizzazione" ha alterato i parametri TCP
```

---

## WINS e NetBIOS

### Protocolli Legacy

```
NetBIOS e WINS sono protocolli legacy per la risoluzione nomi pre-DNS.
In ambienti moderni con AD, dovrebbero essere DISABILITATI per sicurezza
(LLMNR e NetBIOS sono vettori per attacchi come Responder).

Ordine risoluzione nomi con NetBIOS:
1. Cache NetBIOS locale: nbtstat -c
2. WINS server (se configurato)
3. Broadcast NetBIOS sulla subnet
4. File lmhosts (C:\Windows\System32\drivers\etc\lmhosts)
```

### Disabilitare NetBIOS e LLMNR

```powershell
# Disabilitare NetBIOS over TCP/IP (per adattatore)
$adapters = Get-ChildItem "HKLM:\SYSTEM\CurrentControlSet\Services\NetBT\Parameters\Interfaces"
foreach ($adapter in $adapters) {
    Set-ItemProperty -Path $adapter.PSPath -Name "NetbiosOptions" -Value 2
}

# Disabilitare LLMNR via GPO
# Computer → Administrative Templates → Network → DNS Client
# → Turn off multicast name resolution: Enabled

# Oppure via Registry
New-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\DNSClient" `
    -Name "EnableMulticast" -Value 0 -PropertyType DWord -Force

# Disabilitare mDNS
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\Dnscache\Parameters" `
    -Name "EnableMDNS" -Value 0 -PropertyType DWord -Force

# Verificare stato NetBIOS
nbtstat -n    # Nomi NetBIOS registrati
nbtstat -c    # Cache NetBIOS
nbtstat -r    # Statistiche risoluzione

# Se WINS è ancora necessario (ambienti legacy):
# Configurare WINS server come opzione DHCP (opzione 44)
# O configurare staticamente:
# Set-DnsClientServerAddress non gestisce WINS, usare netsh:
# netsh interface ipv4 set winsservers "Ethernet" static 192.168.10.10
```

---

## Best Practices

1. **DNS e' tutto**: in ambiente AD, DNS deve essere affidabile. Almeno 2 DNS server, client configurati correttamente, scavenging attivo
2. **Disabilitare protocolli legacy**: LLMNR, NetBIOS, WINS, mDNS, WPAD — sono vettori di attacco (Responder, relay, MITM)
3. **NIC Teaming per ridondanza**: ogni server critico deve avere almeno 2 NIC in teaming
4. **Documentare la configurazione**: IP, DNS, gateway, VLAN, NIC teaming — per ogni server
5. **Monitorare la rete**: packet capture periodico, baseline di traffico, alerting su anomalie
6. **IPv6**: se non lo si usa, disabilitarlo esplicitamente. Se lo si usa, configurarlo correttamente (non lasciare in auto-config)
7. **QoS**: in ambienti converged (dati + voce + storage), configurare QoS per prioritizzare il traffico critico
8. **SMB 1.0**: disabilitare su TUTTI i sistemi. E' il protocollo sfruttato da WannaCry/EternalBlue
9. **SMB Signing e Encryption**: abilitare su tutti i server e client. AES-GCM preferito su SMB 3.1.1
10. **Firewall profiles**: verificare che i server in dominio abbiano il profilo "Domain" attivo (dipende da raggiungibilita' DC via DNS)
11. **IPsec per segmentazione**: usare Connection Security Rules per cifrare traffico tra server critici
12. **Backup configurazione rete**: esportare regolarmente configurazione firewall, NPS, RRAS
13. **LDAP Channel Binding**: abilitare su tutti i DC (valore 2 = Always)
14. **RPC restrictions**: limitare range porte RPC per semplificare regole firewall
15. **NLA per RDP**: sempre abilitato — previene attacchi pre-authentication DoS
16. **Always On VPN**: preferire ad DirectAccess per nuovi deployment remote access
17. **Patch management**: driver NIC e firmware aggiornati — molte vulnerabilita' sono a livello driver

---

## Troubleshooting

**"Impossibile raggiungere server per nome ma ping per IP funziona"** → Problema DNS. Verificare `Resolve-DnsName`, flush cache (`Clear-DnsClientCache`), verificare DNS server configurato, controllare hosts file, verificare DNS suffix search list.

**"Connessione lenta o packet loss"** → Verificare duplex/speed con `Get-NetAdapter`, controllare errori NIC (`Get-NetAdapterStatistics`), testare con `pktmon` per identificare dove si perdono pacchetti, verificare switch port configuration.

**"NIC Teaming: failover non funziona"** → Verificare modalita' teaming, controllare cavi/porte switch, `Get-NetLbfoTeamMember` per stato dei membri, testare disabilitando un membro manualmente.

**"Accesso rete negato dopo join al dominio"** → Il profilo firewall potrebbe essere su "Public" invece di "Domain". Verificare con `Get-NetConnectionProfile`. Se il DC non e' raggiungibile via DNS al boot, il profilo rimane Public.

**"SMB share inaccessibile: 'Access Denied'"** → Verificare permessi NTFS + permessi condivisione (entrambi devono permettere l'accesso). Controllare `Get-SmbShareAccess -Name "NomeShare"`. Verificare che SMB Signing sia compatibile tra client e server. Se encryption e' richiesta dal server, il client deve supportare SMB 3.0+.

**"Connessione VPN fallisce con errore 812"** → NPS policy non corrisponde. Verificare che l'utente sia nel gruppo AD corretto, che la Network Policy su NPS abbia le condizioni corrette, e che il metodo EAP sia configurato correttamente sia su NPS che sul client.

**"VPN connessa ma nessun accesso alla rete interna"** → Verificare routing: split-tunnel vs full-tunnel. Controllare `Get-VpnConnection | Select-Object SplitTunneling`. Se split-tunnel, verificare che le route siano aggiunte (`Get-VpnConnectionRoute`). Controllare DNS: il client deve usare il DNS server interno via VPN.

**"Velocita' di rete inferiore al previsto con NIC 10GbE"** → Verificare Jumbo Frames (devono essere configurati su NIC, switch e tutti gli hop). Controllare RSS (`Get-NetAdapterRss`). Verificare TCP autotuning (`Get-NetTCPSetting`). Testare con `iperf3` o `NTttcp` per isolare il collo di bottiglia.

**"Impossibile accedere a server dopo abilitazione SMB Encryption"** → Client con Windows 7 o precedente non supportano SMB 3.0 encryption. Verificare il dialetto SMB in uso: `Get-SmbConnection`. Per ambienti misti, abilitare encryption per condivisione invece che globalmente.

**"DHCP: client ottiene IP APIPA (169.254.x.x)"** → Il client non riceve risposta dal server DHCP. Verificare connettivita' L2 (cavo, switch, VLAN). Controllare che il servizio DHCP sia attivo sul server. Se il client e' in una subnet diversa, verificare che il DHCP relay agent sia configurato. Controllare lo scope DHCP per indirizzi disponibili.

**"DNS: risoluzione intermittente"** → Verificare i DNS server configurati: `Get-DnsClientServerAddress`. Se il DNS primario e' lento/non risponde, il client switcha al secondario solo dopo timeout (1-2 secondi). Controllare latenza verso DNS server. Verificare che non ci siano regole NRPT che redirigono query.

**"Firewall: regola creata ma traffico ancora bloccato"** → Verificare ordine delle regole (Block ha priorita' su Allow se in conflitto). Controllare profilo: la regola potrebbe essere per "Domain" ma il profilo attivo e' "Public". Verificare con `Get-NetFirewallRule -DisplayName "NomeRegola" | Get-NetFirewallPortFilter`. Controllare connection security rules che potrebbero richiedere IPsec.

**"Hyper-V VM: no network dopo creazione vSwitch esterno"** → Quando si crea un vSwitch esterno con `AllowManagementOS $false`, l'host perde la connettivita'. Verificare con `Get-VMSwitch`. Soluzione: ricreare con `-AllowManagementOS $true` oppure aggiungere un secondo adattatore di management.

**"SMB Multichannel non attivo"** → Verificare che SMB 3.0+ sia in uso (`Get-SmbConnection | Select Dialect`). Le NIC devono essere in subnet diverse o la NIC deve avere RSS abilitato. NIC Teaming LBFO e' incompatibile con Multichannel (usare SET). Verificare: `Get-SmbMultichannelConnection`.

**"Latenza elevata su connessioni TCP"** → Controllare retransmissions: `Get-Counter "\TCPv4\Segments Retransmitted/sec"`. Verificare TCP autotuning: potrebbe essere disabilitato da un GPO o tool di "ottimizzazione". Controllare firewall/IDS inline che causano inspection delay. Usare `pathping` per identificare l'hop problematico.

**"802.1X: autenticazione fallisce su porta switch"** → Verificare che il servizio `dot3svc` (Wired AutoConfig) sia attivo. Controllare certificato machine/user (scaduto? revocato?). Verificare NPS event log per il motivo del rifiuto. Controllare shared secret RADIUS tra switch e NPS.

**"IPv6: indirizzi link-local ma nessun global address"** → Verificare che il router invii Router Advertisements (RA). Controllare firewall: ICMPv6 deve essere permesso. Se si usa DHCPv6, verificare che il server sia configurato e raggiungibile. Controllare: `Get-NetIPAddress -AddressFamily IPv6`.

**"BranchCache: nessun caching attivo"** → Verificare che la feature sia installata su client e content server. Controllare che la condivisione abbia hash generation abilitato. Verificare firewall: porte TCP 80 (HTTP) e WS-Discovery (UDP 3702). Controllare: `Get-BCStatus`.

**"Performance rete degradata dopo Windows Update"** → Verificare che driver NIC non siano stati aggiornati/regrediti. Controllare con `Get-NetAdapter | Select InterfaceDescription, DriverVersion`. Verificare che offloading settings non siano cambiati. Controllare se nuove regole firewall sono state aggiunte.

**"QoS DSCP marking non funziona"** → Verificare che la QoS policy sia applicata: `Get-NetQosPolicy`. Controllare che il NIC supporti DSCP offloading. Se si usa GPO, verificare che `gpresult /R` mostri la policy applicata. DSCP marking richiede che l'intera catena (NIC, switch, router) rispetti i valori DSCP.

---

## FAQ

**D: Devo disabilitare IPv6 in ambiente enterprise?**
R: Microsoft sconsiglia la disabilitazione completa di IPv6. Alcuni componenti Windows (Hyper-V networking, cluster failover, DirectAccess) dipendono da IPv6. L'approccio raccomandato e' preferire IPv4 senza disabilitare IPv6 (registry `DisabledComponents = 0x20`). Se si disabilita, testare accuratamente tutti i servizi prima del rollout.

**D: Qual e' la differenza tra LBFO e SET per NIC teaming?**
R: LBFO (Load Balancing and Failover) e' la soluzione classica, disponibile su tutti i Windows Server, supporta Switch Independent/LACP/Static. SET (Switch Embedded Teaming) e' integrato nel virtual switch Hyper-V, supporta RDMA, ed e' raccomandato per nuovi deployment Hyper-V. LBFO non riceve piu' nuove feature ed e' considerato legacy.

**D: SMB Signing impatta la performance?**
R: Si', SMB Signing aggiunge overhead CPU per la firma di ogni pacchetto. Su SMB 2.x/3.0 con SHA-256 HMAC, l'impatto e' circa 10-15%. Su SMB 3.1.1 con AES-GMAC (Windows Server 2022+), l'overhead e' minimo (<3%). In ogni caso, il beneficio di sicurezza supera l'impatto performance.

**D: Come faccio a sapere se il mio profilo firewall e' "Domain"?**
R: Eseguire `Get-NetConnectionProfile`. Se mostra `NetworkCategory: DomainAuthenticated`, il profilo e' Domain. Se mostra Private o Public, il PC non riesce a contattare un DC via DNS al boot. Verificare che il DNS server sia raggiungibile e che i record SRV di AD siano risolvibili.

**D: Quando usare Always On VPN vs DirectAccess?**
R: Always On VPN e' raccomandato per tutti i nuovi deployment. Supporta qualsiasi edizione Windows 10/11, IKEv2/SSTP, conditional access con Azure AD. DirectAccess richiede Windows Enterprise, usa IPv6 transition technologies (piu' complesse), e non riceve piu' nuove feature.

**D: Perche' LLMNR e NetBIOS sono pericolosi?**
R: Entrambi effettuano broadcast/multicast per la risoluzione nomi, senza autenticazione. Un attaccante con tool come Responder puo' rispondere a queste query, catturare hash NTLM, e usarli per relay attack o cracking offline. In ambiente AD con DNS funzionante, LLMNR e NetBIOS sono ridondanti e devono essere disabilitati.

**D: Come catturare traffico di rete su Windows senza installare Wireshark?**
R: Windows include `pktmon` (Windows 10 2004+ / Server 2019+) per packet capture a livello kernel. Supporta filtri per porta, protocollo, IP. Cattura in formato ETL convertibile in pcapng con `pktmon etl2pcap`. In alternativa, `netsh trace start capture=yes` e' disponibile su tutte le versioni moderne.

**D: Come funziona SMB Multichannel?**
R: SMB Multichannel usa automaticamente tutte le NIC disponibili tra client e server per aumentare throughput e resilienza. Requisiti: SMB 3.0+, almeno 2 NIC (o 1 con RSS). Le NIC devono poter raggiungere lo stesso server. Non e' compatibile con NIC Teaming LBFO — usare SET in ambienti Hyper-V.

**D: Come limitare le porte RPC per il firewall?**
R: Configurare il range porte RPC via registry su ogni server: `HKLM:\SOFTWARE\Microsoft\Rpc\Internet`, chiave `Ports` con il range desiderato (es. "49152-49200"), poi creare regola firewall per quel range. Questo semplifica enormemente le regole firewall in ambienti AD.

**D: E' possibile cifrare tutto il traffico SMB in rete?**
R: Si'. `Set-SmbServerConfiguration -EncryptData $true` forza encryption su tutte le condivisioni. Con `-RejectUnencryptedAccess $true`, i client che non supportano SMB 3.0+ vengono rifiutati. Verificare che tutti i client supportino SMB 3.0 prima di attivare globalmente.

**D: Qual e' il vantaggio di BranchCache rispetto a un DFS-R replica?**
R: BranchCache e' trasparente: i client scaricano dal server centrale, e il contenuto viene automaticamente cachato localmente per altri client. DFS-R replica l'intero dataset. BranchCache riduce banda WAN senza duplicare dati su un server locale (in modalita' Distributed). Hosted Cache richiede un server locale ma non replica tutto il dataset.

**D: Come diagnosticare se un problema e' DNS, rete, o firewall?**
R: Procedura sistematica: (1) `ping IP` del server — se funziona, la rete L3 e' ok. (2) `Resolve-DnsName hostname` — se fallisce, problema DNS. (3) `Test-NetConnection -Port 445` — se il ping funziona ma la porta no, e' firewall o servizio. (4) Controllare profilo firewall: `Get-NetConnectionProfile`. (5) Controllare event log rilevanti.

**D: Come migrare da DirectAccess a Always On VPN?**
R: Deployment side-by-side: installare VPN server separato, configurare NPS, distribuire profili VPN via Intune/SCCM. Migrazione graduale per gruppo di utenti. Entrambi possono coesistere. Dopo la migrazione completa, disabilitare DirectAccess GPO e decommissionare il server DA.

**D: DCB e' necessario per ambienti con SMB Direct (RDMA)?**
R: DCB (Data Center Bridging) con PFC (Priority Flow Control) e' necessario per RoCE v2 (RDMA over Converged Ethernet) per garantire no-drop sulle classi di traffico RDMA. Per iWARP, DCB non e' strettamente necessario ma raccomandato. Per InfiniBand, DCB non si applica.

**D: Come verificare che NPS stia processando le richieste RADIUS?**
R: Controllare NPS event log: Event Viewer → Custom Views → Server Roles → Network Policy and Access Services. Event ID 6272 = Access-Accept, Event ID 6273 = Access-Reject. Verificare anche il RADIUS accounting log in `C:\Windows\System32\LogFiles\`. Abilitare logging dettagliato in NPS console → Accounting.

---

## Esercizi

### Esercizio 1: Diagnostica TCP/IP e DNS

Su un server Windows di lab, eseguire una diagnostica completa della connettività di rete:

1. Raccogliere la configurazione IP di tutte le interfacce con `Get-NetIPConfiguration -Detailed`.
2. Verificare la risoluzione DNS per 5 hostname interni e 3 esterni con `Resolve-DnsName`.
3. Testare la connettività verso un file server su porta 445 con `Test-NetConnection -Port 445`.
4. Identificare il profilo firewall attivo con `Get-NetConnectionProfile` e spiegare le implicazioni di sicurezza.

**Criteri di validazione**: documentare ogni comando con output, identificare eventuali anomalie e proporre una correzione.

### Esercizio 2: NIC Teaming e Switch Embedded Teaming

Configurare un NIC team in un ambiente di lab (fisico o Hyper-V):

1. Creare un NIC team LBFO con due NIC in modalità Switch Independent / Address Hash tramite `New-NetLbfoTeam`.
2. Verificare il funzionamento con `Get-NetLbfoTeam` e testare il failover disconnettendo una NIC.
3. Se disponibile un host Hyper-V, creare un virtual switch SET con `New-VMSwitch -EnableEmbeddedTeaming $true` e confrontare il comportamento.

**Criteri di validazione**: throughput aggregato misurato con `Get-NetAdapterStatistics`, failover completato in < 5 secondi.

### Esercizio 3: Regole Firewall Avanzate

Creare un set di regole firewall per un file server:

1. Bloccare tutto il traffico in ingresso con una regola catch-all.
2. Permettere SMB (445/TCP) solo dalla subnet client (es. 10.0.1.0/24).
3. Permettere RDP (3389/TCP) solo dalla VLAN di gestione.
4. Permettere ICMP solo da server di monitoraggio specifici.
5. Esportare la configurazione con `netsh advfirewall export` e documentare ogni regola con `Get-NetFirewallRule`.

**Criteri di validazione**: `Test-NetConnection` dalla subnet autorizzata deve avere successo; dalla subnet non autorizzata deve fallire.

### Esercizio 4: SMB Security Hardening

Configurare un file server con SMB 3.x hardened:

1. Disabilitare SMB 1.0 con `Disable-WindowsOptionalFeature` e verificare con `Get-SmbServerConfiguration`.
2. Abilitare encryption globale con `Set-SmbServerConfiguration -EncryptData $true -RejectUnencryptedAccess $true`.
3. Abilitare signing obbligatorio con `Set-SmbServerConfiguration -RequireSecuritySignature $true`.
4. Verificare le connessioni attive con `Get-SmbSession` e `Get-SmbConnection` per confermare encryption e signing.
5. Disabilitare LLMNR e NetBIOS via GPO.

**Criteri di validazione**: `Get-SmbServerConfiguration` deve mostrare EncryptData=True, RequireSecuritySignature=True, EnableSMB1Protocol=False.

---

## Auto-valutazione

### Domanda 1

Qual è la differenza tra NIC Teaming LBFO e Switch Embedded Teaming (SET)?

<details>
<summary>Risposta</summary>

LBFO (Load Balancing and Failover) è la tecnologia di teaming tradizionale di Windows, funziona su qualsiasi Windows Server, e supporta fino a 32 NIC. SET è specifico per Hyper-V, integrato nel virtual switch, supporta fino a 8 NIC, ed è compatibile con RDMA e SR-IOV. LBFO non è compatibile con RDMA e non è supportato su NIC usate da un virtual switch Hyper-V dal Windows Server 2019 in poi. In ambienti Hyper-V, SET è la scelta raccomandata.

Riferimento: Microsoft Learn, Switch Embedded Teaming. Consultato: 2026-05-23.
</details>

### Domanda 2

Come funziona SMB Multichannel e quali sono i requisiti?

<details>
<summary>Risposta</summary>

SMB Multichannel utilizza automaticamente tutte le NIC disponibili tra client e server per aumentare throughput e resilienza. Requisiti: SMB 3.0 o superiore, almeno 2 NIC (o 1 con RSS abilitato). Le NIC devono poter raggiungere lo stesso server. Non è compatibile con NIC Teaming LBFO — in ambienti Hyper-V usare SET. La negoziazione Multichannel avviene nella fase di sessione SMB senza configurazione manuale.

Riferimento: Microsoft Learn, SMB Multichannel. Consultato: 2026-05-23.
</details>

### Domanda 3

Perché LLMNR e NetBIOS sono pericolosi in un ambiente Active Directory?

<details>
<summary>Risposta</summary>

Entrambi effettuano broadcast/multicast per la risoluzione nomi senza autenticazione. Un attaccante con tool come Responder può rispondere a queste query, catturare hash NTLM e usarli per relay attack o cracking offline. In ambiente AD con DNS funzionante, LLMNR e NetBIOS sono ridondanti. Disabilitare LLMNR via GPO (Computer Configuration → Administrative Templates → Network → DNS Client → Turn Off Multicast Name Resolution). Disabilitare NetBIOS via DHCP option 001 o nella configurazione NIC.

Riferimento: MITRE ATT&CK, T1557.001 — LLMNR/NBT-NS Poisoning. Consultato: 2026-05-23.
</details>

### Domanda 4

Qual è la differenza tra Always On VPN e DirectAccess?

<details>
<summary>Risposta</summary>

Always On VPN è raccomandato per tutti i nuovi deployment. Supporta qualsiasi edizione Windows 10/11, IKEv2/SSTP, conditional access con Azure AD, e riceve nuove funzionalità. DirectAccess richiede Windows Enterprise, usa IPv6 transition technologies (più complesse), e non riceve più nuove feature. Always On VPN è basato su standard aperti (IKEv2), DirectAccess su tecnologie proprietarie Microsoft (IP-HTTPS, Teredo, 6to4).

Riferimento: Microsoft Learn, Always On VPN deployment. Consultato: 2026-05-23.
</details>

### Domanda 5

Come catturare traffico di rete su Windows senza installare software di terze parti?

<details>
<summary>Risposta</summary>

Windows include `pktmon` (Windows 10 2004+ / Server 2019+) per packet capture a livello kernel. Supporta filtri per porta, protocollo, IP. Cattura in formato ETL convertibile in pcapng con `pktmon etl2pcap`. In alternativa, `netsh trace start capture=yes` è disponibile su tutte le versioni moderne e cattura in formato ETL analizzabile con Network Monitor o Message Analyzer. `pktmon` è preferibile per la granularità dei filtri e il minor overhead.

Riferimento: Microsoft Learn, Packet Monitor (pktmon). Consultato: 2026-05-23.
</details>

### Domanda 6

Come si limitano le porte RPC per semplificare le regole firewall in ambienti AD?

<details>
<summary>Risposta</summary>

Configurare il range porte RPC via registry su ogni server: `HKLM:\SOFTWARE\Microsoft\Rpc\Internet`, chiave `Ports` con il range desiderato (es. "49152-49200"), chiave `PortsInternetAvailable` = "Y", chiave `UseInternetPorts` = "Y". Poi creare una regola firewall per quel range. Questo riduce il range da 49152-65535 (16383 porte) a un set gestibile. Richiede riavvio del servizio RPC.

Riferimento: Microsoft Learn, How to configure RPC dynamic port allocation. Consultato: 2026-05-23.
</details>

---

## Letture Primarie Consigliate

1. **Microsoft Learn: Networking Fundamentals** — Documentazione ufficiale su TCP/IP, DNS, DHCP e stack di rete Windows.
   https://learn.microsoft.com/en-us/windows-server/networking/
   Consultato: 2026-05-23.

2. **Microsoft Learn: SMB Protocol** — Architettura SMB 3.x, security features, Multichannel e Direct.
   https://learn.microsoft.com/en-us/windows-server/storage/file-server/smb-overview
   Consultato: 2026-05-23.

3. **Microsoft Learn: Windows Firewall** — Configurazione avanzata, profili, e regole con PowerShell.
   https://learn.microsoft.com/en-us/windows/security/operating-system-security/network-security/windows-firewall/
   Consultato: 2026-05-23.

4. **Microsoft Learn: Always On VPN** — Deployment guide per Always On VPN con IKEv2 e conditional access.
   https://learn.microsoft.com/en-us/windows-server/remote/remote-access/vpn/always-on-vpn/
   Consultato: 2026-05-23.

5. **Microsoft Learn: NPS (RADIUS)** — Documentazione Network Policy Server per 802.1X e VPN authentication.
   https://learn.microsoft.com/en-us/windows-server/networking/technologies/nps/nps-top
   Consultato: 2026-05-23.

---

## Collegamenti Incrociati

| File | Relazione con questo modulo |
|---|---|
| [02-powershell.md](02-powershell.md) | Prerequisito: cmdlet di base per la gestione rete (`Get-NetAdapter`, `Test-NetConnection`) |
| [05-sicurezza-windows.md](05-sicurezza-windows.md) | Approfondimento: hardening di rete, disabilitazione LLMNR/NetBIOS, SMB signing |
| [07-storage-windows.md](07-storage-windows.md) | Contesto: SMB come protocollo di accesso allo storage, SMB Direct/RDMA |
| [23-hyper-v-guida-completa.md](23-hyper-v-guida-completa.md) | Contesto: virtual switch, SET, VLAN tagging in ambienti Hyper-V |
| [19-troubleshooting.md](19-troubleshooting.md) | Metodologie generali di diagnostica rete, complementare alla sezione troubleshooting |

---

## Glossario Locale

| Termine | Definizione |
|---|---|
| **DCB** | Data Center Bridging. Set di estensioni Ethernet (PFC, ETS) per traffico lossless, necessario per RoCE v2 (RDMA). |
| **LBFO** | Load Balancing and Failover. Tecnologia di NIC teaming nativa di Windows per aggregazione e ridondanza. |
| **LLMNR** | Link-Local Multicast Name Resolution. Protocollo di risoluzione nomi locale senza server DNS, vulnerabile a poisoning. |
| **NPS** | Network Policy Server. Implementazione Microsoft di RADIUS per autenticazione 802.1X e VPN. |
| **pktmon** | Packet Monitor. Tool nativo Windows per cattura pacchetti a livello kernel (Windows 10 2004+). |
| **RDMA** | Remote Direct Memory Access. Accesso diretto alla memoria del sistema remoto senza coinvolgere la CPU, usato da SMB Direct. |
| **RSS** | Receive Side Scaling. Distribuzione del traffico di rete su più code hardware e CPU per parallelismo. |
| **SET** | Switch Embedded Teaming. Teaming integrato nel virtual switch Hyper-V, compatibile con RDMA e SR-IOV. |
| **SMB** | Server Message Block. Protocollo di condivisione file e pipe di Windows. Versione corrente: SMB 3.1.1. |
| **WFP** | Windows Filtering Platform. Framework kernel per filtraggio pacchetti, usato da Windows Firewall e VPN. |
