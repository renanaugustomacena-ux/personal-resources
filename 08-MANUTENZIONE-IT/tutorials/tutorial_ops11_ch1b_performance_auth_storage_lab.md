# Tutorial: Troubleshooting Avanzato — Performance, Autenticazione e Storage

> **Documento di riferimento:** `11-troubleshooting-generale.md` (sezioni 4-9)
> **Dominio:** Troubleshooting Generale IT (Dominio 11)
> **Ambito:** CPU, RAM, disco, rete, Active Directory, LDAP/SSO, storage, email, stampa, strumenti diagnostici
> **Durata lab:** 8-10 ore (suddivise in 3 sessioni)
> **Livello:** Da intermedio (Parte A) ad avanzato (Parte C)
> **Prerequisiti:** `tutorial_ops11_ch1a_methodology_network_lab.md` (metodologia base + troubleshooting rete)
> **Ambiente:** Lab isolato — DC-LAB-01 (Windows Server 2022) + SRV-LINUX-01 (Ubuntu 22.04)

---

## Analogia Iniziale: Il Medico Specialista

Nel tutorial precedente hai imparato il metodo del medico di base: anamnesi, esame obiettivo, diagnosi differenziale. Questo tutorial è il lavoro del **medico specialista**: non si tratta più di "il paziente ha la febbre" (rete non funziona), ma di diagnosi precise su organi specifici.

Il cardiologo sa come leggere un ECG e interpretare ogni picco. Il nefrologo sa riconoscere i pattern di insufficienza renale dalle analisi del sangue. L'endocrinologo sa leggere la storia ormonale nel tempo.

Tu diventerai uno specialista IT:
- **CPU/RAM/Disco** → nefrologo: analizza cosa consuma le risorse e perché
- **Active Directory** → cardiologo: il cuore dell'autenticazione aziendale
- **Storage** → chirurgo: interviene prima che il danno sia irreversibile
- **Email** → pneumologo: il flusso della posta come il flusso del respiro

---

## Lab Environment Setup

### Requisiti

| Componente | Minimo | Raccomandato |
|---|---|---|
| DC-LAB-01 (Windows Server 2022) | 2 vCPU / 4 GB RAM | 4 vCPU / 8 GB RAM |
| SRV-LINUX-01 (Ubuntu 22.04) | 2 vCPU / 4 GB RAM | 4 vCPU / 8 GB RAM |

### Topologia

```
┌─────────────────────────────────────────────────────────────┐
│                   Rete Lab: 192.168.56.0/24                 │
│                                                             │
│  ┌──────────────────┐      ┌──────────────────────────┐    │
│  │   DC-LAB-01      │      │      SRV-LINUX-01         │    │
│  │ 192.168.56.10    │      │    192.168.56.20           │    │
│  │                  │      │                           │    │
│  │  AD DS, DNS      │      │  Apache :80               │    │
│  │  DHCP            │      │  MySQL/PostgreSQL :3306   │    │
│  │  Print Server    │      │  Prometheus :9090         │    │
│  │  WSUS            │      │  Grafana :3000            │    │
│  └──────────────────┘      └──────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Setup Lab per Questo Tutorial

```powershell
# Su DC-LAB-01 — Setup utenti e servizi per i test

# Creare OU e utenti di test
New-ADOrganizationalUnit -Name "Lab-Users" -Path "DC=lab,DC=local" -ProtectedFromAccidentalDeletion $false
New-ADUser -Name "TestUser01" -SamAccountName "testuser01" -UserPrincipalName "testuser01@lab.local" `
    -Path "OU=Lab-Users,DC=lab,DC=local" -AccountPassword (ConvertTo-SecureString "P@ssw0rd123!" -AsPlainText -Force) `
    -Enabled $true

# Creare account di servizio per i test LDAP
New-ADUser -Name "svc-ldap" -SamAccountName "svc-ldap" -UserPrincipalName "svc-ldap@lab.local" `
    -Path "CN=Users,DC=lab,DC=local" -AccountPassword (ConvertTo-SecureString "Svc!Ldap2026" -AsPlainText -Force) `
    -Enabled $true -PasswordNeverExpires $true

# Installare una stampante virtuale
Add-PrinterPort -Name "10.0.0.200" -PrinterHostAddress "10.0.0.200"
Add-PrinterDriver -Name "Generic / Text Only"
Add-Printer -Name "LAB-PRN-01" -DriverName "Generic / Text Only" -PortName "10.0.0.200"
```

```bash
# Su SRV-LINUX-01 — Setup servizi Linux per i test

# Installare strumenti di monitoring e test
sudo apt-get update -qq
sudo apt-get install -y sysstat iotop htop nmon stress-ng ldap-utils mailutils

# Simulare carico CPU (5 minuti) per generare dati storici
stress-ng --cpu 2 --timeout 300 &

# Riempire un file di test per il disco
dd if=/dev/zero of=/tmp/testfile bs=1M count=500 status=progress

# Installare servizio email per test SMTP
sudo apt-get install -y postfix
sudo systemctl start postfix
```

---

## PART A: FONDAMENTI — Capire le Cause dei Problemi

### Concetto A1: Performance — Dove Guardare Prima

**Analogia**: Un'auto che non va come dovrebbe può avere il motore in difficoltà (CPU), il serbatoio quasi vuoto (RAM), la trasmissione bloccata (disco I/O), o la strada congestionata (rete). Controllare l'ago del carburante (RAM disponibile) è il primo passo, non smontare il motore.

**L'ordine di diagnosi performance:**

```
1. DISPONIBILITÀ IMMEDIATA: c'è RAM libera? c'è CPU libera?
   └─ No → trovare il consumatore → decidere se è legittimo

2. TREND: il problema è improvviso o graduale?
   └─ Improvviso → evento scatenante (deployment, picco, bug)
   └─ Graduale → crescita organica, memory leak, frammentazione

3. ISOLAMENTO: quale processo? quale server? quale servizio?
   └─ Identificare il PID → analizzare il processo → decisione

4. BASELINE: il valore attuale è normale o anomalo?
   └─ Senza baseline storica non puoi rispondere a questa domanda
```

**Metriche e soglie:**

| Risorsa | Normale | Attenzione | Critico | Strumento |
|---|---|---|---|---|
| CPU (media) | < 50% | 50-70% | > 70% | `top`, `htop`, `Get-Counter` |
| CPU (picco) | fino a 100% momentaneo | > 95% per > 5 min | > 95% costante | `sar -u`, `perfmon` |
| RAM utilizzata | < 70% | 70-85% | > 85% | `free -h`, `Get-Process` |
| Swap in uso | 0 | < 10% | > 20% | `vmstat`, `swapon -s` |
| Disk queue | < 1 (HDD), < 8 (SSD) | 1-2 (HDD) | > 2 (HDD) | `iostat -x`, `perfmon` |
| Disk latency | < 5ms (SSD), < 20ms (HDD) | 20-50ms | > 50ms | `iostat -x` (await) |

### Concetto A2: Active Directory — Il Cuore dell'Autenticazione

**Analogia**: Active Directory è come l'ufficio anagrafe di un comune: registra chi siete (account), dove abitate (OU), a quali gruppi appartenete. Quando l'ufficio anagrafe ha problemi (AD in trouble), nessuno riesce a "registrarsi" (autenticarsi) in alcun sistema.

**Flusso di autenticazione AD:**

```
Utente inserisce password
       ↓
Client Windows contatta Domain Controller
       ↓
   Kerberos AS-REQ: "Voglio un ticket per autenticarmi"
       ↓
   DC verifica password → emette TGT (Ticket Granting Ticket)
       ↓
   Client usa TGT per richiedere Service Ticket
       ↓
   Service Ticket presentato al servizio (file server, mail, web)
       ↓
   Accesso concesso

Se qualcosa si rompe in questo flusso → problemi di autenticazione
```

**Cause più comuni dei problemi AD:**
- **Account lockout**: tentativi di login ripetuti (password salvata vecchia)
- **Time skew**: differenza > 5 minuti tra client e DC invalida tutti i ticket Kerberos
- **Replica non funzionante**: utenti creati su DC1 non visibili su DC2
- **Trust relationship rotta**: la password condivisa tra computer e dominio è desincronizzata

### Concetto A3: Storage — Prevenire è Meglio che Curare

**Analogia**: Lo storage è come il disco rigido del tuo computer, ma per un intero datacenter. Quando si riempie, non è come quando si riempie il tuo disco personale (potresti solo non riuscire a scaricare un film): si bloccano i database, i log smettono di scrivere, e in alcuni casi il sistema operativo si congela.

**Tre categorie di problemi storage:**

```
1. SPAZIO DISCO ESAURITO
   → Impatto: immediato e catastrofico
   → Causa tipica: log cresciuti, database espansi, file temporanei
   → Prevenzione: alert a 75%, capacity planning mensile

2. PERFORMANCE I/O DEGRADATA
   → Impatto: graduale (applicazioni lente, timeout)
   → Causa tipica: carico eccessivo su HDD, RAID rebuild in corso
   → Prevenzione: migrate a SSD, monitorare disk queue

3. RAID DEGRADATO O IN GUASTO
   → Impatto: alta disponibilità a rischio, nessun secondo guasto tollerabile
   → Causa tipica: disco guasto (SMART warning precedente ignorato)
   → Prevenzione: monitorare SMART, alert RAID controller, sostituzione preventiva
```

### Concetto A4: Email — Diagnosticare il Flusso

**Analogia**: Il sistema email è come il servizio postale: una lettera può non arrivare perché il mittente non ha scritto l'indirizzo bene (SPF/DKIM failure), perché la cassetta della posta è piena (mailbox quota), perché il postino non riesce a raggiungere l'indirizzo (DNS/rete), o perché la lettera è stata sequestrata dalla dogana (spam filter).

**I layer del flusso email:**

```
Mittente → Client SMTP (Outlook)
         → Server SMTP mittente (Exchange, Postfix)
         → DNS lookup: record MX del destinatario
         → Connessione SMTP al server destinazione (porta 25)
         → Verifica SPF/DKIM/DMARC
         → Delivery nella mailbox
         → Client IMAP/POP3 del destinatario scarica il messaggio
```

Ogni freccia è un potenziale punto di guasto da verificare sistematicamente.

---

## PART B: OPERAZIONI — Diagnosi Pratica dei Problemi

### Esercizio B1: Diagnosi CPU Alta e Memory Leak

**Obiettivo.** Identificare il processo responsabile di CPU alta, analizzarne l'origine, e rilevare un potenziale memory leak.

**Step 1 — Simulare carico elevato su SRV-LINUX-01**

```bash
# Avviare un processo che consuma CPU e RAM in modo controllato
stress-ng --cpu 2 --vm 1 --vm-bytes 512M --timeout 180 &
echo "Stress test PID: $!"

# Attendere 10 secondi per stabilizzare il carico
sleep 10
```

**Step 2 — Identificare il consumatore di CPU**

```bash
# Metodo 1: top (interattivo)
top -bn1 -o %CPU | head -15
# Output: lista processi ordinati per CPU, con PID

# Metodo 2: ps con ordinamento (non interattivo, per script)
ps aux --sort=-%cpu | head -10
echo "---"
ps aux --sort=-%mem | head -10

# Metodo 3: pidstat (da sysstat) — mostra trend per PID
pidstat -u 5 3   # ogni 5 secondi, 3 iterazioni
```

**Output atteso:**
```
USER       PID %CPU %MEM    VSZ   RSS COMMAND
root      4821 99.3  3.2 128440 65792 stress-ng--cpu
root      4822 98.1  0.1  12340  3456 stress-ng--vm
root      4823 35.2  2.0  87200 42100 java
```

**Step 3 — Analizzare il PID sospetto**

```bash
# Supponiamo PID=4823 (processo Java sospetto)
TARGET_PID=4823

# Informazioni base sul processo
cat /proc/${TARGET_PID}/status | grep -E "Name|VmRSS|VmPeak|Threads"

# File aperti dal processo
ls -la /proc/${TARGET_PID}/fd 2>/dev/null | head -20

# Connessioni di rete del processo (malware usa spesso connessioni sospette)
ss -tlnp | grep ${TARGET_PID}

# Path dell'eseguibile (importante per rilevare malware)
readlink -f /proc/${TARGET_PID}/exe
```

**Step 4 — Monitorare un memory leak nel tempo**

```python
#!/usr/bin/env python3
"""
watch_memory_leak.py — Monitora il consumo di RAM di un processo nel tempo.
Segnala se il processo mostra una crescita lineare costante (probabile memory leak).
"""

import subprocess
import time
from dataclasses import dataclass


@dataclass
class MemSample:
    timestamp: float
    rss_mb: float


def get_process_rss_mb(pid: int) -> float | None:
    """Legge RSS (Resident Set Size) di un processo in MB."""
    try:
        with open(f"/proc/{pid}/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    kb = int(line.split()[1])
                    return kb / 1024
    except FileNotFoundError:
        return None
    return None


def linear_trend(samples: list[MemSample]) -> float:
    """Calcola la pendenza del trend lineare (MB/minuto)."""
    if len(samples) < 3:
        return 0.0
    n = len(samples)
    t0 = samples[0].timestamp
    xs = [(s.timestamp - t0) / 60 for s in samples]  # in minuti
    ys = [s.rss_mb for s in samples]
    sum_x = sum(xs)
    sum_y = sum(ys)
    sum_xy = sum(x * y for x, y in zip(xs, ys))
    sum_x2 = sum(x ** 2 for x in xs)
    denom = n * sum_x2 - sum_x ** 2
    if abs(denom) < 1e-9:
        return 0.0
    return (n * sum_xy - sum_x * sum_y) / denom


def watch_process(pid: int, interval_sec: int = 30, duration_min: int = 10) -> None:
    samples: list[MemSample] = []
    print(f"Monitoraggio PID {pid} per {duration_min} minuti (ogni {interval_sec}s)")
    print(f"{'Ora':>10}  {'RAM (MB)':>10}  {'Trend':>15}")
    print("-" * 40)

    iterations = (duration_min * 60) // interval_sec
    for _ in range(iterations):
        rss = get_process_rss_mb(pid)
        if rss is None:
            print(f"PID {pid} non trovato — processo terminato?")
            break
        sample = MemSample(timestamp=time.time(), rss_mb=rss)
        samples.append(sample)
        trend = linear_trend(samples)
        trend_str = f"+{trend:.1f} MB/min" if trend > 0.1 else (f"{trend:.1f} MB/min" if trend < -0.1 else "stabile")
        print(f"{time.strftime('%H:%M:%S'):>10}  {rss:>10.1f}  {trend_str:>15}")
        time.sleep(interval_sec)

    if len(samples) >= 3:
        final_trend = linear_trend(samples)
        print("\n--- DIAGNOSI ---")
        if final_trend > 1.0:
            print(f"ATTENZIONE: Probabile memory leak! Crescita {final_trend:.1f} MB/minuto")
            print(f"  Al ritmo attuale: +{final_trend*60:.0f} MB/ora")
        elif final_trend > 0.2:
            print(f"Crescita moderata: {final_trend:.1f} MB/min — monitorare")
        else:
            print(f"Memoria stabile — nessun leak rilevato")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print(f"Uso: {sys.argv[0]} <PID>")
        sys.exit(1)
    watch_process(int(sys.argv[1]), interval_sec=10, duration_min=3)
```

```bash
# Eseguire il monitor su un processo di test
stress-ng --vm 1 --vm-bytes 100M --vm-keep --timeout 120 &
STRESS_PID=$!

python3 /opt/reporting/scripts/watch_memory_leak.py ${STRESS_PID}
```

**Step 5 — Stesso esercizio su Windows**

```powershell
# Su DC-LAB-01 — Identificare processi con CPU alta
Get-Process | Sort-Object CPU -Descending | Select-Object -First 10 `
    Name, Id, CPU, @{N='RAM_MB';E={[math]::Round($_.WorkingSet64/1MB,0)}}

# Monitorare crescita RAM di un processo nel tempo (60 iterazioni × 5s = 5 minuti)
$process_name = "svchost"   # Cambia con il processo da monitorare
1..60 | ForEach-Object {
    $p = Get-Process -Name $process_name -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($p) {
        $ts = Get-Date -Format "HH:mm:ss"
        $mb = [math]::Round($p.WorkingSet64 / 1MB, 1)
        Write-Host "$ts  $($p.Name)  RAM: $mb MB"
    }
    Start-Sleep -Seconds 5
}
```

---

### Esercizio B2: Diagnosi Active Directory — Account Lockout e Replica

**Obiettivo.** Trovare la sorgente di un account lockout ripetuto, verificare lo stato della replica AD, e diagnosticare problemi Kerberos.

**Step 1 — Simulare e diagnosticare un account lockout**

```powershell
# Su DC-LAB-01

# Prima: configurare la policy di lockout nel lab (per i test)
# Fine Account Lockout Policy: 3 tentativi, lockout per 10 minuti
Set-ADDefaultDomainPasswordPolicy -LockoutThreshold 3 -LockoutDuration (New-TimeSpan -Minutes 10) -LockoutObservationWindow (New-TimeSpan -Minutes 5)

# Simulare un lockout (eseguire da WKS-LAB-01 o PowerShell con credenziali errate)
# Nota: fallo solo nell'ambiente lab, non in produzione
for ($i = 1; $i -le 4; $i++) {
    $cred = New-Object System.Management.Automation.PSCredential("lab\testuser01", (ConvertTo-SecureString "WrongPassword$i" -AsPlainText -Force))
    try { Invoke-Command -ComputerName DC-LAB-01 -Credential $cred -ScriptBlock { whoami } -ErrorAction SilentlyContinue }
    catch { Write-Host "Tentativo $i fallito (atteso)" }
}

# Verificare che l'account sia bloccato
Get-ADUser -Identity testuser01 -Properties LockedOut, BadLogonCount, LastBadPasswordAttempt |
    Select-Object SamAccountName, LockedOut, BadLogonCount, LastBadPasswordAttempt
```

**Step 2 — Trovare la sorgente del lockout dal Security Log**

```powershell
# Trovare l'evento 4740 (account locked out) sul PDC Emulator
$PDC = (Get-ADDomain).PDCEmulator
Write-Host "PDC Emulator: $PDC"

# Cercare eventi di lockout nelle ultime 24 ore
Get-WinEvent -ComputerName $PDC -FilterHashtable @{
    LogName = 'Security'
    Id = 4740
    StartTime = (Get-Date).AddDays(-1)
} -ErrorAction SilentlyContinue |
    Select-Object TimeCreated,
        @{N='Account';E={$_.Properties[0].Value}},
        @{N='CallerComputer';E={$_.Properties[1].Value}} |
    Format-Table -AutoSize

# Trovare eventi di logon failure (4625) — cercare il processo responsabile
Get-WinEvent -FilterHashtable @{
    LogName = 'Security'
    Id = 4625
    StartTime = (Get-Date).AddHours(-2)
} -ErrorAction SilentlyContinue |
    Select-Object -First 20 TimeCreated,
        @{N='AccountName';E={$_.Properties[5].Value}},
        @{N='WorkstationName';E={$_.Properties[13].Value}},
        @{N='FailureReason';E={$_.Properties[9].Value}} |
    Format-Table -AutoSize
```

**Step 3 — Sbloccare l'account e verificare**

```powershell
# Sbloccare l'account
Unlock-ADAccount -Identity testuser01

# Verificare sblocco
Get-ADUser -Identity testuser01 -Properties LockedOut | Select-Object SamAccountName, LockedOut

# Checklist: dove aggiornare la password
Write-Host @"
CHECKLIST DOPO CAMBIO PASSWORD:
  [ ] Aggiornare credenziali salvate su tutti i dispositivi mobili
  [ ] Aggiornare le unità di rete mappate con credenziali salvate
  [ ] Aggiornare i servizi Windows che usano questo account
  [ ] Aggiornare i task schedulati
  [ ] Verificare le sessioni RDP disconnesse (usano ancora il vecchio token)
"@
```

**Step 4 — Verificare lo stato della replica AD**

```powershell
# Riepilogo della replica
repadmin /replsummary

# Dettaglio per ogni Domain Controller
repadmin /showrepl

# Verificare la coda di replica
repadmin /queue

# Diagnostica completa del Domain Controller
dcdiag /test:replications /v

# Forzare la replica se bloccata
# repadmin /syncall /AdeP
```

**Output atteso di repadmin /replsummary:**
```
Replication Summary Start Time: 2026-07-15 14:30:00

Beginning data collection for replication summary, this may take awhile:

Source DSA          largest delta    fails/total %%   error
 DC-LAB-01           00m:15s    0 /   5    0
 
Destination DSA     largest delta    fails/total %%   error
 DC-LAB-01           00m:15s    0 /   5    0
```

**Step 5 — Diagnosi Kerberos e Time Skew**

```powershell
# Verificare i ticket Kerberos correnti
klist

# Verificare la sincronizzazione temporale
w32tm /query /status

# Confrontare l'ora con il DC (la differenza deve essere < 5 minuti)
$dcTime = (Get-Date -ComputerName DC-LAB-01).ToUniversalTime()
$localTime = (Get-Date).ToUniversalTime()
$skewSeconds = [math]::Abs(($dcTime - $localTime).TotalSeconds)
Write-Host "Time skew vs DC: $skewSeconds secondi"
if ($skewSeconds -gt 300) {
    Write-Host "CRITICO: Time skew > 5 minuti! Kerberos non funzionerà correttamente!"
} elseif ($skewSeconds -gt 60) {
    Write-Host "ATTENZIONE: Time skew > 1 minuto — monitorare"
} else {
    Write-Host "OK: Time skew entro limiti"
}
```

---

### Esercizio B3: Diagnosi Storage — Spazio Disco e SMART

**Obiettivo.** Identificare le directory che consumano più spazio, rilevare i problemi comuni (log, DB, shadow copy), e verificare la salute dei dischi tramite SMART.

**Step 1 — Trovare i consumatori di spazio su Linux**

```bash
# Panoramica generale dei filesystem
df -h

# I top 20 consumatori sotto /var (dove vivono log e DB)
du -sh /var/* 2>/dev/null | sort -rh | head -20

# Trovare file creati di recente che potrebbero spiegare il consumo
find /var -type f -newer /var/log/syslog -size +100M 2>/dev/null

# Strumento interattivo (navigazione)
ncdu /var   # se installato: apt install ncdu

# Verificare log che crescono senza rotazione
ls -lh /var/log/*.log | sort -k5 -rh | head -10
```

**Step 2 — Pulizia sicura**

```bash
# Pulire package cache (sicuro)
sudo apt-get clean
sudo apt-get autoremove -y

# Verificare e configurare logrotate
cat /etc/logrotate.d/apache2  # o il servizio di interesse

# Svuotare journal di systemd (mantenere solo ultimi 500 MB)
sudo journalctl --vacuum-size=500M

# Verificare file temporanei vecchi (più di 7 giorni)
find /tmp -type f -atime +7 -size +10M -exec ls -lh {} \;
# Per eliminare (con attenzione):
# find /tmp -type f -atime +7 -delete
```

**Step 3 — Trovare i consumatori di spazio su Windows**

```powershell
# Spazio per volume
Get-PSDrive -PSProvider FileSystem | Select-Object Name,
    @{N='Used_GB';E={[math]::Round($_.Used/1GB,2)}},
    @{N='Free_GB';E={[math]::Round($_.Free/1GB,2)}},
    @{N='Used_PCT';E={[math]::Round($_.Used/($_.Used+$_.Free)*100,1)}}

# Top 20 directory per dimensione (lento su directory grandi)
function Get-DirSize {
    param([string]$Path = "C:\")
    Get-ChildItem $Path -ErrorAction SilentlyContinue |
        ForEach-Object { $_ | Add-Member -MemberType NoteProperty -Name 'Size' `
            -Value ((Get-ChildItem $_.FullName -Recurse -ErrorAction SilentlyContinue |
            Measure-Object Length -Sum).Sum) -PassThru } |
        Sort-Object Size -Descending | Select-Object -First 20 Name, @{N='Size_MB';E={[math]::Round($_.Size/1MB,0)}}
}
Get-DirSize -Path "C:\"

# Verificare Shadow Copy (VSS) — spesso occupa molto spazio
vssadmin list shadowstorage
vssadmin list shadows
```

**Step 4 — Verifica salute disco con SMART (Linux)**

```bash
# Installare smartmontools se non presente
sudo apt-get install -y smartmontools

# Verificare la salute del disco principale
sudo smartctl -a /dev/sda

# Valori SMART critici da controllare:
# ID 5:  Reallocated Sectors Count — settori riassegnati (deve essere 0)
# ID 187: Reported Uncorrectable Errors
# ID 197: Current Pending Sector Count — settori in attesa di riassegnazione
# ID 198: Off-Line Uncorrectable Sector Count
# CRITICAL se QUESTI aumentano nel tempo → guasto imminente

# Test veloce (3-5 minuti)
sudo smartctl -t short /dev/sda
sleep 300
sudo smartctl -l selftest /dev/sda
```

**Step 5 — Monitorare I/O con iostat**

```bash
# Statistiche I/O estese (ogni 5 secondi, 3 iterazioni)
iostat -x 5 3

# Interpretare l'output:
# await: latenza media I/O in ms (< 5ms ottimo, < 20ms OK, > 50ms problema)
# util: utilizzo del disco in % (> 80% = disco saturo)
# r/s e w/s: operazioni al secondo
```

**Output atteso iostat:**
```
Device  r/s  w/s  rMB/s  wMB/s  await  %util
sda     2.5  8.3   0.15   0.42    1.2    4.2

# Disco sano: await < 5ms, util < 50%
```

---

### Esercizio B4: Diagnosi Email — Flusso e Problemi DNS

**Obiettivo.** Verificare il flusso email su Postfix, diagnosticare i record DNS (MX, SPF, DKIM), e testare la connettività SMTP.

**Step 1 — Verificare lo stato di Postfix**

```bash
# Stato del servizio
sudo systemctl status postfix

# Verificare la coda di posta (messaggi in attesa)
mailq
# oppure
postqueue -p

# Log recenti del servizio email
sudo tail -50 /var/log/mail.log
sudo tail -50 /var/log/mail.err

# Statistiche della coda
postqueue -p | awk 'BEGIN{n=0} /^[A-Z0-9]/{n++} END{print "Messaggi in coda:", n}'
```

**Step 2 — Testare il flusso SMTP manualmente**

```bash
# Test connessione SMTP a un server esterno (simulazione)
# In lab, testiamo verso localhost
telnet localhost 25
# Risposta attesa: "220 srv-linux-01.lab.local ESMTP Postfix"
# Poi:
# EHLO lab.local
# MAIL FROM:<test@lab.local>
# RCPT TO:<admin@lab.local>
# DATA
# Subject: Test SMTP
# Test body
# .
# QUIT

# Versione automatizzata con netcat
printf "EHLO lab.local\nMAIL FROM:<test@lab.local>\nRCPT TO:<admin@lab.local>\nDATA\nSubject: Test\n\nTest body\n.\nQUIT\n" | \
    nc -q 3 localhost 25
```

**Step 3 — Verificare record DNS per email**

```bash
# In un ambiente reale, sostituire "contoso.com" con il dominio del lab
DOMAIN="lab.local"

echo "=== Record MX ==="
dig MX ${DOMAIN} || nslookup -type=mx ${DOMAIN}

echo "=== Record SPF (TXT) ==="
dig TXT ${DOMAIN} | grep "v=spf"

echo "=== Verifica raggiungibilità server MX ==="
MX_SERVER=$(dig +short MX ${DOMAIN} | awk '{print $2}' | head -1)
if [ -n "$MX_SERVER" ]; then
    echo "MX server: $MX_SERVER"
    nc -zv "$MX_SERVER" 25 && echo "Porta 25: APERTA" || echo "Porta 25: CHIUSA/FILTRATA"
else
    echo "Nessun record MX trovato per ${DOMAIN}"
fi
```

**Step 4 — Script di diagnosi email completa**

```python
#!/usr/bin/env python3
"""
email_diagnostics.py — Diagnosi completa del flusso email.
Verifica DNS, connettività SMTP, stato coda, log recenti.
"""

import subprocess
import socket
from pathlib import Path


def run(cmd: list[str]) -> str:
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    return result.stdout + result.stderr


def check_smtp_port(host: str, port: int = 25, timeout: int = 5) -> bool:
    try:
        s = socket.create_connection((host, port), timeout=timeout)
        banner = s.recv(256).decode("utf-8", errors="replace")
        s.close()
        return "220" in banner
    except Exception:
        return False


def check_mail_queue() -> int:
    output = run(["postqueue", "-p"])
    lines = [l for l in output.splitlines() if l and l[0].isalnum()]
    return len(lines)


def check_recent_errors(log_path: str = "/var/log/mail.err", lines: int = 10) -> list[str]:
    try:
        content = Path(log_path).read_text(errors="replace")
        return content.splitlines()[-lines:]
    except FileNotFoundError:
        return [f"Log non trovato: {log_path}"]


def main() -> None:
    print("=" * 60)
    print("DIAGNOSI EMAIL — REPORT")
    print("=" * 60)

    # 1. Stato del servizio
    service_status = run(["systemctl", "is-active", "postfix"]).strip()
    icon = "✅" if service_status == "active" else "❌"
    print(f"\n{icon} Servizio Postfix: {service_status}")

    # 2. Coda di posta
    queue_size = check_mail_queue()
    icon = "✅" if queue_size == 0 else ("⚠️ " if queue_size < 10 else "❌")
    print(f"{icon} Messaggi in coda: {queue_size}")

    # 3. Connettività SMTP locale
    smtp_ok = check_smtp_port("localhost", 25)
    icon = "✅" if smtp_ok else "❌"
    print(f"{icon} SMTP porta 25 locale: {'raggiungibile' if smtp_ok else 'NON raggiungibile'}")

    # 4. Log recenti
    print(f"\n📋 Ultimi errori da /var/log/mail.err:")
    errors = check_recent_errors()
    for line in errors:
        print(f"   {line}")

    # 5. Configurazione relay
    main_cf = Path("/etc/postfix/main.cf")
    if main_cf.exists():
        config = main_cf.read_text()
        mydestination = [l for l in config.splitlines() if l.startswith("mydestination")]
        mynetworks = [l for l in config.splitlines() if l.startswith("mynetworks")]
        print(f"\n📋 Configurazione Postfix:")
        for line in mydestination + mynetworks:
            print(f"   {line}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
```

```bash
python3 /opt/reporting/scripts/email_diagnostics.py
```

---

### Esercizio B5: Diagnosi Problemi di Stampa

**Obiettivo.** Diagnosticare i problemi più comuni del Print Spooler e delle stampanti di rete.

```powershell
# Su DC-LAB-01

# Step 1: Verificare stato spooler
Get-Service Spooler | Select-Object Name, Status, StartType

# Step 2: Visualizzare le stampanti installate
Get-Printer | Select-Object Name, PortName, DriverName, PrinterStatus

# Step 3: Verificare la coda di stampa
Get-PrintJob -PrinterName "LAB-PRN-01" -ErrorAction SilentlyContinue | 
    Select-Object JobStatus, Document, UserName, TotalPages

# Step 4: Script di fix automatico per spooler bloccato
function Reset-PrintSpooler {
    param([switch]$Force)
    
    Write-Host "Arresto Print Spooler..."
    Stop-Service Spooler -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    
    Write-Host "Verifica file coda di stampa..."
    $spoolDir = "C:\Windows\System32\spool\PRINTERS"
    $files = Get-ChildItem $spoolDir -ErrorAction SilentlyContinue
    if ($files.Count -gt 0) {
        Write-Host "Trovati $($files.Count) file in coda"
        if ($Force) {
            $files | Remove-Item -Force -ErrorAction SilentlyContinue
            Write-Host "File rimossi"
        } else {
            Write-Host "Aggiungere -Force per rimuovere i file"
        }
    } else {
        Write-Host "Coda vuota"
    }
    
    Write-Host "Avvio Print Spooler..."
    Start-Service Spooler
    $status = (Get-Service Spooler).Status
    Write-Host "Stato finale Spooler: $status"
}

# Eseguire il fix (in lab)
Reset-PrintSpooler -Force

# Step 5: Testare connettività verso stampante di rete
Test-NetConnection -ComputerName "10.0.0.200" -Port 9100   # Porta RAW
Test-NetConnection -ComputerName "10.0.0.200" -Port 631    # Porta IPP
```

---

### Esercizio B6: Strumenti Diagnostici Avanzati — strace e Sysinternals

**Obiettivo.** Usare strace su Linux e Process Monitor su Windows per capire esattamente cosa fa un processo.

**Step 1 — strace su Linux: tracciare le system call**

```bash
# Avviare un processo di test da tracciare
cat /tmp/missing_file.txt &   # Genera un errore FileNotFoundError
MISSING_PID=$!

# Tracciare le system call del processo (cattura dopo l'avvio)
strace -p ${MISSING_PID} -e trace=open,read,write,openat 2>&1 | head -30

# In alternativa, tracciare dall'inizio
strace -e trace=network -f curl http://localhost 2>&1 | grep connect

# Conteggio delle system call (utile per profiling)
strace -c ls /var/log 2>&1
```

**Output atteso strace:**
```
execve("/bin/cat", ["cat", "/tmp/missing_file.txt"], 0x... /* N vars */) = 0
...
openat(AT_FDCWD, "/tmp/missing_file.txt", O_RDONLY) = -1 ENOENT (No such file or directory)
write(2, "cat: /tmp/missing_file.txt: No s"..., 44) = 44
...
```

**Step 2 — lsof: chi ha quali file aperti**

```bash
# Trovare quale processo ha un file aperto (utile per "file in uso")
sudo lsof /var/log/syslog

# Trovare tutti i file aperti da un processo
sudo lsof -p $(pgrep apache2 | head -1) | head -20

# Trovare chi sta usando una porta specifica
sudo lsof -i :80

# File aperti in una directory
sudo lsof +D /var/log | head -20
```

**Step 3 — Process Monitor su Windows (simulazione tramite PowerShell)**

```powershell
# Tracciare le operazioni di file system di un processo
# (equivalente base di Process Monitor via PowerShell)
$targetProcess = "notepad"

# Avviare notepad per il test
Start-Process notepad.exe
Start-Sleep -Seconds 2

$pid = (Get-Process -Name $targetProcess -ErrorAction SilentlyContinue | Select-Object -First 1).Id
if ($pid) {
    # Visualizzare file handle aperti
    $handles = [System.Diagnostics.Process]::GetProcessById($pid).Modules |
        Select-Object ModuleName, FileName | Format-Table -AutoSize
    
    Write-Host "Moduli caricati da $targetProcess (PID: $pid):"
    [System.Diagnostics.Process]::GetProcessById($pid).Modules |
        Select-Object -First 10 ModuleName, FileName | Format-Table -AutoSize
}

# Fermare il processo di test
Stop-Process -Name notepad -ErrorAction SilentlyContinue
```

---

## PART C: SISTEMATIZZARE — Automazione della Diagnosi

### Progetto C1: Script di Health Check Completo

**Obiettivo.** Uno script che verifica automaticamente tutti i punti analizzati nel tutorial e produce un report.

```bash
cat > /opt/reporting/scripts/system_health_check.sh << 'SCRIPT'
#!/bin/bash
# system_health_check.sh — Health check completo del sistema

LOG=/tmp/health_check_$(date +%Y%m%d_%H%M%S).txt
THRESHOLD_CPU=70
THRESHOLD_MEM=85
THRESHOLD_DISK=80

log() { echo "$1" | tee -a "$LOG"; }
ok()  { log "  ✅ $1"; }
warn(){ log "  ⚠️  $1"; }
fail(){ log "  ❌ $1"; }

log "============================================"
log "  SYSTEM HEALTH CHECK — $(date)"
log "============================================"
log ""

# --- CPU ---
log "1. CPU"
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | tr -d '%us,' | cut -d'.' -f1)
if [ "${CPU_USAGE:-0}" -lt "$THRESHOLD_CPU" ]; then
    ok "CPU: ${CPU_USAGE}% (soglia: ${THRESHOLD_CPU}%)"
elif [ "${CPU_USAGE:-0}" -lt 85 ]; then
    warn "CPU: ${CPU_USAGE}% — sopra soglia warning"
else
    fail "CPU: ${CPU_USAGE}% — CRITICO"
fi
# Top 3 processi
log "  Top processi per CPU:"
ps aux --sort=-%cpu | head -4 | tail -3 | awk '{printf "    PID:%-6s CPU:%-6s %s\n", $2, $3, $11}' >> "$LOG"

log ""

# --- MEMORIA ---
log "2. MEMORIA"
MEM_INFO=$(free | grep Mem)
MEM_TOTAL=$(echo $MEM_INFO | awk '{print $2}')
MEM_USED=$(echo $MEM_INFO | awk '{print $3}')
MEM_PCT=$((MEM_USED * 100 / MEM_TOTAL))

if [ "$MEM_PCT" -lt "$THRESHOLD_MEM" ]; then
    ok "RAM: ${MEM_PCT}% (soglia: ${THRESHOLD_MEM}%)"
else
    fail "RAM: ${MEM_PCT}% — CRITICO"
fi

SWAP_USED=$(free | grep Swap | awk '{print $3}')
if [ "${SWAP_USED:-0}" -eq 0 ]; then
    ok "SWAP: non in uso"
else
    warn "SWAP: ${SWAP_USED} KB in uso"
fi

log ""

# --- DISCO ---
log "3. DISCO"
df -h | grep -E "^/dev" | while read line; do
    USAGE=$(echo "$line" | awk '{print $5}' | tr -d '%')
    MOUNT=$(echo "$line" | awk '{print $6}')
    DEV=$(echo "$line" | awk '{print $1}')
    if [ "${USAGE:-0}" -lt "$THRESHOLD_DISK" ]; then
        ok "${DEV} → ${MOUNT}: ${USAGE}%"
    elif [ "${USAGE:-0}" -lt 90 ]; then
        warn "${DEV} → ${MOUNT}: ${USAGE}% — sopra soglia warning"
    else
        fail "${DEV} → ${MOUNT}: ${USAGE}% — CRITICO"
    fi
done

log ""

# --- SERVIZI CRITICI ---
log "4. SERVIZI"
SERVICES=(ssh postfix cron)
for svc in "${SERVICES[@]}"; do
    STATUS=$(systemctl is-active "$svc" 2>/dev/null)
    if [ "$STATUS" = "active" ]; then
        ok "Servizio $svc: $STATUS"
    else
        fail "Servizio $svc: $STATUS"
    fi
done

log ""

# --- DISK I/O ---
log "5. DISK I/O"
AWAIT=$(iostat -x 1 1 2>/dev/null | awk '/^(sd|vd|hd|nvme)/ {print $1, $NF}' | head -3)
if [ -n "$AWAIT" ]; then
    echo "$AWAIT" | while read dev util; do
        UTIL_INT=${util%%.*}
        if [ "${UTIL_INT:-0}" -lt 80 ]; then
            ok "Disco $dev: utilizzo ${util}%"
        else
            warn "Disco $dev: utilizzo ${util}% — alto"
        fi
    done
else
    log "  iostat non disponibile o nessun dispositivo"
fi

log ""
log "Report salvato in: $LOG"
SCRIPT

chmod +x /opt/reporting/scripts/system_health_check.sh

# Eseguire il check
/opt/reporting/scripts/system_health_check.sh
```

### Progetto C2: Monitor Automatico di Active Directory

```powershell
# Su DC-LAB-01
# ad_health_monitor.ps1 — Monitoraggio salute AD

function Get-ADHealthReport {
    $report = [ordered]@{}
    
    # 1. Replica AD
    $replSummary = repadmin /replsummary 2>&1
    $replErrors = ($replSummary | Select-String "fails" | Where-Object { $_ -match "[1-9]\d*/\d+" }).Count
    $report["Replica AD"] = if ($replErrors -eq 0) { "OK" } else { "ERRORI: $replErrors" }
    
    # 2. Account bloccati
    $lockedUsers = (Get-ADUser -Filter {LockedOut -eq $true} -Properties LockedOut).Count
    $report["Account bloccati"] = if ($lockedUsers -eq 0) { "OK (0)" } else { "ATTENZIONE: $lockedUsers bloccati" }
    
    # 3. Password scadute
    $today = Get-Date
    $expiredPasswords = (Get-ADUser -Filter {Enabled -eq $true -and PasswordNeverExpires -eq $false} `
        -Properties PasswordLastSet, PasswordExpired | 
        Where-Object { $_.PasswordExpired -eq $true }).Count
    $report["Password scadute"] = if ($expiredPasswords -eq 0) { "OK (0)" } else { "ATTENZIONE: $expiredPasswords" }
    
    # 4. Sincronizzazione oraria
    $w32Status = w32tm /query /status 2>&1
    $stratum = ($w32Status | Select-String "Stratum" | Select-Object -First 1).ToString()
    $report["NTP Stratum"] = $stratum
    
    # 5. Domain Controller raggiungibile
    $dcPing = Test-Connection -ComputerName $env:LOGONSERVER.TrimStart("\\") -Count 1 -Quiet
    $report["DC pingabile"] = if ($dcPing) { "OK" } else { "ERRORE: DC non raggiungibile" }
    
    # Output report
    Write-Host "`n=== AD HEALTH REPORT — $(Get-Date -Format 'yyyy-MM-dd HH:mm') ===" -ForegroundColor Cyan
    $report.GetEnumerator() | ForEach-Object {
        $icon = if ($_.Value -like "OK*") { "✅" } elseif ($_.Value -like "ERRORE*") { "❌" } else { "⚠️ " }
        Write-Host "  $icon $($_.Key): $($_.Value)"
    }
}

Get-ADHealthReport
```

### Progetto C3: Dashboard degli Incidenti per Causa

```python
#!/usr/bin/env python3
"""
incident_cause_analysis.py — Analisi Pareto degli incidenti per causa radice.
Usa dati simulati o reali da GLPI per identificare le aree su cui intervenire.
"""

from collections import Counter
import json
from pathlib import Path

# Dati simulati (in produzione: recuperare da GLPI via API)
SAMPLE_INCIDENTS = [
    {"id": f"INC-{i:04d}", "category": cat, "priority": prio}
    for i, (cat, prio) in enumerate([
        ("Errore di configurazione", "P2"),
        ("Patch non applicato", "P2"),
        ("Errore di configurazione", "P3"),
        ("Capacity insufficiente", "P2"),
        ("Password/Cert scaduto", "P3"),
        ("Errore di configurazione", "P1"),
        ("Guasto hardware", "P1"),
        ("Patch non applicato", "P3"),
        ("Errore di configurazione", "P3"),
        ("Capacity insufficiente", "P3"),
        ("Password/Cert scaduto", "P2"),
        ("Errore di configurazione", "P3"),
        ("Bug software vendor", "P2"),
        ("Patch non applicato", "P2"),
        ("Capacity insufficiente", "P2"),
        ("Password/Cert scaduto", "P3"),
        ("Errore utente", "P3"),
        ("Errore di configurazione", "P3"),
        ("Guasto hardware", "P2"),
        ("Bug software vendor", "P3"),
    ] * 5)  # 100 incidenti simulati
]


def pareto_analysis(incidents: list[dict]) -> None:
    """Analisi Pareto degli incidenti per categoria."""
    total = len(incidents)
    category_counts = Counter(inc["category"] for inc in incidents)

    print(f"\n{'='*70}")
    print(f"  ANALISI PARETO INCIDENTI — {total} incidenti analizzati")
    print(f"{'='*70}")
    print(f"\n  {'Categoria':<35} {'Num':>5} {'%':>6}  {'Cum.%':>7}  Azione")
    print(f"  {'-'*65}")

    cumulative = 0.0
    for category, count in category_counts.most_common():
        pct = count / total * 100
        cumulative += pct
        action = "🔴 PRIORITÀ MASSIMA" if cumulative <= 80 else ("🟡 Monitorare" if cumulative <= 95 else "⚪ Minore")
        print(f"  {category:<35} {count:>5} {pct:>6.1f}%  {cumulative:>7.1f}%  {action}")

    print(f"\n  Il 20% delle categorie genera l'80% degli incidenti (principio Pareto).")
    print(f"  Concentrare le azioni sulle categorie con azione 🔴")

    print(f"\n{'='*70}")
    print("  RACCOMANDAZIONI PER CATEGORIA:")
    print(f"{'='*70}")
    recommendations = {
        "Errore di configurazione": "→ Implementare IaC (Ansible/Terraform), peer review obbligatoria per ogni change",
        "Patch non applicato": "→ Automatizzare il patching con WSUS/SCCM/Ansible, finestre fisse settimanali",
        "Capacity insufficiente": "→ Capacity planning trimestrale, alert predittivi con predict_linear()",
        "Password/Cert scaduto": "→ Inventario centralizzato certificati, alert 60/30/7 gg prima della scadenza",
        "Guasto hardware": "→ Contratti di manutenzione, sostituire hardware EOL, RAID + hot spare",
        "Bug software vendor": "→ Testing su staging prima del deploy, gestione patch vendor strutturata",
        "Errore utente": "→ Formazione utenti, guide self-service, KB accessibile",
    }
    for category, count in category_counts.most_common():
        rec = recommendations.get(category, "→ Analizzare le cause specifiche")
        print(f"\n  {category}:")
        print(f"  {rec}")


if __name__ == "__main__":
    pareto_analysis(SAMPLE_INCIDENTS)
```

---

## Checklist di Validazione Lab

**Parte A — Fondamenti:**
- [ ] A1: Elencare 3 cause di CPU alta e il relativo strumento di diagnosi su Linux
- [ ] A2: Descrivere il flusso Kerberos e cosa causa il "time skew error"
- [ ] A3: Elencare le 3 categorie di problemi storage e la soglia di alert per il disco
- [ ] A4: Descrivere i 5 layer del flusso email e dove può rompersi

**Parte B — Esercizi:**
- [ ] B1: `watch_memory_leak.py` eseguito — output mostra il trend di crescita RAM
- [ ] B1: Processo stress-ng identificato come top consumer con `ps aux --sort=-%cpu`
- [ ] B2: Account lockout simulato e trovata la sorgente con Event ID 4740
- [ ] B2: `repadmin /replsummary` mostra 0 errori di replica
- [ ] B2: Time skew verificato — differenza entro 5 minuti
- [ ] B3: Top 10 directory per dimensione identificate con `du -sh /var/* | sort -rh`
- [ ] B3: SMART check eseguito su `/dev/sda` — rilevare numero Reallocated Sectors
- [ ] B3: `iostat -x` mostra latenza (await) e utilizzo disco
- [ ] B4: `email_diagnostics.py` eseguito — output mostra stato postfix e coda
- [ ] B4: Test SMTP manuale completato con risposta "220"
- [ ] B5: `Reset-PrintSpooler -Force` eseguito — spooler riavviato con coda vuota
- [ ] B6: `strace -c ls /var/log` mostra il conteggio delle system call
- [ ] B6: `lsof -i :80` mostra quale processo usa la porta 80

**Parte C — Sistematizzazione:**
- [ ] C1: `system_health_check.sh` completato senza errori critici
- [ ] C1: Report salvato in `/tmp/health_check_*.txt`
- [ ] C2: `Get-ADHealthReport` mostra 0 account bloccati e 0 errori replica
- [ ] C3: `incident_cause_analysis.py` mostra analisi Pareto con raccomandazioni

---

## Appendice A: Comandi di Riferimento Rapido

### Linux — Performance

| Comando | Cosa mostra |
|---|---|
| `top -bn1 -o %CPU` | Top processi per CPU (un ciclo) |
| `ps aux --sort=-%mem` | Ordinato per memoria |
| `free -h` | Memoria disponibile e swap |
| `iostat -x 5 3` | I/O per disco ogni 5 secondi |
| `iotop -o` | I/O per processo (root) |
| `vmstat 5 5` | CPU + memoria + swap (5 campioni) |
| `sar -u 5 5` | CPU storico |

### Windows — Performance

| Cmdlet/Comando | Cosa mostra |
|---|---|
| `Get-Process \| Sort CPU -Desc \| Select -First 10` | Top per CPU |
| `Get-Counter '\Memory\Available MBytes'` | RAM disponibile |
| `Get-PSDrive -PSProvider FileSystem` | Spazio dischi |
| `Get-PhysicalDisk \| Select HealthStatus` | Salute dischi |

### Linux — Rete e Strumenti Avanzati

| Comando | Uso |
|---|---|
| `ss -tlnp` | Porte TCP in ascolto con PID |
| `lsof -i :<port>` | Chi usa quella porta |
| `strace -p <pid> -c` | Conteggio system call |
| `lsof -p <pid>` | File aperti da un processo |
| `netstat -tlnp` | (legacy, usare ss) |

---

## Appendice B: Albero Decisionale — Performance Lenta

```
Performance lenta
    │
    ├─ CPU > 70%?
    │       │
    │       ├─ SÌ → qual processo? (top/ps)
    │       │           │
    │       │           ├─ Processo noto → bug/overload? restart/tune
    │       │           ├─ Processo sconosciuto → malware? scan!
    │       │           └─ kernel/idle → driver issue? (xperf/perf)
    │       │
    │       └─ NO → passa a RAM
    │
    ├─ RAM > 85% o swap in uso?
    │       │
    │       ├─ SÌ → qual processo usa più RAM? (ps aux --sort=-%mem)
    │       │           │
    │       │           ├─ Crescita progressiva → memory leak?
    │       │           └─ Valore stabile alto → sizing insufficiente
    │       │
    │       └─ NO → passa a disco
    │
    ├─ Disk await > 20ms o queue > 2?
    │       │
    │       ├─ SÌ → quale processo fa I/O? (iotop)
    │       │           │
    │       │           ├─ Backup in esecuzione → schedulare
    │       │           ├─ RAID rebuild → attendere completamento
    │       │           └─ Carico legittimo → migrazione a SSD
    │       │
    │       └─ NO → verifica rete
    │
    └─ Rete > 60% utilizzo o latenza alta?
            │
            ├─ SÌ → quale traffico? (iperf3, tcpdump)
            │           │
            │           ├─ Backup su WAN → schedulare off-peak
            │           ├─ Saturazione link → QoS o upgrade
            │           └─ DNS lento → cambio server DNS
            │
            └─ NO → problema applicativo (log, APM, profiling)
```

---

## Appendice C: Riferimenti e Integrazioni ITIL 4

| Pratica ITIL 4 | Connessione con Questo Tutorial |
|---|---|
| **Monitoring and Event Management** | Gli alert CPU/disco/memoria identificati in B1-B3 sono eventi che richiedono gestione strutturata |
| **Incident Management** | Il troubleshooting performance/auth/storage è la risposta operativa a un incidente aperto |
| **Problem Management** | I pattern identificati con l'analisi Pareto (C3) diventano Problem Record proattivi |
| **Service Configuration Management** | Le baseline di performance sono configurazioni da tracciare nel CMDB |
| **Continual Improvement** | L'analisi Pareto identifica i Quick Win su cui concentrare i miglioramenti |

---

## Riferimenti

- `11-troubleshooting-generale.md` — Documento sorgente (sezioni 4-9)
- `tutorial_ops11_ch1a_methodology_network_lab.md` — Metodologia base e troubleshooting rete (prerequisito)
- `tutorial_ops07_ch1a_monitoring_setup_lab.md` — Setup Prometheus per raccolta metriche storiche
- `tutorial_ops11_ch2a_rca_problem_management_lab.md` — RCA e Problem Management (tutorial successivo)
- Linux `man` pages: `iostat(1)`, `strace(1)`, `lsof(8)`, `vmstat(8)`
- Microsoft Docs: `Get-Counter`, `Get-WinEvent`, `repadmin`
