# Tutorial: SOP e Runbook — Costruire le Procedure Operative Standard

> **Documento di riferimento:** `09-procedure-operative.md`
> **Dominio:** Procedure Operative (Dominio 09)
> **Ambito:** Creazione, gestione e manutenzione di SOP (Standard Operating Procedures) e Runbook operativi
> **Durata lab:** 8-10 ore (suddivise in 3 sessioni)
> **Livello:** Da principiante (Parte A) a operativo avanzato (Parte C)
> **Prerequisiti:** `tutorial_ops01_ch1a_itil_foundations_lab.md`, `tutorial_ops07_ch1b_incident_management_lab.md`, `tutorial_ops04_ch1b_active_directory_ldap_lab.md`
> **Ambiente:** Solo lab isolato — mai applicare runbook ransomware su sistemi reali

---

## Analogia Iniziale: Il Libretto di Istruzioni della Cucina

Immagina una cucina industriale. Ogni mattina lo chef prepara gli stessi piatti, ma senza una ricetta scritta ogni giorno dipende dalla memoria dello chef di turno. Se lui è malato, la qualità cala. Se arriva un nuovo chef, ricomincia da zero.

Le **SOP** (Standard Operating Procedures) sono le ricette scritte della cucina IT: ogni tecnico, di qualsiasi esperienza, esegue le stesse operazioni nel modo corretto, ogni volta.

I **Runbook** sono le schede d'emergenza affisse vicino ai fornelli: "SE il forno fa fumo → FASI 1-2-3-4". Non spiegano perché, ma dicono esattamente cosa fare nei prossimi 10 minuti.

---

## Lab Environment Setup

### Requisiti Hardware

| Componente | Minimo | Raccomandato |
|---|---|---|
| VM Windows Server 2022 (DC-LAB-01) | 2 vCPU / 4 GB RAM / 60 GB | 4 vCPU / 8 GB RAM / 80 GB |
| VM Ubuntu 22.04 (SRV-LINUX-01) | 1 vCPU / 2 GB RAM / 40 GB | 2 vCPU / 4 GB RAM / 60 GB |
| VM Windows 10 (WKS-LAB-01) | 2 vCPU / 4 GB RAM / 50 GB | 4 vCPU / 8 GB RAM / 80 GB |

### Topologia di Rete

```
┌─────────────────────────────────────────────────────────┐
│              Rete Lab: 192.168.56.0/24                  │
│                                                         │
│  ┌──────────────┐    ┌──────────────┐    ┌───────────┐  │
│  │  DC-LAB-01   │    │ SRV-LINUX-01 │    │ WKS-LAB-01│  │
│  │ 192.168.56.10│    │192.168.56.20 │    │192.168.56 │  │
│  │              │    │              │    │    .30    │  │
│  │  AD DS / DNS │    │  GitLab CE   │    │           │  │
│  │  DHCP / CA   │    │  Gitea       │    │ Client    │  │
│  │  File Server │    │  Wiki.js     │    │ Workstaz. │  │
│  └──────────────┘    └──────────────┘    └───────────┘  │
│                                                         │
│  Repository procedure: http://192.168.56.20:3000       │
│  Wiki interna:         http://192.168.56.20:3001       │
└─────────────────────────────────────────────────────────┘
```

### Setup Gitea (repository procedure)

```bash
# Su SRV-LINUX-01 — Gitea per versionamento procedure
docker run -d \
  --name gitea \
  --restart always \
  -p 3000:3000 \
  -v /opt/gitea:/data \
  gitea/gitea:latest

# Accedere a http://192.168.56.20:3000
# Utente admin: lab-admin / Lab@2024!
# Creare repository: "procedure-operative"
```

### Setup Wiki.js (documentale web)

```bash
# Wiki.js per pubblicazione procedure leggibili
docker run -d \
  --name wikijs \
  --restart always \
  -p 3001:3000 \
  -e DB_TYPE=sqlite \
  -v /opt/wikijs:/wiki/data \
  ghcr.io/requarks/wiki:2

# Accedere a http://192.168.56.20:3001
# Configurare admin: lab-admin@lab.local / Lab@2024!
```

### Struttura Directory Procedure

```bash
# Su SRV-LINUX-01 — struttura per procedure
mkdir -p /opt/procedures/{sop,runbooks,templates,archive,scripts}

# Su DC-LAB-01 (PowerShell)
New-Item -ItemType Directory -Path "C:\Procedures" -Force
New-Item -ItemType Directory -Path "C:\Procedures\SOP" -Force
New-Item -ItemType Directory -Path "C:\Procedures\Runbooks" -Force
New-Item -ItemType Directory -Path "C:\Procedures\Templates" -Force
```

---

## PART A: FONDAMENTI — Capire Perché le Procedure Scritte Esistono

### Concetto A1: SOP vs Runbook — Due Strumenti, Due Scopi

**Analogia**: Le SOP sono il manuale di uso e manutenzione della tua auto. Il Runbook è la guida di pronto soccorso nel cruscotto: "SE la spia dell'olio si accende MENTRE GUIDI → PASSI 1-2-3".

| Caratteristica | SOP | Runbook |
|---|---|---|
| **Trigger** | Pianificato, ricorrente, atteso | Reattivo, su evento/alert |
| **Tono** | Metodico, spiegato | Imperativo, immediato |
| **Lunghezza** | Media-lunga (5-30 pagine) | Corta-media (1-10 pagine) |
| **Quando si usa** | "Ogni nuovo utente, ogni lunedì, ogni mese" | "Quando scatta l'alert X alle 3:00" |
| **Include il perché?** | Sì, nelle note e nel contesto | No — solo cosa fare nei prossimi minuti |
| **Esempi tipici** | Creazione account, patching mensile, offboarding | Riavvio servizio, failover DB, risposta ransomware |
| **Chi lo usa** | Tecnici in condizioni normali | Chiunque risponda all'emergenza, sotto stress |

**Perché mi interessa?**
Senza procedure scritte, ogni tecnico gestisce le operazioni a modo proprio. Quando un utente viene creato, un sistema patchato, un account disabilitato: i passi variano, i log sono incompleti, gli audit falliscono. Le SOP trasformano competenza individuale in processo aziendale riproducibile.

### Concetto A2: La Struttura SOP Standard — Le 10 Sezioni

Una SOP ben strutturata ha sempre le stesse 10 sezioni. Ogni sezione ha uno scopo preciso:

```
============================================================
STANDARD OPERATING PROCEDURE
============================================================
Codice:            SOP-[AREA]-[NUMERO]
Titolo:            [Titolo descrittivo e univoco]
Versione:          [X.Y]
Data creazione:    [GG/MM/AAAA]
Ultima modifica:   [GG/MM/AAAA]
Autore:            [Nome Cognome]
Approvato da:      [Responsabile area]
Classificazione:   [Interna / Riservata]
============================================================
```

| Sezione | Scopo | Domanda che risponde |
|---|---|---|
| **1. Scopo** | Perché esiste questa procedura | "Cosa risolve?" |
| **2. Ambito** | A chi e cosa si applica | "Chi deve seguirla?" |
| **3. Prerequisiti** | Cosa serve prima di iniziare | "Posso eseguirla ora?" |
| **4. Definizioni** | Termini tecnici e acronimi | "Cosa significa X?" |
| **5. Responsabilità** | Chi fa cosa (RACI) | "È compito mio?" |
| **6. Procedura** | I passi operativi in sequenza | "Come si fa?" |
| **7. Verifiche** | Come confermare il successo | "Ha funzionato?" |
| **8. Rollback** | Come annullare le modifiche | "Come torno indietro?" |
| **9. Riferimenti** | Link a documentazione correlata | "Dove trovo più info?" |
| **10. Storico revisioni** | Traccia delle modifiche | "Cosa è cambiato?" |

### Concetto A3: La Struttura Runbook Standard

Il Runbook privilegia la velocità di consultazione sulla completezza:

```
============================================================
RUNBOOK
============================================================
Codice:          RB-[AREA]-[NUMERO]
Titolo:          [Titolo descrittivo]
Versione:        [X.Y]
Classificazione: [Interna / Riservata]
============================================================

TRIGGER: [Condizione esatta che attiva questo runbook — alert, sintomo, evento]

PREREQUISITI: [Accessi necessari, strumenti, informazioni da raccogliere]

PROCEDURA:
  PASSO N: [Azione]
    → Comando: [copia-incolla pronto]
    → Output atteso: [cosa vedere]
    → Se diverso: [cosa fare]
    → Tempo massimo: [minuti]

CRITERI ESCALATION: [Quando smettere e coinvolgere livello superiore]

VERIFICA: [Come confermare la risoluzione]

POST-AZIONE: [Documentazione, notifiche, follow-up]
```

**La regola d'oro del Runbook**: ogni passo deve avere un comando copia-incolla pronto. Chi esegue un runbook alle 3:00 di notte non deve ricordare la sintassi — deve solo copiare e incollare.

### Concetto A4: Il Ciclo di Vita delle Procedure

Le procedure non sono documenti statici. Hanno un ciclo di vita:

```
           ┌─────────┐
           │ BOZZA   │← Autore redige
           └────┬────┘
                ↓
           ┌─────────┐
           │REVISIONE│← Peer review tecnico
           └────┬────┘
                ↓
           ┌─────────┐
           │APPROVAZ.│← Owner area (+ CISO per security)
           └────┬────┘
                ↓
           ┌─────────┐
           │PUBBLICA.│← Disponibile nel repository
           └────┬────┘
                ↓        ← Evento: incidente, cambio sistema,
           ┌─────────┐     audit, calendario annuale
           │REVISIONE│← Minima annuale (trimestrale per critiche)
           └────┬────┘
                ↓
           ┌─────────┐
           │AGGIORNA.│← Nuova versione o archiviazione
           └─────────┘
```

**Regola pratica**: una procedura che non è stata revisionata negli ultimi 12 mesi è sospetta. Può riferirsi a server rinominati, software aggiornati, processi cambiati.

---

## PART B: OPERAZIONI — Creare Procedure Operative Reali

### Esercizio B1: SOP-IAM-001 — Creazione Account Active Directory

**Obiettivo.** Creare la SOP completa per la creazione di un nuovo account utente in Active Directory, incluse le fasi post-creazione (licenze, mailbox, gruppi).

**Background.** Ogni nuovo dipendente richiede la creazione di un account. Senza una SOP, ogni tecnico potrebbe dimenticare un passo (licenza M365, gruppo corretto, configurazione password). Il risultato: audit falliti, utenti con accessi errati, licenze non assegnate.

**Step 1 — Creare il file SOP**

```bash
# Su SRV-LINUX-01
cat > /opt/procedures/sop/SOP-IAM-001_v1.0.md << 'EOF'
# SOP-IAM-001: Creazione Account Utente Active Directory

## Intestazione
- **Codice**: SOP-IAM-001
- **Titolo**: Creazione Account Utente Active Directory
- **Versione**: 1.0
- **Data creazione**: 2026-01-10
- **Ultima modifica**: 2026-01-10
- **Autore**: Lab Admin
- **Approvato da**: IT Manager
- **Classificazione**: Interna

---

## 1. Scopo
Definire la procedura standardizzata per la creazione di un account utente
nel dominio Active Directory, inclusa l'assegnazione di licenze M365,
la creazione della mailbox e l'aggiunta ai gruppi appropriati.
Garantisce la tracciabilità delle operazioni e la conformità alle policy aziendali.

## 2. Ambito
Applicabile a: tutti i nuovi dipendenti, collaboratori con contratto, stagisti.
Esclusi: account di servizio (vedere SOP-IAM-006), account temporanei per fornitori
(vedere SOP-IAM-007).

## 3. Prerequisiti
- [ ] Ticket HR approvato con dati completi del nuovo utente
- [ ] Accesso amministrativo al dominio (ruolo: Account Operators o superiore)
- [ ] Accesso al portale Microsoft 365 Admin Center
- [ ] Accesso al sistema di gestione licenze
- [ ] Conoscenza del reparto e manager del nuovo utente (per assegnazione gruppi)

## 4. Definizioni
- **UPN** (User Principal Name): nome.cognome@azienda.local
- **SamAccountName**: nome.cognome (max 20 caratteri)
- **OU** (Organizational Unit): contenitore AD che determina policy applicate
- **M365**: Microsoft 365 (suite produttività cloud)
- **MFA**: Multi-Factor Authentication (obbligatoria da policy)

## 5. Responsabilità
| Attività | Responsabile | Approvatore |
|---|---|---|
| Ricezione richiesta HR | Service Desk (L1) | — |
| Creazione account AD | IT Operations (L2) | — |
| Assegnazione licenze M365 | IT Operations (L2) | IT Manager |
| Comunicazione credenziali | Service Desk (L1) | — |
| Chiusura ticket | Service Desk (L1) | — |

## 6. Procedura

### Passo 1 — Raccogliere le informazioni necessarie dal ticket HR

Verificare che il ticket contenga obbligatoriamente:
- Nome e cognome (evitare abbreviazioni)
- Data di inizio
- Reparto e sede
- Nome del manager diretto
- Tipologia di contratto (dipendente / collaboratore / stagista)
- Dispositivi assegnati
- Applicazioni necessarie

### Passo 2 — Creare l'account Active Directory

```powershell
# Da DC-LAB-01 con privilegi Domain Admin
# Adattare i valori alle informazioni del ticket

$Nome = "Mario"
$Cognome = "Rossi"
$Reparto = "IT Operations"
$Manager = "IT Manager"
$OU = "OU=IT,OU=Utenti,DC=lab,DC=local"

# Costruire i campi standard
$UPN = "$($Nome.ToLower()).$($Cognome.ToLower())@lab.local"
$SamAccount = "$($Nome.ToLower()).$($Cognome.ToLower())"
$DisplayName = "$Cognome $Nome"

# Generare password temporanea sicura
$TempPassword = "Temp$(Get-Random -Minimum 1000 -Maximum 9999)!Lab"

# Creare l'account
New-ADUser `
    -Name $DisplayName `
    -GivenName $Nome `
    -Surname $Cognome `
    -UserPrincipalName $UPN `
    -SamAccountName $SamAccount `
    -EmailAddress $UPN `
    -Department $Reparto `
    -Path $OU `
    -AccountPassword (ConvertTo-SecureString $TempPassword -AsPlainText -Force) `
    -ChangePasswordAtLogon $true `
    -Enabled $true `
    -Description "Creato $(Get-Date -Format 'yyyy-MM-dd') - Ticket #[NUMERO]"

Write-Output "Account creato: $UPN"
Write-Output "Password temporanea: $TempPassword"
```

**Verifica passo 2**:
```powershell
Get-ADUser -Identity $SamAccount -Properties * | 
    Select-Object Name, UserPrincipalName, Enabled, DistinguishedName
```
Output atteso: account visibile con `Enabled: True`.

### Passo 3 — Aggiungere ai gruppi di sicurezza appropriati

```powershell
# Gruppi base per tutti gli utenti (esempio)
$GruppiBase = @(
    "GRP-VPN-Users",
    "GRP-WiFi-Corp",
    "GRP-M365-Standard"
)

# Gruppo specifico per reparto
$GruppoReparto = "GRP-$Reparto"

foreach ($gruppo in ($GruppiBase + $GruppoReparto)) {
    try {
        Add-ADGroupMember -Identity $gruppo -Members $SamAccount
        Write-Output "Aggiunto a: $gruppo"
    } catch {
        Write-Warning "Gruppo non trovato: $gruppo — verificare manualmente"
    }
}
```

### Passo 4 — Assegnare licenza Microsoft 365

```powershell
# Tramite Microsoft Graph (PowerShell moderno)
# Installare: Install-Module Microsoft.Graph -Scope CurrentUser

Connect-MgGraph -Scopes "User.ReadWrite.All", "Organization.Read.All"

# Identificare la licenza disponibile
Get-MgSubscribedSku | Select-Object SkuPartNumber, ConsumedUnits, @{
    N="Disponibili"; E={$_.PrepaidUnits.Enabled - $_.ConsumedUnits}
}

# Assegnare licenza M365 Business Standard (esempio)
$LicenzaSku = "SPB"  # Microsoft 365 Business Standard
$SkuId = (Get-MgSubscribedSku | Where-Object SkuPartNumber -eq $LicenzaSku).SkuId

Set-MgUserLicense -UserId $UPN `
    -AddLicenses @{SkuId = $SkuId} `
    -RemoveLicenses @()

Write-Output "Licenza $LicenzaSku assegnata a $UPN"
```

### Passo 5 — Impostare il manager

```powershell
$ManagerDN = (Get-ADUser -Filter {DisplayName -eq $Manager}).DistinguishedName
Set-ADUser -Identity $SamAccount -Manager $ManagerDN
Write-Output "Manager impostato: $Manager"
```

### Passo 6 — Comunicare le credenziali

Inviare al manager del nuovo utente (NON all'utente direttamente):
- Username: `$UPN`
- Password temporanea: `$TempPassword`
- Istruzioni per il primo accesso e cambio password
- Link al portale di reset MFA

**NON inviare mai le credenziali via email non cifrata.**

## 7. Verifiche Post-Procedura

```powershell
# Verifica completa
$UserInfo = Get-ADUser -Identity $SamAccount -Properties *
Write-Output "=== VERIFICA ACCOUNT CREATO ==="
Write-Output "Nome: $($UserInfo.DisplayName)"
Write-Output "UPN: $($UserInfo.UserPrincipalName)"
Write-Output "OU: $($UserInfo.DistinguishedName)"
Write-Output "Abilitato: $($UserInfo.Enabled)"
Write-Output "Cambio password al logon: $($UserInfo.PasswordExpired)"
Write-Output "Manager: $($UserInfo.Manager)"
Write-Output "Gruppi: $(Get-ADPrincipalGroupMembership $SamAccount | Select-Object -Expand Name | Join-String -Separator ', ')"
```

- [ ] Account abilitato in AD
- [ ] UPN corretto (nome.cognome@lab.local)
- [ ] OU corretta per il reparto
- [ ] Gruppi base assegnati
- [ ] Licenza M365 assegnata
- [ ] Manager impostato
- [ ] Credenziali comunicate al manager

## 8. Rollback

In caso di errore o necessità di annullamento prima che l'utente acceda:

```powershell
# Disabilitare l'account (non eliminare — per tracciabilità)
Disable-ADAccount -Identity $SamAccount

# Rimuovere la licenza M365
Set-MgUserLicense -UserId $UPN -AddLicenses @() -RemoveLicenses @($SkuId)

# Documentare nel ticket il motivo dell'annullamento
```

**Eliminazione definitiva**: solo dopo 30 giorni e approvazione del manager IT.

## 9. Riferimenti
- SOP-IAM-002: Offboarding account utente
- SOP-IAM-006: Creazione account di servizio
- Policy Password Aziendale: [link]
- Guida assegnazione OU: [link]

## 10. Storico Revisioni
| Versione | Data | Autore | Descrizione |
|---|---|---|---|
| 1.0 | 2026-01-10 | Lab Admin | Prima versione |
EOF

echo "SOP-IAM-001 creata con successo"
```

**Output atteso:**
```
SOP-IAM-001 creata con successo
```

**Checkpoint di verifica:**
```bash
ls -lh /opt/procedures/sop/SOP-IAM-001_v1.0.md
wc -l /opt/procedures/sop/SOP-IAM-001_v1.0.md
```

---

### Esercizio B2: SOP-IAM-002 — Offboarding Account Utente

**Obiettivo.** Creare la SOP per la disattivazione sicura di un account utente alla cessazione del rapporto di lavoro.

**Background.** L'offboarding è una delle operazioni più critiche per la sicurezza. Un account attivo di un ex-dipendente è una vulnerabilità diretta. Studi mostrano che il 58% degli ex-dipendenti mantiene accesso ai sistemi aziendali dopo la fine del contratto — spesso perché non esiste una procedura formale.

**Step 1 — Creare SOP-IAM-002**

```bash
cat > /opt/procedures/sop/SOP-IAM-002_v1.0.md << 'EOF'
# SOP-IAM-002: Offboarding Account Utente

## Intestazione
- **Codice**: SOP-IAM-002
- **Versione**: 1.0
- **Classificazione**: Interna

---

## 1. Scopo
Garantire la revoca immediata e completa degli accessi di un utente
che cessa il rapporto di lavoro, proteggendo i dati aziendali e
rispettando i requisiti di compliance (GDPR art. 5, ISO 27001 A.9.2.6).

## 3. Prerequisiti
- [ ] Notifica HR con data ultima di lavoro e username dell'utente
- [ ] Accesso amministrativo AD, M365, sistemi applicativi
- [ ] Conferma del manager per l'accesso a dati critici

## 6. Procedura

### FASE 1 — Azioni immediate (entro 1 ora dall'uscita)

```powershell
$SamAccount = "mario.rossi"  # Username dell'utente in uscita
$DataUscita = Get-Date -Format "yyyy-MM-dd"

# 1. DISABILITARE IMMEDIATAMENTE l'account (NON eliminarlo)
Disable-ADAccount -Identity $SamAccount
Write-Output "[$(Get-Date)] Account $SamAccount disabilitato"

# 2. Reimpostare la password con valore casuale (impedisce l'accesso anche con vecchia pwd)
$NewPwd = [System.Web.Security.Membership]::GeneratePassword(24, 4)
Set-ADAccountPassword -Identity $SamAccount `
    -NewPassword (ConvertTo-SecureString $NewPwd -AsPlainText -Force) -Reset

# 3. Rimuovere da TUTTI i gruppi di sicurezza (eccetto Domain Users)
$Gruppi = Get-ADPrincipalGroupMembership $SamAccount | 
    Where-Object { $_.Name -ne "Domain Users" }
foreach ($g in $Gruppi) {
    Remove-ADGroupMember -Identity $g -Members $SamAccount -Confirm:$false
    Write-Output "Rimosso da: $($g.Name)"
}

# 4. Spostare in OU disabilitati (per audit trail)
Move-ADObject `
    -Identity (Get-ADUser $SamAccount).DistinguishedName `
    -TargetPath "OU=Disabilitati,DC=lab,DC=local"

# 5. Aggiungere nota descrittiva
Set-ADUser -Identity $SamAccount -Description "DISABILITATO $DataUscita - Offboarding"
```

### FASE 2 — Gestione mailbox (entro 24 ore)

```powershell
# 1. Convertire la mailbox in mailbox condivisa (mantiene i dati accessibili)
# In ambiente Exchange/M365:
# Set-Mailbox -Identity $SamAccount -Type Shared

# 2. Impostare reindirizzamento al manager (opzionale, max 30 giorni)
# Set-MailboxAutoReplyConfiguration -Identity $SamAccount -AutoReplyState Enabled
#     -ExternalMessage "Questa casella non è più attiva."
#     -InternalMessage "Questa casella non è più attiva. Contattare [manager]."

# 3. Rimuovere la licenza M365 (dopo aver esportato dati se necessario)
# Attendere D+7 prima di rimuovere la licenza per garantire l'accesso ai dati

Write-Output "RICORDARE: Rimuovere licenza M365 il $(
    (Get-Date).AddDays(7).ToString('yyyy-MM-dd'))"
```

### FASE 3 — Gestione dati (entro 48 ore)

1. Verificare se l'utente era owner di file critici sul file server
2. Trasferire la ownership al manager o al team
3. Revocare accessi VPN, applicazioni cloud, sistemi di terze parti
4. Disattivare token MFA fisici (se presenti)
5. Recuperare dispositivi aziendali (laptop, smartphone, badge)

### FASE 4 — Archiviazione account (D+30)

```powershell
# Dopo 30 giorni, verificare che non siano necessari dati dall'account
# e procedere all'eliminazione definitiva

# Verifica ultima attività
Get-ADUser -Identity $SamAccount -Properties LastLogonDate | 
    Select-Object Name, LastLogonDate, Enabled

# Eliminazione definitiva (IRREVERSIBILE — richiedere approvazione scritta)
# Remove-ADUser -Identity $SamAccount -Confirm:$false
```

## 7. Verifiche Post-Procedura

- [ ] Account disabilitato in AD: `Get-ADUser -Identity $SamAccount | Select-Object Enabled`
- [ ] Account in OU Disabilitati: verificare DistinguishedName
- [ ] Nessun gruppo attivo (eccetto Domain Users)
- [ ] Password reimpostata (non testabile direttamente — verificare dal log)
- [ ] Licenza M365 rimossa (entro D+7)
- [ ] Dispositivi restituiti documentati nel ticket

## 8. Rollback

L'offboarding non ha un rollback standard. In caso di riassunzione:
- Creare un NUOVO account (non riabilitare quello vecchio)
- Trattare come nuovo utente (SOP-IAM-001)
- Documentare il collegamento con l'account precedente

## 10. Storico Revisioni
| Versione | Data | Autore | Descrizione |
|---|---|---|---|
| 1.0 | 2026-01-10 | Lab Admin | Prima versione |
EOF

echo "SOP-IAM-002 creata"
```

---

### Esercizio B3: SOP-SRV-001 — Provisioning Nuovo Server

**Obiettivo.** Creare la SOP per il provisioning standardizzato di un nuovo server fisico o virtuale.

**Background.** Il provisioning senza procedura porta a server senza monitoring, senza backup, senza CMDB entry, senza hardening. Un server "dimenticato" che non compare nei sistemi di gestione è un blind spot operativo e di sicurezza.

```bash
cat > /opt/procedures/sop/SOP-SRV-001_v1.0.md << 'EOF'
# SOP-SRV-001: Provisioning Nuovo Server

## Intestazione
- **Codice**: SOP-SRV-001
- **Versione**: 1.0
- **Classificazione**: Interna

---

## 6. Procedura

### Passo 1 — Pre-provisioning (prima di accendere il server)

**Decisioni da prendere:**
- [ ] VM o fisico?
- [ ] OS: Windows Server 2022 / Ubuntu 22.04 LTS / RHEL 9?
- [ ] Naming convention: `[RUOLO]-[SEDE]-[NUMERO]` (es. `WEB-MI-01`)
- [ ] IP: statico riservato in DHCP o assegnato manualmente?
- [ ] Dimensionamento: vCPU, RAM, storage (documentare la motivazione)

**Registro CMDB pre-provisioning:**
```bash
# Creare il CI in GLPI prima del deploy (per tracciabilità)
# Stato: "In deployment"
# Dati necessari: nome, IP pianificato, responsabile, progetto
```

### Passo 2 — Installazione OS (VM su Proxmox/VMware)

```bash
# Su Proxmox — creare VM tramite CLI
pvesh create /nodes/proxmox/qemu \
    --vmid 200 \
    --name "SRV-LAB-02" \
    --memory 4096 \
    --cores 2 \
    --net0 virtio,bridge=vmbr0 \
    --scsi0 local-lvm:50 \
    --cdrom local:iso/ubuntu-22.04.3-live-server-amd64.iso \
    --boot order=ide2 \
    --ostype l26
```

### Passo 3 — Post-installazione: hardening base

```bash
# Per Ubuntu Server

# 1. Aggiornare il sistema
sudo apt update && sudo apt upgrade -y

# 2. Configurare hostname corretto
sudo hostnamectl set-hostname SRV-LAB-02
echo "127.0.1.1 SRV-LAB-02.lab.local SRV-LAB-02" | sudo tee -a /etc/hosts

# 3. Configurare IP statico (Netplan)
cat > /etc/netplan/01-lab.yaml << 'NETPLAN'
network:
  version: 2
  ethernets:
    ens18:
      addresses: [192.168.56.25/24]
      gateway4: 192.168.56.1
      nameservers:
        addresses: [192.168.56.10]
NETPLAN
sudo netplan apply

# 4. Installare agenti base
sudo apt install -y glpi-agent prometheus-node-exporter fail2ban unattended-upgrades

# 5. Configurare fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# 6. Disabilitare servizi non necessari
sudo systemctl disable --now avahi-daemon cups bluetooth 2>/dev/null || true

# 7. Configurare SSH hardening
sudo sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
echo "AllowUsers lab-admin" | sudo tee -a /etc/ssh/sshd_config
sudo systemctl restart sshd
```

### Passo 4 — Aggiungere al monitoring

```bash
# Verificare che Prometheus Node Exporter sia attivo
curl -s http://localhost:9100/metrics | head -5

# Aggiungere al prometheus.yml su SRV-LINUX-01
cat >> /etc/prometheus/prometheus.yml << 'PROM'
  - targets: ['192.168.56.25:9100']
    labels:
      hostname: 'SRV-LAB-02'
      environment: 'lab'
PROM

sudo systemctl reload prometheus
```

### Passo 5 — Configurare backup

```bash
# Aggiungere alla politica di backup (Veeam/Restic/Bareos)
# Documentare nel ticket il job di backup creato

# Verifica rapida con Restic
restic -r sftp:backup@192.168.56.10:/backup/SRV-LAB-02 init
```

### Passo 6 — Aggiornare CMDB

```python
# Script per aggiornare il CI in GLPI
import requests

GLPI_URL = "http://192.168.56.20:8080/glpi"
USER_TOKEN = "YOUR_TOKEN"
APP_TOKEN = "YOUR_APP_TOKEN"

def update_ci_status(computer_name: str, new_status: int) -> bool:
    """Aggiorna lo stato di un CI da 'In deployment' a 'Production'."""
    headers = {
        "Content-Type": "application/json",
        "App-Token": APP_TOKEN
    }
    # Inizializzare sessione
    resp = requests.get(
        f"{GLPI_URL}/apirest.php/initSession",
        headers={**headers, "Authorization": f"user_token {USER_TOKEN}"},
        timeout=10
    )
    session_token = resp.json().get("session_token")
    headers["Session-Token"] = session_token

    # Trovare il computer per nome
    search_resp = requests.get(
        f"{GLPI_URL}/apirest.php/Computer?searchText[name]={computer_name}",
        headers=headers,
        timeout=10
    )
    computers = search_resp.json()
    if not computers:
        print(f"CI non trovato per: {computer_name}")
        return False

    ci_id = computers[0]["id"]

    # Aggiornare stato (5 = In production in GLPI default)
    update_resp = requests.put(
        f"{GLPI_URL}/apirest.php/Computer/{ci_id}",
        headers=headers,
        json={"states_id": new_status},
        timeout=10
    )
    print(f"CI {computer_name} aggiornato: status_code={update_resp.status_code}")
    requests.get(f"{GLPI_URL}/apirest.php/killSession", headers=headers, timeout=5)
    return update_resp.status_code == 200

update_ci_status("SRV-LAB-02", 5)
```

## 7. Verifiche Completamento

```bash
# Script di verifica post-provisioning
#!/bin/bash
HOST="SRV-LAB-02"
IP="192.168.56.25"

echo "=== VERIFICA POST-PROVISIONING: $HOST ==="
echo ""

# 1. Ping
ping -c 3 $IP > /dev/null && echo "[OK] Raggiungibile via ping" || echo "[FAIL] Non raggiungibile"

# 2. SSH
ssh -o ConnectTimeout=5 lab-admin@$IP "echo '[OK] SSH funzionante'" 2>/dev/null

# 3. Monitoring
curl -sf http://$IP:9100/metrics > /dev/null && \
    echo "[OK] Node Exporter attivo" || echo "[FAIL] Node Exporter non risponde"

# 4. Hostname
ssh lab-admin@$IP "hostname" 2>/dev/null | grep -q $HOST && \
    echo "[OK] Hostname corretto" || echo "[FAIL] Hostname errato"

echo ""
echo "=== CHECKLIST MANUALE ==="
echo "[ ] CI aggiornato in GLPI (stato: Production)"
echo "[ ] Job di backup configurato"
echo "[ ] Ticket di provisioning aggiornato con IP, hostname, data"
echo "[ ] DNS record creato: $HOST.lab.local → $IP"
```
EOF

echo "SOP-SRV-001 creata"
```

---

### Esercizio B4: RB-SVC-001 — Runbook Riavvio Servizi Critici

**Obiettivo.** Creare il Runbook operativo per il riavvio dei servizi critici in risposta a un alert di monitoraggio.

**Background.** Alle 3:00 un alert sveglia il tecnico on-call: "SQL Server non risponde". Senza un Runbook, il tecnico deve ricordare a memoria i comandi, la sequenza corretta, i criteri di escalation. Con un Runbook, legge e segue. La differenza in termini di MTTR (Mean Time To Repair) può essere di ore.

```bash
cat > /opt/procedures/runbooks/RB-SVC-001_v2.1.md << 'EOF'
# RB-SVC-001: Riavvio Servizi Critici

## Intestazione
- **Codice**: RB-SVC-001
- **Versione**: 2.1
- **Ultima modifica**: 2026-03-18
- **Classificazione**: Interna

---

## TRIGGER

Alert di monitoraggio che indica servizio critico non risponde o in stato degradato.
Il servizio non si è ripristinato automaticamente entro 5 minuti dall'alert.

---

## PREREQUISITI

- Accesso RDP/SSH al server interessato
- Credenziali amministrative appropriate
- Accesso ai log di sistema
- Numero ticket da aprire su GLPI (da fare prima di iniziare)

---

## PROCEDURA

### A. SQL Server

```powershell
# PASSO A1 — Verificare lo stato
Get-Service -Name "MSSQLSERVER" -ComputerName "MI-SQL-01"
# Output atteso: Status = Stopped (o Running ma non responsivo)

# PASSO A2 — Se Running ma non responsivo, verificare i processi
Invoke-Command -ComputerName "MI-SQL-01" -ScriptBlock {
    Get-Process -Name "sqlservr" | Select-Object CPU, WorkingSet64, Threads
}
# Se CPU > 95% o RAM > 90%: escalare al DBA prima di procedere

# PASSO A3 — Riavvio grazioso (Tempo massimo: 120 secondi)
Restart-Service -Name "MSSQLSERVER" -ComputerName "MI-SQL-01" -Force

# PASSO A4 — Attendere e verificare
Start-Sleep -Seconds 30
Get-Service -Name "MSSQLSERVER" -ComputerName "MI-SQL-01"
# Output atteso: Status = Running

# PASSO A5 — Test connettività DB
Invoke-Sqlcmd -ServerInstance "MI-SQL-01" -Query "SELECT @@VERSION" -QueryTimeout 30
# Output atteso: stringa con versione SQL Server

# PASSO A6 — Riavviare SQL Agent
Restart-Service -Name "SQLSERVERAGENT" -ComputerName "MI-SQL-01"
```

**→ ESCALATION**: Se il servizio non si avvia entro 5 minuti → coinvolgere DBA immediatamente.

### B. Active Directory Domain Services

> ⚠️ **ATTENZIONE CRITICA**: Il riavvio di AD DS impatta TUTTI i servizi di autenticazione.
> Eseguire SOLO se strettamente necessario e SOLO dopo aver verificato altri DC disponibili.

```powershell
# PASSO B1 — Verificare altri DC disponibili
Get-ADDomainController -Filter * | Select-Object HostName, IsGlobalCatalog, OperatingSystem
# STOP se questo è l'UNICO DC disponibile → escalare IMMEDIATAMENTE

# PASSO B2 — Verificare la replicazione
repadmin /replsummary
# Output atteso: 0 errori di replicazione

# PASSO B3 — Riavviare solo il servizio (non il server)
Restart-Service -Name "NTDS" -ComputerName "MI-DC-02" -Force

# PASSO B4 — Verificare
dcdiag /s:MI-DC-02 /test:services /test:replications /test:advertising
# Output atteso: tutti i test = Passed
```

### C. Apache/Nginx (Linux)

```bash
# PASSO C1 — Verificare la configurazione prima del riavvio
nginx -t    # o: apache2ctl configtest
# Output atteso: "syntax is ok / test is successful"
# → Se FAIL: NON riavviare — diagnosticare la configurazione

# PASSO C2 — Riavvio grazioso
sudo systemctl restart nginx    # o apache2/httpd

# PASSO C3 — Verifica
systemctl status nginx
curl -s -o /dev/null -w "%{http_code}" https://webapp.azienda.com/health
# Output atteso: 200
```

---

## CRITERI DI ESCALATION

Smettere e coinvolgere il livello superiore se:
- Il servizio non si avvia entro il tempo massimo indicato
- I log mostrano errori sconosciuti o corruzione di dati
- La verifica di connettività fallisce dopo il riavvio
- Questo è l'unico nodo (singolo DC, singolo DB senza replica)
- Sono le ore notturne e l'impatto business è elevato

**Contatti escalation**: vedere matrice reperibilità in [link]

---

## VERIFICA

Il problema è risolto quando:
1. Il servizio è in stato `Running`
2. Il test funzionale specifico del servizio ha esito positivo
3. Gli alert di monitoraggio sono rientrati
4. Le applicazioni che dipendono dal servizio funzionano normalmente

---

## POST-AZIONE

1. Aggiornare il ticket con: orario intervento, comandi eseguiti, esito
2. Se l'alert si ripete entro 24 ore: aprire un problema (Problem Management)
3. Notificare i responsabili applicativi se il servizio ha avuto downtime > 15 minuti
4. Controllare i log per identificare la causa (da fare entro 4 ore)

EOF

echo "RB-SVC-001 creato"
```

---

### Esercizio B5: RB-SEC-001 — Runbook Risposta Ransomware (Versione Lab)

**Obiettivo.** Creare una versione lab-safe del Runbook per la risposta a un incidente ransomware, con tutte le fasi reali ma senza eseguire operazioni rischiose.

**Background.** Il Runbook ransomware è il più critico in assoluto. Non lo usi mai — finché non devi. E quando devi, è la cosa più importante che esiste. Avere questo Runbook significa che la risposta dura ore invece di giorni.

```bash
cat > /opt/procedures/runbooks/RB-SEC-001_v2.0.md << 'EOF'
# RB-SEC-001: Risposta Incidente Ransomware

## Intestazione
- **Codice**: RB-SEC-001
- **Versione**: 2.0
- **Ultima modifica**: 2026-03-20
- **Classificazione**: RISERVATA — DISTRIBUZIONE CONTROLLATA
- **Stampa copia fisica**: Sì — tenere in sala server accessibile offline

---

## TRIGGER

Uno o più dei seguenti:
- File cifrati in modo anomalo (estensioni cambiate, nota di riscatto)
- Alert EDR per comportamento di cifratura massiva
- Segnalazione utente di file inaccessibili con pattern sistematico
- Alert SIEM per accesso anomalo a condivisioni di rete

---

## ⚠️ AVVISO CRITICO

**OGNI MINUTO DI RITARDO = MIGLIAIA DI FILE AGGIUNTIVI CIFRATI.**

Le prime azioni devono essere eseguite entro 15 minuti dal rilevamento.

---

## FASE 1 — ISOLAMENTO IMMEDIATO (T+0 → T+15min)

```powershell
# OPZIONE A: Disabilitare porta switch (metodo più rapido)
# Sostituire XX e YY con il numero corretto di switch e porta
ssh admin@switch-accesso-XX "interface GigabitEthernet0/YY" ; "shutdown"

# OPZIONE B: Disabilitare interfacce di rete via script
Invoke-Command -ComputerName "PC-INFETTO" -ScriptBlock {
    Get-NetAdapter | Disable-NetAdapter -Confirm:$false
}

# OPZIONE C: Via console EDR
# CrowdStrike: Hosts > Manage > Contain Host
# Defender for Endpoint: Devices > Isolate Device

# !! NON SPEGNERE LE MACCHINE — la memoria volatile contiene prove forensi !!

# DISABILITARE IMMEDIATAMENTE gli account compromessi
Disable-ADAccount -Identity "utente-compromesso"
Set-ADAccountPassword -Identity "utente-compromesso" `
    -NewPassword (ConvertTo-SecureString "T3mp_S3cur3_P@ss!" -AsPlainText -Force) -Reset
```

---

## FASE 2 — VALUTAZIONE AMBITO (T+15min → T+60min)

```powershell
# Identificare altri sistemi potenzialmente coinvolti via log AD
Get-WinEvent -LogName Security -ComputerName "MI-DC-01" -MaxEvents 5000 |
    Where-Object {
        $_.Id -in @(4624, 4625, 4672, 4720, 4728, 4732) -and
        $_.TimeCreated -gt (Get-Date).AddHours(-6)
    } |
    Select-Object TimeCreated, Id, Message |
    Export-Csv "C:\Incident\AD-Events.csv" -NoTypeInformation

# VERIFICA CRITICA: lo stato del backup è integro?
# Il backup server è raggiungibile? Il ransomware lo ha raggiunto?
# → Se il backup è compromesso: escalare IMMEDIATAMENTE alla Direzione
```

---

## FASE 3 — NOTIFICHE OBBLIGATORIE

```
ORDINE DI NOTIFICA (non saltare nessuno):

T+0:   CISO / Responsabile Sicurezza IT    → TELEFONO + email
T+30:  IT Manager / CIO                    → TELEFONO + email
T+60:  Direzione Generale / CEO            → tramite CISO
T+120: Ufficio Legale                      → email formale
T+240: DPO (Data Protection Officer)       → email formale
       → Valutare notifica Garante Privacy (GDPR art. 33 — entro 72h)

!! NON comunicare pubblicamente senza approvazione management + ufficio legale !!
!! NON contattare gli attaccanti !!
!! NON pagare il riscatto senza approvazione esplicita Direzione + consulenza legale !!
```

---

## FASE 4 — RIPRISTINO DA BACKUP

**Prerequisito**: verificare che il ransomware sia eradicato PRIMA del ripristino.

1. Identificare il punto di ripristino sicuro (ultimo backup PRIMA della compromissione iniziale — non della cifratura, che può essere successiva all'intrusione)
2. Procedere con RB-BKP-001 per il ripristino, partendo dai sistemi più critici
3. Ricostruire da zero le macchine compromesse (NON ripristinare solo i file — l'attaccante può aver installato backdoor)
4. Reimpostare TUTTE le password prima di riconnettere alla rete

---

## FASE 5 — HARDENING POST-INCIDENTE

- Analizzare il vettore di attacco iniziale e chiudere la vulnerabilità
- Verificare e rafforzare backup (regola 3-2-1, backup immutabile, air-gapped)
- Implementare/rafforzare la segmentazione di rete
- Verificare policy di least privilege per tutti gli account
- Aggiornare le regole EDR/antivirus

---

## POST-AZIONE: LESSONS LEARNED (entro 2 settimane)

Condurre Post-Incident Review (PIR) con output:
1. Timeline dettagliata dell'incidente
2. Root Cause Analysis completa
3. Valutazione efficacia risposta
4. Elenco azioni correttive con responsabile e scadenza
5. Aggiornamento dei runbook in base alle lezioni apprese

EOF

echo "RB-SEC-001 creato"
```

---

### Esercizio B6: Repository e Versionamento Procedure

**Obiettivo.** Configurare Gitea come repository centralizzato per le procedure con workflow di approvazione.

**Background.** Le procedure in cartelle condivise o email si perdono, si duplicano, si contraddicono. Un repository Git porta versionamento, storico delle modifiche, branch per revisione, e un'unica fonte di verità.

**Step 1 — Inizializzare il repository**

```bash
# Su SRV-LINUX-01
cd /opt/procedures

# Inizializzare Git
git init
git config user.email "lab-admin@lab.local"
git config user.name "Lab Admin"

# Creare struttura standard
mkdir -p sop runbooks templates archive scripts

# File README principale
cat > README.md << 'EOF'
# Repository Procedure Operative

Questo repository contiene tutte le SOP (Standard Operating Procedures) e i Runbook
del team IT Operations.

## Struttura
- `sop/` — Standard Operating Procedures (pianificate, ricorrenti)
- `runbooks/` — Runbook (reattivi, su evento)
- `templates/` — Template vuoti per nuove procedure
- `archive/` — Procedure deprecate (NON eliminare — per storico)
- `scripts/` — Script di supporto alle procedure

## Workflow di contribuzione
1. Creare un branch: `feature/SOP-[CODICE]-[descrizione]`
2. Aggiungere/modificare la procedura
3. Aprire una Pull Request con descrizione delle modifiche
4. Review obbligatoria da un peer tecnico
5. Approvazione dell'owner dell'area
6. Merge su main

## Convenzioni di naming
- SOP: `SOP-[AREA]-[NNN]_v[X.Y].md`
- Runbook: `RB-[AREA]-[NNN]_v[X.Y].md`
- Aree: IAM, SRV, WKS, NET, SEC, BKP, OPS

## Revisioni
Ogni procedura viene rivista: annualmente (minimo) o su evento.
Scadenze di revisione: vedere `scripts/review_scheduler.sh`
EOF

# Aggiungere tutti i file
git add .
git commit -m "Initial commit: SOP-IAM-001, SOP-IAM-002, SOP-SRV-001, RB-SVC-001, RB-SEC-001"

# Collegare a Gitea (dopo aver creato il repository nell'interfaccia web)
git remote add origin http://192.168.56.20:3000/lab-admin/procedure-operative.git
git push -u origin main
```

**Output atteso:**
```
[main (root-commit) abc1234] Initial commit: SOP-IAM-001, SOP-IAM-002, SOP-SRV-001, RB-SVC-001, RB-SEC-001
 6 files changed, 450 insertions(+)
Enumerating objects: 8, done.
Writing objects: 100% (8/8), done.
To http://192.168.56.20:3000/lab-admin/procedure-operative.git
 * [new branch]      main -> main
```

---

## PART C: SISTEMATIZZARE — Dall'Esecuzione alla Governance

### Progetto C1: Script di Verifica Scadenze Revisione

**Obiettivo.** Creare uno script che verifica le scadenze di revisione di tutte le procedure e genera un report.

```bash
cat > /opt/procedures/scripts/review_scheduler.sh << 'SCRIPT'
#!/bin/bash
# review_scheduler.sh — Verifica scadenze revisione procedure

PROCEDURE_DIR="/opt/procedures"
DAYS_WARNING=30    # Avvisare 30 giorni prima della scadenza
REVIEW_CYCLE=365   # Revisione annuale (giorni)

echo "=== REPORT SCADENZE REVISIONE PROCEDURE ==="
echo "Data: $(date '+%Y-%m-%d %H:%M')"
echo ""

EXPIRED=0
EXPIRING_SOON=0
OK=0

# Analizzare ogni file .md nelle sottocartelle
while IFS= read -r -d '' file; do
    # Estrarre la data dell'ultima modifica dal frontmatter del file
    last_mod=$(grep -m1 "Ultima modifica:" "$file" | grep -oP '\d{2}/\d{2}/\d{4}')
    
    if [ -z "$last_mod" ]; then
        # Fallback: usare la data di modifica del file
        last_mod_ts=$(stat -c %Y "$file")
        last_mod_date="$last_mod_ts"
    else
        # Convertire da GG/MM/AAAA a timestamp
        day="${last_mod:0:2}"
        month="${last_mod:3:2}"
        year="${last_mod:6:4}"
        last_mod_ts=$(date -d "$year-$month-$day" +%s 2>/dev/null)
    fi
    
    if [ -n "$last_mod_ts" ]; then
        now=$(date +%s)
        days_since_review=$(( (now - last_mod_ts) / 86400 ))
        days_until_expiry=$(( REVIEW_CYCLE - days_since_review ))
        
        basename=$(basename "$file")
        
        if [ $days_until_expiry -lt 0 ]; then
            echo "❌ SCADUTA ($((days_since_review - REVIEW_CYCLE)) giorni fa): $basename"
            EXPIRED=$((EXPIRED+1))
        elif [ $days_until_expiry -le $DAYS_WARNING ]; then
            echo "⚠️  IN SCADENZA (tra $days_until_expiry giorni): $basename"
            EXPIRING_SOON=$((EXPIRING_SOON+1))
        else
            echo "✅ OK (scade tra $days_until_expiry giorni): $basename"
            OK=$((OK+1))
        fi
    fi
done < <(find "$PROCEDURE_DIR/sop" "$PROCEDURE_DIR/runbooks" -name "*.md" -print0 2>/dev/null)

echo ""
echo "=== SOMMARIO ==="
echo "Procedure OK:            $OK"
echo "In scadenza (< ${DAYS_WARNING}gg): $EXPIRING_SOON"
echo "Scadute:                 $EXPIRED"
echo ""
if [ $((EXPIRED + EXPIRING_SOON)) -gt 0 ]; then
    echo "AZIONE RICHIESTA: $(( EXPIRED + EXPIRING_SOON )) procedure necessitano revisione"
fi
SCRIPT

chmod +x /opt/procedures/scripts/review_scheduler.sh

# Test dello script
/opt/procedures/scripts/review_scheduler.sh
```

### Progetto C2: Script di Audit Completezza SOP

**Obiettivo.** Automatizzare la verifica che ogni SOP contenga tutte le 10 sezioni obbligatorie.

```bash
cat > /opt/procedures/scripts/sop_completeness_check.sh << 'SCRIPT'
#!/bin/bash
# sop_completeness_check.sh — Verifica completezza struttura SOP

PROCEDURE_DIR="/opt/procedures"
REQUIRED_SECTIONS=(
    "## 1\. Scopo"
    "## 2\. Ambito"
    "## 3\. Prerequisiti"
    "## 4\. Definizioni"
    "## 5\. Responsabilit"
    "## 6\. Procedura"
    "## 7\. Verifiche"
    "## 8\. Rollback"
    "## 9\. Riferimenti"
    "## 10\. Storico"
)

echo "=== AUDIT COMPLETEZZA SOP ==="
echo ""

TOTAL_FILES=0
TOTAL_ISSUES=0

while IFS= read -r -d '' file; do
    TOTAL_FILES=$((TOTAL_FILES+1))
    basename=$(basename "$file")
    issues=0
    
    for section in "${REQUIRED_SECTIONS[@]}"; do
        if ! grep -qE "$section" "$file"; then
            if [ $issues -eq 0 ]; then
                echo "📋 $basename:"
            fi
            echo "   ❌ Sezione mancante: $section"
            issues=$((issues+1))
            TOTAL_ISSUES=$((TOTAL_ISSUES+1))
        fi
    done
    
    if [ $issues -eq 0 ]; then
        echo "✅ $basename — tutte le sezioni presenti"
    fi

done < <(find "$PROCEDURE_DIR/sop" -name "*.md" -print0 2>/dev/null)

echo ""
echo "=== SOMMARIO ==="
echo "File analizzati: $TOTAL_FILES"
echo "Problemi trovati: $TOTAL_ISSUES"
SCRIPT

chmod +x /opt/procedures/scripts/sop_completeness_check.sh
/opt/procedures/scripts/sop_completeness_check.sh
```

### Progetto C3: Collegare le Procedure ai Ticket ITSM

**Obiettivo.** Creare uno script Python che, quando si apre un ticket GLPI di un determinato tipo, suggerisce automaticamente la procedura correlata.

```python
#!/usr/bin/env python3
"""
sop_linker.py — Collega i ticket GLPI alle procedure SOP appropriate.
Analizza il contenuto di un ticket e suggerisce la procedura più rilevante.
"""

import requests
from typing import Optional

GLPI_URL = "http://192.168.56.20:8080/glpi"
USER_TOKEN = "YOUR_TOKEN"
APP_TOKEN = "YOUR_APP_TOKEN"
REPO_URL = "http://192.168.56.20:3000/lab-admin/procedure-operative"

# Mappa keyword → procedura
SOP_KEYWORDS: dict[str, dict] = {
    "nuovo utente": {
        "sop": "SOP-IAM-001",
        "titolo": "Creazione Account Active Directory",
        "url": f"{REPO_URL}/src/branch/main/sop/SOP-IAM-001_v1.0.md"
    },
    "creazione utente": {
        "sop": "SOP-IAM-001",
        "titolo": "Creazione Account Active Directory",
        "url": f"{REPO_URL}/src/branch/main/sop/SOP-IAM-001_v1.0.md"
    },
    "offboarding": {
        "sop": "SOP-IAM-002",
        "titolo": "Offboarding Account Utente",
        "url": f"{REPO_URL}/src/branch/main/sop/SOP-IAM-002_v1.0.md"
    },
    "disattivare utente": {
        "sop": "SOP-IAM-002",
        "titolo": "Offboarding Account Utente",
        "url": f"{REPO_URL}/src/branch/main/sop/SOP-IAM-002_v1.0.md"
    },
    "nuovo server": {
        "sop": "SOP-SRV-001",
        "titolo": "Provisioning Nuovo Server",
        "url": f"{REPO_URL}/src/branch/main/sop/SOP-SRV-001_v1.0.md"
    },
    "provisioning": {
        "sop": "SOP-SRV-001",
        "titolo": "Provisioning Nuovo Server",
        "url": f"{REPO_URL}/src/branch/main/sop/SOP-SRV-001_v1.0.md"
    },
    "servizio non risponde": {
        "sop": "RB-SVC-001",
        "titolo": "Runbook: Riavvio Servizi Critici",
        "url": f"{REPO_URL}/src/branch/main/runbooks/RB-SVC-001_v2.1.md"
    },
}


def get_session_token() -> Optional[str]:
    resp = requests.get(
        f"{GLPI_URL}/apirest.php/initSession",
        headers={
            "Authorization": f"user_token {USER_TOKEN}",
            "App-Token": APP_TOKEN,
            "Content-Type": "application/json"
        },
        timeout=10
    )
    if resp.status_code == 200:
        return resp.json().get("session_token")
    return None


def find_relevant_sop(ticket_title: str, ticket_content: str) -> Optional[dict]:
    """Trova la SOP più rilevante in base al contenuto del ticket."""
    combined_text = f"{ticket_title} {ticket_content}".lower()
    for keyword, sop_info in SOP_KEYWORDS.items():
        if keyword in combined_text:
            return sop_info
    return None


def add_procedure_note(ticket_id: int, sop_info: dict, session_token: str) -> bool:
    """Aggiunge una nota al ticket con il link alla procedura suggerita."""
    headers = {
        "App-Token": APP_TOKEN,
        "Session-Token": session_token,
        "Content-Type": "application/json"
    }
    note_content = (
        f"📋 **PROCEDURA SUGGERITA**: {sop_info['sop']}\n"
        f"**Titolo**: {sop_info['titolo']}\n"
        f"**Link**: {sop_info['url']}\n\n"
        f"_Nota aggiunta automaticamente dal sistema di linking procedure._"
    )
    resp = requests.post(
        f"{GLPI_URL}/apirest.php/ITILFollowup",
        headers=headers,
        json={
            "input": {
                "itemtype": "Ticket",
                "items_id": ticket_id,
                "content": note_content,
                "is_private": 1
            }
        },
        timeout=10
    )
    return resp.status_code == 201


def process_new_ticket(ticket_id: int) -> None:
    session_token = get_session_token()
    if not session_token:
        print("Errore: impossibile ottenere session token GLPI")
        return

    headers = {
        "App-Token": APP_TOKEN,
        "Session-Token": session_token,
        "Content-Type": "application/json"
    }

    try:
        ticket_resp = requests.get(
            f"{GLPI_URL}/apirest.php/Ticket/{ticket_id}",
            headers=headers,
            timeout=10
        )
        if ticket_resp.status_code != 200:
            print(f"Ticket {ticket_id} non trovato")
            return

        ticket = ticket_resp.json()
        title = ticket.get("name", "")
        content = ticket.get("content", "")

        sop_info = find_relevant_sop(title, content)
        if sop_info:
            success = add_procedure_note(ticket_id, sop_info, session_token)
            if success:
                print(f"Procedura {sop_info['sop']} collegata al ticket #{ticket_id}")
            else:
                print(f"Errore nell'aggiungere nota al ticket #{ticket_id}")
        else:
            print(f"Nessuna procedura trovata per il ticket #{ticket_id}: '{title}'")
    finally:
        requests.get(
            f"{GLPI_URL}/apirest.php/killSession",
            headers=headers,
            timeout=5
        )


if __name__ == "__main__":
    # Test con ticket fittizio in lab
    import sys
    ticket_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    process_new_ticket(ticket_id)
```

---

## Checklist di Validazione Lab

Al termine degli esercizi, verificare:

**Parte A — Fondamenti:**
- [ ] A1: Sapere distinguere SOP e Runbook senza guardare le note (test orale)
- [ ] A2: Template SOP a 10 sezioni memorizzato (verificare scrivendo il template di memoria)
- [ ] A3: Capire perché il Runbook non spiega il "perché"
- [ ] A4: Disegnare il ciclo di vita delle procedure su carta

**Parte B — Esercizi:**
- [ ] B1: SOP-IAM-001 creata e salvata in /opt/procedures/sop/
- [ ] B1: Script PowerShell `New-ADUser` eseguito con successo sul lab
- [ ] B1: Account testuser creato e verificato in AD
- [ ] B2: SOP-IAM-002 creata e salvata
- [ ] B2: Account testuser disabilitato e spostato in OU Disabilitati
- [ ] B3: SOP-SRV-001 creata e salvata
- [ ] B4: RB-SVC-001 creato con comandi copia-incolla funzionanti
- [ ] B5: RB-SEC-001 creato con tutte le fasi di risposta
- [ ] B6: Repository Gitea inizializzato e procedure committate

**Parte C — Sistematizzazione:**
- [ ] C1: Script `review_scheduler.sh` esegue senza errori e mostra output corretto
- [ ] C2: Script `sop_completeness_check.sh` identifica sezioni mancanti
- [ ] C3: Script `sop_linker.py` trova la SOP corretta per keyword di test

---

## Appendice A: Codici di Area per SOP e Runbook

| Area | Codice | Esempi |
|---|---|---|
| Identity & Access Management | IAM | SOP-IAM-001 (creazione), SOP-IAM-002 (offboarding) |
| Server & Infrastruttura | SRV | SOP-SRV-001 (provisioning), SOP-SRV-003 (riavvio) |
| Workstation & Client | WKS | SOP-WKS-001 (deployment) |
| Network | NET | SOP-NET-001 (incidente rete) |
| Security | SEC | SOP-SEC-001 (patch), SOP-SEC-003 (certificati) |
| Backup | BKP | SOP-BKP-001 (monitoring backup) |
| Operations | OPS | SOP-OPS-005 (escalation vendor) |
| Database | DB | RB-DB-001 (failover DB) |

---

## Appendice B: Matrice SOP vs Runbook

| Scenario | SOP | Runbook |
|---|---|---|
| Creare un nuovo utente ogni lunedì | ✅ SOP-IAM-001 | — |
| SQL Server non risponde alle 3:00 | — | ✅ RB-SVC-001 |
| Deployment mensile patch di sicurezza | ✅ SOP-SEC-001 | — |
| Failover database primario | — | ✅ RB-DB-001 |
| Provisioning nuovo server (pianificato) | ✅ SOP-SRV-001 | — |
| Risposta ransomware | — | ✅ RB-SEC-001 |
| Rotazione password service account | ✅ SOP-IAM-004 | — |
| Ripristino da backup | — | ✅ RB-BKP-001 |

---

## Appendice C: Le 10 Best Practice per Procedure Efficaci

1. **Scrivere per il lettore meno esperto** — eseguibile anche dal tecnico junior alle 3:00
2. **Un passo, un'azione** — passi multipli = punti di fallimento multipli
3. **Includere sempre i comandi di verifica** — "riavvia" e poi "verifica che sia Running"
4. **Documentare l'output atteso** — l'operatore riconosce subito se qualcosa è sbagliato
5. **Prevedere sempre il rollback** — sapere come tornare indietro è tanto importante quanto andare avanti
6. **Mantenere le procedure vive** — revisione annuale minima, trimestrale per le critiche
7. **Linguaggio imperativo** — "Eseguire il comando" non "Si potrebbe eseguire"
8. **Separare cosa dal perché** — il corpo ha le istruzioni, le note hanno le spiegazioni
9. **Testare prima di pubblicare** — farlo eseguire a un collega in ambiente test
10. **Centralizzare e indicizzare** — un unico repository, cercabile, sempre aggiornato

---

## Appendice D: Integrazione ITIL

| Pratica ITIL | SOP/Runbook corrispondente |
|---|---|
| **Access Management** | SOP-IAM-001, SOP-IAM-002, SOP-IAM-004 |
| **Deployment Management** | SOP-SRV-001, SOP-WKS-001 |
| **Incident Management** | RB-SVC-001, RB-SEC-001 + tutorial ops07 |
| **Problem Management** | Sezione Post-Azione dei runbook → Problem ticket |
| **Change Management** | SOP-SRV-003 richiede change, SOP-SEC-001 segue processo change |
| **Availability Management** | RB-DB-001 (failover), RB-BKP-001 (ripristino) |
| **Knowledge Management** | Repository Gitea + Wiki.js (questo tutorial) |

---

## Riferimenti

- `09-procedure-operative.md` — Documento sorgente con tutte le SOP e Runbook
- `tutorial_ops07_ch1b_incident_management_lab.md` — War Room, SEV levels, Post-Mortem
- `tutorial_ops08_ch1b_cmdb_implementation_lab.md` — CMDB per tracciare CI nei ticket
- `tutorial_ops04_ch1b_active_directory_ldap_lab.md` — Prerequisito per SOP-IAM-001/002
- ISO 27001 A.12.1.1 — Documented operating procedures
- ITIL 4 Practice Guide: Incident Management, Knowledge Management
