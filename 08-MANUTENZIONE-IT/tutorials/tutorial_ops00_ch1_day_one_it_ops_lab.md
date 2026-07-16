# Tutorial: Il Primo Giorno in IT Operations — Hands-On Lab

> **Documento di riferimento:** Nuovo contenuto — nessun file sorgente
> **Dominio:** 00 — Orientamento e Setup dell'Ambiente
> **Ambito:** Introduzione al campo IT Operations; configurazione dell'ambiente lab che verrà usato in tutti i tutorial del corso
> **Durata lab:** 4–6 ore (due sessioni da 2–3 ore)
> **Livello:** Principiante assoluto — nessuna conoscenza IT richiesta
> **Prerequisiti:** Saper usare un PC Windows; almeno 16 GB di RAM e 100 GB liberi su SSD
> **Ambiente:** PC personale con VirtualBox — completamente isolato da internet durante gli esercizi

---

## Indice

- [Setup dell'Ambiente Lab](#setup-dellambiente-lab)
- [Part A — Fondamenti: Che Cos'è l'IT Operations](#part-a--fondamenti-che-cosè-lit-operations)
  - [A1: L'IT Operations come Servizio Pubblico Interno](#concetto-a1-lit-operations-come-servizio-pubblico-interno)
  - [A2: I Cinque Tipi di Manutenzione IT](#concetto-a2-i-cinque-tipi-di-manutenzione-it)
  - [A3: Perché Esistono i Framework (ITIL)](#concetto-a3-perché-esistono-i-framework-itil)
  - [A4: La Giornata Tipo di un IT Operations Engineer](#concetto-a4-la-giornata-tipo-di-un-it-operations-engineer)
  - [A5: Cos'è una Virtual Machine — Spiegato a Tre Livelli](#concetto-a5-cosè-una-virtual-machine--spiegato-a-tre-livelli)
  - [A6: VirtualBox — Il Nostro Hypervisor Gratuito](#concetto-a6-virtualbox--il-nostro-hypervisor-gratuito)
  - [A7: Le Tre VM del Nostro Lab — Perché Tre?](#concetto-a7-le-tre-vm-del-nostro-lab--perché-tre)

---

## Setup dell'Ambiente Lab

Prima di toccare qualsiasi concetto teorico, prepariamo il terreno. In IT Operations si dice spesso: *"un ambiente non documentato è un ambiente non esistente."* Configureremo le tre macchine virtuali del corso e capiremo esattamente cosa stiamo costruendo e perché.

### Requisiti Hardware

Il tuo PC fisico — chiamato **host** in gergo tecnico — deve soddisfare questi requisiti per ospitare le tre VM contemporaneamente senza bloccarsi.

| Componente | Minimo (funziona, ma lento) | Raccomandato (esperienza fluida) |
|------------|-------------------------------|----------------------------------|
| **CPU** | 4 core fisici, con supporto virtualizzazione (VT-x o AMD-V attivo nel BIOS) | 8 core fisici o più (Intel Core i7/i9 o AMD Ryzen 7/9) |
| **RAM** | 16 GB | 32 GB |
| **Disco** | 100 GB liberi su qualsiasi disco (anche HDD) | 150 GB liberi su SSD NVMe |
| **Rete** | Non necessaria durante gli esercizi (ambiente isolato) | Non necessaria durante gli esercizi (ambiente isolato) |
| **Sistema Operativo Host** | Windows 10 64-bit (versione 1903 o successiva) | Windows 10/11 64-bit, aggiornato |

> **Come verificare VT-x/AMD-V:** Apri Task Manager (`Ctrl+Shift+Esc`), scheda **Performance**, clicca su **CPU**. In basso a destra leggi **Virtualization: Enabled**. Se leggi *Disabled*, devi entrare nel BIOS/UEFI del tuo PC e abilitare la virtualizzazione prima di procedere.

---

### Topologia del Lab — Diagramma ASCII

Il lab è composto da tre VM collegate tra loro tramite una rete **host-only** di VirtualBox. Questa rete esiste solo all'interno del tuo PC: le VM possono comunicare tra loro e con il tuo PC fisico, ma **non possono raggiungere internet**. Questo è intenzionale: durante gli esercizi lavoriamo in un ambiente sicuro e isolato.

```
┌─────────────────────────────────────────────────────────────────┐
│                        PC HOST (il tuo PC fisico)               │
│                        Windows 10/11                            │
│                                                                 │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │              VirtualBox Host-Only Network                │  │
│   │              Subnet: 192.168.56.0/24                     │  │
│   │              Gateway host: 192.168.56.1                  │  │
│   │                                                          │  │
│   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │  │
│   │  │   VM1        │  │   VM2        │  │   VM3        │   │  │
│   │  │ Windows      │  │ Ubuntu       │  │ Windows 10   │   │  │
│   │  │ Server 2022  │  │ Server 22.04 │  │              │   │  │
│   │  │              │  │              │  │              │   │  │
│   │  │ DC-LAB-01    │  │SRV-LINUX-01  │  │ WKS-LAB-01   │   │  │
│   │  │              │  │              │  │              │   │  │
│   │  │192.168.56.10 │  │192.168.56.20 │  │192.168.56.30 │   │  │
│   │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │  │
│   │         │                 │                  │           │  │
│   │         └─────────────────┴──────────────────┘           │  │
│   │                    eth0 / vboxnet0                        │  │
│   └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

Legenda:
  VM1 = Domain Controller + DNS + DHCP (server Windows)
  VM2 = Server di monitoraggio e servizi Linux
  VM3 = Workstation utente/amministratore
  ↔  = Comunicazione bidirezionale tramite rete host-only
```

---

### Specifiche delle Tre VM

| # | Nome VM | Sistema Operativo | Hostname | IP Statico | RAM Assegnata | Disco Virtuale | Ruolo nel Lab |
|---|---------|-------------------|----------|------------|---------------|---------------|---------------|
| VM1 | Windows Server 2022 | Windows Server 2022 Standard (Desktop Experience) | `DC-LAB-01` | `192.168.56.10` | 4 GB | 60 GB | Domain Controller, DNS, DHCP, File Server |
| VM2 | Ubuntu Server 22.04 | Ubuntu Server 22.04.4 LTS | `SRV-LINUX-01` | `192.168.56.20` | 2 GB | 30 GB | Monitoring, servizi Linux, Zabbix |
| VM3 | Windows 10 | Windows 10 Pro 64-bit | `WKS-LAB-01` | `192.168.56.30` | 4 GB | 40 GB | Workstation amministratore / utente simulato |

> **Nota sulle ISO:** Per questo lab puoi usare le versioni di valutazione gratuite a 180 giorni di Windows Server 2022 (scaricabili dal sito Microsoft Evaluation Center) e Ubuntu Server 22.04 (scaricabile da ubuntu.com). Windows 10 può essere installato con la licenza che già hai sul tuo PC o con la versione di valutazione.

---

### Script PowerShell — Configurazione IP Statico su VM1 e VM3

Esegui questo script su **VM1 (DC-LAB-01)** e poi, con le modifiche indicate nei commenti, su **VM3 (WKS-LAB-01)**. Apri PowerShell come **Amministratore** all'interno della VM.

```powershell
# =============================================================================
# Script: Set-StaticIP-Lab.ps1
# Scopo:  Configurare IP statico, subnet mask, gateway e DNS su una VM Windows
# Uso:    Modificare le variabili nella sezione CONFIGURAZIONE prima di eseguire
# =============================================================================

# ---------- SEZIONE CONFIGURAZIONE — modifica questi valori ----------

# Per VM1 (DC-LAB-01):
$NomeMacchina   = "DC-LAB-01"
$IndirizzIP     = "192.168.56.10"
$SubnetPrefix   = 24                    # /24 equivale a 255.255.255.0
$Gateway        = "192.168.56.1"        # IP del gateway VirtualBox host-only
$DNS1           = "192.168.56.10"       # VM1 sarà il proprio DNS (dopo aver installato AD DS)
$DNS2           = "8.8.8.8"            # DNS Google come fallback (solo per aggiornamenti iniziali)

# Per VM3 (WKS-LAB-01) — modifica queste righe e commenta quelle sopra:
# $NomeMacchina = "WKS-LAB-01"
# $IndirizzIP   = "192.168.56.30"
# $SubnetPrefix = 24
# $Gateway      = "192.168.56.1"
# $DNS1         = "192.168.56.10"      # Puntiamo al DC come DNS primario
# $DNS2         = "8.8.8.8"

# ---------- FINE SEZIONE CONFIGURAZIONE ----------

# Identificare l'interfaccia di rete corretta (quella collegata alla rete host-only)
Write-Host "Ricerca interfacce di rete disponibili..." -ForegroundColor Cyan
Get-NetAdapter | Format-Table Name, InterfaceDescription, Status, MacAddress

# Selezionare l'adattatore attivo (di norma "Ethernet" o "Ethernet 2" nelle VM VirtualBox)
$Adattatore = Get-NetAdapter | Where-Object { $_.Status -eq "Up" } | Select-Object -First 1

if (-not $Adattatore) {
    Write-Error "Nessun adattatore di rete attivo trovato. Verifica la configurazione di rete in VirtualBox."
    exit 1
}

Write-Host "Adattatore selezionato: $($Adattatore.Name) — $($Adattatore.InterfaceDescription)" -ForegroundColor Green

# Rimuovere eventuali configurazioni IP esistenti (DHCP o IP statico precedente)
Write-Host "Rimozione configurazione IP esistente..." -ForegroundColor Yellow
Remove-NetIPAddress -InterfaceAlias $Adattatore.Name -Confirm:$false -ErrorAction SilentlyContinue
Remove-NetRoute -InterfaceAlias $Adattatore.Name -Confirm:$false -ErrorAction SilentlyContinue

# Assegnare il nuovo IP statico
Write-Host "Configurazione IP statico: $IndirizzIP/$SubnetPrefix" -ForegroundColor Cyan
New-NetIPAddress `
    -InterfaceAlias $Adattatore.Name `
    -IPAddress $IndirizzIP `
    -PrefixLength $SubnetPrefix `
    -DefaultGateway $Gateway | Out-Null

# Configurare i server DNS
Write-Host "Configurazione DNS: primario=$DNS1, secondario=$DNS2" -ForegroundColor Cyan
Set-DnsClientServerAddress `
    -InterfaceAlias $Adattatore.Name `
    -ServerAddresses $DNS1, $DNS2

# Rinominare il computer (richiede riavvio per avere effetto)
Write-Host "Rinomina macchina in '$NomeMacchina'..." -ForegroundColor Cyan
Rename-Computer -NewName $NomeMacchina -Force -ErrorAction SilentlyContinue

# Verifica finale della configurazione applicata
Write-Host "`n=== CONFIGURAZIONE APPLICATA ===" -ForegroundColor Green
Get-NetIPAddress -InterfaceAlias $Adattatore.Name | Format-Table IPAddress, PrefixLength, AddressFamily
Get-DnsClientServerAddress -InterfaceAlias $Adattatore.Name | Format-Table InterfaceAlias, ServerAddresses

Write-Host "`nConfigurazione completata. Riavvia la VM per applicare il nuovo hostname." -ForegroundColor Green
Write-Host "Comando riavvio: Restart-Computer -Force" -ForegroundColor Yellow
```

---

### Script Bash — Configurazione IP Statico su VM2 (Ubuntu Server 22.04)

Ubuntu Server 22.04 usa **Netplan** per la configurazione di rete. Netplan è un sistema che legge file YAML e li traduce nella configurazione di rete effettiva del sistema.

Accedi a VM2 (`SRV-LINUX-01`) e lancia i comandi seguenti **come root o con sudo**.

```bash
#!/usr/bin/env bash
# =============================================================================
# Script: configure-static-ip.sh
# Scopo:  Configurare IP statico su Ubuntu Server 22.04 tramite Netplan
# Uso:    sudo bash configure-static-ip.sh
# =============================================================================

set -euo pipefail   # Interrompi in caso di errore, variabili non definite, o pipe fallite

# ---------- VARIABILI DI CONFIGURAZIONE ----------
IP_ADDRESS="192.168.56.20"
PREFIX_LENGTH="24"                  # /24 = 255.255.255.0
GATEWAY="192.168.56.1"
DNS_PRIMARY="192.168.56.10"        # VM1 sarà il DNS del dominio
DNS_SECONDARY="8.8.8.8"
HOSTNAME_NEW="SRV-LINUX-01"
NETPLAN_FILE="/etc/netplan/01-lab-static.yaml"
# ---------- FINE VARIABILI ----------

# Verificare di essere root
if [[ "$EUID" -ne 0 ]]; then
    echo "[ERRORE] Questo script deve essere eseguito come root (usa: sudo bash $0)"
    exit 1
fi

echo "[INFO] Identificazione dell'interfaccia di rete..."
# Trovare il nome dell'interfaccia di rete principale (di solito enp0s3 nelle VM VirtualBox)
INTERFACE=$(ip link show | awk '/^[0-9]+: / {print $2}' | grep -v '^lo:' | head -1 | tr -d ':')

if [[ -z "$INTERFACE" ]]; then
    echo "[ERRORE] Nessuna interfaccia di rete trovata. Controlla con: ip link show"
    exit 1
fi

echo "[INFO] Interfaccia selezionata: $INTERFACE"

# Disabilitare tutti i file Netplan esistenti per evitare conflitti
echo "[INFO] Backup e disabilitazione configurazioni Netplan esistenti..."
for existing_config in /etc/netplan/*.yaml; do
    if [[ "$existing_config" != "$NETPLAN_FILE" ]]; then
        mv "$existing_config" "${existing_config}.bak"
        echo "[INFO] Backup: ${existing_config} -> ${existing_config}.bak"
    fi
done

# Creare il nuovo file di configurazione Netplan
echo "[INFO] Creazione configurazione Netplan in $NETPLAN_FILE..."
cat > "$NETPLAN_FILE" << EOF
# Configurazione Netplan — Generato da configure-static-ip.sh
# Lab IT Operations — SRV-LINUX-01
network:
  version: 2
  renderer: networkd
  ethernets:
    ${INTERFACE}:
      dhcp4: false
      dhcp6: false
      addresses:
        - ${IP_ADDRESS}/${PREFIX_LENGTH}
      routes:
        - to: default
          via: ${GATEWAY}
      nameservers:
        addresses:
          - ${DNS_PRIMARY}
          - ${DNS_SECONDARY}
        search:
          - lab.local
EOF

# Impostare permessi corretti (Netplan richiede 600 per i file di configurazione)
chmod 600 "$NETPLAN_FILE"
echo "[INFO] Permessi file impostati a 600 (richiesto da Netplan)"

# Applicare la configurazione
echo "[INFO] Applicazione configurazione Netplan..."
netplan generate
netplan apply

# Configurare l'hostname
echo "[INFO] Impostazione hostname: $HOSTNAME_NEW"
hostnamectl set-hostname "$HOSTNAME_NEW"

# Aggiungere la voce /etc/hosts per la risoluzione locale
if ! grep -q "$HOSTNAME_NEW" /etc/hosts; then
    echo "${IP_ADDRESS}    ${HOSTNAME_NEW}.lab.local    ${HOSTNAME_NEW}" >> /etc/hosts
fi

# Verifica finale
echo ""
echo "=== VERIFICA CONFIGURAZIONE APPLICATA ==="
echo "--- Interfacce di rete ---"
ip addr show "$INTERFACE"
echo ""
echo "--- Tabella di routing ---"
ip route show
echo ""
echo "--- DNS configurato ---"
resolvectl status "$INTERFACE" 2>/dev/null || cat /etc/resolv.conf
echo ""
echo "--- Hostname ---"
hostnamectl
echo ""
echo "[OK] Configurazione completata con successo."
echo "[INFO] Nessun riavvio necessario — la configurazione è già attiva."
```

Rendi lo script eseguibile e lancia:

```bash
# All'interno di VM2
chmod +x configure-static-ip.sh
sudo bash configure-static-ip.sh
```

---

### Verifica della Connettività tra le VM

Dopo aver configurato le tre VM, esegui questi comandi di verifica per confermare che la rete funzioni correttamente.

**Da VM3 (WKS-LAB-01) — PowerShell:**

```powershell
# Test connettività verso VM1 (Domain Controller)
Test-NetConnection -ComputerName 192.168.56.10 -InformationLevel Detailed

# Test connettività verso VM2 (Server Linux)
Test-NetConnection -ComputerName 192.168.56.20 -InformationLevel Detailed

# Ping classico verso tutte e tre le macchine
ping 192.168.56.10 -n 4    # VM1
ping 192.168.56.20 -n 4    # VM2
ping 192.168.56.30 -n 4    # VM3 stessa (loopback verso se stesso)

# Verifica che il nome DNS si risolva (solo dopo aver configurato Active Directory)
Resolve-DnsName -Name DC-LAB-01.lab.local -Server 192.168.56.10
```

**Da VM2 (SRV-LINUX-01) — Bash:**

```bash
# Ping verso VM1
ping -c 4 192.168.56.10

# Ping verso VM3
ping -c 4 192.168.56.30

# Traceroute per vedere il percorso dei pacchetti
traceroute 192.168.56.10

# Verifica che le porte base siano raggiungibili (richiede nmap o nc)
nc -zv 192.168.56.10 445   # SMB — porta File Sharing Windows
nc -zv 192.168.56.10 389   # LDAP — porta Active Directory
```

**Da VM1 (DC-LAB-01) — PowerShell:**

```powershell
# Ping verso VM2
ping 192.168.56.20 -n 4

# Ping verso VM3
ping 192.168.56.30 -n 4

# Verifica che tutte e tre le macchine siano visibili nella rete
Get-NetNeighbor | Where-Object { $_.IPAddress -like "192.168.56.*" }
```

> **Risultato atteso:** Tutti i ping devono rispondere senza perdita di pacchetti (0% loss). Se un ping fallisce, controlla che la VM di destinazione sia accesa e che l'adattatore di rete in VirtualBox sia impostato su **Host-Only Adapter** (non NAT).

---

## Part A — Fondamenti: Che Cos'è l'IT Operations

Questa sezione non richiede di toccare il computer. Leggi con calma, senza fretta. Ogni concetto che capirai qui ti renderà molto più efficace in tutto il resto del corso.

---

### Concetto A1: L'IT Operations come Servizio Pubblico Interno

#### Analogia

Immagina il tuo comune. Il comune non produce automobili, non vende vestiti, non costruisce ponti per guadagno. Eppure senza il comune la città non funziona: niente acqua corrente, niente elettricità, niente strade asfaltate, niente raccolta rifiuti. I dipendenti del comune non sono "il cuore del business" — ma se smettono di lavorare un solo giorno, tutta la città si accorge immediatamente della loro assenza.

L'IT Operations è esattamente questo per un'azienda moderna: è il comune dell'azienda.

#### Spiegazione Tecnica

**IT Operations** (spesso abbreviato *IT Ops*) è la funzione aziendale responsabile della gestione, manutenzione e disponibilità continua di tutta l'infrastruttura tecnologica che permette all'azienda di operare. Questa infrastruttura comprende:

- **Server:** i computer "potenti" che erogano servizi a tutti gli altri
- **Rete:** i cavi, gli switch, i router, i firewall che collegano tutto
- **Workstation:** i PC dei dipendenti
- **Applicazioni:** i software usati per il lavoro (ERP, CRM, email, gestionale, ecc.)
- **Storage:** i sistemi dove vengono conservati i dati dell'azienda
- **Backup e Disaster Recovery:** i meccanismi per non perdere i dati in caso di guasto
- **Sicurezza:** i sistemi che proteggono l'azienda da attacchi e violazioni
- **Monitoraggio:** gli strumenti che controllano che tutto funzioni correttamente in ogni momento

Senza IT Ops un'azienda moderna si ferma in poche ore. Non c'è email. Non c'è accesso ai file condivisi. I commessi non riescono ad aprire i registri di cassa. I contabili non possono emettere fatture. I magazzinieri non vedono lo stock. I venditori non aprono il CRM. Il fenomeno è esattamente quello di una città senza corrente elettrica: le persone ci sono, le competenze ci sono, ma non si riesce a fare nulla.

**Cosa gestisce concretamente un team IT Ops:**

| Area | Esempi Concreti |
|------|----------------|
| **Server Management** | Installare aggiornamenti, monitorare le prestazioni, gestire i servizi (Active Directory, DNS, DHCP) |
| **Network Operations** | Configurare switch e router, gestire firewall, analizzare traffico di rete |
| **Endpoint Management** | Distribuire software sui PC degli utenti, gestire antivirus, applicare policy di sicurezza |
| **Service Desk** | Rispondere ai ticket degli utenti, risolvere problemi di primo/secondo livello |
| **Backup & Recovery** | Eseguire backup pianificati, testare i ripristini, gestire il disaster recovery |
| **Monitoring & Alerting** | Configurare sistemi di monitoring (Zabbix, Nagios, PRTG), ricevere e gestire gli alert |
| **Change Management** | Pianificare e documentare ogni modifica all'infrastruttura per minimizzare i rischi |
| **Asset Management** | Tenere traccia di ogni dispositivo hardware e software presente in azienda |

#### Perché Mi Interessa?

Capire che l'IT Ops è un **servizio interno** — non un reparto "di supporto secondario" — è fondamentale per il tuo atteggiamento professionale. Quando un server di posta si ferma alle 8:30 di mattina, cento dipendenti smettono di lavorare in attesa che tu lo risolva. La pressione è reale, il costo per l'azienda è reale (ogni ora di downtime ha un costo calcolabile in euro), e il tuo lavoro ha un impatto diretto misurabile sull'intera organizzazione.

Questo non deve spaventarti — deve motivarti. L'IT Operations è uno dei campi dove ogni giorno puoi vedere chiaramente il risultato del tuo lavoro.

---

### Concetto A2: I Cinque Tipi di Manutenzione IT

#### Analogia di Contesto

La manutenzione IT non è una sola cosa. Così come in medicina esistono diversi tipi di cure — dalla visita di routine all'intervento d'urgenza — in IT esistono cinque tipi distinti di manutenzione, ciascuno con uno scopo preciso, una pianificazione diversa e strumenti differenti.

#### I Cinque Tipi, con Analogia, Spiegazione e Importanza

---

##### Manutenzione Preventiva

**Analogia — Visita Medica Annuale:**
Il tuo medico ti chiede di venire ogni anno per una visita di routine, anche se ti senti perfettamente bene. Misura pressione, glicemia, colesterolo. Non stai male adesso — ma la visita serve a rilevare segnali deboli prima che diventino problemi gravi. Se salti le visite per anni, il problema arriva lo stesso, ma quando lo scopri potrebbe essere troppo tardi per un intervento semplice.

**Spiegazione Tecnica:**
La manutenzione preventiva IT è l'insieme di attività pianificate e ricorrenti eseguite *prima* che un guasto si verifichi, con l'obiettivo di ridurre la probabilità di guasto e prolungare la vita dei sistemi.

Esempi concreti:
- Applicare patch di sicurezza mensili ai server (Microsoft Patch Tuesday)
- Pulire fisicamente i rack server dalla polvere ogni 6 mesi
- Verificare lo stato dei dischi con `SMART` ogni settimana
- Controllare i log di sistema alla ricerca di warning ricorrenti
- Verificare la capacità dello storage e fare previsioni di crescita
- Sostituire l'UPS (gruppo di continuità) dopo 3–5 anni anche se funziona ancora

**Strumenti Usati:** Zabbix (monitoring), Windows Update / WSUS (patch), script PowerShell/Bash pianificati con Task Scheduler o cron, checklist documentate nel sistema ITSM (es. GLPI).

**Perché Mi Interessa?**
La manutenzione preventiva è la differenza tra un IT Ops professionista e uno "spegni-incendi". Chi non la fa bene passa il 90% del tempo a risolvere emergenze che avrebbe potuto evitare. Chi la fa bene dorme tranquillo — e il management lo sa e lo rispetta.

---

##### Manutenzione Correttiva

**Analogia — Pronto Soccorso:**
Ti rompi un braccio. Non puoi pianificarlo, non puoi rimandarlo, non puoi ignorarlo. Vai al pronto soccorso e il problema viene risolto nell'immediato, con l'obiettivo prioritario di ripristinare la funzionalità nel minor tempo possibile.

**Spiegazione Tecnica:**
La manutenzione correttiva è l'intervento eseguito *dopo* che un guasto si è verificato, con l'obiettivo di ripristinare il servizio nel minor tempo possibile. In ITIL questa fase è parte della gestione degli **Incident** (incidenti).

Esempi concreti:
- Un server si riavvia inaspettatamente alle 3 di notte → tu ricevi l'alert da Zabbix e ti connetti in VPN per diagnosticare e risolvere
- Un disco si guasta in un array RAID → vai fisicamente nel datacenter a sostituirlo
- Un'applicazione smette di rispondere → riavvii il servizio, identifichi la causa, ripristini la normale operatività
- Un account utente viene bloccato dopo troppi tentativi sbagliati → lo sblocchi e verifichi perché è successo

**Strumenti Usati:** Sistema di ticketing (GLPI, ServiceNow, Jira Service Management), monitoring con alert (Zabbix, PagerDuty), accesso remoto (RDP, SSH), log analysis.

**Perché Mi Interessa?**
La manutenzione correttiva è inevitabile — nessun sistema è immortale. Ma la differenza tra un buon IT Ops e un ottimo IT Ops sta nel **tempo di risposta e nel tempo di risoluzione**. Questi due valori si chiamano **MTTR** (Mean Time To Recovery) e vengono misurati da tutti i team professionali. Più basso è il tuo MTTR, più sei bravo.

---

##### Manutenzione Predittiva

**Analogia — Analisi del Sangue Preventiva:**
Il tuo medico analizza i valori del sangue e nota che il tuo colesterolo LDL è in lenta crescita negli ultimi tre anni. Non sei malato oggi, ma la traiettoria indica che senza intervento tra cinque anni avrai problemi cardiaci. Il medico agisce ora — con dieta, farmaci leggeri, esercizio — per cambiare la traiettoria prima che il problema si manifesti.

**Spiegazione Tecnica:**
La manutenzione predittiva IT usa i dati storici e le tendenze per prevedere quando un sistema potrebbe guastarsi, intervenendo prima che il guasto si verifichi. Si basa su tecniche di analisi dei trend (*trend analysis*), machine learning applicato all'infrastruttura, e correlazione di metriche nel tempo.

Esempi concreti:
- Il monitoring mostra che lo spazio disco libero su un server si riduce di 2 GB al giorno → tra 30 giorni il disco sarà pieno → pianifichi l'espansione tra due settimane
- L'analisi SMART di un disco mostra che il numero di "reallocated sectors" aumenta ogni settimana → il disco sta degradando → lo sostituisci prima che si guasti
- Le prestazioni di un server SQL peggiorano lentamente ogni venerdì pomeriggio → analizzi la causa (batch notturno mal pianificato) e intervieni
- La memoria RAM di un server mostra picchi sempre più frequenti → prevedi un problema di leak di memoria nell'applicazione → apri un ticket al team di sviluppo

**Strumenti Usati:** Zabbix (baseline + trend), Grafana (visualizzazione trend), script Python per analisi dei log, strumenti SMART per dischi (`smartctl`).

**Perché Mi Interessa?**
La manutenzione predittiva è il livello di maturità più alto nell'IT Ops tradizionale. I team che la praticano sistematicamente riescono a prevenire la maggior parte dei guasti importanti e vengono considerati dal management come un asset strategico, non come un costo da ridurre.

---

##### Manutenzione Adattiva

**Analogia — Cambiare Farmaco per Nuova Normativa:**
Il tuo medico ti prescriveva un certo farmaco da cinque anni. Una nuova direttiva ministeriale stabilisce che quel principio attivo deve essere sostituito con uno nuovo, più sicuro secondo le più recenti ricerche. Il medico non cambia il farmaco perché sei malato — cambia perché il contesto esterno (la normativa) è cambiato e il sistema di cura deve adattarsi.

**Spiegazione Tecnica:**
La manutenzione adattiva è l'insieme di modifiche apportate ai sistemi IT non per correggere guasti o migliorare prestazioni, ma per adattarsi a cambiamenti **esterni** all'infrastruttura stessa: nuove normative, nuovi requisiti di compliance, aggiornamenti del sistema operativo imposti dal vendor, cambiamenti nei sistemi con cui l'infrastruttura si interfaccia.

Esempi concreti:
- Microsoft termina il supporto a Windows Server 2012 R2 → migri tutti i server a Windows Server 2022 non perché siano rotti, ma perché il vendor non rilascerà più patch di sicurezza
- Il GDPR entra in vigore → adatti i sistemi di logging per rispettare i requisiti di data retention e anonimizzazione
- Un fornitore esterno cambia le API del proprio servizio dalla versione 1 alla versione 2 → aggiorni tutti gli script di integrazione
- La normativa PCI-DSS richiede TLS 1.2 minimo → disabiliti TLS 1.0 e 1.1 su tutti i server web

**Perché Mi Interessa?**
L'IT Ops non vive in un vuoto. Il mondo cambia, le normative cambiano, i vendor abbandonano i vecchi sistemi. Un professionista IT Ops deve tenere traccia di queste scadenze esterne — fine vita dei sistemi operativi, fine supporto dei vendor, scadenze compliance — e pianificare le migrazioni per tempo, non all'ultimo momento.

---

##### Manutenzione Perfettiva

**Analogia — Fare Palestra da Sani:**
Non sei malato, non hai subito un infortunio, nessuno ti ha detto di farlo. Ma inizi ad andare in palestra regolarmente per essere in forma migliore, avere più energia, dormire meglio, prevenire problemi futuri. Non c'è un problema da risolvere — c'è un livello da alzare.

**Spiegazione Tecnica:**
La manutenzione perfettiva è l'ottimizzazione e il miglioramento dei sistemi IT che funzionano correttamente, con l'obiettivo di migliorare le prestazioni, la manutenibilità, la sicurezza o l'efficienza operativa — senza che ci sia stato alcun guasto o obbligo esterno.

Esempi concreti:
- Riorganizzare e documentare gli script di automazione che si sono accumulati negli anni in modo disordinato
- Ottimizzare le query SQL lente di un database che funziona ma impiega 10 secondi dove potrebbe impiegare 0.5 secondi
- Aggiungere dashboard di monitoring più dettagliati a un sistema già monitorato, per avere visibilità migliore
- Migrare un processo manuale ripetitivo (es. creazione account utenti) a uno script automatizzato
- Aggiungere la documentazione mancante a procedure che esistono solo nella testa delle persone

**Perché Mi Interessa?**
La manutenzione perfettiva è quella che separa i team eccellenti dai team mediocri. Un sistema che "funziona" ma è mal documentato, pieno di script illeggibili, con query lente e processi manuali, è un sistema che prima o poi genererà problemi gravi. Investire regolarmente in miglioramenti incrementali è il modo con cui i team professionali evitano il debito tecnico.

---

#### Tabella Riassuntiva dei Cinque Tipi

| Tipo | Trigger | Obiettivo | Pianificazione | Esempio Concreto |
|------|---------|-----------|---------------|-----------------|
| **Preventiva** | Pianificazione periodica | Evitare guasti futuri | Programmata (settimanale/mensile) | Applicare patch mensili |
| **Correttiva** | Guasto già avvenuto | Ripristinare il servizio | Non pianificabile (reattiva) | Sostituire disco guasto |
| **Predittiva** | Trend negativi nei dati | Anticipare guasti imminenti | Basata su dati (continua) | Espandere storage prima che si riempia |
| **Adattiva** | Cambio esterno (normativa, vendor) | Mantenere compatibilità | Determinata da eventi esterni | Migrare da TLS 1.0 a TLS 1.2 |
| **Perfettiva** | Volontà di miglioramento | Migliorare qualità/efficienza | Pianificabile (roadmap) | Automatizzare processo manuale |

---

### Concetto A3: Perché Esistono i Framework (ITIL)

#### Analogia

Pensa alla differenza tra cucinare a casa e gestire una cucina industriale di un ristorante stellato.

A casa, cucini ad istinto. Metti un po' di sale "a occhio", assaggi e aggiusti. Se esci dall'appartamento con un piatto diverso dal solito, è un problema solo per te. Non hai bisogno di documentare nulla perché sei l'unico che cucina.

In un ristorante stellato con 30 cuochi, 500 coperti a sera e clienti che si aspettano che il risotto alla milanese sia *esattamente identico* ogni volta — a qualsiasi ora, qualunque sia il cuoco di turno — non puoi permetterti l'improvvisazione. Ogni piatto ha una **ricetta standardizzata** con ingredienti, pesi esatti, tempi di cottura precisi, impiattamento definito. I processi sono documentati. I nuovi cuochi vengono formati sulle procedure. La qualità è misurabile e costante.

**ITIL è il ricettario standard dell'IT.**

#### Spiegazione Tecnica

**ITIL** (Information Technology Infrastructure Library) è un framework — cioè un insieme strutturato di pratiche, processi e raccomandazioni — per la gestione dei servizi IT. Non è un software, non è un tool, non è un prodotto da comprare: è una *metodologia*, un modo condiviso di fare le cose.

ITIL nasce negli anni '80 nel governo britannico come raccolta delle migliori pratiche osservate nelle organizzazioni IT più efficienti. Nel tempo è diventato lo standard globale più diffuso per l'IT Service Management (ITSM).

**ITIL 4** (la versione attuale, pubblicata nel 2019) si organizza attorno a un **Sistema di Valore del Servizio** (SVS) e include 34 pratiche di gestione. Per i nostri scopi, le pratiche più rilevanti sono:

| Pratica ITIL | Cosa Significa in Pratica |
|-------------|--------------------------|
| **Incident Management** | Come gestire un guasto: rilevarlo, classificarlo, risolverlo, documentarlo |
| **Problem Management** | Come trovare la causa radice di incidenti ricorrenti per eliminarla definitivamente |
| **Change Enablement** | Come pianificare, approvare e implementare modifiche all'infrastruttura senza causare guasti |
| **Service Request Management** | Come gestire le richieste degli utenti (nuovo account, nuovo PC, nuovo accesso) |
| **Configuration Management** | Come tenere traccia di tutti gli asset IT e delle loro relazioni (il CMDB) |
| **Knowledge Management** | Come documentare soluzioni e procedure per non reinventare la ruota ogni volta |
| **Monitoring and Event Management** | Come rilevare automaticamente eventi anomali nei sistemi |

**Perché un team IT Ops ha bisogno di ITIL?**

Immagina un team di 5 persone IT in un'azienda di 200 dipendenti. Arriva una segnalazione: "la stampante di reparto non funziona." Senza un framework:
- Chi la gestisce? Mario o Luca?
- Come la registriamo? In un foglio Excel? In un'email? Sulla lavagna?
- Come sappiamo se è già stata segnalata?
- Come misuriamo quanto tempo ci abbiamo messo?
- Come sappiamo se questa stampante si è rotta già tre volte nell'ultimo mese (problema ricorrente)?

Con ITIL (e un tool ITSM come GLPI):
1. L'utente apre un **ticket** nel sistema
2. Il ticket viene **classificato** (Incident → Hardware → Printing)
3. Viene **assegnato** automaticamente alla persona giusta
4. Viene **prioritizzato** in base all'impatto (se è l'unica stampante del reparto contabilità durante il trimestrale, è priorità alta)
5. Il tecnico risolve e **documenta** la soluzione
6. Il ticket si **chiude** e i dati restano nel sistema per analisi future
7. Se la stessa stampante apre 5 ticket in 2 mesi, il sistema lo segnala e si apre un **Problem** per trovare la causa radice

#### Perché Mi Interessa?

Nei tuoi primi mesi di lavoro in IT Ops sentirai spesso dire: *"aprimi un ticket"*, *"hai aggiornato il CMDB?"*, *"l'hai documentato nel KB?"*, *"qual è la priorità?"*, *"qual è la causa radice?"*. Tutte queste frasi vengono da ITIL. Capire la logica di questo framework ti permetterà di muoverti in qualsiasi azienda professionale senza sentirti perso nel primo giorno.

---

### Concetto A4: La Giornata Tipo di un IT Operations Engineer

Una giornata nel mondo IT Ops non è mai identica a un'altra. Ma c'è una struttura ricorrente che imparerai a riconoscere. Vediamo la giornata di un IT Ops Engineer di livello junior/mid in un'azienda di medie dimensioni (100–500 dipendenti).

---

#### Timeline Realistica — Turno Mattino (08:00 – 17:00)

```
08:00  ┌─────────────────────────────────────────────────────────────
       │ INGRESSO E HANDOVER
       │ Strumento: Zabbix (monitoring), email, sistema di ticketing (GLPI)
       │
       │ • Controlli dashboard Zabbix: qualche alert critico durante la notte?
       │ • Leggi le note del turno notturno (o del collega in smart working)
       │ • Scorri i ticket aperti: ce ne sono di nuovi ad alta priorità?
       │ • Controlla lo stato dei backup notturni (successo/fallimento)
       └─────────────────────────────────────────────────────────────

08:30  ┌─────────────────────────────────────────────────────────────
       │ TRIAGE DEI TICKET
       │ Strumento: GLPI (o ServiceNow / Jira Service Management)
       │
       │ • Classificazione e prioritizzazione dei ticket nuovi
       │ • Assegnazione al tecnico competente
       │ • Risposta ai ticket urgenti (P1/P2) già in coda dalla notte
       └─────────────────────────────────────────────────────────────

09:00  ┌─────────────────────────────────────────────────────────────
       │ BLOCCO LAVORO PIANIFICATO — Manutenzione Preventiva
       │ Strumento: PowerShell / Bash, Zabbix, WSUS, documentazione
       │
       │ Esempi di attività pianificate:
       │ • Applicare gli aggiornamenti del Patch Tuesday ai server
       │ • Verificare spazio disco su tutti i server (script automatizzato)
       │ • Controllare lo stato dell'hardware (temperatura CPU, stato RAID)
       │ • Revisionare le policy di backup
       └─────────────────────────────────────────────────────────────

10:30  ┌─────────────────────────────────────────────────────────────
       │ GESTIONE RICHIESTE UTENTI — Service Request
       │ Strumento: GLPI, Active Directory (ADUC), Microsoft 365 Admin
       │
       │ Esempi di richieste tipiche:
       │ • Creazione nuovo account utente (onboarding neoassunto)
       │ • Reset password
       │ • Installazione software su una workstation
       │ • Mappatura nuova cartella condivisa
       │ • Accesso a un sistema specifico
       └─────────────────────────────────────────────────────────────

12:00  ┌─────────────────────────────────────────────────────────────
       │ PAUSA PRANZO
       └─────────────────────────────────────────────────────────────

13:00  ┌─────────────────────────────────────────────────────────────
       │ INCIDENTI — Gestione Reattiva
       │ Strumento: Zabbix (alert), RDP/SSH (accesso remoto), log analyzer
       │
       │ Nota: gli incident arrivano quando vogliono loro.
       │ La mattina è dedicata al lavoro pianificato,
       │ ma un alert P1 interrompe TUTTO il resto.
       └─────────────────────────────────────────────────────────────

14:00  ┌─────────────────────────────────────────────────────────────
       │ DOCUMENTAZIONE E KNOWLEDGE BASE
       │ Strumento: Wiki aziendale (Confluence, Notion, SharePoint)
       │
       │ • Documentare la soluzione di un problema risolto oggi
       │ • Aggiornare procedure operative che sono cambiate
       │ • Scrivere la procedura per un'attività ricorrente non documentata
       └─────────────────────────────────────────────────────────────

15:00  ┌─────────────────────────────────────────────────────────────
       │ CHANGE MANAGEMENT
       │ Strumento: GLPI Change module, email, calendario
       │
       │ • Preparare RFC (Request for Change) per intervento pianificato
       │ • Partecipare al CAB (Change Advisory Board) settimanale
       │ • Implementare change approvati in questa finestra temporale
       └─────────────────────────────────────────────────────────────

16:30  ┌─────────────────────────────────────────────────────────────
       │ CHIUSURA TURNO — Handover e Report
       │ Strumento: Email, GLPI, Zabbix
       │
       │ • Aggiornare lo stato dei ticket gestiti
       │ • Scrivere note di handover per il turno successivo
       │ • Ultimo controllo dashboard Zabbix
       │ • Verificare che nessun backup critico sia programmato senza supervisione
       └─────────────────────────────────────────────────────────────

17:00  ┌─────────────────────────────────────────────────────────────
       │ FINE TURNO
       └─────────────────────────────────────────────────────────────
```

#### Strumenti Usati — Panoramica Rapida

| Strumento | Categoria | Usato Per |
|-----------|-----------|-----------|
| **Zabbix** | Monitoring | Dashboard in tempo reale di server, rete, servizi; alert automatici |
| **GLPI** | ITSM / Ticketing | Gestione ticket, richieste, change, CMDB, asset inventory |
| **PowerShell** | Automazione Windows | Gestione server Windows, Active Directory, scripting, deployment |
| **Bash** | Automazione Linux | Gestione server Linux, scripting, automazione task |
| **Active Directory (ADUC)** | Identity Management | Creazione/gestione utenti, gruppi, policy di dominio |
| **RDP (Remote Desktop)** | Accesso Remoto | Connettersi ai server e workstation Windows a distanza |
| **SSH** | Accesso Remoto | Connettersi ai server Linux a distanza in modo sicuro |
| **Wireshark / tcpdump** | Network Analysis | Analizzare il traffico di rete per diagnosi di problemi |
| **Event Viewer** | Log Windows | Leggere i log di sistema, sicurezza, applicazioni su Windows |
| **journalctl / syslog** | Log Linux | Leggere i log di sistema su Linux |

#### Perché Mi Interessa?

Vedere la giornata tipo ti aiuta a capire che l'IT Ops non è "stare seduto ad aspettare che si rompa qualcosa." C'è una struttura, ci sono priorità, ci sono responsabilità precise. Imparare a gestire il proprio tempo tra lavoro pianificato e interruzioni reattive è una delle competenze più importanti che svilupperai.

---

### Concetto A5: Cos'è una Virtual Machine — Spiegato a Tre Livelli

Useremo le Virtual Machine (VM) per tutto il corso. Prima di crearle, capiamo davvero cosa sono.

---

#### Livello 1 — Per un Bambino di 10 Anni

Immagina che il tuo PC sia come una grande stanza. In quella stanza hai il tuo computer, con il suo schermo, la sua tastiera, il suo Windows.

Ora immagina di poter costruire una stanza finta dentro questa stanza reale. Dentro la stanza finta c'è un altro computer finto — con il suo schermo finto, la sua tastiera finta, il suo Windows finto. Ma questo computer finto si comporta esattamente come uno vero: ci puoi installare programmi, navigare in internet (se lo colleghi), salvare file.

La cosa magica è che puoi avere 2, 3, 5 di queste stanze finte contemporaneamente, tutte dentro la stanza reale. E se distruggi accidentalmente la stanza finta (per esempio installi qualcosa di sbagliato), non hai rotto nulla di vero — puoi semplicemente ricostruire la stanza finta da zero in pochi minuti.

**Una Virtual Machine è un computer finto che vive dentro il tuo computer vero.**

---

#### Livello 2 — Per uno Studente IT

Una **Virtual Machine (VM)** è un ambiente di elaborazione software completamente isolato che simula un computer fisico. La VM ha:

- **CPU virtuale** (vCPU): una porzione della CPU fisica del tuo PC viene assegnata alla VM
- **RAM virtuale**: una porzione della RAM del tuo PC viene dedicata alla VM
- **Disco virtuale**: un file sul tuo PC (formato `.vdi`, `.vmdk`, o `.vhd`) che simula un disco rigido fisico
- **Scheda di rete virtuale**: un adattatore software che simula una NIC (Network Interface Card) fisica

Il sistema operativo che gira dentro la VM — chiamato **Guest OS** — non sa di essere virtualizzato (o quasi non lo sa). Dal punto di vista del Guest OS, lui sta girando su hardware reale.

Il tuo sistema operativo principale (Windows 10/11 sul tuo PC) si chiama **Host OS**, perché *ospita* le VM.

**Vantaggi chiave:**
- **Isolamento:** se la VM viene compromessa o si rompe, il tuo PC fisico non ne risente
- **Snapshot:** puoi salvare lo stato esatto della VM in un preciso momento e tornare a quel momento quando vuoi (come la funzione "Annulla" di un elaboratore di testi, ma per interi sistemi operativi)
- **Portabilità:** una VM è un file — puoi copiarla su un USB e farla girare su un altro PC
- **Efficienza:** su un server fisico puoi far girare decine di VM, usando molto meglio le risorse hardware

---

#### Livello 3 — Per il Tecnico

**L'Hypervisor** è il software che crea, gestisce e isola le VM. Il termine deriva da *hyper* (sopra) + *supervisor* (supervisore): è il supervisore che sta sopra i sistemi operativi.

Esistono due tipi di hypervisor, con architetture fondamentalmente diverse:

**Hypervisor di Tipo 1 (Bare-Metal):**
Gira *direttamente sull'hardware fisico*, senza sistema operativo host intermedio. Ha accesso diretto alla CPU, alla RAM e ai dispositivi I/O.

```
┌───────────────────────────────────────┐
│          VM1         VM2         VM3  │
│   (Windows) (Ubuntu) (Windows)        │
├───────────────────────────────────────┤
│         HYPERVISOR TIPO 1             │
│  (VMware ESXi / Hyper-V / Proxmox /   │
│   XenServer / KVM)                    │
├───────────────────────────────────────┤
│           HARDWARE FISICO             │
│   CPU  RAM  Dischi  NIC  GPU  ...     │
└───────────────────────────────────────┘
```

Esempi: VMware ESXi, Microsoft Hyper-V (in modalità server), Proxmox VE, XenServer, KVM su Linux.
Usato in: datacenter aziendali, server di produzione, cloud provider (AWS EC2, Azure VMs, Google Compute Engine usano tutti hypervisor tipo 1 sotto).

**Hypervisor di Tipo 2 (Hosted):**
Gira *come un'applicazione* sopra un sistema operativo host già installato. Ha un layer intermedio (il sistema operativo host) tra lui e l'hardware fisico — questo lo rende leggermente meno performante del tipo 1, ma molto più semplice da installare e usare su un normale PC.

```
┌───────────────────────────────────────┐
│          VM1         VM2         VM3  │
│   (Windows) (Ubuntu) (Windows)        │
├───────────────────────────────────────┤
│         HYPERVISOR TIPO 2             │
│  (VirtualBox / VMware Workstation /   │
│   VMware Fusion / Parallels Desktop)  │
├───────────────────────────────────────┤
│         SISTEMA OPERATIVO HOST        │
│         (Windows 10/11 / macOS)       │
├───────────────────────────────────────┤
│           HARDWARE FISICO             │
│   CPU  RAM  Dischi  NIC  GPU  ...     │
└───────────────────────────────────────┘
```

Esempi: Oracle VirtualBox, VMware Workstation (Windows/Linux), VMware Fusion (macOS), Parallels Desktop (macOS).
Usato in: sviluppo locale, lab di studio, testing, ambienti non critici.

**Virtualizzazione CPU — VT-x e AMD-V:**
I processori moderni Intel e AMD includono estensioni hardware specifiche per la virtualizzazione:
- **Intel VT-x** (Virtualization Technology): presente su quasi tutti i processori Intel Core i3/i5/i7/i9 dal 2007 in poi
- **AMD-V** (AMD Virtualization, nota anche come SVM): presente su quasi tutti i processori AMD Ryzen

Queste estensioni permettono all'hypervisor di eseguire istruzioni privilegiate della VM *direttamente sulla CPU fisica* invece di emularle via software — il risultato è prestazioni vicine all'hardware nativo. Senza VT-x/AMD-V, la virtualizzazione sarebbe 10–20 volte più lenta e inutilizzabile in pratica.

**Perché Mi Interessa?**

Nel tuo lavoro in IT Ops gestirai principalmente **hypervisor di tipo 1** su server fisici in datacenter o in cloud. Ma per imparare e per il lab di questo corso usiamo un **hypervisor di tipo 2** (VirtualBox) sul tuo PC personale, perché non richiede hardware server dedicato e si installa in cinque minuti. I concetti che imparerai con VirtualBox si trasferiscono direttamente a Proxmox, VMware ESXi e Hyper-V — cambiano i menù, non i principi.

---

### Concetto A6: VirtualBox — Il Nostro Hypervisor Gratuito

#### Cos'è VirtualBox

**Oracle VM VirtualBox** è un hypervisor di tipo 2 open source sviluppato originariamente da Sun Microsystems, acquisito da Oracle nel 2010 e distribuito gratuitamente con licenza GPLv2 (la versione base) e con licenza commerciale (la versione con Extension Pack aggiuntivo).

È disponibile per Windows, macOS, Linux e Solaris. Per il nostro lab useremo la versione Windows.

---

#### Perché Usiamo VirtualBox e Non Altro

| Criterio | VirtualBox | VMware Workstation | Hyper-V | Proxmox VE |
|----------|-----------|-------------------|---------|------------|
| **Costo** | Gratuito | A pagamento (~200€/anno) | Gratuito (incluso in Windows Pro) | Gratuito (open source) |
| **Piattaforma** | Windows, macOS, Linux | Windows, Linux | Solo Windows | Solo Linux / Bare metal |
| **Difficoltà setup** | Molto facile | Facile | Media (richiede Windows Pro) | Alta (richiede server dedicato) |
| **Formato snapshot** | Ottimo | Ottimo | Buono | Ottimo |
| **Rete host-only** | Sì, integrata | Sì, integrata | Limitata | Sì, integrata |
| **Adatto al lab** | Sì | Sì | Sì, ma più complesso | No (richiede hardware dedicato) |

**La scelta:** VirtualBox è gratuito, multipiattaforma, semplice da installare, e ha tutte le funzionalità che ci servono. Le skill che impari con VirtualBox si trasferiscono facilmente a Proxmox e VMware una volta in ambiente aziendale.

**Nota su Hyper-V:** Se hai Windows 10/11 Pro o Enterprise, Hyper-V è già incluso. Può essere una valida alternativa a VirtualBox — ma non possono coesistere sullo stesso PC senza configurazione avanzata, e Hyper-V ha un'interfaccia meno intuitiva per i principianti. Per questo corso, **disabilita Hyper-V** prima di installare VirtualBox.

---

#### Installazione di VirtualBox su Windows 10/11

**Passo 1 — Disabilitare Hyper-V (se attivo)**

Apri PowerShell come Amministratore e lancia:

```powershell
# Disabilitare Hyper-V e le funzionalità correlate
# ATTENZIONE: richiede riavvio del PC
bcdedit /set hypervisorlaunchtype off
Disable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All -NoRestart
Disable-WindowsOptionalFeature -Online -FeatureName HypervisorPlatform -NoRestart
Disable-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform -NoRestart

Write-Host "Hyper-V disabilitato. Riavvia il PC prima di installare VirtualBox." -ForegroundColor Yellow
```

Riavvia il PC.

**Passo 2 — Scaricare VirtualBox**

1. Vai su [https://www.virtualbox.org/wiki/Downloads](https://www.virtualbox.org/wiki/Downloads)
2. Scarica **VirtualBox X.X.X platform packages → Windows hosts** (il file `.exe`)
3. Scarica anche il **VirtualBox Extension Pack** (stesso link, sezione "VirtualBox Extension Pack") — aggiunge supporto USB 2.0/3.0 e altre funzionalità utili

**Passo 3 — Installare VirtualBox**

1. Lancia l'installer scaricato (doppio click sul file `.exe`)
2. Clicca **Next** alle prime schermate
3. Nella schermata "Custom Setup", lascia tutto come default
4. Alla richiesta "Warning: Network Interfaces" → clicca **Yes** (la rete del PC si interromperà per alcuni secondi durante l'installazione — normale)
5. Completa l'installazione → **Install** → **Finish**

**Passo 4 — Installare l'Extension Pack**

1. Apri VirtualBox
2. Menu **File** → **Tools** → **Extension Pack Manager**
3. Clicca sul pulsante **Install** (icona +)
4. Seleziona il file `.vbox-extpack` scaricato
5. Accetta la licenza → **I Agree**

**Passo 5 — Configurare la Rete Host-Only**

La rete host-only è quella che useremo per collegare le tre VM tra loro.

```powershell
# Verifica che VirtualBox sia installato correttamente
& "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe" --version

# Crea la rete host-only (se non esiste già)
& "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe" hostonlyif create

# Configura l'IP del gateway host-only (il tuo PC fisico sarà 192.168.56.1)
& "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe" hostonlyif ipconfig "VirtualBox Host-Only Ethernet Adapter" `
    --ip 192.168.56.1 `
    --netmask 255.255.255.0

# Disabilita il server DHCP automatico di VirtualBox sulla rete host-only
# (useremo IP statici, non DHCP)
& "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe" dhcpserver modify `
    --ifname "VirtualBox Host-Only Ethernet Adapter" `
    --disable
```

In alternativa, usa l'interfaccia grafica:
1. Menu **File** → **Tools** → **Network Manager**
2. Scheda **Host-only Networks**
3. Verifica che esista `vboxnet0` con IP `192.168.56.1` e maschera `255.255.255.0`
4. Nella scheda **DHCP Server** → spunta **Disable Server**

---

#### Le Alternative — Quando le Userai in Ambiente Aziendale

| Tool | Quando lo Incontri | Cosa Cambia Rispetto a VirtualBox |
|------|-------------------|----------------------------------|
| **Proxmox VE** | Server on-premise aziendali, home lab avanzati | Hypervisor tipo 1, gestione via browser, cluster HA, storage shared |
| **VMware vSphere / ESXi** | Enterprise medio-grande, datacenter | Hypervisor tipo 1 leader di mercato, feature avanzate, licenze costose |
| **Microsoft Hyper-V** | Ambienti Microsoft-centrico, Windows Server | Integrato in Windows Server, gestito con PowerShell o Hyper-V Manager |
| **AWS EC2 / Azure VM / GCP** | Cloud | VM nel cloud — non gestisci l'hypervisor, gestisci solo la VM |
| **KVM + libvirt** | Ambienti Linux enterprise | Hypervisor tipo 1 integrato nel kernel Linux, gestito da CLI o virt-manager |

#### Perché Mi Interessa?

VirtualBox è il tuo campo di addestramento. Imparare a creare VM, configurare reti, fare snapshot, clonare macchine, e diagnosticare problemi in VirtualBox ti dà una base solida che si trasferisce — con piccoli adattamenti — a qualsiasi altro hypervisor che incontrerai in carriera.

---

### Concetto A7: Le Tre VM del Nostro Lab — Perché Tre?

Potresti chiederti: "perché creare tre VM diverse? Non basterebbe una sola?" La risposta è: tre VM perché stiamo **riproducendo in miniatura la struttura reale di una rete aziendale**. Ogni VM ha un ruolo preciso, e la loro interazione ti insegnerà come funziona davvero l'infrastruttura IT.

---

#### VM1 — Windows Server 2022 · `DC-LAB-01` · 192.168.56.10

**Ruolo nel lab:** Domain Controller, DNS Server, DHCP Server, File Server

**In un'azienda reale, cosa fa questa macchina:**

Questa è la macchina più importante della rete Windows. Il **Domain Controller (DC)** è il cuore dell'infrastruttura Microsoft aziendale. Gestisce:

- **Active Directory Domain Services (AD DS):** il "registro" centralizzato di tutti gli utenti, computer, gruppi e policy dell'azienda. Quando un dipendente digita username e password per accedere al PC, è il DC che verifica le credenziali. Quando l'IT crea un nuovo account per un neoassunto, lo crea nel DC. Senza DC, ogni PC avrebbe i propri account separati — gestire 200 PC separatamente sarebbe impossibile.

- **DNS (Domain Name System):** il "rubrica telefonica" della rete. Traduce nomi in indirizzi IP: quando il PC di Mario cerca `file-server.azienda.local`, è il DNS del DC che risponde con l'indirizzo IP `192.168.56.10`. Senza DNS, ogni computer dovrebbe ricordare l'indirizzo IP di tutti gli altri — impraticabile.

- **DHCP (Dynamic Host Configuration Protocol):** il servizio che assegna automaticamente gli indirizzi IP ai nuovi dispositivi che si collegano alla rete. Quando un laptop connette il Wi-Fi aziendale, è il DHCP che gli dice "il tuo IP per questa sessione è 192.168.1.47." Nel lab useremo IP statici, ma il servizio DHCP lo configureremo comunque per capire come funziona.

- **File Server:** la cartella condivisa aziendale. I dipendenti salvano i file non sul proprio PC ma sul server — così i file sono centralizzati, protetti da backup, accessibili da qualsiasi PC in azienda. Windows Server gestisce le share tramite **SMB (Server Message Block)**.

**Cosa impareremo con VM1:**
- Promuovere un server a Domain Controller (installare Active Directory)
- Creare e gestire utenti e gruppi in Active Directory
- Configurare DNS zones e record
- Configurare DHCP scopes e reservations
- Creare e gestire cartelle condivise con permessi granulari
- Applicare Group Policy Objects (GPO) per configurare automaticamente i PC del dominio
- Unire VM3 al dominio (join domain)

---

#### VM2 — Ubuntu Server 22.04 · `SRV-LINUX-01` · 192.168.56.20

**Ruolo nel lab:** Server di monitoraggio, servizi Linux, Zabbix

**In un'azienda reale, cosa fa questa macchina:**

Il server Linux ha un ruolo completamente diverso dal Domain Controller Windows. In un'infrastruttura mista (Windows + Linux — la situazione più comune nelle aziende reali), i server Linux spesso gestiscono:

- **Monitoring:** strumenti come Zabbix, Nagios, Prometheus girano tipicamente su Linux. Nel nostro lab installeremo **Zabbix Server** su VM2 per monitorare VM1 e VM3. Vedremo alert in tempo reale, dashboard, metriche di sistema.

- **Web server / Application server:** Apache, Nginx, Node.js, Python Flask — la maggior parte dei web server del mondo girano su Linux.

- **Database server:** MySQL, PostgreSQL, MariaDB sono nativi Linux.

- **Backup server:** molte soluzioni di backup (Bacula, Amanda, rsync) girano meglio su Linux.

- **Scripting e automazione:** Bash e Python sono strumenti nativi Linux — script complessi che sarebbero macchinosi in PowerShell sono spesso più eleganti in Bash.

**Perché Linux in un lab principalmente Windows:**

Nelle aziende reali, il 100% delle infrastrutture Windows-only è raro. Quasi sempre c'è almeno un server Linux per compiti specifici. Un IT Ops che non sa navigare in Linux a livello base è limitato. In questo lab userai VM2 per:
- Imparare i comandi Linux fondamentali (navigazione filesystem, gestione file, processi, permessi)
- Installare e configurare servizi da riga di comando (no interfaccia grafica)
- Lavorare con SSH come metodo standard di accesso remoto
- Capire la struttura del filesystem Linux (`/etc`, `/var`, `/home`, `/opt`, ecc.)
- Installare Zabbix e configurare il monitoring dell'intero lab

**Cosa impareremo con VM2:**
- Navigazione filesystem Linux e gestione dei permessi (`chmod`, `chown`)
- Gestione dei servizi con `systemctl` (start/stop/enable/disable/status)
- Lettura e analisi dei log con `journalctl`, `tail -f`, `grep`
- Installazione software con `apt` (package manager di Ubuntu/Debian)
- Configurazione SSH e gestione accesso remoto sicuro
- Installazione e configurazione di Zabbix Server
- Scrittura di script Bash di base per automazione

---

#### VM3 — Windows 10 · `WKS-LAB-01` · 192.168.56.30

**Ruolo nel lab:** Workstation dell'utente/amministratore

**In un'azienda reale, cosa fa questa macchina:**

VM3 simula il PC di un dipendente — o del tecnico IT stesso. Nel lab la useremo in due modi diversi:

1. **Come workstation utente:** testeremo come si vede l'infrastruttura dal punto di vista di un utente normale. Uniremo questa macchina al dominio Active Directory di VM1, vedremo le cartelle condivise, applicheremo le Group Policy, simuleremo i problemi che gli utenti aprono come ticket.

2. **Come workstation amministratore:** installeremo i tool di amministrazione (RSAT — Remote Server Administration Tools) per gestire il Domain Controller da questa macchina invece di andare fisicamente sul server. Questo è il modo normale di lavorare in un'azienda: l'amministratore IT gestisce i server da remoto, non si siede davanti ad ogni server.

**Tools che installeremo su VM3:**
- **RSAT (Remote Server Administration Tools):** la suite di strumenti Microsoft per gestire remotamente Active Directory, DNS, DHCP, File Server, senza stare fisicamente davanti al server
- **Zabbix Frontend (browser):** apriremo la dashboard di Zabbix dal browser di VM3 per vedere il monitoring
- **Putty / Windows Terminal:** per connetterci via SSH a VM2 (il server Linux)
- **PowerShell 7:** per gestire sia Windows che (via moduli) Linux e Azure

**Cosa impareremo con VM3:**
- Join al dominio Active Directory
- Effetto delle Group Policy (prima e dopo l'applicazione di una GPO)
- Uso di RSAT per gestione AD, DNS, DHCP da workstation
- Accesso alle cartelle condivise via UNC path (`\\DC-LAB-01\Share`)
- Connessione SSH a server Linux da Windows tramite Terminal / Putty
- Troubleshooting di problemi comuni della workstation (dal punto di vista IT Ops)

---

#### Perché Tre VM e Non Una?

Riassumendo con un'analogia: un'azienda ha ruoli diversi — il direttore generale, il magazziniere e l'impiegato. Nessuno di loro fa il lavoro dell'altro. Mettere tutti i ruoli nella stessa persona creerebbe caos e vulnerabilità.

In IT la stessa logica si applica: **separation of roles**. Il Domain Controller non deve essere anche il server di produzione web. Il server di monitoring non deve ospitare anche i database aziendali. La workstation dell'utente non deve avere accesso diretto ai servizi backend.

Con tre VM separate:
- Impari come le macchine **comunicano** tra loro (protocolli: SMB, LDAP, DNS, RDP, SSH)
- Impari come i **permessi** attraversano i confini di sistema (un utente Active Directory può accedere ai file su VM1 dalla workstation VM3)
- Impari a gestire l'infrastruttura **da remoto**, come si fa in realtà
- Impari che rompere una VM non rompe le altre (isolamento)

---

#### Schema Riassuntivo dei Ruoli

```
VM1 (DC-LAB-01)                VM2 (SRV-LINUX-01)           VM3 (WKS-LAB-01)
Windows Server 2022            Ubuntu Server 22.04           Windows 10
192.168.56.10                  192.168.56.20                 192.168.56.30
─────────────────              ──────────────────            ─────────────────
• Active Directory             • Zabbix Server               • Client di dominio
• DNS Server                   • Monitoring di VM1 e VM3     • RSAT (gestione AD)
• DHCP Server                  • SSH access point            • Browser → Zabbix UI
• File Server (SMB)            • Script Bash lab             • PowerShell admin
• Group Policy                 • Servizi Linux demo          • Simulazione utente
                                                              • SSH client → VM2
       │                              │                              │
       └──────────────────────────────┴──────────────────────────────┘
                          192.168.56.0/24 (Host-Only)
```

---

*Fine Part A — Fondamenti.*

*La Part B coprirà l'installazione step-by-step delle tre VM e la configurazione di Active Directory su VM1.*

---

---

## PART B: OPERAZIONI — Configurare l'Ambiente Lab

> In questa sezione costruiamo passo dopo passo il lab che useremo in tutti i tutorial del corso. Ogni esercizio include obiettivo, istruzioni dettagliate, output atteso, checkpoint di verifica e troubleshooting dei problemi più comuni.

---

### Esercizio B1: Scaricare e Installare VirtualBox

**Obiettivo.** Installare VirtualBox 7.x su Windows 10/11 e verificare che la virtualizzazione hardware sia abilitata nel processore.

**Background.** VirtualBox è un *hypervisor di tipo 2* — un software che gira sopra il tuo sistema operativo e crea ambienti virtuali isolati. È sviluppato da Oracle, gratuito e open-source, funziona su Windows, macOS e Linux. Prima di installarlo, il processore deve avere la virtualizzazione hardware abilitata nel firmware BIOS/UEFI: questa funzionalità si chiama VT-x sui processori Intel e AMD-V (o SVM) su AMD. Senza di essa, le VM sarebbero troppo lente per essere usate.

> **Analogia.** Pensa a VirtualBox come a un teatrino di burattini: la scena è il tuo PC fisico, i burattini sono le VM. Ogni burattino recita il suo ruolo (server, client, router) ma condivide lo stesso palcoscenico. Se un burattino cade, gli altri continuano a muoversi.

**Perché mi interessa?** Senza un ambiente di lab sicuro, ogni errore potrebbe danneggiare sistemi reali. VirtualBox crea una "bolla" isolata dove puoi sbagliare, imparare e ricominciare da zero senza conseguenze.

**Step 1 — Verifica che la virtualizzazione sia abilitata**

Apri PowerShell (tasto Windows → digita `powershell` → Enter) e digita:

```powershell
(Get-ComputerInfo).HyperVRequirementVirtualizationFirmwareEnabled
```

Output atteso se la virtualizzazione è abilitata:
```
True
```

Se il risultato è `False`, devi entrare nel BIOS/UEFI del tuo PC (riavvia e premi F2, F10, Del o il tasto specifico del produttore durante il POST) e cercare la voce `Intel Virtualization Technology`, `Intel VT-x`, `AMD-V` o `SVM Mode` — abilitala, salva e riavvia.

**Step 2 — Disabilitare Hyper-V se attivo (Windows 11)**

Windows 11 attiva Hyper-V di default su alcuni sistemi, creando conflitti con VirtualBox. Verifica:

```powershell
Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All | Select-Object State
```

Se lo stato è `Enabled`, disabilita Hyper-V da PowerShell **avviato come Amministratore**:

```powershell
bcdedit /set hypervisorlaunchtype off
Disable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All -NoRestart
Restart-Computer
```

**Step 3 — Scaricare e Installare VirtualBox**

Vai su `https://www.virtualbox.org/wiki/Downloads` e scarica:
- **VirtualBox 7.x platform packages** → Windows hosts
- **VirtualBox Extension Pack** (stessa pagina, sezione sotto) — stesso numero di versione esatto

Avvia il file `.exe` → Next → Next → Yes (installa driver di rete) → Install → Finish.

Poi installa l'Extension Pack: VirtualBox → File → Preferences → Extensions → icona "+" → seleziona il file `.vbox-extpack` → Install → accetta la licenza → OK.

**Step 4 — Creare la Rete Host-Only**

La rete Host-Only permette alle VM di comunicare tra loro e con il tuo PC, senza uscire su internet. È la "rete privata" del lab.

VirtualBox → File → Host Network Manager → **Create** → appare `VirtualBox Host-Only Ethernet Adapter`

Configura i valori:

| Parametro | Valore da impostare |
|---|---|
| IPv4 Address | 192.168.56.1 |
| IPv4 Network Mask | 255.255.255.0 |
| DHCP Server | **Disabilitato** |

Clicca Apply → Close.

**Checkpoint di verifica B1:**
- [ ] PowerShell mostra `True` per la virtualizzazione hardware
- [ ] VirtualBox si apre senza errori
- [ ] Extension Pack installato (File → Preferences → Extensions mostra una voce con la versione corretta)
- [ ] Rete Host-Only `192.168.56.0/24` creata con DHCP disabilitato

**Cosa potrebbe andare storto:**
1. *"Virtualizzazione non trovata nel BIOS"* → Produttori diversi nascondono questa opzione in posti diversi: su Dell cerca sotto "Virtualization Support", su Lenovo sotto "Security" → "Virtualization", su HP sotto "System Configuration" → "Device Configurations"
2. *"Conflitto con Windows Sandbox o WSL 2"* → Anche queste funzionalità usano Hyper-V; disabilitale temporaneamente durante il lab
3. *"Extension Pack: versione incompatibile"* → Deve corrispondere ESATTAMENTE alla versione di VirtualBox installata (es. 7.0.14 con 7.0.14, mai 7.0.12 con 7.0.14)

---

### Esercizio B2: Creare VM1 — Windows Server 2022 (DC-LAB-01)

**Obiettivo.** Creare e configurare la VM che simula il server principale dell'azienda — gestirà Active Directory, DNS, DHCP e File Server nei tutorial successivi.

**Background.** Windows Server 2022 è il sistema operativo server di Microsoft, progettato per hardware fisico o virtuale in ambienti aziendali. Microsoft offre **versioni di valutazione di 180 giorni** completamente gratuite e funzionali — perfette per il lab.

> **Analogia.** Se la tua azienda fosse un condominio, DC-LAB-01 è il portiere: conosce tutti i residenti (Active Directory), gestisce le chiavi di accesso (autenticazione), e sa dove abita ogni appartamento (DNS). Ogni altro servizio dipende da lui.

**Step 1 — Scaricare Windows Server 2022 Evaluation**

Vai su: `https://www.microsoft.com/evalcenter/evaluate-windows-server-2022`

Compila il form (puoi usare dati inventati per il lab) e scarica l'ISO di circa 5 GB. Il download richiede 20-60 minuti secondo la connessione.

**Step 2 — Creare la VM in VirtualBox**

VirtualBox → Machine → New:

| Parametro | Valore |
|---|---|
| Nome | DC-LAB-01 |
| Folder | lascia il default |
| ISO Image | seleziona l'ISO scaricata |
| Skip Unattended Installation | ✓ spunta questa casella |
| Tipo | Microsoft Windows |
| Versione | Windows 2022 (64-bit) |
| RAM | 4096 MB (o 8192 se hai 32 GB sul PC) |
| CPU | 2 |
| Disco | 60 GB, VDI, Pre-allocazione dinamica |

**Step 3 — Configurare le Schede di Rete**

Seleziona DC-LAB-01 → Settings → Network:

- **Adapter 1**: NAT (accesso internet per download durante installazione)
- **Adapter 2**: abilitato → Host-only Adapter → `VirtualBox Host-Only Ethernet Adapter`

**Step 4 — Avviare l'Installazione di Windows Server**

Avvia la VM (doppio click su DC-LAB-01). Si avvia dall'ISO e appare il setup di Windows:

- Lingua: English (consigliato per seguire documentazione internazionale)
- **Edizione**: `Windows Server 2022 Standard Evaluation (Desktop Experience)` ← IMPORTANTE: scegli la versione con Desktop, non Server Core
- Tipo installazione: **Custom** → seleziona il disco da 60 GB → Next

L'installazione richiede 20-30 minuti. Al termine Windows chiede la password di Administrator:

```
Password:  Lab@2024!
Conferma:  Lab@2024!
```

**Step 5 — Configurare IP Statico e Hostname**

Apri PowerShell su DC-LAB-01 (Start → digita `powershell` → tasto destro → Run as Administrator):

```powershell
# Vedi le interfacce disponibili
Get-NetAdapter | Select-Object Name, Status, MacAddress
```

Output tipico:
```
Name        Status  MacAddress
--------    ------  -----------------
Ethernet    Up      08-00-27-AA-BB-CC   <- Adapter 1 (NAT)
Ethernet 2  Up      08-00-27-DD-EE-FF   <- Adapter 2 (Host-Only)
```

```powershell
# Assegna IP statico all'interfaccia Host-Only
New-NetIPAddress `
    -InterfaceAlias "Ethernet 2" `
    -IPAddress "192.168.56.10" `
    -PrefixLength 24

# Configura DNS (questa VM sarà il server DNS)
Set-DnsClientServerAddress `
    -InterfaceAlias "Ethernet 2" `
    -ServerAddresses "192.168.56.10","8.8.8.8"

# Rinomina il computer e riavvia
Rename-Computer -NewName "DC-LAB-01" -Force -Restart
```

Dopo il riavvio, verifica l'IP:

```powershell
ipconfig /all
# Cerca la sezione "Ethernet 2":
# IPv4 Address. . . . . . . : 192.168.56.10
# Subnet Mask . . . . . . . : 255.255.255.0
```

**Checkpoint di verifica B2:**
- [ ] VM avviata e installazione completata senza errori
- [ ] Edizione: Standard Evaluation **con Desktop Experience** (interfaccia grafica visibile)
- [ ] IP `192.168.56.10` presente su Ethernet 2
- [ ] Hostname: `DC-LAB-01` (verifica con `hostname` in PowerShell)
- [ ] Login con `Administrator` / `Lab@2024!` funzionante dopo il riavvio

**Cosa potrebbe andare storto:**
1. *"La VM si avvia ma non mostra il setup ISO"* → Settings → Storage → Controller IDE: verifica che l'ISO sia selezionata; oppure usa Devices → Optical Drives → scegli l'ISO mentre la VM è avviata
2. *"Solo opzione Server Core nell'installer"* → Hai scaricato l'ISO versione Core (solo terminale); scarica di nuovo la versione corretta dall'Evaluation Center
3. *"Ethernet 2 assente in Get-NetAdapter"* → VirtualBox → VM Settings → Network → Adapter 2: spunta "Enable Network Adapter" e seleziona "Host-only Adapter"

---

### Esercizio B3: Creare VM2 — Ubuntu Server 22.04 (SRV-LINUX-01)

**Obiettivo.** Creare la VM Linux che ospiterà i servizi di monitoring (Prometheus/Grafana), GLPI ticketing, Docker e altri servizi nei tutorial successivi.

**Background.** Ubuntu Server 22.04 LTS è distribuita **senza interfaccia grafica** — si gestisce tutto da terminale. Questo è la norma sui server: l'interfaccia grafica consuma RAM e CPU inutilmente, visto che ci si connette sempre da remoto via SSH. Il suffisso LTS (Long Term Support) garantisce aggiornamenti di sicurezza fino ad aprile 2027.

> **Analogia.** Se DC-LAB-01 è il portiere del condominio, SRV-LINUX-01 è il tecnico di manutenzione: non ha un ufficio di rappresentanza (niente GUI), ma conosce ogni tubo e cavo dell'edificio. Ci parli per telefono (SSH), non di persona.

**Step 1 — Scaricare Ubuntu Server 22.04**

Vai su: `https://ubuntu.com/download/server` → scegli **Ubuntu Server 22.04.x LTS** (circa 1.4 GB).

**Step 2 — Creare la VM in VirtualBox**

VirtualBox → Machine → New:

| Parametro | Valore |
|---|---|
| Nome | SRV-LINUX-01 |
| Tipo | Linux |
| Versione | Ubuntu (64-bit) |
| RAM | 4096 MB |
| CPU | 2 |
| Disco | 40 GB, VDI, dinamico |

Network: Adapter 1 → NAT; Adapter 2 → Host-Only (stesso setup di VM1).

**Step 3 — Installare Ubuntu Server**

L'installer di Ubuntu Server è testuale (no mouse): naviga con Tab, Frecce e Enter. Selezioni importanti:

```
Keyboard layout    → Italian → Italian (no dead keys)
Network            → lascia DHCP sul NAT per ora
Storage            → Use entire disk → No LVM (più semplice per il lab)
Profile setup:
  Your name:       Lab Admin
  Server name:     srv-linux-01
  Username:        lab-admin
  Password:        Lab@2024!
SSH:               ✓ Install OpenSSH server  ← OBBLIGATORIO
Featured snaps:    nessuno, scegli Done/Skip
```

L'installazione richiede 15-25 minuti. Al termine clicca "Reboot Now". Quando appare il messaggio `Please remove the installation medium`, premi Enter (VirtualBox rimuove l'ISO automaticamente).

**Step 4 — Login e Configurazione IP Statico**

Dopo il riavvio compare il prompt di login testuale. Accedi con `lab-admin` / `Lab@2024!`.

```bash
# Vedi le interfacce di rete
ip addr show
```

Output tipico:
```
1: lo: <LOOPBACK,UP,LOWER_UP> ...
2: enp0s3: <BROADCAST,MULTICAST,UP,LOWER_UP>   <- Adapter 1 (NAT)
    inet 10.0.2.15/24
3: enp0s8: <BROADCAST,MULTICAST,UP,LOWER_UP>   <- Adapter 2 (Host-Only)
    (nessun IP ancora assegnato)
```

```bash
# Crea il file di configurazione Netplan per IP statico
sudo tee /etc/netplan/99-lab-static.yaml > /dev/null << 'NETPLAN_EOF'
network:
  version: 2
  renderer: networkd
  ethernets:
    enp0s8:
      dhcp4: false
      addresses:
        - 192.168.56.20/24
      nameservers:
        addresses:
          - 192.168.56.10
          - 8.8.8.8
NETPLAN_EOF

# Imposta permessi corretti (Netplan richiede 600 per sicurezza)
sudo chmod 600 /etc/netplan/99-lab-static.yaml

# Applica la configurazione senza riavvio
sudo netplan apply

# Verifica l'IP
ip addr show enp0s8
```

Output atteso dopo `netplan apply`:
```
3: enp0s8: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500
    link/ether 08:00:27:ab:cd:ef brd ff:ff:ff:ff:ff:ff
    inet 192.168.56.20/24 brd 192.168.56.255 scope global enp0s8
       valid_lft forever preferred_lft forever
```

**Checkpoint di verifica B3:**
- [ ] Login con `lab-admin` / `Lab@2024!` funzionante
- [ ] IP `192.168.56.20/24` visibile su `enp0s8`
- [ ] SSH accessibile: da WKS-LAB-01 esegui `ssh lab-admin@192.168.56.20` (dopo aver completato B4)

**Cosa potrebbe andare storto:**
1. *"Il nome dell'interfaccia non è enp0s8"* → Usa `ip addr show` per trovare il nome reale (può essere `eth1`, `ens34`, ecc.) e adatta il campo `ethernets:` nel file YAML
2. *"Netplan apply: permission denied"* → `sudo chmod 600 /etc/netplan/99-lab-static.yaml` poi riprova
3. *"L'IP non risponde al ping"* → Verifica in VirtualBox che Adapter 2 sia Host-Only (non Internal Network o Bridged)

---

### Esercizio B4: Creare VM3 — Windows 10 Workstation (WKS-LAB-01)

**Obiettivo.** Creare la postazione client che simula il PC dell'amministratore IT — da qui apriremo browser per GLPI e Grafana, userai Remote Desktop verso i server, e lancerai PowerShell per amministrare Active Directory.

> **Analogia.** WKS-LAB-01 è la scrivania dell'amministratore IT. Da lì guarda i dashboard (Grafana), apre i ticket (GLPI), controlla i server (RDP) e digita comandi (PowerShell). È il punto di controllo centrale, non il luogo dove gira la logica del business.

**Step 1 — Scaricare Windows 10**

Usa il Media Creation Tool ufficiale Microsoft: `https://www.microsoft.com/software-download/windows10`

Seleziona "Create installation media for another PC" → ISO file → scegli la posizione dove salvarlo. Dimensione: circa 5 GB.

> Windows 10 funziona senza attivazione per 30 giorni — più che sufficiente per i tutorial del corso. Dopo puoi reinstallare o usare una chiave generica KMS per il lab.

**Step 2 — Creare la VM in VirtualBox**

| Parametro | Valore |
|---|---|
| Nome | WKS-LAB-01 |
| Tipo | Microsoft Windows |
| Versione | Windows 10 (64-bit) |
| RAM | 4096 MB |
| CPU | 2 |
| Disco | 40 GB, VDI, dinamico |

Network: Adapter 1 → NAT; Adapter 2 → Host-Only.

**Step 3 — Installare Windows 10**

Avvia la VM. Durante l'installazione:
- Quando chiede il product key: clicca **"I don't have a product key"**
- Edizione: **Windows 10 Pro** (necessaria per unirsi al dominio AD nei tutorial successivi)
- Tipo installazione: **Custom** → disco da 40 GB → Next
- Account: crea un account locale (non Microsoft); nome `lab-user`, password `Lab@2024!`

L'installazione richiede 20-30 minuti.

**Step 4 — Configurare IP Statico e Hostname**

```powershell
# Apri PowerShell come Amministratore su WKS-LAB-01
# Vedi le interfacce
Get-NetAdapter | Select-Object Name, Status

# Assegna IP statico
New-NetIPAddress `
    -InterfaceAlias "Ethernet 2" `
    -IPAddress "192.168.56.30" `
    -PrefixLength 24

# Configura DNS verso DC-LAB-01
Set-DnsClientServerAddress `
    -InterfaceAlias "Ethernet 2" `
    -ServerAddresses "192.168.56.10","8.8.8.8"

# Rinomina il computer e riavvia
Rename-Computer -NewName "WKS-LAB-01" -Force -Restart
```

**Checkpoint di verifica B4:**
- [ ] IP `192.168.56.30` su Ethernet 2 (verifica con `ipconfig /all`)
- [ ] Hostname `WKS-LAB-01` (verifica con `hostname` in PowerShell)
- [ ] Login con `lab-user` / `Lab@2024!` funzionante

---

### Esercizio B5: Verificare la Connettività Completa tra le VM

**Obiettivo.** Confermare che tutte e tre le VM comunicano correttamente sulla rete host-only prima di procedere con i tutorial successivi. Questo è il collaudo del lab.

> **Perché questo passaggio è critico?** Tutti i tutorial successivi assumono che le VM si vedano. Se la rete non funziona, ogni esercizio futuro fallirà con errori fuorvianti (es. "timeout" quando in realtà il problema è l'IP sbagliato). Meglio scoprirlo ora.

**Test da WKS-LAB-01 verso le altre VM:**

```powershell
# Da WKS-LAB-01, apri PowerShell

# Test connettività verso DC-LAB-01 (porta 3389 = Remote Desktop)
Write-Host "--- Test verso VM1 (DC-LAB-01 @ 192.168.56.10) ---"
Test-NetConnection -ComputerName 192.168.56.10 -Port 3389 |
    Select-Object ComputerName, RemotePort, TcpTestSucceeded

# Test connettività verso SRV-LINUX-01 (porta 22 = SSH)
Write-Host "--- Test verso VM2 (SRV-LINUX-01 @ 192.168.56.20) ---"
Test-NetConnection -ComputerName 192.168.56.20 -Port 22 |
    Select-Object ComputerName, RemotePort, TcpTestSucceeded
```

Output atteso:
```
--- Test verso VM1 (DC-LAB-01 @ 192.168.56.10) ---
ComputerName     RemotePort TcpTestSucceeded
------------     ---------- ----------------
192.168.56.10          3389             True

--- Test verso VM2 (SRV-LINUX-01 @ 192.168.56.20) ---
ComputerName     RemotePort TcpTestSucceeded
------------     ---------- ----------------
192.168.56.20              22             True
```

**Test da SRV-LINUX-01 verso le altre VM:**

```bash
# Da SRV-LINUX-01, nel terminale
echo "=== Test ping verso tutte le VM del lab ==="
for ip in 192.168.56.10 192.168.56.30; do
    risultato=$(ping -c 3 -W 2 $ip 2>&1 | grep -E "transmitted|rtt")
    echo "--- $ip ---"
    echo "$risultato"
done
```

Output atteso:
```
=== Test ping verso tutte le VM del lab ===
--- 192.168.56.10 ---
3 packets transmitted, 3 received, 0% packet loss, time 2002ms
rtt min/avg/max/mdev = 0.312/0.445/0.612/0.127 ms
--- 192.168.56.30 ---
3 packets transmitted, 3 received, 0% packet loss, time 2001ms
rtt min/avg/max/mdev = 0.289/0.401/0.534/0.103 ms
```

**Test SSH da WKS-LAB-01 a SRV-LINUX-01:**

```powershell
# Da WKS-LAB-01 (Windows 10 include SSH client da Windows 10 v1809+)
ssh lab-admin@192.168.56.20
# Risponde: "Are you sure you want to continue connecting? (yes/no)"
# Digita: yes
# Password: Lab@2024!
# Appare il prompt: lab-admin@srv-linux-01:~$
# Per uscire digita: exit
```

**Checkpoint di verifica B5:**
- [ ] WKS-LAB-01 → DC-LAB-01: `TcpTestSucceeded: True` sulla porta 3389
- [ ] WKS-LAB-01 → SRV-LINUX-01: `TcpTestSucceeded: True` sulla porta 22
- [ ] SRV-LINUX-01 → DC-LAB-01: ping 0% packet loss
- [ ] SRV-LINUX-01 → WKS-LAB-01: ping 0% packet loss
- [ ] SSH da WKS-LAB-01 a SRV-LINUX-01 funzionante (login riuscito)

**Cosa potrebbe andare storto:**
1. *"TcpTestSucceeded: False verso DC-LAB-01 porta 3389"* → RDP potrebbe essere disabilitato di default su Windows Server; abilitalo: su DC-LAB-01 vai in Settings → System → Remote Desktop → Enable Remote Desktop
2. *"Ping timeout tra VM"* → Il Windows Firewall di default blocca l'ICMP. Su DC-LAB-01 in PowerShell: `New-NetFirewallRule -Name "Allow-Ping-In" -Protocol ICMPv4 -IcmpType 8 -Direction Inbound -Action Allow`
3. *"Una VM non risponde affatto"* → Verifica che la VM sia accesa e che abbia l'IP corretto (`ipconfig /all` su Windows, `ip addr` su Linux)

---

### Esercizio B6: Snapshot Iniziali — Il Punto di Ripristino del Lab

**Obiettivo.** Creare un punto di ripristino per ogni VM prima di iniziare qualsiasi tutorial operativo. Se qualcosa va storto durante le esercitazioni, puoi tornare allo stato iniziale in meno di 60 secondi.

**Background.** Uno snapshot è una "fotografia" istantanea dello stato della VM: disco, configurazione, e opzionalmente RAM. Non è un backup completo (se il file `.vdi` viene eliminato, lo snapshot non serve), ma è un meccanismo di rollback rapido ideale durante l'apprendimento.

> **Regola d'oro del lab:** Prima di ogni esercizio che potrebbe modificare irreversibilmente il sistema, fai uno snapshot. Costa 30 secondi e ti risparmia ore di reinstallazione.

**Procedura — Per ogni VM (con la VM SPENTA):**

1. In VirtualBox, **spegni la VM** se è accesa (Machine → ACPI Shutdown, poi attendi lo spegnimento completo)
2. Seleziona la VM nell'elenco di VirtualBox
3. Menu Machine → **Take Snapshot** (oppure usa la scorciatoia Ctrl+Shift+S)
4. Compila i campi:
   - **Snapshot Name:** `0.1 - Setup Base Completato`
   - **Snapshot Description:** `IP statici configurati, hostname assegnati, connettività lab verificata`
5. Clicca OK

Ripeti per tutte e tre le VM: DC-LAB-01, SRV-LINUX-01, WKS-LAB-01.

**Come ripristinare uno snapshot se qualcosa va storto:**

1. In VirtualBox, seleziona la VM
2. Clicca l'icona **Snapshots** (in alto a destra nella finestra principale)
3. Seleziona `0.1 - Setup Base Completato`
4. Clicca **Restore** → al messaggio "Do you want to take a snapshot of the current machine state?" scegli **No** (a meno che tu non voglia salvare lo stato attuale prima di ripristinare)
5. La VM torna esattamente allo stato del setup iniziale: stesso IP, stesso hostname, stessa configurazione

**Checkpoint finale del lab — Ambiente Pronto:**
- [ ] Snapshot `0.1 - Setup Base Completato` presente su DC-LAB-01
- [ ] Snapshot `0.1 - Setup Base Completato` presente su SRV-LINUX-01
- [ ] Snapshot `0.1 - Setup Base Completato` presente su WKS-LAB-01
- [ ] Tutte e tre le VM si pingano tra loro senza packet loss
- [ ] SSH da WKS-LAB-01 verso SRV-LINUX-01 funzionante
- [ ] RDP da WKS-LAB-01 verso DC-LAB-01 funzionante (Start → Remote Desktop Connection → 192.168.56.10)

> **Punto di sincronizzazione.** Hai completato la costruzione dell'ambiente lab. Ogni tutorial successivo di questo corso partirà da questo stato e descriverà solo le modifiche incrementali necessarie per quell'argomento specifico. Non dovrai mai ripartire da zero.

---

## PART C: SISTEMATIZZARE — Dall'Esecuzione alla Governance

> Nei tutorial precedenti hai *fatto* le cose. In questa sezione impari a *documentare, automatizzare e strutturare* quelle stesse attività — la differenza tra un tecnico che sa fare e un professionista IT che può delegare, scalare e auditare il proprio lavoro.

---

### Progetto C1: SOP "Avvio e Verifica dell'Ambiente Lab"

**Obiettivo.** Scrivere un documento SOP (Standard Operating Procedure) che qualsiasi collega possa seguire per avviare il lab e verificarne lo stato, senza dover ricordare ogni passaggio a memoria.

**Perché i professionisti IT scrivono le SOP?** Tre motivi: (1) Riproducibilità — lo stesso risultato indipendentemente da chi esegue; (2) Onboarding — i nuovi arrivati diventano operativi più velocemente; (3) Audit — in caso di incidente, la SOP documenta cosa avrebbe dovuto succedere.

**Template SOP — `LAB-OPS-001: Avvio Ambiente Lab`**

Crea un file `sop_lab_startup.md` nella cartella `docs/` del tuo progetto (o Desktop se preferisci):

```markdown
# SOP LAB-OPS-001: Avvio e Verifica Ambiente Lab
**Versione:** 1.0  
**Data:** [data corrente]  
**Autore:** [tuo nome]  
**Revisore:** —  
**Applicabilità:** Ambiente lab locale VirtualBox  

---

## 1. Scopo
Descrive la procedura di avvio ordinato delle VM del lab e la verifica di connettività,
da eseguire all'inizio di ogni sessione di studio prima di iniziare qualsiasi tutorial.

## 2. Prerequisiti
- VirtualBox 7.x installato e funzionante
- Tutte e tre le VM create con snapshot "0.1 - Setup Base Completato"
- PC host con almeno 8 GB RAM libera

## 3. Responsabilità
| Ruolo | Azione |
|---|---|
| Lab Admin (tu) | Esecuzione della procedura |

## 4. Procedura

### 4.1 Sequenza di avvio (OBBLIGATORIO: avviare in questo ordine)
1. **VM1 — DC-LAB-01** → Avvia → Attendi login screen (circa 60-90 secondi)
2. **VM2 — SRV-LINUX-01** → Avvia → Attendi prompt testuale login
3. **VM3 — WKS-LAB-01** → Avvia → Attendi desktop Windows

> MOTIVO dell'ORDINE: DC-LAB-01 fornirà DNS e Active Directory agli altri; deve essere disponibile prima degli altri.

### 4.2 Verifica connettività (da WKS-LAB-01, PowerShell)
```powershell
Test-NetConnection 192.168.56.10 -Port 3389  # DC-LAB-01
Test-NetConnection 192.168.56.20 -Port 22    # SRV-LINUX-01
```
Entrambi devono rispondere TcpTestSucceeded: True.

### 4.3 Criteri di successo
- [ ] Tutte e tre le VM rispondono
- [ ] SSH verso SRV-LINUX-01 funzionante

## 5. Rollback
Se una VM non risponde: VirtualBox → seleziona VM → Snapshots → ripristina "0.1 - Setup Base Completato".

## 6. Storico revisioni
| Versione | Data | Autore | Descrizione |
|---|---|---|---|
| 1.0 | [data] | [nome] | Prima versione |
```

> **Connessione ITIL v4.** Questa SOP implementa la pratica *Service Configuration Management* (gestione delle configurazioni) e *Continual Improvement* (documentare le procedure per migliorarle nel tempo). Anche un lab personale beneficia delle stesse pratiche usate in ambienti enterprise.

---

### Progetto C2: Script di Health Check Automatizzato

**Obiettivo.** Scrivere uno script PowerShell che verifichi automaticamente lo stato dell'intero lab in un colpo solo, invece di ripetere i test manualmente ogni volta.

**Il principio.** Ogni operazione ripetitiva che esegui più di tre volte merita di essere automatizzata. Il health check del lab lo esegui all'inizio di ogni sessione — è il candidato perfetto.

Crea il file `lab_healthcheck.ps1` sulla postazione WKS-LAB-01 (es. in `C:\Lab\Scripts\`):

```powershell
# lab_healthcheck.ps1
# Health check completo per l'ambiente lab IT Operations
# Esegui da WKS-LAB-01 con: .\lab_healthcheck.ps1

$VMs = @(
    @{ Name = "DC-LAB-01";     IP = "192.168.56.10"; Port = 3389; Service = "RDP" },
    @{ Name = "SRV-LINUX-01";  IP = "192.168.56.20"; Port = 22;   Service = "SSH" },
    @{ Name = "WKS-LAB-01";    IP = "192.168.56.30"; Port = 445;  Service = "SMB" }
)

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  LAB HEALTH CHECK — $timestamp" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

$allOk = $true

foreach ($vm in $VMs) {
    $result = Test-NetConnection -ComputerName $vm.IP -Port $vm.Port -WarningAction SilentlyContinue
    
    if ($result.TcpTestSucceeded) {
        Write-Host "  OK  $($vm.Name) ($($vm.IP)) — $($vm.Service) porta $($vm.Port)" -ForegroundColor Green
    } else {
        Write-Host "  FAIL $($vm.Name) ($($vm.IP)) — $($vm.Service) porta $($vm.Port) NON RAGGIUNGIBILE" -ForegroundColor Red
        $allOk = $false
    }
}

Write-Host ""
if ($allOk) {
    Write-Host "  [OK] Lab completamente operativo. Puoi iniziare il tutorial." -ForegroundColor Green
} else {
    Write-Host "  [ATTENZIONE] Alcuni componenti non rispondono. Verifica le VM in VirtualBox." -ForegroundColor Yellow
    Write-Host "  Consulta la SOP LAB-OPS-001 per la procedura di rollback." -ForegroundColor Yellow
}
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
```

**Eseguire lo script:**

```powershell
# Dalla cartella dove hai salvato lo script
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser  # solo la prima volta
.\lab_healthcheck.ps1
```

Output atteso (lab funzionante):
```
============================================
  LAB HEALTH CHECK — 2026-07-15 09:30:45
============================================
  OK  DC-LAB-01 (192.168.56.10) — RDP porta 3389
  OK  SRV-LINUX-01 (192.168.56.20) — SSH porta 22
  OK  WKS-LAB-01 (192.168.56.30) — SMB porta 445

  [OK] Lab completamente operativo. Puoi iniziare il tutorial.
============================================
```

> **Estensione proposta.** Nel tutorial ops02 (Manutenzione Preventiva) imparerai a schedulare questo script con Task Scheduler per farlo girare automaticamente ogni mattina alle 08:00 e inviarti un report via email.

---

### Progetto C3: Connessione al Framework ITIL

**Obiettivo.** Capire come le attività che hai appena eseguito nel lab corrispondono a pratiche reali del framework ITIL v4, il framework di governance IT più usato nelle aziende italiane ed europee.

| Attività nel Lab | Pratica ITIL v4 Corrispondente | Perché Conta |
|---|---|---|
| Setup ambiente VM con IP fissi | **Infrastructure and Platform Management** | Gestione infrastruttura sistematica e documentata |
| Creazione snapshot prima di ogni modifica | **Change Enablement** | Ogni cambiamento deve avere un rollback plan |
| Scrittura SOP LAB-OPS-001 | **Knowledge Management** | La conoscenza documentata è un asset aziendale |
| Health check automatizzato | **Service Monitoring and Event Management** | I problemi vanno rilevati proattivamente, non aspettando che gli utenti si lamentino |
| Sequenza di avvio DC prima degli altri | **Service Dependency Management** | Capire le dipendenze tra servizi evita outage a cascata |
| Test di connettività sistematici | **Service Validation and Testing** | Nessun sistema in produzione senza test verificati |

**Come scala in produzione?**

Il lab usa 3 VM su un PC. Un ambiente enterprise potrebbe avere 300 server distribuiti su 5 datacenter. Le pratiche sono identiche — cambia solo la scala:

- Invece di VirtualBox, VMware vSphere o Azure
- Invece di uno script PowerShell, un sistema di monitoring professionale (Zabbix, Prometheus)
- Invece di una SOP Word, un sistema di knowledge management (Confluence, SharePoint)
- Invece di snapshot manuali, snapshot automatizzate con retention policy di 30 giorni

Questa è la progressione che seguirai nei tutorial successivi.

---

## Checklist di Validazione — Tutorial ops00 Completato

Verifica di aver completato ogni elemento prima di procedere al tutorial ops01:

### Fondamenti (Part A)
- [ ] Sai spiegare la differenza tra i 5 tipi di manutenzione IT (correttiva, preventiva, predittiva, proattiva, evolutiva)
- [ ] Sai descrivere cos'è una VM usando almeno un'analogia che funziona
- [ ] Sai elencare le componenti del lab (3 VM, rete host-only, hypervisor)

### Ambiente Lab (Part B)
- [ ] VirtualBox 7.x installato con Extension Pack
- [ ] Rete Host-Only 192.168.56.0/24 creata, DHCP disabilitato
- [ ] DC-LAB-01 con IP 192.168.56.10, hostname DC-LAB-01, Windows Server 2022 Desktop Experience
- [ ] SRV-LINUX-01 con IP 192.168.56.20, hostname srv-linux-01, Ubuntu Server 22.04 + SSH
- [ ] WKS-LAB-01 con IP 192.168.56.30, hostname WKS-LAB-01, Windows 10 Pro
- [ ] Connettività verificata: tutte le VM si pingano, SSH funzionante
- [ ] Snapshot "0.1 - Setup Base Completato" presente su tutte e tre le VM

### Governance (Part C)
- [ ] SOP LAB-OPS-001 creata e salvata
- [ ] Script `lab_healthcheck.ps1` creato e testato su WKS-LAB-01
- [ ] Sai associare almeno 3 attività del lab a pratiche ITIL v4

---

## Appendice A: Comandi Essenziali del Lab

### Windows PowerShell (DC-LAB-01 e WKS-LAB-01)

```powershell
# Rete
ipconfig /all                          # mostra IP, MAC, DNS di tutte le interfacce
Get-NetAdapter                         # lista adattatori di rete
Test-NetConnection IP -Port N          # test connettività TCP verso IP:porta
Resolve-DnsName nome.dominio           # risoluzione DNS

# Sistema
hostname                               # nome del computer
Get-ComputerInfo | Select-Object *     # info complete sul sistema
Get-WmiObject Win32_OperatingSystem    # versione OS
systeminfo                             # riepilogo sistema

# Servizi
Get-Service                            # lista tutti i servizi
Get-Service -Name "NomeSvc" | Select-Object Name, Status, StartType
Start-Service "NomeSvc"               # avvia un servizio
Stop-Service "NomeSvc"                # ferma un servizio
Restart-Service "NomeSvc"             # riavvia un servizio
```

### Linux Bash (SRV-LINUX-01)

```bash
# Rete
ip addr show                  # mostra IP di tutte le interfacce
ip route show                 # tabella di routing
ping -c 4 IP                  # ping 4 pacchetti verso IP
ss -tlnp                      # porte TCP in ascolto (sostituto di netstat)
curl -s http://IP:PORTA       # test HTTP verso un servizio

# Sistema
hostname                      # nome del sistema
uname -a                      # kernel e architettura
uptime                        # quanto è acceso il sistema
free -h                       # memoria RAM disponibile
df -h                         # spazio disco per filesystem

# Servizi (systemd)
systemctl status servizio     # stato di un servizio
systemctl start servizio      # avvia un servizio
systemctl stop servizio       # ferma un servizio
systemctl restart servizio    # riavvia un servizio
systemctl enable servizio     # abilita avvio automatico al boot
journalctl -u servizio -f     # log in tempo reale di un servizio

# File e permessi
ls -la                        # lista file con permessi
chmod 600 file                # imposta permessi rw solo per proprietario
sudo comando                  # esegui comando come root
cat /var/log/syslog | tail -50 # ultime 50 righe del log di sistema
```

---

## Appendice B: Tabella Comparativa delle Tre VM

| Caratteristica | DC-LAB-01 | SRV-LINUX-01 | WKS-LAB-01 |
|---|---|---|---|
| **OS** | Windows Server 2022 | Ubuntu Server 22.04 | Windows 10 Pro |
| **Ruolo** | Domain Controller, DNS, DHCP | Monitoring, Ticketing, Docker | Postazione Admin |
| **IP** | 192.168.56.10 | 192.168.56.20 | 192.168.56.30 |
| **Hostname** | DC-LAB-01 | srv-linux-01 | WKS-LAB-01 |
| **RAM** | 4-8 GB | 4 GB | 4 GB |
| **Disco** | 60 GB | 40 GB | 40 GB |
| **GUI** | Sì (Desktop Experience) | No (solo terminale) | Sì |
| **Accesso remoto** | RDP (porta 3389) | SSH (porta 22) | RDP (porta 3389) |
| **Credenziali** | Administrator / Lab@2024! | lab-admin / Lab@2024! | lab-user / Lab@2024! |
| **Tutorials principali** | ops01, ops03a, ops04b | ops04a, ops07, ops08 | tutti (client) |

---

## Appendice C: Mappa delle Dipendenze tra VM

```
                    HOST (il tuo PC fisico)
                         |
                    VirtualBox
                         |
          +--------------+---------------+
          |              |               |
    DC-LAB-01      SRV-LINUX-01    WKS-LAB-01
    .56.10          .56.20           .56.30
    (VM1)           (VM2)           (VM3)
    DNS Server      SSH Server       Admin PC
    AD DS           Monitoring       RDP Client
    DHCP            Docker           Browser
          |              |               |
          +---- RETE HOST-ONLY 192.168.56.0/24 ----+
                         |
          (ogni VM ha anche Adapter 1 = NAT per internet)
```

**Ordine critico di avvio:** VM1 → VM2 → VM3
- VM2 e VM3 dipenderanno da VM1 per il DNS una volta configurato Active Directory
- Avviare VM2 e VM3 prima di VM1 causa ritardi di risoluzione DNS

---

## Riferimenti

| Risorsa | URL / Posizione | Argomento |
|---|---|---|
| VirtualBox Downloads | virtualbox.org/wiki/Downloads | Hypervisor + Extension Pack |
| VirtualBox User Manual | virtualbox.org/manual | Guida completa VirtualBox |
| Windows Server 2022 Eval | microsoft.com/evalcenter/evaluate-windows-server-2022 | ISO valutazione 180gg |
| Ubuntu Server 22.04 | ubuntu.com/download/server | ISO Ubuntu Server LTS |
| Netplan Documentation | netplan.io | Configurazione rete Ubuntu |
| ITIL 4 Foundation (libro) | axelos.com | Framework ITIL ufficiale |
| Syllabus del corso | `../00-SYLLABUS.md` | Struttura e obiettivi del corso |
| Tutorial successivo | `tutorial_ops01_ch1a_itil_foundations_lab.md` | Framework ITIL v4 in dettaglio |

---

*Fine tutorial ops00 — Prossimo: `tutorial_ops01_ch1a_itil_foundations_lab.md`*
