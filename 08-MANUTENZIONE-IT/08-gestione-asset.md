# Gestione Asset IT — Guida Completa

> **Modulo 08** · **Tempo:** 60 min · **Aggiornamento:** 2026-04-27

## Idee guida

1. **Asset catalog completo: HW + SW + license + contratti.** Singolo source of truth.
2. **License compliance audit: trimestrale.** Vendor audit costa 10x di buona disciplina.
3. **Lifecycle tracking: acquisto → deploy → maintenance → retirement.**
4. **CMDB integration: relationship CI = visibilita impatto change.**


## Indice

1. [Panoramica](#panoramica)
2. [Inventario e Catalogazione](#inventario-e-catalogazione)
   - [Inventario Hardware](#inventario-hardware)
   - [Inventario Software](#inventario-software)
   - [Inventario Rete](#inventario-rete)
3. [Ciclo di Vita Asset](#ciclo-di-vita-asset)
   - [Fasi del Ciclo di Vita](#fasi-del-ciclo-di-vita)
   - [Procurement](#procurement)
   - [Deployment e Assegnazione](#deployment-e-assegnazione)
4. [Gestione Garanzie](#gestione-garanzie)
5. [Gestione Licenze Software](#gestione-licenze-software)
6. [Pianificazione Refresh e EOL/EOS](#pianificazione-refresh-e-eoleos)
7. [Decommissioning e Smaltimento](#decommissioning-e-smaltimento)
8. [Strumenti ITAM](#strumenti-itam)
9. [Reportistica Asset](#reportistica-asset)
10. [Best Practices](#best-practices)
11. [Troubleshooting](#troubleshooting)
12. [Framework ISO/IEC 19770 e Standard ITAM](#framework-isoiec-19770-e-standard-itam)
    - [Struttura dello Standard ISO 19770](#struttura-dello-standard-iso-19770)
    - [Tiers di Conformita ISO 19770-1](#tiers-di-conformita-iso-19770-1)
    - [Integrazione con Altri Standard ISO](#integrazione-con-altri-standard-iso)
13. [Modello di Maturita ITAM](#modello-di-maturita-itam)
    - [Livelli di Maturita](#livelli-di-maturita)
    - [Assessment della Maturita](#assessment-della-maturita)
    - [Roadmap di Evoluzione](#roadmap-di-evoluzione)
14. [Gestione Asset Cloud e SaaS](#gestione-asset-cloud-e-saas)
    - [Cloud Asset Management](#cloud-asset-management)
    - [SaaS Management Platform](#saas-management-platform)
    - [FinOps e Ottimizzazione dei Costi Cloud](#finops-e-ottimizzazione-dei-costi-cloud)
    - [Governance Multi-Cloud](#governance-multi-cloud)
15. [Shadow IT e Shadow AI](#shadow-it-e-shadow-ai)
    - [Dimensione del Fenomeno](#dimensione-del-fenomeno)
    - [Tecniche di Rilevamento Avanzate](#tecniche-di-rilevamento-avanzate)
    - [Shadow AI: La Nuova Frontiera](#shadow-ai-la-nuova-frontiera)
    - [Strategia di Contenimento](#strategia-di-contenimento)
16. [Integrazione CMDB e ITSM](#integrazione-cmdb-e-itsm)
    - [CMDB vs Asset Database](#cmdb-vs-asset-database)
    - [Relationship Mapping e Impact Analysis](#relationship-mapping-e-impact-analysis)
    - [Integrazione con Change Management](#integrazione-con-change-management)
    - [Federation e Data Quality](#federation-e-data-quality)
17. [Conformita Normativa e GDPR](#conformita-normativa-e-gdpr)
    - [GDPR e Ciclo di Vita degli Asset](#gdpr-e-ciclo-di-vita-degli-asset)
    - [Audit Trail e Tracciabilita](#audit-trail-e-tracciabilita)
    - [Data Processing Agreement per ITAD](#data-processing-agreement-per-itad)
18. [Vendor Audit: Preparazione e Difesa](#vendor-audit-preparazione-e-difesa)
    - [Anatomia di un Vendor Audit](#anatomia-di-un-vendor-audit)
    - [Preparazione Proattiva](#preparazione-proattiva)
    - [Gestione dell'Audit in Corso](#gestione-dellaudit-in-corso)
    - [Scenari di Audit per Vendor](#scenari-di-audit-per-vendor)
19. [Automazione e Intelligenza Artificiale nell'ITAM](#automazione-e-intelligenza-artificiale-nellitam)
    - [AI per la Discovery e Normalizzazione](#ai-per-la-discovery-e-normalizzazione)
    - [Predictive Asset Management](#predictive-asset-management)
    - [Agentic AI e Automazione dei Workflow](#agentic-ai-e-automazione-dei-workflow)
20. [Policy e Governance ITAM](#policy-e-governance-itam)
    - [Template Policy ITAM Aziendale](#template-policy-itam-aziendale)
    - [RACI Matrix per ITAM](#raci-matrix-per-itam)
    - [Metriche di Governance](#metriche-di-governance)

---

## Panoramica

La **Gestione degli Asset IT** (IT Asset Management, ITAM) rappresenta l'insieme di processi, politiche e strumenti finalizzati a tracciare, gestire e ottimizzare l'intero patrimonio tecnologico di un'organizzazione durante il suo ciclo di vita completo. Un programma ITAM maturo non si limita alla mera catalogazione degli apparati: esso integra aspetti finanziari, contrattuali, operativi e di conformita in un framework coerente che supporta le decisioni strategiche dell'IT.

L'importanza di una gestione asset strutturata si manifesta in molteplici ambiti:

- **Controllo dei costi**: La conoscenza precisa degli asset in possesso evita acquisti duplicati, permette di negoziare contratti di volume e ottimizza l'allocazione delle risorse. Senza un inventario accurato, le organizzazioni tendono a sovra-approvvigionare (over-provisioning) del 15-30% rispetto alle reali necessita.
- **Conformita normativa e licenze**: Le verifiche di audit software (compliance audit) possono comportare penali significative in caso di utilizzo non autorizzato di licenze. Un ITAM efficace garantisce che ogni installazione software sia correttamente licenziata.
- **Sicurezza**: Asset non tracciati rappresentano potenziali vettori di attacco. Dispositivi con sistemi operativi non aggiornati, software EOL o configurazioni non conformi aumentano la superficie di attacco dell'organizzazione.
- **Pianificazione strategica**: La conoscenza dell'eta, delle prestazioni e dello stato di garanzia degli asset consente di pianificare refresh e investimenti con anticipo, evitando emergenze e spese impreviste.
- **Efficienza operativa**: Quando un tecnico riceve una segnalazione, l'accesso immediato alle informazioni sull'asset (configurazione, storia delle riparazioni, software installato, utente assegnatario) riduce drasticamente i tempi di diagnosi e risoluzione.

Il framework ITAM si colloca all'intersezione tra ITSM (IT Service Management), gestione finanziaria e governance IT. Lo standard **ISO/IEC 19770** definisce le best practice per il Software Asset Management (SAM), mentre ITIL v4 include la pratica "IT Asset Management" come componente fondamentale del Service Value System. Il presente documento adotta un approccio pratico e operativo, fornendo procedure, strumenti e template immediatamente applicabili in ambienti di produzione reali.

---

## Inventario e Catalogazione

La base di ogni programma ITAM e un inventario completo, accurato e costantemente aggiornato. Un inventario incompleto o obsoleto e peggio dell'assenza totale di inventario, poiche genera una falsa sicurezza che porta a decisioni errate.

### Inventario Hardware

L'inventario hardware deve coprire ogni dispositivo fisico che fa parte dell'infrastruttura IT, inclusi ma non limitati a:

**Categorie di asset da tracciare:**

| Categoria | Esempi | Ciclo Refresh Tipico |
|-----------|--------|---------------------|
| Server fisici | Rack server, tower server, blade | 5-7 anni |
| Workstation | Desktop, all-in-one | 4-5 anni |
| Laptop | Notebook, ultrabook | 3-4 anni |
| Dispositivi mobili | Smartphone, tablet aziendali | 2-3 anni |
| Periferiche | Monitor, stampanti, scanner | 5-7 anni |
| Storage | NAS, SAN, tape library | 5-7 anni |
| Apparati di rete | Switch, router, firewall, access point | 7-10 anni |
| Apparati UPS | Gruppi di continuita, batterie | 3-5 anni (batterie) |
| Infrastruttura DC | Rack, PDU, sistemi di raffreddamento | 10-15 anni |

**Dati da raccogliere per ogni asset hardware:**

Per ciascun dispositivo, il record di inventario deve includere come minimo i seguenti campi:

```
Identificativo Asset:
  - Asset Tag (codice interno univoco, es. HW-SRV-0042)
  - Codice a barre / QR code
  - Numero di serie (serial number del produttore)
  - MAC address (per dispositivi di rete)

Informazioni Prodotto:
  - Produttore (es. Dell, HP, Lenovo)
  - Modello (es. PowerEdge R750)
  - Categoria (server, laptop, switch, ecc.)
  - Specifiche tecniche (CPU, RAM, storage, GPU)

Informazioni Commerciali:
  - Data di acquisto
  - Fornitore
  - Numero ordine di acquisto (PO)
  - Costo di acquisto (CAPEX)
  - Numero fattura

Garanzia e Supporto:
  - Data inizio garanzia
  - Data scadenza garanzia
  - Tipo di supporto (NBD, 4h, 24/7)
  - Contratto di manutenzione associato
  - Numero contratto supporto

Collocazione:
  - Sede / Edificio
  - Piano / Stanza
  - Data center / Rack / Posizione U (per apparati rack-mounted)
  - Utente assegnatario (per dispositivi personali)
  - Dipartimento

Stato:
  - In uso / In magazzino / In riparazione / Dismesso
  - Data ultima modifica stato
  - Data prevista dismissione
```

**Strumenti di Discovery e Inventario:**

L'inventario manuale e impraticabile per organizzazioni con piu di poche decine di dispositivi. Gli strumenti di discovery automatico scansionano la rete e raccolgono informazioni sugli asset connessi:

- **GLPI + FusionInventory**: Soluzione open-source completa. GLPI funge da CMDB/ITSM, FusionInventory e l'agente che esegue la discovery e l'inventario. L'agente puo essere installato su ogni endpoint e invia periodicamente i dati al server GLPI. Supporta WMI per Windows, SNMP per dispositivi di rete, e raccoglie informazioni dettagliate su hardware e software installato.

- **Snipe-IT**: Piattaforma open-source web-based specificamente progettata per l'asset management. Interfaccia moderna e intuitiva, supporto per codici a barre e QR code, gestione checkout/checkin degli asset, reportistica integrata. Ideale per organizzazioni di medie dimensioni che necessitano di una soluzione dedicata e snella.

- **NetBox**: Originariamente sviluppato da DigitalOcean, NetBox e una soluzione open-source focalizzata sulla documentazione dell'infrastruttura di rete e data center. Eccelle nella modellazione di rack, dispositivi, cablaggio, IPAM e circuiti. Meno adatto alla gestione degli endpoint utente, eccellente per l'infrastruttura core.

- **LANSweeper**: Soluzione commerciale con potenti capacita di agentless discovery. Scansiona la rete tramite WMI, SSH, SNMP e altri protocolli per costruire un inventario completo senza richiedere l'installazione di agenti sugli endpoint. Ottimo per ambienti eterogenei e di grandi dimensioni.

- **PDQ Inventory**: Strumento commerciale specializzato in ambienti Windows. Esegue scansioni agentless tramite WMI e fornisce informazioni dettagliate su hardware, software, configurazioni Windows, aggiornamenti installati e molto altro. Si integra con PDQ Deploy per la distribuzione software.

**Inventario Automatico vs Manuale:**

L'approccio consigliato prevede una combinazione di entrambi i metodi:

```
Discovery Automatica (schedulata):
  - Scansione rete settimanale per nuovi dispositivi
  - Aggiornamento quotidiano inventario tramite agenti
  - Alert per dispositivi non autorizzati (rogue device detection)

Verifica Manuale (periodica):
  - Audit fisico trimestrale per aree critiche (data center)
  - Audit fisico semestrale per endpoint utente
  - Riconciliazione inventario fisico vs logico
  - Verifica asset tag e leggibilita etichette
```

**Asset Tagging con Codici a Barre e QR Code:**

L'etichettatura fisica degli asset e fondamentale per collegare il mondo fisico al database logico:

- Utilizzare etichette resistenti e durevoli (poliestere laminato o alluminio anodizzato per ambienti data center)
- Schema di numerazione strutturato: `[TIPO]-[SEDE]-[SEQUENZIALE]` (es. `SRV-MI01-0023`)
- QR code preferibili ai codici a barre lineari: contengono piu informazioni e sono leggibili anche se parzialmente danneggiati
- Posizionamento coerente: sempre nella stessa posizione su dispositivi simili per facilitare l'identificazione rapida
- Registro del posizionamento fisico: per asset rack-mounted, registrare data center, fila, rack e posizione U

### Inventario Software

L'inventario software e complementare a quello hardware e riveste un'importanza critica per la gestione delle licenze e la conformita normativa.

**Tipologie di Licenze Software:**

| Tipo Licenza | Descrizione | Esempio |
|-------------|-------------|---------|
| Per-seat / Per-user | Una licenza per ogni utente che utilizza il software | Microsoft 365 Business |
| Per-device | Una licenza per ogni dispositivo su cui il software e installato | Antivirus endpoint |
| Per-core / Per-CPU | Licenziamento basato sui core/CPU del server | SQL Server Enterprise |
| Subscription | Abbonamento periodico (mensile/annuale) | Adobe Creative Cloud |
| OEM | Licenza legata al dispositivo specifico, non trasferibile | Windows OEM pre-installato |
| Volume Licensing (VL) | Licenze acquistate in blocco con condizioni agevolate | Microsoft Open/Select/EA |
| Perpetual | Acquisto una-tantum, diritto d'uso permanente | AutoCAD 2023 perpetua |
| Concurrent / Floating | Numero limitato di utilizzi contemporanei | Software CAD floating |
| Site License | Utilizzo illimitato per una sede/organizzazione | Licenza campus universitario |
| Freemium / Open-source | Gratuita con limitazioni o completamente libera | LibreOffice, 7-Zip |

**Audit Software Installato — Comandi Operativi:**

Per rilevare il software installato sugli endpoint, si utilizzano i seguenti comandi e strumenti:

```powershell
# Windows — PowerShell: elenco software installato
Get-CimInstance -ClassName Win32_Product | Select-Object Name, Version, Vendor, InstallDate |
    Sort-Object Name | Export-Csv -Path "C:\audit\software_inventory.csv" -NoTypeInformation

# Windows — Registro di sistema (piu completo e veloce di Win32_Product)
$paths = @(
    "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*",
    "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*"
)
Get-ItemProperty $paths | Where-Object { $_.DisplayName } |
    Select-Object DisplayName, DisplayVersion, Publisher, InstallDate |
    Sort-Object DisplayName | Export-Csv -Path "C:\audit\software_registry.csv" -NoTypeInformation

# Windows — Elenco programmi Microsoft Store (UWP/AppX)
Get-AppxPackage | Select-Object Name, Version, Publisher |
    Export-Csv -Path "C:\audit\appx_packages.csv" -NoTypeInformation
```

```bash
# Linux (Debian/Ubuntu) — Elenco pacchetti installati
dpkg -l | awk '/^ii/ {print $2, $3, $4}' > /tmp/software_inventory_deb.txt

# Linux (RHEL/CentOS/Fedora) — Elenco pacchetti installati
rpm -qa --queryformat '%{NAME} %{VERSION}-%{RELEASE} %{VENDOR}\n' | sort > /tmp/software_inventory_rpm.txt

# Linux — Software installato fuori dal package manager (snap, flatpak)
snap list 2>/dev/null > /tmp/snap_packages.txt
flatpak list 2>/dev/null > /tmp/flatpak_packages.txt

# macOS — Elenco applicazioni
system_profiler SPApplicationsDataType > /tmp/software_inventory_mac.txt
```

**Rilevamento Shadow IT:**

La Shadow IT comprende software, servizi cloud e dispositivi utilizzati dai dipendenti senza l'approvazione o la conoscenza del dipartimento IT. Le strategie di rilevamento includono:

- Analisi del traffico DNS e dei log del proxy web per identificare servizi SaaS non autorizzati
- Scansione periodica degli endpoint per rilevare software non presente nella whitelist aziendale
- Monitoraggio delle sottoscrizioni tramite analisi delle note spese (servizi acquistati con carte aziendali)
- Cloud Access Security Broker (CASB) per monitorare l'accesso a servizi cloud
- Politiche chiare di acceptable use e processi semplificati per la richiesta di nuovo software, in modo da ridurre l'incentivo al ricorso alla Shadow IT

**Rilevamento Software Non Autorizzato:**

```powershell
# PowerShell — Confronto tra software installato e whitelist approvata
$whitelist = Get-Content "C:\admin\approved_software.txt"
$installed = Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*" |
    Where-Object { $_.DisplayName } | Select-Object -ExpandProperty DisplayName

$unauthorized = $installed | Where-Object { $_ -notin $whitelist }
if ($unauthorized) {
    Write-Warning "Software non autorizzato rilevato:"
    $unauthorized | ForEach-Object { Write-Output "  - $_" }
}
```

### Inventario Rete

L'inventario dei dispositivi di rete richiede un approccio specifico data la natura di questi apparati:

**Dispositivi da tracciare:**

- Switch (access, distribution, core)
- Router
- Firewall (hardware e virtual appliance)
- Access Point Wi-Fi e controller wireless
- Load balancer
- VPN concentrator
- Modem e apparati WAN

**IP Address Management (IPAM):**

La gestione degli indirizzi IP e parte integrante dell'inventario di rete. Un sistema IPAM deve tracciare:

- Allocazione delle subnet (pianificazione dello spazio di indirizzamento)
- Assegnazione IP statica (server, stampanti, apparati di rete)
- Scope DHCP e relative configurazioni
- Record DNS associati
- VLAN mapping e assegnazione porte

Strumenti IPAM consigliati:
- **NetBox** (open-source, eccellente per IPAM e documentazione infrastruttura)
- **phpIPAM** (open-source, dedicato esclusivamente alla gestione IP)
- **Infoblox** (enterprise, IPAM + DNS + DHCP integrato)
- **GLPI** con plugin IPAM

**Documentazione di Rete — Port Mapping:**

Per ogni switch e apparato di rete, documentare:

```
Switch: SW-CORE-01 (Cisco Catalyst 9300-48P)
Location: DC-Milano, Rack A3, U20
-----------------------------------------------
Porta    | VLAN | Descrizione          | Dispositivo collegato
---------|------|----------------------|----------------------
Gi1/0/1  | 100  | Uplink Router        | RTR-CORE-01 Gi0/0/0
Gi1/0/2  | 100  | Uplink SW-DIST-01    | SW-DIST-01 Gi1/0/48
Gi1/0/3  | 200  | Server ESXi Host 01  | SRV-ESX-01 NIC1
Gi1/0/4  | 200  | Server ESXi Host 01  | SRV-ESX-01 NIC2
...
Gi1/0/48 | 999  | Non utilizzata       | — (shutdown)
```

**Diagrammi di Rete:**

La documentazione visiva della rete e essenziale. Strumenti consigliati:

- **draw.io (diagrams.net)**: Gratuito, open-source, disponibile come applicazione web o desktop. Ampia libreria di simboli di rete (Cisco, generic networking). Supporta il salvataggio su cloud o in locale.
- **NetBox**: Genera automaticamente diagrammi di interconnessione basati sui dati inseriti nel CMDB.
- **Microsoft Visio**: Standard de facto in ambienti enterprise, ampie librerie di stencil, integrazione con Active Directory per auto-discovery.

Tipologie di diagrammi da mantenere:
- Diagramma logico L3 (topologia routing, subnet, VLAN)
- Diagramma fisico L1 (cablaggio, rack layout, interconnessioni)
- Diagramma L2 (domini di broadcast, trunk, spanning tree)
- Diagramma WAN/connettivita esterna (collegamenti ISP, VPN site-to-site)

---

## Ciclo di Vita Asset

### Fasi del Ciclo di Vita

Ogni asset IT attraversa un ciclo di vita ben definito, dalla richiesta iniziale fino allo smaltimento finale. La gestione strutturata di ogni fase garantisce tracciabilita, controllo dei costi e conformita normativa.

```
[1. Procurement] --> [2. Receiving] --> [3. Deployment] --> [4. Operation]
                                                                |
                                                                v
              [7. Disposal] <-- [6. Retirement] <-- [5. Maintenance]
```

**Fase 1 — Procurement (Approvvigionamento):**
Definizione dei requisiti, valutazione fornitori, approvazione budget, emissione ordine di acquisto.

**Fase 2 — Receiving (Ricezione):**
Verifica della corrispondenza tra merce ricevuta e ordine, registrazione nell'inventario, applicazione dell'asset tag, aggiornamento del database CMDB.

**Fase 3 — Deployment (Distribuzione):**
Configurazione secondo lo standard aziendale (hardening, installazione software, join al dominio), assegnazione all'utente o alla collocazione finale.

**Fase 4 — Operation (Operativita):**
Fase di utilizzo produttivo. Include aggiornamenti regolari, monitoraggio delle prestazioni, gestione degli incidenti.

**Fase 5 — Maintenance (Manutenzione):**
Interventi di riparazione, sostituzione componenti (RAM, dischi, batterie), upgrade hardware, estensione garanzie se necessario.

**Fase 6 — Retirement (Dismissione):**
L'asset raggiunge la fine della sua vita utile. Viene rimosso dall'ambiente produttivo, i dati vengono cancellati in modo sicuro, le licenze software vengono recuperate (license harvesting).

**Fase 7 — Disposal (Smaltimento):**
Smaltimento fisico conforme alle normative ambientali (RAEE/WEEE), eventuale donazione o rivendita, ottenimento del certificato di distruzione se applicabile.

### Procurement

Il processo di approvvigionamento deve essere strutturato per garantire acquisti coerenti con le esigenze aziendali e ottimizzati nei costi:

**Workflow di Richiesta e Approvazione:**

```
Utente/Responsabile               IT Department                  Direzione/Acquisti
       |                               |                               |
       |--- Richiesta asset ---------> |                               |
       |                               |--- Valutazione tecnica        |
       |                               |--- Verifica budget            |
       |                               |--- Scelta configurazione std  |
       |                               |                               |
       |                               |--- Richiesta approvazione --> |
       |                               |                               |--- Approvazione
       |                               | <--- Ordine autorizzato ------|
       |                               |                               |
       |                               |--- Emissione PO al fornitore |
       |                               |--- Tracking consegna         |
       | <--- Notifica assegnazione ---|                               |
```

**Gestione Fornitori:**

Mantenere un albo fornitori qualificati con le seguenti informazioni:
- Ragione sociale, partita IVA, contatti commerciali e tecnici
- Condizioni contrattuali (sconti volume, tempi di consegna, politiche di reso)
- Storico ordini e valutazione prestazioni (qualita, puntualita, assistenza post-vendita)
- Certificazioni pertinenti (ISO 9001, ISO 14001 per lo smaltimento)

**Configurazioni Standard:**

Definire profili di configurazione standard per ridurre la complessita e ottenere economie di scala:

```
Profilo: WKS-STANDARD (Workstation Ufficio Standard)
  CPU:    Intel Core i5 (gen. attuale o precedente)
  RAM:    16 GB DDR5
  Storage: 512 GB NVMe SSD
  Display: 24" Full HD IPS
  OS:     Windows 11 Pro
  Note:   Per attivita office, email, navigazione web

Profilo: WKS-POWER (Workstation Utente Avanzato)
  CPU:    Intel Core i7 / AMD Ryzen 7
  RAM:    32 GB DDR5
  Storage: 1 TB NVMe SSD
  GPU:    Dedicata (NVIDIA RTX 4060 o equiv.)
  Display: 27" QHD IPS
  OS:     Windows 11 Pro
  Note:   Per sviluppo software, grafica, CAD leggero

Profilo: SRV-STANDARD (Server Rack 1U)
  CPU:    2x Intel Xeon Silver
  RAM:    128 GB ECC DDR5
  Storage: 4x 1.92 TB SAS SSD (RAID 10)
  NIC:    4x 10 GbE
  PSU:    2x ridondanti
  iDRAC/iLO: Enterprise con licenza
  Note:   Virtualizzazione, database, application server
```

**Considerazioni di Budget (CAPEX vs OPEX):**

| Aspetto | CAPEX (Acquisto) | OPEX (Leasing/DaaS) |
|---------|-----------------|---------------------|
| Costo iniziale | Elevato | Basso (canone mensile) |
| Proprietà | Dell'azienda | Del fornitore |
| Ammortamento | 3-5 anni | Non applicabile |
| Refresh | Responsabilità interna | Incluso nel contratto |
| Flessibilità | Bassa | Alta (scalabilità) |
| TCO a 5 anni | Generalmente inferiore | Generalmente superiore |
| Ideale per | Infrastruttura stabile | Endpoint con refresh rapido |

### Deployment e Assegnazione

Il processo di deployment deve essere standardizzato e documentato:

**Checklist di Deployment — Endpoint Utente:**

```
[ ] Asset registrato nel CMDB con tutti i campi compilati
[ ] Asset tag applicato e verificato
[ ] Immagine OS standard installata (da template MDT/SCCM/Intune)
[ ] Join al dominio Active Directory / Entra ID
[ ] Politiche di gruppo (GPO) applicate e verificate
[ ] Software standard installato (Office, antivirus, VPN client, ecc.)
[ ] Aggiornamenti Windows/macOS applicati (patch corrente)
[ ] Crittografia disco attivata (BitLocker/FileVault)
[ ] Agente di monitoraggio/inventory installato (es. FusionInventory)
[ ] Test funzionale completato (rete, stampa, applicazioni critiche)
[ ] Assegnazione a utente registrata nel CMDB
[ ] Modulo di presa in consegna firmato dall'utente
[ ] Documentazione consegnata all'utente (se necessario)
```

**Modulo di Assegnazione Asset:**

```
MODULO DI ASSEGNAZIONE ASSET IT
================================
Data: _______________
Asset Tag: _______________  Serial Number: _______________
Tipo: _______________       Modello: _______________

Assegnato a: _______________ (Nome e Cognome)
Dipartimento: _______________
Sede: _______________

L'utente dichiara di:
- Aver ricevuto l'asset in buone condizioni
- Impegnarsi a utilizzarlo secondo le policy aziendali
- Segnalare tempestivamente guasti o smarrimenti
- Restituire l'asset al termine del rapporto lavorativo

Firma utente: _______________  Firma IT: _______________
```

---

## Gestione Garanzie

La gestione proattiva delle garanzie e dei contratti di supporto e fondamentale per minimizzare i tempi di fermo e i costi di riparazione.

**Tracking delle Scadenze:**

Implementare un sistema di alert progressivi per le scadenze garanzia:

| Tempo alla Scadenza | Azione |
|---------------------|--------|
| 90 giorni | Notifica al responsabile IT: valutare estensione garanzia o piano di sostituzione |
| 60 giorni | Decisione sull'estensione: richiedere preventivo al vendor |
| 30 giorni | Ultima opportunita per estensione; se non estesa, pianificare ricambistica |
| Scaduta | Asset marcato come "fuori garanzia" nel CMDB; valutare incremento ricambi a magazzino |

**Verifica Garanzia Online per Vendor:**

La maggior parte dei produttori offre portali online per la verifica della garanzia tramite serial number:

- **Dell**: [dell.com/support](https://dell.com/support) — inserire il Service Tag
- **HP/HPE**: [support.hp.com](https://support.hp.com) — inserire il serial number o product number
- **Lenovo**: [pcsupport.lenovo.com](https://pcsupport.lenovo.com) — inserire il serial number o machine type
- **Cisco**: Cisco Commerce Workspace o Smart Net Total Care portal
- **Apple**: [checkcoverage.apple.com](https://checkcoverage.apple.com)

**Script di verifica garanzia batch (esempio Dell):**

```powershell
# Verifica garanzia Dell via API (richiede API key)
$apiKey = "YOUR_DELL_API_KEY"
$serviceTags = @("ABC1234", "DEF5678", "GHI9012")

foreach ($tag in $serviceTags) {
    $uri = "https://apigtwb2c.us.dell.com/PROD/sbil/eapi/v5/asset-entitlements?servicetags=$tag"
    $headers = @{ "Authorization" = "Bearer $apiKey" }
    $response = Invoke-RestMethod -Uri $uri -Headers $headers -Method Get

    $warranty = $response | Select-Object -ExpandProperty entitlements |
        Where-Object { $_.serviceLevelDescription -like "*ProSupport*" } |
        Select-Object -First 1

    Write-Output "$tag | Scadenza: $($warranty.endDate) | Tipo: $($warranty.serviceLevelDescription)"
}
```

**Livelli di Supporto Hardware:**

| Livello | SLA Intervento | Descrizione | Costo Relativo |
|---------|---------------|-------------|----------------|
| Basic / Carry-In | 5-10 gg lavorativi | L'utente porta il dispositivo al centro assistenza | Basso |
| NBD (Next Business Day) | Entro il giorno lavorativo successivo | Intervento on-site il giorno dopo la segnalazione | Medio |
| 4-Hour Response | Entro 4 ore lavorative | Intervento on-site entro 4 ore (orario lavorativo) | Alto |
| 24/7 4-Hour | Entro 4 ore, 24/7 | Intervento on-site entro 4 ore, inclusi festivi e notturni | Molto Alto |
| Mission Critical | Entro 2 ore, 24/7 | Massima priorita con team dedicato | Premium |

**Processo RMA (Return Merchandise Authorization):**

```
1. Diagnosi del guasto e conferma che l'asset e coperto da garanzia
2. Contatto con il supporto del vendor (telefono/portale/email)
3. Apertura del caso e ottenimento del numero RMA
4. Preparazione dell'asset per la spedizione (backup dati, reset se necessario)
5. Spedizione al centro riparazioni (con etichetta RMA)
6. Tracking dello stato della riparazione
7. Ricezione dell'asset riparato/sostituito
8. Verifica funzionamento e re-deployment
9. Chiusura del caso RMA e aggiornamento CMDB
```

---

## Gestione Licenze Software

La gestione delle licenze software (Software Asset Management, SAM) e uno degli aspetti piu complessi e a maggior rischio dell'ITAM. Un audit da parte di un vendor software (Microsoft, Adobe, Oracle, SAP) che rilevi non-conformita puo comportare costi significativi in termini di penali, acquisti forzati di licenze e danni reputazionali.

**Audit di Conformita Licenze:**

Il processo di compliance audit prevede:

1. **Inventario del software installato**: Raccolta automatizzata di tutti i software installati su ogni endpoint e server (vedere sezione Inventario Software).
2. **Inventario delle licenze acquistate**: Raccolta di tutte le prove di acquisto (Product Key, certificati di licenza, contratti VL, fatture, email di conferma per sottoscrizioni).
3. **Riconciliazione**: Confronto tra installazioni rilevate e licenze possedute.
4. **Gap analysis**: Identificazione di over-licensing (licenze pagate ma non utilizzate) e under-licensing (installazioni senza licenza corrispondente).
5. **Remediation**: Acquisto delle licenze mancanti, rimozione del software non licenziato, recupero delle licenze inutilizzate.

**Rilevamento Over/Under-Licensing:**

```
Esempio di Riconciliazione:
============================
Software: Microsoft Office Professional Plus 2021
Licenze acquistate (VL):    250 (contratto EA #12345)
Installazioni rilevate:     287
Differenza:                 -37 (UNDER-LICENSED)
Azione: Acquistare 37 licenze aggiuntive o disinstallare da 37 endpoint

Software: Adobe Acrobat Pro DC
Licenze acquistate (Named): 50 (subscription annuale)
Utilizzi attivi ultimi 90gg: 28
Licenze inutilizzate:       22 (OVER-LICENSED)
Azione: Ridurre le licenze al prossimo rinnovo (risparmio potenziale)

Software: AutoCAD 2024
Licenze acquistate (Named): 15
Installazioni rilevate:     15
Utilizzi attivi ultimi 90gg: 14
Stato:                      CONFORME (1 licenza sottoutilizzata - monitorare)
```

**License Harvesting (Recupero Licenze):**

Il license harvesting e il processo di recupero delle licenze software da asset non piu in uso o assegnate a utenti che non le utilizzano effettivamente:

- Monitorare l'effettivo utilizzo del software (non solo l'installazione)
- Definire soglie di inattivita (es. software non avviato da 90 giorni)
- Disinstallare automaticamente o segnalare le installazioni inattive
- Recuperare la licenza per riassegnazione ad altri utenti richiedenti
- Per licenze subscription: ridurre il numero al prossimo rinnovo

**Gestione Volume Licensing — Microsoft:**

Microsoft offre diversi programmi di Volume Licensing, ciascuno con le proprie regole e portali:

- **Microsoft 365 / Entra ID**: Gestione licenze tramite il portale admin.microsoft.com (assegnazione per utente)
- **VLSC (Volume Licensing Service Center)**: Per licenze perpetue acquistate tramite Open, Select, EA
- **Enterprise Agreement (EA)**: Contratto triennale per grandi organizzazioni, prevede true-up annuale
- **CSP (Cloud Solution Provider)**: Licenze acquistate tramite partner, gestione flessibile mensile

**True-Up Process (per contratti EA):**

Il true-up e la riconciliazione annuale obbligatoria prevista dai contratti Enterprise Agreement Microsoft:

```
Processo True-Up Annuale:
1. Conteggio delle licenze effettivamente in uso alla data di anniversary
2. Confronto con le licenze dichiarate nel contratto EA
3. Se le installazioni superano le licenze dichiarate:
   - Pagamento retroattivo delle licenze aggiuntive utilizzate
4. Se le installazioni sono inferiori (non sempre possibile ridurre):
   - Dipende dai termini specifici del contratto
5. Reportistica al Microsoft Licensing Partner
6. Aggiornamento del contratto per il periodo successivo
```

**Gestione Subscription Cloud:**

Per le licenze cloud (Azure, AWS, Microsoft 365), implementare:

- Revisione mensile delle assegnazioni di licenza M365 (rimuovere licenze da utenti disabilitati/terminati)
- Monitoraggio dei costi Azure/AWS tramite Cost Management (alert per superamento soglie)
- Tag delle risorse cloud per allocazione dei costi ai centri di costo
- Reserved Instances / Savings Plans per carichi di lavoro prevedibili (risparmio 30-60% rispetto a on-demand)
- Right-sizing periodico delle risorse cloud (ridimensionamento VM sottoutilizzate)

---

## Pianificazione Refresh e EOL/EOS

La pianificazione del refresh tecnologico e la gestione delle date EOL (End of Life) / EOS (End of Support) sono attivita strategiche che richiedono visione a medio-lungo termine.

**Cicli di Refresh Tipici:**

| Categoria Asset | Ciclo Refresh | Motivazione |
|----------------|---------------|-------------|
| Laptop | 3-4 anni | Usura batteria, prestazioni, garanzia |
| Workstation Desktop | 4-5 anni | Prestazioni, compatibilita software |
| Server fisici | 5-7 anni | Fine garanzia, efficienza energetica, prestazioni |
| Storage (SAN/NAS) | 5-7 anni | Capacita, prestazioni I/O, fine supporto |
| Switch di accesso | 7-10 anni | Fine supporto, standard di rete (nuovi PoE, velocita) |
| Switch core/distribuzione | 5-7 anni | Prestazioni, funzionalita, ridondanza |
| Firewall | 5-7 anni | Throughput, funzionalita di sicurezza, fine supporto |
| Access Point Wi-Fi | 4-6 anni | Nuovi standard Wi-Fi (Wi-Fi 6/6E/7) |
| UPS (batterie) | 3-5 anni | Degradazione batterie (test periodici) |
| Smartphone aziendali | 2-3 anni | Aggiornamenti OS, sicurezza, usura |

**Tracking EOL/EOS:**

Mantenere un registro aggiornato delle date di fine supporto per tutti i software e sistemi operativi in uso:

```
REGISTRO EOL/EOS — Esempio
============================
Prodotto                    | EOL (fine vendita) | EOS (fine supporto) | Stato    | Piano
----------------------------|--------------------|--------------------|----------|------------------
Windows 10                  | —                  | 14 Ott 2025        | SCADUTO  | Migrazione a Win 11 completata
Windows Server 2016         | —                  | 12 Gen 2027        | ATTIVO   | Piano migrazione in corso
Windows Server 2019         | —                  | 09 Gen 2029        | ATTIVO   | Nessuna azione immediata
SQL Server 2016             | —                  | 14 Lug 2026        | URGENTE  | Upgrade a SQL 2022 pianificato
VMware vSphere 7.0          | —                  | Verificare         | ATTIVO   | Valutare upgrade a vSphere 8
Cisco Catalyst 3750-X       | 2016               | 2021               | SCADUTO  | Sostituzione con Cat 9200
FortiGate 60E               | 2023               | 2028               | ATTIVO   | Pianificare sostituzione 2027
```

**Pianificazione Budget per Refresh:**

```
Piano Refresh Triennale — Esempio
===================================
Anno 2026:
  - 50 laptop (ciclo 4 anni, lotto 2022)     €50.000
  - 2 server rack (ciclo 6 anni, lotto 2020) €30.000
  - Upgrade storage NAS                       €15.000
  Totale stimato: €95.000

Anno 2027:
  - 30 workstation desktop (lotto 2023)       €30.000
  - 10 switch di accesso (lotto 2017)         €25.000
  - 5 access point Wi-Fi (Wi-Fi 6E)          €5.000
  Totale stimato: €60.000

Anno 2028:
  - 50 laptop (ciclo 4 anni, lotto 2024)     €55.000
  - Firewall perimetrale (lotto 2022)         €20.000
  - Rinnovo UPS batterie                      €8.000
  Totale stimato: €83.000
```

**Criteri di Prioritizzazione per il Refresh:**

1. **Criticita operativa**: Asset che supportano servizi business-critical hanno priorita massima
2. **Stato di supporto**: Asset con software/hardware EOL/EOS hanno priorita alta per rischi di sicurezza
3. **Prestazioni**: Asset che non soddisfano i requisiti minimi per i carichi di lavoro attuali
4. **Costi di manutenzione**: Quando il costo annuo di manutenzione supera il 30-40% del costo di sostituzione
5. **Conformita**: Asset non conformi a standard di sicurezza o normative vigenti
6. **Efficienza energetica**: Server/storage di vecchia generazione con consumi energetici elevati
7. **Soddisfazione utente**: Endpoint che generano un numero elevato di ticket di assistenza

---

## Decommissioning e Smaltimento

Il processo di dismissione e smaltimento degli asset IT richiede particolare attenzione alla sicurezza dei dati e alla conformita ambientale.

**Procedure di Sanificazione Dati — NIST SP 800-88 Rev. 1:**

La guida NIST 800-88 "Guidelines for Media Sanitization" definisce tre livelli di sanificazione:

| Metodo | Descrizione | Quando Utilizzarlo | Strumenti |
|--------|-------------|-------------------|-----------|
| **Clear** | Sovrascrittura logica dei dati con dati nulli/casuali | Riutilizzo interno dell'asset | `shred`, `sdelete`, DBAN |
| **Purge** | Sanificazione che rende i dati irrecuperabili anche con tecniche forensi | Riutilizzo esterno, donazione, rivendita | Secure Erase (ATA), Cryptographic Erase |
| **Destroy** | Distruzione fisica del supporto | Dati altamente sensibili, supporti non funzionanti | Degausser, shredder industriale |

**Comandi Operativi per la Sanificazione:**

```bash
# Linux — Sovrascrittura con shred (3 passaggi + azzeramento finale)
shred -vzn 3 /dev/sdX

# Linux — Sovrascrittura con dd (un passaggio con zeri)
dd if=/dev/zero of=/dev/sdX bs=1M status=progress

# Linux — Sovrascrittura con dati casuali
dd if=/dev/urandom of=/dev/sdX bs=1M status=progress

# Linux — Secure Erase per SSD (tramite hdparm)
hdparm --user-master u --security-set-pass PASS /dev/sdX
hdparm --user-master u --security-erase PASS /dev/sdX

# Linux — NVMe Secure Erase
nvme format /dev/nvme0n1 --ses=1    # User Data Erase
nvme format /dev/nvme0n1 --ses=2    # Cryptographic Erase (preferibile)
```

```powershell
# Windows — SDelete di Sysinternals (sovrascrittura spazio libero)
sdelete64.exe -z C:

# Windows — cipher (sovrascrittura spazio libero nativo)
cipher /w:C:\

# Windows — Format con sovrascrittura (Windows 10/11)
Format D: /P:3    # 3 passaggi di sovrascrittura
```

**Certificato di Distruzione:**

Per ogni asset dismesso contenente dati, ottenere e archiviare un certificato di distruzione che includa:

```
CERTIFICATO DI AVVENUTA SANIFICAZIONE/DISTRUZIONE
===================================================
Data: _______________
Asset Tag: _______________
Serial Number: _______________
Tipo supporto: HDD / SSD / NVMe / Tape / Altro: _______________
Capacita: _______________

Metodo di sanificazione utilizzato:
[ ] Clear — Sovrascrittura (n. passaggi: ___)  Strumento: _______________
[ ] Purge — Secure Erase / Crypto Erase        Strumento: _______________
[ ] Destroy — Distruzione fisica                Metodo: _______________

Eseguito da: _______________ (Nome, Ruolo)
Verificato da: _______________ (Nome, Ruolo)
Firma: _______________
```

**Conformita Ambientale — RAEE/WEEE:**

La normativa RAEE (Rifiuti di Apparecchiature Elettriche ed Elettroniche), recepimento italiano della direttiva europea WEEE, impone obblighi specifici per lo smaltimento di apparecchiature elettroniche:

- I rifiuti elettronici NON possono essere smaltiti come rifiuti ordinari
- Le aziende devono affidarsi a **raccoglitori autorizzati** iscritti all'Albo Nazionale Gestori Ambientali
- Conservare il **Formulario di Identificazione del Rifiuto (FIR)** per almeno 5 anni
- Classificazione CER/EER corretta (es. 16 02 14 per apparecchiature fuori uso, 16 02 13 se contenenti componenti pericolosi)
- Per quantitativi superiori a 10 unita/anno, considerare l'iscrizione al SISTRI/RENTRI (Registro Elettronico Nazionale Tracciabilita Rifiuti)

**Procedure di Donazione e Rivendita:**

Per asset ancora funzionanti ma non piu adeguati all'uso aziendale:

1. Sanificazione completa dei dati (livello Purge minimo)
2. Reinstallazione del sistema operativo con licenza OEM originale (se applicabile)
3. Verifica delle condizioni contrattuali (alcune licenze VL vietano il trasferimento)
4. Valutazione del valore residuo dell'asset
5. Documentazione della cessione (destinatario, data, elenco asset)
6. Per donazioni: verifica dei requisiti fiscali per la deducibilita

**Chain of Custody:**

Mantenere una tracciabilita completa dell'asset dal momento della dismissione fino allo smaltimento finale:

```
Asset: HW-LAP-0142 (Dell Latitude 5530, SN: ABC123DEF)
-------------------------------------------------------
Data        | Azione                    | Responsabile      | Note
------------|---------------------------|-------------------|------------------
2026-03-01  | Ritirato dall'utente      | Rossi M. (IT)     | Fine rapporto dipendente
2026-03-02  | Backup dati utente        | Bianchi L. (IT)   | Dati trasferiti a NAS
2026-03-03  | Sanificazione disco       | Bianchi L. (IT)   | NVMe Crypto Erase
2026-03-03  | Licenze software recuperate| Bianchi L. (IT)  | M365, Adobe CC rimosse
2026-03-05  | Trasferito a magazzino    | Verdi G. (IT)     | In attesa smaltimento
2026-03-15  | Consegnato a raccoglitore | Verdi G. (IT)     | FIR n. 2026/0089
```

---

## Strumenti ITAM

### Confronto Strumenti

| Caratteristica | GLPI | Snipe-IT | NetBox | LANSweeper | ServiceNow ITAM |
|---------------|------|----------|--------|------------|-----------------|
| Tipo | Open-source | Open-source | Open-source | Commerciale | Enterprise SaaS |
| Focus | ITSM + ITAM | Asset Management | Infrastruttura DC | Discovery + Inventory | ITSM + ITAM completo |
| Discovery automatica | Si (FusionInventory) | No (import manuale/API) | No (import/API) | Si (agentless) | Si (Discovery) |
| Gestione licenze | Si | Si (basilare) | No | Si | Si (avanzata) |
| IPAM | Plugin | No | Si (eccellente) | Si | Plugin |
| CMDB | Si | No | Si (infrastruttura) | Parziale | Si (completo) |
| Ticketing integrato | Si | No | No | No | Si |
| API REST | Si | Si | Si | Si | Si |
| Barcode/QR | Si (plugin) | Si (nativo) | No | No | Si |
| Costo | Gratuito | Gratuito (self-hosted) | Gratuito | Da ~€15K/anno | Da ~€50K/anno |
| Ideale per | PMI e medie imprese | PMI, asset tracking | DC e infrastruttura rete | Medie e grandi imprese | Enterprise |

### Setup Pratico: GLPI con Inventario Automatico

GLPI (Gestionnaire Libre de Parc Informatique) e la soluzione open-source piu completa per ITAM nelle organizzazioni di piccole e medie dimensioni. Di seguito una guida pratica per l'installazione e la configurazione.

**Installazione GLPI (su Ubuntu Server 22.04/24.04):**

```bash
# Prerequisiti: Apache, PHP, MariaDB
sudo apt update && sudo apt upgrade -y
sudo apt install -y apache2 php php-{mysql,curl,gd,xml,mbstring,intl,ldap,zip,bz2} \
    mariadb-server libapache2-mod-php

# Configurazione database
sudo mysql -e "CREATE DATABASE glpi CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
sudo mysql -e "CREATE USER 'glpi'@'localhost' IDENTIFIED BY 'SecurePassword123!';"
sudo mysql -e "GRANT ALL PRIVILEGES ON glpi.* TO 'glpi'@'localhost';"
sudo mysql -e "FLUSH PRIVILEGES;"

# Download e installazione GLPI (verificare ultima versione su github.com/glpi-project/glpi)
cd /tmp
wget https://github.com/glpi-project/glpi/releases/download/10.0.16/glpi-10.0.16.tgz
sudo tar xzf glpi-10.0.16.tgz -C /var/www/html/
sudo chown -R www-data:www-data /var/www/html/glpi
sudo chmod -R 755 /var/www/html/glpi

# Abilitare mod_rewrite
sudo a2enmod rewrite
sudo systemctl restart apache2

# Completare l'installazione via browser: http://server-ip/glpi
# Credenziali default: glpi/glpi (CAMBIARE IMMEDIATAMENTE dopo il login)
```

**Installazione FusionInventory Agent (su endpoint Windows):**

```powershell
# Download dell'installer FusionInventory Agent per Windows
# URL: https://github.com/fusioninventory/fusioninventory-agent/releases
# Installazione silenziosa con parametri:
fusioninventory-agent_windows-x64_2.6.exe /S /server="http://glpi-server/glpi/plugins/fusioninventory/" /tag="SEDE-MILANO"
```

```bash
# Installazione FusionInventory Agent su Linux (Debian/Ubuntu)
sudo apt install -y fusioninventory-agent

# Configurazione
sudo tee /etc/fusioninventory/agent.cfg << 'AGENTCFG'
server = http://glpi-server/glpi/plugins/fusioninventory/
tag = SEDE-MILANO
# Frequenza di inventario in secondi (86400 = 24 ore)
delaytime = 86400
AGENTCFG

# Avvio e abilitazione del servizio
sudo systemctl enable --now fusioninventory-agent
# Esecuzione immediata di un inventario
sudo fusioninventory-agent --force
```

**Configurazione GLPI per la Ricezione degli Inventari:**

1. Accedere a GLPI come amministratore
2. Navigare in **Configurazione > Plugin** e attivare il plugin FusionInventory
3. In **Plugin > FusionInventory > Generale**, configurare le regole di importazione
4. Creare regole per l'assegnazione automatica delle entita (sedi) in base al tag dell'agente
5. Configurare le regole di raggruppamento per evitare duplicati (match su serial number)
6. Verificare la ricezione dei primi inventari in **Asset > Computer**

---

## Reportistica Asset

Una reportistica strutturata e fondamentale per prendere decisioni informate e dimostrare il valore del programma ITAM al management.

### Template Report Inventario Asset

```
REPORT INVENTARIO ASSET IT
===========================
Data: [DATA]
Periodo di riferimento: [TRIMESTRE/ANNO]
Redatto da: [NOME RESPONSABILE IT]

RIEPILOGO GENERALE:
-------------------
Totale asset attivi:                    [N]
  - Server fisici:                      [N]
  - Workstation/Desktop:                [N]
  - Laptop:                             [N]
  - Dispositivi mobili:                 [N]
  - Apparati di rete:                   [N]
  - Stampanti/Periferiche:              [N]
  - Altro:                              [N]

Asset in magazzino (spare):             [N]
Asset in riparazione:                   [N]
Asset dismessi nel periodo:             [N]
Asset acquisiti nel periodo:            [N]

DISTRIBUZIONE PER SEDE:
-----------------------
Sede Milano:    [N] asset ([%] del totale)
Sede Roma:      [N] asset ([%] del totale)
Sede Torino:    [N] asset ([%] del totale)

ETA MEDIA DEL PARCO (in mesi):
------------------------------
Laptop:         [N] mesi (target: < 48 mesi)
Workstation:    [N] mesi (target: < 60 mesi)
Server:         [N] mesi (target: < 84 mesi)
Rete:           [N] mesi (target: < 120 mesi)
```

### Report Conformita Licenze

```
REPORT CONFORMITA LICENZE SOFTWARE
====================================
Data audit: [DATA]
Strumento di rilevazione: [TOOL]

RIEPILOGO CONFORMITA:
--------------------
Prodotti verificati:          [N]
Prodotti conformi:            [N] ([%])
Prodotti sotto-licenziati:    [N] ([%])  *** ATTENZIONE ***
Prodotti sovra-licenziati:    [N] ([%])  --- Ottimizzazione possibile ---

DETTAGLIO SOTTO-LICENZIAMENTO:
-----------------------------
Prodotto             | Licenze | Installazioni | Gap  | Costo Stim.
---------------------|---------|---------------|------|------------
[Software A]         | [N]     | [N]           | [N]  | €[X]
[Software B]         | [N]     | [N]           | [N]  | €[X]

DETTAGLIO SOVRA-LICENZIAMENTO:
-----------------------------
Prodotto             | Licenze | Utilizzo Eff. | Eccedenza | Risparmio Pot.
---------------------|---------|---------------|-----------|---------------
[Software C]         | [N]     | [N]           | [N]       | €[X]/anno
[Software D]         | [N]     | [N]           | [N]       | €[X]/anno

RISCHIO COMPLESSIVO: [BASSO/MEDIO/ALTO/CRITICO]
RISPARMIO POTENZIALE DA OTTIMIZZAZIONE: €[X]/anno
```

### Report Scadenza Garanzie

```
REPORT SCADENZA GARANZIE
==========================
Data: [DATA]

GARANZIE GIA SCADUTE (azione immediata richiesta):
  [N] asset fuori garanzia in produzione
  Dettaglio: [lista asset con data scadenza e criticita]

GARANZIE IN SCADENZA ENTRO 30 GIORNI:
  [N] asset
  Dettaglio: [lista asset]

GARANZIE IN SCADENZA ENTRO 90 GIORNI:
  [N] asset
  Dettaglio: [lista asset]

GARANZIE IN SCADENZA ENTRO 180 GIORNI:
  [N] asset — Pianificare decisione estensione/sostituzione

COPERTURA COMPLESSIVA:
  Asset con garanzia attiva:     [N] ([%])
  Asset fuori garanzia:          [N] ([%])
  Contratti di manutenzione:     [N] attivi
```

### Analisi TCO (Total Cost of Ownership)

```
ANALISI TCO PER TIPOLOGIA ASSET
=================================
Periodo: [ANNO]

Laptop Standard (profilo WKS-STANDARD):
  Costo acquisizione:           €900
  Costo setup e deployment:     €50  (tempo IT stimato: 1h)
  Costo licenze SW annuo:       €200 (M365, antivirus, ecc.)
  Costo supporto/manutenzione:  €100/anno (media)
  Costo energetico annuo:       €30
  Costo dismissione:            €20
  ----------------------------------------
  TCO su 4 anni:                €2.290
  TCO mensile:                  €47,7/mese

Server Standard (profilo SRV-STANDARD):
  Costo acquisizione:           €15.000
  Costo setup e deployment:     €500  (tempo IT stimato: 8h)
  Costo licenze SW annuo:       €3.000 (OS, hypervisor, backup)
  Costo supporto hardware:      €2.000/anno (garanzia estesa 24/7)
  Costo energetico annuo:       €1.500 (con raffreddamento)
  Costo housing/rack space:     €600/anno
  Costo dismissione:            €100
  ----------------------------------------
  TCO su 6 anni:                €58.200
  TCO mensile:                  €808/mese
```

### Dashboard ITAM — KPI Consigliati

| KPI | Descrizione | Target |
|-----|-------------|--------|
| Accuratezza inventario | % asset fisici che corrispondono al CMDB | > 95% |
| Copertura discovery | % della rete coperta dalla scansione automatica | > 98% |
| Conformita licenze | % prodotti software correttamente licenziati | 100% |
| Copertura garanzia | % asset critici con garanzia attiva | > 90% |
| Eta media endpoint | Eta media dei dispositivi utente | < 3,5 anni |
| Tempo medio deployment | Tempo dal ricevimento al deployment operativo | < 2 gg lavorativi |
| Tasso di utilizzo | % asset attivi sul totale acquistato | > 90% |
| Costo per endpoint/mese | TCO medio mensile per postazione utente | Monitorare trend |
| Asset fuori policy | % asset non conformi agli standard aziendali | < 5% |
| Ticket per asset | Numero medio di ticket di assistenza per asset | Monitorare trend |

---

## Best Practices

1. **Mantenere un CMDB come Single Source of Truth**: Ogni informazione relativa agli asset deve essere aggiornata nel CMDB. Evitare fogli di calcolo paralleli, email informali o documentazione non strutturata. Se il CMDB non riflette la realta, e il CMDB che deve essere corretto, non la realta che deve essere ignorata.

2. **Automatizzare la Discovery e l'Inventario**: L'inventario manuale e inaffidabile e non scalabile. Implementare agenti di inventario (FusionInventory, SCCM, Intune) su tutti gli endpoint gestiti e scansioni SNMP/WMI per gli apparati di rete. La scansione automatica deve coprire almeno il 98% della rete.

3. **Implementare il Lifecycle Management fin dal Giorno Zero**: Ogni asset deve entrare nel CMDB al momento dell'ordine di acquisto (non alla ricezione o al deployment). Il tracciamento del ciclo di vita completo — dall'approvvigionamento allo smaltimento — fornisce dati storici preziosi per le decisioni future.

4. **Separare la Gestione delle Licenze dalla Gestione dell'Hardware**: Le licenze software hanno cicli di vita, regole e complessita proprie. Dedicare risorse specifiche al Software Asset Management (SAM) e condurre audit di conformita almeno semestrali. Il costo di un programma SAM interno e sempre inferiore alle penali di un audit fallito.

5. **Pianificare il Refresh con Almeno 12 Mesi di Anticipo**: Elaborare un piano di refresh triennale aggiornato annualmente. Questo consente di distribuire la spesa nel tempo, negoziare condizioni migliori con i fornitori e minimizzare le interruzioni operative.

6. **Standardizzare le Configurazioni**: Limitare il numero di modelli e configurazioni hardware approvate. La standardizzazione riduce la complessita del supporto, semplifica la gestione dei ricambi, migliora la negoziazione con i fornitori e accelera il deployment.

7. **Implementare Alert Proattivi per le Scadenze Critiche**: Configurare notifiche automatiche per scadenze garanzia, fine supporto software, rinnovi contrattuali e date di fine licenza. Un alert a 90/60/30 giorni dalla scadenza lascia tempo sufficiente per le decisioni e le azioni necessarie.

8. **Documentare la Chain of Custody per Tutto il Ciclo di Vita**: Ogni trasferimento, riparazione, prestito, dismissione e smaltimento deve essere documentato con data, responsabile e motivazione. Questo protegge l'organizzazione sia dal punto di vista della sicurezza dei dati che della conformita normativa (GDPR, RAEE).

9. **Condurre Audit Fisici Periodici**: L'inventario automatico non sostituisce completamente la verifica fisica. Programmare audit fisici trimestrali per le aree critiche (data center, server room) e semestrali per gli endpoint utente. Confrontare i risultati dell'audit fisico con il CMDB e risolvere le discrepanze.

10. **Misurare e Comunicare il Valore del Programma ITAM**: Produrre reportistica periodica che quantifichi i risparmi ottenuti (licenze recuperate, acquisti duplicati evitati, penali scongiurate) e i rischi mitigati. Comunicare questi risultati al management per giustificare l'investimento nel programma ITAM e ottenere il supporto necessario per il suo miglioramento continuo.

---

## Troubleshooting

### Problema: Discrepanze tra Inventario CMDB e Realta Fisica

**Sintomi:** L'audit fisico rileva asset non presenti nel CMDB, oppure il CMDB elenca asset che non si trovano nella posizione indicata.

**Cause comuni:**
- Asset spostati senza aggiornare il CMDB
- Nuovi asset deployati senza registrazione
- Asset dismessi senza aggiornamento dello stato
- Duplicati nel CMDB (stesso asset registrato piu volte con identificativi diversi)

**Soluzione:**
- Eseguire una riconciliazione completa: scansione automatica + verifica fisica
- Implementare processi obbligatori di aggiornamento CMDB per ogni movimento di asset
- Configurare regole di deduplicazione basate su serial number
- Formare il personale IT sull'importanza dell'aggiornamento tempestivo del CMDB
- Considerare l'adozione di processi di change management che richiedano l'aggiornamento del CMDB come step obbligatorio

### Problema: Discovery Automatica Non Rileva Tutti i Dispositivi

**Sintomi:** Dispositivi noti non compaiono nei risultati della scansione di rete.

**Cause comuni:**
- Firewall o ACL che bloccano i protocolli di scansione (WMI, SNMP, SSH)
- Dispositivi su VLAN non raggiungibili dallo scanner
- Credenziali di scansione insufficienti o errate
- Dispositivi spenti o disconnessi durante la finestra di scansione
- Agente di inventario non installato o non funzionante

**Soluzione:**
```bash
# Verificare la raggiungibilita di base
ping -c 3 [IP_DISPOSITIVO]

# Verificare le porte di gestione aperte
nmap -p 135,443,161,22 [IP_DISPOSITIVO]
# 135: WMI (Windows)
# 443: HTTPS management
# 161: SNMP
# 22: SSH (Linux)

# Verificare la risposta SNMP
snmpwalk -v2c -c [COMMUNITY_STRING] [IP_DISPOSITIVO] sysDescr.0

# Verificare la connettivita WMI (da Windows)
Test-WsMan -ComputerName [HOSTNAME]
Get-CimInstance -ComputerName [HOSTNAME] -ClassName Win32_ComputerSystem
```

- Assicurarsi che le credenziali di scansione abbiano i privilegi necessari (admin locale per WMI, community string corretta per SNMP)
- Verificare che lo scanner abbia accesso a tutte le VLAN (o posizionare scanner distribuiti)
- Programmare scansioni in orari diversi per intercettare dispositivi mobili
- Implementare un processo per la registrazione manuale dei dispositivi non scansionabili

### Problema: Software Non Autorizzato Rilevato sugli Endpoint

**Sintomi:** La scansione software rileva applicazioni non presenti nella whitelist aziendale.

**Cause comuni:**
- Utenti con privilegi di amministratore locale che installano software autonomamente
- Software portable (non richiede installazione, non compare nel registro)
- Estensioni browser non gestite
- Software installato da altri dipartimenti senza coordinamento con l'IT

**Soluzione:**
- Rimuovere i privilegi di amministratore locale dove non strettamente necessari
- Implementare Application Control (AppLocker, Windows Defender Application Control)
- Distribuire il software tramite un sistema centralizzato (SCCM, Intune, PDQ Deploy)
- Creare un catalogo self-service dove gli utenti possono richiedere software approvato
- Monitorare periodicamente e generare alert per installazioni non autorizzate
- Stabilire una policy chiara con conseguenze per l'installazione non autorizzata

### Problema: Licenze Software Insufficienti Rilevate Durante un Audit

**Sintomi:** Il confronto tra installazioni e licenze mostra un deficit (under-licensing).

**Cause comuni:**
- Acquisto iniziale sottodimensionato
- Crescita organica non accompagnata dall'acquisto di licenze aggiuntive
- Licenze non correttamente contabilizzate (es. OEM non trasferibili usate su hardware diverso)
- Mancata comprensione dei termini di licenza (es. per-core vs per-server per SQL Server)

**Soluzione:**
- Acquistare immediatamente le licenze mancanti per sanare la non-conformita
- Valutare se alcune installazioni possono essere disinstallate (utenti che non utilizzano il software)
- Considerare il passaggio a una tipologia di licenza piu adeguata (es. da per-device a per-user se gli utenti hanno piu dispositivi)
- Implementare un processo di approvazione che verifichi la disponibilita di licenze prima di ogni nuova installazione
- Attivare il license harvesting per recuperare licenze inutilizzate

### Problema: Asset Smarriti o Non Rintracciabili

**Sintomi:** Asset presenti nel CMDB con stato "attivo" non risultano fisicamente rintracciabili.

**Cause comuni:**
- Asset prestati temporaneamente e non restituiti
- Furti non denunciati
- Asset smaltiti senza aggiornamento del CMDB
- Errori nel campo di collocazione (sede/stanza errata)

**Soluzione:**
- Verificare l'ultimo accesso di rete dell'asset (log DHCP, NAC, Active Directory last logon)
- Contattare l'ultimo assegnatario registrato nel CMDB
- Verificare nei magazzini e nelle aree di stoccaggio
- Se l'asset conteneva dati sensibili, attivare la procedura di incident response (possibile data breach)
- Aggiornare lo stato nel CMDB come "smarrito/rubato" e attivare le procedure aziendali appropriate
- Prevenzione: implementare processi di checkout/checkin rigorosi e audit fisici regolari

### Problema: Costi ITAM Fuori Controllo

**Sintomi:** I costi di gestione del parco IT crescono in modo sproporzionato rispetto alla crescita dell'organizzazione.

**Cause comuni:**
- Assenza di standardizzazione (troppi modelli diversi = costi di supporto elevati)
- Mancata ottimizzazione delle licenze (over-licensing diffuso)
- Rinnovo automatico di contratti non piu necessari
- Risorse cloud non monitorate (istanze dimenticate, storage non utilizzato)
- Assenza di pianificazione del refresh (acquisti in emergenza a prezzi maggiorati)

**Soluzione:**
- Condurre un'analisi TCO completa per ogni tipologia di asset
- Implementare il license harvesting e ridurre le licenze subscription inutilizzate
- Rivedere tutti i contratti di manutenzione e supporto (eliminare quelli non necessari)
- Attivare il monitoraggio dei costi cloud con alert per anomalie
- Implementare politiche di right-sizing per le risorse cloud
- Negoziare contratti quadro con i fornitori principali per ottenere sconti volume
- Valutare il modello DaaS (Device as a Service) per gli endpoint, trasformando il CAPEX in OPEX prevedibile

---

## Framework ISO/IEC 19770 e Standard ITAM

Lo standard **ISO/IEC 19770** rappresenta il riferimento normativo internazionale per la gestione degli asset IT. Originariamente pubblicato nel 2006 con focus esclusivo sul Software Asset Management (SAM), si e evoluto in un framework olistico che copre hardware, software, servizi cloud e asset digitali. La revisione del 2017 ha allineato lo standard con altri sistemi di gestione ISO (ISO 9001, ISO 27001), facilitando l'integrazione nei programmi di governance aziendale esistenti.

### Struttura dello Standard ISO 19770

Lo standard si articola in piu parti, ciascuna dedicata a un aspetto specifico della gestione degli asset IT:

```
ISO/IEC 19770 — Struttura Completa
====================================

Parte 1: Processi e Requisiti del Sistema di Gestione ITAM
  - Framework di 27 aree di processo
  - Obiettivi e risultati dettagliati per ogni area
  - Modello di valutazione a livelli (Tiers)
  - Allineamento con ISO 20000-1 (Service Management)

Parte 2: Software Identification Tag (SWID Tag)
  - Specifica tecnica per l'identificazione univoca del software
  - Formato XML per tag di identificazione software
  - Supporto per tag di corpus, primari e supplementari
  - Facilitazione dell'inventario automatizzato del software

Parte 3: Software Entitlement Schema
  - Schema per la rappresentazione formale dei diritti di licenza
  - Definizione delle metriche di licenza (per-seat, per-core, ecc.)
  - Supporto per la riconciliazione automatizzata licenze-installazioni
  - Modello di dati per contratti e accordi di licenza

Parte 5: Panoramica e Vocabolario
  - Terminologia unificata per ITAM/SAM
  - Relazioni tra le parti dello standard
  - Principi fondamentali e concetti chiave

Parte 8: Linee Guida per la Mappatura di Elementi di Risorse
  - Normalizzazione dei dati di inventario
  - Mappatura tra dati di discovery e catalogo software
  - Correlazione tra installazioni e diritti di licenza
```

**Aree di Processo Chiave (ISO 19770-1):**

Lo standard definisce 27 aree di processo organizzate in quattro categorie principali:

| Categoria | Aree di Processo | Obiettivo |
|-----------|-----------------|-----------|
| Processi Organizzativi | Governance, politiche, ruoli e responsabilita, competenze | Stabilire le fondamenta organizzative per l'ITAM |
| Processi di Gestione Fondamentali | Inventario, verifica, operazioni di conformita | Garantire l'accuratezza e la completezza dei dati |
| Processi di Gestione del Ciclo di Vita | Pianificazione, acquisizione, deployment, ritiro, dismissione | Gestire ogni fase del ciclo di vita degli asset |
| Processi Interfaccia | Integrazione con service management, sicurezza, finanza | Connettere l'ITAM con le altre funzioni aziendali |

### Tiers di Conformita ISO 19770-1

Lo standard definisce un sistema di valutazione a livelli progressivi (Tiers) che consente alle organizzazioni di misurare il proprio grado di conformita e pianificare un percorso di miglioramento graduale:

```
Tier 1 — Dati Attendibili (Trustworthy Data)
  Obiettivo: Costruire un inventario completo e affidabile
  Requisiti:
    - Inventario hardware e software completo e aggiornato
    - Processi di base per la raccolta e la verifica dei dati
    - Identificazione degli stakeholder e delle responsabilita
    - Procedure documentate per la gestione degli asset
  Risultato: L'organizzazione sa cosa possiede e dove si trova

Tier 2 — Gestione del Ciclo di Vita (Lifecycle Management)
  Obiettivo: Gestire gli asset durante tutto il loro ciclo di vita
  Requisiti:
    - Processi definiti per ogni fase del ciclo di vita
    - Integrazione con procurement e finance
    - Tracking di garanzie, contratti e scadenze
    - Gestione dei cambiamenti e delle assegnazioni
  Risultato: L'organizzazione gestisce attivamente i propri asset

Tier 3 — Ottimizzazione (Optimization)
  Obiettivo: Ottimizzare costi e utilizzo degli asset
  Requisiti:
    - Analisi TCO e ottimizzazione dei costi
    - License harvesting e recupero risorse
    - Pianificazione strategica del refresh
    - Metriche di performance e KPI consolidati
  Risultato: L'organizzazione ottimizza il valore dei propri asset

Tier 4 — Integrazione e Conformita (Integration & Compliance)
  Obiettivo: Integrare ITAM con la governance aziendale complessiva
  Requisiti:
    - Integrazione completa con ITSM, sicurezza e finanza
    - Conformita normativa continua (GDPR, SOX, ecc.)
    - Gestione proattiva dei rischi
    - Miglioramento continuo basato sui dati
  Risultato: L'ITAM e parte integrante della strategia aziendale
```

### Integrazione con Altri Standard ISO

L'ISO 19770 non opera in isolamento. La sua efficacia si moltiplica quando integrato con altri standard di gestione:

| Standard | Relazione con ISO 19770 | Valore dell'Integrazione |
|----------|------------------------|--------------------------|
| ISO/IEC 20000-1 (Service Management) | Complementare: ITAM supporta la gestione dei servizi IT | Gli asset sono legati ai servizi che supportano |
| ISO 27001 (Information Security) | Dipendenza: l'inventario asset e requisito di ISO 27001 (A.8) | Visibilita completa degli asset per la gestione della sicurezza |
| ISO 9001 (Quality Management) | Allineamento strutturale: stessa struttura HLS | Integrazione nel sistema di gestione qualita |
| ISO 14001 (Environmental Management) | Complementare: gestione impatto ambientale IT | Tracciamento del ciclo di vita ambientale degli asset |
| ISO 55001 (Asset Management) | Framework superiore: gestione asset in senso lato | ITAM come specializzazione dell'asset management |
| ITIL 4 (IT Service Management) | Pratica ITAM come componente del SVS | Integrazione operativa con incident, change, problem management |

Le revisioni 2024-2025 dello standard hanno introdotto requisiti aggiuntivi relativi al tracciamento dell'impatto ambientale degli asset IT, includendo il consumo energetico dei data center e l'impronta carbonica del ciclo di vita del software dispiegato.

---

## Modello di Maturita ITAM

Il modello di maturita ITAM e un framework strutturato che descrive le fasi progressive attraverso cui le organizzazioni migliorano le proprie capacita di gestione degli asset. Ogni livello rappresenta un grado superiore di disciplina dei processi, automazione e valore per il business. La distanza tra un programma ITAM di Livello 1 e uno di Livello 4, misurata in risultati commerciali, si traduce tipicamente in un risparmio del 15-25% sulla spesa software complessiva dell'organizzazione.

### Livelli di Maturita

```
Livello 1 — Ad Hoc / Caotico
═══════════════════════════════
Caratteristiche:
  - Nessun inventario completo, accurato e aggiornato
  - Gestione reattiva basata su emergenze e richieste puntuali
  - Spreadsheet come strumento principale (se presente)
  - Nessun processo formalizzato per acquisizione o dismissione
  - Mancanza di visibilita sulle licenze software possedute
  - Nessuna correlazione tra asset e servizi/utenti

Rischi:
  - Esposizione massima a penali in caso di vendor audit
  - Impossibilita di rispondere in tempi ragionevoli a richieste di compliance
  - Acquisti duplicati e sprechi non identificati
  - Shadow IT diffusa e incontrollata
  - Superficie di attacco sconosciuta (asset non tracciati)

Indicatore: La maggioranza delle PMI e un numero sorprendente di grandi
            imprese opera ancora a questo livello.


Livello 2 — Reattivo / Compliance-Driven
═════════════════════════════════════════
Caratteristiche:
  - Inventario parziale o basato su scansioni periodiche
  - Processi attivati principalmente in risposta a vendor audit
  - CMDB presente ma con dati spesso obsoleti (accuratezza <70%)
  - Gestione licenze focalizzata sui vendor a piu alto rischio
  - Processi di procurement definiti ma non sempre seguiti
  - Inizio di standardizzazione hardware

Valore principale:
  - Capacita di difesa in caso di audit: dati preparati e difendibili
  - Riduzione delle penali per non-conformita
  - Primo livello di visibilita sul parco installato

Indicatore: L'organizzazione reagisce ai problemi ma non li previene.


Livello 3 — Gestito / Proattivo
════════════════════════════════
Caratteristiche:
  - Inventario automatizzato con agenti di discovery
  - Visibilita continua sulle licenze: utilizzo vs diritti
  - Gestione attiva del consumo (license harvesting operativo)
  - Processi del ciclo di vita definiti e seguiti
  - KPI misurati e reportistica periodica al management
  - Integrazione parziale con ITSM (incident, change management)
  - Budget planning basato su dati storici

Valore principale:
  - Ottimizzazione attiva dei costi (riduzione 10-15% spesa licenze)
  - Tempi di risposta ad audit ridotti a settimane anziche mesi
  - Pianificazione del refresh basata su dati reali
  - Riduzione significativa della Shadow IT

Indicatore: L'organizzazione gestisce proattivamente i propri asset.


Livello 4 — Ottimizzato / Integrato
════════════════════════════════════
Caratteristiche:
  - ITAM completamente automatizzato e integrato nei workflow operativi
  - Integrazione completa con governance e framework operativi
  - Tracking completo dall'approvvigionamento alla dismissione
  - Ottimizzazione finanziaria continua (TCO, right-sizing)
  - Gestione proattiva dei rischi di compliance
  - Dashboard in tempo reale con KPI e trend
  - Cloud e SaaS management integrati nella piattaforma ITAM

Valore principale:
  - Risparmio 15-25% sulla spesa software complessiva
  - Zero sorprese durante i vendor audit
  - Decisioni strategiche basate su dati completi e affidabili
  - Tempi di deployment ridotti grazie a processi ottimizzati

Indicatore: L'ITAM e un enabler strategico per il business.


Livello 5 — Avanzato / Predittivo
══════════════════════════════════
Caratteristiche:
  - Utilizzo di intelligenza artificiale per analisi predittive
  - Cicli di refresh determinati da dati reali (utilizzo, degradazione)
  - ITAM come processo continuo e data-driven
  - Integrazione con FinOps per la gestione dei costi cloud
  - Automazione end-to-end con agentic AI
  - Miglioramento continuo guidato da machine learning
  - Sostenibilita ambientale tracciata e ottimizzata

Valore principale:
  - Anticipazione dei problemi prima che si manifestino
  - Ottimizzazione continua basata su pattern storici
  - Allineamento completo con la strategia digitale dell'organizzazione

Indicatore: L'ITAM evolve autonomamente con le esigenze dell'organizzazione.
```

### Assessment della Maturita

Per valutare il livello di maturita attuale dell'organizzazione, utilizzare il seguente questionario strutturato:

```
ASSESSMENT MATURITA ITAM
==========================

SEZIONE A — Inventario e Discovery (peso: 25%)
-----------------------------------------------
A1. Esiste un inventario centralizzato degli asset IT?
    [ ] No (0 punti)
    [ ] Si, parziale/manuale (1 punto)
    [ ] Si, automatizzato parzialmente (2 punti)
    [ ] Si, automatizzato e aggiornato quotidianamente (3 punti)
    [ ] Si, automatizzato con AI per normalizzazione dati (4 punti)

A2. Quale percentuale di asset e coperta dall'inventario?
    [ ] < 50% (0)  [ ] 50-70% (1)  [ ] 70-85% (2)  [ ] 85-95% (3)  [ ] > 95% (4)

A3. Con quale frequenza viene verificata l'accuratezza dell'inventario?
    [ ] Mai (0)  [ ] Annualmente (1)  [ ] Semestralmente (2)
    [ ] Trimestralmente (3)  [ ] Continuamente (4)

A4. Gli asset cloud e SaaS sono inclusi nell'inventario?
    [ ] No (0)  [ ] Parzialmente (1)  [ ] Principalmente (2)
    [ ] Completamente (3)  [ ] Completamente con costi e utilizzo (4)

SEZIONE B — Gestione Licenze Software (peso: 25%)
---------------------------------------------------
B1. Esiste un processo di riconciliazione licenze-installazioni?
    [ ] No (0)  [ ] Si, manuale occasionale (1)  [ ] Si, semestrale (2)
    [ ] Si, trimestrale automatizzato (3)  [ ] Si, continuo (4)

B2. Il license harvesting e operativo?
    [ ] No (0)  [ ] In fase di valutazione (1)  [ ] Per alcuni vendor (2)
    [ ] Per tutti i vendor principali (3)  [ ] Automatizzato con soglie (4)

B3. L'organizzazione e preparata per un vendor audit immediato?
    [ ] Assolutamente no (0)  [ ] Con difficolta significative (1)
    [ ] Con qualche settimana di preparazione (2)
    [ ] Con pochi giorni di preparazione (3)  [ ] Sempre pronta (4)

SEZIONE C — Ciclo di Vita e Processi (peso: 25%)
--------------------------------------------------
C1. I processi del ciclo di vita sono documentati e seguiti?
    [ ] No (0)  [ ] Parzialmente documentati (1)  [ ] Documentati ma non sempre seguiti (2)
    [ ] Documentati e seguiti (3)  [ ] Documentati, seguiti e misurati (4)

C2. La pianificazione del refresh e strutturata?
    [ ] No (0)  [ ] Reattiva (1)  [ ] Piano annuale (2)
    [ ] Piano triennale (3)  [ ] Piano basato su dati e analisi predittiva (4)

C3. Il processo di dismissione include la sanificazione certificata dei dati?
    [ ] No (0)  [ ] Occasionalmente (1)  [ ] Per asset critici (2)
    [ ] Per tutti gli asset (3)  [ ] Per tutti gli asset con chain of custody completa (4)

SEZIONE D — Integrazione e Governance (peso: 25%)
---------------------------------------------------
D1. L'ITAM e integrato con il sistema ITSM?
    [ ] No (0)  [ ] Parzialmente (1)  [ ] Per incident e change (2)
    [ ] Completamente (3)  [ ] Completamente con automazione (4)

D2. Esistono KPI misurati e reportistica periodica?
    [ ] No (0)  [ ] KPI basilari (1)  [ ] KPI regolari (2)
    [ ] Dashboard in tempo reale (3)  [ ] Dashboard con trend e predizioni (4)

D3. L'ITAM e riconosciuto dal management come funzione strategica?
    [ ] No (0)  [ ] Poco (1)  [ ] In crescita (2)
    [ ] Si, con budget dedicato (3)  [ ] Si, con rappresentanza nel board IT (4)

PUNTEGGIO:
  0-12: Livello 1 (Ad Hoc)
  13-24: Livello 2 (Reattivo)
  25-36: Livello 3 (Gestito)
  37-44: Livello 4 (Ottimizzato)
  45-48: Livello 5 (Avanzato)
```

### Roadmap di Evoluzione

Per pianificare la transizione tra livelli, considerare il seguente percorso tipico:

| Transizione | Durata Tipica | Investimento Chiave | Quick Win |
|-------------|--------------|---------------------|-----------|
| Livello 1 → 2 | 3-6 mesi | Tool di discovery + inventario base | Identificare le prime non-conformita licenze |
| Livello 2 → 3 | 6-12 mesi | Automazione discovery + processi SAM | Primo ciclo di license harvesting |
| Livello 3 → 4 | 12-18 mesi | Integrazione ITSM + governance | Dashboard KPI per il management |
| Livello 4 → 5 | 12-24 mesi | AI/ML + FinOps integration | Analisi predittiva dei guasti |

---

## Gestione Asset Cloud e SaaS

La crescita esponenziale dei servizi cloud e delle applicazioni SaaS ha trasformato radicalmente il panorama ITAM. Le organizzazioni moderne devono gestire un mix eterogeneo di asset on-premises, risorse cloud IaaS/PaaS, applicazioni SaaS e servizi ibridi. Senza una gestione strutturata, il cloud sprawl e il SaaS sprawl generano costi nascosti che possono superare del 30-40% il budget pianificato.

### Cloud Asset Management

La gestione degli asset cloud richiede approcci diversi rispetto all'hardware tradizionale. Le risorse cloud sono effimere, elastiche e distribuite globalmente. I principi fondamentali includono:

**Inventario delle Risorse Cloud:**

```
TEMPLATE INVENTARIO RISORSE CLOUD
====================================

Provider: [AWS / Azure / GCP / Altro]
Account/Subscription ID: _______________
Environment: [Produzione / Staging / Sviluppo / Test / Sandbox]
Cost Center: _______________
Owner: _______________

Risorse Compute:
  - Istanze VM/EC2:        [N] attive, [N] arrestate
  - Container (ECS/AKS):   [N] cluster, [N] pod attivi
  - Serverless (Lambda):    [N] funzioni, [N] invocazioni/mese
  - Kubernetes nodes:       [N] nodi totali

Risorse Storage:
  - Object Storage (S3/Blob): [N] TB, costo: €[X]/mese
  - Block Storage (EBS/Disk): [N] volumi, [N] TB totali
  - File Storage (EFS/Files): [N] share, [N] TB
  - Backup/Snapshot:          [N] snapshot, [N] TB

Risorse Database:
  - Database managed (RDS/SQL): [N] istanze
  - NoSQL (DynamoDB/CosmosDB):  [N] tabelle/collezioni
  - Cache (ElastiCache/Redis):  [N] cluster

Risorse Networking:
  - VPC/VNet:              [N] reti virtuali
  - Load Balancer:         [N] bilanciatori
  - VPN/ExpressRoute:      [N] connessioni
  - DNS zones:             [N] zone

Costo Mensile Stimato: €[X]
Costo Mensile Effettivo: €[X]
Varianza: [+/-] [X]%
```

**Tagging Strategy per le Risorse Cloud:**

L'implementazione di un sistema di tagging coerente e il prerequisito fondamentale per la gestione dei costi e la governance cloud. Definire uno schema di tag obbligatori che copra almeno le seguenti dimensioni:

```
Tag Obbligatori per Risorse Cloud:
===================================
environment:    prod | staging | dev | test | sandbox
owner:          email del proprietario tecnico
cost-center:    codice centro di costo
project:        nome progetto / applicazione
team:           team responsabile
data-class:     public | internal | confidential | restricted
backup:         required | optional | none
auto-shutdown:  true | false (per ambienti non-prod)
created-by:     processo/persona che ha creato la risorsa
expiry-date:    data di scadenza prevista (per risorse temporanee)

Esempio AWS:
  aws ec2 create-tags --resources i-1234567890abcdef0 \
    --tags Key=environment,Value=prod \
           Key=owner,Value=mario.rossi@azienda.it \
           Key=cost-center,Value=CC-IT-0042 \
           Key=project,Value=ERP-Migration \
           Key=team,Value=infrastructure \
           Key=data-class,Value=confidential

Esempio Azure:
  az resource tag --tags \
    environment=prod \
    owner=mario.rossi@azienda.it \
    cost-center=CC-IT-0042 \
    project=ERP-Migration \
    --ids /subscriptions/.../resourceGroups/.../providers/...
```

**Rilevamento Risorse Cloud Orfane:**

Le risorse cloud "orfane" — risorse attive ma non utilizzate — sono una delle principali fonti di spreco. Script e procedure per identificarle:

```bash
# AWS — Identificare volumi EBS non collegati
aws ec2 describe-volumes \
    --filters Name=status,Values=available \
    --query 'Volumes[*].{ID:VolumeId,Size:Size,Created:CreateTime}' \
    --output table

# AWS — Identificare Elastic IP non associati
aws ec2 describe-addresses \
    --query 'Addresses[?AssociationId==null].{IP:PublicIp,AllocId:AllocationId}' \
    --output table

# AWS — Identificare snapshot obsoleti (piu vecchi di 90 giorni)
aws ec2 describe-snapshots --owner-ids self \
    --query "Snapshots[?StartTime<='$(date -d '-90 days' +%Y-%m-%d)'].{ID:SnapshotId,Size:VolumeSize,Date:StartTime}" \
    --output table

# Azure — Identificare dischi non collegati
az disk list --query "[?managedBy==null].{Name:name,Size:diskSizeGb,RG:resourceGroup}" \
    --output table

# Azure — Identificare IP pubblici non associati
az network public-ip list \
    --query "[?ipConfiguration==null].{Name:name,IP:ipAddress,RG:resourceGroup}" \
    --output table
```

### SaaS Management Platform

Le piattaforme di gestione SaaS (SMP) forniscono visibilita e controllo sull'ecosistema di applicazioni SaaS dell'organizzazione. Nel 2025-2026, il mercato SMP e dominato da soluzioni che combinano discovery automatica, ottimizzazione delle licenze e automazione dei workflow.

**Funzionalita Chiave delle Piattaforme SMP:**

| Funzionalita | Descrizione | Valore |
|-------------|-------------|--------|
| Discovery automatica | Rilevamento di tutte le app SaaS in uso tramite SSO, email, browser extension, API | Eliminazione dei punti ciechi |
| Ottimizzazione licenze | Analisi dell'utilizzo effettivo vs licenze acquistate | Riduzione costi 20-30% |
| Gestione onboarding/offboarding | Automazione provisioning e de-provisioning utenti | Riduzione rischi sicurezza |
| Workflow approvazione | Processi strutturati per richiesta nuove app | Controllo della Shadow IT |
| Analisi contrattuale | Tracking scadenze, rinnovi automatici, termini | Negoziazione informata |
| Compliance monitoring | Verifica conformita a policy aziendali e normative | Riduzione rischi |
| Spend analytics | Visibilita sulla spesa SaaS per team, progetto, categoria | Ottimizzazione budget |

**Piattaforme SMP di Riferimento (2025-2026):**

```
Piattaforme Enterprise:
  - Zylo: Leader di mercato, specializzata in SaaS management e ottimizzazione.
    Focus su spend analytics e contract management.
    Ideale per organizzazioni con 500+ applicazioni SaaS.

  - BetterCloud: Leader nel Gartner Magic Quadrant per SaaS Management
    Platforms (2025). Eccelle nell'automazione dei workflow IT
    e nella gestione del ciclo di vita degli utenti SaaS.

  - CloudEagle: Piattaforma AI-powered con modello "Savings-as-a-Service".
    Piu di $2 miliardi in risparmi dichiarati dai clienti.
    Forte nell'assistenza alla negoziazione con i vendor.

  - Flexera One: Piattaforma ITAM completa che consolida dati di asset
    software, hardware e SaaS in una vista normalizzata unica.
    Eccelle nella gestione di ambienti ibridi complessi.

  - Torii: Focus su automazione SaaS, discovery e ottimizzazione.
    Forte nella gestione dell'onboarding/offboarding
    e nella rilevazione della Shadow IT.

Piattaforme per PMI:
  - Zluri: Moderna piattaforma SMP con profonda visibilita sull'ecosistema
    SaaS. Ottima per organizzazioni in crescita.

  - Productiv: Piattaforma SaaS intelligence con analytics avanzate
    sull'engagement e l'utilizzo delle applicazioni.
```

### FinOps e Ottimizzazione dei Costi Cloud

Il **FinOps** (Financial Operations) e la pratica di gestione finanziaria del cloud che unisce tecnologia, finanza e business per massimizzare il valore dell'investimento cloud. Il framework FinOps 2025 introduce il concetto di **Scopes**, che consente alle organizzazioni di segmentare la pratica FinOps per aree specifiche di spesa tecnologica (IaaS, SaaS, AI).

**Le Tre Fasi del FinOps:**

```
Fase 1 — INFORM (Informare)
  Obiettivo: Visibilita completa sui costi cloud
  Attivita:
    - Implementazione del tagging obbligatorio
    - Allocazione dei costi ai centri di costo
    - Dashboard di visualizzazione dei costi in tempo reale
    - Showback/Chargeback ai dipartimenti
    - Anomaly detection per picchi di spesa inattesi

Fase 2 — OPTIMIZE (Ottimizzare)
  Obiettivo: Riduzione della spesa senza impatto sulle prestazioni
  Attivita:
    - Right-sizing delle istanze sottoutilizzate
    - Acquisto di Reserved Instances e Savings Plans
    - Eliminazione delle risorse orfane e inutilizzate
    - Scheduling degli ambienti non-prod (auto-shutdown notturno)
    - Selezione delle regioni ottimali per costo
    - Utilizzo di spot/preemptible instances per carichi toleranti

Fase 3 — OPERATE (Operare)
  Obiettivo: Governance continua e miglioramento
  Attivita:
    - Policy automatizzate per compliance dei costi
    - Budget alert e threshold notification
    - Review periodiche dei commitment (RI/SP)
    - Benchmarking interno tra team e progetti
    - Continuous optimization loop
```

**Strumenti FinOps Nativi dei Cloud Provider:**

| Strumento | Provider | Funzionalita Chiave |
|-----------|----------|---------------------|
| AWS Cost Explorer | AWS | Analisi costi, forecast, raccomandazioni RI |
| AWS Cost Optimization Hub | AWS | Hub centralizzato con integrazione Amazon Q |
| Azure Cost Management | Azure | Analisi costi, budget, advisor, export |
| Google Cloud Billing | GCP | Reports, budget, allocazione, raccomandazioni |
| OCI Cost Analysis | Oracle | Analisi costi, tagging, budget tracking |

**Template Report FinOps Mensile:**

```
REPORT FINOPS MENSILE
=======================
Periodo: [MESE/ANNO]
Budget mensile: €[X]
Spesa effettiva: €[X]
Varianza: [+/-] [X]% ([sotto/sopra] budget)

DISTRIBUZIONE PER PROVIDER:
  AWS:    €[X] ([%]) — [trend vs mese precedente]
  Azure:  €[X] ([%]) — [trend vs mese precedente]
  GCP:    €[X] ([%]) — [trend vs mese precedente]

DISTRIBUZIONE PER AMBIENTE:
  Produzione:  €[X] ([%])
  Staging:     €[X] ([%])
  Sviluppo:    €[X] ([%])
  Test:        €[X] ([%])

TOP 5 SERVIZI PER COSTO:
  1. [Servizio] — €[X] ([trend])
  2. [Servizio] — €[X] ([trend])
  3. [Servizio] — €[X] ([trend])
  4. [Servizio] — €[X] ([trend])
  5. [Servizio] — €[X] ([trend])

RISORSE NON TAGGATE: [N] risorse, €[X] costo stimato
RISORSE ORFANE IDENTIFICATE: [N], costo mensile: €[X]
RACCOMANDAZIONI RIGHT-SIZING: [N] istanze, risparmio potenziale: €[X]/mese
COMMITMENT UTILIZATION: RI [X]%, SP [X]%

AZIONI IN CORSO:
  - [Azione 1]: responsabile, deadline, risparmio atteso
  - [Azione 2]: responsabile, deadline, risparmio atteso
```

### Governance Multi-Cloud

Per le organizzazioni che operano su piu cloud provider, la governance centralizzata e essenziale per evitare la frammentazione della gestione e l'esplosione dei costi:

**Principi di Governance Multi-Cloud:**

1. **Inventario unificato**: Un unico registro che includa tutte le risorse di tutti i provider, normalizzato con uno schema di tagging comune
2. **Policy consistenti**: Regole di sicurezza, compliance e costi applicate uniformemente su tutti i cloud
3. **Visibilita centralizzata**: Dashboard unica che aggreghi costi, utilizzo e compliance di tutti i provider
4. **FinOps team dedicato**: Ruolo cross-funzionale che coordini le pratiche di ottimizzazione su tutti i cloud
5. **Landing zone standardizzate**: Template di architettura pre-approvati per ogni provider
6. **Single pane of glass**: Piattaforma centralizzata per la gestione operativa di tutti gli ambienti

**Strumenti di Governance Multi-Cloud:**

```
Piattaforme Commerciali:
  - Flexera One: Normalizzazione asset e costi multi-cloud
  - CloudHealth (VMware): Governance e ottimizzazione multi-cloud
  - Cloudability (Apptio): FinOps e allocazione costi multi-cloud
  - Spot by NetApp: Ottimizzazione automatizzata dei workload

Piattaforme Open-Source:
  - OpenCost: Standard open-source per il monitoraggio dei costi Kubernetes
  - Cloud Custodian: Policy-as-code per governance cloud multi-provider
  - Infracost: Stima dei costi dell'infrastruttura Terraform prima del deploy
  - Steampipe: Query SQL su risorse cloud multi-provider
```

---

## Shadow IT e Shadow AI

### Dimensione del Fenomeno

La Shadow IT — l'utilizzo di hardware, software e servizi cloud senza l'approvazione o la conoscenza del dipartimento IT — rappresenta una sfida crescente per le organizzazioni. Nel 2025, la Shadow IT copre stimatamente il 30-40% dell'utilizzo tecnologico aziendale, con una crescita significativa guidata dalla facilita di accesso ai servizi cloud e SaaS e dalla diffusione del lavoro remoto.

**Tipologie di Shadow IT:**

| Categoria | Esempi | Rischio |
|-----------|--------|---------|
| SaaS non approvato | Trello, Notion, Canva, tool di AI generativa | Dati aziendali su piattaforme non controllate |
| IaaS/PaaS non approvato | Account AWS/Azure personali, Heroku, Vercel | Infrastruttura non conforme alle policy di sicurezza |
| Hardware personale | Laptop, smartphone, chiavette USB, NAS personali | Potenziale vettore di malware, data leakage |
| Servizi di comunicazione | WhatsApp, Telegram, Signal per comunicazioni di lavoro | Violazione policy di data retention |
| Storage cloud personale | Google Drive personale, Dropbox free, OneDrive personale | Dati aziendali fuori dal perimetro controllato |
| Strumenti di sviluppo | IDE cloud, repository personali, CI/CD non approvati | Codice sorgente fuori dal controllo aziendale |

### Tecniche di Rilevamento Avanzate

Il rilevamento della Shadow IT richiede un approccio multi-sorgente che combini diverse tecniche complementari:

**1. Analisi del Traffico di Rete:**

```bash
# Analisi dei log DNS per identificare domini SaaS non approvati
# Esempio con log del DNS resolver aziendale

# Estrarre i domini piu frequentati non nella whitelist
awk '{print $8}' /var/log/named/query.log | \
    sort | uniq -c | sort -rn | head -100 | \
    while read count domain; do
        grep -q "$domain" /etc/itam/approved_domains.txt || \
            echo "NON APPROVATO: $count query - $domain"
    done

# Analisi dei log del proxy web (Squid esempio)
grep -oP 'https?://[^/]+' /var/log/squid/access.log | \
    sort | uniq -c | sort -rn | head -200 | \
    while read count url; do
        domain=$(echo "$url" | awk -F/ '{print $3}')
        grep -q "$domain" /etc/itam/approved_domains.txt || \
            echo "SHADOW IT POTENZIALE: $count accessi - $domain"
    done
```

**2. Analisi delle Integrazioni SSO/IdP:**

Le applicazioni che supportano SSO (Single Sign-On) possono essere rilevate tramite i log dell'Identity Provider (Entra ID, Okta, ecc.):

```powershell
# Microsoft Entra ID — Elenco applicazioni con consent utente
# (Applicazioni a cui gli utenti hanno concesso accesso senza approvazione IT)
Connect-MgGraph -Scopes "AuditLog.Read.All"
Get-MgAuditLogDirectoryAudit -Filter "activityDisplayName eq 'Consent to application'" |
    Select-Object ActivityDateTime, InitiatedBy, TargetResources |
    Export-Csv -Path "C:\audit\user_consented_apps.csv" -NoTypeInformation
```

**3. Analisi delle Note Spese:**

Monitorare le note spese aziendali per identificare sottoscrizioni SaaS acquistate con carte di credito aziendali senza approvazione IT. Parole chiave da cercare: "subscription", "monthly", "annual", "license", nomi di vendor SaaS noti.

**4. Cloud Access Security Broker (CASB):**

I CASB forniscono visibilita in tempo reale sull'utilizzo dei servizi cloud da parte degli utenti aziendali. Funzionalita chiave:

- Rilevamento automatico di servizi cloud in uso (tipicamente 1000+ servizi in organizzazioni medie)
- Valutazione del rischio di ogni servizio (sicurezza, conformita, affidabilita)
- Applicazione di policy in linea (blocco, allow, coach, encrypt)
- Data Loss Prevention (DLP) per prevenire l'esfiltrazione di dati sensibili
- Visibilita sull'utilizzo di servizi cloud anche da reti esterne (agent-based)

**5. Endpoint Detection:**

```powershell
# Rilevamento processi sospetti su endpoint Windows
# Confronto tra processi in esecuzione e whitelist approvata

$approvedProcesses = Get-Content "C:\admin\approved_processes.txt"
$runningProcesses = Get-Process | Select-Object -ExpandProperty Name -Unique

$shadowProcesses = $runningProcesses | Where-Object { $_ -notin $approvedProcesses }
if ($shadowProcesses) {
    Write-Warning "Processi non approvati rilevati:"
    foreach ($proc in $shadowProcesses) {
        $details = Get-Process -Name $proc -ErrorAction SilentlyContinue |
            Select-Object -First 1 Name, Path, Company, Description
        Write-Output "  - $($details.Name): $($details.Path) [$($details.Company)]"
    }
}
```

### Shadow AI: La Nuova Frontiera

A partire dal 2024-2025, la Shadow AI e emersa come una sottocategoria particolarmente critica della Shadow IT. I dipendenti utilizzano strumenti di intelligenza artificiale generativa (ChatGPT, Claude, Gemini, Midjourney, Copilot e decine di altri) senza approvazione, caricando potenzialmente dati aziendali sensibili, codice sorgente proprietario, documenti riservati e informazioni personali su piattaforme esterne.

**Rischi Specifici della Shadow AI:**

- **Data leakage**: Dati aziendali sensibili caricati come prompt o contesto in tool AI esterni
- **Proprieta intellettuale**: Codice sorgente e design proprietari condivisi con servizi AI
- **Conformita normativa**: Dati personali (GDPR) o dati regolamentati trasmessi a servizi non approvati
- **Qualita e affidabilita**: Output AI non verificati utilizzati in decisioni aziendali
- **Rischio legale**: Contenuti generati con AI che violano copyright o licenze

**Rilevamento della Shadow AI:**

La Shadow AI e piu difficile da rilevare della Shadow IT tradizionale perche spesso opera all'interno di applicazioni gia approvate (es. funzionalita AI integrate in tool esistenti). Le tecniche di rilevamento includono:

- Monitoraggio del traffico verso domini di servizi AI noti (api.openai.com, claude.ai, gemini.google.com, ecc.)
- Analisi dei pattern di upload: volumi anomali di dati in uscita verso servizi AI
- Browser extension monitoring per plugin AI non approvati
- Endpoint agent che rilevi l'utilizzo di applicazioni AI desktop
- Analisi dei log di Identity Provider per consent a app AI

### Strategia di Contenimento

La strategia piu efficace non e il blocco totale, ma la combinazione di governance, educazione e alternative approvate:

```
STRATEGIA DI CONTENIMENTO SHADOW IT / SHADOW AI
=================================================

1. DISCOVER — Identificare
   - Implementare strumenti di discovery multi-sorgente
   - Condurre assessment periodici della Shadow IT
   - Analizzare trend e pattern di adozione non autorizzata

2. ASSESS — Valutare
   - Classificare i servizi rilevati per rischio (alto/medio/basso)
   - Valutare se il servizio risponde a un'esigenza legittima
   - Identificare alternative approvate o approvabili

3. GOVERN — Governare
   - Per servizi a basso rischio: valutare l'approvazione formale
   - Per servizi a rischio medio: negoziare contratti enterprise
   - Per servizi ad alto rischio: bloccare e fornire alternative
   - Per la Shadow AI: definire policy d'uso accettabile con guardrail

4. ENABLE — Abilitare
   - Creare un catalogo self-service di app e servizi approvati
   - Semplificare il processo di richiesta di nuove app
   - Fornire piattaforme AI aziendali approvate con DLP integrato
   - Formare gli utenti su rischi e alternative

5. MONITOR — Monitorare
   - Monitoraggio continuo per nuove istanze di Shadow IT/AI
   - Reportistica periodica al management
   - Aggiornamento continuo del catalogo approvato
```

---

## Integrazione CMDB e ITSM

### CMDB vs Asset Database

Il CMDB (Configuration Management Database) e il database degli asset IT sono concetti correlati ma distinti. Comprendere la differenza e fondamentale per implementare una gestione efficace:

| Aspetto | Asset Database (ITAM) | CMDB (Configuration Management) |
|---------|----------------------|--------------------------------|
| Focus | Cosa possediamo e il suo valore | Come gli elementi sono configurati e connessi |
| Dati principali | Acquisto, costo, garanzia, licenza, ubicazione | Configurazione, relazioni, dipendenze, servizi |
| Granularita | Asset fisico o logico completo | Configuration Item (CI) con attributi specifici |
| Ciclo di vita | Dall'acquisto allo smaltimento | Dalla configurazione al ritiro del servizio |
| Utenti principali | Finance, procurement, compliance | Operations, change management, incident management |
| Domanda chiave | "Quanto abbiamo speso e cosa possediamo?" | "Cosa sara impattato se questo CI cambia?" |

**Integrazione delle Due Viste:**

L'approccio ottimale prevede l'integrazione delle informazioni finanziarie e di ciclo di vita dell'ITAM con le informazioni di configurazione e relazione del CMDB. Questo consente di rispondere simultaneamente a domande come:

- "Quanto costa mantenere il servizio email aziendale?" (asset + CMDB)
- "Se il server X si guasta, quali servizi saranno impattati?" (CMDB)
- "La garanzia del server X e scaduta?" (ITAM)
- "Quali utenti saranno impattati se aggiorniamo il software Y?" (CMDB + ITAM)

### Relationship Mapping e Impact Analysis

La potenza del CMDB risiede nella sua capacita di modellare le relazioni tra Configuration Item (CI). L'impact analysis consente di prevedere le conseguenze di guasti o cambiamenti prima che si verifichino:

```
Esempio di Relationship Mapping:
=================================

Servizio: ERP Aziendale (SAP S/4HANA)
├── Application: SAP S/4HANA
│   ├── Database: SAP HANA DB
│   │   ├── Server: SRV-DB-01 (primario)
│   │   │   ├── Storage: SAN-LUN-042
│   │   │   ├── Network: VLAN 200, IP 10.0.2.10
│   │   │   └── UPS: UPS-DC-01
│   │   └── Server: SRV-DB-02 (replica)
│   │       ├── Storage: SAN-LUN-043
│   │       ├── Network: VLAN 200, IP 10.0.2.11
│   │       └── UPS: UPS-DC-01
│   ├── Application Server: SRV-APP-01
│   │   ├── Network: VLAN 300, IP 10.0.3.10
│   │   └── Load Balancer: LB-PROD-01
│   └── Application Server: SRV-APP-02
│       ├── Network: VLAN 300, IP 10.0.3.11
│       └── Load Balancer: LB-PROD-01
├── Infrastructure:
│   ├── Firewall: FW-CORE-01
│   ├── Switch Core: SW-CORE-01
│   └── Router: RTR-WAN-01
└── Users: 450 utenti (Dipartimenti: Finance, HR, Operations, Sales)

Impact Analysis:
  Se SRV-DB-01 guasto → Failover su SRV-DB-02 (impatto: <5 min)
  Se SAN-LUN-042 guasto → Database primario offline, failover su replica
  Se SW-CORE-01 guasto → TUTTO il servizio ERP offline (CRITICO)
  Se LB-PROD-01 guasto → Application server non raggiungibili (CRITICO)
  Se UPS-DC-01 guasto → Rischio shutdown non controllato di DB primario e replica
```

### Integrazione con Change Management

L'integrazione ITAM-CMDB con il change management garantisce che ogni modifica all'infrastruttura sia tracciata e che l'impatto sia valutato prima dell'implementazione:

**Workflow Integrato Change-CMDB-ITAM:**

```
1. Richiesta di Change (RFC)
   ├── Identificazione dei CI impattati (CMDB lookup)
   ├── Valutazione dell'impatto sui servizi (CMDB relationship)
   ├── Verifica stato garanzia/supporto degli asset (ITAM)
   └── Verifica disponibilita licenze software necessarie (SAM)

2. Approvazione
   ├── CAB review con dati CMDB e ITAM
   ├── Risk assessment basato su impact analysis
   └── Pianificazione finestra di manutenzione

3. Implementazione
   ├── Esecuzione del change secondo il piano approvato
   ├── Aggiornamento del CMDB con nuova configurazione
   └── Aggiornamento dell'inventario ITAM se hardware/software modificato

4. Post-Implementation Review
   ├── Verifica che il CMDB rifletta lo stato attuale
   ├── Conferma che l'inventario ITAM sia aggiornato
   └── Chiusura del change record con evidenza degli aggiornamenti
```

### Federation e Data Quality

La qualita dei dati nel CMDB e nell'inventario ITAM e il fattore critico di successo. Un CMDB con dati inaccurati e peggio di nessun CMDB, perche genera decisioni basate su informazioni errate.

**Strategie per la Data Quality:**

- **Automated discovery**: Scansioni continue come fonte primaria di dati, non inserimenti manuali
- **Reconciliation rules**: Regole automatiche per la riconciliazione tra fonti dati multiple
- **Data normalization**: Normalizzazione automatica dei nomi vendor, modelli e versioni software
- **Deduplication**: Algoritmi di deduplicazione basati su serial number, MAC address e hostname
- **Confidence scoring**: Punteggio di affidabilita per ogni record basato sulla freschezza e la fonte dei dati
- **Stale data cleanup**: Processi automatici per identificare e gestire record obsoleti
- **Data steward**: Ruolo dedicato alla governance della qualita dei dati del CMDB

**KPI di Data Quality:**

| KPI | Descrizione | Target |
|-----|-------------|--------|
| Accuratezza | % di record che corrispondono alla realta verificata | > 95% |
| Completezza | % di campi obbligatori compilati su tutti i record | > 98% |
| Freschezza | % di record aggiornati negli ultimi 30 giorni | > 90% |
| Unicita | % di record senza duplicati | > 99% |
| Consistenza | % di record con valori coerenti tra campi correlati | > 95% |

---

## Conformita Normativa e GDPR

### GDPR e Ciclo di Vita degli Asset

Il Regolamento Generale sulla Protezione dei Dati (GDPR) ha un impatto diretto sulla gestione degli asset IT, in particolare nelle fasi di riassegnazione, riparazione e dismissione. Ogni dispositivo IT puo contenere dati personali che devono essere protetti durante l'intero ciclo di vita dell'asset e cancellati in modo sicuro quando l'asset viene dismesso.

**Obblighi GDPR Rilevanti per l'ITAM:**

| Articolo GDPR | Requisito | Implicazione per l'ITAM |
|--------------|-----------|------------------------|
| Art. 5(1)(f) | Integrita e riservatezza dei dati | Protezione dei dati su tutti gli asset IT |
| Art. 17 | Diritto alla cancellazione | Capacita di cancellare dati da asset specifici su richiesta |
| Art. 28 | Responsabile del trattamento | Contratti con fornitori ITAD che trattano dati |
| Art. 30 | Registro dei trattamenti | Documentazione degli asset che trattano dati personali |
| Art. 32 | Sicurezza del trattamento | Misure tecniche adeguate su tutti gli asset |
| Art. 33 | Notifica violazione | Capacita di identificare rapidamente asset compromessi |
| Art. 35 | DPIA | Valutazione d'impatto per nuove tecnologie |

**Sanzioni**: Le sanzioni per non-conformita GDPR possono raggiungere i 20 milioni di euro o il 4% del fatturato globale annuo, a seconda di quale importo sia superiore.

### Audit Trail e Tracciabilita

Il GDPR richiede la capacita di dimostrare la conformita (principio di accountability, Art. 5(2)). Per l'ITAM, questo si traduce nella necessita di mantenere un audit trail completo per ogni asset che tratta dati personali:

```
AUDIT TRAIL GDPR PER ASSET IT
================================

Asset: HW-LAP-0287 (Dell Latitude 7440, SN: XYZ789)
Classificazione dati: Contiene dati personali (HR, CRM)

Data        | Evento                          | Responsabile   | Evidenza
------------|--------------------------------|----------------|-------------------
2025-01-15  | Acquisto e registrazione CMDB   | IT Procurement | PO #2025-0042
2025-01-17  | Installazione OS e cifratura    | IT Operations  | BitLocker Key ID
2025-01-18  | Join dominio + GPO applicate    | IT Operations  | AD Computer Object
2025-01-20  | Assegnato a Mario Rossi (HR)    | IT Service Desk| Modulo assegnazione
2025-06-10  | Riparazione schermo (in loco)   | Fornitore XYZ  | Ticket #INC-4521
2025-11-05  | Riassegnato a Laura Bianchi     | IT Service Desk| Modulo trasferimento
2025-11-05  | Profilo utente precedente rimosso| IT Operations  | Script log
2026-03-20  | Dismissione per fine ciclo      | IT Operations  | Modulo dismissione
2026-03-20  | Sanificazione NVMe (Crypto Erase)| IT Operations | Certificato #CE-0189
2026-03-25  | Consegnato a ITAD certificato   | IT Operations  | FIR + DPA firmata
```

### Data Processing Agreement per ITAD

Quando lo smaltimento degli asset IT (IT Asset Disposition, ITAD) e affidato a un fornitore esterno, il GDPR richiede un **Data Processing Agreement (DPA)** che formalizzi il rapporto tra Titolare e Responsabile del trattamento:

```
CHECKLIST DPA PER FORNITORE ITAD
==================================

[ ] Descrizione del trattamento (natura, finalita, durata)
[ ] Tipologie di dati personali potenzialmente presenti sugli asset
[ ] Categorie di interessati i cui dati potrebbero essere presenti
[ ] Obblighi di riservatezza del personale del fornitore
[ ] Misure tecniche e organizzative per la sicurezza (Art. 32)
[ ] Condizioni per il ricorso a sub-responsabili
[ ] Obbligo di assistenza al Titolare per le richieste degli interessati
[ ] Obbligo di restituzione o cancellazione dei dati al termine
[ ] Obbligo di messa a disposizione delle informazioni per audit
[ ] Notifica tempestiva in caso di violazione dei dati

Certificazioni richieste al fornitore ITAD:
  - ISO 27001 (Information Security Management)
  - ISO 14001 (Environmental Management)
  - R2 o e-Stewards (standard ITAD specifici)
  - Iscrizione all'Albo Nazionale Gestori Ambientali
  - Conformita WEEE/RAEE per lo smaltimento dei rifiuti elettronici
```

---

## Vendor Audit: Preparazione e Difesa

### Anatomia di un Vendor Audit

I vendor software (Microsoft, Oracle, SAP, IBM, Adobe) conducono regolarmente audit di conformita licenze presso i propri clienti. Comprendere l'anatomia di un audit e fondamentale per prepararsi adeguatamente. Secondo le statistiche di settore, il 64% delle aziende sottoposte ad audit negli ultimi tre anni ha dovuto pagare costi aggiuntivi per non-conformita: il 35% ha pagato piu di 100.000 dollari e il 10% ha pagato oltre un milione di dollari. Oracle da solo genera un fatturato stimato di 3 miliardi di dollari annui dalle attivita di audit software, pari al 6% del suo fatturato totale.

**Fasi Tipiche di un Vendor Audit:**

```
TIMELINE DI UN VENDOR AUDIT
=============================

Settimana 0: NOTIFICA
  - Ricezione della lettera di audit dal vendor (o dal suo rappresentante)
  - Citazione della clausola contrattuale che autorizza l'audit
  - Richiesta di collaborazione e definizione delle tempistiche
  - Tipicamente: 30-90 giorni dalla notifica all'inizio dell'audit

Settimane 1-2: PREPARAZIONE INTERNA
  - Revisione dei contratti di licenza e dei diritti acquisiti
  - Raccolta delle prove di acquisto (PO, fatture, certificati)
  - Esecuzione dell'inventario software interno
  - Coinvolgimento del consulente legale (se necessario)
  - Nomina di un referente unico per le comunicazioni con il vendor

Settimane 3-6: RACCOLTA DATI
  - Il vendor richiede l'esecuzione di script di discovery
  - Revisione degli script PRIMA dell'esecuzione (sicurezza)
  - Esecuzione della scansione negli ambienti concordati
  - Consegna dei dati di inventario al vendor

Settimane 7-12: ANALISI
  - Il vendor analizza i dati di inventario
  - Confronto tra installazioni rilevate e diritti di licenza
  - Identificazione delle discrepanze (gap analysis)
  - ATTENZIONE: il vendor tendera a interpretare le ambiguita a suo favore

Settimane 13-16: REPORT E NEGOZIAZIONE
  - Ricezione del report preliminare dal vendor
  - Revisione interna del report (contestare errori e interpretazioni)
  - Negoziazione del settlement (quantificazione del gap, piano di remediation)
  - Accordo finale e chiusura dell'audit

Durata tipica totale: 3-6 mesi
Costo medio in ore lavoro interne: 60+ giornate
```

### Preparazione Proattiva

La migliore difesa contro i vendor audit e la preparazione proattiva e continua:

**Programma di Audit Readiness:**

```
AUDIT READINESS — PROGRAMMA TRIMESTRALE
==========================================

TRIMESTRE 1 (Gennaio-Marzo): MICROSOFT
  [ ] Inventario installazioni Microsoft (OS, Office, Server, SQL, CAL)
  [ ] Riconciliazione con licenze VLSC / Admin Center M365
  [ ] Verifica corretta assegnazione licenze M365 per utente
  [ ] Controllo licenze CAL (Device vs User, standard vs enterprise)
  [ ] Documentazione virtual rights (licenze server in ambienti virtualizzati)
  [ ] Archiviazione prove di acquisto aggiornate

TRIMESTRE 2 (Aprile-Giugno): ORACLE
  [ ] Inventario installazioni Oracle (Database, Middleware, Java)
  [ ] ATTENZIONE: Oracle Java SE richiede licenza commerciale dal 2019
  [ ] Verifica metriche di licenza (NUP vs Processor, edizione)
  [ ] Controllo ambienti virtualizzati (Oracle policy su VMware = soft partition)
  [ ] Verifica Oracle DB Options e Management Packs attivati
  [ ] Controllo Java runtime su tutti gli endpoint

TRIMESTRE 3 (Luglio-Settembre): SAP
  [ ] Inventario utenti SAP per tipologia (Professional, Limited, ecc.)
  [ ] Verifica Indirect/Digital Access (accesso indiretto tramite API/interfacce)
  [ ] Controllo motori di database utilizzati con SAP
  [ ] Riconciliazione con Named User License Agreement (NULA)

TRIMESTRE 4 (Ottobre-Dicembre): ADOBE + ALTRI VENDOR
  [ ] Inventario installazioni Adobe (Creative Cloud, Acrobat, ecc.)
  [ ] Verifica assegnazioni Adobe Named User License
  [ ] Controllo altri vendor significativi (VMware, Citrix, IBM, ecc.)
  [ ] Revisione annuale complessiva della posizione di compliance
```

### Gestione dell'Audit in Corso

Quando un vendor notifica un audit, seguire questa procedura strutturata:

1. **Non ignorare la notifica**: Ignorare una richiesta di audit puo comportare azioni legali e penali aggiuntive
2. **Coinvolgere immediatamente il consulente legale**: Esaminare i diritti di audit previsti dal contratto
3. **Nominare un single point of contact**: Tutte le comunicazioni devono passare da una persona designata
4. **Controllare l'ambito dell'audit**: L'audit deve limitarsi a quanto previsto contrattualmente
5. **Esaminare gli script di discovery**: Non eseguire script non verificati; possono raccogliere piu dati del necessario
6. **Documentare tutto**: Ogni comunicazione, ogni dato fornito, ogni contestazione
7. **Contestare le interpretazioni sfavorevoli**: I vendor tendono a interpretare le ambiguita a proprio vantaggio
8. **Negoziare il settlement**: Il primo importo proposto dal vendor e quasi sempre negoziabile
9. **Pianificare la remediation**: Acquistare le licenze mancanti o rimuovere il software in eccesso

### Scenari di Audit per Vendor

**Microsoft — Aree di Attenzione:**

```
Rischi frequenti negli audit Microsoft:
  - Windows Server: licenze per core insufficienti (minimo 16 core per server fisico)
  - SQL Server: edizione Enterprise installata con licenza Standard
  - CAL (Client Access License): numero insufficiente o tipo errato (Device vs User)
  - Microsoft 365: utenti disabilitati con licenza ancora assegnata
  - Office: versioni diverse installate rispetto alla licenza VL
  - Diritti di virtualizzazione: licenze Datacenter vs Standard in ambienti VMware
  - Extended Security Updates (ESU): Windows Server 2012 R2 in produzione senza ESU
```

**Oracle — Aree di Attenzione:**

```
Rischi frequenti negli audit Oracle:
  - Oracle Database: Options e Management Packs attivati ma non licenziati
    (es. Diagnostics Pack, Tuning Pack attivi per default in alcune installazioni)
  - Metriche di licenza: NUP (Named User Plus) con piu utenti del consentito
  - Virtualizzazione: Oracle non riconosce VMware come "hard partitioning"
    (tutta l'infrastruttura VMware cluster deve essere licenziata)
  - Java SE: utilizzo commerciale senza licenza Enterprise (dal 2019)
  - Oracle DB Free/XE: rischio di installazioni di versioni complete
    durante lo sviluppo che migrano in produzione
  - Fusioni e acquisizioni: licenze dell'azienda acquisita non trasferibili
```

---

## Automazione e Intelligenza Artificiale nell'ITAM

Le tendenze 2025-2026 mostrano un passaggio dall'ITAM reattivo e manuale a un ITAM predittivo, automatizzato e profondamente integrato con le funzioni di sicurezza e finanza. L'intelligenza artificiale sta trasformando ogni aspetto della gestione degli asset IT.

### AI per la Discovery e Normalizzazione

Uno dei problemi piu persistenti nell'ITAM e la qualita dei dati di inventario. Lo stesso software puo apparire con decine di nomi diversi nel database (es. "Microsoft Office Professional Plus 2021", "MS Office Pro Plus 21", "MSOFFICE2021PP"). L'AI risolve questo problema attraverso:

- **Normalizzazione dei titoli software**: Modelli di NLP che mappano varianti dello stesso titolo a un'unica voce del catalogo normalizzato
- **Normalizzazione dei modelli hardware**: Riconoscimento e unificazione delle varianti di modello da fonti diverse
- **Normalizzazione dei nomi vendor**: Mappatura delle varianti dei nomi dei produttori
- **Classificazione automatica**: Categorizzazione automatica degli asset scoperti in base alle caratteristiche rilevate
- **Anomaly detection**: Identificazione di asset con configurazioni anomale o comportamenti insoliti

**Esempio di Normalizzazione AI-Assisted:**

```
INPUT (Dati grezzi da discovery multiple):
  - "Adobe Acrobat Pro DC" (fonte: agente endpoint)
  - "Adobe Acrobat Professional - Continuous" (fonte: SCCM)
  - "AcrobatPro_DC" (fonte: registro Windows)
  - "com.adobe.acrobat.pro" (fonte: MDM mobile)

OUTPUT (Dopo normalizzazione AI):
  Titolo normalizzato: Adobe Acrobat Pro DC
  Vendor: Adobe Inc.
  Categoria: Produttivita > PDF > Editor Professionale
  Tipo licenza: Subscription (Named User)
  Versione corrente: 2025.001.20005
  EOL/EOS: N/A (subscription rolling)
```

### Predictive Asset Management

L'AI consente di passare da una gestione reattiva ("l'asset si e guastato") a una predittiva ("l'asset potrebbe guastarsi nei prossimi 30 giorni"):

**Applicazioni dell'Analisi Predittiva nell'ITAM:**

| Applicazione | Dati Utilizzati | Beneficio |
|-------------|----------------|-----------|
| Previsione guasti hardware | SMART data SSD/HDD, log errori, temperatura, eta | Sostituzione preventiva, riduzione downtime |
| Ottimizzazione cicli di refresh | Utilizzo effettivo, ticket per asset, costi manutenzione | Refresh basato su dati reali vs calendario fisso |
| Previsione esigenze di capacita | Trend utilizzo CPU/RAM/storage, crescita utenti | Procurement anticipato, evitare bottleneck |
| Ottimizzazione licenze | Pattern di utilizzo, stagionalita, turnover | Dimensionamento accurato degli acquisti |
| Previsione costi di manutenzione | Storico guasti, eta, modello, ambiente operativo | Budget planning piu accurato |
| Rilevamento anomalie di sicurezza | Comportamento dell'asset, traffico di rete, log | Identificazione tempestiva di asset compromessi |

### Agentic AI e Automazione dei Workflow

L'AI agentica rappresenta l'evoluzione piu recente (2025-2026), in cui agenti AI autonomi eseguono task ITAM senza intervento umano:

**Casi d'uso dell'AI Agentica nell'ITAM:**

- **Auto-remediation delle non-conformita**: L'agente rileva una non-conformita di licenza, disinstalla automaticamente il software in eccesso dagli endpoint meno utilizzati e riassegna la licenza
- **Procurement assistito**: L'agente analizza i pattern di richiesta, le scorte disponibili e i contratti in essere per generare ordini di acquisto ottimizzati
- **Onboarding/Offboarding automatizzato**: Provisioning e de-provisioning completo degli asset e delle licenze basato su eventi HR
- **Report generation**: Generazione automatica di report di compliance e KPI con analisi e raccomandazioni
- **Vendor negotiation support**: Analisi dei dati di utilizzo e benchmark di mercato per supportare le negoziazioni contrattuali

**Consolidamento delle Piattaforme:**

Una tendenza chiave del 2025-2026 e il passaggio dal multi-tool sprawl (molti strumenti frammentati) a piattaforme unificate con AI integrata. Le organizzazioni stanno consolidando su piattaforme primarie che integrano ITAM, SAM, SaaS management, FinOps e CMDB in un'unica soluzione governata.

---

## Policy e Governance ITAM

### Template Policy ITAM Aziendale

Una policy ITAM formale e il fondamento per un programma di gestione asset efficace. Di seguito un template completo da personalizzare:

```
POLICY DI GESTIONE DEGLI ASSET IT
====================================
Versione: [X.Y]
Data di emissione: [DATA]
Approvata da: [CIO / IT Director]
Prossima revisione: [DATA + 12 mesi]

1. SCOPO
   Definire le regole, le responsabilita e le procedure per la gestione
   di tutti gli asset IT dell'organizzazione durante il loro intero
   ciclo di vita, garantendo conformita normativa, sicurezza dei dati
   e ottimizzazione dei costi.

2. AMBITO DI APPLICAZIONE
   Questa policy si applica a:
   - Tutti gli asset hardware di proprieta o in leasing dell'organizzazione
   - Tutto il software installato su asset aziendali
   - Tutti i servizi cloud (IaaS, PaaS, SaaS) sottoscritti dall'organizzazione
   - Tutti i dispositivi personali utilizzati per accedere a dati aziendali (BYOD)
   - Tutti i dipendenti, collaboratori, consulenti e fornitori

3. RESPONSABILITA
   3.1 IT Asset Manager: Responsabile complessivo del programma ITAM
   3.2 IT Operations: Esecuzione dei processi operativi (deployment, manutenzione)
   3.3 Procurement/Acquisti: Gestione acquisti e contratti
   3.4 Finance: Gestione ammortamenti, budget e reporting finanziario
   3.5 Security: Verifica conformita sicurezza degli asset
   3.6 Utenti finali: Utilizzo conforme e segnalazione tempestiva di problemi

4. REGISTRAZIONE E INVENTARIO
   4.1 Ogni asset IT deve essere registrato nel CMDB prima del deployment
   4.2 L'asset tag deve essere applicato prima dell'assegnazione all'utente
   4.3 L'inventario automatico deve essere aggiornato almeno quotidianamente
   4.4 Audit fisici devono essere condotti trimestralmente (aree critiche)
       e semestralmente (tutti gli asset)

5. ACQUISIZIONE
   5.1 Ogni acquisizione deve essere preventivamente approvata
   5.2 Solo configurazioni standard approvate possono essere acquistate
   5.3 Deroghe alle configurazioni standard richiedono approvazione del CIO
   5.4 Le licenze software devono essere verificate prima dell'installazione

6. UTILIZZO
   6.1 Gli asset aziendali devono essere utilizzati esclusivamente
       per scopi lavorativi autorizzati
   6.2 L'installazione di software non approvato e vietata
   6.3 La modifica delle configurazioni di sicurezza e vietata
   6.4 Lo spostamento di asset tra sedi richiede notifica all'IT

7. DISMISSIONE
   7.1 La dismissione deve seguire il processo di decommissioning approvato
   7.2 I dati devono essere sanificati con metodo certificato
   7.3 Le licenze software devono essere recuperate prima della dismissione
   7.4 Lo smaltimento deve avvenire tramite fornitori ITAD autorizzati
   7.5 Il certificato di distruzione deve essere archiviato per 10 anni

8. CONFORMITA E SANZIONI
   8.1 La violazione di questa policy puo comportare azioni disciplinari
   8.2 La conformita viene verificata tramite audit periodici
   8.3 Le eccezioni devono essere documentate e approvate

9. REVISIONE
   Questa policy viene rivista annualmente o in caso di cambiamenti
   normativi significativi.
```

### RACI Matrix per ITAM

La matrice RACI definisce chiaramente chi e Responsabile (R), Accountable (A), Consultato (C) e Informato (I) per ogni attivita ITAM:

| Attivita | IT Asset Mgr | IT Ops | Procurement | Finance | Security | Utente Finale |
|----------|-------------|--------|-------------|---------|----------|---------------|
| Definizione policy ITAM | A | C | C | C | C | I |
| Registrazione asset nel CMDB | A | R | I | I | I | I |
| Procurement hardware | C | C | R | A | C | I |
| Procurement software/licenze | A | C | R | A | C | I |
| Deployment endpoint | C | R | I | I | C | I |
| Gestione licenze software | R | C | C | I | I | I |
| Audit conformita licenze | R | C | I | I | C | I |
| Vendor audit response | A | R | C | C | I | I |
| Pianificazione refresh | A | C | C | R | C | I |
| Dismissione e sanificazione | A | R | I | I | C | I |
| Smaltimento RAEE | C | R | R | I | I | I |
| Discovery e inventario automatico | A | R | I | I | C | I |
| Gestione garanzie e supporto | A | R | C | I | I | I |
| Cloud cost management | A | R | C | R | C | I |
| Shadow IT detection | A | R | I | I | R | I |
| Reportistica ITAM | R | C | I | C | I | I |

### Metriche di Governance

Oltre ai KPI operativi gia descritti nella sezione Reportistica, le metriche di governance misurano l'efficacia complessiva del programma ITAM:

**Metriche Finanziarie:**

| Metrica | Calcolo | Target |
|---------|---------|--------|
| Risparmio licenze annuo | Valore licenze recuperate + ottimizzazione subscription | > 10% della spesa licenze |
| Costo ITAM per asset | Costo totale programma ITAM / numero asset gestiti | < €50/asset/anno |
| ROI del programma ITAM | (Risparmi + penali evitate - Costo programma) / Costo programma | > 200% |
| Varianza budget cloud | (Spesa cloud effettiva - Budget) / Budget | < 10% |
| Valore asset non utilizzati | Costo degli asset attivi non assegnati o non utilizzati | < 5% del valore totale |

**Metriche di Rischio:**

| Metrica | Calcolo | Target |
|---------|---------|--------|
| Indice di esposizione audit | N. prodotti sotto-licenziati / N. prodotti totali | < 2% |
| Asset fuori garanzia critici | N. asset critici senza garanzia / N. asset critici totali | 0% |
| Asset EOL/EOS in produzione | N. asset con software EOL / N. asset totali | < 3% |
| Tempo medio di risposta audit | Giorni dalla notifica alla consegna dati completi | < 10 giorni |
| Tasso Shadow IT | N. app non approvate rilevate / N. app totali in uso | < 15% |

**Metriche di Processo:**

| Metrica | Calcolo | Target |
|---------|---------|--------|
| Tempo medio onboarding asset | Giorni dalla ricezione al deployment operativo | < 2 giorni |
| Tempo medio offboarding asset | Giorni dalla richiesta alla dismissione completa | < 5 giorni |
| Tasso di aggiornamento CMDB | % di change implementati con aggiornamento CMDB | > 95% |
| Copertura discovery | % della rete coperta dalla scansione automatica | > 98% |
| Frequenza audit fisico | N. audit fisici completati / N. pianificati | 100% |

---

> **Documento correlato:** Per le procedure operative specifiche di manutenzione degli asset, consultare la sezione [09-Procedure Operative](09-procedure-operative.md). Per la gestione degli incidenti relativi agli asset, fare riferimento a [07-Monitoraggio e Incidenti](07-monitoraggio-incidenti.md). Per le strategie di backup dei dati sugli asset, vedere [06-Backup e Disaster Recovery](06-backup-disaster-recovery.md).

---

## Esercizi
1. **Lab — asset audit.** Discovery + reconcile con CMDB; identifica orphan.
2. **Stretch — license compliance check.** Per ogni vendor, valida count vs contract.

## Auto-valutazione
1. CMDB vs Asset DB: differenza.
2. License audit: cadenza?
3. Lifecycle stage: cosa tracciare?

## Glossario locale
| Termine | Definizione |
|---|---|
| **Asset catalog** | Inventario completo IT. |
| **License compliance** | Aderenza contratto licensing. |
| **Lifecycle** | Acquisto → retirement. |
| **CI (Configuration Item)** | Asset gestito in CMDB. |
