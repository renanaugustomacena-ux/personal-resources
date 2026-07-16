# Tutorial: Change Management e Release Management — Gestire le Modifiche in Produzione

> **Documento di riferimento:** `09-procedure-operative.md` (sezioni Change Enablement, Release Management, Service Request Fulfillment, Access Review, Decommissioning)
> **Dominio:** Procedure Operative (Dominio 09 — Parte B)
> **Ambito:** Processo end-to-end per la gestione di change, rilasci applicativi, richieste di servizio e ricertificazione accessi
> **Durata lab:** 8-10 ore (suddivise in 3 sessioni)
> **Livello:** Da principiante (Parte A) a operativo avanzato (Parte C)
> **Prerequisiti:** `tutorial_ops09_ch1a_sop_runbook_creation_lab.md`, `tutorial_ops08_ch1b_cmdb_implementation_lab.md`, `tutorial_ops07_ch1b_incident_management_lab.md`
> **Ambiente:** Solo lab isolato — simulare i processi, non eseguire change su sistemi reali

---

## Analogia Iniziale: Il Semaforo della Chirurgia

Immagina un ospedale senza protocollo chirurgico. Un medico decide di operare un paziente in qualsiasi momento, con qualsiasi strumento, senza preavviso. La probabilità di errore è alta, il coordinamento tra i team è zero, e se qualcosa va storto non c'è un piano di rientro.

Il **Change Management** è il protocollo chirurgico dell'IT: ogni intervento sull'infrastruttura viene pianificato, comunicato, approvato, eseguito con backup disponibile, e poi verificato. La velocità è importante, ma non più dell'affidabilità del servizio.

Il **Release Management** è l'intero ciclo dalla preparazione dell'intervento (sala operatoria, strumenti sterili) al follow-up post-operatorio: quando qualcosa entra in produzione, è stato testato, approvato da chi di dovere, e si sa come tornare indietro.

---

## Lab Environment Setup

### Requisiti

| Componente | Minimo | Raccomandato |
|---|---|---|
| VM Windows Server 2022 (DC-LAB-01) | 2 vCPU / 4 GB RAM | 4 vCPU / 8 GB RAM |
| VM Ubuntu 22.04 (SRV-LINUX-01) | 2 vCPU / 4 GB RAM | 4 vCPU / 8 GB RAM |
| VM Windows 10 (WKS-LAB-01) | 2 vCPU / 4 GB RAM | 4 vCPU / 8 GB RAM |

### Topologia di Rete

```
┌─────────────────────────────────────────────────────────────┐
│                  Rete Lab: 192.168.56.0/24                  │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │  DC-LAB-01   │    │ SRV-LINUX-01 │    │  WKS-LAB-01  │   │
│  │192.168.56.10 │    │192.168.56.20 │    │192.168.56.30 │   │
│  │              │    │              │    │              │   │
│  │  AD DS / DNS │    │ GLPI 10+     │    │ Client       │   │
│  │  File Server │    │ Gitea        │    │ Workstation  │   │
│  │  CA          │    │ Prometheus   │    │              │   │
│  └──────────────┘    └──────────────┘    └──────────────┘   │
│                                                             │
│  GLPI (ITSM):     http://192.168.56.20:8080/glpi           │
│  Gitea (repo):    http://192.168.56.20:3000                │
│  Prometheus:      http://192.168.56.20:9090                │
└─────────────────────────────────────────────────────────────┘
```

### Configurare GLPI per il Change Management

```bash
# Su SRV-LINUX-01 — verificare che GLPI sia in esecuzione
docker ps | grep glpi

# Se non attivo, avviarlo
docker start glpi-server glpi-mysql

# Accedere a GLPI
# URL: http://192.168.56.20:8080/glpi
# Admin: glpi / glpi

# Nel pannello GLPI — abilitare il modulo Change Management:
# Configurazione → Settori → ITIL → Change → Abilitato: Sì
```

---

## PART A: FONDAMENTI — Capire la Differenza tra Incidente, Change e Service Request

### Concetto A1: Le Tre Categorie di Lavoro IT

**Analogia**: In un hotel, ci sono tre tipi di situazioni:
- **Incidente**: il riscaldamento smette di funzionare in inverno → risposta immediata, ripristino
- **Change**: sostituire il vecchio impianto di riscaldamento → pianificato, approvato, comunicato
- **Service Request**: un ospite chiede asciugamani aggiuntivi → richiesta standard, pre-autorizzata

In IT:

| Categoria | Definizione | Risposta | Esempio |
|---|---|---|---|
| **Incidente** | Interruzione non pianificata o degradazione di servizio | Immediata, reattiva | Server giù, rete down, applicazione lenta |
| **Change** | Aggiunta, modifica o rimozione di componenti IT | Pianificata, approvata | Upgrade firmware, nuova configurazione, deploy |
| **Service Request** | Richiesta standard pre-approvata a basso rischio | Standard, SLA definito | Reset password, nuova workstation, accesso VPN |
| **Problem** | Causa radice di uno o più incidenti | Investigativa, non urgente | Trovare perché il server si riavvia periodicamente |

**Perché mi interessa?**
Confondere queste categorie è la fonte più comune di caos in IT. Un change non autorizzato ("ho solo cambiato un parametro") diventa un incidente il venerdì sera. Un incidente mal classificato come service request rimane in coda per settimane. La classificazione corretta indirizza il lavoro al processo giusto.

### Concetto A2: Change Enablement (ITIL 4) — Il Processo

ITIL 4 ha rinominato "Change Management" in "**Change Enablement**" per sottolineare che l'obiettivo non è bloccare i change, ma abilitarli in modo sicuro e veloce.

Le tre tipologie fondamentali:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    TIPOLOGIE DI CHANGE                              │
├──────────────┬────────────────┬─────────────────────────────────────┤
│   STANDARD   │     NORMAL     │           EMERGENCY                 │
├──────────────┼────────────────┼─────────────────────────────────────┤
│ Pre-approvato│ Richiede       │ Approvazione accelerata (ECAB)      │
│ Basso rischio│ valutazione    │ RFC retroattiva entro 24h           │
│ Nessun CAB   │ e approvazione │ Per vulnerabilità critiche, fix     │
│              │ formale        │ produzione urgenti                  │
├──────────────┼────────────────┼─────────────────────────────────────┤
│ Reset pwd    │ Upgrade server │ Patch zero-day                      │
│ Aggiungi     │ Migrazione DB  │ Hotfix produzione                   │
│ utente a     │ Cambio VLAN    │ Rollback di emergenza               │
│ gruppo       │ Deploy app     │                                     │
└──────────────┴────────────────┴─────────────────────────────────────┘
```

**Regola d'oro**: il processo di change esiste perché **il 60-80% degli incidenti di produzione è causato da change non gestiti correttamente** (fonte: dati Gartner/ITIL). Un change ben gestito ha backup, piano di rollback, finestra comunicata e verifiche post-implementazione.

### Concetto A3: La Matrice Rischio/Impatto

Ogni Normal Change viene classificato secondo questa matrice:

```
                    MATRICE RISCHIO / IMPATTO
                    ─────────────────────────────
                    Impatto   Impatto   Impatto
                     Basso     Medio     Alto
                   ┌─────────┬─────────┬─────────┐
Probabilità Alta   │  MEDIO  │  ALTO   │CRITICO  │
Probabilità Media  │  BASSO  │  MEDIO  │  ALTO   │
Probabilità Bassa  │  BASSO  │  BASSO  │  MEDIO  │
                   └─────────┴─────────┴─────────┘
```

La classificazione determina l'approvazione necessaria:

| Rischio | Approvatore |
|---|---|
| Basso | Change Manager |
| Medio | Change Manager + Technical Lead dell'area |
| Alto | Change Advisory Board (CAB) |
| Critico | CAB + IT Director + Business Owner |

**Il CAB** (Change Advisory Board) si riunisce tipicamente ogni settimana (martedì) per rivedere le RFC in coda. Non è un comitato burocratico — è una riunione tecnica di 30-60 minuti dove si valutano rischi, conflitti tra change, disponibilità di risorse.

### Concetto A4: Release Management e Semantic Versioning

Il **Release Management** coordina l'intero ciclo di vita di un rilascio applicativo: dalla pianificazione al deployment in produzione.

**Semantic Versioning (SemVer)**: ogni release ha un numero nel formato `MAJOR.MINOR.PATCH`:

```
Esempio: v3.2.0 → v3.2.1 → v3.3.0 → v4.0.0

MAJOR (3 → 4): cambiamenti incompatibili con versioni precedenti
               es. nuovo database, API breaking change, architettura ridisegnata

MINOR (2 → 3): nuove funzionalità compatibili con le versioni precedenti
               es. nuovo modulo, nuova sezione dell'app, nuova API endpoint

PATCH (0 → 1): bugfix e hotfix compatibili
               es. correzione di un bug, fix di sicurezza, ottimizzazione
```

**Le tre tipologie di rilascio**:

| Tipo | Frequenza tipica | Approvazione | Esempio |
|---|---|---|---|
| **Major Release** | Trimestrale / Semestrale | CAB + Business Owner | Nuova versione dell'ERP |
| **Minor Release** | Mensile / Bisettimanale | Release Manager + Tech Lead | Nuovo report, nuova feature |
| **Patch / Hotfix** | Su necessità | ECAB (percorso accelerato) | Fix vulnerabilità, correzione critica |

### Concetto A5: Le Finestre di Manutenzione

Un change in produzione fuori dalla finestra di manutenzione è come eseguire un intervento chirurgico nel corridoio dell'ospedale: possibile, ma rischioso e inaccettabile come prassi.

```
FINESTRE DI MANUTENZIONE STANDARD
──────────────────────────────────────────────────────
Tipo Ambiente         Finestra Primaria       Secondaria
────────────────────  ──────────────────────  ─────────────────
Produzione            Sabato 02:00-06:00      Domenica 02:00-06:00
Pre-produzione        Mercoledì 22:00-02:00   Venerdì 22:00-02:00
Test/Sviluppo         Qualsiasi lavorativo    —
Rete/Infrastruttura   Domenica 02:00-06:00    Su approvazione CAB

LEAD TIME MINIMI
────────────────────────────────────────────────────────
Standard Change       Nessuno (pre-approvato)
Normal Basso          3 giorni lavorativi
Normal Medio          5 giorni lavorativi
Normal Alto           10 giorni lavorativi
Normal Critico        15 giorni lavorativi
Emergency             Immediato (RFC retroattiva entro 24h)
```

---

## PART B: OPERAZIONI — Gestire Change e Release nel Lab

### Esercizio B1: Registrare un Normal Change in GLPI

**Scenario**: Devi aggiornare il firmware del switch di laboratorio. Il change è classificato Normal/Medio: basso impatto (solo lab), ma media probabilità di errore durante l'aggiornamento firmware.

**Obiettivo.** Creare una RFC (Request for Change) completa in GLPI con tutti i campi obbligatori.

**Step 1 — Creare la RFC via API GLPI**

```python
#!/usr/bin/env python3
"""
create_rfc.py — Crea una Request for Change in GLPI tramite REST API.
"""

import requests
from datetime import datetime, timedelta

GLPI_URL = "http://192.168.56.20:8080/glpi"
USER_TOKEN = "YOUR_TOKEN"
APP_TOKEN = "YOUR_APP_TOKEN"


def get_session_token() -> str:
    resp = requests.get(
        f"{GLPI_URL}/apirest.php/initSession",
        headers={
            "Authorization": f"user_token {USER_TOKEN}",
            "App-Token": APP_TOKEN,
            "Content-Type": "application/json"
        },
        timeout=10
    )
    resp.raise_for_status()
    return resp.json()["session_token"]


def create_rfc(session_token: str) -> int:
    """Crea una RFC per upgrade firmware switch."""
    headers = {
        "App-Token": APP_TOKEN,
        "Session-Token": session_token,
        "Content-Type": "application/json"
    }

    # Data implementazione pianificata: sabato prossimo alle 02:00
    today = datetime.now()
    days_to_saturday = (5 - today.weekday()) % 7 or 7
    maint_date = (today + timedelta(days=days_to_saturday)).strftime("%Y-%m-%d 02:00:00")

    rfc_data = {
        "input": {
            "name": "CHG-2026-0042: Upgrade firmware switch LAB-SW-01",
            "content": """DESCRIZIONE MODIFICA:
Aggiornamento firmware dello switch di laboratorio LAB-SW-01 dalla versione 15.2.4
alla versione 15.2.7 per correggere vulnerabilità CVE-2026-1234.

MOTIVAZIONE:
La versione attuale del firmware presenta una vulnerabilità CVSS 7.8 che consente
privilege escalation via SNMP. L'aggiornamento è obbligatorio secondo la policy
di patch management (SOP-SEC-001).

CI IMPATTATI:
- LAB-SW-01 (switch laboratorio, 192.168.56.1)
- Tutti i sistemi del laboratorio (impatto: interruzione rete per ~15 minuti)

PIANO DI IMPLEMENTAZIONE:
1. T-30min: Notificare team lab dell'imminente manutenzione
2. T-5min: Salvare la configurazione corrente del switch
3. T+0: Caricare il firmware nel flash del switch
4. T+5min: Avviare il processo di upgrade
5. T+20min: Verificare che il switch sia tornato online con nuova versione
6. T+25min: Testare la connettività da tutti i sistemi lab

PIANO DI ROLLBACK:
1. Se il firmware non si installa: il switch mantiene la versione precedente
2. Se il switch non riavvia: accesso via console seriale, boot da versione precedente
3. Tempo massimo rollback: 20 minuti
4. Prerequisito rollback: backup configurazione in flash secondaria

TEST PIANIFICATI:
- Verifica versione firmware post-upgrade
- Ping test da tutti gli host lab
- Verifica VLAN configuration intatta
- Verifica SNMP funzionante

COMUNICAZIONE:
Notifica via email al team IT il giovedì precedente con:
- Orario manutenzione: sabato 02:00-03:00
- Impatto atteso: ~15 minuti interruzione rete lab
- Contatto reperibile durante la finestra: lab-admin@lab.local""",
            "status": 1,       # 1 = Nuovo
            "urgency": 2,      # 2 = Medio
            "impact": 2,       # 2 = Medio
            "priority": 2,     # 2 = Medio
            "time_to_resolve": maint_date,
        }
    }

    resp = requests.post(
        f"{GLPI_URL}/apirest.php/Change",
        headers=headers,
        json=rfc_data,
        timeout=10
    )
    resp.raise_for_status()
    change_id = resp.json()["id"]
    print(f"RFC creata con ID: {change_id}")
    return change_id


def add_task_to_rfc(session_token: str, change_id: int, task: str) -> None:
    """Aggiunge un task (passo di implementazione) alla RFC."""
    headers = {
        "App-Token": APP_TOKEN,
        "Session-Token": session_token,
        "Content-Type": "application/json"
    }
    requests.post(
        f"{GLPI_URL}/apirest.php/ChangeTask",
        headers=headers,
        json={
            "input": {
                "changes_id": change_id,
                "content": task,
                "state": 1  # 1 = Da fare
            }
        },
        timeout=10
    )


def main() -> None:
    session_token = get_session_token()
    try:
        change_id = create_rfc(session_token)
        # Aggiungere task di implementazione
        tasks = [
            "Backup configurazione switch: copy running-config flash:backup_before_upgrade.cfg",
            "Caricare firmware: copy tftp://192.168.56.20/firmware/c2960-15.2.7.bin flash:",
            "Eseguire upgrade: archive download-sw /reload /overwrite tftp://...",
            "Verificare versione: show version | include Version",
            "Test connettività: ping 192.168.56.10, .20, .30 da switch",
            "Aggiornare CMDB: cambiare firmware version del CI LAB-SW-01 in GLPI"
        ]
        for task in tasks:
            add_task_to_rfc(session_token, change_id, task)
        print(f"RFC CHG-2026-0042 creata con {len(tasks)} task di implementazione")
        print(f"Accedere a: http://192.168.56.20:8080/glpi/front/change.form.php?id={change_id}")
    finally:
        requests.get(
            f"{GLPI_URL}/apirest.php/killSession",
            headers={"App-Token": APP_TOKEN, "Session-Token": session_token},
            timeout=5
        )


if __name__ == "__main__":
    main()
```

**Output atteso:**
```
RFC creata con ID: 42
RFC CHG-2026-0042 creata con 6 task di implementazione
Accedere a: http://192.168.56.20:8080/glpi/front/change.form.php?id=42
```

---

### Esercizio B2: Gestire un Emergency Change

**Scenario**: Viene rilevata una vulnerabilità critica (CVSS 9.8) in OpenSSH attiva su SRV-LINUX-01. Il patch deve essere applicato entro 4 ore. Questo è un Emergency Change.

**Obiettivo.** Simulare il processo ECAB accelerato e applicare la patch con le stesse garanzie di sicurezza di un Normal Change (backup, verifica, documentazione).

**Step 1 — Notifica ECAB e preparazione**

```bash
# Su SRV-LINUX-01 — PRIMA di qualsiasi modifica: verificare la versione attuale
ssh_version=$(ssh -V 2>&1)
echo "Versione SSH attuale: $ssh_version"

# Verificare i servizi che dipendono da SSH
ss -tlnp | grep :22
who  # Chi è connesso via SSH in questo momento?
```

**Step 2 — Backup pre-change (OBBLIGATORIO anche per Emergency)**

```bash
# Snapshot della VM se possibile (da hypervisor)
# In lab con Proxmox:
# qm snapshot 101 "pre-ssh-patch-$(date +%Y%m%d-%H%M)" --description "Pre-patch CVE-2026-9999"

# Alternativa: backup configurazione SSH e lista pacchetti
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak.$(date +%Y%m%d)
dpkg -l | grep openssh > /tmp/openssh-version-pre-patch.txt
echo "Backup pre-patch completato: $(date)"
```

**Step 3 — Applicare la patch**

```bash
# Aggiornare OpenSSH
sudo apt update
sudo apt install --only-upgrade openssh-server openssh-client -y

# Verificare che il servizio sia stato aggiornato
ssh_version_new=$(ssh -V 2>&1)
echo "Nuova versione SSH: $ssh_version_new"

# Riavviare il servizio SSH (connessione esistente rimane attiva)
sudo systemctl restart sshd
echo "Servizio SSH riavviato: $(systemctl is-active sshd)"
```

**Step 4 — Verifiche post-patch**

```bash
#!/bin/bash
# verify_emergency_change.sh — verifica post-applicazione patch

echo "=== VERIFICA EMERGENCY CHANGE: Patch OpenSSH ==="
echo "Data: $(date)"
echo ""

# 1. Versione SSH aggiornata
echo "1. Versione OpenSSH:"
ssh -V 2>&1

# 2. Servizio attivo
echo ""
echo "2. Stato servizio SSH:"
systemctl status sshd --no-pager | grep -E "Active|Main PID"

# 3. Porta 22 in ascolto
echo ""
echo "3. Porta 22:"
ss -tlnp | grep :22

# 4. Test connessione da client
echo ""
echo "4. Test connessione da WKS-LAB-01:"
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 lab-admin@192.168.56.20 "echo '[OK] Connessione SSH funzionante'" 2>/dev/null

# 5. Verifica configurazione SSH non alterata
echo ""
echo "5. Configurazione SSH (parametri critici):"
grep -E "^PermitRootLogin|^PasswordAuthentication|^AllowUsers" /etc/ssh/sshd_config

echo ""
echo "=== VERIFICA COMPLETATA ==="
```

**Step 5 — Documentare il change retroattivamente**

```python
#!/usr/bin/env python3
"""
document_emergency_change.py — Registra retroattivamente l'Emergency Change in GLPI.
Deve essere completato entro 24 ore dall'implementazione.
"""

import requests
from datetime import datetime

GLPI_URL = "http://192.168.56.20:8080/glpi"
USER_TOKEN = "YOUR_TOKEN"
APP_TOKEN = "YOUR_APP_TOKEN"


def document_emergency_change(session_token: str) -> None:
    headers = {
        "App-Token": APP_TOKEN,
        "Session-Token": session_token,
        "Content-Type": "application/json"
    }
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    rfc_data = {
        "input": {
            "name": f"EMER-CHG-2026-0043: Emergency patch OpenSSH CVE-2026-9999",
            "content": f"""EMERGENCY CHANGE — RFC RETROATTIVA
Creata: {now}

VULNERABILITÀ: CVE-2026-9999 (CVSS 9.8 — Critico)
Componente: OpenSSH < versione X.X
Impatto: RCE non autenticata via porta 22

AUTORIZZAZIONE ECAB:
Data: {now}
Partecipanti: lab-admin (Change Manager), lab-admin (Tech Lead)
Autorizzazione verbale alle: {now}
Motivo emergenza: CVSS 9.8, exploit pubblico disponibile, finestra di attacco aperta

AZIONI ESEGUITE:
1. Backup configurazione SSH: /etc/ssh/sshd_config.bak.{datetime.now().strftime('%Y%m%d')}
2. Snapshot VM creato: pre-ssh-patch-{datetime.now().strftime('%Y%m%d-%H%M')}
3. Patch applicata: apt upgrade openssh-server
4. Servizio riavviato: systemctl restart sshd
5. Verifica post-patch: SUCCESSO

SISTEMI IMPATTATI: SRV-LINUX-01 (192.168.56.20)
DOWNTIME: 0 (patch a caldo, nessuna interruzione di servizio)

REVISIONE CAB ORDINARIA: pianificata per il prossimo martedì

NEXT STEPS:
- Verificare altri sistemi con OpenSSH vulnerabile
- Aggiornare asset inventory per tracciare la patch
- Aggiornare CMDB con nuova versione software""",
            "status": 5,   # 5 = Completato
            "urgency": 5,  # 5 = Urgentissimo
            "impact": 4,   # 4 = Alto
            "priority": 5, # 5 = Critico
        }
    }

    resp = requests.post(
        f"{GLPI_URL}/apirest.php/Change",
        headers=headers,
        json=rfc_data,
        timeout=10
    )
    resp.raise_for_status()
    change_id = resp.json()["id"]
    print(f"Emergency Change documentato con ID: {change_id}")


def main() -> None:
    resp = requests.get(
        f"{GLPI_URL}/apirest.php/initSession",
        headers={"Authorization": f"user_token {USER_TOKEN}", "App-Token": APP_TOKEN},
        timeout=10
    )
    session_token = resp.json()["session_token"]
    try:
        document_emergency_change(session_token)
    finally:
        requests.get(
            f"{GLPI_URL}/apirest.php/killSession",
            headers={"App-Token": APP_TOKEN, "Session-Token": session_token},
            timeout=5
        )


if __name__ == "__main__":
    main()
```

---

### Esercizio B3: Creare un Modello Standard Change

**Obiettivo.** Creare il modello GLPI per il reset password (Standard Change), che consente l'esecuzione senza approvazione real-time.

**Background.** Senza modelli Standard Change, ogni reset password diventerebbe una Normal Change da approvare — assurdo. I modelli pre-approvati dal CAB consentono ai tecnici di procedere autonomamente per le attività a rischio zero.

**Step 1 — Definire il modello Standard Change**

```bash
cat > /opt/procedures/templates/SC-IAM-001_reset_password.md << 'EOF'
# Modello Standard Change: SC-IAM-001 — Reset Password Utente

## Stato: PRE-APPROVATO dal CAB in data 2026-01-15

## Classificazione
- **Tipo**: Standard Change
- **Rischio**: Basso (azione reversibile, impatta singolo utente)
- **Finestra di esecuzione**: Qualsiasi orario lavorativo (lunedì-venerdì 08:00-18:00)
  - Per richieste urgenti fuori orario: solo se il manager dell'utente è raggiungibile

## Campi variabili (da compilare a ogni esecuzione)
- Username dell'utente: ___________
- Motivo del reset: ___________
- Richiedente (nome manager o utente): ___________
- Ticket correlato: ___________

## Procedura (NON modificare — modello pre-approvato)

```powershell
$Username = "NOME.COGNOME"  # Sostituire con lo username reale
$TempPwd = "Reset$(Get-Random -Min 1000 -Max 9999)!Tmp"

# 1. Reimpostare la password
Set-ADAccountPassword -Identity $Username `
    -NewPassword (ConvertTo-SecureString $TempPwd -AsPlainText -Force) -Reset

# 2. Richiedere cambio al prossimo login
Set-ADUser -Identity $Username -ChangePasswordAtLogon $true

# 3. Sbloccare l'account se bloccato
Unlock-ADAccount -Identity $Username

# 4. Verificare
$user = Get-ADUser -Identity $Username -Properties LockedOut, PasswordExpired
Write-Output "Account: $($user.SamAccountName) — Sbloccato: $(-not $user.LockedOut)"
```

## Verifica
- [ ] Account non bloccato: `Get-ADUser -Identity $Username -Properties LockedOut`
- [ ] Utente riesce ad accedere con la nuova password temporanea
- [ ] Utente viene forzato al cambio password al primo accesso

## Comunicazione
- Inviare la password temporanea al richiedente (manager) via canale sicuro
- NON inviare via email non cifrata

## Registrazione
Il completamento viene registrato automaticamente nel sistema ITSM con:
- Timestamp
- Username del tecnico esecutore
- Username dell'utente interessato

## Revisione modello
Prossima revisione CAB: 2027-01-15
EOF

echo "Modello SC-IAM-001 creato"
```

---

### Esercizio B4: Pianificare un Ciclo di Release

**Obiettivo.** Creare il piano di release per una versione `v2.3.0` di un'applicazione web lab, con tutte le fasi documentate.

**Background.** In questo esercizio l'applicazione è un semplice servizio web Python che espone un'API. Il ciclo di release simula il processo reale di un team di sviluppo.

**Step 1 — Creare l'applicazione di esempio**

```python
# webapp/app.py — Applicazione web di esempio per il lab
"""
Versione 2.2.0 — release attuale in produzione
Nuova versione 2.3.0 da rilasciare: aggiunge endpoint /health e /version
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os

APP_VERSION = os.environ.get("APP_VERSION", "2.2.0")


class LabHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self._respond(200, {"status": "ok", "app": "Lab WebApp"})
        elif self.path == "/version":
            self._respond(200, {"version": APP_VERSION})
        elif self.path == "/health":
            self._respond(200, {"status": "healthy", "version": APP_VERSION})
        else:
            self._respond(404, {"error": "not found"})

    def _respond(self, code: int, data: dict) -> None:
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass  # Silenziare i log in stdout per pulizia output


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8090), LabHandler)
    print(f"Lab WebApp v{APP_VERSION} in ascolto su :8090")
    server.serve_forever()
```

**Step 2 — Script di release pipeline**

```bash
#!/bin/bash
# release_pipeline.sh — Pipeline di release per Lab WebApp
# Uso: ./release_pipeline.sh <version> <environment>

VERSION="${1:-2.3.0}"
ENV="${2:-staging}"
APP_DIR="/opt/webapp"
BACKUP_DIR="/opt/webapp-backup"
RELEASE_LOG="/var/log/releases/release-${VERSION}-$(date +%Y%m%d).log"

mkdir -p "$(dirname $RELEASE_LOG)" "$BACKUP_DIR"
log() { echo "[$(date '+%H:%M:%S')] $1" | tee -a "$RELEASE_LOG"; }

log "=== RELEASE PIPELINE: v${VERSION} → ${ENV} ==="
log "Avviato da: $(whoami)"

# ─── FASE 1: Verifica prerequisiti ────────────────────────────────────────
log ""
log "FASE 1: Verifica prerequisiti"
log "────────────────────────────"

# Verificare che la versione sia taggata in Git
if ! git -C "$APP_DIR" tag | grep -q "v${VERSION}"; then
    log "[FAIL] Tag v${VERSION} non trovato in Git"
    exit 1
fi
log "[OK] Tag v${VERSION} trovato"

# Verificare test automatizzati
log "Esecuzione test suite..."
if python3 -m pytest tests/ -q 2>/dev/null; then
    log "[OK] Tutti i test passano"
else
    log "[FAIL] Test falliti — release bloccata"
    exit 1
fi

# ─── FASE 2: Build e checksum ─────────────────────────────────────────────
log ""
log "FASE 2: Build e checksum"
log "────────────────────────"

TARBALL="webapp-${VERSION}.tar.gz"
git -C "$APP_DIR" archive --prefix="webapp-${VERSION}/" "v${VERSION}" | gzip > "/tmp/${TARBALL}"
sha256sum "/tmp/${TARBALL}" > "/tmp/${TARBALL}.sha256"
log "[OK] Build completata: ${TARBALL}"
log "[OK] Checksum: $(cat /tmp/${TARBALL}.sha256 | awk '{print $1}')"

# ─── FASE 3: Deploy in ambiente target ────────────────────────────────────
log ""
log "FASE 3: Deploy in ${ENV}"
log "────────────────────────"

# Backup versione corrente
if [ -d "$APP_DIR/current" ]; then
    CURRENT_VERSION=$(cat "$APP_DIR/current/VERSION" 2>/dev/null || echo "unknown")
    cp -r "$APP_DIR/current" "${BACKUP_DIR}/webapp-${CURRENT_VERSION}-$(date +%Y%m%d)"
    log "[OK] Backup versione corrente (${CURRENT_VERSION})"
fi

# Deploy nuova versione
mkdir -p "$APP_DIR/releases/v${VERSION}"
tar -xzf "/tmp/${TARBALL}" -C "$APP_DIR/releases/" 2>/dev/null || true
echo "${VERSION}" > "$APP_DIR/releases/v${VERSION}/VERSION"

# Aggiornare il symlink "current"
rm -f "$APP_DIR/current"
ln -s "$APP_DIR/releases/v${VERSION}" "$APP_DIR/current"
log "[OK] Symlink aggiornato: current → v${VERSION}"

# Riavviare il servizio
export APP_VERSION="${VERSION}"
pkill -f "webapp/app.py" 2>/dev/null || true
sleep 1
nohup python3 "$APP_DIR/current/app.py" >> /var/log/webapp.log 2>&1 &
sleep 2

# ─── FASE 4: Smoke test post-deploy ───────────────────────────────────────
log ""
log "FASE 4: Smoke test"
log "──────────────────"

DEPLOYED_VERSION=$(curl -s http://localhost:8090/version 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('version','?'))" 2>/dev/null)
HEALTH_STATUS=$(curl -s http://localhost:8090/health 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','?'))" 2>/dev/null)

if [ "$DEPLOYED_VERSION" = "$VERSION" ] && [ "$HEALTH_STATUS" = "healthy" ]; then
    log "[OK] Versione deployata: ${DEPLOYED_VERSION}"
    log "[OK] Health check: ${HEALTH_STATUS}"
    log ""
    log "=== RELEASE v${VERSION} COMPLETATA CON SUCCESSO ==="
else
    log "[FAIL] Versione attesa: ${VERSION}, trovata: ${DEPLOYED_VERSION}"
    log "[FAIL] Health: ${HEALTH_STATUS}"
    log ""
    log "=== AVVIANDO ROLLBACK ==="
    # Rollback al symlink precedente
    if [ -d "${BACKUP_DIR}/webapp-${CURRENT_VERSION}-$(date +%Y%m%d)" ]; then
        rm -f "$APP_DIR/current"
        ln -s "${BACKUP_DIR}/webapp-${CURRENT_VERSION}-$(date +%Y%m%d)" "$APP_DIR/current"
        pkill -f "webapp/app.py" 2>/dev/null || true
        sleep 1
        nohup python3 "$APP_DIR/current/app.py" >> /var/log/webapp.log 2>&1 &
        log "[OK] Rollback a v${CURRENT_VERSION} completato"
    fi
    exit 1
fi
```

**Step 3 — Checklist Go/No-Go Release**

```bash
cat > /opt/procedures/templates/go_nogo_checklist.md << 'EOF'
# Checklist Go/No-Go — Release [VERSIONE]

**Data riunione**: _______________
**Partecipanti**: Release Manager, Tech Lead, QA Lead, Business Owner, Ops Lead

---

## CRITERI DI GO (tutti devono essere soddisfatti)

### Test e Qualità
- [ ] Tutti i test automatizzati passano (0 fallimenti)
- [ ] Test manuali completati con esito positivo
- [ ] UAT sign-off ricevuto dal Business Owner (firma: _______________)
- [ ] Nessun difetto bloccante (Sev 1) aperto
- [ ] Difetti Sev 2 documentati con workaround o differiti al prossimo rilascio

### Operazioni
- [ ] Runbook di deployment revisionato e testato in staging
- [ ] Runbook di rollback revisionato e testato in staging
- [ ] Backup/snapshot pianificato (chi lo esegue: _______________)
- [ ] Finestra di manutenzione confermata e comunicata agli stakeholder
- [ ] Risorse tecniche disponibili durante il deployment

### Governance
- [ ] RFC approvata dal CAB (per Major/Minor release)
- [ ] Piano di comunicazione pronto e inviato
- [ ] Monitoraggio post-rilascio pianificato (chi monitora: _______________)
- [ ] CMDB aggiornato con i CI che cambieranno

---

## RISULTATO

- [ ] **GO** — Procedere con il rilascio
- [ ] **NO-GO** — Rinviare (motivazione: _______________)
- [ ] **GO CONDIZIONATO** — Procedere con riserva (condizioni: _______________)

**Firma Release Manager**: _______________
**Firma Business Owner**: _______________

---

## BAKING TIME (monitoraggio post-release)

Periodo: 72 ore (3 giorni) post-deployment
Responsabile: _______________
Metriche da monitorare:
- Tasso di errori (target: < 1% delle richieste)
- Tempo di risposta p95 (target: < 500ms)
- Utilizzo CPU e memoria (target: non superiore al baseline + 20%)
- Alert Prometheus/Grafana: nessun alert critico

Notifica al team se tasso errori > 1% o se ricevuto feedback negativo dagli utenti.
EOF

echo "Checklist Go/No-Go creata"
```

---

### Esercizio B5: Access Review Periodica

**Obiettivo.** Eseguire un ciclo di Access Review per gli utenti del laboratorio, identificare account inattivi e generare il report per il manager.

**Background.** La ricertificazione degli accessi non è un'attività facoltativa per le organizzazioni soggette a ISO 27001, SOX, GDPR. È un controllo obbligatorio che verifica periodicamente che ogni utente abbia esattamente i permessi necessari — non di più.

**Step 1 — Estrarre gli accessi correnti**

```powershell
# Su DC-LAB-01 — Estrarre tutti gli utenti con i loro gruppi
$ReportDate = Get-Date -Format "yyyyMMdd"
$OutputPath = "C:\AccessReview\UserAccess_$ReportDate.csv"

New-Item -ItemType Directory -Path "C:\AccessReview" -Force | Out-Null

Get-ADUser -Filter {Enabled -eq $true} -Properties MemberOf, LastLogonDate, Department, Manager |
    Select-Object SamAccountName, Name, Department,
        @{N='Manager'; E={(Get-ADUser $_.Manager -ErrorAction SilentlyContinue).Name}},
        @{N='Groups'; E={
            ($_.MemberOf | ForEach-Object { (Get-ADGroup $_ -ErrorAction SilentlyContinue).Name }) -join '; '
        }},
        LastLogonDate, Enabled |
    Export-Csv -Path $OutputPath -NoTypeInformation -Encoding UTF8

Write-Output "Report accessi esportato: $OutputPath"
Write-Output "Righe nel file: $((Import-Csv $OutputPath | Measure-Object).Count)"
```

**Step 2 — Identificare anomalie**

```powershell
# Account inattivi (nessun login da 90+ giorni)
$InactiveThreshold = (Get-Date).AddDays(-90)
$InactiveAccounts = Get-ADUser -Filter {
    Enabled -eq $true -and LastLogonDate -lt $InactiveThreshold
} -Properties LastLogonDate |
    Select-Object SamAccountName, Name, LastLogonDate

Write-Output "=== ACCOUNT INATTIVI (90+ giorni) ==="
$InactiveAccounts | Format-Table -AutoSize

# Account senza login recente
$NeverLoggedIn = Get-ADUser -Filter {
    Enabled -eq $true -and LastLogonDate -notlike "*"
} |
    Select-Object SamAccountName, Name

Write-Output ""
Write-Output "=== ACCOUNT MAI USATI ==="
$NeverLoggedIn | Format-Table -AutoSize
```

**Step 3 — Script Python per report HTML**

```python
#!/usr/bin/env python3
"""
access_review_report.py — Genera report HTML per l'Access Review.
Legge il CSV esportato da PowerShell e produce un report leggibile per i manager.
"""

import csv
from datetime import datetime, timedelta
from pathlib import Path

CSV_PATH = "/mnt/c/AccessReview/UserAccess_20260101.csv"  # Aggiornare data
OUTPUT_PATH = "/opt/procedures/reports/access_review_report.html"
INACTIVE_DAYS = 90


def load_users(csv_path: str) -> list[dict]:
    with open(csv_path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def classify_user(user: dict) -> str:
    last_logon = user.get("LastLogonDate", "")
    if not last_logon:
        return "mai_usato"
    try:
        logon_date = datetime.strptime(last_logon[:10], "%Y-%m-%d")
        if logon_date < datetime.now() - timedelta(days=INACTIVE_DAYS):
            return "inattivo"
    except ValueError:
        return "sconosciuto"
    return "attivo"


def generate_html(users: list[dict]) -> str:
    active = [u for u in users if classify_user(u) == "attivo"]
    inactive = [u for u in users if classify_user(u) == "inattivo"]
    never = [u for u in users if classify_user(u) == "mai_usato"]

    def user_rows(user_list: list[dict]) -> str:
        rows = []
        for u in user_list:
            rows.append(
                f"<tr><td>{u.get('SamAccountName','')}</td>"
                f"<td>{u.get('Name','')}</td>"
                f"<td>{u.get('Department','')}</td>"
                f"<td>{u.get('Manager','')}</td>"
                f"<td>{u.get('LastLogonDate','Mai')[:10]}</td>"
                f"<td style='font-size:0.8em'>{u.get('Groups','')[:80]}...</td></tr>"
            )
        return "\n".join(rows)

    return f"""<!DOCTYPE html>
<html lang="it">
<head><meta charset="UTF-8">
<title>Access Review — {datetime.now().strftime('%Y-%m-%d')}</title>
<style>
body {{font-family: Arial, sans-serif; margin: 20px;}}
h1 {{color: #333;}} h2 {{color: #555;}}
table {{border-collapse: collapse; width: 100%; margin-bottom: 20px;}}
th {{background: #4a90d9; color: white; padding: 8px; text-align: left;}}
td {{border: 1px solid #ddd; padding: 6px;}}
tr:nth-child(even) {{background: #f9f9f9;}}
.summary {{background: #f0f4ff; border: 1px solid #c0d0ff; padding: 15px; border-radius: 5px;}}
.warn {{background: #fff3cd;}} .danger {{background: #f8d7da;}}
</style></head>
<body>
<h1>Report Access Review — {datetime.now().strftime('%d/%m/%Y')}</h1>
<div class="summary">
<strong>Totale utenti analizzati:</strong> {len(users)}<br>
<strong>Account attivi:</strong> {len(active)}<br>
<strong>Account inattivi (90+ giorni):</strong> {len(inactive)} ⚠️<br>
<strong>Account mai usati:</strong> {len(never)} ❌<br>
<strong>Azione richiesta entro:</strong> {(datetime.now() + timedelta(days=10)).strftime('%d/%m/%Y')}
</div>

<h2>Account Inattivi — Azione Richiesta</h2>
<p>Per ogni utente selezionare: <strong>[CONFERMA]</strong> / <strong>[REVOCA]</strong> / <strong>[MODIFICA]</strong></p>
<table class="warn">
<tr><th>Username</th><th>Nome</th><th>Reparto</th><th>Manager</th>
<th>Ultimo accesso</th><th>Gruppi (estratto)</th></tr>
{user_rows(inactive)}
</table>

<h2>Account Mai Usati</h2>
<table class="danger">
<tr><th>Username</th><th>Nome</th><th>Reparto</th><th>Manager</th>
<th>Ultimo accesso</th><th>Gruppi (estratto)</th></tr>
{user_rows(never)}
</table>

<h2>Account Attivi</h2>
<table>
<tr><th>Username</th><th>Nome</th><th>Reparto</th><th>Manager</th>
<th>Ultimo accesso</th><th>Gruppi (estratto)</th></tr>
{user_rows(active)}
</table>
</body></html>"""


def main() -> None:
    Path(OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)
    users = load_users(CSV_PATH)
    html = generate_html(users)
    Path(OUTPUT_PATH).write_text(html, encoding="utf-8")
    print(f"Report generato: {OUTPUT_PATH}")
    print(f"Aprire con: firefox {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
```

---

### Esercizio B6: SOP Decommissioning Asset IT (Dismissione Sicura)

**Obiettivo.** Simulare il processo completo di dismissione di un server lab, con sanitizzazione dati e aggiornamento CMDB.

**Background.** La dismissione di un asset senza sanitizzazione dei dati è una violazione del GDPR (art. 5) e un rischio di sicurezza critico. Dischi rigidi venduti su eBay con dati aziendali sono una categoria frequente di data breach.

**Step 1 — Checklist pre-dismissione**

```bash
#!/bin/bash
# decommission_check.sh — Pre-dismissione checklist

ASSET_HOSTNAME="${1:-SRV-OLD-01}"
ASSET_IP="${2:-192.168.56.50}"

echo "=== CHECKLIST PRE-DISMISSIONE: $ASSET_HOSTNAME ==="
echo ""

# 1. Ping
echo "1. Verifica raggiungibilità:"
ping -c 2 "$ASSET_IP" > /dev/null 2>&1 && echo "   [!] Sistema ancora raggiungibile — procedere con cautela" || echo "   [OK] Sistema non raggiungibile (spento o rimosso rete)"

# 2. Verificare servizi attivi
echo ""
echo "2. Servizi che potrebbero dipendere da questo sistema:"
echo "   → Controllare in GLPI: CI $ASSET_HOSTNAME → relazioni 'depends on'"
echo "   → Verificare in Prometheus: metriche per target $ASSET_IP"

# 3. Backup dati
echo ""
echo "3. Backup finale:"
echo "   [ ] Tutti i dati critici sono stati trasferiti o archiviati"
echo "   [ ] Backup finale verificato e testato"

# 4. Accessi da revocare
echo ""
echo "4. Accessi da revocare prima della dismissione:"
echo "   [ ] Account di servizio specifici per questo server"
echo "   [ ] Regole firewall dedicate (SSH, RDP, porte applicazione)"
echo "   [ ] DNS record: $(nslookup "$ASSET_HOSTNAME" 192.168.56.10 2>/dev/null | grep -A1 "Name:" | tail -1)"
echo "   [ ] Monitoring: rimuovere target $ASSET_IP da Prometheus"
echo "   [ ] Backup job: disattivare o eliminare il job di backup"

echo ""
echo "PRIMA DI PROCEDERE: completare tutti i check sopra"
```

**Step 2 — Sanitizzazione dati (simulata in lab)**

```bash
# SIMULAZIONE in lab — NON eseguire su sistemi reali senza approvazione

echo "=== SANITIZZAZIONE DATI ==="
echo ""
echo "Metodi disponibili in base al tipo di supporto:"
echo ""
echo "HDD Magnetico:"
echo "  1. Sovrascrittura 3 passaggi (NIST Clear):"
echo "     shred -vfz -n 3 /dev/sdX"
echo ""
echo "  2. Sovrascrittura con nwipe (DoD Short):"
echo "     nwipe --autonuke --method=dodshort /dev/sdX"
echo ""
echo "SSD/NVMe:"
echo "  1. ATA Secure Erase (NIST Purge):"
echo "     hdparm --security-erase 'SECURE ERASE PASSWORD' /dev/sdX"
echo ""
echo "  2. NVMe Crypto Erase:"
echo "     nvme format /dev/nvme0 --ses=1"
echo ""
echo "Distruzione fisica (per dati classificati):"
echo "  → Affidate a fornitore certificato R2/e-Stewards con certificato di distruzione"
echo ""

# In lab: simulare con un file di test
echo "--- SIMULAZIONE ---"
dd if=/dev/urandom of=/tmp/test_sanitization.dat bs=1M count=1 2>/dev/null
shred -vfz -n 1 /tmp/test_sanitization.dat 2>&1 | head -5
echo "Sanitizzazione simulata completata"
```

**Step 3 — Aggiornare CMDB e ITSM**

```python
#!/usr/bin/env python3
"""
decommission_asset.py — Aggiorna GLPI alla dismissione di un CI.
"""

import requests

GLPI_URL = "http://192.168.56.20:8080/glpi"
USER_TOKEN = "YOUR_TOKEN"
APP_TOKEN = "YOUR_APP_TOKEN"


def decommission_ci(asset_name: str, reason: str, session_token: str) -> None:
    headers = {
        "App-Token": APP_TOKEN,
        "Session-Token": session_token,
        "Content-Type": "application/json"
    }

    # Cercare il CI
    search_resp = requests.get(
        f"{GLPI_URL}/apirest.php/Computer?searchText[name]={asset_name}",
        headers=headers,
        timeout=10
    )
    computers = search_resp.json()
    if not computers:
        print(f"CI non trovato: {asset_name}")
        return

    ci_id = computers[0]["id"]

    # Aggiornare lo stato a "Dismesso" (stati GLPI: 1=Nuovo, 2=In uso, 3=Riparazione, 4=Dismissione, 5=Dismesso)
    update_resp = requests.put(
        f"{GLPI_URL}/apirest.php/Computer/{ci_id}",
        headers=headers,
        json={
            "input": {
                "states_id": 5,  # Dismesso
                "comment": f"DISMESSO: {reason}"
            }
        },
        timeout=10
    )

    if update_resp.status_code == 200:
        print(f"CI {asset_name} (ID: {ci_id}) aggiornato a stato Dismesso")
    else:
        print(f"Errore aggiornamento CI: {update_resp.status_code}")


def main() -> None:
    resp = requests.get(
        f"{GLPI_URL}/apirest.php/initSession",
        headers={"Authorization": f"user_token {USER_TOKEN}", "App-Token": APP_TOKEN},
        timeout=10
    )
    session_token = resp.json()["session_token"]
    try:
        decommission_ci(
            asset_name="SRV-OLD-01",
            reason="End of life — 7 anni di servizio. Sostituito da SRV-LAB-03. Dati sanitizzati con shred.",
            session_token=session_token
        )
    finally:
        requests.get(
            f"{GLPI_URL}/apirest.php/killSession",
            headers={"App-Token": APP_TOKEN, "Session-Token": session_token},
            timeout=5
        )


if __name__ == "__main__":
    main()
```

---

## PART C: SISTEMATIZZARE — KPI, Calendario e Governance

### Progetto C1: Dashboard KPI Change Management

**Obiettivo.** Creare uno script Python che calcola i KPI del processo Change Management dal database GLPI.

```python
#!/usr/bin/env python3
"""
change_kpi.py — Calcola e stampa i KPI del processo Change Management da GLPI.
"""

import requests
from datetime import datetime, timedelta
from typing import Any

GLPI_URL = "http://192.168.56.20:8080/glpi"
USER_TOKEN = "YOUR_TOKEN"
APP_TOKEN = "YOUR_APP_TOKEN"

TARGET_KPIS = {
    "success_rate": 95.0,     # >= 95% change completati con successo
    "emergency_ratio": 5.0,   # <= 5% emergency change sul totale
    "failed_change_rate": 2.0 # <= 2% change che causano incidenti
}


def get_all_changes(session_token: str, days: int = 30) -> list[dict[str, Any]]:
    """Recupera tutti i change dell'ultimo periodo."""
    headers = {
        "App-Token": APP_TOKEN,
        "Session-Token": session_token,
        "Content-Type": "application/json"
    }
    resp = requests.get(
        f"{GLPI_URL}/apirest.php/Change",
        headers=headers,
        params={"range": "0-999"},
        timeout=15
    )
    if resp.status_code != 200:
        return []
    return resp.json() if isinstance(resp.json(), list) else []


def calculate_kpis(changes: list[dict[str, Any]]) -> dict[str, float]:
    if not changes:
        return {}

    total = len(changes)
    # Status GLPI Change: 5 = Risolto (completato), 8 = Chiuso, 3 = In corso
    # Urgency 5 = Emergency
    completed = sum(1 for c in changes if c.get("status") in (5, 8))
    emergency = sum(1 for c in changes if c.get("urgency") == 5)

    return {
        "total_changes": total,
        "completed": completed,
        "emergency": emergency,
        "success_rate": (completed / total * 100) if total else 0,
        "emergency_ratio": (emergency / total * 100) if total else 0,
    }


def print_kpi_report(kpis: dict[str, float]) -> None:
    print(f"\n{'='*60}")
    print(f"  KPI CHANGE MANAGEMENT — {datetime.now().strftime('%d/%m/%Y')}")
    print(f"{'='*60}\n")

    if not kpis:
        print("  Nessun dato disponibile nel periodo selezionato.")
        return

    print(f"  Change totali periodo:  {kpis.get('total_changes', 0)}")
    print(f"  Change completati:      {kpis.get('completed', 0)}")
    print(f"  Change emergency:       {kpis.get('emergency', 0)}")
    print()

    sr = kpis.get("success_rate", 0)
    er = kpis.get("emergency_ratio", 0)

    sr_status = "✅" if sr >= TARGET_KPIS["success_rate"] else "❌"
    er_status = "✅" if er <= TARGET_KPIS["emergency_ratio"] else "❌"

    print(f"  {sr_status} Change Success Rate:    {sr:.1f}%  (target: ≥{TARGET_KPIS['success_rate']}%)")
    print(f"  {er_status} Emergency Change Ratio: {er:.1f}%  (target: ≤{TARGET_KPIS['emergency_ratio']}%)")
    print(f"\n{'='*60}\n")


def main() -> None:
    resp = requests.get(
        f"{GLPI_URL}/apirest.php/initSession",
        headers={"Authorization": f"user_token {USER_TOKEN}", "App-Token": APP_TOKEN},
        timeout=10
    )
    session_token = resp.json().get("session_token")
    if not session_token:
        print("Errore autenticazione GLPI")
        return
    try:
        changes = get_all_changes(session_token)
        kpis = calculate_kpis(changes)
        print_kpi_report(kpis)
    finally:
        requests.get(
            f"{GLPI_URL}/apirest.php/killSession",
            headers={"App-Token": APP_TOKEN, "Session-Token": session_token},
            timeout=5
        )


if __name__ == "__main__":
    main()
```

### Progetto C2: Calendario Automatizzato Change e Manutenzioni

```bash
cat > /opt/procedures/scripts/maintenance_calendar.sh << 'SCRIPT'
#!/bin/bash
# maintenance_calendar.sh — Genera il calendario delle prossime manutenzioni

NEXT_DAYS=30
TODAY=$(date +%s)

echo "=== CALENDARIO MANUTENZIONI — PROSSIMI $NEXT_DAYS GIORNI ==="
echo "Generato: $(date '+%d/%m/%Y %H:%M')"
echo ""

# Calcolare le finestre di manutenzione produzione (sabati 02:00-06:00)
echo "FINESTRE PRODUZIONE (Sabato 02:00-06:00):"
for i in $(seq 0 $NEXT_DAYS); do
    FUTURE=$(date -d "+$i days" +%u)  # 6 = Sabato
    if [ "$FUTURE" = "6" ]; then
        DATE=$(date -d "+$i days" '+%d/%m/%Y')
        echo "  → $DATE 02:00-06:00 (tra $i giorni)"
    fi
done

echo ""
echo "REVISIONI PROCEDURE IN SCADENZA (prossimi 30 giorni):"
/opt/procedures/scripts/review_scheduler.sh 2>/dev/null | grep -E "SCADUTA|IN SCADENZA"

echo ""
echo "ACCESS REVIEW IN PROGRAMMA:"
echo "  → Account privilegiati: revisione trimestrale"
echo "  → Revisione prossima: $(date -d '+90 days' '+%d/%m/%Y')"

echo ""
echo "CAB MEETINGS (ogni martedì):"
for i in $(seq 0 $NEXT_DAYS); do
    FUTURE=$(date -d "+$i days" +%u)  # 2 = Martedì
    if [ "$FUTURE" = "2" ]; then
        DATE=$(date -d "+$i days" '+%d/%m/%Y')
        echo "  → $DATE 14:00-15:00 — CAB Meeting"
    fi
done
SCRIPT

chmod +x /opt/procedures/scripts/maintenance_calendar.sh
/opt/procedures/scripts/maintenance_calendar.sh
```

### Progetto C3: Integrare Change → CMDB → Monitoring

**Il principio di integrazione**: ogni change approvato aggiorna il CMDB, e ogni aggiornamento CMDB aggiorna le dashboard di monitoring. Nessun CI rimane fuori sincronia.

```python
#!/usr/bin/env python3
"""
change_cmdb_sync.py — Sincronizza il completamento di un change con CMDB e monitoring.
Quando un change viene chiuso in GLPI:
1. Aggiorna il CI nel CMDB (versione, stato, data ultimo aggiornamento)
2. Aggiorna le label in Prometheus (opzionale, via file di configurazione)
3. Aggiunge una nota nel ticket con la conferma di aggiornamento CMDB
"""

import requests
import json
from pathlib import Path

GLPI_URL = "http://192.168.56.20:8080/glpi"
USER_TOKEN = "YOUR_TOKEN"
APP_TOKEN = "YOUR_APP_TOKEN"
PROMETHEUS_SD_DIR = "/etc/prometheus/file_sd"


def update_ci_after_change(
    ci_name: str,
    new_version: str,
    change_id: int,
    session_token: str
) -> None:
    headers = {
        "App-Token": APP_TOKEN,
        "Session-Token": session_token,
        "Content-Type": "application/json"
    }

    # 1. Trovare il CI per nome
    search_resp = requests.get(
        f"{GLPI_URL}/apirest.php/Computer?searchText[name]={ci_name}",
        headers=headers, timeout=10
    )
    computers = search_resp.json() if search_resp.status_code == 200 else []
    if not computers:
        print(f"CI non trovato: {ci_name}")
        return

    ci_id = computers[0]["id"]

    # 2. Aggiornare il CI (versione software, commento)
    from datetime import datetime
    update_data = {
        "input": {
            "comment": f"Aggiornato da CHG-{change_id} il {datetime.now().strftime('%Y-%m-%d %H:%M')}. Versione: {new_version}",
            "states_id": 2  # In uso (normale)
        }
    }
    resp = requests.put(
        f"{GLPI_URL}/apirest.php/Computer/{ci_id}",
        headers=headers, json=update_data, timeout=10
    )
    if resp.status_code == 200:
        print(f"CI {ci_name} aggiornato in CMDB con versione {new_version}")

    # 3. Aggiungere nota al change ticket
    note = f"""CMDB AGGIORNATO:
CI: {ci_name} (ID: {ci_id})
Versione software aggiornata a: {new_version}
Aggiornamento automatico post-change."""

    requests.post(
        f"{GLPI_URL}/apirest.php/ChangeTask",
        headers=headers,
        json={"input": {"changes_id": change_id, "content": note, "state": 2}},  # 2 = Completato
        timeout=10
    )
    print(f"Nota aggiunta al change #{change_id}")

    # 4. Aggiornare Prometheus file service discovery (aggiornare labels)
    sd_file = Path(PROMETHEUS_SD_DIR) / f"{ci_name.lower()}.json"
    if sd_file.parent.exists():
        sd_config = [{
            "targets": [f"{ci_name.lower()}:9100"],
            "labels": {
                "hostname": ci_name,
                "version": new_version,
                "last_change": f"CHG-{change_id}",
                "environment": "lab"
            }
        }]
        sd_file.write_text(json.dumps(sd_config, indent=2))
        print(f"Prometheus SD aggiornato: {sd_file}")


def main() -> None:
    resp = requests.get(
        f"{GLPI_URL}/apirest.php/initSession",
        headers={"Authorization": f"user_token {USER_TOKEN}", "App-Token": APP_TOKEN},
        timeout=10
    )
    session_token = resp.json().get("session_token")
    if not session_token:
        print("Errore autenticazione GLPI")
        return
    try:
        # Simulare la sincronizzazione post-change
        update_ci_after_change(
            ci_name="SRV-LINUX-01",
            new_version="OpenSSH 9.7p1",
            change_id=43,  # ID del change "EMER-CHG-2026-0043"
            session_token=session_token
        )
    finally:
        requests.get(
            f"{GLPI_URL}/apirest.php/killSession",
            headers={"App-Token": APP_TOKEN, "Session-Token": session_token},
            timeout=5
        )


if __name__ == "__main__":
    main()
```

---

## Checklist di Validazione Lab

**Parte A — Fondamenti:**
- [ ] A1: Classificare correttamente 5 scenari reali (incidente/change/SR/problem) senza consultare note
- [ ] A2: Disegnare il flusso Normal Change (RFC → valutazione → approvazione → impl. → PIR) su carta
- [ ] A3: Applicare la matrice rischio/impatto a 3 scenari proposti
- [ ] A4: Spiegare il formato SemVer e la differenza tra Major/Minor/Patch
- [ ] A5: Elencare le finestre di manutenzione standard e i lead time

**Parte B — Esercizi:**
- [ ] B1: RFC CHG-2026-0042 creata in GLPI con tutti i campi
- [ ] B1: RFC visibile nella lista change con stato "Nuovo"
- [ ] B2: Emergency Change patch OpenSSH eseguito e verificato
- [ ] B2: Emergency Change documentato retroattivamente in GLPI
- [ ] B3: Modello Standard Change SC-IAM-001 creato e salvato
- [ ] B4: Script `release_pipeline.sh` eseguito con successo per v2.3.0
- [ ] B4: Smoke test post-deploy: versione e health check OK
- [ ] B4: Checklist Go/No-Go compilata
- [ ] B5: Report Access Review generato con utenti classificati
- [ ] B5: Account inattivi identificati e azione documentata
- [ ] B6: Script `decommission_check.sh` eseguito per asset di test
- [ ] B6: CI aggiornato a "Dismesso" in GLPI

**Parte C — Sistematizzazione:**
- [ ] C1: Script `change_kpi.py` produce report KPI con valori reali da GLPI
- [ ] C2: Script `maintenance_calendar.sh` mostra prossime finestre manutenzione
- [ ] C3: Script `change_cmdb_sync.py` aggiorna CI e aggiunge nota al change

---

## Appendice A: Flusso Normal Change — Diagramma Completo

```
RFC Registrata
     │
     ▼
Valutazione Change Manager
     │
     ├── Info insufficienti → Richiedere integrazioni
     │
     ▼
Classificazione Rischio/Impatto
     │
     ├── Basso → Approvazione Change Manager
     ├── Medio → Change Manager + Tech Lead
     ├── Alto  → CAB (riunione settimanale)
     └── Critico → CAB + IT Director + Business Owner
     │
     ▼ (se approvata)
Pianificazione Implementazione
  - Finestra di manutenzione confermata
  - Backup/snapshot pianificato
  - Comunicazione stakeholder
  - Risorse disponibili verificate
     │
     ▼
IMPLEMENTAZIONE (nella finestra approvata)
  1. Comunicare inizio manutenzione
  2. Eseguire backup/snapshot
  3. Eseguire la modifica (piano RFC)
  4. Verifiche post-implementazione
     │
     ├── FALLIMENTO → ROLLBACK IMMEDIATO → Analisi causa
     │
     └── SUCCESSO ──────────────────────────────────────┐
                                                        │
     ▼                                                  │
Post-Implementation Review (PIR)  ◄────────────────────┘
  - Monitoraggio "baking time" (24-72h)
  - Aggiornamento CMDB
  - Chiusura RFC con esito
  - Lessons learned (per change con problemi)
```

---

## Appendice B: KPI del Processo Change Enablement

| KPI | Target | Come si misura |
|---|---|---|
| **Change Success Rate** | ≥ 95% | (Change completati / Change totali) × 100 |
| **Emergency Change Ratio** | ≤ 5% | (Emergency change / Change totali) × 100 |
| **Failed Change Rate** | ≤ 2% | (Change che causano incidenti / totali) × 100 |
| **Tempo medio approvazione RFC** | ≤ 3 gg lavorativi | Date approvazione - Date sottomissione |
| **PIR completata per change High/Critical** | 100% | Verifica nel sistema ITSM |
| **Backlog RFC non processate** | ≤ 10 | Count RFC in stato "Registrata" > 5 giorni |

**Regola pratica**: se il Failed Change Rate supera il 2%, fare una review dei change degli ultimi 30 giorni e cercare pattern comuni (stesso tipo di change, stesso tecnico, stessa finestra oraria, stesso sistema).

---

## Appendice C: Confronto tra Strategie di Deployment

| Strategia | Come funziona | Rischio | Rollback | Caso d'uso |
|---|---|---|---|---|
| **Big Bang** | Deploy tutto su tutti i server contemporaneamente | Alto | Difficile, richiede rollback completo | Applicazioni monolitiche a basso traffico |
| **Rolling** | Un server alla volta nel pool, graduale | Medio | Fermare il rolling, versioni miste per un po' | API stateless, microservizi |
| **Blue/Green** | Due ambienti identici, switch del traffico | Basso | Istantaneo (switch indietro) | Applicazioni critiche, zero-downtime |
| **Canary** | 5-10% del traffico sul nuovo, espandere se OK | Molto basso | Reindirizzare 100% alla versione stabile | Grandi applicazioni consumer |
| **Feature Flag** | Deploy disabilitato, attivare via flag | Minimo | Disabilitare il flag | Funzionalità sperimentali, A/B testing |

---

## Appendice D: Integrazione Change Management con ITIL 4

| Pratica ITIL 4 | Relazione con Change Management |
|---|---|
| **Incident Management** | Il 60-80% degli incidenti deriva da change mal gestiti → tracciare "change correlato" nei ticket incidente |
| **Problem Management** | Change ripetutamente falliti → aprire problem per trovare la root cause |
| **Service Level Management** | Change nelle finestre di manutenzione protegge gli SLA → SLA che vietano change fuori finestra |
| **Configuration Management** | Ogni change deve aggiornare il CMDB come post-action obbligatoria |
| **Release Management** | Release = orchestrazione di più change → coordinare RFC e release plan |
| **Knowledge Management** | PIR post-change → aggiornare knowledge base con lessons learned |

---

## Riferimenti

- `09-procedure-operative.md` — Documento sorgente: SOP-CHG-001, SOP-REL-001, SOP-SRF-001, SOP-IAM-006, SOP-AST-001
- `tutorial_ops09_ch1a_sop_runbook_creation_lab.md` — SOP/Runbook base (prerequisito)
- `tutorial_ops08_ch1b_cmdb_implementation_lab.md` — CMDB per tracciare CI e relazioni
- `tutorial_ops07_ch1b_incident_management_lab.md` — Incidente management correlato
- ITIL 4 Practice Guide: Change Enablement
- ITIL 4 Practice Guide: Release Management
- ISO/IEC 20000-1 — IT Service Management
- GDPR Art. 5, 32 — Protezione dati e access review
