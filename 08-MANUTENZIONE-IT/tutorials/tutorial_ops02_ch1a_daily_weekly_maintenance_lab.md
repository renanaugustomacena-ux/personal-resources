# Tutorial: Manutenzione Preventiva — Routine Giornaliere e Settimanali — Hands-On Lab

> **Documento di riferimento:** `02-manutenzione-preventiva.md` (sezioni 1-3)
> **Dominio:** Manutenzione Preventiva
> **Ambito:** Checklist giornaliere e settimanali, verifica backup, monitoring spazio disco, log review, patch weekly
> **Durata lab:** 3-4 ore (strutturate come sessioni mattutine simulate)
> **Livello:** Da principiante ad intermedio
> **Prerequisiti:** `tutorial_ops00` (lab configurato), `tutorial_ops01_ch1a` (concetti ITIL base)
> **Ambiente:** Lab isolato — DC-LAB-01, SRV-LINUX-01, WKS-LAB-01 tutti accesi

---

## Lab Environment Setup

Usa il lab già configurato in tutorial_ops00. Verifica rapidamente:

```powershell
# Da WKS-LAB-01
.\lab_healthcheck.ps1
# Atteso: tutti TcpTestSucceeded: True
```

**Aggiunte specifiche per questo tutorial:**

Su DC-LAB-01 aggiungeremo: WSUS (Windows Server Update Services) simulato, Task Scheduler per automazione checklist.
Su SRV-LINUX-01 aggiungeremo: script cron per monitoring giornaliero, logrotate, disk usage alerts.

Non è necessario installare nulla ora — lo installiamo step-by-step negli esercizi.

---

## PART A: FONDAMENTI — La Scienza della Manutenzione Proattiva

> Questa sezione risponde alla domanda che ogni tecnico IT si pone: "Perché perdere tempo a fare queste cose PRIMA che si rompa qualcosa?" La risposta è nel denaro, nella carriera, e in una vita professionale meno stressante.

---

### Concetto A1: I Tre Regimi di Manutenzione — Analogia Medica

> **Analogia.** Un medico sportivo può seguire il suo atleta in tre modi: (1) aspettare che si faccia male e curarlo; (2) farlo visitare ogni 3 mesi e prescrivere esercizi preventivi; (3) monitorare parametri fisiologici in tempo reale e intervenire quando un indicatore si discosta dalla norma. Il primo approccio porta l'atleta al pronto soccorso. Il secondo porta l'atleta a performance costanti. Il terzo porta l'atleta alle Olimpiadi. L'IT funziona esattamente così.

**Manutenzione Correttiva (Reattiva) — Il Pronto Soccorso IT**

Si interviene *dopo* il guasto. Caratteristiche:
- Costo: imprevedibile e alto (emergenza = ore notturne, corrieri express, tecnici urgenti)
- Impatto: downtime non pianificato, utenti bloccati, dati potenzialmente persi
- Stress: massimo (il telefono suona alle 3 di notte, il CEO è furioso)
- Quando è inevitabile: per guasti genuinamente imprevedibili (fulmine, danneggiamento fisico accidentale)

**Manutenzione Preventiva (Pianificata) — La Visita di Controllo**

Si eseguono interventi programmati a intervalli fissi, indipendentemente dallo stato apparente. Caratteristiche:
- Costo: prevedibile e distribuito (basso costo per intervento × molti interventi = costo totale gestibile)
- Impatto: downtime pianificato, comunicato, controllato (il venerdì sera il server è già giù per manutenzione)
- Stress: basso (stai lavorando a un piano, non rincorrendo un incendio)
- Riduzione guasti: 50-70% rispetto alla sola manutenzione correttiva

**Manutenzione Predittiva (Condition-Based) — Il Monitoraggio Fisiologico**

Si usano dati di monitoraggio per prevedere i guasti prima che si verifichino. Caratteristiche:
- Costo: alto setup iniziale (strumenti monitoring, competenze), poi molto efficiente
- Impatto: si interviene nel momento *ottimale* — né troppo presto (spreco) né troppo tardi (guasto)
- Strumenti: dati SMART dei dischi, temperature CPU, errori ECC RAM, cicli scrittura SSD, trend rete
- Livello di maturità: avanzato (tutorial ops07 dedica un intero modulo al monitoring)

**Il modello ottimale per una PMI italiana:**

```
PREVENTIVA (base, sempre)
    + PREDITTIVA (dove hai monitoring)
    + CORRETTIVA (solo per il residuo imprevedibile)
         =
    Piano di manutenzione maturo
```

> **Ratio costo prevenzione vs reazione:** Studi industriali mostrano un ratio 1:10 — ogni euro speso in manutenzione preventiva evita 10 euro di costi in manutenzione correttiva (emergenze, perdita produttività, danni hardware).

---

### Concetto A2: Il ROI della Manutenzione — Perché il Manager Ti Ascolta

> **Analogia.** Il cambio dell'olio di un'auto costa 50€ e richiede 30 minuti ogni 10.000 km. Ignorarlo può significare un motore fuso da 3.000€ e un'auto fuori uso per 2 settimane. Il management IT capisce questo calcolo perfettamente — ma solo se glielo presenti in termini di costi, non di operatività tecnica.

**Il calcolo del costo del downtime:**

Per un'azienda media italiana con 200 dipendenti che fattura 10M€/anno:

```
Fatturato orario: 10.000.000 / 250 giorni / 8 ore = ~5.000€/ora

Costo di un'ora di downtime del sistema ERP:
  - Produttività persa: 200 dipendenti × 25€/ora = 5.000€
  - Fatturato perso (se vendite bloccate): ~5.000€
  - Costi IT emergenza (tecnico notturno, corriere express): 500-2.000€
  - Costo reputazionale (clienti che non ricevono ordini): difficile da quantificare
  TOTALE: 10.000-15.000€ per ogni ora di downtime
```

**Il costo di una buona manutenzione preventiva:**

```
Checklist giornaliera (30 minuti): 1 tecnico × 0.5h × 25€/h = 12.50€/giorno
Checklist settimanale (2 ore): 1 tecnico × 2h × 25€/h = 50€/settimana
Patching mensile (8 ore + finestra manutenzione): ~300€/mese

TOTALE MANUTENZIONE PREVENTIVA MENSILE: ~900€/mese
```

**Il calcolo del ROI:**

```
Senza manutenzione preventiva: 1 incidente P1 al mese × 4 ore = 40.000-60.000€/mese
Con manutenzione preventiva: ~900€/mese + 0.3 incidenti P1 = ~6.000€/mese
RISPARMIO MENSILE: ~34.000-54.000€
ROI DELLA MANUTENZIONE PREVENTIVA: 3.700-6.000%
```

> **Come usare questi numeri.** Quando il tuo manager dice "hai tempo per la checklist giornaliera?", la risposta corretta non è "mi ci vuole solo mezz'ora" — è "la checklist giornaliera ci risparmia statisticamente 34.000€ al mese. Conviene farla?".

**Perché mi interessa?** Capire il ROI della manutenzione preventiva ti trasforma da "tecnico che fa cose" a "professionista IT che protegge il business". È la differenza tra essere visto come un costo e essere visto come un investimento.

---

### Concetto A3: Il Calendario di Manutenzione — Ritmo e Cadenze

> **Analogia.** Pensa a un ristorante di alta cucina. Il cuoco ha cadenze precise: ogni mattina verifica le materie prime (giornaliera), ogni lunedì ordina le scorte settimanali (settimanale), ogni mese pulisce i frigos a fondo (mensile), ogni anno rinnova il contratto con i fornitori (annuale). Non improvvisa. Non aspetta che il cliente si lamenti per scoprire che il pesce è scaduto.

La manutenzione IT segue cadenze simili. Ogni cadenza ha:
- Attività specifiche appropriate a quella frequenza
- Durata stimata
- Finestra temporale preferita
- Output documentato (log, report, ticket GLPI)

**La piramide delle cadenze:**

```
              ANNUALE (8-16 ore)
           [DR drill, audit sicurezza]
          ─────────────────────────────
          SEMESTRALE (4-8 ore/semestre)
       [vulnerability scan, pulizia fisica]
      ─────────────────────────────────────
       TRIMESTRALE (4-8 ore/trimestre)
    [test hardware, revisione accessi, DR parziale]
   ───────────────────────────────────────────────
         MENSILE (4-8 ore/mese)
    [patching, restore test, capacity review]
  ──────────────────────────────────────────────
        SETTIMANALE (1-2 ore/settimana)
  [patch review, AD replica, certificati SSL]
 ────────────────────────────────────────────────
        GIORNALIERA (30-45 minuti/giorno)
 [backup check, disk space, log review, service check]
══════════════════════════════════════════════════════
```

**Regola d'oro del calendario:** Le attività giornaliere devono essere abbastanza veloci da essere completate ogni mattina senza interrompere altri lavori. Se richiedono più di 45 minuti, vanno automatizzate o semplificate.

**Quando fare le attività:**

| Cadenza | Momento ottimale | Perché |
|---|---|---|
| Giornaliera | Prima dell'orario di ufficio (7:30-8:30) | Rileva problemi notturni prima che impattino gli utenti |
| Settimanale | Lunedì mattina, prima del triage | Base per pianificare la settimana IT |
| Mensile | Prima settimana del mese | Coincide con il ciclo di patch Microsoft |
| Trimestrale | Fine trimestre fiscale | Allineamento con cicli business |
| Annuale | Dicembre/Gennaio | Pianificazione budget e rinnovi |

---

### Concetto A4: I Log — La Scatola Nera dell'IT

> **Analogia.** Ogni aereo di linea ha una "scatola nera" che registra ogni parametro di volo: velocità, quota, posizione comandi, conversazioni in cabina. Se l'aereo precipita, gli investigatori usano quella scatola per capire COSA è successo e PERCHÉ. L'IT senza log è come un aereo senza scatola nera: quando qualcosa va storto, non hai dati per capire cosa è successo.

**Cosa trovi nei log:**

```
WINDOWS EVENT LOG (DC-LAB-01):
System Log:          errori di sistema, avvio/spegnimento servizi, driver
Application Log:     errori applicativi, crash, eventi di performance
Security Log:        login riusciti/falliti, modifiche permessi, account changes

LINUX SYSLOG (SRV-LINUX-01):
/var/log/syslog:     log generale di sistema
/var/log/auth.log:   autenticazioni, sudo, SSH
/var/log/kern.log:   messaggi del kernel (hardware, driver)
/var/log/nginx/:     accessi e errori web server
/var/log/mysql/:     query lente, errori database

APPLICATIVI:
/var/log/glpi/:      GLPI web application errors
/var/www/html/glpi/files/_log/: GLPI SQL e application log
```

**I 3 livelli di severità da conoscere:**

| Livello | Cosa significa | Azione richiesta |
|---|---|---|
| **INFO / INFORMATION** | Sistema funziona normalmente; evento registrato per audit | Nessuna — ma utile per ricostruire la cronologia |
| **WARNING / WARN** | Situazione anomala ma non critica; potrebbe peggiorare | Monitora; se si ripete, investigare |
| **ERROR / CRITICAL** | Malfunzionamento; servizio impattato | Investigare immediatamente; aprire ticket |

**Pattern da riconoscere nella checklist mattutina:**

```
✓ Normale:   INFORMATION  7.723 entries  → log regolare, nessun problema
⚠ Attenzione: WARNING 3 entries "Disk volume C: at 78%" → tieni d'occhio
✗ Problema:  ERROR 1 entry "Backup job FAILED at 03:12" → apri ticket P2
🚨 Urgente:  CRITICAL 1 entry "Domain Controller unresponsive" → P1 immediato
```

---

### Concetto A5: Automazione vs Esecuzione Manuale

> **Analogia.** Hai due opzioni per essere svegliato di mattina: (1) qualcuno ti chiama a voce ogni mattina alle 7:00; (2) una sveglia automatica che suona alle 7:00 e ti manda anche un SMS se non la spengi in 5 minuti. L'automazione non elimina il tuo intervento — cambia la natura dell'intervento da "eseguire la checklist" a "gestire le eccezioni rilevate dalla checklist automatica".

**Cosa automatizzare per prima:**

| Attività | Frequenza | Candidata all'automazione? | Strumento |
|---|---|---|---|
| Verifica completamento backup | Giornaliera | ✓ Alta priorità | Task Scheduler / cron + script |
| Controllo spazio disco | Giornaliera | ✓ Alta priorità | Script con alert email |
| Verifica servizi critici | Giornaliera | ✓ Alta priorità | Monitoring (Zabbix) o script |
| Review log di sicurezza | Giornaliera | Parzialmente | Script filtra eventi critici |
| Patching Windows | Mensile | ✓ Automazione parziale | WSUS + Windows Update |
| Backup configurazioni switch | Settimanale | ✓ | Script TFTP/SCP |
| Verifica certificati SSL | Settimanale | ✓ | Script check-cert |
| Analisi manuale dei trend | Mensile | ✗ (richiede giudizio) | Manuale su report automatici |

**Il principio "automazione prima":**

Non automatizzare mai un processo che non capisci ancora — produci automazione del caos. Prima esegui manualmente 3-5 volte per capire:
1. Cosa controlli esattamente
2. Come distingui "OK" da "PROBLEMA"
3. Cosa fai quando trovi un problema
4. Quanto tempo ci vuole in media

Solo *dopo* aver eseguito manualmente e compreso, automatizzi.

**Cosa NON automatizzare:**

- Decisioni che richiedono contesto (es. "applico questa patch? Dipende se c'è un cambio freeze aziendale")
- Azioni con impatto critico senza checkpoint umano (es. reboot di un server di produzione)
- Analisi di trend (uno script vede i numeri; tu vedi il contesto: "questa settimana c'è stata la fiera aziendale, il traffico è normale")

---

### Concetto A6: La Documentazione dell'Esecuzione — Trace completo

> **Analogia.** Un chirurgo documenta ogni intervento sul registro operatorio: data, anestesista, procedura, durata, complicazioni, esito. Non perché non si fidi della propria memoria — ma perché tra 6 mesi un altro medico deve poter capire cosa è successo. In IT, la documentazione dell'esecuzione della manutenzione serve esattamente allo stesso scopo.

**Cosa documentare:**

```
Per ogni esecuzione della checklist:
  ✓ Data e ora di esecuzione
  ✓ Chi ha eseguito la verifica
  ✓ Per ogni item: fatto / non fatto / skipped + perché se skipped
  ✓ Anomalie rilevate e azioni intraprese
  ✓ Ticket aperti se ci sono problemi

ESEMPIO DI LOG GIORNALIERO:
=== 2026-07-15 08:15 - Checklist giornaliera ===
Tecnico: mario.rossi@lab.local
[ OK ] Backup notturno completato: 47 GB, integrity OK
[ OK ] Spazio disco DC-LAB-01 C: 34% usato (< 80% threshold)
[ OK ] Spazio disco SRV-LINUX-01 /: 28% usato
[WARN] Spazio disco SRV-LINUX-01 /var: 76% usato → MONITORARE
[ OK ] Servizi critici: AD, DNS, DHCP, Email tutti UP
[ OK ] Nessun evento CRITICAL nei log security ultimi 24h
[FAIL] Alert monitoring: SRV-LINUX-01 /var/log crescita anomala
       → AZIONE: Aperto ticket GLPI #0042 P3, verifica logrotate
Durata esecuzione: 22 minuti
```

**La regola degli "skip giustificati":**

Non riuscire a completare una checklist item è accettabile se documentato. Non documentare uno skip è inaccettabile — equivale a non averlo fatto.

Formato per gli skip:
```
[SKIP] Verifica AD replica: MOTIVO: DC secondario in manutenzione pianificata
       (change CAB-2026-047). NEXT: verifica lunedì 22/07 al completamento della manutenzione.
```

---

## PART B: OPERAZIONI — Implementare la Routine di Manutenzione Giornaliera e Settimanale

> Ogni esercizio in questa sezione simula un'attività reale della checklist di manutenzione. Alla fine avrai uno script automatizzato che esegue la checklist mattutina per te e un processo documentato per la settimana.

---

### Esercizio B1: Simulare la Checklist Mattutina Manuale (DC-LAB-01)

**Obiettivo.** Eseguire manualmente tutte le verifiche della checklist giornaliera su DC-LAB-01 (Windows Server 2022), registrando ogni risultato.

Apri PowerShell come Administrator su DC-LAB-01.

**Check 1: Spazio disco su tutti i volumi**

```powershell
# Verifica spazio disco
Get-PSDrive -PSProvider FileSystem | 
    Select-Object Name, 
        @{N="Used(GB)"; E={[math]::Round($_.Used/1GB, 2)}},
        @{N="Free(GB)"; E={[math]::Round($_.Free/1GB, 2)}},
        @{N="Total(GB)"; E={[math]::Round(($_.Used+$_.Free)/1GB, 2)}},
        @{N="Used%"; E={[math]::Round($_.Used/($_.Used+$_.Free)*100, 1)}}
```

Output tipico:
```
Name Used(GB) Free(GB) Total(GB) Used%
---- -------- -------- --------- -----
C       18.4     39.8       58.2  31.6
```

Interpretazione:
- `Used%` < 70% → ✓ OK
- `Used%` 70-85% → ⚠ WARNING — pianifica pulizia
- `Used%` > 85% → ✗ CRITICAL — apri ticket P2 subito

**Check 2: Stato dei servizi critici**

```powershell
# Verifica servizi critici di Windows Server
$critical_services = @(
    "ADWS",       # Active Directory Web Services
    "DNS",        # Domain Name Service
    "DHCPServer", # DHCP Server
    "Netlogon",   # Net Logon
    "W32Time",    # Windows Time
    "EventLog"    # Event Log
)

foreach ($svc in $critical_services) {
    $s = Get-Service -Name $svc -ErrorAction SilentlyContinue
    if ($null -eq $s) {
        Write-Host "[N/A] $svc - servizio non trovato su questo server" -ForegroundColor Gray
    } elseif ($s.Status -eq "Running") {
        Write-Host "[ OK] $svc - Running" -ForegroundColor Green
    } else {
        Write-Host "[FAIL] $svc - $($s.Status)" -ForegroundColor Red
    }
}
```

Output atteso (DC-LAB-01 funzionante):
```
[ OK] ADWS - Running
[ OK] DNS - Running
[ OK] DHCPServer - Running
[ OK] Netlogon - Running
[ OK] W32Time - Running
[ OK] EventLog - Running
```

**Check 3: Log eventi delle ultime 24 ore**

```powershell
# Filtra eventi Error e Critical negli ultimi 24 ore
$since = (Get-Date).AddHours(-24)

$critical_events = Get-WinEvent -FilterHashtable @{
    LogName   = 'System','Application'
    Level     = 1,2   # 1=Critical, 2=Error
    StartTime = $since
} -ErrorAction SilentlyContinue | 
Select-Object TimeCreated, ProviderName, Id, Message |
Sort-Object TimeCreated -Descending |
Select-Object -First 10

if ($critical_events.Count -eq 0) {
    Write-Host "[ OK] Nessun evento Critical/Error nelle ultime 24 ore" -ForegroundColor Green
} else {
    Write-Host "[!] $($critical_events.Count) eventi Critical/Error trovati:" -ForegroundColor Yellow
    $critical_events | Format-Table TimeCreated, Id, ProviderName -AutoSize
}
```

**Check 4: Connettività DNS**

```powershell
# Verifica risoluzione DNS funzionante
$test_names = @("google.com", "DC-LAB-01")
foreach ($name in $test_names) {
    try {
        $result = Resolve-DnsName $name -ErrorAction Stop | Select-Object -First 1
        Write-Host "[ OK] DNS risolve $name → $($result.IPAddress)" -ForegroundColor Green
    } catch {
        Write-Host "[FAIL] DNS non risolve $name" -ForegroundColor Red
    }
}
```

**Registra i risultati in un file log:**

```powershell
# Crea la directory per i log di manutenzione
New-Item -ItemType Directory -Path "C:\MaintLogs" -Force | Out-Null

# Salva il report della giornata
$log_file = "C:\MaintLogs\daily_check_$(Get-Date -Format 'yyyy-MM-dd').log"
$date_str = Get-Date -Format "yyyy-MM-dd HH:mm"

Add-Content -Path $log_file -Value "=== $date_str Checklist Giornaliera DC-LAB-01 ==="
Add-Content -Path $log_file -Value "Tecnico: $env:USERNAME@$env:USERDOMAIN"
Add-Content -Path $log_file -Value "[ ] Spazio disco: [inserisci risultato manualmente]"
Add-Content -Path $log_file -Value "[ ] Servizi critici: [inserisci risultato]"
Add-Content -Path $log_file -Value "[ ] Log eventi: [inserisci risultato]"
Add-Content -Path $log_file -Value "[ ] DNS funzionante: [inserisci risultato]"
Add-Content -Path $log_file -Value "Note: [inserisci eventuali anomalie]"

Write-Host "Log creato: $log_file"
```

**Checkpoint B1:**
- [ ] Spazio disco: volumi rilevati correttamente
- [ ] Servizi: tutti `Running` (o sai perché non lo sono)
- [ ] Log eventi: sezione verificata, nessun CRITICAL inaspettato
- [ ] File log creato in `C:\MaintLogs\`

---

### Esercizio B2: Checklist Giornaliera su SRV-LINUX-01

**Obiettivo.** Eseguire le stesse verifiche su Linux — lo stesso principio, comandi diversi.

Accedi via SSH: `ssh lab-admin@192.168.56.20`

**Check 1: Spazio disco su tutti i filesystem**

```bash
# Panoramica spazio disco
df -h

# Output tipico:
# Filesystem      Size  Used Avail Use% Mounted on
# /dev/sda1        38G  8.1G   28G  23% /
# /dev/sda2       2.0G  156M  1.7G   9% /boot
# tmpfs           2.0G     0  2.0G   0% /dev/shm

# Filtra filesystem che superano il 75% (warning threshold)
df -h | awk 'NR>1 {gsub(/%/, "", $5); if ($5+0 >= 75) print "[WARN] "$0}'
# Se nessun output: tutti sotto soglia
```

**Check 2: Stato servizi critici su Linux (systemd)**

```bash
# Lista dei servizi critici su SRV-LINUX-01
declare -a critical_services=("ssh" "docker" "systemd-networkd" "systemd-resolved")

for svc in "${critical_services[@]}"; do
    status=$(systemctl is-active "$svc" 2>/dev/null)
    if [ "$status" = "active" ]; then
        echo "[ OK] $svc: $status"
    else
        echo "[FAIL] $svc: $status"
    fi
done
```

Output atteso:
```
[ OK] ssh: active
[ OK] docker: active
[ OK] systemd-networkd: active
[ OK] systemd-resolved: active
```

**Check 3: Log di sistema (ultimi errori)**

```bash
# Log di sistema ultime 24 ore - solo errori
journalctl --since "24 hours ago" -p err -n 20

# Se nessun output: nessun errore critico
# Se ci sono errori: leggi i messaggi e valuta l'impatto

# Alternativa più semplice - solo righe con ERROR o CRITICAL
sudo grep -i "error\|critical\|fail" /var/log/syslog | tail -20
```

**Check 4: Memoria e carico sistema**

```bash
# Memoria disponibile
free -h
# Atteso: available > 1 GB

# Carico CPU (load average)
uptime
# Atteso: load average (1min, 5min, 15min) < numero di CPU
# es. su sistema 2 CPU: load average < 2.0 è normale

# Top 5 processi per uso memoria
ps aux --sort=-%mem | head -6
```

**Check 5: Container GLPI funzionante**

```bash
cd ~/glpi-lab
docker compose ps
# Atteso: glpi-db e glpi-app in stato "Up"

# Test rapido GLPI risponde
curl -s -o /dev/null -w "GLPI HTTP Status: %{http_code}\n" http://localhost:8080/
# Atteso: HTTP Status: 200 o 302
```

**Checkpoint B2:**
- [ ] `df -h` non mostra filesystem sopra 75%
- [ ] Tutti i servizi critici in stato `active`
- [ ] `journalctl` non mostra errori critici inaspettati
- [ ] GLPI risponde HTTP 200

---

### Esercizio B3: Automatizzare la Checklist Giornaliera (Script PowerShell)

**Obiettivo.** Scrivere uno script PowerShell che esegue automaticamente tutte le verifiche giornaliere e produce un report + apre un ticket GLPI se trova problemi.

Crea il file `C:\Lab\Scripts\daily_maintenance_check.ps1` su DC-LAB-01:

```powershell
# daily_maintenance_check.ps1
# Checklist giornaliera automatizzata per DC-LAB-01
# Eseguire ogni mattina alle 07:30 tramite Task Scheduler

param(
    [string]$LogDir = "C:\MaintLogs",
    [int]$DiskWarnThreshold = 75,
    [int]$DiskCritThreshold = 85
)

$ErrorActionPreference = "Continue"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$logFile   = Join-Path $LogDir "daily_$(Get-Date -Format 'yyyy-MM-dd').log"
$issues    = @()

New-Item -ItemType Directory -Path $LogDir -Force | Out-Null

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $line = "[$timestamp][$Level] $Message"
    Add-Content -Path $logFile -Value $line
    switch ($Level) {
        "OK"   { Write-Host $line -ForegroundColor Green }
        "WARN" { Write-Host $line -ForegroundColor Yellow }
        "FAIL" { Write-Host $line -ForegroundColor Red }
        default { Write-Host $line }
    }
}

Write-Log "=== INIZIO CHECKLIST GIORNALIERA - DC-LAB-01 ==="
Write-Log "Operatore: $env:USERNAME"

# --- CHECK 1: Spazio Disco ---
Write-Log "--- CHECK: Spazio Disco ---"
Get-PSDrive -PSProvider FileSystem | ForEach-Object {
    $usedPct = [math]::Round($_.Used / ($_.Used + $_.Free) * 100, 1)
    $freePct = 100 - $usedPct
    if ($usedPct -ge $DiskCritThreshold) {
        Write-Log "DISCO $($_.Name): $usedPct% usato - CRITICO" "FAIL"
        $issues += "CRITICO: Disco $($_.Name) al $usedPct% (soglia: $DiskCritThreshold%)"
    } elseif ($usedPct -ge $DiskWarnThreshold) {
        Write-Log "DISCO $($_.Name): $usedPct% usato - ATTENZIONE" "WARN"
        $issues += "WARN: Disco $($_.Name) al $usedPct% (soglia: $DiskWarnThreshold%)"
    } else {
        Write-Log "DISCO $($_.Name): $usedPct% usato - OK" "OK"
    }
}

# --- CHECK 2: Servizi Critici ---
Write-Log "--- CHECK: Servizi Critici ---"
$svcList = @("ADWS","DNS","DHCPServer","Netlogon","W32Time","EventLog","LanmanServer")
foreach ($svc in $svcList) {
    $s = Get-Service -Name $svc -ErrorAction SilentlyContinue
    if ($null -eq $s) {
        Write-Log "SERVIZIO $svc: non presente" "INFO"
    } elseif ($s.Status -eq "Running") {
        Write-Log "SERVIZIO $svc: Running" "OK"
    } else {
        Write-Log "SERVIZIO $svc: $($s.Status)" "FAIL"
        $issues += "FAIL: Servizio $svc in stato $($s.Status)"
    }
}

# --- CHECK 3: Log Critici ---
Write-Log "--- CHECK: Event Log (ultime 24h) ---"
$since = (Get-Date).AddHours(-24)
$critCount = (Get-WinEvent -FilterHashtable @{
    LogName='System','Application'; Level=1,2; StartTime=$since
} -ErrorAction SilentlyContinue | Measure-Object).Count

if ($critCount -eq 0) {
    Write-Log "LOG CRITICI: 0 eventi Error/Critical - OK" "OK"
} elseif ($critCount -le 5) {
    Write-Log "LOG CRITICI: $critCount eventi - ATTENZIONE (verifica manualmente)" "WARN"
} else {
    Write-Log "LOG CRITICI: $critCount eventi - INVESTIGARE" "FAIL"
    $issues += "FAIL: $critCount eventi critici nei log ultime 24h"
}

# --- CHECK 4: Connettività Rete ---
Write-Log "--- CHECK: Connettività ---"
$pingTests = @("192.168.56.20","192.168.56.30","8.8.8.8")
foreach ($ip in $pingTests) {
    $r = Test-Connection -ComputerName $ip -Count 2 -Quiet
    if ($r) {
        Write-Log "PING $ip: OK" "OK"
    } else {
        Write-Log "PING $ip: TIMEOUT" "FAIL"
        $issues += "FAIL: Ping verso $ip fallito"
    }
}

# --- RIEPILOGO ---
Write-Log "=== RIEPILOGO CHECKLIST ==="
if ($issues.Count -eq 0) {
    Write-Log "RISULTATO: TUTTO OK - Nessuna anomalia rilevata" "OK"
} else {
    Write-Log "RISULTATO: $($issues.Count) PROBLEMI RILEVATI:" "WARN"
    foreach ($issue in $issues) {
        Write-Log "  - $issue" "WARN"
    }
    Write-Log "AZIONE: Verificare manualmente e aprire ticket GLPI se necessario" "WARN"
}
Write-Log "=== FINE CHECKLIST ==="
Write-Log "Log salvato: $logFile"
```

**Esegui lo script:**

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\C:\Lab\Scripts\daily_maintenance_check.ps1
```

**Checkpoint B3:**
- [ ] Script eseguito senza errori di sintassi
- [ ] File di log creato in `C:\MaintLogs\`
- [ ] Il report distingue correttamente OK / WARN / FAIL
- [ ] Hai modificato le soglie di warning (valore `DiskWarnThreshold`) e verificato che funzionino

---

### Esercizio B4: Automatizzare la Checklist su Linux (Bash + Cron)

**Obiettivo.** Creare lo script equivalente su SRV-LINUX-01 e schedularlo con cron per esecuzione automatica ogni mattina.

```bash
# Su SRV-LINUX-01
mkdir -p ~/scripts ~/maint-logs
nano ~/scripts/daily_check.sh
```

Incolla questo contenuto:

```bash
#!/bin/bash
# daily_check.sh - Checklist giornaliera SRV-LINUX-01
# Schedulato con cron: 07:30 ogni giorno lavorativo

LOG_DIR="$HOME/maint-logs"
LOG_FILE="$LOG_DIR/daily_$(date +%Y-%m-%d).log"
DISK_WARN=75
DISK_CRIT=85
ISSUES=()

mkdir -p "$LOG_DIR"

log() {
    local level="$1"
    local msg="$2"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')][$level] $msg" | tee -a "$LOG_FILE"
}

log "INFO" "=== INIZIO CHECKLIST GIORNALIERA - SRV-LINUX-01 ==="
log "INFO" "Operatore: $(whoami)"

# --- CHECK 1: Spazio disco ---
log "INFO" "--- CHECK: Spazio Disco ---"
while IFS= read -r line; do
    pct=$(echo "$line" | awk '{print $5}' | tr -d '%')
    mount=$(echo "$line" | awk '{print $6}')
    if [ -n "$pct" ] && [ "$pct" -ge "$DISK_CRIT" ] 2>/dev/null; then
        log "FAIL" "DISCO $mount: ${pct}% usato - CRITICO"
        ISSUES+=("CRITICO: $mount al ${pct}%")
    elif [ -n "$pct" ] && [ "$pct" -ge "$DISK_WARN" ] 2>/dev/null; then
        log "WARN" "DISCO $mount: ${pct}% usato - ATTENZIONE"
        ISSUES+=("WARN: $mount al ${pct}%")
    elif [ -n "$pct" ]; then
        log "OK  " "DISCO $mount: ${pct}% usato - OK"
    fi
done < <(df -h | grep -v "^Filesystem" | grep -v "^tmpfs" | grep -v "^udev")

# --- CHECK 2: Servizi critici ---
log "INFO" "--- CHECK: Servizi ---"
for svc in ssh docker systemd-networkd; do
    status=$(systemctl is-active "$svc" 2>/dev/null)
    if [ "$status" = "active" ]; then
        log "OK  " "SERVIZIO $svc: active"
    else
        log "FAIL" "SERVIZIO $svc: $status"
        ISSUES+=("FAIL: Servizio $svc = $status")
    fi
done

# --- CHECK 3: Memoria ---
log "INFO" "--- CHECK: Memoria ---"
mem_avail_gb=$(free -g | awk '/Mem:/{print $7}')
if [ "${mem_avail_gb:-0}" -lt 1 ]; then
    log "WARN" "RAM disponibile: ${mem_avail_gb}GB - BASSA"
    ISSUES+=("WARN: RAM disponibile solo ${mem_avail_gb}GB")
else
    log "OK  " "RAM disponibile: ${mem_avail_gb}GB - OK"
fi

# --- CHECK 4: Errori nel syslog ---
log "INFO" "--- CHECK: Log Sistema (ultime 24h) ---"
err_count=$(journalctl --since "24 hours ago" -p err -q 2>/dev/null | wc -l)
if [ "$err_count" -eq 0 ]; then
    log "OK  " "LOG ERRORI: 0 errori - OK"
elif [ "$err_count" -le 10 ]; then
    log "WARN" "LOG ERRORI: $err_count errori - verifica consigliata"
    ISSUES+=("WARN: $err_count errori nel syslog")
else
    log "FAIL" "LOG ERRORI: $err_count errori - investigare"
    ISSUES+=("FAIL: $err_count errori nel syslog ultime 24h")
fi

# --- CHECK 5: Container GLPI ---
log "INFO" "--- CHECK: Container Docker ---"
if docker compose -f ~/glpi-lab/docker-compose.yml ps --status running | grep -q "running"; then
    log "OK  " "GLPI container: running"
else
    log "FAIL" "GLPI container: non in running"
    ISSUES+=("FAIL: Container GLPI non in esecuzione")
fi

# --- RIEPILOGO ---
log "INFO" "=== RIEPILOGO CHECKLIST ==="
if [ ${#ISSUES[@]} -eq 0 ]; then
    log "OK  " "RISULTATO: TUTTO OK - nessuna anomalia"
else
    log "WARN" "RISULTATO: ${#ISSUES[@]} PROBLEMI RILEVATI:"
    for issue in "${ISSUES[@]}"; do
        log "WARN" "  - $issue"
    done
    log "WARN" "AZIONE: Verificare manualmente e aprire ticket GLPI"
fi
log "INFO" "Log: $LOG_FILE"
```

```bash
# Rendi lo script eseguibile
chmod +x ~/scripts/daily_check.sh

# Test esecuzione
~/scripts/daily_check.sh
```

**Schedulare con cron:**

```bash
# Apri l'editor crontab
crontab -e

# Aggiungi questa riga (esegui alle 07:30 ogni giorno lavorativo, lunedì-venerdì):
30 7 * * 1-5 /home/lab-admin/scripts/daily_check.sh >> /home/lab-admin/maint-logs/cron.log 2>&1

# Salva ed esci (Ctrl+X in nano)

# Verifica che il cron sia stato aggiunto
crontab -l
```

**Checkpoint B4:**
- [ ] Script `daily_check.sh` eseguibile senza errori
- [ ] Distingue correttamente OK / WARN / FAIL per ogni check
- [ ] Cron schedulato per le 07:30 Lun-Ven
- [ ] File di log creato in `~/maint-logs/`

---

### Esercizio B5: Checklist Settimanale — Verifica Certificati SSL e Scadenze

**Obiettivo.** Implementare il check settimanale più spesso trascurato — la verifica dei certificati SSL/TLS. Un certificato scaduto mette offline siti web, API, email e crea errori incomprensibili per gli utenti.

**Perché i certificati scadono "a sorpresa"?**

Perché vengono rinnovati e poi dimenticati per 1 anno (o 2 anni per i vecchi standard). Senza monitoring attivo, scopri che il certificato è scaduto quando gli utenti chiamano perché "il sito non funziona" — e il browser mostra un errore di sicurezza, non "certificato scaduto".

**Script: check-certs.sh (su SRV-LINUX-01)**

```bash
cat > ~/scripts/weekly_cert_check.sh << 'CERT_EOF'
#!/bin/bash
# weekly_cert_check.sh - Verifica scadenza certificati SSL
# Soglia di warning: 30 giorni

WARN_DAYS=30
LOG="$HOME/maint-logs/cert_check_$(date +%Y-%m-%d).log"
ISSUES=()

check_cert() {
    local host="$1"
    local port="${2:-443}"
    
    expiry=$(echo | openssl s_client -connect "$host:$port" -servername "$host" 2>/dev/null |
             openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2)
    
    if [ -z "$expiry" ]; then
        echo "[SKIP] $host:$port - non raggiungibile o non TLS"
        return
    fi
    
    expiry_epoch=$(date -d "$expiry" +%s 2>/dev/null)
    now_epoch=$(date +%s)
    days_left=$(( (expiry_epoch - now_epoch) / 86400 ))
    
    if [ "$days_left" -lt 0 ]; then
        echo "[FAIL] $host:$port - SCADUTO $days_left giorni fa" | tee -a "$LOG"
        ISSUES+=("$host:$port SCADUTO")
    elif [ "$days_left" -lt "$WARN_DAYS" ]; then
        echo "[WARN] $host:$port - scade in $days_left giorni ($expiry)" | tee -a "$LOG"
        ISSUES+=("$host:$port scade in $days_left giorni")
    else
        echo "[ OK] $host:$port - scade in $days_left giorni ($expiry)" | tee -a "$LOG"
    fi
}

echo "=== CERT CHECK $(date) ===" | tee -a "$LOG"

# Lista host/porte da verificare (adatta al tuo ambiente)
check_cert "google.com" 443           # test esterno (deve funzionare)
check_cert "192.168.56.10" 443        # DC-LAB-01 se ha IIS/HTTPS
check_cert "192.168.56.20" 8080       # SRV-LINUX-01 GLPI (HTTP, no cert)

echo ""
if [ ${#ISSUES[@]} -gt 0 ]; then
    echo "ATTENZIONE: ${#ISSUES[@]} certificati richiedono azione:"
    for i in "${ISSUES[@]}"; do echo "  - $i"; done
fi
CERT_EOF

chmod +x ~/scripts/weekly_cert_check.sh
~/scripts/weekly_cert_check.sh
```

**Aggiungi al crontab settimanale (lunedì ore 08:00):**

```bash
crontab -e
# Aggiungi:
0 8 * * 1 /home/lab-admin/scripts/weekly_cert_check.sh
```

**Checkpoint B5:**
- [ ] Script `weekly_cert_check.sh` eseguibile
- [ ] Verifica google.com funzionante (test connettività TLS)
- [ ] Hai capito come aggiungere altri host alla lista

---

### Esercizio B6: Aprire Ticket di Manutenzione in GLPI

**Obiettivo.** Praticare il flusso corretto: la checklist trova un problema → si apre un ticket GLPI → il problema viene gestito secondo la priorità corretta.

**Scenario simulato:**

Lo script `daily_maintenance_check.ps1` ha rilevato questa anomalia:
```
[WARN] DISCO C: 79% usato - ATTENZIONE
```

**Apri il ticket in GLPI (da WKS-LAB-01, browser → `http://192.168.56.20:8080/`):**

Accedi come `it-admin` → Helpdesk → Create Ticket:

| Campo | Valore |
|---|---|
| Type | Incident |
| Category | Infrastruttura → Server → Capacità Storage |
| Title | "DC-LAB-01: Volume C: al 79% - Soglia di attenzione raggiunta" |
| Description | "Rilevato dal daily maintenance check del 15/07/2026 ore 07:30. Volume C: utilizzo 79%, soglia warning 75%. Trend crescita stimato: +2%/settimana. Se non si interviene, si raggiungerà il 90% entro circa 5-6 settimane." |
| Urgency | Low |
| Impact | Medium |
| (auto-calcolata) Priority | P4 - Low |
| Assign to | it-admin |
| Due date | +14 giorni |

**Aggiorna il ticket con il piano d'azione:**

Nel ticket appena creato → Add a followup:

```
Piano d'azione proposto:
1. Identificare i file più grandi con: Get-ChildItem C:\ -Recurse | Sort-Object Length -Descending | Select-Object -First 20
2. Verificare log di sistema e file temporanei in C:\Windows\Temp e C:\Users\*\AppData\Local\Temp
3. Eseguire pulizia disk cleanup
4. Se necessario, aggiungere spazio disco alla VM (Action: modifica HDD virtuale in VirtualBox)
5. Verificare che il trend si stabilizzi dopo la pulizia

ETA risoluzione: 3 giorni lavorativi.
```

**Checkpoint B6:**
- [ ] Ticket P4 creato in GLPI per problema spazio disco
- [ ] Followup con piano d'azione aggiunto al ticket
- [ ] Ticket assegnato con data di scadenza entro 14 giorni

---

## PART C: SISTEMATIZZARE — Dal Fare al Gestire la Manutenzione

> Hai imparato i fondamenti (Part A) e hai eseguito le checklist (Part B). In questa sezione costruiamo le strutture che trasformano una "buona abitudine personale" in un processo organizzativo scalabile.

---

### Progetto C1: Pianificazione Task Scheduler su DC-LAB-01

**Obiettivo.** Schedulare `daily_maintenance_check.ps1` con Windows Task Scheduler per esecuzione automatica ogni mattina alle 07:30, con esecuzione anche se l'utente non è loggato.

```powershell
# Crea il task schedulato (esegui come Administrator su DC-LAB-01)
$action  = New-ScheduledTaskAction `
    -Execute "PowerShell.exe" `
    -Argument "-NonInteractive -ExecutionPolicy RemoteSigned -File C:\Lab\Scripts\daily_maintenance_check.ps1"

$trigger = New-ScheduledTaskTrigger `
    -Weekly `
    -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday `
    -At "07:30"

$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
    -RestartCount 2 `
    -RestartInterval (New-TimeSpan -Minutes 5)

$principal = New-ScheduledTaskPrincipal `
    -UserId "SYSTEM" `
    -LogonType ServiceAccount `
    -RunLevel Highest

Register-ScheduledTask `
    -TaskName "IT-DailyMaintenanceCheck" `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description "Checklist giornaliera automatizzata IT Operations - esecuzione lunedi-venerdi 07:30"
```

**Verifica il task creato:**

```powershell
Get-ScheduledTask -TaskName "IT-DailyMaintenanceCheck" | Select-Object TaskName, State, LastRunTime
```

**Test manuale del task:**

```powershell
Start-ScheduledTask -TaskName "IT-DailyMaintenanceCheck"
Start-Sleep -Seconds 10
Get-ScheduledTaskInfo -TaskName "IT-DailyMaintenanceCheck" | Select-Object LastRunTime, LastTaskResult
# LastTaskResult: 0 = successo
```

---

### Progetto C2: Dashboard Manutenzione con Checklist Interattiva

**Obiettivo.** Creare uno script PowerShell interattivo che guida il tecnico attraverso la checklist settimanale in modo strutturato, raccogliendo i risultati e generando il report.

Crea `C:\Lab\Scripts\weekly_checklist_interactive.ps1` su DC-LAB-01:

```powershell
# weekly_checklist_interactive.ps1
# Checklist settimanale interattiva - da eseguire ogni lunedì mattina

$LogFile = "C:\MaintLogs\weekly_$(Get-Date -Format 'yyyy-MM-dd').log"
$Checklist = @(
    @{ Item = "Verifica patch Windows disponibili (WSUS o Windows Update)"; Category = "Patch" },
    @{ Item = "Verifica bollettini sicurezza CERT-AGiD (cert-agid.gov.it)"; Category = "Security" },
    @{ Item = "Backup configurazione switch/router (se presente)"; Category = "Backup" },
    @{ Item = "Verifica replica AD: repadmin /replsummary (DC multipli)"; Category = "AD" },
    @{ Item = "Verifica certificati SSL (> 30 giorni alla scadenza)"; Category = "Cert" },
    @{ Item = "Verifica scadenza account di servizio e password policy"; Category = "AD" },
    @{ Item = "Analisi trend utilizzo risorse ultima settimana"; Category = "Capacity" },
    @{ Item = "Verifica job schedulati (Task Scheduler / cron)"; Category = "Automation" }
)

$results = @()

Write-Host "`n=========================================" -ForegroundColor Cyan
Write-Host "  CHECKLIST SETTIMANALE IT — $(Get-Date -Format 'yyyy-MM-dd')" -ForegroundColor Cyan
Write-Host "  Tecnico: $env:USERNAME" -ForegroundColor Cyan
Write-Host "=========================================`n" -ForegroundColor Cyan

foreach ($item in $Checklist) {
    Write-Host "[$($item.Category)] $($item.Item)"
    Write-Host "  Risultato? [1=OK] [2=WARN] [3=FAIL] [4=SKIP]: " -NoNewline
    $choice = Read-Host
    
    $status = switch ($choice) {
        "1" { "OK" }
        "2" { "WARN" }
        "3" { "FAIL" }
        "4" { "SKIP" }
        default { "SKIP" }
    }
    
    $note = ""
    if ($status -in @("WARN","FAIL","SKIP")) {
        Write-Host "  Note/motivazione: " -NoNewline
        $note = Read-Host
    }
    
    $results += [PSCustomObject]@{
        Category = $item.Category
        Item     = $item.Item
        Status   = $status
        Notes    = $note
    }
}

# Genera il report
$reportLines = @("=== CHECKLIST SETTIMANALE $(Get-Date -Format 'yyyy-MM-dd HH:mm') ===")
$reportLines += "Tecnico: $env:USERNAME"
$reportLines += ""
foreach ($r in $results) {
    $reportLines += "[$($r.Status)] [$($r.Category)] $($r.Item)"
    if ($r.Notes) { $reportLines += "         Note: $($r.Notes)" }
}

$failCount = ($results | Where-Object {$_.Status -eq "FAIL"}).Count
$warnCount = ($results | Where-Object {$_.Status -eq "WARN"}).Count
$reportLines += ""
$reportLines += "RIEPILOGO: $failCount FAIL | $warnCount WARN | $(($results | Where-Object {$_.Status -eq "OK"}).Count) OK"

$reportLines | Out-File -FilePath $LogFile -Encoding UTF8

Write-Host "`nReport salvato: $LogFile" -ForegroundColor Green
if ($failCount -gt 0) {
    Write-Host "ATTENZIONE: $failCount item FAIL rilevati — aprire ticket GLPI" -ForegroundColor Red
}
```

---

### Progetto C3: Connessione ITIL — Manutenzione Preventiva come Practice

**Obiettivo.** Collegare le attività di manutenzione preventiva alle practice ITIL v4 che implementano.

| Attività di Manutenzione | Practice ITIL v4 | Categoria SVS |
|---|---|---|
| Checklist giornaliera backup | **Availability Management** | Deliver and Support |
| Verifica spazio disco + alert | **Capacity and Performance Management** | Deliver and Support |
| Review log eventi sicurezza | **Monitoring and Event Management** | Deliver and Support |
| Patching mensile + test | **Release Management** + **Change Enablement** | Design and Transition |
| Verifica certificati SSL | **IT Asset Management** | Deliver and Support |
| Backup configurazioni rete | **Service Configuration Management** (CMDB) | Design and Transition |
| DR drill trimestrale | **Service Continuity Management** | Design and Transition |
| Pulizia fisica server room | **Infrastructure and Platform Management** | Obtain/Build |
| Report KPI mensile | **Measurement and Reporting** | Plan + Improve |
| Revisione accessi utenti | **Information Security Management** | Deliver and Support |

**Come scala in produzione:**

| Lab (1 tecnico) | Enterprise (team IT 10 persone) |
|---|---|
| Checklist manuale / script bash | CMDB + Zabbix con 500 alert configurati |
| Task Scheduler per 3 server | Ansible Playbook su 300 server |
| Email alert se problema | PagerDuty on-call rotation |
| Foglio Excel manutenzione | Jira Service Management CMDB dashboard |
| Backup manuale su NAS locale | Backup automatizzato, immutable, offsite |

---

## Checklist di Validazione — Tutorial ops02a Completato

### Fondamenti (Part A)
- [ ] Sai spiegare la differenza tra manutenzione correttiva, preventiva e predittiva
- [ ] Sai calcolare il ROI della manutenzione preventiva per una PMI
- [ ] Sai descrivere le 5 cadenze di manutenzione (giornaliera → annuale) con esempi
- [ ] Sai spiegare perché si documenta anche quando "tutto va bene"
- [ ] Hai capito il principio "automatizza solo ciò che capisci già manualmente"

### Strumenti (Part B)
- [ ] Checklist giornaliera manuale completata su DC-LAB-01 e SRV-LINUX-01
- [ ] Script `daily_maintenance_check.ps1` creato e testato su DC-LAB-01
- [ ] Script `daily_check.sh` creato e testato su SRV-LINUX-01
- [ ] Cron su SRV-LINUX-01 schedulato per le 07:30 Lun-Ven
- [ ] Script `weekly_cert_check.sh` funzionante
- [ ] Ticket P4 aperto in GLPI per problema spazio disco simulato

### Governance (Part C)
- [ ] Task Scheduler su DC-LAB-01 schedulato per daily_maintenance_check.ps1
- [ ] Script `weekly_checklist_interactive.ps1` creato e testato
- [ ] Hai mappato almeno 5 attività di manutenzione alle practice ITIL corrispondenti

---

## Appendice A: Comandi Checklist — Riferimento Rapido

### Windows PowerShell — Monitoring

```powershell
# Spazio disco
Get-PSDrive -PSProvider FileSystem | Select-Object Name, @{N="Used%"; E={[math]::Round($_.Used/($_.Used+$_.Free)*100,1)}}

# Servizi non in Running
Get-Service | Where-Object {$_.StartType -eq "Automatic" -and $_.Status -ne "Running"}

# Event Log: errori ultime 24h
Get-WinEvent -FilterHashtable @{LogName='System','Application'; Level=1,2; StartTime=(Get-Date).AddHours(-24)} -ErrorAction SilentlyContinue | Select-Object TimeCreated, Id, ProviderName, Message -First 20

# Uptime del server
(Get-Date) - (gcim Win32_OperatingSystem).LastBootUpTime
```

### Linux Bash — Monitoring

```bash
# Spazio disco sopra 80%
df -h | awk 'NR>1 {gsub(/%/,"",$5); if($5+0>=80) print "WARN:",$0}'

# Servizi failed
systemctl --failed

# Log errori ultime 24h
journalctl --since "24 hours ago" -p err -n 30

# Load average
cat /proc/loadavg
# Formato: 1min 5min 15min jobs-running jobs-total pid

# Processi che consumano più memoria
ps aux --sort=-%mem | head -5

# File più grandi (utile per pulizia disco)
find / -type f -size +100M -printf '%s\t%p\n' 2>/dev/null | sort -rn | head -10
```

---

## Appendice B: SOP "Programma di Manutenzione Preventiva"

```markdown
# SOP MAINT-001: Programma di Manutenzione Preventiva

**Versione:** 1.0  
**Scope:** Infrastruttura IT Lab IT Corporation  
**Frequenza revisione SOP:** Trimestrale  

## 1. Calendario Esecuzione

| Cadenza | Giorno/Ora | Strumento | Responsabile |
|---|---|---|---|
| Giornaliera | Lun-Ven 07:30 | Task Scheduler (auto) + review manuale | IT Ops |
| Settimanale | Lunedì 08:30 | weekly_checklist_interactive.ps1 | IT Ops |
| Mensile | Prima settimana mese | Checklist mensile (da SOP MAINT-002) | IT Lead |
| Trimestrale | Gen/Apr/Lug/Ott | Checklist trimestrale (da SOP MAINT-003) | IT Lead + Management |
| Annuale | Dicembre | DR drill + assessment sicurezza | IT Team |

## 2. Escalation Matrix

| Risultato Checklist | Azione | Entro |
|---|---|---|
| WARN su un item | Monitora, agenda follow-up in 3 giorni | 24h |
| FAIL su un item non critico | Ticket GLPI P3, risoluzione entro 1 settimana | 4h |
| FAIL su servizio critico | Ticket GLPI P2, contatta team lead | 30 min |
| FAIL su servizio business-critical | Ticket GLPI P1, procedure incident management | 15 min |

## 3. Archiviazione Report

I log di manutenzione sono conservati per 12 mesi in:
- Windows: `C:\MaintLogs\` su DC-LAB-01
- Linux: `~/maint-logs/` su SRV-LINUX-01
- GLPI: ticket aperti dalla checklist, con tag "maintenance"
```

---

## Riferimenti

| Risorsa | Posizione | Contenuto |
|---|---|---|
| Documento sorgente | `../02-manutenzione-preventiva.md` | Guida completa manutenzione preventiva |
| ITIL 4: Capacity Practice | axelos.com | Capacity and Performance Management |
| Microsoft Task Scheduler | docs.microsoft.com | Schedulazione Windows Server |
| Cron man page | `man crontab` (da terminale) | Sintassi cron Linux |
| Tutorial ops00 | `tutorial_ops00_ch1_day_one_it_ops_lab.md` | Setup lab di base |
| Tutorial ops01a | `tutorial_ops01_ch1a_itil_foundations_lab.md` | Framework ITIL |
| Tutorial successivo (02b) | `tutorial_ops02_ch1b_monthly_annual_predictive_lab.md` | Manutenzione mensile/annuale e predittiva |

---

*Fine tutorial ops02a — Prossimo: `tutorial_ops02_ch1b_monthly_annual_predictive_lab.md`*
