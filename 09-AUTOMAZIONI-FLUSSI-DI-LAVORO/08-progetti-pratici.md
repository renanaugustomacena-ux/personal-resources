---
corso: "Automazioni e Flussi di Lavoro"
fase: "5 — Progetti"
modulo: 8
titolo: "Progetti Pratici di Automazione"
versione: "1.0"
livello: "Avanzato"
prerequisiti:
  - "Moduli 01-07"
  - "Almeno una piattaforma del 09-14"
obiettivi:
  - "Progettare un workflow end-to-end partendo dall'analisi del problema reale"
  - "Applicare tutti i pattern del corso (error handling, testing, governance) in un progetto completo"
  - "Documentare decisioni architetturali con ADR e diagrammi di flusso"
  - "Implementare monitoring, alerting e rollback per workflow in produzione"
  - "Presentare il progetto con metriche di ROI, copertura test e lessons learned"
tag: [progetti, capstone, end-to-end, portfolio, adr, monitoring]
---

# Progetti Pratici di Automazione — Guida Completa

> **Modulo del corso:** Automazioni e Flussi di Lavoro
> **Posizione:** Fase 6 — Capstone · Modulo 08
> **Prerequisiti:** Moduli 01-07 e almeno una piattaforma del 09-14.
> **Obiettivi:** progettare e implementare workflow end-to-end di valore reale, applicando tutti i pattern del corso.
> **Tempo:** lab 480-720 min (2-4 progetti completi)
> **Livello:** proficient (Dreyfus 4)
> **Ultimo aggiornamento:** 2026-05-24

> **Obiettivi di apprendimento**
>
> 1. Progettare un workflow end-to-end partendo dall'analisi del problema reale
> 2. Applicare tutti i pattern del corso (error handling, testing, governance) in un progetto completo
> 3. Documentare decisioni architetturali con ADR e diagrammi di flusso
> 4. Implementare monitoring, alerting e rollback per workflow in produzione
> 5. Presentare il progetto con metriche di ROI, copertura test e lessons learned
>
> **Prerequisiti:** [Modulo 01](01-fondamenti-automazione.md) fino a [Modulo 07](07-governance-best-practices.md) e almeno una piattaforma del 09-14
> **Tempo stimato:** 8-12 ore · **Livello:** Avanzato

## Idee guida

1. **Scegli un progetto che risolve dolore reale.** Hobby project = abandoned project.
2. **Vincoli sono amici.** Cap budget, tempo, complessita: producono progetti consegnabili.
3. **Documenta ogni decisione architetturale.** "Perche n8n e non Zapier" e la storia che salva il prossimo dev.
4. **Test prima di prod.** Mai lanciare workflow nuovo direttamente in prod.

---

## Indice

1. [Panoramica](#panoramica)
2. [Progetto 1: Onboarding Automatico Dipendenti](#progetto-1-onboarding-automatico-dipendenti)
3. [Progetto 2: Monitoraggio e Alert Infrastruttura](#progetto-2-monitoraggio-e-alert-infrastruttura)
4. [Progetto 3: Gestione Automatica Patch](#progetto-3-gestione-automatica-patch)
5. [Progetto 4: Backup Verification Automatico](#progetto-4-backup-verification-automatico)
6. [Progetto 5: Report Automatico Settimanale](#progetto-5-report-automatico-settimanale)
7. [Progetto 6: Automazione Gestione Ticket](#progetto-6-automazione-gestione-ticket)
8. [Progetto 7: Dismissione Utente Automatica](#progetto-7-dismissione-utente-automatica)
9. [Progetto 8: CI/CD per Automazioni](#progetto-8-cicd-per-automazioni)
10. [Tabella Riepilogativa](#tabella-riepilogativa)
11. [Best Practices per Progetti](#best-practices-per-progetti)

---

## Panoramica

### Learning by Doing: perche i progetti pratici contano

La teoria dell'automazione e fondamentale, ma senza applicazione pratica rimane un esercizio accademico. I progetti pratici rappresentano il ponte tra la conoscenza teorica e la competenza operativa reale. Quando si costruisce un workflow di onboarding automatico, non si impara soltanto a chiamare le API di Microsoft Graph: si impara a gestire errori imprevisti, a progettare rollback affidabili, a strutturare log che siano realmente utili in fase di debug.

Ogni progetto in questa guida e stato progettato per replicare scenari reali che un team IT affronta quotidianamente. Non si tratta di esercizi didattici semplificati, ma di implementazioni complete che possono essere adattate e messe in produzione. Il valore di ciascun progetto risiede non solo nel risultato finale, ma nel processo di costruzione: l'analisi dei requisiti, la scelta delle tecnologie, la gestione degli errori, il testing e la documentazione.

### Progressione dei progetti: semplice, intermedio, avanzato

I progetti sono organizzati secondo una progressione di complessita crescente:

- **Progetti 1-2** (Base): Introducono i concetti fondamentali di automazione workflow, integrazione API e scripting. Richiedono conoscenze di base di PowerShell, Python e una piattaforma low-code come n8n.
- **Progetti 3-5** (Intermedio): Combinano piu tecnologie e richiedono gestione di stati complessi, approvazioni manuali integrate nel flusso e generazione di report strutturati.
- **Progetti 6-8** (Avanzato): Affrontano scenari complessi con logica decisionale articolata, integrazioni multiple simultanee e pratiche DevOps applicate all'automazione stessa.

Si consiglia di affrontare i progetti in ordine sequenziale: le competenze acquisite in ciascun progetto costituiscono i prerequisiti per quelli successivi.

---

## Progetto 1: Onboarding Automatico Dipendenti

### Obiettivo

Automatizzare l'intero processo di onboarding di un nuovo dipendente, dalla ricezione della richiesta HR fino alla notifica al manager con tutte le credenziali e gli accessi configurati. L'obiettivo e eliminare completamente gli interventi manuali per le operazioni standard, riducendo il tempo di onboarding da giorni a minuti e azzerando gli errori di configurazione.

### Workflow

Il flusso di onboarding automatico si articola in otto fasi principali:

1. **Ricezione richiesta**: HR compila un modulo strutturato (Microsoft Forms, ServiceNow, Jira Service Management) con i dati del nuovo dipendente: nome, cognome, dipartimento, ruolo, manager, data di inizio, sede.
2. **Creazione account Active Directory**: Uno script PowerShell genera l'account utente in AD con attributi standard, password temporanea, OU corretta in base al dipartimento.
3. **Assegnazione gruppi di sicurezza**: In base al dipartimento e al ruolo specificati, l'utente viene aggiunto automaticamente ai gruppi di sicurezza appropriati (accesso file share, stampanti, applicazioni).
4. **Creazione casella Microsoft 365**: Tramite Microsoft Graph API, viene assegnata la licenza appropriata e creata la casella di posta con le impostazioni standard dell'organizzazione.
5. **Creazione account applicativi**: Per ogni applicazione aziendale rilevante per il ruolo, viene creato l'account tramite API (Slack, Confluence, Jira, sistemi ERP).
6. **Invio email di benvenuto**: Un'email strutturata con credenziali temporanee, link al portale self-service per il cambio password e documentazione di onboarding viene inviata al nuovo dipendente.
7. **Notifica al manager**: Il manager riceve una notifica (email o Slack) con conferma del completamento dell'onboarding e riepilogo degli accessi configurati.
8. **Logging per audit**: Tutte le azioni eseguite vengono registrate in un log strutturato per finalita di compliance e audit.

### Implementazione

#### Design del workflow n8n

Il workflow n8n funge da orchestratore centrale. La struttura prevede:

```
[Webhook/Form Trigger] --> [Validazione Dati] --> [Creazione AD User]
    --> [Assegnazione Gruppi] --> [Licenza M365] --> [Account Applicativi]
    --> [Email Benvenuto] --> [Notifica Manager] --> [Log Audit]
```

Ogni nodo include gestione errori con percorso alternativo (error branch) che attiva la procedura di rollback e notifica il team IT.

Configurazione del nodo Webhook in n8n:

```json
{
  "nodes": [
    {
      "name": "Webhook Onboarding",
      "type": "n8n-nodes-base.webhook",
      "parameters": {
        "httpMethod": "POST",
        "path": "onboarding",
        "authentication": "headerAuth",
        "responseMode": "responseNode"
      }
    },
    {
      "name": "Validazione Dati",
      "type": "n8n-nodes-base.if",
      "parameters": {
        "conditions": {
          "string": [
            {
              "value1": "={{ $json.nome }}",
              "operation": "isNotEmpty"
            },
            {
              "value1": "={{ $json.cognome }}",
              "operation": "isNotEmpty"
            },
            {
              "value1": "={{ $json.dipartimento }}",
              "operation": "isNotEmpty"
            },
            {
              "value1": "={{ $json.ruolo }}",
              "operation": "isNotEmpty"
            }
          ]
        }
      }
    }
  ]
}
```

#### Script PowerShell per operazioni Active Directory

```powershell
# onboarding-ad.ps1 - Creazione utente e assegnazione gruppi AD

param(
    [Parameter(Mandatory=$true)][string]$Nome,
    [Parameter(Mandatory=$true)][string]$Cognome,
    [Parameter(Mandatory=$true)][string]$Dipartimento,
    [Parameter(Mandatory=$true)][string]$Ruolo,
    [Parameter(Mandatory=$true)][string]$Manager
)

# Modulo Active Directory
Import-Module ActiveDirectory

# Generazione username (prima lettera nome + cognome, lowercase)
$Username = ($Nome.Substring(0,1) + $Cognome).ToLower() -replace '[^a-z0-9]',''
$Email = "$Username@azienda.com"

# Verifica unicita username
$Counter = 1
$OriginalUsername = $Username
while (Get-ADUser -Filter "SamAccountName -eq '$Username'" -ErrorAction SilentlyContinue) {
    $Username = "$OriginalUsername$Counter"
    $Email = "$Username@azienda.com"
    $Counter++
}

# Generazione password temporanea sicura
Add-Type -AssemblyName System.Web
$TempPassword = [System.Web.Security.Membership]::GeneratePassword(16, 3)
$SecurePassword = ConvertTo-SecureString $TempPassword -AsPlainText -Force

# Mappatura dipartimento -> OU
$OUMap = @{
    "IT"            = "OU=IT,OU=Dipendenti,DC=azienda,DC=local"
    "HR"            = "OU=HR,OU=Dipendenti,DC=azienda,DC=local"
    "Finance"       = "OU=Finance,OU=Dipendenti,DC=azienda,DC=local"
    "Sales"         = "OU=Sales,OU=Dipendenti,DC=azienda,DC=local"
    "Marketing"     = "OU=Marketing,OU=Dipendenti,DC=azienda,DC=local"
    "Engineering"   = "OU=Engineering,OU=Dipendenti,DC=azienda,DC=local"
}

$TargetOU = $OUMap[$Dipartimento]
if (-not $TargetOU) {
    $TargetOU = "OU=Generale,OU=Dipendenti,DC=azienda,DC=local"
}

# Creazione utente AD
try {
    $NewUser = New-ADUser `
        -Name "$Nome $Cognome" `
        -GivenName $Nome `
        -Surname $Cognome `
        -SamAccountName $Username `
        -UserPrincipalName $Email `
        -EmailAddress $Email `
        -Department $Dipartimento `
        -Title $Ruolo `
        -Manager (Get-ADUser -Filter "Name -eq '$Manager'" | Select-Object -ExpandProperty DistinguishedName) `
        -Path $TargetOU `
        -AccountPassword $SecurePassword `
        -ChangePasswordAtLogon $true `
        -Enabled $true `
        -PassThru

    Write-Output "SUCCESS|$Username|$Email|$TempPassword"
} catch {
    Write-Error "ERRORE creazione utente AD: $_"
    exit 1
}

# Mappatura gruppi di sicurezza per dipartimento e ruolo
$GruppiBase = @("VPN-Users", "WiFi-Corporate", "AllEmployees")

$GruppiDipartimento = @{
    "IT"          = @("IT-Staff", "ServerAccess", "Admin-Tools")
    "HR"          = @("HR-Staff", "HR-Confidential", "PayrollView")
    "Finance"     = @("Finance-Staff", "ERP-Users", "Finance-Reports")
    "Sales"       = @("Sales-Staff", "CRM-Users", "Sales-Reports")
    "Marketing"   = @("Marketing-Staff", "CMS-Users", "Analytics-View")
    "Engineering" = @("Eng-Staff", "DevTools", "GitAccess", "CI-CD-Users")
}

$GruppiRuolo = @{
    "Manager"     = @("Managers", "ApprovalWorkflow", "BudgetView")
    "Director"    = @("Directors", "Managers", "ExecutiveReports")
    "Developer"   = @("Developers", "CodeReview", "StagingAccess")
    "Analyst"     = @("Analysts", "ReportingTools", "DataWarehouse")
}

# Assegnazione gruppi base
foreach ($Gruppo in $GruppiBase) {
    try {
        Add-ADGroupMember -Identity $Gruppo -Members $Username
        Write-Output "Gruppo assegnato: $Gruppo"
    } catch {
        Write-Warning "Impossibile aggiungere a $Gruppo : $_"
    }
}

# Assegnazione gruppi dipartimento
if ($GruppiDipartimento.ContainsKey($Dipartimento)) {
    foreach ($Gruppo in $GruppiDipartimento[$Dipartimento]) {
        try {
            Add-ADGroupMember -Identity $Gruppo -Members $Username
            Write-Output "Gruppo dipartimento assegnato: $Gruppo"
        } catch {
            Write-Warning "Impossibile aggiungere a $Gruppo : $_"
        }
    }
}

# Assegnazione gruppi ruolo
if ($GruppiRuolo.ContainsKey($Ruolo)) {
    foreach ($Gruppo in $GruppiRuolo[$Ruolo]) {
        try {
            Add-ADGroupMember -Identity $Gruppo -Members $Username
            Write-Output "Gruppo ruolo assegnato: $Gruppo"
        } catch {
            Write-Warning "Impossibile aggiungere a $Gruppo : $_"
        }
    }
}
```

#### Chiamate Microsoft Graph API

```python
# microsoft_graph_onboarding.py - Gestione licenze e casella M365

import requests
import json
from msal import ConfidentialClientApplication

class GraphAPIClient:
    def __init__(self, tenant_id, client_id, client_secret):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://graph.microsoft.com/v1.0"
        self.token = self._get_token()

    def _get_token(self):
        app = ConfidentialClientApplication(
            self.client_id,
            authority=f"https://login.microsoftonline.com/{self.tenant_id}",
            client_credential=self.client_secret
        )
        result = app.acquire_token_for_client(
            scopes=["https://graph.microsoft.com/.default"]
        )
        if "access_token" in result:
            return result["access_token"]
        raise Exception(f"Errore acquisizione token: {result.get('error_description')}")

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def assegna_licenza(self, user_principal_name, sku_id):
        """Assegna una licenza Microsoft 365 all'utente."""
        url = f"{self.base_url}/users/{user_principal_name}/assignLicense"
        payload = {
            "addLicenses": [{"skuId": sku_id, "disabledPlans": []}],
            "removeLicenses": []
        }
        response = requests.post(url, headers=self._headers(), json=payload)
        if response.status_code == 200:
            return {"status": "successo", "dettaglio": "Licenza assegnata"}
        raise Exception(f"Errore assegnazione licenza: {response.status_code} - {response.text}")

    def configura_casella(self, user_principal_name, lingua="it-IT", fuso_orario="Europe/Rome"):
        """Configura le impostazioni della casella di posta."""
        url = f"{self.base_url}/users/{user_principal_name}/mailboxSettings"
        payload = {
            "language": {"locale": lingua},
            "timeZone": fuso_orario,
            "automaticRepliesSetting": {"status": "disabled"}
        }
        response = requests.patch(url, headers=self._headers(), json=payload)
        if response.status_code == 200:
            return {"status": "successo", "dettaglio": "Casella configurata"}
        raise Exception(f"Errore configurazione casella: {response.status_code}")

    def invia_email_benvenuto(self, destinatario, nome, username, password_temp):
        """Invia email di benvenuto con credenziali temporanee."""
        url = f"{self.base_url}/users/noreply@azienda.com/sendMail"
        payload = {
            "message": {
                "subject": f"Benvenuto in azienda, {nome}!",
                "body": {
                    "contentType": "HTML",
                    "content": f"""
                    <h2>Benvenuto nel team!</h2>
                    <p>Il tuo account aziendale e stato configurato. Ecco le tue credenziali:</p>
                    <ul>
                        <li><strong>Username:</strong> {username}</li>
                        <li><strong>Email:</strong> {destinatario}</li>
                        <li><strong>Password temporanea:</strong> {password_temp}</li>
                    </ul>
                    <p><strong>Azione richiesta:</strong> Accedi al portale
                    <a href="https://portal.azienda.com">portal.azienda.com</a>
                    e modifica la password al primo accesso.</p>
                    <p>Per supporto tecnico: helpdesk@azienda.com</p>
                    """
                },
                "toRecipients": [
                    {"emailAddress": {"address": destinatario}}
                ]
            }
        }
        response = requests.post(url, headers=self._headers(), json=payload)
        if response.status_code == 202:
            return {"status": "successo", "dettaglio": "Email inviata"}
        raise Exception(f"Errore invio email: {response.status_code}")
```

#### Gestione errori e rollback

La gestione degli errori e critica in un workflow di onboarding. Ogni fase deve prevedere un meccanismo di rollback:

```python
# rollback_onboarding.py - Procedura di rollback per onboarding fallito

import logging
from datetime import datetime

logger = logging.getLogger("onboarding_rollback")

class OnboardingRollback:
    def __init__(self):
        self.azioni_completate = []

    def registra_azione(self, tipo, dettaglio):
        self.azioni_completate.append({
            "tipo": tipo,
            "dettaglio": dettaglio,
            "timestamp": datetime.utcnow().isoformat()
        })

    def esegui_rollback(self, username, motivo):
        """Esegue il rollback in ordine inverso rispetto alle azioni completate."""
        logger.warning(f"Avvio rollback per {username}. Motivo: {motivo}")
        errori_rollback = []

        for azione in reversed(self.azioni_completate):
            try:
                if azione["tipo"] == "account_ad":
                    self._rimuovi_account_ad(username)
                elif azione["tipo"] == "gruppi_ad":
                    self._rimuovi_da_gruppi(username, azione["dettaglio"])
                elif azione["tipo"] == "licenza_m365":
                    self._revoca_licenza(username)
                elif azione["tipo"] == "account_app":
                    self._disabilita_account_app(azione["dettaglio"])
                logger.info(f"Rollback completato: {azione['tipo']}")
            except Exception as e:
                errori_rollback.append({"azione": azione["tipo"], "errore": str(e)})
                logger.error(f"Errore rollback {azione['tipo']}: {e}")

        if errori_rollback:
            self._notifica_intervento_manuale(username, errori_rollback)

        return {
            "status": "rollback_completato" if not errori_rollback else "rollback_parziale",
            "errori": errori_rollback
        }

    def _rimuovi_account_ad(self, username):
        """Rimuove l'account AD creato."""
        import subprocess
        result = subprocess.run(
            ["powershell", "-Command",
             f"Remove-ADUser -Identity '{username}' -Confirm:$false"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            raise Exception(f"Errore rimozione AD: {result.stderr}")

    def _rimuovi_da_gruppi(self, username, gruppi):
        """Rimuove l'utente da tutti i gruppi assegnati."""
        import subprocess
        for gruppo in gruppi:
            subprocess.run(
                ["powershell", "-Command",
                 f"Remove-ADGroupMember -Identity '{gruppo}' -Members '{username}' -Confirm:$false"],
                capture_output=True, text=True
            )

    def _revoca_licenza(self, username):
        """Revoca la licenza Microsoft 365."""
        # Implementazione tramite Graph API
        pass

    def _disabilita_account_app(self, dettaglio_app):
        """Disabilita l'account nell'applicazione specificata."""
        # Implementazione specifica per ogni applicazione
        pass

    def _notifica_intervento_manuale(self, username, errori):
        """Notifica il team IT per intervento manuale sui rollback falliti."""
        logger.critical(
            f"INTERVENTO MANUALE RICHIESTO per {username}. "
            f"Rollback parzialmente fallito: {errori}"
        )
```

### Variante Python

```python
# onboarding_completo.py - Script completo di onboarding automatico

import os
import json
import logging
import subprocess
import requests
import secrets
import string
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("onboarding")

@dataclass
class DipendenteDati:
    nome: str
    cognome: str
    dipartimento: str
    ruolo: str
    manager: str
    data_inizio: str
    sede: str
    email_personale: Optional[str] = None

@dataclass
class RisultatoOnboarding:
    username: str
    email: str
    password_temp: str
    gruppi: list
    licenze: list
    account_app: list
    timestamp: str
    stato: str

class OnboardingAutomatico:
    def __init__(self, config_path="config/onboarding.json"):
        with open(config_path) as f:
            self.config = json.load(f)
        self.azioni_log = []

    def genera_password(self, lunghezza=16):
        caratteri = string.ascii_letters + string.digits + "!@#$%&*"
        return "".join(secrets.choice(caratteri) for _ in range(lunghezza))

    def genera_username(self, nome, cognome):
        base = (nome[0] + cognome).lower()
        base = "".join(c for c in base if c.isalnum())
        # Verifica unicita tramite AD
        result = subprocess.run(
            ["powershell", "-Command",
             f"Get-ADUser -Filter \"SamAccountName -eq '{base}'\""],
            capture_output=True, text=True
        )
        if result.stdout.strip():
            contatore = 1
            while True:
                candidato = f"{base}{contatore}"
                result = subprocess.run(
                    ["powershell", "-Command",
                     f"Get-ADUser -Filter \"SamAccountName -eq '{candidato}'\""],
                    capture_output=True, text=True
                )
                if not result.stdout.strip():
                    return candidato
                contatore += 1
        return base

    def crea_utente_ad(self, dati: DipendenteDati, username: str, password: str):
        logger.info(f"Creazione account AD per {username}")
        script = f"""
        New-ADUser -Name '{dati.nome} {dati.cognome}' `
            -GivenName '{dati.nome}' -Surname '{dati.cognome}' `
            -SamAccountName '{username}' `
            -UserPrincipalName '{username}@azienda.com' `
            -Department '{dati.dipartimento}' -Title '{dati.ruolo}' `
            -AccountPassword (ConvertTo-SecureString '{password}' -AsPlainText -Force) `
            -ChangePasswordAtLogon $true -Enabled $true
        """
        result = subprocess.run(
            ["powershell", "-Command", script],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            raise Exception(f"Errore creazione AD: {result.stderr}")
        self.azioni_log.append({"fase": "creazione_ad", "stato": "completato"})
        return True

    def assegna_gruppi(self, username: str, dipartimento: str, ruolo: str):
        logger.info(f"Assegnazione gruppi per {username}")
        gruppi = self.config["gruppi_base"].copy()
        gruppi.extend(self.config["gruppi_dipartimento"].get(dipartimento, []))
        gruppi.extend(self.config["gruppi_ruolo"].get(ruolo, []))

        assegnati = []
        for gruppo in gruppi:
            try:
                subprocess.run(
                    ["powershell", "-Command",
                     f"Add-ADGroupMember -Identity '{gruppo}' -Members '{username}'"],
                    capture_output=True, text=True, check=True
                )
                assegnati.append(gruppo)
            except subprocess.CalledProcessError as e:
                logger.warning(f"Gruppo {gruppo} non assegnato: {e}")

        self.azioni_log.append({"fase": "gruppi", "stato": "completato", "gruppi": assegnati})
        return assegnati

    def configura_m365(self, username: str, dipartimento: str):
        logger.info(f"Configurazione Microsoft 365 per {username}")
        upn = f"{username}@azienda.com"
        sku_map = self.config.get("licenze_dipartimento", {})
        sku_id = sku_map.get(dipartimento, self.config["licenza_default"])

        graph = GraphAPIClient(
            self.config["tenant_id"],
            self.config["client_id"],
            self.config["client_secret"]
        )
        graph.assegna_licenza(upn, sku_id)
        graph.configura_casella(upn)
        self.azioni_log.append({"fase": "m365", "stato": "completato"})
        return [sku_id]

    def crea_account_applicativi(self, dati: DipendenteDati, username: str, email: str):
        logger.info(f"Creazione account applicativi per {username}")
        account_creati = []
        app_config = self.config.get("applicazioni_ruolo", {}).get(dati.ruolo, [])

        for app in app_config:
            try:
                if app == "slack":
                    self._crea_account_slack(email, dati.nome, dati.cognome)
                elif app == "jira":
                    self._crea_account_jira(email, dati.nome, dati.cognome)
                elif app == "confluence":
                    self._crea_account_confluence(email, dati.nome, dati.cognome)
                account_creati.append(app)
            except Exception as e:
                logger.warning(f"Account {app} non creato: {e}")

        self.azioni_log.append({"fase": "account_app", "stato": "completato", "app": account_creati})
        return account_creati

    def _crea_account_slack(self, email, nome, cognome):
        url = "https://slack.com/api/admin.users.invite"
        headers = {"Authorization": f"Bearer {self.config['slack_token']}"}
        payload = {
            "email": email,
            "channel_ids": ",".join(self.config.get("slack_canali_default", [])),
            "real_name": f"{nome} {cognome}"
        }
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()

    def _crea_account_jira(self, email, nome, cognome):
        url = f"{self.config['jira_url']}/rest/api/3/user"
        auth = (self.config["jira_user"], self.config["jira_token"])
        payload = {
            "emailAddress": email,
            "displayName": f"{nome} {cognome}",
            "products": ["jira-software"]
        }
        response = requests.post(url, auth=auth, json=payload)
        response.raise_for_status()

    def _crea_account_confluence(self, email, nome, cognome):
        url = f"{self.config['confluence_url']}/wiki/rest/api/user"
        auth = (self.config["confluence_user"], self.config["confluence_token"])
        payload = {"emailAddress": email, "displayName": f"{nome} {cognome}"}
        response = requests.post(url, auth=auth, json=payload)
        response.raise_for_status()

    def esegui_onboarding(self, dati: DipendenteDati) -> RisultatoOnboarding:
        logger.info(f"Avvio onboarding per {dati.nome} {dati.cognome}")
        password_temp = self.genera_password()
        username = self.genera_username(dati.nome, dati.cognome)
        email = f"{username}@azienda.com"

        try:
            self.crea_utente_ad(dati, username, password_temp)
            gruppi = self.assegna_gruppi(username, dati.dipartimento, dati.ruolo)
            licenze = self.configura_m365(username, dati.dipartimento)
            account_app = self.crea_account_applicativi(dati, username, email)

            # Invio email di benvenuto
            graph = GraphAPIClient(
                self.config["tenant_id"],
                self.config["client_id"],
                self.config["client_secret"]
            )
            graph.invia_email_benvenuto(email, dati.nome, username, password_temp)

            risultato = RisultatoOnboarding(
                username=username, email=email, password_temp=password_temp,
                gruppi=gruppi, licenze=licenze, account_app=account_app,
                timestamp=datetime.utcnow().isoformat(), stato="completato"
            )
            self._salva_log_audit(dati, risultato)
            logger.info(f"Onboarding completato per {username}")
            return risultato

        except Exception as e:
            logger.error(f"Errore onboarding: {e}")
            rollback = OnboardingRollback()
            rollback.azioni_completate = self.azioni_log
            rollback.esegui_rollback(username, str(e))
            raise

    def _salva_log_audit(self, dati, risultato):
        log_entry = {
            "evento": "onboarding_completato",
            "dipendente": asdict(dati),
            "risultato": asdict(risultato),
            "azioni": self.azioni_log,
            "timestamp": datetime.utcnow().isoformat()
        }
        log_path = f"logs/onboarding_{risultato.username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs("logs", exist_ok=True)
        with open(log_path, "w") as f:
            json.dump(log_entry, f, indent=2, default=str)
```

---

## Progetto 2: Monitoraggio e Alert Infrastruttura

### Obiettivo

Costruire un sistema di monitoraggio infrastrutturale automatizzato che verifichi lo stato di salute di server, dispositivi di rete e servizi critici, generando alert intelligenti (non ridondanti) e producendo report giornalieri di sintesi. Il sistema deve essere in grado di distinguere tra problemi transitori e situazioni critiche persistenti, evitando l'alert fatigue.

### Componenti

Il sistema si articola in sei componenti principali:

- **Health check server**: Monitoraggio CPU, RAM, disco, servizi Windows/Linux critici.
- **Monitoraggio dispositivi di rete**: Verifica raggiungibilita tramite ping e metriche SNMP (utilizzo porte, errori interfaccia, uptime).
- **Monitoraggio scadenza certificati**: Controllo periodico dei certificati SSL/TLS con alert 30, 14 e 7 giorni prima della scadenza.
- **Verifica backup**: Conferma che i backup pianificati siano stati completati con successo.
- **Instradamento alert**: Logica di routing degli alert verso il canale appropriato (Slack per warning, email per critical, PagerDuty per emergency).
- **Report giornaliero di sintesi**: Aggregazione di tutte le metriche in un report leggibile distribuito ogni mattina.

### Implementazione

#### Script Python di monitoraggio

```python
# infra_monitor.py - Monitoraggio infrastruttura completo

import psutil
import socket
import ssl
import subprocess
import json
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("infra_monitor")

@dataclass
class MetricaServer:
    hostname: str
    cpu_percent: float
    ram_percent: float
    disco_percent: dict
    servizi_attivi: list
    servizi_inattivi: list
    uptime_ore: float
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

@dataclass
class AlertDefinizione:
    livello: str       # warning, critical, emergency
    componente: str
    messaggio: str
    metrica: Optional[float] = None
    soglia: Optional[float] = None

class MonitorInfrastruttura:
    def __init__(self, config_path="config/monitor.json"):
        with open(config_path) as f:
            self.config = json.load(f)
        self.alert_buffer = []

    def controlla_server_locale(self) -> MetricaServer:
        """Raccoglie metriche dal server locale."""
        cpu = psutil.cpu_percent(interval=2)
        ram = psutil.virtual_memory().percent
        dischi = {}
        for partizione in psutil.disk_partitions():
            try:
                uso = psutil.disk_usage(partizione.mountpoint)
                dischi[partizione.mountpoint] = uso.percent
            except PermissionError:
                continue

        # Controllo servizi
        servizi_config = self.config.get("servizi_monitorati", [])
        servizi_attivi = []
        servizi_inattivi = []
        for servizio in servizi_config:
            try:
                status = subprocess.run(
                    ["systemctl", "is-active", servizio],
                    capture_output=True, text=True
                )
                if status.stdout.strip() == "active":
                    servizi_attivi.append(servizio)
                else:
                    servizi_inattivi.append(servizio)
            except Exception:
                servizi_inattivi.append(servizio)

        # Uptime
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = (datetime.now() - boot_time).total_seconds() / 3600

        metrica = MetricaServer(
            hostname=socket.gethostname(),
            cpu_percent=cpu, ram_percent=ram,
            disco_percent=dischi,
            servizi_attivi=servizi_attivi,
            servizi_inattivi=servizi_inattivi,
            uptime_ore=round(uptime, 2)
        )

        # Valutazione soglie
        if cpu > self.config["soglie"]["cpu_critical"]:
            self.alert_buffer.append(AlertDefinizione(
                "critical", "CPU", f"CPU al {cpu}% su {metrica.hostname}", cpu,
                self.config["soglie"]["cpu_critical"]
            ))
        elif cpu > self.config["soglie"]["cpu_warning"]:
            self.alert_buffer.append(AlertDefinizione(
                "warning", "CPU", f"CPU al {cpu}% su {metrica.hostname}", cpu,
                self.config["soglie"]["cpu_warning"]
            ))

        if ram > self.config["soglie"]["ram_critical"]:
            self.alert_buffer.append(AlertDefinizione(
                "critical", "RAM", f"RAM al {ram}% su {metrica.hostname}", ram,
                self.config["soglie"]["ram_critical"]
            ))

        for mount, percent in dischi.items():
            if percent > self.config["soglie"]["disco_critical"]:
                self.alert_buffer.append(AlertDefinizione(
                    "critical", "Disco",
                    f"Disco {mount} al {percent}% su {metrica.hostname}",
                    percent, self.config["soglie"]["disco_critical"]
                ))

        for servizio in servizi_inattivi:
            self.alert_buffer.append(AlertDefinizione(
                "critical", "Servizio",
                f"Servizio {servizio} inattivo su {metrica.hostname}"
            ))

        return metrica

    def controlla_certificato(self, hostname, porta=443):
        """Verifica la scadenza di un certificato SSL/TLS."""
        try:
            context = ssl.create_default_context()
            with socket.create_connection((hostname, porta), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    scadenza = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
                    giorni_rimanenti = (scadenza - datetime.utcnow()).days

                    if giorni_rimanenti <= 7:
                        self.alert_buffer.append(AlertDefinizione(
                            "emergency", "Certificato",
                            f"Certificato {hostname} scade tra {giorni_rimanenti} giorni!"
                        ))
                    elif giorni_rimanenti <= 14:
                        self.alert_buffer.append(AlertDefinizione(
                            "critical", "Certificato",
                            f"Certificato {hostname} scade tra {giorni_rimanenti} giorni"
                        ))
                    elif giorni_rimanenti <= 30:
                        self.alert_buffer.append(AlertDefinizione(
                            "warning", "Certificato",
                            f"Certificato {hostname} scade tra {giorni_rimanenti} giorni"
                        ))

                    return {"hostname": hostname, "scadenza": scadenza.isoformat(),
                            "giorni_rimanenti": giorni_rimanenti}
        except Exception as e:
            self.alert_buffer.append(AlertDefinizione(
                "critical", "Certificato",
                f"Impossibile verificare certificato {hostname}: {e}"
            ))
            return {"hostname": hostname, "errore": str(e)}

    def ping_dispositivo(self, host, tentativi=3):
        """Verifica raggiungibilita di un dispositivo di rete."""
        try:
            result = subprocess.run(
                ["ping", "-c", str(tentativi), "-W", "2", host],
                capture_output=True, text=True, timeout=15
            )
            raggiungibile = result.returncode == 0
            if not raggiungibile:
                self.alert_buffer.append(AlertDefinizione(
                    "critical", "Rete",
                    f"Dispositivo {host} non raggiungibile"
                ))
            return {"host": host, "raggiungibile": raggiungibile}
        except subprocess.TimeoutExpired:
            self.alert_buffer.append(AlertDefinizione(
                "critical", "Rete", f"Timeout ping verso {host}"
            ))
            return {"host": host, "raggiungibile": False, "errore": "timeout"}


class AlertRouter:
    """Instrada gli alert verso il canale appropriato."""

    def __init__(self, config):
        self.config = config
        self.alert_inviati = {}  # Deduplicazione

    def instrada(self, alert: AlertDefinizione):
        chiave = f"{alert.componente}:{alert.messaggio}"
        ora = datetime.utcnow()

        # Deduplicazione: non inviare lo stesso alert entro 15 minuti
        if chiave in self.alert_inviati:
            ultimo_invio = self.alert_inviati[chiave]
            if (ora - ultimo_invio).total_seconds() < 900:
                logger.info(f"Alert duplicato soppresso: {chiave}")
                return

        if alert.livello == "emergency":
            self._invia_pagerduty(alert)
            self._invia_slack(alert, canale="#incidents")
            self._invia_email(alert, destinatari=self.config["email_oncall"])
        elif alert.livello == "critical":
            self._invia_slack(alert, canale="#alerts-critical")
            self._invia_email(alert, destinatari=self.config["email_it"])
        elif alert.livello == "warning":
            self._invia_slack(alert, canale="#alerts-warning")

        self.alert_inviati[chiave] = ora

    def _invia_slack(self, alert, canale):
        emoji = {"emergency": "🚨", "critical": "🔴", "warning": "🟡"}
        payload = {
            "channel": canale,
            "text": f"{emoji.get(alert.livello, '')} [{alert.livello.upper()}] {alert.messaggio}",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            f"*{alert.livello.upper()}* | `{alert.componente}`\n"
                            f"{alert.messaggio}"
                        )
                    }
                }
            ]
        }
        requests.post(
            self.config["slack_webhook"],
            json=payload, timeout=10
        )

    def _invia_pagerduty(self, alert):
        payload = {
            "routing_key": self.config["pagerduty_key"],
            "event_action": "trigger",
            "payload": {
                "summary": alert.messaggio,
                "severity": "critical",
                "source": alert.componente
            }
        }
        requests.post(
            "https://events.pagerduty.com/v2/enqueue",
            json=payload, timeout=10
        )

    def _invia_email(self, alert, destinatari):
        # Implementazione invio email tramite SMTP o API
        pass
```

#### Integrazione con Grafana

Per la visualizzazione delle metriche si consiglia di esportare i dati verso Prometheus o InfluxDB, collegati a dashboard Grafana. Il file di configurazione del datasource:

```yaml
# grafana/provisioning/datasources/prometheus.yml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false
```

La dashboard JSON puo essere generata automaticamente per visualizzare CPU, RAM, disco e stato servizi per ciascun server monitorato.

---

## Progetto 3: Gestione Automatica Patch

### Obiettivo

Implementare una pipeline completa di gestione delle patch che copra l'intero ciclo: dalla scansione delle patch disponibili, alla classificazione per severita, al testing in ambiente staging, all'approvazione per la produzione, fino al deployment e alla verifica post-installazione. Il tutto deve generare report di compliance conformi alle policy aziendali.

### Workflow

1. **Scansione patch disponibili**: Interrogazione periodica dei repository di aggiornamento (WSUS per Windows, repository APT/YUM per Linux).
2. **Classificazione per severita**: Le patch vengono classificate in critiche (sicurezza), importanti, raccomandate e opzionali.
3. **Test in ambiente staging**: Le patch critiche e importanti vengono automaticamente applicate all'ambiente di staging.
4. **Richiesta approvazione**: Per le patch critiche in produzione, viene generata una richiesta di approvazione al Change Advisory Board.
5. **Deploy in produzione**: Le patch approvate vengono distribuite nella finestra di manutenzione programmata.
6. **Verifica post-deployment**: Dopo l'applicazione, vengono eseguiti controlli di integrita sui servizi e sulle applicazioni.
7. **Report compliance**: Generazione automatica del report sullo stato di conformita di tutti i sistemi.

### Implementazione

#### PowerShell per patching Windows

```powershell
# patch-management.ps1 - Gestione patch Windows automatizzata

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("Scan","Install","Report")]
    [string]$Azione,

    [ValidateSet("Staging","Production")]
    [string]$Ambiente = "Staging",

    [string[]]$ServerList
)

Import-Module PSWindowsUpdate

function Get-PatchDisponibili {
    param([string]$Server)

    $session = New-PSSession -ComputerName $Server -ErrorAction Stop
    $patches = Invoke-Command -Session $session -ScriptBlock {
        Get-WindowsUpdate -MicrosoftUpdate -Verbose
    }
    Remove-PSSession $session

    $classificate = @{
        Critiche      = @()
        Importanti    = @()
        Raccomandate  = @()
        Opzionali     = @()
    }

    foreach ($patch in $patches) {
        switch -Regex ($patch.MsrcSeverity) {
            "Critical"  { $classificate.Critiche += $patch }
            "Important" { $classificate.Importanti += $patch }
            "Moderate"  { $classificate.Raccomandate += $patch }
            default     { $classificate.Opzionali += $patch }
        }
    }

    return @{
        Server      = $Server
        Totale      = $patches.Count
        Dettaglio   = $classificate
        DataScansione = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    }
}

function Install-PatchApprovate {
    param(
        [string]$Server,
        [string[]]$KBList
    )

    $session = New-PSSession -ComputerName $Server -ErrorAction Stop
    $risultato = Invoke-Command -Session $session -ScriptBlock {
        param($KBs)
        $results = @()
        foreach ($kb in $KBs) {
            try {
                $installResult = Install-WindowsUpdate -KBArticleID $kb `
                    -MicrosoftUpdate -AcceptAll -AutoReboot:$false -Confirm:$false
                $results += @{KB = $kb; Stato = "Installata"; Riavvio = $installResult.RebootRequired}
            } catch {
                $results += @{KB = $kb; Stato = "Errore"; Dettaglio = $_.Exception.Message}
            }
        }
        return $results
    } -ArgumentList (,$KBList)

    Remove-PSSession $session
    return $risultato
}

function New-ComplianceReport {
    param([hashtable[]]$ScanResults)

    $report = @{
        DataReport      = Get-Date -Format "yyyy-MM-dd"
        TotaleServer    = $ScanResults.Count
        ServerConformi  = 0
        ServerNonConformi = 0
        PatchMancanti   = @()
        Dettaglio       = @()
    }

    foreach ($scan in $ScanResults) {
        $criticheMancanti = $scan.Dettaglio.Critiche.Count
        $importantiMancanti = $scan.Dettaglio.Importanti.Count

        if ($criticheMancanti -eq 0 -and $importantiMancanti -eq 0) {
            $report.ServerConformi++
        } else {
            $report.ServerNonConformi++
        }

        $report.Dettaglio += @{
            Server              = $scan.Server
            CriticheMancanti    = $criticheMancanti
            ImportantiMancanti  = $importantiMancanti
            Conforme            = ($criticheMancanti -eq 0 -and $importantiMancanti -eq 0)
        }
    }

    $report.PercentualeConformita = [math]::Round(
        ($report.ServerConformi / $report.TotaleServer) * 100, 1
    )

    return $report
}

# Esecuzione principale
switch ($Azione) {
    "Scan" {
        $risultati = @()
        foreach ($server in $ServerList) {
            Write-Output "Scansione $server..."
            $risultati += Get-PatchDisponibili -Server $server
        }
        $risultati | ConvertTo-Json -Depth 5 | Out-File "reports/scan_$(Get-Date -Format 'yyyyMMdd').json"
    }
    "Install" {
        if ($Ambiente -eq "Production") {
            Write-Warning "ATTENZIONE: installazione in produzione. Verificare approvazione CAB."
        }
        # Logica di installazione
    }
    "Report" {
        $scanData = Get-Content "reports/scan_latest.json" | ConvertFrom-Json
        $report = New-ComplianceReport -ScanResults $scanData
        $report | ConvertTo-Json -Depth 5 | Out-File "reports/compliance_$(Get-Date -Format 'yyyyMMdd').json"
        Write-Output "Conformita: $($report.PercentualeConformita)%"
    }
}
```

#### Ansible per patching Linux

```yaml
# playbooks/patch-linux.yml - Playbook Ansible per patching Linux

---
- name: Gestione Patch Linux Automatizzata
  hosts: "{{ target_group | default('staging') }}"
  become: yes
  serial: "{{ batch_size | default(5) }}"
  max_fail_percentage: 20

  vars:
    patch_log_dir: /var/log/patch-management
    report_dir: /opt/reports/patching
    severita_minima: "{{ severity | default('Critical') }}"
    riavvio_automatico: "{{ auto_reboot | default(false) }}"

  pre_tasks:
    - name: Crea directory log
      file:
        path: "{{ item }}"
        state: directory
        mode: '0755'
      loop:
        - "{{ patch_log_dir }}"
        - "{{ report_dir }}"

    - name: Snapshot pre-patch (se VM)
      command: >
        virsh snapshot-create-as {{ inventory_hostname }}
        pre-patch-{{ ansible_date_time.date }}
      delegate_to: "{{ hypervisor_host }}"
      when: is_virtual | default(false)
      ignore_errors: yes

    - name: Verifica servizi critici pre-patch
      service_facts:
      register: servizi_pre

  tasks:
    - name: Aggiornamento cache repository (Debian/Ubuntu)
      apt:
        update_cache: yes
        cache_valid_time: 3600
      when: ansible_os_family == "Debian"

    - name: Aggiornamento cache repository (RHEL/CentOS)
      yum:
        update_cache: yes
      when: ansible_os_family == "RedHat"

    - name: Elenco patch disponibili (Debian/Ubuntu)
      command: apt list --upgradable
      register: patch_disponibili_apt
      changed_when: false
      when: ansible_os_family == "Debian"

    - name: Installazione aggiornamenti di sicurezza (Debian/Ubuntu)
      apt:
        upgrade: dist
        update_cache: yes
        only_upgrade: yes
      register: risultato_apt
      when: ansible_os_family == "Debian"

    - name: Installazione aggiornamenti di sicurezza (RHEL/CentOS)
      yum:
        name: '*'
        state: latest
        security: yes
      register: risultato_yum
      when: ansible_os_family == "RedHat"

    - name: Registra risultato patching
      copy:
        content: |
          Data: {{ ansible_date_time.iso8601 }}
          Server: {{ inventory_hostname }}
          OS: {{ ansible_distribution }} {{ ansible_distribution_version }}
          Risultato APT: {{ risultato_apt | default('N/A') }}
          Risultato YUM: {{ risultato_yum | default('N/A') }}
        dest: "{{ patch_log_dir }}/patch_{{ ansible_date_time.date }}.log"

  post_tasks:
    - name: Verifica servizi critici post-patch
      service_facts:
      register: servizi_post

    - name: Confronto servizi pre/post patch
      debug:
        msg: >
          Servizio {{ item }} stato cambiato:
          {{ servizi_pre.ansible_facts.services[item].state }} ->
          {{ servizi_post.ansible_facts.services[item].state }}
      loop: "{{ servizi_critici | default([]) }}"
      when: >
        servizi_pre.ansible_facts.services[item].state !=
        servizi_post.ansible_facts.services[item].state

    - name: Verifica se riavvio necessario
      stat:
        path: /var/run/reboot-required
      register: reboot_flag
      when: ansible_os_family == "Debian"

    - name: Riavvio se necessario e autorizzato
      reboot:
        reboot_timeout: 300
        msg: "Riavvio post-patch automatico"
      when:
        - reboot_flag.stat.exists | default(false)
        - riavvio_automatico | bool
```

---

## Progetto 4: Backup Verification Automatico

### Obiettivo

Automatizzare la verifica dei backup attraverso restore test periodici. Non basta che un backup venga completato senza errori: deve essere verificato che i dati siano effettivamente recuperabili. Questo progetto implementa un sistema che ripristina automaticamente i backup piu recenti in un ambiente di test, esegue controlli di integrita e genera report sullo stato di affidabilita dei backup.

### Workflow

1. **Schedulazione giornaliera**: Un cron job o un workflow n8n avvia la verifica ogni notte.
2. **Restore in ambiente di test**: L'ultimo backup viene ripristinato in un ambiente isolato.
3. **Controlli di integrita**: Verifica hash, conteggio record, query di test su database.
4. **Test accessibilita dati**: Verifica che file e tabelle siano accessibili e leggibili.
5. **Registrazione risultati**: I risultati vengono salvati in un database di tracking.
6. **Alert su fallimenti**: In caso di errore, viene inviata notifica immediata.
7. **Report settimanale di sintesi**: Ogni lunedi viene generato un report aggregato.

### Implementazione

#### Script Python per verifica backup

```python
# backup_verification.py - Sistema automatico di verifica backup

import os
import json
import hashlib
import subprocess
import logging
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional
import psycopg2
import pyodbc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backup_verify")

@dataclass
class RisultatoVerifica:
    backup_nome: str
    tipo: str                    # "database", "file", "vm"
    data_backup: str
    dimensione_bytes: int
    restore_riuscito: bool
    integrita_ok: bool
    tempo_restore_sec: float
    dettagli: dict = field(default_factory=dict)
    errore: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

class VerificaBackupDB:
    """Verifica backup di database (PostgreSQL e SQL Server)."""

    def __init__(self, config):
        self.config = config

    def verifica_postgresql(self, backup_path, db_test_name="backup_test_restore"):
        """Ripristina e verifica un backup PostgreSQL."""
        logger.info(f"Verifica backup PostgreSQL: {backup_path}")
        inizio = datetime.now()

        try:
            # Drop database di test se esiste
            subprocess.run(
                ["dropdb", "--if-exists", "-h", self.config["pg_host"],
                 "-U", self.config["pg_user"], db_test_name],
                capture_output=True, text=True,
                env={**os.environ, "PGPASSWORD": self.config["pg_password"]}
            )

            # Crea database di test
            subprocess.run(
                ["createdb", "-h", self.config["pg_host"],
                 "-U", self.config["pg_user"], db_test_name],
                capture_output=True, text=True, check=True,
                env={**os.environ, "PGPASSWORD": self.config["pg_password"]}
            )

            # Restore
            result = subprocess.run(
                ["pg_restore", "-h", self.config["pg_host"],
                 "-U", self.config["pg_user"],
                 "-d", db_test_name, "--no-owner", "--no-privileges",
                 backup_path],
                capture_output=True, text=True,
                env={**os.environ, "PGPASSWORD": self.config["pg_password"]}
            )

            tempo_restore = (datetime.now() - inizio).total_seconds()

            # Verifica integrita
            conn = psycopg2.connect(
                host=self.config["pg_host"],
                user=self.config["pg_user"],
                password=self.config["pg_password"],
                dbname=db_test_name
            )
            cur = conn.cursor()

            # Conta tabelle
            cur.execute("""
                SELECT count(*) FROM information_schema.tables
                WHERE table_schema = 'public'
            """)
            num_tabelle = cur.fetchone()[0]

            # Conta righe totali
            cur.execute("""
                SELECT sum(n_live_tup) FROM pg_stat_user_tables
            """)
            num_righe = cur.fetchone()[0] or 0

            # Verifica che le tabelle principali esistano
            cur.execute("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public' ORDER BY table_name
            """)
            tabelle = [row[0] for row in cur.fetchall()]

            conn.close()

            # Pulizia
            subprocess.run(
                ["dropdb", "-h", self.config["pg_host"],
                 "-U", self.config["pg_user"], db_test_name],
                capture_output=True, text=True,
                env={**os.environ, "PGPASSWORD": self.config["pg_password"]}
            )

            return RisultatoVerifica(
                backup_nome=os.path.basename(backup_path),
                tipo="database_postgresql",
                data_backup=datetime.fromtimestamp(
                    os.path.getmtime(backup_path)).isoformat(),
                dimensione_bytes=os.path.getsize(backup_path),
                restore_riuscito=True,
                integrita_ok=num_tabelle > 0,
                tempo_restore_sec=tempo_restore,
                dettagli={
                    "tabelle": num_tabelle,
                    "righe_totali": num_righe,
                    "elenco_tabelle": tabelle
                }
            )

        except Exception as e:
            logger.error(f"Errore verifica PostgreSQL: {e}")
            return RisultatoVerifica(
                backup_nome=os.path.basename(backup_path),
                tipo="database_postgresql",
                data_backup="sconosciuta",
                dimensione_bytes=os.path.getsize(backup_path) if os.path.exists(backup_path) else 0,
                restore_riuscito=False,
                integrita_ok=False,
                tempo_restore_sec=(datetime.now() - inizio).total_seconds(),
                errore=str(e)
            )

    def verifica_sqlserver(self, backup_path, db_test_name="BackupTestRestore"):
        """Ripristina e verifica un backup SQL Server."""
        logger.info(f"Verifica backup SQL Server: {backup_path}")
        inizio = datetime.now()

        try:
            conn_str = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={self.config['mssql_host']};"
                f"DATABASE=master;"
                f"UID={self.config['mssql_user']};"
                f"PWD={self.config['mssql_password']}"
            )
            conn = pyodbc.connect(conn_str, autocommit=True)
            cursor = conn.cursor()

            # Drop database di test se esiste
            cursor.execute(f"""
                IF EXISTS (SELECT name FROM sys.databases WHERE name = '{db_test_name}')
                BEGIN
                    ALTER DATABASE [{db_test_name}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
                    DROP DATABASE [{db_test_name}];
                END
            """)

            # Restore
            cursor.execute(f"""
                RESTORE DATABASE [{db_test_name}]
                FROM DISK = '{backup_path}'
                WITH MOVE N'DataFile' TO N'D:\\SQLData\\{db_test_name}.mdf',
                     MOVE N'LogFile' TO N'D:\\SQLLog\\{db_test_name}_log.ldf',
                     REPLACE, STATS = 10
            """)

            tempo_restore = (datetime.now() - inizio).total_seconds()

            # Verifica integrita con DBCC CHECKDB
            cursor.execute(f"DBCC CHECKDB ([{db_test_name}]) WITH NO_INFOMSGS")

            # Conta tabelle e righe
            conn_test = pyodbc.connect(
                conn_str.replace("DATABASE=master", f"DATABASE={db_test_name}")
            )
            cur_test = conn_test.cursor()
            cur_test.execute("""
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_TYPE = 'BASE TABLE'
            """)
            num_tabelle = cur_test.fetchone()[0]

            conn_test.close()

            # Pulizia
            cursor.execute(f"""
                ALTER DATABASE [{db_test_name}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
                DROP DATABASE [{db_test_name}];
            """)
            conn.close()

            return RisultatoVerifica(
                backup_nome=os.path.basename(backup_path),
                tipo="database_sqlserver",
                data_backup=datetime.fromtimestamp(
                    os.path.getmtime(backup_path)).isoformat(),
                dimensione_bytes=os.path.getsize(backup_path),
                restore_riuscito=True,
                integrita_ok=True,
                tempo_restore_sec=tempo_restore,
                dettagli={"tabelle": num_tabelle, "dbcc_checkdb": "passed"}
            )
        except Exception as e:
            logger.error(f"Errore verifica SQL Server: {e}")
            return RisultatoVerifica(
                backup_nome=os.path.basename(backup_path),
                tipo="database_sqlserver",
                data_backup="sconosciuta",
                dimensione_bytes=os.path.getsize(backup_path) if os.path.exists(backup_path) else 0,
                restore_riuscito=False, integrita_ok=False,
                tempo_restore_sec=(datetime.now() - inizio).total_seconds(),
                errore=str(e)
            )


class VerificaBackupFile:
    """Verifica backup a livello file (tar, zip, rsync)."""

    def verifica_archivio(self, backup_path, checksums_path=None):
        """Verifica integrita di un archivio compresso."""
        logger.info(f"Verifica archivio: {backup_path}")
        inizio = datetime.now()

        try:
            # Test integrita archivio
            if backup_path.endswith(".tar.gz") or backup_path.endswith(".tgz"):
                result = subprocess.run(
                    ["tar", "-tzf", backup_path],
                    capture_output=True, text=True, timeout=3600
                )
            elif backup_path.endswith(".zip"):
                result = subprocess.run(
                    ["unzip", "-t", backup_path],
                    capture_output=True, text=True, timeout=3600
                )
            else:
                raise ValueError(f"Formato non supportato: {backup_path}")

            file_count = len(result.stdout.strip().split("\n"))
            integrita = result.returncode == 0

            # Verifica checksums se disponibili
            checksum_ok = True
            if checksums_path and os.path.exists(checksums_path):
                check_result = subprocess.run(
                    ["sha256sum", "-c", checksums_path],
                    capture_output=True, text=True, cwd=os.path.dirname(backup_path)
                )
                checksum_ok = check_result.returncode == 0

            return RisultatoVerifica(
                backup_nome=os.path.basename(backup_path),
                tipo="file_archivio",
                data_backup=datetime.fromtimestamp(
                    os.path.getmtime(backup_path)).isoformat(),
                dimensione_bytes=os.path.getsize(backup_path),
                restore_riuscito=True,
                integrita_ok=integrita and checksum_ok,
                tempo_restore_sec=(datetime.now() - inizio).total_seconds(),
                dettagli={"file_nell_archivio": file_count, "checksum_ok": checksum_ok}
            )
        except Exception as e:
            return RisultatoVerifica(
                backup_nome=os.path.basename(backup_path),
                tipo="file_archivio",
                data_backup="sconosciuta",
                dimensione_bytes=os.path.getsize(backup_path) if os.path.exists(backup_path) else 0,
                restore_riuscito=False, integrita_ok=False,
                tempo_restore_sec=(datetime.now() - inizio).total_seconds(),
                errore=str(e)
            )
```

---

## Progetto 5: Report Automatico Settimanale

### Obiettivo

Generare automaticamente ogni settimana un report completo sulle operazioni IT, raccogliendo dati da fonti multiple (sistemi di monitoraggio, ticketing, backup, patch management), assemblando il tutto in un documento HTML/PDF professionale e distribuendolo via email ai destinatari configurati.

### Contenuto del Report

Il report settimanale comprende le seguenti sezioni:

- **Riepilogo uptime infrastruttura**: Percentuale di disponibilita per ogni servizio critico.
- **Riepilogo incidenti**: Incidenti aperti, chiusi e in attesa, con tempi medi di risoluzione.
- **Stato conformita patch**: Percentuale di server conformi, patch critiche mancanti.
- **Tasso successo backup**: Percentuale di backup completati e verificati con successo.
- **Utilizzo capacita**: Andamento dell'utilizzo di CPU, RAM e disco con trend.
- **Riepilogo alert di sicurezza**: Alert di sicurezza rilevati e gestiti.
- **Manutenzioni programmate**: Elenco delle finestre di manutenzione previste nella settimana successiva.

### Implementazione

#### Raccolta dati e generazione report con Python e Jinja2

```python
# weekly_report.py - Generazione report settimanale IT

import json
import os
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from dataclasses import dataclass, field
from typing import Optional
import requests
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

@dataclass
class DatiReport:
    periodo_inizio: str
    periodo_fine: str
    uptime: dict = field(default_factory=dict)
    incidenti: dict = field(default_factory=dict)
    patch: dict = field(default_factory=dict)
    backup: dict = field(default_factory=dict)
    capacita: dict = field(default_factory=dict)
    sicurezza: dict = field(default_factory=dict)
    manutenzioni: list = field(default_factory=list)

class CollettoreDati:
    """Raccoglie dati da fonti multiple per il report settimanale."""

    def __init__(self, config):
        self.config = config

    def raccogli_uptime(self) -> dict:
        """Raccoglie dati di uptime da Prometheus/Grafana."""
        url = f"{self.config['prometheus_url']}/api/v1/query_range"
        fine = datetime.utcnow()
        inizio = fine - timedelta(days=7)

        risultati = {}
        for servizio in self.config["servizi_monitorati"]:
            params = {
                "query": f'avg_over_time(up{{job="{servizio}"}}[7d]) * 100',
                "start": inizio.isoformat() + "Z",
                "end": fine.isoformat() + "Z",
                "step": "1h"
            }
            try:
                response = requests.get(url, params=params, timeout=30)
                data = response.json()
                if data["data"]["result"]:
                    valori = [float(v[1]) for v in data["data"]["result"][0]["values"]]
                    risultati[servizio] = {
                        "uptime_percent": round(sum(valori) / len(valori), 2),
                        "downtime_minuti": round((1 - sum(valori) / len(valori) / 100) * 7 * 24 * 60, 1)
                    }
            except Exception as e:
                risultati[servizio] = {"errore": str(e)}

        return risultati

    def raccogli_incidenti(self) -> dict:
        """Raccoglie dati incidenti da Jira Service Management."""
        url = f"{self.config['jira_url']}/rest/api/3/search"
        auth = (self.config["jira_user"], self.config["jira_token"])
        fine = datetime.utcnow()
        inizio = fine - timedelta(days=7)

        jql = (
            f'project = "IT-OPS" AND type = Incident '
            f'AND created >= "{inizio.strftime("%Y-%m-%d")}"'
        )
        response = requests.get(
            url, auth=auth,
            params={"jql": jql, "maxResults": 500, "fields": "status,priority,resolutiondate,created"},
            timeout=30
        )
        issues = response.json().get("issues", [])

        aperti = sum(1 for i in issues if i["fields"]["status"]["name"] not in ["Done", "Closed"])
        chiusi = sum(1 for i in issues if i["fields"]["status"]["name"] in ["Done", "Closed"])

        # Calcolo MTTR (Mean Time To Resolve)
        tempi_risoluzione = []
        for issue in issues:
            if issue["fields"].get("resolutiondate"):
                creato = datetime.fromisoformat(issue["fields"]["created"].replace("Z", "+00:00"))
                risolto = datetime.fromisoformat(issue["fields"]["resolutiondate"].replace("Z", "+00:00"))
                tempi_risoluzione.append((risolto - creato).total_seconds() / 3600)

        mttr = round(sum(tempi_risoluzione) / len(tempi_risoluzione), 1) if tempi_risoluzione else 0

        return {
            "totale": len(issues),
            "aperti": aperti,
            "chiusi": chiusi,
            "in_attesa": len(issues) - aperti - chiusi,
            "mttr_ore": mttr,
            "per_priorita": {
                "critica": sum(1 for i in issues if i["fields"]["priority"]["name"] == "Critical"),
                "alta": sum(1 for i in issues if i["fields"]["priority"]["name"] == "High"),
                "media": sum(1 for i in issues if i["fields"]["priority"]["name"] == "Medium"),
                "bassa": sum(1 for i in issues if i["fields"]["priority"]["name"] == "Low")
            }
        }

    def raccogli_backup(self) -> dict:
        """Raccoglie statistiche backup dalla settimana."""
        log_dir = self.config.get("backup_log_dir", "/var/log/backup-verification")
        risultati = {"totale": 0, "successi": 0, "fallimenti": 0, "dettaglio": []}

        for filename in os.listdir(log_dir):
            if filename.endswith(".json"):
                with open(os.path.join(log_dir, filename)) as f:
                    data = json.load(f)
                    risultati["totale"] += 1
                    if data.get("restore_riuscito") and data.get("integrita_ok"):
                        risultati["successi"] += 1
                    else:
                        risultati["fallimenti"] += 1
                    risultati["dettaglio"].append(data)

        risultati["tasso_successo"] = (
            round(risultati["successi"] / risultati["totale"] * 100, 1)
            if risultati["totale"] > 0 else 0
        )
        return risultati


class GeneratoreReport:
    """Genera il report HTML/PDF e lo distribuisce via email."""

    def __init__(self, config):
        self.config = config
        self.env = Environment(loader=FileSystemLoader("templates"))

    def genera_html(self, dati: DatiReport) -> str:
        template = self.env.get_template("report_settimanale.html.j2")
        return template.render(
            dati=dati,
            generato_il=datetime.now().strftime("%d/%m/%Y %H:%M")
        )

    def genera_pdf(self, html_content: str, output_path: str):
        HTML(string=html_content).write_pdf(output_path)
        return output_path

    def invia_email(self, html_content: str, pdf_path: str, destinatari: list):
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Report Settimanale IT - {datetime.now().strftime('%d/%m/%Y')}"
        msg["From"] = self.config["email_from"]
        msg["To"] = ", ".join(destinatari)

        msg.attach(MIMEText(html_content, "html"))

        with open(pdf_path, "rb") as f:
            pdf_attachment = MIMEApplication(f.read(), _subtype="pdf")
            pdf_attachment.add_header(
                "Content-Disposition", "attachment",
                filename=f"report_settimanale_{datetime.now().strftime('%Y%m%d')}.pdf"
            )
            msg.attach(pdf_attachment)

        with smtplib.SMTP(self.config["smtp_host"], self.config["smtp_port"]) as server:
            server.starttls()
            server.login(self.config["smtp_user"], self.config["smtp_password"])
            server.send_message(msg)

        logger.info(f"Report inviato a {len(destinatari)} destinatari")
```

Il template Jinja2 per il report (`templates/report_settimanale.html.j2`) definisce la struttura HTML con stili CSS inline per garantire compatibilita con i principali client email, includendo tabelle riepilogative per ogni sezione, indicatori colorati per stati critici e grafici a barre semplici realizzati in CSS puro.

---

## Progetto 6: Automazione Gestione Ticket

### Obiettivo

Implementare un sistema intelligente di gestione dei ticket che automatizzi la categorizzazione, l'assegnazione della priorita, il routing al team appropriato, il monitoraggio degli SLA e l'invio di risposte automatiche per le problematiche piu comuni. L'obiettivo e ridurre il carico manuale di triage del 70-80% e garantire che nessun ticket critico venga trascurato.

### Funzionalita

- **Auto-categorizzazione**: Analisi del titolo e della descrizione del ticket per assegnare categoria e sottocategoria tramite keyword matching e regole.
- **Assegnazione priorita**: Regole basate su impatto (numero utenti coinvolti), urgenza (presenza di workaround) e tipo di servizio.
- **Assegnazione automatica**: Routing al team o alla persona corretta in base a categoria, competenze e carico di lavoro.
- **Monitoraggio SLA**: Tracking continuo dei tempi di risposta e risoluzione con escalation automatica.
- **Risposte automatiche**: Per problematiche note (reset password, accesso VPN, richieste standard), invio automatico di istruzioni risolutive.
- **Notifiche di stato**: Aggiornamenti proattivi ai richiedenti sullo stato del ticket.

### Implementazione

#### Motore di regole Python

```python
# ticket_automation.py - Sistema intelligente di gestione ticket

import re
import json
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ticket_automation")

@dataclass
class Ticket:
    id: str
    titolo: str
    descrizione: str
    richiedente: str
    email_richiedente: str
    data_creazione: str
    categoria: Optional[str] = None
    sottocategoria: Optional[str] = None
    priorita: Optional[str] = None
    assegnato_a: Optional[str] = None
    team: Optional[str] = None
    sla_scadenza: Optional[str] = None
    stato: str = "nuovo"

class MotoreRegole:
    """Motore di regole per categorizzazione e prioritizzazione ticket."""

    def __init__(self, config_path="config/ticket_rules.json"):
        with open(config_path) as f:
            self.config = json.load(f)

    def categorizza(self, ticket: Ticket) -> tuple:
        """Determina categoria e sottocategoria del ticket."""
        testo = f"{ticket.titolo} {ticket.descrizione}".lower()
        regole = self.config["regole_categorizzazione"]

        for regola in regole:
            pattern = regola["pattern"]
            if re.search(pattern, testo):
                return regola["categoria"], regola["sottocategoria"]

        return "Generale", "Non classificato"

    def assegna_priorita(self, ticket: Ticket) -> str:
        """Calcola la priorita in base a regole di impatto e urgenza."""
        testo = f"{ticket.titolo} {ticket.descrizione}".lower()
        punteggio = 0

        # Parole chiave di urgenza
        parole_critiche = ["down", "non funziona", "bloccato", "impossibile lavorare",
                           "tutti gli utenti", "produzione", "emergenza", "urgente"]
        parole_alte = ["errore", "lento", "problema", "malfunzionamento",
                       "diversi utenti", "importante"]
        parole_basse = ["richiesta", "informazione", "domanda", "quando possibile",
                        "miglioramento", "suggerimento"]

        for parola in parole_critiche:
            if parola in testo:
                punteggio += 3
        for parola in parole_alte:
            if parola in testo:
                punteggio += 2
        for parola in parole_basse:
            if parola in testo:
                punteggio -= 1

        # Regole VIP
        if ticket.email_richiedente in self.config.get("utenti_vip", []):
            punteggio += 2

        # Regole orario (fuori orario lavorativo = potenziale urgenza)
        ora_creazione = datetime.fromisoformat(ticket.data_creazione).hour
        if ora_creazione < 7 or ora_creazione > 20:
            punteggio += 1

        if punteggio >= 6:
            return "critica"
        elif punteggio >= 4:
            return "alta"
        elif punteggio >= 2:
            return "media"
        else:
            return "bassa"

    def assegna_team(self, ticket: Ticket) -> tuple:
        """Determina il team e la persona responsabile."""
        mappatura = self.config.get("mappatura_team", {})
        chiave = f"{ticket.categoria}:{ticket.sottocategoria}"

        if chiave in mappatura:
            team_info = mappatura[chiave]
            # Selezione persona con carico minore
            membro = self._seleziona_membro_disponibile(team_info["team"])
            return team_info["team"], membro

        # Fallback
        return "IT-Generale", None

    def _seleziona_membro_disponibile(self, team):
        """Seleziona il membro del team con minor carico di ticket aperti."""
        membri = self.config.get("membri_team", {}).get(team, [])
        if not membri:
            return None

        carichi = {}
        for membro in membri:
            # Query al sistema di ticketing per contare ticket aperti
            carichi[membro] = self._conta_ticket_aperti(membro)

        return min(carichi, key=carichi.get)

    def _conta_ticket_aperti(self, assegnatario):
        """Conta i ticket aperti assegnati a una persona."""
        # Implementazione specifica per il sistema di ticketing
        return 0

    def calcola_sla(self, ticket: Ticket) -> str:
        """Calcola la scadenza SLA in base alla priorita."""
        sla_ore = self.config.get("sla_ore", {})
        ore = sla_ore.get(ticket.priorita, 48)
        scadenza = datetime.fromisoformat(ticket.data_creazione) + timedelta(hours=ore)
        return scadenza.isoformat()

    def verifica_risposta_automatica(self, ticket: Ticket) -> Optional[str]:
        """Verifica se il ticket corrisponde a una problematica nota."""
        testo = f"{ticket.titolo} {ticket.descrizione}".lower()
        risposte = self.config.get("risposte_automatiche", [])

        for risposta in risposte:
            if re.search(risposta["pattern"], testo):
                return risposta["template"]

        return None


class SLAMonitor:
    """Monitora gli SLA e gestisce le escalation."""

    def __init__(self, config):
        self.config = config

    def controlla_sla(self, tickets: list):
        """Controlla tutti i ticket aperti per violazioni SLA."""
        ora = datetime.utcnow()
        violazioni = []
        in_scadenza = []

        for ticket in tickets:
            if not ticket.sla_scadenza or ticket.stato in ["chiuso", "risolto"]:
                continue

            scadenza = datetime.fromisoformat(ticket.sla_scadenza)
            delta = scadenza - ora

            if delta.total_seconds() < 0:
                violazioni.append(ticket)
                self._escalation(ticket, "violazione")
            elif delta.total_seconds() < 3600:
                in_scadenza.append(ticket)
                self._escalation(ticket, "in_scadenza")

        return {"violazioni": violazioni, "in_scadenza": in_scadenza}

    def _escalation(self, ticket, tipo):
        """Esegue l'escalation per un ticket."""
        if tipo == "violazione":
            # Notifica al manager del team
            logger.warning(f"SLA VIOLATO per ticket {ticket.id}")
            self._notifica_slack(
                f"SLA VIOLATO | Ticket {ticket.id}: {ticket.titolo} | "
                f"Assegnato a: {ticket.assegnato_a}",
                canale="#sla-violations"
            )
        elif tipo == "in_scadenza":
            # Notifica all'assegnatario
            logger.info(f"SLA in scadenza per ticket {ticket.id}")
            self._notifica_slack(
                f"SLA in scadenza (< 1 ora) | Ticket {ticket.id}: {ticket.titolo}",
                canale="#alerts-warning"
            )

    def _notifica_slack(self, messaggio, canale):
        requests.post(
            self.config["slack_webhook"],
            json={"channel": canale, "text": messaggio},
            timeout=10
        )
```

Il file di configurazione `config/ticket_rules.json` contiene le regole di categorizzazione, le mappature team, le definizioni SLA e i template delle risposte automatiche, permettendo al team di modificare il comportamento del sistema senza intervenire sul codice.

---

## Progetto 7: Dismissione Utente Automatica

### Obiettivo

Automatizzare l'intero processo di offboarding di un dipendente, garantendo che tutti gli accessi vengano revocati in modo tempestivo e completo, le risorse vengano trasferite e archiviate, e venga generata documentazione di audit conforme alle policy aziendali. L'offboarding e speculare all'onboarding ma con complessita aggiuntive legate alla sicurezza e alla conservazione dei dati.

### Workflow

1. **Trigger HR**: HR avvia l'offboarding tramite form o ticket con la data di ultimo giorno lavorativo.
2. **Disabilitazione account AD**: L'account viene disabilitato (non eliminato) immediatamente alla data di cessazione.
3. **Rimozione da tutti i gruppi**: L'utente viene rimosso da ogni gruppo di sicurezza e distribuzione.
4. **Revoca licenza Microsoft 365**: Le licenze vengono rimosse per liberare slot.
5. **Inoltro email**: La casella viene configurata per inoltrare la posta al manager per 30 giorni.
6. **Archiviazione casella**: La casella viene convertita in shared mailbox e archiviata.
7. **Disabilitazione accesso applicazioni**: Account disabilitati in tutte le applicazioni aziendali tramite API.
8. **Trasferimento proprieta file**: I file OneDrive/SharePoint vengono trasferiti al manager.
9. **Disabilitazione accesso VPN**: Rimozione configurazione VPN.
10. **Generazione report di audit**: Report dettagliato di tutte le azioni eseguite.
11. **Schedulazione eliminazione permanente**: L'account viene schedulato per l'eliminazione definitiva dopo 90 giorni.

### Implementazione

```python
# offboarding.py - Dismissione automatica dipendente

import subprocess
import json
import logging
import requests
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("offboarding")

@dataclass
class RichiestaOffboarding:
    username: str
    nome_completo: str
    manager: str
    manager_email: str
    ultimo_giorno: str
    dipartimento: str
    motivo: str = "Cessazione rapporto"

class OffboardingAutomatico:
    def __init__(self, config_path="config/offboarding.json"):
        with open(config_path) as f:
            self.config = json.load(f)
        self.azioni_completate = []
        self.errori = []

    def _registra(self, fase, stato, dettagli=None):
        entry = {
            "fase": fase,
            "stato": stato,
            "dettagli": dettagli,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.azioni_completate.append(entry)
        if stato == "errore":
            self.errori.append(entry)

    def disabilita_account_ad(self, username):
        """Fase 1: Disabilita l'account AD e sposta nella OU di dismissione."""
        logger.info(f"Disabilitazione account AD: {username}")
        try:
            script = f"""
            $user = Get-ADUser -Identity '{username}' -Properties MemberOf
            Disable-ADAccount -Identity '{username}'
            Set-ADUser -Identity '{username}' -Description 'Dismissione: {datetime.now().strftime("%Y-%m-%d")}'
            Move-ADObject -Identity $user.DistinguishedName `
                -TargetPath 'OU=Dismissioni,OU=Dipendenti,DC=azienda,DC=local'
            """
            result = subprocess.run(
                ["powershell", "-Command", script],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                self._registra("disabilita_ad", "completato")
            else:
                raise Exception(result.stderr)
        except Exception as e:
            self._registra("disabilita_ad", "errore", str(e))
            logger.error(f"Errore disabilitazione AD: {e}")

    def rimuovi_tutti_gruppi(self, username):
        """Fase 2: Rimuove l'utente da tutti i gruppi AD."""
        logger.info(f"Rimozione gruppi per: {username}")
        try:
            script = f"""
            $user = Get-ADUser -Identity '{username}' -Properties MemberOf
            $gruppi = $user.MemberOf
            $rimossi = @()
            foreach ($gruppo in $gruppi) {{
                try {{
                    Remove-ADGroupMember -Identity $gruppo -Members '{username}' -Confirm:$false
                    $rimossi += (Get-ADGroup -Identity $gruppo).Name
                }} catch {{
                    Write-Warning "Non rimosso da $gruppo : $_"
                }}
            }}
            $rimossi | ConvertTo-Json
            """
            result = subprocess.run(
                ["powershell", "-Command", script],
                capture_output=True, text=True
            )
            gruppi_rimossi = json.loads(result.stdout) if result.stdout.strip() else []
            self._registra("rimuovi_gruppi", "completato", {"gruppi": gruppi_rimossi})
        except Exception as e:
            self._registra("rimuovi_gruppi", "errore", str(e))

    def configura_inoltro_email(self, username, manager_email, giorni=30):
        """Fase 3: Configura inoltro email al manager."""
        logger.info(f"Configurazione inoltro email per {username} -> {manager_email}")
        try:
            graph = GraphAPIClient(
                self.config["tenant_id"],
                self.config["client_id"],
                self.config["client_secret"]
            )
            upn = f"{username}@azienda.com"
            url = f"{graph.base_url}/users/{upn}/mailboxSettings"
            payload = {
                "automaticRepliesSetting": {
                    "status": "scheduled",
                    "scheduledStartDateTime": {
                        "dateTime": datetime.utcnow().isoformat(),
                        "timeZone": "UTC"
                    },
                    "scheduledEndDateTime": {
                        "dateTime": (datetime.utcnow() + timedelta(days=giorni)).isoformat(),
                        "timeZone": "UTC"
                    },
                    "internalReplyMessage": (
                        f"Questo utente non e piu in azienda. "
                        f"Per urgenze contattare {manager_email}."
                    ),
                    "externalReplyMessage": (
                        f"Questo utente non e piu disponibile. "
                        f"Per urgenze contattare {manager_email}."
                    )
                }
            }
            response = requests.patch(url, headers=graph._headers(), json=payload)
            response.raise_for_status()

            # Configura regola di inoltro
            rules_url = f"{graph.base_url}/users/{upn}/mailFolders/inbox/messageRules"
            forward_rule = {
                "displayName": "Forward to Manager",
                "sequence": 1,
                "isEnabled": True,
                "conditions": {},
                "actions": {
                    "forwardTo": [
                        {"emailAddress": {"address": manager_email}}
                    ],
                    "stopProcessingRules": True
                }
            }
            requests.post(rules_url, headers=graph._headers(), json=forward_rule)

            self._registra("inoltro_email", "completato",
                          {"destinatario": manager_email, "durata_giorni": giorni})
        except Exception as e:
            self._registra("inoltro_email", "errore", str(e))

    def revoca_licenze_m365(self, username):
        """Fase 4: Revoca tutte le licenze Microsoft 365."""
        logger.info(f"Revoca licenze M365 per {username}")
        try:
            graph = GraphAPIClient(
                self.config["tenant_id"],
                self.config["client_id"],
                self.config["client_secret"]
            )
            upn = f"{username}@azienda.com"
            url = f"{graph.base_url}/users/{upn}"
            response = requests.get(url, headers=graph._headers(),
                                   params={"$select": "assignedLicenses"})
            licenze = response.json().get("assignedLicenses", [])
            sku_ids = [lic["skuId"] for lic in licenze]

            if sku_ids:
                remove_url = f"{graph.base_url}/users/{upn}/assignLicense"
                payload = {
                    "addLicenses": [],
                    "removeLicenses": sku_ids
                }
                requests.post(remove_url, headers=graph._headers(), json=payload)

            self._registra("revoca_licenze", "completato", {"licenze_revocate": len(sku_ids)})
        except Exception as e:
            self._registra("revoca_licenze", "errore", str(e))

    def disabilita_applicazioni(self, username):
        """Fase 5: Disabilita accesso a tutte le applicazioni aziendali."""
        logger.info(f"Disabilitazione applicazioni per {username}")
        email = f"{username}@azienda.com"
        app_disabilitate = []

        # Slack
        try:
            response = requests.post(
                "https://slack.com/api/admin.users.remove",
                headers={"Authorization": f"Bearer {self.config['slack_token']}"},
                json={"user_id": self._get_slack_user_id(email)}
            )
            app_disabilitate.append("slack")
        except Exception as e:
            logger.warning(f"Errore disabilitazione Slack: {e}")

        # Jira/Confluence
        try:
            response = requests.delete(
                f"{self.config['jira_url']}/rest/api/3/user?accountId="
                f"{self._get_jira_account_id(email)}",
                auth=(self.config["jira_user"], self.config["jira_token"])
            )
            app_disabilitate.append("jira")
        except Exception as e:
            logger.warning(f"Errore disabilitazione Jira: {e}")

        self._registra("disabilita_app", "completato", {"app": app_disabilitate})

    def trasferisci_file(self, username, manager):
        """Fase 6: Trasferisce i file OneDrive al manager."""
        logger.info(f"Trasferimento file da {username} a {manager}")
        try:
            # Utilizzo di Graph API per trasferimento ownership OneDrive
            # In produzione, si utilizza tipicamente lo strumento di migrazione SharePoint
            self._registra("trasferimento_file", "completato",
                          {"da": username, "a": manager})
        except Exception as e:
            self._registra("trasferimento_file", "errore", str(e))

    def genera_report_audit(self, richiesta: RichiestaOffboarding) -> dict:
        """Genera il report di audit completo dell'offboarding."""
        report = {
            "tipo": "offboarding_audit",
            "dipendente": asdict(richiesta),
            "data_esecuzione": datetime.utcnow().isoformat(),
            "azioni": self.azioni_completate,
            "errori": self.errori,
            "stato_generale": "completato" if not self.errori else "completato_con_errori"
        }

        # Salva report
        report_path = (
            f"reports/offboarding_{richiesta.username}_"
            f"{datetime.now().strftime('%Y%m%d')}.json"
        )
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2, default=str)

        return report

    def esegui_offboarding(self, richiesta: RichiestaOffboarding):
        """Esegue l'intero processo di offboarding."""
        logger.info(f"Avvio offboarding per {richiesta.username}")

        self.disabilita_account_ad(richiesta.username)
        self.rimuovi_tutti_gruppi(richiesta.username)
        self.configura_inoltro_email(richiesta.username, richiesta.manager_email)
        self.revoca_licenze_m365(richiesta.username)
        self.disabilita_applicazioni(richiesta.username)
        self.trasferisci_file(richiesta.username, richiesta.manager)

        report = self.genera_report_audit(richiesta)

        # Notifica completamento
        self._notifica_completamento(richiesta, report)

        # Schedula eliminazione permanente a 90 giorni
        self._schedula_eliminazione(richiesta.username, giorni=90)

        return report

    def _notifica_completamento(self, richiesta, report):
        stato = report["stato_generale"]
        requests.post(
            self.config["slack_webhook"],
            json={
                "channel": "#hr-operations",
                "text": (
                    f"Offboarding {'completato' if stato == 'completato' else 'completato con errori'} "
                    f"per {richiesta.nome_completo} ({richiesta.username}). "
                    f"Azioni eseguite: {len(self.azioni_completate)}, "
                    f"Errori: {len(self.errori)}"
                )
            }
        )

    def _schedula_eliminazione(self, username, giorni):
        """Crea un task schedulato per l'eliminazione permanente."""
        data_eliminazione = datetime.now() + timedelta(days=giorni)
        logger.info(
            f"Eliminazione permanente di {username} schedulata per "
            f"{data_eliminazione.strftime('%Y-%m-%d')}"
        )
        # In produzione: creare un record nel database di schedulazione
        # o un ticket con data di scadenza
```

---

## Progetto 8: CI/CD per Automazioni

### Obiettivo

Implementare una pipeline CI/CD dedicata al codice di automazione stesso. Le automazioni IT sono software a tutti gli effetti e meritano le stesse pratiche di qualita del codice applicativo: version control, testing automatizzato, code review, deployment controllato. Questo progetto applica i principi DevOps agli script e ai workflow di automazione.

### Componenti

- **Repository Git strutturato**: Organizzazione chiara di script, configurazioni, test e documentazione.
- **Pre-commit hooks**: Linting e formattazione automatica prima di ogni commit.
- **Pipeline CI con GitHub Actions**: Test automatizzati, analisi statica, scansione di sicurezza.
- **Deployment a staging**: Distribuzione automatica all'ambiente di test.
- **Gate di approvazione**: Approvazione manuale richiesta prima del deploy in produzione.
- **Deployment a produzione**: Distribuzione controllata con verifica post-deploy.
- **Procedura di rollback**: Meccanismo per ripristinare la versione precedente in caso di problemi.

### Implementazione

#### Struttura del repository

```
automazioni-it/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml
│   │   ├── deploy-staging.yml
│   │   └── deploy-production.yml
│   └── CODEOWNERS
├── scripts/
│   ├── onboarding/
│   │   ├── onboarding_completo.py
│   │   ├── onboarding-ad.ps1
│   │   └── config/
│   ├── offboarding/
│   │   ├── offboarding.py
│   │   └── config/
│   ├── monitoring/
│   │   ├── infra_monitor.py
│   │   └── config/
│   └── patching/
│       ├── patch-management.ps1
│       └── playbooks/
├── workflows/
│   ├── n8n/
│   │   ├── onboarding-workflow.json
│   │   └── monitoring-workflow.json
│   └── make/
├── tests/
│   ├── test_onboarding.py
│   ├── test_offboarding.py
│   ├── test_monitoring.py
│   └── conftest.py
├── templates/
│   └── report_settimanale.html.j2
├── .pre-commit-config.yaml
├── pyproject.toml
├── requirements.txt
└── requirements-dev.txt
```

#### Configurazione pre-commit

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-added-large-files
        args: ['--maxkb=500']
      - id: detect-private-key
      - id: check-merge-conflict

  - repo: https://github.com/psf/black
    rev: 24.3.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
        args: ['--max-line-length=120', '--ignore=E203,W503']

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
        args: ['--profile=black']

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.9.0
    hooks:
      - id: mypy
        additional_dependencies: ['types-requests']
        args: ['--ignore-missing-imports']
```

#### Pipeline CI con GitHub Actions

```yaml
# .github/workflows/ci.yml
name: CI Pipeline Automazioni IT

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  lint:
    name: Linting e Formattazione
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Installa dipendenze
        run: |
          pip install -r requirements-dev.txt

      - name: Esegui Black (formattazione)
        run: black --check scripts/ tests/

      - name: Esegui Flake8 (linting)
        run: flake8 scripts/ tests/ --max-line-length=120

      - name: Esegui isort (ordinamento import)
        run: isort --check-only scripts/ tests/

      - name: Esegui mypy (type checking)
        run: mypy scripts/ --ignore-missing-imports

  test:
    name: Test Automatizzati
    runs-on: ubuntu-latest
    needs: lint
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_db
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Installa dipendenze
        run: pip install -r requirements.txt -r requirements-dev.txt

      - name: Esegui test con copertura
        run: |
          pytest tests/ -v --cov=scripts --cov-report=xml --cov-report=html
        env:
          TEST_DB_HOST: localhost
          TEST_DB_PORT: 5432
          TEST_DB_USER: test
          TEST_DB_PASS: test

      - name: Verifica copertura minima
        run: |
          coverage report --fail-under=80

      - name: Upload report copertura
        uses: actions/upload-artifact@v4
        with:
          name: coverage-report
          path: htmlcov/

  security:
    name: Scansione Sicurezza
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Installa Bandit
        run: pip install bandit[toml]

      - name: Scansione sicurezza codice
        run: bandit -r scripts/ -c pyproject.toml -f json -o bandit-report.json
        continue-on-error: true

      - name: Verifica dipendenze vulnerabili
        run: |
          pip install safety
          safety check -r requirements.txt --json --output safety-report.json
        continue-on-error: true

      - name: Scansione secrets
        uses: trufflesecurity/trufflehog@main
        with:
          extra_args: --only-verified

  deploy-staging:
    name: Deploy Staging
    runs-on: ubuntu-latest
    needs: [test, security]
    if: github.ref == 'refs/heads/develop'
    environment: staging
    steps:
      - uses: actions/checkout@v4

      - name: Deploy a server staging
        run: |
          rsync -avz --delete \
            --exclude='.git' \
            --exclude='tests/' \
            --exclude='*.md' \
            scripts/ ${{ secrets.STAGING_USER }}@${{ secrets.STAGING_HOST }}:/opt/automazioni/

      - name: Verifica deploy
        run: |
          ssh ${{ secrets.STAGING_USER }}@${{ secrets.STAGING_HOST }} \
            "cd /opt/automazioni && python -c 'import onboarding.onboarding_completo; print(\"OK\")'"

  deploy-production:
    name: Deploy Produzione
    runs-on: ubuntu-latest
    needs: [test, security]
    if: github.ref == 'refs/heads/main'
    environment:
      name: production
      url: https://automazioni.azienda.com
    steps:
      - uses: actions/checkout@v4

      - name: Backup versione corrente
        run: |
          ssh ${{ secrets.PROD_USER }}@${{ secrets.PROD_HOST }} \
            "cp -r /opt/automazioni /opt/automazioni.backup.$(date +%Y%m%d%H%M%S)"

      - name: Deploy a produzione
        run: |
          rsync -avz --delete \
            --exclude='.git' \
            --exclude='tests/' \
            --exclude='*.md' \
            scripts/ ${{ secrets.PROD_USER }}@${{ secrets.PROD_HOST }}:/opt/automazioni/

      - name: Verifica post-deploy
        run: |
          ssh ${{ secrets.PROD_USER }}@${{ secrets.PROD_HOST }} \
            "cd /opt/automazioni && python -m pytest tests/smoke/ -v"

      - name: Notifica Slack
        if: always()
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "Deploy produzione automazioni: ${{ job.status }}",
              "channel": "#deployments"
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

#### Framework di testing

```python
# tests/test_onboarding.py - Test per il modulo di onboarding

import pytest
from unittest.mock import patch, MagicMock
from scripts.onboarding.onboarding_completo import (
    OnboardingAutomatico,
    DipendenteDati,
    RisultatoOnboarding
)

@pytest.fixture
def config_test(tmp_path):
    import json
    config = {
        "gruppi_base": ["AllEmployees", "VPN-Users"],
        "gruppi_dipartimento": {
            "IT": ["IT-Staff", "ServerAccess"],
            "HR": ["HR-Staff"]
        },
        "gruppi_ruolo": {
            "Manager": ["Managers"],
            "Developer": ["Developers"]
        },
        "tenant_id": "test-tenant",
        "client_id": "test-client",
        "client_secret": "test-secret",
        "licenza_default": "sku-enterprise",
        "applicazioni_ruolo": {
            "Developer": ["slack", "jira"],
            "Manager": ["slack"]
        }
    }
    config_path = tmp_path / "onboarding.json"
    config_path.write_text(json.dumps(config))
    return str(config_path)

@pytest.fixture
def dipendente_test():
    return DipendenteDati(
        nome="Mario",
        cognome="Rossi",
        dipartimento="IT",
        ruolo="Developer",
        manager="Luigi Bianchi",
        data_inizio="2026-04-01",
        sede="Milano"
    )

class TestGenerazioneUsername:
    def test_username_standard(self, config_test):
        onb = OnboardingAutomatico(config_test)
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="", returncode=0)
            username = onb.genera_username("Mario", "Rossi")
            assert username == "mrossi"

    def test_username_con_caratteri_speciali(self, config_test):
        onb = OnboardingAutomatico(config_test)
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="", returncode=0)
            username = onb.genera_username("Jean-Pierre", "O'Brien")
            assert username == "jobrien"

class TestGenerazionePassword:
    def test_lunghezza_password(self, config_test):
        onb = OnboardingAutomatico(config_test)
        password = onb.genera_password(lunghezza=16)
        assert len(password) == 16

    def test_complessita_password(self, config_test):
        onb = OnboardingAutomatico(config_test)
        password = onb.genera_password()
        ha_maiuscola = any(c.isupper() for c in password)
        ha_minuscola = any(c.islower() for c in password)
        ha_numero = any(c.isdigit() for c in password)
        assert ha_maiuscola and ha_minuscola and ha_numero

class TestAssegnazioneGruppi:
    @patch("subprocess.run")
    def test_gruppi_base_assegnati(self, mock_run, config_test):
        mock_run.return_value = MagicMock(returncode=0)
        onb = OnboardingAutomatico(config_test)
        gruppi = onb.assegna_gruppi("mrossi", "IT", "Developer")
        assert "AllEmployees" in gruppi
        assert "VPN-Users" in gruppi

    @patch("subprocess.run")
    def test_gruppi_dipartimento(self, mock_run, config_test):
        mock_run.return_value = MagicMock(returncode=0)
        onb = OnboardingAutomatico(config_test)
        gruppi = onb.assegna_gruppi("mrossi", "IT", "Developer")
        assert "IT-Staff" in gruppi
        assert "ServerAccess" in gruppi
```

---

## Tabella Riepilogativa

| Progetto | Difficolta | Tempo Stimato | Tecnologie Principali | Obiettivi di Apprendimento |
|----------|-----------|---------------|----------------------|---------------------------|
| 1. Onboarding Automatico | Base | 2-3 settimane | PowerShell, Python, Graph API, n8n | Workflow orchestration, integrazione AD e M365, gestione errori e rollback |
| 2. Monitoraggio Infrastruttura | Base | 2-3 settimane | Python, Prometheus, Grafana, Slack API | Raccolta metriche, alert routing, deduplicazione notifiche |
| 3. Gestione Patch | Intermedio | 3-4 settimane | PowerShell, Ansible, n8n | Patch lifecycle, approval workflow, compliance reporting |
| 4. Backup Verification | Intermedio | 2-3 settimane | Python, PostgreSQL, SQL Server | Restore testing, integrita dati, scheduling |
| 5. Report Settimanale | Intermedio | 2-3 settimane | Python, Jinja2, WeasyPrint, API multiple | Aggregazione dati multi-sorgente, templating, distribuzione report |
| 6. Gestione Ticket | Avanzato | 3-4 settimane | Python, Jira API, Slack API, n8n | Rule engine, NLP base, SLA monitoring, escalation |
| 7. Dismissione Utente | Avanzato | 3-4 settimane | PowerShell, Python, Graph API, n8n | Offboarding completo, sicurezza, audit compliance |
| 8. CI/CD per Automazioni | Avanzato | 2-3 settimane | Git, GitHub Actions, pytest, Bandit | DevOps practices, testing, deployment pipeline, security scanning |

---

## Best Practices per Progetti

**1. Iniziare sempre con un Proof of Concept (PoC)**

Non tentare di costruire l'intera automazione in un'unica iterazione. Iniziare con un PoC che copra il percorso critico (happy path) e validarlo con gli stakeholder prima di investire tempo nelle gestione di tutti i casi limite. Un PoC funzionante in due giorni vale piu di una specifica perfetta in due settimane.

**2. Progettare per il fallimento, non solo per il successo**

Ogni fase del workflow deve prevedere cosa succede in caso di errore. Implementare gestione errori esplicita, meccanismi di retry con backoff esponenziale e procedure di rollback. I log devono contenere informazioni sufficienti per diagnosticare il problema senza accesso al sistema in tempo reale. Un'automazione senza error handling e una bomba a orologeria.

**3. Mantenere la configurazione separata dal codice**

Utilizzare file di configurazione esterni (JSON, YAML) per tutti i parametri che possono variare tra ambienti (staging/produzione) o nel tempo (soglie, liste di server, mappature gruppi). Questo permette di modificare il comportamento dell'automazione senza toccare il codice e semplifica la gestione multi-ambiente.

**4. Implementare logging strutturato fin dal primo giorno**

Non rimandare il logging a una fase successiva. Utilizzare logging strutturato (JSON) con livelli appropriati (DEBUG, INFO, WARNING, ERROR, CRITICAL). Includere sempre il contesto: chi ha avviato l'operazione, su quale risorsa, in quale fase del workflow. I log sono l'unico strumento disponibile quando qualcosa va storto alle tre di notte.

**5. Testare in un ambiente isolato prima di ogni deploy**

Mantenere un ambiente di staging che replichi la struttura (se non la scala) della produzione. Ogni modifica deve essere testata in staging prima del deploy. I test automatizzati devono coprire non solo il codice Python, ma anche le interazioni con i servizi esterni tramite mock e, quando possibile, tramite test di integrazione contro ambienti sandbox.

**6. Documentare il workflow, non solo il codice**

La documentazione del codice (docstring, commenti) e necessaria ma non sufficiente. Documentare il workflow complessivo: trigger, fasi, dipendenze, decisioni, output attesi. Un diagramma di flusso aggiornato vale piu di mille righe di commenti. Utilizzare strumenti come Mermaid per mantenere i diagrammi versionati insieme al codice.

**7. Implementare il principio del minimo privilegio**

Le credenziali utilizzate dalle automazioni devono avere solo i permessi strettamente necessari. Creare service account dedicati per ogni automazione, non riutilizzare credenziali personali. Utilizzare secret manager (Azure Key Vault, HashiCorp Vault) per la gestione delle credenziali, mai hard-coded nei file di configurazione.

**8. Pianificare la manutenzione evolutiva**

Le automazioni non sono statiche. Le API cambiano, i requisiti evolvono, nuove applicazioni vengono introdotte. Progettare il codice per essere facilmente estensibile: utilizzare pattern come Strategy o Plugin per aggiungere nuove integrazioni senza modificare il codice esistente. Schedulare revisioni periodiche (trimestrali) di tutte le automazioni in produzione per verificare che funzionino ancora correttamente e che siano allineate ai requisiti attuali.

---

## Esercizi

1. **Capstone-prep — onboarding cliente PMI.** Implementa workflow descritto in `00-CAPSTONE.md` (form → CRM → fattura SDI → notifica) con n8n self-hosted o Python. Vai in profondita.
2. **Project — sync rubrica clienti CRM ↔ G-Suite contacts.** Bidirectional sync, conflict resolution, dry-run mode.
3. **Stretch — incident response automation.** PagerDuty webhook → enrich con context (Datadog, Sentry) → Slack alert → auto-ack → escalation se non risolto in 30min.

## Auto-valutazione

1. Cosa rendere "consegnabile" un progetto?
2. Decisione architetturale: cosa documentare?
3. Bidirectional sync: pattern conflict resolution.
4. Incident automation: criteri auto-ack vs escalate.

## Letture primarie consigliate

- Documentation dei vendor cloud (Google Workspace, M365, Slack, Stripe) consultate al 2026-04-27.

## Collegamenti incrociati

- `00-CAPSTONE.md`: progetto finale formalizzato.
- Tutti i moduli precedenti (01-07).

## Glossario locale

| Termine | Definizione |
|---|---|
| **End-to-end workflow** | Workflow completo dall'input al delivery. |
| **Strategy pattern** | Design pattern per scambiare implementazioni. |
| **Plugin pattern** | Estensibilita via discovery dinamica. |
| **Conflict resolution** | Strategia per merge di modifiche concorrenti. |
