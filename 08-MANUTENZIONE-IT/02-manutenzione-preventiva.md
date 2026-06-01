# Manutenzione Preventiva — Guida Completa

> **Modulo:** Operations IT · Fase 1 · Modulo 02
> **Prerequisiti:** Modulo 01.
> **Obiettivi:** programma manutenzione cyclical (daily/weekly/monthly/quarterly/yearly); checklist; documentazione esecuzione.
> **Tempo:** 60 min · lab 180 min · **Livello:** novice → competent · **Aggiornamento:** 2026-04-27

## Idee guida

1. **Manutenzione preventiva > reattiva, sempre.** Cost ratio 1:10 prevention vs reaction.
2. **Schedule documentato + auto-execution + audit log.** Verbale, no manuale.
3. **Checklist tangibili: "fatto/non fatto/skipped + perche".** Trail completo.
4. **Skip giustificato e accettabile, skip silente no.**

La manutenzione preventiva costituisce il pilastro fondamentale di qualsiasi strategia di gestione dell'infrastruttura IT. Un approccio sistematico e pianificato alla manutenzione riduce drasticamente i tempi di inattivita non pianificati, prolunga la vita utile dei componenti hardware e garantisce livelli di servizio costanti e affidabili. Questa guida fornisce procedure operative dettagliate, comandi specifici e checklist pronte all'uso per implementare un programma di manutenzione preventiva completo ed efficace.

---

## Indice

1. [Panoramica](#panoramica)
2. [Pianificazione Manutenzione](#pianificazione-manutenzione)
3. [Manutenzione Hardware Server](#manutenzione-hardware-server)
4. [Manutenzione Infrastruttura Rete](#manutenzione-infrastruttura-rete)
5. [Alimentazione e Ambiente](#alimentazione-e-ambiente)
6. [Manutenzione Virtualizzazione](#manutenzione-virtualizzazione)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

---

## Panoramica

### Manutenzione Preventiva vs Correttiva vs Predittiva

Le tre strategie di manutenzione non sono alternative ma complementari. Comprendere le differenze e scegliere la combinazione giusta per il proprio ambiente e fondamentale.

**Manutenzione Correttiva (Reattiva)**

Si interviene solo dopo il verificarsi di un guasto. Rappresenta l'approccio piu costoso e rischioso: i tempi di ripristino sono imprevedibili, i danni collaterali frequenti e l'impatto sul business potenzialmente devastante. Un disco che si guasta senza preavviso su un server senza RAID ridondante puo causare perdita di dati irreversibile. La manutenzione correttiva dovrebbe essere limitata ai soli eventi realmente imprevedibili, non rappresentare la strategia principale.

**Manutenzione Preventiva (Pianificata)**

Si eseguono interventi programmati a intervalli regolari, indipendentemente dallo stato apparente del componente. Si sostituiscono batterie UPS ogni 3-4 anni, si applicano patch mensilmente, si verificano i backup quotidianamente. Il costo e prevedibile e distribuito nel tempo. Secondo studi di settore, un programma di manutenzione preventiva ben implementato riduce i guasti non pianificati del 50-70% e abbassa i costi complessivi di manutenzione del 25-30%.

**Manutenzione Predittiva (Basata su Condizione)**

Si utilizzano dati di monitoraggio e analisi delle tendenze per prevedere i guasti prima che si verifichino. I dati SMART dei dischi, le temperature dei processori, i contatori di errori ECC della RAM, il numero di cicli di scrittura degli SSD: tutti questi indicatori permettono di intervenire nel momento ottimale, ne troppo presto (spreco) ne troppo tardi (guasto). La manutenzione predittiva richiede strumenti di monitoraggio avanzati e competenze nell'analisi dei dati, ma rappresenta l'evoluzione naturale della manutenzione preventiva.

### ROI della Manutenzione Preventiva

Il ritorno sull'investimento della manutenzione preventiva e ampiamente documentato e si manifesta su molteplici dimensioni:

- **Riduzione dei downtime**: il costo medio di un'ora di downtime per un'azienda media europea si aggira tra i 10.000 e i 50.000 euro, considerando perdita di produttivita, mancati ricavi e danno reputazionale. Ogni ora di downtime evitata ripaga mesi di manutenzione preventiva
- **Allungamento ciclo di vita hardware**: componenti mantenuti correttamente durano il 20-40% in piu rispetto a quelli trascurati. Un server ben gestito puo operare affidabilmente per 5-7 anni anziche 3-4
- **Riduzione interventi d'emergenza**: gli interventi fuori orario costano tipicamente 2-3 volte quelli pianificati, considerando straordinari del personale, tempi di risposta dei vendor e stress operativo
- **Conformita normativa**: molti framework normativi (ISO 27001, GDPR, SOC 2) richiedono evidenza documentata di procedure di manutenzione regolari
- **Prevedibilita dei costi**: un budget di manutenzione pianificato e molto piu facile da gestire e giustificare rispetto a spese impreviste per emergenze

### Principi di Pianificazione

La pianificazione efficace della manutenzione preventiva si basa su principi chiave:

1. **Schedulazione durante finestre di manutenzione**: gli interventi che comportano rischio di disservizio devono essere pianificati in orari di basso utilizzo, comunicati in anticipo e documentati
2. **Approccio basato sul rischio**: assegnare priorita alle attivita in base all'impatto potenziale di un guasto e alla probabilita che si verifichi
3. **Documentazione completa**: ogni intervento deve essere registrato con data, attivita svolta, risultato e firma dell'operatore
4. **Automazione dove possibile**: le attivita ripetitive come la verifica dei backup, il controllo dello spazio disco e il monitoraggio delle temperature devono essere automatizzate
5. **Revisione periodica**: il programma di manutenzione deve essere rivisto trimestralmente e adattato in base ai cambiamenti dell'infrastruttura

---

## Pianificazione Manutenzione

### Calendario Manutenzione Annuale

Un calendario di manutenzione annuale ben strutturato garantisce che nessuna attivita venga trascurata e permette di distribuire il carico di lavoro in modo equilibrato durante l'anno. La seguente organizzazione e basata sulla frequenza degli interventi.

#### Attivita Giornaliere (Lunedi-Venerdi, entro le 10:00)

Le attivita giornaliere richiedono circa 30-45 minuti e devono essere completate ogni mattina come prima attivita della giornata lavorativa:

- Verifica completamento backup notturni (controllare report automatici, verificare dimensione e integrita)
- Revisione dashboard di monitoraggio (Zabbix, Nagios, PRTG o equivalente)
- Triage degli alert generati nelle ultime 24 ore
- Revisione rapida dei log critici (eventi di sicurezza, errori applicativi, errori di sistema)
- Controllo spazio disco su server critici (soglia di attenzione: 80%, soglia critica: 90%)
- Verifica stato servizi critici (Active Directory, DNS, DHCP, posta elettronica)
- Controllo code di stampa e servizi di rete condivisi

#### Attivita Settimanali (tipicamente Lunedi mattina, 1-2 ore)

- Revisione patch disponibili per Windows (WSUS) e Linux (apt/yum/dnf)
- Analisi bollettini di sicurezza pubblicati nell'ultima settimana (CERT, CVE)
- Verifica replica Active Directory tra domain controller (`repadmin /replsummary`)
- Controllo scadenza certificati SSL/TLS (soglia: 30 giorni)
- Revisione account di servizio e utenti privilegiati
- Verifica funzionamento job schedulati (task Windows, cron Linux)
- Analisi trend utilizzo risorse (CPU, RAM, disco, rete) dell'ultima settimana
- Backup configurazione switch, router e firewall

#### Attivita Mensili (prima settimana del mese, 4-8 ore)

- Ciclo completo di patching: test in ambiente di staging, approvazione, deployment in produzione
- Pulizia WSUS (rimozione aggiornamenti obsoleti, `Invoke-WsusServerCleanup`)
- Pulizia repository apt/yum (rimozione kernel vecchi, pacchetti orfani)
- Confronto baseline prestazionali: comparare metriche del mese corrente con quelle storiche
- Revisione capacita: analisi trend di crescita spazio disco, utilizzo CPU e RAM
- Audit regole firewall: identificare regole inutilizzate, temporanee scadute, shadow rules
- Test di restore da backup: ripristinare almeno un sistema o dataset diverso ogni mese
- Aggiornamento firmware access point wireless (se disponibile)
- Verifica integrita database di monitoraggio e pulizia dati storici obsoleti
- Revisione e rotazione log applicativi

#### Attivita Trimestrali (Q1: Gennaio, Q2: Aprile, Q3: Luglio, Q4: Ottobre)

- Test Disaster Recovery parziale: ripristino di un sistema critico in ambiente isolato
- Test batterie UPS sotto carico controllato
- Diagnostica hardware completa su server (memtest, diagnostica vendor)
- Revisione accessi: verifica permessi utente, rimozione account inattivi, revisione gruppi AD
- Aggiornamento documentazione: schemi di rete, inventario asset, procedure operative
- Pulizia fisica server room: pulizia polvere, verifica cablaggio, controllo etichette
- Test failover cluster (se presente): migrazione controllata di servizi tra nodi
- Verifica licenze software: controllo scadenze e conformita

#### Attivita Semestrali (Giugno e Dicembre)

- Assessment di sicurezza completo: vulnerability scan interno ed esterno
- Revisione contratti vendor: SLA, tempi di risposta, copertura garanzie hardware
- Pulizia storage approfondita: identificazione dati orfani, deduplicazione, archiviazione
- Aggiornamento diagrammi di rete completi (fisici e logici)
- Revisione policy di backup: adeguatezza RPO/RTO, verifica copertura completa
- Revisione policy di sicurezza: password policy, MFA, policy di accesso remoto
- Pianificazione budget semestrale per manutenzione e aggiornamenti

#### Attivita Annuali (tipicamente Novembre-Dicembre)

- Simulazione Disaster Recovery completa: ripristino dell'intero ambiente in sito alternativo
- Pianificazione refresh hardware: identificazione server e apparati da sostituire nei prossimi 12 mesi
- Audit licenze completo: inventario software, conformita, ottimizzazione costi
- Capacity planning annuale: proiezione crescita, identificazione colli di bottiglia futuri
- Penetration test di sicurezza (interno ed esterno, condotto da terze parti)
- Revisione architettura: valutazione nuove tecnologie, piano di modernizzazione
- Redazione piano di manutenzione per l'anno successivo

### Finestre di Manutenzione — Best Practices

Le finestre di manutenzione (maintenance window) sono periodi concordati durante i quali e consentito eseguire interventi che possono causare disservizi. Gestirle correttamente e fondamentale:

- **Schedulazione regolare**: definire finestre ricorrenti (es. ogni primo sabato del mese dalle 06:00 alle 12:00) per creare aspettative prevedibili
- **Comunicazione anticipata**: notificare tutti gli stakeholder almeno 48 ore prima, specificando sistemi coinvolti, durata prevista e impatto atteso
- **Piano di rollback**: ogni intervento deve avere un piano di rollback documentato e testato, con criteri chiari per decidere quando attivarlo
- **Personale adeguato**: garantire la presenza di almeno due operatori per interventi critici
- **Conferma post-intervento**: verificare il corretto funzionamento di tutti i servizi prima di dichiarare conclusa la finestra di manutenzione
- **Documentazione post-intervento**: registrare tutte le attivita svolte, eventuali problemi incontrati e azioni correttive

---

### Checklist per Frequenza

Di seguito le checklist operative dettagliate, organizzate per frequenza. Ogni elemento include la procedura specifica e i comandi da eseguire.

#### Checklist Giornaliera

```
[ ] Verifica backup notturni
    - Controllare report email/dashboard dal software di backup
    - Verificare: stato completamento, dimensione coerente, eventuali warning
    - Se fallito: identificare causa, avviare backup manuale, aprire ticket

[ ] Revisione dashboard monitoraggio
    - Accedere a Zabbix/Nagios/PRTG
    - Verificare: nessun host in stato DOWN/UNREACHABLE
    - Verificare: nessun servizio in stato CRITICAL
    - Documentare eventuali anomalie nel registro giornaliero

[ ] Triage alert ultime 24 ore
    - Classificare: critico/importante/informativo
    - Critici: azione immediata
    - Importanti: pianificare intervento entro 24-48 ore
    - Informativi: archiviare, analizzare trend settimanale

[ ] Revisione log critici
    - Windows: Event Viewer > System e Security (errori e warning)
    - Linux: journalctl --since yesterday --priority=err
    - Applicativi: log specifici delle applicazioni critiche

[ ] Controllo spazio disco
    - Windows: Get-WmiObject Win32_LogicalDisk | Select DeviceID,
      @{N='Free(GB)';E={[math]::Round($_.FreeSpace/1GB,2)}},
      @{N='%Free';E={[math]::Round($_.FreeSpace/$_.Size*100,1)}}
    - Linux: df -h | awk '$5+0 > 80 {print}'
    - Soglia attenzione: >80% utilizzato
    - Soglia critica: >90% utilizzato
```

#### Checklist Settimanale

```
[ ] Revisione patch disponibili
    - Windows: WSUS Console > Updates > Unapproved
    - Linux (Debian/Ubuntu): apt list --upgradable
    - Linux (RHEL/CentOS): dnf check-update
    - Classificare per criticita: Security Critical, Security Important, Other

[ ] Bollettini sicurezza
    - Consultare: CERT-AGID, Microsoft MSRC, CVE database
    - Valutare impatto su sistemi in produzione
    - Documentare azioni richieste

[ ] Verifica replica Active Directory
    - repadmin /replsummary
    - repadmin /showrepl
    - dcdiag /v
    - Verificare: nessun errore di replica, delta temporale < 15 minuti

[ ] Scadenza certificati
    - Controllare certificati SSL/TLS su web server e servizi esposti
    - Linux: echo | openssl s_client -connect host:443 2>/dev/null |
      openssl x509 -noout -dates
    - Rinnovare certificati con scadenza < 30 giorni

[ ] Verifica job schedulati
    - Windows: Get-ScheduledTask | Where State -eq 'Ready' |
      Select TaskName, LastRunTime, LastTaskResult
    - Linux: verificare output cron in /var/log/syslog o journalctl -u cron
    - Investigare job falliti (LastTaskResult != 0 o exit code != 0)
```

#### Checklist Mensile

```
[ ] Ciclo completo patching
    - Fase 1: download e test in ambiente staging (giorno 1-3)
    - Fase 2: approvazione change e comunicazione (giorno 4-5)
    - Fase 3: deployment in produzione durante maintenance window
    - Fase 4: verifica post-patching (giorno successivo)
    - Documentare tutto nel sistema di change management

[ ] Pulizia WSUS
    - PowerShell: Invoke-WsusServerCleanup -CleanupObsoleteUpdates
      -CleanupUnneededContentFiles -CompressUpdates
      -DeclineExpiredUpdates -DeclineSupersededUpdates
    - Verificare spazio disco recuperato

[ ] Pulizia repository Linux
    - Debian/Ubuntu: apt autoremove && apt clean
    - RHEL/CentOS: dnf autoremove && dnf clean all
    - Rimuovere kernel obsoleti mantenendo almeno gli ultimi 2

[ ] Confronto baseline prestazionali
    - Comparare metriche correnti con mese precedente e stesso mese anno precedente
    - Attenzione a: crescita utilizzo CPU >10%, crescita RAM >15%, crescita disco >20%
    - Documentare anomalie e pianificare azioni correttive

[ ] Test restore backup
    - Selezionare un sistema diverso ogni mese (rotazione annuale)
    - Eseguire restore completo in ambiente isolato
    - Verificare integrita dati, funzionamento applicazioni, coerenza database
    - Documentare: tempo di restore, eventuali problemi, esito finale
    - CRITICO: un backup non testato non e un backup affidabile

[ ] Audit regole firewall
    - Identificare regole con hit count = 0 (potenzialmente inutilizzate)
    - Verificare regole temporanee: data scadenza, ancora necessarie?
    - Controllare regole troppo permissive (any/any)
    - Verificare ordine regole (shadow rules)
    - Documentare tutte le modifiche effettuate
```

#### Checklist Trimestrale

```
[ ] Test Disaster Recovery parziale
    - Selezionare un sistema critico diverso ogni trimestre
    - Eseguire ripristino completo da backup in ambiente isolato
    - Misurare RTO effettivo vs RTO dichiarato
    - Verificare RPO: controllare la data dell'ultimo backup disponibile
    - Documentare: esito, tempi, problemi riscontrati, azioni correttive

[ ] Test batterie UPS
    - Eseguire test sotto carico (vedi sezione dedicata UPS)
    - Misurare runtime effettivo vs dichiarato
    - Pianificare sostituzione se runtime < 80% del nominale

[ ] Diagnostica hardware completa
    - Server Dell: iDRAC > Diagnostics > Extended Test
    - Server HP: iLO > Diagnostics > All Tests
    - Linux generico: memtest86+ (richiede riavvio), smartctl per dischi
    - Documentare risultati e pianificare sostituzioni preventive

[ ] Revisione accessi
    - Active Directory: identificare account inattivi (>90 giorni senza login)
      Search-ADAccount -AccountInactive -TimeSpan 90 -UsersOnly
    - Verificare gruppi privilegiati (Domain Admins, Enterprise Admins)
    - Rimuovere accessi non piu necessari (principio del minimo privilegio)
    - Verificare account di servizio: password rotation, permessi minimi
```

---

## Manutenzione Hardware Server

### Ispezione Fisica

L'ispezione fisica regolare dei server e un'attivita spesso sottovalutata ma fondamentale per prevenire guasti causati da condizioni ambientali inadeguate.

#### Monitoraggio Temperature

Il monitoraggio delle temperature deve essere continuo e automatizzato, con soglie di allarme configurate nel sistema di monitoraggio centralizzato.

**Comandi IPMI (standard, funzionano su molti server):**

```bash
# Lettura sensori temperatura via IPMI
ipmitool sensor list | grep -i temp
ipmitool sdr type Temperature

# Lettura remota (specificare IP BMC, utente e password)
ipmitool -I lanplus -H 192.168.1.100 -U admin -P password sensor list | grep -i temp

# Soglie configurate sul BMC
ipmitool sensor get "CPU1 Temp"
```

**Dell iDRAC (interfaccia web e racadm):**

```bash
# Stato termico via racadm
racadm getconfig -g cfgServerInfo -o cfgServerThermalStatus

# Sensori temperatura
racadm getsensorinfo

# Via SSH a iDRAC
ssh root@idrac-ip "racadm getsensorinfo"
```

**HP iLO (interfaccia web e ilorest):**

```bash
# Utilizzando iLOrest tool
ilorest login <ilo-ip> -u admin -p password
ilorest get Temperatures --select Thermal.
ilorest logout

# Via curl REST API
curl -k -u admin:password \
  https://ilo-ip/redfish/v1/Chassis/1/Thermal/
```

**Soglie di riferimento raccomandate:**

| Componente | Normale | Attenzione | Critico |
|-----------|---------|------------|---------|
| CPU | < 70 C | 70-85 C | > 85 C |
| Ambiente rack | < 27 C | 27-35 C | > 35 C |
| Disco HDD | < 40 C | 40-50 C | > 50 C |
| Disco SSD | < 45 C | 45-55 C | > 55 C |
| Inlet Air | < 30 C | 30-35 C | > 35 C |

#### Checklist Ispezione Visiva

Eseguire durante ogni accesso alla sala server (almeno trimestralmente come attivita dedicata):

```
[ ] LED di stato su tutti i server (verde = OK, ambra = warning, rosso = errore)
[ ] LED dischi: nessun disco con LED ambra/rosso
[ ] Ventole: nessun rumore anomalo, tutte in rotazione
[ ] Cavi di alimentazione: connessioni salde, nessun cavo piegato o danneggiato
[ ] Cavi di rete: tutti collegati, nessun cavo allentato, etichette leggibili
[ ] Display frontale server (se presente): nessun messaggio di errore
[ ] Livello polvere visibile: se eccessivo, pianificare pulizia
[ ] Temperatura percepita nella sala: coerente con quanto indicato dai sensori
[ ] Pavimento sopraelevato (se presente): nessuna piastrella fuori posto
```

#### Procedure Pulizia Polvere

La polvere e il nemico silenzioso dell'hardware. Riduce l'efficienza del raffreddamento, accelera l'usura dei componenti e puo causare cortocircuiti. La pulizia deve essere eseguita almeno semestralmente, trimestralmente in ambienti polverosi.

**Procedura operativa:**

1. Pianificare l'intervento durante la finestra di manutenzione
2. Spegnere il server in modo ordinato e scollegare l'alimentazione
3. Utilizzare aria compressa a bassa pressione (max 3 bar) o aspiratore ESD-safe
4. Procedere dall'alto verso il basso, dall'interno verso l'esterno
5. Prestare particolare attenzione a: dissipatori CPU, ventole, griglie di aspirazione e espulsione, alimentatori
6. Non utilizzare MAI aspirapolvere domestici (rischio scariche elettrostatiche)
7. Indossare sempre braccialetto antistatico quando si toccano componenti interni
8. Documentare l'intervento con foto prima/dopo se opportuno
9. Ricollegare, riavviare e verificare il corretto funzionamento

#### Gestione Cablaggio

Un cablaggio ordinato facilita la manutenzione, riduce gli errori e migliora il flusso d'aria all'interno dei rack:

- Ogni cavo deve avere un'etichetta a entrambe le estremita (identificativo porta, server/switch, funzione)
- Utilizzare cavi della lunghezza appropriata: cavi troppo lunghi creano disordine, troppo corti creano tensione
- Separare fisicamente cavi di alimentazione e cavi dati
- Utilizzare velcro (non fascette di plastica) per fissare i cavi: facilita modifiche future
- Documentare ogni cavo in una matrice di cablaggio (spreadsheet o CMDB)
- Verificare trimestralmente che la documentazione corrisponda alla realta fisica

### Controllo Dischi e RAID

I dischi sono tra i componenti piu soggetti a guasto. Un monitoraggio proattivo permette di identificare dischi in fase di degrado e sostituirli prima del guasto completo.

#### Monitoraggio SMART

**Linux (smartmontools):**

```bash
# Installazione
apt install smartmontools    # Debian/Ubuntu
dnf install smartmontools    # RHEL/CentOS

# Stato salute rapido
smartctl -H /dev/sda

# Report completo attributi SMART
smartctl -A /dev/sda

# Attributi critici da monitorare:
# - Reallocated_Sector_Ct (ID 5): settori riallocati, >0 indica degrado
# - Current_Pending_Sector (ID 197): settori in attesa di riallocazione
# - Offline_Uncorrectable (ID 198): settori non correggibili
# - UDMA_CRC_Error_Count (ID 199): errori di trasferimento (possibile problema cavo)

# Avviare test esteso (dura alcune ore, non impatta le operazioni)
smartctl -t long /dev/sda

# Verificare risultato test
smartctl -l selftest /dev/sda

# Monitoraggio continuo (abilitare il daemon)
systemctl enable --now smartd
# Configurare /etc/smartd.conf per alert email
```

**Windows (PowerShell):**

```powershell
# Stato disco fisico
Get-PhysicalDisk | Select FriendlyName, MediaType, HealthStatus,
  OperationalStatus, Size

# Dettagli affidabilita
Get-PhysicalDisk | Get-StorageReliabilityCounter |
  Select DeviceId, ReadErrorsTotal, WriteErrorsTotal, Temperature,
  Wear, PowerOnHours

# Contatore errori disco
Get-WinEvent -LogName System -FilterXPath "*[System[EventID=7 or EventID=11 or EventID=15 or EventID=51 or EventID=52]]" -MaxEvents 20

# Per server con Storage Spaces Direct
Get-VirtualDisk | Select FriendlyName, HealthStatus, OperationalStatus
Get-StoragePool | Select FriendlyName, HealthStatus, IsPrimordial
```

#### Controllo Salute RAID

**MegaRAID (controller LSI/Broadcom, comuni su Dell e Lenovo):**

```bash
# Stato generale controller
storcli /c0 show

# Stato tutti i virtual drive (array RAID)
storcli /c0 /vall show

# Stato tutti i physical drive
storcli /c0 /eall /sall show

# Dettaglio errori su disco specifico (enclosure 252, slot 0)
storcli /c0 /e252 /s0 show all | grep -i -E "error|fail|smart"

# Verifica hot spare
storcli /c0 /eall /sall show | grep -i "hotspare"

# Stato ricostruzione RAID (se in corso)
storcli /c0 /vall show rebuild

# Con il vecchio tool MegaCli (legacy)
MegaCli64 -LDInfo -Lall -aALL
MegaCli64 -PDList -aALL | grep -E "Firmware|Slot|Error|Other|Predictive"
```

**HP Smart Array (controller HPE):**

```bash
# Utilizzando ssacli (Smart Storage Administrator CLI)
ssacli ctrl all show status
ssacli ctrl slot=0 show config
ssacli ctrl slot=0 pd all show status
ssacli ctrl slot=0 ld all show status

# Dettaglio errori
ssacli ctrl slot=0 pd all show detail | grep -E "Status|Error|Temperature|SSD"

# Verifica cache e batteria
ssacli ctrl slot=0 show status | grep -i -E "cache|battery|capacitor"
```

#### Monitoraggio Usura SSD

Gli SSD hanno un numero finito di cicli di scrittura. Monitorare il livello di usura e fondamentale per pianificare la sostituzione preventiva.

```bash
# Linux: livello usura SSD (smartctl)
smartctl -A /dev/sda | grep -i -E "wear|life|endurance"

# Attributi tipici SSD:
# - Wear_Leveling_Count (Samsung): 100 = nuovo, 0 = fine vita
# - Media_Wearout_Indicator (Intel): 100 = nuovo, 1 = fine vita
# - Percentage_Used (NVMe): 0% = nuovo, 100% = vita nominale raggiunta

# Per SSD NVMe
smartctl -a /dev/nvme0 | grep -E "Percentage Used|Data Units Written|Available Spare"
nvme smart-log /dev/nvme0

# Soglie raccomandate per sostituzione preventiva:
# - Usura > 80% della vita nominale
# - Available Spare < 20%
# - Media Errors > 0 (investigare immediatamente)
```

#### Procedura Sostituzione Disco

1. Identificare il disco guasto tramite LED fisico e comandi software
2. Verificare disponibilita disco sostitutivo compatibile (stesso tipo, stessa capacita o superiore)
3. Verificare che il RAID sia in stato OPTIMAL (non sostituire se gia in degrado con un altro disco)
4. Rimuovere fisicamente il disco guasto (hot-swap se supportato, altrimenti pianificare fermo)
5. Inserire il nuovo disco nello slot
6. Verificare che la ricostruzione RAID si avvii automaticamente
7. Monitorare il progresso della ricostruzione fino al completamento
8. Verificare lo stato finale: tutti i dischi ONLINE, array in stato OPTIMAL
9. Documentare: data sostituzione, serial number vecchio e nuovo disco, tempo ricostruzione

### Memoria RAM

#### Verifica Errori

La memoria RAM e un componente critico la cui affidabilita e spesso data per scontata. Gli errori di memoria possono causare crash di sistema, corruzione dati e comportamenti imprevedibili.

**Test approfondito con memtest86+:**

```bash
# Installazione
apt install memtest86+    # Debian/Ubuntu

# memtest86+ si avvia dal boot loader (GRUB)
# Selezionare "Memory test" dal menu di avvio
# Lasciare eseguire almeno 2 passaggi completi (diverse ore)
# RICHIEDE riavvio del server e tempo di inattivita
```

**Windows Memory Diagnostic:**

```powershell
# Avviare diagnostica memoria (richiede riavvio)
mdsched.exe

# Selezionare "Riavvia ora e individua problemi"
# Al riavvio, selezionare test esteso (F1 > Extended)
# Risultati visibili dopo il riavvio successivo in Event Viewer:
Get-WinEvent -LogName System | Where-Object {
  $_.ProviderName -eq "Microsoft-Windows-MemoryDiagnostics-Results"
}
```

#### Monitoraggio Errori ECC

I server enterprise utilizzano memoria ECC (Error Correcting Code) che corregge automaticamente errori singoli e rileva errori doppi. Il monitoraggio dei contatori ECC e fondamentale.

```bash
# Linux: modulo edac (Error Detection and Correction)
# Verificare caricamento modulo
lsmod | grep edac

# Contatori errori ECC
edac-util -s          # stato generale
edac-util -r          # report dettagliato

# Alternativa via sysfs
cat /sys/devices/system/edac/mc/mc0/ce_count    # errori corretti
cat /sys/devices/system/edac/mc/mc0/ue_count    # errori non corretti

# Via IPMI
ipmitool sel list | grep -i memory

# Interpretazione:
# ce_count (Correctable Errors): pochi sono normali, trend crescente indica degrado
# ue_count (Uncorrectable Errors): QUALSIASI valore > 0 richiede sostituzione DIMM
```

#### Capacity Planning RAM

```bash
# Linux: analisi utilizzo memoria
free -h
vmstat 1 5
sar -r 1 5

# Pagine di swap utilizzate (se > 0 su un server, potrebbe servire piu RAM)
swapon --show
vmstat | awk 'NR==3 {print "Swap In:", $7, "Swap Out:", $8}'
```

```powershell
# Windows: analisi utilizzo memoria
Get-Process | Sort WorkingSet64 -Descending | Select -First 20 Name,
  @{N='RAM(MB)';E={[math]::Round($_.WorkingSet64/1MB,2)}}
Get-Counter '\Memory\Available MBytes'
Get-Counter '\Memory\Pages/sec'
Get-Counter '\Paging File(*)\% Usage'
```

### Firmware e BIOS

Gli aggiornamenti firmware risolvono bug, migliorano prestazioni, chiudono vulnerabilita di sicurezza e aggiungono funzionalita. Devono essere gestiti con cautela poiche un aggiornamento fallito puo rendere inutilizzabile il componente.

#### Aggiornamento Server Dell (iDRAC / Dell System Update)

```bash
# Dell System Update (DSU) su Linux
# Installazione repository Dell
wget -q -O - https://linux.dell.com/repo/hardware/dsu/bootstrap.cgi | bash

# Verifica aggiornamenti disponibili
dsu --preview

# Applicare aggiornamenti (richiede riavvio)
dsu --apply-upgrades

# Aggiornamento iDRAC via racadm
racadm update -f firmimg.d9 -l /path/to/firmware

# Via interfaccia web iDRAC:
# Maintenance > System Update > Upload firmware file > Install
```

#### Aggiornamento Server HP (iLO / Smart Update Manager)

```bash
# HP Smart Update Manager (SUM) - interfaccia grafica o CLI
# Scaricare SPP (Service Pack for ProLiant) dal portale HPE

# CLI mode
hpsum /s /use_latest /allow_update_to_bundle

# Aggiornamento iLO via ilorest
ilorest login <ilo-ip> -u admin -p password
ilorest flashfirmware ilo5_xxx.bin
ilorest logout

# Via interfaccia web iLO:
# Administration > Firmware > Upload firmware file
```

#### Aggiornamento Server Lenovo (XCC / OneCLI)

```bash
# Lenovo OneCLI
onecli update flash --bmc <xcc-ip> --user admin --password password
onecli update scan --bmc <xcc-ip> --user admin --password password

# Via interfaccia web XCC:
# BMC Configuration > Firmware Update > Upload and activate
```

#### Checklist Pre-Aggiornamento Firmware

```
[ ] Verificare compatibilita firmware con hardware e sistema operativo installati
[ ] Leggere completamente le release notes (attenzione a known issues)
[ ] Verificare prerequisiti (versioni firmware minime necessarie)
[ ] Eseguire backup completo del sistema
[ ] Eseguire backup configurazione BMC (iDRAC/iLO/XCC)
[ ] Verificare che il server non sia sotto carico critico
[ ] Pianificare l'intervento durante finestra di manutenzione
[ ] Avere a disposizione un piano di rollback (firmware precedente)
[ ] Testare prima su un server non critico (se possibile)
[ ] Documentare versioni correnti prima dell'aggiornamento
```

### Alimentazione

#### Test Ridondanza PSU

La maggior parte dei server enterprise dispone di alimentatori ridondanti. Verificare periodicamente che la ridondanza funzioni realmente.

```
Procedura test ridondanza PSU (trimestrale):
1. Verificare che il server abbia almeno 2 PSU installate e funzionanti
2. Verificare che le PSU siano collegate a circuiti elettrici indipendenti
3. Durante finestra di manutenzione, scollegare UNA PSU
4. Verificare che il server continui a funzionare normalmente
5. Verificare che venga generato un alert (LED, trap SNMP, evento)
6. Ricollegare la PSU scollegata
7. Verificare che il sistema torni in stato di ridondanza completa
8. Ripetere il test scollegando l'ALTRA PSU
9. Documentare esito del test
```

```bash
# Monitoraggio consumo energetico via IPMI
ipmitool dcmi power reading

# Dell iDRAC
racadm getconfig -g cfgServerPower

# HP iLO (via REST API)
curl -k -u admin:password \
  https://ilo-ip/redfish/v1/Chassis/1/Power/
```

---

## Manutenzione Infrastruttura Rete

### Switch

Gli switch sono il cuore della rete locale. Un guasto switch puo isolare interi segmenti di rete, rendendo inaccessibili server, stampanti e servizi critici.

#### Audit Stato Porte

```
# Cisco IOS
show interfaces status
show interfaces counters errors
show interfaces | include line protocol|input errors|output errors

# HP/Aruba ProCurve/ArubaOS-Switch
show interfaces brief
show interfaces status
show interfaces all | include errors

# Identificare porte con errori crescenti (possibile cavo difettoso)
# Identificare porte attive non documentate (possibile connessione non autorizzata)
# Identificare porte in stato err-disabled (riattivare dopo aver risolto la causa)
```

#### Controllo Contatori Errori

```
# Cisco IOS - contatori errori dettagliati
show interfaces GigabitEthernet0/1 counters errors

# Tipi di errore da monitorare:
# - CRC errors: errori di integrita frame (cavo difettoso o interferenze)
# - Input errors: pacchetti ricevuti con errori
# - Output errors: pacchetti non trasmessi (congestione o errori)
# - Collisions: normali su half-duplex, anomali su full-duplex
# - Giants/Runts: frame di dimensione anomala (possibile problema NIC)

# Reset contatori (dopo aver documentato i valori)
clear counters GigabitEthernet0/1
```

#### Aggiornamento Firmware Switch

```
# Cisco IOS - procedura aggiornamento
# 1. Backup configurazione corrente
copy running-config startup-config
copy startup-config tftp://192.168.1.10/switch-backup.cfg

# 2. Verificare spazio flash disponibile
dir flash:

# 3. Copiare nuovo firmware
copy tftp://192.168.1.10/new-firmware.bin flash:

# 4. Verificare hash MD5
verify /md5 flash:new-firmware.bin

# 5. Configurare boot dal nuovo firmware
boot system flash:new-firmware.bin

# 6. Riavviare durante finestra di manutenzione
reload

# HP/Aruba - procedura aggiornamento
copy tftp flash 192.168.1.10 new-firmware.swi primary
boot system flash primary
reload
```

#### Backup Configurazione

Il backup regolare delle configurazioni degli apparati di rete e fondamentale. Una configurazione persa o corrotta puo richiedere ore di ricostruzione.

```
# Cisco IOS
copy running-config tftp://192.168.1.10/switches/switch01-20260326.cfg

# HP/Aruba
copy running-config tftp 192.168.1.10 switches/aruba01-20260326.cfg

# Automazione con script (esempio con Expect o Ansible)
# Pianificare backup settimanale via cron/task scheduler
# Mantenere almeno le ultime 4 versioni di configurazione
# Confrontare periodicamente configurazione corrente con ultimo backup
```

#### Verifica Spanning Tree Protocol (STP)

STP previene i loop di rete ma una configurazione errata puo causare problemi di connettivita o convergenza lenta.

```
# Cisco IOS
show spanning-tree summary
show spanning-tree root
show spanning-tree interface GigabitEthernet0/1 detail

# Verifiche chiave:
# - Root bridge: e lo switch previsto? (deve essere il core switch)
# - Porte in stato Blocking: sono quelle previste?
# - Nessuna porta in stato "Listening" o "Learning" prolungato
# - Topology changes recenti: un numero elevato indica instabilita
show spanning-tree detail | include changes
```

### Router

#### Verifica Tabella di Routing

```
# Cisco IOS
show ip route summary
show ip route

# Verifiche chiave:
# - Tutte le rotte previste sono presenti?
# - Nessuna rotta con next-hop irraggiungibile?
# - Rotte statiche: sono tutte ancora necessarie e corrette?
# - Rotte dinamiche (OSPF/BGP): convergenza completa?
```

#### Audit ACL (Access Control List)

```
# Cisco IOS
show access-lists
show ip access-lists

# Per ogni ACL:
# - Hit count: regole con 0 hit sono probabilmente obsolete
# - Ordine: le regole piu specifiche devono precedere quelle generiche
# - Regole deny esplicite: sono tutte documentate e giustificate?
# - Implicit deny finale: e il comportamento desiderato?

# Verificare quali ACL sono applicate alle interfacce
show ip interface | include line protocol|access list
```

#### Monitoraggio Prestazioni

```
# Cisco IOS
show processes cpu history
show memory statistics
show interfaces summary

# Soglie di attenzione:
# - CPU > 60% media su 5 minuti: investigare
# - Memoria libera < 20%: investigare
# - Interfacce con errori crescenti: verificare cavo/porta
# - Input/Output queue drops: possibile congestione
```

#### Salute Protocolli di Routing

```
# OSPF
show ip ospf neighbor
show ip ospf interface brief
# Verificare: tutti i neighbor in stato FULL, nessun flapping

# BGP (se utilizzato)
show ip bgp summary
show ip bgp neighbors | include state|Prefixes
# Verificare: sessioni in stato Established, numero prefissi stabile
```

### Access Point

#### Test Copertura

Eseguire almeno semestralmente un test di copertura wireless per verificare che tutti gli ambienti siano adeguatamente coperti e che non ci siano zone morte create da modifiche strutturali o nuove fonti di interferenza.

- Utilizzare strumenti di survey come Ekahau, NetSpot o WiFi Analyzer
- Documentare livelli di segnale per area (obiettivo: minimo -67 dBm per applicazioni voce, -70 dBm per dati)
- Identificare zone di interferenza co-canale (access point adiacenti sullo stesso canale)
- Verificare la corretta copertura delle aree recentemente modificate

#### Ottimizzazione Canali

```
# Verificare canali correnti e interferenze
# La maggior parte dei controller wireless moderni ha funzionalita di auto-channel

# Best practices canali 2.4 GHz: utilizzare solo canali 1, 6, 11 (non sovrapposti)
# Best practices canali 5 GHz: utilizzare canali DFS se consentito, per massimizzare
# la capacita disponibile

# Monitorare densita client per access point (soglia attenzione: >25 client per AP)
```

### Firewall

#### Audit e Pulizia Regole

L'accumulo di regole firewall obsolete e uno dei problemi piu comuni e pericolosi. Regole dimenticate creano superficie di attacco non necessaria e complicano il troubleshooting.

```
Procedura audit regole firewall (mensile):

1. Esportare l'intero ruleset in formato leggibile
2. Per ogni regola verificare:
   - Esiste un ticket/change request associato?
   - Il proprietario della regola e ancora in azienda?
   - Il servizio protetto dalla regola e ancora attivo?
   - La regola e troppo permissiva? (source/destination/port "any")
   - Ci sono regole duplicate o in conflitto?
3. Contrassegnare le regole da rimuovere
4. Pianificare la rimozione durante finestra di manutenzione
5. Disabilitare prima di rimuovere (attendere 30 giorni)
6. Se nessun impatto dopo 30 giorni, rimuovere definitivamente
7. Documentare tutte le modifiche nel change log
```

#### Rinnovo Certificati

```
Checklist certificati firewall:
[ ] Certificato SSL per management interface
[ ] Certificati per VPN SSL/IPsec
[ ] Certificati per SSL inspection/decryption
[ ] Certificati CA intermedie e root (trust chain)
[ ] CRL (Certificate Revocation List) aggiornate

# Monitorare scadenze con almeno 60 giorni di anticipo per i firewall
# (il rinnovo richiede piu tempo e pianificazione rispetto a un web server)
```

#### Aggiornamento Firme IPS

```
# I sistemi IPS/IDS richiedono aggiornamenti frequenti delle firme
# per riconoscere le minacce piu recenti

# Verificare:
# - Data ultimo aggiornamento firme (deve essere < 7 giorni)
# - Versione engine IPS
# - Policy attive e loro modalita (detect vs prevent)
# - Falsi positivi recenti da gestire (tuning regole)
```

### Cablaggio

#### Test e Etichettatura Cavi

```
Procedura test cablaggio (annuale o dopo modifiche):

1. Utilizzare un cable tester certificato (non solo continuita ma anche prestazioni)
2. Per cavi Cat 6/6a: verificare conformita ai parametri di certificazione
   - Lunghezza massima: 90 metri (patch cord escluse)
   - Attenuazione entro specifiche
   - NEXT (Near End Crosstalk) entro specifiche
   - Return Loss entro specifiche
3. Per fibra ottica:
   - Misurare attenuazione con OTDR o power meter
   - Verificare pulizia connettori con microscopio per fibre
   - Documentare misurazioni per ogni tratta
4. Sostituire cavi difettosi
5. Aggiornare documentazione con risultati test
6. Etichettare ENTRAMBE le estremita di ogni cavo con:
   - Identificativo univoco del cavo
   - Punto di partenza e destinazione
   - Data di installazione
```

#### Documentazione Patch Panel

Mantenere una matrice aggiornata che associa ogni porta del patch panel alla presa a muro corrispondente e alla porta dello switch. Questa documentazione e fondamentale durante il troubleshooting e diventa critica durante emergenze notturne quando la concentrazione e ridotta.

---

## Alimentazione e Ambiente

### UPS (Uninterruptible Power Supply)

L'UPS e l'ultima linea di difesa contro le interruzioni di alimentazione elettrica. Un UPS con batterie degradate e un falso senso di sicurezza.

#### Procedure Test Batteria

**APC (Smart-UPS) via apctest:**

```bash
# Installazione
apt install apcupsd    # Debian/Ubuntu

# Configurare /etc/apcupsd/apcupsd.conf
# UPSCABLE usb
# UPSTYPE usb
# DEVICE (lasciare vuoto per auto-detect USB)

# Avviare il servizio
systemctl start apcupsd

# Stato UPS
apcaccess status

# Test batteria (ATTENZIONE: il carico funzionera a batteria durante il test)
apctest
# Selezionare opzione 6: "Test battery runtime"

# Parametri da verificare:
# - BATTV (tensione batteria): confrontare con nominale
# - TIMELEFT (autonomia residua): deve essere >= RTO pianificato
# - BCHARGE (% carica): deve essere 100% in condizioni normali
# - LASTXFER (motivo ultimo trasferimento su batteria)
# - NUMXFERS (numero trasferimenti su batteria): trend crescente
#   indica problemi di alimentazione elettrica
```

**Network-based UPS management (SNMP):**

```bash
# Interrogazione SNMP per UPS con scheda di rete
# OID comuni per UPS APC
snmpwalk -v2c -c public ups-ip .1.3.6.1.4.1.318.1.1.1.2    # Battery group
snmpget -v2c -c public ups-ip .1.3.6.1.4.1.318.1.1.1.2.2.0  # Remaining runtime
snmpget -v2c -c public ups-ip .1.3.6.1.4.1.318.1.1.1.2.1.0  # Battery status
snmpget -v2c -c public ups-ip .1.3.6.1.4.1.318.1.1.1.2.3.0  # Battery charge %

# Integrare con Zabbix/Nagios per monitoraggio continuo
# Configurare alert per:
# - Battery status != normal
# - Charge < 80%
# - Runtime < minuti_necessari_per_shutdown_ordinato
# - Trasferimento su batteria (evento immediato)
```

#### Calcolo Runtime

```
Formula: Runtime (minuti) = (Capacita_batteria_Wh * Efficienza) / Carico_W

Esempio pratico:
- UPS APC Smart-UPS 3000VA / 2700W
- Batteria: 816 Wh (nominale da nuovo)
- Efficienza: 0.90 (90%)
- Carico attuale: 1200W (misurato)
- Runtime = (816 * 0.90) / 1200 = 0.612 ore = 36.7 minuti

Regola pratica: pianificare il runtime necessario per:
1. Ricevere l'alert di mancanza corrente
2. Avviare la procedura di shutdown ordinato (automatica o manuale)
3. Completare lo shutdown di tutti i server e servizi
4. Margine di sicurezza (aggiungere 30%)

Se il runtime calcolato e insufficiente: ridurre il carico o aggiungere
batterie esterne.
```

#### Pianificazione Sostituzione Batterie

```
Indicatori per sostituzione batterie:
- Eta batterie > 3 anni (piombo-acido) o > 5 anni (litio)
- Runtime effettivo < 80% del nominale
- Test batteria fallito (APC: "Replace Battery" indicator)
- Tensione batteria sotto il nominale a pieno carico
- Numero cicli di scarica elevato (>200 per piombo-acido)

Procedura sostituzione:
1. Acquistare batterie compatibili (verificare modello esatto)
2. Pianificare sostituzione quando alimentazione di rete e disponibile
3. Per UPS con hot-swap batterie: sostituire senza interrompere alimentazione
4. Per UPS senza hot-swap: pianificare durante finestra di manutenzione
5. Dopo sostituzione: eseguire ciclo di calibrazione
6. Documentare data sostituzione e programmare la prossima
```

### Raffreddamento

#### Monitoraggio Temperature

```bash
# Linux: sensori hardware (lm-sensors)
apt install lm-sensors    # Debian/Ubuntu
sensors-detect            # Rilevamento automatico sensori
sensors                   # Lettura sensori

# Monitoraggio ambiente sala server via SNMP
# Sensori ambientali (es. APC NetBotz, Paessler, Akcp)
snmpwalk -v2c -c public sensor-ip .1.3.6.1.4.1.318.1.1.10.2.3.2
```

#### Coordinamento Manutenzione HVAC

L'impianto di condizionamento della sala server richiede manutenzione regolare coordinata con il team facility management:

- **Trimestrale**: pulizia filtri, verifica livello refrigerante, controllo funzionamento ventilatori
- **Semestrale**: verifica completa circuito refrigerante, test termostati, pulizia batterie scambio
- **Annuale**: manutenzione straordinaria completa da tecnico certificato

Pianificare la manutenzione HVAC durante periodi di basso carico termico (inverno) e garantire sempre un sistema di raffreddamento di backup durante gli interventi.

#### Verifica Hot/Cold Aisle

La configurazione hot aisle / cold aisle (corridoio caldo / corridoio freddo) e la base dell'efficienza del raffreddamento in sala server:

```
Verifiche periodiche (trimestrali):
[ ] I server aspirano aria dal corridoio freddo (fronte rack)
[ ] I server espellono aria nel corridoio caldo (retro rack)
[ ] Nessun rack installato con orientamento invertito
[ ] Pannelli ciechi installati in tutti gli slot rack vuoti (evitare bypass aria)
[ ] Cavi gestiti in modo da non ostruire il flusso d'aria
[ ] Nessuna ostruzione nelle griglie del pavimento sopraelevato (se presente)
[ ] Delta temperatura corridoio freddo/caldo: dovrebbe essere 10-15 gradi C
[ ] Nessun punto caldo anomalo (utilizzare termocamera se disponibile)
```

#### Soglie di Alert

| Parametro | Normale | Warning | Critico |
|----------|---------|---------|---------|
| Temperatura ambiente sala | 18-27 C | 27-32 C | > 32 C |
| Umidita relativa | 40-60% | 30-40% o 60-70% | < 30% o > 70% |
| Delta T (inlet-outlet) | 10-15 C | 15-20 C | > 20 C |

### Monitoraggio Ambientale

#### Sensori Umidita

L'umidita e un fattore critico spesso trascurato. Umidita troppo bassa causa scariche elettrostatiche che danneggiano i componenti; umidita troppo alta causa condensa e corrosione.

- Installare sensori di umidita in almeno 2 punti della sala server (ingresso aria fredda e corridoio caldo)
- Range ottimale: 40-60% di umidita relativa
- Configurare alert per valori fuori range
- Se l'umidita e costantemente fuori range, richiedere intervento sull'impianto HVAC (umidificatore/deumidificatore)

#### Rilevamento Perdite Acqua

Le perdite d'acqua in sala server possono derivare da impianto di condizionamento, tubazioni dell'edificio o infiltrazioni. Le conseguenze possono essere catastrofiche.

- Installare sensori di rilevamento acqua sotto il pavimento sopraelevato
- Posizionare sensori vicino a: unita CRAC/CRAH, punti di ingresso tubazioni, sotto le unita UPS
- Configurare alert immediato (email, SMS, chiamata telefonica)
- Predisporre un kit di emergenza: secchi, pompa portatile, teli protettivi

#### Sicurezza Fisica

```
Verifiche mensili:
[ ] Sistema di controllo accessi funzionante (badge, biometrico)
[ ] Log accessi degli ultimi 30 giorni: solo personale autorizzato?
[ ] Telecamere di sorveglianza funzionanti e registranti
[ ] Porte e finestre della sala server: chiuse e bloccate correttamente
[ ] Estintori presenti, con revisione in corso di validita
[ ] Segnaletica di sicurezza visibile e aggiornata
[ ] Inventario chiavi/badge: corrisponde al personale autorizzato attuale?
```

#### Configurazione Sensori Ambientali

Per un monitoraggio completo della sala server, si raccomanda la seguente distribuzione minima di sensori:

- **Temperatura**: almeno 1 sensore ogni 3 rack, posizionato all'ingresso dell'aria fredda (fronte rack, altezza media)
- **Umidita**: almeno 2 sensori per sala (ingresso e uscita aria)
- **Acqua**: sensori a nastro lungo tutto il perimetro del pavimento sopraelevato
- **Fumo**: rilevatori su soffitto e sotto pavimento sopraelevato (se presente)
- **Alimentazione**: monitoraggio su ogni PDU (Power Distribution Unit) principale

Tutti i sensori devono essere integrati nel sistema di monitoraggio centralizzato (Zabbix, PRTG, Nagios) con alert configurati per ogni soglia.

---

## Manutenzione Virtualizzazione

### VMware vSphere

#### Health Check Host ESXi

```bash
# Via SSH all'host ESXi

# Stato generale
esxcli system version get
esxcli system maintenanceMode get
esxcli hardware platform get

# Stato storage
esxcli storage core path list | grep -E "State:|Display Name:"
esxcli storage vmfs extent list

# Stato rete
esxcli network nic list
esxcli network vswitch standard list
esxcli network ip interface list

# Log errori recenti
cat /var/log/vmkernel.log | grep -i -E "error|warn|fail" | tail -50

# Stato hardware (sensori)
esxcli hardware sensor list
```

**Via PowerCLI (da una workstation):**

```powershell
# Connessione
Connect-VIServer -Server vcenter.dominio.local

# Stato host
Get-VMHost | Select Name, ConnectionState, PowerState,
  @{N='CPU_Usage%';E={[math]::Round($_.CpuUsageMhz/$_.CpuTotalMhz*100,1)}},
  @{N='RAM_Usage%';E={[math]::Round($_.MemoryUsageGB/$_.MemoryTotalGB*100,1)}}

# Alert attivi
Get-VMHost | Get-VIEvent -Types Error, Warning -MaxSamples 20 |
  Select CreatedTime, FullFormattedMessage

# Datastore usage
Get-Datastore | Select Name,
  @{N='Free(GB)';E={[math]::Round($_.FreeSpaceGB,1)}},
  @{N='%Free';E={[math]::Round($_.FreeSpaceGB/$_.CapacityGB*100,1)}} |
  Sort '%Free'
```

#### Stato Servizi vCenter

```powershell
# Verifica servizi vCenter (via SSH o API)
# VAMI: https://vcenter:5480 > Services

# Via PowerCLI
Get-Service -ComputerName vcenter | Where-Object {
  $_.DisplayName -like "*VMware*"
} | Select Status, DisplayName

# Servizi critici da verificare:
# - VMware vCenter Server
# - VMware vSphere Profile-Driven Storage
# - VMware vSphere Update Manager (VUM)
# - VMware Certificate Authority (VMCA)
# - VMware Directory Service (vmdir)
```

#### Pulizia Snapshot

Gli snapshot VMware sono una delle cause piu comuni di problemi prestazionali e di esaurimento spazio disco. NON sono un sostituto del backup.

```powershell
# Identificare TUTTE le VM con snapshot
Get-VM | Get-Snapshot | Select VM, Name, Created, SizeGB |
  Sort Created | Format-Table -AutoSize

# Snapshot piu vecchi di 7 giorni (potenziale problema)
Get-VM | Get-Snapshot | Where-Object {
  $_.Created -lt (Get-Date).AddDays(-7)
} | Select VM, Name, Created, @{N='SizeGB';E={[math]::Round($_.SizeGB,2)}} |
  Sort SizeGB -Descending

# Rimuovere snapshot specifico (ATTENZIONE: operazione I/O intensiva)
# Pianificare durante orari di basso utilizzo
Get-VM "nome-vm" | Get-Snapshot -Name "nome-snapshot" | Remove-Snapshot -Confirm:$false

# REGOLA: nessuno snapshot deve esistere per piu di 72 ore in produzione
# Eccezione: snapshot pre-aggiornamento mantenuti fino a conferma stabilita (max 7 giorni)
```

#### Aggiornamento VMware Tools

```powershell
# Verificare versioni VMware Tools
Get-VM | Select Name,
  @{N='ToolsVersion';E={$_.ExtensionData.Guest.ToolsVersion}},
  @{N='ToolsStatus';E={$_.ExtensionData.Guest.ToolsVersionStatus2}}

# VM con Tools non aggiornati
Get-VM | Where-Object {
  $_.ExtensionData.Guest.ToolsVersionStatus2 -ne 'guestToolsCurrent'
} | Select Name, PowerState

# Aggiornare VMware Tools (richiede breve interruzione rete sulla VM)
Get-VM "nome-vm" | Update-Tools -NoReboot
```

#### Verifica HA e DRS

```powershell
# Stato cluster HA
Get-Cluster | Select Name,
  @{N='HA_Enabled';E={$_.HAEnabled}},
  @{N='HA_Admission';E={$_.HAAdmissionControlEnabled}},
  @{N='DRS_Enabled';E={$_.DrsEnabled}},
  @{N='DRS_Mode';E={$_.DrsAutomationLevel}}

# Verificare che HA sia configurato per tollerare almeno 1 host failure
# Verificare che il DRS sia bilanciato (nessun host sovraccarico)

# Host in stato HA
Get-VMHost | Select Name,
  @{N='ConnectionState';E={$_.ConnectionState}},
  @{N='HAState';E={$_.ExtensionData.Runtime.DasHostState.State}}

# Tutti gli host devono essere in stato "connectedToMaster" o "master"
```

### Hyper-V

#### Health Check Host

```powershell
# Stato host Hyper-V
Get-VMHost | Select Name, VirtualMachineMigrationEnabled,
  LogicalProcessorCount, MemoryCapacity

# Stato VM
Get-VM | Select Name, State, CPUUsage, MemoryAssigned,
  @{N='MemoryAssigned(GB)';E={[math]::Round($_.MemoryAssigned/1GB,2)}},
  Uptime, Status

# Stato replica Hyper-V (se configurata)
Get-VMReplication | Select VMName, State, Health, Mode,
  LastReplicationTime

# Verifica Integration Services
Get-VM | Select Name, IntegrationServicesVersion,
  @{N='ISUpToDate';E={
    $_.IntegrationServicesVersion -ge [version]"6.3.9600.0"
  }}

# Stato storage
Get-VMHost | Get-VMHostStorage | Select -ExpandProperty Path
Get-Volume | Where DriveType -eq 'Fixed' | Select DriveLetter,
  FileSystemLabel, @{N='Free(GB)';E={[math]::Round($_.SizeRemaining/1GB,2)}},
  @{N='%Free';E={[math]::Round($_.SizeRemaining/$_.Size*100,1)}}
```

#### Pulizia Checkpoint Hyper-V

```powershell
# Elenco checkpoint (equivalente snapshot VMware)
Get-VM | Get-VMCheckpoint | Select VMName, Name, CreationTime,
  @{N='SizeGB';E={[math]::Round(
    (Get-ChildItem $_.HardDrives.Path -ErrorAction SilentlyContinue |
    Measure-Object Length -Sum).Sum/1GB, 2)}}

# Rimuovere checkpoint obsoleti
Get-VM "nome-vm" | Get-VMCheckpoint | Where-Object {
  $_.CreationTime -lt (Get-Date).AddDays(-7)
} | Remove-VMCheckpoint

# ATTENZIONE: la rimozione del checkpoint causa un merge del disco
# differenziale. Operazione I/O intensiva, pianificare in orari di basso carico.
```

#### Validazione Cluster

```powershell
# Test validazione cluster (non impatta i servizi in esecuzione)
Test-Cluster -Node node1,node2 -Include "Storage","Network","Inventory"

# Stato cluster
Get-ClusterNode | Select Name, State, DynamicWeight
Get-ClusterGroup | Select Name, OwnerNode, State
Get-ClusterSharedVolume | Select Name, State,
  @{N='FreeGB';E={[math]::Round(
    ($_ | Select -Expand SharedVolumeInfo | Select -Expand Partition).FreeSpace/1GB, 2)}}

# Verificare Cluster Shared Volumes
Get-ClusterSharedVolumeState | Select Name, Node, StateInfo

# Quorum
Get-ClusterQuorum | Select Cluster, QuorumResource, QuorumType
```

### Proxmox VE

#### Health Check Nodo

```bash
# Stato nodo
pvesh get /nodes/$(hostname)/status

# Informazioni versione
pveversion -v

# Stato storage
pvesm status

# Lista VM e stato
qm list

# Lista container LXC e stato
pct list

# Stato servizi Proxmox
systemctl status pve-cluster
systemctl status pvedaemon
systemctl status pveproxy
systemctl status pvestatd

# Log recenti
journalctl -u pvedaemon --since "24 hours ago" --priority=err
journalctl -u pve-cluster --since "24 hours ago" --priority=err
```

#### Verifica Storage

```bash
# Stato pool ZFS (se utilizzato)
zpool status
zpool list
zfs list

# Stato Ceph (se utilizzato)
ceph status
ceph osd tree
ceph df
rados df

# Spazio storage disponibile
pvesm status | column -t

# Verificare:
# - Nessun disco in stato DEGRADED o FAULTED (ZFS)
# - Nessun OSD down (Ceph)
# - Spazio libero > 20% su ogni storage
```

#### Verifica Backup

```bash
# Lista backup pianificati
cat /etc/pve/jobs.cfg

# Verifica ultimo backup eseguito
# Directory backup predefinita
ls -la /var/lib/vz/dump/

# Verifica log ultimo backup
ls -lt /var/log/vzdump/*.log | head -5
tail -50 /var/log/vzdump/vzdump-*.log

# Verificare:
# - Tutti i servizi critici hanno un job di backup configurato
# - I backup completano senza errori
# - La retention policy e adeguata
# - Lo storage di backup ha spazio sufficiente
```

#### Stato Cluster

```bash
# Stato cluster Proxmox
pvecm status
pvecm nodes

# Stato quorum
pvecm expected 1    # NON eseguire: questo e solo per consultazione del quorum atteso

# Verifica corosync
corosync-cfgtool -s
corosync-quorumtool

# Verificare:
# - Tutti i nodi online
# - Quorum raggiunto
# - Nessun errore di comunicazione tra nodi
# - Ring status: no faults
```

### KVM/libvirt

#### Health Check con virsh

```bash
# Lista VM e stato
virsh list --all

# Informazioni nodo
virsh nodeinfo
virsh nodememstats
virsh nodecpustats

# Stato VM specifica
virsh dominfo nome-vm
virsh domstats nome-vm

# Dettaglio interfacce di rete VM
virsh domiflist nome-vm
virsh domifstat nome-vm vnet0

# Dettaglio dischi VM
virsh domblklist nome-vm
virsh domblkstat nome-vm vda

# Verifica console log (utile per debug boot)
virsh console nome-vm    # Ctrl+] per uscire

# Snapshot (se supportato dallo storage backend)
virsh snapshot-list nome-vm
```

#### Verifica Storage Pool

```bash
# Lista pool di storage
virsh pool-list --all

# Dettaglio pool specifico
virsh pool-info default

# Verificare:
# - Tutti i pool in stato "active" e "running"
# - Spazio disponibile adeguato
# - Nessun errore su volumi

# Lista volumi in un pool
virsh vol-list default

# Refresh pool (aggiorna informazioni)
virsh pool-refresh default
```

#### Stato Bridge di Rete

```bash
# Stato bridge
brctl show
# oppure (su sistemi piu recenti)
bridge link show
ip link show type bridge

# Verificare:
# - Tutti i bridge previsti sono attivi
# - Le interfacce corrette sono associate ai bridge
# - Lo stato e UP per tutti i componenti

# Dettaglio bridge
bridge -d link show br0
ip -s link show br0

# Verifica connettivita
ping -c 3 gateway-ip    # dal bridge di gestione
```

---

## Metriche di Manutenzione: MTBF, MTTR, MTTA, MTTF

La misurazione e il fondamento di qualsiasi programma di manutenzione preventiva maturo. Senza metriche oggettive e possibile avere solo percezioni soggettive sull'efficacia del programma. Le metriche di manutenzione permettono di quantificare le prestazioni, identificare aree di miglioramento, giustificare investimenti e confrontare le proprie performance con benchmark di settore. Secondo le best practice SMRP (Society for Maintenance and Reliability Professionals, 6a edizione), un programma di manutenzione preventiva world-class raggiunge una compliance del 90% o superiore, ovvero almeno 9 attivita su 10 pianificate vengono completate entro la finestra prevista. Per asset critici di classe A, l'obiettivo sale al 95%.

### MTBF — Mean Time Between Failures

Il MTBF (Tempo Medio Tra i Guasti) e la metrica piu utilizzata per quantificare l'affidabilita di un componente o sistema riparabile. Rappresenta il tempo medio di funzionamento tra un guasto e il successivo, e viene espresso in ore.

**Formula:**

```
MTBF = Tempo Totale di Funzionamento / Numero di Guasti

Esempio pratico:
Un server ha funzionato per 8.760 ore (1 anno) e ha subito 2 guasti.
MTBF = 8.760 / 2 = 4.380 ore

Interpretazione: mediamente, ci si puo aspettare un guasto ogni 4.380 ore
(circa 6 mesi) su questo specifico server.
```

**Valori di riferimento MTBF per componenti IT:**

| Componente | MTBF Tipico | Note |
|-----------|------------|------|
| Server enterprise (complessivo) | 15.000 - 30.000 ore | Dipende dalla qualita dei componenti e dall'ambiente |
| Hard disk HDD enterprise | 1.000.000 - 2.500.000 ore | Il valore reale e spesso inferiore al dichiarato |
| SSD enterprise NVMe | 2.000.000 - 2.500.000 ore | Maggiore affidabilita meccanica rispetto agli HDD |
| SSD consumer | 1.500.000 - 1.800.000 ore | Non adatti a carichi enterprise sostenuti |
| Modulo RAM ECC | 1.000.000+ ore | Errori corretti non contano come guasti |
| Alimentatore server (PSU) | 100.000 - 200.000 ore | Ridondanza mitiga l'impatto |
| Switch enterprise | 200.000 - 500.000 ore | Esclude guasti software/firmware |
| Router enterprise | 150.000 - 400.000 ore | Include componenti meccanici (ventole) |
| UPS (elettronica) | 100.000 - 300.000 ore | Esclusa la vita delle batterie |
| Ventola server | 50.000 - 100.000 ore | Componente con vita utile piu breve |

**Attenzione critica sull'interpretazione del MTBF:** il MTBF non significa che un componente durera quel numero di ore prima di guastarsi. E una misura statistica calcolata su una popolazione di componenti. Un disco con MTBF dichiarato di 2.000.000 ore non durera 228 anni. Significa che su una popolazione ampia di dischi identici, la frequenza media dei guasti corrisponde a quel valore. In un datacenter con 1.000 dischi identici con MTBF di 1.000.000 ore, ci si aspetta mediamente circa 8-9 guasti disco all'anno (1.000 * 8.760 / 1.000.000 ≈ 8,76).

### MTTR — Mean Time To Repair

Il MTTR (Tempo Medio di Riparazione) misura il tempo medio necessario per ripristinare un componente o sistema dal momento del guasto al momento del ritorno in servizio. E la metrica complementare al MTBF e insieme definiscono la disponibilita del sistema.

**Formula:**

```
MTTR = Tempo Totale di Riparazione / Numero di Riparazioni

Esempio pratico:
Nell'arco di un anno, un server ha subito 3 guasti con i seguenti tempi di
riparazione: 2 ore, 4 ore, 3 ore.
MTTR = (2 + 4 + 3) / 3 = 3 ore

Nota: il tempo di riparazione include:
- Tempo di diagnosi (identificazione del guasto)
- Tempo di approvvigionamento pezzi di ricambio
- Tempo di riparazione effettiva
- Tempo di test e validazione post-riparazione
```

**Obiettivi MTTR per categorie di sistemi:**

| Categoria Sistema | MTTR Target | Strategia per Raggiungere il Target |
|------------------|-------------|--------------------------------------|
| Sistemi Tier 1 (mission-critical) | < 1 ora | Hot spare, contratti 4h on-site, ridondanza totale |
| Sistemi Tier 2 (business-critical) | < 4 ore | Contratto NBD (Next Business Day), parti a scorta |
| Sistemi Tier 3 (supporto) | < 8 ore | Contratto standard vendor, procedure documentate |
| Sistemi Tier 4 (non critici) | < 24 ore | Best effort, parti su ordine |

**Come ridurre il MTTR:**

1. **Documentazione accessibile**: runbook dettagliati con procedure passo-passo per ogni scenario di guasto conosciuto
2. **Parti di ricambio a scorta**: mantenere hot spare per i componenti piu critici e soggetti a guasto (dischi, PSU, ventole, moduli RAM)
3. **Contratti di supporto adeguati**: SLA del vendor allineati alla criticita del sistema (4 ore per Tier 1, NBD per Tier 2)
4. **Formazione del team**: tutto il personale deve saper eseguire le procedure di ripristino dei sistemi critici
5. **Strumenti diagnostici pronti**: tool di diagnostica preinstallati e accessibili (iDRAC/iLO per server, console di management per rete)
6. **Monitoraggio proattivo**: rilevamento rapido del guasto riduce il tempo totale di disservizio

### MTTA — Mean Time To Acknowledge

Il MTTA (Tempo Medio di Presa in Carico) misura il tempo tra la generazione di un alert e il momento in cui un operatore lo prende in carico. E una metrica spesso trascurata ma fondamentale per misurare l'efficacia del processo di gestione degli incidenti e la reattivita del team.

```
MTTA = Tempo Totale di Presa in Carico / Numero di Alert

Esempio: 5 alert nel mese con tempi di presa in carico di
5 min, 15 min, 3 min, 45 min, 10 min
MTTA = (5 + 15 + 3 + 45 + 10) / 5 = 15,6 minuti

Target raccomandati:
- Orario lavorativo: < 15 minuti
- Fuori orario (reperibilita): < 30 minuti
- Weekend/festivita: < 60 minuti
```

Un MTTA elevato indica problemi nel processo di notifica (alert che non raggiungono l'operatore), nella copertura del team (personale insufficiente) o nel sistema di escalation (mancanza di procedure chiare su chi deve rispondere e quando).

### MTTF — Mean Time To Failure

Il MTTF (Tempo Medio al Guasto) e simile al MTBF ma si applica a componenti non riparabili, ovvero che vengono sostituiti anziche riparati. Esempi tipici: batterie UPS, nastri magnetici, supporti ottici, lampade di proiettori. La formula e identica al MTBF ma il contesto e diverso: dopo il guasto, il componente viene scartato e sostituito con uno nuovo.

```
MTTF = Tempo Totale di Funzionamento / Numero di Guasti (su componenti diversi)

Esempio: 10 batterie UPS identiche installate contemporaneamente.
3 si guastano dopo 28.000, 32.000 e 26.000 ore rispettivamente.
MTTF = (28.000 + 32.000 + 26.000) / 3 = 28.667 ore
```

### Disponibilita del Sistema

La disponibilita (Availability) e il rapporto tra il tempo in cui il sistema e operativo e il tempo totale. Combina MTBF e MTTR in un singolo indicatore percentuale facilmente comprensibile anche dal management non tecnico.

**Formula:**

```
Availability = MTBF / (MTBF + MTTR) * 100

Esempio:
Server con MTBF = 4.380 ore e MTTR = 3 ore
Availability = 4.380 / (4.380 + 3) * 100 = 99,93%
```

**Tabella di riferimento disponibilita:**

| Livello | Uptime % | Downtime Annuo | Uso Tipico |
|---------|---------|----------------|------------|
| 2 nines | 99% | 87,6 ore (3,65 giorni) | Sistemi non critici interni |
| 3 nines | 99,9% | 8,76 ore | Applicazioni business standard |
| 4 nines | 99,99% | 52,6 minuti | Servizi business-critical |
| 5 nines | 99,999% | 5,26 minuti | Infrastruttura mission-critical |
| 6 nines | 99,9999% | 31,5 secondi | Telecomunicazioni, finanza HFT |

### Dashboard KPI di Manutenzione

Per un monitoraggio efficace delle metriche, implementare una dashboard che visualizzi in tempo reale i seguenti KPI:

```
KPI principali da tracciare:

1. MTBF per categoria di asset (server, storage, rete)
2. MTTR per categoria di asset e livello di criticita
3. MTTA (tempo medio di presa in carico alert)
4. PM Compliance Rate (% attivita PM completate nei tempi)
5. Rapporto manutenzione pianificata vs non pianificata (target: 80/20)
6. Numero di guasti per mese (trend)
7. Costo manutenzione per asset
8. Backlog di manutenzione (attivita in arretrato)
9. Tasso di primo intervento risolutivo (First Time Fix Rate)
10. Disponibilita per sistema/servizio
```

Rendere la dashboard visibile al team (monitor in sala operativa o pagina web accessibile) favorisce la cultura della responsabilita condivisa e permette di identificare rapidamente trend negativi prima che diventino problemi gravi.

### Calcolo Pratico: Scenario Completo

Consideriamo un ambiente IT con 20 server che operano per un anno (8.760 ore ciascuno):

```
Dati dell'anno:
- Tempo totale di funzionamento: 20 * 8.760 = 175.200 ore
- Guasti totali registrati: 12
- Tempo totale di riparazione: 47 ore
- Alert totali generati: 340
- Tempo totale presa in carico: 2.890 minuti

Calcolo metriche:
MTBF = 175.200 / 12 = 14.600 ore (buono, sopra la media)
MTTR = 47 / 12 = 3,92 ore (accettabile per sistemi Tier 2-3)
MTTA = 2.890 / 340 = 8,5 minuti (eccellente)
Availability = 14.600 / (14.600 + 3,92) * 100 = 99,97% (circa 4 nines)
PM Compliance = (esecuzioni completate / esecuzioni pianificate) * 100

Costo stimato dei guasti:
- Costo medio per ora di riparazione (personale + parti): 250 EUR
- Costo medio per ora di downtime (impatto business): 15.000 EUR
- Costo totale riparazioni: 47 * 250 = 11.750 EUR
- Costo totale impatto business: 47 * 15.000 = 705.000 EUR
- Costo totale annuo guasti: 716.750 EUR

Se la manutenzione preventiva avesse prevenuto il 60% dei guasti:
- Guasti evitati: 7
- Ore di downtime evitate: ~28 ore
- Risparmio: ~28 * 15.000 = 420.000 EUR
```

---

## Manutenzione Predittiva e Basata su Condizione — Approfondimento

La manutenzione predittiva rappresenta l'evoluzione naturale della manutenzione preventiva. Mentre quest'ultima si basa su intervalli temporali fissi (sostituisci la batteria ogni 3 anni, applica le patch ogni mese), la manutenzione predittiva si basa sulle condizioni reali del componente, intervenendo quando i dati indicano un degrado imminente. Questo approccio ottimizza sia i costi (evitando sostituzioni premature di componenti ancora funzionanti) sia l'affidabilita (intervenendo prima del guasto effettivo).

### La Curva di Degrado (P-F Curve)

Il concetto fondamentale della manutenzione predittiva e la curva P-F (Potential Failure - Functional Failure). Ogni componente attraversa una fase di degrado progressivo prima del guasto funzionale completo. L'intervallo P-F rappresenta il tempo tra il punto in cui il degrado diventa rilevabile (P) e il punto in cui il componente smette di funzionare (F).

```
Prestazione
  ^
  |████████████████████
  |                    ████
  |                        ████
  |                            ██── P (Potential Failure: degrado rilevabile)
  |                              ██
  |                                ██
  |                                  ██── Punto di intervento ottimale
  |                                    ██
  |                                      ██── F (Functional Failure: guasto)
  +─────────────────────────────────────────> Tempo
  
  |<──── Funzionamento normale ────>|<─ P-F interval ─>|

L'obiettivo della manutenzione predittiva e rilevare il punto P il piu
presto possibile e pianificare l'intervento nel P-F interval, prima di
raggiungere il punto F.
```

**Intervalli P-F tipici per componenti IT:**

| Componente | Indicatore di Degrado | Intervallo P-F Tipico |
|-----------|----------------------|----------------------|
| HDD | Settori riallocati crescenti | Settimane - mesi |
| SSD NVMe | Usura endurance >80% | Mesi |
| RAM ECC | Errori corretti crescenti | Giorni - settimane |
| Ventola server | Velocita anomala, vibrazione | Giorni - settimane |
| Batteria UPS | Runtime ridotto, resistenza interna alta | Mesi |
| PSU server | Efficienza ridotta, temperatura elevata | Settimane - mesi |
| Condensatori (server/switch) | Rigonfiamento visivo, ESR elevato | Settimane - mesi |

### Metodologia di Monitoraggio Basato su Condizione

Il monitoraggio basato su condizione (Condition-Based Monitoring, CBM) richiede una pipeline strutturata di raccolta, analisi e azione sui dati:

**Fase 1: Raccolta Dati**

La raccolta dati deve essere automatizzata, continua e centralizzata. I principali canali di raccolta per l'infrastruttura IT sono:

- **IPMI/BMC**: temperatura CPU, tensione, velocita ventole, stato PSU, eventi hardware
- **SMART/NVMe Health**: usura SSD, settori riallocati HDD, errori di lettura/scrittura, temperatura disco
- **EDAC/ECC**: contatori errori memoria corretti e non corretti
- **SNMP**: metriche ambientali (temperatura sala, umidita), stato UPS, metriche di rete
- **Log di sistema**: eventi kernel, errori driver, crash applicativi, timeout I/O
- **Contatori prestazionali**: latenza I/O, throughput rete, utilizzo CPU/RAM nel tempo

**Fase 2: Definizione delle Baseline**

Per ogni metrica raccolta, stabilire una baseline di funzionamento normale basata su almeno 30 giorni di dati storici:

```bash
# Esempio: raccolta baseline temperatura CPU su Linux
# Salvare dati ogni 5 minuti per 30 giorni

#!/bin/bash
# /usr/local/bin/collect_baseline.sh
LOGDIR="/var/log/maintenance/baseline"
mkdir -p "$LOGDIR"
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)

# Temperatura CPU via lm-sensors
CPU_TEMP=$(sensors | grep -oP 'Package id 0:\s+\+\K[0-9.]+')

# Carico CPU
CPU_LOAD=$(awk '{print $1}' /proc/loadavg)

# Utilizzo memoria
MEM_USED=$(free | awk '/^Mem:/{printf "%.1f", $3/$2*100}')

# Latenza I/O media
IO_AWAIT=$(iostat -d -x 1 2 | awk '/^sd|^nvme/{sum+=$10; n++} END{if(n>0) printf "%.2f", sum/n; else print "0"}')

echo "${TIMESTAMP},${CPU_TEMP},${CPU_LOAD},${MEM_USED},${IO_AWAIT}" \
  >> "${LOGDIR}/baseline_$(hostname)_$(date +%Y%m).csv"

# Cron entry (ogni 5 minuti):
# */5 * * * * /usr/local/bin/collect_baseline.sh
```

**Fase 3: Definizione Soglie e Trend**

Le soglie statiche (temperatura > X gradi) sono utili ma insufficienti. La vera potenza della manutenzione predittiva sta nell'analisi dei trend:

```
Regole di trend analysis:

1. RATE OF CHANGE: se una metrica cresce piu del 10% in una settimana
   rispetto alla baseline, investigare.
   Esempio: temperatura CPU baseline 55°C, questa settimana media 62°C
   → delta +12,7% → investigare (polvere? ventola degradata? carico anomalo?)

2. ACCELERAZIONE: se il tasso di crescita stesso sta accelerando, la
   situazione e piu urgente.
   Esempio: settori riallocati HDD: +2/mese per 6 mesi, poi +8/mese
   → il tasso di degrado sta accelerando → pianificare sostituzione

3. CORRELAZIONE: se piu metriche peggiorano insieme, il problema
   potrebbe essere ambientale.
   Esempio: temperature CPU + temperature disco + velocita ventole tutte
   in aumento → possibile problema HVAC in sala server

4. STAGIONALITA: alcune variazioni sono normali (temperature estive piu
   alte) e non devono generare falsi positivi.
```

**Fase 4: Azione — Dall'Alert all'Intervento**

```
Matrice decisionale predittiva:

| Condizione Rilevata | Urgenza | Azione |
|---------------------|---------|--------|
| Metrica sopra soglia statica WARNING | Media | Ticket, investigare entro 48h |
| Metrica sopra soglia statica CRITICAL | Alta | Ticket urgente, investigare entro 4h |
| Trend negativo costante | Media | Pianificare intervento nella prossima MW |
| Trend negativo in accelerazione | Alta | Pianificare intervento nella MW piu vicina |
| Correlazione multi-metrica anomala | Alta | Investigazione immediata causa radice |
| Superamento vita utile componente | Media | Pianificare sostituzione preventiva |
```

### Limiti della Manutenzione Predittiva Basata su SMART

E importante comprendere i limiti dei dati SMART per la predizione dei guasti disco. La ricerca accademica e industriale ha dimostrato che i modelli predittivi basati su attributi SMART raggiungono una precisione del 70% circa, ma il recall (capacita di identificare tutti i dischi che guasteranno) non supera il 50%. Questo significa che circa la meta dei guasti disco avviene senza preavviso rilevabile tramite SMART, i cosiddetti "sudden death" (morti improvvise). Le cause includono difetti del firmware, guasti elettronici improvvisi, sbalzi di tensione e difetti meccanici catastrofici non preceduti da degrado graduale.

**Implicazione pratica:** la manutenzione predittiva basata su SMART e un complemento eccellente alla manutenzione preventiva, non un sostituto. Continuare a pianificare sostituzioni preventive basate sull'eta del componente e mantenere la ridondanza RAID rimane essenziale anche in presenza di un eccellente sistema di monitoraggio predittivo.

### Integrazione Predittiva nel Workflow di Manutenzione

```
Workflow integrato preventivo + predittivo:

1. MANUTENZIONE PREVENTIVA (schedulata):
   - Interventi a calendario fisso (daily/weekly/monthly/quarterly/yearly)
   - Indipendente dai dati di condizione
   - Base minima garantita di manutenzione

2. MANUTENZIONE PREDITTIVA (su condizione):
   - Monitoraggio continuo delle metriche di salute
   - Alert su deviazioni dalla baseline
   - Interventi aggiuntivi quando i dati lo indicano
   - Puo anticipare o posticipare interventi preventivi

3. SINERGIA:
   - Dati predittivi ottimizzano il calendario preventivo
   - Calendario preventivo copre i "punti ciechi" del predittivo
   - Il risultato e un approccio ibrido superiore a ciascuno singolarmente
```

---

## Monitoraggio Usura SSD/NVMe: TBW e DWPD — Approfondimento

Gli SSD, a differenza degli HDD, non hanno parti meccaniche soggette a usura fisica, ma le celle di memoria flash NAND hanno un numero finito di cicli di programmazione/cancellazione (P/E cycles). Monitorare il livello di usura e fondamentale per pianificare le sostituzioni preventive ed evitare perdite di dati.

### TBW — Terabytes Written

Il TBW (Terabyte Scritti) rappresenta la quantita totale di dati che un SSD e progettato per scrivere durante la sua intera vita utile. E la specifica di endurance piu intuitiva.

```
Esempio:
Un SSD da 1 TB con rating di 600 TBW puo scrivere 600 terabyte totali
prima di raggiungere la fine della vita utile dichiarata.

Se si scrivono mediamente 30 GB al giorno:
Vita stimata = 600.000 GB / 30 GB/giorno = 20.000 giorni ≈ 54,8 anni

Se si scrivono mediamente 100 GB al giorno (carico server moderato):
Vita stimata = 600.000 GB / 100 GB/giorno = 6.000 giorni ≈ 16,4 anni

Se si scrivono mediamente 500 GB al giorno (database OLTP attivo):
Vita stimata = 600.000 GB / 500 GB/giorno = 1.200 giorni ≈ 3,3 anni
```

### DWPD — Drive Writes Per Day

Il DWPD (Scritture Giornaliere dell'Intero Drive) indica quante volte al giorno e possibile sovrascrivere l'intera capacita dell'SSD per l'intera durata della garanzia (tipicamente 5 anni).

```
Formula di conversione:

DWPD = TBW / (Capacita_Drive_TB * 365 * Anni_Garanzia)

Esempio:
SSD 1.6 TB con 8.760 TBW e garanzia 5 anni
DWPD = 8.760 / (1,6 * 365 * 5) = 8.760 / 2.920 = 3 DWPD

Conversione inversa:
TBW = DWPD * Capacita_Drive_TB * 365 * Anni_Garanzia

Esempio:
SSD 960 GB (0,96 TB), 1 DWPD, garanzia 5 anni
TBW = 1 * 0,96 * 365 * 5 = 1.752 TBW
```

### Classificazione SSD per Endurance

| Categoria | DWPD | Uso Tipico | Esempi |
|-----------|------|-----------|--------|
| Read-intensive | 0,3 - 1 DWPD | Boot OS, web serving, media streaming, backup | Intel D3-S4520, Samsung PM893 |
| Mixed-use | 1 - 3 DWPD | Virtualizzazione, email, file server, applicazioni generiche | Intel D3-S4620, Samsung PM897 |
| Write-intensive | 3 - 25+ DWPD | Database OLTP, WAL, cache tier, logging ad alto volume | Intel D7-P5620, Samsung PM1735 |

**Regola pratica per la selezione:** scegliere un SSD con DWPD pari ad almeno 1,5 volte il carico di scrittura effettivo previsto, per garantire margine di sicurezza e tenere conto del write amplification factor (WAF), che tipicamente varia tra 1,1x e 3x a seconda del controller, del firmware e del pattern di scrittura.

### Write Amplification Factor (WAF)

Il WAF e il rapporto tra la quantita di dati effettivamente scritti sulle celle NAND e la quantita di dati che l'host ha richiesto di scrivere. E sempre >= 1 a causa delle operazioni interne dell'SSD (garbage collection, wear leveling, metadata updates).

```
WAF = Dati_Scritti_NAND / Dati_Scritti_Host

WAF tipici:
- Workload sequenziale: 1,1 - 1,5x
- Workload casuale misto: 2,0 - 3,0x
- Workload casuale scritture piccole: 3,0 - 5,0x

Impatto pratico:
Se un SSD ha 3.000 TBW e il WAF e 2,0x, la quantita di dati
che l'host puo scrivere e effettivamente 3.000 / 2,0 = 1.500 TB

Monitoraggio WAF su NVMe:
nvme smart-log /dev/nvme0 | grep -E "data_units_written|host_write"
# Confrontare data_units_written (lato NAND) con host_write_commands
```

### Monitoraggio Avanzato Endurance SSD

```bash
# Script completo di monitoraggio usura SSD
#!/bin/bash
# /usr/local/bin/ssd_health_report.sh

echo "============================================"
echo "Report Salute SSD - $(hostname)"
echo "Data: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "============================================"
echo ""

for disk in /dev/nvme?; do
  if [ -b "$disk" ]; then
    echo "--- Disco: $disk ---"
    
    # Modello e firmware
    smartctl -i "$disk" | grep -E "Model|Firmware|Serial|Size"
    
    # Metriche di salute NVMe
    PERCENT_USED=$(smartctl -A "$disk" | grep "Percentage Used" | awk '{print $3}' | tr -d '%')
    AVAIL_SPARE=$(smartctl -A "$disk" | grep "Available Spare:" | awk '{print $3}' | tr -d '%')
    DATA_WRITTEN=$(smartctl -A "$disk" | grep "Data Units Written" | awk '{print $4}' | tr -d ',')
    POWER_ON=$(smartctl -A "$disk" | grep "Power On Hours" | awk '{print $4}' | tr -d ',')
    MEDIA_ERRORS=$(smartctl -A "$disk" | grep "Media and Data" | awk '{print $6}')
    UNSAFE_SHUTDOWNS=$(smartctl -A "$disk" | grep "Unsafe Shutdowns" | awk '{print $3}')
    TEMP=$(smartctl -A "$disk" | grep "Temperature:" | head -1 | awk '{print $2}')
    
    echo "  Usura: ${PERCENT_USED}%"
    echo "  Spare disponibile: ${AVAIL_SPARE}%"
    echo "  Dati scritti: ${DATA_WRITTEN} unita (x 512KB)"
    echo "  Ore funzionamento: ${POWER_ON}"
    echo "  Errori media: ${MEDIA_ERRORS}"
    echo "  Shutdown non sicuri: ${UNSAFE_SHUTDOWNS}"
    echo "  Temperatura: ${TEMP} C"
    
    # Soglie di alert
    if [ -n "$PERCENT_USED" ] && [ "$PERCENT_USED" -ge 80 ]; then
      echo "  *** ATTENZIONE: Usura >= 80% - Pianificare sostituzione ***"
    fi
    if [ -n "$AVAIL_SPARE" ] && [ "$AVAIL_SPARE" -le 20 ]; then
      echo "  *** ATTENZIONE: Spare disponibile <= 20% ***"
    fi
    if [ -n "$MEDIA_ERRORS" ] && [ "$MEDIA_ERRORS" -gt 0 ]; then
      echo "  *** CRITICO: Errori media rilevati! Investigare immediatamente ***"
    fi
    if [ -n "$TEMP" ] && [ "$TEMP" -ge 70 ]; then
      echo "  *** ATTENZIONE: Temperatura elevata (>= 70 C) ***"
    fi
    echo ""
  fi
done

# Per dischi SATA SSD
for disk in /dev/sd?; do
  if [ -b "$disk" ]; then
    IS_SSD=$(cat "/sys/block/$(basename $disk)/queue/rotational" 2>/dev/null)
    if [ "$IS_SSD" = "0" ]; then
      echo "--- Disco SATA SSD: $disk ---"
      smartctl -i "$disk" | grep -E "Model|Firmware|Serial|Capacity"
      
      # Attributi usura SATA SSD
      WEAR=$(smartctl -A "$disk" | grep -i -E "wear_leveling|media_wearout|percent_lifetime" | head -1)
      if [ -n "$WEAR" ]; then
        echo "  Indicatore usura: $WEAR"
      fi
      
      REALLOC=$(smartctl -A "$disk" | grep "Reallocated_Sector" | awk '{print $10}')
      if [ -n "$REALLOC" ] && [ "$REALLOC" -gt 0 ]; then
        echo "  *** ATTENZIONE: Settori riallocati: $REALLOC ***"
      fi
      echo ""
    fi
  fi
done
```

### Criteri di Sostituzione Preventiva SSD

```
Soglie di sostituzione preventiva raccomandate:

SOSTITUZIONE IMMEDIATA (entro 7 giorni):
- Media Errors > 0 (qualsiasi errore media indica problema grave)
- Available Spare < 10%
- Percentage Used > 100% (superata la vita nominale)
- Test SMART fallito (SMART overall-health: FAILED)

SOSTITUZIONE PIANIFICATA (entro 30 giorni):
- Percentage Used > 90%
- Available Spare < 15%
- Unsafe Shutdowns in rapido aumento

MONITORAGGIO INTENSIFICATO (alert settimanale):
- Percentage Used > 80%
- Available Spare < 25%
- Temperatura operativa costantemente > 65°C
- WAF anomalmente alto (possibile problema firmware)

NOTA IMPORTANTE:
Superare la soglia di endurance dichiarata (100% Percentage Used)
invalida la garanzia del produttore ma non significa guasto immediato.
Molti SSD continuano a funzionare oltre la specifica. Tuttavia, in
ambiente di produzione, e irresponsabile operare oltre questa soglia
senza piano di sostituzione attivo.
```

---

## Analisi Costi-Benefici della Manutenzione Preventiva

Uno dei maggiori ostacoli all'implementazione di un programma di manutenzione preventiva completo e la difficolta nel giustificare i costi al management. Questa sezione fornisce strumenti concreti per quantificare il ritorno sull'investimento e comunicarlo efficacemente ai decisori aziendali.

### Il Rapporto Costo Preventivo vs Reattivo

Secondo dati del Dipartimento dell'Energia degli Stati Uniti (DoE), la manutenzione preventiva genera un risparmio del 12-18% rispetto alla manutenzione puramente reattiva. Studi indipendenti confermano che la manutenzione reattiva costa da 2 a 5 volte di piu rispetto alla preventiva, e che la manutenzione predittiva aggiunge un ulteriore risparmio dell'8-12% rispetto alla sola preventiva.

```
Regola empirica dei costi:

1 EUR investito in prevenzione = 5 EUR risparmiati in reazione

Rapporto di costo per tipo di manutenzione:
- Preventiva (base):         1x
- Predittiva:                0,9x (risparmio 10% rispetto alla preventiva)
- Correttiva pianificata:    2-3x
- Correttiva d'emergenza:    5-10x (inclusi straordinari, perdita produttivita)
```

### Formula ROI della Manutenzione Preventiva

```
ROI_PM = ((Costi_Evitati - Costo_Programma_PM) / Costo_Programma_PM) * 100

Dove:
Costi_Evitati = (Guasti_Prevenuti * Costo_Medio_Guasto) +
                (Ore_Downtime_Evitate * Costo_Orario_Downtime) +
                (Risparmio_Vita_Utile_Estesa)

Costo_Programma_PM = Costo_Personale_PM + Costo_Strumenti + 
                     Costo_Parti_Ricambio_Preventive + Costo_Formazione
```

### Scenario di Calcolo Dettagliato: PMI con 10 Server

```
SCENARIO: Azienda media, 10 server, 50 utenti, settore servizi

COSTO DEL PROGRAMMA DI MANUTENZIONE PREVENTIVA (annuale):
- Personale dedicato (0,5 FTE tecnico): 22.000 EUR
- Software di monitoraggio (Zabbix/open source): 0 EUR (licenza)
- Manutenzione hardware contratti vendor: 8.000 EUR
- Parti di ricambio preventive (dischi, batterie, ventole): 3.000 EUR
- Formazione annuale del personale: 2.000 EUR
- Strumenti e licenze software manutenzione: 1.500 EUR
TOTALE PROGRAMMA PM: 36.500 EUR/anno

COSTO SENZA MANUTENZIONE PREVENTIVA (stima basata su statistiche):
- Guasti non pianificati stimati: 8-12/anno (vs 3-4 con PM)
- Costo medio per guasto (riparazione + parti + downtime):
  - Guasto disco con perdita dati: 5.000-25.000 EUR
  - Guasto server con downtime 8h: 4.000 EUR (riparazione) + 
    80.000 EUR (impatto business 8h * 10.000 EUR/h)
  - Guasto switch rete (4h downtime): 1.500 EUR + 40.000 EUR
  - Breach sicurezza da patch mancante: 50.000-500.000 EUR
- Stima conservativa costo guasti senza PM: 180.000 EUR/anno
- Stima conservativa costo guasti con PM: 45.000 EUR/anno

ROI = ((180.000 - 45.000 - 36.500) / 36.500) * 100 = 270%

Per ogni euro investito nel programma PM, l'azienda risparmia 2,70 EUR
in costi di guasto evitati.
```

### Tabella Comparativa Strategie di Manutenzione

| Parametro | Reattiva | Preventiva | Predittiva |
|----------|---------|------------|------------|
| Costo relativo | 1x (base alta) | 0,4-0,6x | 0,3-0,5x |
| Pianificabilita | Nessuna | Alta | Molto alta |
| Impatto su downtime | Massimo | Ridotto 50-70% | Ridotto 70-90% |
| Rischio perdita dati | Alto | Basso | Molto basso |
| Vita utile asset | Ridotta | Estesa 20-40% | Estesa 25-50% |
| Complessita implementazione | Minima | Media | Alta |
| Competenze richieste | Base | Intermedie | Avanzate |
| Investimento iniziale | Nullo | Moderato | Significativo |
| Tempo per ROI positivo | N/A | 6-12 mesi | 12-18 mesi |
| Adatto a | Asset non critici | Tutti gli asset | Asset critici ad alto costo |

### Il Costo del Downtime: Come Calcolarlo

Per giustificare il budget di manutenzione preventiva, e essenziale quantificare il costo del downtime specifico per la propria organizzazione:

```
Formula costo downtime:

Costo_Downtime_Ora = Perdita_Ricavi + Costo_Produttivita_Persa + 
                     Costo_Recupero + Costo_Reputazionale + 
                     Costo_Penali_SLA

Calcolo dettagliato:

1. Perdita ricavi diretti:
   = Ricavi_Annui / Ore_Lavorative_Anno * %_Ricavi_Dipendenti_Da_IT
   Esempio: 5.000.000 EUR / 2.000h * 80% = 2.000 EUR/h

2. Costo produttivita persa:
   = Numero_Dipendenti_Impattati * Costo_Orario_Medio
   Esempio: 40 dipendenti * 35 EUR/h = 1.400 EUR/h

3. Costo recupero e straordinari:
   = Tecnici_Coinvolti * Costo_Orario_Straordinario
   Esempio: 3 tecnici * 75 EUR/h = 225 EUR/h

4. Costo reputazionale (difficile da quantificare):
   = Stima basata su clienti persi, recensioni negative
   Esempio stimato: 500-5.000 EUR/h per aziende B2C

5. Penali SLA contrattuali:
   = Variabile per contratto

TOTALE ESEMPIO: ~4.125 EUR/h (senza reputazionale e penali)
```

### Comunicazione al Management

Il report al management deve essere sintetico, focalizzato sui numeri e orientato alla decisione:

```
Template report trimestrale PM per il management:

EXECUTIVE SUMMARY - Manutenzione Preventiva Q[X] [Anno]

RISULTATI CHIAVE:
- Disponibilita media sistemi: 99,97% (target: 99,95%) ✓
- Guasti prevenuti dal programma PM: 4 (stima risparmio: 120.000 EUR)
- Attivita PM completate nei tempi: 94% (target: 90%) ✓
- MTBF medio server: 14.600h (trend: stabile)
- MTTR medio: 3,2h (miglioramento del 15% vs trimestre precedente)

INVESTIMENTO vs RISPARMIO:
- Costo programma PM Q[X]: 9.125 EUR
- Risparmio stimato (guasti evitati): 120.000 EUR
- ROI trimestrale: 1.215%

CRITICITA IDENTIFICATE:
- 3 dischi SSD con usura > 85%: sostituzione pianificata in MW di [data]
- Batterie UPS rack 3: runtime sceso al 72% del nominale, ordine effettuato
- Aggiornamento firmware switch core pianificato per [data]

RICHIESTE DI BUDGET:
- Sostituzione 3 SSD enterprise: 2.400 EUR
- Sostituzione batterie UPS: 1.800 EUR
TOTALE: 4.200 EUR
```

---

## Automazione della Manutenzione con Script e Ansible

L'automazione delle attivita di manutenzione preventiva e essenziale per garantire coerenza, ridurre gli errori umani e liberare il personale tecnico per attivita a maggior valore aggiunto. Ogni attivita eseguita manualmente piu di tre volte e candidata all'automazione.

### Script Bash: Health Check Giornaliero Completo

```bash
#!/bin/bash
# /usr/local/bin/daily_health_check.sh
# Esegue i controlli giornalieri di manutenzione preventiva
# Genera un report e lo invia via email
#
# Cron: 0 7 * * 1-5 /usr/local/bin/daily_health_check.sh

set -euo pipefail

REPORT_DIR="/var/log/maintenance/reports"
mkdir -p "$REPORT_DIR"

REPORT_FILE="${REPORT_DIR}/daily_$(hostname)_$(date +%Y%m%d).txt"
ALERT_LEVEL="OK"  # OK, WARNING, CRITICAL

# Funzione per aggiungere al report
log_report() {
  echo "$1" >> "$REPORT_FILE"
}

log_alert() {
  local level="$1"
  local msg="$2"
  log_report "[${level}] ${msg}"
  if [ "$level" = "CRITICAL" ]; then
    ALERT_LEVEL="CRITICAL"
  elif [ "$level" = "WARNING" ] && [ "$ALERT_LEVEL" != "CRITICAL" ]; then
    ALERT_LEVEL="WARNING"
  fi
}

# Intestazione report
log_report "======================================================"
log_report "REPORT MANUTENZIONE GIORNALIERA"
log_report "Host: $(hostname)"
log_report "Data: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
log_report "Uptime: $(uptime -p)"
log_report "======================================================"
log_report ""

# --- 1. SPAZIO DISCO ---
log_report "--- SPAZIO DISCO ---"
while IFS= read -r line; do
  usage=$(echo "$line" | awk '{print $5}' | tr -d '%')
  mount=$(echo "$line" | awk '{print $6}')
  if [ "$usage" -ge 90 ]; then
    log_alert "CRITICAL" "Disco ${mount}: ${usage}% utilizzato"
  elif [ "$usage" -ge 80 ]; then
    log_alert "WARNING" "Disco ${mount}: ${usage}% utilizzato"
  fi
  log_report "  ${mount}: ${usage}% utilizzato"
done < <(df -h --output=pcent,target -x tmpfs -x devtmpfs | tail -n +2)
log_report ""

# --- 2. SALUTE DISCHI (SMART) ---
log_report "--- SALUTE DISCHI ---"
for disk in /dev/sd? /dev/nvme?; do
  if [ -b "$disk" ]; then
    health=$(smartctl -H "$disk" 2>/dev/null | grep -i "result\|SMART Health" | head -1)
    if echo "$health" | grep -qi "FAIL\|failed"; then
      log_alert "CRITICAL" "SMART ${disk}: FAILED"
    else
      log_report "  ${disk}: OK"
    fi
  fi
done
log_report ""

# --- 3. ERRORI MEMORIA ECC ---
log_report "--- ERRORI MEMORIA ECC ---"
if [ -d /sys/devices/system/edac/mc ]; then
  for mc in /sys/devices/system/edac/mc/mc*; do
    ce=$(cat "${mc}/ce_count" 2>/dev/null || echo "N/A")
    ue=$(cat "${mc}/ue_count" 2>/dev/null || echo "N/A")
    mc_name=$(basename "$mc")
    if [ "$ue" != "N/A" ] && [ "$ue" -gt 0 ]; then
      log_alert "CRITICAL" "Memoria ${mc_name}: ${ue} errori non corretti!"
    elif [ "$ce" != "N/A" ] && [ "$ce" -gt 100 ]; then
      log_alert "WARNING" "Memoria ${mc_name}: ${ce} errori corretti (trend elevato)"
    fi
    log_report "  ${mc_name}: CE=${ce} UE=${ue}"
  done
else
  log_report "  EDAC non disponibile su questo sistema"
fi
log_report ""

# --- 4. SERVIZI CRITICI ---
log_report "--- SERVIZI CRITICI ---"
SERVICES=("sshd" "rsyslog" "cron" "smartd" "zabbix-agent")
for svc in "${SERVICES[@]}"; do
  if systemctl is-active --quiet "$svc" 2>/dev/null; then
    log_report "  ${svc}: RUNNING"
  else
    log_alert "WARNING" "Servizio ${svc}: NON ATTIVO"
  fi
done
log_report ""

# --- 5. ERRORI LOG RECENTI ---
log_report "--- ERRORI LOG (ultime 24h) ---"
err_count=$(journalctl --since "24 hours ago" --priority=err --no-pager 2>/dev/null | wc -l)
crit_count=$(journalctl --since "24 hours ago" --priority=crit --no-pager 2>/dev/null | wc -l)
if [ "$crit_count" -gt 0 ]; then
  log_alert "CRITICAL" "Trovati ${crit_count} messaggi critici nel log"
fi
if [ "$err_count" -gt 50 ]; then
  log_alert "WARNING" "Trovati ${err_count} errori nel log (soglia: 50)"
fi
log_report "  Errori: ${err_count}, Critici: ${crit_count}"
log_report ""

# --- 6. CARICO SISTEMA ---
log_report "--- CARICO SISTEMA ---"
cpu_cores=$(nproc)
load_1=$(awk '{print $1}' /proc/loadavg)
load_ratio=$(echo "$load_1 $cpu_cores" | awk '{printf "%.0f", ($1/$2)*100}')
if [ "$load_ratio" -ge 90 ]; then
  log_alert "WARNING" "Carico CPU elevato: ${load_1} su ${cpu_cores} core (${load_ratio}%)"
fi
log_report "  Load average: $(cat /proc/loadavg | awk '{print $1, $2, $3}')"
log_report "  Core CPU: ${cpu_cores} (rapporto: ${load_ratio}%)"

mem_avail=$(awk '/MemAvailable/{print $2}' /proc/meminfo)
mem_total=$(awk '/MemTotal/{print $2}' /proc/meminfo)
mem_pct=$(echo "$mem_avail $mem_total" | awk '{printf "%.0f", (1-$1/$2)*100}')
if [ "$mem_pct" -ge 90 ]; then
  log_alert "WARNING" "Memoria utilizzata: ${mem_pct}%"
fi
log_report "  Memoria utilizzata: ${mem_pct}%"
log_report ""

# --- RIEPILOGO ---
log_report "======================================================"
log_report "STATO COMPLESSIVO: ${ALERT_LEVEL}"
log_report "======================================================"

# Invio email (configurare con il proprio mail relay)
# mail -s "[${ALERT_LEVEL}] Health Check $(hostname) $(date +%Y-%m-%d)" \
#   team-it@azienda.it < "$REPORT_FILE"

echo "Report generato: $REPORT_FILE (Stato: $ALERT_LEVEL)"
```

### Script Python: Monitoraggio Trend e Analisi

```python
#!/usr/bin/env python3
"""
Analisi trend metriche di manutenzione preventiva.
Legge i dati baseline raccolti e identifica trend anomali.

Uso: python3 /usr/local/bin/trend_analysis.py --days 30
"""

import csv
import sys
import os
from datetime import datetime, timedelta
from statistics import mean, stdev
from pathlib import Path

BASELINE_DIR = "/var/log/maintenance/baseline"
ALERT_THRESHOLDS = {
    "cpu_temp": {"warning": 75, "critical": 85},
    "cpu_load_ratio": {"warning": 80, "critical": 95},
    "mem_used_pct": {"warning": 85, "critical": 95},
    "io_await_ms": {"warning": 20, "critical": 50},
}

def load_data(hostname, days=30):
    """Carica dati baseline degli ultimi N giorni."""
    records = []
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    for csv_file in Path(BASELINE_DIR).glob(f"baseline_{hostname}_*.csv"):
        with open(csv_file) as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 5:
                    try:
                        ts = datetime.fromisoformat(row[0].replace('Z', '+00:00'))
                        if ts.replace(tzinfo=None) >= cutoff:
                            records.append({
                                "timestamp": ts,
                                "cpu_temp": float(row[1]) if row[1] else None,
                                "cpu_load": float(row[2]) if row[2] else None,
                                "mem_used": float(row[3]) if row[3] else None,
                                "io_await": float(row[4]) if row[4] else None,
                            })
                    except (ValueError, IndexError):
                        continue
    
    return sorted(records, key=lambda r: r["timestamp"])

def analyze_trend(values, metric_name):
    """Analizza trend: media, deviazione standard, direzione."""
    if len(values) < 10:
        return {"status": "INSUFFICIENT_DATA", "message": "Dati insufficienti"}
    
    avg = mean(values)
    sd = stdev(values) if len(values) > 1 else 0
    
    # Dividere in prima e seconda meta per rilevare trend
    mid = len(values) // 2
    first_half_avg = mean(values[:mid])
    second_half_avg = mean(values[mid:])
    
    change_pct = ((second_half_avg - first_half_avg) / first_half_avg * 100
                  if first_half_avg > 0 else 0)
    
    trend = "STABILE"
    if change_pct > 10:
        trend = "CRESCENTE"
    elif change_pct < -10:
        trend = "DECRESCENTE"
    
    # Ultimo valore vs soglie
    last_val = values[-1]
    thresholds = ALERT_THRESHOLDS.get(metric_name, {})
    status = "OK"
    if thresholds.get("critical") and last_val >= thresholds["critical"]:
        status = "CRITICAL"
    elif thresholds.get("warning") and last_val >= thresholds["warning"]:
        status = "WARNING"
    
    return {
        "status": status,
        "average": round(avg, 2),
        "std_dev": round(sd, 2),
        "trend": trend,
        "change_pct": round(change_pct, 1),
        "last_value": round(last_val, 2),
    }

def main():
    import socket
    hostname = socket.gethostname()
    days = 30
    
    if "--days" in sys.argv:
        idx = sys.argv.index("--days")
        days = int(sys.argv[idx + 1])
    
    print(f"Analisi trend - {hostname} - ultimi {days} giorni")
    print("=" * 60)
    
    records = load_data(hostname, days)
    if not records:
        print("ERRORE: nessun dato baseline trovato.")
        print(f"Directory: {BASELINE_DIR}")
        sys.exit(1)
    
    print(f"Record analizzati: {len(records)}")
    print(f"Periodo: {records[0]['timestamp']} -> {records[-1]['timestamp']}")
    print()
    
    metrics = {
        "cpu_temp": [r["cpu_temp"] for r in records if r["cpu_temp"] is not None],
        "cpu_load_ratio": [r["cpu_load"] for r in records if r["cpu_load"] is not None],
        "mem_used_pct": [r["mem_used"] for r in records if r["mem_used"] is not None],
        "io_await_ms": [r["io_await"] for r in records if r["io_await"] is not None],
    }
    
    for name, values in metrics.items():
        result = analyze_trend(values, name)
        print(f"  {name}:")
        print(f"    Stato: {result['status']}")
        print(f"    Media: {result.get('average', 'N/A')}")
        print(f"    Dev.Std: {result.get('std_dev', 'N/A')}")
        print(f"    Trend: {result.get('trend', 'N/A')} ({result.get('change_pct', 0)}%)")
        print(f"    Ultimo valore: {result.get('last_value', 'N/A')}")
        print()

if __name__ == "__main__":
    main()
```

### Playbook Ansible: Manutenzione Preventiva Server

```yaml
# playbooks/preventive_maintenance.yml
# Esegue le attivita di manutenzione preventiva su tutti i server Linux
#
# Uso: ansible-playbook -i inventory/production preventive_maintenance.yml
# Schedulare via cron: ogni lunedi alle 07:00

---
- name: Manutenzione Preventiva - Health Check Settimanale
  hosts: all_servers
  become: true
  gather_facts: true
  vars:
    report_dir: /var/log/maintenance/ansible
    disk_warning_pct: 80
    disk_critical_pct: 90
    max_load_ratio: 80
    max_mem_pct: 85
    
  tasks:
    - name: Creare directory report
      ansible.builtin.file:
        path: "{{ report_dir }}"
        state: directory
        mode: '0755'

    - name: Controllare spazio disco
      ansible.builtin.shell: |
        df -h --output=target,pcent -x tmpfs -x devtmpfs | tail -n +2 | \
        awk '{gsub(/%/,"",$2); if ($2 >= {{ disk_warning_pct }}) print $1, $2"%"}'
      register: disk_check
      changed_when: false

    - name: Alert spazio disco
      ansible.builtin.debug:
        msg: "ATTENZIONE spazio disco su {{ inventory_hostname }}: {{ disk_check.stdout }}"
      when: disk_check.stdout | length > 0

    - name: Verificare salute SMART dischi
      ansible.builtin.shell: |
        for disk in /dev/sd? /dev/nvme?; do
          if [ -b "$disk" ]; then
            result=$(smartctl -H "$disk" 2>/dev/null | grep -i "result\|health" | head -1)
            echo "${disk}: ${result}"
          fi
        done
      register: smart_check
      changed_when: false
      ignore_errors: true

    - name: Verificare errori ECC memoria
      ansible.builtin.shell: |
        if [ -d /sys/devices/system/edac/mc ]; then
          for mc in /sys/devices/system/edac/mc/mc*; do
            ue=$(cat "${mc}/ue_count" 2>/dev/null || echo "0")
            echo "$(basename $mc): UE=${ue}"
          done
        else
          echo "EDAC non disponibile"
        fi
      register: ecc_check
      changed_when: false

    - name: Pulizia log vecchi (> 90 giorni)
      ansible.builtin.find:
        paths: 
          - /var/log
          - "{{ report_dir }}"
        patterns: "*.log.gz,*.log.[0-9]*,*.old"
        age: "90d"
        recurse: false
      register: old_logs

    - name: Rimuovere log vecchi
      ansible.builtin.file:
        path: "{{ item.path }}"
        state: absent
      loop: "{{ old_logs.files }}"
      when: old_logs.matched > 0

    - name: Pulizia pacchetti non necessari (Debian/Ubuntu)
      ansible.builtin.apt:
        autoremove: true
        autoclean: true
      when: ansible_os_family == "Debian"

    - name: Pulizia pacchetti non necessari (RHEL/CentOS)
      ansible.builtin.dnf:
        autoremove: true
      when: ansible_os_family == "RedHat"

    - name: Verificare servizi critici
      ansible.builtin.systemd:
        name: "{{ item }}"
      loop:
        - sshd
        - rsyslog
        - cron
        - smartd
      register: services_check
      ignore_errors: true

    - name: Verificare aggiornamenti sicurezza disponibili (Debian/Ubuntu)
      ansible.builtin.shell: |
        apt list --upgradable 2>/dev/null | grep -i security | wc -l
      register: security_updates
      changed_when: false
      when: ansible_os_family == "Debian"

    - name: Generare report manutenzione
      ansible.builtin.template:
        src: templates/maintenance_report.j2
        dest: "{{ report_dir }}/weekly_{{ ansible_hostname }}_{{ ansible_date_time.date }}.txt"
        mode: '0644'
```

### Playbook Ansible: Backup Configurazione Apparati di Rete

```yaml
# playbooks/network_config_backup.yml
# Backup configurazione switch e router
# Schedulare settimanalmente

---
- name: Backup Configurazione Apparati di Rete
  hosts: network_devices
  gather_facts: false
  vars:
    backup_dir: /backup/network/configs
    retention_days: 90
    
  tasks:
    - name: Creare directory backup con data
      ansible.builtin.file:
        path: "{{ backup_dir }}/{{ ansible_date_time.date }}"
        state: directory
        mode: '0750'
      delegate_to: localhost
      run_once: true

    - name: Backup configurazione Cisco IOS
      ansible.netcommon.cli_command:
        command: show running-config
      register: cisco_config
      when: ansible_network_os == 'cisco.ios.ios'

    - name: Salvare configurazione Cisco
      ansible.builtin.copy:
        content: "{{ cisco_config.stdout }}"
        dest: "{{ backup_dir }}/{{ ansible_date_time.date }}/{{ inventory_hostname }}.cfg"
      delegate_to: localhost
      when: cisco_config is defined and cisco_config.stdout is defined

    - name: Pulizia backup vecchi
      ansible.builtin.find:
        paths: "{{ backup_dir }}"
        file_type: directory
        age: "{{ retention_days }}d"
      register: old_backups
      delegate_to: localhost
      run_once: true

    - name: Rimuovere backup obsoleti
      ansible.builtin.file:
        path: "{{ item.path }}"
        state: absent
      loop: "{{ old_backups.files }}"
      delegate_to: localhost
      run_once: true
      when: old_backups.matched > 0
```

### Automazione Monitoraggio Scadenza Certificati

```bash
#!/bin/bash
# /usr/local/bin/check_certificates.sh
# Verifica scadenza certificati SSL/TLS
# Cron: 0 8 * * 1 /usr/local/bin/check_certificates.sh

HOSTS=(
  "webserver.azienda.it:443"
  "mail.azienda.it:443"
  "vpn.azienda.it:443"
  "intranet.azienda.it:443"
  "api.azienda.it:443"
)

WARNING_DAYS=60
CRITICAL_DAYS=30

echo "Verifica scadenza certificati SSL/TLS - $(date +%Y-%m-%d)"
echo "============================================================"

ALERTS=""

for host_port in "${HOSTS[@]}"; do
  host=$(echo "$host_port" | cut -d: -f1)
  port=$(echo "$host_port" | cut -d: -f2)
  
  expiry=$(echo | openssl s_client -connect "${host}:${port}" \
    -servername "$host" 2>/dev/null | \
    openssl x509 -noout -enddate 2>/dev/null | \
    cut -d= -f2)
  
  if [ -z "$expiry" ]; then
    echo "[ERRORE] ${host}:${port} - Impossibile leggere certificato"
    ALERTS="${ALERTS}ERRORE: ${host}:${port} non raggiungibile\n"
    continue
  fi
  
  expiry_epoch=$(date -d "$expiry" +%s 2>/dev/null)
  now_epoch=$(date +%s)
  days_left=$(( (expiry_epoch - now_epoch) / 86400 ))
  
  if [ "$days_left" -le 0 ]; then
    echo "[SCADUTO] ${host}:${port} - Scaduto da $((-days_left)) giorni!"
    ALERTS="${ALERTS}CRITICO: ${host}:${port} SCADUTO\n"
  elif [ "$days_left" -le "$CRITICAL_DAYS" ]; then
    echo "[CRITICO] ${host}:${port} - Scade tra ${days_left} giorni (${expiry})"
    ALERTS="${ALERTS}CRITICO: ${host}:${port} scade tra ${days_left} giorni\n"
  elif [ "$days_left" -le "$WARNING_DAYS" ]; then
    echo "[WARNING] ${host}:${port} - Scade tra ${days_left} giorni (${expiry})"
    ALERTS="${ALERTS}WARNING: ${host}:${port} scade tra ${days_left} giorni\n"
  else
    echo "[OK]      ${host}:${port} - Scade tra ${days_left} giorni (${expiry})"
  fi
done

if [ -n "$ALERTS" ]; then
  echo ""
  echo "RIEPILOGO ALERT:"
  echo -e "$ALERTS"
  # Invio notifica
  # echo -e "$ALERTS" | mail -s "Alert Certificati SSL" team-it@azienda.it
fi
```

---

## Gestione del Ciclo di Vita Firmware — Approfondimento

Il firmware e il software che opera a livello piu basso dell'hardware: BIOS/UEFI dei server, firmware dei controller RAID, firmware delle schede di rete, firmware degli switch e router, firmware degli SSD e dei dischi. Un aggiornamento firmware mal gestito puo rendere un dispositivo completamente inutilizzabile (bricking), ma trascurare gli aggiornamenti espone a vulnerabilita di sicurezza critiche e problemi di prestazioni noti e gia risolti.

### Principi di Gestione Firmware

**1. Sicurezza della Supply Chain Firmware**

Il firmware deve essere scaricato esclusivamente dai siti ufficiali del produttore. Mai da fonti terze, mirror non ufficiali o link ricevuti via email. Verificare sempre l'integrita del file scaricato tramite checksum (SHA-256 minimo) pubblicato sul sito del vendor. Il firmware enterprise moderno e firmato digitalmente dal produttore, e il dispositivo verifica la firma prima dell'installazione, rifiutando firmware non autenticati.

**2. Strategia A/B Partitioning**

I dispositivi enterprise moderni (switch, router, server BMC) supportano il dual-image firmware: due partizioni (A e B) contengono ciascuna una copia completa del firmware. L'aggiornamento viene installato sulla partizione inattiva, poi il dispositivo viene riavviato dalla nuova partizione. Se l'avvio fallisce, il dispositivo ritorna automaticamente alla partizione precedente (rollback automatico). Verificare che questa funzionalita sia attiva sui propri dispositivi.

**3. Policy di Aggiornamento per Ambiente**

```
Approccio stratificato all'aggiornamento firmware:

STAGING/TEST (settimana 1):
- Applicare il firmware su dispositivi di test o staging
- Monitorare per almeno 5 giorni lavorativi
- Eseguire test funzionali completi
- Verificare: prestazioni, stabilita, compatibilita

PRODUZIONE NON CRITICA (settimana 2-3):
- Applicare su server/dispositivi di produzione non critici
- Monitorare per almeno 5 giorni lavorativi
- Documentare qualsiasi anomalia

PRODUZIONE CRITICA (settimana 3-4):
- Applicare su sistemi critici durante MW pianificata
- Ridondanza verificata prima dell'intervento
- Piano di rollback testato
- Personale di supporto disponibile

ECCEZIONE - Firmware di sicurezza critico:
- Se il firmware corregge una vulnerabilita con CVSS >= 9.0
  e con exploit noto in circolazione:
- Timeline accelerata: staging 48h, poi produzione nella MW piu vicina
- Documentare la deroga dal processo standard
```

### Inventario Firmware e Tracking Versioni

Mantenere un registro aggiornato di tutte le versioni firmware installate e fondamentale per la gestione delle vulnerabilita e la pianificazione degli aggiornamenti:

```
Template registro firmware:

| Asset | Tipo | Componente | Versione Attuale | Ultima Disponibile | Data Ultimo Aggiornamento | Note |
|-------|------|-----------|-----------------|-------------------|--------------------------|------|
| SRV-PROD-01 | Server Dell R750 | BIOS | 2.9.1 | 2.10.3 | 2026-01-15 | Aggiornamento in MW di marzo |
| SRV-PROD-01 | Server Dell R750 | iDRAC | 7.00.00.171 | 7.00.30.00 | 2026-01-15 | -- |
| SRV-PROD-01 | Server Dell R750 | PERC H755 | 52.24.4-4903 | 52.24.8-5010 | 2025-10-20 | Verificare compatibilita |
| SW-CORE-01 | Switch Cisco C9300 | IOS-XE | 17.9.5 | 17.12.2 | 2026-02-28 | -- |
| FW-01 | Firewall FortiGate 200F | FortiOS | 7.4.3 | 7.4.5 | 2026-03-10 | -- |
| UPS-01 | APC Smart-UPS 3000 | NMC Firmware | 3.1.4 | 3.2.1 | 2025-08-15 | -- |

Revisione: trimestrale (Q1, Q2, Q3, Q4)
Responsabile: [nome tecnico referente]
```

### Script Automazione Verifica Firmware Dell

```bash
#!/bin/bash
# /usr/local/bin/check_dell_firmware.sh
# Verifica firmware Dell tramite iDRAC (Redfish API)
# Richiede: curl, jq

IDRAC_HOSTS=(
  "idrac-srv01.azienda.local"
  "idrac-srv02.azienda.local"
  "idrac-srv03.azienda.local"
)
IDRAC_USER="monitor"
# Password da variabile d'ambiente o secret manager
IDRAC_PASS="${IDRAC_MONITOR_PASSWORD}"

if [ -z "$IDRAC_PASS" ]; then
  echo "ERRORE: variabile IDRAC_MONITOR_PASSWORD non impostata"
  exit 1
fi

echo "Inventario Firmware Server Dell - $(date +%Y-%m-%d)"
echo "======================================================="

for idrac in "${IDRAC_HOSTS[@]}"; do
  echo ""
  echo "--- ${idrac} ---"
  
  # Query Redfish API per inventario firmware
  firmware_json=$(curl -sk -u "${IDRAC_USER}:${IDRAC_PASS}" \
    "https://${idrac}/redfish/v1/UpdateService/FirmwareInventory" \
    2>/dev/null)
  
  if [ $? -ne 0 ] || [ -z "$firmware_json" ]; then
    echo "  ERRORE: impossibile contattare ${idrac}"
    continue
  fi
  
  # Estrarre lista componenti firmware
  members=$(echo "$firmware_json" | jq -r '.Members[]."@odata.id"' 2>/dev/null)
  
  for member in $members; do
    detail=$(curl -sk -u "${IDRAC_USER}:${IDRAC_PASS}" \
      "https://${idrac}${member}" 2>/dev/null)
    
    name=$(echo "$detail" | jq -r '.Name // "N/A"')
    version=$(echo "$detail" | jq -r '.Version // "N/A"')
    installable=$(echo "$detail" | jq -r '.Updateable // "N/A"')
    
    echo "  ${name}: v${version} (aggiornabile: ${installable})"
  done
done
```

---

## Sistema CMMS e Gestione Ordini di Lavoro

Un CMMS (Computerized Maintenance Management System) e il sistema informativo che supporta la gestione operativa di tutte le attivita di manutenzione. Per ambienti IT di dimensioni medie e grandi, l'adozione di un CMMS e il passo che trasforma la manutenzione da un insieme di attivita ad hoc a un processo strutturato, misurabile e migliorabile.

### Funzionalita Essenziali di un CMMS per IT

Un CMMS adatto alla manutenzione di infrastrutture IT deve offrire le seguenti funzionalita minime:

1. **Registro asset**: inventario completo di server, apparati di rete, UPS, storage con anagrafica tecnica (marca, modello, serial number, data acquisto, scadenza garanzia, posizione, configurazione)
2. **Pianificazione manutenzione preventiva**: calendario di attivita ricorrenti con frequenze configurabili (giornaliera, settimanale, mensile, trimestrale, semestrale, annuale)
3. **Ordini di lavoro (Work Order)**: creazione, assegnazione, tracciamento e chiusura di ogni intervento di manutenzione, sia preventivo che correttivo
4. **Gestione ricambi**: inventario parti di ricambio, soglie di riordino, tracciamento utilizzo per asset
5. **Storico interventi**: registro completo di tutti gli interventi eseguiti su ogni asset, accessibile per analisi e troubleshooting
6. **Reportistica e KPI**: generazione automatica di report con metriche MTBF, MTTR, compliance PM, costi di manutenzione
7. **Integrazione monitoraggio**: capacita di ricevere alert dal sistema di monitoraggio (Zabbix, Nagios, PRTG) e creare automaticamente work order

### Soluzioni CMMS Open Source per IT

Per ambienti IT, diverse soluzioni CMMS open source offrono funzionalita adeguate senza costi di licenza:

```
Confronto soluzioni CMMS open source:

| Soluzione | Licenza | Punti di Forza | Limiti |
|-----------|---------|---------------|--------|
| GLPI | GPL v3 | Integrazione ITSM, plugin ricco, | Curva apprendimento |
|      |         | gestione ticket + asset + PM    | iniziale ripida |
| Snipe-IT | AGPL v3 | Asset management eccellente, | Manutenzione PM limitata |
|          |          | interfaccia moderna, API REST | rispetto a CMMS puri |
| Ralph | Apache 2 | DCIM + CMMS, datacenter focused | Comunita piu piccola |
| iTop | AGPL v3 | ITIL compliant, CMDB potente | Complessita configurazione |

Raccomandazione per PMI IT:
- GLPI con plugin manutenzione per gestione completa
- Snipe-IT per asset management + script esterni per PM scheduling
- iTop per ambienti ITIL-aligned con processi maturi
```

### Ciclo di Vita di un Ordine di Lavoro di Manutenzione

```
Flusso Work Order di manutenzione preventiva:

1. GENERAZIONE (automatica da calendario PM o da alert monitoraggio)
   → Work Order creato con: asset, attivita, checklist, priorita, deadline

2. ASSEGNAZIONE (automatica o manuale)
   → Assegnato al tecnico competente in base a skill e disponibilita

3. PIANIFICAZIONE
   → Tecnico pianifica l'intervento nella finestra di manutenzione
   → Coordina con team applicativo se necessario fermo servizio

4. ESECUZIONE
   → Tecnico esegue l'attivita seguendo la checklist
   → Registra: tempo impiegato, parti utilizzate, risultato, note

5. VERIFICA
   → Verifica post-intervento: sistema funzionante, metriche normali
   → Se problema riscontrato: riapertura o nuovo WO

6. CHIUSURA
   → Compilazione completa di tutti i campi
   → Aggiornamento registro manutenzione dell'asset
   → Dati disponibili per calcolo KPI

METRICHE DA TRACCIARE:
- % WO completati nei tempi (target: >=90%)
- Tempo medio di completamento per tipo di WO
- Backlog: WO aperti non ancora eseguiti (target: <10% del totale mensile)
- Rapporto WO preventivi vs WO correttivi (target: 80/20)
```

### Integrazione CMMS con Sistema di Monitoraggio

L'integrazione tra il sistema di monitoraggio (Zabbix, Nagios, PRTG) e il CMMS consente di creare automaticamente ordini di lavoro quando vengono rilevate condizioni che richiedono intervento:

```
Esempi di trigger automatici monitoraggio → CMMS:

| Trigger Monitoraggio | Azione CMMS |
|---------------------|-------------|
| Disco SMART: settori riallocati > 0 | WO: "Verificare salute disco [asset]" |
| SSD usura > 80% | WO: "Pianificare sostituzione SSD [asset]" |
| Temperatura CPU > soglia warning 3 volte in 24h | WO: "Verificare raffreddamento [asset]" |
| UPS: batteria status != normal | WO: "Test batteria UPS [asset]" |
| Certificato SSL: scadenza < 60 giorni | WO: "Rinnovare certificato [host]" |
| Spazio disco > 85% su 3 giorni consecutivi | WO: "Capacity planning disco [asset]" |
| Errori ECC corretti: trend crescente | WO: "Diagnostica memoria [asset]" |
| Backup fallito 2 volte consecutive | WO urgente: "Ripristinare backup [sistema]" |
```

Questa integrazione chiude il loop tra il rilevamento del problema e l'azione correttiva, garantendo che nessun alert critico venga perso o dimenticato.

---

## Best Practices

Le seguenti best practice rappresentano i principi guida per un programma di manutenzione preventiva efficace e sostenibile:

**1. Documentare tutto, sempre e in modo strutturato**

Ogni intervento di manutenzione deve essere registrato con: data, operatore, sistema coinvolto, attivita svolta, risultato, eventuali anomalie riscontrate. Utilizzare un sistema centralizzato (CMDB, wiki, ticketing) accessibile a tutto il team. La documentazione non e un onere burocratico ma uno strumento operativo: durante un'emergenza notturna, la documentazione aggiornata puo fare la differenza tra un ripristino di 30 minuti e uno di 3 ore.

**2. Automatizzare le attivita ripetitive**

Ogni attivita che viene eseguita piu di 3 volte manualmente e candidata all'automazione. Utilizzare script (PowerShell, Bash, Python), strumenti di configuration management (Ansible, Puppet, Chef), job scheduler e il sistema di monitoraggio per automatizzare controlli giornalieri, raccolta metriche, generazione report e alert. L'automazione riduce gli errori umani, garantisce consistenza e libera tempo per attivita a maggior valore aggiunto.

**3. Applicare il principio di minimo impatto**

Pianificare gli interventi in modo da minimizzare il rischio di disservizio. Eseguire le attivita ad alto rischio durante le finestre di manutenzione concordate. Testare sempre in ambiente non produttivo prima di applicare in produzione. Avere sempre un piano di rollback pronto e testato. Non eseguire mai modifiche su piu sistemi contemporaneamente: procedere un sistema alla volta e verificare prima di passare al successivo.

**4. Mantenere un inventario aggiornato e completo**

Un inventario accurato di tutti gli asset IT (server, switch, firewall, UPS, licenze, contratti) e prerequisito per una manutenzione efficace. Per ogni asset registrare: marca, modello, serial number, data acquisto, scadenza garanzia, posizione fisica, configurazione, responsabile. Aggiornare l'inventario ad ogni modifica. Revisionare completamente almeno una volta all'anno.

**5. Testare i backup regolarmente e metodicamente**

Un backup non testato non e un backup affidabile. Pianificare test di restore mensili, alternando i sistemi testati in modo da coprire l'intero ambiente in un anno. Misurare il tempo effettivo di restore e confrontarlo con l'RTO dichiarato. Verificare l'integrita dei dati ripristinati. Documentare i risultati e le eventuali azioni correttive. Il peggior momento per scoprire che i backup non funzionano e durante un'emergenza reale.

**6. Gestire le patch con un processo strutturato e disciplinato**

Le patch di sicurezza devono essere applicate tempestivamente ma in modo controllato. Definire un processo che preveda: valutazione, test in staging, approvazione, deployment in produzione, verifica post-patching. Le patch critiche di sicurezza devono avere un percorso accelerato (max 72 ore dalla pubblicazione). Documentare tutte le patch applicate e quelle deliberatamente escluse (con motivazione).

**7. Monitorare proattivamente con soglie significative**

Configurare il monitoraggio non solo per rilevare guasti conclamati ma per identificare tendenze preoccupanti. Spazio disco che cresce del 5% a settimana raggiungera il 100% in poche settimane. Temperature che aumentano gradualmente indicano un problema di raffreddamento in sviluppo. Errori ECC che crescono indicano un modulo RAM in degrado. Configurare soglie di warning (non solo critical) e revisarle periodicamente.

**8. Formare il team e condividere le conoscenze**

La manutenzione preventiva e efficace solo se tutto il team conosce le procedure e sa eseguirle. Documentare le procedure in runbook accessibili e comprensibili. Ruotare le responsabilita in modo che tutti conoscano tutti i sistemi. Organizzare sessioni periodiche di condivisione delle conoscenze. Dopo ogni incidente significativo, condurre un post-mortem costruttivo e aggiornare le procedure.

**9. Revisionare e adattare il programma regolarmente**

Il programma di manutenzione non e statico. Deve essere rivisto trimestralmente in base a: nuovi sistemi aggiunti, sistemi dismessi, problemi ricorrenti che richiedono controlli piu frequenti, attivita che non hanno mai rilevato problemi e potrebbero essere ridotte in frequenza. Utilizzare i dati di monitoraggio e la storia degli incidenti per ottimizzare il programma.

**10. Considerare la manutenzione come investimento, non come costo**

La manutenzione preventiva richiede tempo, risorse e pianificazione. Tuttavia, i costi sono prevedibili e controllabili, a differenza dei costi di un'emergenza. Comunicare regolarmente al management i risultati della manutenzione preventiva in termini di: downtime evitati, guasti prevenuti, conformita mantenuta, rischi mitigati. Questo giustifica il budget e garantisce il supporto organizzativo necessario.

---

## Troubleshooting

### Problemi Comuni nella Manutenzione Preventiva

#### Problema: Patch Windows causa errore BSOD al riavvio

**Sintomo**: dopo l'applicazione di aggiornamenti Windows, il server non si riavvia correttamente mostrando una schermata blu (BSOD).

**Diagnosi e risoluzione**:
1. Avviare in Safe Mode (F8 durante il boot o tramite iDRAC/iLO console remota)
2. Verificare il codice di errore BSOD nel log eventi (System > BugCheck)
3. Se il problema e causato da una patch specifica:
   - Safe Mode > `wusa /uninstall /kb:XXXXXXX /quiet /norestart`
   - In alternativa: DISM `/Online /Remove-Package /PackageName:Package_name`
4. Riavviare e verificare il corretto funzionamento
5. Segnalare la patch problematica al team e bloccarla in WSUS
6. Monitorare i bollettini Microsoft per una versione corretta
7. Documentare l'incidente e aggiornare la procedura di patching

**Prevenzione**: testare sempre le patch in ambiente staging prima della produzione. Mantenere un backup/snapshot recente prima del patching.

#### Problema: RAID in stato degradato dopo sostituzione disco

**Sintomo**: dopo aver sostituito un disco guasto, il RAID non inizia la ricostruzione automatica oppure la ricostruzione fallisce ripetutamente.

**Diagnosi e risoluzione**:
1. Verificare compatibilita del disco sostitutivo (stesso tipo, capacita >= originale)
2. Verificare che il disco sia riconosciuto dal controller:
   - MegaRAID: `storcli /c0 /eall /sall show`
   - HP SmartArray: `ssacli ctrl slot=0 pd all show status`
3. Se il disco e in stato "Unconfigured Good", assegnarlo manualmente:
   - `storcli /c0 /e252 /s3 add vd r5 DG=0`
4. Se la ricostruzione fallisce, verificare gli altri dischi dell'array: un secondo disco potrebbe essere in fase di degrado
5. Controllare i log del controller per errori specifici
6. Se persistono problemi, testare il disco sostitutivo in un altro slot

**Prevenzione**: mantenere sempre almeno un hot spare configurato per ogni array RAID critico. Monitorare i contatori SMART di tutti i dischi dell'array, non solo di quello guasto.

#### Problema: Snapshot VMware causa esaurimento spazio datastore

**Sintomo**: le VM su un datastore iniziano a rallentare o a bloccarsi. Lo spazio libero sul datastore e vicino allo zero.

**Diagnosi e risoluzione**:
1. Identificare immediatamente gli snapshot presenti:
   ```powershell
   Get-VM -Datastore "nome-datastore" | Get-Snapshot |
     Select VM, Name, Created, SizeGB | Sort SizeGB -Descending
   ```
2. Se lo spazio e criticamente basso (< 1%), potrebbe essere necessario spegnere alcune VM non critiche per liberare spazio
3. Rimuovere gli snapshot piu grandi e vecchi (uno alla volta, monitorando lo spazio)
4. ATTENZIONE: la rimozione di snapshot temporaneamente richiede spazio AGGIUNTIVO per il consolidamento
5. Se non c'e spazio sufficiente per il consolidamento:
   - Migrare una VM su un altro datastore con Storage vMotion
   - Aggiungere storage temporaneo al datastore (se possibile)
   - Come ultima risorsa, spegnere la VM prima di rimuovere lo snapshot

**Prevenzione**: monitorare quotidianamente la presenza di snapshot. Configurare alert per snapshot piu vecchi di 48 ore. Configurare alert per spazio datastore libero < 20%.

#### Problema: Batteria UPS segnala "Replace Battery" ma e stata sostituita recentemente

**Sintomo**: l'UPS continua a segnalare la necessita di sostituzione batteria nonostante le batterie siano state sostituite di recente.

**Diagnosi e risoluzione**:
1. Verificare che le batterie installate siano del tipo corretto (tensione e capacita)
2. Eseguire una calibrazione runtime:
   - APC: `apctest` > opzione calibrazione runtime
   - La calibrazione scarica la batteria fino a un livello basso e la ricarica completamente
   - Questo resetta i contatori interni dell'UPS
3. Se il problema persiste dopo la calibrazione:
   - Verificare le connessioni delle batterie (morsetti ben serrati)
   - Misurare la tensione di ogni batteria individualmente con un multimetro
   - Una batteria difettosa nel pacco puo causare il messaggio per tutto il gruppo
4. Verificare data di produzione delle batterie: batterie rimaste in magazzino per oltre 6 mesi senza ricarica potrebbero essere gia danneggiate

**Prevenzione**: acquistare batterie da fornitori affidabili con date di produzione recenti. Non accumulare scorte di batterie per periodi prolungati. Eseguire la calibrazione immediatamente dopo ogni sostituzione.

#### Problema: Certificato SSL/TLS scaduto causa disservizio

**Sintomo**: gli utenti ricevono errori di certificato nel browser o le applicazioni che verificano i certificati smettono di funzionare.

**Diagnosi e risoluzione**:
1. Identificare il certificato scaduto:
   ```bash
   echo | openssl s_client -connect host:443 2>/dev/null |
     openssl x509 -noout -dates -subject
   ```
2. Verificare se esiste un certificato rinnovato pronto per l'installazione
3. Installare il nuovo certificato sul web server/load balancer
4. Riavviare il servizio che utilizza il certificato
5. Verificare la corretta catena di certificazione:
   ```bash
   echo | openssl s_client -connect host:443 -showcerts 2>/dev/null |
     openssl x509 -noout -text | grep -E "Issuer|Subject|Not After"
   ```
6. Testare da diversi client per confermare la risoluzione

**Prevenzione**: monitorare la scadenza di TUTTI i certificati con il sistema di monitoraggio centralizzato. Configurare alert a 90, 60, 30 e 7 giorni dalla scadenza. Mantenere un inventario completo di tutti i certificati con date di scadenza.

#### Problema: Backup completa con successo ma il restore fallisce

**Sintomo**: i report di backup indicano completamento con successo, ma quando si tenta un restore (test o reale) i dati risultano corrotti o incompleti.

**Diagnosi e risoluzione**:
1. Verificare i log dettagliati del backup (non solo lo stato di completamento)
2. Controllare se ci sono warning nascosti (file saltati, permessi negati, file in uso)
3. Verificare l'integrita del media di backup:
   - Tape: eseguire verify dopo ogni backup
   - Disco: verificare checksum dei file di backup
4. Testare il restore su un sistema alternativo per escludere problemi dell'ambiente di destinazione
5. Verificare compatibilita versioni: il software di restore deve essere della stessa versione (o superiore) di quello di backup
6. Controllare i permessi: l'account di servizio del software di backup ha accesso a tutti i file?

**Prevenzione**: eseguire SEMPRE un test di restore dopo aver configurato un nuovo job di backup. Includere la verifica (verify/checksum) come parte integrante del job di backup. Eseguire test di restore mensili a rotazione su tutti i sistemi.

#### Problema: Switch non accetta aggiornamento firmware

**Sintomo**: il caricamento del firmware sullo switch fallisce con errore di spazio insufficiente o incompatibilita.

**Diagnosi e risoluzione**:
1. Verificare spazio disponibile sulla flash:
   ```
   dir flash:    # Cisco
   show flash    # HP/Aruba
   ```
2. Se spazio insufficiente, rimuovere firmware vecchi:
   ```
   delete flash:old-firmware.bin    # Cisco
   ```
3. Verificare compatibilita: il firmware e per il modello esatto dello switch?
4. Verificare prerequisiti: alcuni firmware richiedono una versione intermedia prima dell'upgrade
5. Verificare integrita del file scaricato (MD5/SHA checksum)
6. Se il trasferimento via TFTP fallisce, provare con SCP o USB (se supportato)

**Prevenzione**: verificare sempre la matrice di compatibilita e le release notes prima di procedere. Mantenere spazio libero sulla flash. Eseguire backup della configurazione corrente e del firmware corrente prima di aggiornare.

---

*Documento aggiornato: Marzo 2026*
*Versione: 1.0*

> Nota: questo documento deve essere revisionato trimestralmente e aggiornato in base ai cambiamenti dell'infrastruttura, alle nuove tecnologie adottate e alle lezioni apprese dagli incidenti. La manutenzione preventiva e un processo vivente che si perfeziona continuamente con l'esperienza operativa.

---

## Esercizi

1. **Lab — calendar manutenzione PMI.** Scrivi calendario daily/weekly/monthly/quarterly/yearly per organizzazione 50 utenti, 5 server fisici.
2. **Stretch — automazione checklist via Ansible.** Playbook che esegue check + record `changed=N` log.

## Auto-valutazione

1. Differenza preventiva vs predittiva.
2. Skip giustificato: come documentare?
3. Cyclical schedule: durata tipica per categoria?

## Collegamenti incrociati

- Modulo 09 — `09-procedure-operative.md`.
- Modulo 16 — `16-hardware-lifecycle-refresh.md`.

## Glossario locale

| Termine | Definizione |
|---|---|
| **Manutenzione preventiva** | Schedule pianificato. |
| **Manutenzione reattiva** | Risposta a guasto. |
| **Manutenzione predittiva** | Su segnali (smart, log). |
| **Skip giustificato** | Skip con motivazione tracciabile. |
| **Cyclical schedule** | Cadenza ricorrente. |
