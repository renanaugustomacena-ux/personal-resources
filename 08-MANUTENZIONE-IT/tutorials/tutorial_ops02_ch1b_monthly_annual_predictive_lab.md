# Tutorial: Manutenzione Preventiva — Cicli Mensili, Trimestrali, Annuali e Manutenzione Predittiva — Hands-On Lab

> **Documento di riferimento:** `02-manutenzione-preventiva.md` (sezioni 4-8)
> **Dominio:** Manutenzione Preventiva
> **Ambito:** Patching mensile, restore test, DR drill trimestrale, analisi SMART, capacity planning, maintenance windows
> **Durata lab:** 4-5 ore (distribuibili in più sessioni)
> **Livello:** Intermedio — richiede conoscenza del lab base e dei cicli giornalieri/settimanali
> **Prerequisiti:** `tutorial_ops00` (lab), `tutorial_ops01_ch1a` (ITIL), `tutorial_ops02_ch1a` (manutenzione giornaliera/settimanale)
> **Ambiente:** Lab isolato — DC-LAB-01, SRV-LINUX-01, WKS-LAB-01 tutti accesi e funzionanti

---

## Lab Environment Setup

Il lab è già configurato dai tutorial precedenti. Per questo tutorial useremo:
- DC-LAB-01: ciclo di patching Windows, WSUS, analisi log mensile
- SRV-LINUX-01: apt upgrade gestito, analisi SMART, cron mensile
- WKS-LAB-01: browser per GLPI (change request patching)

**Prerequisito specifico:** GLPI deve essere funzionante su SRV-LINUX-01 (Esercizio B2 del tutorial ops01a).

---

## PART A: FONDAMENTI — I Cicli di Manutenzione a Lungo Termine

> La manutenzione giornaliera è come spazzare il pavimento — necessaria ma non sufficiente. La manutenzione mensile è come pulire le finestre. Quella trimestrale è come riverniciare le pareti. Quella annuale è come rifare l'impianto elettrico. Ognuno ha la sua frequenza, la sua complessità, e il suo impatto se trascurata.

---

### Concetto A1: Il Ciclo di Patching — L'Operazione più Importante e più Pericolosa

> **Analogia.** Immagina di dover vaccinare 300 persone contro l'influenza. Se aspetti fino all'epidemia, è troppo tardi. Se vaccini tutti in un solo giorno senza preparazione, qualcuno potrebbe avere una reazione avversa e non hai il personale medico per gestirla. La soluzione è un programma vaccinale: prima i più vulnerabili, poi gli altri, con monitoraggio post-vaccinazione. Il patching IT funziona esattamente così.

**Perché il patching è rischioso nonostante sia necessario?**

Ogni patch modifica il codice di un sistema che funziona. Le patch:
- Chiudono vulnerabilità di sicurezza (necessario)
- Correggono bug (positivo)
- Aggiungono funzionalità (potenziale incompatibilità)
- **Possono rompere applicazioni** che dipendevano dal comportamento precedente (rischio reale)

Esempi storici reali:
- CrowdStrike July 2024: un aggiornamento del sensore EDR ha mandato offline 8.5 milioni di computer Windows in tutto il mondo
- KB5001404 Windows (2021): patch che rompeva i DC Active Directory
- OpenSSL 1.1.1 → 3.0 (2022): upgrade che ha rotto applicazioni che usavano API deprecate

**Il ciclo di patching sicuro in 4 fasi:**

```
FASE 1: RICEZIONE (settimana 1 del mese)
  - Microsoft Patch Tuesday: secondo martedì del mese
  - CVE database review: priorità per CVSS score > 7.5
  - WSUS / apt cache aggiornate automaticamente
  
FASE 2: TEST (settimana 1-2)
  - Deploy su ambiente di test/staging (non produzione)
  - Verifica funzionalità critiche post-patch
  - Test regressione: le applicazioni chiave funzionano ancora?
  - Documentazione: quale patch ha causato quale comportamento?
  
FASE 3: APPROVAZIONE E COMUNICAZIONE (settimana 2)
  - RFC (Request for Change) in GLPI
  - Approvazione del Change Advisory Board (CAB meeting)
  - Comunicazione agli utenti: "sabato dalle 23:00 alle 03:00 manutenzione"
  - Snapshot/backup di tutte le VM prima della maintenance window
  
FASE 4: DEPLOYMENT E VERIFICA (maintenance window)
  - Deploy in produzione
  - Verifica post-deployment: tutti i servizi up, applicazioni funzionanti
  - Attivazione periodo di osservazione: 48-72h di monitoring intensificato
  - Rollback immediato se problemi critici rilevati entro 72h
```

**Classificazione priorità patch:**

| Categoria | Tempo massimo deploy | Esempio |
|---|---|---|
| **Critical Security** (CVSS ≥ 9.0) | 72 ore (emergency patch, salto staging) | Log4Shell, EternalBlue |
| **High Security** (CVSS 7.0-8.9) | 7 giorni | RCE su servizi esposti |
| **Medium Security** (CVSS 4.0-6.9) | Ciclo mensile normale | Privilege escalation locale |
| **Low Security / Bug Fix** | Ciclo mensile o trimestrale | Correzioni minor, UX fix |

---

### Concetto A2: Il Test di Restore — Il Controllo più Trascurato

> **Analogia.** Hai mai notato che quasi nessuno testa le vie di fuga in caso di incendio? Tutti sanno dove sono le uscite di emergenza sulla carta, ma pochi le hanno mai usate davvero. Quando scoppia un incendio, si scopre che alcune porte sono bloccate, le scale di emergenza sono piene di materiale, e nessuno ricorda il percorso. Il backup senza restore test è esattamente così: sai che esiste, ma non sai se funziona quando serve.

**La statistica più importante del backup:**

Secondo diverse ricerche di settore (Veeam, Acronis):
- 77% delle aziende ha avuto almeno un fallimento di backup nell'ultimo anno
- 50% di chi ha tentato un restore completo ha riscontrato problemi
- Solo il 26% delle aziende testa regolarmente il restore

**Cosa testare nel restore mensile:**

Non testare tutto ogni mese — ruota:

```
Gennaio:    Restore di una singola VM (DC-LAB-01)
Febbraio:   Restore di un singolo file/cartella da VM2
Marzo:      Restore di un database (es. database GLPI)
Aprile:     Restore di uno share di rete
Maggio:     DR parziale: restore di DC-LAB-01 in VirtualBox su altra porta IP
Giugno:     Full restore di una workstation
Luglio:     → ricomincia il ciclo
```

**Metriche da misurare durante ogni restore test:**

| Metrica | Definizione | Come misurare |
|---|---|---|
| **RTO Effettivo** | Tempo dal disastro alla ripresa del servizio | Cronometro: dal momento del "disastro simulato" all'utente che può tornare a lavorare |
| **RPO Effettivo** | Quanti dati persi nell'ultimo backup prima del "disastro" | Data e ora del backup usato per il restore |
| **Integrità dati** | I dati ripristinati sono corretti e completi? | Verifica checksum, test applicazione, query DB |
| **Success rate** | % di restore completati senza problemi | Storico mensile su 12 mesi |

**La regola 3-2-1-1-0:**

```
3 copie dei dati (1 primaria + 2 backup)
2 tipi di media diversi (es. disco locale + nastro/cloud)
1 copia offsite (fuori dal datacenter)
1 copia air-gapped (disconnessa dalla rete — protezione ransomware)
0 errori verificati nell'ultimo restore test
```

La "0" finale è la parte più importante — un backup non verificato non conta.

---

### Concetto A3: Manutenzione Predittiva — Leggere i Segnali Prima del Guasto

> **Analogia.** Un meccanico esperto ascolta il motore di un'auto mentre la guida. Sente un clic metallico ogni 30 secondi e dice "tra 2 settimane ti si romperà il cuscinetto anteriore sinistro". Non aspetta che la ruota si stacchi. Usa i segnali deboli per prevenire il guasto catastrofico. La manutenzione predittiva IT fa la stessa cosa con i dati SMART, le temperature e i contatori di errore.

**I 4 sensori predittivi più importanti:**

**1. Dati SMART dei dischi (Self-Monitoring, Analysis and Reporting Technology)**

I dischi meccanici e SSD espongono centinaia di parametri di salute. I più critici:

| Attributo SMART | Cosa misura | Segnale di pericolo |
|---|---|---|
| Reallocated Sectors Count | Settori riallocati (difetti superficiali compensati) | Qualsiasi valore > 0 (dischi meccanici) |
| Pending Sector Count | Settori in attesa di riallocazione | Qualsiasi valore > 0 |
| Uncorrectable Sector Count | Errori non correggibili | Qualsiasi valore > 0 — sostituire immediatamente |
| SSD Lifetime Used (% Media Wearout) | Vita residua SSD | < 20% = pianificare sostituzione |
| Spin Retry Count | Quante volte il disco ha avuto difficoltà ad avviarsi | > 0 = pericolo imminente |
| Temperature Celsius | Temperatura operativa | HDD: > 55°C critico; SSD: > 70°C critico |

**2. Temperature CPU e Chassis**

Le CPU moderne hanno protezioni termiche (throttling, shutdown automatico), ma il danno da calore è cumulativo nel tempo — accelera l'invecchiamento dei condensatori e della pasta termale.

Soglie tipiche:
- CPU: idle < 40°C / carico normale < 75°C / CRITICO > 90°C
- Chassis inlet: < 25°C ideale / > 35°C richiede intervento raffrescamento
- RAM: < 45°C normale / > 60°C critico

**3. Errori ECC della RAM (Error Correcting Code)**

La RAM ECC (presente nei server, non nei PC consumer) corregge automaticamente gli errori a singolo bit ma registra quanti ne corregge. Un aumento del tasso di correzioni indica RAM che si sta degradando.

**4. NIC errors e interface flapping**

Interfacce di rete che vanno up/down frequentemente o che mostrano elevati counter di errori CRC indicano problemi fisici: cavo difettoso, porta switch difettosa, NIC che si sta degradando.

---

### Concetto A4: Le Maintenance Windows — Come si Gestisce un Downtime Pianificato

> **Analogia.** Un ospedale non può permettersi di fare manutenzione alla sala operatoria mentre c'è un intervento in corso. Pianifica la manutenzione in slot notturni, tiene una sala di backup disponibile durante i lavori, e comunica in anticipo ai chirurghi. L'IT aziendale ha le stesse esigenze: non puoi aggiornare l'ERP mentre i commerciali stanno inserendo ordini.

**Elementi essenziali di una maintenance window:**

| Elemento | Perché è obbligatorio |
|---|---|
| Data/ora di inizio e fine | Gli utenti devono sapere quando tornerà disponibile il servizio |
| Sistemi coinvolti | Permette a chi non è impattato di continuare a lavorare |
| Impatto atteso | "ERP non disponibile" vs "solo rallentamento login" — impatto molto diverso |
| Piano di rollback | Cosa fare se l'aggiornamento fallisce a metà |
| Criteri go/no-go | A che punto si decide di procedere vs posticipare |
| Persona di riferimento | Chi contattare durante la maintenance |

**Template comunicazione maintenance window:**

```
OGGETTO: [MANUTENZIONE PROGRAMMATA] ERP Aziendale — Sabato 20 luglio 22:00-02:00

Gentili colleghi,

vi comunichiamo che sabato 20 luglio 2026 dalle 22:00 alle 02:00 (domenica)
eseguiremo un intervento di manutenzione programmata sul sistema ERP.

SISTEMI NON DISPONIBILI:
- Modulo gestione ordini
- Modulo contabilità
- Reportistica

SISTEMI DISPONIBILI:
- Email aziendale
- SharePoint / Teams
- Tutti gli altri sistemi

IMPATTO: nessuna vendita/ordine inseribile durante la finestra.
RACCOMANDAZIONE: completare gli ordini urgenti entro venerdì 19 luglio ore 20:00.

In caso di problemi urgenti durante la manutenzione, contattare:
[nome tecnico] — tel. +39 XXX XXX XXXX

Ci scusiamo per il disagio.
Team IT
```

**Change Freeze — Quando NON fare manutenzione:**

Alcune periodi dell'anno richiedono il congelamento di qualsiasi modifica:
- Chiusura fiscale di anno / trimestre (dicembre, marzo, giugno, settembre)
- Picchi stagionali di business (Black Friday per e-commerce, estate per turismo)
- Audit esterni / certificazioni (ISO, SOC 2)
- Periodi di rilascio prodotto

Il change freeze deve essere pianificato a inizio anno e comunicato all'IT team.

---

## PART B: OPERAZIONI — Implementare i Cicli di Manutenzione a Lungo Termine

---

### Esercizio B1: Ciclo di Patching Mensile su DC-LAB-01

**Obiettivo.** Simulare il ciclo completo di patching su DC-LAB-01 (Windows Server 2022): verifica aggiornamenti disponibili, creazione change request, applicazione patch, verifica post-patching.

**Step 1 — Aprire il Change Request in GLPI prima del patching**

Da WKS-LAB-01, accedi a GLPI (`http://192.168.56.20:8080/`) come `it-admin`:

Helpdesk → Changes → Add:

| Campo | Valore |
|---|---|
| Tipo | Change Normal |
| Categoria | Infrastruttura → Server → Patching |
| Titolo | "Patching mensile luglio 2026 — DC-LAB-01" |
| Urgenza | Bassa |
| Impatto | Medio |
| Descrizione | "Applicazione patch di sicurezza Microsoft Patch Tuesday luglio 2026. Sistemi coinvolti: DC-LAB-01. Finestra: sabato 20 luglio 22:00-01:00. Impatto: riavvio server, max 30 minuti di interruzione AD/DNS/DHCP." |
| Data implementazione | [data futura] ore 22:00 |
| Piano di rollback | "Ripristino snapshot VirtualBox 'Pre-Patch-2026-07' entro 15 minuti" |

**Step 2 — Snapshot pre-patching (OBBLIGATORIO)**

Prima di qualsiasi patching in produzione, fai uno snapshot. Nel lab, fai questo dalla VM DC-LAB-01 spenta:

VirtualBox → DC-LAB-01 → Machine → Take Snapshot:
- Nome: `Pre-Patch-2026-07`
- Descrizione: `Snapshot pre-patching mensile luglio 2026`

**Step 3 — Verificare gli aggiornamenti disponibili (DC-LAB-01)**

```powershell
# Installa il modulo PSWindowsUpdate se non presente
Install-Module PSWindowsUpdate -Force -Scope CurrentUser

# Elenca aggiornamenti disponibili (senza installarli)
Get-WindowsUpdate -AcceptAll -Verbose | 
    Select-Object Title, Size, MsrcSeverity, IsDownloaded |
    Format-Table -AutoSize
```

Output tipico:
```
Title                                    Size    MsrcSeverity IsDownloaded
-----                                    ----    ------------ ------------
2024-07 Cumulative Update for Win...     450 MB  Critical     False
Windows Malicious Software Removal...    1.2 MB  None         False
```

**Step 4 — Download degli aggiornamenti (senza installare)**

```powershell
# Scarica gli aggiornamenti in cache senza installarli
Get-WindowsUpdate -AcceptAll -Download -Verbose

Write-Host "Download completato. Pronto per l'installazione durante maintenance window."
```

**Step 5 — Installare le patch (durante maintenance window)**

```powershell
# Registra ora di inizio
$startTime = Get-Date
Write-Host "Patching iniziato: $($startTime.ToString('HH:mm:ss'))"

# Installa tutti gli aggiornamenti e riavvia se necessario
Install-WindowsUpdate -AcceptAll -AutoReboot -Verbose

# Dopo il riavvio, verifica gli aggiornamenti installati
Get-WinEvent -FilterHashtable @{LogName='System'; Id=19; StartTime=(Get-Date).AddHours(-2)} |
    Select-Object TimeCreated, Message -First 10
```

**Step 6 — Verifica post-patching**

```powershell
# Verifica che i servizi critici siano tutti Running
$svcs = @("ADWS","DNS","DHCPServer","Netlogon","W32Time")
foreach ($s in $svcs) {
    $svc = Get-Service -Name $s -ErrorAction SilentlyContinue
    if ($svc.Status -eq "Running") {
        Write-Host "[ OK] $s: Running" -ForegroundColor Green
    } else {
        Write-Host "[ERR] $s: $($svc.Status)" -ForegroundColor Red
    }
}

# Verifica aggiornamenti installati correttamente
$endTime = Get-Date
Write-Host "`nPatching completato: $($endTime.ToString('HH:mm:ss'))"
Write-Host "Durata: $([math]::Round(($endTime-$startTime).TotalMinutes,0)) minuti"

# Elenca patch installate oggi
Get-HotFix | Where-Object {$_.InstalledOn -ge (Get-Date).Date} | 
    Select-Object HotFixID, Description, InstalledOn
```

**Step 7 — Chiudi il Change Request in GLPI**

Torna in GLPI → apri il Change creato in Step 1 → aggiorna:
- Stato: Completato
- Commento finale: "Patching completato alle [ora]. X patch installate. Tutti i servizi verificati e funzionanti. Nessuna anomalia riscontrata."

**Checkpoint B1:**
- [ ] Change request creato e approvato in GLPI prima del patching
- [ ] Snapshot pre-patching creato in VirtualBox
- [ ] Aggiornamenti installati senza errori
- [ ] Verifica post-patching: tutti i servizi AD, DNS, DHCP, Netlogon in Running
- [ ] Change request chiuso in GLPI con documentazione dell'esito

---

### Esercizio B2: Ciclo di Patching Mensile su SRV-LINUX-01 (apt)

**Obiettivo.** Implementare il patching Ubuntu sicuro con gestione snapshot e verifica post-upgrade.

```bash
# Su SRV-LINUX-01 — PRIMA del patching
# Crea snapshot VirtualBox (fai da VirtualBox con VM spenta):
# Nome: Pre-Apt-Upgrade-2026-07

# Connettiti via SSH
ssh lab-admin@192.168.56.20

# Step 1: Verifica aggiornamenti disponibili
sudo apt-get update
apt list --upgradable 2>/dev/null

# Step 2: Aggiornamenti di sicurezza urgenti (senza reboot)
sudo apt-get install -y unattended-upgrades
sudo unattended-upgrade --dry-run -d  # preview

# Step 3: Full upgrade (durante maintenance window)
# Registra lo stato pre-upgrade
dpkg -l | grep "^ii" | wc -l > /tmp/pkg_count_pre.txt

# Esegui l'upgrade
sudo apt-get upgrade -y 2>&1 | tee /tmp/apt_upgrade_$(date +%Y%m%d).log

# Step 4: Autoremove pacchetti non necessari
sudo apt-get autoremove -y
sudo apt-get autoclean

# Step 5: Verifica post-upgrade
echo "=== VERIFICA POST-UPGRADE ==="

# Container GLPI ancora funzionante?
docker compose -f ~/glpi-lab/docker-compose.yml ps

# Servizi critici?
for svc in ssh docker systemd-networkd; do
    status=$(systemctl is-active "$svc")
    if [ "$status" = "active" ]; then
        echo "[ OK] $svc: $status"
    else
        echo "[ERR] $svc: $status"
    fi
done

# Kernel aggiornato? (richiede riavvio per applicarsi)
uname -r
apt list --upgradable 2>/dev/null | grep linux-image

# Step 6: Riavvio se necessario (durante maintenance window)
if [ -f /var/run/reboot-required ]; then
    echo "[REBOOT] Riavvio richiesto per applicare kernel aggiornato"
    echo "Pianifica riavvio durante la maintenance window: sudo reboot"
else
    echo "[ OK] Nessun riavvio richiesto"
fi
```

**Checkpoint B2:**
- [ ] `apt list --upgradable` non mostra più pacchetti pendenti dopo l'upgrade
- [ ] Container GLPI in stato `running` dopo upgrade
- [ ] Log dell'upgrade salvato in `/tmp/apt_upgrade_YYYYMMDD.log`

---

### Esercizio B3: Test di Restore — Verificare che il Backup Funziona

**Obiettivo.** Eseguire un test di restore controllato su SRV-LINUX-01 usando gli snapshot VirtualBox, simulando il ripristino dopo un guasto.

**Scenario simulato:** SRV-LINUX-01 ha subito un guasto dopo l'installazione di un pacchetto errato. Devi ripristinare allo snapshot `0.1 - Setup Base Completato`.

**Step 1 — Simulare il "danno"**

```bash
# Su SRV-LINUX-01 — crea un file di test che "sparirà" dopo il restore
echo "Questo file rappresenta dati creati DOPO il backup" > ~/test_restore_$(date +%Y%m%d).txt
ls ~/test_restore_*.txt
```

Nota la data e ora corrente: questo diventerà il tuo RPO.

**Step 2 — Arrestare la VM**

Dalla VM SRV-LINUX-01:
```bash
sudo shutdown -h now
```

**Step 3 — Ripristinare lo snapshot in VirtualBox**

VirtualBox → SRV-LINUX-01 → Machine → Snapshots:
1. Seleziona `0.1 - Setup Base Completato`
2. Clicca **Restore**
3. Al messaggio di conferma: scegli "No" (non fare snapshot dello stato corrente)
4. Avvia la VM ripristinata

**Step 4 — Verifica del restore**

```bash
# Dopo login nella VM ripristinata
ssh lab-admin@192.168.56.20

# Il file di test deve essere SPARITO (era stato creato dopo lo snapshot)
ls ~/test_restore_*.txt 2>/dev/null && echo "PROBLEMA: file presente!" || echo "OK: file assente (restore corretto)"

# Verifica IP e servizi
ip addr show enp0s8 | grep "192.168.56.20"
systemctl is-active ssh
docker compose -f ~/glpi-lab/docker-compose.yml ps
```

**Step 5 — Calcola RTO e RPO effettivi e documentali in GLPI**

Apri GLPI → Gestione → Problemi → Add (tipo "Problem" per documentare):

```
Titolo: "TEST RESTORE MENSILE - SRV-LINUX-01 - Luglio 2026"
Tipo: Mantenimento (non è un vero problema)

Risultati:
- RTO effettivo: [tempo dal momento del "guasto" al servizio ripristinato]
  Misurato: spegnimento VM (02:30) → snapshot restore (02:33) → VM avviata e servizi up (02:38)
  RTO: 8 minuti
- RPO effettivo: [data snapshot] → dati creati dopo quella data PERSI
  In questo scenario, l'RPO è la data dello snapshot "0.1 - Setup Base Completato"
- Integrità: OK (servizi funzionanti, nessun dato corrotto)
- Anomalie: nessuna
- Azioni: il restore test è andato bene.
  NOTA: In produzione reale, RPO di diversi mesi è inaccettabile.
  Per il lab reale useremo backup giornalieri (tutorial ops06).
```

**Checkpoint B3:**
- [ ] Snapshot ripristinato correttamente (file di test sparito)
- [ ] Servizi (SSH, Docker, GLPI) funzionanti dopo il restore
- [ ] IP 192.168.56.20 ancora assegnato dopo il restore
- [ ] RTO e RPO documentati in GLPI (o file markdown)

---

### Esercizio B4: Analisi SMART dei Dischi Virtuali

**Obiettivo.** Anche nel lab virtuale, possiamo imparare a leggere i dati SMART dei dischi. In un ambiente reale, questi dati sono fondamentali per prevenire la perdita di dati.

> Nota: I dischi virtuali VirtualBox non espongono i dati SMART reali del disco fisico sottostante. Installeremo smartmontools e analizzeremo i dati disponibili — in un ambiente reale, questi dati vengono dal disco fisico.

```bash
# Su SRV-LINUX-01
sudo apt-get install -y smartmontools

# Lista i dischi disponibili
sudo smartctl --scan

# Output tipico con VirtualBox:
# /dev/sda -d sat # /dev/sda, ATA device (o simile)

# Analisi SMART del disco principale
sudo smartctl -a /dev/sda
```

Output tipico:
```
smartctl 7.3 2022-02-28 r5338 [x86_64-linux-5.15.0-117-generic] (local build)
Copyright (C) 2002-22, Bruce Allen, Christian Franke, www.smartmontools.org

=== START OF INFORMATION SECTION ===
Device Model:     VBOX HARDDISK
Serial Number:    VBxxxx-xxxx
...
SMART overall-health self-assessment test result: PASSED
```

**Simula l'analisi di un disco reale con dati SMART preoccupanti:**

```bash
# Crea un file di esempio con dati SMART simulati di un disco degradato
cat > /tmp/smart_example_bad.txt << 'SMART_EOF'
# Esempio dati SMART preoccupanti (dati SIMULATI per esercizio didattico)
ID  ATTRIBUTE_NAME          VALUE  WORST  THRESH  TYPE       WHEN_FAILED  RAW_VALUE
  5 Reallocated_Sector_Ct   100    100     10     Pre-fail   -            87
196 Reallocated_Event_Count  99     99     0      Old_age    -            87
197 Current_Pending_Sector   100    100     0      Old_age    -            3
198 Offline_Uncorrectable    100    100     0      Old_age    -            0
199 UDMA_CRC_Error_Count     200    200     0      Old_age    -            0
SMART_EOF

echo "=== ANALISI DATI SMART SIMULATI ==="
echo ""
echo "Interpretazione dei valori critici trovati:"
echo ""
echo "Reallocated_Sector_Ct = 87"
echo "  → CRITICO: 87 settori hanno avuto difetti fisici e sono stati riallocati"
echo "  → Azione: pianificare sostituzione IMMEDIATA del disco"
echo "  → Backup urgente se non già presente"
echo ""
echo "Current_Pending_Sector = 3"
echo "  → CRITICO: 3 settori in attesa di verifica di riallocazione"
echo "  → Indica settori fisicamente danneggiati che non rispondono correttamente"
echo "  → Rischio perdita dati IMMINENTE"
echo ""
echo "DECISIONE: Sostituire il disco entro 24-48 ore."
echo "Prima: backup completo verificato. Poi: sostituzione in maintenance window."
```

**Script di monitoring SMART automatizzato:**

```bash
cat > ~/scripts/smart_monitor.sh << 'SMART_SCRIPT'
#!/bin/bash
# smart_monitor.sh - Verifica settimanale salute dischi
LOG="$HOME/maint-logs/smart_$(date +%Y-%m-%d).log"
ISSUES=()

echo "=== SMART DISK CHECK $(date) ===" | tee -a "$LOG"

for disk in $(smartctl --scan | awk '{print $1}'); do
    echo "--- Disco: $disk ---" | tee -a "$LOG"
    
    health=$(sudo smartctl -H "$disk" 2>/dev/null | grep "overall-health" | awk '{print $NF}')
    
    if [ "$health" = "PASSED" ]; then
        echo "[ OK] $disk: SMART health PASSED" | tee -a "$LOG"
    else
        echo "[WARN] $disk: SMART health = $health" | tee -a "$LOG"
        ISSUES+=("$disk: SMART health = $health")
    fi
    
    # Verifica attributi critici
    for attr in 5 196 197 198; do
        raw=$(sudo smartctl -A "$disk" 2>/dev/null | awk -v id="$attr" '$1==id{print $NF}')
        if [ -n "$raw" ] && [ "$raw" != "0" ]; then
            echo "[WARN] $disk: SMART attributo $attr = $raw (> 0)" | tee -a "$LOG"
            ISSUES+=("$disk: attributo SMART $attr = $raw")
        fi
    done
done

if [ ${#ISSUES[@]} -gt 0 ]; then
    echo "ATTENZIONE: ${#ISSUES[@]} problemi SMART rilevati — backup e sostituzione pianificata"
fi
SMART_SCRIPT

chmod +x ~/scripts/smart_monitor.sh
~/scripts/smart_monitor.sh
```

**Checkpoint B4:**
- [ ] `smartmontools` installato su SRV-LINUX-01
- [ ] `smartctl -a /dev/sda` eseguito e output letto
- [ ] Sai interpretare i 5 attributi SMART critici
- [ ] Script `smart_monitor.sh` creato e funzionante

---

### Esercizio B5: DR Drill Trimestrale — Piano e Simulazione

**Obiettivo.** Pianificare e parzialmente simulare un DR (Disaster Recovery) drill — l'esercitazione trimestrale che verifica che il piano di ripristino funzioni davvero.

**Perché il DR drill è diverso dal restore test mensile?**

| Restore test mensile | DR drill trimestrale |
|---|---|
| Un singolo sistema ripristinato | L'intera infrastruttura critica ripristinata |
| Ambiente isolato, parallelo | Simula l'indisponibilità del sistema principale |
| 30-60 minuti | 4-8 ore |
| Solo team tecnico IT | Coinvolge management, utenti chiave, fornitori |
| Misura integrità backup | Misura RTO e RPO dell'intera organizzazione |

**Template Piano DR Drill:**

Crea il file `dr_drill_plan_Q3_2026.md`:

```markdown
# Piano DR Drill Q3 2026 — Lab IT Corporation

**Data:** Sabato 19 Luglio 2026, 09:00-17:00  
**Coordinatore:** [tuo nome]  
**Obiettivo:** Verificare ripristino completo del lab in <2 ore  

---

## 1. Scenario di Disastro Simulato

"Alle 08:00 di sabato mattina, un incendio nella sala server ha reso 
inaccessibili tutti i sistemi fisici. Le VM sono su backup offsite. 
Dobbiamo ripristinare l'intera infrastruttura su hardware alternativo 
(un altro PC con VirtualBox installato) entro le 10:00."

---

## 2. Sistemi da Ripristinare (in ordine)

| Priorità | Sistema | RTO Target | Responsabile |
|---|---|---|---|
| 1 | DC-LAB-01 (AD/DNS/DHCP) | 30 min | [tech1] |
| 2 | SRV-LINUX-01 (GLPI ticketing) | 45 min | [tech1] |
| 3 | WKS-LAB-01 (workstation admin) | 20 min | [tech2] |

---

## 3. Risorse Necessarie

- PC alternativo con VirtualBox installato e 16GB RAM
- Backup delle VM (snapshot esportati in formato OVA o file VDI)
- Media: USB drive da 128GB con i backup
- Documenti: procedure di ripristino (questo file)
- Accesso: credenziali di tutti i sistemi stampate e custodite fisicamente

---

## 4. Runbook di Ripristino (step-by-step)

### DC-LAB-01
1. Importa il file OVA di DC-LAB-01 in VirtualBox sul PC alternativo
2. Configura la rete host-only (192.168.56.0/24)
3. Avvia la VM
4. Verifica: ping 192.168.56.10 da WKS-LAB-01
5. Verifica: accesso AD con Administrator / Lab@2024!
6. Documenta RTO effettivo

### SRV-LINUX-01
[stessa struttura...]

---

## 5. Criteri di Successo/Fallimento

| Criterio | Pass | Fail |
|---|---|---|
| DC-LAB-01 operativo | < 30 min | > 30 min o non raggiungibile |
| GLPI accessibile | < 45 min | > 45 min o errori DB |
| Tutti i servizi verificati | < 2 ore totali | > 2 ore |

---

## 6. Lessons Learned (dopo il drill)

[Da compilare durante il debrief post-drill]
- Cosa ha funzionato bene:
- Cosa ha rallentato il ripristino:
- Azioni correttive per il prossimo drill:
```

**Simulazione semplificata nel lab:**

```powershell
# Esporta DC-LAB-01 come OVA (backup portatile) da WKS-LAB-01 PowerShell
# Nota: richiede che DC-LAB-01 sia SPENTA

# Alternativa con VBoxManage (tool da riga di comando VirtualBox)
$vboxManage = "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe"
$exportPath = "C:\Lab\Backups\DC-LAB-01.ova"

& $vboxManage export "DC-LAB-01" --output $exportPath --ovf20
Write-Host "Export completato: $exportPath"
Get-Item $exportPath | Select-Object Name, @{N="Size(GB)";E={[math]::Round($_.Length/1GB,2)}}
```

**Checkpoint B5:**
- [ ] Documento `dr_drill_plan_Q3_2026.md` creato con tutti i campi compilati
- [ ] Hai identificato quali sistemi ripristinare in quale ordine e perché
- [ ] Sai calcolare i criteri go/no-go per un drill
- [ ] (Opzionale) Export OVA di DC-LAB-01 completato

---

### Esercizio B6: Analisi Mensile delle Capacity Trends

**Obiettivo.** Creare una baseline mensile delle risorse e identificare tendenze di crescita che potrebbero richiedere intervento prima che diventino problemi.

**Script Python per analisi trend (su WKS-LAB-01 o SRV-LINUX-01):**

```python
#!/usr/bin/env python3
"""
capacity_trend.py
Analizza trend di crescita delle risorse dal log di monitoring
e proietta quando si raggiungeranno le soglie critiche.
"""

from datetime import datetime, timedelta
import json

# Dati simulati storici (in produzione, questi vengono da Zabbix/Prometheus)
# Formato: (data, % disco usato, % RAM usata, carico CPU medio)
historic_data = [
    ("2026-01-01", 22.0, 35.0, 15.0),
    ("2026-02-01", 24.5, 36.2, 16.3),
    ("2026-03-01", 27.1, 37.8, 17.1),
    ("2026-04-01", 29.8, 39.5, 18.0),
    ("2026-05-01", 32.4, 41.2, 18.9),
    ("2026-06-01", 35.0, 43.0, 19.8),
    ("2026-07-01", 37.6, 44.8, 20.7),
]

# Soglie di allarme
DISK_WARN = 75.0
DISK_CRIT = 85.0
RAM_WARN  = 80.0

def linear_projection(data_points: list, threshold: float) -> str:
    """Proietta quando si raggiungerà una soglia dato un trend lineare."""
    if len(data_points) < 2:
        return "Dati insufficienti"
    
    # Calcola crescita mensile media (ultimi 3 mesi)
    recent = data_points[-3:]
    values = [d[1] for d in recent]
    avg_monthly_growth = (values[-1] - values[0]) / (len(values) - 1)
    
    if avg_monthly_growth <= 0:
        return "Stabile o in calo"
    
    current = values[-1]
    months_to_threshold = (threshold - current) / avg_monthly_growth
    projected_date = datetime.now() + timedelta(days=months_to_threshold * 30)
    return f"{months_to_threshold:.1f} mesi ({projected_date.strftime('%Y-%m')})"

print("\n" + "=" * 65)
print("  CAPACITY TREND REPORT — Luglio 2026")
print("  Analisi basata su ultimi 7 mesi di dati storici")
print("=" * 65)

# Trend disco
disk_data = [(d[0], d[1]) for d in historic_data]
disk_current = disk_data[-1][1]
disk_growth = disk_data[-1][1] - disk_data[-2][1]

print(f"\n[DISCO - DC-LAB-01 Volume C:]")
print(f"  Utilizzo corrente: {disk_current:.1f}%")
print(f"  Crescita mensile (ultimo mese): +{disk_growth:.1f}%")
print(f"  Proiezione soglia 75%: {linear_projection(disk_data, DISK_WARN)}")
print(f"  Proiezione soglia 85%: {linear_projection(disk_data, DISK_CRIT)}")
if disk_current > 70:
    print(f"  RACCOMANDAZIONE: pianificare espansione entro il prossimo mese")

# Trend RAM
ram_data = [(d[0], d[2]) for d in historic_data]
ram_current = ram_data[-1][1]
ram_growth = ram_data[-1][1] - ram_data[-2][1]

print(f"\n[RAM - SRV-LINUX-01:]")
print(f"  Utilizzo corrente: {ram_current:.1f}%")
print(f"  Crescita mensile: +{ram_growth:.1f}%")
print(f"  Proiezione soglia 80%: {linear_projection(ram_data, RAM_WARN)}")

print("\n" + "=" * 65)
print("  AZIONI PIANIFICATE:")
print("  1. Audit file grandi su DC-LAB-01 (disco al 37.6%)")
print("  2. Pianificare upgrade RAM SRV-LINUX-01 per Q4 2026 se trend confermato")
print("  3. Rivalutare tra 30 giorni")
print("=" * 65 + "\n")
```

**Checkpoint B6:**
- [ ] Script `capacity_trend.py` eseguito con output comprensibile
- [ ] Sai interpretare cosa significa "mesi alla soglia critica"
- [ ] Hai aggiornato la pianificazione: quando intervenire sul disco di DC-LAB-01?

---

## PART C: SISTEMATIZZARE — Governance del Programma di Manutenzione

---

### Progetto C1: Piano Annuale di Manutenzione

Crea il file `maintenance_plan_2026.md`:

```markdown
# Piano Annuale di Manutenzione IT — Lab IT Corporation 2026

**Versione:** 1.0 | **Data creazione:** 2026-01-01 | **Revisione prossima:** 2027-01-01

---

## Change Freeze Periods 2026

| Periodo | Motivazione |
|---|---|
| 28 dic 2025 - 7 gen 2026 | Chiusura anno fiscale |
| 25 mar - 1 apr 2026 | Chiusura Q1 |
| 24 giu - 1 lug 2026 | Chiusura semestrale |
| 23 set - 1 ott 2026 | Chiusura Q3 |
| 18 dic - 31 dic 2026 | Chiusura anno fiscale |

---

## Maintenance Windows Ricorrenti

| Tipo | Quando | Durata | Sistemi |
|---|---|---|---|
| Monthly Patch | Primo sabato del mese, 22:00 | 4 ore | Tutti |
| Quarterly DR Drill | Gen/Apr/Lug/Ott, prima domenica, 09:00 | 8 ore | Lab completo |
| Semi-annual Audit | Giugno e Dicembre | 2 giorni | Security + Asset |

---

## Calendario Interventi Pianificati 2026

| Mese | Intervento | Sistemi | Responsabile |
|---|---|---|---|
| Gennaio | Patch mensile + Audit accessi Q1 | Tutti | IT Ops |
| Febbraio | Patch mensile | Tutti | IT Ops |
| Marzo | Patch mensile + DR Drill Q1 | Lab completo | IT Lead |
| Aprile | Patch mensile + Review licenze | Tutti | IT Lead |
| Maggio | Patch mensile | Tutti | IT Ops |
| Giugno | Patch mensile + Security Assessment | Tutti + Security | IT Lead + CISO |
| Luglio | Patch mensile + DR Drill Q3 | Lab completo | IT Lead |
| Agosto | Patch mensile (ridotta: solo security) | Tutti | IT Ops |
| Settembre | Patch mensile + Review HW lifecycle | Tutti | IT Lead |
| Ottobre | Patch mensile + DR Drill Q4 | Lab completo | IT Lead |
| Novembre | Patch mensile + Capacity planning 2027 | Tutti | IT Lead |
| Dicembre | Patch mensile + Budget review + DR annuale | Lab completo | IT Lead + Management |
```

---

### Progetto C2: Template Post-Maintenance Review

Dopo ogni maintenance window significativa (mensile o superiore), compila questo template e salvalo in GLPI:

```markdown
# Post-Maintenance Review — [Data] [Tipo]

**Maintenance Window:** [data inizio] → [data fine]
**Durata effettiva:** [N] ore [N] minuti
**Durata pianificata:** [N] ore
**Variazione:** [+N minuti / -N minuti / come pianificato]

## Attività Eseguite

| # | Attività | Esito | Note |
|---|---|---|---|
| 1 | [es. Patching DC-LAB-01] | OK / FAIL / PARTIAL | [dettagli] |
| 2 | [es. Patching SRV-LINUX-01] | OK | Riavvio richiesto |

## Problemi Riscontrati

[Descrizione di qualsiasi problema incontrato durante la maintenance]
[Se nessun problema: "Nessun problema riscontrato"]

## Rollback Eseguiti

[Se è stato necessario fare rollback: descrivi cosa, perché, e esito]
[Se nessun rollback: "Nessun rollback necessario"]

## Verifica Post-Maintenance

- [ ] Tutti i servizi critici verificati e funzionanti
- [ ] Nessun alert nel sistema di monitoring
- [ ] Utenti notificati del completamento
- [ ] Documentazione aggiornata

## Lessons Learned

**Cosa ha funzionato bene:**
[...]

**Cosa migliorare per la prossima maintenance:**
[...]

**Azioni correttive:**
| Azione | Responsabile | Deadline |
|---|---|---|
| [azione] | [chi] | [quando] |
```

---

### Progetto C3: KPI del Programma di Manutenzione

**Metriche mensili da tracciare:**

| KPI | Formula | Target | Come misurare |
|---|---|---|---|
| Planned Maintenance Completion Rate | (attività completate / pianificate) × 100 | > 95% | Da checklist mensile |
| Unplanned Downtime | Ore downtime non pianificato / mese | < 4 ore | Da ticket Incident GLPI |
| Patch Compliance Rate | (sistemi patchati / totale) × 100 | > 98% | Da WSUS / Ansible |
| Backup Success Rate | (backup riusciti / totali) × 100 | > 99.9% | Da log backup |
| Restore Test Success Rate | (restore test riusciti / totali) × 100 | 100% | Da DR log |
| MTBF (Mean Time Between Failures) | Ore operative / numero guasti | trend crescente | Da GLPI Incident |
| Change Success Rate | (change senza rollback / totali) × 100 | > 95% | Da GLPI Change |

**Script Python per KPI mensile:**

```python
#!/usr/bin/env python3
"""kpi_monthly.py - Calcola e stampa i KPI mensili di manutenzione."""

# Dati di esempio per luglio 2026 (in produzione vengono da GLPI API)
monthly_data = {
    "mese": "Luglio 2026",
    "maintenance_tasks_planned": 12,
    "maintenance_tasks_completed": 12,
    "unplanned_downtime_hours": 1.5,
    "systems_patched": 3,
    "systems_total": 3,
    "backups_scheduled": 93,       # 31 giorni × 3 VM
    "backups_successful": 92,
    "restore_tests_planned": 1,
    "restore_tests_successful": 1,
    "changes_total": 3,
    "changes_with_rollback": 0,
    "incidents_total": 5,
    "total_uptime_hours": 720,     # 30 giorni × 24 ore
}

d = monthly_data
print(f"\n{'='*55}")
print(f"  KPI MANUTENZIONE — {d['mese']}")
print(f"{'='*55}")

kpis = [
    ("Completamento Manutenzione", 
     d['maintenance_tasks_completed'] / d['maintenance_tasks_planned'] * 100,
     95, "%"),
    ("Downtime non pianificato",
     d['unplanned_downtime_hours'],
     4, "ore/mese", "lower_is_better"),
    ("Patch Compliance",
     d['systems_patched'] / d['systems_total'] * 100,
     98, "%"),
    ("Backup Success Rate",
     d['backups_successful'] / d['backups_scheduled'] * 100,
     99.9, "%"),
    ("Restore Test Success",
     d['restore_tests_successful'] / d['restore_tests_planned'] * 100,
     100, "%"),
    ("Change Success Rate",
     (d['changes_total'] - d['changes_with_rollback']) / d['changes_total'] * 100,
     95, "%"),
    ("MTBF (ore)",
     d['total_uptime_hours'] / max(d['incidents_total'], 1),
     100, "ore"),
]

for kpi in kpis:
    name, value, target, unit = kpi[0], kpi[1], kpi[2], kpi[3]
    lower_is_better = len(kpi) > 4 and kpi[4] == "lower_is_better"
    
    if lower_is_better:
        is_ok = value <= target
    else:
        is_ok = value >= target
    
    status = "OK " if is_ok else "WARN"
    print(f"  [{status}] {name}: {value:.1f} {unit} (target: {'<=' if lower_is_better else '>='}{target})")

print(f"{'='*55}\n")
```

---

## Checklist di Validazione — Tutorial ops02b Completato

### Fondamenti (Part A)
- [ ] Sai descrivere il ciclo di patching in 4 fasi e il motivo di ognuna
- [ ] Sai spiegare cos'è la regola 3-2-1-1-0 e a cosa serve il "0"
- [ ] Sai elencare i 5 attributi SMART critici e il loro significato
- [ ] Sai descrivere gli elementi obbligatori di una maintenance window
- [ ] Sai spiegare cos'è un change freeze e perché esiste

### Strumenti (Part B)
- [ ] Ciclo patching Windows: change request GLPI → snapshot → upgrade → verifica
- [ ] Ciclo patching Linux: apt upgrade → verifica servizi → log salvato
- [ ] Restore test completato: snapshot ripristinato, servizi verificati, RTO calcolato
- [ ] smartmontools installato, `smartctl -a` eseguito e interpretato
- [ ] DR drill plan Q3 2026 documentato con runbook
- [ ] Script `capacity_trend.py` eseguito con interpretazione dell'output

### Governance (Part C)
- [ ] `maintenance_plan_2026.md` creato con change freeze e maintenance windows
- [ ] Template Post-Maintenance Review compilato per almeno una maintenance simulata
- [ ] Script `kpi_monthly.py` eseguito con dati reali o simulati del lab

---

## Appendice A: Comandi Patching — Riferimento Rapido

### Windows PowerShell
```powershell
# Lista aggiornamenti disponibili (richiede PSWindowsUpdate)
Get-WindowsUpdate | Select-Object Title, Size, MsrcSeverity

# Installa tutto e riavvia
Install-WindowsUpdate -AcceptAll -AutoReboot

# Verifica patch installate oggi
Get-HotFix | Where-Object {$_.InstalledOn -ge (Get-Date).Date}

# WSUS cleanup mensile
Invoke-WsusServerCleanup -CleanupObsoleteUpdates -CleanupUnneededContentFiles `
    -CompressUpdates -DeclineExpiredUpdates -DeclineSupersededUpdates
```

### Linux (Debian/Ubuntu)
```bash
# Aggiorna lista pacchetti
sudo apt-get update

# Lista aggiornamenti disponibili
apt list --upgradable 2>/dev/null

# Upgrade sicurezza + non-security
sudo apt-get upgrade -y

# Aggiornamenti di sicurezza automatici (non-interattivi)
sudo unattended-upgrade -d

# Rimozione pacchetti inutili
sudo apt-get autoremove -y && sudo apt-get autoclean

# Verifica se riavvio necessario
[ -f /var/run/reboot-required ] && echo "Riavvio richiesto" || echo "Nessun riavvio necessario"
```

---

## Riferimenti

| Risorsa | URL / Posizione | Contenuto |
|---|---|---|
| Documento sorgente | `../02-manutenzione-preventiva.md` (sez. 4-8) | Manutenzione mensile/annuale/predittiva |
| Microsoft MSRC | msrc.microsoft.com | Security updates Microsoft |
| CERT-AGID | cert-agid.gov.it | Bollettini sicurezza italiani |
| PSWindowsUpdate | PowerShell Gallery | Modulo gestione aggiornamenti Windows |
| smartmontools | smartmontools.org | SMART analysis tool |
| Tutorial ops06 | `tutorial_ops06_ch1a_backup_strategy_lab.md` | Backup e DR completo |
| Tutorial ops12 | `tutorial_ops12_ch1a_capacity_planning_lab.md` | Capacity planning avanzato |

---

*Fine tutorial ops02b — Prossimo: `tutorial_ops03_ch1a_windows_server_ops_lab.md`*
