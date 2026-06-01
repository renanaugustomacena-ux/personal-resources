# Sicurezza Operativa — Guida Completa

> **Modulo 05** · **Tempo:** 90 min · **Aggiornamento:** 2026-04-27

## Idee guida

1. **Defense in depth: 5+ layer.** Fail di un layer non e fail totale.
2. **Vulnerability management: scan + patch + verify, ciclo continuo.**
3. **Least privilege everywhere.** Service account, user account, container, network.
4. **Audit log + SIEM correlation = visibilita reale.**


## Indice

1. [Panoramica](#panoramica)
2. [Sicurezza Endpoint](#sicurezza-endpoint)
   - [Antivirus/EDR Management](#antivirusedr-management)
   - [Endpoint Hardening](#endpoint-hardening)
   - [Vulnerability Management](#vulnerability-management)
3. [Sicurezza Rete e Firewall](#sicurezza-rete-e-firewall)
   - [Firewall Rule Management](#firewall-rule-management)
   - [IDS/IPS Management](#idsips-management)
   - [Network Segmentation](#network-segmentation)
   - [WAF (Web Application Firewall)](#waf-web-application-firewall)
   - [Network Monitoring](#network-monitoring)
4. [Gestione Certificati](#gestione-certificati)
   - [PKI Maintenance](#pki-maintenance)
   - [SSL/TLS Certificate Management](#ssltls-certificate-management)
   - [Certificate Automation](#certificate-automation)
5. [Audit e Compliance](#audit-e-compliance)
   - [Security Audit Program](#security-audit-program)
   - [Log Audit](#log-audit)
   - [Compliance Frameworks](#compliance-frameworks)
   - [Access Audit](#access-audit)
6. [Gestione Accessi](#gestione-accessi)
   - [Privileged Access Management (PAM)](#privileged-access-management-pam)
   - [RBAC Implementation](#rbac-implementation)
   - [Identity Lifecycle](#identity-lifecycle)
7. [Security Operations Center (SOC)](#security-operations-center-soc)
   - [Architettura e Modelli SOC](#architettura-e-modelli-soc)
   - [Processi Operativi del SOC](#processi-operativi-del-soc)
   - [Metriche e KPI del SOC](#metriche-e-kpi-del-soc)
   - [Strumenti e Tecnologie SOC](#strumenti-e-tecnologie-soc)
8. [SIEM — Configurazione Avanzata e Gestione Log](#siem--configurazione-avanzata-e-gestione-log)
   - [Architettura SIEM e Raccolta Log](#architettura-siem-e-raccolta-log)
   - [Normalizzazione e Parsing dei Log](#normalizzazione-e-parsing-dei-log)
   - [Regole di Rilevamento e Casi d'Uso](#regole-di-rilevamento-e-casi-duso)
   - [Gestione del Volume e Retention Avanzata](#gestione-del-volume-e-retention-avanzata)
9. [Threat Hunting e Risposta agli Incidenti](#threat-hunting-e-risposta-agli-incidenti)
   - [Programma di Threat Hunting](#programma-di-threat-hunting)
   - [Piano di Risposta agli Incidenti (IRP)](#piano-di-risposta-agli-incidenti-irp)
   - [SOAR — Automazione della Risposta](#soar--automazione-della-risposta)
10. [Sicurezza Fisica e Ambientale](#sicurezza-fisica-e-ambientale)
    - [Controllo Accessi Fisici](#controllo-accessi-fisici)
    - [Protezione Data Center e Locali Tecnici](#protezione-data-center-e-locali-tecnici)
    - [Integrazione Sicurezza Fisica e Logica](#integrazione-sicurezza-fisica-e-logica)
11. [Formazione e Consapevolezza sulla Sicurezza](#formazione-e-consapevolezza-sulla-sicurezza)
    - [Programma di Security Awareness](#programma-di-security-awareness)
    - [Simulazioni di Phishing](#simulazioni-di-phishing)
    - [Formazione Specifica per Ruolo](#formazione-specifica-per-ruolo)
12. [Patch Management Operativo](#patch-management-operativo)
    - [Ciclo di Vita del Patch](#ciclo-di-vita-del-patch)
    - [Automazione del Patching](#automazione-del-patching)
    - [Gestione delle Eccezioni e Rollback](#gestione-delle-eccezioni-e-rollback)
13. [Controllo Accessi Avanzato — ABAC e Zero Trust](#controllo-accessi-avanzato--abac-e-zero-trust)
    - [Attribute-Based Access Control (ABAC)](#attribute-based-access-control-abac)
    - [Implementazione Zero Trust](#implementazione-zero-trust)
    - [Matrice di Controllo Accessi](#matrice-di-controllo-accessi)
14. [Best Practices](#best-practices)
15. [Troubleshooting](#troubleshooting)

---

## Panoramica

La sicurezza operativa rappresenta l'insieme di pratiche, processi e tecnologie che garantiscono la protezione continua dell'infrastruttura IT durante le normali operazioni di manutenzione e gestione quotidiana. A differenza della progettazione iniziale della sicurezza (security by design), la sicurezza operativa si concentra sul mantenimento, il monitoraggio e il miglioramento costante della postura di sicurezza nel tempo.

Un concetto fondamentale da interiorizzare fin dall'inizio: **la sicurezza non e' un traguardo, ma un processo continuo**. Non esiste un momento in cui un sistema possa essere dichiarato "sicuro" in modo definitivo. Le minacce evolvono, le vulnerabilita' vengono scoperte, le configurazioni derivano nel tempo (configuration drift) e il personale cambia. Il compito del team di manutenzione IT e' mantenere un livello di sicurezza adeguato al rischio accettabile definito dall'organizzazione, reagendo tempestivamente alle nuove minacce e verificando costantemente l'efficacia delle contromisure in atto.

La sicurezza operativa nel contesto della manutenzione IT comprende cinque pilastri fondamentali:

- **Sicurezza Endpoint**: protezione dei dispositivi finali (workstation, server, dispositivi mobili) attraverso soluzioni antivirus/EDR, hardening e gestione delle vulnerabilita'.
- **Sicurezza Rete e Firewall**: controllo del traffico di rete, segmentazione, rilevamento delle intrusioni e protezione delle applicazioni web.
- **Gestione Certificati**: manutenzione dell'infrastruttura PKI, gestione del ciclo di vita dei certificati SSL/TLS e automazione dei rinnovi.
- **Audit e Compliance**: verifiche periodiche di sicurezza, analisi dei log, conformita' ai framework normativi e audit degli accessi.
- **Gestione Accessi**: implementazione del principio del minimo privilegio, gestione degli accessi privilegiati e controllo del ciclo di vita delle identita'.

Ogni pilastro richiede attenzione costante, procedure documentate e strumenti adeguati. Questa guida fornisce indicazioni operative dettagliate per ciascuna area, con riferimenti a strumenti specifici, checklist pratiche e procedure di troubleshooting.

Il modello di riferimento per la sicurezza operativa si basa sul ciclo **Identify - Protect - Detect - Respond - Recover** del NIST Cybersecurity Framework, applicato in modo continuo e iterativo alle attivita' di manutenzione ordinaria.

---

## Sicurezza Endpoint

La protezione degli endpoint rappresenta la prima linea di difesa dell'infrastruttura IT. Ogni dispositivo collegato alla rete aziendale e' un potenziale punto di ingresso per un attaccante. La gestione efficace della sicurezza endpoint richiede un approccio multilivello che combina rilevamento delle minacce, hardening del sistema operativo e gestione proattiva delle vulnerabilita'.

### Antivirus/EDR Management

Le soluzioni EDR (Endpoint Detection and Response) hanno sostituito i tradizionali antivirus basati esclusivamente su firme, offrendo capacita' di rilevamento comportamentale, analisi forense e risposta automatica agli incidenti. La gestione efficace di questi strumenti richiede attenzione continua.

**Configurazione e tuning delle policy**

La configurazione delle policy EDR deve bilanciare il livello di protezione con l'impatto sulle prestazioni e sull'operativita' degli utenti. Le policy vanno definite per gruppi logici di dispositivi:

- **Server di produzione**: protezione massima con esclusioni mirate per le applicazioni critiche. Scansioni pianificate in orari di basso carico. Risposta automatica limitata per evitare interruzioni di servizio non pianificate.
- **Workstation standard**: protezione completa con risposta automatica aggressiva. Scansioni in tempo reale abilitate. Blocco automatico dei file sospetti.
- **Workstation sviluppatori**: protezione completa con esclusioni specifiche per IDE, compilatori e ambienti di sviluppo. Le esclusioni devono essere approvate dal team di sicurezza.
- **Dispositivi mobili/laptop**: protezione completa con policy di cifratura del disco obbligatoria. Verifica dello stato di sicurezza al momento della connessione VPN.

**Gestione aggiornamento firme e definizioni**

Gli aggiornamenti delle definizioni devono seguire un flusso controllato:

1. Il server di gestione centrale scarica gli aggiornamenti dal vendor (verificare l'integrita' tramite hash/firma digitale).
2. Gli aggiornamenti vengono distribuiti a un gruppo pilota (5-10% degli endpoint) per 4-6 ore di osservazione.
3. In assenza di problemi, distribuzione graduale al resto dell'infrastruttura.
4. Monitoraggio degli endpoint che non ricevono aggiornamenti entro 24 ore — generare alert per agenti non aggiornati.
5. Frequenza raccomandata: almeno ogni 4 ore per le firme, aggiornamenti del motore secondo le indicazioni del vendor.

**Gestione delle esclusioni**

Le esclusioni rappresentano un rischio significativo se non gestite correttamente. Ogni esclusione riduce la superficie di protezione e puo' essere sfruttata da un attaccante. Procedura raccomandata:

- Ogni richiesta di esclusione deve essere documentata con: giustificazione tecnica, percorso o processo escluso, richiedente, data di approvazione, data di revisione prevista.
- Le esclusioni devono essere approvate dal responsabile della sicurezza, non dal solo team di operations.
- Revisione trimestrale di tutte le esclusioni attive: verificare che siano ancora necessarie, che il software che le ha richieste sia ancora installato e che non esistano alternative meno invasive.
- Mai escludere intere unita' disco o directory di primo livello (es. `C:\` o `/var`).
- Preferire esclusioni per processo anziche' per percorso quando possibile: questo limita l'esclusione al solo processo legittimo.

**Workflow di triage degli alert**

Un sistema EDR ben configurato genera comunque un volume significativo di alert. Il triage efficiente e' essenziale:

1. **Alert automatici ad alta severita'** (malware confermato, ransomware detection, lateral movement): risposta immediata, isolamento automatico dell'endpoint se configurato, escalation al SOC o al responsabile sicurezza.
2. **Alert a media severita'** (comportamento sospetto, PUP detection, policy violation): analisi entro 4 ore lavorative, verifica del contesto (utente, applicazione, orario), decisione: falso positivo, vero positivo da gestire, o richiesta di ulteriori informazioni.
3. **Alert a bassa severita'** (informazionali, adware, scansione completata con rilevamenti minori): analisi entro 24 ore, aggregazione per identificare pattern.
4. Documentare ogni alert analizzato con la decisione presa e la motivazione. Questo storico e' prezioso per il tuning successivo e per le attivita' di audit.

**Monitoraggio del tasso di rilevamento e salute degli agenti**

Metriche chiave da monitorare con cadenza settimanale:

- Percentuale di endpoint con agente attivo e aggiornato (obiettivo: >99%).
- Numero di endpoint con definizioni obsolete (>48 ore).
- Tempo medio di rilevamento (Mean Time to Detect).
- Tasso di falsi positivi (obiettivo: riduzione progressiva tramite tuning).
- Numero di endpoint isolati o in stato di quarantena.
- Stato di salute dell'agente: verificare che il servizio sia in esecuzione, che comunichi con la console centrale e che la versione del motore sia supportata.

**Strumenti di riferimento**: Microsoft Defender for Endpoint (integrato in Windows, ottimo rapporto costo-funzionalita' per ambienti Microsoft), CrowdStrike Falcon (leader di mercato per capacita' di rilevamento), SentinelOne (forte sull'automazione della risposta), Sophos Intercept X (buon bilanciamento tra funzionalita' e semplicita' di gestione), ESET PROTECT (leggero sulle risorse, adatto a endpoint con hardware limitato).

### Endpoint Hardening

L'hardening consiste nel ridurre la superficie di attacco di un sistema operativo rimuovendo funzionalita' non necessarie, configurando in modo restrittivo i servizi e applicando best practice di sicurezza riconosciute.

**Applicazione dei CIS Benchmarks**

I CIS (Center for Internet Security) Benchmarks forniscono guide dettagliate e testate per l'hardening di sistemi operativi e applicazioni. L'applicazione avviene in fasi:

1. **Selezione del profilo**: CIS offre due livelli — Level 1 (raccomandato per tutti i sistemi, impatto minimo sull'operativita') e Level 2 (sicurezza avanzata, potenziale impatto sulla funzionalita'). Per i server di produzione in ambienti sensibili, applicare Level 2 dopo test approfonditi. Per le workstation, Level 1 e' generalmente sufficiente.
2. **Assessment iniziale**: utilizzare CIS-CAT Pro o strumenti equivalenti per valutare lo stato attuale rispetto al benchmark. Documentare il punteggio iniziale.
3. **Pianificazione della remediation**: raggruppare le raccomandazioni per impatto e complessita'. Applicare prima quelle ad alto impatto e bassa complessita'.
4. **Applicazione tramite GPO/Configuration Management**: automatizzare l'applicazione attraverso Group Policy (Windows) o strumenti come Ansible/Puppet (Linux). Mai applicare manualmente le configurazioni su singoli sistemi.
5. **Verifica post-applicazione**: ripetere l'assessment e documentare il punteggio raggiunto. Obiettivo minimo: 85% di conformita' per Level 1.
6. **Revisione periodica**: ri-eseguire l'assessment trimestralmente e dopo ogni major update del sistema operativo.

**Checklist di hardening per Windows**

- Disabilitare SMBv1 (`Disable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol`).
- Configurare Windows Firewall con policy di default deny in ingresso.
- Abilitare Credential Guard e Device Guard su hardware compatibile.
- Disabilitare l'esecuzione di script PowerShell non firmati (`Set-ExecutionPolicy AllSigned`).
- Abilitare l'audit avanzato (logon events, privilege use, object access).
- Disabilitare account Guest e rinominare l'account Administrator locale.
- Configurare la policy di complessita' password (minimo 14 caratteri, complessita' abilitata).
- Abilitare il blocco account dopo 5 tentativi falliti (lockout duration: 30 minuti).
- Rimuovere funzionalita' non necessarie tramite Server Manager (per i server) o DISM (per le workstation).
- Disabilitare i protocolli di rete obsoleti (NetBIOS, LLMNR).
- Configurare LAPS (Local Administrator Password Solution) per la gestione delle password degli amministratori locali.

**Checklist di hardening per Linux**

- Configurare `iptables`/`nftables` con policy di default DROP in INPUT e FORWARD.
- Disabilitare l'accesso root via SSH (`PermitRootLogin no` in `/etc/ssh/sshd_config`).
- Implementare autenticazione SSH tramite chiave pubblica, disabilitare l'autenticazione password.
- Configurare `fail2ban` per la protezione da brute force.
- Rimuovere i pacchetti non necessari (`apt autoremove` o `yum autoremove`).
- Verificare i permessi SUID/SGID e rimuovere quelli non necessari (`find / -perm -4000 -type f`).
- Configurare `auditd` per il monitoraggio degli eventi di sicurezza.
- Abilitare SELinux (Red Hat/CentOS) o AppArmor (Debian/Ubuntu) in modalita' enforcing.
- Configurare i mount point con opzioni restrittive (`noexec`, `nosuid`, `nodev` per `/tmp`, `/var/tmp`).
- Impostare `umask 027` come default.
- Disabilitare i core dump (`* hard core 0` in `/etc/security/limits.conf`).

**Application Whitelisting**

Il whitelisting delle applicazioni impedisce l'esecuzione di software non autorizzato. Su Windows:

- **AppLocker**: disponibile nelle edizioni Enterprise/Education. Configurare regole basate su publisher (firma digitale), percorso e hash del file. Iniziare in modalita' Audit Only per raccogliere dati sulle applicazioni in uso, poi passare gradualmente a Enforce.
- **WDAC (Windows Defender Application Control)**: piu' robusto di AppLocker, opera a livello kernel. Richiede pianificazione accurata ma offre protezione superiore. Utilizzare il Wizard WDAC per generare le policy iniziali basate su scansione dei sistemi di riferimento.

**Controllo USB/supporti rimovibili**

- Disabilitare l'autorun/autoplay su tutti i sistemi.
- Per ambienti ad alta sicurezza, bloccare completamente l'accesso ai dispositivi di archiviazione USB tramite GPO o soluzione EDR.
- Per ambienti che richiedono l'uso di USB, implementare una soluzione di Device Control che consenta solo dispositivi autorizzati (basata su VID/PID o certificato).
- Registrare tutti gli eventi di connessione USB nei log di sicurezza.

**Cifratura disco**

- **Windows**: BitLocker con TPM + PIN. Configurare tramite GPO la policy di cifratura obbligatoria. Archiviare le chiavi di ripristino in Active Directory o in un vault sicuro. Verificare periodicamente lo stato di cifratura con `manage-bde -status`.
- **Linux**: LUKS (Linux Unified Key Setup) per la cifratura completa del disco. Configurare durante l'installazione del sistema. Per i server, valutare la cifratura selettiva delle sole partizioni contenenti dati sensibili per semplificare la gestione dei riavvii automatici. Conservare le chiavi di ripristino in un sistema di gestione segreti (es. HashiCorp Vault).

**Firewall locale**

Ogni endpoint deve avere un firewall locale attivo, indipendentemente dalla protezione perimetrale di rete:

- Windows: Windows Defender Firewall con profili Domain, Private e Public configurati separatamente. Default deny in ingresso, allow in uscita con eccezioni documentate.
- Linux: `nftables` (o `iptables` per compatibilita') con regole specifiche per i servizi in ascolto. Utilizzare configuration management per garantire coerenza tra i server.

### Vulnerability Management

La gestione delle vulnerabilita' e' il processo sistematico di identificazione, classificazione, prioritizzazione e remediation delle debolezze di sicurezza nei sistemi informatici.

**Pianificazione delle scansioni**

Le scansioni di vulnerabilita' devono seguire una pianificazione strutturata:

- **Scansione settimanale**: tutti i sistemi esposti a Internet (DMZ, server web, mail server) e i sistemi critici interni.
- **Scansione mensile**: tutti i sistemi interni, workstation comprese.
- **Scansione on-demand**: dopo l'installazione di nuovi sistemi, dopo modifiche significative alla configurazione, dopo la pubblicazione di vulnerabilita' critiche (es. Log4Shell, PrintNightmare).
- **Scansione autenticata vs non autenticata**: le scansioni autenticate (con credenziali del sistema target) rilevano significativamente piu' vulnerabilita' rispetto a quelle non autenticate. Utilizzare sempre scansioni autenticate per i sistemi interni. Le credenziali di scansione devono essere account di servizio dedicati con permessi di sola lettura.

**Strumenti di riferimento**: Tenable Nessus (standard de facto per ambienti enterprise, ampio database di plugin), OpenVAS/Greenbone (alternativa open source valida, richiede maggiore manutenzione), Qualys VMDR (soluzione cloud con capacita' avanzate di prioritizzazione).

**Scoring CVSS e prioritizzazione**

Il CVSS (Common Vulnerability Scoring System) fornisce un punteggio da 0 a 10 per ogni vulnerabilita', ma il punteggio CVSS da solo non e' sufficiente per la prioritizzazione. Fattori aggiuntivi da considerare:

- **Esposizione del sistema**: un sistema esposto a Internet con una vulnerabilita' CVSS 7.0 puo' avere priorita' maggiore di un sistema interno con CVSS 9.0.
- **Disponibilita' di exploit pubblici**: verificare su Exploit-DB, Metasploit e fonti OSINT se esistono exploit funzionanti. Le vulnerabilita' con exploit pubblici hanno priorita' elevata indipendentemente dal CVSS.
- **Criticita' del sistema per il business**: un database contenente dati dei clienti ha priorita' superiore a un server di test interno.
- **Possibilita' di mitigazione temporanea**: se esiste un workaround efficace (es. disabilitazione di una funzionalita'), la priorita' di patching puo' essere ridotta temporaneamente.

**SLA di remediation per severita'**

| Severita' CVSS | Classificazione | SLA Remediation | Note |
|----------------|-----------------|-----------------|------|
| 9.0 - 10.0 | Critica | 72 ore (3 giorni) | Patching immediato o mitigazione entro 24 ore |
| 7.0 - 8.9 | Alta | 7 giorni | Pianificazione nel prossimo ciclo di patching |
| 4.0 - 6.9 | Media | 30 giorni | Inclusione nella manutenzione ordinaria |
| 0.1 - 3.9 | Bassa | 90 giorni | Remediation quando conveniente |

Questi SLA devono essere adattati al contesto dell'organizzazione e approvati dal management. Le deviazioni devono essere documentate tramite il processo di accettazione del rischio.

**Processo di accettazione del rischio**

Quando una vulnerabilita' non puo' essere corretta entro lo SLA previsto (es. sistema legacy, dipendenza da vendor, incompatibilita' dell'aggiornamento), il rischio residuo deve essere formalmente accettato:

1. Il responsabile tecnico documenta la vulnerabilita', il motivo per cui non puo' essere corretta e le contromisure compensative in atto (es. segmentazione di rete, monitoraggio aggiuntivo).
2. Il risk owner (tipicamente il responsabile del processo di business) firma l'accettazione del rischio.
3. L'accettazione ha una scadenza (massimo 6 mesi) dopo la quale deve essere rivalutata.
4. Le accettazioni di rischio attive vengono revisionate trimestralmente dal CISO o dal responsabile della sicurezza.

**Template del rapporto vulnerabilita'**

Ogni ciclo di scansione deve produrre un rapporto strutturato contenente:

- Data della scansione, ambito (sistemi scansionati), tipo di scansione (autenticata/non autenticata).
- Riepilogo esecutivo: numero totale di vulnerabilita' per severita', trend rispetto alla scansione precedente, sistemi piu' vulnerabili.
- Dettaglio delle vulnerabilita' critiche e alte: CVE, descrizione, sistemi interessati, remediation raccomandata, SLA.
- Stato delle vulnerabilita' precedenti: risolte, in corso di remediation, accettazione rischio attiva.
- Metriche: tempo medio di remediation, percentuale di vulnerabilita' risolte entro lo SLA, numero di accettazioni di rischio attive.

---

## Sicurezza Rete e Firewall

La sicurezza di rete costituisce il secondo livello di difesa dell'infrastruttura IT. Un approccio defense-in-depth richiede che la protezione non dipenda da un singolo punto di controllo, ma da una serie di barriere sovrapposte che un attaccante deve superare.

### Firewall Rule Management

Le regole del firewall sono la base della sicurezza di rete, ma senza manutenzione attiva tendono ad accumulare complessita' e configurazioni obsolete che indeboliscono la postura di sicurezza.

**Metodologia di audit delle regole (revisione trimestrale)**

L'audit trimestrale delle regole firewall segue un processo strutturato:

1. **Esportazione del ruleset completo**: esportare tutte le regole in un formato analizzabile (CSV o XML). Includere: numero regola, sorgente, destinazione, porta/protocollo, azione, hit count, data ultima modifica, commento/giustificazione.
2. **Analisi delle regole inutilizzate**: identificare le regole con hit count zero negli ultimi 90 giorni. Verificare con i proprietari dei servizi se sono ancora necessarie. Le regole stagionali (es. processi di fine anno) devono essere documentate come tali.
3. **Verifica delle regole troppo permissive**: cercare regole con "any" nella sorgente, destinazione o servizio. Ogni regola "any" deve essere giustificata o sostituita con regole specifiche.
4. **Rilevamento delle regole duplicate o in conflitto**: due regole che coprono lo stesso traffico creano confusione e possono mascherare problemi. Rimuovere i duplicati e risolvere i conflitti.
5. **Verifica delle regole shadow**: una regola "shadow" e' una regola che non viene mai valutata perche' una regola precedente cattura gia' tutto il traffico corrispondente. Identificare e rimuovere queste regole per migliorare le prestazioni e la leggibilita'.
6. **Documentazione dei risultati**: produrre un report con le azioni raccomandate (rimozione, modifica, conferma) per ogni regola anomala individuata.

**Requisiti di documentazione delle regole**

Ogni regola firewall deve avere un commento strutturato che includa:

- Identificativo della richiesta di change (ticket number).
- Data di creazione.
- Proprietario del servizio/applicazione.
- Giustificazione di business.
- Data di scadenza prevista (per regole temporanee).
- Riferimento al diagramma di flusso di rete, se disponibile.

Le regole prive di documentazione rilevate durante l'audit devono essere investigate e documentate o rimosse.

**Ottimizzazione dell'ordinamento delle regole**

L'ordine delle regole influisce sia sulle prestazioni che sulla sicurezza:

- Le regole di deny esplicite per traffico noto malevolo (blocklist) dovrebbero essere posizionate in alto.
- Le regole piu' frequentemente matchate (hit count elevato) dovrebbero essere posizionate prima delle regole meno utilizzate per migliorare le prestazioni.
- Le regole di log dovrebbero essere posizionate strategicamente per catturare il traffico di interesse senza impatto eccessivo sulle prestazioni.
- La regola di default deny (implicit deny) deve essere sempre l'ultima regola.

**Controllo dei cambiamenti per le regole firewall**

Ogni modifica alle regole firewall deve seguire il processo di change management:

1. Richiesta formale con giustificazione di business e dettaglio tecnico (sorgente, destinazione, porta, protocollo).
2. Valutazione dell'impatto sulla sicurezza da parte del team di sicurezza.
3. Approvazione da parte del change advisory board (CAB) per modifiche significative.
4. Implementazione in una finestra di manutenzione pianificata.
5. Verifica post-implementazione: confermare che il traffico desiderato funzioni e che non ci siano effetti collaterali.
6. Documentazione della modifica nel sistema di tracking.

**Procedure di test delle regole**

Dopo ogni modifica, verificare il corretto funzionamento:

- Utilizzare strumenti come `nmap`, `hping3` o `netcat` per verificare che il traffico consentito passi e che il traffico non consentito venga bloccato.
- Testare da entrambe le direzioni (sorgente e destinazione).
- Verificare i log del firewall per confermare che le regole vengano applicate come previsto.
- Per ambienti complessi, mantenere una suite di test automatizzati (es. script Python con `scapy`) che verifichi le regole critiche dopo ogni modifica.

### IDS/IPS Management

I sistemi IDS (Intrusion Detection System) e IPS (Intrusion Prevention System) analizzano il traffico di rete alla ricerca di pattern malevoli noti e comportamenti anomali.

**Pianificazione degli aggiornamenti delle firme**

- Le firme IDS/IPS devono essere aggiornate quotidianamente. Per i sistemi in modalita' IPS (prevenzione attiva), applicare gli aggiornamenti prima in modalita' detection-only per 24-48 ore per verificare l'assenza di falsi positivi bloccanti.
- Mantenere un elenco delle firme disabilitate con la motivazione. Revisione mensile.
- Sottoscrivere i feed di Emerging Threats (ET Open o ET Pro) in aggiunta alle firme del vendor.

**Tuning dei falsi positivi**

I falsi positivi sono la sfida principale nella gestione IDS/IPS. Un tasso elevato di falsi positivi causa alert fatigue e puo' portare a ignorare alert legittimi:

- Analizzare ogni falso positivo per comprendere la causa (traffico legittimo che corrisponde a una firma, firma troppo generica, applicazione che genera pattern sospetti).
- Creare eccezioni specifiche (per sorgente, destinazione, porta) anziche' disabilitare completamente la firma.
- Documentare ogni eccezione con ticket di riferimento.
- Monitorare le firme con il maggior numero di alert per identificare candidati al tuning.

**Correlazione degli alert e integrazione threat intelligence**

- Integrare gli alert IDS/IPS con il SIEM per la correlazione con eventi da altre fonti (log di autenticazione, log applicativi, alert EDR).
- Configurare feed di threat intelligence (STIX/TAXII) per arricchire gli alert con informazioni contestuali (reputazione IP, indicatori di compromissione noti).
- Implementare regole di correlazione che combinino alert IDS/IPS con altri indicatori per ridurre i falsi positivi e aumentare la confidenza nel rilevamento.

### Network Segmentation

La segmentazione della rete limita il movimento laterale di un attaccante che ha compromesso un sistema, contenendo l'impatto di un'eventuale violazione.

**Audit delle VLAN**

- Verificare trimestralmente che ogni VLAN contenga solo i dispositivi previsti. Scansionare le VLAN per rilevare dispositivi non autorizzati (rogue device detection).
- Documentare lo scopo di ogni VLAN, i sistemi che contiene e le regole di accesso inter-VLAN.
- Verificare che le VLAN di gestione (management VLAN) siano separate dalle VLAN di produzione e che l'accesso alla management VLAN sia limitato ai soli amministratori autorizzati.

**Verifica della micro-segmentazione**

La micro-segmentazione estende la segmentazione tradizionale a livello di singola workload o applicazione:

- Verificare che le policy di micro-segmentazione riflettano le comunicazioni effettivamente necessarie tra le applicazioni (principio di zero trust: nega tutto, consenti solo il necessario).
- Utilizzare strumenti di network flow analysis per mappare le comunicazioni reali e confrontarle con le policy configurate.
- Testare periodicamente che le barriere di segmentazione funzionino (tentativo di comunicazione tra segmenti che dovrebbero essere isolati).

**Audit della DMZ**

La DMZ (Demilitarized Zone) ospita i servizi esposti a Internet e richiede controlli rigorosi:

- Verificare che i server in DMZ non possano iniziare connessioni verso la rete interna (solo risposta a connessioni in ingresso o connessioni specifiche verso backend interni strettamente necessarie).
- Verificare che i server in DMZ non comunichino tra loro a meno che non sia esplicitamente richiesto dall'architettura applicativa.
- Controllare che i servizi di gestione (SSH, RDP) sui server DMZ siano accessibili solo dalla rete di gestione, mai da Internet.

**Principi dell'architettura Zero Trust**

L'approccio Zero Trust si basa sul principio "never trust, always verify":

- Nessun dispositivo o utente e' considerato affidabile per default, indipendentemente dalla posizione nella rete.
- Ogni richiesta di accesso viene autenticata, autorizzata e cifrata.
- L'accesso e' basato su identita' (utente + dispositivo + contesto) anziche' sulla posizione di rete.
- Implementazione graduale: iniziare con le risorse piu' critiche e i segmenti piu' sensibili, poi estendere progressivamente.

### WAF (Web Application Firewall)

Il WAF protegge le applicazioni web da attacchi specifici come SQL injection, cross-site scripting (XSS), file inclusion e altre vulnerabilita' applicative.

**Aggiornamento dei set di regole (OWASP CRS)**

- L'OWASP Core Rule Set (CRS) fornisce un set di regole generico per la protezione delle applicazioni web. Aggiornare alla versione piu' recente trimestralmente.
- Dopo ogni aggiornamento, attivare le nuove regole in modalita' detection-only (anomaly scoring senza blocco) per una settimana, analizzare i log per falsi positivi, poi attivare il blocco.
- Configurare il paranoia level appropriato: livello 1 per applicazioni standard, livello 2-3 per applicazioni che gestiscono dati sensibili, livello 4 solo per ambienti ad altissima sicurezza con applicazioni semplici e ben definite.

**Gestione delle regole personalizzate**

- Creare regole personalizzate per proteggere logiche applicative specifiche (es. protezione API, rate limiting su endpoint critici, blocco di user-agent noti malevoli).
- Documentare ogni regola personalizzata con: scopo, condizione di match, azione, data di creazione, proprietario.
- Testare le regole personalizzate in ambiente di staging prima del deployment in produzione.

**Gestione dei falsi positivi**

- Analizzare i log WAF quotidianamente per identificare blocchi legittimi e falsi positivi.
- Per i falsi positivi, creare eccezioni specifiche (per URI, per parametro, per IP sorgente) anziche' disabilitare la regola globalmente.
- Mantenere un registro delle eccezioni con revisione mensile.

**Monitoraggio dell'impatto sulle prestazioni**

- Monitorare la latenza aggiunta dal WAF (obiettivo: <5ms per richiesta in condizioni normali).
- Monitorare l'utilizzo CPU/memoria del WAF durante i picchi di traffico.
- Configurare la modalita' fail-open o fail-close in base alla criticita' dell'applicazione protetta (fail-open: in caso di malfunzionamento del WAF, il traffico passa senza ispezione; fail-close: il traffico viene bloccato).

### Network Monitoring

Il monitoraggio del traffico di rete fornisce visibilita' sulle comunicazioni e consente di rilevare anomalie che potrebbero indicare un attacco o un malfunzionamento.

**Analisi del traffico (NetFlow/sFlow)**

- Configurare l'esportazione NetFlow/sFlow su tutti i router e switch principali.
- Raccogliere i flussi in un collector centralizzato (es. ntopng, Elastiflow, SolarWinds NTA).
- Definire baseline del traffico normale per ogni segmento di rete (top talkers, protocolli predominanti, pattern temporali).
- Configurare alert per deviazioni significative dalla baseline (es. aumento improvviso del traffico verso un singolo host, traffico su porte insolite, comunicazioni verso paesi non previsti).

**Rilevamento anomalie**

- Monitorare il traffico DNS per rilevare tunneling DNS (query con entropia elevata, volume anomalo di query verso un singolo dominio).
- Rilevare scansioni di rete interne (un host che contatta un numero elevato di IP o porte in breve tempo).
- Monitorare il traffico cifrato: analisi dei metadati TLS (JA3/JA3S fingerprinting) per identificare comunicazioni con C2 server noti.

**Utilizzo della banda e distribuzione dei protocolli**

- Monitorare l'utilizzo della banda per interfaccia e per VLAN. Generare alert quando l'utilizzo supera l'80% della capacita' per un periodo prolungato.
- Analizzare la distribuzione dei protocolli: variazioni significative possono indicare un problema (es. aumento del traffico ICMP potrebbe indicare un tunnel ICMP, aumento del traffico sulla porta 445 potrebbe indicare un attacco laterale tramite SMB).

---

## Gestione Certificati

I certificati digitali sono alla base della sicurezza delle comunicazioni cifrate e dell'autenticazione. Un certificato scaduto o configurato in modo errato puo' causare interruzioni di servizio, vulnerabilita' di sicurezza e perdita di fiducia degli utenti.

### PKI Maintenance

L'infrastruttura PKI (Public Key Infrastructure) richiede manutenzione regolare per garantire la fiducia e l'integrita' della catena di certificazione.

**Health check della CA (Certificate Authority)**

- Verificare settimanalmente lo stato dei servizi della CA (processo, connettivita' di rete, spazio disco).
- Controllare la validita' del certificato della CA stessa: il certificato della root CA ha tipicamente una validita' di 10-20 anni, ma le subordinate CA hanno validita' inferiore (3-5 anni). Monitorare con largo anticipo.
- Verificare la corretta sincronizzazione temporale (NTP) della CA: un'ora errata puo' causare problemi nella validazione dei certificati.
- Testare periodicamente il processo di emissione di un certificato per verificare che la CA funzioni correttamente end-to-end.

**Verifica della pubblicazione CRL**

La CRL (Certificate Revocation List) e' l'elenco dei certificati revocati. Se la CRL non viene pubblicata correttamente, i client non possono verificare se un certificato e' stato revocato:

- Verificare quotidianamente che la CRL sia accessibile al punto di distribuzione configurato (CDP).
- Monitorare la data di scadenza della CRL (Next Update field): se la CRL scade senza essere rinnovata, i client potrebbero rifiutare tutti i certificati della CA.
- Se si utilizza OCSP (Online Certificate Status Protocol), verificare che il responder sia attivo e risponda correttamente.

**Inventario dei certificati e monitoraggio delle scadenze**

Mantenere un inventario completo di tutti i certificati emessi:

- Soggetto (CN/SAN), emittente, numero di serie, data di emissione, data di scadenza, algoritmo di firma, lunghezza della chiave, sistema/servizio su cui e' installato.
- Configurare alert a 90, 60 e 30 giorni dalla scadenza. Per i certificati critici (load balancer, gateway VPN, server mail), alert aggiuntivo a 14 e 7 giorni.
- Utilizzare strumenti di certificate discovery per rilevare certificati non censiti nell'inventario (scansione delle porte 443, 8443, 636, ecc. sulla rete interna).

**Pianificazione della rotazione delle chiavi**

- Le chiavi private associate ai certificati devono essere ruotate periodicamente, non solo rinnnovando il certificato con la stessa chiave.
- Frequenza raccomandata: generare una nuova coppia di chiavi ad ogni rinnovo del certificato.
- Per le chiavi della CA, la rotazione e' un'operazione piu' complessa che richiede pianificazione e comunicazione a tutti i sistemi che si fidano della CA.

### SSL/TLS Certificate Management

**Inventario dei certificati esterni (servizi pubblici)**

Per ogni servizio esposto a Internet, documentare:

- FQDN protetto (inclusi tutti i SAN).
- Certificate Authority che ha emesso il certificato (Let's Encrypt, DigiCert, Sectigo, ecc.).
- Data di scadenza e processo di rinnovo (automatico o manuale).
- Tipo di certificato (DV, OV, EV).
- Responsabile del rinnovo.

**Inventario dei certificati interni**

I certificati interni sono spesso piu' numerosi e meno monitorati di quelli esterni:

- Certificati per comunicazioni interne (microservizi, database, code, servizi interni).
- Certificati per autenticazione client (smart card, VPN client).
- Certificati per la firma del codice.
- Certificati per la cifratura email (S/MIME).

**Configurazione auto-rinnovo (certbot, ACME)**

Per i certificati Let's Encrypt e altre CA compatibili ACME:

```bash
# Installazione certbot
apt install certbot python3-certbot-nginx

# Ottenimento certificato con validazione HTTP
certbot certonly --webroot -w /var/www/html -d example.com -d www.example.com

# Configurazione rinnovo automatico (cron o systemd timer)
# certbot renew viene eseguito due volte al giorno dal timer di sistema
systemctl enable certbot.timer

# Verifica del rinnovo automatico
certbot renew --dry-run

# Hook post-rinnovo per ricaricare il servizio
# In /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh
#!/bin/bash
systemctl reload nginx
```

**Audit della configurazione TLS**

- Testare la configurazione TLS di tutti i servizi pubblici con SSL Labs (obiettivo: grado A o A+).
- Per i servizi interni, utilizzare `testssl.sh` o `sslyze` per verifiche automatizzate.
- Configurazione raccomandata minima: TLS 1.2 come versione minima (TLS 1.3 preferito), disabilitare TLS 1.0 e 1.1 completamente.
- Eliminare le cipher suite deboli: RC4, DES, 3DES, export ciphers, NULL ciphers.
- Abilitare HSTS (HTTP Strict Transport Security) con max-age di almeno 6 mesi su tutti i servizi web.
- Configurare l'OCSP stapling per migliorare le prestazioni e la privacy.

**Rilevamento cipher suite deboli**

Script di verifica periodica:

```bash
# Verifica con nmap
nmap --script ssl-enum-ciphers -p 443 target.example.com

# Verifica con openssl
openssl s_client -connect target.example.com:443 -tls1 2>/dev/null | grep -i "cipher"
# Se la connessione ha successo con -tls1, TLS 1.0 e' ancora abilitato

# Verifica completa con testssl.sh
./testssl.sh --severity HIGH target.example.com:443
```

### Certificate Automation

L'automazione della gestione dei certificati riduce il rischio di scadenze non gestite e standardizza il processo di emissione e rinnovo.

**Setup del protocollo ACME**

Il protocollo ACME (Automatic Certificate Management Environment) consente l'emissione e il rinnovo automatico dei certificati:

- Configurare un client ACME (certbot, acme.sh, Caddy built-in) su ogni server che necessita di certificati.
- Per ambienti con molti server, centralizzare la gestione ACME con un proxy o un servizio dedicato.
- Utilizzare la validazione DNS (dns-01 challenge) per certificati wildcard o per server non raggiungibili via HTTP dall'esterno.

**Integrazione Let's Encrypt**

- Let's Encrypt fornisce certificati gratuiti con validita' di 90 giorni, richiedendo automazione del rinnovo.
- Configurare il rinnovo automatico con almeno 30 giorni di anticipo sulla scadenza.
- Monitorare i limiti di rate limiting di Let's Encrypt (50 certificati per dominio registrato a settimana).
- Avere un piano di fallback con un'altra CA nel caso Let's Encrypt abbia problemi temporanei.

**Auto-enrollment per CA interne**

- Configurare l'auto-enrollment in Active Directory Certificate Services (AD CS) per i certificati interni (autenticazione computer, autenticazione utente).
- Definire template di certificato con impostazioni appropriate (validita', lunghezza chiave, utilizzo chiave).
- Monitorare il funzionamento dell'auto-enrollment tramite i log degli eventi di Windows.

**Script di monitoraggio**

PowerShell per il monitoraggio dei certificati su server Windows:

```powershell
# Controllo certificati in scadenza nei prossimi 30 giorni
$threshold = (Get-Date).AddDays(30)
$certs = Get-ChildItem Cert:\LocalMachine\My |
    Where-Object { $_.NotAfter -lt $threshold -and $_.NotAfter -gt (Get-Date) }

foreach ($cert in $certs) {
    $daysLeft = ($cert.NotAfter - (Get-Date)).Days
    Write-Warning "Certificato $($cert.Subject) scade tra $daysLeft giorni ($($cert.NotAfter))"
}
```

Bash per il monitoraggio dei certificati su server Linux:

```bash
#!/bin/bash
# Controllo scadenza certificati SSL su una lista di host
HOSTS="web01.example.com:443 mail.example.com:993 api.example.com:443"
WARN_DAYS=30

for HOST in $HOSTS; do
    EXPIRY=$(echo | openssl s_client -servername "${HOST%%:*}" \
        -connect "$HOST" 2>/dev/null | \
        openssl x509 -noout -enddate 2>/dev/null | \
        cut -d= -f2)

    if [ -n "$EXPIRY" ]; then
        EXPIRY_EPOCH=$(date -d "$EXPIRY" +%s)
        NOW_EPOCH=$(date +%s)
        DAYS_LEFT=$(( (EXPIRY_EPOCH - NOW_EPOCH) / 86400 ))

        if [ "$DAYS_LEFT" -lt "$WARN_DAYS" ]; then
            echo "ATTENZIONE: $HOST - certificato scade tra $DAYS_LEFT giorni ($EXPIRY)"
        fi
    else
        echo "ERRORE: impossibile verificare il certificato di $HOST"
    fi
done
```

---

## Audit e Compliance

L'audit di sicurezza e la conformita' normativa sono componenti essenziali della sicurezza operativa. Forniscono la garanzia che i controlli di sicurezza funzionino come previsto e che l'organizzazione soddisfi i requisiti legali e contrattuali.

### Security Audit Program

Un programma di audit strutturato garantisce che tutte le aree della sicurezza vengano verificate regolarmente.

**Tipologie di audit**

- **Audit interno**: condotto dal team di sicurezza interno o da un team indipendente all'interno dell'organizzazione. Frequenza: semestrale per le aree critiche, annuale per le altre. Vantaggio: conoscenza approfondita dell'ambiente. Rischio: possibile mancanza di obiettivita'.
- **Audit esterno**: condotto da societa' di consulenza specializzate. Frequenza: almeno annuale. Obbligatorio per alcune certificazioni (ISO 27001, PCI DSS). Fornisce una valutazione indipendente e obiettiva.
- **Audit di compliance**: focalizzato sulla verifica della conformita' a specifici requisiti normativi o standard. Puo' essere interno o esterno a seconda del framework.

**Frequenza e pianificazione**

- Definire un piano di audit annuale che copra tutte le aree di sicurezza.
- Le aree ad alto rischio (gestione accessi privilegiati, sicurezza perimetrale, gestione vulnerabilita') devono essere auditate con maggiore frequenza.
- Pianificare gli audit in modo da non sovrapporre troppe attivita' di verifica nello stesso periodo (audit fatigue).

**Procedure di raccolta delle evidenze**

- Definire in anticipo le evidenze necessarie per ogni controllo da verificare.
- Le evidenze devono essere raccolte in modo non invasivo e senza alterare i sistemi in produzione.
- Tipologie di evidenze: screenshot con timestamp, export di configurazioni, log (con hash per garantire l'integrita'), report automatici degli strumenti di sicurezza, verbali di interviste al personale.
- Archiviare le evidenze in modo sicuro con accesso limitato al team di audit.

**Classificazione dei findings**

| Classificazione | Descrizione | SLA Remediation |
|----------------|-------------|-----------------|
| Critico | Vulnerabilita' sfruttabile immediatamente con impatto grave | 7 giorni |
| Alto | Controllo di sicurezza mancante o gravemente carente | 30 giorni |
| Medio | Controllo presente ma non pienamente efficace | 90 giorni |
| Basso | Miglioramento raccomandato, rischio contenuto | 180 giorni |

**Tracciamento della remediation**

- Ogni finding deve essere assegnato a un responsabile con una data di scadenza per la remediation.
- Tracciare lo stato di avanzamento della remediation in un sistema centralizzato (puo' essere il sistema di ticketing esistente).
- Verificare la remediation con un test di conferma (non affidarsi alla sola dichiarazione del responsabile).
- Escalation automatica per finding non risolti entro lo SLA.

### Log Audit

I log sono la fonte primaria di informazioni per il rilevamento degli incidenti, l'analisi forense e la verifica della conformita'.

**Sorgenti di log rilevanti per la sicurezza**

- **Autenticazione**: log di Active Directory (Event ID 4624, 4625, 4648, 4768, 4771), log di RADIUS/TACACS+, log di VPN.
- **Accesso privilegiato**: log di sudo/su (Linux), log di PowerShell (Event ID 4104), log di sessioni RDP (Event ID 4778, 4779).
- **Modifiche di sistema**: log di audit del sistema operativo (`auditd` su Linux, Security event log su Windows), log di Group Policy.
- **Rete**: log del firewall, log IDS/IPS, log del proxy web, log DNS, log NetFlow.
- **Applicazioni**: log dei web server, log dei database, log delle applicazioni business-critical.
- **Sicurezza fisica**: log di accesso fisico (badge), log di videosorveglianza.

**Integrita' dei log (rilevamento manomissioni)**

I log devono essere protetti da alterazioni. Un attaccante sofisticato tentera' di cancellare o modificare i log per nascondere le proprie tracce:

- Configurare l'invio dei log in tempo reale a un server centralizzato (syslog, Windows Event Forwarding). I log sul sistema di origine possono essere compromessi se il sistema viene violato; i log sul collector centralizzato sono protetti.
- Implementare la firma digitale dei log o l'hashing a catena (ogni entry di log include l'hash della precedente, rendendo impossibile modificare un singolo record senza invalidare tutti i successivi).
- Limitare l'accesso al server di raccolta log ai soli amministratori del SIEM. Nessun altro utente o sistema deve poter scrivere, modificare o cancellare i log centralizzati.
- Utilizzare storage WORM (Write Once Read Many) per i log che devono soddisfare requisiti di conformita' stringenti.

**Policy di retention dei log**

La durata di conservazione dei log dipende dai requisiti normativi e di business:

| Categoria | Retention Minima | Requisito |
|-----------|-----------------|-----------|
| Log di sicurezza generali | 12 mesi online, 24 mesi archivio | Best practice ISO 27001 |
| Log di accesso ai dati personali | 24 mesi | GDPR (accountability) |
| Log di transazioni finanziarie | 5 anni | Normativa fiscale italiana |
| Log PCI DSS | 12 mesi online con 3 mesi di analisi immediata | PCI DSS Req. 10.7 |
| Log di accesso amministrativo | 24 mesi | Best practice, NIS2 |

**Regole di correlazione SIEM**

Il SIEM (Security Information and Event Management) correla eventi da fonti diverse per rilevare attacchi complessi. Regole di correlazione essenziali:

- **Brute force detection**: piu' di 10 tentativi di autenticazione falliti dallo stesso IP in 5 minuti.
- **Credential stuffing**: tentativi di autenticazione falliti su molti account diversi dalla stessa sorgente.
- **Lateral movement**: autenticazione riuscita su piu' server in rapida successione dallo stesso account.
- **Privilege escalation**: un account standard che improvvisamente esegue azioni amministrative.
- **Data exfiltration**: volume anomalo di traffico in uscita verso destinazioni insolite, specialmente in orari non lavorativi.
- **Impossible travel**: autenticazione dallo stesso utente da localita' geografiche incompatibili in un intervallo di tempo troppo breve.

### Compliance Frameworks

**Mappatura ISO 27001 alla manutenzione IT**

Lo standard ISO 27001 (Annex A) include controlli direttamente rilevanti per la manutenzione IT:

- **A.8.8 Management of technical vulnerabilities**: gestione delle vulnerabilita' tecniche, patching, scansioni.
- **A.8.9 Configuration management**: gestione delle configurazioni, hardening, baseline.
- **A.8.15 Logging**: raccolta, protezione e analisi dei log.
- **A.8.16 Monitoring activities**: monitoraggio della sicurezza, rilevamento anomalie.
- **A.8.20 Networks security**: sicurezza di rete, segmentazione, firewall.
- **A.8.24 Use of cryptography**: gestione certificati, cifratura, protocolli sicuri.
- **A.5.15 Access control**: gestione degli accessi, RBAC, principio del minimo privilegio.
- **A.5.18 Access rights**: provisioning e deprovisioning degli accessi.

**Requisiti tecnici GDPR**

Il GDPR richiede misure tecniche "adeguate" per la protezione dei dati personali. Nella manutenzione IT, questo si traduce in:

- Cifratura dei dati personali in transito (TLS) e a riposo (cifratura disco, cifratura database).
- Pseudonimizzazione dove possibile (negli ambienti di test e sviluppo, mai usare dati personali reali).
- Capacita' di rilevare violazioni dei dati (data breach) entro 72 ore (requisito SIEM/monitoraggio).
- Capacita' di ripristinare l'accesso ai dati in caso di incidente (requisito backup/DR).
- Test regolari dell'efficacia delle misure di sicurezza (vulnerability assessment, penetration test).
- Registro delle attivita' di trattamento e log di accesso ai dati personali.

**Requisiti della direttiva NIS2**

La direttiva NIS2 (Network and Information Security Directive 2), recepita in Italia con il D.Lgs. 138/2024, introduce obblighi stringenti per i soggetti essenziali e importanti:

- Analisi dei rischi e politiche di sicurezza dei sistemi informatici e di rete.
- Gestione degli incidenti (rilevamento, analisi, risposta, notifica alle autorita' competenti).
- Continuita' operativa e gestione delle crisi.
- Sicurezza della catena di approvvigionamento (supply chain security).
- Gestione delle vulnerabilita' e divulgazione responsabile.
- Pratiche di igiene informatica di base e formazione in materia di sicurezza.
- Uso della crittografia e della cifratura.
- Sicurezza delle risorse umane, strategie di controllo degli accessi e gestione degli asset.

**Controlli PCI DSS rilevanti**

Per le organizzazioni che gestiscono dati di carte di pagamento:

- **Requisito 1**: installare e mantenere controlli di sicurezza di rete (firewall, segmentazione).
- **Requisito 2**: applicare configurazioni sicure a tutti i componenti del sistema (hardening).
- **Requisito 5**: proteggere tutti i sistemi e le reti dal malware (antivirus/EDR).
- **Requisito 6**: sviluppare e mantenere sistemi e software sicuri (patching, vulnerability management).
- **Requisito 8**: identificare gli utenti e autenticare l'accesso ai componenti del sistema (MFA, gestione password).
- **Requisito 10**: registrare e monitorare tutti gli accessi ai componenti del sistema e ai dati dei titolari di carte (logging, SIEM).
- **Requisito 11**: testare regolarmente la sicurezza dei sistemi e delle reti (scansioni ASV trimestrali, penetration test annuali).

**Requisiti SOC 2 Type II**

SOC 2 Type II verifica l'efficacia dei controlli nel tempo (tipicamente 6-12 mesi):

- I controlli devono essere non solo presenti (Type I) ma anche operativi e efficaci nel periodo di osservazione (Type II).
- Le evidenze devono coprire l'intero periodo di audit, non un singolo momento.
- Per la manutenzione IT, questo significa: log continui, report periodici di patching, metriche di vulnerability management nel tempo, evidenza di revisioni periodiche degli accessi.

### Access Audit

L'audit degli accessi verifica che i permessi assegnati siano appropriati e conformi al principio del minimo privilegio.

**Revisione degli accessi privilegiati (trimestrale)**

- Elencare tutti gli account con privilegi amministrativi (Domain Admins, root, sudo, accesso a console di gestione).
- Per ogni account, verificare: l'account e' ancora necessario? La persona e' ancora nel ruolo che richiede quei privilegi? L'ultimo accesso e' recente (l'account e' effettivamente utilizzato)?
- Rimuovere immediatamente i privilegi non piu' necessari.
- Documentare la revisione con firma del responsabile.

**Audit degli account di servizio**

Gli account di servizio sono spesso trascurati e rappresentano un rischio significativo:

- Inventariare tutti gli account di servizio con: nome, scopo, sistemi su cui e' utilizzato, privilegi assegnati, proprietario (responsabile del servizio), data dell'ultima modifica della password.
- Verificare che ogni account di servizio abbia solo i privilegi strettamente necessari per il suo funzionamento.
- Verificare che le password degli account di servizio siano gestite in un vault e ruotate regolarmente (o utilizzare Managed Service Accounts/gMSA in ambiente Active Directory).

**Eliminazione degli account condivisi**

Gli account condivisi (es. un account "admin" utilizzato da piu' persone) impediscono la tracciabilita' individuale e devono essere eliminati:

- Identificare tutti gli account condivisi nell'organizzazione.
- Per ogni account condiviso, creare account individuali con i medesimi permessi.
- Se l'eliminazione immediata non e' possibile (es. vincoli applicativi), implementare una soluzione PAM che registri quale persona fisica utilizza l'account condiviso in ogni sessione.

**Verifica della conformita' MFA**

- Verificare che l'MFA (Multi-Factor Authentication) sia attiva per tutti gli accessi privilegiati, accessi remoti (VPN, RDP gateway), accessi alle console di gestione cloud, accessi alle applicazioni che gestiscono dati sensibili.
- Identificare eventuali eccezioni e valutarne la giustificazione.
- Verificare che i metodi MFA utilizzati siano robusti: evitare SMS come secondo fattore (vulnerabile a SIM swapping), preferire app authenticator (TOTP), chiavi hardware (FIDO2/WebAuthn) o push notification con number matching.

**Rilevamento account dormienti**

- Interrogare Active Directory per gli account con `lastLogonTimestamp` superiore a 90 giorni.
- Gli account dormienti devono essere prima disabilitati (non cancellati) per un periodo di 30 giorni, poi cancellati se nessuno ne rivendica l'utilizzo.
- Automatizzare il processo con uno script che generi un report settimanale degli account dormienti e invii una notifica al responsabile.

**Revisione delle appartenenze ai gruppi**

- Verificare trimestralmente le appartenenze ai gruppi di sicurezza, in particolare ai gruppi con privilegi elevati.
- Identificare il "role creep": utenti che hanno accumulato appartenenze a gruppi nel tempo a causa di cambi di ruolo senza revoca dei permessi precedenti.
- Confrontare le appartenenze ai gruppi con la matrice RBAC approvata e rimuovere le discrepanze.

---

## Gestione Accessi

La gestione degli accessi e' il processo attraverso il quale si controlla chi puo' accedere a quali risorse e con quali permessi. Un sistema di gestione accessi efficace si basa sul principio del minimo privilegio: ogni utente deve avere solo i permessi strettamente necessari per svolgere il proprio lavoro.

### Privileged Access Management (PAM)

Gli accessi privilegiati (amministratori di sistema, DBA, amministratori di rete) rappresentano il rischio maggiore per la sicurezza perche' consentono il controllo completo dei sistemi. Una soluzione PAM limita, monitora e registra l'utilizzo di questi accessi.

**Configurazione degli strumenti PAM**

Strumenti di riferimento:

- **CyberArk**: soluzione enterprise leader di mercato. Offre password vaulting, session recording, just-in-time access, threat analytics. Costo elevato, adatto a grandi organizzazioni.
- **BeyondTrust**: alternativa solida con buone capacita' di session management e privilegio minimo su endpoint. Interfaccia piu' intuitiva di CyberArk.
- **Alternative open source**: Teleport (accesso SSH/RDP/database con audit trail completo), HashiCorp Vault (gestione segreti e credenziali dinamiche), Apache Guacamole (gateway per accesso remoto con registrazione delle sessioni).

**Registrazione delle sessioni**

- Tutte le sessioni privilegiate (SSH con accesso root, RDP con account amministratore, accesso a console di gestione) devono essere registrate.
- La registrazione deve catturare: comandi eseguiti (per sessioni CLI), video della sessione (per sessioni grafiche), timestamp di inizio e fine, indirizzo IP di origine, account utilizzato.
- Le registrazioni devono essere conservate per almeno 12 mesi e accessibili solo al team di sicurezza.
- Implementare alert in tempo reale per comandi ad alto rischio eseguiti durante sessioni privilegiate (es. `rm -rf`, `DROP DATABASE`, modifica di configurazioni di sicurezza).

**Accesso just-in-time (JIT)**

L'accesso JIT elimina i privilegi permanenti:

- Gli utenti richiedono l'accesso privilegiato tramite un workflow approvativo.
- L'accesso viene concesso per un periodo limitato (es. 2-4 ore) e revocato automaticamente alla scadenza.
- Ogni concessione e' registrata con: richiedente, approvatore, motivazione, durata, risorse accessibili.
- Per le emergenze (break glass), prevedere un processo accelerato con approvazione successiva e revisione obbligatoria entro 24 ore.

**Password vaulting**

- Le password degli account privilegiati non devono essere conosciute dagli operatori. Le password sono generate automaticamente dal vault, complesse e univoche per ogni sistema.
- L'operatore si autentica al vault con le proprie credenziali personali + MFA, il vault fornisce l'accesso al sistema target senza rivelare la password (session brokering).
- Le password nel vault vengono ruotate automaticamente dopo ogni utilizzo o con cadenza regolare (es. ogni 24 ore per gli account piu' critici).
- Il vault deve essere configurato in alta disponibilita' (cluster) per evitare che un guasto al vault impedisca l'accesso ai sistemi. Prevedere procedure di break glass per l'accesso di emergenza senza vault.

### RBAC Implementation

Il modello RBAC (Role-Based Access Control) assegna i permessi tramite ruoli anziche' direttamente agli utenti, semplificando la gestione e migliorando la conformita'.

**Definizione e documentazione dei ruoli**

La definizione dei ruoli richiede un lavoro congiunto tra IT e business:

1. Identificare le funzioni lavorative nell'organizzazione (es. analista finanziario, sviluppatore, helpdesk operator, system administrator).
2. Per ogni funzione, determinare le risorse e i permessi necessari (applicazioni, share di rete, caselle email, sistemi).
3. Creare ruoli che raggruppino i permessi necessari per ciascuna funzione. Un utente puo' avere piu' ruoli (es. un team leader puo' avere il ruolo del suo team piu' un ruolo di gestione).
4. Documentare ogni ruolo in una matrice RBAC: nome del ruolo, descrizione, permessi inclusi, approvatore per l'assegnazione del ruolo.
5. Revisionare la matrice annualmente o quando cambiano i processi di business.

**Audit dell'assegnazione dei ruoli**

- Verificare trimestralmente che ogni utente abbia solo i ruoli appropriati per la propria funzione attuale.
- Generare report sugli utenti con ruoli multipli e verificare che non ci siano conflitti (es. un utente che puo' sia creare che approvare ordini di acquisto — violazione della separazione dei compiti).

**Verifica del minimo privilegio**

- Analizzare periodicamente l'utilizzo effettivo dei permessi: se un utente ha un permesso che non ha mai utilizzato in 90 giorni, il permesso potrebbe non essere necessario.
- Utilizzare strumenti di access analytics (disponibili in Azure AD/Entra ID, CyberArk, SailPoint) per identificare permessi non utilizzati.

**Rilevamento del role creep**

Il role creep si verifica quando un utente accumula ruoli e permessi nel tempo senza che quelli precedenti vengano revocati:

- Confrontare il numero di ruoli/permessi di ogni utente con la media del suo gruppo di pari. Utenti con permessi significativamente superiori alla media sono candidati per la revisione.
- Implementare un processo automatico che segnali gli utenti con un numero di ruoli superiore a una soglia definita.

**Separazione dei compiti (Segregation of Duties)**

- Definire le combinazioni di ruoli incompatibili (es. chi gestisce il backup non dovrebbe poter cancellare i backup; chi amministra il firewall non dovrebbe poter cancellare i log del firewall).
- Implementare controlli tecnici che impediscano l'assegnazione simultanea di ruoli incompatibili.
- Dove la separazione completa non e' possibile (es. team IT ridotto), implementare controlli compensativi (approvazione duale, revisione dei log da parte di un terzo).

### Identity Lifecycle

La gestione del ciclo di vita delle identita' garantisce che gli accessi vengano concessi, modificati e revocati in modo tempestivo e controllato.

**Processo di onboarding (provisioning degli accessi)**

1. Il responsabile del nuovo assunto compila una richiesta di accesso specificando il ruolo e le risorse necessarie.
2. Il team IT verifica la richiesta rispetto alla matrice RBAC: i permessi richiesti sono coerenti con il ruolo?
3. Gli accessi vengono creati seguendo la checklist di provisioning (account AD, casella email, accesso VPN, applicazioni di business, badge di accesso fisico).
4. Le credenziali temporanee vengono consegnate in modo sicuro (mai via email in chiaro). L'utente e' obbligato a cambiare la password al primo accesso.
5. Verifica post-provisioning: confermare che l'utente possa accedere a tutte le risorse previste e a nessuna risorsa non prevista.

**Gestione dei cambiamenti di ruolo (trasferimento/promozione)**

Questa fase e' spesso la piu' critica perche' e' dove si genera il role creep:

1. Il responsabile del trasferimento notifica il team IT del cambio di ruolo.
2. Il team IT assegna i nuovi ruoli/permessi necessari per la nuova funzione.
3. **Cruciale**: il team IT revoca i permessi relativi alla funzione precedente che non sono piu' necessari. Questo passaggio viene spesso dimenticato.
4. Verificare dopo 30 giorni che il dipendente non abbia piu' bisogno di accesso ai sistemi della funzione precedente.

**Processo di offboarding (deprovisioning degli accessi)**

Il deprovisioning tempestivo e' fondamentale per prevenire accessi non autorizzati da parte di ex dipendenti:

1. Le risorse umane notificano il team IT con almeno 24 ore di anticipo rispetto all'ultimo giorno lavorativo del dipendente (per dimissioni volontarie) o immediatamente (per licenziamento).
2. Il giorno di uscita, disabilitare tutti gli accessi secondo la checklist di deprovisioning: account AD (disabilitare, non cancellare immediatamente), accesso VPN, accesso email, accesso applicazioni cloud (revocare sessioni attive e token OAuth), badge di accesso fisico, account su sistemi esterni (SaaS, portali vendor).
3. Reindirizzare la casella email al responsabile designato per un periodo definito (tipicamente 30-90 giorni).
4. Dopo 30 giorni dalla disabilitazione, e in assenza di richieste, cancellare l'account e archiviare i dati secondo la policy di data retention.
5. Per i dipendenti con accesso privilegiato: ruotare immediatamente tutte le password condivise a cui avevano accesso e revocare le chiavi SSH/certificati personali.

**Certificazione periodica degli accessi**

Anche con processi di provisioning e deprovisioning perfetti, e' necessaria una verifica periodica:

- Frequenza: semestrale per gli accessi standard, trimestrale per gli accessi privilegiati.
- Ogni responsabile riceve l'elenco degli accessi dei propri collaboratori e deve confermare o revocare ciascun accesso.
- Gli accessi non confermati entro la scadenza vengono automaticamente revocati.
- Il processo deve essere supportato da uno strumento di Identity Governance (es. SailPoint, Saviynt, One Identity) per garantire tracciabilita' e automazione.

---

## Security Operations Center (SOC)

Il Security Operations Center (SOC) e' l'unita' organizzativa centralizzata responsabile del monitoraggio continuo, del rilevamento delle minacce e della risposta agli incidenti di sicurezza. Un SOC efficace combina persone, processi e tecnologie per fornire visibilita' in tempo reale sulla postura di sicurezza dell'organizzazione e per coordinare la risposta alle minacce.

### Architettura e Modelli SOC

La scelta del modello SOC dipende dalle dimensioni dell'organizzazione, dal budget disponibile, dalla maturita' della sicurezza e dai requisiti normativi.

**SOC interno (in-house)**

L'organizzazione costruisce e gestisce il SOC interamente con risorse proprie:

- **Vantaggi**: controllo completo sulle operazioni, conoscenza approfondita dell'ambiente, personalizzazione totale dei processi e degli strumenti, tempi di risposta potenzialmente piu' rapidi grazie alla prossimita' all'infrastruttura.
- **Svantaggi**: costo elevato (personale H24, strumenti, formazione continua), difficolta' nel reclutamento e nella retention di analisti qualificati, rischio di burn-out del team per organizzazioni con risorse limitate.
- **Adatto a**: grandi organizzazioni con budget adeguato e requisiti di conformita' che richiedono il pieno controllo dei dati e delle operazioni.

**SOC gestito (MSSP / MDR)**

Le operazioni di sicurezza sono delegate in tutto o in parte a un fornitore esterno:

- **Managed Security Service Provider (MSSP)**: il fornitore gestisce gli strumenti di sicurezza (SIEM, firewall, IDS/IPS), monitora gli alert e fornisce report. L'organizzazione mantiene la decisione sulla risposta agli incidenti.
- **Managed Detection and Response (MDR)**: il fornitore va oltre il monitoraggio, eseguendo threat hunting proattivo e fornendo capacita' di risposta diretta agli incidenti. Include tipicamente l'analisi comportamentale e l'intelligence sulle minacce.
- **Adatto a**: organizzazioni medio-piccole che non possono sostenere un SOC interno, oppure come complemento a un SOC interno per la copertura notturna e nei fine settimana.

**SOC ibrido**

Combina risorse interne ed esterne:

- Il team interno gestisce gli incidenti ad alta priorita', le decisioni strategiche e la conoscenza specifica dell'ambiente.
- Il fornitore esterno fornisce copertura H24/7/365, capacita' di analisi aggiuntiva e competenze specialistiche (analisi malware, digital forensics).
- Questo modello offre il miglior equilibrio tra costo e controllo per molte organizzazioni.

**Livelli di maturita' del SOC**

| Livello | Descrizione | Caratteristiche |
|---------|-------------|-----------------|
| 1 — Iniziale | Reattivo, basato su alert | Monitoraggio basico, risposta ad-hoc, nessun processo formalizzato |
| 2 — Gestito | Processi definiti | SIEM configurato, procedure di risposta documentate, metriche base |
| 3 — Definito | Processi standardizzati | Playbook per i principali scenari, threat intelligence integrata, reportistica regolare |
| 4 — Quantificato | Misurato e ottimizzato | KPI monitorati, threat hunting proattivo, automazione parziale (SOAR) |
| 5 — Ottimizzato | Miglioramento continuo | Automazione avanzata, intelligence-driven, analisi predittiva, integrazione completa con il business |

### Processi Operativi del SOC

**Triage degli alert — workflow strutturato**

Il processo di triage e' il cuore dell'operativita' del SOC. Ogni alert deve essere classificato, analizzato e gestito secondo un flusso definito:

1. **Ricezione e classificazione iniziale** (Tier 1 — analista junior):
   - L'alert viene ricevuto dal SIEM o da altre fonti di rilevamento.
   - L'analista verifica se l'alert e' un duplicato o se e' gia' correlato a un incidente aperto.
   - Classificazione iniziale: vero positivo, falso positivo, o richiede ulteriore analisi.
   - Se falso positivo confermato: documentare e chiudere. Se il pattern e' ricorrente, richiedere tuning della regola.
   - Se vero positivo o incerto: escalation a Tier 2 con le evidenze raccolte.
   - SLA: classificazione iniziale entro 15 minuti dalla ricezione per alert ad alta severita'.

2. **Analisi approfondita** (Tier 2 — analista senior):
   - Correlazione con eventi da altre fonti (log di autenticazione, EDR, NetFlow, threat intelligence).
   - Analisi del contesto: l'attivita' e' coerente con il comportamento normale dell'utente/sistema? C'e' un change autorizzato in corso?
   - Determinazione dell'impatto: quali sistemi e dati sono potenzialmente coinvolti?
   - Se confermato come incidente: apertura di un ticket di incidente, attivazione del piano di risposta appropriato.
   - Se richiede competenze specialistiche: escalation a Tier 3.

3. **Analisi avanzata e risposta** (Tier 3 — specialista/incident responder):
   - Analisi forense approfondita: acquisizione di evidenze, analisi di malware, ricostruzione della timeline dell'attacco.
   - Coordinamento della risposta: contenimento, eradicazione, ripristino.
   - Comunicazione con il management e, se necessario, con le autorita' competenti (CSIRT nazionale, Garante per la protezione dei dati personali).

**Modello di turni e copertura H24**

Per garantire la copertura continua, il SOC deve operare con turni strutturati:

- **Modello a 3 turni** (8 ore ciascuno): mattina (06:00-14:00), pomeriggio (14:00-22:00), notte (22:00-06:00). Richiede almeno 5 analisti per turno per garantire la copertura con ferie e malattie.
- **Modello a 4 turni** (12 ore, 2 giorni lavorativi + 2 giorni liberi): riduce il numero di passaggi di consegna ma aumenta la fatica per turno. Utilizzato frequentemente dai SOC maturi.
- **Modello ibrido**: copertura interna durante l'orario di ufficio (8:00-20:00) con escalation al fornitore MDR durante la notte e i fine settimana.
- Per ogni modello, definire una procedura di handover strutturata: gli analisti del turno uscente devono documentare lo stato di tutti gli incidenti aperti, le attivita' in corso e le anomalie osservate.

**Comunicazione e escalation**

Definire una matrice di escalation chiara con i seguenti livelli:

| Severita' Incidente | Notifica Iniziale | Escalation (se non risolto entro SLA) | Comunicazione Management |
|---------------------|-------------------|---------------------------------------|--------------------------|
| Critica (P1) | Immediata — telefono/chat | 30 minuti → SOC Manager → CISO | Entro 1 ora |
| Alta (P2) | Entro 15 minuti — chat/email | 2 ore → SOC Manager | Entro 4 ore |
| Media (P3) | Entro 1 ora — email/ticket | 8 ore → Team Lead | Report giornaliero |
| Bassa (P4) | Ticket di servizio | 24 ore → analista designato | Report settimanale |

### Metriche e KPI del SOC

Le metriche sono essenziali per valutare l'efficacia del SOC e giustificare gli investimenti. Senza dati misurabili, non e' possibile dimostrare il valore del SOC al management ne' identificare aree di miglioramento.

**Metriche operative chiave**

| Metrica | Descrizione | Obiettivo |
|---------|-------------|-----------|
| MTTD (Mean Time to Detect) | Tempo medio dalla compromissione alla rilevazione | < 24 ore (obiettivo avanzato: < 1 ora) |
| MTTR (Mean Time to Respond) | Tempo medio dalla rilevazione al contenimento | < 4 ore per incidenti critici |
| MTTC (Mean Time to Contain) | Tempo medio dalla rilevazione al contenimento completo | < 8 ore per incidenti critici |
| Tasso di falsi positivi | Percentuale di alert che risultano non essere minacce reali | < 30% (obiettivo: riduzione progressiva) |
| Volume alert per analista | Numero medio di alert gestiti per analista per turno | < 50 alert significativi per turno |
| Tasso di escalation | Percentuale di alert che richiedono escalation da Tier 1 a Tier 2 | 15-25% (se superiore: migliorare il training o il tuning) |
| Copertura di rilevamento MITRE ATT&CK | Percentuale di tecniche ATT&CK coperte da regole di rilevamento | > 70% per le tecniche piu' comuni |
| Dwell time | Tempo in cui un attaccante rimane non rilevato nell'ambiente | < 7 giorni (media settore 2025: ~10 giorni) |

**Dashboard operativa del SOC**

La dashboard del SOC deve fornire una vista in tempo reale delle metriche chiave:

- Pannello superiore: stato degli incidenti aperti per severita' (P1/P2/P3/P4), trend delle ultime 24/72 ore.
- Pannello centrale: volume degli alert per fonte (SIEM, EDR, IDS/IPS, WAF), tasso di falsi positivi per regola, top 10 regole piu' attivate.
- Pannello inferiore: stato di salute delle fonti di log (sistemi che non inviano log), stato degli agenti EDR, indicatori di threat intelligence (IOC attivi, campagne in corso).
- Reportistica settimanale e mensile per il management: trend degli incidenti, metriche di performance, azioni di miglioramento intraprese.

### Strumenti e Tecnologie SOC

**Stack tecnologico tipico di un SOC**

| Categoria | Strumenti | Funzione |
|-----------|-----------|----------|
| SIEM | Splunk, Microsoft Sentinel, Elastic Security, IBM QRadar, Wazuh | Raccolta log, correlazione, alerting |
| EDR/XDR | CrowdStrike Falcon, Microsoft Defender for Endpoint, SentinelOne | Rilevamento e risposta su endpoint |
| SOAR | Palo Alto Cortex XSOAR, Splunk SOAR, IBM QRadar SOAR | Automazione della risposta |
| Threat Intelligence | MISP, OpenCTI, Recorded Future, Mandiant Threat Intelligence | Informazioni sulle minacce |
| Network Detection | Zeek (Bro), Suricata, Darktrace, Vectra AI | Analisi del traffico di rete |
| Vulnerability Scanner | Tenable Nessus, Qualys VMDR, OpenVAS/Greenbone | Scansione vulnerabilita' |
| Ticketing | ServiceNow, Jira Service Management, TheHive | Gestione incidenti e workflow |

**Integrazione tra gli strumenti**

L'efficacia del SOC dipende dall'integrazione tra gli strumenti. I silos informativi rallentano l'analisi e possono causare la mancata rilevazione di attacchi multi-stadio:

- Il SIEM deve ricevere log da tutti gli strumenti di sicurezza e dall'infrastruttura.
- L'EDR deve inviare alert e telemetria al SIEM per la correlazione.
- La piattaforma di threat intelligence deve arricchire gli alert del SIEM con contesto (reputazione IP, hash di file, indicatori di campagna).
- Il SOAR deve poter interagire con tutti gli strumenti per eseguire azioni automatiche (isolamento endpoint via EDR, blocco IP via firewall, disabilitazione account via AD).
- Il sistema di ticketing deve tracciare l'intero ciclo di vita dell'incidente, dalla rilevazione alla chiusura.

---

## SIEM — Configurazione Avanzata e Gestione Log

Questa sezione approfondisce gli aspetti tecnici della configurazione SIEM e della gestione centralizzata dei log, complementando le informazioni di base presenti nella sezione Audit e Compliance.

### Architettura SIEM e Raccolta Log

**Componenti architetturali**

Un'architettura SIEM enterprise comprende tipicamente:

- **Collector/Forwarder**: agenti o servizi leggeri installati sui sistemi sorgente che raccolgono i log e li inviano al livello successivo. Esempi: Filebeat, Winlogbeat, NXLog, Fluentd, rsyslog.
- **Aggregation Layer**: livello intermedio che aggrega, filtra e normalizza i log prima dell'invio al SIEM centrale. Riduce il carico sulla rete e sul SIEM. Esempi: Logstash, Kafka, EventHub.
- **SIEM Engine**: il motore centrale che esegue l'indicizzazione, la correlazione, il matching delle regole e la generazione degli alert.
- **Storage**: archiviazione dei log indicizzati per la ricerca e l'analisi. Storage caldo (hot) per i log recenti (ricerca rapida), storage tiepido (warm) per i log meno recenti, storage freddo (cold) per l'archiviazione a lungo termine.
- **Presentation Layer**: interfaccia web per dashboard, ricerche, report e gestione degli incidenti.

**Configurazione della raccolta log — esempi pratici**

Configurazione rsyslog per l'invio centralizzato (Linux):

```bash
# /etc/rsyslog.d/50-remote.conf
# Inviare tutti i log di sicurezza al SIEM centrale via TCP con TLS
$DefaultNetstreamDriverCAFile /etc/ssl/certs/siem-ca.pem
$DefaultNetstreamDriverCertFile /etc/ssl/certs/client-cert.pem
$DefaultNetstreamDriverKeyFile /etc/ssl/private/client-key.pem
$ActionSendStreamDriver gtls
$ActionSendStreamDriverMode 1
$ActionSendStreamDriverAuthMode x509/name
$ActionSendStreamDriverPermittedPeer siem.azienda.local

# Inviare auth, authpriv e tutti i log di severita' warning o superiore
auth,authpriv.*    @@siem.azienda.local:6514
*.warn             @@siem.azienda.local:6514
```

Configurazione Windows Event Forwarding (WEF):

```xml
<!-- Subscription per eventi di sicurezza critici -->
<Subscription xmlns="http://schemas.microsoft.com/2006/03/windows/events/subscription">
  <SubscriptionId>SecurityEvents</SubscriptionId>
  <SubscriptionType>SourceInitiated</SubscriptionType>
  <Description>Raccolta eventi sicurezza per SIEM</Description>
  <Enabled>true</Enabled>
  <Uri>http://schemas.microsoft.com/wbem/wsman/1/windows/EventLog</Uri>
  <Query>
    <![CDATA[
      <QueryList>
        <Query Id="0" Path="Security">
          <!-- Logon/Logoff -->
          <Select>*[System[(EventID=4624 or EventID=4625 or EventID=4634 or EventID=4648)]]</Select>
          <!-- Account Management -->
          <Select>*[System[(EventID=4720 or EventID=4722 or EventID=4723 or EventID=4724 or EventID=4725 or EventID=4726)]]</Select>
          <!-- Privilege Use -->
          <Select>*[System[(EventID=4672 or EventID=4673)]]</Select>
          <!-- Policy Change -->
          <Select>*[System[(EventID=4719 or EventID=4739)]]</Select>
        </Query>
        <Query Id="1" Path="System">
          <!-- Service Installation -->
          <Select>*[System[(EventID=7045)]]</Select>
        </Query>
        <Query Id="2" Path="Microsoft-Windows-PowerShell/Operational">
          <!-- PowerShell Script Block Logging -->
          <Select>*[System[(EventID=4104)]]</Select>
        </Query>
      </QueryList>
    ]]>
  </Query>
</Subscription>
```

### Normalizzazione e Parsing dei Log

**Importanza della normalizzazione**

I log provengono da fonti eterogenee con formati diversi (syslog, CEF, JSON, XML, testo libero). Senza normalizzazione, la correlazione tra fonti diverse e' impossibile. La normalizzazione converte i log in un formato comune con campi standardizzati.

**Schema di normalizzazione raccomandato**

Utilizzare uno schema standard come l'Elastic Common Schema (ECS) o l'Open Cybersecurity Schema Framework (OCSF):

| Campo normalizzato | Descrizione | Esempio |
|-------------------|-------------|---------|
| @timestamp | Timestamp dell'evento in UTC ISO 8601 | 2026-05-24T14:30:00.000Z |
| event.category | Categoria dell'evento | authentication, network, process |
| event.action | Azione specifica | logon-success, logon-failed, file-created |
| event.severity | Severita' normalizzata (0-4) | 3 (high) |
| source.ip | Indirizzo IP sorgente | 192.168.1.100 |
| destination.ip | Indirizzo IP destinazione | 10.0.1.50 |
| user.name | Nome utente | mario.rossi |
| host.name | Nome host sorgente | SRV-WEB-01 |
| process.name | Nome del processo | sshd, cmd.exe |
| file.hash.sha256 | Hash SHA256 del file | a1b2c3... |

**Validazione della qualita' dei dati**

Implementare controlli regolari sulla qualita' dei log ingeriti:

- Monitorare il volume di log per sorgente: un calo improvviso puo' indicare un problema di raccolta (agente fermo, errore di rete) o un attaccante che ha disabilitato il logging.
- Verificare la completezza dei campi: i campi critici (timestamp, source IP, user) devono essere presenti nella maggior parte degli eventi. Percentuali elevate di campi vuoti indicano problemi di parsing.
- Controllare il ritardo di ingestione (lag): il tempo tra la generazione dell'evento e la sua disponibilita' nel SIEM. Un ritardo superiore a 5 minuti per le fonti critiche e' da investigare.

### Regole di Rilevamento e Casi d'Uso

**Strutturazione dei casi d'uso di rilevamento**

Ogni regola di rilevamento deve essere documentata come un caso d'uso strutturato:

```
Caso d'uso: Rilevamento accesso con credenziali compromesse
ID: UC-AUTH-003
Fase MITRE ATT&CK: Initial Access (TA0001) — Valid Accounts (T1078)
Sorgenti dati: Log Active Directory (Event ID 4624, 4625), VPN log, proxy log
Logica: Autenticazione riuscita da un IP che nei 30 giorni precedenti non e' mai
        stato utilizzato dall'utente, combinata con almeno uno dei seguenti:
        - L'IP e' in una lista di reputazione negativa (threat intelligence)
        - L'orario di accesso e' fuori dall'orario lavorativo abituale dell'utente
        - L'accesso avviene da una geolocalizzazione incompatibile con l'ultima
          posizione nota (impossible travel)
Soglia: singola occorrenza
Severita': Alta
Azione: Notifica Tier 2, verifica con l'utente, se non confermato → reset password,
        verifica sessioni attive, analisi log per attivita' post-accesso
Falsi positivi attesi: viaggi di lavoro, uso VPN personale, cambio provider Internet
Tuning: whitelist IP aziendali noti, aggiungere eccezioni per utenti con mobilita'
        documentata
```

**Regole di rilevamento essenziali — catalogo base**

Oltre alle regole di correlazione gia' descritte nella sezione Audit e Compliance, un SOC dovrebbe implementare le seguenti regole aggiuntive:

- **Esecuzione di strumenti di attacco noti**: rilevare l'esecuzione di tool come Mimikatz, BloodHound, Cobalt Strike, Impacket, PsExec in contesti non autorizzati. Basarsi su nome processo, hash, linea di comando e comportamento.
- **Living-off-the-Land (LOtL)**: rilevare l'uso sospetto di strumenti legittimi del sistema operativo per fini malevoli (PowerShell con script codificati in Base64, certutil per il download di file, mshta per l'esecuzione di script remoti, wmic per l'esecuzione remota).
- **Modifica dei log di sicurezza**: rilevare tentativi di cancellazione o modifica dei log di sicurezza (Event ID 1102 su Windows — audit log cleared).
- **Creazione di account anomala**: creazione di account utente fuori dal processo standard (account creato direttamente sulla macchina locale, account creato da un processo non standard).
- **Movimenti laterali via protocolli di gestione**: connessioni RDP, SSH, WinRM, WMI anomale (sorgente non autorizzata, orario insolito, account non previsto).
- **Esfiltrazione dati**: volume anomalo di upload verso servizi cloud esterni (Dropbox, Google Drive, OneDrive personale), connessioni a servizi di file sharing non autorizzati, traffico DNS con entropia elevata (DNS tunneling).
- **Persistenza**: creazione di servizi Windows, task pianificati, chiavi di registro Run/RunOnce, modifiche a crontab da processi non autorizzati.

**Formato Sigma per regole portatili**

Il formato Sigma permette di scrivere regole di rilevamento indipendenti dalla piattaforma SIEM, convertibili automaticamente per Splunk, Elastic, Microsoft Sentinel e altri:

```yaml
title: Suspicious PowerShell Encoded Command
id: f3a0d56e-8b1c-4d2f-9e3a-7c5b8d6e1234
status: stable
description: Rilevamento esecuzione PowerShell con comando codificato Base64
references:
  - https://attack.mitre.org/techniques/T1059/001/
logsource:
  category: process_creation
  product: windows
detection:
  selection:
    Image|endswith: '\powershell.exe'
    CommandLine|contains:
      - '-enc '
      - '-EncodedCommand '
      - '-ec '
  condition: selection
falsepositives:
  - Script di automazione legittimi che usano encoding
  - Strumenti di gestione remota configurati con encoded commands
level: high
tags:
  - attack.execution
  - attack.t1059.001
```

### Gestione del Volume e Retention Avanzata

**Strategia di tiering dello storage**

Per gestire il volume dei log in modo economicamente sostenibile senza sacrificare la capacita' di analisi:

| Tier | Periodo | Tipo Storage | Velocita' Ricerca | Uso |
|------|---------|-------------|-------------------|-----|
| Hot | 0-30 giorni | SSD / storage ad alte prestazioni | < 5 secondi | Analisi in tempo reale, incident response |
| Warm | 30-90 giorni | HDD / storage standard | < 30 secondi | Investigazioni, threat hunting |
| Cold | 90 giorni - 1 anno | Object storage (S3, Azure Blob) | Minuti | Compliance, analisi storiche |
| Frozen | 1-7 anni | Archive storage / tape | Ore | Requisiti normativi, analisi forensi rare |

**Filtraggio e riduzione del volume**

Non tutti i log hanno lo stesso valore per la sicurezza. Applicare filtri intelligenti per ridurre il volume senza perdere visibilita':

- Eliminare i log di debug e informativi non rilevanti per la sicurezza (es. heartbeat di monitoraggio, log di performance applicativa puri).
- Aggregare eventi ripetitivi: anziche' conservare ogni singolo pacchetto bloccato dal firewall, aggregare per sorgente/destinazione/porta con conteggio e timestamp primo/ultimo.
- Conservare i log grezzi (raw) delle sorgenti critiche (autenticazione, accesso privilegiato, modifiche di sistema) e solo i log aggregati o filtrati per le sorgenti a basso valore di sicurezza.
- Stimare il volume giornaliero per sorgente e monitorare i trend: un aumento improvviso puo' indicare un problema (log flooding, attacco, misconfiguration) o un'opportunita' di ottimizzazione.

---

## Threat Hunting e Risposta agli Incidenti

Il threat hunting e la risposta agli incidenti rappresentano le capacita' proattive e reattive del SOC. Il threat hunting cerca attivamente minacce non rilevate dai sistemi automatici, mentre la risposta agli incidenti gestisce le minacce confermate attraverso un processo strutturato.

### Programma di Threat Hunting

Il threat hunting e' l'attivita' proattiva di ricerca di minacce che hanno eluso i controlli automatici di rilevamento. A differenza del monitoraggio reattivo basato su alert, il threat hunting parte da ipotesi formulate dagli analisti e utilizza tecniche di analisi avanzata per identificare attivita' malevole nascoste.

**Metodologia di threat hunting**

1. **Formulazione dell'ipotesi**: basata su threat intelligence (nuove campagne di attacco, TTP osservate in organizzazioni simili), analisi delle lacune di rilevamento (tecniche MITRE ATT&CK non coperte da regole), o intuizione dell'analista basata su anomalie osservate.
2. **Raccolta e analisi dei dati**: interrogazione del SIEM, analisi dei log grezzi, esame della telemetria EDR, analisi del traffico di rete. L'analista cerca pattern, anomalie e indicatori coerenti con l'ipotesi.
3. **Validazione dei risultati**: ogni anomalia trovata viene analizzata per determinare se e' un vero indicatore di compromissione (IOC) o un comportamento legittimo non documentato.
4. **Documentazione e azione**: se la minaccia e' confermata, attivare il piano di risposta agli incidenti. Se l'ipotesi non e' confermata, documentare i risultati (negativi inclusi) per riferimento futuro.
5. **Miglioramento continuo**: ogni sessione di hunting deve produrre raccomandazioni per nuove regole di rilevamento, miglioramenti alla visibilita' (nuove fonti di log) o correzioni di configurazione.

**Tecniche di hunting basate su MITRE ATT&CK**

Il framework MITRE ATT&CK fornisce una tassonomia strutturata delle tecniche di attacco, organizzata per tattiche (obiettivi dell'attaccante) e tecniche (metodi utilizzati). Utilizzare ATT&CK per strutturare le sessioni di hunting:

- **Initial Access (TA0001)**: cercare connessioni da IP/domini con bassa reputazione, allegati email sospetti non rilevati dall'antispam, utilizzo di credenziali valide da posizioni anomale.
- **Execution (TA0002)**: cercare esecuzioni di PowerShell con parametri sospetti, utilizzo di mshta/cscript/wscript, macro Office che lanciano processi figlio insoliti.
- **Persistence (TA0003)**: verificare modifiche a chiavi di registro di avvio automatico, nuovi servizi creati, task pianificati anomali, DLL hijacking.
- **Privilege Escalation (TA0004)**: cercare tentativi di exploit di vulnerabilita' locali, creazione di token con privilegi elevati, bypass UAC.
- **Defense Evasion (TA0005)**: cercare processi che disabilitano strumenti di sicurezza, utilizzo di process injection, timestomping su file.
- **Credential Access (TA0006)**: cercare accessi anomali al file SAM/NTDS.dit, dumping della memoria LSASS, attacchi Kerberoasting.
- **Lateral Movement (TA0008)**: cercare connessioni RDP/SMB/WinRM tra sistemi che normalmente non comunicano, pass-the-hash, pass-the-ticket.
- **Exfiltration (TA0010)**: cercare volumi anomali di traffico in uscita, compressione di grandi quantita' di file, utilizzo di canali di comunicazione alternativi (DNS, ICMP).

**Cadenza e reportistica del threat hunting**

- Frequenza raccomandata: almeno una sessione di hunting strutturata a settimana, focalizzata su una specifica ipotesi o tecnica ATT&CK.
- Ogni sessione deve produrre un report con: ipotesi testata, dati analizzati, risultati (positivi o negativi), raccomandazioni, tempo impiegato.
- Tracciare la copertura cumulativa delle tecniche ATT&CK investigate nel tempo. L'obiettivo e' coprire le tecniche piu' comuni e rilevanti per il settore dell'organizzazione almeno una volta ogni trimestre.

### Piano di Risposta agli Incidenti (IRP)

Il Piano di Risposta agli Incidenti (Incident Response Plan — IRP) definisce le procedure, i ruoli e le responsabilita' per gestire gli incidenti di sicurezza in modo strutturato ed efficace. Il piano deve essere documentato, approvato dal management, distribuito a tutto il personale coinvolto e testato regolarmente.

**Fasi della risposta agli incidenti (modello NIST SP 800-61r3)**

Il NIST Cybersecurity Framework aggiornato al 2025 (SP 800-61 revisione 3) definisce quattro fasi interconnesse:

**Fase 1 — Preparazione**

- Formazione del CSIRT (Computer Security Incident Response Team) con ruoli e responsabilita' definiti: incident commander, analisti, comunicazione, legale, management.
- Predisposizione degli strumenti: kit forense (write blocker, supporti di acquisizione, software di analisi), accesso al SIEM, EDR e firewall con credenziali dedicate, canali di comunicazione out-of-band (telefono, chat cifrata — non dipendere dai sistemi potenzialmente compromessi).
- Documentazione: playbook per i principali scenari di incidente (ransomware, data breach, compromissione account, DDoS, insider threat), checklist operative, contatti di emergenza (interni ed esterni).
- Relazioni con entita' esterne: accordi con fornitori di incident response (retainer), contatti con le forze dell'ordine (Polizia Postale), contatti con il CSIRT nazionale (CSIRT Italia), consulente legale specializzato in cybersecurity.

**Fase 2 — Rilevamento e Analisi**

- Identificazione dell'incidente attraverso alert SIEM, segnalazioni utenti, notifiche esterne (threat intelligence, CERT, vendor).
- Classificazione della severita' secondo la matrice definita nel piano.
- Analisi iniziale: determinare il vettore di attacco, l'estensione della compromissione, i sistemi e i dati coinvolti.
- Documentazione di tutte le attivita' con timestamp UTC ISO 8601. Ogni azione intrapresa durante la risposta deve essere registrata.

**Fase 3 — Contenimento, Eradicazione e Ripristino**

- **Contenimento a breve termine**: azioni immediate per limitare il danno senza distruggere le evidenze (isolamento dell'endpoint dalla rete mantenendolo acceso, blocco dell'account compromesso, blocco dell'IP attaccante sul firewall).
- **Contenimento a lungo termine**: azioni piu' strutturate (segmentazione della rete per isolare il segmento compromesso, applicazione di patch di emergenza, reimpostazione delle credenziali potenzialmente compromesse).
- **Eradicazione**: rimozione completa della minaccia dall'ambiente (eliminazione del malware, chiusura delle backdoor, rimozione degli account creati dall'attaccante, bonifica dei sistemi compromessi — in caso di compromissione profonda, ricostruzione completa del sistema da immagine pulita).
- **Ripristino**: ritorno alla normale operativita' (ripristino dei servizi in ordine di criticita' di business, monitoraggio intensivo dei sistemi ripristinati per 72-96 ore, verifica dell'integrita' dei dati ripristinati).

**Fase 4 — Attivita' Post-Incidente**

- **Lessons learned meeting**: riunione entro 5 giorni lavorativi dalla chiusura dell'incidente con tutti i soggetti coinvolti. Analizzare: cosa ha funzionato, cosa non ha funzionato, cosa si sarebbe potuto fare meglio, quali controlli devono essere aggiunti o migliorati.
- **Report dell'incidente**: documento strutturato con timeline dell'attacco, azioni intraprese, impatto (tecnico e di business), causa radice, raccomandazioni.
- **Aggiornamento dei controlli**: implementare le raccomandazioni emerse (nuove regole SIEM, hardening aggiuntivo, modifiche alla segmentazione, aggiornamento dei playbook).
- **Aggiornamento degli indicatori**: alimentare la piattaforma di threat intelligence interna con gli IOC dell'incidente (IP, domini, hash, TTP).

### SOAR — Automazione della Risposta

Le piattaforme SOAR (Security Orchestration, Automation and Response) automatizzano le attivita' ripetitive di risposta agli incidenti, riducendo il tempo di risposta e il carico sugli analisti.

**Playbook di automazione — esempi pratici**

**Playbook: Phishing email segnalata dall'utente**

```
Trigger: Email segnalata dall'utente tramite pulsante "Report Phishing"

Azioni automatiche:
1. Estrarre gli indicatori dall'email (mittente, URL, allegati, header)
2. Verificare gli URL contro servizi di reputazione (VirusTotal, URLhaus)
3. Verificare gli allegati in sandbox (detonazione in ambiente isolato)
4. Verificare il mittente contro la lista dei mittenti bloccati
5. Se malevolo confermato:
   a. Cercare e rimuovere l'email da tutte le caselle aziendali
   b. Bloccare il mittente e i domini/URL malevoli
   c. Verificare se qualcuno ha cliccato sul link (log del proxy)
   d. Se qualcuno ha cliccato: escalation a Tier 2, scansione EDR
      dell'endpoint, reset password dell'utente
6. Notificare l'utente segnalante dell'esito
7. Aggiornare le statistiche del programma di phishing awareness

Azione umana richiesta: solo se l'analisi automatica e' inconclusiva
Tempo stimato (automatico): < 5 minuti
Tempo stimato (manuale): 30-45 minuti
```

**Playbook: Endpoint con alert EDR critico**

```
Trigger: Alert EDR con severita' critica (ransomware detection,
         lateral movement)

Azioni automatiche:
1. Arricchire l'alert con informazioni sull'endpoint (proprietario,
   criticita', ultimo patch, software installato)
2. Verificare gli IOC associati contro threat intelligence
3. Isolare l'endpoint dalla rete tramite EDR (containment)
4. Acquisire snapshot della memoria e dei processi in esecuzione
5. Notificare il SOC Tier 2 con tutte le informazioni raccolte
6. Creare ticket di incidente con severita' P1

Azione umana richiesta: analisi dell'alert, decisione su eradicazione
                         e ripristino
```

**Criteri per l'automazione**

Non tutto puo' o deve essere automatizzato. Criteri per decidere cosa automatizzare:

- **Automatizzare**: azioni ripetitive con logica binaria (malware si/no), arricchimento dati (lookup IP/hash/dominio), azioni di contenimento reversibili (isolamento endpoint, blocco IP temporaneo), notifiche e creazione ticket.
- **Non automatizzare**: decisioni che richiedono contesto di business (questo server puo' essere isolato senza impatto critico?), azioni irreversibili (cancellazione di dati, revoca permanente di accessi), comunicazioni verso l'esterno (notifica al Garante, comunicazione ai media).

---

## Sicurezza Fisica e Ambientale

La sicurezza fisica e' spesso sottovalutata in un contesto IT, ma rappresenta un pilastro fondamentale della defense-in-depth. Un attaccante con accesso fisico a un server puo' bypassare la maggior parte dei controlli logici. La sicurezza fisica protegge l'infrastruttura IT da accessi non autorizzati, danneggiamenti, furti e minacce ambientali.

### Controllo Accessi Fisici

**Modello a zone concentriche**

La sicurezza fisica si implementa attraverso zone concentriche con livelli di protezione crescenti:

| Zona | Descrizione | Controlli |
|------|-------------|-----------|
| Zona 0 — Perimetro esterno | Area esterna all'edificio | Recinzione, illuminazione, videosorveglianza perimetrale, controllo veicolare |
| Zona 1 — Edificio | Area comune dell'edificio | Porta d'ingresso con controllo accessi (badge), reception con verifica visitatori |
| Zona 2 — Area riservata IT | Uffici e locali IT | Badge + PIN o biometria, videosorveglianza, registrazione accessi |
| Zona 3 — Data center / sala server | Locali critici | Badge + biometria + mantrap, videosorveglianza continua, accompagnamento visitatori |
| Zona 4 — Rack/cabinet | Singoli armadi server | Serratura individuale con chiave registrata, sensori di apertura |

**Gestione badge e credenziali fisiche**

- Ogni badge deve essere associato a una singola persona (mai condividere badge).
- Disattivare immediatamente i badge di dipendenti uscenti, contrattisti con contratto scaduto e badge smarriti/rubati.
- Revisione trimestrale degli accessi fisici: verificare che ogni persona abbia accesso solo alle zone necessarie per il proprio ruolo.
- Implementare anti-passback: il sistema impedisce l'utilizzo dello stesso badge per due ingressi consecutivi senza una uscita intermedia (previene il "tailgating" tramite badge condiviso).
- Registrare e conservare i log di accesso fisico per almeno 12 mesi.

**Gestione visitatori**

- Tutti i visitatori devono essere registrati (nome, cognome, azienda, documento di identita', orario di ingresso/uscita, persona di riferimento).
- I visitatori devono indossare un badge visitatore visibile con la zona di accesso autorizzata.
- I visitatori non possono accedere a Zona 3 e Zona 4 senza accompagnamento di un dipendente autorizzato.
- I badge visitatore devono essere restituiti all'uscita e disattivati automaticamente a fine giornata.

### Protezione Data Center e Locali Tecnici

**Controlli ambientali**

- **Temperatura**: mantenere la temperatura nella sala server tra 18°C e 27°C (raccomandazione ASHRAE). Monitoraggio continuo con sensori e alert per deviazioni.
- **Umidita'**: mantenere l'umidita' relativa tra 40% e 60%. Umidita' troppo bassa aumenta il rischio di scariche elettrostatiche, troppo alta causa condensa e corrosione.
- **Rilevamento allagamenti**: installare sensori di allagamento sotto il pavimento rialzato e vicino a tubazioni idriche.
- **Sistema antincendio**: sistemi di rilevamento fumo a campionamento d'aria (VESDA) per la rilevazione precoce, sistema di spegnimento a gas inerte (FM-200, Novec 1230) per le sale server (mai acqua o polvere chimica su apparecchiature elettroniche attive).
- **Alimentazione elettrica**: UPS (Uninterruptible Power Supply) dimensionato per mantenere il carico critico per almeno 15-30 minuti, generatore diesel con autonomia di almeno 24 ore, test mensile del generatore con carico.

**Sicurezza del cablaggio**

- I cavi di rete devono passare attraverso percorsi protetti (canaline chiuse, pavimento rialzato con pannelli rimovibili solo con utensili).
- Etichettare ogni cavo con entrambe le terminazioni per facilitare la tracciabilita'.
- Le porte di rete non utilizzate devono essere disabilitate a livello di switch (port security) per prevenire la connessione di dispositivi non autorizzati.
- Separare fisicamente i cavi di rete dai cavi elettrici per evitare interferenze elettromagnetiche.

### Integrazione Sicurezza Fisica e Logica

**Correlazione eventi fisici e logici**

L'integrazione tra i sistemi di sicurezza fisica e logica permette di rilevare scenari di attacco avanzati:

- **Accesso logico senza accesso fisico**: un utente si autentica su un server nel data center, ma il sistema di controllo accessi fisici non registra il suo ingresso nella sala server. Possibile compromissione delle credenziali.
- **Accesso fisico senza accesso logico**: un badge accede alla sala server, ma nessun accesso logico viene registrato sui sistemi. Possibile attivita' non autorizzata (accesso all'hardware, installazione di dispositivi).
- **Orari incompatibili**: un badge accede all'edificio alle 3:00 di notte, ma l'utente non ha ragioni documentate per essere presente fuori orario. Generare alert per verificare.

Configurare regole di correlazione nel SIEM che combinino i log del sistema di controllo accessi fisici con i log di autenticazione logica per rilevare queste anomalie.

---

## Formazione e Consapevolezza sulla Sicurezza

Il fattore umano rimane il vettore di attacco piu' sfruttato. Le tecnologie di sicurezza piu' avanzate possono essere vanificate da un singolo utente che clicca su un link di phishing o comunica le proprie credenziali a un attaccante. Un programma di security awareness efficace riduce significativamente il rischio legato al comportamento umano.

### Programma di Security Awareness

**Struttura del programma annuale**

Un programma di formazione sulla sicurezza deve essere continuo, non limitato a un singolo evento annuale:

| Frequenza | Attivita' | Destinatari | Durata |
|-----------|----------|-------------|--------|
| All'assunzione | Formazione iniziale sulla sicurezza | Tutti i nuovi assunti | 2 ore |
| Mensile | Newsletter/comunicazione su minacce attuali | Tutti i dipendenti | 5 minuti di lettura |
| Mensile | Simulazione di phishing | Tutti i dipendenti | N/A (test) |
| Trimestrale | Microlearning interattivo su un tema specifico | Tutti i dipendenti | 15-20 minuti |
| Semestrale | Formazione approfondita sulla sicurezza | Tutti i dipendenti | 1 ora |
| Annuale | Formazione avanzata per ruoli specifici | IT, management, finanza, HR | 2-4 ore |
| Continuo | Intervento formativo dopo incidente o simulazione fallita | Utenti coinvolti | 10-15 minuti |

**Contenuti del programma base**

- Riconoscimento di email di phishing, smishing (SMS) e vishing (telefono): indicatori chiave (urgenza, errori grammaticali, mittente sospetto, URL mascherati), procedure di segnalazione.
- Gestione sicura delle password: utilizzo di password manager, non riutilizzare le password, riconoscere i tentativi di social engineering mirati alla raccolta di credenziali.
- Sicurezza dei dispositivi mobili e del lavoro remoto: cifratura, VPN obbligatoria, non utilizzare reti Wi-Fi pubbliche non protette, blocco automatico dello schermo.
- Classificazione e gestione dei dati sensibili: cosa sono i dati personali (GDPR), cosa sono i dati riservati aziendali, come trattarli (cifratura, canali sicuri, clean desk policy).
- Segnalazione degli incidenti di sicurezza: a chi segnalare, cosa segnalare, importanza della segnalazione tempestiva (meglio un falso allarme che un incidente non segnalato).
- Sicurezza fisica: non tenere aperte le porte di sicurezza (tailgating), non lasciare documenti sensibili sulla scrivania, bloccare il computer quando ci si allontana.

### Simulazioni di Phishing

Le simulazioni di phishing misurano la resilienza dell'organizzazione agli attacchi di social engineering e identificano gli utenti che necessitano di formazione aggiuntiva.

**Progettazione delle simulazioni**

- Utilizzare scenari realistici basati su attacchi reali osservati nel settore dell'organizzazione. Mai utilizzare scenari banali che tutti riconoscono immediatamente (non c'e' valore di test).
- Variare i canali: email di phishing classica, spear phishing personalizzato (utilizzando informazioni reali dell'organizzazione), smishing via SMS, vishing via telefono.
- Variare la difficolta': includere simulazioni semplici (errori evidenti) e difficili (email quasi indistinguibili da comunicazioni legittime) per misurare la capacita' a diversi livelli.
- Frequenza raccomandata: almeno una simulazione al mese, con scenari diversi.
- Tempistica: variare il giorno e l'ora dell'invio per simulare le diverse condizioni di attenzione (prima cosa al mattino, dopo pranzo, venerdi' pomeriggio).

**Metriche delle simulazioni**

| Metrica | Descrizione | Obiettivo |
|---------|-------------|-----------|
| Click rate | Percentuale di utenti che cliccano sul link malevolo | < 5% (media settore 2025: ~10-15%) |
| Submission rate | Percentuale di utenti che inseriscono credenziali | < 2% |
| Report rate | Percentuale di utenti che segnalano la simulazione | > 60% |
| Time to first click | Tempo dal ricevimento al primo click | Indicatore di impulsivita' |
| Time to first report | Tempo dal ricevimento alla prima segnalazione | < 10 minuti |
| Repeat offenders | Utenti che falliscono piu' di 2 simulazioni consecutive | < 3% (questi utenti richiedono intervento individuale) |

**Gestione etica delle simulazioni**

- Informare i dipendenti che le simulazioni di phishing fanno parte del programma di sicurezza (senza specificare date e contenuti).
- Utilizzare un approccio educativo, non punitivo: chi clicca riceve una formazione aggiuntiva, non una sanzione. L'obiettivo e' il cambiamento comportamentale.
- Non utilizzare esche emotive eccessive (simulazioni di licenziamento, emergenze sanitarie dei familiari) che possano danneggiare il rapporto di fiducia con i dipendenti.
- Rispettare la privacy: le metriche aggregate sono condivise con il management, i risultati individuali sono noti solo al team di sicurezza e vengono utilizzati esclusivamente per interventi formativi mirati.

### Formazione Specifica per Ruolo

**Formazione per il personale IT**

- Secure coding practices (per gli sviluppatori): OWASP Top 10, input validation, gestione sicura delle sessioni, protezione delle API.
- Hardening e configurazione sicura: CIS Benchmarks, principi di minimo privilegio, gestione sicura delle credenziali.
- Riconoscimento delle tecniche di attacco avanzate: social engineering mirato al personale IT (pretexting, impersonation di vendor), attacchi alla supply chain software.
- Risposta agli incidenti: ruoli e procedure del CSIRT, acquisizione forense delle evidenze, gestione della comunicazione durante un incidente.

**Formazione per il management**

- Rischio cyber come rischio di business: impatto finanziario, reputazionale e legale degli incidenti di sicurezza.
- Responsabilita' legali: obblighi NIS2, GDPR (notifica entro 72 ore), responsabilita' degli amministratori.
- Business email compromise (BEC): riconoscimento delle email fraudolente che simulano dirigenti o fornitori per richiedere trasferimenti di denaro o informazioni sensibili.
- Decisioni durante gli incidenti: quando e come comunicare con clienti, media e autorita'.

**Formazione per il personale finanziario**

- Riconoscimento delle frodi BEC e delle fatture fraudolente.
- Procedure di verifica per bonifici superiori a una soglia definita (doppia autorizzazione, verifica telefonica con il richiedente tramite numero noto, non tramite il numero indicato nell'email).
- Protezione dei dati finanziari: cifratura, accesso limitato, audit trail completo.

---

## Patch Management Operativo

Il patch management operativo va oltre la semplice installazione degli aggiornamenti e comprende l'intero ciclo di vita del patching, dalla valutazione alla verifica post-installazione. Questa sezione approfondisce gli aspetti operativi del processo, complementando le informazioni sulla gestione delle vulnerabilita' presenti nella sezione Sicurezza Endpoint.

### Ciclo di Vita del Patch

**Processo strutturato di patch management**

1. **Monitoraggio e identificazione**: monitorare le fonti di informazione sulle vulnerabilita' e sui rilasci di patch:
   - Bollettini di sicurezza dei vendor (Microsoft Patch Tuesday, Oracle Critical Patch Update, advisory di Red Hat/Ubuntu/SUSE).
   - Database nazionali delle vulnerabilita' (NVD, CERT nazionale italiano).
   - Feed di threat intelligence per vulnerabilita' attivamente sfruttate (CISA KEV — Known Exploited Vulnerabilities catalog).
   - Mailing list di sicurezza (oss-security, Full Disclosure, vendor-specific).

2. **Valutazione e prioritizzazione**: per ogni patch disponibile, valutare:
   - Severita' della vulnerabilita' corretta (CVSS base score + contesto ambientale).
   - Disponibilita' di exploit pubblici e sfruttamento attivo in the wild.
   - Sistemi aziendali interessati e loro criticita' per il business.
   - Requisiti di compatibilita' e potenziali impatti (la patch potrebbe rompere un'applicazione?).
   - Classificazione: emergenza (deploy entro 24-72 ore), critica (deploy entro 7 giorni), standard (deploy nel prossimo ciclo di manutenzione), differibile (deploy a discrezione).

3. **Test pre-deployment**: testare la patch in un ambiente di staging che replica la produzione:
   - Verificare l'installazione corretta della patch.
   - Testare le applicazioni critiche che girano sui sistemi patchati.
   - Verificare le prestazioni post-patch (regressioni).
   - Per le patch classificate come emergenza, il test puo' essere abbreviato ma non eliminato. Documentare il rischio residuo accettato.

4. **Deployment pianificato**: distribuire la patch seguendo un approccio graduale:
   - Ring 0 — Sistemi di test e pilota (5% degli endpoint): deploy immediato, monitoraggio intensivo per 24 ore.
   - Ring 1 — Sistemi non critici e early adopters (20%): deploy dopo 24 ore di osservazione positiva su Ring 0.
   - Ring 2 — Sistemi di produzione standard (50%): deploy dopo 48 ore di osservazione positiva su Ring 1.
   - Ring 3 — Sistemi critici e server di produzione (25%): deploy nella finestra di manutenzione pianificata, dopo conferma positiva da tutti i ring precedenti.

5. **Verifica post-deployment**: confermare il successo dell'installazione:
   - Verificare che la patch sia effettivamente installata (non solo che il processo di installazione sia stato avviato).
   - Ripetere la scansione di vulnerabilita' sui sistemi patchati per confermare che la vulnerabilita' sia risolta.
   - Monitorare i sistemi per anomalie nelle 48 ore successive.
   - Documentare il risultato del ciclo di patching con metriche (sistemi patchati, fallimenti, eccezioni).

### Automazione del Patching

**Strumenti di automazione**

| Strumento | Piattaforme | Caratteristiche |
|-----------|-------------|-----------------|
| WSUS / Microsoft Endpoint Configuration Manager | Windows | Nativo Microsoft, integrazione con AD, approvazione manuale o automatica |
| Ansible + apt/yum | Linux | Agentless, playbook personalizzabili, idempotente, adatto a IaC |
| Ivanti Patch Management | Windows, Linux, macOS | Ampio database di patch third-party, prioritizzazione basata su rischio |
| ManageEngine Patch Manager Plus | Windows, Linux, macOS | Supporto third-party esteso, reportistica dettagliata |
| Automox | Windows, Linux, macOS | Cloud-native, policy-based, zero-touch patching |

**Esempio di playbook Ansible per il patching Linux**

```yaml
---
# playbook: patch_linux_servers.yml
# Descrizione: Applicazione patch di sicurezza ai server Linux con verifica
- name: Patching di sicurezza server Linux
  hosts: linux_servers
  become: true
  serial: "25%"  # Deploy a gruppi del 25% per ridurre il rischio
  max_fail_percentage: 10  # Interrompere se piu' del 10% fallisce

  pre_tasks:
    - name: Creare snapshot/backup pre-patch
      command: "lvcreate -L 10G -s -n pre_patch_snap /dev/vg0/root"
      ignore_errors: true

    - name: Verificare spazio disco disponibile
      assert:
        that: ansible_mounts | selectattr('mount','eq','/') |
              map(attribute='size_available') | first > 2147483648
        fail_msg: "Spazio disco insufficiente per il patching (< 2GB)"

  tasks:
    - name: Aggiornare la cache dei pacchetti
      apt:
        update_cache: true
        cache_valid_time: 3600
      when: ansible_os_family == "Debian"

    - name: Installare solo aggiornamenti di sicurezza
      apt:
        upgrade: dist
        default_release: "{{ ansible_distribution_release }}-security"
      when: ansible_os_family == "Debian"
      register: apt_result

    - name: Verificare se e' necessario un riavvio
      stat:
        path: /var/run/reboot-required
      register: reboot_required

    - name: Riavviare se necessario (con attesa)
      reboot:
        reboot_timeout: 300
        msg: "Riavvio per applicazione patch di sicurezza"
      when: reboot_required.stat.exists

  post_tasks:
    - name: Verificare che i servizi critici siano attivi
      service_facts:

    - name: Assert servizi critici in esecuzione
      assert:
        that: ansible_facts.services[item].state == 'running'
        fail_msg: "Servizio {{ item }} non in esecuzione dopo il patching"
      loop:
        - sshd.service
        - rsyslog.service
```

### Gestione delle Eccezioni e Rollback

**Procedura di eccezione al patching**

Quando una patch non puo' essere applicata (incompatibilita' applicativa, sistema legacy, vincoli vendor), il processo di eccezione deve essere formalizzato:

- Documentare: sistema interessato, vulnerabilita' non corretta (CVE), motivo dell'eccezione, data di richiesta, richiedente.
- Valutare e documentare le contromisure compensative (segmentazione di rete aggiuntiva, monitoraggio rafforzato, regole WAF/IPS specifiche, disabilitazione della funzionalita' vulnerabile se possibile).
- Approvazione da parte del risk owner (responsabile di business) e del responsabile della sicurezza.
- Durata massima dell'eccezione: 90 giorni, dopo i quali deve essere rivalutata.
- Tracciamento centralizzato di tutte le eccezioni attive con dashboard di monitoraggio.

**Procedura di rollback**

Quando una patch causa problemi in produzione:

1. Determinare l'impatto: il problema interessa un singolo sistema o e' diffuso?
2. Se il problema e' critico (servizio non disponibile): procedere immediatamente al rollback.
3. Metodi di rollback: ripristino da snapshot/backup pre-patch, disinstallazione della patch (se supportato dal sistema operativo), ripristino dell'immagine da backup.
4. Dopo il rollback, documentare il problema e aprire un caso con il vendor per ottenere una versione corretta della patch.
5. Riapplicare le contromisure compensative fino a quando una patch funzionante non e' disponibile.

---

## Controllo Accessi Avanzato — ABAC e Zero Trust

Questa sezione estende i concetti di gestione accessi presentati nella sezione Gestione Accessi con modelli avanzati di controllo accessi e l'architettura Zero Trust.

### Attribute-Based Access Control (ABAC)

Il modello ABAC (Attribute-Based Access Control) va oltre l'RBAC assegnando i permessi di accesso in base a attributi dinamici dell'utente, della risorsa, dell'azione e del contesto ambientale.

**Differenze chiave tra RBAC e ABAC**

| Aspetto | RBAC | ABAC |
|---------|------|------|
| Base della decisione | Ruolo dell'utente | Attributi multipli (utente, risorsa, contesto) |
| Granularita' | Media (per ruolo) | Alta (per attributo) |
| Complessita' di gestione | Bassa-media | Media-alta |
| Adattabilita' al contesto | Limitata | Elevata |
| Scalabilita' | Rischio di role explosion | Scala con gli attributi |
| Esempio | "Un amministratore puo' accedere al server" | "Un dipendente del dipartimento Finanza, dal network aziendale, durante l'orario di lavoro, puo' accedere in sola lettura ai report finanziari del proprio dipartimento" |

**Categorie di attributi per le decisioni di accesso**

- **Attributi dell'utente (soggetto)**: dipartimento, livello di seniority, certificazioni possedute, livello di rischio dell'utente (basato su comportamento recente), tipo di contratto (dipendente, contrattista, fornitore).
- **Attributi della risorsa (oggetto)**: classificazione dei dati (pubblico, interno, riservato, segreto), proprietario della risorsa, tipo di risorsa (file, database, applicazione), ambiente (produzione, staging, sviluppo).
- **Attributi dell'azione**: tipo di operazione (lettura, scrittura, cancellazione, esecuzione, approvazione).
- **Attributi del contesto (ambiente)**: ora del giorno, giorno della settimana, posizione geografica, tipo di dispositivo (aziendale/personale), stato di conformita' del dispositivo, tipo di rete (aziendale, VPN, pubblica).

**Esempio di policy ABAC**

```
Policy: Accesso ai dati finanziari
Condizioni:
  - utente.dipartimento == "Finanza" OR utente.ruolo == "Auditor"
  - risorsa.classificazione IN ["interno", "riservato"]
  - risorsa.tipo == "report_finanziario"
  - contesto.rete IN ["aziendale", "vpn_aziendale"]
  - contesto.ora BETWEEN "08:00" AND "20:00"
  - contesto.dispositivo.conformita' == "compliant"
Azione consentita: lettura
Azione negata: scrittura, cancellazione (richiede ruolo "Finance Manager"
               E approvazione aggiuntiva)
```

### Implementazione Zero Trust

L'architettura Zero Trust elimina il concetto di "rete fidata" e richiede la verifica continua di ogni richiesta di accesso, indipendentemente dalla posizione dell'utente o del dispositivo.

**Principi fondamentali dell'implementazione**

1. **Verifica esplicita**: ogni richiesta di accesso viene autenticata e autorizzata sulla base di tutti i dati disponibili (identita' dell'utente, stato del dispositivo, servizio richiesto, classificazione dei dati, anomalie rilevate).
2. **Accesso con minimo privilegio**: l'accesso e' limitato al minimo necessario, con protezione just-in-time (JIT) e just-enough-access (JEA). I permessi sono concessi per la durata necessaria e revocati automaticamente.
3. **Presunzione di compromissione**: i controlli sono progettati assumendo che l'attaccante possa essere gia' all'interno della rete. Segmentazione granulare, cifratura end-to-end, e monitoraggio continuo del comportamento.

**Fasi di implementazione Zero Trust**

| Fase | Attivita' | Durata tipica |
|------|----------|---------------|
| 1 — Assessment | Mappatura degli asset, dei flussi di dati e degli accessi attuali | 2-3 mesi |
| 2 — Identita' | MFA universale, SSO, conditional access policies, identity governance | 3-6 mesi |
| 3 — Dispositivi | Device compliance policies, MDM/MAM, endpoint health verification | 3-6 mesi |
| 4 — Rete | Micro-segmentazione, software-defined perimeter, ZTNA | 6-12 mesi |
| 5 — Applicazioni | Application proxy, API gateway con autenticazione, code signing | 6-12 mesi |
| 6 — Dati | Classificazione automatica, cifratura basata su classificazione, DLP | 6-12 mesi |
| 7 — Monitoraggio continuo | Analytics comportamentale, UEBA, continuous access evaluation | Continuo |

**Conditional Access — esempi di policy**

Le policy di conditional access sono il meccanismo tecnico attraverso cui si implementa la verifica continua di Zero Trust:

```
Policy 1: Accesso alla posta elettronica
SE:
  - Utente: qualsiasi utente aziendale
  - Applicazione: Exchange Online / Outlook
  - Dispositivo: conforme alle policy di sicurezza (antivirus attivo,
    disco cifrato, OS aggiornato)
  - Rischio di accesso: basso o medio
ALLORA: consenti accesso con MFA
SE:
  - Dispositivo: non conforme o non gestito
  - Rischio di accesso: alto
ALLORA: blocca accesso o consenti solo accesso web con restrizioni
        (no download allegati)

Policy 2: Accesso a risorse critiche
SE:
  - Utente: gruppo "amministratori"
  - Applicazione: console di gestione infrastruttura
  - Rete: NON rete aziendale e NON VPN aziendale
ALLORA: blocca accesso
SE:
  - Rete: aziendale o VPN aziendale
  - Dispositivo: conforme e gestito
  - MFA: completata con metodo resistente al phishing (FIDO2)
ALLORA: consenti accesso per sessione di 4 ore massimo
```

### Matrice di Controllo Accessi

La matrice di controllo accessi documenta in modo strutturato chi puo' accedere a cosa e con quali permessi. E' uno strumento fondamentale per l'audit e per la verifica della conformita' al principio del minimo privilegio.

**Esempio di matrice per applicazioni aziendali**

| Risorsa / Ruolo | Helpdesk L1 | Sysadmin | DBA | Security Analyst | CISO | Sviluppatore |
|-----------------|-------------|----------|-----|-----------------|------|--------------|
| Active Directory — lettura | R | RW | — | R | R | — |
| Active Directory — modifica | — | RW | — | — | R | — |
| Server produzione — console | — | RW | R | R | R | — |
| Server produzione — deploy | — | RW | — | — | — | R (solo CI/CD) |
| Database produzione — dati | — | — | RW | R (log only) | — | — |
| Database produzione — schema | — | — | RW | — | — | — |
| SIEM — dashboard | R | R | — | RW | RW | — |
| SIEM — regole | — | — | — | RW | RW | — |
| Firewall — regole | — | R | — | R | RW | — |
| Vault PAM | — | R (checkout) | R (checkout) | R (audit) | RW | — |
| Backup — ripristino | — | RW | R | — | R | — |
| Backup — cancellazione | — | — | — | — | RW (con approvazione) | — |

Legenda: R = lettura, W = scrittura, RW = lettura e scrittura, — = nessun accesso

**Manutenzione della matrice**

- La matrice deve essere rivista e aggiornata almeno semestralmente o quando cambiano ruoli, applicazioni o requisiti di business.
- Ogni modifica alla matrice deve seguire il processo di change management e essere approvata dal responsabile della sicurezza.
- Confrontare periodicamente i permessi effettivi (estratti dai sistemi) con la matrice approvata per rilevare discrepanze.
- Utilizzare la matrice come base per la certificazione periodica degli accessi: i responsabili confermano che i permessi del loro personale sono conformi alla matrice.

---

## Best Practices

1. **Adottare un approccio defense-in-depth**: non affidarsi mai a un singolo controllo di sicurezza. Implementare livelli multipli di protezione (endpoint, rete, applicazione, dati) in modo che il fallimento di un livello non comprometta l'intera sicurezza. Se il firewall viene bypassato, l'EDR deve rilevare la minaccia; se l'EDR fallisce, la segmentazione di rete deve contenere il danno.

2. **Automatizzare tutto cio' che e' ripetitivo**: i processi manuali sono soggetti a errori e non scalano. Automatizzare il patching, il rinnovo dei certificati, la scansione delle vulnerabilita', il provisioning/deprovisioning degli accessi e la generazione dei report di compliance. Utilizzare strumenti di configuration management (Ansible, Puppet, Chef) per garantire la coerenza delle configurazioni di sicurezza su tutti i sistemi.

3. **Implementare il principio del minimo privilegio senza eccezioni**: ogni utente, servizio e processo deve avere solo i permessi strettamente necessari per svolgere la propria funzione. Questo principio si applica a tutti i livelli: account utente, account di servizio, regole firewall, permessi su file e directory, policy IAM cloud. Resistere alla tentazione di concedere permessi ampi "per comodita'" o "per ora, poi restringiamo": quei permessi temporanei diventano permanenti.

4. **Monitorare continuamente e rispondere rapidamente**: la prevenzione perfetta non esiste. Investire nel rilevamento e nella risposta tanto quanto nella prevenzione. Configurare il SIEM con regole di correlazione efficaci, eseguire threat hunting proattivo e mantenere un piano di risposta agli incidenti aggiornato e testato. Il tempo medio di rilevamento (MTTD) e il tempo medio di risposta (MTTR) sono metriche chiave da misurare e migliorare.

5. **Documentare ogni decisione di sicurezza**: ogni regola firewall, ogni esclusione EDR, ogni accettazione di rischio, ogni eccezione alla policy deve essere documentata con la motivazione, il responsabile e la data di revisione. Questa documentazione e' essenziale per l'audit, per la continuita' operativa (se il responsabile cambia) e per la revisione periodica.

6. **Eseguire test regolari dell'efficacia dei controlli**: non fidarsi mai della sola configurazione. Testare che il firewall blocchi effettivamente il traffico non autorizzato, che l'EDR rilevi campioni di malware di test (EICAR), che il SIEM generi alert per scenari di attacco simulati, che il backup sia effettivamente ripristinabile. Pianificare penetration test almeno annuali e tabletop exercise trimestrali per il piano di risposta agli incidenti.

7. **Gestire la sicurezza della supply chain**: verificare la sicurezza dei fornitori che hanno accesso ai sistemi aziendali. Richiedere certificazioni di sicurezza (ISO 27001, SOC 2), limitare l'accesso dei fornitori ai soli sistemi necessari, monitorare le loro attivita' e revocare gli accessi immediatamente al termine del contratto. Questo requisito e' ora esplicitamente previsto dalla direttiva NIS2.

8. **Formare continuamente il personale tecnico**: la sicurezza operativa dipende dalle competenze del team IT. Investire in formazione continua su nuove minacce, nuovi strumenti e best practice aggiornate. Incoraggiare le certificazioni professionali (CISSP, CISM, CompTIA Security+, vendor-specific). Condurre sessioni di knowledge sharing interne dopo ogni incidente o dopo la scoperta di nuove tecniche di attacco.

9. **Mantenere un inventario completo e aggiornato degli asset**: non e' possibile proteggere cio' che non si conosce. Ogni sistema, applicazione, certificato, account privilegiato e regola firewall deve essere censito in un inventario centralizzato. L'inventario deve essere aggiornato automaticamente (tramite strumenti di discovery) e verificato manualmente con cadenza regolare. L'inventario e' il prerequisito per ogni altra attivita' di sicurezza.

10. **Adottare una mentalita' "assume breach"**: progettare i controlli di sicurezza assumendo che un attaccante sia gia' all'interno della rete. Questo approccio porta a implementare segmentazione di rete robusta, monitoraggio del traffico interno (non solo perimetrale), cifratura dei dati a riposo (non solo in transito), e rilevamento del movimento laterale. L'approccio Zero Trust e' l'evoluzione naturale di questa mentalita'.

---

## Troubleshooting

### Problema: agente EDR non aggiornato o non comunicante

**Sintomi**: la console centrale mostra l'agente come offline o con definizioni obsolete. L'endpoint non compare nei report di scansione.

**Diagnosi e risoluzione**:

1. Verificare la connettivita' di rete tra l'endpoint e il server di gestione EDR. Testare con `telnet <server_edr> <porta>` o `Test-NetConnection`. Verificare che il firewall locale e di rete non blocchi la comunicazione.
2. Verificare che il servizio dell'agente sia in esecuzione (`Get-Service <nome_servizio>` su Windows, `systemctl status <nome_servizio>` su Linux).
3. Se il servizio e' fermo, tentare il riavvio. Controllare i log dell'agente per errori.
4. Verificare lo spazio disco: un disco pieno puo' impedire il download delle definizioni.
5. Verificare la sincronizzazione temporale: un'ora di sistema errata puo' causare il fallimento della verifica del certificato nella comunicazione con il server di gestione.
6. Se il problema persiste, reinstallare l'agente utilizzando il pacchetto di installazione piu' recente dalla console centrale.

### Problema: falsi positivi ricorrenti da IDS/IPS

**Sintomi**: alert ripetuti per lo stesso tipo di traffico che l'analisi conferma essere legittimo. Possibile impatto sulle prestazioni di rete se l'IPS blocca il traffico.

**Diagnosi e risoluzione**:

1. Identificare la firma che genera i falsi positivi (ID della regola, descrizione).
2. Analizzare il traffico che attiva la firma: catturare un campione con `tcpdump` o Wireshark per comprendere perche' il traffico legittimo corrisponde alla firma.
3. Creare un'eccezione specifica: per sorgente/destinazione/porta, non disabilitando la firma globalmente.
4. Documentare l'eccezione nel registro delle esclusioni con la giustificazione.
5. Monitorare per 48 ore dopo l'applicazione dell'eccezione per confermare che il falso positivo sia risolto senza creare punti ciechi.

### Problema: certificato SSL/TLS scaduto in produzione

**Sintomi**: gli utenti ricevono errori di certificato nel browser. Le applicazioni client ricevono errori di connessione TLS. Possibile interruzione completa del servizio per applicazioni che non consentono di ignorare gli errori di certificato.

**Diagnosi e risoluzione**:

1. Verificare la scadenza del certificato: `echo | openssl s_client -connect <host>:443 2>/dev/null | openssl x509 -noout -dates`.
2. Se il rinnovo automatico avrebbe dovuto funzionare, verificare i log di certbot/ACME per errori (permessi, DNS, raggiungibilita' della CA).
3. Per il ripristino immediato: rinnovare manualmente il certificato. Se il certificato e' di una CA commerciale, utilizzare il portale del vendor. Se e' Let's Encrypt, eseguire `certbot renew --force-renewal`.
4. Installare il nuovo certificato e ricaricare il servizio web (`nginx -s reload` o `systemctl restart apache2`).
5. Verificare il funzionamento con `curl -v https://<host>` e controllare che la catena di certificati sia completa.
6. **Azione preventiva**: configurare o riparare il monitoraggio delle scadenze per evitare che il problema si ripeta. Verificare il funzionamento del timer di rinnovo automatico.

### Problema: accesso non autorizzato rilevato durante l'audit degli accessi

**Sintomi**: durante la revisione trimestrale degli accessi, si rileva un utente con permessi non giustificati dal suo ruolo attuale.

**Diagnosi e risoluzione**:

1. Verificare la cronologia dell'account: quando sono stati assegnati i permessi? Da chi? C'e' un ticket di richiesta associato?
2. Contattare il responsabile dell'utente per verificare se i permessi sono effettivamente necessari per il ruolo attuale.
3. Se i permessi non sono giustificati, revocarli immediatamente e notificare l'utente e il responsabile.
4. Analizzare i log di accesso dell'utente per il periodo in cui ha avuto i permessi non autorizzati. Verificare se ci sono state attivita' anomale o accessi a dati sensibili.
5. Se si rilevano attivita' sospette, escalare al team di risposta agli incidenti.
6. Documentare il finding e verificare che il processo di change role/offboarding venga migliorato per prevenire situazioni analoghe.

### Problema: regole firewall che bloccano traffico legittimo dopo una modifica

**Sintomi**: dopo una modifica alle regole del firewall, un servizio smette di funzionare. Gli utenti riportano impossibilita' di accesso.

**Diagnosi e risoluzione**:

1. Verificare che la modifica sia la causa: controllare il timestamp della modifica e confrontarlo con l'inizio del problema.
2. Analizzare i log del firewall per cercare pacchetti bloccati (drop/deny) corrispondenti al traffico del servizio interessato.
3. Identificare quale regola sta bloccando il traffico: utilizzare la funzione di packet tracer o rule trace del firewall per simulare il percorso di un pacchetto.
4. Se necessario, effettuare un rollback della modifica per ripristinare il servizio immediatamente, poi analizzare la causa con calma.
5. Correggere la regola: la nuova regola potrebbe avere un errore nella definizione di sorgente, destinazione, porta, o potrebbe essere posizionata dopo una regola di deny piu' generica che la "ombra".
6. Riapplicare la modifica corretta e testare prima di confermare.

### Problema: scansione di vulnerabilita' che restituisce risultati incompleti o incoerenti

**Sintomi**: il report di scansione mostra un numero di vulnerabilita' significativamente inferiore rispetto alle scansioni precedenti, oppure alcuni sistemi risultano non scansionati.

**Diagnosi e risoluzione**:

1. Verificare la configurazione della scansione: l'ambito (target list) e' corretto e completo? I range IP sono aggiornati?
2. Se la scansione e' autenticata, verificare che le credenziali siano ancora valide. Le password degli account di scansione potrebbero essere scadute o gli account bloccati.
3. Verificare la connettivita' di rete tra lo scanner e i target: firewall, routing, segmentazione potrebbero bloccare la scansione.
4. Controllare i log dello scanner per errori di connessione, timeout o autenticazione fallita.
5. Per i sistemi non scansionati, eseguire una scansione di verifica mirata su un campione per confermare il problema.
6. Aggiornare i plugin/feed dello scanner alla versione piu' recente e ripetere la scansione.

### Problema: alert SIEM con volume eccessivo (alert fatigue)

**Sintomi**: il team di sicurezza riceve centinaia o migliaia di alert al giorno, rendendo impossibile l'analisi di ciascuno. Gli alert critici rischiano di passare inosservati.

**Diagnosi e risoluzione**:

1. Analizzare la distribuzione degli alert per tipo/regola: identificare le regole che generano il volume maggiore.
2. Per le regole piu' rumorose, valutare: la soglia e' troppo bassa? La regola e' troppo generica? Il traffico che attiva la regola e' legittimo?
3. Implementare l'aggregazione degli alert: alert identici dallo stesso IP/utente in un intervallo di tempo definito vengono raggruppati in un singolo alert.
4. Creare whitelist per il traffico noto legittimo che attiva regole generiche.
5. Implementare un sistema di prioritizzazione automatica che tenga conto del contesto (criticita' dell'asset, reputazione dell'IP sorgente, correlazione con altri eventi).
6. Considerare l'adozione di strumenti SOAR (Security Orchestration, Automation and Response) per automatizzare la risposta agli alert a bassa complessita', lasciando al team umano solo gli alert che richiedono analisi.

### Problema: impossibilita' di accesso al vault PAM in caso di emergenza

**Sintomi**: il sistema PAM non e' raggiungibile (guasto hardware, problema di rete, aggiornamento fallito) e gli operatori non possono accedere alle credenziali privilegiate necessarie per gestire un incidente critico.

**Diagnosi e risoluzione**:

1. Attivare la procedura di break glass: accedere alle credenziali di emergenza conservate in busta sigillata in cassaforte fisica (verificare periodicamente che le buste siano integre e le credenziali ancora valide).
2. Registrare ogni utilizzo della procedura di break glass: chi, quando, perche', quali credenziali.
3. Risolvere il problema del vault PAM seguendo le procedure di disaster recovery dello strumento.
4. Una volta ripristinato il vault, ruotare immediatamente tutte le credenziali utilizzate tramite break glass.
5. Condurre una revisione post-incidente per migliorare la resilienza del sistema PAM (alta disponibilita', backup piu' frequenti, procedura di failover testata).
6. **Azione preventiva**: testare la procedura di break glass almeno semestralmente. Verificare che le credenziali di emergenza siano aggiornate e che il personale conosca la procedura.

---

## Esercizi
1. **Lab — vuln scan + patch flow.** Scan Nessus/OpenVAS, prioritize CVSS, patch ring deployment.
2. **Stretch — break glass drill.** Trimestrale; misurare time-to-access.
3. **Lab — configurazione SIEM.** Configurare la raccolta log da almeno tre sorgenti diverse (Active Directory, firewall, server web), creare una regola di correlazione per brute force e verificare la generazione dell'alert.
4. **Lab — threat hunting.** Formulare un'ipotesi basata su una tecnica MITRE ATT&CK (es. T1059.001 — PowerShell), interrogare i log del SIEM per evidenze, documentare i risultati.
5. **Lab — simulazione phishing.** Progettare una campagna di phishing simulato con tre livelli di difficolta', eseguirla su un gruppo pilota, analizzare le metriche e pianificare la formazione di follow-up.
6. **Lab — matrice di controllo accessi.** Costruire una matrice RBAC per un ambiente di test con almeno 5 ruoli e 8 risorse, implementarla in Active Directory, verificare con audit che i permessi effettivi corrispondano alla matrice.
7. **Stretch — tabletop exercise.** Simulare uno scenario di ransomware con il team IT: dalla rilevazione iniziale alla comunicazione con il management, passando per contenimento, eradicazione e ripristino. Documentare le lezioni apprese.

## Auto-valutazione
1. Defense in depth: cosa significa e come si implementa nella pratica?
2. Break glass account: come si gestisce e con quale frequenza si testa?
3. SIEM forward: quali sorgenti di log includere e perche'?
4. SOC tier model: descrivere le responsabilita' di Tier 1, 2 e 3.
5. Threat hunting vs monitoraggio reattivo: quali sono le differenze fondamentali?
6. ABAC vs RBAC: quando preferire uno all'altro?
7. Zero Trust: quali sono i tre principi fondamentali?
8. Patch management: descrivere il modello a ring deployment e i suoi vantaggi.
9. Incident response: elencare le quattro fasi del modello NIST SP 800-61r3.
10. Security awareness: come si misura l'efficacia di un programma di formazione sulla sicurezza?

## Glossario locale
| Termine | Definizione |
|---|---|
| **PAM** | Privileged Access Management — gestione degli accessi privilegiati. |
| **Break glass** | Procedura di emergenza per accedere a credenziali privilegiate quando il vault PAM non e' disponibile. |
| **CVSS** | Common Vulnerability Scoring System — sistema di punteggio per classificare la severita' delle vulnerabilita'. |
| **SIEM** | Security Information and Event Management — piattaforma per la raccolta, correlazione e analisi dei log di sicurezza. |
| **SOC** | Security Operations Center — unita' organizzativa per il monitoraggio continuo e la risposta agli incidenti. |
| **SOAR** | Security Orchestration, Automation and Response — piattaforma per l'automazione dei processi di risposta agli incidenti. |
| **EDR** | Endpoint Detection and Response — soluzione per il rilevamento e la risposta alle minacce sugli endpoint. |
| **XDR** | Extended Detection and Response — evoluzione dell'EDR che correla telemetria da endpoint, rete e cloud. |
| **ABAC** | Attribute-Based Access Control — modello di controllo accessi basato su attributi dinamici. |
| **RBAC** | Role-Based Access Control — modello di controllo accessi basato su ruoli predefiniti. |
| **MITRE ATT&CK** | Framework che cataloga tattiche, tecniche e procedure (TTP) utilizzate dagli attaccanti. |
| **MTTD** | Mean Time to Detect — tempo medio di rilevazione di una minaccia. |
| **MTTR** | Mean Time to Respond — tempo medio di risposta a un incidente. |
| **IOC** | Indicator of Compromise — indicatore di compromissione (IP, hash, dominio, pattern di comportamento). |
| **CSIRT** | Computer Security Incident Response Team — team di risposta agli incidenti di sicurezza informatica. |
| **IRP** | Incident Response Plan — piano documentato per la gestione degli incidenti di sicurezza. |
| **ZTNA** | Zero Trust Network Access — accesso di rete basato su principi Zero Trust. |
| **JIT** | Just-In-Time access — accesso privilegiato concesso temporaneamente su richiesta. |
| **KEV** | Known Exploited Vulnerabilities — catalogo CISA delle vulnerabilita' attivamente sfruttate. |
| **CRS** | Core Rule Set — set di regole OWASP per Web Application Firewall. |
| **Sigma** | Formato aperto e portabile per la scrittura di regole di rilevamento SIEM. |
| **WORM** | Write Once Read Many — storage che impedisce la modifica dei dati dopo la scrittura. |
