# Servizi Infrastruttura — Guida Completa

> **Modulo 04** · **Tempo:** 60 min · **Aggiornamento:** 2026-04-27

## Idee guida

1. **DNS, DHCP, NTP, DC sono i 4 servizi-foundation.** Ognuno HA-protected.
2. **Time sync (NTP/PTP) e foundation: senza, Kerberos rompe.**
3. **DHCP scope = capacity planning.** Esauriente scope = utenti senza IP.
4. **Anycast DNS recursive piu robusto di unicast.**


## Indice

1. [Panoramica](#panoramica)
2. [Manutenzione DNS](#manutenzione-dns)
   - [DNS Server Windows (AD-Integrated)](#dns-server-windows-ad-integrated)
   - [DNS Server Linux (BIND9)](#dns-server-linux-bind9)
   - [DNS Monitoring e Alerting](#dns-monitoring-e-alerting)
   - [DNS Sicurezza](#dns-sicurezza)
   - [DNS Record Audit](#dns-record-audit)
3. [Manutenzione DHCP](#manutenzione-dhcp)
   - [DHCP Server Maintenance](#dhcp-server-maintenance)
   - [DHCP Audit e Reportistica](#dhcp-audit-e-reportistica)
4. [Manutenzione Email](#manutenzione-email)
   - [Exchange Server / Exchange Online](#exchange-server--exchange-online)
   - [Microsoft 365 Email](#microsoft-365-email)
   - [Email Security (SPF, DKIM, DMARC)](#email-security-spf-dkim-dmarc)
   - [Anti-Spam e Filtering](#anti-spam-e-filtering)
5. [Manutenzione Storage](#manutenzione-storage)
   - [SAN/NAS Management](#sannas-management)
   - [File Server](#file-server)
   - [Storage Capacity Planning](#storage-capacity-planning)
6. [Manutenzione Database](#manutenzione-database)
   - [SQL Server](#sql-server)
   - [PostgreSQL](#postgresql)
   - [MySQL/MariaDB](#mysqlmariadb)
   - [Database Backup e Recovery](#database-backup-e-recovery)
7. [Manutenzione Web Server](#manutenzione-web-server)
   - [IIS](#iis)
   - [Nginx/Apache](#nginxapache)
   - [Web Application Health](#web-application-health)
8. [Manutenzione Active Directory e LDAP](#manutenzione-active-directory-e-ldap)
   - [Active Directory Domain Services](#active-directory-domain-services)
   - [Manutenzione LDAP](#manutenzione-ldap)
   - [Group Policy Management](#group-policy-management)
   - [AD Security Hardening](#ad-security-hardening)
9. [Manutenzione NTP e PTP](#manutenzione-ntp-e-ptp)
   - [NTP — Network Time Protocol](#ntp--network-time-protocol)
   - [PTP — Precision Time Protocol](#ptp--precision-time-protocol)
   - [Monitoraggio e Troubleshooting Temporale](#monitoraggio-e-troubleshooting-temporale)
10. [Servizi File di Rete (NFS, SMB/CIFS)](#servizi-file-di-rete-nfs-smbcifs)
    - [NFS — Network File System](#nfs--network-file-system)
    - [SMB/CIFS — Server Message Block](#smbcifs--server-message-block)
    - [Ambienti Multi-Protocollo](#ambienti-multi-protocollo)
11. [Servizi di Stampa](#servizi-di-stampa)
    - [Windows Print Server](#windows-print-server)
    - [CUPS — Linux/Unix Print Server](#cups--linuxunix-print-server)
    - [Monitoraggio e Troubleshooting Stampa](#monitoraggio-e-troubleshooting-stampa)
12. [Manutenzione Virtualizzazione](#manutenzione-virtualizzazione)
    - [VMware vSphere / ESXi](#vmware-vsphere--esxi)
    - [Microsoft Hyper-V](#microsoft-hyper-v)
    - [Proxmox VE](#proxmox-ve)
    - [Infrastruttura Iperconvergente (HCI)](#infrastruttura-iperconvergente-hci)
13. [Servizi di Accesso alla Rete (RADIUS, TACACS+, 802.1X)](#servizi-di-accesso-alla-rete-radius-tacacs-8021x)
    - [RADIUS e 802.1X](#radius-e-8021x)
    - [TACACS+](#tacacs)
    - [Network Access Control (NAC)](#network-access-control-nac)
14. [PKI — Infrastruttura a Chiave Pubblica](#pki--infrastruttura-a-chiave-pubblica)
    - [Architettura PKI Aziendale](#architettura-pki-aziendale)
    - [Gestione del Ciclo di Vita dei Certificati](#gestione-del-ciclo-di-vita-dei-certificati)
    - [Automazione e ACME](#automazione-e-acme)
15. [IPAM e DDI — Gestione Indirizzi IP](#ipam-e-ddi--gestione-indirizzi-ip)
    - [IPAM — IP Address Management](#ipam--ip-address-management)
    - [DDI — DNS, DHCP e IPAM Integrati](#ddi--dns-dhcp-e-ipam-integrati)
    - [Transizione IPv6](#transizione-ipv6)
16. [Best Practices](#best-practices)
17. [Troubleshooting](#troubleshooting)

---

## Panoramica

I servizi infrastrutturali rappresentano le fondamenta su cui poggia l'intera operativita aziendale. Un'interruzione del DNS impedisce la risoluzione dei nomi e paralizza ogni applicazione; un guasto al servizio email blocca le comunicazioni interne ed esterne; un malfunzionamento dello storage rischia di compromettere i dati di produzione. Per questa ragione, la manutenzione proattiva di ciascun servizio infrastrutturale non e un'attivita facoltativa, ma un requisito imprescindibile per garantire continuita operativa, sicurezza e prestazioni adeguate.

Questa guida copre in modo approfondito e pratico i seguenti servizi critici:

- **DNS (Domain Name System):** risoluzione nomi, zone integrate in Active Directory, BIND9, sicurezza DNSSEC e audit dei record.
- **DHCP (Dynamic Host Configuration Protocol):** assegnazione automatica degli indirizzi IP, monitoraggio degli scope, failover e rilevamento di server DHCP non autorizzati.
- **Email:** manutenzione di Exchange Server e Microsoft 365, sicurezza delle comunicazioni con SPF, DKIM e DMARC, filtraggio anti-spam e protezione dal phishing.
- **Storage:** gestione SAN e NAS, monitoraggio delle prestazioni, file server, pianificazione della capacita e deduplicazione.
- **Database:** manutenzione di SQL Server, PostgreSQL, MySQL/MariaDB, strategie di backup e verifica del ripristino.
- **Web Server:** IIS, Nginx, Apache, monitoraggio delle applicazioni web e gestione dei certificati SSL/TLS.

Per ciascun servizio vengono forniti comandi operativi, soglie di allarme, procedure di audit e script di automazione. L'obiettivo e permettere a sistemisti e amministratori di rete di implementare un piano di manutenzione strutturato, riducendo al minimo i tempi di inattivita non pianificati e mantenendo un livello di servizio conforme agli SLA aziendali.

---

## Manutenzione DNS

Il DNS e uno dei servizi piu critici dell'infrastruttura IT. Quando il DNS non funziona correttamente, praticamente nulla funziona: la navigazione web si interrompe, le applicazioni non raggiungono i backend, la posta elettronica non viene instradata e l'autenticazione Active Directory fallisce. La manutenzione regolare del DNS previene guasti silenziosi che possono accumularsi fino a provocare interruzioni di servizio significative.

### DNS Server Windows (AD-Integrated)

Le zone DNS integrate in Active Directory offrono vantaggi significativi rispetto alle zone standard basate su file: la replica avviene tramite la replica di Active Directory stessa, si beneficia della sicurezza integrata e si elimina la necessita di configurare separatamente i trasferimenti di zona. Tuttavia, richiedono una manutenzione specifica.

**Verifica dello stato delle zone**

Il primo passo nella manutenzione DNS Windows consiste nel verificare lo stato di salute delle zone. Utilizzare il seguente comando PowerShell per ottenere un elenco completo delle zone e del loro stato:

```powershell
# Elenco di tutte le zone DNS con il relativo stato
Get-DnsServerZone | Select-Object ZoneName, ZoneType, DynamicUpdate, IsReverseLookupZone, IsDsIntegrated

# Verifica dello stato di una zona specifica
Get-DnsServerZone -Name "azienda.local" | Format-List *

# Controllo dei record in una zona
Get-DnsServerResourceRecord -ZoneName "azienda.local" | Where-Object {$_.RecordType -eq "A"} | Select-Object HostName, RecordType, @{N='IP';E={$_.RecordData.IPv4Address}}, Timestamp
```

**Configurazione dello scavenging (pulizia dei record obsoleti)**

Lo scavenging e fondamentale per rimuovere automaticamente i record DNS dinamici che non vengono piu rinnovati dai client. Senza scavenging, la zona si riempie progressivamente di record orfani che possono causare conflitti di risoluzione e rallentamenti.

```powershell
# Abilitare lo scavenging sulla zona
Set-DnsServerZoneAging -Name "azienda.local" -Aging $true -NoRefreshInterval 7.00:00:00 -RefreshInterval 7.00:00:00

# Verificare le impostazioni di aging della zona
Get-DnsServerZoneAging -Name "azienda.local"

# Abilitare lo scavenging sul server DNS
Set-DnsServerScavenging -ScavengingState $true -ScavengingInterval 7.00:00:00

# Eseguire lo scavenging manualmente (per test)
Start-DnsServerScavenging -Force

# Identificare record con timestamp obsoleto (piu vecchi di 30 giorni)
$soglia = (Get-Date).AddDays(-30)
Get-DnsServerResourceRecord -ZoneName "azienda.local" | Where-Object {
    $_.Timestamp -ne $null -and $_.Timestamp -lt $soglia
} | Select-Object HostName, RecordType, Timestamp
```

Si raccomanda di impostare il No-Refresh Interval e il Refresh Interval entrambi a 7 giorni. Lo Scavenging Interval dovrebbe essere di 7 giorni. Questo significa che un record dinamico che non viene rinnovato per 14 giorni (7 di no-refresh + 7 di refresh) diventa eleggibile per la rimozione allo scavenging successivo.

**Pulizia dei record obsoleti (Stale Records)**

```powershell
# Script per identificare e rimuovere record stale
$zone = "azienda.local"
$staleRecords = Get-DnsServerResourceRecord -ZoneName $zone | Where-Object {
    $_.Timestamp -ne $null -and
    $_.Timestamp -lt (Get-Date).AddDays(-21) -and
    $_.RecordType -in @("A", "AAAA", "PTR")
}

# Report dei record obsoleti
$staleRecords | Export-Csv -Path "C:\Reports\DNS-StaleRecords-$(Get-Date -Format 'yyyyMMdd').csv" -NoTypeInformation

# Rimozione dopo verifica manuale
foreach ($record in $staleRecords) {
    Remove-DnsServerResourceRecord -ZoneName $zone -Name $record.HostName -RRType $record.RecordType -Force -WhatIf
}
# Rimuovere -WhatIf solo dopo aver verificato l'output
```

**Audit dei Conditional Forwarders**

I conditional forwarders devono essere verificati periodicamente per assicurarsi che puntino a server DNS validi e raggiungibili:

```powershell
# Elenco dei conditional forwarders
Get-DnsServerZone | Where-Object {$_.ZoneType -eq "Forwarder"} | Select-Object ZoneName, MasterServers

# Verifica della raggiungibilita dei server di destinazione
$forwarders = Get-DnsServerZone | Where-Object {$_.ZoneType -eq "Forwarder"}
foreach ($fw in $forwarders) {
    foreach ($server in $fw.MasterServers) {
        $result = Test-Connection -ComputerName $server.IPAddressToString -Count 2 -Quiet
        Write-Output "Zona: $($fw.ZoneName) - Server: $($server.IPAddressToString) - Raggiungibile: $result"
    }
}
```

**DNS Debug Logging**

Il debug logging e essenziale per diagnosticare problemi di risoluzione e individuare query anomale:

```powershell
# Abilitare il debug logging
Set-DnsServerDiagnostics -All $true -LogFilePath "C:\DNS_Logs\dns_debug.log" -MaxMBFileSize 500

# Abilitare logging selettivo (meno impattante sulle prestazioni)
Set-DnsServerDiagnostics -Queries $true -Answers $true -LogFilePath "C:\DNS_Logs\dns_query.log"

# Verificare lo stato del logging
Get-DnsServerDiagnostics
```

Nota importante: il debug logging DNS e un'operazione che impatta le prestazioni del server. Si raccomanda di abilitarlo solo durante le sessioni di troubleshooting e di disabilitarlo al termine dell'indagine, oppure di utilizzare il logging selettivo limitato alle sole query.

### DNS Server Linux (BIND9)

BIND9 rimane il software DNS piu diffuso in ambiente Linux e richiede una manutenzione specifica basata su strumenti a linea di comando.

**Verifica dei file di zona**

Prima di applicare qualsiasi modifica ai file di zona, e obbligatorio eseguire la validazione sintattica:

```bash
# Verifica della configurazione generale di BIND
named-checkconf /etc/bind/named.conf
named-checkconf -z  # verifica anche le zone

# Verifica di un singolo file di zona
named-checkzone azienda.it /etc/bind/zones/db.azienda.it

# Verifica della zona inversa
named-checkzone 168.192.in-addr.arpa /etc/bind/zones/db.192.168

# Verifica completa con output dettagliato
named-checkzone -D azienda.it /etc/bind/zones/db.azienda.it

# Dump della cache per analisi
rndc dumpdb -cache
# Il file viene salvato in /var/cache/bind/named_dump.db

# Statistiche del server
rndc stats
# Le statistiche vengono salvate in /var/cache/bind/named.stats
```

**Rotazione delle chiavi DNSSEC**

DNSSEC richiede la rotazione periodica delle chiavi crittografiche per mantenere la sicurezza della firma digitale delle zone:

```bash
# Generare una nuova ZSK (Zone Signing Key) — rotazione ogni 90 giorni
dnssec-keygen -a ECDSAP256SHA256 -n ZONE azienda.it

# Generare una nuova KSK (Key Signing Key) — rotazione annuale
dnssec-keygen -a ECDSAP256SHA256 -n ZONE -f KSK azienda.it

# Firmare la zona con le nuove chiavi
dnssec-signzone -A -3 $(head -c 16 /dev/urandom | od -A n -t x | tr -d ' ') \
    -N INCREMENT -o azienda.it -t /etc/bind/zones/db.azienda.it

# Verificare le firme DNSSEC
dig @localhost azienda.it DNSKEY +dnssec
dig @localhost azienda.it SOA +dnssec

# Verifica della catena di fiducia
delv @localhost azienda.it SOA +rtrace
```

La rotazione della ZSK dovrebbe avvenire ogni 3 mesi, mentre la KSK va ruotata almeno una volta all'anno. E fondamentale mantenere la vecchia chiave attiva durante il periodo di transizione per evitare interruzioni nella validazione DNSSEC.

**Analisi dei log**

```bash
# Log delle query (se abilitato il query logging)
journalctl -u named --since "1 hour ago" | grep "query:"

# Identificare le query piu frequenti
journalctl -u named --since today | grep "query:" | awk '{print $NF}' | sort | uniq -c | sort -rn | head 20

# Identificare errori di risoluzione
journalctl -u named --since today | grep -E "(SERVFAIL|REFUSED|NXDOMAIN)" | head 50

# Monitoraggio in tempo reale
journalctl -u named -f

# Analisi dei trasferimenti di zona falliti
journalctl -u named | grep "transfer of" | grep -i "fail"
```

**Ottimizzazione delle prestazioni**

```bash
# Configurazione ottimizzata in /etc/bind/named.conf.options
# Dimensione della cache (adattare alla RAM disponibile)
# max-cache-size 512M;
# max-ncache-ttl 3600;
# minimal-responses yes;
# prefetch 2 9;

# Numero di thread (adattare ai core della CPU)
# Monitorare l'utilizzo con:
rndc status

# Verificare la dimensione della cache
rndc stats && grep "cache" /var/cache/bind/named.stats
```

### DNS Monitoring e Alerting

Il monitoraggio continuo del servizio DNS e indispensabile per rilevare degradi prestazionali e anomalie prima che impattino gli utenti.

**Metriche chiave da monitorare**

| Metrica | Descrizione | Soglia di Warning | Soglia Critica |
|---|---|---|---|
| Query Rate | Numero di query al secondo | > 5.000 qps | > 10.000 qps |
| Resolution Time | Tempo medio di risoluzione | > 50 ms | > 200 ms |
| NXDOMAIN Rate | Percentuale di risposte NXDOMAIN | > 15% | > 30% |
| Cache Hit Ratio | Percentuale di risposte dalla cache | < 70% | < 50% |
| SERVFAIL Rate | Percentuale di errori SERVFAIL | > 1% | > 5% |
| Recursive Query Failures | Query ricorsive fallite | > 2% | > 10% |

**Monitoraggio con Prometheus e Grafana**

Per BIND9, utilizzare il modulo `bind_exporter` per Prometheus:

```yaml
# prometheus.yml - configurazione dello scrape
scrape_configs:
  - job_name: 'bind'
    static_configs:
      - targets: ['dns-server:9119']
    scrape_interval: 30s

# Alert rules per DNS
groups:
  - name: dns_alerts
    rules:
      - alert: DNSHighQueryRate
        expr: rate(bind_resolver_queries_total[5m]) > 10000
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Query rate DNS elevato su {{ $labels.instance }}"

      - alert: DNSHighSERVFAIL
        expr: rate(bind_responses_total{result="SERVFAIL"}[5m]) / rate(bind_responses_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Tasso SERVFAIL superiore al 5% su {{ $labels.instance }}"

      - alert: DNSLowCacheHitRatio
        expr: bind_resolver_cache_hits / (bind_resolver_cache_hits + bind_resolver_cache_misses) < 0.5
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Cache hit ratio DNS inferiore al 50%"
```

**Monitoraggio con Zabbix**

```
# Template Zabbix per DNS
# Item: dns.query.time[azienda.local]
# Tipo: Simple check
# Chiave: net.dns.record[dns-server,azienda.local,A,2,2]
# Trigger: {dns-server:net.dns.record[dns-server,azienda.local,A,2,2].last()}=0
#   Severity: High
#   Descrizione: Risoluzione DNS fallita per azienda.local
```

### DNS Sicurezza

La sicurezza del DNS e un aspetto critico spesso sottovalutato. Un DNS compromesso puo reindirizzare il traffico verso server malevoli, intercettare credenziali e facilitare attacchi di tipo man-in-the-middle.

**Configurazione e manutenzione DNSSEC**

DNSSEC aggiunge firme crittografiche ai record DNS, permettendo ai resolver di verificare l'autenticita delle risposte:

```bash
# Verifica dello stato DNSSEC di un dominio
dig azienda.it +dnssec +short
dig azienda.it DNSKEY +short
dig azienda.it DS +short

# Validazione della catena DNSSEC
drill -S azienda.it
# oppure
delv azienda.it @8.8.8.8

# Monitoraggio della scadenza delle firme
# Le firme RRSIG hanno una data di scadenza che va monitorata
dig azienda.it RRSIG | grep -E "RRSIG.*SOA" | awk '{print "Scadenza:", $9}'
```

**DNS over HTTPS (DoH) e DNS over TLS (DoT)**

Per proteggere le query DNS dal monitoraggio e dalla manipolazione in transito:

```bash
# Test DoT con kdig
kdig -d @1.1.1.1 +tls-ca azienda.it A

# Test DoH
curl -H "accept: application/dns-json" "https://cloudflare-dns.com/dns-query?name=azienda.it&type=A"

# Configurazione BIND9 per DoT (named.conf)
# tls local-tls {
#     key-file "/etc/bind/ssl/dns-key.pem";
#     cert-file "/etc/bind/ssl/dns-cert.pem";
# };
# listen-on tls local-tls { any; };
```

**Response Rate Limiting (RRL)**

Il RRL protegge il server DNS dall'essere utilizzato come amplificatore in attacchi DDoS:

```bash
# Configurazione RRL in BIND9 (named.conf)
# rate-limit {
#     responses-per-second 10;
#     errors-per-second 5;
#     nxdomains-per-second 5;
#     slip 2;
#     window 15;
#     max-table-size 20000;
#     log-only no;
# };
```

**Blocco dei domini malevoli e DNS Sinkholing**

Il DNS sinkholing consiste nel reindirizzare le query verso domini noti come malevoli a un indirizzo IP controllato, impedendo ai dispositivi compromessi di comunicare con i server command-and-control:

```bash
# Aggiungere una zona di blocco in BIND9
# zone "dominio-malevolo.com" {
#     type master;
#     file "/etc/bind/zones/db.sinkhole";
#     allow-query { any; };
# };

# File db.sinkhole (reindirizza tutto a un IP interno di sinkhole)
# $TTL 86400
# @ IN SOA sinkhole.azienda.it. admin.azienda.it. (
#     2024010101 3600 900 604800 86400 )
# @ IN NS sinkhole.azienda.it.
# @ IN A 10.0.0.250
# * IN A 10.0.0.250

# Aggiornamento automatico delle blocklist
# Scaricare e convertire le liste di domini malevoli
# wget -O /tmp/blocklist.txt https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts
# Script per generare zone BIND dalle blocklist
```

In ambiente Windows, e possibile utilizzare le DNS Policy per implementare il sinkholing:

```powershell
# Creare una zona di blocco
Add-DnsServerQueryResolutionPolicy -Name "BlockMalware" -Action DENY -FQDN "EQ,*.dominio-malevolo.com"

# Reindirizzare a sinkhole
Add-DnsServerQueryResolutionPolicy -Name "SinkholeMalware" -Action ALLOW -FQDN "EQ,*.dominio-malevolo.com" -IPAddress "EQ,10.0.0.250"
```

### DNS Record Audit

L'audit periodico dei record DNS e necessario per mantenere la zona pulita, coerente e sicura.

**Procedura di audit regolare**

L'audit DNS dovrebbe essere eseguito con cadenza mensile e comprendere le seguenti verifiche:

1. **Coerenza dei record A con l'inventario IP:** ogni record A deve corrispondere a un dispositivo effettivamente presente nella rete.
2. **Coerenza dei record PTR:** ogni record A in una zona di ricerca diretta dovrebbe avere il corrispondente PTR nella zona inversa.
3. **Record orfani:** identificare record che puntano a indirizzi IP non piu assegnati o a dispositivi dismessi.
4. **Record CNAME in conflitto:** verificare che non esistano CNAME che puntano a CNAME (catene CNAME) o CNAME coesistenti con altri record dello stesso nome.
5. **Record MX validi:** verificare che i record MX puntino a server raggiungibili e configurati correttamente.

**Rilevamento dei record orfani**

```powershell
# Script PowerShell per trovare record DNS orfani
$zone = "azienda.local"
$records = Get-DnsServerResourceRecord -ZoneName $zone -RRType A

$orphans = @()
foreach ($record in $records) {
    $ip = $record.RecordData.IPv4Address.ToString()
    $ping = Test-Connection -ComputerName $ip -Count 1 -Quiet -TimeoutSeconds 2
    if (-not $ping) {
        $orphans += [PSCustomObject]@{
            HostName = $record.HostName
            IP = $ip
            Timestamp = $record.Timestamp
            Raggiungibile = $false
        }
    }
}

$orphans | Export-Csv -Path "C:\Reports\DNS-Orphans-$(Get-Date -Format 'yyyyMMdd').csv" -NoTypeInformation
Write-Output "Record potenzialmente orfani trovati: $($orphans.Count)"
```

**Verifica della coerenza PTR**

```powershell
# Verifica coerenza record A <-> PTR
$zone = "azienda.local"
$aRecords = Get-DnsServerResourceRecord -ZoneName $zone -RRType A

$inconsistencies = @()
foreach ($record in $aRecords) {
    $ip = $record.RecordData.IPv4Address.ToString()
    $ptrResult = Resolve-DnsName -Name $ip -Type PTR -ErrorAction SilentlyContinue

    if ($null -eq $ptrResult) {
        $inconsistencies += [PSCustomObject]@{
            HostName = $record.HostName
            IP = $ip
            Problema = "Record PTR mancante"
        }
    } elseif ($ptrResult.NameHost -ne "$($record.HostName).$zone") {
        $inconsistencies += [PSCustomObject]@{
            HostName = $record.HostName
            IP = $ip
            Problema = "PTR non corrisponde: $($ptrResult.NameHost)"
        }
    }
}

$inconsistencies | Format-Table -AutoSize
```

---

## Manutenzione DHCP

Il servizio DHCP assegna automaticamente gli indirizzi IP ai dispositivi della rete. Un malfunzionamento del DHCP impedisce ai nuovi dispositivi di ottenere un indirizzo IP e, alla scadenza dei lease esistenti, puo causare una perdita di connettivita progressiva su tutta la rete.

### DHCP Server Maintenance

**Monitoraggio dell'utilizzo degli scope**

La causa piu comune di problemi DHCP e l'esaurimento degli indirizzi disponibili in uno scope. E fondamentale monitorare costantemente la percentuale di utilizzo e impostare allarmi preventivi:

```powershell
# Verifica dell'utilizzo di tutti gli scope
Get-DhcpServerv4Scope | ForEach-Object {
    $stats = Get-DhcpServerv4ScopeStatistics -ScopeId $_.ScopeId
    [PSCustomObject]@{
        ScopeId = $_.ScopeId
        Nome = $_.Name
        SubnetMask = $_.SubnetMask
        InUso = $stats.InUse
        Liberi = $stats.Free
        Riservati = $stats.Reserved
        PercentualeUtilizzo = [math]::Round(($stats.InUse / ($stats.InUse + $stats.Free)) * 100, 1)
    }
} | Format-Table -AutoSize

# Identificare scope con utilizzo superiore all'80%
Get-DhcpServerv4Scope | ForEach-Object {
    $stats = Get-DhcpServerv4ScopeStatistics -ScopeId $_.ScopeId
    $percent = [math]::Round(($stats.InUse / ($stats.InUse + $stats.Free)) * 100, 1)
    if ($percent -gt 80) {
        Write-Warning "ATTENZIONE: Scope $($_.ScopeId) ($($_.Name)) al $percent% di utilizzo!"
    }
}
```

**Pulizia del database dei lease**

```powershell
# Elenco dei lease attivi con dettagli
Get-DhcpServerv4Lease -ScopeId "192.168.1.0" | Select-Object IPAddress, HostName, ClientId, LeaseExpiryTime, AddressState | Sort-Object LeaseExpiryTime

# Identificare lease scaduti o in stato anomalo
Get-DhcpServerv4Lease -ScopeId "192.168.1.0" | Where-Object {
    $_.AddressState -ne "Active"
} | Format-Table

# Rimuovere un lease specifico (in caso di conflitto IP)
Remove-DhcpServerv4Lease -ScopeId "192.168.1.0" -IPAddress "192.168.1.105"

# Backup del database DHCP prima della manutenzione
Backup-DhcpServer -Path "C:\Backup\DHCP\$(Get-Date -Format 'yyyyMMdd')"
```

**Audit delle opzioni di configurazione**

```powershell
# Verificare le opzioni a livello di server
Get-DhcpServerv4OptionValue

# Verificare le opzioni a livello di scope
Get-DhcpServerv4OptionValue -ScopeId "192.168.1.0"

# Report completo delle opzioni per tutti gli scope
Get-DhcpServerv4Scope | ForEach-Object {
    Write-Output "=== Scope: $($_.ScopeId) - $($_.Name) ==="
    Get-DhcpServerv4OptionValue -ScopeId $_.ScopeId | Format-Table OptionId, Name, Value -AutoSize
}
```

**Verifica dello stato del DHCP Failover**

Il failover DHCP garantisce la continuita del servizio in caso di guasto del server primario. La verifica periodica del suo stato e essenziale:

```powershell
# Stato di tutti i failover configurati
Get-DhcpServerv4Failover | Select-Object Name, PartnerServer, Mode, State, ScopeId

# Dettaglio di un failover specifico
Get-DhcpServerv4Failover -Name "DC01-DC02-Failover" | Format-List *

# Replica forzata dello scope (in caso di disallineamento)
Invoke-DhcpServerv4FailoverReplication -Name "DC01-DC02-Failover" -Force

# Verifica che i lease siano sincronizzati tra i partner
# Confrontare il numero di lease su entrambi i server
$server1Leases = (Get-DhcpServerv4Lease -ScopeId "192.168.1.0" -ComputerName "DC01").Count
$server2Leases = (Get-DhcpServerv4Lease -ScopeId "192.168.1.0" -ComputerName "DC02").Count
Write-Output "Lease su DC01: $server1Leases | Lease su DC02: $server2Leases | Differenza: $([Math]::Abs($server1Leases - $server2Leases))"
```

**Gestione delle riserve**

```powershell
# Elenco di tutte le riserve
Get-DhcpServerv4Scope | ForEach-Object {
    Get-DhcpServerv4Reservation -ScopeId $_.ScopeId | Select-Object ScopeId, IPAddress, ClientId, Name, Description
} | Format-Table -AutoSize

# Verifica che le riserve siano ancora necessarie (ping test)
Get-DhcpServerv4Scope | ForEach-Object {
    Get-DhcpServerv4Reservation -ScopeId $_.ScopeId
} | ForEach-Object {
    $raggiungibile = Test-Connection -ComputerName $_.IPAddress.ToString() -Count 1 -Quiet -TimeoutSeconds 2
    [PSCustomObject]@{
        IP = $_.IPAddress
        Nome = $_.Name
        MAC = $_.ClientId
        Raggiungibile = $raggiungibile
    }
} | Where-Object { -not $_.Raggiungibile } | Format-Table
```

### DHCP Audit e Reportistica

**Analisi dei log di audit DHCP**

Windows DHCP Server genera automaticamente log di audit nella cartella `%windir%\System32\dhcp`. Questi log contengono informazioni dettagliate su ogni operazione DHCP:

```powershell
# Percorso predefinito dei log DHCP
$logPath = "$env:windir\System32\dhcp"

# Analizzare i log dell'ultimo giorno
# I file sono nel formato DhcpSrvLog-*.log
Get-ChildItem "$logPath\DhcpSrvLog-*.log" -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending | Select-Object -First 7

# Cercare eventi specifici nei log
# Event ID 10 = New Lease
# Event ID 11 = Lease Renewed
# Event ID 12 = Lease Released
# Event ID 13 = Lease not found (potenziale conflitto)
# Event ID 15 = Lease denied (scope esaurito)
# Event ID 20 = BOOTP request
```

**Report sull'utilizzo degli indirizzi IP**

```powershell
# Report mensile sull'utilizzo IP
$report = Get-DhcpServerv4Scope | ForEach-Object {
    $stats = Get-DhcpServerv4ScopeStatistics -ScopeId $_.ScopeId
    [PSCustomObject]@{
        Data = Get-Date -Format "yyyy-MM-dd"
        ScopeId = $_.ScopeId
        Nome = $_.Name
        TotaleIndirizzi = $stats.InUse + $stats.Free
        InUso = $stats.InUse
        Liberi = $stats.Free
        Riservati = $stats.Reserved
        Percentuale = [math]::Round(($stats.InUse / ($stats.InUse + $stats.Free)) * 100, 1)
    }
}

$report | Export-Csv -Path "C:\Reports\DHCP-Usage-$(Get-Date -Format 'yyyyMM').csv" -NoTypeInformation -Append
```

**Rilevamento di server DHCP non autorizzati (Rogue DHCP)**

Un server DHCP non autorizzato sulla rete puo assegnare configurazioni errate ai client, causando interruzioni di servizio o compromissioni di sicurezza:

```powershell
# Verifica dei server DHCP autorizzati in Active Directory
Get-DhcpServerInDC | Format-Table DnsName, IPAddress

# Script per rilevare risposte DHCP non autorizzate sulla rete
# Utilizzare dhcptest o nmap per rilevare server DHCP rogue
# nmap --script broadcast-dhcp-discover -e eth0

# In ambiente Windows, controllare i log di sicurezza per eventi DHCP
# Event ID 1063: rogue DHCP server detected
Get-WinEvent -FilterHashtable @{LogName='System'; Id=1063} -MaxEvents 10 -ErrorAction SilentlyContinue
```

---

## Manutenzione Email

La posta elettronica rimane il canale di comunicazione aziendale primario. Un'interruzione del servizio email ha un impatto immediato e misurabile sulla produttivita e sulle relazioni commerciali. La manutenzione preventiva dei sistemi email deve coprire sia l'infrastruttura di messaggistica sia le misure di sicurezza che proteggono l'integrita delle comunicazioni.

### Exchange Server / Exchange Online

**Manutenzione del database delle caselle di posta**

```powershell
# Stato dei database
Get-MailboxDatabase -Status | Select-Object Name, Server, DatabaseSize, AvailableNewMailboxSpace, Mounted, BackupInProgress

# Verifica dell'integrita del database
# ATTENZIONE: eseguire solo durante finestre di manutenzione
# eseutil /mh "percorso_database.edb"

# Dimensione delle caselle di posta (top 20)
Get-Mailbox -ResultSize Unlimited | Get-MailboxStatistics | Sort-Object TotalItemSize -Descending | Select-Object DisplayName, TotalItemSize, ItemCount -First 20

# Caselle che superano la quota
Get-Mailbox -ResultSize Unlimited | Get-MailboxStatistics | Where-Object {
    $_.StorageLimitStatus -ne "BelowLimit"
} | Select-Object DisplayName, TotalItemSize, StorageLimitStatus
```

**Monitoraggio delle code di posta**

Le code di posta (queue) sono un indicatore critico dello stato di salute del flusso email. Code che crescono indicano problemi di consegna:

```powershell
# Stato delle code
Get-Queue | Select-Object Identity, DeliveryType, Status, MessageCount, NextHopDomain

# Code con messaggi in attesa
Get-Queue | Where-Object {$_.MessageCount -gt 0} | Format-Table Identity, Status, MessageCount, LastError -AutoSize

# Dettaglio dei messaggi in coda
Get-Queue -Identity "server\coda" | Get-Message | Select-Object FromAddress, Recipients, Subject, DateReceived, LastError

# Forzare il retry di una coda bloccata
Retry-Queue -Identity "server\coda"

# Monitoraggio continuo delle code (ogni 30 secondi)
# while ($true) { Get-Queue | Where-Object {$_.MessageCount -gt 10}; Start-Sleep 30 }
```

**Test del flusso email**

```powershell
# Test del flusso email interno
Test-MailFlow -TargetEmailAddress utente@azienda.it

# Invio di un messaggio di test
Send-MailMessage -From "monitoring@azienda.it" -To "admin@azienda.it" -Subject "Test flusso email $(Get-Date)" -Body "Test automatico" -SmtpServer "exchange.azienda.local"

# Verifica della connettivita SMTP esterna
Test-NetConnection -ComputerName "smtp.destinazione.it" -Port 25
Test-NetConnection -ComputerName "smtp.destinazione.it" -Port 587

# Test del certificato SMTP
# openssl s_client -connect mail.azienda.it:587 -starttls smtp
```

**Verifica dello stato del DAG (Database Availability Group)**

```powershell
# Stato del DAG
Get-DatabaseAvailabilityGroup | Format-List Name, Servers, WitnessServer, WitnessDirectory

# Stato delle copie del database
Get-MailboxDatabaseCopyStatus * | Select-Object Name, Status, CopyQueueLength, ReplayQueueLength, ContentIndexState | Format-Table -AutoSize

# Identificare copie in stato non sano
Get-MailboxDatabaseCopyStatus * | Where-Object {
    $_.Status -ne "Mounted" -and $_.Status -ne "Healthy"
} | Format-Table Name, Status, CopyQueueLength, ReplayQueueLength -AutoSize

# Test della replica
Test-ReplicationHealth | Format-Table Server, Check, Result, Error -AutoSize
```

**Gestione dei certificati**

```powershell
# Elenco dei certificati Exchange
Get-ExchangeCertificate | Select-Object Subject, Thumbprint, NotAfter, Services, Status | Format-Table -AutoSize

# Certificati in scadenza nei prossimi 30 giorni
Get-ExchangeCertificate | Where-Object {
    $_.NotAfter -lt (Get-Date).AddDays(30) -and $_.NotAfter -gt (Get-Date)
} | Select-Object Subject, NotAfter

# Audit dei connettori
Get-ReceiveConnector | Select-Object Name, Bindings, RemoteIPRanges, AuthMechanism | Format-List
Get-SendConnector | Select-Object Name, AddressSpaces, SmartHosts, TlsAuthLevel | Format-List
```

### Microsoft 365 Email

**Monitoraggio della salute del servizio**

```powershell
# Richiede il modulo ExchangeOnlineManagement
# Connect-ExchangeOnline -UserPrincipalName admin@azienda.onmicrosoft.com

# Stato del servizio (tramite Microsoft Graph)
# Utilizzare il portale admin.microsoft.com o Microsoft Graph API
# GET https://graph.microsoft.com/v1.0/admin/serviceAnnouncement/healthOverviews

# Report sul flusso email degli ultimi 7 giorni
Get-MailFlowStatusReport -StartDate (Get-Date).AddDays(-7) -EndDate (Get-Date)
```

**Audit delle regole di flusso email**

Le regole di trasporto (Transport Rules) e le regole di flusso email devono essere revisionate periodicamente per verificare che siano ancora pertinenti e non creino conflitti:

```powershell
# Elenco delle regole di trasporto
Get-TransportRule | Select-Object Name, State, Priority, Description | Format-Table -AutoSize

# Dettaglio di una regola specifica
Get-TransportRule -Identity "Nome Regola" | Format-List *

# Regole disabilitate (candidati alla rimozione)
Get-TransportRule | Where-Object {$_.State -eq "Disabled"} | Select-Object Name, WhenChanged

# Gestione della quarantena
Get-QuarantineMessage -StartReceivedDate (Get-Date).AddDays(-7) | Select-Object Subject, SenderAddress, RecipientAddress, QuarantineTypes, ReleaseStatus | Format-Table -AutoSize

# Rilascio di un messaggio dalla quarantena
# Release-QuarantineMessage -Identity <MessageId> -ReleaseToAll
```

**Revisione delle policy DLP (Data Loss Prevention)**

```powershell
# Elenco delle policy DLP
Get-DlpCompliancePolicy | Select-Object Name, Enabled, Mode, ExchangeLocation

# Dettaglio delle regole DLP
Get-DlpComplianceRule | Select-Object Name, ParentPolicyName, ContentContainsSensitiveInformation, BlockAccess

# Report sulle violazioni DLP (ultimi 30 giorni)
# Disponibile nel Security & Compliance Center
# https://compliance.microsoft.com/reports/DLPPolicyMatchesReport
```

### Email Security (SPF, DKIM, DMARC)

SPF, DKIM e DMARC costituiscono il trittico essenziale per l'autenticazione delle email e la protezione contro lo spoofing. La loro corretta configurazione e manutenzione e fondamentale per la deliverability delle email e per la protezione del marchio aziendale.

**Configurazione e validazione SPF**

SPF (Sender Policy Framework) specifica quali server sono autorizzati a inviare email per conto del dominio:

```bash
# Verificare il record SPF attuale
dig TXT azienda.it | grep "v=spf1"
nslookup -type=TXT azienda.it

# Esempio di record SPF ben strutturato
# v=spf1 ip4:203.0.113.0/24 include:spf.protection.outlook.com include:_spf.google.com -all

# Verificare che il record SPF non superi il limite di 10 lookup DNS
# Ogni meccanismo "include", "a", "mx", "redirect" conta come un lookup
# Strumenti online: mxtoolbox.com/spf.aspx oppure dmarcian.com/spf-survey

# Test di validazione SPF da linea di comando
# spfquery -ip 203.0.113.10 -sender user@azienda.it -helo mail.azienda.it
```

Errori comuni da evitare nel record SPF:
- Superare il limite di 10 meccanismi DNS (causa PermError)
- Utilizzare `~all` (softfail) invece di `-all` (hardfail) in produzione
- Dimenticare di includere tutti i servizi che inviano email (CRM, marketing, ticketing)
- Record SPF multipli (deve essercene uno solo per dominio)

**Rotazione delle chiavi DKIM**

DKIM (DomainKeys Identified Mail) firma crittograficamente le email in uscita, permettendo al destinatario di verificarne l'integrita:

```bash
# Verificare il record DKIM attuale
dig TXT selector1._domainkey.azienda.it
dig TXT selector2._domainkey.azienda.it

# Generare una nuova coppia di chiavi DKIM (2048 bit)
openssl genrsa -out dkim_private.pem 2048
openssl rsa -in dkim_private.pem -pubout -out dkim_public.pem

# Il contenuto di dkim_public.pem va inserito nel record DNS TXT
# selector2024._domainkey.azienda.it IN TXT "v=DKIM1; k=rsa; p=MIIBIjANBg..."
```

La rotazione delle chiavi DKIM dovrebbe avvenire ogni 6-12 mesi. Il processo prevede:
1. Generare la nuova chiave con un nuovo selector (es. `selector2024q2`)
2. Pubblicare il record DNS con il nuovo selector
3. Attendere la propagazione DNS (24-48 ore)
4. Configurare il server email per utilizzare il nuovo selector
5. Mantenere il vecchio selector attivo per 7 giorni per consentire la validazione delle email in transito
6. Rimuovere il vecchio record DNS

**Progressione della policy DMARC**

DMARC (Domain-based Message Authentication, Reporting and Conformance) indica ai server riceventi come trattare le email che falliscono i controlli SPF e DKIM:

```bash
# Verificare il record DMARC attuale
dig TXT _dmarc.azienda.it

# Progressione raccomandata della policy DMARC:
# Fase 1 (Monitoraggio - 2-4 settimane):
# _dmarc.azienda.it IN TXT "v=DMARC1; p=none; rua=mailto:dmarc-reports@azienda.it; ruf=mailto:dmarc-forensic@azienda.it; pct=100"

# Fase 2 (Quarantena parziale - 2-4 settimane):
# _dmarc.azienda.it IN TXT "v=DMARC1; p=quarantine; pct=25; rua=mailto:dmarc-reports@azienda.it"

# Fase 3 (Quarantena totale - 2-4 settimane):
# _dmarc.azienda.it IN TXT "v=DMARC1; p=quarantine; pct=100; rua=mailto:dmarc-reports@azienda.it"

# Fase 4 (Rifiuto - obiettivo finale):
# _dmarc.azienda.it IN TXT "v=DMARC1; p=reject; rua=mailto:dmarc-reports@azienda.it; ruf=mailto:dmarc-forensic@azienda.it"
```

**Analisi dei report DMARC**

I report aggregati DMARC (inviati all'indirizzo `rua`) sono file XML che contengono statistiche sulle email inviate dal dominio. E fondamentale analizzarli regolarmente per identificare sorgenti non autorizzate e problemi di autenticazione:

```bash
# I report arrivano come allegati XML compressi
# Estrarre e analizzare con strumenti dedicati:
# - dmarcian.com (SaaS)
# - parsedmarc (open source, Python)
# pip install parsedmarc
# parsedmarc -i /percorso/report_dmarc.xml.gz

# Metriche chiave da monitorare:
# - Percentuale di email che passano SPF
# - Percentuale di email che passano DKIM
# - Percentuale di email allineate (alignment)
# - Sorgenti di email non autorizzate
```

**Analisi degli header email per troubleshooting**

```bash
# Header chiave da verificare:
# Authentication-Results: indica i risultati di SPF, DKIM, DMARC
# Received-SPF: pass/fail/softfail/neutral
# DKIM-Signature: firma DKIM presente
# ARC-Authentication-Results: risultati ARC per le email inoltrate

# Esempio di analisi con strumento a linea di comando
# Estrarre l'header Authentication-Results da un file .eml
# grep -i "Authentication-Results" messaggio.eml
```

### Anti-Spam e Filtering

**Ottimizzazione dei filtri anti-spam**

La configurazione dei filtri anti-spam richiede un equilibrio costante tra protezione e usabilita. Filtri troppo aggressivi generano falsi positivi (email legittime bloccate), mentre filtri troppo permissivi lasciano passare spam e phishing.

```powershell
# Exchange Online: verificare le impostazioni anti-spam
Get-HostedContentFilterPolicy | Select-Object Name, BulkThreshold, SpamAction, HighConfidenceSpamAction

# Regolare la soglia per il bulk email (da 1 a 9, default 7)
# Set-HostedContentFilterPolicy -Identity Default -BulkThreshold 6

# Verificare gli override consentiti
Get-HostedContentFilterPolicy | Select-Object Name, AllowedSenders, AllowedSenderDomains, BlockedSenders, BlockedSenderDomains
```

**Gestione delle whitelist e blacklist**

```powershell
# Aggiungere un mittente alla whitelist
Set-HostedContentFilterPolicy -Identity Default -AllowedSenderDomains @{Add="partner-fidata.it"}

# Aggiungere un mittente alla blacklist
Set-HostedContentFilterPolicy -Identity Default -BlockedSenderDomains @{Add="spammer.com"}

# Elenco completo delle liste
Get-HostedContentFilterPolicy | Select-Object -ExpandProperty AllowedSenderDomains
Get-HostedContentFilterPolicy | Select-Object -ExpandProperty BlockedSenderDomains
```

**Protezione dal phishing**

```powershell
# Verificare le policy anti-phishing
Get-AntiPhishPolicy | Select-Object Name, Enabled, PhishThresholdLevel, EnableMailboxIntelligence, EnableSpoofIntelligence

# Verificare le protezioni Safe Attachments
Get-SafeAttachmentPolicy | Select-Object Name, Action, Enable, Redirect, RedirectAddress

# Verificare le protezioni Safe Links
Get-SafeLinksPolicy | Select-Object Name, IsEnabled, DoNotRewriteUrls, ScanUrls, EnableForInternalSenders
```

---

## Manutenzione Storage

Lo storage e la componente infrastrutturale che ospita i dati aziendali. Un guasto allo storage non rilevato tempestivamente puo portare a perdita di dati irreversibile, mentre un degrado prestazionale impatta direttamente la produttivita degli utenti e le prestazioni delle applicazioni.

### SAN/NAS Management

**Monitoraggio e provisioning dei LUN**

```bash
# Verifica dello stato dei LUN (esempio con strumenti NetApp)
# lun show -fields state,mapped,serial-hex,size
# lun show -v

# Verifica multipath I/O
# Linux
multipath -ll
multipathd show paths
multipathd show status

# Windows PowerShell
Get-MSDSMSupportedDeviceList
mpclaim -s -d

# Verifica dello stato dei dischi (Linux)
smartctl -a /dev/sda
smartctl --scan | while read device rest; do echo "=== $device ===" && smartctl -H "$device"; done
```

**Alert per Thin Provisioning**

Il thin provisioning consente di allocare piu spazio logico di quello fisicamente disponibile. E fondamentale monitorare lo spazio fisico effettivamente consumato per evitare condizioni di out-of-space che causerebbero la corruzione dei dati:

```bash
# Monitorare l'utilizzo effettivo vs allocato
# Soglie raccomandate:
# - Warning: utilizzo fisico > 70%
# - Critico: utilizzo fisico > 85%
# - Emergenza: utilizzo fisico > 95% (azione immediata richiesta)

# ZFS (esempio)
zpool list -o name,size,alloc,free,capacity,health
zfs list -o name,used,avail,refer,compressratio

# LVM (Linux)
lvs --units g -o lv_name,lv_size,data_percent,metadata_percent
vgs --units g -o vg_name,vg_size,vg_free,vg_free_count
```

**Monitoraggio delle prestazioni storage**

```bash
# Metriche chiave:
# - IOPS (Input/Output Operations Per Second): misura le operazioni al secondo
# - Latenza: tempo di risposta per singola operazione
# - Throughput: MB/s trasferiti

# Soglie raccomandate:
# | Metrica     | SSD/NVMe      | HDD (15K RPM) | HDD (7.2K RPM) |
# |-------------|---------------|---------------|-----------------|
# | IOPS        | > 100.000     | > 200         | > 100           |
# | Latenza     | < 1 ms        | < 5 ms        | < 10 ms         |
# | Throughput  | > 500 MB/s    | > 150 MB/s    | > 100 MB/s      |

# Monitoraggio con iostat (Linux)
iostat -xz 5 3

# Monitoraggio con Windows Performance Monitor
# Contatori: PhysicalDisk\Avg. Disk sec/Read, PhysicalDisk\Avg. Disk sec/Write
# PhysicalDisk\Disk Reads/sec, PhysicalDisk\Disk Writes/sec
```

**Gestione degli snapshot**

```bash
# Elenco degli snapshot (ZFS)
zfs list -t snapshot -o name,creation,used,referenced

# Rimuovere snapshot vecchi (piu di 30 giorni)
zfs list -t snapshot -o name,creation -H | while read name creation; do
    snap_date=$(date -d "$creation" +%s 2>/dev/null)
    threshold=$(date -d "30 days ago" +%s)
    if [ -n "$snap_date" ] && [ "$snap_date" -lt "$threshold" ]; then
        echo "Eliminare: $name (creato il $creation)"
        # zfs destroy "$name"  # decommentare per eseguire
    fi
done
```

**Aggiornamento firmware**

Gli aggiornamenti firmware dei controller storage e dei dischi devono essere pianificati con attenzione:

1. Verificare le release notes del produttore per bug fix critici
2. Testare l'aggiornamento in ambiente di staging se disponibile
3. Eseguire un backup completo prima dell'aggiornamento
4. Pianificare una finestra di manutenzione (alcuni aggiornamenti richiedono il riavvio del controller)
5. Verificare che il failover del controller sia funzionante prima di procedere
6. Aggiornare un controller alla volta per mantenere la disponibilita
7. Verificare lo stato di salute dell'array dopo l'aggiornamento

### File Server

**Audit dei permessi sulle condivisioni**

L'audit periodico dei permessi delle condivisioni di rete e fondamentale per la sicurezza e la conformita. I permessi tendono ad accumularsi nel tempo con concessioni incrementali che violano il principio del minimo privilegio:

```powershell
# Report dei permessi NTFS su una cartella condivisa
$path = "D:\Condivisioni\Dipartimento"
Get-Acl $path | Select-Object -ExpandProperty Access | Select-Object IdentityReference, FileSystemRights, AccessControlType, IsInherited | Format-Table -AutoSize

# Report ricorsivo dei permessi (primo livello di sottocartelle)
Get-ChildItem $path -Directory | ForEach-Object {
    $acl = Get-Acl $_.FullName
    foreach ($ace in $acl.Access) {
        [PSCustomObject]@{
            Cartella = $_.Name
            Identita = $ace.IdentityReference
            Permessi = $ace.FileSystemRights
            Tipo = $ace.AccessControlType
            Ereditato = $ace.IsInherited
        }
    }
} | Export-Csv -Path "C:\Reports\NTFS-Permissions-$(Get-Date -Format 'yyyyMMdd').csv" -NoTypeInformation

# Verifica dei permessi delle condivisioni SMB
Get-SmbShare | Where-Object {$_.Name -notlike "*$"} | ForEach-Object {
    Write-Output "=== $($_.Name) ==="
    Get-SmbShareAccess -Name $_.Name | Format-Table AccountName, AccessControlType, AccessRight
}
```

**Monitoraggio delle quote**

```powershell
# Stato delle quote FSRM
Get-FsrmQuota | Select-Object Path, Size, Usage, Template | Format-Table -AutoSize

# Quote che superano l'80% di utilizzo
Get-FsrmQuota | Where-Object {
    ($_.Usage / $_.Size) -gt 0.8
} | Select-Object Path, @{N='DimensioneGB';E={[math]::Round($_.Size/1GB,2)}}, @{N='UtilizzoGB';E={[math]::Round($_.Usage/1GB,2)}}, @{N='Percentuale';E={[math]::Round(($_.Usage/$_.Size)*100,1)}}

# Configurare notifiche per le quote
# New-FsrmQuotaThreshold -Percentage 85 | Add-FsrmAction -Type Email -MailTo "admin@azienda.it" -Subject "Quota quasi esaurita" -Body "La quota per [Quota Path] ha raggiunto [Quota Threshold]%"
```

**Verifica della replica DFS**

```powershell
# Stato della replica DFS
Get-DfsrState -ComputerName DC01 | Select-Object FileName, UpdateState, Inbound

# Report diagnostico DFS
dfsrdiag backlog /rgname:"NomeGruppoReplica" /rfname:"NomeCartellaReplicata" /sendingmember:DC01 /receivingmember:DC02

# Stato del gruppo di replica
Get-DfsReplicationGroup | ForEach-Object {
    $group = $_.GroupName
    Get-DfsReplicatedFolder -GroupName $group | ForEach-Object {
        Write-Output "Gruppo: $group - Cartella: $($_.FolderName) - Stato: $($_.State)"
    }
}

# Report sullo stato di salute della replica
Write-DfsrHealthReport -GroupName "NomeGruppoReplica" -ReferenceComputerName "DC01" -Path "C:\Reports\DFS"
```

**Verifica ABE (Access Based Enumeration)**

ABE nasconde agli utenti le cartelle e i file per i quali non hanno permessi di lettura, migliorando la sicurezza e riducendo la confusione:

```powershell
# Verificare lo stato ABE su tutte le condivisioni
Get-SmbShare | Where-Object {$_.Name -notlike "*$"} | Select-Object Name, FolderEnumerationMode

# Abilitare ABE su una condivisione
# Set-SmbShare -Name "NomeCondivisione" -FolderEnumerationMode AccessBased
```

### Storage Capacity Planning

**Analisi delle tendenze di crescita**

La pianificazione della capacita storage richiede dati storici sull'utilizzo per prevedere quando sara necessario espandere lo storage:

```powershell
# Script per raccolta dati giornaliera sull'utilizzo storage
$drives = Get-WmiObject Win32_LogicalDisk -Filter "DriveType=3"
$data = $drives | ForEach-Object {
    [PSCustomObject]@{
        Data = Get-Date -Format "yyyy-MM-dd"
        Drive = $_.DeviceID
        DimensioneGB = [math]::Round($_.Size/1GB, 2)
        LiberoGB = [math]::Round($_.FreeSpace/1GB, 2)
        UtilizzoPercent = [math]::Round((1 - $_.FreeSpace/$_.Size) * 100, 1)
    }
}
$data | Export-Csv -Path "C:\Reports\Storage-Capacity-$(Get-Date -Format 'yyyyMMdd').csv" -NoTypeInformation -Append
```

Raccogliendo questi dati quotidianamente per almeno 6 mesi, e possibile calcolare il tasso di crescita medio e stimare quando lo storage raggiungera la capacita massima. Ad esempio, se lo storage cresce di 50 GB al mese e rimangono 500 GB liberi, lo storage si esaurira in circa 10 mesi.

**Ottimizzazione dello storage a livelli (Tiered Storage)**

Lo storage tiering prevede la collocazione dei dati su diversi livelli di storage in base alla frequenza di accesso:
- **Tier 1 (SSD/NVMe):** dati ad accesso frequente, database attivi, macchine virtuali in produzione
- **Tier 2 (SAS/HDD veloci):** dati ad accesso moderato, file server, archivi recenti
- **Tier 3 (SATA/Object Storage):** dati ad accesso raro, backup, archivi storici

**Efficacia della deduplicazione**

```powershell
# Stato della deduplicazione (Windows Server)
Get-DedupStatus | Select-Object Volume, OptimizedFilesCount, InPolicyFilesCount, OptimizedFilesSavingsRate, SavingsRate

# Spazio risparmiato dalla deduplicazione
Get-DedupVolume | Select-Object Volume, SavingsRate, UnoptimizedSize, UsedSpace, FreeSpace

# Avviare un job di deduplicazione manuale
# Start-DedupJob -Volume "D:" -Type Optimization
```

---

## Manutenzione Database

I database contengono i dati applicativi critici dell'azienda. Una manutenzione regolare previene la corruzione dei dati, il degrado prestazionale e i tempi di ripristino eccessivi in caso di guasto.

### SQL Server

**Verifica dell'integrita del database (DBCC CHECKDB)**

DBCC CHECKDB e il comando piu importante per la manutenzione di SQL Server. Verifica l'integrita fisica e logica di ogni oggetto nel database:

```sql
-- Verifica completa dell'integrita (eseguire settimanalmente)
DBCC CHECKDB ('NomeDatabase') WITH NO_INFOMSGS, ALL_ERRORMSGS;

-- Verifica solo delle pagine di allocazione (piu veloce, eseguire quotidianamente)
DBCC CHECKALLOC ('NomeDatabase') WITH NO_INFOMSGS;

-- Verifica dell'integrita del catalogo
DBCC CHECKCATALOG ('NomeDatabase') WITH NO_INFOMSGS;

-- Stato dell'ultima esecuzione di DBCC CHECKDB per tutti i database
SELECT
    name AS DatabaseName,
    DATABASEPROPERTYEX(name, 'LastGoodCheckDbTime') AS LastGoodCheckDb
FROM sys.databases
WHERE state_desc = 'ONLINE';
```

**Manutenzione degli indici**

Gli indici si frammentano nel tempo a causa delle operazioni di inserimento, aggiornamento e cancellazione. La frammentazione eccessiva degrada le prestazioni delle query:

```sql
-- Identificare la frammentazione degli indici
SELECT
    OBJECT_NAME(ips.object_id) AS TableName,
    i.name AS IndexName,
    ips.index_type_desc,
    ips.avg_fragmentation_in_percent,
    ips.page_count
FROM sys.dm_db_index_physical_stats(DB_ID(), NULL, NULL, NULL, 'LIMITED') ips
INNER JOIN sys.indexes i ON ips.object_id = i.object_id AND ips.index_id = i.index_id
WHERE ips.avg_fragmentation_in_percent > 10
    AND ips.page_count > 1000
ORDER BY ips.avg_fragmentation_in_percent DESC;

-- Strategia di manutenzione:
-- Frammentazione 10-30%: REORGANIZE (operazione online)
-- Frammentazione > 30%: REBUILD (operazione offline o online con Enterprise Edition)

-- Reorganize di un indice specifico
ALTER INDEX IX_NomeIndice ON dbo.NomeTabella REORGANIZE;

-- Rebuild di un indice specifico
ALTER INDEX IX_NomeIndice ON dbo.NomeTabella REBUILD WITH (ONLINE = ON);

-- Rebuild di tutti gli indici di una tabella
ALTER INDEX ALL ON dbo.NomeTabella REBUILD WITH (ONLINE = ON);
```

**Aggiornamento delle statistiche**

```sql
-- Aggiornare le statistiche di tutti i database
EXEC sp_updatestats;

-- Aggiornare con full scan (piu preciso ma piu lento)
UPDATE STATISTICS dbo.NomeTabella WITH FULLSCAN;

-- Identificare statistiche obsolete
SELECT
    OBJECT_NAME(s.object_id) AS TableName,
    s.name AS StatName,
    sp.last_updated,
    sp.rows,
    sp.modification_counter
FROM sys.stats s
CROSS APPLY sys.dm_db_stats_properties(s.object_id, s.stats_id) sp
WHERE sp.modification_counter > 0
ORDER BY sp.modification_counter DESC;
```

**Gestione del transaction log**

```sql
-- Dimensione e utilizzo del transaction log
SELECT
    DB_NAME(database_id) AS DatabaseName,
    type_desc,
    name,
    size * 8 / 1024 AS SizeMB,
    FILEPROPERTY(name, 'SpaceUsed') * 8 / 1024 AS UsedMB
FROM sys.master_files
WHERE type_desc = 'LOG'
ORDER BY size DESC;

-- Verificare il motivo per cui il log non si riduce
SELECT
    name,
    log_reuse_wait_desc
FROM sys.databases;

-- Se log_reuse_wait_desc = 'LOG_BACKUP', eseguire un backup del log
BACKUP LOG NomeDatabase TO DISK = 'C:\Backup\NomeDatabase_Log.trn';
```

**Verifica dei backup**

```sql
-- Verifica dell'integrita di un file di backup (senza ripristinare)
RESTORE VERIFYONLY FROM DISK = 'C:\Backup\NomeDatabase_Full.bak' WITH CHECKSUM;

-- Ultimo backup per ogni database
SELECT
    d.name AS DatabaseName,
    MAX(CASE WHEN b.type = 'D' THEN b.backup_finish_date END) AS LastFullBackup,
    MAX(CASE WHEN b.type = 'I' THEN b.backup_finish_date END) AS LastDiffBackup,
    MAX(CASE WHEN b.type = 'L' THEN b.backup_finish_date END) AS LastLogBackup
FROM sys.databases d
LEFT JOIN msdb.dbo.backupset b ON d.name = b.database_name
WHERE d.state_desc = 'ONLINE'
GROUP BY d.name
ORDER BY d.name;
```

**Monitoraggio di TempDB**

```sql
-- Utilizzo dello spazio in TempDB
SELECT
    SUM(unallocated_extent_page_count) * 8 / 1024 AS FreeSpaceMB,
    SUM(internal_object_reserved_page_count) * 8 / 1024 AS InternalObjectsMB,
    SUM(user_object_reserved_page_count) * 8 / 1024 AS UserObjectsMB,
    SUM(version_store_reserved_page_count) * 8 / 1024 AS VersionStoreMB
FROM sys.dm_db_file_space_usage;

-- Sessioni che consumano piu spazio in TempDB
SELECT
    session_id,
    internal_objects_alloc_page_count * 8 / 1024 AS InternalAllocMB,
    user_objects_alloc_page_count * 8 / 1024 AS UserAllocMB
FROM sys.dm_db_session_space_usage
WHERE internal_objects_alloc_page_count + user_objects_alloc_page_count > 0
ORDER BY (internal_objects_alloc_page_count + user_objects_alloc_page_count) DESC;
```

**Analisi delle Wait Statistics**

```sql
-- Top 10 wait types (indicano i colli di bottiglia)
SELECT TOP 10
    wait_type,
    waiting_tasks_count,
    wait_time_ms / 1000.0 AS wait_time_sec,
    max_wait_time_ms / 1000.0 AS max_wait_time_sec,
    signal_wait_time_ms / 1000.0 AS signal_wait_time_sec
FROM sys.dm_os_wait_stats
WHERE wait_type NOT IN (
    'CLR_SEMAPHORE','LAZYWRITER_SLEEP','RESOURCE_QUEUE',
    'SLEEP_TASK','SLEEP_SYSTEMTASK','SQLTRACE_BUFFER_FLUSH',
    'WAITFOR','LOGMGR_QUEUE','CHECKPOINT_QUEUE',
    'REQUEST_FOR_DEADLOCK_SEARCH','XE_TIMER_EVENT',
    'BROKER_TO_FLUSH','BROKER_TASK_STOP','CLR_MANUAL_EVENT',
    'DISPATCHER_QUEUE_SEMAPHORE','FT_IFTS_SCHEDULER_IDLE_WAIT',
    'XE_DISPATCHER_WAIT','HADR_FILESTREAM_IOMGR_IOCOMPLETION'
)
ORDER BY wait_time_ms DESC;
```

**Audit dei job dell'Agent**

```sql
-- Stato degli ultimi job eseguiti
SELECT
    j.name AS JobName,
    h.run_date,
    h.run_time,
    CASE h.run_status
        WHEN 0 THEN 'Fallito'
        WHEN 1 THEN 'Successo'
        WHEN 2 THEN 'Retry'
        WHEN 3 THEN 'Annullato'
    END AS Stato,
    h.run_duration,
    h.message
FROM msdb.dbo.sysjobs j
INNER JOIN msdb.dbo.sysjobhistory h ON j.job_id = h.job_id
WHERE h.step_id = 0
ORDER BY h.run_date DESC, h.run_time DESC;

-- Job falliti nelle ultime 24 ore
SELECT
    j.name AS JobName,
    h.run_date,
    h.message
FROM msdb.dbo.sysjobs j
INNER JOIN msdb.dbo.sysjobhistory h ON j.job_id = h.job_id
WHERE h.step_id = 0
    AND h.run_status = 0
    AND CONVERT(datetime, CAST(h.run_date AS char(8)), 112) > DATEADD(day, -1, GETDATE())
ORDER BY h.run_date DESC;
```

### PostgreSQL

**Pianificazione di VACUUM e ANALYZE**

PostgreSQL utilizza il meccanismo MVCC (Multi-Version Concurrency Control) che lascia tuple morte nelle tabelle dopo le operazioni di UPDATE e DELETE. Il VACUUM recupera questo spazio:

```sql
-- Verificare le tabelle che necessitano di VACUUM
SELECT
    schemaname || '.' || relname AS table_name,
    n_live_tup,
    n_dead_tup,
    ROUND(n_dead_tup::numeric / NULLIF(n_live_tup + n_dead_tup, 0) * 100, 2) AS dead_percent,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables
WHERE n_dead_tup > 1000
ORDER BY n_dead_tup DESC;

-- VACUUM manuale con ANALYZE
VACUUM (VERBOSE, ANALYZE) nome_tabella;

-- VACUUM FULL (recupera spazio su disco, ma blocca la tabella)
-- Utilizzare solo durante le finestre di manutenzione
VACUUM FULL VERBOSE nome_tabella;

-- Configurazione dell'autovacuum (postgresql.conf)
-- autovacuum = on
-- autovacuum_vacuum_threshold = 50
-- autovacuum_vacuum_scale_factor = 0.1  (default 0.2)
-- autovacuum_analyze_threshold = 50
-- autovacuum_analyze_scale_factor = 0.05 (default 0.1)
-- autovacuum_max_workers = 4
```

**Monitoraggio del bloat delle tabelle**

```sql
-- Stima del bloat delle tabelle
SELECT
    schemaname || '.' || tablename AS table_name,
    pg_size_pretty(pg_total_relation_size(schemaname || '.' || tablename)) AS total_size,
    pg_size_pretty(pg_relation_size(schemaname || '.' || tablename)) AS table_size,
    pg_size_pretty(pg_indexes_size(schemaname || '.' || tablename::regclass)) AS index_size
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_total_relation_size(schemaname || '.' || tablename) DESC
LIMIT 20;

-- Utilizzare l'estensione pgstattuple per un'analisi precisa
-- CREATE EXTENSION IF NOT EXISTS pgstattuple;
-- SELECT * FROM pgstattuple('nome_tabella');
```

**Gestione del connection pool**

```sql
-- Connessioni attive per database
SELECT
    datname,
    count(*) AS connections,
    count(*) FILTER (WHERE state = 'active') AS active,
    count(*) FILTER (WHERE state = 'idle') AS idle,
    count(*) FILTER (WHERE state = 'idle in transaction') AS idle_in_transaction
FROM pg_stat_activity
GROUP BY datname
ORDER BY connections DESC;

-- Connessioni idle in transaction da piu di 5 minuti (potenziale problema)
SELECT
    pid, usename, datname, state, query,
    now() - state_change AS idle_duration
FROM pg_stat_activity
WHERE state = 'idle in transaction'
    AND now() - state_change > interval '5 minutes';

-- Terminare una connessione problematica
-- SELECT pg_terminate_backend(pid);
```

**Gestione WAL (Write-Ahead Log)**

```sql
-- Dimensione dei WAL
SELECT
    pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), '0/0')) AS wal_total_size;

-- Verifica della configurazione WAL
SHOW wal_level;
SHOW max_wal_size;
SHOW min_wal_size;
SHOW archive_mode;
SHOW archive_command;

-- Stato dell'archiviazione WAL
SELECT * FROM pg_stat_archiver;
```

**Analisi con pg_stat_statements**

```sql
-- Abilitare l'estensione (postgresql.conf: shared_preload_libraries = 'pg_stat_statements')
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Top 10 query per tempo totale di esecuzione
SELECT
    LEFT(query, 100) AS query_truncated,
    calls,
    ROUND(total_exec_time::numeric / 1000, 2) AS total_time_sec,
    ROUND(mean_exec_time::numeric, 2) AS mean_time_ms,
    rows
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 10;

-- Query con il piu alto rapporto tempo/chiamata
SELECT
    LEFT(query, 100) AS query_truncated,
    calls,
    ROUND(mean_exec_time::numeric, 2) AS mean_time_ms
FROM pg_stat_statements
WHERE calls > 100
ORDER BY mean_exec_time DESC
LIMIT 10;
```

**Monitoraggio del ritardo di replica**

```sql
-- Sul server primario: verificare lo stato della replica
SELECT
    client_addr,
    state,
    sent_lsn,
    write_lsn,
    flush_lsn,
    replay_lsn,
    pg_wal_lsn_diff(sent_lsn, replay_lsn) AS replication_lag_bytes,
    pg_size_pretty(pg_wal_lsn_diff(sent_lsn, replay_lsn)) AS replication_lag
FROM pg_stat_replication;

-- Sul server replica: verificare il ritardo
SELECT
    now() - pg_last_xact_replay_timestamp() AS replication_delay;
```

### MySQL/MariaDB

**Ottimizzazione delle tabelle**

```sql
-- Identificare tabelle frammentate
SELECT
    TABLE_SCHEMA,
    TABLE_NAME,
    DATA_LENGTH,
    DATA_FREE,
    ROUND(DATA_FREE / DATA_LENGTH * 100, 2) AS fragmentation_percent
FROM information_schema.TABLES
WHERE DATA_FREE > 0
    AND TABLE_SCHEMA NOT IN ('mysql', 'information_schema', 'performance_schema', 'sys')
ORDER BY DATA_FREE DESC;

-- Ottimizzare una tabella (recupera spazio e ricostruisce gli indici)
OPTIMIZE TABLE nome_schema.nome_tabella;

-- Per tabelle InnoDB, OPTIMIZE equivale a ALTER TABLE ... ENGINE=InnoDB
-- che ricostruisce la tabella e gli indici
```

**Analisi dello slow query log**

```sql
-- Verificare lo stato dello slow query log
SHOW VARIABLES LIKE 'slow_query_log%';
SHOW VARIABLES LIKE 'long_query_time';

-- Abilitare lo slow query log (se non attivo)
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 1;  -- soglia in secondi

-- Utilizzare mysqldumpslow per analizzare il log
-- mysqldumpslow -s t -t 10 /var/log/mysql/mysql-slow.log
-- -s t: ordina per tempo totale
-- -t 10: mostra le prime 10 query

-- Oppure utilizzare pt-query-digest di Percona Toolkit
-- pt-query-digest /var/log/mysql/mysql-slow.log --limit 20
```

**Dimensionamento del Buffer Pool**

```sql
-- Stato del buffer pool InnoDB
SHOW STATUS LIKE 'Innodb_buffer_pool%';

-- Hit ratio del buffer pool (dovrebbe essere > 99%)
SELECT
    ROUND((1 - (
        (SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Innodb_buffer_pool_reads') /
        (SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Innodb_buffer_pool_read_requests')
    )) * 100, 2) AS buffer_pool_hit_ratio;

-- Dimensione raccomandata del buffer pool
-- Regola: 70-80% della RAM disponibile su un server dedicato
SHOW VARIABLES LIKE 'innodb_buffer_pool_size';
```

**Gestione dei binary log**

```sql
-- Elenco dei binary log
SHOW BINARY LOGS;

-- Spazio occupato dai binary log
SELECT
    SUM(FILE_SIZE) / 1024 / 1024 AS total_binlog_size_mb
FROM performance_schema.file_summary_by_instance
WHERE FILE_NAME LIKE '%binlog%';

-- Configurazione della retention
SHOW VARIABLES LIKE 'binlog_expire_logs_seconds';  -- MySQL 8.0+
SHOW VARIABLES LIKE 'expire_logs_days';             -- versioni precedenti

-- Eliminare binary log vecchi
PURGE BINARY LOGS BEFORE DATE_SUB(NOW(), INTERVAL 7 DAY);
```

**Verifica dello stato della replica**

```sql
-- Sul server replica
SHOW REPLICA STATUS\G
-- Verificare:
-- Replica_IO_Running: Yes
-- Replica_SQL_Running: Yes
-- Seconds_Behind_Source: < soglia accettabile
-- Last_Error: (dovrebbe essere vuoto)

-- Sul server sorgente
SHOW REPLICAS;
```

### Database Backup e Recovery

**Strategia di backup per tipo di database**

| Database | Full Backup | Differential/Incremental | Log Backup |
|---|---|---|---|
| SQL Server | Settimanale (domenica) | Giornaliero | Ogni 15-30 min |
| PostgreSQL | Giornaliero (pg_dump o pg_basebackup) | WAL archiving continuo | N/A (tramite WAL) |
| MySQL/MariaDB | Giornaliero (mysqldump o xtrabackup) | Incremental con xtrabackup | Binary log continuo |

**Test di ripristino point-in-time**

Il test regolare del ripristino e la verifica piu importante della strategia di backup. Un backup che non puo essere ripristinato e inutile:

```sql
-- SQL Server: verifica del backup senza ripristino
RESTORE VERIFYONLY FROM DISK = 'C:\Backup\NomeDatabase_Full.bak' WITH CHECKSUM;

-- SQL Server: ripristino point-in-time di test
RESTORE DATABASE NomeDatabase_Test
FROM DISK = 'C:\Backup\NomeDatabase_Full.bak'
WITH MOVE 'NomeDatabase_Data' TO 'C:\Test\NomeDatabase_Test.mdf',
     MOVE 'NomeDatabase_Log' TO 'C:\Test\NomeDatabase_Test.ldf',
     NORECOVERY;

RESTORE LOG NomeDatabase_Test
FROM DISK = 'C:\Backup\NomeDatabase_Log.trn'
WITH STOPAT = '2024-06-15T14:30:00', RECOVERY;
```

```bash
# PostgreSQL: ripristino di test con pg_restore
pg_restore -d database_test -v /backup/database_dump.custom

# PostgreSQL: ripristino point-in-time con pg_basebackup + WAL
# 1. Ripristinare il base backup
# 2. Configurare recovery.conf (o postgresql.auto.conf in PG >= 12)
#    restore_command = 'cp /archive/%f %p'
#    recovery_target_time = '2024-06-15 14:30:00'
#    recovery_target_action = 'promote'

# MySQL: ripristino di test
# mysql -u root -p database_test < /backup/database_dump.sql
# mysqlbinlog --stop-datetime="2024-06-15 14:30:00" /var/log/mysql/binlog.000123 | mysql -u root -p database_test
```

**Monitoraggio della dimensione dei backup**

Si raccomanda di tracciare la dimensione dei backup nel tempo per rilevare anomalie (un backup improvvisamente molto piu grande o molto piu piccolo puo indicare un problema):

```powershell
# SQL Server: dimensione degli ultimi backup
SELECT
    database_name,
    type AS backup_type,
    backup_finish_date,
    ROUND(backup_size / 1024 / 1024, 2) AS size_mb,
    ROUND(compressed_backup_size / 1024 / 1024, 2) AS compressed_size_mb,
    ROUND((1 - compressed_backup_size / backup_size) * 100, 1) AS compression_ratio
FROM msdb.dbo.backupset
WHERE backup_finish_date > DATEADD(day, -30, GETDATE())
ORDER BY backup_finish_date DESC;
```

---

## Manutenzione Web Server

I web server ospitano le applicazioni aziendali e i servizi esposti su Internet. La loro manutenzione e fondamentale per garantire disponibilita, prestazioni e sicurezza.

### IIS

**Pianificazione del riciclo degli Application Pool**

Il riciclo periodico degli application pool previene memory leak e degrado prestazionale delle applicazioni .NET:

```powershell
# Stato degli application pool
Get-IISAppPool | Select-Object Name, State, ManagedRuntimeVersion, @{N='WorkerProcesses';E={$_.WorkerProcesses.Count}}

# Configurazione del riciclo
Get-IISAppPool | ForEach-Object {
    $pool = $_
    $recycling = $pool.Recycling.PeriodicRestart
    [PSCustomObject]@{
        Nome = $pool.Name
        ScheduleRiciclo = ($recycling.Schedule | ForEach-Object { $_.Time.ToString() }) -join ", "
        IntervalloMinuti = $recycling.Time.TotalMinutes
        LimiteMemoriaKB = $recycling.Memory
        LimiteRichiestePrivateKB = $recycling.PrivateMemory
    }
} | Format-Table -AutoSize

# Configurare il riciclo a un orario specifico (es. alle 3:00 di notte)
# Set-ItemProperty "IIS:\AppPools\NomePool" -Name recycling.periodicRestart.schedule -Value @{value="03:00:00"}

# Riciclo manuale di un application pool
Restart-WebAppPool -Name "NomePool"
```

**Monitoraggio dei worker process**

```powershell
# Worker process attivi e utilizzo risorse
Get-IISAppPool | ForEach-Object {
    $pool = $_
    $pool.WorkerProcesses | ForEach-Object {
        $process = Get-Process -Id $_.ProcessId -ErrorAction SilentlyContinue
        [PSCustomObject]@{
            AppPool = $pool.Name
            PID = $_.ProcessId
            CPU_Sec = if ($process) { [math]::Round($process.CPU, 2) } else { "N/A" }
            RAM_MB = if ($process) { [math]::Round($process.WorkingSet64/1MB, 2) } else { "N/A" }
            Threads = if ($process) { $process.Threads.Count } else { "N/A" }
        }
    }
} | Format-Table -AutoSize
```

**Gestione dei certificati SSL**

```powershell
# Certificati SSL associati ai binding IIS
Get-ChildItem IIS:SSLBindings | ForEach-Object {
    $cert = Get-ChildItem Cert:\LocalMachine\My | Where-Object {$_.Thumbprint -eq $_.Thumbprint}
    [PSCustomObject]@{
        Binding = "$($_.IPAddress):$($_.Port)"
        Thumbprint = $_.Thumbprint
        Host = $_.Host
    }
}

# Certificati in scadenza nei prossimi 30 giorni
Get-ChildItem Cert:\LocalMachine\My | Where-Object {
    $_.NotAfter -lt (Get-Date).AddDays(30) -and $_.NotAfter -gt (Get-Date)
} | Select-Object Subject, Thumbprint, NotAfter | Format-Table -AutoSize
```

**Rotazione dei log IIS**

```powershell
# Verificare la configurazione del logging
Get-WebConfigurationProperty -Filter "system.applicationHost/sites/siteDefaults/logFile" -Name * | Select-Object directory, period, truncateSize, logExtFileFlags

# Pulizia dei log IIS vecchi (piu di 90 giorni)
$logPath = "C:\inetpub\logs\LogFiles"
Get-ChildItem -Path $logPath -Recurse -Filter "*.log" | Where-Object {
    $_.LastWriteTime -lt (Get-Date).AddDays(-90)
} | Remove-Item -Force -WhatIf
# Rimuovere -WhatIf dopo la verifica
```

### Nginx/Apache

**Validazione della configurazione**

```bash
# Nginx: verifica della configurazione
nginx -t
nginx -T  # mostra anche la configurazione completa

# Apache: verifica della configurazione
apachectl configtest
apachectl -S  # mostra i virtual host configurati
httpd -t -D DUMP_VHOSTS  # su alcune distribuzioni
```

**Rotazione dei log**

```bash
# Configurazione logrotate per Nginx (/etc/logrotate.d/nginx)
# /var/log/nginx/*.log {
#     daily
#     missingok
#     rotate 52
#     compress
#     delaycompress
#     notifempty
#     create 0640 www-data adm
#     sharedscripts
#     postrotate
#         [ -f /var/run/nginx.pid ] && kill -USR1 $(cat /var/run/nginx.pid)
#     endscript
# }

# Verificare lo stato di logrotate
logrotate -d /etc/logrotate.d/nginx  # dry run per debug
```

**Rinnovo automatico dei certificati SSL con certbot**

```bash
# Verifica dello stato dei certificati
certbot certificates

# Rinnovo di tutti i certificati in scadenza
certbot renew --dry-run  # test senza applicare
certbot renew

# Rinnovo forzato di un certificato specifico
certbot renew --cert-name azienda.it --force-renewal

# Configurare il rinnovo automatico via crontab
# 0 3 * * * certbot renew --quiet --post-hook "systemctl reload nginx"

# Verificare il grado SSL/TLS del sito
# Utilizzare ssllabs.com/ssltest o testssl.sh
# testssl.sh https://www.azienda.it
```

**Audit dei moduli**

```bash
# Nginx: elenco dei moduli compilati
nginx -V 2>&1 | tr -- - '\n' | grep module

# Apache: elenco dei moduli caricati
apachectl -M
# oppure
httpd -M
```

**Ottimizzazione delle prestazioni Nginx**

```bash
# Parametri chiave da verificare e ottimizzare:
# worker_processes: impostare al numero di core CPU
# worker_connections: 1024-4096 per worker
# keepalive_timeout: 65-120 secondi
# gzip: abilitare per contenuti testuali
# client_max_body_size: adattare alle esigenze applicative
# proxy_buffer_size e proxy_buffers: ottimizzare per il backend

# Verificare i parametri correnti
nginx -T | grep -E "worker_processes|worker_connections|keepalive_timeout|gzip|client_max_body"
```

### Web Application Health

**Monitoraggio degli endpoint di salute**

Ogni applicazione web dovrebbe esporre un endpoint `/health` o `/status` che restituisce lo stato di salute dell'applicazione e delle sue dipendenze:

```bash
# Verifica manuale dell'endpoint di salute
curl -s -o /dev/null -w "%{http_code} %{time_total}s" https://app.azienda.it/health

# Script di monitoraggio periodico
#!/bin/bash
ENDPOINTS=(
    "https://app1.azienda.it/health"
    "https://app2.azienda.it/health"
    "https://api.azienda.it/health"
)

for url in "${ENDPOINTS[@]}"; do
    response=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 --max-time 10 "$url")
    if [ "$response" != "200" ]; then
        echo "CRITICO: $url ha risposto con codice $response"
        # Inviare allarme
    fi
done
```

**Monitoraggio dei tempi di risposta**

```bash
# Misura dettagliata dei tempi con curl
curl -w "\nDNS: %{time_namelookup}s\nConnect: %{time_connect}s\nTLS: %{time_appconnect}s\nTTFB: %{time_starttransfer}s\nTotal: %{time_total}s\n" -o /dev/null -s https://app.azienda.it/

# Soglie raccomandate:
# DNS resolution: < 50 ms
# TCP connect: < 100 ms
# TLS handshake: < 200 ms
# Time To First Byte (TTFB): < 500 ms
# Total: < 2 secondi
```

**Monitoraggio del tasso di errore**

Analizzare i log del web server per individuare tassi di errore anomali:

```bash
# Nginx: conteggio errori 5xx dell'ultima ora
awk -v date="$(date -d '1 hour ago' '+%d/%b/%Y:%H')" '$4 ~ date && $9 ~ /^5/ {count++} END {print "Errori 5xx:", count+0}' /var/log/nginx/access.log

# Distribuzione dei codici di risposta dell'ultimo giorno
awk '{print $9}' /var/log/nginx/access.log | sort | uniq -c | sort -rn | head 10
```

**Verifica del grado SSL/TLS**

```bash
# Utilizzare testssl.sh per una verifica completa
# testssl.sh --severity HIGH https://www.azienda.it

# Verifica rapida del certificato
openssl s_client -connect www.azienda.it:443 -servername www.azienda.it < /dev/null 2>/dev/null | openssl x509 -noout -dates -subject -issuer

# Verifica dei protocolli supportati
nmap --script ssl-enum-ciphers -p 443 www.azienda.it
```

---

## Manutenzione Active Directory e LDAP

Active Directory (AD) e il servizio di directory piu diffuso nelle infrastrutture aziendali Windows. Centralizza l'autenticazione, l'autorizzazione e la gestione delle risorse di rete. Un guasto o una compromissione di Active Directory paralizza l'intera organizzazione: gli utenti non possono autenticarsi, le Group Policy non vengono applicate, le applicazioni integrate (Exchange, SharePoint, SQL Server) cessano di funzionare. La manutenzione proattiva di AD e quindi una priorita assoluta per qualsiasi team IT.

### Active Directory Domain Services

**Verifica dello stato di salute dei Domain Controller**

La prima attivita di manutenzione AD consiste nel verificare lo stato di replica e la salute generale dei Domain Controller (DC). Un errore di replica non rilevato puo causare incongruenze progressive tra i DC, con conseguenze che vanno dalla mancata applicazione delle policy alla perdita di modifiche alle password.

```powershell
# Riepilogo della replica AD — mostra eventuali errori tra tutti i DC
repadmin /replsummary

# Stato dettagliato della replica per ogni partizione
repadmin /showrepl

# Verifica della replica tra due DC specifici
repadmin /replicate DC02 DC01 "DC=azienda,DC=local"

# Forzare la replica di tutte le partizioni su tutti i DC
repadmin /syncall /AdeP

# Identificare oggetti in conflitto (lingering objects)
repadmin /removelingeringobjects DC02 DC01 "DC=azienda,DC=local" /advisory_mode

# Verifica della topologia di replica con KCC
repadmin /kcc

# Report completo sullo stato di salute AD
dcdiag /v /c /d /e /s:DC01

# Test specifici di dcdiag
dcdiag /test:dns /v              # test DNS integrato
dcdiag /test:replications /v     # test replica
dcdiag /test:fsmocheck /v        # verifica dei ruoli FSMO
dcdiag /test:topology /v         # verifica topologia di replica
dcdiag /test:advertising /v      # verifica annunci del DC
```

**Monitoraggio dei ruoli FSMO**

I cinque ruoli FSMO (Flexible Single Master Operations) sono critici per il funzionamento di Active Directory. Ogni ruolo deve risiedere su un DC accessibile e performante:

```powershell
# Visualizzare il titolare di ogni ruolo FSMO
netdom query fsmo

# Oppure tramite PowerShell
Get-ADDomain | Select-Object InfrastructureMaster, RIDMaster, PDCEmulator
Get-ADForest | Select-Object DomainNamingMaster, SchemaMaster

# Verifica che il PDC Emulator sia raggiungibile (critico per l'autenticazione)
Test-Connection (Get-ADDomain).PDCEmulator -Count 4

# Verifica del pool RID rimanente (se si esaurisce, non si possono creare nuovi oggetti)
dcdiag /test:ridmanager /v
```

I ruoli FSMO e le loro funzioni:

| Ruolo FSMO | Ambito | Funzione critica |
|---|---|---|
| Schema Master | Foresta | Modifica dello schema AD |
| Domain Naming Master | Foresta | Aggiunta/rimozione domini nella foresta |
| PDC Emulator | Dominio | Sincronizzazione orario, cambio password prioritario, blocco account |
| RID Master | Dominio | Distribuzione pool di RID ai DC per la creazione di nuovi oggetti |
| Infrastructure Master | Dominio | Aggiornamento riferimenti cross-domain (SID, DN) |

**Manutenzione del database AD (NTDS.dit)**

Il database di Active Directory (NTDS.dit) puo frammentarsi nel tempo, aumentando di dimensione e rallentando le operazioni di ricerca:

```powershell
# Verificare la dimensione del database AD
Get-ItemProperty "C:\Windows\NTDS\ntds.dit" | Select-Object Name, @{N='DimensioneMB';E={[math]::Round($_.Length/1MB,2)}}

# Verificare lo spazio libero nel database (spazio recuperabile con defrag offline)
# Richiede l'avvio in modalita DSRM (Directory Services Restore Mode)
# ntdsutil
#   activate instance ntds
#   files
#   info
#   compact to C:\Temp\NTDS_Compact

# Verifica dell'integrita del database (da modalita DSRM)
# esentutl /g "C:\Windows\NTDS\ntds.dit" /!10240 /8 /o

# Backup dello stato di sistema (include AD, SYSVOL, registry)
wbadmin start systemstatebackup -backuptarget:E:

# Verifica dell'ultimo backup dello stato di sistema
wbadmin get versions -backupTarget:E: | Select-String "system state"
```

**Audit degli account e pulizia oggetti obsoleti**

Active Directory accumula nel tempo account utente disabilitati, computer inattivi e gruppi vuoti. Questa entropia aumenta la superficie di attacco e rende piu difficile l'amministrazione:

```powershell
# Account utente inattivi da piu di 90 giorni
$soglia = (Get-Date).AddDays(-90)
Get-ADUser -Filter {LastLogonDate -lt $soglia -and Enabled -eq $true} -Properties LastLogonDate |
    Select-Object Name, SamAccountName, LastLogonDate, Enabled |
    Sort-Object LastLogonDate |
    Export-Csv -Path "C:\Reports\AD-InactiveUsers-$(Get-Date -Format 'yyyyMMdd').csv" -NoTypeInformation

# Computer inattivi da piu di 90 giorni
Get-ADComputer -Filter {LastLogonDate -lt $soglia} -Properties LastLogonDate |
    Select-Object Name, LastLogonDate, OperatingSystem |
    Sort-Object LastLogonDate |
    Export-Csv -Path "C:\Reports\AD-InactiveComputers-$(Get-Date -Format 'yyyyMMdd').csv" -NoTypeInformation

# Gruppi vuoti (senza membri)
Get-ADGroup -Filter * -Properties Members | Where-Object { $_.Members.Count -eq 0 } |
    Select-Object Name, GroupScope, GroupCategory |
    Export-Csv -Path "C:\Reports\AD-EmptyGroups-$(Get-Date -Format 'yyyyMMdd').csv" -NoTypeInformation

# Account con password che non scade mai (rischio di sicurezza)
Get-ADUser -Filter {PasswordNeverExpires -eq $true -and Enabled -eq $true} |
    Select-Object Name, SamAccountName |
    Export-Csv -Path "C:\Reports\AD-PasswordNeverExpires-$(Get-Date -Format 'yyyyMMdd').csv" -NoTypeInformation

# Account con delega non vincolata (Kerberos unconstrained delegation - rischio elevato)
Get-ADUser -Filter {TrustedForDelegation -eq $true} -Properties TrustedForDelegation |
    Select-Object Name, SamAccountName
Get-ADComputer -Filter {TrustedForDelegation -eq $true} -Properties TrustedForDelegation |
    Select-Object Name, DNSHostName
```

**Monitoraggio della replica SYSVOL**

SYSVOL contiene le Group Policy e gli script di logon. Se la replica SYSVOL si interrompe, i client possono ricevere policy obsolete o incoerenti:

```powershell
# Stato della replica SYSVOL (DFSR)
dfsrdiag pollad

# Verifica della coerenza SYSVOL tra i DC
Get-ChildItem "\\DC01\SYSVOL\azienda.local\Policies" | Measure-Object | Select-Object Count
Get-ChildItem "\\DC02\SYSVOL\azienda.local\Policies" | Measure-Object | Select-Object Count
# I conteggi devono corrispondere

# Report diagnostico DFSR per SYSVOL
dfsrdiag backlog /rgname:"Domain System Volume" /rfname:"SYSVOL Share" /sendingmember:DC01 /receivingmember:DC02
# Un backlog di 0 indica che la replica e aggiornata

# Evento 4602 nel log DFS Replication indica il completamento della replica iniziale
Get-WinEvent -FilterHashtable @{LogName='DFS Replication'; Id=4602} -MaxEvents 5
```

### Manutenzione LDAP

LDAP (Lightweight Directory Access Protocol) e il protocollo attraverso cui applicazioni e servizi interrogano Active Directory. Con Windows Server 2025, LDAP Signing e Channel Binding sono abilitati per impostazione predefinita, richiedendo che tutte le comunicazioni LDAP siano firmate e crittografate.

**Verifica della configurazione LDAP Signing e Channel Binding**

```powershell
# Verificare il livello di LDAP Signing richiesto dal DC
Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Services\NTDS\Parameters" -Name "LDAPServerIntegrity" -ErrorAction SilentlyContinue
# Valore 2 = Require signing (raccomandato)

# Verificare il livello di Channel Binding
Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Services\NTDS\Parameters" -Name "LdapEnforceChannelBinding" -ErrorAction SilentlyContinue
# Valore 2 = Always (raccomandato per Windows Server 2025+)

# Cercare nei log eventi le connessioni LDAP non firmate (Event ID 2889)
Get-WinEvent -FilterHashtable @{LogName='Directory Service'; Id=2889} -MaxEvents 20 -ErrorAction SilentlyContinue |
    Select-Object TimeCreated, Message

# Abilitare il logging diagnostico per LDAP (temporaneo, per troubleshooting)
# Set-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Services\NTDS\Diagnostics" -Name "16 LDAP Interface Events" -Value 2
```

**Configurazione LDAPS (LDAP over SSL/TLS)**

LDAPS crittografa l'intero traffico LDAP, proteggendo le credenziali e i dati trasmessi. E obbligatorio per ambienti conformi a normative come GDPR, PCI-DSS e ISO 27001:

```powershell
# Verificare che il DC abbia un certificato valido per LDAPS
Get-ChildItem Cert:\LocalMachine\My | Where-Object {
    $_.EnhancedKeyUsageList.FriendlyName -contains "Server Authentication" -and
    $_.NotAfter -gt (Get-Date) -and
    $_.Subject -match $env:COMPUTERNAME
} | Select-Object Subject, Thumbprint, NotAfter

# Test della connessione LDAPS (porta 636)
Test-NetConnection -ComputerName DC01.azienda.local -Port 636
```

```bash
# Test LDAPS da Linux con openssl
openssl s_client -connect DC01.azienda.local:636 -showcerts

# Test LDAPS con ldapsearch
ldapsearch -H ldaps://DC01.azienda.local:636 -x -b "DC=azienda,DC=local" -D "CN=admin,CN=Users,DC=azienda,DC=local" -W "(objectClass=user)" cn sAMAccountName -z 5

# Verifica del certificato LDAPS
echo | openssl s_client -connect DC01.azienda.local:636 2>/dev/null | openssl x509 -noout -dates -subject
```

**Monitoraggio delle prestazioni LDAP**

```powershell
# Query LDAP lente — verificare i contatori di prestazioni
# Performance Monitor > Active Directory > LDAP Searches/sec
# Performance Monitor > Active Directory > LDAP Successful Binds/sec
# Performance Monitor > Active Directory > LDAP Active Threads

# Verificare il numero di connessioni LDAP attive
Get-Counter "\NTDS\LDAP Active Threads" -SampleInterval 5 -MaxSamples 3
Get-Counter "\NTDS\LDAP Searches/sec" -SampleInterval 5 -MaxSamples 3
Get-Counter "\NTDS\LDAP Successful Binds/sec" -SampleInterval 5 -MaxSamples 3

# Identificare client con troppe connessioni LDAP (potenziale problema applicativo)
# Event ID 2898: LDAP notification limit reached
Get-WinEvent -FilterHashtable @{LogName='Directory Service'; Id=2898} -MaxEvents 10 -ErrorAction SilentlyContinue
```

### Group Policy Management

Le Group Policy (GPO) controllano le configurazioni di sicurezza, le impostazioni del desktop, le installazioni software e le restrizioni applicate agli utenti e ai computer del dominio. Una GPO mal configurata puo bloccare l'accesso a sistemi critici o aprire falle di sicurezza.

**Audit e manutenzione delle Group Policy**

```powershell
# Elenco di tutte le GPO con data di modifica
Get-GPO -All | Select-Object DisplayName, Id, GpoStatus, CreationTime, ModificationTime |
    Sort-Object ModificationTime -Descending | Format-Table -AutoSize

# GPO non collegate (potenziali candidati alla rimozione)
Get-GPO -All | ForEach-Object {
    $gpo = $_
    $links = (Get-GPOReport -Guid $gpo.Id -ReportType XML | Select-Xml -XPath "//gpo:LinksTo" -Namespace @{gpo="http://www.microsoft.com/GroupPolicy/Settings"}).Count
    if ($links -eq 0) {
        [PSCustomObject]@{
            Nome = $gpo.DisplayName
            UltimaModifica = $gpo.ModificationTime
            Stato = $gpo.GpoStatus
        }
    }
}

# Report HTML di una GPO specifica
Get-GPOReport -Name "Security Baseline" -ReportType HTML -Path "C:\Reports\GPO-SecurityBaseline.html"

# Report HTML di tutte le GPO
Get-GPOReport -All -ReportType HTML -Path "C:\Reports\GPO-All-$(Get-Date -Format 'yyyyMMdd').html"

# Verificare il risultato delle GPO su un computer specifico (RSoP)
gpresult /h C:\Reports\GPResult-ComputerName.html /scope computer
gpresult /h C:\Reports\GPResult-User.html /scope user

# Backup di tutte le GPO
Backup-GPO -All -Path "C:\Backup\GPO\$(Get-Date -Format 'yyyyMMdd')"
```

**Rilevamento delle modifiche alle GPO**

Il monitoraggio delle modifiche alle GPO e critico per la sicurezza e la conformita. Una modifica non autorizzata a una GPO puo disabilitare controlli di sicurezza, aprire porte nel firewall o concedere privilegi elevati:

```powershell
# Abilitare l'auditing sulle GPO (tramite Advanced Audit Policy)
# Configurare: Computer Configuration > Policies > Windows Settings > Security Settings >
# Advanced Audit Policy > DS Access > Audit Directory Service Changes

# Cercare eventi di modifica GPO (Event ID 5136, 5137)
Get-WinEvent -FilterHashtable @{LogName='Security'; Id=5136,5137} -MaxEvents 20 -ErrorAction SilentlyContinue |
    Where-Object { $_.Message -match "groupPolicyContainer" } |
    Select-Object TimeCreated, @{N='Dettagli';E={$_.Message.Substring(0, [Math]::Min(200, $_.Message.Length))}}
```

### AD Security Hardening

La protezione di Active Directory e una priorita di sicurezza critica. Il 95% delle aziende Fortune 1000 utilizza AD per la gestione delle identita, rendendolo un bersaglio primario per gli attaccanti. La compromissione di AD equivale alla compromissione dell'intera infrastruttura.

**Disabilitazione progressiva di NTLM**

A partire da Windows Server 2025, Microsoft raccomanda la dismissione progressiva di NTLM in favore di Kerberos. NTLM e vulnerabile ad attacchi pass-the-hash, relay e brute force:

```powershell
# Audit dell'utilizzo di NTLM nell'ambiente (prima di disabilitare)
# Abilitare l'auditing NTLM:
# Computer Configuration > Policies > Windows Settings > Security Settings >
# Local Policies > Security Options > Network security: Restrict NTLM

# Verificare gli eventi di autenticazione NTLM
Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4776} -MaxEvents 50 |
    Select-Object TimeCreated, @{N='Account';E={$_.Properties[0].Value}}, @{N='Source';E={$_.Properties[1].Value}}

# Cercare eventi NTLM specifici nel log NTLM operativo
Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-NTLM/Operational'} -MaxEvents 20 -ErrorAction SilentlyContinue
```

**Protezione degli account privilegiati**

```powershell
# Membri del gruppo Domain Admins (dovrebbero essere il minimo indispensabile)
Get-ADGroupMember "Domain Admins" | Select-Object Name, SamAccountName, ObjectClass

# Membri del gruppo Enterprise Admins
Get-ADGroupMember "Enterprise Admins" | Select-Object Name, SamAccountName, ObjectClass

# Membri del gruppo Schema Admins
Get-ADGroupMember "Schema Admins" | Select-Object Name, SamAccountName, ObjectClass

# Account di servizio con privilegi di Domain Admin (antipattern da correggere)
Get-ADGroupMember "Domain Admins" -Recursive | Where-Object {
    $_.Name -match "svc|service|app|sql|backup"
} | Select-Object Name, SamAccountName

# Verificare lo stato del gruppo Protected Users (migliora la sicurezza Kerberos)
Get-ADGroupMember "Protected Users" | Select-Object Name, SamAccountName

# Account con AdminCount=1 ma non piu membri di gruppi privilegiati (ACL orfane)
Get-ADUser -Filter {AdminCount -eq 1} -Properties AdminCount, MemberOf |
    Where-Object { -not ($_.MemberOf -match "Domain Admins|Enterprise Admins|Schema Admins|Administrators") } |
    Select-Object Name, SamAccountName
```

**Monitoraggio degli accessi anomali**

```powershell
# Account lockout recenti (possibile indicatore di attacco brute force)
Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4740} -MaxEvents 30 -ErrorAction SilentlyContinue |
    Select-Object TimeCreated, @{N='Account';E={$_.Properties[0].Value}}, @{N='CallerComputer';E={$_.Properties[1].Value}}

# Tentativi di accesso falliti (Event ID 4625)
Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4625} -MaxEvents 50 |
    Select-Object TimeCreated, @{N='Account';E={$_.Properties[5].Value}}, @{N='SourceIP';E={$_.Properties[19].Value}}, @{N='FailureReason';E={$_.Properties[8].Value}}

# Creazione di nuovi account amministratori (Event ID 4728 per gruppi globali)
Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4728,4732,4756} -MaxEvents 20 -ErrorAction SilentlyContinue |
    Select-Object TimeCreated, @{N='Dettagli';E={$_.Message.Substring(0, [Math]::Min(300, $_.Message.Length))}}
```

---

## Manutenzione NTP e PTP

La sincronizzazione temporale e un servizio fondazionale dell'infrastruttura IT. Senza un orario coerente e accurato su tutti i dispositivi, Kerberos (il protocollo di autenticazione di Active Directory) fallisce con una tolleranza predefinita di 5 minuti, i log non sono correlabili per le indagini di sicurezza, i backup incrementali possono produrre risultati incoerenti e le transazioni distribuite possono generare conflitti. NTP e PTP sono i due protocolli principali per la sincronizzazione temporale, ciascuno con casi d'uso e precisioni diverse.

### NTP — Network Time Protocol

NTP opera su UDP porta 123 e fornisce una precisione nell'ordine dei millisecondi, sufficiente per la maggior parte delle esigenze aziendali. L'architettura NTP e gerarchica e basata sul concetto di stratum: lo Stratum 0 e la sorgente di riferimento (orologio atomico, GPS), lo Stratum 1 e un server direttamente connesso alla sorgente, e cosi via fino allo Stratum 15 (Stratum 16 indica un server non sincronizzato).

**Architettura NTP raccomandata**

Per un'infrastruttura aziendale robusta, la RFC 8633 (Network Time Protocol Best Current Practices) raccomanda:

- Almeno 4 sorgenti NTP per ogni server per evitare il "two-clock problem" (con 2 sorgenti in disaccordo, il client non puo determinare quale sia corretta)
- Server NTP Stratum 1 interni con ricevitore GNSS multi-costellazione (GPS + Galileo + GLONASS)
- Server NTP Stratum 2 come sorgenti per i client interni
- Diversita dei percorsi di rete e delle sorgenti temporali
- Protezione NTS (Network Time Security) o autenticazione simmetrica

```
Architettura NTP aziendale:

[GPS/GNSS Antenna] ─── [Stratum 1 Server A]
                              │
[GPS/GNSS Antenna] ─── [Stratum 1 Server B]
                              │
                    ┌─────────┴─────────┐
              [Stratum 2 DC01]    [Stratum 2 DC02]
                    │                     │
              ┌─────┴─────┐         ┌────┴─────┐
         [Client]    [Client]   [Client]   [Client]
```

**Configurazione e manutenzione NTP su Windows**

In un dominio Active Directory, il PDC Emulator della foresta root e la sorgente temporale autorevole. Tutti gli altri DC sincronizzano con il PDC Emulator, e i client sincronizzano con il DC che li autentica:

```powershell
# Verificare la sorgente temporale e lo stato di sincronizzazione
w32tm /query /status
w32tm /query /source
w32tm /query /peers

# Verificare la configurazione del servizio W32Time
w32tm /query /configuration

# Configurare il PDC Emulator per sincronizzare con una sorgente esterna
w32tm /config /manualpeerlist:"0.it.pool.ntp.org,0x8 1.it.pool.ntp.org,0x8 2.it.pool.ntp.org,0x8 3.it.pool.ntp.org,0x8" /syncfromflags:manual /reliable:yes /update
Restart-Service w32time

# Forzare la risincronizzazione
w32tm /resync /force

# Monitorare lo scostamento temporale tra due macchine
w32tm /stripchart /computer:DC01.azienda.local /samples:5 /dataonly

# Verificare lo scostamento su tutti i DC
$dcs = Get-ADDomainController -Filter * | Select-Object -ExpandProperty HostName
foreach ($dc in $dcs) {
    $result = w32tm /stripchart /computer:$dc /samples:1 /dataonly 2>$null | Select-Object -Last 1
    Write-Output "$dc : $result"
}
```

**Configurazione e manutenzione NTP su Linux**

```bash
# Verificare lo stato di sincronizzazione con chrony (raccomandato su RHEL/CentOS/Fedora)
chronyc tracking
chronyc sources -v
chronyc sourcestats

# Verificare lo stato con ntpd (Debian/Ubuntu tradizionale)
ntpq -p
ntpstat

# Configurazione chrony (/etc/chrony.conf)
# server 0.it.pool.ntp.org iburst prefer
# server 1.it.pool.ntp.org iburst
# server 2.it.pool.ntp.org iburst
# server 3.it.pool.ntp.org iburst
# driftfile /var/lib/chrony/drift
# makestep 1 3
# rtcsync
# logdir /var/log/chrony
# log measurements statistics tracking

# Verificare il drift dell'orologio locale
cat /var/lib/chrony/drift

# Monitoraggio della salute NTP con Prometheus (chrony_exporter)
# Metriche chiave: chrony_tracking_last_offset_seconds, chrony_tracking_root_delay_seconds
```

**Soglie di allarme NTP**

| Metrica | Warning | Critico | Azione |
|---|---|---|---|
| Offset (scostamento) | > 100 ms | > 500 ms | Verificare sorgente NTP, rete |
| Jitter | > 50 ms | > 200 ms | Problemi di rete o sorgente instabile |
| Stratum | > 5 | > 10 | Catena troppo lunga, aggiungere sorgenti |
| Reach (raggiungibilita) | < 377 | < 177 | Perdita di pacchetti NTP |
| Root dispersion | > 100 ms | > 500 ms | Scarsa qualita della sorgente |

### PTP — Precision Time Protocol

PTP (IEEE 1588) fornisce una precisione nell'ordine dei nanosecondi/microsecondi, necessaria per applicazioni come il trading ad alta frequenza, le reti di telecomunicazione 5G, i sistemi di acquisizione dati scientifici e le reti di automazione industriale. PTP opera su porte UDP 319 (evento) e 320 (generale).

**Verifica della configurazione PTP su Linux**

```bash
# Stato del servizio ptp4l (implementazione Linux di PTP)
systemctl status ptp4l

# Stato della sincronizzazione PTP
pmc -u -b 0 'GET CURRENT_DATA_SET'
pmc -u -b 0 'GET TIME_STATUS_NP'

# Verifica dell'offset del clock
# L'output di ptp4l mostra l'offset in nanosecondi
journalctl -u ptp4l --since "5 minutes ago" | grep "offset"

# Configurazione PTP (/etc/ptp4l.conf)
# [global]
# twoStepFlag 1
# slaveOnly 1
# logging_level 6
# verbose 1
# use_syslog 1
# summary_interval 0
# domainNumber 0
# [eth0]

# Sincronizzare l'orologio di sistema con il clock PTP hardware
# phc2sys -a -r -r
systemctl status phc2sys
```

**Confronto NTP vs PTP**

| Caratteristica | NTP | PTP |
|---|---|---|
| Precisione tipica | 1-50 ms | 10 ns - 1 us |
| Porta | UDP 123 | UDP 319, 320 |
| Hardware dedicato | Non richiesto | Richiesto (NIC con hardware timestamping) |
| Complessita | Bassa | Media-Alta |
| Costo | Basso | Medio-Alto |
| Caso d'uso | Infrastruttura IT generale | Trading, telecomunicazioni, automazione |
| Standard | RFC 5905 | IEEE 1588-2019 |

### Monitoraggio e Troubleshooting Temporale

**Script di verifica della sincronizzazione temporale su tutta l'infrastruttura**

```bash
#!/bin/bash
# Verifica della sincronizzazione NTP su tutti i server Linux
SERVERS=(
    "server1.azienda.local"
    "server2.azienda.local"
    "server3.azienda.local"
)

SOGLIA_WARNING_MS=100
SOGLIA_CRITICO_MS=500

for server in "${SERVERS[@]}"; do
    offset_ms=$(ssh "$server" "chronyc tracking 2>/dev/null | grep 'Last offset' | awk '{print \$4}' | tr -d '-'" 2>/dev/null)
    if [ -z "$offset_ms" ]; then
        echo "ERRORE: $server - impossibile verificare NTP"
    else
        offset_abs=$(echo "$offset_ms * 1000" | bc 2>/dev/null)
        echo "$server: offset = ${offset_ms}s (${offset_abs}ms)"
    fi
done
```

**Problemi comuni di sincronizzazione temporale**

| Problema | Sintomo | Causa probabile | Risoluzione |
|---|---|---|---|
| Kerberos fallisce | "Clock skew too great" | Scostamento > 5 min tra client e DC | Forzare risincronizzazione NTP |
| Log non correlabili | Timestamp incoerenti nei SIEM | Server con fusi orari o sorgenti NTP diverse | Standardizzare su UTC, unificare sorgenti NTP |
| Offset crescente | Drift continuo dell'orologio | NTP non raggiunge la sorgente, firewall blocca UDP 123 | Verificare rete, aprire UDP 123 |
| Salti temporali | Cambio improvviso dell'ora | `makestep` troppo aggressivo, sorgente NTP anomala | Configurare `makestep 1 3` (solo al boot) |

---

## Servizi File di Rete (NFS, SMB/CIFS)

I servizi file di rete consentono la condivisione centralizzata dei dati tra i dispositivi dell'organizzazione. La scelta del protocollo (NFS per ambienti Unix/Linux, SMB/CIFS per ambienti Windows, o entrambi in ambienti misti) impatta direttamente le prestazioni, la sicurezza e la complessita di gestione. Una manutenzione accurata di questi servizi previene la perdita di dati, il degrado prestazionale e le violazioni dei permessi di accesso.

### NFS — Network File System

NFS e il protocollo standard per la condivisione di file in ambienti Unix/Linux e viene utilizzato estensivamente per i datastore VMware, le condivisioni applicative Oracle e le home directory degli utenti. La versione corrente e NFSv4.2 (RFC 7862), che introduce miglioramenti significativi in termini di sicurezza e prestazioni rispetto a NFSv3.

**Manutenzione e monitoraggio NFS Server (Linux)**

```bash
# Verificare le esportazioni NFS attive
exportfs -v

# Verificare il file di configurazione delle esportazioni
cat /etc/exports

# Statistiche del server NFS
nfsstat -s       # statistiche lato server
nfsstat -c       # statistiche lato client
nfsstat -m       # informazioni sui mount

# Verificare i client connessi
showmount -a     # mostra tutti i client connessi
showmount -d     # mostra le directory montate dai client

# Monitoraggio delle prestazioni NFS in tempo reale
nfsiostat 5 3    # intervallo 5 secondi, 3 campioni

# Verificare lo stato del servizio NFS
systemctl status nfs-server
systemctl status rpcbind

# Verificare i lock NFS attivi (potenziali problemi di stale lock)
cat /proc/fs/nfsd/max_block_size
sm-notify -f     # notifica ai client dopo il riavvio del server per rilasciare lock stale
```

**Configurazione sicura delle esportazioni NFS**

```bash
# Esempio di /etc/exports con opzioni di sicurezza
# /dati/condivisa  192.168.1.0/24(rw,sync,no_subtree_check,root_squash,sec=krb5p)
# /dati/readonly   192.168.1.0/24(ro,sync,no_subtree_check,all_squash,anonuid=65534,anongid=65534)

# Opzioni di sicurezza raccomandate:
# root_squash: mappa root remoto a anonuid/anongid (predefinito, non disabilitare)
# no_all_squash: mantiene l'identita degli utenti non-root
# sync: scrive su disco prima di confermare (previene la perdita di dati)
# sec=krb5p: autenticazione Kerberos con crittografia dei dati (NFSv4)
# no_subtree_check: migliora le prestazioni ed evita problemi con file rinominati

# Applicare le modifiche senza riavviare il servizio
exportfs -ra

# Verificare la versione NFS negoziata
mount | grep nfs
# oppure
nfsstat -m
```

**Differenze chiave tra NFSv3 e NFSv4**

| Caratteristica | NFSv3 | NFSv4/4.1/4.2 |
|---|---|---|
| Porte | Dinamiche (richiede portmapper) | Singola porta TCP 2049 |
| Sicurezza | AUTH_SYS (UID/GID) | Kerberos (krb5, krb5i, krb5p) |
| Firewall | Complesso (porte multiple) | Semplice (una porta) |
| Lock | Protocollo NLM separato | Integrato nel protocollo |
| ACL | Limitate (mode bits POSIX) | ACL complete stile Windows |
| Deleghe | No | Si (migliora cache client) |

### SMB/CIFS — Server Message Block

SMB e il protocollo nativo per la condivisione di file in ambienti Windows. La versione corrente e SMB 3.1.1 (introdotta con Windows 10/Server 2016), che include crittografia AES-256-GCM, integrita pre-autenticazione e protezione contro attacchi man-in-the-middle. CIFS (Common Internet File System) e il nome obsoleto di SMB 1.0, un protocollo con gravi vulnerabilita di sicurezza che deve essere disabilitato (ha permesso la diffusione di WannaCry e NotPetya).

**Disabilitazione di SMB 1.0 (OBBLIGATORIA)**

SMB 1.0 e un protocollo con vulnerabilita critiche note (MS17-010 / EternalBlue). La sua disabilitazione e una misura di sicurezza non negoziabile:

```powershell
# Verificare se SMB 1.0 e abilitato
Get-SmbServerConfiguration | Select-Object EnableSMB1Protocol

# Disabilitare SMB 1.0 sul server
Set-SmbServerConfiguration -EnableSMB1Protocol $false -Force

# Disabilitare il client SMB 1.0
Disable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol -NoRestart

# Verificare le versioni SMB negoziate nelle connessioni attive
Get-SmbConnection | Select-Object ServerName, ShareName, Dialect

# Audit delle connessioni SMB 1.0 prima della disabilitazione
# Abilitare l'auditing per identificare i client che usano ancora SMB 1.0
Set-SmbServerConfiguration -AuditSmb1Access $true
# Cercare nei log: Event ID 3000 nel log Microsoft-Windows-SMBServer/Audit
Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-SMBServer/Audit'; Id=3000} -MaxEvents 20 -ErrorAction SilentlyContinue
```

**Manutenzione delle condivisioni SMB**

```powershell
# Elenco delle condivisioni SMB con dettagli
Get-SmbShare | Where-Object {$_.Name -notlike "*$"} |
    Select-Object Name, Path, Description, CurrentUsers, EncryptData, FolderEnumerationMode | Format-Table -AutoSize

# Sessioni SMB attive
Get-SmbSession | Select-Object ClientComputerName, ClientUserName, NumOpens, SecondsExists, Dialect | Format-Table -AutoSize

# File aperti tramite SMB (utile per troubleshooting di file bloccati)
Get-SmbOpenFile | Select-Object ClientComputerName, ClientUserName, Path, ShareRelativePath | Format-Table -AutoSize

# Chiudere un file bloccato (dopo verifica con l'utente)
# Close-SmbOpenFile -FileId <ID> -Force

# Configurare la crittografia SMB su una condivisione
Set-SmbShare -Name "DatiSensibili" -EncryptData $true

# Verificare le prestazioni SMB
Get-SmbServerConfiguration | Select-Object EnableMultiChannel, MaxChannelPerSession, Smb2CreditsMin, Smb2CreditsMax
```

**Manutenzione Samba (SMB su Linux)**

```bash
# Verificare la configurazione di Samba
testparm -s

# Verificare lo stato del servizio
systemctl status smbd nmbd
smbstatus              # connessioni attive, file aperti, condivisioni

# Elenco delle condivisioni
smbclient -L localhost -N

# Verificare la versione SMB minima configurata
grep -i "server min protocol" /etc/samba/smb.conf
# Raccomandato: server min protocol = SMB2_10

# Verificare l'appartenenza al dominio AD
net ads testjoin
net ads info

# Monitoraggio delle prestazioni Samba
smbstatus -p     # processi attivi
smbstatus -S     # condivisioni in uso
smbstatus -L     # file bloccati
```

### Ambienti Multi-Protocollo

In ambienti enterprise misti (Windows + Linux), e frequente la necessita di condividere gli stessi dati tramite entrambi i protocolli NFS e SMB. Questa configurazione richiede attenzione particolare alla gestione dei permessi e alla mappatura delle identita.

**Sfide degli ambienti multi-protocollo**

1. **Mappatura delle identita:** gli UID/GID Unix devono corrispondere ai SID Windows. Soluzioni come SSSD, Winbind o ID mapping sui NAS enterprise gestiscono questa mappatura.
2. **Semantiche ACL diverse:** le ACL POSIX (NFS) e le ACL NTFS (SMB) hanno modelli di permessi diversi. I NAS enterprise (NetApp ONTAP, Dell PowerStore) gestiscono la traduzione automatica, ma e necessario definire quale stile di sicurezza (Unix o NTFS) sia prevalente per ogni volume.
3. **Lock file:** NFS e SMB utilizzano meccanismi di lock diversi. I NAS enterprise gestiscono i cross-protocol lock, ma e fondamentale verificare che funzionino correttamente per evitare la corruzione dei file.

```bash
# NetApp ONTAP: verificare lo stile di sicurezza di un volume
# vserver security style show -vserver SVM1

# NetApp ONTAP: verificare la mappatura nomi (name-mapping)
# vserver name-mapping show -vserver SVM1

# Verificare la coerenza dei permessi multi-protocollo
# Accedere allo stesso file via NFS e SMB e confrontare i permessi
ls -la /mount/nfs/file_test.txt
# Confrontare con i permessi visibili dal client Windows sullo stesso file
```

---

## Servizi di Stampa

I servizi di stampa, sebbene spesso sottovalutati, rimangono una componente essenziale dell'infrastruttura IT aziendale. Documenti legali, contratti, etichette di spedizione, report finanziari e badge identificativi richiedono ancora la stampa fisica. Un'interruzione dei servizi di stampa impatta direttamente i processi operativi, in particolare nei settori manifatturiero, sanitario, legale e logistico.

### Windows Print Server

**Monitoraggio e manutenzione del server di stampa Windows**

```powershell
# Elenco delle stampanti condivise e il loro stato
Get-Printer | Where-Object {$_.Shared -eq $true} |
    Select-Object Name, PortName, DriverName, PrinterStatus, JobCount, Shared | Format-Table -AutoSize

# Verificare i job di stampa in coda
Get-PrintJob -PrinterName "NomeStampante" | Select-Object Id, UserName, DocumentName, SubmittedTime, JobStatus, Size

# Eliminare tutti i job di stampa bloccati
Get-Printer | ForEach-Object {
    $jobs = Get-PrintJob -PrinterName $_.Name -ErrorAction SilentlyContinue
    if ($jobs) {
        $stuckJobs = $jobs | Where-Object { $_.JobStatus -match "Error|Offline|Paused" }
        if ($stuckJobs) {
            Write-Output "Stampante: $($_.Name) - Job bloccati: $($stuckJobs.Count)"
            # $stuckJobs | Remove-PrintJob
        }
    }
}

# Verificare lo stato dello spooler di stampa
Get-Service Spooler | Select-Object Status, StartType

# Riavviare lo spooler (risolve molti problemi di stampa)
Restart-Service Spooler -Force

# Pulire la coda di stampa manualmente (in caso di spooler bloccato)
Stop-Service Spooler -Force
Remove-Item "$env:SystemRoot\System32\spool\PRINTERS\*" -Force
Start-Service Spooler

# Report sull'utilizzo delle stampanti (richiede l'auditing abilitato)
Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-PrintService/Operational'; Id=307} -MaxEvents 100 -ErrorAction SilentlyContinue |
    Select-Object TimeCreated, @{N='Utente';E={$_.Properties[2].Value}}, @{N='Stampante';E={$_.Properties[4].Value}}, @{N='Pagine';E={$_.Properties[7].Value}}

# Gestione dei driver di stampa
Get-PrinterDriver | Select-Object Name, PrinterEnvironment, MajorVersion | Format-Table -AutoSize

# Driver di stampa v3 (legacy, da migrare a v4 o IPP Everywhere)
Get-PrinterDriver | Where-Object { $_.MajorVersion -lt 4 } |
    Select-Object Name, MajorVersion
```

**Universal Print (Microsoft 365)**

A partire dal 2025, Microsoft Universal Print offre un'alternativa cloud-native ai server di stampa on-premise. Le stampanti vengono registrate nel cloud e gestite tramite Entra ID, eliminando la necessita di server di stampa dedicati e driver locali:

```powershell
# Verificare lo stato del connettore Universal Print
# Il connettore gira come servizio Windows e collega le stampanti on-premise a Universal Print
Get-Service "UniversalPrintConnector" -ErrorAction SilentlyContinue |
    Select-Object Status, StartType

# La gestione avviene tramite il portale admin Universal Print
# https://portal.azure.com > Universal Print
# oppure tramite Microsoft Graph API
```

### CUPS — Linux/Unix Print Server

CUPS (Common Unix Printing System) e il sistema di stampa standard per Linux e macOS. Utilizza nativamente il protocollo IPP (Internet Printing Protocol) e puo funzionare come server di stampa centralizzato per reti miste.

```bash
# Verificare lo stato del servizio CUPS
systemctl status cups

# Elenco delle stampanti configurate
lpstat -p -d
lpstat -a        # stato di accettazione dei job

# Coda di stampa
lpq -a           # tutti i job in coda
lpstat -o        # job in attesa

# Cancellare un job di stampa specifico
cancel <job-id>
# Cancellare tutti i job di una stampante
cancel -a NomeStampante

# Verificare la configurazione CUPS
cupsctl           # mostra la configurazione corrente

# Configurazione sicura di CUPS (/etc/cups/cupsd.conf)
# ServerAlias *
# Listen localhost:631
# Listen /var/run/cups/cups.sock
# Browsing Off
# DefaultAuthType Basic
# WebInterface Yes

# Log di CUPS per troubleshooting
# /var/log/cups/error_log     — errori del servizio
# /var/log/cups/access_log    — accessi all'interfaccia web
# /var/log/cups/page_log      — pagine stampate (per accounting)

# Aumentare il livello di debug (temporaneamente)
cupsctl --debug-logging
# Ripristinare il livello normale
cupsctl --no-debug-logging

# Aggiungere una stampante di rete via IPP
lpadmin -p NomeStampante -E -v ipp://192.168.1.100/ipp/print -m everywhere
```

### Monitoraggio e Troubleshooting Stampa

**Metriche chiave da monitorare**

| Metrica | Soglia Warning | Soglia Critica | Azione |
|---|---|---|---|
| Job in coda | > 20 | > 50 | Verificare stato stampante |
| Tempo medio in coda | > 5 min | > 15 min | Verificare prestazioni stampante/rete |
| Errori di stampa/giorno | > 10 | > 30 | Verificare driver, connettivita |
| Dimensione spool | > 1 GB | > 5 GB | Pulire spool, verificare job anomali |

**Problemi comuni e risoluzione**

| Problema | Causa probabile | Risoluzione |
|---|---|---|
| Job bloccato in coda | Driver incompatibile, stampante offline | Riavviare spooler, verificare connettivita |
| Stampa lenta | File di grandi dimensioni, rete congestionata | Verificare rete, comprimere documenti |
| Qualita scadente | Toner/cartuccia esaurita, testina sporca | Manutenzione hardware della stampante |
| Stampante non trovata | DNS/mDNS non risolvono, porta WSD bloccata | Verificare risoluzione nomi, firewall |
| Permessi negati | ACL sulla condivisione o GPO restrittive | Verificare permessi, GPO di stampa |

---

## Manutenzione Virtualizzazione

La virtualizzazione e diventata il paradigma dominante per l'erogazione dei servizi IT aziendali. Le piattaforme di virtualizzazione ospitano la maggior parte dei workload di produzione: server applicativi, database, servizi infrastrutturali, ambienti di sviluppo e test. Un guasto dell'infrastruttura di virtualizzazione ha un impatto a cascata su tutti i servizi virtualizzati. La manutenzione proattiva degli hypervisor, dei cluster e delle risorse virtuali e quindi critica per la continuita operativa.

Il panorama della virtualizzazione enterprise e in rapida evoluzione: l'acquisizione di VMware da parte di Broadcom (completata nel 2024) ha portato alla eliminazione delle licenze perpetue e al passaggio a modelli esclusivamente subscription-based, con aumenti di costo significativi. Questo ha causato una crescita esponenziale (+340% anno su anno secondo Gartner) delle valutazioni di alternative come Proxmox VE, oltre a un rinnovato interesse per Microsoft Hyper-V e per le soluzioni basate su KVM.

### VMware vSphere / ESXi

**Manutenzione degli host ESXi**

```bash
# Verificare lo stato di salute dell'host ESXi (via SSH)
esxcli system health status get
esxcli hardware platform get

# Verificare lo stato dei datastore
esxcli storage filesystem list

# Verificare gli aggiornamenti disponibili
esxcli software vib list | head -20
esxcli software profile get

# Verificare lo stato delle NIC fisiche
esxcli network nic list
esxcli network nic stats get -n vmnic0

# Verificare lo stato dei percorsi multipath
esxcli storage nmp path list

# Log degli eventi recenti
tail -100 /var/log/vmkernel.log
tail -100 /var/log/hostd.log
```

**Manutenzione vCenter e cluster (PowerCLI)**

```powershell
# Connessione a vCenter
# Connect-VIServer -Server vcenter.azienda.local

# Stato di salute di tutti gli host nel cluster
Get-VMHost | Select-Object Name, ConnectionState, PowerState,
    @{N='CPU_Usage%';E={[math]::Round($_.CpuUsageMhz/$_.CpuTotalMhz*100,1)}},
    @{N='RAM_Usage%';E={[math]::Round($_.MemoryUsageGB/$_.MemoryTotalGB*100,1)}},
    Version, Build | Format-Table -AutoSize

# Verificare gli allarmi attivi
Get-AlarmAction | Where-Object {$_.Alarm.ExtensionData.Info.Enabled}

# VM con snapshot attivi (consumano spazio e degradano le prestazioni)
Get-VM | Get-Snapshot | Select-Object VM, Name, Created, SizeGB |
    Sort-Object SizeGB -Descending | Format-Table -AutoSize

# Snapshot piu vecchi di 7 giorni (da rimuovere)
Get-VM | Get-Snapshot | Where-Object {
    $_.Created -lt (Get-Date).AddDays(-7)
} | Select-Object VM, Name, Created, SizeGB

# Verifica della configurazione HA del cluster
Get-Cluster | Select-Object Name, HAEnabled, HAFailoverLevel, DrsEnabled, DrsMode | Format-Table -AutoSize

# VM con risorse sovradimensionate (right-sizing)
Get-VM | Where-Object {$_.PowerState -eq "PoweredOn"} | ForEach-Object {
    $vm = $_
    $stats = Get-Stat -Entity $vm -Stat "cpu.usage.average","mem.usage.average" -Realtime -MaxSamples 30
    $avgCpu = ($stats | Where-Object {$_.MetricId -eq "cpu.usage.average"} | Measure-Object -Property Value -Average).Average
    $avgMem = ($stats | Where-Object {$_.MetricId -eq "mem.usage.average"} | Measure-Object -Property Value -Average).Average
    if ($avgCpu -lt 10 -and $avgMem -lt 20) {
        [PSCustomObject]@{
            VM = $vm.Name
            vCPU = $vm.NumCpu
            RAM_GB = [math]::Round($vm.MemoryGB, 1)
            Avg_CPU_Pct = [math]::Round($avgCpu, 1)
            Avg_MEM_Pct = [math]::Round($avgMem, 1)
            Nota = "Candidata al right-sizing"
        }
    }
}
```

### Microsoft Hyper-V

**Manutenzione degli host Hyper-V**

```powershell
# Stato di salute dell'host Hyper-V
Get-VMHost | Select-Object Name, LogicalProcessorCount, MemoryCapacity,
    VirtualHardDiskPath, VirtualMachinePath | Format-List

# Elenco delle VM con stato e risorse
Get-VM | Select-Object Name, State, CPUUsage, MemoryAssigned, MemoryDemand,
    Uptime, Status | Format-Table -AutoSize

# VM con checkpoint attivi (equivalenti VMware snapshot)
Get-VM | Get-VMSnapshot | Select-Object VMName, Name, CreationTime,
    @{N='SizeGB';E={[math]::Round(($_.HardDrives | ForEach-Object {(Get-VHD $_.Path).FileSize} | Measure-Object -Sum).Sum/1GB,2)}} |
    Sort-Object CreationTime

# Verificare lo stato della replica Hyper-V
Get-VMReplication | Select-Object VMName, State, Health, Mode, PrimaryServer, ReplicaServer, FrequencySec |
    Format-Table -AutoSize

# Verificare la replica con problemi
Get-VMReplication | Where-Object { $_.Health -ne "Normal" } |
    Select-Object VMName, Health, LastReplicationTime

# Stato del cluster Hyper-V
Get-ClusterNode | Select-Object Name, State, DynamicWeight
Get-ClusterResource | Where-Object { $_.ResourceType -eq "Virtual Machine" } |
    Select-Object Name, State, OwnerNode | Format-Table -AutoSize

# Verificare la Live Migration
Get-VMHost | Select-Object VirtualMachineMigrationEnabled,
    VirtualMachineMigrationAuthenticationType,
    MaximumVirtualMachineMigrations

# Verifica dei Virtual Switch
Get-VMSwitch | Select-Object Name, SwitchType, NetAdapterInterfaceDescription, AllowManagementOS | Format-Table -AutoSize
```

### Proxmox VE

Proxmox VE e una piattaforma di virtualizzazione open-source che combina KVM per le macchine virtuali e LXC per i container. Con Proxmox VE 9 (rilasciato a meta 2025), la piattaforma ha raggiunto un livello di maturita enterprise, con supporto per Ceph integrato, Software-Defined Networking (SDN), High Availability e backup integrati.

**Manutenzione di Proxmox VE**

```bash
# Verificare lo stato del cluster Proxmox
pvecm status
pvecm nodes

# Stato dello storage
pvesm status

# Verificare lo stato di tutti i nodi
pvesh get /cluster/status

# Elenco delle VM e dei container con stato
qm list          # macchine virtuali KVM
pct list         # container LXC

# Verificare le risorse del nodo
pvesh get /nodes/$(hostname)/status

# Stato del servizio di HA
ha-manager status

# Verificare gli aggiornamenti disponibili
apt update && apt list --upgradable

# Verifica dello storage Ceph (se configurato)
ceph -s          # stato del cluster Ceph
ceph osd tree    # topologia degli OSD
ceph df          # utilizzo dello storage Ceph
rados df         # dettaglio per pool

# Verificare i backup schedulati
pvesh get /cluster/backup

# Verifica della salute del cluster Proxmox
pvesh get /cluster/resources --type vm |
    python3 -c "import sys,json; data=json.load(sys.stdin); [print(f\"{d['name']}: status={d['status']}, cpu={d.get('cpu',0):.1%}, mem={d.get('mem',0)/d.get('maxmem',1):.1%}\") for d in data]"
```

### Infrastruttura Iperconvergente (HCI)

L'infrastruttura iperconvergente (HCI) integra compute, storage e networking in un'unica piattaforma software-defined, eliminando la necessita di SAN e NAS dedicati. I principali vendor nel 2025-2026 sono Nutanix, VMware vSAN (ora sotto Broadcom), Dell VxRail, HPE SimpliVity e Scale Computing. Il 52% dei leader IT sta considerando strategie multi-hypervisor per evitare il vendor lock-in, in seguito ai cambiamenti di licensing post-acquisizione Broadcom.

**Manutenzione di un cluster HCI Nutanix**

```bash
# Stato del cluster Nutanix (da CVM — Controller VM)
ncli cluster get-params
ncli cluster status

# Stato dei nodi
ncli host list

# Stato dello storage
ncli container list
ncli storage-pool list

# Verificare lo stato di salute del cluster
ncc health_checks run_all

# NCC (Nutanix Cluster Check) — verifica completa
ncc health_checks run_all --show_passed=false

# Verificare lo stato del RF (Replication Factor)
ncli container list | grep -E "Name|Replication"

# Stato delle VM
acli vm.list

# Verificare l'utilizzo delle risorse
ncli cluster get-utilization-stats

# Aggiornamenti disponibili
# Gestiti tramite Prism Central > Life Cycle Manager (LCM)
# lcm inventory
# lcm upgrade
```

**Metriche chiave per il monitoraggio HCI**

| Metrica | Soglia Warning | Soglia Critica | Impatto |
|---|---|---|---|
| Utilizzo CPU cluster | > 70% | > 85% | Prestazioni VM degradate |
| Utilizzo RAM cluster | > 75% | > 90% | Impossibilita di avviare nuove VM |
| Utilizzo storage | > 70% | > 85% | Rischio di esaurimento spazio |
| Latenza I/O | > 5 ms | > 20 ms | Rallentamento applicazioni |
| Degraded nodes | >= 1 | >= 2 | Riduzione della ridondanza |
| Rebuild in corso | Presente | Presente + nodo down | Rischio perdita dati |

**Confronto delle piattaforme di virtualizzazione (2025-2026)**

| Caratteristica | VMware vSphere | Microsoft Hyper-V | Proxmox VE |
|---|---|---|---|
| Licenza | Subscription (Broadcom) | Inclusa in Windows Server | Open source (GPL) |
| Costo 10 host | ~45.000+ EUR/anno | ~15.000 EUR (licenze WS) | ~1.000 EUR/anno (supporto) |
| Hypervisor | ESXi (Type 1) | Hyper-V (Type 1) | KVM (Type 1) + LXC |
| Storage integrato | vSAN | Storage Spaces Direct | Ceph, ZFS |
| Ecosistema | Vastissimo | Ampio (integrazione MS) | In crescita |
| Complessita | Media-Alta | Media | Media |
| Supporto enterprise | Broadcom/partner | Microsoft | Proxmox Server Solutions |

---

## Servizi di Accesso alla Rete (RADIUS, TACACS+, 802.1X)

I servizi di accesso alla rete controllano chi e cosa puo connettersi alla rete aziendale e chi puo amministrare i dispositivi di rete. RADIUS gestisce l'autenticazione degli utenti e dei dispositivi (Wi-Fi, VPN, accesso cablato 802.1X), mentre TACACS+ gestisce l'autenticazione e l'autorizzazione degli amministratori di rete. In un'architettura Zero Trust, questi servizi sono il primo punto di applicazione delle policy di accesso.

### RADIUS e 802.1X

RADIUS (Remote Authentication Dial-In User Service) opera su porte UDP 1812 (autenticazione) e 1813 (accounting). IEEE 802.1X fornisce il framework per l'autenticazione port-based, utilizzando RADIUS come backend di autenticazione e EAP (Extensible Authentication Protocol) come meccanismo di trasporto delle credenziali.

**Manutenzione del server RADIUS (FreeRADIUS)**

```bash
# Verificare lo stato del servizio FreeRADIUS
systemctl status freeradius

# Test di autenticazione RADIUS
radtest utente_test password_test localhost 0 shared_secret_test

# Test con attributi EAP (piu realistico)
eapol_test -c /etc/freeradius/eapol_test.conf -s shared_secret

# Verificare la configurazione
freeradius -XC    # verifica sintattica della configurazione

# Avviare in modalita debug (per troubleshooting)
freeradius -X     # output verbose su console

# Log delle autenticazioni
tail -f /var/log/freeradius/radius.log

# Statistiche del server
radmin -e "stats client"

# Verificare i client RADIUS configurati (switch, AP, VPN)
cat /etc/freeradius/3.0/clients.conf | grep -E "client|secret|ipaddr"
```

**Manutenzione NPS (Windows Network Policy Server)**

```powershell
# Verificare lo stato del servizio NPS
Get-Service IAS | Select-Object Status, StartType

# Elenco delle policy di rete
netsh nps show np

# Elenco dei client RADIUS configurati
netsh nps show client

# Log delle autenticazioni (richiede il logging abilitato)
Get-WinEvent -FilterHashtable @{LogName='Security'; Id=6272,6273} -MaxEvents 30 |
    Select-Object TimeCreated, @{N='Risultato';E={if($_.Id -eq 6272){'Successo'}else{'Fallito'}}},
    @{N='Utente';E={$_.Properties[1].Value}}

# Backup della configurazione NPS
netsh nps export filename="C:\Backup\NPS\NPS-Config-$(Get-Date -Format 'yyyyMMdd').xml" exportPSK=YES

# Ripristino della configurazione NPS
# netsh nps import filename="C:\Backup\NPS\NPS-Config.xml"
```

**Architettura 802.1X tipica**

```
[Client/Supplicant] ─── 802.1X ──── [Switch/AP (Authenticator)] ─── RADIUS ──── [RADIUS Server]
                                                                                       │
                                                                            [Directory Service]
                                                                            (AD, LDAP, Entra ID)
```

Componenti e flusso:
1. **Supplicant:** il client (PC, telefono, IoT) che richiede l'accesso alla rete
2. **Authenticator:** lo switch o l'access point che media l'autenticazione
3. **Authentication Server:** il server RADIUS che verifica le credenziali contro il directory service

**Metodi EAP raccomandati (2025-2026)**

| Metodo EAP | Sicurezza | Complessita | Caso d'uso |
|---|---|---|---|
| EAP-TLS | Massima (certificati X.509) | Alta (richiede PKI) | Dispositivi aziendali gestiti |
| PEAP-MSCHAPv2 | Buona (password + TLS tunnel) | Media | BYOD, ambienti misti |
| EAP-TTLS | Buona (flessibile nel metodo interno) | Media | Ambienti Linux/multi-piattaforma |
| TEAP | Massima (RFC 7170, multi-round) | Alta | Sostituzione moderna di PEAP |

### TACACS+

TACACS+ (Terminal Access Controller Access-Control System Plus) opera su porta TCP 49 e fornisce autenticazione, autorizzazione e accounting separati (a differenza di RADIUS che combina autenticazione e autorizzazione). TACACS+ crittografa l'intero pacchetto (RADIUS crittografa solo la password), rendendolo piu sicuro per l'amministrazione dei dispositivi di rete.

**Manutenzione del server TACACS+**

```bash
# Verificare lo stato del servizio (tac_plus o Cisco ISE)
systemctl status tac_plus

# Verificare la configurazione
tac_plus -P /etc/tacacs+/tac_plus.conf

# Log delle autenticazioni amministrative
tail -f /var/log/tac_plus.acct

# Test di autenticazione
# Da un dispositivo di rete:
# switch# test aaa group tacacs+ user admin legacy
```

**Confronto RADIUS vs TACACS+**

| Caratteristica | RADIUS | TACACS+ |
|---|---|---|
| Protocollo | UDP 1812/1813 | TCP 49 |
| Crittografia | Solo password | Intero pacchetto |
| AAA | Combinati (AuthN + AuthZ) | Separati (piu granulare) |
| Caso d'uso primario | Accesso alla rete (802.1X, VPN, Wi-Fi) | Amministrazione dispositivi di rete |
| Accounting | Dettagliato | Dettagliato |
| Autorizzazione per comando | No | Si (per-command authorization) |

### Network Access Control (NAC)

NAC estende 802.1X con la verifica della postura del dispositivo (antivirus aggiornato, patch installate, cifratura disco attiva) prima di concedere l'accesso completo alla rete. I dispositivi non conformi vengono indirizzati a una VLAN di remediation.

**Verifica della configurazione NAC sugli switch**

```
! Configurazione 802.1X su switch Cisco (esempio)
! Verificare lo stato delle porte 802.1X
show dot1x all
show dot1x interface GigabitEthernet1/0/1

! Verificare lo stato di autenticazione per porta
show authentication sessions
show authentication sessions interface GigabitEthernet1/0/1 details

! Verificare le VLAN assegnate dinamicamente
show vlan brief

! Log delle autenticazioni
show logging | include DOT1X|MAB|RADIUS
```

---

## PKI — Infrastruttura a Chiave Pubblica

La PKI (Public Key Infrastructure) e il framework crittografico che consente la gestione dei certificati digitali utilizzati per l'autenticazione, la crittografia e la firma digitale. I certificati PKI sono alla base di HTTPS, VPN, email sicura (S/MIME), 802.1X (EAP-TLS), firma del codice e autenticazione smart card. Una PKI mal gestita espone l'organizzazione a interruzioni di servizio (certificati scaduti), man-in-the-middle (certificati non verificati) e compromissioni (chiavi private non protette).

A partire dal 2026, la durata massima dei certificati TLS pubblici e stata ridotta a 200 giorni (con ulteriore riduzione a 100 giorni nel 2027 e 47 giorni entro marzo 2029), rendendo l'automazione del ciclo di vita dei certificati non piu opzionale ma obbligatoria.

### Architettura PKI Aziendale

L'architettura PKI raccomandata e a due livelli (two-tier):

```
[Root CA] ────────── OFFLINE (fisicamente isolata)
    │                 Emette solo il certificato della Subordinate CA
    │                 Chiave privata in HSM o su supporto rimovibile
    │
[Issuing CA] ──────── ONLINE (integrata in AD come Enterprise CA)
    │                 Emette certificati a utenti, computer, servizi
    │                 Chiave privata in HSM o nel software store protetto
    │
    ├── [Certificati utente] ── Autenticazione smart card, S/MIME, firma documenti
    ├── [Certificati computer] ── 802.1X EAP-TLS, LDAPS, IPSec
    ├── [Certificati server] ── HTTPS, LDAPS, Exchange, SQL Server
    └── [Certificati servizio] ── Code signing, timestamping
```

**Manutenzione della CA (Active Directory Certificate Services)**

```powershell
# Verificare lo stato del servizio CA
Get-Service CertSvc | Select-Object Status, StartType
certutil -ping    # verifica la raggiungibilita della CA

# Verificare la configurazione della CA
certutil -CAInfo
certutil -getreg CA\ValidityPeriod
certutil -getreg CA\ValidityPeriodUnits

# Elenco dei template di certificato pubblicati
certutil -CATemplates

# Certificati emessi negli ultimi 30 giorni
certutil -view -restrict "NotBefore>=$(Get-Date (Get-Date).AddDays(-30) -Format 'MM/dd/yyyy')" -out "RequestID,CommonName,NotBefore,NotAfter,CertificateTemplate"

# Certificati in scadenza nei prossimi 30 giorni
certutil -view -restrict "NotAfter<=$(Get-Date (Get-Date).AddDays(30) -Format 'MM/dd/yyyy'),NotAfter>=$(Get-Date -Format 'MM/dd/yyyy')" -out "RequestID,CommonName,NotAfter,CertificateTemplate"

# Certificati revocati
certutil -view -restrict "Disposition=21" -out "RequestID,CommonName,RevokedWhen,RevokedReason"

# Verificare la CRL (Certificate Revocation List)
certutil -getCRL

# Verificare che la CRL sia accessibile e non scaduta
certutil -URL "http://pki.azienda.it/CertEnroll/Azienda-CA.crl"

# Backup della CA (database e chiave privata)
certutil -backupDB C:\Backup\CA\DB
certutil -backupKey C:\Backup\CA\Key
```

### Gestione del Ciclo di Vita dei Certificati

Il ciclo di vita di un certificato comprende: emissione, distribuzione, utilizzo, rinnovo, revoca e archiviazione. Ogni fase richiede processi e controlli specifici.

**Inventario centralizzato dei certificati**

```powershell
# Inventario dei certificati su un server Windows
Get-ChildItem Cert:\LocalMachine\My | Select-Object Subject, Thumbprint, NotAfter,
    @{N='GiorniAllaScadenza';E={($_.NotAfter - (Get-Date)).Days}},
    @{N='KeyAlgorithm';E={$_.PublicKey.Key.KeySize}},
    @{N='SignatureAlgorithm';E={$_.SignatureAlgorithm.FriendlyName}} |
    Sort-Object NotAfter | Format-Table -AutoSize

# Certificati in scadenza nei prossimi 90 giorni (su tutti i server)
$servers = @("WEB01", "WEB02", "EXCHANGE01", "SQL01")
foreach ($server in $servers) {
    Invoke-Command -ComputerName $server -ScriptBlock {
        Get-ChildItem Cert:\LocalMachine\My | Where-Object {
            $_.NotAfter -lt (Get-Date).AddDays(90) -and $_.NotAfter -gt (Get-Date)
        } | Select-Object Subject, NotAfter, Thumbprint
    } | Select-Object @{N='Server';E={$server}}, Subject, NotAfter, Thumbprint
}
```

```bash
# Inventario dei certificati su server Linux
# Verificare i certificati in /etc/ssl/certs, /etc/pki/tls/certs
find /etc/ssl /etc/pki -name "*.pem" -o -name "*.crt" 2>/dev/null | while read cert; do
    expiry=$(openssl x509 -in "$cert" -noout -enddate 2>/dev/null | cut -d= -f2)
    subject=$(openssl x509 -in "$cert" -noout -subject 2>/dev/null | cut -d= -f2-)
    if [ -n "$expiry" ]; then
        echo "$cert | Subject: $subject | Scadenza: $expiry"
    fi
done

# Verificare i certificati di un servizio remoto
echo | openssl s_client -connect servizio.azienda.it:443 -servername servizio.azienda.it 2>/dev/null |
    openssl x509 -noout -dates -subject -issuer -fingerprint
```

### Automazione e ACME

Il protocollo ACME (Automatic Certificate Management Environment, RFC 8555) automatizza l'emissione, il rinnovo e la revoca dei certificati. Let's Encrypt e il provider ACME piu noto per i certificati pubblici, ma e possibile configurare server ACME interni (come Smallstep, EJBCA o Boulder) per i certificati aziendali interni.

```bash
# Verificare lo stato dei certificati gestiti da certbot
certbot certificates

# Rinnovo automatico con verifica
certbot renew --dry-run

# Configurazione del rinnovo automatico via systemd timer
# /etc/systemd/system/certbot-renewal.timer
# [Timer]
# OnCalendar=*-*-* 03:00:00
# RandomizedDelaySec=3600
# Persistent=true

# Monitoraggio della scadenza dei certificati con Prometheus
# Utilizzare blackbox_exporter con il modulo tls_connect
# probe_ssl_earliest_cert_expiry fornisce la data di scadenza
```

---

## IPAM e DDI — Gestione Indirizzi IP

La gestione degli indirizzi IP (IPAM — IP Address Management) e la gestione integrata DDI (DNS, DHCP, IPAM) rappresentano servizi fondamentali per il governo della rete aziendale. Con la crescita esponenziale dei dispositivi connessi (IoT, BYOD, container, microservizi), la gestione manuale degli indirizzi IP tramite fogli di calcolo non e piu sostenibile. Meno della meta (48%) delle organizzazioni ha piena visibilita sulle proprie risorse DDI, esponendosi a conflitti IP, zone DNS orfane e scope DHCP mal dimensionati.

### IPAM — IP Address Management

IPAM centralizza la visibilita e il controllo sull'allocazione degli indirizzi IP (IPv4 e IPv6), la gestione delle subnet, il tracciamento delle assegnazioni e il rilevamento dei conflitti.

**IPAM integrato in Windows Server**

```powershell
# Verificare lo stato del servizio IPAM
Get-Service IPAM* | Select-Object Name, Status

# Panoramica dell'utilizzo degli indirizzi IP
Get-IpamRange | Select-Object NetworkId, StartAddress, EndAddress,
    ManagedByService, PercentageUtilized, AssignedAddresses |
    Sort-Object PercentageUtilized -Descending | Format-Table -AutoSize

# Range con utilizzo superiore all'80%
Get-IpamRange | Where-Object { $_.PercentageUtilized -gt 80 } |
    Select-Object NetworkId, PercentageUtilized, AssignedAddresses

# Ricerca di un indirizzo IP specifico
Find-IpamFreeAddress -SubnetId "192.168.1.0/24" -NumberOfAddresses 5

# Conflitti IP rilevati
Get-IpamAddress | Where-Object { $_.AddressState -eq "Conflicting" } |
    Select-Object IPAddress, MACAddress, DeviceName

# Audit dell'utilizzo degli indirizzi (storico)
Get-IpamAddressUtilizationThreshold
```

**Strumenti IPAM open source**

Per ambienti non-Windows o multi-piattaforma, phpIPAM e NetBox sono le soluzioni open source piu diffuse:

```bash
# NetBox (DCIM + IPAM) — verifica dello stato
systemctl status netbox netbox-rq

# NetBox API — query delle subnet
# curl -s -H "Authorization: Token <TOKEN>" \
#   "https://netbox.azienda.local/api/ipam/prefixes/?status=active" | python3 -m json.tool

# phpIPAM — verifica dello stato
systemctl status apache2    # o nginx
systemctl status mysql      # backend database
```

### DDI — DNS, DHCP e IPAM Integrati

Il mercato DDI (DNS, DHCP, IPAM) ha raggiunto i 755 milioni di dollari nel 2025 e sta crescendo rapidamente, spinto dalla necessita di automazione della rete, dalla transizione IPv6 e dall'integrazione con piattaforme cloud e container. Una soluzione DDI integrata offre una vista unificata di tutte le risorse di rete, automazione del provisioning e rilevamento proattivo delle anomalie.

**Architettura DDI tipica**

```
[DDI Management Platform]
        │
        ├── [DNS Management] ─── Gestione zone, record, DNSSEC
        │       │
        │       ├── DNS Autoritativo (zone interne)
        │       └── DNS Ricorsivo (risoluzione esterna)
        │
        ├── [DHCP Management] ── Gestione scope, lease, failover
        │       │
        │       ├── DHCP Server primario
        │       └── DHCP Server secondario (failover)
        │
        └── [IPAM] ──────────── Inventario IP, subnet, VLAN
                │
                ├── Tracciamento assegnazioni
                ├── Rilevamento conflitti
                ├── Pianificazione capacita
                └── Report e compliance
```

**Vendor DDI principali (2025-2026)**

| Vendor | Tipo | Punti di forza |
|---|---|---|
| Infoblox | Appliance/SaaS | Market leader, DNS security integrata, threat intelligence |
| EfficientIP | Appliance/VM | Forte in EMEA, DNS Guardian, integrazione SIEM |
| BlueCat | Software/SaaS | Integrazione cloud nativa, API-first |
| ManageEngine DDI Central | Software | Costo accessibile, integrazione con suite ManageEngine |
| SolarWinds IPAM | Software | Forte in ambienti mid-market, interfaccia intuitiva |
| Micetro (Men&Mice) | Overlay | Si sovrappone all'infrastruttura esistente senza sostituirla |

**Metriche chiave per il monitoraggio DDI**

| Metrica | Soglia Warning | Soglia Critica | Azione |
|---|---|---|---|
| Utilizzo subnet IPv4 | > 75% | > 90% | Pianificare espansione o suddivisione |
| Zone DNS senza SOA update | > 30 giorni | > 90 giorni | Verificare zone orfane |
| Scope DHCP utilizzo | > 80% | > 95% | Espandere scope, ridurre lease time |
| Conflitti IP rilevati | > 0 | > 5 | Investigare e risolvere immediatamente |
| DNS query rate anomalo | +50% dalla baseline | +200% dalla baseline | Possibile attacco DDoS o malware |
| Lease DHCP scaduti non rilasciati | > 10% | > 25% | Verificare client, pulizia lease |

### Transizione IPv6

Oltre il 48% delle aziende globali sta completando una transizione parziale a IPv6 entro il 2026. La gestione di un ambiente dual-stack (IPv4 + IPv6) richiede strumenti IPAM in grado di tracciare entrambi gli spazi di indirizzamento e garantire la coerenza delle configurazioni DNS (record A e AAAA) e DHCP (DHCPv4 e DHCPv6/SLAAC).

**Verifica della configurazione IPv6**

```bash
# Verificare la configurazione IPv6 sulle interfacce
ip -6 addr show
ip -6 route show

# Verificare la raggiungibilita IPv6
ping6 -c 4 ipv6.azienda.it

# Verificare i record AAAA nel DNS
dig AAAA www.azienda.it
dig AAAA www.azienda.it @dns-server

# Verificare la configurazione DHCPv6 (ISC DHCP)
# dhcpd -6 -t    # verifica sintattica della configurazione

# Verificare lo stato del Router Advertisement
radvdump          # cattura gli annunci RA sulla rete
```

```powershell
# Windows: verificare la configurazione IPv6
Get-NetIPAddress -AddressFamily IPv6 | Select-Object InterfaceAlias, IPAddress, PrefixLength, AddressState

# Verificare la raggiungibilita IPv6
Test-Connection -TargetName ipv6.azienda.it -IPv6

# Stato della transizione ISATAP, Teredo, 6to4 (meccanismi di transizione)
Get-NetIPInterface | Where-Object { $_.InterfaceAlias -match "isatap|teredo|6to4" } |
    Select-Object InterfaceAlias, AddressFamily, ConnectionState
```

---

## Best Practices

1. **Documentare ogni servizio infrastrutturale con un runbook operativo.** Per ciascun servizio critico (DNS, DHCP, Email, Storage, Database, Web Server), creare e mantenere aggiornato un documento che descriva la configurazione, le procedure di manutenzione ordinaria, le procedure di emergenza e i contatti di escalation. Un runbook ben scritto riduce drasticamente il tempo di risoluzione degli incidenti e consente anche a personale meno esperto di intervenire efficacemente.

2. **Implementare il monitoraggio proattivo con soglie progressive (Warning e Critical).** Non attendere che un servizio si guasti per intervenire. Configurare un sistema di monitoraggio (Zabbix, Prometheus/Grafana, PRTG o equivalente) con almeno due livelli di soglia: Warning per il degrado iniziale che richiede attenzione pianificata, e Critical per le condizioni che richiedono intervento immediato. Ogni allarme deve avere una procedura di risposta associata.

3. **Automatizzare le operazioni ripetitive con script versionati.** Le attivita di manutenzione ricorrenti (pulizia dei record DNS stale, verifica delle code email, controllo della frammentazione degli indici) devono essere automatizzate con script PowerShell, Bash o Python. Questi script devono essere versionati in un repository Git, testati in ambiente di staging e schedulati tramite Task Scheduler, cron o un orchestratore come Ansible.

4. **Testare regolarmente i backup con ripristini effettivi.** Un backup non verificato e una speranza, non una garanzia. Pianificare test di ripristino mensili per i database critici e trimestrali per gli altri servizi. Misurare e documentare l'RTO (Recovery Time Objective) effettivo e confrontarlo con l'RTO dichiarato negli SLA. Se l'RTO effettivo supera quello contrattuale, adottare misure correttive immediate.

5. **Mantenere un inventario aggiornato delle dipendenze tra servizi.** I servizi infrastrutturali sono interdipendenti: il DNS e necessario per il funzionamento di email, web e database; il DHCP e necessario per la connettivita di rete; lo storage e necessario per tutti i servizi. Mappare queste dipendenze in un diagramma aggiornato consente di valutare correttamente l'impatto di un guasto e di pianificare le finestre di manutenzione senza causare interruzioni a cascata.

6. **Applicare il principio del minimo privilegio a tutti i servizi.** Ogni servizio deve operare con i permessi minimi necessari per svolgere la propria funzione. Gli account di servizio devono essere dedicati (un account per servizio), avere password complesse e ruotate periodicamente, e non devono mai essere utilizzati per accessi interattivi. I permessi sulle condivisioni di file, sui database e sui servizi web devono essere auditati trimestralmente.

7. **Pianificare finestre di manutenzione regolari e comunicarle agli stakeholder.** Stabilire un calendario di manutenzione mensile con finestre temporali predefinite (es. ogni terzo sabato del mese, dalle 02:00 alle 06:00). Comunicare il calendario a tutti gli stakeholder all'inizio di ogni trimestre e inviare un reminder specifico 48 ore prima di ogni sessione di manutenzione. Documentare ogni intervento eseguito.

8. **Gestire i certificati SSL/TLS con un inventario centralizzato e alert di scadenza.** Censire tutti i certificati in uso (web server, email, VPN, servizi interni) in un inventario che riporti il soggetto, l'emittente, la data di scadenza e il servizio associato. Configurare allarmi automatici a 90, 60, 30 e 7 giorni dalla scadenza. Dove possibile, implementare il rinnovo automatico con certbot o ACME. La scadenza di un certificato e una delle cause piu frequenti e piu evitabili di interruzione dei servizi.

9. **Implementare la ridondanza per ogni servizio critico.** Nessun servizio infrastrutturale dovrebbe avere un single point of failure. Il DNS deve avere almeno due server, il DHCP deve essere configurato in failover, le email devono utilizzare un DAG o un servizio cloud con SLA garantito, lo storage deve essere configurato in RAID con controller ridondanti, i database devono avere repliche sincrone o asincrone, e i web server devono essere bilanciati.

10. **Eseguire un audit di sicurezza trimestrale su tutti i servizi esposti.** Ogni trimestre, verificare che le configurazioni di sicurezza siano aggiornate: DNSSEC attivo e chiavi non scadute, SPF/DKIM/DMARC correttamente configurati, protocolli TLS aggiornati (disabilitare TLS 1.0 e 1.1), permessi di accesso ai servizi verificati, log di audit attivi e conservati per il periodo richiesto dalle normative. Utilizzare strumenti di vulnerability scanning per identificare configurazioni deboli o vulnerabilita note.

---

## Troubleshooting

### Problemi DNS

**Problema: Risoluzione DNS lenta o intermittente**
- **Sintomi:** le applicazioni impiegano diversi secondi per connettersi, timeout saltuari.
- **Diagnosi:**
  ```bash
  # Misurare il tempo di risoluzione
  dig azienda.it @dns-server +stats | grep "Query time"

  # Verificare la catena di risoluzione
  dig +trace azienda.it

  # Testare i forwarder
  dig azienda.it @8.8.8.8 +stats
  dig azienda.it @dns-server +stats
  ```
- **Cause comuni:** forwarder non raggiungibili, cache DNS piena, rete congestionata, server DNS sovraccarico.
- **Risoluzione:** verificare la connettivita verso i forwarder, svuotare la cache DNS (`rndc flush` su BIND, `Clear-DnsServerCache` su Windows), aumentare la dimensione della cache, verificare le risorse del server.

**Problema: Record DNS non aggiornati dopo modifica**
- **Sintomi:** il record e stato modificato ma i client continuano a risolvere il vecchio valore.
- **Diagnosi:**
  ```powershell
  # Verificare il TTL del record
  Resolve-DnsName -Name host.azienda.it -Type A -DnsOnly | Select-Object Name, TTL, IPAddress

  # Verificare su quale server il client sta risolvendo
  nslookup host.azienda.it
  ```
- **Cause comuni:** TTL elevato nella cache dei client o dei resolver intermedi, replica AD non completata.
- **Risoluzione:** attendere la scadenza del TTL, forzare lo svuotamento della cache client (`ipconfig /flushdns`), verificare lo stato della replica AD (`repadmin /replsummary`).

### Problemi DHCP

**Problema: I client non ricevono un indirizzo IP**
- **Sintomi:** i dispositivi si assegnano un indirizzo APIPA (169.254.x.x).
- **Diagnosi:**
  ```powershell
  # Verificare lo stato del servizio DHCP
  Get-Service DHCPServer

  # Verificare la disponibilita di indirizzi nello scope
  Get-DhcpServerv4ScopeStatistics -ScopeId "192.168.1.0"

  # Verificare se il DHCP relay e configurato sulla VLAN corretta
  # (il router/switch deve avere l'ip helper-address)
  ```
- **Cause comuni:** scope esaurito, servizio DHCP arrestato, DHCP relay non configurato sulla VLAN, conflitto con server DHCP rogue.
- **Risoluzione:** espandere lo scope o ridurre la durata dei lease, riavviare il servizio, configurare il DHCP relay, rilevare e disattivare server DHCP non autorizzati.

**Problema: Conflitti di indirizzi IP**
- **Sintomi:** messaggi di conflitto IP, connettivita intermittente.
- **Diagnosi:**
  ```powershell
  # Cercare conflitti nel log eventi
  Get-WinEvent -FilterHashtable @{LogName='System'; Id=4198,4199} -MaxEvents 10

  # Identificare il MAC address associato a un IP
  arp -a | findstr "192.168.1.105"
  ```
- **Cause comuni:** dispositivo con IP statico che confligge con il range DHCP, lease duplicato, riserva non configurata correttamente.
- **Risoluzione:** configurare le esclusioni nello scope DHCP per gli IP statici, eliminare il lease in conflitto, verificare le riserve.

### Problemi Email

**Problema: Email in uscita bloccate o rifiutate dal destinatario**
- **Sintomi:** NDR (Non-Delivery Report) con errori 550, 553, 554.
- **Diagnosi:**
  ```bash
  # Verificare SPF
  dig TXT azienda.it | grep "v=spf1"

  # Verificare DKIM
  dig TXT selector1._domainkey.azienda.it

  # Verificare DMARC
  dig TXT _dmarc.azienda.it

  # Verificare la reputazione dell'IP
  # Consultare: mxtoolbox.com/blacklists.aspx
  ```
- **Cause comuni:** IP del server email in una blacklist, SPF non configurato correttamente, DKIM non valido, DMARC con policy reject e allineamento fallito.
- **Risoluzione:** richiedere la rimozione dalla blacklist, correggere il record SPF, rigenerare le chiavi DKIM, verificare l'allineamento DMARC.

**Problema: Code di posta in crescita**
- **Sintomi:** ritardo nella consegna delle email, code con centinaia di messaggi.
- **Diagnosi:**
  ```powershell
  Get-Queue | Where-Object {$_.MessageCount -gt 50} | Format-Table Identity, MessageCount, LastError -AutoSize
  ```
- **Cause comuni:** server di destinazione non raggiungibile, errore DNS nella risoluzione MX, certificato scaduto sul connettore, disco pieno sul server.
- **Risoluzione:** verificare la connettivita verso il destinatario, verificare la risoluzione MX, rinnovare il certificato, liberare spazio su disco.

### Problemi Storage

**Problema: Prestazioni storage degradate**
- **Sintomi:** applicazioni lente, tempi di risposta elevati, utenti che lamentano lentezza nell'accesso ai file.
- **Diagnosi:**
  ```bash
  # Linux: verificare la latenza I/O
  iostat -xz 5 3
  # Attenzione a: await > 20ms, %util > 80%

  # Verificare lo stato RAID
  cat /proc/mdstat  # Linux software RAID
  # megacli -LDInfo -Lall -aALL  # controller hardware
  ```
- **Cause comuni:** disco in fase di rebuilding RAID, I/O saturo da un singolo processo, frammentazione del filesystem, disco in fase di guasto.
- **Risoluzione:** attendere il completamento del rebuild, identificare e limitare il processo che genera I/O eccessivo, deframmentare il filesystem, sostituire il disco in fase di guasto.

**Problema: Spazio su disco in esaurimento**
- **Sintomi:** allarmi di spazio, errori di scrittura, servizi che si arrestano.
- **Diagnosi:**
  ```bash
  # Linux
  df -h
  du -sh /* | sort -rh | head 10

  # Trovare file di grandi dimensioni
  find / -xdev -type f -size +500M -exec ls -lh {} \; 2>/dev/null | sort -k5 -rh | head 20
  ```
  ```powershell
  # Windows
  Get-PSDrive -PSProvider FileSystem | Select-Object Name, @{N='UsedGB';E={[math]::Round($_.Used/1GB,2)}}, @{N='FreeGB';E={[math]::Round($_.Free/1GB,2)}}
  ```
- **Cause comuni:** log non ruotati, backup locali non eliminati, file temporanei accumulati, crescita imprevista del database.
- **Risoluzione:** implementare la rotazione dei log, pulire i file temporanei, spostare i dati meno utilizzati su storage a costo inferiore, espandere il volume se necessario.

### Problemi Database

**Problema: Query lente e degrado prestazionale**
- **Sintomi:** applicazioni che rispondono lentamente, timeout sulle connessioni al database.
- **Diagnosi:**
  ```sql
  -- SQL Server: query attualmente in esecuzione
  SELECT
      r.session_id, r.status, r.command, r.wait_type,
      r.cpu_time, r.total_elapsed_time,
      SUBSTRING(t.text, r.statement_start_offset/2+1,
          (CASE WHEN r.statement_end_offset = -1 THEN LEN(CONVERT(nvarchar(max), t.text))*2
          ELSE r.statement_end_offset END - r.statement_start_offset)/2+1) AS query_text
  FROM sys.dm_exec_requests r
  CROSS APPLY sys.dm_exec_sql_text(r.sql_handle) t
  WHERE r.session_id > 50
  ORDER BY r.total_elapsed_time DESC;
  ```
- **Cause comuni:** indici frammentati o mancanti, statistiche obsolete, query non ottimizzate, lock e blocking, risorse hardware insufficienti.
- **Risoluzione:** ricostruire gli indici frammentati, aggiornare le statistiche, analizzare il piano di esecuzione delle query lente, identificare e risolvere i blocking, valutare l'aggiunta di risorse.

### Problemi Web Server

**Problema: Errori 502 Bad Gateway o 503 Service Unavailable**
- **Sintomi:** gli utenti ricevono pagine di errore, il sito non e raggiungibile.
- **Diagnosi:**
  ```bash
  # Nginx: verificare lo stato del backend
  curl -v http://backend-server:porta/health

  # Verificare i log di errore
  tail -50 /var/log/nginx/error.log

  # Verificare le connessioni attive
  ss -tlnp | grep nginx
  ss -tlnp | grep -E ":80|:443"
  ```
  ```powershell
  # IIS: verificare lo stato degli application pool
  Get-WebAppPoolState *

  # Verificare il log eventi
  Get-WinEvent -FilterHashtable @{LogName='System'; ProviderName='WAS'} -MaxEvents 20
  ```
- **Cause comuni:** application pool arrestato, backend non raggiungibile, risorse esaurite (RAM, connessioni), certificato scaduto.
- **Risoluzione:** riavviare l'application pool, verificare lo stato del backend, aumentare le risorse, rinnovare il certificato.

**Problema: Certificato SSL scaduto**
- **Sintomi:** i browser mostrano un avviso di sicurezza, le API restituiscono errori SSL.
- **Diagnosi:**
  ```bash
  # Verificare la scadenza del certificato
  echo | openssl s_client -connect www.azienda.it:443 -servername www.azienda.it 2>/dev/null | openssl x509 -noout -dates
  ```
- **Cause comuni:** mancato rinnovo automatico, errore nel job di certbot, certificato rinnovato ma non applicato al web server.
- **Risoluzione:** rinnovare il certificato (`certbot renew --force-renewal`), riavviare il web server per applicare il nuovo certificato, verificare che il job di rinnovo automatico sia funzionante e correttamente schedulato.

### Problemi Active Directory

**Problema: Replica AD fallita tra Domain Controller**
- **Sintomi:** utenti che non riescono ad autenticarsi su alcuni DC, password cambiate che non funzionano su tutti i DC, GPO non aggiornate.
- **Diagnosi:**
  ```powershell
  # Verifica degli errori di replica
  repadmin /replsummary
  repadmin /showrepl /errorsonly

  # Verifica degli eventi di errore
  Get-WinEvent -FilterHashtable @{LogName='Directory Service'; Level=2} -MaxEvents 20

  # Test completo della salute AD
  dcdiag /v /c /e
  ```
- **Cause comuni:** connettivita di rete interrotta tra i DC (firewall, routing), DNS non funzionante (la replica AD dipende dal DNS), tombstone lifetime superato (> 180 giorni di disconnessione), clock skew tra i DC.
- **Risoluzione:** verificare la connettivita di rete tra i DC (porte TCP/UDP per AD: 53, 88, 135, 389, 445, 464, 636, 3268, 3269, 49152-65535), verificare che il DNS funzioni correttamente, forzare la replica con `repadmin /replicate`, verificare la sincronizzazione temporale.

**Problema: Account lockout ripetuti (possibile attacco brute force)**
- **Sintomi:** utenti bloccati frequentemente, allarmi di sicurezza per tentativi di accesso multipli.
- **Diagnosi:**
  ```powershell
  # Identificare la sorgente dei lockout
  Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4740} -MaxEvents 20 |
      Select-Object TimeCreated, @{N='Account';E={$_.Properties[0].Value}}, @{N='CallerComputer';E={$_.Properties[1].Value}}

  # Utilizzare Account Lockout Tools di Microsoft per analisi approfondita
  # LockoutStatus.exe, EventCombMT.exe
  ```
- **Cause comuni:** credenziali cached obsolete (drive mappati, applicazioni, task schedulati), attacco brute force esterno (VPN, OWA), servizio con credenziali scadute.
- **Risoluzione:** identificare la sorgente dal campo CallerComputer, verificare i drive mappati e le applicazioni che utilizzano credenziali cached, verificare i servizi Windows con credenziali dell'utente, aggiornare le credenziali su tutti i punti di accesso.

### Problemi di Sincronizzazione Temporale

**Problema: Clock skew Kerberos — "Clock skew too great"**
- **Sintomi:** utenti non riescono ad autenticarsi, errori "clock skew too great" nei log.
- **Diagnosi:**
  ```powershell
  # Verificare lo scostamento temporale
  w32tm /stripchart /computer:DC01 /samples:3 /dataonly

  # Verificare la sorgente NTP
  w32tm /query /source
  w32tm /query /status
  ```
- **Cause comuni:** PDC Emulator configurato con una sorgente NTP non raggiungibile, firewall blocca UDP 123, VM con time sync disabilitato, battery CMOS esaurita su hardware fisico.
- **Risoluzione:** configurare il PDC Emulator con sorgenti NTP affidabili (`w32tm /config /manualpeerlist:... /syncfromflags:manual /reliable:yes /update`), verificare che UDP 123 sia aperto, verificare la configurazione VMware Tools / Hyper-V Integration Services per la sincronizzazione temporale delle VM.

### Problemi File Service

**Problema: Condivisione SMB non accessibile**
- **Sintomi:** gli utenti ricevono "Access Denied" o "Network path not found" quando accedono a una condivisione.
- **Diagnosi:**
  ```powershell
  # Verificare che la condivisione esista
  Get-SmbShare -Name "NomeCondivisione" -ErrorAction SilentlyContinue

  # Verificare i permessi sulla condivisione
  Get-SmbShareAccess -Name "NomeCondivisione"

  # Verificare i permessi NTFS
  Get-Acl "D:\Condivisioni\NomeCondivisione" | Select-Object -ExpandProperty Access

  # Verificare la connettivita SMB
  Test-NetConnection -ComputerName FileServer -Port 445
  ```
- **Cause comuni:** permessi NTFS non corretti (il permesso effettivo e l'intersezione piu restrittiva tra permesso di condivisione e permesso NTFS), firewall blocca la porta 445, server DNS non risolve il nome del file server, SPN duplicato per il file server.
- **Risoluzione:** verificare e correggere i permessi NTFS e di condivisione, verificare il firewall (porta TCP 445), verificare la risoluzione DNS, verificare gli SPN con `setspn -L hostname`.

### Problemi di Virtualizzazione

**Problema: VM con prestazioni degradate (CPU ready elevato)**
- **Sintomi:** applicazioni lente nella VM, CPU ready superiore al 5% nel monitoraggio dell'hypervisor.
- **Diagnosi:**
  ```powershell
  # VMware PowerCLI: verificare il CPU ready di una VM
  Get-Stat -Entity (Get-VM "NomeVM") -Stat "cpu.ready.summation" -Realtime -MaxSamples 30 |
      Measure-Object -Property Value -Average | Select-Object Average

  # Hyper-V: verificare l'utilizzo delle risorse
  Get-VM "NomeVM" | Select-Object CPUUsage, MemoryAssigned, MemoryDemand
  ```
- **Cause comuni:** host sovraccarico (troppe VM per le risorse disponibili), VM sovradimensionata in vCPU (NUMA crossing), contesa di risorse con altre VM, DRS non configurato o non bilanciato.
- **Risoluzione:** ridurre il numero di vCPU se l'utilizzo effettivo e basso (right-sizing), migrare la VM su un host meno carico, verificare la configurazione NUMA, abilitare DRS con bilanciamento automatico.

### Problemi PKI e Certificati

**Problema: CRL non raggiungibile — applicazioni che rifiutano i certificati**
- **Sintomi:** applicazioni restituiscono errori di validazione del certificato, smart card login fallisce, LDAPS non funziona.
- **Diagnosi:**
  ```powershell
  # Verificare che la CRL sia raggiungibile
  certutil -URL "http://pki.azienda.it/CertEnroll/Azienda-CA.crl"

  # Verificare la scadenza della CRL
  certutil -dump "http://pki.azienda.it/CertEnroll/Azienda-CA.crl" | Select-String "Next Update"
  ```
  ```bash
  # Da Linux
  curl -s "http://pki.azienda.it/CertEnroll/Azienda-CA.crl" | openssl crl -inform DER -text -noout | grep "Next Update"
  ```
- **Cause comuni:** server web che ospita la CRL non funzionante, CRL scaduta (il servizio CA non ha generato una nuova CRL), DNS non risolve il nome del CDP (CRL Distribution Point).
- **Risoluzione:** verificare il servizio CA e generare una nuova CRL (`certutil -CRL`), verificare il server web del CDP, verificare la risoluzione DNS del CDP.

---

## Esercizi
1. **Lab — DNS HA.** 2 server DNS authoritative + 2 recursive con NSD/Unbound; test failover.
2. **Stretch — PTP.** Setup PTP per sub-microsecond time accuracy in datacenter.
3. **Lab — AD Health Check.** Configurare uno script automatico che esegua `dcdiag`, `repadmin /replsummary` e verifichi i ruoli FSMO, con invio email in caso di errori.
4. **Lab — 802.1X Wired.** Configurare FreeRADIUS con autenticazione EAP-TLS su uno switch gestito. Verificare che un client senza certificato venga assegnato alla VLAN di quarantena.
5. **Lab — PKI Two-Tier.** Costruire una CA root offline e una Issuing CA online con AD CS. Emettere un certificato per un web server e configurare il rinnovo automatico.
6. **Lab — NTP Stratum.** Configurare un server Stratum 2 con chrony sincronizzato con 4 sorgenti pool.ntp.org. Misurare l'offset e il jitter dopo 24 ore.
7. **Lab — SMB Security.** Disabilitare SMB 1.0, abilitare la crittografia SMB su una condivisione, verificare che solo connessioni SMB 3.x siano accettate. Testare con `Get-SmbConnection` la versione negoziata.
8. **Lab — HCI Monitoring.** Configurare il monitoraggio di un cluster Proxmox VE o Nutanix con Prometheus e Grafana, includendo metriche di CPU, RAM, storage e latenza I/O.
9. **Stretch — DDI Integrato.** Configurare un ambiente DDI con Infoblox, EfficientIP o IPAM Windows Server. Verificare la coerenza tra DNS, DHCP e l'inventario IPAM dopo la creazione di 50 host.
10. **Stretch — IPv6 Dual-Stack.** Configurare un segmento di rete dual-stack (IPv4 + IPv6) con DHCPv6 e SLAAC. Verificare la risoluzione DNS per record A e AAAA.

## Auto-valutazione
1. DNS authoritative vs recursive: quali sono le differenze e quando si usa ciascuno?
2. NTP stratum: cosa significa e perche e importante avere una gerarchia coerente?
3. DHCP scope: come si dimensiona correttamente per evitare l'esaurimento degli indirizzi?
4. Quali sono i 5 ruoli FSMO in Active Directory e cosa succede se uno non e disponibile?
5. Perche NTLM deve essere dismesso e quali sono le alternative?
6. Qual e la differenza tra NFSv3 e NFSv4 in termini di sicurezza e gestione firewall?
7. Perche SMB 1.0 (CIFS) deve essere disabilitato e come si verifica che sia effettivamente disabilitato?
8. RADIUS vs TACACS+: quando si usa l'uno e quando l'altro?
9. Architettura PKI a due livelli: perche la Root CA deve essere offline?
10. Cosa significa "DDI" e perche la gestione integrata e superiore alla gestione separata di DNS, DHCP e IPAM?
11. Quali sono le metriche chiave per valutare la salute di un cluster HCI?
12. Come si verifica che la sincronizzazione temporale NTP funzioni correttamente in un dominio AD?

## Glossario locale
| Termine | Definizione |
|---|---|
| **DNS authoritative** | Server che ospita zona. |
| **DNS recursive** | Server che risolve per client. |
| **NTP** | Network Time Protocol (RFC 5905). Sincronizzazione temporale a precisione millisecondi. |
| **PTP** | Precision Time Protocol (IEEE 1588). Sincronizzazione sub-microsecondo. |
| **NTS** | Network Time Security (RFC 8915). Autenticazione crittografica per NTP. |
| **DHCP scope** | Range IP allocabili. |
| **Anycast** | Stesso IP da multipli location. |
| **Active Directory (AD)** | Servizio di directory Microsoft per autenticazione, autorizzazione e gestione risorse. |
| **LDAP** | Lightweight Directory Access Protocol. Protocollo per interrogare i servizi di directory. |
| **LDAPS** | LDAP over SSL/TLS (porta 636). Crittografa l'intero traffico LDAP. |
| **FSMO** | Flexible Single Master Operations. 5 ruoli critici in AD (Schema Master, Domain Naming Master, PDC Emulator, RID Master, Infrastructure Master). |
| **GPO** | Group Policy Object. Oggetto che definisce configurazioni e restrizioni per utenti e computer in AD. |
| **Kerberos** | Protocollo di autenticazione predefinito in AD. Richiede sincronizzazione temporale (tolleranza 5 min). |
| **NTLM** | NT LAN Manager. Protocollo di autenticazione legacy, vulnerabile ad attacchi pass-the-hash e relay. Da dismettere. |
| **NFS** | Network File System. Protocollo di condivisione file nativo per Unix/Linux (corrente: NFSv4.2, RFC 7862). |
| **SMB** | Server Message Block. Protocollo di condivisione file nativo per Windows (corrente: SMB 3.1.1). |
| **CIFS** | Common Internet File System. Nome obsoleto di SMB 1.0. Vulnerabile, da disabilitare. |
| **CUPS** | Common Unix Printing System. Sistema di stampa standard per Linux/macOS. |
| **IPP** | Internet Printing Protocol. Protocollo di stampa basato su HTTP, nativo in CUPS. |
| **HCI** | Hyper-Converged Infrastructure. Piattaforma che integra compute, storage e networking in un'unica soluzione software-defined. |
| **RADIUS** | Remote Authentication Dial-In User Service. Protocollo AAA per accesso alla rete (UDP 1812/1813). |
| **TACACS+** | Terminal Access Controller Access-Control System Plus. Protocollo AAA per amministrazione dispositivi di rete (TCP 49). |
| **802.1X** | Standard IEEE per autenticazione port-based su LAN e WLAN. |
| **EAP** | Extensible Authentication Protocol. Framework per il trasporto delle credenziali in 802.1X. |
| **NAC** | Network Access Control. Controllo dell'accesso alla rete con verifica della postura del dispositivo. |
| **PKI** | Public Key Infrastructure. Framework per la gestione dei certificati digitali. |
| **CA** | Certificate Authority. Entita che emette e gestisce i certificati digitali. |
| **CRL** | Certificate Revocation List. Elenco dei certificati revocati dalla CA. |
| **OCSP** | Online Certificate Status Protocol. Verifica in tempo reale dello stato di revoca di un certificato. |
| **ACME** | Automatic Certificate Management Environment (RFC 8555). Protocollo per l'automazione del ciclo di vita dei certificati. |
| **HSM** | Hardware Security Module. Dispositivo dedicato alla protezione delle chiavi crittografiche. |
| **IPAM** | IP Address Management. Gestione centralizzata degli indirizzi IP. |
| **DDI** | DNS, DHCP, IPAM. Gestione integrata dei tre servizi fondamentali di rete. |
| **Stratum** | Livello gerarchico NTP. Stratum 0 = sorgente di riferimento, Stratum 1 = server direttamente connesso. |
| **GNSS** | Global Navigation Satellite System. Sistemi di navigazione satellitare (GPS, Galileo, GLONASS, BeiDou). |
| **Dual-stack** | Configurazione di rete che supporta contemporaneamente IPv4 e IPv6. |
| **SLAAC** | Stateless Address Autoconfiguration. Meccanismo IPv6 per l'autoconfigurazione degli indirizzi senza server DHCP. |
