# Backup e Disaster Recovery — Guida Completa

> **Modulo 06** · **Tempo:** 90 min · **Aggiornamento:** 2026-04-27

## Idee guida

1. **3-2-1-1-0 rule: 3 copie, 2 supporti, 1 offsite, 1 immutable, 0 errori.**
2. **RTO + RPO definiti = strategia conseguente.** Senza target, e improvvisazione.
3. **Restore drill > backup test.** Il backup esiste finche non lo restorize con successo.
4. **WORM/immutable backup contro ransomware.** Senza, attaccante cripta anche i backup.


## Indice

1. [Panoramica](#panoramica)
2. [Strategia di Backup](#strategia-di-backup)
   - [Regola 3-2-1-1-0](#regola-3-2-1-1-0)
   - [Tipi di Backup](#tipi-di-backup)
   - [Backup per Tipo di Sistema](#backup-per-tipo-di-sistema)
   - [Scheduling e Retention](#scheduling-e-retention)
   - [Strumenti di Backup](#strumenti-di-backup)
3. [Verifica Backup](#verifica-backup)
   - [Test di Restore](#test-di-restore)
   - [Monitoraggio Backup](#monitoraggio-backup)
   - [Integrita Dati](#integrità-dati)
4. [Disaster Recovery](#disaster-recovery)
   - [Business Impact Analysis (BIA)](#business-impact-analysis-bia)
   - [DRP (Disaster Recovery Plan)](#drp-disaster-recovery-plan)
   - [Scenari di Disaster](#scenari-di-disaster)
   - [DR Testing](#dr-testing)
5. [Business Continuity](#business-continuity)
   - [BCP vs DRP](#bcp-vs-drp)
   - [Alta Disponibilita](#alta-disponibilità)
   - [Continuita Operativa](#continuità-operativa)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## Panoramica

Il backup e il disaster recovery rappresentano due pilastri fondamentali della manutenzione IT, indissolubilmente legati fra loro ma concettualmente distinti. Il **backup** si occupa della protezione dei dati attraverso la creazione di copie di sicurezza che consentano il ripristino in caso di perdita, corruzione o cancellazione accidentale. Il **disaster recovery** (DR) affronta scenari piu ampi, definendo processi, procedure e infrastrutture necessarie per ripristinare l'operativita dell'intero ambiente IT a seguito di un evento catastrofico.

La differenza pratica e significativa: un backup funzionante non garantisce la capacita di ripristinare un servizio complesso in tempi accettabili. Senza un piano di disaster recovery strutturato e testato, anche disponendo di copie perfette dei dati, il tempo necessario per ricostruire l'infrastruttura, riconfigurare le dipendenze e validare il funzionamento applicativo puo rendere il ripristino inaccettabilmente lungo.

L'approccio moderno alla protezione dei dati integra backup, disaster recovery e business continuity in un framework unitario che considera:

- **Protezione dei dati**: salvaguardia delle informazioni attraverso copie multiple, diversificate e verificate.
- **Resilienza infrastrutturale**: capacita dell'infrastruttura di tollerare guasti senza interruzione del servizio.
- **Ripristino operativo**: procedure documentate e testate per il ritorno alla normalita dopo un disastro.
- **Continuita del business**: mantenimento delle operazioni aziendali essenziali anche durante un'interruzione IT prolungata.

In questa guida vengono trattati tutti questi aspetti con un approccio pratico e operativo, fornendo procedure concrete, template utilizzabili e criteri di valutazione per ogni componente della strategia di protezione.

---

## Strategia di Backup

Una strategia di backup efficace deve rispondere a cinque domande fondamentali: cosa proteggere, con quale frequenza, dove conservare le copie, per quanto tempo mantenerle e come verificare che siano effettivamente utilizzabili. Le risposte a queste domande determinano l'architettura complessiva del sistema di backup.

### Regola 3-2-1-1-0

La regola 3-2-1 e stata per anni il riferimento standard per la protezione dei dati. L'evoluzione delle minacce, in particolare la diffusione del ransomware, ha portato all'estensione in **3-2-1-1-0**, che rappresenta oggi il livello minimo raccomandato per qualsiasi organizzazione.

**3 copie dei dati**: mantenere almeno tre copie complete di ogni dato critico. Questo include la copia di produzione (i dati originali) piu due copie di backup indipendenti. La ragione matematica e semplice: con tre copie indipendenti, la probabilita di perdita simultanea di tutte e tre e astronomicamente bassa. Se la probabilita di guasto di un singolo supporto e 1/100, la probabilita di perdita tripla simultanea e 1/1.000.000.

**2 tipi di supporto diversi**: conservare le copie su almeno due tecnologie di storage differenti. Ad esempio, una copia su disco locale e una su nastro, oppure una su NAS e una su object storage cloud. Questo protegge da guasti sistematici che colpiscono una specifica tecnologia. Un firmware difettoso del controller RAID potrebbe corrompere simultaneamente tutti i dati su un array di dischi, ma non toccherebbe le copie su nastro o cloud.

**1 copia offsite**: almeno una copia deve trovarsi in una posizione geograficamente distinta. Questo protegge da eventi fisici come incendi, alluvioni, terremoti o furti che colpiscono la sede principale. La distanza minima raccomandata dipende dai rischi specifici della zona: almeno 50 km per rischi localizzati, oltre 200 km per rischi regionali come terremoti.

**1 copia immutabile o air-gapped**: questa e l'estensione critica introdotta in risposta al ransomware. Una copia immutabile non puo essere modificata o cancellata per un periodo definito, nemmeno da un amministratore con credenziali compromesse. Le implementazioni possibili includono:

- **Object Lock S3** (WORM compliance): i dati scritti non possono essere sovrascritti o cancellati fino alla scadenza del periodo di retention.
- **Nastri offline**: cartucce fisicamente rimosse dall'infrastruttura e conservate in un caveau.
- **Air-gapped storage**: sistemi di storage fisicamente disconnessi dalla rete, connessi solo durante le finestre di backup.
- **Immutability nativa**: funzionalita offerte da soluzioni come Veeam Hardened Repository o Borg con append-only mode.

**0 errori (restore verificati)**: ogni backup deve essere verificato attraverso test di restore periodici. Un backup non testato e un backup di cui non ci si puo fidare. La verifica deve includere non solo il controllo dell'integrita del file di backup, ma il ripristino effettivo dei dati e la validazione della loro utilizzabilita.

### Tipi di Backup

La scelta del tipo di backup influisce direttamente su quattro fattori: la finestra di backup (tempo necessario per completare l'operazione), lo spazio di storage richiesto, la velocita di ripristino e la complessita della gestione.

| Caratteristica | Full | Incrementale | Differenziale | Synthetic Full |
|---|---|---|---|---|
| **Cosa salva** | Tutti i dati | Solo le modifiche dall'ultimo backup (qualsiasi tipo) | Modifiche dall'ultimo full | Ricostruzione full da incrementali |
| **Spazio richiesto** | Massimo | Minimo | Medio (crescente) | Equivalente a full |
| **Tempo di backup** | Lungo | Brevissimo | Medio (crescente) | Medio (elaborazione locale) |
| **Tempo di restore** | Veloce (singolo job) | Lento (catena di incrementali) | Medio (full + ultimo diff) | Veloce (singolo job) |
| **Complessita** | Bassa | Media (gestione catena) | Bassa | Media |
| **Rischio catena** | Nessuno | Alto (se un incrementale si corrompe, tutti i successivi sono inutili) | Basso (serve solo full + diff) | Basso |

**Synthetic Full Backup**: rappresenta un compromesso intelligente. Invece di leggere nuovamente tutti i dati dal server di produzione, il software di backup combina l'ultimo full con tutti gli incrementali successivi per creare un nuovo full backup sul repository. Questo riduce il carico sul sistema di produzione e sulla rete, spostando l'elaborazione sul server di backup.

**Changed Block Tracking (CBT)**: tecnologia chiave per l'efficienza dei backup, specialmente in ambienti virtualizzati. Il CBT tiene traccia dei blocchi di disco modificati dall'ultimo backup, consentendo al software di leggere e copiare solo i blocchi effettivamente cambiati. L'implementazione varia per piattaforma:

- **VMware**: vSphere CBT nativo integrato nell'hypervisor, attivabile per singola VM.
- **Hyper-V**: Resilient Change Tracking (RCT) a partire da Windows Server 2016.
- **Proxmox/KVM**: dirty bitmap tracking, supportato da soluzioni come Proxmox Backup Server.

**Deduplicazione e compressione**: due tecniche complementari per ridurre lo spazio di storage:

- **Deduplicazione inline**: analizza i blocchi durante la scrittura ed elimina i duplicati in tempo reale. Riduce significativamente lo spazio (rapporti tipici 10:1 — 50:1 per backup di VM simili) ma richiede risorse computazionali e RAM significative.
- **Deduplicazione post-process**: eseguita dopo la scrittura, riduce l'impatto sulle prestazioni di backup ma richiede temporaneamente piu spazio.
- **Compressione**: algoritmi come LZ4 (veloce, rapporto moderato), Zstandard (buon bilanciamento), o LZMA (massima compressione, lento). La scelta dipende dal compromesso tra velocita e rapporto di compressione.

### Backup per Tipo di Sistema

Ogni tipologia di sistema richiede approcci specifici per garantire backup consistenti e ripristinabili.

#### File Server

Il backup dei file server sembra semplice ma nasconde insidie legate ai file aperti, ai permessi e alla struttura delle condivisioni.

**Volume Shadow Copy Service (VSS)**: tecnologia Microsoft fondamentale per il backup di file aperti. VSS crea uno snapshot point-in-time del volume, consentendo al software di backup di leggere una copia consistente dei file anche mentre gli utenti li stanno modificando. Configurazione raccomandata:

- Allocare almeno il 10% dello spazio del volume per le shadow copy.
- Programmare snapshot VSS ogni 2 ore durante l'orario lavorativo per consentire il self-service restore degli utenti.
- Non affidarsi esclusivamente a VSS come soluzione di backup — le shadow copy risiedono sullo stesso volume dei dati originali.

**Backup agent-based**: un agente installato sul file server gestisce il backup. Vantaggi: accesso diretto ai file, gestione VSS integrata, possibilita di backup a livello di file o di volume. Svantaggi: richiede installazione e manutenzione dell'agente su ogni server.

**Backup agentless**: il software di backup accede ai file tramite condivisioni di rete (SMB/CIFS o NFS). Vantaggi: nessuna installazione sui server. Svantaggi: dipendenza dalla rete, impossibilita di gestire VSS dal remoto, problemi con file aperti non gestiti tramite VSS remoto.

Dati da includere nel backup: condivisioni utente, home directory, dati dipartimentali, configurazione del server (quote, permessi NTFS, configurazione DFS), certificati e script di gestione.

#### Active Directory

Active Directory e il cuore dell'infrastruttura Windows e richiede procedure di backup specifiche.

**System State Backup**: include il database AD (NTDS.DIT), SYSVOL, registro di sistema, configurazione dei servizi, certificati e informazioni del cluster. Il backup del System State deve essere eseguito su ogni domain controller, non solo su uno.

```powershell
# Backup System State con Windows Server Backup
wbadmin start systemstatebackup -backupTarget:E: -quiet

# Verifica dello stato del backup
wbadmin get versions -backupTarget:E:
```

**ntdsutil**: strumento per operazioni avanzate sul database AD, incluso il ripristino autoritativo di oggetti specifici.

```powershell
# Snapshot del database AD per verifica offline
ntdsutil "activate instance ntds" "ifm" "create full C:\IFM" quit quit
```

Considerazioni critiche per il backup AD:

- Il backup del System State ha una validita limitata: non puo essere piu vecchio della durata del tombstone lifetime (per impostazione predefinita 180 giorni).
- In ambienti multi-domain controller, pianificare il backup in modo sfalsato per evitare problemi di replica.
- Documentare la procedura di ripristino autoritativo vs non-autoritativo e quando utilizzare ciascuna.
- Includere nel backup anche le Group Policy Objects (GPO), esportandole separatamente con `Backup-GPO`.

#### Exchange / Email Server

I sistemi di posta richiedono backup application-aware per garantire la consistenza dei database.

**Backup DAG-aware (Database Availability Group)**: in configurazioni Exchange con DAG, il backup deve essere consapevole della topologia del gruppo di disponibilita per evitare di eseguire il backup della stessa copia passiva su piu nodi. La best practice e eseguire il backup dalla copia passiva per non impattare le prestazioni della copia attiva.

**Backup a livello di mailbox**: complementare al backup a livello di database, consente il ripristino granulare di singole caselle di posta, cartelle o messaggi. Indispensabile per soddisfare richieste di ripristino puntuali senza dover ripristinare un intero database.

Per ambienti Microsoft 365/Exchange Online:

- Microsoft non garantisce il backup dei dati dei tenant — la responsabilita e del cliente.
- Utilizzare soluzioni di backup dedicate per Microsoft 365 (Veeam Backup for Microsoft 365, Commvault, ecc.).
- Backup di mailbox, OneDrive, SharePoint e Teams.
- Retention configurabile indipendente dalle policy di retention di Microsoft.

#### Database

Il backup dei database richiede attenzione particolare alla consistenza transazionale.

**SQL Server**:

| Tipo | Comando | Contenuto | Frequenza tipica |
|---|---|---|---|
| Full | `BACKUP DATABASE [DB] TO DISK='path'` | Intero database | Giornaliero |
| Differential | `BACKUP DATABASE [DB] TO DISK='path' WITH DIFFERENTIAL` | Modifiche dall'ultimo full | Ogni 4-6 ore |
| Transaction Log | `BACKUP LOG [DB] TO DISK='path'` | Log delle transazioni | Ogni 15-30 minuti |

La catena dei backup del transaction log e fondamentale per il point-in-time recovery: permette di ripristinare il database a qualsiasi istante, fino all'ultimo backup del log completato. Interrompere la catena (ad esempio con un backup full senza `COPY_ONLY`) invalida tutti i log backup precedenti.

**PostgreSQL**:

- **pg_dump**: backup logico, produce un file SQL o un archivio custom. Adatto per database di piccole-medie dimensioni e per la migrazione tra versioni diverse.

```bash
# Backup logico con compressione
pg_dump -Fc -f /backup/mydb_$(date +%Y%m%d).dump mydb

# Restore
pg_restore -d mydb /backup/mydb_20260326.dump
```

- **pg_basebackup**: backup fisico dell'intero cluster PostgreSQL. Necessario come base per il point-in-time recovery tramite WAL archiving.

```bash
# Backup base con WAL inclusi
pg_basebackup -D /backup/base -Ft -z -Xs -P
```

- **WAL Archiving e PITR**: configurando `archive_mode = on` e `archive_command`, PostgreSQL copia ogni WAL segment completato in una posizione di archivio. Combinando un backup base con i WAL archiviati, e possibile ripristinare il database a qualsiasi punto nel tempo.

```
# postgresql.conf
archive_mode = on
archive_command = 'cp %p /archive/wal/%f'
```

Strumenti avanzati come **pgBackRest** e **Barman** automatizzano l'intero workflow: backup base, gestione WAL, retention, verifica e ripristino PITR con un'interfaccia unificata.

**MySQL/MariaDB**:

- **mysqldump**: backup logico, analogo a pg_dump. Blocca le tabelle durante il dump (a meno di usare `--single-transaction` con InnoDB).

```bash
mysqldump --single-transaction --routines --triggers --all-databases | \
  gzip > /backup/all_db_$(date +%Y%m%d).sql.gz
```

- **Percona XtraBackup**: backup fisico a caldo (hot backup) per MySQL/MariaDB con engine InnoDB. Non richiede lock sulle tabelle durante il backup, rendendolo ideale per ambienti di produzione ad alto carico.

```bash
# Backup completo
xtrabackup --backup --target-dir=/backup/full

# Backup incrementale
xtrabackup --backup --target-dir=/backup/inc1 \
  --incremental-basedir=/backup/full
```

#### Virtualizzazione

Il backup a livello di hypervisor e oggi l'approccio preferito per gli ambienti virtualizzati, offrendo backup agentless, consistenti e rapidi.

**VM-level snapshot e backup**:

- **Veeam Backup & Replication**: soluzione enterprise leader per ambienti VMware e Hyper-V. Funzionalita chiave: CBT, application-aware processing (garantisce consistenza per AD, SQL, Exchange, Oracle), instant VM recovery (avvia la VM direttamente dal backup), SureBackup (verifica automatica dei backup).

- **Proxmox Backup Server (PBS)**: soluzione nativa per ambienti Proxmox VE. Supporta backup incrementali a livello di blocco, deduplicazione lato server, crittografia lato client, verifica automatica dell'integrita. Integrazione diretta con l'interfaccia di gestione Proxmox.

```bash
# Configurazione backup job in Proxmox (pvesh)
pvesh create /cluster/backup \
  --storage pbs-remote \
  --schedule "0 2 * * *" \
  --mailnotification always \
  --mode snapshot \
  --compress zstd
```

- **borgmatic / BorgBackup**: soluzione open source per backup incrementali, deduplicati e crittografati. Ideale per server Linux standalone, VM o container. La deduplicazione a livello di blocco variabile offre rapporti eccellenti.

```yaml
# borgmatic config.yaml
repositories:
  - path: ssh://backup@remote/./repo
    label: offsite
storage:
  compression: auto,zstd
  encryption_passphrase: "${BORG_PASSPHRASE}"
retention:
  keep_daily: 7
  keep_weekly: 4
  keep_monthly: 12
hooks:
  before_backup:
    - /usr/local/bin/pre-backup-checks.sh
  after_backup:
    - /usr/local/bin/verify-backup.sh
```

**Application-consistent snapshot**: un semplice snapshot della VM cattura lo stato del disco in un istante, ma i dati delle applicazioni (database, mail server) potrebbero trovarsi in uno stato inconsistente. Gli snapshot application-consistent utilizzano meccanismi come VMware Tools con VSS (Windows) o script pre/post-freeze (Linux) per forzare le applicazioni a scrivere tutti i dati in memoria su disco prima dello snapshot.

#### Endpoint

La protezione degli endpoint (workstation, laptop) e spesso trascurata ma fondamentale.

- **OneDrive/SharePoint**: la sincronizzazione dei file utente su OneDrive fornisce una protezione di base ma non e un backup. I file eliminati vengono mantenuti nel cestino per un periodo limitato (93 giorni per SharePoint). Per una protezione completa, utilizzare soluzioni di backup dedicate per Microsoft 365.

- **Endpoint backup agents**: agenti leggeri installati sulle workstation che eseguono backup continui o schedulati dei dati utente verso un repository centralizzato. Soluzioni come Veeam Agent, Acronis Cyber Protect, CrashPlan o Duplicati.

- Dati prioritari per il backup endpoint: documenti utente, profili di applicazione, configurazioni personalizzate, certificati client, chiavi SSH, credential store locali.

#### Configurazioni

Il backup delle configurazioni e spesso il piu trascurato ma il piu rapido da ripristinare e il piu critico per la ricostruzione dell'infrastruttura.

- **Dispositivi di rete**: esportazione periodica delle configurazioni di switch, router, access point. Utilizzare strumenti come RANCID, Oxidized o script personalizzati per automatizzare il backup delle configurazioni via SSH/SNMP.

```bash
# Esempio: backup configurazione switch Cisco via SSH
ssh admin@switch "show running-config" > \
  /backup/network/switch01_$(date +%Y%m%d).conf
```

- **Firewall**: esportazione delle regole, NAT, VPN, certificati. Ogni modifica deve essere documentata e il backup aggiornato prima e dopo la modifica.

- **Certificati**: backup di tutti i certificati SSL/TLS, chiavi private (in formato protetto), certificati CA interni, certificati di code signing. Conservare in un vault crittografato con accesso limitato.

- **Script e IaC (Infrastructure as Code)**: tutti gli script di automazione, i template Terraform/Ansible/Puppet, i file di configurazione dei servizi devono essere versionati in un repository Git. Il repository Git stesso deve essere sottoposto a backup offsite.

### Scheduling e Retention

La pianificazione dei backup e le politiche di retention determinano la granularita del ripristino e i costi di storage.

#### Schema di Rotazione Grandfather-Father-Son (GFS)

Il GFS e lo schema di retention piu diffuso, che bilancia la granularita del ripristino con l'efficienza dello storage:

| Livello | Retention | Tipo | Frequenza |
|---|---|---|---|
| **Son** (giornaliero) | 7-14 giorni | Incrementale | Ogni giorno feriale |
| **Father** (settimanale) | 4-5 settimane | Full o Synthetic Full | Ogni venerdi/sabato |
| **Grandfather** (mensile) | 12 mesi | Full | Primo sabato del mese |
| **Annuale** | 3-10 anni | Full | 1 gennaio o fine anno fiscale |

#### Retention per Tipo di Dato

Non tutti i dati richiedono la stessa retention. Una classificazione tipica:

| Tipo di Dato | Retention Minima | Note |
|---|---|---|
| Dati finanziari/contabili | 10 anni | Obblighi fiscali |
| Dati del personale | Durata rapporto + 10 anni | Normativa lavoro |
| Email aziendali | 3-5 anni | Compliance interna |
| Dati di progetto | Durata progetto + 2 anni | Garanzie contrattuali |
| Log di sistema | 1-2 anni | Requisiti di audit |
| Database di produzione | 30 giorni operativi + archivio mensile | Bilanciamento costo/rischio |
| Configurazioni | Indefinita (versionata) | Repository Git |
| Dati GDPR/privacy | Secondo informativa | Cancellazione obbligatoria alla scadenza |

#### Requisiti Legali di Retention

La normativa italiana ed europea impone obblighi specifici:

- **GDPR (Regolamento UE 2016/679)**: i dati personali non devono essere conservati oltre il periodo necessario per le finalita del trattamento. Il backup deve prevedere meccanismi per la cancellazione dei dati su richiesta (diritto all'oblio), compatibilmente con le limitazioni tecniche.
- **Codice Civile italiano**: documenti contabili conservati per 10 anni (art. 2220).
- **Normativa fiscale**: fatture e documenti fiscali conservati per almeno 10 anni.
- **D.Lgs. 231/2001**: conservazione della documentazione relativa al modello organizzativo e ai controlli.

#### Pianificazione della Capacita di Storage

Formula di base per stimare lo storage necessario:

```
Storage annuale = (Dimensione full * numero full/anno) +
                  (Dimensione incrementale media * numero incrementali/anno) *
                  (1 - rapporto deduplicazione) *
                  (1 - rapporto compressione) +
                  Margine crescita (15-25%)
```

Esempio pratico: 10 TB di dati di produzione con backup giornaliero incrementale e full settimanale, retention GFS 12 mesi, deduplicazione 60%, compressione 40%:

- 52 full/anno * 10 TB = 520 TB lordi
- 260 incrementali/anno * 0.5 TB medio = 130 TB lordi
- Totale lordo: 650 TB
- Dopo deduplicazione (60%): 260 TB
- Dopo compressione (40%): 156 TB
- Con margine 20%: circa 187 TB di storage necessario

### Strumenti di Backup

La scelta dello strumento di backup dipende dall'ambiente, dal budget e dai requisiti specifici.

| Strumento | Tipo | Ambienti | Licenza | Punti di Forza | Limitazioni |
|---|---|---|---|---|---|
| **Veeam B&R** | Enterprise | VMware, Hyper-V, fisici, cloud, M365 | Commerciale (Community Edition gratuita fino a 10 workload) | CBT, SureBackup, Instant Recovery, scalabilita | Costo licenze, richiede Windows per il server |
| **Commvault** | Enterprise | Universale | Commerciale | Copertura amplissima, governance dati, automazione | Complessita, costo elevato |
| **BorgBackup** | Open Source | Linux, macOS | BSD | Deduplicazione eccellente, crittografia, efficienza | Solo CLI, nessuna GUI nativa, no Windows nativo |
| **Restic** | Open Source | Multi-piattaforma | BSD | Multi-backend (S3, SFTP, Azure, ecc.), crittografia | Deduplicazione meno efficiente di Borg, no compressione nativa fino a v0.14 |
| **Bacula** | Open Source/Enterprise | Multi-piattaforma | AGPLv3 / Commerciale | Architettura scalabile, flessibile, supporto nastro | Configurazione complessa, curva di apprendimento ripida |
| **Windows Server Backup** | Nativo | Windows Server | Incluso nel SO | Nessun costo aggiuntivo, backup bare metal, System State | Funzionalita limitate, nessuna deduplicazione, gestione basilare |
| **Proxmox Backup Server** | Open Source | Proxmox VE, Linux | AGPLv3 | Integrazione nativa Proxmox, deduplicazione, incrementale, crittografia | Legato all'ecosistema Proxmox |
| **rsync-based** | Open Source | Linux/Unix | GPL | Semplicita, efficienza rete, disponibilita universale | Nessuna deduplicazione, nessuna crittografia nativa, gestione manuale retention |

---

## Verifica Backup

Un backup non verificato e sostanzialmente inutile. La fase di verifica e tanto importante quanto il backup stesso, eppure e la piu frequentemente trascurata. Secondo statistiche di settore, circa il 30% dei restore fallisce a causa di backup non verificati, corrotti o incompleti.

### Test di Restore

I test di restore devono essere eseguiti con regolarita e a diversi livelli di complessita.

#### Procedura di Test Mensile

Ogni mese, eseguire almeno un test di ripristino per ciascuna categoria di backup:

1. **Selezione del target**: scegliere un backup recente (non l'ultimo, per verificare anche la catena di incrementali).
2. **Preparazione dell'ambiente**: predisporre l'ambiente di test (VM temporanea, database di test, directory di restore).
3. **Esecuzione del restore**: eseguire il ripristino completo seguendo la procedura documentata, cronometrando il tempo.
4. **Validazione dei dati**: verificare che i dati ripristinati siano completi, leggibili e utilizzabili.
5. **Documentazione**: compilare il report di test con esito, tempi, eventuali problemi riscontrati.

#### Esercitazione Trimestrale di Full Restore

Ogni trimestre, eseguire un test di ripristino completo che simuli uno scenario realistico:

- Ripristino bare metal di un server critico su hardware alternativo o VM.
- Ripristino completo di un database di produzione con verifica dell'integrita e delle prestazioni.
- Ripristino di Active Directory e validazione dell'autenticazione e delle policy.
- Misurazione accurata dei tempi di ogni fase e confronto con gli RTO definiti.

#### Cosa Testare

| Livello di Test | Cosa Verificare | Frequenza | Responsabile |
|---|---|---|---|
| **File-level** | Ripristino di file/cartelle singole, verifica permessi | Mensile | Operatore backup |
| **Volume-level** | Ripristino di un intero volume, verifica struttura | Trimestrale | Sistemista |
| **Bare metal** | Ripristino completo del sistema operativo su hardware diverso | Semestrale | Team infrastruttura |
| **Application-level** | Ripristino e avvio applicazione, verifica funzionalita | Trimestrale | Sistemista + referente applicativo |
| **Database** | Ripristino DB, verifica integrita, test query | Mensile | DBA |

#### Documentazione dei Risultati

Ogni test di restore deve produrre un report che includa:

- Data e ora del test.
- Backup utilizzato (data, tipo, dimensione).
- Sistema target del ripristino.
- Procedura seguita (con eventuali deviazioni dalla procedura standard).
- Tempo effettivo di restore per ogni fase.
- Esito della validazione dei dati.
- Problemi riscontrati e azioni correttive.
- Confronto del tempo di restore con l'RTO definito.
- Firma del responsabile del test.

#### Misurazione del Tempo di Restore vs RTO

Mantenere un registro storico dei tempi di restore per ogni sistema critico. Calcolare la media e il trend. Se il tempo medio di restore supera l'80% dell'RTO, attivare un piano di miglioramento (ottimizzazione della rete, upgrade dello storage di backup, revisione della procedura).

### Monitoraggio Backup

Il monitoraggio proattivo dei backup e essenziale per identificare problemi prima che diventino critici.

#### Monitoraggio dei Job di Backup

Configurare alerting per ogni job di backup con i seguenti livelli:

- **Success**: job completato senza errori — log informativo, nessun alert.
- **Warning**: job completato con avvisi (file saltati, retry riusciti, timeout parziali) — alert via email al team operativo.
- **Failed**: job fallito — alert immediato via email e SMS/messaggistica al responsabile.
- **Missed**: job non avviato nell'orario previsto — alert critico, indagine immediata.

Per ogni job fallito, documentare:

- Causa del fallimento (spazio insufficiente, errore di rete, lock su file, errore VSS, timeout).
- Azione correttiva intrapresa.
- Verifica del completamento del job successivo.

#### Trending della Dimensione dei Backup

Monitorare l'andamento delle dimensioni dei backup nel tempo consente di:

- Rilevare anomalie (aumento improvviso = possibile infezione malware o dump massivo di dati; diminuzione improvvisa = possibile errore di configurazione o esclusione non intenzionale).
- Pianificare l'espansione dello storage.
- Ottimizzare le policy di deduplicazione e compressione.

#### Conformita della Finestra di Backup

Verificare che i job si completino entro la finestra di backup definita. Se un job inizia a sforare regolarmente la finestra:

- Analizzare i colli di bottiglia (rete, disco, CPU, lock applicativi).
- Valutare l'ottimizzazione (CBT, incrementali piu frequenti, compressione diversa).
- Considerare la ridistribuzione dei job su finestre diverse.

#### Utilizzo dello Storage

Monitorare lo spazio disponibile sul repository di backup con soglie di alert:

- **Warning**: utilizzo superiore al 75%.
- **Critical**: utilizzo superiore al 85%.
- **Emergency**: utilizzo superiore al 95% — rischio imminente di fallimento dei backup.

#### Configurazione degli Alert

Centralizzare gli alert di backup in un sistema di monitoraggio unificato (Zabbix, PRTG, Checkmk, Prometheus/Grafana) per avere visibilita complessiva. Configurare:

- Dashboard dedicata ai backup con stato in tempo reale di tutti i job.
- Report settimanale automatico con riepilogo successi/fallimenti/warning.
- Escalation automatica per job falliti non risolti entro 24 ore.

### Integrita Dati

La verifica dell'integrita garantisce che i dati di backup non siano corrotti e siano effettivamente utilizzabili.

#### Verifica Checksum

Ogni operazione di backup dovrebbe calcolare e registrare i checksum (SHA-256 o superiore) dei dati salvati. Durante la verifica, ricalcolare i checksum e confrontarli con quelli registrati. Discrepanze indicano corruzione.

```bash
# Verifica integrita repository BorgBackup
borg check --repository-only /backup/repo

# Verifica integrita con dati
borg check --verify-data /backup/repo
```

#### Validazione Automatica del Backup

**Veeam SureBackup**: funzionalita che automatizza la verifica dei backup. SureBackup avvia una VM dal backup in un ambiente isolato (sandbox), verifica che il sistema operativo si avvii correttamente, esegue test applicativi (ping, porta di servizio, script personalizzati) e documenta il risultato. Tutto questo avviene senza impatto sull'ambiente di produzione.

**Verifica manuale**: per soluzioni che non offrono validazione automatica, creare script che:

1. Montino il backup (se supportato).
2. Verifichino la presenza dei file critici.
3. Controllino l'integrita dei database (DBCC CHECKDB per SQL Server, pg_verifybackup per PostgreSQL).
4. Generino un report con l'esito.

#### Rilevamento della Corruzione

Implementare controlli proattivi:

- Scansione periodica del repository di backup con gli strumenti nativi della soluzione.
- Monitoraggio degli errori di lettura sullo storage di backup (SMART per dischi, contatori errori per array).
- Alert immediato per qualsiasi errore di integrita rilevato.

#### Verifica dell'Immutabilita

Per i backup immutabili, verificare periodicamente che l'immutabilita sia effettivamente attiva:

- Tentare la cancellazione di un backup protetto e verificare che fallisca.
- Controllare le policy di Object Lock o WORM.
- Verificare che le credenziali di gestione dell'immutabilita siano separate da quelle operative.

---

## Disaster Recovery

Il disaster recovery si occupa del ripristino dell'operativita IT a seguito di eventi che rendono indisponibile l'infrastruttura primaria. A differenza del semplice restore da backup, il DR considera l'intero ecosistema: infrastruttura, applicazioni, dati, connettivita e processi operativi.

### Business Impact Analysis (BIA)

La BIA e il punto di partenza di qualsiasi strategia di DR. Identifica i processi aziendali critici, quantifica l'impatto della loro indisponibilita e definisce i parametri di ripristino.

#### Identificazione dei Processi Critici

Per ogni processo aziendale, determinare:

- Funzione supportata e utenti impattati.
- Sistemi IT da cui dipende.
- Impatto finanziario dell'indisponibilita (per ora, per giorno).
- Impatto reputazionale e legale.
- Dipendenze interne ed esterne (fornitori, clienti, partner).

#### Classificazione RTO/RPO per Sistema

| Classificazione | RTO | RPO | Esempi | Strategia |
|---|---|---|---|---|
| **Tier 1 — Mission Critical** | < 1 ora | < 15 minuti | ERP, database transazionale, email, autenticazione | HA attiva, replica sincrona, failover automatico |
| **Tier 2 — Business Critical** | 1-4 ore | < 1 ora | CRM, file server principali, sistemi HR, intranet | Replica asincrona, backup frequenti, procedure di failover documentate |
| **Tier 3 — Important** | 4-24 ore | < 4 ore | Server di sviluppo, sistemi di reporting, archivi | Backup regolari, restore da backup, hardware spare |
| **Tier 4 — Non Critical** | 24-72 ore | < 24 ore | Ambienti di test, documentazione, sistemi legacy | Backup giornaliero, ricostruzione da zero se necessario |

**RTO (Recovery Time Objective)**: tempo massimo accettabile per il ripristino del servizio dopo un'interruzione. Include il tempo per la diagnosi, il ripristino dell'infrastruttura, il restore dei dati, la validazione e il ritorno in produzione.

**RPO (Recovery Point Objective)**: quantita massima di dati che l'organizzazione puo permettersi di perdere, espressa in tempo. Un RPO di 1 ora significa che il backup/replica piu recente non deve essere piu vecchio di 1 ora.

#### MTPD (Maximum Tolerable Period of Disruption)

L'MTPD rappresenta il tempo massimo assoluto di interruzione che l'organizzazione puo sopportare prima di subire danni irreversibili (perdita di clienti chiave, sanzioni legali insuperabili, fallimento). L'MTPD e sempre superiore all'RTO e rappresenta il limite ultimo entro cui il ripristino deve assolutamente avvenire.

Relazione tra i parametri: RPO < RTO < MTPD

#### Valutazione dell'Impatto Finanziario

Per ogni sistema critico, stimare:

- **Costo diretto**: mancato fatturato, penali contrattuali, costi di straordinario.
- **Costo indiretto**: perdita di produttivita dei dipendenti, costo opportunita.
- **Costo reputazionale**: difficile da quantificare ma spesso il piu significativo nel lungo termine.
- **Costo di ripristino**: hardware sostitutivo, consulenze esterne, licenze temporanee.

#### Mappatura delle Dipendenze

Creare una mappa delle dipendenze tra sistemi che evidenzi:

- Dipendenze upstream (da chi dipende questo sistema).
- Dipendenze downstream (chi dipende da questo sistema).
- Single Point of Failure (SPOF) nell'architettura.
- Ordine di ripristino corretto (non si puo ripristinare l'applicazione prima del database da cui dipende, ne il database prima dello storage e della rete).

### DRP (Disaster Recovery Plan)

Il DRP e il documento operativo che guida le attivita di ripristino durante un disastro. Deve essere sufficientemente dettagliato da poter essere eseguito sotto pressione, potenzialmente da personale diverso dal team abituale.

#### Struttura del Piano

1. **Introduzione e ambito**: scopo del piano, sistemi coperti, scenari considerati.
2. **Team di DR**: ruoli, responsabilita, reperibilita, sostituti.
3. **Criteri di attivazione**: quando e come si attiva il piano di DR.
4. **Piano di comunicazione**: chi informare, quando, come.
5. **Procedure di ripristino**: step-by-step per ogni sistema, ordinati per priorita.
6. **Validazione e ritorno alla normalita**: come verificare il ripristino e come effettuare il failback.
7. **Appendici**: contatti, credenziali (in formato sicuro), diagrammi di rete, inventario hardware.

#### Ruoli e Responsabilita del Team DR

| Ruolo | Responsabilita | Competenze Richieste |
|---|---|---|
| **DR Manager** | Decisione di attivazione, coordinamento generale, comunicazione con il management | Leadership, visione d'insieme |
| **Infrastructure Lead** | Ripristino rete, storage, server | Sistemistica avanzata, virtualizzazione |
| **Application Lead** | Ripristino applicazioni, validazione funzionale | Conoscenza applicativa, database |
| **Security Lead** | Valutazione sicurezza, gestione accessi, forensics (se necessario) | Sicurezza IT, incident response |
| **Communication Lead** | Comunicazione interna, esterna, con autorita | Comunicazione aziendale, relazioni |

Per ogni ruolo definire un titolare e almeno un sostituto. Tutti devono avere accesso ai documenti di DR anche in caso di indisponibilita dell'infrastruttura primaria (copie stampate, cloud storage separato).

#### Piano di Comunicazione

Il piano di comunicazione deve prevedere:

**Comunicazione interna**:
- Notifica immediata al management (entro 30 minuti dall'evento).
- Aggiornamenti periodici al personale (ogni 2-4 ore durante la crisi).
- Canali alternativi se i sistemi aziendali sono indisponibili (telefono, messaggistica personale, radio).

**Comunicazione esterna**:
- Notifica ai clienti impattati con tempistiche realistiche per il ripristino.
- Comunicazione ai fornitori critici.
- Gestione dei media (se l'evento ha rilevanza pubblica).
- Notifica al Garante Privacy entro 72 ore se coinvolti dati personali (obbligo GDPR).

**Comunicazione con le autorita**:
- Forze dell'ordine in caso di attacco informatico.
- Autorita di vigilanza per settori regolamentati.
- ACN (Agenzia per la Cybersicurezza Nazionale) per incidenti significativi.

#### Procedure di Ripristino per Priorita di Sistema

L'ordine di ripristino deve seguire le dipendenze tecniche e la classificazione di criticita:

1. **Infrastruttura di base**: rete (routing, switching, firewall, DNS, DHCP), storage, hypervisor.
2. **Servizi di identita**: Active Directory / LDAP, servizi di autenticazione.
3. **Servizi Tier 1**: database primari, ERP, sistemi transazionali.
4. **Servizi Tier 2**: email, file server, CRM.
5. **Servizi Tier 3**: sistemi secondari, reporting, sviluppo.
6. **Validazione end-to-end**: test funzionale completo di ogni servizio ripristinato.

#### Lista Contatti Fornitori

Mantenere una lista aggiornata (verificata trimestralmente) dei contatti di emergenza:

- Fornitore hardware (contratto di supporto, numero di case, SLA).
- Fornitore hosting/cloud (contatto premium support, numero account).
- ISP (contatto tecnico emergenze, circuiti alternativi).
- Fornitore software critici (supporto prioritario).
- Consulenti specialistici (DBA, sicurezza, networking).

#### Opzioni per il Sito di Recovery

| Opzione | Costo | RTO Raggiungibile | Descrizione |
|---|---|---|---|
| **Hot Site** | Molto alto | < 1 ora | Infrastruttura completamente replicata, dati sincronizzati, pronta all'uso |
| **Warm Site** | Alto | 4-24 ore | Infrastruttura predisposta, richiede restore dei dati e configurazione finale |
| **Cold Site** | Medio | 24-72+ ore | Solo spazio fisico e connettivita, richiede installazione completa |
| **Cloud DR** | Variabile (pay-per-use) | 1-4 ore | Infrastruttura dormiente nel cloud, attivata on-demand (Azure Site Recovery, AWS DR, Zerto) |
| **DRaaS** | Medio-alto | 1-4 ore | Disaster Recovery as a Service, gestito dal provider |

### Scenari di Disaster

Per ogni scenario, definire procedure specifiche e dettagliate.

#### Guasto del Data Center

Cause: interruzione prolungata dell'alimentazione elettrica, guasto del sistema di raffreddamento, evento naturale (alluvione, terremoto, incendio).

**Procedura di risposta**:

1. **Rilevamento e valutazione** (0-30 minuti): confermare l'indisponibilita, valutare l'entita del danno, stimare il tempo di ripristino in loco.
2. **Decisione** (30-60 minuti): se il ripristino in loco non e possibile entro l'RTO, attivare il piano di DR.
3. **Attivazione del sito DR** (1-4 ore): avviare l'infrastruttura di recovery, verificare la connettivita.
4. **Ripristino dei servizi** (4-24 ore): seguire l'ordine di priorita definito, ripristinare i dati dall'ultimo backup/replica.
5. **Validazione** (2-4 ore): test funzionale di ogni servizio, verifica delle prestazioni.
6. **Comunicazione**: notifica del ripristino agli utenti, istruzioni per l'accesso al sito DR.
7. **Pianificazione del failback**: definire tempi e modalita per il ritorno al sito primario una volta ripristinato.

#### Attacco Ransomware

Il ransomware rappresenta oggi la minaccia piu frequente e devastante per le infrastrutture IT. La procedura di risposta deve essere rapida e strutturata.

**Fase 1 — Isolamento** (primi 15 minuti):
- Disconnettere immediatamente dalla rete i sistemi infetti identificati.
- Bloccare le connessioni est-ovest (micro-segmentazione, VLAN isolation).
- Disabilitare gli account potenzialmente compromessi.
- NON spegnere i sistemi infetti (potrebbe distruggere evidenze forensi in memoria).

**Fase 2 — Valutazione** (1-4 ore):
- Determinare la portata dell'infezione (quali sistemi sono colpiti, quali dati sono cifrati).
- Identificare la variante di ransomware (puo esistere un decryptor gratuito).
- Verificare l'integrita dei backup — controllare se i backup sono stati compromessi.
- Valutare se i backup immutabili/air-gapped sono intatti.

**Fase 3 — Recovery** (4-72 ore, dipende dalla portata):
- Ricostruire l'infrastruttura di base da zero (non fidarsi dei sistemi potenzialmente compromessi).
- Ripristinare Active Directory da backup verificato e pulito.
- Ripristinare i servizi in ordine di priorita da backup verificati.
- Cambiare TUTTE le credenziali (utenti, servizi, amministratori, certificati).
- Applicare le patch di sicurezza mancanti prima di riconnettere i sistemi alla rete.

**Fase 4 — Comunicazione**:
- Notifica al Garante Privacy entro 72 ore se coinvolti dati personali.
- Notifica alle forze dell'ordine (Polizia Postale).
- Comunicazione ai clienti/partner se i loro dati sono potenzialmente esposti.
- NON pagare il riscatto senza il coinvolgimento di esperti legali e di sicurezza.

**Fase 5 — Post-incident**:
- Analisi forense per identificare il vettore di attacco.
- Implementazione delle contromisure per prevenire la recidiva.
- Aggiornamento del piano di DR con le lezioni apprese.

#### Guasto Hardware

**Server singolo**:
- Identificare il componente guasto (disco, alimentatore, memoria, scheda madre).
- Se il server e virtualizzato: riavviare la VM su un altro host (HA automatico o manuale).
- Se il server e fisico: sostituire il componente (sotto contratto di supporto) o ripristinare su hardware alternativo (bare metal restore).
- Tempo stimato: 1-4 ore per VM, 4-24 ore per server fisici.

**Storage array**:
- Guasto di un singolo disco: rebuild automatico dal RAID (monitorare il completamento).
- Guasto di piu dischi: attivare il piano di DR se il RAID non e piu in grado di proteggere i dati.
- Guasto del controller: failover sul controller secondario (configurazione dual-controller).
- Guasto totale: ripristino da backup su storage alternativo.

**Apparecchiatura di rete**:
- Switch/router: attivare il percorso alternativo (spanning tree, VRRP/HSRP, routing ridondante).
- Firewall: failover su unita secondaria (HA pair) o applicare la configurazione di backup su un dispositivo sostitutivo.
- Documentare la configurazione di ogni dispositivo di rete per consentire la rapida riconfigurazione di un sostituto.

#### Corruzione Logica

**Corruzione del database**:
- Eseguire i controlli di integrita nativi (DBCC CHECKDB, pg_amcheck).
- Tentare il ripristino dalla corruzione con gli strumenti nativi.
- Se il ripristino non e possibile: restore da backup con point-in-time recovery fino all'istante precedente la corruzione.
- Indagare la causa della corruzione (hardware, bug software, errore umano).

**Cancellazione accidentale**:
- Dati su file server: ripristino da shadow copy (se disponibile) o da backup.
- Record di database: restore da backup con applicazione selettiva dei dati mancanti.
- Oggetti Active Directory: ripristino dal cestino AD (se abilitato) o restore autoritativo.
- VM: ripristino da backup a livello di VM o di singoli file.

#### Outage del Cloud Provider

L'affidamento a un singolo cloud provider introduce un rischio di concentrazione.

**Mitigazioni preventive**:
- Architettura multi-region per i servizi critici.
- Backup dei dati cloud in una posizione indipendente dal provider.
- Documentazione delle procedure di migrazione verso un provider alternativo.
- Contratti con SLA chiari e penali per indisponibilita.

**Procedura di failover**:
- Attivazione delle risorse nella region secondaria.
- Aggiornamento dei record DNS per reindirizzare il traffico.
- Verifica della consistenza dei dati replicati.
- Monitoraggio del ripristino della region primaria per pianificare il failback.

### DR Testing

Il test del piano di DR e essenziale per verificarne l'efficacia e mantenere il team preparato.

#### Tipi di Test

**Tabletop Exercise (esercitazione teorica)**:
- Il team si riunisce e percorre il piano di DR su carta, discutendo le azioni per uno scenario specifico.
- Durata: 2-4 ore.
- Costo: basso (solo tempo del personale).
- Valore: identifica lacune nel piano, migliora la consapevolezza del team, verifica la completezza della documentazione.
- Frequenza raccomandata: trimestrale.

**Walkthrough (percorso guidato)**:
- Il team percorre fisicamente le procedure (accesso ai sistemi di backup, verifica dei contatti, localizzazione della documentazione) senza eseguire effettivamente il ripristino.
- Durata: mezza giornata.
- Frequenza raccomandata: semestrale.

**Simulation (simulazione)**:
- Ripristino effettivo di uno o piu sistemi in un ambiente isolato, simulando uno scenario specifico.
- Durata: 1-2 giorni.
- Costo: medio (risorse di test, tempo del personale).
- Frequenza raccomandata: annuale.

**Full Test (test completo)**:
- Attivazione completa del sito di DR con failover di tutti i servizi e validazione end-to-end.
- Durata: 1-3 giorni.
- Costo: alto (potenziale impatto sulla produzione, risorse significative).
- Frequenza raccomandata: annuale (per le organizzazioni piu mature) o biennale.

#### Template di Pianificazione del Test

```
PIANO DI TEST DR
================
Data: [data]
Tipo: [tabletop/walkthrough/simulation/full]
Scenario: [descrizione dello scenario simulato]
Sistemi coinvolti: [elenco]
Team partecipante: [nomi e ruoli]
Prerequisiti: [backup verificati, ambiente di test pronto, ecc.]

FASI DEL TEST:
1. [fase] — Responsabile: [nome] — Tempo previsto: [durata]
2. [fase] — Responsabile: [nome] — Tempo previsto: [durata]
...

CRITERI DI SUCCESSO:
- [ ] Tutti i sistemi Tier 1 ripristinati entro RTO
- [ ] Dati ripristinati con perdita massima pari a RPO
- [ ] Validazione funzionale superata per tutti i servizi
- [ ] Comunicazioni eseguite secondo il piano

RISULTATI:
Tempo effettivo di ripristino per sistema: [tabella]
Problemi riscontrati: [elenco]
Gap identificati: [elenco]
Azioni correttive: [elenco con responsabile e scadenza]
```

#### Revisione Post-Test e Miglioramenti

Dopo ogni test, condurre una sessione di lessons learned:

- Cosa ha funzionato bene.
- Cosa non ha funzionato o ha richiesto piu tempo del previsto.
- Gap nella documentazione o nelle procedure.
- Competenze mancanti nel team.
- Aggiornamenti necessari al piano di DR.

Documentare tutte le azioni correttive con responsabile e scadenza. Verificare il completamento delle azioni prima del test successivo.

#### Documentazione dei Gap e Remediation

Mantenere un registro dei gap identificati durante i test:

| Gap ID | Descrizione | Severita | Azione Correttiva | Responsabile | Scadenza | Stato |
|---|---|---|---|---|---|---|
| GAP-001 | Documentazione restore AD incompleta | Alta | Aggiornare la procedura con i passaggi mancanti | [nome] | [data] | Aperto |
| GAP-002 | Tempo di restore DB > RTO (3h vs 1h RTO) | Critica | Implementare replica sincrona | [nome] | [data] | In corso |
| GAP-003 | Contatti fornitore hardware non aggiornati | Media | Verificare e aggiornare la lista contatti | [nome] | [data] | Chiuso |

---

## Business Continuity

La business continuity va oltre il disaster recovery IT, abbracciando l'intera organizzazione e le sue capacita di continuare a operare durante e dopo un'interruzione.

### BCP vs DRP

Il **Business Continuity Plan (BCP)** e il **Disaster Recovery Plan (DRP)** sono complementari ma distinti:

| Aspetto | BCP | DRP |
|---|---|---|
| **Ambito** | Intera organizzazione | Infrastruttura IT |
| **Focus** | Continuita delle operazioni aziendali | Ripristino dei sistemi IT |
| **Include** | Processi, persone, strutture, IT, fornitori | Server, rete, storage, applicazioni, dati |
| **Attivazione** | Qualsiasi interruzione significativa | Disastro che colpisce l'IT |
| **Responsabile** | Management aziendale | IT Management |
| **Standard** | ISO 22301 | ISO 27031 |

Il BCP comprende aspetti che il DRP non copre:

- Sede alternativa per i dipendenti (non solo per i server).
- Continuita delle operazioni manuali (come lavorare senza IT).
- Gestione delle risorse umane durante la crisi (turni, reperibilita, welfare).
- Continuita della catena di fornitura.
- Gestione della comunicazione con clienti e stakeholder.
- Aspetti legali e regolamentari.

L'integrazione tra BCP e DRP e fondamentale: il DRP e una componente del BCP, ma il BCP fornisce il contesto aziendale che guida le priorita del DRP. L'RTO definito nel DRP deve essere coerente con le esigenze di continuita operativa definite nel BCP.

### Alta Disponibilita

L'alta disponibilita (High Availability, HA) e la strategia che consente di mantenere i servizi operativi anche in caso di guasto di un singolo componente, eliminando i single point of failure.

#### Clustering

**Windows Server Failover Clustering (WSFC)**:
- Fino a 64 nodi per cluster.
- Supporto per ruoli clusterizzati: File Server, Hyper-V, SQL Server, DHCP, ecc.
- Quorum basato su witness (disco, file share, cloud).
- Richiede storage condiviso (SAN, Storage Spaces Direct) o replica dello storage.

```powershell
# Validazione prerequisiti cluster
Test-Cluster -Node "node1","node2" -Include "Storage","Network","Inventory"

# Creazione cluster
New-Cluster -Name "CL-PROD" -Node "node1","node2" `
  -StaticAddress 192.168.1.100 -NoStorage
```

**Pacemaker/Corosync (Linux)**:
- Stack HA standard per Linux.
- Corosync gestisce la comunicazione e il membership tra i nodi.
- Pacemaker gestisce le risorse e le decisioni di failover.
- Supporto per risorse di ogni tipo: IP virtuali, filesystem, servizi, database.

```bash
# Configurazione risorsa IP virtuale con Pacemaker
pcs resource create VIP ocf:heartbeat:IPaddr2 \
  ip=192.168.1.100 cidr_netmask=24 \
  op monitor interval=10s

# Configurazione risorsa servizio
pcs resource create WebServer systemd:httpd \
  op monitor interval=30s
pcs constraint colocation add WebServer with VIP INFINITY
pcs constraint order VIP then WebServer
```

#### Replica del Database

**SQL Server Always On Availability Groups**:
- Replica sincrona (RPO = 0, failover automatico) o asincrona (RPO > 0, failover manuale).
- Fino a 9 repliche (5 sincrone).
- Le repliche secondarie possono essere utilizzate per letture e backup.
- Richiede Windows Server Failover Clustering come infrastruttura sottostante (o Pacemaker su Linux).

**PostgreSQL Streaming Replication**:
- Replica sincrona o asincrona basata su WAL streaming.
- Supporto per multiple standby in cascata.
- Failover manuale (promozione dello standby) o automatico con Patroni/repmgr.

```yaml
# Configurazione Patroni per HA PostgreSQL
scope: postgres-cluster
name: node1
restapi:
  listen: 0.0.0.0:8008
postgresql:
  listen: 0.0.0.0:5432
  data_dir: /var/lib/postgresql/data
  parameters:
    wal_level: replica
    max_wal_senders: 5
    synchronous_standby_names: "*"
```

#### Load Balancing

Il bilanciamento del carico distribuisce il traffico tra piu istanze di un servizio:

- **Layer 4 (TCP/UDP)**: HAProxy, NGINX, LVS, cloud load balancer. Bilanciamento basato su IP/porta.
- **Layer 7 (HTTP/HTTPS)**: HAProxy, NGINX, Traefik, Apache mod_proxy. Bilanciamento basato su URL, header, cookie.
- **Algoritmi**: round-robin, least connections, IP hash, weighted.
- **Health check**: verifica periodica della disponibilita dei backend, rimozione automatica dei nodi non rispondenti.

```nginx
# Configurazione NGINX come load balancer con health check
upstream backend {
    least_conn;
    server 192.168.1.11:8080 weight=3;
    server 192.168.1.12:8080 weight=2;
    server 192.168.1.13:8080 backup;
}

server {
    listen 80;
    location / {
        proxy_pass http://backend;
        proxy_next_upstream error timeout;
        proxy_connect_timeout 5s;
    }
}
```

#### Ridondanza Geografica

Per la protezione da disastri regionali:

- **Active-Active**: entrambi i siti servono traffico di produzione. Massima resilienza ma complessita elevata (gestione della consistenza dei dati, bilanciamento globale).
- **Active-Passive**: il sito secondario e in standby e viene attivato solo in caso di failover. Piu semplice ma con RTO piu alto.
- **Replica dello storage**: sincrona (RPO = 0, richiede bassa latenza tra i siti, tipicamente < 10 ms) o asincrona (RPO > 0, tollerante alla latenza).

#### DNS Failover

Il DNS puo essere utilizzato come meccanismo di failover di alto livello:

- **DNS-based load balancing**: multiple record A/AAAA per lo stesso nome, risoluzione round-robin.
- **Health-check DNS**: servizi come Route 53 (AWS), Cloudflare, NS1 che monitorano la disponibilita degli endpoint e rimuovono automaticamente i record dei siti non disponibili.
- **TTL basso**: per consentire un failover rapido, configurare TTL bassi (30-300 secondi) sui record DNS critici, accettando il maggior carico sui server DNS.

Limitazione: il DNS failover dipende dal rispetto del TTL da parte dei client e dei resolver intermedi. Alcuni client e resolver cachano i record oltre il TTL, causando ritardi nel failover.

### Continuita Operativa

La continuita operativa riguarda la capacita dell'organizzazione di mantenere le operazioni essenziali anche quando i sistemi IT non sono disponibili.

#### Procedure di Fallback Manuale

Per ogni processo critico, documentare una procedura manuale alternativa:

- **Ordini**: moduli cartacei pre-stampati, trasmissione telefonica, registrazione manuale.
- **Comunicazioni**: uso di telefoni cellulari personali, gruppi di messaggistica pre-configurati, email personali.
- **Autenticazione**: elenco di password temporanee in busta sigillata, procedure di accesso di emergenza.
- **Pagamenti**: procedure manuali con la banca, bonifici telefonici, pagamenti di emergenza.

Queste procedure devono essere documentate, distribuite (anche in formato cartaceo) e periodicamente aggiornate.

#### Documentazione dei Workaround

Ogni workaround deve specificare:

- Condizioni di attivazione (quando usare il workaround).
- Procedura passo-passo (comprensibile anche da personale non IT).
- Limitazioni (cosa non si puo fare con il workaround).
- Durata massima sostenibile (per quanto tempo il workaround e praticabile).
- Procedura di rientro (come passare dal workaround al sistema ripristinato, inclusa l'eventuale re-immissione dei dati registrati manualmente).

#### Comunicazione durante l'Outage

Definire un piano di comunicazione specifico per la durata dell'interruzione:

- **Primo annuncio** (entro 30 minuti): conferma dell'interruzione, causa (se nota), stima dei tempi.
- **Aggiornamenti periodici** (ogni 2-4 ore): stato del ripristino, azioni in corso, nuova stima dei tempi.
- **Comunicazione di ripristino**: conferma della risoluzione, eventuali limitazioni residue, istruzioni per gli utenti.
- **Post-mortem** (entro 1 settimana): comunicazione delle cause, azioni intraprese, miglioramenti pianificati.

Canali di comunicazione da prevedere: pagina di stato web (ospitata esternamente), email (se disponibile), SMS, messaggistica istantanea, centralino telefonico.

#### MBCO (Minimum Business Continuity Objective)

L'MBCO definisce il livello minimo di servizio che deve essere garantito durante un'interruzione. Non si tratta di ripristinare tutto al 100%, ma di definire cosa e assolutamente indispensabile.

Esempio di MBCO:

| Servizio | Livello Normale | MBCO durante Crisi |
|---|---|---|
| Ordini cliente | 100% online, real-time | 50% capacita, ritardo 4h accettabile |
| Email | Piena funzionalita | Solo invio/ricezione, no archivio |
| ERP | Tutte le funzioni | Solo contabilita e fatturazione |
| Assistenza clienti | Multicanale | Solo telefono |
| Reporting | Real-time | Report manuali giornalieri |

L'MBCO aiuta a definire le priorita di ripristino: i servizi necessari per raggiungere l'MBCO vengono ripristinati per primi.

---

## Best Practices

1. **Trattare il backup come infrastruttura critica**: il sistema di backup deve avere lo stesso livello di ridondanza, monitoraggio e manutenzione dei sistemi di produzione. Un server di backup con un singolo disco o senza monitoraggio e un rischio, non una protezione.

2. **Automatizzare tutto, verificare tutto**: ogni operazione di backup deve essere completamente automatizzata (scheduling, esecuzione, verifica, notifica). Parallelamente, implementare verifiche automatiche dell'integrita e test di restore periodici. L'automazione elimina l'errore umano, ma la verifica garantisce che l'automazione funzioni.

3. **Separare le credenziali del backup**: le credenziali utilizzate per gestire i backup devono essere distinte da quelle degli amministratori di sistema. In caso di compromissione delle credenziali di amministrazione (scenario ransomware), i backup devono rimanere protetti. Implementare l'autenticazione multi-fattore per l'accesso ai sistemi di backup.

4. **Documentare ogni procedura di restore, non solo di backup**: la documentazione di come eseguire un backup e relativamente semplice. La vera sfida e documentare come ripristinare ogni tipo di sistema, passo dopo passo, in modo che anche un operatore meno esperto possa eseguire il ripristino sotto pressione. Includere screenshot, comandi esatti e verifiche intermedie.

5. **Implementare l'immutabilita dei backup**: l'immutabilita non e un optional ma una necessita. Almeno una copia di ogni backup critico deve essere immutabile per un periodo minimo pari alla retention definita. Verificare regolarmente che l'immutabilita sia effettivamente attiva e funzionante.

6. **Testare il DR almeno annualmente con un test realisitico**: un piano di DR non testato e solo un documento. Eseguire almeno un tabletop exercise trimestrale e un test completo annuale. Il test deve essere realistico: non informare il team in anticipo dei dettagli dello scenario, misurare i tempi reali, documentare ogni problema.

7. **Mantenere il piano di DR aggiornato e accessibile**: il piano deve essere aggiornato a ogni cambiamento infrastrutturale significativo (nuovo server, nuova applicazione, cambio di provider). Deve essere accessibile anche quando l'infrastruttura primaria non e disponibile: copie cartacee, cloud storage esterno, copia sui dispositivi mobili dei responsabili.

8. **Monitorare proattivamente la salute dello storage di backup**: non aspettare che lo spazio finisca o che un disco si guasti. Monitorare SMART, contatori di errore, spazio disponibile, prestazioni I/O. Pianificare la sostituzione preventiva dei componenti e l'espansione della capacita.

9. **Classificare i dati e calibrare la protezione**: non tutti i dati meritano lo stesso livello di protezione. Classificare i dati per criticita e sensibilita, quindi calibrare backup frequency, retention e strategia di DR di conseguenza. Sovra-proteggere dati non critici spreca risorse; sotto-proteggere dati critici e un rischio inaccettabile.

10. **Includere il cloud nella strategia, non dipendere esclusivamente da esso**: il cloud offre vantaggi significativi per il DR (elasticita, pay-per-use, distribuzione geografica) ma non elimina la necessita di una strategia propria. I dati nel cloud devono essere protetti con backup indipendente dal provider. Le configurazioni cloud (IaC) devono essere versionate e protette.

---

## Troubleshooting

### Backup job fallisce con errore VSS

**Sintomo**: il backup di un server Windows fallisce con errori relativi a Volume Shadow Copy Service.

**Cause possibili e soluzioni**:
- **VSS writer in stato di errore**: verificare lo stato dei writer con `vssadmin list writers`. Se un writer e in stato "Failed" o "Waiting for completion", riavviare il servizio corrispondente. Se il problema persiste, riavviare il servizio VSS (`net stop vss && net start vss`).
- **Spazio shadow copy insufficiente**: verificare con `vssadmin list shadowstorage`. Aumentare il limite massimo: `vssadmin resize shadowstorage /For=C: /On=C: /MaxSize=20%`.
- **Timeout VSS**: applicazioni pesanti (Exchange, SQL) possono impiegare troppo tempo per il freeze. Aumentare il timeout VSS nel software di backup o programmare il backup in orari di minor carico.
- **Driver di filtro incompatibili**: antivirus o software di crittografia possono interferire con VSS. Escludere le directory di backup dal monitoraggio antivirus.

### Backup incrementale molto piu grande del previsto

**Sintomo**: un backup incrementale occupa uno spazio simile a un full, pur non essendo cambiati molti dati.

**Cause possibili e soluzioni**:
- **CBT resettato**: un evento (snapshot rimosso, migrazione VM, aggiornamento dell'hypervisor) ha invalidato il tracking dei blocchi modificati. Il software esegue un "full read" per ricostruire la baseline. Verificare i log del software di backup per conferma.
- **Deframmentazione**: la deframmentazione del disco nella VM riscrive i blocchi in posizioni diverse, facendoli apparire come modificati al CBT. Disabilitare la deframmentazione automatica sulle VM.
- **File di paginazione/swap**: file temporanei grandi che cambiano costantemente. Escluderli dal backup o configurare il software per gestirli.
- **Database con crescita automatica**: un database che si e espanso automaticamente appare come un grande cambiamento. Monitorare la crescita dei database.

### Restore fallisce per catena incrementale interrotta

**Sintomo**: il restore da backup incrementale fallisce perche manca un anello della catena.

**Soluzioni**:
- Verificare se esiste un backup full o differenziale piu recente che consenta di bypassare l'incrementale mancante.
- Se il backup corrotto e recente, tentare il ripristino dal penultimo full + incrementali disponibili (accettando una perdita di dati piu ampia).
- Per prevenire in futuro: aumentare la frequenza dei full/synthetic full per limitare la lunghezza della catena di incrementali. Una catena di 7 incrementali e molto piu sicura di una di 30.

### Tempo di restore superiore all'RTO

**Sintomo**: i test dimostrano che il restore richiede piu tempo dell'RTO definito.

**Soluzioni**:
- **Rete**: verificare che la velocita di trasferimento tra repository di backup e server target sia adeguata. Considerare link dedicati o diretti.
- **Storage**: utilizzare storage ad alte prestazioni per il repository di backup (SSD per i backup recenti).
- **Parallelismo**: se il software lo supporta, aumentare il numero di stream di restore paralleli.
- **Instant Recovery**: per ambienti virtualizzati, soluzioni come Veeam Instant Recovery avviano la VM direttamente dal backup mentre i dati vengono migrati in background, riducendo drasticamente l'RTO.
- **Replica vs restore**: per i sistemi Tier 1, valutare la replica continua al posto del restore da backup. Il failover su una replica e ordini di grandezza piu veloce del restore.
- **Rivedere l'RTO**: se le soluzioni tecniche non sono sufficienti o il costo e proibitivo, discutere con il management la possibilita di rivedere l'RTO in base a un'analisi costi-benefici aggiornata.

### Backup su nastro non leggibile

**Sintomo**: i nastri conservati per il long-term retention non sono leggibili quando servono.

**Cause e prevenzioni**:
- **Degrado del nastro**: i nastri hanno una vita utile limitata (tipicamente 15-30 anni in condizioni ottimali, molto meno in condizioni reali). Programmare la riscrittura periodica dei nastri a lungo termine.
- **Incompatibilita drive**: i nastri scritti con un drive di una generazione possono non essere leggibili con drive di generazioni successive. Mantenere almeno un drive compatibile con il formato piu vecchio in uso, oppure migrare i dati a ogni cambio generazionale.
- **Condizioni di conservazione**: temperatura (18-24 gradi C), umidita (40-50%), assenza di campi magnetici. Verificare periodicamente le condizioni del caveau.
- **Verifica periodica**: eseguire una lettura di verifica dei nastri archiviati almeno una volta all'anno.

### Deduplicazione che degrada le prestazioni

**Sintomo**: il backup rallenta significativamente dopo l'attivazione della deduplicazione.

**Soluzioni**:
- **RAM insufficiente**: la deduplicazione inline richiede RAM significativa per mantenere l'indice dei blocchi in memoria. Verificare che il server di backup abbia RAM sufficiente (regola empirica: 1 GB di RAM per ogni TB di dati deduplicati per alcune soluzioni).
- **Passare a post-process**: se la deduplicazione inline impatta la finestra di backup, passare alla deduplicazione post-process che viene eseguita dopo il completamento del backup.
- **Storage dell'indice su SSD**: l'indice di deduplicazione deve risiedere su storage veloce (SSD/NVMe). Un indice su disco rotazionale causa enormi rallentamenti.
- **Dimensione del blocco**: blocchi di deduplicazione piu grandi riducono il carico computazionale ma diminuiscono il rapporto di deduplicazione. Trovare il bilanciamento ottimale per il proprio workload.

### Replica asincrona con ritardo crescente

**Sintomo**: il lag di replica tra il sito primario e il sito DR aumenta progressivamente, compromettendo l'RPO.

**Soluzioni**:
- **Banda insufficiente**: calcolare il change rate medio e di picco e confrontarlo con la banda disponibile. Se il change rate supera la banda, la replica non potra mai recuperare il ritardo. Aumentare la banda o ottimizzare la compressione.
- **Latenza di rete**: la latenza impatta le prestazioni della replica, specialmente quella sincrona. Verificare la latenza con strumenti come `ping` e `iperf3`, indagare eventuali problemi di routing.
- **Carico del sistema**: se il server sorgente e sotto carico eccessivo, la generazione dei dati di replica viene rallentata. Programmare i picchi di scrittura (batch job, manutenzione) in orari diversi.
- **Throttling**: verificare che il software di replica non sia configurato con limiti di banda che ne riducono l'efficacia.

### Backup cloud lento o in timeout

**Sintomo**: i backup verso storage cloud (S3, Azure Blob, Google Cloud Storage) sono lenti o falliscono per timeout.

**Soluzioni**:
- **Upload parallelo**: configurare il software per utilizzare upload multi-part e multithread.
- **Compressione e deduplicazione lato sorgente**: ridurre la quantita di dati da trasferire comprimendo e deduplicando prima dell'invio.
- **Regione dello storage**: scegliere la regione cloud piu vicina per minimizzare la latenza.
- **Proxy o gateway**: utilizzare un gateway locale che faccia da buffer e gestisca il trasferimento in modo asincrono (ad esempio, AWS Storage Gateway).
- **Verifica della connessione**: testare la velocita effettiva verso lo storage cloud con strumenti dedicati, escludere problemi di ISP o di peering.

---

> **Nota**: questa guida deve essere considerata un documento vivo, da aggiornare a ogni cambiamento significativo dell'infrastruttura, a ogni test di DR e a ogni incidente che riveli lacune nella strategia di protezione. La periodicita minima di revisione raccomandata e semestrale.

---

## Backup Immutabile Avanzato

L'immutabilita dei backup e passata da best practice raccomandata a requisito imprescindibile. Secondo il rapporto Verizon 2025 Data Breach Investigations Report, il 44% di tutte le violazioni nel 2025 ha coinvolto ransomware, e l'89% delle organizzazioni ha subito tentativi di attacco ai propri repository di backup. In questo scenario, un backup che puo essere modificato o cancellato dall'attaccante non offre alcuna protezione reale.

### Modelli di Immutabilita

L'immutabilita puo essere implementata a diversi livelli dello stack tecnologico. La scelta del modello dipende dall'infrastruttura esistente, dal budget e dal livello di protezione richiesto.

#### S3 Object Lock — Compliance Mode vs Governance Mode

Amazon S3 e i provider compatibili S3 offrono due modalita di Object Lock con caratteristiche diverse:

| Caratteristica | Compliance Mode | Governance Mode |
|---|---|---|
| **Protezione** | Nessuno puo cancellare o sovrascrivere, incluso l'account root AWS | Gli utenti con permessi speciali possono rimuovere la protezione |
| **Caso d'uso** | Backup critici, conformita regolamentare (GDPR, SOX, HIPAA) | Protezione operativa con flessibilita amministrativa |
| **Riduzione retention** | Impossibile fino alla scadenza | Possibile con permesso `s3:BypassGovernanceRetention` |
| **Rischio** | Se configurata con retention troppo lunga, i costi di storage non possono essere ridotti | Un attaccante con credenziali privilegiate potrebbe bypassare la protezione |
| **Raccomandazione** | Usare per backup di conformita e copie anti-ransomware | Usare per backup operativi dove serve flessibilita |

**Configurazione pratica di S3 Object Lock con Compliance Mode**:

```bash
# Creazione bucket con Object Lock abilitato (deve essere abilitato alla creazione)
aws s3api create-bucket \
  --bucket backup-immutabile-prod \
  --region eu-south-1 \
  --create-bucket-configuration LocationConstraint=eu-south-1 \
  --object-lock-enabled-for-bucket

# Configurazione retention di default (90 giorni in Compliance Mode)
aws s3api put-object-lock-configuration \
  --bucket backup-immutabile-prod \
  --object-lock-configuration '{
    "ObjectLockEnabled": "Enabled",
    "Rule": {
      "DefaultRetention": {
        "Mode": "COMPLIANCE",
        "Days": 90
      }
    }
  }'

# Verifica della configurazione
aws s3api get-object-lock-configuration \
  --bucket backup-immutabile-prod
```

**Verifica dell'immutabilita**: dopo la configurazione, eseguire un test di cancellazione per confermare che l'immutabilita sia effettivamente attiva:

```bash
# Tentativo di cancellazione (deve fallire con errore AccessDenied)
aws s3api delete-object \
  --bucket backup-immutabile-prod \
  --key test-backup-file.dat

# Output atteso:
# An error occurred (AccessDenied) when calling the DeleteObject operation:
# Access Denied
```

#### Veeam Hardened Repository

Il Veeam Hardened Repository (VHR) implementa l'immutabilita a livello di file system Linux sfruttando l'attributo immutable (`chattr +i`). I file di backup vengono resi immutabili dal sistema operativo per la durata della retention definita.

**Requisiti e architettura del VHR**:

- Sistema operativo: Ubuntu Server LTS (consigliato 22.04 o 24.04), senza interfaccia grafica.
- Account di servizio: un utente non-root con accesso SSH limitato, utilizzato solo per il deployment iniziale. Dopo il deployment, l'accesso SSH puo essere disabilitato per l'utente di servizio.
- Storage: XFS come file system (richiesto per il supporto fast clone/reflink), preferibilmente su volumi dedicati con crittografia LUKS.
- Rete: segmentazione di rete dedicata, accesso limitato esclusivamente dal Veeam Backup Server.
- Nessun accesso root permanente al repository: l'immutabilita e applicata dal sistema operativo e non puo essere rimossa senza accesso fisico alla macchina.

**Hardening aggiuntivo raccomandato**:

```bash
# Disabilitare SSH password authentication
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl restart sshd

# Configurare firewall per accesso solo dal Veeam server
ufw default deny incoming
ufw allow from 192.168.10.50/32 to any port 6162  # Veeam data mover
ufw enable

# Verificare che i file di backup siano immutabili
lsattr /mnt/backup-repo/backups/*.vbk
# Output atteso: ----i----------- /mnt/backup-repo/backups/file.vbk
```

#### BorgBackup Append-Only Mode

BorgBackup supporta una modalita append-only che impedisce la cancellazione o la modifica degli archivi esistenti sul server remoto, pur consentendo la creazione di nuovi archivi.

**Configurazione server-side append-only**:

```bash
# File ~/.ssh/authorized_keys sul server di backup
# Forzare append-only mode per la chiave SSH del client
command="borg serve --restrict-to-repository /backup/borg-repo --append-only",restrict ssh-ed25519 AAAA... client@hostname
```

Con questa configurazione, il client puo creare nuovi backup ma non puo eseguire `borg delete`, `borg prune` o `borg compact` sul repository remoto. La manutenzione del repository (pruning, compaction) deve essere eseguita localmente sul server di backup da un amministratore separato, con credenziali distinte da quelle utilizzate per il backup.

**Verifica periodica dell'append-only mode**:

```bash
# Dal client, tentare un prune (deve fallire)
borg prune --keep-daily 7 ssh://backup@server/./borg-repo
# Output atteso: Repository is in append-only mode

# Dal server (accesso locale), eseguire la manutenzione pianificata
borg prune --keep-daily 30 --keep-weekly 12 --keep-monthly 24 /backup/borg-repo
borg compact /backup/borg-repo
```

#### Air-Gap Design Patterns

L'air-gap fisico rimane la protezione piu forte contro attacchi informatici sofisticati. Un sistema air-gapped e fisicamente disconnesso dalla rete e viene connesso solo durante le finestre di backup pianificate.

**Pattern 1 — Nastro LTO offline**:
- I nastri vengono scritti durante la finestra di backup notturna.
- Dopo la scrittura, i nastri vengono espulsi automaticamente dalla libreria e conservati in un caveau ignifugo.
- I nastri non sono accessibili dalla rete in nessun momento.
- Limitazione: latenza elevata per il restore (tempo di recupero fisico dei nastri).

**Pattern 2 — Disco USB rotativo**:
- Due o piu dischi USB vengono alternati (uno connesso, uno in cassaforte).
- Rotazione giornaliera o settimanale.
- Adatto a piccole organizzazioni o filiali con dati limitati.
- Limitazione: capacita limitata, rischio di danneggiamento meccanico.

**Pattern 3 — Storage di rete con disconnessione automatizzata**:
- Un NAS o server dedicato viene connesso alla rete tramite uno switch gestito.
- Uno script automatizzato connette la porta dello switch solo durante la finestra di backup, quindi la disconnette.
- Il backup viene eseguito, verificato, e la porta viene chiusa automaticamente.

```bash
#!/bin/bash
# Script: air-gap-backup.sh
# Connette la porta dello switch, esegue il backup, disconnette la porta

SWITCH_IP="192.168.1.1"
SWITCH_PORT="Gi0/24"
SNMP_COMMUNITY="backup-mgmt"
BACKUP_TARGET="/mnt/airgap-storage"
LOG="/var/log/airgap-backup.log"

log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $1" >> "$LOG"; }

# Attivare la porta dello switch
log "Attivazione porta $SWITCH_PORT"
snmpset -v2c -c "$SNMP_COMMUNITY" "$SWITCH_IP" \
  IF-MIB::ifAdminStatus.24 i 1

sleep 30  # Attesa link-up e mount NFS

# Montaggio storage
mount -t nfs 192.168.20.100:/backup "$BACKUP_TARGET"
if [ $? -ne 0 ]; then
  log "ERRORE: mount NFS fallito"
  # Disattivare la porta anche in caso di errore
  snmpset -v2c -c "$SNMP_COMMUNITY" "$SWITCH_IP" \
    IF-MIB::ifAdminStatus.24 i 2
  exit 1
fi

# Esecuzione backup (esempio con restic)
log "Inizio backup"
restic -r "$BACKUP_TARGET/restic-repo" backup /data/critical \
  --password-file /etc/restic/password.txt \
  --tag airgap --tag "$(date +%Y%m%d)" \
  2>> "$LOG"

BACKUP_STATUS=$?

# Smontaggio e disconnessione
umount "$BACKUP_TARGET"
log "Disattivazione porta $SWITCH_PORT"
snmpset -v2c -c "$SNMP_COMMUNITY" "$SWITCH_IP" \
  IF-MIB::ifAdminStatus.24 i 2

if [ $BACKUP_STATUS -eq 0 ]; then
  log "Backup air-gap completato con successo"
else
  log "ERRORE: backup fallito con codice $BACKUP_STATUS"
fi
```

### Immutabilita su File System Linux

Oltre alle soluzioni specifiche per il backup, Linux offre meccanismi nativi per rendere immutabili i file a livello di file system:

```bash
# Rendere un file immutabile (richiede root)
chattr +i /backup/archive/backup-20260524.tar.gz

# Verificare l'attributo
lsattr /backup/archive/backup-20260524.tar.gz
# Output: ----i---------e----- /backup/archive/backup-20260524.tar.gz

# Rimuovere l'immutabilita (richiede root, da proteggere con accesso limitato)
chattr -i /backup/archive/backup-20260524.tar.gz
```

Per una protezione piu robusta, combinare `chattr +i` con la rimozione della capability `CAP_LINUX_IMMUTABLE` dall'ambiente, impedendo anche a root di rimuovere l'attributo immutable senza un riavvio del sistema.

---

## Backup Cloud Nativo

Le piattaforme cloud offrono servizi di backup nativi che si integrano profondamente con le risorse cloud, semplificando la gestione e riducendo la complessita operativa. E fondamentale comprendere che il modello di responsabilita condivisa attribuisce al cliente la responsabilita della protezione dei propri dati, anche nelle piattaforme gestite.

### AWS Backup

AWS Backup fornisce un servizio centralizzato per la gestione dei backup di risorse AWS (EC2, RDS, DynamoDB, EFS, S3, EBS, FSx). Supporta policy-driven backup plans, cross-region copy, cross-account copy e vault lock per l'immutabilita.

**Architettura raccomandata**:

```
┌─────────────────────────────────────────────────────────┐
│                    Account di Produzione                 │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐      │
│  │ EC2  │  │ RDS  │  │ EFS  │  │ DynDB│  │  S3  │      │
│  └──┬───┘  └──┬───┘  └──┬───┘  └──┬───┘  └──┬───┘      │
│     └──────────┴────────┴─────────┴─────────┘           │
│                        │                                 │
│              ┌─────────▼──────────┐                      │
│              │    AWS Backup      │                      │
│              │  (Backup Plan)     │                      │
│              └─────────┬──────────┘                      │
│                        │                                 │
│              ┌─────────▼──────────┐                      │
│              │   Backup Vault     │                      │
│              │ (Vault Lock WORM)  │                      │
│              └─────────┬──────────┘                      │
│                        │                                 │
│              Cross-Region Copy                           │
│                        │                                 │
└────────────────────────┼────────────────────────────────┘
                         │
           ┌─────────────▼──────────────┐
           │   Account DR Separato       │
           │  ┌───────────────────────┐  │
           │  │  Backup Vault (DR)    │  │
           │  │  Vault Lock attivo    │  │
           │  │  Region: eu-west-1    │  │
           │  └───────────────────────┘  │
           └────────────────────────────┘
```

**Configurazione di un Backup Plan con AWS CLI**:

```bash
# Creazione del Backup Vault con crittografia KMS dedicata
aws backup create-backup-vault \
  --backup-vault-name vault-produzione \
  --encryption-key-arn arn:aws:kms:eu-south-1:123456789012:key/abc-123 \
  --region eu-south-1

# Attivazione Vault Lock (immutabilita WORM)
# MinRetentionDays: i backup non possono essere cancellati prima di 30 giorni
# MaxRetentionDays: retention massima consentita 365 giorni
# ChangeableForDays: 3 giorni di grazia per modificare la configurazione
aws backup put-backup-vault-lock-configuration \
  --backup-vault-name vault-produzione \
  --min-retention-days 30 \
  --max-retention-days 365 \
  --changeable-for-days 3

# Creazione del Backup Plan (JSON)
cat > backup-plan.json << 'PLAN_EOF'
{
  "BackupPlanName": "piano-produzione-giornaliero",
  "Rules": [
    {
      "RuleName": "backup-giornaliero",
      "TargetBackupVaultName": "vault-produzione",
      "ScheduleExpression": "cron(0 2 * * ? *)",
      "StartWindowMinutes": 60,
      "CompletionWindowMinutes": 180,
      "Lifecycle": {
        "MoveToColdStorageAfterDays": 30,
        "DeleteAfterDays": 365
      },
      "CopyActions": [
        {
          "DestinationBackupVaultArn": "arn:aws:backup:eu-west-1:123456789012:backup-vault:vault-dr",
          "Lifecycle": {
            "DeleteAfterDays": 90
          }
        }
      ]
    },
    {
      "RuleName": "backup-settimanale",
      "TargetBackupVaultName": "vault-produzione",
      "ScheduleExpression": "cron(0 3 ? * SAT *)",
      "StartWindowMinutes": 120,
      "CompletionWindowMinutes": 480,
      "Lifecycle": {
        "MoveToColdStorageAfterDays": 90,
        "DeleteAfterDays": 730
      }
    }
  ]
}
PLAN_EOF

aws backup create-backup-plan \
  --backup-plan file://backup-plan.json
```

### Azure Backup e Azure Site Recovery

Azure offre due servizi complementari per la protezione dei dati:

- **Azure Backup**: protezione dei dati con backup automatizzati in Recovery Services Vault. Supporta VM Azure, SQL Server in VM, Azure Files, Azure Blob, Azure Database for PostgreSQL e workload on-premises tramite MARS Agent o MABS (Microsoft Azure Backup Server).

- **Azure Site Recovery (ASR)**: replica continua delle VM e orchestrazione del failover per scenari di disaster recovery. ASR replica le VM da una region primaria a una region secondaria e consente il failover orchestrato con un singolo clic.

**Configurazione Azure Backup con Azure CLI**:

```bash
# Creazione del Recovery Services Vault
az backup vault create \
  --resource-group rg-backup \
  --name vault-backup-prod \
  --location italynorth

# Configurazione della policy di backup
az backup policy create \
  --resource-group rg-backup \
  --vault-name vault-backup-prod \
  --name policy-vm-giornaliera \
  --policy '{
    "schedulePolicy": {
      "schedulePolicyType": "SimpleSchedulePolicy",
      "scheduleRunFrequency": "Daily",
      "scheduleRunTimes": ["2026-01-01T02:00:00Z"]
    },
    "retentionPolicy": {
      "retentionPolicyType": "LongTermRetentionPolicy",
      "dailySchedule": {
        "retentionTimes": ["2026-01-01T02:00:00Z"],
        "retentionDuration": { "count": 30, "durationType": "Days" }
      },
      "weeklySchedule": {
        "daysOfTheWeek": ["Saturday"],
        "retentionTimes": ["2026-01-01T02:00:00Z"],
        "retentionDuration": { "count": 12, "durationType": "Weeks" }
      },
      "monthlySchedule": {
        "retentionScheduleFormatType": "Daily",
        "retentionScheduleDaily": { "daysOfTheMonth": [{ "date": 1 }] },
        "retentionTimes": ["2026-01-01T02:00:00Z"],
        "retentionDuration": { "count": 12, "durationType": "Months" }
      }
    }
  }'

# Abilitazione backup per una VM
az backup protection enable-for-vm \
  --resource-group rg-backup \
  --vault-name vault-backup-prod \
  --vm rg-produzione/vm-erp-01 \
  --policy-name policy-vm-giornaliera
```

**Immutabilita in Azure — Immutable Vault**:

Azure supporta l'immutabilita dei backup attraverso la funzionalita Immutable Vault, che impedisce operazioni che potrebbero causare la perdita dei punti di ripristino prima della scadenza della retention. Puo essere configurata in modalita Locked (irreversibile) o Unlocked (reversibile).

### Google Cloud Backup and DR

Google Cloud offre il servizio Backup and DR per la protezione di VM Compute Engine, database Cloud SQL e file system. Il servizio supporta backup incrementali basati su snapshot, retention personalizzabile e ripristino cross-region.

### Confronto dei Servizi Cloud di Backup

| Caratteristica | AWS Backup | Azure Backup | GCP Backup & DR |
|---|---|---|---|
| **Risorse supportate** | EC2, RDS, DynamoDB, EFS, S3, EBS, FSx, Neptune, DocumentDB | VM, SQL Server, Azure Files, Blob, PostgreSQL, SAP HANA | Compute Engine, Cloud SQL, Filestore |
| **Immutabilita** | Vault Lock (WORM) | Immutable Vault (Locked/Unlocked) | Backup lock |
| **Cross-region** | Si, tramite Copy Actions | Si, tramite GRS/RA-GRS | Si, multi-region |
| **Cross-account** | Si, tramite AWS Organizations | Si, tramite Cross-Subscription | Si, tramite Cross-Project |
| **Crittografia** | KMS (CMK o AWS-managed) | AES-256, CMK supportato | CMEK o Google-managed |
| **DR orchestration** | AWS Elastic Disaster Recovery | Azure Site Recovery | DR orchestration nativo |
| **Costo modello** | Pay-per-GB protetto + storage | Per istanza protetta + storage | Per GB protetto |

---

## Backup per Ambienti Kubernetes e Container

L'adozione crescente di Kubernetes e delle architetture containerizzate introduce nuove sfide per il backup e il disaster recovery. I workload containerizzati sono intrinsecamente diversi dalle VM tradizionali: sono effimeri, distribuiti, e comprendono sia risorse del cluster (Deployment, Service, ConfigMap, Secret) sia dati persistenti (PersistentVolumeClaim).

### Sfide Specifiche del Backup Kubernetes

- **Stato distribuito**: lo stato dell'applicazione e distribuito tra etcd (stato del cluster), PersistentVolumes (dati applicativi), ConfigMaps/Secrets (configurazione) e risorse custom (CRD).
- **Efemerita dei Pod**: i Pod vengono creati e distrutti continuamente; il backup deve catturare lo stato logico, non lo stato fisico dei singoli container.
- **Consistenza applicativa**: un backup a livello di file system del PV potrebbe catturare i dati in uno stato inconsistente se l'applicazione sta scrivendo. Servono hook pre/post-backup per garantire la consistenza.
- **Multi-tenancy**: in ambienti multi-tenant, il backup deve rispettare i confini dei namespace e i permessi RBAC.

### Backup di etcd

etcd e il datastore critico di Kubernetes che contiene l'intero stato del cluster. La perdita di etcd significa la perdita della configurazione di tutti i workload, servizi, permessi e risorse custom.

```bash
# Snapshot di etcd (eseguire su un nodo control plane)
ETCDCTL_API=3 etcdctl snapshot save /backup/etcd/snapshot-$(date +%Y%m%d-%H%M).db \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# Verifica dello snapshot
ETCDCTL_API=3 etcdctl snapshot status /backup/etcd/snapshot-20260524-0200.db \
  --write-out=table

# Restore di etcd (su un cluster completamente fermo)
ETCDCTL_API=3 etcdctl snapshot restore /backup/etcd/snapshot-20260524-0200.db \
  --data-dir=/var/lib/etcd-restored \
  --initial-cluster="master1=https://192.168.1.10:2380" \
  --initial-advertise-peer-urls="https://192.168.1.10:2380" \
  --name=master1
```

**Frequenza raccomandata del backup etcd**: ogni 1-2 ore per cluster di produzione. Retention minima: 7 giorni di snapshot orari, 4 settimane di snapshot giornalieri.

### Velero

Velero (precedentemente Heptio Ark, donato alla CNCF nel 2025) e lo strumento open source standard per il backup di cluster Kubernetes. Velero esegue il backup delle risorse del cluster (oggetti API) e dei PersistentVolumes, consentendo il ripristino completo o parziale in caso di disastro o migrazione.

**Installazione e configurazione di base**:

```bash
# Installazione Velero con provider AWS S3
velero install \
  --provider aws \
  --bucket velero-backup-prod \
  --secret-file ./credentials-velero \
  --backup-location-config region=eu-south-1 \
  --snapshot-location-config region=eu-south-1 \
  --plugins velero/velero-plugin-for-aws:v1.10.0 \
  --use-node-agent \
  --default-volumes-to-fs-backup

# Creazione di un backup schedulato giornaliero
velero schedule create daily-full \
  --schedule="0 2 * * *" \
  --ttl 720h \
  --include-namespaces production,staging \
  --snapshot-volumes=true

# Backup on-demand di un namespace specifico
velero backup create erp-backup-20260524 \
  --include-namespaces erp-production \
  --snapshot-volumes=true \
  --wait

# Verifica dello stato del backup
velero backup describe erp-backup-20260524 --details

# Restore di un namespace da backup
velero restore create erp-restore-20260524 \
  --from-backup erp-backup-20260524 \
  --include-namespaces erp-production \
  --restore-volumes=true
```

**Backup hooks per consistenza applicativa**:

```yaml
# Annotazione del Pod per eseguire comandi pre/post backup
apiVersion: v1
kind: Pod
metadata:
  name: postgresql-prod
  annotations:
    pre.hook.backup.velero.io/command: '["/bin/bash", "-c", "pg_dump -U postgres mydb > /backup/pre-velero-dump.sql"]'
    pre.hook.backup.velero.io/timeout: "120s"
    post.hook.backup.velero.io/command: '["/bin/bash", "-c", "rm -f /backup/pre-velero-dump.sql"]'
```

### Veeam Kasten K10

Kasten K10 e la soluzione enterprise di Veeam per il backup Kubernetes, con un approccio application-aware che comprende l'intero stack applicativo (risorse API, PV, configurazioni) come una singola unita.

**Caratteristiche distintive rispetto a Velero**:

- **Application-aware**: Kasten comprende le relazioni tra le risorse Kubernetes e le tratta come un'applicazione unificata.
- **Blueprint**: meccanismo per definire azioni pre/post backup specifiche per ogni tipo di applicazione (PostgreSQL, MySQL, MongoDB, Cassandra).
- **Policy-driven**: gestione centralizzata delle policy di backup con interfaccia web.
- **Disaster recovery cross-cluster**: replica dei backup tra cluster Kubernetes in region diverse.
- **Ransomware detection**: scansione dei backup per individuare indicatori di compromissione.

### Confronto Velero vs Kasten K10

| Caratteristica | Velero | Kasten K10 |
|---|---|---|
| **Licenza** | Open Source (Apache 2.0) | Commerciale (free tier limitato) |
| **Application-awareness** | Limitata (hooks manuali) | Nativa (Blueprint) |
| **Interfaccia** | CLI | Web UI + CLI |
| **Backup PV** | CSI Snapshots, Kopia (dedup/compress) | CSI Snapshots, export generico |
| **Cross-cluster DR** | Manuale (backup + restore su altro cluster) | Automatizzato con policy |
| **Ransomware scan** | No | Si |
| **CNCF** | Sandbox (donato da Broadcom 2025) | No (Veeam/proprietario) |
| **Costo** | Gratuito (solo costi storage) | Licenza per nodo worker |
| **Ideale per** | Team DevOps, ambienti medio-piccoli | Enterprise, ambienti regolamentati |

---

## DR Orchestration e Automazione

L'orchestrazione del disaster recovery automatizza la sequenza di operazioni necessarie per il failover e il failback, riducendo l'RTO e eliminando errori umani durante situazioni di stress elevato. Le soluzioni moderne di DR orchestration vanno oltre il semplice ripristino dei dati, gestendo l'intera catena di dipendenze tra sistemi.

### Zerto — Continuous Data Protection

Zerto (acquisita da HPE) e una piattaforma di DR basata su Continuous Data Protection (CDP) che replica ogni operazione di scrittura in tempo reale verso il sito DR, senza snapshot e senza agent. Il journal-based recovery consente il ripristino a qualsiasi punto nel tempo degli ultimi 30 giorni (configurabile), con granularita di pochi secondi.

**Caratteristiche principali di Zerto**:

- **RPO in secondi**: la replica continua consente RPO di 5-15 secondi, rispetto ai minuti/ore del backup tradizionale.
- **Journal-Based Recovery**: ogni scrittura viene registrata in un journal che consente il point-in-time recovery con granularita secondi.
- **Orchestrazione del failover**: Zerto orchestra automaticamente l'ordine di avvio delle VM, le configurazioni di rete, e gli script personalizzati.
- **Failover test non-disruptive**: possibilita di testare il failover senza impatto sulla produzione, utilizzando una copia isolata dei dati replicati.
- **Multi-piattaforma**: supporto per VMware, Hyper-V, AWS, Azure, con possibilita di DR cross-platform (es. da VMware on-premises ad Azure).
- **Supporto Proxmox**: dalla versione 11.2 (aprile 2026), supporto completo per vSphere 9 e Proxmox VE 9.0.

### Veeam Disaster Recovery Orchestrator

Veeam Orchestrator (parte di Veeam Data Platform) consente di creare orchestration plans che automatizzano l'intero processo di DR, includendo pre-step (verifiche prerequisiti), failover ordinato, re-IP automatico, script personalizzati e verifica post-failover. L'integrazione nativa con Veeam Backup & Replication e con le repliche Veeam rende l'orchestrazione trasparente.

### Azure Site Recovery — Orchestrazione

Azure Site Recovery (ASR) offre orchestrazione del DR per VM Azure e workload on-premises replicati verso Azure. I Recovery Plans di ASR definiscono l'ordine di failover delle macchine, raggruppandole in gruppi di avvio sequenziale e aggiungendo azioni personalizzate (script PowerShell, Azure Automation runbook) tra i gruppi.

### Template di DR Runbook Dettagliato

Il seguente template fornisce un modello operativo completo per un runbook di disaster recovery, con procedure step-by-step per ogni fase del ripristino.

```
============================================================
          DISASTER RECOVERY RUNBOOK — v3.2
          [Nome Organizzazione]
          Data ultimo aggiornamento: 2026-05-24
          Prossima revisione: 2026-11-24
============================================================

SEZIONE 1: INFORMAZIONI GENERALI
---------------------------------
Documento:          DR-RUN-001
Classificazione:    RISERVATO
Responsabile:       [Nome DR Manager]
Distribuzione:      Team DR (lista in Sezione 2)
Copie fisiche:      Cassaforte sede principale, cassaforte sede DR,
                    dispositivi mobili responsabili

SEZIONE 2: TEAM DI DISASTER RECOVERY
--------------------------------------
Ruolo                  | Titolare         | Telefono       | Sostituto
DR Manager             | [Nome]           | +39 xxx        | [Nome]
Infrastructure Lead    | [Nome]           | +39 xxx        | [Nome]
Network Lead           | [Nome]           | +39 xxx        | [Nome]
Database Lead (DBA)    | [Nome]           | +39 xxx        | [Nome]
Application Lead       | [Nome]           | +39 xxx        | [Nome]
Security Lead          | [Nome]           | +39 xxx        | [Nome]
Communication Lead     | [Nome]           | +39 xxx        | [Nome]

Contatti fornitori critici:
- Hardware:     [Fornitore] — Contratto: [ID] — Tel: [numero] — SLA: 4h
- Hosting/Cloud: [Provider] — Account: [ID] — Premium Support: [numero]
- ISP primario: [ISP] — Circuito: [ID] — NOC: [numero]
- ISP backup:   [ISP] — Circuito: [ID] — NOC: [numero]

SEZIONE 3: CRITERI DI ATTIVAZIONE
-----------------------------------
Il DR Plan viene attivato quando:
- [ ] L'infrastruttura primaria e inaccessibile per > 30 minuti
  E il ripristino in-place stimato supera l'RTO del sistema Tier 1 piu critico
- [ ] Attacco ransomware confermato con impatto su sistemi di produzione
- [ ] Danno fisico al datacenter (incendio, alluvione, terremoto)
- [ ] Decisione del DR Manager su base discrezionale

Autorizzazione all'attivazione:
- Livello 1 (failover parziale, Tier 1 only): DR Manager
- Livello 2 (failover completo): DR Manager + CIO/CTO
- Livello 3 (failover con comunicazione esterna): DR Manager + CIO + CEO

SEZIONE 4: PROCEDURE DI FAILOVER — ORDINE DI RIPRISTINO
---------------------------------------------------------

FASE 0: VALUTAZIONE E DECISIONE (0-30 min)
  0.1 Confermare l'indisponibilita del datacenter primario
  0.2 Valutare l'entita del danno e stimare il tempo di ripristino in loco
  0.3 Attivare il conference bridge di emergenza: [numero/link]
  0.4 Decisione: attivare DR SI/NO
  0.5 Se SI: notificare tutti i membri del team DR (call tree)

FASE 1: INFRASTRUTTURA DI BASE (30 min - 2h)
  1.1 Verificare connettivita del sito DR
      Comando: ping -c 5 [IP gateway DR]
      Atteso: 0% packet loss
  1.2 Verificare storage DR disponibile e sano
      Comando: [comandi specifici per lo storage in uso]
  1.3 Avviare gli hypervisor (se non gia attivi)
  1.4 Verificare la rete DR (VLAN, routing, firewall)
      Comando: show ip route (sui router DR)
  1.5 Attivare la VPN site-to-site verso le sedi remote (se necessario)
  1.6 Documentare: ora di completamento, problemi riscontrati

FASE 2: SERVIZI DI IDENTITA (2h - 3h)
  2.1 Ripristinare il primo Domain Controller
      Metodo: [restore da backup / replica / VM pre-configurata]
      Verifica: dcdiag /v — tutti i test devono essere PASSED
  2.2 Verificare la risoluzione DNS
      Comando: nslookup [dominio] [IP DC DR]
  2.3 Verificare DHCP (se servito dal DC)
  2.4 Verificare la replica AD (se applicabile)
  2.5 Documentare: ora di completamento, problemi riscontrati

FASE 3: DATABASE (3h - 5h)
  3.1 Ripristinare il database SQL Server principale
      Metodo: restore da backup full + differential + log fino all'ultimo disponibile
      Comandi:
        RESTORE DATABASE [NomeDB] FROM DISK='[path_full]' WITH NORECOVERY;
        RESTORE DATABASE [NomeDB] FROM DISK='[path_diff]' WITH NORECOVERY;
        RESTORE LOG [NomeDB] FROM DISK='[path_log]' WITH RECOVERY;
      Verifica: DBCC CHECKDB([NomeDB]) WITH NO_INFOMSGS;
  3.2 Ripristinare il database PostgreSQL
      Metodo: pg_basebackup + WAL replay
      Verifica: SELECT count(*) FROM [tabella_critica];
  3.3 Aggiornare le stringhe di connessione nelle applicazioni (se necessario)
  3.4 Documentare: ora di completamento, perdita dati effettiva vs RPO

FASE 4: APPLICAZIONI TIER 1 (5h - 8h)
  4.1 Avviare il server ERP
      Verifica: login utente di test, creazione ordine di prova
  4.2 Avviare il server di posta
      Verifica: invio/ricezione email di test
  4.3 Avviare il server di autenticazione applicativa
      Verifica: login SSO da un client di test
  4.4 Documentare: ora di completamento, problemi riscontrati

FASE 5: APPLICAZIONI TIER 2 (8h - 12h)
  5.1 Avviare file server / NAS
  5.2 Avviare CRM
  5.3 Avviare intranet
  5.4 Documentare: ora di completamento

FASE 6: VALIDAZIONE END-TO-END (12h - 14h)
  6.1 Eseguire la checklist di validazione funzionale
      - [ ] Autenticazione AD funzionante
      - [ ] Risoluzione DNS corretta
      - [ ] Database accessibile e dati consistenti
      - [ ] ERP operativo (test ordine, test fattura)
      - [ ] Email funzionante (invio/ricezione interna ed esterna)
      - [ ] File server accessibile con permessi corretti
      - [ ] VPN per utenti remoti funzionante
      - [ ] Stampe funzionanti
      - [ ] Connessioni a sistemi esterni (banche, fornitori) operative
  6.2 Comunicazione formale di ripristino a tutti gli utenti

SEZIONE 5: PROCEDURA DI FAILBACK
----------------------------------
  1. Verificare che il sito primario sia completamente ripristinato e funzionante
  2. Sincronizzare i dati dal sito DR al sito primario (attenzione: i dati
     sul sito DR sono piu aggiornati durante il failover)
  3. Pianificare la finestra di failback (preferibilmente nel weekend)
  4. Eseguire il failback in ordine inverso rispetto al failover
  5. Verificare il funzionamento completo sul sito primario
  6. Mantenere il sito DR pronto per un eventuale re-failover per 48 ore
  7. Documentare l'intera procedura e aggiornare il runbook

SEZIONE 6: REGISTRO EVENTI
----------------------------
| Ora (UTC) | Evento | Azione | Responsabile | Note |
|-----------|--------|--------|-------------|------|
| [ora]     | [desc] | [azione] | [nome]    | [note]|
```

### Automazione del Failover con Script

L'automazione del failover riduce i tempi di ripristino e gli errori umani. Di seguito un esempio di script per l'orchestrazione del failover DNS:

```bash
#!/bin/bash
# Script: failover-dns.sh
# Aggiorna i record DNS per reindirizzare il traffico al sito DR

ZONE_ID="Z1234567890"
DR_IP_WEB="10.20.30.40"
DR_IP_MAIL="10.20.30.41"
DR_IP_VPN="10.20.30.42"
LOG="/var/log/dr-failover.log"
TTL=60

log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) [FAILOVER] $1" >> "$LOG"; }

log "=== INIZIO FAILOVER DNS ==="

# Aggiornamento record A per i servizi principali
for RECORD_NAME in "www.azienda.it" "erp.azienda.it" "portal.azienda.it"; do
  aws route53 change-resource-record-sets \
    --hosted-zone-id "$ZONE_ID" \
    --change-batch "{
      \"Changes\": [{
        \"Action\": \"UPSERT\",
        \"ResourceRecordSet\": {
          \"Name\": \"$RECORD_NAME\",
          \"Type\": \"A\",
          \"TTL\": $TTL,
          \"ResourceRecords\": [{\"Value\": \"$DR_IP_WEB\"}]
        }
      }]
    }" 2>> "$LOG"
  log "Record $RECORD_NAME aggiornato a $DR_IP_WEB"
done

# Aggiornamento record MX
aws route53 change-resource-record-sets \
  --hosted-zone-id "$ZONE_ID" \
  --change-batch "{
    \"Changes\": [{
      \"Action\": \"UPSERT\",
      \"ResourceRecordSet\": {
        \"Name\": \"azienda.it\",
        \"Type\": \"MX\",
        \"TTL\": $TTL,
        \"ResourceRecords\": [{\"Value\": \"10 mail-dr.azienda.it\"}]
      }
    }]
  }" 2>> "$LOG"

log "=== FAILOVER DNS COMPLETATO ==="
log "Nota: la propagazione DNS richiede fino a $TTL secondi"
```

---

## Script Pratici di Backup

Questa sezione raccoglie script operativi pronti all'uso per i principali scenari di backup, con gestione degli errori, logging e notifiche.

### Script Restic — Backup Automatizzato con Retention e Healthcheck

```bash
#!/bin/bash
# Script: restic-daily-backup.sh
# Backup giornaliero automatizzato con Restic, retention GFS e healthcheck
# Prerequisiti: restic installato, repository inizializzato, variabili d'ambiente configurate

set -euo pipefail

# --- CONFIGURAZIONE ---
export RESTIC_REPOSITORY="s3:s3.eu-south-1.amazonaws.com/backup-restic-prod"
export RESTIC_PASSWORD_FILE="/etc/restic/password.txt"
export AWS_ACCESS_KEY_ID="$(cat /etc/restic/aws-key-id.txt)"
export AWS_SECRET_ACCESS_KEY="$(cat /etc/restic/aws-secret-key.txt)"

BACKUP_PATHS="/data/production /data/shared /etc /var/lib/postgresql"
EXCLUDE_FILE="/etc/restic/excludes.txt"
HEALTHCHECK_URL="https://hc-ping.com/uuid-della-healthcheck"
LOG_FILE="/var/log/restic/backup-$(date +%Y%m%d).log"
RETENTION_DAILY=7
RETENTION_WEEKLY=4
RETENTION_MONTHLY=12
RETENTION_YEARLY=3
MAX_BACKUP_AGE_HOURS=26  # Alert se l'ultimo backup e piu vecchio di 26 ore

# --- FUNZIONI ---
log() {
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) [$1] $2" | tee -a "$LOG_FILE"
}

notify_failure() {
  local msg="$1"
  log "ERROR" "$msg"
  # Notifica via webhook (Slack, Teams, ecc.)
  curl -sf -X POST "$HEALTHCHECK_URL/fail" -d "$msg" || true
  # Notifica via email
  echo "$msg" | mail -s "[BACKUP FALLITO] $(hostname) - $(date +%Y-%m-%d)" \
    backup-alert@azienda.it 2>/dev/null || true
}

cleanup() {
  if [ $? -ne 0 ]; then
    notify_failure "Backup interrotto con errore. Controllare $LOG_FILE"
  fi
}
trap cleanup EXIT

# --- INIZIO BACKUP ---
log "INFO" "=== Inizio backup giornaliero ==="

# Segnalare inizio al healthcheck
curl -sf "$HEALTHCHECK_URL/start" > /dev/null 2>&1 || true

# Pre-check: verificare che il repository sia raggiungibile
log "INFO" "Verifica connettivita al repository"
if ! restic snapshots --latest 1 > /dev/null 2>&1; then
  notify_failure "Repository non raggiungibile: $RESTIC_REPOSITORY"
  exit 1
fi

# Esecuzione backup
log "INFO" "Avvio backup di: $BACKUP_PATHS"
restic backup \
  $BACKUP_PATHS \
  --exclude-file="$EXCLUDE_FILE" \
  --tag "daily" \
  --tag "$(hostname)" \
  --tag "$(date +%Y%m%d)" \
  --verbose \
  --json 2>&1 | tee -a "$LOG_FILE"

BACKUP_EXIT=$?

if [ $BACKUP_EXIT -ne 0 ]; then
  notify_failure "Backup fallito con codice di uscita $BACKUP_EXIT"
  exit $BACKUP_EXIT
fi

log "INFO" "Backup completato con successo"

# Applicazione retention policy (forget + prune)
log "INFO" "Applicazione retention policy"
restic forget \
  --keep-daily $RETENTION_DAILY \
  --keep-weekly $RETENTION_WEEKLY \
  --keep-monthly $RETENTION_MONTHLY \
  --keep-yearly $RETENTION_YEARLY \
  --tag "$(hostname)" \
  --prune \
  --verbose 2>&1 | tee -a "$LOG_FILE"

# Verifica integrita (subset per non sovraccaricare — check completo settimanale)
DOW=$(date +%u)
if [ "$DOW" -eq 7 ]; then
  log "INFO" "Domenica: verifica integrita completa"
  restic check --read-data 2>&1 | tee -a "$LOG_FILE"
else
  log "INFO" "Verifica integrita parziale (10% dei dati)"
  restic check --read-data-subset=10% 2>&1 | tee -a "$LOG_FILE"
fi

# Segnalare successo al healthcheck
curl -sf "$HEALTHCHECK_URL" > /dev/null 2>&1 || true

log "INFO" "=== Backup giornaliero completato con successo ==="
```

**File di esclusione (`/etc/restic/excludes.txt`)**:

```
# File temporanei e cache
*.tmp
*.temp
*.swp
*~
.cache/
__pycache__/
node_modules/
.npm/

# File di swap e paginazione
/data/*/swap
pagefile.sys

# File di log voluminosi (gia gestiti separatamente)
/var/log/journal/

# Build artifacts
*.o
*.pyc
target/
build/
dist/

# Database socket files
/var/run/postgresql/
*.pid
*.sock
```

**Configurazione systemd timer per l'esecuzione automatica**:

```ini
# /etc/systemd/system/restic-backup.service
[Unit]
Description=Restic Backup Giornaliero
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/restic-daily-backup.sh
User=restic-backup
Group=restic-backup
Nice=19
IOSchedulingClass=idle

# Limiti di risorse per non impattare la produzione
CPUQuota=50%
MemoryMax=2G
```

```ini
# /etc/systemd/system/restic-backup.timer
[Unit]
Description=Esecuzione giornaliera del backup Restic

[Timer]
OnCalendar=*-*-* 02:00:00
Persistent=true
RandomizedDelaySec=300

[Install]
WantedBy=timers.target
```

```bash
# Abilitazione del timer
systemctl daemon-reload
systemctl enable --now restic-backup.timer

# Verifica stato
systemctl list-timers restic-backup.timer
```

### Script PowerShell — Backup Windows Server con Verifica

```powershell
<#
.SYNOPSIS
    Backup automatizzato Windows Server con Windows Server Backup e verifica.
.DESCRIPTION
    Esegue backup System State e volumi dati, verifica il risultato,
    invia notifica email.
#>

# --- CONFIGURAZIONE ---
$BackupTarget = "E:"  # Volume dedicato al backup
$MailServer = "smtp.azienda.it"
$MailFrom = "backup@azienda.it"
$MailTo = "it-ops@azienda.it"
$LogPath = "C:\Logs\Backup"
$MaxBackupAgeDays = 2
$Timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm"
$LogFile = Join-Path $LogPath "backup_$Timestamp.log"

# --- FUNZIONI ---
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $entry = "$(Get-Date -Format 'yyyy-MM-ddTHH:mm:ssZ') [$Level] $Message"
    Add-Content -Path $LogFile -Value $entry
    Write-Host $entry
}

function Send-Notification {
    param([string]$Subject, [string]$Body)
    try {
        Send-MailMessage -From $MailFrom -To $MailTo `
            -Subject $Subject -Body $Body `
            -SmtpServer $MailServer -Priority High
    } catch {
        Write-Log "Errore invio email: $_" "ERROR"
    }
}

# --- INIZIO ---
New-Item -ItemType Directory -Path $LogPath -Force | Out-Null
Write-Log "=== Inizio backup Windows Server ==="

# Verifica spazio disponibile sul target
$targetDrive = Get-PSDrive -Name ($BackupTarget.TrimEnd(':'))
$freeGB = [math]::Round($targetDrive.Free / 1GB, 2)
Write-Log "Spazio libero su $BackupTarget : $freeGB GB"

if ($freeGB -lt 50) {
    $msg = "ATTENZIONE: spazio insufficiente su $BackupTarget ($freeGB GB liberi)"
    Write-Log $msg "WARN"
    Send-Notification "[BACKUP WARNING] $env:COMPUTERNAME" $msg
}

# Backup System State
Write-Log "Avvio backup System State"
try {
    $wbJob = Start-WBBackup -Policy (Get-WBPolicy -Editable) -Force
    Write-Log "Backup System State completato"
} catch {
    Write-Log "System State backup fallito con errore: $_" "ERROR"
}

# Backup volumi dati con wbadmin
Write-Log "Avvio backup volumi dati (D:, F:)"
$wbResult = wbadmin start backup -backupTarget:$BackupTarget `
    -include:D:,F: -systemState -allCritical -quiet 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Log "Backup volumi completato con successo"
} else {
    $errorMsg = "Backup volumi FALLITO (exit code: $LASTEXITCODE)"
    Write-Log $errorMsg "ERROR"
    Send-Notification "[BACKUP FALLITO] $env:COMPUTERNAME" `
        "$errorMsg`n`nDettagli:`n$wbResult"
    exit 1
}

# Verifica: controllare l'ultimo backup
Write-Log "Verifica del backup piu recente"
$lastBackup = wbadmin get versions -backupTarget:$BackupTarget 2>&1
Write-Log "Ultimo backup: $lastBackup"

# Verifica eta del backup
$latestVersion = Get-WBBackupSet | Sort-Object -Property BackupTime -Descending |
    Select-Object -First 1
if ($latestVersion) {
    $age = (Get-Date) - $latestVersion.BackupTime
    if ($age.TotalDays -gt $MaxBackupAgeDays) {
        $msg = "ATTENZIONE: ultimo backup piu vecchio di $MaxBackupAgeDays giorni"
        Write-Log $msg "WARN"
        Send-Notification "[BACKUP STALE] $env:COMPUTERNAME" $msg
    } else {
        Write-Log "Eta backup OK: $([math]::Round($age.TotalHours, 1)) ore"
    }
}

# Report finale
$report = @"
Backup Report - $env:COMPUTERNAME - $Timestamp
================================================
Stato: COMPLETATO
Spazio libero target: $freeGB GB
Log completo: $LogFile
"@

Send-Notification "[BACKUP OK] $env:COMPUTERNAME - $Timestamp" $report
Write-Log "=== Backup completato con successo ==="
```

### Script borgmatic — Configurazione Completa con Systemd

```yaml
# /etc/borgmatic/config.yaml
# Configurazione borgmatic completa per server Linux di produzione

source_directories:
  - /data/production
  - /data/shared
  - /etc
  - /home
  - /var/lib/postgresql
  - /var/lib/mysql
  - /opt/applications

repositories:
  - path: ssh://borg@backup-server.azienda.it/./srv/borg/{hostname}
    label: locale
  - path: ssh://borg@backup-offsite.azienda.it/./srv/borg/{hostname}
    label: offsite

exclude_patterns:
  - '*.pyc'
  - '*/.cache'
  - '*/node_modules'
  - '*/tmp'
  - '*.tmp'
  - '*/lost+found'
  - '/var/log/journal'

exclude_caches: true
exclude_if_present:
  - .nobackup

encryption_passcommand: cat /etc/borgmatic/passphrase.txt

compression: auto,zstd,6

ssh_command: ssh -o BatchMode=yes -o ServerAliveInterval=30

archive_name_format: '{hostname}-{now:%Y-%m-%dT%H:%M:%S}'

retention:
  keep_within: 48H
  keep_daily: 7
  keep_weekly: 4
  keep_monthly: 12
  keep_yearly: 3

consistency:
  checks:
    - name: repository
      frequency: 1 week
    - name: archives
      frequency: 2 weeks
    - name: data
      frequency: 1 month

hooks:
  before_backup:
    - echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) Inizio backup borgmatic" >> /var/log/borgmatic/hook.log
    # Dump database PostgreSQL pre-backup
    - pg_dumpall -U postgres > /data/backup-staging/pg_dumpall.sql
    # Dump database MySQL pre-backup
    - mysqldump --single-transaction --routines --triggers --all-databases > /data/backup-staging/mysql_all.sql

  after_backup:
    - echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) Backup completato" >> /var/log/borgmatic/hook.log
    - rm -f /data/backup-staging/pg_dumpall.sql
    - rm -f /data/backup-staging/mysql_all.sql

  on_error:
    - echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) ERRORE backup" >> /var/log/borgmatic/hook.log
    - curl -sf -X POST "https://hc-ping.com/uuid-healthcheck/fail" || true

  healthchecks:
    ping_url: https://hc-ping.com/uuid-healthcheck
```

---

## Confronto Dettagliato degli Strumenti di Backup e DR

La seguente tabella fornisce un confronto approfondito tra le principali soluzioni di backup e disaster recovery disponibili nel 2025-2026, valutate su criteri operativi chiave.

### Tabella Comparativa — Soluzioni di Backup

| Criterio | Veeam B&R v13 | Commvault | BorgBackup | Restic | Bacula Enterprise | PBS | Nakivo | Duplicati |
|---|---|---|---|---|---|---|---|---|
| **Licenza** | Commerciale (CE gratuita 10 workload) | Commerciale | BSD (open source) | BSD (open source) | AGPLv3 / Commerciale | AGPLv3 (open source) | Commerciale | LGPL (open source) |
| **Piattaforme** | Windows, Linux, VMware, Hyper-V, Proxmox, cloud | Universale | Linux, macOS, BSD | Windows, Linux, macOS, BSD | Linux, Windows, macOS, Unix, AIX | Linux (Proxmox) | VMware, Hyper-V, Proxmox, AWS, Azure | Windows, Linux, macOS |
| **Deduplicazione** | Si (inline, repository-level) | Si (inline e post-process) | Si (content-defined chunking, eccellente 60-90%) | Si (content-defined chunking) | Si (global dedup) | Si (chunk-level, lato server) | Si | Si (block-level) |
| **Crittografia** | AES-256 (at-rest e in-transit) | AES-256 | AES-256-OCB o ChaCha20-Poly1305 (client-side) | AES-256 (client-side, sempre attiva) | AES-256, TLS | AES-256 (client-side) + TLS | AES-256 | AES-256 (client-side) |
| **Immutabilita** | Hardened Repository, S3 Object Lock | Si (WORM, Object Lock) | Append-only mode (server-side) | No nativo (dipende dal backend) | Si (WORM) | No nativo | Si (S3 Object Lock) | No nativo |
| **Cloud backend** | S3, Azure Blob, GCS, Wasabi | S3, Azure, GCS | No nativo (via rclone) | S3, Azure, GCS, B2, SFTP, REST | S3, Azure, GCS | S3 (via Proxmox) | S3, Azure, Wasabi | S3, Azure, GCS, B2, OneDrive, SFTP, FTP, WebDAV |
| **RPO minimo** | Secondi (CDP) | Minuti (replica) | Minuti (dipende da scheduling) | Minuti (dipende da scheduling) | Minuti | Minuti | 15 secondi (replica) | Ore (scheduling) |
| **GUI** | Si (desktop + web v13) | Si (web) | No (solo CLI, borgmatic wrapper) | No (solo CLI, Backrest GUI) | Si (web — BWeb, BAT) | Si (web, integrata Proxmox) | Si (web) | Si (web) |
| **Application-aware** | Si (AD, SQL, Exchange, Oracle, SAP) | Si (ampio supporto) | No (pre/post hook manuali) | No (pre/post hook manuali) | Si (plugin per MySQL, PostgreSQL, Oracle, MSSQL, SAP) | No | Si (SQL, Exchange, AD) | No |
| **Supporto nastro** | Si | Si | No | No | Si (eccellente) | No | No | No |
| **Verifica automatica** | SureBackup | Si | borg check --verify-data | restic check --read-data | Si (verify job) | Si (verify) | Si (screenshot verification) | No |
| **Curva apprendimento** | Media | Alta | Bassa (CLI) | Bassa (CLI) | Alta | Bassa (se gia su Proxmox) | Bassa | Bassa |
| **Costo indicativo** | €€€ (enterprise), gratuito CE | €€€€ | Gratuito | Gratuito | €€€ (enterprise), gratuito community | Gratuito | €€ | Gratuito |

### Tabella Comparativa — Soluzioni di DR e Replica

| Criterio | Zerto (HPE) | Azure Site Recovery | Veeam Orchestrator | AWS Elastic DR | Nakivo Site Recovery |
|---|---|---|---|---|---|
| **Tipo** | CDP journal-based | Replica asincrona | Orchestrazione backup/replica Veeam | Replica continua (block-level) | Replica VM |
| **RPO** | 5-15 secondi | 30 secondi - 5 minuti | Dipende da backup/replica sottostante | Sotto-secondo | 15 secondi (replica) |
| **RTO** | Minuti | Minuti - ore | Minuti (automatizzato) | Minuti | Minuti |
| **Piattaforme sorgente** | VMware, Hyper-V, AWS, Azure, Proxmox (v11.2+) | VM Azure, VMware, Hyper-V, fisici | VMware, Hyper-V (con Veeam) | AWS, VMware, fisici | VMware, Hyper-V, Proxmox |
| **Piattaforma target** | Multi-cloud, on-premises | Azure | On-premises, cloud | AWS | On-premises, cloud |
| **Test non-disruptivo** | Si (failover test isolato) | Si (test failover) | Si (test plan) | Si (drill) | Si |
| **Orchestrazione** | Si (VPG, boot order, script) | Si (Recovery Plans) | Si (plan con step, script, validazione) | Si (recovery plan) | Si (site recovery job) |
| **Costo** | €€€€ (per VM protetta) | Incluso Azure (costo per istanza) | Incluso in Veeam Data Platform | Pay-per-use AWS | €€ (per socket/VM) |

### Guida alla Scelta

**Per PMI con budget limitato e competenze Linux**: BorgBackup + borgmatic per il backup, Restic come seconda copia offsite su cloud. Nessun costo di licenza, eccellente deduplicazione e crittografia.

**Per PMI con infrastruttura VMware/Hyper-V**: Veeam Community Edition (gratuita fino a 10 workload) o Nakivo. Buon bilanciamento tra funzionalita e costo.

**Per ambienti Proxmox**: Proxmox Backup Server come scelta naturale. Integrazione nativa, deduplicazione, crittografia, gratuito.

**Per enterprise con requisiti stringenti di RTO**: Zerto o Veeam Data Platform con replica e orchestrazione. Costo elevato ma RPO in secondi e RTO in minuti.

**Per ambienti multi-cloud e Kubernetes**: Velero per Kubernetes (open source), combinato con i servizi nativi del cloud provider (AWS Backup, Azure Backup) per le risorse cloud.

**Per ambienti eterogenei con nastro**: Bacula Enterprise o Commvault. Supporto nastro eccellente, ampia copertura di piattaforme, complessita gestionale superiore.

---

## Metriche e KPI di Backup

La misurazione sistematica delle prestazioni del sistema di backup e fondamentale per garantire l'efficacia della strategia di protezione e giustificare gli investimenti. Senza metriche oggettive, e impossibile identificare trend negativi prima che causino problemi operativi.

### KPI Essenziali

| KPI | Formula | Target | Frequenza Misurazione |
|---|---|---|---|
| **Backup Success Rate** | (Job riusciti / Job totali) * 100 | >= 99% | Settimanale |
| **RPO Compliance** | (Backup entro RPO / Backup totali) * 100 | >= 99.5% | Settimanale |
| **RTO Compliance** | (Restore entro RTO / Restore totali) * 100 | >= 95% (test) | Trimestrale (durante test) |
| **Restore Test Pass Rate** | (Test riusciti / Test eseguiti) * 100 | >= 98% | Mensile |
| **Backup Window Compliance** | (Job completati entro finestra / Job totali) * 100 | >= 95% | Settimanale |
| **Storage Efficiency Ratio** | Dati protetti lordi / Storage effettivo utilizzato | >= 3:1 (con dedup) | Mensile |
| **Costo per TB Protetto** | Costo totale backup (infra + licenze + personale) / TB protetti | Trend decrescente | Trimestrale |
| **Data Change Rate** | Volume dati modificati giornaliero / Volume dati totale | Tracking trend | Giornaliero |
| **Backup Data Growth** | (Storage mese corrente - Storage mese precedente) / Storage mese precedente | Previsione capacita | Mensile |
| **Mean Time to Restore (MTTR)** | Tempo medio di restore per tipo di sistema | Sotto l'RTO target | Trimestrale |

### Dashboard di Monitoraggio Backup

Una dashboard efficace per il monitoraggio dei backup dovrebbe includere le seguenti sezioni:

**Vista operativa giornaliera**:
- Stato di tutti i job delle ultime 24 ore (successo, warning, fallito, mancato).
- Elenco dei job falliti con causa e azione correttiva.
- Utilizzo dello storage (percentuale e trend).
- Ultimo backup riuscito per ogni sistema critico.

**Vista settimanale/mensile**:
- Trend del Backup Success Rate.
- Trend della dimensione dei backup (per identificare anomalie).
- Compliance con la finestra di backup.
- Rapporto di deduplicazione e compressione.
- Previsione dell'esaurimento dello storage.

**Vista strategica trimestrale**:
- Risultati dei test di restore (pass/fail, tempi misurati vs RTO).
- RPO/RTO compliance per tier di sistema.
- Costo per TB protetto e trend.
- Gap identificati e stato delle azioni correttive.
- Raccomandazioni per miglioramenti.

### Monitoraggio con Prometheus e Grafana

Per ambienti che utilizzano lo stack Prometheus/Grafana, e possibile esporre metriche di backup personalizzate:

```yaml
# Esempio: prometheus exporter per metriche di backup (node_exporter textfile)
# Script eseguito dopo ogni backup per aggiornare le metriche

#!/bin/bash
METRICS_DIR="/var/lib/node_exporter/textfile_collector"
METRICS_FILE="$METRICS_DIR/backup_metrics.prom"

# Ultimo backup riuscito (timestamp Unix)
LAST_SUCCESS=$(date +%s)

# Dimensione ultimo backup in bytes
LAST_SIZE=$(restic snapshots --latest 1 --json | jq '.[0].stats.total_size // 0')

# Numero totale di snapshot
SNAP_COUNT=$(restic snapshots --json | jq 'length')

cat > "$METRICS_FILE" << METRICS_EOF
# HELP backup_last_success_timestamp_seconds Timestamp dell'ultimo backup riuscito
# TYPE backup_last_success_timestamp_seconds gauge
backup_last_success_timestamp_seconds{host="$(hostname)",repo="production"} $LAST_SUCCESS

# HELP backup_last_size_bytes Dimensione dell'ultimo backup in bytes
# TYPE backup_last_size_bytes gauge
backup_last_size_bytes{host="$(hostname)",repo="production"} $LAST_SIZE

# HELP backup_snapshot_count Numero totale di snapshot nel repository
# TYPE backup_snapshot_count gauge
backup_snapshot_count{host="$(hostname)",repo="production"} $SNAP_COUNT
METRICS_EOF
```

**Alert rules per Prometheus**:

```yaml
# /etc/prometheus/rules/backup_alerts.yml
groups:
  - name: backup_alerts
    rules:
      - alert: BackupStale
        expr: time() - backup_last_success_timestamp_seconds > 93600  # 26 ore
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Backup non eseguito da oltre 26 ore su {{ $labels.host }}"
          description: "L'ultimo backup riuscito risale a {{ $value | humanizeDuration }} fa."

      - alert: BackupStorageHigh
        expr: backup_storage_used_percent > 85
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Storage backup oltre l'85% su {{ $labels.host }}"

      - alert: BackupStorageCritical
        expr: backup_storage_used_percent > 95
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Storage backup oltre il 95% su {{ $labels.host }}"
```

---

## Backup SaaS — Microsoft 365 e Google Workspace

### Il Modello di Responsabilita Condivisa

Un errore comune e assumere che i provider SaaS (Microsoft, Google) si occupino del backup dei dati dei propri clienti. In realta, il modello di responsabilita condivisa prevede che:

- **Il provider** e responsabile della disponibilita dell'infrastruttura, della sicurezza della piattaforma e della protezione contro guasti hardware.
- **Il cliente** e responsabile della protezione dei propri dati contro cancellazione accidentale, attacchi ransomware, errori umani, insider threat e requisiti di retention regolamentare.

Microsoft stessa dichiara esplicitamente nelle condizioni di servizio che raccomanda l'uso di soluzioni di backup di terze parti per proteggere i dati dei clienti.

### Limiti della Retention Nativa

**Microsoft 365**:

| Elemento | Retention Nativa | Limitazione |
|---|---|---|
| Email (cestino) | 14-30 giorni | Non configurabile a lungo termine senza E5/add-on |
| OneDrive (cestino) | 93 giorni | Dopo l'eliminazione dell'account utente, i dati vengono eliminati dopo 30 giorni |
| SharePoint (cestino) | 93 giorni (2 stadi) | Primo stadio: utente; secondo stadio: admin. Dopo 93 giorni totali, eliminazione permanente |
| Teams (messaggi) | Retention policy configurabile | Richiede licenza di conformita per retention avanzata |
| Exchange Online (recovery) | 14 giorni (soft-delete) | Non adeguato per conformita a lungo termine |

**Google Workspace**:

| Elemento | Retention Nativa | Limitazione |
|---|---|---|
| Gmail (cestino) | 30 giorni | Dopo l'eliminazione dall'utente, non recuperabile senza Google Vault |
| Drive (cestino) | 30 giorni | Dopo l'eliminazione, non recuperabile |
| Google Vault | Retention configurabile | Richiede licenza aggiuntiva; non e un vero backup (non protegge da cancellazione dell'account) |

### Soluzioni di Backup per Microsoft 365

**Veeam Backup for Microsoft 365**: la soluzione piu diffusa per il backup di ambienti M365 enterprise. Supporta Exchange Online, SharePoint Online, OneDrive for Business e Teams. I dati vengono salvati in un repository locale o su object storage (S3, Azure Blob), offrendo al cliente il pieno controllo sui propri backup indipendentemente da Microsoft.

**Funzionalita chiave delle soluzioni di backup M365**:

- Backup granulare di singole email, file, siti, canali Teams.
- Retention indipendente dalle policy Microsoft (configurabile a lungo termine).
- Ricerca full-text nei backup per eDiscovery e conformita.
- Restore granulare (singolo elemento) o bulk (intero sito/casella).
- Supporto per la conformita GDPR: possibilita di cancellare dati specifici dai backup su richiesta.
- Legal hold sui backup per procedimenti legali.

### Considerazioni per il Backup SaaS

1. **Frequenza di backup**: per ambienti M365 con alta attivita, pianificare backup ogni 6-12 ore. Per ambienti meno attivi, giornaliero puo essere sufficiente.

2. **Storage**: i backup M365 possono essere voluminosi (email con allegati, OneDrive con file di grandi dimensioni). Pianificare lo storage tenendo conto della crescita e della retention richiesta. L'object storage cloud (S3, Azure Blob) con tier di archiviazione (Glacier, Cool/Archive) offre il miglior rapporto costo/capacita per la retention a lungo termine.

3. **Sicurezza**: i backup M365 contengono dati aziendali sensibili. Crittografare i backup at-rest e in-transit, limitare l'accesso al repository di backup, implementare l'immutabilita per proteggere da ransomware.

4. **Conformita**: verificare che la soluzione di backup supporti i requisiti regolamentari dell'organizzazione (GDPR, retention fiscale, eDiscovery). La capacita di esportare i dati in formati standard (PST, EML, file nativi) e fondamentale per rispondere a richieste legali.

5. **Test di restore**: come per qualsiasi backup, testare periodicamente il ripristino da backup M365. Verificare la capacita di ripristinare singoli elementi (email, file) e interi workload (casella di posta completa, sito SharePoint).

---

## Esercizi
1. **Lab — restore drill.** Mensile; restore VM random, valida.
2. **Stretch — DR drill multi-site.** Annuale full failover.

## Auto-valutazione
1. RTO vs RPO: differenza.
2. 3-2-1-1-0: cosa significa ogni numero?
3. Immutable backup: tecnologie?

## Glossario locale
| Termine | Definizione |
|---|---|
| **RTO** | Recovery Time Objective. |
| **RPO** | Recovery Point Objective. |
| **WORM** | Write-Once-Read-Many. |
| **Immutable backup** | Non modificabile dopo write. |
| **Restore drill** | Test ripristino schedulato. |
| **3-2-1-1-0** | Backup best practice rule. |
