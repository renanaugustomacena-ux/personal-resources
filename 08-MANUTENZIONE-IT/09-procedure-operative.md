# Procedure Operative — Guida Completa

> **Modulo 09** · **Tempo:** 60 min · **Aggiornamento:** 2026-04-27

## Idee guida

1. **Runbook executable da terzi senza guida = qualita.** Test: dai a un junior, vedi se completa.
2. **Versioning runbook in Git.** Diff visibile, history blame, review.
3. **Decision tree esplicito > prosa.** Step "if X then Y else Z".
4. **Quick reference cards per emergenza.** 1 pagina, key commands.


## Indice

1. [Panoramica](#panoramica)
2. [Standard Operating Procedures (SOP)](#standard-operating-procedures-sop)
   - [Struttura SOP Standard](#struttura-sop-standard)
   - [SOP: Creazione Utente](#sop-creazione-utente)
   - [SOP: Dismissione Utente (Offboarding)](#sop-dismissione-utente-offboarding)
   - [SOP: Configurazione Workstation](#sop-configurazione-workstation)
   - [SOP: Aggiunta Server](#sop-aggiunta-server)
   - [SOP: Riavvio Pianificato Server](#sop-riavvio-pianificato-server)
   - [SOP: Patch Management](#sop-patch-management)
   - [SOP: Backup e Verifica](#sop-backup-e-verifica)
   - [SOP: Gestione Incidente di Rete](#sop-gestione-incidente-di-rete)
   - [SOP: Cambio Password Account Servizio](#sop-cambio-password-account-servizio)
   - [SOP: Gestione Certificati](#sop-gestione-certificati)
   - [SOP: Escalation a Fornitori](#sop-escalation-a-fornitori)
3. [Runbook](#runbook)
   - [Struttura Runbook Standard](#struttura-runbook-standard)
   - [Runbook: Riavvio Servizi Critici](#runbook-riavvio-servizi-critici)
   - [Runbook: Failover Database](#runbook-failover-database)
   - [Runbook: Ripristino da Backup](#runbook-ripristino-da-backup)
   - [Runbook: Risposta Ransomware](#runbook-risposta-ransomware)
4. [Gestione Documentazione](#gestione-documentazione)
5. [Best Practices](#best-practices)
6. [Troubleshooting](#troubleshooting)
7. [Change Management — Change Enablement](#change-management--change-enablement)
   - [SOP: Change Enablement (ITIL 4)](#sop-change-enablement-itil-4)
   - [Matrice di Approvazione per Tipo di Change](#matrice-di-approvazione-per-tipo-di-change)
   - [Diagramma di Flusso — Normal Change](#diagramma-di-flusso--normal-change)
8. [Release Management](#release-management)
   - [SOP: Release Management](#sop-release-management)
   - [Checklist Go/No-Go Release](#checklist-gono-go-release)
9. [Configuration Management e CMDB](#configuration-management-e-cmdb)
   - [SOP: Gestione CMDB e Configuration Item](#sop-gestione-cmdb-e-configuration-item)
10. [Service Request Fulfillment](#service-request-fulfillment)
    - [SOP: Evasione Richieste di Servizio](#sop-evasione-richieste-di-servizio)
11. [Ricertificazione Accessi e Compliance](#ricertificazione-accessi-e-compliance)
    - [SOP: Access Review e Ricertificazione](#sop-access-review-e-ricertificazione)
12. [Decommissioning Asset IT](#decommissioning-asset-it)
    - [SOP: Dismissione e Smaltimento Asset IT](#sop-dismissione-e-smaltimento-asset-it)
13. [Capacity Planning e Performance Management](#capacity-planning-e-performance-management)
    - [SOP: Capacity Planning](#sop-capacity-planning)
14. [Knowledge Management](#knowledge-management)
    - [SOP: Gestione della Conoscenza (KCS)](#sop-gestione-della-conoscenza-kcs)
15. [Runbook Aggiuntivi](#runbook-aggiuntivi)
    - [Runbook: Major Incident Management](#runbook-major-incident-management)
    - [Runbook: DR Testing — Esercitazione Disaster Recovery](#runbook-dr-testing--esercitazione-disaster-recovery)
    - [Runbook: Emergenza Spazio Disco](#runbook-emergenza-spazio-disco)
    - [Runbook: Guasto DNS/DHCP](#runbook-guasto-dnsdhcp)
16. [Problem Management e Root Cause Analysis](#problem-management-e-root-cause-analysis)
17. [Automazione e Riduzione del Toil](#automazione-e-riduzione-del-toil)
18. [Playbook vs Runbook vs SOP — Framework Strategico](#playbook-vs-runbook-vs-sop--framework-strategico)
19. [Procedure di Compliance e Audit](#procedure-di-compliance-e-audit)

---

## Panoramica

Le procedure operative rappresentano il fondamento documentale di ogni reparto IT che aspiri all'eccellenza operativa. In un ambiente enterprise, dove decine di sistemi eterogenei devono coesistere in modo affidabile, la standardizzazione delle operazioni tramite Standard Operating Procedures (SOP) e runbook non e' un lusso organizzativo: e' una necessita' critica.

Una **SOP** e' un documento prescrittivo che descrive, passo dopo passo, come eseguire un'attivita' ricorrente in modo coerente, sicuro e ripetibile. Le SOP eliminano l'ambiguita', riducono la dipendenza dalla memoria individuale e garantiscono che ogni tecnico, indipendentemente dal livello di esperienza, esegua l'operazione con lo stesso standard qualitativo. Senza SOP formalizzate, le operazioni dipendono dal cosiddetto "tribal knowledge" — conoscenza tacita posseduta da pochi individui, che rappresenta un rischio operativo enorme quando tali individui sono assenti, cambiano ruolo o lasciano l'organizzazione.

Un **runbook** e' un documento operativo piu' tecnico e specifico, orientato alla risposta a eventi, incidenti o situazioni particolari. Mentre la SOP descrive un processo pianificato (es. creare un utente), il runbook fornisce istruzioni precise per reagire a una condizione (es. un database ha eseguito un failover inatteso, un servizio critico non risponde, un attacco ransomware e' in corso). I runbook contengono tipicamente comandi effettivi da eseguire, output attesi, criteri di escalation e tempi massimi per ciascuna fase.

La differenza fondamentale tra i due documenti e' il contesto di utilizzo:

| Caratteristica | SOP | Runbook |
|---|---|---|
| Tipo di attivita' | Pianificata, ricorrente | Reattiva o su evento |
| Livello di dettaglio tecnico | Medio-alto | Molto alto, con comandi |
| Frequenza d'uso | Regolare (giornaliera/settimanale) | Su necessita' (incidente/evento) |
| Destinatario tipico | Tutti i livelli del team | Tecnici operativi di livello 2/3 |
| Output attesi | Checklist completata | Sistema ripristinato/stabilizzato |

Entrambi i tipi di documenti condividono alcuni principi essenziali:

- **Accuratezza**: ogni passo deve corrispondere alla realta' operativa attuale del sistema.
- **Completezza**: non devono essere omessi passaggi ritenuti "ovvi" — cio' che e' ovvio per un tecnico senior puo' essere ignoto a un junior.
- **Versionamento**: ogni modifica deve essere tracciata con numero di versione, data e autore.
- **Validazione**: le procedure devono essere testate periodicamente per verificarne la correttezza.
- **Accessibilita'**: devono essere facilmente reperibili da tutto il team, anche in situazioni di emergenza.

Questa guida fornisce template completi e procedure reali, pronti per essere adattati e implementati in un ambiente enterprise. Ogni procedura e' strutturata per essere immediatamente operativa.

---

## Standard Operating Procedures (SOP)

### Struttura SOP Standard

Ogni SOP deve rispettare il seguente template standardizzato. L'adozione di una struttura uniforme facilita la consultazione rapida e garantisce che nessun elemento critico venga omesso.

```
============================================================
STANDARD OPERATING PROCEDURE
============================================================

Codice:          SOP-[AREA]-[NUMERO]
Titolo:          [Titolo descrittivo della procedura]
Versione:        [X.Y]
Data creazione:  [GG/MM/AAAA]
Ultima modifica: [GG/MM/AAAA]
Autore:          [Nome e cognome]
Owner:           [Responsabile della procedura]
Approvato da:    [Nome, ruolo, data approvazione]
Classificazione: [Interna / Riservata / Pubblica]
Prossima revisione: [GG/MM/AAAA]

------------------------------------------------------------
1. SCOPO
------------------------------------------------------------
Descrizione sintetica dell'obiettivo della procedura e del
risultato atteso al termine dell'esecuzione.

------------------------------------------------------------
2. AMBITO DI APPLICAZIONE
------------------------------------------------------------
Sistemi, servizi o ambienti a cui si applica questa procedura.
Eventuali esclusioni esplicite.

------------------------------------------------------------
3. PREREQUISITI
------------------------------------------------------------
- Accessi necessari (account, permessi, VPN)
- Strumenti richiesti (software, console, chiavi)
- Approvazioni preliminari (change request, autorizzazione)
- Documentazione di riferimento

------------------------------------------------------------
4. DEFINIZIONI E ACRONIMI
------------------------------------------------------------
Glossario dei termini tecnici utilizzati nella procedura.

------------------------------------------------------------
5. RESPONSABILITA'
------------------------------------------------------------
Ruolo             | Responsabilita'
------------------+----------------------------------------
[Ruolo 1]         | [Descrizione responsabilita']
[Ruolo 2]         | [Descrizione responsabilita']

------------------------------------------------------------
6. PROCEDURA
------------------------------------------------------------
Passo | Azione                    | Responsabile | Note
------+---------------------------+--------------+--------
6.1   | [Descrizione azione]      | [Ruolo]      | [Note]
6.2   | [Descrizione azione]      | [Ruolo]      | [Note]
...

------------------------------------------------------------
7. VERIFICHE POST-ESECUZIONE
------------------------------------------------------------
Checklist di controllo per confermare la corretta esecuzione.

------------------------------------------------------------
8. ROLLBACK
------------------------------------------------------------
Procedura di annullamento in caso di errore o risultato
inatteso. Deve essere eseguibile senza ulteriori approvazioni
in situazioni di emergenza.

------------------------------------------------------------
9. RIFERIMENTI
------------------------------------------------------------
Documenti correlati, policy, standard di riferimento.

------------------------------------------------------------
10. STORICO REVISIONI
------------------------------------------------------------
Versione | Data       | Autore    | Descrizione modifica
---------+------------+-----------+-------------------------
1.0      | GG/MM/AAAA | [Nome]   | Creazione iniziale
1.1      | GG/MM/AAAA | [Nome]   | [Modifica]
```

---

### SOP: Creazione Utente

```
============================================================
STANDARD OPERATING PROCEDURE
============================================================

Codice:          SOP-IAM-001
Titolo:          Creazione Account Utente e Provisioning Risorse
Versione:        2.3
Data creazione:  15/01/2024
Ultima modifica: 10/03/2026
Autore:          [Amministratore di Sistema]
Owner:           Responsabile IT Operations
Approvato da:    IT Manager — 12/03/2026
Classificazione: Interna
Prossima revisione: 10/03/2027
```

**1. Scopo**

Definire la procedura completa per la creazione di un nuovo account utente nell'infrastruttura aziendale, comprensiva di provisioning della casella di posta, assegnazione a gruppi, distribuzione software e consegna dell'equipaggiamento.

**2. Ambito di applicazione**

Si applica a tutti i nuovi dipendenti, collaboratori esterni e consulenti che necessitano di accesso ai sistemi IT aziendali. Esclusi gli account di servizio (fare riferimento a SOP-IAM-005) e gli account amministrativi privilegiati (fare riferimento a SOP-IAM-003).

**3. Prerequisiti**

- Ricezione del modulo di richiesta approvato da HR (ticket ITSM con allegato modulo HR-NEW-001)
- Accesso alla console Active Directory Users and Computers (ADUC) o al centro di amministrazione AD
- Accesso alla console di amministrazione Exchange / Microsoft 365 Admin Center
- Accesso al portale di gestione software (SCCM / Intune / altro MDM)
- Accesso al sistema di asset management per assegnazione dispositivi
- Template di comunicazione credenziali (email HR, busta sigillata)

**4. Procedura**

**Passo 1 — Verifica richiesta e dati anagrafici**

Controllare che il ticket ITSM contenga tutte le informazioni necessarie:

- Nome e cognome completo
- Data di inizio rapporto
- Reparto/Business Unit di appartenenza
- Manager diretto (per approvazioni e catena gerarchica)
- Ruolo/Profilo (determina i gruppi e il software da assegnare)
- Sede di lavoro
- Eventuale necessita' di accesso VPN o remoto
- Eventuale necessita' di dispositivo mobile aziendale

Se mancano informazioni, rispedire il ticket a HR con richiesta di integrazione. Non procedere con dati incompleti.

**Passo 2 — Creazione account Active Directory**

```powershell
# Generare lo username secondo la naming convention aziendale
# Formato: prima lettera nome + cognome (es. mrossi per Mario Rossi)
# In caso di omonimia: prima lettera nome + prima lettera secondo nome + cognome

$NuovoUtente = @{
    Name              = "Mario Rossi"
    GivenName         = "Mario"
    Surname           = "Rossi"
    SamAccountName    = "mrossi"
    UserPrincipalName = "mario.rossi@azienda.local"
    DisplayName       = "Rossi, Mario"
    Description       = "Reparto Commerciale — Assunto 01/04/2026"
    Office            = "Milano — Sede Centrale"
    Department        = "Commerciale"
    Title             = "Account Manager"
    Manager           = "CN=Luigi Bianchi,OU=Commerciale,OU=Utenti,DC=azienda,DC=local"
    Path              = "OU=Commerciale,OU=Utenti,DC=azienda,DC=local"
    AccountPassword   = (ConvertTo-SecureString "P@ssw0rd_T3mp!" -AsPlainText -Force)
    ChangePasswordAtLogon = $true
    Enabled           = $true
}

New-ADUser @NuovoUtente
```

Verificare la corretta creazione:

```powershell
Get-ADUser -Identity "mrossi" -Properties *
```

**Passo 3 — Assegnazione ai gruppi di sicurezza**

Basandosi sul profilo ruolo, assegnare l'utente ai gruppi appropriati:

```powershell
# Gruppi standard per tutti i dipendenti
Add-ADGroupMember -Identity "GRP-AllDipendenti" -Members "mrossi"
Add-ADGroupMember -Identity "GRP-WiFi-Corporate" -Members "mrossi"
Add-ADGroupMember -Identity "GRP-Intranet-Access" -Members "mrossi"

# Gruppi specifici per il reparto Commerciale
Add-ADGroupMember -Identity "GRP-Commerciale" -Members "mrossi"
Add-ADGroupMember -Identity "GRP-CRM-Users" -Members "mrossi"
Add-ADGroupMember -Identity "GRP-ShareDrive-Commerciale" -Members "mrossi"

# Eventuale VPN
Add-ADGroupMember -Identity "GRP-VPN-Users" -Members "mrossi"
```

**Passo 4 — Creazione casella di posta**

Per ambienti Exchange On-Premises:

```powershell
Enable-Mailbox -Identity "mrossi" -Database "DB-Mailbox-01"
Set-Mailbox -Identity "mrossi" -MaxSendSize 25MB -MaxReceiveSize 35MB
Set-Mailbox -Identity "mrossi" -IssueWarningQuota 4.5GB -ProhibitSendQuota 4.75GB -ProhibitSendReceiveQuota 5GB
```

Per ambienti Microsoft 365: assegnare la licenza appropriata (es. Microsoft 365 Business Standard) tramite il portale admin o PowerShell:

```powershell
Set-MsolUserLicense -UserPrincipalName "mario.rossi@azienda.com" -AddLicenses "azienda:O365_BUSINESS_PREMIUM"
```

**Passo 5 — Distribuzione software**

Aggiungere l'utente o il dispositivo assegnato alla collection SCCM / gruppo Intune appropriato per il deployment automatico del software di profilo:

- Microsoft Office (se non incluso nella licenza cloud)
- Client VPN aziendale
- Software specifico di reparto (CRM, ERP, CAD, ecc.)
- Agente antivirus/EDR (se non gia' presente nell'immagine base)
- Strumenti di collaborazione (Teams, Slack, ecc.)

**Passo 6 — Assegnazione equipaggiamento**

1. Selezionare un dispositivo disponibile dall'inventario asset (stato: "Disponibile — Pronto").
2. Aggiornare il record nel CMDB: assegnare l'asset all'utente, cambiare stato in "In Uso".
3. Verificare che la workstation sia stata configurata secondo SOP-WKS-001.
4. Preparare la busta con credenziali temporanee e istruzioni primo accesso.
5. Coordinare la consegna con HR e il manager del nuovo assunto.

**Passo 7 — Documentazione e chiusura**

1. Aggiornare il ticket ITSM con tutti i dettagli delle operazioni eseguite.
2. Registrare nel CMDB la relazione utente-dispositivo-licenze.
3. Inviare notifica a HR e al manager confermando che il provisioning e' completato.
4. Allegare al ticket la checklist di verifica compilata.

**5. Checklist di verifica**

```
[ ] Account AD creato e abilitato
[ ] UPN e email corretti
[ ] Gruppi di sicurezza assegnati (elencare)
[ ] Casella di posta attiva e funzionante
[ ] Invio/ricezione email testato
[ ] Software deployato correttamente
[ ] Accesso alle share di rete verificato
[ ] VPN funzionante (se applicabile)
[ ] Dispositivo assegnato e registrato nel CMDB
[ ] Credenziali consegnate in modo sicuro
[ ] Ticket ITSM aggiornato e chiuso
```

**6. Rollback**

In caso di annullamento (es. il candidato rifiuta l'offerta prima della data di inizio):

```powershell
Disable-ADAccount -Identity "mrossi"
Remove-ADGroupMember -Identity "GRP-AllDipendenti" -Members "mrossi" -Confirm:$false
# Rimuovere da tutti i gruppi
Get-ADUser "mrossi" -Properties MemberOf | Select-Object -ExpandProperty MemberOf |
    ForEach-Object { Remove-ADGroupMember $_ -Members "mrossi" -Confirm:$false }
# Disabilitare la mailbox
Disable-Mailbox -Identity "mrossi" -Confirm:$false
# Riportare il dispositivo allo stato "Disponibile" nel CMDB
```

---

### SOP: Dismissione Utente (Offboarding)

```
============================================================
Codice:          SOP-IAM-002
Titolo:          Dismissione Account Utente e Deprovisioning
Versione:        2.1
Owner:           Responsabile IT Operations
Classificazione: Riservata
============================================================
```

**1. Scopo**

Garantire la revoca completa, sicura e tracciabile di tutti gli accessi IT di un dipendente/collaboratore cessato, nel rispetto delle normative sulla protezione dei dati e delle policy aziendali di data retention.

**2. Procedura**

**Passo 1 — Ricezione e validazione richiesta**

HR invia il ticket di offboarding con almeno 5 giorni lavorativi di anticipo (salvo licenziamento immediato). Il ticket deve contenere:

- Data effettiva di cessazione
- Tipologia di cessazione (dimissioni, licenziamento, scadenza contratto, trasferimento)
- Indicazione se e' richiesto il mantenimento temporaneo della casella di posta
- Manager che ereditera' eventuali deleghe o dati
- Conferma dell'avvenuta restituzione dei dispositivi (o data prevista)

**Passo 2 — Disabilitazione account (giorno D, entro le ore 18:00)**

```powershell
# Disabilitare immediatamente l'account
Disable-ADAccount -Identity "mrossi"

# Reimpostare la password con una stringa casuale di 32 caratteri
$NuovaPassword = -join ((65..90) + (97..122) + (48..57) + (33..47) |
    Get-Random -Count 32 | ForEach-Object {[char]$_})
Set-ADAccountPassword -Identity "mrossi" -NewPassword (
    ConvertTo-SecureString $NuovaPassword -AsPlainText -Force) -Reset

# Rimuovere la descrizione e impostare la data di cessazione
Set-ADUser -Identity "mrossi" -Description "CESSATO $(Get-Date -Format 'yyyy-MM-dd') — Ticket INC-12345"

# Nascondere dalla GAL (Global Address List)
Set-ADUser -Identity "mrossi" -Replace @{msExchHideFromAddressLists=$true}
```

**Passo 3 — Rimozione da tutti i gruppi**

```powershell
$Utente = Get-ADUser "mrossi" -Properties MemberOf
$Utente.MemberOf | ForEach-Object {
    Remove-ADGroupMember -Identity $_ -Members "mrossi" -Confirm:$false
    Write-Output "Rimosso da: $_"
}
# Conservare il log dei gruppi di appartenenza nel ticket prima della rimozione
```

IMPORTANTE: prima di rimuovere i gruppi, documentare nel ticket l'elenco completo delle appartenenze. Questo dato e' essenziale in caso di contestazioni o necessita' di ripristino temporaneo.

**Passo 4 — Gestione casella di posta**

Opzione A — Conversione a shared mailbox (per mantenimento temporaneo):

```powershell
# Exchange On-Premises
Set-Mailbox -Identity "mrossi" -Type Shared
Add-MailboxPermission -Identity "mrossi" -User "manager@azienda.local" -AccessRights FullAccess -AutoMapping $true

# Microsoft 365
Set-Mailbox -Identity "mario.rossi@azienda.com" -Type Shared
# Rimuovere la licenza per risparmiare costi (la shared mailbox non richiede licenza fino a 50GB)
```

Opzione B — Esportazione e archiviazione (per cessazione definitiva):

```powershell
# Esportare la mailbox in PST
New-MailboxExportRequest -Mailbox "mrossi" -FilePath "\\fileserver\archive\ex-dipendenti\mrossi_$(Get-Date -Format 'yyyyMMdd').pst"
# Attendere il completamento dell'export
Get-MailboxExportRequest | Where-Object {$_.Mailbox -eq "mrossi"} | Get-MailboxExportRequestStatistics
```

Configurare un messaggio di risposta automatica:

```powershell
Set-MailboxAutoReplyConfiguration -Identity "mrossi" -AutoReplyState Enabled -InternalMessage "L'utente non e' piu' raggiungibile a questo indirizzo. Per assistenza contattare reparto.commerciale@azienda.com" -ExternalMessage "This mailbox is no longer active. Please contact info@azienda.com"
```

**Passo 5 — Recupero e ricondizionamento equipaggiamento**

1. Verificare la restituzione fisica di: laptop/desktop, monitor, tastiera, mouse, cuffie, telefono aziendale, badge, token MFA fisici, chiavi ufficio.
2. Aggiornare lo stato nel CMDB da "In Uso" a "Da Ricondizionare".
3. Eseguire il wipe del dispositivo o reimmagine secondo SOP-WKS-001.
4. Verificare la rimozione di dati personali dal dispositivo mobile (MDM wipe).

**Passo 6 — Recupero licenze**

1. Rimuovere le licenze Microsoft 365 / Office 365 dall'account.
2. Revocare le licenze software nominali (Adobe Creative Cloud, Salesforce, ecc.).
3. Disattivare token VPN e revocare certificati client personali.
4. Aggiornare il registro licenze nel CMDB.

**Passo 7 — Data retention e archiviazione**

1. I dati della home directory dell'utente vengono spostati nella cartella di archivio: `\\fileserver\archive\ex-dipendenti\mrossi\`.
2. Il periodo di conservazione standard e' di 12 mesi, salvo diversa indicazione da parte dell'ufficio legale.
3. Applicare un retention tag con data di scadenza alla cartella archiviata.
4. La mailbox archiviata (PST o shared) segue la stessa policy di retention.

**Passo 8 — Spostamento account in OU apposita (giorno D+1)**

```powershell
Move-ADObject -Identity "CN=Mario Rossi,OU=Commerciale,OU=Utenti,DC=azienda,DC=local" `
    -TargetPath "OU=Account-Cessati,OU=Utenti,DC=azienda,DC=local"
```

**Passo 9 — Eliminazione definitiva account (giorno D+90)**

Dopo 90 giorni dalla cessazione, e previa verifica che non vi siano contenziosi o necessita' di accesso ai dati:

```powershell
Remove-ADUser -Identity "mrossi" -Confirm:$false
```

**Checklist di verifica offboarding**

```
[ ] Account AD disabilitato
[ ] Password reimpostata con valore casuale
[ ] Nascosto dalla GAL
[ ] Rimosso da tutti i gruppi (elenco documentato nel ticket)
[ ] Casella di posta convertita/archiviata
[ ] Risposta automatica configurata
[ ] Dispositivi restituiti e inventariati
[ ] Wipe/reimmagine dispositivi eseguito
[ ] Licenze software revocate
[ ] Token MFA/VPN revocati
[ ] Certificati personali revocati
[ ] Dati home directory archiviati
[ ] CMDB aggiornato
[ ] Account spostato in OU cessati
[ ] Ticket ITSM completato con documentazione completa
```

---

### SOP: Configurazione Workstation

```
============================================================
Codice:          SOP-WKS-001
Titolo:          Configurazione e Deployment Workstation
Versione:        3.0
Owner:           Responsabile Endpoint Management
Classificazione: Interna
============================================================
```

**1. Procedura**

**Passo 1 — Preparazione hardware**

1. Disimballare il dispositivo e verificare la conformita' con l'ordine di acquisto (modello, configurazione RAM/SSD, accessori).
2. Ispezionare visivamente per danni da trasporto.
3. Registrare il serial number nel CMDB (stato: "In Preparazione").
4. Applicare l'etichetta patrimoniale aziendale (asset tag).
5. Collegare il dispositivo alla rete di staging (VLAN isolata per il deployment).

**Passo 2 — Deployment sistema operativo**

Metodo A — Windows Deployment Services (WDS) / MDT:

1. Avviare il dispositivo tramite PXE boot (F12 all'avvio).
2. Selezionare la task sequence appropriata (es. "WIN11-ENT-STD-2026").
3. Inserire il nome computer secondo la naming convention: `[SEDE]-[TIPO]-[NUMERO]` (es. `MI-LT-0451`).
4. La task sequence esegue automaticamente: partitioning, installazione OS, driver injection, domain join, installazione software base.
5. Durata stimata: 45-90 minuti.

Metodo B — Microsoft Autopilot (per dispositivi cloud-managed):

1. Registrare l'hardware hash nel tenant Autopilot.
2. Assegnare il profilo di deployment appropriato.
3. Alla prima accensione, l'utente finale segue il wizard OOBE guidato.
4. Intune applica automaticamente le configurazioni e il software.

Metodo C — Installazione manuale (casi eccezionali, previa approvazione):

1. Installare Windows 11 Enterprise da supporto USB certificato.
2. Applicare le impostazioni regionali e linguistiche standard (it-IT, layout tastiera italiano).
3. Eseguire il domain join manuale.
4. Installare manualmente i driver dal sito del produttore o dal repository aziendale.

**Passo 3 — Domain join e posizionamento OU**

```powershell
# Se non eseguito automaticamente dalla task sequence
Add-Computer -DomainName "azienda.local" -OUPath "OU=Workstation,OU=Milano,OU=Computer,DC=azienda,DC=local" -Credential (Get-Credential) -Restart
```

Verificare che le Group Policy vengano applicate correttamente:

```cmd
gpupdate /force
gpresult /r
```

**Passo 4 — Installazione software**

Software base installato automaticamente tramite task sequence o policy:

- Microsoft Office (versione aziendale corrente)
- Client antivirus/EDR (CrowdStrike, Defender for Endpoint, Sophos, ecc.)
- Client VPN
- 7-Zip
- Adobe Acrobat Reader
- Browser aggiuntivo (Chrome/Firefox con profilo gestito)
- Agente di monitoraggio (SCCM client, Intune agent, Zabbix agent)
- Client di backup endpoint (se previsto)

Software specifico di reparto: installato in base al profilo dell'utente assegnato.

**Passo 5 — Applicazione security baseline**

Verificare l'applicazione delle seguenti configurazioni di sicurezza (tramite GPO o Intune compliance policy):

```
[ ] BitLocker attivo su unita' C: (chiave di recovery esportata in AD)
[ ] Windows Firewall attivo su tutti i profili
[ ] Windows Update configurato per WSUS/WUfB
[ ] UAC attivo e configurato al livello standard
[ ] Esecuzione script PowerShell limitata (RemoteSigned)
[ ] Protocolli legacy disabilitati (SMBv1, TLS 1.0/1.1)
[ ] Account Administrator locale disabilitato o gestito da LAPS
[ ] Screen lock configurato a 10 minuti di inattivita'
[ ] USB storage controllato (blocco o solo lettura, in base alla policy)
```

**Passo 6 — Assegnazione all'utente e documentazione**

1. Aggiornare il CMDB: associare il dispositivo all'utente, cambiare stato in "In Uso".
2. Stampare il foglio di consegna con: asset tag, serial number, modello, software installato, data consegna.
3. Far firmare all'utente il modulo di presa in carico.
4. Archiviare il modulo firmato (scansione nel ticket ITSM).

---

### SOP: Aggiunta Server

```
============================================================
Codice:          SOP-SRV-001
Titolo:          Provisioning e Configurazione Nuovo Server
Versione:        2.5
Owner:           Responsabile Infrastruttura
Classificazione: Riservata
============================================================
```

**1. Procedura**

**Passo 1 — Provisioning hardware / VM**

Per server fisico:
1. Installare il server nel rack designato (verificare potenza elettrica, raffreddamento, connettivita' di rete disponibili).
2. Collegare alimentazione ridondante (PSU A su circuito A, PSU B su circuito B).
3. Collegare le interfacce di rete secondo lo schema di cablaggio (management, production, backup/heartbeat).
4. Configurare la management interface (iLO, iDRAC, IPMI) con IP statico sulla VLAN di management.
5. Aggiornare il firmware all'ultima versione stabile.

Per macchina virtuale:
1. Approvare la richiesta risorse (CPU, RAM, storage) con il capacity planning.
2. Creare la VM sull'hypervisor designato (VMware vSphere, Hyper-V, Proxmox):

```powershell
# Esempio Hyper-V
New-VM -Name "SRV-APP-03" -MemoryStartupBytes 8GB -Generation 2 `
    -NewVHDPath "D:\VMs\SRV-APP-03\SRV-APP-03.vhdx" -NewVHDSizeBytes 120GB `
    -SwitchName "vSwitch-Production"
Set-VM -Name "SRV-APP-03" -ProcessorCount 4 -DynamicMemory -MemoryMinimumBytes 4GB -MemoryMaximumBytes 16GB
```

**Passo 2 — Installazione e hardening sistema operativo**

1. Installare il sistema operativo dalla ISO ufficiale (Windows Server 2022 / RHEL 9 / Ubuntu 22.04 LTS).
2. Applicare tutte le patch di sicurezza disponibili prima di qualsiasi altra configurazione.
3. Configurare il hostname secondo la naming convention: `[SEDE]-[RUOLO]-[NUMERO]` (es. `MI-SQL-02`).
4. Configurare IP statico, DNS, gateway secondo lo schema di rete.
5. Applicare le configurazioni di hardening:

Per Windows Server:

```powershell
# Disabilitare servizi non necessari
Set-Service -Name "Spooler" -StartupType Disabled   # se non e' un print server
Set-Service -Name "RemoteRegistry" -StartupType Disabled

# Configurare il firewall — abilitare solo le porte necessarie al ruolo
Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled True

# Abilitare auditing avanzato
auditpol /set /category:"Logon/Logoff" /success:enable /failure:enable
auditpol /set /category:"Account Logon" /success:enable /failure:enable
auditpol /set /category:"Object Access" /success:enable /failure:enable

# Configurare NTP
w32tm /config /manualpeerlist:"ntp.azienda.local" /syncfromflags:manual /reliable:yes /update
```

Per Linux:

```bash
# Aggiornare tutti i pacchetti
dnf update -y    # RHEL/CentOS
apt update && apt upgrade -y    # Ubuntu/Debian

# Disabilitare root login via SSH
sed -i 's/^PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/^#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl restart sshd

# Configurare il firewall
firewall-cmd --permanent --add-service=ssh
firewall-cmd --permanent --remove-service=dhcpv6-client
firewall-cmd --reload

# Configurare chronyd per NTP
echo "server ntp.azienda.local iburst" > /etc/chrony.conf
systemctl restart chronyd
```

**Passo 3 — Domain join e posizionamento OU**

```powershell
# Windows
Add-Computer -DomainName "azienda.local" -OUPath "OU=Server,OU=Milano,DC=azienda,DC=local" -Credential (Get-Credential) -Restart
```

```bash
# Linux (con SSSD e realmd)
realm join azienda.local --user=admin-domjoin
```

**Passo 4 — Installazione ruolo e configurazione specifica**

Installare i ruoli necessari in base alla funzione del server (file server, application server, database server, web server, ecc.). Fare riferimento alla SOP specifica del ruolo.

**Passo 5 — Sicurezza**

1. Installare e configurare l'agente antivirus/EDR con le esclusioni appropriate al ruolo.
2. Configurare le regole firewall specifiche per il ruolo del server.
3. Verificare le policy di audit applicate tramite GPO o configurazione locale.
4. Configurare la log collection verso il SIEM aziendale.

**Passo 6 — Monitoraggio**

```bash
# Installare l'agente Zabbix (esempio Linux)
dnf install zabbix-agent2 -y
sed -i "s/^Server=.*/Server=zabbix.azienda.local/" /etc/zabbix/zabbix_agent2.conf
sed -i "s/^Hostname=.*/Hostname=MI-SQL-02/" /etc/zabbix/zabbix_agent2.conf
systemctl enable --now zabbix-agent2
```

Verificare che il server appaia nel sistema di monitoraggio e che tutti i check di base siano verdi (CPU, RAM, disco, rete, servizi specifici).

**Passo 7 — Backup**

1. Installare l'agente di backup (Veeam Agent, Commvault, Bacula, ecc.).
2. Configurare la policy di backup appropriata al ruolo del server.
3. Eseguire un primo backup completo e verificarne la correttezza.
4. Configurare le notifiche di successo/fallimento.

**Passo 8 — Documentazione e CMDB**

1. Creare il record nel CMDB con tutti i dettagli: hostname, IP, OS, ruolo, responsabile, data installazione, hardware/VM specs.
2. Aggiornare il diagramma di rete se il server introduce nuovi flussi.
3. Documentare nel wiki/knowledge base eventuali configurazioni specifiche.
4. Chiudere il change request con documentazione completa.

---

### SOP: Riavvio Pianificato Server

```
============================================================
Codice:          SOP-SRV-003
Titolo:          Riavvio Pianificato Server
Versione:        1.4
Owner:           Responsabile IT Operations
Classificazione: Interna
============================================================
```

**1. Procedura**

**Passo 1 — Verifiche pre-riavvio (T-24 ore)**

1. Controllare che il riavvio sia stato approvato nel calendario dei change (change calendar).
2. Verificare che non ci siano altre maintenance window in conflitto.
3. Controllare lo stato attuale del server: carico CPU, memoria, processi attivi, job schedulati.
4. Identificare tutti i servizi e le applicazioni in esecuzione sul server.
5. Verificare lo stato dell'ultimo backup: deve essere completato con successo nelle ultime 24 ore.

**Passo 2 — Notifica agli stakeholder (T-4 ore minimo)**

Inviare comunicazione via email e sul canale operativo (Teams/Slack) contenente:

```
Oggetto: [MANUTENZIONE PIANIFICATA] Riavvio server MI-APP-01 — DD/MM/AAAA HH:MM

Gentili colleghi,

si comunica che il server MI-APP-01 sara' riavviato per manutenzione
programmata nella seguente finestra temporale:

  Data: DD/MM/AAAA
  Ora inizio: HH:MM
  Durata stimata: 15 minuti
  Servizi impattati: [elenco servizi]

Durante il riavvio, i seguenti servizi non saranno disponibili:
  - [Servizio 1]
  - [Servizio 2]

Per urgenze, contattare il team IT Operations: [contatto]
```

**Passo 3 — Spegnimento grazioso dei servizi (T-0)**

```powershell
# Verificare che non ci siano utenti connessi attivamente
query user /server:MI-APP-01

# Fermare i servizi applicativi in ordine inverso di dipendenza
Stop-Service -Name "AppService-Frontend" -Force
Stop-Service -Name "AppService-Backend" -Force
Stop-Service -Name "AppService-Worker" -Force

# Per SQL Server: verificare che non ci siano transazioni attive
Invoke-Sqlcmd -ServerInstance "MI-SQL-01" -Query "SELECT * FROM sys.dm_exec_requests WHERE status = 'running'"
# Attendere il completamento o terminare le query di lunga durata
Stop-Service -Name "MSSQLSERVER"
```

**Passo 4 — Esecuzione riavvio**

```powershell
Restart-Computer -ComputerName "MI-APP-01" -Force -Wait -Timeout 600
```

```bash
# Linux
sudo shutdown -r now "Riavvio pianificato — Maintenance INC-56789"
```

**Passo 5 — Verifiche post-riavvio**

```powershell
# Verificare uptime (deve mostrare pochi minuti)
(Get-CimInstance Win32_OperatingSystem).LastBootUpTime

# Verificare che tutti i servizi critici siano in esecuzione
Get-Service -Name "MSSQLSERVER","AppService-Frontend","AppService-Backend" |
    Select-Object Name, Status, StartType

# Controllare il log eventi per errori al boot
Get-WinEvent -LogName System -MaxEvents 50 | Where-Object {$_.LevelDisplayName -eq "Error"}

# Verificare la connettivita' di rete
Test-NetConnection -ComputerName "MI-APP-01" -Port 443
Test-NetConnection -ComputerName "MI-APP-01" -Port 1433
```

**Passo 6 — Notifica di completamento**

Inviare comunicazione confermando il completamento con successo o, in caso di problemi, informare sulla situazione e le azioni correttive intraprese.

---

### SOP: Patch Management

```
============================================================
Codice:          SOP-SEC-001
Titolo:          Gestione Ciclo Mensile di Patching
Versione:        3.2
Owner:           Responsabile Sicurezza IT
Classificazione: Interna
============================================================
```

**1. Procedura — Ciclo mensile**

**Settimana 1 — Valutazione patch (Patch Tuesday + 1-2 giorni)**

1. Scaricare l'elenco delle patch rilasciate (Microsoft Patch Tuesday, bollettini vendor Linux, aggiornamenti firmware).
2. Classificare ciascuna patch per criticita' (Critical, Important, Moderate, Low) e per ambito (OS, applicativo, firmware).
3. Identificare le patch che risolvono vulnerabilita' attivamente sfruttate (zero-day) — queste richiedono fast-track.
4. Compilare il report di valutazione patch mensile con la raccomandazione di installazione per ciascuna.
5. Presentare il report al Change Advisory Board (CAB) per approvazione.

**Settimana 2 — Deployment in ambiente di test**

1. Applicare le patch approvate ai server e alle workstation dell'ambiente di test/staging.
2. Eseguire i test di regressione sulle applicazioni critiche.
3. Monitorare per 48-72 ore la stabilita' dei sistemi patchati.
4. Documentare eventuali incompatibilita' o problemi riscontrati.
5. Se vengono riscontrati problemi, valutare con il CAB se procedere, ritardare o escludere la patch problematica.

**Settimana 3 — Deployment pilota**

1. Applicare le patch a un gruppo pilota di workstation di produzione (10-15% del parco) e a 1-2 server non critici.
2. Monitorare per 48 ore.
3. Raccogliere feedback dagli utenti pilota.
4. In caso di assenza di problemi, approvare il deployment di massa.

**Settimana 4 — Deployment produzione**

1. Applicare le patch a tutte le workstation durante la finestra di manutenzione notturna.
2. Applicare le patch ai server in ordine di criticita' crescente (prima i server meno critici, poi quelli critici).
3. Per ogni server critico, seguire SOP-SRV-003 (Riavvio Pianificato).
4. Verificare il successo del deployment tramite report WSUS/SCCM/Intune.
5. Documentare le workstation/server che non hanno ricevuto le patch (offline, errori) e pianificare il recupero.

**Rollback**

In caso di problemi gravi causati da una patch:

```powershell
# Windows — Rimuovere un aggiornamento specifico
wusa /uninstall /kb:5012345 /quiet /norestart
# Oppure tramite DISM
DISM /Online /Remove-Package /PackageName:Package_for_KB5012345~31bf3856ad364e35~amd64~~10.0.1.0
```

```bash
# Linux RHEL/CentOS — Rollback ultimo aggiornamento
dnf history undo last -y
```

---

### SOP: Backup e Verifica

```
============================================================
Codice:          SOP-BKP-001
Titolo:          Monitoraggio Backup e Verifiche di Ripristino
Versione:        2.0
Owner:           Responsabile IT Operations
Classificazione: Interna
============================================================
```

**1. Procedura**

**Attivita' giornaliera — Monitoraggio backup (entro le ore 09:30)**

1. Accedere alla console di backup (Veeam, Commvault, Bacula, Acronis, ecc.).
2. Verificare lo stato di tutti i job eseguiti nelle ultime 24 ore.
3. Per ogni job in stato "Failed" o "Warning":
   - Analizzare il log dell'errore.
   - Se l'errore e' transitorio (rete, timeout, lock file), riprogrammare il job immediatamente.
   - Se l'errore e' strutturale (disco pieno, agente non raggiungibile, errore di autenticazione), aprire un ticket e intervenire entro la giornata.
4. Compilare il report giornaliero di backup (template automatizzato o manuale).
5. Inviare il report al responsabile IT Operations.

**Attivita' settimanale — Revisione (ogni lunedi')**

1. Analizzare i trend della settimana: numero di fallimenti, tempi di completamento, dimensioni dei backup.
2. Verificare che la capacita' dello storage di backup sia sufficiente per almeno 30 giorni.
3. Controllare che tutti i server/endpoint siano coperti dalla policy di backup (confronto con l'inventario CMDB).
4. Verificare la corretta esecuzione dei backup offsite/cloud (se configurati).

**Attivita' mensile — Test di ripristino**

1. Selezionare almeno 3 sistemi a rotazione (1 server critico, 1 server applicativo, 1 database).
2. Per ciascuno, eseguire un ripristino di test:
   - File-level restore: ripristinare 5-10 file casuali e verificarne l'integrita'.
   - Volume-level restore (se applicabile): ripristinare un volume su una VM di test.
   - Database restore: ripristinare un database su un'istanza di test e verificare la consistenza.
3. Documentare i risultati nel report mensile di backup con: tempo di ripristino effettivo (RTA — Recovery Time Actual), stato integrita' dati, eventuali anomalie.

**Attivita' trimestrale — Esercitazione completa di ripristino**

1. Simulare lo scenario di perdita totale di un server critico.
2. Eseguire il ripristino completo (bare metal o rebuild + data restore) in ambiente di test.
3. Misurare RTO e RPO effettivi e confrontarli con gli obiettivi dichiarati.
4. Documentare le discrepanze e le azioni correttive.
5. Presentare i risultati al management.

---

### SOP: Gestione Incidente di Rete

```
============================================================
Codice:          SOP-NET-001
Titolo:          Gestione Incidente di Rete
Versione:        1.8
Owner:           Responsabile Networking
Classificazione: Interna
============================================================
```

**1. Procedura**

**Passo 1 — Valutazione iniziale (entro 5 minuti dalla segnalazione)**

1. Ricevere la segnalazione (monitoraggio automatico, chiamata utente, ticket).
2. Determinare la natura del problema: connettivita' totale, parziale, degradazione prestazioni, DNS, DHCP.
3. Identificare l'ambito: singola postazione, piano/sede, VLAN, intera rete, WAN.
4. Assegnare la priorita' in base all'impatto:
   - P1: intera sede/rete non raggiungibile — intervento immediato
   - P2: VLAN o servizio critico impattato — entro 30 minuti
   - P3: singola postazione o servizio non critico — entro 4 ore

**Passo 2 — Determinazione dell'impatto**

```bash
# Verifica connettivita' di base
ping -c 4 gateway.azienda.local
ping -c 4 dns1.azienda.local
ping -c 4 8.8.8.8    # Test connettivita' internet

# Verifica DNS
nslookup intranet.azienda.local dns1.azienda.local

# Verifica traceroute
traceroute server-critico.azienda.local

# Verifica stato interfacce switch (via SSH)
ssh admin@switch-core-01 "show interfaces status"
ssh admin@switch-core-01 "show spanning-tree summary"
```

**Passo 3 — Isolamento (se necessario)**

Se si sospetta un loop, una tempesta broadcast o un'attivita' malevola:

```bash
# Disabilitare la porta dello switch sospetta
ssh admin@switch-accesso-03 "configure terminal"
ssh admin@switch-accesso-03 "interface GigabitEthernet0/24"
ssh admin@switch-accesso-03 "shutdown"
```

Documentare ogni azione di isolamento nel ticket con timestamp e motivazione.

**Passo 4 — Diagnosi**

1. Analizzare i log degli apparati di rete coinvolti (switch, router, firewall, AP wireless).
2. Controllare la dashboard del sistema di monitoraggio per correlazioni temporali.
3. Verificare se ci sono state modifiche recenti alla configurazione (controllare il changelog).
4. Eseguire test di connettivita' specifici per isolare il punto di guasto.

**Passo 5 — Risoluzione**

Applicare la correzione identificata. Esempi comuni:
- Riavvio porta switch in caso di errore di negoziazione.
- Correzione configurazione VLAN / routing.
- Sostituzione cavo difettoso.
- Ripristino configurazione precedente da backup.
- Riavvio servizio DHCP/DNS.

**Passo 6 — Verifica e chiusura**

1. Verificare il ripristino della connettivita' da piu' punti della rete.
2. Monitorare per almeno 30 minuti la stabilita'.
3. Notificare gli utenti del ripristino.
4. Completare la documentazione dell'incidente nel ticket: timeline, causa radice, azioni intraprese, lezioni apprese.
5. Se l'incidente rivela una debolezza strutturale, aprire un problem ticket per l'analisi RCA.

---

### SOP: Cambio Password Account Servizio

```
============================================================
Codice:          SOP-IAM-004
Titolo:          Rotazione Password Account di Servizio
Versione:        1.6
Owner:           Responsabile Sicurezza IT
Classificazione: Riservata
============================================================
```

**1. Scopo**

La rotazione periodica delle password degli account di servizio e' un requisito di sicurezza fondamentale. Tuttavia, a differenza degli account utente, il cambio password di un service account richiede l'aggiornamento coordinato in tutti i servizi e applicazioni che lo utilizzano, pena l'interruzione del servizio.

**2. Procedura**

**Passo 1 — Inventario dipendenze (T-7 giorni)**

1. Identificare l'account di servizio da ruotare (es. `svc-sqlbackup`).
2. Consultare il CMDB per ottenere l'elenco completo di tutti i servizi, task schedulati, connection string e applicazioni che utilizzano l'account.
3. Per ciascuna dipendenza, documentare: sistema, servizio, come viene utilizzata la credenziale (servizio Windows, scheduled task, connection string in file di configurazione, credential store).

Esempio di matrice dipendenze:

```
Account: svc-sqlbackup

Sistema          | Servizio/Uso                  | Tipo credenziale
-----------------+-------------------------------+---------------------------
MI-SQL-01        | SQL Server Agent              | Servizio Windows
MI-SQL-01        | Task "NightlyBackup"          | Scheduled Task
MI-APP-02        | Connection string app backup  | File web.config (criptato)
MI-MON-01        | Zabbix SQL monitoring          | Credential store Zabbix
```

**Passo 2 — Pianificazione maintenance window**

1. Richiedere l'approvazione del change nel calendario dei change.
2. Pianificare la manutenzione in una finestra di basso impatto (tipicamente notturna o nel weekend).
3. Notificare gli stakeholder dei servizi impattati.

**Passo 3 — Esecuzione cambio password (durante la maintenance window)**

```powershell
# 1. Generare la nuova password (minimo 24 caratteri, complessita' elevata)
$NuovaPassword = -join ((65..90) + (97..122) + (48..57) + (33..38) |
    Get-Random -Count 30 | ForEach-Object {[char]$_})

# 2. Cambiare la password in Active Directory
Set-ADAccountPassword -Identity "svc-sqlbackup" -NewPassword (
    ConvertTo-SecureString $NuovaPassword -AsPlainText -Force) -Reset

# 3. Aggiornare il servizio Windows su MI-SQL-01
$svc = Get-WmiObject -Class Win32_Service -Computer "MI-SQL-01" -Filter "Name='SQLSERVERAGENT'"
$svc.Change($null,$null,$null,$null,$null,$null,"AZIENDA\svc-sqlbackup",$NuovaPassword)
Restart-Service -Name "SQLSERVERAGENT" -ComputerName "MI-SQL-01"

# 4. Aggiornare lo scheduled task
schtasks /change /s MI-SQL-01 /tn "NightlyBackup" /ru "AZIENDA\svc-sqlbackup" /rp "$NuovaPassword"

# 5. Aggiornare la connection string su MI-APP-02
# (accedere al server e aggiornare il file di configurazione criptato)

# 6. Aggiornare le credenziali nel credential store di Zabbix
# (tramite interfaccia web o API Zabbix)
```

**Passo 4 — Verifica di tutti i servizi**

```powershell
# Verificare che il servizio SQL Server Agent sia in esecuzione
Get-Service -Name "SQLSERVERAGENT" -ComputerName "MI-SQL-01" | Select-Object Status

# Verificare che lo scheduled task non sia in stato di errore
schtasks /query /s MI-SQL-01 /tn "NightlyBackup" /v /fo LIST

# Verificare la connettivita' dell'applicazione di backup
# (eseguire un test di backup manuale)

# Verificare il monitoraggio Zabbix
# (controllare nella dashboard che il check SQL sia verde)
```

**Passo 5 — Documentazione**

1. Aggiornare il password vault (KeePass, CyberArk, HashiCorp Vault) con la nuova password.
2. Registrare la data di rotazione nel CMDB.
3. Aggiornare il ticket di change con i dettagli dell'operazione.
4. Pianificare la prossima rotazione (tipicamente ogni 90 giorni).

---

### SOP: Gestione Certificati

```
============================================================
Codice:          SOP-SEC-003
Titolo:          Gestione Ciclo di Vita Certificati Digitali
Versione:        1.5
Owner:           Responsabile Sicurezza IT
Classificazione: Interna
============================================================
```

**1. Procedura**

**Passo 1 — Richiesta certificato (CSR Generation)**

1. Identificare il tipo di certificato necessario: SSL/TLS per web server, code signing, client authentication, S/MIME per email.
2. Generare la Certificate Signing Request (CSR) sul server destinatario:

```bash
# Generazione CSR con OpenSSL
openssl req -new -newkey rsa:2048 -nodes \
    -keyout /etc/ssl/private/webapp.azienda.com.key \
    -out /etc/ssl/certs/webapp.azienda.com.csr \
    -subj "/C=IT/ST=Lombardia/L=Milano/O=Azienda SpA/OU=IT/CN=webapp.azienda.com" \
    -addext "subjectAltName=DNS:webapp.azienda.com,DNS:www.webapp.azienda.com"

# Verificare il contenuto della CSR
openssl req -in /etc/ssl/certs/webapp.azienda.com.csr -text -noout
```

```powershell
# Generazione CSR con PowerShell (per CA interna Microsoft)
$Template = "WebServer"
$SubjectName = "CN=webapp.azienda.com,O=Azienda SpA,L=Milano,S=Lombardia,C=IT"
$SAN = @{dns=@("webapp.azienda.com","www.webapp.azienda.com")}
Get-Certificate -Template $Template -SubjectName $SubjectName -DnsName $SAN.dns -CertStoreLocation cert:\LocalMachine\My
```

**Passo 2 — Approvazione e emissione**

1. Per CA interna: sottoporre la CSR alla Certificate Authority aziendale. L'approvazione segue il workflow definito (automatico o manuale in base al tipo di certificato).
2. Per CA esterna (DigiCert, Let's Encrypt, Sectigo): sottomettere la CSR tramite il portale del provider e completare la validazione del dominio (DCV).
3. Scaricare il certificato emesso e la catena intermedia.

**Passo 3 — Installazione**

```bash
# Apache/Nginx
cp webapp.azienda.com.crt /etc/ssl/certs/
cp chain.crt /etc/ssl/certs/
# Aggiornare la configurazione del virtualhost
# Riavviare il servizio web
systemctl reload nginx
```

```powershell
# IIS
Import-PfxCertificate -FilePath "C:\certs\webapp.azienda.com.pfx" `
    -CertStoreLocation Cert:\LocalMachine\My -Password (ConvertTo-SecureString "password" -AsPlainText -Force)
# Associare il certificato al binding del sito in IIS Manager
```

**Passo 4 — Verifica**

```bash
# Verificare il certificato installato
openssl s_client -connect webapp.azienda.com:443 -servername webapp.azienda.com < /dev/null 2>/dev/null | openssl x509 -text -noout

# Verificare la catena completa
openssl s_client -connect webapp.azienda.com:443 -showcerts
```

**Passo 5 — Monitoraggio scadenze e rinnovo**

1. Registrare il certificato nel registro centralizzato (spreadsheet, CMDB, o tool dedicato come Venafi/Keyfactor).
2. Configurare alert di scadenza: 90 giorni, 60 giorni, 30 giorni, 14 giorni, 7 giorni.
3. Avviare il processo di rinnovo almeno 30 giorni prima della scadenza.

**Passo 6 — Revoca (quando necessario)**

Revocare un certificato immediatamente se:
- La chiave privata e' stata compromessa.
- Il server associato e' stato decommissionato.
- Il dominio non e' piu' di proprieta' dell'organizzazione.
- Il certificato e' stato emesso con informazioni errate.

```bash
# Tramite CA interna Microsoft
certutil -revoke <serial_number> 1    # reason: key compromise
# Pubblicare la CRL aggiornata
certutil -CRL
```

---

### SOP: Escalation a Fornitori

```
============================================================
Codice:          SOP-OPS-005
Titolo:          Escalation Incidenti a Fornitori Esterni
Versione:        1.3
Owner:           Responsabile IT Operations
Classificazione: Interna
============================================================
```

**1. Scopo**

Standardizzare il processo di coinvolgimento dei fornitori esterni (vendor) nella risoluzione di incidenti che superano le competenze o i permessi del team IT interno.

**2. Quando eseguire l'escalation**

- Il problema riguarda un bug nel software del vendor.
- E' necessario accedere a livelli di supporto o diagnostica non disponibili internamente.
- Il problema persiste dopo aver esaurito tutte le procedure interne di troubleshooting.
- Il contratto SLA prevede il coinvolgimento del vendor per determinate tipologie di incidenti.
- E' necessaria una patch o un hotfix dal vendor.

**3. Procedura**

**Passo 1 — Preparazione informazioni**

Prima di contattare il fornitore, raccogliere TUTTE le informazioni necessarie:

```
INFORMAZIONI DA PREPARARE PER L'ESCALATION:

1. Identificazione sistema:
   - Nome prodotto e versione esatta (build number)
   - Sistema operativo e versione
   - Architettura (fisico/virtuale, specifiche hardware)
   - Configurazione rilevante

2. Descrizione del problema:
   - Sintomi osservati (con screenshot/video se possibile)
   - Timestamp esatto di inizio del problema
   - Frequenza: continuo, intermittente, occasionale
   - Impatto: numero di utenti/sistemi coinvolti

3. Azioni gia' intraprese:
   - Elenco dettagliato di tutti i troubleshooting eseguiti
   - Risultati di ciascun tentativo
   - Eventuali workaround temporanei applicati

4. Evidenze tecniche:
   - Log rilevanti (ultimi 24-48 ore)
   - Dump di memoria (se applicabile)
   - Trace di rete (se applicabile)
   - Output di comandi diagnostici

5. Riferimenti:
   - Numero ticket interno
   - Numero contratto di supporto / SLA
   - Livello di severita' richiesto
```

**Passo 2 — Contatto fornitore**

1. Aprire il ticket tramite il portale del vendor (preferibile) o telefonicamente.
2. Specificare chiaramente il livello di severita':
   - Sev 1 / Critical: sistema di produzione non funzionante, nessun workaround
   - Sev 2 / High: funzionalita' critica degradata, workaround parziale disponibile
   - Sev 3 / Medium: problema con impatto limitato, workaround disponibile
   - Sev 4 / Low: richiesta informazione, miglioramento, problema cosmetico
3. Fornire tutte le informazioni preparate al Passo 1.
4. Richiedere esplicitamente il numero di ticket del vendor e i tempi di risposta previsti dall'SLA.

**Passo 3 — Follow-up strutturato**

| Severita' | Frequenza follow-up | Canale |
|-----------|---------------------|--------|
| Sev 1 | Ogni 2 ore | Telefono + email |
| Sev 2 | Ogni 4 ore lavorative | Email + portale |
| Sev 3 | Ogni 24 ore lavorative | Portale |
| Sev 4 | Ogni 72 ore lavorative | Portale |

**Passo 4 — Verifica risoluzione**

1. Testare la soluzione proposta dal vendor in ambiente di test prima di applicarla in produzione.
2. Se la soluzione funziona, applicarla in produzione seguendo il processo di change management.
3. Monitorare il sistema per almeno 48 ore dopo l'applicazione.
4. Confermare la risoluzione al vendor e chiudere il ticket.

**Passo 5 — Documentazione**

1. Aggiornare il ticket interno con: numero ticket vendor, timeline completa, soluzione applicata.
2. Se la soluzione rappresenta una nuova procedura, creare o aggiornare la knowledge base interna.
3. Valutare se la causa del problema richiede azioni preventive (upgrade, configurazione diversa, monitoring aggiuntivo).

---

## Runbook

### Struttura Runbook Standard

A differenza delle SOP, i runbook sono documenti altamente tecnici, orientati all'esecuzione rapida durante situazioni operative critiche. Il formato deve privilegiare la chiarezza e la velocita' di consultazione.

```
============================================================
RUNBOOK
============================================================

Codice:          RB-[AREA]-[NUMERO]
Titolo:          [Titolo descrittivo]
Versione:        [X.Y]
Ultima modifica: [GG/MM/AAAA]
Autore:          [Nome]
Classificazione: [Interna / Riservata]

------------------------------------------------------------
CONDIZIONE DI ATTIVAZIONE (TRIGGER)
------------------------------------------------------------
Descrivere la condizione esatta che richiede l'esecuzione
di questo runbook (alert specifico, sintomo osservato, ecc.)

------------------------------------------------------------
PREREQUISITI
------------------------------------------------------------
- Accessi necessari
- Strumenti richiesti
- Informazioni da raccogliere prima di iniziare

------------------------------------------------------------
PROCEDURA
------------------------------------------------------------
Ogni passo include:
  - Comando da eseguire (copia-incolla pronto)
  - Output atteso
  - Cosa fare se l'output e' diverso da quello atteso
  - Tempo massimo per il passo

------------------------------------------------------------
CRITERI DI ESCALATION
------------------------------------------------------------
Condizioni in cui fermarsi e coinvolgere il livello superiore.

------------------------------------------------------------
VERIFICA
------------------------------------------------------------
Come confermare che il problema e' risolto.

------------------------------------------------------------
POST-AZIONE
------------------------------------------------------------
Documentazione, notifiche, azioni di follow-up.
```

---

### Runbook: Riavvio Servizi Critici

```
============================================================
RUNBOOK
============================================================
Codice:          RB-SVC-001
Titolo:          Riavvio Servizi Critici
Versione:        2.1
Ultima modifica: 18/03/2026
Classificazione: Interna
============================================================
```

**Trigger**: Alert di monitoraggio indica che un servizio critico non risponde o e' in stato degradato. Il servizio non si e' ripristinato automaticamente entro 5 minuti.

**SQL Server**

```powershell
# 1. Verificare lo stato attuale
Get-Service -Name "MSSQLSERVER" -ComputerName "MI-SQL-01"
# Output atteso: Status = Stopped o status = Running ma non risponde alle query

# 2. Se il servizio e' in esecuzione ma non risponde, verificare i processi
Invoke-Command -ComputerName "MI-SQL-01" -ScriptBlock {
    Get-Process -Name "sqlservr" | Select-Object CPU, WorkingSet64, Threads
}

# 3. Tentare il riavvio grazioso
Restart-Service -Name "MSSQLSERVER" -ComputerName "MI-SQL-01" -Force
# Attendere fino a 120 secondi

# 4. Verificare il ripristino
Invoke-Sqlcmd -ServerInstance "MI-SQL-01" -Query "SELECT @@VERSION" -QueryTimeout 30
# Output atteso: versione SQL Server

# 5. Riavviare SQL Server Agent
Restart-Service -Name "SQLSERVERAGENT" -ComputerName "MI-SQL-01"

# ESCALATION: se il servizio non si avvia entro 5 minuti, coinvolgere il DBA
```

**Exchange Server (servizi principali)**

```powershell
# 1. Verificare lo stato di tutti i servizi Exchange
Get-Service -ComputerName "MI-EXC-01" | Where-Object {$_.DisplayName -like "Microsoft Exchange*"} | Select-Object Name, Status

# 2. Riavviare i servizi critici in ordine
$ServiziExchange = @(
    "MSExchangeADTopology",
    "MSExchangeServiceHost",
    "MSExchangeIS",
    "MSExchangeTransport",
    "MSExchangeMailboxAssistants",
    "MSExchangeRPC"
)

foreach ($svc in $ServiziExchange) {
    Write-Output "Riavvio $svc..."
    Restart-Service -Name $svc -ComputerName "MI-EXC-01" -Force
    Start-Sleep -Seconds 15
    $status = (Get-Service -Name $svc -ComputerName "MI-EXC-01").Status
    Write-Output "$svc: $status"
}

# 3. Verificare il flusso email
Send-MailMessage -From "test@azienda.local" -To "admin@azienda.local" -Subject "Test post-riavvio $(Get-Date)" -SmtpServer "MI-EXC-01"
```

**Active Directory Domain Services**

```powershell
# ATTENZIONE: il riavvio di AD DS impatta tutti i servizi di autenticazione.
# Eseguire SOLO se strettamente necessario e dopo aver verificato la disponibilita'
# di almeno un altro domain controller funzionante.

# 1. Verificare la disponibilita' degli altri DC
Get-ADDomainController -Filter * | Select-Object HostName, IsGlobalCatalog, OperatingSystem

# 2. Verificare la replicazione
repadmin /replsummary
# Output atteso: 0 errori

# 3. Riavviare il servizio NTDS (solo il servizio, non il server)
Restart-Service -Name "NTDS" -ComputerName "MI-DC-02" -Force

# 4. Verificare
dcdiag /s:MI-DC-02 /test:services /test:replications /test:advertising
# Output atteso: tutti i test passed
```

**IIS (Internet Information Services)**

```powershell
# 1. Riavviare l'application pool specifico (preferibile al riavvio completo)
Invoke-Command -ComputerName "MI-WEB-01" -ScriptBlock {
    Import-Module WebAdministration
    Restart-WebAppPool -Name "AppPoolWebApp"
}

# 2. Se il problema persiste, riavviare IIS completamente
Invoke-Command -ComputerName "MI-WEB-01" -ScriptBlock { iisreset /restart }

# 3. Verificare che i siti rispondano
Invoke-WebRequest -Uri "https://webapp.azienda.com/health" -UseBasicParsing | Select-Object StatusCode
# Output atteso: StatusCode = 200
```

**Apache/Nginx (Linux)**

```bash
# Apache
sudo systemctl restart httpd    # RHEL/CentOS
sudo systemctl restart apache2  # Ubuntu/Debian

# Verificare
systemctl status httpd
curl -s -o /dev/null -w "%{http_code}" https://webapp.azienda.com/health
# Output atteso: 200

# Nginx
sudo systemctl restart nginx

# Verificare la configurazione prima del riavvio (best practice)
nginx -t
# Output atteso: syntax is ok / test is successful
sudo systemctl restart nginx
```

**PostgreSQL**

```bash
# 1. Verificare lo stato
sudo systemctl status postgresql-15

# 2. Riavvio grazioso
sudo systemctl restart postgresql-15

# 3. Verificare la connettivita'
psql -h localhost -U postgres -c "SELECT version();"
# Output atteso: versione PostgreSQL

# 4. Verificare che i database siano accessibili
psql -h localhost -U postgres -c "SELECT datname, numbackends FROM pg_stat_database WHERE datname NOT LIKE 'template%';"
```

---

### Runbook: Failover Database

```
============================================================
RUNBOOK
============================================================
Codice:          RB-DB-001
Titolo:          Failover Manuale Database
Versione:        1.8
Ultima modifica: 22/03/2026
Classificazione: Riservata
============================================================
```

**Trigger**: Il nodo primario del database cluster non e' raggiungibile o mostra degradazione critica delle prestazioni. Il failover automatico non si e' attivato oppure e' necessario un failover manuale pianificato.

**SQL Server Always On Availability Group**

```powershell
# 1. Verificare lo stato corrente del gruppo di disponibilita'
Invoke-Sqlcmd -ServerInstance "MI-SQL-02" -Query "
    SELECT ag.name AS ag_name,
           ar.replica_server_name,
           ars.role_desc,
           ars.synchronization_health_desc,
           ars.connected_state_desc
    FROM sys.dm_hadr_availability_replica_states ars
    JOIN sys.availability_replicas ar ON ars.replica_id = ar.replica_id
    JOIN sys.availability_groups ag ON ar.group_id = ag.group_id
"
# Output atteso: MI-SQL-01 = PRIMARY (o non raggiungibile), MI-SQL-02 = SECONDARY

# 2. Verificare che la replica secondaria sia sincronizzata
Invoke-Sqlcmd -ServerInstance "MI-SQL-02" -Query "
    SELECT database_name, synchronization_state_desc, synchronization_health_desc,
           last_hardened_lsn, last_received_lsn
    FROM sys.dm_hadr_database_replica_states
    WHERE is_local = 1
"
# Output atteso: synchronization_state_desc = SYNCHRONIZED

# 3. Eseguire il failover manuale (SOLO se la replica e' SYNCHRONIZED)
Invoke-Sqlcmd -ServerInstance "MI-SQL-02" -Query "
    ALTER AVAILABILITY GROUP [AG-Produzione] FAILOVER
"
# ATTENZIONE: se la replica non e' sincronizzata e il primario non e' raggiungibile,
# e' necessario un forced failover con potenziale perdita di dati:
# ALTER AVAILABILITY GROUP [AG-Produzione] FORCE_FAILOVER_ALLOW_DATA_LOSS

# 4. Verificare il nuovo stato
Invoke-Sqlcmd -ServerInstance "MI-SQL-02" -Query "
    SELECT replica_server_name, role_desc
    FROM sys.dm_hadr_availability_replica_states ars
    JOIN sys.availability_replicas ar ON ars.replica_id = ar.replica_id
"
# Output atteso: MI-SQL-02 = PRIMARY

# 5. Verificare la connettivita' applicativa
# (il listener DNS dovrebbe ora puntare a MI-SQL-02)
Invoke-Sqlcmd -ServerInstance "sql-listener.azienda.local" -Query "SELECT @@SERVERNAME"
# Output atteso: MI-SQL-02

# 6. Monitorare per 15 minuti eventuali errori applicativi
```

**PostgreSQL con Patroni**

```bash
# 1. Verificare lo stato del cluster Patroni
patronictl -c /etc/patroni/patroni.yml list
# Output atteso: mostra tutti i nodi con i loro ruoli (Leader, Replica)

# 2. Verificare il lag di replicazione
patronictl -c /etc/patroni/patroni.yml list
# Controllare la colonna "Lag in MB" — deve essere 0 o quasi

# 3. Eseguire il switchover (failover pianificato verso un nodo specifico)
patronictl -c /etc/patroni/patroni.yml switchover --master pg-node-01 --candidate pg-node-02 --force
# Output atteso: conferma del switchover completato

# 4. Per failover forzato (se il leader non e' raggiungibile)
patronictl -c /etc/patroni/patroni.yml failover --force
# Patroni selezionera' automaticamente la replica piu' aggiornata

# 5. Verificare il nuovo stato
patronictl -c /etc/patroni/patroni.yml list
# Output atteso: pg-node-02 = Leader

# 6. Verificare la connettivita' applicativa tramite il VIP/HAProxy
psql -h pg-vip.azienda.local -U app_user -d app_database -c "SELECT inet_server_addr();"
# Output atteso: IP di pg-node-02

# 7. Verificare i log di Patroni per errori
journalctl -u patroni -n 100 --no-pager
```

**Notifica post-failover**

Inviare immediatamente una comunicazione al team con:
- Timestamp del failover
- Motivo (guasto, pianificato, degradazione)
- Nodo attuale primario
- Stato della replicazione
- Eventuali azioni di follow-up necessarie (ripristino del vecchio primario come replica)

---

### Runbook: Ripristino da Backup

```
============================================================
RUNBOOK
============================================================
Codice:          RB-BKP-001
Titolo:          Ripristino Dati da Backup
Versione:        2.3
Ultima modifica: 15/03/2026
Classificazione: Riservata
============================================================
```

**Trigger**: Perdita di dati, corruzione di file, guasto server, richiesta di ripristino dati da parte di un utente o di un'applicazione.

**Passo 1 — Determinare cosa ripristinare**

| Scenario | Tipo di ripristino | Strumento tipico |
|---|---|---|
| File/cartella singola cancellata | File-level restore | Veeam, Commvault, Shadow Copy |
| Intero volume corrotto | Volume-level restore | Veeam, Commvault |
| Server completamente guasto | Bare metal restore / VM restore | Veeam, Commvault, Windows Server Backup |
| Database corrotto | Database restore | Strumento nativo (SQL BAK, pg_restore) |
| VM non avviabile | Full VM restore | Veeam, Commvault, snapshot hypervisor |

**Passo 2 — Selezionare il backup appropriato**

1. Consultare la console di backup per identificare i backup disponibili.
2. Selezionare il punto di ripristino piu' recente PRECEDENTE all'evento che ha causato la perdita.
3. Verificare l'integrita' del backup selezionato (checksum, stato "Success" del job).

**Passo 3 — Eseguire il ripristino**

**File-level restore (Veeam)**

```powershell
# 1. Avviare una sessione di restore dalla console Veeam
# GUI: Backup & Replication > Home > Restore > Guest files > Microsoft Windows

# 2. Selezionare il backup point desiderato
# 3. Navigare fino al file/cartella da ripristinare
# 4. Scegliere "Restore" > "Overwrite" o "Keep existing" in base alla necessita'
```

**Full VM restore (Veeam)**

```powershell
# 1. Dalla console Veeam: Home > Restore > VMware vSphere > Entire VM
# 2. Selezionare la VM e il restore point
# 3. Scegliere la destinazione:
#    - Original location (sovrascrive la VM esistente)
#    - New location (ripristina come nuova VM — preferibile per test)
# 4. Configurare le opzioni di rete (disconnettere la NIC se si ripristina nella stessa rete per evitare conflitti IP)
# 5. Avviare il restore
```

**Database restore — SQL Server**

```sql
-- 1. Ripristinare l'ultimo backup completo
RESTORE DATABASE [AppDatabase] FROM DISK = N'\\backup\sql\AppDatabase_FULL_20260325.bak'
WITH NORECOVERY, REPLACE,
MOVE 'AppDatabase_Data' TO 'D:\SQLData\AppDatabase.mdf',
MOVE 'AppDatabase_Log' TO 'L:\SQLLog\AppDatabase_log.ldf'

-- 2. Applicare i backup differenziali
RESTORE DATABASE [AppDatabase] FROM DISK = N'\\backup\sql\AppDatabase_DIFF_20260326_0200.bak'
WITH NORECOVERY

-- 3. Applicare i backup del transaction log fino al punto desiderato
RESTORE LOG [AppDatabase] FROM DISK = N'\\backup\sql\AppDatabase_LOG_20260326_0800.trn'
WITH RECOVERY, STOPAT = '2026-03-26T07:30:00'

-- 4. Verificare l'integrita'
DBCC CHECKDB ('AppDatabase') WITH NO_INFOMSGS
```

**Database restore — PostgreSQL**

```bash
# 1. Fermare il servizio (se necessario un restore completo)
sudo systemctl stop postgresql-15

# 2. Ripristinare da pg_dump (logical backup)
pg_restore -h localhost -U postgres -d app_database -c -v /backup/pg/app_database_20260325.dump

# 3. Oppure ripristinare da base backup (physical backup) + WAL replay
# Fermare PostgreSQL
sudo systemctl stop postgresql-15
# Spostare la directory dati corrente
mv /var/lib/pgsql/15/data /var/lib/pgsql/15/data_old
# Ripristinare il base backup
tar xzf /backup/pg/base_20260325.tar.gz -C /var/lib/pgsql/15/
# Configurare il recovery
cat > /var/lib/pgsql/15/data/postgresql.auto.conf << 'CONF'
restore_command = 'cp /backup/pg/wal/%f %p'
recovery_target_time = '2026-03-26 07:30:00+01'
recovery_target_action = 'promote'
CONF
touch /var/lib/pgsql/15/data/recovery.signal
# Avviare PostgreSQL
sudo systemctl start postgresql-15
```

**Passo 4 — Verificare l'integrita' dei dati**

1. Confrontare i dati ripristinati con le aspettative (conteggio record, file campione, hash).
2. Per i database, eseguire query di verifica su tabelle critiche.
3. Per i file, verificare che siano leggibili e non corrotti.

**Passo 5 — Riavvio servizi e notifica**

1. Riavviare i servizi applicativi che dipendono dai dati ripristinati.
2. Verificare il funzionamento dell'applicazione.
3. Notificare gli utenti/richiedenti del completamento del ripristino.
4. Documentare nel ticket: punto di ripristino utilizzato, dati ripristinati, eventuali dati persi (gap tra ultimo backup e momento dell'incidente).

---

### Runbook: Risposta Ransomware

```
============================================================
RUNBOOK
============================================================
Codice:          RB-SEC-001
Titolo:          Risposta a Incidente Ransomware
Versione:        2.0
Ultima modifica: 20/03/2026
Classificazione: RISERVATA — DISTRIBUZIONE CONTROLLATA
============================================================
```

**Trigger**: Rilevamento di attivita' ransomware: file criptati in modo anomalo, note di riscatto trovate, alert EDR per comportamento di cifratura massiva, segnalazione utente di file inaccessibili.

**FASE 1 — Isolamento immediato (entro 15 minuti dal rilevamento)**

QUESTO E' IL PASSO PIU' CRITICO. Ogni minuto di ritardo nell'isolamento puo' significare migliaia di file aggiuntivi cifrati.

```powershell
# 1. Isolare IMMEDIATAMENTE la/le macchine infette dalla rete
# Opzione A: Disabilitare le porte switch
ssh admin@switch-accesso-XX "configure terminal"
ssh admin@switch-accesso-XX "interface GigabitEthernet0/YY"
ssh admin@switch-accesso-XX "shutdown"

# Opzione B: Disabilitare le interfacce di rete via GPO o script remoto
Invoke-Command -ComputerName "PC-INFETTO" -ScriptBlock {
    Get-NetAdapter | Disable-NetAdapter -Confirm:$false
}

# Opzione C: Tramite EDR — contenimento endpoint (CrowdStrike, Defender for Endpoint)
# Utilizzare la funzione "Isolate device" nella console EDR

# 2. NON SPEGNERE LE MACCHINE (la memoria volatile contiene evidenze forensi)

# 3. Disabilitare IMMEDIATAMENTE gli account utente compromessi
Disable-ADAccount -Identity "utente-compromesso"
# Reimpostare la password
Set-ADAccountPassword -Identity "utente-compromesso" -NewPassword (
    ConvertTo-SecureString "T3mp_S3cur3_P@ss!" -AsPlainText -Force) -Reset
```

**FASE 2 — Valutazione dell'ambito (entro 1 ora)**

```powershell
# 1. Identificare tutti i sistemi potenzialmente coinvolti
# Cercare nella console EDR gli alert correlati
# Cercare nei log del file server accessi anomali

# 2. Controllare i log di Active Directory per attivita' sospette
Get-WinEvent -LogName Security -ComputerName "MI-DC-01" -MaxEvents 5000 |
    Where-Object { $_.Id -in @(4624,4625,4672,4720,4728,4732) -and
    $_.TimeCreated -gt (Get-Date).AddHours(-6) } |
    Select-Object TimeCreated, Id, Message | Export-Csv "C:\Incident\AD-Events.csv"

# 3. Verificare se la replicazione AD e' stata compromessa
repadmin /replsummary

# 4. Controllare lo stato dei backup — sono integri? Il ransomware ha raggiunto il backup server?
# Verificare IMMEDIATAMENTE la raggiungibilita' e l'integrita' del backup repository
```

**FASE 3 — Preservazione delle evidenze**

1. Catturare un dump della memoria delle macchine infette (prima di qualsiasi altra azione):

```bash
# Utilizzare strumenti forensi come WinPmem, FTK Imager, Volatility
# winpmem_mini_x64.exe output.raw
```

2. Creare un'immagine forense dei dischi delle macchine infette (se possibile senza interrompere l'isolamento).
3. Esportare tutti i log rilevanti: EDR, firewall, proxy, DNS, AD, file server.
4. Documentare ogni azione con timestamp esatto.
5. Preservare la catena di custodia delle evidenze.

**FASE 4 — Comunicazione**

Seguire rigorosamente il piano di comunicazione aziendale per incidenti di sicurezza:

```
NOTIFICHE OBBLIGATORIE (in ordine di priorita'):

1. CISO / Responsabile Sicurezza IT — IMMEDIATO
   Canale: telefono + email

2. IT Manager / CIO — entro 30 minuti
   Canale: telefono + email

3. Direzione Generale / CEO — entro 1 ora
   Canale: tramite CISO/CIO

4. Ufficio Legale — entro 2 ore
   Canale: email formale

5. DPO (Data Protection Officer) — entro 4 ore
   Canale: email formale (valutazione obbligo notifica Garante Privacy
   ai sensi GDPR art. 33 — entro 72 ore dalla scoperta)

6. Forze dell'Ordine (Polizia Postale) — secondo indicazioni legali
   Canale: tramite Ufficio Legale

7. Assicurazione Cyber (se presente polizza) — entro 24 ore
   Canale: secondo quanto previsto dalla polizza

IMPORTANTE: NON comunicare pubblicamente l'incidente senza approvazione
del management e dell'ufficio legale. NON contattare direttamente
gli attaccanti. NON pagare il riscatto senza approvazione esplicita
della Direzione e consulenza legale.
```

**FASE 5 — Ripristino da backup**

1. Verificare che il ransomware sia stato completamente eradicato da tutti i sistemi prima di iniziare il ripristino.
2. Identificare il punto di ripristino sicuro: l'ultimo backup PRECEDENTE alla data stimata di compromissione iniziale (non la data di cifratura, che potrebbe essere successiva all'intrusione iniziale).
3. Procedere al ripristino seguendo RB-BKP-001, iniziando dai sistemi piu' critici.
4. Ricostruire da zero le macchine compromesse (NON ripristinare semplicemente i file — l'attaccante potrebbe aver installato backdoor).
5. Reimpostare TUTTE le password di dominio (utenti, servizi, amministratori) prima di riconnettere i sistemi alla rete.

**FASE 6 — Hardening post-incidente**

1. Analizzare il vettore di attacco iniziale e chiudere la vulnerabilita'.
2. Verificare e rafforzare le policy di backup (regola 3-2-1, backup immutabile, air-gapped backup).
3. Implementare o rafforzare la segmentazione di rete.
4. Verificare e aggiornare le regole EDR/antivirus.
5. Implementare o rafforzare il monitoraggio delle condivisioni di rete.
6. Verificare le policy di least privilege per tutti gli account.

**FASE 7 — Lessons learned**

Entro 2 settimane dall'incidente, condurre una sessione di Post-Incident Review (PIR) che produca:

1. Timeline dettagliata dell'incidente.
2. Root Cause Analysis (RCA) completa.
3. Valutazione dell'efficacia della risposta.
4. Elenco delle azioni correttive con responsabile e scadenza.
5. Aggiornamento dei runbook e delle procedure in base alle lezioni apprese.

---

## Gestione Documentazione

La gestione della documentazione delle procedure operative e' essa stessa un processo che richiede disciplina e struttura. Procedure obsolete o inaccurate sono peggio dell'assenza di procedure, perche' creano un falso senso di sicurezza.

### Controllo versione

Ogni modifica a una SOP o a un runbook deve essere tracciata:

1. **Numerazione versioni**: utilizzare il formato X.Y dove X rappresenta le modifiche sostanziali (nuovi passi, cambio di flusso) e Y le modifiche minori (correzioni, chiarimenti, aggiornamenti di URL o nomi server).
2. **Changelog**: ogni versione deve avere un'entry nello storico revisioni con data, autore e descrizione sintetica della modifica.
3. **Repository**: tutte le procedure devono risiedere in un repository centralizzato (wiki, SharePoint, Git) con controllo degli accessi e storico delle modifiche.

### Ciclo di revisione

- **Revisione minima annuale**: ogni procedura deve essere revisionata almeno una volta all'anno, anche se non sono state apportate modifiche. La revisione conferma che la procedura e' ancora valida e rilevante.
- **Revisione su evento**: una procedura deve essere revisionata immediatamente quando:
  - Un incidente rivela che la procedura e' incompleta o errata.
  - Un sistema o un servizio referenziato viene modificato, aggiornato o sostituito.
  - Un cambio organizzativo modifica le responsabilita'.
  - Un audit identifica una non conformita'.
- **Revisione trimestrale raccomandata** per le procedure critiche (risposta incidenti, disaster recovery, sicurezza).

### Workflow di approvazione

1. L'autore redige o modifica la procedura.
2. Un peer reviewer tecnico verifica l'accuratezza dei contenuti.
3. Il responsabile dell'area (owner della procedura) approva formalmente.
4. Per le procedure che impattano la sicurezza o la compliance, il CISO o il responsabile compliance aggiunge la propria approvazione.
5. La versione approvata viene pubblicata nel repository ufficiale e la versione precedente viene archiviata.

### Distribuzione e accesso

- Le procedure devono essere accessibili a tutto il team IT, con eccezione di quelle classificate come "Riservate" (es. risposte a incidenti di sicurezza, procedure forensi).
- L'accesso offline deve essere garantito per i runbook critici (le emergenze possono includere interruzioni di rete che impediscono l'accesso ai sistemi documentali).
- Mantenere copie stampate dei runbook piu' critici (risposta ransomware, disaster recovery) in una posizione fisica nota e accessibile.

### Formazione sulle procedure

- Ogni nuovo membro del team deve completare un percorso di formazione sulle SOP principali durante l'onboarding.
- Le esercitazioni pratiche (tabletop exercise, simulation drill) devono essere condotte almeno semestralmente per i runbook critici.
- Le sessioni di formazione devono essere documentate con data, partecipanti e contenuti trattati.

### Test delle procedure

- Le SOP devono essere testate facendole eseguire a un tecnico che non ha partecipato alla loro stesura (test di eseguibilita').
- I runbook devono essere testati in ambiente di laboratorio/staging almeno una volta all'anno.
- I risultati dei test devono alimentare il ciclo di revisione per correggere eventuali ambiguita' o errori.

---

## Best Practices

1. **Scrivere per il lettore meno esperto**: una procedura deve essere eseguibile anche da un tecnico junior o da un collega di un altro team chiamato a intervenire in emergenza. Non dare mai per scontate conoscenze pregresse.

2. **Un passo, un'azione**: ogni passo della procedura deve descrivere una singola azione. Evitare passi che contengono molteplici operazioni combinate — aumentano il rischio di errore e rendono difficile identificare il punto di fallimento.

3. **Includere sempre i comandi di verifica**: dopo ogni azione significativa, includere il comando per verificare che l'azione abbia avuto successo. Non limitarsi a dire "riavviare il servizio" — aggiungere "verificare che il servizio sia in stato Running con il comando...".

4. **Documentare gli output attesi**: per ogni comando, descrivere l'output che ci si aspetta di vedere. Questo permette all'operatore di riconoscere immediatamente se qualcosa e' andato storto.

5. **Prevedere sempre il rollback**: ogni SOP deve includere una sezione di rollback che descriva come annullare le modifiche apportate. In situazioni di emergenza, sapere come tornare allo stato precedente e' altrettanto importante quanto sapere come procedere.

6. **Mantenere le procedure vive**: una procedura che non viene aggiornata da piu' di 12 mesi e' sospetta. Inserire nel calendario IT le scadenze di revisione e trattarle con la stessa serieta' delle scadenze operative.

7. **Usare un linguaggio imperativo e non ambiguo**: scrivere "Eseguire il comando..." e non "Si potrebbe eseguire il comando...". Le procedure non sono suggerimenti — sono istruzioni.

8. **Separare il "cosa" dal "perche'"**: il corpo della procedura deve contenere le istruzioni operative (cosa fare). Le spiegazioni del motivo (perche') possono essere inserite in note a margine o in sezioni dedicate, per non rallentare l'esecuzione in situazioni di urgenza.

9. **Testare ogni procedura prima di pubblicarla**: una procedura non testata e' una procedura inaffidabile. Farla eseguire a un collega in ambiente di test prima di dichiararla operativa.

10. **Centralizzare e indicizzare**: tutte le procedure devono risiedere in un unico repository con un sistema di ricerca efficace. Il tempo speso a cercare una procedura durante un'emergenza e' tempo che aggrava l'incidente.

---

## Troubleshooting

### Problema: la procedura non corrisponde piu' alla realta' del sistema

**Causa**: il sistema e' stato aggiornato o modificato senza aggiornare la procedura corrispondente.
**Soluzione**: implementare un processo obbligatorio che colleghi ogni change request alla revisione delle procedure impattate. Nel ticket di change, includere un campo "Procedure da aggiornare" che deve essere compilato prima della chiusura del change.

### Problema: le procedure vengono scritte ma non utilizzate dal team

**Causa**: il team non conosce l'esistenza delle procedure, non le trova facilmente o le considera troppo complicate.
**Soluzione**: integrare le procedure nel flusso di lavoro quotidiano. Collegare le procedure ai ticket ITSM (es. quando si apre un ticket di tipo "Creazione utente", il sistema deve proporre automaticamente il link alla SOP-IAM-001). Semplificare le procedure eccessivamente verbose. Raccogliere feedback dal team sull'usabilita'.

### Problema: procedure duplicate o contraddittorie

**Causa**: assenza di un processo centralizzato di gestione documentale. Piu' persone hanno creato procedure simili in ubicazioni diverse.
**Soluzione**: eseguire un audit completo della documentazione esistente. Eliminare i duplicati, consolidare le versioni e stabilire un singolo repository ufficiale con un owner designato per ogni area tematica.

### Problema: i runbook richiedono troppo tempo per essere consultati durante un'emergenza

**Causa**: i runbook sono eccessivamente lunghi, mal strutturati o contengono troppe informazioni di contesto.
**Soluzione**: ristrutturare i runbook con un formato "comando-output-decisione" che permetta all'operatore di eseguire senza leggere paragrafi di testo. Spostare le informazioni di background in documenti di riferimento separati.

### Problema: le credenziali nei runbook sono scadute o errate

**Causa**: i runbook contengono credenziali hardcoded che non vengono aggiornate durante la rotazione delle password.
**Soluzione**: non inserire MAI credenziali direttamente nei runbook. Referenziare il password vault aziendale (es. "Recuperare le credenziali dal vault CyberArk, safe: IT-Operations, account: svc-backup"). In questo modo, la rotazione delle credenziali non invalida il runbook.

### Problema: l'approvazione delle procedure rallenta eccessivamente la pubblicazione

**Causa**: il workflow di approvazione e' troppo complesso o i responsabili non danno priorita' alle revisioni.
**Soluzione**: differenziare il livello di approvazione in base alla criticita' della procedura. Le procedure operative standard possono richiedere solo l'approvazione del team lead. Le procedure di sicurezza e disaster recovery richiedono approvazioni multiple. Stabilire un SLA per l'approvazione (es. 5 giorni lavorativi) e prevedere un meccanismo di escalation in caso di ritardo.

### Problema: difficolta' nel mantenere aggiornate le procedure durante progetti di migrazione

**Causa**: durante una migrazione infrastrutturale, i sistemi cambiano frequentemente e le procedure diventano obsolete rapidamente.
**Soluzione**: durante i progetti di migrazione, adottare un approccio "dual-track" mantenendo sia la procedura per il vecchio sistema che quella per il nuovo, chiaramente etichettate. Al completamento della migrazione, archiviare la procedura vecchia e consolidare quella nuova.

### Problema: le procedure non coprono gli scenari di errore

**Causa**: le procedure sono state scritte assumendo che ogni passo vada a buon fine (happy path).
**Soluzione**: per ogni passo critico, aggiungere una sezione "Se il risultato non e' quello atteso" con le azioni alternative. Includere i criteri di escalation chiari: a quale punto l'operatore deve fermarsi e chiamare un collega senior o il vendor.

---

## Change Management — Change Enablement

### SOP: Change Enablement (ITIL 4)

```
============================================================
STANDARD OPERATING PROCEDURE
============================================================

Codice:          SOP-CHG-001
Titolo:          Change Enablement — Gestione Modifiche Infrastrutturali
Versione:        2.0
Data creazione:  10/01/2025
Ultima modifica: 15/04/2026
Autore:          [Change Manager]
Owner:           Change Manager / IT Governance
Approvato da:    IT Director — 18/04/2026
Classificazione: Interna
Prossima revisione: 15/04/2027
```

**1. Scopo**

Definire il processo strutturato per la gestione di tutte le modifiche all'infrastruttura IT, ai servizi e alle applicazioni, garantendo che ogni change venga valutato, autorizzato, pianificato, implementato e revisionato in modo controllato. L'obiettivo primario e' minimizzare il rischio di interruzioni non pianificate derivanti da modifiche mal gestite, massimizzando al contempo la velocita' di delivery delle modifiche a basso rischio.

Con ITIL 4, la pratica di "Change Management" e' stata rinominata "Change Enablement" per riflettere un approccio piu' orientato al valore: non si tratta piu' semplicemente di controllare i cambiamenti, ma di abilitarli in modo sicuro e rapido.

**2. Ambito di applicazione**

Si applica a tutte le modifiche che impattano i Configuration Item (CI) registrati nel CMDB aziendale, inclusi:

- Modifiche hardware (server, storage, apparati di rete, endpoint)
- Modifiche software (installazione, aggiornamento, rimozione)
- Modifiche alla configurazione (parametri OS, servizi, policy, regole firewall)
- Modifiche infrastrutturali (rete, cablaggio, VLAN, DNS, DHCP)
- Modifiche applicative (rilascio nuove versioni, hotfix, patch custom)
- Modifiche ai processi automatizzati (scheduled task, script, job batch)

Escluse le modifiche operative standard pre-approvate (es. reset password utente, aggiunta di un utente a un gruppo pre-approvato), le quali sono classificate come Standard Change e seguono un percorso semplificato.

**3. Classificazione dei Change**

ITIL 4 classifica le modifiche in tre tipologie fondamentali:

| Tipologia | Rischio | Approvazione | Tempi | Esempio |
|---|---|---|---|---|
| **Standard Change** | Basso, ben compreso | Pre-approvata (nessuna approvazione real-time necessaria) | Immediata o secondo SLA | Reset password, aggiunta utente a gruppo esistente, sostituzione mouse/tastiera |
| **Normal Change** | Variabile (basso-alto) | Richiede valutazione e approvazione formale | Pianificata secondo calendario change | Upgrade firmware switch, installazione nuovo server, migrazione database |
| **Emergency Change** | Alto, urgente | Approvazione accelerata (ECAB) | Immediata, fuori finestra standard | Hotfix per vulnerabilita' zero-day, correzione critica in produzione |

**4. Procedura — Normal Change**

**Passo 1 — Registrazione della Request for Change (RFC)**

1. Il richiedente compila la RFC nel sistema ITSM inserendo:
   - Descrizione dettagliata della modifica proposta
   - Giustificazione di business / motivazione tecnica
   - CI impattati (consultare il CMDB)
   - Piano di implementazione con timeline stimata
   - Piano di rollback dettagliato
   - Valutazione dell'impatto e del rischio (utilizzare la matrice rischio/impatto)
   - Finestra di manutenzione proposta
   - Test eseguiti o pianificati

2. La RFC viene registrata con stato "Registrata" e assegnata al Change Manager per la revisione iniziale.

**Passo 2 — Valutazione e classificazione**

Il Change Manager valuta la RFC secondo i seguenti criteri:

```
CHECKLIST VALUTAZIONE RFC:

[ ] La descrizione e' sufficientemente dettagliata?
[ ] I CI impattati sono stati identificati correttamente nel CMDB?
[ ] Il piano di rollback e' realistico e testato?
[ ] La finestra di manutenzione e' appropriata?
[ ] Esistono conflitti con altri change pianificati? (consultare il calendario change)
[ ] L'impatto sugli SLA e' stato valutato?
[ ] Le risorse necessarie sono disponibili?
[ ] Il test pre-implementazione e' stato pianificato?
[ ] La comunicazione agli stakeholder e' stata pianificata?
[ ] Il rischio residuo e' accettabile?
```

Classificazione del rischio:

```
MATRICE RISCHIO / IMPATTO:

                    Impatto Basso    Impatto Medio    Impatto Alto
Probabilita' Alta  |   MEDIO       |    ALTO         |   CRITICO     |
Probabilita' Media |   BASSO       |    MEDIO        |   ALTO        |
Probabilita' Bassa |   BASSO       |    BASSO        |   MEDIO       |
```

**Passo 3 — Approvazione**

In base alla classificazione del rischio, la RFC viene sottoposta all'approvazione appropriata:

- **Rischio Basso**: approvazione del Change Manager
- **Rischio Medio**: approvazione del Change Manager + Technical Lead dell'area
- **Rischio Alto**: approvazione del Change Advisory Board (CAB)
- **Rischio Critico**: approvazione del CAB + IT Director + Business Owner

Il CAB si riunisce settimanalmente (tipicamente ogni martedi') per esaminare le RFC in coda. Per le RFC urgenti, e' possibile convocare una sessione CAB straordinaria.

**Passo 4 — Implementazione**

1. Verificare che tutti i prerequisiti siano soddisfatti (accessi, risorse, finestra di manutenzione confermata).
2. Comunicare l'inizio della manutenzione agli stakeholder secondo il piano di comunicazione.
3. Eseguire un backup/snapshot dei CI impattati prima di qualsiasi modifica.
4. Implementare la modifica seguendo il piano approvato nella RFC, passo per passo.
5. Eseguire le verifiche post-implementazione documentate nella RFC.
6. In caso di fallimento: attivare IMMEDIATAMENTE il piano di rollback. Non tentare fix improvvisati durante la finestra di manutenzione senza approvazione.

**Passo 5 — Post-Implementation Review (PIR)**

1. Verificare che la modifica funzioni come previsto.
2. Monitorare i sistemi per il periodo di "baking time" definito nella RFC (tipicamente 24-72 ore).
3. Aggiornare il CMDB con le nuove configurazioni.
4. Chiudere la RFC con stato "Completata con successo" o "Completata con problemi" o "Fallita/Rollback".
5. Per i change con problemi, aprire un ticket per le azioni correttive.
6. Documentare le lezioni apprese per il miglioramento continuo.

**5. Procedura — Emergency Change**

Gli Emergency Change seguono un percorso accelerato ma NON privo di controlli:

1. Il richiedente contatta il Change Manager (o il suo delegato on-call) telefonicamente.
2. Il Change Manager convoca l'Emergency CAB (ECAB) composto dal Change Manager, dal Technical Lead e dal responsabile del servizio impattato. La riunione puo' essere telefonica e durare 15 minuti.
3. L'ECAB autorizza verbalmente il change. La documentazione formale (RFC retroattiva) viene completata entro 24 ore lavorative dall'implementazione.
4. L'implementazione segue le stesse regole di backup, rollback e verifica dei Normal Change.
5. Nella successiva riunione CAB ordinaria, l'Emergency Change viene revisionato retrospettivamente.

ATTENZIONE: l'uso eccessivo di Emergency Change e' un indicatore di processi di pianificazione inadeguati. Piu' del 5% di Emergency Change sul totale mensile deve attivare una revisione del processo.

**6. Procedura — Standard Change**

1. Lo Standard Change deve avere un modello pre-approvato nel sistema ITSM che documenta: la procedura passo-passo, i rischi noti e le mitigazioni, i criteri di successo e il responsabile dell'esecuzione.
2. L'operatore seleziona il modello, compila i campi variabili (es. nome utente, nome server) e procede all'implementazione senza attendere approvazione.
3. Il completamento viene registrato automaticamente nel sistema ITSM.
4. I modelli di Standard Change vengono revisionati annualmente dal CAB.

**7. KPI del processo Change Enablement**

```
INDICATORI CHIAVE DI PRESTAZIONE:

- Change Success Rate:          target >= 95%
- Emergency Change Ratio:       target <= 5%
- Tempo medio approvazione RFC: target <= 3 giorni lavorativi
- Change con PIR completata:    target = 100% per High/Critical
- Change causa di incidente:    target <= 2% (Failed Change Rate)
- Backlog RFC non processate:   target <= 10
```

---

### Matrice di Approvazione per Tipo di Change

```
================================================================================
MATRICE DI APPROVAZIONE CHANGE
================================================================================

Tipo Change      | Rischio  | Approvatore 1      | Approvatore 2      | Approvatore 3
-----------------+----------+--------------------+--------------------+------------------
Standard         | Pre-appr | (nessuno)          | —                  | —
Normal - Basso   | Basso    | Change Manager     | —                  | —
Normal - Medio   | Medio    | Change Manager     | Technical Lead     | —
Normal - Alto    | Alto     | CAB (unanimita')   | —                  | —
Normal - Critico | Critico  | CAB                | IT Director        | Business Owner
Emergency        | Variab.  | ECAB (verbal)      | RFC retroattiva    | CAB review post.

================================================================================
FINESTRE DI MANUTENZIONE STANDARD
================================================================================

Tipo Ambiente     | Finestra Primaria           | Finestra Secondaria
------------------+-----------------------------+---------------------------
Produzione        | Sabato 02:00-06:00          | Domenica 02:00-06:00
Pre-produzione    | Mercoledi' 22:00-02:00      | Venerdi' 22:00-02:00
Test/Sviluppo     | Qualsiasi orario lavorativo | —
Rete/Infrastruttura| Domenica 02:00-06:00       | Su approvazione CAB

================================================================================
LEAD TIME MINIMI PER TIPO DI CHANGE
================================================================================

Tipo              | Lead Time Minimo     | Eccezioni
------------------+----------------------+---------------------------
Standard          | Nessuno              | —
Normal Basso      | 3 giorni lavorativi  | —
Normal Medio      | 5 giorni lavorativi  | —
Normal Alto       | 10 giorni lavorativi | CAB puo' abbreviare
Normal Critico    | 15 giorni lavorativi | IT Director puo' abbreviare
Emergency         | Immediato            | RFC retroattiva entro 24h
```

---

### Diagramma di Flusso — Normal Change

```
                    +---------------------+
                    |  RFC Registrata     |
                    +----------+----------+
                               |
                               v
                    +---------------------+
                    | Valutazione Change  |
                    | Manager             |
                    +----------+----------+
                               |
                    +----------+----------+
                    | Informazioni        |
              NO <--+ sufficienti?        +--> SI
              |     +---------------------+     |
              v                                 v
    +------------------+             +---------------------+
    | Richiedi         |             | Classificazione     |
    | integrazioni     |             | Rischio/Impatto     |
    +--------+---------+             +----------+----------+
             |                                  |
             +---> (torna a Valutazione)        v
                                     +---------------------+
                                     | Approvazione        |
                                     | (secondo matrice)   |
                                     +----------+----------+
                                                |
                                     +----------+----------+
                               NO <--+ Approvata?          +--> SI
                               |     +---------------------+     |
                               v                                 v
                    +------------------+             +---------------------+
                    | RFC Rifiutata    |             | Pianificazione      |
                    | (con motivo)     |             | Implementazione     |
                    +------------------+             +----------+----------+
                                                               |
                                                               v
                                                    +---------------------+
                                                    | Backup / Snapshot   |
                                                    +----------+----------+
                                                               |
                                                               v
                                                    +---------------------+
                                                    | Implementazione     |
                                                    +----------+----------+
                                                               |
                                                    +----------+----------+
                                              NO <--+ Successo?           +--> SI
                                              |     +---------------------+     |
                                              v                                 v
                                   +------------------+             +---------------------+
                                   | ROLLBACK         |             | Verifica post-impl  |
                                   | (piano approvato)|             +----------+----------+
                                   +--------+---------+                        |
                                            |                                  v
                                            v                       +---------------------+
                                   +------------------+             | Aggiornamento CMDB  |
                                   | Analisi causa    |             +----------+----------+
                                   | fallimento       |                        |
                                   +------------------+                        v
                                                                    +---------------------+
                                                                    | PIR + Chiusura RFC  |
                                                                    +---------------------+
```

---

## Release Management

### SOP: Release Management

```
============================================================
STANDARD OPERATING PROCEDURE
============================================================

Codice:          SOP-REL-001
Titolo:          Gestione Rilasci Applicativi in Produzione
Versione:        1.5
Data creazione:  05/03/2025
Ultima modifica: 20/04/2026
Autore:          [Release Manager]
Owner:           Release Manager / IT Operations
Approvato da:    IT Director — 22/04/2026
Classificazione: Interna
Prossima revisione: 20/04/2027
```

**1. Scopo**

Definire il processo end-to-end per la pianificazione, la costruzione, il test, il deployment e la revisione dei rilasci applicativi nell'ambiente di produzione. Il Release Management garantisce che le modifiche software vengano distribuite in modo controllato, minimizzando il rischio di regressioni e massimizzando la qualita' del servizio erogato agli utenti finali.

**2. Classificazione dei rilasci**

| Tipo | Descrizione | Frequenza tipica | Approvazione |
|---|---|---|---|
| **Major Release** | Nuove funzionalita' significative, cambiamenti architetturali, migrazioni | Trimestrale / Semestrale | CAB + Business Owner |
| **Minor Release** | Miglioramenti incrementali, correzioni non urgenti, ottimizzazioni | Mensile / Bisettimanale | Release Manager + Tech Lead |
| **Patch / Hotfix** | Correzioni critiche di bug, vulnerabilita' di sicurezza | Su necessita' (emergency) | ECAB (percorso accelerato) |

**3. Procedura — Ciclo di rilascio standard**

**Fase 1 — Pianificazione del rilascio (T-15 giorni lavorativi)**

1. Il Release Manager raccoglie le change request e le user story destinate al rilascio.
2. Definire il contenuto del rilascio (release manifest): elenco completo di tutte le modifiche incluse.
3. Identificare le dipendenze tra le modifiche e con altri rilasci pianificati.
4. Assegnare un release number secondo il formato Semantic Versioning: MAJOR.MINOR.PATCH.
5. Definire la finestra di rilascio e le risorse necessarie.
6. Creare il release plan nel sistema ITSM con link a tutte le RFC correlate.

**Fase 2 — Build e packaging (T-10 giorni lavorativi)**

1. Compilare e pacchettizzare gli artefatti del rilascio nell'ambiente di build.
2. Generare checksum (SHA-256) per ogni artefatto per la verifica di integrita'.
3. Taggare il codice sorgente nel sistema di version control (Git tag).
4. Documentare le istruzioni di deployment nel runbook di rilascio.
5. Documentare le istruzioni di rollback.

```bash
# Esempio: tagging del rilascio in Git
git tag -a v3.2.0 -m "Release 3.2.0 — Feature: nuovo modulo reportistica"
git push origin v3.2.0

# Generazione checksum artefatti
sha256sum webapp-3.2.0.tar.gz > webapp-3.2.0.tar.gz.sha256
```

**Fase 3 — Test in ambiente di staging (T-7 giorni lavorativi)**

1. Deployare il rilascio nell'ambiente di staging seguendo le istruzioni del runbook.
2. Eseguire la suite di test automatizzati (unit test, integration test, regression test).
3. Eseguire test manuali sulle funzionalita' critiche.
4. Eseguire test di performance / carico se il rilascio include modifiche significative.
5. Eseguire il test di rollback: verificare che il rollback funzioni correttamente in staging.
6. Documentare i risultati dei test nel release report.

**Fase 4 — User Acceptance Testing (UAT) (T-3 giorni lavorativi)**

1. Coinvolgere gli utenti di business designati per la validazione funzionale.
2. Fornire uno script di test con scenari predefiniti.
3. Raccogliere il sign-off formale dagli utenti di business (email o firma nel sistema ITSM).
4. In caso di difetti bloccanti: rinviare il rilascio e aprire ticket per le correzioni.

**Fase 5 — Go/No-Go Decision (T-1 giorno lavorativo)**

Riunione di Go/No-Go con: Release Manager, Technical Lead, QA Lead, Business Owner, Operations Lead.

**Fase 6 — Deployment in produzione (giorno D)**

1. Comunicare l'inizio del rilascio a tutti gli stakeholder.
2. Eseguire backup/snapshot dell'ambiente di produzione.
3. Deployare seguendo il runbook di rilascio, passo per passo.
4. Eseguire i test di verifica post-deployment (smoke test).
5. Monitorare i log e le metriche per anomalie.
6. Comunicare il completamento del rilascio.

Strategie di deployment:

```
STRATEGIE DI DEPLOYMENT DISPONIBILI:

1. Big Bang: tutto in una volta. Usare per rilasci minori a basso rischio.
2. Rolling: aggiornare un server/istanza alla volta nel pool.
3. Blue/Green: mantenere due ambienti identici, switchare il traffico.
4. Canary: rilasciare al 5-10% del traffico, monitorare, estendere.
5. Feature Flag: deployare il codice disabilitato, attivare via flag.

Strategia raccomandata per ambienti enterprise: Blue/Green o Canary.
```

**Fase 7 — Post-Release Review (D+3 giorni lavorativi)**

1. Analizzare le metriche post-rilascio: errori, performance, feedback utenti.
2. Documentare le lezioni apprese.
3. Aggiornare il release register.
4. Chiudere tutte le RFC correlate.

---

### Checklist Go/No-Go Release

```
============================================================
CHECKLIST GO/NO-GO — Release [Versione]
============================================================

Data riunione: _______________
Partecipanti: _______________

CRITERI DI GO (tutti devono essere soddisfatti):

[ ] Tutti i test automatizzati passano (0 fallimenti)
[ ] Test manuali completati con esito positivo
[ ] UAT sign-off ricevuto dal Business Owner
[ ] Nessun difetto bloccante (Sev 1) aperto
[ ] Difetti Sev 2 documentati con workaround o differiti al prossimo rilascio
[ ] Runbook di deployment revisionato e testato in staging
[ ] Runbook di rollback revisionato e testato in staging
[ ] Backup/snapshot pianificato prima del deployment
[ ] Finestra di manutenzione confermata e comunicata
[ ] Risorse tecniche disponibili durante il deployment
[ ] Piano di comunicazione pronto
[ ] Monitoraggio post-rilascio pianificato
[ ] RFC approvata dal CAB (per Major Release)
[ ] CMDB aggiornato con i CI che cambieranno

RISULTATO:    [ ] GO — Procedere con il rilascio
              [ ] NO-GO — Rinviare (motivazione: _____________)
              [ ] GO CONDIZIONATO — Procedere con riserva (condizioni: _____________)

Firma Release Manager: _______________
Firma Business Owner:  _______________
```

---

## Configuration Management e CMDB

### SOP: Gestione CMDB e Configuration Item

```
============================================================
STANDARD OPERATING PROCEDURE
============================================================

Codice:          SOP-CFG-001
Titolo:          Gestione CMDB e Ciclo di Vita dei Configuration Item
Versione:        1.8
Data creazione:  12/02/2025
Ultima modifica: 28/04/2026
Autore:          [Configuration Manager]
Owner:           Configuration Manager / IT Governance
Approvato da:    IT Director — 30/04/2026
Classificazione: Interna
Prossima revisione: 28/04/2027
```

**1. Scopo**

Il Configuration Management Database (CMDB) e' il repository centralizzato che contiene le informazioni su tutti i Configuration Item (CI) dell'infrastruttura IT e le relazioni tra di essi. Una CMDB accurata e' il prerequisito fondamentale per il funzionamento efficace di tutti gli altri processi ITSM: Incident Management, Problem Management, Change Enablement e Service Level Management dipendono tutti dalla qualita' dei dati nel CMDB.

Questa SOP definisce le procedure per la registrazione, l'aggiornamento, la verifica e la dismissione dei CI nel CMDB aziendale.

**2. Ambito — Tipologie di CI**

| Categoria CI | Esempi | Attributi chiave |
|---|---|---|
| Hardware — Server | Server fisici, blade, chassis | Serial number, modello, CPU, RAM, storage, rack, U position |
| Hardware — Network | Switch, router, firewall, AP, load balancer | Serial number, modello, firmware, porte, VLAN |
| Hardware — Endpoint | Laptop, desktop, thin client, stampanti | Serial number, asset tag, utente assegnato, modello |
| Infrastruttura virtuale | VM, container, vSwitch, datastore | Hypervisor host, vCPU, vRAM, vDisk, rete |
| Software | OS, applicazioni, middleware, database | Versione, licenza, vendor, data installazione |
| Servizi | Servizi IT erogati (email, ERP, CRM, VPN) | Owner, SLA, CI dipendenti |
| Documenti | Policy, SOP, contratti, licenze | Owner, data scadenza, stato |

**3. Procedura — Registrazione nuovo CI**

1. All'acquisizione o alla creazione di un nuovo asset/servizio, il responsabile apre una richiesta di registrazione CI nel sistema ITSM.
2. Compilare tutti gli attributi obbligatori del CI secondo lo schema della categoria corrispondente.
3. Definire le relazioni con gli altri CI:
   - "runs on" (es. applicazione runs on server)
   - "depends on" (es. servizio email depends on Exchange Server)
   - "connected to" (es. server connected to switch)
   - "managed by" (es. server managed by team infrastruttura)
4. Assegnare lo stato iniziale del CI: "In Preparazione" o "In Uso".
5. Il Configuration Manager verifica la completezza e l'accuratezza dei dati prima dell'approvazione.

**4. Procedura — Aggiornamento CI**

Ogni modifica significativa a un CI deve essere riflessa nel CMDB. I trigger per l'aggiornamento includono:

- Completamento di un Change approvato che impatta il CI
- Aggiornamento firmware/software
- Riassegnazione dell'asset a un diverso utente o reparto
- Cambio di stato (es. da "In Uso" a "In Manutenzione")
- Modifica della relazione con altri CI

```
STATI DEL CICLO DI VITA CI:

  Ordinato --> In Preparazione --> In Uso --> In Manutenzione --> Da Dismettere --> Dismesso
                                    ^              |
                                    |              |
                                    +--------------+
                                  (ritorno in servizio)
```

**5. Procedura — Discovery e riconciliazione**

1. Eseguire la scansione automatica della rete tramite strumenti di discovery (ServiceNow Discovery, Lansweeper, SCCM, Nmap) almeno settimanalmente.
2. Confrontare i risultati della discovery con i dati presenti nel CMDB.
3. Identificare le discrepanze:
   - CI presenti nella discovery ma non nel CMDB ("CI fantasma" — shadow IT)
   - CI presenti nel CMDB ma non nella discovery ("CI orfano" — potenziale asset dismesso non aggiornato)
4. Per ogni discrepanza, aprire un ticket di investigazione e correzione.

**6. Audit CMDB**

| Tipo audit | Frequenza | Responsabile | Obiettivo |
|---|---|---|---|
| Audit automatizzato (discovery) | Settimanale | Configuration Manager | Identificare discrepanze |
| Audit a campione manuale | Mensile | Team Operations | Verificare 10% dei CI critici |
| Audit completo | Annuale | Configuration Manager + Audit IT | Verifica totale accuratezza |

Metriche di qualita' CMDB:

```
METRICHE CMDB:

- Completezza attributi:    target >= 95%
- Accuratezza dati:         target >= 98%
- CI con relazioni mappate: target >= 90%
- CI orfani:                target <= 2%
- CI fantasma:              target <= 1%
- Tempo medio aggiornamento post-change: target <= 24 ore
```

---

## Service Request Fulfillment

### SOP: Evasione Richieste di Servizio

```
============================================================
STANDARD OPERATING PROCEDURE
============================================================

Codice:          SOP-SRF-001
Titolo:          Evasione Richieste di Servizio IT
Versione:        1.4
Data creazione:  20/01/2025
Ultima modifica: 05/05/2026
Autore:          [Service Desk Manager]
Owner:           Service Desk Manager / IT Operations
Approvato da:    IT Manager — 07/05/2026
Classificazione: Interna
Prossima revisione: 05/05/2027
```

**1. Scopo**

Definire il processo per la gestione e l'evasione delle richieste di servizio IT, dalla ricezione alla chiusura. Le richieste di servizio (Service Request) sono attivita' a basso rischio, pre-definite e ripetitive che vengono evase dal Service Desk o dai team di supporto. A differenza degli incidenti, le richieste di servizio non rappresentano un degrado o un'interruzione del servizio, ma una necessita' operativa dell'utente.

In ITIL 4, questa pratica e' denominata "Service Request Management" e si focalizza sulla velocita', la trasparenza e l'esperienza utente.

**2. Catalogo delle richieste di servizio**

Il Service Catalog definisce tutte le richieste disponibili, i tempi di evasione e le approvazioni necessarie:

```
================================================================================
CATALOGO RICHIESTE DI SERVIZIO (estratto)
================================================================================

Codice    | Richiesta                        | SLA          | Approvazione
----------+----------------------------------+--------------+----------------
SR-ACC-01 | Creazione account utente         | 2 gg lav     | HR + Manager
SR-ACC-02 | Reset password                   | 30 minuti    | Nessuna (self-service)
SR-ACC-03 | Modifica permessi / gruppi       | 1 gg lav     | Manager utente
SR-ACC-04 | Accesso VPN                      | 1 gg lav     | Manager + Sicurezza IT
SR-HW-01  | Richiesta nuova workstation      | 5 gg lav     | Manager + IT Manager
SR-HW-02  | Sostituzione periferica          | 2 gg lav     | Nessuna
SR-HW-03  | Richiesta monitor aggiuntivo     | 3 gg lav     | Manager
SR-SW-01  | Installazione software standard  | 1 gg lav     | Nessuna (dal catalogo)
SR-SW-02  | Installazione software custom    | 3 gg lav     | Manager + Sicurezza IT
SR-SW-03  | Licenza software aggiuntiva      | 5 gg lav     | Manager + IT Manager
SR-NET-01 | Configurazione stampante di rete | 1 gg lav     | Nessuna
SR-NET-02 | Richiesta porta di rete          | 3 gg lav     | Networking Team
SR-MOB-01 | Provisioning dispositivo mobile  | 3 gg lav     | Manager + Sicurezza IT
SR-INF-01 | Richiesta nuova casella email     | 1 gg lav     | Manager
SR-INF-02 | Creazione lista di distribuzione | 1 gg lav     | Manager
SR-INF-03 | Richiesta spazio storage         | 2 gg lav     | Manager + Infrastruttura
```

**3. Procedura di evasione**

**Passo 1 — Ricezione e registrazione**

1. L'utente sottomette la richiesta tramite il portale self-service (canale preferenziale), email, telefono o chat.
2. Il Service Desk registra la richiesta nel sistema ITSM con: identificativo utente, codice richiesta dal catalogo, dettagli specifici, priorita'.
3. L'utente riceve una conferma automatica con il numero di ticket e i tempi di evasione previsti.

**Passo 2 — Categorizzazione e routing**

1. Il sistema ITSM categorizza automaticamente la richiesta in base al codice selezionato.
2. Se e' richiesta un'approvazione, il ticket viene automaticamente inoltrato all'approvatore.
3. L'approvatore ha un SLA di 24 ore lavorative per approvare o rifiutare.
4. Una volta approvata (o se non richiede approvazione), la richiesta viene assegnata al gruppo di evasione competente.

**Passo 3 — Evasione**

1. Il tecnico assegnato esegue la richiesta seguendo la SOP specifica (es. SOP-IAM-001 per creazione utente).
2. Documentare nel ticket tutte le azioni eseguite.
3. In caso di impedimenti, comunicare immediatamente all'utente il ritardo e la nuova data prevista.

**Passo 4 — Verifica e chiusura**

1. Verificare che la richiesta sia stata completata correttamente.
2. Contattare l'utente per confermare la soddisfazione.
3. Chiudere il ticket con le note di completamento.
4. L'utente riceve un sondaggio automatico di soddisfazione (CSAT).

**4. KPI Service Request Management**

```
INDICATORI:

- SLA rispettati:               target >= 95%
- First Contact Resolution:     target >= 40% (richieste risolte al primo contatto)
- Tempo medio evasione:         target <= SLA definito per categoria
- CSAT (soddisfazione utente):  target >= 4.0 / 5.0
- Richieste self-service:       target >= 60% del totale (shift-left)
- Backlog richieste aperte:     target <= 20
```

---

## Ricertificazione Accessi e Compliance

### SOP: Access Review e Ricertificazione

```
============================================================
STANDARD OPERATING PROCEDURE
============================================================

Codice:          SOP-IAM-006
Titolo:          Access Review e Ricertificazione Periodica degli Accessi
Versione:        1.3
Data creazione:  01/04/2025
Ultima modifica: 10/05/2026
Autore:          [Security Analyst]
Owner:           CISO / Responsabile Sicurezza IT
Approvato da:    CISO — 12/05/2026
Classificazione: Riservata
Prossima revisione: 10/11/2026 (semestrale)
```

**1. Scopo**

Garantire che tutti gli accessi ai sistemi IT aziendali siano appropriati, aggiornati e conformi al principio del minimo privilegio (Least Privilege). La ricertificazione periodica e' un requisito di sicurezza fondamentale e un obbligo normativo per organizzazioni soggette a SOX, GDPR, ISO 27001, PCI-DSS e altre normative di settore.

**2. Frequenza di ricertificazione**

| Categoria di accesso | Frequenza | Normativa di riferimento |
|---|---|---|
| Account privilegiati (admin, DBA, root) | Trimestrale | SOX ITGC, ISO 27001 |
| Accesso a dati personali (PII/dati sensibili) | Trimestrale | GDPR Art. 5, 32 |
| Accesso applicazioni critiche (ERP, CRM, HR) | Semestrale | SOX ITGC |
| Accesso standard (email, file share, intranet) | Annuale | Policy aziendale |
| Account di servizio | Semestrale | SOX ITGC, best practice |
| Account di fornitori / terze parti | Trimestrale | ISO 27001, GDPR |

**3. Procedura**

**Passo 1 — Estrazione dei dati di accesso (T-10 giorni lavorativi prima della deadline)**

```powershell
# Estrarre tutti gli utenti e le loro appartenenze ai gruppi AD
Get-ADUser -Filter {Enabled -eq $true} -Properties MemberOf, LastLogonDate, Department, Manager |
    Select-Object SamAccountName, Name, Department,
    @{N='Manager';E={(Get-ADUser $_.Manager -ErrorAction SilentlyContinue).Name}},
    @{N='Groups';E={($_.MemberOf | ForEach-Object { (Get-ADGroup $_).Name }) -join '; '}},
    LastLogonDate |
    Export-Csv "C:\AccessReview\UserAccess_$(Get-Date -Format 'yyyyMMdd').csv" -NoTypeInformation -Encoding UTF8

# Identificare account inattivi (nessun login da 90+ giorni)
Get-ADUser -Filter {Enabled -eq $true -and LastLogonDate -lt $((Get-Date).AddDays(-90))} -Properties LastLogonDate |
    Select-Object SamAccountName, Name, LastLogonDate |
    Export-Csv "C:\AccessReview\InactiveAccounts_$(Get-Date -Format 'yyyyMMdd').csv" -NoTypeInformation
```

**Passo 2 — Distribuzione ai revisori**

1. Per ogni reparto/business unit, inviare al manager responsabile l'elenco degli utenti del proprio team con i relativi accessi.
2. Includere nel pacchetto di revisione:
   - Elenco utenti attivi con gruppi e permessi
   - Elenco account inattivi (90+ giorni senza login)
   - Elenco account di fornitori/terze parti con data scadenza contratto
3. Stabilire la deadline per la revisione (tipicamente 10 giorni lavorativi).

**Passo 3 — Revisione da parte dei manager**

Il manager deve rispondere per ogni utente/accesso con una delle seguenti azioni:

```
AZIONI DI RICERTIFICAZIONE:

[CONFERMA]  - L'accesso e' appropriato, l'utente ne ha ancora bisogno
[REVOCA]    - L'accesso non e' piu' necessario, rimuovere
[MODIFICA]  - L'accesso necessita di modifica (specificare)
[ESCALATION]- Non ho visibilita' sufficiente, escalare al livello superiore
```

**Passo 4 — Applicazione delle decisioni**

1. Per ogni decisione di REVOCA: disabilitare l'accesso entro 5 giorni lavorativi dalla decisione.
2. Per ogni decisione di MODIFICA: aggiornare i permessi entro 5 giorni lavorativi.
3. Per gli account inattivi senza giustificazione: disabilitare immediatamente.
4. Documentare ogni azione nel sistema ITSM.

**Passo 5 — Documentazione di audit**

Per ogni ciclo di ricertificazione, produrre e archiviare:

```
DOCUMENTAZIONE AUDIT ACCESS REVIEW:

[ ] Report completo degli accessi revisionati
[ ] Registro delle decisioni prese (con nome revisore e timestamp)
[ ] Evidenza delle azioni di revoca/modifica applicate
[ ] Elenco eccezioni (accessi non revisionati con giustificazione)
[ ] Attestazione firmata dal CISO sulla completezza della revisione
[ ] Report riepilogativo con metriche (% revisionato, % revocato, % confermato)
```

Conservare la documentazione per almeno 7 anni (requisito SOX) o per il periodo previsto dalla policy di data retention aziendale.

---

## Decommissioning Asset IT

### SOP: Dismissione e Smaltimento Asset IT

```
============================================================
STANDARD OPERATING PROCEDURE
============================================================

Codice:          SOP-AST-001
Titolo:          Dismissione e Smaltimento Sicuro Asset IT
Versione:        1.6
Data creazione:  15/03/2025
Ultima modifica: 12/05/2026
Autore:          [Asset Manager]
Owner:           Responsabile IT Operations / DPO
Approvato da:    IT Manager + DPO — 14/05/2026
Classificazione: Interna
Prossima revisione: 12/05/2027
```

**1. Scopo**

Definire il processo per la dismissione sicura degli asset IT giunti a fine vita (End-of-Life), garantendo la protezione dei dati residenti sui dispositivi, la conformita' normativa (GDPR, normativa ambientale RAEE) e la corretta registrazione contabile.

**2. Procedura**

**Passo 1 — Identificazione e autorizzazione dismissione**

1. Identificare gli asset candidati alla dismissione in base a:
   - Eta' superiore alla vita utile definita dalla policy (tipicamente 4-5 anni per laptop, 5-7 anni per server)
   - Stato di fine supporto del vendor (EoL / EoS)
   - Guasto irreparabile o costo di riparazione superiore al 60% del valore di sostituzione
   - Requisiti di performance non piu' soddisfatti
2. Ottenere l'approvazione del responsabile IT e del responsabile finanziario.
3. Aprire un ticket di dismissione nel sistema ITSM.

**Passo 2 — Backup dati**

1. Verificare che tutti i dati utili siano stati trasferiti o archiviati.
2. Eseguire un backup finale del dispositivo come misura precauzionale.
3. Documentare nel ticket la conferma che nessun dato critico rimane esclusivamente sull'asset da dismettere.

**Passo 3 — Sanitizzazione dati**

CRITICO: la sanitizzazione dei dati deve seguire standard riconosciuti per garantire l'irrecuperabilita' dei dati.

```
METODI DI SANITIZZAZIONE PER TIPO DI SUPPORTO:

Tipo supporto   | Metodo                           | Standard di riferimento
-----------------+----------------------------------+---------------------------
HDD magnetici   | Sovrascrittura 3 passaggi         | NIST SP 800-88 Rev. 1 (Clear)
                 | oppure Degaussing                 | NIST SP 800-88 Rev. 1 (Purge)
                 | oppure Distruzione fisica         | NIST SP 800-88 Rev. 1 (Destroy)
SSD / NVMe      | Secure Erase (comando ATA)        | NIST SP 800-88 Rev. 1
                 | oppure Crypto Erase               | Dove disponibile (SED)
                 | oppure Distruzione fisica         | Per dati classificati
Dispositivi mob. | Factory Reset + MDM Wipe          | Combinato per massima sicurezza
Nastri backup   | Degaussing o distruzione fisica   | NIST SP 800-88 Rev. 1
```

```bash
# Esempio sanitizzazione con shred (Linux)
shred -vfz -n 3 /dev/sda

# Esempio con nwipe (strumento dedicato, standard NIST)
nwipe --autonuke --method=dodshort /dev/sda
```

```powershell
# Windows — Cancellazione sicura prima della formattazione
# Utilizzare strumenti come Eraser, DBAN (boot da USB) o il comando cipher
cipher /w:C:\
```

**Passo 4 — Segregazione fisica**

1. Spostare fisicamente l'asset in un'area dedicata ("Magazzino dismissione"), separata dagli asset attivi.
2. L'area deve essere ad accesso controllato per prevenire furti di componenti o accesso non autorizzato ai dati residui.

**Passo 5 — Aggiornamento CMDB e contabilita'**

1. Aggiornare lo stato del CI nel CMDB a "Dismesso".
2. Rimuovere le relazioni con altri CI attivi.
3. Notificare il reparto Amministrazione per l'aggiornamento del registro cespiti.
4. Revocare eventuali licenze software associate all'asset.

**Passo 6 — Smaltimento**

1. Affidare lo smaltimento esclusivamente a fornitori certificati (R2, e-Stewards, RAEE).
2. Ottenere dal fornitore il certificato di distruzione per ogni asset smaltito.
3. Archiviare i certificati di distruzione per almeno 7 anni.
4. Per asset riutilizzabili internamente: ricondizionare e reinserire nell'inventario con stato "Disponibile — Ricondizionato".

**7. Checklist dismissione**

```
CHECKLIST DISMISSIONE ASSET:

[ ] Approvazione dismissione ottenuta
[ ] Backup dati finale completato
[ ] Sanitizzazione dati eseguita (metodo: _____________)
[ ] Certificato sanitizzazione generato (tool: _____________)
[ ] Asset segregato fisicamente
[ ] CMDB aggiornato (stato: Dismesso)
[ ] Registro cespiti aggiornato
[ ] Licenze software revocate
[ ] Smaltimento affidato a fornitore certificato
[ ] Certificato di distruzione ricevuto e archiviato
[ ] Ticket ITSM chiuso con documentazione completa
```

---

## Capacity Planning e Performance Management

### SOP: Capacity Planning

```
============================================================
STANDARD OPERATING PROCEDURE
============================================================

Codice:          SOP-CAP-001
Titolo:          Capacity Planning e Monitoraggio Performance
Versione:        1.2
Data creazione:  01/06/2025
Ultima modifica: 20/05/2026
Autore:          [Infrastructure Engineer]
Owner:           Responsabile Infrastruttura
Approvato da:    IT Director — 22/05/2026
Classificazione: Interna
Prossima revisione: 20/05/2027
```

**1. Scopo**

Garantire che l'infrastruttura IT disponga di capacita' sufficiente per soddisfare le esigenze attuali e future del business, prevenendo sia il sotto-dimensionamento (che causa degradazione del servizio) sia il sovra-dimensionamento (che genera sprechi di budget).

**2. Procedura — Monitoraggio continuo**

**Metriche chiave da monitorare:**

```
================================================================================
SOGLIE DI ALLERTA PER RISORSA
================================================================================

Risorsa          | Warning (giallo)   | Critical (rosso)   | Azione
-----------------+--------------------+--------------------+-------------------------
CPU              | Utilizzo > 75%     | Utilizzo > 90%     | Analisi processi / scaling
                 | per > 15 min       | per > 5 min        |
RAM              | Utilizzo > 80%     | Utilizzo > 95%     | Analisi leak / scaling
                 | sostenuto          | o swap > 50%       |
Disco            | Occupazione > 80%  | Occupazione > 90%  | Cleanup / espansione
                 |                    |                    |
Rete             | Utilizzo banda > 70%| Utilizzo > 90%    | QoS / upgrade link
                 |                    |                    |
Connessioni DB   | Pool > 75%         | Pool > 90%         | Ottimizzazione query
                 |                    |                    |
Code messaggi    | Lunghezza > 1000   | Lunghezza > 5000   | Scaling consumer
                 |                    |                    |
```

**Attivita' mensile — Report capacita'**

1. Raccogliere i dati di utilizzo medio e di picco per tutti i sistemi critici.
2. Identificare i sistemi con trend di crescita che raggiungeranno le soglie critiche nei prossimi 3-6 mesi.
3. Produrre il report di capacity con raccomandazioni.
4. Presentare il report al management per le decisioni di investimento.

**Attivita' trimestrale — Forecasting**

1. Analizzare i trend storici di utilizzo (12-24 mesi).
2. Integrare le previsioni di crescita del business (nuovi progetti, nuove assunzioni, picchi stagionali).
3. Calcolare la capacita' necessaria futura con margine del 20% (headroom).
4. Identificare i gap e proporre le azioni correttive (scaling verticale, orizzontale, ottimizzazione, decommissioning risorse sottoutilizzate).

---

## Knowledge Management

### SOP: Gestione della Conoscenza (KCS)

```
============================================================
STANDARD OPERATING PROCEDURE
============================================================

Codice:          SOP-KM-001
Titolo:          Knowledge Management — Metodologia KCS
Versione:        1.0
Data creazione:  10/05/2025
Ultima modifica: 18/05/2026
Autore:          [Knowledge Manager]
Owner:           Service Desk Manager
Approvato da:    IT Manager — 20/05/2026
Classificazione: Interna
Prossima revisione: 18/05/2027
```

**1. Scopo**

Implementare un processo strutturato di gestione della conoscenza basato sulla metodologia KCS (Knowledge-Centered Service), integrando la creazione e l'aggiornamento degli articoli di knowledge base direttamente nel flusso di lavoro di risoluzione dei ticket. L'obiettivo e' ridurre i tempi di risoluzione, abilitare il self-service degli utenti e preservare la conoscenza organizzativa.

**2. Principi KCS**

A differenza del knowledge management tradizionale — dove pochi esperti creano articoli "a priori" — KCS adotta un modello collaborativo in cui ogni operatore del Service Desk contribuisce alla knowledge base come parte integrante della risoluzione dei ticket.

**3. Procedura — Ciclo di vita articolo KCS**

**Passo 1 — Cattura (durante la risoluzione del ticket)**

1. Quando un tecnico risolve un ticket, verificare se esiste gia' un articolo nella knowledge base che copre il problema.
2. Se esiste: linkare l'articolo al ticket. Se la soluzione applicata e' diversa o piu' aggiornata, aggiornare l'articolo.
3. Se non esiste: creare un nuovo articolo utilizzando il template standard.

**Template articolo KCS:**

```
============================================================
KNOWLEDGE BASE ARTICLE
============================================================

ID:              KB-[NUMERO]
Titolo:          [Titolo descrittivo del problema/soluzione]
Stato:           [Bozza / Revisionato / Pubblicato / Archiviato]
Categoria:       [Hardware / Software / Rete / Account / Sicurezza]
Pubblico:        [Interno / Self-Service (visibile agli utenti)]
Data creazione:  [GG/MM/AAAA]
Ultima modifica: [GG/MM/AAAA]
Autore:          [Nome]
Revisore:        [Nome]
Ticket correlati: [INC-xxxxx, SR-xxxxx]

------------------------------------------------------------
SINTOMO / PROBLEMA
------------------------------------------------------------
Descrivere il problema come lo riporta l'utente o come
si manifesta nel monitoraggio. Utilizzare le parole chiave
che l'utente userebbe per cercare questo articolo.

------------------------------------------------------------
AMBIENTE
------------------------------------------------------------
Sistema operativo, applicazione, versione, configurazione
specifica in cui si manifesta il problema.

------------------------------------------------------------
CAUSA
------------------------------------------------------------
Causa radice del problema (se nota). Se la causa non e'
nota, indicare "In indagine" e aggiornare quando disponibile.

------------------------------------------------------------
SOLUZIONE
------------------------------------------------------------
Passi dettagliati per risolvere il problema.
Includere comandi copia-incolla pronti all'uso.
Includere screenshot se utili.

------------------------------------------------------------
WORKAROUND
------------------------------------------------------------
Soluzione temporanea (se disponibile) da utilizzare
finche' la soluzione definitiva non e' implementata.

------------------------------------------------------------
ARTICOLI CORRELATI
------------------------------------------------------------
Link ad altri articoli della knowledge base correlati.
```

**Passo 2 — Strutturazione**

1. Redigere l'articolo con un linguaggio chiaro e orientato alla ricerca (pensare alle parole chiave che un tecnico o un utente userebbe per trovarlo).
2. Separare chiaramente: sintomo, causa, soluzione, workaround.
3. Includere comandi e screenshot dove appropriato.

**Passo 3 — Revisione e pubblicazione**

| Stato | Visibilita' | Chi puo' modificare |
|---|---|---|
| Bozza | Solo autore e revisori | Autore |
| Revisionato | Team interno IT | Autore + revisore assegnato |
| Pubblicato (interno) | Tutto il team IT | Knowledge Manager |
| Pubblicato (self-service) | Utenti finali | Knowledge Manager |
| Archiviato | Non visibile | Knowledge Manager (puo' riattivare) |

**Passo 4 — Miglioramento continuo**

1. Monitorare le metriche di utilizzo degli articoli: visualizzazioni, link da ticket, feedback utenti.
2. Gli articoli non utilizzati da 12+ mesi vengono marcati per revisione: archiviare o aggiornare.
3. Gli articoli con feedback negativo vengono assegnati per la correzione.

**4. KPI Knowledge Management**

```
METRICHE KCS:

- Ticket con articolo KB linkato:              target >= 60%
- Articoli creati/aggiornati per mese:         trend crescente
- First Contact Resolution con KB:             target >= 50%
- Ticket risolti via self-service:              target >= 25%
- Articoli con feedback positivo:              target >= 80%
- Tempo medio risoluzione con KB vs senza KB:  riduzione >= 30%
```

---

## Runbook Aggiuntivi

### Runbook: Major Incident Management

```
============================================================
RUNBOOK
============================================================
Codice:          RB-INC-001
Titolo:          Gestione Major Incident
Versione:        1.5
Ultima modifica: 10/05/2026
Classificazione: Interna
============================================================
```

**Trigger**: Un incidente viene classificato come Major Incident quando soddisfa almeno uno dei seguenti criteri: interruzione completa di un servizio critico, impatto su piu' del 25% degli utenti, violazione di SLA su un servizio classificato come Tier 1, potenziale impatto finanziario superiore a EUR 50.000, rischio reputazionale significativo.

**FASE 1 — Dichiarazione Major Incident (entro 15 minuti)**

1. Il Service Desk o il sistema di monitoraggio identifica un incidente con impatto elevato.
2. Il Service Desk Manager (o l'on-call manager) dichiara formalmente il Major Incident.
3. Attivare il protocollo di Major Incident:

```
ATTIVAZIONE MAJOR INCIDENT:

1. Nominare l'Incident Commander (IC)
   L'IC e' il punto di coordinamento unico. Tutte le comunicazioni
   passano attraverso l'IC. L'IC NON risolve il problema — coordina.

2. Aprire il bridge di comunicazione (war room virtuale):
   - Canale Teams/Slack dedicato: #major-incident-YYMMDD-NNN
   - Conference call permanente per i tecnici

3. Attivare il team di risoluzione:
   - Tecnici specialisti per l'area impattata
   - DBA (se coinvolti database)
   - Networking (se coinvolta la rete)
   - Security (se sospettata componente di sicurezza)

4. Attivare il flusso di comunicazione:
   - Stakeholder interni: aggiornamento ogni 30 minuti
   - Management: aggiornamento ogni 60 minuti
   - Utenti: aggiornamento alla dichiarazione, alla risoluzione,
     e ogni 2 ore nel frattempo
```

**FASE 2 — Diagnosi e risoluzione**

1. L'IC coordina la diagnosi, assegnando task specifici ai tecnici.
2. Ogni tecnico riporta i risultati all'IC, non direttamente agli stakeholder.
3. L'IC mantiene un log cronologico di tutte le azioni intraprese con timestamp.
4. L'obiettivo primario e' il ripristino del servizio, anche con workaround temporanei. La root cause analysis avviene DOPO il ripristino.
5. L'IC puo' decidere di escalare funzionalmente (coinvolgere tecnici piu' specializzati) o gerarchicamente (coinvolgere il management per decisioni di business).

**FASE 3 — Risoluzione e ripristino**

1. Applicare la soluzione/workaround identificata.
2. Verificare il ripristino del servizio da piu' punti di osservazione.
3. Monitorare la stabilita' per almeno 30 minuti.
4. L'IC dichiara la chiusura del Major Incident.
5. Comunicare il ripristino a tutti gli stakeholder.

**FASE 4 — Post-Incident Review (PIR)**

Entro 5 giorni lavorativi dalla risoluzione, l'IC convoca la PIR con tutti i partecipanti. La PIR deve produrre:

```
TEMPLATE POST-INCIDENT REVIEW:

1. RIEPILOGO INCIDENTE
   - Servizio impattato: _______________
   - Durata totale: da [HH:MM] a [HH:MM] = [XX ore, YY minuti]
   - Utenti impattati: _______________
   - Impatto business stimato: _______________

2. TIMELINE DETTAGLIATA
   [HH:MM] Evento / Azione presa
   [HH:MM] ...

3. ROOT CAUSE
   Causa radice identificata: _______________
   Categoria: [Errore umano / Bug software / Guasto hardware /
              Problema di rete / Problema di configurazione /
              Capacita' insufficiente / Terza parte / Sconosciuta]

4. COSA HA FUNZIONATO BENE
   - _______________

5. COSA DEVE MIGLIORARE
   - _______________

6. AZIONI CORRETTIVE
   # | Azione                    | Responsabile | Scadenza  | Stato
   1 | [descrizione]             | [nome]       | [data]    | [aperto]
   2 | ...                       | ...          | ...       | ...
```

---

### Runbook: DR Testing — Esercitazione Disaster Recovery

```
============================================================
RUNBOOK
============================================================
Codice:          RB-DR-001
Titolo:          Esercitazione Pianificata di Disaster Recovery
Versione:        1.3
Ultima modifica: 15/05/2026
Classificazione: Riservata
============================================================
```

**Trigger**: Esercitazione pianificata secondo il calendario annuale DR (minimo 2 volte/anno) o a seguito di modifiche significative all'infrastruttura che richiedono la validazione del piano DR.

**Tipologie di test DR**

| Tipo | Complessita' | Frequenza | Coinvolgimento |
|---|---|---|---|
| Tabletop Exercise | Bassa | Trimestrale | Discussione teorica — team IT + business |
| Walkthrough Test | Media | Semestrale | Revisione step-by-step delle procedure |
| Simulation Test | Alta | Annuale | Test parziale dei sistemi di recovery |
| Full-Scale Test | Molto alta | Annuale (almeno 1) | Recovery completo in ambiente isolato |

**Procedura — Full-Scale DR Test**

**Fase 1 — Pianificazione (T-30 giorni)**

1. Definire lo scenario di disastro simulato (es. "perdita completa del data center primario").
2. Identificare i sistemi da includere nel test (in base alla criticita' BIA).
3. Stabilire gli obiettivi misurabili: RTO target, RPO target per ogni sistema.
4. Coordinare con i team tecnici e il business la data e la finestra temporale.
5. Preparare l'ambiente di recovery (sito DR, cloud DR, infrastruttura secondaria).
6. Comunicare il piano a tutti i partecipanti.

**Fase 2 — Esecuzione (giorno D)**

1. L'esercitazione inizia con la simulazione della dichiarazione di disastro.
2. I team attivano le procedure documentate nel piano DR — senza accesso al data center primario (simulato).
3. Per ogni sistema critico:
   - Avviare il ripristino da backup/replica seguendo il runbook specifico.
   - Misurare il tempo effettivo di ripristino (RTA — Recovery Time Actual).
   - Verificare l'integrita' dei dati ripristinati.
   - Verificare la funzionalita' delle applicazioni.
4. Documentare ogni passo con timestamp, successi, fallimenti e deviazioni dalle procedure.

**Fase 3 — Valutazione risultati**

```
TEMPLATE REPORT DR TEST:

Sistema          | RTO Target | RTA Effettivo | RPO Target | RPO Effettivo | Esito
-----------------+------------+---------------+------------+---------------+--------
Email (Exchange) | 4 ore      | [misurato]    | 1 ora      | [misurato]    | OK/KO
ERP              | 8 ore      | [misurato]    | 4 ore      | [misurato]    | OK/KO
Database SQL     | 2 ore      | [misurato]    | 15 min     | [misurato]    | OK/KO
File Server      | 6 ore      | [misurato]    | 24 ore     | [misurato]    | OK/KO
Active Directory | 1 ora      | [misurato]    | 0 (replica)| [misurato]    | OK/KO

Gap identificati:
1. _______________
2. _______________

Azioni correttive:
1. _______________
2. _______________
```

---

### Runbook: Emergenza Spazio Disco

```
============================================================
RUNBOOK
============================================================
Codice:          RB-SRV-002
Titolo:          Emergenza Spazio Disco Server
Versione:        1.4
Ultima modifica: 12/05/2026
Classificazione: Interna
============================================================
```

**Trigger**: Alert di monitoraggio indica che un volume ha superato il 90% di occupazione, oppure un servizio sta fallendo con errore "disk full" / "no space left on device".

**Procedura — Windows**

```powershell
# 1. Verificare lo spazio disponibile
Get-WmiObject Win32_LogicalDisk -ComputerName "MI-SRV-01" |
    Select-Object DeviceID, @{N='Size_GB';E={[math]::Round($_.Size/1GB,2)}},
    @{N='Free_GB';E={[math]::Round($_.FreeSpace/1GB,2)}},
    @{N='Used_Pct';E={[math]::Round(($_.Size-$_.FreeSpace)/$_.Size*100,1)}}

# 2. Identificare i file/cartelle piu' grandi
# PowerShell — top 20 file piu' grandi
Get-ChildItem -Path "C:\" -Recurse -ErrorAction SilentlyContinue |
    Sort-Object Length -Descending |
    Select-Object -First 20 FullName, @{N='Size_MB';E={[math]::Round($_.Length/1MB,2)}}

# 3. Azioni di cleanup sicure (in ordine di priorita')
# a. Svuotare la cartella temp
Remove-Item -Path "C:\Windows\Temp\*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "$env:TEMP\*" -Recurse -Force -ErrorAction SilentlyContinue

# b. Pulire i log vecchi (conservare ultimi 30 giorni)
Get-ChildItem -Path "D:\Logs\" -Recurse -File |
    Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } |
    Remove-Item -Force

# c. Comprimere i log che devono essere conservati
Compress-Archive -Path "D:\Logs\2025\*" -DestinationPath "D:\Archive\Logs_2025.zip"

# d. Svuotare il cestino
Clear-RecycleBin -Force -ErrorAction SilentlyContinue

# e. Pulire Windows Update cache (se applicabile e non in fase di patching)
Stop-Service -Name wuauserv
Remove-Item -Path "C:\Windows\SoftwareDistribution\Download\*" -Recurse -Force
Start-Service -Name wuauserv

# 4. Verificare lo spazio recuperato
Get-WmiObject Win32_LogicalDisk -ComputerName "MI-SRV-01" |
    Select-Object DeviceID, @{N='Free_GB';E={[math]::Round($_.FreeSpace/1GB,2)}}
```

**Procedura — Linux**

```bash
# 1. Verificare lo spazio disponibile
df -h

# 2. Identificare le directory piu' grandi
du -sh /* 2>/dev/null | sort -rh | head -20
du -sh /var/* 2>/dev/null | sort -rh | head -10

# 3. Cercare file grandi (> 100MB)
find / -xdev -type f -size +100M -exec ls -lh {} \; 2>/dev/null | sort -k5 -rh | head -20

# 4. Verificare i file cancellati ma ancora aperti (spazio non rilasciato)
lsof +D / 2>/dev/null | grep deleted

# 5. Azioni di cleanup sicure
# a. Ruotare e pulire i log
journalctl --vacuum-time=7d
find /var/log -name "*.gz" -mtime +30 -delete
find /var/log -name "*.log.*" -mtime +30 -delete

# b. Pulire cache pacchetti
dnf clean all        # RHEL/CentOS
apt-get clean        # Ubuntu/Debian

# c. Pulire file temporanei
find /tmp -type f -mtime +7 -delete

# 6. Verificare lo spazio recuperato
df -h
```

**ESCALATION**: se dopo le azioni di cleanup lo spazio libero e' ancora sotto il 15%, escalare al team Infrastruttura per l'espansione del volume o la migrazione dei dati.

---

### Runbook: Guasto DNS/DHCP

```
============================================================
RUNBOOK
============================================================
Codice:          RB-NET-002
Titolo:          Guasto Servizi DNS / DHCP
Versione:        1.2
Ultima modifica: 08/05/2026
Classificazione: Interna
============================================================
```

**Trigger**: Segnalazioni multiple di impossibilita' a navigare, risolvere nomi, ottenere indirizzo IP. Alert di monitoraggio su servizi DNS o DHCP.

**Procedura — Diagnosi DNS**

```bash
# 1. Verificare la raggiungibilita' del server DNS
ping -c 4 dns1.azienda.local
ping -c 4 dns2.azienda.local

# 2. Testare la risoluzione dei nomi
nslookup intranet.azienda.local dns1.azienda.local
nslookup google.com dns1.azienda.local
dig @dns1.azienda.local intranet.azienda.local A

# 3. Verificare il servizio DNS
# Windows
Get-Service -Name "DNS" -ComputerName "MI-DC-01" | Select-Object Status
# Linux (BIND)
systemctl status named

# 4. Controllare i log DNS
# Windows
Get-WinEvent -LogName "DNS Server" -ComputerName "MI-DC-01" -MaxEvents 50
# Linux
journalctl -u named -n 50 --no-pager
```

**Procedura — Risoluzione DNS**

```powershell
# Riavvio servizio DNS (Windows)
Restart-Service -Name "DNS" -ComputerName "MI-DC-01"

# Verificare la zona DNS
dnscmd MI-DC-01 /ZoneInfo azienda.local

# Ricostruire la cache DNS
dnscmd MI-DC-01 /ClearCache

# Verificare la replicazione DNS tra i domain controller
dcdiag /test:DNS /s:MI-DC-01 /DnsBasic
```

```bash
# Riavvio servizio DNS (Linux BIND)
sudo systemctl restart named

# Verificare la configurazione
named-checkconf
named-checkzone azienda.local /var/named/azienda.local.zone
```

**Procedura — Diagnosi e risoluzione DHCP**

```powershell
# 1. Verificare il servizio DHCP
Get-Service -Name "DHCPServer" -ComputerName "MI-DHCP-01" | Select-Object Status

# 2. Verificare lo scope DHCP e le statistiche
Get-DhcpServerv4ScopeStatistics -ComputerName "MI-DHCP-01"
# Output: verificare che il pool non sia esaurito (AddressesFree > 0)

# 3. Se il pool e' esaurito:
# a. Identificare lease scadute o inattive
Get-DhcpServerv4Lease -ComputerName "MI-DHCP-01" -ScopeId "10.0.1.0" |
    Where-Object { $_.AddressState -eq "InactiveReservation" -or
                   $_.LeaseExpiryTime -lt (Get-Date) }

# b. Estendere il range se necessario
Set-DhcpServerv4Scope -ComputerName "MI-DHCP-01" -ScopeId "10.0.1.0" `
    -EndRange "10.0.1.250"

# 4. Riavvio servizio DHCP
Restart-Service -Name "DHCPServer" -ComputerName "MI-DHCP-01"

# 5. Verificare che i client ottengano un indirizzo
# Dal client:
ipconfig /release
ipconfig /renew
ipconfig /all    # Verificare che l'IP sia stato assegnato correttamente
```

**ESCALATION**: se il servizio DNS/DHCP non si ripristina entro 30 minuti, attivare il protocollo di Major Incident (RB-INC-001) data la natura trasversale dell'impatto.

---

## Problem Management e Root Cause Analysis

Il Problem Management e' il processo ITSM che si occupa di identificare e rimuovere le cause radice degli incidenti, prevenendone la ricorrenza. Mentre l'Incident Management si focalizza sul ripristino rapido del servizio (anche con workaround temporanei), il Problem Management cerca la soluzione definitiva.

### Tipologie di Problem Management

**Problem Management reattivo**: si attiva dopo la risoluzione di incidenti, in particolare:
- Incidenti ricorrenti (stesso sintomo rilevato 3+ volte in 30 giorni)
- Major Incident (ogni MI genera automaticamente un Problem ticket per la RCA)
- Incidenti con workaround applicato ma senza soluzione definitiva

**Problem Management proattivo**: si attiva prima che si verifichino incidenti, attraverso:
- Analisi dei trend degli incidenti (pattern recognition)
- Analisi dei log e degli alert per anomalie sottosoglia
- Vulnerability assessment e analisi delle configurazioni
- Revisione delle capacita' e dei trend di performance

### Tecniche di Root Cause Analysis (RCA)

**Tecnica 1 — 5 Perche' (5 Whys)**

Metodo semplice e diretto: per ogni problema, chiedersi "perche'?" ricorsivamente fino a raggiungere la causa radice.

```
Esempio pratico:

Problema: Il server web e' andato in crash alle 03:00.
  1. Perche'? Il processo httpd ha esaurito la memoria.
  2. Perche'? Un memory leak nel modulo PHP ha accumulato 8GB di RAM.
  3. Perche'? Il codice non rilascia correttamente le connessioni DB.
  4. Perche'? La libreria di connessione al DB non e' stata aggiornata alla versione
     che corregge il bug noto CVE-2025-XXXX.
  5. Perche'? Il processo di patch management applicativo non include le dipendenze
     di terze parti.

Causa radice: gap nel processo di patch management per le dipendenze applicative.
Azione correttiva: estendere il processo di patch management per includere
l'inventario e l'aggiornamento periodico delle dipendenze di terze parti.
```

**Tecnica 2 — Diagramma di Ishikawa (Fishbone)**

Analisi strutturata che categorizza le possibili cause in 6 dimensioni:

```
                              PROBLEMA
                                 |
    +----------+----------+------+------+----------+----------+
    |          |          |             |          |          |
  Persone   Processi   Tecnologia   Ambiente   Dati     Terze Parti
    |          |          |             |          |          |
  - Errore  - SOP      - Bug SW      - Rete    - Corruz. - Vendor
    umano     assente   - HW guasto   - Power   - Inconsis - ISP
  - Training- Processo - Config      - Cooling  - Volume  - Cloud
    inadeg.   non       errata       - Sicurezza  eccessivo  provider
  - Comun.    seguito  - Compatib.             - Integr.
    carente            - Capacity                mancante
```

**Tecnica 3 — Known Error Database (KEDB)**

Quando la causa radice e' identificata ma la soluzione definitiva non puo' essere implementata immediatamente (es. richiede un upgrade pianificato, una modifica architetturale, o un budget non ancora approvato), il problema viene registrato come Known Error con workaround documentato.

```
TEMPLATE KNOWN ERROR:

ID:              KE-[NUMERO]
Problema:        [Descrizione del problema]
Causa radice:    [Causa identificata]
Workaround:      [Soluzione temporanea da applicare quando si ripresenta]
Soluzione def.:  [Soluzione definitiva pianificata]
Data prevista:   [Data di risoluzione definitiva]
Ticket correlati: [PRB-xxxxx, INC-xxxxx]
CI impattati:    [Elenco CI]
```

---

## Automazione e Riduzione del Toil

Il concetto di "toil" proviene dalla disciplina SRE (Site Reliability Engineering) di Google e identifica il lavoro manuale, ripetitivo, automatizzabile e privo di valore duraturo che scala linearmente con la crescita dei sistemi. La riduzione del toil e' un obiettivo strategico per qualsiasi team IT operativo.

### Identificazione del Toil

Condurre un "toil audit" periodico (semestrale) chiedendo a ogni membro del team di registrare per 5 giorni lavorativi tutte le attivita' ripetitive svolte:

```
TEMPLATE TOIL LOG:

Data    | Attivita'                    | Durata | Frequenza  | Automatizzabile?
--------+------------------------------+--------+------------+------------------
LUN     | Verifica manuale backup      | 30 min | Giornaliera| SI — script + alert
LUN     | Reset password utente        | 10 min | 3-4/giorno | SI — self-service
MAR     | Provisioning VM              | 45 min | Settimanale| SI — IaC (Terraform)
MAR     | Aggiunta utente a gruppi AD  | 15 min | 2-3/giorno | SI — workflow ITSM
MER     | Report capacita' manuale     | 60 min | Mensile    | SI — dashboard auto
...
```

### Prioritizzazione del Toil

Formula di prioritizzazione: **Impatto = Frequenza x Tempo per esecuzione**

```
MATRICE PRIORITIZZAZIONE TOIL:

Attivita'               | Freq/mese | Min/esec | Ore/mese | Priorita' automazione
------------------------+-----------+----------+----------+----------------------
Reset password          | 80        | 10       | 13.3     | ALTA (self-service)
Verifica backup         | 22        | 30       | 11.0     | ALTA (script + alert)
Provisioning VM         | 8         | 45       | 6.0      | MEDIA (IaC)
Report capacita'        | 1         | 60       | 1.0      | BASSA (dashboard)
```

### Strumenti di automazione

| Categoria | Strumento | Uso tipico |
|---|---|---|
| Infrastructure as Code | Terraform, Pulumi | Provisioning infrastruttura |
| Configuration Management | Ansible, Puppet, Chef | Configurazione sistemi |
| CI/CD | Jenkins, GitLab CI, GitHub Actions | Build e deployment automatizzati |
| Workflow ITSM | ServiceNow Flow Designer, Jira Automation | Automazione ticket e approvazioni |
| Scripting | PowerShell, Bash, Python | Automazione task operativi |
| Monitoring/Alerting | Zabbix, Prometheus, Grafana | Monitoraggio e notifiche automatiche |
| ChatOps | Slack/Teams bot + webhook | Esecuzione comandi da chat |

### Obiettivo organizzativo

Seguendo il modello SRE di Google, l'obiettivo e' mantenere il toil operativo sotto il 50% del tempo di ciascun operatore. Almeno il 50% del tempo deve essere dedicato a lavoro ingegneristico che riduce il toil futuro o aggiunge funzionalita' al servizio.

```
METRICHE TOIL:

- Percentuale tempo toil per operatore:   target <= 50%
- Task automatizzati nell'ultimo trimestre: trend crescente
- Ore/mese risparmiate da automazione:      trend crescente
- Numero di runbook convertiti in script:   target >= 30% dei runbook
```

---

## Playbook vs Runbook vs SOP — Framework Strategico

La distinzione tra Playbook, Runbook e SOP e' fondamentale per organizzare correttamente la documentazione operativa. I tre documenti operano a livelli di astrazione diversi e servono scopi complementari.

### Confronto strutturale

```
================================================================================
CONFRONTO PLAYBOOK / RUNBOOK / SOP
================================================================================

Caratteristica   | SOP                    | Runbook                 | Playbook
-----------------+------------------------+-------------------------+-----------
Livello          | Operativo              | Tattico                 | Strategico
Scopo            | Standardizzare un      | Reagire a un evento     | Coordinare una
                 | processo ricorrente    | specifico               | risposta complessa
Chi lo usa       | Tutti i livelli        | Tecnici L2/L3           | Manager, IC, team
Frequenza uso    | Quotidiana/settimanale | Su evento/incidente     | Su scenario complesso
Contiene         | Passi prescrittivi,    | Comandi, output attesi, | Ruoli, comunicazione,
                 | checklist, template    | decision tree, escalat. | strategie, procedure
Esempio          | SOP-IAM-001 Creazione  | RB-SVC-001 Riavvio     | Playbook risposta
                 | utente                 | servizi critici         | attacco DDoS
Aggiornamento    | Annuale o su modifica  | Su incidente o test     | Annuale + dopo ogni
                 | del processo           |                         | esercitazione
Formato ideale   | Documento strutturato  | Comando-output-         | Documento + diagramma
                 | con checklist          | decisione               | + tabella ruoli
```

### Quando usare cosa

```
DECISION TREE — TIPO DI DOCUMENTO:

L'attivita' e' pianificata e ricorrente?
  |
  +-- SI --> E' prevalentemente procedurale (passi da seguire)?
  |           |
  |           +-- SI --> SOP
  |           +-- NO --> Policy / Linea guida
  |
  +-- NO --> E' una risposta a un evento specifico?
              |
              +-- SI --> Coinvolge un singolo sistema/servizio?
              |           |
              |           +-- SI --> Runbook
              |           +-- NO --> Coinvolge coordinazione multi-team?
              |                       |
              |                       +-- SI --> Playbook
              |                       +-- NO --> Runbook (con sezione escalation)
              |
              +-- NO --> Piano di progetto / Procedura ad-hoc
```

### Struttura tipo di un Playbook

A differenza dei runbook gia' documentati in questa guida, un playbook include anche:

1. **Matrice RACI** (Responsible, Accountable, Consulted, Informed) per ogni fase
2. **Piano di comunicazione** con template di messaggi per ogni livello di stakeholder
3. **Criteri di attivazione e disattivazione** dello scenario
4. **Procedure di coordinamento inter-team** con punti di sincronizzazione
5. **Decision tree strategici** (es. quando escalare al management, quando coinvolgere legale, quando comunicare esternamente)

---

## Procedure di Compliance e Audit

### Preparazione all'audit IT

L'audit IT verifica che i controlli IT siano progettati e operino in modo efficace. La preparazione all'audit richiede un processo strutturato di raccolta evidenze.

**Procedura — Preparazione evidenze pre-audit**

**Passo 1 — Raccolta evidenze (T-30 giorni prima dell'audit)**

Per ogni area di controllo, preparare le evidenze richieste:

```
================================================================================
MATRICE EVIDENZE AUDIT PER AREA DI CONTROLLO
================================================================================

Area di controllo     | Evidenza richiesta                        | Fonte
----------------------+-------------------------------------------+---------
Change Management     | Log RFC approvate (campione 12 mesi)      | ITSM
                      | Verbali CAB con firme                     | SharePoint
                      | Report Failed Change con PIR              | ITSM
Incident Management   | Report SLA rispettati / violati           | ITSM
                      | PIR per Major Incident                    | ITSM
                      | Procedure di escalation documentate       | Wiki/Doc
Access Management     | Report access review con sign-off         | ITSM
                      | Log provisioning / deprovisioning         | AD + ITSM
                      | Policy password e MFA                     | GPO export
Backup & Recovery     | Report backup giornalieri (12 mesi)       | Console backup
                      | Report test di ripristino (trimestrali)   | ITSM
                      | Policy di backup approvata                | Doc
Patch Management      | Report compliance patching                | WSUS/SCCM
                      | Policy di patching approvata              | Doc
                      | Evidenza test patch in staging             | ITSM
Physical Security     | Log accesso data center (campione)        | Sistema badge
                      | Contratti manutenzione impianti           | Amministrazione
Business Continuity   | BCP e DRP aggiornati                      | Doc
                      | Report test DR                            | ITSM
                      | Verbali esercitazioni                     | Doc
```

**Passo 2 — Verifica completezza**

Per ogni evidenza:

```
CHECKLIST VERIFICA EVIDENZA AUDIT:

[ ] L'evidenza copre l'intero periodo di audit?
[ ] L'evidenza e' datata e firmata (dove richiesto)?
[ ] L'evidenza e' in formato non modificabile (PDF, export con timestamp)?
[ ] L'evidenza e' conservata nella cartella di audit strutturata?
[ ] Le eccezioni sono documentate con giustificazione?
[ ] I gap identificati hanno un piano di remediation documentato?
```

**Passo 3 — Remediation dei gap**

Se durante la preparazione si identificano gap nei controlli:

1. Documentare il gap con: descrizione, impatto potenziale, causa.
2. Definire il piano di remediation con: azione correttiva, responsabile, scadenza.
3. Implementare la remediation PRIMA dell'audit dove possibile.
4. Per i gap che non possono essere chiusi prima dell'audit, preparare una spiegazione chiara del piano di remediation con timeline.

### Conservazione della documentazione di audit

```
PERIODI DI CONSERVAZIONE DOCUMENTAZIONE:

Tipo documentazione                    | Periodo minimo | Normativa
---------------------------------------+----------------+-----------
Evidenze audit SOX (ITGC)             | 7 anni         | SOX Section 802
Documentazione accessi / access review | 7 anni         | SOX, ISO 27001
Log di sicurezza e accessi             | 3-5 anni       | GDPR, PCI-DSS
Report backup e test DR                | 5 anni         | Best practice
Verbali CAB e decisioni change         | 5 anni         | ITIL best practice
Report incidenti di sicurezza          | 10 anni        | Normativa settoriale
Certificati di distruzione asset       | 7 anni         | GDPR, RAEE
Policy e procedure IT (versioni arch.) | Illimitato      | Best practice
```

---

## Esercizi
1. **Lab — runbook test.** Junior esegue runbook senza guida; identifica gap.
2. **Stretch — runbook automatici.** Conversione a script Ansible.

## Auto-valutazione
1. Runbook qualita: test?
2. Runbook versioning: dove?
3. Decision tree: quando usare?

## Glossario locale
| Termine | Definizione |
|---|---|
| **Runbook** | Procedura operativa documentata. |
| **SOP** | Standard Operating Procedure. |
| **Quick reference card** | Sintesi 1-pagina. |
| **Decision tree** | Albero decisione esplicito. |
| **CAB** | Change Advisory Board — comitato che valuta e approva le RFC. |
| **ECAB** | Emergency CAB — sessione accelerata per Emergency Change. |
| **RFC** | Request for Change — richiesta formale di modifica infrastrutturale. |
| **Change Enablement** | Denominazione ITIL 4 per il processo di gestione dei cambiamenti. |
| **PIR** | Post-Incident Review — revisione strutturata post-incidente. |
| **RCA** | Root Cause Analysis — analisi della causa radice. |
| **CMDB** | Configuration Management Database — repository centralizzato dei CI. |
| **CI** | Configuration Item — qualsiasi componente IT gestito nel CMDB. |
| **KCS** | Knowledge-Centered Service — metodologia di gestione della conoscenza. |
| **KEDB** | Known Error Database — database degli errori noti con workaround. |
| **Playbook** | Documento strategico di coordinamento risposta multi-team. |
| **Release Manifest** | Elenco completo delle modifiche incluse in un rilascio. |
| **Toil** | Lavoro manuale, ripetitivo e automatizzabile privo di valore duraturo (SRE). |
| **Shift-left** | Spostare la risoluzione piu' vicino al punto di contatto utente. |
| **CSAT** | Customer Satisfaction Score — indice di soddisfazione utente. |
| **RACI** | Responsible, Accountable, Consulted, Informed — matrice di responsabilita'. |
| **ITGC** | IT General Controls — controlli IT generali per la compliance SOX. |
| **BIA** | Business Impact Analysis — analisi dell'impatto sul business. |
| **RTO** | Recovery Time Objective — tempo massimo accettabile di ripristino. |
| **RPO** | Recovery Point Objective — perdita dati massima accettabile. |
| **RTA** | Recovery Time Actual — tempo di ripristino effettivamente misurato. |
| **SLA** | Service Level Agreement — accordo sui livelli di servizio. |
| **IaC** | Infrastructure as Code — gestione infrastruttura tramite codice. |
| **Semantic Versioning** | Schema di versionamento MAJOR.MINOR.PATCH. |
| **Sanitizzazione dati** | Processo di cancellazione irreversibile dei dati dai supporti. |
| **RAEE** | Rifiuti Apparecchiature Elettriche ed Elettroniche — normativa smaltimento. |
| **Incident Commander** | Coordinatore unico durante un Major Incident. |
