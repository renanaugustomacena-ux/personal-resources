# Tutorial: Servizi File e Stampa di Rete — NFS, SMB, Print — Hands-On Lab

> **Documento di riferimento:** `04-servizi-infrastruttura.md` (sezioni Servizi File di Rete e Servizi di Stampa)
> **Dominio:** Infrastruttura — File e Risorse Condivise
> **Ambito:** NFS server su Linux (export, security, nfsstat), SMB/CIFS (disabilitazione SMB1, condivisioni Windows, Samba Linux), servizi di stampa (Windows Spooler, CUPS Linux, IPP), troubleshooting
> **Durata lab:** 3-4 ore
> **Livello:** Intermedio — richiede ops03a (Windows Server) e ops03b (Linux)
> **Prerequisiti:** DC-LAB-01 e SRV-LINUX-01 operativi, WKS-LAB-01 per test client
> **Ambiente:** SRV-LINUX-01 (NFS Server, Samba, CUPS), DC-LAB-01 (SMB Shares, Print Spooler), WKS-LAB-01 (client test)

---

## Lab Environment Setup

```bash
# Su SRV-LINUX-01 — verifica pre-lab
echo "=== VERIFICA PRE-LAB FILE E STAMPA ==="

# NFS tools
if dpkg -l nfs-kernel-server &>/dev/null 2>&1; then
    echo "[OK] NFS server installato"
else
    echo "[INFO] NFS server da installare: sudo apt install -y nfs-kernel-server"
fi

# Samba
if command -v smbd &>/dev/null; then
    echo "[OK] Samba installato: $(smbd --version | head -1)"
else
    echo "[INFO] Samba da installare: sudo apt install -y samba"
fi

# CUPS
if command -v cupsd &>/dev/null; then
    echo "[OK] CUPS installato"
else
    echo "[INFO] CUPS da installare: sudo apt install -y cups"
fi

# Rete lab
echo ""
echo "=== RETE ==="
ping -c1 -W2 192.168.56.10 &>/dev/null && echo "[OK] DC-LAB-01 raggiungibile" || echo "[WARN] DC-LAB-01 non risponde"
ping -c1 -W2 192.168.56.30 &>/dev/null && echo "[OK] WKS-LAB-01 raggiungibile" || echo "[WARN] WKS-LAB-01 non risponde"
```

---

## PART A: FONDAMENTI — File e Stampa: i Servizi che Rendono Produttivi gli Utenti

> Un'azienda senza file condivisi è come un ufficio dove ogni impiegato lavora su un'isola deserta. I file devono essere accessibili a tutti, sicuri, e sempre disponibili. Il file server centralizza e governa l'accesso ai dati aziendali. I servizi di stampa trasformano i documenti digitali in output fisico quando necessario. Questi servizi, spesso considerati "banali", impattano direttamente la produttività quotidiana di ogni lavoratore.

---

### Concetto A1: NFS — La Condivisione File del Mondo Unix/Linux

> **Analogia.** NFS è come un hard disk USB condiviso su una rete. Un server mette a disposizione una cartella (il disco). Tutti i client autorizzati possono "montare" quella cartella nel loro filesystem locale e usarla come se fosse sul loro stesso computer. Il file è in un posto solo (il server), ma tutti lo vedono come se fosse locale.

**Evoluzione NFS — perché importa la versione:**

```
NFSv3 (1995) — ancora molto diffuso
  Porta: multiple dinamiche (richiede portmapper/rpcbind)
  Sicurezza: basata su UID/GID UNIX (facile da falsificare!)
  Lock: protocollo NLM separato (causa problemi di stale lock)
  Firewall: difficile da filtrare (porte casuali)
  
NFSv4 (2003) e NFSv4.1/4.2 — raccomandato oggi
  Porta: SOLO TCP 2049 (un buco solo nel firewall!)
  Sicurezza: supporta Kerberos (krb5, krb5i, krb5p)
  Lock: integrato nel protocollo (niente stale lock)
  ACL: compatibili con Windows NTFS
  Deleghe: il client può cachare operazioni (più veloce)
```

**Opzioni di sicurezza export NFS critiche:**

```bash
# /etc/exports — ogni riga è una regola di condivisione
# FORMATO: path  host(opzioni)

# SICURO — condivisione dati aziendali per rete interna:
/dati/condivisa  192.168.56.0/24(rw,sync,no_subtree_check,root_squash)
# rw: read-write
# sync: scrivi su disco PRIMA di confermare al client (no data loss)
# no_subtree_check: migliora performance (evita problemi con rename)
# root_squash: l'utente root del client viene mappato ad anonymous (SICUREZZA!)

# SOLA LETTURA — backup, repository:
/dati/archivio  192.168.56.0/24(ro,sync,all_squash,anonuid=65534,anongid=65534)
# ro: read-only
# all_squash: TUTTI gli utenti diventano anonymous
# anonuid/anongid: specifica chi è l'anonymous

# ERRORI COMUNI:
/dati  *(rw,no_root_squash)  # ← PERICOLOSISSIMO!
# * = tutti possono accedere da qualsiasi IP
# no_root_squash = il root del client è root anche sul server → backdoor!
```

---

### Concetto A2: SMB/CIFS — La Condivisione File del Mondo Windows

> **Analogia.** SMB è come NFS ma parla "la lingua di Windows". Quando vedi `\\server\cartella` in Windows Explorer, stai usando SMB. È il protocollo che consente la classica "condivisione di rete" Windows: Risorse del Computer → Percorso UNC → Entra con le tue credenziali AD.

**La storia dei protocolli SMB — perché SMB1 è vietato:**

```
SMB 1.0 (1984) — OBSOLETO E PERICOLOSO
  Vulnerabilità: MS17-010 / EternalBlue (usata da WannaCry nel 2017)
  WannaCry ha cifrato 200.000+ computer in 150 paesi in 24 ore
  Propagazione: SMB1 sul vettore di attacco principale
  AZIONE: Disabilita SMB1 IMMEDIATAMENTE se ancora attivo
  
SMB 2.0/2.1 (Vista/7) — obsoleto ma sicuro
SMB 3.0 (Windows 8/Server 2012) — multichannel, crittografia
SMB 3.1.1 (Windows 10/Server 2016) — AES-256, pre-auth integrity
  AZIONE: Richiedi SMB minimo 2.1, preferisci 3.x
```

**Dove usare NFS vs SMB:**

```
NFS → ambienti Linux/Unix puri
  Linux server che montano storage condiviso
  VMware ESXi datastore
  Home directory Linux
  HPC clusters
  
SMB → ambienti Windows o misti
  File server aziendale standard (Windows)
  Home drive utenti AD
  Profili roaming
  Condivisione cartelle con utenti Windows
  
ENTRAMBI (NAS enterprise):
  NetApp, Dell EMC, Synology espongono entrambi
  La stessa cartella è accessibile da Linux (NFS) e Windows (SMB)
  Richiede mappatura identità (UID/GID ↔ SID AD)
```

---

### Concetto A3: Permessi File in Ambiente Misto — La Complessità dell'Integrazione

> **Perché mi interessa?** Il problema più comune nei file server misti Linux/Windows è: "L'utente Mario ha i permessi ma non riesce ad accedere al file." Spesso è perché i permessi POSIX (Linux) e NTFS (Windows) sono due sistemi diversi che devono essere sincronizzati.

**Modello permessi POSIX (Linux/NFS):**

```
Ogni file ha: owner (utente), group, others
Ogni entità ha: read(4), write(2), execute(1)
Esempio: -rwxr-x--- = 750
  owner: rwx (7)
  group: r-x (5)
  others: --- (0)

Identificazione tramite UID (User ID numerico, es. 1001)
Problema NFS: il client dice "sono UID 1001" — il server si fida
              Se un utente malevolo crea un file con UID 1001 su un altro client → accede!
              → Soluzione: NFSv4 + Kerberos elimina questo problema
```

**Modello permessi NTFS (Windows/SMB):**

```
Ogni file ha una ACL (Access Control List) con voci chiamate ACE
Ogni ACE associa un SID (Security Identifier) a permessi granulari
Esempio ACL: 
  ALLOW  BUILTIN\Administrators: Full Control
  ALLOW  LAB\Mario: Read, Write (no Delete, no Modify Permissions)
  DENY   LAB\Guest: Read

Identificazione tramite SID (es. S-1-5-21-...-1001)
Vantaggio: permessi molto granulari, gestiti da Active Directory
```

---

### Concetto A4: Servizi di Stampa — Perché la Stampa È Ancora Critica

> **Perché mi interessa?** "La stampante non funziona" è uno dei ticket più frequenti nel helpdesk. Ma i servizi di stampa non sono banali: un Print Server gestisce decine di stampanti, migliaia di job al giorno, driver di 5 versioni diverse, e deve essere disponibile H24 per reparti come contabilità, logistica, HR. Un Print Spooler bloccato blocca TUTTE le stampanti simultaneamente.

**Architettura Print Server:**

```
CLIENT (WKS-LAB-01)
  │ Vuole stampare documento.pdf
  │ Invia job via SMB a \\DC-LAB-01\HP-LaserJet-01
  ▼
PRINT SERVER (DC-LAB-01)
  │ Windows Print Spooler Service riceve il job
  │ Applica driver di stampa (trasforma PDF in linguaggio stampante)
  │ Mette in coda (spool directory: C:\Windows\System32\spool\PRINTERS\)
  │ Invia alla stampante fisica quando è disponibile
  ▼
STAMPANTE FISICA
  │ Riceve job su porta TCP 9100 (RAW) o IPP (Internet Printing Protocol)
  │ Stampa il documento
```

**Print Spooler — il servizio critico:**

```
Windows Print Spooler (spoolsv.exe):
  - Servizio SINGOLO che gestisce TUTTE le stampanti
  - Se crasha o si blocca → TUTTE le stampanti smettono di funzionare
  - Può bloccarsi per: driver corrotto, job di grandi dimensioni, 
                       permission issue, corruzione spool directory
  
Soluzione standard al blocco:
  1. Stop-Service Spooler -Force
  2. Remove-Item "C:\Windows\System32\spool\PRINTERS\*" -Force
  3. Start-Service Spooler
  
Spool directory: C:\Windows\System32\spool\PRINTERS\
  - Contiene i job in attesa come file .SPL e .SHD
  - Può riempirsi (job grandi, scanner in batch) → esaurisce C:
  - Monitorare dimensione! Alert se > 1 GB
```

**CUPS — Linux Print Server:**

```
CUPS (Common Unix Printing System):
  - Standard su Linux e macOS
  - Protocollo: IPP (Internet Printing Protocol) su porta 631
  - Web interface: http://localhost:631
  - Funziona sia come server locale che come server di rete
  
Differenza da Windows:
  Windows Spooler:  ogni stampante ha driver specifico Windows
  CUPS:             usa PPD (PostScript Printer Description) o
                    driverless con IPP Everywhere
```

---

### Concetto A5: IPP — Il Futuro della Stampa

> **Perché mi interessa?** Il trend nel 2025 è l'eliminazione dei Print Server tradizionali. IPP Everywhere permette ai client di stampare direttamente alle stampanti moderne senza driver e senza print server. Microsoft Universal Print porta la gestione stampanti nel cloud (Azure). Conoscere questi trend aiuta a pianificare il futuro dell'infrastruttura di stampa.

```
TRADIZIONALE (anni 2000-2020):
  Client → Print Server → Driver → Stampante
  Problema: driver da installare su ogni client, print server = SPOF

IPP EVERYWHERE (oggi):
  Client → Stampante direttamente (HTTP-like protocol)
  Nessun driver, nessun print server
  Richiede: stampante moderna con certificazione IPP Everywhere
  
UNIVERSAL PRINT (Microsoft 365):
  Client → Entra ID → Universal Print → Stampante
  Print server in cloud, zero infrastruttura on-premise
  Richiede: licenza M365, connettore per stampanti legacy
  Ideale per: ambienti cloud-first, hybrid work
  
Coesistenza (realtà attuale):
  Stampanti moderne (2020+): IPP Everywhere o Universal Print
  Stampanti legacy: ancora richiedono driver e spooler tradizionale
```

---
---

## PART B: OPERAZIONI — Configurare e Gestire File e Stampa in Lab

> **Obiettivo generale.** Alla fine di questa sezione sarai in grado di: configurare NFS Server su SRV-LINUX-01 e montarlo da un client Linux, configurare condivisioni SMB su DC-LAB-01 con permessi AD, verificare e hardening SMB (disabilitare SMB1), gestire lo spooler di stampa Windows, configurare CUPS su Linux, e diagnosticare i problemi più comuni di file e stampa.

---

### Esercizio B1: NFS Server — Configurazione e Test

**Obiettivo.** Installare e configurare NFS Server su SRV-LINUX-01, esportare una cartella con opzioni di sicurezza corrette, montarla da un client Linux.

**Background.** In produzione, NFS è usato per: home directory degli utenti Linux (tutti accedono alla stessa cartella da qualsiasi workstation), datastore VMware (le VM risiedono sul NFS share), condivisioni applicative (un DB server monta /db-data via NFS). Questo esercizio crea un export realistico con sicurezza appropriata.

**Step 1 — Installa NFS Server su SRV-LINUX-01.**

```bash
# Su SRV-LINUX-01

echo "=== INSTALLAZIONE NFS SERVER ==="
sudo apt update -qq
sudo apt install -y nfs-kernel-server nfs-common

# Verifica installazione
systemctl status nfs-server --no-pager | head -5
echo "NFS version: $(cat /proc/fs/nfsd/supported_krb5i 2>/dev/null && echo 'NFSv4+Kerberos' || echo 'NFSv4 senza Kerberos')"
```

**Step 2 — Crea struttura cartelle da esportare.**

```bash
# Crea cartelle per diversi tipi di condivisione
sudo mkdir -p /srv/nfs/shared-lab    # Condivisione lab (read-write)
sudo mkdir -p /srv/nfs/readonly-lab  # Sola lettura (archivio)

# Permessi appropriati
sudo chown nobody:nogroup /srv/nfs/shared-lab
sudo chmod 2775 /srv/nfs/shared-lab  # setgid bit: file ereditano il gruppo

sudo chown root:root /srv/nfs/readonly-lab
sudo chmod 755 /srv/nfs/readonly-lab

# Crea file di test
echo "File condiviso via NFS - $(date)" | sudo tee /srv/nfs/shared-lab/nfs_test.txt
echo "File archivio - $(date)"          | sudo tee /srv/nfs/readonly-lab/archive.txt

ls -la /srv/nfs/
```

**Step 3 — Configura gli export NFS.**

```bash
# Backup della configurazione originale
sudo cp /etc/exports /etc/exports.bak

# Scrivi la nuova configurazione
sudo tee /etc/exports << 'EXPORTS'
# NFS Exports — SRV-LINUX-01
# FORMATO: /percorso  rete(opzioni)
#
# Condivisione lab (read-write per rete interna)
/srv/nfs/shared-lab   192.168.56.0/24(rw,sync,no_subtree_check,root_squash)
#
# Archivio (sola lettura, tutti anonimi)
/srv/nfs/readonly-lab  192.168.56.0/24(ro,sync,no_subtree_check,all_squash,anonuid=65534,anongid=65534)
EXPORTS

echo "=== CONTENUTO /etc/exports ==="
cat /etc/exports
```

**Step 4 — Attiva gli export e verifica.**

```bash
# Applica la configurazione (senza riavviare il servizio)
sudo exportfs -ra
echo "Export applicati"

# Verifica export attivi
echo "=== EXPORT ATTIVI ==="
exportfs -v

# Avvia e abilita NFS server
sudo systemctl enable nfs-server
sudo systemctl start nfs-server
sudo systemctl status nfs-server --no-pager | head -8

# Porte NFS in ascolto
echo ""
echo "=== PORTE NFS ==="
sudo ss -tlnp | grep -E "2049|111|20048"
# 2049: nfs
# 111: rpcbind/portmapper
# 20048: mountd
```

**Output atteso:**

```
=== EXPORT ATTIVI ===
/srv/nfs/shared-lab   192.168.56.0/24(rw,wdelay,root_squash,no_subtree_check)
/srv/nfs/readonly-lab 192.168.56.0/24(ro,wdelay,all_squash,no_subtree_check)
```

**Step 5 — Test dal client: monta NFS da SRV-LINUX-01 su sé stesso.**

```bash
# Test locale (monta il nostro stesso export — equivalente al test da client)
sudo mkdir -p /mnt/nfs-test-shared
sudo mkdir -p /mnt/nfs-test-readonly

# Monta il share read-write
sudo mount -t nfs 192.168.56.20:/srv/nfs/shared-lab /mnt/nfs-test-shared
# oppure via loopback:
# sudo mount -t nfs localhost:/srv/nfs/shared-lab /mnt/nfs-test-shared

# Monta il share read-only
sudo mount -t nfs 192.168.56.20:/srv/nfs/readonly-lab /mnt/nfs-test-readonly

# Verifica mount
mount | grep nfs
echo ""
df -h /mnt/nfs-test-shared /mnt/nfs-test-readonly
```

**Step 6 — Test operazioni sul mount.**

```bash
# Test su shared (deve funzionare)
echo "=== TEST READ/WRITE su shared ==="
cat /mnt/nfs-test-shared/nfs_test.txt
echo "Scrittura di test - $(date)" >> /mnt/nfs-test-shared/nfs_test.txt
echo "[OK] Lettura e scrittura funzionanti"

# Test su readonly (scrittura deve fallire)
echo "=== TEST su readonly (deve dare permission denied) ==="
cat /mnt/nfs-test-readonly/archive.txt
if echo "test scrittura" >> /mnt/nfs-test-readonly/archive.txt 2>/dev/null; then
    echo "[ERRORE] Scrittura riuscita su share read-only — configurazione errata!"
else
    echo "[OK] Scrittura correttamente negata — read-only funzionante"
fi

# Statistiche NFS
echo ""
echo "=== STATISTICHE SERVER NFS ==="
nfsstat -s 2>/dev/null | head -20 || echo "[INFO] nfsstat richiede installazione: sudo apt install nfs-common"
```

**Step 7 — Smonta e configura /etc/fstab per mount permanente.**

```bash
# Smonta i mount temporanei
sudo umount /mnt/nfs-test-shared /mnt/nfs-test-readonly 2>/dev/null

# Per mount permanente (come si farebbe in produzione):
echo ""
echo "=== RIGA PER /etc/fstab (mount permanente) ==="
echo "192.168.56.20:/srv/nfs/shared-lab /mnt/shared nfs rw,sync,hard,intr,timeo=14 0 0"
echo ""
echo "[SPIEGAZIONE OPZIONI /etc/fstab]"
echo "  hard     → se NFS non raggiungibile, blocca (non silenzioso) — raccomandato"
echo "  intr     → permetti CTRL+C durante attesa (interrompibile)"
echo "  timeo=14 → timeout 1.4 secondi per i retry"
echo "  _netdev  → monta solo dopo che la rete è up"
```

**Checkpoint B1:**
- [ ] NFS server installato e in esecuzione (`systemctl status nfs-server`)
- [ ] `/etc/exports` configurato con `root_squash` e `sync`
- [ ] `exportfs -v` mostra i due export attivi
- [ ] Mount locale riuscito su `/mnt/nfs-test-shared`
- [ ] Scrittura su share read-only nega l'accesso correttamente

---

### Esercizio B2: SMB — Hardening e Gestione Condivisioni su DC-LAB-01

**Obiettivo.** Su DC-LAB-01, disabilitare SMB1, verificare le versioni SMB negoziate, creare condivisioni SMB con permessi AD, e gestire le sessioni attive.

**Background.** SMB1 è il protocollo che ha permesso la diffusione massiva di WannaCry nel 2017. Nei sistemi Windows moderni è disabilitato di default, ma potrebbe essere stato riabilitato per compatibilità con periferiche legacy (scanner, NAS vecchi). Verifica è obbligatoria in ogni audit di sicurezza.

**Step 1 — Su DC-LAB-01: verifica e disabilita SMB1.**

```powershell
# Su DC-LAB-01 (PowerShell come Administrator)

Write-Host "=== VERIFICA SMB1 ===" -ForegroundColor Cyan

# Verifica stato SMB1
$smb1Server = (Get-SmbServerConfiguration).EnableSMB1Protocol
$smb1Feature = (Get-WindowsOptionalFeature -Online -FeatureName "SMB1Protocol" -ErrorAction SilentlyContinue).State

Write-Host "SMB1 Server: $smb1Server"
Write-Host "SMB1 Feature: $smb1Feature"

if ($smb1Server -eq $true) {
    Write-Host "[ATTENZIONE] SMB1 è ABILITATO — vulnerabilità di sicurezza!" -ForegroundColor Red
    Write-Host "Disabilitazione in corso..."
    Set-SmbServerConfiguration -EnableSMB1Protocol $false -Force
    Write-Host "[OK] SMB1 disabilitato" -ForegroundColor Green
} else {
    Write-Host "[OK] SMB1 già disabilitato" -ForegroundColor Green
}

# Disabilita anche il client SMB1 (feature Windows)
if ($smb1Feature -eq "Enabled") {
    Disable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol -NoRestart
    Write-Host "[OK] Feature SMB1Protocol disabilitata"
}
```

**Step 2 — Abilita auditing SMB per rilevare client legacy.**

```powershell
Write-Host "`n=== AUDITING SMB ===" -ForegroundColor Cyan

# Abilita logging accessi SMB1 (prima di disabilitare, per sapere chi lo usa)
Set-SmbServerConfiguration -AuditSmb1Access $true -Force
Write-Host "Auditing SMB1 abilitato"

# Cerca connessioni SMB1 negli ultimi 7 giorni
Write-Host "`nRicerca connessioni SMB1 recenti..."
$smb1Events = Get-WinEvent -FilterHashtable @{
    LogName = "Microsoft-Windows-SMBServer/Audit"
    Id      = 3000
    StartTime = (Get-Date).AddDays(-7)
} -ErrorAction SilentlyContinue

if ($smb1Events) {
    Write-Host "[ATTENZIONE] Trovate $($smb1Events.Count) connessioni SMB1!" -ForegroundColor Yellow
    $smb1Events | Select-Object TimeCreated, Message | Format-Table -Wrap -AutoSize | Select-Object -First 10
    Write-Host "[AZIONE RICHIESTA] Aggiorna o isola i client che usano SMB1"
} else {
    Write-Host "[OK] Nessuna connessione SMB1 rilevata negli ultimi 7 giorni"
}
```

**Step 3 — Verifica versioni SMB nelle connessioni attive.**

```powershell
Write-Host "`n=== VERSIONI SMB CONNESSIONI ATTIVE ===" -ForegroundColor Cyan

# Mostra le sessioni SMB attive e le versioni negoziate
$sessions = Get-SmbSession -ErrorAction SilentlyContinue
if ($sessions) {
    $sessions | Select-Object ClientComputerName, ClientUserName, Dialect,
        @{N='SessAge_Min';E={[math]::Round($_.SecondsExists/60,1)}},
        NumOpens | Format-Table -AutoSize
    
    # Controlla se ci sono sessioni con protocolli vecchi
    $oldDialect = $sessions | Where-Object { $_.Dialect -match "^1\." -or $_.Dialect -eq "2.0.2" }
    if ($oldDialect) {
        Write-Host "[WARN] Client con versione SMB obsoleta ($($oldDialect.Dialect))" -ForegroundColor Yellow
    } else {
        Write-Host "[OK] Tutte le sessioni usano SMB 2.1 o superiore"
    }
} else {
    Write-Host "[INFO] Nessuna sessione SMB attiva al momento"
}

# Configurazione server SMB corrente
Write-Host "`n=== CONFIGURAZIONE SMB SERVER ===" -ForegroundColor Cyan
Get-SmbServerConfiguration | Select-Object EnableSMB1Protocol, EnableSMB2Protocol,
    EncryptData, RequireSecuritySignature, EnableMultiChannel | Format-List
```

**Step 4 — Crea condivisione SMB con permessi AD.**

```powershell
Write-Host "`n=== CREAZIONE CONDIVISIONE SMB LAB ===" -ForegroundColor Cyan

# Crea cartella per il file share
$sharePath = "C:\LabShare"
$shareName = "LabShare"

if (-not (Test-Path $sharePath)) {
    New-Item -ItemType Directory -Path $sharePath | Out-Null
    Write-Host "Cartella creata: $sharePath"
}

# Rimuovi condivisione esistente se già presente
if (Get-SmbShare -Name $shareName -ErrorAction SilentlyContinue) {
    Remove-SmbShare -Name $shareName -Force
    Write-Host "Condivisione precedente rimossa"
}

# Crea la nuova condivisione
New-SmbShare -Name $shareName -Path $sharePath `
    -Description "Condivisione Lab IT Operations" `
    -FullAccess "BUILTIN\Administrators" `
    -ReadAccess "LAB\Domain Users" `
    -FolderEnumerationMode AccessBased `
    -EncryptData $false   # In lab; in produzione usare $true

Write-Host "[OK] Condivisione '$shareName' creata"
Write-Host "     Path: $sharePath"
Write-Host "     UNC: \\$(hostname)\$shareName"

# Verifica la condivisione
Get-SmbShare -Name $shareName | Format-List Name, Path, Description, CurrentUsers, FolderEnumerationMode
```

**Step 5 — Verifica permessi NTFS e share permissions.**

```powershell
Write-Host "`n=== PERMESSI SHARE ===" -ForegroundColor Cyan

# Share-level permissions
Get-SmbShareAccess -Name "LabShare" | Format-Table -AutoSize

Write-Host "`n=== PERMESSI NTFS sulla cartella ==="
(Get-Acl "C:\LabShare").Access |
    Select-Object IdentityReference, FileSystemRights, AccessControlType |
    Format-Table -AutoSize

Write-Host "`n[NOTA] Permessi di accesso effettivo = intersezione tra Share e NTFS"
Write-Host "       Share: Domain Users = Read"
Write-Host "       NTFS:  Domain Users = Modify"
Write-Host "       Risultato: Domain Users ottengono READ (il più restrittivo dei due)"
```

**Step 6 — Gestione file aperti e sessioni bloccate.**

```powershell
Write-Host "`n=== FILE APERTI VIA SMB ===" -ForegroundColor Cyan

# File attualmente aperti da client SMB
$openFiles = Get-SmbOpenFile -ErrorAction SilentlyContinue
if ($openFiles) {
    $openFiles | Select-Object ClientComputerName, ClientUserName, Path, ShareRelativePath |
        Format-Table -AutoSize
    
    Write-Host "[INFO] Per chiudere un file bloccato:"
    Write-Host "       Close-SmbOpenFile -FileId <ID> -Force"
} else {
    Write-Host "[INFO] Nessun file aperto via SMB al momento"
}

# Simulazione: crea un file di test nella share
"File di test SMB - $(Get-Date)" | Out-File "C:\LabShare\smb_test.txt" -Encoding UTF8
Write-Host "`n[TEST] File creato in \\$(hostname)\LabShare\smb_test.txt"
Write-Host "       Accedi da WKS-LAB-01: Start → Run → \\192.168.56.10\LabShare"
```

**Checkpoint B2:**
- [ ] SMB1 verificato e disabilitato (`EnableSMB1Protocol = False`)
- [ ] Versioni SMB negoziate controllate (tutte 2.1+)
- [ ] Condivisione `LabShare` creata su DC-LAB-01
- [ ] Permessi share e NTFS configurati e verificati
- [ ] File di test accessibile da WKS-LAB-01 via `\\192.168.56.10\LabShare`

---

### Esercizio B3: Samba su SRV-LINUX-01 — File Server Linux per Client Windows

**Obiettivo.** Installare e configurare Samba su SRV-LINUX-01 per esporre una condivisione SMB accessibile da WKS-LAB-01, verificare le connessioni e lo stato del servizio.

**Background.** Samba è l'implementazione open-source di SMB per Linux. Permette a un server Linux di comportarsi come un file server Windows agli occhi dei client Windows. Usato comunemente per: NAS Linux accessibili da Windows, file server ibridi, condivisioni in ambienti open source.

**Step 1 — Installa Samba.**

```bash
# Su SRV-LINUX-01
echo "=== INSTALLAZIONE SAMBA ==="
sudo apt update -qq
sudo apt install -y samba samba-client

# Verifica versione
smbd --version
```

**Step 2 — Configura Samba.**

```bash
# Backup configurazione originale
sudo cp /etc/samba/smb.conf /etc/samba/smb.conf.bak

# Crea cartella da condividere
sudo mkdir -p /srv/samba/lab-share
sudo chown nobody:nogroup /srv/samba/lab-share
sudo chmod 0777 /srv/samba/lab-share

# Scrivi configurazione Samba
sudo tee /etc/samba/smb.conf << 'SAMBACONF'
[global]
   workgroup = LAB
   server string = SRV-LINUX-01 Samba Server
   server role = standalone server
   
   # Sicurezza: disabilita versioni obsolete
   server min protocol = SMB2_10
   server max protocol = SMB3
   
   # Logging
   log file = /var/log/samba/log.%m
   max log size = 1000
   logging = file
   
   # Performance
   socket options = TCP_NODELAY IPTOS_LOWDELAY

[lab-share]
   comment = Lab IT Operations Share
   path = /srv/samba/lab-share
   browseable = yes
   read only = no
   guest ok = yes
   guest account = nobody
   create mask = 0664
   directory mask = 0775
   
[homes]
   comment = Home Directories
   browseable = no
   read only = yes
   valid users = %S
SAMBACONF

echo "=== CONFIGURAZIONE CREATA ==="
```

**Step 3 — Valida e avvia Samba.**

```bash
# Valida la configurazione (come nginx -t per Nginx)
echo "=== VALIDAZIONE CONFIGURAZIONE ==="
testparm -s

echo ""
echo "=== AVVIO SAMBA ==="
sudo systemctl enable smbd nmbd
sudo systemctl restart smbd nmbd
sudo systemctl status smbd --no-pager | head -8
sudo systemctl status nmbd --no-pager | head -5

# Verifica porte
echo ""
echo "=== PORTE SAMBA ==="
sudo ss -tlnp | grep -E "445|139|137|138"
# 445: SMB diretto (TCP)
# 139: NetBIOS over TCP
# 137/138: NetBIOS (UDP) — usati da nmbd
```

**Step 4 — Test locale e remoto.**

```bash
# Test locale: lista condivisioni
echo "=== LISTA CONDIVISIONI (locale) ==="
smbclient -L localhost -N
# -L: lista condivisioni
# -N: no password (guest)

# Test connessione (apri sessione)
echo ""
echo "=== TEST CONNESSIONE SAMBA ==="
smbclient //192.168.56.20/lab-share -N -c "ls; put /etc/hosts test_upload.txt; ls; rm test_upload.txt"

# Status: connessioni attive
echo ""
echo "=== SAMBA STATUS ==="
sudo smbstatus | head -30
```

**Step 5 — Accesso da WKS-LAB-01 (Windows).**

```
Su WKS-LAB-01:
1. Apri Windows Explorer
2. Barra indirizzi: \\192.168.56.20\lab-share
3. Dovrebbe aprirsi la cartella condivisa
   (nessuna credenziale richiesta — guest ok = yes)

Alternativa da Command Prompt:
  net use Z: \\192.168.56.20\lab-share /user:guest ""
  dir Z:\
  copy C:\Windows\System32\drivers\etc\hosts Z:\hosts_test.txt
  del Z:\hosts_test.txt

Disconnetti:
  net use Z: /delete
```

**Step 6 — Sicurezza minima Samba — disabilita versione SMB vecchia.**

```bash
# Verifica versione minima SMB configurata
grep -i "min protocol" /etc/samba/smb.conf

# Verifica log per connessioni anomale
sudo tail -20 /var/log/samba/log.smbd 2>/dev/null || \
sudo tail -20 /var/log/samba/log.* 2>/dev/null | head -20

echo ""
echo "[BEST PRACTICE]"
echo "server min protocol = SMB2_10  → nessun client può usare SMB1 contro Samba"
echo "In produzione: aggiungi anche 'valid users = lista_utenti' (non guest ok)"
```

**Checkpoint B3:**
- [ ] Samba installato e in esecuzione (`systemctl status smbd`)
- [ ] `testparm -s` non mostra errori
- [ ] `smbclient -L localhost -N` lista `lab-share`
- [ ] Accesso da WKS-LAB-01 via `\\192.168.56.20\lab-share` funzionante
- [ ] `server min protocol = SMB2_10` nella configurazione

---

### Esercizio B4: Gestione Print Spooler su DC-LAB-01

**Obiettivo.** Monitorare lo stato del Print Spooler di Windows, gestire le code di stampa, simulare il ripristino da spooler bloccato.

**Background.** Il Print Spooler è il servizio Windows che gestisce tutte le stampanti. Quando si blocca, nessun utente riesce a stampare. La procedura di ripristino è ben nota, ma deve essere eseguita correttamente per non perdere i job in coda importanti.

**Step 1 — Verifica stato Spooler e stampanti.**

```powershell
# Su DC-LAB-01

Write-Host "=== STATO PRINT SPOOLER ===" -ForegroundColor Cyan
Get-Service -Name Spooler | Select-Object Name, Status, StartType

Write-Host "`n=== STAMPANTI INSTALLATE ===" -ForegroundColor Cyan
Get-Printer | Select-Object Name, PortName, DriverName, PrinterStatus, Shared |
    Format-Table -AutoSize

Write-Host "`n=== CONDIVISIONI STAMPANTE ===" -ForegroundColor Cyan
Get-Printer | Where-Object { $_.Shared -eq $true } |
    Select-Object Name, ShareName, PrinterStatus | Format-Table -AutoSize
```

**Step 2 — Aggiungi una stampante virtuale per il lab.**

```powershell
Write-Host "=== AGGIUNTA STAMPANTE VIRTUALE (per test) ===" -ForegroundColor Cyan

# In lab senza stampante fisica, usa Microsoft Print to PDF
# (installata di default su Windows Server 2022)
$pdfPrinter = Get-Printer -Name "Microsoft Print to PDF" -ErrorAction SilentlyContinue
if ($pdfPrinter) {
    Write-Host "[OK] Microsoft Print to PDF disponibile per test"
    # Condividi come stampante di rete (test)
    Set-Printer -Name "Microsoft Print to PDF" -Shared $true -ShareName "LAB-PDF-01"
    Write-Host "[OK] Stampante condivisa come LAB-PDF-01"
} else {
    Write-Host "[INFO] Aggiungi manualmente una stampante PDF da Impostazioni → Stampanti"
}
```

**Step 3 — Simula e risolvi spooler bloccato.**

```powershell
Write-Host "=== SIMULAZIONE SPOOLER RECOVERY ===" -ForegroundColor Cyan

# Verifica dimensione spool directory
$spoolDir = "$env:SystemRoot\System32\spool\PRINTERS"
$spoolSize = (Get-ChildItem -Path $spoolDir -ErrorAction SilentlyContinue |
    Measure-Object -Property Length -Sum).Sum / 1MB
Write-Host "Dimensione spool: $([math]::Round($spoolSize, 2)) MB"

if ($spoolSize -gt 1024) {
    Write-Host "[WARN] Spool > 1 GB — possibile problema" -ForegroundColor Yellow
} else {
    Write-Host "[OK] Dimensione spool normale"
}

# Procedura standard per spooler bloccato
Write-Host "`n=== PROCEDURA RIPRISTINO SPOOLER (simulazione) ===" -ForegroundColor Yellow
Write-Host "In caso di spooler bloccato:"
Write-Host ""
Write-Host "STEP 1: Stop spooler"
Write-Host "  Stop-Service Spooler -Force"
Write-Host ""
Write-Host "STEP 2: Elimina job in coda"
Write-Host "  Remove-Item '$env:SystemRoot\System32\spool\PRINTERS\*' -Force"
Write-Host ""
Write-Host "STEP 3: Riavvia spooler"
Write-Host "  Start-Service Spooler"
Write-Host ""
Write-Host "  (i job persi devono essere ristampati dagli utenti)"
Write-Host ""
Write-Host "=== ESECUZIONE (riavvio pulito senza eliminare job) ==="
Restart-Service Spooler
Get-Service Spooler | Select-Object Status
```

**Step 4 — Monitoraggio code e job.**

```powershell
Write-Host "=== JOB IN CODA ==="
Get-Printer | ForEach-Object {
    $jobs = Get-PrintJob -PrinterName $_.Name -ErrorAction SilentlyContinue
    if ($jobs) {
        Write-Host "Stampante: $($_.Name)"
        $jobs | Select-Object Id, UserName, DocumentName, JobStatus, Size |
            Format-Table -AutoSize
    }
}

Write-Host "`n=== DRIVER DI STAMPA INSTALLATI ===" 
Get-PrinterDriver | Select-Object Name, PrinterEnvironment, MajorVersion |
    Format-Table -AutoSize

# Driver versione < 4 (legacy) = attenzione
$legacyDrivers = Get-PrinterDriver | Where-Object { $_.MajorVersion -lt 4 }
if ($legacyDrivers) {
    Write-Host "[WARN] Driver versione < 4 trovati (legacy, instabili):" -ForegroundColor Yellow
    $legacyDrivers | Select-Object Name, MajorVersion | Format-Table
} else {
    Write-Host "[OK] Tutti i driver sono versione 4+"
}
```

**Step 5 — Event log per stampa (Event ID 307).**

```powershell
Write-Host "=== LOG EVENTI STAMPA (ultimi 7 giorni) ===" -ForegroundColor Cyan

# Event ID 307 = document printed
$printEvents = Get-WinEvent -FilterHashtable @{
    LogName   = "Microsoft-Windows-PrintService/Operational"
    Id        = 307
    StartTime = (Get-Date).AddDays(-7)
} -ErrorAction SilentlyContinue

if ($printEvents) {
    Write-Host "Job di stampa negli ultimi 7 giorni: $($printEvents.Count)"
    $printEvents | Select-Object TimeCreated,
        @{N='Utente';E={$_.Properties[2].Value}},
        @{N='Stampante';E={$_.Properties[4].Value}},
        @{N='Documento';E={$_.Properties[1].Value}},
        @{N='Pagine';E={$_.Properties[7].Value}} |
        Format-Table -AutoSize | Select-Object -First 10
} else {
    Write-Host "[INFO] Nessun log di stampa disponibile"
    Write-Host "       Abilita auditing: auditpol /set /subcategory:'Detailed File Share' /success:enable"
}
```

**Checkpoint B4:**
- [ ] `Get-Service Spooler` mostra status Running
- [ ] `Get-Printer` lista le stampanti (almeno "Microsoft Print to PDF")
- [ ] Conosci la procedura Stop → Svuota spool → Start
- [ ] `Get-PrintJob` usato per verificare le code

---

### Esercizio B5: CUPS — Print Server Linux

**Obiettivo.** Installare CUPS su SRV-LINUX-01, verificare la configurazione, aggiungere una stampante virtuale, e accedere all'interfaccia web di amministrazione.

**Background.** CUPS è il sistema di stampa standard di Linux (e macOS). In un ambiente con client Linux, CUPS gestisce centralmente tutte le stampanti. Può anche funzionare come print server per client Windows tramite Samba.

**Step 1 — Installa e configura CUPS.**

```bash
# Su SRV-LINUX-01

echo "=== INSTALLAZIONE CUPS ==="
sudo apt install -y cups cups-bsd cups-client

sudo systemctl enable cups
sudo systemctl start cups
sudo systemctl status cups --no-pager | head -8

# Verifica porta 631 (CUPS web interface)
sudo ss -tlnp | grep 631
```

**Step 2 — Configura CUPS per accesso remoto.**

```bash
# Per default CUPS ascolta solo su localhost
# Configura per accettare connessioni dalla rete lab

# Backup
sudo cp /etc/cups/cupsd.conf /etc/cups/cupsd.conf.bak

# Modifica per accettare connessioni dalla rete lab
sudo sed -i 's/^Listen localhost:631/Port 631/' /etc/cups/cupsd.conf
sudo sed -i 's/<Location \/>/<Location \/>\n  Allow 192.168.56.0\/24/' /etc/cups/cupsd.conf

# Aggiungi lab-admin al gruppo lpadmin (per gestire stampanti)
sudo usermod -a -G lpadmin lab-admin

# Riavvia CUPS
sudo systemctl restart cups
sleep 2
echo "CUPS riavviato - accesso web: http://192.168.56.20:631"
```

**Step 3 — Aggiungi stampante PDF virtuale (per test lab).**

```bash
# Installa cups-pdf (stampante virtuale che genera PDF)
sudo apt install -y cups-pdf

# Riavvia CUPS per caricare il nuovo driver
sudo systemctl restart cups

# Verifica che la stampante PDF sia registrata
lpstat -p -d
echo ""
lpstat -a

# Stampa una pagina di test
echo "Test di stampa - $(date)" | lp -P "PDF" 2>/dev/null || \
echo "[INFO] Stampante PDF: accedi a http://192.168.56.20:631 per configurare"
```

**Step 4 — Comandi di gestione CUPS.**

```bash
echo "=== STATO STAMPANTI CUPS ==="
lpstat -p             # lista stampanti e stato
lpstat -d             # stampante di default

echo ""
echo "=== CODE DI STAMPA ==="
lpq -a                # job in tutte le code

echo ""
echo "=== CONFIGURAZIONE CUPS ==="
cupsctl               # configurazione corrente

echo ""
echo "=== LOG CUPS (ultime 20 righe) ==="
sudo tail -20 /var/log/cups/error_log 2>/dev/null || \
sudo journalctl -u cups --no-pager | tail -20
```

**Step 5 — Test stampa da riga di comando.**

```bash
# Stampa un file di testo
echo "=== TEST STAMPA ==="
echo "Documento di test IT Ops Lab
Generato il: $(date)
Hostname: $(hostname)
Questo è un test di stampa via CUPS" > /tmp/print_test.txt

# Stampa verso la stampante PDF (genera /root/PDF/ o ~/PDF/)
lp /tmp/print_test.txt 2>/dev/null && \
    echo "[OK] Job di stampa inviato" || \
    echo "[INFO] Configura una stampante in CUPS: http://192.168.56.20:631"

# Job in coda
lpstat -o
echo ""
echo "=== FILE PDF GENERATI (cups-pdf) ==="
ls -lah ~/PDF/ 2>/dev/null || ls -lah /root/PDF/ 2>/dev/null || echo "[INFO] Directory PDF non trovata"
```

**Checkpoint B5:**
- [ ] CUPS installato e in esecuzione (`systemctl status cups`)
- [ ] Porta 631 in ascolto (`ss -tlnp | grep 631`)
- [ ] `lpstat -p` lista almeno la stampante PDF
- [ ] Accesso web funzionante: `http://192.168.56.20:631`
- [ ] Test di stampa eseguito

---

### Esercizio B6: Troubleshooting — Diagnosi Problemi File e Stampa

**Obiettivo.** Applicare un metodo sistematico di diagnosi ai problemi più comuni di file server e print server.

**Background.** Questo esercizio simula i ticket di helpdesk reali. Per ogni problema, segui il metodo: sintomo → verifica → causa → risoluzione → verifica.

**Scenario 1: "Non riesco a montare la condivisione NFS"**

```bash
# Su SRV-LINUX-01 — diagnosi sistematica

echo "=== DIAGNOSI NFS MOUNT FAILURE ==="

# 1. Il servizio NFS è attivo?
echo "1. Servizio NFS:"
systemctl is-active nfs-server && echo "  [OK] NFS attivo" || echo "  [FAIL] NFS non attivo — avviare: sudo systemctl start nfs-server"

# 2. L'export esiste?
echo "2. Export configurati:"
exportfs -v | grep -E "/srv/nfs" && echo "  [OK] Export presenti" || \
    echo "  [FAIL] Nessun export — verificare /etc/exports e eseguire exportfs -ra"

# 3. Il firewall blocca la porta NFS?
echo "3. Firewall NFS (porta 2049):"
sudo ufw status 2>/dev/null | grep -E "2049|nfs" || echo "  [INFO] ufw non attivo o NFS non nella lista esplicita"
# Se NFS bloccato: sudo ufw allow from 192.168.56.0/24 to any port 2049

# 4. Il client può raggiungere il server?
echo "4. Raggiungibilità:"
ping -c1 -W2 192.168.56.20 &>/dev/null && echo "  [OK] Server raggiungibile" || echo "  [FAIL] Server non raggiungibile"

# 5. I permessi dell'export corrispondono all'IP del client?
echo "5. Permessi per IP client (192.168.56.30):"
exportfs -v | grep "192.168.56"
```

**Scenario 2: "Il file server SMB è lento"**

```powershell
# Su DC-LAB-01

Write-Host "=== DIAGNOSI SMB LENTO ===" -ForegroundColor Cyan

# 1. Quante sessioni SMB attive?
$sessions = Get-SmbSession -ErrorAction SilentlyContinue
Write-Host "1. Sessioni SMB attive: $($sessions.Count)"
$sessions | Sort-Object NumOpens -Descending | Select-Object -First 5 ClientComputerName, ClientUserName, NumOpens | Format-Table

# 2. CPU del Print/File Server?
$cpu = Get-Counter '\Processor(_Total)\% Processor Time' -SampleInterval 3 -MaxSamples 1
Write-Host "2. CPU: $([math]::Round($cpu.CounterSamples[0].CookedValue, 1))%"

# 3. Disco: Avg Queue Length?
$diskQ = Get-Counter '\PhysicalDisk(_Total)\Avg. Disk Queue Length' -SampleInterval 3 -MaxSamples 1
$dql = [math]::Round($diskQ.CounterSamples[0].CookedValue, 2)
Write-Host "3. Disk Queue: $dql"
if ($dql -gt 2) { Write-Host "   [WARN] Disco saturo — possibile bottleneck I/O" -ForegroundColor Yellow }

# 4. Multichannel SMB abilitato?
$mc = (Get-SmbServerConfiguration).EnableMultiChannel
Write-Host "4. SMB MultiChannel: $mc"
if (-not $mc) { Write-Host "   [INFO] Abilita: Set-SmbServerConfiguration -EnableMultiChannel $true" }
```

**Scenario 3: "La stampante non stampa" (spooler bloccato)**

```powershell
# Su DC-LAB-01

Write-Host "=== DIAGNOSI STAMPANTE NON FUNZIONANTE ===" -ForegroundColor Cyan

# 1. Spooler attivo?
$spooler = Get-Service Spooler
Write-Host "1. Spooler: $($spooler.Status)"

# 2. Job bloccati in coda?
$allJobs = Get-Printer | ForEach-Object {
    Get-PrintJob -PrinterName $_.Name -ErrorAction SilentlyContinue
} 
$stuckJobs = $allJobs | Where-Object { $_.JobStatus -match "Error|Offline|Paused|Deleting" }
Write-Host "2. Job bloccati: $($stuckJobs.Count)"
$stuckJobs | Select-Object DocumentName, UserName, JobStatus | Format-Table

# 3. Stampante in stato di errore?
$errorPrinters = Get-Printer | Where-Object { $_.PrinterStatus -ne "Normal" }
if ($errorPrinters) {
    Write-Host "3. Stampanti in errore:" -ForegroundColor Yellow
    $errorPrinters | Select-Object Name, PrinterStatus | Format-Table
} else {
    Write-Host "3. Tutte le stampanti: status Normal"
}

# 4. Risoluzione standard
Write-Host "`n=== RISOLUZIONE ===" -ForegroundColor Yellow
Write-Host "Se spooler bloccato:"
Write-Host "  Stop-Service Spooler -Force"
Write-Host "  Remove-Item '$env:SystemRoot\System32\spool\PRINTERS\*' -Force"
Write-Host "  Start-Service Spooler"
Write-Host ""
Write-Host "Se stampante offline:"
Write-Host "  Set-Printer -Name 'NomeStampante' -WorkOffline `$false"
```

**Checkpoint B6:**
- [ ] Diagnosi NFS mount failure eseguita step-by-step
- [ ] Cause comuni SMB lento identificate (sessioni, CPU, disk queue, multichannel)
- [ ] Procedura ripristino spooler bloccato compresa e simulata

---
---

## PART C: SISTEMATIZZARE — Governance File e Stampa

---

### SOP-FS-001: Manutenzione Servizi File e Stampa

```
DOCUMENTO: SOP-FS-001 v1.0
TITOLO:    Procedura Operativa Standard — File Server e Print Server
AMBITO:    NFS (Linux), SMB (Windows/Samba), Print (Windows/CUPS)
TRIGGER:   Check settimanale + risposta a incident
OWNER:     Team IT Operations
```

**1. Check Settimanale (20 min)**

```
STEP 1: NFS (SRV-LINUX-01)
  systemctl status nfs-server | grep -E "Active|Error"
  exportfs -v | grep -E "Error|warning"
  nfsstat -s | grep -E "badcalls|badfmt|badauth"
  → badcalls > 0 = client che tentano accessi non autorizzati

STEP 2: SMB (DC-LAB-01)
  Get-SmbServerConfiguration | Select EnableSMB1Protocol
  → se True: DISABILITA IMMEDIATAMENTE (ticket P1)
  
  Get-SmbSession | Measure-Object → conta sessioni attive
  → anomalo spike = possibile attività insolita (investigate)
  
  (Get-SmbShare | Where {$_.Name -notlike "*$"}).Count
  → numero condivisioni deve essere stabile (nuove condivisioni = change request)

STEP 3: Print Spooler (DC-LAB-01)
  Get-Service Spooler | Select Status → deve essere Running
  Get-Printer | Where PrinterStatus -ne 'Normal' → stampanti in errore
  (Get-ChildItem "$env:SystemRoot\System32\spool\PRINTERS").Length / 1MB
  → > 100 MB: investigare job anomali
  → > 1 GB: ALERT P2, verifica job bloccati

STEP 4: CUPS (SRV-LINUX-01)
  systemctl is-active cups
  lpstat -a | grep -i reject → stampanti che non accettano job
  
STEP 5: Documenta in GLPI
  Stato OK: chiude ticket routine settimanale
  Anomalie: apri ticket di incidente appropriato
```

**2. Escalation**

```
NFS non risponde:     Verifica nfs-server → se down: incident P2
SMB1 riabilitato:     Incident P1 immediato → investigazione cause
Spool > 5 GB:         Incident P1 → ferma nuovi job, indaga causa
Stampanti tutte down: Incident P1 → impatto su tutti gli utenti
File non accessibili: Verifica permessi → se OK verifica disco → escalate a P2
```

---

### Script C1: fileprint_health.sh — Check File e Stampa su Linux

```bash
#!/usr/bin/env bash
# fileprint_health.sh — Check NFS e Samba e CUPS su SRV-LINUX-01
# Schedulare: 0 8 * * 1 /opt/scripts/fileprint_health.sh >> /var/log/fileprint_health.log 2>&1

set -euo pipefail
LOG="/tmp/fileprint_health_$(date +%Y%m%d_%H%M%S).txt"
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
STATUS="OK"; ISSUES=()

ok()   { echo -e "${GREEN}[OK]${NC}      $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC}    $*"; STATUS="WARNING"; ISSUES+=("WARN: $*"); }
crit() { echo -e "${RED}[CRITICO]${NC} $*"; STATUS="CRITICAL"; ISSUES+=("CRIT: $*"); }

{
echo "=================================================="
echo "  FILE & PRINT HEALTH REPORT — $(hostname)"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "=================================================="
echo ""

# ─── NFS ──────────────────────────────────────────────────────────────────────
echo "━━━ [1] NFS SERVER ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if systemctl is-active nfs-server &>/dev/null; then
    ok "NFS Server: RUNNING"
    
    # Conta export
    export_count=$(exportfs -v 2>/dev/null | wc -l)
    ok "Export attivi: $export_count"
    
    # Verifica client connessi
    client_count=$(showmount -a 2>/dev/null | grep -c ":" || echo 0)
    ok "Client NFS connessi: $client_count"
    
    # Verifica bad calls (accessi non autorizzati)
    bad_calls=$(nfsstat -s 2>/dev/null | grep -A2 "Server rpc stats" | grep "badcalls" | \
        awk '{print $2}' || echo 0)
    if [ "${bad_calls:-0}" -gt 100 ]; then
        warn "NFS badcalls: $bad_calls — possibili tentativi accesso non autorizzato"
    else
        ok "NFS badcalls: ${bad_calls:-0}"
    fi
else
    if systemctl list-unit-files nfs-server.service &>/dev/null 2>&1; then
        crit "NFS Server: STOPPED — avviare: sudo systemctl start nfs-server"
    else
        ok "NFS Server: non installato (skip)"
    fi
fi
echo ""

# ─── SAMBA ────────────────────────────────────────────────────────────────────
echo "━━━ [2] SAMBA ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if systemctl is-active smbd &>/dev/null; then
    ok "Samba smbd: RUNNING"
    
    # Versione minima protocollo
    min_proto=$(grep -i "server min protocol" /etc/samba/smb.conf 2>/dev/null | \
        tail -1 | awk '{print $NF}' || echo "not set")
    if echo "$min_proto" | grep -qiE "SMB1|LANMAN|CORE|NT1"; then
        crit "Samba min protocol: $min_proto — VULNERABILE! Impostare SMB2_10+"
    elif [ "$min_proto" = "not set" ]; then
        warn "Samba min protocol: non configurato — impostare 'server min protocol = SMB2_10'"
    else
        ok "Samba min protocol: $min_proto"
    fi
    
    # Condivisioni attive
    share_count=$(smbclient -L localhost -N 2>/dev/null | grep -c "Disk" || echo 0)
    ok "Condivisioni SMB: $share_count"
    
    # Sessioni attive
    conn_count=$(smbstatus -p 2>/dev/null | grep -c "smbd" || echo 0)
    ok "Processi Samba: $conn_count"
else
    if command -v smbd &>/dev/null; then
        warn "Samba smbd: STOPPED"
    else
        ok "Samba: non installato (skip)"
    fi
fi
echo ""

# ─── CUPS ─────────────────────────────────────────────────────────────────────
echo "━━━ [3] CUPS PRINT SERVER ━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if systemctl is-active cups &>/dev/null; then
    ok "CUPS: RUNNING"
    
    # Stampanti configurate
    printer_count=$(lpstat -p 2>/dev/null | grep -c "^printer" || echo 0)
    ok "Stampanti CUPS: $printer_count"
    
    # Job in coda
    job_count=$(lpstat -o 2>/dev/null | wc -l || echo 0)
    if [ "${job_count:-0}" -gt 50 ]; then
        warn "Job in coda CUPS: $job_count — verifica stampante"
    elif [ "${job_count:-0}" -gt 0 ]; then
        ok "Job in coda CUPS: $job_count"
    else
        ok "Code CUPS: vuote"
    fi
    
    # Errori recenti in log
    error_count=$(sudo grep -c "^E " /var/log/cups/error_log 2>/dev/null || echo 0)
    if [ "${error_count:-0}" -gt 10 ]; then
        warn "Errori CUPS log: $error_count — controllare /var/log/cups/error_log"
    else
        ok "Errori CUPS log: ${error_count:-0}"
    fi
else
    if command -v cupsd &>/dev/null; then
        warn "CUPS: STOPPED"
    else
        ok "CUPS: non installato (skip)"
    fi
fi
echo ""

# ─── SPAZIO DISCO (export NFS) ────────────────────────────────────────────────
echo "━━━ [4] SPAZIO CARTELLE CONDIVISE ━━━━━━━━━━━━━━━━━━━━"
for dir in /srv/nfs /srv/samba /home; do
    if [ -d "$dir" ]; then
        usage=$(df -h "$dir" | tail -1 | awk '{print $5}' | tr -d '%')
        avail=$(df -h "$dir" | tail -1 | awk '{print $4}')
        if [ "${usage:-0}" -ge 90 ]; then
            crit "$dir: ${usage}% utilizzato ($avail liberi)"
        elif [ "${usage:-0}" -ge 75 ]; then
            warn "$dir: ${usage}% utilizzato ($avail liberi)"
        else
            ok "$dir: ${usage}% utilizzato ($avail liberi)"
        fi
    fi
done
echo ""

# ─── SOMMARIO ─────────────────────────────────────────────────────────────────
echo "=================================================="
echo "STATO: $STATUS"
if [ ${#ISSUES[@]} -gt 0 ]; then
    echo "AZIONI RICHIESTE:"
    for i in "${ISSUES[@]}"; do echo "  → $i"; done
fi
echo "Fine: $(date '+%H:%M:%S')"
echo "=================================================="
} | tee "$LOG"
```

---

### Script C2: smb_security_check.ps1 — Audit SMB su Windows

```powershell
# smb_security_check.ps1 — Audit sicurezza SMB su DC-LAB-01
# Eseguire come Administrator: PowerShell -ExecutionPolicy Bypass -File smb_security_check.ps1

$Report = @()
$Status = "OK"

function Check {
    param([string]$Item, [bool]$IsOk, [string]$OkMsg, [string]$FailMsg, [string]$Severity="WARN")
    if ($IsOk) {
        Write-Host "[OK]      $Item : $OkMsg" -ForegroundColor Green
        $script:Report += [PSCustomObject]@{Item=$Item; Status="OK"; Detail=$OkMsg}
    } else {
        Write-Host "[$Severity] $Item : $FailMsg" -ForegroundColor $(if ($Severity -eq "CRIT") {"Red"} else {"Yellow"})
        $script:Report += [PSCustomObject]@{Item=$Item; Status=$Severity; Detail=$FailMsg}
        if ($Severity -eq "CRIT") { $script:Status = "CRITICAL" }
        elseif ($script:Status -ne "CRITICAL") { $script:Status = "WARNING" }
    }
}

Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "  SMB SECURITY AUDIT — $(hostname)"
Write-Host "  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

# ─── SMB1 ─────────────────────────────────────────────────────────────────────
Write-Host "━━━ SMB1 SECURITY ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
$smb1 = (Get-SmbServerConfiguration).EnableSMB1Protocol
Check "SMB1 Server" (-not $smb1) "Disabilitato (sicuro)" "ABILITATO — VULNERABILITA CRITICA (EternalBlue/WannaCry)" "CRIT"

$smb1Feature = (Get-WindowsOptionalFeature -Online -FeatureName "SMB1Protocol" -ErrorAction SilentlyContinue).State
Check "SMB1 Feature" ($smb1Feature -ne "Enabled") "Feature non installata" "Feature ancora presente — disabilitare" "WARN"

# ─── SMB SIGNING ──────────────────────────────────────────────────────────────
Write-Host "`n━━━ SMB SIGNING (integrità) ━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
$smbConfig = Get-SmbServerConfiguration
Check "SMB Signing Required" $smbConfig.RequireSecuritySignature "Richiesto" "Non richiesto — vulnerabile a relay attack" "WARN"
Check "SMB Signing Enabled"  $smbConfig.EnableSecuritySignature  "Abilitato" "Disabilitato — rischio relay" "WARN"

# ─── CRITTOGRAFIA SMB ─────────────────────────────────────────────────────────
Write-Host "`n━━━ CRITTOGRAFIA SMB ━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Check "SMB Encrypt" $smbConfig.EncryptData "Abilitato globalmente" "Disabilitato — dati in chiaro (normale in lab)" "WARN"

$encryptedShares = (Get-SmbShare | Where-Object { $_.EncryptData -eq $true }).Count
$totalShares     = (Get-SmbShare | Where-Object { $_.Name -notlike "*$" }).Count
Write-Host "          Condivisioni con crittografia: $encryptedShares/$totalShares"

# ─── VERSIONI DIALETTO SMB ATTIVO ─────────────────────────────────────────────
Write-Host "`n━━━ VERSIONI SMB IN USO ━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
$sessions = Get-SmbSession -ErrorAction SilentlyContinue
if ($sessions) {
    $dialectGroups = $sessions | Group-Object Dialect | Sort-Object Name
    foreach ($g in $dialectGroups) {
        $isOld = $g.Name -match "^1\." -or $g.Name -eq "2.0.2"
        Check "Dialetto SMB $($g.Name)" (-not $isOld) `
            "$($g.Count) sessioni (sicuro)" "$($g.Count) sessioni — dialetto obsoleto!" `
            $(if ($g.Name -match "^1\.") {"CRIT"} else {"WARN"})
    }
} else {
    Write-Host "          [INFO] Nessuna sessione SMB attiva"
}

# ─── CONDIVISIONI ─────────────────────────────────────────────────────────────
Write-Host "`n━━━ CONDIVISIONI SMB ━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
$shares = Get-SmbShare | Where-Object { $_.Name -notlike "*$" }
Write-Host "          Condivisioni non-admin: $($shares.Count)"
foreach ($s in $shares) {
    $abeEnabled = ($s.FolderEnumerationMode -eq "AccessBased")
    Check "Share $($s.Name): ABE" $abeEnabled "AccessBased (sicuro)" "Tutti vedono tutti i file" "WARN"
}

# ─── SOMMARIO ─────────────────────────────────────────────────────────────────
Write-Host "`n===========================================" -ForegroundColor Cyan
Write-Host "STATO FINALE: $Status" -ForegroundColor $(if ($Status -eq "OK") {"Green"} elseif ($Status -eq "WARNING") {"Yellow"} else {"Red"})
$Report | Where-Object { $_.Status -ne "OK" } | Format-Table Item, Status, Detail -AutoSize
Write-Host "==========================================="
```

---

### Integrazione con ITIL

| Pratica ITIL | File e Stampa |
|---|---|
| **Service Catalogue** | "Accesso file aziendali", "Stampa di rete" come servizi del catalogo |
| **Incident Management** | File inaccessibili, spooler bloccato → ticket P1/P2 con SLA |
| **Security Management** | SMB1 disabilitato, NFS con root_squash, ACL NTFS verificate |
| **Configuration Management** | CMDB: ogni share, ogni stampante è un CI con owner e SLA |
| **Change Management** | Nuova condivisione SMB = change record (chi lo approva?) |

---

### Checklist di Validazione Lab

**Part A — Fondamenti:**
- [ ] Sai spiegare la differenza NFSv3 vs NFSv4 (porta, sicurezza, lock)
- [ ] Sai cosa fa `root_squash` e perché `no_root_squash` è pericoloso
- [ ] Comprendi perché SMB1 è proibito (EternalBlue/WannaCry)
- [ ] Sai spiegare il flusso di stampa: client → spooler → stampante
- [ ] Conosci la differenza IPP Everywhere vs Print Server tradizionale

**Part B — Operazioni:**
- [ ] NFS server installato e export verificati con `exportfs -v`
- [ ] Mount NFS testato (shared e readonly con comportamento corretto)
- [ ] SMB1 disabilitato su DC-LAB-01 (`EnableSMB1Protocol = $false`)
- [ ] Condivisione LabShare creata con permessi ABE
- [ ] Samba installato con `server min protocol = SMB2_10`
- [ ] CUPS installato e `lpstat -p` mostra stampante PDF
- [ ] Diagnosi 3 scenari (NFS fail, SMB lento, spooler bloccato) completata

**Part C — Sistematizzare:**
- [ ] SOP-FS-001 letta con comprensione check settimanale e escalation
- [ ] `fileprint_health.sh` deployato e testato
- [ ] `smb_security_check.ps1` eseguito con output interpretato
- [ ] Connessione file/print a pratiche ITIL identificata

---

### Appendice A: Comandi Rapidi

```bash
# NFS (Linux)
exportfs -v                    # export attivi
showmount -a                   # client connessi
showmount -e 192.168.56.20     # export visibili da client
nfsstat -s                     # statistiche server
nfsstat -m                     # info sui mount
systemctl restart nfs-server   # riavvia NFS

# SAMBA (Linux)
testparm -s                    # valida smb.conf
smbstatus                      # connessioni, file aperti
smbclient -L localhost -N      # lista condivisioni
smbpasswd -a utente            # aggiungi utente Samba
smbpasswd -e utente            # abilita utente Samba

# CUPS (Linux)
lpstat -p -d                   # stampanti e default
lpstat -o                      # job in coda
lp -P NomeStampante file.pdf   # invia job
cancel JOBID                   # cancella job
cancel -a NomeStampante        # cancella tutti i job della stampante
cupsctl                        # configurazione CUPS
cupsctl --debug-logging        # abilita debug log (temporaneo)
```

```powershell
# SMB (Windows)
Get-SmbServerConfiguration                      # configurazione server
Get-SmbShare                                    # condivisioni
Get-SmbSession                                  # sessioni attive
Get-SmbOpenFile                                 # file aperti
Get-SmbConnection                               # connessioni (lato client)
Set-SmbServerConfiguration -EnableSMB1Protocol $false -Force  # disabilita SMB1

# PRINT SPOOLER (Windows)
Get-Service Spooler                             # stato spooler
Restart-Service Spooler                         # riavvia (senza pulire job)
Stop-Service Spooler -Force                     # ferma
Remove-Item "$env:SystemRoot\System32\spool\PRINTERS\*" -Force  # pulisci spool
Start-Service Spooler                           # riavvia
Get-Printer                                     # tutte le stampanti
Get-PrintJob -PrinterName "nome"               # job in coda
Get-PrinterDriver                               # driver installati
```

---

### Riferimenti

- `04-servizi-infrastruttura.md` §Servizi File di Rete e §Servizi di Stampa
- RFC 7862: NFSv4.2
- MS17-010: EternalBlue — la vulnerabilità SMB1 usata da WannaCry
- CUPS Documentation: https://www.cups.org/doc/
- Tutorial prerequisiti: `tutorial_ops03a` (Windows Server), `tutorial_ops03b` (Linux)
- Tutorial correlati: `tutorial_ops04_ch1b` (Active Directory — permessi), `tutorial_ops05_ch1a` (Security — SMB hardening)
