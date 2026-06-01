# Troubleshooting Generale IT — Guida Completa

> **Modulo 11** · **Tempo:** 60 min · **Aggiornamento:** 2026-04-27

## Idee guida

1. **OSI layer-by-layer.** Mai saltare livelli.
2. **Reproduce > theorize.** Bug che non riprodu = bug che non risolvi.
3. **Binary search to isolate.** Disabilita meta del sistema; problema in quale meta?
4. **Document RCA per riferimento futuro.**


## Indice

1. [Panoramica](#panoramica)
2. [Metodologia di Troubleshooting](#metodologia-di-troubleshooting)
   - [Framework Generale (6 Steps)](#framework-generale-6-steps)
   - [Tecniche di Diagnosi](#tecniche-di-diagnosi)
   - [Raccolta Informazioni](#raccolta-informazioni)
3. [Troubleshooting Rete](#troubleshooting-rete)
   - [Layer 1-2 (Fisico e Data Link)](#layer-1-2-fisico-e-data-link)
   - [Layer 3 (Network)](#layer-3-network)
   - [Layer 4-7 (Transport e Application)](#layer-4-7-transport-e-application)
   - [Strumenti Rete](#strumenti-rete)
4. [Troubleshooting Performance](#troubleshooting-performance)
   - [CPU Alta](#cpu-alta)
   - [Memoria Insufficiente](#memoria-insufficiente)
   - [Disco Lento](#disco-lento)
   - [Rete Lenta](#rete-lenta)
5. [Troubleshooting Autenticazione](#troubleshooting-autenticazione)
   - [Active Directory](#active-directory)
   - [LDAP e SSO](#ldap-e-sso)
6. [Troubleshooting Storage](#troubleshooting-storage)
   - [Disk Space](#disk-space)
   - [RAID Issues](#raid-issues)
   - [Storage Performance](#storage-performance)
7. [Troubleshooting Email](#troubleshooting-email)
   - [Mail Flow Issues](#mail-flow-issues)
   - [Client Issues](#client-issues)
8. [Troubleshooting Stampa](#troubleshooting-stampa)
9. [Strumenti Diagnostici Essenziali](#strumenti-diagnostici-essenziali)
   - [Windows](#windows)
   - [Linux](#linux)
10. [Best Practices](#best-practices)
11. [Troubleshooting del Troubleshooting](#troubleshooting-del-troubleshooting)
12. [Root Cause Analysis Approfondita](#root-cause-analysis-approfondita)
    - [La Tecnica dei 5 Whys](#la-tecnica-dei-5-whys)
    - [Diagramma di Ishikawa (Fishbone)](#diagramma-di-ishikawa-fishbone)
    - [Fault Tree Analysis (FTA)](#fault-tree-analysis-fta)
    - [Metodo Kepner-Tregoe](#metodo-kepner-tregoe)
    - [Analisi di Pareto (80/20)](#analisi-di-pareto-8020)
    - [Template RCA Operativo](#template-rca-operativo)
13. [Problem Management ITIL](#problem-management-itil)
    - [Ciclo di Vita del Problema](#ciclo-di-vita-del-problema)
    - [Problem Management Reattivo](#problem-management-reattivo)
    - [Problem Management Proattivo](#problem-management-proattivo)
    - [Known Error Database (KEDB)](#known-error-database-kedb)
    - [Workaround vs Soluzione Definitiva](#workaround-vs-soluzione-definitiva)
14. [Matrice di Escalation e Priorita'](#matrice-di-escalation-e-priorita)
    - [Matrice Impatto-Urgenza](#matrice-impatto-urgenza)
    - [Livelli di Escalation](#livelli-di-escalation)
    - [Procedure di Escalation per Priorita'](#procedure-di-escalation-per-priorita)
    - [Escalation Funzionale vs Gerarchica](#escalation-funzionale-vs-gerarchica)
    - [Comunicazione durante gli Incidenti](#comunicazione-durante-gli-incidenti)
15. [Knowledge Base Management](#knowledge-base-management)
    - [Knowledge-Centered Service (KCS)](#knowledge-centered-service-kcs)
    - [Struttura degli Articoli](#struttura-degli-articoli)
    - [Ciclo di Vita della Conoscenza](#ciclo-di-vita-della-conoscenza)
    - [Metriche della Knowledge Base](#metriche-della-knowledge-base)
16. [Post-Mortem e Incident Review](#post-mortem-e-incident-review)
    - [Cultura Blameless](#cultura-blameless)
    - [Template Post-Mortem](#template-post-mortem)
    - [Processo di Conduzione](#processo-di-conduzione)
    - [Action Item e Follow-Up](#action-item-e-follow-up)
17. [Flowchart Diagnostici Operativi](#flowchart-diagnostici-operativi)
    - [Flowchart: Utente Non Naviga su Internet](#flowchart-utente-non-naviga-su-internet)
    - [Flowchart: Servizio Applicativo Non Risponde](#flowchart-servizio-applicativo-non-risponde)
    - [Flowchart: Performance Degradata del Server](#flowchart-performance-degradata-del-server)
    - [Flowchart: Problema di Autenticazione](#flowchart-problema-di-autenticazione)
18. [Troubleshooting Moderno: AIOps e Observability](#troubleshooting-moderno-aiops-e-observability)
    - [OpenTelemetry e Telemetria Unificata](#opentelemetry-e-telemetria-unificata)
    - [eBPF per Diagnostica di Rete](#ebpf-per-diagnostica-di-rete)
    - [AIOps: dall'Allarme alla Remediation Automatica](#aiops-dallallarme-alla-remediation-automatica)
    - [Strumenti di Observability Moderni](#strumenti-di-observability-moderni)
19. [Troubleshooting Avanzato: Scenari Complessi](#troubleshooting-avanzato-scenari-complessi)
    - [Problemi Intermittenti (Heisenbugs)](#problemi-intermittenti-heisenbugs)
    - [Problemi di Performance sotto Carico](#problemi-di-performance-sotto-carico)
    - [Troubleshooting in Ambienti Virtualizzati](#troubleshooting-in-ambienti-virtualizzati)
    - [Troubleshooting DNS Avanzato](#troubleshooting-dns-avanzato)

---

## Panoramica

Il troubleshooting rappresenta una delle competenze fondamentali e trasversali per qualsiasi professionista IT. Non si tratta semplicemente di "risolvere problemi", ma di applicare un approccio sistematico, rigoroso e ripetibile alla diagnosi e alla risoluzione di malfunzionamenti che possono colpire qualsiasi componente dell'infrastruttura tecnologica: reti, server, applicazioni, storage, servizi di autenticazione, posta elettronica e periferiche.

Un troubleshooter efficace non si affida all'intuizione casuale, ma segue metodologie consolidate, raccoglie evidenze prima di agire, formula ipotesi verificabili e documenta ogni intervento per costruire una base di conoscenza che riduca progressivamente i tempi di risoluzione futuri. L'obiettivo finale non e' solo ripristinare il servizio nel minor tempo possibile (minimizzare il MTTR, Mean Time To Resolution), ma comprendere la causa radice (RCA, Root Cause Analysis) per prevenire il ripetersi del problema.

Questa guida copre in modo completo la metodologia generale di troubleshooting, le tecniche di diagnosi applicabili a ogni scenario, e poi scende nel dettaglio di ambiti specifici: rete, performance, autenticazione, storage, email e stampa. Per ogni area vengono forniti comandi concreti, strumenti consigliati e procedure passo-passo utilizzabili immediatamente in ambienti di produzione.

La capacita' di troubleshooting si affina con l'esperienza, ma un framework solido permette anche a tecnici meno esperti di affrontare problemi complessi in modo strutturato, evitando le trappole piu' comuni: agire senza comprendere, modificare piu' variabili contemporaneamente, dimenticare di documentare, o trascurare l'impatto delle proprie azioni su altri sistemi.

---

## Metodologia di Troubleshooting

### Framework Generale (6 Steps)

Il framework a sei fasi rappresenta lo standard universale per il troubleshooting IT. Ogni fase e' essenziale e saltarne una porta quasi inevitabilmente a interventi inefficaci, risoluzioni parziali o, nel caso peggiore, a peggiorare la situazione.

#### Step 1 — Identificare il Problema

Questa e' la fase piu' critica e spesso la piu' sottovalutata. Prima di poter risolvere qualsiasi cosa, bisogna comprendere esattamente cosa non funziona, da quando, per chi, e in quali condizioni.

**Raccogliere informazioni dall'utente o dal sistema di monitoraggio:**
- Qual e' esattamente il sintomo osservato? (Non accettare "non funziona" — servono dettagli specifici)
- Quando e' iniziato il problema? Era funzionante prima? Cosa e' cambiato?
- Chi e' colpito? Un singolo utente, un dipartimento, l'intera organizzazione?
- Il problema e' costante o intermittente? Se intermittente, con quale frequenza?
- E' possibile riprodurre il problema su richiesta?

**Riprodurre il problema:**
La capacita' di riprodurre un problema in modo affidabile e' fondamentale. Se non riesci a vederlo con i tuoi occhi, chiedi all'utente di mostrartelo (di persona, via screen sharing o tramite video). Un problema che non si riesce a riprodurre e' enormemente piu' difficile da diagnosticare. In caso di problemi intermittenti, stabilire un sistema di cattura (logging avanzato, network capture continuo, monitoring granulare) che possa registrare il momento esatto in cui il problema si manifesta.

**Definire lo scope:**
Determinare l'ampiezza del problema e' cruciale per indirizzare correttamente l'indagine. Se tutti gli utenti di un ufficio non raggiungono un server, il problema e' probabilmente di rete. Se un solo utente ha difficolta', e' probabilmente locale. Se il problema riguarda solo un'applicazione specifica su tutti i client, e' probabilmente lato server o applicativo. Lo scope guida la direzione dell'indagine.

**Verificare le recenti modifiche:**
Una percentuale significativa dei problemi IT e' causata da modifiche recenti: aggiornamenti software, patch di sicurezza, modifiche alla configurazione di rete, deployment di nuove policy, installazione di nuovo hardware. Consultare il change log, il sistema di ticketing e i colleghi per individuare qualsiasi modifica avvenuta nel periodo in cui il problema e' iniziato.

#### Step 2 — Stabilire una Teoria delle Cause Probabili

Sulla base delle informazioni raccolte, formulare una o piu' ipotesi sulle possibili cause. Questo richiede conoscenza tecnica ed esperienza, ma anche un approccio sistematico di eliminazione.

**Principi guida:**
- Partire dalle cause piu' semplici e probabili (Rasoio di Occam). Un cavo scollegato e' piu' probabile di un bug del firmware dello switch
- Considerare le cause in ordine di probabilita', non di gravita'
- Non trascurare i fondamentali: alimentazione, connettivita' fisica, DNS, DHCP
- Tenere una lista delle cause considerate ed eliminate, non solo di quella su cui si sta lavorando
- Chiedersi: "Cosa potrebbe causare esattamente QUESTO sintomo in QUESTE condizioni?"

**Eliminazione per esclusione:**
Se il problema e' "l'utente non naviga su internet", le cause possibili includono: cavo di rete scollegato, IP non assegnato, DNS non funzionante, proxy non configurato, firewall che blocca, problema del provider. Si eliminano una alla volta, partendo dalla piu' semplice da verificare.

#### Step 3 — Testare la Teoria

Ogni ipotesi deve essere verificata con un test specifico prima di procedere con azioni correttive. Mai assumere che la causa sia stata identificata senza conferma.

**Regole fondamentali:**
- Un test alla volta. Modificare una sola variabile per volta. Se si cambiano due cose contemporaneamente e il problema si risolve, non si sa quale delle due fosse la causa
- Il test deve essere specifico per la teoria: se la teoria e' "DNS non funziona", il test e' `nslookup` verso il server DNS, non un generico ping
- Se il test conferma la teoria, procedere allo Step 4
- Se il test smentisce la teoria, tornare allo Step 2 con una nuova ipotesi
- Documentare il risultato di ogni test, anche quelli negativi (saranno utili per la documentazione finale e per eventuali escalation)

**Esempio pratico:**
Teoria: "Il server DNS primario non risponde." Test: `nslookup google.com 10.0.1.10`. Risultato: timeout. Controprova: `nslookup google.com 8.8.8.8`. Risultato: risponde. Teoria confermata: il DNS primario non funziona. Prossimo passo: capire perche' il DNS primario non risponde (servizio fermo? server spento? rete irraggiungibile?).

#### Step 4 — Stabilire un Piano d'Azione

Una volta confermata la causa, pianificare l'intervento prima di agire. Agire di impulso puo' trasformare un problema gestibile in un disastro.

**Elementi del piano:**
- **Azione correttiva specifica:** cosa esattamente si fara' (riavvio del servizio DNS, modifica della configurazione, sostituzione del cavo, ecc.)
- **Valutazione dei rischi:** l'intervento potrebbe causare un'interruzione piu' ampia? Quali servizi dipendono dal componente su cui si interviene?
- **Tempistiche:** quanto durera' l'intervento? E' necessario schedularlo in una finestra di manutenzione?
- **Piano di rollback:** se l'intervento peggiora la situazione, come si torna allo stato precedente? Fare sempre un backup/snapshot prima di modifiche significative
- **Comunicazione:** chi deve essere informato? Utenti, management, altri team tecnici? Se il servizio sara' interrotto, inviare una notifica preventiva
- **Approvazione:** modifiche significative in produzione richiedono l'approvazione attraverso il processo di Change Management

#### Step 5 — Implementare la Soluzione

Seguire il piano stabilito in modo disciplinato.

**Durante l'implementazione:**
- Eseguire le azioni nell'ordine pianificato
- Verificare ogni passo prima di procedere al successivo
- Tenere una sessione di terminale con timestamp (script/log della sessione) per avere un registro preciso di ogni comando eseguito
- Dopo l'intervento, verificare immediatamente che il problema originale sia effettivamente risolto
- Verificare che non siano stati introdotti nuovi problemi (regressioni)
- Chiedere all'utente originale di confermare la risoluzione dal suo punto di vista
- Monitorare il sistema per un periodo adeguato dopo la risoluzione per assicurarsi che il problema non si ripresenti

#### Step 6 — Documentare

La documentazione e' l'investimento piu' sottovalutato nel troubleshooting. Una buona documentazione trasforma ogni problema risolto in conoscenza riutilizzabile dall'intero team.

**Cosa documentare:**
- **Sintomo originale:** descrizione precisa di come il problema si manifestava
- **Causa radice (RCA):** la vera causa del problema, non solo il sintomo risolto
- **Procedura di diagnosi:** i passi seguiti, inclusi i vicoli ciechi (utili per il futuro)
- **Soluzione applicata:** esattamente cosa e' stato fatto per risolvere
- **Prevenzione futura:** quali azioni possono impedire il ripetersi del problema (monitoraggio, automazione, hardening, formazione)
- **Tempo impiegato:** per calcolo del MTTR e ottimizzazione dei processi

**Dove documentare:**
Nel sistema di ticketing (chiudendo il ticket con informazioni complete), nella knowledge base interna, e se il problema era significativo, in un post-mortem condiviso con il team.

---

### Tecniche di Diagnosi

Oltre al framework a sei fasi, esistono diverse tecniche specifiche di diagnosi che possono essere applicate nello Step 2 e Step 3 per individuare la causa in modo piu' efficiente.

#### Top-Down Approach

Si parte dal livello applicativo (Layer 7 del modello OSI) e si scende verso il basso. E' l'approccio piu' naturale quando il sintomo e' chiaramente applicativo ("l'applicazione web restituisce errore 500").

Esempio: Applicazione web non funziona → Verificare il servizio web → Verificare la connettivita' di rete verso il server → Verificare la configurazione IP → Verificare il cavo fisico.

**Vantaggi:** Partendo dal sintomo visibile, spesso si arriva rapidamente alla causa se il problema e' ai livelli superiori. **Svantaggi:** Se il problema e' fisico (Layer 1), si perde tempo a indagare tutti i livelli superiori.

#### Bottom-Up Approach

Si parte dal livello fisico (Layer 1) e si sale. E' l'approccio migliore quando non ci sono indicazioni chiare su dove sia il problema, o quando si sospetta un problema infrastrutturale.

Esempio: Verificare il cavo → Verificare il link → Verificare l'IP → Verificare il routing → Verificare la porta TCP → Verificare l'applicazione.

**Vantaggi:** Metodico e completo, non tralascia nulla. **Svantaggi:** Lento se il problema e' ai livelli superiori.

#### Divide and Conquer

Si divide il sistema a meta' e si testa. In base al risultato, si elimina una meta' e si concentra l'indagine sull'altra. E' la tecnica piu' efficiente in termini di numero di test necessari.

Esempio di rete: Il client non raggiunge il server remoto. Il percorso attraversa 5 hop di rete. Si testa la connettivita' verso l'hop centrale (il terzo). Se funziona, il problema e' tra l'hop 3 e il server. Se non funziona, il problema e' tra il client e l'hop 3. Si continua a dividere fino a isolare il punto esatto.

#### Analisi Layer-by-Layer del Modello OSI

Si analizza sistematicamente ogni livello del modello OSI, concentrandosi sugli aspetti specifici di ciascuno. Questa tecnica e' particolarmente potente per i problemi di rete, perche' ogni livello ha strumenti e sintomi specifici.

- **Layer 1 (Fisico):** Cavi, connettori, segnale ottico, alimentazione PoE
- **Layer 2 (Data Link):** MAC address, switch, VLAN, STP, errori di frame
- **Layer 3 (Network):** IP, subnet, routing, ARP, ICMP
- **Layer 4 (Transport):** Porte TCP/UDP, firewall, NAT, sessioni
- **Layer 5-7 (Sessione/Presentazione/Applicazione):** Protocolli applicativi, certificati SSL/TLS, DNS, HTTP

#### Binary Search (Bisect)

Simile al divide and conquer, ma applicato nel tempo o nelle configurazioni. Se un sistema ha smesso di funzionare dopo una serie di modifiche, si applica il metodo della bisezione per trovare quale modifica specifica ha causato il problema. Questo e' analogo a `git bisect` nel mondo dello sviluppo software.

Esempio: 10 modifiche applicate nell'ultimo mese. Si testa lo stato dopo la modifica 5. Se funziona, il problema e' nelle modifiche 6-10. Si testa la 8. E cosi' via.

#### Comparison Method (Working vs Broken)

Si confronta un sistema funzionante con uno malfunzionante per individuare le differenze. E' una tecnica estremamente efficace quando si ha a disposizione un sistema di riferimento.

Esempio: Due PC identici, stesso modello, stesso software. Uno naviga su internet, l'altro no. Si confrontano: configurazione IP, DNS, proxy, routing table, firewall locale, driver di rete. Le differenze trovate sono le candidate causa del problema.

Strumenti utili: `diff` per confrontare file di configurazione, `fc` su Windows, PowerShell `Compare-Object`, export e confronto di policy GPO.

#### Component Swap/Isolation

Si sostituisce o si isola un componente per determinare se e' la causa del problema. E' la tecnica definitiva quando le altre non danno risultati chiari.

Esempio: Si sospetta un problema del cavo di rete. Si sostituisce il cavo con uno sicuramente funzionante. Se il problema si risolve, il cavo era la causa. Applicabile a: cavi, switch port, schede di rete, alimentatori, moduli SFP, dischi, moduli di memoria.

Per l'isolamento: si rimuove un componente dalla catena e si testa. Esempio: si sospetta che un firewall blocchi il traffico. Si bypassa temporaneamente il firewall (in ambiente controllato). Se il traffico passa, il firewall e' la causa.

---

### Raccolta Informazioni

La qualita' della diagnosi dipende direttamente dalla qualita' delle informazioni raccolte. Un troubleshooter esperto dedica piu' tempo alla raccolta dati che all'azione correttiva.

#### Domande Fondamentali

Ogni sessione di troubleshooting dovrebbe iniziare con queste domande:

1. **Quando e' iniziato?** La correlazione temporale con eventi (deployment, aggiornamenti, modifiche di rete) e' spesso la chiave per la risoluzione
2. **Cosa e' cambiato?** La risposta "niente" e' quasi sempre sbagliata. Insistere: aggiornamenti Windows, nuove installazioni, modifiche di configurazione, cambio di password, spostamento fisico
3. **Chi e' colpito?** Un utente, un gruppo, un dipartimento, un ufficio, tutti? Questo definisce lo scope e indirizza l'indagine
4. **E' riproducibile?** Se si': farlo accadere per osservarlo direttamente. Se no: stabilire un sistema di cattura
5. **Qual e' l'impatto?** Servizio completamente fermo o degradato? Questo determina la priorita' e l'urgenza dell'intervento
6. **Ci sono messaggi di errore?** Ottenere lo screenshot o il testo esatto del messaggio di errore. Mai accettare "dava un errore"

#### Tecniche di Analisi dei Log

I log sono la fonte primaria di informazioni per il troubleshooting. Ogni sistema operativo, servizio e applicazione produce log che contengono indizi cruciali.

**Windows Event Viewer:**
```powershell
# Cercare errori negli ultimi 30 minuti nel log System
Get-WinEvent -FilterHashtable @{LogName='System'; Level=2; StartTime=(Get-Date).AddMinutes(-30)}

# Cercare eventi specifici per Event ID
Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4740} | Select-Object -First 10

# Filtrare per sorgente (provider)
Get-WinEvent -FilterHashtable @{LogName='Application'; ProviderName='MSSQLSERVER'}
```

**Linux journalctl e log tradizionali:**
```bash
# Ultimi 30 minuti di log di sistema
journalctl --since "30 minutes ago"

# Log di un servizio specifico
journalctl -u nginx.service --since today

# Livello di severita' (errori e critici)
journalctl -p err..crit --since "1 hour ago"

# Seguire i log in tempo reale
journalctl -f -u sshd.service

# Log tradizionali
tail -f /var/log/syslog
tail -f /var/log/auth.log
```

#### Dati di Monitoraggio

Se l'infrastruttura dispone di un sistema di monitoraggio (Zabbix, Nagios, PRTG, Prometheus/Grafana, Datadog), i dati storici sono fondamentali per correlare il problema con metriche di performance, variazioni di traffico, picchi di utilizzo risorse, o eventi di altri sistemi.

Verificare sempre: grafici CPU/memoria/disco/rete nel periodo in cui il problema e' iniziato, alert precedenti che potrebbero essere correlati, e metriche di disponibilita' dei servizi dipendenti.

#### Catture di Rete

Per problemi di comunicazione, una cattura di pacchetti fornisce evidenze incontrovertibili di cosa sta accadendo a livello di protocollo.

```bash
# Cattura con tcpdump su Linux
tcpdump -i eth0 -w /tmp/capture.pcap host 10.0.1.50 and port 443

# Cattura con pktmon su Windows (Server 2019+)
pktmon start --capture --comp nics -f capture.etl
pktmon stop
pktmon etl2pcap capture.etl --out capture.pcap
```

Analizzare poi con Wireshark, filtrando per il traffico rilevante. Cercare: handshake TCP incompleti (SYN senza SYN-ACK), RST inaspettati, retransmission eccessive, errori applicativi nei payload.

#### Dati di Performance

Raccogliere baseline di performance per confronto con i valori attuali. Se non esiste una baseline storica, raccoglierla da un sistema funzionante equivalente.

```powershell
# Windows: Performance counter collection
Get-Counter '\Processor(_Total)\% Processor Time','\Memory\Available MBytes','\PhysicalDisk(_Total)\Avg. Disk Queue Length' -SampleInterval 5 -MaxSamples 12
```

```bash
# Linux: Snapshot delle risorse
vmstat 5 12
iostat -x 5 12
sar -u -r -d 5 12
```

---

## Troubleshooting Rete

I problemi di rete sono tra i piu' frequenti e impattanti in un ambiente IT. L'approccio layer-by-layer del modello OSI e' la metodologia piu' efficace per diagnosticarli sistematicamente.

### Layer 1-2 (Fisico e Data Link)

I problemi ai livelli fisico e data link sono spesso banali nella causa ma devastanti nell'effetto. Un cavo difettoso puo' causare sintomi che sembrano problemi applicativi complessi.

#### Test dei Cavi

- **Continuita':** Utilizzare un cable tester per verificare che tutti e 8 i conduttori siano collegati correttamente (pin-to-pin per cavi straight-through, schema incrociato per crossover)
- **Certificazione:** Per problemi intermittenti, un semplice test di continuita' non basta. Servono test di attenuazione, NEXT (Near-End Crosstalk), e return loss che richiedono un certificatore professionale
- **Ispezione visiva:** Connettori danneggiati, cavi schiacciati, pieghe eccessive, vicinanza a fonti di interferenza elettromagnetica (motori, neon, cavi di alimentazione paralleli)

#### Stato del Link

```bash
# Linux: verificare stato link, velocita', duplex
ethtool eth0
# Output rilevante: Speed, Duplex, Link detected

ip link show eth0
# Output: state UP/DOWN
```

```powershell
# Windows: stato adattatore di rete
Get-NetAdapter | Format-Table Name, Status, LinkSpeed, MediaConnectionState
Get-NetAdapterAdvancedProperty -Name "Ethernet" | Where-Object {$_.DisplayName -match "Speed|Duplex"}
```

**Problemi comuni:**
- **Link down:** Cavo scollegato, porta switch disabilitata, guasto hardware NIC o porta switch
- **Speed/Duplex mismatch:** Negoziazione automatica fallita. Un lato a 100 Mbps Full, l'altro a 1 Gbps Half. Causa performance terribili e pacchetti persi. Soluzione: forzare la stessa impostazione su entrambi i lati o assicurarsi che entrambi siano in auto-negotiation
- **Link flapping:** Il link sale e scende ripetutamente. Causa comune: cavo marginale, porta switch difettosa, SFP che perde segnale

#### Errori della Porta Switch

```
# Cisco IOS
show interface GigabitEthernet0/1
show interface GigabitEthernet0/1 counters errors
```

**Contatori da monitorare:**
- **CRC errors:** Indicano cavo difettoso, interferenza, o duplex mismatch
- **Collisions (late collisions):** Indicano duplex mismatch (un lato half-duplex, l'altro full-duplex)
- **Input/Output drops:** La coda della porta e' piena, il traffico eccede la capacita'
- **Runts/Giants:** Frame piu' piccoli o piu' grandi del consentito, indicano problemi hardware

#### Problemi PoE (Power over Ethernet)

Se i dispositivi alimentati via PoE (telefoni IP, access point, telecamere) non si accendono o si riavviano casualmente:
- Verificare il power budget dello switch: la potenza totale richiesta da tutti i dispositivi PoE potrebbe superare la capacita' dello switch
- Verificare la classe PoE: dispositivi che richiedono PoE+ (802.3at, 30W) su switch che supportano solo PoE (802.3af, 15.4W)
- Cavi troppo lunghi (oltre 100 metri) possono causare caduta di tensione insufficiente per l'alimentazione

---

### Layer 3 (Network)

Il livello network riguarda indirizzamento IP, routing e raggiungibilita'. I problemi qui sono tra i piu' comuni e spesso i piu' rapidi da diagnosticare con gli strumenti giusti.

#### Verifica Configurazione IP

```powershell
# Windows
ipconfig /all
# Verificare: IP, subnet mask, gateway, DNS, DHCP enabled/disabled, DHCP server, lease

# Se DHCP non assegna IP (indirizzo APIPA 169.254.x.x)
ipconfig /release
ipconfig /renew
```

```bash
# Linux
ip addr show
ip route show
cat /etc/resolv.conf

# Rinnovo DHCP
dhclient -r eth0
dhclient eth0
```

**Problemi comuni:**
- **IP APIPA (169.254.x.x):** Il client non ha ricevuto un indirizzo dal DHCP server. Cause: servizio DHCP fermo, scope esaurito, problema di rete tra client e server DHCP, relay DHCP non configurato
- **IP duplicato:** Due dispositivi con lo stesso indirizzo IP. Causa conflitti intermittenti. Individuare con `arp -a` e cercare il MAC address duplicato
- **Subnet mask errata:** Il client pensa di essere in una subnet diversa, non riesce a comunicare con dispositivi nella stessa rete

#### Problemi di Routing

```powershell
# Windows
route print
tracert 10.0.2.50
pathping 10.0.2.50   # Combina tracert con statistiche di packet loss per ogni hop
```

```bash
# Linux
ip route show
traceroute 10.0.2.50
mtr 10.0.2.50        # Versione avanzata combinata di ping+traceroute
```

**Problemi comuni:**
- **Gateway mancante o errato:** Il client non ha un default gateway o punta a un gateway inesistente
- **Routing asimmetrico:** Il traffico di andata segue un percorso diverso dal ritorno. Puo' causare problemi con firewall stateful che vedono solo meta' della connessione
- **Route mancante:** Il router non sa come raggiungere la subnet di destinazione. Verificare le routing table dei router intermedi
- **Routing loop:** I pacchetti girano in cerchio tra due o piu' router. Visibile nel traceroute come hop ripetuti. TTL decrementato a zero genera ICMP Time Exceeded

#### Problemi ARP

```bash
# Visualizzare cache ARP
arp -a                    # Windows e Linux
ip neigh show             # Linux

# Svuotare cache ARP (per forzare nuova risoluzione)
arp -d *                  # Windows (richiede admin)
ip neigh flush all        # Linux
```

**Problemi comuni:**
- **ARP entry statica errata:** Un'entry manuale nella cache ARP punta al MAC address sbagliato
- **ARP spoofing/poisoning:** Un attaccante invia ARP reply falsificati. Rilevabile confrontando il MAC address del gateway nella cache ARP con quello reale
- **Gratuitous ARP non ricevuto:** Dopo una migrazione di IP (failover), i client continuano a inviare traffico al vecchio MAC address

#### Test ICMP e Problemi MTU

```bash
# Ping base
ping 10.0.1.1

# Ping con dimensione specifica per test MTU (non frammentare)
ping -M do -s 1472 10.0.1.1     # Linux: -M do = don't fragment
ping -f -l 1472 10.0.1.1         # Windows: -f = don't fragment

# Se il ping con 1472 byte fallisce, ridurre fino a trovare la MTU massima
# MTU = dimensione payload + 28 byte (20 IP header + 8 ICMP header)
```

**Problemi MTU:** Quando la MTU lungo il percorso e' inferiore a 1500 (tipico con tunnel VPN, MPLS, PPPoE), i pacchetti grandi vengono scartati se il flag "Don't Fragment" e' impostato. Il sintomo classico: ping con pacchetti piccoli funziona, ma il trasferimento di file o pagine web grandi si blocca. Soluzione: ridurre la MTU sull'interfaccia o abilitare Path MTU Discovery.

#### VLAN e Subnet Misconfiguration

- Client in una VLAN sbagliata: riceve IP dalla subnet errata, non raggiunge le risorse nella sua subnet corretta
- Trunk port con VLAN non consentita: il traffico della VLAN viene scartato dallo switch
- Native VLAN mismatch tra due switch collegati in trunk: causa comportamento imprevedibile per il traffico untagged

---

### Layer 4-7 (Transport e Application)

Quando la connettivita' IP e' confermata (ping funziona), ma i servizi non sono raggiungibili, il problema e' ai livelli superiori: porte bloccate, firewall, problemi DNS, certificati, o errori applicativi.

#### Test di Connettivita' su Porta

```powershell
# Windows PowerShell
Test-NetConnection -ComputerName server01 -Port 443
Test-NetConnection -ComputerName server01 -Port 3389 -InformationLevel Detailed
```

```bash
# Linux
nc -zv server01 443          # netcat: test connessione TCP
timeout 5 bash -c '</dev/tcp/server01/443 && echo "Open" || echo "Closed"'
curl -v telnet://server01:25  # Per test porte di servizi specifici
```

#### Verifica Regole Firewall

```powershell
# Windows Firewall
Get-NetFirewallRule | Where-Object {$_.Enabled -eq 'True' -and $_.Direction -eq 'Inbound'} | Select-Object DisplayName, Action, Profile
netsh advfirewall firewall show rule name=all dir=in | Select-String "Rule Name|Enabled|Action|LocalPort"
```

```bash
# Linux iptables/nftables
iptables -L -n -v --line-numbers
nft list ruleset

# Verificare se una porta specifica e' bloccata
iptables -L INPUT -n -v | grep 443
```

**Approccio sistematico:**
Quando il traffico non passa, verificare i firewall in ordine lungo il percorso: firewall locale del client, firewall di rete (perimetrale), firewall locale del server. Per ogni firewall, cercare regole che consentano il traffico sulla porta specifica, nella direzione corretta, per l'IP sorgente/destinazione coinvolto.

#### Test di Risoluzione DNS

```powershell
# Windows
nslookup webapp.contoso.com
nslookup webapp.contoso.com 10.0.1.10     # Interrogando un DNS specifico
Resolve-DnsName webapp.contoso.com -Type A
Resolve-DnsName contoso.com -Type MX       # Record MX per la posta
Clear-DnsClientCache                        # Svuotare cache DNS locale
```

```bash
# Linux
dig webapp.contoso.com
dig webapp.contoso.com @10.0.1.10          # Interrogando un DNS specifico
dig +trace webapp.contoso.com              # Tracciare l'intera catena di risoluzione
host webapp.contoso.com
systemd-resolve --flush-caches             # Svuotare cache (systemd-resolved)
```

**Problemi DNS comuni:**
- Server DNS non raggiungibile (porta 53 UDP/TCP bloccata o servizio fermo)
- Record mancante o errato nel DNS
- Cache DNS locale con entry obsoleta (risolvere con flush)
- DNS suffix search list non configurato (il client cerca `webapp` ma non prova `webapp.contoso.com`)
- DNS forwarder non funzionante (risoluzione interna funziona, esterna no)

#### Test Disponibilita' Servizi

```bash
# HTTP/HTTPS test
curl -v https://webapp.contoso.com/health
curl -o /dev/null -s -w "HTTP Status: %{http_code}\nTime: %{time_total}s\n" https://webapp.contoso.com

# Con dettagli di timing
curl -w "DNS: %{time_namelookup}s\nConnect: %{time_connect}s\nTLS: %{time_appconnect}s\nTotal: %{time_total}s\n" -o /dev/null -s https://webapp.contoso.com
```

```powershell
# PowerShell
Invoke-WebRequest -Uri https://webapp.contoso.com/health -UseBasicParsing
(Invoke-WebRequest -Uri https://webapp.contoso.com -UseBasicParsing).StatusCode
```

#### Problemi SSL/TLS

```bash
# Verificare il certificato e la catena di trust
openssl s_client -connect webapp.contoso.com:443 -servername webapp.contoso.com

# Verificare scadenza certificato
openssl s_client -connect webapp.contoso.com:443 2>/dev/null | openssl x509 -noout -dates

# Verificare i protocolli TLS supportati
openssl s_client -connect webapp.contoso.com:443 -tls1_2
openssl s_client -connect webapp.contoso.com:443 -tls1_3
```

**Problemi TLS comuni:**
- Certificato scaduto: errore immediato nel browser/client
- Certificato per hostname errato (CN/SAN non corrispondente)
- Catena di certificazione incompleta (manca il certificato intermedio)
- Protocollo TLS non supportato (server richiede TLS 1.2+ ma il client supporta solo TLS 1.0)
- Cipher suite mismatch: client e server non hanno cipher suite in comune

---

### Strumenti Rete

#### Panoramica degli Strumenti Principali

| Strumento | Piattaforma | Utilizzo Principale |
|-----------|-------------|---------------------|
| `ping` | Tutte | Test raggiungibilita' base (ICMP echo) |
| `traceroute`/`tracert` | Linux/Windows | Tracciamento del percorso hop-by-hop |
| `pathping` | Windows | Traceroute + statistiche packet loss per hop |
| `mtr` | Linux | Traceroute continuo con statistiche in tempo reale |
| `nslookup` | Tutte | Query DNS interattive |
| `dig` | Linux (installabile su Windows) | Query DNS avanzate con dettagli completi |
| `Resolve-DnsName` | Windows PowerShell | Query DNS native PowerShell |
| `netstat` | Tutte (legacy) | Visualizzare connessioni e porte in ascolto |
| `ss` | Linux | Sostituto moderno di netstat, piu' veloce |
| `Get-NetTCPConnection` | Windows PowerShell | Equivalente moderno di netstat |
| `tcpdump` | Linux | Cattura pacchetti da riga di comando |
| `Wireshark` | Tutte (GUI) | Analisi pacchetti con interfaccia grafica |
| `pktmon` | Windows Server 2019+ | Cattura pacchetti nativa Windows |
| `nmap` | Tutte | Port scanning e network discovery |
| `iperf3` | Tutte | Test di bandwidth tra due endpoint |
| `curl` | Tutte | Test HTTP/HTTPS e download |

#### Utilizzo Avanzato di Alcuni Strumenti

```bash
# mtr: traceroute continuo con statistiche
mtr -rwc 100 10.0.2.50     # 100 cicli, formato report

# nmap: scansione porte di un host
nmap -sT -p 80,443,3389,22 10.0.1.50     # TCP connect scan su porte specifiche
nmap -sU -p 53,161 10.0.1.50              # UDP scan (DNS, SNMP)

# iperf3: test bandwidth (richiede server e client)
# Sul server:
iperf3 -s
# Sul client:
iperf3 -c 10.0.1.50 -t 30 -P 4     # 30 secondi, 4 stream paralleli

# tcpdump: cattura mirata
tcpdump -i eth0 'tcp port 443 and host 10.0.1.50' -c 100 -w /tmp/tls_debug.pcap
```

---

## Troubleshooting Performance

I problemi di performance sono tra i piu' insidiosi perche' spesso non causano un'interruzione completa del servizio, ma una degradazione che puo' essere difficile da quantificare e localizzare.

### CPU Alta

#### Identificazione

```powershell
# Windows: identificare processi con CPU alta
Get-Process | Sort-Object CPU -Descending | Select-Object -First 10 Name, Id, CPU, WorkingSet64
Get-Counter '\Processor(_Total)\% Processor Time' -SampleInterval 2 -MaxSamples 5

# Dettaglio per processo
Get-Counter '\Process(*)\% Processor Time' -SampleInterval 2 | ForEach-Object {
    $_.CounterSamples | Sort-Object CookedValue -Descending | Select-Object -First 5 InstanceName, CookedValue
}
```

```bash
# Linux: identificare processi con CPU alta
top -bn1 | head -20
htop                    # Versione interattiva avanzata
ps aux --sort=-%cpu | head -10
```

#### Cause Comuni e Risoluzione

**Processo in runaway (loop infinito o bug):**
- Identificare il processo con il PID specifico
- Verificare se e' un processo noto o sospetto
- Se noto: riavviare il servizio. Se e' un bug, contattare il vendor con i dettagli
- Se sospetto: potrebbe essere malware. Analizzare il percorso dell'eseguibile, verificare con antivirus

**Malware/Cryptominer:**
- Processo sconosciuto con CPU costantemente alta
- Verificare il percorso dell'eseguibile: `ls -la /proc/<PID>/exe` (Linux) o Process Explorer (Windows)
- Scansione antivirus/antimalware completa
- Verificare connessioni di rete del processo: `netstat -anp | grep <PID>` (Linux)

**Risorse insufficienti:**
- Il carico e' legittimo ma il server non ha abbastanza core CPU
- Verificare il trend storico: il carico e' cresciuto gradualmente (crescita utenti/dati) o improvvisamente?
- Soluzione: scaling verticale (piu' CPU) o orizzontale (load balancing)

**Driver o firmware problematico:**
- Su Windows: il processo `System` o `System Interrupts` mostra CPU alta
- Indica un driver kernel-mode con problemi
- Utilizzare `xperf` (Windows Performance Toolkit) per identificare il driver specifico

**Strumenti avanzati Linux:**
```bash
# perf: profiling della CPU
perf top                          # Profiling in tempo reale
perf record -p <PID> sleep 30    # Registrare 30 secondi di attivita'
perf report                       # Analizzare la registrazione

# strace: tracciare le system call di un processo
strace -p <PID> -c               # Conteggio system call
strace -p <PID> -e trace=read,write -T   # Tracciare I/O con timing
```

---

### Memoria Insufficiente

#### Identificazione

```powershell
# Windows
Get-Counter '\Memory\Available MBytes','\Memory\Pages/sec','\Paging File(_Total)\% Usage'
Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First 10 Name, Id, @{N='RAM_MB';E={[math]::Round($_.WorkingSet64/1MB,0)}}
```

```bash
# Linux
free -h                          # Panoramica memoria
vmstat 5 5                       # Trend con swap (colonne si/so)
ps aux --sort=-%mem | head -10   # Top processi per memoria
```

#### Memory Leak Detection

Un memory leak si manifesta come crescita costante e progressiva dell'utilizzo di memoria di un processo nel tempo, senza mai rilasciarla.

**Indicatori:**
- Working set di un processo che cresce continuamente (ore/giorni) senza mai stabilizzarsi
- Performance che degrada progressivamente fino al riavvio del servizio
- Il riavvio del servizio "risolve" temporaneamente (la memoria viene rilasciata) ma il problema si ripresenta

**Diagnosi:**
```powershell
# Windows: monitorare il working set di un processo nel tempo
$process = "w3wp"   # Esempio: IIS worker process
while($true) {
    $p = Get-Process -Name $process -ErrorAction SilentlyContinue
    if($p) { "$((Get-Date).ToString('HH:mm:ss')) - $($p.Name) - WorkingSet: $([math]::Round($p.WorkingSet64/1MB,0)) MB" }
    Start-Sleep -Seconds 60
}
```

```bash
# Linux: monitorare RSS di un processo
while true; do
    echo "$(date '+%H:%M:%S') - $(ps -p <PID> -o rss=,vsz=,comm=)"
    sleep 60
done
```

**Risoluzione:**
- A breve termine: riavviare periodicamente il servizio (workaround, non soluzione)
- A lungo termine: segnalare al vendor con evidenze (grafici di crescita memoria nel tempo), applicare patch se disponibile

#### Cause Comuni

- **Application leak:** Il colpevole piu' frequente. Un'applicazione alloca memoria senza rilasciarla
- **Troppi servizi sullo stesso server:** Consolidamento eccessivo. Ogni servizio richiede la sua quota di RAM
- **RAM fisicamente insufficiente:** Il carico e' cresciuto oltre la capacita'. Verificare trend storico
- **Cache non configurata:** Alcune applicazioni (database, web server) allocano cache che cresce senza limiti se non configurata correttamente

---

### Disco Lento

#### Identificazione

```powershell
# Windows
Get-Counter '\PhysicalDisk(_Total)\Avg. Disk Queue Length','\PhysicalDisk(_Total)\Avg. Disk sec/Read','\PhysicalDisk(_Total)\Avg. Disk sec/Write','\PhysicalDisk(_Total)\Disk Transfers/sec'
# Queue Length > 2 per spindle = collo di bottiglia
# Latenza > 20ms per SSD, > 50ms per HDD = problemi
```

```bash
# Linux
iostat -x 5 3          # Statistiche I/O estese ogni 5 secondi
iotop -o               # Mostrare solo processi con I/O attivo
```

#### Cause Comuni e Risoluzione

**Frammentazione (solo HDD):**
- Su Windows: Analizzare con `Optimize-Volume -DriveLetter C -Analyze`
- Su Windows: Deframmentare con `Optimize-Volume -DriveLetter C -Defrag`
- Non applicabile a SSD (usare invece TRIM: `Optimize-Volume -DriveLetter C -ReTrim`)

**Disco in fase di guasto:**
- Errori SMART indicano problemi imminenti
- Windows: `wmic diskdrive get status`, oppure strumenti come CrystalDiskInfo
- Linux: `smartctl -a /dev/sda` (pacchetto smartmontools)
- Se ci sono settori riallocati in crescita o errori di lettura: sostituire il disco immediatamente con backup preventivo

**RAID rebuild in corso:**
- Durante il rebuild di un array RAID, le performance I/O crollano significativamente
- Non interrompere il rebuild. Pianificare le attivita' I/O intensive per dopo il completamento
- Monitorare il progresso: controller RAID specifico del vendor

**Backup o antivirus in esecuzione:**
- Processi di backup o scansioni antivirus full-disk generano I/O intenso
- Soluzione: schedulare in ore non lavorative, limitare la banda I/O dei processi di backup, escludere directory non necessarie dalla scansione antivirus

---

### Rete Lenta

#### Identificazione

```bash
# Test bandwidth
iperf3 -c server_target -t 10

# Test latenza e packet loss
ping -c 100 server_target     # Linux
mtr -rwc 100 server_target    # Report dettagliato per hop
```

```powershell
# Windows
Test-NetConnection -ComputerName server_target -InformationLevel Detailed
pathping server_target
```

#### Cause Comuni e Risoluzione

**Saturazione di banda:**
- Traffico legittimo che satura il link (upload pesanti, backup su WAN, streaming)
- Identificare con monitoraggio SNMP della porta switch/router (utilizzo percentuale)
- Soluzione: QoS per prioritizzare il traffico critico, upgrade della banda, schedulazione dei trasferimenti bulk

**Duplex mismatch:**
- Un lato in full-duplex, l'altro in half-duplex
- Sintomo: alte collision count, performance molto inferiore al teorico
- Soluzione: auto-negotiation su entrambi i lati, oppure configurazione manuale identica

**Problemi DNS:**
- DNS lento puo' sembrare "internet lento" perche' ogni nuova connessione attende la risoluzione
- Test: `dig google.com` e verificare il tempo di risposta (Query time). Dovrebbe essere < 50ms per server DNS locali
- Soluzione: verificare il server DNS, la sua connettivita', il forwarding

**Problemi di routing (percorso subottimale):**
- Il traffico segue un percorso piu' lungo del necessario
- Verificare con traceroute: il numero di hop e' ragionevole?
- Soluzione: correggere le routing table per usare percorsi ottimali

**Problemi MTU:**
- Pacchetti grandi frammentati o scartati lungo il percorso
- Sintomo: ping piccoli funzionano, trasferimenti grandi si bloccano o sono lentissimi
- Test e soluzione: vedere la sezione MTU nel Layer 3

---

## Troubleshooting Autenticazione

### Active Directory

#### Account Lockout Investigation

Un account bloccato ripetutamente e' uno dei problemi piu' comuni e frustranti. La sfida e' trovare la sorgente dei tentativi di accesso falliti.

```powershell
# Trovare l'evento di lockout (Event ID 4740) sul PDC Emulator
$PDC = (Get-ADDomain).PDCEmulator
Get-WinEvent -ComputerName $PDC -FilterHashtable @{LogName='Security'; Id=4740} |
    Where-Object { $_.Properties[0].Value -eq 'username_bloccato' } |
    Select-Object TimeCreated, @{N='Account';E={$_.Properties[0].Value}}, @{N='CallerComputer';E={$_.Properties[1].Value}}

# Alternativa: Microsoft Account Lockout Status (lockoutstatus.exe)
# Scaricabile da Microsoft, mostra lo stato di lockout su tutti i DC
```

**Cause comuni di lockout ripetuto:**
- Password cambiata ma non aggiornata su: dispositivi mobili (profilo email/wifi), unita' di rete mappate con credenziali salvate, servizi Windows in esecuzione con le vecchie credenziali, task schedulati, sessioni RDP disconnesse
- Procedura: identificare il `CallerComputer` dall'evento 4740, poi cercare su quel computer Event ID 4625 (logon failure) per trovare il processo/servizio responsabile

#### Problemi di Replica

```powershell
# Stato della replica AD
repadmin /replsummary
repadmin /showrepl
repadmin /queue

# Diagnostica completa del Domain Controller
dcdiag /v /c /e     # Verbose, Comprehensive, tutti i DC

# Forzare la replica
repadmin /syncall /AdeP
```

**Sintomi di replica non funzionante:**
- Utenti creati su un DC non visibili su un altro
- Password cambiata ma il vecchio password funziona ancora (su un DC diverso da quello dove e' stata cambiata)
- Group Policy applicate in modo incoerente

#### Problemi Kerberos

```powershell
# Visualizzare ticket Kerberos correnti
klist

# Svuotare ticket Kerberos (forzare nuova autenticazione)
klist purge

# Verificare la sincronizzazione temporale (Kerberos tollera max 5 minuti di differenza)
w32tm /query /status
w32tm /stripchart /computer:dc01.contoso.com

# Verificare SPN (Service Principal Name)
setspn -L <service_account>
setspn -Q HTTP/webapp.contoso.com     # Cercare un SPN specifico
```

**Problemi Kerberos comuni:**
- **Time skew:** Differenza di orario > 5 minuti tra client e DC. Risoluzione: sincronizzare NTP
- **SPN duplicato o mancante:** Il servizio non riesce ad autenticarsi con Kerberos, fallback a NTLM. Identificare con `setspn -X` (duplicati) e registrare correttamente
- **Ticket scaduto o corrotto:** `klist purge` e riottenere i ticket

#### Group Policy Non Applicata

```powershell
# Verificare quali GPO sono applicate all'utente e al computer
gpresult /R              # Report sintetico
gpresult /H gpresult.html   # Report dettagliato HTML
gpresult /scope:computer /v  # Dettaglio solo computer

# Forzare aggiornamento Group Policy
gpupdate /force

# Modalita' di pianificazione (RSoP - Resultant Set of Policy)
# Utilizzare la console "Resultant Set of Policy" (rsop.msc) per simulazione
```

**Problemi comuni:**
- GPO linkato alla OU sbagliata (l'oggetto computer/utente non e' nella OU corretta)
- Filtro di sicurezza: la GPO e' linkata correttamente ma il filtro di sicurezza non include l'utente/computer
- WMI filter che esclude il target
- Ereditarieta' bloccata o precedenza errata
- Link lento (Slow Link Detection): su connessioni lente alcune estensioni GPO non vengono elaborate

#### Trust Relationship Failures

```powershell
# Verificare la trust relationship del computer con il dominio
Test-ComputerSecureChannel -Verbose

# Riparare la trust relationship (richiede credenziali di dominio)
Test-ComputerSecureChannel -Repair -Credential (Get-Credential)

# Alternativa: rimuovere e riaggiunere il computer al dominio
# (piu' radicale, usare solo se il repair non funziona)
```

Sintomo tipico: "The trust relationship between this workstation and the primary domain failed." L'account computer in AD ha una password condivisa con il computer locale che viene rinnovata periodicamente. Se si desincronizzano (per esempio dopo il ripristino di un backup vecchio), la trust si rompe.

---

### LDAP e SSO

#### LDAP Bind Failures

```bash
# Test LDAP bind (Linux)
ldapsearch -x -H ldap://dc01.contoso.com -D "CN=svc_ldap,OU=Service,DC=contoso,DC=com" -W -b "DC=contoso,DC=com" "(sAMAccountName=testuser)"

# Test LDAPS (LDAP over SSL, porta 636)
ldapsearch -x -H ldaps://dc01.contoso.com:636 -D "CN=svc_ldap,OU=Service,DC=contoso,DC=com" -W -b "DC=contoso,DC=com" "(sAMAccountName=testuser)"
```

**Cause comuni:**
- Credenziali di bind errate (password dell'account di servizio scaduta o cambiata)
- Account di servizio bloccato o disabilitato
- Firewall che blocca porta 389 (LDAP) o 636 (LDAPS)
- Base DN errato nella configurazione dell'applicazione

#### Problemi Certificato LDAPS

```bash
# Verificare il certificato LDAPS
openssl s_client -connect dc01.contoso.com:636

# Verificare scadenza
openssl s_client -connect dc01.contoso.com:636 2>/dev/null | openssl x509 -noout -dates -subject
```

Il certificato LDAPS deve essere valido, non scaduto, emesso per l'hostname corretto del DC, e l'intera catena di certificazione deve essere attendibile dal client che effettua la connessione.

#### SSO Token Issues

- Token scaduto: verificare la durata configurata dei token e i tempi di refresh
- Token troppo grande: in ambienti con molti gruppi AD, il token Kerberos puo' superare la dimensione massima (causa: utente membro di centinaia di gruppi). Soluzione: ridurre le group membership o aumentare MaxTokenSize via registry
- Clock skew: come per Kerberos, la sincronizzazione temporale e' critica per la validazione dei token

#### SAML/OIDC Troubleshooting

- Verificare il metadata dell'IdP e del SP: entity ID, endpoint URL, certificati di firma
- Verificare il SAML assertion con strumenti di decode (base64 decode del SAMLResponse nel browser)
- Controllare il claim mapping: l'attributo atteso dall'applicazione corrisponde a quello inviato dall'IdP?
- Verificare i certificati di firma: scaduti o non corrispondenti tra IdP e SP

#### Problemi MFA

- Token hardware desincronizzato: risincronizzare inserendo due codici consecutivi
- App authenticator: verificare la sincronizzazione temporale del telefono (NTP)
- SMS non ricevuti: problemi del provider telefonico, numero cambiato
- Fallback: verificare che i metodi di recovery (backup codes, telefono alternativo) siano configurati

---

## Troubleshooting Storage

### Disk Space

L'esaurimento dello spazio disco e' un problema critico che puo' causare il blocco di servizi, database corrotti, e impossibilita' di effettuare login.

#### Identificare i Consumatori di Spazio

```powershell
# Windows: spazio disco per volume
Get-PSDrive -PSProvider FileSystem | Select-Object Name, @{N='Used_GB';E={[math]::Round($_.Used/1GB,2)}}, @{N='Free_GB';E={[math]::Round($_.Free/1GB,2)}}

# Strumenti grafici: WinDirStat, TreeSize Free
# Entrambi forniscono una visualizzazione grafica dello spazio utilizzato per directory
```

```bash
# Linux
df -h                         # Spazio per filesystem
du -sh /var/* | sort -rh | head -20    # Top 20 directory sotto /var per dimensione
ncdu /                        # Navigazione interattiva dello spazio disco
```

#### Cause Comuni e Risoluzione

**Crescita dei log:**
- File di log che crescono senza rotazione (IIS, Apache, applicativi custom, database)
- Soluzione immediata: archiviare e comprimere i log vecchi. Soluzione permanente: configurare la log rotation
- Windows IIS: configurare il log recycling per dimensione o per giorno
- Linux: configurare `logrotate` per tutti i servizi

**Crescita del database:**
- Database che crescono oltre le previsioni, transaction log non troncati
- SQL Server: verificare il recovery model (Full senza backup del log = crescita infinita del transaction log). Effettuare backup del log o passare a Simple recovery model se appropriato
- PostgreSQL/MySQL: verificare autovacuum, tabelle non purgabili, BLOB storage

**Shadow Copy (VSS) su Windows:**
```powershell
# Verificare spazio utilizzato dalle shadow copy
vssadmin list shadowstorage
# Ridurre lo spazio massimo allocato
vssadmin resize shadowstorage /For=C: /On=C: /MaxSize=10GB
```

**Pulizia file temporanei:**
```powershell
# Windows: Disk Cleanup da riga di comando
cleanmgr /d C /sageset:1    # Configurare
cleanmgr /d C /sagerun:1    # Eseguire

# Pulire cartella TEMP utente e sistema
Remove-Item "$env:TEMP\*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "C:\Windows\Temp\*" -Recurse -Force -ErrorAction SilentlyContinue
```

```bash
# Linux
apt-get clean           # Debian/Ubuntu: pulire cache pacchetti
yum clean all           # RHEL/CentOS: pulire cache pacchetti
find /tmp -type f -atime +7 -delete    # File temporanei non acceduti da 7+ giorni
journalctl --vacuum-size=500M          # Limitare dimensione journal
```

---

### RAID Issues

#### RAID Degraded State

Un array RAID in stato degradato significa che uno o piu' dischi sono falliti ma l'array e' ancora operativo (grazie alla ridondanza). Questa e' una situazione urgente perche' un secondo guasto potrebbe causare perdita di dati.

**Identificazione:**
- Alert dal controller RAID (via email, SNMP, agente del vendor)
- LED di stato sui dischi (ambra/rosso = guasto)
- Software del controller RAID:
  - Dell OMSA: `omreport storage pdisk controller=0`
  - HP SSA: `ssacli ctrl slot=0 pd all show status`
  - LSI/Avago: `storcli /c0/eall/sall show`

**Procedura di sostituzione disco:**
1. Identificare il disco guasto (numero di slot, serial number)
2. Procurare un disco sostitutivo compatibile (stesso tipo, stessa dimensione o superiore, stessa velocita')
3. Se il controller supporta hot-swap: sostituire il disco a caldo. Il rebuild inizia automaticamente
4. Se non supporta hot-swap: schedulare una finestra di manutenzione, spegnere il server, sostituire, riaccendere
5. Monitorare il rebuild fino al completamento (ore per dischi grandi)

**Monitoraggio del rebuild:**
- Il rebuild puo' richiedere da ore a giorni a seconda della dimensione dei dischi
- Durante il rebuild le performance I/O sono significativamente ridotte
- Non riavviare il server durante il rebuild salvo assoluta necessita'
- Monitorare il progresso con gli strumenti del vendor

---

### Storage Performance

#### Collo di Bottiglia IOPS

Quando le applicazioni richiedono piu' operazioni I/O al secondo di quanto lo storage possa fornire, si verificano code e latenza.

**Identificazione:**
- Disk queue length elevata (> 2 per spindle HDD, > 32 per SSD consumer, variabile per SSD enterprise)
- Latenza I/O in crescita (visibile in `iostat -x` colonna await su Linux, Performance Monitor su Windows)

**Risoluzione:**
- Upgrade a SSD/NVMe se ancora su HDD
- Aggiungere dischi al pool/array per distribuire il carico
- Implementare caching (write-back cache sul controller RAID, read cache SSD)
- Ottimizzare l'applicazione per ridurre le I/O (query database piu' efficienti, indici, caching applicativo)

#### Problemi di Connettivita' SAN

Per storage basato su SAN (iSCSI, Fibre Channel):
- Verificare la connettivita' multipath: tutti i percorsi devono essere attivi
- Verificare la latenza del fabric FC o della rete iSCSI
- Queue depth del HBA: se troppo basso, le richieste I/O vengono messe in coda lato host
- Zoning/masking errato: il server non vede i LUN

```powershell
# Windows: verificare multipath I/O
mpclaim -s -d    # Mostrare dispositivi multipath e percorsi attivi
Get-MSDSMSupportedHW    # Hardware supportato da MPIO
```

```bash
# Linux: verificare multipath
multipath -ll       # Stato multipath
multipathd show paths   # Dettaglio percorsi
```

---

## Troubleshooting Email

### Mail Flow Issues

#### Analisi delle Code di Posta

```powershell
# Exchange Server: visualizzare code
Get-TransportServer | Get-Queue | Where-Object {$_.MessageCount -gt 0}
Get-Queue -Filter {MessageCount -gt 10} | Format-Table Identity, Status, MessageCount, NextHopDomain

# Dettaglio messaggi in coda
Get-Message -Queue "server\queue_name" | Select-Object -First 10 FromAddress, Status, Subject, LastError
```

**Code piene indicano:**
- Server di destinazione non raggiungibile (DNS, rete, server destinazione giu')
- Server di destinazione che rifiuta le connessioni (blocklist, limite raggiunto)
- Problemi di relay (il server non e' autorizzato a inviare verso quel dominio)

#### Message Tracking

```powershell
# Tracciare il percorso di un messaggio specifico
Get-MessageTrackingLog -Server EX01 -Sender "utente@contoso.com" -Start (Get-Date).AddHours(-4) -ResultSize 50

# Filtrare per destinatario e evento
Get-MessageTrackingLog -Recipients "dest@esempio.com" -EventId "FAIL" -Start (Get-Date).AddDays(-1)
```

**Event ID principali:**
- RECEIVE: messaggio ricevuto dal server
- SEND: messaggio inviato al next hop
- DELIVER: messaggio consegnato alla mailbox
- FAIL: consegna fallita permanentemente
- DEFER: consegna ritardata (tentativo successivo schedulato)
- DSN: notifica di stato consegna generata (bounce)

#### Analisi NDR (Non-Delivery Report)

I codici di bounce indicano la causa del mancato recapito:

| Codice | Significato | Causa Tipica |
|--------|-------------|--------------|
| 550 5.1.1 | User unknown | Indirizzo destinatario inesistente |
| 550 5.7.1 | Relay denied | Il server non e' autorizzato al relay |
| 553 5.1.3 | Invalid address | Formato indirizzo non valido |
| 421 4.7.0 | Temporary reject | Rate limiting, graylisting, problema temporaneo |
| 550 5.7.25 | SPF/DKIM fail | Autenticazione email fallita |
| 552 5.3.4 | Message too large | Messaggio supera il limite di dimensione |

#### Problemi DNS per la Posta

```bash
# Verificare record MX
dig MX contoso.com
nslookup -type=mx contoso.com

# Verificare che il mail server sia raggiungibile
telnet mail.contoso.com 25

# Verificare record SPF
dig TXT contoso.com | grep spf

# Verificare record DKIM
dig TXT selector._domainkey.contoso.com

# Verificare record DMARC
dig TXT _dmarc.contoso.com
```

**Problemi comuni:**
- Record MX mancante o che punta a un IP sbagliato
- SPF troppo restrittivo: non include tutti i server autorizzati a inviare per il dominio
- DKIM key rotation: la chiave nel DNS non corrisponde a quella configurata sul server
- DMARC policy p=reject attiva prima che SPF e DKIM siano completamente verificati

#### Configurazione Relay

- Open relay: il server accetta posta da qualsiasi sorgente verso qualsiasi destinazione (rischio di abuso spam). Deve essere bloccato
- Relay autorizzato: solo specifici IP/subnet possono utilizzare il server come relay
- Smart host: il server inoltra tutta la posta in uscita a un relay centrale (comune con servizi di email filtering)

---

### Client Issues

#### Outlook Connectivity

```powershell
# Exchange: test connettivita' Outlook
Test-OutlookConnectivity -ProbeIdentity "OutlookSelfTestProbe"

# Test Autodiscover
Test-OutlookWebServices -Identity utente@contoso.com -MailboxCredential (Get-Credential)
```

**Dall'esterno:**
Utilizzare il Microsoft Remote Connectivity Analyzer (https://testconnectivity.microsoft.com) per verificare Autodiscover, EWS, ActiveSync, e la connettivita' SMTP.

#### Verifica Autodiscover

Autodiscover e' il meccanismo che configura automaticamente il client Outlook. Se non funziona, Outlook non riesce a trovare il server.

**Test manuale:** Tenere premuto Ctrl, click destro sull'icona di Outlook nel system tray → "Test E-mail AutoConfiguration". Mostra tutti i tentativi di Autodiscover e i risultati.

**Ordine di ricerca Autodiscover:**
1. SCP (Service Connection Point) in AD
2. Root domain (https://contoso.com/autodiscover/autodiscover.xml)
3. Autodiscover subdomain (https://autodiscover.contoso.com/autodiscover/autodiscover.xml)
4. DNS SRV record (_autodiscover._tcp.contoso.com)

#### Profilo Corrotto e Problemi OST/PST

**Profilo corrotto:**
- Sintomo: Outlook si blocca all'avvio, errore "Cannot start Microsoft Outlook"
- Soluzione: creare un nuovo profilo Outlook (Pannello di Controllo → Mail → Profili)
- Tentativo di riparazione: `outlook.exe /resetnavpane` o avvio in Safe Mode (`outlook.exe /safe`)

**File OST/PST corrotti:**
- Utilizzare lo strumento di ripristino ScanPST.exe (installato con Office, tipicamente in `C:\Program Files\Microsoft Office\root\Office16\`)
- Per file OST: eliminare il file OST e lasciare che Outlook lo ricrei (riscarica da Exchange)
- Per file PST: eseguire ScanPST, se non ripara tentare con strumenti di terze parti

#### Sincronizzazione Dispositivi Mobili

- ActiveSync: verificare che il dispositivo sia nella lista dispositivi consentiti (`Get-MobileDevice -Mailbox utente@contoso.com`)
- Profilo email da riconfigurare dopo cambio password
- Certificato SSL non attendibile dal dispositivo mobile
- Policy ActiveSync (ABQ - Allow/Block/Quarantine) che blocca il dispositivo

---

## Troubleshooting Stampa

### Print Spooler

#### Spooler Service Hang

Il servizio Print Spooler che si blocca e' un problema classico che impedisce qualsiasi operazione di stampa.

```powershell
# Verificare stato del servizio
Get-Service Spooler

# Riavviare il servizio
Restart-Service Spooler -Force

# Se il riavvio non funziona, svuotare la coda e riavviare
Stop-Service Spooler -Force
Remove-Item "C:\Windows\System32\spool\PRINTERS\*" -Force
Start-Service Spooler
```

**Causa comune:** Un print job corrotto nella coda che blocca lo spooler. La procedura di svuotamento della coda (eliminare i file in `C:\Windows\System32\spool\PRINTERS\`) risolve nella maggior parte dei casi.

#### Print Queue Stuck

```powershell
# Visualizzare la coda di stampa
Get-PrintJob -PrinterName "NomePrinter"

# Rimuovere un job specifico
Remove-PrintJob -PrinterName "NomePrinter" -ID 1

# Rimuovere tutti i job
Get-PrintJob -PrinterName "NomePrinter" | Remove-PrintJob
```

#### Problemi Driver

- Driver incompatibile con la versione del sistema operativo
- Conflitto tra driver Type 3 (user mode) e Type 4 (V4 driver)
- Driver corrotto: disinstallare completamente il driver (`Remove-PrinterDriver`) e reinstallare
- In ambienti Terminal Server/RDS: preferire driver Type 4 (V4) o il driver universale del produttore

#### Connettivita' Stampante di Rete

```powershell
# Verificare raggiungibilita'
Test-NetConnection -ComputerName 10.0.1.200 -Port 9100    # Porta RAW
Test-NetConnection -ComputerName 10.0.1.200 -Port 631     # Porta IPP

# Verificare la coda
ping 10.0.1.200
```

**Problemi comuni:**
- IP della stampante cambiato (DHCP senza reservation). Soluzione: creare una DHCP reservation o assegnare IP statico
- Stampante in sleep mode con interfaccia di rete che non risponde. Verificare le impostazioni di risparmio energetico della stampante
- Firewall che blocca porta 9100 (RAW), 515 (LPR), o 631 (IPP)

#### Deployment Stampanti via GPO

- Verificare che la GPO sia applicata correttamente (`gpresult /R`)
- La stampante e' collegata per-user o per-machine? (diverse sezioni della GPO)
- Il client deve poter raggiungere il print server e scaricare il driver
- Problemi di permessi: l'utente deve avere il permesso di aggiungere stampanti (Point and Print restrictions)

---

## Strumenti Diagnostici Essenziali

### Windows

#### Event Viewer

Lo strumento piu' fondamentale per il troubleshooting su Windows. I log principali sono:
- **System:** Errori di sistema, driver, servizi
- **Application:** Errori applicativi, crash, warning
- **Security:** Logon/logoff, accesso risorse, audit
- **Setup:** Installazioni e aggiornamenti

**Ricerche efficaci:**
- Filtrare per livello (Critical, Error, Warning) e per intervallo temporale
- Correlare gli eventi per timestamp: cosa e' successo immediatamente prima dell'errore?
- Cercare l'Event ID su internet: Microsoft e la community hanno documentato la maggior parte degli Event ID

#### Reliability Monitor

Accessibile da Pannello di Controllo → Sicurezza e Manutenzione → Manutenzione → Visualizza cronologia affidabilita'. Fornisce una timeline grafica di installazioni, errori, crash e aggiornamenti. Fondamentale per correlare problemi con modifiche recenti.

#### Performance Monitor (perfmon)

- Contatori in tempo reale per CPU, memoria, disco, rete
- Data Collector Sets per raccolta dati prolungata
- Generazione report con analisi automatica

#### Sysinternals Suite

Strumenti avanzati gratuiti di Microsoft (originariamente di Mark Russinovich):
- **Process Monitor (procmon):** Cattura in tempo reale tutte le operazioni di file system, registry, rete, processo/thread. Fondamentale per capire perche' un'applicazione fallisce (file non trovato, accesso negato, errore di registro)
- **Process Explorer:** Task Manager avanzato con dettagli sui handle aperti, DLL caricate, thread, connessioni di rete per ogni processo
- **Autoruns:** Mostra tutto cio' che si avvia automaticamente (servizi, driver, scheduled task, estensioni shell, ecc.)
- **TCPView:** Visualizzazione in tempo reale di tutte le connessioni TCP/UDP con i processi associati

#### WinDbg per Analisi BSOD

Quando Windows mostra una schermata blu (BSOD), viene generato un file di dump della memoria in `C:\Windows\MEMORY.DMP` o `C:\Windows\Minidump\`.

```
# In WinDbg dopo aver aperto il dump:
!analyze -v
# Mostra il driver/componente che ha causato il crash, lo stack trace, e spesso suggerimenti sulla causa
```

#### PowerShell Diagnostic Cmdlets

```powershell
# System Information
Get-ComputerInfo
systeminfo

# Servizi in errore
Get-Service | Where-Object {$_.Status -eq 'Stopped' -and $_.StartType -eq 'Automatic'}

# Disco
Get-PhysicalDisk | Select-Object FriendlyName, MediaType, OperationalStatus, HealthStatus, Size

# Rete
Get-NetAdapter | Select-Object Name, Status, LinkSpeed
Get-DnsClientServerAddress
Get-NetRoute -DestinationPrefix '0.0.0.0/0'    # Default gateway

# Certificati in scadenza
Get-ChildItem Cert:\LocalMachine\My | Where-Object {$_.NotAfter -lt (Get-Date).AddDays(30)} | Select-Object Subject, NotAfter
```

---

### Linux

#### journalctl e dmesg

```bash
# Log recenti del sistema
journalctl -xe                      # Ultime voci con spiegazione
journalctl --since "2 hours ago"    # Ultime 2 ore
journalctl -u sshd -p err          # Solo errori di sshd
journalctl -k                      # Solo messaggi kernel (equivalente a dmesg)

# dmesg: messaggi kernel (hardware, driver, errori disco)
dmesg -T | tail -50                # Ultime 50 righe con timestamp leggibile
dmesg -T --level=err,crit,alert,emerg    # Solo errori gravi
```

#### strace, ltrace, lsof

```bash
# strace: tracciare le system call di un processo
strace -p <PID> -f -tt             # Attaccarsi a processo esistente, follow fork, timestamp
strace -e trace=network -p <PID>   # Solo system call di rete
strace -o /tmp/strace.log command  # Tracciare un nuovo comando

# ltrace: tracciare le chiamate a librerie
ltrace -p <PID>

# lsof: file e socket aperti
lsof -p <PID>                     # File aperti da un processo
lsof -i :443                      # Processi che usano porta 443
lsof -i tcp -s tcp:listen         # Tutte le porte TCP in ascolto
lsof +D /var/log                  # Processi che hanno file aperti in /var/log
```

#### Strumenti di Rete

```bash
# ss: socket statistics (sostituto moderno di netstat)
ss -tlnp                          # TCP listening, numerico, con PID
ss -s                             # Sommario statistiche socket
ss -t state established '( dport = 443 )'    # Connessioni stabilite verso porta 443

# ip: configurazione rete
ip addr show                      # Indirizzi IP
ip route show                     # Tabella di routing
ip neigh show                     # Cache ARP/NDP
ip link show                      # Stato interfacce

# tcpdump: cattura pacchetti
tcpdump -i any -nn port 53        # Catturare traffico DNS su tutte le interfacce
tcpdump -i eth0 -w /tmp/cap.pcap 'host 10.0.1.50 and tcp port 443'    # Cattura mirata su file
```

#### Strumenti di Performance

```bash
# top/htop: monitoraggio processi in tempo reale
top -bn1 -o %MEM | head -15      # Ordinato per memoria, una iterazione

# iotop: I/O per processo
iotop -o -a                       # Solo processi con I/O, accumulo

# vmstat: statistiche sistema
vmstat 5 10                       # Ogni 5 secondi, 10 iterazioni
# Colonne chiave: r (runnable), b (blocked), si/so (swap in/out), us/sy/wa (CPU user/system/wait)

# sar: System Activity Reporter (storico)
sar -u 5 10                       # CPU
sar -r 5 10                       # Memoria
sar -d 5 10                       # Disco
sar -n DEV 5 10                   # Rete
```

#### dig, curl, openssl

```bash
# dig: query DNS avanzate
dig +short A webapp.contoso.com           # Solo il risultato
dig +trace webapp.contoso.com             # Traccia completa della risoluzione
dig @8.8.8.8 contoso.com ANY             # Tutti i record, DNS specifico

# curl: test HTTP avanzati
curl -vvv https://webapp.contoso.com      # Massimo verboso (include TLS handshake)
curl -k https://webapp.contoso.com        # Ignorare errori certificato (solo per test)
curl --resolve webapp.contoso.com:443:10.0.1.50 https://webapp.contoso.com    # Forzare IP specifico

# openssl: debug TLS/SSL
openssl s_client -connect webapp.contoso.com:443 -servername webapp.contoso.com    # Handshake completo
openssl s_client -connect mail.contoso.com:25 -starttls smtp    # STARTTLS per SMTP
openssl x509 -in cert.pem -noout -text    # Dettaglio certificato locale
```

---

## Best Practices

1. **Cambiare una sola variabile alla volta.** Questa e' la regola d'oro del troubleshooting. Se si modificano due parametri contemporaneamente e il problema si risolve, non si sa quale modifica fosse necessaria. Se il problema peggiora, non si sa quale delle due ha causato il peggioramento. La tentazione di "provare tutto insieme" e' forte sotto pressione, ma porta sempre a risultati ambigui e a una comprensione superficiale del problema.

2. **Documentare ogni passo del processo diagnostico, inclusi i test negativi.** I test che non hanno trovato nulla sono importanti quanto quelli positivi: escludono cause possibili e sono preziosi per chi dovra' affrontare un problema simile in futuro. Inoltre, in caso di escalation, il team di livello superiore deve sapere cosa e' gia' stato verificato per non ripetere gli stessi test.

3. **Verificare sempre i fondamentali prima di cercare cause complesse.** La maggior parte dei problemi IT ha cause banali: cavo scollegato, servizio non avviato, spazio disco esaurito, DNS non raggiungibile, password scaduta. Verificare sempre queste cause per prime, indipendentemente dalla complessita' apparente del sintomo. Un principio noto come "When you hear hoofbeats, think horses, not zebras."

4. **Fare un backup o uno snapshot prima di qualsiasi modifica significativa.** Prima di modificare la configurazione di un server in produzione, fare uno snapshot della VM o un backup della configurazione. Se l'intervento peggiora la situazione, il rollback deve essere immediato e garantito. Il tempo speso per il backup e' sempre inferiore al tempo necessario per ricostruire da zero.

5. **Comunicare proattivamente con gli utenti e il management durante l'intervento.** Gli utenti tollerano meglio un'interruzione quando sanno che qualcuno ci sta lavorando e quando hanno una stima, anche approssimativa, dei tempi. L'assenza di comunicazione genera ansia e telefonate che rallentano il troubleshooting. Inviare un aggiornamento ogni 30-60 minuti durante un incidente significativo.

6. **Stabilire e mantenere una baseline di performance per ogni sistema critico.** Senza una baseline, non si puo' dire se un valore e' "normale" o "anomalo". Raccogliere metriche di CPU, memoria, disco e rete in condizioni normali per poterle confrontare durante il troubleshooting. I sistemi di monitoraggio automatizzano questo processo.

7. **Non ignorare i warning: spesso precedono gli errori critici.** Un warning nel log di oggi e' l'errore critico di domani. Dedicare tempo regolare alla revisione dei warning e risolverli proattivamente. Un disco con SMART warning sara' un disco guasto entro settimane. Un certificato in scadenza tra 30 giorni causera' un'interruzione se ignorato.

8. **Mantenere una knowledge base aggiornata con le soluzioni ai problemi ricorrenti.** Ogni problema risolto dovrebbe generare un articolo nella knowledge base. Includere: sintomo, causa, procedura di risoluzione, comandi utilizzati, screenshot se utili. La knowledge base riduce il MTTR per problemi gia' visti e permette anche a tecnici meno esperti di risolvere autonomamente.

9. **Conoscere i propri strumenti a fondo prima dell'emergenza.** Non e' il momento di imparare a usare Wireshark o Process Monitor quando il sistema e' giu'. Investire tempo nella formazione sugli strumenti diagnostici in condizioni normali. Esercitarsi a catturare traffico, analizzare log, e utilizzare gli strumenti di performance prima che siano necessari in emergenza.

10. **Effettuare una post-mortem dopo ogni incidente significativo.** La post-mortem non e' una ricerca del colpevole (blameless post-mortem), ma un'analisi strutturata per capire cosa e' successo, perche' non e' stato prevenuto, come e' stato risolto, e cosa fare per evitare che si ripeta. Condividere le post-mortem con tutto il team. Ogni incidente e' un'opportunita' di apprendimento.

---

## Troubleshooting del Troubleshooting

A volte il processo di troubleshooting stesso si inceppa: non si riesce a trovare la causa, i test non danno risultati chiari, o il problema sembra sfidare la logica. Questa sezione affronta i meta-problemi del troubleshooting.

### Criteri di Escalation

Non ogni problema puo' o deve essere risolto al primo livello. Riconoscere quando escalare e' una competenza importante tanto quanto risolvere.

**Escalare quando:**
- Il tempo trascorso supera il limite definito dalla priorita' dell'incidente (es. P1: escalare dopo 30 minuti senza progressi)
- Non si hanno le competenze tecniche necessarie (es. problema di rete complesso richiede un network engineer)
- Non si hanno gli accessi necessari (es. problema su un firewall a cui non si ha accesso)
- Il problema coinvolge componenti di terze parti (vendor software, ISP, cloud provider)
- L'impatto e' piu' ampio di quanto inizialmente stimato e richiede coordinamento di piu' team

**Come escalare efficacemente:**
- Fornire un riassunto chiaro del problema e dell'impatto
- Elencare tutti i test gia' effettuati e i loro risultati (evita ripetizioni)
- Fornire log, catture, screenshot rilevanti
- Specificare la propria ipotesi corrente, anche se non confermata
- Indicare chiaramente cosa si chiede al livello superiore

### Quando Ricostruire invece che Riparare

A volte riparare un sistema e' piu' costoso (in tempo e rischio) che ricostruirlo.

**Considerare la ricostruzione quando:**
- Il sistema e' stato compromesso (malware, intrusione): non ci si puo' fidare di un sistema compromesso anche dopo la "pulizia"
- La corruzione e' estesa e non deterministica: problemi di file system corrotto, registro di Windows corrotto in modo diffuso
- Il tempo per diagnosticare supera il tempo per ricostruire: se si ha un'immagine o un template aggiornato, il deploy puo' essere piu' rapido della diagnosi
- Il sistema non era documentato e la sua configurazione e' sconosciuta: a volte e' piu' efficiente ricostruire con una configurazione nota e documentata

**Prerequisiti per la ricostruzione:**
- Backup dei dati verificato e accessibile
- Documentazione della configurazione (o template/immagine aggiornata)
- Piano di migrazione per i servizi ospitati
- Comunicazione con gli utenti sul downtime previsto

### Coinvolgere il Supporto del Vendor in Modo Efficace

Quando si apre un caso con il supporto del vendor, la qualita' delle informazioni fornite determina la velocita' di risoluzione.

**Preparare prima di chiamare:**
- Versione esatta del prodotto, patch level, sistema operativo
- Descrizione precisa del problema con timeline
- Test gia' effettuati e risultati
- Log rilevanti gia' estratti e pronti da condividere
- Ambiente (produzione/staging/test), numero di utenti colpiti, impatto sul business
- Eventuali modifiche recenti all'ambiente

**Durante l'interazione:**
- Se la prima risposta del supporto e' generica ("riavviare il servizio"), insistere che e' gia' stato provato e chiedere di procedere al livello successivo
- Chiedere sempre un case number e il nome del tecnico assegnato
- Se il problema e' critico, chiedere l'escalation a un senior engineer e mantenere la pressione con aggiornamenti regolari
- Richiedere una RCA scritta dal vendor dopo la risoluzione

### Tecniche di Investigazione Parallela

Quando un singolo filone di indagine non produce risultati, avviare investigazioni parallele puo' accelerare la risoluzione.

**Strategie:**
- **Dividere il team:** Se disponibili piu' persone, assegnare filoni diversi a ciascuna (es. una persona indaga la rete, un'altra il server, una terza l'applicazione)
- **Raccolta dati massiva:** Attivare logging avanzato, cattura di rete, e monitoraggio granulare su tutti i componenti coinvolti. Anche se non si sa ancora cosa cercare, avere i dati disponibili quando serve e' fondamentale
- **Confronto con ambiente di staging/test:** Replicare il problema in un ambiente non di produzione dove si puo' testare in modo piu' aggressivo (es. riavviare servizi, modificare configurazioni senza impatto sugli utenti)
- **Ricerca esterna:** Cercare il messaggio di errore esatto (tra virgolette) su motori di ricerca, forum tecnici, knowledge base del vendor. Spesso qualcun altro ha gia' avuto lo stesso problema
- **Ragionamento per assurdo:** Se tutti i componenti sembrano funzionare correttamente ma il sistema non funziona, chiedersi: "Cosa devo aver sbagliato a verificare?" Riesaminare i test effettuati con occhio critico. A volte un test considerato positivo era in realta' ambiguo

### Trappole Cognitive nel Troubleshooting

Essere consapevoli dei bias cognitivi che possono sviare la diagnosi:

- **Confirmation bias:** Cercare solo le prove che confermano la propria teoria, ignorando quelle contrarie. Contromisura: cercare attivamente prove che smentiscano la teoria
- **Anchoring:** Fissarsi sulla prima ipotesi e non abbandonarla anche quando le evidenze la smentiscono. Contromisura: stabilire un limite di tempo per ogni teoria; se dopo N minuti non si conferma, passare alla successiva
- **Recency bias:** Assumere che la causa sia correlata all'ultimo cambiamento effettuato. Spesso e' vero, ma non sempre. Contromisura: verificare la correlazione, non assumerla
- **Expert bias:** "So gia' cos'e'" senza verificare. L'esperienza e' preziosa ma puo' portare a saltare i fondamentali. Contromisura: anche se si pensa di sapere la causa, eseguire comunque il test di conferma
- **Tunnel vision:** Concentrarsi su un singolo componente ignorando il quadro complessivo. Contromisura: periodicamente fare un passo indietro e riconsiderare il problema dall'alto

Il troubleshooting efficace e' tanto una disciplina mentale quanto una competenza tecnica. La combinazione di un framework strutturato, strumenti appropriati, comunicazione chiara e consapevolezza dei propri limiti cognitivi e' la ricetta per risolvere qualsiasi problema IT in modo efficiente e duraturo.

---

## Root Cause Analysis Approfondita

L'analisi delle cause radice (Root Cause Analysis, RCA) rappresenta il cuore intellettuale del troubleshooting professionale. Mentre il framework a sei fasi descrive il processo generale, la RCA fornisce le tecniche specifiche per scavare oltre i sintomi superficiali e identificare la vera origine di un problema. Un troubleshooter che si limita a risolvere il sintomo senza comprendere la causa radice condanna l'organizzazione a subire lo stesso problema piu' e piu' volte.

La RCA non e' una singola tecnica, ma una famiglia di metodologie complementari. Ciascuna ha punti di forza specifici e si adatta meglio a determinate tipologie di problemi. Un professionista IT maturo conosce e padroneggia tutte queste tecniche, scegliendo quella piu' appropriata in base al contesto.

### La Tecnica dei 5 Whys

La tecnica dei 5 Whys (5 Perche') e' stata sviluppata da Sakichi Toyoda e adottata dal Toyota Production System negli anni '50. Nonostante la sua semplicita', resta una delle tecniche piu' potenti per arrivare alla causa radice di un problema.

**Principio:** Si parte dal sintomo osservato e si chiede ripetutamente "Perche'?" ad ogni risposta, fino a raggiungere la causa fondamentale. Il numero 5 e' una guida, non un vincolo rigido: a volte bastano 3 iterazioni, altre volte ne servono 7 o piu'.

**Esempio pratico IT — Server web non raggiungibile:**

```
Problema: Il sito web aziendale e' irraggiungibile dalle 14:30.

Perche' 1: Perche' il sito e' irraggiungibile?
→ Perche' il servizio Apache sul server web01 e' in stato "stopped".

Perche' 2: Perche' il servizio Apache si e' fermato?
→ Perche' il processo e' stato terminato dal kernel per OOM (Out of Memory).

Perche' 3: Perche' il server ha esaurito la memoria?
→ Perche' un processo Java (applicazione interna) ha consumato 
  14 GB di RAM su un server con 16 GB totali.

Perche' 4: Perche' il processo Java ha consumato cosi' tanta memoria?
→ Perche' un memory leak nell'applicazione causa crescita progressiva 
  dell'heap senza garbage collection efficace.

Perche' 5: Perche' il memory leak non e' stato rilevato prima?
→ Perche' non e' configurato alcun alert di monitoraggio sulla soglia 
  di utilizzo memoria del server, e non ci sono limiti di heap (-Xmx) 
  configurati per il processo Java.

Causa radice: Assenza di monitoraggio proattivo della memoria e 
configurazione JVM senza limiti di heap.

Azioni correttive:
1. Configurare -Xmx4g sulla JVM per limitare il consumo di memoria
2. Configurare alert su Zabbix/Prometheus per memoria > 80%
3. Segnalare il memory leak al team di sviluppo per correzione
4. Valutare il sizing del server (16 GB potrebbero essere insufficienti)
```

**Regole per un 5 Whys efficace:**

1. **Basarsi su fatti, non su supposizioni.** Ogni risposta "perche'" deve essere verificata con evidenze (log, metriche, test). Se la risposta e' una supposizione, segnarla come tale e verificarla prima di procedere
2. **Non fermarsi ai sintomi tecnici.** Spesso la causa radice e' organizzativa o di processo: mancanza di monitoraggio, documentazione assente, formazione insufficiente, processo di change management bypassato
3. **Evitare risposte troppo generiche.** "Perche' il server e' caduto? → Perche' l'hardware e' vecchio" non e' utile. Servono dettagli: quale componente hardware, quale tipo di guasto, quale indicatore SMART
4. **Considerare cause multiple.** I problemi complessi hanno spesso piu' di una causa radice. Se al secondo "Perche'" emergono due risposte plausibili, seguire entrambi i rami
5. **Coinvolgere le persone giuste.** La persona che risponde ai "Perche'" deve avere la conoscenza diretta del componente in questione. Non fare 5 Whys da soli su un sistema che non si conosce

**Limitazioni:**
- Rischia di portare a una singola catena causale, ignorando la complessita' multi-fattoriale
- Soggettiva: persone diverse possono arrivare a cause radice diverse partendo dallo stesso problema
- Non adatta a problemi molto complessi con molteplici interazioni. In questi casi, combinare con il diagramma di Ishikawa

---

### Diagramma di Ishikawa (Fishbone)

Il diagramma di Ishikawa, noto anche come diagramma a lisca di pesce (fishbone diagram) o diagramma causa-effetto, e' stato sviluppato da Kaoru Ishikawa negli anni '60. E' particolarmente efficace per esplorare sistematicamente tutte le possibili cause di un problema, organizzandole in categorie logiche.

**Struttura:** Il diagramma ha la forma di uno scheletro di pesce. La "testa" a destra rappresenta il problema (effetto). La "spina dorsale" e' la linea centrale orizzontale. Le "costole" principali sono le categorie di cause. Da ogni costola si diramano le cause specifiche e le sotto-cause.

**Categorie Standard per IT (le 6M adattate):**

Per l'IT, le tradizionali 6M del manufacturing (Man, Machine, Method, Material, Measurement, Mother Nature) si adattano in:

1. **Persone (People):** Errore umano, competenze insufficienti, formazione carente, turni sottodimensionati, comunicazione insufficiente, procedure non seguite
2. **Tecnologia (Technology):** Hardware difettoso, software buggato, versioni incompatibili, capacita' insufficiente, obsolescenza, firmware non aggiornato
3. **Processi (Process):** Procedure assenti o inadeguate, change management bypassato, testing insufficiente, deployment non controllato, mancanza di peer review
4. **Ambiente (Environment):** Temperatura, alimentazione elettrica, connettivita' di rete, datacenter, dipendenze esterne, cloud provider, ISP
5. **Dati (Data):** Corruzione dati, input non validato, migrazione errata, backup non verificato, crescita non pianificata, encoding errato
6. **Monitoraggio (Monitoring):** Alert mancanti, soglie non calibrate, falsi positivi che mascherano i veri problemi, log insufficienti, metriche non raccolte

**Esempio pratico — Diagramma Ishikawa per "Applicazione lenta":**

```
                            APPLICAZIONE LENTA
                                    |
    ┌───────────────┬───────────────┼───────────────┬───────────────┐
    |               |               |               |               |
 PERSONE        TECNOLOGIA       PROCESSI         DATI          AMBIENTE
    |               |               |               |               |
 ├─ DBA assente  ├─ CPU satura  ├─ No load     ├─ Query      ├─ Latenza
 |  in azienda  |  al 95%      |  testing     |  N+1        |  WAN alta
 |              |               |  pre-deploy  |  su tabelle |
 ├─ Dev non     ├─ RAM al      |              |  da 50M     ├─ SAN al
 |  ottimizza   |  limite      ├─ Nessun     |  di righe   |  limite
 |  le query    |  (14/16 GB)  |  capacity   |              |  di IOPS
 |              |               |  planning   ├─ Indici     |
 ├─ Nessun      ├─ Disco HDD  |              |  mancanti   ├─ Rete
    code review  |  (no SSD)   ├─ Deploy      |  o obsoleti |  saturata
                 |              |  in orario  |              |  al 90%
                 ├─ JVM heap   |  di picco   ├─ Cache non  |
                    non tuned  |              |  configurata├─ DNS lento
                               ├─ No APM     |              |  (200ms)
                                  monitoring ├─ Blob in DB |
                                             |  da 500 MB  |
                                             |              |
                                          MONITORAGGIO
                                             |
                                          ├─ Nessun alert
                                          |  su tempo
                                          |  di risposta
                                          ├─ Log level
                                          |  troppo basso
                                          ├─ No distributed
                                             tracing
```

**Procedura di Utilizzo:**

1. **Definire il problema in modo preciso** (non "applicazione lenta" ma "tempo di risposta medio della pagina /dashboard > 8 secondi durante le ore 09:00-12:00, contro una baseline di 1.2 secondi")
2. **Disegnare la struttura base** con le categorie principali
3. **Brainstorming delle cause** per ciascuna categoria, coinvolgendo persone con competenze diverse (network, server, database, sviluppo, operations)
4. **Approfondire le sotto-cause** per ogni causa identificata (sub-branching)
5. **Verificare e prioritizzare** ogni causa con dati ed evidenze
6. **Combinare con i 5 Whys** sulle cause piu' probabili per arrivare alla radice

---

### Fault Tree Analysis (FTA)

La Fault Tree Analysis (FTA) e' una tecnica top-down di analisi deduttiva che utilizza la logica booleana per modellare le combinazioni di eventi che possono causare un guasto di sistema. Originariamente sviluppata nei Bell Labs negli anni '60 per l'analisi di sicurezza dei missili balistici, e' diventata uno standard anche nell'ingegneria dell'affidabilita' IT.

**Differenza rispetto al diagramma di Ishikawa:** Mentre Ishikawa esplora tutte le possibili cause in modo qualitativo, la FTA modella le relazioni logiche tra gli eventi (AND, OR) e puo' essere utilizzata per calcoli di probabilita' di guasto.

**Elementi del Fault Tree:**

- **Top Event:** L'evento di guasto principale che si sta analizzando (es. "Servizio email completamente fermo")
- **Gate AND:** Tutti gli eventi sotto questo gate devono verificarsi affinche' l'evento superiore si verifichi. Esempio: il servizio si ferma solo se sia il server primario sia il server secondario sono giu'
- **Gate OR:** Basta che uno degli eventi sotto questo gate si verifichi. Esempio: il server puo' andare giu' per guasto hardware OPPURE per crash del software OPPURE per attacco DDoS
- **Basic Event:** Evento elementare che non richiede ulteriore analisi (es. "disco guasto", "patch non applicata")
- **Undeveloped Event:** Evento che non viene analizzato ulteriormente in questo albero per mancanza di dati o perche' fuori scope

**Esempio FTA — Servizio Email Non Disponibile:**

```
              [Servizio Email Non Disponibile]
                          |
                        (OR)
              ┌───────────┼───────────┐
              |           |           |
        [Server MX    [Network    [Storage
         Fermo]       Failure]     Pieno]
              |           |           |
            (OR)        (OR)        (AND)
         ┌────┼────┐  ┌──┼──┐    ┌───┼───┐
         |    |    |  |     |    |       |
     [Crash [HW  [OS [Link [FW  [Mail  [Nessun
      App]  Fail] Panic]Down]Block]DB    alert
                                Full]  configurato]
```

In questo esempio, il servizio email e' non disponibile se si verifica ALMENO UNO tra: server MX fermo, failure di rete, o storage pieno. Lo storage pieno richiede che ENTRAMBE le condizioni siano vere (AND): il database mail e' pieno E non c'e' un alert configurato (altrimenti si sarebbe intervenuti prima).

**Quando usare la FTA in IT:**
- Analisi di affidabilita' di servizi critici
- Pianificazione della ridondanza (identificare single point of failure)
- Analisi post-incidente di guasti complessi con molteplici fattori
- Business Continuity Planning e Disaster Recovery Design

**Limitazione:** Per sistemi distribuiti moderni (microservizi, cloud-native), l'albero dei guasti puo' diventare enormemente complesso. In questi contesti, gli strumenti di observability automatizzata (OpenTelemetry, distributed tracing) sono piu' pratici per la diagnostica in tempo reale.

---

### Metodo Kepner-Tregoe

Il metodo Kepner-Tregoe (KT), sviluppato da Charles Kepner e Benjamin Tregoe, e' uno dei metodi strutturati piu' rigorosi per l'analisi dei problemi. E' raccomandato da ITIL come tecnica per il Problem Management ed e' particolarmente efficace per problemi complessi dove le cause non sono immediatamente evidenti.

**I quattro processi KT:**

1. **Situation Appraisal (SA):** Chiarire la situazione, identificare le preoccupazioni, stabilire le priorita', decidere il prossimo passo
2. **Problem Analysis (PA):** Trovare la causa di un problema attraverso la specifica IS/IS NOT
3. **Decision Analysis (DA):** Fare scelte tra alternative, valutando rischi
4. **Potential Problem Analysis (PPA):** Proteggere un piano o un'azione da potenziali rischi futuri

**La Matrice IS/IS NOT:**

Il cuore del Problem Analysis KT e' la specifica IS/IS NOT, che delimita il problema con precisione chirurgica confrontando cio' che e' affetto con cio' che non lo e', per identificare i "distinctions" (differenze) che possono spiegare la causa.

```
┌─────────────┬──────────────────────┬──────────────────────┬──────────────────┐
| Dimensione  | IS (E')              | IS NOT (NON E')      | Distinzioni      |
├─────────────┼──────────────────────┼──────────────────────┼──────────────────┤
| COSA        | Applicazione CRM     | Tutte le altre       | CRM aggiornato   |
|             | non funziona         | applicazioni         | venerdi' scorso  |
|             |                      | funzionano           |                  |
├─────────────┼──────────────────────┼──────────────────────┼──────────────────┤
| DOVE        | Solo ufficio Milano  | Roma e Napoli        | Milano ha un     |
|             |                      | funzionano           | proxy locale     |
|             |                      | correttamente        | diverso          |
├─────────────┼──────────────────────┼──────────────────────┼──────────────────┤
| QUANDO      | Da lunedi' mattina   | Venerdi' funzionava  | Weekend:         |
|             | ore 08:00            | regolarmente         | manutenzione     |
|             |                      |                      | proxy            |
├─────────────┼──────────────────────┼──────────────────────┼──────────────────┤
| QUANTO      | Tutti gli utenti     | Non tutti i moduli:  | Moduli che usano |
|             | di Milano            | solo CRM vendite     | API v3 (nuova)   |
|             |                      | e CRM marketing      |                  |
└─────────────┴──────────────────────┴──────────────────────┴──────────────────┘

Ipotesi derivata dalle distinzioni:
L'aggiornamento del CRM di venerdi' ha introdotto chiamate API v3 che il
proxy di Milano (aggiornato nel weekend con nuove regole) blocca.

Test: Bypassare il proxy di Milano → CRM funziona → Causa confermata.
```

**Quando usare KT:**
- Post-incidente, durante l'analisi RCA formale (non durante l'incidente in corso — richiede troppo tempo)
- Problemi complessi dove i metodi rapidi (5 Whys) non hanno funzionato
- Problemi ricorrenti mai risolti definitivamente
- Situazioni con molteplici teorie in conflitto tra i membri del team

---

### Analisi di Pareto (80/20)

Il principio di Pareto, applicato al troubleshooting IT, indica che circa l'80% degli incidenti e' causato dal 20% delle cause radice. L'analisi di Pareto permette di concentrare gli sforzi di prevenzione e miglioramento sulle cause che generano il maggior numero di incidenti.

**Procedura:**

1. **Raccogliere i dati:** Estrarre dal sistema di ticketing tutti gli incidenti di un periodo (es. ultimo trimestre)
2. **Categorizzare per causa radice:** Raggruppare gli incidenti per causa (es. "patch mancante", "errore di configurazione", "guasto hardware", "capacity insufficiente")
3. **Ordinare per frequenza:** Dalla causa con piu' incidenti a quella con meno
4. **Calcolare la percentuale cumulativa**
5. **Identificare il 20% critico:** Le cause che insieme generano l'80% degli incidenti

**Esempio di Analisi Pareto su 200 incidenti trimestrali:**

```
| Causa Radice               | Incidenti | %    | Cumulativo |
|----------------------------|-----------|------|------------|
| Errore di configurazione   | 54        | 27%  | 27%        |
| Patch/Update non applicato | 38        | 19%  | 46%        |
| Capacity insufficiente     | 32        | 16%  | 62%        |
| Password/Certificato scad. | 24        | 12%  | 74%        |
| Guasto hardware            | 18        |  9%  | 83%        |
| Bug software vendor        | 14        |  7%  | 90%        |
| Errore utente              | 10        |  5%  | 95%        |
| Attacco/Sicurezza          |  6        |  3%  | 98%        |
| Causa sconosciuta          |  4        |  2%  | 100%       |

→ Le prime 4 cause (20% delle categorie) generano il 74% degli incidenti.
  Concentrare gli sforzi su: configurazione, patching, capacity, scadenze.
```

**Azioni derivabili:**
- Errori di configurazione al 27%: implementare Infrastructure as Code (IaC), peer review obbligatoria per ogni change, drift detection automatizzata
- Patch non applicati al 19%: automatizzare il patching con WSUS/SCCM/Ansible, creare finestre di manutenzione regolari
- Capacity insufficiente al 16%: implementare capacity planning trimestrale con proiezioni di crescita, configurare alert predittivi
- Certificati/Password scaduti al 12%: inventario centralizzato dei certificati con alert 60/30/7 giorni prima della scadenza

---

### Template RCA Operativo

Un template RCA standardizzato garantisce che ogni analisi sia completa, coerente e utilizzabile come riferimento futuro.

```
═══════════════════════════════════════════════════════
       ROOT CAUSE ANALYSIS — TEMPLATE OPERATIVO
═══════════════════════════════════════════════════════

RCA ID:          RCA-2026-0042
Data Incidente:  2026-05-20 14:32 UTC
Data Analisi:    2026-05-22
Analista:        [Nome dell'analista]
Revisore:        [Nome del revisore]
Servizio:        [Nome del servizio impattato]
Severity:        P1 / P2 / P3 / P4

────────────────────────────────────────────────────
1. DESCRIZIONE DELL'INCIDENTE
────────────────────────────────────────────────────
Sintomo osservato: [Descrizione precisa del sintomo]
Impatto: [Utenti/Servizi/Revenue impattati]
Durata: [Da HH:MM a HH:MM UTC — durata totale]
Ticket di riferimento: [INC-XXXX]

────────────────────────────────────────────────────
2. TIMELINE DEGLI EVENTI
────────────────────────────────────────────────────
| Ora (UTC)    | Evento                              |
|--------------|-------------------------------------|
| 14:32        | Primo alert dal monitoraggio        |
| 14:35        | Conferma impatto utenti             |
| 14:40        | Inizio indagine — team Infra        |
| 14:55        | Identificata causa probabile        |
| 15:10        | Applicata correzione                |
| 15:15        | Servizio ripristinato               |
| 15:30        | Conferma stabilita' del servizio    |
| 15:30        | Incidente chiuso                    |

────────────────────────────────────────────────────
3. ANALISI DELLA CAUSA RADICE
────────────────────────────────────────────────────
Metodo utilizzato: [5 Whys / Ishikawa / Kepner-Tregoe]

[Dettaglio dell'analisi — inserire il diagramma o
la catena dei 5 Whys qui]

Causa radice identificata:
[Descrizione chiara e specifica della vera causa]

Cause contribuenti:
- [Fattore 1]
- [Fattore 2]

────────────────────────────────────────────────────
4. AZIONI CORRETTIVE
────────────────────────────────────────────────────
| # | Azione                | Owner    | Scadenza   | Stato    |
|---|----------------------|----------|------------|----------|
| 1 | [Azione immediata]   | [Nome]   | 2026-05-22 | Chiusa   |
| 2 | [Azione a breve]     | [Nome]   | 2026-06-01 | Aperta   |
| 3 | [Azione preventiva]  | [Nome]   | 2026-06-15 | Aperta   |
| 4 | [Miglioramento proc.]| [Nome]   | 2026-07-01 | Pianif.  |

────────────────────────────────────────────────────
5. LEZIONI APPRESE
────────────────────────────────────────────────────
- Cosa ha funzionato bene: [...]
- Cosa non ha funzionato: [...]
- Cosa abbiamo avuto fortuna: [...]

────────────────────────────────────────────────────
6. METRICHE
────────────────────────────────────────────────────
MTTD (Mean Time To Detect):    [minuti]
MTTR (Mean Time To Resolve):   [minuti]
Impatto utenti:                [numero utenti x minuti]
Impatto finanziario stimato:   [€ se calcolabile]

═══════════════════════════════════════════════════════
```

---

## Problem Management ITIL

Il Problem Management, come definito nel framework ITIL (Information Technology Infrastructure Library), e' il processo dedicato alla gestione del ciclo di vita di tutti i problemi IT. Un "problema" in termini ITIL e' la causa (o potenziale causa) di uno o piu' incidenti. La distinzione e' fondamentale: l'Incident Management si occupa di ripristinare il servizio il piu' rapidamente possibile; il Problem Management si occupa di trovare e correggere la causa radice per prevenire il ripetersi degli incidenti.

### Ciclo di Vita del Problema

Il ciclo di vita di un problema ITIL attraversa fasi ben definite:

1. **Rilevamento del Problema (Problem Detection):** Un problema puo' essere identificato da molteplici fonti:
   - Analisi dei trend degli incidenti (pattern ripetitivi)
   - Escalation da parte dell'Incident Management per incidenti maggiori
   - Segnalazione dal monitoraggio di eventi (correlazione di alert)
   - Analisi proattiva dell'infrastruttura
   - Notifiche dai vendor su difetti noti (es. security advisory)
   - Post-mortem di incidenti maggiori

2. **Registrazione e Categorizzazione:** Il problema viene registrato nel sistema di ticketing con una categoria (rete, server, applicazione, sicurezza, ecc.), una priorita' basata sulla matrice impatto/urgenza, e un collegamento agli incidenti correlati.

3. **Investigazione e Diagnosi:** Fase di analisi utilizzando le tecniche di RCA (5 Whys, Ishikawa, Kepner-Tregoe). L'obiettivo e' identificare la causa radice e determinare se esiste un workaround applicabile immediatamente.

4. **Workaround Documentation:** Se viene trovato un workaround (soluzione temporanea che mitiga l'impatto senza risolvere la causa radice), viene documentato e reso disponibile al Service Desk e agli utenti.

5. **Known Error Record:** Quando la causa radice e' identificata e documentata, il problema diventa un Known Error (Errore Noto) nel Known Error Database (KEDB). Il Known Error include: la causa radice, il workaround (se disponibile), e lo stato della soluzione permanente.

6. **Risoluzione:** La soluzione permanente viene implementata attraverso il processo di Change Management. Solo dopo che il change e' stato applicato e verificato, il problema viene chiuso.

7. **Chiusura e Revisione:** Il problem record viene chiuso con tutte le informazioni complete, e viene effettuata una revisione per valutare l'efficacia del processo.

### Problem Management Reattivo

Il Problem Management reattivo si attiva dopo che uno o piu' incidenti si sono gia' verificati. Il trigger piu' comune e' un incidente maggiore (Major Incident) che richiede una RCA formale, oppure un pattern di incidenti ripetitivi che suggerisce una causa comune sottostante.

**Trigger per l'apertura di un Problem Record reattivo:**

- Major Incident (P1 o P2) — apertura automatica del Problem dopo la risoluzione dell'incidente
- Incidenti ricorrenti (3+ incidenti con la stessa categorizzazione entro 30 giorni)
- Incidente con causa radice sconosciuta (risolto tramite riavvio o workaround senza comprendere la causa)
- Escalation dal Service Desk per incidenti complessi non risolvibili con le procedure standard

**Procedura operativa:**

```
Incidente risolto → Analisi necessaria? → SI → Apri Problem Record
                                         → Assegna Problem Manager
                                         → Esegui RCA (5 Whys, Ishikawa)
                                         → Identifica causa radice
                                         → Workaround disponibile? 
                                            → SI → Documenta in KEDB
                                            → NO → Escalare al vendor/sviluppo
                                         → Soluzione permanente identificata?
                                            → SI → Apri RFC (Request for Change)
                                            → Implementa tramite Change Management
                                            → Verifica risoluzione
                                            → Chiudi Problem Record
```

### Problem Management Proattivo

Il Problem Management proattivo mira a identificare e risolvere i problemi prima che causino incidenti. E' la forma piu' matura di Problem Management e richiede un investimento significativo in monitoraggio, analisi dei trend e capacity planning.

**Attivita' proattive:**

1. **Trend Analysis:** Analisi periodica (mensile) dei dati degli incidenti per identificare pattern emergenti. Esempio: aumento del 40% degli incidenti "disco pieno" su server di database → problema di capacity planning
2. **Pain Value Analysis:** Calcolare il "valore del dolore" per ogni servizio combinando: numero di incidenti, durata totale, numero di utenti impattati, criticita' del servizio. Concentrare le risorse di Problem Management sui servizi con il pain value piu' alto
3. **Maturity Audit dell'Infrastruttura:** Revisione periodica dello stato di salute dell'infrastruttura: server con EOL (End of Life) imminente, software fuori supporto, certificati in scadenza, licenze in esaurimento
4. **Vulnerability Management Integration:** Coordinamento con il team di sicurezza per trasformare le vulnerabilita' note in Problem Record e tracciare la loro risoluzione
5. **Capacity Planning:** Proiezioni di crescita basate sui dati storici per anticipare i colli di bottiglia prima che causino incidenti

### Known Error Database (KEDB)

Il KEDB e' un database che contiene tutti gli errori noti dell'infrastruttura: problemi per i quali la causa radice e' stata identificata e un workaround o una soluzione permanente e' documentata. Il KEDB e' uno strumento fondamentale per il Service Desk, perche' permette di risolvere rapidamente gli incidenti ricorrenti senza dover rieseguire ogni volta la diagnosi.

**Struttura di un record KEDB:**

```
KEDB ID:         KE-2026-0128
Problem ID:      PRB-2026-0042
Data Creazione:  2026-04-15
Servizio:        Exchange Online - Outlook Desktop
Categoria:       Applicazione > Email > Client

Sintomo:
  Outlook si blocca per 30-60 secondi quando si apre un
  allegato Excel su client Windows 11 con Office 2021 LTSC.

Causa Radice:
  Conflitto tra il Protected View di Excel e la policy DLP
  (Data Loss Prevention) aziendale che scansiona gli allegati.
  Il timeout della scansione DLP blocca il thread UI di Outlook.

Workaround:
  1. Salvare l'allegato su disco prima di aprirlo
  2. Oppure: disabilitare Protected View per file da Outlook
     (File > Opzioni > Centro protezione > Impostazioni
     centro protezione > Visualizzazione protetta > deselezionare
     "Abilita visualizzazione protetta per allegati di Outlook")

Soluzione Permanente:
  Aggiornamento a Office 2024 o M365 Apps che corregge il bug
  (KB5024xxx). RFC-2026-0089 in pianificazione per Q3 2026.

Stato: Workaround attivo, soluzione permanente pianificata
```

### Workaround vs Soluzione Definitiva

La distinzione tra workaround e soluzione definitiva e' critica nel Problem Management:

| Aspetto | Workaround | Soluzione Definitiva |
|---------|-----------|---------------------|
| **Obiettivo** | Mitigare l'impatto immediatamente | Eliminare la causa radice |
| **Tempistica** | Minuti/ore | Giorni/settimane/mesi |
| **Rischio** | Basso (non modifica il sistema) | Medio/Alto (richiede change) |
| **Durata** | Temporaneo (fino alla soluzione) | Permanente |
| **Processo** | Applicabile direttamente | Richiede Change Management |
| **Esempio** | Riavviare il servizio ogni notte | Correggere il memory leak |

Un workaround ben documentato e' spesso la differenza tra un Service Desk efficiente e uno sopraffatto dagli incidenti. Tuttavia, un workaround non deve mai diventare la "soluzione" accettata: ogni workaround attivo deve avere un Problem Record associato con una timeline per la soluzione definitiva.

---

## Matrice di Escalation e Priorita'

### Matrice Impatto-Urgenza

La priorita' di un incidente o problema viene determinata dall'incrocio di due dimensioni: l'impatto (quanti utenti/servizi sono colpiti e quanto e' critico il servizio) e l'urgenza (quanto rapidamente deve essere risolto).

**Definizioni di Impatto:**

| Livello | Descrizione | Esempio |
|---------|-------------|---------|
| **Alto** | Servizio critico completamente fermo, o degradazione che colpisce >50% degli utenti | Email aziendale ferma, ERP non accessibile, rete dell'intero sito giu' |
| **Medio** | Servizio importante degradato, o servizio non critico fermo, o 10-50% degli utenti colpiti | Stampante di reparto ferma, VPN lenta, applicazione dipartimentale non disponibile |
| **Basso** | Singolo utente colpito, servizio non critico degradato, esiste workaround | PC singolo utente lento, problema cosmetico interfaccia, feature non critica non funzionante |

**Definizioni di Urgenza:**

| Livello | Descrizione | Esempio |
|---------|-------------|---------|
| **Alta** | Impatto sul business in corso, nessun workaround disponibile, deadline imminente | Chiusura contabile in corso e ERP fermo, produzione bloccata |
| **Media** | Impatto sul business con workaround disponibile, o deadline non imminente | Utenti possono lavorare con metodo alternativo, impatto finanziario limitato |
| **Bassa** | Nessun impatto immediato sul business, puo' essere schedulato | Richiesta di miglioramento, problema che si manifesta raramente |

**Matrice di Calcolo Priorita':**

```
                    U R G E N Z A
                 Alta    Media    Bassa
            ┌────────┬────────┬────────┐
   Alto     |   P1   |   P2   |   P3   |
I           |CRITICAL| HIGH   | MEDIUM |
M           ├────────┼────────┼────────┤
P   Medio   |   P2   |   P3   |   P4   |
A           | HIGH   | MEDIUM |  LOW   |
T           ├────────┼────────┼────────┤
T   Basso   |   P3   |   P4   |   P5   |
O           | MEDIUM |  LOW   | MINOR  |
            └────────┴────────┴────────┘
```

### Livelli di Escalation

```
┌──────────────────────────────────────────────────────────────────┐
| Livello     | Ruolo                    | Responsabilita'         |
├─────────────┼──────────────────────────┼─────────────────────────┤
| L1          | Service Desk /           | Registrazione, triage,  |
|             | Help Desk                | risoluzione con KB,     |
|             |                          | workaround noti         |
├─────────────┼──────────────────────────┼─────────────────────────┤
| L2          | System Administrator /   | Diagnostica approfondita|
|             | Network Engineer /       | configurazione avanzata,|
|             | DBA                      | analisi log, scripting  |
├─────────────┼──────────────────────────┼─────────────────────────┤
| L3          | Senior Engineer /        | RCA complessa, patch    |
|             | Architect / Specialist   | custom, redesign,       |
|             |                          | interazione con vendor  |
├─────────────┼──────────────────────────┼─────────────────────────┤
| L4          | Vendor / Sviluppatore    | Bug fix nel codice      |
|             | del prodotto             | sorgente, hotfix,       |
|             |                          | supporto dedicato       |
├─────────────┼──────────────────────────┼─────────────────────────┤
| Management  | IT Manager / CTO /      | Decisioni su risorse,   |
| Escalation  | Service Delivery Manager | comunicazione al        |
|             |                          | business, priorita'     |
└──────────────────────────────────────────────────────────────────┘
```

### Procedure di Escalation per Priorita'

**P1 — CRITICAL (Impatto Alto + Urgenza Alta):**

```
Tempo          Azione
─────────────────────────────────────────────────────────
0 min          Alert automatico → Assegnazione L2 immediata
               Notifica: IT Manager, Service Delivery Manager
5 min          Bridge call aperta (war room virtuale)
               Tutti i team rilevanti convocati
15 min         Se nessun progresso → Escalation a L3
               Notifica: CTO/Direttore IT
30 min         Se nessun progresso → Contatto vendor (P1 support)
               Management briefing ogni 30 minuti
60 min         Se nessun progresso → Valutare disaster recovery
               / failover su sistema secondario
               Comunicazione utenti ogni 30 minuti

SLA Target Risoluzione: 4 ore
```

**P2 — HIGH (Impatto Alto + Urgenza Media, o Impatto Medio + Urgenza Alta):**

```
Tempo          Azione
─────────────────────────────────────────────────────────
0 min          Assegnazione L1/L2
15 min         Se L1 non risolve → Escalation a L2
30 min         Se nessun workaround → Notifica IT Manager
1 ora          Se nessun progresso → Escalation a L3
2 ore          Se nessun progresso → Contatto vendor
               Management briefing ogni 2 ore

SLA Target Risoluzione: 8 ore lavorative
```

**P3 — MEDIUM:**

```
Tempo          Azione
─────────────────────────────────────────────────────────
0 min          Assegnazione L1
30 min         Se L1 non risolve → Escalation a L2
4 ore          Se nessun progresso → Notifica al team lead
8 ore          Se nessun progresso → Escalation a L3

SLA Target Risoluzione: 24 ore lavorative
```

**P4/P5 — LOW/MINOR:**

```
Tempo          Azione
─────────────────────────────────────────────────────────
0 min          Assegnazione L1, inserimento in coda
               Risoluzione durante orario lavorativo standard

SLA Target Risoluzione: 5 giorni lavorativi (P4) / 10 giorni (P5)
```

### Escalation Funzionale vs Gerarchica

Esistono due tipi fondamentali di escalation, spesso utilizzati in parallelo:

**Escalation Funzionale (Tecnica):** Il ticket viene passato a un team con competenze piu' specifiche o piu' avanzate. L1 → L2 → L3. E' il tipo piu' comune e segue la catena tecnica. Non implica necessariamente un problema di urgenza, ma di competenza necessaria per la risoluzione.

**Escalation Gerarchica (Management):** Il management viene coinvolto per autorizzare risorse aggiuntive, prendere decisioni sul business impact, approvare interventi straordinari (es. downtime non schedulato), o applicare pressione su vendor/fornitori esterni. L'escalation gerarchica non sostituisce quella funzionale: i tecnici continuano a lavorare sul problema mentre il management gestisce la comunicazione e le decisioni di business.

**Quando attivare l'escalation gerarchica:**
- L'incidente P1 non e' risolto entro il primo SLA checkpoint
- Il costo del downtime supera una soglia predefinita
- E' necessario coinvolgere risorse di altri team o business unit
- Il vendor non risponde con la priorita' adeguata
- L'incidente ha implicazioni legali, di compliance o di reputazione

### Comunicazione durante gli Incidenti

Una comunicazione strutturata durante gli incidenti e' tanto importante quanto la risoluzione tecnica.

**Template di Comunicazione Incidente:**

```
OGGETTO: [STATO] - [Servizio] - [Sintomo breve]
Esempio: [IN CORSO] - Email Aziendale - Impossibile inviare/ricevere

─────────────────────────────────────────────
AGGIORNAMENTO INCIDENTE #INC-2026-0042
Data/Ora: 2026-05-20 15:30 UTC
Stato: IN CORSO / WORKAROUND APPLICATO / RISOLTO

Servizio colpito: [Nome servizio]
Impatto: [Descrizione dell'impatto sugli utenti]
Inizio: [Data/Ora inizio]

Situazione attuale:
[Breve descrizione dello stato corrente dell'indagine]

Azioni in corso:
[Cosa si sta facendo per risolvere]

Workaround disponibile:
[Se esiste, descrivere il workaround che gli utenti possono applicare]

Prossimo aggiornamento: [Data/Ora del prossimo aggiornamento]

Contatto: [Nome e recapito del responsabile dell'incidente]
─────────────────────────────────────────────
```

---

## Knowledge Base Management

### Knowledge-Centered Service (KCS)

Il Knowledge-Centered Service (KCS) e' una metodologia sviluppata dal Consortium for Service Innovation che integra la creazione e la manutenzione della conoscenza direttamente nel processo di risoluzione degli incidenti. Invece di creare articoli di knowledge base come attivita' separata e a posteriori, KCS prevede che la conoscenza venga catturata, strutturata e condivisa nel momento stesso in cui il problema viene risolto.

**I quattro principi KCS:**

1. **Creare conoscenza come sottoprodotto della risoluzione:** Ogni volta che un tecnico risolve un incidente, documenta la soluzione direttamente nella knowledge base. Non e' un'attivita' separata, ma parte integrante del processo di chiusura del ticket
2. **Evolvere la conoscenza basandosi sulla domanda:** Gli articoli vengono aggiornati e migliorati ogni volta che vengono riutilizzati. Se un tecnico riusa un articolo e scopre che manca un passaggio o che la procedura e' cambiata, aggiorna immediatamente l'articolo
3. **Sviluppare una base di conoscenza condivisa:** La conoscenza non appartiene a un singolo tecnico ma all'intero team. Eliminare i "knowledge silos" dove la conoscenza e' nella testa di una persona
4. **Premiare l'apprendimento e la condivisione:** I KPI del team includono la creazione e il riutilizzo degli articoli KB, non solo il numero di ticket chiusi

**Workflow KCS integrato nel troubleshooting:**

```
Incidente ricevuto
    |
    ├─ Cercare nella KB → Articolo trovato?
    |                        |
    |                      SI → Applicare la soluzione
    |                        |    → Funziona?
    |                        |       SI → Chiudi ticket, conferma articolo
    |                        |       NO → Aggiorna articolo con nuove info
    |                        |
    |                      NO → Diagnosticare il problema
    |                             → Risolto?
    |                                SI → Creare nuovo articolo KB
    |                                     → Chiudi ticket
    |                                NO → Escalare
    |                                     → Documenta diagnosi parziale
```

### Struttura degli Articoli

Un articolo di knowledge base efficace segue una struttura standard che lo rende facilmente ricercabile e utilizzabile:

```
═══════════════════════════════════════════════
   KNOWLEDGE BASE ARTICLE — TEMPLATE
═══════════════════════════════════════════════

KB ID:         KB-2026-0385
Titolo:        [Titolo descrittivo del problema/soluzione]
Categoria:     [Rete / Server / Applicazione / Stampa / ...]
Sottocategoria: [Specifica]
Parole chiave: [tag1, tag2, tag3 — per la ricercabilita']
Livello:       L1 / L2 / L3  (chi puo' applicare questa soluzione)

Versione:      3.0
Autore:        [Chi ha creato l'articolo]
Ultimo agg.:   2026-05-15
Revisore:      [Chi ha validato l'articolo]
Scadenza rev.: 2026-11-15 (revisione semestrale)

───────────────────────────────────────────────
SINTOMO
───────────────────────────────────────────────
[Descrizione del sintomo esattamente come lo vede/descrive
l'utente o il sistema di monitoraggio. Includere messaggi di
errore esatti tra virgolette.]

───────────────────────────────────────────────
CAUSA
───────────────────────────────────────────────
[Spiegazione della causa tecnica del problema]

───────────────────────────────────────────────
AMBIENTE APPLICABILE
───────────────────────────────────────────────
- OS: Windows 11 23H2+
- Applicazione: Microsoft Outlook 2021 LTSC / M365
- Rete: VPN GlobalProtect 6.x

───────────────────────────────────────────────
SOLUZIONE
───────────────────────────────────────────────
Passo 1: [Azione precisa con screenshot/comandi]
Passo 2: [Azione successiva]
Passo 3: [Verifica che la soluzione abbia funzionato]

───────────────────────────────────────────────
NOTE E AVVERTENZE
───────────────────────────────────────────────
[Casi particolari, eccezioni, effetti collaterali]

───────────────────────────────────────────────
ARTICOLI CORRELATI
───────────────────────────────────────────────
- KB-2026-0290: [Titolo correlato]
- KB-2026-0312: [Titolo correlato]
═══════════════════════════════════════════════
```

### Ciclo di Vita della Conoscenza

Gli articoli KB non sono statici. Hanno un ciclo di vita che deve essere gestito:

1. **Draft (Bozza):** Articolo appena creato, non ancora validato. Visibile solo all'autore e ai revisori
2. **In Review (In Revisione):** Sottoposto a peer review tecnica per verificare accuratezza e completezza
3. **Published (Pubblicato):** Validato e disponibile per l'uso da parte del Service Desk e degli utenti (se KB self-service)
4. **Flagged (Segnalato):** Un tecnico ha segnalato che l'articolo necessita di aggiornamento (procedura cambiata, nuovo workaround disponibile, soluzione non piu' funzionante)
5. **Retired (Ritirato):** L'articolo non e' piu' applicabile (sistema dismesso, problema risolto permanentemente) ma viene mantenuto in archivio per riferimento storico

**Regole di governance:**
- Revisione obbligatoria ogni 6 mesi per articoli attivi
- Articoli non utilizzati da 12 mesi: valutare il ritiro
- Articoli con feedback negativo (>20% "non utile"): revisione prioritaria
- Metriche di qualita': percentuale di risoluzione al primo contatto con KB

### Metriche della Knowledge Base

Misurare l'efficacia della knowledge base e' essenziale per il miglioramento continuo:

| Metrica | Descrizione | Target |
|---------|-------------|--------|
| KB Coverage | % di incidenti con articolo KB corrispondente | >70% |
| First Call Resolution con KB | % incidenti risolti al primo contatto usando KB | >50% |
| KB Reuse Rate | Media riutilizzi per articolo | >5 |
| KB Accuracy | % feedback positivo ("utile") | >85% |
| KB Freshness | % articoli aggiornati negli ultimi 6 mesi | >80% |
| KB Contribution | Nuovi articoli creati per mese per tecnico | >2 |
| MTTR con KB vs senza KB | Differenza tempo di risoluzione | -40% |

---

## Post-Mortem e Incident Review

### Cultura Blameless

La post-mortem blameless (senza colpevolizzazione) e' un principio fondamentale della cultura SRE (Site Reliability Engineering) adottato da organizzazioni come Google, Netflix e Amazon. Il principio e' semplice ma profondo: in una post-mortem, si analizzano i sistemi, i processi e le condizioni che hanno permesso all'errore di verificarsi, senza cercare un colpevole individuale.

**Perche' blameless funziona:**
- Se le persone temono di essere punite, nascondono gli errori. Errori nascosti = problemi che si ripetono
- La colpa individuale maschera le cause sistemiche: se un tecnico ha applicato una configurazione errata, la domanda non e' "chi ha sbagliato?" ma "perche' il sistema ha permesso che una configurazione errata venisse applicata in produzione senza validazione?"
- Un ambiente psicologicamente sicuro incoraggia la segnalazione proattiva di near-miss (quasi-incidenti) che sono opportunita' di prevenzione

**Regole della cultura blameless:**
1. Le persone coinvolte nell'incidente sono le migliori fonti di informazione, non i sospettati
2. L'obiettivo e' "cosa possiamo migliorare nel sistema" non "chi deve essere punito"
3. Partire dall'assunzione che tutti hanno agito con le migliori intenzioni e con le informazioni disponibili al momento
4. L'errore umano e' l'inizio dell'indagine, non la sua conclusione
5. Documentare apertamente, inclusi i propri errori, e' un atto di coraggio professionale, non di debolezza

### Template Post-Mortem

```
═══════════════════════════════════════════════════════
       POST-MORTEM — INCIDENT REVIEW
═══════════════════════════════════════════════════════

Titolo:          [Titolo descrittivo dell'incidente]
Data Incidente:  [YYYY-MM-DD]
Data Post-Mortem: [YYYY-MM-DD]
Autore:          [Nome]
Partecipanti:    [Lista persone coinvolte nella review]
Severity:        P1 / P2
Durata Impatto:  [HH:MM - da rilevamento a risoluzione]

────────────────────────────────────────────────────
EXECUTIVE SUMMARY
────────────────────────────────────────────────────
[2-3 frasi che riassumono: cosa e' successo, qual e' stato
l'impatto, e come e' stato risolto. Deve essere comprensibile
da un non-tecnico.]

────────────────────────────────────────────────────
IMPATTO
────────────────────────────────────────────────────
- Utenti colpiti: [numero e percentuale]
- Servizi colpiti: [elenco]
- Durata del disservizio: [minuti/ore]
- Revenue impact: [€ stimato se calcolabile]
- SLA violati: [elenco SLA e di quanto]
- Ticket correlati: [INC-xxxx, INC-yyyy]

────────────────────────────────────────────────────
TIMELINE DETTAGLIATA (tutti gli orari in UTC)
────────────────────────────────────────────────────
| Ora     | Evento                                    |
|---------|------------------------------------------|
| 14:00   | Deploy versione 4.2.1 in produzione       |
| 14:15   | Primo alert: latenza API > 5s             |
| 14:18   | L2 inizia investigazione                  |
| 14:25   | Identificato: pool connessioni DB saturo  |
| 14:30   | Rollback a versione 4.2.0 iniziato        |
| 14:35   | Rollback completato                       |
| 14:40   | Metriche tornano nella norma              |
| 14:45   | Incidente dichiarato risolto              |
| 14:50   | Monitoraggio post-fix per 30 min          |
| 15:20   | Servizio confermato stabile               |

────────────────────────────────────────────────────
ROOT CAUSE
────────────────────────────────────────────────────
[Spiegazione tecnica dettagliata della causa radice.
Non fermarsi al "cosa" ma spiegare il "perche'".]

────────────────────────────────────────────────────
FATTORI CONTRIBUENTI
────────────────────────────────────────────────────
- [Fattore 1: es. test di carico non eseguito sul nuovo codice]
- [Fattore 2: es. staging non rappresentativo della produzione]
- [Fattore 3: es. deploy il venerdi' pomeriggio]

────────────────────────────────────────────────────
COSA HA FUNZIONATO BENE
────────────────────────────────────────────────────
- [Es. Alert scattato entro 15 minuti]
- [Es. Rollback eseguito in meno di 10 minuti]
- [Es. Comunicazione al business tempestiva]

────────────────────────────────────────────────────
COSA NON HA FUNZIONATO
────────────────────────────────────────────────────
- [Es. Mancanza di test di carico pre-deploy]
- [Es. Ambiente staging con 1/10 dei dati di produzione]

────────────────────────────────────────────────────
DOVE ABBIAMO AVUTO FORTUNA
────────────────────────────────────────────────────
- [Es. L'ingegnere esperto era online nonostante il venerdi']
- [Es. Il database non si e' corrotto nonostante il pool saturo]

────────────────────────────────────────────────────
ACTION ITEMS
────────────────────────────────────────────────────
| # | Tipo        | Azione                  | Owner  | Scadenza   |
|---|-------------|------------------------|--------|------------|
| 1 | Prevenzione | Aggiungere test carico | DevOps | 2026-06-01 |
| 2 | Rilevamento | Alert su pool conn DB  | Infra  | 2026-05-25 |
| 3 | Processo    | No deploy venerdi' PM  | SDM    | 2026-05-22 |
| 4 | Mitigazione | Staging con dati reali | DBA    | 2026-07-01 |

═══════════════════════════════════════════════════════
```

### Processo di Conduzione

La post-mortem e' una riunione strutturata, non una discussione informale. Un facilitatore guida il processo con regole chiare.

**Tempistiche:**
- Bozza della post-mortem: entro 48-72 ore dall'incidente (mentre i ricordi sono freschi)
- Riunione di review: entro 5-7 giorni lavorativi
- Documento finale con action items: entro 10 giorni
- Follow-up action items: tracciamento settimanale fino a completamento

**Agenda della riunione (60-90 minuti):**

1. **Introduzione e regole (5 min):** Il facilitatore ricorda i principi blameless e le regole di condotta
2. **Timeline review (15 min):** Si percorre la timeline degli eventi. Ogni partecipante aggiunge dettagli dal proprio punto di vista
3. **Root Cause Analysis (20 min):** Discussione tecnica sulla causa radice. Uso dei 5 Whys o Ishikawa collaborativo
4. **Fattori contribuenti (10 min):** Identificazione dei fattori che hanno permesso al problema di verificarsi o ne hanno ritardato la risoluzione
5. **Cosa ha funzionato / Cosa no (10 min):** Analisi delle buone pratiche e delle aree di miglioramento
6. **Action items (15 min):** Definizione delle azioni correttive e preventive con owner e scadenze specifiche
7. **Wrap-up (5 min):** Conferma distribuzione documento, prossimi passi

### Action Item e Follow-Up

Gli action item sono il prodotto piu' importante della post-mortem. Senza action item tracciati e completati, la post-mortem e' un esercizio accademico.

**Categorie di Action Item:**

- **Prevenzione:** Azioni che impediscono il ripetersi del problema (es. configurare rate limiting, aggiungere validazione, implementare IaC)
- **Rilevamento:** Azioni che migliorano la capacita' di rilevare il problema prima che impatti gli utenti (es. nuovi alert, health check, synthetic monitoring)
- **Mitigazione:** Azioni che riducono l'impatto se il problema si ripresenta (es. auto-scaling, circuit breaker, failover automatico)
- **Processo:** Azioni che migliorano i processi operativi (es. change freeze il venerdi', peer review obbligatoria, runbook aggiornati)

**Regole per action item efficaci:**
- Specifici e misurabili (non "migliorare il monitoraggio" ma "aggiungere alert su latenza API > 2s con notifica Slack su #incidents")
- Con owner singolo (una persona responsabile, non "il team")
- Con scadenza realistica
- Tracciati in un sistema condiviso (Jira, ServiceNow, ecc.)
- Revisionati settimanalmente fino a completamento

---

## Flowchart Diagnostici Operativi

I flowchart operativi forniscono ai tecnici di primo e secondo livello un percorso guidato per la diagnosi dei problemi piu' comuni. Non sostituiscono il ragionamento critico, ma assicurano che i fondamentali vengano sempre verificati prima di escalare.

### Flowchart: Utente Non Naviga su Internet

```
[UTENTE NON NAVIGA SU INTERNET]
            |
            v
    Solo questo utente o piu' utenti?
            |
     ┌──────┴──────┐
     |              |
  SINGOLO        MULTIPLI
     |              |
     v              v
  Cavo/WiFi      Switch/Router
  collegato?     funzionante?
     |              |
  NO → Ricollegare  NO → Verificare
     |  cavo/WiFi       alimentazione
  SI |                  e stato
     v
  IP assegnato?
  (ipconfig/ip addr)
     |
  NO → DHCP funziona?
     |    |
     |  NO → Verificare DHCP server,
     |       relay, scope
     |  SI → Rinnovare lease
     |       (ipconfig /renew)
  SI |
     v
  Ping gateway?
     |
  NO → Verificare VLAN,
     |  porta switch, ACL
  SI |
     v
  Ping 8.8.8.8?
     |
  NO → Problema routing/
     |  firewall → Verificare
     |  route table, regole FW
  SI |
     v
  nslookup google.com?
     |
  NO → Problema DNS →
     |  Verificare DNS server,
     |  forwarder, suffisso
  SI |
     v
  Proxy configurato?
     |
  NO → Configurare proxy
     |  (PAC file, WPAD)
  SI |
     v
  Certificato SSL proxy
  attendibile?
     |
  NO → Installare CA root
     |  del proxy
  SI |
     v
  Firewall locale/
  Antivirus blocca?
     |
  SI → Verificare regole,
     |  esclusioni
  NO |
     v
  Escalare a L2/L3
  con tutti i test
  eseguiti documentati
```

### Flowchart: Servizio Applicativo Non Risponde

```
[SERVIZIO APPLICATIVO NON RISPONDE]
            |
            v
    Il server e' raggiungibile?
    (ping <server_ip>)
            |
     ┌──────┴──────┐
     |              |
    NO             SI
     |              |
     v              v
  Problema di    La porta del servizio
  rete/server    e' in ascolto?
  (vedi flowchart  (ss -tlnp / netstat -an)
  rete)            |
              ┌────┴────┐
              |          |
             NO         SI
              |          |
              v          v
         Servizio     Test connessione
         fermo →      sulla porta
         Avviare      (curl / telnet)
         servizio        |
              |     ┌────┴────┐
         Non si     |          |
         avvia?     RIFIUTATA  CONNESSA
              |     |          |
              v     v          v
         Verif.  Firewall   Servizio
         log:    blocca?    risponde
         - errori di        con errore?
           configuraz.        |
         - porta gia'    ┌────┴────┐
           in uso        |          |
         - permessi      SI        NO
         - dipendenze    |          |
           mancanti    Analizzare  Timeout?
                       il codice     |
                       di errore   Verificare:
                       (HTTP 500,  - carico CPU/RAM
                        502, 503)  - connection pool
                                   - backend/DB lento
                                   - deadlock
```

### Flowchart: Performance Degradata del Server

```
[SERVER LENTO / PERFORMANCE DEGRADATA]
            |
            v
    Quale risorsa e' al limite?
    (top/htop, vmstat, iostat)
            |
     ┌──────┼──────┬──────┐
     |      |      |      |
    CPU    RAM   DISCO   RETE
     |      |      |      |
     v      v      v      v
  Quale   free -h  iostat  iperf3/
  processo?       -x      mtr
  (top -o  Swap     |      |
   %CPU)   attivo? await  Packet
     |      |    > 20ms?  loss?
     v      |      |      |
  Legittimo? SI    SI     SI
     |      |      |      |
  SI → Scale v     v      v
  up/out  Quale   SMART   Duplex
          processo? errors? mismatch?
  NO →    (ps aux  Rebuild Saturazione?
  Kill/   --sort=  RAID?   QoS?
  Investigate -%mem)  HDD→SSD?
         |
      Memory
      leak?
      (crescita
       nel tempo)
         |
      SI → Riavvio
      temporaneo +
      segnalazione
      vendor/dev
```

### Flowchart: Problema di Autenticazione

```
[UTENTE NON RIESCE AD AUTENTICARSI]
            |
            v
    Messaggio di errore specifico?
            |
     ┌──────┼──────────────┬───────────────┐
     |      |              |               |
  "Account "Password     "Trust          "Cannot
  locked"   expired"     relationship    contact
     |      |            failed"         domain"
     v      v              |               |
  Verificare Verificare    v               v
  Event ID  scadenza    Test-Computer   Verif. DNS
  4740 sul  in AD:      SecureChannel   per record
  PDC →     net user    -Repair         SRV del DC
  trovare   <user>        |               |
  sorgente  /domain     Non funziona?  nslookup
  del lockout  |        Rimuovere e    -type=srv
     |      Cambiare    riaggiunere    _ldap._tcp.
     v      password    al dominio     dc._msdcs.
  Credenziali  |                       <domain>
  salvate?  Aggiornare                    |
  - Mapped  su tutti i                 Se fallisce:
    drives  dispositivi               verificare
  - Servizi  (mobile, RDP,            configurazione
  - Task     VPN, WiFi)               DNS del client
  - RDP disc.                         e raggiungib.
     |                                del DC
     v
  Rimuovere
  credenziali
  obsolete,
  sbloccare
  account
```

---

## Troubleshooting Moderno: AIOps e Observability

Il panorama del troubleshooting IT sta attraversando una trasformazione profonda guidata dall'adozione di pratiche di observability avanzata, telemetria unificata e intelligenza artificiale applicata alle operazioni (AIOps). Queste tecnologie non sostituiscono le competenze fondamentali di troubleshooting trattate nelle sezioni precedenti, ma le amplificano enormemente, automatizzando la raccolta e la correlazione dei dati e riducendo il tempo tra il rilevamento di un problema e la sua risoluzione.

### OpenTelemetry e Telemetria Unificata

OpenTelemetry (OTel) e' diventato lo standard de facto per la telemetria unificata, supportato dalla Cloud Native Computing Foundation (CNCF) e adottato da tutti i principali vendor di observability. OTel definisce un framework vendor-neutral per la raccolta, l'elaborazione e l'esportazione di tre (e ora quattro) tipi di dati di telemetria:

1. **Traces (Tracce distribuite):** Seguono una singola richiesta attraverso tutti i servizi che attraversa (microservizi, database, cache, code, API esterne). Ogni segmento della richiesta e' uno "span" con timing preciso. Fondamentale per identificare dove il tempo viene speso in un sistema distribuito
2. **Metrics (Metriche):** Misurazioni numeriche aggregate nel tempo: contatori (richieste totali), gauge (utilizzo CPU attuale), istogrammi (distribuzione dei tempi di risposta). Essenziali per dashboard, alert e capacity planning
3. **Logs (Log):** Registrazioni di eventi discreti con timestamp. In OTel, i log sono correlati automaticamente alle tracce, permettendo di passare da un alert a uno span a un log specifico in secondi
4. **Profiles (Profili):** Aggiunto come standard nel 2024, il profiling continuo mostra dove il codice spende CPU e memoria a livello di funzione, permettendo ottimizzazioni mirate senza strumenti di profiling dedicati

**Impatto sul troubleshooting:**

Senza OTel, il troubleshooting di un sistema distribuito richiede di accedere separatamente ai log di ogni servizio, correlare manualmente per timestamp, e ricostruire il flusso della richiesta mentalmente. Con OTel, un singolo trace ID collega tutti i log, le metriche e gli span di una richiesta problematica, riducendo il MTTD (Mean Time To Detect) e l'MTTR (Mean Time To Resolve) in modo significativo.

```bash
# Esempio: ricerca di un trace specifico con traceID
# In un sistema con Jaeger come backend di tracing:
curl "http://jaeger:16686/api/traces/<traceID>"

# In Grafana Tempo:
# Navigare a Explore → Tempo → TraceQL
# { status = error && duration > 5s }

# Correlare log con trace (usando il traceID nel log):
journalctl | grep "traceID=abc123def456"
```

### eBPF per Diagnostica di Rete

eBPF (extended Berkeley Packet Filter) e' una tecnologia rivoluzionaria del kernel Linux che permette di eseguire programmi nel kernel senza modificarlo o caricare moduli kernel custom. Per il troubleshooting IT, eBPF apre possibilita' diagnostiche precedentemente impossibili o estremamente costose in termini di performance.

**Applicazioni di eBPF nel troubleshooting:**

1. **Network diagnostics senza overhead:** Cattura di pacchetti, latenza per connessione, retransmission TCP, tutto senza l'overhead di tcpdump completo
2. **Tracing di sistema operativo:** Monitorare system call, I/O disco, scheduling CPU a livello di processo senza impatto misurabile sulle performance
3. **Security monitoring:** Rilevamento di comportamenti anomali (connessioni in uscita inaspettate, accesso a file sensibili) in tempo reale
4. **Auto-instrumentation:** OpenTelemetry eBPF Instrumentation (OBI) permette di raccogliere tracce distribuite da applicazioni senza modificare il loro codice sorgente

**Strumenti eBPF per troubleshooting:**

```bash
# bpftrace: tracing ad-hoc del kernel
# Monitorare le latenze I/O disco per processo:
bpftrace -e 'tracepoint:block:block_rq_complete {
    @us[comm] = hist((nsecs - @start[tid]) / 1000);
}'

# Monitorare connessioni TCP con dettagli:
bpftrace -e 'kprobe:tcp_connect {
    printf("%s -> %s:%d\n", comm, ntop(arg1), arg2);
}'

# bcc tools (BPF Compiler Collection):
# Latenza DNS:
/usr/share/bcc/tools/gethostlatency

# Connessioni TCP accettate/rifiutate:
/usr/share/bcc/tools/tcpconnect
/usr/share/bcc/tools/tcpaccept

# Latenza I/O per disco:
/usr/share/bcc/tools/biolatency
```

### AIOps: dall'Allarme alla Remediation Automatica

L'AIOps (Artificial Intelligence for IT Operations) rappresenta l'evoluzione piu' significativa del troubleshooting IT nel periodo 2024-2026. Dalla fase iniziale di "chatbot che risponde alle domande", l'AIOps sta maturando verso sistemi che rilevano autonomamente le anomalie, correlano gli eventi, diagnosticano la causa probabile e, in casi definiti, applicano la remediation automatica.

**Livelli di maturita' AIOps:**

1. **Alert Correlation:** Raggruppamento automatico di alert correlati per ridurre il "rumore". Invece di 200 alert separati durante un'interruzione, il sistema identifica che sono tutti correlati allo stesso evento radice e presenta un singolo alert aggregato con contesto
2. **Anomaly Detection:** Modelli di machine learning che apprendono il comportamento normale dell'infrastruttura (baseline dinamica) e rilevano deviazioni significative prima che diventino incidenti. Esempio: "L'utilizzo CPU di questo server e' cresciuto del 15% rispetto al pattern abituale per questo orario del giorno"
3. **Root Cause Inference:** Dato un insieme di anomalie e alert, il sistema suggerisce la causa radice piu' probabile basandosi su modelli di dipendenza dei servizi (service map) e pattern storici. "Con probabilita' dell'87%, la causa dell'incremento di latenza del servizio X e' la saturazione del connection pool verso il database Y"
4. **Automated Remediation:** Per incidenti con causa nota e azione correttiva sicura e idempotente, il sistema applica automaticamente la correzione. Esempio: riavvio automatico di un servizio che ha raggiunto la soglia di memory leak nota, scaling automatico in risposta a picchi di traffico

**Cautele sull'AIOps:**
- L'AIOps non sostituisce la competenza umana: amplifica la capacita' di analisi ma richiede professionisti che comprendano i risultati e intervengano quando l'automazione non e' sufficiente
- I modelli di ML hanno bisogno di dati storici di qualita' e tempo per apprendere i pattern normali
- La remediation automatica deve essere limitata ad azioni sicure e ben testate, con possibilita' di override umano
- Garbage in, garbage out: se la telemetria e' incompleta o i servizi non sono strumentati correttamente, l'AIOps generera' falsi positivi o manchera' problemi reali

### Strumenti di Observability Moderni

La tabella seguente riassume gli strumenti di observability moderni piu' rilevanti per il troubleshooting nel periodo 2025-2026:

| Strumento | Tipo | Funzionalita' Chiave |
|-----------|------|---------------------|
| **Grafana** | Dashboarding/Visualizzazione | Dashboard unificata per metriche, log, tracce. Supporta Prometheus, Loki, Tempo, Mimir |
| **Prometheus** | Metriche (TSDB) | Database time-series per metriche. Pull model, PromQL per query, AlertManager per alert |
| **Grafana Loki** | Log aggregation | Aggregazione log scalabile. Non indicizza il contenuto, solo i label — costo ridotto |
| **Grafana Tempo** | Distributed tracing | Backend per tracce distribuite. Supporta Jaeger, Zipkin, OTel nativamente |
| **Jaeger** | Distributed tracing | Tracing distribuito open-source (CNCF). UI per l'analisi delle tracce |
| **OpenTelemetry Collector** | Pipeline telemetria | Riceve, elabora, esporta telemetria. Vendor-neutral, altamente configurabile |
| **Cilium** | Networking eBPF | Networking e security basati su eBPF per Kubernetes. Hubble per observability di rete |
| **Datadog / Dynatrace / Splunk** | Piattaforme commerciali | Observability full-stack con AIOps integrata, supporto enterprise |

---

## Troubleshooting Avanzato: Scenari Complessi

### Problemi Intermittenti (Heisenbugs)

I problemi intermittenti — quelli che si manifestano in modo non prevedibile e spesso scompaiono quando si tenta di osservarli — sono tra i piu' frustranti nel troubleshooting IT. Il termine "Heisenbug" (dal principio di indeterminazione di Heisenberg) descrive proprio un bug che cambia comportamento o scompare quando si tenta di osservarlo.

**Strategie per i problemi intermittenti:**

1. **Cattura continua:** Poiche' non si sa quando il problema si manifestera', configurare una cattura continua dei dati rilevanti:
   - Network capture rolling: `tcpdump -i eth0 -w /tmp/rolling.pcap -W 10 -C 100` (10 file da 100MB ciascuno, sovrascrittura circolare)
   - Log verbosity aumentata temporaneamente
   - Metriche con granularita' massima (ogni 10 secondi invece di ogni minuto)

2. **Alert di cattura:** Configurare alert che, quando il sintomo si manifesta, attivano automaticamente una cattura dettagliata dei dati. Esempio con un cron job:
   ```bash
   # Script che verifica la latenza e cattura dati se alta
   #!/bin/bash
   LATENCY=$(curl -o /dev/null -s -w "%{time_total}" https://app.interno/health)
   THRESHOLD="2.0"
   if (( $(echo "$LATENCY > $THRESHOLD" | bc -l) )); then
       TIMESTAMP=$(date +%Y%m%d_%H%M%S)
       ss -tnp > /tmp/diag_${TIMESTAMP}_connections.txt
       top -bn1 > /tmp/diag_${TIMESTAMP}_top.txt
       vmstat 1 30 > /tmp/diag_${TIMESTAMP}_vmstat.txt &
       tcpdump -i eth0 -c 10000 -w /tmp/diag_${TIMESTAMP}.pcap &
       echo "$(date) - Latenza alta rilevata: ${LATENCY}s" >> /var/log/latency_alert.log
   fi
   ```

3. **Correlazione temporale:** Quando il problema si manifesta, cercare correlazioni temporali con:
   - Cron job schedulati (backup, rotazione log, pulizia cache)
   - Pattern di traffico utente (ora di punta, batch notturni)
   - Operazioni infrastrutturali (RAID rebuild, replica database, aggiornamenti automatici)
   - Condizioni ambientali (temperatura datacenter, utilizzo UPS)

4. **Statistical debugging:** Raccogliere abbastanza occorrenze per identificare pattern statistici. Dopo 20+ occorrenze, analizzare: c'e' un orario ricorrente? Un giorno della settimana? Un utente/client/endpoint specifico? Un valore di carico correlato?

### Problemi di Performance sotto Carico

I problemi di performance che si manifestano solo sotto carico significativo presentano sfide diagnostiche uniche perche' l'ambiente di test spesso non replica le condizioni reali.

**Strumenti e tecniche:**

```bash
# Generare carico controllato per riprodurre il problema
# Apache Bench (ab): carico HTTP semplice
ab -n 10000 -c 100 https://app.interno/api/search

# wrk: carico HTTP avanzato con scripting Lua
wrk -t12 -c400 -d30s https://app.interno/api/search

# stress-ng: stress test di CPU/memoria/I/O
stress-ng --cpu 4 --io 2 --vm 2 --vm-bytes 1G --timeout 60s

# Durante il carico, monitorare con:
# Terminal 1: metriche sistema
vmstat 1 | tee /tmp/vmstat_under_load.txt

# Terminal 2: I/O
iostat -x 1 | tee /tmp/iostat_under_load.txt

# Terminal 3: connessioni di rete
watch -n1 'ss -s'

# Terminal 4: specifico per il servizio
# PostgreSQL: query attive
watch -n1 "psql -c \"SELECT pid, now()-query_start AS duration, 
  state, query FROM pg_stat_activity WHERE state != 'idle' 
  ORDER BY duration DESC LIMIT 10;\""
```

**Pattern comuni di problemi sotto carico:**

- **Connection pool exhaustion:** Il numero di connessioni al database raggiunge il limite. Sintomo: timeout nelle richieste. Verificare con `SHOW processlist` (MySQL) o `pg_stat_activity` (PostgreSQL)
- **Thread starvation:** Tutti i thread del server sono occupati. Nuove richieste rimangono in coda. Verificare il thread pool del server applicativo (thread dump Java con `jstack <PID>`)
- **Lock contention:** Sotto carico, il locking diventa un collo di bottiglia. Verificare con `SHOW ENGINE INNODB STATUS` (MySQL) o `pg_locks` (PostgreSQL)
- **GC pressure:** Il garbage collector della JVM impiega troppo tempo, causando pause applicative. Verificare con i GC log (`-Xlog:gc*` in Java 11+)

### Troubleshooting in Ambienti Virtualizzati

Gli ambienti virtualizzati (VMware vSphere, Hyper-V, KVM/QEMU, Proxmox) aggiungono un livello di complessita' al troubleshooting perche' le metriche di performance all'interno della VM possono non riflettere la realta' dell'host fisico.

**Problemi specifici della virtualizzazione:**

1. **CPU Ready / CPU Wait:** La VM vuole utilizzare la CPU ma l'hypervisor non gliela assegna perche' le risorse fisiche sono contese. All'interno della VM, la CPU sembra poco utilizzata, ma le performance sono scarse. Verificare con `esxtop` (VMware) o `virt-top` (KVM)
2. **Memory ballooning:** L'hypervisor recupera memoria dalle VM inattive per assegnarla a quelle attive. Se il ballooning e' eccessivo, la VM inizia a swappare. Verificare: `vmware-toolbox-cmd stat balloon` o il balloon driver nel guest
3. **Storage latency dall'hypervisor:** L'I/O storage passa attraverso piu' livelli (guest OS → virtual disk → hypervisor → storage controller → SAN/NAS). La latenza misurata nel guest puo' essere significativamente diversa da quella misurata sull'host
4. **Network latency virtuale:** Il virtual switch e l'hypervisor aggiungono microseconddi di latenza. In contesti ad alta frequenza (database, trading), questo puo' essere significativo. Soluzioni: SR-IOV per bypassare il virtual switch, DPDK per applicazioni ad alte performance

```powershell
# VMware: comandi utili per troubleshooting
# esxtop sul host ESXi (console diretta o SSH):
esxtop
# Premere 'c' per CPU: controllare %RDY (Ready) < 5%
# Premere 'm' per Memory: controllare MCTLSZ (balloon) e SWCUR (swap)
# Premere 'd' per Disk: controllare DAVG (device latency) e KAVG (kernel latency)
# Premere 'n' per Network: controllare %DRPTX/%DRPRX (pacchetti persi)
```

### Troubleshooting DNS Avanzato

Il DNS e' coinvolto in una percentuale sorprendentemente alta di problemi IT. Un troubleshooting DNS superficiale puo' portare a conclusioni errate. Questa sezione copre scenari avanzati che vanno oltre il semplice `nslookup`.

**Scenari avanzati:**

```bash
# 1. Verificare la propagazione DNS (confrontare piu' server)
for dns in 8.8.8.8 1.1.1.1 9.9.9.9 208.67.222.222; do
    echo "=== DNS: $dns ==="
    dig @$dns app.example.com +short
done

# 2. Verificare la catena DNSSEC
dig +dnssec +multi app.example.com

# 3. Verificare il TTL residuo (per capire quando la cache scadra')
dig app.example.com | grep -E "^app" | awk '{print "TTL residuo: "$2" secondi"}'

# 4. Tracciare la risoluzione completa dalla root
dig +trace app.example.com

# 5. Reverse DNS (PTR) — fondamentale per email e sicurezza
dig -x 93.184.216.34

# 6. Verificare tutti i record di un dominio
dig app.example.com ANY

# 7. Verificare record CAA (Certificate Authority Authorization)
dig CAA example.com

# 8. Test di zona transfer (per verificare se e' bloccato correttamente)
dig AXFR example.com @ns1.example.com
# Questo DEVE fallire da fonti non autorizzate (sicurezza)

# 9. Misurare tempo di risoluzione DNS ripetuto (cache test)
for i in $(seq 1 5); do
    dig app.example.com | grep "Query time"
done
# La prima query sara' piu' lenta (miss), le successive piu' veloci (cache hit)
```

**Problemi DNS avanzati e soluzioni:**

- **DNS Rebinding:** Un attaccante usa un record DNS con TTL molto basso che alterna tra un IP esterno e un IP interno, potenzialmente bypassando controlli di sicurezza
- **DNS Amplification Attack:** Query DNS con IP sorgente spoofato che generano risposte amplificate verso il target. Mitigazione: response rate limiting (RRL) sul server DNS, disabilitare ricorsione per client esterni
- **Split-Horizon DNS Mismatch:** Il DNS interno e quello esterno risolvono lo stesso hostname a IP diversi. Problemi quando un client interno usa accidentalmente il DNS esterno (es. DNS over HTTPS che bypassa il DNS aziendale)
- **Stale DNS records dopo migrazione:** Dopo una migrazione di servizi, i vecchi record DNS con TTL alto continuano a indirizzare i client al vecchio server. Soluzione: ridurre il TTL a 300 secondi almeno 24 ore prima della migrazione, poi ripristinarlo dopo la verifica

---

## Esercizi
1. **Lab — OSI binary search.** Problema rete; trova layer in 3 step.
2. **Stretch — RCA documentation template.** Standardizza per la tua org.
3. **Lab — 5 Whys su incidente simulato.** Dato un incidente (server web irraggiungibile), percorri la catena dei 5 Whys fino alla causa radice organizzativa.
4. **Lab — Diagramma Ishikawa.** Per un problema "VPN lenta per gli utenti remoti", costruisci un diagramma fishbone completo con almeno 5 categorie e 3 cause per categoria.
5. **Lab — Matrice IS/IS NOT (Kepner-Tregoe).** Per un problema "applicazione CRM non funziona solo da un ufficio", compila la matrice IS/IS NOT e formula un'ipotesi basata sulle distinzioni.
6. **Lab — Post-Mortem blameless.** Dato lo scenario di un deploy fallito che ha causato 45 minuti di downtime, compila il template di post-mortem completo con timeline, RCA, fattori contribuenti e action items.
7. **Lab — Flowchart diagnostico custom.** Crea un flowchart diagnostico per uno scenario specifico della tua organizzazione (es. "stampante di rete non stampa") con almeno 8 decision point.

## Auto-valutazione
1. OSI layer: ordine.
2. Binary search: come applicare.
3. Cognitive bias in troubleshooting: 2 esempi.
4. Qual e' la differenza tra Incident Management e Problem Management in ITIL?
5. Spiega quando useresti i 5 Whys vs il diagramma di Ishikawa vs Kepner-Tregoe.
6. Cosa significa "blameless" in una post-mortem e perche' e' importante?
7. Descrivi i quattro segnali di telemetria di OpenTelemetry e il loro ruolo nel troubleshooting.
8. Qual e' la differenza tra escalation funzionale e gerarchica?
9. Cosa include un record del Known Error Database (KEDB)?
10. Come si calcula la priorita' di un incidente usando la matrice impatto-urgenza?

## Glossario locale
| Termine | Definizione |
|---|---|
| **OSI model** | 7-layer network model. |
| **Binary search** | Tecnica isolamento. |
| **RCA** | Root Cause Analysis — analisi sistematica per identificare la vera causa di un problema. |
| **5 Whys** | Tecnica di indagine iterativa: chiedere "Perche'?" ripetutamente per risalire alla causa radice. |
| **Ishikawa (Fishbone)** | Diagramma causa-effetto a forma di lisca di pesce per esplorare le cause organizzate per categorie. |
| **FTA** | Fault Tree Analysis — analisi deduttiva top-down con logica booleana (AND/OR gates). |
| **Kepner-Tregoe** | Metodo strutturato di problem analysis basato sulla matrice IS/IS NOT. |
| **Pareto (80/20)** | Principio per cui ~80% degli effetti deriva dal ~20% delle cause. |
| **ITIL** | Information Technology Infrastructure Library — framework per la gestione dei servizi IT. |
| **Problem Management** | Processo ITIL dedicato all'identificazione e alla risoluzione delle cause radice degli incidenti. |
| **KEDB** | Known Error Database — database degli errori noti con workaround e soluzioni. |
| **Workaround** | Soluzione temporanea che mitiga l'impatto senza risolvere la causa radice. |
| **KCS** | Knowledge-Centered Service — metodologia per integrare la gestione della conoscenza nel troubleshooting. |
| **Post-Mortem** | Analisi strutturata post-incidente per identificare cause e azioni preventive. |
| **Blameless** | Approccio alla post-mortem che analizza i sistemi senza colpevolizzare le persone. |
| **MTTD** | Mean Time To Detect — tempo medio dal verificarsi del problema al suo rilevamento. |
| **MTTR** | Mean Time To Resolve — tempo medio dal rilevamento alla risoluzione completa. |
| **OpenTelemetry** | Standard CNCF per la raccolta unificata di tracce, metriche, log e profili. |
| **eBPF** | Extended Berkeley Packet Filter — tecnologia kernel Linux per diagnostica ad alte prestazioni. |
| **AIOps** | Artificial Intelligence for IT Operations — applicazione di ML/AI alla gestione dell'infrastruttura IT. |
| **SRE** | Site Reliability Engineering — disciplina ingegneristica per la gestione dell'affidabilita' dei servizi. |
| **P1-P5** | Livelli di priorita' degli incidenti, da Critical (P1) a Minor (P5). |
| **Escalation funzionale** | Passaggio del ticket a un team con competenze tecniche piu' avanzate (L1→L2→L3). |
| **Escalation gerarchica** | Coinvolgimento del management per decisioni, risorse o pressione su terze parti. |
| **Heisenbug** | Bug intermittente che cambia comportamento quando si tenta di osservarlo. |
